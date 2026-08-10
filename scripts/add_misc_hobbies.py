# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a new "多趣味・その他" domain/scene: vocabulary and phrases for a wide
mix of hobbies that don't fit an existing domain, authored by Claude
(2026-08-10・ユーザー要望).

対象語彙: 占い(fortune-telling / astrology / horoscope / tarot card /
fortune teller)、座禅・瞑想(zazen / meditation cushion / mindful
breathing)、和太鼓(taiko ensemble / drumstick)、モルック(Mölkky / wooden
pin)、けん玉(kendama / muscle memory)、読書(bookworm / page-turner /
book club / audiobook)、俳句・短歌(haiku / tanka / kigo)、アロマ
(aromatherapy / essential oil / diffuser)、DJ(disc jockey / turntablism
/ crossfader / beatmatching)、手話(sign language / fingerspelling / sign
language interpreter)、モールス通信(Morse key / dots and dashes)、カメラ
(viewfinder / prime lens / candid shot ・「趣味・ガジェット」の既存語と
重複しない範囲で少数のみ)、および趣味全般の語(pastime / hone / niche
hobby)。占いは占星術・タロット等の一般的な語に留め、特定の教義・宗教色の
強い表現は避けた。固有名詞は使っていない(Mölkkyは競技名だが一般名詞的に
扱われるため使用)。

事前に既存DB(words)をチェックし、taiko drum(→ドメイン「芸術」)、
meditation / mindfulness(→「宗教」)、Morse code / CW(→「アマチュア無線
・無線通信」)、zodiac(→「天文」)、verse(→「音楽」)、remix(→「電子工作」)、
aperture(→「天文」)、shutter(→「建築・建物」)、turntable(→「音楽」)、
taiko drumming(→「お祭り」)が既に別ドメインに存在することを確認済み。
それらと同一の語はこのリストから除外し、taiko ensemble / meditation
cushion / Morse key / dots and dashes のような、重複しない語に置き換えて
いる。カメラは「趣味・ガジェット」の既存語(autofocus / bokeh / dynamic
range / image stabilization / rolling shutter 等)と重複しない
viewfinder / prime lens / candid shot のみ追加した。キャンプ関連は
「アウトドア・レジャー」で十分カバーされているため省略した。

フレーズは各趣味を紹介・体験する場面で実際に使う自然な口語表現("Have you
ever played Mölkky?" "Could you sign that again more slowly?" など)。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_misc_hobbies.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 占い ---
    ("fortune-telling", "占い", "名詞", "Fortune-telling is often just a fun icebreaker at parties.", "多趣味・その他", "400"),
    ("astrology", "占星術", "名詞", "She has been interested in astrology since she was a teenager.", "多趣味・その他", "600"),
    ("horoscope", "星占い", "名詞", "He reads his horoscope in the newspaper every morning.", "多趣味・その他", "500"),
    ("tarot card", "タロットカード", "名詞", "She shuffled the deck and drew three tarot cards for the reading.", "多趣味・その他", "600"),
    ("fortune teller", "占い師", "名詞", "The fortune teller told her that a big change was coming soon.", "多趣味・その他", "500"),
    # --- 座禅・瞑想 ---
    ("zazen", "座禅", "名詞", "We sat in silent zazen for twenty minutes at the temple.", "多趣味・その他", "700"),
    ("meditation cushion", "瞑想・座禅用のクッション(座蒲)", "名詞", "He placed a small meditation cushion on the floor before sitting down.", "多趣味・その他", "650"),
    ("mindful breathing", "意識を集中した呼吸法", "名詞", "Mindful breathing helped her calm her nerves before the exam.", "多趣味・その他", "650"),
    # --- 和太鼓 ---
    ("taiko ensemble", "和太鼓の演奏グループ", "名詞", "The taiko ensemble performed in perfect rhythm at the summer festival.", "多趣味・その他", "700"),
    ("drumstick", "(太鼓の)ばち", "名詞", "She gripped a drumstick in each hand and faced the big drum.", "多趣味・その他", "500"),
    # --- モルック ---
    ("Mölkky", "モルック", "名詞", "In Mölkky, players toss a wooden peg to knock down numbered pins.", "多趣味・その他", "800"),
    ("wooden pin", "(モルックなどの)木製ピン", "名詞", "Each wooden pin is numbered from one to twelve.", "多趣味・その他", "500"),
    # --- けん玉 ---
    ("kendama", "けん玉", "名詞", "He finally landed a difficult kendama trick after weeks of practice.", "多趣味・その他", "700"),
    ("muscle memory", "筋肉の記憶・体で覚えた動き", "名詞", "Years of practice gave her the muscle memory to catch the ball without looking.", "多趣味・その他", "700"),
    # --- 読書 ---
    ("bookworm", "本の虫・読書家", "名詞", "My sister is such a bookworm that she finishes a novel every week.", "多趣味・その他", "500"),
    ("page-turner", "一気に読ませる面白い本", "名詞", "The mystery novel was such a page-turner that I stayed up all night.", "多趣味・その他", "650"),
    ("book club", "読書会", "名詞", "Our book club meets once a month to discuss a new novel.", "多趣味・その他", "500"),
    ("audiobook", "オーディオブック", "名詞", "I listen to an audiobook during my morning commute.", "多趣味・その他", "450"),
    # --- 俳句・短歌 ---
    ("haiku", "俳句", "名詞", "She wrote a haiku about the first snow of the year.", "多趣味・その他", "550"),
    ("tanka", "短歌", "名詞", "A tanka has five lines, two more than a haiku.", "多趣味・その他", "750"),
    ("kigo", "季語", "名詞", "Every haiku traditionally includes a kigo, or seasonal word.", "多趣味・その他", "850"),
    # --- アロマ ---
    ("aromatherapy", "アロマセラピー", "名詞", "She unwinds with aromatherapy after a long day at work.", "多趣味・その他", "600"),
    ("essential oil", "エッセンシャルオイル・精油", "名詞", "A few drops of essential oil filled the room with a calming scent.", "多趣味・その他", "550"),
    ("diffuser", "ディフューザー(香りを拡散させる器具)", "名詞", "He switched on the diffuser to fill the room with a lavender scent.", "多趣味・その他", "600"),
    # --- DJ ---
    ("disc jockey", "ディスクジョッキー(DJ)", "名詞", "The disc jockey kept the crowd dancing until well past midnight.", "多趣味・その他", "500"),
    ("turntablism", "ターンテーブリズム(DJ技術)", "名詞", "Turntablism turns record players into instruments through scratching and mixing.", "多趣味・その他", "850"),
    ("crossfader", "クロスフェーダー(DJ機材)", "名詞", "She used the crossfader to blend smoothly into the next track.", "多趣味・その他", "750"),
    ("beatmatching", "ビートマッチング(曲のテンポ合わせ)", "名詞", "Beatmatching lets a DJ mix two songs without the beat falling apart.", "多趣味・その他", "800"),
    # --- 手話 ---
    ("sign language", "手話", "名詞", "He learned sign language so he could talk with his deaf coworker.", "多趣味・その他", "500"),
    ("fingerspelling", "指文字", "名詞", "She used fingerspelling to sign her name letter by letter.", "多趣味・その他", "700"),
    ("sign language interpreter", "手話通訳者", "名詞", "A sign language interpreter stood beside the speaker throughout the ceremony.", "多趣味・その他", "600"),
    # --- モールス通信 ---
    ("Morse key", "モールス電鍵", "名詞", "He tapped out a short message on the Morse key.", "多趣味・その他", "750"),
    ("dots and dashes", "短点と長点(モールス信号の基本要素)", "名詞", "Morse code messages are built entirely out of dots and dashes.", "多趣味・その他", "700"),
    # --- カメラ(既存「趣味・ガジェット」と重複しない語のみ) ---
    ("viewfinder", "ファインダー", "名詞", "She looked through the viewfinder to frame the shot.", "多趣味・その他", "550"),
    ("prime lens", "単焦点レンズ", "名詞", "A prime lens is lighter than a zoom lens but can't change its focal length.", "多趣味・その他", "700"),
    ("candid shot", "自然な表情を捉えたスナップ写真", "名詞", "He prefers a candid shot over a posed photo.", "多趣味・その他", "650"),
    # --- 趣味全般 ---
    ("pastime", "趣味・気晴らし", "名詞", "Gardening has become her favorite pastime on weekends.", "多趣味・その他", "500"),
    ("hone", "(技術を)磨く・洗練させる", "動詞", "He spent years honing his kendama skills through daily practice.", "多趣味・その他", "750"),
    ("niche hobby", "マイナーな趣味", "名詞", "Mölkky is still a niche hobby outside the Nordic countries.", "多趣味・その他", "700"),
]

PHRASES: list[tuple[str, str]] = [
    ("Have you ever had your fortune told?", "占ってもらったことはありますか？"),
    ("What's your zodiac sign?", "あなたの星座は何ですか？"),
    ("I read my horoscope every morning just for fun.", "楽しみで毎朝星占いを読んでいます。"),
    ("She had her tarot cards read at the festival.", "彼女はお祭りでタロット占いをしてもらいました。"),
    ("Shall we try zazen at the temple this weekend?", "今週末、お寺で座禅をやってみませんか？"),
    ("Just focus on your breathing.", "ただ呼吸に意識を集中してください。"),
    ("The taiko performance gave me chills.", "和太鼓の演奏に鳥肌が立ちました。"),
    ("Can I try hitting the drum too?", "私も太鼓を叩いてみてもいいですか？"),
    ("Have you ever played Mölkky?", "モルックをやったことはありますか？"),
    ("Let's set up the pins first.", "まずピンを並べましょう。"),
    ("Can you show me a kendama trick?", "けん玉の技を見せてもらえますか？"),
    ("I finally landed that trick!", "ついにその技を決めました！"),
    ("What are you reading these days?", "最近は何を読んでいますか？"),
    ("I got so absorbed that I couldn't put the book down.", "夢中になって、その本を手放せませんでした。"),
    ("Do you belong to a book club?", "読書会に入っていますか？"),
    ("I just started writing haiku.", "俳句を書き始めたところです。"),
    ("Does this follow the traditional 5-7-5 syllable pattern?", "これは伝統的な五・七・五の音節パターンに沿っていますか？"),
    ("This scent is so relaxing.", "この香り、とてもリラックスできますね。"),
    ("Which essential oil would you recommend for sleep?", "眠るのにはどのエッセンシャルオイルがおすすめですか？"),
    ("Could you teach me the basics of DJing?", "DJの基本を教えてもらえますか？"),
    ("Try blending these two tracks together.", "この2曲をつなげてミックスしてみて。"),
    ("I'm learning sign language little by little.", "少しずつ手話を学んでいます。"),
    ("Could you sign that again more slowly?", "もう一度、ゆっくり手話で示してもらえますか？"),
    ("How do you spell your name in sign language?", "手話であなたの名前はどう表しますか？"),
    ("I'm practicing Morse code in my free time.", "空いた時間にモールス信号を練習しています。"),
    ("Can you send an SOS in Morse code?", "モールス信号でSOSを送れますか？"),
    ("Mind if I look through your viewfinder?", "ファインダーを覗かせてもらってもいいですか？"),
    ("Let's take a candid shot of everyone.", "みんなの自然な表情を撮りましょう。"),
    ("I've picked up a lot of new hobbies lately.", "最近、新しい趣味がたくさん増えました。"),
    ("It's a pretty niche hobby, but I love it.", "かなりマイナーな趣味ですが、大好きなんです。"),
    ("How long did it take you to get good at that?", "それが上手になるまでどれくらいかかりましたか？"),
    ("I'm still a total beginner.", "まだまったくの初心者です。"),
    ("Want to give it a try?", "試してみたいですか？"),
    ("It's easier than it looks, honestly.", "正直、見た目ほど難しくはないんです。"),
]


def main() -> int:
    with db() as conn:
        existing_words = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing_words:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing_words.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")

    with db() as conn:
        existing_phrases = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in existing_phrases:
                p_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, 'いろいろな趣味の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
