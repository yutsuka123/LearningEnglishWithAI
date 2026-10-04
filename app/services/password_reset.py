"""パスワード再発行(2026-10-04・ver1.5.12・オーナー決定)。

パスワードの再設定機能が無く、使い捨てメールでも登録できる設計(確認メールなし・メール送信基盤なし)のため、
**管理者が本人確認のうえ、使い捨ての再設定リンクを発行して本人へ渡す**方式にした。

- リンクのトークンは32バイトの乱数(`secrets.token_urlsafe`)。DBにはsha256のハッシュだけを保存する。
- 有効期限付き(既定24時間)・1回限り。同じユーザーに新しく発行すると古いリンクは失効する。
- 再設定が完了したら、そのユーザーの全セッションを無効化(session_epoch)し、ログインのロックも解除する。自動ログインはしない。
- 発行できないアカウント: 管理者・ゲストの疑似ユーザー・退会済み/無効。
- 管理者が見る本人確認の手がかり(登録日・最終ログイン・チャージ履歴等)は`lookup`で返す。判断は管理者が行う
  (メールを持たない/使い捨てで受け取れない人にも対応するため、自動では本人確認しない)。
"""

from __future__ import annotations

import hashlib
import secrets
import sqlite3
from typing import Optional

from ..config import log
from ..database import OWNER_USER_ID
from . import auth, ip_retention

ALLOWED_HOURS = (1, 24, 72)
DEFAULT_HOURS = 24
LOOKUP_LIMIT = 10


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def issue_blocker(conn: sqlite3.Connection, user: Optional[dict]) -> Optional[str]:
    """このユーザーにリンクを発行できない理由(日本語・管理者向け)。発行できるならNone。"""
    if not user:
        return "ユーザーが見つかりません。"
    if user.get("role") == "admin":
        return "管理者アカウントには発行できません(サーバー側で個別に対応します)。"
    if int(user["id"]) == OWNER_USER_ID:
        return "運営者(オーナー)のアカウントには発行できません(サーバー側で個別に対応します)。"
    if auth.is_guest_user_id(conn, int(user["id"])):
        return "ゲストの疑似ユーザーには発行できません。"
    if not user.get("is_active"):
        return "退会済み・無効のアカウントには発行できません。"
    return None


def create_link(conn: sqlite3.Connection, admin_id: int, user_id: int,
                hours: int = DEFAULT_HOURS, note: str = "") -> tuple[str, str]:
    """(トークン, 有効期限(UTC文字列))を返す。トークン本体は戻り値でしか得られない(DBには残さない)。
    呼び出し側が`issue_blocker`で発行可否を確認済みであること。"""
    if hours not in ALLOWED_HOURS:
        hours = DEFAULT_HOURS
    revoke_all(conn, user_id)
    token = secrets.token_urlsafe(32)
    conn.execute(
        "INSERT INTO password_reset_tokens "
        "(user_id, token_hash, created_by, expires_at, note) "
        "VALUES (?, ?, ?, datetime('now', ?), ?)",
        (user_id, _hash(token), admin_id, f"+{hours} hours", (note or "").strip()[:200]))
    expires = conn.execute(
        "SELECT expires_at FROM password_reset_tokens WHERE token_hash = ?",
        (_hash(token),)).fetchone()[0]
    log.info("password-reset: link issued uid=%s by admin=%s hours=%s", user_id, admin_id, hours)
    return token, expires


def revoke_all(conn: sqlite3.Connection, user_id: int) -> int:
    """そのユーザーの有効なリンク(未使用・未失効)をすべて失効させる。失効させた件数を返す。"""
    cur = conn.execute(
        "UPDATE password_reset_tokens SET revoked_at = datetime('now') "
        "WHERE user_id = ? AND used_at IS NULL AND revoked_at IS NULL", (user_id,))
    return cur.rowcount or 0


def _valid_row(conn: sqlite3.Connection, token: str) -> Optional[sqlite3.Row]:
    if not token or len(token) > 200:
        return None
    return conn.execute(
        "SELECT t.id, t.user_id, u.username, u.role, u.is_active "
        "FROM password_reset_tokens t JOIN users u ON u.id = t.user_id "
        "WHERE t.token_hash = ? AND t.used_at IS NULL AND t.revoked_at IS NULL "
        "AND t.expires_at > datetime('now')", (_hash(token),)).fetchone()


def is_valid(conn: sqlite3.Connection, token: str) -> bool:
    """リンクがいま使えるか(未使用・未失効・期限内・対象ユーザーが発行可能な状態)。"""
    row = _valid_row(conn, token)
    return bool(row) and issue_blocker(conn, dict(row, id=row["user_id"])) is None


def ip_hash(conn: sqlite3.Connection, ip: str) -> str:
    """調査用のIPの変換値(生のIPは保存しない)。`ip_retention`と同じ鍵・同じ変換(HMAC)なので、古くなって変換された
    ログインログのIPと突き合わせられる。総当たりでは元のIPに戻せない。鍵が取れない環境では空文字(何も保存しない)。"""
    if not ip:
        return ""
    try:
        return ip_retention.hash_ip(ip, ip_retention.derive_key(conn))
    except ip_retention.NoKeyError:
        return ""


def consume(conn: sqlite3.Connection, token: str, new_password: str, ip: str = "") -> tuple[str, str]:
    """リンクを使ってパスワードを設定する。戻り値は(結果, 補足):
    ('ok', username) / ('invalid', '') / ('policy', messagesのキー)。
    1回限りの使用は`UPDATE ... WHERE used_at IS NULL`の件数で原子的に保証する(同時に2回押されても片方だけ成功)。"""
    row = _valid_row(conn, token)
    if row is None or issue_blocker(conn, dict(row, id=row["user_id"])) is not None:
        return "invalid", ""
    key = auth.password_policy_key(new_password)
    if key:
        return "policy", key
    cur = conn.execute(
        "UPDATE password_reset_tokens SET used_at = datetime('now'), used_ip_hash = ? "
        "WHERE id = ? AND used_at IS NULL AND revoked_at IS NULL "
        "AND expires_at > datetime('now')", (ip_hash(conn, ip), row["id"]))
    if cur.rowcount != 1:
        return "invalid", ""
    uid = int(row["user_id"])
    auth.set_password(conn, uid, new_password)
    auth.bump_session_epoch(conn, uid)           # 以前のセッション(忘れる前に入っていた端末・盗まれたCookie)を全て無効化
    revoke_all(conn, uid)                         # 他に残っているリンクも失効
    log.info("password-reset: password reset completed uid=%s", uid)
    return "ok", row["username"]


def _like_escape(s: str) -> str:
    return s.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


# 依頼の本文の先頭2行はサーバーが作る(利用者の入力は入らない)。突き合わせはこの先頭の完全一致で行う
# (ニックネーム・補足に同じ文字列を書いても他人の依頼として数えられない・2026-10-04再照査N-1)。
REQUEST_HEAD = "【パスワード再発行の依頼】\n"
_REQ_EMAIL = "登録したメールアドレス: "


def request_prefix(email: str) -> str:
    return REQUEST_HEAD + _REQ_EMAIL + email + "\n"


def _user_mails(user: dict) -> set[str]:
    return {m.strip().lower() for m in (user.get("username"), user.get("email")) if m and "@" in m}


def _requests_for(conn: sqlite3.Connection, user: dict) -> list[dict]:
    """そのユーザーの登録メールについて、直近30日に届いた「パスワード再発行」の依頼(新しい順・最大5件)。
    **返信先が登録メールと違うか**・依頼のニックネームが登録のお名前と合うかを添える(依頼者が他人の登録メールを
    書いて返信先を自分のアドレスにする攻撃を、管理者が見落とさないため・2026-10-04独立照査H-1)。"""
    mails = _user_mails(user)
    out = []
    for m in sorted(mails):
        rows = conn.execute(
            "SELECT id, created_at, name, email, content, status FROM inquiries "
            "WHERE kind = 'パスワード再発行' AND created_at >= datetime('now', '-30 days') "
            "AND instr(content, ?) = 1 ORDER BY id DESC LIMIT 5",
            (request_prefix(m),)).fetchall()
        for r in rows:
            note = ""
            for line in (r["content"] or "").split("\n"):
                if line.startswith("補足(登録時期・チャージの有無など): "):
                    note = line.split(": ", 1)[1]
            reply = (r["email"] or "").strip().lower()
            nick = (r["name"] or "").strip()
            out.append({
                "id": r["id"], "created_at": r["created_at"], "status": r["status"], "nickname": nick,
                "reply_to": reply, "reply_differs": reply not in mails,
                "nickname_matches": (nick == (user.get("display_name") or "").strip()) if nick else None,
                "note": note[:300],
            })
    out.sort(key=lambda x: -x["id"])
    return out[:5]


def reply_differs_count(conn: sqlite3.Connection, user: dict) -> int:
    """直近30日の依頼のうち、返信先が登録メールと違うものの件数(全件を数える。表示は最新5件だけなので、相違のある依頼の
    後に同じ返信先の依頼を積んでも警告が消えないように・2026-10-04再照査N-6)。"""
    mails = sorted(_user_mails(user))
    if not mails:
        return 0
    ph = ",".join("?" * len(mails))
    total = 0
    for m in mails:
        total += conn.execute(
            "SELECT COUNT(*) FROM inquiries WHERE kind = 'パスワード再発行' "
            "AND created_at >= datetime('now', '-30 days') AND instr(content, ?) = 1 "
            f"AND lower(trim(COALESCE(email, ''))) NOT IN ({ph})",
            (request_prefix(m), *mails)).fetchone()[0]
    return total


def ack_required_message(differs: int) -> str:
    """返信先が登録メールと異なる依頼があるのに確認(ack)なしで発行しようとしたときの、管理者向けの文言。"""
    return (f"この登録メールには、返信先が登録メールと異なる依頼が直近30日に{differs}件あります。"
            "画面を検索し直して内容を確認し、確認のうえで発行してください。")


def lookup(conn: sqlite3.Connection, query: str) -> list[dict]:
    """管理者が本人確認の材料にする情報つきで候補ユーザーを返す(最大10件)。
    検索: ユーザー名/メールアドレス(大文字小文字を区別しない完全一致)・呼んでほしいお名前(部分一致)・数字ならユーザーID。"""
    q = (query or "").strip()
    if not q:
        return []
    rows = conn.execute(
        "SELECT id, username, email, display_name, role, is_active, created_at, balance_jpy "
        "FROM users WHERE lower(username) = lower(?) OR lower(email) = lower(?) "
        "OR display_name LIKE ? ESCAPE '\\' OR id = ? ORDER BY id LIMIT ?",
        (q, q, "%" + _like_escape(q) + "%",
         int(q) if (q.isascii() and q.isdigit() and len(q) <= 9) else -1, LOOKUP_LIMIT)).fetchall()
    out = []
    for r in rows:
        u = dict(r)
        if auth.is_guest_user_id(conn, u["id"]):
            continue
        last = conn.execute(
            "SELECT created_at FROM login_log WHERE username = ? AND success = 1 "
            "ORDER BY id DESC LIMIT 1", (u["username"],)).fetchone()
        n30 = conn.execute(
            "SELECT COUNT(*) FROM login_log WHERE username = ? AND success = 1 "
            "AND created_at >= datetime('now', '-30 days')", (u["username"],)).fetchone()[0]
        ch = conn.execute(
            "SELECT COUNT(*), COALESCE(SUM(delta_jpy), 0), MAX(created_at) FROM balance_ledger "
            "WHERE user_id = ? AND delta_jpy > 0", (u["id"],)).fetchone()
        recent = conn.execute(
            "SELECT created_at, delta_jpy, reason FROM balance_ledger "
            "WHERE user_id = ? AND delta_jpy > 0 ORDER BY id DESC LIMIT 3", (u["id"],)).fetchall()
        tokens = conn.execute(
            "SELECT created_at, expires_at, used_at, revoked_at FROM password_reset_tokens "
            "WHERE user_id = ? ORDER BY id DESC LIMIT 3", (u["id"],)).fetchall()
        blocker = issue_blocker(conn, {"id": u["id"], "role": u["role"], "is_active": u["is_active"]})
        out.append({
            "id": u["id"], "username": u["username"], "email": u["email"],
            "display_name": u["display_name"], "role": u["role"], "is_active": bool(u["is_active"]),
            "created_at": u["created_at"], "last_login": last[0] if last else None,
            "logins_30d": n30, "balance_jpy": u["balance_jpy"],
            "charges": {"count": ch[0], "sum_jpy": ch[1], "last": ch[2],
                        "recent": [dict(x) for x in recent]},
            "disposable_email": auth.is_disposable_email_domain(u["username"] if "@" in (u["username"] or "") else (u["email"] or "")),
            "requests": _requests_for(conn, u),
            "reply_differs_count": reply_differs_count(conn, u),
            "reset_links": [dict(t) for t in tokens],
            "can_issue": blocker is None, "blocker": blocker,
        })
    return out
