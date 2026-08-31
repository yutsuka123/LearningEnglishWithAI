# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""猫(cat)・犬(dog)の専門用語集を新設、authored by Claude(2026-08-25・
ユーザー要望「犬と猫の用語集」「たくさん入れたい」「詳細充実+裏取り+照査を」)。

既存の「動物」ドメイン(scripts/add_cat_dog_breeds.py)は犬種・猫種の品種名
(Labrador Retriever等)のみで、解剖・行動・飼育・慣用句は手薄だったため、
既存分類はそのまま(品種名は動物ドメインに残す)にしつつ、新ドメイン
「猫」「犬」を新設して専門語彙を追加する(ユーザー要望「既存はそのまま、
猫もしくは犬分類に入れる」)。フレーズは新シーン「猫・犬にまつわる英語」
として、猫/犬の慣用句(idiom)と飼い主が使う実用フレーズを収録する。

**配慮事項(ユーザー明言)**: 残酷な表現や、猫好き・犬好きが嫌がるような
慣用句(動物への暴力を連想させるもの等、例:"more than one way to skin a
cat")は選定から除外した。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` /
`phrases` tables.

Run:  python scripts/add_cats_dogs.py
仕上げ: 投入後に `python scripts/relevel.py` と
        `python scripts/relevel_phrases.py` で難易度を再設定する。

**2026-08-31追記(方針転換・再実行不可)**: 上記「品種名は動物ドメインに
残す」という当初方針をユーザー指示で転換し、`words`の基本語・品種名
(cat/dog/kitten/puppy/主要犬種13種/主要猫種7種、計37件)を`動物(身近な
動物)`から`猫`/`犬`へ移動、`phrases`の「猫・犬にまつわる英語」(156件)も
`猫にまつわる英語`/`犬にまつわる英語`に分割した(犬猫両方に言及する3件は
両分野に複製)。理由: 犬派/猫派どちらか一方だけの学習者向けに分野を
絞れるようにするため(宣伝面でも猫好き/犬好き層を別々に狙う施策と連動)。
**このスクリプトを再実行すると「猫・犬にまつわる英語」の156件が重複挿入
される**(english列の重複チェックはあるが、シーン名が変わったため通らない
可能性が高い)。再実行しないこと。詳細は`app/services/taxonomy.py`の
該当コメントと本番/ローカルDBの実データを参照。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

CAT = "猫"
DOG = "犬"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 猫: 解剖・身体的特徴 ---
    ("whisker pad", "ひげ袋(猫の上唇にある、ひげの根元が集まった膨らんだ部分)", "名詞", "A cat's whisker pad helps it sense the width of a gap before squeezing through.", CAT, "800"),
    ("toe beans", "肉球(猫の足裏にある豆のような形のパッド、俗語)", "名詞", "She loves gently pressing her cat's toe beans.", CAT, "700"),
    ("paw pad", "肉球(足裏のクッション部分の正式な呼び方)", "名詞", "The paw pad cushions the cat's steps and helps it move silently.", CAT, "700"),
    ("dewclaw", "狼爪(前脚の内側にある、地面に着かない退化した爪)", "名詞", "A cat's dewclaw doesn't touch the ground, so unlike its other claws it never wears down naturally and needs regular trimming.", CAT, "850"),
    ("retractable claws", "引っ込められる爪(猫の爪の特徴、普段は肉球の中に収納される)", "名詞", "A cat's retractable claws stay sharp because they are protected inside the paw when not in use.", CAT, "800"),
    ("flehmen response", "フレーメン反応(上唇をめくって特定のにおいを鋤鼻器で感知する行動)", "名詞", "The cat's flehmen response, with its mouth slightly open, helps it analyze unfamiliar scents.", CAT, "950"),
    ("third eyelid", "瞬膜(目頭側から現れる半透明の膜、眼を保護する)", "名詞", "A visible third eyelid can be a sign that a cat is unwell.", CAT, "850"),
    ("tapetum lucidum", "タペタム(輝板、暗闇で目が光って見える理由となる反射層)", "名詞", "The tapetum lucidum behind a cat's retina is why its eyes seem to glow in the dark.", CAT, "950"),
    ("slit pupil", "縦長の瞳孔(猫の瞳孔の形状)", "名詞", "A cat's slit pupil can narrow to a thin line in bright light.", CAT, "800"),
    ("whisker fatigue", "ひげ疲れ(ひげへの過度な刺激によるストレス、俗に言われる概念)", "名詞", "Some owners switch to a wide, shallow bowl to reduce whisker fatigue.", CAT, "900"),
    ("scruff", "首の後ろのたるんだ皮膚(母猫が子猫をくわえて運ぶ部分)", "名詞", "A mother cat carries her kittens by the scruff of the neck.", CAT, "750"),
    ("tabby", "トラ猫・キジトラ(縞模様の毛色パターンの猫)", "名詞", "The tabby's fur had a distinctive M-shaped marking on its forehead.", CAT, "600"),
    ("mackerel tabby", "サバトラ(魚の骨のような縞模様が特徴のトラ猫のパターン)", "名詞", "A mackerel tabby has narrow, parallel stripes running down its sides.", CAT, "850"),
    ("calico", "三毛猫(白・黒・オレンジの3色が混じった毛色)", "名詞", "Almost all calico cats are female due to how the coat color genes work.", CAT, "700"),
    ("tortoiseshell", "べっ甲猫(黒とオレンジがまだら状に混ざった毛色)", "名詞", "The tortoiseshell's coat mixed black and orange in an irregular pattern.", CAT, "800"),
    # --- 猫: 行動・鳴き声 ---
    ("purr", "ゴロゴロと喉を鳴らす", "動詞", "The cat began to purr as soon as she picked it up.", CAT, "500"),
    ("chirrup", "チャーピングする(短く高い声で鳴く、猫が興味を示す時の鳴き声)", "動詞", "The cat chirruped at the bird outside the window.", CAT, "900"),
    ("trill", "小さく震える声で鳴く(猫が挨拶の時に出す鳴き声)", "動詞", "She trilled softly whenever her owner came home.", CAT, "900"),
    ("bunting (cat behavior)", "頭突き・すりすり(頭や顔をこすりつけてマーキングする行動)", "名詞", "The cat's bunting against her leg was a sign of affection and scent-marking.", CAT, "900"),
    ("kneading", "ふみふみ(前足で交互に押す動作、子猫が母乳を出す動作の名残とされる)", "名詞", "The cat's kneading on the blanket is a comforting, kitten-like behavior.", CAT, "800"),
    ("allogrooming", "相互グルーミング(複数の猫が互いに毛づくろいをすること)", "名詞", "The two cats engaged in allogrooming, a sign of a close bond.", CAT, "950"),
    ("hairball", "毛玉(毛づくろいで飲み込んだ毛が胃の中で固まったもの)", "名詞", "The cat coughed up a hairball on the carpet.", CAT, "600"),
    ("catnip response", "またたび反応(またたびに対する陶酔的な反応)", "名詞", "Not every cat shows a catnip response; the trait is genetically inherited.", CAT, "800"),
    ("feral cat", "野良猫・野生化した猫(人に馴れていない、または元は飼い猫だった野生の猫)", "名詞", "A feral cat is generally more fearful of humans than a stray that was once socialized.", CAT, "750"),
    ("community cat", "地域猫(特定の地域で複数の住民が見守り管理する野良猫)", "名詞", "Volunteers feed and monitor the community cats in the neighborhood.", CAT, "800"),
    ("trap-neuter-return", "TNR(野良猫を捕獲・不妊去勢手術し、元の場所に戻す活動)", "名詞", "The animal shelter runs a trap-neuter-return program to control the feral cat population.", CAT, "900"),
    ("cat nuisance", "猫害(糞尿被害・鳴き声・農作物被害など、猫による近隣トラブルの総称)", "名詞", "The neighborhood association discussed how to reduce cat nuisance complaints from residents.", CAT, "800"),
    ("spraying (cat)", "スプレー行動(縦に立てた尻尾から尿を吹きかけてマーキングする行動)", "名詞", "Spraying is a marking behavior seen more often in unneutered male cats.", CAT, "850"),
    ("crepuscular", "薄明薄暮性の(夜明けと夕暮れに最も活発になる性質、猫の典型的な習性)", "形容詞", "Cats are crepuscular animals, most active around dawn and dusk.", CAT, "900"),
    # --- 猫: 飼育・設備 ---
    ("litter box", "トイレ・猫砂の箱", "名詞", "Cleaning the litter box daily helps prevent litter box aversion.", CAT, "500"),
    ("scratching post", "爪とぎ", "名詞", "A scratching post keeps the cat from clawing the furniture.", CAT, "550"),
    ("cat tree", "キャットタワー", "名詞", "The cat tree gave the cats a place to climb and observe the room.", CAT, "500"),
    ("cat flap", "キャットドア・猫用の出入り口", "名詞", "The cat flap let the cat go outside whenever it wanted.", CAT, "600"),
    ("cattery", "猫舎・キャッテリー(ブリーダーの飼育施設、または猫の一時預かり施設)", "名詞", "The couple boarded their cat at a cattery while they were on vacation.", CAT, "800"),
    ("indoor cat", "室内飼いの猫", "名詞", "Keeping an indoor cat generally results in a longer lifespan than letting it roam outside.", CAT, "600"),
    ("microchipping", "マイクロチップの装着(識別用のICチップを皮下に埋め込むこと)", "名詞", "Microchipping makes it much easier to reunite a lost cat with its owner.", CAT, "700"),
    ("obligate carnivore", "真性肉食動物(動物性タンパク質を必須とする、猫の食性を示す語)", "名詞", "As an obligate carnivore, a cat cannot thrive on a purely plant-based diet.", CAT, "900"),
    ("cat carrier", "キャリーバッグ・猫用の運搬ケース", "名詞", "The cat hissed as she was placed inside the cat carrier.", CAT, "550"),
    ("declawing", "抜爪(単なる爪切除ではなく、爪の生えている指の末節骨ごと切断する外科手術。多くの国で議論・規制がある)", "名詞", "Declawing is banned or restricted in many countries due to animal welfare concerns.", CAT, "900"),
    ("polydactyl cat", "多指症の猫(通常より指の数が多い猫)", "名詞", "A polydactyl cat may have six or seven toes on a single paw.", CAT, "900"),
    ("senior cat", "シニア猫(高齢の猫、一般的に7〜10歳以上)", "名詞", "A senior cat needs more frequent veterinary checkups.", CAT, "600"),
    ("Fel d 1", "Fel d 1(猫アレルギーの主な原因となるアレルゲンタンパク質)", "名詞", "Fel d 1, found in cat saliva and skin, is the main protein behind most cat allergies.", CAT, "950"),
    ("moggy", "雑種猫(英国のくだけた表現、血統書のない猫)", "名詞", "Despite being just a moggy, he was the friendliest cat in the shelter.", CAT, "900"),
    ("domestic shorthair", "ドメスティック・ショートヘア(特定の血統を持たない短毛の猫)", "名詞", "Most cats in shelters are domestic shorthairs rather than purebred cats.", CAT, "700"),
    ("cat show", "キャットショー(猫の品評会)", "名詞", "The Persian took first place at the regional cat show.", CAT, "600"),
    ("chattering (cat)", "チャタリング(獲物を見た時などに歯を小刻みに鳴らす行動)", "名詞", "The cat's chattering at the bird outside the window puzzled her owner.", CAT, "900"),
    ("territorial marking", "縄張りマーキング(においなどで自分の縄張りを示す行動)", "名詞", "Rubbing its cheek on furniture is a form of territorial marking.", CAT, "800"),
    ("vertical territory", "垂直方向の縄張り(高い場所を好む猫特有の空間の使い方)", "名詞", "Providing vertical territory like shelves helps a multi-cat household avoid conflict.", CAT, "900"),
    ("cat behaviorist", "猫の行動専門家(問題行動の相談に応じる専門職)", "名詞", "A cat behaviorist helped the family understand why their cat had started scratching the sofa.", CAT, "850"),
    ("environmental enrichment", "環境エンリッチメント(飼育環境を刺激的で快適なものにする工夫)", "名詞", "Puzzle feeders are a simple form of environmental enrichment for indoor cats.", CAT, "900"),
    ("solitary hunter", "単独ハンター(群れず単独で狩りをする性質、猫の祖先の習性)", "名詞", "Unlike wolves, the cat's wild ancestors were solitary hunters.", CAT, "850"),
    ("self-soothing behavior", "自己鎮静行動(不安を和らげるための猫自身の行動、毛づくろい等)", "名詞", "Excessive grooming can be a self-soothing behavior triggered by stress.", CAT, "900"),
    ("scent marking", "におい付け(頬ずりやスプレー等、においで縄張りや所有物を示す行動)", "名詞", "Cats use scent marking to feel secure in their own territory.", CAT, "800"),
    ("barn cat", "納屋猫(農場などでネズミ駆除のために飼われる半野生の猫)", "名詞", "The barn cat kept the mouse population under control without ever coming inside.", CAT, "800"),
    ("lap cat", "膝の上に乗るのが好きな猫", "名詞", "Some breeds are known for being especially affectionate lap cats.", CAT, "600"),
    ("multi-cat household", "複数の猫を飼う家庭", "名詞", "A multi-cat household needs enough litter boxes to prevent territorial stress.", CAT, "800"),
    ("litter box aversion", "トイレの忌避(猫が特定の理由でトイレを避けるようになる状態)", "名詞", "Litter box aversion often develops after an unpleasant experience, like being startled while using it.", CAT, "900"),
    # --- 犬: 解剖・身体的特徴 ---
    ("hackles", "背筋の逆立った毛(警戒・興奮時に首から背中にかけて逆立つ毛)", "名詞", "The dog's hackles rose the moment a stranger approached the gate.", DOG, "850"),
    ("jowls", "垂れた頬・あご下のたるみ(大型犬などに見られる垂れ下がった皮膚)", "名詞", "The bloodhound's jowls hung low, helping trap scent particles near its nose.", DOG, "800"),
    ("undercoat", "下毛・アンダーコート(表面の毛の下にある柔らかい毛)", "名詞", "Double-coated breeds shed their undercoat heavily twice a year.", DOG, "750"),
    ("double coat", "ダブルコート(下毛と上毛の二層構造の被毛)", "名詞", "A double coat helps some breeds stay warm in cold climates.", DOG, "750"),
    ("dock (tail)", "断尾する(尾の一部を切除すること)", "動詞", "Some working breeds were traditionally docked to prevent tail injuries in the field.", DOG, "900"),
    ("crop (ears)", "断耳する(耳の一部を切除し立たせる処置)", "動詞", "Cropping a dog's ears is illegal in many countries today.", DOG, "900"),
    ("dewclaw (dog)", "狼爪(犬の前脚・後脚にある地面に着かない退化した爪)", "名詞", "The vet recommended trimming the dewclaw regularly since it doesn't wear down naturally.", DOG, "850"),
    ("scent hound", "嗅覚ハウンド(嗅覚を頼りに獲物を追う猟犬のグループ)", "名詞", "Bloodhounds are scent hounds famous for their tracking ability.", DOG, "800"),
    ("sighthound", "視覚ハウンド(視覚と速さを頼りに獲物を追う猟犬のグループ)", "名詞", "Greyhounds are sighthounds bred for chasing fast-moving prey by sight.", DOG, "850"),
    # --- 犬: 行動 ---
    ("play bow", "プレイバウ(前足を伸ばしお尻を上げる、遊びの誘いを示す姿勢)", "名詞", "The puppy gave a play bow before darting off across the yard.", DOG, "850"),
    ("zoomies", "ゾーミーズ(突然走り回る興奮行動、俗語)", "名詞", "After the bath, the dog got a case of the zoomies and sprinted around the living room.", DOG, "800"),
    ("tail wagging", "尻尾を振ること", "名詞", "Tail wagging doesn't always mean a dog is happy; the direction and speed matter.", DOG, "500"),
    ("prey drive", "捕食欲求(動くものを追いかけ捕らえたいという本能的な衝動)", "名詞", "A high prey drive can make some breeds unsuitable to live with small pets.", DOG, "850"),
    ("resource guarding", "リソースガーディング(食べ物やおもちゃなどを守ろうとする行動)", "名詞", "Resource guarding around food bowls is a common issue trainers help owners address.", DOG, "900"),
    ("separation anxiety", "分離不安(飼い主と離れることへの強い不安)", "名詞", "Separation anxiety can cause a dog to bark or destroy furniture when left alone.", DOG, "800"),
    ("leash reactivity", "リードリアクティビティ(散歩中に他の犬や人へ過剰に反応すること)", "名詞", "The trainer worked on the dog's leash reactivity using positive reinforcement.", DOG, "900"),
    ("recall (command)", "呼び戻し(名前を呼んで戻らせるコマンド)", "名詞", "A reliable recall can keep a dog safe when it's off leash.", DOG, "700"),
    ("heel", "脚側について歩く(飼い主のすぐ横について歩くよう指示するコマンド)", "動詞", "She trained her dog to heel calmly even past distractions.", DOG, "750"),
    ("socialization", "社会化(様々な人・動物・環境に慣れさせるトレーニング)", "名詞", "Early socialization helps puppies grow into confident, well-adjusted adults.", DOG, "700"),
    ("clicker training", "クリッカートレーニング(音を鳴らして望ましい行動を強化する訓練法)", "名詞", "Clicker training marks the exact moment the dog does the right behavior.", DOG, "800"),
    ("positive reinforcement", "正の強化(望ましい行動にご褒美を与えて強化する訓練の考え方)", "名詞", "Modern dog training relies heavily on positive reinforcement rather than punishment.", DOG, "800"),
    # --- 犬: 役割・種類 ---
    ("service dog", "介助犬・使役犬(障害のある人を補助する訓練を受けた犬)", "名詞", "A service dog is legally permitted in most public places.", DOG, "700"),
    ("guide dog", "盲導犬", "名詞", "The guide dog led its owner safely across the busy intersection.", DOG, "600"),
    ("therapy dog", "セラピードッグ(病院や施設で人々を癒す訪問活動を行う犬)", "名詞", "The therapy dog visited the hospital ward every Friday afternoon.", DOG, "700"),
    ("herding dog", "牧羊犬・牧畜犬", "名詞", "Herding dogs like Border Collies instinctively try to gather moving groups together.", DOG, "700"),
    ("working dog", "使役犬(牧畜・救助・警備など特定の仕事のために育種された犬)", "名詞", "Working dogs generally need more physical and mental stimulation than companion breeds.", DOG, "700"),
    ("gun dog", "鳥猟犬(狩猟で獲物の回収などを助ける犬)", "名詞", "Retrievers are gun dogs originally bred to bring back shot waterfowl.", DOG, "800"),
    # --- 犬: 飼育・訓練・設備 ---
    ("crate training", "クレートトレーニング(ケージを安心できる居場所として慣れさせる訓練)", "名詞", "Crate training can make house-training a puppy much easier.", DOG, "800"),
    ("house-training", "トイレトレーニング(室内での排泄場所を教えるしつけ)", "名詞", "House-training a puppy usually takes a few weeks of consistent routine.", DOG, "700"),
    ("dog park", "ドッグラン", "名詞", "The dogs ran freely off leash at the dog park.", DOG, "500"),
    ("agility (dog sport)", "アジリティ(障害物コースを走るドッグスポーツ)", "名詞", "The border collie weaved through the poles during the agility competition.", DOG, "700"),
    ("whelping", "出産する(犬が子犬を産むこと)", "動詞", "The breeder stayed up all night while the mother dog was whelping.", DOG, "850"),
    ("litter (puppies)", "一腹の子犬(同時に生まれた子犬のグループ)", "名詞", "The litter of six puppies was ready for adoption at eight weeks old.", DOG, "700"),
    ("microchipping (dog)", "マイクロチップの装着(識別用のICチップを皮下に埋め込むこと)", "名詞", "Microchipping is now required by law for dogs in many countries.", DOG, "700"),
    ("brachycephalic", "短頭種の(鼻先が短く平らな犬種の特徴を示す語)", "形容詞", "Brachycephalic breeds like bulldogs are prone to breathing difficulties.", DOG, "950"),
    ("hip dysplasia", "股関節形成不全(股関節がうまく発達しない遺伝性の疾患)", "名詞", "Hip dysplasia is common in large breeds and can cause lifelong joint pain.", DOG, "900"),
    ("heartworm", "フィラリア(蚊が媒介する寄生虫、心臓や肺の血管に寄生する)", "名詞", "Vets recommend monthly heartworm prevention for dogs year-round.", DOG, "850"),
    ("spay", "避妊手術をする(メスの生殖器を摘出する手術)", "動詞", "The shelter spays every female dog before putting it up for adoption.", DOG, "700"),
    ("neuter", "去勢手術をする(オスの生殖器を摘出する手術)", "動詞", "Neutering a male dog can reduce certain territorial behaviors.", DOG, "700"),
    ("canine good citizen", "キャナイン・グッド・シチズン(米国の犬のマナー認定プログラム)", "名詞", "Passing the canine good citizen test showed the dog could behave calmly in public.", DOG, "900"),
    ("puppy mill", "パピーミル(利益優先で劣悪な環境の下で繁殖を行う悪質な業者)", "名詞", "Animal welfare groups campaign against puppy mills that prioritize profit over the dogs' health.", DOG, "850"),
    ("rescue dog", "保護犬(元は捨てられた・虐待されたなどの経緯で保護された犬)", "名詞", "Their rescue dog was nervous around strangers at first but slowly came out of its shell.", DOG, "600"),
    ("shelter dog", "シェルターにいる犬(保護施設で新しい飼い主を待つ犬)", "名詞", "The family adopted a shelter dog instead of buying a puppy from a breeder.", DOG, "600"),
    ("leash law", "リード着用義務(公共の場で犬をリードにつなぐことを定めた法律)", "名詞", "The city's leash law requires dogs to be on a leash no longer than six feet in public parks.", DOG, "800"),
    ("scent work", "セントワーク(嗅覚を使って隠された匂いを探す犬のスポーツ・訓練)", "名詞", "Scent work gives working breeds a mentally stimulating way to use their nose.", DOG, "850"),
    ("flyball", "フライボール(リレー形式で障害物を越えてボールを取りに行くドッグスポーツ)", "名詞", "The relay team's dogs raced each other in a lively game of flyball.", DOG, "850"),
    ("canine cognition", "犬の認知能力(犬の学習・記憶・問題解決能力に関する研究分野)", "名詞", "Researchers studying canine cognition found dogs can recognize dozens of object names.", DOG, "900"),
    ("dock diving", "ドックダイビング(桟橋から水中のおもちゃを目がけて飛び込む距離を競うドッグスポーツ)", "名詞", "The Labrador launched off the dock in a dock diving competition.", DOG, "850"),
    ("counter-conditioning", "拮抗条件付け(苦手なものへの反応を、良い体験と結びつけて変えていく訓練法)", "名詞", "Counter-conditioning paired the sound of the vacuum with treats to ease the dog's fear.", DOG, "950"),
    ("desensitization", "脱感作(苦手な刺激に少しずつ慣れさせていく訓練法)", "名詞", "Gradual desensitization to car rides reduced the dog's travel anxiety over several weeks.", DOG, "900"),
    ("reactive dog", "反応性の高い犬(特定の刺激に過剰に反応しやすい犬)", "名詞", "A reactive dog may lunge or bark at other dogs out of fear rather than aggression.", DOG, "850"),
    ("breed standard", "犬種標準(その犬種の理想的な体格・性質を定めた基準)", "名詞", "Judges compare each dog against the official breed standard at a conformation show.", DOG, "850"),
    ("conformation show", "コンフォメーションショー(犬種標準への適合度を審査する犬の品評会)", "名詞", "The poodle placed second at the regional conformation show.", DOG, "800"),
    ("obedience trial", "服従訓練競技会(コマンドへの服従度を競う競技会)", "名詞", "Their border collie earned top marks at the obedience trial.", DOG, "800"),
    ("canine cognitive dysfunction", "犬の認知機能不全(高齢犬に見られる、人間の認知症に似た状態)", "名詞", "Canine cognitive dysfunction can cause an older dog to seem confused or disoriented at home.", DOG, "950"),
    ("senior dog", "シニア犬(高齢の犬、一般的に7歳以上)", "名詞", "A senior dog often needs a softer bed to ease pressure on its joints.", DOG, "600"),
]


PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "猫・犬にまつわる英語": [
        # --- 猫の慣用句 ---
        ("Curiosity killed the cat, but satisfaction brought it back.", "好奇心は猫をも殺す、しかし満足感がそれを生き返らせた(過度の詮索を戒めつつ、それでも知る価値はあるという言い回し)。"),
        ("She let the cat out of the bag before the surprise party started.", "彼女はサプライズパーティーが始まる前にうっかり秘密を漏らしてしまった。"),
        ("When the cat's away, the mice will play.", "鬼の居ぬ間に洗濯(上司や監視役がいない間に羽を伸ばすことのたとえ)。"),
        ("Look what the cat dragged in!", "何とまあ、ひどい格好で来たものだ(冗談っぽく相手をからかう表現)。"),
        ("Cat got your tongue?", "どうしたの、黙り込んじゃって(何も言わない相手をからかう表現)。"),
        ("It's raining cats and dogs outside.", "外はどしゃ降りだ。"),
        ("They say a cat has nine lives.", "猫には九つの命があると言われている。"),
        ("He was as nervous as a cat on a hot tin roof before the interview.", "彼は面接前、まるで熱いトタン屋根の上の猫のようにそわそわしていた。"),
        ("She looked like the cat that got the cream after winning the award.", "彼女は受賞後、まるでクリームにありついた猫のようにご満悦の様子だった。"),
        ("The two rivals have been playing cat and mouse for weeks.", "その2人のライバルは何週間も駆け引きを続けている。"),
        ("Getting the whole team to agree is like herding cats.", "チーム全員の合意を得るのは、まるで猫の群れを誘導するように至難の業だ。"),
        ("A cat may look at a king, after all.", "所詮、身分の低い者にも相手を見る権利くらいはあるものだ。"),
        ("The little boy is such a copycat of his older brother.", "その男の子はお兄ちゃんの真似ばかりする。"),
        ("With his sunglasses and leather jacket, he looked like a real cool cat.", "サングラスと革ジャン姿の彼はまさにイケてる男という感じだった。"),
        ("The fat cats on Wall Street rarely feel the effects of a recession.", "ウォール街の大金持ちたちは不況の影響をほとんど感じない。"),
        ("I need a quick cat nap before the meeting.", "会議の前にちょっと仮眠を取りたい。"),
        ("He grinned like a Cheshire cat when he heard the good news.", "彼は良い知らせを聞いてにんまりと満面の笑みを浮かべた。"),
        ("The cat burglar slipped in and out without triggering a single alarm.", "その怪盗はアラームを一つも作動させることなく忍び込み、また抜け出した。"),
        # --- 犬の慣用句 ---
        ("Don't worry, every dog has its day.", "心配しないで、誰にでもいつか良い日が来るものだ。"),
        ("It's better to let sleeping dogs lie.", "寝た子を起こすようなことはしない方がいい。"),
        ("You're barking up the wrong tree if you think I did it.", "私がやったと思っているなら、それは見当違いだよ。"),
        ("Working two jobs to pay the bills is a dog's life.", "生活費のために掛け持ちで働くのは骨の折れる暮らしだ。"),
        ("The competition in this industry is pure dog eat dog.", "この業界の競争はまさに弱肉強食だ。"),
        ("He's been in the doghouse ever since he forgot her birthday.", "彼は彼女の誕生日を忘れて以来、ずっと不興を買っている。"),
        ("You can't teach an old dog new tricks, or so they say.", "年寄りに新しいことを教えるのは難しいとよく言われる。"),
        ("I felt sick as a dog after eating that leftover sushi.", "残り物の寿司を食べたらひどく気分が悪くなった。"),
        ("The old neighborhood has really gone to the dogs.", "その昔ながらの地域は本当に荒れ果ててしまった。"),
        ("After the long shift, she was completely dog tired.", "長い勤務の後、彼女はへとへとに疲れ切っていた。"),
        ("Their company has become the top dog in the smartphone market.", "彼らの会社はスマートフォン市場のトップ企業になった。"),
        ("He joked that a little hair of the dog would cure his hangover.", "彼は迎え酒で二日酔いが治るだろうと冗談を言った。"),
        ("It was a three dog night, so they piled on extra blankets.", "凍えるほど寒い夜だったので、彼らは毛布を何枚も重ねた。"),
        ("Once he starts a project, he's like a dog with a bone.", "彼はプロジェクトを始めると、まるで骨をくわえた犬のように離さない。"),
        ("She's been working like a dog all week to finish the report.", "彼女は報告書を仕上げるため、その週ずっと必死に働いていた。"),
        ("In that marriage, it sometimes feels like the tail is wagging the dog.", "あの夫婦関係は時々、主従が逆転しているように見える。"),
        ("The dog days of summer make everyone in the office sluggish.", "真夏の蒸し暑い時期はオフィスの誰もがだるそうにしている。"),
        ("Just throw him a bone and let him feel useful.", "彼に少し役目を与えて、役に立っていると感じさせてあげなよ。"),
        ("Don't worry about the boss, his bark is worse than his bite.", "上司のことは心配しなくていい、口は悪いが実際は優しい人だから。"),
        # --- 猫の日常・行動フレーズ ---
        ("My cat always kneads the blanket before falling asleep.", "うちの猫はいつも眠る前に毛布をふみふみする。"),
        ("She rubbed her cat's whisker pad and it started to purr.", "彼女が猫のひげ袋をなでると、猫はゴロゴロと鳴き始めた。"),
        ("The cat flattened its ears and hissed at the vacuum cleaner.", "猫は耳を後ろに倒して掃除機に向かって威嚇の声を上げた。"),
        ("He gently pressed his cat's toe beans and laughed at how soft they were.", "彼は猫の肉球をそっと押して、その柔らかさに笑った。"),
        ("The kitten pounced on the toy the moment it moved.", "その子猫はおもちゃが動いた瞬間に飛びかかった。"),
        ("My cat headbutts my hand whenever she wants attention.", "うちの猫はかまってほしい時、いつも私の手に頭突きしてくる。"),
        ("The cat coughed up a hairball right in the middle of the hallway.", "猫は廊下のど真ん中で毛玉を吐き戻した。"),
        ("She noticed her cat's third eyelid showing and took it to the vet.", "彼女は猫の瞬膜が見えているのに気づき、動物病院に連れて行った。"),
        ("The tabby stretched out in a warm patch of sunlight on the floor.", "そのトラ猫は床の暖かい日だまりで体を伸ばして寝そべった。"),
        ("Cats often knead soft surfaces, a habit left over from kittenhood.", "猫は柔らかい面をふみふみすることが多く、これは子猫時代からの習性の名残である。"),
        ("Two cats in the house were allogrooming on the windowsill.", "家の中の2匹の猫は窓辺で互いに毛づくろいをしていた。"),
        ("The stray cat has become a regular community cat in the alley.", "その野良猫は路地の常連の地域猫になった。"),
        ("Volunteers organized a trap-neuter-return event for the local feral cats.", "ボランティアたちは地域の野良猫のためにTNRイベントを開催した。"),
        ("Neighbors complained about cat nuisance after cats kept using their garden as a litter box.", "猫が庭をトイレ代わりにし続けるため、近隣住民から猫害についての苦情が寄せられた。"),
        ("An unneutered male cat is far more likely to start spraying indoors.", "去勢していないオス猫は室内でスプレー行動を始める可能性がずっと高い。"),
        ("The cat crouched low, twitching its tail before it pounced on the toy mouse.", "猫は尻尾を小さく震わせながら低く身をかがめ、おもちゃのネズミに飛びかかった。"),
        ("She scratched behind the cat's ears until it started to purr loudly.", "彼女が猫の耳の後ろをかいてやると、猫は大きな声でゴロゴロと鳴き始めた。"),
        ("The vet checked the cat's slit pupils with a small flashlight.", "獣医は小さな懐中電灯で猫の縦長の瞳孔を確認した。"),
        ("Because cats are crepuscular, ours gets most active around dinnertime and dawn.", "猫は薄明薄暮性なので、うちの猫は夕食どきと明け方に一番活発になる。"),
        ("The senior cat now needs a ramp to reach her favorite windowsill.", "そのシニア猫はお気に入りの窓辺に上るのに今ではスロープが必要だ。"),
        ("A polydactyl cat's extra toes give its paws a distinctly wide look.", "多指症の猫は指が多いため、足がひときわ大きく見える。"),
        ("The breeder brought three domestic shorthairs to the cat show.", "そのブリーダーはキャットショーに3匹のドメスティック・ショートヘアを連れてきた。"),
        # --- 犬の日常・行動フレーズ ---
        ("The puppy gave a playful play bow before chasing the ball.", "その子犬はボールを追いかける前に遊びの誘いのポーズを取った。"),
        ("Our dog got a sudden case of the zoomies after his bath.", "うちの犬はお風呂の後、突然ゾーミーズが始まった。"),
        ("His tail wagging slowed down as soon as the vet walked in.", "獣医が入ってきた途端、彼の尻尾を振るスピードが落ちた。"),
        ("The dog's hackles rose when the delivery truck pulled into the driveway.", "配達トラックが私道に入ってきた時、犬の背中の毛が逆立った。"),
        ("He trained his dog to heel calmly even when other dogs passed by.", "彼は他の犬とすれ違っても落ち着いて脚側について歩くよう犬を訓練した。"),
        ("The border collie's herding instinct kicked in around the sheep.", "そのボーダー・コリーは羊を前にすると牧畜本能が働き始めた。"),
        ("Positive reinforcement worked much better than scolding for house-training.", "トイレトレーニングでは叱ることより正の強化の方がずっと効果的だった。"),
        ("The trainer used a clicker to mark the exact moment the dog sat.", "トレーナーは犬が座った瞬間を示すためにクリッカーを使った。"),
        ("Their dog developed separation anxiety after they moved to a new house.", "彼らの犬は引っ越し後、分離不安を発症した。"),
        ("The rescue dog was fearful of men at first, likely due to a rough past.", "その保護犬は、おそらく過去のつらい経験から、最初は男性を怖がっていた。"),
        ("A reliable recall command can save a dog's life near traffic.", "確実な呼び戻しのコマンドは、交通量の多い場所で犬の命を救うことがある。"),
        ("The vet said the dog's resource guarding around his food bowl was mild.", "獣医は犬の餌皿をめぐるリソースガーディングは軽度だと言った。"),
        ("Puppies need plenty of socialization with other dogs and people early on.", "子犬は早い時期に他の犬や人との十分な社会化が必要だ。"),
        ("Crate training helped the puppy feel safe during thunderstorms.", "クレートトレーニングのおかげで、子犬は雷雨の間も安心して過ごせるようになった。"),
        ("The guide dog waited patiently at the curb until it was safe to cross.", "その盲導犬は渡っても安全になるまで、辛抱強く縁石で待っていた。"),
        ("A therapy dog visited the children's ward every Friday afternoon.", "セラピードッグは毎週金曜日の午後に小児病棟を訪れた。"),
        ("The dog park was full of dogs off leash, running and playing together.", "ドッグランは犬たちがリードを外して一緒に走り回って遊んでいっぱいだった。"),
        ("His leash reactivity improved dramatically after months of gradual training.", "何か月もの段階的なトレーニングの末、彼のリードリアクティビティは劇的に改善した。"),
        ("The sighthound easily outran every other dog at the park.", "その視覚ハウンドは公園にいる他のどの犬よりも簡単に速く走った。"),
        ("She signed her dog up for a scent work class to keep him mentally busy.", "彼女は犬の頭を使わせるため、セントワークの教室に登録した。"),
        ("The breeder made sure every puppy in the litter was checked by a vet.", "そのブリーダーは一腹の子犬全員が獣医の検査を受けるようにした。"),
        ("Watching the dogs race in flyball was the highlight of the afternoon.", "フライボールで犬たちが競争する姿を見るのがその午後の一番の見どころだった。"),
        # --- 獣医・健康管理 ---
        ("The vet recommended year-round heartworm prevention for the dog.", "獣医は犬に対し1年を通したフィラリア予防を勧めた。"),
        ("Hip dysplasia is more common in large-breed dogs than small ones.", "股関節形成不全は小型犬より大型犬でより一般的である。"),
        ("Brachycephalic breeds often struggle to breathe in hot weather.", "短頭種は暑い天候の中で呼吸に苦労することが多い。"),
        ("The clinic offers a discount for spaying or neutering rescue animals.", "そのクリニックは保護動物の避妊・去勢手術に割引を提供している。"),
        ("She scheduled her cat for a dental cleaning at the vet.", "彼女は猫の歯のクリーニングを動物病院で予約した。"),
        ("Fel d 1 in the cat's saliva was likely triggering his allergies.", "猫の唾液に含まれるFel d 1が彼のアレルギーの原因になっていた可能性が高い。"),
        ("Regular flea and tick prevention is important for both cats and dogs.", "定期的なノミ・ダニ予防は猫にも犬にも重要である。"),
        ("The kitten's vaccination schedule started at eight weeks old.", "その子猫のワクチン接種は生後8週から始まった。"),
        ("Microchipping made it possible to reunite the lost dog with its family within hours.", "マイクロチップのおかげで、迷子になった犬は数時間で家族のもとへ戻ることができた。"),
        ("The vet said the dog's kennel cough would clear up within two weeks.", "獣医はその犬のケンネルコフは2週間ほどで治まるだろうと言った。"),
        ("Obesity in indoor cats is often linked to overfeeding and inactivity.", "室内飼いの猫の肥満は、餌の与えすぎと運動不足に関係していることが多い。"),
        ("The vet gently examined the cat's third eyelid during the checkup.", "獣医は健診中、猫の瞬膜を優しく確認した。"),
        ("Declawing is now banned in several countries on animal welfare grounds.", "抜爪は動物福祉の観点から現在いくつかの国で禁止されている。"),
        ("A balanced diet is essential since cats are obligate carnivores.", "猫は真性肉食動物であるため、バランスの取れた食事が不可欠である。"),
        ("The vet clipped the dog's overgrown dewclaw during the visit.", "獣医は診察の際、犬の伸びすぎた狼爪を切った。"),
        ("Owners are advised to brush a double-coated breed several times a week.", "ダブルコートの犬種は週に数回ブラッシングすることが飼い主に推奨されている。"),
        ("Whisker fatigue is a debated theory some owners cite for why their cats prefer wide, shallow bowls.", "ひげ疲れは、猫が浅く広い器を好む理由として一部の飼い主が挙げる、賛否のある説である。"),
        ("Cropping and docking are now restricted or banned in much of Europe.", "断耳と断尾は現在、ヨーロッパの多くの地域で規制または禁止されている。"),
        ("Cat allergies are triggered less by fur itself than by proteins like Fel d 1.", "猫アレルギーは毛そのものより、Fel d 1のようなタンパク質によって引き起こされることが多い。"),
        # --- 保護・里親 ---
        ("They decided to adopt a shelter dog instead of buying a puppy.", "彼らは子犬を買う代わりに、シェルターの犬を引き取ることにした。"),
        ("The rescue organization requires a home visit before approving any adoption.", "その保護団体は、里親を承認する前に自宅訪問を必須としている。"),
        ("Fostering a litter of kittens for a few weeks is a rewarding experience.", "数週間、子猫の一腹を里親として預かることは、やりがいのある経験だ。"),
        ("She paid a modest adoption fee that covered the cat's vaccinations.", "彼女は猫のワクチン代を含む、それほど高くない譲渡費用を支払った。"),
        ("Animal welfare groups warn potential buyers about the dangers of puppy mills.", "動物福祉団体は購入検討者にパピーミルの危険性について警告している。"),
        ("The shelter was overcrowded with feral cats brought in from the neighborhood.", "そのシェルターは近隣から連れてこられた野良猫であふれかえっていた。"),
        ("Volunteers at the cattery help kittens get used to human contact.", "キャッテリーのボランティアは子猫が人との触れ合いに慣れるのを手伝う。"),
        ("A responsible breeder will always let you meet the puppy's parents.", "責任あるブリーダーは常に子犬の両親に会わせてくれるものだ。"),
        ("The community cat program keeps track of which cats have been neutered.", "地域猫プログラムは、どの猫が不妊去勢手術を受けたかを記録している。"),
        ("Adopting an older, senior cat can be just as rewarding as adopting a kitten.", "高齢のシニア猫を引き取ることも、子猫を引き取るのと同じくらいやりがいがある。"),
        ("The rescue dog took a few months to trust its new family completely.", "その保護犬が新しい家族を完全に信頼するまでには数か月かかった。"),
        ("Local leash laws require dogs to be under control at all times in the park.", "地域のリード着用義務により、公園内では犬を常に制御下に置くことが求められている。"),
        # --- しつけ・トレーニング ---
        ("Clicker training helped the puppy learn commands surprisingly quickly.", "クリッカートレーニングのおかげで、その子犬は驚くほど早くコマンドを覚えた。"),
        ("The trainer used positive reinforcement instead of punishment.", "そのトレーナーは罰ではなく正の強化を用いた。"),
        ("Consistent house-training routines make accidents much less frequent.", "一貫したトイレトレーニングの習慣は、失敗をずっと少なくする。"),
        ("A dog with strong prey drive may need extra training around small animals.", "捕食欲求の強い犬は、小動物のそばでは追加のトレーニングが必要な場合がある。"),
        ("Crate training should always feel like a safe space, never a punishment.", "クレートトレーニングは常に安心できる場所として感じられるべきで、決して罰であってはならない。"),
        ("She practiced loose-leash walking every day on their evening walk.", "彼女は毎晩の散歩で、リードを引っ張らずに歩く練習を毎日行った。"),
        ("Getting a Canine Good Citizen certification is a popular training goal.", "キャナイン・グッド・シチズンの認定を取得することは人気のあるトレーニング目標だ。"),
        ("Agility training builds both the dog's confidence and physical fitness.", "アジリティのトレーニングは犬の自信と体力の両方を養う。"),
        # --- 追加: 猫・犬にまつわるさらなる表現 ---
        ("A cat behaviorist suggested adding more scratching posts around the house.", "猫の行動専門家は家中に爪とぎをもっと増やすよう提案した。"),
        ("Puzzle feeders are a simple form of environmental enrichment for a bored indoor cat.", "パズルフィーダーは、退屈している室内飼いの猫にとって手軽な環境エンリッチメントの一つだ。"),
        ("As solitary hunters by nature, cats often prefer eating alone.", "生まれつき単独ハンターである猫は、一人で食事をすることを好むことが多い。"),
        ("Excessive licking can sometimes be a self-soothing behavior linked to anxiety.", "過度な毛づくろいは、不安に関連した自己鎮静行動である場合がある。"),
        ("Rubbing against furniture is just scent marking, not a sign of trouble.", "家具にすりすりするのは単なるにおい付けであって、問題行動ではない。"),
        ("The old barn cat kept mice away without ever setting paw indoors.", "その年老いた納屋猫は、一度も室内に足を踏み入れることなくネズミを寄せ付けなかった。"),
        ("Their Ragdoll turned out to be a real lap cat, happiest curled up on her owner.", "彼らのラグドールは本当に膝の上が大好きな猫で、飼い主に丸まっているのが一番幸せそうだった。"),
        ("In a multi-cat household, experts recommend one litter box per cat, plus one extra.", "複数の猫を飼う家庭では、猫の数プラス1個のトイレを用意することが専門家に推奨されている。"),
        ("Switching litter brands too often can sometimes cause litter box aversion.", "猫砂の銘柄を頻繁に変えると、トイレの忌避を引き起こすことがある。"),
        ("Researchers studying canine cognition were surprised by how many words some dogs could learn.", "犬の認知能力を研究する研究者たちは、犬が覚えられる単語の多さに驚いた。"),
        ("Their Labrador competed in a dock diving event for the first time this summer.", "彼らのラブラドールはこの夏、初めてドックダイビングの大会に出場した。"),
        ("Counter-conditioning slowly changed the dog's fear of the vacuum into eager anticipation of a treat.", "拮抗条件付けは、犬の掃除機への恐怖心を少しずつ、おやつを心待ちにする気持ちへと変えていった。"),
        ("The trainer used gradual desensitization to help the dog cope with fireworks.", "トレーナーは花火に対処できるよう、段階的な脱感作を用いた。"),
        ("A reactive dog isn't necessarily aggressive; it may simply be overwhelmed.", "反応性の高い犬が必ずしも攻撃的とは限らず、単に刺激に圧倒されているだけのこともある。"),
        ("The breeder explained how the puppy compared to the official breed standard.", "そのブリーダーは子犬が公式の犬種標準にどう当てはまるか説明した。"),
        ("She spent months preparing her dog for its first conformation show.", "彼女は愛犬の初めてのコンフォメーションショーに向けて何か月も準備した。"),
        ("Their dog earned a perfect score at the obedience trial.", "彼らの犬は服従訓練競技会で満点を獲得した。"),
        ("The vet explained that canine cognitive dysfunction can make an old dog pace at night.", "獣医は、犬の認知機能不全が高齢犬を夜に徘徊させる原因になり得ると説明した。"),
        ("Their senior dog now takes shorter, gentler walks than he used to.", "彼らのシニア犬は、以前よりも短く緩やかな散歩をするようになった。"),
        ("The kitten batted at the string dangling from the toy.", "その子猫はおもちゃからぶら下がる紐にじゃれついた。"),
        ("Cats often sleep up to sixteen hours a day.", "猫は一日に最大16時間も眠ることがある。"),
        ("She adopted two kittens so they could keep each other company.", "彼女は互いに寂しくないよう2匹の子猫を引き取った。"),
        ("The vet trimmed the cat's claws before the checkup ended.", "獣医は健診の終わりに猫の爪を切った。"),
        ("A well-socialized puppy tends to be calmer around strangers as an adult.", "しっかり社会化された子犬は、成犬になっても見知らぬ人に対して落ち着いていることが多い。"),
        ("The two dogs sniffed each other cautiously before starting to play.", "その2匹の犬は遊び始める前に、慎重に互いのにおいを嗅ぎ合った。"),
        ("His dog's recall was so reliable that he let it off leash at the beach.", "彼の犬の呼び戻しはとても確実だったので、彼はビーチでリードを外して遊ばせた。"),
        ("She keeps healthy treats on hand for quick training sessions.", "彼女は手早いトレーニングのため、健康的なおやつを常に手元に置いている。"),
        ("The cat's ears swiveled toward the sound of the can opener.", "猫の耳は缶切りの音の方へくるりと向いた。"),
        ("A short walk before bedtime helped settle the puppy for the night.", "就寝前の短い散歩は、その子犬を夜に落ち着かせるのに役立った。"),
        ("Their dog greeted every visitor with an enthusiastic tail wag.", "彼らの犬はどの来客にも尻尾を勢いよく振って挨拶した。"),
        ("The cat curled up in a tight ball to conserve warmth on the cold night.", "その寒い夜、猫は暖を取るためにきつく丸くなって眠った。"),
        ("She keeps a spare leash by the front door in case of emergencies.", "彼女は万が一に備えて、玄関にリードの予備を置いている。"),
        ("The vet reminded them that dental care matters for cats just as much as for dogs.", "獣医は、歯のケアは犬同様に猫にとっても重要だと彼らに念を押した。"),
        ("Their new kitten spent the first day hiding under the couch.", "彼らの新しい子猫は最初の一日、ソファの下に隠れて過ごした。"),
        ("A tired dog after a long walk is usually a well-behaved dog at home.", "長い散歩の後で疲れた犬は、たいてい家では行儀よく過ごすものだ。"),
    ]
}


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

        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        ph_added = ph_skipped = 0
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in ph_existing:
                    ph_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                ph_existing.add(en.lower())
                ph_added += 1

    print(f"words:   +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    with db() as conn:
        print("totals -> words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
              "phrases:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
