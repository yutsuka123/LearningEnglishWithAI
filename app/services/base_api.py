"""BASE APIクライアント（注文自動検知・Phase B・2026-08-19）。

app/routers/base_oauth.pyでOAuth連携済み(base_api_tokensにトークンあり)
であることが前提。アクセストークンは1時間で失効するため、必要なら
リフレッシュトークンで自動更新してから使う。リフレッシュトークンも
使用のたび新しい値に入れ替わる(ローテーションする)ため、都度DBへ
保存し直す(参照: docs.thebase.in/api/oauth/refresh_token/)。

注意: BASE API v1はβ版ドキュメントのため、実際のレスポンス構造が
ドキュメントと食い違う可能性がある(base_oauth.pyの注意書きと同じ)。
エラー時はapp.logの`base_api:`ログで実際のレスポンス内容を確認すること。
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import httpx

from ..config import log

API_BASE = "https://api.thebase.in/1"
TOKEN_URL = f"{API_BASE}/oauth/token"
# base_oauth.pyのREDIRECT_URIと同じ値(トークン更新時も一致させる必要がある)。
REDIRECT_URI = "https://study.nyangailab.com/admin/base-oauth/callback"


class BaseApiError(Exception):
    """BASE API呼び出し時のエラー（管理画面にそのままメッセージ表示する）。"""


def _save_token(conn, access_token: str, refresh_token: str, expires_in) -> str:
    try:
        expires_in = int(expires_in)
    except (TypeError, ValueError):
        expires_in = 3600
    expires_at = (
        datetime.now(timezone.utc) + timedelta(seconds=expires_in)
    ).isoformat()
    conn.execute(
        "UPDATE base_api_tokens SET access_token = ?, refresh_token = ?, "
        "expires_at = ?, updated_at = datetime('now') WHERE id = 1",
        (access_token, refresh_token, expires_at),
    )
    return expires_at


def _refresh_access_token(conn, refresh_token: str) -> str:
    client_id = os.getenv("BASE_CLIENT_ID", "").strip()
    client_secret = os.getenv("BASE_CLIENT_SECRET", "").strip()
    if not client_id or not client_secret:
        raise BaseApiError("BASE_CLIENT_ID/SECRETが.envに未設定です。")
    try:
        resp = httpx.post(TOKEN_URL, data={
            "grant_type": "refresh_token",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "redirect_uri": REDIRECT_URI,
        }, timeout=15.0)
    except httpx.HTTPError as e:
        log.warning("base_api: refresh request failed: %s", e)
        raise BaseApiError("BASEへの接続に失敗しました(トークン更新)。")
    if resp.status_code != 200:
        log.warning("base_api: refresh failed status=%s body=%s",
                    resp.status_code, resp.text[:500])
        raise BaseApiError(
            f"トークン更新に失敗しました(status={resp.status_code})。"
            "リフレッシュトークンが失効している場合、管理画面から"
            "「BASEと連携する」を再実行してください。")
    data = resp.json()
    access_token = data.get("access_token", "")
    new_refresh = data.get("refresh_token", "")
    expires_in = data.get("expires_in", 3600)
    if not access_token or not new_refresh:
        log.warning("base_api: unexpected refresh response keys=%s",
                    list(data.keys()))
        raise BaseApiError("トークン更新の応答にaccess_token/refresh_token"
                            "が含まれていません。")
    _save_token(conn, access_token, new_refresh, expires_in)
    log.info("base_api: access token refreshed (expires_in=%s)", expires_in)
    return access_token


def get_valid_access_token(conn) -> str:
    """有効なアクセストークンを返す。期限切れ間近ならリフレッシュする。
    未連携ならBaseApiErrorを送出する。"""
    row = conn.execute(
        "SELECT access_token, refresh_token, expires_at "
        "FROM base_api_tokens WHERE id = 1"
    ).fetchone()
    if not row:
        raise BaseApiError(
            "BASEと連携されていません。管理画面(フルフィルメント管理)から"
            "「BASEと連携する」を実行してください。")
    try:
        expires_at = datetime.fromisoformat(row["expires_at"])
    except ValueError:
        expires_at = datetime.now(timezone.utc)
    # 実行中に切れるのを防ぐため、5分の余裕を持たせて判定する。
    if expires_at <= datetime.now(timezone.utc) + timedelta(minutes=5):
        return _refresh_access_token(conn, row["refresh_token"])
    return row["access_token"]


def list_orders(
    access_token: str, start_ordered: str, end_ordered: str,
) -> list[dict]:
    """指定期間(yyyy-mm-dd)の注文一覧を全ページ取得する。"""
    orders: list[dict] = []
    offset = 0
    limit = 100
    headers = {"Authorization": f"Bearer {access_token}"}
    while True:
        try:
            resp = httpx.get(f"{API_BASE}/orders", headers=headers, params={
                "start_ordered": start_ordered, "end_ordered": end_ordered,
                "limit": limit, "offset": offset,
            }, timeout=20.0)
        except httpx.HTTPError as e:
            log.warning("base_api: orders list request failed: %s", e)
            raise BaseApiError("BASEへの接続に失敗しました(注文一覧取得)。")
        if resp.status_code != 200:
            log.warning("base_api: orders list failed status=%s body=%s",
                        resp.status_code, resp.text[:500])
            raise BaseApiError(
                f"注文一覧の取得に失敗しました(status={resp.status_code})。")
        data = resp.json()
        page = data.get("orders", [])
        orders.extend(page)
        if len(page) < limit:
            break
        offset += limit
        if offset > 5000:  # 暴走防止の安全上限（実運用では届かない想定）。
            break
    return orders


def get_order_detail(access_token: str, unique_key: str) -> dict:
    """注文の詳細（購入者メールアドレス等）を取得する。"""
    headers = {"Authorization": f"Bearer {access_token}"}
    try:
        resp = httpx.get(f"{API_BASE}/orders/detail/{unique_key}",
                          headers=headers, timeout=20.0)
    except httpx.HTTPError as e:
        log.warning("base_api: order detail request failed: %s", e)
        raise BaseApiError("BASEへの接続に失敗しました(注文詳細取得)。")
    if resp.status_code != 200:
        log.warning("base_api: order detail failed status=%s body=%s",
                    resp.status_code, resp.text[:500])
        raise BaseApiError(
            f"注文詳細の取得に失敗しました(status={resp.status_code})。")
    data = resp.json()
    # β版ドキュメントにつき"order"キーで包まれる可能性/直下の可能性の
    # 両対応（2026-08-19時点で実レスポンスを検証できていないため防御的に）。
    return data.get("order", data) if isinstance(data, dict) else {}
