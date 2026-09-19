"""日次スナップショット(成長ログ)の自動更新（cron用・2026-09-20・計測設計
フェーズ2 3-F）。

前日までの未保存の日と直近数日(既定7日)を、人間(自分・ボットを除く)の
日次集計として`logs.growth_daily`/`growth_cohort_daily`に**冪等に**保存する
(何度実行しても同じ結果・1日分をまるごと入れ替える)。usage_eventsを
削除する`scripts/prune_usage_events.py`が実行の**前**に自動で呼ぶため、
通常は単独でcronに登録する必要はない(単独実行は手動の確認・再集計用)。
集計の定義・除外ルールは`app/services/growth_metrics.py`の先頭コメント。

生ログが保持期間(90日)から外れた日は既存の行に触らない(欠けた生ログで
再集計して0で上書きするのを防ぐ)。過去の全期間を最初に埋める場合は
`scripts/backfill_growth_daily.py`を使う。

使い方(VPS上、eigo-appコンテナの中のpython3で実行を想定):
  docker exec eigo-app python3 scripts/snapshot_growth_daily.py
  docker exec eigo-app python3 scripts/snapshot_growth_daily.py --dry-run
終了コード: 0=成功 / 1=失敗(失敗は管理画面の日次スナップショット欄にも
「最終実行: 失敗」と出る)。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import init_db  # noqa: E402
from app.services import growth_metrics  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--lookback", type=int, default=7,
                    help="未保存の日に加えて再集計する直近の日数(既定7)")
    ap.add_argument("--dry-run", action="store_true",
                    help="集計だけ行い保存しない")
    args = ap.parse_args(argv)
    init_db()
    try:
        res = growth_metrics.run_daily(
            lookback=max(1, args.lookback), dry_run=args.dry_run)
    except Exception as e:
        print(f"日次スナップショットに失敗: {type(e).__name__}: {e}",
              file=sys.stderr)
        return 1
    print(
        f"growth_daily: {res['days']}日分({res['first']}〜{res['last']})・"
        f"{res['rows']}行を{'集計(保存なし)' if args.dry_run else '保存'}、"
        f"cohort {res['cohort_rows']}行、"
        f"保持期間外で触らなかった日 {res['skipped_old']}日")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
