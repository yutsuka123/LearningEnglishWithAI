# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated words and phrases for KITCHEN TOOLS & EQUIPMENT,
authored by Claude.

Focus (「料理」ドメインの手薄な領域を補強): 調理の「技法」ではなく、物理的な
道具・器具の語彙。包丁の種類、鍋・フライパンの種類、計量/下ごしらえ道具、
キッチン家電、収納・雑貨、そしてキッチンという空間そのもの（調理台・戸棚・
シンクなど）を体系的にカバーする。フレーズは、道具を借りる／使い方を説明する
／キッチン用品を買う／レシピの手順で道具に言及する、という4つの実用シーンを
中心に構成した。

`pot` / `spatula` / `whisk` / `wok` / `mortar and pestle` / `cleaver` / `sieve`
など、既存の「料理」ドメインに既に入っている道具語は再追加していない。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased), checked
against the ENTIRE `words`/`phrases` tables (not just this domain), so
overlap with other domains (e.g. rice cooker, kettle, apron, toaster,
microwave, dishwasher, faucet — already present elsewhere) is skipped safely
at insert time.

Run:  python scripts/add_kitchen_tools.py
      python scripts/add_kitchen_tools.py --missing-words   # report only

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
    "キッチン道具・調理器具": [
        # --- 道具を借りる ---
        ("Can I borrow your whisk for a second?", "泡立て器をちょっと貸してもらえますか？"),
        ("Do you have a can opener I could use?", "使える缶切りはありますか？"),
        ("Could you pass me the tongs?", "トングを取ってもらえますか？"),
        ("Is there a grater somewhere in the kitchen?", "キッチンのどこかにおろし金はありますか？"),
        ("Mind if I use your food processor?", "フードプロセッサーを使ってもいいですか？"),
        ("I forgot my measuring cups. Could I borrow yours?", "計量カップを忘れました。貸してもらえますか？"),
        ("Would you mind lending me your rolling pin?", "麺棒を貸していただけますか？"),
        ("I don't have a mandoline, so I'll just use a knife.", "スライサーがないので、包丁を使います。"),
        ("Could I borrow a cutting board? Mine's in the dishwasher.", "まな板を貸してもらえますか？私のは食洗機の中なので。"),
        # --- 使い方を説明する ---
        ("You just squeeze the garlic press like this.", "こんなふうにガーリックプレスを握るだけです。"),
        ("Set the pressure cooker for twenty minutes.", "圧力鍋を20分にセットしてください。"),
        ("Make sure to preheat the toaster oven before you put the bread in.", "パンを入れる前にトースターオーブンを予熱しておいてください。"),
        ("Just pulse it a few times in the blender.", "ブレンダーで数回パルスするだけでいいですよ。"),
        ("Hold the peeler at an angle and pull it toward you.", "皮むき器を斜めに持って手前に引いてください。"),
        ("Whisk it until the batter is smooth.", "生地がなめらかになるまで泡立ててください。"),
        ("Line the baking sheet with parchment paper first.", "まず天板にクッキングシートを敷いてください。"),
        ("Wrap the leftovers in plastic wrap before you put them in the fridge.", "残り物を冷蔵庫に入れる前にラップで包んでください。"),
        ("The immersion blender is great for pureeing soup right in the pot.", "ハンドブレンダーは鍋の中でそのままスープを裏ごしするのに便利です。"),
        ("Use the slotted spoon to lift the vegetables out of the water.", "野菜をお湯からすくい上げるのに穴あきお玉を使ってください。"),
        ("Drain the pasta in the colander.", "パスタをザルで湯切りしてください。"),
        ("Put on your oven mitts before you take that out.", "それを取り出す前にオーブンミトンをはめてください。"),
        # --- レシピの手順で道具に言及する ---
        ("Beat the eggs with a hand mixer for two minutes.", "卵をハンドミキサーで2分間泡立ててください。"),
        ("Chop the onions on the cutting board.", "まな板の上で玉ねぎを刻んでください。"),
        ("Simmer the sauce in a saucepan over low heat.", "弱火でソースパンにソースを煮込んでください。"),
        ("Pour the batter into a greased baking dish.", "生地に油を塗った耐熱皿に流し込んでください。"),
        ("Sear the steak in a hot skillet for two minutes per side.", "熱したスキレットでステーキを片面2分ずつ焼き固めてください。"),
        ("Weigh the flour on a kitchen scale for accuracy.", "正確を期すためキッチンスケールで小麦粉を量ってください。"),
        ("Cover the dutch oven and let it braise for two hours.", "ダッチオーブンにふたをして2時間煮込んでください。"),
        # --- キッチンという空間 ---
        ("There's no more room on the countertop.", "調理台にもうスペースがありません。"),
        ("Could you put the pasta in the pantry?", "パスタをパントリーに入れてもらえますか？"),
        ("The dishwasher is full again.", "食洗機がまた満杯です。"),
        ("Check the cupboard under the sink for a trivet.", "シンクの下の戸棚に鍋敷きがないか見てください。"),
        ("The range hood needs cleaning.", "レンジフードの掃除が必要です。"),
        ("Turn off the stovetop before you leave the kitchen.", "キッチンを出る前にコンロの火を消してください。"),
        ("Can you hand me the dish towel?", "ふきんを取ってもらえますか？"),
        ("This spice rack keeps everything organized.", "このスパイスラックですべて整理整頓できます。"),
        ("I keep my knives in a knife block on the counter.", "包丁はカウンターのナイフブロックにしまっています。"),
        ("Let the dishes dry in the dish rack overnight.", "食器は一晩水切りかごで乾かしてください。"),
        ("Throw the peels in the trash can.", "皮はゴミ箱に捨ててください。"),
    ],
    "調理器具の買い物": [
        ("I'm looking for a good chef's knife.", "良いシェフナイフを探しています。"),
        ("Do you sell stand mixers here?", "ここでスタンドミキサーは売っていますか？"),
        ("Which frying pan would you recommend for a beginner?", "初心者にはどのフライパンがおすすめですか？"),
        ("I need a new set of measuring spoons.", "計量スプーンの新しいセットが必要です。"),
        ("Is this coffee grinder easy to clean?", "このコーヒーミルは掃除が簡単ですか？"),
        ("How much is this air fryer?", "このエアフライヤーはいくらですか？"),
        ("I'd like to replace my old kettle with an electric one.", "古いやかんを電気ケトルに買い替えたいです。"),
        ("Do you carry cast iron skillets?", "鋳鉄製のスキレットは扱っていますか？"),
        ("This juicer looks a bit expensive.", "このジューサーは少し高そうですね。"),
        ("I'll take this cutting board and a set of kitchen shears.", "このまな板とキッチンばさみのセットをいただきます。"),
        ("Where can I find storage containers in this store?", "この店の保存容器はどこにありますか？"),
        ("Do you have any deep fryers in stock?", "揚げ物用フライヤーの在庫はありますか？"),
        ("I want a slow cooker that's not too big.", "あまり大きくないスロークッカーが欲しいです。"),
        ("Does this waffle iron come with a warranty?", "このワッフルメーカーには保証は付いていますか？"),
        ("Can I return this potato masher if it doesn't work well?", "うまく使えなかったらこのマッシャーは返品できますか？"),
        ("Do you have a garlic press that's dishwasher-safe?", "食洗機で洗えるガーリックプレスはありますか？"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 切る・下ごしらえの道具 ---
    ("knife", "包丁・ナイフ", "名詞", "Be careful, that knife is very sharp.", "料理", "300"),
    ("chef's knife", "シェフナイフ・牛刀", "名詞", "A chef's knife is the most versatile tool in the kitchen.", "料理", "450"),
    ("paring knife", "ペティナイフ", "名詞", "Use a paring knife to peel the apple.", "料理", "550"),
    ("bread knife", "パン切りナイフ", "名詞", "A bread knife has a serrated edge for slicing bread.", "料理", "550"),
    ("cutting board", "まな板", "名詞", "Chop the vegetables on the cutting board.", "料理", "350"),
    ("peeler", "皮むき器", "名詞", "Use a peeler to peel the potatoes quickly.", "料理", "450"),
    ("grater", "おろし金", "名詞", "Grate the cheese with a grater.", "料理", "450"),
    ("zester", "ゼスター（皮すりおろし器）", "名詞", "Use a zester to grate the lemon peel.", "料理", "800"),
    ("mandoline", "スライサー", "名詞", "A mandoline slices vegetables into even, thin pieces.", "料理", "850"),
    ("kitchen shears", "キッチンばさみ", "名詞", "I use kitchen shears to cut the chicken into pieces.", "料理", "700"),
    ("garlic press", "ガーリックプレス", "名詞", "Just squeeze the garlic press to mince the garlic.", "料理", "650"),
    # --- 鍋・フライパン類 ---
    ("frying pan", "フライパン", "名詞", "Heat some oil in the frying pan.", "料理", "300"),
    ("saucepan", "ソースパン・片手鍋", "名詞", "Simmer the sauce in a small saucepan.", "料理", "400"),
    ("stockpot", "寸胴鍋", "名詞", "Boil the broth in a large stockpot.", "料理", "600"),
    ("skillet", "スキレット", "名詞", "Sear the steak in a hot skillet.", "料理", "550"),
    ("dutch oven", "ダッチオーブン", "名詞", "Braise the beef in a dutch oven for two hours.", "料理", "700"),
    ("pressure cooker", "圧力鍋", "名詞", "The pressure cooker cuts the cooking time in half.", "料理", "600"),
    ("grill pan", "グリルパン", "名詞", "Cook the vegetables on a grill pan for those char marks.", "料理", "700"),
    ("griddle", "鉄板・グリドル", "名詞", "Cook the pancakes on a hot griddle.", "料理", "650"),
    ("roasting pan", "ロースト用鍋・天板", "名詞", "Put the turkey in the roasting pan.", "料理", "600"),
    ("baking sheet", "天板", "名詞", "Line the baking sheet with parchment paper.", "料理", "500"),
    ("baking dish", "耐熱皿・グラタン皿", "名詞", "Pour the batter into a greased baking dish.", "料理", "550"),
    ("casserole dish", "キャセロール皿", "名詞", "Bake the casserole in a covered casserole dish.", "料理", "650"),
    # --- 調理用ユーテンシル ---
    ("ladle", "お玉", "名詞", "Serve the soup with a ladle.", "料理", "500"),
    ("tongs", "トング", "名詞", "Use tongs to flip the meat on the grill.", "料理", "500"),
    ("slotted spoon", "穴あきお玉・スロテッドスプーン", "名詞", "Use a slotted spoon to lift the vegetables out of the broth.", "料理", "600"),
    ("rolling pin", "麺棒", "名詞", "Roll out the dough with a rolling pin.", "料理", "500"),
    ("colander", "水切りざる", "名詞", "Drain the pasta in a colander.", "料理", "600"),
    ("strainer", "こし器・ストレーナー", "名詞", "Pour the stock through a fine strainer.", "料理", "550"),
    ("funnel", "じょうご", "名詞", "Use a funnel to pour the oil into the bottle.", "料理", "500"),
    ("can opener", "缶切り", "名詞", "I can't find the can opener anywhere.", "料理", "450"),
    ("corkscrew", "コルク抜き", "名詞", "Do you have a corkscrew to open this wine?", "料理", "500"),
    ("pastry brush", "刷毛（はけ）", "名詞", "Brush the crust with egg wash using a pastry brush.", "料理", "650"),
    ("ice cream scoop", "アイスクリームスクープ", "名詞", "Scoop out the ice cream with an ice cream scoop.", "料理", "600"),
    ("potato masher", "マッシャー", "名詞", "Mash the potatoes with a potato masher.", "料理", "600"),
    ("salad spinner", "サラダスピナー", "名詞", "Dry the lettuce in a salad spinner.", "料理", "750"),
    ("meat tenderizer", "肉たたき", "名詞", "Pound the meat flat with a meat tenderizer.", "料理", "750"),
    # --- 計量・下ごしらえ道具 ---
    ("measuring cup", "計量カップ", "名詞", "Measure the flour with a measuring cup.", "料理", "400"),
    ("measuring spoon", "計量スプーン", "名詞", "Add a teaspoon of salt using a measuring spoon.", "料理", "450"),
    ("kitchen scale", "キッチンスケール", "名詞", "Weigh the flour on a kitchen scale for accuracy.", "料理", "550"),
    ("mixing bowl", "ボウル（混ぜる用）", "名詞", "Combine the ingredients in a large mixing bowl.", "料理", "400"),
    ("prep bowl", "下ごしらえ用ボウル", "名詞", "Keep your chopped vegetables in separate prep bowls.", "料理", "600"),
    ("meat thermometer", "肉用温度計", "名詞", "Check the chicken with a meat thermometer before serving.", "料理", "700"),
    ("kitchen timer", "キッチンタイマー", "名詞", "Set the kitchen timer for ten minutes.", "料理", "550"),
    # --- キッチン家電 ---
    ("blender", "ブレンダー・ミキサー", "名詞", "Blend the fruit in a blender until smooth.", "料理", "400"),
    ("food processor", "フードプロセッサー", "名詞", "Chop the nuts in a food processor.", "料理", "550"),
    ("stand mixer", "スタンドミキサー", "名詞", "Knead the dough in a stand mixer.", "料理", "650"),
    ("hand mixer", "ハンドミキサー", "名詞", "Beat the eggs with a hand mixer.", "料理", "600"),
    ("toaster oven", "オーブントースター", "名詞", "Toast the bread in the toaster oven.", "料理", "550"),
    ("electric kettle", "電気ケトル", "名詞", "Boil water quickly in the electric kettle.", "料理", "500"),
    ("immersion blender", "ハンドブレンダー", "名詞", "Puree the soup right in the pot with an immersion blender.", "料理", "850"),
    ("juicer", "ジューサー", "名詞", "Squeeze fresh orange juice with a juicer.", "料理", "550"),
    ("coffee maker", "コーヒーメーカー", "名詞", "Brew a pot of coffee in the coffee maker.", "料理", "500"),
    ("coffee grinder", "コーヒーミル", "名詞", "Grind the beans in a coffee grinder before brewing.", "料理", "600"),
    ("air fryer", "エアフライヤー", "名詞", "Cook the fries in an air fryer without oil.", "料理", "600"),
    ("slow cooker", "スロークッカー", "名詞", "Leave the stew in the slow cooker all day.", "料理", "600"),
    ("deep fryer", "揚げ物用フライヤー", "名詞", "Fry the chicken in a deep fryer at 180 degrees.", "料理", "650"),
    ("waffle iron", "ワッフルメーカー", "名詞", "Pour the batter into the waffle iron.", "料理", "650"),
    # --- 収納・雑貨 ---
    ("oven mitt", "オーブンミトン", "名詞", "Put on an oven mitt before taking out the hot pan.", "料理", "450"),
    ("dish towel", "台ふきん", "名詞", "Dry the plates with a dish towel.", "料理", "450"),
    ("plastic wrap", "ラップ", "名詞", "Cover the bowl with plastic wrap.", "料理", "450"),
    ("aluminum foil", "アルミホイル", "名詞", "Wrap the fish in aluminum foil before baking.", "料理", "450"),
    ("parchment paper", "クッキングシート", "名詞", "Line the pan with parchment paper so nothing sticks.", "料理", "600"),
    ("storage container", "保存容器", "名詞", "Keep the leftovers in a storage container.", "料理", "500"),
    ("ziplock bag", "ジップロック袋", "名詞", "Freeze the berries in a ziplock bag.", "料理", "500"),
    ("trivet", "鍋敷き", "名詞", "Set the hot pot down on a trivet.", "料理", "750"),
    ("spice rack", "スパイスラック", "名詞", "Keep the spices organized on a spice rack.", "料理", "650"),
    ("knife block", "ナイフブロック", "名詞", "Store your knives safely in a knife block.", "料理", "700"),
    ("dish rack", "水切りかご", "名詞", "Let the dishes dry in the dish rack.", "料理", "500"),
    # --- キッチンという空間 ---
    ("countertop", "調理台・カウンター", "名詞", "Clear off the countertop before you start cooking.", "料理", "500"),
    ("pantry", "パントリー・食料貯蔵室", "名詞", "Check the pantry for canned beans.", "料理", "500"),
    ("cupboard", "戸棚", "名詞", "Put the plates back in the cupboard.", "料理", "450"),
    ("stovetop", "コンロ", "名詞", "Turn off the stovetop before you leave the kitchen.", "料理", "500"),
    ("range hood", "レンジフード", "名詞", "Turn on the range hood while you're frying.", "料理", "700"),
    ("sink", "シンク", "名詞", "Wash your hands in the sink first.", "料理", "300"),
    ("trash can", "ゴミ箱", "名詞", "Throw the peels in the trash can.", "料理", "350"),
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
