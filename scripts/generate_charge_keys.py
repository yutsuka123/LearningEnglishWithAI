"""チャージキー生成CLI（BASE等での手売り用・§商用化）。

使い方:
  python scripts/generate_charge_keys.py <pattern> <amount_jpy> [--count N]

例（正式な価格ラインナップは ¥800(800pt) / ¥8,000(8,800pt) の2種類）:
  python scripts/generate_charge_keys.py 5J8Q 800  --count 5   # ¥800 -> 800pt
  python scripts/generate_charge_keys.py 5K8B 8800 --count 5   # ¥8,000 -> 8,800pt

pattern は4桁の固定値（アルファベット: 23456789ABCDEFGHJKMNPQRSTUVWXYZ。
0/O/1/I/L は使えない）。額面/バッチ等の意味を自分で割り当てて管理する
（対応表は手元のメモで十分・1万パターンまで使える）。

生成された平文キー（全16桁）は標準出力にのみ表示される。DBにはシークレット
部分のハッシュしか残らないため、この出力をその場でコピーして買い手に送付し、
ターミナルの履歴等に残さないこと。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db, init_db  # noqa: E402
from app.services import charge_keys  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("pattern", help="4桁の固定値(パターンコード)")
    ap.add_argument("amount_jpy", type=int, help="償還時に付与する額(pt)")
    ap.add_argument("--count", type=int, default=1, help="生成する個数")
    args = ap.parse_args()

    init_db()
    try:
        with db() as conn:
            keys = [
                charge_keys.generate_key(
                    conn, pattern=args.pattern, amount_jpy=args.amount_jpy)
                for _ in range(args.count)
            ]
    except ValueError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1

    for k in keys:
        print(k)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
