# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for CONTRAST PAIRS: 直訳すると失礼に響く英語 vs
実際に使われる自然で丁寧な言い方, authored by Claude.

Focus (ユーザー要望): 日本語の直接的な言い回しをそのまま英訳すると、文法的には
正しくても英語では唐突・ぶしつけ・失礼に響いてしまう文と、実際にネイティブが
使う自然で丁寧な言い換えを、ペアで並べて対比させる。単なる丁寧度のグラデー
ションではなく「直訳の落とし穴」に焦点を当てる点が、既存の依頼・お願い／
許可を求める／婉曲・クッション言葉／申し出・もてなし（scripts/add_polite_requests.py）
とは異なる。

カバー範囲: 職場・メール表現、接客・カスタマーサービス（客側・店員側の両方）、
雑談・誘いを断る場面、道案内・指示出し、悪い知らせを和らげる／謝罪。
一般的な依頼・断り・義務・話に割り込む表現は姉妹スクリプトの担当領域のため
本スクリプトでは扱わない。

各ペアは「直訳すると自然だが失礼に響く」文の直後に「実際に使われる丁寧な
言い方」を並べ、日本語訳に〔注〕でその対比を明示した。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_polite_vs_rude_pairs2.py
      python scripts/add_polite_vs_rude_pairs2.py --missing-words   # report only

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
    "直訳で失礼に響く表現→丁寧な言い方(2)": [
        # ============================================================
        # 職場・メール表現
        # ============================================================
        ("Reply to me by tomorrow.", "明日までに返信してください。〔注: 直訳すると自然だが、メールでは命令口調で唐突・失礼に響く〕"),
        ("It would be great if you could reply by tomorrow.", "明日までにご返信いただけると助かります。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Fix this mistake.", "このミスを直してください。〔注: 直訳すると自然だが、指摘として唐突・命令口調に響く〕"),
        ("Could you take a look at this when you get a chance?", "お手すきの際にこちらをご確認いただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("This is wrong.", "これは間違っています。〔注: 直訳すると自然だが、フィードバックの場では断定的で失礼に響く〕"),
        ("I think there might be a small issue here.", "ここに小さな問題があるかもしれません。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Call me back.", "折り返し電話してください。〔注: 直訳すると自然だが、命令口調で唐突に響く〕"),
        ("Could you give me a call back when you have a moment?", "お時間のあるときに折り返しお電話いただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("I disagree.", "私は反対です。〔注: 直訳すると自然だが、会議で唐突・断定的に響く〕"),
        ("I see it a little differently, if I may.", "もしよろしければ、私は少し違う見方をしています。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("You didn't do what I asked.", "頼んだことをやっていませんね。〔注: 直訳すると自然だが、相手を責めるように失礼に響く〕"),
        ("I think there might have been a mix-up — could we go over this again?", "何か行き違いがあったかもしれません。もう一度確認できますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Send me the file.", "ファイルを送ってください。〔注: 直訳すると自然だが、メールでは素っ気なく命令口調に響く〕"),
        ("Would you mind sending me the file when you get a chance?", "お手すきの際にファイルを送っていただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("You need to redo this.", "これはやり直す必要があります。〔注: 直訳すると自然だが、断定的で高圧的に響く〕"),
        ("Would you mind taking another pass at this?", "もう一度手を加えていただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Answer my email.", "私のメールに返事してください。〔注: 直訳すると自然だが、催促として失礼に響く〕"),
        ("Just following up on my earlier email — did you get a chance to see it?", "先ほどのメールについてフォローアップです。ご覧いただけましたか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Come to my office.", "私のオフィスに来てください。〔注: 直訳すると自然だが、召喚するように高圧的に響く〕"),
        ("Could you swing by my office when you get a chance?", "お手すきの際に私のオフィスに寄っていただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("You're late.", "あなたは遅刻です。〔注: 直訳すると自然だが、面と向かって言うと非難がましく響く〕"),
        ("I noticed you've been running a bit behind lately.", "最近少し遅れが続いているようですね。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Finish it today.", "今日中に終わらせてください。〔注: 直訳すると自然だが、命令として高圧的に響く〕"),
        ("Would it be possible to have this done by today?", "今日中に仕上げていただくことは可能でしょうか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Explain yourself.", "説明してください（弁明しなさい）。〔注: 直訳すると自然だが、詰問するように厳しく響く〕"),
        ("Could you help me understand what happened?", "何が起きたのか教えていただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("That's not correct.", "それは正しくありません。〔注: 直訳すると自然だが、会議やメールでは断定的に響く〕"),
        ("I'm not sure that's quite right — could we double-check?", "少し違うかもしれません。念のため確認しませんか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        # ============================================================
        # 接客・カスタマーサービス（客側・店員側の両方）
        # ============================================================
        ("Give me a discount.", "値引きしてください。〔注: 直訳すると自然だが、要求として図々しく響く〕"),
        ("Is there any chance of a discount?", "何か割引していただける可能性はありますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("I want a refund.", "返金してほしいです。〔注: 直訳すると自然だが、要求として一方的に響く〕"),
        ("I was hoping to get a refund, if that's possible.", "もし可能であれば、返金していただけたらと思っていました。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Bring the check.", "会計を持ってきてください。〔注: 直訳すると自然だが、命令口調でぶっきらぼうに響く〕"),
        ("Could we get the check, please?", "お会計をお願いできますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("This is broken, fix it.", "これ壊れています、直してください。〔注: 直訳すると自然だが、詰め寄るように高圧的に響く〕"),
        ("This doesn't seem to be working — could you help me with it?", "これがうまく動かないようなのですが、見ていただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Move.", "どいてください。〔注: 直訳すると自然だが、混雑した場所で唐突・ぶっきらぼうに響く〕"),
        ("Excuse me, could I just get by?", "すみません、ちょっと通していただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Bring me the menu.", "メニューを持ってきてください。〔注: 直訳すると自然だが、命令口調でぶっきらぼうに響く〕"),
        ("Could I get a menu, please?", "メニューをいただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("I don't want this, take it back.", "これはいりません、下げてください。〔注: 直訳すると自然だが、突き放すように失礼に響く〕"),
        ("Actually, I don't think this is what I ordered — could you take a look?", "実は注文したものと違うようなのですが、確認していただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Give me a table for two.", "2人用のテーブルをください。〔注: 直訳すると自然だが、要求口調でぶっきらぼうに響く〕"),
        ("Could we get a table for two, please?", "2名でお願いできますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Hurry up.", "急いでください。〔注: 直訳すると自然だが、店員に対して高圧的・失礼に響く〕"),
        ("I'm a little pressed for time — would it be possible to speed things up?", "少し時間に余裕がないのですが、急いでいただくことは可能でしょうか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("You made a mistake with my order.", "注文を間違えましたね。〔注: 直訳すると自然だが、店員を責めるように直接的に響く〕"),
        ("I think there might be a mix-up with my order.", "注文に何か行き違いがあったかもしれません。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Show me a cheaper one.", "もっと安いのを見せてください。〔注: 直訳すると自然だが、要求として素っ気なく響く〕"),
        ("Do you have anything a little more affordable?", "もう少し手頃なものはありますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("We're closed, come back tomorrow.", "閉店です、明日来てください。〔注: 直訳すると自然だが、店員の対応として突き放すように素っ気なく響く〕"),
        ("I'm afraid we're closed for the day — would you be able to come back tomorrow?", "本日は閉店とさせていただいております。よろしければ明日お越しいただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        # ============================================================
        # 雑談・誘いを断る場面
        # ============================================================
        ("I can't come.", "行けません。〔注: 直訳すると自然だが、誘いを断る返事としてそっけなく響く〕"),
        ("I'm afraid I won't be able to make it.", "残念ながら伺えそうにありません。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("I'm busy.", "忙しいです。〔注: 直訳すると自然だが、断りの返事として素っ気なく冷たく響く〕"),
        ("I've got a lot on my plate right now, unfortunately.", "今ちょっと立て込んでいて、すみません。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Speak slower.", "もっとゆっくり話してください。〔注: 直訳すると自然だが、命令口調でぶっきらぼうに響く〕"),
        ("Would you mind speaking a little more slowly?", "もう少しゆっくり話していただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("I don't want to.", "やりたくありません。〔注: 直訳すると自然だが、子どもっぽく・素っ気なく響く〕"),
        ("I'd rather not, if that's okay.", "できればやりたくないのですが、よろしいでしょうか。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Stop talking about that.", "その話はやめてください。〔注: 直訳すると自然だが、命令口調で高圧的に響く〕"),
        ("Could we maybe talk about something else?", "何か別の話をしませんか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("That's not funny.", "それ、面白くないです。〔注: 直訳すると自然だが、相手の冗談を切り捨てるように失礼に響く〕"),
        ("I'm not sure I follow the joke, sorry!", "その冗談、ちょっとよく分からなくてごめんなさい！〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("No, I don't like it.", "いいえ、好きではありません。〔注: 直訳すると自然だが、率直すぎて相手を傷つけかねない〕"),
        ("It's not really my thing, but I can see why you like it.", "あまり私の好みではないですが、あなたが好きな理由は分かります。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("I don't have time for this.", "そんな時間はありません。〔注: 直訳すると自然だが、突き放すように冷たく響く〕"),
        ("I wish I could, but I just don't have the time right now.", "できればそうしたいのですが、今は時間が取れなくて。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("I forgot your name.", "あなたの名前を忘れました。〔注: 直訳すると自然だが、率直すぎて気まずく響く〕"),
        ("I'm so sorry, could you remind me of your name again?", "申し訳ありません、お名前をもう一度教えていただけますか？〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("I have to go now.", "もう行かないといけません。〔注: 直訳すると自然だが、会話を急に切り上げるように素っ気なく響く〕"),
        ("I'm afraid I should get going, but it was so nice talking with you.", "そろそろ失礼しないといけないのですが、お話しできてよかったです。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Don't ask me that.", "それを私に聞かないでください。〔注: 直訳すると自然だが、突っぱねるように高圧的に響く〕"),
        ("I'd rather not get into that, if you don't mind.", "できればその話には触れたくないのですが、よろしいでしょうか。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("I already told you that.", "それはもう言いましたよね。〔注: 直訳すると自然だが、相手をたしなめるように冷たく響く〕"),
        ("I mentioned this earlier, but just to recap...", "先ほどお伝えした通りですが、念のためもう一度…〔注: 実際に使われる自然で丁寧な言い方〕"),

        # ============================================================
        # 道案内・指示出し（ぶっきらぼう → やわらげた言い方）
        # ============================================================
        ("Turn left.", "左に曲がってください。〔注: 単独では自然だが、見知らぬ人への道案内では命令口調にやや響く〕"),
        ("You'll want to turn left up ahead.", "この先で左に曲がるといいですよ。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Do it this way.", "こうやってください。〔注: 直訳すると自然だが、押し付けるように高圧的に響く〕"),
        ("It might work better if you tried it this way.", "こうやってみると、うまくいくかもしれません。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Read the manual.", "マニュアルを読んでください。〔注: 直訳すると自然だが、突き放すように冷たく響く〕"),
        ("It might help to check the manual first.", "まずマニュアルを確認してみると役立つかもしれません。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Go straight, then turn right.", "まっすぐ行って、右に曲がってください。〔注: 直訳すると自然だが、見知らぬ人への道案内では命令口調にやや響く〕"),
        ("You'll want to go straight, and then take a right.", "まっすぐ行って、それから右に曲がるといいですよ。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Press this button first.", "まずこのボタンを押してください。〔注: 直訳すると自然だが、命令口調でぶっきらぼうに響く〕"),
        ("You'll want to press this button first.", "まずこのボタンを押すといいですよ。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("Use a different approach.", "違うやり方を使ってください。〔注: 直訳すると自然だが、頭ごなしに指示するように響く〕"),
        ("You might want to try a different approach.", "違うやり方を試してみるといいかもしれません。〔注: 実際に使われる自然で丁寧な言い方〕"),

        # ============================================================
        # 悪い知らせを和らげる・謝罪にクッションを加える
        # ============================================================
        ("I made a mistake.", "私はミスをしました。〔注: それ自体は問題ない言い方だが、クッション言葉を加えるとより丁寧に響く〕"),
        ("I'm really sorry, I think I made a mistake here.", "本当に申し訳ありません、ここでミスをしてしまったようです。〔注: クッション言葉を加えたより丁寧な言い方〕"),

        ("We can't do that.", "それはできません。〔注: 直訳すると自然だが、断定的に突き放すように響く〕"),
        ("Unfortunately, that's not something we're able to do.", "残念ながら、それは私どもではいたしかねます。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("It's too expensive.", "それは高すぎます。〔注: 直訳すると自然だが、率直すぎて失礼に響くことがある〕"),
        ("That might be a bit outside our budget, unfortunately.", "残念ながら、それは少し予算オーバーかもしれません。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("That won't work.", "それはうまくいきません。〔注: 直訳すると自然だが、断定的に切り捨てるように響く〕"),
        ("I'm not sure that will quite work, unfortunately.", "残念ながら、それはうまくいかないかもしれません。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("We don't have it.", "それはありません（在庫がありません）。〔注: 直訳すると自然だが、素っ気なく突き放すように響く〕"),
        ("I'm afraid we don't have that in stock right now.", "あいにく、只今その商品の在庫を切らしております。〔注: 実際に使われる自然で丁寧な言い方〕"),

        ("The answer is no.", "答えはノーです。〔注: 直訳すると自然だが、非常に冷たく突き放すように響く〕"),
        ("I'm afraid the answer is no, at least for now.", "残念ながら、少なくとも今のところは難しいです。〔注: 実際に使われる自然で丁寧な言い方〕"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

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
    "before", "later", "earlier", "second", "point", "say",
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
