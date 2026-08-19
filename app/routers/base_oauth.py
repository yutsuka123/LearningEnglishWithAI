"""BASE API連携のOAuth認可（2026-08-18・注文自動検知の土台）。

管理者専用。BASE Developers(developers.thebase.com)でアプリ登録し、
.envにBASE_CLIENT_ID/BASE_CLIENT_SECRETを設定してから使う。

フロー: ①/start で管理者がBASEの認可画面へ飛ぶ → ②承認後 /callback に
authorization codeが飛んでくる → ③トークンに交換しbase_api_tokensへ保存。

注意: BASE API v1はβ版ドキュメントのため、トークン応答の正確な
フィールド名・scopeの区切り文字が未検証（2026-08-18時点で公式ドキュメント
から確認できたのはエンドポイントパスとレート制限のみ）。実際に認可を
通した際にエラーになった場合は、まずapp.logの`base_oauth:`ログで
実際のレスポンス内容を確認すること。
"""

from __future__ import annotations

import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse

from ..config import log
from ..database import db
from ..services.auth import current_user_id, get_user

router = APIRouter(prefix="/admin/base-oauth", tags=["base-oauth"])

AUTHORIZE_URL = "https://api.thebase.in/1/oauth/authorize"
TOKEN_URL = "https://api.thebase.in/1/oauth/token"
REDIRECT_URI = "https://study.nyangailab.com/admin/base-oauth/callback"
DEFAULT_SCOPE = "read_orders read_users"

# CSRF対策のstateをプロセス内メモリで一時保持（単一管理者・低頻度操作の
# 前提。数分で失効するのでDB化までは不要）。
_pending_states: dict[str, float] = {}
_STATE_TTL = 600.0


def _require_admin(conn) -> dict:
    me = get_user(conn, current_user_id())
    if not me or me.get("role") != "admin":
        raise HTTPException(403, "管理者のみ操作できます。")
    return me


def _cleanup_states() -> None:
    now = time.monotonic()
    for k in [k for k, t in _pending_states.items() if now - t > _STATE_TTL]:
        _pending_states.pop(k, None)


@router.get("/status")
def status():
    """連携状態(接続済みか・トークン有効期限)を返す（管理画面表示用）。"""
    with db() as conn:
        _require_admin(conn)
        row = conn.execute(
            "SELECT expires_at, scope, updated_at FROM base_api_tokens "
            "WHERE id = 1"
        ).fetchone()
    client_configured = bool(
        os.getenv("BASE_CLIENT_ID", "").strip()
        and os.getenv("BASE_CLIENT_SECRET", "").strip()
    )
    if not row:
        return {"ok": True, "connected": False,
                "client_configured": client_configured}
    return {
        "ok": True, "connected": True,
        "client_configured": client_configured,
        "expires_at": row["expires_at"], "scope": row["scope"],
        "updated_at": row["updated_at"],
    }


@router.get("/start")
def start():
    with db() as conn:
        _require_admin(conn)
    client_id = os.getenv("BASE_CLIENT_ID", "").strip()
    if not client_id:
        raise HTTPException(
            400, "BASE_CLIENT_IDが.envに未設定です。先に設定してください。")
    _cleanup_states()
    state = secrets.token_urlsafe(24)
    _pending_states[state] = time.monotonic()
    scope = os.getenv("BASE_OAUTH_SCOPE", DEFAULT_SCOPE).strip()
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": REDIRECT_URI,
        "scope": scope,
        "state": state,
    }
    return RedirectResponse(f"{AUTHORIZE_URL}?{urlencode(params)}")


@router.get("/callback")
def callback(code: str = "", state: str = "", error: str = ""):
    with db() as conn:
        me = _require_admin(conn)
    if error:
        log.warning("base_oauth: authorize error=%s", error)
        raise HTTPException(400, f"BASE側で認可が拒否/失敗しました: {error}")
    if not code or not state:
        raise HTTPException(400, "code/stateが不足しています。")
    _cleanup_states()
    issued_at = _pending_states.pop(state, None)
    if issued_at is None:
        raise HTTPException(
            400, "無効または期限切れのstateです。もう一度"
            "「BASEと連携する」からやり直してください。")

    client_id = os.getenv("BASE_CLIENT_ID", "").strip()
    client_secret = os.getenv("BASE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise HTTPException(400, "BASE_CLIENT_ID/SECRETが.envに未設定です。")

    try:
        resp = httpx.post(TOKEN_URL, data={
            "grant_type": "authorization_code",
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": REDIRECT_URI,
        }, timeout=15.0)
    except httpx.HTTPError as e:
        log.warning("base_oauth: token exchange request failed: %s", e)
        raise HTTPException(502, "BASEへの接続に失敗しました。")

    if resp.status_code != 200:
        log.warning("base_oauth: token exchange failed status=%s body=%s",
                    resp.status_code, resp.text[:500])
        raise HTTPException(
            502, f"BASEとのトークン交換に失敗しました(status={resp.status_code})。"
            "app.logに詳細を記録したので確認してください。")

    data = resp.json()
    access_token = data.get("access_token", "")
    refresh_token = data.get("refresh_token", "")
    expires_in = data.get("expires_in", 3600)
    scope = data.get("scope", "")
    if not access_token or not refresh_token:
        log.warning("base_oauth: unexpected token response keys=%s",
                    list(data.keys()))
        raise HTTPException(
            502, "BASEのトークン応答にaccess_token/refresh_tokenが"
            "含まれていません。app.logで実際のレスポンス内容を確認してください。")

    try:
        expires_in = int(expires_in)
    except (TypeError, ValueError):
        expires_in = 3600
    expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    ).isoformat()

    with db() as conn:
        conn.execute(
            "INSERT INTO base_api_tokens "
            "(id, access_token, refresh_token, expires_at, scope, updated_at) "
            "VALUES (1, ?, ?, ?, ?, datetime('now')) "
            "ON CONFLICT(id) DO UPDATE SET "
            "access_token=excluded.access_token, "
            "refresh_token=excluded.refresh_token, "
            "expires_at=excluded.expires_at, scope=excluded.scope, "
            "updated_at=excluded.updated_at",
            (access_token, refresh_token, expires_at, scope),
        )
    log.info("base_oauth: connected by admin_uid=%s scope=%s expires_at=%s",
              me["id"], scope, expires_at)
    return RedirectResponse("/admin/fulfillment?base_connected=1")
