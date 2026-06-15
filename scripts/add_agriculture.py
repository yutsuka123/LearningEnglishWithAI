# ruff: noqa: E501
"""Agriculture & horticulture vocabulary. Authored by Claude — no app/OpenAI
API calls. Dedupe on english; back-fill examples. domain="農業・園芸".
Run: python scripts/add_agriculture.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

GROUPS: dict[str, tuple[str, list[tuple[str, str, str]]]] = {
    "農業・作物": ("600", [
        ("agriculture", "農業", "Agriculture feeds the world."),
        ("planting", "作付け・植え付け", "Spring is the time for planting."),
        ("paddy field", "田んぼ・水田", "Rice grows in a flooded paddy field."),
        ("field (farm)", "畑", "The farmer plowed the field."),
        ("harvest", "収穫", "The rice harvest begins in autumn."),
        ("crop", "作物", "Wheat is an important crop."),
        ("rice plant", "稲", "The rice plant turns golden when ripe."),
        ("wheat", "小麦", "Bread is made from wheat."),
        ("barley", "大麦", "Barley is used to brew beer."),
        ("rye", "ライ麦", "Rye bread has a dark color."),
        ("corn", "とうもろこし", "The cornfield stretched for miles."),
        ("cornfield", "とうもろこし畑", "Crows gathered over the cornfield."),
        ("potato field", "ジャガイモ畑", "They dug potatoes from the field."),
        ("threshing", "脱穀", "Threshing separates the grain from the stalk."),
        ("seed rice", "種籾(たねもみ)", "The seed rice is soaked before sowing."),
        ("rice planting", "田植え", "Rice planting is hard, wet work."),
        ("seedling", "苗", "Each seedling is set into the mud."),
        ("nursery bed", "苗床", "Seedlings are raised in a nursery bed."),
        ("germination", "発芽", "Warmth speeds up germination."),
        ("sprout", "芽・芽吹く", "Tiny sprouts pushed through the soil."),
        ("leaf blight", "葉枯れ病・葉焼け", "Leaf blight damaged the wheat."),
        ("crop rotation", "輪作", "Crop rotation keeps the soil healthy."),
        ("fallow", "休耕(地)", "The field was left fallow for a year."),
        ("irrigation", "灌漑(かんがい)", "Irrigation brings water to dry fields."),
    ]),
    "肥料・栽培": ("700", [
        ("fertilizer", "肥料", "Fertilizer helps the crops grow."),
        ("fertilization", "施肥", "Proper fertilization boosts the yield."),
        ("nitrogen", "窒素", "Nitrogen helps leaves grow green."),
        ("phosphate", "リン酸", "Phosphate supports root growth."),
        ("potash", "カリ・カリウム肥料", "Potash strengthens the plant."),
        ("compost", "堆肥(たいひ)", "Compost enriches the garden soil."),
        ("manure", "肥やし・厩肥", "Farmers spread manure on the field."),
        ("soil", "土壌", "Healthy soil grows strong plants."),
        ("hydroponics", "水耕栽培", "Hydroponics grows plants without soil."),
        ("organic farming", "有機栽培", "Organic farming avoids synthetic chemicals."),
        ("pesticide", "農薬・殺虫剤", "Pesticide controls harmful insects."),
        ("pesticide-free", "無農薬の", "They sell pesticide-free vegetables."),
        ("pest", "害虫", "Pests can ruin a whole crop."),
        ("weed", "雑草", "Pull the weeds before they spread."),
        ("mulch", "マルチ・敷きわら", "Mulch keeps the soil moist."),
        ("yield", "収量・収穫高", "Good weather raised the yield."),
    ]),
    "機械・園芸": ("600", [
        ("combine harvester", "コンバイン", "A combine harvester cuts and threshes grain."),
        ("rice transplanter", "田植機", "The rice transplanter sets seedlings in rows."),
        ("tractor", "トラクター", "The tractor pulled the plow."),
        ("plow", "鋤(すき)・耕す", "He plowed the field before planting."),
        ("cowshed", "牛舎", "The cows return to the cowshed at night."),
        ("greenhouse", "ビニールハウス・温室", "Tomatoes grow well in a greenhouse."),
        ("vegetable garden", "菜園", "She keeps a small vegetable garden."),
        ("horticulture", "園芸", "Horticulture is the art of growing plants."),
        ("gardening", "ガーデニング", "Gardening is a relaxing hobby."),
        ("ridge", "畝(うね)", "Seeds are sown along each ridge."),
        ("stake", "支柱", "Tie the tomato plant to a stake."),
        ("pruning", "剪定(せんてい)", "Pruning shapes the fruit tree."),
        ("grafting", "接ぎ木", "Grafting joins two plants into one."),
        ("transplant", "移植する", "Transplant the seedlings into pots."),
        ("bulb", "球根", "Plant the tulip bulb in autumn."),
        ("watering", "水やり", "The garden needs daily watering in summer."),
        ("flower bed", "花壇", "She planted roses in the flower bed."),
    ]),
}


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = filled = 0
        per_group: dict[str, int] = {}
        for group, (level, items) in GROUPS.items():
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
                    (en, ja, "", ex, "農業・園芸", level),
                )
                existing.add(en.lower())
                added += 1
                per_group[group] = per_group.get(group, 0) + 1
    print(f"words: +{added} (例文補充 {filled})  {per_group}")
    with db() as conn:
        print("単語総数:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
