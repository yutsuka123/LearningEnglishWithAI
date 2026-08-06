# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add vocabulary for occupations of medieval / early-modern Japan and China,
authored by Claude (2026-08-06・ユーザー要望:「英語で日本・中国の歴史文化を
紹介する文脈」を想定した、中世〜近世の日本・中国に存在した職業の語彙追加).

domain='職業' の既存53件は firefighter, blacksmith, tailor, civil servant の
ような現代・汎用的な職業が中心で、中世〜近世の日本・中国に固有の職業は
含まれていなかった。このスクリプトはそこに、英語で日本・中国の歴史文化を
説明する際によく登場する職業語彙を追加する:

- 日本(16語): 浪人・執権・僧兵・刀鍛冶・茶人・浮世絵師・(江戸時代の)商人・
  庄屋/名主・札差・奥医師・鷹匠・彫師・陰陽師・城代・杜氏・町奉行
- 中国(16語): 科挙官僚・宦官・絹商人・道士・御医・書家・知県(地方官)・
  茶商・陶工・御史(監察官)・本草学者・欽天監(天文官)・史官・徴税官・
  織工・禁軍(親衛隊)

事前に既存DB(words ~7000件超)を全件チェックし、以下がすでに存在する
ことを確認したため、このリストから除外した(またはそれと衝突しない
別語に差し替えた):
  samurai(侍/歴史), ninja(忍者/歴史), daimyo(大名/歴史), shogun(将軍/歴史),
  geisha(芸者/歴史), court noble(公家/階級社会), ukiyo-e(浮世絵/芸術),
  monk(僧・修道士/宗教), merchant(商人/歴史), physician(医師/医療),
  magistrate(治安判事/法律), retainer(家臣・従者/歴史), vassal(家臣/歴史),
  scholar-official(士大夫・科挙官僚/階級社会)
上記と紛らわしい語(例: 「僧」「商人」「医師」「奉行・地方官」)は、
Edo-period merchant / court physician / county magistrate / town magistrate
のように、既存語より限定的で歴史的に正確な複合語・別語に置き換えている。

domain は '職業' に統一(既存の職業語彙と同じ domain)。品詞はすべて名詞。
level は ["300-","300","350","400","450","500","550","600","650","700",
"750","800","850","900","950","990","990+"] のスケールに沿って付与しており、
比較的知られた語(ronin, sake brewer, silk merchant, tea merchant, tax
collectorなど)は550〜700、専門的な役職・職名(shogunal regent, rice
broker, onmyoji, castellan, imperial censor, court astronomerなど)は
750〜900とした。

事実確認: すべて実在した職業・役職の一般名称であり、特定の実在人物名は
一切使用していない(例文も個人名を含まない一般的な説明文)。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_occupations_medieval_japan_china.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 日本(中世〜近世) ---
    ("ronin", "浪人(主君を持たない武士)", "名詞", "After his lord's clan was defeated in battle, the ronin wandered from town to town looking for work.", "職業", "600"),
    ("shogunal regent", "執権(将軍を補佐した実質的な最高権力者)", "名詞", "During the Kamakura period, the shogunal regent often held more real power than the shogun himself.", "職業", "850"),
    ("warrior monk", "僧兵(武装した僧)", "名詞", "Warrior monks from mountain temples sometimes clashed with samurai armies over land and influence.", "職業", "750"),
    ("swordsmith", "刀鍛冶", "名詞", "A skilled swordsmith could spend weeks folding and hammering steel to forge a single blade.", "職業", "650"),
    ("tea master", "茶人・茶道の師匠", "名詞", "The tea master guided his students through every precise movement of the tea ceremony.", "職業", "650"),
    ("ukiyo-e artist", "浮世絵師", "名詞", "An ukiyo-e artist would design a woodblock print, which craftsmen then carved and printed.", "職業", "700"),
    ("Edo-period merchant", "江戸時代の商人", "名詞", "Although wealthy, an Edo-period merchant officially ranked below samurai, farmers, and artisans in the social order.", "職業", "600"),
    ("village headman", "庄屋・名主", "名詞", "The village headman collected taxes on behalf of the local lord and settled disputes among farmers.", "職業", "700"),
    ("rice broker", "札差(武士の俸禄米を換金・仲介した商人)", "名詞", "A rice broker converted a samurai's rice stipend into cash, often lending money against future harvests.", "職業", "850"),
    ("court physician", "奥医師(将軍や大名に仕えた医師)", "名詞", "A court physician treated the shogun and his family, and the position was often passed down within one family.", "職業", "750"),
    ("falconer", "鷹匠", "名詞", "The falconer trained hawks for the lord's hunting expeditions, a skill passed down for generations.", "職業", "700"),
    ("woodblock carver", "彫師(浮世絵の版木を彫る職人)", "名詞", "The woodblock carver transferred the artist's drawing onto a block of wood, cutting away everything but the lines.", "職業", "750"),
    ("onmyoji", "陰陽師(陰陽道に基づく占い・儀式を行った官人)", "名詞", "At the imperial court, an onmyoji advised nobles on lucky directions and performed rituals to ward off misfortune.", "職業", "850"),
    ("castellan", "城代(城主に代わって城を管理する家老)", "名詞", "While the lord was away at war, the castellan governed the castle and its surrounding lands.", "職業", "850"),
    ("sake brewer", "杜氏・酒蔵の醸造責任者", "名詞", "A master sake brewer oversaw the fermentation process through the cold winter months.", "職業", "600"),
    ("town magistrate", "町奉行(江戸などの行政・司法を担った役職)", "名詞", "The town magistrate handled both administrative duties and criminal trials within the city.", "職業", "750"),
    # --- 中国(中世〜近世) ---
    ("mandarin official", "科挙に合格して任官した官僚", "名詞", "To become a mandarin official, a candidate had to pass a series of rigorous imperial examinations.", "職業", "750"),
    ("court eunuch", "宦官", "名詞", "A court eunuch served inside the imperial palace and could sometimes gain great influence over the emperor.", "職業", "800"),
    ("silk merchant", "絹商人", "名詞", "The silk merchant traveled along trade routes, selling fine fabric to buyers in distant cities.", "職業", "550"),
    ("Taoist priest", "道士", "名詞", "A Taoist priest performed rituals and offered guidance based on the teachings of Taoism.", "職業", "650"),
    ("imperial physician", "御医(皇帝に仕えた医師)", "名詞", "An imperial physician treated the emperor and had to be extremely careful, since a wrong diagnosis could cost him his position.", "職業", "750"),
    ("calligrapher", "書家", "名詞", "A skilled calligrapher could earn great respect at court simply through the beauty of his brushwork.", "職業", "650"),
    ("county magistrate", "知県(地方の行政・司法を司った官吏)", "名詞", "The county magistrate was responsible for collecting taxes, judging court cases, and keeping order in his district.", "職業", "700"),
    ("tea merchant", "茶商", "名詞", "A tea merchant bought leaves from mountain farms and sold them in markets across the empire.", "職業", "550"),
    ("porcelain maker", "陶工(磁器職人)", "名詞", "A skilled porcelain maker could spend years perfecting the glaze used on fine ceramics.", "職業", "650"),
    ("imperial censor", "御史(官吏の不正を監察する役人)", "名詞", "An imperial censor was expected to report corruption among officials, even those of higher rank.", "職業", "850"),
    ("herbalist", "本草学者・薬草医", "名詞", "The herbalist prepared remedies from dried roots and plants according to traditional medical texts.", "職業", "700"),
    ("court astronomer", "欽天監(暦の作成や天文観測を担った官人)", "名詞", "The court astronomer tracked the movements of the stars and helped compile the official calendar.", "職業", "800"),
    ("court historian", "史官(歴代の出来事を記録した官吏)", "名詞", "The court historian recorded the events of each reign so that future generations could study them.", "職業", "800"),
    ("tax collector", "徴税官", "名詞", "The tax collector traveled from village to village, gathering grain and coin owed to the state.", "職業", "550"),
    ("silk weaver", "織工(絹織物職人)", "名詞", "A silk weaver could spend months completing a single length of fine patterned fabric.", "職業", "600"),
    ("imperial guard", "禁軍・御林軍の兵士(皇帝や宮殿を守る兵士)", "名詞", "Members of the imperial guard were stationed throughout the palace to protect the emperor at all times.", "職業", "600"),
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
