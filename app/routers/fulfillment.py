"""BASE注文フルフィルメント管理（2026-08-09・Phase A、2026-08-19 Phase B）。

チャージキーの手動/半自動配送を「見逃さない」ための管理用API。
- 注文を台帳(base_orders)に記録（手入力に加え、Phase B(2026-08-19〜)で
  BASE API(GET /1/orders・GET /1/orders/detail)から自動投入もできる）。
- 未配送一覧を古い順で返し、検知から一定時間を超えたものに overdue フラグを付ける。
- 注文に対しチャージキーを発行（平文は応答で一度だけ返す・DBには保存しない）。
- 配送済み/キャンセルに状態を更新する。

管理者(role=admin, ownerを含む)専用。認可は inquiries.py と同じ方式。
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter

from ..services import errors
from pydantic import BaseModel

from ..config import log
from ..database import db
from ..services import base_api, charge_keys, mailer
from ..services.auth import current_user_id

router = APIRouter(prefix="/api/fulfillment", tags=["fulfillment"])

# 検知から配送されないまま何時間で「超過(要対応)」とみなすか。
OVERDUE_HOURS = 24

# 購入金額(税込) -> (付与pt, キー生成パターン4桁)。
# パターンは自分用の識別ラベル（額面は付与pt側で決まる）。使用可能文字は
# charge_keys の ALPHABET（0/1/O/I/L 不可）に限る。
PRICE_TABLE: dict[int, tuple[int, str]] = {
    800: (800, "C5AA"),
    8000: (8800, "C5KK"),
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
        raise errors.http_error("2004", "管理者のみ操作できます。")


def _row_to_dict(r) -> dict:
    d = dict(r)
    # 未配送かつ検知から OVERDUE_HOURS 超過なら overdue=True。
    d["overdue"] = bool(d.pop("_overdue", 0)) and d["status"] == "pending"
    # キーの状態を1つの文字列にまとめる（2026-08-19ユーザー要望「発行済み・
    # 使用済みもわかるといい」・管理画面の表示用）。
    if not d.get("charge_key_id"):
        d["key_status"] = "unissued"
    elif d.pop("charge_key_revoked_at", None):
        d["key_status"] = "revoked"
    elif d.get("charge_key_used_at"):
        d["key_status"] = "used"
    else:
        d["key_status"] = "issued"
    return d


def _log_action(
    conn, order_id: int, action: str, *,
    admin_user_id: int | None = None, note: str = "",
) -> None:
    """base_order_actionsに1行残す（無期限保持・2026-08-19ユーザー要望
    「フルフィルメント管理も無期限で」）。記録失敗で本来の操作を妨げない
    よう best-effort。"""
    try:
        conn.execute(
            "INSERT INTO base_order_actions "
            "(order_id, action, admin_user_id, note) VALUES (?, ?, ?, ?)",
            (order_id, action, admin_user_id, note),
        )
    except Exception:
        log.warning("base_order_actions記録に失敗", exc_info=True)


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
        raise errors.http_error("7002", "金額は正の整数で入力してください。")
    default_pt, _ = _pt_and_pattern(payload.amount_jpy)
    pt = payload.pt_to_grant if payload.pt_to_grant is not None else default_pt
    if pt <= 0:
        raise errors.http_error("7002", "付与ポイントは正の整数にしてください。")
    base_order_id = payload.base_order_id.strip() or None
    with db() as conn:
        _require_admin(conn)
        if base_order_id:
            dup = conn.execute(
                "SELECT 1 FROM base_orders WHERE base_order_id = ?",
                (base_order_id,),
            ).fetchone()
            if dup:
                raise errors.http_error("3011", "この注文IDは既に登録済みです。")
        cur = conn.execute(
            "INSERT INTO base_orders (base_order_id, amount_jpy, pt_to_grant, "
            " product_label, buyer_name, buyer_email, note) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (base_order_id, payload.amount_jpy, pt,
             payload.product_label.strip(), payload.buyer_name.strip(),
             payload.buyer_email.strip(), payload.note.strip()),
        )
        _log_action(
            conn, int(cur.lastrowid), "added",
            admin_user_id=current_user_id())
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
            " k.created_at AS charge_key_issued_at, "
            " k.used_at AS charge_key_used_at, "
            " k.revoked_at AS charge_key_revoked_at, "
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
def issue_key(order_id: int, reissue: bool = False):
    """この注文に対しチャージキーを1つ発行し、平文キーを一度だけ返す。
    平文はDBに保存されない（charge_key_id で参照のみ保持）。

    二重発行防止(2026-08-18): 既にこの注文に有効な(未使用・未失効)キーが
    紐付いている場合、reissue=true を明示しない限り409で拒否する。管理画面
    はコピーし損ねた等で再発行が必要なとき、確認ダイアログを出したうえで
    reissue=true を付けて呼び直す。再発行時は旧キーを失効させてから新しい
    キーを発行するため、1注文につき常に「償還可能なキーは最大1本」になる
    （古いキーが生き残ったまま新キーも生きる、という二重発行状態を防ぐ）。"""
    with db() as conn:
        _require_admin(conn)
        row = conn.execute(
            "SELECT amount_jpy, pt_to_grant, status, charge_key_id "
            "FROM base_orders WHERE id = ?", (order_id,),
        ).fetchone()
        if not row:
            raise errors.http_error("7001", "注文が見つかりません。")
        if row["status"] == "cancelled":
            raise errors.http_error("3012", "キャンセル済みの注文には発行できません。")
        if row["charge_key_id"]:
            existing = conn.execute(
                "SELECT id FROM charge_keys WHERE id = ? "
                "AND used_at IS NULL AND revoked_at IS NULL",
                (row["charge_key_id"],),
            ).fetchone()
            if existing and not reissue:
                raise errors.http_error(
                    "3013", "この注文には既に有効なキーが発行済みです。"
                    "再発行すると古いキーは無効化されます。")
            if existing:
                charge_keys.revoke_key_by_id(conn, existing["id"])
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
        _log_action(
            conn, order_id, "reissued" if reissue else "issued",
            admin_user_id=current_user_id(),
            note=key_id_public)
    return {"ok": True, "charge_key": plain, "pt": int(row["pt_to_grant"])}


@router.get("/stats")
def stats():
    """チャージキーの発行状況サマリ（管理画面の見出しに表示・発行数管理用）。"""
    with db() as conn:
        _require_admin(conn)
        return {"ok": True, **charge_keys.issuance_stats(conn)}


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
            raise errors.http_error("7001", "見つからないか、キャンセル済みです。")
        _log_action(
            conn, order_id, "delivered", admin_user_id=current_user_id(),
            note=(payload.note.strip() if payload else ""))
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
            raise errors.http_error("7001", "見つかりません。")
        _log_action(
            conn, order_id, "cancelled", admin_user_id=current_user_id())
    return {"ok": True}


@router.get("/orders/{order_id}/actions")
def order_actions(order_id: int):
    """この注文に対する操作履歴（誰が/いつ何をしたか・無期限保持・
    2026-08-19ユーザー要望）。"""
    with db() as conn:
        _require_admin(conn)
        rows = conn.execute(
            "SELECT a.action, a.note, a.created_at, "
            " u.username AS admin_username "
            "FROM base_order_actions a "
            "LEFT JOIN users u ON u.id = a.admin_user_id "
            "WHERE a.order_id = ? ORDER BY a.id DESC",
            (order_id,),
        ).fetchall()
        return {"actions": [dict(r) for r in rows]}


# --- Phase B: BASE APIからの注文自動検知（2026-08-19）--------------------

# app_state のキー。最後に同期できた注文日時(ISO)を覚えておき、次回は
# そこから少し余裕を持って(_SYNC_OVERLAP)遡って取り直す(取りこぼし防止)。
_SYNC_STATE_KEY = "base_orders_last_synced_at"
_SYNC_OVERLAP = timedelta(days=2)
_SYNC_INITIAL_LOOKBACK = timedelta(days=35)
# 自動投入の対象にするdispatch_status（支払い済みで発送待ちの状態のみ。
# unpaid=未入金・cancelled=キャンセル・dispatched=発送済み は対象外）。
_SYNC_TARGET_STATUSES = {"ordered"}


def _sync_window(conn) -> tuple[str, str]:
    row = conn.execute(
        "SELECT value FROM app_state WHERE key = ?", (_SYNC_STATE_KEY,),
    ).fetchone()
    now = datetime.now(timezone.utc)
    if row and row["value"]:
        try:
            last = datetime.fromisoformat(row["value"])
            start = last - _SYNC_OVERLAP
        except ValueError:
            start = now - _SYNC_INITIAL_LOOKBACK
    else:
        start = now - _SYNC_INITIAL_LOOKBACK
    return start.strftime("%Y-%m-%d"), now.strftime("%Y-%m-%d")


def _mark_synced(conn, when: datetime) -> None:
    conn.execute(
        "INSERT INTO app_state (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (_SYNC_STATE_KEY, when.isoformat()),
    )


def sync_orders_from_base(conn) -> dict:
    """BASE APIから直近の注文を取得し、未登録かつ支払い済みのものを
    base_ordersへ自動投入する(冪等・base_order_idのUNIQUE制約で重複防止)。
    管理画面の「今すぐ同期」ボタンとcronの両方から呼ばれる共通ロジック。"""
    access_token = base_api.get_valid_access_token(conn)
    start, end = _sync_window(conn)
    raw_orders = base_api.list_orders(access_token, start, end)

    existing_ids = {
        r["base_order_id"] for r in conn.execute(
            "SELECT base_order_id FROM base_orders "
            "WHERE base_order_id IS NOT NULL",
        ).fetchall()
    }

    checked = 0
    new_count = 0
    skipped_status: dict[str, int] = {}
    errors: list[str] = []
    new_orders_detail: list[dict] = []
    for o in raw_orders:
        unique_key = str(o.get("unique_key") or "").strip()
        if not unique_key:
            continue
        checked += 1
        if unique_key in existing_ids:
            continue
        status = o.get("dispatch_status", "")
        if status not in _SYNC_TARGET_STATUSES:
            skipped_status[status] = skipped_status.get(status, 0) + 1
            continue
        try:
            detail = base_api.get_order_detail(access_token, unique_key)
        except base_api.BaseApiError as e:
            log.warning("base_api: detail fetch failed unique_key=%s: %s",
                        unique_key, e)
            errors.append(f"{unique_key}: {e}")
            continue
        amount = detail.get("total") or o.get("total") or 0
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            amount = 0
        if amount <= 0:
            continue
        pt, _pattern = _pt_and_pattern(amount)
        buyer_name = " ".join(filter(None, [
            detail.get("last_name") or o.get("last_name") or "",
            detail.get("first_name") or o.get("first_name") or "",
        ])).strip()
        buyer_email = (detail.get("mail_address") or "").strip()
        items = detail.get("order_items") or []
        product_label = ", ".join(
            str(it.get("title", "")) for it in items if it.get("title")
        )[:200]
        try:
            cur = conn.execute(
                "INSERT INTO base_orders (base_order_id, amount_jpy, "
                " pt_to_grant, product_label, buyer_name, buyer_email, note) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (unique_key, amount, pt, product_label, buyer_name,
                 buyer_email, "BASE APIで自動検知"),
            )
            _log_action(
                conn, int(cur.lastrowid), "synced",
                note=f"BASE API unique_key={unique_key}")
            existing_ids.add(unique_key)
            new_count += 1
            new_orders_detail.append({
                "id": int(cur.lastrowid), "amount_jpy": amount,
                "pt_to_grant": pt, "buyer_name": buyer_name,
                "product_label": product_label,
            })
        except Exception as e:  # UNIQUE制約競合等はスキップして続行
            log.warning("base_api: insert failed unique_key=%s: %s",
                        unique_key, e)
            errors.append(f"{unique_key}: 登録に失敗しました")

    _mark_synced(conn, datetime.now(timezone.utc))
    log.info(
        "base_api: sync done checked=%s new=%s skipped=%s errors=%s",
        checked, new_count, skipped_status, len(errors),
    )
    if new_orders_detail:
        _notify_new_orders(new_orders_detail)
    _notify_overdue_if_needed(conn)
    return {
        "ok": True, "checked": checked, "new_orders": new_count,
        "skipped_status": skipped_status, "errors": errors,
        "window": {"start": start, "end": end},
    }


# --- Phase C: メール通知（2026-08-25）--------------------------------------
# 送信は常にbest-effort（失敗しても同期処理自体は成功として扱う・
# mailer.send_email()自体が例外を握りつぶす設計と二重に保護）。

_OVERDUE_NOTIFY_STATE_KEY = "base_orders_last_overdue_notified_at"
# 未配送リマインドの再送間隔（毎回のcron(30分おき)で送ると鬱陶しいため、
# overdue(=OVERDUE_HOURS超過)が残っている限りこの間隔でダイジェストのみ送る）。
_OVERDUE_NOTIFY_INTERVAL_HOURS = 12


def _notify_new_orders(new_orders_detail: list[dict]) -> None:
    lines = [
        f"BASEで新しい注文を{len(new_orders_detail)}件検知しました"
        "（自動投入済み・要キー発行）。",
        "",
    ]
    for o in new_orders_detail:
        lines.append(
            f"- 注文#{o['id']}: ¥{o['amount_jpy']:,} → {o['pt_to_grant']}pt"
            f" / 購入者: {o['buyer_name'] or '(未取得)'}"
            f" / 商品: {o['product_label'] or '(未取得)'}"
        )
    lines.append("")
    lines.append("管理画面(フルフィルメント管理)からキーを発行してください。")
    try:
        mailer.send_email(
            f"[nyangailab] 新規注文{len(new_orders_detail)}件を検知",
            "\n".join(lines),
        )
    except Exception:
        log.warning("base_api: 新規注文メール通知に失敗", exc_info=True)


def _notify_overdue_if_needed(conn) -> None:
    row = conn.execute(
        "SELECT id, base_order_id, amount_jpy, buyer_name, detected_at "
        "FROM base_orders WHERE status = 'pending' "
        "AND (julianday('now') - julianday(detected_at)) * 24 > ? "
        "ORDER BY detected_at ASC",
        (OVERDUE_HOURS,),
    ).fetchall()
    if not row:
        return
    state = conn.execute(
        "SELECT value FROM app_state WHERE key = ?",
        (_OVERDUE_NOTIFY_STATE_KEY,),
    ).fetchone()
    now = datetime.now(timezone.utc)
    if state and state["value"]:
        try:
            last = datetime.fromisoformat(state["value"])
            if (now - last) < timedelta(hours=_OVERDUE_NOTIFY_INTERVAL_HOURS):
                return
        except ValueError:
            pass
    lines = [
        f"未配送のまま{OVERDUE_HOURS}時間を超えた注文が{len(row)}件あります。",
        "",
    ]
    for o in row:
        lines.append(
            f"- 注文#{o['id']} (検知: {o['detected_at']}): "
            f"¥{o['amount_jpy']:,} / {o['buyer_name'] or '(未取得)'}"
        )
    lines.append("")
    lines.append("管理画面(フルフィルメント管理)から対応してください。")
    try:
        sent = mailer.send_email(
            f"[nyangailab] 未配送の注文が{len(row)}件たまっています",
            "\n".join(lines),
        )
    except Exception:
        sent = False
        log.warning("base_api: 未配送リマインドメール送信に失敗", exc_info=True)
    if sent:
        conn.execute(
            "INSERT INTO app_state (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (_OVERDUE_NOTIFY_STATE_KEY, now.isoformat()),
        )


@router.post("/base-sync")
def base_sync():
    """BASE APIから注文を取得し、未登録の支払い済み注文を自動投入する
    （管理画面の「今すぐ同期」ボタン用）。"""
    with db() as conn:
        _require_admin(conn)
        try:
            return sync_orders_from_base(conn)
        except base_api.BaseApiError as e:
            raise errors.http_error("3014", str(e))
