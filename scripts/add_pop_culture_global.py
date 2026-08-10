# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Expand the existing "大衆文化" domain with vocabulary and phrases for
celebrity/entertainment culture and fandom across the US/Europe, South Korea,
Japan, China, and India, authored by Claude (2026-08-10・ユーザー要望).

既存の「大衆文化」ドメインは pop culture / subculture / viral trend など
抽象的な総論語のみで、国・ジャンル別の具体的な語彙が皆無だったため、
欧米・韓国・日本・中国・インドの5地域に目配りしつつ、芸能ニュースを話す・
推しを語る・作品の感想を話す等の場面で使う語彙を追加する。

対象語彙: 欧米の芸能・メディア用語(celebrity, paparazzi, red carpet,
blockbuster, reality TV, talk show, late-night show, tabloid)、韓国のアイドル
文化用語(idol group, trainee, debut, comeback, fan meeting, fandom name,
K-drama, Hallyu)、日本の芸能文化用語(idol, variety show, fan service,
talent agency, handshake event)、中国の大衆文化用語(C-drama, web novel,
livestreaming culture, short-video platform, fan translation)、インドの
映画文化用語(Bollywood, playback singer, item number, masala film, musical
number)、横断的なファンダム・配信文化用語(stan, parasocial relationship,
influencer, streamer, subscriber count, viral video, recommendation
algorithm, binge-read)。

既存の「アニメ」「SF」「音楽」ドメインと重複する語(binge-watch, cosplay,
fandom, spoiler, franchise, K-pop 等)、および他ドメインに既存の語
(box office, livestream, trending, cancel culture 等)は避けている。
固有の実在人物名・グループ名・作品名は一切使用せず、すべて一般的な現象・
仕組みを指す語のみ。

フレーズは芸能ニュースを話す・推しを語る・作品の感想を話す等、実際に使う
自然な口語表現("Who's your favorite idol group right now?" "I stan that
group so hard." など)。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_pop_culture_global.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 欧米: 芸能・メディア用語 ---
    ("celebrity", "有名人・セレブ", "名詞", "The restaurant is popular with celebrities.", "大衆文化", "400"),
    ("paparazzi", "パパラッチ", "名詞", "Paparazzi waited outside the hotel for hours.", "大衆文化", "700"),
    ("red carpet", "レッドカーペット", "名詞", "She walked the red carpet in a bold red dress.", "大衆文化", "600"),
    ("blockbuster", "大ヒット作", "名詞", "The studio is counting on this movie to be a blockbuster.", "大衆文化", "650"),
    ("reality TV", "リアリティ番組", "名詞", "Reality TV shows follow real people instead of actors.", "大衆文化", "550"),
    ("talk show", "トークショー", "名詞", "The actor promoted her new film on a talk show.", "大衆文化", "500"),
    ("late-night show", "深夜トークバラエティ番組", "名詞", "He told a funny story on a late-night show.", "大衆文化", "600"),
    ("tabloid", "タブロイド紙・ゴシップ紙", "名詞", "The tabloid printed an unconfirmed rumor about the singer.", "大衆文化", "700"),
    # --- 韓国: アイドル文化用語 ---
    ("idol group", "アイドルグループ", "名詞", "The idol group released their first single last month.", "大衆文化", "500"),
    ("trainee", "練習生", "名詞", "She trained as a trainee for five years before her debut.", "大衆文化", "650"),
    ("debut", "デビューする／デビュー", "動詞", "The group will debut next spring.", "大衆文化", "500"),
    ("comeback", "カムバック(新曲・新作でのシーン復帰)", "名詞", "Fans are excited about the singer's comeback.", "大衆文化", "600"),
    ("fan meeting", "ファンミーティング", "名詞", "Tickets for the fan meeting sold out in minutes.", "大衆文化", "550"),
    ("fandom name", "ファンダム名(公式のファンの呼び名)", "名詞", "Every fandom name is chosen by the group or its agency.", "大衆文化", "700"),
    ("K-drama", "韓国ドラマ", "名詞", "She stayed up all night watching a K-drama.", "大衆文化", "450"),
    ("Hallyu", "韓流(韓国大衆文化の世界的ブーム)", "名詞", "Hallyu has made Korean culture popular around the world.", "大衆文化", "750"),
    # --- 日本: 芸能文化用語 ---
    ("idol", "アイドル(日本のアイドル文化における)", "名詞", "The idol greeted fans after every show.", "大衆文化", "450"),
    ("variety show", "バラエティ番組", "名詞", "Japanese variety shows often mix comedy and games.", "大衆文化", "550"),
    ("fan service", "ファンサービス(ファンを喜ばせる演出・対応)", "名詞", "The actor's wave to the crowd was pure fan service.", "大衆文化", "650"),
    ("talent agency", "芸能事務所", "名詞", "The talent agency manages dozens of young performers.", "大衆文化", "600"),
    ("handshake event", "握手会", "名詞", "Fans lined up for hours before the handshake event.", "大衆文化", "700"),
    # --- 中国: 大衆文化用語 ---
    ("C-drama", "中国ドラマ", "名詞", "The C-drama became a huge hit across Asia.", "大衆文化", "450"),
    ("web novel", "ウェブ小説(ネット発の連載小説)", "名詞", "The web novel was later adapted into a TV series.", "大衆文化", "600"),
    ("livestreaming culture", "生配信文化", "名詞", "Livestreaming culture has changed how fans interact with stars.", "大衆文化", "700"),
    ("short-video platform", "ショート動画プラットフォーム", "名詞", "The dance trend spread quickly on a short-video platform.", "大衆文化", "650"),
    ("fan translation", "ファン翻訳(非公式のファンによる翻訳)", "名詞", "A fan translation let overseas readers enjoy the story early.", "大衆文化", "700"),
    # --- インド: 映画文化用語 ---
    ("Bollywood", "ボリウッド(インドのヒンディー語映画産業)", "名詞", "Bollywood produces more films each year than Hollywood.", "大衆文化", "550"),
    ("playback singer", "プレイバックシンガー(俳優に代わって歌う専門の歌手)", "名詞", "A playback singer recorded the song the actor lip-synced on screen.", "大衆文化", "800"),
    ("item number", "アイテムナンバー(映画中の華やかな挿入歌ダンスシーン)", "名詞", "The item number became the most talked-about scene in the film.", "大衆文化", "800"),
    ("masala film", "マサラ映画(様々なジャンル要素を混ぜたインドの娯楽映画)", "名詞", "A typical masala film blends action, romance, comedy, and music.", "大衆文化", "800"),
    ("musical number", "ミュージカルシーン(映画中の歌と踊りの場面)", "名詞", "Almost every scene can lead into a musical number.", "大衆文化", "600"),
    # --- 横断的: ファンダム・配信文化用語 ---
    ("stan", "熱狂的なファン(俗語)", "名詞", "She's a huge stan of the group and never misses a comeback.", "大衆文化", "700"),
    ("parasocial relationship", "パラソーシャル関係(一方的に親密さを感じる関係)", "名詞", "Fans can develop a parasocial relationship with a streamer they've never met.", "大衆文化", "850"),
    ("influencer", "インフルエンサー", "名詞", "The influencer promoted the brand's new product online.", "大衆文化", "500"),
    ("streamer", "配信者", "名詞", "The streamer chatted with viewers while playing the game.", "大衆文化", "500"),
    ("subscriber count", "登録者数(チャンネル登録者数)", "名詞", "Her subscriber count doubled after the video went viral.", "大衆文化", "600"),
    ("viral video", "バズった動画", "名詞", "The viral video was shared millions of times in a single day.", "大衆文化", "500"),
    ("recommendation algorithm", "おすすめアルゴリズム(視聴履歴等に基づく推薦の仕組み)", "名詞", "The recommendation algorithm keeps suggesting similar content.", "大衆文化", "750"),
    ("binge-read", "一気読みする", "動詞", "I binge-read the entire web novel in one weekend.", "大衆文化", "650"),
]

PHRASES: list[tuple[str, str]] = [
    ("Have you seen the news about that celebrity scandal?", "あの有名人のスキャンダルのニュース見た？"),
    ("Paparazzi photos leaked before the wedding.", "結婚式の前にパパラッチの写真が流出した。"),
    ("She walked the red carpet in a bold red dress.", "彼女は大胆な赤いドレスでレッドカーペットを歩いた。"),
    ("The movie was a huge blockbuster overseas.", "その映画は海外で大ヒットした。"),
    ("Did you catch the actor's talk show interview?", "あの俳優のトークショーのインタビュー見た？"),
    ("I can't believe that tabloid printed such a wild rumor.", "あのタブロイド紙があんな突飛な噂を載せるなんて信じられない。"),
    ("Who's your favorite idol group right now?", "今一番好きなアイドルグループは誰？"),
    ("She trained as a trainee for five years before her debut.", "彼女はデビューするまで5年間練習生として練習した。"),
    ("Their comeback song is stuck in my head.", "彼らのカムバック曲が頭から離れない。"),
    ("I got tickets to the fan meeting!", "ファンミーティングのチケット取れた！"),
    ("This K-drama has such a good plot.", "このK-drama、ストーリーがすごくいいんだよ。"),
    ("Hallyu really changed how people see Korean culture.", "韓流のおかげで韓国文化の見られ方がすっかり変わったよね。"),
    ("That variety show always makes me laugh.", "あのバラエティ番組はいつも笑える。"),
    ("The actor's fan service moment went viral.", "あの俳優のファンサービスがバズったよね。"),
    ("Which talent agency does she belong to?", "彼女はどの芸能事務所に所属してるの？"),
    ("The line for the handshake event was insane.", "握手会の列がすごかった。"),
    ("This C-drama has amazing costumes.", "この中国ドラマは衣装がすごく凝ってる。"),
    ("I've been binge-reading this web novel all week.", "今週はずっとこのウェブ小説を一気読みしてる。"),
    ("The dance trend blew up on that short-video platform.", "あのダンスがショート動画プラットフォームで一気に広まった。"),
    ("A fan translation let me read the story before it was official.", "ファン翻訳のおかげで公式より先にその話を読めた。"),
    ("I love Bollywood movies for the musical numbers.", "ボリウッド映画の歌と踊りのシーンが大好き。"),
    ("That item number is the most famous scene in the film.", "あのアイテムナンバーはその映画で一番有名なシーンだよ。"),
    ("It's a total masala film — action, romance, comedy, everything.", "アクションも恋愛もコメディも全部入りのマサラ映画だね。"),
    ("I follow a few influencers who review makeup.", "コスメをレビューするインフルエンサーを何人かフォローしてる。"),
    ("She streams every night after work.", "彼女は仕事終わりに毎晩配信してる。"),
    ("His subscriber count hit a million yesterday.", "彼のチャンネル登録者数が昨日100万人を超えた。"),
    ("Careful — parasocial relationships can feel very real.", "気をつけて、パラソーシャルな関係ってすごくリアルに感じられるから。"),
    ("The recommendation algorithm keeps showing me the same content.", "おすすめアルゴリズムが同じような動画ばかり出してくる。"),
    ("I stan that group so hard.", "あのグループめちゃくちゃ推してる。"),
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
                "VALUES (?, ?, '大衆文化・エンタメの英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
