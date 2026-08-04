# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for「クレーム・抗議」「やんわり不満/断り」
「反論・意見の相違」— 日本人英語学習者が特に苦手とする、失礼にならず
かつ弱腰にもならない自己主張の英語表現を4つの異なるレジスターに分けて
収録する。authored 2026-08-04 per user request, zero API cost (手作業で
作成し、直接 SQLite に投入する).

対象4シーン:
  1. クレーム・抗議の英語
     消費者・職場・サービス場面での「フォーマルだが芯のある」抗議・
     クレーム表現。関係を壊さずに結果を得るための、丁寧さと主張の
     バランスが取れた言い方（エスカレーション、問題の明確化、職場での
     決定への異議、未解決事案のフォローアップなど）。
  2. やんわり不満を伝える英語
     対立を表に出さずに軽い不満・小さな怒りを伝える、より間接的で
     控えめな言い方（英国的understatement／外交的ヘッジの語法）。
  3. やんわり断る英語
     誘い・依頼・申し出・提案を、冷たくならず・謝りすぎずに断る、
     自然で人間関係を保つ言い方（仕事の依頼を断る、誘いを断る、
     営業を断る、食い下がられても丁寧かつ毅然と断る、代替案で
     和らげる、など）。
  4. 反論・意見の相違を伝える英語
     会議・議論の場で、喧嘩腰にならずに反対意見・異なる視点を
     伝える言い方。

姉妹スクリプト scripts/add_polite_vs_rude_pairs1.py / pairs2.py は
「直訳すると失礼に響く表現→丁寧な言い方」を対比ペアとして扱っている。
本スクリプトはそれとは独立した内容で、対比ペアではなく状況別の
単独フレーズとして4シーンに整理している（重複がないことを投入前に
確認済み）。

No app / OpenAI API calls — everything is hand-written and inserted
directly into the SQLite DB. Duplicates are skipped by english
(lowercased); zero overlap against the live `phrases` table was
verified before this file was finalized.

Run:  python scripts/add_complaints_refusals.py
      python scripts/add_complaints_refusals.py --missing-words   # report only

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
    "クレーム・抗議の英語": [
        ("I'd like to speak to a manager, please.", "責任者の方とお話しさせていただきたいのですが。"),
        ("This is the third time this has happened.", "これが起きるのはこれで3回目です。"),
        ("I need this resolved by Friday.", "金曜日までにこれを解決していただく必要があります。"),
        ("This isn't what we agreed on.", "これは私たちが合意した内容ではありません。"),
        ("I'm not satisfied with the service I received.", "受けたサービスに満足していません。"),
        ("I have to disagree with this approach.", "このやり方には賛成しかねます。"),
        ("I don't think this is the right call, and here's why.", "これが正しい判断だとは思いません。理由をお話しします。"),
        ("I'd like to raise a concern about this.", "この件について懸念をお伝えしたいのですが。"),
        ("I'm calling to follow up on an issue I reported last week.", "先週報告した件のフォローアップでお電話しています。"),
        ("This isn't the first time I've had a problem with this.", "この件で問題が起きたのは今回が初めてではありません。"),
        ("I was told this would be taken care of, but nothing's changed.", "対応してもらえると言われましたが、何も変わっていません。"),
        ("I'd like this in writing, please.", "これを書面でいただきたいのですが。"),
        ("Who can I speak to about getting this sorted out?", "この件を解決するにはどなたに相談すればよろしいですか？"),
        ("This falls short of what was promised.", "これは約束された内容に達していません。"),
        ("I expected better than this, frankly.", "正直、もっと良いものを期待していました。"),
        ("There's clearly been a mistake somewhere, and I'd like it corrected.", "どこかで明らかにミスがありましたので、訂正していただきたいです。"),
        ("I'm going to have to insist on a full refund.", "全額返金をお願いせざるを得ません。"),
        ("This needs to be addressed today, not next week.", "これは来週ではなく、今日中に対応していただく必要があります。"),
        ("I want to formally register my objection to this decision.", "この決定について正式に異議を申し立てたいと思います。"),
        ("I have some serious concerns about how this was handled.", "この件の対応の仕方について、重大な懸念があります。"),
        ("Can you explain why this keeps happening?", "なぜこれが繰り返し起きるのか説明していただけますか？"),
        ("I don't feel this has been handled appropriately.", "この件が適切に対応されたとは感じられません。"),
        ("I'd like an explanation for the delay.", "この遅れについて説明をいただきたいです。"),
        ("This is unacceptable, and I'd like it fixed right away.", "これは受け入れられません。すぐに直していただきたいです。"),
        ("I'm going to need to escalate this if it isn't resolved soon.", "早急に解決しない場合、これを上に報告せざるを得ません。"),
        ("Let's be clear about what was promised versus what was delivered.", "約束されたことと実際に提供されたことをはっきりさせましょう。"),
        ("I'd appreciate it if someone could look into this properly this time.", "今回はきちんと調べていただけるとありがたいです。"),
        ("This charge doesn't match what I was quoted.", "この請求額は見積もりと一致していません。"),
        ("I think we need to revisit this decision — it's not working.", "この決定を見直す必要があると思います。うまくいっていません。"),
        ("I want to go on record as objecting to this.", "この件に反対したことを正式に記録に残しておきたいです。"),
    ],
    "やんわり不満を伝える英語": [
        ("I have to admit, I'm a little disappointed with how this turned out.", "正直に言うと、この結果には少しがっかりしています。"),
        ("This isn't quite what I was expecting, to be honest.", "正直、これは思っていたのとはちょっと違いました。"),
        ("I was hoping for something a bit different.", "もう少し違うものを期待していたんです。"),
        ("It's not a huge deal, but I did want to mention it.", "大したことではないのですが、一応お伝えしておきたくて。"),
        ("I don't want to make a big thing of this, but it did bother me a little.", "大げさにしたくはないのですが、少し気になったんです。"),
        ("Just so you know, this caused a bit of an issue on my end.", "念のためお伝えしますが、こちら側で少し問題が生じました。"),
        ("I'll be honest, this hasn't been the smoothest experience.", "正直に言うと、あまりスムーズな体験ではありませんでした。"),
        ("I have to say, I was a little surprised by that.", "正直、それには少し驚きました。"),
        ("It's a small thing, but it's been on my mind.", "些細なことなんですが、ずっと気になっていて。"),
        ("I don't mean to make a fuss, but I did notice a few problems.", "騒ぎ立てるつもりはないのですが、いくつか問題に気づきました。"),
        ("I'm not going to lie, this was a bit frustrating.", "正直に言うと、これには少しイライラしました。"),
        ("Not a big deal in the grand scheme of things, but worth flagging.", "全体としては大したことではないのですが、一応お伝えしておく価値はあるかと。"),
        ("I probably wouldn't have chosen this myself, if I'm honest.", "正直、自分だったら選ばなかったと思います。"),
        ("It left a bit of a sour taste, if I'm being honest.", "正直に言うと、少し後味の悪いものが残りました。"),
        ("I won't pretend I'm thrilled about this.", "これに大喜びしているふりはできません。"),
        ("Between you and me, I wasn't overly impressed.", "ここだけの話、あまり感心はしませんでした。"),
        ("It's a minor gripe, but I thought I'd mention it anyway.", "些細な不満なのですが、一応お伝えしておこうと思いまして。"),
        ("I'll admit it rubbed me the wrong way a little.", "正直、少し引っかかるものがありました。"),
        ("Nothing major, but it did catch me off guard.", "大したことではないのですが、ちょっと意表を突かれました。"),
        ("I'm not upset exactly, just a bit underwhelmed.", "怒っているというほどではないのですが、少し物足りなさを感じています。"),
        ("It wasn't quite the experience I was hoping for.", "期待していたような体験ではありませんでした。"),
        ("A small heads-up: this hasn't gone entirely smoothly.", "念のためお伝えしておくと、これは完全にスムーズとは言えませんでした。"),
        ("I did want to gently mention that this hasn't been ideal.", "やんわりお伝えしたいのですが、これはあまり理想的ではありませんでした。"),
        ("I'm sure it wasn't intentional, but it did cause a bit of a headache.", "意図的ではなかったと思いますが、少し困ったことになりました。"),
    ],
    "やんわり断る英語": [
        ("I'm afraid I won't be able to take this on right now.", "申し訳ないのですが、今はこれをお引き受けできません。"),
        ("I'd love to, but I've already got plans that day.", "ぜひ行きたいのですが、その日はもう予定が入っていて。"),
        ("I'll have to pass on this one, but thanks for thinking of me.", "今回は見送らせていただきますが、声をかけてくれてありがとう。"),
        ("I appreciate you asking again, but my answer's still no.", "また聞いてくれてありがたいのですが、答えはやはりノーです。"),
        ("I can't do Friday, but Monday works for me.", "金曜日は無理ですが、月曜日なら大丈夫です。"),
        ("Thanks so much for the offer, but I think I'll sit this one out.", "お誘いありがとうございます、でも今回は遠慮しておきます。"),
        ("I really appreciate the invite, but I'm going to have to say no this time.", "お誘い本当にありがたいのですが、今回は辞退させてください。"),
        ("That sounds great, but I don't think I can commit to it right now.", "とても良さそうですが、今は確約できそうにありません。"),
        ("I'm going to have to give this one a miss, I'm afraid.", "申し訳ないのですが、今回は見送らせていただきます。"),
        ("As tempting as that sounds, I'll have to say no.", "魅力的なお話ですが、お断りせざるを得ません。"),
        ("I don't think I can swing that this week, sorry.", "すみません、今週はそれをやりくりできそうにありません。"),
        ("My plate's a little full at the moment, so I'll have to pass.", "今ちょっと手一杯なので、見送らせてください。"),
        ("I'd rather not, but thanks for asking.", "できればご遠慮したいのですが、聞いてくれてありがとう。"),
        ("Thanks, but it's not really something I'm looking for right now.", "ありがたいのですが、今はそういうものを求めていないんです。"),
        ("I hear you, but I'm going to stick with no on this one.", "おっしゃることは分かりますが、この件はやはりノーとさせてください。"),
        ("I appreciate you following up, but nothing's changed on my end.", "確認してくれてありがたいのですが、こちらの状況は変わっていません。"),
        ("That's a generous offer, but I think I'll pass for now.", "ありがたいお申し出ですが、今回は見送ろうと思います。"),
        ("I don't think this is the right time for me, unfortunately.", "残念ながら、今は自分にとって良いタイミングではなさそうです。"),
        ("Not this time, but ask me again down the road — I might be free.", "今回は無理ですが、また今度声をかけてください。空いているかもしれません。"),
        ("I appreciate the thought, but I'm going to say no for now.", "気持ちはありがたいのですが、今のところノーとさせてください。"),
        ("It's not really my kind of thing, but thanks for the invite.", "あまり自分の好みではないのですが、誘ってくれてありがとう。"),
        ("I'm swamped this week, so I'll have to take a pass.", "今週は手一杯なので、見送らせていただきます。"),
        ("Much as I'd like to help, I don't think I'm the right person for this.", "力になりたいのはやまやまですが、自分は適任ではないと思います。"),
        ("I'd rather not commit to that just yet, if you don't mind.", "よろしければ、それについてはまだ確約は避けたいのですが。"),
        ("Thanks for thinking of me, but I'll leave this one to someone else.", "声をかけてくれてありがとう、でもこれは他の方に任せようと思います。"),
        ("I don't think I'm going to be able to make that work, sorry.", "すみません、それを実現するのは難しそうです。"),
        ("Let's leave it for now — maybe another time.", "今回は見送りましょう、また機会があれば。"),
        ("I can't take this on, but I know someone who might be able to help.", "これは引き受けられませんが、力になれそうな人に心当たりがあります。"),
        ("Sorry, this one's a no from me, but good luck with it.", "すみません、これは私からはノーです。でもうまくいくといいですね。"),
    ],
    "反論・意見の相違を伝える英語": [
        ("I'm not sure I fully agree with that.", "それに完全に同意できるかは分かりません。"),
        ("Can I offer a different perspective?", "別の視点を提示してもよろしいですか？"),
        ("That's a fair point, but I'd push back on one part of it.", "それはもっともな指摘ですが、一部については異論があります。"),
        ("I hear what you're saying, but I don't think that's the whole picture.", "おっしゃることは分かりますが、それが全てではないと思います。"),
        ("I see where you're coming from, but I'm not entirely convinced.", "お考えは理解できますが、完全には納得できていません。"),
        ("I take your point, but I'd frame it a little differently.", "おっしゃることは分かりますが、私なら少し違う捉え方をします。"),
        ("I'm going to have to respectfully disagree on this one.", "この件については、失礼ながら異論を唱えさせていただきます。"),
        ("That's not quite how I see it, honestly.", "正直、私の見方は少し違います。"),
        ("I think there's another way to look at this.", "これには別の見方もあると思います。"),
        ("Can I throw in a different take on this?", "これについて別の見解を挟んでもいいですか？"),
        ("I get the logic, but something about it doesn't sit right with me.", "理屈は分かるのですが、何かしっくりこない部分があります。"),
        ("I'm on the fence about that — I see both sides.", "それについてはまだ迷っています。どちらの言い分も分かるので。"),
        ("That's one way to look at it, but I'd add a caveat.", "それも一つの見方ですが、一言付け加えたいことがあります。"),
        ("I'm not entirely sold on that idea, to be honest.", "正直、その考えには完全には納得していません。"),
        ("I think we're not quite on the same page here.", "この件について、私たちの認識は少しずれているように思います。"),
        ("There's a piece of this I still don't agree with.", "この中で、まだ納得できない部分があります。"),
        ("I'd like to poke a hole in that argument, if I can.", "もしよければ、その主張の弱点を指摘させてください。"),
        ("Fair enough, but let me offer a counterpoint.", "それはもっともですが、反対の視点も述べさせてください。"),
        ("I don't see it quite the same way you do.", "私はあなたとまったく同じようには見ていません。"),
        ("I think it's worth considering the other side of this too.", "この件については、別の側面も考える価値があると思います。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----
# このバッチは状況別のフレーズに焦点を当てており、追加の単語は不要。

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
