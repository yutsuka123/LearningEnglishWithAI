"""和食シーンのフレーズQA(リリース前チェックリスト2)で見つかった矛盾を修正する。

id 4268「醤油はネタ側かシャリ側か」と id 4275「追加で醤油をつける必要は
ない」が、文脈なしに読むと矛盾して見える(常に醤油をつけるべきか不要かが
ブレる)。実際は id 4275 は「シェフがすでにタレを塗った一部のネタ」限定の
話なので、その前提を明示する文言に修正する(id 4268 の一般的な浸け方の
説明とは矛盾しなくなる)。

冪等: 旧文言のままなら更新・新文言に既に変わっていればスキップする。

使い方:
  python scripts/fix_washoku_soy_sauce_contradiction.py
  python scripts/fix_washoku_soy_sauce_contradiction.py --dry-run
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

PHRASE_ID = 4275
OLD_EN = ("There's no need to add extra soy sauce — the chef has "
          "already seasoned it.")
OLD_JA = "追加で醤油をつける必要はありません。シェフがすでに味付けしています。"
NEW_EN = ("For pieces the chef has already brushed with sauce, "
          "there's no need to add extra soy sauce.")
NEW_JA = ("シェフがすでにタレ(醤油だれ)を塗ってくれている場合、"
          "追加で醤油をつける必要はありません。")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    with db() as conn:
        row = conn.execute(
            "SELECT english, japanese FROM phrases WHERE id = ?",
            (PHRASE_ID,)).fetchone()
        if row is None:
            print(f"[未検出] id={PHRASE_ID} が存在しません")
            return 1
        if row["english"] == NEW_EN and row["japanese"] == NEW_JA:
            print(f"[済み] id={PHRASE_ID} は既に修正済みです")
            return 0
        if row["english"] != OLD_EN or row["japanese"] != OLD_JA:
            print(f"[想定外] id={PHRASE_ID} の内容が既知の新旧どちらとも "
                  f"一致しません。手動確認してください: {dict(row)}")
            return 1
        print(f"  before: {row['english']} | {row['japanese']}")
        print(f"  after : {NEW_EN} | {NEW_JA}")
        if not args.dry_run:
            conn.execute(
                "UPDATE phrases SET english = ?, japanese = ? "
                "WHERE id = ? AND english = ? AND japanese = ?",
                (NEW_EN, NEW_JA, PHRASE_ID, OLD_EN, OLD_JA))
    if args.dry_run:
        print("[dry-run] 適用しませんでした。")
    else:
        print("適用しました。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
