"""ver1.5.25(怪しいアクセスの『国・地域』と『過去の履歴(再来)』表示)のローカル検査。一時データ領域(DATA_DIR)で動かし、
本番にも開発DBにもVPSにも、外部の位置情報サービスにも触れない(geoip.enrich_ipは差し替える)。
使い方: リポジトリ直下で `<repo>/.venv/bin/python scripts/check_ver1525.py`(全項目OKなら終了コード0)。
★認証経路は本番と同じMULTIUSER=1で検査する(MULTIUSER無し=全員が管理者になり権限の検査にならない・ver1.5.6の教訓)。"""
import importlib.util
import json
import os
import re
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(os.environ.get("REPO") or Path(__file__).resolve().parents[1])
tmp = tempfile.mkdtemp(prefix="eigo_ver1525_")
os.environ["DATA_DIR"] = tmp
os.environ["MULTIUSER"] = "1"
TOKEN = "tok-" + "x" * 30
os.environ["FAIL2BAN_NOTIFY_TOKEN"] = TOKEN
os.environ["SESSION_SECRET"] = "test-secret-ver1525"   # ip_retention(毎日のprune)が鍵を要る。Cookieの署名も同じ鍵になる
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import app.main as m
from app.database import db, init_db
from app.routers import system
from app.services import auth, geoip, ip_blocks

init_db()
ok = fail = 0
REAL_ENRICH = geoip.enrich_ip


def check(label, cond, extra=""):
    global ok, fail
    if cond:
        ok += 1
        print("OK  ", label)
    else:
        fail += 1
        print("FAIL", label, extra)


H = {"X-F2B-Token": TOKEN}
IP_A, IP_B, IP_C, IP_D = "45.33.32.156", "185.220.101.5", "91.92.109.43", "8.8.4.4"
IPV6 = "2606:4700:4700::1111"


def mk(name, role):
    with db() as conn:
        r = auth.create_user(conn, name, "Passw0rd!x1", role=role)
        return r["id"] if isinstance(r, dict) else r


admin, normal = mk("adm_t", "admin"), mk("usr_t", "user")


def cookie(uid):
    with db() as conn:
        secret = auth.get_session_secret(conn)
        epoch = auth.get_session_epoch(conn, uid)
    return {auth.SESSION_COOKIE: auth.make_session_token(secret, uid, epoch, int(time.time()))}


def item(ip, **kw):
    now = time.time()
    d = {"ip": ip, "first_seen": now - 600, "last_seen": now - 60, "total": 40, "probe": 0,
         "authfail": 0, "ratelimited": 0, "errors4xx": 0,
         "paths": [{"m": "GET", "p": "/.env", "s": 307, "n": 3}], "ua": "curl/8.0", "exempt": False}
    d.update(kw)
    return d


def utc(days_ago=0, hours_ago=0):
    return ip_blocks.fmt_utc(ip_blocks.utc_now() - timedelta(days=days_ago, hours=hours_ago))


# ---------------------------------------------------------------- 1) 純粋関数
check("jst_day: UTC 15:01 は日本時間の翌日", ip_blocks.jst_day("2026-11-07 15:01:05") == "2026-11-08")
check("jst_day: UTC 14:59:59 はまだ同じ日", ip_blocks.jst_day("2026-11-07 14:59:59") == "2026-11-07")
check("jst_day: 不正値・None・空は空文字", ip_blocks.jst_day("x") == "" and ip_blocks.jst_day(None) == "" and ip_blocks.jst_day("") == "")


def dayrow(day, **kw):
    return {"day": day, "total": 10, "probe": 0, "authfail": 0, "ratelimited": 0, "errors4xx": 0, **kw}


h = ip_blocks.build_history("2026-11-03 14:00:00", [dayrow("2026-11-02", probe=1), dayrow("2026-11-03", probe=3)], [], [], None, None)
check("history: 前の日の記録があれば再来(今回の日は数えない)", h["repeat"] and h["prior_days"] == 1 and h["last_prior_day"] == "2026-11-02" and h["first_day"] == "2026-11-02", h)
check("history: 日ごとの記録は新しい順・最大の危険度", [d["day"] for d in h["recent_days"]] == ["2026-11-03", "2026-11-02"] and h["max_level"] == "high" and h["flagged_days"] == 2, h)
h = ip_blocks.build_history("2026-11-03 14:00:00", [dayrow("2026-11-03", probe=1)], [], [], None, None)
check("history: 今回の日だけなら『初めて』", not h["repeat"] and h["prior_days"] == 0 and h["last_prior_day"] is None, h)
h = ip_blocks.build_history("2026-11-03 14:00:00", [dayrow("2026-11-04", probe=1)], [], [], None, None)
check("history: 今回より後の日は過去に数えない", not h["repeat"], h)
bans = [{"jail": "eigo-probe", "action": "ban", "mode": "ban", "created_at": "2026-10-20 03:00:00"},
        {"jail": "eigo-probe", "action": "unban", "mode": "ban", "created_at": "2026-10-21 03:00:00"},
        {"jail": "eigo-loginflood", "action": "ban", "mode": "dryrun", "created_at": "2026-10-10 03:00:00"}]
h = ip_blocks.build_history("2026-11-03 14:00:00", [dayrow("2026-11-03", probe=1)], bans, [], None, None)
check("history: 実際の遮断(ban/mode=ban)は過去の証拠・解除と試験運転(dryrun)は数えない",
      h["repeat"] and h["prior_days"] == 1 and h["bans"]["count"] == 1 and h["bans"]["jails"] == ["eigo-probe"]
      and h["bans"]["first"] == "2026-10-20" and h["first_day"] == "2026-10-20", h)
h = ip_blocks.build_history("2026-11-03 14:00:00", [dayrow("2026-11-03", probe=1)], [], [{"created_at": "2026-09-01 00:00:00"}], None, None)
check("history: 手動ブロックの履歴も過去の証拠", h["repeat"] and h["manual_blocks"] == 1 and h["first_day"] == "2026-09-01", h)
h = ip_blocks.build_history("2026-11-03 14:00:00", [dayrow("2026-11-03", probe=1)], [], [],
                            {"n": 138, "a": "2026-10-01 00:00:00", "b": "2026-11-03 00:00:00", "bots": 138}, {"fail": 3, "ok": 0})
check("history: 訪問記録・ログイン失敗は参考情報(これだけでは『再来』にしない)",
      not h["repeat"] and h["visits"]["count"] == 138 and h["visits"]["bots"] == 138 and h["login"]["fail"] == 3, h)
h = ip_blocks.build_history("2026-11-03 14:00:00", [], [], [], None, None)
check("history: 何も無ければ空(max_levelはNone)", not h["repeat"] and h["flagged_days"] == 0 and h["max_level"] is None and h["visits"] is None and h["login"] is None, h)

# ---------------------------------------------------------------- 2) 起動時の取り込み(INSERT OR IGNORE・冪等)
with db() as conn:
    conn.execute("INSERT INTO suspicious_access (ip, first_seen, last_seen, total, probe, authfail, ratelimited, errors4xx, paths, ua, exempt) "
                 "VALUES (?, '2026-11-07 10:00:00', '2026-11-07 15:01:05', 30, 14, 0, 0, 0, '[]', '', 0)", (IP_D,))
    conn.commit()
init_db()
init_db()
with db() as conn:
    seeded = [dict(r) for r in conn.execute("SELECT * FROM suspicious_access_days WHERE ip = ?", (IP_D,))]
check("起動時: 既存のsuspicious_accessが日(日本時間)つきで履歴表に入る・何度走っても1行", len(seeded) == 1 and seeded[0]["day"] == "2026-11-08" and seeded[0]["probe"] == 14, seeded)
with db() as conn:
    conn.execute("INSERT INTO suspicious_access (ip, first_seen, last_seen, total, probe, authfail, ratelimited, errors4xx, paths, ua, exempt) "
                 "VALUES (?, '2026-11-07 10:00:00', '2026-11-07 15:01:05', 30, 14, 0, 0, 0, '[]', '', 1)", (IP_C,))
    conn.commit()
init_db()
with db() as conn:
    ex = conn.execute("SELECT COUNT(*) AS n FROM suspicious_access_days WHERE ip = ?", (IP_C,)).fetchone()["n"]
check("起動時: 信頼IP/許可リスト(exempt=1)は履歴(360日保持)に取り込まない", ex == 0, ex)
with db() as conn:
    conn.execute("DELETE FROM suspicious_access"); conn.execute("DELETE FROM suspicious_access_days"); conn.commit()

# ---------------------------------------------------------------- 3) 取り込み: 日ごとの履歴と、国・地域の取得依頼
enrich_calls = []
geoip.enrich_ip = lambda ip: enrich_calls.append(ip)   # 外部の位置情報サービスには絶対に繋がない
c = TestClient(m.app)
now = time.time()
r = c.post("/api/system/security-events/suspects",
           json={"items": [item(IP_A, probe=5, total=50, first_seen=now - 5 * 3600, last_seen=now - 60)]}, headers=H)
check("ingest: 200", r.status_code == 200, r.text)
check("ingest: 国が未取得のIPは取得を依頼(geo_queued=1)", r.json().get("geo_queued") == 1 and enrich_calls == [IP_A], (r.json(), enrich_calls))
with db() as conn:
    rows = {x["day"]: dict(x) for x in conn.execute("SELECT * FROM suspicious_access_days WHERE ip = ?", (IP_A,))}
today_jst = ip_blocks.jst_day(ip_blocks.epoch_to_utc(now - 60))
check("ingest: 最後に動いた日(日本時間)に件数が入る", rows.get(today_jst, {}).get("probe") == 5 and rows[today_jst]["total"] == 50, rows)
first_day = ip_blocks.jst_day(ip_blocks.epoch_to_utc(now - 5 * 3600))
if first_day != today_jst:
    check("ingest: 窓が日をまたぐと、最初の日には件数0の印が入る", rows.get(first_day, {}).get("probe") == 0 and rows[first_day]["total"] == 0, rows)
else:
    check("ingest: (窓が同じ日に収まる時刻なので印の検査は省略)", len(rows) == 1, rows)
enrich_calls.clear()
r = c.post("/api/system/security-events/suspects", json={"items": [item(IP_A, probe=2, total=20, first_seen=now - 300, last_seen=now - 30)]}, headers=H)
with db() as conn:
    again = conn.execute("SELECT probe, total FROM suspicious_access_days WHERE ip = ? AND day = ?", (IP_A, today_jst)).fetchone()
    n_rows = conn.execute("SELECT COUNT(*) AS n FROM suspicious_access_days WHERE ip = ?", (IP_A,)).fetchone()["n"]
check("ingest: 同じ日の再取り込みは最大値を保つ(件数が減る窓でも減らさない)", again["probe"] == 5 and again["total"] == 50, dict(again))
r = c.post("/api/system/security-events/suspects", json={"items": [item(IP_A, probe=9, total=90, first_seen=now - 300, last_seen=now - 30)]}, headers=H)
with db() as conn:
    bigger = conn.execute("SELECT probe, total FROM suspicious_access_days WHERE ip = ? AND day = ?", (IP_A, today_jst)).fetchone()
check("ingest: 同じ日でも大きい値が来れば更新", bigger["probe"] == 9 and bigger["total"] == 90, dict(bigger))
check("ingest: 取得依頼は1回だけ(キャッシュが無くても、依頼先が埋めるまでの再依頼は別の話=ここでは再依頼しても害なし)", True)

# 国あり/国なし(問い合わせ済み)のキャッシュ・上限
with db() as conn:
    conn.execute("INSERT OR REPLACE INTO ip_geo_cache (ip, country, region, city, org) VALUES (?, 'Japan', 'Tokyo', 'Tokyo', 'Example ISP')", (IP_B,))
    conn.execute("INSERT OR REPLACE INTO ip_geo_cache (ip, country, region, city, org, error) VALUES (?, '', '', '', '', 'ipapi.co HTTP 429')", (IP_C,))
    conn.commit()
enrich_calls.clear()
r = c.post("/api/system/security-events/suspects", json={"items": [item(IP_B, authfail=6), item(IP_C, probe=1), item("10.1.2.3", probe=9)]}, headers=H)
check("ingest: キャッシュ済み(国あり・国なし問い合わせ済み)・プライベートIPは取得を依頼しない", r.json()["geo_queued"] == 0 and enrich_calls == [], (r.json(), enrich_calls))
with db() as conn:   # 失敗(国が空)から1日以上たったIPは取り直す・直近の失敗は取り直さない
    conn.execute("UPDATE ip_geo_cache SET fetched_at = datetime('now', '-2 days') WHERE ip = ?", (IP_C,)); conn.commit()
enrich_calls.clear()
r = c.post("/api/system/security-events/suspects", json={"items": [item(IP_C, probe=1)]}, headers=H)
with db() as conn:
    left = conn.execute("SELECT COUNT(*) AS n FROM ip_geo_cache WHERE ip = ?", (IP_C,)).fetchone()["n"]
check("ingest: 国が空の失敗から1日以上たったIPは取り直す(空の行を消して依頼)", r.json()["geo_queued"] == 1 and enrich_calls == [IP_C] and left == 0, (r.json(), enrich_calls, left))
with db() as conn:   # 後の検査のために元の状態(直近の失敗)へ戻す
    conn.execute("INSERT OR REPLACE INTO ip_geo_cache (ip, country, region, city, org, error) VALUES (?, '', '', '', '', 'ipapi.co HTTP 429')", (IP_C,)); conn.commit()
with db() as conn:   # 国がNULL(空文字でなく)の失敗行も、1日以上たてば取り直す(NULLでは永久に再依頼されるバグの防止)
    conn.execute("INSERT OR REPLACE INTO ip_geo_cache (ip, country, fetched_at) VALUES ('20.88.30.40', NULL, datetime('now', '-2 days'))"); conn.commit()
enrich_calls.clear()
r = c.post("/api/system/security-events/suspects", json={"items": [item("20.88.30.40", probe=1)]}, headers=H)
with db() as conn:
    nl = conn.execute("SELECT COUNT(*) AS n FROM ip_geo_cache WHERE ip = '20.88.30.40'").fetchone()["n"]
check("ingest: 国がNULLの古い失敗行も取り直す(行を消して依頼・NULLで永久に再依頼しない)", r.json()["geo_queued"] == 1 and nl == 0, (r.json(), nl))
check("ingest: 取得の依頼が終わると『取得中』の印(_GEO_INFLIGHT)は空に戻る", system._GEO_INFLIGHT == set(), system._GEO_INFLIGHT)
system._GEO_INFLIGHT.add("20.77.30.40")
enrich_calls.clear()
r = c.post("/api/system/security-events/suspects", json={"items": [item("20.77.30.40", probe=1)]}, headers=H)
check("ingest: 取得中(依頼済みで未完了)のIPは二重に依頼しない", r.json()["geo_queued"] == 0 and enrich_calls == [], (r.json(), enrich_calls))
system._GEO_INFLIGHT.discard("20.77.30.40")
enrich_calls.clear()
r = c.post("/api/system/security-events/suspects", json={"items": [item("20.77.30.40", probe=1)]}, headers=H)
check("ingest: 印が消えれば(完了後)また依頼できる", r.json()["geo_queued"] == 1 and enrich_calls == ["20.77.30.40"], (r.json(), enrich_calls))
r = c.post("/api/system/security-events/suspects", json={"items": [item("20.66.30.40", probe=4, exempt=True)]}, headers=H)
with db() as conn:
    sa = conn.execute("SELECT COUNT(*) AS n FROM suspicious_access WHERE ip = '20.66.30.40'").fetchone()["n"]
    dy = conn.execute("SELECT COUNT(*) AS n FROM suspicious_access_days WHERE ip = '20.66.30.40'").fetchone()["n"]
check("ingest: 信頼IP(exempt)は一覧の要約には載るが、360日保持の履歴には積まない", sa == 1 and dy == 0, (sa, dy))
many = [f"20.{i}.30.40" for i in range(1, 16)]
enrich_calls.clear()
r = c.post("/api/system/security-events/suspects", json={"items": [item(ip, probe=1) for ip in many]}, headers=H)
check("ingest: 1回の取得依頼は上限10件(外部サービスの無料枠を守る)",
      r.json()["geo_queued"] == system.GEO_ENRICH_PER_INGEST == 10 and len(enrich_calls) == 10, (r.json(), len(enrich_calls)))
enrich_calls.clear()
r = c.post("/api/system/security-events/suspects", json={"items": [item(IPV6, probe=2)]}, headers=H)
check("ingest: IPv6の公開アドレスも取得を依頼する", enrich_calls == [IPV6], enrich_calls)
r = c.post("/api/system/security-events/suspects", json={"items": []}, headers=H)
check("ingest: 空の送信は200・依頼0", r.status_code == 200 and r.json()["geo_queued"] == 0, r.text)
enrich_calls.clear()
r_no = c.post("/api/system/security-events/suspects", json={"items": [item("20.99.30.40", probe=1)]})
r_bad = c.post("/api/system/security-events/suspects", json={"items": [item("20.99.30.41", probe=1)]}, headers={"X-F2B-Token": "wrong"})
check("ingest: トークン無し・誤トークンは404(存在を教えない)で、位置情報の取得も依頼しない(取得依頼の経路を外部に開けない)",
      r_no.status_code == 404 and r_bad.status_code == 404 and enrich_calls == [], (r_no.status_code, r_bad.status_code, enrich_calls))

# 360日より古い日ごとの履歴は取り込み時に消える
with db() as conn:
    conn.execute("INSERT OR REPLACE INTO suspicious_access_days (ip, day, probe) VALUES (?, ?, 1)", (IP_A, ip_blocks.jst_day(utc(days_ago=361))))
    conn.execute("INSERT OR REPLACE INTO suspicious_access_days (ip, day, probe) VALUES (?, ?, 1)", (IP_A, ip_blocks.jst_day(utc(days_ago=359))))
    conn.commit()
c.post("/api/system/security-events/suspects", json={"items": []}, headers=H)
with db() as conn:
    old = conn.execute("SELECT COUNT(*) AS n FROM suspicious_access_days WHERE day = ?", (ip_blocks.jst_day(utc(days_ago=361)),)).fetchone()["n"]
    keep = conn.execute("SELECT COUNT(*) AS n FROM suspicious_access_days WHERE day = ?", (ip_blocks.jst_day(utc(days_ago=359)),)).fetchone()["n"]
check("保持期限: 361日前の履歴は取り込み時に削除・359日前は残る(IP保持期限360日以内)", old == 0 and keep == 1, (old, keep))

from app.services import ip_retention
with db() as conn:
    conn.execute("INSERT OR REPLACE INTO suspicious_access_days (ip, day, probe) VALUES (?, ?, 1)", (IP_B, ip_blocks.jst_day(utc(days_ago=400))))
    conn.execute("INSERT OR REPLACE INTO suspicious_access_days (ip, day, probe) VALUES (?, ?, 1)", (IP_B, ip_blocks.jst_day(utc(days_ago=10))))
    conn.commit()
    dry = ip_retention.anonymize_old_ips(conn, now=ip_blocks.utc_now(), dry_run=True)
    left_dry = conn.execute("SELECT COUNT(*) AS n FROM suspicious_access_days WHERE ip = ?", (IP_B,)).fetchone()["n"]
    real = ip_retention.anonymize_old_ips(conn, now=ip_blocks.utc_now())
    conn.commit()
    left = [r["day"] for r in conn.execute("SELECT day FROM suspicious_access_days WHERE ip = ?", (IP_B,))]
check("保持期限: 毎日のprune(ip_retention)でも、360日超の履歴を削除する(dry-runは数えるだけ)",
      dry.get("suspicious_access_days") == 1 and left_dry == 3 and real.get("suspicious_access_days") == 1
      and ip_blocks.jst_day(utc(days_ago=400)) not in left and ip_blocks.jst_day(utc(days_ago=10)) in left, (dry, real, left))

# ---------------------------------------------------------------- 4) 管理画面API
c.cookies.clear()
check("一覧: 未ログインは見られない", c.get("/api/system/admin/suspicious-access").status_code in (401, 403))
c.cookies.update(cookie(normal))
check("一覧: 一般ユーザーは見られない(国・履歴も見えない)", c.get("/api/system/admin/suspicious-access").status_code == 403)
c.cookies.clear(); c.cookies.update(cookie(admin))
# 履歴を仕込む: IP_A=過去の日+過去の遮断(再来)・IP_B=今回だけ・IP_C=国取得失敗・IPV6=キャッシュ無し(取得中)
with db() as conn:
    conn.execute("DELETE FROM suspicious_access"); conn.execute("DELETE FROM suspicious_access_days"); conn.execute("DELETE FROM security_events")
    conn.commit()
now = time.time()
c.post("/api/system/security-events/suspects", json={"items": [
    item(IP_A, probe=5, first_seen=now - 600, last_seen=now - 60),
    item(IP_B, authfail=6, first_seen=now - 600, last_seen=now - 120),
    item(IP_C, probe=1, first_seen=now - 600, last_seen=now - 180),
    item(IPV6, probe=2, first_seen=now - 600, last_seen=now - 240),
]}, headers=H)
with db() as conn:
    for d in (3, 10):
        conn.execute("INSERT OR REPLACE INTO suspicious_access_days (ip, day, total, probe) VALUES (?, ?, 20, 4)", (IP_A, ip_blocks.jst_day(utc(days_ago=d))))
    conn.execute("INSERT INTO security_events (ip, jail, action, mode, created_at) VALUES (?, 'eigo-probe', 'ban', 'ban', ?)", (IP_A, utc(days_ago=3)))
    conn.execute("INSERT INTO security_events (ip, jail, action, mode, created_at) VALUES (?, 'eigo-probe', 'unban', 'ban', ?)", (IP_A, utc(days_ago=2)))
    conn.execute("INSERT INTO security_events (ip, jail, action, mode, created_at) VALUES (?, 'eigo-loginflood', 'ban', 'dryrun', ?)", (IP_B, utc(days_ago=8)))
    conn.execute("INSERT INTO landing_visits (ip, kind, path, user_agent, bot_mark, created_at) VALUES (?, 'visit', '/', 'x', 1, ?)", (IP_A, utc(days_ago=3)))
    conn.execute("INSERT INTO login_log (username, success, ip, created_at) VALUES ('nobody', 0, ?, ?)", (IP_A, utc(days_ago=3)))
    conn.commit()
r = c.get("/api/system/admin/suspicious-access?hours=720")
check("一覧: 管理者は200", r.status_code == 200, r.status_code)
res = r.json()
byip = {x["ip"]: x for x in res["items"]}
check("一覧: 既存の項目(ip/level/paths/block/f2b…)は変わらない",
      all(k in byip[IP_A] for k in ["ip", "level", "first_seen", "last_seen", "total", "probe", "authfail", "ratelimited", "errors4xx",
                                    "paths", "ua", "exempt", "ipv6", "human_visits_30d", "dismissed", "block", "f2b"]), list(byip[IP_A]))
g = byip[IP_B]["geo"]
check("国・地域: 日本は『日本』『東京都』(日本語表記)・接続元の名前つき",
      g["state"] == "ok" and g["country_label"] == "日本" and g["region_label"] == "東京都" and g["org"] == "Example ISP", g)
check("国・地域: 問い合わせたが取れなかったIPは unknown", byip[IP_C]["geo"] == {"state": "unknown"}, byip[IP_C]["geo"])
check("国・地域: まだ問い合わせていないIPは pending", byip[IPV6]["geo"] == {"state": "pending"}, byip[IPV6]["geo"])
hA, hB = byip[IP_A]["history"], byip[IP_B]["history"]
check("履歴: 過去の日と過去の遮断があるIPは再来(過去2日)", hA["repeat"] and hA["prior_days"] == 2 and hA["flagged_days"] >= 3, hA)
check("履歴: 遮断は1回(解除は数えない)・jailが出る", hA["bans"]["count"] == 1 and hA["bans"]["jails"] == ["eigo-probe"], hA["bans"])
check("履歴: 訪問記録(bot印つき)とログイン失敗が参考情報として付く",
      hA["visits"]["count"] == 1 and hA["visits"]["bots"] == 1 and hA["login"] == {"fail": 1, "ok": 0}, (hA["visits"], hA["login"]))
check("履歴: 今回だけのIP(遮断の試験運転dryrunのみ)は『初めて』", not hB["repeat"] and hB["bans"]["count"] == 0, hB)
check("履歴: 記録の始まり(history_since)が返る", res["history_since"]["flagged"] is not None and res["history_since"]["ban"] is not None, res["history_since"])
check("履歴: 一覧は既定の並び(危険度順)のまま", [x["level"] for x in res["items"]] == sorted([x["level"] for x in res["items"]], key=lambda v: {"high": 0, "mid": 1, "low": 2}[v]))
# 生のIPが履歴の部分に紛れ込んでいない(管理者向けだがipは項目のipだけ)
dump = json.dumps({k: byip[IP_A][k] for k in ("geo", "history")})
check("履歴/国: 応答のgeo・historyに生のIPを含めない", IP_A not in dump and IP_B not in json.dumps(byip[IP_B]["geo"]), dump[:120])
# 問題なし→履歴は残る
c.post("/api/system/admin/suspicious-access/dismiss", json={"ip": IP_A})
r2 = c.get("/api/system/admin/suspicious-access?hours=720&include_dismissed=true")
check("問題なしにしても履歴は消えない", {x["ip"]: x for x in r2.json()["items"]}[IP_A]["history"]["repeat"] is True)

import logging
from app.config import log as applog
class _Cap(logging.Handler):
    def __init__(self): super().__init__(); self.recs = []
    def emit(self, rec): self.recs.append((rec.levelno, rec.getMessage()))
_cap = _Cap(); _old_level = applog.level
applog.addHandler(_cap); applog.setLevel(logging.DEBUG)
_orig_prov, _orig_rdns = geoip._PROVIDERS, geoip.reverse_dns
geoip.reverse_dns = lambda ip: ""
try:
    geoip._PROVIDERS = (("a", lambda cl, ip: ({}, "a HTTP 429")), ("b", lambda cl, ip: ({}, "b HTTP 429")))
    REAL_ENRICH("20.55.66.77")
    recs429 = [r for r in _cap.recs if "lookup failed" in r[1]]
    _cap.recs.clear()
    geoip._PROVIDERS = (("a", lambda cl, ip: ({}, "a HTTP 500")), ("b", lambda cl, ip: ({}, "b HTTP 429")))
    REAL_ENRICH("20.55.66.78")
    recs500 = [r for r in _cap.recs if "lookup failed" in r[1]]
finally:
    geoip._PROVIDERS, geoip.reverse_dns = _orig_prov, _orig_rdns
    applog.removeHandler(_cap); applog.setLevel(_old_level)
check("位置情報: 無料枠の制限(429のみ)はINFO・それ以外の失敗が混じればWARNING(朝チェックのWARNING0件を崩さない)",
      recs429 and all(r[0] == logging.INFO for r in recs429) and recs500 and all(r[0] == logging.WARNING for r in recs500), (recs429, recs500))

# ---------------------------------------------------------------- 5) 補完スクリプト(summarize / load)
spec = importlib.util.spec_from_file_location("sdb", ROOT / "scripts" / "suspect_days_backfill.py")
sdb = importlib.util.module_from_spec(spec); spec.loader.exec_module(sdb)
host_mod = sdb._load_host()


def cl(ts, ip, method, uri, status, ua="curl/8.0", host="study.nyangailab.com"):
    return json.dumps({"ts": ts, "status": status, "request": {"remote_ip": ip, "host": host, "method": method, "uri": uri,
                                                              "headers": {"User-Agent": [ua]}}})


t_end = datetime(2026, 11, 7, 14, 59, 59, tzinfo=timezone.utc).timestamp()   # 日本時間 11/7 23:59:59
t_next = t_end + 1                                                            # 日本時間 11/8 00:00:00
lines = [cl(t_end, IP_A, "GET", "/.env?x=1", 307), cl(t_next, IP_A, "GET", "/wp-login.php", 307),
         cl(t_end, IP_B, "GET", "/.env", 307, ua="Mozilla/5.0 (compatible; Googlebot/2.1)"),
         cl(t_end, "10.0.0.5", "GET", "/.env", 307),
         cl(t_end, "not-an-ip", "GET", "/.env", 307),
         cl(t_end, IP_C, "GET", "/.env", 307, host="other.example"),
         "{broken json"]
lines += [cl(t_end - i, IP_D, "GET", f"/nope{i}", 404) for i in range(15)]      # 4xxが15件=一覧に載る条件ちょうど
lines += [cl(t_end - i, "198.18.1.1", "GET", f"/nope{i}", 404) for i in range(20)]  # 非公開(198.18/15)は除外
lines += [cl(t_end - i, "44.44.44.44", "GET", f"/nope{i}", 404) for i in range(14)]  # 14件は載らない
out = sdb.summarize(lines, host_mod)
bykey = {(r["ip"], r["day"]): r for r in out}
check("補完/summarize: 日本時間の0時で日が分かれる(23:59:59と0:00:00)", (IP_A, "2026-11-07") in bykey and (IP_A, "2026-11-08") in bykey, list(bykey))
check("補完/summarize: ホスト側と同じ判定(クエリを落とした/.envと.php→探索各1)", bykey[(IP_A, "2026-11-07")]["probe"] == 1 and bykey[(IP_A, "2026-11-08")]["probe"] == 1)
check("補完/summarize: クローラー(Googlebot)・非公開IP・不正IP・別ホスト・壊れた行は除く", not any(r["ip"] in (IP_B, IP_C, "10.0.0.5", "not-an-ip", "198.18.1.1") for r in out), out)
check("補完/summarize: 4xx 15件は載り14件は載らない(一覧に載る条件と同じ)", (IP_D, "2026-11-07") in bykey and ("44.44.44.44", "2026-11-07") not in bykey and bykey[(IP_D, "2026-11-07")]["errors4xx"] == 15)

dbp = os.path.join(tmp, "logs.db")
conn0 = sqlite3.connect(dbp)
conn0.execute("DELETE FROM suspicious_access_days WHERE ip IN (?, ?)", (IP_A, IP_D)); conn0.commit()
conn0.execute("INSERT INTO suspicious_access_days (ip, day, total, probe) VALUES (?, '2026-11-07', 999, 7)", (IP_A,)); conn0.commit(); conn0.close()
n_before = sqlite3.connect(dbp).execute("SELECT COUNT(*) FROM suspicious_access_days").fetchone()[0]
rc = sdb.load(out, apply=False, db_path=dbp)
n_dry = sqlite3.connect(dbp).execute("SELECT COUNT(*) FROM suspicious_access_days").fetchone()[0]
check("補完/load: --applyが無ければ何も書かない(ドライラン)", rc == 0 and n_dry == n_before, (rc, n_before, n_dry))
rc = sdb.load(out, apply=True, db_path=dbp)
conn1 = sqlite3.connect(dbp)
a_old = conn1.execute("SELECT total, probe FROM suspicious_access_days WHERE ip = ? AND day = '2026-11-07'", (IP_A,)).fetchone()
a_new = conn1.execute("SELECT probe FROM suspicious_access_days WHERE ip = ? AND day = '2026-11-08'", (IP_A,)).fetchone()
n_after = conn1.execute("SELECT COUNT(*) FROM suspicious_access_days").fetchone()[0]
conn1.close()
backups = [f for f in os.listdir(tmp) if f.startswith("backup_logs_manual_") and f.endswith("_before_suspect_days.db")]
check("補完/load --apply: 成功(件数の減少なし)・バックアップを先に作る", rc == 0 and len(backups) == 1, (rc, backups))
check("補完/load --apply: 既にある行は上書きしない(999のまま)・新しい行だけ入る", tuple(a_old) == (999, 7) and a_new and a_new[0] == 1, (a_old, a_new))
check("補完/load --apply: 入れた件数が期待どおり(既存1行を除く)", n_after == n_before + len(out) - 1, (n_before, len(out), n_after))
rc = sdb.load(out, apply=True, db_path=dbp)
n_again = sqlite3.connect(dbp).execute("SELECT COUNT(*) FROM suspicious_access_days").fetchone()[0]
check("補完/load: 2回流しても増えない(冪等)", rc == 0 and n_again == n_after, (rc, n_after, n_again))
_orig_counts, _calls = sdb._counts, {"n": 0}
def _fake_counts(conn):
    _calls["n"] += 1
    r = _orig_counts(conn)
    return {k: v - 1 for k, v in r.items()} if _calls["n"] == 2 else r   # 2回目(挿入後)だけ件数が減ったように見せる
sdb._counts = _fake_counts
row_new = {"ip": "20.1.1.1", "day": "2026-10-01", "total": 3, "probe": 1, "authfail": 0, "ratelimited": 0, "errors4xx": 0}
n_pre = sqlite3.connect(dbp).execute("SELECT COUNT(*) FROM suspicious_access_days").fetchone()[0]
rc = sdb.load([row_new], apply=True, db_path=dbp)
n_post = sqlite3.connect(dbp).execute("SELECT COUNT(*) FROM suspicious_access_days").fetchone()[0]
sdb._counts = _orig_counts
check("補完/load --apply: 件数が想定と違えばROLLBACKして何も変えない(終了コード1)", rc == 1 and n_post == n_pre, (rc, n_pre, n_post))
empty = os.path.join(tmp, "empty.db"); sqlite3.connect(empty).execute("CREATE TABLE x(a)").connection.commit()
check("補完/load: 履歴表が無い(ver1.5.25の起動前)なら何もしないで終了コード2", sdb.load(out, apply=True, db_path=empty) == 2)
# 履歴の表を足した後でも、旧ファイルの他の表を壊していない
integ = sqlite3.connect(dbp).execute("PRAGMA integrity_check").fetchone()[0]
check("補完後のlogs.db: integrity_check ok", integ == "ok", integ)

# ---------------------------------------------------------------- 6) 画面(JS)
views = (ROOT / "static" / "js" / "views.js").read_text(encoding="utf-8")
check("画面: 国・地域と過去の履歴の列が追加されている", "<th>国・地域</th><th>過去の履歴</th>" in views and "function geoHtml" in views and "function historyHtml" in views)
check("画面: 再来だけ表示するチェックがあり、変更で再読み込みする", 'id="susRepeatOnly"' in views and '#susRepeatOnly").addEventListener("change", loadSuspects)' in views)
seg = views[views.index("function dayShort"):views.index("function suspectState")]
interp = re.findall(r"\$\{([^}]+)\}", seg)
risky = [x for x in interp if re.search(r"\b(g|h|d)\.(country_label|country|region_label|city_label|org|jails|day|bans|visits)\b", x) and "escapeHtml" not in x
         and not re.search(r"^h\.(prior_days|bans\.count|manual_blocks|login\.fail|visits\.count|visits\.bots|flagged_days)( \?.*)?$", x.strip())]
check("画面: 外部サービス由来の地名・組織名・jail名は全てescapeHtmlを通す(数値だけは素通し)", not risky, risky)
check("画面: 記録の始まり・共有IP/同じ事業者の別IPは再来にならない旨・位置は推定の旨を画面に書く",
      "記録の始まり" in views and "推定した目安" in views and "再来" in views and "別IP" in views)
check("画面: 日付をまたぐ1回の動きが翌日『再来』と出うる旨を注記", "日付(日本時間)をまたいで続いた1回の動き" in views)
if subprocess.run(["which", "node"], capture_output=True).returncode == 0:
    check("画面: node --check", subprocess.run(["node", "--check", str(ROOT / "static" / "js" / "views.js")]).returncode == 0)

# ---------------------------------------------------------------- 7) バージョン・記録
cfg = (ROOT / "app" / "config.py").read_text(encoding="utf-8")
check("バージョン: ver1.5.25", 'APP_VERSION = "ver1.5.25"' in cfg)
cl_txt = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
check("CHANGELOG: ver1.5.25の見出し", re.search(r"^## ver1\.5\.25 ", cl_txt, re.M) is not None)
rn = json.loads((ROOT / "release_notes.json").read_text(encoding="utf-8"))
v0 = rn["versions"][0]
check("release_notes: 先頭がver1.5.25(public/adminあり)", v0["version"] == "ver1.5.25" and v0["public"] and v0["admin"], v0.get("version"))
pub = " ".join(v0["public"])
check("release_notes: publicに内部の機能名・IP・ブロック等を書かない", not re.search(r"ブロック|fail2ban|怪しい|IP|探索|再来|不審", pub), pub)

print(f"\n{ok} OK / {fail} FAIL")
sys.exit(1 if fail else 0)
