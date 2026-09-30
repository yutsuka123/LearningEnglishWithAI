"""座標あり行の再照合(2026-10-01・オーナー指示「群が小さくて判定できなかった行も、今後数日かけて厳格版で全件再照合」)。

背景: ip_geo_cache の緯度経度は、2026-09-29〜30の後追い補完(国だけを照合)で入った行が多く、保存済みの
市区町村とは別の推定の座標が混ざっていた(「東京」の点が北陸に出る等)。判定(app/services/geo_consistency.py)で
拾えた75件は2026-10-01にNULLに戻して取り直したが、群が小さく判定できなかった行は未検証のまま残る。
このスクリプトは、**対象の全行を外部API(ipapi.co→ipwho.is)で再照合**する。外部APIの無料枠(1日約1,000件)に
合わせて、1回あたり--limit件(既定450)ずつ、数日に分けて実行する(再開できる・何度実行しても安全)。

対象と進み具合は /data/geo_reverify_20261001.json に保存する(--initで「その時点で座標のある行」をIPのハッシュで記録。
生のIPは保存しない)。--init後に補完(後追い)で座標が入った行は、厳格版で取得済みなので対象に入らない。

1行ごとの判定(保存済み=ラベル+座標 / 応答=事業者の最新の推定):
  same              ラベルが一致(または比べられない)し、座標も50km以内 → 変更しない(検証済み)
  updated           ラベルは一致するが座標が50km超ずれている → 応答の座標に更新(ラベルと整合する座標にする)
  kept_corroborated ラベルは食い違うが、応答の座標が保存済みの座標の100km以内 → 座標は別の照会でも裏付けられたので残す
  nulled            国が違う/ラベルも食い違い座標も遠い → 座標をNULLに戻す(地図に出さない・次の補完で取り直す候補)
  (応答なし/429等)   記録せず次回に回す。5件連続で失敗したら打ち切る(無料枠切れの可能性)

**緯度経度の2列だけを更新する**(他の列は一切変えない)。書き込む回の最初にlogs.dbを別名でバックアップし、
実行後に「実行前からあった行の他の列が変わっていない・消えた行が無い・ログ系の件数が減っていない」を確認して表示する。
出力に生のIPは出ない(件数のみ)。テスト: scripts/check_reverify_geoip_coords.py

使い方(VPSのeigo-appコンテナ内):
  python3 scripts/reverify_geoip_coords.py --init                    # 対象を記録(初回のみ・2回目以降は何もしない)
  python3 scripts/reverify_geoip_coords.py                           # 残り件数の確認のみ(書き込まない・API呼び出しなし)
  python3 scripts/reverify_geoip_coords.py --execute --limit 450 --until 2026-10-06
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import math
import os
import random
import re
import sqlite3
import sys
import time
import unicodedata
from pathlib import Path

try:
    _ROOT = Path(__file__).resolve().parent.parent
except NameError:  # docker exec -i ... python3 - (標準入力)から実行した場合
    _ROOT = Path("/app")
sys.path.insert(0, str(_ROOT))

import httpx  # noqa: E402

from app.config import paths  # noqa: E402
from app.database import db  # noqa: E402
from app.services import geoip  # noqa: E402

STATE_NAME = "geo_reverify_20261001.json"
_DEFAULT_LIMIT = 450
_DEFAULT_SLEEP = 1.2
_MAX_CONSECUTIVE = 5
SAME_KM = 50.0          # 座標がこの距離以内なら「同じ」
CORROBORATE_KM = 100.0  # ラベルが食い違っても、応答の座標がこの距離以内なら座標は裏付けられたとみなす
_JST = dt.timezone(dt.timedelta(hours=9))

_PLACE_NOISE = {"prefecture", "province", "state", "region", "county", "oblast", "city",
                "metropolis", "district"}


def state_path() -> Path:
    return Path(paths.data_dir) / STATE_NAME


def ip_hash(ip: str) -> str:
    return hashlib.sha256(("reverify-" + ip).encode()).hexdigest()[:16]


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p = math.pi / 180.0
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742.0 * math.asin(min(1.0, math.sqrt(a)))


def _norm_place(s: str | None) -> str:
    t = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode("ascii").lower()
    return "".join(w for w in re.sub(r"[^a-z0-9]+", " ", t).split() if w not in _PLACE_NOISE)


def same_place(cached_region: str, cached_city: str, got_region: str, got_city: str) -> bool | None:
    """True=地域か市区町村が一致 / False=比べられるのにどちらも食い違う / None=比べられない
    (scripts/backfill_geoip_latlon_2026_09_29.py の同名関数と同じ判定)。"""
    cr, cc, gr, gc = (_norm_place(x) for x in (cached_region, cached_city, got_region, got_city))
    if not ((cr and gr) or (cc and gc)):
        return None
    return bool(cr and gr and cr == gr) or bool(cc and gc and cc == gc)


def _sane(lat: float, lon: float) -> bool:
    return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0 and not (lat == 0.0 and lon == 0.0)


def lookup_candidates(client: httpx.Client, ip: str, country: str, region: str, city: str
                      ) -> tuple[list[tuple[str, dict, float, float]], list[str]]:
    """事業者を順に引き、座標が取れた応答を集める。ラベルが一致する応答が取れたらそこで止める
    (無料枠の節約)。戻り値: ([(事業者名, 応答, lat, lon)...], エラー一覧)。"""
    cands: list[tuple[str, dict, float, float]] = []
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
        cands.append((name, geo, lat, lon))
        if _country_ok(geo, country) and same_place(region, city, str(geo.get("region") or ""),
                                                    str(geo.get("city") or "")) is not False:
            break
    return cands, errors


def _country_ok(geo: dict, country: str) -> bool:
    got = str(geo.get("country") or "").strip()
    return (not got) or got.casefold() == (country or "").strip().casefold()


def classify(stored: tuple, cands: list[tuple[str, dict, float, float]]
             ) -> tuple[str, float | None, float | None]:
    """stored=(country, region, city, lat, lon)。戻り値: (判定, 新lat, 新lon)。新lat/lonがNoneでも
    判定'nulled'は座標をNULLにする意味(呼び出し側で判定名を見て処理する)。"""
    country, region, city, lat0, lon0 = stored
    for _name, geo, lat, lon in cands:     # ラベルが一致する応答があればそれを採用
        if _country_ok(geo, country) and same_place(region, city, str(geo.get("region") or ""),
                                                    str(geo.get("city") or "")) is not False:
            if haversine_km(lat0, lon0, lat, lon) <= SAME_KM:
                return "same", None, None
            return "updated", lat, lon
    _name, geo, lat, lon = cands[0]        # 一致する応答が無い=食い違いの応答だけ
    if _country_ok(geo, country) and haversine_km(lat0, lon0, lat, lon) <= CORROBORATE_KM:
        return "kept_corroborated", None, None
    return "nulled", None, None


# --- 状態(対象と進み具合) -------------------------------------------------------
def _load_state() -> dict | None:
    p = state_path()
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def _save_state(st: dict) -> None:
    p = state_path()
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, p)


def init_state() -> dict:
    """その時点で座標のある行を対象として記録する(既にあれば何もしない)。"""
    st = _load_state()
    if st is not None:
        return {"created": False, "targets": len(st["targets"]), "done": len(st["done"])}
    with db() as conn:
        rows = conn.execute(
            "SELECT ip FROM ip_geo_cache WHERE latitude IS NOT NULL AND longitude IS NOT NULL "
            "AND COALESCE(country, '') != ''").fetchall()
    st = {"created_at": dt.datetime.now(_JST).strftime("%F %T JST"),
          "targets": sorted(ip_hash(r["ip"]) for r in rows), "done": {}}
    _save_state(st)
    return {"created": True, "targets": len(st["targets"]), "done": 0}


def _snapshot() -> tuple[dict, dict]:
    with db() as conn:
        rows = {r["ip"]: tuple(r) for r in conn.execute(
            "SELECT ip, country, region, city, org, hostname, error, fetched_at FROM ip_geo_cache")}
        logs = {t: conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
                for t in ("landing_visits", "usage_events", "client_errors")}
    return rows, logs


def _backup_logs_db() -> str:
    src = Path(paths.data_dir) / "logs.db"
    stamp = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    dst = Path(paths.data_dir) / f"backup_logs_manual_{stamp}_before_geo_reverify.db"
    s = sqlite3.connect(f"file:{src}?mode=ro", uri=True)
    d = sqlite3.connect(str(dst))
    s.backup(d)
    ok = d.execute("PRAGMA integrity_check").fetchone()[0]
    d.close()
    s.close()
    if ok != "ok":
        raise RuntimeError(f"バックアップの整合性が ok ではありません({dst.name})")
    return dst.name


def run(limit: int = _DEFAULT_LIMIT, sleep: float = _DEFAULT_SLEEP, execute: bool = False,
        until: str | None = None, client: httpx.Client | None = None, quiet: bool = False,
        backup: bool = True) -> dict:
    stats = {"pending_before": 0, "tried": 0, "same": 0, "updated": 0, "kept_corroborated": 0,
             "nulled": 0, "retry": 0, "skipped": 0, "aborted": False, "expired": False,
             "changed_other_cols": 0, "lost_rows": 0, "logs_decreased": [], "backup": ""}
    st = _load_state()
    if st is None:
        raise SystemExit("対象が未記録です。先に --init を実行してください。")
    if until:
        today = dt.datetime.now(_JST).date()
        if today > dt.date.fromisoformat(until):
            stats["expired"] = True
            return stats
    pending = set(st["targets"]) - set(st["done"])
    stats["pending_before"] = len(pending)
    if not execute or not pending:
        return stats

    with db() as conn:
        rows = conn.execute(
            "SELECT ip, country, region, city, latitude, longitude FROM ip_geo_cache "
            "WHERE latitude IS NOT NULL AND longitude IS NOT NULL").fetchall()
    by_hash = {ip_hash(r["ip"]): r for r in rows}
    # 座標が既に無い行(判定でNULL化済み等)・消えた行は対象外として片付ける
    for h in list(pending):
        if h not in by_hash:
            st["done"][h] = {"at": dt.datetime.now(_JST).strftime("%F %T"), "result": "skipped"}
            pending.discard(h)
            stats["skipped"] += 1
    targets = random.sample(sorted(pending), min(limit, len(pending)))
    if not targets:
        _save_state(st)
        return stats

    if backup:
        stats["backup"] = _backup_logs_db()
    before_rows, before_logs = _snapshot()
    own = client is None
    client = client or httpx.Client(timeout=geoip._TIMEOUT)
    consecutive = 0
    try:
        for i, h in enumerate(targets, 1):
            r = by_hash[h]
            stats["tried"] += 1
            cands, errs = lookup_candidates(client, r["ip"], r["country"], r["region"] or "", r["city"] or "")
            if not cands:
                stats["retry"] += 1
                consecutive += 1
                if not quiet:
                    print(f"  [{i}/{len(targets)}] {r['country']}: 応答なし({(errs[0] if errs else '?')[:50]})・次回に回す")
                if consecutive >= _MAX_CONSECUTIVE:
                    stats["aborted"] = True
                    if not quiet:
                        print(f"  {_MAX_CONSECUTIVE}件連続で失敗したため中断します(無料枠切れ/障害の可能性)。次回に続きを行います。")
                    break
            else:
                consecutive = 0
                result, nlat, nlon = classify(
                    (r["country"], r["region"] or "", r["city"] or "", r["latitude"], r["longitude"]), cands)
                if result == "updated":
                    with db() as conn:
                        conn.execute("UPDATE ip_geo_cache SET latitude = ?, longitude = ? WHERE ip = ?",
                                     (nlat, nlon, r["ip"]))
                elif result == "nulled":
                    with db() as conn:
                        conn.execute("UPDATE ip_geo_cache SET latitude = NULL, longitude = NULL WHERE ip = ?",
                                     (r["ip"],))
                stats[result] += 1
                st["done"][h] = {"at": dt.datetime.now(_JST).strftime("%F %T"), "result": result}
                if not quiet:
                    print(f"  [{i}/{len(targets)}] {r['country']}: {result}")
            if i % 20 == 0:
                _save_state(st)
            if i < len(targets) and sleep > 0:
                time.sleep(sleep)
    finally:
        _save_state(st)
        if own:
            client.close()

    after_rows, after_logs = _snapshot()
    stats["changed_other_cols"] = sum(1 for ip, t in before_rows.items() if after_rows.get(ip) != t)
    stats["lost_rows"] = sum(1 for ip in before_rows if ip not in after_rows)
    stats["logs_decreased"] = [k for k in before_logs if after_logs[k] < before_logs[k]]
    return stats


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--init", action="store_true", help="対象(いま座標のある行)を記録する(初回のみ)")
    ap.add_argument("--execute", action="store_true", help="実際に外部APIを引いて更新する(指定しなければ件数の確認のみ)")
    ap.add_argument("--limit", type=int, default=_DEFAULT_LIMIT, help=f"1回あたりの最大件数(既定 {_DEFAULT_LIMIT})")
    ap.add_argument("--sleep", type=float, default=_DEFAULT_SLEEP, help=f"1件ごとの待ち秒数(既定 {_DEFAULT_SLEEP})")
    ap.add_argument("--until", default=None, help="この日付(JST・YYYY-MM-DD)を過ぎたら何もしない(cronの消し忘れ対策)")
    args = ap.parse_args()

    if args.init:
        print("対象の記録:", init_state())
        return 0
    s = run(limit=args.limit, sleep=args.sleep, execute=args.execute, until=args.until)
    if s["expired"]:
        print(f"期限({args.until})を過ぎているため何もしません。cronの行を削除してください。")
        return 0
    if not args.execute:
        print(f"残りの対象: {s['pending_before']} 件(書き込み・外部API呼び出しは行っていません。--execute で実行)")
        return 0
    print(f"完了: 判定 same={s['same']} updated={s['updated']} kept_corroborated={s['kept_corroborated']} "
          f"nulled={s['nulled']} / 次回に回す {s['retry']} / 対象外 {s['skipped']} / "
          f"実行前の残り {s['pending_before']} 件 / 打ち切り={s['aborted']}")
    print(f"確認: 他列の変更 {s['changed_other_cols']}件 {'✅' if s['changed_other_cols'] == 0 else '⚠️ 要確認'} / "
          f"消えた行 {s['lost_rows']}件 {'✅' if s['lost_rows'] == 0 else '⚠️ 要確認'} / "
          f"ログ系の減少 {s['logs_decreased'] or 'なし ✅'} / バックアップ {s['backup'] or '-'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
