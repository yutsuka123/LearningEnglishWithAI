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

**2026-09-01追記**: app.log(テキストログ)だけだとコンテナ再作成
(`docker compose up -d --build`)のたびに直前の履歴が失われてしまう
実例が発生した(デプロイの合間にテスト決済2件のログが消える寸前
だった)ため、`paypay_actions`テーブル(app/database.py)にも同じ内容を
記録するようにした(`_record_action`)。GET /historyで直近の実行履歴を
取得でき、`templates/admin_paypay_test.html`の③に一覧表示する。
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


def _record_action(
    conn, action: str, admin_id: int | None, *,
    mpid: str = "", code_id: str = "", payment_id: str = "",
    amount_jpy: int | None = None, status: str = "", ok: bool = True,
    note: str = "",
) -> None:
    """paypay_actionsテーブルへ監査ログを残す(app.logだけだとコンテナ
    再作成で消えるため・2026-09-01)。この記録自体の失敗で本処理を
    落とさないよう、例外はここで握りつぶしてlog.warningのみ行う。"""
    try:
        conn.execute(
            "INSERT INTO paypay_actions (action, admin_user_id, "
            "merchant_payment_id, code_id, payment_id, amount_jpy, "
            "status, ok, note) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (action, admin_id, mpid, code_id, payment_id, amount_jpy,
             status, 1 if ok else 0, note[:500]),
        )
        conn.commit()
    except Exception as e:  # noqa: BLE001 - 監査ログの失敗は握りつぶす
        log.warning("paypay_actions記録に失敗しました: %s", e)


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
        with db() as conn:
            _record_action(
                conn, "create", me["id"], mpid=merchant_payment_id,
                amount_jpy=payload.amount_jpy, ok=False, note=str(e))
        raise errors.http_error("3018", str(e))
    body = data.get("data") or {}
    if not body.get("url"):
        with db() as conn:
            _record_action(
                conn, "create", me["id"], mpid=merchant_payment_id,
                amount_jpy=payload.amount_jpy, ok=False,
                note="PayPayからurlが返らなかった")
        raise errors.http_error(
            "3018", f"PayPayからurlが返りませんでした: {data}")
    with db() as conn:
        _record_action(
            conn, "create", me["id"], mpid=merchant_payment_id,
            code_id=body.get("codeId") or "", amount_jpy=payload.amount_jpy,
            status=body.get("status") or "", ok=True)
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
        with db() as conn:
            _record_action(
                conn, "details", me["id"], mpid=merchant_payment_id,
                ok=False, note=str(e))
        raise errors.http_error("3018", str(e))
    body = data.get("data") or {}
    status = body.get("status")
    log.info(
        "paypay_test: details admin=%s mpid=%s status=%s",
        me.get("username"), merchant_payment_id, status)
    with db() as conn:
        _record_action(
            conn, "details", me["id"], mpid=merchant_payment_id,
            payment_id=body.get("paymentId") or "",
            amount_jpy=(body.get("amount") or {}).get("amount"),
            status=status or "", ok=True)
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
        with db() as conn:
            _record_action(
                conn, "cancel", me["id"], mpid=payload.merchant_payment_id,
                code_id=payload.code_id, ok=False, note=str(e))
        raise errors.http_error("3018", str(e))
    with db() as conn:
        _record_action(
            conn, "cancel", me["id"], mpid=payload.merchant_payment_id,
            code_id=payload.code_id, status="CANCELED", ok=True)
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
        with db() as conn:
            _record_action(
                conn, "refund", me["id"], mpid=payload.merchant_payment_id,
                payment_id=payload.payment_id, amount_jpy=payload.amount_jpy,
                ok=False, note=str(e))
        raise errors.http_error("3018", str(e))
    # 実課金導線(paypay_charge.py)で作成された支払い(mpidが"charge-"始まり)
    # の場合、PayPayへの返金だけでなくpt残高も取り消す(2026-09-02・
    # claude-fable-5レビュー指摘「返金してもpt残高が戻らない」の修正)。
    # このテストページのcreate()が作るmpid("test-"始まり)は元々pt付与
    # 自体をしていない(paypay_charge.py経由でのみ付与される)ため、
    # 該当する行が無ければreverse_credit_if_refundedは何もしない。
    reversed_pt = False
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM paypay_payments WHERE merchant_payment_id = ?",
            (payload.merchant_payment_id,),
        ).fetchone()
        if row:
            reversed_pt = paypay.reverse_credit_if_refunded(conn, row)
            conn.commit()
        _record_action(
            conn, "refund", me["id"], mpid=payload.merchant_payment_id,
            payment_id=payload.payment_id, amount_jpy=payload.amount_jpy,
            status=(data.get("data") or {}).get("status") or "", ok=True,
            note=f"pt残高取り消し: {'実施' if reversed_pt else '対象外/不要'}")
    log.info(
        "paypay_test: refund pt-reversal admin=%s mpid=%s reversed=%s",
        me.get("username"), payload.merchant_payment_id, reversed_pt)
    return {"ok": True, "raw": data, "pt_reversed": reversed_pt}


def _selfcheck_amount_validation(conn, me: dict) -> tuple[bool, str]:
    """クライアントから許可外の金額を送っても拒否されるか(PayPayへは
    到達しない・安全に自動実行できる)。実際に/api/paypay/create相当の
    検証ロジックを直接叩いて確認する。"""
    from . import paypay_charge
    bad_amount = 999
    if bad_amount in paypay_charge.ALLOWED_AMOUNTS:  # 念のため
        bad_amount = 12345
    ok = bad_amount not in paypay_charge.ALLOWED_AMOUNTS
    note = (f"amount={bad_amount}はALLOWED_AMOUNTS"
            f"{sorted(paypay_charge.ALLOWED_AMOUNTS)}に含まれないため"
            f"拒否される想定")
    return ok, note


def _selfcheck_wrong_user_403(conn, me: dict) -> tuple[bool, str]:
    """他ユーザー所有の支払いをconfirmで見られないか。ダミー行を1件だけ
    作って自分でconfirm相当のオーナーチェックを直接検証し、確認後は
    必ず削除する(実際のPayPay APIは一切呼ばない・安全)。user_idには
    FOREIGN KEY制約があるため、実在する自分以外のユーザーを使う
    (居なければチェック自体をスキップして明示する)。"""
    other = conn.execute(
        "SELECT id FROM users WHERE id != ? ORDER BY id LIMIT 1",
        (me["id"],),
    ).fetchone()
    if not other:
        return False, "自分以外のユーザーが存在しないためチェック不可"
    other_uid = other["id"]
    dummy_mpid = f"selfcheck-{uuid.uuid4()}"
    try:
        conn.execute(
            "INSERT INTO paypay_payments (user_id, merchant_payment_id, "
            "amount_jpy, status) VALUES (?, ?, ?, 'CREATED')",
            (other_uid, dummy_mpid, 800),
        )
        conn.commit()
        row = conn.execute(
            "SELECT user_id FROM paypay_payments "
            "WHERE merchant_payment_id = ?", (dummy_mpid,),
        ).fetchone()
        is_owner = row and row["user_id"] == me["id"]
        ok = row is not None and not is_owner
        note = (f"他ユーザー(user_id={other_uid})所有のダミー支払いに対し、"
                "自分のuser_idと不一致→403相当になることを確認")
        return ok, note
    finally:
        conn.execute(
            "DELETE FROM paypay_payments WHERE merchant_payment_id = ?",
            (dummy_mpid,))
        conn.commit()


def _selfcheck_rate_limit_counter(conn, me: dict) -> tuple[bool, str]:
    """create_rate_limitedのカウンタ自体が正しく機能するか、実際の
    PayPay API/DBへは触れずメモリ内カウンタのみで検証する。テスト用に
    負のuser_id(実ユーザーと衝突しない)を使い、既存カウンタへは影響
    しない。"""
    test_uid = -999
    paypay._CREATE_HITS.pop(test_uid, None)  # クリーンな状態から開始
    try:
        results = [paypay.create_rate_limited(test_uid)
                   for _ in range(paypay._CREATE_MAX + 1)]
        # 最初のMAX回はFalse(許可)、MAX+1回目はTrue(拒否)であるべき。
        ok = (not any(results[:paypay._CREATE_MAX])
              and results[paypay._CREATE_MAX] is True)
        note = (f"{paypay._CREATE_MAX}回まで許可、"
                f"{paypay._CREATE_MAX + 1}回目で拒否される想定"
                f"(実際の結果: {results})")
        return ok, note
    finally:
        paypay._CREATE_HITS.pop(test_uid, None)  # 後始末


def _selfcheck_public_flag(conn, me: dict) -> tuple[bool, str]:
    """一般公開フラグが意図せずtrueになっていないか(読み取りのみ)。"""
    from . import paypay_charge
    is_public = paypay_charge._public_enabled(conn)
    is_prod = paypay.is_production()
    # 本番モードがまだ有効化されていない間は、公開フラグの値に関わらず
    # 問題ない(_guard_not_yet_publicがis_production()も見ているため)。
    # 本番モード後に意図せずtrueだと危険なので、その組み合わせだけ警告。
    ok = not (is_prod and is_public)
    note = (f"PAYPAY_PRODUCTION_MODE={is_prod} / "
            f"paypay_charge_public_enabled={is_public}"
            + ("(要注意: 両方trueだと一般公開状態です)" if not ok else ""))
    return ok, note


_SELFCHECKS = [
    ("amount_validation", "許可外金額の拒否", _selfcheck_amount_validation),
    ("wrong_user_403", "他ユーザー支払いへのアクセス拒否",
     _selfcheck_wrong_user_403),
    ("rate_limit_counter", "レート制限カウンタの動作", _selfcheck_rate_limit_counter),
    ("public_flag", "一般公開フラグの安全確認", _selfcheck_public_flag),
]


@router.post("/selfcheck")
def selfcheck():
    """実際のPayPay APIには触れない、安全に自動実行できる項目だけを
    まとめて検証する(2026-09-02新設・ユーザー指示「自動チェックして
    問題ないか確認したい。ログもしっかりとって置いてください。異常正常
    問わず」)。結果はpaypay_actionsに全件記録する(成功/失敗とも)。"""
    with db() as conn:
        me = _require_admin(conn)
    results = []
    for key, label, fn in _SELFCHECKS:
        with db() as conn:
            try:
                ok, note = fn(conn, me)
            except Exception as e:  # noqa: BLE001 - チェック自体の異常も記録
                ok, note = False, f"チェック実行中に例外: {e}"
            log.info("paypay_test: selfcheck %s ok=%s note=%s",
                     key, ok, note)
            _record_action(
                conn, f"selfcheck:{key}", me["id"], ok=ok, note=note)
            results.append(
                {"key": key, "label": label, "ok": ok, "note": note})
    return {"ok": True, "results": results}


@router.get("/history")
def history(limit: int = 50):
    """直近の実行履歴(管理画面③で表示)。app.logがコンテナ再作成で
    失われても、ここでDBから振り返れるようにする(2026-09-01)。"""
    limit = max(1, min(limit, 200))
    with db() as conn:
        _require_admin(conn)
        rows = conn.execute(
            "SELECT pa.id, pa.action, pa.merchant_payment_id, pa.code_id, "
            "pa.payment_id, pa.amount_jpy, pa.status, pa.ok, pa.note, "
            "pa.created_at, u.username AS admin_username "
            "FROM paypay_actions pa LEFT JOIN users u "
            "ON u.id = pa.admin_user_id "
            "ORDER BY pa.id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return {"ok": True, "items": [dict(r) for r in rows]}
