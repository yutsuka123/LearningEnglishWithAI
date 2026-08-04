# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated words & phrases for FRENCH / ITALIAN CUISINE VOCABULARY,
authored by Claude.

Focus (`料理`ドメインの深掘り): 既存の141語は仏伊料理名の基本語（baguette, coq au
vin, croissant / carbonara, pizza, tiramisuなど）と共通調理技法（bake, sauté,
whisk...）でほぼ埋まっている。本スクリプトはその先— フランス料理・イタリア料理を
「英語で語る」ための語彙を深掘りする:

- フランス: sous vide / flambe / deglaze / roux / mise en place / julienne /
  confit などフランス語由来の調理技法、cassoulet / tarte tatin / eclair /
  madeleine / pate / terrine / gratin などの料理、amuse-bouche / entree（仏語の
  「前菜」の意味、米語のmain courseとは違う） / fine dining / cheese course /
  Michelin star / sommelier などの食文化語彙。
- イタリア: penne / fusilli / ravioli / tortellini / linguine / orzo などパスタ
  の形状語彙、osso buco / saltimbocca / caprese salad / bruschetta / pesto /
  focaccia / arancini などの料理、primo/secondo のコース構成、aperitivo文化、
  al denteの概念、nonna（おばあちゃん）の手料理語彙。

フレーズは注文・給仕への質問・ワイン/コースのペアリング・食事作法の説明を中心に
2シーン（フランス料理を英語で語る／イタリア料理を英語で語る）に整理した。

既存語（コース側で既に投入済みのため再追加していないもの）:
baguette, coq au vin, creme brulee, crepe, croissant, escargot, foie gras,
quiche, ratatouille, souffle, bouillabaisse, macaron, carbonara, gnocchi,
lasagna, mozzarella, pasta, pizza, risotto, spaghetti, tiramisu, prosciutto,
minestrone, gelato, および bake/boil/simmer/sauté/whisk/knead/marinate/
season/garnish/dice/mince/peel/drain/ferment/steam/grill/deep-fry/stir-fry
などの調理技法（他の料理にも共通するため）。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_food_france_italy.py
      python scripts/add_food_france_italy.py --missing-words   # report only

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
    "フランス料理を英語で語る": [
        # --- 注文・メニューについて尋ねる ---
        ("What's in the sauce?", "ソースには何が入っていますか？"),
        ("What does 'confit' mean on this menu?", "メニューにある『コンフィ』とはどういう意味ですか？"),
        ("Is this dish served with a sauce on the side?", "この料理はソースを別添えで出していただけますか？"),
        ("I'd like to start with the amuse-bouche, please.", "まずアミューズブーシュからお願いします。"),
        ("Could we see the cheese course selection?", "チーズコースの品揃えを見せていただけますか？"),
        ("Is the foie gras pan-seared or served as a terrine?", "フォアグラはソテーですか、それともテリーヌですか？"),
        ("We'd like to order the tasting menu tonight.", "今夜はテイスティングメニューをお願いします。"),
        ("How many courses are included in the tasting menu?", "テイスティングメニューには何コース含まれていますか？"),
        ("What's today's fish special?", "本日の魚料理のおすすめは何ですか？"),
        ("Is the sauce made with a reduction of red wine?", "このソースは赤ワインを煮詰めて作られていますか？"),
        ("We'll have the cheese course before dessert.", "デザートの前にチーズコースをお願いします。"),
        ("This dish was cooked sous vide, wasn't it?", "この料理は低温真空調理で作られていますよね？"),
        ("The chef flambeed it right at our table.", "シェフがテーブルの前でフランベしてくれました。"),
        ("This pate has a wonderfully rich texture.", "このパテは素晴らしく濃厚な食感です。"),
        ("Could you tell me what's in the reduction sauce?", "この煮詰めソースの中身を教えていただけますか？"),
        ("Is the bread included, or is it extra?", "パンは料金に含まれていますか、それとも別料金ですか？"),
        # --- ワイン・ペアリング ---
        ("Could you recommend a wine pairing for this?", "これに合うワインペアリングを教えていただけますか？"),
        ("Could you suggest something that pairs well with red wine?", "赤ワインに合う一品を提案していただけますか？"),
        ("Would you recommend a Bordeaux or a Burgundy with this?", "これにはボルドーとブルゴーニュ、どちらがおすすめですか？"),
        ("Could you decant the wine before serving?", "ワインは注ぐ前にデキャンタージュしていただけますか？"),
        ("We'd like separate wine pairings for each course.", "各コースに合わせて別々のワインペアリングをお願いします。"),
        ("Is this restaurant Michelin-starred?", "このレストランはミシュランの星付きですか？"),
        # --- 食事作法・食文化を説明する ---
        ("My compliments to the pastry chef.", "パティシエに賛辞を送ります。"),
        ("In French fine dining, the cheese course usually comes before dessert.", "フランスの高級料理では、チーズコースは通常デザートの前に出されます。"),
        ("Is it customary to leave a tip in French restaurants?", "フランスのレストランではチップを残すのが習慣ですか？"),
        ("The entree in French actually refers to the starter, not the main dish.", "フランス語のentreeは実は前菜を指し、メイン料理ではありません。"),
        ("Could we get some more mise en place before we start cooking?", "調理を始める前に下ごしらえをもう少しお願いできますか？"),
        ("A proper French meal is built around a fixed course structure.", "本格的なフランス料理の食事は、決まったコース構成で組み立てられています。"),
    ],
    "イタリア料理を英語で語る": [
        # --- 注文・給仕への質問 ---
        ("Could I get this pasta al dente?", "このパスタはアルデンテでお願いできますか？"),
        ("What's the difference between primo and secondo?", "プリモとセコンドの違いは何ですか？"),
        ("We usually start with an antipasto to share.", "普段は前菜のアンティパストをシェアすることから始めます。"),
        ("Is the ragu made with beef or pork?", "このラグーは牛肉ですか、それとも豚肉ですか？"),
        ("Could you recommend a good trattoria nearby?", "近くにおすすめのトラットリアはありますか？"),
        ("Is this a Neapolitan-style or Sicilian-style pizza?", "これはナポリ風ですか、それともシチリア風のピザですか？"),
        ("Could we order a plate of mixed antipasti to start?", "まず盛り合わせのアンティパストを一皿お願いできますか？"),
        ("Is the sauce made with fresh basil pesto?", "このソースは生バジルのペストで作られていますか？"),
        ("What pasta shape goes best with this sauce?", "このソースにはどのパスタの形が一番合いますか？"),
        ("This risotto is cooked to perfection, wonderfully creamy.", "このリゾットは完璧な仕上がりで、素晴らしくクリーミーです。"),
        ("Could you bring us some fresh parmesan on top?", "上に新鮮なパルメザンチーズをかけていただけますか？"),
        ("Could you tell me what contorno comes with the secondo?", "セコンドにはどんな付け合わせ（コントルノ）が付きますか？"),
        ("Is this olive oil extra virgin and cold-pressed?", "このオリーブオイルはエキストラバージンで低温圧搾ですか？"),
        ("Is the burrata fresh today?", "ブラータチーズは今日届いたばかりですか？"),
        ("Is this a wood-fired pizza?", "これは薪窯で焼いたピザですか？"),
        ("Could you tell me which region this wine is from?", "このワインはどの地方のものか教えていただけますか？"),
        # --- 食文化を説明する ---
        ("We always have a little aperitivo before dinner.", "私たちは夕食前に必ず軽いアペリティーヴォをとります。"),
        ("This tastes just like my nonna's recipe.", "これはまるで私のおばあちゃんの手料理のような味です。"),
        ("Would you like an espresso after the meal?", "食後にエスプレッソはいかがですか？"),
        ("In Italy, cappuccino is mainly a morning drink.", "イタリアではカプチーノは主に朝に飲むものです。"),
        ("We finished the meal with a shot of limoncello.", "食事の締めにリモンチェッロを一杯いただきました。"),
        ("The dolce here is homemade every day.", "ここのデザートは毎日手作りです。"),
        ("Is this a family recipe passed down for generations?", "これは代々受け継がれてきた家庭のレシピですか？"),
        ("Northern Italian cuisine uses more butter and cream than the south.", "北イタリア料理は南部よりバターやクリームを多く使います。"),
        ("We'd like to try the regional specialties of Tuscany.", "トスカーナ地方の郷土料理を試してみたいです。"),
        ("Could you recommend a wine that pairs with osso buco?", "オッソブーコに合うワインを教えていただけますか？"),
        ("Let's finish with an affogato instead of plain gelato.", "普通のジェラートではなくアフォガートで締めましょう。"),
        ("Could we share a few small plates, Italian style?", "イタリア風に、いくつかの小皿をシェアしましょうか？"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # ============================= フランス料理 =============================
    # --- 調理技法（フランス語由来で英語圏でも使われる） ---
    ("sous vide", "低温真空調理（そしてヴィード）", "名詞", "The salmon was cooked sous vide for perfect texture.", "料理", "900"),
    ("flambe", "フランベする（アルコールで一気に燃やす）", "動詞", "The waiter flambeed the dessert at our table.", "料理", "900"),
    ("deglaze", "デグラッセする（鍋底の旨味をワイン等で溶かす）", "動詞", "Deglaze the pan with white wine after searing.", "料理", "850"),
    ("roux", "ルー（小麦粉とバターを炒めたソースの素）", "名詞", "Whisk the roux until it turns golden brown.", "料理", "800"),
    ("mise en place", "下ごしらえ・仕込み", "名詞", "Good mise en place makes service run smoothly.", "料理", "900"),
    ("bechamel sauce", "ベシャメルソース（ホワイトソース）", "名詞", "The gratin is topped with bechamel sauce.", "料理", "800"),
    # --- 料理・菓子 ---
    ("cassoulet", "カスレ（白いんげん豆と肉の煮込み）", "名詞", "Cassoulet is a hearty stew from southern France.", "料理", "900"),
    ("tarte tatin", "タルトタタン（逆さまに焼くリンゴタルト）", "名詞", "We shared a warm tarte tatin for dessert.", "料理", "850"),
    ("eclair", "エクレア", "名詞", "The eclair was filled with rich chocolate cream.", "料理", "600"),
    ("madeleine", "マドレーヌ", "名詞", "She served warm madeleines with the tea.", "料理", "650"),
    ("pate", "パテ（肉や魚をペースト状にした前菜料理）", "名詞", "The pate was served with toasted baguette slices.", "料理", "750"),
    ("terrine", "テリーヌ（型に詰めて冷やし固めた料理）", "名詞", "The terrine had layers of vegetables and meat.", "料理", "850"),
    ("gratin", "グラタン（表面を焼いて焦げ目をつけた料理）", "名詞", "The potato gratin was golden and bubbling.", "料理", "600"),
    # --- 食文化・食事の作法 ---
    ("amuse-bouche", "アミューズブーシュ（コース前の一口料理）", "名詞", "The chef sent out an amuse-bouche before the starter.", "料理", "950"),
    ("entree", "アントレ（仏式では主菜の前の一皿、米式では主菜）", "名詞", "In France, the entree is not the main dish.", "料理", "700"),
    ("main course", "メインディッシュ・主菜", "名詞", "What would you like for your main course?", "料理", "500"),
    ("fine dining", "高級レストランでの食事", "名詞", "This is one of the best fine dining spots in town.", "料理", "700"),
    ("etiquette", "作法・エチケット", "名詞", "Table etiquette matters a lot at formal dinners.", "料理", "600"),
    ("wine pairing", "ワインペアリング（料理とワインの組み合わせ）", "名詞", "The wine pairing really brought out the flavors.", "料理", "800"),
    ("sommelier", "ソムリエ（ワインの専門家）", "名詞", "The sommelier recommended a light white wine.", "料理", "800"),
    ("cheese course", "チーズコース（メインとデザートの間に出る）", "名詞", "We finished the meal with a cheese course.", "料理", "800"),
    ("michelin star", "ミシュランの星", "名詞", "The restaurant just earned its first Michelin star.", "料理", "750"),
    ("tasting menu", "テイスティングメニュー・お任せコース", "名詞", "We opted for the seven-course tasting menu.", "料理", "750"),
    ("multi-course meal", "複数コースの食事", "名詞", "It was a long multi-course meal, but every dish was worth it.", "料理", "650"),
    ("palate", "味覚・舌", "名詞", "This wine has a very refined palate.", "料理", "800"),
    ("exquisite", "極上の・洗練された", "形容詞", "The presentation of each dish was exquisite.", "料理", "800"),
    ("vinaigrette", "ビネグレット（フレンチドレッシング）", "名詞", "The salad was dressed with a light vinaigrette.", "料理", "700"),
    ("consomme", "コンソメ（澄んだスープ）", "名詞", "The consomme was crystal clear and full of flavor.", "料理", "700"),
    ("ganache", "ガナッシュ（チョコレートとクリームを混ぜたもの）", "名詞", "The truffles are coated in dark chocolate ganache.", "料理", "800"),
    ("puff pastry", "パイ生地", "名詞", "The pie is wrapped in flaky puff pastry.", "料理", "700"),
    ("creme fraiche", "クレームフレッシュ（コクのある発酵クリーム）", "名詞", "A dollop of creme fraiche finished the soup.", "料理", "800"),
    ("shallot", "エシャロット", "名詞", "Finely chop the shallot before adding it to the pan.", "料理", "700"),
    ("gourmet", "グルメ通の・高級な・美食家", "形容詞", "It's a gourmet grocery store with imported cheeses.", "料理", "500"),
    ("delicacy", "珍味・ごちそう", "名詞", "Escargot is considered a delicacy in France.", "料理", "700"),
    ("vintage", "ヴィンテージ（ワインの収穫年）", "名詞", "What vintage is this Bordeaux?", "料理", "600"),
    ("decant", "デキャンタージュする（澱を除くため別容器に移す）", "動詞", "We let the sommelier decant the wine at the table.", "料理", "850"),
    ("bistro", "ビストロ（気軽なフランス料理店）", "名詞", "There's a cozy bistro just around the corner.", "料理", "650"),
    ("brasserie", "ブラッスリー（大衆的なフランス料理店）", "名詞", "The brasserie serves classic dishes all day.", "料理", "800"),
    ("charcuterie", "シャルキュトリー（食肉加工品の盛り合わせ）", "名詞", "We ordered a charcuterie board to start.", "料理", "850"),
    ("patisserie", "パティスリー（洋菓子店）", "名詞", "The patisserie down the street sells amazing croissants.", "料理", "750"),
    ("boulangerie", "ブーランジェリー（パン屋）", "名詞", "The boulangerie opens at six every morning.", "料理", "750"),
    ("dijon mustard", "ディジョンマスタード", "名詞", "The dressing is made with dijon mustard and olive oil.", "料理", "700"),
    ("crouton", "クルトン", "名詞", "The soup was topped with garlic croutons.", "料理", "500"),
    ("french onion soup", "オニオングラタンスープ", "名詞", "The french onion soup came with a layer of melted cheese.", "料理", "550"),
    ("steak frites", "ステーキフリット（ステーキとフライドポテト）", "名詞", "Steak frites is a classic French bistro dish.", "料理", "750"),
    ("petit four", "プティフール（一口サイズの小さな菓子）", "名詞", "The meal ended with a plate of petit fours.", "料理", "900"),
    ("artisanal", "職人技の・こだわりの", "形容詞", "The bakery only uses artisanal baking methods.", "料理", "700"),
    # ============================= イタリア料理 =============================
    # --- パスタの形状 ---
    ("penne", "ペンネ（筒状のパスタ）", "名詞", "The penne was tossed in a spicy tomato sauce.", "料理", "500"),
    ("fusilli", "フジッリ（らせん状のパスタ）", "名詞", "Fusilli holds thick sauces really well.", "料理", "650"),
    ("ravioli", "ラビオリ（詰め物入りのパスタ）", "名詞", "The ravioli was stuffed with ricotta and spinach.", "料理", "550"),
    ("tortellini", "トルテリーニ（輪状の詰め物入りパスタ）", "名詞", "We ordered tortellini in a light broth.", "料理", "700"),
    ("linguine", "リングイネ（平打ちの細長いパスタ）", "名詞", "The linguine was served with clams and garlic.", "料理", "650"),
    ("orzo", "オルゾ（米粒状のパスタ）", "名詞", "The orzo was cooked in a rich vegetable broth.", "料理", "800"),
    ("macaroni", "マカロニ", "名詞", "She made macaroni and cheese for the kids.", "料理", "400"),
    # --- 料理 ---
    ("osso buco", "オッソブーコ（仔牛すね肉の煮込み）", "名詞", "Osso buco is traditionally served with risotto.", "料理", "900"),
    ("saltimbocca", "サルティンボッカ（仔牛肉と生ハム、セージの料理）", "名詞", "The saltimbocca was wrapped in prosciutto and sage.", "料理", "900"),
    ("caprese salad", "カプレーゼサラダ（トマトとモッツァレラのサラダ）", "名詞", "The caprese salad used the ripest summer tomatoes.", "料理", "600"),
    ("bruschetta", "ブルスケッタ", "名詞", "The bruschetta was topped with diced tomato and basil.", "料理", "600"),
    ("panna cotta", "パンナコッタ", "名詞", "The panna cotta was served with a berry coulis.", "料理", "600"),
    ("pesto", "ペスト（バジルベースのソース）", "名詞", "The pasta was tossed in fresh basil pesto.", "料理", "600"),
    ("focaccia", "フォカッチャ", "名詞", "The focaccia was drizzled with olive oil and rosemary.", "料理", "650"),
    ("calzone", "カルツォーネ（折りたたんで焼いたピザ）", "名詞", "The calzone was stuffed with cheese and ham.", "料理", "650"),
    ("arancini", "アランチーニ（揚げライスコロッケ）", "名詞", "The arancini were crispy on the outside and creamy inside.", "料理", "800"),
    ("polenta", "ポレンタ（とうもろこし粉を煮た料理）", "名詞", "The polenta was served soft under braised beef.", "料理", "750"),
    ("antipasto", "アンティパスト（イタリア料理の前菜）", "名詞", "The antipasto included cured meats and olives.", "料理", "700"),
    ("cannoli", "カンノーリ（筒状の揚げ菓子）", "名詞", "The cannoli was filled with sweet ricotta cream.", "料理", "700"),
    ("ragu", "ラグー（肉のトマト煮込みソース）", "名詞", "The ragu had simmered for hours on the stove.", "料理", "700"),
    ("carpaccio", "カルパッチョ（薄切りの生肉・生魚料理）", "名詞", "The beef carpaccio was drizzled with olive oil.", "料理", "700"),
    ("pizzeria", "ピッツェリア（ピザ専門店）", "名詞", "There's a great pizzeria near the train station.", "料理", "650"),
    ("pancetta", "パンチェッタ（イタリアの塩漬け豚肉）", "名詞", "The sauce was made with pancetta and onions.", "料理", "800"),
    ("burrata", "ブラータ（外はモッツァレラ、中はクリーム状のチーズ）", "名詞", "The burrata oozed cream when we cut into it.", "料理", "800"),
    ("ricotta", "リコッタチーズ", "名詞", "The ravioli was filled with ricotta and spinach.", "料理", "600"),
    ("affogato", "アフォガート（エスプレッソをかけたジェラート）", "名詞", "We ended dinner with an affogato.", "料理", "850"),
    ("biscotti", "ビスコッティ（二度焼きの硬いクッキー）", "名詞", "The biscotti is perfect for dipping in coffee.", "料理", "700"),
    ("amaro", "アマーロ（イタリアの薬草系食後酒）", "名詞", "We tried a bitter amaro after the meal.", "料理", "900"),
    ("contorno", "コントルノ（セコンドに添える副菜）", "名詞", "The contorno was simple roasted vegetables.", "料理", "950"),
    ("dolce", "ドルチェ（イタリア料理のコースにおけるデザート）", "名詞", "For dolce, we shared a slice of tiramisu.", "料理", "850"),
    # --- 食材・飲み物 ---
    ("espresso", "エスプレッソ", "名詞", "He always finishes his meal with an espresso.", "料理", "400"),
    ("cappuccino", "カプチーノ", "名詞", "In Italy, cappuccino is rarely ordered after noon.", "料理", "350"),
    ("digestivo", "ディジェスティーヴォ（食後酒）", "名詞", "The waiter offered a digestivo to settle the meal.", "料理", "850"),
    ("limoncello", "リモンチェッロ（レモンリキュール）", "名詞", "Limoncello is a specialty of the Amalfi Coast.", "料理", "800"),
    ("balsamic vinegar", "バルサミコ酢", "名詞", "A drizzle of balsamic vinegar finished the salad.", "料理", "600"),
    ("parmesan", "パルメザンチーズ", "名詞", "Could you grate some parmesan over the pasta?", "料理", "450"),
    ("olive oil", "オリーブオイル", "名詞", "Drizzle olive oil over the bread before serving.", "料理", "400"),
    ("extra virgin", "エキストラバージン（オリーブオイルの最高級グレード）", "形容詞", "This is extra virgin olive oil, pressed just last month.", "料理", "750"),
    # --- 地域性 ---
    ("tuscan", "トスカーナの・トスカーナ風", "形容詞", "Tuscan cuisine relies heavily on olive oil and beans.", "料理", "800"),
    ("sicilian", "シチリアの・シチリア風", "形容詞", "Sicilian cooking often features seafood and citrus.", "料理", "750"),
    ("neapolitan", "ナポリの・ナポリ風", "形容詞", "Neapolitan pizza has a soft, thin crust.", "料理", "800"),
    ("regional cuisine", "郷土料理・地方料理", "名詞", "Every region in Italy has its own regional cuisine.", "料理", "700"),
    # --- 食文化・コース構成 ---
    ("primo", "プリモ（一皿目、パスタなどの主食コース）", "名詞", "The primo was a simple spaghetti aglio e olio.", "料理", "900"),
    ("secondo", "セコンド（二皿目、肉や魚のメインコース）", "名詞", "For the secondo, we chose grilled sea bass.", "料理", "900"),
    ("aperitivo", "アペリティーヴォ（食前酒とおつまみの習慣）", "名詞", "Aperitivo hour usually starts around six.", "料理", "850"),
    ("al dente", "アルデンテ（歯ごたえを残した茹で加減）", "形容詞", "The pasta should always be cooked al dente.", "料理", "700"),
    ("trattoria", "トラットリア（気軽なイタリア料理店）", "名詞", "We found a small trattoria run by a local family.", "料理", "750"),
    ("osteria", "オステリア（居酒屋的なイタリア料理店）", "名詞", "The osteria only had five tables and a short menu.", "料理", "850"),
    ("nonna", "おばあちゃん（イタリアの家庭料理の象徴）", "名詞", "The recipe has been in her nonna's kitchen for decades.", "料理", "800"),
    ("homemade", "家庭で作った・手作りの", "形容詞", "The pasta here is all homemade.", "料理", "400"),
    ("family recipe", "家伝のレシピ", "名詞", "It's a family recipe passed down from her grandmother.", "料理", "500"),
    ("rustic", "素朴な・田舎風の", "形容詞", "The restaurant has a rustic, countryside feel.", "料理", "700"),
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
