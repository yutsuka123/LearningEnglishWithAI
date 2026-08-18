# ruff: noqa: E501  (data-heavy seed script: long example-sentence lines are fine)
"""「地理」ドメインの語彙拡充（気候・地形・地図・その他人文地理）。

既存の「地理」ドメインは21語のみで、気候(climate)関連の語彙が皆無、
地図・地図学(cartography)関連の語彙も皆無という大きな穴があった
（既存21語: plain, basin, continent, delta, equator, latitude,
longitude, terrain, demographics, peninsula, strait, archipelago,
hemisphere, monsoon, savanna, tundra, urbanization, biome, topography,
tributary, watershed）。

本スクリプトは以下4分野を追加する（すべて高校地理以上のレベルを意識）:
  - 気候 (climate zones, precipitation patterns, climate types)
  - 地形 (landforms beyond the existing basin/delta/peninsula etc.)
  - 地図・地図学 (map reading, projections, coordinates)
  - その他人文地理 (population/urban geography terms)

事前にDB全体を検索し、既存の語（他ドメイン含む）と英単語が完全一致する
ものは除外済み（例: climate, humidity, precipitation, cliff, arid,
plateau, glacier, drought, erosion, fjord, isthmus, mesa, moraine,
sediment, migration, ecosystem, habitat, deforestation, biodiversity,
compass, canyon, mountain pass, sinkhole, caldera, tectonic plate,
fault line, arable land, geyser, surveyor, ridge, satellite image 等は
既に他ドメインに存在するため、本リストには含めていない）。

無難な教材(政治的論争・係争地・国別の政治的言及を避けた物理地理・
地図学・基礎的な人文地理の語彙のみ)。

words.detail / 音声は空のまま挿入。挿入後に
`python scripts/build_details.py --limit N` と
`python scripts/build_audio.py --words N` で補完すること。

再実行安全: 既存english（小文字比較、DB全体）と一致する語はスキップする。

使い方:
  python scripts/add_geography_climate_terrain_maps.py            # 挿入
  python scripts/add_geography_climate_terrain_maps.py --dry-run  # 件数だけ確認
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "地理"

# (english, japanese, part_of_speech, example, domain, level)
WORDS: list[tuple[str, str, str, str, str, str]] = []


def G(level: str, rows: list[tuple[str, str, str, str]]) -> None:
    """Append (en, ja, pos, ex) rows to WORDS with a shared level/domain."""
    for en, ja, pos, ex in rows:
        WORDS.append((en, ja, pos, ex, DOMAIN, level))


# ─────────────────────────────────────────────────────────────
# 気候 (climate)
# ─────────────────────────────────────────────────────────────
G("400", [
    ("humid", "湿気の多い", "形容詞", "Summer in Tokyo is hot and humid."),
])
G("450", [
    ("rainfall", "降雨量", "名詞",
     "Annual rainfall in the region has been decreasing for years."),
    ("dry season", "乾季", "名詞",
     "Wildlife gathers around the remaining water holes during the dry season."),
    ("wet season", "雨季", "名詞", "Roads often flood during the wet season."),
])
G("500", [
    ("climate zone", "気候帯", "名詞",
     "Japan spans several climate zones, from the subtropical south to the snowy north."),
    ("tropical climate", "熱帯気候", "名詞",
     "Singapore has a tropical climate with high humidity all year round."),
    ("temperate climate", "温帯気候", "名詞",
     "Most of Japan has a temperate climate with four distinct seasons."),
])
G("550", [
    ("polar climate", "寒帯気候", "名詞",
     "A polar climate has extremely cold winters and very short, cool summers."),
    ("arid climate", "乾燥気候", "名詞",
     "An arid climate receives very little rainfall throughout the year."),
])
G("650", [
    ("subarctic", "亜寒帯の・亜寒帯気候", "形容詞/名詞",
     "Siberia has a subarctic climate with extremely long, harsh winters."),
    ("semi-arid", "半乾燥の", "形容詞",
     "Semi-arid regions get slightly more rain than true deserts do."),
    ("growing season", "生育期間", "名詞",
     "The growing season is much shorter at higher altitudes."),
    ("continental climate", "大陸性気候", "名詞",
     "A continental climate has hot summers and very cold winters."),
])
G("700", [
    ("microclimate", "微気候", "名詞",
     "The valley floor has its own microclimate, cooler than the surrounding hills."),
    ("maritime climate", "海洋性気候", "名詞",
     "Coastal areas often have a milder maritime climate than inland regions."),
    ("Mediterranean climate", "地中海性気候", "名詞",
     "A Mediterranean climate has dry summers and mild, wet winters."),
])
G("750", [
    ("prevailing wind", "卓越風", "名詞",
     "The prevailing wind blows from the west for most of the year."),
    ("trade winds", "貿易風", "名詞",
     "Sailors once relied on the trade winds to cross the Atlantic Ocean."),
    ("aridity", "乾燥度", "名詞",
     "The extreme aridity of the desert makes farming almost impossible."),
    ("desertification", "砂漠化", "名詞",
     "Overgrazing and repeated drought have accelerated desertification in the region."),
])
G("800", [
    ("rain shadow", "雨影（山の風下側にできる乾燥地帯）", "名詞",
     "The valley lies in the rain shadow of the mountain range, so it rarely rains there."),
])
G("850", [
    ("isotherm", "等温線", "名詞",
     "The map's isotherms connect places that share the same average temperature."),
    ("isohyet", "等雨量線", "名詞",
     "Isohyets on the map connect points that receive the same amount of rainfall."),
])

# ─────────────────────────────────────────────────────────────
# 地形 (terrain / landforms)
# ─────────────────────────────────────────────────────────────
G("400", [
    ("bay", "湾・入り江", "名詞", "Fishing boats return to the bay every evening."),
])
G("450", [
    ("mountain range", "山脈", "名詞",
     "The Andes form the longest mountain range in the world."),
    ("coastline", "海岸線", "名詞", "The country has a long, rugged coastline."),
])
G("500", [
    ("highland", "高地", "名詞",
     "The highlands are much cooler than the coastal lowlands."),
    ("lowland", "低地", "名詞",
     "Rice is grown in the fertile lowlands near the river."),
    ("shoreline", "岸辺・水際線", "名詞",
     "Erosion has gradually reshaped the shoreline over the decades."),
    ("cape", "岬", "名詞", "Ships must round the cape carefully in rough weather."),
    ("gulf", "湾（規模の大きい入り江）", "名詞",
     "Oil platforms operate far out in the gulf."),
])
G("550", [
    ("sand dune", "砂丘", "名詞",
     "Wind constantly reshapes the sand dunes in the desert."),
    ("oasis", "オアシス", "名詞",
     "Weary travelers rested at the oasis before crossing the desert."),
    ("wetland", "湿地", "名詞",
     "The wetland provides an important habitat for migratory birds."),
    ("marsh", "沼地", "名詞", "Tall reeds grow thickly throughout the marsh."),
])
G("600", [
    ("foothills", "山麓", "名詞", "The town sits in the foothills of the mountains."),
    ("mountain ridge", "尾根・山稜", "名詞",
     "Hikers followed the mountain ridge all the way to the summit."),
])
G("650", [
    ("lagoon", "潟湖・ラグーン", "名詞",
     "The lagoon is separated from the open ocean by a coral reef."),
    ("prairie", "プレーリー（北米の草原）", "名詞",
     "The prairie stretches flat and nearly treeless for miles."),
])
G("750", [
    ("headland", "岬・海に突き出た高台の地形", "名詞",
     "Waves crash against the rocky headland."),
    ("estuary", "河口・三角江", "名詞",
     "Many young fish grow up in the estuary where the river meets the sea."),
    ("steppe", "ステップ（樹木の少ない温帯の草原）", "名詞",
     "Nomadic herders once crossed the vast steppe with their livestock."),
    ("continental shelf", "大陸棚", "名詞",
     "The continental shelf drops off sharply into the deep ocean."),
    ("ocean trench", "海溝", "名詞",
     "The Mariana Trench is the deepest ocean trench on Earth."),
])
G("800", [
    ("escarpment", "断崖・急斜面", "名詞",
     "The escarpment drops steeply down to the plain below."),
    ("alluvial plain", "沖積平野", "名詞",
     "Farmers value the alluvial plain for its rich, fertile soil."),
])
G("850", [
    ("karst", "カルスト地形", "名詞",
     "Karst landscapes are riddled with caves and sinkholes formed by dissolving limestone."),
])

# ─────────────────────────────────────────────────────────────
# 地図・地図学 (maps / cartography)
# ─────────────────────────────────────────────────────────────
G("400", [
    ("globe", "地球儀", "名詞",
     "A globe represents the Earth's true shape better than a flat map."),
])
G("450", [
    ("atlas", "地図帳", "名詞", "She looked up the small country in an atlas."),
])
G("500", [
    ("cardinal direction", "方位（東西南北）", "名詞",
     "North, south, east, and west are the four cardinal directions."),
])
G("550", [
    ("coordinates", "座標", "名詞",
     "Enter the coordinates into the GPS device to find the exact spot."),
])
G("600", [
    ("map scale", "縮尺", "名詞",
     "Check the map scale to estimate the actual distance between towns."),
    ("map legend", "凡例", "名詞",
     "The map legend explains what each symbol represents."),
])
G("650", [
    ("satellite imagery", "衛星画像データ", "名詞",
     "Scientists use satellite imagery to track deforestation over time."),
])
G("700", [
    ("contour line", "等高線", "名詞",
     "Contour lines drawn close together indicate a steep slope."),
    ("topographic map", "地形図", "名詞",
     "A topographic map shows elevation using contour lines."),
    ("prime meridian", "本初子午線", "名詞",
     "The prime meridian passes through Greenwich, England."),
    ("aerial photograph", "空中写真", "名詞",
     "Aerial photographs help geographers track changes in land use."),
])
G("750", [
    ("relief map", "起伏地図・立体地図", "名詞",
     "The relief map shows the mountains and valleys in three dimensions."),
    ("tropic of Cancer", "北回帰線", "固有名詞",
     "The Tropic of Cancer marks the northernmost point where the sun can appear directly overhead."),
    ("tropic of Capricorn", "南回帰線", "固有名詞",
     "The Tropic of Capricorn lies south of the equator, at a matching latitude to the Tropic of Cancer."),
])
G("800", [
    ("cartography", "地図学・地図作成法", "名詞",
     "Modern cartography relies heavily on satellite data."),
    ("cartographer", "地図製作者", "名詞",
     "The cartographer updated the map with the new border lines."),
    ("map projection", "地図投影法", "名詞",
     "Every map projection distorts either area, shape, or distance."),
    ("grid reference", "グリッド参照（地図上の位置を示す座標）", "名詞",
     "Use the grid reference to pinpoint the exact location on the map."),
])

# ─────────────────────────────────────────────────────────────
# その他人文地理 (population / urban geography)
# ─────────────────────────────────────────────────────────────
G("450", [
    ("urban", "都市の", "形容詞", "Urban areas are growing rapidly across Asia."),
    ("rural", "田舎の・農村の", "形容詞",
     "Rural communities often rely heavily on agriculture."),
    ("coastal", "沿岸の", "形容詞",
     "Coastal cities are especially vulnerable to rising sea levels."),
    ("suburb", "郊外", "名詞",
     "Many families moved to the suburbs for more living space."),
])
G("500", [
    ("time zone", "タイムゾーン（時間帯）", "名詞",
     "Japan and Australia's east coast are in different time zones."),
])
G("550", [
    ("population density", "人口密度", "名詞",
     "Tokyo has one of the highest population densities in the world."),
    ("population growth", "人口増加", "名詞",
     "Population growth has slowed in many developed countries."),
])
G("650", [
    ("land use", "土地利用", "名詞",
     "Land use planning balances housing, farming, and conservation."),
    ("megacity", "メガシティ（人口が非常に多い巨大都市）", "名詞",
     "Tokyo is considered the world's largest megacity."),
    ("metropolitan area", "都市圏", "名詞",
     "The metropolitan area includes several surrounding suburbs."),
])
G("700", [
    ("overpopulation", "人口過密", "名詞",
     "Overpopulation puts pressure on water and food supplies."),
    ("emigration", "国外移住", "名詞",
     "Emigration from rural areas has left many villages nearly empty."),
    ("landlocked", "内陸の（海に面していない）", "形容詞",
     "Switzerland is a landlocked country with no coastline."),
    ("landmass", "陸塊", "名詞",
     "Australia is the smallest of the world's continental landmasses."),
    ("subcontinent", "亜大陸", "名詞",
     "India is often described geographically as a subcontinent."),
])
G("750", [
    ("navigable", "航行可能な", "形容詞",
     "The river is navigable by large cargo ships as far as the capital."),
])
G("800", [
    ("vegetation zone", "植生帯", "名詞",
     "Vegetation zones shift from rainforest to alpine tundra as you climb the mountain."),
])
G("850", [
    ("hinterland", "後背地", "名詞",
     "The port city serves as a gateway to a vast hinterland of farms and mines."),
])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                     help="件数だけ表示して挿入しない")
    args = ap.parse_args()

    with db() as conn:
        have_w = {r[0].strip().lower()
                  for r in conn.execute("SELECT english FROM words")}

        seen: set[str] = set()
        uniq_w: list[tuple[str, str, str, str, str, str]] = []
        skipped_dup = 0
        skipped_existing = 0
        for w in WORDS:
            k = w[0].strip().lower()
            if k in have_w:
                skipped_existing += 1
                continue
            if k in seen:
                skipped_dup += 1
                continue
            seen.add(k)
            uniq_w.append(w)

        print(f"WORDS: 定義 {len(WORDS)} / 新規 {len(uniq_w)} "
              f"(既存重複 {skipped_existing} / リスト内重複 {skipped_dup})")

        by_level: dict[str, int] = {}
        for w in uniq_w:
            by_level[w[5]] = by_level.get(w[5], 0) + 1
        for level in sorted(by_level, key=lambda x: int(x)):
            print(f"   level {level}: {by_level[level]}")

        if args.dry_run:
            print("[dry-run] 挿入しません。")
            return 0

        conn.executemany(
            "INSERT INTO words (english, japanese, part_of_speech, example, "
            "domain, level) VALUES (?, ?, ?, ?, ?, ?)", uniq_w,
        )
        print(f"挿入完了: words +{len(uniq_w)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
