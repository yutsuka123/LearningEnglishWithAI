"""PayPayでのpt購入（実課金導線・2026-09-01新設）。

`app/routers/paypay_test.py`（管理者専用のサンドボックス結合テスト）とは
別に、ログイン中の一般ユーザーが実際にpt(残高)を購入できる導線。

安全設計（ユーザー指示「安全策」への対応・2026-09-01）:
  1. 支払い完了の判定は必ずGet Payment Details(`data.status=="COMPLETED"`)
     で行う。redirect復帰それ自体を成功の根拠にしない
     (`app/services/paypay.py`参照)。ユーザーがPayPayアプリで途中
     キャンセルした場合はstatusがCOMPLETEDにならないため、pt付与は
     一切起こらない。
  2. pt付与は`paypay_payments.credited_at`が空(NULL)の行だけを対象に
     した原子的なUPDATE(`WHERE credited_at IS NULL`)が成功した場合のみ
     実行する。これは`app/services/charge_keys.py`の`redeem_key`と全く
     同じ二重防止パターンで、確認ボタンの連打・複数タブでの同時確認・
     後述の巡回スクリプトのいずれから来ても、同じ支払いに対してpt付与は
     構造的に1回しか起こり得ない。
  3. ユーザーが支払い後にブラウザへ戻ってこなかった場合（タブを閉じる
     等）に備え、`scripts/reconcile_paypay_payments.py`をVPSのcronで
     定期実行し、未確定のまま放置された支払いを追跡確認する。この
     ルーターの`/confirm`エンドポイントだけに決済確定を依存させない。
  4. 金額はALLOWED_AMOUNTS(BASEショップの既存価格帯と同じ¥800/¥8000)
     のみ受け付け、クライアントからの任意額指定は拒否する。
"""

from __future__ import annotations

import urllib.parse
import uuid

from fastapi import APIRouter, Path, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from ..config import log
from ..database import db
from ..services import auth, errors, paypay

router = APIRouter(prefix="/api/paypay", tags=["paypay-charge"])

# 動作確認用のpaypay_test.pyと同じ価格帯(BASEショップの既存2プラン)。
ALLOWED_AMOUNTS = {800, 8000}

# merchantPaymentId用の形式検証(パス注入対策、paypay_test.pyと同じ方針)。
_ID_PATTERN = r"^[A-Za-z0-9_-]{1,64}$"

# app_stateのキー。一般公開のON/OFF切替(2026-09-01・ユーザー指示
# 「本番環境が開通後、管理者がテストしてそれが成功した後公開します」)。
_PUBLIC_FLAG_KEY = "paypay_charge_public_enabled"


def _public_enabled(conn) -> bool:
    row = conn.execute(
        "SELECT value FROM app_state WHERE key = ?", (_PUBLIC_FLAG_KEY,)
    ).fetchone()
    return bool(row and row["value"] == "true")


def _guard_not_yet_public(conn, uid: int) -> None:
    """一般公開前は管理者だけがこの導線を使える(2段階ゲート):
    1) PAYPAY_PRODUCTION_MODE=trueでないとサンドボックスのままお金を
       払わずにptだけ付与されてしまう(is_production()がFalseの間は常に
       ブロック)。
    2) 本番モードになった後も、_PUBLIC_FLAG_KEYが'true'になるまでは
       一般ユーザーには公開しない(管理者が実機で動作確認してから
       app_stateを更新して公開する運用)。
    どちらの段階でも管理者(role='admin')は自分自身のテストのため常に
    通す。"""
    me = auth.get_user(conn, uid)
    is_admin = bool(me and me.get("role") == "admin")
    if is_admin:
        return
    if not paypay.is_production() or not _public_enabled(conn):
        raise errors.http_error("3020")


def _record(
    conn, action: str, user_id: int, *, mpid: str = "", code_id: str = "",
    payment_id: str = "", amount_jpy: int | None = None, status: str = "",
    ok: bool = True, note: str = "",
) -> None:
    """paypay_actionsテーブルへ監査ログを残す(paypay_test.pyの
    _record_actionと同じ設計。この記録自体の失敗で本処理を落とさない)。"""
    try:
        conn.execute(
            "INSERT INTO paypay_actions (action, user_id, "
            "merchant_payment_id, code_id, payment_id, amount_jpy, "
            "status, ok, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (action, user_id, mpid, code_id, payment_id, amount_jpy,
             status, 1 if ok else 0, note[:500]),
        )
        conn.commit()
    except Exception as e:  # noqa: BLE001 - 監査ログの失敗は握りつぶす
        log.warning("paypay_actions記録に失敗しました: %s", e)


class CreateIn(BaseModel):
    amount_jpy: int


@router.post("/create")
def create(payload: CreateIn, request: Request):
    """pt購入用の支払いコードを作成する。一般公開されるまでは管理者の
    自己テストのみに制限する(`_guard_not_yet_public`参照)。未ログインは
    `_auth_context`ミドルウェアが先に401を返す。"""
    if payload.amount_jpy not in ALLOWED_AMOUNTS:
        raise errors.http_error(
            "3019",
            f"金額は{sorted(ALLOWED_AMOUNTS)}のいずれかにしてください。")
    uid = auth.current_user_id()
    with db() as conn:
        _guard_not_yet_public(conn, uid)
    merchant_payment_id = f"charge-{uuid.uuid4()}"
    # request.base_urlは常にhttp(本番はCaddy経由のDocker内接続のため)。
    # external_schemeで実際のスキームに直す(paypay_test.pyと同じ理由)。
    scheme = auth.external_scheme(request)
    redirect_url = (
        f"{scheme}://{request.url.netloc}/api/paypay/return"
        f"?mpid={merchant_payment_id}")
    with db() as conn:
        conn.execute(
            "INSERT INTO paypay_payments (user_id, merchant_payment_id, "
            "amount_jpy, status) VALUES (?, ?, ?, 'CREATED')",
            (uid, merchant_payment_id, payload.amount_jpy),
        )
        conn.commit()
    log.info(
        "paypay_charge: create uid=%s amount=%s mpid=%s",
        uid, payload.amount_jpy, merchant_payment_id)
    try:
        data = paypay.create_code(
            merchant_payment_id, payload.amount_jpy,
            redirect_url=redirect_url,
            order_description=f"pt購入 ¥{payload.amount_jpy}",
        )
    except paypay.PayPayError as e:
        log.warning(
            "paypay_charge: create FAILED uid=%s mpid=%s: %s",
            uid, merchant_payment_id, e)
        with db() as conn:
            # statusをFAILEDにしておかないと、この行がcredited_at NULLの
            # まま残り続け、reconcile_paypay_payments.pyが実在しない
            # merchantPaymentIdを7日間毎回PayPayに問い合わせ続けてしまう
            # (Opusレビュー指摘・2026-09-01)。
            conn.execute(
                "UPDATE paypay_payments SET status = 'FAILED', "
                "updated_at = datetime('now') "
                "WHERE merchant_payment_id = ?", (merchant_payment_id,))
            _record(conn, "create", uid, mpid=merchant_payment_id,
                    amount_jpy=payload.amount_jpy, ok=False, note=str(e))
        raise errors.http_error("3018", str(e))
    body = data.get("data") or {}
    if not body.get("url"):
        with db() as conn:
            conn.execute(
                "UPDATE paypay_payments SET status = 'FAILED', "
                "updated_at = datetime('now') "
                "WHERE merchant_payment_id = ?", (merchant_payment_id,))
            _record(conn, "create", uid, mpid=merchant_payment_id,
                    amount_jpy=payload.amount_jpy, ok=False,
                    note="PayPayからurlが返らなかった")
        raise errors.http_error(
            "3018", f"PayPayからurlが返りませんでした: {data}")
    with db() as conn:
        conn.execute(
            "UPDATE paypay_payments SET code_id = ?, updated_at = "
            "datetime('now') WHERE merchant_payment_id = ?",
            (body.get("codeId") or "", merchant_payment_id),
        )
        _record(conn, "create", uid, mpid=merchant_payment_id,
                code_id=body.get("codeId") or "",
                amount_jpy=payload.amount_jpy, ok=True)
    return {
        "ok": True,
        "merchant_payment_id": merchant_payment_id,
        "url": body["url"],
        "deeplink": body.get("deeplink"),
    }


@router.get("/return")
def paypay_return(mpid: str = ""):
    """PayPayのredirectUrl着地点。ここでは何も確定せず、専用の確認ページ
    (`/paypay-charge`)にmpidを渡すだけ(paypay_test.pyと同じ方針:
    redirect復帰そのものを成功の証拠にしない)。"""
    query = urllib.parse.urlencode({"mpid": mpid})
    return RedirectResponse(f"/paypay-charge?{query}")


@router.get("/confirm/{merchant_payment_id}")
def confirm(merchant_payment_id: str = Path(pattern=_ID_PATTERN)):
    """支払い状況をPayPayに問い合わせ、COMPLETEDならpt付与する。
    何度呼ばれても安全(冪等)。付与済みかどうかは`credited_at`で判定する
    ため、このエンドポイントを何度叩いても二重付与は起こらない。"""
    uid = auth.current_user_id()
    with db() as conn:
        _guard_not_yet_public(conn, uid)
        row = conn.execute(
            "SELECT * FROM paypay_payments WHERE merchant_payment_id = ?",
            (merchant_payment_id,),
        ).fetchone()
        if not row:
            raise errors.http_error("7001", "対象の支払いが見つかりません。")
        if row["user_id"] != uid:
            raise errors.http_error("3021")
        already_credited = row["credited_at"] is not None
        amount_jpy = row["amount_jpy"]

    try:
        data = paypay.get_payment_details(merchant_payment_id)
    except paypay.PayPayError as e:
        log.warning(
            "paypay_charge: confirm FAILED uid=%s mpid=%s: %s",
            uid, merchant_payment_id, e)
        with db() as conn:
            _record(conn, "details", uid, mpid=merchant_payment_id,
                    amount_jpy=amount_jpy, ok=False, note=str(e))
        raise errors.http_error("3018", str(e))
    body = data.get("data") or {}
    status = body.get("status") or ""
    payment_id = body.get("paymentId") or ""

    with db() as conn:
        # 二重付与を構造的に防ぐ核心ロジックはapp/services/paypay.pyの
        # credit_if_completedに一本化(scripts/reconcile_paypay_payments.py
        # と挙動を一致させるため)。
        credited_now = paypay.credit_if_completed(
            conn, row, status, payment_id)
        me = auth.get_user(conn, uid)
        _record(conn, "details", uid, mpid=merchant_payment_id,
                payment_id=payment_id, amount_jpy=amount_jpy,
                status=status, ok=True,
                note="credited" if credited_now else "")
    log.info(
        "paypay_charge: confirm uid=%s mpid=%s status=%s credited_now=%s",
        uid, merchant_payment_id, status, credited_now)
    balance_jpy = me.get("balance_jpy") if me else None
    return {
        "ok": True,
        "status": status,
        "credited": credited_now or already_credited,
        "balance_jpy": round(balance_jpy, 1) if balance_jpy is not None
        else None,
        "amount_jpy": amount_jpy,
    }
