"""usage_events(画面表示/再生/クリックのイベントログ)の古い行を削除する
（cron用・2026-08-19）。

ボタン押下等の操作ログは1ヶ月保持で十分という方針（ログイン履歴・
AI利用ログ・残高変更履歴等は無期限のまま・対象外）のため、このテーブル
だけ定期的に間引く。100ユーザー規模だと無期限では年間数百MB〜GB級に
育ちうるため、放置しないための保守。

使い方(VPS上、eigo-appコンテナの中のpython3で実行を想定):
  docker exec eigo-app python3 scripts/prune_usage_events.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db, init_db  # noqa: E402

# 1ヶ月保持の方針に、cron間隔分の余裕(5日)を足した保持日数。
_KEEP_DAYS = 35


def main() -> int:
    init_db()
    with db() as conn:
        before = conn.execute(
            "SELECT COUNT(*) FROM usage_events").fetchone()[0]
        conn.execute(
            "DELETE FROM usage_events WHERE created_at < "
            "datetime('now', ?)", (f"-{_KEEP_DAYS} days",),
        )
        after = conn.execute("SELECT COUNT(*) FROM usage_events").fetchone()[0]
    # 注意: VACUUMはしない。DB全体(数GB・音声等含む)をロックしながら
    # コピーする重い操作で、削除した行の分だけでは実効果も薄いため
    # (2026-08-19)。空いたページはSQLiteが同テーブルへの次回書き込みで
    # 自動的に再利用する。
    print(f"usage_events: {before}件 -> {after}件（{before - after}件削除）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
