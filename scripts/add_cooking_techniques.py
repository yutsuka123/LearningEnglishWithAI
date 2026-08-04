# ruff: noqa: E501  (data-heavy seed script: long word/example lines are fine)
"""Bulk-add curated vocabulary for GENERAL COOKING TECHNIQUES / METHODS,
authored by Claude.

Focus (料理ドメインの手薄な領域を補強): 具体的な料理名や汎用の基本動詞
（bake, boil, simmer, whisk, knead, marinate, season, garnish, dice, mince,
peel, drain, ferment, steam, grill, deep-fry, stir-fry, chop, mash, preheat,
fry, tender など）はすでに投入済みのため、それ以外の「加熱技法」
「下ごしらえ・混ぜ方の技法」「製菓・パン生地の技法」「保存・仕上げの技法」
を体系的に補強する。どの料理ジャンルでも通用する汎用の調理技術用語。

日常的によく使う技法（roast, poach, sear など）は易しめのレベル、
ソース系のやや専門的な技法（braise, reduce, temper など）は中級、
製菓・専門店レベルの技法（laminate, brunoise, chiffonade, clarify など）
は上級レベルに設定した。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_cooking_techniques.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 加熱技法 ---
    ("poach", "（卵などを）静かに茹でる", "動詞", "Poach the eggs in gently simmering water for three minutes.", "料理", "500"),
    ("blanch", "下茹でする（さっと熱湯にくぐらせる）", "動詞", "Blanch the broccoli for one minute, then plunge it into ice water.", "料理", "650"),
    ("sear", "表面を強火でさっと焼き付ける", "動詞", "Sear the steak on both sides before finishing it in the oven.", "料理", "600"),
    ("braise", "少量の液体でじっくり蒸し煮にする", "動詞", "Braise the short ribs in red wine for three hours.", "料理", "750"),
    ("roast", "オーブンでローストする", "動詞", "Roast the chicken at 200 degrees until the skin is golden.", "料理", "500"),
    ("caramelize", "砂糖分を焦がして風味とコクを出す", "動詞", "Slowly caramelize the onions until they turn deep brown.", "料理", "700"),
    ("char", "表面を黒く焦がすように焼く", "動詞", "Char the peppers directly over the flame until the skin blisters.", "料理", "650"),
    ("toast", "軽く炒って香りを引き出す", "動詞", "Toast the cumin seeds in a dry pan until fragrant.", "料理", "550"),
    ("reduce", "ソースなどを煮詰めて濃縮する", "動詞", "Reduce the sauce over low heat until it coats the back of a spoon.", "料理", "750"),
    ("broil", "上火で強く焼く", "動詞", "Broil the salmon for five minutes until the top is lightly charred.", "料理", "650"),
    ("smoke", "燻製にする", "動詞", "We smoke the salmon over applewood chips for two hours.", "料理", "650"),
    ("confit", "低温の油や脂でじっくり煮て保存性を高める", "動詞", "Confit the duck legs slowly in their own fat.", "料理", "900"),
    ("pressure cook", "圧力鍋で調理する", "動詞", "Pressure cook the dried beans for twenty minutes instead of soaking them overnight.", "料理", "600"),
    ("stew", "とろ火でじっくり煮込む", "動詞", "Stew the beef with carrots and potatoes until tender.", "料理", "550"),
    # --- 下ごしらえ・混ぜ方の技法 ---
    ("fold", "泡を潰さないようにさっくりと混ぜ込む", "動詞", "Gently fold the egg whites into the batter.", "料理", "700"),
    ("cream", "バターと砂糖などをすり混ぜてなめらかにする", "動詞", "Cream the butter and sugar together until light and fluffy.", "料理", "750"),
    ("emulsify", "乳化させる", "動詞", "Whisk quickly to emulsify the oil and vinegar into a smooth dressing.", "料理", "850"),
    ("puree", "ピューレ状にする", "動詞", "Puree the roasted tomatoes into a smooth sauce.", "料理", "650"),
    ("strain", "濾して液体と固形物を分ける", "動詞", "Strain the stock through a fine sieve before using it.", "料理", "550"),
    ("sift", "粉をふるいにかけて空気を含ませる", "動詞", "Sift the flour and baking powder together before mixing.", "料理", "650"),
    ("sieve", "ふるいにかける・濾す", "動詞", "Sieve the flour to remove any lumps.", "料理", "700"),
    ("skim", "表面に浮いた脂やアクをすくい取る", "動詞", "Skim the fat off the top of the broth as it simmers.", "料理", "700"),
    ("zest", "柑橘類の皮をすりおろす", "動詞", "Zest a lemon directly over the finished pasta.", "料理", "700"),
    ("julienne", "細長い千切りにする", "動詞", "Julienne the carrots into thin, matchstick-sized strips.", "料理", "850"),
    ("brunoise", "極小のさいの目に切る", "動詞", "Brunoise the shallots for a fine, even garnish.", "料理", "950"),
    ("chiffonade", "葉野菜をリボン状の細切りにする", "動詞", "Chiffonade the basil leaves and scatter them over the pizza.", "料理", "950"),
    ("butterfly", "肉を観音開きに切り開く", "動詞", "Butterfly the chicken breast so it cooks more evenly.", "料理", "800"),
    ("debone", "骨を取り除く", "動詞", "Debone the trout before stuffing it with herbs.", "料理", "750"),
    ("fillet", "魚などを三枚におろす・骨を取り除いて切り身にする", "動詞", "Fillet the fish and remove any remaining pin bones.", "料理", "700"),
    ("score", "肉や皮に浅く切り込みを入れる", "動詞", "Score the pork skin in a diamond pattern before roasting.", "料理", "700"),
    ("tenderize", "肉を柔らかくする", "動詞", "Tenderize the meat with a mallet before frying it.", "料理", "700"),
    ("pound", "肉を叩いて薄く伸ばす", "動詞", "Pound the chicken breast flat with a meat mallet.", "料理", "650"),
    ("truss", "鳥などを糸で縛って形を整える", "動詞", "Truss the turkey so it cooks evenly in the oven.", "料理", "900"),
    # --- 製菓・パン生地の技法 ---
    ("proof", "生地を発酵させる", "動詞", "Let the dough proof in a warm place until it doubles in size.", "料理", "800"),
    ("punch down", "発酵した生地のガスを抜く", "動詞", "Punch down the dough once it has risen, then shape it into loaves.", "料理", "850"),
    ("laminate", "生地とバターを何層にも折り込む", "動詞", "Laminate the dough by folding it around the butter several times.", "料理", "950"),
    ("glaze", "つやを出すために表面を塗る", "動詞", "Glaze the donuts with a thin layer of icing while they're still warm.", "料理", "650"),
    ("dust", "粉や砂糖を薄くまぶす", "動詞", "Dust the cake with powdered sugar before serving.", "料理", "600"),
    ("pipe", "クリームや生地を絞り袋で絞り出す", "動詞", "Pipe the frosting onto the cupcakes in a spiral pattern.", "料理", "750"),
    ("crimp", "パイ生地の縁をひだ状に押さえて留める", "動詞", "Crimp the edges of the pie crust with a fork.", "料理", "850"),
    ("whip", "泡立てて空気を含ませる", "動詞", "Whip the cream until soft peaks form.", "料理", "550"),
    # --- 保存・仕上げの技法 ---
    ("brine", "塩水に漬け込む", "動詞", "Brine the turkey overnight for extra moisture and flavor.", "料理", "750"),
    ("cure", "塩や砂糖などで保存加工する", "動詞", "Cure the salmon with salt and sugar for two days.", "料理", "800"),
    ("pickle", "酢や塩水に漬ける", "動詞", "Pickle the cucumbers in vinegar, sugar, and dill.", "料理", "600"),
    ("render", "脂を加熱して溶かし出す", "動詞", "Render the bacon fat slowly over medium-low heat.", "料理", "800"),
    ("clarify", "バターの不純物を取り除いて澄ませる", "動詞", "Clarify the butter by skimming off the milk solids.", "料理", "900"),
    ("infuse", "風味を液体に染み込ませる", "動詞", "Infuse the cream with vanilla bean overnight.", "料理", "700"),
    ("steep", "熱い液体に浸して風味を出す", "動詞", "Steep the tea leaves in hot water for five minutes.", "料理", "650"),
    ("temper", "チョコレートなどの温度を調整して質感を整える", "動詞", "Temper the chocolate so it sets with a glossy finish.", "料理", "850"),
    ("rest", "調理後の肉を休ませて肉汁を落ち着かせる", "動詞", "Let the steak rest for five minutes before slicing.", "料理", "600"),
    ("baste", "焼き汁や油をかけながら焼く", "動詞", "Baste the turkey with pan juices every thirty minutes.", "料理", "700"),
    ("coat", "衣やソースをまんべんなくまとわせる", "動詞", "Coat the chicken pieces evenly in flour before frying.", "料理", "550"),
    ("dredge", "粉などを薄くまぶしつける", "動詞", "Dredge the fish fillets in seasoned flour before pan-frying.", "料理", "750"),
    ("sweat", "色をつけずに弱火でしんなりさせる", "動詞", "Sweat the onions in butter until soft and translucent.", "料理", "750"),
    ("shuck", "殻や皮をむく（牡蠣・トウモロコシなど）", "動詞", "Shuck the oysters carefully to avoid cutting yourself.", "料理", "700"),
]


# --- insertion --------------------------------------------------------------

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

    print(f"words: +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print("total words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
