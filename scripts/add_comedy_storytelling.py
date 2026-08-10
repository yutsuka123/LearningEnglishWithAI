# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a new "話芸・コメディ" domain/scene: vocabulary and phrases for comedy
and spoken storytelling in English — stand-up comedy, sketch comedy, improv,
and how to explain Japanese traditional storytelling arts (rakugo, manzai)
to English speakers, authored by Claude (2026-08-10・ユーザー要望).

対象語彙: コメディ全般の基本用語(punchline、setup、timing、delivery、heckler、
comic relief等)、スタンダップコメディの用語(stand-up comedy、open mic、
one-liner、callback、bit、crowd work等)、コント・寸劇の用語(sketch、skit、
improv、character comedy、slapstick、deadpan、running gag等)、観客の反応
(laugh out loud、burst into laughter、groan、awkward silence等)、そして
落語・漫才など日本の伝統話芸を外国人に説明するための表現(a single
storyteller playing multiple roles、using only a fan and a small cloth as
props、a comic duo with a straight man and a funny man等)。実在のコメディ
アン名・番組名・作品名などの固有名詞は一切使用せず、すべて一般的な用語のみ。

フレーズは演者としての表現("Let me set up the joke.")、観客としての反応
("That was hilarious!")、そして落語・漫才を外国人に説明する表現("The
performer plays every character by just changing his voice and posture."
など)を含む自然な口語表現。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_comedy_storytelling.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 基本語 ---
    ("joke", "冗談・ジョーク", "名詞", "She told a joke that made everyone laugh.", "話芸・コメディ", "300"),
    ("funny", "面白い・おかしい", "形容詞", "That story was really funny.", "話芸・コメディ", "300"),
    ("laugh", "笑う", "動詞", "The whole audience started to laugh.", "話芸・コメディ", "300"),
    ("audience", "観客", "名詞", "The audience clapped after the performance.", "話芸・コメディ", "400"),
    ("performer", "演者・パフォーマー", "名詞", "The performer bowed at the end of the show.", "話芸・コメディ", "400"),
    ("stage", "舞台", "名詞", "She walked onto the stage with confidence.", "話芸・コメディ", "350"),
    ("humor", "ユーモア", "名詞", "His humor put everyone at ease.", "話芸・コメディ", "450"),
    ("timing", "間・タイミング", "名詞", "Good comedy depends heavily on timing.", "話芸・コメディ", "500"),
    ("punchline", "オチ・パンチライン", "名詞", "The punchline caught the whole room off guard.", "話芸・コメディ", "600"),
    ("setup", "ジョークの前振り", "名詞", "A good setup makes the punchline land harder.", "話芸・コメディ", "650"),
    ("delivery", "話し方・語り口", "名詞", "His deadpan delivery made the joke even funnier.", "話芸・コメディ", "650"),
    ("heckler", "野次を飛ばす客", "名詞", "The comedian handled the heckler with a quick comeback.", "話芸・コメディ", "800"),
    ("comic relief", "コミックリリーフ(緊張を和らげる笑い)", "名詞", "The clumsy sidekick provides comic relief in the story.", "話芸・コメディ", "750"),
    ("stand-up comedy", "スタンダップコメディ", "名詞", "She performs stand-up comedy at a small club every weekend.", "話芸・コメディ", "600"),
    ("comedian", "コメディアン", "名詞", "The comedian told stories about his childhood.", "話芸・コメディ", "500"),
    ("open mic", "オープンマイク(誰でも出演できる小規模ステージ)", "名詞", "New comedians often start out at an open mic night.", "話芸・コメディ", "700"),
    ("one-liner", "一言オチのジョーク", "名詞", "He specializes in short, sharp one-liners.", "話芸・コメディ", "700"),
    ("callback", "コールバック(前のネタへの回収)", "名詞", "The comedian used a callback to an earlier joke for a bigger laugh.", "話芸・コメディ", "800"),
    ("bit", "持ちネタ・一まとまりの話", "名詞", "That bit about airports always gets a big laugh.", "話芸・コメディ", "600"),
    ("crowd work", "客いじり", "名詞", "She does a lot of crowd work before starting her set.", "話芸・コメディ", "800"),
    ("set", "持ち時間・演目一式", "名詞", "His set lasted about twenty minutes.", "話芸・コメディ", "550"),
    ("sketch", "コント・寸劇", "名詞", "The group performed a short sketch about a job interview.", "話芸・コメディ", "550"),
    ("skit", "寸劇・ちょっとした劇", "名詞", "They wrote a funny skit for the school festival.", "話芸・コメディ", "550"),
    ("improv", "即興劇・インプロ", "名詞", "The actors made up the whole scene through improv.", "話芸・コメディ", "700"),
    ("character comedy", "キャラクターコメディ", "名詞", "She built her act around a single strange character comedy.", "話芸・コメディ", "800"),
    ("slapstick", "ドタバタ喜劇", "名詞", "The film relies heavily on slapstick humor.", "話芸・コメディ", "800"),
    ("deadpan", "無表情な・淡々とした", "形容詞", "He delivered the joke in a completely deadpan tone.", "話芸・コメディ", "850"),
    ("running gag", "繰り返し出てくる持ちネタ", "名詞", "The umbrella joke became a running gag throughout the show.", "話芸・コメディ", "800"),
    ("improvise", "即興で演じる", "動詞", "The performers had to improvise when a prop broke.", "話芸・コメディ", "700"),
    ("burst into laughter", "笑い出す・爆笑する", "動詞", "The whole room burst into laughter at the punchline.", "話芸・コメディ", "650"),
    ("groan", "うんざりして声を出す", "動詞", "The audience let out a groan at the terrible pun.", "話芸・コメディ", "700"),
    ("awkward silence", "気まずい沈黙", "名詞", "The joke was met with an awkward silence.", "話芸・コメディ", "700"),
    ("witty", "気の利いた・機知に富んだ", "形容詞", "She gave a witty reply that made everyone smile.", "話芸・コメディ", "750"),
    ("pun", "駄洒落", "名詞", "He can never resist making a pun.", "話芸・コメディ", "600"),
    ("satire", "風刺", "名詞", "The show is a gentle satire of office life.", "話芸・コメディ", "800"),
    ("parody", "パロディ", "名詞", "The sketch is a parody of a typical morning news program.", "話芸・コメディ", "750"),
    ("straight man", "ツッコミ役(漫才等の常識人役)", "名詞", "In the duo, one plays the straight man and reacts to the jokes.", "話芸・コメディ", "800"),
    ("funny man", "ボケ役(漫才等のとぼけ役)", "名詞", "The funny man keeps making outrageous mistakes on purpose.", "話芸・コメディ", "800"),
    ("storyteller", "語り手", "名詞", "A single storyteller can bring a whole cast of characters to life.", "話芸・コメディ", "500"),
    ("narration", "語り・ナレーション", "名詞", "The story is told entirely through the performer's narration.", "話芸・コメディ", "600"),
]

PHRASES: list[tuple[str, str]] = [
    ("Let me set up the joke.", "ジョークの前振りをさせてください。"),
    ("And here comes the punchline.", "そしてここでオチが来ます。"),
    ("That was hilarious!", "それ、すごく面白かった！"),
    ("I couldn't stop laughing.", "笑いが止まりませんでした。"),
    ("You have great comic timing.", "あなたは笑いの間の取り方がとても上手ですね。"),
    ("Sorry, that joke didn't land.", "すみません、今のジョークはウケませんでしたね。"),
    ("Can you do a bit about daily life?", "日常生活についてのネタをやってもらえますか？"),
    ("He's really good at crowd work.", "彼は客いじりが本当にうまいです。"),
    ("Let's improvise this scene.", "このシーンは即興でやりましょう。"),
    ("Keep a straight face during this part.", "この部分では真顔を保ってください。"),
    ("That's an old running gag of ours.", "それは私たちの昔からの持ちネタです。"),
    ("The audience went completely silent.", "観客は完全に静まり返りました。"),
    ("Nice callback to the earlier joke.", "さっきのジョークへの回収、うまいですね。"),
    ("His delivery was completely deadpan.", "彼の話し方は完全に無表情でした。"),
    ("I bombed on stage last night.", "昨夜のステージは滑ってしまいました。"),
    ("She killed it at the open mic.", "彼女はオープンマイクで大ウケでした。"),
    ("Don't worry, the audience loves a good pun.", "心配しないで、観客は駄洒落が好きですから。"),
    ("Let's rehearse the sketch one more time.", "もう一度コントを通し稽古しましょう。"),
    ("Who's playing the straight man in this scene?", "このシーンでは誰がツッコミ役をやりますか？"),
    ("I love how absurd this skit is.", "このコント、ばかばかしくて大好きです。"),
    ("In rakugo, a single performer plays every character in the story.", "落語では、一人の演者が物語の登場人物すべてを演じます。"),
    ("The performer changes voice and posture to switch between characters.", "演者は声や姿勢を変えることで、登場人物を切り替えます。"),
    ("Rakugo storytellers use only a fan and a small cloth as props.", "落語家は扇子と手ぬぐいだけを小道具として使います。"),
    ("The fan can represent chopsticks, a pipe, or even a letter.", "扇子は箸やキセル、手紙などいろいろなものを表すことができます。"),
    ("Every rakugo story ends with a clever twist called the punchline.", "落語の話はどれも「オチ」と呼ばれる気の利いた結末で終わります。"),
    ("Manzai is a comic duo act with a straight man and a funny man.", "漫才はツッコミ役とボケ役からなる二人組のお笑いです。"),
    ("The funny man says something silly, and the straight man corrects him.", "ボケ役が変なことを言い、ツッコミ役がそれを訂正します。"),
    ("It's a traditional style of Japanese spoken storytelling.", "それは日本の伝統的な話芸のスタイルです。"),
    ("The stories are often passed down from master to apprentice.", "その話は師匠から弟子へと受け継がれることが多いです。"),
    ("Even without costumes or sets, the story feels very vivid.", "衣装やセットがなくても、物語はとても生き生きと感じられます。"),
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
                "VALUES (?, ?, '話芸・コメディの英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
