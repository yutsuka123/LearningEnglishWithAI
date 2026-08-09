"""BASE注文フルフィルメント管理（2026-08-09・Phase A）。

チャージキーの手動/半自動配送を「見逃さない」ための管理用API。
- 注文を台帳(base_orders)に記録（当面は手入力。Phase BでBASE APIから自動投入）。
- 未配送一覧を古い順で返し、検知から一定時間を超えたものに overdue フラグを付ける。
- 注文に対しチャージキーを発行（平文は応答で一度だけ返す・DBには保存しない）。
- 配送済み/キャンセルに状態を更新する。

管理者(role=admin, ownerを含む)専用。認可は inquiries.py と同じ方式。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import db
from ..services import charge_keys
from ..services.auth import current_user_id

router = APIRouter(prefix="/api/fulfillment", tags=["fulfillment"])

# 検知から配送されないまま何時間で「超過(要対応)」とみなすか。
OVERDUE_HOURS = 24

# 購入金額(税込) -> (付与pt, キー生成パターン4桁)。
# パターンは自分用の識別ラベル（額面は付与pt側で決まる）。使用可能文字は
# charge_keys の ALPHABET（0/1/O/I/L 不可）に限る。
PRICE_TABLE: dict[int, tuple[int, str]] = {
    500: (500, "C5AA"),
    5000: (5500, "C5KK"),
}
_DEFAULT_PATTERN = "CZ99"


def _pt_and_pattern(amount_jpy: int) -> tuple[int, str]:
    """金額から (付与pt, パターン) を返す。未定義額は pt=額面, 既定パターン。"""
    if amount_jpy in PRICE_TABLE:
        return PRICE_TABLE[amount_jpy]
    return amount_jpy, _DEFAULT_PATTERN


def _require_admin(conn) -> None:
    from ..services import auth
    me = auth.get_user(conn, current_user_id())
    if not me or me.get("role") != "admin":
        raise HTTPException(403, "管理者のみ操作できます。")


def _row_to_dict(r) -> dict:
    d = dict(r)
    # 未配送かつ検知から OVERDUE_HOURS 超過なら overdue=True。
    d["overdue"] = bool(d.pop("_overdue", 0)) and d["status"] == "pending"
    return d


class OrderIn(BaseModel):
    amount_jpy: int
    base_order_id: str = ""
    buyer_name: str = ""
    buyer_email: str = ""
    product_label: str = ""
    pt_to_grant: int | None = None
    note: str = ""


@router.post("/orders")
def add_order(payload: OrderIn):
    """注文を台帳に追加（手入力）。付与ptは未指定なら金額表から自動決定。"""
    if payload.amount_jpy <= 0:
        raise HTTPException(400, "金額は正の整数で入力してください。")
    default_pt, _ = _pt_and_pattern(payload.amount_jpy)
    pt = payload.pt_to_grant if payload.pt_to_grant is not None else default_pt
    if pt <= 0:
        raise HTTPException(400, "付与ポイントは正の整数にしてください。")
    base_order_id = payload.base_order_id.strip() or None
    with db() as conn:
        _require_admin(conn)
        if base_order_id:
            dup = conn.execute(
                "SELECT 1 FROM base_orders WHERE base_order_id = ?",
                (base_order_id,),
            ).fetchone()
            if dup:
                raise HTTPException(409, "この注文IDは既に登録済みです。")
        cur = conn.execute(
            "INSERT INTO base_orders (base_order_id, amount_jpy, pt_to_grant, "
            " product_label, buyer_name, buyer_email, note) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (base_order_id, payload.amount_jpy, pt,
             payload.product_label.strip(), payload.buyer_name.strip(),
             payload.buyer_email.strip(), payload.note.strip()),
        )
    return {"ok": True, "id": int(cur.lastrowid)}


@router.get("/orders")
def list_orders(status: str = "pending"):
    """注文一覧。status で絞り込み（pending/delivered/cancelled/all）。
    未配送は古い順（対応漏れ防止）、それ以外は新しい順で返す。"""
    with db() as conn:
        _require_admin(conn)
        where = ""
        args: tuple = ()
        if status and status != "all":
            where = "WHERE o.status = ?"
            args = (status,)
        order_by = ("o.detected_at ASC" if status == "pending"
                    else "o.id DESC")
        rows = conn.execute(
            "SELECT o.id, o.base_order_id, o.amount_jpy, o.pt_to_grant, "
            " o.product_label, o.buyer_name, o.buyer_email, o.charge_key_id, "
            " o.status, o.note, o.detected_at, o.delivered_at, "
            " k.key_id AS charge_key_public_id, "
            " CASE WHEN (julianday('now') - julianday(o.detected_at)) * 24 "
            "      > ? THEN 1 ELSE 0 END AS _overdue "
            "FROM base_orders o "
            "LEFT JOIN charge_keys k ON k.id = o.charge_key_id "
            f"{where} ORDER BY {order_by}",
            (OVERDUE_HOURS, *args),
        ).fetchall()
        counts = dict(conn.execute(
            "SELECT status, COUNT(*) FROM base_orders GROUP BY status"
        ).fetchall())
    pending = int(counts.get("pending", 0))
    return {
        "orders": [_row_to_dict(r) for r in rows],
        "counts": {k: int(v) for k, v in counts.items()},
        "pending": pending,
        "overdue_hours": OVERDUE_HOURS,
    }


@router.post("/orders/{order_id}/issue_key")
def issue_key(order_id: int):
    """この注文に対しチャージキーを1つ発行し、平文キーを一度だけ返す。
    平文はDBに保存されない（charge_key_id で参照のみ保持）。控え損ねた場合は
    再発行してよい（未償還の旧キーは無害）。"""
    with db() as conn:
        _require_admin(conn)
        row = conn.execute(
            "SELECT amount_jpy, pt_to_grant, status FROM base_orders "
            "WHERE id = ?", (order_id,),
        ).fetchone()
        if not row:
            raise HTTPException(404, "注文が見つかりません。")
        if row["status"] == "cancelled":
            raise HTTPException(400, "キャンセル済みの注文には発行できません。")
        _pt, pattern = _pt_and_pattern(row["amount_jpy"])
        plain = charge_keys.generate_key(
            conn, pattern=pattern, amount_jpy=int(row["pt_to_grant"]))
        # 生成したキーのidを、注文に紐付ける（key_idで逆引き）。
        key_id_public = plain[: charge_keys.KEY_ID_DIGITS]
        krow = conn.execute(
            "SELECT id FROM charge_keys WHERE key_id = ?", (key_id_public,),
        ).fetchone()
        if krow:
            conn.execute(
                "UPDATE base_orders SET charge_key_id = ? WHERE id = ?",
                (krow["id"], order_id),
            )
    return {"ok": True, "charge_key": plain, "pt": int(row["pt_to_grant"])}


class StatusUpdate(BaseModel):
    note: str = ""


@router.post("/orders/{order_id}/deliver")
def deliver(order_id: int, payload: StatusUpdate | None = None):
    """配送済みにする（delivered_at を記録）。"""
    with db() as conn:
        _require_admin(conn)
        cur = conn.execute(
            "UPDATE base_orders SET status = 'delivered', "
            " delivered_at = datetime('now') WHERE id = ? "
            " AND status != 'cancelled'",
            (order_id,),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "見つからないか、キャンセル済みです。")
    return {"ok": True}


@router.post("/orders/{order_id}/cancel")
def cancel(order_id: int):
    """注文をキャンセル状態にする。"""
    with db() as conn:
        _require_admin(conn)
        cur = conn.execute(
            "UPDATE base_orders SET status = 'cancelled' WHERE id = ?",
            (order_id,),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "見つかりません。")
    return {"ok": True}
