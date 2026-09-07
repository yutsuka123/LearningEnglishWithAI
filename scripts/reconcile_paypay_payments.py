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

確認間隔(バックオフ方式・2026-09-08ユーザー指示「1決済に対してすでに
確認済みの内容を何度も確認している」問題への対応。cron自体は2分おきの
ままだが、このスクリプト側で「今回の実行で本当にPayPayに問い合わせる
必要がある行」だけに絞り込む・`_due_for_check`参照):
  - 作成から10分未満: 支払い直後の反映を早くしたいため、cronが回る
    たびに毎回確認する(2026-09-07に「10分以内の反映遅延」対応で短縮
    した当初の挙動を維持)。
  - 作成から10分〜24時間: 30分・1時間・2時間・4時間・6時間・12時間・
    24時間の各経過時点で1回だけ確認する(`_CHECKPOINTS_MIN`)。
  - 作成から24時間を超えた行: 経過時間ベースの間隔をやめ、1晩1回・
    深夜のアクセスが少ない時間帯(JST 3:30〜4:00)にまとめて確認する
    (2026-09-08ユーザー指示「負荷分散」。各行の作成時刻に関わらず同じ
    時間帯に集約するため、日中にバラバラと無駄な問い合わせが発生しない)。
  - 作成から7日(元々の仕様どおり・2026-09-08ユーザー確認で維持)を
    過ぎたら、その夜の確認を最後としてタイムアウト扱いにし
    (status='EXPIRED')、以後は`status NOT IN (...)`の条件で対象から
    外れ二度と問い合わせない。

  ⚠️ `paypay_payments.created_at`/`updated_at`はSQLiteの`datetime('now')`
  (=UTC)で記録されている。アプリコンテナ内にタイムゾーン情報が無く
  (`datetime('now','localtime')`を試してもUTCのまま・2026-09-08実機確認)、
  VPSホストのタイムゾーン(Asia/Tokyo)とは無関係なため、夜間バッチの
  時刻判定は`_NIGHT_START_UTC`/`_NIGHT_END_UTC`(UTC 18:30〜19:00 =
  JST 3:30〜4:00)を直接比較する。安易にJSTだと思って時刻を変更しない
  こと。

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
from datetime import datetime
from datetime import time as dt_time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import log  # noqa: E402
from app.database import db  # noqa: E402
from app.services import paypay  # noqa: E402

_DT_FMT = "%Y-%m-%d %H:%M:%S"

# 作成から10分未満は常に確認対象(毎回のcronで確認)。
_FAST_STAGE_MAX_MIN = 10.0
# 10分〜24時間の間の確認チェックポイント(分・2026-09-08ユーザー指示)。
_CHECKPOINTS_MIN = (30, 60, 120, 240, 360, 720, 1440)
# 24時間経過後の夜間バッチ枠(UTC。JST 3:30〜4:00 = UTC 18:30〜19:00)。
_NIGHT_START_UTC = dt_time(18, 30)
_NIGHT_END_UTC = dt_time(19, 0)
# タイムアウト: 作成から7日(元の仕様どおり・2026-09-08ユーザー確認)。
_TIMEOUT_MIN = 7 * 24 * 60


def _parse(s: str) -> datetime:
    return datetime.strptime(s, _DT_FMT)


def _minutes_since(created_at: str, at: str) -> float:
    return (_parse(at) - _parse(created_at)).total_seconds() / 60.0


def _stage(elapsed_min: float) -> int:
    """経過時間(分)の時点で「到達済みの最後のチェックポイント(分)」を返す。
    まだどのチェックポイントにも到達していなければ-1。"""
    reached = [cp for cp in _CHECKPOINTS_MIN if cp <= elapsed_min]
    return reached[-1] if reached else -1


def _in_night_window(now: str) -> bool:
    return _NIGHT_START_UTC <= _parse(now).time() < _NIGHT_END_UTC


def _due_for_check(created_at: str, updated_at: str, now: str) -> bool:
    """今回の実行でこの行をPayPayに問い合わせるべきか判定する
    (バックオフ方式・モジュールdocstring参照)。"""
    since_now = _minutes_since(created_at, now)
    if since_now < _FAST_STAGE_MAX_MIN:
        return True
    if since_now <= _CHECKPOINTS_MIN[-1]:
        since_last = _minutes_since(created_at, updated_at)
        return _stage(since_now) > _stage(since_last)
    # 24時間超: 深夜バッチ枠内、かつ今日(UTC日付)まだ確認していなければ
    # 確認する(1晩1回・負荷分散)。
    return _in_night_window(now) and updated_at[:10] != now[:10]


def main() -> int:
    # 本番モードでない間はサンドボックスのテスト決済(管理者の動作確認用)
    # がここでpt付与されてしまう恐れがあるため、常にスキップする
    # (Opusレビュー指摘・2026-09-01。公開フラグ自体はこのcronの安全装置
    # ではなく、あくまで一般ユーザーへの導線公開/非公開の切替なので
    # 別途チェックしない)。
    if not paypay.is_production():
        print("PAYPAY_PRODUCTION_MODE=false のためスキップしました。")
        return 0
    checked = credited = timed_out = errored = 0
    with db() as conn:
        now = conn.execute("SELECT datetime('now')").fetchone()[0]
        # CANCELED/EXPIREDになった行を除外し忘れると、同じ結論(未払いの
        # まま)を無期限に問い合わせ続けてしまう(2026-09-07・Fable監査
        # 指摘)。作成からの年齢による上限はここでは設けず、7日超過は
        # 下のタイムアウト処理でEXPIREDにして自然に対象から外す。
        rows = conn.execute(
            "SELECT * FROM paypay_payments WHERE credited_at IS NULL "
            "AND status NOT IN ('FAILED', 'CANCELED', 'EXPIRED') "
            "AND created_at <= datetime('now', '-1 minutes') "
            "ORDER BY created_at"
        ).fetchall()
    for row in rows:
        mpid = row["merchant_payment_id"]
        created_at = row["created_at"]
        updated_at = row["updated_at"] or created_at
        if not _due_for_check(created_at, updated_at, now):
            continue
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
            if not did_credit and _minutes_since(created_at, now) >= (
                    _TIMEOUT_MIN):
                conn.execute(
                    "UPDATE paypay_payments SET status = 'EXPIRED', "
                    "updated_at = datetime('now') "
                    "WHERE merchant_payment_id = ? AND credited_at IS NULL",
                    (mpid,),
                )
                conn.commit()
                timed_out += 1
                log.info(
                    "reconcile_paypay_payments: timed out (7days over) "
                    "uid=%s mpid=%s", row["user_id"], mpid)
        if did_credit:
            credited += 1
            log.info(
                "reconcile_paypay_payments: credited uid=%s mpid=%s "
                "amount=%s", row["user_id"], mpid, row["amount_jpy"])
    print(
        f"確認 {checked} 件 / 新規付与 {credited} 件 / "
        f"タイムアウト {timed_out} 件 / 失敗 {errored} 件")
    return 0


if __name__ == "__main__":
    sys.exit(main())
