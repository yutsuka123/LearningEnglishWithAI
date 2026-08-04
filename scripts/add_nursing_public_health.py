# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add 看護学(nursing practice) as a new domain and top up the thin 保健
(public health) domain, authored by Claude (2026-08-04・ユーザー要望:
「看護学 保健学もほしいかな」).

既存の医療(medical)は身体部位・症状・疾患・基本的な臨床用語(biopsy,
diagnosis, prognosis, physician, prescription, transfusion等)が中心。
保健(health)はわずか16語(nutrition, immunity, cardiovascular,
respiratory, acute, prevention, rehabilitation, deficiency, contagious,
sanitation, dosage, metabolic, wellbeing, vaccination, disorder,
screening)のみだった。

このスクリプトでは:
  1. 新規ドメイン「看護学」: バイタルサイン測定、ケアプラン、感染対策、
     看護師の職種・役割、患者対応など、医療ドメインとは異なる看護実務
     ・専門職の語彙。
  2. 既存ドメイン「保健」を拡張: 疫学、公衆衛生サーベイランス、予防医学、
     健康格差、生活習慣病、ウェルネスなど公衆衛生・保健学の語彙。

追加でシーン「看護・医療現場の英語」に臨床現場でよく使われる自然な
フレーズを追加。

No app / OpenAI API calls — everything is hand-written and inserted
directly into the SQLite DB. Duplicates are skipped by english
(lowercased), checked against the full live words/phrases tables.

Run:  python scripts/add_nursing_public_health.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 看護学: バイタル測定・アセスメント ---
    ("vital signs", "バイタルサイン", "名詞句", "The nurse checked the patient's vital signs every four hours.", "看護学", "650"),
    ("blood pressure cuff", "血圧計のカフ", "名詞句", "She wrapped the blood pressure cuff around his upper arm.", "看護学", "700"),
    ("pulse oximeter", "パルスオキシメーター", "名詞句", "The pulse oximeter showed his oxygen saturation was 96%.", "看護学", "750"),
    ("patient chart", "患者カルテ", "名詞句", "Please update the patient chart after the examination.", "看護学", "600"),
    ("nursing assessment", "看護アセスメント", "名詞句", "A thorough nursing assessment is the first step of the care process.", "看護学", "750"),
    ("care plan", "ケアプラン", "名詞句", "The nurse revised the care plan after the patient's condition changed.", "看護学", "650"),
    ("triage", "トリアージ", "名詞", "Patients are sorted by severity during triage in the emergency room.", "看護学", "750"),
    ("bedside manner", "患者への接し方(態度)", "名詞句", "The new nurse was praised for her warm bedside manner.", "看護学", "800"),
    ("informed consent", "インフォームドコンセント", "名詞句", "The doctor obtained informed consent before starting the procedure.", "看護学", "800"),
    ("discharge instructions", "退院指導", "名詞句", "The nurse went over the discharge instructions with the patient's family.", "看護学", "750"),
    ("medication administration", "与薬・投薬管理", "名詞句", "Medication administration must always follow the five rights.", "看護学", "800"),
    ("IV drip", "点滴", "名詞句", "The IV drip was set to run over two hours.", "看護学", "650"),
    ("catheter", "カテーテル", "名詞", "The nurse carefully inserted the catheter.", "看護学", "750"),
    ("wound dressing", "創傷処置・包帯交換", "名詞句", "The nurse changed the wound dressing twice a day.", "看護学", "700"),
    ("pressure ulcer", "褥瘡(床ずれ)", "名詞句", "Patients on bed rest are at risk of developing a pressure ulcer.", "看護学", "850"),
    ("bedsore", "床ずれ", "名詞", "Turning the patient regularly helps prevent a bedsore.", "看護学", "750"),
    ("patient handoff", "患者引き継ぎ", "名詞句", "A clear patient handoff reduces the risk of medical errors.", "看護学", "800"),
    ("shift report", "申し送り", "名詞句", "The night shift nurse gave a detailed shift report to the day team.", "看護学", "700"),
    ("nurse-to-patient ratio", "看護師対患者比率", "名詞句", "A low nurse-to-patient ratio improves patient safety.", "看護学", "850"),
    ("scope of practice", "業務範囲", "名詞句", "Administering that medication falls outside her scope of practice.", "看護学", "850"),
    ("registered nurse", "正看護師(RN)", "名詞句", "She has worked as a registered nurse for over ten years.", "看護学", "650"),
    ("licensed practical nurse", "准看護師(LPN)", "名詞句", "A licensed practical nurse works under the supervision of an RN.", "看護学", "800"),
    ("nurse practitioner", "ナースプラクティショナー", "名詞句", "The nurse practitioner can prescribe certain medications.", "看護学", "800"),
    ("charge nurse", "リーダー看護師・主任看護師", "名詞句", "The charge nurse assigned patients to each staff member.", "看護学", "750"),
    ("code blue", "コードブルー(緊急事態コール)", "名詞句", "A code blue was called when the patient's heart stopped.", "看護学", "800"),
    ("do-not-resuscitate", "蘇生措置拒否(DNR)の", "形容詞句", "The patient had signed a do-not-resuscitate order.", "看護学", "850"),
    ("palliative care", "緩和ケア", "名詞句", "Palliative care focuses on comfort rather than a cure.", "看護学", "800"),
    ("hospice care", "ホスピスケア", "名詞句", "The family chose hospice care for their grandmother.", "看護学", "800"),
    ("infection control", "感染管理", "名詞句", "Strict infection control measures were enforced in the ward.", "看護学", "700"),
    ("hand hygiene", "手指衛生", "名詞句", "Hand hygiene is the single most effective way to prevent infection.", "看護学", "650"),
    ("personal protective equipment", "個人防護具(PPE)", "名詞句", "Staff must wear personal protective equipment in the isolation room.", "看護学", "750"),
    ("sterile technique", "無菌操作", "名詞句", "The nurse used sterile technique when changing the dressing.", "看護学", "800"),
    ("patient advocacy", "患者擁護", "名詞句", "Patient advocacy is a core value in nursing practice.", "看護学", "850"),
    ("continuity of care", "ケアの継続性", "名詞句", "Good documentation ensures continuity of care between shifts.", "看護学", "850"),
    ("home health care", "在宅医療・訪問看護", "名詞句", "He receives home health care three times a week.", "看護学", "700"),
    ("long-term care", "長期療養ケア", "名詞句", "Her grandmother now lives in a long-term care facility.", "看護学", "700"),
    ("geriatric care", "高齢者ケア", "名詞句", "The unit specializes in geriatric care for elderly patients.", "看護学", "750"),
    ("pediatric nursing", "小児看護", "名詞句", "She switched careers to focus on pediatric nursing.", "看護学", "750"),
    ("postpartum care", "産後ケア", "名詞句", "Postpartum care includes monitoring both mother and baby.", "看護学", "800"),
    ("patient education", "患者教育", "名詞句", "Patient education helps people manage chronic conditions at home.", "看護学", "700"),
    ("fall risk assessment", "転倒リスクアセスメント", "名詞句", "A fall risk assessment is done for every elderly patient on admission.", "看護学", "850"),
    ("restraint", "身体拘束", "名詞", "Restraint is used only as a last resort and must be documented.", "看護学", "750"),
    ("isolation precautions", "隔離予防策", "名詞句", "Isolation precautions were put in place for the patient with the infection.", "看護学", "800"),
    # --- 保健(公衆衛生・保健学): 疫学・サーベイランス ---
    ("epidemiology", "疫学", "名詞", "Epidemiology is the study of how diseases spread in populations.", "保健", "900"),
    ("incidence rate", "罹患率", "名詞句", "The incidence rate of the disease rose sharply last winter.", "保健", "850"),
    ("prevalence", "有病率", "名詞", "The prevalence of diabetes has increased in recent decades.", "保健", "850"),
    ("mortality rate", "死亡率", "名詞句", "The mortality rate from the disease dropped after the vaccine rollout.", "保健", "800"),
    ("morbidity", "罹病率・疾病率", "名詞", "Obesity is linked to higher morbidity in older adults.", "保健", "900"),
    ("public health surveillance", "公衆衛生サーベイランス", "名詞句", "Public health surveillance helped officials detect the outbreak early.", "保健", "900"),
    ("herd immunity", "集団免疫", "名詞句", "High vaccination rates help a community reach herd immunity.", "保健", "800"),
    ("outbreak investigation", "アウトブレイク調査", "名詞句", "The team led an outbreak investigation at the local school.", "保健", "850"),
    ("contact tracing", "接触者追跡", "名詞句", "Contact tracing was used to identify who had been exposed.", "保健", "800"),
    ("health disparity", "健康格差", "名詞句", "The report highlighted a health disparity between rural and urban areas.", "保健", "850"),
    ("social determinants of health", "健康の社会的決定要因", "名詞句", "Income and education are important social determinants of health.", "保健", "950"),
    ("health literacy", "ヘルスリテラシー", "名詞句", "Low health literacy can make it hard for patients to follow treatment plans.", "保健", "850"),
    ("preventive medicine", "予防医学", "名詞句", "Preventive medicine focuses on stopping disease before it starts.", "保健", "800"),
    ("primary prevention", "一次予防", "名詞句", "Vaccination is a classic example of primary prevention.", "保健", "850"),
    ("secondary prevention", "二次予防", "名詞句", "Cancer screening is a form of secondary prevention.", "保健", "850"),
    ("tertiary prevention", "三次予防", "名詞句", "Rehabilitation after a stroke is an example of tertiary prevention.", "保健", "900"),
    ("risk factor", "リスク要因", "名詞句", "Smoking is a major risk factor for heart disease.", "保健", "700"),
    ("at-risk population", "リスクのある人口集団", "名詞句", "The clinic offers free screenings for at-risk populations.", "保健", "800"),
    ("health promotion", "健康増進", "名詞句", "The city launched a health promotion campaign about diet and exercise.", "保健", "750"),
    ("community health", "地域保健", "名詞句", "She works as a community health worker in a rural area.", "保健", "700"),
    ("occupational health", "産業保健", "名詞句", "Occupational health specialists assess safety risks at the factory.", "保健", "800"),
    ("environmental health", "環境保健", "名詞句", "Environmental health experts study how pollution affects public health.", "保健", "800"),
    ("health policy", "保健政策", "名詞句", "The government revised its health policy after the pandemic.", "保健", "750"),
    ("universal health coverage", "国民皆保険・ユニバーサルヘルスカバレッジ", "名詞句", "The country aims to achieve universal health coverage by 2030.", "保健", "900"),
    ("health equity", "健康の公平性", "名詞句", "Health equity means everyone has a fair chance to be healthy.", "保健", "850"),
    ("chronic disease management", "慢性疾患管理", "名詞句", "The clinic offers a program for chronic disease management.", "保健", "800"),
    ("lifestyle-related disease", "生活習慣病", "名詞句", "Type 2 diabetes is often classified as a lifestyle-related disease.", "保健", "800"),
    ("sedentary lifestyle", "座りがちな生活習慣", "名詞句", "A sedentary lifestyle increases the risk of heart disease.", "保健", "750"),
    ("wellness program", "ウェルネスプログラム", "名詞句", "The company introduced a wellness program to reduce employee stress.", "保健", "700"),
    ("mental health awareness", "メンタルヘルスへの理解・意識", "名詞句", "The school held an event to raise mental health awareness.", "保健", "750"),
    ("stress management", "ストレス管理", "名詞句", "Stress management techniques include deep breathing and exercise.", "保健", "650"),
    ("work-life balance", "ワークライフバランス", "名詞句", "Poor work-life balance can negatively affect both mental and physical health.", "保健", "700"),
    ("health screening program", "健康診断プログラム", "名詞句", "The company runs an annual health screening program for employees.", "保健", "750"),
    ("biostatistics", "生物統計学", "名詞", "Biostatistics is used to analyze data from clinical trials.", "保健", "950"),
]

PHRASES: list[tuple[str, str]] = [
    ("Can you check his vital signs?", "彼のバイタルサインを確認してもらえますか？"),
    ("I need to update the care plan.", "ケアプランを更新する必要があります。"),
    ("Let's do a hand-off to the next shift.", "次のシフトへ申し送りをしましょう。"),
    ("What's his blood pressure reading?", "彼の血圧の数値はいくつですか？"),
    ("The patient's oxygen saturation is dropping.", "患者の酸素飽和度が下がっています。"),
    ("Please put on your PPE before entering the room.", "部屋に入る前にPPEを着用してください。"),
    ("We need to start an IV drip right away.", "すぐに点滴を開始する必要があります。"),
    ("Has the patient been given informed consent?", "患者にインフォームドコンセントは取られましたか？"),
    ("I'll page the charge nurse.", "リーダー看護師を呼び出します。"),
    ("Let's reposition him to prevent a pressure ulcer.", "褥瘡予防のために体位を変えましょう。"),
    ("The wound dressing needs to be changed.", "創傷処置(包帯交換)が必要です。"),
    ("Can someone call a code blue?", "誰かコードブルーを呼んでください。"),
    ("Please remember to wash your hands between patients.", "患者ごとに手を洗うのを忘れないでください。"),
    ("We're short-staffed on this shift.", "今回のシフトは人手が足りません。"),
    ("I'm going over the discharge instructions with the family.", "ご家族に退院指導の説明をしています。"),
    ("This patient is a high fall risk.", "この患者さんは転倒リスクが高いです。"),
    ("Let's schedule a follow-up health screening.", "フォローアップの健康診断を予約しましょう。"),
    ("We're conducting contact tracing for this outbreak.", "この感染拡大について接触者追跡を行っています。"),
    ("Early detection through screening saves lives.", "検診による早期発見は命を救います。"),
    ("The clinic focuses on preventive care for the community.", "このクリニックは地域の予防医療に力を入れています。"),
]


def main() -> int:
    with db() as conn:
        existing_words = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added_w = skipped_w = 0
        added_nursing = added_health = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing_words:
                skipped_w += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing_words.add(en.lower())
            added_w += 1
            if domain == "看護学":
                added_nursing += 1
            elif domain == "保健":
                added_health += 1

        existing_phrases = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        added_p = skipped_p = 0
        for en, ja in PHRASES:
            if en.lower() in existing_phrases:
                skipped_p += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, '看護・医療現場の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            added_p += 1

    print(
        f"words: +{added_w} (看護学 +{added_nursing}, 保健 +{added_health}) "
        f"(skipped {skipped_w})"
    )
    print(f"phrases: +{added_p} (skipped {skipped_p})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
