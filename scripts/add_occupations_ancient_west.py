# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""Add ANCIENT-WESTERN-OCCUPATION vocabulary, authored by Claude
(2026-08-06・ユーザー要望: 「古代の欧米(古代ギリシャ・古代ローマ・古代エジプト等)に
存在した職業で、現代日本語話者には馴染みが薄いが、歴史・古典文学・映画等で登場する語」)。

domain='職業' の語彙に、古代ギリシャ・古代ローマ・古代エジプトに実在した職業・
役職を追加する。scribe(書記)、gladiator の代わりに hoplite(重装歩兵)、
senator(元老院議員)、centurion(百人隊長)といった比較的知られた語から、
haruspex(内臓占い師)、lanista(剣闘士養成者)、pontifex(ローマの上級神官)、
lictor(政務官の護衛・随行官)のような専門的な語まで幅広く収録した。

各語の example は、その職業がどの古代文明・時代のものかが伝わる英文とし、
不確かな年代の断定や誇張表現は避けた(例: カエサル暗殺の逸話は
"According to ancient accounts, ..." と出典のニュアンスを残す形にした)。

level は ["300-","300","350","400","450","500","550","600","650","700",
"750","800","850","900","950","990","990+"] のスケールに沿って付与しており、
比較的知られた語(scribe, senator, philosopher, potter など)は500〜650、
古代ローマ・ギリシャに特有の専門的な役職(haruspex, lanista, lictor,
aedile, rhapsode など)は900〜950とした。

事前に既存DB(data/vocabulary.db, words ~7000件)を読み取り専用でチェックし、
候補語のうち "gladiator"(domain='歴史', level=650)が既に存在することを
確認したため、このリストからは除外し、代わりに hoplite(重装歩兵)を採用した。
architect / glassblower / surveyor も domain='職業' で既に存在することを
確認済みのため、このリストには含めていない。それ以外の35語は重複なしを
確認済みだが、念のため main() 側でも english(小文字化)による重複チェックを
行い、既存語はスキップする。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).
This script only INSERTs into `words`; it does not touch `phrases`.

Run:  python scripts/add_occupations_ancient_west.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("scribe", "書記", "名詞", "A scribe in ancient Egypt recorded harvests and tax records on papyrus.", "職業", "500"),
    ("herald", "伝令官", "名詞", "A herald in ancient Greece announced official messages to the public.", "職業", "600"),
    ("hoplite", "重装歩兵(ホプリタイ)", "名詞", "Hoplites were citizen-soldiers in ancient Greece who fought together in a tight formation called a phalanx.", "職業", "750"),
    ("senator", "元老院議員", "名詞", "A Roman senator debated laws and policy in the Senate house.", "職業", "550"),
    ("centurion", "百人隊長", "名詞", "A centurion commanded a unit of around a hundred soldiers in the Roman army.", "職業", "650"),
    ("oracle", "神託を告げる者(神託所)", "名詞", "People traveled to the oracle at Delphi to seek advice from the gods.", "職業", "600"),
    ("soothsayer", "占い師", "名詞", "According to ancient accounts, a soothsayer warned Julius Caesar to beware the Ides of March.", "職業", "700"),
    ("charioteer", "戦車の御者", "名詞", "Charioteers competed in dangerous races at the Circus Maximus in Rome.", "職業", "750"),
    ("embalmer", "ミイラ職人(遺体防腐処理師)", "名詞", "Embalmers in ancient Egypt preserved the bodies of the dead before burial.", "職業", "750"),
    ("vestal virgin", "ウェスタの巫女", "名詞", "A vestal virgin tended the sacred fire in the Temple of Vesta in Rome.", "職業", "850"),
    ("praetor", "法務官(プラエトル)", "名詞", "A praetor oversaw legal matters and administered justice in the Roman Republic.", "職業", "900"),
    ("tribune", "護民官", "名詞", "A tribune of the plebs could veto actions that harmed the interests of common citizens.", "職業", "800"),
    ("philosopher", "哲学者", "名詞", "Philosophers in ancient Greece such as Socrates taught in public spaces like the agora.", "職業", "500"),
    ("rhetorician", "修辞学者", "名詞", "A rhetorician trained young Romans in the art of persuasive public speaking.", "職業", "850"),
    ("moneylender", "金貸し", "名詞", "Moneylenders in ancient Rome charged interest on loans made to merchants.", "職業", "650"),
    ("augur", "鳥占官", "名詞", "An augur interpreted the flight and calls of birds to learn the will of the gods.", "職業", "900"),
    ("haruspex", "内臓占い師", "名詞", "A haruspex examined the entrails of sacrificed animals to interpret omens.", "職業", "950"),
    ("legionary", "軍団兵", "名詞", "A legionary served as a professional soldier in one of Rome's legions.", "職業", "700"),
    ("consul", "執政官", "名詞", "Two consuls were elected each year to jointly lead the Roman Republic.", "職業", "650"),
    ("shipwright", "造船工", "名詞", "Shipwrights in ancient Greece built wooden warships known as triremes.", "職業", "800"),
    ("tax collector", "徴税人", "名詞", "Tax collectors known as publicans gathered revenue on behalf of the Roman government.", "職業", "550"),
    ("midwife", "助産師", "名詞", "Midwives in ancient Rome assisted women during childbirth.", "職業", "600"),
    ("potter", "陶工", "名詞", "Ancient Greek potters shaped clay into vases that were later painted with scenes from daily life.", "職業", "500"),
    ("vase painter", "壺絵師", "名詞", "Vase painters decorated Greek pottery with scenes from mythology and everyday life.", "職業", "700"),
    ("armorer", "武具職人", "名詞", "Armorers forged swords, shields, and armor for Roman soldiers.", "職業", "700"),
    ("lanista", "剣闘士養成者", "名詞", "A lanista owned and trained gladiators before sending them to fight in the arena.", "職業", "950"),
    ("mosaic maker", "モザイク職人", "名詞", "Mosaic makers decorated the floors of Roman villas with intricate patterns made of small tiles.", "職業", "800"),
    ("fuller", "織物仕上げ職人(縮絨職人)", "名詞", "A fuller cleaned and treated wool cloth in ancient Rome.", "職業", "900"),
    ("rhapsode", "叙事詩吟唱者", "名詞", "A rhapsode recited long epic poems such as Homer's Iliad at public gatherings.", "職業", "950"),
    ("lictor", "リクトル(政務官に随行し権標を運ぶ護衛官)", "名詞", "A lictor walked ahead of a Roman magistrate, carrying the ceremonial fasces.", "職業", "950"),
    ("quaestor", "財務官", "名詞", "A quaestor managed public funds and financial affairs in ancient Rome.", "職業", "900"),
    ("aedile", "按察官", "名詞", "An aedile was responsible for maintaining public buildings, markets, and festivals in Rome.", "職業", "950"),
    ("pontifex", "神官(ローマの上級神官)", "名詞", "The pontifex maximus led Rome's college of priests known as the pontifices.", "職業", "900"),
    ("astrologer", "占星術師", "名詞", "Astrologers in the ancient world studied the movements of stars and planets to predict future events.", "職業", "650"),
    ("stonecutter", "石工", "名詞", "Stonecutters quarried and shaped the large blocks used to build the pyramids in ancient Egypt.", "職業", "600"),
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
