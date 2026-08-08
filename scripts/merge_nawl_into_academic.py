"""NAWL(New Academic Word List)の名称を含む分野を一般名に統合する。

商用アプリで特定の著作物名(NAWL)をそのまま分野名に出すのは著作権/商標上
避けた方が無難という判断（2026-08-08ユーザー指摘）。単語そのもの(一般的な
学術英単語)は著作物ではないため引き続き収録するが、分野名からは「NAWL」を
外し、既存の「論文用語」分野と統合して「論文・学術」に一本化する。

冪等: 対象分野が既に無ければ何もしない。

使い方:
  python scripts/merge_nawl_into_academic.py
  python scripts/merge_nawl_into_academic.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

OLD_DOMAINS = ["学術英単語(NAWL)", "論文用語"]
NEW_DOMAIN = "論文・学術"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with db() as conn:
        total = 0
        for old in OLD_DOMAINS:
            n = conn.execute(
                "SELECT COUNT(*) FROM words WHERE domain = ?",
                (old,)).fetchone()[0]
            print(f"  {old}: {n}件 → {NEW_DOMAIN}")
            total += n
            if not args.dry_run and n:
                conn.execute(
                    "UPDATE words SET domain = ? WHERE domain = ?",
                    (NEW_DOMAIN, old))
        print(f"合計 {total}件")
    if args.dry_run:
        print("[dry-run] 適用しませんでした。")
    else:
        print("適用しました。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
