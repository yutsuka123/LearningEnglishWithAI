# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a new "ダンス・大道芸" domain/scene: vocabulary and phrases for dance in
general (including Japanese traditional dance), pole dance, busking/street
performance, stage combat (殺陣＝舞台での立ち回り), ventriloquism, and
magic/close-up magic, authored by Claude (2026-08-10・ユーザー要望).

対象語彙: ダンス全般の基本用語(dance, dancer, choreography, choreographer,
routine, rehearsal, warm-up, stretch, stage, spotlight, curtain call, bow,
applause, audience, gesture)、日本舞踊でも使う一般語(folding fan)、ポール
ダンスの基本用語(pole, spin, grip, inversion, core strength)、大道芸の基本
用語(busker, street performer, juggling, unicycle, balance, tip jar,
crowd)、殺陣(舞台での立ち回り)の基本用語(stage combat, prop sword, cue,
timing)、腹話術の基本用語(ventriloquist, puppet, throw one's voice)、マジッ
ク・手品の基本用語(magician, magic trick, sleight of hand, misdirection,
illusion)。特定の流派・団体・実在の演者名などの固有名詞は一切使用せず、すべ
て一般的な用語のみ。

フレーズは練習・稽古・本番・観客とのやり取りで実際に使う自然な口語表現
("Let's run through the routine one more time." "Pick a card, any card."
など)。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_dance_performance.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- ダンス全般の基本語 ---
    ("dance", "踊る・ダンス", "動詞", "She started to dance the moment the music began.", "ダンス・大道芸", "300"),
    ("dancer", "ダンサー・踊り手", "名詞", "The dancer bowed to the audience after the final note.", "ダンス・大道芸", "300"),
    ("choreography", "振り付け", "名詞", "The choreography blends sharp turns with slow, flowing arms.", "ダンス・大道芸", "600"),
    ("choreographer", "振付師", "名詞", "The choreographer adjusted the spacing between the dancers.", "ダンス・大道芸", "650"),
    ("routine", "一連の振り付け・ルーティン", "名詞", "We ran through the routine twice before the show.", "ダンス・大道芸", "500"),
    ("rehearsal", "リハーサル・稽古", "名詞", "The last rehearsal before opening night ran late.", "ダンス・大道芸", "450"),
    ("warm-up", "ウォームアップ・準備運動", "名詞", "Never skip the warm-up, even for a short performance.", "ダンス・大道芸", "400"),
    ("stretch", "ストレッチをする", "動詞", "Stretch your shoulders before you attempt that lift.", "ダンス・大道芸", "350"),
    ("stage", "舞台・ステージ", "名詞", "The lights came up as she stepped onto the stage.", "ダンス・大道芸", "300"),
    ("spotlight", "スポットライト", "名詞", "A single spotlight followed the dancer across the floor.", "ダンス・大道芸", "500"),
    # --- 観客・本番 ---
    ("curtain call", "カーテンコール", "名詞", "The whole cast returned for the curtain call.", "ダンス・大道芸", "700"),
    ("bow", "お辞儀をする", "動詞", "All the performers bowed together at the end.", "ダンス・大道芸", "400"),
    ("applause", "拍手", "名詞", "The trick was met with loud applause.", "ダンス・大道芸", "500"),
    ("audience", "観客", "名詞", "The audience held its breath during the final spin.", "ダンス・大道芸", "350"),
    ("gesture", "身振り・仕草", "名詞", "In Japanese dance, even a small gesture carries meaning.", "ダンス・大道芸", "550"),
    ("folding fan", "扇子", "名詞", "She snapped the folding fan open in one smooth motion.", "ダンス・大道芸", "600"),
    # --- ポールダンス ---
    ("pole", "ポール(ダンス用の支柱)", "名詞", "She wrapped one leg around the pole and lifted off the floor.", "ダンス・大道芸", "500"),
    ("spin", "回転する・スピンする", "動詞", "Spin slowly at first until you find your balance.", "ダンス・大道芸", "400"),
    ("grip", "握り・グリップ", "名詞", "Chalk improves your grip on the pole.", "ダンス・大道芸", "550"),
    ("inversion", "倒立技・逆さの姿勢", "名詞", "The inversion took months of core training to master.", "ダンス・大道芸", "750"),
    ("core strength", "体幹の強さ", "名詞", "Core strength keeps every move controlled instead of shaky.", "ダンス・大道芸", "650"),
    # --- 大道芸 ---
    ("busker", "大道芸人・ストリートミュージシャン", "名詞", "The busker played guitar outside the station every evening.", "ダンス・大道芸", "700"),
    ("street performer", "大道芸人", "名詞", "A street performer juggled knives in the square.", "ダンス・大道芸", "550"),
    ("juggling", "ジャグリング", "名詞", "He kept four balls in the air while juggling.", "ダンス・大道芸", "500"),
    ("unicycle", "一輪車", "名詞", "She rode a unicycle while juggling torches.", "ダンス・大道芸", "600"),
    ("balance", "バランス・平衡感覚", "名詞", "Balance matters more than speed in this act.", "ダンス・大道芸", "400"),
    ("tip jar", "投げ銭入れ・チップ用の容器", "名詞", "Passersby dropped coins into the tip jar.", "ダンス・大道芸", "650"),
    ("crowd", "観衆・人だかり", "名詞", "A small crowd gathered to watch the act.", "ダンス・大道芸", "350"),
    # --- 殺陣(舞台での立ち回り) ---
    ("stage combat", "殺陣・舞台上の立ち回り", "名詞", "Stage combat looks dangerous but every hit is carefully timed.", "ダンス・大道芸", "750"),
    ("prop sword", "小道具の刀", "名詞", "The actors rehearsed with a prop sword for weeks.", "ダンス・大道芸", "700"),
    ("cue", "合図・キュー", "名詞", "Wait for your cue before you draw the sword.", "ダンス・大道芸", "550"),
    ("timing", "タイミング", "名詞", "Good timing is what makes a stage fight believable.", "ダンス・大道芸", "500"),
    # --- 腹話術 ---
    ("ventriloquist", "腹話術師", "名詞", "The ventriloquist's lips barely moved as the puppet spoke.", "ダンス・大道芸", "800"),
    ("puppet", "人形・パペット", "名詞", "The puppet seemed to argue back with its owner.", "ダンス・大道芸", "500"),
    ("throw one's voice", "声を投げる(腹話術の技法)", "動詞句", "It takes years of practice to throw your voice convincingly.", "ダンス・大道芸", "850"),
    # --- マジック・手品 ---
    ("magician", "マジシャン・手品師", "名詞", "The magician asked a volunteer to pick a card.", "ダンス・大道芸", "400"),
    ("magic trick", "手品・マジック", "名詞", "That magic trick fooled the whole room.", "ダンス・大道芸", "400"),
    ("sleight of hand", "手先の早業", "名詞", "Sleight of hand is the secret behind most card tricks.", "ダンス・大道芸", "800"),
    ("misdirection", "ミスディレクション(注意をそらす技法)", "名詞", "Misdirection makes the audience look the wrong way at the right moment.", "ダンス・大道芸", "850"),
    ("illusion", "錯覚・イリュージョン", "名詞", "The disappearing box is a classic stage illusion.", "ダンス・大道芸", "600"),
]

PHRASES: list[tuple[str, str]] = [
    ("Let's run through the routine one more time.", "もう一度ルーティンを通しでやってみましょう。"),
    ("Can we take it from the top?", "最初からやり直せますか？"),
    ("Watch your spacing on this part.", "この部分は間隔に気をつけてください。"),
    ("Five minutes until places, everyone.", "皆さん、開始位置につくまであと5分です。"),
    ("Break a leg out there.", "本番、うまくいきますように。"),
    ("Let's mark through the choreography first.", "まずは振りを軽くさらいましょう。"),
    ("Can you slow that count down for me?", "そのカウントをもう少しゆっくりにしてもらえますか？"),
    ("I lost the count somewhere in the middle.", "途中でカウントを見失いました。"),
    ("Keep your eyes on the audience, not the floor.", "床ではなく客席の方を見てください。"),
    ("Save your energy for the second half.", "後半のためにスタミナを温存してください。"),
    ("That landing needs to be cleaner.", "その着地はもっとクリーンにする必要があります。"),
    ("Chalk up before you get on the pole.", "ポールに上がる前にチョークをつけてください。"),
    ("Spot me on this trick, please.", "この技、補助（見守り）をお願いします。"),
    ("Gather round, the show's about to start!", "集まってください、まもなくショーが始まります！"),
    ("Feel free to drop a tip if you enjoyed the show.", "楽しんでいただけたら、投げ銭よろしくお願いします。"),
    ("Step back a little, please, for everyone's safety.", "安全のため、少し下がってください。"),
    ("Give it up for our next performer!", "次の演者に盛大な拍手を！"),
    ("Can I get a volunteer from the audience?", "観客の中からボランティアをお願いできますか？"),
    ("Pick a card, any card.", "カードを一枚選んでください、どれでも構いません。"),
    ("Watch closely, nothing up my sleeve.", "よく見ていてください、何も仕込みはありませんよ。"),
    ("Let's block out the sword fight in slow motion first.", "まずは剣の立ち回りをスローモーションで振り付けしましょう。"),
    ("Freeze right there, that's your cue.", "そこで止まって、それが合図です。"),
    ("Nobody gets near the blade during rehearsal.", "稽古中は誰も刃物に近づかないようにしてください。"),
    ("Let's go over the safety checks before we start.", "始める前に安全確認をしましょう。"),
    ("The puppet needs more personality in its voice.", "その人形の声にもっと個性が必要です。"),
    ("Try not to move your lips on that line.", "そのセリフでは唇を動かさないようにしてください。"),
    ("Let's do a full run before we call it a day.", "終わりにする前に通し稽古をしましょう。"),
    ("Thank you all for coming out tonight.", "今夜はお越しいただき、ありがとうございました。"),
    ("That's a wrap for today.", "今日はこれで終わりです。"),
    ("Can we get the music cued up again?", "もう一度音楽を準備してもらえますか？"),
    ("Hold your final pose until the lights go down.", "照明が落ちるまで最後のポーズを保ってください。"),
    ("Let's take five and stretch it out.", "5分休憩して、体をストレッチしましょう。"),
    ("I need a mirror to check my form.", "フォームを確認するために鏡が必要です。"),
    ("The crowd's really into it tonight.", "今夜のお客さんはノリがいいですね。"),
    ("One more bow, everyone, together now.", "みなさん、もう一度お辞儀を、せーので。"),
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
                "VALUES (?, ?, 'ダンス・パフォーマンスの英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
