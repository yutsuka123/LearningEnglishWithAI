# ruff: noqa: E501
"""Animals: common insects/pests + more animals. Authored by Claude — no
app/OpenAI API calls. Dedupe on english; back-fill examples. domain="動物".
Run: python scripts/add_animals2.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

GROUPS: dict[str, list[tuple[str, str, str]]] = {
    "昆虫・害虫": [
        ("cockroach", "ゴキブリ", "Cockroaches scurry away from the light."),
        ("mosquito", "蚊", "A mosquito bit me on the arm."),
        ("fly", "ハエ", "A fly buzzed around the food."),
        ("housefly", "イエバエ", "A housefly landed on the table."),
        ("bee", "ハチ・ミツバチ", "A bee gathered nectar from the flower."),
        ("wasp", "スズメバチ・アシナガバチ", "A wasp can sting more than once."),
        ("hornet", "スズメバチ", "A hornet's sting is very painful."),
        ("horsefly", "アブ", "A horsefly bit the grazing cow."),
        ("stink bug", "カメムシ", "A stink bug gives off a foul smell."),
        ("mite", "ダニ(微小)", "Dust mites live in bedding."),
        ("tick", "マダニ", "A tick can carry disease."),
        ("flea", "ノミ", "The dog scratched at a flea."),
        ("ant", "アリ", "Ants marched in a long line."),
        ("cricket", "コオロギ", "A cricket chirps in the evening."),
        ("grasshopper", "バッタ", "A grasshopper leaped through the grass."),
        ("cicada", "セミ", "Cicadas buzz loudly in summer."),
        ("large brown cicada", "アブラゼミ", "The large brown cicada is common in Japan."),
        ("evening cicada", "ヒグラシ", "The evening cicada sings at dusk."),
        ("dragonfly", "トンボ", "A dragonfly hovered over the pond."),
        ("moth", "ガ(蛾)", "A moth circled the lamp."),
        ("beetle", "甲虫・カブトムシ", "A beetle crawled along the log."),
        ("ladybug", "テントウムシ", "A ladybug has bright red spots."),
        ("centipede", "ムカデ", "A centipede has many legs."),
        ("termite", "シロアリ", "Termites damage wooden houses."),
        ("aphid", "アブラムシ", "Aphids harm the garden plants."),
        ("maggot", "ウジ虫", "Maggots feed on rotting waste."),
        ("larva", "幼虫", "The larva will turn into a butterfly."),
        ("spider", "クモ", "A spider spun a web in the corner."),
        ("worm", "ミミズ・虫", "An earthworm enriches the soil."),
    ],
    "動物": [
        ("snake", "ヘビ", "A snake slid through the tall grass."),
        ("water buffalo", "水牛", "A water buffalo wallowed in the mud."),
        ("capybara", "カピバラ", "A capybara relaxed in the hot spring."),
        ("raccoon dog", "タヌキ", "The raccoon dog is native to Japan."),
        ("raccoon", "アライグマ", "A raccoon raided the trash can."),
        ("fox", "キツネ", "A fox crossed the snowy field."),
        ("falcon", "ハヤブサ", "A falcon dives at amazing speed."),
        ("hawk", "タカ", "A hawk circled high overhead."),
        ("eagle", "ワシ", "An eagle soared above the cliff."),
        ("owl", "フクロウ", "An owl hooted in the dark woods."),
        ("deer", "シカ", "A deer grazed in the meadow."),
        ("wild boar", "イノシシ", "A wild boar charged through the brush."),
        ("weasel", "イタチ", "A weasel slipped into the barn."),
        ("badger", "アナグマ", "A badger dug a deep burrow."),
        ("otter", "カワウソ", "An otter floated on its back."),
        ("hedgehog", "ハリネズミ", "A hedgehog curled into a tight ball."),
        ("mole", "モグラ", "A mole tunneled under the lawn."),
        ("bat", "コウモリ", "A bat flew out at dusk."),
        ("crow", "カラス", "A crow cawed loudly from the roof."),
        ("sparrow", "スズメ", "A sparrow hopped along the path."),
        ("pigeon", "ハト", "Pigeons gathered in the square."),
        ("heron", "サギ", "A heron stood still in the shallows."),
        ("crane", "ツル", "A crane is a symbol of long life."),
        ("swan", "ハクチョウ", "A swan glided across the lake."),
        ("squirrel", "リス", "A squirrel buried an acorn."),
        ("hare", "野ウサギ", "A hare bounded across the field."),
    ],
}


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = filled = 0
        per_group: dict[str, int] = {}
        for group, items in GROUPS.items():
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
                    (en, ja, "", ex, "動物", "500"),
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
