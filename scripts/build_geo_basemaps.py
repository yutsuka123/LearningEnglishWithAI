"""管理画面のアクセスログ地図表示(2026-09-29〜)用の背景地図データを、
Natural Earth(パブリックドメイン・出典表記も不要。
https://www.naturalearthdata.com/about/terms-of-use/ )のGeoJSONから
生成するビルドスクリプト(実行時にはネットに一切出ない・事前に一度だけ
実行して static/js/geo_basemaps.js を作る/更新する用)。

地図タイルや外部の描画ライブラリをCDNから読むと、本アプリが今まで
守ってきた「外部への実行時通信は増やさない」方針(Googleタグの抑制方針・
CSP等)を崩すため、簡略化した海岸線パスをこのファイル(ビルド成果物)に
埋め込み、実行時はstatic配下の自前JSを読むだけにする。

世界地図＝ne_110m_admin_0_countries(粗い・世界全体を小さく表示するには
十分)、日本地図＝ne_50m_admin_0_countries から日本だけ抽出(1か国分だけ
なのでファイルサイズは小さいまま、110mより形が分かりやすい)。

使い方:
  1. 元データを取得(このスクリプトはネットに出ない・手動で用意する):
     curl -o /tmp/ne_110m.json \\
       https://raw.githubusercontent.com/nvkelso/natural-earth-vector/\\
master/geojson/ne_110m_admin_0_countries.geojson
     curl -o /tmp/ne_50m.json \\
       https://raw.githubusercontent.com/nvkelso/natural-earth-vector/\\
master/geojson/ne_50m_admin_0_countries.geojson
  2. python3 scripts/build_geo_basemaps.py \\
       --world /tmp/ne_110m.json --japan-source /tmp/ne_50m.json
     → static/js/geo_basemaps.js を生成/上書き。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_PATH = ROOT / "static" / "js" / "geo_basemaps.js"

# 世界地図: 経度[-180,180]→x[0,720]、緯度[-90,90]→y[0,360](y反転)。
_WORLD_SCALE = 2.0
_WORLD_W, _WORLD_H = 360 * _WORLD_SCALE, 180 * _WORLD_SCALE
# 日本地図: このバウンディングボックス(本州・北海道・九州・沖縄まで)を
# viewBox 0..W / 0..H に収める。
_JP_LON0, _JP_LON1 = 122.5, 154.5
_JP_LAT0, _JP_LAT1 = 20.0, 46.0
_JP_SCALE = 8.0
_JP_W = (_JP_LON1 - _JP_LON0) * _JP_SCALE
_JP_H = (_JP_LAT1 - _JP_LAT0) * _JP_SCALE


def _simplify(points: list[tuple[float, float]],
              tolerance: float) -> list[tuple[float, float]]:
    """Douglas-Peucker法によるポリラインの間引き(外部ライブラリ不使用)。"""
    if len(points) < 3:
        return points

    def _perp_dist(p, a, b):
        (x, y), (ax, ay), (bx, by) = p, a, b
        dx, dy = bx - ax, by - ay
        if dx == 0 and dy == 0:
            return ((x - ax) ** 2 + (y - ay) ** 2) ** 0.5
        t = ((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy)
        px, py = ax + t * dx, ay + t * dy
        return ((x - px) ** 2 + (y - py) ** 2) ** 0.5

    def _rdp(pts):
        if len(pts) < 3:
            return pts
        a, b = pts[0], pts[-1]
        idx, dmax = -1, 0.0
        for i in range(1, len(pts) - 1):
            d = _perp_dist(pts[i], a, b)
            if d > dmax:
                idx, dmax = i, d
        if dmax > tolerance:
            left = _rdp(pts[:idx + 1])
            right = _rdp(pts[idx:])
            return left[:-1] + right
        return [a, b]

    return _rdp(points)


def _rings(geom: dict) -> list[list[tuple[float, float]]]:
    """Polygon/MultiPolygonの外周・内周リング(lon,lat)をすべて返す。"""
    out: list[list[tuple[float, float]]] = []
    t = geom.get("type")
    if t == "Polygon":
        polys = [geom["coordinates"]]
    elif t == "MultiPolygon":
        polys = geom["coordinates"]
    else:
        return out
    for poly in polys:
        for ring in poly:
            out.append([(pt[0], pt[1]) for pt in ring])
    return out


def _project_world(lon: float, lat: float) -> tuple[float, float]:
    x = (lon + 180.0) * _WORLD_SCALE
    y = (90.0 - lat) * _WORLD_SCALE
    return x, y


def _project_japan(lon: float, lat: float) -> tuple[float, float]:
    x = (lon - _JP_LON0) * _JP_SCALE
    y = (_JP_LAT1 - lat) * _JP_SCALE
    return x, y


def _ring_area(ring: list[tuple[float, float]]) -> float:
    """(近似)符号なし面積。小さい島を間引く閾値判定用。"""
    a = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]
        x2, y2 = ring[i + 1]
        a += x1 * y2 - x2 * y1
    return abs(a) / 2.0


def _build_path(rings_lonlat: list[list[tuple[float, float]]],
                 project, simplify_tol: float,
                 min_points: int, min_area: float) -> str:
    segs = []
    for ring in rings_lonlat:
        projected = [project(lon, lat) for lon, lat in ring]
        simplified = _simplify(projected, simplify_tol)
        if len(simplified) < min_points:
            continue
        if _ring_area(simplified) < min_area:
            continue
        d = ("M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in simplified)
             + " Z")
        segs.append(d)
    return " ".join(segs)


def build_world(path: Path) -> tuple[str, str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rings: list[list[tuple[float, float]]] = []
    for feat in data["features"]:
        rings.extend(_rings(feat["geometry"]))
    d = _build_path(rings, _project_world, simplify_tol=0.6,
                     min_points=4, min_area=3.0)
    view_box = f"0 0 {_WORLD_W:.0f} {_WORLD_H:.0f}"
    proj = {"lon0": -180.0, "lat1": 90.0, "scale": _WORLD_SCALE}
    return view_box, d, proj


def build_japan(path: Path) -> tuple[str, str, dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    rings: list[list[tuple[float, float]]] = []
    for feat in data["features"]:
        props = feat.get("properties", {})
        name = props.get("ADMIN") or props.get("SOVEREIGNT") or ""
        if name != "Japan":
            continue
        rings.extend(_rings(feat["geometry"]))
    if not rings:
        raise SystemExit("Japan の地物が見つかりませんでした"
                          "(--japan-source のADMIN/SOVEREIGNT列を確認)")
    d = _build_path(rings, _project_japan, simplify_tol=0.03,
                     min_points=4, min_area=0.05)
    view_box = f"0 0 {_JP_W:.0f} {_JP_H:.0f}"
    proj = {"lon0": _JP_LON0, "lat1": _JP_LAT1, "scale": _JP_SCALE}
    return view_box, d, proj


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--world", required=True, type=Path,
                    help="ne_110m_admin_0_countries.geojson へのパス")
    p.add_argument("--japan-source", required=True, type=Path,
                    help="ne_50m_admin_0_countries.geojson へのパス"
                         "(この中から日本だけ抽出する)")
    args = p.parse_args()

    world_vb, world_d, world_proj = build_world(args.world)
    print(f"world: viewBox={world_vb} path_len={len(world_d)}")
    japan_vb, japan_d, japan_proj = build_japan(args.japan_source)
    print(f"japan: viewBox={japan_vb} path_len={len(japan_d)}")

    def entry(view_box: str, d: str, proj: dict) -> str:
        return ("{viewBox: " + json.dumps(view_box)
                + ", path: " + json.dumps(d)
                + ", proj: " + json.dumps(proj) + "}")

    js = (
        "// 自動生成ファイル(scripts/build_geo_basemaps.py)。\n"
        "// 元データ: Natural Earth(パブリックドメイン・出典表記不要。\n"
        "// https://www.naturalearthdata.com/about/terms-of-use/)。\n"
        "// 手で編集しないこと(再生成すると上書きされる)。\n"
        "// proj: 経緯度→SVG座標の変換式\n"
        "//   x = (lon - lon0) * scale, y = (lat1 - lat) * scale\n"
        "window.GEO_BASEMAPS = {\n"
        f"  world: {entry(world_vb, world_d, world_proj)},\n"
        f"  japan: {entry(japan_vb, japan_d, japan_proj)},\n"
        "};\n"
    )
    OUT_PATH.write_text(js, encoding="utf-8")
    print(f"書き出し完了: {OUT_PATH} ({OUT_PATH.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
