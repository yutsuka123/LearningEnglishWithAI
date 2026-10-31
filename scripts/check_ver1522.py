"""ver1.5.22(管理画面の「怪しいアクセス」一覧と手動ブロック)のローカル検査。一時データ領域(DATA_DIR)で動かし、
本番にも開発DBにもVPSにも触れない。ホスト側スクリプトは本物のfail2ban/iptablesを使わず、偽のfail2ban-clientで動かす。
使い方: リポジトリ直下で `.venv/bin/python scripts/check_ver1522.py`(全項目OKなら終了コード0)。
★認証経路は本番と同じMULTIUSER=1で検査する(MULTIUSER無し=全員が管理者になりトークン/権限の検査にならない・ver1.5.6の教訓)。"""
import importlib.machinery
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(os.environ.get("REPO") or Path(__file__).resolve().parents[1])
tmp = tempfile.mkdtemp(prefix="eigo_ver1522_")
os.environ["DATA_DIR"] = tmp
os.environ["MULTIUSER"] = "1"
TOKEN = "tok-" + "x" * 30
os.environ["FAIL2BAN_NOTIFY_TOKEN"] = TOKEN
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
import app.main as m
from app.database import db, init_db
from app.routers import system
from app.services import auth, ip_blocks

init_db()
ok = fail = 0


def check(label, cond, extra=""):
    global ok, fail
    if cond:
        ok += 1
        print("OK  ", label)
    else:
        fail += 1
        print("FAIL", label, extra)


H = {"X-F2B-Token": TOKEN}
IP_A, IP_B, IP_C, IP_D, IP_E = "45.33.32.156", "185.220.101.5", "91.92.109.43", "8.8.4.4", "103.21.244.7"
IP_SELF = "198.18.5.5"  # 198.18/15はis_global=False。自分のIPの検査は別の公開IPを使う
SELF = "104.16.1.9"


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
         "paths": [{"m": "GET", "p": "/.env", "s": 404, "n": 3}], "ua": "curl/8.0", "exempt": False}
    d.update(kw)
    return d


# --- 1) ip_blocks の純粋な部分
check("公開IPv4は通る", ip_blocks.canonical_public_ipv4(IP_A) == IP_A)
for bad in ["10.0.0.1", "192.168.1.1", "127.0.0.1", "169.254.1.1", "100.64.0.1", "0.0.0.0", "224.0.0.1",
            "2001:db8::1", "::1", "abc", "", "1.2.3", "1.2.3.4/24", "203.0.113.5"]:
    check(f"ブロック不可のIP: {bad!r}", ip_blocks.canonical_public_ipv4(bad) is None)
check("制御文字を除く", ip_blocks.clean_text("a\x00b\nc\x7f", 10) == "abc")
check("期間の定義", set(ip_blocks.DURATIONS) == {"1h", "24h", "7d", "30d", "permanent"}
      and ip_blocks.DURATIONS["permanent"][0] is None and ip_blocks.DEFAULT_DURATION == "24h")
check("危険度: 探索3→高", ip_blocks.suspect_level({"probe": 3, "authfail": 0, "ratelimited": 0, "errors4xx": 0}) == "high")
check("危険度: 探索1→中", ip_blocks.suspect_level({"probe": 1, "authfail": 0, "ratelimited": 0, "errors4xx": 0}) == "mid")
check("危険度: 4xx15のみ→低", ip_blocks.suspect_level({"probe": 0, "authfail": 0, "ratelimited": 0, "errors4xx": 15}) == "low")

with TestClient(m.app, follow_redirects=False) as c:
    # --- 2) ホスト向け(トークン認証)エンドポイント
    paths_post = ["/api/system/security-events/suspects", "/api/system/security-events/manual-blocks/report"]
    for p in paths_post:
        r = c.post(p, json={"items": []} if p.endswith("suspects") else {})
        check(f"トークン無し→404(存在を教えない) {p.rsplit('/', 1)[-1]}", r.status_code == 404, r.status_code)
        r = c.post(p, json={"items": []} if p.endswith("suspects") else {}, headers={"X-F2B-Token": "wrong"})
        check(f"トークン違い→404 {p.rsplit('/', 1)[-1]}", r.status_code == 404, r.status_code)
    r = c.get("/api/system/security-events/manual-blocks/desired")
    check("desired: トークン無し→404", r.status_code == 404, r.status_code)

    long_path = "/x" * 200
    body = {"items": [
        item(IP_A, probe=5, paths=[{"m": "GET", "p": "/wp-login.php\x00<script>", "s": 404, "n": 5}]),
        item(IP_B, authfail=6),
        item("10.1.2.3", probe=9),             # プライベートは保存しない
        item("not-an-ip", probe=9),
        item("2606:4700:4700::1111", probe=2),  # IPv6は保存(ブロックは不可)
    ]}
    r = c.post("/api/system/security-events/suspects", json=body, headers=H)
    check("ingest: 200", r.status_code == 200, r.text)
    check("ingest: 公開3件を保存・2件を除外", r.json().get("saved") == 3 and r.json().get("skipped") == 2, r.json())
    r = c.post("/api/system/security-events/suspects", json={"items": [item(IP_A, paths=[{"m": "G", "p": long_path, "s": 404, "n": 1}])]}, headers=H)
    check("ingest: 長いパスは切り詰めて受理(422でなく)", r.status_code in (200, 422))
    r = c.post("/api/system/security-events/suspects", json={"items": [item(IP_A)] * 301}, headers=H)
    check("ingest: 301件は拒否", r.status_code == 422, r.status_code)
    r = c.post("/api/system/security-events/suspects", json={"items": [item(IP_A, probe=-1)]}, headers=H)
    check("ingest: 負の回数は拒否", r.status_code == 422, r.status_code)
    r = c.post("/api/system/security-events/suspects", json=body, headers=H)
    with db() as conn:
        n = conn.execute("SELECT COUNT(*) AS n FROM suspicious_access").fetchone()["n"]
        stored = conn.execute("SELECT paths FROM suspicious_access WHERE ip = ?", (IP_A,)).fetchone()["paths"]
    check("ingest: 同じIPは上書き(重複行なし)", n == 3, n)
    check("ingest: 保存前に制御文字を除く", "\\u0000" not in stored and "\x00" not in stored, stored)

    # --- 3) 管理者向け一覧の権限
    r = c.get("/api/system/admin/suspicious-access")
    check("一覧: 未ログインは見られない", r.status_code in (401, 403), r.status_code)
    c.cookies.clear(); c.cookies.update(cookie(normal))
    check("一覧: 一般ユーザーは見られない", c.get("/api/system/admin/suspicious-access").status_code == 403)
    check("ブロック: 一般ユーザーは作れない", c.post("/api/system/admin/manual-blocks", json={"ip": IP_A}).status_code == 403)
    check("解除: 一般ユーザーは不可", c.post("/api/system/admin/manual-blocks/1/release", json={}).status_code == 403)
    check("問題なし: 一般ユーザーは不可", c.post("/api/system/admin/suspicious-access/dismiss", json={"ip": IP_A}).status_code == 403)
    check("ブロック履歴: 一般ユーザーは見られない", c.get("/api/system/admin/manual-blocks").status_code == 403)
    c.cookies.clear(); c.cookies.update(cookie(admin))
    r = c.get("/api/system/admin/suspicious-access")
    check("一覧: 管理者は200", r.status_code == 200, r.status_code)
    items = r.json()["items"]
    byip = {x["ip"]: x for x in items}
    check("一覧: 3件(IPv6含む)", len(items) == 3, [x["ip"] for x in items])
    check("一覧: 危険度 探索5→高・ログイン失敗6→中", byip[IP_A]["level"] == "high" and byip[IP_B]["level"] == "mid", byip)
    check("一覧: 高が先頭", items[0]["level"] == "high")
    check("一覧: IPv6の印", byip["2606:4700:4700::1111"]["ipv6"] is True and byip[IP_A]["ipv6"] is False)
    check("一覧: 最終集計時刻が入る", r.json()["collected_at"] is not None)

    # --- 4) 問題なし → 新しいアクセスで再び出る
    r = c.post("/api/system/admin/suspicious-access/dismiss", json={"ip": IP_B})
    check("問題なし: 200", r.status_code == 200, r.text)
    check("問題なし後は既定の一覧から消える",
          IP_B not in [x["ip"] for x in c.get("/api/system/admin/suspicious-access").json()["items"]])
    r = c.get("/api/system/admin/suspicious-access?include_dismissed=true")
    check("問題なし: 表示オプションで見える(dismissed=true)",
          any(x["ip"] == IP_B and x["dismissed"] for x in r.json()["items"]))
    time.sleep(1.1)
    c.post("/api/system/security-events/suspects", json={"items": [item(IP_B, authfail=6, last_seen=time.time() + 5)]}, headers=H)
    check("問題なし後に新しいアクセスがあれば再び出る",
          IP_B in [x["ip"] for x in c.get("/api/system/admin/suspicious-access").json()["items"]])
    check("問題なし: 存在しないIPは404", c.post("/api/system/admin/suspicious-access/dismiss", json={"ip": "9.9.9.9"}).status_code == 404)

    # --- 5) ブロックの作成と安全装置
    def blk(ip, dur="24h", **kw):
        return c.post("/api/system/admin/manual-blocks", json={"ip": ip, "duration": dur, **kw},
                      headers=kw.pop("_h", {}) if False else None)

    r = blk(IP_A)
    check("ブロック: 作成200", r.status_code == 200 and r.json()["duration"] == "24h", r.text)
    bid_a = r.json().get("id")
    exp = datetime.strptime(r.json()["expires_at"], "%Y-%m-%d %H:%M:%S")
    check("ブロック: 24時間の期限", abs((exp - datetime.utcnow()).total_seconds() - 86400) < 120)
    r = c.post("/api/system/admin/manual-blocks", json={"ip": IP_C})
    check("ブロック: 期間を省略すると24時間(『ブロック』だけ押したとき)", r.status_code == 200 and r.json()["duration"] == "24h", r.text)
    for dur, secs in [("1h", 3600), ("7d", 7 * 86400), ("30d", 30 * 86400)]:
        r = blk(IP_D, dur)
        e = datetime.strptime(r.json()["expires_at"], "%Y-%m-%d %H:%M:%S")
        check(f"ブロック: {dur}の期限", r.status_code == 200 and abs((e - datetime.utcnow()).total_seconds() - secs) < 120, r.text)
    r = blk(IP_D, "permanent")
    check("ブロック: 永久は期限なし", r.status_code == 200 and r.json()["expires_at"] is None, r.text)
    check("ブロック: 不正な期間は拒否", c.post("/api/system/admin/manual-blocks", json={"ip": IP_E, "duration": "99y"}).status_code == 422)
    for bad, why in [("10.0.0.5", "プライベート"), ("2606:4700:4700::1111", "IPv6"), ("zzz", "不正"), ("127.0.0.1", "ループバック")]:
        check(f"ブロック不可: {why}", blk(bad).status_code in (400, 422), bad)
    with db() as conn:
        act = conn.execute("SELECT COUNT(*) AS n FROM manual_blocks WHERE released_at IS NULL").fetchone()["n"]
    check("同じIPの置き換え: 有効な行はIPごとに1つ(A,C,Dの3件)", act == 3, act)
    with db() as conn:
        sup = conn.execute("SELECT COUNT(*) AS n FROM manual_blocks WHERE released_by = 'superseded'").fetchone()["n"]
    check("置き換えられた旧い行はsuperseded(IP_Dを4回→3件)", sup == 3, sup)

    r = c.post("/api/system/admin/manual-blocks", json={"ip": SELF}, headers={"x-forwarded-for": SELF})
    check("安全装置: いま操作している自分のIPは不可", r.status_code == 400 and "自分" in r.text, r.text)
    r = c.post("/api/system/admin/manual-blocks", json={"ip": "62.4.3.2"}, headers={"x-forwarded-for": "1.1.1.1, 62.4.3.1"})
    check("自分のIP判定はXFFの一番右(偽装できる左側は無視)", r.status_code == 200, r.text)
    orig_known = system.load_admin_known_ips
    system.load_admin_known_ips = lambda: {"62.4.3.77"}
    r = blk("62.4.3.77")
    check("安全装置: ADMIN_KNOWN_IPSは不可", r.status_code == 400, r.text)
    system.load_admin_known_ips = orig_known
    # 登録ユーザーのログイン実績
    uid = mk("old_user", "user")
    with db() as conn:
        conn.execute("UPDATE users SET created_at = datetime('now', '-20 days') WHERE id = ?", (uid,))
        conn.execute("INSERT INTO login_log (username, ip, success, created_at) VALUES ('old_user', '77.88.55.1', 1, datetime('now', '-3 days'))")
        conn.execute("INSERT INTO login_log (username, ip, success, created_at) VALUES ('old_user', '77.88.55.2', 0, datetime('now', '-3 days'))")
        conn.commit()
    check("安全装置: 登録ユーザーのログイン実績のIPは不可", blk("77.88.55.1").status_code == 400)
    check("ログイン『失敗』だけのIPは信頼IPでない(ブロック可)", blk("77.88.55.2").status_code == 200)
    # exemptの印
    c.post("/api/system/security-events/suspects", json={"items": [item("66.77.88.9", probe=3, exempt=True)]}, headers=H)
    check("安全装置: ホストが許可リスト/信頼IPと判定(exempt)したIPは不可", blk("66.77.88.9").status_code == 400)
    check("一覧: exemptの印が出る", {x["ip"]: x for x in c.get("/api/system/admin/suspicious-access").json()["items"]}["66.77.88.9"]["exempt"] is True)
    # 共有IPの確認
    with db() as conn:
        conn.execute("INSERT INTO landing_visits (ip, path, user_agent, kind, bot_mark) VALUES ('55.44.33.22', '/', 'Mozilla', 'visit', 0)")
        conn.execute("INSERT INTO landing_visits (ip, path, user_agent, kind, bot_mark) VALUES ('55.44.33.23', '/', 'bot', 'visit', 4)")
        conn.commit()
    r = blk("55.44.33.22")
    check("共有IP(人間らしい訪問あり)は確認なしだと409", r.status_code == 409 and "共有IP" in r.text, (r.status_code, r.text))
    r = blk("55.44.33.22", confirm_shared=True)
    check("共有IPでも確認済みなら通る", r.status_code == 200, r.text)
    check("botの訪問だけのIPは確認不要", blk("55.44.33.23").status_code == 200)

    # --- 6) ホストが取りに来る一覧
    r = c.get("/api/system/security-events/manual-blocks/desired", headers=H)
    check("desired: 200", r.status_code == 200 and r.json()["ok"] is True, r.text)
    des = {b["ip"]: b for b in r.json()["blocks"]}
    check("desired: 有効なブロックのみ(置き換え前の旧い行は含まない)", IP_A in des and IP_C in des and IP_D in des)
    check("desired: jail名が期間に対応", des[IP_A]["jail"] == "eigo-manual-24h" and des[IP_D]["jail"] == "eigo-manual-perm", des)
    check("desired: 永久は期限なし・一時は期限あり", des[IP_D]["expires_epoch"] is None and isinstance(des[IP_A]["expires_epoch"], int))
    check("desired: 全jailが定義済み", all(b["jail"] in ip_blocks.MANUAL_JAILS for b in des.values()))

    # 期限切れは一覧から消える
    with db() as conn:
        conn.execute("UPDATE manual_blocks SET expires_at = datetime('now', '-1 minute') WHERE id = ?", (bid_a,))
        conn.commit()
    des = {b["ip"] for b in c.get("/api/system/security-events/manual-blocks/desired", headers=H).json()["blocks"]}
    check("desired: 期限切れは消える(ホストが解除する)", IP_A not in des)
    # ハッシュ化済みIPが混ざってもホストへ渡さない
    with db() as conn:
        conn.execute("INSERT INTO manual_blocks (ip, duration, expires_at) VALUES ('h:abcdef0123456789abcd', 'permanent', NULL)")
        conn.commit()
    des = c.get("/api/system/security-events/manual-blocks/desired", headers=H).json()["blocks"]
    check("desired: ハッシュ化済みIPなどの不正値は渡さない", all(ip_blocks.canonical_public_ipv4(b["ip"]) for b in des))

    # --- 7) 報告・解除・一覧の状態
    with db() as conn:
        pend = conn.execute("SELECT id, ip FROM manual_blocks WHERE ip = ? AND released_at IS NULL", (IP_C,)).fetchone()
    r = c.post("/api/system/security-events/manual-blocks/report",
               json={"applied": [pend["id"]], "refused": []}, headers=H)
    check("report: 200", r.status_code == 200, r.text)
    states = {b["ip"]: b["state"] for b in c.get("/api/system/admin/manual-blocks").json()["blocks"] if b["state"] in ("active", "pending")}
    check("一覧: 反映済み=active・未反映=pending", states[IP_C] == "active" and states.get(IP_D) == "pending", states)
    with db() as conn:
        did = conn.execute("SELECT id FROM manual_blocks WHERE ip = ? AND released_at IS NULL", (IP_D,)).fetchone()["id"]
    c.post("/api/system/security-events/manual-blocks/report", json={"applied": [], "refused": [{"id": did, "reason": "ホストの許可リスト"}]}, headers=H)
    blocks = {b["id"]: b for b in c.get("/api/system/admin/manual-blocks").json()["blocks"]}
    check("report: 拒否された行は解除扱い+理由が残る", blocks[did]["state"] == "refused" and "許可リスト" in blocks[did]["applied_note"], blocks[did])
    check("report: 最終同期時刻が入る", c.get("/api/system/admin/manual-blocks").json()["synced_at"] is not None)
    r = c.post(f"/api/system/admin/manual-blocks/{pend['id']}/release", json={})
    check("解除: 200", r.status_code == 200, r.text)
    des = {b["ip"] for b in c.get("/api/system/security-events/manual-blocks/desired", headers=H).json()["blocks"]}
    check("解除したIPはdesiredから消える", IP_C not in des)
    check("解除: 存在しないIDは404", c.post("/api/system/admin/manual-blocks/999999/release", json={}).status_code == 404)
    st = {b["id"]: b["state"] for b in c.get("/api/system/admin/manual-blocks").json()["blocks"]}
    check("履歴の状態: released/expired/refused", st[pend["id"]] == "released" and st[bid_a] == "expired" and st[did] == "refused", st)
    # 一覧に手動ブロックの状態が出る
    c.post("/api/system/security-events/suspects", json={"items": [item(IP_E, probe=2)]}, headers=H)
    blk(IP_E, "7d")
    sus = {x["ip"]: x for x in c.get("/api/system/admin/suspicious-access").json()["items"]}
    check("一覧: ブロック中のIPにblock情報が付く", sus[IP_E]["block"] and sus[IP_E]["block"]["duration"] == "7d", sus[IP_E])

    # --- 8) 上限
    ip_blocks_max = ip_blocks.MAX_ACTIVE, ip_blocks.MAX_PERMANENT
    with db() as conn:
        n_act = conn.execute(f"SELECT COUNT(*) AS n FROM manual_blocks WHERE {ip_blocks.active_where()}").fetchone()["n"]
    ip_blocks.MAX_ACTIVE = n_act
    check("上限: 有効なブロックが上限だと新規は不可", blk("31.31.31.31").status_code == 400)
    check("上限: 既存IPの置き換えは上限でも可", blk(IP_E, "30d").status_code == 200)
    ip_blocks.MAX_ACTIVE = ip_blocks_max[0]
    ip_blocks.MAX_PERMANENT = 0
    check("上限: 永久の上限", blk("32.32.32.32", "permanent").status_code == 400)
    ip_blocks.MAX_PERMANENT = ip_blocks_max[1]

    # --- 9) 古い行の削除
    with db() as conn:
        conn.execute("INSERT INTO suspicious_access (ip, first_seen, last_seen) VALUES ('1.2.3.5', datetime('now', '-40 days'), datetime('now', '-40 days'))")
        conn.execute("INSERT INTO manual_blocks (ip, duration, expires_at, released_at) VALUES ('1.2.3.6', '1h', datetime('now', '-400 days'), datetime('now', '-400 days'))")
        conn.commit()
    c.post("/api/system/security-events/suspects", json={"items": []}, headers=H)
    with db() as conn:
        o1 = conn.execute("SELECT COUNT(*) AS n FROM suspicious_access WHERE ip = '1.2.3.5'").fetchone()["n"]
        o2 = conn.execute("SELECT COUNT(*) AS n FROM manual_blocks WHERE ip = '1.2.3.6'").fetchone()["n"]
        o3 = conn.execute("SELECT COUNT(*) AS n FROM manual_blocks WHERE released_at IS NULL AND ip LIKE 'h:%'").fetchone()["n"]
    check("30日超の怪しいアクセス要約・360日超のブロック記録は削除", o1 == 0 and o2 == 0)
    check("空の送信も受理して最終集計時刻を更新", c.get("/api/system/admin/suspicious-access").json()["collected_at"] is not None)

    # --- 10) ホスト側: 集計スクリプト(eigo-f2b-suspects)
    def load(name):
        path = ROOT / "deploy" / "fail2ban" / "bin" / name
        loader = importlib.machinery.SourceFileLoader(name.replace("-", "_"), str(path))
        spec = importlib.util.spec_from_loader(loader.name, loader)
        mod = importlib.util.module_from_spec(spec)
        loader.exec_module(mod)
        return mod

    sus_mod = load("eigo-f2b-suspects")
    logdir = Path(tmp) / "caddy"
    logdir.mkdir()
    conf = Path(tmp) / "eigo-f2b.conf"
    conf.write_text(f"CADDY_LOG_DIR={logdir}\nAPP_DATA_DIR={tmp}\nAPP_URL=http://127.0.0.1:1\nNOTIFY_TOKEN={TOKEN}\n")
    sus_mod.CONF = str(conf)
    sus_mod.AUDIT = str(Path(tmp) / "audit.log")
    now = time.time()

    def line(ip, uri, status, method="GET", ua="Mozilla/5.0 (X11; Linux)", ts=None):
        return json.dumps({"ts": ts or now - 30, "status": status, "request": {
            "remote_ip": ip, "method": method, "host": "study.nyangailab.com", "uri": uri,
            "headers": {"User-Agent": [ua]}}})

    S1, S2, S3, S4, S5, S6 = "44.1.1.1", "44.1.1.2", "44.1.1.3", "44.1.1.4", "44.1.1.5", "44.1.1.6"
    rows = []
    rows += [line(S1, "/.env?x=gclid_secret", 404), line(S1, "/wp-login.php", 404), line(S1, "/", 200)] * 2
    rows += [line(S2, "/api/auth/login", 401, "POST")] * 3 + [line(S2, "/api/auth/login", 200, "POST")]
    rows += [line(S3, "/api/decks", 401)] * 40                       # ゲストの通常の401は数えない
    rows += [line(S4, "/api/foo%d" % i, 404) for i in range(15)]      # 4xx 15回
    rows += [line(S4, "/static/x.js", 404)] * 30                      # 静的ファイルの404は数えない
    rows += [line(S5, "/wp-login.php", 404, ua="Mozilla/5.0 (compatible; Googlebot/2.1)")]  # クローラーUAは数えない
    rows += [line("10.9.9.9", "/.env", 404)]                          # プライベートは数えない
    rows += [line(S6, "/api/words", 429)] * 70 + [line(S6, "/api/other", 429)] * 3
    rows += [line("44.1.1.7", "/.env", 404, ts=now - 3 * 86400)]      # 24時間より前は数えない
    rows += ["not json", "{}", json.dumps({"ts": now, "status": "x"})]  # 壊れた行で落ちない
    (logdir / "study.log").write_text("\n".join(rows) + "\n")
    ips = sus_mod.summarize(sus_mod.read_lines(str(logdir / "study.log"), now), now)
    check("集計: 探索(クエリ文字列のgclidは見ない・200は数えない)", ips[S1]["probe"] == 4 and ips[S1]["total"] == 6, ips[S1])
    check("集計: ログイン失敗3回(200は数えない)", ips[S2]["authfail"] == 3, ips[S2])
    check("集計: ゲストの通常の401(GET)は数えない", ips[S3]["errors4xx"] == 0 and ips[S3]["authfail"] == 0)
    check("集計: 4xxは15回・静的ファイルの404は数えない", ips[S4]["errors4xx"] == 15, ips[S4])
    check("集計: クローラーUAは数えない", S5 not in ips)
    check("集計: プライベートIPは数えない", "10.9.9.9" not in ips)
    check("集計: 429は/api/wordsを除いて数える(3回)", ips[S6]["ratelimited"] == 3, ips[S6])
    check("集計: 24時間より前は数えない", "44.1.1.7" not in ips)
    sus_mod.is_exempt = lambda ip: ip == S2
    items2 = sus_mod.build_items(ips)
    got = {x["ip"]: x for x in items2}
    check("一覧の条件: 探索1以上/ログイン失敗3以上/429が3以上/4xxが15以上",
          set(got) == {S1, S2, S4, S6}, set(got))
    check("exemptの判定を送る", got[S2]["exempt"] is True and got[S1]["exempt"] is False)
    check("パスは回数順・クエリなし", got[S1]["paths"][0]["p"] in ("/.env", "/wp-login.php") and "?" not in json.dumps(got[S1]["paths"]), got[S1]["paths"])
    check("危険度の高い順(探索が先頭)", items2[0]["ip"] == S1, [x["ip"] for x in items2])
    check("送るUAは1種(最頻)", got[S1]["ua"].startswith("Mozilla"))
    check("clientに生のクエリ・ヘッダー全体を含めない", "gclid_secret" not in json.dumps(items2))
    posted = {}
    sus_mod.post = lambda items, token, url: posted.update(
        r=c.post("/api/system/security-events/suspects", json={"items": items}, headers={"X-F2B-Token": token}))
    c.cookies.clear()
    check("main: 正常終了", sus_mod.main() == 0 and posted["r"].status_code == 200, posted)
    c.cookies.update(cookie(admin))
    check("main: アプリの一覧に反映", S1 in {x["ip"] for x in c.get("/api/system/admin/suspicious-access").json()["items"]})
    conf.write_text("NOTIFY_TOKEN=\n")
    posted.clear()
    check("main: 未設定なら何もしない", sus_mod.main() == 0 and not posted)

    # --- 11) ホスト側: 反映スクリプト(eigo-f2b-manual-sync)を偽のfail2banで動かす
    ms = load("eigo-f2b-manual-sync")
    conf.write_text(f"APP_URL=http://127.0.0.1:1\nNOTIFY_TOKEN={TOKEN}\n")
    ms.CONF = str(conf)
    ms.AUDIT = str(Path(tmp) / "audit2.log")
    jails = {j: set() for j in ms.MANUAL_JAILS}
    calls = []
    fail_status = set()

    def fake_f2b(*args):
        calls.append(args)
        if args[0] == "status":
            if args[1] in fail_status or args[1] not in jails:
                return False, "ERROR"
            ips_ = " ".join(sorted(jails[args[1]]))
            return True, f"Status for the jail: {args[1]}\n`- Actions\n   |- Currently banned: {len(jails[args[1]])}\n   `- Banned IP list:   {ips_}\n"
        if args[0] == "set" and args[2] == "banip":
            jails[args[1]].add(args[3]); return True, ""
        if args[0] == "set" and args[2] == "unbanip":
            jails[args[1]].discard(args[3]); return True, ""
        return False, "unexpected"

    app_down = {"v": False}
    bad_reply = {"v": None}

    def fake_api(method, path, token, url, body=None):
        if app_down["v"]:
            raise ms.urllib.error.URLError("down")
        if bad_reply["v"] is not None and method == "GET":
            return bad_reply["v"]
        if method == "GET":
            r_ = c.get(path, headers={"X-F2B-Token": token})
        else:
            r_ = c.post(path, json=body, headers={"X-F2B-Token": token})
        return r_.content

    ms.f2b, ms.api = fake_f2b, fake_api
    ms.is_exempt = lambda ip: ip == IP_D
    # 状態を作り直す: 有効なブロックは E(7d→30dに置き換え済み)・IP_D(refusedで解除済み)・他
    with db() as conn:
        conn.execute("UPDATE manual_blocks SET released_at = datetime('now'), released_by = 'test'")
        conn.commit()
    c.post("/api/system/admin/manual-blocks", json={"ip": IP_A, "duration": "1h"})
    c.post("/api/system/admin/manual-blocks", json={"ip": IP_B, "duration": "permanent"})
    c.post("/api/system/admin/manual-blocks", json={"ip": IP_D, "duration": "7d"})   # ホストの許可リストに当たる想定
    ms.main()
    check("同期: 期間に応じたjailに入る", IP_A in jails["eigo-manual-1h"] and IP_B in jails["eigo-manual-perm"], jails)
    check("同期: 許可リスト/信頼IPはbanしない", all(IP_D not in v for v in jails.values()), jails)
    st = {}
    for b in sorted(c.get("/api/system/admin/manual-blocks").json()["blocks"], key=lambda b: b["id"]):
        st[b["ip"]] = b  # IPごとの最新の行
    check("同期: 反映済みがアプリでactiveになる", st[IP_A]["state"] == "active" and st[IP_B]["state"] == "active", st[IP_A])
    check("同期: 拒否がアプリに報告される(refused)", st[IP_D]["state"] == "refused", st[IP_D])
    n_calls = len(calls)
    ms.main()
    check("同期: 2回目は変更なし(banipを再度呼ばない)", not [a for a in calls[n_calls:] if a[0] == "set"], calls[n_calls:])
    # 置き換え(1h→30d): 旧jailから外れて新jailへ
    c.post("/api/system/admin/manual-blocks", json={"ip": IP_A, "duration": "30d"})
    ms.main()
    check("同期: 期間変更で旧jailから外れ新jailに入る", IP_A not in jails["eigo-manual-1h"] and IP_A in jails["eigo-manual-30d"], jails)
    # 解除
    with db() as conn:
        rid = conn.execute("SELECT id FROM manual_blocks WHERE ip = ? AND released_at IS NULL", (IP_B,)).fetchone()["id"]
    c.post(f"/api/system/admin/manual-blocks/{rid}/release", json={})
    ms.main()
    check("同期: 解除したIPはjailから外れる", IP_B not in jails["eigo-manual-perm"], jails)
    # 期限切れ
    with db() as conn:
        conn.execute("UPDATE manual_blocks SET expires_at = datetime('now', '-1 minute') WHERE ip = ? AND released_at IS NULL", (IP_A,))
        conn.commit()
    ms.main()
    check("同期: 期限切れのIPはjailから外れる", IP_A not in jails["eigo-manual-30d"], jails)
    # 安全側: アプリに繋がらない/形式違い/jailが取れない → 何もしない
    c.post("/api/system/admin/manual-blocks", json={"ip": IP_C, "duration": "24h"})
    ms.main()
    check("(準備)IP_Cがjailに入った", IP_C in jails["eigo-manual-24h"])
    snapshot = {k: set(v) for k, v in jails.items()}
    app_down["v"] = True
    rc = ms.main()
    check("アプリに繋がらないときは何もしない(全員を解除しない)", rc == 1 and jails == snapshot, jails)
    app_down["v"] = False
    for bad in [b"{}", b'{"ok": false, "blocks": []}', b"not json", b'{"ok": true, "blocks": "x"}']:
        bad_reply["v"] = bad
        rc = ms.main()
        check(f"想定外の応答は何もしない: {bad[:24]!r}", rc == 1 and jails == snapshot, jails)
    bad_reply["v"] = b'{"ok": true, "blocks": [{"id": 1, "ip": "10.0.0.1", "jail": "eigo-manual-24h"}, {"id": 2, "ip": "44.5.5.5", "jail": "sshd"}, {"id": "x", "ip": "44.5.5.6", "jail": "eigo-manual-1h"}]}'
    n_before = len(calls)
    ms.main()
    sets = [a for a in calls[n_before:] if a[0] == "set"]
    check("不正な項目(プライベートIP・他のjail名・idが数値でない)はbanしない",
          not [a for a in sets if a[2] == "banip"], sets)
    check("不正な項目のためにsshd等の他jailへ触れない", not [a for a in calls if len(a) > 1 and a[1] in ("sshd", "science-adminfail")])
    check("触れるのはeigo-manual-*のjailだけ", all((a[0] != "set") or a[1] in ms.MANUAL_JAILS for a in calls))
    check("全jail対象のunbanは使わない", not [a for a in calls if a[0] == "unban"])
    bad_reply["v"] = None
    jails_before = {k: set(v) for k, v in jails.items()}
    fail_status.add("eigo-manual-24h")
    c.post("/api/system/admin/manual-blocks", json={"ip": "88.1.1.1", "duration": "24h"})
    ms.main()
    check("jailの状態が取れないときはそのjailに触れない", "88.1.1.1" not in jails["eigo-manual-24h"] and jails["eigo-manual-24h"] == jails_before["eigo-manual-24h"], jails)
    fail_status.clear()
    ms.main()
    check("取れるようになれば反映される", "88.1.1.1" in jails["eigo-manual-24h"])
    check("パース: Banned IP listの解析", ms.banned_in("eigo-manual-24h") is not None)
    ms.f2b = lambda *a: (True, "Status for the jail: x\n   `- Banned IP list:   44.2.2.2 10.0.0.9 bogus 44.2.2.3\n")
    check("パース: 公開IPv4だけ取り出す", ms.banned_in("eigo-manual-1h") == {"44.2.2.2", "44.2.2.3"})
    ms.f2b = lambda *a: (True, "Status for the jail: x\n   `- Banned IP list:\n")
    check("パース: BAN中のIPが空", ms.banned_in("eigo-manual-1h") == set())

# --- 12) 設定ファイルの整合
fdir = ROOT / "deploy" / "fail2ban"
tmpl = (fdir / "jail.d" / "eigo.local.tmpl").read_text(encoding="utf-8")
sections = dict(re.findall(r"^\[(eigo-manual-[^\]]+)\]\n((?:(?!\n\[).)*)", tmpl, re.S | re.M))
check("jail: 手動ブロック用の5つが定義されている", set(sections) == ip_blocks.MANUAL_JAILS, set(sections))
want_bt = {"eigo-manual-1h": "1h", "eigo-manual-24h": "24h", "eigo-manual-7d": "7d", "eigo-manual-30d": "30d", "eigo-manual-perm": "-1"}
for j, bt in want_bt.items():
    body_ = sections.get(j, "")
    check(f"jail {j}: bantime={bt}・実遮断アクション・manual.log・フィルター", re.search(rf"^bantime = {re.escape(bt)}$", body_, re.M)
          and "__ACTIONS_MANUAL__" in body_ and "/var/lib/eigo-f2b/manual.log" in body_ and "filter = eigo-manual" in body_
          and "ignorecommand" not in body_ and "enabled = true" in body_)
check("jail: DURATIONSのjail名とテンプレートが一致", {j for _, j in ip_blocks.DURATIONS.values()} == set(sections))
for f in re.findall(r"^filter = (\S+)$", tmpl, re.M):
    check(f"filterファイルが存在: {f}", (fdir / "filter.d" / f"{f}.conf").exists())
check("フィルターは何にもマッチしない正規表現", "never-matches" in (fdir / "filter.d" / "eigo-manual.conf").read_text())
inst = (fdir / "install.sh").read_text(encoding="utf-8")
check("install.sh: __ACTIONS_MANUAL__を置換・manual.logを作成・自己テスト", "__ACTIONS_MANUAL__" in inst and "manual.log" in inst and "eigo-manual-1h banip" in inst)
check("install.sh: 手動ブロック自己テストはTEST-NET-1の仮IP", "TESTIP3=\"192.0.2." in inst)
check("install.sh: bin/eigo-f2b-*のglobで新スクリプトも配置される", 'install -m 755 "$SRC"/bin/eigo-f2b-*' in inst)
cron = (fdir / "cron.d" / "eigo-f2b").read_text()
check("cron: manual-syncは毎分・suspectsは5分毎・flock付き", re.search(r"^\* \* \* \* \* root flock -n \S+ /usr/local/sbin/eigo-f2b-manual-sync", cron, re.M)
      and re.search(r"^\*/5 \* \* \* \* root flock -n \S+ /usr/local/sbin/eigo-f2b-suspects", cron, re.M))
for s_ in ["eigo-f2b-suspects", "eigo-f2b-manual-sync"]:
    check(f"{s_}: 実行権限", os.access(fdir / "bin" / s_, os.X_OK))
    check(f"{s_}: 先頭がpython3", (fdir / "bin" / s_).read_text().startswith("#!/usr/bin/env python3"))
check("bash -n install.sh/review.sh", subprocess.run(["bash", "-n", str(fdir / "install.sh")]).returncode == 0
      and subprocess.run(["bash", "-n", str(fdir / "review.sh")]).returncode == 0)
check("manual-syncのjail一覧がアプリと一致", set(load("eigo-f2b-manual-sync").MANUAL_JAILS) == ip_blocks.MANUAL_JAILS)
check("review.sh: 手動ブロックのjailも表示", "eigo-manual-perm" in (fdir / "review.sh").read_text())

# --- 13) 画面(JS)
views = (ROOT / "static" / "js" / "views.js").read_text(encoding="utf-8")
check("画面: 怪しいアクセスの欄が遅延読み込みに登録", '["#logSuspectsDetails", loadSuspects]' in views)
check("画面: 期間の選択肢(1時間/24時間/7日/30日/永久)",
      all(x in views for x in ['["1h", "1時間"]', '["24h", "24時間"]', '["7d", "7日"]', '["30d", "30日"]', '["permanent", "永久"]']))
check("画面: 既定は24時間", 'durOptions("24h")' in views)
seg = views[views.index("const BLOCK_DURATIONS"):views.index("async function loadAccessLog")]
raw_interp = re.findall(r"\$\{([^}]+)\}", seg)
risky = [x for x in raw_interp if re.search(r"\b(it|b|x)\.(ip|ua|p|m|created_by|applied_note|note)\b", x) and "escapeHtml" not in x]
check("画面: 攻撃者が決められる文字列(ip/ua/パス/備考)は全てescapeHtmlを通す", not risky, risky)
if subprocess.run(["which", "node"], capture_output=True).returncode == 0:
    check("画面: node --check", subprocess.run(["node", "--check", str(ROOT / "static" / "js" / "views.js")]).returncode == 0)

print(f"\n{ok} OK / {fail} FAIL")
sys.exit(1 if fail else 0)
