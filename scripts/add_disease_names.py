# ruff: noqa: E501  (data-heavy seed script)
"""「医療(病名)」ドメインを新設(2026-08-13・ユーザー指示: 語彙拡張ペンディング
中の例外実装)。既存の「医療(症状)」は症状・治療語彙が中心で体系的な病名一覧
ではなかったため、風邪からがん・成人病・重大感染症・精神疾患まで、純粋な
病名だけを集めた新ドメインを作る（怪我(捻挫・骨折等)は対象外）。

6カテゴリ(一般的な風邪等/がん/成人病・慢性疾患/重大感染症/精神・皮膚疾患/
その他マイナー疾患)を並列サブエージェント(Claude, 2026-08-13)で下書きし、
本スクリプトでまとめてローカルDBに投入する。下書きJSONは
scratchpad/culture_domains/disease_{common,cancer,chronic,infectious,
mental_skin,other}.json（配列形式）。

Run:  python scripts/add_disease_names.py <json_dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "医療(病名)"
FILES = [
    "disease_common", "disease_cancer", "disease_chronic",
    "disease_infectious", "disease_mental_skin", "disease_other",
]


def main() -> int:
    if len(sys.argv) < 2:
        print("使い方: python scripts/add_disease_names.py <json_dir>")
        return 1
    json_dir = Path(sys.argv[1])

    with db() as conn:
        existing_words = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for key in FILES:
            items = json.loads((json_dir / f"{key}.json").read_text(encoding="utf-8"))
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
            print(f"{key}: 投入完了")
    print(f"words: +{added} (skipped {skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
