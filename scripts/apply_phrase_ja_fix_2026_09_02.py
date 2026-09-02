"""翻訳品質監査(2026-09-02)で見つかったフレーズ訳の誤り2件を、english
テキスト一致で安全に修正する(idはローカル/本番で一致しない既知の問題が
あるため、id直指定ではなくenglish一致で対象行を特定する)。

対象:
  - "He is an elite runner." の訳が「エリート」の発音解説になっていた
    (翻訳ではなく無関係な豆知識に置き換わっていたバグ)。
  - "My sister works as an office worker at a trading company." の訳が
    「OL」の和製英語解説になっていた(同種のバグ)。

Run:  python scripts/apply_phrase_ja_fix_2026_09_02.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

FIXES = [
    ("He is an elite runner.", "彼はエリートランナーです。"),
    ("My sister works as an office worker at a trading company.",
     "私の姉は商社で事務員として働いています。"),
]


def main() -> int:
    with db() as conn:
        for eng, new_ja in FIXES:
            row = conn.execute(
                "SELECT id, japanese FROM phrases WHERE english = ?", (eng,)
            ).fetchone()
            if not row:
                print(f"  [skip] not found: {eng}")
                continue
            print(f"  id={row['id']}: {row['japanese']!r} -> {new_ja!r}")
            conn.execute(
                "UPDATE phrases SET japanese = ? WHERE id = ?",
                (new_ja, row["id"]),
            )
        conn.commit()
    print("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
