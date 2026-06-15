# ruff: noqa: E501
"""AI ステータス語彙: Claude などの AI が「考え中/処理中」に表示する英単語
(Thinking / Deliberating / Pondering / Ruminating ... )を学習用に追加する。

表示はたいてい -ing 形だが、学習しやすいように **原形(基本語)** で登録する。
意味は一般的な辞書義(AIは「じっくり考える/処理する」の意味で使っている)。
domain="AI"。english で重複判定し、既存語は例文だけ補充する。著者は Claude
(app/OpenAI API は呼ばない)。

Run: python scripts/add_ai_status_words.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# (english, japanese, example, level)  ※ part_of_speech は "動詞" 固定
ITEMS: list[tuple[str, str, str, str]] = [
    # --- 「熟考する」系 ---
    ("ponder", "熟考する", "She pondered the question for a while.", "800"),
    ("deliberate", "熟考する・審議する", "The jury deliberated for hours.", "800"),
    ("ruminate", "思いめぐらす・反芻する", "He ruminated on the problem all night.", "900"),
    ("cogitate", "じっくり考える", "She cogitated over the puzzle.", "990"),
    ("muse", "思いにふける", "He mused about his future.", "800"),
    ("mull", "じっくり考える(mull over)", "Let me mull it over.", "800"),
    ("contemplate", "熟考する・じっと見る", "She contemplated her next move.", "700"),
    ("meditate", "瞑想する・熟考する", "She meditated on the issue.", "700"),
    ("reflect", "よく考える・反映する", "He reflected on his mistakes.", "600"),
    ("speculate", "推測する", "Investors speculate about prices.", "800"),
    ("theorize", "理論を立てる", "Scientists theorized about the cause.", "800"),
    ("hypothesize", "仮説を立てる", "She hypothesized a link.", "900"),
    ("pontificate", "もったいぶって語る", "He loves to pontificate about art.", "990"),
    ("puzzle", "頭を悩ませる(puzzle over)", "He puzzled over the riddle.", "600"),
    # --- 「考えを生み出す/練る」系 ---
    ("formulate", "策定する・公式化する", "We formulated a strategy.", "800"),
    ("devise", "考案する", "She devised a clever test.", "800"),
    ("concoct", "でっち上げる・調合する", "They concocted a new plan.", "900"),
    ("conjure", "思い浮かべる・呼び出す", "He conjured a clever solution.", "900"),
    ("brainstorm", "ブレインストーミングする", "Let's brainstorm some ideas.", "700"),
    ("ideate", "着想する", "The team ideated for an hour.", "990"),
    ("strategize", "戦略を練る", "We need to strategize first.", "800"),
    ("orchestrate", "うまく仕組む・指揮する", "She orchestrated the whole event.", "900"),
    ("noodle", "あれこれ考える(略式)", "Let me noodle on that idea.", "990"),
    # --- 「煮詰める/温める」系(料理メタファー) ---
    ("brew", "醸造する・(事が)生じる", "A plan was brewing in his mind.", "700"),
    ("percolate", "浸透する・じわじわ広がる", "The idea percolated through the team.", "900"),
    ("marinate", "(考えを)寝かせる・漬ける", "Let the idea marinate overnight.", "800"),
    ("simmer", "とろ火で煮る・くすぶる", "Let the plan simmer for a day.", "700"),
    ("stew", "思い悩む・煮込む", "Don't stew over small mistakes.", "700"),
    ("distill", "蒸留する・(要点を)抽出する", "Distill the report into one page.", "900"),
    ("incubate", "温める・(計画を)育てる", "We incubate new ideas here.", "900"),
    ("germinate", "芽生える・(考えが)生じる", "An idea germinated in her mind.", "900"),
    ("gestate", "(考えを)温める・妊娠している", "The idea was still gestating.", "990"),
    ("synthesize", "統合する・合成する", "She synthesized the findings.", "900"),
    # --- 「処理する/計算する」系 ---
    ("compute", "計算する", "The system computes the result.", "700"),
    ("crunch", "(数字を)処理する・かみ砕く", "The computer crunches the numbers.", "700"),
    ("churn", "かき混ぜる・大量にこなす", "The machine churns through data.", "800"),
    ("parse", "解析する・構文解析する", "The program parses the text.", "800"),
    ("decipher", "解読する", "She deciphered the code.", "800"),
    ("untangle", "もつれを解く・解明する", "He untangled the complex problem.", "800"),
    ("wrangle", "手こずって扱う・論争する", "He wrangled with the messy data.", "900"),
    ("finagle", "うまく手に入れる・画策する", "She finagled a better deal.", "990"),
    ("reckon", "考える・見積もる", "I reckon it will work.", "700"),
    ("ascertain", "確かめる", "We must ascertain the facts.", "900"),
    ("discern", "識別する・見分ける", "It is hard to discern the difference.", "900"),
    ("tinker", "いじって直す・試行錯誤する", "He tinkered with the engine.", "800"),
    ("whir", "ブーンと回る", "The cooling fan whirred quietly.", "900"),
    # --- 「動き回る/精を出す」系(ゆるい表示語) ---
    ("toil", "あくせく働く", "They toiled through the night.", "800"),
    ("frolic", "はしゃぎ回る", "The children frolicked in the park.", "900"),
    ("mosey", "ぶらぶら歩く(略式)", "He moseyed over to the desk.", "990"),
    ("doodle", "いたずら書きする", "She doodled in the margin.", "800"),
    ("spelunk", "洞窟探検する", "They spelunked deep into the cave.", "990"),
    ("schlep", "苦労して運ぶ(略式)", "I had to schlep the bags upstairs.", "990"),
]


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = filled = 0
        for en, ja, ex, level in ITEMS:
            if en.lower() in existing:
                conn.execute(
                    "UPDATE words SET example = ? WHERE "
                    "LOWER(english)=LOWER(?) AND COALESCE(example,'')=''",
                    (ex, en),
                )
                filled += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, "動詞", ex, "AI", level),
            )
            existing.add(en.lower())
            added += 1
    print(f"AI status words: +{added} (例文補充 {filled})")
    with db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        ai = conn.execute(
            "SELECT COUNT(*) FROM words WHERE domain='AI'").fetchone()[0]
    print(f"単語総数: {total} / domain=AI: {ai}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
