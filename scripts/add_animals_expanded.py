# ruff: noqa: E501  (data-heavy seed script: long word/example lines are fine)
"""Bulk-add curated vocabulary for the ANIMALS domain (動物), authored by Claude.

背景: `words` テーブルには既に cat/dog/lion/tiger/elephant/giraffe/zebra/monkey/
horse/cow/pig/sheep/goat/rabbit/mouse/fox/deer/duck/chicken/frog/snake/bee/ant/
bird 等、基本的な動物語彙が約120語ある。本スクリプトはそこから範囲を大きく広げ、
以下を体系的に補強する:

  - 哺乳類の裾野（有袋類・霊長類・げっ歯類・大型ネコ科・海洋哺乳類など）
  - 鳥類の基礎を超えた語彙（猛禽・水鳥・飛べない鳥・鳴き鳥など）
  - 爬虫類・両生類（トカゲ・ヘビ・カメ・カエルの仲間の広がり）
  - 魚類・海洋生物（甲殻類・軟体動物・サンゴ礁の生き物など）
  - 昆虫・節足動物（甲虫・チョウの変態・節足動物の分類語彙）
  - 解剖・生態・分類の語彙（肉食/草食/雑食、生息地、渡り、冬眠、擬態、
    毒性、絶滅危惧、群れの呼び方、繁殖・子育てに関する語など）
  - 農場動物・幼獣の呼び名・飼育施設（子牛、子豚、畜舎など）

レベルは "300"〜"990+" のスケール全体に意図的に分散させている。ごく身近な
動物（koala, zoo, bird, fish 等）は 300 台、やや専門的な分類・生態語彙
（marsupial, venomous, domesticated 等）は 800 台、真に専門的な語
（diurnal, gestation 等）は 850〜900 に置いた。990/990+ 相当の語は今回は
該当なしと判断し使用していない。

内容方針: 事実に基づく教育的な語彙のみ。動物の死や狩猟については
predator/prey のような中立的な生物学用語の範囲にとどめ、生々しい描写は
含めない。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased), checked
against the ENTIRE words table (not just domain=動物).

Run:  python scripts/add_animals_expanded.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 哺乳類（有袋類・霊長類・海洋哺乳類など） ---
    ("koala", "コアラ", "名詞", "Koalas sleep for up to 20 hours a day.", "動物", "300"),
    ("hippopotamus", "カバ", "名詞", "A hippopotamus can weigh over a ton.", "動物", "350"),
    ("rhinoceros", "サイ", "名詞", "The rhinoceros has thick, tough skin.", "動物", "350"),
    ("platypus", "カモノハシ", "名詞", "The platypus is one of the few mammals that lay eggs.", "動物", "650"),
    ("sloth", "ナマケモノ", "名詞", "Sloths move very slowly through the trees.", "動物", "550"),
    ("armadillo", "アルマジロ", "名詞", "An armadillo can roll itself into a ball for protection.", "動物", "650"),
    ("anteater", "アリクイ", "名詞", "An anteater uses its long tongue to eat ants.", "動物", "600"),
    ("chimpanzee", "チンパンジー", "名詞", "Chimpanzees are known for using simple tools.", "動物", "450"),
    ("orangutan", "オランウータン", "名詞", "Orangutans spend most of their lives in trees.", "動物", "500"),
    ("baboon", "ヒヒ", "名詞", "Baboons live in large social groups called troops.", "動物", "600"),
    ("lemur", "キツネザル", "名詞", "Lemurs are found only on the island of Madagascar.", "動物", "650"),
    ("meerkat", "ミーアキャット", "名詞", "Meerkats take turns standing guard for predators.", "動物", "600"),
    ("mongoose", "マングース", "名詞", "A mongoose is famous for fighting venomous snakes.", "動物", "650"),
    ("porcupine", "ヤマアラシ", "名詞", "A porcupine's quills protect it from predators.", "動物", "600"),
    ("beaver", "ビーバー", "名詞", "Beavers build dams out of branches and mud.", "動物", "500"),
    ("chipmunk", "シマリス", "名詞", "The chipmunk stuffed acorns into its cheeks.", "動物", "450"),
    ("shrew", "トガリネズミ", "名詞", "A shrew has to eat almost constantly to survive.", "動物", "750"),
    ("opossum", "オポッサム", "名詞", "An opossum sometimes plays dead when it feels threatened.", "動物", "650"),
    ("skunk", "スカンク", "名詞", "A skunk sprays a foul-smelling liquid when scared.", "動物", "500"),
    ("lynx", "オオヤマネコ", "名詞", "The lynx has tufted ears and a short tail.", "動物", "650"),
    ("cheetah", "チーター", "名詞", "The cheetah is the fastest land animal.", "動物", "400"),
    ("jaguar", "ジャガー", "名詞", "The jaguar is the largest cat in the Americas.", "動物", "450"),
    ("cougar", "ピューマ・マウンテンライオン", "名詞", "The cougar is also known as the mountain lion.", "動物", "550"),
    ("hyena", "ハイエナ", "名詞", "Hyenas have an extremely powerful bite.", "動物", "500"),
    ("jackal", "ジャッカル", "名詞", "Jackals often scavenge for food left by larger predators.", "動物", "700"),
    ("bison", "バイソン・アメリカバイソン", "名詞", "Millions of bison once roamed the American plains.", "動物", "500"),
    ("moose", "ヘラジカ", "名詞", "The moose is the largest species of deer.", "動物", "450"),
    ("elk", "アメリカアカシカ", "名詞", "A male elk grows large antlers each year.", "動物", "650"),
    ("reindeer", "トナカイ", "名詞", "Reindeer are common in the cold north of Europe.", "動物", "400"),
    ("caribou", "カリブー（北米のトナカイ）", "名詞", "Wild caribou migrate long distances every year.", "動物", "700"),
    ("antelope", "アンテロープ・レイヨウ", "名詞", "Antelope can run extremely fast to escape predators.", "動物", "500"),
    ("gazelle", "ガゼル", "名詞", "A gazelle can leap several meters in a single bound.", "動物", "500"),
    ("wildebeest", "ヌー", "名詞", "Millions of wildebeest cross the plains each year in search of grass.", "動物", "700"),
    ("tapir", "バク", "名詞", "A tapir has a short, flexible snout like a small trunk.", "動物", "800"),
    ("llama", "リャマ", "名詞", "Farmers use llamas to carry heavy loads in the mountains.", "動物", "500"),
    ("alpaca", "アルパカ", "名詞", "Alpaca wool is soft and warm.", "動物", "500"),
    ("yak", "ヤク", "名詞", "Yaks are well suited to life at high altitudes.", "動物", "600"),
    ("donkey", "ロバ", "名詞", "A donkey carried supplies up the narrow mountain path.", "動物", "400"),
    ("mule", "ラバ（ロバと馬の交雑種）", "名詞", "A mule is a cross between a horse and a donkey.", "動物", "550"),
    ("ox", "去勢した雄牛", "名詞", "The farmer used an ox to pull the plow.", "動物", "450"),
    ("bull", "雄牛", "名詞", "The bull charged at the red cloth.", "動物", "400"),
    ("foal", "子馬", "名詞", "The mare gave birth to a healthy foal.", "動物", "550"),
    ("piglet", "子豚", "名詞", "The piglets followed their mother around the pen.", "動物", "500"),
    ("lamb", "子羊", "名詞", "The lamb stayed close to its mother in the field.", "動物", "400"),
    ("kitten", "子猫", "名詞", "The kitten chased a ball of yarn across the floor.", "動物", "350"),
    ("puppy", "子犬", "名詞", "The puppy wagged its tail excitedly.", "動物", "350"),
    ("cub", "（クマ・ライオンなどの）子", "名詞", "The lioness watched over her cubs closely.", "動物", "450"),
    ("walrus", "セイウチ", "名詞", "A walrus uses its long tusks to haul itself onto ice.", "動物", "450"),
    ("manatee", "マナティー", "名詞", "Manatees are gentle, slow-moving sea mammals.", "動物", "600"),
    ("narwhal", "イッカク", "名詞", "The narwhal is known for its long, spiral tusk.", "動物", "650"),
    ("orca", "シャチ（キラーホエールとも）", "名詞", "Orcas hunt in coordinated family groups.", "動物", "500"),
    ("sperm whale", "マッコウクジラ", "名詞", "The sperm whale has the largest brain of any animal.", "動物", "600"),
    ("humpback whale", "ザトウクジラ", "名詞", "Humpback whales are known for their complex songs.", "動物", "550"),
    ("blue whale", "シロナガスクジラ", "名詞", "The blue whale is the largest animal on Earth.", "動物", "500"),
    ("polar bear", "ホッキョクグマ", "名詞", "Polar bears hunt seals on the sea ice.", "動物", "350"),
    ("grizzly bear", "グリズリー（ハイイログマ）", "名詞", "Grizzly bears can be very dangerous when surprised.", "動物", "450"),
    ("black bear", "アメリカクロクマ", "名詞", "Black bears are common in North American forests.", "動物", "450"),
    ("red panda", "レッサーパンダ", "名詞", "The red panda looks like a mix of a cat and a raccoon.", "動物", "500"),
    ("wolverine", "クズリ", "名詞", "The wolverine is a fierce hunter despite its small size.", "動物", "750"),
    ("ferret", "フェレット", "名詞", "Some people keep ferrets as playful pets.", "動物", "550"),
    ("vole", "ハタネズミ", "名詞", "A vole looks similar to a mouse but has a shorter tail.", "動物", "800"),
    ("gopher", "ホリネズミ", "名詞", "Gophers dig extensive tunnels underground.", "動物", "700"),
    ("guinea pig", "モルモット", "名詞", "Children often keep guinea pigs as a first pet.", "動物", "450"),
    ("hamster", "ハムスター", "名詞", "The hamster ran on its wheel all night.", "動物", "400"),
    ("gerbil", "スナネズミ", "名詞", "A gerbil needs plenty of space to burrow.", "動物", "650"),
    ("marsupial", "有袋類", "名詞", "A kangaroo is a marsupial that carries its young in a pouch.", "動物", "800"),
    ("primate", "霊長類", "名詞", "Humans and gorillas both belong to the primate family.", "動物", "800"),
    ("rodent", "齧歯類（げっしるい）", "名詞", "Mice and squirrels are both rodents.", "動物", "750"),
    # --- 鳥類 ---
    ("flamingo", "フラミンゴ", "名詞", "Flamingos often stand on one leg while resting.", "動物", "400"),
    ("peacock", "クジャク", "名詞", "The peacock spread its colorful tail feathers.", "動物", "400"),
    ("woodpecker", "キツツキ", "名詞", "A woodpecker was drumming on the old tree trunk.", "動物", "500"),
    ("hummingbird", "ハチドリ", "名詞", "A hummingbird can hover in place while feeding.", "動物", "500"),
    ("ostrich", "ダチョウ", "名詞", "The ostrich is the largest bird but cannot fly.", "動物", "400"),
    ("parrot", "オウム・インコ", "名詞", "The parrot learned to repeat several phrases.", "動物", "400"),
    ("toucan", "オオハシ", "名詞", "A toucan is easy to recognize by its huge, colorful beak.", "動物", "550"),
    ("kingfisher", "カワセミ", "名詞", "The kingfisher dove into the river to catch a fish.", "動物", "650"),
    ("seagull", "カモメ", "名詞", "Seagulls gathered near the fishing boats.", "動物", "400"),
    ("albatross", "アホウドリ", "名詞", "An albatross can glide over the ocean for hours without flapping its wings.", "動物", "700"),
    ("pelican", "ペリカン", "名詞", "The pelican scooped fish into its large throat pouch.", "動物", "550"),
    ("stork", "コウノトリ", "名詞", "A stork built its nest on top of the chimney.", "動物", "500"),
    ("vulture", "ハゲタカ・ハゲワシ", "名詞", "Vultures circled high above, looking for food.", "動物", "550"),
    ("raven", "ワタリガラス", "名詞", "The raven is larger and smarter than the common crow.", "動物", "550"),
    ("magpie", "カササギ", "名詞", "The magpie is known for collecting shiny objects.", "動物", "600"),
    ("robin", "コマドリ・アメリカコマドリ", "名詞", "Seeing a robin is often considered a sign of spring.", "動物", "450"),
    ("cardinal", "ショウジョウコウカンチョウ", "名詞", "The bright red cardinal perched on the fence.", "動物", "500"),
    ("blue jay", "アオカケス", "名詞", "A blue jay screeched loudly from the branch.", "動物", "550"),
    ("canary", "カナリア", "名詞", "Canaries are known for their beautiful singing voice.", "動物", "500"),
    ("cuckoo", "カッコウ", "名詞", "The cuckoo lays its eggs in other birds' nests.", "動物", "600"),
    ("nightingale", "ナイチンゲール（サヨナキドリ）", "名詞", "The nightingale is famous for its beautiful song.", "動物", "650"),
    ("turkey", "シチメンチョウ", "名詞", "Families often eat turkey on Thanksgiving.", "動物", "350"),
    ("goose", "ガチョウ", "名詞", "A goose hissed loudly to protect its nest.", "動物", "400"),
    ("quail", "ウズラ", "名詞", "The quail hid quietly in the tall grass.", "動物", "600"),
    ("pheasant", "キジ", "名詞", "The pheasant has strikingly colorful feathers.", "動物", "650"),
    ("kiwi", "キーウィ（キーウィ鳥）", "名詞", "The kiwi is a flightless bird native to New Zealand.", "動物", "550"),
    ("emu", "エミュー", "名詞", "The emu is the second-largest living bird after the ostrich.", "動物", "550"),
    ("cockatoo", "オウム（バタン）", "名詞", "The cockatoo has a distinctive crest on its head.", "動物", "650"),
    ("macaw", "コンゴウインコ", "名詞", "Macaws are known for their brilliant, colorful feathers.", "動物", "650"),
    ("puffin", "ニシツノメドリ", "名詞", "Puffins nest in burrows along rocky cliffs.", "動物", "600"),
    ("chick", "ひな鳥・ひよこ", "名詞", "The mother hen watched over her chicks.", "動物", "350"),
    ("hatchling", "孵化したばかりの幼体", "名詞", "The sea turtle hatchlings crawled toward the ocean.", "動物", "650"),
    ("talon", "（猛禽類の）かぎ爪", "名詞", "The eagle gripped the fish tightly with its talons.", "動物", "700"),
    ("plumage", "羽毛（一式）", "名詞", "The male bird's bright plumage attracts mates.", "動物", "750"),
    ("migrate", "渡る・移動する", "動詞", "Many birds migrate south for the winter.", "動物", "600"),
    # --- 爬虫類・両生類 ---
    ("alligator", "アリゲーター", "名詞", "An alligator has a broader snout than a crocodile.", "動物", "450"),
    ("gecko", "ヤモリ", "名詞", "A gecko can climb smooth walls with its sticky feet.", "動物", "500"),
    ("iguana", "イグアナ", "名詞", "The iguana basked in the sun on a warm rock.", "動物", "550"),
    ("chameleon", "カメレオン", "名詞", "A chameleon can change color to match its surroundings.", "動物", "550"),
    ("tortoise", "リクガメ", "名詞", "Unlike turtles, a tortoise lives entirely on land.", "動物", "450"),
    ("salamander", "サンショウウオ", "名詞", "A salamander can regrow a lost tail.", "動物", "600"),
    ("newt", "イモリ", "名詞", "The newt lives in water during part of its life.", "動物", "700"),
    ("toad", "ヒキガエル", "名詞", "A toad has drier, bumpier skin than a frog.", "動物", "450"),
    ("python", "ニシキヘビ", "名詞", "A python wraps around its prey and squeezes tightly.", "動物", "450"),
    ("viper", "クサリヘビ", "名詞", "The viper's bite injects a dangerous venom.", "動物", "650"),
    ("cobra", "コブラ", "名詞", "A cobra raises its head and spreads its hood when threatened.", "動物", "500"),
    ("rattlesnake", "ガラガラヘビ", "名詞", "A rattlesnake shakes its tail to warn off predators.", "動物", "550"),
    ("komodo dragon", "コモドオオトカゲ", "名詞", "The komodo dragon is the largest living lizard.", "動物", "700"),
    # --- 魚類・海洋生物 ---
    ("fish", "魚", "名詞", "We caught several fish in the lake this morning.", "動物", "300"),
    ("ray", "エイ", "名詞", "A ray glided gracefully along the ocean floor.", "動物", "600"),
    ("stingray", "アカエイ", "名詞", "A stingray has a sharp barb on its tail.", "動物", "600"),
    ("eel", "ウナギ", "名詞", "The eel slid silently through the murky water.", "動物", "550"),
    ("squid", "イカ", "名詞", "A squid can shoot ink to escape predators.", "動物", "500"),
    ("starfish", "ヒトデ", "名詞", "A starfish can regrow an arm that it loses.", "動物", "450"),
    ("lobster", "ロブスター・オマール海老", "名詞", "The lobster has two large claws in front.", "動物", "500"),
    ("shrimp", "エビ（小型）", "名詞", "Shrimp are a popular ingredient in many dishes.", "動物", "450"),
    ("coral", "サンゴ", "名詞", "Coral reefs support an enormous variety of marine life.", "動物", "500"),
    ("clownfish", "カクレクマノミ", "名詞", "A clownfish lives safely among the tentacles of a sea anemone.", "動物", "450"),
    ("salmon", "サケ・サーモン", "名詞", "Salmon swim upstream to lay their eggs.", "動物", "450"),
    ("tuna", "マグロ", "名詞", "Tuna are large, fast-swimming fish found in open ocean water.", "動物", "450"),
    ("goldfish", "金魚", "名詞", "The children fed the goldfish every morning.", "動物", "350"),
    ("catfish", "ナマズ", "名詞", "A catfish uses its whiskers to sense food in murky water.", "動物", "500"),
    ("swordfish", "メカジキ", "名詞", "The swordfish gets its name from its long, flat bill.", "動物", "550"),
    ("seahorse", "タツノオトシゴ", "名詞", "Unlike most fish, male seahorses carry the eggs.", "動物", "500"),
    ("clam", "二枚貝・ハマグリ", "名詞", "The clam buried itself in the wet sand.", "動物", "500"),
    ("oyster", "カキ", "名詞", "An oyster sometimes forms a pearl inside its shell.", "動物", "500"),
    ("mussel", "ムール貝・イガイ", "名詞", "Mussels attach themselves tightly to rocks.", "動物", "600"),
    ("barnacle", "フジツボ", "名詞", "Barnacles cling to the bottom of ships.", "動物", "700"),
    ("sea anemone", "イソギンチャク", "名詞", "A sea anemone looks like a colorful underwater flower.", "動物", "650"),
    ("plankton", "プランクトン", "名詞", "Plankton form the base of the entire ocean food chain.", "動物", "700"),
    ("fin", "ひれ", "名詞", "The shark's fin cut through the surface of the water.", "動物", "500"),
    ("gill", "えら", "名詞", "Fish breathe by taking in oxygen through their gills.", "動物", "600"),
    # --- 昆虫・節足動物 ---
    ("scorpion", "サソリ", "名詞", "A scorpion's sting can be very painful.", "動物", "500"),
    ("millipede", "ヤスデ", "名詞", "A millipede has far more legs than a centipede.", "動物", "650"),
    ("caterpillar", "幼虫（チョウ・ガの）", "名詞", "The caterpillar will eventually turn into a butterfly.", "動物", "400"),
    ("cocoon", "繭（まゆ）", "名詞", "The moth spun a cocoon before its transformation.", "動物", "600"),
    ("chrysalis", "さなぎ（チョウの）", "名詞", "A butterfly emerges from its chrysalis after about two weeks.", "動物", "750"),
    ("pupa", "蛹（さなぎ）", "名詞", "Many insects pass through a pupa stage before becoming adults.", "動物", "750"),
    ("silkworm", "カイコ", "名詞", "Silkworms produce the thread used to make silk fabric.", "動物", "650"),
    ("firefly", "ホタル", "名詞", "Fireflies lit up the summer evening with tiny flashes.", "動物", "500"),
    ("praying mantis", "カマキリ", "名詞", "A praying mantis holds its front legs together as if praying.", "動物", "600"),
    ("stick insect", "ナナフシ", "名詞", "A stick insect is almost invisible against a twig.", "動物", "650"),
    ("earwig", "ハサミムシ", "名詞", "An earwig has small pincers at the tip of its abdomen.", "動物", "750"),
    ("arthropod", "節足動物", "名詞", "Insects and spiders are both types of arthropods.", "動物", "850"),
    ("invertebrate", "無脊椎動物", "名詞", "A worm is a simple invertebrate with no backbone.", "動物", "800"),
    ("vertebrate", "脊椎動物", "名詞", "Fish, birds, and mammals are all vertebrates.", "動物", "800"),
    ("pincer", "はさみ（カニなどの）", "名詞", "The crab snapped its pincers at the passing fish.", "動物", "700"),
    # --- 動物の分類・生態・行動語彙 ---
    ("offspring", "子孫・子", "名詞", "A mother bear fiercely protects her offspring.", "動物", "700"),
    ("litter", "（動物の）一腹の子", "名詞", "The dog gave birth to a litter of six puppies.", "動物", "650"),
    ("pack", "群れ（オオカミなどの）", "名詞", "Wolves usually hunt together in a pack.", "動物", "500"),
    ("brood", "ひとかえりのひな・一腹の子（鳥の）", "名詞", "The hen led her brood of chicks across the yard.", "動物", "700"),
    ("school", "群れ（魚の）", "名詞", "A large school of fish moved as one across the reef.", "動物", "500"),
    ("domesticated", "家畜化された・飼いならされた", "形容詞", "Dogs were among the first animals to be domesticated.", "動物", "800"),
    ("wild", "野生の", "形容詞", "It's dangerous to approach wild animals in the forest.", "動物", "300"),
    ("camouflage", "保護色・カモフラージュ", "名詞", "The lizard's camouflage made it hard to spot among the leaves.", "動物", "700"),
    ("venomous", "毒を持つ（咬む・刺す動物）", "形容詞", "That spider looks venomous, so don't touch it.", "動物", "800"),
    ("poisonous", "毒のある（触れる・食べると危険）", "形容詞", "Some brightly colored frogs are extremely poisonous.", "動物", "600"),
    ("diurnal", "昼行性の", "形容詞", "Unlike owls, most songbirds are diurnal.", "動物", "900"),
    ("molt", "脱皮する・換毛する", "動詞", "Snakes molt their skin several times a year.", "動物", "750"),
    ("burrow", "巣穴を掘る／巣穴", "動詞", "Rabbits burrow deep tunnels to raise their young.", "動物", "600"),
    ("den", "巣穴・ねぐら（キツネなどの）", "名詞", "The fox retreated to its den for the winter.", "動物", "500"),
    ("lair", "隠れ家・ねぐら（猛獣の）", "名詞", "The bear returned to its lair after hunting.", "動物", "650"),
    ("pouch", "（有袋類の）育児嚢・袋", "名詞", "A baby kangaroo stays in its mother's pouch for months.", "動物", "600"),
    ("gestation", "妊娠期間", "名詞", "An elephant's gestation period lasts almost two years.", "動物", "850"),
    ("hatch", "孵化する", "動詞", "The eggs will hatch in about three weeks.", "動物", "500"),
    ("roost", "ねぐらにつく／ねぐら", "動詞", "Hundreds of birds roost in that tree every evening.", "動物", "700"),
    ("pride", "群れ（ライオンの）", "名詞", "A pride of lions rested in the shade.", "動物", "650"),
    ("warm-blooded", "恒温性の", "形容詞", "Mammals and birds are both warm-blooded animals.", "動物", "750"),
    ("cold-blooded", "変温性の", "形容詞", "Reptiles are cold-blooded, so they rely on the sun for warmth.", "動物", "750"),
    ("instinct", "本能", "名詞", "Migration is driven largely by instinct.", "動物", "700"),
    ("territorial", "縄張り意識の強い", "形容詞", "Male birds can become very territorial during breeding season.", "動物", "750"),
    ("food chain", "食物連鎖", "名詞", "Small insects sit near the bottom of the food chain.", "動物", "700"),
    ("apex predator", "頂点捕食者", "名詞", "The great white shark is an apex predator in the ocean.", "動物", "800"),
    ("extinction", "絶滅", "名詞", "Habitat loss is a major cause of extinction.", "動物", "750"),
    ("zoo", "動物園", "名詞", "We saw elephants and giraffes at the zoo.", "動物", "300"),
    ("aviary", "鳥小屋・大型の鳥かご", "名詞", "The zoo's aviary is home to dozens of tropical birds.", "動物", "800"),
    # --- 動物の体の部位 ---
    ("wing", "翼・羽", "名詞", "The bird spread its wings and flew away.", "動物", "300"),
    ("tail", "尻尾", "名詞", "The dog wagged its tail happily.", "動物", "300"),
    ("tusk", "牙（象・セイウチなどの長い牙）", "名詞", "An elephant's tusks continue growing throughout its life.", "動物", "550"),
    ("antler", "枝角（シカの）", "名詞", "Male deer shed their antlers every year.", "動物", "650"),
    ("paw", "（動物の）足・手", "名詞", "The cat lifted its paw to touch the window.", "動物", "400"),
    ("snout", "鼻先・鼻づら", "名詞", "A pig uses its snout to dig in the dirt.", "動物", "650"),
    ("whisker", "ひげ（動物の）", "名詞", "A cat's whiskers help it sense its surroundings.", "動物", "600"),
    ("shell", "殻・甲羅", "名詞", "The turtle pulled its head into its shell.", "動物", "400"),
    ("bird", "鳥", "名詞", "A small bird landed on the windowsill.", "動物", "300"),
    # --- 家畜・幼獣・飼育施設 ---
    ("barn", "納屋・畜舎", "名詞", "The horses spent the night in the barn.", "動物", "400"),
    ("pen", "囲い（家畜用）", "名詞", "The farmer kept the pigs in a small pen.", "動物", "500"),
    ("coop", "鶏小屋", "名詞", "The hens returned to the coop before sunset.", "動物", "600"),
    ("stable", "馬小屋・厩舎", "名詞", "The groom led the horse into the stable.", "動物", "500"),
    ("pasture", "牧草地", "名詞", "The cows grazed peacefully in the pasture.", "動物", "400"),
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
