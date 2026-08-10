# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add to the existing "身体" domain/scene: the most basic, everyday body-part
words that turned out to be **completely missing** from the DB despite being
some of the first words an English learner meets — head, neck, nose, mouth,
hand, tooth, etc. — plus a few adjacent gaps (urinary tract, genitals as
clinical/anatomical vocabulary), authored by Claude (2026-08-10・ユーザー
要望).

## 背景
DB全体を`SELECT english, domain FROM words WHERE LOWER(english) IN
('head','neck','skin','nose','mouth','foot','feet','hand','back',...)`で
確認したところ**1件もヒットしなかった**(「eye」だけ囲碁ドメインに誤ヒット
するが体の部位としての意味ではないため今回も対象外のまま)。既存の`身体`
ドメイン(`scripts/add_body_parts.py`)は臨床的な部位名(esophagus, trachea,
cornea等)中心でlevel 400〜800に偏っており、most basicな部位語が丸ごと
抜けていた。本スクリプトはその穴を埋める第2弾。

対象語彙:
1. **最も基礎的な体の部位**(head, neck, skin, nose, mouth, foot/feet, hand,
   belly, bone, tooth/teeth, finger, thumb, pinky finger, index finger,
   ear, hair, face, arm, leg)。「back」は一般語(戻る/後ろ)と衝突するため
   `back (body part)`という複合見出しにした(DB内に`field (farm)`
   `satellite (moon)`等、同種の曖昧さ回避パターンが既にあることを確認
   済み)。加えてchin/cheek/lips/toe/cheekboneもDB内に皆無だったため
   同カテゴリで追加した。
2. **既存に無い泌尿器・内臓**: urethra, large intestine(既存の"colon"とは
   別見出し)。
3. **生殖器系(泌尿器科・婦人科の症状説明で使う中立的な解剖学用語のみ)**:
   testicle(s), ovary/ovaries, penis, vagina, scrotum, vulva, prostate,
   genitals。**下品・性的な表現は一切使わない**。既存`医療`ドメインに
   すでに`uterus`が収録されていることに倣い、医者が患者を診察・問診する
   際に実際に使う中立的な医学用語として、症状説明の文脈でのみ収録した
   (例文は全て"The doctor examined..."のような臨床的な内容)。なお
   `groin`と`forearm`はDB確認の結果`身体`ドメインに既に存在したため
   本ファイルには含めていない。
4. **体毛**: beard, armpit hair, pubic hair, chest hair(3と同様、中立的な
   語のみ)。
5. **歯**: tooth, teeth(1と重複しないよう1回のみ収録), front tooth, molar,
   wisdom tooth。
6. **その他**: nasal cavity。

フレーズは診察室で患者が症状を伝える・医者が問診する自然な英語表現。
デリケートな話題(泌尿器・生殖器)についても、実際の医療現場で使われる
丁寧・中立的な言い回し("I'd like to discuss a urinary symptom with you
privately." など)にした。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_body_basics.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 最も基礎的な体の部位 ---
    ("head", "頭", "名詞", "I hit my head on the cabinet door.", "身体", "400"),
    ("neck", "首", "名詞", "My neck feels stiff after sleeping in an odd position.", "身体", "400"),
    ("skin", "皮膚", "名詞", "The doctor checked her skin for any unusual marks.", "身体", "400"),
    ("nose", "鼻", "名詞", "My nose has been stuffy since yesterday.", "身体", "350"),
    ("mouth", "口", "名詞", "Open your mouth and say ah.", "身体", "350"),
    ("foot", "足(単数)", "名詞", "I hurt my foot playing soccer.", "身体", "350"),
    ("feet", "足(複数)", "名詞", "My feet are swollen after the long flight.", "身体", "400"),
    ("hand", "手", "名詞", "I cut my hand while chopping vegetables.", "身体", "300"),
    ("back (body part)", "背中", "名詞", "My back hurts when I bend forward.", "身体", "400"),
    ("belly", "お腹・腹", "名詞", "I have a dull pain in my belly.", "身体", "400"),
    ("bone", "骨", "名詞", "The X-ray showed a small crack in the bone.", "身体", "400"),
    ("tooth", "歯(単数)", "名詞", "I have a sharp pain in one tooth.", "身体", "400"),
    ("teeth", "歯(複数)", "名詞", "My teeth are sensitive to cold drinks.", "身体", "400"),
    ("finger", "指(手の指)", "名詞", "I jammed my finger playing basketball.", "身体", "350"),
    ("thumb", "親指", "名詞", "I sprained my thumb playing volleyball.", "身体", "400"),
    ("pinky finger", "小指", "名詞", "My pinky finger feels numb.", "身体", "450"),
    ("index finger", "人差し指", "名詞", "I cut my index finger while cooking.", "身体", "450"),
    ("ear", "耳", "名詞", "I have a sharp pain deep in my ear.", "身体", "350"),
    ("hair", "髪・体毛(総称)", "名詞", "My hair has been falling out more than usual.", "身体", "300"),
    ("face", "顔", "名詞", "I have a rash on my face.", "身体", "300"),
    ("arm", "腕", "名詞", "I can't fully straighten my arm.", "身体", "300"),
    ("leg", "脚", "名詞", "I have a cramp in my leg.", "身体", "300"),
    ("chin", "あご", "名詞", "My chin feels numb after the dental procedure.", "身体", "400"),
    ("cheek", "頬", "名詞", "I have a swollen cheek.", "身体", "400"),
    ("lips", "唇(両方)", "名詞", "My lips are chapped and cracked.", "身体", "400"),
    ("toe", "足の指", "名詞", "I stubbed my toe on the doorframe.", "身体", "400"),
    ("cheekbone", "頬骨", "名詞", "The doctor gently pressed on my cheekbone.", "身体", "550"),
    # --- 泌尿器・内臓(既存に無いもの) ---
    ("urethra", "尿道", "名詞", "I have a burning sensation in my urethra when I urinate.", "身体", "750"),
    ("large intestine", "大腸", "名詞", "The scan showed mild inflammation in the large intestine.", "身体", "700"),
    # --- 生殖器系(症状説明のための中立的な医学用語のみ) ---
    ("testicle", "精巣(片方)", "名詞", "I've noticed some swelling in one testicle.", "身体", "700"),
    ("testicles", "精巣(両方)", "名詞", "The doctor examined both testicles during the check-up.", "身体", "700"),
    ("ovary", "卵巣(片方)", "名詞", "An ultrasound showed a small cyst on her ovary.", "身体", "700"),
    ("ovaries", "卵巣(両方)", "名詞", "The doctor checked both ovaries during the ultrasound.", "身体", "700"),
    ("penis", "陰茎", "名詞", "The doctor examined the penis for any signs of irritation.", "身体", "700"),
    ("vagina", "腟", "名詞", "She described some discomfort in the vagina during the exam.", "身体", "700"),
    ("scrotum", "陰嚢", "名詞", "He mentioned some mild swelling in the scrotum.", "身体", "750"),
    ("vulva", "外陰部", "名詞", "The doctor asked about any tenderness around the vulva.", "身体", "750"),
    ("prostate", "前立腺", "名詞", "The doctor recommended a routine prostate exam.", "身体", "750"),
    ("genitals", "性器・陰部(総称)", "名詞", "The physical exam included a brief check of the genitals.", "身体", "700"),
    # --- 体毛 ---
    ("beard", "あごひげ", "名詞", "His beard was irritated from the new razor.", "身体", "400"),
    ("armpit hair", "わき毛", "名詞", "The nurse asked if he had noticed any rash near his armpit hair.", "身体", "450"),
    ("pubic hair", "陰毛", "名詞", "The doctor asked a few questions about the area near the pubic hair.", "身体", "700"),
    ("chest hair", "胸毛", "名詞", "He noticed a small mole in his chest hair.", "身体", "450"),
    # --- 歯 ---
    ("front tooth", "前歯", "名詞", "My front tooth feels loose after the fall.", "身体", "450"),
    ("molar", "奥歯・臼歯", "名詞", "One of my molars needs a filling.", "身体", "600"),
    ("wisdom tooth", "親知らず", "名詞", "My wisdom tooth is coming in and it hurts.", "身体", "600"),
    # --- その他 ---
    ("nasal cavity", "鼻腔", "名詞", "The doctor examined my nasal cavity with a small light.", "身体", "700"),
]

PHRASES: list[tuple[str, str]] = [
    ("Where does it hurt exactly?", "正確にどこが痛みますか？"),
    ("I have a headache and my neck feels stiff.", "頭痛がして、首も凝っています。"),
    ("I have dry, flaky skin on the back of my hand.", "手の甲に乾燥してかさかさした皮膚があります。"),
    ("My nose has been running for three days.", "3日前から鼻水が出ています。"),
    ("Open your mouth wide and say ah.", "口を大きく開けて「あー」と言ってください。"),
    ("My feet swell up by the end of the day.", "夕方になると足がむくみます。"),
    ("My back has been hurting since I moved some furniture.", "家具を運んでから背中が痛みます。"),
    ("I've had a cramping pain in my belly since last night.", "昨夜からお腹に差し込むような痛みがあります。"),
    ("It looks like you may have broken a small bone in your finger.", "指の小さな骨を折っているかもしれません。"),
    ("I have a toothache that gets worse at night.", "夜になると悪化する歯痛があります。"),
    ("My pinky finger has been numb since this morning.", "今朝から小指がしびれています。"),
    ("I jammed my index finger during the game.", "試合中に人差し指を突き指しました。"),
    ("I've noticed more hair falling out than usual lately.", "最近、いつもより髪の毛が抜けている気がします。"),
    ("My chin has felt numb since the dental work.", "歯科治療を受けてからあごがしびれています。"),
    ("My lips are so chapped they've started to crack.", "唇がひどく荒れてひび割れてきました。"),
    ("I stubbed my toe on the door frame this morning.", "今朝ドア枠に足の指をぶつけました。"),
    ("His beard has been irritated since he switched razors.", "剃刀を替えてから、あごひげのあたりがかぶれています。"),
    ("I feel a burning sensation when I urinate.", "排尿時に灼熱感があります。"),
    ("I've had some discomfort near my large intestine for a few days.", "数日前から大腸のあたりに不快感があります。"),
    ("I'd like to discuss a urinary symptom with you privately, if that's all right.", "よろしければ、泌尿器の症状について個人的にご相談したいのですが。"),
    ("I've noticed some swelling in one testicle and would like it checked.", "片方の精巣に腫れがあり、診てもらいたいです。"),
    ("I'd like to make an appointment to discuss a concern about my ovaries.", "卵巣について相談するための予約を取りたいです。"),
    ("My doctor recommended a routine prostate screening this year.", "医師から今年、定期的な前立腺検査を勧められました。"),
    ("I've had some vaginal discharge that I'd like you to take a look at.", "気になる腟分泌物があるので診ていただきたいです。"),
    ("Is it normal to feel some tenderness around the vulva after the exam?", "検査の後、外陰部の周りに圧痛を感じるのは普通ですか？"),
    ("I noticed a small bump near my penis and I'd like it checked.", "陰茎の近くに小さなできものがあり、診てもらいたいです。"),
    ("I have some mild discomfort in my scrotum that I'd like checked.", "陰嚢に軽い不快感があり、診てもらいたいです。"),
    ("The physical exam included a brief, routine check of the genitals.", "健康診断には、陰部の簡単な定期チェックも含まれていました。"),
    ("My wisdom tooth is coming in and one of my molars needs a filling.", "親知らずが生えてきていて、奥歯の一本に詰め物が必要です。"),
    ("The doctor examined my nasal cavity with a small light.", "医師は小さなライトで鼻腔を診てくれました。"),
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
