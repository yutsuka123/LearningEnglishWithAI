"""ver1.5.17(管理系の404化・_require_admin集約)のローカル検査。一時データ領域(DATA_DIR)で動かし、本番にも開発DBにも触れない。
使い方: リポジトリ直下で `.venv/bin/python scripts/check_admin_guard.py`(全項目OKなら終了コード0)。"""
import os, sys, tempfile, time
from pathlib import Path
tmp = tempfile.mkdtemp(prefix="eigo_step4_")
os.environ["DATA_DIR"] = tmp
os.environ["MULTIUSER"] = "1"
sys.path.insert(0, os.environ.get("REPO") or str(Path(__file__).resolve().parents[1]))

from fastapi import HTTPException
from fastapi.testclient import TestClient
import app.main as m
from app.database import db, init_db
from app.services import auth

init_db()
def mk(name, role, active=1):
    with db() as conn:
        r = auth.create_user(conn, name, "Passw0rd!x1", role=role)
        uid = r["id"] if isinstance(r, dict) else r
        if not active:
            conn.execute("UPDATE users SET is_active=0 WHERE id=?", (uid,))
        return uid
admin, normal, dead_admin = mk("adm_t", "admin"), mk("usr_t", "user"), mk("adm_dead", "admin", active=0)

def cookie(uid):
    with db() as conn:
        secret = auth.get_session_secret(conn)
        epoch = auth.get_session_epoch(conn, uid)
    return {auth.SESSION_COOKIE: auth.make_session_token(secret, uid, epoch, int(time.time()))}

ok = fail = 0
def check(label, cond, extra=""):
    global ok, fail
    if cond: ok += 1; print("OK  ", label)
    else: fail += 1; print("FAIL", label, extra)

with TestClient(m.app, follow_redirects=False) as c:
    # 未ログイン: 存在しないパスと同じ扱い(どちらも/loginへ)
    a = c.get("/admin/fulfillment"); b = c.get("/zzz-not-exist")
    check("未ログイン: /admin と存在しないパスが同じ応答の型", a.status_code == b.status_code and a.headers["location"].split("?")[0] == b.headers["location"].split("?")[0], (a.status_code, b.status_code))
    # 一般ユーザー: 存在しないパスと同一の404
    c.cookies.clear(); c.cookies.update(cookie(normal))
    for path in ("/admin/fulfillment", "/admin/paypay-test"):
        a = c.get(path); b = c.get("/zzz-not-exist")
        check(f"一般ユーザー {path} は存在しないパスと同じ404", a.status_code == 404 and (a.status_code, a.text, a.headers.get("content-type")) == (b.status_code, b.text, b.headers.get("content-type")), (a.status_code, a.text[:60], b.status_code, b.text[:60]))
    # 一般ユーザー: 末尾スラッシュ・非GET・/admin配下の他のパスも、存在しないパスと全く同じ応答(照査指摘2026-10-19)
    def sig(r): return (r.status_code, r.text, r.headers.get("content-type"), r.headers.get("allow"), r.headers.get("location"),
                        r.headers.get("x-frame-options"), r.headers.get("content-security-policy"))
    for method in ("GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"):
        for path, ref in (("/admin/fulfillment", "/zzz-not-exist"), ("/admin/fulfillment/", "/zzz-not-exist/"),
                          ("/admin/paypay-test/", "/zzz-not-exist/"), ("/admin/base-oauth/status", "/zzz-not-exist/a"),
                          ("/admin", "/zzz"), ("/admin/", "/zzz/")):
            a = c.request(method, path); b = c.request(method, ref)
            check(f"一般ユーザー {method} {path} は存在しないパスと同一応答", sig(a) == sig(b) and a.status_code == 404, (sig(a), sig(b)))
    # 管理者: 開ける
    c.cookies.clear(); c.cookies.update(cookie(admin))
    for path in ("/admin/fulfillment", "/admin/paypay-test"):
        check(f"管理者 {path} は200", c.get(path).status_code == 200)
    check("管理者 /admin/base-oauth/status は404にならない(従来どおり到達できる)", c.get("/admin/base-oauth/status").status_code != 404)
    check("管理者 POST /admin/fulfillment は従来どおり405", c.post("/admin/fulfillment").status_code == 405)
    # robots.txt
    rb = c.get("/robots.txt").text
    check("robots.txtに/adminを載せない", "/admin" not in rb and "Disallow: /api/" in rb)

# 集約した管理者ガード: 9つの入口すべてで 管理者=通る / 一般=403+従来文言
from app.routers import (base_oauth, system, inquiries, password_reset, vocabulary,
                         fulfillment, auth_routes, admin_memos, paypay_test)
cases = [
    (base_oauth._require_admin, "管理者のみ操作できます。", True),
    (system._require_admin, "管理者のみ利用できます。", False),
    (inquiries._require_admin, "管理者のみ閲覧できます。", True),
    (password_reset._require_admin, "管理者のみ利用できます。", True),
    (vocabulary._require_admin, "単語の追加・変更は管理者のみ行えます。", True),
    (fulfillment._require_admin, "管理者のみ操作できます。", True),
    (auth_routes._require_admin, "管理者のみ閲覧できます。", True),
    (admin_memos._require_admin, "管理者のみ利用できます。", True),
    (paypay_test._require_admin, "管理者のみ操作できます。", True),
]
def run(fn, uid, takes_conn):
    tok = auth.set_current_user_id(uid)
    try:
        if takes_conn:
            with db() as conn: return fn(conn)
        return fn()
    finally:
        auth.reset_current_user_id(tok)
for fn, msg, takes_conn in cases:
    name = fn.__module__.split(".")[-1]
    try: run(fn, admin, takes_conn); okA = True
    except Exception as e: okA = False
    try: run(fn, normal, takes_conn); raised = None
    except HTTPException as e: raised = e
    check(f"{name}: 管理者は通る", okA)
    check(f"{name}: 一般は403で従来の文言", raised is not None and raised.status_code == 403 and msg in str(raised.detail), getattr(raised, "detail", None))
# 無効化済み管理者: password_resetだけ弾く(従来どおり)・他は従来どおり通る
try: run(password_reset._require_admin, dead_admin, True); r = False
except HTTPException: r = True
check("password_reset: 無効化済み管理者は弾く", r)
try: run(base_oauth._require_admin, dead_admin, True); r = True
except HTTPException: r = False
check("base_oauth: 無効化済み管理者は従来どおり通る(挙動不変)", r)
print(f"\n{ok} OK / {fail} FAIL")
sys.exit(1 if fail else 0)
