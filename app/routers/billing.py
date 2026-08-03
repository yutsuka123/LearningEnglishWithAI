"""チャージキー償還API（BASE等で購入したキーをセルフサービスで残高に反映）。"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import db
from ..services import charge_keys
from ..services.auth import current_user_id

router = APIRouter(prefix="/api/billing", tags=["billing"])


class RedeemIn(BaseModel):
    key: str


@router.post("/redeem")
def redeem(payload: RedeemIn):
    """ログイン中のユーザーがチャージキーを償還し、残高(pt)に加算する。"""
    with db() as conn:
        try:
            new_balance = charge_keys.redeem_key(
                conn, current_user_id(), payload.key)
        except charge_keys.ChargeKeyError as e:
            raise HTTPException(400, str(e))
    return {"ok": True, "balance_jpy": round(new_balance, 1)}
