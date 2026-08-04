# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for ANIME/MANGA FANDOM ENGLISH, authored by
Claude.

Focus (フレーズ集の手薄な領域を補強): 海外のアニメ・漫画ファンが実際に使う
「英語」。日本語のアニメ用語ではなく、Reddit・YouTubeのリアクション動画・
考察系動画エッセイなどで英語圏のファンが交わす表現を体系的にカバーする。
エピソードへの実況・感想、神回や展開の評価、原作準拠 vs アニメオリジナルの
議論、作画・制作会社の話題、ファンダム文化（ネタバレ配慮・考察・カップリン
グ・脳内設定）、配信・視聴形態（サブ/ダブ/同時配信）、英語ファンダムに定着
した日本語由来のロ－ンワード（isekai, shounenなど）、コンベンション・コス
プレ関連、SNS/動画エッセイでの決まり文句までを網羅する。

コンテンツポリシー: 性的な内容・暴力/グロ表現・ファンサービス的/示唆的な
表現は一切含めない（他の一般向けシーンと同じトーンを維持）。

丁寧度やニュアンス・使われる文脈が分かるよう、日本語訳に〔注〕を付した。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_anime_fandom.py
      python scripts/add_anime_fandom.py --missing-words   # report only

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
    "アニメ・海外ファン文化": [
        # --- 実況・感想（エピソードへの反応） ---
        ("That episode was insane.", "あの話やばかった。〔強い感想・くだけた〕"),
        ("I did NOT see that coming.", "全然予想してなかった。〔大文字のNOTで強調〕"),
        ("I'm still not over that scene.", "あのシーンまだ引きずってる。"),
        ("This arc is such a slow burn.", "この編、じわじわ盛り上がるタイプだね。〔slow burn=ゆっくり展開〕"),
        ("That was such a gut punch.", "あれは精神的にきつかった。〔感情的に強くこたえた〕"),
        ("I need a minute after that episode.", "あの話の後、ちょっと放心してる。"),
        ("The internet is losing it over this episode.", "このエピソードでネット中が大騒ぎになってる。"),
        ("This scene lives in my head rent-free.", "このシーン、頭から離れない。〔ずっと考えてしまう〕"),
        # --- 神回・展開の評価・考察 ---
        ("This show really knows how to stick the landing.", "この作品、締めくくり方が本当にうまい。〔終わり方を綺麗に決める〕"),
        ("The finale kind of fell flat for me.", "最終回、正直ちょっと物足りなかった。"),
        ("That plot twist completely blindsided me.", "あの展開の急転にまったく気づかなかった。"),
        ("Called it!", "やっぱりそうなると思った！〔予想が的中したときの決まり文句〕"),
        ("I have a theory about who the real villain is.", "本当の黒幕について自分なりの考察がある。"),
        ("This fan theory actually holds up.", "このファン考察、意外と筋が通ってる。"),
        ("That was a total curveball.", "予想外の展開だった。"),
        ("This episode is peak fiction.", "この話はもう最高傑作級。〔ネットスラング・最大級の褒め言葉〕"),
        # --- 原作・アニメ化・作画 ---
        ("This adaptation is pretty faithful to the source material.", "このアニメ化、原作にかなり忠実だね。"),
        ("They cut a lot of content from the manga.", "漫画からかなり内容がカットされてる。"),
        ("The anime deviates from the manga around episode 12.", "12話あたりからアニメが原作と違う展開になる。"),
        ("It's an anime-original arc, not in the manga at all.", "それはアニメオリジナルの編で、原作には全くない。"),
        ("This is filler, so you can skip it.", "これは本筋と関係ない話だから飛ばしても大丈夫。〔filler=補完エピソード〕"),
        ("The pacing works better in the manga, honestly.", "正直、テンポは漫画の方がうまくいってる。"),
        ("The animation quality took a huge dip this episode.", "この話、作画の質がかなり落ちた。"),
        ("Studio really outdid themselves with this fight scene.", "このバトルシーン、制作会社が本当に頑張った出来。"),
        ("The character designs got a bit of a glow-up this season.", "今シーズン、キャラデザが少し洗練された。〔glow-up=見違えるほど良くなる〕"),
    ],
    "アニメ・視聴とファンダム作法": [
        # --- ファンダム文化（ネタバレ・考察・カップリング・脳内設定） ---
        ("Please tag your spoilers.", "ネタバレにはタグをつけてください。〔SNSでの投稿マナー〕"),
        ("No spoilers past episode 5, please!", "5話より先のネタバレは無しでお願いします！"),
        ("I'm still catching up, so no spoilers.", "まだ追いついてないのでネタバレなしでお願いします。"),
        ("Let's keep this thread spoiler-free.", "このスレッドはネタバレなしで進めましょう。"),
        ("That's just my headcanon, but I love the idea.", "あくまで自分の脳内設定だけど、この考え好きなんだ。〔headcanon=公式設定ではない個人的解釈〕"),
        ("I'm not really into shipping, but I get the appeal.", "カップリング推しはあまりしないけど、魅力はわかる。〔shipping=キャラ同士の関係を推すこと〕"),
        ("They're endgame.", "この二人は最終的に結ばれる運命だと思う。〔カップリング考察の決まり文句〕"),
        ("This fandom is surprisingly wholesome.", "このファン層、意外と温かい雰囲気だね。"),
        ("The fandom's been buzzing about the new season announcement.", "続編発表でファンダムが盛り上がってる。"),
        # --- 配信・視聴方法 ---
        ("The simulcast drops every Friday.", "毎週金曜日に同時配信される。〔simulcast=日本と同時期の配信〕"),
        ("It's getting a dub next season.", "来シーズン吹き替え版が出る。"),
        ("I prefer watching it subbed.", "字幕版で見る方が好き。"),
        ("This show is a Crunchyroll exclusive.", "この作品はCrunchyroll独占配信。"),
        ("The simuldub comes out a week after the Japanese release.", "同時吹き替え版は日本での放送の1週間後に出る。"),
        ("It's streaming with a one-week delay.", "1週間遅れで配信されている。"),
        ("I'm binge-watching the whole series this weekend.", "今週末、シリーズを一気見するつもり。"),
        ("This series got picked up for an English dub.", "この作品、英語吹き替え版が制作されることになった。"),
        ("The episode just dropped.", "エピソードがちょうど配信された。〔drop=配信・公開される〕"),
        # --- 英語ファンダムに定着した日本語由来の言葉 ---
        ("This series is a classic isekai.", "この作品は王道の異世界転生ものだね。"),
        ("It's a shounen with a surprisingly deep story.", "少年漫画系だけど、意外と深いストーリーがある。"),
        ("It's giving very shoujo vibes.", "少女漫画っぽい雰囲気があるね。〔giving ~ vibes=〜な雰囲気がする〕"),
        ("That's such a tsundere thing to say.", "いかにもツンデレっぽい言い方だね。"),
        ("He's got serious main character energy.", "あの人、まさに主人公らしいオーラがある。〔ネットスラング・存在感の強さ〕"),
        ("The OP for this season is a total banger.", "今シーズンのオープニング曲、めちゃくちゃいい。〔banger=大ヒット曲・くだけた表現〕"),
        ("This is peak slice-of-life.", "これぞ日常系アニメの真骨頂。"),
        ("The senpai-kouhai dynamic is a big theme here.", "先輩後輩の関係性がここでは大きなテーマになっている。"),
    ],
    "アニメ・コンベンションと発信": [
        # --- コンベンション・コスプレ関連 ---
        ("Are you cosplaying anyone this year?", "今年は誰かのコスプレする予定？"),
        ("The con badge lines were insane this year.", "今年のコンベンションの入場列、すごい長さだった。〔con=convention の略〕"),
        ("I'm heading to Artist Alley to buy some prints.", "アーティストアレイにプリントを買いに行く。〔同人作家の販売エリア〕"),
        ("She won best in show for her cosplay.", "彼女のコスプレがコンテストで最優秀賞をとった。"),
        ("Let's grab a photo op with the voice actor.", "声優さんと写真撮影の機会をもらおう。"),
        ("The panel line wrapped around the building.", "パネル（トークイベント）の待機列が建物を一周してた。"),
        ("I picked up some merch at the dealer's room.", "物販エリアでグッズをいくつか買った。"),
        ("Are you doing a group cosplay with your friends?", "友達とグループコスプレする予定？"),
        # --- SNS・レビュー・動画エッセイの決まり文句 ---
        ("Let's break down why this scene works so well.", "このシーンがなぜこんなにいいのか分析してみよう。〔動画エッセイの定番の切り出し〕"),
        ("Hear me out on this theory.", "この考察、最後まで聞いてほしい。"),
        ("This is a hot take, but the movie was better than the show.", "賛否あるかもしれないけど、映画の方がテレビシリーズより良かった。"),
        ("Unpopular opinion: the pacing was actually fine.", "少数意見かもしれないけど、テンポは実際問題なかったと思う。"),
        ("I'll die on this hill.", "この意見だけは絶対に譲らない。〔強いこだわりを表す決まり文句〕"),
        ("This show is criminally underrated.", "この作品、正当に評価されてなさすぎる。"),
        ("It's a masterclass in world-building.", "世界観構築の見本のような作品。"),
        ("This trope is way overused at this point.", "このお決まり展開、さすがに使われすぎ。〔trope=定番の展開・型〕"),
        ("The character writing really carries this series.", "キャラクターの描写がこの作品を支えている。"),
        ("Let's do a spoiler-free review first.", "まずネタバレなしのレビューをしよう。"),
        ("I'll put my full thoughts in the comments.", "詳しい感想はコメント欄に書きます。"),
        ("This video essay changed how I see the whole series.", "この動画エッセイでシリーズ全体の見方が変わった。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("protagonist", "主人公", "名詞", "The protagonist grows a lot over the series.", "アニメ", "700"),
    ("antagonist", "敵役・対立者", "名詞", "The antagonist has a surprisingly sympathetic backstory.", "アニメ", "800"),
    ("filler", "本筋と関係ない補完エピソード", "名詞", "This episode is just filler.", "アニメ", "700"),
    ("pacing", "展開のテンポ・ペース配分", "名詞", "The pacing felt rushed this season.", "アニメ", "700"),
    ("adaptation", "脚色・映像化作品", "名詞", "This adaptation is very faithful to the manga.", "アニメ", "700"),
    ("source material", "原作", "名詞", "The show sticks closely to the source material.", "アニメ", "800"),
    ("dub", "吹き替え版", "名詞", "I usually watch the dub, not the sub.", "アニメ", "600"),
    ("simulcast", "同時配信", "名詞", "The simulcast airs right after the Japanese broadcast.", "アニメ", "800"),
    ("binge-watch", "一気見する", "動詞", "I binge-watched the whole season in one night.", "アニメ", "600"),
    ("spoiler", "ネタバレ", "名詞", "Please don't post any spoilers here.", "アニメ", "600"),
    ("headcanon", "個人的な脳内設定・解釈", "名詞", "It's just my headcanon, not confirmed by the creators.", "アニメ", "800"),
    ("fandom", "ファン層・ファンダム", "名詞", "The fandom has been very active lately.", "アニメ", "700"),
    ("franchise", "(続編を含む作品の)シリーズ全体", "名詞", "This franchise has been running for over a decade.", "アニメ", "700"),
    ("underrated", "過小評価されている", "形容詞", "This series is criminally underrated.", "アニメ", "700"),
    ("wholesome", "心温まる・健全な", "形容詞", "It's such a wholesome moment between the two characters.", "アニメ", "700"),
    ("cosplay", "コスプレ(する)", "名詞", "She made her own cosplay costume by hand.", "アニメ", "600"),
    ("voice actor", "声優", "名詞", "The voice actor really brought the character to life.", "アニメ", "600"),
    ("world-building", "世界観の構築", "名詞", "The series is praised for its rich world-building.", "アニメ", "800"),
    ("trope", "お決まりの展開・類型", "名詞", "That's a common trope in this genre.", "アニメ", "800"),
    ("villain", "悪役", "名詞", "The villain's motives are more complex than they seem.", "アニメ", "600"),
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
    "could", "would", "shall", "rather", "ever", "way", "still", "kind",
    "totally", "actually", "honestly", "pretty", "bit", "little", "next",
    "first", "full", "same", "own", "week", "year", "night", "weekend",
    "put", "grab", "picked", "buy", "made", "heading", "gets", "getting",
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
