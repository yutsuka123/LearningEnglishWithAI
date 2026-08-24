"""チャージキー償還API（BASE等で購入したキーをセルフサービスで残高に反映）。"""

from __future__ import annotations

from fastapi import APIRouter

from ..services import errors
from pydantic import BaseModel

from ..config import log
from ..database import db
from ..services import charge_keys
from ..services.auth import current_user_id

router = APIRouter(prefix="/api/billing", tags=["billing"])


class RedeemIn(BaseModel):
    key: str


@router.post("/redeem")
def redeem(payload: RedeemIn):
    """ログイン中のユーザーがチャージキーを償還し、残高(pt)に加算する。
    総当たり対策: 直近1時間に10回失敗した場合はロックする
    （app/services/charge_keys.py の redeem_locked 参照）。"""
    uid = current_user_id()
    if charge_keys.redeem_locked(uid):
        log.warning("billing/redeem: rate-limited uid=%s", uid)
        raise errors.http_error(
            "3003", "失敗が続いたため、しばらく時間をおいてから再試行して"
            "ください。")
    with db() as conn:
        try:
            new_balance = charge_keys.redeem_key(conn, uid, payload.key)
        except charge_keys.ChargeKeyError as e:
            log.warning("billing/redeem: failed uid=%s reason=%s", uid, e)
            raise errors.http_error("3001", str(e))
    log.info("billing/redeem: ok uid=%s new_balance=%s", uid, new_balance)
    return {"ok": True, "balance_jpy": round(new_balance, 1)}
