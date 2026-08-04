# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for READING IRONY, SARCASM, AND HEDGED/INDIRECT
CRITICISM in English, authored by Claude.

Focus (フレーズ集の手薄な領域を補強): 教科書的な直接表現ではなく、ネイティブが
Reddit・GitHub・フォーラム・日常会話で日常的に使う「言葉の裏を読む」スキルを
体系的に強化する。具体的には次の4つの角度をカバーする。

  1. 皮肉・アイロニーの合図: 字面（literal）はポジティブなのに、意図
     （intended）はネガティブ・批判的、という「二重構造」を持つ表現
     （例: "Oh, great, ANOTHER meeting." / "Well, that went well."）。
  2. 遠回しな批判: 一見丁寧・中立に聞こえるが、実際は強い反対・懸念を
     伝えている表現（例: "Interesting choice." / "That's... one way to
     do it."）。ビジネス・オンラインのコードレビューやフォーラムで頻出。
  3. 「技術的には可能だが推奨しない」を示す言い回し（例: "You could do
     that, but I wouldn't recommend it." / "That would technically
     work, though I wouldn't."）。
  4. 書き言葉（チャット・メール・PRコメント）における、本心からの賛同と
     しぶしぶ・皮肉混じりの賛同の見分け方。感嘆符の有無、"I guess" の
     付加、"..." の間など、テキストならではの合図に焦点を当てる。
     （相槌・話し言葉での強弱の賛同は scripts/add_backchannel.py で
     既に扱っているため、本スクリプトでは書き言葉特有の合図に絞り、
     重複を避けている。）

各フレーズの日本語訳には、字面通りの意味と、文脈上の本当の意図（皮肉・遠回しな
批判のからくり）の両方を説明する〔注〕を付した。これが本バッチの核となる
学習ポイントである。

内容ポリシー: 職場・フォーラムで問題にならない範囲に留め、下品な表現や
特定の個人・集団を攻撃する内容は含まない。あくまで「皮肉・婉曲表現という
言語メカニズム」を教えることが目的であり、意地悪さそのものを教える
ものではない。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_irony_hedging.py
      python scripts/add_irony_hedging.py --missing-words   # report only

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
    "皮肉・アイロニー：字面と本音のギャップ": [
        # --- 皮肉・アイロニーの合図（字面はポジティブ、意図はネガティブ） ---
        ("Oh, great, another meeting.", "ああ、最高、また会議か。〔字面は「素晴らしい」だが、実際は「うんざりだ」という皮肉〕"),
        ("Well, that went well.", "いやはや、うまくいきましたね。〔字面は成功を評価しているが、実際は「大失敗だった」という皮肉〕"),
        ("Sure, because that's totally going to work.", "ええ、それは絶対うまくいきますとも。〔字面は同意・確信を示すが、実際は「うまくいくわけがない」という強い皮肉〕"),
        ("Nice job.", "よくやったね。〔文脈次第で字面通りの称賛にも、ミスを咎める皮肉にもなる。声のトーンや状況で判断する必要がある〕"),
        ("Oh, fantastic.", "ああ、最高だね。〔字面は「素晴らしい」だが、悪い知らせへの落胆・皮肉の反応として使われることが多い〕"),
        ("Just what I needed.", "まさに欲しかったものだ。〔字面は歓迎の言葉だが、実際は「余計な厄介事が増えた」という皮肉〕"),
        ("Couldn't have gone better.", "これ以上ないほどうまくいったよ。〔字面は最高の結果を示すが、実際は「散々な結果だった」という皮肉として使われることが多い〕"),
        ("Oh, I'm sure that'll be fine.", "ああ、それはきっと大丈夫でしょうね。〔字面は楽観的な励ましだが、実際は「絶対にうまくいかない」という皮肉的な懸念〕"),
        ("Wow, didn't see that coming.", "うわ、予想外だったな。〔字面は驚きを示すが、実際は「予想通りすぎて笑える」という皮肉〕"),
        ("Shocking.", "驚きだね。〔字面は驚愕を示すが、「まったく意外ではない（分かりきっていた）」という皮肉として使われる〕"),
        ("What could possibly go wrong?", "何も問題なんて起きるわけないよね？〔字面は楽観的な問いかけだが、実際は「色々問題が起きるに決まっている」という皮肉の定型句〕"),
        ("Living the dream.", "夢のような生活だよ。〔字面は充実した人生を表すが、実際は「退屈・大変な日常」を自嘲・皮肉る決まり文句〕"),
        ("Great, more paperwork.", "最高だね、また書類仕事か。〔字面の「最高」とは裏腹に、面倒な仕事が増えたことへの不満を表す〕"),
        ("Perfect, just perfect.", "完璧、まさに完璧だよ。〔字面は満足を示すが、実際は悪い状況への呆れ・不満の皮肉〕"),
        ("You must be so proud.", "さぞかし誇らしいでしょうね。〔字面は祝福だが、実際は失敗や愚かな行動をやんわり非難する皮肉〕"),
        ("Cool cool cool.", "はいはい、そうですか。〔同じ語を淡々と繰り返すことで、興味のなさや呆れを示すくだけたネット表現〕"),
        ("Love that for us.", "それは最高だね（私たちにとって）。〔本来は好意的な出来事を喜ぶ表現だが、悪い状況を自嘲・皮肉る反語としても頻用される〕"),
        ("Oh sure, that'll definitely scale.", "ああ、それは間違いなくスケールするでしょうね。〔技術系フォーラムで、無理のある設計への皮肉。字面は肯定だが「絶対に破綻する」という意味〕"),
    ],
    "遠回しな批判・やんわりした反対（ビジネス／オンライン）": [
        # --- 丁寧そうで実は強い反対・批判（ビジネス／オンライン） ---
        ("Interesting choice.", "面白い選択ですね。〔字面は中立的な感想だが、実際は「その判断はどうかと思う」という遠回しな疑問・批判〕"),
        ("That's... one way to do it.", "まあ…そういうやり方もありますね。〔間を置く「…」が「賛成はしていない」というニュアンスを示す遠回しな批判〕"),
        ("Not sure that's the best approach, but okay.", "それがベストなやり方かは分かりませんが、まあいいでしょう。〔「ベストではない」と暗に否定しつつ渋々受け入れる言い方〕"),
        ("I mean, if that's what you want to do...", "まあ、それがやりたいことなら…〔文末を濁すことで「本当は賛成できない」という留保を示す〕"),
        ("That's a bold move.", "大胆な判断ですね。〔字面は称賛的だが、実際は「無謀・リスキーだ」という皮肉混じりの懸念〕"),
        ("Well, it's certainly a choice.", "まあ、確かに一つの選択ではありますね。〔「choice」だけを強調することで、暗に「良い選択とは言えない」と示す定型の遠回し批判〕"),
        ("I have some thoughts.", "少し思うところがあります。〔控えめな前置きだが、実際はこの後にまとまった批判・懸念が続く合図〕"),
        ("Not my first choice, but I can live with it.", "私が一番に選ぶものではありませんが、まあ受け入れられます。〔不満を残しつつ妥協する遠回しな表現〕"),
        ("This works, I guess.", "まあ、動くには動きますね。〔「I guess」を付け加えることで「本当は満足していない」という留保を示す〕"),
        ("I wouldn't have gone that way, but sure.", "私ならそのやり方は選びませんが、まあいいでしょう。〔不同意を先に示してから渋々容認する言い方〕"),
        ("Curious why you went with this approach.", "なぜこのやり方にしたのか気になります。〔字面は純粋な質問だが、実質は「このやり方は疑問だ」という遠回しな批判。GitHubのコードレビューなどで頻出〕"),
        ("Might be worth reconsidering this part.", "この部分は見直す価値があるかもしれません。〔控えめな提案の形を取っているが、実際は「ここは問題だ」という指摘〕"),
        ("This could use some work.", "ここはまだ改善の余地がありますね。〔控えめな言い方だが、実際は「出来があまり良くない」という婉曲的な批判〕"),
        ("Not bad, I guess.", "悪くはない…と思います。〔積極的な称賛ではなく、しぶしぶの及第点評価〕"),
        ("That's certainly a decision.", "それは確かに一つの決断ではありますね。〔「certainly a decision」という空虚な言い回しで、暗に「賛成できない決断だ」と示すミーム的表現〕"),
        ("I'll allow it, but I have questions.", "それで構いませんが、いくつか疑問があります。〔許可しつつも強い懸念を伝える言い方〕"),
        ("You do you.", "まあ、好きにすれば。〔一見「自由にどうぞ」という肯定的な言葉だが、実際は「私は賛成しないが、口出しはしない」という距離を置いた不同意〕"),
        ("I guess we'll see how that goes.", "まあ、どうなるか見てみましょう。〔懐疑的な様子を隠しつつ結果を見守る、遠回しな不安の表明〕"),
        # --- 「技術的には可能だが推奨しない」という含み ---
        ("You could do that, but I wouldn't recommend it.", "それをすることはできますが、おすすめはしません。〔可能性は認めつつ強く牽制する言い方〕"),
        ("That would technically work, though I wouldn't.", "技術的にはうまくいくでしょうが、私ならやりません。〔「technically」が「理屈の上では」という限定を示す典型表現〕"),
        ("I guess it's an option.", "まあ、選択肢の一つではありますね。〔積極的には勧めていない、消極的な容認〕"),
        ("Technically, yes, but...", "技術的にはそうですが…〔文字通りは肯定だが、後に続く「but」で実質的な反対を示す〕"),
        ("It's possible, but there might be a better way.", "可能ではありますが、もっと良い方法があるかもしれません。〔遠回しに「その方法は最善ではない」と示す〕"),
        ("That's a workaround, not a fix.", "それは応急処置であって、根本的な解決ではありません。〔一時しのぎであることを指摘し、本質的な懸念を伝える〕"),
        ("It'll work, until it doesn't.", "うまくいくとは思いますが、いつか破綻しますよ。〔一時的な動作確認は認めつつ、将来的な問題を皮肉交じりに警告する定型句〕"),
        ("Sure, it'll work — for now.", "ええ、今のところは動くでしょうね。〔「for now」が将来的な破綻を暗示する〕"),
        ("That's not wrong, exactly.", "間違ってはいない…とは言い切れますが。〔完全な肯定を避けることで、実質的な懸念を示す〕"),
        ("I wouldn't call it best practice, but it'll run.", "ベストプラクティスとは言えませんが、動くには動きます。〔動作することは認めつつ、質の低さを遠回しに指摘〕"),
        ("There are cleaner ways to do this, but this works too.", "もっとすっきりしたやり方はありますが、これでも一応動きます。〔「動く」ことは認めつつ、より良い方法があることを示唆〕"),
        ("It's not ideal, but it's not the end of the world either.", "理想的ではありませんが、致命的というわけでもありません。〔問題があることは認めつつ、許容範囲だと伝える〕"),
        # --- 書き言葉での「本心の賛同」vs「しぶしぶ・皮肉混じりの賛同」---
        ("Sounds good, thanks!", "了解です、ありがとうございます！〔感嘆符と「thanks」が本心からの前向きな同意を示す〕"),
        ("Sounds good, I guess.", "まあ、いいと思います。〔文末の「I guess」が乗り気でない・しぶしぶの同意を示す〕"),
        ("LGTM!", "問題なさそうです！（Looks Good To Meの略）〔コードレビューで本心からの承認を示す定型略語〕"),
        ("LGTM, if that's what you want to do.", "そういうことなら、まあ問題ないと思います。〔LGTMの後に条件を付けることで、実質は不本意な承認であることを示す〕"),
        ("Yeah, let's do it!", "うん、やりましょう！〔感嘆符付きで本心からの積極的な賛成を示す〕"),
        ("Yeah... let's do it.", "うん…やりましょうか。〔「…」の間が迷い・気乗りしなさを示す、書き言葉特有の合図〕"),
        ("No objections here!", "こちらは異論ありません！〔明るい即答で本心からの賛成を示す〕"),
        ("No objections... I guess.", "異論は…まあ、ないです。〔間と「I guess」が実は完全には納得していないニュアンスを残す〕"),
        ("Great, thanks.", "了解、どうも。〔感嘆符もなく短く素っ気ない返信は、チャットでは不満・そっけなさのサインとして読まれやすい〕"),
        ("This all sounds great, thank you so much!", "全部いいと思います、本当にありがとうございます！〔感嘆符・強調語が重なることで、字面通りの強い賛同を示す〕"),
        ("Sure, whatever works.", "ええ、まあ、どちらでもいいです。〔一見同意しているが、「whatever」が投げやりな態度・関心の薄さを示す〕"),
        ("K.", "了解。〔一文字だけの素っ気ない返信は、チャットでは不満・怒りのサインとして受け取られることが多い〕"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("sarcasm", "皮肉・嫌味", "名詞", "I could hear the sarcasm in his voice.", "口語", "700"),
    ("sarcastic", "皮肉な・嫌味な", "形容詞", "That was a pretty sarcastic comment.", "口語", "700"),
    ("irony", "皮肉(な状況)", "名詞", "There's a certain irony in that statement.", "口語", "700"),
    ("ironic", "皮肉な", "形容詞", "It's ironic that he's complaining about being late.", "口語", "700"),
    ("deadpan", "真顔で・無表情な", "形容詞", "She delivered the joke in a deadpan tone.", "口語", "800"),
    ("backhanded", "裏のある・遠回しに批判的な", "形容詞", "That sounded like a backhanded compliment.", "口語", "800"),
    ("understatement", "控えめな表現・過小に言うこと", "名詞", "Saying it was 'a bit late' is an understatement — it was three hours late.", "口語", "800"),
    ("euphemism", "婉曲表現", "名詞", "'Let go' is a euphemism for 'fired'.", "ビジネス", "800"),
    ("passive-aggressive", "遠回しに攻撃的な", "形容詞", "His email felt a little passive-aggressive.", "ビジネス", "800"),
    ("condescending", "見下したような", "形容詞", "He has a condescending way of explaining things.", "ビジネス", "800"),
    ("dismissive", "そっけない・軽視するような", "形容詞", "Her reply felt dismissive of the whole idea.", "ビジネス", "700"),
    ("snarky", "皮肉っぽい・意地悪な", "形容詞", "He left a snarky comment on the pull request.", "口語", "700"),
    ("terse", "そっけない・簡潔すぎる", "形容詞", "His reply was short and terse.", "ビジネス", "800"),
    ("hedge", "言葉を濁す・断定を避ける", "動詞", "She hedged her answer instead of giving a clear yes or no.", "ビジネス", "700"),
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
