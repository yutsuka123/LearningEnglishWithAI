# ruff: noqa: E501
"""化学ドメインの本格拡充(2026-08-09)。

ユーザー要望: 「化学は元素周期表の化学物質全部載せたい。元素周期表用語・
族なども。反応など主な用語。化学専門の大学教養程度の用語拡充。有機化学・
無機化学の主な化合物を追加」。

既存の`化学`domain(265語、うち元素は原子番号1-20台+アルカリ土類等の一部
既存)を精査し、周期表118元素のうち未登録の90元素・族/周期などの周期表
用語・大学教養レベルの一般化学用語・有機/無機の主要化合物のうち未登録
のものだけを追加する(既存語との重複はスクリプトが自動スキップ)。

"period"は既に空欄domainで「期間・時代」の意味で登録済みのため、周期表の
「周期」の意味は"period (chemistry)"として別語彙にした(clock/translation
と同じ多義語対応パターン)。

No app / OpenAI API calls — hand-written(元素データは標準的な周期表に
基づく)。Duplicates skipped by english (lowercased)。

Run:  python scripts/add_chemistry_deep_2026_08_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "化学"

# (atomic_number, symbol, english, japanese, level) — 周期表で未登録の90元素
ELEMENTS: list[tuple[int, str, str, str, str]] = [
    (4, "Be", "beryllium", "ベリリウム", "700"),
    (5, "B", "boron", "ホウ素", "600"),
    (9, "F", "fluorine", "フッ素", "550"),
    (21, "Sc", "scandium", "スカンジウム", "750"),
    (23, "V", "vanadium", "バナジウム", "700"),
    (24, "Cr", "chromium", "クロム", "600"),
    (25, "Mn", "manganese", "マンガン", "650"),
    (27, "Co", "cobalt", "コバルト", "600"),
    (28, "Ni", "nickel", "ニッケル", "600"),
    (31, "Ga", "gallium", "ガリウム", "700"),
    (32, "Ge", "germanium", "ゲルマニウム", "700"),
    (34, "Se", "selenium", "セレン", "700"),
    (35, "Br", "bromine", "臭素", "650"),
    (36, "Kr", "krypton", "クリプトン", "650"),
    (37, "Rb", "rubidium", "ルビジウム", "750"),
    (38, "Sr", "strontium", "ストロンチウム", "700"),
    (39, "Y", "yttrium", "イットリウム", "800"),
    (40, "Zr", "zirconium", "ジルコニウム", "750"),
    (41, "Nb", "niobium", "ニオブ", "800"),
    (42, "Mo", "molybdenum", "モリブデン", "750"),
    (43, "Tc", "technetium", "テクネチウム", "850"),
    (44, "Ru", "ruthenium", "ルテニウム", "800"),
    (45, "Rh", "rhodium", "ロジウム", "800"),
    (46, "Pd", "palladium", "パラジウム", "750"),
    (48, "Cd", "cadmium", "カドミウム", "750"),
    (49, "In", "indium", "インジウム", "750"),
    (50, "Sn", "tin", "スズ", "550"),
    (51, "Sb", "antimony", "アンチモン", "750"),
    (52, "Te", "tellurium", "テルル", "800"),
    (53, "I", "iodine", "ヨウ素", "600"),
    (54, "Xe", "xenon", "キセノン", "650"),
    (55, "Cs", "cesium", "セシウム", "750"),
    (56, "Ba", "barium", "バリウム", "700"),
    (57, "La", "lanthanum", "ランタン", "750"),
    (58, "Ce", "cerium", "セリウム", "800"),
    (59, "Pr", "praseodymium", "プラセオジム", "850"),
    (60, "Nd", "neodymium", "ネオジム", "750"),
    (61, "Pm", "promethium", "プロメチウム", "850"),
    (62, "Sm", "samarium", "サマリウム", "800"),
    (63, "Eu", "europium", "ユウロピウム", "850"),
    (64, "Gd", "gadolinium", "ガドリニウム", "800"),
    (65, "Tb", "terbium", "テルビウム", "850"),
    (66, "Dy", "dysprosium", "ジスプロシウム", "850"),
    (67, "Ho", "holmium", "ホルミウム", "850"),
    (68, "Er", "erbium", "エルビウム", "850"),
    (69, "Tm", "thulium", "ツリウム", "850"),
    (70, "Yb", "ytterbium", "イッテルビウム", "850"),
    (71, "Lu", "lutetium", "ルテチウム", "850"),
    (72, "Hf", "hafnium", "ハフニウム", "800"),
    (73, "Ta", "tantalum", "タンタル", "800"),
    (74, "W", "tungsten", "タングステン", "650"),
    (75, "Re", "rhenium", "レニウム", "850"),
    (76, "Os", "osmium", "オスミウム", "800"),
    (77, "Ir", "iridium", "イリジウム", "800"),
    (79, "Au", "gold", "金", "500"),
    (81, "Tl", "thallium", "タリウム", "750"),
    (83, "Bi", "bismuth", "ビスマス", "750"),
    (84, "Po", "polonium", "ポロニウム", "800"),
    (85, "At", "astatine", "アスタチン", "850"),
    (86, "Rn", "radon", "ラドン", "700"),
    (87, "Fr", "francium", "フランシウム", "850"),
    (88, "Ra", "radium", "ラジウム", "700"),
    (89, "Ac", "actinium", "アクチニウム", "800"),
    (90, "Th", "thorium", "トリウム", "800"),
    (91, "Pa", "protactinium", "プロトアクチニウム", "850"),
    (93, "Np", "neptunium", "ネプツニウム", "800"),
    (95, "Am", "americium", "アメリシウム", "800"),
    (96, "Cm", "curium", "キュリウム", "850"),
    (97, "Bk", "berkelium", "バークリウム", "850"),
    (98, "Cf", "californium", "カリホルニウム", "850"),
    (99, "Es", "einsteinium", "アインスタイニウム", "850"),
    (100, "Fm", "fermium", "フェルミウム", "850"),
    (101, "Md", "mendelevium", "メンデレビウム", "850"),
    (102, "No", "nobelium", "ノーベリウム", "850"),
    (103, "Lr", "lawrencium", "ローレンシウム", "850"),
    (104, "Rf", "rutherfordium", "ラザホージウム", "900"),
    (105, "Db", "dubnium", "ドブニウム", "900"),
    (106, "Sg", "seaborgium", "シーボーギウム", "900"),
    (107, "Bh", "bohrium", "ボーリウム", "900"),
    (108, "Hs", "hassium", "ハッシウム", "900"),
    (109, "Mt", "meitnerium", "マイトネリウム", "900"),
    (110, "Ds", "darmstadtium", "ダームスタチウム", "900"),
    (111, "Rg", "roentgenium", "レントゲニウム", "900"),
    (112, "Cn", "copernicium", "コペルニシウム", "900"),
    (113, "Nh", "nihonium", "ニホニウム", "900"),
    (114, "Fl", "flerovium", "フレロビウム", "900"),
    (115, "Mc", "moscovium", "モスコビウム", "900"),
    (116, "Lv", "livermorium", "リバモリウム", "900"),
    (117, "Ts", "tennessine", "テネシン", "900"),
    (118, "Og", "oganesson", "オガネソン", "900"),
]

# (english, japanese, part_of_speech, example, level) — 族・周期表用語/
# 大学教養レベルの一般化学用語/有機・無機の主要化合物
EXTRA_WORDS: list[tuple[str, str, str, str, str]] = [
    ("group", "族（周期表の縦の列）", "名詞", "Elements in the same group of the periodic table share similar chemical properties.", "650"),
    ("period (chemistry)", "周期（周期表の横の行）", "名詞", "Elements in the same period have the same number of electron shells.", "650"),
    ("alkali metal", "アルカリ金属", "名詞", "Sodium and potassium are both alkali metals.", "650"),
    ("alkaline earth metal", "アルカリ土類金属", "名詞", "Calcium and magnesium are alkaline earth metals.", "650"),
    ("transition metal", "遷移金属", "名詞", "Iron and copper are common transition metals.", "650"),
    ("lanthanide", "ランタノイド", "名詞", "The lanthanides are a series of seventeen rare earth elements.", "800"),
    ("actinide", "アクチノイド", "名詞", "Uranium and plutonium both belong to the actinide series.", "800"),
    ("halogen", "ハロゲン", "名詞", "Fluorine, chlorine, and iodine are all halogens.", "650"),
    ("noble gas", "希ガス", "名詞", "Noble gases rarely react with other elements.", "600"),
    ("metalloid", "半金属", "名詞", "Silicon is a metalloid with properties between metals and nonmetals.", "700"),
    ("atomic number", "原子番号", "名詞", "The atomic number tells you how many protons an atom has.", "600"),
    ("atomic mass", "原子量", "名詞", "The atomic mass of carbon is about twelve.", "600"),
    ("valence electron", "価電子", "名詞", "Valence electrons determine how an atom bonds with others.", "700"),
    ("electron shell", "電子殻", "名詞", "Electrons are arranged in shells around the nucleus.", "650"),
    ("cation", "陽イオン", "名詞", "A sodium atom becomes a cation when it loses an electron.", "650"),
    ("anion", "陰イオン", "名詞", "A chlorine atom becomes an anion when it gains an electron.", "650"),
    ("atomic radius", "原子半径", "名詞", "Atomic radius generally increases as you move down a group.", "750"),
    ("ionization energy", "イオン化エネルギー", "名詞", "Ionization energy is the energy needed to remove an electron from an atom.", "750"),
    ("Avogadro's number", "アボガドロ数", "名詞", "Avogadro's number is approximately 6.022 times ten to the twenty-third.", "700"),
    ("molarity", "モル濃度", "名詞", "Molarity expresses the concentration of a solution in moles per liter.", "700"),
    ("ethane", "エタン", "名詞", "Ethane is a simple hydrocarbon with two carbon atoms.", "650"),
    ("butane", "ブタン", "名詞", "Butane is commonly used as fuel in lighters and portable stoves.", "600"),
    ("propylene", "プロピレン", "名詞", "Propylene is used to manufacture plastics like polypropylene.", "750"),
    ("acetylene", "アセチレン", "名詞", "Acetylene burns at a very high temperature and is used in welding.", "700"),
    ("toluene", "トルエン", "名詞", "Toluene is a common industrial solvent found in paint thinner.", "700"),
    ("formaldehyde", "ホルムアルデヒド", "名詞", "Formaldehyde is used as a preservative in some laboratory specimens.", "700"),
    ("aniline", "アニリン", "名詞", "Aniline was historically important in the dye industry.", "800"),
    ("sucrose", "ショ糖", "名詞", "Sucrose is the scientific name for ordinary table sugar.", "600"),
    ("fructose", "果糖", "名詞", "Fructose is a natural sugar found in fruit and honey.", "600"),
    ("cellulose", "セルロース", "名詞", "Cellulose gives plant cell walls their structural strength.", "650"),
    ("chloroform", "クロロホルム", "名詞", "Chloroform was once used as an anesthetic before safer options were found.", "700"),
    ("amide", "アミド", "名詞", "An amide is formed when a carboxylic acid reacts with an amine.", "750"),
    ("carbon monoxide", "一酸化炭素", "名詞", "Carbon monoxide is a colorless, odorless, and highly toxic gas.", "550"),
    ("calcium carbonate", "炭酸カルシウム", "名詞", "Calcium carbonate is the main component of limestone and chalk.", "600"),
    ("sodium bicarbonate", "重炭酸ナトリウム（重曹の化学名）", "名詞", "Sodium bicarbonate is the chemical name for baking soda.", "650"),
    ("potassium permanganate", "過マンガン酸カリウム", "名詞", "Potassium permanganate produces a deep purple solution in water.", "800"),
    ("copper sulfate", "硫酸銅", "名詞", "Copper sulfate forms bright blue crystals.", "700"),
    ("iron oxide", "酸化鉄", "名詞", "Iron oxide is the reddish compound better known as rust.", "600"),
    ("aluminum oxide", "酸化アルミニウム", "名詞", "Aluminum oxide forms a protective layer on the surface of aluminum metal.", "700"),
    ("silicon dioxide", "二酸化ケイ素", "名詞", "Silicon dioxide is the main component of ordinary sand.", "650"),
    ("silica", "シリカ（二酸化ケイ素の別称）", "名詞", "Silica gel packets are often used to absorb moisture.", "650"),
    ("ozone", "オゾン", "名詞", "Ozone in the upper atmosphere blocks harmful ultraviolet radiation.", "600"),
    ("hydrogen peroxide", "過酸化水素", "名詞", "Hydrogen peroxide is commonly used to disinfect small cuts.", "600"),
    ("sulfur dioxide", "二酸化硫黄", "名詞", "Sulfur dioxide released by burning fossil fuels can cause acid rain.", "650"),
    ("ammonium nitrate", "硝酸アンモニウム", "名詞", "Ammonium nitrate is widely used as an agricultural fertilizer.", "700"),
    ("calcium oxide", "酸化カルシウム（生石灰）", "名詞", "Calcium oxide, also called quicklime, reacts vigorously with water.", "700"),
]


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }

        added = skipped = 0
        for _num, _sym, en, ja, level in ELEMENTS:
            if en.lower() in w_existing:
                skipped += 1
                continue
            example = f"{en.capitalize()} is element number {_num} on the periodic table, with the chemical symbol {_sym}."
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, "名詞", example, DOMAIN, level),
            )
            w_existing.add(en.lower())
            added += 1
        print(f"elements: +{added} (skipped {skipped})")

        added2 = skipped2 = 0
        for en, ja, pos, ex, level in EXTRA_WORDS:
            if en.lower() in w_existing:
                skipped2 += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, DOMAIN, level),
            )
            w_existing.add(en.lower())
            added2 += 1
        print(f"extra terms: +{added2} (skipped {skipped2})")

    with db() as conn:
        print("total words:", conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
        print("化学 domain count:",
              conn.execute("SELECT COUNT(*) FROM words WHERE domain=?", (DOMAIN,)).fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
