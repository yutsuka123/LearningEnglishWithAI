# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a new "助産学" domain/scene: vocabulary and phrases for midwifery /
obstetrics (Midwifery/Obstetrics), authored by Claude (2026-08-10・ユーザー
要望)。既存の`看護学`ドメイン(43語・患者ケア/病棟業務中心)と対になる位置
づけで、妊娠・出産・産後に特化した語彙を扱う。

対象語彙: 妊娠・出生前(妊婦健診、出産予定日、妊娠三半期、つわり、胎児心音、
胎動、妊娠週数、ハイリスク妊娠、超音波検査、産科医)、陣痛・分娩(陣痛、
破水、子宮口の開大、無痛分娩の麻酔、自然分娩、帝王切開、経腟分娩、分娩体位、
助産ケア、ドゥーラ、逆子)、産後・新生児(産後回復、母乳育児、母乳育児相談員、
へその緒、胎盤、羊水、新生児スクリーニング検査、アプガースコア、カンガルー
ケア、初乳、おくるみ、授乳の吸い付き、骨盤底)、助産師の業務・資格(認定看護
助産師、自宅出産、バースプラン、バースセンター)。

**見出し語の衝突対策**: このDBのdedupは`english`列を全ドメイン横断・小文字
完全一致で判定する。事前に`sqlite3 data/vocabulary.db "SELECT english,
domain FROM words WHERE LOWER(english) IN ('labor','delivery','midwife',
'pregnant');"`で確認したところ、
  - `labor`      … domain空欄の孤立エントリが既存
  - `delivery`   … まさかの`話芸・コメディ`ドメイン(コメディの「間の取り方」
                    の意味で登録されており、出産の意味ではない)
  - `midwife`    … `職業`ドメインに既存(職業名としての「助産師」)
  - `pregnant`   … `医療(その他)`ドメインに既存
のようにサイレントな衝突/スキップが起きることが判明した。そのため、
`labor`と`delivery`は出産文脈であることを明示する複合見出し
`labor (childbirth)` / `delivery (childbirth)` として登録する
(単純に`labor`/`delivery`を見出しにすると、上記の無関係な既存語と
衝突して意図した語が登録されないため)。`midwife`(職業名)・`pregnant`は
既存語のため本ファイルでは重複追加しない(代わりに`midwifery care`など
別語を採用)。

フレーズは助産師・妊婦・産科医が実際に使う自然な英語表現(陣痛の様子を
伝える、呼吸法を指導する、出産計画を話す、授乳を支援する等)。健全で
臨床的な文脈に留め、扇情的・悲観的な内容(死産・流産等)は扱わない。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_midwifery.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 妊娠・出生前 ---
    ("prenatal care", "妊婦健診・出生前ケア", "名詞", "Regular prenatal care helps catch problems early in pregnancy.", "助産学", "500"),
    ("prenatal checkup", "妊婦健診", "名詞", "She has a prenatal checkup scheduled for next Tuesday.", "助産学", "500"),
    ("due date", "出産予定日", "名詞", "Her due date is in early October.", "助産学", "450"),
    ("trimester", "(妊娠の)三半期", "名詞", "Morning sickness usually eases by the second trimester.", "助産学", "600"),
    ("morning sickness", "つわり", "名詞", "Morning sickness can happen at any time of day, not just morning.", "助産学", "600"),
    ("fetal heartbeat", "胎児心音", "名詞", "The midwife listened for the fetal heartbeat with a Doppler device.", "助産学", "700"),
    ("fetal movement", "胎動", "名詞", "Decreased fetal movement should be reported to your midwife right away.", "助産学", "700"),
    ("gestational age", "妊娠週数", "名詞", "The ultrasound confirmed the baby's gestational age.", "助産学", "750"),
    ("high-risk pregnancy", "ハイリスク妊娠", "名詞", "A high-risk pregnancy requires closer monitoring by the care team.", "助産学", "750"),
    ("ultrasound", "超音波検査(エコー)", "名詞", "The ultrasound showed a healthy, strong heartbeat.", "助産学", "550"),
    ("obstetrician", "産科医", "名詞", "Her obstetrician recommended a follow-up appointment in two weeks.", "助産学", "700"),
    # --- 陣痛・分娩 ---
    ("labor (childbirth)", "陣痛・分娩", "名詞", "She went into labor early on Sunday morning.", "助産学", "500"),
    ("contraction", "陣痛の収縮", "名詞", "The contractions are getting closer together now.", "助産学", "600"),
    ("water breaking", "破水", "名詞", "Water breaking is one of the first signs that labor has started.", "助産学", "650"),
    ("dilation", "子宮口の開大", "名詞", "The midwife checked her dilation every hour during labor.", "助産学", "750"),
    ("epidural", "硬膜外麻酔(無痛分娩の麻酔)", "名詞", "She decided to get an epidural once the pain became intense.", "助産学", "700"),
    ("natural childbirth", "自然分娩", "名詞", "She hoped for a natural childbirth without any pain medication.", "助産学", "650"),
    ("cesarean section", "帝王切開", "名詞", "The doctor recommended a cesarean section due to the baby's position.", "助産学", "700"),
    ("vaginal delivery", "経腟分娩", "名詞", "Most pregnancies end in a normal vaginal delivery.", "助産学", "750"),
    ("delivery (childbirth)", "分娩・出産", "名詞", "The delivery went smoothly and both mother and baby are doing well.", "助産学", "500"),
    ("birthing position", "分娩体位", "名詞", "The midwife encouraged her to try a different birthing position.", "助産学", "700"),
    ("midwifery care", "助産ケア", "名詞", "Midwifery care focuses on supporting a woman throughout pregnancy and birth.", "助産学", "700"),
    ("doula", "ドゥーラ(出産サポーター)", "名詞", "Her doula stayed by her side through the entire labor.", "助産学", "800"),
    ("breech position", "骨盤位(逆子)", "名詞", "The baby was in a breech position, so they discussed a cesarean section.", "助産学", "800"),
    # --- 産後・新生児 ---
    ("postpartum recovery", "産後回復", "名詞", "Postpartum recovery can take several weeks after delivery.", "助産学", "650"),
    ("breastfeeding", "母乳育児", "名詞", "The lactation consultant helped her with breastfeeding in the first days.", "助産学", "500"),
    ("lactation consultant", "母乳育児相談員", "名詞", "A lactation consultant can help if breastfeeding feels difficult.", "助産学", "750"),
    ("umbilical cord", "へその緒", "名詞", "The nurse clamped and cut the umbilical cord after delivery.", "助産学", "600"),
    ("placenta", "胎盤", "名詞", "The placenta was delivered a few minutes after the baby.", "助産学", "700"),
    ("amniotic fluid", "羊水", "名詞", "The amniotic fluid cushions and protects the baby in the womb.", "助産学", "750"),
    ("newborn screening", "新生児スクリーニング検査", "名詞", "Newborn screening checks for several rare conditions shortly after birth.", "助産学", "750"),
    ("Apgar score", "アプガースコア", "名詞", "The baby received a high Apgar score one minute after birth.", "助産学", "800"),
    ("skin-to-skin contact", "肌と肌の触れ合い(カンガルーケア)", "名詞", "Skin-to-skin contact right after birth helps calm the newborn.", "助産学", "700"),
    ("colostrum", "初乳", "名詞", "Colostrum is rich in antibodies that protect the newborn.", "助産学", "850"),
    ("swaddle", "おくるみで包む", "動詞", "The nurse showed the new parents how to swaddle their baby.", "助産学", "600"),
    ("latch", "(授乳時に)乳首に吸い付く", "動詞", "A good latch makes breastfeeding much more comfortable.", "助産学", "700"),
    ("pelvic floor", "骨盤底", "名詞", "Pelvic floor exercises can help with recovery after childbirth.", "助産学", "750"),
    # --- 助産師の業務・資格 ---
    ("certified nurse-midwife", "認定看護助産師", "名詞", "A certified nurse-midwife can manage low-risk pregnancies and births.", "助産学", "800"),
    ("home birth", "自宅出産", "名詞", "She chose a home birth with a certified nurse-midwife.", "助産学", "650"),
    ("birth plan", "バースプラン(出産計画)", "名詞", "They discussed her birth plan at the last prenatal checkup.", "助産学", "650"),
    ("birthing center", "バースセンター(助産院)", "名詞", "The birthing center offers a more home-like setting than a hospital.", "助産学", "700"),
]

PHRASES: list[tuple[str, str]] = [
    ("How far apart are your contractions?", "陣痛の間隔はどのくらいですか？"),
    ("My water just broke.", "今、破水しました。"),
    ("Take a deep breath and breathe through the contraction.", "深呼吸をして、陣痛を呼吸で乗り切ってください。"),
    ("You're fully dilated now.", "子宮口が全開大になりました。"),
    ("Would you like an epidural?", "無痛分娩の麻酔をご希望ですか？"),
    ("I'd like to have a natural childbirth if possible.", "できれば自然分娩で出産したいです。"),
    ("The baby's heartbeat sounds strong and steady.", "赤ちゃんの心音は力強く安定しています。"),
    ("Let's go over your birth plan together.", "一緒にバースプランを確認しましょう。"),
    ("Try changing your birthing position to ease the pain.", "痛みを和らげるために分娩体位を変えてみましょう。"),
    ("Push when you feel the next contraction.", "次の陣痛が来たらいきんでください。"),
    ("Congratulations, it's a healthy baby girl!", "おめでとうございます、健康な女の子です！"),
    ("We'll place the baby on your chest for skin-to-skin contact.", "カンガルーケアのため赤ちゃんをお母さんの胸に乗せますね。"),
    ("Is breastfeeding going well so far?", "授乳はここまで順調ですか？"),
    ("The lactation consultant can help you with latching.", "母乳育児相談員が授乳の吸い付き方を手伝ってくれます。"),
    ("We need to monitor your blood pressure closely.", "血圧を注意深くモニタリングする必要があります。"),
    ("Your due date is coming up soon.", "出産予定日がもうすぐですね。"),
    ("How many weeks along are you?", "妊娠何週目ですか？"),
    ("We recommend a cesarean section because the baby is breech.", "赤ちゃんが逆子なので帝王切開をお勧めします。"),
    ("Would you like your partner in the delivery room?", "パートナーの方に分娩室に入ってもらいますか？"),
    ("Let's schedule your next prenatal checkup.", "次回の妊婦健診の予約を取りましょう。"),
    ("The midwife checked her dilation and said it wouldn't be long now.", "助産師が子宮口の開大を確認し、もうすぐだと言った。"),
    ("I felt the baby move for the first time today.", "今日、初めて胎動を感じました。"),
    ("We'll do the newborn screening before you leave the hospital.", "退院前に新生児スクリーニング検査を行います。"),
    ("Try to relax your body between contractions.", "陣痛と陣痛の間は体をリラックスさせてください。"),
    ("She's considering a home birth with a certified nurse-midwife.", "彼女は認定看護助産師による自宅出産を検討している。"),
    ("The birthing center feels more relaxed than a hospital ward.", "バースセンターは病棟より落ち着いた雰囲気です。"),
    ("Colostrum gives your baby important antibodies in the first few days.", "初乳は生後数日間、赤ちゃんに重要な抗体を与えてくれます。"),
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
                "VALUES (?, ?, '助産学の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
