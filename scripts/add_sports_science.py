# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a new "スポーツ科学" domain/scene: vocabulary and phrases for sports
science / exercise physiology terminology, authored by Claude (2026-08-10・
ユーザー要望).

対象語彙: 生理学的指標(VO2 max、有酸素能力、無酸素性作業閾値、乳酸閾値、
心拍変動)、筋・トレーニング理論(速筋/遅筋線維、プライオメトリックトレー
ニング、等尺性/求心性/遠心性収縮、筋肥大、インターバル/クロストレーニン
グ)、トレーニング計画(ピリオダイゼーション、メソサイクル、テーパリング、
オーバートレーニング症候群、高地トレーニング)、動作分析(バイオメカニクス、
キネティックチェーン、固有受容感覚、床反力)、コンディショニング/障害予防
(リカバリープロトコル、スポーツ栄養、外傷予防、競技復帰プロトコル、遅発性
筋肉痛)、心理面(スポーツ心理学、ピークパフォーマンス)。既存`医療`(基礎的
な体の部位語彙)・`スポーツ`(水泳・陸上競技等の実践語彙)・`保健`(公衆衛生
用語)とは重複しない、より専門的なスポーツ科学用語のみを扱う。

フレーズはトレーナー・コーチが選手に対して実際に使う自然な英語表現
("Let's check your heart rate variability before today's session." など)。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_sports_science.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 生理学的指標 ---
    ("VO2 max", "最大酸素摂取量", "名詞", "Her VO2 max improved significantly after months of interval training.", "スポーツ科学", "750"),
    ("aerobic capacity", "有酸素能力", "名詞", "We need to build your aerobic capacity before adding speed work.", "スポーツ科学", "700"),
    ("anaerobic threshold", "無酸素性作業閾値", "名詞", "Training just below your anaerobic threshold improves endurance.", "スポーツ科学", "800"),
    ("lactate threshold", "乳酸閾値", "名詞", "Your lactate threshold largely determines your sustainable race pace.", "スポーツ科学", "800"),
    ("heart rate variability", "心拍変動", "名詞", "We track heart rate variability every morning to monitor recovery.", "スポーツ科学", "750"),
    ("cardiorespiratory fitness", "心肺持久力", "名詞", "Cardiorespiratory fitness is one of the strongest predictors of long-term health.", "スポーツ科学", "800"),
    # --- 筋・トレーニング理論 ---
    ("muscle fiber", "筋線維", "名詞", "Sprinters tend to have a higher proportion of fast-twitch muscle fiber.", "スポーツ科学", "700"),
    ("fast-twitch fiber", "速筋線維", "名詞", "Fast-twitch fiber contracts quickly but tires faster than slow-twitch fiber.", "スポーツ科学", "800"),
    ("slow-twitch fiber", "遅筋線維", "名詞", "Marathon runners rely heavily on slow-twitch fiber for sustained effort.", "スポーツ科学", "800"),
    ("plyometric training", "プライオメトリックトレーニング", "名詞", "Plyometric training will help you jump higher and react faster.", "スポーツ科学", "800"),
    ("isometric contraction", "等尺性収縮", "名詞", "Holding a plank is a classic example of an isometric contraction.", "スポーツ科学", "800"),
    ("concentric contraction", "求心性収縮", "名詞", "The upward phase of a squat is a concentric contraction.", "スポーツ科学", "850"),
    ("eccentric contraction", "遠心性収縮", "名詞", "Eccentric contraction, the lengthening phase, often causes the most muscle soreness.", "スポーツ科学", "850"),
    ("hypertrophy", "筋肥大", "名詞", "Higher training volume tends to drive more hypertrophy than heavy singles.", "スポーツ科学", "850"),
    ("interval training", "インターバルトレーニング", "名詞", "Interval training alternates short bursts of intense effort with rest.", "スポーツ科学", "650"),
    ("cross-training", "クロストレーニング", "名詞", "Cross-training with cycling can reduce overuse injuries in runners.", "スポーツ科学", "650"),
    # --- トレーニング計画 ---
    ("periodization", "期分け・ピリオダイゼーション", "名詞", "Let's periodize your training over the next twelve weeks.", "スポーツ科学", "850"),
    ("mesocycle", "メソサイクル(中期周期)", "名詞", "Each mesocycle in the plan lasts about four weeks.", "スポーツ科学", "900"),
    ("tapering", "テーパリング(調整期)", "名詞", "We start tapering two weeks before the race to let your body recover.", "スポーツ科学", "800"),
    ("overtraining syndrome", "オーバートレーニング症候群", "名詞", "He's showing early signs of overtraining syndrome, including chronic fatigue.", "スポーツ科学", "850"),
    ("altitude training", "高地トレーニング", "名詞", "Altitude training stimulates the body to produce more red blood cells.", "スポーツ科学", "750"),
    # --- 動作分析 ---
    ("biomechanics", "バイオメカニクス・生体力学", "名詞", "Biomechanics analyzes the forces and motion of the human body during exercise.", "スポーツ科学", "800"),
    ("kinetic chain", "運動連鎖(キネティックチェーン)", "名詞", "We're analyzing your kinetic chain to figure out why your shoulder hurts.", "スポーツ科学", "850"),
    ("proprioception", "固有受容感覚", "名詞", "Balance drills improve proprioception and help prevent ankle sprains.", "スポーツ科学", "850"),
    ("ground reaction force", "床反力", "名詞", "We measure ground reaction force on the force plate to analyze your running form.", "スポーツ科学", "900"),
    # --- コンディショニング・障害予防 ---
    ("recovery protocol", "回復プロトコル", "名詞", "A good recovery protocol is just as important as the training itself.", "スポーツ科学", "700"),
    ("sports nutrition", "スポーツ栄養学", "名詞", "A sports nutritionist can help you plan your pre-race meals.", "スポーツ科学", "650"),
    ("injury prevention", "外傷予防", "名詞", "Injury prevention starts with a proper warm-up routine.", "スポーツ科学", "650"),
    ("return to play protocol", "競技復帰プロトコル", "名詞", "We'll follow a strict return to play protocol after your injury.", "スポーツ科学", "850"),
    ("delayed onset muscle soreness", "遅発性筋肉痛(DOMS)", "名詞", "You'll likely feel some delayed onset muscle soreness a day or two after a hard workout.", "スポーツ科学", "900"),
    # --- 心理面 ---
    ("sports psychology", "スポーツ心理学", "名詞", "Sports psychology can make the difference in a close competition.", "スポーツ科学", "700"),
    ("peak performance", "ピークパフォーマンス", "名詞", "Athletes train for months to reach peak performance on race day.", "スポーツ科学", "700"),
]

PHRASES: list[tuple[str, str]] = [
    ("Let's check your heart rate variability before today's session.", "今日のセッションの前に心拍変動をチェックしましょう。"),
    ("We need to build your aerobic base before adding speed work.", "スピード練習を加える前に有酸素能力の基礎を作る必要があります。"),
    ("Your VO2 max has improved since last month.", "先月からVO2 maxが向上していますね。"),
    ("Let's start the tapering phase two weeks before the race.", "レースの2週間前からテーパリング期に入りましょう。"),
    ("He's showing early signs of overtraining syndrome.", "彼はオーバートレーニング症候群の初期症状が出ています。"),
    ("Focus on proprioception drills to prevent ankle sprains.", "足首の捻挫予防のために固有受容感覚のドリルに集中しましょう。"),
    ("We'll follow a strict return to play protocol after your injury.", "怪我の後は厳格な競技復帰プロトコルに従います。"),
    ("Plyometric training will help you jump higher.", "プライオメトリックトレーニングはジャンプ力向上に役立ちます。"),
    ("Let's periodize your training over the next twelve weeks.", "これから12週間のトレーニングを期分けしましょう。"),
    ("Your lactate threshold determines your race pace.", "あなたの乳酸閾値がレースペースを決めます。"),
    ("Recovery protocols are just as important as training itself.", "回復プロトコルはトレーニング自体と同じくらい重要です。"),
    ("Sports psychology can make the difference in close competitions.", "スポーツ心理学は接戦での差を生むことがあります。"),
    ("We're analyzing your kinetic chain to fix that shoulder pain.", "その肩の痛みを直すために運動連鎖を分析しています。"),
    ("Let's do some cross-training to avoid overuse injuries.", "使いすぎによる怪我を避けるためにクロストレーニングをしましょう。"),
    ("You'll feel some delayed onset muscle soreness tomorrow.", "明日は少し遅発性筋肉痛を感じるでしょう。"),
    ("A sports nutritionist can help you plan your pre-race meals.", "スポーツ栄養士がレース前の食事プランを手伝ってくれます。"),
    ("We measure ground reaction force to analyze your running form.", "あなたのランニングフォームを分析するために床反力を測定します。"),
    ("This exercise mainly targets your fast-twitch muscle fiber.", "この種目は主に速筋線維を鍛えます。"),
    ("Injury prevention starts with a proper warm-up routine.", "外傷予防は適切なウォームアップルーティンから始まります。"),
    ("Let's schedule your altitude training camp for next month.", "来月に高地トレーニングキャンプの予定を入れましょう。"),
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
                "VALUES (?, ?, 'スポーツ科学の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
