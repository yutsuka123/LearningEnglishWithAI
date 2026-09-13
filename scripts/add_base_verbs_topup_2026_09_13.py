# ruff: noqa: E501
"""基礎動詞(take/get/make)追加(2026-09-13・authored by Claude、backlog B25)。

ユーザー提起「take/get/run/make のような極端に多義的な基礎動詞」のうち、
DB確認の結果 take・get・make は見出し語として存在しなかった(句動詞
take off/get over/make up 等や takeaway/intake のような派生語はあるが、
基本動詞そのものは無い)ため、この3語を新規追加する。run は既存行
(id=15425)があるため、この投入スクリプトには含めない
(detailの充実はscripts/data/base_verbs_topup_details_2026_09_13.jsonの
run分をid指定で別途反映する)。

detail(多義の意味一覧・例文・派生語など)は
scripts/data/base_verbs_topup_details_2026_09_13.json を
scripts/import_details.py で別途投入すること。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_base_verbs_topup_2026_09_13.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("take", "取る、持っていく、(乗り物に)乗る", "動詞", "She took a book from the shelf and started reading.", "基礎語彙", "350"),
    ("get", "得る、着く、〜になる", "動詞", "I need to get some milk from the store on my way home.", "基礎語彙", "350"),
    ("make", "作る、〜させる、稼ぐ", "動詞", "She made a beautiful cake for her friend's birthday.", "基礎語彙", "350"),
]


def main() -> None:
    with db() as conn:
        existing = set()
        for r in conn.execute("SELECT english FROM words").fetchall():
            existing.add(r["english"].lower())
        inserted = 0
        skipped = 0
        for english, japanese, pos, example, domain, level in WORDS:
            if english.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (english, japanese, pos, example, domain, level),
            )
            existing.add(english.lower())
            inserted += 1
        print("inserted=" + str(inserted) + " skipped=" + str(skipped))


if __name__ == "__main__":
    main()
