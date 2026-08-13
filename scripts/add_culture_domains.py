# ruff: noqa: E501  (data-heavy seed script)
"""地域別文化ドメインを新設(2026-08-13・ユーザー指示: 語彙拡張ペンディング中の
例外実装)。「芸術・文化」大分類の下に日本文化/中国文化/アジア文化/欧州文化/
米国文化/文化(その他の国)の6ドメインを追加する。

料理・祭り・宗教・歴史・美術等の既存ドメインとは重複しない、価値観・社会規範・
慣習に関する語彙を対象とした（各執筆エージェントへの指示で明記済み）。

6地域を並列サブエージェント(Claude, 2026-08-13)で下書きし、本スクリプトで
まとめてローカルDBに投入する。下書きJSONは
scratchpad/culture_domains/{japan,china,asia,europe,usa,other}.json。

Run:  python scripts/add_culture_domains.py <json_dir>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAINS = [
    ("japan", "日本文化"),
    ("china", "中国文化"),
    ("asia", "アジア文化"),
    ("europe", "欧州文化"),
    ("usa", "米国文化"),
    ("other", "文化(その他の国)"),
]


def main() -> int:
    if len(sys.argv) < 2:
        print("使い方: python scripts/add_culture_domains.py <json_dir>")
        return 1
    json_dir = Path(sys.argv[1])

    with db() as conn:
        existing_words = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        existing_phrases = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        w_added = w_skipped = p_added = p_skipped = 0
        for key, domain in DOMAINS:
            data = json.loads((json_dir / f"{key}.json").read_text(encoding="utf-8"))
            for w in data["words"]:
                en = w["english"].strip()
                if en.lower() in existing_words:
                    w_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO words (english, japanese, part_of_speech, "
                    "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                    (en, w["japanese"], w.get("pos", "名詞"), w.get("example", ""),
                     domain, w.get("level", "")),
                )
                existing_words.add(en.lower())
                w_added += 1
            for p in data["phrases"]:
                en = p["english"].strip()
                if en.lower() in existing_phrases:
                    p_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, p["japanese"], domain),
                )
                existing_phrases.add(en.lower())
                p_added += 1
            print(f"{domain}: 投入完了")
    print(f"words: +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
