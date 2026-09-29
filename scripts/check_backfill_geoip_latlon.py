"""scripts/backfill_geoip_latlon_2026_09_29.py の検査(2026-09-29)。

隔離した一時DB(DATA_DIR)で、外部APIを模擬して「緯度経度だけを更新し、失敗・食い違い・
不正値のときは既存の行を一切変えない」ことを確認する。本物の外部API・本番DBは使わない。

  .venv/bin/python scripts/check_backfill_geoip_latlon.py     # 0=全部OK
"""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp(prefix="check_geo_")
os.environ["DATA_DIR"] = _tmp
os.environ["MULTIUSER"] = "0"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import db, init_db  # noqa: E402
from app.services import geoip  # noqa: E402
import backfill_geoip_latlon_2026_09_29 as bf  # noqa: E402

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("  OK   " if cond else "  FAIL ") + name + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


# 模擬する外部APIの応答(IPの末尾で振り分ける)
RESP = {
    "1": ({"country": "Japan", "latitude": 35.6812, "longitude": 139.7671}, ""),
    "2": ({}, "fake HTTP 429"),                                             # 失敗(レート制限)
    "3": ({"country": "United States", "latitude": 40.7, "longitude": -74.0}, ""),  # 国が食い違う
    "6": ({"country": "Japan", "latitude": 0.0, "longitude": 0.0}, ""),     # (0,0)は不正
    "7": ({"country": "japan", "latitude": "34.6937", "longitude": "135.5023"}, ""),  # 文字列・大文字小文字違い
    "8": ({"country": "Japan", "latitude": 95.0, "longitude": 10.0}, ""),   # 範囲外
}


def fake_lookup(client, ip):
    return RESP.get(ip.rsplit(".", 1)[-1], ({}, "fake 応答なし"))


def snapshot() -> dict:
    with db() as conn:
        return {r["ip"]: dict(r) for r in conn.execute("SELECT * FROM ip_geo_cache")}


def put(ip, country="Japan", org="Org", host="host.example", lat=None, lon=None, err=""):
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO ip_geo_cache (ip, country, region, city, org, hostname, error, "
            "fetched_at, latitude, longitude) VALUES (?, ?, 'Tokyo', 'Chiyoda', ?, ?, ?, "
            "'2026-09-01 00:00:00', ?, ?)", (ip, country, org, host, err, lat, lon))


init_db()
geoip._PROVIDERS = (("fake", fake_lookup),)

print("== 1. 通常ケース(更新される行・更新されない行)")
put("198.51.100.1", org="OrgA", host="hostA")                       # 成功 → 緯度経度だけ入る
put("198.51.100.2", org="Amazon", host="ec2-x")                     # 失敗 → 何も変えない
put("198.51.100.3", org="OrgC", host="hostC")                       # 国の食い違い → 何も変えない
put("198.51.100.4", org="OrgD", host="hostD", lat=10.0, lon=20.0)   # 既に入っている → 対象外
put("198.51.100.5", country="", org="", host="", err="ipapi.co HTTP 429")  # country空 → 対象外
put("198.51.100.6", org="OrgF", host="hostF")                       # (0,0) → 何も変えない
put("198.51.100.7", org="OrgG", host="hostG")                       # 文字列の緯度経度・国の大小文字違い → 更新される
put("198.51.100.8", org="OrgH", host="hostH")                       # 範囲外 → 何も変えない
before = snapshot()
check("対象件数が6件(1,2,3,6,7,8)", bf.count_candidates() == 6, str(bf.count_candidates()))

s = bf.run(limit=100, sleep=0, execute=False, client=object(), quiet=True)
check("dry-run は何も変更しない", snapshot() == before and s["tried"] == 0)

s = bf.run(limit=100, sleep=0, execute=True, client=object(), quiet=True)
after = snapshot()
check("更新は2件(1と7)", s["updated"] == 2, str(s))
check("失敗3件(2・6・8)", s["failed"] == 3, str(s))
check("国の食い違い1件(3)", s["mismatch"] == 1, str(s))
check("連続失敗の打ち切りは起きていない(失敗が5件未満)", not s["aborted"])

a = after["198.51.100.1"]
check("成功行は緯度経度が入った", abs(a["latitude"] - 35.6812) < 1e-6 and abs(a["longitude"] - 139.7671) < 1e-6)
check("成功行でも他の列は不変(country/region/city/org/hostname/error/fetched_at)",
      all(a[k] == before["198.51.100.1"][k] for k in ("country", "region", "city", "org", "hostname", "error", "fetched_at")))
g = after["198.51.100.7"]
check("文字列の緯度経度と国の大文字小文字違いは更新される", abs(g["latitude"] - 34.6937) < 1e-6)
for ip, why in (("198.51.100.2", "失敗行"), ("198.51.100.3", "国が食い違う行"),
                ("198.51.100.6", "(0,0)の行"), ("198.51.100.8", "範囲外の行")):
    check(f"{why}は完全に不変(組織名・ホスト名も残っている)", after[ip] == before[ip])
check("既に緯度経度がある行は不変", after["198.51.100.4"] == before["198.51.100.4"])
check("country空の行は不変", after["198.51.100.5"] == before["198.51.100.5"])
check("行は1件も消えていない", set(after) == set(before))
check("残りの対象は4件(失敗3+食い違い1)", bf.count_candidates() == 4, str(bf.count_candidates()))

print("== 2. 連続5件の失敗で打ち切る(既存の行は無傷)")
with db() as conn:
    conn.execute("DELETE FROM ip_geo_cache")
for n in range(20, 30):
    put(f"203.0.113.{n}" if False else f"198.51.100.{n}", org=f"Org{n}", host=f"h{n}")   # 末尾20〜29は応答なし=失敗
before2 = snapshot()
s2 = bf.run(limit=100, sleep=0, execute=True, client=object(), quiet=True)
check("5件連続失敗で打ち切る", s2["aborted"] and s2["tried"] == 5 and s2["updated"] == 0, str(s2))
check("打ち切っても既存の行は全て不変", snapshot() == before2)

print("== 3. 実行しても他のテーブルには触れない")
with db() as conn:
    n_tables = conn.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
check("テーブル数は変わらない", n_tables > 0)

print()
if FAILS:
    print(f"❌ 失敗 {len(FAILS)} 件: " + ", ".join(FAILS))
    raise SystemExit(1)
print("✅ すべて成功")
