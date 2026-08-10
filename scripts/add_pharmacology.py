# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add pharmacology / pharmacy English vocabulary and phrases across three
new domains, authored by Claude (2026-08-10・ユーザー要望).

対象語彙: 薬学(一般薬)=市販薬(OTC)・家庭薬に関する語(over-the-counter drug、
generic drug、syrup、ointment、eye drops、antacid、antihistamine等)、
薬学(処方薬)=処方薬・調剤・薬局業務に関する語(prescription drug、controlled
substance、dispense、drug interaction、prior authorization、copay、
formulary等)、薬学(専門他)=薬理学・創薬・薬物動態等の専門用語
(pharmacokinetics、pharmacodynamics、bioavailability、therapeutic index、
placebo、clinical trial等)。既存の`医療`ドメインにある薬関連語
(antibiotic, anticoagulant, analgesic, painkiller, penicillin,
prescription, pharmacy, medication, medicine, epinephrine, vaccine,
side effect, overdose, contraindication, regimen等)とは重複しない語を
選定。実在の薬品名・製薬会社名は使用せず、一般名・分類名のみ。

フレーズは薬局で薬剤師と話す・処方薬について医者と話す・薬物動態などを
専門的に議論する場面で実際に使う自然な英語表現。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_pharmacology.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 薬学(一般薬): OTC医薬品・家庭薬 ---
    ("over-the-counter drug", "市販薬・OTC医薬品", "名詞", "You can buy this over-the-counter drug without a prescription.", "薬学(一般薬)", "650"),
    ("generic drug", "ジェネリック医薬品(後発医薬品)", "名詞", "The generic drug contains the same active ingredient as the brand-name version.", "薬学(一般薬)", "650"),
    ("brand-name drug", "先発医薬品・ブランド薬", "名詞", "The brand-name drug usually costs more than its generic equivalent.", "薬学(一般薬)", "650"),
    ("syrup", "シロップ剤", "名詞", "Give the child one teaspoon of the syrup after meals.", "薬学(一般薬)", "450"),
    ("ointment", "軟膏", "名詞", "Apply a thin layer of ointment to the affected skin.", "薬学(一般薬)", "500"),
    ("eye drops", "目薬・点眼薬", "名詞", "Use the eye drops twice a day for dry eyes.", "薬学(一般薬)", "500"),
    ("cough syrup", "咳止めシロップ", "名詞", "He took some cough syrup before going to bed.", "薬学(一般薬)", "500"),
    ("antacid", "制酸剤", "名詞", "An antacid can quickly relieve heartburn.", "薬学(一般薬)", "600"),
    ("antihistamine", "抗ヒスタミン薬", "名詞", "This antihistamine helps control her seasonal allergies.", "薬学(一般薬)", "650"),
    ("expiration date", "(薬の)使用期限", "名詞", "Always check the expiration date before taking any medicine.", "薬学(一般薬)", "500"),
    ("active ingredient", "有効成分", "名詞", "Check the label to see the active ingredient and its amount.", "薬学(一般薬)", "600"),
    ("daily dose", "1日の服用量", "名詞", "Do not exceed the recommended daily dose.", "薬学(一般薬)", "550"),
    ("laxative", "下剤", "名詞", "The doctor recommended a mild laxative for occasional constipation.", "薬学(一般薬)", "650"),
    ("decongestant", "鼻づまり解消薬", "名詞", "A decongestant can relieve a stuffy nose caused by a cold.", "薬学(一般薬)", "700"),
    ("expectorant", "去痰薬", "名詞", "An expectorant helps loosen mucus so you can cough it up.", "薬学(一般薬)", "750"),
    ("inhaler", "吸入器", "名詞", "She carries an inhaler in case her asthma flares up.", "薬学(一般薬)", "550"),
    ("suppository", "座薬", "名詞", "The suppository is inserted rectally for faster absorption.", "薬学(一般薬)", "750"),
    ("lozenge", "トローチ", "名詞", "Suck on a lozenge to soothe your sore throat.", "薬学(一般薬)", "650"),
    ("nasal spray", "点鼻薬", "名詞", "Use the nasal spray only as directed on the label.", "薬学(一般薬)", "550"),
    # --- 薬学(処方薬): 処方薬・調剤・薬局業務 ---
    ("prescription drug", "処方薬", "名詞", "This prescription drug requires a doctor's approval before you can buy it.", "薬学(処方薬)", "600"),
    ("controlled substance", "規制薬物(管理医薬品)", "名詞", "Pharmacists must keep detailed records of every controlled substance they dispense.", "薬学(処方薬)", "800"),
    ("refill request", "(処方箋の)リフィル依頼", "名詞", "I'd like to submit a refill request for my blood pressure medication.", "薬学(処方薬)", "650"),
    ("dispense", "(薬を)調剤して渡す", "動詞", "The pharmacist will dispense your medication once the prescription is verified.", "薬学(処方薬)", "700"),
    ("drug interaction", "薬物相互作用", "名詞", "The pharmacist checked for any dangerous drug interaction before filling the order.", "薬学(処方薬)", "750"),
    ("dosage instructions", "用法用量の指示", "名詞", "Please follow the dosage instructions printed on the label carefully.", "薬学(処方薬)", "650"),
    ("generic substitution", "ジェネリック医薬品への代替調剤", "名詞", "Ask your pharmacist about generic substitution to save money.", "薬学(処方薬)", "800"),
    ("prior authorization", "(保険の)事前承認", "名詞", "Your insurance company requires prior authorization for this medication.", "薬学(処方薬)", "800"),
    ("pharmacy benefit", "薬剤給付(保険による薬代カバー)", "名詞", "Check your pharmacy benefit to see how much this drug will cost you.", "薬学(処方薬)", "800"),
    ("compounding", "調剤・混合調剤", "名詞", "The pharmacy offers compounding services for custom dosages.", "薬学(処方薬)", "800"),
    ("pharmacy technician", "調剤補助スタッフ・薬局技術者", "名詞", "The pharmacy technician counted the tablets and labeled the bottle.", "薬学(処方薬)", "650"),
    ("drive-through pharmacy", "ドライブスルー薬局", "名詞", "I picked up my prescription at the drive-through pharmacy without leaving my car.", "薬学(処方薬)", "600"),
    ("copay", "(自己負担の)一部負担金", "名詞", "My copay for this prescription is only five dollars.", "薬学(処方薬)", "650"),
    ("deductible", "(保険の)自己負担額・控除額", "名詞", "You have to meet your deductible before insurance covers the medication.", "薬学(処方薬)", "750"),
    ("formulary", "保険適用医薬品リスト", "名詞", "This drug isn't on the insurance formulary, so it costs more.", "薬学(処方薬)", "850"),
    ("dosing schedule", "服薬スケジュール", "名詞", "Follow the dosing schedule exactly to keep the medication effective.", "薬学(処方薬)", "700"),
    ("medication guide", "服薬ガイド(説明書)", "名詞", "Read the medication guide for information about possible side effects.", "薬学(処方薬)", "600"),
    # --- 薬学(専門他): 薬理学・創薬・薬物動態 ---
    ("pharmacokinetics", "薬物動態学", "名詞", "Pharmacokinetics studies how the body absorbs, distributes, and eliminates a drug.", "薬学(専門他)", "900"),
    ("pharmacodynamics", "薬力学", "名詞", "Pharmacodynamics explains how a drug affects the body at the molecular level.", "薬学(専門他)", "900"),
    ("bioavailability", "生物学的利用能", "名詞", "The drug's bioavailability is much lower when taken orally than by injection.", "薬学(専門他)", "900"),
    ("metabolite", "代謝産物", "名詞", "The liver breaks the drug down into an active metabolite.", "薬学(専門他)", "850"),
    ("drug tolerance", "薬物耐性", "名詞", "Patients can develop drug tolerance after long-term use of the same dose.", "薬学(専門他)", "800"),
    ("drug dependence", "薬物依存", "名詞", "Drug dependence can develop even with medications prescribed by a doctor.", "薬学(専門他)", "800"),
    ("therapeutic index", "治療係数(安全域を示す指標)", "名詞", "A drug with a narrow therapeutic index requires careful dose monitoring.", "薬学(専門他)", "900"),
    ("placebo", "プラセボ・偽薬", "名詞", "Some patients in the study received a placebo instead of the real drug.", "薬学(専門他)", "800"),
    ("clinical trial", "臨床試験", "名詞", "The new drug is currently being tested in a large clinical trial.", "薬学(専門他)", "750"),
    ("active pharmaceutical ingredient", "原薬(有効成分の原料)", "名詞", "The factory manufactures the active pharmaceutical ingredient before it is formulated into tablets.", "薬学(専門他)", "900"),
    ("formulation", "製剤・調合", "名詞", "Researchers developed a new formulation that releases the drug more slowly.", "薬学(専門他)", "800"),
    ("onset of action", "(薬の)作用発現", "名詞", "This medication has a fast onset of action, working within minutes.", "薬学(専門他)", "850"),
    ("duration of action", "(薬の)作用持続時間", "名詞", "The duration of action determines how often you need to take the drug.", "薬学(専門他)", "850"),
    ("sublingual", "舌下(投与)の", "形容詞", "The tablet is administered by the sublingual route so it dissolves quickly under the tongue.", "薬学(専門他)", "850"),
    ("therapeutic window", "治療域(安全に効果が出る範囲)", "名詞", "Doctors must keep the drug concentration within the therapeutic window.", "薬学(専門他)", "900"),
    ("efficacy", "有効性", "名詞", "The clinical trial confirmed the drug's efficacy in reducing symptoms.", "薬学(専門他)", "800"),
]

PHRASES: list[tuple[str, str]] = [
    ("Can I get this prescription filled here?", "この処方箋をここで調剤してもらえますか？"),
    ("How many refills do I have left?", "リフィル(再調剤)は残り何回分ありますか？"),
    ("Is this available over the counter, or do I need a prescription?", "これは市販で買えますか、それとも処方箋が必要ですか？"),
    ("Should I take this with food or on an empty stomach?", "これは食事と一緒に飲むべきですか、それとも空腹時ですか？"),
    ("How often should I take this medication?", "この薬はどのくらいの頻度で服用すればいいですか？"),
    ("Are there any side effects I should watch out for?", "注意すべき副作用はありますか？"),
    ("Can I take this together with my other medications?", "他の薬と一緒にこれを飲んでも大丈夫ですか？"),
    ("Is there a generic version of this drug?", "この薬のジェネリック版はありますか？"),
    ("My insurance requires prior authorization for this drug.", "この薬には保険の事前承認が必要です。"),
    ("What's my copay for this prescription?", "この処方箋の自己負担額はいくらですか？"),
    ("Does my insurance cover this medication?", "この薬は保険適用されますか？"),
    ("Can you explain the dosage instructions again?", "用法用量をもう一度説明していただけますか？"),
    ("I'd like to switch to the generic substitution.", "ジェネリック医薬品への代替調剤に切り替えたいのですが。"),
    ("Please store this medicine in a cool, dry place.", "この薬は涼しく乾燥した場所で保管してください。"),
    ("Keep this out of reach of children.", "これは子供の手の届かないところに保管してください。"),
    ("What should I do if I miss a dose?", "飲み忘れた場合はどうすればいいですか？"),
    ("This drug has a narrow therapeutic window.", "この薬は治療域が狭いです。"),
    ("The new formulation has a slower onset of action.", "新しい製剤は作用発現が遅くなっています。"),
    ("We need to monitor the drug's bioavailability in this study.", "この研究では薬のバイオアベイラビリティを観察する必要があります。"),
    ("The trial showed strong efficacy compared to the placebo group.", "この試験ではプラセボ群と比べて高い有効性が示されました。"),
    ("Long-term use may lead to drug tolerance.", "長期使用は薬物耐性につながる可能性があります。"),
    ("Let's check for any potential drug interaction first.", "まず薬物相互作用の可能性を確認しましょう。"),
    ("The pharmacokinetics of this compound are still under study.", "この化合物の薬物動態はまだ研究中です。"),
    ("Can you dispense a two-week supply instead?", "代わりに2週間分を調剤してもらえますか？"),
    ("I'd like to pick up my prescription at the drive-through pharmacy.", "ドライブスルー薬局で処方箋を受け取りたいのですが。"),
    ("Please read the medication guide before starting this drug.", "この薬を使い始める前に服薬ガイドを読んでください。"),
    ("The active ingredient can cause drowsiness in some patients.", "有効成分が一部の患者に眠気を引き起こすことがあります。"),
    ("Has this drug passed its expiration date?", "この薬は使用期限を過ぎていませんか？"),
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
                "VALUES (?, ?, '薬局・薬学の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
