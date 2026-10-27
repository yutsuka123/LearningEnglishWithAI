"""ver1.5.21(管理画面の「要注意」バナー・偽装UAのbot判定)のローカル検査。一時データ領域(DATA_DIR)で動かし、本番にも開発DBにも触れない。
使い方: リポジトリ直下で `.venv/bin/python scripts/check_ver1521.py`(全項目OKなら終了コード0)。"""
import os, re, sys, tempfile, time
from datetime import datetime, timedelta
from pathlib import Path
tmp = tempfile.mkdtemp(prefix="eigo_ver1521_")
os.environ["DATA_DIR"] = tmp
os.environ["MULTIUSER"] = "1"
sys.path.insert(0, os.environ.get("REPO") or str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient
import app.main as m
from app.database import db, init_db
from app.services import auth, visitor_kind

init_db()
ok = fail = 0
def check(label, cond, extra=""):
    global ok, fail
    if cond: ok += 1; print("OK  ", label)
    else: fail += 1; print("FAIL", label, extra)

# --- 1) 偽装UA(iOS 13.2.3のiPhone)はその他botとして判定。本物の新しいiPhone/Androidは巻き込まない
FAKE = ("Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1")
mark, why = visitor_kind.classify_ua(FAKE)
check("偽装UA(iPhone OS 13_2_3)は※4(その他bot)", mark == visitor_kind.MARK_OTHER_BOT, (mark, why))
REAL = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.7 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]
for ua in REAL:
    check(f"本物の端末は巻き込まない: {ua[30:70]}", visitor_kind.classify_ua(ua)[0] == visitor_kind.MARK_NONE)

# --- 2) 要注意バナーの集計
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

KEY = "admin_alert_ack_security_at"
def set_ack(ts):
    with db() as conn:
        conn.execute("INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)", (KEY, ts))
        conn.commit()
def add_event(ip, jail, mode, failures, age, action="ban"):
    with db() as conn:
        conn.execute(
            "INSERT INTO security_events (ip, jail, action, mode, failures, bantime_seconds, evidence, created_at) "
            "VALUES (?, ?, ?, ?, ?, 0, '', datetime('now', ?))", (ip, jail, action, mode, failures, age))
        conn.commit()

fmt = "%Y-%m-%d %H:%M:%S"
set_ack((datetime.utcnow() - timedelta(days=2)).strftime(fmt))
add_event("203.0.113.1", "eigo-probe", "ban", 5, "-1 hour")          # 自動遮断(同じIPを2行→1と数える)
add_event("203.0.113.1", "eigo-probe", "ban", 5, "-50 minutes")
add_event("203.0.113.2", "eigo-loginflood", "dryrun", 12, "-30 minutes")  # 候補(未遮断)
add_event("203.0.113.3", "eigo-probe-trusted", "dryrun", 3, "-20 minutes")  # 信頼IPの探索
add_event("203.0.113.4", "eigo-probe", "ban", 0, "-10 minutes")        # 手動banip(failures=0)=数えない
add_event("203.0.113.5", "eigo-probe", "ban", 5, "-3 days")            # 確認より前=数えない
add_event("203.0.113.1", "eigo-probe", "unban", 0, "-5 minutes", action="unban")  # 解除行=数えない

with TestClient(m.app, follow_redirects=False) as c:
    r = c.get("/api/system/admin/alerts")
    check("未ログインは警告を見られない", r.status_code != 200, r.status_code)
    c.cookies.clear(); c.cookies.update(cookie(normal))
    r = c.get("/api/system/admin/alerts")
    check("一般ユーザーは警告を見られない", r.status_code != 200, r.status_code)
    c.cookies.clear(); c.cookies.update(cookie(admin))
    r = c.get("/api/system/admin/alerts")
    check("管理者は200", r.status_code == 200, r.status_code)
    sec = r.json().get("security") or {}
    check("遮断=1(同じIPの2行は1と数える・手動/解除/過去は除く)", sec.get("ban") == 1, sec)
    check("候補(未遮断)=1", sec.get("candidates") == 1, sec)
    check("信頼IPの探索=1", sec.get("trusted") == 1, sec)
    check("合計=3", sec.get("count") == 3, sec)
    check("既存の registrants/errors も従来どおり返る", "registrants" in r.json() and "errors" in r.json())
    # 確認(ack)で0に戻る。ほかの種類の確認時刻は触らない
    with db() as conn:
        before = conn.execute("SELECT value FROM app_state WHERE key = 'admin_alert_ack_errors_at'").fetchone()
    r = c.post("/api/system/admin/alerts/ack", json={"kind": "security"})
    check("ackは200", r.status_code == 200, (r.status_code, r.text[:120]))
    check("ack後は0件", (r.json().get("security") or {}).get("count") == 0, r.text[:200])
    with db() as conn:
        after = conn.execute("SELECT value FROM app_state WHERE key = 'admin_alert_ack_errors_at'").fetchone()
    check("security の確認が errors の確認時刻を動かさない", (before and before["value"]) == (after and after["value"]))
    # 確認後に新しいイベントが来たら再び出る
    time.sleep(1.1)
    add_event("203.0.113.9", "eigo-probe", "ban", 7, "+0 seconds")
    r = c.get("/api/system/admin/alerts")
    check("確認後の新しい遮断で再び出る", (r.json().get("security") or {}).get("ban") == 1, r.text[:200])
    # 想定外のkindは拒否
    r = c.post("/api/system/admin/alerts/ack", json={"kind": "nope"})
    check("想定外のkindは422", r.status_code == 422, r.status_code)
    # 一般ユーザーは確認も押せない
    c.cookies.clear(); c.cookies.update(cookie(normal))
    r = c.post("/api/system/admin/alerts/ack", json={"kind": "security"})
    check("一般ユーザーはackできない", r.status_code != 200, r.status_code)

# --- 3) 画面側(静的チェック): 「要注意」行・詳細確認の飛び先・既存2種の行を壊していない
js = (Path(__file__).resolve().parents[1] / "static/js/views.js").read_text(encoding="utf-8")
check("バナーに要注意の行がある", 'data-kind="security"' in js and "要注意" in js)
check("詳細確認の飛び先が #logSecurityEventsDetails", "#logSecurityEventsDetails" in js and 'id="logSecurityEventsDetails"' in js)
check("既存の registrants/errors の行が残っている", 'data-kind="registrants"' in js and 'data-kind="errors"' in js)

print(f"\n{ok} OK / {fail} FAIL")
sys.exit(1 if fail else 0)
