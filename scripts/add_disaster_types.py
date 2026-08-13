# ruff: noqa: E501  (data-heavy seed script)
"""「災害(種類)」ドメインを新設(2026-08-13・ユーザー指示: 語彙拡張ペンディング
中の例外実装)。既存の「災害」は避難所・救援・ボランティア等の対応語彙が
中心で、地震・津波・台風・竜巻・イナゴの害等、災害そのものの名称が手薄
だったため、現象名だけを集めた新ドメインを作る。

下書きJSONは scratchpad/culture_domains/disaster_types.json（配列形式）。

Run:  python scripts/add_disaster_types.py <json_dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "災害(種類)"
FILE = "disaster_types"


def main() -> int:
    if len(sys.argv) < 2:
        print("使い方: python scripts/add_disaster_types.py <json_dir>")
        return 1
    json_dir = Path(sys.argv[1])

    with db() as conn:
        existing_words = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        items = json.loads((json_dir / f"{FILE}.json").read_text(encoding="utf-8"))
        for w in items:
            en = w["english"].strip()
            if en.lower() in existing_words:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, w["japanese"], w.get("pos", "名詞"), w.get("example", ""),
                 DOMAIN, w.get("level", "")),
            )
            existing_words.add(en.lower())
            added += 1
        print(f"{DOMAIN}: 投入完了")
    print(f"words: +{added} (skipped {skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
