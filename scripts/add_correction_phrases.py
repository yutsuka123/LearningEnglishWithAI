# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for CORRECTING / CAUTIONING SOMEONE'S BEHAVIOR
(注意・叱り方), authored by Claude on 2026-08-04 per user request. Zero API
cost — everything below is hand-written.

姉妹スクリプト scripts/add_compliments.py（褒め方集）と対をなす。相手との
関係性・上下関係によって、注意・指摘の言い方は大きく変わる。本スクリプトは
そのニュアンスの違いを、以下の3つの場面に分けて扱う:

  1. 職場で注意する英語（部下・後輩・同僚）
     - 部下（直属の報告者）: 毅然としつつも敬意を保った言い方
     - 後輩（kohai）: 支援的・育成的な言い方
     - 同僚（ピア）: 対立を避けつつ率直に伝える言い方
  2. 子供を注意する英語
     - 危険・望ましくない行動の制止／境界線の設定／結果の説明／
       言い換え（リダイレクト）／落ち着いてやり抜く、の5段階
  3. ペットを注意する英語
     - 噛む・飛びつく・吠える・家具に乗る・おねだり等、日常的な問題行動への
       シンプルで実用的な声かけ

(注: 褒め方集とは異なり、目上の人・年配の方・他人のペットを「注意する」の
は社会的に極めて不自然なため、本スクリプトはそれらの関係性を含めていない。
これは抜け漏れではなく意図的な設計。)

TONE — 最重要の制約: すべて建設的・プロフェッショナルなトーンに統一し、
人格否定・威圧・皮肉・虐待的な響きは徹底的に排除している。職場向けは
管理職研修で教えられるような、冷静かつ公平な言い方をモデルにした。子供
向けは現代の子育て指導で使われる、脅しや怒鳴り口調を含まない年齢相応の
言い方をモデルにした。ペット向けはシンプルで日常的な声かけに徹し、人に
向けたら虐待的に聞こえるような表現は一切含めていない。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased). Verified
zero overlap (case-insensitive, punctuation-insensitive) against the live
`phrases` table (4305 rows as of authoring) before finalizing this file.

Run:  python scripts/add_correction_phrases.py
      python scripts/add_correction_phrases.py --missing-words   # report only

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
    "職場で注意する英語(部下・後輩・同僚)": [
        # --- 部下を注意する（毅然としつつ敬意を保つ） ---
        ("This needs to be redone before the deadline.", "これは締め切り前にやり直す必要があります。"),
        ("I need you to double-check your work more carefully from now on.", "今後はもっと注意深く自分の仕事を確認してください。"),
        ("This isn't up to the standard we discussed.", "これは私たちが話し合った基準に達していません。"),
        ("I expected more attention to detail on this.", "この件はもっと細部への注意を期待していました。"),
        ("This can't go out the way it is right now.", "このままの状態では出せません。"),
        ("I need this fixed before we send it to the client.", "クライアントに送る前にこれを修正してほしいです。"),
        ("Let's make sure this doesn't happen again.", "これが二度と起きないようにしましょう。"),
        ("I need you to follow the process we agreed on.", "私たちが合意した手順に従ってほしいです。"),
        ("This is the second time this has come up — let's address it now.", "これで二回目です。今のうちに対処しましょう。"),
        ("I'm holding you to a higher standard on this.", "この件については、より高い基準を求めています。"),
        ("I need you to take this more seriously going forward.", "今後はこの件をもっと真剣に受け止めてほしいです。"),
        ("This isn't the standard I expect — let's talk about what happened.", "これは私が期待している水準ではありません。何があったか話しましょう。"),
        ("Going forward, I need this checked before it's submitted.", "今後は提出前に必ず確認してください。"),
        ("I need you to own this mistake and fix it.", "このミスをきちんと自分の責任として受け止め、修正してほしいです。"),
        # --- 後輩を注意する（支援的に） ---
        ("Let's go over what went wrong here so it doesn't happen again.", "何が問題だったか一緒に確認して、次に活かしましょう。"),
        ("You'll want to be more careful with this next time.", "次回はもう少し注意した方がいいですね。"),
        ("This is a good learning moment — let's break down what happened.", "いい学びの機会です。何が起きたか整理してみましょう。"),
        ("Next time, run this by me before sending it out.", "次回は送る前に一度私に確認してください。"),
        ("I think this needs another pass before it's ready.", "これはもう一度見直しが必要だと思います。"),
        ("Let's walk through this together so it's clearer next time.", "一緒に見ていって、次はもっと分かりやすくしましょう。"),
        ("This wasn't quite right, but I can see what you were going for.", "少し違いましたが、意図していたことは分かります。"),
        ("A quick tip for next time: double-check the numbers before submitting.", "次回のためのちょっとしたコツですが、提出前に数字を再確認してください。"),
        ("You're close, but this part needs some work.", "惜しいですが、この部分はまだ改善が必要です。"),
        ("Let's fix this together so you know what to look for next time.", "一緒に直して、次に何を見ればいいか分かるようにしましょう。"),
        ("I want to flag this now so it doesn't become a habit.", "習慣にならないように、今のうちに指摘しておきたいです。"),
        # --- 同僚に問題を伝える（気配りしつつ率直に） ---
        ("I need to raise something about how that was handled.", "あの件の対応について、少し話したいことがあります。"),
        ("Can we talk about what happened in that meeting?", "あの会議で何があったか話せますか？"),
        ("I don't think that was the right call, and I want to understand your thinking.", "それが正しい判断だったとは思えなくて、あなたの考えを聞きたいです。"),
        ("I wanted to flag something before it becomes a bigger issue.", "大きな問題になる前に、指摘しておきたいことがあります。"),
        ("Can I share some feedback on how that went?", "あの件について、フィードバックを伝えてもいいですか？"),
        ("I think we need to align on how we handle this going forward.", "今後どう対応するか、認識をすり合わせる必要があると思います。"),
        ("I noticed something in the report and wanted to check in with you about it.", "レポートで気になる点があって、確認したかったんです。"),
        ("I don't think we're on the same page about this — can we sync up?", "この件、認識がずれている気がします。すり合わせできますか？"),
        ("I want to be upfront that I had some concerns about that decision.", "正直に言うと、あの決定について懸念がありました。"),
        ("Can we revisit how that was communicated to the team?", "あれがチームにどう伝えられたか、見直せますか？"),
    ],
    "子供を注意する英語": [
        # --- 危険・望ましくない行動を止める ---
        ("Stop that right now.", "今すぐやめて。"),
        ("That's dangerous, don't do that.", "それは危ないから、やめてね。"),
        ("Get down from there, please.", "そこから降りてね。"),
        ("Freeze — don't move.", "止まって、動かないで。"),
        ("Not so close to the stove.", "コンロにそんなに近づかないで。"),
        ("Put that down, it's not safe.", "それを置いて、危ないから。"),
        # --- 境界線を伝える ---
        ("We don't hit.", "叩くのはだめだよ。"),
        ("No means no.", "だめと言ったらだめなの。"),
        ("That's not okay, and here's why.", "それはよくないよ、理由を説明するね。"),
        ("We use gentle hands.", "手はやさしく使おうね。"),
        ("It's not okay to speak to me that way.", "そんな話し方はよくないよ。"),
        ("We don't throw things in the house.", "家の中でものを投げるのはだめだよ。"),
        # --- 結果・帰結を説明する ---
        ("If you keep doing that, you'll lose screen time.", "それを続けたら、画面を見る時間はなしだよ。"),
        ("You need to clean this up before you go play.", "遊びに行く前に、これを片付けてね。"),
        ("If you can't share nicely, the toy goes away for now.", "仲良く貸し借りできないなら、そのおもちゃはしばらくお預けだよ。"),
        ("Keep doing that, and we'll have to leave.", "それを続けるなら、帰らないといけなくなるよ。"),
        ("You need to apologize before we move on.", "次に進む前に、謝ってね。"),
        ("If this keeps happening, there will be no dessert tonight.", "これが続くなら、今夜のデザートはなしだよ。"),
        # --- 言い換え・リダイレクト ---
        ("Let's use our words instead.", "言葉で伝えようね。"),
        ("Can you show me a better way to ask for that?", "もっといい聞き方を教えてくれる？"),
        ("Let's take a deep breath together.", "一緒に深呼吸しようね。"),
        ("Why don't we try that a different way?", "違うやり方で試してみようか。"),
        ("Let's find something safer to climb on.", "もっと安全に登れる場所を探そうね。"),
        ("How about we use this instead?", "代わりにこれを使ってみようか。"),
        # --- 落ち着いてやり抜く ---
        ("I already told you once. This is your last warning.", "もう一回言ったよね。これが最後の注意だよ。"),
        ("Time-out, let's take a break.", "タイムアウト、ちょっと休憩しようね。"),
        ("I meant what I said — let's go.", "さっき言ったこと、本気だからね。行くよ。"),
        ("I need you to listen the first time I ask.", "最初に言った時に聞いてほしいな。"),
        ("We talked about this already, remember?", "これはもう話したよね、覚えてる？"),
        ("I'm going to count to three, and then we need to stop.", "3つ数えるから、それでやめようね。"),
    ],
    "ペットを注意する英語": [
        ("No! Drop it.", "だめ！離しなさい。"),
        ("Off the couch.", "ソファから降りて。"),
        ("Leave it.", "そのままにして（触らないで）。"),
        ("Quiet!", "静かに！"),
        ("Bad dog, don't do that.", "だめでしょ、それはしないで。"),
        ("Down!", "伏せ！"),
        ("Stop that barking.", "吠えるのをやめて。"),
        ("Don't jump on the guests.", "お客さんに飛びつかないで。"),
        ("No begging at the table.", "食卓でおねだりしないの。"),
        ("Out of the trash!", "ゴミ箱から出て！"),
        ("Sit and stay.", "お座りして、そのまま待って。"),
        ("No chewing on the shoes.", "靴を噛まないで。"),
        ("Gentle! No biting.", "優しくね！噛んじゃだめ。"),
        ("Get off the bed.", "ベッドから降りて。"),
        ("No jumping on the counter.", "カウンターに飛び乗らないで。"),
        ("Settle down.", "落ち着いて。"),
        ("No barking at the mailman.", "郵便屋さんに吠えないの。"),
        ("Leave the cat alone.", "猫にちょっかい出さないで。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----
# このバッチは注意・叱り方フレーズに焦点を当てており、追加の単語は不要。

WORDS: list[tuple[str, str, str, str, str, str]] = []


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
    "before", "later", "earlier", "second", "sooner", "soon", "quick",
    "possible", "everything", "something", "someone", "anything", "everyone",
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
