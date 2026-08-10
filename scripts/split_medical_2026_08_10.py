# ruff: noqa: E501
"""「医療」ドメインを4分類に再編する(2026-08-10・ドラフト/未実行)。

ユーザー要望: 既存の`医療`ドメイン(190語)を、内容に基づいて次の4分類に
再編する:

- `医療(症状)`: 病気・症状・所見を表す語 (例: fever, rash, nausea,
  fracture, symptom, diabetes, tumor 等)。基礎的な症状語彙(fever, dizzy,
  rash, swelling, nausea等)・急性/慢性疾患名(diabetes, asthma, pneumonia,
  hypertension, migraine, tuberculosis等)・怪我/所見(fracture, bruise,
  lesion, hemorrhage, laceration等)・臨床上の状態像
  (asymptomatic, metastasis, remission, sepsis, comatose, cardiac arrest,
  vitals, pulse等)をまとめてここに含めた。
- `医療(治療)`: 治療・処置・薬・医療機器・応急処置に関する語 (例:
  antibiotic, surgical, bandage, ventilator, vaccine, painkiller 等)。
  薬剤(medicine, antibiotic, painkiller, analgesic, anticoagulant,
  penicillin, epinephrine等)・処置/手技(anesthesia, biopsy, transfusion,
  resection, intubation, amputate等)・医療機器/応急処置用品(bandage,
  crutches, wheelchair, stethoscope, scalpel, defibrillator,
  ventilator等)を含む。
- `医療(専門・学問)`: 医学の学問分野・専門職・研究用語 (例: pathology,
  immunology, physician, diagnosis, prognosis, histology, toxicology
  等)。学問分野名(pathology, anatomy, physiology, immunology,
  dermatology, toxicology等)・専門職(physician, veterinarian,
  specialist等)・臨床/病理診断用語(diagnosis, prognosis, benign,
  malignant, biomarker, contraindication, iatrogenic等)を含む。
- `医療(その他)`: 上記に明確に当てはまらない一般的な医療関連語 (例:
  clinic, appointment, elderly, hygiene, wellness, emergency 等の受け皿)。
  一般的な医療関連語(checkup, clinic, appointment, emergency, hygiene,
  wellness, pharmacy, ambulance等)に加えて、**体の部位名**
  (chest, kidney, liver, spine, ankle, artery等・約50語)もここに含めた。
  部位名は症状・治療・専門のいずれにも明確には属さないため
  (ユーザー指示により、部位名の再編自体は別途新設`身体`ドメインが担当する
  範囲外＝今回は既存4分類の中に収める)。

190語は`SELECT english FROM words WHERE domain='医療'`で全件取得した上で
1件ずつ目視し、4つのPython setに人力で振り分けた(部分一致等の機械的分類は
行っていない)。

フレーズ側は、`SELECT scene, COUNT(*) FROM phrases WHERE scene LIKE
'%医療%' OR scene LIKE '%病院%' OR scene LIKE '%看護%'`で見つかった
既存4シーン(`医療機関を受診する`25件・`生活・医療`11件・`病院・症状`
76件・`看護・医療現場の英語`20件、計132件)を対象に、1件ずつ内容を確認して
以下の4シーンへ再分類した:

- `医療(症状)の英語`(65件): 症状の描写("I have a fever."等、`病院・症状`
  シーンの大半)・バイタル/急変を扱う臨床現場フレーズ("Can you check his
  vital signs?"等)。
- `医療(治療)の英語`(18件): 処方箋・服薬・ワウンドケア等、治療/投薬に
  関するやり取り。
- `医療(専門・学問)の英語`(8件): 専門職への相談・臨床現場の専門業務
  ("Let's do a hand-off to the next shift."等)。
- `医療(他)の英語`(41件): 受診予約・保険・支払い等の事務手続き
  ("I'd like to make an appointment for next week."等、`医療機関を
  受診する`シーンの全件を含む)。単語側の`appointment`/`emergency`等と
  同様に、症状・治療・専門のいずれにも明確に当てはまらない一般的な
  医療関連フレーズの受け皿とした。

前例スクリプト`scripts/split_music_2026_08_10.py`・
`scripts/split_automotive_embedded_2026_08_09.py`と同じ手法(setに無い語は
`[WARN] unclassified`として警告表示・UPDATE文で実際に再分類・最後に旧
domain/sceneの残件数を確認するverificationブロック)を踏襲している。

【重要】このスクリプトはファイルを作成するのみで、実行はしていない。
190語規模の分類は誤分類のリスクがあるため、投入前に人間または別プロセス
によるレビューを想定している。DBを実際に変更するには下記コマンドを
レビュー後に実行すること。

Run:  python scripts/split_medical_2026_08_10.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

OLD_WORD_DOMAIN = "医療"
OLD_PHRASE_SCENES = ("医療機関を受診する", "生活・医療", "病院・症状", "看護・医療現場の英語")

NEW_WORD_DOMAIN_SYMPTOM = "医療(症状)"
NEW_WORD_DOMAIN_TREATMENT = "医療(治療)"
NEW_WORD_DOMAIN_EXPERT = "医療(専門・学問)"
NEW_WORD_DOMAIN_OTHER = "医療(その他)"

NEW_PHRASE_SCENE_SYMPTOM = "医療(症状)の英語"
NEW_PHRASE_SCENE_TREATMENT = "医療(治療)の英語"
NEW_PHRASE_SCENE_EXPERT = "医療(専門・学問)の英語"
NEW_PHRASE_SCENE_OTHER = "医療(他)の英語"


# --- 医療(症状): 病気・症状・所見を表す語 (71語) ---
SYMPTOM_WORDS = {
    "allergy", "chronic", "drowsiness", "cancer", "sick", "disease", "illness",
    "infect", "allergic", "fever", "dizzy", "nauseous", "symptom",
    "side effect", "swollen", "appetite", "blurry", "overdose", "inflammation",
    "swelling", "rash", "numbness", "cramp", "sprain", "fracture", "bruise",
    "dizziness", "nausea", "diabetes", "asthma", "pneumonia", "influenza",
    "stroke", "heart attack", "hypertension", "migraine", "arthritis",
    "anemia", "hepatitis", "tuberculosis", "dementia", "depression",
    "insomnia", "obesity", "ulcer", "diarrhea", "constipation", "infection",
    "tumor", "concussion", "food poisoning", "dehydration", "measles",
    "chickenpox", "lesion", "relapse", "asymptomatic", "metastasis",
    "remission", "sepsis", "obese", "pulse", "flatline", "vitals", "comatose",
    "cardiac arrest", "seizure", "hemorrhage", "dilate", "laceration",
    "rigor mortis",
}

# --- 医療(治療): 治療・処置・薬・医療機器・応急処置 (33語) ---
TREATMENT_WORDS = {
    "prescription", "regimen", "surgical", "medicine", "remedy", "medication",
    "fluids", "penicillin", "anesthesia", "antibiotic", "biopsy",
    "transfusion", "prophylaxis", "palliative", "resection", "subcutaneous",
    "intravenous", "analgesic", "anticoagulant", "vaccine", "painkiller",
    "bandage", "crutches", "wheelchair", "stethoscope", "gurney", "scalpel",
    "forceps", "defibrillator", "intubation", "ventilator", "epinephrine",
    "amputate",
}

# --- 医療(専門・学問): 学問分野・専門職・研究/臨床用語 (26語) ---
EXPERT_WORDS = {
    "physician", "veterinarian", "vet", "psychological", "specialist",
    "diagnosis", "prognosis", "pathology", "anatomy", "physiology", "benign",
    "malignant", "immunology", "dermatology", "etiology", "pathogenesis",
    "comorbidity", "contraindication", "idiopathic", "iatrogenic", "histology",
    "biomarker", "antigen", "cadaver", "toxicology", "malpractice",
}

# --- 医療(その他): 上記に明確に当てはまらない一般語・体の部位名等 (60語) ---
OTHER_WORDS = {
    "checkup", "welfare", "aging", "circulation", "hygiene", "elderly",
    "toxic", "ambulance", "pharmacy", "emergency", "ankle", "throat",
    "pregnant", "organ", "chest", "rib", "heart", "lung", "liver", "kidney",
    "stomach", "intestine", "bowel", "spleen", "pancreas", "gallbladder",
    "bladder", "uterus", "skull", "forehead", "temple", "jaw", "gum", "tongue",
    "spine", "joint", "muscle", "nerve", "artery", "vein", "elbow", "wrist",
    "knee", "shoulder", "abdomen", "waist", "hip", "thigh", "calf", "palm",
    "epidemic", "pandemic", "clinic", "appointment", "nutrient", "calorie",
    "immune", "wellness", "recovery", "morgue",
}


# --- フレーズ: 医療(症状)の英語 (65件) ---
SYMPTOM_PHRASES = {
    "I don't feel well.",
    "I have a fever.",
    "I have a headache.",
    "I have a sore throat.",
    "I've been coughing a lot.",
    "My stomach hurts.",
    "I feel dizzy.",
    "I feel nauseous.",
    "It hurts here.",
    "I twisted my ankle.",
    "I'm allergic to penicillin.",
    "I have high blood pressure.",
    "I've had this pain for three days.",
    "I think I caught a cold.",
    "I feel short of breath.",
    "My vision is blurry.",
    "I've lost my appetite.",
    "The wound is swollen.",
    "Where does it hurt the most?",
    "It hurts around here.",
    "It hurts right here.",
    "My right chest hurts.",
    "My left chest hurts.",
    "I have chest pain.",
    "I feel a pain near my heart.",
    "My heart is pounding.",
    "My elbow hurts.",
    "The front of my head hurts.",
    "The back of my head hurts.",
    "I have a throbbing headache.",
    "My whole head hurts.",
    "I feel faint.",
    "I feel light-headed.",
    "I feel dizzy and nauseous.",
    "I have a sharp pain in my stomach.",
    "My stomach feels heavy.",
    "I have abdominal pain.",
    "My intestines hurt.",
    "My lower abdomen hurts.",
    "It's itchy here.",
    "I have a rash.",
    "I threw out my back.",
    "My lower back hurts.",
    "My shoulders are stiff.",
    "My neck is stiff.",
    "My knee hurts when I walk.",
    "My joints ache.",
    "I feel numb here.",
    "I have a dull pain.",
    "I have a sharp, stabbing pain.",
    "It hurts when I press here.",
    "It hurts when I breathe.",
    "The pain comes and goes.",
    "The pain spreads to my arm.",
    "It's swollen and red.",
    "My side hurts.",
    "My ear hurts.",
    "My eyes are sore.",
    "I have a burning feeling in my chest.",
    "My muscles are sore.",
    "Can you check his vital signs?",
    "What's his blood pressure reading?",
    "The patient's oxygen saturation is dropping.",
    "Can someone call a code blue?",
    "This patient is a high fall risk.",
}

# --- フレーズ: 医療(治療)の英語 (18件) ---
TREATMENT_PHRASES = {
    "Do I need a prescription for this?",
    "Do you have anything for a headache?",
    "I've run out of my medication.",
    "How often should I take this?",
    "How many times a day should I take this?",
    "Are there any side effects?",
    "Could I have a prescription?",
    "I need to refill my medication.",
    "I'm running out of my medicine.",
    "Take this twice a day after meals.",
    "Rest and drink plenty of fluids.",
    "I need a refill of my prescription.",
    "I need to update the care plan.",
    "Please put on your PPE before entering the room.",
    "We need to start an IV drip right away.",
    "Let's reposition him to prevent a pressure ulcer.",
    "The wound dressing needs to be changed.",
    "I'm going over the discharge instructions with the family.",
}

# --- フレーズ: 医療(専門・学問)の英語 (8件) ---
EXPERT_PHRASES = {
    "Should I see a specialist?",
    "Let's do a hand-off to the next shift.",
    "Has the patient been given informed consent?",
    "I'll page the charge nurse.",
    "We're short-staffed on this shift.",
    "Let's schedule a follow-up health screening.",
    "We're conducting contact tracing for this outbreak.",
    "Early detection through screening saves lives.",
}

# --- フレーズ: 医療(他)の英語 (41件) ---
OTHER_PHRASES = {
    "I have an appointment at ten o'clock.",
    "I'd like to make an appointment for next week.",
    "Do you have any openings this afternoon?",
    "I'm a new patient here.",
    "This is my first time visiting this clinic.",
    "Here's my insurance card.",
    "I don't have insurance here — how much would it cost to pay out of pocket?",
    "Is my insurance accepted here?",
    "Could you spell your name for me?",
    "Could I get a form for insurance reimbursement?",
    "Please take a seat in the waiting room.",
    "How long is the wait right now?",
    "Thank you for waiting, the doctor is ready for you now.",
    "The doctor will see you shortly.",
    "How would you like to pay?",
    "Can I pay by credit card?",
    "Could I have a receipt for my insurance claim?",
    "Could you itemize the receipt, please?",
    "I'd like to schedule a follow-up visit.",
    "When should I come back for a check-up?",
    "Do I need to bring anything next time?",
    "Is there a cancellation fee?",
    "Could you write the diagnosis in English?",
    "I need this translated for my insurance company back home.",
    "Is walk-in okay, or do I need an appointment?",
    "I'd like to register with a GP.",
    "Can I book an appointment, please?",
    "I'd like to see a doctor today.",
    "Where's the nearest pharmacy?",
    "I think I need to see a dentist.",
    "It's an emergency.",
    "Could you call an ambulance?",
    "I'd like to see a doctor.",
    "Where is the nearest pharmacy?",
    "Do I need to fast before the test?",
    "Can I have a doctor's note?",
    "Is this covered by insurance?",
    "Please call an ambulance.",
    "I'm pregnant.",
    "Please remember to wash your hands between patients.",
    "The clinic focuses on preventive care for the community.",
}


def main() -> int:
    with db() as conn:
        rows = conn.execute(
            "SELECT id, english FROM words WHERE domain=?", (OLD_WORD_DOMAIN,)
        ).fetchall()
        w_symptom = w_treatment = w_expert = w_other = w_unclassified = 0
        for r in rows:
            eng = r["english"]
            if eng in SYMPTOM_WORDS:
                conn.execute("UPDATE words SET domain=? WHERE id=?",
                             (NEW_WORD_DOMAIN_SYMPTOM, r["id"]))
                w_symptom += 1
            elif eng in TREATMENT_WORDS:
                conn.execute("UPDATE words SET domain=? WHERE id=?",
                             (NEW_WORD_DOMAIN_TREATMENT, r["id"]))
                w_treatment += 1
            elif eng in EXPERT_WORDS:
                conn.execute("UPDATE words SET domain=? WHERE id=?",
                             (NEW_WORD_DOMAIN_EXPERT, r["id"]))
                w_expert += 1
            elif eng in OTHER_WORDS:
                conn.execute("UPDATE words SET domain=? WHERE id=?",
                             (NEW_WORD_DOMAIN_OTHER, r["id"]))
                w_other += 1
            else:
                print(f"  [WARN] unclassified word: {eng!r} (id={r['id']})")
                w_unclassified += 1

        placeholders = ",".join("?" for _ in OLD_PHRASE_SCENES)
        prows = conn.execute(
            f"SELECT id, english FROM phrases WHERE scene IN ({placeholders})",
            OLD_PHRASE_SCENES,
        ).fetchall()
        p_symptom = p_treatment = p_expert = p_other = p_unclassified = 0
        for r in prows:
            eng = r["english"]
            if eng in SYMPTOM_PHRASES:
                conn.execute("UPDATE phrases SET scene=? WHERE id=?",
                             (NEW_PHRASE_SCENE_SYMPTOM, r["id"]))
                p_symptom += 1
            elif eng in TREATMENT_PHRASES:
                conn.execute("UPDATE phrases SET scene=? WHERE id=?",
                             (NEW_PHRASE_SCENE_TREATMENT, r["id"]))
                p_treatment += 1
            elif eng in EXPERT_PHRASES:
                conn.execute("UPDATE phrases SET scene=? WHERE id=?",
                             (NEW_PHRASE_SCENE_EXPERT, r["id"]))
                p_expert += 1
            elif eng in OTHER_PHRASES:
                conn.execute("UPDATE phrases SET scene=? WHERE id=?",
                             (NEW_PHRASE_SCENE_OTHER, r["id"]))
                p_other += 1
            else:
                print(f"  [WARN] unclassified phrase: {eng!r} (id={r['id']})")
                p_unclassified += 1

    print(
        f"words -> 医療(症状): {w_symptom}, 医療(治療): {w_treatment}, "
        f"医療(専門・学問): {w_expert}, 医療(その他): {w_other}, "
        f"unclassified: {w_unclassified}"
    )
    print(
        f"phrases -> 医療(症状)の英語: {p_symptom}, 医療(治療)の英語: {p_treatment}, "
        f"医療(専門・学問)の英語: {p_expert}, 医療(他)の英語: {p_other}, "
        f"unclassified: {p_unclassified}"
    )

    with db() as conn:
        remaining = conn.execute(
            "SELECT COUNT(*) FROM words WHERE domain=?", (OLD_WORD_DOMAIN,)
        ).fetchone()[0]
        placeholders = ",".join("?" for _ in OLD_PHRASE_SCENES)
        remaining_p = conn.execute(
            f"SELECT COUNT(*) FROM phrases WHERE scene IN ({placeholders})",
            OLD_PHRASE_SCENES,
        ).fetchone()[0]
        print(f"remaining in old word domain: {remaining}, old phrase scenes: {remaining_p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
