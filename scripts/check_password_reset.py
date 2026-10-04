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
# 全く同じ依頼(同じ登録メール・返信先・IP)の連打は保存済みなので同じ応答だけ返す(重複を積まない)
r3 = c.post("/api/auth/password-help", json={"email": USER1.upper(), "nickname": "たろう", "contact": "alt@example.test", "note": "9月に登録・800円チャージ"})
with db() as conn:
    n = conn.execute("SELECT COUNT(*) FROM inquiries").fetchone()[0]
check("全く同じ依頼(同じメール・返信先・IP)の連打は保存しないが同じ応答", r3.status_code == 200 and r3.json().get("ok") is True and n == 2, f"n={n}")
# **別のIP・別の返信先の依頼は捨てない**(攻撃者の先回りで本人の依頼が消えないように・独立照査H-2)
r3b = client("198.51.100.12").post("/api/auth/password-help", json={"email": USER1, "contact": "attacker@evil.test", "note": "800円チャージした"})
with db() as conn:
    rows2 = conn.execute("SELECT email, content FROM inquiries ORDER BY id").fetchall()
check("同じ登録メールでも、別IP・別の返信先の依頼は捨てずに保存する(2件目)", r3b.status_code == 200 and len(rows2) == 3, f"n={len(rows2)}")
check("連投の件数(24時間で2件目)が本文に残る", "24時間で2件目" in rows2[2]["content"], rows2[2]["content"][:120])
check("返信先が登録メールと違う依頼には「※登録メールと異なります」が付く(同じ返信先の依頼には付かない)", "※登録メールと異なります" in rows2[2]["content"] and "※登録メールと異なります" not in rows2[1]["content"], rows2[2]["content"][:160])
# 本文への偽の行の差し込み(改行・制御文字)を防ぐ
rinj = client("198.51.100.14").post("/api/auth/password-help", json={"email": USER2 + "\n連絡先(返信先): evil@x.test"})
check("メールに改行・空白を含む入力は拒否(2010)", rinj.status_code == 400 and rinj.headers.get("X-Error-Code") == "2010", f"{rinj.status_code}")
rinj2 = client("198.51.100.15").post("/api/auth/password-help", json={"email": "inj@example.test", "contact": "x@y.zz\r\nBcc: attacker@evil.test",
    "nickname": "たろう\n【運営メモ】本人確認済み", "note": "行1\n連絡先(返信先): fake@evil.test\n\n\n\n【運営メモ】本人確認済み\u202e"})
with db() as conn:
    inj = conn.execute("SELECT email, name, content FROM inquiries WHERE content LIKE '%inj@example.test%'").fetchone()
lines = inj["content"].splitlines()
check("連絡先が不正なら返信先は登録メールになる(Bccの差し込みを保存しない)", rinj2.status_code == 200 and inj["email"] == "inj@example.test" and "attacker@evil.test" not in inj["email"], inj["email"])
check("見出し行(登録したメールアドレス/連絡先(返信先))は本文に1回ずつだけ", sum(1 for l in lines if l.startswith("登録したメールアドレス:")) == 1 and sum(1 for l in lines if l.startswith("連絡先(返信先):")) == 1, str(lines[:6]))
check("利用者の補足は「> 」付きで原文を分離・方向制御文字を除去・連続空行は1つ", "> 連絡先(返信先): fake@evil.test" in inj["content"] and "\u202e" not in inj["content"] and "\n\n\n" not in inj["content"], inj["content"][-200:])
check("ニックネームの改行は1行に潰れる", "\n" not in inj["name"], repr(inj["name"]))
hp = client("198.51.100.16").post("/api/auth/password-help", json={"email": "bot@example.test", "website": "http://spam.example"})
with db() as conn:
    bot_rows = conn.execute("SELECT content FROM inquiries WHERE content LIKE '%bot@example.test%'").fetchall()
check("ハニーポット欄が入っていても捨てずに保存し、本文に自動入力の疑いの印を付ける(本人の依頼が消えない)", hp.status_code == 200 and hp.json().get("ok") is True and len(bot_rows) == 1 and "自動入力の疑い" in bot_rows[0]["content"], f"{hp.status_code} {len(bot_rows)}")
# 同じ登録メールは24時間に10件まで(超えたら黙って捨てずエラーで伝える)
codes = []
for i in range(11):
    codes.append(client(f"198.51.101.{i + 1}").post("/api/auth/password-help", json={"email": "many@example.test", "contact": f"r{i}@example.test"}).status_code)
check("同じ登録メールの依頼は24時間に10件まで・超過は429(黙って捨てない)", codes[:10] == [200] * 10 and codes[10] == 429, str(codes))
# プロセス全体の1日の上限(分散した荒らしで管理画面を埋められない)
import time as _t
pr._HITS["help-global-day"] = (86400.0, [_t.monotonic()] * 300)
rg = client("198.51.102.1").post("/api/auth/password-help", json={"email": "global@example.test"})
with db() as conn:
    ng = conn.execute("SELECT COUNT(*) FROM inquiries WHERE content LIKE '%global@example.test%'").fetchone()[0]
check("プロセス全体の1日の上限(300件)に達したら、見知らぬIPの依頼は保存せず429(利用者に伝える)", rg.status_code == 429 and ng == 0, f"{rg.status_code} {ng}")
with db() as conn:
    conn.execute("INSERT INTO login_log (username, ip, success) VALUES (?, ?, 1)", (USER2, "198.51.102.9"))
rk = client("198.51.102.9").post("/api/auth/password-help", json={"email": "known-ip@example.test"})
with db() as conn:
    nk = conn.execute("SELECT COUNT(*) FROM inquiries WHERE content LIKE '%known-ip@example.test%'").fetchone()[0]
check("直近30日にログイン成功のあるIPは、全体の上限に達していても依頼できる(荒らしに枯らされても本人は復旧できる)", rk.status_code == 200 and nk == 1, f"{rk.status_code} {nk}")
pr._HITS.pop("help-global-day", None)
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

reqs = cl.get("requests", [])
check("本人確認の手がかり: この登録メールの依頼が並ぶ(返信先・ニックネーム一致・補足)", len(reqs) >= 2 and all(r["reply_differs"] for r in reqs), str(reqs)[:200])
client("198.51.100.17").post("/api/auth/password-help", json={"email": USER2, "nickname": "はなこ", "note": "10月に登録"})
reqs2 = ca.get("/api/auth/admin/password-reset/lookup", params={"q": USER2}).json()["users"][0]["requests"]
check("返信先が登録メールと同じ依頼は reply_differs=False・ニックネームが登録のお名前と一致", len(reqs2) == 1 and reqs2[0]["reply_differs"] is False and reqs2[0]["nickname_matches"] is True, str(reqs2)[:200])
check("返信先が登録メールと違う依頼に reply_differs=True が付く(管理者の見落とし防止)", any(r["reply_to"] == "attacker@evil.test" and r["reply_differs"] for r in reqs), str(reqs)[:200])
check("ニックネームが登録のお名前と一致/不一致が分かる", any(r["nickname_matches"] is True for r in reqs), str(reqs)[:160])
check("登録メールが使い捨てかどうかが分かる(通常のメールならFalse)", cl["disposable_email"] is False)
check("最近のチャージ(日付・金額)が見える(依頼者への知識照合に使う)", cl["charges"]["recent"] and cl["charges"]["recent"][0]["delta_jpy"] == 800, str(cl["charges"]))
for q in ("²", "9" * 25, "٣"):
    rq = ca.get("/api/auth/admin/password-reset/lookup", params={"q": q})
    check(f"特殊な数字入力でも500にならない({q[:6]})", rq.status_code == 200, str(rq.status_code))
with db() as _c:
    check("オーナー(id=1)はroleがuserでも発行できない", "オーナー" in (password_reset.issue_blocker(_c, {"id": 1, "role": "user", "is_active": 1}) or ""))
print("== 3. リンクの発行")
for uid, label in ((admin2_id, "管理者"), (guest_id, "ゲストの疑似ユーザー"), (gone, "退会済み/無効")):
    r = ca.post("/api/auth/admin/password-reset/link", json={"user_id": uid})
    check(f"{label}には発行できない(2018)", r.status_code == 400 and r.headers.get("X-Error-Code") == "2018", f"{r.status_code} {r.text[:60]}")
r = ca.post("/api/auth/admin/password-reset/link", json={"user_id": 99999})
check("存在しないユーザーは7001", r.status_code in (400, 404) and r.headers.get("X-Error-Code") == "7001", f"{r.status_code} {r.headers.get('X-Error-Code')}")
r = ca.post("/api/auth/admin/password-reset/link", json={"ack_reply_differs": True, "user_id": u1, "hours": 24, "note": "登録メール・チャージ額が一致"})
j = r.json()
check("発行できる(リンクのパス・有効期限が返る)", r.status_code == 200 and j["path"].startswith("/reset-password#t=") and j["expires_at"] and j["hours"] == 24, r.text[:100])
tok1 = j["path"].split("#t=", 1)[1]
check("リンクは絶対URLでも返る(https)", j["url"].startswith("https://") and j["url"].endswith(j["path"]), j["url"][:40])
with db() as conn:
    rows = conn.execute("SELECT token_hash, created_by, note FROM password_reset_tokens WHERE user_id = ?", (u1,)).fetchall()
check("DBにはトークン本体ではなくsha256のハッシュだけ・発行した管理者と控えを記録", len(rows) == 1 and tok1 not in rows[0]["token_hash"] and len(rows[0]["token_hash"]) == 64 and rows[0]["created_by"] == admin_id and "一致" in rows[0]["note"], str(dict(rows[0])) if rows else "なし")
check("トークンは十分長い(43文字以上)", len(tok1) >= 43, str(len(tok1)))
r = ca.post("/api/auth/admin/password-reset/link", json={"ack_reply_differs": True, "user_id": u1, "hours": 72})
tok2 = r.json()["path"].split("#t=", 1)[1]
check("hoursは1/24/72のみ(72を指定できる)", r.json()["hours"] == 72)
r = ca.post("/api/auth/admin/password-reset/link", json={"ack_reply_differs": True, "user_id": u1, "hours": 9999})
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
t = ca.post("/api/auth/admin/password-reset/link", json={"ack_reply_differs": True, "user_id": u1}).json()["path"].split("#t=", 1)[1]
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

print("== 7. レビュー指摘の追加検査(使用時のIP・Hostヘッダ・無効な管理者・掃除・静的パス)")
with db() as conn:
    used = conn.execute("SELECT used_ip_hash FROM password_reset_tokens WHERE used_at IS NOT NULL AND used_ip_hash != '' ORDER BY id LIMIT 1").fetchone()
check("再設定の使用時に、IPの変換値(HMAC・ip_retentionと同じ形式h:+20桁)を記録する(生のIPは保存しない)", used is not None and used[0].startswith("h:") and len(used[0]) == 22 and "198.51" not in used[0], str(used and used[0]))
from app.services import ip_retention as _ipr  # noqa: E402
with db() as conn:
    _same = password_reset.ip_hash(conn, "198.51.100.1") == _ipr.hash_ip("198.51.100.1", _ipr.derive_key(conn))
check("同じIPは同じ変換値になる(ログインログの変換済みIPと突き合わせられる)・IPが空なら空", _same and password_reset.ip_hash(conn, "") == "")
t = ca.post("/api/auth/admin/password-reset/link", json={"ack_reply_differs": True, "user_id": u1}, headers={"Host": "evil.example"}).json()
check("Hostヘッダを偽装しても、発行リンクの宛先は本番ドメインに固定される", t["url"].startswith("https://study.nyangailab.com/reset-password#t="), t["url"][:50])
t = ca.post("/api/auth/admin/password-reset/link", json={"ack_reply_differs": True, "user_id": u1}, headers={"Host": "study.nyangailab.com"}).json()
check("本番ドメインのHostならそのまま使う", t["url"].startswith("https://study.nyangailab.com/reset-password#t="), t["url"][:50])
t = ca.post("/api/auth/admin/password-reset/link", json={"ack_reply_differs": True, "user_id": u1}, headers={"Host": "localhost:8000"}).json()
check("localhostのHostは許可(開発・SSHトンネル用)", t["url"].startswith("http://localhost:8000/reset-password#t="), t["url"][:50])
os.environ["PUBLIC_BASE_URL"] = "https://example.invalid/"
t = ca.post("/api/auth/admin/password-reset/link", json={"ack_reply_differs": True, "user_id": u1}, headers={"Host": "evil.example"}).json()
check("PUBLIC_BASE_URLがあればそれを使う(末尾の/は除く)", t["url"].startswith("https://example.invalid/reset-password#t="), t["url"][:50])
del os.environ["PUBLIC_BASE_URL"]
with db() as conn:
    admin3 = auth.create_user(conn, "admin3@example.test", "AdminPass#1234", role="admin", email="admin3@example.test", display_name="運営3")
c3 = client("198.51.100.70")
check("(前提)3人目の管理者でログインできる", login(c3, "admin3@example.test", "AdminPass#1234").status_code == 200)
with db() as conn:
    conn.execute("UPDATE users SET is_active = 0 WHERE id = ?", (admin3,))
r = c3.post("/api/auth/admin/password-reset/link", json={"user_id": u1})
check("無効化された管理者のセッションではリンクを発行できない", r.status_code in (401, 403), f"{r.status_code}")
# 回数制限の掃除: 24時間の窓のキーが、1時間の窓の掃除で消えない
import time as _t2
now = _t2.monotonic()
pr._HITS.clear()
for i in range(5100):
    pr._HITS[f"old|{i}"] = (3600.0, [now - 7200])
pr._HITS["long|keep"] = (86400.0, [now - 7200])
pr._rate_limited("trigger", 99, 60.0)
check("掃除は窓ごとの長さで判定(24時間の窓の記録は2時間では消えない・1時間の窓の古い記録は消える)", "long|keep" in pr._HITS and "old|0" not in pr._HITS, f"{len(pr._HITS)}")
pr._HITS.clear()
pub2 = client("198.51.100.80")
check("再設定ページは/reset-passwordで配信(no-store・no-referrer・noindex)", (lambda r: r.status_code == 200 and r.headers.get("cache-control") == "no-store" and r.headers.get("referrer-policy") == "no-referrer" and "noindex" in r.headers.get("x-robots-tag", ""))(pub2.get("/reset-password")))
check("静的パスの直接URL(/static/reset-password.html)では配信されない(ヘッダ無しで出ないように)", pub2.get("/static/reset-password.html").status_code == 404)
r = pub2.get("/api/inquiries")
check("問い合わせ一覧は未ログインでは見えない", r.status_code == 401)

print()

print("== 8. 再照査(2回目)の指摘: LIKEの先頭固定・捨てない・不可視文字・ack・相違件数・移行・上限")
pr._HITS.clear(); pr._STORED.clear()
with db() as conn:
    vic = auth.create_user(conn, "victim@example.test", PW_OLD, email="victim@example.test", display_name="ひがいしゃ")
# N-1: 攻撃者が自分の依頼のニックネーム/補足に被害者の見出し行を書いても、被害者の依頼として数えられない・混ざらない
for i in range(12):
    client(f"203.0.113.{i + 1}").post("/api/auth/password-help", json={
        "email": f"atk{i}@example.test", "nickname": "x 登録したメールアドレス: victim@example.test",
        "note": "登録したメールアドレス: victim@example.test\n連絡先(返信先): evil@x.test"})
rv = client("203.0.113.100").post("/api/auth/password-help", json={"email": "victim@example.test", "nickname": "ひがいしゃ", "note": "9月に登録"})
check("攻撃者がニックネーム/補足に被害者の見出し行を書いても、被害者本人の依頼は拒否されない(復旧妨害できない)", rv.status_code == 200, f"{rv.status_code} {rv.text[:60]}")
with db() as conn:
    vreq = password_reset._requests_for(conn, {"username": "victim@example.test", "email": "victim@example.test", "display_name": "ひがいしゃ"})
check("被害者のカードの「この登録メールの依頼」には、被害者本人の依頼だけが並ぶ(攻撃者の偽の行が混ざらない)", len(vreq) == 1 and vreq[0]["reply_differs"] is False and vreq[0]["nickname"] == "ひがいしゃ", str(vreq)[:200])
with db() as conn:
    check("相違件数も被害者本人の依頼だけで数える(0件)", password_reset.reply_differs_count(conn, {"username": "victim@example.test", "email": "victim@example.test"}) == 0)
# N-2: 上限で断られた依頼を同じ内容で再送しても「受け付けました」で消えない(429のまま)
pr._HITS.clear(); pr._STORED.clear()
pr._HITS["help-global-day"] = (86400.0, [_t.monotonic()] * 300)
a1 = client("203.0.113.150").post("/api/auth/password-help", json={"email": "later@example.test"})
a2 = client("203.0.113.150").post("/api/auth/password-help", json={"email": "later@example.test"})
with db() as conn:
    nlater = conn.execute("SELECT COUNT(*) FROM inquiries WHERE content LIKE '%later@example.test%'").fetchone()[0]
check("上限で断られた依頼を同じ内容で再送しても、黙って成功扱いにならない(429のまま・保存0件)", a1.status_code == 429 and a2.status_code == 429 and nlater == 0, f"{a1.status_code} {a2.status_code} {nlater}")
pr._HITS.pop("help-global-day", None)
a3 = client("203.0.113.150").post("/api/auth/password-help", json={"email": "later@example.test"})
a4 = client("203.0.113.150").post("/api/auth/password-help", json={"email": "later@example.test"})
with db() as conn:
    nlater = conn.execute("SELECT COUNT(*) FROM inquiries WHERE content LIKE '%later@example.test%'").fetchone()[0]
check("上限が解けたら保存され、直後の同じ再送は重複として保存しない(1件のまま)", a3.status_code == 200 and a4.status_code == 200 and nlater == 1, f"{a3.status_code} {a4.status_code} {nlater}")
# N-5: 不可視文字
inv_mail = "inv\u2060\u00ad\u034f\ufe0f\u3164@example.test"
ri = client("203.0.113.160").post("/api/auth/password-help", json={"email": inv_mail, "contact": "re\U000e0041ply@example.test", "nickname": "さ\u2060ぶ", "note": "a\u0085b\u2028c"})
with db() as conn:
    irow = conn.execute("SELECT name, email, content FROM inquiries WHERE content LIKE '%inv@example.test%'").fetchone()
check("メールの不可視文字(WJ・SHY・CGJ・VS16・フィラー)は除かれ、登録メールと同じ形で保存される", ri.status_code == 200 and irow is not None and "登録したメールアドレス: inv@example.test\n" in irow["content"], str(dict(irow)) if irow else "なし")
check("返信先のタグ文字も除かれる・ニックネームの不可視文字も除かれる", irow is not None and irow["email"] == "reply@example.test" and irow["name"] == "さぶ", str(dict(irow)) if irow else "")
check("NEL・U+2028で行が割れない(補足は1つの引用行・見出し行を偽装できない)", irow is not None and "> a b c" in irow["content"] and "\x85" not in irow["content"] and "\u2028" not in irow["content"], (irow["content"][-80:] if irow else ""))
check("全角の@・数字はNFKCで通常の形に直る", pr._clean_line("ｖｉｃｔｉｍ＠ｅｘａｍｐｌｅ．ｔｅｓｔ", 300, strict=True) == "victim@example.test")
check("絵文字の異体字セレクタはニックネーム(非strict)では残る・メール(strict)では除く", pr._clean_line("❤\ufe0f", 10) == "❤\ufe0f" and pr._clean_line("a\ufe0f@b.cc", 30, strict=True) == "a@b.cc")
# N-4/N-6: 返信先相違のackをサーバーで要求・控えへサーバーが印を付ける・5件積んでも相違件数は消えない
pr._HITS.clear(); pr._STORED.clear()
with db() as conn:
    tgt = auth.create_user(conn, "target@example.test", PW_OLD, email="target@example.test", display_name="たーげっと")
client("203.0.113.170").post("/api/auth/password-help", json={"email": "target@example.test", "contact": "attacker2@evil.test"})
for i in range(6):
    client(f"203.0.113.{171 + i}").post("/api/auth/password-help", json={"email": "target@example.test", "nickname": f"n{i}"})
lk = ca.get("/api/auth/admin/password-reset/lookup", params={"q": "target@example.test"}).json()["users"][0]
check("最新5件が全て同じ返信先でも、30日分の相違件数(reply_differs_count)は消えない", len(lk["requests"]) == 5 and all(not r["reply_differs"] for r in lk["requests"]) and lk["reply_differs_count"] == 1, f"{len(lk['requests'])} {lk['reply_differs_count']}")
rn = ca.post("/api/auth/admin/password-reset/link", json={"user_id": tgt, "note": "確認した"})
with db() as conn:
    ntok = conn.execute("SELECT COUNT(*) FROM password_reset_tokens WHERE user_id = ?", (tgt,)).fetchone()[0]
check("返信先相違の依頼があるのにackなしの発行は拒否される(2018・リンクは作られない)", rn.status_code == 400 and rn.headers.get("X-Error-Code") == "2018" and ntok == 0 and "異なる" in rn.text, f"{rn.status_code} {rn.text[:80]} {ntok}")
ry = ca.post("/api/auth/admin/password-reset/link", json={"user_id": tgt, "note": "x" * 200, "ack_reply_differs": True})
with db() as conn:
    note_saved = conn.execute("SELECT note FROM password_reset_tokens WHERE user_id = ? ORDER BY id DESC LIMIT 1", (tgt,)).fetchone()[0]
check("ack付きなら発行でき、サーバーが控えの先頭に「[返信先相違あり]」を付ける(200字の上限内・422にならない)", ry.status_code == 200 and note_saved.startswith("[返信先相違あり] ") and len(note_saved) == 200, f"{ry.status_code} {len(note_saved)} {note_saved[:30]}")
with db() as conn:
    tgt2 = auth.create_user(conn, "plain@example.test", PW_OLD, email="plain@example.test", display_name="ぷれーん")
rp = ca.post("/api/auth/admin/password-reset/link", json={"user_id": tgt2, "note": "一致"})
with db() as conn:
    note_plain = conn.execute("SELECT note FROM password_reset_tokens WHERE user_id = ? ORDER BY id DESC LIMIT 1", (tgt2,)).fetchone()[0]
check("相違のない依頼(依頼なし)ではackなしで発行でき、控えに印は付かない", rp.status_code == 200 and note_plain == "一致", f"{rp.status_code} {note_plain}")
# N-7: d6fd123で作られた旧スキーマ(used_ip_hash列なし)のDBを移行で直せる
import sqlite3 as _sq
_old = _sq.connect(":memory:")
_old.row_factory = _sq.Row
_old.execute("CREATE TABLE password_reset_tokens (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, token_hash TEXT NOT NULL UNIQUE, created_by INTEGER NOT NULL, created_at TEXT NOT NULL DEFAULT (datetime('now')), expires_at TEXT NOT NULL, used_at TEXT, revoked_at TEXT, note TEXT NOT NULL DEFAULT '')")
from app import database as _dbm  # noqa: E402
_dbm._add_col(_old, "password_reset_tokens", "used_ip_hash", "used_ip_hash TEXT NOT NULL DEFAULT ''")
_dbm._add_col(_old, "password_reset_tokens", "used_ip_hash", "used_ip_hash TEXT NOT NULL DEFAULT ''")
check("旧スキーマにも列追加の移行で used_ip_hash が入る(2回実行しても安全)", "used_ip_hash" in {r["name"] for r in _old.execute("PRAGMA table_info(password_reset_tokens)")})
check("(前提)移行のコードが_migrate内にある", 'password_reset_tokens", "used_ip_hash"' in Path(ROOT / "app/database.py").read_text(encoding="utf-8"))
# N-8: 窓の内側のキーが大量でも_HITSは増え続けない
pr._HITS.clear()
now = _t.monotonic()
for i in range(21000):
    pr._HITS[f"live|{i}"] = (86400.0, [now - i * 0.001])
pr._rate_limited("trigger2", 99, 60.0)
check("窓の内側のキーが2万を超えたら、古い順に捨てて上限を保つ(最新は残る)", len(pr._HITS) <= 15001 and "trigger2" in pr._HITS and "live|0" in pr._HITS, f"{len(pr._HITS)}")
pr._HITS.clear(); pr._STORED.clear()

if FAILS:
    print(f"❌ 失敗 {len(FAILS)} 件: " + ", ".join(FAILS))
    raise SystemExit(1)
print("✅ すべて成功")
