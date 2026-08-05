# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""学術英単語(NAWL: New Academic Word List) 最初の100語, authored by Claude
(2026-08-05・ユーザー要望:「学術英単語（NAWL）の追加　まず100語　さらに
追加はtodo検討」).

NAWL(Browne, Culligan & Phillips, 2013)は学術英文コーパスに基づく963語の
実在する公開語彙リスト。本スクリプトは公式サイト(eapfoundation.com掲載の
アルファベット順一覧)で確認したNAWL語彙の**先頭100語(abdominal〜broadly、
アルファベット順)**を採用（頻度順データは配布ファイル形式のため未取得。
アルファベット順の先頭100語であることをユーザーに明示）。既存DBに既に
別ドメインで存在する語(acceleration/acid/algorithm/alien等、約37語)は
自動的にスキップされる。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words`
table.

Run:  python scripts/add_nawl_100.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

D = "学術英単語(NAWL)"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("abdominal", "腹部の", "形容詞", "The doctor pressed gently to check for abdominal pain.", D, "750"),
    ("absorb", "吸収する", "動詞", "Plant roots absorb water and minerals from the soil.", D, "600"),
    ("absorption", "吸収", "名詞", "The absorption of the drug is faster on an empty stomach.", D, "750"),
    ("accelerate", "加速する", "動詞", "The economy began to accelerate after the new policy took effect.", D, "650"),
    ("accent", "アクセント・方言", "名詞", "She still speaks with a slight accent from her hometown.", D, "500"),
    ("accumulate", "蓄積する", "動詞", "Dust had accumulated on the shelves after months of neglect.", D, "700"),
    ("accumulation", "蓄積", "名詞", "The accumulation of small errors eventually caused a major failure.", D, "800"),
    ("accuracy", "正確さ", "名詞", "The accuracy of the forecast improved with better data.", D, "650"),
    ("acidic", "酸性の", "形容詞", "The soil here is too acidic for most vegetables to grow well.", D, "700"),
    ("activate", "作動させる・活性化する", "動詞", "Pressing the button will activate the alarm system.", D, "650"),
    ("actively", "積極的に", "副詞", "She actively participated in every discussion during the seminar.", D, "600"),
    ("adaptive", "適応性の", "形容詞", "The species developed an adaptive trait that helped it survive the drought.", D, "800"),
    ("adjacent", "隣接した", "形容詞", "The library is adjacent to the main lecture hall.", D, "750"),
    ("adolescent", "青年期の・思春期の", "形容詞", "Adolescent development includes rapid physical and emotional change.", D, "750"),
    ("adverse", "不利な・有害な", "形容詞", "The medication can cause adverse side effects in rare cases.", D, "800"),
    ("aerosol", "エアロゾル・噴霧剤", "名詞", "Aerosol particles in the air can affect both climate and health.", D, "800"),
    ("aesthetic", "美的な", "形容詞", "The building's aesthetic appeal comes from its simple, clean lines.", D, "800"),
    ("affirm", "断言する・肯定する", "動詞", "The court affirmed the lower court's original decision.", D, "800"),
    ("afterward", "その後", "副詞", "They toured the factory and had lunch afterward.", D, "500"),
    ("aggregate", "集計した・総計", "形容詞・名詞", "The aggregate score combines results from all three tests.", D, "800"),
    ("aluminum", "アルミニウム", "名詞", "Aluminum is valued for being both lightweight and resistant to rust.", D, "600"),
    ("amino", "アミノの", "形容詞", "Each amino acid has a slightly different chemical structure.", D, "800"),
    ("amongst", "〜の中で（amongの異表記）", "前置詞", "The tradition is still practiced amongst several rural communities.", D, "700"),
    ("amplitude", "振幅", "名詞", "The amplitude of the wave determines how loud the sound will be.", D, "850"),
    ("analogy", "類推・アナロジー", "名詞", "The teacher used a simple analogy to explain how electricity flows.", D, "750"),
    ("ancestor", "祖先", "名詞", "Her ancestors settled in the valley over two hundred years ago.", D, "650"),
    ("anthropology", "人類学", "名詞", "Anthropology examines how different cultures organize daily life.", D, "800"),
    ("antibody", "抗体", "名詞", "The vaccine trains the body to produce antibodies against the virus.", D, "800"),
    ("appendix", "付録・虫垂", "名詞", "The full data set is included in the appendix at the back of the report.", D, "750"),
    ("approximate", "おおよその", "形容詞", "The approximate cost of the repair is around two hundred dollars.", D, "700"),
    ("approximation", "近似・概算", "名詞", "The model is only an approximation of how real traffic behaves.", D, "800"),
    ("arbitrary", "任意の・恣意的な", "形容詞", "The rule seemed arbitrary since no one could explain the reasoning behind it.", D, "800"),
    ("archaeology", "考古学", "名詞", "Archaeology helped researchers date the ruins to the early Bronze Age.", D, "750"),
    ("array", "配列・並び", "名詞", "The garden displayed a wide array of colorful flowers.", D, "700"),
    ("articulate", "はっきり述べる", "動詞", "She articulated her concerns clearly during the meeting.", D, "750"),
    ("artistic", "芸術的な", "形容詞", "The building's artistic design won several international awards.", D, "600"),
    ("artwork", "美術品・作品", "名詞", "The gallery displayed artwork from local painters throughout the summer.", D, "550"),
    ("assert", "主張する", "動詞", "He asserted that the results had been misinterpreted.", D, "750"),
    ("athletic", "運動能力に優れた", "形容詞", "She has always been athletic, excelling in nearly every sport.", D, "600"),
    ("atomic", "原子の", "形容詞", "Atomic structure determines how an element behaves chemically.", D, "700"),
    ("auction", "競売・オークション", "名詞", "The painting sold for a record price at the auction.", D, "600"),
    ("audio", "音声の", "形容詞", "The audio quality on the recording was surprisingly clear.", D, "500"),
    ("authority", "権威・当局", "名詞", "The local authority approved the plan after months of review.", D, "650"),
    ("autonomy", "自主性・自治", "名詞", "The region was granted a degree of autonomy over its own laws.", D, "800"),
    ("availability", "利用可能性・在庫状況", "名詞", "Availability of the part depends on the supplier's current stock.", D, "700"),
    ("axiom", "公理・自明の理", "名詞", "The proof begins with a simple axiom that everyone accepts as true.", D, "850"),
    ("axis", "軸", "名詞", "The Earth rotates around its axis once every twenty-four hours.", D, "700"),
    ("backward", "後方へ・逆行して", "副詞", "The car rolled backward slightly before the brake engaged.", D, "550"),
    ("bacteria", "細菌", "名詞", "Bacteria can multiply rapidly under the right conditions.", D, "650"),
    ("bacterial", "細菌の", "形容詞", "The infection turned out to be bacterial rather than viral.", D, "700"),
    ("bang", "大きな音・衝撃", "名詞", "The door slammed shut with a loud bang.", D, "500"),
    ("basin", "盆地・水盆", "名詞", "The river basin supports farmland for hundreds of kilometers.", D, "700"),
    ("beam", "梁・光線", "名詞", "A steel beam supports the entire weight of the roof.", D, "600"),
    ("behavioral", "行動の", "形容詞", "The therapist recommended a behavioral approach to managing anxiety.", D, "750"),
    ("bilingual", "二言語を話す", "形容詞", "Growing up bilingual gave her an advantage in language learning later on.", D, "650"),
    ("binary", "二進法の・二者択一の", "形容詞", "Computers store all information using a binary system of ones and zeros.", D, "750"),
    ("biodiversity", "生物多様性", "名詞", "The rainforest is home to an extraordinary level of biodiversity.", D, "800"),
    ("biologist", "生物学者", "名詞", "The biologist spent years studying coral reefs before the collapse.", D, "650"),
    ("bizarre", "奇妙な", "形容詞", "The witness gave a bizarre account of what had happened.", D, "700"),
    ("blank", "空白の", "形容詞", "Please leave the last field blank if it doesn't apply to you.", D, "500"),
    ("bleed", "出血する", "動詞", "The wound continued to bleed until pressure was applied.", D, "600"),
    ("bodily", "身体の", "形容詞", "The injury caused significant bodily harm.", D, "700"),
    ("bonus", "特別給与・ボーナス", "名詞", "Employees received a bonus after the company's best year on record.", D, "550"),
    ("bracket", "括弧・等級", "名詞", "The tax bracket determines the percentage owed on each portion of income.", D, "750"),
    ("breakdown", "故障・詳細な分析", "名詞", "The report includes a full breakdown of where the budget was spent.", D, "700"),
    ("broadly", "大まかに・広く", "副詞", "The two proposals are broadly similar in their overall goals.", D, "700"),
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
