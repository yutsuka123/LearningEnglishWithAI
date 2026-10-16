"""航空管制フレーズ2件の「グラウンド118.9」を121.9に直す(2026-10-16・オーナー指示)。

背景: 2026-10-12のSNS九弾の照査(Fable)で、アプリのフレーズ訳に誤りが見つかった。
英文は「ground point niner」(=周波数の末尾「.9」だけを言う省略形)で、グラウンド(地上走行)
管制の周波数は118.xではなく121.6〜121.9MHz帯。タワーの118.xと混同した訳だった。

対象(英文の完全一致で特定する。IDはローカルと本番で違うため):
  ・"Readback correct, contact ground point niner when ready to taxi."
  ・"Contact ground point niner."
各行の japanese / detail(JSON文字列)の中の「118.9」を「121.9」に置換するだけ。
英文は変えない(音声は英文のハッシュで引くので、音声の作り直しは不要)。
タワー118.3(別フレーズ)や、英文が118.xと言っている別フレーズには触れない。

オプション `--with-ramp-phrase`: 同じ誤りが3つ目にもあった(本番id=6827・類似表現「Contact ground point six once clear.」の訳が
「グラウンド118.6」・英文は「point six」(末尾.6)だけ)ので、英文の完全一致 "Contact ramp control once clear of the runway." の
detail内の「グラウンド118.6」だけを「グラウンド121.6」に直せる。**オーナー指示の2件には含まれないため既定では触らない**。

本番のDBを丸ごと上書きしない(CLAUDE.md 2026-09-13の重大インシデント): このスクリプトは
phrases表の該当2行のUPDATEだけを行い、実行前に content.db を SQLite バックアップAPIで複製し、
前後で主要テーブルの件数が変わらないことを確認する。

使い方(本番ではコンテナの中で。ローカルは DATA_DIR を隔離したコピーで試す):
  python scripts/fix_phrase_ground_freq_2026_10_16.py            # dry-run(読み取りだけ)
  python scripts/fix_phrase_ground_freq_2026_10_16.py --apply    # 実行(バックアップ+件数確認つき)
  python scripts/fix_phrase_ground_freq_2026_10_16.py --rollback <data/script_backups/..._originals.json>
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _db_safety import default_backup_dir, key_counts, print_counts, same_counts  # noqa: E402
from app.config import paths  # noqa: E402
from app.database import db  # noqa: E402

# (英文の完全一致, 置換前, 置換後, japaneseに期待する出現数, detailに期待する出現数)
# **期待する出現数と実際が違えば、1行も書かずに中止する**(2026-10-16・独立照査M4): 本番の2行を読み取りで確認した値
# (6704=japanese1+detail2[類似表現の「グラウンド118.9を聴取」と説明の「グラウンド周波数118.9」]・6776=japanese1)。
# 想定外の「118.9」(例: タワーの周波数に触れた補足文)が増えていたら、機械的な置換で壊さず人が見る。
TARGETS = (
    ("Readback correct, contact ground point niner when ready to taxi.", "118.9", "121.9", 1, 2),
    ("Contact ground point niner.", "118.9", "121.9", 1, 0),
)
# オーナー指示の2件ではない(--with-ramp-phrase のときだけ)。detailの類似表現の「グラウンド118.6」だけを直す。
EXTRA_TARGETS = (
    ("Contact ramp control once clear of the runway.", "グラウンド118.6", "グラウンド121.6", 0, 1),
)


LIVE_TABLES = ("users", "paypay_payments", "landing_visits", "usage_events")   # 運用中は増える。減っていないことだけ見る


def _counts_ok(before: dict, after: dict) -> bool:
    """words/phrases は不変・生きている表は減っていないこと(2026-10-16・2回目の独立照査LOW-1)。
    本番ではこのスクリプトの実行中にも訪問記録(landing_visits/usage_events)が増えるため、全表の一致を要求すると
    無害な増加で中止してしまう(中止しても安全だが、障害に見える文言になる)。"""
    if any(before.get(t) != after.get(t) for t in ("words", "phrases")):
        return False
    return all(after.get(t, 0) >= before.get(t, 0) for t in LIVE_TABLES)


def _num_pattern(old: str):
    """数値の途中に一致しない(118.95や2118.9を巻き込まない)パターン。"""
    return re.compile(r"(?<![\d.])" + re.escape(old) + r"(?!\d)")


def _backup_content_db(backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    dst = backup_dir / f"content_before_ground_freq_{time.strftime('%Y%m%d_%H%M%S')}.db"
    src = sqlite3.connect(f"file:{paths.content_db_file}?mode=ro", uri=True)
    out = sqlite3.connect(dst)
    with out:
        src.backup(out)
    out.close()
    src.close()
    return dst


def _contexts(text: str, needle: str, pat, width: int = 24) -> list[str]:
    """出現箇所ごとの前後(±width字)。dry-runで「何が変わるか」を人が目で確かめるため。"""
    return ["…" + text[max(0, m.start() - width):m.start()] + "【" + needle + "】" + text[m.end():m.end() + width] + "…"
            for m in pat.finditer(text)]


def _plan(conn, targets) -> list[dict]:
    """対象行ごとに {id, english, japanese, detail, new_japanese, new_detail, n_ja, n_detail} を作る。
    英文の完全一致が1行でなければ中止(想定外のデータには書かない)。出現数が期待と違っても中止。"""
    plan = []
    for en, OLD, NEW, exp_ja, exp_detail in targets:
        pat = _num_pattern(OLD)
        rows = conn.execute(
            "SELECT id, english, japanese, detail FROM phrases WHERE english = ?", (en,)
        ).fetchall()
        if len(rows) != 1:
            raise SystemExit(f"中止: 英文 {en!r} に一致する行が{len(rows)}件(期待1件)")
        r = rows[0]
        ja, detail = r["japanese"] or "", r["detail"] or ""
        item = {
            "id": r["id"], "english": r["english"], "japanese": ja, "detail": detail,
            "raw_japanese": r["japanese"], "raw_detail": r["detail"],     # 元のNULLを保つ(ロールバック用)
            "old": OLD, "new": NEW,
            "n_ja": len(pat.findall(ja)), "n_detail": len(pat.findall(detail)),
            # 元がNULLの列は、書き戻してもNULLのまま(空文字に変えない)
            "new_japanese": None if r["japanese"] is None else pat.sub(NEW, ja),
            "new_detail": None if r["detail"] is None else pat.sub(NEW, detail),
        }
        if item["n_ja"] + item["n_detail"] == 0 and NEW in (ja + detail):
            item["state"] = "済み"
        elif item["n_ja"] + item["n_detail"] == 0:
            raise SystemExit(f"中止: id={r['id']} に {OLD} も {NEW} も見当たらない(想定外の内容)")
        else:
            item["state"] = "要修正"
            if (item["n_ja"], item["n_detail"]) != (exp_ja, exp_detail):
                raise SystemExit(
                    f"中止: id={r['id']} の{OLD}の出現数が想定と違う(japanese {item['n_ja']}/想定{exp_ja}・detail {item['n_detail']}/想定{exp_detail})。"
                    "本番の内容が変わっているか、想定外の箇所に同じ数値がある。人が確認してから")
        item["ctx_ja"] = _contexts(ja, OLD, pat)
        item["ctx_detail"] = _contexts(detail, OLD, pat)
        if detail:
            json.loads(item["new_detail"])   # detail が壊れたJSONにならないこと
        plan.append(item)
    return plan


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="実際に書き込む(既定はdry-run)")
    ap.add_argument("--with-ramp-phrase", action="store_true",
                    help="3つ目(Contact ramp control once clear of the runway.)の「グラウンド118.6」も121.6に直す")
    ap.add_argument("--rollback", default=None, help="--apply が保存した *_originals.json から2行を元に戻す")
    ap.add_argument("--backup-dir", default=None, help="既定 DATA_DIR/script_backups")
    args = ap.parse_args()
    backup_dir = Path(args.backup_dir) if args.backup_dir else default_backup_dir()

    if args.rollback:
        originals = json.loads(Path(args.rollback).read_text(encoding="utf-8"))
        with db() as conn:
            before = key_counts(conn)
            print_counts("before", before)
            for o in originals:
                cur = conn.execute("UPDATE phrases SET japanese = ?, detail = ? WHERE id = ? AND english = ?",
                                   (o["japanese"], o["detail"], o["id"], o["english"]))
                if cur.rowcount != 1:
                    raise SystemExit(f"中止(ここまでの更新は取り消し): id={o['id']} を戻せなかった(rowcount={cur.rowcount})")
            after = key_counts(conn)
            print_counts("after", after)
            ok = _counts_ok(before, after)
            print("件数チェック:", "OK" if ok else "NG ← 想定外。直ちに調査")
            if not ok:
                raise SystemExit("中止(更新は取り消し): words/phrasesの件数が変わった、または生きている表が減った")
        return 0

    with db() as conn:
        before = key_counts(conn)
        print_counts("before", before)
        plan = _plan(conn, TARGETS + (EXTRA_TARGETS if args.with_ramp_phrase else ()))
        for p in plan:
            print(f"id={p['id']} [{p['state']}] {p['english']}")
            print(f"    japanese: {p['japanese']}  ({p['old']}が{p['n_ja']}箇所)")
            print(f"    → {p['new_japanese'] or ''}")
            print(f"    detail内の{p['old']}: {p['n_detail']}箇所")
            for c in p["ctx_ja"] + p["ctx_detail"]:
                print(f"      {c}")
        todo = [p for p in plan if p["state"] == "要修正"]
        if not args.apply:
            print(f"dry-run のため書き込みません(修正対象 {len(todo)}行)。--apply で実行。")
            return 0
        if not todo:
            print("修正済みです。何もしません。")
            return 0

        bk = _backup_content_db(backup_dir)
        print(f"content DB バックアップ: {bk}")
        orig_file = backup_dir / f"ground_freq_originals_{time.strftime('%Y%m%d_%H%M%S')}.json"
        orig_file.write_text(
            json.dumps([{"id": p["id"], "english": p["english"], "japanese": p["raw_japanese"], "detail": p["raw_detail"]}
                        for p in todo], ensure_ascii=False, indent=1), encoding="utf-8")
        for p in todo:
            cur = conn.execute(
                "UPDATE phrases SET japanese = ?, detail = ? WHERE id = ? AND english = ?",
                (p["new_japanese"], p["new_detail"], p["id"], p["english"]))
            if cur.rowcount != 1:
                raise SystemExit(f"中止(ここまでの更新は取り消し): id={p['id']} の更新が1行ではない(rowcount={cur.rowcount})")
        after = key_counts(conn)
        print_counts("after", after)
        ok = _counts_ok(before, after)
        if not ok:
            # `with db()`は例外で巻き戻す。NGのまま確定(commit)させない。
            raise SystemExit("中止(更新は取り消し): words/phrasesの件数が変わった、または生きている表(users等)が減った ← 想定外。調査")
        print(f"件数チェック: OK(words/phrasesの行数は不変・生きている表は減っていない・該当{len(todo)}行の本文だけが変わった)")
        print(f"元に戻す: --rollback {orig_file}")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
