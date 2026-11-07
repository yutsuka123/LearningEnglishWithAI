"""怪しいアクセスの『日ごとの履歴』(logs.suspicious_access_days)を、Caddyの過去ログから補完する(2026-11-08・ver1.5.25)。

背景: 履歴の表は取り込み(5分毎)で積むので、ver1.5.25を入れるまでの動きは入っていない。Caddyのログ
(rotateされた.gzを含む)は2026-07-24から残っているので、そこからIPごと・日ごと(日本時間)に集計して
INSERT OR IGNOREで入れる(取り込みが積んだ行は上書きしない=何度流しても同じ・既存の行は変えない)。

2段構え(**集計は作業機・DBへの書き込みはコンテナ内**。Caddyのログはアプリのコンテナから読めないため):
  summarize  Caddyのログ(JSON行)を標準入力から読み、(IP, 日)ごとの要約をJSON行で標準出力へ。
             「怪しい」の基準はホスト側eigo-f2b-suspectsと**同じコード**(classify/BOT_UA/一覧に載る条件)を読み込んで使う。
             作業機でリポジトリのdeploy/fail2ban/bin/eigo-f2b-suspectsを読むので、コンテナには不要。
  load       summarizeの出力を標準入力から読み、logs.dbへ入れる。**--applyが無い間は何も書かない(ドライラン=件数だけ)**。
             --apply では、先にlogs.dbを別名でバックアップし、入れた後に主要テーブルの件数が減っていないか確認する
             (CLAUDE.md「本番DBに書き込む操作の前後の決まり」)。

使い方(コンテナのイメージの中身に依存しないよう、スクリプトを/tmpへ置いてから実行する):
  # 1) 集計(作業機・読み取りだけ)
  ssh eigo-vps 'docker exec aipoc-web sh -c "for f in /var/log/caddy/study-*.gz; do gunzip -c \\$f; done; cat /var/log/caddy/study.log"' \\
    | python3 -I scripts/suspect_days_backfill.py summarize > days.jsonl
  # 2) 書き込み(ver1.5.25を起動してから。まずドライラン→件数を確認→--apply)
  ssh eigo-vps "docker exec -i eigo-app sh -c 'cat > /tmp/sdb.py'" < scripts/suspect_days_backfill.py
  ssh eigo-vps "docker exec -i eigo-app python3 /tmp/sdb.py load" < days.jsonl            # ドライラン
  ssh eigo-vps "docker exec -i eigo-app python3 /tmp/sdb.py load --apply" < days.jsonl    # 実行
全手順は docs/ops/backfill_suspect_days_20261108.sh(git管理外)にまとめてある。
"""
from __future__ import annotations

import datetime as dt
import importlib.machinery
import importlib.util
import json
import os
import sqlite3
import sys
from pathlib import Path

JST = dt.timezone(dt.timedelta(hours=9))
HOST_SCRIPT = Path(__file__).resolve().parents[1] / "deploy" / "fail2ban" / "bin" / "eigo-f2b-suspects"
DB_PATH = os.environ.get("LOGS_DB", "/data/logs.db")
# 書き込み前後で減っていないことを確認するテーブル(logs.db内)
GUARD_TABLES = ("landing_visits", "usage_events", "client_errors", "security_events", "login_log",
                "suspicious_access", "manual_blocks", "ip_geo_cache")
HOST = "study.nyangailab.com"


def _load_host():
    loader = importlib.machinery.SourceFileLoader("eigo_f2b_suspects", str(HOST_SCRIPT))
    spec = importlib.util.spec_from_loader("eigo_f2b_suspects", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


def summarize(lines, host_mod) -> list[dict]:
    """Caddyのログ行 → (ip, 日本時間の日)ごとの要約。一覧に載る条件(build_itemsと同じ)を満たす日だけ。"""
    per: dict[tuple[str, str], dict] = {}
    for line in lines:
        try:
            r = json.loads(line)
        except ValueError:
            continue
        if not isinstance(r, dict):
            continue
        q = r.get("request") or {}
        if q.get("host") != HOST:
            continue
        ip = q.get("remote_ip") or ""
        if not host_mod.is_global(ip):
            continue
        ua = ((q.get("headers") or {}).get("User-Agent") or [""])[0]
        if host_mod.BOT_UA.search(ua):
            continue
        ts = float(r.get("ts") or 0)
        if ts <= 0:
            continue
        day = dt.datetime.fromtimestamp(ts, JST).strftime("%Y-%m-%d")
        e = per.setdefault((ip, day), {"total": 0, "probe": 0, "authfail": 0, "ratelimited": 0, "errors4xx": 0})
        e["total"] += 1
        kind = host_mod.classify(str(q.get("method") or "")[:10],
                                 host_mod.CTRL.sub("", str(q.get("uri") or "").split("?")[0])[:120],
                                 int(r.get("status") or 0))
        if kind:
            e[kind] += 1
    out = []
    for (ip, day), e in sorted(per.items()):
        if e["probe"] >= 1 or e["authfail"] >= 3 or e["ratelimited"] >= 10 or e["errors4xx"] >= 15:
            out.append({"ip": ip, "day": day, **e})
    return out


def _counts(conn) -> dict[str, int]:
    res = {}
    for t in GUARD_TABLES:
        try:
            res[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except sqlite3.Error:
            res[t] = -1
    return res


def load(rows: list[dict], apply: bool, db_path: str = DB_PATH) -> int:
    """--applyが無ければ読むだけ。--applyは、①先にバックアップ ②**1つの書き込みトランザクション**(BEGIN IMMEDIATE)の中で
    読み取り・挿入・件数の確認を行い、件数が想定と違えばROLLBACK(動いているアプリの取り込みと競合して件数が
    ずれても、誤って確定しない/誤って失敗扱いにならない・独立照査Fableの指摘)。"""
    conn = sqlite3.connect(db_path, timeout=30, isolation_level=None)   # 手動でトランザクションを管理
    try:
        has = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='suspicious_access_days'").fetchone()
        if not has:
            print("suspicious_access_days がまだ無い(ver1.5.25を起動してから実行する)。何もしない。")
            return 2
        if apply:
            stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")
            bk_path = os.path.join(os.path.dirname(db_path) or ".", f"backup_logs_manual_{stamp}_before_suspect_days.db")
            dst = sqlite3.connect(bk_path)
            try:
                conn.backup(dst)
            finally:
                dst.close()
            print("バックアップ:", os.path.basename(bk_path))
            conn.execute("BEGIN IMMEDIATE")   # ここから確定までの間、他の書き込みは待たされる(数秒)
        try:
            before_n = conn.execute("SELECT COUNT(*) FROM suspicious_access_days").fetchone()[0]
            existing = {(r[0], r[1]) for r in conn.execute("SELECT ip, day FROM suspicious_access_days")}
            new = [r for r in rows if (r["ip"], r["day"]) not in existing]
            ips = {r["ip"] for r in new}
            print(f"入力 {len(rows)}行 / 既にある {len(rows) - len(new)}行(変更しない) / 新規 {len(new)}行 "
                  f"({len(ips)} IP) / 履歴表の現在 {before_n}行")
            if not apply:
                print("ドライラン: 何も書いていない(--apply を付けると実行)。")
                return 0
            guard_before = _counts(conn)
            conn.executemany(
                "INSERT OR IGNORE INTO suspicious_access_days "
                "(ip, day, total, probe, authfail, ratelimited, errors4xx) VALUES (?, ?, ?, ?, ?, ?, ?)",
                [(r["ip"], r["day"], r["total"], r["probe"], r["authfail"], r["ratelimited"], r["errors4xx"])
                 for r in new])
            after_n = conn.execute("SELECT COUNT(*) FROM suspicious_access_days").fetchone()[0]
            guard_after = _counts(conn)
            bad = {t: (guard_before[t], guard_after[t]) for t in GUARD_TABLES if guard_after[t] < guard_before[t]}
            print(f"履歴表 {before_n} → {after_n}行(期待 +{len(new)})")
            print("主要テーブルの件数: " + ("減少なし ✅" if not bad else f"⚠️ 減少 {bad}"))
            if bad or after_n != before_n + len(new):
                conn.execute("ROLLBACK")
                print("⚠️ 想定と違うため取り消した(ROLLBACK)。何も変更していない。バックアップは残してある。")
                return 1
            conn.execute("COMMIT")
            return 0
        except BaseException:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
            raise
    finally:
        conn.close()


def main(argv: list[str]) -> int:
    if len(argv) < 2 or argv[1] not in ("summarize", "load"):
        print(__doc__)
        return 2
    if argv[1] == "summarize":
        rows = summarize(sys.stdin, _load_host())
        for r in rows:
            print(json.dumps(r, ensure_ascii=False))
        print(f"# summarize: {len(rows)}行 / {len({r['ip'] for r in rows})} IP", file=sys.stderr)
        return 0
    rows = [json.loads(x) for x in sys.stdin if x.strip() and not x.startswith("#")]
    return load(rows, "--apply" in argv)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
