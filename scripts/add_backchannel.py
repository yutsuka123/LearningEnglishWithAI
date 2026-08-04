# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for BACKCHANNELING / CONVERSATIONAL CONNECTORS,
authored by Claude.

Focus (フレーズ集の手薄な領域を補強): 相槌・つなぎ言葉。単なる「はい/いいえ」
ではなく、強い賛同と弱い/しぶしぶの賛同の区別、驚き・意外性の表現、話題転換、
考え中のつなぎ言葉、やんわりした反論の切り出し方、話をまとめて終える表現など、
日常会話・ビジネス会話どちらにも効く「地の英語力」を体系的に強化する。

丁寧度やニュアンスの強さの段階が分かるよう、日本語訳に〔注〕を付した。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_backchannel.py
      python scripts/add_backchannel.py --missing-words   # report only

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- phrases: scene -> [(english, japanese)] --------------------------------

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "相槌・つなぎ言葉": [
        # --- 基本の相槌（中立） ---
        ("I see.", "なるほど。〔中立的な相槌〕"),
        ("Right.", "そうですね。〔軽い相槌〕"),
        ("Got it.", "わかりました。〔理解を示す相槌〕"),
        ("Makes sense.", "なるほど、筋が通ってますね。"),
        ("Fair enough.", "それはもっともですね。〔一定の納得〕"),
        ("Uh-huh.", "うんうん。〔聞いている合図・くだけた〕"),
        ("Okay, go on.", "はい、続けてください。"),
        ("Interesting.", "それは興味深いですね。"),
        # --- 強い賛同 ---
        ("I couldn't agree more.", "まったく同感です。〔最も強い賛同〕"),
        ("Absolutely.", "まさにその通り。〔強い賛同〕"),
        ("Exactly.", "まさにそれです。〔強い賛同・要点を突いた同意〕"),
        ("You're absolutely right.", "まったくおっしゃる通りです。"),
        ("That's exactly what I was thinking.", "私もまさにそう思っていました。"),
        ("No question about it.", "疑いの余地はありません。〔強い断定的賛同〕"),
        ("You took the words right out of my mouth.", "まさに言おうとしていたことです。"),
        # --- 弱い・しぶしぶの賛同 ---
        ("I guess so.", "まあ、そうかもしれません。〔弱い・しぶしぶの賛同〕"),
        ("If you say so.", "そう言うなら（そうなんでしょうね）。〔納得しきっていないニュアンス〕"),
        ("I suppose you're right.", "まあ、あなたが正しいのでしょう。〔渋々の同意〕"),
        ("Sort of.", "まあ、ある意味では。〔部分的な同意〕"),
        ("I guess that's one way to look at it.", "まあ、そういう見方もありますね。〔完全同意ではない〕"),
        ("It's not that I disagree, but...", "反対というわけではないのですが…〔やんわりした留保〕"),
        ("I could be wrong, but I'm not fully convinced.", "私が間違っているかもしれませんが、完全には納得していません。"),
        # --- やんわりした反論の切り出し ---
        ("I see your point, but...", "おっしゃることはわかりますが…〔反論の前置き〕"),
        ("That's true, however...", "それは事実ですが、しかし…"),
        ("With all due respect, I have to disagree.", "失礼ながら、私は異論があります。〔かなり丁寧な反論〕"),
        ("I'm not sure that's entirely accurate.", "それが完全に正確かどうかはわかりかねます。〔遠回しな否定〕"),
        ("That's one perspective, but there's another way to see it.", "それも一つの見方ですが、別の見方もあります。"),
        ("Correct me if I'm wrong, but...", "間違っていたら訂正してください、ただ…〔控えめな異論〕"),
        ("I'd push back on that a little.", "そこは少し異論を挟みたいです。"),
        # --- 驚き・意外性 ---
        ("Really?", "本当に？"),
        ("No way!", "うそでしょ！〔強い驚き・くだけた〕"),
        ("You're kidding!", "冗談でしょう！"),
        ("Seriously?", "マジで？〔くだけた驚き〕"),
        ("That's surprising.", "それは意外ですね。"),
        ("I wouldn't have guessed that.", "それは予想していませんでした。"),
        ("Wow, I had no idea.", "わあ、全然知りませんでした。"),
        # --- 話題転換・つなぎ ---
        ("Anyway,", "とにかく、〔話を戻す・切り上げる〕"),
        ("By the way,", "ところで、〔話題を変える〕"),
        ("Speaking of which,", "それと言えば、〔関連する話題へ〕"),
        ("That reminds me,", "それで思い出したのですが、"),
        ("On a different note,", "話は変わりますが、〔ビジネスでも使える〕"),
        ("Getting back to what you said earlier,", "先ほどおっしゃっていた話に戻りますが、"),
        ("Before I forget,", "忘れないうちに、"),
        # --- 考え中のつなぎ言葉 ---
        ("Let me think.", "ちょっと考えさせてください。"),
        ("Well...", "そうですね…〔考えながら話し始める〕"),
        ("How should I put it...", "何と言えばいいか…〔言葉を選んでいる〕"),
        ("Let me see.", "ええと…〔思案する間〕"),
        ("That's a good question.", "いい質問ですね。〔答えを考える時間稼ぎにも使う〕"),
        ("Give me a second to think about that.", "少し考える時間をください。"),
        ("I'm not sure off the top of my head.", "今すぐには思いつきません。"),
        # --- 話をまとめる・終える ---
        ("Anyway, that's about it.", "とにかく、そんなところです。"),
        ("So, to sum up,", "それで、まとめると、"),
        ("Long story short,", "手短に言うと、"),
        ("That's the gist of it.", "それが要点です。"),
        ("I think that covers it.", "それで大体網羅できたと思います。"),
        ("Let's leave it there.", "この辺にしておきましょう。〔話を切り上げる〕"),
        ("We can pick this up later.", "続きはまた今度にしましょう。"),
        # --- 相手の話を促す・確認する ---
        ("Go on.", "続けてください。"),
        ("What do you mean by that?", "それはどういう意味ですか？"),
        ("Could you elaborate on that?", "もう少し詳しく話していただけますか？"),
        ("Just to make sure I understand,", "理解を確認したいのですが、"),
        ("So what you're saying is...", "つまり、おっしゃりたいのは…"),
        ("Are you following me?", "話についてきていますか？"),
        ("Does that make sense?", "ここまでで分かりますか？"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("acknowledge", "認める・（発言を）受け止める", "動詞", "Let me acknowledge your point first.", "口語", "600"),
    ("concede", "しぶしぶ認める", "動詞", "I have to concede you have a point.", "口語", "700"),
    ("reluctant", "気が進まない・渋々の", "形容詞", "She gave a reluctant nod.", "口語", "700"),
    ("digress", "話がそれる", "動詞", "Sorry, I'm digressing.", "口語", "800"),
    ("tangent", "本題からそれた話", "名詞", "Let's not go off on a tangent.", "口語", "700"),
    ("segue", "自然に話題を変える", "動詞", "Let me segue into the next topic.", "ビジネス", "800"),
    ("gist", "要点・要旨", "名詞", "That's the gist of the report.", "ビジネス", "700"),
    ("elaborate", "詳しく述べる", "動詞", "Could you elaborate on that point?", "ビジネス", "700"),
    ("skeptical", "懐疑的な", "形容詞", "I'm a bit skeptical about that claim.", "口語", "700"),
    ("convinced", "納得した・確信した", "形容詞", "I'm not fully convinced yet.", "口語", "600"),
    ("nod", "うなずく", "動詞", "He nodded in agreement.", "口語", "500"),
    ("hesitant", "ためらいがちな", "形容詞", "She sounded hesitant to agree.", "口語", "600"),
    ("wholeheartedly", "心から・全面的に", "副詞", "I wholeheartedly agree.", "口語", "800"),
    ("reservation", "留保・懸念", "名詞", "I have some reservations about the plan.", "ビジネス", "700"),
    ("perspective", "視点・見方", "名詞", "That's an interesting perspective.", "ビジネス", "600"),
]


# --- insertion --------------------------------------------------------------

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")
_STOP = {
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on", "at",
    "for", "with", "from", "by", "as", "is", "are", "was", "were", "be", "been",
    "do", "does", "did", "have", "has", "had", "will", "would", "can", "could",
    "should", "may", "might", "must", "i", "you", "he", "she", "it", "we",
    "they", "me", "him", "her", "us", "them", "my", "your", "his", "its", "our",
    "their", "this", "that", "these", "those", "here", "there", "what", "when",
    "where", "who", "how", "why", "not", "no", "yes", "so", "up", "out", "off",
    "down", "let", "lets", "please", "thanks", "thank", "ok", "okay", "im",
    "ill", "id", "ive", "dont", "cant", "wont", "isnt", "thats", "whats",
    "very", "just", "too", "more", "some", "any", "all", "one", "two", "get",
    "got", "go", "going", "like", "want", "need", "make", "made", "take",
    "see", "now", "today", "tonight", "good", "well", "back", "about", "over",
    "into", "than", "then", "again", "really", "much", "many", "wish", "mind",
    "could", "would", "shall", "rather", "ever", "way", "one's", "off",
    "before", "later", "earlier", "second", "gist", "point", "way", "say",
    "saying", "sure", "understand", "following", "pick", "leave", "there",
}


def _content_words(phrases: list[tuple[str, str]]) -> set[str]:
    out: set[str] = set()
    for en, _ in phrases:
        for tok in _WORD_RE.findall(en.lower()):
            w = tok.strip("'-")
            if len(w) >= 4 and w not in _STOP:
                out.add(w)
    return out


def report_missing() -> None:
    """Print content words used in the new phrases that are not yet in `words`
    and not covered by the WORDS list above (authoring aid)."""
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
    covered = {w[0].lower() for w in WORDS}
    all_phrases = [p for lst in PHRASES_BY_SCENE.values() for p in lst]
    missing = sorted(
        w for w in _content_words(all_phrases)
        if w not in existing and w not in covered
    )
    print(f"missing content words ({len(missing)}):")
    print(", ".join(missing))


def main() -> int:
    if "--missing-words" in sys.argv:
        report_missing()
        return 0

    with db() as conn:
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }

        ph_added = ph_skipped = 0
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in ph_existing:
                    ph_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                ph_existing.add(en.lower())
                ph_added += 1

        w_added = w_skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in w_existing:
                w_skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            w_existing.add(en.lower())
            w_added += 1

    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    print(f"words:   +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print("totals -> phrases:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0],
              "words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
