# ruff: noqa: E501
"""林業・漁業ドメイン新設(2026-08-09)。

TODO.md「B20 工場・一次産業・手芸の語彙拡充」の一次産業部分に対応:
「一次産業: 農業／林業／漁業（既存「農業」ドメインの拡張＋林業・漁業は
新設）」。既存の`農業・園芸`domain(111語)は既にrice transplanter/
integrated pest management/hydroponics等、産業レベルの語彙が充実して
いたため、農業自体の追加はスコープ外とし、**存在しなかった`林業`・
`漁業`の2ドメインを新設**する。

Run:  python scripts/add_forestry_fishery_2026_08_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# (english, japanese, part_of_speech, example, domain, level)
WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 林業 ---
    ("logging", "伐採（木材を切り出す作業）", "名詞", "Logging in this forest is strictly regulated to prevent overharvesting.", "林業", "550"),
    ("clear-cutting", "皆伐（一区画の樹木をすべて伐採すること）", "名詞", "Clear-cutting removes every tree in an area at once.", "林業", "650"),
    ("selective logging", "択伐（特定の木だけを選んで伐採すること）", "名詞", "Selective logging removes only mature trees and leaves the rest of the forest intact.", "林業", "700"),
    ("reforestation", "再植林", "名詞", "Reforestation efforts have restored thousands of hectares of forest.", "林業", "600"),
    ("afforestation", "新規植林（元々森林でなかった土地への植林）", "名詞", "Afforestation projects turn barren land into new forest over time.", "林業", "700"),
    ("silviculture", "造林学（森林を育成・管理する技術）", "名詞", "Silviculture guides how foresters plant, thin, and harvest trees sustainably.", "林業", "800"),
    ("forester", "林業技術者・森林官", "名詞", "The forester marked which trees were ready for harvest.", "林業", "550"),
    ("lumberjack", "きこり（伐採作業員）", "名詞", "The lumberjack felled the tree with practiced precision.", "林業", "500"),
    ("chainsaw", "チェーンソー", "名詞", "He started the chainsaw and began cutting the fallen log into pieces.", "林業", "450"),
    ("timber", "材木・木材", "名詞", "The mill processes timber into lumber for construction.", "林業", "500"),
    ("lumber mill", "製材所", "名詞", "Logs are trucked to the lumber mill to be cut into boards.", "林業", "550"),
    ("log skidder", "ログスキッダー（丸太を運び出す林業用重機）", "名詞", "A log skidder drags felled trees out of the forest to the loading area.", "林業", "750"),
    ("canopy", "樹冠（森林の上部を覆う枝葉の層）", "名詞", "Sunlight barely reaches the forest floor through the dense canopy.", "林業", "600"),
    ("undergrowth", "下草・低木層", "名詞", "Thick undergrowth made it hard to walk through the forest.", "林業", "600"),
    ("forest floor", "林床", "名詞", "Fallen leaves decompose slowly on the forest floor.", "林業", "550"),
    ("old-growth forest", "原生林", "名詞", "Old-growth forest has never been logged and contains some very old trees.", "林業", "650"),
    ("sustainable forestry", "持続可能な林業", "名詞", "Sustainable forestry balances timber production with long-term forest health.", "林業", "700"),
    ("forest fire", "山火事", "名詞", "A forest fire swept through the dry hillside last summer.", "林業", "500"),
    ("prescribed burn", "計画的な野焼き（山火事予防等のための意図的な焼却）", "名詞", "Rangers use a prescribed burn to clear dry brush before wildfire season.", "林業", "750"),
    ("deforestation", "森林伐採（破壊的な意味合いを含む）", "名詞", "Deforestation has destroyed large areas of rainforest in recent decades.", "林業", "600"),
    ("national forest", "国有林", "名詞", "Camping is allowed in most parts of the national forest.", "林業", "550"),
    ("forest ranger", "森林保護官", "名詞", "The forest ranger patrols the trails looking for signs of illegal logging.", "林業", "550"),
    ("board foot", "ボードフィート（木材の体積単位）", "名詞", "Lumber in the US is often priced by the board foot.", "林業", "750"),
    ("girth", "幹周り（木の胴回り）", "名詞", "The old oak's girth suggested it was over two hundred years old.", "林業", "700"),
    ("coppicing", "台伐り（萌芽更新を利用した伐採・育林法）", "名詞", "Coppicing lets the same tree stump regrow new shoots after cutting.", "林業", "800"),
    # --- 漁業 ---
    ("fisherman", "漁師", "名詞", "The fisherman set out before dawn to check his nets.", "漁業", "400"),
    ("fishing vessel", "漁船", "名詞", "The fishing vessel returned to port loaded with tuna.", "漁業", "450"),
    ("trawler", "トロール船", "名詞", "A trawler drags a large net along the ocean floor to catch fish.", "漁業", "600"),
    ("trawling", "トロール漁法", "名詞", "Bottom trawling can damage fragile habitats on the seafloor.", "漁業", "700"),
    ("gillnet", "刺し網", "名詞", "Fish get caught in the gillnet as they try to swim through.", "漁業", "700"),
    ("longline", "はえ縄（一本の幹縄に多数の釣り針を付けた漁具）", "名詞", "A longline can stretch for miles and carry thousands of hooks.", "漁業", "750"),
    ("purse seine", "巻き網", "名詞", "A purse seine encircles a school of fish before the bottom is drawn closed.", "漁業", "800"),
    ("aquaculture", "養殖業", "名詞", "Aquaculture now supplies more than half of the fish eaten worldwide.", "漁業", "650"),
    ("fish farm", "養殖場", "名詞", "The fish farm raises salmon in large offshore pens.", "漁業", "500"),
    ("hatchery", "孵化場", "名詞", "Young salmon are raised at the hatchery before being released into the river.", "漁業", "600"),
    ("bycatch", "混獲（狙っていない魚介類が網にかかること）", "名詞", "Bycatch of dolphins remains a serious concern in some fisheries.", "漁業", "700"),
    ("overfishing", "乱獲", "名詞", "Overfishing has caused several cod populations to collapse.", "漁業", "550"),
    ("fishing quota", "漁獲割当量", "名詞", "Each boat must stay within its annual fishing quota.", "漁業", "650"),
    ("catch limit", "漁獲制限", "名詞", "Regulators lowered the catch limit to help the population recover.", "漁業", "600"),
    ("sustainable fishery", "持続可能な漁業", "名詞", "A sustainable fishery is managed so fish stocks can replenish naturally.", "漁業", "650"),
    ("fish stock", "資源量（漁業対象となる魚の個体群）", "名詞", "Scientists monitor fish stocks to set safe catch limits.", "漁業", "650"),
    ("spawning ground", "産卵場", "名詞", "Dams have blocked salmon from reaching their traditional spawning grounds.", "漁業", "700"),
    ("migratory fish", "回遊魚", "名詞", "Migratory fish like salmon travel between freshwater and the ocean.", "漁業", "650"),
    ("fish market", "魚市場", "名詞", "The fish market opens before sunrise for the daily auction.", "漁業", "450"),
    ("seafood processing plant", "水産加工場", "名詞", "The catch is delivered fresh to the seafood processing plant each morning.", "漁業", "600"),
    ("ice hold", "魚倉（漁獲物を氷で冷やして保管する船内の区画）", "名詞", "Fish are stored in the ice hold to stay fresh during the trip back to port.", "漁業", "700"),
    ("net mending", "網の修繕", "名詞", "Fishermen spend the off-season net mending and repairing gear.", "漁業", "650"),
    ("fishing net", "漁網", "名詞", "The crew hauled in the fishing net, heavy with the day's catch.", "漁業", "450"),
    ("coastal fishing", "沿岸漁業", "名詞", "Coastal fishing relies on smaller boats that stay close to shore.", "漁業", "600"),
    ("deep-sea fishing", "遠洋漁業", "名詞", "Deep-sea fishing trips can last for weeks at a time far from land.", "漁業", "600"),
    ("fish auction", "魚のセリ", "名詞", "Buyers gather early for the fish auction at the port.", "漁業", "550"),
]

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "林業の英語": [
        ("How old do you think this tree is, based on its girth?", "この木は幹周りからすると、どれくらいの樹齢だと思いますか。"),
        ("The company promised to replant every tree it logs.", "その会社は伐採した分だけ植林することを約束しました。"),
        ("We hiked through an old-growth forest that's never been logged.", "一度も伐採されたことのない原生林の中をハイキングしました。"),
        ("Rangers set a prescribed burn to reduce wildfire risk.", "レンジャーたちは山火事のリスクを減らすため計画的な野焼きを行いました。"),
        ("The lumberjack felled the tree in exactly the direction he planned.", "きこりは狙い通りの方向に木を倒しました。"),
        ("Deforestation in the region has slowed compared to a decade ago.", "この地域の森林伐採は10年前と比べて減速しています。"),
        ("Sustainable forestry certification means the wood came from a responsibly managed forest.", "持続可能な林業認証は、その木材が責任を持って管理された森林から来たことを意味します。"),
        ("Sunlight barely reaches the ground through such a dense canopy.", "これほど密な樹冠を通しては、日光がほとんど地面に届きません。"),
    ],
    "漁業の英語": [
        ("How big was your catch this morning?", "今朝の漁獲量はどれくらいでしたか。"),
        ("The boat stayed within its fishing quota for the season.", "その船は今シーズンの漁獲割当量内に収まりました。"),
        ("Overfishing has pushed several species toward collapse.", "乱獲により複数の魚種が枯渇の危機に瀕しています。"),
        ("The salmon are heading upstream to their spawning grounds.", "サケは産卵場を目指して川を遡っています。"),
        ("Bycatch is one of the biggest challenges in commercial fishing.", "混獲は商業漁業における最大の課題の一つです。"),
        ("This restaurant only serves fish from certified sustainable fisheries.", "このレストランは認証された持続可能な漁業由来の魚だけを提供しています。"),
        ("The crew spent the whole afternoon net mending.", "乗組員は午後いっぱい網の修繕に費やしました。"),
        ("Fresh catch goes straight from the boat to the fish market.", "獲れたての魚はそのまま船から魚市場へ運ばれます。"),
    ],
}


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
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

        ph_added = ph_skipped = 0
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in ph_existing:
                    ph_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                ph_existing.add(en.lower())
                ph_added += 1

    print(f"words: +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
