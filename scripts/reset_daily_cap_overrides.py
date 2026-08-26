"""2026-08-26: 日次AI利用無料枠を100pt(通常)/1000pt(admin)へ統一するため、
既存の個別`daily_cost_cap_usd`(USD建て・為替レート変動で円換算がぶれる)を
クリアし、`app/services/ai.py`の新しい役割別デフォルト
(`_default_daily_cap_usd`)へフォールバックさせる。

`monthly_cost_cap_usd`は意図的に対象外（例: アルファ配布した友人の
月¥500上限はそのまま維持する方針・ユーザーへの確認なく変更しない）。

対象: `daily_cost_cap_usd`が設定されている、email未設定(legacy/招待)
ユーザー全員（is_test問わず）。

使い方:
  python scripts/reset_daily_cap_overrides.py            # 適用
  python scripts/reset_daily_cap_overrides.py --dry-run  # 対象確認のみ
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    with db() as conn:
        rows = conn.execute(
            "SELECT id, username, role, monthly_cost_cap_usd "
            "FROM users WHERE daily_cost_cap_usd IS NOT NULL "
            "AND (email IS NULL OR email = '')"
        ).fetchall()
        print(f"対象 {len(rows)} 件:")
        for r in rows:
            print(f"  id={r['id']} username={r['username']} "
                  f"role={r['role']} "
                  f"monthly_cost_cap_usd={r['monthly_cost_cap_usd']}"
                  f"(変更なし)")
        if args.dry_run:
            print("--dry-run のため変更なし。")
            return
        conn.execute(
            "UPDATE users SET daily_cost_cap_usd = NULL "
            "WHERE daily_cost_cap_usd IS NOT NULL "
            "AND (email IS NULL OR email = '')"
        )
        conn.commit()
        print(f"{len(rows)} 件の daily_cost_cap_usd を NULL に更新しました。")


if __name__ == "__main__":
    main()
