# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated words & phrases for INDIAN / VIETNAMESE / SPANISH cuisine
vocabulary, authored by Claude.

Focus (料理ドメインの深掘り): `料理` ドメインには既に curry, dal, naan, chapati,
samosa, biryani, tandoori, masala, lassi, paneer, chai（インド）、pho,
spring roll（ベトナム）、paella, tapas, gazpacho, sangria, jamon, churros
（スペイン）が入っているため、それらは再投入せず、その先の語彙を拡充する:

- インド料理: 地域差（北インド＝小麦中心／南インド＝米中心）、追加の代表料理
  （butter chicken, tikka masala, dosa, idli, vindaloo, korma, saag, raita,
  ghee, papadum, thali, gulab jamun など）、スパイス語彙（turmeric, cumin,
  coriander, cardamom, garam masala など）、辛さ・食文化語彙（手で食べる、
  ナンで具をすくう、料理をシェアする、など）。
- ベトナム料理: banh mi, 魚醤（fish sauce / nuoc mam）, bun cha, banh xeo,
  生春巻き(goi cuon)と揚げ春巻き(cha gio)の区別, ベトナムコーヒー
  (ca phe sua da), rice paper, ハーブの盛り合わせ, スープ語彙。
- スペイン料理: jamón ibérico（無印の jamon との違い）, croquetas,
  patatas bravas, salmorejo（gazpacho との違い）, tortilla española
  （※メキシコの tortilla との「空似（false friend）」を明示的に指摘）,
  pintxos, sherry, オリーブオイル文化, シエスタ・遅い夕食などの食事時間文化,
  タパス式のシェアダイニング作法。

各料理につき「注文する／辛さ・材料・アレルギーを尋ねる／料理を説明する／
食文化を語る」という自然なフレーズも収録した。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased), both
against pre-existing rows and against words already added by sibling scripts
running in the same content batch.

Run:  python scripts/add_food_india_vietnam_spain.py
      python scripts/add_food_india_vietnam_spain.py --missing-words   # report only

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
    "インド料理を英語で語る": [
        # --- 注文する ---
        ("I'll have the butter chicken with garlic naan, please.", "バターチキンとガーリックナンをお願いします。"),
        ("Could we get a vegetarian thali for the table?", "テーブル用にベジタリアンのターリーをお願いできますか？"),
        ("Could we get some extra papadums while we wait?", "待っている間にパパドをいくつか追加でもらえますか？"),
        ("Could you recommend something not too spicy for a beginner?", "辛いのが苦手な初心者向けに何かおすすめはありますか？"),
        # --- 辛さ・材料・アレルギーを尋ねる ---
        ("How spicy is the vindaloo?", "ヴィンダルーはどのくらい辛いですか？"),
        ("Could you make it mild, please?", "辛さを控えめにしていただけますか？"),
        ("I'd like mine without too much chili.", "チリを控えめでお願いします。"),
        ("What's in this curry?", "このカレーには何が入っていますか？"),
        ("Does this contain dairy?", "これには乳製品が入っていますか？〔アレルギー確認〕"),
        ("I'm allergic to nuts — is there any cashew in this?", "ナッツアレルギーがあります。カシューは入っていますか？"),
        # --- 料理を説明する ---
        ("This curry has a nice, warming heat to it.", "このカレーはじんわり温まるような辛さですね。"),
        ("This dosa is fermented overnight before it's cooked.", "このドーサは一晩発酵させてから焼きます。"),
        ("A little raita on the side really cools things down.", "ライタを添えると辛さが和らぎます。"),
        ("Chai here is brewed strong with milk and spices.", "ここのチャイはミルクとスパイスでしっかり煮出してあります。"),
        ("The tandoor gives the naan its smoky, blistered crust.", "タンドールのおかげでナンに香ばしい焦げ目がつきます。"),
        ("North Indian food tends to be wheat-based, while South Indian food is more rice-based.", "北インド料理は小麦中心、南インド料理は米中心の傾向があります。"),
        # --- 食文化を語る ---
        ("It's customary to eat with your right hand in many parts of India.", "インドの多くの地域では右手で食事をするのが習わしです。"),
        ("We tear off a piece of naan and use it to scoop up the curry.", "ナンをちぎって、それでカレーをすくって食べます。"),
        ("Curries are usually shared, so we order a few dishes for the table.", "カレーは大抵シェアするので、テーブル用に数皿頼みます。"),
        ("A dabbawala can deliver a home-cooked lunch across the whole city.", "ダッバーワーラーは街中どこへでも家庭料理の弁当を配達してくれます。"),
    ],
    "ベトナム料理を英語で語る": [
        # --- 注文する ---
        ("I'll have the goi cuon, not the fried ones.", "揚げていない生春巻き（ゴイクン）をお願いします。"),
        ("I'll take a banh mi with pate and pickled vegetables.", "パテと漬け野菜入りのバインミーをお願いします。"),
        ("Could I get ca phe sua da, please?", "カフェ・スア・ダー（練乳入りアイスコーヒー）をお願いします。"),
        ("Could we share a few dishes instead of ordering separately?", "それぞれ別々に頼むより、何品かシェアしませんか？"),
        # --- 辛さ・材料・アレルギーを尋ねる ---
        ("Could I get extra herbs on the side?", "ハーブを別皿で追加でもらえますか？"),
        ("Is the broth made with fish sauce?", "このスープはナンプラー（魚醤）ベースですか？"),
        ("I'm vegetarian — is there a broth without fish sauce?", "ベジタリアンなのですが、魚醤を使わないスープはありますか？"),
        ("Could you go easy on the chili?", "チリは控えめにしていただけますか？"),
        ("Are there any peanuts in this? I have a peanut allergy.", "これにピーナッツは入っていますか？ピーナッツアレルギーがあるので。"),
        ("What's inside a banh mi?", "バインミーには何が入っていますか？"),
        # --- 料理を説明する ---
        ("What's the difference between fresh and fried spring rolls?", "生春巻きと揚げ春巻きの違いは何ですか？"),
        ("The dipping sauce is a mix of fish sauce, lime, sugar, and chili.", "つけダレは魚醤・ライム・砂糖・チリを混ぜたものです。"),
        ("Rice paper wrappers need just a quick dip in water.", "ライスペーパーはさっと水にくぐらせるだけで使えます。"),
        ("Star anise and cinnamon give the broth its deep aroma.", "スターアニスとシナモンがスープに深い香りを与えます。"),
        ("Vietnamese coffee is much stronger than regular drip coffee.", "ベトナムコーヒーは普通のドリップコーヒーよりかなり濃いです。"),
        # --- 食文化を語る ---
        ("How do I eat pho properly?", "フォーはどうやって食べるのが正式ですか？"),
        ("You add the herbs, bean sprouts, and lime right before eating.", "食べる直前にハーブ、もやし、ライムを加えます。"),
        ("It's totally fine to slurp your noodles here.", "ここでは麺をすすって食べても全く問題ありません。"),
        ("This dish is served with a plate of fresh herbs on the side.", "この料理には新鮮なハーブの盛り合わせが添えられます。"),
        ("Street food stalls are often the best place to try local specialties.", "屋台こそ地元の名物を味わうのに一番の場所であることが多いです。"),
    ],
    "スペイン料理を英語で語る": [
        # --- 注文する ---
        ("Could we order a few tapas to share?", "シェアできるタパスをいくつか頼みましょうか？"),
        ("What would you recommend for the table?", "テーブル用に何がおすすめですか？"),
        ("Could we get the jamón ibérico, if it's not too expensive?", "高すぎなければハモン・イベリコをお願いできますか？"),
        ("Could I have a glass of sherry to start?", "食前にシェリー酒を一杯いただけますか？"),
        # --- 辛さ・材料・アレルギーを尋ねる ---
        ("Are the croquetas vegetarian?", "クロケッタはベジタリアン向けですか？"),
        ("Is there any shellfish in the patatas bravas sauce?", "パタタス・ブラバスのソースに甲殻類は入っていますか？"),
        ("Could you tell me what's in this pintxo?", "このピンチョスには何が入っているか教えていただけますか？"),
        ("Is the tortilla española made with potatoes?", "トルティーヤ・エスパニョーラはじゃがいも入りですか？"),
        # --- 料理を説明する ---
        ("Don't confuse this with a Mexican tortilla — it's a potato omelette.", "メキシコのトルティーヤと混同しないでください、これはじゃがいものオムレツです。"),
        ("This ham comes from acorn-fed pigs, which makes it especially prized.", "このハムはどんぐりを食べて育った豚のもので、特に珍重されています。"),
        ("What's the difference between gazpacho and salmorejo?", "ガスパチョとサルモレホの違いは何ですか？"),
        ("Salmorejo is thicker and often topped with ham and egg.", "サルモレホの方が濃厚で、ハムや卵をのせて出されることが多いです。"),
        ("A good olive oil really makes a difference here.", "良質なオリーブオイルがあるかどうかで味がかなり変わります。"),
        ("Could you drizzle a little more olive oil on the bread?", "パンにもう少しオリーブオイルをかけていただけますか？"),
        ("This Rioja pairs really well with grilled meat.", "このリオハは炭火焼きの肉料理とよく合います。"),
        # --- 食文化を語る ---
        ("Dinner here doesn't really start until nine or ten at night.", "こちらでは夕食は夜9時か10時にならないと本格的に始まりません。"),
        ("Many shops close in the early afternoon for a siesta.", "多くの店は午後の早い時間、シエスタのために閉まります。"),
        ("We like to linger at the table and chat after the meal.", "食後もテーブルに残っておしゃべりするのが好きなんです。"),
        ("At a pintxos bar, you just help yourself and they count your toothpicks at the end.", "ピンチョスのバーでは自由に取って、最後に楊枝の本数で会計します。"),
        ("We ended up bar-hopping around the old town all evening.", "結局、夜通し旧市街のバーを飲み歩くことになりました。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # ===== インド料理 =====
    ("butter chicken", "バターチキン（クリーミーでマイルドなトマトベースのカレー）", "名詞", "Butter chicken is creamy, mildly spiced, and popular even outside India.", "料理", "500"),
    ("tikka masala", "ティッカマサラ（英国生まれとも言われる“インド風”カレー）", "名詞", "Chicken tikka masala is often called Britain's favorite curry.", "料理", "500"),
    ("dosa", "ドーサ（発酵させた米と豆の生地で作るパリパリのクレープ状の南インド料理）", "名詞", "A dosa is a crispy, fermented rice-and-lentil crepe from South India.", "料理", "650"),
    ("idli", "イドゥリ（蒸した米と豆の蒸しケーキ、南インドの定番朝食）", "名詞", "Idli are soft steamed rice cakes usually served with chutney.", "料理", "750"),
    ("vindaloo", "ヴィンダルー（ゴア地方発祥の非常に辛いカレー）", "名詞", "Vindaloo is a fiery curry from Goa, known for its intense heat.", "料理", "750"),
    ("korma", "コルマ（マイルドでクリーミーなカレー）", "名詞", "Korma is a mild, creamy curry, a good choice if you don't like spice.", "料理", "650"),
    ("saag", "サーグ（スパイスを効かせたほうれん草料理）", "名詞", "Saag is a spiced spinach dish, often served with paneer or meat.", "料理", "750"),
    ("raita", "ライタ（ヨーグルトベースの箸休め・辛さを和らげる副菜）", "名詞", "Raita is a cooling yogurt side dish that tames the heat of a curry.", "料理", "700"),
    ("ghee", "ギー（インド料理で使う澄ましバター）", "名詞", "Ghee is clarified butter, prized for its rich, nutty flavor.", "料理", "600"),
    ("papadum", "パパド（豆粉で作るパリパリの薄焼きウエハース）", "名詞", "Papadums are crispy lentil wafers often served as a starter.", "料理", "800"),
    ("thali", "ターリー（複数の小皿が並ぶ定食風の一皿）", "名詞", "A thali is a platter with small servings of several different dishes.", "料理", "750"),
    ("gulab jamun", "グラブジャムン（シロップに浸したミルク団子のデザート）", "名詞", "Gulab jamun is a soft milk dumpling soaked in rose-scented syrup.", "料理", "800"),
    ("tandoor", "タンドール（粘土製の壺形オーブン）", "名詞", "Naan is traditionally baked against the wall of a clay tandoor.", "料理", "700"),
    ("roti", "ロティ（全粒粉で作るシンプルな無発酵の丸いパン）", "名詞", "Roti is a simple, unleavened whole-wheat flatbread.", "料理", "650"),
    ("paratha", "パラータ（層になったバター風味の平パン）", "名詞", "Paratha is a flaky, layered flatbread often stuffed with vegetables.", "料理", "800"),
    ("chutney", "チャツネ（果物や野菜で作る甘辛い添えソース）", "名詞", "Mango chutney adds a sweet, tangy contrast to savory snacks.", "料理", "650"),
    ("turmeric", "ターメリック・ウコン（カレーに黄色をつける香辛料）", "名詞", "Turmeric gives curry its deep yellow color and earthy flavor.", "料理", "500"),
    ("cumin", "クミン（土っぽい香りの香辛料）", "名詞", "Cumin seeds are often toasted first to bring out their aroma.", "料理", "550"),
    ("coriander", "コリアンダー（種子のスパイス。葉の部分は米語で cilantro と呼ぶ）", "名詞", "Coriander seeds taste quite different from the fresh cilantro leaves.", "料理", "600"),
    ("cardamom", "カルダモン（香り高いスパイス。チャイにもよく使う）", "名詞", "Cardamom pods add a sweet, floral note to a cup of chai.", "料理", "650"),
    ("garam masala", "ガラムマサラ（数種のスパイスを合わせた合わせ調味料）", "名詞", "Garam masala is a warming spice blend added near the end of cooking.", "料理", "700"),
    ("fenugreek", "フェヌグリーク（ほろ苦い香りのスパイス）", "名詞", "Fenugreek leaves add a slightly bitter, distinctive aroma to the sauce.", "料理", "850"),
    ("asafoetida", "アサフェティダ（強い香りの豆科植物由来のスパイス、通称ヒング）", "名詞", "A pinch of asafoetida replaces onion and garlic in some vegetarian dishes.", "料理", "950"),
    ("clove", "クローブ・丁子", "名詞", "Whole cloves are used to season the rice in a biryani.", "料理", "600"),
    ("cinnamon", "シナモン", "名詞", "Cinnamon sticks add warmth to both biryani and chai.", "料理", "500"),
    ("saffron", "サフラン（世界で最も高価なスパイスの一つ）", "名詞", "Saffron gives both an Indian biryani and a Spanish paella their golden color.", "料理", "700"),
    ("flatbread", "フラットブレッド（平たいパンの総称）", "名詞", "Naan and roti are both types of Indian flatbread.", "料理", "550"),
    ("lentil", "レンズ豆", "名詞", "Dal is a spiced stew made from lentils.", "料理", "550"),
    ("mild", "辛くない・マイルドな", "形容詞", "Korma is much milder than vindaloo.", "料理", "450"),
    ("fiery", "火のように辛い", "形容詞", "Vindaloo has a reputation for being fiery.", "料理", "700"),
    ("curry house", "カレー屋（英国で定着したインド料理店を指す言い方）", "名詞", "On Friday nights, many Brits head to their local curry house.", "料理", "800"),
    ("pilau", "ピラウ（スパイスで炊き込んだ米料理）", "名詞", "Vegetable pilau is a fragrant, gently spiced rice dish.", "料理", "750"),
    ("communal", "みんなで分け合う・共有の", "形容詞", "Indian meals are often a communal affair, with dishes shared at the table.", "料理", "750"),
    ("scoop", "すくう", "動詞", "People often scoop up curry with a piece of naan instead of using a fork.", "料理", "600"),
    ("finger bowl", "フィンガーボウル（食後に手を洗うための水を張った器）", "名詞", "A finger bowl is provided for washing your hands after eating with them.", "料理", "900"),
    ("tiffin", "ティフィン（重箱状の弁当箱、またはその中身）", "名詞", "A tiffin is a stacked lunchbox traditionally used to carry a home-cooked meal.", "料理", "900"),
    ("dabbawala", "ダッバーワーラー（インドの弁当配達人）", "名詞", "A dabbawala delivers thousands of home-cooked lunchboxes across Mumbai every day.", "料理", "990+"),
    ("basmati", "バスマティ（香り高い長粒種の米）", "名詞", "Basmati is a long-grain, fragrant rice from the Indian subcontinent.", "料理", "700"),
    ("staple", "主食・定番の食材", "名詞", "Rice and wheat are both staples of the Indian diet.", "料理", "650"),
    ("aromatic", "香り高い", "形容詞", "Basmati rice is prized for its aromatic, nutty fragrance.", "料理", "650"),
    ("pungent", "刺激臭のある・強烈な香りの", "形容詞", "Asafoetida has a surprisingly pungent smell before cooking mellows it.", "料理", "750"),
    ("digestive", "消化を助ける食べ物・消化剤", "名詞", "A small bowl of fennel seeds is offered as a digestive after the meal.", "料理", "850"),
    ("creamy", "クリーミーな・まろやかな", "形容詞", "Butter chicken owes its creamy texture to butter and cream.", "料理", "450"),
    ("earthy", "土っぽい・素朴な風味の", "形容詞", "Cumin has a warm, earthy flavor that defines many Indian dishes.", "料理", "700"),
    ("fermented", "発酵させた", "形容詞", "Dosa batter is fermented overnight, which gives it a slight tang.", "料理", "650"),
    # ===== ベトナム料理 =====
    ("banh mi", "バインミー（フランスパンのベトナム風サンドイッチ）", "名詞", "Banh mi is a Vietnamese baguette sandwich filled with meat, pickles, and herbs.", "料理", "550"),
    ("bun cha", "ブンチャー（炭火焼き豚と米麺、つけダレの一皿）", "名詞", "Bun cha is grilled pork served with rice noodles, herbs, and a tangy dipping sauce.", "料理", "800"),
    ("banh xeo", "バインセオ（ターメリック色の香ばしいベトナム風お好み焼き）", "名詞", "Banh xeo is a crispy, turmeric-yellow savory pancake folded around pork and bean sprouts.", "料理", "850"),
    ("goi cuon", "ゴイクン（生春巻き、揚げない米紙の巻き物）", "名詞", "Goi cuon are fresh, uncooked spring rolls wrapped in translucent rice paper.", "料理", "800"),
    ("cha gio", "チャーゾー（揚げ春巻き、goi cuon の揚げ版）", "名詞", "Cha gio are crispy fried spring rolls, the deep-fried counterpart to goi cuon.", "料理", "850"),
    ("rice paper", "ライスペーパー（米で作る半透明の薄い皮）", "名詞", "Rice paper wrappers turn soft and sticky after a quick dip in water.", "料理", "650"),
    ("fish sauce", "魚醤・ナンプラー（現地語で nuoc mam）", "名詞", "Fish sauce, called nuoc mam locally, is the salty backbone of Vietnamese cooking.", "料理", "600"),
    ("nuoc cham", "ヌクチャム（魚醤ベースの万能つけダレ）", "名詞", "Nuoc cham is a tangy dipping sauce made from fish sauce, lime, sugar, and chili.", "料理", "800"),
    ("star anise", "スターアニス・八角", "名詞", "Star anise gives pho broth its distinctive, warm aroma.", "料理", "750"),
    ("broth-based", "スープ（出汁）をベースにした", "形容詞", "Pho is a broth-based noodle soup, unlike stir-fried noodle dishes.", "料理", "600"),
    ("condensed milk", "練乳", "名詞", "Condensed milk sweetens Vietnamese iced coffee instead of sugar or cream.", "料理", "650"),
    ("ca phe sua da", "カフェ・スア・ダー（練乳入りベトナム風アイスコーヒー）", "名詞", "Ca phe sua da is strong drip coffee served over ice with condensed milk.", "料理", "850"),
    ("phin", "フィン（一滴ずつ抽出するベトナム式コーヒーフィルター）", "名詞", "A phin is a small metal filter that drips coffee slowly, one drop at a time.", "料理", "900"),
    ("vermicelli", "ビーフン・極細麺", "名詞", "Rice vermicelli is much thinner than the flat noodles used in pho.", "料理", "700"),
    ("hoisin sauce", "ホイシンソース（甘辛い中華風の合わせ調味料）", "名詞", "A dab of hoisin sauce adds sweetness to a bowl of pho.", "料理", "750"),
    ("sriracha", "スリラチャソース（辛口チリソース）", "名詞", "Sriracha is the go-to chili sauce for spicing up noodle soups.", "料理", "600"),
    ("bean sprout", "もやし", "名詞", "Fresh bean sprouts add crunch when stirred into hot pho broth.", "料理", "650"),
    ("clay pot", "土鍋", "名詞", "Ca kho to is fish braised slowly in a clay pot.", "料理", "750"),
    ("street food", "屋台料理", "名詞", "Vietnamese street food is famous for being fresh, light, and inexpensive.", "料理", "550"),
    ("herb platter", "ハーブの盛り合わせ", "名詞", "A herb platter of mint, basil, and cilantro is served alongside the noodles.", "料理", "700"),
    ("pickled", "酢漬けの・ピクルスにした", "形容詞", "Banh mi is topped with pickled carrots and daikon for a tangy crunch.", "料理", "600"),
    ("condiment", "薬味・調味料", "名詞", "Sriracha and hoisin sauce are common condiments for a bowl of pho.", "料理", "650"),
    ("tamarind", "タマリンド（酸味のある実、調味料に使う）", "名詞", "Tamarind adds a sour tang to some Vietnamese soups and sauces.", "料理", "750"),
    ("shrimp paste", "エビペースト（mam tom、独特の強い香り）", "名詞", "Shrimp paste has a pungent smell but adds deep umami flavor.", "料理", "900"),
    ("slurp", "音を立ててすする", "動詞", "Slurping your noodles is perfectly acceptable, even encouraged, when eating pho.", "料理", "600"),
    ("umami", "うま味", "名詞", "Fish sauce adds a deep umami note to almost every Vietnamese dish.", "料理", "700"),
    ("tangy", "ピリッと酸味のある", "形容詞", "Nuoc cham has a tangy balance of sour, sweet, salty, and spicy.", "料理", "650"),
    ("fragrant", "香りの良い", "形容詞", "A fragrant broth simmers for hours before it's ready to serve.", "料理", "600"),
    ("crispy", "パリパリの・カリッとした", "形容詞", "Cha gio are fried until the wrapper turns crispy and golden.", "料理", "450"),
    ("zesty", "爽やかで刺激的な風味の", "形容詞", "A squeeze of lime makes the dipping sauce taste even zestier.", "料理", "700"),
    # ===== スペイン料理 =====
    ("jamon iberico", "ハモン・イベリコ（どんぐりを食べて育った黒豚の高級生ハム）", "名詞", "Jamón ibérico, cured from acorn-fed black Iberian pigs, is prized above ordinary jamón.", "料理", "850"),
    ("croqueta", "クロケッタ（ベシャメルソース入りの揚げ物）", "名詞", "Croquetas are crisp fried fritters with a creamy bechamel filling.", "料理", "700"),
    ("patatas bravas", "パタタス・ブラバス（辛味ソースをかけた揚げじゃがいも）", "名詞", "Patatas bravas are fried potato chunks topped with a spicy tomato sauce.", "料理", "650"),
    ("salmorejo", "サルモレホ（gazpacho より濃厚な冷製トマトスープ）", "名詞", "Salmorejo is a thicker, creamier cousin of gazpacho, often topped with ham and egg.", "料理", "800"),
    ("tortilla espanola", "トルティーヤ・エスパニョーラ（じゃがいもと卵の厚焼きオムレツ）。※メキシコ料理の tortilla（生地の薄焼き）とは全くの別物なので要注意〔false friend〕", "名詞", "Tortilla española is a thick potato omelette, completely different from a Mexican tortilla.", "料理", "700"),
    ("pintxos", "ピンチョス（バスク風タパス、爪楊枝で留めることが多い）", "名詞", "Pintxos are Basque-style tapas, often held together with a toothpick.", "料理", "850"),
    ("sherry", "シェリー酒（ヘレス地方の酒精強化ワイン）", "名詞", "Sherry is a fortified wine from the Jerez region, ranging from bone-dry to sweet.", "料理", "750"),
    ("paprika", "パプリカ・パプリカ粉（スペイン産は燻製が有名）", "名詞", "Smoked paprika, or pimentón, gives Spanish sausages their deep red color.", "料理", "600"),
    ("extra-virgin", "エキストラバージンの（オリーブオイルの最高等級）", "形容詞", "Extra-virgin olive oil is the highest, least processed grade.", "料理", "750"),
    ("siesta", "シエスタ（午後の昼寝・休憩時間）", "名詞", "Many small shops still close for a siesta in the early afternoon.", "料理", "600"),
    ("sobremesa", "ソブレメサ（食後もテーブルに残っておしゃべりする時間）", "名詞", "Sobremesa is the unhurried conversation that lingers at the table after a meal.", "料理", "900"),
    ("small plates", "小皿料理（シェアを前提にした少量の一皿）", "名詞", "Tapas are traditionally served as small plates meant for sharing.", "料理", "600"),
    ("bar-hop", "はしご酒をする", "動詞", "Locals often bar-hop from one tapas bar to the next for a night out.", "料理", "800"),
    ("manchego", "マンチェゴ（ラ・マンチャ地方の羊乳チーズ）", "名詞", "Manchego is a firm, nutty sheep's-milk cheese from La Mancha.", "料理", "800"),
    ("rioja", "リオハ（テンプラニーリョ種で知られる赤ワイン産地）", "名詞", "Rioja is a red wine region famous for its tempranillo grapes.", "料理", "850"),
    ("tempranillo", "テンプラニーリョ（スペイン原産の黒ブドウ品種）", "名詞", "Tempranillo is the dark-skinned grape behind most Rioja wines.", "料理", "900"),
    ("cured", "塩漬け・熟成させた", "形容詞", "Cured meats like jamón are salted and air-dried rather than cooked.", "料理", "700"),
    ("cava", "カバ（スペイン産のスパークリングワイン）", "名詞", "Cava is Spain's sparkling wine, made using the same method as champagne.", "料理", "850"),
    ("vermouth", "ベルモット（香草を加えた酒精強化ワイン）", "名詞", "A glass of vermouth on tap is a classic pre-lunch aperitif in Spain.", "料理", "850"),
    ("aperitif", "食前酒", "名詞", "Locals often have an aperitif before the late Spanish dinner hour.", "料理", "800"),
    ("toothpick", "爪楊枝", "名詞", "At a pintxos bar, your bill is tallied by counting your toothpicks.", "料理", "600"),
    ("skewer", "串刺しにする・串", "動詞", "Pintxos are often skewered onto a slice of bread with a toothpick.", "料理", "650"),
    ("drizzle", "（液体を）少量たらす", "動詞", "Drizzle a little good olive oil over the bread before serving.", "料理", "650"),
    ("anchovy", "アンチョビ", "名詞", "A salted anchovy is a classic pintxos topping.", "料理", "600"),
    ("bechamel", "ベシャメルソース", "名詞", "Croquetas get their creamy center from a rich bechamel sauce.", "料理", "750"),
    ("tapas bar", "タパスバー", "名詞", "A good tapas bar is always crowded with locals in the evening.", "料理", "600"),
    ("bite-sized", "一口サイズの", "形容詞", "Tapas are bite-sized dishes meant to be shared around the table.", "料理", "600"),
    ("savory", "香ばしく塩気のある・食欲をそそる（甘くない）", "形容詞", "Patatas bravas make a savory start to a night of tapas.", "料理", "450"),
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
