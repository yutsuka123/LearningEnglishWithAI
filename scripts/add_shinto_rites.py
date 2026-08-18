# ruff: noqa: E501
"""「宗教（日本）」に神事(Shinto ritual/ceremonial rites)語彙を追加(2026-08-18)。

ユーザー要望:「宗教（日本） 神事関係もお願いします 流鏑馬はここにはいる
のか？？」— 流鏑馬(yabusame、神事として神社で奉納される騎射)はまさに
神事の代表例のため、ここ(宗教（日本）)に収録する。人生儀礼(お宮参り・
七五三)、清めの儀式(禊・祓い)、地鎮祭・神前式等の代表的な神事語彙を
まとめて追加。既存の「mikoshi」(お祭りドメイン)・「ritual」(宗教ドメイン、
一般語)とは重複させない。

No AI calls — 直接SQLiteへ投入。既存語との重複はenglish(小文字)で判定して
スキップ。

Run:  python scripts/add_shinto_rites.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# english, japanese, part_of_speech, example, domain, level
WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("Shinto ritual", "神事", "名詞", "The shrine holds a Shinto ritual at the start of every month.", "宗教（日本）", "500"),
    ("yabusame", "流鏑馬(神事として神社に奉納される騎射)", "名詞", "Archers on horseback perform yabusame to pray for a good harvest.", "宗教（日本）", "800"),
    ("ceremonial archery", "儀式としての弓術", "名詞", "Ceremonial archery has been offered at shrines for centuries.", "宗教（日本）", "700"),
    ("purification ceremony", "清めの儀式", "名詞", "Priests perform a purification ceremony before the festival begins.", "宗教（日本）", "550"),
    ("misogi", "禊(水を浴びて行う清め)", "名詞", "Practitioners stand under a waterfall to perform misogi.", "宗教（日本）", "750"),
    ("harae", "祓い(お祓い)", "名詞", "A priest waves a wand over the car in a harae to ward off accidents.", "宗教（日本）", "700"),
    ("harai-gushi", "祓串(お祓いに使う道具)", "名詞", "The priest swept the harai-gushi from side to side over the worshippers.", "宗教（日本）", "850"),
    ("gohei", "御幣(祓いに用いる紙垂のついた幣)", "名詞", "White paper strips hang from the gohei used in the ceremony.", "宗教（日本）", "800"),
    ("jichinsai", "地鎮祭(工事の前に土地を清める儀式)", "名詞", "A jichinsai was held before construction began on the new house.", "宗教（日本）", "750"),
    ("Shinto wedding", "神前式", "名詞", "They chose a traditional Shinto wedding at a small local shrine.", "宗教（日本）", "600"),
    ("Shinto funeral rite", "神葬祭", "名詞", "A Shinto funeral rite differs from the more common Buddhist funeral in Japan.", "宗教（日本）", "750"),
    ("omiyamairi", "お宮参り(赤ちゃんの初めての神社参り)", "名詞", "Parents bring their newborn for omiyamairi about a month after birth.", "宗教（日本）", "750"),
    ("Shichi-Go-San", "七五三(子供の成長を祝う神事)", "名詞", "Children dressed in kimono visit the shrine for Shichi-Go-San in November.", "宗教（日本）", "650"),
    ("rite of passage", "通過儀礼", "名詞", "Shichi-Go-San is a rite of passage marking a child's growth.", "宗教（日本）", "600"),
    ("purification salt", "清めの塩・盛り塩", "名詞", "A small pile of purification salt sits by the entrance to keep away bad luck.", "宗教（日本）", "650"),
    ("sacred fire", "神事で使われる神聖な火", "名詞", "A sacred fire is lit to purify the ritual space before the ceremony.", "宗教（日本）", "650"),
    ("divine offering", "神饌(神への食物の供物)", "名詞", "Rice, sake, and fish are arranged as a divine offering on the altar.", "宗教（日本）", "750"),
    ("harvest thanksgiving rite", "新嘗祭のような収穫感謝の神事", "名詞", "The harvest thanksgiving rite gives thanks to the kami for the year's crops.", "宗教（日本）", "850"),
]


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing:
                skipped += 1
                print(f"  skip (exists): {en}")
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")
    with db() as conn:
        print("宗教（日本） total:", conn.execute(
            "SELECT COUNT(*) FROM words WHERE domain='宗教（日本）'"
        ).fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
