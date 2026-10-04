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
from . import auth

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


def consume(conn: sqlite3.Connection, token: str, new_password: str) -> tuple[str, str]:
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
        "UPDATE password_reset_tokens SET used_at = datetime('now') "
        "WHERE id = ? AND used_at IS NULL AND revoked_at IS NULL "
        "AND expires_at > datetime('now')", (row["id"],))
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
        (q, q, "%" + _like_escape(q) + "%", int(q) if q.isdigit() else -1, LOOKUP_LIMIT)).fetchall()
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
        tokens = conn.execute(
            "SELECT created_at, expires_at, used_at, revoked_at FROM password_reset_tokens "
            "WHERE user_id = ? ORDER BY id DESC LIMIT 3", (u["id"],)).fetchall()
        blocker = issue_blocker(conn, {"id": u["id"], "role": u["role"], "is_active": u["is_active"]})
        out.append({
            "id": u["id"], "username": u["username"], "email": u["email"],
            "display_name": u["display_name"], "role": u["role"], "is_active": bool(u["is_active"]),
            "created_at": u["created_at"], "last_login": last[0] if last else None,
            "logins_30d": n30, "balance_jpy": u["balance_jpy"],
            "charges": {"count": ch[0], "sum_jpy": ch[1], "last": ch[2]},
            "reset_links": [dict(t) for t in tokens],
            "can_issue": blocker is None, "blocker": blocker,
        })
    return out
