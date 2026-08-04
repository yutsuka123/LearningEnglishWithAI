# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated vocabulary for WORLD CUISINES beyond the ones already
well covered in the DB, authored by Claude.

Focus (料理ドメインの手薄な領域を補強): 韓国・メキシコ・中東・ギリシャ・ロシア・
カリブ/ブラジル・北欧の料理語彙とフレーズ。既存DB (料理ドメイン141語+) には
すでに以下が入っているため、それらは再投入しない:
  - 韓国: bibimbap, bulgogi, kimchi, kimchi stew, japchae, gimbap,
    samgyeopsal, tteokbokki
  - メキシコ: burrito, taco, guacamole, tortilla, churros
  - 中東: falafel, hummus, kebab
  - ロシア: borscht, blini, pelmeni, pirozhki, beef stroganoff
  - その他: caviar, chorizo (他ドメインでカバー済み)

このスクリプトはそれらより「一段深い」語彙（バンチャン、コチュジャン、
モレソース、シャワルマ、ツァジキ、クワス、フェイジョアーダ、
スモーガスボードなど）と、注文・料理について尋ねる・未知の料理を説明する
自然な会話フレーズを追加する。

他の並行バッチが日本/中国/タイ、インド/ベトナム/スペイン、フランス/
イタリア、アメリカ/イギリス/ドイツをカバーしているため、本スクリプトは
それらの国・地域には触れない。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_food_world_other.py
      python scripts/add_food_world_other.py --missing-words   # report only

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
    "韓国・メキシコ料理を英語で語る": [
        # --- 韓国料理: 注文する ---
        ("Could I get an order of banchan to start?", "最初に韓国のおかず（バンチャン）を一皿もらえますか？"),
        ("What's in doenjang jjigae?", "テンジャンチゲには何が入っていますか？"),
        ("Is this spicy? It looks like it has gochujang in it.", "これは辛いですか？コチュジャンが入っているようですが。"),
        ("Can we get the tabletop grill going for Korean BBQ?", "卓上グリルをつけて韓国式焼肉を始めましょうか。"),
        ("I'll have a bowl of bingsu for dessert.", "デザートにビンス（かき氷）を一つください。"),
        ("Do you want to split a bottle of soju?", "焼酎（ソジュ）を一本シェアしませんか？"),
        ("Wrap the galbi in a lettuce leaf with some ssamjang.", "カルビをレタスで包んでサムジャンを添えて食べてください。"),
        ("Two orders of mandu, steamed, please.", "マンドゥ（韓国餃子）を蒸しで二皿お願いします。"),
        # --- 韓国料理: 説明する ---
        ("How would you describe Korean food to someone who's never tried it?", "韓国料理を食べたことのない人にどう説明しますか？"),
        ("It's a mix of fermented, spicy, and savory flavors.", "発酵・辛さ・旨味が混ざり合った味です。"),
        ("Samgyetang is a whole chicken soup stuffed with rice and ginseng.", "サムゲタンは米と高麗人参を詰めた丸鶏のスープです。"),
        ("Jjigae is basically a category of Korean stews.", "チゲとは基本的に韓国の鍋料理の総称です。"),
        # --- メキシコ料理: 注文する ---
        ("Two chicken enchiladas, please, with extra salsa verde.", "チキンエンチラーダを二つ、サルサベルデを多めでお願いします。"),
        ("Could I get that with corn tortillas instead of flour?", "それを小麦粉ではなくコーントルティーヤでお願いできますか？"),
        ("Let's grab elote from that street cart.", "あの屋台でエロテ（メキシコ風焼きとうもろこし）を買いましょう。"),
        ("That little taqueria on the corner has the best al pastor.", "角にある小さなタケリアがアル・パストールが一番おいしいです。"),
        ("Add some pico de gallo on top if you like it fresh.", "さっぱりさせたいならピコ・デ・ガヨを上にのせてください。"),
        # --- メキシコ料理: 尋ねる・説明する ---
        ("Is this the red salsa or the green one?", "これは赤いサルサですか、それとも緑のサルサですか？"),
        ("What's the difference between a taco and a quesadilla?", "タコスとケサディーヤの違いは何ですか？"),
        ("Mole sauce takes hours to make — it has chocolate in it.", "モレソースは作るのに何時間もかかり、チョコレートが入っています。"),
    ],
    "中東・ギリシャ料理を英語で語る": [
        # --- 中東料理: 注文する ---
        ("Could I get a chicken shawarma wrap to go?", "チキンシャワルマラップをテイクアウトでもらえますか？"),
        ("Would you like tabbouleh or fattoush as a side?", "サイドにタブーリとファットゥーシュ、どちらがいいですか？"),
        ("Do you have tahini on the side?", "タヒニ（ごまペースト）は別添えでありますか？"),
        ("Let's order a few mezze to share.", "シェアするためにメゼを何品か注文しましょう。"),
        ("Could I try a piece of Turkish delight?", "ターキッシュ・ディライトを一切れ試してもいいですか？"),
        ("A small cup of Turkish coffee, please — unsweetened.", "トルココーヒーを一杯、無糖でお願いします。"),
        # --- 中東料理: 尋ねる・説明する ---
        ("What's baklava made of?", "バクラヴァは何でできていますか？"),
        ("It's layers of phyllo dough with nuts and honey.", "ナッツと蜂蜜を挟んだフィロ生地の層です。"),
        ("The pita bread here is fresh out of the oven.", "ここのピタパンは焼きたてです。"),
        ("This salad is seasoned with za'atar.", "このサラダはザアタルで味付けされています。"),
        ("What's labneh usually served with?", "ラブネは普段何と一緒に出されますか？"),
        ("Is this dolma stuffed with rice or meat?", "このドルマは米詰めですか、それとも肉詰めですか？"),
        ("The kofta is grilled over charcoal.", "コフタは炭火で焼かれています。"),
        ("Sumac gives it a slightly sour, lemony taste.", "スマックは少し酸味のあるレモンのような味を加えます。"),
        ("This dip is baba ghanoush — it's made from roasted eggplant.", "このディップはバーバガヌーシュで、焼きナスから作られています。"),
        # --- ギリシャ料理: 説明する・注文する ---
        ("How would you explain Greek food to a first-timer?", "初めての人にギリシャ料理をどう説明しますか？"),
        ("A gyro is meat, vegetables, and tzatziki wrapped in flatbread.", "ジャイロは肉と野菜、ザジキをフラットブレッドで包んだものです。"),
        ("Moussaka is a layered dish with eggplant and ground meat.", "ムサカはナスとひき肉を重ねた料理です。"),
        ("This salad has feta cheese and kalamata olives on top.", "このサラダにはフェタチーズとカラマタオリーブがのっています。"),
        ("We ordered souvlaki skewers and spanakopita.", "スブラキの串焼きとスパナコピタを注文しました。"),
        ("Would you like a glass of ouzo after dinner?", "食後にウーゾを一杯いかがですか？"),
    ],
    "その他世界の料理を英語で語る": [
        # --- ロシア料理 ---
        ("Have you ever tried kvass? It's a fermented rye drink.", "クワスを飲んだことがありますか？発酵させたライ麦の飲み物です。"),
        ("The waiter brought out a plate of zakuski before the meal.", "ウェイターが食事の前にザクースキ（前菜盛り合わせ）を持ってきました。"),
        ("Would you like a shot of vodka to go with the meal?", "食事と一緒にウォッカを一杯いかがですか？"),
        ("This bread is dense — it's a traditional Russian black bread.", "このパンはずっしりしていて、伝統的なロシアの黒パンです。"),
        ("Shashlik is meat marinated and grilled on skewers.", "シャシリクはマリネした肉を串で焼いたものです。"),
        # --- カリブ・ブラジル料理 ---
        ("The jerk chicken has a smoky, spicy kick to it.", "ジャークチキンは燻製のような辛さがあります。"),
        ("Could I get fried plantain on the side?", "付け合わせに揚げたプランテンをもらえますか？"),
        ("Feijoada is a black bean stew with different cuts of pork.", "フェイジョアーダは豚肉のいろいろな部位を使った黒豆の煮込みです。"),
        ("We're grilling churrasco this weekend.", "今週末はシュラスコを焼く予定です。"),
        ("Could I have an empanada filled with beef?", "牛肉入りのエンパナーダをもらえますか？"),
        ("Picanha is a popular cut for Brazilian barbecue.", "ピカーニャはブラジル風バーベキューでよく使われる部位です。"),
        ("Tostones are twice-fried plantain slices.", "トストーネスは二度揚げしたプランテンのスライスです。"),
        ("Let's order a round of caipirinhas.", "カイピリーニャを一杯ずつ頼みましょう。"),
        # --- 北欧料理 ---
        ("How would you describe Scandinavian food to someone unfamiliar with it?", "北欧料理を知らない人にどう説明しますか？"),
        ("A smorgasbord is a spread of many small dishes.", "スモーガスボードはたくさんの小皿料理を並べたものです。"),
        ("Gravlax is salmon cured with salt, sugar, and dill.", "グラブラックスは塩と砂糖、ディルで漬けたサーモンです。"),
        ("Swedish meatballs are usually served with lingonberry jam.", "スウェーデン風ミートボールは通常リンゴンベリージャムと一緒に出されます。"),
        ("Would you like some crispbread with your cheese?", "チーズと一緒にクリスプブレッドはいかがですか？"),
        ("Let's take a fika break with coffee and a cinnamon bun.", "コーヒーとシナモンバンでフィーカ（休憩）にしましょう。"),
        # --- 総括: 未知の料理を説明してもらう ---
        ("I'm not familiar with this cuisine — could you walk me through the menu?", "この料理はよく知らないので、メニューを説明してもらえますか？"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 韓国料理 ---
    ("banchan", "韓国のおかず・副菜", "名詞", "The table was covered with small dishes of banchan.", "料理", "850"),
    ("doenjang", "テンジャン（韓国の発酵味噌）", "名詞", "Doenjang jjigae is a stew made with fermented soybean paste.", "料理", "900"),
    ("gochujang", "コチュジャン（唐辛子味噌）", "名詞", "Add a spoonful of gochujang to make it spicier.", "料理", "700"),
    ("gochugaru", "コチュガル（韓国産唐辛子粉）", "名詞", "Sprinkle some gochugaru over the kimchi while it ferments.", "料理", "900"),
    ("samgyetang", "サムゲタン（参鶏湯）", "名詞", "Samgyetang is often eaten on the hottest days of summer.", "料理", "950"),
    ("bingsu", "ビンス（韓国のかき氷）", "名詞", "We shared a big bowl of bingsu on a hot afternoon.", "料理", "800"),
    ("soju", "焼酎（韓国の蒸留酒）", "名詞", "They toasted with small glasses of soju.", "料理", "700"),
    ("makgeolli", "マッコリ（濁り酒）", "名詞", "Makgeolli is a milky, slightly fizzy rice wine.", "料理", "900"),
    ("galbi", "カルビ（韓国風焼き肉）", "名詞", "The galbi sizzled on the tabletop grill.", "料理", "750"),
    ("ssamjang", "サムジャン（包み野菜用の合わせ味噌）", "名詞", "Dip the grilled meat in ssamjang before wrapping it.", "料理", "900"),
    ("mandu", "マンドゥ（韓国餃子）", "名詞", "My grandmother makes mandu by hand every New Year.", "料理", "850"),
    ("jjigae", "チゲ（韓国の鍋料理）", "名詞", "This jjigae is simmering with tofu and vegetables.", "料理", "850"),
    ("tteok", "トッ（韓国餅）", "名詞", "The soft, chewy tteok is made from pounded rice.", "料理", "850"),
    ("sesame oil", "ごま油", "名詞", "Finish the dish with a drizzle of sesame oil.", "料理", "400"),
    ("hotteok", "ホットク（韓国の甘い焼き餅）", "名詞", "Hotteok is a sweet pancake filled with brown sugar and nuts.", "料理", "900"),
    ("dakgalbi", "タッカルビ（韓国風鶏肉炒め）", "名詞", "Dakgalbi is stir-fried chicken cooked with a spicy sauce.", "料理", "950"),
    ("naengmyeon", "冷麺", "名詞", "Naengmyeon is a bowl of cold buckwheat noodles, perfect for summer.", "料理", "950"),
    # --- メキシコ料理 ---
    ("enchilada", "エンチラーダ", "名詞", "The enchilada was smothered in red sauce and melted cheese.", "料理", "500"),
    ("quesadilla", "ケサディーヤ", "名詞", "She folded the tortilla in half to make a quesadilla.", "料理", "450"),
    ("tamale", "タマレ（トウモロコシの皮で包んだ蒸し料理）", "名詞", "Each tamale is steamed inside its corn husk wrapper.", "料理", "650"),
    ("mole sauce", "モレソース（メキシコの複雑なソース）", "名詞", "The chicken was served in a rich, dark mole sauce.", "料理", "750"),
    ("salsa", "サルサ（辛味ソース）", "名詞", "Pass me the salsa for my chips.", "料理", "400"),
    ("salsa verde", "サルサベルデ（緑のサルサ）", "名詞", "Salsa verde is made with tomatillos instead of red tomatoes.", "料理", "600"),
    ("salsa roja", "サルサロハ（赤いサルサ）", "名詞", "Salsa roja gets its color from red chilies and tomatoes.", "料理", "650"),
    ("ceviche", "セビーチェ（魚介のライム締め）", "名詞", "The ceviche is made with raw fish cured in lime juice.", "料理", "650"),
    ("elote", "エロテ（メキシコ風焼きとうもろこし）", "名詞", "Elote is grilled corn on the cob coated with mayo, cheese, and chili powder.", "料理", "850"),
    ("pico de gallo", "ピコ・デ・ガヨ（トマトのみじん切りサルサ）", "名詞", "Top your tacos with fresh pico de gallo.", "料理", "700"),
    ("taqueria", "タケリア（タコス専門店）", "名詞", "There's a great taqueria just around the corner.", "料理", "750"),
    ("corn tortilla", "コーントルティーヤ", "名詞", "Street tacos are usually served on a small corn tortilla.", "料理", "550"),
    ("flour tortilla", "小麦粉のトルティーヤ", "名詞", "A burrito is wrapped in a large flour tortilla.", "料理", "550"),
    ("jalapeño", "ハラペーニョ", "名詞", "Add sliced jalapeño if you want more heat.", "料理", "500"),
    ("carne asada", "カルネ・アサーダ（炭火焼き牛肉）", "名詞", "The carne asada was grilled over an open flame.", "料理", "700"),
    ("al pastor", "アル・パストール（豚肉の串焼き）", "名詞", "Al pastor is pork marinated in chilies and pineapple.", "料理", "850"),
    ("queso fresco", "ケソ・フレスコ（メキシコの生チーズ）", "名詞", "Crumble some queso fresco over the beans.", "料理", "800"),
    ("street taco", "ストリートタコス（屋台風の小さなタコス）", "名詞", "Street tacos are small and usually served with just onion and cilantro.", "料理", "600"),
    ("horchata", "オルチャータ（米のミルク飲料）", "名詞", "Horchata is a sweet, cinnamon-flavored rice drink.", "料理", "750"),
    ("tres leches cake", "トレス・レチェス・ケーキ（三種のミルクケーキ）", "名詞", "Tres leches cake is soaked in three kinds of milk.", "料理", "850"),
    ("chile relleno", "チレ・レジェーノ（詰め物ペッパーフライ）", "名詞", "A chile relleno is a stuffed and battered pepper.", "料理", "850"),
    ("tortilla chips", "トルティーヤチップス", "名詞", "We ordered a basket of tortilla chips with guacamole.", "料理", "400"),
    ("pozole", "ポソレ（トウモロコシと豚肉のスープ）", "名詞", "Pozole is a hearty soup made with hominy and pork.", "料理", "900"),
    # --- 中東料理 ---
    ("shawarma", "シャワルマ", "名詞", "The shawarma meat is stacked on a spit and roasted slowly.", "料理", "550"),
    ("baklava", "バクラヴァ", "名詞", "Baklava is a sweet pastry made of many layers of phyllo dough.", "料理", "600"),
    ("tabbouleh", "タブーリ（パセリのサラダ）", "名詞", "Tabbouleh is a fresh salad made mostly of parsley and bulgur.", "料理", "750"),
    ("pita bread", "ピタパン", "名詞", "Scoop up the hummus with a piece of pita bread.", "料理", "450"),
    ("tahini", "タヒニ（ごまペースト）", "名詞", "Tahini is a paste made from ground sesame seeds.", "料理", "650"),
    ("za'atar", "ザアタル（中東のスパイスミックス）", "名詞", "The bread was sprinkled with za'atar and olive oil.", "料理", "850"),
    ("mezze", "メゼ（中東の前菜盛り合わせ）", "名詞", "We ordered a mezze platter to share before the main course.", "料理", "750"),
    ("Turkish delight", "ターキッシュ・ディライト（トルコの伝統菓子）", "名詞", "Turkish delight comes in flavors like rosewater and pistachio.", "料理", "600"),
    ("Turkish coffee", "トルココーヒー", "名詞", "Turkish coffee is served in a small cup with the grounds settled at the bottom.", "料理", "600"),
    ("labneh", "ラブネ（水切りヨーグルト）", "名詞", "Labneh is a thick, strained yogurt often drizzled with olive oil.", "料理", "900"),
    ("fattoush", "ファットゥーシュ（パンのサラダ）", "名詞", "Fattoush is a salad topped with crispy pieces of fried pita.", "料理", "850"),
    ("dolma", "ドルマ（葡萄の葉の巻き物）", "名詞", "Dolma are grape leaves stuffed with rice and herbs.", "料理", "800"),
    ("kofta", "コフタ（ひき肉の串焼き）", "名詞", "The kofta skewers were grilled over an open flame.", "料理", "750"),
    ("sumac", "スマック（酸味のあるスパイス）", "名詞", "A dash of sumac adds a tangy, citrusy flavor.", "料理", "850"),
    ("baba ghanoush", "バーバガヌーシュ（焼きナスのディップ）", "名詞", "Baba ghanoush is made from roasted, mashed eggplant.", "料理", "750"),
    ("shakshuka", "シャクシューカ（卵のトマト煮）", "名詞", "Shakshuka is eggs poached in a spiced tomato sauce.", "料理", "700"),
    ("manakish", "マナキーシュ（中東のフラットブレッド）", "名詞", "Manakish is a flatbread often topped with za'atar and olive oil.", "料理", "950"),
    ("kibbeh", "キッベ（ひき肉とブルグルの料理）", "名詞", "Kibbeh is made from ground meat mixed with bulgur wheat.", "料理", "900"),
    ("harissa", "ハリッサ（辛味唐辛子ペースト）", "名詞", "Harissa is a fiery chili paste used across North African cooking.", "料理", "750"),
    # --- ギリシャ料理 ---
    ("gyro", "ジャイロ（ギリシャ風肉巻き）", "名詞", "The gyro was stuffed with meat, onions, and tzatziki.", "料理", "550"),
    ("moussaka", "ムサカ（ナスの重ね焼き）", "名詞", "Moussaka is baked in layers with eggplant, potato, and ground meat.", "料理", "650"),
    ("tzatziki", "ザジキ（ヨーグルトソース）", "名詞", "Tzatziki is a cool yogurt sauce with cucumber and garlic.", "料理", "600"),
    ("feta cheese", "フェタチーズ", "名詞", "Crumble some feta cheese over the salad.", "料理", "450"),
    ("souvlaki", "スブラキ（ギリシャの串焼き）", "名詞", "Souvlaki is grilled meat served on a skewer.", "料理", "700"),
    ("spanakopita", "スパナコピタ（ほうれん草のパイ）", "名詞", "Spanakopita is a savory pie filled with spinach and feta.", "料理", "750"),
    ("Greek salad", "ギリシャ風サラダ", "名詞", "A Greek salad usually skips the lettuce entirely.", "料理", "450"),
    ("ouzo", "ウーゾ（ギリシャの蒸留酒）", "名詞", "Ouzo turns cloudy white when you add water to it.", "料理", "750"),
    ("phyllo dough", "フィロ生地（極薄のパイ生地）", "名詞", "The pie is wrapped in thin sheets of phyllo dough.", "料理", "700"),
    ("kalamata olives", "カラマタオリーブ", "名詞", "The salad was topped with kalamata olives and feta.", "料理", "650"),
    ("Greek yogurt", "ギリシャヨーグルト", "名詞", "Greek yogurt is strained to make it thicker and creamier.", "料理", "400"),
    ("loukoumades", "ルクマデス（蜂蜜がけの揚げ団子）", "名詞", "Loukoumades are fried dough balls drizzled with honey.", "料理", "900"),
    ("halloumi", "ハルーミ（焼いても溶けないチーズ）", "名詞", "Halloumi is a cheese that holds its shape when grilled.", "料理", "700"),
    ("retsina", "レツィーナ（松脂風味のギリシャワイン）", "名詞", "Retsina is a Greek wine flavored with pine resin.", "料理", "900"),
    # --- ロシア料理 ---
    ("kvass", "クワス（ライ麦の発酵飲料）", "名詞", "Kvass is a lightly fermented drink made from rye bread.", "料理", "950"),
    ("zakuski", "ザクースキ（ロシアの前菜盛り合わせ）", "名詞", "Zakuski are small appetizers served before a big meal.", "料理", "950"),
    ("vodka", "ウォッカ", "名詞", "They raised their glasses of vodka for a toast.", "料理", "400"),
    ("samovar", "サモワール（ロシアの湯沸かし茶器）", "名詞", "Tea was brewed slowly in an old samovar.", "料理", "900"),
    ("black bread", "黒パン（ロシアのライ麦パン）", "名詞", "The dense black bread is served with almost every meal.", "料理", "700"),
    ("kasha", "カーシャ（そば粥）", "名詞", "Kasha is a warm porridge usually made from buckwheat.", "料理", "850"),
    ("shashlik", "シャシリク（串焼き肉）", "名詞", "Shashlik is meat marinated overnight and grilled on skewers.", "料理", "850"),
    # --- カリブ・ブラジル料理 ---
    ("jerk chicken", "ジャークチキン", "名詞", "Jerk chicken is marinated in a fiery blend of spices.", "料理", "650"),
    ("plantain", "プランテン（料理用バナナ）", "名詞", "Fried plantain makes a great side dish.", "料理", "600"),
    ("feijoada", "フェイジョアーダ（黒豆と豚肉の煮込み）", "名詞", "Feijoada simmers for hours until the beans turn rich and dark.", "料理", "900"),
    ("churrasco", "シュラスコ（ブラジル風炭火焼き肉）", "名詞", "Churrasco is meat grilled slowly over an open fire.", "料理", "750"),
    ("empanada", "エンパナーダ（詰め物パイ）", "名詞", "Each empanada is stuffed and folded before frying.", "料理", "600"),
    ("picanha", "ピカーニャ（牛肉の部位）", "名詞", "Picanha is prized for its thick layer of fat on top.", "料理", "900"),
    ("farofa", "ファロッファ（キャッサバ粉の炒り物）", "名詞", "Farofa is toasted cassava flour sprinkled over rice and beans.", "料理", "950"),
    ("caipirinha", "カイピリーニャ（ブラジルのカクテル）", "名詞", "A caipirinha is made with lime, sugar, and cachaça.", "料理", "750"),
    ("mofongo", "モフォンゴ（プランテン料理）", "名詞", "Mofongo is mashed plantain mixed with garlic and pork cracklings.", "料理", "900"),
    ("rice and peas", "ライス・アンド・ピーズ（カリブ風豆ご飯）", "名詞", "Rice and peas is a classic side dish in Caribbean cooking.", "料理", "650"),
    ("allspice", "オールスパイス", "名詞", "Allspice gives jerk seasoning its distinctive smell.", "料理", "700"),
    ("jerk seasoning", "ジャークシーズニング", "名詞", "Rub the chicken with jerk seasoning the night before.", "料理", "650"),
    ("brigadeiro", "ブリガデイロ（ブラジルのチョコ菓子）", "名詞", "Brigadeiro is a chocolate truffle rolled in sprinkles.", "料理", "900"),
    ("pão de queijo", "パン・デ・ケイジョ（ブラジルのチーズパン）", "名詞", "Pão de queijo is a chewy cheese bread made with cassava flour.", "料理", "950"),
    ("cassava", "キャッサバ", "名詞", "Cassava is a starchy root used across Caribbean and Brazilian cooking.", "料理", "650"),
    ("tostones", "トストーネス（二度揚げプランテン）", "名詞", "Tostones are crispy, twice-fried plantain slices.", "料理", "850"),
    # --- 北欧料理 ---
    ("smorgasbord", "スモーガスボード（北欧式ビュッフェ）", "名詞", "The buffet was a smorgasbord of cold meats, fish, and bread.", "料理", "600"),
    ("gravlax", "グラブラックス（塩漬けサーモン）", "名詞", "Gravlax is served thinly sliced with a mustard-dill sauce.", "料理", "750"),
    ("Swedish meatballs", "スウェーデン風ミートボール", "名詞", "Swedish meatballs are usually served with lingonberry jam and gravy.", "料理", "500"),
    ("rye bread", "ライ麦パン", "名詞", "The sandwich was made with dense, dark rye bread.", "料理", "450"),
    ("crispbread", "クリスプブレッド（薄焼きパン）", "名詞", "Crispbread stays crunchy for weeks without going stale.", "料理", "650"),
    ("fika", "フィーカ（北欧のコーヒー休憩の習慣）", "名詞", "Fika is a daily break for coffee and something sweet.", "料理", "850"),
    ("lingonberry", "リンゴンベリー（コケモモ）", "名詞", "Lingonberry jam has a tart, slightly bitter taste.", "料理", "700"),
    ("pickled herring", "ニシンの酢漬け", "名詞", "Pickled herring is a staple of the holiday table.", "料理", "700"),
    ("aquavit", "アクアビット（北欧のスパイス蒸留酒）", "名詞", "Aquavit is a spiced spirit often served ice cold.", "料理", "900"),
    ("cardamom bun", "カルダモンバン（北欧の菓子パン）", "名詞", "The bakery sells warm cardamom buns every morning.", "料理", "900"),
    ("cloudberry", "クラウドベリー（ホロムイイチゴ）", "名詞", "Cloudberries grow wild in the far north.", "料理", "900"),
    ("cinnamon bun", "シナモンバン（シナモンロール）", "名詞", "They took a fika break with coffee and a cinnamon bun.", "料理", "500"),
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
