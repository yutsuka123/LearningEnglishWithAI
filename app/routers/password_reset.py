"""パスワード再発行(2026-10-04・ver1.5.12・仕組みは`app/services/password_reset.py`参照)。

利用者の流れ: ログイン画面の「パスワードを忘れた方」→ 依頼(`POST /api/auth/password-help`・お問い合わせとして保存)→
管理者が管理画面で本人確認 → 使い捨ての再設定リンクを発行して本人へ渡す →
本人が`/reset-password`で新しいパスワードを設定(`POST /api/auth/password-reset`)。

- 依頼の応答は、登録の有無によらず常に同じ(登録メールアドレスの存在を外部に漏らさない)。
- 公開エンドポイントはIPごとに回数を制限する(プロセス内メモリ・再起動でリセット)。
- 管理者用エンドポイントは全て管理者(role=admin)専用(サーバー側で強制)。
"""

from __future__ import annotations

import os
import time

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from ..config import log
from ..database import db
from ..services import auth, errors, messages, password_reset

router = APIRouter(prefix="/api/auth", tags=["password-reset"])

# ---- 回数制限(プロセス内メモリ) -------------------------------------------------
_HITS: dict[str, list[float]] = {}


def _rate_limited(key: str, limit: int, window: float) -> bool:
    """直近`window`秒に`limit`回に達していれば真(真のときは数えない)。偽のときは1回数える。"""
    now = time.monotonic()
    hits = [t for t in _HITS.get(key, []) if now - t < window]
    if len(hits) >= limit:
        _HITS[key] = hits
        return True
    hits.append(now)
    _HITS[key] = hits
    if len(_HITS) > 5000:           # 古いキーを掃除(メモリの肥大防止)
        for k in [k for k, v in _HITS.items() if not v or now - v[-1] > 3600]:
            _HITS.pop(k, None)
    return False


def _require_admin(conn) -> int:
    me = auth.get_user(conn, auth.current_user_id())
    if not me or me.get("role") != "admin":
        raise errors.http_error("2004", "管理者のみ利用できます。")
    return int(me["id"])


def _email_ok(email: str) -> bool:
    return bool(email) and len(email) <= 254 and "@" in email and "." in email.split("@")[-1]


# ---- 利用者: 再発行の依頼 -----------------------------------------------------------
class PasswordHelpIn(BaseModel):
    email: str = Field(default="", max_length=300)          # 登録したメールアドレス(必須)
    nickname: str = Field(default="", max_length=100)       # 登録時の呼んでほしいお名前(任意)
    contact: str = Field(default="", max_length=300)        # 返信先(任意・空なら登録メール)
    note: str = Field(default="", max_length=1500)          # 登録時期・チャージの有無など本人確認の手がかり(任意)


@router.post("/password-help")
def password_help(payload: PasswordHelpIn, request: Request):
    ip = auth.real_client_ip(request)
    if _rate_limited(f"help-ip|{ip}", 5, 3600.0):
        return errors.error_response("2002")
    email = payload.email.strip().lower()
    if not _email_ok(email):
        return errors.error_response("2010")
    contact = payload.contact.strip().lower()
    reply = contact if _email_ok(contact) else email
    nickname = " ".join(payload.nickname.split())[:100]
    note = payload.note.strip()[:1500]
    # 同じ登録メールでの依頼が続いたら(10分以内に1件・24時間に3件まで)、保存せず同じ応答を返す(連打・荒らしの抑止)。
    if _rate_limited(f"help-email-fast|{email}", 1, 600.0) or _rate_limited(f"help-email-day|{email}", 3, 86400.0):
        return {"ok": True}
    content = (
        "【パスワード再発行の依頼】\n"
        f"登録したメールアドレス: {email}\n"
        f"ニックネーム: {nickname or '(未記入)'}\n"
        f"連絡先(返信先): {reply}\n"
        f"補足(登録時期・チャージの有無など): {note or '(未記入)'}")
    with db() as conn:
        conn.execute(
            "INSERT INTO inquiries (user_id, kind, name, email, content) VALUES (?, ?, ?, ?, ?)",
            # user_idは空にする: 認証不要のパスでは`current_user_id()`が運営者(id=1)になる仕様のため、使わない
            (None, "パスワード再発行", nickname, reply, content))
    log.info("password-help: request stored ip=%s", ip)   # メールアドレス・本文はログに出さない
    return {"ok": True}


# ---- 利用者: 再設定リンクの確認と新パスワードの設定 ------------------------------------------
class TokenIn(BaseModel):
    token: str = Field(default="", max_length=300)


class ResetIn(BaseModel):
    token: str = Field(default="", max_length=300)
    new_password: str = Field(default="", max_length=200)


@router.post("/password-reset/check")
def password_reset_check(payload: TokenIn, request: Request):
    """リンクがいま使えるか(新パスワードを入力する前に、無効なリンクだと分かるように)。"""
    if _rate_limited(f"reset-check|{auth.real_client_ip(request)}", 30, 600.0):
        return errors.error_response("2002")
    with db() as conn:
        return {"valid": password_reset.is_valid(conn, payload.token)}


@router.post("/password-reset")
def password_reset_apply(payload: ResetIn, request: Request):
    ip = auth.real_client_ip(request)
    if _rate_limited(f"reset-apply|{ip}", 20, 600.0):
        return errors.error_response("2002")
    with db() as conn:
        result, detail = password_reset.consume(conn, payload.token, payload.new_password)
    if result == "invalid":
        log.warning("password-reset: invalid or expired link ip=%s", ip)
        return errors.error_response("2017")
    if result == "policy":
        return errors.error_response("2012", messages.tr(detail))
    auth.clear_all_login_failures_for_username(detail)
    return {"ok": True}      # 自動ログインはしない(新しいパスワードでログインし直してもらう)


# ---- 管理者: 本人確認の手がかりの表示・リンクの発行/取り消し ------------------------------------
@router.get("/admin/password-reset/lookup")
def admin_lookup(q: str = ""):
    with db() as conn:
        _require_admin(conn)
        return {"users": password_reset.lookup(conn, q)}


class IssueIn(BaseModel):
    user_id: int
    hours: int = password_reset.DEFAULT_HOURS
    note: str = Field(default="", max_length=200)      # 何を根拠に本人と判断したか(監査用の控え)


@router.post("/admin/password-reset/link")
def admin_issue(payload: IssueIn, request: Request):
    with db() as conn:
        admin_id = _require_admin(conn)
        target = auth.get_user(conn, payload.user_id)
        if not target:
            raise errors.http_error("7001", "ユーザーが見つかりません。")
        blocker = password_reset.issue_blocker(conn, target)
        if blocker:
            raise errors.http_error("2018", blocker)
        token, expires = password_reset.create_link(
            conn, admin_id, payload.user_id, payload.hours, payload.note)
    path = f"/reset-password#t={token}"
    base = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if not base:
        host = request.headers.get("host", "")
        base = f"{auth.external_scheme(request)}://{host}" if host else ""
    return {"ok": True, "path": path, "url": base + path, "expires_at": expires,
            "hours": payload.hours if payload.hours in password_reset.ALLOWED_HOURS else password_reset.DEFAULT_HOURS}


class RevokeIn(BaseModel):
    user_id: int


@router.post("/admin/password-reset/revoke")
def admin_revoke(payload: RevokeIn):
    with db() as conn:
        _require_admin(conn)
        n = password_reset.revoke_all(conn, payload.user_id)
    return {"ok": True, "revoked": n}
