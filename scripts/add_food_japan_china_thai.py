# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated vocabulary & phrases for EXPLAINING/ORDERING/DISCUSSING
Japanese, Chinese, and Thai cuisine IN ENGLISH, authored by Claude.

The `料理`(cooking) domain already has 141 words covering common dish names
(sushi, sashimi, tempura, ramen, udon, miso soup, chow mein, dim sum, mapo
tofu, wonton, pad thai, etc. — see scripts/add_cuisine.py). This script goes
DEEPER: it does not re-add any of those dish names. Instead it targets the
English a Japanese learner needs to actually TALK ABOUT this food with a
foreigner — more specific dishes/concepts, ingredient & technique vocabulary,
dining-culture terms, and natural phrases for ordering, asking about spice
level/allergens/ingredients, and explaining an unfamiliar dish.

Three scene buckets:
  - 和食   (washoku beyond the basics: kaiseki, izakaya, natto,
                        dashi, umami, wagyu, mochi, sake, chopstick etiquette...)
  - 中華料理 (regional variety: Sichuan/Cantonese/Hunan, mala,
                        wok technique, xiaolongbao vs. potstickers, dim sum
                        brunch, lazy Susan, family-style dining...)
  - タイ料理 (tom yum, curries, som tam, sticky rice, fish sauce,
                        lemongrass-family aromatics, spice-level vocabulary,
                        street food culture, allergen questions...)

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_food_japan_china_thai.py
      python scripts/add_food_japan_china_thai.py --missing-words   # report only

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
    "和食": [
        ("What's in this dish?", "この料理には何が入っていますか？"),
        ("Is this raw fish?", "これは生魚ですか？"),
        ("Sashimi is raw fish served without rice, while sushi usually includes vinegared rice.", "刺身は酢飯を使わない生魚で、寿司は普通酢飯を使います。"),
        ("Could you explain what miso soup is?", "味噌汁とはどんなものか説明していただけますか？"),
        ("It's a fermented soybean paste dissolved in a savory broth.", "発酵させた大豆のペーストを、うまみのある出汁に溶かしたものです。"),
        ("Natto is fermented soybeans — it's sticky and has a strong smell.", "納豆は発酵させた大豆で、粘り気があり匂いが強いです。"),
        ("Is it okay to slurp my noodles?", "麺をすすって食べてもいいですか？"),
        ("Yes, slurping is actually considered polite in Japan.", "はい、実は日本ではすするのは礼儀にかなっているとされています。"),
        ("Do you know how to use chopsticks?", "箸の使い方をご存じですか？"),
        ("Never stick your chopsticks upright in a bowl of rice — it's associated with funerals.", "箸をご飯に垂直に突き刺してはいけません。お葬式を連想させます。"),
        ("Could I get this set meal with miso soup and rice?", "この定食を味噌汁とご飯付きでお願いできますか？"),
        ("What's the difference between udon and soba?", "うどんとそばの違いは何ですか？"),
        ("Udon is made from wheat flour, while soba is made from buckwheat.", "うどんは小麦粉で作られ、そばはそば粉で作られます。"),
        ("Would you like it grilled, simmered, or fried?", "焼き、煮込み、揚げのどれがいいですか？"),
        ("This restaurant is known for its wagyu beef.", "このお店は和牛で有名です。"),
        ("The marbling on this cut is incredible.", "この部位の霜降りは素晴らしいですね。"),
        ("Japanese cuisine puts a lot of emphasis on seasonal ingredients.", "和食は旬の食材をとても大切にします。"),
        ("Delicate flavors matter just as much as presentation in kaiseki dining.", "懐石料理では繊細な味わいが見た目と同じくらい重視されます。"),
        ("Let's go to an izakaya and order a few small dishes to share.", "居酒屋に行って、いくつか小皿料理をシェアして注文しましょう。"),
        ("I'd recommend trying tonkatsu if you like fried food.", "揚げ物が好きなら、とんかつを試してみるのがおすすめです。"),
        ("Sake pairs really well with sashimi.", "日本酒は刺身とよく合います。"),
        ("Would you like your sake warm or chilled?", "日本酒は熱燗と冷酒どちらがよろしいですか？"),
    ],
    "中華料理": [
        ("Chinese food varies a lot depending on the region.", "中華料理は地方によってかなり違います。"),
        ("Sichuan cuisine is known for being spicy and numbing.", "四川料理は辛くて痺れる味で知られています。"),
        ("What does mala actually taste like?", "麻辣とは実際どんな味なんですか？"),
        ("It's a combination of spicy chili and numbing Sichuan peppercorns.", "辛い唐辛子と、痺れる花椒を組み合わせた味です。"),
        ("Cantonese cuisine tends to be lighter and less oily.", "広東料理は比較的あっさりして油っこくない傾向があります。"),
        ("Could we get a few dishes to share family-style?", "みんなでシェアする形でいくつか料理を頼めますか？"),
        ("In Chinese dining culture, dishes are placed in the middle for everyone to share.", "中国の食文化では、料理は真ん中に置かれ、みんなで取り分けます。"),
        ("Could you spin the lazy Susan so I can reach the dumplings?", "餃子に手が届くように回転テーブルを回してもらえますか？"),
        ("What's the difference between potstickers and xiaolongbao?", "焼き餃子と小籠包の違いは何ですか？"),
        ("Potstickers are pan-fried, while xiaolongbao are filled with hot broth inside.", "焼き餃子は鍋で焼きますが、小籠包は中に熱いスープが入っています。"),
        ("Be careful — the soup inside xiaolongbao is very hot.", "気をつけて、小籠包の中のスープはとても熱いです。"),
        ("We usually go for dim sum brunch on Sunday mornings.", "私たちは日曜の朝によく飲茶ブランチに行きます。"),
        ("Could I get a pot of jasmine tea with that?", "それにジャスミン茶も一つお願いできますか？"),
        ("The chef tossed the noodles quickly in a smoking hot wok.", "シェフは煙が出るほど熱い中華鍋で麺を手早く炒めました。"),
        ("That smoky flavor from the wok is called wok hei.", "あの中華鍋から出る香ばしい風味は「鍋気（ウォクヘイ）」と呼ばれます。"),
        ("Is this dish very spicy, or can you make it milder?", "この料理はかなり辛いですか、それとももう少しマイルドにできますか？"),
        ("Could you go easy on the chili oil, please?", "ラー油は控えめにしていただけますか？"),
        ("This sauce is a bit too pungent for me.", "このソースは私には少し香りが強すぎます。"),
        ("Peking duck is traditionally wrapped in a thin pancake with hoisin sauce.", "北京ダックは伝統的に薄いパンケーキにホイシンソースを添えて包みます。"),
        ("I've never tried a century egg before — what does it taste like?", "ピータンは食べたことがないのですが、どんな味ですか？"),
        ("It has a creamy yolk and a somewhat pungent smell.", "とろりとした黄身で、少し香りの強い匂いがあります。"),
        ("Chinese tea culture goes hand in hand with a good meal.", "中国の茶文化はおいしい食事と切っても切れない関係です。"),
    ],
    "タイ料理": [
        ("How spicy is this curry?", "このカレーはどのくらい辛いですか？"),
        ("Could you make it mild? I can't handle spicy food very well.", "マイルドにしていただけますか？辛い物があまり得意ではないので。"),
        ("What spice level would you like — mild, medium, or Thai spicy?", "辛さのレベルはどれにしますか？マイルド、ミディアム、それともタイ基準の激辛？"),
        ("I'll go with medium spicy, please.", "中辛でお願いします。"),
        ("Trust me, Thai spicy is much hotter than you'd expect.", "本当に、タイ基準の激辛は思っている以上に辛いですよ。"),
        ("Tom yum is a hot and sour soup made with lemongrass and lime leaves.", "トムヤムはレモングラスとこぶみかんの葉を使った酸辛スープです。"),
        ("What's the difference between green curry and red curry?", "グリーンカレーとレッドカレーの違いは何ですか？"),
        ("Green curry uses fresh green chilies, while red curry uses dried red ones.", "グリーンカレーは生の青唐辛子を使い、レッドカレーは乾燥した赤唐辛子を使います。"),
        ("Som tam is a spicy salad made from shredded green papaya.", "ソムタムは千切りの青パパイヤを使った辛いサラダです。"),
        ("It's pounded together with chilies, lime juice, and fish sauce in a mortar and pestle.", "唐辛子、ライム果汁、ナンプラーと一緒に乳鉢とすりこぎで叩いて作ります。"),
        ("Could I get sticky rice instead of steamed rice?", "白米の代わりにもち米にしていただけますか？"),
        ("Mango sticky rice is the perfect way to end a Thai meal.", "マンゴーともち米のデザートはタイ料理の食事を締めくくるのにぴったりです。"),
        ("I'm allergic to peanuts, so could you leave the peanut sauce out?", "ピーナッツアレルギーがあるので、ピーナッツソースは抜いていただけますか？"),
        ("Does this dish contain shrimp paste or fish sauce?", "この料理にはエビペーストやナンプラーが入っていますか？"),
        ("I have a shellfish allergy — is that safe for me to eat?", "甲殻類アレルギーがあるのですが、これは食べても大丈夫ですか？"),
        ("Thai cuisine is all about balancing sweet, sour, salty, and spicy flavors.", "タイ料理は甘味、酸味、塩味、辛味のバランスがすべてです。"),
        ("This curry paste is made fresh every morning.", "このカレーペーストは毎朝作りたてです。"),
        ("The best pad thai I've had was from a street food stall in Bangkok.", "今まで食べた中で一番おいしいパッタイは、バンコクの屋台の店のものでした。"),
        ("Let's check out the night market — the food there is amazing.", "ナイトマーケットを見に行きましょう、あそこの食べ物は最高です。"),
        ("Satay is grilled meat on skewers, usually served with a peanut dipping sauce.", "サテは串焼きの肉で、たいていピーナッツソースが添えられます。"),
        ("Could we get a Thai iced tea and a mango sticky rice for dessert?", "タイティーとマンゴーともち米のデザートをお願いできますか？"),
        ("This restaurant is famous for how authentic its curries taste.", "このお店はカレーを本場の味そのままに作ることで有名です。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 和食 (Japanese cuisine) ---
    ("washoku", "和食（日本の伝統的な料理）", "名詞", "Washoku was added to UNESCO's Intangible Cultural Heritage list in 2013.", "料理", "800"),
    ("kaiseki", "懐石料理（多皿からなる会席料理）", "名詞", "Kaiseki is a traditional multi-course Japanese meal.", "料理", "850"),
    ("izakaya", "居酒屋", "名詞", "Let's grab some small dishes at an izakaya.", "料理", "600"),
    ("onigiri", "おにぎり", "名詞", "She wrapped the onigiri in a sheet of nori.", "料理", "500"),
    ("natto", "納豆（発酵させた大豆）", "名詞", "Natto has a sticky texture that surprises many foreigners.", "料理", "600"),
    ("tsukemono", "漬物", "名詞", "Tsukemono are served as a side dish with rice.", "料理", "700"),
    ("dashi", "だし（和食の出汁）", "名詞", "Dashi is made from kombu and dried bonito flakes.", "料理", "650"),
    ("umami", "うま味（第五の味覚）", "名詞", "Umami is considered the fifth basic taste, alongside sweet and sour.", "料理", "750"),
    ("wagyu", "和牛", "名詞", "Wagyu is famous for its fine marbling.", "料理", "700"),
    ("unagi", "うなぎの蒲焼き", "名詞", "Unagi is brushed with a sweet soy glaze and grilled.", "料理", "650"),
    ("katsu", "カツ（パン粉をつけて揚げた料理）", "名詞", "Katsu curry combines a fried cutlet with Japanese curry sauce.", "料理", "550"),
    ("tonkatsu", "とんかつ", "名詞", "Tonkatsu is a breaded, deep-fried pork cutlet.", "料理", "550"),
    ("gyudon", "牛丼", "名詞", "Gyudon is thinly sliced beef simmered with onions over rice.", "料理", "600"),
    ("oden", "おでん", "名詞", "Oden is a comforting winter dish of ingredients simmered in broth.", "料理", "700"),
    ("chawanmushi", "茶碗蒸し", "名詞", "Chawanmushi is a savory steamed egg custard.", "料理", "800"),
    ("mochi", "餅", "名詞", "Mochi is made by pounding steamed sticky rice.", "料理", "500"),
    ("dorayaki", "どら焼き", "名詞", "Dorayaki has sweet red bean paste sandwiched between two pancakes.", "料理", "700"),
    ("matcha", "抹茶", "名詞", "Matcha is whisked with hot water in the tea ceremony.", "料理", "500"),
    ("sake", "日本酒", "名詞", "Sake can be served warm, at room temperature, or chilled.", "料理", "500"),
    ("shabu-shabu", "しゃぶしゃぶ", "名詞", "Shabu-shabu is thinly sliced meat swished through hot broth.", "料理", "750"),
    ("sukiyaki", "すき焼き", "名詞", "Sukiyaki simmers beef, vegetables, and tofu in a sweet soy sauce.", "料理", "700"),
    ("bento", "弁当", "名詞", "She packs a colorful bento for her kids every morning.", "料理", "500"),
    ("nigiri", "握り寿司", "名詞", "Nigiri is a hand-formed mound of rice topped with a slice of fish.", "料理", "650"),
    ("vinegared rice", "酢飯", "名詞句", "Sushi rice is vinegared rice seasoned with sugar and salt.", "料理", "750"),
    ("soy sauce", "醤油", "名詞句", "Dip the sushi lightly in soy sauce.", "料理", "400"),
    ("wasabi", "わさび", "名詞", "A little wasabi adds a sharp kick to sushi.", "料理", "500"),
    ("pickled ginger", "ガリ（甘酢生姜）", "名詞句", "Pickled ginger cleanses your palate between different pieces of sushi.", "料理", "650"),
    ("marbling", "霜降り（脂肪の入り方）", "名詞", "Wagyu beef is prized for its fine marbling.", "料理", "800"),
    ("tare", "タレ（甘辛い和風のたれ）", "名詞", "Unagi is brushed with a sweet tare sauce before grilling.", "料理", "750"),
    ("hand roll", "手巻き寿司", "名詞句", "A hand roll is a cone-shaped piece of sushi wrapped in nori.", "料理", "700"),
    ("fermented", "発酵させた", "形容詞", "Natto and miso are both fermented soybean products.", "料理", "650"),
    ("seasonal ingredients", "旬の食材", "名詞句", "Japanese chefs build their menus around seasonal ingredients.", "料理", "700"),
    ("delicate", "繊細な・上品な", "形容詞", "Japanese cuisine is prized for its delicate flavors.", "料理", "600"),
    ("raw fish", "生魚", "名詞句", "Sashimi is thinly sliced raw fish served without rice.", "料理", "500"),
    ("chopsticks", "箸", "名詞", "Could you show me the right way to hold chopsticks?", "料理", "400"),
    ("skewer", "串", "名詞", "Yakitori is chicken grilled on a bamboo skewer.", "料理", "550"),
    ("tatami seating", "座敷（畳の席）", "名詞句", "We booked a private room with tatami seating.", "料理", "800"),
    ("set meal", "定食", "名詞句", "The lunch set meal comes with rice, soup, and pickles.", "料理", "600"),
    ("counter seat", "カウンター席", "名詞句", "Sitting at the counter seat lets you watch the chef work.", "料理", "700"),
    ("slurp", "（麺を）ずるずるすする", "動詞", "It's considered polite to slurp your noodles in Japan.", "料理", "700"),
    ("staple food", "主食", "名詞句", "Rice is the staple food of Japan.", "料理", "650"),
    ("side dish", "副菜・おかず", "名詞句", "Tsukemono is often served as a side dish.", "料理", "500"),
    ("broth-based", "だしベースの", "形容詞", "Ramen is a broth-based noodle dish, unlike stir-fried noodles.", "料理", "750"),
    ("hearty", "食べ応えのある・滋味深い", "形容詞", "Oden is a hearty dish that warms you up in winter.", "料理", "650"),

    # --- 中華料理 (Chinese cuisine) ---
    ("Sichuan cuisine", "四川料理", "名詞句", "Sichuan cuisine is famous for its bold, spicy flavors.", "料理", "750"),
    ("Cantonese cuisine", "広東料理", "名詞句", "Cantonese cuisine tends to be milder and emphasizes fresh ingredients.", "料理", "800"),
    ("Hunan cuisine", "湖南料理", "名詞句", "Hunan cuisine can be even spicier than Sichuan food.", "料理", "900"),
    ("mala", "麻辣（痺れる辛さ）", "名詞", "Mala refers to the numbing, spicy flavor typical of Sichuan food.", "料理", "900"),
    ("numbing", "痺れるような", "形容詞", "Sichuan peppercorns give the dish a numbing sensation.", "料理", "850"),
    ("Sichuan peppercorn", "花椒（ホアジャオ）", "名詞句", "Sichuan peppercorns are what make the dish numbingly spicy.", "料理", "900"),
    ("wok", "中華鍋", "名詞", "The chef tossed the vegetables in a hot wok.", "料理", "600"),
    ("steamer basket", "蒸籠（せいろ）", "名詞句", "Dim sum is often served straight from a bamboo steamer basket.", "料理", "700"),
    ("char siu", "チャーシュー（叉焼）", "名詞", "Char siu is roasted pork glazed with a sweet marinade.", "料理", "700"),
    ("hot and sour soup", "サンラータン（酸辣湯）", "名詞句", "Hot and sour soup balances vinegar and pepper.", "料理", "600"),
    ("potsticker", "焼き餃子", "名詞", "Potstickers are pan-fried on one side and steamed on the other.", "料理", "650"),
    ("xiaolongbao", "小籠包", "名詞", "Xiaolongbao are soup dumplings filled with hot broth.", "料理", "900"),
    ("dim sum brunch", "飲茶ブランチ", "名詞句", "We went for a dim sum brunch with rolling carts of small dishes.", "料理", "750"),
    ("lazy Susan", "回転テーブル（レイジー・スーザン）", "名詞句", "The dishes were placed on a lazy Susan so everyone could share.", "料理", "800"),
    ("family-style dining", "大皿を分け合う食事スタイル", "名詞句", "Chinese meals are usually served family-style, with shared dishes in the middle.", "料理", "800"),
    ("shared dish", "取り分ける料理", "名詞句", "Order a few shared dishes for the table.", "料理", "600"),
    ("clay pot", "土鍋", "名詞句", "The rice was cooked in a clay pot and had a crispy bottom.", "料理", "700"),
    ("century egg", "ピータン（皮蛋）", "名詞句", "A century egg has a dark, jelly-like white and a creamy yolk.", "料理", "850"),
    ("tofu skin", "湯葉（豆腐皮）", "名詞句", "Tofu skin is a thin layer that forms when soy milk is heated.", "料理", "800"),
    ("black bean sauce", "豆豉醤（トウチジャン）", "名詞句", "The beef was cooked in a rich black bean sauce.", "料理", "750"),
    ("oyster sauce", "オイスターソース", "名詞句", "Oyster sauce adds a savory depth to the vegetables.", "料理", "650"),
    ("hoisin sauce", "ホイシンソース", "名詞句", "Hoisin sauce is brushed onto the Peking duck pancakes.", "料理", "750"),
    ("five-spice powder", "五香粉", "名詞句", "Five-spice powder gives the pork its distinctive aroma.", "料理", "800"),
    ("scallion pancake", "葱油餅（ネギ入り中華パンケーキ）", "名詞句", "A scallion pancake is crispy on the outside and flaky inside.", "料理", "750"),
    ("tea culture", "茶文化", "名詞句", "Tea culture is deeply woven into Chinese dining traditions.", "料理", "700"),
    ("jasmine tea", "ジャスミン茶", "名詞句", "Jasmine tea is commonly served with dim sum.", "料理", "500"),
    ("wok hei", "鍋気（強火で炒めた際の香ばしさ）", "名詞句", "Wok hei is the smoky aroma that comes from cooking over intense heat.", "料理", "950"),
    ("deep-fried noodles", "揚げ麺", "名詞句", "The dish was topped with a handful of deep-fried noodles.", "料理", "700"),
    ("sweet bean paste", "あんこ（甘い豆あん）", "名詞句", "The bun was filled with sweet bean paste.", "料理", "650"),
    ("steam bun", "中華まん", "名詞句", "A steam bun is soft, fluffy, and often filled with pork.", "料理", "600"),
    ("noodle soup", "麺料理（スープ入り）", "名詞句", "The noodle soup was rich with pork bone broth.", "料理", "500"),
    ("cleaver", "中華包丁（大型の万能包丁）", "名詞", "The chef diced the vegetables with a heavy cleaver.", "料理", "650"),
    ("spatula", "中華べら（炒め用のへら）", "名詞", "The chef flipped the vegetables with a metal spatula.", "料理", "600"),
    ("round table", "円卓", "名詞句", "Big family dinners are held around a large round table.", "料理", "550"),
    ("pungent", "香りや匂いが強い・刺激的な", "形容詞", "Fermented tofu has a famously pungent smell.", "料理", "800"),
    ("fiery", "ひりひり辛い", "形容詞", "The Sichuan hot pot broth was fiery red with chili oil.", "料理", "750"),
    ("tangy", "酸味のある", "形容詞", "The hot and sour soup has a tangy kick.", "料理", "650"),
    ("savory", "塩気があって旨みのある", "形容詞", "The char siu was sweet and savory at the same time.", "料理", "600"),
    ("flash-fry", "強火でさっと炒める", "動詞", "The chef flash-fries the vegetables to keep them crisp.", "料理", "750"),
    ("street vendor", "屋台の売り子", "名詞句", "A street vendor was flipping scallion pancakes right on the sidewalk.", "料理", "650"),
    ("condiment", "調味料・薬味", "名詞", "Chili oil is a popular condiment at Chinese restaurants.", "料理", "700"),
    ("chili oil", "ラー油", "名詞句", "A drizzle of chili oil brings out the flavor of the dumplings.", "料理", "550"),
    ("bok choy", "チンゲンサイ・青梗菜", "名詞句", "The stir-fry included baby bok choy and garlic.", "料理", "600"),

    # --- タイ料理 (Thai cuisine) ---
    ("tom yum", "トムヤム（酸辛スープ）", "名詞句", "Tom yum is a hot and sour Thai soup made with lemongrass.", "料理", "650"),
    ("green curry", "グリーンカレー", "名詞句", "Green curry gets its color from fresh green chilies.", "料理", "600"),
    ("red curry", "レッドカレー", "名詞句", "Red curry looks milder in color but is often just as spicy.", "料理", "600"),
    ("massaman curry", "マッサマンカレー", "名詞句", "Massaman curry has Persian roots and a milder, nutty flavor.", "料理", "800"),
    ("som tam", "ソムタム（青パパイヤサラダ）", "名詞句", "Som tam is a spicy shredded green papaya salad.", "料理", "800"),
    ("papaya salad", "パパイヤサラダ", "名詞句", "The papaya salad was pounded fresh in a mortar and pestle.", "料理", "700"),
    ("sticky rice", "もち米（カオニャオ）", "名詞句", "Sticky rice is eaten by hand with many Thai dishes.", "料理", "600"),
    ("mango sticky rice", "マンゴーともち米のデザート", "名詞句", "Mango sticky rice is a popular Thai dessert made with coconut milk.", "料理", "650"),
    ("satay", "サテ（串焼き肉）", "名詞", "Satay is grilled meat on skewers served with peanut sauce.", "料理", "650"),
    ("peanut sauce", "ピーナッツソース", "名詞句", "Satay is dipped in a rich peanut sauce.", "料理", "550"),
    ("fish sauce", "ナンプラー（魚醤）", "名詞句", "Fish sauce is the salty backbone of Thai cooking.", "料理", "600"),
    ("tamarind", "タマリンド", "名詞", "Tamarind gives pad thai its tangy sweetness.", "料理", "750"),
    ("galangal", "ガランガル（タイしょうが）", "名詞", "Galangal looks like ginger but has a sharper, piney taste.", "料理", "900"),
    ("Thai basil", "タイバジル", "名詞句", "Thai basil has a spicier, more anise-like flavor than sweet basil.", "料理", "750"),
    ("kaffir lime leaf", "こぶみかんの葉", "名詞句", "A kaffir lime leaf adds a floral, citrusy note to the curry.", "料理", "900"),
    ("coconut milk", "ココナッツミルク", "名詞句", "Coconut milk mellows out the spiciness of Thai curries.", "料理", "500"),
    ("spice level", "辛さのレベル", "名詞句", "What spice level would you like — mild, medium, or Thai spicy?", "料理", "600"),
    ("Thai spicy", "タイ基準の激辛", "名詞句", "Thai spicy is much hotter than what most tourists expect.", "料理", "700"),
    ("mild", "辛さ控えめの", "形容詞", "Could you make it mild? I can't handle spicy food.", "料理", "400"),
    ("medium spicy", "中辛の", "形容詞句", "I'll go with medium spicy, please.", "料理", "450"),
    ("street food", "屋台料理", "名詞句", "Bangkok is famous for its vibrant street food scene.", "料理", "600"),
    ("street food stall", "屋台の店", "名詞句", "The best pad thai I ever had was from a street food stall.", "料理", "650"),
    ("night market", "ナイトマーケット", "名詞句", "The night market was full of food carts and grilled skewers.", "料理", "600"),
    ("mortar and pestle", "乳鉢とすりこぎ", "名詞句", "Som tam is pounded together in a mortar and pestle.", "料理", "800"),
    ("pad see ew", "パッシーユー（醤油炒め麺）", "名詞句", "Pad see ew is stir-fried flat noodles in a sweet soy sauce.", "料理", "800"),
    ("drunken noodles", "パッキーマオ（酔っ払い炒め麺）", "名詞句", "Drunken noodles are spicy stir-fried noodles with Thai basil.", "料理", "850"),
    ("Thai iced tea", "タイティー", "名詞句", "Thai iced tea is bright orange and very sweet.", "料理", "600"),
    ("sour", "酸味のある", "形容詞", "Tom yum balances sour, spicy, salty, and sweet flavors.", "料理", "400"),
    ("fragrant", "香り高い", "形容詞", "The curry was fragrant with galangal and kaffir lime leaves.", "料理", "600"),
    ("spicy tolerance", "辛さへの耐性", "名詞句", "My spicy tolerance isn't very high, so please go easy on the chilies.", "料理", "700"),
    ("chili paste", "チリペースト（唐辛子ペースト）", "名詞句", "The curry paste starts with a base of chili paste.", "料理", "650"),
    ("curry paste", "カレーペースト", "名詞句", "Green curry paste is made by grinding chilies, herbs, and spices together.", "料理", "700"),
    ("allergen", "アレルゲン", "名詞", "Please let the kitchen know about any allergens before you order.", "料理", "700"),
    ("shellfish", "甲殻類・貝類", "名詞", "I have a shellfish allergy, so no shrimp paste, please.", "料理", "550"),
    ("shrimp paste", "エビペースト（カピ）", "名詞句", "Shrimp paste adds a deep umami flavor to Thai curries.", "料理", "800"),
    ("peanut allergy", "ピーナッツアレルギー", "名詞句", "He has a peanut allergy, so he avoids satay.", "料理", "550"),
    ("banana leaf", "バナナの葉", "名詞句", "The dish was steamed and served in a banana leaf.", "料理", "700"),
    ("bamboo skewer", "竹串", "名詞句", "The satay is grilled on bamboo skewers over charcoal.", "料理", "650"),
    ("condensed milk", "コンデンスミルク", "名詞句", "Thai iced tea is topped with condensed milk.", "料理", "550"),
    ("signature dish", "看板料理・名物料理", "名詞句", "Tom yum kung is the restaurant's signature dish.", "料理", "700"),
    ("balance of flavors", "味のバランス", "名詞句", "Thai cuisine is known for its balance of flavors — sweet, sour, salty, and spicy.", "料理", "750"),
    ("Thai chili", "プリッキーヌ（タイの激辛唐辛子）", "名詞句", "Just one Thai chili can make a dish incredibly hot.", "料理", "850"),
    ("khao soi", "カオソーイ（北タイのカレー麺）", "名詞", "Khao soi is a Northern Thai curry noodle soup topped with crispy fried noodles.", "料理", "900"),
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
