"""PayPay支払いの取りこぼし救済(2026-09-01新設・実課金導線の安全策)。

ユーザーがPayPayアプリで支払いを完了した直後にブラウザへ戻ってこな
かった場合(タブを閉じる・アプリを閉じる等)、`app/routers/paypay_charge.py`
の`/confirm`エンドポイントが一度も呼ばれず、支払い済みなのにpt未付与の
まま`paypay_payments`に残り続けることがありうる。このスクリプトは
「作成されてから一定時間経つのに未確定(credited_atが空)」の行を定期的に
拾い、PayPayに直接ステータスを問い合わせて、COMPLETEDならpt付与する。

付与の可否判定・二重防止は`/confirm`と全く同じ
`app/services/paypay.py`の`credit_if_completed`を呼ぶ(挙動を一致させ、
実装を2箇所でずらさないため)。

対象の絞り込み:
  - 作成から10分以上経過（支払い中の可能性がある直近の行には触れない）
  - 作成から7日以内（それ以上古い行はPayPay側のコード有効期限も切れて
    おり、今さら救済してもユーザー体験上意味が薄いため対象外。7日を
    超えて未確定のまま残る行は、放置された/キャンセルされた支払いの
    ノイズとして扱い、必要なら別途手動で調査する）

使い方(VPSのコンテナ内・cronで15〜30分おき程度を想定):
    docker cp scripts/reconcile_paypay_payments.py eigo-app:/app/scripts/
    docker exec -i eigo-app python scripts/reconcile_paypay_payments.py
VPSホストのcrontabへの登録例(15分おき):
    */15 * * * * cd ~/eigo && docker exec eigo-app \
        python scripts/reconcile_paypay_payments.py \
        >> data/reconcile_paypay_cron.log 2>&1
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import log  # noqa: E402
from app.database import db  # noqa: E402
from app.services import paypay  # noqa: E402


def main() -> int:
    # 本番モードでない間はサンドボックスのテスト決済(管理者の動作確認用)
    # がここでpt付与されてしまう恐れがあるため、常にスキップする
    # (Opusレビュー指摘・2026-09-01。公開フラグ自体はこのcronの安全装置
    # ではなく、あくまで一般ユーザーへの導線公開/非公開の切替なので
    # 別途チェックしない)。
    if not paypay.is_production():
        print("PAYPAY_PRODUCTION_MODE=false のためスキップしました。")
        return 0
    checked = credited = errored = 0
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM paypay_payments WHERE credited_at IS NULL "
            "AND status != 'FAILED' "
            "AND created_at <= datetime('now', '-10 minutes') "
            "AND created_at >= datetime('now', '-7 days') "
            "ORDER BY created_at"
        ).fetchall()
    for row in rows:
        mpid = row["merchant_payment_id"]
        checked += 1
        try:
            data = paypay.get_payment_details(mpid)
        except paypay.PayPayError as e:
            errored += 1
            log.warning(
                "reconcile_paypay_payments: FAILED mpid=%s: %s", mpid, e)
            continue
        body = data.get("data") or {}
        status = body.get("status") or ""
        payment_id = body.get("paymentId") or ""
        with db() as conn:
            did_credit = paypay.credit_if_completed(
                conn, row, status, payment_id)
        if did_credit:
            credited += 1
            log.info(
                "reconcile_paypay_payments: credited uid=%s mpid=%s "
                "amount=%s", row["user_id"], mpid, row["amount_jpy"])
    print(f"確認 {checked} 件 / 新規付与 {credited} 件 / 失敗 {errored} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
