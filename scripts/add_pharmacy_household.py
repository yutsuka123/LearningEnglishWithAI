# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add household/OTC medicine items to the existing "薬学(一般薬)" domain
that were missing after the initial pharmacology batch, authored by Claude
(2026-08-10・ユーザー要望: 包帯/せき止め/頭痛薬/湿布/下痢止め/胃腸薬/下剤/
止瀉薬/浣腸/粉薬/オブラート/錠剤/カプセル/消毒薬など)。

事前にDBを確認した結果:
- `bandage`(包帯)は既存`医療(治療)`ドメインに、`laxative`(下剤)は既存
  `薬学(一般薬)`ドメインに既にあるため、この2語は対象外(再追加不要)。
- `tablet`(錠剤)は既存だが domain='家電'(タブレット端末の意味)、
  `capsule`(カプセル)も既存だが domain='航空・宇宙'(宇宙カプセルの意味)
  ＝どちらも薬の意味では未収録の同名異義語。このDBのdedupは英単語を
  ドメイン横断・小文字完全一致で見るため、そのまま`tablet`/`capsule`を
  追加すると別語義のまま無条件でスキップされてしまう。そのため
  `tablet (medicine)`/`capsule (medicine)`のように薬の文脈と明示する
  見出しにした。

追加語: cough medicine(せき止め・錠剤/シロップ以外の総称)、headache
medicine(頭痛薬)、medicated patch(湿布)、antidiarrheal medicine
(下痢止め・止瀉薬)、stomach medicine(胃腸薬)、enema(浣腸)、powdered
medicine(粉薬)、oblate wafer(オブラート・日本や欧州で使われる、苦い粉薬
を包んで飲みやすくする可食フィルム)、tablet (medicine)、capsule
(medicine)、disinfectant(消毒薬)、antiseptic(殺菌消毒剤)、gauze(ガーゼ)。

フレーズは薬局・自宅の常備薬棚で実際に使う自然な英語表現。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_pharmacy_household.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("cough medicine", "せき止め薬", "名詞", "He took some cough medicine before going to bed.", "薬学(一般薬)", "450"),
    ("headache medicine", "頭痛薬", "名詞", "Do you have any headache medicine I could take?", "薬学(一般薬)", "450"),
    ("medicated patch", "湿布(貼り薬)", "名詞", "She put a medicated patch on her sore shoulder.", "薬学(一般薬)", "600"),
    ("antidiarrheal medicine", "下痢止め・止瀉薬", "名詞", "Take this antidiarrheal medicine if your stomach is still upset.", "薬学(一般薬)", "700"),
    ("stomach medicine", "胃腸薬", "名詞", "I always carry stomach medicine when I travel abroad.", "薬学(一般薬)", "500"),
    ("enema", "浣腸", "名詞", "The nurse explained how to use the enema safely.", "薬学(一般薬)", "800"),
    ("powdered medicine", "粉薬", "名詞", "Children's powdered medicine is often mixed with a little water.", "薬学(一般薬)", "550"),
    ("oblate wafer", "オブラート(苦い粉薬を包む可食フィルム)", "名詞", "Wrap the bitter powder in an oblate wafer so it's easier to swallow.", "薬学(一般薬)", "800"),
    ("tablet (medicine)", "錠剤", "名詞", "Take one tablet after each meal, three times a day.", "薬学(一般薬)", "450"),
    ("capsule (medicine)", "カプセル(薬)", "名詞", "This capsule should be swallowed whole with a glass of water.", "薬学(一般薬)", "450"),
    ("disinfectant", "消毒薬", "名詞", "Clean the wound with disinfectant before applying the bandage.", "薬学(一般薬)", "550"),
    ("antiseptic", "殺菌消毒剤", "名詞", "Apply a small amount of antiseptic to the cut.", "薬学(一般薬)", "600"),
    ("gauze", "ガーゼ", "名詞", "Cover the wound with a piece of sterile gauze.", "薬学(一般薬)", "500"),
]

PHRASES: list[tuple[str, str]] = [
    ("Do you have anything for a headache?", "頭痛に効くものはありますか？"),
    ("I need some cough medicine for a bad cough.", "ひどい咳に効くせき止めが欲しいです。"),
    ("Could you recommend a good stomach medicine?", "何かいい胃腸薬を勧めてもらえますか？"),
    ("I'll put a medicated patch on my shoulder tonight.", "今夜、肩に湿布を貼ります。"),
    ("This antidiarrheal medicine should help settle your stomach.", "この下痢止めでお腹が落ち着くはずです。"),
    ("Take this powdered medicine with plenty of water.", "この粉薬は水をたくさん飲んで服用してください。"),
    ("Is it easier to swallow as a tablet or a capsule?", "錠剤とカプセル、どちらが飲みやすいですか？"),
    ("Please disinfect the wound before bandaging it.", "傷口は消毒してから包帯を巻いてください。"),
    ("We're out of gauze — can you pick some up at the pharmacy?", "ガーゼが切れているので、薬局で買ってきてもらえますか？"),
    ("The doctor prescribed an enema for the constipation.", "医師は便秘に対して浣腸を処方しました。"),
    ("Some people wrap bitter medicine in an oblate wafer.", "苦い薬をオブラートに包んで飲む人もいます。"),
    ("How many times a day should I take this?", "これは1日何回服用すればいいですか？"),
    ("Please store this medicine in a cool, dry place.", "この薬は涼しく乾燥した場所で保管してください。"),
    ("I'd like something for an upset stomach.", "お腹の調子が悪いので、何か薬をいただけますか。"),
    ("Should I take this before or after meals?", "これは食前と食後、どちらに飲めばいいですか？"),
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
