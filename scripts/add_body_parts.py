# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a new "身体" domain/scene: vocabulary and phrases for body-part
terms used in real clinical conversation — what a patient says to describe
symptoms and what a doctor says to explain them — authored by Claude
(2026-08-10・ユーザー要望).

対象語彙: 内臓・器官(esophagus, trachea, bronchus, larynx, pharynx, colon,
rectum, tonsil, thyroid gland, adrenal gland, sinus, windpipe)、骨格の主要
部位を口語＋一般名で(collarbone, shoulder blade, kneecap, tibia, fibula,
vertebra ※分類学的な関節の種類・体軸/体肢骨格などは扱わない)、目・耳・
感覚器(cornea, retina, pupil, eardrum, optic nerve, sciatic nerve)、皮膚・
その他(scalp, eyelid, eyelash, eyebrow, nostril, earlobe, fingernail,
toenail, knuckle, shin, heel, sole, armpit)、口語的な部位表現(lower back,
upper arm, forearm, belly button, navel, groin, buttock, Achilles tendon)。
既存`医療`ドメイン190語(abdomen/ankle/artery/bladder/chest/gallbladder/
hip/joint/knee/muscle/nerve/palm/rib/spine/skull/thigh/throat/tongue/vein/
waist/wrist等)、および同時進行の`解剖学`ドメイン(scripts/add_anatomy.py:
femur/humerus/clavicle/scapula/sternum/patella/mandible/cranium・関節の
分類・結合組織・解剖学的方向用語等の学術用語)とは重複しない。骨や関節の
分類学的な呼称は解剖学ドメインに譲り、ここでは患者・医者が診察室で実際に
口にする部位名(専門用語と口語表現の両方)のみを扱う。

なお、DB全体を確認したところ"diaphragm"(建築・建物ドメインで構造用語として
既存)と"appendix"(論文・学術ドメインで「付録」の意味として既存)は英単語の
綴りが医学用語と衝突するため採用を避け、代わりに"windpipe"(気管の口語)と
"sinus"(副鼻腔)を採用した。

フレーズは診察室で患者が症状を訴える・医者が部位を指し示しながら説明する
場面の自然な英語表現("Where does it hurt?" "It hurts here." など)。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_body_parts.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 内臓・器官 ---
    ("esophagus", "食道", "名詞", "Food travels from the mouth to the stomach through the esophagus.", "身体", "750"),
    ("windpipe", "気管(口語)", "名詞", "The windpipe carries air down to your lungs.", "身体", "500"),
    ("trachea", "気管", "名詞", "The trachea splits into two bronchi just above the lungs.", "身体", "750"),
    ("bronchus", "気管支", "名詞", "The doctor heard a slight wheeze in her left bronchus.", "身体", "800"),
    ("larynx", "喉頭", "名詞", "The larynx contains the vocal cords.", "身体", "800"),
    ("pharynx", "咽頭", "名詞", "The pharynx connects the back of the mouth and nose to the esophagus.", "身体", "800"),
    ("colon", "結腸", "名詞", "The doctor recommended a colon screening after age fifty.", "身体", "750"),
    ("rectum", "直腸", "名詞", "The exam included a check of the rectum.", "身体", "800"),
    ("tonsil", "扁桃腺", "名詞", "Her tonsils were swollen and red.", "身体", "600"),
    ("thyroid gland", "甲状腺", "名詞", "The thyroid gland helps regulate your metabolism.", "身体", "750"),
    ("adrenal gland", "副腎", "名詞", "The adrenal glands release hormones when you're under stress.", "身体", "800"),
    ("sinus", "副鼻腔", "名詞", "My sinuses feel completely blocked when I have a cold.", "身体", "550"),
    # --- 骨格の主要部位(口語＋一般名) ---
    ("collarbone", "鎖骨(口語)", "名詞", "I broke my collarbone in a bike accident.", "身体", "500"),
    ("shoulder blade", "肩甲骨(口語)", "名詞", "I have a tight knot in my shoulder blade.", "身体", "550"),
    ("kneecap", "膝のお皿(口語)", "名詞", "I hit my kneecap on the edge of the table.", "身体", "500"),
    ("tibia", "脛骨", "名詞", "The X-ray showed a hairline fracture in her tibia.", "身体", "700"),
    ("fibula", "腓骨", "名詞", "He fractured his fibula during the soccer game.", "身体", "750"),
    ("vertebra", "椎骨", "名詞", "One vertebra in her lower back is slightly out of alignment.", "身体", "800"),
    # --- 目・耳・感覚器 ---
    ("cornea", "角膜", "名詞", "The cornea is the clear front layer of the eye.", "身体", "800"),
    ("retina", "網膜", "名詞", "A detached retina requires immediate treatment.", "身体", "800"),
    ("pupil", "瞳孔", "名詞", "The doctor shined a light in her eyes to check her pupils.", "身体", "600"),
    ("eardrum", "鼓膜", "名詞", "Loud noises over time can damage your eardrum.", "身体", "600"),
    ("optic nerve", "視神経", "名詞", "The optic nerve carries visual signals from the eye to the brain.", "身体", "800"),
    ("sciatic nerve", "坐骨神経", "名詞", "Pain from the sciatic nerve can run down the back of your leg.", "身体", "800"),
    # --- 皮膚・その他 ---
    ("scalp", "頭皮", "名詞", "My scalp has been itchy for a few days.", "身体", "500"),
    ("eyelid", "まぶた", "名詞", "My eyelid has been swollen since this morning.", "身体", "450"),
    ("eyelash", "まつげ", "名詞", "An eyelash got stuck in my eye.", "身体", "450"),
    ("eyebrow", "眉毛", "名詞", "She has a small scar above her eyebrow.", "身体", "400"),
    ("nostril", "鼻の穴(鼻孔)", "名詞", "One of my nostrils feels completely blocked.", "身体", "500"),
    ("earlobe", "耳たぶ", "名詞", "There's some swelling around my earlobe.", "身体", "450"),
    ("fingernail", "指の爪", "名詞", "I broke a fingernail while gardening.", "身体", "400"),
    ("toenail", "足の爪", "名詞", "My toenail turned dark after I stubbed my toe.", "身体", "450"),
    ("knuckle", "指の関節", "名詞", "My knuckles ache whenever it's cold outside.", "身体", "500"),
    ("shin", "すね", "名詞", "I bruised my shin on the coffee table.", "身体", "450"),
    ("heel", "かかと", "名詞", "My heel hurts every time I take a step.", "身体", "400"),
    ("sole", "足の裏(足底)", "名詞", "There's a painful blister on the sole of my foot.", "身体", "500"),
    ("armpit", "わきの下", "名詞", "I found a small lump under my armpit.", "身体", "450"),
    # --- 口語的な部位表現 ---
    ("lower back", "腰(下背部)", "名詞", "I've had a dull ache in my lower back all week.", "身体", "400"),
    ("upper arm", "二の腕(上腕)", "名詞", "I pulled a muscle in my upper arm at the gym.", "身体", "400"),
    ("forearm", "前腕", "名詞", "There's a rash spreading across my forearm.", "身体", "500"),
    ("belly button", "おへそ(口語)", "名詞", "The rash started right around my belly button.", "身体", "400"),
    ("navel", "へそ", "名詞", "The nurse checked the skin around the navel.", "身体", "550"),
    ("groin", "股関節部・鼠径部", "名詞", "I felt a sharp pain in my groin while running.", "身体", "600"),
    ("buttock", "尻(片方)", "名詞", "He has a large bruise on his left buttock.", "身体", "500"),
    ("achilles tendon", "アキレス腱", "名詞", "She strained her Achilles tendon during the marathon.", "身体", "650"),
]

PHRASES: list[tuple[str, str]] = [
    ("Where does it hurt?", "どこが痛みますか？"),
    ("It hurts here.", "ここが痛いです。"),
    ("Can you press this area for me?", "この部分を押してみてもらえますか？"),
    ("Does it hurt when I press here?", "ここを押すと痛いですか？"),
    ("Can you show me exactly where it hurts?", "正確にどこが痛むか見せてもらえますか？"),
    ("I have a dull ache in my lower back.", "腰に鈍い痛みがあります。"),
    ("My shoulder blade feels really stiff.", "肩甲骨のあたりがとても凝っています。"),
    ("I have a sharp pain in my chest.", "胸に鋭い痛みを感じます。"),
    ("My eyelid has been swollen since this morning.", "今朝からまぶたが腫れています。"),
    ("There's a rash on my forearm.", "前腕に発疹があります。"),
    ("I found a small lump under my armpit.", "わきの下に小さなしこりを見つけました。"),
    ("My throat is sore, especially around my tonsils.", "喉が痛くて、特に扁桃腺のあたりがつらいです。"),
    ("Take a deep breath for me.", "大きく息を吸ってください。"),
    ("I sprained my wrist while playing tennis.", "テニス中に手首をひねりました。"),
    ("The pain spreads from my lower back down my leg.", "腰から脚にかけて痛みが広がります。"),
    ("Can you bend your knee for me?", "膝を曲げてみてください。"),
    ("I have a dull pain around my collarbone.", "鎖骨のあたりが鈍く痛みます。"),
    ("My kneecap feels a little loose.", "膝のお皿がぐらつく感じがします。"),
    ("I stubbed my toe and my toenail is bruised.", "つま先をぶつけて、足の爪が内出血しています。"),
    ("The doctor gently pressed on my abdomen.", "医者はお腹を優しく押しました。"),
    ("I have numbness in my fingertips and knuckles.", "指先と関節にしびれがあります。"),
    ("My heel hurts every time I walk.", "歩くとかかとが痛みます。"),
    ("There's some swelling around my earlobe.", "耳たぶの周りが腫れています。"),
    ("I feel pressure behind my eyes, near my sinuses.", "目の奥、副鼻腔のあたりに圧迫感があります。"),
    ("Please bend forward so I can check your spine.", "脊椎を確認しますので前かがみになってください。"),
    ("I pulled a muscle in my upper arm.", "二の腕の筋肉を痛めました。"),
    ("Does it hurt when you swallow?", "飲み込むときに痛みますか？"),
    ("My scalp has been itchy for a few days.", "数日前から頭皮がかゆいです。"),
    ("I strained my Achilles tendon during the marathon.", "マラソン中にアキレス腱を痛めました。"),
    ("Let's take a closer look at your eye.", "目をもう少し詳しく診てみましょう。"),
]


def main() -> int:
    with db() as conn:
        existing_words = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing_words:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing_words.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")

    with db() as conn:
        existing_phrases = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in existing_phrases:
                p_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, '身体の部位の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
