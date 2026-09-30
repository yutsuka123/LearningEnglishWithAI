"""app/services/geo_consistency.py と admin_geo_map の検査(2026-10-01)。

隔離した一時DB(DATA_DIR)だけを使い、本番・外部APIには触れない。

  .venv/bin/python scripts/check_geo_consistency.py     # 0=全部OK
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp(prefix="check_geocons_")
os.environ["DATA_DIR"] = _tmp
os.environ["MULTIUSER"] = "0"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db, init_db  # noqa: E402
from app.routers import system  # noqa: E402
from app.services import geo_consistency as gc  # noqa: E402

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("  OK   " if cond else "  FAIL ") + name + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def row(ip, country, region, city, lat, lon):
    return {"ip": ip, "country": country, "region": region, "city": city, "latitude": lat, "longitude": lon}


print("== 1. 純粋関数(inconsistent_ips)")
tokyo = [row(f"10.0.0.{i}", "Japan", "Tokyo", "Tokyo", 35.68 + i * 0.01, 139.69 - i * 0.01) for i in range(8)]
far = row("10.0.1.1", "Japan", "Tokyo", "Tokyo", 36.56, 136.66)                     # 北陸(東京から約270km)→食い違い
near = row("10.0.1.2", "Japan", "Tokyo", "Tokyo", 35.47, 139.63)                    # 横浜付近(約25km)→正当
bad = gc.inconsistent_ips(tokyo + [far, near])
check("東京のラベルで北陸の座標は食い違い", "10.0.1.1" in bad)
check("東京のラベルで横浜付近(約25km)は正当", "10.0.1.2" not in bad)
check("東京の多数派は食い違いにならない", not any(r["ip"] in bad for r in tokyo))

small = [row("10.0.2.1", "Germany", "Bavaria", "Augsburg", 48.37, 10.90), row("10.0.2.2", "Germany", "Bavaria", "Munich", 48.14, 11.58)]
check("群が小さい(根拠不足)行は判定せず採用する", gc.inconsistent_ips(small + [row("10.0.2.3", "Germany", "Bavaria", "X", 40.0, 20.0)]) == set())

# 地域レベル(市区町村の群が小さい)・日本は250km・米国は800km
osaka_region = [row(f"10.0.3.{i}", "Japan", "Osaka", f"C{i}", 34.69 + i * 0.01, 135.50) for i in range(6)]
far_osaka = row("10.0.3.9", "Japan", "Osaka", "Z", 35.69, 139.69)                   # 大阪ラベルで東京の座標
check("地域レベル: 日本で250km超は食い違い", "10.0.3.9" in gc.inconsistent_ips(osaka_region + [far_osaka]))
ny = [row(f"10.0.4.{i}", "United States", "New York", "New York City", 40.71, -74.0) for i in range(6)]
buffalo = row("10.0.4.50", "United States", "New York", "Buffalo", 42.89, -78.88)   # 約470km=州内で正当
dallas_bad = row("10.0.4.60", "United States", "New York", "Albany", 32.78, -96.80)  # 約2,500km → 食い違い
b2 = gc.inconsistent_ips(ny + [buffalo, dallas_bad])
check("米国の州内(約470km)は正当", "10.0.4.50" not in b2)
check("米国でも州から約2,500kmは食い違い", "10.0.4.60" in b2)

check("緯度経度の無い行・国が空の行は無視する(例外にならない)",
      gc.inconsistent_ips([row("a", "Japan", "Tokyo", "Tokyo", None, None), row("b", "", "", "", 1.0, 2.0)]) == set())
check("空の入力", gc.inconsistent_ips([]) == set())
check("地域が空の行は判定しない", gc.inconsistent_ips(tokyo + [row("10.0.5.1", "Japan", "", "", 10.0, 10.0)]) == set())

print("== 2. admin_geo_map(隔離DB)")
init_db()
system._require_admin = lambda: None
system.load_admin_known_ips = lambda: set()
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"


def put_geo(ip, country, region, city, lat, lon):
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO ip_geo_cache (ip, country, region, city, org, hostname, error, fetched_at, latitude, longitude) "
            "VALUES (?, ?, ?, ?, '', '', '', '2026-10-01 00:00:00', ?, ?)", (ip, country, region, city, lat, lon))


def visit(ip, n=1):
    with db() as conn:
        for _ in range(n):
            conn.execute(
                "INSERT INTO landing_visits (ip, path, user_agent, kind, success, guest_sid, is_internal, bot_mark) "
                "VALUES (?, '/', ?, 'visit', 0, ?, 0, 0)", (ip, UA, "g-" + ip))


for r in tokyo + [far, near]:
    put_geo(r["ip"], r["country"], r["region"], r["city"], r["latitude"], r["longitude"])
    visit(r["ip"], 2 if r["ip"] == far["ip"] else 1)        # 食い違いの行は2件
# 同じ座標に件数の違う2つのIP: 吹き出しの地名は件数が多い方になる
put_geo("10.9.0.1", "France", "Ile-de-France", "Versailles", 48.85, 2.35)
put_geo("10.9.0.2", "France", "Ile-de-France", "Paris", 48.85, 2.35)
visit("10.9.0.1", 1)
visit("10.9.0.2", 5)
res = system.admin_geo_map(kind="visit", days=30)
pts = res["points"]
check("食い違い行の件数(2)がinconsistent_visitsに出る", res["inconsistent_visits"] == 2, str(res["inconsistent_visits"]))
check("食い違い行の座標は点にならない", not any(abs(p["lat"] - 36.56) < 0.01 for p in pts))
check("食い違い行もランキング(市区町村別)には数える: 東京= 8+1(near)+2(far)=11",
      next(c for c in res["city_ranking"] if c["city"] == "Tokyo")["count"] == 11, str(res["city_ranking"][:2]))
check("位置情報あり件数は食い違い行も含む", res["with_geo"] == res["total"], f"{res['with_geo']}/{res['total']}")
paris = next(p for p in pts if abs(p["lat"] - 48.85) < 0.01)
check("同じ座標の複数IP: 点の件数は合計(6)", paris["count"] == 6, str(paris))
check("同じ座標の複数IP: 吹き出しの地名は件数が多いIP(Paris)", paris["city"] == "Paris", paris["city"])
check("内部用の_bestキーは出力に残らない", all("_best" not in p for p in pts))

print()
if FAILS:
    print(f"❌ 失敗 {len(FAILS)} 件: " + ", ".join(FAILS))
    raise SystemExit(1)
print("✅ すべて成功")
