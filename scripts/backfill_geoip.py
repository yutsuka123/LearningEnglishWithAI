"""landing_visits に記録済みで ip_geo_cache が未取得のIPを後追いで埋める
（2026-08-21）。

geo情報の収集(app/services/geoip.py)は2026-08-20に導入したもので、
リクエスト受信時のバックグラウンド処理でしか埋まらない。そのため
導入前に訪問していたIPは管理画面「未登録アクセス状況」の
「国/地域/市区」「接続元組織・ホスト名」が「—」のまま残る。
このスクリプトはその取りこぼしを後から埋める。

対象にするIP:
  1. ip_geo_cache に行が無い
  2. 行はあるが country が空（外部APIの RateLimited 等で取得に失敗した
     ケース。管理画面上は結局「—」になるので再試行する）

外部API(ipapi.co)の無料枠は1日1000リクエストで、超過すると
error='RateLimited' が保存され country が空のままになる。連続で叩くと
短時間でも弾かれるため、既定で1.2秒間隔・1回の実行あたり最大300件に
制限している。取りこぼしが残った場合は日を改めて再実行すればよい
（成功済みのIPは対象から外れるので、何度実行しても無駄打ちしない）。

使い方(VPS上、eigo-appコンテナの中で実行を想定):
  docker exec eigo-app python3 scripts/backfill_geoip.py             # 件数確認のみ
  docker exec eigo-app python3 scripts/backfill_geoip.py --execute   # 実際に取得
  docker exec eigo-app python3 scripts/backfill_geoip.py --execute --days 90
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db, init_db  # noqa: E402
from app.services import geoip  # noqa: E402

# ipapi.co の無料枠(1日1000件)に対する安全側の既定値。
_DEFAULT_SLEEP = 1.2
_DEFAULT_LIMIT = 300


def _candidates(days: int, limit: int) -> list[str]:
    """未取得・取得失敗のIPを、直近に訪問があったものから順に返す。"""
    where_days = ""
    params: list[object] = []
    if days > 0:
        where_days = "AND lv.created_at >= datetime('now', ?)"
        params.append(f"-{days} days")
    params.append(limit)
    with db() as conn:
        rows = conn.execute(
            "SELECT lv.ip AS ip, MAX(lv.created_at) AS last_seen "
            "FROM landing_visits lv "
            "LEFT JOIN ip_geo_cache g ON g.ip = lv.ip "
            f"WHERE lv.ip != '' {where_days} "
            "  AND (g.ip IS NULL OR COALESCE(g.country, '') = '') "
            "GROUP BY lv.ip "
            "ORDER BY last_seen DESC LIMIT ?",
            params,
        ).fetchall()
    return [r["ip"] for r in rows]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--days", type=int, default=0,
                   help="対象期間(日)。0なら全期間（既定: 0）")
    p.add_argument("--limit", type=int, default=_DEFAULT_LIMIT,
                   help=f"1回の実行で取得する最大件数（既定: {_DEFAULT_LIMIT}）")
    p.add_argument("--sleep", type=float, default=_DEFAULT_SLEEP,
                   help=f"外部API呼び出しの間隔(秒)（既定: {_DEFAULT_SLEEP}）")
    p.add_argument("--execute", action="store_true",
                   help="指定しない場合は対象件数を表示するだけ(dry-run)")
    args = p.parse_args()

    init_db()
    targets = _candidates(args.days, args.limit)
    scope = "全期間" if args.days <= 0 else f"直近{args.days}日"
    print(f"対象({scope}・未取得/取得失敗): {len(targets)} 件")
    if not args.execute:
        print("dry-run です。実際に取得するには --execute を付けてください。")
        return 0
    if not targets:
        return 0

    eta = len(targets) * args.sleep
    print(f"取得を開始します（{args.sleep}秒間隔・想定所要 約{eta / 60:.1f}分）")

    ok = failed = 0
    # 外部APIが軒並み駄目（レート制限・障害）なときに112件を無駄に叩き
    # 続けないための打ち切り。単発の失敗（PTR無し等）では止めない。
    consecutive_failures = 0
    _MAX_CONSECUTIVE = 5
    for i, ip in enumerate(targets, 1):
        # enrich_ip はキャッシュ行があると即returnするため、再試行対象
        # (country が空の行)は先に消してから呼ぶ。
        with db() as conn:
            conn.execute("DELETE FROM ip_geo_cache WHERE ip = ?", (ip,))
        try:
            geoip.enrich_ip(ip)
        except Exception as e:  # noqa: BLE001 — 1件の失敗で全体を止めない
            print(f"  [{i}/{len(targets)}] {ip} 例外: {e}")
            failed += 1
            continue
        with db() as conn:
            row = conn.execute(
                "SELECT country, city, org, hostname, error "
                "FROM ip_geo_cache WHERE ip = ?", (ip,),
            ).fetchone()
        if row and row["country"]:
            ok += 1
            consecutive_failures = 0
            where = " / ".join(x for x in (row["country"], row["city"]) if x)
            who = row["org"] or row["hostname"] or "(組織名なし)"
            print(f"  [{i}/{len(targets)}] {ip} -> {where} / {who}")
        else:
            failed += 1
            consecutive_failures += 1
            reason = (row["error"] if row else "") or "(空の応答)"
            print(f"  [{i}/{len(targets)}] {ip} -> 失敗: {reason}")
            if consecutive_failures >= _MAX_CONSECUTIVE:
                print(f"  {_MAX_CONSECUTIVE}件連続で失敗したため中断します"
                      "（外部APIのレート上限/障害の可能性）。"
                      "時間をおいて再実行してください。")
                break
        if i < len(targets):
            time.sleep(args.sleep)

    print(f"完了: 成功 {ok} 件 / 失敗 {failed} 件")
    if failed:
        print("失敗分は再実行で再試行されます（成功済みは対象外）。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
