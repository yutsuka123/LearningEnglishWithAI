# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add occupations from Japanese kids'/students' "なりたい職業ランキング"
(dream-job rankings) plus newly emerged modern occupations to the existing
"職業" domain, authored by Claude (2026-08-10・ユーザー要望:
「日本の子供男女がなりたい職業ベスト10/大学生・高校生がなりたい職業/
近年登場した新しい職業(アニメーター等)」)。

事前にDBを確認し、`animator`/`voice actor`/`pilot`/`firefighter`/
`astronaut`/`pharmacist`/`idol`/`vet`/`veterinarian`/`hairdresser`/
`beautician`/`data scientist`/`game designer`/`flight attendant`/
`streamer`/`influencer`/`celebrity`は既に別ドメイン(職業/大衆文化/医療
(専門・学問)/美容/航空・宇宙等)に存在するため重複追加しない。
`physician`(医療(専門・学問))/`registered nurse`(看護学)は既存だが、
子供のランキングで使われる平易な`doctor`/`nurse`は未収録だったため
今回追加する。

対象(男女の子供に人気の職業ランキング上位の定番): soccer player、
baseball player、YouTuber、doctor、game creator、company employee、
train driver、pastry chef、nurse、manga artist、florist。
大学生・高校生に人気の職業(業界寄り): trading company employee、
consultant、cabin attendant。
近年登場した新しい職業: esports player、professional gamer、drone
operator、social media manager、UX designer、illustrator、cosplayer、
content creator。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_occupations_aspirational.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "職業"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 子供に人気の職業(定番) ---
    ("soccer player", "サッカー選手", "名詞", "He dreams of becoming a professional soccer player.", DOMAIN, "350"),
    ("baseball player", "野球選手", "名詞", "She wants to be a baseball player when she grows up.", DOMAIN, "350"),
    ("YouTuber", "ユーチューバー", "名詞", "Many kids say they want to be a YouTuber someday.", DOMAIN, "400"),
    ("doctor", "医者", "名詞", "He has wanted to be a doctor since he was a child.", DOMAIN, "300"),
    ("nurse", "看護師", "名詞", "She decided to become a nurse after visiting the hospital.", DOMAIN, "300"),
    ("game creator", "ゲームクリエイター", "名詞", "He studied programming so he could become a game creator.", DOMAIN, "500"),
    ("company employee", "会社員", "名詞", "Most of her classmates just want to be a company employee.", DOMAIN, "350"),
    ("train driver", "電車の運転士", "名詞", "Being a train driver is a popular dream job for young children.", DOMAIN, "400"),
    ("pastry chef", "パティシエ", "名詞", "She wants to become a pastry chef and open her own shop.", DOMAIN, "500"),
    ("manga artist", "漫画家", "名詞", "He spends every weekend drawing, hoping to become a manga artist.", DOMAIN, "500"),
    ("florist", "花屋・フローリスト", "名詞", "She has always dreamed of becoming a florist.", DOMAIN, "450"),
    # --- 大学生・高校生に人気の職業 ---
    ("trading company employee", "商社マン(総合商社の社員)", "名詞", "He landed a job as a trading company employee after graduation.", DOMAIN, "650"),
    ("consultant", "コンサルタント", "名詞", "She works as a consultant advising companies on strategy.", DOMAIN, "550"),
    ("cabin attendant", "客室乗務員(CA)", "名詞", "Becoming a cabin attendant is still a popular choice among students.", DOMAIN, "500"),
    # --- 近年登場した新しい職業 ---
    ("esports player", "eスポーツ選手", "名詞", "He competes as a professional esports player.", DOMAIN, "600"),
    ("professional gamer", "プロゲーマー", "名詞", "She makes a living as a professional gamer.", DOMAIN, "550"),
    ("drone operator", "ドローン操縦士", "名詞", "The drone operator filmed the event from above.", DOMAIN, "650"),
    ("social media manager", "SNS運用担当者", "名詞", "The company hired a social media manager to grow its online presence.", DOMAIN, "650"),
    ("UX designer", "UXデザイナー", "名詞", "The UX designer improved how easy the app is to use.", DOMAIN, "700"),
    ("illustrator", "イラストレーター", "名詞", "She works as a freelance illustrator.", DOMAIN, "500"),
    ("cosplayer", "コスプレイヤー", "名詞", "Some professional cosplayers make a living through sponsorships and events.", DOMAIN, "600"),
    ("content creator", "コンテンツクリエイター", "名詞", "He works as a content creator, making videos and writing articles.", DOMAIN, "550"),
]

PHRASES: list[tuple[str, str]] = [
    ("What do you want to be when you grow up?", "大きくなったら何になりたい？"),
    ("She wants to be a doctor when she grows up.", "彼女は大きくなったら医者になりたいそうです。"),
    ("Being a YouTuber is one of the most popular dream jobs for kids now.", "今、ユーチューバーは子供たちに人気の夢の職業のひとつです。"),
    ("He's studying hard to become a game creator.", "彼はゲームクリエイターになるため一生懸命勉強しています。"),
    ("A lot of students hope to land a job at a trading company.", "多くの学生が商社への就職を希望しています。"),
    ("She's training to become a cabin attendant.", "彼女は客室乗務員になるための訓練を受けています。"),
    ("He makes a living as a professional gamer.", "彼はプロゲーマーとして生計を立てています。"),
    ("The company is looking for a social media manager.", "その会社はSNS運用担当者を探しています。"),
    ("I've always dreamed of becoming a pastry chef.", "私はずっとパティシエになることを夢見てきました。"),
    ("She works as a freelance illustrator.", "彼女はフリーランスのイラストレーターとして働いています。"),
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
                "VALUES (?, ?, '職業の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
