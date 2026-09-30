"""緯度経度が、同じ行の市区町村・地域ラベルと食い違っていないかの判定(2026-10-01)。

背景: ip_geo_cache の緯度経度は、2026-09-29〜30に「後追い補完」した行が多い。補完は保存済みの
国だけを照合して外部API(ipapi.co→ipwho.is)の緯度経度を採用したため、保存済みの市区町村(古い
照会の結果)とは別の推定に基づく座標が混ざり、「東京」のラベルの点が北陸に出るなどの位置ずれが
起きた(2026-10-01オーナー指摘)。日本の緯度経度ありの行のうち、地域の中央値から100km超は
後追い補完の行で約2割(新規の行は0件)。

対策(描画側): 同じ市区町村(n>=5)/同じ地域(n>=5)の**多数派の位置**から大きく外れた座標は、
**地図の点にしない**(国別/地域別/市区町村別のランキングの件数は従来どおり数える)。
多数派が誤っていることは想定しない(同じ地域の行は同じ応答で保存された行が多いため)。
根拠が足りない(群が小さい)行は、判定せず採用する。

純粋関数のみ(DBに触れない)。テスト: scripts/check_geo_consistency.py
"""
from __future__ import annotations

import math
import statistics
from collections import defaultdict
from typing import Iterable, Mapping

CITY_MIN_ROWS = 5       # この件数以上ある市区町村は、その中央値を基準にする
REGION_MIN_ROWS = 5     # この件数以上ある地域(都道府県/州)は、その中央値を基準にする(小さい群は誤った行に引きずられるため判定しない)
# 中央値からこの距離(km)を超えたら「食い違い」。日本は都道府県・市が小さいので厳しく、
# それ以外(米国の州・ブラジルの州等)は広さに余裕を持たせる(2026-10-01に本番データで調整:
# 米国のバッファローはニューヨーク州の中央値から約470km=正当・ダラスが約1,900km離れた位置は誤り)。
CITY_MAX_KM = {"Japan": 60.0}
CITY_MAX_KM_DEFAULT = 100.0
REGION_MAX_KM = {"Japan": 250.0}
REGION_MAX_KM_DEFAULT = 800.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p = math.pi / 180.0
    a = (math.sin((lat2 - lat1) * p / 2) ** 2
         + math.cos(lat1 * p) * math.cos(lat2 * p) * math.sin((lon2 - lon1) * p / 2) ** 2)
    return 12742.0 * math.asin(min(1.0, math.sqrt(a)))


def _median_point(pts: list[tuple[float, float]]) -> tuple[float, float]:
    return (statistics.median(p[0] for p in pts), statistics.median(p[1] for p in pts))


def inconsistent_ips(rows: Iterable[Mapping]) -> set[str]:
    """rows: ip/country/region/city/latitude/longitude を持つ行(緯度経度のある行のみ渡す)。
    返り値: 「同じ市区町村/地域の多数派の位置から大きく外れている」IPの集合。"""
    rows = [r for r in rows
            if r.get("latitude") is not None and r.get("longitude") is not None
            and (r.get("country") or "")]
    city_pts: dict[tuple, list] = defaultdict(list)
    region_pts: dict[tuple, list] = defaultdict(list)
    for r in rows:
        pt = (float(r["latitude"]), float(r["longitude"]))
        country, region, city = r["country"], (r.get("region") or ""), (r.get("city") or "")
        if region and city:
            city_pts[(country, region, city)].append(pt)
        if region:
            region_pts[(country, region)].append(pt)
    city_ref = {k: _median_point(v) for k, v in city_pts.items() if len(v) >= CITY_MIN_ROWS}
    region_ref = {k: _median_point(v) for k, v in region_pts.items() if len(v) >= REGION_MIN_ROWS}

    bad: set[str] = set()
    for r in rows:
        lat, lon = float(r["latitude"]), float(r["longitude"])
        country, region, city = r["country"], (r.get("region") or ""), (r.get("city") or "")
        ref = limit = None
        if region and city and (country, region, city) in city_ref:
            ref, limit = city_ref[(country, region, city)], CITY_MAX_KM.get(country, CITY_MAX_KM_DEFAULT)
        elif region and (country, region) in region_ref:
            ref, limit = region_ref[(country, region)], REGION_MAX_KM.get(country, REGION_MAX_KM_DEFAULT)
        if ref is not None and haversine_km(lat, lon, ref[0], ref[1]) > limit:
            bad.add(r["ip"])
    return bad
