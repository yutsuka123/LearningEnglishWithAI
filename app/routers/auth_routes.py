"""ログイン/ログアウト/現在ユーザー（§A マルチユーザー化）。

MULTIUSER=1 のときに使う。ローカル単一ユーザー（既定）では認証は不要で、
常に owner として動くため、これらのエンドポイントは使われない（/me は owner を
返す）。セッションは stdlib hmac の署名Cookie（app/services/auth.py）。
"""

from __future__ import annotations

import os
import time

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..database import db
from ..services import auth

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _cookie_secure(request: Request) -> bool:
    """本番HTTPSでは Secure Cookie を必須にする。COOKIE_SECURE=1 で強制、
    auto（既定）はリバプロの X-Forwarded-Proto / scheme が https かで判定。"""
    mode = os.getenv("COOKIE_SECURE", "auto").strip().lower()
    if mode in ("1", "true", "yes"):
        return True
    if mode in ("0", "false", "no"):
        return False
    xfp = request.headers.get("x-forwarded-proto", "").split(",")[0].strip()
    return request.url.scheme == "https" or xfp == "https"


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(payload: LoginIn, request: Request, response: Response):
    ip = request.client.host if request.client else "?"
    locked = auth.login_locked(payload.username, ip)
    if locked:
        return JSONResponse(
            {"ok": False, "error": "試行が多すぎます。しばらく待って"
             "から再試行してください。"}, status_code=429)
    with db() as conn:
        u = auth.authenticate(conn, payload.username, payload.password)
        if not u:
            auth.record_login_failure(payload.username, ip)
            return JSONResponse(
                {"ok": False, "error": "ユーザー名かパスワードが違います。"},
                status_code=401,
            )
        secret = auth.get_session_secret(conn)
    auth.clear_login_failures(payload.username, ip)
    token = auth.make_session_token(secret, u["id"], int(time.time()))
    resp = JSONResponse({"ok": True, "user": {
        "id": u["id"], "username": u["username"], "role": u["role"],
        "display_name": u["display_name"],
    }})
    # HttpOnly + SameSite=Lax + (本番HTTPSは)Secure。
    resp.set_cookie(
        auth.SESSION_COOKIE, token, max_age=auth._SESSION_TTL,
        httponly=True, samesite="lax", path="/",
        secure=_cookie_secure(request),
    )
    return resp


@router.post("/logout")
def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(auth.SESSION_COOKIE, path="/")
    return resp


@router.get("/me")
def me():
    """現在ログイン中のユーザー情報（残高・上限を含む）。未ログインは 401。"""
    uid = auth.current_user_id()
    with db() as conn:
        u = auth.get_user(conn, uid)
    if not u:
        return JSONResponse({"ok": False, "error": "未ログイン"},
                            status_code=401)
    return {"ok": True, "user": {
        "id": u["id"], "username": u["username"], "role": u["role"],
        "display_name": u["display_name"],
        "daily_cost_cap_usd": u["daily_cost_cap_usd"],
        "monthly_cost_cap_usd": u["monthly_cost_cap_usd"],
        "balance_jpy": u["balance_jpy"],
        "multiuser": auth.multiuser_enabled(),
    }}
