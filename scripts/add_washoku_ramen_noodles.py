# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add RAMEN / NOODLE-SHOP / TEMPURA / UNAGI vocabulary and phrases to the
和食(washoku) domain, authored by Claude (2026-08-06・ユーザー要望:
「和食の中でも手薄だった具体的な料理名・ラーメン・麺類を厚めにする」).

このスクリプトは scripts/add_omakase_sushi.py の続編にあたる。前作は
おまかせ・時価・寿司カウンターまわりの「案内・説明」フレーズが中心
だったのに対し、こちらはラーメン屋・そば屋・うどん屋・うなぎ屋の
店頭で交わされる、より具体的な料理名と「注文・好みを伝える」フレーズ
を厚めにする:

- ラーメンの種類(豚骨/塩/醤油/味噌/つけ麺/油そば)とトッピング
  (チャーシュー・メンマ・海苔・味玉・ねぎ)、麺の硬さやスープの
  こってり/あっさりを表す表現
- うなぎ料理(うな丼/うな重/蒲焼き/肝吸い)
- 天ぷら(海老天/野菜天/衣/天丼/天つゆ)
- 蕎麦・うどん(ざるそば/かけそば/天ぷらうどん/カレーうどん/そば粉)
- 手薄だった寿司ネタ(サーモン/ウニ/イクラ/ハマチ/穴子/玉子/帆立)
- ごはん・味噌汁のバリエーション(白いご飯/丼物/あさりの味噌汁/
  赤味噌・白味噌)

words の domain は '和食' に統一(ユーザー指定。前作の add_omakase_sushi.py
は domain='料理' としていたが、DB上では和食語彙は '和食' に統一されて
いるため、今回は最初から '和食' で登録する)。
phrases の scene は既存の '和食' を継続利用(拡張)する。

level は ["300-","300","350","400","450","500","550","600","650","700",
"750","800","850","900","950","990","990+"] のスケールに沿って付与して
おり、一般的な語(ramen shop, shrimp tempura, steamed riceなど)は
400〜600、専門的な語(tsukemen, kabayaki, abura soba, unajuなど)は
700〜850とした。

事前に既存DB(words ~7000件, phrases ~4200件)を全件チェックし、
sushi / tempura / ramen / udon / soba / miso soup / onigiri / unagi /
gyudon / nigiri / vinegared rice / broth / eel / salmon / rice /
wasabi / pickled ginger / otoro / akami / soy sauce / buckwheat(既存は
「そば」の意味で植物ドメインに登録済み) が domain='和食' 等に既に
存在することを確認済み。それらと文字列が完全一致する語は避け、
buckwheat は "buckwheat flour"、tendon(天丼)は英語の身体部位
"tendon(腱)"と綴りが衝突するため "tempura rice bowl" として登録する
など、既存語・紛らわしい同綴語との衝突を避けている。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_washoku_ramen_noodles.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- ラーメンの種類 ---
    ("tonkotsu ramen", "豚骨ラーメン", "名詞", "Tonkotsu ramen has a rich, creamy pork bone broth.", "和食", "700"),
    ("shio ramen", "塩ラーメン", "名詞", "Shio ramen features a light, salt-based broth.", "和食", "700"),
    ("shoyu ramen", "醤油ラーメン", "名詞", "Shoyu ramen is flavored with a soy sauce base.", "和食", "700"),
    ("miso ramen", "味噌ラーメン", "名詞", "Miso ramen originated in Hokkaido and has a hearty, savory broth.", "和食", "650"),
    ("tsukemen", "つけ麺(麺とスープが別々に出てくる食べ方)", "名詞", "With tsukemen, you dip the noodles into a separate bowl of concentrated broth.", "和食", "800"),
    ("abura soba", "油そば(スープのない和えそば)", "名詞", "Abura soba is served without soup, tossed instead in a savory sauce and oil.", "和食", "850"),
    ("ramen shop", "ラーメン屋", "名詞", "We waited in line outside a popular ramen shop.", "和食", "500"),
    ("ramen broth", "ラーメンのスープ(だし)", "名詞", "The ramen broth had simmered for over twelve hours.", "和食", "550"),
    ("instant ramen", "インスタントラーメン", "名詞", "Instant ramen is quick to make but tastes very different from a ramen shop's version.", "和食", "500"),
    # --- ラーメンのトッピング・要素 ---
    ("chashu", "チャーシュー(煮豚)", "名詞", "Two thick slices of chashu topped the bowl of ramen.", "和食", "750"),
    ("menma", "メンマ(味付けした発酵タケノコ)", "名詞", "Menma adds a crunchy texture to ramen.", "和食", "800"),
    ("nori", "海苔", "名詞", "A sheet of nori was propped against the side of the bowl.", "和食", "550"),
    ("ajitama", "味玉(味付け半熟卵)", "名詞", "Ajitama is a soft-boiled egg marinated in a soy-based sauce.", "和食", "800"),
    ("soft-boiled egg", "半熟卵", "名詞", "I always order extra soft-boiled egg on my ramen.", "和食", "500"),
    ("scallion", "万能ねぎ・小ねぎ", "名詞", "Chopped scallion is sprinkled on top for a fresh, sharp flavor.", "和食", "550"),
    ("noodle firmness", "麺の硬さ", "名詞", "You can usually choose your noodle firmness at ramen shops.", "和食", "700"),
    ("rich-flavored", "こってりした(味が濃厚な)", "形容詞", "I prefer a rich-flavored tonkotsu broth over a light one.", "和食", "700"),
    ("light-flavored", "あっさりした(味が薄めの)", "形容詞", "Shio ramen tends to have a light-flavored broth.", "和食", "700"),
    ("extra-firm noodles", "硬麺(バリカタなど)", "名詞", "He always orders extra-firm noodles at this shop.", "和食", "750"),
    # --- うなぎ料理 ---
    ("unadon", "うな丼(うなぎ丼)", "名詞", "Unadon is a simple bowl of rice topped with grilled eel.", "和食", "750"),
    ("unaju", "うな重(重箱に入ったうなぎ)", "名詞", "Unaju is served in a lacquered box instead of a bowl.", "和食", "850"),
    ("kabayaki", "蒲焼き(甘辛いタレで焼いたうなぎ)", "名詞", "Kabayaki-style eel is grilled and basted with a sweet soy glaze.", "和食", "800"),
    ("eel liver soup", "肝吸い(うなぎの肝のお吸い物)", "名詞", "Eel liver soup is traditionally served alongside unadon.", "和食", "850"),
    ("grilled eel", "蒲焼き(焼いたうなぎ)", "名詞", "Grilled eel is brushed with a sweet soy glaze while cooking.", "和食", "600"),
    ("unagi restaurant", "うなぎ専門店", "名詞", "This unagi restaurant has been grilling eel for three generations.", "和食", "650"),
    # --- 天ぷら ---
    ("shrimp tempura", "海老天(エビの天ぷら)", "名詞", "Shrimp tempura is one of the most popular tempura choices.", "和食", "500"),
    ("vegetable tempura", "野菜の天ぷら", "名詞", "The vegetable tempura included sweet potato and pumpkin.", "和食", "500"),
    ("tempura batter", "天ぷらの衣", "名詞", "Cold water keeps the tempura batter light and crisp.", "和食", "650"),
    ("tempura rice bowl", "天丼(天ぷらをのせた丼)", "名詞", "A tempura rice bowl is topped with a sweet, savory sauce.", "和食", "700"),
    ("crispy batter", "サクサクの衣", "名詞", "The crispy batter shattered with the first bite.", "和食", "600"),
    ("tempura sauce", "天つゆ(天ぷらのつけダレ)", "名詞", "Dip the tempura lightly in the sauce before eating.", "和食", "650"),
    # --- 蕎麦・うどん ---
    ("zaru soba", "ざるそば(冷たいそばをつゆにつけて食べる)", "名詞", "Zaru soba is served cold on a bamboo mat with dipping sauce.", "和食", "750"),
    ("kake soba", "かけそば(温かいつゆをかけたそば)", "名詞", "Kake soba is a simple bowl of noodles in hot broth.", "和食", "750"),
    ("tempura udon", "天ぷらうどん", "名詞", "Tempura udon combines chewy noodles with crispy tempura on top.", "和食", "600"),
    ("curry udon", "カレーうどん", "名詞", "Curry udon has a thick, spicy-savory broth.", "和食", "700"),
    ("buckwheat flour", "そば粉", "名詞", "Soba noodles are made from buckwheat flour.", "和食", "750"),
    ("udon noodles", "うどん(麺そのもの)", "名詞", "Udon noodles are thick, chewy, and made from wheat flour.", "和食", "500"),
    ("soba noodles", "そば(麺そのもの)", "名詞", "Soba noodles are thinner than udon and have a nutty flavor.", "和食", "500"),
    ("dipping sauce", "つけつゆ・つけダレ", "名詞", "Dip the cold noodles into the dipping sauce before eating.", "和食", "500"),
    # --- 手薄だった寿司ネタ ---
    ("salmon nigiri", "サーモンの握り寿司", "名詞", "Salmon nigiri is one of the most popular choices for beginners.", "和食", "550"),
    ("sea urchin", "ウニ", "名詞", "Sea urchin has a rich, creamy, slightly sweet flavor.", "和食", "650"),
    ("salmon roe", "イクラ(鮭の卵)", "名詞", "Salmon roe bursts with a briny flavor in your mouth.", "和食", "700"),
    ("yellowtail", "ハマチ・ブリ", "名詞", "Yellowtail is prized for its buttery texture in winter.", "和食", "650"),
    ("eel sushi", "穴子寿司(アナゴ)", "名詞", "Eel sushi is often brushed with a sweet glaze instead of dipped in soy sauce.", "和食", "700"),
    ("egg sushi", "玉子寿司(卵焼きの寿司)", "名詞", "Egg sushi is a sweet, simple choice that's popular with kids.", "和食", "600"),
    ("scallop nigiri", "帆立の握り寿司", "名詞", "Scallop nigiri has a delicate, slightly sweet taste.", "和食", "650"),
    # --- ごはん・味噌汁 ---
    ("steamed rice", "白いご飯(炊いた米)", "名詞", "A bowl of steamed rice comes with almost every set meal.", "和食", "400"),
    ("rice bowl dish", "丼物(どんぶりもの)", "名詞", "A rice bowl dish is a quick, filling one-bowl meal.", "和食", "600"),
    ("clam miso soup", "あさりの味噌汁", "名詞", "Clam miso soup is a popular breakfast item in coastal areas.", "和食", "650"),
    ("red miso", "赤味噌(濃い色の味噌)", "名詞", "Red miso has a stronger, saltier flavor than white miso.", "和食", "700"),
    ("white miso", "白味噌(甘みのある味噌)", "名詞", "White miso is milder and slightly sweet.", "和食", "700"),
]

PHRASES: list[tuple[str, str]] = [
    ("Would you prefer tonkotsu or shio ramen?", "豚骨と塩、どちらがお好みですか？"),
    ("I like a light-flavored broth better than a rich one.", "こってりよりあっさりが好きです。"),
    ("I'll have the rich, tonkotsu-style broth, please.", "こってりの豚骨スープでお願いします。"),
    ("Could I get the noodles firm, please?", "麺は硬めでお願いします。"),
    ("Could you make the noodles extra soft?", "麺は柔らかめにしていただけますか？"),
    ("Can I get a large portion?", "大盛りにできますか？"),
    ("Is there an extra charge for a large portion?", "大盛りは追加料金がかかりますか？"),
    ("Could I add an extra egg to my ramen?", "ラーメンに味玉を追加できますか？"),
    ("Is eel in season right now?", "うなぎは今が旬ですか？"),
    ("Eel is best in the summer, when it's most in season.", "うなぎは夏が一番の旬です。"),
    ("Would you like the unadon or the unaju?", "うな丼とうな重、どちらになさいますか？"),
    ("What's the difference between unadon and unaju?", "うな丼とうな重の違いは何ですか？"),
    ("The unaju comes in a lacquered box and usually costs more.", "うな重は重箱に入っていて、通常はより高めです。"),
    ("This tempura is so crispy!", "この天ぷらはサクサクですね！"),
    ("The batter stayed light and crunchy even after it cooled.", "衣は冷めても軽くてサクサクのままでした。"),
    ("Could I get the tempura on the side instead of on top of the noodles?", "天ぷらは麺の上ではなく、別皿でお願いできますか？"),
    ("I'll have the tempura udon, please.", "天ぷらうどんをお願いします。"),
    ("Could I get curry udon instead?", "代わりにカレーうどんにできますか？"),
    ("Would you like your soba hot or cold?", "そばは温かいのと冷たいの、どちらがいいですか？"),
    ("I'll take the zaru soba — cold noodles with dipping sauce.", "ざるそばにします。冷たい麺をつゆにつけて食べるものです。"),
    ("Could I get extra dipping sauce on the side?", "つけつゆを多めにいただけますか？"),
    ("Is tsukemen different from regular ramen?", "つけ麺は普通のラーメンと違うのですか？"),
    ("With tsukemen, you dip the noodles into a separate, thicker broth.", "つけ麺は、麺を別皿の濃いめのスープにつけて食べます。"),
    ("Could I get extra chashu on top?", "チャーシューを追加でのせてもらえますか？"),
    ("Do you have a vegetarian ramen option?", "ベジタリアン向けのラーメンはありますか？"),
    ("How spicy is the miso ramen here?", "ここの味噌ラーメンはどのくらい辛いですか？"),
    ("Could you make it less salty?", "もう少し塩分を控えめにしていただけますか？"),
    ("I'd like white miso soup instead of red, if that's possible.", "できれば赤味噌ではなく白味噌の味噌汁にしていただきたいです。"),
    ("Is the broth made from pork bones or chicken?", "スープは豚骨ですか、それとも鶏がらですか？"),
    ("This shop is famous for its rich, twelve-hour broth.", "このお店は12時間煮込んだ濃厚なスープで有名です。"),
]


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
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

        p_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in p_existing:
                p_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, '和食')",
                (en, ja),
            )
            p_existing.add(en.lower())
            p_added += 1

    print(f"words:   +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
