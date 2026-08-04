# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for COMPLIMENTING / PRAISING PEOPLE (褒め方集),
authored by Claude on 2026-08-04 per user request, zero API cost.

Focus (フレーズ集の手薄な領域を補強): 日本語には敬語という文法的な仕組みが
あるため、相手が上司なのか部下なのか、年配の方なのか子供なのかによって、
語尾や言い回しが自動的に切り替わる。ところが英語には敬語の文法装置がなく、
「誰に対してどうほめるか」は語彙・言い回し・トーンの選び方だけで表現する
必要がある。この差は日本人学習者にとって見えにくい盲点であり、英語では
「上司にへつらいすぎない敬意」「部下を子供扱いしない励まし」「年配の方への
敬意」「子供への素直な称賛」を、文法ではなく単語選びで作り分けなければ
ならない。本スクリプトは、ほめる相手（上司・同僚・部下・後輩・年配の方・
子供・服装の相手・ペット）ごとに自然な英語表現を整理し、その使い分けを
学べるようにする。

トーン方針: すべて職場や日常で使える、プラトニックで社会的に適切な範囲の
称賛にとどめている（実績・努力・スキル・気配り・服装センスなど）。恋愛的・
身体評価的な表現は避けている。

DB上の scene 列は粗いカテゴリにまとめているが、各リスト内は Python コメント
で「誰をほめるか」のサブグループに区切ってあり、著者の意図が分かるように
してある:
  - 職場でほめる英語(上司・同僚・部下・後輩): 上司・先輩／同僚・ピア／
    部下・直属の後輩／後輩（経験の浅いメンバー）の4グループ
  - ほめる英語(年配の方・子供): 年配の方／子供の2グループ
  - ほめる英語(男性・女性の服装や印象): 中性的に使える表現／男性向けに
    典型的な表現／女性向けに典型的な表現の3グループ
  - ペットをほめる英語(自分の・他人の): 自分のペット／他人のペットの
    2グループ

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_compliments.py
      python scripts/add_compliments.py --missing-words   # report only

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
    "職場でほめる英語(上司・同僚・部下・後輩)": [
        # --- 上司・先輩の仕事ぶりを、へつらわず敬意を持ってほめる ---
        ("Your presentation really tied everything together.", "プレゼン、全体がすごくまとまっていましたね。"),
        ("I learned a lot from how you handled that.", "あの対応の仕方、すごく勉強になりました。"),
        ("You made that look easy, and I know it wasn't.", "簡単そうにやってましたけど、実際は大変だったはずですよね。"),
        ("That was a really smart way to frame it.", "あの説明の切り口、本当に上手でしたね。"),
        ("I appreciate how clearly you laid that out for the team.", "チームにあんなに分かりやすく説明してくださって、ありがたいです。"),
        ("You always know exactly what to say in these situations.", "こういう場面で、いつも的確な言葉を選びますよね。"),
        ("That's a great call — I wouldn't have thought of that.", "それはいい判断ですね、自分では思いつきませんでした。"),
        ("Your instincts on that were spot on.", "あの時の勘、まさにその通りでしたね。"),
        ("I really respect how you handled that meeting.", "あの会議の進め方、本当に尊敬します。"),
        ("You made a tough decision look straightforward.", "難しい決断だったはずなのに、あっさりこなしてましたね。"),
        # --- 同僚・ピアをほめる ---
        ("Nice work on that account, seriously.", "あの案件、マジでいい仕事しましたね。"),
        ("You handled that client really well.", "あのクライアント対応、本当にうまかったですね。"),
        ("You really pulled that project together.", "あのプロジェクト、よくまとめましたね。"),
        ("That was a great save — nice thinking on your feet.", "あれはナイスフォローでした、とっさの判断が見事でしたね。"),
        ("You crushed that deadline.", "あの締め切り、余裕でクリアしましたね。"),
        ("Seriously, that report was solid.", "マジで、あのレポートしっかりしてましたね。"),
        ("You've got a real knack for this stuff.", "こういうの、本当に得意ですよね。"),
        ("That was a clean pitch — well done.", "あのプレゼン、すごくきれいにまとまってましたね、お見事。"),
        ("I don't know how you got that done so fast, but nice work.", "どうやってあんなに早く終わらせたのか分からないけど、お疲れさま。"),
        ("You made that look effortless.", "涼しい顔でこなしてましたね。"),
        # --- 部下・直属のメンバーを、自信をつけるようにほめる ---
        ("You've really grown into this role.", "この役割、本当に板についてきましたね。"),
        ("That's exactly the kind of initiative I like to see.", "そういう自発的な動き、まさに求めていたものです。"),
        ("You handled that with a lot more poise than I expected.", "思っていた以上に落ち着いて対応してましたね。"),
        ("I'm impressed with how you managed that on your own.", "一人であそこまでやり切ったこと、感心しました。"),
        ("You should be proud of how that turned out.", "あの結果、誇っていいと思いますよ。"),
        ("That was a really mature way to handle a tough situation.", "難しい状況だったのに、大人な対応でしたね。"),
        ("You've come a long way since you started.", "入ったばかりの頃から、本当に成長しましたね。"),
        ("I trust you with this kind of thing now — you've earned it.", "こういうことも、もう安心して任せられます。ちゃんと実力で勝ち取りましたね。"),
        ("That was a good judgment call.", "あれはいい判断でしたね。"),
        ("Keep doing what you're doing — it's working.", "今のやり方、そのまま続けてください。ちゃんと結果につながっていますよ。"),
        # --- 後輩・まだ経験の浅いメンバーを励ますようにほめる ---
        ("You're picking this up fast.", "覚えるの、すごく早いですね。"),
        ("That was a smart way to handle it for someone still learning the ropes.", "まだ慣れていないのに、あの対応は賢いやり方でしたね。"),
        ("You're getting the hang of this already.", "もうコツをつかんできましたね。"),
        ("That question showed you're really paying attention.", "あの質問、ちゃんと話を聞いている証拠ですね。"),
        ("You're ahead of where I was at your stage.", "自分がその時期だった頃より、よっぽど出来てますよ。"),
        ("Nice catch — most people miss that at first.", "よく気づきましたね、最初はみんな見落とすところです。"),
        ("You handled that a lot better than I would have expected.", "思っていたよりずっと上手に対応してましたね。"),
        ("You're a quick study.", "覚えが早いですね。"),
        ("Don't sell yourself short — that was good work.", "自分を過小評価しないで、あれはいい仕事でしたよ。"),
        ("You've got good instincts for this.", "この仕事の勘、いいものを持ってますね。"),
    ],
    "ほめる英語(年配の方・子供)": [
        # --- 年配の方を敬意を持ってほめる ---
        ("You're in wonderful shape for your age.", "お年を感じさせないくらい、お元気ですね。"),
        ("I really admire how active you still are.", "今もこんなにアクティブでいらっしゃること、本当に尊敬します。"),
        ("You have so much energy — it's inspiring.", "すごくお元気で、見習いたいくらいです。"),
        ("You look wonderful today.", "今日、とても素敵ですね。"),
        ("I love hearing your stories — you've lived such a full life.", "お話を伺うのが好きです、本当に充実した人生を送ってこられたんですね。"),
        ("You're sharper than people half your age.", "半分の年齢の人より、よっぽど頭が冴えてらっしゃいますね。"),
        ("It's amazing how much you still get done in a day.", "一日でこんなにこなされるなんて、すごいですね。"),
        ("You've got more energy than I do!", "私よりよっぽどお元気じゃないですか！"),
        ("I really admire your outlook on life.", "人生に対する考え方、本当に尊敬します。"),
        ("You handle things with so much grace.", "何事も本当に品よくこなされますね。"),
        ("It's clear you've taken great care of yourself over the years.", "長年ご自愛されてきたのがよく分かります。"),
        ("You still move like someone twenty years younger.", "20歳は若い方みたいに動かれますね。"),
        # --- 子供を適切に励まし、称賛する ---
        ("Great job, you worked really hard on that!", "よくがんばったね、すごいよ！"),
        ("You should be proud of yourself.", "自分のことを誇りに思っていいんだよ。"),
        ("That was really clever of you.", "それ、すごく賢いやり方だったね。"),
        ("Wow, you did that all by yourself!", "わあ、全部自分でできたんだね！"),
        ("I can tell you practiced a lot.", "たくさん練習したのが伝わってくるよ。"),
        ("You're getting so good at this.", "どんどん上手になってるね。"),
        ("That took a lot of patience — nice job sticking with it.", "すごく根気がいったはずだよ、最後までがんばったね。"),
        ("You should be so proud of that!", "それは本当に誇っていいことだよ！"),
        ("You're such a fast learner.", "覚えるのがすごく早いね。"),
        ("Look at you go!", "すごいじゃない、その調子！"),
        ("That was a really kind thing to do.", "それ、すごく優しい行動だったね。"),
        ("You never give up — that's awesome.", "絶対にあきらめないところ、本当にすごいよ。"),
    ],
    "ほめる英語(男性・女性の服装や印象)": [
        # --- 中性的に使える服装・印象の褒め言葉 ---
        ("That's a great outfit.", "いい服ですね。"),
        ("You look really put-together today.", "今日、すごくきちんとした感じでいいですね。"),
        ("That color really suits you.", "その色、すごく似合ってますね。"),
        ("You always dress so well.", "いつもセンスのいい服装ですね。"),
        ("I love that jacket on you.", "そのジャケット、すごく似合ってますね。"),
        ("That's a really sharp look.", "すごく決まってますね、そのスタイル。"),
        ("You clean up nice.", "きちんとすると、また印象が違いますね。"),
        ("You've got great taste in clothes.", "服のセンス、本当にいいですね。"),
        ("That outfit really works on you.", "その格好、本当に似合ってますよ。"),
        ("You always know how to put a look together.", "いつもコーディネートがうまいですね。"),
        # --- 男性向けに典型的な服装の褒め言葉 ---
        ("That's a great suit.", "いいスーツですね。"),
        ("That tie really works with that shirt.", "そのネクタイ、シャツとすごく合ってますね。"),
        ("You look sharp today.", "今日、決まってますね。"),
        ("That's a really nice watch.", "いい時計してますね。"),
        ("That haircut suits you.", "その髪型、似合ってますね。"),
        ("You wear a suit well.", "スーツが本当に似合いますね。"),
        ("Nice shoes — those are a good look.", "いい靴ですね、それ、雰囲気ありますよ。"),
        # --- 女性向けに典型的な服装の褒め言葉 ---
        ("That dress looks great on you.", "そのワンピース、すごく似合ってますね。"),
        ("I love your hair like that.", "その髪型、すごく素敵ですね。"),
        ("That's a beautiful necklace.", "そのネックレス、素敵ですね。"),
        ("Your makeup looks really nice today.", "今日のメイク、すごく素敵ですね。"),
        ("That outfit is so cute on you.", "その服、すごく可愛くて似合ってますね。"),
        ("I love that bag — where did you get it?", "そのバッグ素敵ですね、どこで買ったんですか？"),
        ("That color looks amazing on you.", "その色、本当によく似合ってますね。"),
    ],
    "ペットをほめる英語(自分の・他人の)": [
        # --- 自分のペットを愛情を込めてほめる ---
        ("Aren't you just the best boy?", "本当にいい子だね〜（愛犬に向かって）。"),
        ("Who's a good girl? You are!", "いい子はだあれ？あなたね〜（愛犬・愛猫に向かって）。"),
        ("You're such a good boy, yes you are.", "本当にいい子だね、そうだよね〜。"),
        ("I swear this dog understands everything I say.", "この子、本当に私の言うこと全部分かってる気がする。"),
        ("She's the smartest cat I've ever had.", "今まで飼った中で一番賢い猫だと思う。"),
        ("He's got the best personality of any dog I've owned.", "今まで飼った犬の中で、一番性格がいい子だと思う。"),
        ("You're such a good listener, aren't you?", "本当に話をよく聞いてくれるよね〜。"),
        ("I don't know what I'd do without this little guy.", "この子がいなかったらどうしてたか分からないな。"),
        # --- 他人のペットをほめる ---
        ("Your dog is adorable!", "ワンちゃん、すごく可愛いですね！"),
        ("She's so well-behaved.", "本当にお行儀がいいですね。"),
        ("What a beautiful cat — what breed is he?", "きれいな猫ですね、何の種類ですか？"),
        ("He's got so much personality.", "個性豊かな子ですね。"),
        ("Your dog has the sweetest face.", "ワンちゃん、すごく可愛い顔してますね。"),
        ("She's so gentle — you can tell she's well-trained.", "すごく穏やかで、しつけが行き届いてるのが分かりますね。"),
        ("What a handsome dog!", "かっこいいワンちゃんですね！"),
        ("He's so friendly — he must get that from you.", "すごく人懐っこいですね、飼い主さん譲りですね。"),
        ("Your cat has the most beautiful eyes.", "猫ちゃん、目がすごくきれいですね。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----
# このバッチは相手別の褒め言葉（フレーズ）に焦点を当てており、追加の単語は不要。

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
