# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a brand-new domain/scene pair for PRESENTATION-GIVING and
TEACHING/EXPLAINING English, authored by Claude (2026-08-04・ユーザー要望:
「プレゼン ものを教えるときの フレーズや用語」).

DB確認の結果、プレゼン・人に教える/説明する場面の語彙・フレーズは既存DBに
一切なかった（該当する domain/scene が存在しない）。ビジネス英語で最も
頻出するニーズの一つであるため、新規に以下を追加する:

  - words:   domain='プレゼン・教える技術'
             プレゼンの構成・進行語彙（アジェンダ関連、スライド、Q&Aなど）
             + 教える/説明する技術の語彙（scaffolding, worked example など）
  - phrases: scene='プレゼンの英語'
             プレゼンの開始・展開・トラブル対応・聴衆エンゲージメント・
             まとめ・Q&A対応
  - phrases: scene='教える・説明する英語'
             理解確認・手順説明・具体例の提示・やんわり訂正・励まし・
             簡略化

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased), checked
against the live `words`/`phrases` tables before this script was written
(agenda, segue, handout, pacing, moderator, facilitator already existed as
bare words elsewhere, so they are intentionally omitted here).

Run:  python scripts/add_presentation_teaching.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- words: (english, japanese, part_of_speech, example, domain, level) -----

DOMAIN = "プレゼン・教える技術"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- プレゼンの構成・展開 ---
    ("opening remarks", "冒頭の挨拶・開会の言葉", "名詞", "She began with a few opening remarks to set the tone.", DOMAIN, "650"),
    ("key takeaway", "重要な学び・要点", "名詞", "The key takeaway from today's meeting is to prioritize customer feedback.", DOMAIN, "700"),
    ("talking point", "論点・話すべきポイント", "名詞", "Let's go over the main talking points before the call.", DOMAIN, "650"),
    ("rhetorical question", "修辞疑問(答えを求めない問いかけ)", "名詞", "He opened with a rhetorical question to get the audience thinking.", DOMAIN, "750"),
    ("call to action", "行動喚起・呼びかけ", "名詞", "End your presentation with a clear call to action.", DOMAIN, "700"),
    ("elevator pitch", "エレベーターピッチ(短時間の売り込み)", "名詞", "Can you give me your elevator pitch in under a minute?", DOMAIN, "750"),
    ("executive summary", "エグゼクティブサマリー(要約)", "名詞", "The executive summary is on the first page of the report.", DOMAIN, "750"),
    ("visual aid", "視覚資料", "名詞", "A simple chart works well as a visual aid.", DOMAIN, "650"),
    ("Q&A session", "質疑応答の時間", "名詞", "We'll open the floor for a Q&A session at the end.", DOMAIN, "600"),
    ("live demo", "ライブデモ・実演", "名詞", "The engineer ran a live demo of the new feature.", DOMAIN, "600"),
    ("dry run", "リハーサル・予行演習", "名詞", "Let's do a dry run before the actual presentation.", DOMAIN, "700"),
    ("speaker notes", "発表者用ノート", "名詞", "I keep my speaker notes on index cards, not the slides.", DOMAIN, "700"),
    ("cue card", "カンペ・キューカード", "名詞", "She glanced at her cue card to remember the next point.", DOMAIN, "750"),
    ("filler word", "つなぎ言葉(「あの」「えーと」など)", "名詞", "Try to cut down on filler words like 'um' and 'you know.'", DOMAIN, "750"),
    ("eye contact", "アイコンタクト", "名詞", "Maintaining eye contact with the audience builds trust.", DOMAIN, "600"),
    ("body language", "ボディランゲージ・身振り", "名詞", "Confident body language can make up for a shaky voice.", DOMAIN, "600"),
    ("audience engagement", "聴衆の巻き込み・関与", "名詞", "Polls are a great way to boost audience engagement.", DOMAIN, "750"),
    ("icebreaker", "アイスブレイク(場を和ませる導入)", "名詞", "We started the workshop with a quick icebreaker.", DOMAIN, "650"),
    ("wrap-up", "締めくくり・まとめ", "名詞", "Let's save the last five minutes for a wrap-up.", DOMAIN, "650"),
    ("recap", "要点の振り返り", "名詞", "Here's a quick recap of what we covered today.", DOMAIN, "600"),
    ("follow-up materials", "フォローアップ資料", "名詞", "I'll send follow-up materials after the session.", DOMAIN, "700"),
    ("presentation deck", "プレゼン資料一式", "名詞", "Could you share the presentation deck before the meeting?", DOMAIN, "650"),
    ("slide transition", "スライドの切り替え(演出)", "名詞", "Keep slide transitions simple so they don't distract the audience.", DOMAIN, "750"),
    ("bullet point", "箇条書きの項目", "名詞", "Try to keep each slide to three or four bullet points.", DOMAIN, "600"),
    ("whiteboard", "ホワイトボード", "名詞", "He sketched the workflow on the whiteboard.", DOMAIN, "500"),
    ("flip chart", "フリップチャート・模造紙", "名詞", "The trainer wrote key terms on a flip chart.", DOMAIN, "700"),
    ("laser pointer", "レーザーポインター", "名詞", "She used a laser pointer to highlight the chart.", DOMAIN, "650"),
    ("clicker", "プレゼン用リモコン", "名詞", "Don't forget to bring the clicker for changing slides.", DOMAIN, "650"),
    ("stage fright", "人前で話す緊張・あがり症", "名詞", "Even experienced speakers sometimes get stage fright.", DOMAIN, "700"),
    ("public speaking", "人前で話すこと", "名詞", "Public speaking gets easier with practice.", DOMAIN, "600"),
    ("keynote speech", "基調講演", "名詞", "The CEO delivered the keynote speech on the first day.", DOMAIN, "700"),
    ("panel discussion", "パネルディスカッション", "名詞", "The conference ended with a panel discussion among experts.", DOMAIN, "700"),
    ("breakout session", "分科会・小グループセッション", "名詞", "Each breakout session focused on a different topic.", DOMAIN, "750"),
    ("Q&A moderator", "質疑応答の進行役", "名詞", "The Q&A moderator selected questions from the chat.", DOMAIN, "750"),
    ("time check", "時間確認", "名詞", "Quick time check — we have about ten minutes left.", DOMAIN, "700"),
    ("running over time", "時間を超過している", "動詞句", "We're running over time, so let's speed up.", DOMAIN, "700"),
    ("technical difficulties", "技術的なトラブル", "名詞", "We're experiencing some technical difficulties with the projector.", DOMAIN, "650"),
    ("backup slide", "予備のスライド", "名詞", "I added a backup slide in case someone asks about pricing.", DOMAIN, "750"),
    # --- 教える・説明する技術 ---
    ("scaffolding", "足場かけ(段階的な支援指導法)", "名詞", "The teacher used scaffolding to help students tackle harder problems.", DOMAIN, "850"),
    ("comprehension check", "理解度確認", "名詞", "Do a quick comprehension check before moving to the next section.", DOMAIN, "800"),
    ("guided practice", "指導つき練習", "名詞", "After the demo, we moved into guided practice.", DOMAIN, "800"),
    ("worked example", "解き方を示した例題", "名詞", "Let's go through a worked example together.", DOMAIN, "750"),
    ("analogy", "たとえ・類推", "名詞", "She used a simple analogy to explain how APIs work.", DOMAIN, "700"),
    ("rule of thumb", "経験則・目安", "名詞", "As a rule of thumb, keep each slide under 20 words.", DOMAIN, "700"),
    ("common misconception", "よくある誤解", "名詞", "A common misconception is that more slides mean a better presentation.", DOMAIN, "800"),
    ("learning objective", "学習目標", "名詞", "Start the lesson by stating the learning objective.", DOMAIN, "800"),
    ("hands-on exercise", "実践的な演習", "名詞", "We'll finish with a hands-on exercise to practice what you learned.", DOMAIN, "700"),
    ("formative feedback", "形成的フィードバック(学習途中の助言)", "名詞", "Formative feedback throughout the course helps students improve early.", DOMAIN, "900"),
    ("constructive criticism", "建設的な批判・助言", "名詞", "Good mentors know how to give constructive criticism.", DOMAIN, "750"),
    ("learning curve", "習熟曲線・習得の難しさ", "名詞", "There's a bit of a learning curve, but it gets easier.", DOMAIN, "650"),
    ("rote memorization", "丸暗記", "名詞", "The new curriculum moves away from rote memorization.", DOMAIN, "850"),
    ("active recall", "アクティブリコール(能動的な想起学習)", "名詞", "Active recall is more effective than simply rereading notes.", DOMAIN, "850"),
    ("spaced repetition", "分散学習・間隔反復", "名詞", "Spaced repetition helps move new vocabulary into long-term memory.", DOMAIN, "850"),
    ("peer teaching", "生徒同士で教え合うこと", "名詞", "Peer teaching lets students explain concepts to each other.", DOMAIN, "800"),
    ("one-on-one tutoring", "個別指導", "名詞", "He gets one-on-one tutoring twice a week.", DOMAIN, "650"),
]


# --- phrases: scene -> [(english, japanese)] --------------------------------

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "プレゼンの英語": [
        # --- 開始 ---
        ("Thank you all for being here today.", "本日はお集まりいただきありがとうございます。"),
        ("Let's dive right in.", "早速本題に入りましょう。"),
        ("I'm excited to share what we've been working on.", "私たちが取り組んできたことをご紹介できて嬉しく思います。"),
        ("By the end of this talk, you'll have a clear picture of our plan.", "この発表が終わる頃には、私たちの計画が明確に見えているはずです。"),
        ("Let me start with a quick overview of the agenda.", "まずは簡単にアジェンダの概要からお話しします。"),
        # --- 展開・話題転換 ---
        ("Moving on to the next point...", "次のポイントに移ります…"),
        ("That brings me to my next slide.", "それでは次のスライドに移ります。"),
        ("Let's take a step back for a moment.", "ここで少し話を戻しましょう。"),
        ("With that said, let's look at the numbers.", "それを踏まえて、数字を見ていきましょう。"),
        ("Before I move on, let me quickly recap.", "先に進む前に、簡単に振り返っておきます。"),
        # --- 技術トラブル対応 ---
        ("Bear with me for a second, the slide isn't loading.", "少々お待ちください、スライドが読み込まれていません。"),
        ("Can everyone see the screen okay?", "皆さん、画面はきちんと見えていますか？"),
        ("Sorry about that — let's try that again.", "失礼しました、もう一度試してみます。"),
        ("I'll switch to the backup slides while this loads.", "これが読み込まれる間、バックアップのスライドに切り替えますね。"),
        # --- 聴衆エンゲージメント ---
        ("Feel free to stop me if you have questions.", "質問があればいつでも止めてください。"),
        ("Show of hands — how many of you have experienced this?", "挙手をお願いします — これを経験したことがある方はどのくらいいますか？"),
        ("I'd love to hear your thoughts on this.", "これについて皆さんのご意見を伺いたいです。"),
        ("Does anyone want to share their experience?", "ご自身の経験を共有してくださる方はいますか？"),
        ("Let's do a quick poll before we continue.", "続ける前に簡単な投票をしましょう。"),
        # --- まとめ ---
        ("To sum up what we've covered...", "これまでの内容をまとめますと…"),
        ("I'll leave you with this thought.", "最後にこの言葉を皆さんに贈ります。"),
        ("Happy to take any questions now.", "では、ご質問があればお受けします。"),
        ("Thank you for your time and attention.", "お時間とご清聴、ありがとうございました。"),
        ("That's everything I wanted to cover today.", "本日お伝えしたかった内容は以上です。"),
        # --- Q&A対応 ---
        ("That's a great question.", "それはいい質問ですね。"),
        ("I'm not sure I have the answer to that, but I'll follow up.", "その答えは今すぐには分かりませんが、後ほどフォローします。"),
        ("To answer your question directly...", "ご質問に直接お答えしますと…"),
        ("We're running a bit short on time, so let's take one more question.", "少し時間が押しているので、あと一つだけ質問を受け付けます。"),
        ("Let me rephrase the question to make sure I understand.", "理解を確実にするため、質問を言い換えさせてください。"),
    ],
    "教える・説明する英語": [
        # --- 理解確認 ---
        ("Does that make sense so far?", "ここまでで意味は通っていますか？"),
        ("Let me know if I'm going too fast.", "話すのが速すぎたら教えてください。"),
        ("Can you walk me through your understanding of this?", "これについてのあなたの理解を説明してもらえますか？"),
        ("Just checking — are we on the same page?", "念のため確認ですが、認識は合っていますか？"),
        # --- 手順の説明 ---
        ("First, you'll want to...", "まず、〜するとよいでしょう。"),
        ("Once you've done that, move on to...", "それが終わったら、次に〜に進んでください。"),
        ("The next step is to...", "次のステップは〜することです。"),
        ("Take it one step at a time.", "一度に一つずつ進めてください。"),
        # --- 具体例の提示 ---
        ("Let me give you a concrete example.", "具体的な例を挙げますね。"),
        ("Think of it this way...", "こう考えてみてください…"),
        ("Here's a real-world example of how this works.", "これがどう機能するかの実例を紹介します。"),
        ("Imagine you're trying to...", "〜しようとしていると想像してみてください。"),
        # --- やんわり訂正 ---
        ("That's close, but let's refine it a bit.", "惜しいですが、もう少し詰めていきましょう。"),
        ("Not quite — here's the thing to watch out for.", "少し違います — ここが注意すべき点です。"),
        ("Almost there — just one small adjustment.", "あと少しです — ちょっとした調整だけです。"),
        ("Let's take another look at this part.", "この部分をもう一度見てみましょう。"),
        # --- 励まし ---
        ("You're on the right track.", "その方向性で合っています。"),
        ("Good instinct, let's build on that.", "いい着眼点です、それを土台に進めましょう。"),
        ("You're getting the hang of it.", "だんだんコツをつかんできていますね。"),
        ("Don't worry, this takes practice.", "心配いりません、これは練習が必要なことです。"),
        # --- 簡略化 ---
        ("Let me break this down into smaller steps.", "これをもっと小さいステップに分解しますね。"),
        ("In simple terms, it means...", "簡単に言うと、これは〜という意味です。"),
        ("Here's the short version.", "手短に言うとこうです。"),
        ("Let's simplify this a bit.", "これを少し単純化してみましょう。"),
    ],
}


# --- insertion --------------------------------------------------------------


def main() -> int:
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
