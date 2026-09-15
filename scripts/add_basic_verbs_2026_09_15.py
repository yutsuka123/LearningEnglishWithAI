"""最頻出・多義的な基礎動詞72語の拡充(2026-09-15・6並列エージェントで
authored、本スクリプトで統合投入)。

背景: have/do/go/put/keep等、英語で最も使用頻度の高い基礎動詞がDBに
一切存在せず、take/get/make/run等も「取る、持っていく、(乗り物に)乗る」
のような3語程度の薄いグロスしか無いことが判明した(2026-09-15ユーザー
発見)。新規51語をINSERT、既存21語(基礎語彙ドメインの薄いエントリ)を
UPDATEする。detail列は別途 `import_details.py --force` で投入する
(このスクリプトはwords本体=english/japanese/part_of_speech/example/
domain/levelのみ担当)。

入力: scripts/data/basic_verbs_2026_09_15_g1.json 〜 g6.json
(各12語、{english, is_existing, existing_id, japanese, example, level,
detail} の配列)。

Run: python scripts/add_basic_verbs_2026_09_15.py
"""

from __future__ import annotations

import glob
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "基礎語彙"


def load_all() -> list[dict]:
    items: list[dict] = []
    for f in sorted(glob.glob(
            str(Path(__file__).resolve().parent / "data"
                / "basic_verbs_2026_09_15_g*.json"))):
        items.extend(json.loads(Path(f).read_text(encoding="utf-8")))
    return items


def main() -> None:
    items = load_all()
    print(f"loaded {len(items)} words")
    with db() as conn:
        inserted = updated = skipped = 0
        for it in items:
            english = it["english"].strip()
            japanese = it["japanese"].strip()
            example = it["example"].strip()
            level = int(it["level"])
            if it["is_existing"]:
                eid = int(it["existing_id"])
                row = conn.execute(
                    "SELECT id, english FROM words WHERE id = ?", (eid,),
                ).fetchone()
                if not row or row["english"].strip().lower() != english.lower():
                    print(f"  SKIP (id/english mismatch): {english} "
                          f"expected id={eid} got={dict(row) if row else None}")
                    skipped += 1
                    continue
                conn.execute(
                    "UPDATE words SET japanese = ?, example = ?, level = ? "
                    "WHERE id = ?",
                    (japanese, example, level, eid),
                )
                updated += 1
            else:
                exists = conn.execute(
                    "SELECT 1 FROM words WHERE LOWER(english) = ?",
                    (english.lower(),),
                ).fetchone()
                if exists:
                    print(f"  SKIP (already exists): {english}")
                    skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO words (english, japanese, part_of_speech, "
                    "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                    (english, japanese, "動詞", example, DOMAIN, level),
                )
                inserted += 1
        print(f"inserted={inserted} updated={updated} skipped={skipped}")


if __name__ == "__main__":
    main()
