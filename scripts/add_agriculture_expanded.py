# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""Top up the existing 農業・園芸(agriculture/horticulture) domain, authored
by Claude (2026-08-05・ユーザー要望:「農業園芸の英単語を充実化したいです。
農機、家庭菜園の器具、農業用語、農政用語、干拓、減反、農薬用語、間引き、
水張り、米、麦、じゃがいも、とうもろこしなどの各工程」).

既存の47語は栽培の基本(irrigation/compost/pruning/paddy field等)中心で、
(1) 農機(トラクター以外の播種機・防除機等)、(2) 家庭菜園の手工具、
(3) 農政・農業政策用語、(4) 干拓・減反という日本の農業史に特有の語、
(5) 農薬の分類語、(6) 間引き・水張りという作業工程、(7) 米/麦/じゃがいも/
とうもろこしそれぞれの生育・収穫工程語、が欠けていた。これを補強する。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words`
table (tractor/irrigation/pesticide/compost/pruning等は既存のためスキップ
される想定)。

Run:  python scripts/add_agriculture_expanded.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

D = "農業・園芸"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 農機 ---
    ("cultivator", "耕耘機・カルチベーター", "名詞", "The cultivator breaks up the soil before the seeds are sown.", D, "600"),
    ("seeder", "播種機", "名詞", "The seeder plants rows of seeds at an even depth and spacing.", D, "700"),
    ("crop sprayer", "防除機・スプレーヤー", "名詞", "The crop sprayer applies pesticide evenly across the whole field.", D, "700"),
    ("grain dryer", "穀物乾燥機", "名詞", "The grain dryer lowers the moisture in the rice before it is stored.", D, "750"),
    ("rice husker", "籠摺り機・脱穀後の精米機", "名詞", "The rice husker removes the outer husk from each grain.", D, "800"),
    ("hay baler", "牧草梱包機・ベーラー", "名詞", "The hay baler compresses cut grass into tight round bales.", D, "800"),
    ("agricultural machinery", "農業機械・農機", "名詞", "The cooperative shares expensive agricultural machinery among several farms.", D, "600"),
    # --- 家庭菜園の器具 ---
    ("garden trowel", "移植ごて", "名詞", "She used a garden trowel to plant the seedlings.", D, "500"),
    ("garden fork", "熊手・ガーデンフォーク", "名詞", "A garden fork loosens compacted soil better than a spade.", D, "550"),
    ("hoe", "鍬（くわ）", "名詞", "He used a hoe to clear weeds between the rows.", D, "500"),
    ("pruning shears", "剪定ばさみ", "名詞", "Pruning shears make a clean cut that helps the plant heal quickly.", D, "600"),
    ("watering can", "水やり用のじょうろ", "名詞", "She filled the watering can and gave each pot a little water.", D, "400"),
    ("wheelbarrow", "手押し車・一輪車", "名詞", "He loaded the compost into a wheelbarrow and pushed it to the garden.", D, "500"),
    ("garden hose", "散水用ホース", "名詞", "The garden hose reaches every bed without needing to be moved.", D, "450"),
    ("raised bed", "レイズドベッド（囲い花壇）", "名詞", "A raised bed drains better and keeps soil pests out of reach.", D, "650"),
    ("cold frame", "コールドフレーム（簡易温室）", "名詞", "A cold frame protects young seedlings from frost in early spring.", D, "750"),
    # --- 農業用語（一般） ---
    ("crop yield", "収穫量・収量", "名詞", "Better irrigation increased the crop yield by nearly twenty percent.", D, "650"),
    ("arable land", "耕作可能な土地", "名詞", "Only a small share of the country's land is arable.", D, "750"),
    ("crop failure", "不作・収穫の失敗", "名詞", "A long drought caused a crop failure across the whole region.", D, "700"),
    ("monoculture", "単一栽培・モノカルチャー", "名詞", "Monoculture makes a farm more efficient but more vulnerable to disease.", D, "800"),
    ("agricultural cooperative", "農業協同組合", "名詞", "The agricultural cooperative helps small farmers sell their produce together.", D, "750"),
    ("farmland consolidation", "農地の集約化", "名詞", "Farmland consolidation combines small plots into larger, more efficient fields.", D, "850"),
    # --- 農政用語 ---
    ("agricultural policy", "農業政策・農政", "名詞", "Agricultural policy decides how much support farmers receive each year.", D, "750"),
    ("food self-sufficiency rate", "食料自給率", "名詞", "The country's food self-sufficiency rate has fallen over the past decades.", D, "800"),
    ("agricultural subsidy", "農業補助金", "名詞", "An agricultural subsidy helps farmers survive years of low prices.", D, "700"),
    ("farmland zoning", "農地の区分（ゾーニング）", "名詞", "Farmland zoning restricts how agricultural land can be used or sold.", D, "850"),
    ("agricultural census", "農業統計調査・農業センサス", "名詞", "The agricultural census is carried out every few years to track farm numbers.", D, "800"),
    # --- 干拓 ---
    ("land reclamation", "干拓・埋め立てによる造成", "名詞", "Land reclamation turned the shallow bay into new farmland.", D, "800"),
    ("reclaimed land", "干拓地・埋立地", "名詞", "Rice has been grown on this reclaimed land for over a century.", D, "800"),
    ("drainage (agriculture)", "排水（農業）", "名詞", "Good drainage keeps the roots from rotting in heavy rain.", D, "700"),
    ("polder", "ポルダー（干拓地）", "名詞", "A polder is farmland reclaimed from the sea and protected by dikes.", D, "900"),
    ("levee", "堤防", "名詞", "The levee keeps the river from flooding the surrounding fields.", D, "750"),
    # --- 減反 ---
    ("acreage reduction", "減反", "名詞", "The government's acreage reduction policy paid farmers to grow less rice.", D, "850"),
    ("production adjustment", "生産調整", "名詞", "Production adjustment aims to keep rice prices from falling too far.", D, "850"),
    ("set-aside land", "休耕地・減反した土地", "名詞", "Set-aside land is left unplanted for a season under the program.", D, "850"),
    # --- 農薬用語 ---
    ("insecticide", "殺虫剤", "名詞", "The insecticide protects the cabbage from caterpillars.", D, "650"),
    ("herbicide", "除草剤", "名詞", "The farmer sprayed herbicide along the edges of the field.", D, "700"),
    ("fungicide", "殺菌剤", "名詞", "A fungicide is applied before the rainy season to prevent blight.", D, "750"),
    ("agricultural chemical", "農薬（総称）", "名詞", "Every agricultural chemical must be tested for safety before it is sold.", D, "700"),
    ("pesticide residue", "残留農薬", "名詞", "Inspectors test the vegetables for pesticide residue before they reach the market.", D, "800"),
    ("integrated pest management", "総合的病害虫管理（IPM）", "名詞", "Integrated pest management combines natural predators with limited chemical use.", D, "900"),
    ("pre-harvest interval", "使用禁止期間（収穫前）", "名詞", "The pre-harvest interval is the minimum time between spraying and harvest.", D, "900"),
    # --- 間引き・水張り ---
    ("thinning (crops)", "間引き", "名詞", "Thinning leaves fewer, stronger seedlings with more room to grow.", D, "700"),
    ("paddy flooding", "水張り（田んぼへの)", "名詞", "Paddy flooding softens the soil and prepares it for transplanting.", D, "800"),
    ("puddling (soil)", "田起こし後の代掻き・攪土", "名詞", "Puddling mixes the flooded soil into a smooth, even layer.", D, "900"),
    ("water management (paddy)", "水管理（水田の）", "名詞", "Careful water management keeps the paddy at the right depth all season.", D, "850"),
    # --- 米の各工程 ---
    ("rice nursery", "苗代（稲の育苗場）", "名詞", "Rice seedlings are grown in a rice nursery before they are transplanted.", D, "800"),
    ("rice seedling", "稲の苗", "名詞", "Each rice seedling is planted by hand or by a transplanter.", D, "700"),
    ("heading stage", "出穂期", "名詞", "The heading stage is when the rice plant's ears first appear.", D, "850"),
    ("ripening stage", "登熟期", "名詞", "During the ripening stage, the grains fill and turn golden.", D, "850"),
    ("rice husk", "稲殻・籾殻", "名詞", "Rice husk removed during milling is often used as fertilizer.", D, "750"),
    ("rice milling", "精米", "名詞", "Rice milling removes the husk and bran to produce white rice.", D, "800"),
    # --- 麦の各工程 ---
    ("wheat sowing", "麦の種まき", "名詞", "Wheat sowing usually takes place in the autumn in this region.", D, "700"),
    ("wheat harvest", "麦の収穫", "名詞", "The wheat harvest begins as soon as the ears turn golden brown.", D, "700"),
    ("wheat field", "麦畑", "名詞", "The wheat field stretched all the way to the hills.", D, "500"),
    # --- じゃがいもの各工程 ---
    ("seed potato", "種イモ", "名詞", "Farmers cut each seed potato into pieces with at least one eye.", D, "750"),
    ("potato hilling", "培土（じゃがいもの）", "名詞", "Potato hilling piles soil around the stem as the plant grows.", D, "800"),
    ("potato harvesting", "じゃがいもの収穫", "名詞", "Potato harvesting is done after the leaves above ground have died back.", D, "700"),
    # --- とうもろこしの各工程 ---
    ("corn sowing", "とうもろこしの種まき", "名詞", "Corn sowing takes place once the soil has warmed in spring.", D, "700"),
    ("corn pollination", "とうもろこしの授粉", "名詞", "Corn pollination happens when pollen from the tassel falls onto the silk below.", D, "850"),
    ("silage", "サイレージ（発酵飼料）", "名詞", "The whole corn plant is chopped and stored as silage for winter feed.", D, "850"),
]


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
