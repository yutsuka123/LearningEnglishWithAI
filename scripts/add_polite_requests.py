# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for POLITE REQUESTS / ASKING / PERMISSION /
OFFERS / SUBJUNCTIVE & WISHES, authored by Claude.

Focus (ユーザー要望): could you / would you / can I / may I / I wish,
お願い・尋ねる表現、仮定法、take a seat / have a seat / may I help you 等の
もてなし・申し出表現と、その関連表現を体系的に強化する。

丁寧度の段階や仮定法のニュアンスも学べるよう、日本語訳に〔注〕を付した。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_polite_requests.py
      python scripts/add_polite_requests.py --missing-words   # report only

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
    # 依頼・お願い：can → could → would → would you mind → I was wondering の
    # 順に丁寧（＝控えめ）になる。注で丁寧度を示す。
    "依頼・お願い": [
        ("Can you help me with this?", "これ手伝ってくれる？〔親しい間柄・カジュアル〕"),
        ("Will you give me a hand?", "手を貸してくれる？〔カジュアルな依頼〕"),
        ("Could you help me with this?", "これを手伝っていただけますか？〔丁寧〕"),
        ("Would you help me with this?", "これを手伝っていただけますか？〔丁寧・相手の意向を尋ねる〕"),
        ("Could you possibly help me out?", "もしよろしければ手伝っていただけませんか？〔とても丁寧〕"),
        ("Would you mind helping me?", "手伝っていただけませんか？〔とても丁寧。返事のYes/Noに注意〕"),
        ("Would you mind giving me a hand?", "手を貸していただけませんか？〔とても丁寧〕"),
        ("I was wondering if you could help me.", "手伝っていただけないかと思いまして。〔最も控えめで丁寧〕"),
        ("I was hoping you could take a look at this.", "これを見ていただけたらと思っていたのですが。〔控えめ〕"),
        ("Do you think you could help me with this?", "これを手伝ってもらえそうですか？〔やわらかい依頼〕"),
        ("If it's not too much trouble, could you check this?", "ご面倒でなければ、これを確認していただけますか？"),
        ("When you get a chance, could you reply?", "お手すきのときに返信いただけますか？"),
        ("Whenever you have a moment, please call me.", "お時間のあるときにお電話ください。"),
        ("Could you do me a quick favor?", "ちょっとお願いしてもいい？〔簡単な頼みごと〕"),
        ("May I ask you a favor?", "お願いがあるのですが。〔丁寧〕"),
        ("Could I ask you to send me the file?", "ファイルを送っていただけますか？〔丁寧な依頼〕"),
        ("Would you be able to finish it by Friday?", "金曜までに仕上げていただけますか？〔丁寧〕"),
        ("Would it be possible to move the meeting?", "会議をずらすことは可能でしょうか？〔丁寧な打診〕"),
        ("Could you let me know by tomorrow?", "明日までに教えていただけますか？"),
        ("Would you mind if I asked you to wait a moment?", "少々お待ちいただけますか？〔とても丁寧〕"),
        ("Please go ahead.", "どうぞ進めてください／お先にどうぞ。"),
        ("Please feel free to ask.", "どうぞお気軽にお尋ねください。"),
        ("Could you spare me a few minutes?", "少しお時間をいただけますか？"),
        ("Would you kindly confirm the details?", "詳細をご確認いただけますでしょうか。〔ややフォーマル〕"),
        ("I'd appreciate it if you could reply soon.", "早めにご返信いただけると助かります。〔丁寧〕"),
        ("It would be great if you could join us.", "ご参加いただけたら嬉しいです。"),
        ("Could you possibly lower your voice?", "もう少し声を落としていただけますか？〔遠回しの注意〕"),
        ("Would you mind not smoking here?", "ここでの喫煙はご遠慮いただけますか？〔丁寧な制止〕"),
        ("Sorry to bother you, but could you help me?", "お忙しいところすみません、手伝っていただけますか？"),
        ("I hate to ask, but could you cover my shift?", "申し訳ないのですが、シフトを代わってもらえますか？"),
        ("Can I count on you for this?", "この件、頼りにしていい？"),
        ("Could you keep this between us?", "この件は内緒にしておいてもらえますか？"),
    ],
    # 許可を求める：can I → could I → may I → do you mind if I → would it be OK if
    "許可を求める": [
        ("Can I come in?", "入ってもいい？〔カジュアル〕"),
        ("Could I come in?", "入ってもよろしいですか？〔丁寧〕"),
        ("May I come in?", "入ってもよろしいでしょうか？〔とても丁寧・フォーマル〕"),
        ("Can I sit here?", "ここ座ってもいい？"),
        ("Is this seat taken?", "この席、空いていますか？〔着席前の定番〕"),
        ("Do you mind if I sit here?", "ここに座ってもいいですか？〔丁寧。No＝どうぞの意〕"),
        ("Would you mind if I opened the window?", "窓を開けてもよろしいですか？〔とても丁寧〕"),
        ("Do you mind if I join you?", "ご一緒してもいいですか？"),
        ("May I join you?", "ご一緒してもよろしいですか？〔丁寧〕"),
        ("Can I borrow your pen?", "ペン借りてもいい？"),
        ("Could I borrow this for a second?", "ちょっとこれをお借りできますか？"),
        ("May I use your restroom?", "お手洗いをお借りしてもよろしいですか？"),
        ("Is it okay if I leave early today?", "今日は早めに失礼してもいいですか？"),
        ("Would it be okay if I brought a friend?", "友人を連れてきてもよろしいですか？〔丁寧な打診〕"),
        ("Can I take a look?", "見てもいい？"),
        ("May I take a look at this?", "これを拝見してもよろしいですか？〔丁寧〕"),
        ("Could I have a moment of your time?", "少しお時間をいただけますか？"),
        ("May I have your name, please?", "お名前を伺ってもよろしいですか？〔丁寧〕"),
        ("Do you mind if I record this?", "これを録音してもよろしいですか？"),
        ("Would you mind my asking how old you are?", "失礼ですが、おいくつか伺ってもよろしいですか？〔とても丁寧〕"),
        ("May I be excused?", "席を外してもよろしいですか？〔食事中・会議中など〕"),
        ("Can I get past, please?", "通してもらえますか？"),
        ("Could I trouble you for the salt?", "恐れ入りますが塩を取っていただけますか？〔丁寧〕"),
        ("Would it be all right to pay by card?", "カードで支払ってもよろしいですか？"),
        ("May I interrupt for a second?", "少しだけよろしいですか？〔割り込む前に〕"),
        ("Mind if I take this chair?", "この椅子もらってもいい？〔Do you の省略・カジュアル〕"),
        ("Is it all right if I call you later?", "あとで電話してもいいですか？"),
        ("Could I possibly switch seats with you?", "もしよければ席を替わっていただけますか？"),
        ("May I have a word with you?", "少しお話ししてもよろしいですか？"),
        ("Permission to speak freely?", "率直に申し上げてもよろしいですか？〔ややかしこまった/軍隊的〕"),
    ],
    # 申し出・もてなし（着席・接客）：give an offer / hospitality
    "申し出・もてなし": [
        ("May I help you?", "いらっしゃいませ／お手伝いしましょうか？〔接客の定番〕"),
        ("How may I help you?", "どのようなご用件でしょうか？〔丁寧な接客〕"),
        ("How can I help you today?", "本日はどうなさいましたか？〔接客〕"),
        ("What can I do for you?", "何かご用でしょうか？"),
        ("Have a seat, please.", "どうぞお掛けください。〔丁寧〕"),
        ("Please take a seat.", "どうぞお座りください。〔丁寧〕"),
        ("Take a seat.", "座って。〔カジュアル〕"),
        ("Why don't you have a seat?", "おかけになりませんか？〔やわらかい勧め〕"),
        ("Won't you come in?", "どうぞお入りください。〔丁寧な勧誘〕"),
        ("Please, after you.", "お先にどうぞ。〔ドアなどで譲る〕"),
        ("Can I get you anything to drink?", "お飲み物はいかがですか？"),
        ("Would you like something to drink?", "何かお飲みになりますか？"),
        ("Would you care for some coffee?", "コーヒーはいかがですか？〔ややフォーマル〕"),
        ("Would you like me to help you?", "お手伝いしましょうか？〔申し出〕"),
        ("Shall I carry that for you?", "それ、お持ちしましょうか？〔丁寧な申し出〕"),
        ("Let me get that for you.", "私がやりますよ／お取りします。"),
        ("Allow me.", "私にやらせてください。〔丁寧な申し出〕"),
        ("Do you need a hand?", "手伝いましょうか？"),
        ("Would you like a hand with that?", "それ、手伝いましょうか？"),
        ("Make yourself comfortable.", "どうぞ楽にしてください。"),
        ("Help yourself to the snacks.", "お菓子はご自由にどうぞ。"),
        ("Feel free to look around.", "ご自由にご覧ください。"),
        ("Please don't hesitate to ask.", "遠慮なくお尋ねください。"),
        ("It's no trouble at all.", "全く手間ではありませんよ。"),
        ("Let me know if you need anything.", "何かあれば声をかけてください。"),
        ("Shall we get started?", "始めましょうか？"),
        ("Would you like me to show you around?", "ご案内しましょうか？"),
        ("Can I take your coat?", "コートをお預かりしましょうか？"),
        ("Right this way, please.", "こちらへどうぞ。"),
        ("Please make yourself at home.", "どうぞくつろいでください。"),
        ("Would you like a refill?", "おかわりはいかがですか？"),
        ("Let me walk you out.", "お見送りします。"),
    ],
    # 仮定法・願望：I wish / If I were / would have / It's time / as if
    "仮定法・願望": [
        ("I wish I could help you.", "力になれたらいいのに。〔今できなくて残念〕"),
        ("I wish I were taller.", "もっと背が高ければなあ。〔現在の事実と反対〕"),
        ("I wish I had more time.", "もっと時間があればなあ。"),
        ("I wish you were here.", "君がここにいてくれたらなあ。"),
        ("I wish I had studied harder.", "もっと勉強しておけばよかった。〔過去への後悔〕"),
        ("I wish I hadn't said that.", "あんなこと言わなければよかった。〔過去への後悔〕"),
        ("I wish you would stop complaining.", "文句を言うのをやめてほしいんだけど。〔相手への不満・要望〕"),
        ("If I were you, I'd take the job.", "私があなたなら、その仕事を受けるよ。〔助言の定番〕"),
        ("If I were rich, I would travel the world.", "お金持ちなら世界を旅するのに。"),
        ("If I had known, I would have told you.", "知っていたら教えたのに。〔過去の事実と反対〕"),
        ("If I had left earlier, I wouldn't have missed the train.", "もっと早く出ていれば電車に乗り遅れなかったのに。"),
        ("If only I had listened to you.", "君の言うことを聞いていればなあ。〔強い後悔〕"),
        ("If only I could start over.", "やり直せたらなあ。"),
        ("Had I known, I would have acted differently.", "知っていたら違う行動をとっていた。〔ifを省いた倒置・文語的〕"),
        ("Were I in your position, I would resign.", "あなたの立場なら辞職するだろう。〔倒置・フォーマル〕"),
        ("I would rather stay home tonight.", "今夜はむしろ家にいたいな。"),
        ("I'd rather you didn't tell anyone.", "誰にも言わないでほしいんだ。〔相手への控えめな要望〕"),
        ("It's (high) time we left.", "そろそろ出発する時間だ。〔仮定法過去で「もう〜すべき」〕"),
        ("It's about time you apologized.", "そろそろ謝るべきだよ。"),
        ("He talks as if he knew everything.", "彼はまるで何でも知っているかのように話す。〔事実は知らない〕"),
        ("She acts as though nothing had happened.", "彼女は何事もなかったかのように振る舞う。"),
        ("Suppose you won the lottery, what would you do?", "もし宝くじが当たったら、どうする？"),
        ("What would you do if you were in my shoes?", "私の立場ならどうする？"),
        ("If I could turn back time, I would do it differently.", "時間を戻せるなら、違うやり方をするのに。"),
        ("But for your help, I would have failed.", "あなたの助けがなければ失敗していた。〔フォーマル〕"),
        ("Without water, we couldn't survive.", "水がなければ、私たちは生きられない。"),
        ("I could have done better.", "もっとうまくやれたはずなのに。"),
        ("You should have told me earlier.", "もっと早く言ってくれればよかったのに。〔過去への非難・後悔〕"),
        ("I'd have come if you had invited me.", "誘ってくれていたら行ったのに。"),
        ("If it weren't for you, I'd be lost.", "君がいなかったら、途方に暮れているよ。"),
        ("I wish things were different.", "事情が違えばなあ。"),
        ("May you have a long and happy life.", "末永くお幸せに。〔願望のmay・祈願〕"),
        ("Long may she reign.", "彼女の御代が末永く続きますように。〔祈願・文語〕"),
    ],
    # 婉曲・クッション言葉：丁寧に切り出す/断る/反論する前置き
    "婉曲・クッション言葉": [
        ("I'm sorry to bother you, but do you have a minute?", "お忙しいところ恐れ入りますが、少しよろしいですか？"),
        ("Excuse me for interrupting, but I have a question.", "お話の途中すみませんが、質問があります。"),
        ("If you don't mind my asking, where are you from?", "差し支えなければ、ご出身はどちらですか？"),
        ("I don't mean to be rude, but I have to go.", "失礼を承知で言いますが、もう行かないと。"),
        ("With all due respect, I disagree.", "お言葉ですが、私は反対です。〔丁寧な反論〕"),
        ("I'm afraid I can't make it.", "あいにく行けそうにありません。〔やわらかい断り〕"),
        ("I'd love to, but I'm tied up that day.", "ぜひ行きたいのですが、その日は予定が詰まっていて。"),
        ("Unfortunately, that won't be possible.", "残念ながら、それは難しいです。"),
        ("To be honest, I'm not sure about that.", "正直なところ、それはどうかと思います。"),
        ("If I may say so, this could be improved.", "僭越ながら、ここは改善できると思います。"),
        ("Correct me if I'm wrong, but isn't this overdue?", "間違っていたらすみませんが、これ期限切れでは？"),
        ("I was wondering if you'd reconsider.", "再考いただけないかと思いまして。"),
        ("Would it be too much to ask for an extension?", "締め切りの延長をお願いするのは図々しいでしょうか？"),
        ("I hope you don't mind my saying this, but...", "こう言っては失礼かもしれませんが…"),
        ("Just to be clear, you mean tomorrow, right?", "念のため確認ですが、明日ということですね？"),
        ("I might be wrong, but I think it's this way.", "間違っているかもしれませんが、こちらだと思います。"),
        ("Perhaps we could discuss this later?", "この件はあとで話し合えますでしょうか？〔やわらかい提案〕"),
        ("It might be a good idea to double-check.", "念のため確認した方がいいかもしれません。"),
        ("I'd suggest we wait a little longer.", "もう少し待つことを提案します。"),
        ("Sorry, but I'd rather not talk about it.", "ごめんなさい、その話はあまりしたくなくて。"),
        ("No offense, but that's not quite right.", "気を悪くしないでほしいのですが、それは少し違います。"),
        ("Forgive me for asking, but is everything okay?", "失礼ですが、何か問題でもありましたか？"),
        ("I hate to be a pain, but could you redo this?", "面倒を言って申し訳ないのですが、やり直していただけますか？"),
        ("Would you happen to know the way to the station?", "もしご存じでしたら、駅への道を教えていただけますか？〔遠回しの質問〕"),
        ("Might I make a suggestion?", "一つ提案してもよろしいでしょうか？〔フォーマル〕"),
    ],
}

# --- words: (english, japanese, pos, example, domain, level) ----------------
# Notable vocabulary used in the phrases above. Common words fall through
# (the inserter skips any english already present).

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("favor", "親切な行為・頼みごと", "名詞", "Could you do me a favor?", "口語", "500"),
    ("hesitate", "ためらう", "動詞", "Please don't hesitate to ask.", "口語", "600"),
    ("interrupt", "さえぎる・割り込む", "動詞", "May I interrupt for a second?", "口語", "600"),
    ("bother", "悩ます・手間をかける", "動詞", "Sorry to bother you.", "口語", "600"),
    ("reconsider", "考え直す", "動詞", "I was wondering if you'd reconsider.", "ビジネス", "700"),
    ("extension", "延長・延期", "名詞", "Could I ask for an extension?", "ビジネス", "700"),
    ("overdue", "期限切れの・遅れた", "形容詞", "The report is overdue.", "ビジネス", "700"),
    ("permission", "許可", "名詞", "May I have your permission?", "ビジネス", "600"),
    ("excuse", "許す・席を外させる", "動詞", "May I be excused?", "口語", "500"),
    ("appreciate", "感謝する・正しく理解する", "動詞", "I'd appreciate your help.", "ビジネス", "600"),
    ("kindly", "親切に・どうか", "副詞", "Would you kindly confirm?", "ビジネス", "700"),
    ("suppose", "仮に〜とする・思う", "動詞", "Suppose you won the lottery.", "口語", "600"),
    ("reign", "君臨する・治世", "動詞", "Long may she reign.", "教養", "800"),
    ("resign", "辞職する", "動詞", "I would resign in your position.", "ビジネス", "700"),
    ("complaint", "苦情・不満", "名詞", "I'd like to make a complaint.", "口語", "600"),
    ("complain", "不平を言う", "動詞", "I wish you would stop complaining.", "口語", "500"),
    ("offense", "気分を害すること・違反", "名詞", "No offense, but that's wrong.", "口語", "600"),
    ("spare", "割く・予備の", "動詞", "Could you spare a few minutes?", "口語", "600"),
    ("refill", "おかわり・補充", "名詞", "Would you like a refill?", "口語", "600"),
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
    "could", "would", "shall", "rather", "ever", "happen", "happen",
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
