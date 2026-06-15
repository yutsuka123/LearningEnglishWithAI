# ruff: noqa: E501
"""World cuisine: specific dishes & foods by country. Authored by Claude — no
app/OpenAI API calls. Dedupe on english; back-fill empty examples.
domain="料理", level 600. Run: python scripts/add_cuisine.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# country -> [(english, japanese, example)]
BY_COUNTRY: dict[str, list[tuple[str, str, str]]] = {
    "イタリア": [
        ("pizza", "ピザ", "Pizza comes from Italy."),
        ("pasta", "パスタ", "Pasta is a staple of Italian food."),
        ("spaghetti", "スパゲッティ", "He twirled the spaghetti on his fork."),
        ("lasagna", "ラザニア", "Lasagna is baked in layers."),
        ("risotto", "リゾット", "Risotto is a creamy rice dish."),
        ("gnocchi", "ニョッキ", "Gnocchi are small potato dumplings."),
        ("carbonara", "カルボナーラ", "Carbonara uses egg and bacon."),
        ("tiramisu", "ティラミス", "Tiramisu is a coffee dessert."),
        ("gelato", "ジェラート", "Italian gelato is rich and smooth."),
        ("prosciutto", "生ハム(プロシュート)", "Prosciutto is thinly sliced ham."),
        ("mozzarella", "モッツァレラ", "Mozzarella melts on pizza."),
        ("minestrone", "ミネストローネ", "Minestrone is a vegetable soup."),
    ],
    "米国": [
        ("hamburger", "ハンバーガー", "He ordered a hamburger and fries."),
        ("hot dog", "ホットドッグ", "She ate a hot dog at the game."),
        ("barbecue", "バーベキュー", "We had a backyard barbecue."),
        ("fried chicken", "フライドチキン", "Southern fried chicken is crispy."),
        ("pancakes", "パンケーキ", "He poured syrup on the pancakes."),
        ("doughnut", "ドーナツ", "She bought a glazed doughnut."),
        ("cheesecake", "チーズケーキ", "New York cheesecake is famous."),
        ("apple pie", "アップルパイ", "Apple pie is an American classic."),
        ("clam chowder", "クラムチャウダー", "Clam chowder is a thick soup."),
        ("mac and cheese", "マカロニチーズ", "Kids love mac and cheese."),
        ("buffalo wings", "バッファローウィング", "Buffalo wings are spicy."),
        ("brownie", "ブラウニー", "The brownie was warm and gooey."),
    ],
    "英国": [
        ("fish and chips", "フィッシュ・アンド・チップス", "Fish and chips is a British favorite."),
        ("roast beef", "ローストビーフ", "Sunday roast beef is traditional."),
        ("Yorkshire pudding", "ヨークシャープディング", "Yorkshire pudding is served with roast beef."),
        ("shepherd's pie", "シェパーズパイ", "Shepherd's pie has a mashed-potato top."),
        ("scone", "スコーン", "She had a scone with tea."),
        ("full English breakfast", "イングリッシュブレックファスト", "A full English breakfast is hearty."),
        ("bangers and mash", "ソーセージとマッシュポテト", "Bangers and mash is pub food."),
        ("trifle", "トライフル", "Trifle has layers of cream and fruit."),
        ("black pudding", "ブラックプディング", "Black pudding is a blood sausage."),
        ("crumpet", "クランペット", "He toasted a crumpet for breakfast."),
    ],
    "フランス": [
        ("baguette", "バゲット", "She bought a fresh baguette."),
        ("croissant", "クロワッサン", "A buttery croissant for breakfast."),
        ("crepe", "クレープ", "The crepe was filled with jam."),
        ("quiche", "キッシュ", "Quiche is a savory egg tart."),
        ("ratatouille", "ラタトゥイユ", "Ratatouille is a vegetable stew."),
        ("foie gras", "フォアグラ", "Foie gras is a rich delicacy."),
        ("escargot", "エスカルゴ", "Escargot are cooked snails."),
        ("bouillabaisse", "ブイヤベース", "Bouillabaisse is a fish stew."),
        ("macaron", "マカロン", "The macaron is light and colorful."),
        ("souffle", "スフレ", "The souffle rose in the oven."),
        ("creme brulee", "クレームブリュレ", "Creme brulee has a crisp top."),
        ("coq au vin", "コックオーヴァン", "Coq au vin is chicken in wine."),
    ],
    "インド": [
        ("curry", "カレー", "Indian curry can be very spicy."),
        ("naan", "ナン", "Naan is a soft flatbread."),
        ("tandoori", "タンドリー(料理)", "Tandoori chicken is cooked in a clay oven."),
        ("samosa", "サモサ", "A samosa is a fried pastry."),
        ("biryani", "ビリヤニ", "Biryani is a spiced rice dish."),
        ("chapati", "チャパティ", "Chapati is a thin flatbread."),
        ("masala", "マサラ(混合香辛料)", "Masala is a blend of spices."),
        ("dal", "ダル(豆カレー)", "Dal is a lentil dish."),
        ("lassi", "ラッシー", "Mango lassi is a yogurt drink."),
        ("paneer", "パニール(インドのチーズ)", "Paneer is a fresh cheese."),
        ("chai", "チャイ(香辛料入り紅茶)", "Chai is sweet, spiced tea."),
    ],
    "日本": [
        ("sushi", "寿司", "She ordered a plate of sushi."),
        ("sashimi", "刺身", "Sashimi is sliced raw fish."),
        ("tempura", "天ぷら", "Tempura is lightly battered and fried."),
        ("ramen", "ラーメン", "He slurped a bowl of ramen."),
        ("udon", "うどん", "Udon are thick wheat noodles."),
        ("soba", "そば", "Soba are buckwheat noodles."),
        ("miso soup", "味噌汁", "Miso soup is served with most meals."),
        ("teriyaki", "照り焼き", "Teriyaki chicken has a sweet glaze."),
        ("yakitori", "焼き鳥", "Yakitori is grilled chicken skewers."),
        ("okonomiyaki", "お好み焼き", "Okonomiyaki is a savory pancake."),
        ("takoyaki", "たこ焼き", "Takoyaki are octopus balls."),
        ("donburi", "丼(どんぶり)", "A donburi is a rice bowl with toppings."),
    ],
    "中華": [
        ("dumpling", "餃子・点心", "Steamed dumplings are popular."),
        ("fried rice", "チャーハン", "Fried rice uses leftover rice."),
        ("spring roll", "春巻き", "Spring rolls are crispy and light."),
        ("dim sum", "飲茶(点心)", "We shared several dim sum dishes."),
        ("wonton", "ワンタン", "Wonton soup is light and warm."),
        ("chow mein", "焼きそば(チャーメン)", "Chow mein has stir-fried noodles."),
        ("sweet and sour pork", "酢豚", "Sweet and sour pork is tangy."),
        ("Peking duck", "北京ダック", "Peking duck has crispy skin."),
        ("mapo tofu", "麻婆豆腐", "Mapo tofu is spicy and numbing."),
        ("hot pot", "火鍋(ホットポット)", "We cooked meat in the hot pot."),
        ("congee", "お粥(中華粥)", "Congee is a comforting rice porridge."),
    ],
    "韓国": [
        ("kimchi", "キムチ", "Kimchi is fermented cabbage."),
        ("bibimbap", "ビビンバ", "Bibimbap mixes rice and vegetables."),
        ("bulgogi", "プルコギ", "Bulgogi is marinated grilled beef."),
        ("tteokbokki", "トッポギ", "Tteokbokki are spicy rice cakes."),
        ("japchae", "チャプチェ", "Japchae uses glass noodles."),
        ("gimbap", "キンパ(海苔巻き)", "Gimbap is a Korean rice roll."),
        ("samgyeopsal", "サムギョプサル(豚バラ焼き)", "Samgyeopsal is grilled pork belly."),
        ("kimchi stew", "キムチチゲ", "Kimchi stew is hot and sour."),
    ],
    "ロシア": [
        ("borscht", "ボルシチ", "Borscht is a red beet soup."),
        ("beef stroganoff", "ビーフストロガノフ", "Beef stroganoff has a creamy sauce."),
        ("pelmeni", "ペリメニ(水餃子)", "Pelmeni are small meat dumplings."),
        ("blini", "ブリヌイ(ロシア風クレープ)", "Blini are served with caviar."),
        ("caviar", "キャビア", "Caviar is salted fish roe."),
        ("pirozhki", "ピロシキ", "Pirozhki are stuffed buns."),
    ],
    "スペイン": [
        ("paella", "パエリア", "Paella is a Spanish rice dish."),
        ("tapas", "タパス(小皿料理)", "We ordered several tapas."),
        ("gazpacho", "ガスパチョ", "Gazpacho is a cold tomato soup."),
        ("tortilla", "トルティージャ(スペイン風オムレツ)", "Spanish tortilla has potato and egg."),
        ("churros", "チュロス", "Churros are dipped in chocolate."),
        ("jamon", "ハモン(生ハム)", "Jamon is cured Spanish ham."),
        ("sangria", "サングリア", "Sangria is a wine punch."),
        ("chorizo", "チョリソ", "Chorizo is a spicy sausage."),
    ],
    "その他各国": [
        ("taco", "タコス(メキシコ)", "A taco is folded around the filling."),
        ("burrito", "ブリトー(メキシコ)", "A burrito is wrapped in a tortilla."),
        ("guacamole", "ワカモレ(メキシコ)", "Guacamole is mashed avocado."),
        ("pad thai", "パッタイ(タイ)", "Pad thai is a stir-fried noodle dish."),
        ("pho", "フォー(ベトナム)", "Pho is a Vietnamese noodle soup."),
        ("kebab", "ケバブ(中東)", "A kebab is grilled meat on a skewer."),
        ("falafel", "ファラフェル(中東)", "Falafel are fried chickpea balls."),
        ("hummus", "フムス(中東)", "Hummus is a chickpea dip."),
        ("schnitzel", "シュニッツェル(ドイツ)", "Schnitzel is a breaded cutlet."),
        ("pretzel", "プレッツェル(ドイツ)", "A soft pretzel with mustard."),
        ("sauerkraut", "ザワークラウト(ドイツ)", "Sauerkraut is fermented cabbage."),
    ],
}


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = filled = 0
        per_country: dict[str, int] = {}
        for country, items in BY_COUNTRY.items():
            for en, ja, ex in items:
                if en.lower() in existing:
                    conn.execute(
                        "UPDATE words SET example = ? WHERE "
                        "LOWER(english)=LOWER(?) AND COALESCE(example,'')=''",
                        (ex, en),
                    )
                    filled += 1
                    continue
                conn.execute(
                    "INSERT INTO words (english, japanese, part_of_speech, "
                    "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                    (en, ja, "", ex, "料理", "600"),
                )
                existing.add(en.lower())
                added += 1
                per_country[country] = per_country.get(country, 0) + 1
    print(f"words: +{added} (例文補充 {filled})  {per_country}")
    with db() as conn:
        print("単語総数:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
