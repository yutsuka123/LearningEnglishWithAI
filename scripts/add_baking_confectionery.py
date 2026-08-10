# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a new "製菓・製パン" domain/scene: vocabulary and phrases for home
baking and confectionery — icing cookies, wagashi (Japanese sweets, with
phrasing useful for explaining them to non-Japanese speakers), bread
making, cake decorating, and simple cocktail making, authored by Claude
(2026-08-10・ユーザー要望).

対象語彙: アイシングクッキー関連の道具・工程(icing, royal icing, piping
bag/tip, meringue powder, edible glitter, cookie cutter, offset spatula,
bench scraper, cooling rack)、パン作り(gluten, sourdough starter,
proofing box, banneton, crumb, egg wash, hydration ratio, windowpane
test)、ケーキ・焼き菓子(sponge cake, crumb coat, springform pan, water
bath, candy thermometer, shortcrust pastry, tempering chocolate)、和菓子
(wagashi, anko, red bean paste, kinako, mochiko — 外国人に和菓子を説明する
際に使う語も含む)、カクテル作り(cocktail shaker, jigger, muddler, simple
syrup)。固有名詞(店名・ブランド名等)は一切使用せず、すべて一般的な用語
のみ。

フレーズは実際に一緒にお菓子・パンを作っているとき、教室、レシピを
共有するときに使う自然な口語表現("Is this the right consistency for
piping?" "Let's check if the dough passes the windowpane test." など)。

事前に既存DB(words ~7300件超)を全件チェックし、domain='料理'に既に
大量の製菓・製パン関連語(dough, proof, whisk, crust, ferment, sugar,
scone, oven, cookie, yeast, sift, glaze, ganache, custard, mochi, matcha,
rolling pin, knead, levain, oven spring, batter, crimp, pipe, laminate,
baking sheet/dish 等)が登録済みであることを確認し、それらと文字列が
完全一致する語は避けている。他ドメインの outline(ビジネス)・phyllo
dough(中東・ギリシャ料理)・puff pastry(フランス料理)・sweet bean paste
(中華料理)・nozzle(電子工作)・stand mixer/hand mixer(料理)・baking soda
(化学)・salt(化学)・dust(生活)・batch(製造)等との重複も避けている。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_baking_confectionery.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 基本材料・用語 ---
    ("flour", "小麦粉", "名詞", "Sift the flour before you fold it into the batter.", "製菓・製パン", "300"),
    ("vanilla extract", "バニラエッセンス(バニラ抽出液)", "名詞", "A teaspoon of vanilla extract adds a warm aroma to the batter.", "製菓・製パン", "400"),
    ("room temperature", "常温の", "形容詞", "Use room temperature butter so it creams smoothly with the sugar.", "製菓・製パン", "400"),
    ("filling", "フィリング・詰め物", "名詞", "Spread a thin layer of filling between the two cookies.", "製菓・製パン", "400"),
    # --- アイシングクッキー ---
    ("icing", "アイシング(糖衣)", "名詞", "The cupcakes are topped with a swirl of pink icing.", "製菓・製パン", "400"),
    ("cookie cutter", "クッキー型", "名詞", "Press the cookie cutter straight down into the chilled dough.", "製菓・製パン", "450"),
    ("cooling rack", "冷却ラック", "名詞", "Transfer the cookies to a cooling rack right after baking.", "製菓・製パン", "450"),
    ("piping bag", "絞り袋", "名詞", "Snip a small corner off the piping bag before you begin.", "製菓・製パン", "550"),
    ("royal icing", "ロイヤルアイシング(卵白と粉糖で作る硬めのアイシング)", "名詞", "Royal icing dries to a hard, smooth finish.", "製菓・製パン", "600"),
    ("offset spatula", "オフセットスパチュラ(L字型のパレットナイフ)", "名詞", "An offset spatula makes it easy to smooth frosting on top of a cake.", "製菓・製パン", "650"),
    ("bench scraper", "ベンチスクレーパー(生地を切り分けるへら)", "名詞", "Use a bench scraper to cut the dough into equal portions.", "製菓・製パン", "650"),
    ("piping tip", "口金(絞り袋の先端)", "名詞", "A star-shaped piping tip creates neat swirls of frosting.", "製菓・製パン", "650"),
    ("edible glitter", "食用グリッター(食べられるラメ)", "名詞", "A dusting of edible glitter makes the cake sparkle under the lights.", "製菓・製パン", "700"),
    ("meringue powder", "メレンゲパウダー", "名詞", "Meringue powder lets you make royal icing without raw egg whites.", "製菓・製パン", "750"),
    # --- パン作り ---
    ("egg wash", "卵液(照りを出すために塗る溶き卵)", "名詞", "Brush the pastry with egg wash for a shiny, golden crust.", "製菓・製パン", "500"),
    ("gluten", "グルテン(小麦のたんぱく質)", "名詞", "Overmixing the batter develops too much gluten and makes it tough.", "製菓・製パン", "650"),
    ("crumb", "クラム(パンの内側の生地・気泡構造)", "名詞", "Fresh bread should have a soft, even crumb.", "製菓・製パン", "700"),
    ("sourdough starter", "サワードウ種(自家製の発酵種)", "名詞", "Feed the sourdough starter with equal parts flour and water.", "製菓・製パン", "750"),
    ("proofing box", "発酵器(生地を発酵させる保温箱)", "名詞", "A proofing box holds a steady temperature so the dough rises evenly.", "製菓・製パン", "750"),
    ("banneton", "バヌトン(発酵かご)", "名詞", "Dust the banneton with rice flour so the shaped dough won't stick.", "製菓・製パン", "800"),
    ("hydration ratio", "加水率(生地の水分量の割合)", "名詞", "A higher hydration ratio gives the bread bigger, irregular holes.", "製菓・製パン", "800"),
    ("windowpane test", "ウィンドウペインテスト(生地の伸展性を確認する方法)", "名詞", "The windowpane test tells you whether the gluten is fully developed.", "製菓・製パン", "850"),
    # --- ケーキ・焼き菓子 ---
    ("sponge cake", "スポンジケーキ", "名詞", "The recipe starts with a light, airy sponge cake.", "製菓・製パン", "500"),
    ("springform pan", "スプリングフォーム型(側面が外れるケーキ型)", "名詞", "Grease the springform pan well before pouring in the cheesecake batter.", "製菓・製パン", "650"),
    ("water bath", "湯煎(焼き菓子を湯の中で湯煎焼きすること)", "名詞", "Baking the custard in a water bath keeps the texture smooth.", "製菓・製パン", "650"),
    ("candy thermometer", "菓子用温度計", "名詞", "Clip the candy thermometer to the side of the pot before boiling the sugar.", "製菓・製パン", "700"),
    ("crumb coat", "クラムコート(下塗りのフロスティング)", "名詞", "The crumb coat traps loose crumbs so the final layer of frosting stays clean.", "製菓・製パン", "750"),
    ("shortcrust pastry", "ショートクラストペストリー(サクサクした練り込みパイ生地)", "名詞", "Blind bake the shortcrust pastry so the bottom doesn't turn soggy.", "製菓・製パン", "800"),
    ("tempering chocolate", "チョコレートのテンパリング(温度調整)", "名詞", "Tempering chocolate keeps it glossy and gives it a satisfying snap.", "製菓・製パン", "850"),
    # --- 和菓子(外国人に説明するときにも使える語) ---
    ("wagashi", "和菓子", "名詞", "Wagashi are traditional Japanese sweets that pair well with green tea.", "製菓・製パン", "500"),
    ("red bean paste", "あん(小豆から作る甘い餡)", "名詞", "Red bean paste is the classic filling inside a daifuku.", "製菓・製パン", "550"),
    ("anko", "あんこ(甘く煮た小豆のペースト)", "名詞", "Anko is made by simmering azuki beans with sugar until thick.", "製菓・製パン", "600"),
    ("kinako", "きなこ(炒った大豆の粉)", "名詞", "Kinako gives mochi a nutty, toasted flavor.", "製菓・製パン", "700"),
    ("mochiko", "もち粉(餅米から作る粉)", "名詞", "Mochiko is used to make the soft, stretchy dough for daifuku.", "製菓・製パン", "700"),
    # --- カクテル作り ---
    ("cocktail shaker", "カクテルシェーカー", "名詞", "Shake the cocktail shaker hard for about ten seconds.", "製菓・製パン", "500"),
    ("simple syrup", "シンプルシロップ(砂糖と水を1:1で溶かしたシロップ)", "名詞", "Simple syrup blends into cold drinks much more easily than plain sugar.", "製菓・製パン", "550"),
    ("jigger", "ジガー(カクテル用の計量カップ)", "名詞", "Measure the rum with a jigger for a balanced cocktail.", "製菓・製パン", "650"),
    ("muddler", "マドラー(材料をすり潰す棒)", "名詞", "Use a muddler to release the oils from the mint leaves.", "製菓・製パン", "650"),
]

PHRASES: list[tuple[str, str]] = [
    ("Let's outline the cookie first, then fill it in.", "まずクッキーの輪郭を描いてから、中を塗りつぶしましょう。"),
    ("Give the icing a few minutes to set before you add the next color.", "次の色をのせる前に、アイシングを数分固めてください。"),
    ("Can you pass me the piping bag with the red icing?", "赤いアイシングの入った絞り袋を取ってもらえますか？"),
    ("Make sure the dough is chilled before you cut out the shapes.", "型抜きする前に、生地をしっかり冷やしておいてください。"),
    ("How long should I knead this dough?", "この生地はどのくらいこねればいいですか？"),
    ("The dough should feel smooth and a little tacky, not sticky.", "生地はなめらかで少しべたつく程度で、べちゃべちゃにならないようにしてください。"),
    ("Let the dough rest for about ten minutes before shaping it.", "成形する前に、生地を10分ほど休ませてください。"),
    ("Don't overwork the batter or the cake will turn out dense.", "生地を混ぜすぎないでください、ケーキが重くなってしまいます。"),
    ("Is this the right consistency for piping?", "これは絞り出すのにちょうどいい固さですか？"),
    ("Fold the egg whites in gently so you don't lose the air.", "気泡をつぶさないように卵白をやさしく折り込んでください。"),
    ("We're making anko from scratch today.", "今日はあんこを一から作ります。"),
    ("Wagashi are usually less sweet than Western desserts.", "和菓子は洋菓子に比べて、たいてい甘さが控えめです。"),
    ("This one is filled with red bean paste — it's called daifuku.", "これはあんが入っていて、大福と呼ばれています。"),
    ("Try to shape it into a smooth ball with your palms.", "手のひらで丸くなめらかに形を整えてみてください。"),
    ("The texture should be soft and a bit chewy, like this.", "食感はこんな風に、柔らかくて少しもちもちしているはずです。"),
    ("Would you like to try making mochi by hand?", "手作りで餅を作ってみませんか？"),
    ("Let's check if the dough passes the windowpane test.", "生地がウィンドウペインテストに合格するか確認しましょう。"),
    ("Feed your starter tonight if you want to bake tomorrow.", "明日焼くなら、今夜発酵種にエサをあげてください。"),
    ("Score the top of the loaf before it goes into the oven.", "オーブンに入れる前に、パンの表面に切り込みを入れてください。"),
    ("The bread should sound hollow when you tap the bottom.", "底を叩いたとき、パンが中空な音を立てるはずです。"),
    ("Let's level the cake layers before we start frosting.", "フロスティングを始める前に、ケーキの層を平らにならしましょう。"),
    ("Chill the cake for twenty minutes after the crumb coat.", "クラムコートの後、ケーキを20分冷やしてください。"),
    ("Could you hand me the offset spatula?", "オフセットスパチュラを取ってもらえますか？"),
    ("How do you keep the layers from sliding around?", "どうやって層がずれないようにしているんですか？"),
    ("Let's temper the chocolate so it sets with a nice shine.", "きれいな艶が出るようにチョコレートをテンパリングしましょう。"),
    ("Watch the sugar closely once it starts to caramelize.", "砂糖がカラメル化し始めたら、目を離さないでください。"),
    ("Shake it hard for about ten seconds, then strain it into the glass.", "10秒ほどしっかりシェイクしてから、グラスに濾しながら注いでください。"),
    ("Could you muddle the mint a little more?", "ミントをもう少しすり潰してもらえますか？"),
    ("Rim the glass with sugar before you pour the drink.", "ドリンクを注ぐ前に、グラスの縁に砂糖をつけてください。"),
    ("One part syrup to two parts juice — that's the ratio I use.", "シロップ1に対してジュース2、それが私の使う割合です。"),
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
                "VALUES (?, ?, 'お菓子・パン作りの英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
