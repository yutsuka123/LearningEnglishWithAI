# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a new "球技・アウトドアスポーツ" domain/scene: vocabulary and phrases for
ball games and outdoor sports not yet covered by the existing "スポーツ"
(swimming/athletics-focused) and "アウトドア・レジャー" (hiking/climbing/
parkour/skiing-focused) domains, authored by Claude (2026-08-10・ユーザー
要望).

対象語彙: ラグビー(rugby, try, ruck, maul, lineout, conversion)、乗馬
(equestrian, horseback riding, saddle, stirrup, reins, trot, canter)、
ビリヤード(billiards, cue, cue ball, rack, pocket)、ボウリング(bowling,
bowling alley, bowling pin, gutter, strike)、トライアスロン(triathlon,
transition zone, brick workout)、ボクササイズ(boxercise, shadow boxing,
uppercut, sparring, heavy bag)、その他の球技(badminton, shuttlecock,
table tennis, volleyball, spike, handball, golf)。ダイビング・シュノーケ
リング・ボルダリング・クライミング・パルクールは既存の「アウトドア・
レジャー」ドメインに既にかなりの語彙があるため、このファイルでは扱わない。
特定の団体・大会・商標名(例: Ironman等)は使用せず、すべて一般的な用語のみ。

フレーズは実際にプレイ中・練習中に使う自然な口語表現("Nice shot! Straight
into the pocket." "Let's do a brick workout this weekend." など)。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_ball_outdoor_sports.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- ラグビー ---
    ("rugby", "ラグビー", "名詞", "Rugby is a fast, physical sport played with an oval ball.", "球技・アウトドアスポーツ", "400"),
    ("try", "トライ(ラグビーの得点)", "名詞", "The winger sprinted forty meters to score a try.", "球技・アウトドアスポーツ", "650"),
    ("ruck", "ラック(密集して球を奪い合う局面)", "名詞", "Players bind together to compete for the ball at the ruck.", "球技・アウトドアスポーツ", "800"),
    ("maul", "モール(選手が密集したままボールを前進させるプレー)", "名詞", "The forwards drove the maul over the try line.", "球技・アウトドアスポーツ", "850"),
    ("lineout", "ラインアウト", "名詞", "The hooker threw the ball in straight at the lineout.", "球技・アウトドアスポーツ", "800"),
    ("conversion", "コンバージョンキック(トライ後の追加点)", "名詞", "She calmly kicked the conversion to seal the win.", "球技・アウトドアスポーツ", "750"),
    # --- 乗馬 ---
    ("equestrian", "乗馬の・馬術の", "形容詞", "She has competed in equestrian events since she was ten.", "球技・アウトドアスポーツ", "700"),
    ("horseback riding", "乗馬", "名詞", "We went horseback riding along the beach at sunset.", "球技・アウトドアスポーツ", "400"),
    ("saddle", "鞍(くら)", "名詞", "Make sure the saddle is secure before you mount the horse.", "球技・アウトドアスポーツ", "500"),
    ("stirrup", "鐙(あぶみ)", "名詞", "Keep your feet balanced in the stirrups as you ride.", "球技・アウトドアスポーツ", "700"),
    ("reins", "手綱", "名詞", "Hold the reins loosely and let the horse find its rhythm.", "球技・アウトドアスポーツ", "500"),
    ("trot", "速歩(はやあし)で進む・トロット", "動詞", "The horse began to trot as soon as she gave the signal.", "球技・アウトドアスポーツ", "600"),
    ("canter", "駈歩(かけあし)で進む・キャンター", "動詞", "We let the horses canter across the open field.", "球技・アウトドアスポーツ", "700"),
    # --- ビリヤード ---
    ("billiards", "ビリヤード", "名詞", "We spent the evening playing billiards at a local bar.", "球技・アウトドアスポーツ", "500"),
    ("cue", "キュー(球を突く棒)", "名詞", "He chalked his cue before taking the shot.", "球技・アウトドアスポーツ", "550"),
    ("cue ball", "手球(キューボール)", "名詞", "Hit the cue ball gently so it doesn't scratch.", "球技・アウトドアスポーツ", "600"),
    ("rack", "ラック(球を三角形に並べる道具・行為)", "名詞", "Let's rack the balls before we start a new game.", "球技・アウトドアスポーツ", "550"),
    ("pocket", "ポケット(球を落とす穴)", "名詞", "He sank the eight ball in the corner pocket.", "球技・アウトドアスポーツ", "500"),
    # --- ボウリング ---
    ("bowling", "ボウリング", "名詞", "We're going bowling with some friends this weekend.", "球技・アウトドアスポーツ", "350"),
    ("bowling alley", "ボウリング場", "名詞", "There's a new bowling alley that just opened downtown.", "球技・アウトドアスポーツ", "400"),
    ("bowling pin", "ボウリングのピン", "名詞", "She knocked down all ten bowling pins on her first try.", "球技・アウトドアスポーツ", "400"),
    ("gutter", "ガター(レーン脇の溝)", "名詞", "His ball rolled straight into the gutter.", "球技・アウトドアスポーツ", "550"),
    ("strike", "ストライク(1投で全ピンを倒すこと)", "名詞", "He got three strikes in a row.", "球技・アウトドアスポーツ", "500"),
    # --- トライアスロン ---
    ("triathlon", "トライアスロン", "名詞", "The triathlon combines swimming, cycling, and running.", "球技・アウトドアスポーツ", "600"),
    ("transition zone", "トランジションゾーン(種目を切り替える場所)", "名詞", "Athletes change gear quickly in the transition zone.", "球技・アウトドアスポーツ", "800"),
    ("brick workout", "ブリックワークアウト(自転車の直後にランを行う練習)", "名詞", "Her coach scheduled a brick workout for Saturday morning.", "球技・アウトドアスポーツ", "850"),
    # --- ボクササイズ ---
    ("boxercise", "ボクササイズ", "名詞", "Boxercise combines boxing moves with cardio fitness training.", "球技・アウトドアスポーツ", "650"),
    ("shadow boxing", "シャドーボクシング", "名詞", "She warmed up with five minutes of shadow boxing.", "球技・アウトドアスポーツ", "600"),
    ("uppercut", "アッパーカット", "名詞", "He landed a sharp uppercut during the drill.", "球技・アウトドアスポーツ", "700"),
    ("sparring", "スパーリング(実戦形式の練習)", "名詞", "The two boxers did some light sparring before the match.", "球技・アウトドアスポーツ", "750"),
    ("heavy bag", "サンドバッグ", "名詞", "She practiced her combinations on the heavy bag.", "球技・アウトドアスポーツ", "550"),
    # --- その他の球技 ---
    ("badminton", "バドミントン", "名詞", "We play badminton in the park every weekend.", "球技・アウトドアスポーツ", "350"),
    ("shuttlecock", "シャトル(バドミントンの羽根)", "名詞", "The shuttlecock landed just inside the line.", "球技・アウトドアスポーツ", "600"),
    ("table tennis", "卓球", "名詞", "Table tennis requires very quick reflexes.", "球技・アウトドアスポーツ", "350"),
    ("volleyball", "バレーボール", "名詞", "Our team practices volleyball twice a week.", "球技・アウトドアスポーツ", "350"),
    ("spike", "スパイク(強打)", "名詞", "She jumped high and hit a powerful spike.", "球技・アウトドアスポーツ", "650"),
    ("handball", "ハンドボール", "名詞", "Handball is fast-paced and involves a lot of scoring.", "球技・アウトドアスポーツ", "500"),
    ("golf", "ゴルフ", "名詞", "He plays golf with his coworkers every Sunday.", "球技・アウトドアスポーツ", "350"),
]

PHRASES: list[tuple[str, str]] = [
    ("Great try!", "ナイストライ！"),
    ("Watch the tackle!", "タックルに気をつけて！"),
    ("Who's kicking the conversion?", "コンバージョンキックは誰が蹴るの？"),
    ("Bind in tight at the ruck.", "ラックではしっかり組んで。"),
    ("Let's saddle up.", "鞍を付けて準備しよう。"),
    ("Hold the reins steady.", "手綱をしっかり持って。"),
    ("Can we go for a trot?", "速歩で進んでみようか？"),
    ("Keep your heels down in the stirrups.", "鐙の中でかかとを下げて。"),
    ("Rack 'em up.", "球を並べて。"),
    ("It's your shot.", "あなたの番だよ。"),
    ("Watch out, don't scratch.", "気をつけて、スクラッチしないように。"),
    ("Nice shot! Straight into the pocket.", "ナイスショット！まっすぐポケットに入った。"),
    ("I got a strike!", "ストライクが出た！"),
    ("So close, just missed the spare.", "惜しい、スペアを逃した。"),
    ("Watch out for the gutter.", "ガターに気をつけて。"),
    ("Whose turn is it to bowl?", "次は誰が投げる番？"),
    ("How was your transition time?", "トランジションのタイムはどうだった？"),
    ("Let's do a brick workout this weekend.", "今週末ブリックワークアウトをしよう。"),
    ("Don't forget to hydrate during the race.", "レース中の水分補給を忘れずに。"),
    ("Let's warm up with some shadow boxing.", "シャドーボクシングでウォーミングアップしよう。"),
    ("Keep your guard up.", "ガードを上げたままにして。"),
    ("Hit the bag ten more times.", "サンドバッグをあと10回打って。"),
    ("Are you up for some light sparring?", "軽いスパーリングをやってみる？"),
    ("Nice spike!", "ナイススパイク！"),
    ("Let's rally for a bit before we keep score.", "得点をつける前に少しラリーしよう。"),
    ("Whose serve is it?", "サーブは誰の番？"),
    ("Good game!", "ナイスゲーム！"),
    ("Let's switch sides.", "コートチェンジしよう。"),
    ("Can we play doubles?", "ダブルスで遊べる？"),
    ("I need a new shuttlecock.", "新しいシャトルが必要だ。"),
    ("Do you want to play a round of golf this weekend?", "今週末ゴルフを一緒にラウンドしない？"),
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
                "VALUES (?, ?, 'スポーツ・アウトドアの英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
