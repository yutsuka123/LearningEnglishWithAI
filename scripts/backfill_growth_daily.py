"""日次スナップショット(growth_daily)の過去分バックフィル（2026-09-20・
計測設計フェーズ2 3-F）。

logsに残っている全期間(landing_visitsは2026-08-11〜・usage_eventsは
2026-08-17〜)を日次(JST暦日)に集計して`logs.growth_daily`/
`growth_cohort_daily`へ入れる。**冪等**: 何度実行しても同じデータなら
同じ結果(1日分をまるごと入れ替える)。既存テーブルの行は変更しない。

- 対象は「最古の生ログ日〜昨日」(今日は途中なので含めない)。
- 生ログ(usage_events)が保持期間(90日)から外れた日は、既存の行を
  守るため集計しない(欠けた生ログで再集計すると0で上書きしてしまう)。
  したがって**pruneが古い行を消し始める前(=今のうち)に1回流す**こと。
  日次のcron(prune_usage_events.pyが呼ぶsnapshot)も未保存の日を自動で
  埋めるので、流し忘れても保持期間内の分は補完される。
- 集計の定義・除外ルール(自分・ボットを除く)は
  `app/services/growth_metrics.py`の先頭コメント。

使い方(VPS上、eigo-appコンテナの中のpython3で実行を想定):
  docker exec eigo-app python3 scripts/backfill_growth_daily.py --dry-run
  docker exec eigo-app python3 scripts/backfill_growth_daily.py
  docker exec eigo-app python3 scripts/backfill_growth_daily.py \
      --from 2026-09-01 --to 2026-09-15
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db, init_db  # noqa: E402
from app.services import growth_metrics  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--from", dest="start", default=None,
                    help="開始日(JST・YYYY-MM-DD)。省略時は最古の生ログ日")
    ap.add_argument("--to", dest="end", default=None,
                    help="終了日(JST・YYYY-MM-DD)。省略時は昨日")
    ap.add_argument("--dry-run", action="store_true",
                    help="集計だけ行い保存しない")
    args = ap.parse_args(argv)
    init_db()
    try:
        with db() as conn:
            res = growth_metrics.run_snapshot(
                conn, args.start, args.end, dry_run=args.dry_run)
            if not args.dry_run:
                growth_metrics.write_status(
                    conn, True, {**res, "backfill": True})
    except Exception as e:
        print(f"バックフィルに失敗: {type(e).__name__}: {e}", file=sys.stderr)
        return 1
    mode = "集計のみ(保存なし)" if args.dry_run else "保存"
    print(
        f"growth_daily: {res['days']}日分({res['first']}〜{res['last']})・"
        f"{res['rows']}行を{mode}、cohort {res['cohort_rows']}行")
    if res["skipped_old"]:
        print(f"保持期間(90日)より古く、既存の行を守るため触らなかった日: "
              f"{res['skipped_old']}日")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
