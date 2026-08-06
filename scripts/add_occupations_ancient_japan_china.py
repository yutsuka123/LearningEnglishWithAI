# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""Add ANCIENT JAPAN / ANCIENT CHINA occupation vocabulary, authored by Claude
(2026-08-06・ユーザー要望: 「古代の日本・古代中国に存在した職業を英語で
紹介する語彙を追加してほしい」)。

外国人に日本文化・中国文化を英語で紹介する場面を想定し、古代日本・古代中国に
存在した職業(uji chieftain, court diviner, haniwa maker, court historian,
imperial censor, eunuch, Confucian scholar-official, silk weaver,
oracle bone diviner など)を英単語として追加する。

domain は '職業' に統一。level は
["300-","300","350","400","450","500","550","600","650","700","750","800",
"850","900","950","990","990+"] のスケールに沿って付与しており、専門的な
歴史語彙であることを踏まえ 700〜900 の範囲とした(監察・官僚制度・占術など
より専門性の高い語は 850〜900、比較的一般的な語は 700〜750)。

事実に基づく記述を心がけ、不確かな年代や誇張した表現、特定の実在人物名は
使用していない。例文はいずれも「古代日本」「古代中国」という一般的な
時代設定にとどめ、特定の王朝・世紀を断定する記述は避けた。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_occupations_ancient_japan_china.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("uji chieftain", "氏族長(古代日本の豪族の長)", "名詞", "An uji chieftain led a powerful clan and controlled local land and labor in ancient Japan.", "職業", "850"),
    ("court diviner", "占い師(古代日本の宮廷に仕えた)", "名詞", "A court diviner in ancient Japan interpreted cracks in heated bone to seek guidance from the kami before important decisions.", "職業", "800"),
    ("Shinto priest", "神職(古代の)", "名詞", "A Shinto priest in ancient Japan performed rituals to honor the kami and purify sacred spaces.", "職業", "700"),
    ("haniwa maker", "埴輪職人", "名詞", "A haniwa maker shaped clay figures that were placed around burial mounds in ancient Japan.", "職業", "850"),
    ("rice paddy farmer", "稲作農民(古代の)", "名詞", "A rice paddy farmer in ancient Japan worked the fields that formed the basis of the local economy.", "職業", "700"),
    ("sword smith", "刀鍛冶(古代の)", "名詞", "A sword smith in ancient Japan shaped and tempered iron blades for use in battle and ceremony.", "職業", "800"),
    ("court scribe", "書記官(宮廷の)", "名詞", "A court scribe recorded official documents and correspondence for the ruling court.", "職業", "800"),
    ("provincial governor", "国司(地方官、古代日本の)", "名詞", "A provincial governor was sent from the capital to administer a region in ancient Japan.", "職業", "850"),
    ("shrine maiden", "巫女", "名詞", "A shrine maiden assisted with rituals and dances at a Shinto shrine.", "職業", "700"),
    ("Buddhist monk", "僧侶(仏教の)", "名詞", "A Buddhist monk copied sutras and studied scripture at a temple in ancient Japan.", "職業", "700"),
    ("court lady", "女官(宮廷に仕える女性)", "名詞", "A court lady served the empress and took part in the cultural life of the ancient Japanese court.", "職業", "750"),
    ("weaver", "機織り職人(古代の)", "名詞", "A weaver produced cloth on a hand loom for clothing and tribute in ancient Japan.", "職業", "700"),
    ("potter", "陶工(古代の)", "名詞", "A potter shaped and fired clay vessels used for storing food and grain.", "職業", "700"),
    ("salt maker", "製塩職人(古代の)", "名詞", "A salt maker boiled down seawater to extract salt along the coast of ancient Japan.", "職業", "750"),
    ("court musician", "宮廷楽師", "名詞", "A court musician performed at ceremonies and banquets held by the ruling nobility.", "職業", "750"),
    ("imperial envoy", "遣使(朝廷が派遣した使節)", "名詞", "An imperial envoy traveled abroad to exchange goods, ideas, and diplomatic messages on behalf of the court.", "職業", "800"),
    ("blacksmith", "鍛冶職人(古代の)", "名詞", "A blacksmith forged tools and farm implements from iron in ancient Japan.", "職業", "700"),
    ("temple carpenter", "宮大工", "名詞", "A temple carpenter built and repaired wooden shrines and temples using traditional joinery techniques.", "職業", "800"),
    ("kofun laborer", "古墳建設の労働者", "名詞", "A kofun laborer helped construct the large earthen burial mounds built for rulers in ancient Japan.", "職業", "850"),
    ("ama diver", "海女・海士(素潜り漁師)", "名詞", "An ama diver free-dove for shellfish and seaweed along the coast, a practice recorded since ancient Japan.", "職業", "800"),
    ("court historian", "史官(古代中国の)", "名詞", "A court historian in ancient China recorded the events and decisions of the ruling dynasty.", "職業", "800"),
    ("imperial censor", "御史(監察官)", "名詞", "An imperial censor monitored officials for corruption and reported misconduct directly to the throne.", "職業", "900"),
    ("eunuch", "宦官", "名詞", "A eunuch served inside the imperial palace and sometimes gained considerable influence over court affairs.", "職業", "850"),
    ("Confucian scholar-official", "儒学の官僚(科挙官僚)", "名詞", "A Confucian scholar-official passed rigorous written examinations before being appointed to a government post.", "職業", "900"),
    ("silk weaver", "絹織り職人(古代中国の)", "名詞", "A silk weaver produced fine fabric that became one of ancient China's most valuable exports.", "職業", "750"),
    ("oracle bone diviner", "甲骨占いをする者", "名詞", "An oracle bone diviner interpreted cracks in heated bones and shells to answer questions for the ruler.", "職業", "900"),
    ("tax collector", "徴税官(古代中国の)", "名詞", "A tax collector gathered grain and goods from farmers on behalf of the imperial government.", "職業", "700"),
    ("court astronomer", "宮廷天文官", "名詞", "A court astronomer tracked the movements of stars and planets to advise the ruler on the calendar.", "職業", "850"),
    ("imperial guard", "禁軍・近衛兵(皇帝直属の護衛)", "名詞", "An imperial guard protected the emperor and the palace grounds from threats.", "職業", "750"),
    ("salt and iron official", "塩鉄官(専売を管理する官吏)", "名詞", "A salt and iron official managed the government monopoly over salt and iron production in ancient China.", "職業", "900"),
    ("calligrapher", "書家(古代中国の)", "名詞", "A calligrapher trained for years to master the brushstrokes used in official documents and art.", "職業", "750"),
    ("tomb sculptor", "陵墓の彫刻職人", "名詞", "A tomb sculptor carved clay or stone figures meant to accompany rulers in the afterlife.", "職業", "850"),
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

    print(f"words: +{w_added} (skipped {w_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
