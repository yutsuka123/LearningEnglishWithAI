# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""地学ドメインの大学専門課程レベルへの深化(2026-09-08・B24タスク・
authored by Claude)。`docs/B24_VOCAB_DRAFT_REVIEW.md`で先にドラフトされた
112語(既存DB全体との重複チェック済み)を2並列サブエージェントで
定義文・例文・detail生成→WebSearchで歴史的事実(人名・年代)を検証。

既存DBとの同一概念の重複4語を除外: cleavage (mineral)/Mohs hardness
scale(アウトドア・レジャー分野の既存語と同一概念)、continental shelf
(地理分野の既存語と同一概念)、mass extinction(動物(絶滅)分野の既存語と
同一概念)。meanderのみ、既存語(基礎語彙、動詞「曲がりくねる」)とは
別の意味(名詞、川の蛇行という地学用語)のため`meander (geology)`として
同綴り異義語(B17b)化して採用。

2026-09-08ユーザー指示「語彙拡充は各分野の中学高等学校相当の拡充、
小学校相当の拡充も多少あってもいいと思います」を受け、本バッチとは別に
`tag_domain_breadth_2026_09_08.py`(既存の中学・高校相当語をword_domain_
tagsで地学ドメインにも追加タグ付け)と`add_domain_breadth_elementary_
2026_09_08.py`(小学校〜中学相当の基本語を新規追加)を実施済み
(詳細はdocs/TODO.md参照)。本バッチ自体は当初の計画通り学部専門
レベル(level 850〜990+)のみ。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_geology_advanced.py
仕上げ: relevel.pyは実行しない(add_math_advanced.pyと同じ理由。既存の
H900/H990/H990Pリストに未対応でDOMAIN_BASE="地学"に一律で潰されるため)。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("absolute dating", "岩石や地層、化石などの年代を、放射性同位体の壊変(半減期)などの物理的手法を用いて具体的な年数(例:「約4600万年前」)で決定する年代測定法。地層の上下関係から新旧の順序のみを示す相対年代測定と対比される。", "名詞句", "Absolute dating using radioactive isotopes allows geologists to assign a specific numerical age to a rock sample.", "地学", "870"),
    ("abyssal plain", "大陸棚・大陸斜面の先、深海底(水深約3000〜6000m)に広がる、傾斜が非常に緩やかで平坦な海底地形。陸源堆積物や生物起源の堆積物が海底の起伏を埋めることで形成される。", "名詞句", "The abyssal plain stretches for thousands of kilometers across the ocean floor, remarkably flat and featureless.", "地学", "920"),
    ("aeolian process", "風の作用による侵食・運搬・堆積の一連の地質作用。乾燥地域や海岸砂丘などで、風が砂や細かい粒子を運び、砂丘や黄土(レス)などの地形を形成する。", "名詞句", "Aeolian processes have shaped the crescent-shaped dunes found throughout the desert.", "地学", "930"),
    ("alluvium", "河川の流れによって運搬され、河床・氾濫原・三角州などに堆積した、未固結の砂・シルト・粘土・礫などの堆積物。沖積層。", "名詞", "The fertile soil of the river delta is composed largely of alluvium deposited over thousands of years.", "地学", "900"),
    ("angular unconformity", "下位の地層が傾斜・褶曲した後に侵食され、その侵食面の上にほぼ水平な上位の地層が堆積している不整合。上下の地層が互いに斜めに交わる。傾斜不整合。", "名詞句", "At Siccar Point in Scotland, James Hutton famously observed an angular unconformity that helped establish the concept of deep geological time.", "地学", "930"),
    ("aquitard", "透水性が低く、地下水をほとんど通さないか、通しても非常にゆっくりとしか通さない地層。帯水層(aquifer)の間に挟まれ、地下水の上下方向の移動を妨げる働きをする。難透水層。", "名詞", "A thick layer of clay acted as an aquitard, slowing the downward movement of groundwater into the deeper aquifer.", "地学", "940"),
    ("artesian well", "帯水層が上下を難透水層に挟まれて密閉され(被圧帯水層)、地下水に静水圧がかかっている場合に、井戸を掘るとポンプなしで地下水が地表まで自然に湧出・噴出する井戸。掘り抜き井戸、自噴井。", "名詞句", "The artesian well produced a steady flow of water without any need for pumping.", "地学", "900"),
    ("assimilation (petrology)", "マグマが上昇・貫入する際に周囲の母岩(壁岩)を溶かし込み、その成分を取り込んでマグマ自体の化学組成を変化させる岩石学的な作用。同化作用。", "名詞", "Assimilation of surrounding limestone can alter the composition of a rising magma and produce unusual mineral assemblages.", "地学", "960"),
    ("asthenosphere", "リソスフェア(岩石圏)の下、地下約100〜660kmに広がる、部分的に融けており流動性・可塑性が高いマントル上部の層。プレートテクトニクスにおいてプレート(リソスフェア)がその上を滑るように動く「潤滑層」の役割を果たす。アセノスフェア、岩流圏。", "名詞", "Tectonic plates move slowly over the asthenosphere, which behaves in a plastic, semi-fluid manner over geological timescales.", "地学", "920"),
    ("base level", "河川がそれ以上下方侵食できない下限の高度・水位。最終的な基準は海水準であるが、湖やダム湖などが局所的・一時的な基準面(局地基準面)となることもある。侵食基準面。", "名詞句", "Sea level acts as the ultimate base level below which a river cannot erode its channel.", "地学", "900"),
    ("bathymetry", "海洋や湖沼の水深を測定し、その地形(海底・湖底の起伏)を明らかにする学問・技術。測深学。", "名詞", "Modern bathymetry relies on multibeam sonar to create detailed maps of the ocean floor.", "地学", "910"),
    ("Bowen's reaction series", "カナダの岩石学者ノーマン・L・ボーエンが実験的研究に基づき提唱した、玄武岩質マグマが冷却する際に晶出する主要な造岩鉱物の順序を示す系列。かんらん石から輝石・角閃石・黒雲母へと組成が段階的に変化する不連続系列と、カルシウムに富む斜長石からナトリウムに富む斜長石へと連続的に変化する連続系列からなる。ボーエンの反応系列。", "名詞句", "Bowen's reaction series explains the order in which minerals crystallize as a basaltic magma cools.", "地学", "960"),
    ("brittle deformation", "岩石が、弾性限界を超える応力を受けたときに、破断・破砕によって永久変形する変形様式。断層や節理(ジョイント)の形成など、低温・低圧(地殻の浅部)で生じやすい。脆性変形。", "名詞句", "In the upper crust, rocks tend to undergo brittle deformation, fracturing along faults rather than bending smoothly.", "地学", "920"),
    ("carbon-14 dating", "生物の遺骸や有機物に含まれる放射性同位体・炭素14(半減期約5730年)の残存量を測定し、その生物が死んでからの経過年数を求める年代測定法。数万年前までの比較的新しい試料の年代測定に用いられる。放射性炭素年代測定法。", "名詞句", "Carbon-14 dating showed that the ancient wooden artifact was roughly eight thousand years old.", "地学", "890"),
    ("contact metamorphism", "マグマが貫入した際に、その熱によって周囲の母岩(接触部)が変成作用を受けること。広範囲の圧力変化を伴わず、主に熱の影響によって鉱物組成や組織が変化する。接触変成作用。", "名詞句", "The intrusion of the granite pluton produced a zone of contact metamorphism in the surrounding shale.", "地学", "900"),
    ("continental slope", "大陸棚の外縁から深海底に向かって、比較的急な傾斜で落ち込んでいる海底地形。大陸地殻から海洋地殻への移行帯にあたる。大陸斜面。", "名詞句", "Beyond the edge of the continental shelf, the seafloor drops steeply along the continental slope.", "地学", "880"),
    ("core-mantle boundary", "地球内部の、固体のケイ酸塩質マントルと、その内側にある液体金属の外核との境界面。深さ約2900km、地震波(P波・S波)の伝わり方が急激に変化することから発見された。核-マントル境界。", "名詞句", "Seismic waves change dramatically in speed and behavior as they cross the core-mantle boundary.", "地学", "950"),
    ("crystal habit", "鉱物の結晶が示す、特徴的な外形・形態(柱状・板状・針状・塊状など)。結晶の内部構造(結晶系)は同じでも、成長条件によって現れる外見上の形は異なることがある。結晶癖、晶癖。", "名詞句", "Quartz can display a wide variety of crystal habits, from long prismatic points to compact, granular masses.", "地学", "890"),
    ("crystal system", "結晶を構成する原子・イオンの規則的な配列がもつ対称性に基づいて、結晶を分類する枠組み。立方晶系・正方晶系・斜方晶系・単斜晶系・三斜晶系・六方晶系・三方晶系に分類される。結晶系。", "名詞句", "Halite belongs to the cubic crystal system, which is why its crystals naturally form cube-like shapes.", "地学", "910"),
    ("deposition (geology)", "風・水・氷河などによって運搬されてきた砕屑物や、水中で沈殿した物質が、流速や運搬力の低下によって地表面や水底に積み重なること。堆積(作用)。", "名詞", "As the river slows near its mouth, deposition causes sediment to build up and form a delta.", "地学", "850"),
    ("differentiation (igneous)", "単一のマグマから、結晶分化作用や同化作用などの過程を経て、化学組成の異なる複数の火成岩が生じること。マグマの化学組成が冷却・結晶化の進行とともに変化していく現象全般を指す。マグマの分化作用。", "名詞", "Magmatic differentiation can produce a wide range of igneous rocks, from basalt to granite, from a single parent magma.", "地学", "940"),
    ("disconformity", "上下の地層がほぼ平行に重なっているものの、その境界面に長期間の侵食や堆積の中断(非堆積)を示す不整合。地層の傾斜には食い違いがないため、野外では見分けにくいことが多い。平行不整合。", "名詞", "The disconformity between the two limestone units represents a gap of several million years, even though the layers appear parallel.", "地学", "940"),
    ("drainage basin", "ある河川とその支流に降った雨水や雪解け水がすべて流れ込む範囲。周囲を分水嶺で囲まれた一つのまとまった集水域。流域。", "名詞句", "The Amazon's drainage basin covers a large portion of the South American continent.", "地学", "850"),
    ("ductile deformation", "岩石が、破断することなく、連続的な流動によって永久変形する変形様式。高温・高圧下(地殻深部)で生じやすく、褶曲構造の形成などに関わる。延性変形。", "名詞句", "Deep within the crust, high temperature and pressure cause rocks to undergo ductile deformation, bending and folding rather than breaking.", "地学", "940"),
    ("décollement", "変形した上位の地層と、その下の相対的に変形していない(あるいは異なる様式で変形した)地層とを分離する、水平に近い基底断層(すべり面)。褶曲・衝上断層帯の変形が及ぶ下限を示す。デコルマ、剥離断層。", "名詞", "The fold-and-thrust belt formed above a décollement that separated the deformed sedimentary cover from the undeformed basement below.", "地学", "990"),
    ("eon (geology)", "地質時代の区分の中で最大の単位。数億年から数十億年の長さをもち、複数の「代(era)」から構成される。地球の歴史は冥王代・太古代・原生代・顕生代の4つの累代(eon)に区分される。累代。", "名詞", "The Phanerozoic eon, which began about 539 million years ago, is the interval during which complex, visible life has flourished.", "地学", "890"),
    ("epoch (geology)", "地質時代の区分の中で、「紀(period)」よりも小さい単位。数百万年程度の長さをもつことが多い。例えば新第三紀は中新世・鮮新世という2つの「世(epoch)」に分けられる。世。", "名詞", "We are currently living in the Holocene epoch, which began roughly 11,700 years ago at the end of the last glacial period.", "地学", "890"),
    ("era (geology)", "地質時代の区分の中で、「累代(eon)」の下、「紀(period)」の上に位置する単位。数千万年から数億年の長さをもつ。顕生代は古生代・中生代・新生代の3つの「代(era)」に分けられる。代。", "名詞", "The extinction of the dinosaurs marks the boundary between the Mesozoic era and the Cenozoic era.", "地学", "870"),
    ("fault scarp", "断層運動によって地表にできる、急な崖状の地形。断層の両側で地盤の高さが食い違うことで生じる。断層崖。", "名詞句", "The earthquake produced a fault scarp several meters high, running for kilometers across the valley floor.", "地学", "900"),
    ("fluvial terrace", "かつての河床や氾濫原が、河川の下方侵食によって取り残され、現在の川面よりも高い位置に平坦な段状の地形として残されたもの。河成段丘。", "名詞句", "The fluvial terrace above the river marks the level of an ancient floodplain that has since been abandoned by downcutting.", "地学", "930"),
    ("fold axis", "褶曲構造において、地層面の曲がりが最も急激な部分(最大曲率の点)を結んだ、褶曲の中心を通る仮想的な直線(または曲線)。褶曲軸。", "名詞句", "The fold axis plunges gently to the northeast, indicating the direction in which the fold structure tilts.", "地学", "920"),
    ("foliation", "変成岩において、鉱物(特に雲母や角閃石などの板状・柱状鉱物)が一定の方向に配列することで生じる、面状・縞状の構造。片理。", "名詞", "The strong foliation in this schist is defined by parallel layers of mica crystals.", "地学", "930"),
    ("geochronology", "岩石・鉱物・地層の年代を測定し、地球の歴史における出来事の時間的な順序や絶対年代を明らかにする学問分野。地質年代学。", "名詞", "Geochronology relies heavily on the radioactive decay of isotopes such as uranium and potassium to establish the ages of rocks.", "地学", "930"),
    ("geoid", "地球の平均海水面を、陸地の下も含めて全地球に延長したと仮定した、重力による等ポテンシャル面。地球の形を表す基準面の一つとして測地学で用いられる。ジオイド。", "名詞", "The geoid is not a perfect sphere or ellipsoid; it bulges and dips slightly in response to variations in Earth's gravity field.", "地学", "960"),
    ("geologic time scale", "地球の歴史を、累代・代・紀・世・期といった単位に区分し、地層や化石の記録に基づいて年代順に整理した時間軸。国際層序委員会(ICS)によって国際的な基準が定められ、随時更新されている。地質年代表。", "名詞句", "The geologic time scale divides Earth's 4.6-billion-year history into eons, eras, periods, and epochs.", "地学", "900"),
    ("geomagnetic field", "地球が持つ磁場。主に外核内の液体金属(鉄・ニッケル)の対流運動によって生じる電流(ダイナモ作用)によって形成されると考えられている。地磁気。", "名詞句", "The geomagnetic field protects Earth's surface from much of the harmful solar wind and cosmic radiation.", "地学", "870"),
    ("geomorphology", "地表の地形が、どのような営力(河川・氷河・風・波浪・地殻変動など)によって形成され、どのように変化していくかを研究する学問分野。地形学。", "名詞", "Geomorphology examines how rivers, glaciers, and wind shape the landscapes we see today.", "地学", "890"),
    ("geothermal gradient", "地球内部で、深さが増すごとに温度が上昇していく割合。地殻の浅い部分では平均して1km深くなるごとに約25〜30℃上昇するとされる。地温勾配。", "名詞句", "The average geothermal gradient in the crust is about 25 to 30 degrees Celsius per kilometer of depth.", "地学", "890"),
    ("glacial period", "地球規模で気候が寒冷化し、氷河・氷床が拡大した時期。より大きな時間スケールでの寒冷な期間である氷河時代(ice age)の中でも、特に氷床が広がった相対的に寒い一時期を指すことが多い。氷期。", "名詞句", "During the last glacial period, ice sheets covered much of North America and northern Europe.", "地学", "870"),
    ("graben", "2本以上のほぼ平行な正断層に挟まれ、周囲(両側)に対して相対的に落ち込んだ細長い地塊。地溝。", "名詞", "The Rhine Valley is a classic example of a graben, formed as the crust stretched and the central block dropped down between parallel faults.", "地学", "930"),
    ("gravity anomaly", "ある地点で実際に観測された重力の値と、緯度・標高などから理論的に予測される重力の標準値との差。地下の密度分布の偏りを反映しており、地下構造の推定に利用される。重力異常。", "名詞句", "A positive gravity anomaly over the region suggested the presence of dense rock, such as an iron ore deposit, beneath the surface.", "地学", "940"),
    ("groundwater recharge", "降水や河川水、灌漑水などが地表から浸透し、帯水層に水が補給されること。地下水涵養。", "名詞句", "Groundwater recharge occurs when rainwater infiltrates the soil and percolates down to reach the water table.", "地学", "900"),
    ("horst", "2本以上のほぼ平行な正断層に挟まれ、周囲(両側)に対して相対的に隆起した細長い地塊。地塁。", "名詞", "The mountain range formed as a horst, uplifted between two parallel normal faults while the land on either side subsided.", "地学", "930"),
    ("hotspot (geology)", "プレートの動きとは無関係に、マントル深部からの高温物質(マントルプルーム)の上昇によって、地表(プレート内部やプレート境界から離れた場所)で持続的に火山活動が起こる地点。ホットスポット。", "名詞", "The Hawaiian Islands formed one after another as the Pacific Plate moved slowly over a stationary hotspot.", "地学", "890"),
    ("hydraulic conductivity", "地層や土壌が、水をどれだけ通しやすいかを表す量。ダルシーの法則における比例定数にあたり、透水係数とも呼ばれる。地層の間隙の大きさ・連結性や、流体の粘性などによって決まる。水理伝導率、透水係数。", "名詞句", "Sand has a much higher hydraulic conductivity than clay, allowing water to move through it far more easily.", "地学", "970"),
    ("hydrogeology", "地下水の分布・流動・水質、および地層(帯水層など)との相互作用を研究する学問分野。水理地質学。", "名詞", "Hydrogeology helps engineers determine the safest way to extract groundwater without depleting an aquifer.", "地学", "920"),
    ("ice age", "地球規模で気候が長期間にわたって寒冷化し、大陸規模の氷床が広がった地質学的な時代。氷期と間氷期が繰り返される、より大きな時間スケールでの寒冷期を指す。氷河時代。", "名詞句", "During the last ice age, much of what is now Canada was buried under thick sheets of ice.", "地学", "850"),
    ("index fossil", "ある特定の地質時代にのみ広範囲に生息し、進化速度が速く、化石として発見しやすいことから、地層の年代を特定・対比するための指標として用いられる化石。示準化石。", "名詞句", "Trilobites serve as important index fossils for dating rock layers from the Paleozoic era.", "地学", "880"),
    ("index mineral", "広域変成岩において、特定の温度・圧力条件(変成度)が達成されたときに初めて出現する鉱物。その出現によって変成度の等しい地域(変成分帯)を区分する指標として用いられる。示標鉱物。", "名詞句", "The first appearance of garnet is often used as an index mineral marking a specific grade of regional metamorphism.", "地学", "950"),
    ("interglacial period", "氷河時代の中で、氷期と氷期の間に挟まれた、比較的温暖な時期。氷床が後退し、海水準が上昇する。間氷期。", "名詞句", "We are currently living in an interglacial period known as the Holocene, which began about 11,700 years ago.", "地学", "870"),
    ("isostasy", "地殻が、その下にある密度の高いマントル(アセノスフェア)の上に浮力によって浮かんでいるように支えられているという、地殻均衡の考え方。氷床の融解などで地殻の荷重が変化すると、それに応じて地殻が上下に動く(隆起・沈降する)。アイソスタシー(地殻均衡)。", "名詞", "As the ice sheet melted, the land began to rise slowly due to isostasy.", "地学", "950"),
    ("joint (geology)", "岩石中に生じる、断層のようなずれ(変位)を伴わない亀裂(割れ目)。岩体の冷却・収縮や、上載荷重の除去、地殻変動による応力などによって形成される。節理。", "名詞", "Columnar basalt forms when cooling lava contracts and cracks into hexagonal joints.", "地学", "880"),
    ("karst topography", "石灰岩や苦灰岩(ドロマイト)などの水に溶けやすい岩石が、地下水による溶食作用を受けることで形成される、鍾乳洞・ドリーネ(すり鉢状の窪地)・石灰岩柱などを特徴とする独特の地形。カルスト地形。", "名詞句", "Karst topography is characterized by sinkholes, caves, and underground drainage systems carved out of soluble limestone.", "地学", "900"),
    ("knickpoint", "河川の縦断面において、勾配が急激に変化する地点。滝や急流の形成につながることが多く、下流側の下方侵食が上流側に向かって進行(遡上)する際の、その最先端の位置を示すことが多い。遷急点。", "名詞", "As the waterfall slowly retreats upstream, the knickpoint marks the boundary between the steep, actively eroding channel below and the gentler, older profile above.", "地学", "950"),
    ("law of superposition", "地層が乱されていない限り、下位にある地層ほど古く、上位にある地層ほど新しいとする地質学の基本原理。堆積の順序から地層の相対的な年代を判断する際の基礎となる。", "名詞句", "According to the law of superposition, the oldest rock layers in an undisturbed sequence lie at the bottom.", "地学", "900"),
    ("lineation", "変成岩や変形した岩石の中に見られる、鉱物の伸長配列や褶曲軸などによって形成される線状の構造の総称。面構造(片理・葉理)と組み合わさって岩石の変形履歴を示す指標となる。", "名詞", "The lineation defined by stretched mineral grains indicates the direction of tectonic transport during deformation.", "地学", "950"),
    ("lithosphere", "地殻と上部マントルの最上部を合わせた、剛体的に振る舞う地球最外殻の層。その下にある流動性の高いアセノスフェアの上をプレートとして移動する。", "名詞", "The lithosphere is broken into rigid plates that move slowly over the underlying asthenosphere.", "地学", "890"),
    ("luster", "鉱物の表面が光を反射する際の見た目の性質。金属光沢・ガラス光沢・真珠光沢・樹脂光沢・絹糸光沢などに分類され、鉱物の肉眼鑑定における基本的な判定項目の一つ。", "名詞", "Pyrite has a metallic luster that can easily be mistaken for gold.", "地学", "850"),
    ("magnetic reversal", "地球の磁場のN極とS極が入れ替わる現象。数十万年から数百万年に一度不規則な間隔で発生し、火成岩や海洋底の岩石に記録された残留磁化から過去の反転の履歴を復元できる。", "名詞句", "The last magnetic reversal, known as the Brunhes-Matuyama reversal, occurred about 780,000 years ago.", "地学", "930"),
    ("mantle plume", "マントル深部、しばしば核とマントルの境界付近から上昇してくる、周囲より高温の柱状の物質の流れ。プレート境界とは無関係な場所で火山活動を引き起こす「ホットスポット」の成因と考えられている。", "名詞句", "A mantle plume is thought to be responsible for the volcanic activity that formed the Hawaiian Islands.", "地学", "920"),
    ("meander (geology)", "(一般語彙にある「曲がりくねる」という動詞のmeanderとは別に)河川が平野部などの緩やかな勾配の土地を蛇行しながら流れる、弓状に湾曲した流路そのものを指す地形学・地学用語。侵食と堆積の繰り返しによって時間とともに形状を変え、湾曲が進むと三日月湖(oxbow lake)を残して流路が切り離されることがある。", "名詞", "Over centuries, the meander cut deeper into the outer bank while depositing sediment along the inner bank.", "地学", "870"),
    ("metamorphic facies", "特定の温度・圧力条件下で、異なる化学組成の岩石が共通して示す変成鉱物組み合わせのまとまりを指す分類概念。緑色片岩相・角閃岩相・グラニュライト相などがあり、変成岩が経験した温度・圧力条件を推定する指標となる。", "名詞句", "The presence of garnet and staurolite indicates that the rock reached amphibolite facies conditions.", "地学", "970"),
    ("mid-ocean ridge", "海洋底を貫いて連なる海底の巨大な山脈状の地形。プレートの発散境界にあたり、マントルから上昇したマグマが冷え固まって新しい海洋地殻を形成し続ける、海洋底拡大の中心地。", "名詞句", "New oceanic crust is continuously created at the mid-ocean ridge as tectonic plates move apart.", "地学", "880"),
    ("Milankovitch cycles", "地球の公転軌道の離心率・地軸の傾き(自転軸傾斜角)・歳差運動という3つの周期的な変動が組み合わさって、地球が受け取る日射量の分布を変化させ、氷期・間氷期のサイクルを引き起こすとする天文学的理論。", "名詞句", "Milankovitch cycles help explain the timing of glacial and interglacial periods over the past several hundred thousand years.", "地学", "950"),
    ("mineral zoning", "一つの鉱物結晶の内部で、中心部から外縁部にかけて化学組成が段階的または累帯的に変化している状態。結晶が成長する過程でのマグマや流体の組成変化・温度変化を記録している。", "名詞句", "Compositional mineral zoning in the plagioclase crystal reveals successive pulses of magma with different chemistries.", "地学", "980"),
    ("mineralogy", "鉱物の化学組成・結晶構造・物理的性質・成因・分類などを研究する地質学の一分野。", "名詞", "Mineralogy examines how the internal atomic structure of a mineral determines its physical properties, such as hardness and cleavage.", "地学", "870"),
    ("Moho (Mohorovičić discontinuity)", "地球の地殻とマントルの境界にあたる不連続面。この面を境に地震波(P波)の伝わる速度が急激に増加することから発見された。", "名詞", "Seismic waves suddenly speed up as they cross the Moho, marking the boundary between the crust and the mantle.", "地学", "930"),
    ("normal fault", "地殻が引っ張りの力(伸張応力)を受けることで生じる断層で、断層面の上側にある地盤(上盤)が下側の地盤(下盤)に対して相対的にずり下がるタイプの断層。", "名詞句", "A normal fault forms when the hanging wall slips downward relative to the footwall due to extensional stress.", "地学", "890"),
    ("oceanography", "海洋の物理的・化学的・生物学的・地質学的な性質や現象を総合的に研究する学問分野。海流・波・海水の化学組成・海底地形・海洋生物など幅広い対象を扱う。", "名詞", "Oceanography combines physics, chemistry, biology, and geology to study the world's oceans.", "地学", "870"),
    ("orogeny", "プレートの収束(衝突・沈み込み)によって山脈が形成される地殻変動の過程全体を指す。地層の褶曲・断層形成・変成作用・火成活動を伴うことが多い。", "名詞", "The collision between the Indian and Eurasian plates triggered the orogeny that produced the Himalayas.", "地学", "930"),
    ("oxbow lake", "蛇行河川の湾曲部が洪水などをきっかけに本流から切り離されてできる、三日月形をした孤立湖。", "名詞句", "When the river cut through the narrow neck of the meander, it left behind a crescent-shaped oxbow lake.", "地学", "860"),
    ("paleoclimatology", "地質時代の気候の変動を、堆積物・氷床コア・年輪・サンゴ・化石などの間接的な記録(プロキシデータ)を用いて復元・研究する学問分野。", "名詞", "Paleoclimatology relies on proxy data such as ice cores and tree rings to reconstruct past climate conditions.", "地学", "930"),
    ("paleomagnetism", "岩石中に残された過去の地球磁場の記録(残留磁化)を研究する学問分野。岩石が形成された当時の磁極の位置や、大陸の移動・回転の歴史を明らかにするために用いられる。", "名詞", "Paleomagnetism provided some of the strongest evidence supporting the theory of continental drift.", "地学", "950"),
    ("Pangaea", "約3億年前(古生代末)から中生代三畳紀にかけて存在したとされる、当時の全ての大陸が一つに結合していた超大陸。", "固有名詞", "Pangaea began to break apart roughly 200 million years ago, eventually giving rise to the continents we recognize today.", "地学", "870"),
    ("partial melting", "岩石を構成する複数の鉱物が異なる融点を持つため、加熱されても岩石全体が一度に溶けるのではなく、融点の低い鉱物成分から段階的に溶融していく現象。", "名詞句", "Partial melting of mantle rock beneath mid-ocean ridges generates the basaltic magma that forms new oceanic crust.", "地学", "920"),
    ("peneplain", "長期間にわたる侵食作用によって、山地がほぼ平坦な地形にまで削り取られた広大な準平原。侵食輪廻の最終段階(老年期)に対応する地形として提唱された概念。", "名詞", "Millions of years of erosion can wear down even tall mountains into a nearly flat peneplain.", "地学", "940"),
    ("permeability (hydrogeology)", "岩石や堆積物が、内部の間隙や割れ目を通じて水などの流体をどれだけ通しやすいかを示す性質。同じ間隙率(porosity)を持つ地層でも、間隙同士のつながり方によって透水性は大きく異なる。", "名詞", "Sandstone typically has high permeability because its pore spaces are well connected, allowing groundwater to flow easily.", "地学", "910"),
    ("petrology", "岩石の起源・組織・化学組成・鉱物組み合わせ・成因過程を研究する地質学の一分野。火成岩岩石学・堆積岩岩石学・変成岩岩石学に大別される。", "名詞", "Petrology investigates how the mineral composition and texture of a rock reveal the conditions under which it formed.", "地学", "880"),
    ("polymorphism (mineralogy)", "同じ化学組成を持つ鉱物が、結晶構造の違いによって異なる物理的性質を示す現象。ダイヤモンドと黒鉛(グラファイト)がともに炭素からなりながら全く異なる性質を持つことが代表例。", "名詞", "Diamond and graphite are classic examples of polymorphism, since both consist entirely of carbon atoms.", "地学", "950"),
    ("porosity (geology)", "岩石や堆積物の全体積に対する、粒子間の空隙(間隙)の体積が占める割合。地下水や石油・天然ガスをどれだけ蓄えられるかを左右する基本的な性質。", "名詞", "Porosity determines how much groundwater a rock formation can potentially store.", "地学", "900"),
    ("porphyritic texture", "火成岩の組織の一種で、比較的大きな結晶(斑晶)が、より細粒な結晶やガラス質からなる基質(石基)の中に散在している状態。マグマが地下で徐々に冷えた後、急速に地表または地表付近で冷却されたことを示す。", "名詞句", "The porphyritic texture of the volcanic rock, with large feldspar crystals set in a fine-grained groundmass, suggests two distinct stages of cooling.", "地学", "910"),
    ("protolith", "変成作用を受ける前の、その変成岩のもととなった元の岩石。変成岩の起源を議論する際に用いられる。", "名詞", "By analyzing relict textures and chemical composition, geologists identified shale as the protolith of the slate.", "地学", "950"),
    ("proxy data (climate)", "直接の観測記録が存在しない過去の気候について、その代わりとなる間接的な指標から推定される情報。氷床コア中の同位体比、年輪の幅、サンゴや堆積物の化学組成などが用いられる。", "名詞句", "Ice cores provide proxy data that scientists use to estimate atmospheric temperatures from hundreds of thousands of years ago.", "地学", "950"),
    ("radiometric dating", "岩石や鉱物に含まれる放射性同位体が一定の速さ(半減期)で崩壊していく性質を利用して、その岩石や鉱物が形成されてからの経過年代を数値で算出する年代測定法の総称。", "名詞句", "Radiometric dating allows geologists to assign an actual numerical age, rather than just a relative age, to a rock sample.", "地学", "900"),
    ("regional metamorphism", "プレートの収束や造山運動に伴い、広範囲にわたって高い圧力と温度が同時に作用することで生じる変成作用。造山帯に広く分布する片岩・片麻岩などを形成する。", "名詞句", "Regional metamorphism occurs over large areas where tectonic forces subject rocks to both high pressure and high temperature.", "地学", "920"),
    ("relative dating", "地層や化石、地質構造の間の位置関係や重なりの順序から、ある地質学的事象が別の事象より古いか新しいかという相対的な前後関係を判断する年代測定法。数値としての絶対年代は与えない。", "名詞句", "Relative dating uses principles like superposition and cross-cutting relationships to determine the order in which geological events occurred.", "地学", "870"),
    ("seismic tomography", "世界各地で発生する地震の波を多数の観測点で記録し、その伝播速度のわずかな違いを解析することで、地球内部(マントルや核)の三次元的な温度・密度構造を画像化する手法。医療用CTスキャンに類似した原理を用いる。", "名詞句", "Seismic tomography has revealed that subducted oceanic plates can sink as deep as the boundary between the mantle and the core.", "地学", "980"),
    ("seismology", "地震の発生機構、地震波の伝播、それに伴う地球内部構造を研究する学問分野。", "名詞", "Seismology studies the waves generated by earthquakes to understand both fault mechanics and Earth's internal structure.", "地学", "890"),
    ("silicate mineral", "ケイ素と酸素からなる四面体構造(SiO4四面体)を基本単位として構成される鉱物の総称。地殻を構成する鉱物の大部分(体積比で9割以上)を占める最も重要な鉱物グループ。", "名詞句", "Silicate minerals, built from SiO4 tetrahedra, make up the vast majority of rock-forming minerals in Earth's crust.", "地学", "880"),
    ("solid solution series", "ある鉱物の結晶構造の中で、特定の元素が別の元素と自由に置き換わることができ、両端成分の間で化学組成が連続的に変化する一連の鉱物系列。オリビン(かんらん石)や斜長石が代表例。", "名詞句", "The plagioclase solid solution series ranges continuously from calcium-rich anorthite to sodium-rich albite.", "地学", "980"),
    ("stalactite", "石灰岩の洞窟の天井から、炭酸カルシウムを含む水がしずくとなって滴り落ちる際に少しずつ沈殿することで、つらら状に垂れ下がって成長する鍾乳石。", "名詞", "A stalactite grows downward from the ceiling of a limestone cave as mineral-laden water slowly drips and evaporates.", "地学", "850"),
    ("stalagmite", "石灰岩の洞窟の床に、天井から滴り落ちた炭酸カルシウムを含む水滴が少しずつ沈殿することで、下から上へ塔状に成長する石筍。", "名詞", "A stalagmite forms on a cave floor as drops of mineral-rich water accumulate and deposit calcium carbonate over time.", "地学", "850"),
    ("stratigraphic column", "ある地域における地層の重なりの順序と、各層の岩相・層厚・含まれる化石などをまとめて図示した柱状の図表。地層累重の法則に基づき、下から上へ向かって古い時代から新しい時代の順に並べられる。", "名詞句", "The stratigraphic column for the region shows a sequence of sandstone, shale, and limestone layers spanning millions of years.", "地学", "900"),
    ("stratigraphy", "地層の性質・重なりの順序・分布・形成過程を研究し、地層を年代や成因に基づいて区分・対比する地質学の一分野。", "名詞", "Stratigraphy allows geologists to correlate rock layers across different regions based on their composition, fossils, and age.", "地学", "900"),
    ("streak (mineralogy)", "鉱物を素焼きの陶板(条痕板)にこすりつけたときに残る粉末の色。鉱物そのものの外見上の色(見かけの色)とは異なる場合があり、鉱物の同定に用いられる信頼性の高い性質。", "名詞", "Although pyrite looks golden, its streak is greenish-black, which helps distinguish it from real gold.", "地学", "870"),
    ("strike and dip", "傾斜した地層面や断層面などの三次元的な向きを表現するための、地質学における2つの基本的な測定値。走向(strike)は面と水平面が交わる線の方位、傾斜(dip)はその走向線に直交する方向に測った面の傾き角度を指す。", "名詞句", "Geologists use a compass and clinometer to measure the strike and dip of a rock layer in the field.", "地学", "900"),
    ("strike-slip fault", "断層をはさんだ両側の地盤が、ほぼ水平方向にすれ違うように動く断層。断層面はほぼ垂直で、上下方向のずれをほとんど伴わない。", "名詞句", "The San Andreas Fault is a well-known strike-slip fault where the Pacific and North American plates slide horizontally past each other.", "地学", "900"),
    ("supercontinent cycle", "地球の歴史を通じて、複数の大陸がおよそ数億年周期で一つの超大陸に集合しては再び分裂するという、大陸配置の大規模な周期性を説明する仮説的な理論。ウィルソンサイクルをより地球規模・長期的視点に拡張した概念として位置づけられることが多い。", "名詞句", "The supercontinent cycle suggests that continents periodically converge into a single landmass roughly every few hundred million years.", "地学", "990+"),
    ("terrane", "周囲の地質とは異なる独自の地質学的な形成史を持ち、断層によって境界付けられた地殻の一区画。もともと別の場所で形成された後、プレート運動によって運ばれ、大陸縁辺に付加(集積)したものが多い。", "名詞", "The terrane was originally a volcanic island arc that collided with and became part of the continental margin.", "地学", "960"),
    ("thermohaline circulation", "海水の温度(thermo-)と塩分(-haline)の違いによって生じる密度差を駆動力とする、地球規模の大規模な海洋循環。表層の暖かい海水と深層の冷たく塩分濃度の高い海水が、数百年から千年規模の時間をかけて世界の海洋を巡る。", "名詞句", "Thermohaline circulation transports heat from the tropics toward the poles, playing a major role in regulating global climate.", "地学", "960"),
    ("thrust fault", "地殻が強い水平方向の圧縮力を受けることで生じる断層のうち、断層面の傾斜が比較的緩やか(一般に45度未満)で、上盤が下盤の上に大きくのし上がるように移動するタイプの逆断層。", "名詞句", "A thrust fault allows older rock layers to be pushed up and over younger layers along a gently inclined fault plane.", "地学", "910"),
    ("twinning (crystallography)", "一つの結晶の中に、規則的な対称関係(鏡映や回転など)を保ちながら異なる方位を持つ二つ以上の結晶部分が規則的に結合して成長する現象。", "名詞", "Twinning in the mineral causes it to display two intergrown crystal orientations that are mirror images of each other.", "地学", "970"),
    ("upwelling (oceanography)", "深層の冷たく栄養塩に富んだ海水が、風の作用などによって表層へ湧き上がってくる海洋現象。豊かな漁場を形成する重要な要因となる。", "名詞", "Upwelling brings nutrient-rich deep water to the surface, supporting some of the most productive fishing grounds in the world.", "地学", "930"),
    ("uranium-lead dating", "ウランが最終的に鉛の安定同位体へと崩壊していく際の半減期を利用した放射年代測定法。ジルコンなどの鉱物に適用され、地球上で最も古い岩石や隕石の年代測定にも用いられる、信頼性の高い手法として知られる。", "名詞句", "Uranium-lead dating of zircon crystals has helped scientists determine the age of some of the oldest rocks on Earth.", "地学", "980"),
    ("Wadati-Benioff zone", "海洋プレートが別のプレートの下に沈み込んでいく境界に沿って、深発地震・中発地震が帯状に分布する領域。沈み込むプレートの傾斜を反映して、海溝から陸側・深部へ向かうにつれて震源が深くなっていく。", "名詞句", "Earthquakes along the Wadati-Benioff zone become progressively deeper as they trace the descending path of the subducting plate.", "地学", "990"),
    ("water table", "地下において、土壌や岩石の間隙が水で完全に満たされている飽和帯の最上面。この面より上は不飽和帯(間隙の一部に空気を含む)、下は飽和帯となる。", "名詞句", "The water table rises during the rainy season as more precipitation infiltrates into the ground.", "地学", "870"),
    ("Wilson cycle", "超大陸の分裂とそれに伴う新たな海洋の形成・拡大、その後の海洋プレートの沈み込みによる海洋の縮小、そして大陸同士の衝突による新たな超大陸の形成という一連の過程が繰り返されるという、プレートテクトニクスにおける大規模な周期理論。", "名詞句", "The Wilson cycle describes how oceans open and close as supercontinents repeatedly break apart and reassemble.", "地学", "970"),
    ("yardang", "乾燥地域において、風による侵食(主に風に運ばれた砂粒による研磨作用)を長期間受けることで形成される、卓越風の方向に沿って細長く伸びた流線形の岩石丘・地形。", "名詞", "Strong, persistent winds carved the yardang into a long, streamlined ridge aligned with the prevailing wind direction.", "地学", "970"),]


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

    print(f"words:   +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print("totals -> words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
        if WORDS:
            dom = WORDS[0][4]
            print(f"totals -> {dom}:",
                  conn.execute(
                      "SELECT COUNT(*) FROM words WHERE domain=?", (dom,)
                  ).fetchone()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
