# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""Top up the 化学(chemistry) and 生化学(biochemistry) domains with lab
equipment/glassware, experimental techniques, and more organic/inorganic/
biochemistry terms, authored by Claude (2026-08-04・ユーザー要望:「化学は
生化学、有機化学、無機化学、化学機器、実験用具、滴定などの手法がほしい」)。

既存の化学(125語)・生化学(20語)は物質名・元素名・化合物名や酸化/還元/中和/
沈殿/滴定/合成/加水分解/共有結合/イオン結合/官能基/触媒といった反応概念の
語彙が中心で、実験器具・ガラス器具や実験手法(蒸留・ろ過・抽出・クロマトグラ
フィーなど)、有機化学の反応type/異性体、無機化学の酸化数/電気分解、生化学の
酵素反応速度論/転写・翻訳といった語彙が完全に欠けていた。そのギャップを埋める。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased). Before
writing this list, the full live `words` table was checked for overlap; a
few originally-planned terms were already present under OTHER domains
(clamp→機械工学, funnel→料理, scale→音楽, mortar and pestle→料理,
filtration→園芸・アクアリウム, extraction→コーヒー, endpoint→IT,
standardization→数学, evaporation→地学, control group→論文用語,
electrode→電気電子, enzyme/ribosome/chromosome→生物学) and were either
dropped or replaced with a more specific/non-colliding term (e.g.
"vacuum filtration", "solvent extraction", "titration endpoint",
"standardize", "evaporate").

Run:  python scripts/add_chemistry_lab.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 実験器具・ガラス器具 (domain=化学) ---
    ("beaker", "ビーカー", "名詞", "Pour the solution into a clean beaker before heating it.", "化学", "400"),
    ("Erlenmeyer flask", "三角フラスコ", "名詞", "Swirl the Erlenmeyer flask gently while adding the titrant.", "化学", "500"),
    ("volumetric flask", "メスフラスコ", "名詞", "Use a volumetric flask to prepare exactly 250 mL of standard solution.", "化学", "550"),
    ("test tube", "試験管", "名詞", "She added a few drops of indicator to the test tube.", "化学", "400"),
    ("test tube rack", "試験管立て", "名詞", "Place the test tubes back in the rack after labeling them.", "化学", "450"),
    ("burette", "ビュレット", "名詞", "The burette is clamped vertically above the flask during a titration.", "化学", "600"),
    ("pipette", "ピペット", "名詞", "Use a pipette to transfer exactly 10 mL of the sample.", "化学", "550"),
    ("graduated cylinder", "メスシリンダー", "名詞", "Measure the volume of liquid with a graduated cylinder, not a beaker.", "化学", "500"),
    ("Bunsen burner", "ブンゼンバーナー", "名詞", "Adjust the Bunsen burner until the flame turns blue.", "化学", "450"),
    ("ring stand", "実験用スタンド", "名詞", "The flask is supported on a ring stand above the burner.", "化学", "500"),
    ("filter paper", "ろ紙", "名詞", "Fold the filter paper into a cone before placing it in the funnel.", "化学", "500"),
    ("stirring rod", "ガラス棒(撹拌棒)", "名詞", "Use a stirring rod to mix the solution, not your pipette.", "化学", "550"),
    ("watch glass", "時計皿", "名詞", "Cover the beaker with a watch glass to reduce evaporation.", "化学", "600"),
    ("crucible", "るつぼ", "名詞", "The sample was heated in a crucible until it turned to ash.", "化学", "650"),
    ("desiccator", "デシケーター", "名詞", "Store the dried sample in a desiccator to keep it moisture-free.", "化学", "700"),
    ("fume hood", "ドラフトチャンバー", "名詞", "Always work with volatile solvents inside a fume hood.", "化学", "650"),
    ("safety goggles", "保護メガネ", "名詞", "Put on safety goggles before you handle any acid.", "化学", "450"),
    ("lab coat", "白衣", "名詞", "Everyone must wear a lab coat in the chemistry lab.", "化学", "400"),
    ("balance", "天秤(はかり)", "名詞", "Weigh the powder on the balance before dissolving it.", "化学", "450"),
    ("analytical balance", "分析用電子天秤", "名詞", "The analytical balance can measure mass to the nearest 0.0001 gram.", "化学", "700"),
    ("centrifuge", "遠心分離機", "名詞", "Spin the mixture in the centrifuge to separate the solid from the liquid.", "化学", "650"),
    ("autoclave", "オートクレーブ(高圧蒸気滅菌器)", "名詞", "All the glassware is sterilized in an autoclave before use.", "化学", "700"),
    ("pH meter", "pHメーター", "名詞", "Calibrate the pH meter with buffer solutions before taking a reading.", "化学", "550"),
    ("spectrophotometer", "分光光度計", "名詞", "The spectrophotometer measures how much light the solution absorbs.", "化学", "800"),
    ("thermometer", "温度計", "名詞", "Record the temperature with a thermometer clamped inside the flask.", "化学", "400"),
    ("hot plate", "ホットプレート(実験用)", "名詞", "Set the hot plate to a low temperature so the solution doesn't boil over.", "化学", "450"),
    ("magnetic stirrer", "マグネティックスターラー", "名詞", "Drop a small stir bar into the beaker and turn on the magnetic stirrer.", "化学", "650"),
    ("separating funnel", "分液ロート", "名詞", "Shake the separating funnel and let the two layers settle.", "化学", "700"),
    ("condenser", "冷却器", "名詞", "Cold water flows through the condenser to cool the vapor back into liquid.", "化学", "700"),
    ("distillation apparatus", "蒸留装置", "名詞", "Set up the distillation apparatus before you begin heating the mixture.", "化学", "700"),
    ("dropper", "スポイト", "名詞", "Add the indicator one drop at a time with a dropper.", "化学", "450"),
    ("wash bottle", "洗浄瓶", "名詞", "Rinse the electrode with distilled water from the wash bottle.", "化学", "500"),
    ("litmus paper", "リトマス紙", "名詞", "Dip a strip of litmus paper into the solution to check if it's acidic.", "化学", "500"),
    # --- 実験手法・分析手法 (domain=化学) ---
    ("distillation", "蒸留", "名詞", "Distillation separates the mixture based on differences in boiling point.", "化学", "600"),
    ("vacuum filtration", "減圧ろ過", "名詞", "We used vacuum filtration to speed up the separation of the crystals.", "化学", "700"),
    ("solvent extraction", "溶媒抽出", "名詞", "Solvent extraction removed the organic compound from the aqueous layer.", "化学", "750"),
    ("chromatography", "クロマトグラフィー", "名詞", "Chromatography separated the pigments into several colored bands.", "化学", "750"),
    ("crystallization", "結晶化", "名詞", "Slow cooling encouraged crystallization of the pure compound.", "化学", "650"),
    ("recrystallization", "再結晶", "名詞", "Recrystallization is used to purify a solid by dissolving and reforming its crystals.", "化学", "750"),
    ("calibration curve", "検量線", "名詞", "Plot a calibration curve using solutions of known concentration.", "化学", "750"),
    ("serial dilution", "連続希釈", "名詞", "We prepared a serial dilution to test the reaction at different concentrations.", "化学", "700"),
    ("standard solution", "標準溶液", "名詞", "Fill the burette with a standard solution of known concentration.", "化学", "650"),
    ("titration endpoint", "滴定の終点", "名詞", "The indicator changed color right at the titration endpoint.", "化学", "700"),
    ("equivalence point", "当量点", "名詞", "At the equivalence point, the moles of acid and base are exactly equal.", "化学", "800"),
    ("standardize", "(溶液の濃度を)標定する", "動詞", "We standardized the sodium hydroxide solution against a known acid.", "化学", "750"),
    ("sublimation", "昇華", "名詞", "Dry ice undergoes sublimation, turning straight from solid to gas.", "化学", "600"),
    ("decantation", "デカンテーション(上澄み除去)", "名詞", "Decantation let us pour off the liquid without disturbing the sediment.", "化学", "700"),
    ("evaporate", "蒸発させる", "動詞", "Evaporate the solvent slowly so the crystals form evenly.", "化学", "500"),
    ("gravimetric analysis", "重量分析", "名詞", "Gravimetric analysis determines the amount of a substance by measuring its mass.", "化学", "800"),
    ("qualitative analysis", "定性分析", "名詞", "Qualitative analysis tells us which ions are present, not how much.", "化学", "700"),
    ("quantitative analysis", "定量分析", "名詞", "Quantitative analysis measures exactly how much of each substance is present.", "化学", "700"),
    ("significant figures", "有効数字", "名詞", "Report your answer with the correct number of significant figures.", "化学", "600"),
    ("dimensional analysis", "次元解析", "名詞", "Dimensional analysis helps you check whether your units cancel correctly.", "化学", "800"),
    # --- 有機化学 (domain=化学) ---
    ("esterification", "エステル化", "名詞", "Esterification combines an alcohol and a carboxylic acid to form an ester.", "化学", "800"),
    ("hydrogenation", "水素化", "名詞", "Hydrogenation adds hydrogen across a double bond to saturate it.", "化学", "750"),
    ("substitution reaction", "置換反応", "名詞", "In a substitution reaction, one atom or group replaces another.", "化学", "700"),
    ("addition reaction", "付加反応", "名詞", "An addition reaction adds atoms across a carbon-carbon double bond.", "化学", "700"),
    ("elimination reaction", "脱離反応", "名詞", "An elimination reaction removes atoms to form a new double bond.", "化学", "750"),
    ("isomer", "異性体", "名詞", "These two isomers have the same formula but different structures.", "化学", "700"),
    ("stereochemistry", "立体化学", "名詞", "Stereochemistry describes how atoms are arranged in three-dimensional space.", "化学", "850"),
    ("chirality", "キラリティー(掌性)", "名詞", "Chirality means a molecule cannot be superimposed on its mirror image.", "化学", "850"),
    ("polymerization", "重合", "名詞", "Polymerization links many small monomers into one long chain.", "化学", "700"),
    ("condensation reaction", "縮合反応", "名詞", "A condensation reaction joins two molecules and releases water.", "化学", "750"),
    ("aromatic compound", "芳香族化合物", "名詞", "Benzene is the simplest aromatic compound you'll study this semester.", "化学", "700"),
    ("saturated", "飽和の", "形容詞", "A saturated hydrocarbon contains only single bonds between carbon atoms.", "化学", "550"),
    ("unsaturated", "不飽和の", "形容詞", "Unsaturated fats contain at least one carbon-carbon double bond.", "化学", "550"),
    ("alkane", "アルカン", "名詞", "Alkanes are the simplest family of hydrocarbons, containing only single bonds.", "化学", "600"),
    ("alkene", "アルケン", "名詞", "An alkene contains at least one carbon-carbon double bond.", "化学", "600"),
    ("alkyne", "アルキン", "名詞", "An alkyne contains a carbon-carbon triple bond.", "化学", "650"),
    # --- 無機化学 (domain=化学) ---
    ("coordination compound", "配位化合物", "名詞", "A coordination compound forms when a metal ion bonds with surrounding ligands.", "化学", "850"),
    ("complex ion", "錯イオン", "名詞", "The solution turned deep blue as the complex ion formed.", "化学", "800"),
    ("oxidation state", "酸化数", "名詞", "Determine the oxidation state of each element before balancing the equation.", "化学", "700"),
    ("redox reaction", "酸化還元反応", "名詞", "In a redox reaction, one substance loses electrons while another gains them.", "化学", "650"),
    ("precipitation reaction", "沈殿反応", "名詞", "Mixing the two clear solutions triggered a precipitation reaction.", "化学", "650"),
    ("electrolysis", "電気分解", "名詞", "Electrolysis of water produces hydrogen gas at one electrode and oxygen at the other.", "化学", "650"),
    ("cathode", "陰極", "名詞", "Reduction always occurs at the cathode.", "化学", "650"),
    ("anode", "陽極", "名詞", "Oxidation always occurs at the anode.", "化学", "650"),
    ("activity series", "イオン化傾向(金属の反応性の順列)", "名詞", "According to the activity series, zinc will displace copper from solution.", "化学", "800"),
    # --- 生化学 (domain=生化学) ---
    ("enzyme kinetics", "酵素反応速度論", "名詞", "Enzyme kinetics describes how reaction rate changes with substrate concentration.", "生化学", "850"),
    ("active site", "活性部位", "名詞", "The substrate binds tightly to the enzyme's active site.", "生化学", "750"),
    ("substrate specificity", "基質特異性", "名詞", "Substrate specificity means an enzyme usually reacts with only one type of molecule.", "生化学", "850"),
    ("metabolic pathway", "代謝経路", "名詞", "Glycolysis is just one step in a much longer metabolic pathway.", "生化学", "750"),
    ("cellular respiration", "細胞呼吸", "名詞", "Cellular respiration converts glucose and oxygen into usable energy.", "生化学", "700"),
    ("DNA replication", "DNA複製", "名詞", "DNA replication must occur before a cell can divide.", "生化学", "750"),
    ("transcription", "転写(DNAからRNAへ)", "名詞", "During transcription, the DNA sequence is copied into a strand of mRNA.", "生化学", "750"),
    ("translation", "翻訳(mRNAからタンパク質へ)", "名詞", "During translation, the ribosome reads mRNA and assembles a protein.", "生化学", "750"),
    ("gene expression", "遺伝子発現", "名詞", "Gene expression is regulated so that only certain proteins are made in a given cell.", "生化学", "750"),
    ("allosteric regulation", "アロステリック制御", "名詞", "Allosteric regulation changes an enzyme's activity by binding at a site away from the active site.", "生化学", "900"),
    ("cofactor", "補因子", "名詞", "Many enzymes require a metal ion cofactor to function properly.", "生化学", "750"),
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
