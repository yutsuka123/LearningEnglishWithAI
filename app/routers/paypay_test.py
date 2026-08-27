"""PayPay決済テスト用API（管理者専用・2026-08-26新設）。

サンドボックス環境での結合テストが目的（実際の課金導線への組み込みは
別タスク）。ユーザー指示: 「支払い完了、キャンセルなどのステータスが
表示され、単にpaypayとの結合テストをする。これができれば本番デプロイ・
本番環境でも支払い大丈夫だとわかるところまでとする」。
¥800/¥8000の2ボタンのみ(BASEショップの既存価格帯に合わせた)。

フロー: ①作成(create) → data.url へブラウザをリダイレクト →
②ユーザーがPayPayで支払う → ③redirectUrl(このルーターの/return)に戻る →
④Get Payment Detailsで data.status を確認して表示(COMPLETED等)。
redirect復帰そのものは成功の証拠にしない(app/services/paypay.py参照)。

ログ方針(2026-08-26ユーザー指示「決済での失敗はゆるされない」):
create/details/cancel/refundの全操作を、実行した管理者(username/id)・
merchantPaymentId・codeId・paymentId・金額・結果ステータスとともに
app.logへ記録する(成功はlog.info、失敗はlog.warning)。API secret等の
秘密情報は`app/services/paypay.py`側でも一切ログに出さない設計。
現状はapp.log(テキストログ)のみで、DBテーブル化(base_order_actionsと
同様の構造化監査ログ)は本番決済導線に組み込む際の課題として
docs/TODO.mdに記録済み(このテストページの段階では見送り)。
"""

from __future__ import annotations

import urllib.parse
import uuid

from fastapi import APIRouter, Path, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

from ..config import log
from ..services import errors, paypay
from ..database import db
from ..services import auth
from ..services.auth import current_user_id, get_user

router = APIRouter(prefix="/api/paypay-test", tags=["paypay-test"])

# 動作確認用の固定金額(BASEショップの既存2プランに合わせる)。
ALLOWED_AMOUNTS = {800, 8000}

# merchantPaymentId/codeId用の形式検証(パス注入対策・Fableレビュー指摘
# 2026-08-27)。PayPay発行のcodeIdは"04-英数字"形式、こちらが生成する
# merchantPaymentIdは"test-<uuid4>"形式で、いずれも英数字・アンダー
# スコア・ハイフンのみで表現できる。
_ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"


def _require_admin(conn) -> dict:
    me = get_user(conn, current_user_id())
    if not me or me.get("role") != "admin":
        raise errors.http_error("2004", "管理者のみ操作できます。")
    return me


@router.get("/status")
def config_status():
    """PayPay設定(.env)が揃っているか（管理画面のボタン活性化用）。"""
    with db() as conn:
        _require_admin(conn)
    import os
    configured = bool(
        os.getenv("PAYPAY_API_KEY", "").strip()
        and os.getenv("PAYPAY_API_SECRET", "").strip()
        and os.getenv("PAYPAY_MERCHANT_ID", "").strip()
    )
    return {"ok": True, "configured": configured}


class CreateIn(BaseModel):
    amount_jpy: int


@router.post("/create")
def create(payload: CreateIn, request: Request):
    if payload.amount_jpy not in ALLOWED_AMOUNTS:
        raise errors.http_error(
            "3019", f"金額は{sorted(ALLOWED_AMOUNTS)}のいずれかにしてください。")
    with db() as conn:
        me = _require_admin(conn)
    merchant_payment_id = f"test-{uuid.uuid4()}"
    # request.base_urlは常にhttp(本番はCaddy経由のDocker内接続のため)。
    # external_scheme([[real_client_ip]]と同じ理由)で実際のスキームに直す
    # (2026-08-27発見・修正。ただし実機決済エラーの直接原因はこれとは
    # 別だったと後日判明・docs/TODO.md参照。httpsにする対応自体は
    # 公式ドキュメントの用法に合わせた正当な修正として維持)。
    scheme = auth.external_scheme(request)
    redirect_url = f"{scheme}://{request.url.netloc}" \
        f"/api/paypay-test/return?mpid={merchant_payment_id}"
    log.info(
        "paypay_test: create admin=%s(id=%s) amount=%s mpid=%s",
        me.get("username"), me["id"], payload.amount_jpy,
        merchant_payment_id)
    try:
        data = paypay.create_code(
            merchant_payment_id, payload.amount_jpy,
            redirect_url=redirect_url,
            order_description=f"PayPayテスト決済 ¥{payload.amount_jpy}",
        )
    except paypay.PayPayError as e:
        log.warning(
            "paypay_test: create FAILED admin=%s mpid=%s: %s",
            me.get("username"), merchant_payment_id, e)
        raise errors.http_error("3018", str(e))
    body = data.get("data") or {}
    if not body.get("url"):
        raise errors.http_error(
            "3018", f"PayPayからurlが返りませんでした: {data}")
    return {
        "ok": True,
        "merchant_payment_id": merchant_payment_id,
        "url": body["url"],
        "deeplink": body.get("deeplink"),
        "code_id": body.get("codeId"),
        "expiry_date": body.get("expiryDate"),
    }


@router.get("/return")
def paypay_return(mpid: str = ""):
    """PayPayのredirectUrl着地点。ここではステータス確認せず、
    フロント(HTML)側からGet Payment Detailsを呼ばせる（管理画面に
    そのまま結果を表示するため）。"""
    query = urllib.parse.urlencode({"mpid": mpid})
    return RedirectResponse(f"/admin/paypay-test?{query}")


@router.get("/details/{merchant_payment_id}")
def details(
    merchant_payment_id: str = Path(pattern=_ID_PATTERN),
):
    """Get Payment Details。支払い完了の判定はここで返る
    data.status == "COMPLETED" を見て行うこと(redirect復帰だけでは
    判定しない)。"""
    with db() as conn:
        me = _require_admin(conn)
    try:
        data = paypay.get_payment_details(merchant_payment_id)
    except paypay.PayPayError as e:
        log.warning(
            "paypay_test: details FAILED admin=%s mpid=%s: %s",
            me.get("username"), merchant_payment_id, e)
        raise errors.http_error("3018", str(e))
    status = (data.get("data") or {}).get("status")
    log.info(
        "paypay_test: details admin=%s mpid=%s status=%s",
        me.get("username"), merchant_payment_id, status)
    return {"ok": True, "raw": data}


class CancelIn(BaseModel):
    merchant_payment_id: str = Field(pattern=_ID_PATTERN)
    code_id: str = Field(pattern=_ID_PATTERN)


@router.post("/cancel")
def cancel(payload: CancelIn):
    """未払いのコードを削除(Delete a Code)。支払い前のみ有効。"""
    with db() as conn:
        me = _require_admin(conn)
    log.info(
        "paypay_test: cancel admin=%s(id=%s) mpid=%s code_id=%s",
        me.get("username"), me["id"], payload.merchant_payment_id,
        payload.code_id)
    try:
        data = paypay.delete_code(payload.code_id)
    except paypay.PayPayError as e:
        log.warning(
            "paypay_test: cancel FAILED admin=%s code_id=%s: %s",
            me.get("username"), payload.code_id, e)
        raise errors.http_error("3018", str(e))
    return {"ok": True, "raw": data}


class RefundIn(BaseModel):
    merchant_payment_id: str
    payment_id: str
    amount_jpy: int


@router.post("/refund")
def do_refund(payload: RefundIn):
    """支払い済みの取消(Refund)。"""
    if payload.amount_jpy not in ALLOWED_AMOUNTS:
        raise errors.http_error(
            "3019", f"金額は{sorted(ALLOWED_AMOUNTS)}のいずれかにしてください。")
    with db() as conn:
        me = _require_admin(conn)
    merchant_refund_id = f"refund-{uuid.uuid4()}"
    log.info(
        "paypay_test: refund admin=%s(id=%s) mpid=%s payment_id=%s "
        "amount=%s merchant_refund_id=%s",
        me.get("username"), me["id"], payload.merchant_payment_id,
        payload.payment_id, payload.amount_jpy, merchant_refund_id)
    try:
        data = paypay.refund(
            merchant_refund_id, payload.payment_id, payload.amount_jpy,
            reason="管理者テスト決済の取消")
    except paypay.PayPayError as e:
        log.warning(
            "paypay_test: refund FAILED admin=%s payment_id=%s: %s",
            me.get("username"), payload.payment_id, e)
        raise errors.http_error("3018", str(e))
    return {"ok": True, "raw": data}
