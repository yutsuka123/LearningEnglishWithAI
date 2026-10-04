"""パスワード再発行(管理者が本人確認のうえ発行する使い捨てリンク)の検査(2026-10-04・ver1.5.12)。

  .venv/bin/python scripts/check_password_reset.py     # 0=全部OK(本番・外部には触れない・.envの無い環境で実行)

隔離したDATA_DIR・MULTIUSER=1(本番と同じ認証の経路)・FastAPIのTestClientで、次を確かめる:
 - 依頼(password-help): 登録の有無によらず同じ応答・お問い合わせとして保存(user_idは空)・連打/IP回数の制限
 - 管理者専用: 未ログイン/一般ユーザーは拒否・管理者・ゲスト・退会済み・無効には発行できない
 - リンク: トークンはDBにハッシュだけ・再発行で古いリンクは失効・期限切れ/取り消し/使用済みは無効・1回限り
 - 再設定: パスワードポリシー違反ではリンクを消費しない・成功で全セッション無効化・ロック解除・自動ログインしない
 - ログにトークンを出さない・退会でトークンも消える
"""

from __future__ import annotations

import atexit
import logging
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_TMP = tempfile.mkdtemp(prefix="check_pwreset_")
atexit.register(shutil.rmtree, _TMP, ignore_errors=True)
os.environ.update({
    "DATA_DIR": _TMP, "ALLOW_FRESH_DB": "1", "MULTIUSER": "1", "SESSION_SECRET": "check-secret",
    "OPENAI_API_KEY": "sk-test-not-a-real-key", "SIGNUP_OPEN": "1",
})
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from app.database import db, init_db  # noqa: E402
from app.main import app  # noqa: E402
from app.routers import password_reset as pr  # noqa: E402
from app.services import auth, password_reset  # noqa: E402

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("  OK   " if cond else "  FAIL ") + name + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


# ログ(トークンが出ていないことの確認用)
class _Cap(logging.Handler):
    def __init__(self):
        super().__init__()
        self.lines: list[str] = []

    def emit(self, record):
        self.lines.append(record.getMessage())


cap = _Cap()
logging.getLogger().addHandler(cap)
logging.getLogger().setLevel(logging.DEBUG)

init_db()
ADMIN, USER1, USER2, INACTIVE, ADMIN2 = "admin@example.test", "u1@example.test", "u2@example.test", "gone@example.test", "admin2@example.test"
PW_OLD, PW_NEW = "OldPass#1234", "NewPass#5678"
with db() as conn:
    admin_id = auth.create_user(conn, ADMIN, "AdminPass#1234", role="admin", email=ADMIN, display_name="運営")
    admin2_id = auth.create_user(conn, ADMIN2, "AdminPass#1234", role="admin", email=ADMIN2, display_name="運営2")
    u1 = auth.create_user(conn, USER1, PW_OLD, email=USER1, display_name="たろう")
    u2 = auth.create_user(conn, USER2, PW_OLD, email=USER2, display_name="はなこ")
    gone = auth.create_user(conn, INACTIVE, PW_OLD, email=INACTIVE, display_name="退会者")
    conn.execute("UPDATE users SET is_active = 0 WHERE id = ?", (gone,))
    guest_id = auth.ensure_guest_user_id(conn)
    # チャージ履歴(本人確認の手がかり)
    conn.execute("INSERT INTO balance_ledger (user_id, delta_jpy, balance_after, reason, note) VALUES (?, 800, 800, 'paypay', 'x')", (u1,))


def client(ip: str = "198.51.100.1") -> TestClient:
    return TestClient(app, base_url="https://testserver", headers={"X-Forwarded-For": ip})


def login(c: TestClient, username: str, password: str):
    return c.post("/api/auth/login", json={"username": username, "password": password})


pr._HITS.clear()
print("== 1. 依頼(パスワードを忘れた方) POST /api/auth/password-help")
c = client("198.51.100.10")
r = c.post("/api/auth/password-help", json={"email": USER1.upper(), "nickname": "たろう", "contact": "alt@example.test", "note": "9月に登録・800円チャージ"})
check("登録済みのメールでも受け付ける(未ログインで使える)", r.status_code == 200 and r.json().get("ok") is True, f"{r.status_code} {r.text[:80]}")
r2 = client("198.51.100.11").post("/api/auth/password-help", json={"email": "nobody@example.test"})
check("未登録のメールでも同じ応答(登録の有無を漏らさない)", r2.status_code == 200 and r2.json() == r.json(), r2.text[:80])
with db() as conn:
    rows = conn.execute("SELECT user_id, kind, name, email, content FROM inquiries ORDER BY id").fetchall()
check("お問い合わせ(種別=パスワード再発行)として保存される", len(rows) == 2 and all(x["kind"] == "パスワード再発行" for x in rows), str([dict(x)["kind"] for x in rows]))
check("user_idは空(認証不要のパスでは運営者になる仕様のため使わない)", all(x["user_id"] is None for x in rows))
check("返信先=連絡先があればそれ・なければ登録メール", rows[0]["email"] == "alt@example.test" and rows[1]["email"] == "nobody@example.test", rows[0]["email"] + "/" + rows[1]["email"])
check("本文に登録メール・補足が入る(管理者が本人確認に使う)", f"登録したメールアドレス: {USER1}" in rows[0]["content"] and "800円" in rows[0]["content"])
r3 = client("198.51.100.12").post("/api/auth/password-help", json={"email": USER1})
with db() as conn:
    n = conn.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0]
check("同じ登録メールの連続依頼(10分以内)は保存しないが同じ応答", r3.status_code == 200 and r3.json().get("ok") is True and n == 2, f"n={n}")
rbad = client("198.51.100.13").post("/api/auth/password-help", json={"email": "not-an-email"})
check("メールの形式が不正なら拒否(2010)", rbad.status_code == 400 and rbad.headers.get("X-Error-Code") == "2010", rbad.text[:80])
codes = []
for i in range(7):
    rr = client("198.51.100.20").post("/api/auth/password-help", json={"email": f"x{i}@example.test"})
    codes.append(rr.status_code)
check("同じIPからの依頼は1時間に5回まで(6回目から429)", codes[:5] == [200] * 5 and codes[5] == 429, str(codes))

print("== 2. 管理者専用のAPI")
pr._HITS.clear()
anon = client()
r = anon.get("/api/auth/admin/password-reset/lookup?q=u1")
check("未ログインは拒否(401)", r.status_code == 401, str(r.status_code))
cu = client("198.51.100.30")
check("一般ユーザーでログインできる", login(cu, USER2, PW_OLD).status_code == 200)
r = cu.get("/api/auth/admin/password-reset/lookup?q=u1")
check("一般ユーザーは拒否(2004)", r.status_code == 403 and r.headers.get("X-Error-Code") == "2004", f"{r.status_code} {r.text[:60]}")
r = cu.post("/api/auth/admin/password-reset/link", json={"user_id": u1})
check("一般ユーザーはリンクを作れない", r.status_code == 403)
ca = client("198.51.100.31")
check("管理者でログインできる", login(ca, ADMIN, "AdminPass#1234").status_code == 200)
look = ca.get("/api/auth/admin/password-reset/lookup", params={"q": USER1})
js = look.json()
check("管理者は登録メールで検索できる(本人確認の手がかりつき)", look.status_code == 200 and len(js["users"]) == 1 and js["users"][0]["id"] == u1, look.text[:120])
cl = js["users"][0]
check("手がかり: ニックネーム・登録日・チャージ履歴・発行可否が返る", cl["display_name"] == "たろう" and cl["created_at"] and cl["charges"]["count"] == 1 and cl["charges"]["sum_jpy"] == 800 and cl["can_issue"] is True, str(cl))
check("ニックネームの部分一致でも検索できる", len(ca.get("/api/auth/admin/password-reset/lookup", params={"q": "たろ"}).json()["users"]) == 1)
check("ゲストの疑似ユーザーは検索結果に出ない", all(u["id"] != guest_id for u in ca.get("/api/auth/admin/password-reset/lookup", params={"q": str(guest_id)}).json()["users"]))
check("%や_は文字として扱う(全件ヒットしない)", len(ca.get("/api/auth/admin/password-reset/lookup", params={"q": "%"}).json()["users"]) == 0)

print("== 3. リンクの発行")
for uid, label in ((admin2_id, "管理者"), (guest_id, "ゲストの疑似ユーザー"), (gone, "退会済み/無効")):
    r = ca.post("/api/auth/admin/password-reset/link", json={"user_id": uid})
    check(f"{label}には発行できない(2018)", r.status_code == 400 and r.headers.get("X-Error-Code") == "2018", f"{r.status_code} {r.text[:60]}")
r = ca.post("/api/auth/admin/password-reset/link", json={"user_id": 99999})
check("存在しないユーザーは7001", r.status_code in (400, 404) and r.headers.get("X-Error-Code") == "7001", f"{r.status_code} {r.headers.get('X-Error-Code')}")
r = ca.post("/api/auth/admin/password-reset/link", json={"user_id": u1, "hours": 24, "note": "登録メール・チャージ額が一致"})
j = r.json()
check("発行できる(リンクのパス・有効期限が返る)", r.status_code == 200 and j["path"].startswith("/reset-password#t=") and j["expires_at"] and j["hours"] == 24, r.text[:100])
tok1 = j["path"].split("#t=", 1)[1]
check("リンクは絶対URLでも返る(https)", j["url"].startswith("https://") and j["url"].endswith(j["path"]), j["url"][:40])
with db() as conn:
    rows = conn.execute("SELECT token_hash, created_by, note FROM password_reset_tokens WHERE user_id = ?", (u1,)).fetchall()
check("DBにはトークン本体ではなくsha256のハッシュだけ・発行した管理者と控えを記録", len(rows) == 1 and tok1 not in rows[0]["token_hash"] and len(rows[0]["token_hash"]) == 64 and rows[0]["created_by"] == admin_id and "一致" in rows[0]["note"], str(dict(rows[0])) if rows else "なし")
check("トークンは十分長い(43文字以上)", len(tok1) >= 43, str(len(tok1)))
r = ca.post("/api/auth/admin/password-reset/link", json={"user_id": u1, "hours": 72})
tok2 = r.json()["path"].split("#t=", 1)[1]
check("hoursは1/24/72のみ(72を指定できる)", r.json()["hours"] == 72)
r = ca.post("/api/auth/admin/password-reset/link", json={"user_id": u1, "hours": 9999})
tok3 = r.json()["path"].split("#t=", 1)[1]
check("許可されない時間は既定の24時間になる", r.json()["hours"] == 24)
pub = client("198.51.100.40")
chk = lambda t: pub.post("/api/auth/password-reset/check", json={"token": t}).json().get("valid")  # noqa: E731
check("再発行すると古いリンクは失効する(1・2番目は無効・3番目だけ有効)", chk(tok1) is False and chk(tok2) is False and chk(tok3) is True)
check("でたらめなトークン・空は無効", chk("x" * 40) is False and chk("") is False)

print("== 4. 再設定(新しいパスワードの設定)")
c_old = client("198.51.100.50")
login(c_old, USER1, PW_OLD)
me = c_old.get("/api/auth/me")
check("再設定前: 古いセッションで本人として入れている", me.status_code == 200 and (me.json().get("user") or me.json()).get("username") == USER1, me.text[:80])
for i in range(3):   # ロックされていた状態を作る
    auth.record_login_failure(USER1, "198.51.100.50")
check("(前提)失敗が続いてログインがロックされている", auth.login_locked(USER1, "198.51.100.50"))
r = pub.post("/api/auth/password-reset", json={"token": tok3, "new_password": "short"})
check("パスワードのポリシー違反は拒否(2012)・リンクは消費されない", r.status_code == 400 and r.headers.get("X-Error-Code") == "2012" and chk(tok3) is True, f"{r.status_code} {r.text[:80]}")
r = pub.post("/api/auth/password-reset", json={"token": tok3, "new_password": PW_NEW})
check("正しいリンク+新しいパスワードで成功", r.status_code == 200 and r.json().get("ok") is True and "set-cookie" not in {k.lower() for k in r.headers}, f"{r.status_code} {r.text[:80]} {dict(r.headers)}")
check("自動ログインはしない(セッションCookieを発行しない)", not pub.cookies.get(auth.SESSION_COOKIE))
check("ログインのロックが解除される", not auth.login_locked(USER1, "198.51.100.50"))
check("古いパスワードではログインできない", login(client("198.51.100.51"), USER1, PW_OLD).status_code == 401)
c_new = client("198.51.100.52")
check("新しいパスワードでログインできる", login(c_new, USER1, PW_NEW).status_code == 200)
me2 = c_old.get("/api/auth/me")
check("再設定前の古いセッションは無効になる(全端末ログアウト)", not (me2.status_code == 200 and (me2.json().get("user") or me2.json()).get("username") == USER1), f"{me2.status_code} {me2.text[:80]}")
r = pub.post("/api/auth/password-reset", json={"token": tok3, "new_password": "Another#9999"})
check("リンクは1回限り(2回目は2017)", r.status_code == 400 and r.headers.get("X-Error-Code") == "2017", f"{r.status_code} {r.text[:60]}")
check("使用済みのリンクはcheckでも無効", chk(tok3) is False)

print("== 5. 期限切れ・取り消し・同時使用")
t = ca.post("/api/auth/admin/password-reset/link", json={"user_id": u2}).json()["path"].split("#t=", 1)[1]
with db() as conn:
    conn.execute("UPDATE password_reset_tokens SET expires_at = datetime('now', '-1 minutes') WHERE user_id = ? AND used_at IS NULL", (u2,))
check("期限切れのリンクは無効(check・apply)", chk(t) is False and pub.post("/api/auth/password-reset", json={"token": t, "new_password": PW_NEW}).status_code == 400)
t = ca.post("/api/auth/admin/password-reset/link", json={"user_id": u2}).json()["path"].split("#t=", 1)[1]
rv = ca.post("/api/auth/admin/password-reset/revoke", json={"user_id": u2})
check("管理者は取り消せる(取り消すと無効)", rv.status_code == 200 and rv.json()["revoked"] == 1 and chk(t) is False)
t = ca.post("/api/auth/admin/password-reset/link", json={"user_id": u2}).json()["path"].split("#t=", 1)[1]
with db() as conn:
    # 同時に2回押された状況: 先にUPDATEが通った後は、同じトークンのUPDATEは0件になる(原子的な1回限り)
    first = password_reset.consume(conn, t, PW_NEW)
    second = password_reset.consume(conn, t, "Another#7777")
check("同じトークンの2回目の消費は失敗する(原子的な1回限り)", first[0] == "ok" and second[0] == "invalid", f"{first} {second}")
with db() as conn:
    check("管理者のパスワードは変わらない・ユーザーU2は新しいパスワードになった", auth.authenticate(conn, ADMIN, "AdminPass#1234") is not None and auth.authenticate(conn, USER2, PW_NEW) is not None)
t = ca.post("/api/auth/admin/password-reset/link", json={"user_id": u1}).json()["path"].split("#t=", 1)[1]
with db() as conn:
    conn.execute("UPDATE users SET is_active = 0 WHERE id = ?", (u1,))
check("発行後に退会/無効になったユーザーのリンクは使えない", chk(t) is False and pub.post("/api/auth/password-reset", json={"token": t, "new_password": PW_NEW}).status_code == 400)
with db() as conn:
    conn.execute("UPDATE users SET is_active = 1 WHERE id = ?", (u1,))

print("== 6. 回数制限・ログ・退会")
pr._HITS.clear()
spam = client("198.51.100.60")
codes = [spam.post("/api/auth/password-reset", json={"token": "bad" * 10, "new_password": PW_NEW}).status_code for _ in range(22)]
check("再設定の試行はIPごとに10分に20回まで(21回目から429)", codes[:20] == [400] * 20 and codes[20] == 429, str(codes[18:22]))
spam2 = client("198.51.100.61")
codes = [spam2.post("/api/auth/password-reset/check", json={"token": "bad" * 10}).status_code for _ in range(32)]
check("リンクの確認はIPごとに10分に30回まで", codes[:30] == [200] * 30 and codes[30] == 429, str(codes[29:32]))
joined = "\n".join(cap.lines)
all_tokens = [tok1, tok2, tok3, t]
check("ログにトークン本体が出ていない", not any(x in joined for x in all_tokens))
check("ログに登録メールアドレスの本文が出ていない(依頼の保存・リンク発行)", USER1 not in joined.split("password-help")[-1] if "password-help" in joined else True)
tw = ca.post("/api/auth/admin/password-reset/link", json={"user_id": u2}).json()["path"].split("#t=", 1)[1]
cw = client("198.51.100.62")
login(cw, USER2, PW_NEW)
rw = cw.post("/api/auth/withdraw", json={"reasons": ["other"], "detail": "check"})
with db() as conn:
    left = conn.execute("SELECT COUNT(*) FROM password_reset_tokens WHERE user_id = ?", (u2,)).fetchone()[0]
check("退会するとそのユーザーの再設定リンクも消える", rw.status_code == 200 and left == 0, f"{rw.status_code} left={left}")

print()
if FAILS:
    print(f"❌ 失敗 {len(FAILS)} 件: " + ", ".join(FAILS))
    raise SystemExit(1)
print("✅ すべて成功")
