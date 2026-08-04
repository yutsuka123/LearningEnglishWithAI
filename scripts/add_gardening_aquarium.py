# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add vocabulary + phrases for HOME GARDENING and AQUARIUM KEEPING, authored
by Claude (2026-08-04・ユーザー要望).

家庭菜園・ガーデニングの語彙(道具、剪定・株分けの基本テクニック、育成条件)と、
淡水/海水アクアリウムの語彙(立ち上げ・水質管理・ろ過・レイアウト)をまとめて
追加する。これは「単語を教える」ための語彙コンテンツであり、特定の植物種や
魚種の飼育マニュアルではない。

ドメインについて: 既存の `農業・園芸` ドメイン(add_agriculture.py)は稲作・畑作
など農業寄りの語彙が中心で、`植物` ドメイン(add_plants_expanded.py)は樹木や
花・植物生理学の語彙が中心。どちらも家庭のガーデニング道具・テクニックや
アクアリウムには手薄なため、新ドメイン `園芸・アクアリウム` を導入する。

既存語との重複について: 以下はDB全体を事前にgrepし、既に別ドメインに全く
同じ英単語(大文字小文字無視)で存在することを確認した。意味が近く同じ
ドメインが適切なもの(fertilizer/compost/mulch/pruning/perennial/trellis/
raised bed/potting soil ─ 農業・園芸/植物ドメインに既存)は、WORDSへの
再登録はせず、代わりにPHRASESの自然な例文の中で扱った。一方、既存語と
意味が異なる同綴りの語(annual=ビジネス「年次の」、cutting=機械「切削」、
propagation=IT「電波伝搬」、substrate=化学/半導体「基質・基板」、
invertebrate=動物「無脊椎動物」全般)は、より具体的な複合語
(annual flower / stem cutting / plant propagation / aquarium substrate /
aquatic invertebrate)に言い換えて衝突を避けつつ同じ概念をカバーした。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased), checked
against the entire `words` / `phrases` tables.

Run:  python scripts/add_gardening_aquarium.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "園芸・アクアリウム"
SCENE = "園芸・アクアリウムの英語"

# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # === 家庭菜園・ガーデニング (home gardening) ===
    ("trowel", "移植ごて", "名詞", "She used a small trowel to dig a hole for the seedling.", DOMAIN, "500"),
    ("wheelbarrow", "一輪車・手押し車", "名詞", "He pushed a wheelbarrow full of soil across the yard.", DOMAIN, "500"),
    ("spade", "スコップ・シャベル", "名詞", "Use a spade to turn over the heavy clay soil.", DOMAIN, "500"),
    ("watering can", "じょうろ", "名詞", "Fill the watering can and give the tomatoes a drink.", DOMAIN, "400"),
    ("garden hose", "散水用ホース", "名詞", "Coil the garden hose neatly after you finish watering.", DOMAIN, "450"),
    ("gardening gloves", "園芸用手袋・ガーデニンググローブ", "名詞", "Put on your gardening gloves before you handle the roses.", DOMAIN, "400"),
    ("seed packet", "種の袋・種子パケット", "名詞", "The seed packet lists the best month to sow outdoors.", DOMAIN, "450"),
    ("drainage", "排水・水はけ", "名詞", "Add some gravel to the pot's bottom to improve drainage.", DOMAIN, "650"),
    ("annual flower", "一年草の花", "名詞", "Marigolds are a popular annual flower that blooms all summer.", DOMAIN, "600"),
    ("deadheading", "花がら摘み(咲き終わった花を摘み取る作業)", "名詞", "Deadheading spent blooms encourages the plant to flower again.", DOMAIN, "700"),
    ("pruning shears", "剪定ばさみ", "名詞", "Sharpen your pruning shears before you cut back the hedge.", DOMAIN, "600"),
    ("stem cutting", "挿し木・茎の切り穂", "名詞", "You can grow a whole new plant from a single stem cutting.", DOMAIN, "700"),
    ("plant propagation", "植物の繁殖・増殖", "名詞", "Plant propagation from cuttings is cheaper than buying new seedlings.", DOMAIN, "750"),
    ("root-bound", "根詰まりした", "形容詞", "The fern had become root-bound and needed a bigger pot.", DOMAIN, "750"),
    ("transplant shock", "植え替えショック", "名詞", "Water it deeply after moving it outside to reduce transplant shock.", DOMAIN, "800"),
    ("companion planting", "コンパニオンプランツ・混植", "名詞", "Companion planting basil next to tomatoes is said to keep pests away.", DOMAIN, "800"),
    ("hardiness zone", "耐寒性ゾーン(栽培適地の指標)", "名詞", "Check your hardiness zone before ordering plants online.", DOMAIN, "850"),
    ("native plant", "在来植物・自生種", "名詞", "Native plants usually need less water than imported varieties.", DOMAIN, "700"),
    ("peat moss", "ピートモス", "名詞", "Mix peat moss into the soil to help it hold moisture.", DOMAIN, "750"),
    ("no-dig gardening", "不耕起栽培", "名詞", "No-dig gardening builds up layers of compost instead of tilling the soil.", DOMAIN, "850"),
    ("blight", "疫病・立ち枯れ病", "名詞", "Blight spread quickly through the potato patch after the rain.", DOMAIN, "750"),
    ("aphid infestation", "アブラムシの大量発生", "名詞", "An aphid infestation left a sticky residue on the rose leaves.", DOMAIN, "700"),
    ("overwinter", "冬を越す・越冬させる", "動詞", "Bring the geraniums indoors so they can overwinter in the garage.", DOMAIN, "750"),
    ("leggy", "(植物が)徒長した", "形容詞", "The seedlings grew leggy from not getting enough light.", DOMAIN, "800"),
    ("bolting", "とう立ち(早期に花芽をつけてしまうこと)", "名詞", "Hot weather caused the lettuce to start bolting.", DOMAIN, "800"),
    # === 熱帯魚・アクアリウム (freshwater / saltwater aquarium keeping) ===
    ("fish tank", "水槽", "名詞", "We set up a small fish tank in the living room.", DOMAIN, "400"),
    ("water change", "水換え", "名詞", "A weekly water change keeps the ammonia level under control.", DOMAIN, "600"),
    ("gravel", "砂利(水槽用の底砂)", "名詞", "Rinse the gravel thoroughly before adding it to the tank.", DOMAIN, "450"),
    ("driftwood", "流木", "名詞", "The driftwood slowly released tannins that tinted the water brown.", DOMAIN, "600"),
    ("betta fish", "ベタ・闘魚", "名詞", "A betta fish should usually be kept alone, not with other bettas.", DOMAIN, "500"),
    ("guppy", "グッピー", "名詞", "Guppies breed so quickly that the tank filled up within months.", DOMAIN, "450"),
    ("air pump", "エアポンプ", "名詞", "The air pump keeps the water oxygenated for the fish.", DOMAIN, "500"),
    ("filtration", "ろ過", "名詞", "Good filtration removes waste before it builds up in the tank.", DOMAIN, "700"),
    ("aquarium substrate", "水槽の底砂・基質", "名詞", "Sand makes a finer aquarium substrate than coarse gravel.", DOMAIN, "650"),
    ("tank cycling", "水槽の立ち上げ(サイクリング)", "名詞", "Tank cycling can take four to six weeks before it's safe to add fish.", DOMAIN, "800"),
    ("nitrogen cycle", "窒素循環", "名詞", "Understanding the nitrogen cycle is the first step in keeping fish alive.", DOMAIN, "850"),
    ("water hardness", "水の硬度", "名詞", "Water hardness affects which fish species will thrive in your tank.", DOMAIN, "800"),
    ("pH balance", "pHバランス", "名詞", "Sudden swings in pH balance can seriously stress your fish.", DOMAIN, "750"),
    ("live rock", "ライブロック", "名詞", "Live rock introduces beneficial bacteria into a new saltwater tank.", DOMAIN, "800"),
    ("quarantine tank", "検疫用水槽・隔離用タンク", "名詞", "New fish should sit in a quarantine tank before joining the main tank.", DOMAIN, "800"),
    ("fin rot", "尾ぐされ病", "名詞", "Fin rot often starts as ragged, discolored edges on the fins.", DOMAIN, "800"),
    ("algae bloom", "藻類の大量発生", "名詞", "Too much light triggered an algae bloom that turned the water green.", DOMAIN, "750"),
    ("tankmates", "混泳相手の魚", "名詞", "Choose peaceful tankmates that won't bully the smaller fish.", DOMAIN, "650"),
    ("aquascaping", "アクアスケイピング(水景づくり)", "名詞", "Aquascaping treats the tank like a miniature underwater landscape.", DOMAIN, "800"),
    ("canister filter", "外部フィルター(キャニスターフィルター)", "名詞", "A canister filter sits outside the tank and pumps the water through it.", DOMAIN, "750"),
    ("protein skimmer", "プロテインスキマー", "名詞", "A protein skimmer pulls organic waste out before it can decay in the water.", DOMAIN, "900"),
    ("brackish water", "汽水", "名詞", "Brackish water is a mix of fresh and salt water found in estuaries.", DOMAIN, "800"),
    ("aquatic invertebrate", "水生無脊椎動物", "名詞", "Shrimp are a popular aquatic invertebrate for planted tanks.", DOMAIN, "800"),
    ("beneficial bacteria", "有益なバクテリア(ろ過バクテリア)", "名詞", "Beneficial bacteria convert toxic ammonia into safer compounds.", DOMAIN, "800"),
    ("acclimate", "(水温などに)慣らす", "動詞", "Float the bag for fifteen minutes to let the fish acclimate to the water temperature.", DOMAIN, "750"),
]

# --- phrases: (english, japanese) -------------------------------------------

PHRASES: list[tuple[str, str]] = [
    # --- 家庭菜園・ガーデニング ---
    ("How often should I water this?", "これはどのくらいの頻度で水をあげればいいですか？"),
    ("My plant's leaves are turning yellow.", "うちの植物の葉が黄色くなってきました。"),
    ("Have you added any fertilizer this month?", "今月は肥料をあげましたか？"),
    ("I mixed some compost into the soil before planting.", "植えつける前に土に堆肥を混ぜ込みました。"),
    ("Could you spread some mulch around the base?", "根元にマルチを敷いてもらえますか？"),
    ("It's about time we pruned the roses back.", "そろそろバラを剪定する時期ですね。"),
    ("This perennial comes back bigger every spring.", "この多年草は毎年春になるとさらに大きくなって咲きます。"),
    ("We built a raised bed for the vegetables.", "野菜用にレイズドベッド(盛り土花壇)を作りました。"),
    ("Can you train the vine up this trellis?", "このトレリスに沿ってつるを誘引してもらえますか？"),
    ("Which potting soil do you recommend for succulents?", "多肉植物にはどの培養土がおすすめですか？"),
    # --- アクアリウム ---
    ("Is this tank fully cycled yet?", "この水槽はもう完全にサイクリングが終わっていますか？"),
    ("What's the pH of your water?", "水のpHはいくつですか？"),
    ("I need to do a water change this weekend.", "今週末は水換えをしないといけません。"),
    ("How many fish can this tank hold?", "この水槽には何匹くらい魚を入れられますか？"),
    ("One of the fish looks like it has fin rot.", "1匹の魚が尾ぐされ病にかかっているようです。"),
    ("The water's gone cloudy — is that normal?", "水が濁ってきたんですが、これは普通のことですか？"),
    ("Do these two species make good tankmates?", "この2種は混泳相手として相性がいいですか？"),
    ("I picked up a canister filter for the new tank.", "新しい水槽用に外部フィルターを買いました。"),
    ("Should I quarantine the new fish before adding them?", "新しい魚は入れる前に検疫用水槽に入れたほうがいいですか？"),
    ("The glass is covered in algae again.", "またガラス面が藻だらけになっています。"),
]


def main() -> int:
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
        for en, ja in PHRASES:
            if en.lower() in ph_existing:
                ph_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, ?)",
                (en, ja, SCENE),
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
