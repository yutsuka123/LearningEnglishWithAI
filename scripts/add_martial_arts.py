# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a new "武道・格闘技" domain/scene: vocabulary and phrases for martial
arts in general (karate, aikido, judo, boxing, self-defense, tai chi, yoga,
Shorinji Kempo, etc.), authored by Claude (2026-08-10・ユーザー要望).

対象語彙: 道場や稽古で共通して使われる基本用語(道場、帯、黒帯、段位、昇級審
査、指導者、道着、準備運動、クールダウン)、動作・技術(構え、スパーリング、
技、投げ技、打撃、蹴り、突き、受け、組手、足さばき、連続技、型、寝技、極め
技、関節技)、心構え・マナー(お辞儀、敬意、集中力、規律、呼吸法、バランス、
柔軟性、持久力、瞑想、ポーズ)。特定の流派・団体名や実在の選手名などの固有
名詞は一切使用せず、すべて一般的な用語のみ。攻撃的・暴力的な描写は避け、健
全な練習・指導の文脈にしている。

フレーズは実際に道場や練習・試合の場面で使う自然な口語表現("Bow before you
step onto the mat." "Keep your guard up." "Tap out if it hurts." など)。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_martial_arts.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 基本語 ---
    ("dojo", "道場", "名詞", "You should bow when you enter the dojo.", "武道・格闘技", "300"),
    ("martial arts", "武道・格闘技", "名詞", "She has practiced martial arts since she was six.", "武道・格闘技", "300"),
    ("belt", "帯", "名詞", "Tie your belt tightly before we start.", "武道・格闘技", "350"),
    ("kick", "蹴り", "名詞", "Raise your knee higher before you kick.", "武道・格闘技", "350"),
    ("punch", "突き・パンチ", "名詞", "Keep your fist tight when you punch.", "武道・格闘技", "350"),
    ("stretch", "ストレッチをする", "動詞", "Stretch your hamstrings before kicking drills.", "武道・格闘技", "350"),
    ("balance", "バランス", "名詞", "Good balance is more important than raw strength.", "武道・格闘技", "400"),
    ("technique", "技・テクニック", "名詞", "Practice the technique slowly before speeding up.", "武道・格闘技", "400"),
    ("block", "受け", "名詞", "Use your forearm to block the strike.", "武道・格闘技", "400"),
    ("warm-up", "準備運動", "名詞", "Never skip the warm-up before hard training.", "武道・格闘技", "400"),
    ("bow", "お辞儀をする", "動詞", "Bow to your partner before you begin.", "武道・格闘技", "400"),
    ("partner", "稽古相手", "名詞", "Switch partners after every round.", "武道・格闘技", "400"),
    ("pose", "ポーズ", "名詞", "Hold this pose for thirty seconds.", "武道・格闘技", "400"),
    ("black belt", "黒帯", "名詞", "It took him five years to earn his black belt.", "武道・格闘技", "450"),
    ("instructor", "指導者", "名詞", "Our instructor corrected my stance during class.", "武道・格闘技", "450"),
    ("respect", "敬意", "名詞", "Respect for your training partners is essential.", "武道・格闘技", "450"),
    ("opponent", "対戦相手", "名詞", "Watch your opponent's feet, not their eyes.", "武道・格闘技", "450"),
    # --- 動作・構え ---
    ("rank", "段位・級", "名詞", "Your rank determines which techniques you'll learn next.", "武道・格闘技", "500"),
    ("stance", "構え", "名詞", "Keep a low stance to stay balanced.", "武道・格闘技", "500"),
    ("self-defense", "護身術", "名詞", "She took a self-defense class for beginners.", "武道・格闘技", "500"),
    ("posture", "姿勢", "名詞", "Correct posture protects your back during training.", "武道・格闘技", "500"),
    ("breathing", "呼吸法", "名詞", "Controlled breathing helps you stay calm under pressure.", "武道・格闘技", "500"),
    ("flexibility", "柔軟性", "名詞", "Yoga improves flexibility as well as balance.", "武道・格闘技", "500"),
    ("focus", "集中力", "名詞", "Losing focus for a second can cost you the point.", "武道・格闘技", "500"),
    ("strike", "打撃", "名詞", "A strike to the body can end the match quickly.", "武道・格闘技", "500"),
    ("throw", "投げ技", "名詞", "That throw requires perfect timing.", "武道・格闘技", "500"),
    # --- 練習・稽古 ---
    ("grip", "組手・握り", "名詞", "Fighting for grip is a key part of the match.", "武道・格闘技", "550"),
    ("sparring", "スパーリング", "名詞", "We do light sparring at the end of every class.", "武道・格闘技", "550"),
    ("uniform", "道着", "名詞", "Wash your uniform after every practice.", "武道・格闘技", "550"),
    ("drill", "反復練習", "名詞", "We repeated the same drill for twenty minutes.", "武道・格闘技", "550"),
    ("endurance", "持久力", "名詞", "Long sparring sessions build endurance over time.", "武道・格闘技", "550"),
    ("meditation", "瞑想", "名詞", "We end each class with five minutes of meditation.", "武道・格闘技", "550"),
    ("grading", "昇級審査", "名詞", "The next grading is scheduled for the end of the month.", "武道・格闘技", "600"),
    ("combination", "連続技", "名詞", "He landed a clean combination in the third round.", "武道・格闘技", "600"),
    ("footwork", "足さばき", "名詞", "Good footwork lets you close distance safely.", "武道・格闘技", "600"),
    ("discipline", "規律・鍛錬", "名詞", "Martial arts teaches discipline both on and off the mat.", "武道・格闘技", "600"),
    # --- 専門技術 ---
    ("kata", "型(決められた動作の連続)", "名詞", "We practice a new kata every month.", "武道・格闘技", "700"),
    ("groundwork", "寝技", "名詞", "Groundwork requires a completely different skill set.", "武道・格闘技", "700"),
    ("joint lock", "関節技", "名詞", "A joint lock can end a match without a single strike.", "武道・格闘技", "700"),
    ("submission", "極め技(相手を降参させる技)", "名詞", "He won the match by submission.", "武道・格闘技", "750"),
]

PHRASES: list[tuple[str, str]] = [
    ("Bow before you step onto the mat.", "マットに上がる前にお辞儀をしてください。"),
    ("Let's warm up before we start.", "始める前に準備運動をしましょう。"),
    ("Watch my stance carefully.", "私の構えをよく見てください。"),
    ("Switch partners, please.", "パートナーを交代してください。"),
    ("Keep your guard up.", "ガードを下げないでください。"),
    ("Relax your shoulders.", "肩の力を抜いてください。"),
    ("Slow it down and focus on form.", "スピードを落として、フォームに集中してください。"),
    ("Let's do some light sparring.", "軽くスパーリングをしましょう。"),
    ("Tap out if it hurts.", "痛かったらタップ(参った)をしてください。"),
    ("Great technique!", "いい技ですね！"),
    ("Try that throw again, slower this time.", "その投げ技をもう一度、今度はゆっくりやってみて。"),
    ("Keep your eyes on your opponent.", "相手から目を離さないでください。"),
    ("Breathe out when you strike.", "打つときに息を吐いてください。"),
    ("Let's line up for the bow-in.", "整列して礼をしましょう。"),
    ("That's enough for today. Good work, everyone.", "今日はここまでです。みなさんお疲れ様でした。"),
    ("Can you show me that move one more time?", "その動きをもう一度見せてもらえますか？"),
    ("Protect your center line.", "自分の中心線を守ってください。"),
    ("Don't lock your knees.", "膝を伸ばしきらないでください。"),
    ("Step in with your lead foot first.", "前足から踏み込んでください。"),
    ("Keep a wide base for better balance.", "バランスを取るために足幅を広く取ってください。"),
    ("Take a break and hydrate.", "休憩して水分を取ってください。"),
    ("You're improving a lot.", "だいぶ上達しましたね。"),
    ("Let's review the kata together.", "みんなで型を確認しましょう。"),
    ("Grading is coming up next month.", "来月、昇級審査があります。"),
    ("Control the pace, don't rush.", "焦らずペースをコントロールしてください。"),
    ("Wrap your hands before you hit the bag.", "サンドバッグを打つ前に手にバンテージを巻いてください。"),
    ("Stay relaxed until the moment of impact.", "当たる瞬間まで力を抜いておいてください。"),
    ("Let's cool down and stretch.", "クールダウンしてストレッチしましょう。"),
    ("Good effort today, see you next class.", "今日はよく頑張りました、また次のクラスで。"),
    ("Reset to your starting position.", "元の位置に戻ってください。"),
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
                "VALUES (?, ?, '武道・格闘技の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
