"""scripts/reverify_geoip_coords.py の検査(2026-10-01)。

隔離した一時DB(DATA_DIR)と模擬の外部APIだけを使う。本物の外部API・本番DBには触れない。

  .venv/bin/python scripts/check_reverify_geoip_coords.py     # 0=全部OK
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import tempfile
from pathlib import Path

_tmp = tempfile.mkdtemp(prefix="check_reverify_")
os.environ["DATA_DIR"] = _tmp
os.environ["MULTIUSER"] = "0"
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import db, init_db  # noqa: E402
from app.services import geoip  # noqa: E402
import reverify_geoip_coords as rv  # noqa: E402

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("  OK   " if cond else "  FAIL ") + name + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def put(ip, country="Japan", region="Tokyo", city="Chiyoda", lat=None, lon=None, org="Org", host="h.example"):
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO ip_geo_cache (ip, country, region, city, org, hostname, error, fetched_at, latitude, longitude) "
            "VALUES (?, ?, ?, ?, ?, ?, '', '2026-09-01 00:00:00', ?, ?)", (ip, country, region, city, org, host, lat, lon))


def snap():
    with db() as conn:
        return {r["ip"]: dict(r) for r in conn.execute("SELECT * FROM ip_geo_cache")}


# 模擬の外部API(IPの末尾で振り分け)。事業者A=fake・B=fakeB
TOKYO = (35.68, 139.69)
RESP_A = {
    "1": ({"country": "Japan", "region": "Tokyo", "city": "Chiyoda", "latitude": 35.70, "longitude": 139.75}, ""),        # same(約6km)
    "2": ({"country": "Japan", "region": "Tokyo Metropolis", "city": "X", "latitude": 35.68, "longitude": 139.69}, ""),   # updated(保存は大阪付近)
    "3": ({"country": "Japan", "region": "Niigata", "city": "Niigata", "latitude": 37.92, "longitude": 139.04}, ""),      # 食い違い+座標が保存と近い→kept
    "4": ({"country": "Japan", "region": "Niigata", "city": "Niigata", "latitude": 37.92, "longitude": 139.04}, ""),      # 食い違い+座標が遠い→nulled
    "5": ({"country": "United States", "region": "Texas", "city": "Dallas", "latitude": 32.78, "longitude": -96.8}, ""),  # 国が違う→nulled
    "6": ({}, "fake HTTP 429"),                                                                                          # 失敗→retry
    "7": ({"country": "Japan", "region": "Niigata", "city": "Niigata", "latitude": 37.92, "longitude": 139.04}, ""),      # Aは食い違い→Bで一致
    "8": ({"country": "Japan", "region": "", "city": "", "latitude": 35.0, "longitude": 135.0}, ""),                       # 応答に地域・市が無い(比べられない)+座標遠い→updated
}
RESP_B = {
    "7": ({"country": "Japan", "region": "Tokyo", "city": "Chiyoda", "latitude": 35.69, "longitude": 139.70}, ""),        # 一致・保存と近い→same
}


def fake_a(client, ip):
    return RESP_A.get(ip.rsplit(".", 1)[-1], ({}, "fake 応答なし"))


def fake_b(client, ip):
    return RESP_B.get(ip.rsplit(".", 1)[-1], ({}, "fakeB 応答なし"))


init_db()
geoip._PROVIDERS = (("fake", fake_a), ("fakeB", fake_b))

print("== 1. 単体(判定・照合)")
check("haversine: 東京-大阪は約400km", 380 < rv.haversine_km(35.68, 139.69, 34.69, 135.50) < 420)
check("same_place: Tokyo Metropolis = Tokyo", rv.same_place("Tokyo", "", "Tokyo Metropolis", "") is True)
check("same_place: 比べられない→None", rv.same_place("Tokyo", "Chiyoda", "", "") is None)
check("same_place: 両方食い違い→False", rv.same_place("Tokyo", "Chiyoda", "Niigata", "Niigata") is False)

print("== 2. 状態(--init・再実行・未初期化)")
try:
    rv.run(execute=True, client=object(), sleep=0, quiet=True)
    check("--init前の実行は中止", False)
except SystemExit:
    check("--init前の実行は中止", True)

put("198.51.100.1", lat=35.68, lon=139.69)
put("198.51.100.2", lat=34.69, lon=135.50)
put("198.51.100.3", lat=37.90, lon=139.00)                           # 保存ラベルはTokyoだが座標は新潟付近
put("198.51.100.4", lat=36.56, lon=136.66)                           # 保存ラベルはTokyoで座標は北陸(応答=新潟とも約200km離れ)
put("198.51.100.5", lat=35.0, lon=135.0)
put("198.51.100.6", lat=35.0, lon=135.0)
put("198.51.100.7", lat=35.68, lon=139.69)
put("198.51.100.8", lat=35.68, lon=139.69)
put("198.51.100.9")                                                  # 座標なし→対象外
put("198.51.100.10", country="", lat=1.0, lon=2.0)                   # country空→対象外
r = rv.init_state()
check("対象は座標ありの8件(9=座標なし・10=country空は対象外)", r == {"created": True, "targets": 8, "done": 0}, str(r))
check("2回目の--initは何もしない", rv.init_state() == {"created": False, "targets": 8, "done": 0})
st = json.loads(rv.state_path().read_text(encoding="utf-8"))
check("状態ファイルに生のIPは入らない(ハッシュのみ)", not any("198.51.100" in h for h in st["targets"]) and all(len(h) == 16 for h in st["targets"]))

print("== 3. 確認のみ(既定)は何も変えない・APIを呼ばない")
before = snap()
s = rv.run(execute=False, client=object(), sleep=0, quiet=True)
check("残り8件と表示・DBは不変・試行0", s["pending_before"] == 8 and s["tried"] == 0 and snap() == before)

print("== 4. 実行(--limit 5で5件 → 残り3件を再開)")
s1 = rv.run(limit=5, execute=True, client=object(), sleep=0, quiet=True, backup=True)
check("5件試行", s1["tried"] == 5, str(s1))
check("バックアップが作られた", bool(s1["backup"]) and (Path(_tmp) / s1["backup"]).exists(), s1["backup"])
check("確認: 他列の変更0・消えた行0・ログ系の減少なし", s1["changed_other_cols"] == 0 and s1["lost_rows"] == 0 and not s1["logs_decreased"], str(s1))
s2 = rv.run(limit=50, execute=True, client=object(), sleep=0, quiet=True, backup=False)
check("残りを再開して処理(再試行分を含め合計で8件を1回ずつ)", s1["tried"] + s2["tried"] >= 8, f"{s1['tried']}+{s2['tried']}")
total = {k: s1[k] + s2[k] for k in ("same", "updated", "kept_corroborated", "nulled", "retry")}
retry = total.pop("retry")
check("判定の内訳: same2(1,7)・updated2(2,8)・kept1(3)・nulled2(4,5)", total == {"same": 2, "updated": 2, "kept_corroborated": 1, "nulled": 2}, str(total))
check("失敗の行(6)は「次回に回す」と数えられる(ランダムな選び方で1回目/2回目の両方に入ることがあるので1〜2)", retry in (1, 2), str(retry))
a = snap()
check("same: 座標は変わらない", (a["198.51.100.1"]["latitude"], a["198.51.100.1"]["longitude"]) == (35.68, 139.69))
check("updated: ラベルが一致する応答の座標に更新", abs(a["198.51.100.2"]["latitude"] - 35.68) < 1e-6 and abs(a["198.51.100.2"]["longitude"] - 139.69) < 1e-6)
check("kept_corroborated: 座標は残る", a["198.51.100.3"]["latitude"] == 37.90)
check("nulled(ラベルも食い違い座標も遠い): 緯度経度がNULL", a["198.51.100.4"]["latitude"] is None and a["198.51.100.4"]["longitude"] is None)
check("nulled(国が違う): 緯度経度がNULL", a["198.51.100.5"]["latitude"] is None)
check("比べられない応答+座標が遠い: 応答の座標に更新", abs(a["198.51.100.8"]["latitude"] - 35.0) < 1e-6)
check("事業者Aが食い違っても、事業者Bで一致すれば同じ(same)", (a["198.51.100.7"]["latitude"], a["198.51.100.7"]["longitude"]) == (35.68, 139.69))
check("失敗した行(6)は完全に不変", a["198.51.100.6"] == before["198.51.100.6"])
for ip in before:
    if ip in ("198.51.100.4", "198.51.100.5", "198.51.100.2", "198.51.100.8"):
        continue
    check(f"{ip[-2:].lstrip('.')}: 緯度経度以外の列は不変", all(a[ip][k] == before[ip][k] for k in ("country", "region", "city", "org", "hostname", "error", "fetched_at")))
for ip in ("198.51.100.4", "198.51.100.5", "198.51.100.2", "198.51.100.8"):
    check(f"{ip.rsplit('.', 1)[-1]}: 更新/NULL化した行でも他列(org/hostname等)は不変",
          all(a[ip][k] == before[ip][k] for k in ("country", "region", "city", "org", "hostname", "error", "fetched_at")))
check("座標なし(9)・country空(10)の行は不変", a["198.51.100.9"] == before["198.51.100.9"] and a["198.51.100.10"] == before["198.51.100.10"])
check("行は1件も消えていない", set(a) == set(before))
st = json.loads(rv.state_path().read_text(encoding="utf-8"))
check("済みは7件(失敗の6は未完了として残る)", len(st["done"]) == 7 and rv.ip_hash("198.51.100.6") not in st["done"], str(len(st["done"])))
RESP_A["6"] = ({"country": "Japan", "region": "Tokyo", "city": "Chiyoda", "latitude": 35.69, "longitude": 139.70}, "")   # 次回は取れる(保存の座標(35.0,135.0)は遠い)
s3 = rv.run(limit=50, execute=True, client=object(), sleep=0, quiet=True, backup=False)
check("失敗した行は次回に再照合される(ラベル一致・座標が遠い→updated)", s3["tried"] == 1 and s3["updated"] == 1, str(s3))
check("次回の再照合で座標が応答の値になる", abs(snap()["198.51.100.6"]["latitude"] - 35.69) < 1e-6)
check("全件済みで残り0", rv.run(execute=False, client=object(), sleep=0, quiet=True)["pending_before"] == 0)

print("== 5. 連続5件失敗で打ち切り(状態・行は無傷)")
os.remove(rv.state_path())
with db() as conn:
    conn.execute("DELETE FROM ip_geo_cache")
for n in range(20, 30):
    put(f"198.51.100.{n}", lat=35.0, lon=135.0)                      # 末尾20〜29は応答なし=失敗
rv.init_state()
b5 = snap()
s5 = rv.run(limit=100, execute=True, client=object(), sleep=0, quiet=True, backup=False)
check("5件連続失敗で打ち切る", s5["aborted"] and s5["tried"] == 5 and s5["retry"] == 5, str(s5))
check("打ち切っても行は全て不変・済みは0件", snap() == b5 and not json.loads(rv.state_path().read_text(encoding="utf-8"))["done"])

print("== 6. 期限(--until)を過ぎたら何もしない")
yesterday = (dt.datetime.now(rv._JST).date() - dt.timedelta(days=1)).isoformat()
s6 = rv.run(limit=100, execute=True, client=object(), sleep=0, quiet=True, until=yesterday, backup=False)
check("期限切れは何も試さない", s6["expired"] and s6["tried"] == 0 and snap() == b5)
tomorrow = (dt.datetime.now(rv._JST).date() + dt.timedelta(days=1)).isoformat()
check("期限前なら実行される(応答なしなので打ち切りまで試す)", rv.run(limit=100, execute=True, client=object(), sleep=0, quiet=True, until=tomorrow, backup=False)["tried"] == 5)

print()
if FAILS:
    print(f"❌ 失敗 {len(FAILS)} 件: " + ", ".join(FAILS))
    raise SystemExit(1)
print("✅ すべて成功")
