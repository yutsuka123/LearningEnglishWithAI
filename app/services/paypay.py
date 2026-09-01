"""PayPay for Developers（Open Payment API）クライアント（2026-08-26新設）。

サービス種別は「ウェブペイメント」(=技術ドキュメント上のWeb Cashierフロー)。
公式Python SDK(`paypayopa`)はpkg_resources(setuptools<81が必要)に依存して
おり、現行のPython/setuptoolsでは`import`時点で壊れるため採用しなかった
（2026-08-26確認・setuptools 84でImportError、`setuptools<81`まで下げれば
動くが非推奨警告付きの不安定な依存になる）。認証方式(HMAC署名)自体は
単純なので、公式SDKのソース(`client.py`のauth_header/_update_request)を
参照元にhttpxで直接実装した。

エンドポイント(2026-08-26、公式SDK v1.0.9のソース・
developer.paypay.ne.jp Open Payment API文書で確認済み):
  - Create a Code:        POST   /v2/codes
  - Get Payment Details:  GET    /v2/codes/payments/{merchantPaymentId}
  - Delete a Code:        DELETE /v2/codes/{codeId}          (支払い前のみ)
  - Refund:                POST   /v2/refunds                 (支払い後)

支払い完了の判定は必ずGet Payment DetailsのAPIレスポンス
(`data.status == "COMPLETED"`)で行うこと。redirect復帰それ自体を
成功の根拠にしない(公式ドキュメントが明記)。
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import uuid

import httpx

from ..config import log

# Open Payment API(決済系)のベースURL(公式SDK `constants/url.py`で確認済み)。
_SANDBOX_APIGW = "https://apigw.sandbox.paypay.ne.jp"
_PRODUCTION_APIGW = "https://apigw.paypay.ne.jp"


class PayPayError(Exception):
    """PayPay API呼び出し時のエラー(管理画面にそのままメッセージ表示する)。"""


def is_production() -> bool:
    """本番(実売上)モードかどうか。加盟店審査が完了するまでは常にFalse
    (=サンドボックス)。2026-09-01〜: app/routers/paypay_charge.pyが一般
    ユーザー向けのpt購入を、審査完了までadmin限定に制限する判定にも使う
    (サンドボックスのままだと実際の支払いなしにptだけ付与されてしまう
    ため)。"""
    return os.getenv("PAYPAY_PRODUCTION_MODE", "").strip().lower() in (
        "1", "true", "yes")


def _base_url() -> str:
    return _PRODUCTION_APIGW if is_production() else _SANDBOX_APIGW


def _credentials() -> tuple[str, str, str]:
    api_key = os.getenv("PAYPAY_API_KEY", "").strip()
    api_secret = os.getenv("PAYPAY_API_SECRET", "").strip()
    merchant_id = os.getenv("PAYPAY_MERCHANT_ID", "").strip()
    if not api_key or not api_secret or not merchant_id:
        raise PayPayError(
            "PAYPAY_API_KEY/PAYPAY_API_SECRET/PAYPAY_MERCHANT_IDが"
            ".envに未設定です。")
    return api_key, api_secret, merchant_id


def _auth_header(
    api_key: str, api_secret: str, method: str, path: str,
    body_json: str | None,
) -> str:
    """公式SDK(client.py auth_header)と同一アルゴリズムのHMAC署名。"""
    content_type = "empty" if body_json is None else (
        "application/json;charset=UTF-8")
    nonce = str(uuid.uuid4())[:8]
    timestamp = str(int(time.time()))
    body_hash = "empty"
    if body_json is not None:
        hashed = hashlib.md5()
        hashed.update(content_type.encode("utf-8"))
        hashed.update(body_json.encode("utf-8"))
        body_hash = base64.b64encode(hashed.digest()).decode()
    signature_src = "\n".join(
        [path, method, nonce, timestamp, content_type, body_hash])
    digest = hmac.new(
        api_secret.encode("utf-8"), signature_src.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()
    hmac_b64 = base64.b64encode(digest).decode()
    header = ":".join([api_key, hmac_b64, nonce, timestamp, body_hash])
    return f"hmac OPA-Auth:{header}"


def _request(method: str, path: str, *, body: dict | None = None) -> dict:
    api_key, api_secret, merchant_id = _credentials()
    body_json = json.dumps(body) if body is not None else None
    auth = _auth_header(api_key, api_secret, method, path, body_json)
    headers = {
        "Authorization": auth,
        "Content-Type": "application/json;charset=UTF-8",
        "X-ASSUME-MERCHANT": merchant_id,
    }
    url = f"{_base_url()}{path}"
    # 決済失敗は許されないため、成功/失敗いずれも監査用に必ずログする
    # (2026-08-26ユーザー指示)。Authorizationヘッダ・API secret等の
    # 秘密情報は絶対にログに出さない(bodyはmerchantPaymentId/amount等の
    # 非秘匿情報のみを含む想定)。
    log.info("paypay: request method=%s path=%s production=%s body=%s",
             method, path, is_production(), body_json)
    try:
        resp = httpx.request(
            method, url, headers=headers,
            content=body_json, timeout=30.0)
    except httpx.TimeoutException as e:
        log.warning("paypay: request TIMEOUT method=%s path=%s: %s",
                    method, path, e)
        raise PayPayError(
            "PayPayへの接続がタイムアウトしました(30秒)。時間をおいて"
            "再試行してください。決済自体は処理されている場合があるため、"
            "残高/注文状況を確認してから再送してください。") from e
    except httpx.HTTPError as e:
        log.warning("paypay: request failed method=%s path=%s: %s",
                    method, path, e)
        raise PayPayError("PayPayへの接続に失敗しました。") from e
    try:
        data = resp.json()
    except Exception:
        log.warning("paypay: non-JSON response method=%s path=%s status=%s "
                    "body=%s", method, path, resp.status_code,
                    resp.text[:500])
        raise PayPayError(f"PayPayから不正な応答(status={resp.status_code})。")
    if resp.status_code >= 300:
        info = data.get("resultInfo", {})
        log.warning(
            "paypay: ERROR method=%s path=%s status=%s code=%s message=%s "
            "raw=%s", method, path, resp.status_code, info.get("code"),
            info.get("message"), data)
        raise PayPayError(
            f"PayPay APIエラー: {info.get('code', '?')} "
            f"{info.get('message', '')}".strip())
    resp_data = data.get("data") or {}
    log.info(
        "paypay: OK method=%s path=%s status=%s data.status=%s "
        "data.codeId=%s data.paymentId=%s",
        method, path, resp.status_code, resp_data.get("status"),
        resp_data.get("codeId"), resp_data.get("paymentId"))
    return data


def create_code(
    merchant_payment_id: str, amount_jpy: int, *,
    redirect_url: str, order_description: str = "",
) -> dict:
    """Create a Code(POST /v2/codes)。本実装のサービス種別「ウェブ
    ペイメント」に対応するWeb Cashierドキュメント
    (https://www.paypay.ne.jp/opa/doc/jp/v1.0/webcashier)によれば
    `redirectType`は任意パラメータとして存在し、リダイレクト先が
    ウェブページの場合は"WEB_LINK"を指定する(2026-08-27訂正: 直前に
    店頭QR掲示用のDynamic QR Codeドキュメントを見て「存在しない」と
    誤って削除していた・Fableレビューで指摘)。data.deeplink/data.url
    はいずれもアプリインストール済みなら支払い画面を直接起動する仕様
    (公式Q&A参照)。"""
    body = {
        "merchantPaymentId": merchant_payment_id,
        "amount": {"amount": int(amount_jpy), "currency": "JPY"},
        "codeType": "ORDER_QR",
        "redirectUrl": redirect_url,
        "redirectType": "WEB_LINK",
        "requestedAt": int(time.time()),
    }
    if order_description:
        body["orderDescription"] = order_description[:255]
    return _request("POST", "/v2/codes", body=body)


def get_payment_details(merchant_payment_id: str) -> dict:
    """Get Payment Details(GET /v2/codes/payments/{merchantPaymentId})。
    data.status を必ずここで確認する(redirect復帰だけでは支払い完了と
    見なさない)。"""
    return _request(
        "GET", f"/v2/codes/payments/{merchant_payment_id}")


def delete_code(code_id: str) -> dict:
    """Delete a Code(DELETE /v2/codes/{codeId})。支払い前のみキャンセル可。"""
    return _request("DELETE", f"/v2/codes/{code_id}")


def refund(
    merchant_refund_id: str, payment_id: str, amount_jpy: int, *,
    reason: str = "",
) -> dict:
    """Refund(POST /v2/refunds)。支払い済みの取消はこちら
    (未払いキャンセルは delete_code を使う)。"""
    body = {
        "merchantRefundId": merchant_refund_id,
        "paymentId": payment_id,
        "amount": {"amount": int(amount_jpy), "currency": "JPY"},
        "requestedAt": int(time.time()),
    }
    if reason:
        body["reason"] = reason[:200]
    return _request("POST", "/v2/refunds", body=body)


def credit_if_completed(
    conn, payment_row, status: str, payment_id: str,
) -> bool:
    """`paypay_payments`の1行(sqlite3.Row)に対し、statusがCOMPLETEDで
    かつ未付与の場合に限り、原子的にpt付与する。付与できたかどうかを
    返す。`app/routers/paypay_charge.py`の`/confirm`と
    `scripts/reconcile_paypay_payments.py`の両方から呼ばれる共通ロジック
    (2026-09-01・実装を2箇所に分けると挙動がずれる恐れがあるため一本化)。

    二重防止の仕組み: `credited_at IS NULL`の行だけを対象にUPDATEし、
    実際に更新できた行数(rowcount)が1のときだけpt付与する
    (`app/services/charge_keys.py`の`redeem_key`と同じ「使用済みで
    なければ使用済みにする」という原子的な自己防衛パターン)。同時に
    2回呼ばれても、片方だけが更新に成功しpt付与も1回だけになる。"""
    from . import auth  # 循環import回避のため関数内でimport

    mpid = payment_row["merchant_payment_id"]
    already_credited = payment_row["credited_at"] is not None
    conn.execute(
        "UPDATE paypay_payments SET status = ?, payment_id = ?, "
        "updated_at = datetime('now') WHERE merchant_payment_id = ?",
        (status, payment_id, mpid),
    )
    if status != "COMPLETED" or already_credited:
        return False
    cur = conn.execute(
        "UPDATE paypay_payments SET credited_at = datetime('now') "
        "WHERE merchant_payment_id = ? AND credited_at IS NULL",
        (mpid,),
    )
    if cur.rowcount != 1:
        return False
    mode = "production" if is_production() else "sandbox"
    auth.add_balance(
        conn, payment_row["user_id"], float(payment_row["amount_jpy"]),
        reason="paypay_charge", note=f"mpid={mpid} mode={mode}")
    return True
