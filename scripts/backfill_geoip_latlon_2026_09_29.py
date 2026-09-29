"""ip_geo_cache に既に country 等はあるが緯度経度が未保存の行を埋める
一回限りの後追いスクリプト(2026-09-29・アクセスログの地理的可視化用)。

latitude/longitude 列は2026-09-29に追加した(app/database.py)。それより
前に enrich_ip() でキャッシュ済みだった行は、外部APIのJSONに緯度経度が
含まれていても保存していなかったため空のまま。このスクリプトはその
取りこぼしだけを対象に再取得する(country が既にある行だけが対象・
未取得/取得失敗のIPは scripts/backfill_geoip.py の担当のまま)。

外部APIのレート制限に対する安全策は scripts/backfill_geoip.py と同じ
(既定1.2秒間隔・1回最大300件・連続失敗5回で打ち切り)。

使い方(VPS上、eigo-appコンテナの中で実行を想定):
  docker exec eigo-app python3 scripts/backfill_geoip_latlon_2026_09_29.py             # 件数確認のみ
  docker exec eigo-app python3 scripts/backfill_geoip_latlon_2026_09_29.py --execute
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db, init_db  # noqa: E402
from app.services import geoip  # noqa: E402

_DEFAULT_SLEEP = 1.2
_DEFAULT_LIMIT = 300


def _candidates(limit: int) -> list[str]:
    with db() as conn:
        rows = conn.execute(
            "SELECT ip FROM ip_geo_cache "
            "WHERE COALESCE(country, '') != '' AND latitude IS NULL "
            "ORDER BY fetched_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [r["ip"] for r in rows]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--limit", type=int, default=_DEFAULT_LIMIT,
                   help=f"1回の実行で取得する最大件数（既定: {_DEFAULT_LIMIT}）")
    p.add_argument("--sleep", type=float, default=_DEFAULT_SLEEP,
                   help=f"外部API呼び出しの間隔(秒)（既定: {_DEFAULT_SLEEP}）")
    p.add_argument("--execute", action="store_true",
                   help="指定しない場合は対象件数を表示するだけ(dry-run)")
    args = p.parse_args()

    init_db()
    targets = _candidates(args.limit)
    print(f"対象(country取得済み・緯度経度未取得): {len(targets)} 件")
    if not args.execute:
        print("dry-run です。実際に取得するには --execute を付けてください。")
        return 0
    if not targets:
        return 0

    eta = len(targets) * args.sleep
    print(f"取得を開始します（{args.sleep}秒間隔・想定所要 約{eta / 60:.1f}分）")

    ok = failed = 0
    consecutive_failures = 0
    _MAX_CONSECUTIVE = 5
    for i, ip in enumerate(targets, 1):
        # enrich_ip はキャッシュ行があると即returnするため、既存行を
        # 消してから呼ぶ(country/region/city等も含め丸ごと再取得)。
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
                "SELECT country, city, latitude, longitude, error "
                "FROM ip_geo_cache WHERE ip = ?", (ip,),
            ).fetchone()
        if row and row["latitude"] is not None:
            ok += 1
            consecutive_failures = 0
            where = " / ".join(x for x in (row["country"], row["city"]) if x)
            print(f"  [{i}/{len(targets)}] {ip} -> {where} "
                  f"({row['latitude']:.3f}, {row['longitude']:.3f})")
        else:
            failed += 1
            consecutive_failures += 1
            reason = (row["error"] if row else "") or "(緯度経度なしの応答)"
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
        print("失敗分は再実行で再試行されます(成功済みは対象外)。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
