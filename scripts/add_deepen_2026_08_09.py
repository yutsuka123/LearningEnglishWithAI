# ruff: noqa: E501
"""既存20分野の「深掘り」語彙・フレーズ拡充(2026-08-09)。

ユーザー要望: 「すでにある専門用語他各分野の深掘り拡充は専門家や教授、
趣味等の初心者、マニアックなものも知りたいディープなマニアの気持ちに
なって知りたい単語フレーズの拡充を図ってください。最大+2000単語
最大+1500フレーズ」。

化学/物理/医療/法律/天文/建築・建物/半導体/品質工学/車載組込み開発/
経済学/生化学/航空・宇宙/統計学/音楽/美術・博物館/哲学/宗教/料理/和食/
軍事の20分野について、並列サブエージェント20体(Claude、API原価¥0)に
「専門家・教授/趣味の初心者/ディープなマニア」の3視点で新規語彙・
フレーズを生成させた(既存語との重複を避けるため各分野の既存語リストを
事前に渡した)。生成結果は`data/deepen_2026_08_09/raw_NN_domain.txt`に
`###WORDS`/`###PHRASES`形式で保存済み。本スクリプトはそれを読み込み
DBに投入する（第1弾。最大+2000語/+1500フレーズの一部）。

Run:  python scripts/add_deepen_2026_08_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "deepen_2026_08_09"

# (raw file, word domain, phrase scene)
FILES: list[tuple[str, str, str]] = [
    ("raw_01_化学.txt", "化学", "化学の英語"),
    ("raw_02_物理.txt", "物理", "物理学の英語"),
    ("raw_03_医療.txt", "医療", "医学の英語"),
    ("raw_04_法律.txt", "法律", "法律の英語"),
    ("raw_05_天文.txt", "天文", "天文学の英語"),
    ("raw_06_建築_建物.txt", "建築・建物", "建築の英語"),
    ("raw_07_半導体.txt", "半導体", "半導体の英語"),
    ("raw_08_品質工学.txt", "品質工学", "品質工学の英語"),
    ("raw_09_車載組込み開発.txt", "車載組込み開発", "車載組込み開発の英語"),
    ("raw_10_経済学.txt", "経済学", "経済学の英語"),
    ("raw_11_生化学.txt", "生化学", "生化学の英語"),
    ("raw_12_航空_宇宙.txt", "航空・宇宙", "航空宇宙の英語"),
    ("raw_13_統計学.txt", "統計学", "統計学の英語"),
    ("raw_14_音楽.txt", "音楽", "音楽の演奏"),
    ("raw_15_美術_博物館.txt", "美術・博物館", "美術館・アートの英語"),
    ("raw_16_哲学.txt", "哲学", "哲学の英語"),
    ("raw_17_宗教.txt", "宗教", "宗教の英語"),
    ("raw_18_料理.txt", "料理", "料理の英語"),
    ("raw_19_和食.txt", "和食", "和食"),
    ("raw_20_軍事.txt", "軍事", "軍事の英語"),
]


def parse_file(path: Path) -> tuple[list[tuple[str, str, str, str, str]], list[tuple[str, str]]]:
    text = path.read_text(encoding="utf-8")
    words_part, _, rest = text.partition("###WORDS")
    words_text, _, phrases_text = rest.partition("###PHRASES")

    words: list[tuple[str, str, str, str, str]] = []
    for line in words_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        fields = line.split("\t")
        if len(fields) != 5:
            print(f"  [WARN] {path.name}: skipping malformed word line: {line!r}")
            continue
        en, ja, pos, ex, level = (f.strip() for f in fields)
        words.append((en, ja, pos, ex, level))

    phrases: list[tuple[str, str]] = []
    for line in phrases_text.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        fields = line.split("\t")
        if len(fields) != 2:
            print(f"  [WARN] {path.name}: skipping malformed phrase line: {line!r}")
            continue
        en, ja = (f.strip() for f in fields)
        phrases.append((en, ja))

    return words, phrases


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }

        total_w_added = total_w_skipped = 0
        total_ph_added = total_ph_skipped = 0

        for fname, domain, scene in FILES:
            path = DATA_DIR / fname
            words, phrases = parse_file(path)

            w_added = w_skipped = 0
            for en, ja, pos, ex, level in words:
                if en.lower() in w_existing:
                    w_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO words (english, japanese, part_of_speech, "
                    "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                    (en, ja, pos, ex, domain, level),
                )
                w_existing.add(en.lower())
                w_added += 1

            ph_added = ph_skipped = 0
            for en, ja in phrases:
                if en.lower() in ph_existing:
                    ph_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                ph_existing.add(en.lower())
                ph_added += 1

            print(f"{domain}: words +{w_added} (skip {w_skipped}), "
                  f"phrases +{ph_added} (skip {ph_skipped})")
            total_w_added += w_added
            total_w_skipped += w_skipped
            total_ph_added += ph_added
            total_ph_skipped += ph_skipped

    print(f"\nTOTAL words: +{total_w_added} (skipped {total_w_skipped})")
    print(f"TOTAL phrases: +{total_ph_added} (skipped {total_ph_skipped})")
    with db() as conn:
        print("DB totals -> words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
              "phrases:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
