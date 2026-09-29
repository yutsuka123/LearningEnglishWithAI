"""ip_geo_cache に国等は既にあるが緯度経度が未保存の行へ、緯度経度**だけ**を後追いで入れる
一回限りのスクリプト(2026-09-29・アクセスログの地理的可視化用)。

latitude/longitude 列は2026-09-29(ver1.5.6)に追加した(app/database.py)。それより前に
enrich_ip() でキャッシュ済みだった行は、外部APIのJSONに緯度経度が含まれていても保存して
いなかったため空のまま。enrich_ip() は「キャッシュ済みのIPは何もしない」ので、新しい訪問者
以外は自然には埋まらない(=管理画面の地図に点が出ない・「地図上の点は0地点」)。

**2026-09-29(夜)に作り直した(初版は危険だった)**: 初版は「既存行をDELETEしてenrich_ip()で
丸ごと再取得」だったため、外部APIが失敗すると国/地域/市区/**組織名/ホスト名**が空の行で置き換わって
しまう(組織名・ホスト名はボット判定 visitor_kind.classify にも使うので、失うと統計が変わる)。
失われた行は「country が空」になり次回の対象からも外れる。→ **緯度経度だけをUPDATEする**方式にした。
  - 行は消さない・他の列(country/region/city/org/hostname/error/fetched_at)は一切変えない。
  - 取得に失敗したら何も変更しない(次回の実行で再試行される)。
  - 外部APIが返した国が、保存済みのcountryと食い違う場合は更新しない(IPの割り当て変更などで
    地図の点とランキングが矛盾するのを避ける)。
  - 画面/ログに生のIPを出さない。

外部APIのレート制限に対する安全策は scripts/backfill_geoip.py と同じ(既定1.2秒間隔・連続失敗5回で
打ち切り)。第一候補 ipapi.co が429などで失敗したら ipwho.is に切り替わる(geoip._PROVIDERS)。

使い方(VPS上、eigo-appコンテナの中で実行を想定):
  docker exec eigo-app python3 scripts/backfill_geoip_latlon_2026_09_29.py             # 件数確認のみ
  docker exec eigo-app python3 scripts/backfill_geoip_latlon_2026_09_29.py --execute --limit 300
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402

from app.database import db, init_db  # noqa: E402
from app.services import geoip  # noqa: E402

_DEFAULT_SLEEP = 1.2
_DEFAULT_LIMIT = 300
_MAX_CONSECUTIVE = 5


def count_candidates() -> int:
    with db() as conn:
        return conn.execute(
            "SELECT COUNT(*) FROM ip_geo_cache "
            "WHERE COALESCE(country, '') != '' AND latitude IS NULL").fetchone()[0]


def _candidates(limit: int) -> list[tuple[str, str]]:
    """(ip, 保存済みのcountry)。毎回ランダムな順で取る(取れないIPが先頭に居座って
    他の行が後回しにならないようにするため)。"""
    with db() as conn:
        rows = conn.execute(
            "SELECT ip, country FROM ip_geo_cache "
            "WHERE COALESCE(country, '') != '' AND latitude IS NULL "
            "ORDER BY RANDOM() LIMIT ?", (limit,)).fetchall()
    return [(r["ip"], r["country"]) for r in rows]


def _sane(lat: float, lon: float) -> bool:
    if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
        return False
    return not (lat == 0.0 and lon == 0.0)   # (0,0)は「不明」の代わりに返されがち


def fetch_latlon(client: httpx.Client, ip: str, cached_country: str
                 ) -> tuple[float | None, float | None, str]:
    """緯度経度だけを取得して (lat, lon, error) を返す。error が空でなければ「更新しない」。"""
    errors: list[str] = []
    for name, lookup in geoip._PROVIDERS:
        try:
            geo, err = lookup(client, ip)
        except Exception as e:  # noqa: BLE001 — 個別事業者の失敗は次へ
            geo, err = {}, f"{name} {type(e).__name__}"
        lat = geoip._to_float(geo.get("latitude"))
        lon = geoip._to_float(geo.get("longitude"))
        if lat is None or lon is None or not _sane(lat, lon):
            errors.append(err or f"{name} 緯度経度なしの応答")
            continue
        got_country = str(geo.get("country") or "").strip()
        if got_country and got_country.casefold() != cached_country.strip().casefold():
            return None, None, f"国が食い違う({name})のため更新しない"
        return lat, lon, ""
    return None, None, " / ".join(errors) or "緯度経度なし"


def run(limit: int = _DEFAULT_LIMIT, sleep: float = _DEFAULT_SLEEP,
        execute: bool = False, client: httpx.Client | None = None,
        quiet: bool = False) -> dict:
    """取得して UPDATE する。結果の集計を返す(テストからも呼べる)。"""
    stats = {"candidates_total": count_candidates(), "tried": 0, "updated": 0,
             "failed": 0, "mismatch": 0, "aborted": False}
    if not execute:
        return stats
    own = client is None
    client = client or httpx.Client(timeout=geoip._TIMEOUT)
    consecutive = 0
    try:
        targets = _candidates(limit)
        for i, (ip, country) in enumerate(targets, 1):
            stats["tried"] += 1
            lat, lon, err = fetch_latlon(client, ip, country)
            if err:
                stats["mismatch" if "食い違う" in err else "failed"] += 1
                consecutive += 1
                if not quiet:
                    print(f"  [{i}/{len(targets)}] {country}: 更新しない({err})")
                if consecutive >= _MAX_CONSECUTIVE:
                    stats["aborted"] = True
                    if not quiet:
                        print(f"  {_MAX_CONSECUTIVE}件連続で失敗したため中断します"
                              "(外部APIのレート上限/障害の可能性)。時間をおいて再実行してください。")
                    break
            else:
                consecutive = 0
                with db() as conn:
                    # 緯度経度だけを更新(他の列は触らない)。既に入っていれば何もしない。
                    cur = conn.execute(
                        "UPDATE ip_geo_cache SET latitude = ?, longitude = ? "
                        "WHERE ip = ? AND latitude IS NULL", (lat, lon, ip))
                    stats["updated"] += cur.rowcount
                if not quiet:
                    print(f"  [{i}/{len(targets)}] {country}: ({lat:.2f}, {lon:.2f})")
            if i < len(targets) and sleep > 0:
                time.sleep(sleep)
    finally:
        if own:
            client.close()
    return stats


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
    total = count_candidates()
    print(f"対象(country取得済み・緯度経度未取得): {total} 件"
          f"(今回の実行では最大 {min(total, args.limit)} 件)")
    if not args.execute:
        print("dry-run です。実際に取得するには --execute を付けてください。")
        return 0
    if total == 0:
        return 0
    print(f"取得を開始します({args.sleep}秒間隔・想定所要 約{min(total, args.limit) * args.sleep / 60:.1f}分)")
    s = run(limit=args.limit, sleep=args.sleep, execute=True)
    print(f"完了: 更新 {s['updated']} 件 / 失敗 {s['failed']} 件 / 国の食い違いで見送り {s['mismatch']} 件"
          f" / 残りの対象 {count_candidates()} 件" + (" / 連続失敗で中断" if s["aborted"] else ""))
    if s["failed"] or s["mismatch"]:
        print("更新しなかった行は何も変更していません(再実行で再試行されます)。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
