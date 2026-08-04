# ruff: noqa: E501  (data-heavy seed script: long word/example lines are fine)
"""Bulk-add curated vocabulary for the PLANTS domain (植物), authored by Claude.

The `植物` domain already had ~73 common words (cherry blossom, beech,
dandelion, photosynthesis, deciduous, germinate, stem, petal, ...). This
batch goes broader and deeper across trees, flowers, garden/houseplants,
plant-part & botany vocabulary, plant biology/classification terms, crop &
agriculture plants, and a small set of fungi commonly grouped with nature
vocabulary.

Words already present anywhere in the `words` table were excluded up front
(checked against the full table, not just `植物`) so nothing here collides
with existing entries — including near-miss homonyms already used in other
domains for a different sense, e.g. "annual" (ビジネス), "bloom"/"prune"
(教養), "weed" (禁止用語), "kernel" (IT), "mold" (機械工学), "propagation"
(電気電子), "hedge" (ビジネス), and the whole set of farming/process words
already covered by the existing `農業・園芸` domain (barley, rye, corn,
germination, crop rotation, irrigation, compost, mulch, greenhouse,
horticulture, transplant, bulb, flower bed, etc.) — those are intentionally
NOT repeated here.

Levels are spread across the full scale: common flowers/trees/herbs sit at
300-500, moderately common garden/crop vocabulary at 550-750, and
scientific/technical botany terms (xylem, epiphyte, monocot/dicot,
mycorrhiza, ...) sit at 850-990+.

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_plants_expanded.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # === 樹木 (trees) ===
    ("redwood", "セコイア（巨大な針葉樹）", "名詞", "The redwood tree is one of the tallest in the world.", "植物", "550"),
    ("cypress", "イトスギ", "名詞", "Cypress trees line the entrance to the cemetery.", "植物", "650"),
    ("elm", "ニレの木", "名詞", "The old elm tree shaded the whole yard.", "植物", "600"),
    ("walnut", "クルミの木", "名詞", "We planted a walnut tree in the backyard.", "植物", "500"),
    ("fig tree", "イチジクの木", "名詞", "A fig tree grew beside the old stone wall.", "植物", "550"),
    ("ash tree", "トネリコ", "名詞", "The baseball bat was made from ash tree wood.", "植物", "650"),
    ("poplar", "ポプラ", "名詞", "Poplar trees grew in a straight row along the road.", "植物", "700"),
    ("spruce", "トウヒ", "名詞", "They cut down a spruce for the Christmas tree.", "植物", "650"),
    ("sycamore", "スズカケノキ（プラタナス）", "名詞", "A huge sycamore shaded the park bench.", "植物", "750"),
    ("dogwood", "ハナミズキ", "名詞", "The dogwood blooms with white flowers in spring.", "植物", "800"),
    ("hazel", "ハシバミ", "名詞", "We picked hazel nuts from the bushes in autumn.", "植物", "700"),
    ("olive tree", "オリーブの木", "名詞", "The olive tree has grown in this grove for centuries.", "植物", "500"),
    ("banyan tree", "ベンガルボダイジュ（バニヤンツリー）", "名詞", "The banyan tree's roots hung down like curtains.", "植物", "850"),
    ("mangrove", "マングローブ", "名詞", "Mangrove forests protect the coast from erosion.", "植物", "750"),
    ("teak", "チーク材（の木）", "名詞", "The furniture was carved from solid teak.", "植物", "800"),
    ("mahogany", "マホガニー", "名詞", "The table was made of dark mahogany wood.", "植物", "750"),
    ("eucalyptus", "ユーカリ", "名詞", "Koalas eat almost nothing but eucalyptus leaves.", "植物", "700"),
    ("rubber tree", "ゴムの木", "名詞", "Rubber trees are tapped for their sap to make rubber.", "植物", "750"),
    ("baobab", "バオバブ", "名詞", "The baobab's thick trunk can store huge amounts of water.", "植物", "900"),
    ("sequoia", "セコイアオスギ（巨木）", "名詞", "The giant sequoia is among the largest living things on Earth.", "植物", "800"),
    ("larch", "カラマツ", "名詞", "The larch is one of the few conifers that loses its needles in winter.", "植物", "850"),
    ("holly", "ヒイラギ", "名詞", "We hung holly branches over the fireplace at Christmas.", "植物", "650"),
    ("yew", "イチイ（の木）", "名詞", "The old yew tree in the churchyard is said to be centuries old.", "植物", "850"),
    ("alder", "ハンノキ", "名詞", "Alder trees often grow near rivers and wetlands.", "植物", "900"),
    ("hawthorn", "サンザシ", "名詞", "The hawthorn hedge was covered in white blossoms.", "植物", "900"),
    ("juniper", "ネズ（ジュニパー）", "名詞", "Gin gets its distinctive flavor from juniper berries.", "植物", "750"),
    ("acacia", "アカシア", "名詞", "Acacia trees dot the African savanna.", "植物", "800"),
    ("rowan", "ナナカマド", "名詞", "The rowan tree's red berries attract birds in autumn.", "植物", "950"),

    # === 花 (flowers) ===
    ("peony", "ボタン（芍薬）", "名詞", "The peonies in the garden bloomed in bright pink.", "植物", "600"),
    ("iris", "アヤメ・アイリス", "名詞", "Purple irises grew along the edge of the pond.", "植物", "550"),
    ("daffodil", "スイセン（ラッパズイセン）", "名詞", "Daffodils are one of the first flowers to bloom in spring.", "植物", "550"),
    ("marigold", "マリーゴールド", "名詞", "Marigolds are often planted to keep insects away from vegetables.", "植物", "650"),
    ("hibiscus", "ハイビスカス", "名詞", "A hibiscus flower bloomed just outside the hotel window.", "植物", "600"),
    ("dahlia", "ダリア", "名詞", "The dahlia won first prize at the flower show.", "植物", "700"),
    ("gardenia", "クチナシ", "名詞", "The gardenia's sweet scent filled the whole room.", "植物", "700"),
    ("snapdragon", "キンギョソウ", "名詞", "Children love squeezing snapdragon flowers to make them 'snap'.", "植物", "800"),
    ("primrose", "サクラソウ（プリムローズ）", "名詞", "Primroses were among the first flowers to appear after winter.", "植物", "750"),
    ("buttercup", "キンポウゲ", "名詞", "The meadow was dotted with yellow buttercups.", "植物", "600"),
    ("forget-me-not", "ワスレナグサ", "名詞", "She planted forget-me-nots along the garden path.", "植物", "700"),
    ("bluebell", "ブルーベル（釣鐘型の青い花）", "名詞", "The forest floor was covered in bluebells in April.", "植物", "750"),
    ("foxglove", "ジギタリス（キツネノテブクロ）", "名詞", "Foxglove flowers hang in tall purple spikes.", "植物", "850"),
    ("geranium", "ゼラニウム", "名詞", "Red geraniums hung from every balcony in the village.", "植物", "650"),
    ("petunia", "ペチュニア", "名詞", "Petunias trailed over the edge of the flower pot.", "植物", "700"),
    ("zinnia", "ジニア（百日草）", "名詞", "Zinnias bloom in bright colors all summer long.", "植物", "850"),
    ("anemone", "アネモネ", "名詞", "Sea anemones share their name with the anemone flower.", "植物", "800"),
    ("crocus", "クロッカス", "名詞", "The first crocus of the year pushed up through the snow.", "植物", "750"),
    ("freesia", "フリージア", "名詞", "Freesias are prized for their strong, sweet fragrance.", "植物", "850"),
    ("amaryllis", "アマリリス", "名詞", "The amaryllis bulb produced a huge red flower indoors.", "植物", "900"),
    ("begonia", "ベゴニア", "名詞", "Begonias are popular houseplants because they bloom for months.", "植物", "800"),
    ("impatiens", "インパチェンス（アフリカホウセンカ）", "名詞", "Impatiens thrive in shady, damp corners of the garden.", "植物", "900"),
    ("pansy", "パンジー", "名詞", "Pansies are hardy enough to bloom even in cool weather.", "植物", "650"),
    ("sweet pea", "スイートピー", "名詞", "The sweet pea vine climbed up the wooden trellis.", "植物", "750"),
    ("honeysuckle", "スイカズラ", "名詞", "The scent of honeysuckle drifted through the open window.", "植物", "750"),
    ("water lily", "スイレン", "名詞", "Water lilies floated on the surface of the pond.", "植物", "600"),
    ("edelweiss", "エーデルワイス", "名詞", "Edelweiss grows high in the Alps and is hard to find.", "植物", "900"),

    # === 庭・観葉植物・ハーブ (garden / houseplants / herbs) ===
    ("succulent", "多肉植物", "名詞", "Succulents need very little water to survive.", "植物", "650"),
    ("bonsai", "盆栽", "名詞", "He has been shaping the same bonsai tree for thirty years.", "植物", "600"),
    ("basil", "バジル", "名詞", "Fresh basil gives the sauce its distinctive flavor.", "植物", "400"),
    ("mint", "ミント（ハッカ）", "名詞", "She grows mint in a pot so it won't spread everywhere.", "植物", "350"),
    ("rosemary", "ローズマリー", "名詞", "Rosemary grows well even in dry, sunny spots.", "植物", "500"),
    ("thyme", "タイム", "名詞", "A sprig of thyme was added to the soup.", "植物", "550"),
    ("oregano", "オレガノ", "名詞", "Oregano is a key herb in Italian cooking.", "植物", "550"),
    ("sage", "セージ", "名詞", "The recipe called for a few leaves of fresh sage.", "植物", "600"),
    ("parsley", "パセリ", "名詞", "The plate was garnished with a sprig of parsley.", "植物", "450"),
    ("cilantro", "パクチー（コリアンダーの葉）", "名詞", "Some people love the taste of cilantro, and others hate it.", "植物", "550"),
    ("dill", "ディル（イノンド）", "名詞", "Dill pairs especially well with fish dishes.", "植物", "650"),
    ("chives", "チャイブ（西洋アサツキ）", "名詞", "She sprinkled chopped chives over the baked potato.", "植物", "650"),
    ("lemongrass", "レモングラス", "名詞", "Lemongrass gives Thai soup its citrusy aroma.", "植物", "700"),
    ("houseplant", "観葉植物", "名詞", "This houseplant only needs watering once a week.", "植物", "450"),
    ("potted plant", "鉢植えの植物", "名詞", "A potted plant sat on the windowsill.", "植物", "400"),
    ("terrarium", "テラリウム", "名詞", "She built a small terrarium with moss and tiny ferns.", "植物", "800"),
    ("window box", "ウィンドウボックス（窓辺の植木箱）", "名詞", "Bright flowers spilled out of the window box.", "植物", "750"),
    ("topiary", "トピアリー（樹木の刈り込み造形）", "名詞", "The garden was famous for its elaborate topiary shaped like animals.", "植物", "900"),
    ("raised bed", "盛り土花壇（レイズドベッド）", "名詞", "They built a raised bed to grow vegetables in the small yard.", "植物", "750"),
    ("trellis", "トレリス（つる植物用の格子棚）", "名詞", "The climbing roses were trained up a wooden trellis.", "植物", "800"),
    ("arboretum", "樹木園", "名詞", "The city arboretum has trees from every continent.", "植物", "900"),
    ("botanical garden", "植物園", "名詞", "We spent the afternoon walking through the botanical garden.", "植物", "600"),
    ("air plant", "エアプランツ（土を使わず育つ着生植物）", "名詞", "An air plant doesn't need soil to survive.", "植物", "800"),
    ("potting soil", "培養土", "名詞", "Fill the container with fresh potting soil before planting.", "植物", "700"),

    # === 植物の部位・植物学用語 (plant parts / botany vocabulary) ===
    ("pistil", "雌しべ", "名詞", "The pistil is the female reproductive part of a flower.", "植物", "850"),
    ("stamen", "雄しべ", "名詞", "Pollen is produced on the tip of the stamen.", "植物", "850"),
    ("stigma", "柱頭（雌しべの先端部分）", "名詞", "Pollen must land on the stigma for fertilization to occur.", "植物", "900"),
    ("anther", "葯（やく、雄しべの先端）", "名詞", "The anther releases pollen when it splits open.", "植物", "950"),
    ("rhizome", "根茎", "名詞", "Ginger grows from an underground rhizome.", "植物", "900"),
    ("tuber", "塊茎（かいけい）", "名詞", "A potato is actually a swollen underground tuber.", "植物", "750"),
    ("taproot", "主根", "名詞", "Carrots grow a single thick taproot straight down into the soil.", "植物", "800"),
    ("husk", "殻・皮（穀物や種子の外皮）", "名詞", "You have to remove the husk before you can eat the corn.", "植物", "700"),
    ("cambium", "形成層", "名詞", "The cambium layer produces new wood and bark each year.", "植物", "950"),
    ("xylem", "木部（水を運ぶ組織）", "名詞", "The xylem carries water up from the roots to the leaves.", "植物", "900"),
    ("phloem", "師部（養分を運ぶ組織）", "名詞", "The phloem transports sugars made by the leaves to the rest of the plant.", "植物", "900"),
    ("node", "節（茎に葉が付く部分）", "名詞", "New leaves sprout from each node along the stem.", "植物", "750"),
    ("leaflet", "小葉", "名詞", "A clover leaf is actually made up of three leaflets.", "植物", "800"),
    ("frond", "（シダ・ヤシなどの）葉", "名詞", "The fern's fronds unfurled slowly in the spring sun.", "植物", "850"),
    ("calyx", "がく（花びらの外側を包む部分）", "名詞", "The calyx protects the flower bud before it opens.", "植物", "950"),
    ("sepal", "がく片", "名詞", "The green sepals folded back as the flower bloomed.", "植物", "900"),
    ("pod", "さや", "名詞", "She shelled the peas from their pods.", "植物", "550"),
    ("seedpod", "種のさや", "名詞", "The seedpod cracked open and scattered seeds on the wind.", "植物", "650"),
    ("cotyledon", "子葉", "名詞", "The seedling's first two leaves are called cotyledons.", "植物", "990"),
    ("canopy", "林冠（森の上層部）", "名詞", "Sunlight barely reached the forest floor through the thick canopy.", "植物", "700"),
    ("undergrowth", "下草・低木層", "名詞", "Thick undergrowth made it hard to walk through the forest.", "植物", "750"),
    ("understory", "林床植生（森の下層）", "名詞", "Small shrubs and ferns make up the forest's understory.", "植物", "850"),
    ("thicket", "茂み", "名詞", "The rabbit disappeared into a thicket of bushes.", "植物", "750"),
    ("grove", "木立・果樹園", "名詞", "They had a picnic in a small olive grove.", "植物", "650"),
    ("meadow", "草原・牧草地", "名詞", "Wildflowers covered the meadow in early summer.", "植物", "500"),
    ("wildflower", "野の花", "名詞", "The hillside was full of colorful wildflowers.", "植物", "500"),
    ("wilt", "しおれる", "動詞", "The flowers began to wilt in the afternoon heat.", "植物", "600"),
    ("algae", "藻類", "名詞", "Green algae covered the surface of the pond.", "植物", "550"),

    # === 植物の生態・分類 (plant biology / classification) ===
    ("biennial", "二年生植物（の）", "形容詞", "Carrots are biennial, flowering only in their second year.", "植物", "800"),
    ("pollination", "受粉", "名詞", "Bees play a major role in pollination.", "植物", "700"),
    ("hybrid", "交配種・雑種", "名詞", "This rose is a hybrid bred for both color and fragrance.", "植物", "600"),
    ("native species", "在来種", "名詞", "The park only plants native species to support local wildlife.", "植物", "700"),
    ("invasive species", "外来侵入種", "名詞", "The lake was overrun by an invasive species of weed.", "植物", "750"),
    ("drought-resistant", "耐乾性の", "形容詞", "Cacti are naturally drought-resistant plants.", "植物", "800"),
    ("cross-pollination", "他家受粉", "名詞", "Cross-pollination between varieties can produce new flower colors.", "植物", "850"),
    ("botanist", "植物学者", "名詞", "The botanist spent years studying rare orchids in the rainforest.", "植物", "650"),
    ("cultivate", "栽培する", "動詞", "Farmers cultivate this crop mainly for export.", "植物", "700"),
    ("cultivation", "栽培", "名詞", "The cultivation of rice requires a lot of water.", "植物", "700"),
    ("graft", "接ぎ木する", "動詞", "Gardeners often graft a fruit branch onto a hardier rootstock.", "植物", "750"),
    ("dormant", "休眠状態の", "形容詞", "The seeds stay dormant in the soil until spring rain wakes them.", "植物", "750"),
    ("dormancy", "休眠", "名詞", "Many trees enter a period of dormancy during winter.", "植物", "850"),
    ("epiphyte", "着生植物", "名詞", "Many orchids are epiphytes that grow on the branches of other trees.", "植物", "950"),
    ("xerophyte", "乾生植物", "名詞", "Cacti are classic examples of xerophytes adapted to dry climates.", "植物", "990"),
    ("monoculture", "単一栽培", "名詞", "Relying on a single crop monoculture makes farms vulnerable to disease.", "植物", "850"),
    ("topsoil", "表土", "名詞", "Heavy rain washed away much of the field's topsoil.", "植物", "700"),
    ("humus", "腐植土", "名詞", "Rich humus in the soil helps plants grow strong.", "植物", "800"),
    ("symbiosis", "共生関係", "名詞", "The relationship between bees and flowers is a classic example of symbiosis.", "植物", "850"),
    ("carnivorous plant", "食虫植物", "名詞", "The Venus flytrap is probably the most famous carnivorous plant.", "植物", "700"),
    ("parasitic plant", "寄生植物", "名詞", "Mistletoe is a parasitic plant that draws nutrients from its host tree.", "植物", "800"),
    ("cultivar", "栽培品種", "名詞", "This apple cultivar was bred to resist common diseases.", "植物", "900"),
    ("self-pollination", "自家受粉", "名詞", "Some plants rely entirely on self-pollination to reproduce.", "植物", "850"),
    ("photosynthesize", "光合成する", "動詞", "Plants photosynthesize to convert sunlight into energy.", "植物", "800"),
    ("nitrogen fixation", "窒素固定", "名詞", "Certain bacteria in the roots enable nitrogen fixation in legumes.", "植物", "950"),
    ("monocot", "単子葉植物", "名詞", "Grasses and lilies are both examples of monocots.", "植物", "990"),
    ("dicot", "双子葉植物", "名詞", "Most flowering trees and roses are classified as dicots.", "植物", "990"),
    ("symbiotic", "共生の", "形容詞", "Lichen is formed by a symbiotic relationship between fungi and algae.", "植物", "850"),
    ("botany", "植物学", "名詞", "She majored in botany at university.", "植物", "600"),

    # === 農作物 (crops / agriculture plants) ===
    ("rice", "米・稲", "名詞", "Rice is the staple food for more than half the world's population.", "植物", "300"),
    ("maize", "トウモロコシ（英式表現）", "名詞", "Maize is grown across huge areas of the American Midwest.", "植物", "600"),
    ("soybean", "大豆", "名詞", "Soybean is one of the country's biggest export crops.", "植物", "500"),
    ("cotton plant", "綿花・綿の木", "名詞", "The cotton plant's fluffy white fibers are harvested for fabric.", "植物", "550"),
    ("sugarcane", "サトウキビ", "名詞", "Sugarcane is grown widely in tropical regions.", "植物", "600"),
    ("vineyard", "ぶどう園", "名詞", "The vineyard produces some of the region's finest wine.", "植物", "600"),
    ("grapevine", "ぶどうの木・つる", "名詞", "The grapevine climbed all the way up the stone wall.", "植物", "650"),
    ("oat", "オーツ麦・カラス麦", "名詞", "Oat is often used to make breakfast cereal.", "植物", "500"),
    ("millet", "キビ・アワ（雑穀）", "名詞", "Millet is a hardy grain that grows well in dry climates.", "植物", "800"),
    ("sorghum", "モロコシ（穀物）", "名詞", "Sorghum is an important crop in parts of Africa and Asia.", "植物", "900"),
    ("hops", "ホップ", "名詞", "Hops give beer its bitter flavor.", "植物", "800"),
    ("tobacco plant", "タバコの木", "名詞", "The tobacco plant's leaves are dried and cured before use.", "植物", "650"),
    ("flax", "亜麻", "名詞", "Flax is used to make both linen fabric and linseed oil.", "植物", "850"),
    ("hemp", "麻（ヘンプ）", "名詞", "Hemp fibers are strong enough to make rope and cloth.", "植物", "700"),
    ("tea plant", "茶の木", "名詞", "The tea plant's young leaves are picked by hand.", "植物", "600"),
    ("coffee plant", "コーヒーの木", "名詞", "The coffee plant produces red berries called cherries.", "植物", "600"),
    ("cacao", "カカオ", "名詞", "Chocolate is made from the seeds of the cacao tree.", "植物", "700"),
    ("sugar beet", "サトウダイコン（てん菜）", "名詞", "Sugar beet is grown for sugar in cooler climates.", "植物", "750"),
    ("canola", "キャノーラ（西洋アブラナ）", "名詞", "Canola fields turn bright yellow when the plants bloom.", "植物", "800"),
    ("quinoa", "キヌア", "名詞", "Quinoa has become popular as a healthy grain substitute.", "植物", "700"),
    ("buckwheat", "そば（蕎麦）", "名詞", "Buckwheat flour is used to make soba noodles.", "植物", "800"),

    # === 菌類 (fungi, commonly grouped with plant/nature vocabulary) ===
    ("yeast", "酵母", "名詞", "Yeast makes bread dough rise.", "植物", "500"),
    ("spore", "胞子", "名詞", "Mushrooms release spores to reproduce.", "植物", "650"),
    ("toadstool", "毒キノコ", "名詞", "The bright red toadstool looked pretty but was poisonous.", "植物", "750"),
    ("fungus", "菌類", "名詞", "Mold is a type of fungus that grows in damp places.", "植物", "500"),
    ("truffle", "トリュフ", "名詞", "Chefs prize truffles for their rich, earthy aroma.", "植物", "650"),
    ("lichen", "地衣類", "名詞", "Lichen grew across the surface of the old gravestones.", "植物", "800"),
    ("mycelium", "菌糸体", "名詞", "The mycelium spreads underground long before any mushroom appears above ground.", "植物", "950"),
    ("mildew", "うどんこ病・カビ", "名詞", "Mildew spread across the leaves in the humid greenhouse.", "植物", "700"),
    ("mycorrhiza", "菌根（菌類と植物根の共生体）", "名詞", "Mycorrhiza helps tree roots absorb more water and nutrients.", "植物", "990+"),
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
        print("total words:", conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
