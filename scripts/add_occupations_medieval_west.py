# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add MEDIEVAL WESTERN EUROPE occupation vocabulary (騎士・宮廷・教会・娯楽等),
authored by Claude (2026-08-06・ユーザー要望: 中世ヨーロッパ職業語彙の追加).

既存の domain='職業' には blacksmith, cooper, tanner, thatcher, wheelwright,
journeyman, apprenticeship, tailor, cobbler, stonemason, glassblower,
candlemaker, bricklayer, roofer, scaffolder, miller (occupation) など、
中世ヨーロッパの「職人(手工業)」系の語がすでに存在する。

このスクリプトはそれとは異なる切り口 — 騎士・宮廷・教会・娯楽・その他の
専門職 — の職業語を追加する:

- 騎士・宮廷: knight, squire, page, lord, herald, man-at-arms, mercenary,
  chamberlain, steward, guild master
- 教会: abbot, abbess, friar, nun, bishop, archbishop, pardoner
- 娯楽・芸能: court jester, minstrel, troubadour
- 専門職・その他: alchemist, apothecary, moneylender, usurer, town crier,
  executioner, watchman, falconer, jailer, scribe, illuminator, midwife,
  astrologer, peddler, siege engineer

domain は既存の中世職人語彙と揃えて '職業' に統一。
level は ["300-","300","350","400","450","500","550","600","650","700",
"750","800","850","900","950","990","990+"] のスケールに沿って付与しており、
比較的よく知られた語(knight, lord, nunなど)は450〜600、専門的・希少な語
(falconer, illuminator, pardoner, siege engineerなど)は750〜950とした。

事前に既存DB(words ~7000件)を全件チェックし、monk / physician / pilgrim /
vassal / merchant はすでに他domain(宗教・医療・歴史等)に存在することを
確認済みのため、このリストから除外している。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_occupations_medieval_west.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("knight", "騎士", "名詞", "The knight knelt before the king and swore his loyalty.", "職業", "450"),
    ("squire", "騎士見習い(従者)", "名詞", "As a squire, he cleaned his master's armor and prepared his horse for battle.", "職業", "700"),
    ("page", "小姓(見習いの少年)", "名詞", "The young page carried messages between the lord and his knights.", "職業", "650"),
    ("lord", "領主", "名詞", "Every peasant in the village owed labor and taxes to the local lord.", "職業", "450"),
    ("herald", "紋章官(伝令使)", "名詞", "The herald rode ahead to announce the king's arrival at the castle gates.", "職業", "800"),
    ("court jester", "道化師", "名詞", "The court jester juggled and told jokes to amuse the royal family.", "職業", "700"),
    ("minstrel", "吟遊詩人", "名詞", "A traveling minstrel sang ballads of love and war in the great hall.", "職業", "750"),
    ("troubadour", "吟遊詩人(中世フランス南部の)", "名詞", "The troubadour composed poems of courtly love for the noblewoman.", "職業", "850"),
    ("abbot", "修道院長(男子修道院の)", "名詞", "The abbot governed the monastery and its lands with strict discipline.", "職業", "800"),
    ("abbess", "女子修道院長", "名詞", "The abbess oversaw the daily prayers and chores of the convent.", "職業", "850"),
    ("friar", "托鉢修道士", "名詞", "The friar begged for alms and preached in the streets of the town.", "職業", "800"),
    ("nun", "修道女", "名詞", "The nun spent her days in prayer, copying manuscripts, and caring for the sick.", "職業", "550"),
    ("bishop", "司教", "名詞", "The bishop presided over the cathedral and advised the king on church matters.", "職業", "600"),
    ("archbishop", "大司教", "名詞", "The archbishop crowned the new king in a grand ceremony.", "職業", "800"),
    ("alchemist", "錬金術師", "名詞", "The alchemist spent years trying to turn lead into gold.", "職業", "700"),
    ("apothecary", "薬種商(薬屋)", "名詞", "The apothecary mixed herbs and potions to treat the villagers' ailments.", "職業", "800"),
    ("moneylender", "金貸し", "名詞", "Merchants often borrowed from a moneylender to finance their trading voyages.", "職業", "700"),
    ("usurer", "高利貸し", "名詞", "The usurer was despised in town for charging such high interest on loans.", "職業", "900"),
    ("town crier", "触れ役(布告人)", "名詞", "The town crier stood in the square, shouting the latest royal proclamation.", "職業", "800"),
    ("executioner", "処刑人", "名詞", "The executioner wore a hood to hide his identity from the crowd.", "職業", "700"),
    ("watchman", "夜警", "名詞", "The watchman patrolled the city walls through the night, calling out the hours.", "職業", "650"),
    ("falconer", "鷹匠", "名詞", "The falconer trained hawks to hunt small game for the noble household.", "職業", "850"),
    ("jailer", "牢番(獄吏)", "名詞", "The jailer kept the keys to every cell in the castle dungeon.", "職業", "750"),
    ("scribe", "写字生(書記)", "名詞", "The scribe copied the manuscript by candlelight, letter by letter.", "職業", "650"),
    ("illuminator", "装飾写本画家", "名詞", "The illuminator decorated the manuscript's borders with gold leaf and tiny paintings.", "職業", "900"),
    ("chamberlain", "侍従(家令)", "名詞", "The chamberlain managed the lord's household and personal finances.", "職業", "850"),
    ("steward", "家令(執事)", "名詞", "The steward ran the estate while the lord was away at war.", "職業", "600"),
    ("man-at-arms", "武装従者(下級騎士)", "名詞", "A dozen men-at-arms guarded the castle gate day and night.", "職業", "800"),
    ("mercenary", "傭兵", "名詞", "The mercenary fought for whichever lord paid him best.", "職業", "700"),
    ("pardoner", "免罪符売り", "名詞", "The pardoner sold indulgences that promised to shorten one's time in purgatory.", "職業", "950"),
    ("midwife", "産婆", "名詞", "The midwife was called to the manor as soon as the lady went into labor.", "職業", "600"),
    ("astrologer", "占星術師", "名詞", "The king consulted his astrologer before making any major decision.", "職業", "750"),
    ("peddler", "行商人", "名詞", "The peddler traveled from village to village selling needles, ribbons, and pots.", "職業", "600"),
    ("guild master", "ギルドの親方(組合長)", "名詞", "To become a guild master, a craftsman first had to work for years as a journeyman.", "職業", "750"),
    ("siege engineer", "攻城技師", "名詞", "The siege engineer designed catapults and trebuchets to break through castle walls.", "職業", "900"),
]


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        w_added = w_skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
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

    print(f"words:   +{w_added} (skipped {w_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
