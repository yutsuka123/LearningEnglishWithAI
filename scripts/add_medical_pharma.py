# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""医療(病名)・医療(症状)・薬学(一般薬/処方薬/専門他)の語彙拡充、authored by
Claude(2026-09-01・ユーザー要望「病名は大きい病気からちょっとした風邪まで
網羅、三大成人病・各種癌・難病、他網羅」「薬学は一般/処方が少ない、常備薬から
各病気の処方・投与まで」)。

投入前に本番の既存語彙(5ドメイン計323語)を全件確認し、重複しないものだけを
選定した:
  - 医療(病名)172件 → 難病(ALS/多発性硬化症等)・心血管系(脳梗塞等)・
    未収録のがん種(精巣がん等)・身近だが未収録の疾患(花粉症等)を追加。
  - 医療(症状)71件 → cough/headache/vomiting等、基礎的な症状語が
    多数未収録だったため追加(disease側の重症疾患は既にsymptom側に
    混在済みのため触れない・ドメイン再編は別タスク)。
  - 薬学(一般薬)32件・薬学(処方薬)17件・薬学(専門他)16件 → 常備薬全般、
    主要な病気ごとの処方薬クラス(スタチン・ACE阻害薬等)、投与経路・
    薬物動態関連語を追加。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words`
table (既存の別ドメインにある語は自動的にスキップされる)。

Run:  python scripts/add_medical_pharma.py
仕上げ: 投入後に `python scripts/relevel.py` で難易度を再確認、
        続けて `scripts/build_details.py` / `scripts/build_audio.py` を
        通常のセッション内カデンスで少しずつ回してdetail/音声を埋める。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DISEASE = "医療(病名)"
SYMPTOM = "医療(症状)"
OTC = "薬学(一般薬)"
RX = "薬学(処方薬)"
PHARM_OTHER = "薬学(専門他)"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # === 医療(病名): 難病(指定難病等・よく知られたもの) ===
    ("amyotrophic lateral sclerosis", "筋萎縮性側索硬化症(ALS)", "名詞", "ALS gradually weakens the muscles used for voluntary movement.", DISEASE, "950"),
    ("multiple sclerosis", "多発性硬化症", "名詞", "Multiple sclerosis damages the protective covering of nerve fibers in the brain and spinal cord.", DISEASE, "900"),
    ("myasthenia gravis", "重症筋無力症", "名詞", "Myasthenia gravis causes muscle weakness that worsens with activity and improves with rest.", DISEASE, "950"),
    ("Huntington's disease", "ハンチントン病", "名詞", "Huntington's disease is an inherited disorder that causes nerve cells in the brain to break down over time.", DISEASE, "950"),
    ("muscular dystrophy", "筋ジストロフィー", "名詞", "Muscular dystrophy causes progressive weakness and loss of muscle mass.", DISEASE, "850"),
    ("systemic lupus erythematosus", "全身性エリテマトーデス(ループス)", "名詞", "Systemic lupus erythematosus can cause the immune system to attack many different organs.", DISEASE, "950"),
    ("ulcerative colitis", "潰瘍性大腸炎", "名詞", "Ulcerative colitis causes long-lasting inflammation and ulcers in the digestive tract.", DISEASE, "850"),
    ("Behcet's disease", "ベーチェット病", "名詞", "Behcet's disease can cause mouth sores, eye inflammation, and skin lesions.", DISEASE, "950"),
    ("Guillain-Barre syndrome", "ギラン・バレー症候群", "名詞", "Guillain-Barre syndrome is a rare disorder in which the immune system attacks the peripheral nerves.", DISEASE, "950"),
    ("sarcoidosis", "サルコイドーシス", "名詞", "Sarcoidosis causes tiny clumps of inflammatory cells to form in the lungs and other organs.", DISEASE, "950"),
    ("Marfan syndrome", "マルファン症候群", "名詞", "Marfan syndrome is a genetic disorder that affects the body's connective tissue.", DISEASE, "950"),
    ("Wilson's disease", "ウィルソン病", "名詞", "Wilson's disease causes copper to build up in the liver, brain, and other organs.", DISEASE, "950"),
    ("hemochromatosis", "ヘモクロマトーシス(鉄過剰症)", "名詞", "Hemochromatosis causes the body to absorb too much iron from food.", DISEASE, "950"),
    ("amyloidosis", "アミロイドーシス", "名詞", "Amyloidosis occurs when an abnormal protein builds up in organs and impairs their function.", DISEASE, "950"),
    ("polycystic kidney disease", "多発性嚢胞腎", "名詞", "Polycystic kidney disease causes numerous fluid-filled cysts to develop in the kidneys.", DISEASE, "900"),
    ("sickle cell disease", "鎌状赤血球症", "名詞", "Sickle cell disease causes red blood cells to become rigid and shaped like a crescent.", DISEASE, "850"),
    ("thalassemia", "サラセミア(地中海貧血)", "名詞", "Thalassemia is an inherited blood disorder that causes the body to make less hemoglobin than normal.", DISEASE, "900"),
    ("cystic fibrosis", "嚢胞性線維症", "名詞", "Cystic fibrosis causes thick, sticky mucus to build up in the lungs and digestive system.", DISEASE, "900"),
    ("primary biliary cholangitis", "原発性胆汁性胆管炎", "名詞", "Primary biliary cholangitis slowly destroys the small bile ducts in the liver.", DISEASE, "950"),
    ("aplastic anemia", "再生不良性貧血", "名詞", "Aplastic anemia occurs when the bone marrow fails to produce enough new blood cells.", DISEASE, "900"),
    ("idiopathic pulmonary fibrosis", "特発性肺線維症", "名詞", "Idiopathic pulmonary fibrosis causes scar tissue to form in the lungs for an unknown reason.", DISEASE, "950"),
    ("Sjogren's syndrome", "シェーグレン症候群", "名詞", "Sjogren's syndrome most often affects the glands that produce tears and saliva.", DISEASE, "950"),
    ("scleroderma", "強皮症", "名詞", "Scleroderma causes the skin and connective tissue to thicken and harden.", DISEASE, "900"),
    ("myelodysplastic syndrome", "骨髄異形成症候群", "名詞", "Myelodysplastic syndrome occurs when the bone marrow produces blood cells that are abnormal or immature.", DISEASE, "950"),
    ("Charcot-Marie-Tooth disease", "シャルコー・マリー・トゥース病", "名詞", "Charcot-Marie-Tooth disease damages the peripheral nerves and causes muscle weakness in the feet and hands.", DISEASE, "950"),
    ("moyamoya disease", "もやもや病", "名詞", "Moyamoya disease narrows the arteries at the base of the brain, increasing the risk of stroke.", DISEASE, "900"),
    ("Kawasaki disease", "川崎病", "名詞", "Kawasaki disease causes inflammation in the blood vessels and mainly affects young children.", DISEASE, "850"),
    ("Werner syndrome", "ウェルナー症候群", "名詞", "Werner syndrome is a rare disorder that causes the body to age much faster than normal.", DISEASE, "950"),
    # === 医療(病名): 心血管・脳血管疾患(三大成人病関連) ===
    ("heart disease", "心臓病", "名詞", "Regular exercise and a balanced diet help lower the risk of heart disease.", DISEASE, "500"),
    ("cerebrovascular disease", "脳血管疾患", "名詞", "Cerebrovascular disease is one of the leading causes of death worldwide.", DISEASE, "800"),
    ("cerebral infarction", "脳梗塞", "名詞", "A cerebral infarction occurs when blood flow to part of the brain is blocked.", DISEASE, "750"),
    ("cerebral hemorrhage", "脳出血", "名詞", "A cerebral hemorrhage happens when a blood vessel in the brain bursts.", DISEASE, "750"),
    ("subarachnoid hemorrhage", "くも膜下出血", "名詞", "A subarachnoid hemorrhage often causes a sudden, severe headache.", DISEASE, "900"),
    ("transient ischemic attack", "一過性脳虚血発作", "名詞", "A transient ischemic attack causes stroke-like symptoms that usually resolve within 24 hours.", DISEASE, "900"),
    ("aortic aneurysm", "大動脈瘤", "名詞", "An aortic aneurysm can be life-threatening if the weakened artery wall ruptures.", DISEASE, "850"),
    ("aortic dissection", "大動脈解離", "名詞", "An aortic dissection causes a tear in the inner layer of the body's main artery.", DISEASE, "900"),
    ("peripheral artery disease", "末梢動脈疾患", "名詞", "Peripheral artery disease reduces blood flow to the limbs, most often the legs.", DISEASE, "900"),
    ("cardiomyopathy", "心筋症", "名詞", "Cardiomyopathy makes it harder for the heart to pump blood to the rest of the body.", DISEASE, "900"),
    ("pericarditis", "心膜炎", "名詞", "Pericarditis is inflammation of the thin sac surrounding the heart.", DISEASE, "900"),
    ("endocarditis", "心内膜炎", "名詞", "Endocarditis is a serious infection of the inner lining of the heart's chambers and valves.", DISEASE, "900"),
    # === 医療(病名): 未収録のがん種 ===
    ("testicular cancer", "精巣がん", "名詞", "Testicular cancer is one of the most treatable cancers when caught early.", DISEASE, "800"),
    ("oral cancer", "口腔がん", "名詞", "Oral cancer can develop on the lips, tongue, or the lining of the mouth.", DISEASE, "800"),
    ("laryngeal cancer", "喉頭がん", "名詞", "Laryngeal cancer often causes a persistent hoarse voice.", DISEASE, "850"),
    ("endometrial cancer", "子宮体がん", "名詞", "Endometrial cancer begins in the lining of the uterus.", DISEASE, "850"),
    ("gallbladder cancer", "胆嚢がん", "名詞", "Gallbladder cancer is often found late because early symptoms are rare.", DISEASE, "900"),
    ("mesothelioma", "中皮腫", "名詞", "Mesothelioma is a rare cancer strongly linked to long-term asbestos exposure.", DISEASE, "950"),
    ("glioblastoma", "膠芽腫", "名詞", "Glioblastoma is one of the most aggressive types of brain tumor.", DISEASE, "950"),
    ("Hodgkin lymphoma", "ホジキンリンパ腫", "名詞", "Hodgkin lymphoma often first appears as a painless swelling in the lymph nodes.", DISEASE, "900"),
    ("non-Hodgkin lymphoma", "非ホジキンリンパ腫", "名詞", "Non-Hodgkin lymphoma covers a large group of cancers that start in the lymphatic system.", DISEASE, "900"),
    ("retinoblastoma", "網膜芽細胞腫", "名詞", "Retinoblastoma is a rare eye cancer that mostly affects young children.", DISEASE, "950"),
    ("neuroblastoma", "神経芽細胞腫", "名詞", "Neuroblastoma most commonly develops in infants and young children.", DISEASE, "950"),
    ("chronic myeloid leukemia", "慢性骨髄性白血病", "名詞", "Chronic myeloid leukemia progresses more slowly than most other types of leukemia.", DISEASE, "900"),
    ("acute lymphoblastic leukemia", "急性リンパ性白血病", "名詞", "Acute lymphoblastic leukemia is the most common type of cancer in children.", DISEASE, "900"),
    # === 医療(病名): 身近だが未収録の疾患 ===
    ("hay fever", "花粉症", "名詞", "Many people in Japan take medicine for hay fever every spring.", DISEASE, "500"),
    ("canker sore", "口内炎", "名詞", "A canker sore made it painful for him to eat spicy food.", DISEASE, "550"),
    ("stye", "ものもらい", "名詞", "A stye is a small, painful lump that forms near the edge of the eyelid.", DISEASE, "700"),
    ("tennis elbow", "テニス肘", "名詞", "Tennis elbow causes pain on the outside of the elbow from repetitive arm motion.", DISEASE, "650"),
    ("frozen shoulder", "四十肩・五十肩", "名詞", "Frozen shoulder makes it difficult to move the shoulder joint without pain.", DISEASE, "650"),
    ("carpal tunnel syndrome", "手根管症候群", "名詞", "Carpal tunnel syndrome causes numbness and tingling in the hand and fingers.", DISEASE, "800"),
    ("plantar fasciitis", "足底筋膜炎", "名詞", "Plantar fasciitis causes stabbing heel pain, especially with the first steps in the morning.", DISEASE, "850"),
    ("pinworm infection", "蟯虫症", "名詞", "A pinworm infection is common in young children and causes itching around the anus.", DISEASE, "850"),
    ("otitis externa", "外耳炎", "名詞", "Otitis externa, sometimes called swimmer's ear, is inflammation of the outer ear canal.", DISEASE, "800"),
    ("food allergy", "食物アレルギー", "名詞", "A food allergy can cause reactions ranging from mild hives to a life-threatening emergency.", DISEASE, "500"),

    # === 医療(症状): 基礎的な症状語 ===
    ("cough", "咳", "名詞", "His cough kept him awake most of the night.", SYMPTOM, "350"),
    ("headache", "頭痛", "名詞", "She took some medicine for her headache.", SYMPTOM, "350"),
    ("vomit", "嘔吐する", "動詞", "The child vomited twice after eating lunch.", SYMPTOM, "500"),
    ("vomiting", "嘔吐", "名詞", "Vomiting and diarrhea are common symptoms of food poisoning.", SYMPTOM, "550"),
    ("sore throat", "のどの痛み", "名詞", "A sore throat is often one of the first signs of a cold.", SYMPTOM, "400"),
    ("runny nose", "鼻水", "名詞", "A runny nose and sneezing are classic symptoms of hay fever.", SYMPTOM, "400"),
    ("stuffy nose", "鼻づまり", "名詞", "A stuffy nose made it hard for him to breathe through his nose.", SYMPTOM, "450"),
    ("sneeze", "くしゃみをする", "動詞", "She sneezed several times because of the pollen in the air.", SYMPTOM, "450"),
    ("sneezing", "くしゃみ", "名詞", "Frequent sneezing can be a sign of a seasonal allergy.", SYMPTOM, "450"),
    ("chills", "悪寒", "名詞", "He had chills and a high fever the night before he was diagnosed with the flu.", SYMPTOM, "600"),
    ("sweating", "発汗", "名詞", "Sudden, heavy sweating can sometimes be a warning sign of a heart problem.", SYMPTOM, "550"),
    ("fatigue", "倦怠感・疲労感", "名詞", "Constant fatigue is one of the most common symptoms doctors hear about.", SYMPTOM, "550"),
    ("shortness of breath", "息切れ", "名詞", "She felt shortness of breath after climbing just one flight of stairs.", SYMPTOM, "650"),
    ("chest pain", "胸の痛み", "名詞", "Sudden chest pain is one of the most common reasons people visit the emergency room.", SYMPTOM, "550"),
    ("abdominal pain", "腹痛", "名詞", "The abdominal pain got worse whenever she pressed on her stomach.", SYMPTOM, "550"),
    ("back pain", "腰痛・背中の痛み", "名詞", "Sitting for long hours at a desk can lead to chronic back pain.", SYMPTOM, "450"),
    ("joint pain", "関節痛", "名詞", "Joint pain in the knees often gets worse in cold weather.", SYMPTOM, "600"),
    ("muscle pain", "筋肉痛", "名詞", "He felt muscle pain in his legs the day after the marathon.", SYMPTOM, "500"),
    ("tremor", "震え・振戦", "名詞", "A fine hand tremor is one of the early signs of Parkinson's disease.", SYMPTOM, "750"),
    ("palpitations", "動悸", "名詞", "She went to the clinic after experiencing sudden palpitations.", SYMPTOM, "750"),
    ("loss of appetite", "食欲不振", "名詞", "A loss of appetite that lasts for weeks can be a sign of a deeper problem.", SYMPTOM, "600"),
    ("weight loss", "体重減少", "名詞", "Unexplained weight loss is a symptom doctors take seriously.", SYMPTOM, "450"),
    ("weight gain", "体重増加", "名詞", "The medication listed weight gain as a possible side effect.", SYMPTOM, "450"),
    ("itching", "かゆみ", "名詞", "The rash was accompanied by intense itching.", SYMPTOM, "500"),
    ("itchy", "かゆい", "形容詞", "His skin felt itchy after the insect bite.", SYMPTOM, "450"),
    ("bloating", "腹部膨満感・お腹の張り", "名詞", "Bloating is a feeling of fullness or tightness in the abdomen.", SYMPTOM, "700"),
    ("heartburn", "胸やけ", "名詞", "Spicy food often gives him heartburn late at night.", SYMPTOM, "600"),
    ("jaundice", "黄疸", "名詞", "Jaundice causes the skin and eyes to take on a yellowish color.", SYMPTOM, "800"),
    ("edema", "浮腫(むくみ)", "名詞", "Edema in the legs can be a sign of poor circulation.", SYMPTOM, "800"),
    ("malaise", "倦怠感・不快感", "名詞", "A general sense of malaise is often the first sign that something is wrong.", SYMPTOM, "850"),
    ("lethargy", "無気力・嗜眠", "名詞", "Extreme lethargy kept her in bed for most of the day.", SYMPTOM, "800"),
    ("stiff neck", "首のこり・項部硬直", "名詞", "A stiff neck combined with a fever can be a warning sign of meningitis.", SYMPTOM, "650"),
    ("cold sweat", "冷や汗", "名詞", "He broke out in a cold sweat just before he fainted.", SYMPTOM, "650"),
    ("wheezing", "喘鳴(ぜーぜーという呼吸音)", "名詞", "Wheezing is a common symptom of asthma attacks.", SYMPTOM, "700"),
    ("difficulty breathing", "呼吸困難", "名詞", "Difficulty breathing is one of the most urgent symptoms to report to a doctor.", SYMPTOM, "650"),
    ("blood in urine", "血尿", "名詞", "Blood in urine can be a sign of a problem in the kidneys or bladder.", SYMPTOM, "600"),
    ("blood in stool", "血便", "名詞", "Blood in stool can be caused by conditions ranging from hemorrhoids to colon cancer.", SYMPTOM, "600"),
    ("loss of consciousness", "意識消失", "名詞", "A sudden loss of consciousness is a medical emergency.", SYMPTOM, "750"),
    ("blurred vision", "かすみ目", "名詞", "Blurred vision can sometimes be an early sign of diabetes.", SYMPTOM, "650"),
    ("loose stool", "軟便", "名詞", "Loose stool for more than a couple of days can lead to dehydration.", SYMPTOM, "550"),

    # === 薬学(一般薬): 常備薬・市販薬 ===
    ("painkiller", "鎮痛剤", "名詞", "She took a painkiller for her headache.", OTC, "450"),
    ("analgesic", "鎮痛薬", "名詞", "The doctor recommended a mild analgesic for the muscle pain.", OTC, "700"),
    ("antipyretic", "解熱剤", "名詞", "An antipyretic can help bring down a high fever.", OTC, "700"),
    ("anti-inflammatory drug", "抗炎症薬", "名詞", "An anti-inflammatory drug reduced the swelling in his knee.", OTC, "750"),
    ("antifungal cream", "抗真菌クリーム", "名詞", "She applied antifungal cream to treat her athlete's foot.", OTC, "750"),
    ("antibiotic ointment", "抗生物質軟膏", "名詞", "He put antibiotic ointment on the cut to prevent infection.", OTC, "700"),
    ("oral rehydration solution", "経口補水液", "名詞", "An oral rehydration solution helps replace fluids lost to vomiting and diarrhea.", OTC, "750"),
    ("motion sickness medicine", "乗り物酔いの薬", "名詞", "She took motion sickness medicine before the long bus ride.", OTC, "550"),
    ("sleep aid", "睡眠改善薬(市販の睡眠補助薬)", "名詞", "He occasionally uses a sleep aid when he can't fall asleep.", OTC, "650"),
    ("vitamin supplement", "ビタミン剤・サプリメント", "名詞", "She takes a vitamin supplement every morning with breakfast.", OTC, "500"),
    ("herbal medicine", "漢方薬・生薬", "名詞", "Herbal medicine is still widely used alongside modern treatment in Japan.", OTC, "600"),
    ("cold and flu medicine", "総合感冒薬", "名詞", "He bought some cold and flu medicine at the drugstore.", OTC, "550"),
    ("eyewash", "洗眼薬", "名詞", "She used eyewash to rinse the dust out of her eye.", OTC, "650"),
    ("insect bite cream", "虫刺されの薬", "名詞", "Insect bite cream helped ease the itching from the mosquito bites.", OTC, "600"),
    ("adhesive bandage", "絆創膏", "名詞", "He put an adhesive bandage on the small cut on his finger.", OTC, "400"),
    ("antiseptic wipe", "消毒用ウェットティッシュ", "名詞", "She cleaned the wound with an antiseptic wipe before applying the bandage.", OTC, "600"),
    ("hand sanitizer", "手指消毒液", "名詞", "Hand sanitizer is placed at the entrance of most clinics.", OTC, "500"),
    ("throat spray", "のどスプレー", "名詞", "A throat spray can numb the pain of a sore throat for a short while.", OTC, "600"),
    ("first aid kit", "救急箱", "名詞", "Many households keep a first aid kit within easy reach.", OTC, "450"),
    ("cooling gel patch", "冷却シート・ジェルパッド", "名詞", "She stuck a cooling gel patch on her forehead to help with the fever.", OTC, "650"),

    # === 薬学(処方薬): 主要な病気ごとの処方薬クラス ===
    ("antibiotic", "抗生物質", "名詞", "The doctor prescribed an antibiotic to treat the bacterial infection.", RX, "500"),
    ("statin", "スタチン(脂質異常症治療薬)", "名詞", "A statin can help lower cholesterol and reduce the risk of heart disease.", RX, "800"),
    ("beta blocker", "ベータ遮断薬", "名詞", "A beta blocker slows the heart rate and lowers blood pressure.", RX, "850"),
    ("ACE inhibitor", "ACE阻害薬", "名詞", "An ACE inhibitor is commonly prescribed to treat high blood pressure.", RX, "900"),
    ("calcium channel blocker", "カルシウム拮抗薬", "名詞", "A calcium channel blocker relaxes the blood vessels to lower blood pressure.", RX, "900"),
    ("diuretic", "利尿薬", "名詞", "A diuretic helps the body get rid of excess salt and water.", RX, "800"),
    ("insulin", "インスリン", "名詞", "People with type 1 diabetes need to inject insulin every day.", RX, "600"),
    ("oral hypoglycemic agent", "経口血糖降下薬", "名詞", "An oral hypoglycemic agent helps control blood sugar in type 2 diabetes.", RX, "900"),
    ("SSRI", "SSRI(選択的セロトニン再取り込み阻害薬)", "名詞", "An SSRI is often the first medication tried for depression.", RX, "900"),
    ("benzodiazepine", "ベンゾジアゼピン系薬剤", "名詞", "A benzodiazepine is sometimes prescribed for short-term anxiety relief.", RX, "900"),
    ("antipsychotic", "抗精神病薬", "名詞", "An antipsychotic can help manage the symptoms of schizophrenia.", RX, "850"),
    ("mood stabilizer", "気分安定薬", "名詞", "A mood stabilizer is often used to treat bipolar disorder.", RX, "850"),
    ("corticosteroid", "副腎皮質ステロイド", "名詞", "A corticosteroid can quickly reduce severe inflammation.", RX, "800"),
    ("immunosuppressant", "免疫抑制剤", "名詞", "Patients who receive an organ transplant must take an immunosuppressant for life.", RX, "850"),
    ("anticoagulant", "抗凝固薬", "名詞", "An anticoagulant helps prevent dangerous blood clots from forming.", RX, "800"),
    ("antiplatelet drug", "抗血小板薬", "名詞", "An antiplatelet drug reduces the risk of stroke by keeping the blood from clotting easily.", RX, "850"),
    ("targeted therapy drug", "分子標的薬", "名詞", "A targeted therapy drug attacks specific molecules involved in cancer growth.", RX, "900"),
    ("biologic drug", "生物学的製剤", "名詞", "A biologic drug is often used to treat severe rheumatoid arthritis.", RX, "900"),
    ("antiviral drug", "抗ウイルス薬", "名詞", "An antiviral drug can shorten the duration of the flu if taken early.", RX, "700"),
    ("antifungal drug", "抗真菌薬", "名詞", "An antifungal drug is used to treat infections caused by fungi.", RX, "800"),
    ("bronchodilator", "気管支拡張薬", "名詞", "A bronchodilator opens the airways to make breathing easier during an asthma attack.", RX, "850"),
    ("inhaled corticosteroid", "吸入ステロイド薬", "名詞", "An inhaled corticosteroid is used daily to control chronic asthma.", RX, "900"),
    ("thyroid hormone replacement", "甲状腺ホルモン補充薬", "名詞", "Thyroid hormone replacement is a lifelong treatment for hypothyroidism.", RX, "900"),
    ("hormone replacement therapy", "ホルモン補充療法", "名詞", "Hormone replacement therapy can ease the symptoms of menopause.", RX, "850"),
    ("opioid", "オピオイド(麻薬性鎮痛薬)", "名詞", "An opioid is a powerful painkiller that carries a real risk of dependence.", RX, "800"),
    ("vaccine", "ワクチン", "名詞", "The vaccine is given in two doses several weeks apart.", RX, "450"),
    ("biosimilar", "バイオシミラー(バイオ後続品)", "名詞", "A biosimilar works like the original biologic drug but usually costs less.", RX, "950"),

    # === 薬学(専門他): 投与経路・薬物動態・その他 ===
    ("oral administration", "経口投与", "名詞", "Oral administration is the most common way to take medicine.", PHARM_OTHER, "750"),
    ("intravenous injection", "静脈注射", "名詞", "An intravenous injection delivers medicine directly into the bloodstream.", PHARM_OTHER, "700"),
    ("intramuscular injection", "筋肉注射", "名詞", "The nurse gave the vaccine as an intramuscular injection.", PHARM_OTHER, "750"),
    ("subcutaneous injection", "皮下注射", "名詞", "Insulin is usually given as a subcutaneous injection.", PHARM_OTHER, "800"),
    ("topical application", "外用・局所塗布", "名詞", "Topical application of the cream avoids many of the side effects of oral medicine.", PHARM_OTHER, "800"),
    ("route of administration", "投与経路", "名詞", "The route of administration can change how quickly a drug takes effect.", PHARM_OTHER, "900"),
    ("loading dose", "負荷投与量", "名詞", "A loading dose is given to quickly reach an effective drug level in the blood.", PHARM_OTHER, "900"),
    ("maintenance dose", "維持投与量", "名詞", "After the loading dose, the patient is switched to a lower maintenance dose.", PHARM_OTHER, "900"),
    ("titration", "用量調節", "名詞", "Careful titration of the dose reduced the patient's side effects.", PHARM_OTHER, "900"),
    ("adverse drug reaction", "薬物有害反応", "名詞", "The rash turned out to be an adverse drug reaction to the new antibiotic.", PHARM_OTHER, "850"),
    ("drug allergy", "薬物アレルギー", "名詞", "He carries a card listing his drug allergy in case of an emergency.", PHARM_OTHER, "700"),
    ("off-label use", "適応外使用", "名詞", "Off-label use means prescribing a drug for a purpose not officially approved.", PHARM_OTHER, "900"),
    ("package insert", "添付文書", "名詞", "The package insert lists a drug's dosage, side effects, and precautions.", PHARM_OTHER, "850"),
    ("black box warning", "黒枠警告(最重要警告表示)", "名詞", "A black box warning is the strongest safety warning a drug label can carry.", PHARM_OTHER, "950"),
    ("polypharmacy", "多剤併用", "名詞", "Polypharmacy in elderly patients increases the risk of dangerous drug interactions.", PHARM_OTHER, "900"),
    ("drug metabolism", "薬物代謝", "名詞", "Drug metabolism mostly takes place in the liver.", PHARM_OTHER, "850"),
    ("dosage form", "剤形", "名詞", "The same medicine is often available in more than one dosage form, such as tablets or syrup.", PHARM_OTHER, "850"),
]


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        by_domain: dict[str, int] = {}
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing:
                skipped += 1
                print(f"  [skip: 既存] {en}")
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing.add(en.lower())
            by_domain[domain] = by_domain.get(domain, 0) + 1
            added += 1

    print(f"\nwords: +{added} (skipped {skipped})")
    for d, c in sorted(by_domain.items()):
        print(f"  {d}: +{c}")
    with db() as conn:
        print("total words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
