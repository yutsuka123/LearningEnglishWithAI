# ruff: noqa: E501  (data-heavy seed script)
"""Add concrete animal & plant names (with examples) and a few hotel phrases
(toilet-paper refill, etc.). Authored by Claude — no app/OpenAI API calls.

Run:  python scripts/add_names.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

ANIMALS: list[tuple[str, str, str]] = [
    ("cat", "猫", "The cat is sleeping on the sofa."),
    ("dog", "犬", "The dog wagged its tail."),
    ("lion", "ライオン", "The lion is the king of the jungle."),
    ("tiger", "トラ", "A tiger has orange and black stripes."),
    ("bear", "クマ", "A bear catches fish in the river."),
    ("elephant", "ゾウ", "The elephant has a long trunk."),
    ("giraffe", "キリン", "The giraffe has a very long neck."),
    ("zebra", "シマウマ", "A zebra has black and white stripes."),
    ("monkey", "サル", "The monkey climbed the tree."),
    ("gorilla", "ゴリラ", "The gorilla beat its chest."),
    ("horse", "馬", "She rides a horse every weekend."),
    ("cow", "牛", "The cow gives us milk."),
    ("pig", "豚", "The pig rolled in the mud."),
    ("sheep", "羊", "The sheep grazed on the hill."),
    ("goat", "ヤギ", "The goat climbed the rocky slope."),
    ("rabbit", "ウサギ", "The rabbit hopped across the lawn."),
    ("mouse", "ネズミ", "A mouse ran under the table."),
    ("fox", "キツネ", "A fox crept through the woods."),
    ("wolf", "オオカミ", "The wolf howled at the moon."),
    ("deer", "シカ", "A deer appeared at the forest edge."),
    ("squirrel", "リス", "The squirrel buried a nut."),
    ("raccoon", "アライグマ", "A raccoon raided the trash can."),
    ("bat", "コウモリ", "Bats fly out at dusk."),
    ("whale", "クジラ", "The whale surfaced to breathe."),
    ("dolphin", "イルカ", "Dolphins are very intelligent."),
    ("shark", "サメ", "A shark circled the boat."),
    ("octopus", "タコ", "An octopus has eight arms."),
    ("crab", "カニ", "The crab scuttled sideways."),
    ("jellyfish", "クラゲ", "A jellyfish drifted in the current."),
    ("eagle", "ワシ", "The eagle soared above the cliffs."),
    ("hawk", "タカ", "A hawk hunts small animals."),
    ("owl", "フクロウ", "The owl hooted in the night."),
    ("sparrow", "スズメ", "A sparrow pecked at the crumbs."),
    ("crow", "カラス", "A crow perched on the wire."),
    ("pigeon", "ハト", "Pigeons gathered in the square."),
    ("swan", "ハクチョウ", "A swan glided across the lake."),
    ("duck", "アヒル・カモ", "The ducks paddled in the pond."),
    ("chicken", "ニワトリ", "The chicken laid an egg."),
    ("rooster", "おんどり", "The rooster crows at dawn."),
    ("penguin", "ペンギン", "Penguins live in cold regions."),
    ("frog", "カエル", "A frog jumped into the pond."),
    ("snake", "ヘビ", "The snake slithered through the grass."),
    ("lizard", "トカゲ", "A lizard basked in the sun."),
    ("turtle", "カメ", "The turtle pulled into its shell."),
    ("crocodile", "ワニ", "A crocodile lurked in the water."),
    ("spider", "クモ", "A spider spun a web in the corner."),
    ("ant", "アリ", "Ants carried crumbs to their nest."),
    ("bee", "ハチ", "A bee buzzed around the flowers."),
    ("butterfly", "チョウ", "A butterfly landed on the petal."),
    ("mosquito", "蚊", "A mosquito bit my arm."),
    ("snail", "カタツムリ", "The snail left a slimy trail."),
    ("camel", "ラクダ", "Camels can cross the desert."),
    ("kangaroo", "カンガルー", "A kangaroo hops on its hind legs."),
    ("panda", "パンダ", "The panda chewed on bamboo."),
    ("leopard", "ヒョウ", "A leopard rested in the tree."),
    ("seal", "アザラシ", "A seal sunbathed on the rock."),
]

PLANTS: list[tuple[str, str, str]] = [
    ("cherry blossom", "サクラ", "Cherry blossoms bloom in spring."),
    ("beech", "ブナ", "The beech forest turns gold in autumn."),
    ("dandelion", "タンポポ", "A dandelion grew through the crack."),
    ("rose", "バラ", "He gave her a single red rose."),
    ("tulip", "チューリップ", "The garden was full of tulips."),
    ("sunflower", "ヒマワリ", "The sunflower turns toward the sun."),
    ("lily", "ユリ", "A white lily bloomed by the pond."),
    ("pine", "マツ", "The pine stays green all winter."),
    ("oak", "オーク・樫", "The old oak has thick branches."),
    ("maple", "カエデ", "Maple leaves turn red in fall."),
    ("bamboo", "竹", "Pandas eat bamboo."),
    ("cedar", "スギ", "Cedar wood has a strong scent."),
    ("willow", "ヤナギ", "The willow trailed over the river."),
    ("ginkgo", "イチョウ", "Ginkgo leaves turn bright yellow."),
    ("cactus", "サボテン", "A cactus stores water in its stem."),
    ("ivy", "ツタ", "Ivy climbed up the old wall."),
    ("clover", "クローバー", "She searched for a four-leaf clover."),
    ("daisy", "ヒナギク", "Daisies dotted the meadow."),
    ("orchid", "ラン", "The orchid has delicate flowers."),
    ("lotus", "ハス", "A lotus floated on the pond."),
    ("chrysanthemum", "キク", "Chrysanthemums bloom in autumn."),
    ("hydrangea", "アジサイ", "Hydrangeas bloom in the rainy season."),
    ("morning glory", "アサガオ", "The morning glory opens at dawn."),
    ("plum", "ウメ", "Plum blossoms bloom before the cherry."),
    ("lavender", "ラベンダー", "The field of lavender smelled sweet."),
    ("camellia", "ツバキ", "The camellia blooms in winter."),
    ("wisteria", "フジ", "Wisteria hung from the trellis."),
    ("azalea", "ツツジ", "Azaleas bloom along the path."),
    ("violet", "スミレ", "Tiny violets grew in the shade."),
    ("poppy", "ケシ", "Red poppies swayed in the breeze."),
    ("carnation", "カーネーション", "Carnations are given on Mother's Day."),
    ("fir", "モミ", "A fir tree is used at Christmas."),
    ("birch", "カバ・シラカバ", "The birch has white bark."),
    ("chestnut", "クリ", "We roasted chestnuts in autumn."),
    ("palm tree", "ヤシの木", "Palm trees line the beach."),
    ("reed", "アシ・葦", "Reeds grew along the riverbank."),
    ("wheat", "小麦", "The wheat field swayed in the wind."),
    ("moss", "コケ", "Soft moss covered the stones."),
    ("fern", "シダ", "Ferns grow in damp shade."),
    ("seaweed", "海藻", "Seaweed washed up on the shore."),
    ("mushroom", "キノコ", "We picked mushrooms in the forest."),
    ("cosmos", "コスモス", "Cosmos flowers bloom in autumn fields."),
    ("magnolia", "モクレン", "The magnolia blossoms are huge."),
    ("jasmine", "ジャスミン", "Jasmine smells lovely at night."),
    ("oak tree", "樫の木", "An owl nested in the oak tree."),
]

HOTEL_PHRASES: list[tuple[str, str]] = [
    ("Could you refill the toilet paper?", "トイレットペーパーを補充してください。"),
    ("We're out of toilet paper.", "トイレットペーパーが切れています。"),
    ("Could you restock the toiletries?", "アメニティを補充してもらえますか？"),
    ("Could you bring more drinking water?", "飲料水を追加でいただけますか？"),
    ("The shampoo is empty.", "シャンプーが空です。"),
    ("Could we get more bottled water?", "ペットボトルの水を追加でもらえますか？"),
]


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
        for domain, items in (("動物", ANIMALS), ("植物", PLANTS)):
            for en, ja, ex in items:
                if en.lower() in w_existing:
                    conn.execute(
                        "UPDATE words SET example = ? "
                        "WHERE LOWER(english) = LOWER(?) AND COALESCE(example, '') = ''",
                        (ex, en),
                    )
                    w_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO words (english, japanese, part_of_speech, "
                    "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                    (en, ja, "", ex, domain, "600"),
                )
                w_existing.add(en.lower())
                w_added += 1

        ph_added = ph_skipped = 0
        for en, ja in HOTEL_PHRASES:
            if en.lower() in ph_existing:
                ph_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) VALUES (?, ?, ?)",
                (en, ja, "ホテル"),
            )
            ph_existing.add(en.lower())
            ph_added += 1

    print(f"words:   +{w_added} (skipped {w_skipped})")
    print(f"hotel phrases: +{ph_added} (skipped {ph_skipped})")
    with db() as conn:
        print(
            "totals -> phrases:",
            conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0],
            "words:",
            conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
            "/ words without example:",
            conn.execute("SELECT COUNT(*) FROM words WHERE COALESCE(example,'')=''").fetchone()[0],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
