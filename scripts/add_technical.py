# ruff: noqa: E501  (data-heavy seed script)
"""Add medical symptom phrases (by body part) + organ vocabulary, and
technical vocabulary: chemistry / physics / mechanical / electrical-electronic.

Authored by Claude — no app/OpenAI API calls. All entries are normal, visible
study items (not banned). New word domains: 医療 / 化学 / 物理 / 機械 / 電気電子.

Run:  python scripts/add_technical.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

SCENE_SYMPTOMS = "病院・部位別症状"

# --- medical: symptom phrases (pointing / describing pain by body part) ------

PHRASES_SYMPTOMS: list[tuple[str, str]] = [
    ("It hurts around here.", "この辺が痛いです。"),
    ("It hurts right here.", "ちょうどここが痛いです。"),
    ("My right chest hurts.", "右胸が痛いです。"),
    ("My left chest hurts.", "左胸が痛いです。"),
    ("I have chest pain.", "胸が痛みます。"),
    ("I feel a pain near my heart.", "心臓のあたりが痛いです。"),
    ("My heart is pounding.", "動悸がします。"),
    ("My elbow hurts.", "肘が痛いです。"),
    ("The front of my head hurts.", "頭の前の方が痛いです。"),
    ("The back of my head hurts.", "頭の後ろが痛いです。"),
    ("I have a throbbing headache.", "頭がずきずき痛みます。"),
    ("My whole head hurts.", "頭全体が痛いです。"),
    ("I feel faint.", "もうろうとします／気が遠くなります。"),
    ("I feel light-headed.", "立ちくらみがします。"),
    ("I feel dizzy and nauseous.", "めまいと吐き気がします。"),
    ("My stomach hurts.", "胃が痛いです。"),
    ("I have a sharp pain in my stomach.", "胃がきりきり痛みます。"),
    ("My stomach feels heavy.", "胃がもたれます。"),
    ("I have abdominal pain.", "お腹（腹部）が痛いです。"),
    ("My intestines hurt.", "腸が痛いです。"),
    ("My lower abdomen hurts.", "下腹が痛いです。"),
    ("It's itchy here.", "ここがかゆいです。"),
    ("I have a rash.", "発疹が出ています。"),
    ("I threw out my back.", "ぎっくり腰になりました。"),
    ("My lower back hurts.", "腰が痛いです。"),
    ("My shoulders are stiff.", "肩がこっています。"),
    ("My neck is stiff.", "首がこって回りません。"),
    ("My knee hurts when I walk.", "歩くと膝が痛いです。"),
    ("My joints ache.", "関節が痛みます。"),
    ("I feel numb here.", "ここがしびれます。"),
    ("I have a dull pain.", "鈍い痛みがあります。"),
    ("I have a sharp, stabbing pain.", "鋭い、刺すような痛みがあります。"),
    ("It hurts when I press here.", "ここを押すと痛いです。"),
    ("It hurts when I breathe.", "息をすると痛いです。"),
    ("The pain comes and goes.", "痛みが出たり引いたりします。"),
    ("The pain spreads to my arm.", "痛みが腕に広がります。"),
    ("It's swollen and red.", "腫れて赤くなっています。"),
    ("My side hurts.", "脇腹が痛いです。"),
    ("My ear hurts.", "耳が痛いです。"),
    ("My eyes are sore.", "目が痛いです。"),
    ("I have a burning feeling in my chest.", "胸が焼けるような感じ（胸やけ）がします。"),
    ("My muscles are sore.", "筋肉痛があります。"),
]

# --- words: (english, japanese, pos, example, domain, level) -----------------

WORDS_BODY: list[tuple[str, str]] = [
    ("organ", "臓器"), ("chest", "胸"), ("rib", "肋骨"), ("heart", "心臓"),
    ("lung", "肺"), ("liver", "肝臓"), ("kidney", "腎臓"), ("stomach", "胃"),
    ("intestine", "腸"), ("bowel", "腸"), ("spleen", "脾臓"),
    ("pancreas", "膵臓"), ("gallbladder", "胆のう"), ("bladder", "膀胱"),
    ("uterus", "子宮"), ("brain", "脳"), ("skull", "頭蓋骨"),
    ("forehead", "額"), ("temple", "こめかみ"), ("jaw", "顎"),
    ("gum", "歯茎"), ("tongue", "舌"), ("spine", "背骨"), ("joint", "関節"),
    ("muscle", "筋肉"), ("nerve", "神経"), ("artery", "動脈"), ("vein", "静脈"),
    ("elbow", "肘"), ("wrist", "手首"), ("knee", "膝"), ("shoulder", "肩"),
    ("abdomen", "腹部"), ("waist", "腰"), ("hip", "腰・尻"), ("thigh", "太もも"),
    ("calf", "ふくらはぎ"), ("palm", "手のひら"), ("inflammation", "炎症"),
    ("swelling", "腫れ"), ("rash", "発疹"), ("numbness", "しびれ"),
    ("cramp", "けいれん・差し込み"), ("sprain", "捻挫"), ("fracture", "骨折"),
    ("bruise", "打撲・あざ"), ("dizziness", "めまい"), ("nausea", "吐き気"),
    ("symptom", "症状"), ("diagnosis", "診断"),
]

WORDS_CHEM: list[tuple[str, str]] = [
    ("acid", "酸"), ("alkali", "アルカリ"), ("base", "塩基"),
    ("sulfuric acid", "硫酸"), ("nitric acid", "硝酸"),
    ("hydrochloric acid", "塩酸"), ("citric acid", "クエン酸"),
    ("acetic acid", "酢酸"), ("sodium hydroxide", "水酸化ナトリウム"),
    ("sodium chloride", "塩化ナトリウム"), ("ammonia", "アンモニア"),
    ("hydrogen", "水素"), ("oxygen", "酸素"), ("nitrogen", "窒素"),
    ("carbon", "炭素"), ("compound", "化合物"), ("element", "元素"),
    ("molecule", "分子"), ("atom", "原子"), ("ion", "イオン"),
    ("solution", "溶液"), ("solvent", "溶媒"), ("concentration", "濃度"),
    ("oxidation", "酸化"), ("reduction", "還元"), ("catalyst", "触媒"),
    ("reaction", "(化学)反応"), ("corrosive", "腐食性の"),
    ("flammable", "可燃性の"), ("toxic", "有毒な"), ("dilute", "希釈する"),
    ("neutralize", "中和する"), ("titration", "滴定"), ("reagent", "試薬"),
    ("precipitate", "沈殿（する）"),
]

WORDS_PHYS: list[tuple[str, str]] = [
    ("mechanics", "力学"), ("dynamics", "動力学"), ("statics", "静力学"),
    ("kinematics", "運動学"), ("relativity", "相対性理論"),
    ("quantum", "量子"), ("nuclear", "原子核の"), ("nuclear material", "核物質"),
    ("fission", "核分裂"), ("fusion", "核融合"), ("radiation", "放射線"),
    ("radioactivity", "放射能"), ("gravity", "重力"), ("mass", "質量"),
    ("velocity", "速度"), ("acceleration", "加速度"), ("force", "力"),
    ("momentum", "運動量"), ("energy", "エネルギー"), ("friction", "摩擦"),
    ("inertia", "慣性"), ("vector", "ベクトル"), ("frequency", "周波数"),
    ("wavelength", "波長"), ("amplitude", "振幅"), ("magnetism", "磁気"),
    ("thermodynamics", "熱力学"), ("entropy", "エントロピー"),
    ("particle", "粒子"), ("electron", "電子"), ("proton", "陽子"),
    ("neutron", "中性子"), ("isotope", "同位体"),
]

WORDS_MECH: list[tuple[str, str]] = [
    ("fluid dynamics", "流体力学"), ("flange", "フランジ"), ("motor", "モーター"),
    ("actuator", "アクチュエータ"), ("solenoid", "ソレノイド"),
    ("sheet metal", "板金"), ("surface treatment", "表面処理"),
    ("tolerance", "公差"), ("bearing", "軸受（ベアリング）"), ("gear", "歯車"),
    ("shaft", "軸（シャフト）"), ("valve", "バルブ"), ("pump", "ポンプ"),
    ("piston", "ピストン"), ("cylinder", "シリンダ"), ("torque", "トルク"),
    ("lubrication", "潤滑"), ("viscosity", "粘度"), ("gasket", "ガスケット"),
    ("bolt", "ボルト"), ("nut", "ナット"), ("weld", "溶接（する）"),
    ("casting", "鋳造"), ("machining", "機械加工"), ("lathe", "旋盤"),
    ("coolant", "冷却液"), ("hydraulic", "油圧の"), ("pneumatic", "空圧の"),
    ("assembly", "組立"), ("fatigue", "（金属）疲労"), ("deformation", "変形"),
    ("plating", "めっき"),
]

WORDS_ELEC: list[tuple[str, str]] = [
    ("circuit", "回路"), ("circuit board", "基板（プリント基板）"),
    ("solder", "はんだ（はんだ付けする）"), ("resistor", "抵抗器"),
    ("capacitor", "コンデンサ"), ("inductor", "インダクタ"),
    ("transistor", "トランジスタ"), ("diode", "ダイオード"),
    ("voltage", "電圧"), ("current", "電流"), ("resistance", "(電気)抵抗"),
    ("conductor", "導体"), ("insulator", "絶縁体"),
    ("semiconductor", "半導体"), ("ground", "接地（アース）"),
    ("terminal", "端子"), ("relay", "リレー"), ("fuse", "ヒューズ"),
    ("transformer", "変圧器"), ("capacitance", "静電容量"),
    ("amplifier", "増幅器"), ("oscillator", "発振器"),
    ("microcontroller", "マイコン"), ("firmware", "ファームウェア"),
    ("signal", "信号"), ("waveform", "波形"), ("short circuit", "短絡"),
    ("connector", "コネクタ"), ("voltage drop", "電圧降下"),
    ("printed circuit board", "プリント基板（PCB）"),
]

# Assemble all words with domain + level + a short example.
WORD_GROUPS: list[tuple[str, str, list[tuple[str, str]]]] = [
    ("医療", "700", WORDS_BODY),
    ("化学", "800", WORDS_CHEM),
    ("物理", "800", WORDS_PHYS),
    ("機械", "800", WORDS_MECH),
    ("電気電子", "800", WORDS_ELEC),
]


def main() -> int:
    with db() as conn:
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }

        ph_added = ph_skipped = 0
        for en, ja in PHRASES_SYMPTOMS:
            if en.lower() in ph_existing:
                ph_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) VALUES (?, ?, ?)",
                (en, ja, SCENE_SYMPTOMS),
            )
            ph_existing.add(en.lower())
            ph_added += 1

        w_added = w_skipped = 0
        per_domain: dict[str, int] = {}
        for domain, level, items in WORD_GROUPS:
            for en, ja in items:
                if en.lower() in w_existing:
                    w_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO words (english, japanese, part_of_speech, "
                    "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                    (en, ja, "", "", domain, level),
                )
                w_existing.add(en.lower())
                w_added += 1
                per_domain[domain] = per_domain.get(domain, 0) + 1

    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    print(f"words:   +{w_added} (skipped {w_skipped})  {per_domain}")
    with db() as conn:
        print(
            "totals -> phrases:",
            conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0],
            "words:",
            conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
