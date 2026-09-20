"""usage_events(画面表示/再生/クリックのイベントログ)の古い行を削除する
（cron用・2026-08-19）。

ボタン押下等の操作ログは90日保持という方針（2026-09-20オーナー決定・
当初は1ヶ月だったが、コホート/継続率など成長分析のために延長。プライバシー
ポリシーの「閲覧・操作の記録: 約90日」と一致させること。ログイン履歴・
AI利用ログ・残高変更履歴等は無期限のまま・対象外）のため、このテーブル
だけ定期的に間引く。100ユーザー規模だと無期限では年間数百MB〜GB級に
育ちうるため、放置しないための保守。

**2026-09-20: 削除の前に日次スナップショット(growth_daily)を更新する。**
生ログは消えても日次の集計値(自分・ボットを除く人数・件数)は
`logs.growth_daily`/`growth_cohort_daily`に恒久保存され、過去の推移が
変わらない(scripts/snapshot_growth_daily.py・app/services/growth_metrics.py)。
**スナップショットが失敗した/未保存の日が残っている場合は削除しない**
(終了コード1)。理由: 削除は取り返しがつかないが、pruneが数日遅れても
実害はほぼ無い(90日保持の約束に対し数日のずれ・データ量は年間数MB〜)
ため、集計の前に生ログを消して過去の推移を失う事故の方を避ける。
snapshot自体の不具合が長引いて容量が心配な緊急時だけ`--force`で
スナップショットの結果に関わらず削除できる。

**2026-09-21: 同じ実行の中で、取得から360日を過ぎたIPアドレスを復元できない
変換値(HMAC)へ置き換える**(`app/services/ip_retention.py`・プライバシー
ポリシー§9「IPアドレス・訪問/ログイン/エラーの記録: 約360日」)。行は消さず
IP列だけ置き換える(ログイン履歴等の行は残り、生のIPだけが期限で消える)。
usage_eventsの削除・スナップショットの成否とは独立に、毎回最初に行う。

使い方(VPS上、eigo-appコンテナの中のpython3で実行を想定):
  docker exec eigo-app python3 scripts/prune_usage_events.py
  docker exec eigo-app python3 scripts/prune_usage_events.py --force  # 緊急時のみ
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db, init_db  # noqa: E402
from app.services import growth_metrics, ip_retention  # noqa: E402

# 90日保持の方針(プライバシーポリシー記載と一致・2026-09-20に35日から変更)。
# cronは毎日03:45に実行されるため、余裕を足さず90日ちょうどでよい。
# 日次スナップショット側の「生ログが完全に残る日」の判定
# (growth_metrics.USAGE_KEEP_DAYS)と必ず同じ値にすること。
_KEEP_DAYS = growth_metrics.USAGE_KEEP_DAYS


def main(argv: list[str] | None = None,
         now: datetime | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--force", action="store_true",
                    help="日次スナップショットの失敗・未保存でも削除する"
                         "(緊急時のみ)")
    args = ap.parse_args(argv)
    now = now or datetime.now(timezone.utc)
    init_db()

    # 0) 取得から360日を過ぎたIPアドレスを復元できない変換値へ置き換える
    # (プライバシーポリシー§9・2026-09-21)。usage_eventsの削除やスナップ
    # ショットの成否とは独立に行い、失敗しても以降の処理は続ける。
    try:
        with db() as conn:
            res_ip = ip_retention.anonymize_old_ips(conn, now=now)
        detail = "、".join(f"{k}:{v}" for k, v in res_ip.items() if v) or "対象なし"
        print(f"IP保持期限({ip_retention.IP_KEEP_DAYS}日超): {detail}")
    except ip_retention.NoKeyError as e:
        print(f"IP保持期限の処理をスキップ(変換の鍵が取れません: {e})。"
              "環境変数SESSION_SECRETのあるコンテナ内で実行してください。",
              file=sys.stderr)
    except Exception as e:
        print(f"IP保持期限の処理に失敗: {type(e).__name__}: {e}",
              file=sys.stderr)

    # 1) 削除の前に日次スナップショットを更新する。失敗したら削除しない。
    try:
        res = growth_metrics.run_daily(now=now)
        print(f"growth_daily: {res['days']}日分を更新"
              f"（{res['first']}〜{res['last']}）")
    except Exception as e:
        print(f"日次スナップショットに失敗: {type(e).__name__}: {e}",
              file=sys.stderr)
        if not args.force:
            print("生ログを守るためusage_eventsの削除を中止します"
                  "（--forceで強行可）。", file=sys.stderr)
            return 1
        print("--force指定のため削除を続行します。", file=sys.stderr)

    cutoff = (now - timedelta(days=_KEEP_DAYS)).strftime("%Y-%m-%d %H:%M:%S")
    # 2) これから消す行の日がすべてスナップショット済みか確認する。
    with db() as conn:
        missing = growth_metrics.unsnapshotted_usage_days(conn, cutoff)
    if missing and not args.force:
        print(f"スナップショット未保存の日({len(missing)}日・"
              f"{missing[0]}〜{missing[-1]})の生ログが削除対象に含まれるため、"
              "usage_eventsの削除を中止します(--forceで強行可)。",
              file=sys.stderr)
        return 1

    with db() as conn:
        before = conn.execute(
            "SELECT COUNT(*) FROM usage_events").fetchone()[0]
        conn.execute(
            "DELETE FROM usage_events WHERE created_at < ?", (cutoff,))
        after = conn.execute("SELECT COUNT(*) FROM usage_events").fetchone()[0]
    # 注意: VACUUMはしない。DB全体(数GB・音声等含む)をロックしながら
    # コピーする重い操作で、削除した行の分だけでは実効果も薄いため
    # (2026-08-19)。空いたページはSQLiteが同テーブルへの次回書き込みで
    # 自動的に再利用する。
    print(f"usage_events: {before}件 -> {after}件（{before - after}件削除）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
