# ruff: noqa: E501
"""B20残りの項目(縫製2系統・温泉銭湯サウナ補完・SNS用語・お祭り)を追加(2026-08-09)。

TODO.md「B20 工場・一次産業・手芸の語彙拡充」の残り部分に対応。

1. 縫製用語(2系統): (1)趣味の縫製→既存`手芸`domainに追加、
   (2)産業としての縫製→新設`アパレル産業`domainに追加。
2. 温泉・銭湯・サウナ: 既存`旅行`domain・`温泉文化`sceneは既に
   sauna/hot spring/rotenburo等18フレーズが充実していたため、
   未登録だったsento(銭湯)/löyly(ロウリュ)/totonou(ととのう)等を補完。
3. SNS・ブログ用語: 既存`Web・SEO・LLMO`domainはマーケティング語彙
   (follower count/influencer marketing等)は充実していたが、
   post/like/share/バズる等の日常的なSNS動作語が未登録だったため追加。
4. お祭り用語: 日本の祭り(神輿・屋台・盆踊り等)と欧米の祭り
   (カーニバル・パレード等)、双方の新規ドメイン`お祭り`を追加。

Run:  python scripts/add_b20_remaining_2026_08_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# (english, japanese, part_of_speech, example, domain, level)
WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 手芸（趣味の縫製） ---
    ("fabric", "生地・布地", "名詞", "She chose a soft cotton fabric for the baby blanket.", "手芸", "450"),
    ("sewing pattern", "型紙", "名詞", "Cut the fabric following the sewing pattern's outline.", "手芸", "550"),
    ("hem", "裾上げする・裾", "動詞", "She hemmed the pants so they wouldn't drag on the floor.", "手芸", "550"),
    ("seam allowance", "縫い代", "名詞", "Leave a half-inch seam allowance when you cut out the pieces.", "手芸", "700"),
    ("bobbin", "ボビン（下糸を巻く小さな軸）", "名詞", "Make sure the bobbin has enough thread before you start sewing.", "手芸", "600"),
    ("pin cushion", "針山", "名詞", "She kept all her sewing pins stuck in a small pin cushion.", "手芸", "550"),
    ("seam ripper", "リッパー（縫い目をほどく道具）", "名詞", "A seam ripper makes it easy to undo a mistake without damaging the fabric.", "手芸", "650"),
    ("dressmaking", "洋裁", "名詞", "She took a dressmaking class to learn how to make her own clothes.", "手芸", "550"),
    ("quilting", "キルティング", "名詞", "Quilting layers fabric together with a soft filling in between.", "手芸", "600"),
    ("selvage", "耳（織物の端の解れない部分）", "名詞", "Always check the selvage to see which way the fabric's pattern runs.", "手芸", "750"),
    ("bias tape", "バイアステープ（斜め方向に裁った縁取り用の帯布）", "名詞", "Bias tape neatly finishes the raw edge of the sleeve.", "手芸", "750"),
    ("notions", "裁縫小物（ボタン・ファスナー等の付属品の総称）", "名詞", "Don't forget to buy notions like buttons and zippers along with the fabric.", "手芸", "700"),
    # --- アパレル産業（産業としての縫製、新設ドメイン） ---
    ("garment factory", "縫製工場", "名詞", "Thousands of garment factories supply clothing to global brands.", "アパレル産業", "500"),
    ("cut and sew", "カット・アンド・ソー（生地の裁断から縫製までの工程）", "名詞", "The brand handles cut and sew production entirely in-house.", "アパレル産業", "700"),
    ("garment worker", "縫製工", "名詞", "Garment workers in the factory assemble hundreds of shirts a day.", "アパレル産業", "550"),
    ("textile", "繊維製品・織物", "名詞", "The region has a long history of textile production.", "アパレル産業", "500"),
    ("textile mill", "紡績工場・織物工場", "名詞", "Raw cotton is spun into thread at the textile mill.", "アパレル産業", "600"),
    ("spinning", "紡績", "名詞", "Spinning twists raw fibers into a continuous thread.", "アパレル産業", "650"),
    ("dyeing", "染色", "名詞", "The fabric goes through a dyeing process before it's cut into pieces.", "アパレル産業", "600"),
    ("fast fashion", "ファストファッション", "名詞", "Fast fashion brands release new styles almost every week.", "アパレル産業", "550"),
    ("pattern maker", "パターンメーカー（型紙を作る専門職）", "名詞", "A pattern maker translates the designer's sketch into a wearable shape.", "アパレル産業", "650"),
    ("apparel manufacturing", "アパレル製造業", "名詞", "Apparel manufacturing has largely shifted to countries with lower labor costs.", "アパレル産業", "600"),
    ("sewing line", "縫製ライン", "名詞", "Each worker on the sewing line handles a single step, like attaching sleeves.", "アパレル産業", "650"),
    ("sample room", "サンプルルーム（試作品を作る部署）", "名詞", "The sample room turns the designer's idea into a wearable prototype.", "アパレル産業", "700"),
    ("production quota", "生産ノルマ", "名詞", "Workers are expected to meet a daily production quota.", "アパレル産業", "650"),
    # --- 温泉・銭湯・サウナ（既存`旅行`domain・`温泉文化`sceneの補完） ---
    ("sento", "銭湯（地域住民が利用する公衆浴場、温泉ではなく沸かし湯）", "名詞", "Unlike an onsen, a sento uses heated tap water instead of natural hot spring water.", "旅行", "600"),
    ("löyly", "ロウリュ（サウナストーンに水をかけて発生させる蒸気）", "名詞", "Pouring water on the hot stones creates löyly, a burst of steam that raises the humidity.", "旅行", "700"),
    ("totonou", "ととのう（サウナ・水風呂・休憩を繰り返した後の心地よい恍惚状態）", "名詞", "After the cold plunge, she finally felt totonou, that blissful post-sauna calm.", "旅行", "700"),
    ("cold bath", "水風呂", "名詞", "Jumping into the cold bath right after the sauna is part of the ritual.", "旅行", "550"),
    ("bath towel", "バスタオル", "名詞", "Bring your own bath towel, since the facility doesn't rent them out.", "旅行", "400"),
    ("changing room", "脱衣所", "名詞", "Lockers in the changing room are coin-operated.", "旅行", "450"),
    # --- SNS用語（既存`Web・SEO・LLMO`domainの補完） ---
    ("post", "投稿する・投稿", "動詞", "She posted a photo from her trip.", "Web・SEO・LLMO", "400"),
    ("like", "いいねする・いいね", "動詞", "He liked her comment right away.", "Web・SEO・LLMO", "400"),
    ("repost", "リポストする・拡散する", "動詞", "Please repost this if you found it helpful.", "Web・SEO・LLMO", "450"),
    ("share", "シェアする・共有する", "動詞", "She shared the article with all her friends.", "Web・SEO・LLMO", "400"),
    ("follower", "フォロワー", "名詞", "His account gained ten thousand followers in a week.", "Web・SEO・LLMO", "450"),
    ("direct message", "ダイレクトメッセージ（DM）", "名詞", "Send me a direct message if you have any questions.", "Web・SEO・LLMO", "450"),
    ("go viral", "バズる（急速に拡散する）", "動詞句", "The video went viral overnight.", "Web・SEO・LLMO", "550"),
    ("flame war", "炎上（激しい非難が殺到すること）", "名詞", "The celebrity's comment sparked a flame war online.", "Web・SEO・LLMO", "600"),
    ("notification", "通知", "名詞", "She turned off notifications so she could focus on work.", "Web・SEO・LLMO", "450"),
    ("story (social media)", "ストーリー（24時間で消える投稿形式）", "名詞", "He posted a quick story about his lunch.", "Web・SEO・LLMO", "450"),
    ("feed", "フィード（タイムラインに表示される投稿の一覧）", "名詞", "My feed is full of vacation photos this week.", "Web・SEO・LLMO", "450"),
    ("screenshot", "スクリーンショット", "名詞", "She took a screenshot of the conversation.", "Web・SEO・LLMO", "450"),
    ("monetize", "収益化する", "動詞", "It took him a year to monetize his channel.", "Web・SEO・LLMO", "600"),
    ("livestream", "ライブ配信する・ライブ配信", "動詞", "The band livestreamed their concert for fans around the world.", "Web・SEO・LLMO", "550"),
    ("caption", "キャプション（写真等に添える説明文）", "名詞", "She wrote a funny caption for the photo.", "Web・SEO・LLMO", "500"),
    ("profile picture", "プロフィール写真", "名詞", "He changed his profile picture for the new year.", "Web・SEO・LLMO", "450"),
    ("bio", "自己紹介文（プロフィール欄）", "名詞", "Her bio lists her hobbies and favorite books.", "Web・SEO・LLMO", "450"),
    ("trending", "トレンドになっている", "形容詞", "The hashtag was trending worldwide by evening.", "Web・SEO・LLMO", "500"),
    ("comment section", "コメント欄", "名詞", "The comment section filled up with reactions within minutes.", "Web・SEO・LLMO", "500"),
    ("cancel culture", "キャンセルカルチャー（不祥事を理由に支持を撤回する風潮）", "名詞", "Cancel culture can end a public figure's career almost overnight.", "Web・SEO・LLMO", "700"),
    ("doomscrolling", "ドゥームスクロール（悪いニュースを延々と読み続けてしまうこと）", "名詞", "He admitted to doomscrolling for hours before bed.", "Web・SEO・LLMO", "700"),
    ("shadowban", "シャドウバン（利用者に通知せず投稿の表示範囲を制限すること）", "名詞", "Creators suspect a shadowban when their reach suddenly drops.", "Web・SEO・LLMO", "750"),
    # --- お祭り（新設ドメイン：日本の祭り＋欧米の祭り） ---
    ("mikoshi", "神輿", "名詞", "Dozens of men carried the mikoshi through the crowded streets.", "お祭り", "600"),
    ("yatai", "屋台（祭りの露店）", "名詞", "The street was lined with yatai selling grilled squid and shaved ice.", "お祭り", "500"),
    ("bon odori", "盆踊り", "名詞", "Everyone joined the bon odori circle dance around the yagura tower.", "お祭り", "600"),
    ("fireworks festival", "花火大会", "名詞", "Thousands of people gathered along the river for the fireworks festival.", "お祭り", "450"),
    ("festival float", "山車", "名詞", "An enormous wooden festival float rolled slowly through the old town.", "お祭り", "600"),
    ("taiko drumming", "太鼓演奏", "名詞", "The taiko drumming echoed through the shrine grounds.", "お祭り", "550"),
    ("goldfish scooping", "金魚すくい", "名詞", "Kids lined up for goldfish scooping at the summer festival.", "お祭り", "600"),
    ("kakigori", "かき氷", "名詞", "Nothing beats a bowl of kakigori on a hot festival night.", "お祭り", "500"),
    ("carnival", "カーニバル", "名詞", "Rio's carnival draws millions of visitors every year.", "お祭り", "450"),
    ("parade float", "パレードの山車（西洋の祭りにおける装飾車両）", "名詞", "Each parade float was covered in flowers and streamers.", "お祭り", "550"),
    ("masquerade ball", "仮面舞踏会", "名詞", "Guests wore elaborate masks to the masquerade ball.", "お祭り", "600"),
    ("harvest festival", "収穫祭", "名詞", "Communities across the region celebrate a harvest festival every autumn.", "お祭り", "500"),
    ("street fair", "ストリートフェア（路上市）", "名詞", "The street fair featured live music and local food stalls.", "お祭り", "500"),
    ("confetti", "紙吹雪", "名詞", "Confetti rained down as the parade passed by.", "お祭り", "500"),
    ("costume contest", "仮装コンテスト", "名詞", "The costume contest is always the highlight of the festival.", "お祭り", "500"),
    ("lantern festival", "灯籠祭り", "名詞", "Thousands of paper lanterns floated down the river during the lantern festival.", "お祭り", "550"),
    ("game booth", "出店（縁日のゲームの屋台）", "名詞", "Kids ran from booth to booth trying to win a prize.", "お祭り", "500"),
    ("county fair", "地域の縁日・催し物（主に米国の地方祭り）", "名詞", "The whole town turns out for the annual county fair.", "お祭り", "450"),
]

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "和食": [
        ("This dish is made with simmered fish and a sweet soy-based sauce.", "この料理は魚を甘辛い醤油ベースのタレで煮込んだものです。"),
        ("It's polite to say 'itadakimasu' before you start eating.", "食べ始める前に「いただきます」と言うのが礼儀です。"),
        ("You can pour as much of this dipping sauce as you like.", "このつけダレはお好きなだけかけていただいて構いません。"),
        ("This condiment is quite spicy, so please use it a little at a time.", "この薬味はかなり辛いので、少しずつお使いください。"),
        ("It's customary to eat sushi in the order from lighter to richer flavors.", "寿司は淡白な味から濃厚な味の順に食べるのが慣習です。"),
        ("Feel free to pick up this dish with your hands.", "この料理は手で食べていただいて大丈夫です。"),
        ("This broth was made by simmering kelp and dried bonito flakes.", "この出汁は昆布と鰹節を煮出して作られています。"),
    ],
    "お祭りの英語": [
        ("Have you ever seen a mikoshi being carried through the streets?", "神輿が通りを担がれていくのを見たことはありますか。"),
        ("Try some yatai food while you're at the festival.", "お祭りに来たなら屋台の食べ物をぜひ試してみてください。"),
        ("Would you like to join the bon odori circle?", "盆踊りの輪に加わってみませんか。"),
        ("The best spot to watch the fireworks festival fills up early.", "花火大会を見る一番良い場所は早くから埋まってしまいます。"),
        ("Each neighborhood built its own festival float this year.", "今年は各町内会が独自の山車を作りました。"),
        ("I've always wanted to try goldfish scooping at a summer festival.", "夏祭りで金魚すくいをやってみたいとずっと思っていました。"),
        ("Rio's carnival is famous for its elaborate costumes and parades.", "リオのカーニバルは凝った衣装とパレードで有名です。"),
        ("We wore masks to the masquerade ball last weekend.", "先週末の仮面舞踏会にはマスクをつけて行きました。"),
        ("The county fair has rides, games, and a pie-eating contest.", "その地域の縁日には乗り物やゲーム、パイ早食い競争があります。"),
        ("Confetti covered the entire street after the parade passed.", "パレードが通り過ぎた後、通り一面が紙吹雪で覆われました。"),
    ],
}


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }

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

        ph_added = ph_skipped = 0
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in ph_existing:
                    ph_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                ph_existing.add(en.lower())
                ph_added += 1

    print(f"words: +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
