# ruff: noqa: E501
"""日本刀・火縄銃・鍛冶の伝統工芸語彙を追加(2026-08-18・ユーザー要望
「日本刀 刀鍵(刀鍛冶) 鉄砲鍛冶 火縄銃 他なども入れる」)。

`歴史`ドメインには既に katana(刀)・samurai(侍) がある。swordsmith(刀鍛冶)・
sword smith・blacksmith は`職業`ドメインに、gunpowder(火薬)は`化学`、
forging(鍛造)は`機械工学`、firearm(銃器)は`軍事`に既に存在するため重複
させない。ここでは日本刀・火縄銃に固有の工芸・部位・歴史語彙を`歴史`
ドメインに追加する(katana/samuraiと同じ場所に統一)。

No AI calls — 直接SQLiteへ投入。既存語との重複はenglish(小文字)で判定して
スキップ。

Run:  python scripts/add_japanese_swords_firearms.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# english, japanese, part_of_speech, example, domain, level
WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("nihonto", "日本刀", "名詞", "A nihonto is prized as much for its craftsmanship as for its sharpness.", "歴史", "650"),
    ("tamahagane", "玉鋼(日本刀の原料となる特殊な鋼)", "名詞", "Tamahagane is smelted from iron sand in a traditional clay furnace.", "歴史", "850"),
    ("folded steel", "折り返し鍛錬(日本刀の鍛造技法)", "名詞", "The blade's folded steel gives it a distinctive wavy grain pattern.", "歴史", "800"),
    ("tsuba", "鍔(刀の柄と刃の間の護拳)", "名詞", "The tsuba was engraved with a family crest.", "歴史", "800"),
    ("scabbard", "鞘(さや)", "名詞", "He drew the sword from its lacquered scabbard.", "歴史", "650"),
    ("hilt", "柄(つか、刀剣の持ち手)", "名詞", "The hilt was wrapped in silk cord for a secure grip.", "歴史", "700"),
    ("gunsmith", "鉄砲鍛冶", "名詞", "A gunsmith in the port town began copying the imported firearm.", "歴史", "700"),
    ("armorer", "武具職人", "名詞", "The armorer repaired the samurai's helmet before battle.", "歴史", "700"),
    ("tanegashima", "種子島(日本に伝来した火縄銃の呼称)", "名詞", "The tanegashima takes its name from the island where firearms first reached Japan.", "歴史", "850"),
    ("matchlock gun", "火縄銃", "名詞", "Soldiers lit the fuse of the matchlock gun before firing.", "歴史", "700"),
    ("musket", "マスケット銃", "名詞", "European muskets were similar in design to the early matchlock gun.", "歴史", "650"),
    ("gun barrel", "銃身", "名詞", "The gun barrel was forged from a single piece of iron.", "歴史", "600"),
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
