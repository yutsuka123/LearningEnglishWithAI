# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated CONTRAST PAIRS for "直訳すると失礼に響く英語 → 実際に
使われる丁寧な言い方", authored by Claude.

Focus (フレーズ集の手薄な領域を補強): 日本語の直接的な命令文・要求表現を
そのまま英語に直訳すると、文法的には正しくても唐突・高圧的・失礼に聞こえて
しまうケースが非常に多い（日本語では失礼にならない直接表現が、英語では
そのまま失礼になる）。本スクリプトは、そうした「直訳しがちな失礼表現」と
「実際にネイティブが使う丁寧な言い方」を **ペア** で並べ、対比によって
学べるようにする。

対象カテゴリ（50ペア＝100フレーズに分散）:
  - 依頼・命令文（直接命令 → 婉曲的な依頼）
  - 欲求・必要（"I want / I need" の押しつけがましさ → 柔らかい言い方）
  - 拒否・反論（ぶっきらぼうな否定 → やわらげた否定）
  - 見下す/詰問調に響く質問 → 感じの良い聞き方
  - 義務・命令（"You must/have to" の高圧さ → 柔らかい促し）
  - 話しかける・割り込む（唐突な切り出し → クッション言葉付き）
  - 会話・面会を終える（素っ気ない切り上げ → 丁寧な締めくくり）

各ペアの日本語訳には、対比が一目でわかるよう〔注〕を付した:
  - 失礼に響く方: 〔注: 直訳すると自然だが英語では...に響く〕
  - 丁寧な方:     〔注: 実際に使われる自然で丁寧な言い方〕

姉妹スクリプト scripts/add_polite_requests.py は「依頼・許可・もてなし・
仮定法・婉曲表現」を丁寧度の階調で単独フレーズとして扱っている。本スクリプト
はそれとは構造が異なり、「失礼に響く表現」とその「丁寧な言い換え」を明示的な
ペアとして並べる点が特徴（教材としての対比構造そのものが価値）。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_polite_vs_rude_pairs1.py
      python scripts/add_polite_vs_rude_pairs1.py --missing-words   # report only

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- phrases: scene -> [(english, japanese)] --------------------------------
# 各ペアは「失礼に響く表現」の直後に「丁寧な言い方」を並べている。

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "直訳で失礼に響く表現→丁寧な言い方(1)": [
        # --- 依頼・命令文（直接命令 → 婉曲的な依頼） ---
        ("Give me the menu.", "お品書きをください。〔注: 直訳すると自然だが英語では命令口調で唐突・失礼に響く〕"),
        ("Could I have the menu, please?", "メニューをいただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Tell me your name.", "あなたの名前を教えて。〔注: 直訳すると自然だが英語では詰問調で失礼に響く〕"),
        ("Could I get your name, please?", "お名前を伺ってもよろしいですか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Wait.", "待って。〔注: 直訳すると自然だが英語では素っ気なく命令的に響く〕"),
        ("Just a moment, please.", "少々お待ちください。〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Come here.", "こっちに来て。〔注: 直訳すると自然だが英語では上から目線・命令的に響く〕"),
        ("Could you come over here for a moment?", "少しこちらに来ていただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Explain it again.", "もう一度説明して。〔注: 直訳すると自然だが英語では命令的に響く〕"),
        ("Could you go over that again, please?", "もう一度説明していただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Send me the file.", "ファイルを送って。〔注: 直訳すると自然だが英語では一方的な命令に響く〕"),
        ("Would you mind sending me the file?", "ファイルを送っていただけませんか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Open the door.", "ドアを開けて。〔注: 直訳すると自然だが英語では命令的に響く〕"),
        ("Could you open the door for me, please?", "ドアを開けていただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Give me a pen.", "ペンをちょうだい。〔注: 直訳すると自然だが英語ではぶっきらぼうに響く〕"),
        ("Could I borrow a pen, please?", "ペンをお借りできますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Repeat that.", "それをもう一回言って。〔注: 直訳すると自然だが英語では命令的に響く〕"),
        ("Could you say that again, please?", "もう一度おっしゃっていただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Turn down the music.", "音楽の音量を下げて。〔注: 直訳すると自然だが英語では高圧的に響く〕"),
        ("Would you mind turning the music down a bit?", "音楽の音を少し下げていただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Move your car.", "車をどけて。〔注: 直訳すると自然だが英語では命令的・失礼に響く〕"),
        ("Would you be able to move your car, please?", "お車を移動していただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Check this for me.", "これチェックして。〔注: 直訳すると自然だが英語では雑な命令に響く〕"),
        ("Could you take a look at this for me, please?", "これを確認していただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Sign here.", "ここにサインして。〔注: 直訳すると自然だが英語では事務的で冷たく響く〕"),
        ("Could you sign here, please?", "こちらにご署名いただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Print this out.", "これ印刷して。〔注: 直訳すると自然だが英語では命令的に響く〕"),
        ("Would you mind printing this out for me?", "これを印刷していただけませんか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        # --- 欲求・必要（"I want / I need" の押しつけがましさ → 柔らかい言い方） ---
        ("I want coffee.", "コーヒーが欲しい。〔注: 直訳すると自然だが英語では欲求がむき出しで幼稚・唐突に響く〕"),
        ("I'd like a coffee, please.", "コーヒーをお願いします。〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("I want to know the price.", "値段が知りたい。〔注: 直訳すると自然だが英語では詰問するように響く〕"),
        ("Could you tell me the price?", "お値段を教えていただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("I need this now.", "これが今すぐ必要。〔注: 直訳すると自然だが英語では高圧的・せかすように響く〕"),
        ("Would it be possible to get this soon?", "これをなるべく早くいただくことは可能でしょうか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("I want a table for two.", "二人用のテーブルが欲しい。〔注: 直訳すると自然だが英語では要求口調に響く〕"),
        ("Could we get a table for two, please?", "二人用の席をお願いできますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("I want a refund.", "返金してほしい。〔注: 直訳すると自然だが英語では強い要求口調に響く〕"),
        ("I'd like to request a refund, please.", "返金をお願いしたいのですが。〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("I want you to fix this.", "これを直してほしい。〔注: 直訳すると自然だが英語では命令的に響く〕"),
        ("Would you be able to fix this for me?", "これを直していただくことはできますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("I need more time.", "もっと時間が必要。〔注: 直訳すると自然だが英語では一方的な要求に響く〕"),
        ("Would it be possible to get a bit more time?", "もう少しお時間をいただくことは可能でしょうか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("I need to speak to the manager.", "責任者と話す必要がある。〔注: 直訳すると自然だが英語では威圧的なクレーム口調に響く〕"),
        ("Would it be possible to speak with the manager?", "責任者の方とお話しすることは可能でしょうか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        # --- 拒否・反論（ぶっきらぼうな否定 → やわらげた否定） ---
        ("No.", "いや。〔注: 直訳すると自然だが英語では素っ気なく突き放すように響く〕"),
        ("I'm afraid that won't be possible.", "申し訳ございませんが、それは難しいです。〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("I don't like it.", "それは好きじゃない。〔注: 直訳すると自然だが英語では素っ気なく子供っぽく響く〕"),
        ("It's not really my thing.", "あまり好みではないんです。〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("You're wrong.", "あなたは間違っている。〔注: 直訳すると自然だが英語では対立的・喧嘩腰に響く〕"),
        ("I don't think that's quite right.", "それは少し違うように思います。〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("That's a bad idea.", "それは悪い考えだ。〔注: 直訳すると自然だが英語では突き放すように響く〕"),
        ("I'm not sure that would work.", "それはうまくいかないかもしれません。〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("I can't do that.", "それはできない。〔注: 直訳すると自然だが英語では冷たく拒絶するように響く〕"),
        ("I'm afraid I won't be able to do that.", "申し訳ありませんが、それは難しいです。〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("I disagree.", "反対です。〔注: 直訳すると自然だが英語では対立的に響く〕"),
        ("I see it a bit differently.", "私は少し違う見方をしています。〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("That's not true.", "それは違う。〔注: 直訳すると自然だが英語では相手を強く否定するように響く〕"),
        ("I'm not sure that's accurate.", "それは正確ではないかもしれません。〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Stop it.", "やめて。〔注: 直訳すると自然だが英語では強い命令・叱責に響く〕"),
        ("Would you mind stopping that, please?", "それをやめていただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        # --- 見下す/詰問調に響く質問 → 感じの良い聞き方 ---
        ("Do you understand?", "わかった？〔注: 直訳すると自然だが英語では見下すように響く〕"),
        ("Does everything make sense so far?", "ここまでで分かりにくい点はありますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Why did you do that?", "なんでそんなことしたの？〔注: 直訳すると自然だが英語では詰問調・非難するように響く〕"),
        ("Could you help me understand why you did that?", "なぜそうされたのか、教えていただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("What do you want?", "何が欲しいの？〔注: 接客場面で直訳すると自然だが英語では突き放すように響く〕"),
        ("How can I help you?", "どういったご用件でしょうか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("What's your problem?", "何が問題なの？〔注: 直訳すると自然だが英語では喧嘩腰に響く〕"),
        ("Is everything all right?", "何か問題がありましたか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Why are you late?", "なんで遅れたの？〔注: 直訳すると自然だが英語では責めるように響く〕"),
        ("Is everything okay? You're a bit later than usual.", "大丈夫ですか？いつもより少し遅いですね。〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Why didn't you tell me?", "なんで言わなかったの？〔注: 直訳すると自然だが英語では非難するように響く〕"),
        ("I wish you'd let me know sooner.", "もっと早く教えてもらえたらよかったです。〔注: 実際に使われる自然で丁寧な言い方〕"),
        # --- 義務・命令（"You must/have to" の高圧さ → 柔らかい促し） ---
        ("You must finish this today.", "今日中にこれを終わらせなければならない。〔注: 直訳すると自然だが英語では高圧的な命令に響く〕"),
        ("Could you try to finish this today?", "今日中に終わらせていただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("You have to fix this.", "これを直さなければならない。〔注: 直訳すると自然だが英語では強制的に響く〕"),
        ("It would be great if this could be fixed.", "これを直していただけると助かります。〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("You need to be here by nine.", "9時までにここに来る必要がある。〔注: 直訳すると自然だが英語では命令的に響く〕"),
        ("Could you be here by nine, please?", "9時までにお越しいただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("You should apologize.", "謝るべきだ。〔注: 直訳すると自然だが英語では説教くさく上から目線に響く〕"),
        ("It might be a good idea to apologize.", "謝っておくのがいいかもしれません。〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Do it again.", "もう一回やって。〔注: 直訳すると自然だが英語では命令的に響く〕"),
        ("Would you mind doing it one more time?", "もう一度やっていただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Finish it by Friday.", "金曜までに終わらせて。〔注: 直訳すると自然だが英語では一方的な命令に響く〕"),
        ("Would it be possible to finish it by Friday?", "金曜までに終わらせていただくことは可能でしょうか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        # --- 話しかける・割り込む（唐突な切り出し → クッション言葉付き） ---
        ("Listen.", "聞いて。〔注: 直訳すると自然だが英語では高圧的・命令的に響く〕"),
        ("Could I have your attention for a moment?", "少しお時間よろしいですか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Hey, question.", "ねえ、質問。〔注: 直訳すると自然だが英語では唐突でぶっきらぼうに響く〕"),
        ("Sorry to interrupt, but could I ask something?", "お話し中すみません、少し伺ってもよろしいですか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("Look at this.", "これ見て。〔注: 直訳すると自然だが英語では命令的に響く〕"),
        ("Could you take a look at this, please?", "これを見ていただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("I have a question.", "質問がある。〔注: 直訳すると自然だが会議中などでは唐突に割り込むように響くことがある〕"),
        ("Sorry, may I ask a quick question?", "すみません、少しお伺いしてもよろしいですか？〔注: 実際に使われる自然で丁寧な言い方〕"),
        # --- 会話・面会を終える（素っ気ない切り上げ → 丁寧な締めくくり） ---
        ("I'm leaving now.", "もう帰るね。〔注: 直訳すると自然だが英語では素っ気なく唐突に響く〕"),
        ("I should get going, but thank you so much.", "そろそろ失礼しますが、本当にありがとうございました。〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("I'm done.", "終わった。〔注: 直訳すると自然だが英語では素っ気なく投げやりに響く〕"),
        ("I think that covers everything on my end.", "こちらからは以上になります。〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("I have to go.", "もう行かなきゃ。〔注: 直訳すると自然だが英語では会話を打ち切るように素っ気なく響くことがある〕"),
        ("I'm afraid I need to head out, but it was great talking with you.", "申し訳ないのですが、そろそろ失礼します。お話しできてよかったです。〔注: 実際に使われる自然で丁寧な言い方〕"),
        ("We're done here.", "ここで終わり。〔注: 直訳すると自然だが英語では話を打ち切るように素っ気なく響く〕"),
        ("I think we've covered everything — thank you for your time.", "以上ですべて確認できたかと思います。お時間をいただきありがとうございました。〔注: 実際に使われる自然で丁寧な言い方〕"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----
# このバッチは対比ペア（フレーズ）に焦点を当てており、追加の単語は不要。

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
