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
  - 作成から1分以上経過（支払い中の可能性が高い直近の行には触れない。
    2026-09-07・当初は10分だったが、実機で「支払い後すぐタブを閉じた」
    ケースの反映が最大25分ほど遅れた実例が出たため短縮。PayPay側の
    決済画面に出る「◯分以内にお支払いください」という案内は支払う側
    への呼びかけであり、実際にはコードは支払われるまでstatus="CREATED"
    のまま自動失効しないことを実機確認済み。そのため早めに・頻繁に
    見に行っても無駄がなく、むしろ反映を早くできる）
  - 作成から7日以内（それ以上古い行は放置された/キャンセルされた支払いの
    ノイズとして扱い、必要なら別途手動で調査する。cron間隔を短くした分
    問い合わせ回数は増えるが、CANCELED/EXPIRED等の終端状態になった行は
    除外されるため実際に無限に叩き続けるのは「支払われずCREATEDのまま
    残り続ける行」だけに限られる）

使い方(VPSのコンテナ内・cronで2〜3分おきを想定・2026-09-07に15分おきから
短縮):
    docker cp scripts/reconcile_paypay_payments.py eigo-app:/app/scripts/
    docker exec -i eigo-app python scripts/reconcile_paypay_payments.py
VPSホストのcrontabへの登録例(2分おき):
    */2 * * * * cd ~/eigo && docker exec eigo-app \
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
        # credit_if_completedはCOMPLETED以外でもPayPay側の最新statusを
        # 書き戻す(create()直後のFAILEDと同じ理由)。CANCELED/EXPIREDに
        # なった行を除外し忘れると、7日間・15分おきに同じ結論(未払いの
        # まま)を問い合わせ続けてしまう(2026-09-07・Fable監査指摘。
        # 一般公開後は「作っただけで払わない」が常態化するため無視できない
        # ノイズになる)。
        rows = conn.execute(
            "SELECT * FROM paypay_payments WHERE credited_at IS NULL "
            "AND status NOT IN ('FAILED', 'CANCELED', 'EXPIRED') "
            "AND created_at <= datetime('now', '-1 minutes') "
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
        paypay_amount_jpy = (body.get("amount") or {}).get("amount")
        with db() as conn:
            did_credit = paypay.credit_if_completed(
                conn, row, status, payment_id,
                paypay_amount_jpy=paypay_amount_jpy)
        if did_credit:
            credited += 1
            log.info(
                "reconcile_paypay_payments: credited uid=%s mpid=%s "
                "amount=%s", row["user_id"], mpid, row["amount_jpy"])
    print(f"確認 {checked} 件 / 新規付与 {credited} 件 / 失敗 {errored} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
