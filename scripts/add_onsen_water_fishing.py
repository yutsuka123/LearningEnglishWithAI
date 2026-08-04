# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated words & phrases for HOT SPRINGS / ONSEN CULTURE,
CANYONING (沢登り), SWIMMING TECHNIQUE, and FISHING, authored by Claude.

Focus (手薄なアウトドア/水系トピックの補強):
  1. 温泉文化 — 海外の温泉利用者に日本の入浴マナーを英語で説明できる語彙
     （天然温泉、共同浴場、かけ湯、水着不可という文化的事実、タトゥーに関する
     規則、貸切風呂、露天風呂/rotenburoの概念、鉱泉、療養入浴、温泉町、
     サウナ、水風呂 など）。
  2. 沢登り・渓流 — 日本で人気のアウトドア活動「沢登り」を英語で説明する語彙
     （ウェットスーツ、ヘルメット、懸垂下降、渡渉、岩場のよじ登り、滝つぼ、
     峡谷、防水装備、増水・鉄砲水の警報 など）。
  3. 水泳 — 基礎を超えたプール・技術系語彙（自由形、背泳ぎ、平泳ぎ、
     バタフライ、フリップターン、コース、オープンウォータースイミング、
     離岸流など安全に関わる語彙も含む）。
  4. 釣り — 淡水/海水を問わない一般的な釣り語彙（竿、リール、餌、ルアー、
     釣り針、キャッチアンドリリース、フライフィッシング、沖釣り、
     釣り許可証、トローリング、氷上釣り など）。

既存の「アウトドア・レジャー」ドメインには beach umbrella / swimsuit /
snorkeling / lifeguard 等が既に存在するため、それらとの重複は避けた。
既存語彙との衝突（hook / lure / tackle / bass / salmon / lane / spa /
current / flood / butterfly / tide / sulfur / geothermal 等）も事前に
確認し、複合語や別表現で回避している。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_onsen_water_fishing.py
      python scripts/add_onsen_water_fishing.py --missing-words   # report only

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- phrases: scene -> [(english, japanese)] --------------------------------

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "温泉文化": [
        ("Do I need to wash before entering the bath?", "浴槽に入る前に体を洗う必要がありますか？"),
        ("Are swimsuits allowed in this hot spring?", "この温泉では水着の着用は許可されていますか？"),
        ("Is this a mixed bathing area?", "ここは男女混浴のエリアですか？"),
        ("Are tattoos allowed here?", "ここはタトゥーがあっても入浴できますか？"),
        ("Is there a private bath we can reserve?", "予約できる貸切風呂はありますか？"),
        ("How long should I soak before taking a break?", "休憩を挟む前にどのくらい浸かればいいですか？"),
        ("Is the water natural or heated artificially?", "このお湯は天然のものですか、それとも人工的に温めていますか？"),
        ("What's the water temperature here?", "ここのお湯の温度はどのくらいですか？"),
        ("Can I bring a towel into the bath?", "タオルを湯船に持ち込んでもいいですか？"),
        ("Is there an outdoor bath with a view?", "景色の見える露天風呂はありますか？"),
        ("Where can I rinse off before entering?", "入る前にどこで体を洗い流せますか？"),
        ("Is it okay to take photos here?", "ここで写真を撮っても大丈夫ですか？"),
        ("How do first-timers usually behave at an onsen?", "温泉初心者は普通どう振る舞えばいいですか？"),
        ("Is there a time limit for the private bath?", "貸切風呂には時間制限がありますか？"),
        ("Do you offer a footbath for day visitors?", "日帰り客向けの足湯はありますか？"),
        ("What should I do with my hair while bathing?", "入浴中、髪はどうすればいいですか？"),
        ("Is tying up long hair required?", "長い髪は結ぶ必要がありますか？"),
        ("Can children use the communal bath?", "子供は共同浴場を使えますか？"),
    ],
    "沢登り・渓流": [
        ("Do we need a guide for this canyon?", "この渓谷にはガイドが必要ですか？"),
        ("Is the water level safe today?", "今日の水位は安全なレベルですか？"),
        ("How cold is the water going to be?", "水温はどのくらい冷たくなりますか？"),
        ("Do I need my own wetsuit and helmet?", "自分のウェットスーツとヘルメットが必要ですか？"),
        ("Is there a flash flood risk in this area?", "このエリアには鉄砲水のリスクがありますか？"),
        ("How many waterfalls will we rappel down?", "いくつの滝を懸垂下降しますか？"),
        ("Is the trail suitable for beginners?", "このコースは初心者向けですか？"),
        ("What should I do if I lose my footing?", "足を滑らせたらどうすればいいですか？"),
        ("Is the river crossing dangerous after rain?", "雨の後、渡渉は危険ですか？"),
        ("How deep is the plunge pool?", "滝つぼの深さはどれくらいですか？"),
        ("What gear should I bring for canyoning?", "キャニオニングにはどんな装備を持っていけばいいですか？"),
        ("Is cell phone reception available in the gorge?", "峡谷内で携帯の電波は届きますか？"),
        ("How experienced do I need to be for this route?", "このルートにはどのくらいの経験が必要ですか？"),
        ("What's the flow rate like after heavy rain?", "大雨の後の流量はどんな感じですか？"),
        ("Is it safe to jump into the pool from here?", "ここからプールに飛び込んでも安全ですか？"),
    ],
    "水泳": [
        ("Is this water safe to swim in?", "この水は泳いでも安全ですか？"),
        ("Are there any rip currents today?", "今日は離岸流はありますか？"),
        ("Which lane should beginners use?", "初心者はどのコースを使えばいいですか？"),
        ("How many laps is a mile?", "1マイルは何往復ですか？"),
        ("Is there a lifeguard on duty?", "ライフガードは今いますか？"),
        ("Do I need a wetsuit for open water swimming?", "オープンウォータースイミングにはウェットスーツが必要ですか？"),
        ("What should I do if I get caught in a rip current?", "離岸流に巻き込まれたらどうすればいいですか？"),
        ("Can you teach me the flip turn?", "フリップターンを教えてもらえますか？"),
        ("Is the deep end marked clearly?", "深い側ははっきり印がついていますか？"),
        ("How do I improve my freestyle technique?", "自由形のテクニックを上達させるにはどうすればいいですか？"),
        ("Is it okay to swim here without a lifeguard?", "ライフガードなしでここで泳いでも大丈夫ですか？"),
        ("What's the water temperature in the pool?", "プールの水温はどのくらいですか？"),
        ("Do you rent swim caps and goggles?", "スイムキャップとゴーグルはレンタルできますか？"),
        ("How far offshore is it still safe to swim?", "沖のどのあたりまでなら泳いでも安全ですか？"),
        ("Which stroke burns the most calories?", "どの泳法が一番カロリーを消費しますか？"),
    ],
    "釣り": [
        ("What's biting today?", "今日は何が釣れていますか？"),
        ("Do I need a fishing license here?", "ここで釣りをするには釣り許可証が必要ですか？"),
        ("What kind of bait works best in this lake?", "この湖ではどんな餌が一番効きますか？"),
        ("Can we practice catch and release here?", "ここではキャッチアンドリリースはできますか？"),
        ("How deep should I cast my line?", "どのくらいの深さに糸を投げればいいですか？"),
        ("Is there a size limit on fish we can keep?", "持ち帰れる魚にはサイズ制限がありますか？"),
        ("What time of day do fish bite the most?", "一日のうちで一番魚が食いつく時間帯はいつですか？"),
        ("Do you rent fishing rods and tackle?", "釣り竿と道具はレンタルできますか？"),
        ("Is fly fishing allowed in this river?", "この川ではフライフィッシングは許可されていますか？"),
        ("How far offshore do we need to go for deep sea fishing?", "沖釣りをするにはどのくらい沖に出る必要がありますか？"),
        ("What kind of fish are in season right now?", "今、旬の魚は何ですか？"),
        ("Can beginners join the fishing charter?", "初心者でも釣り船チャーターに参加できますか？"),
        ("Should I use a bigger hook for larger fish?", "大きい魚には大きいフックを使うべきですか？"),
        ("Is ice fishing possible on this lake in winter?", "冬にこの湖で氷上釣りはできますか？"),
        ("How do I know when I've got a bite?", "食いついたときはどうやってわかりますか？"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 温泉文化 (domain: 旅行) ---
    ("hot spring", "温泉", "名詞", "We soaked in a hot spring after hiking all day.", "旅行", "300"),
    ("natural hot spring", "天然温泉", "名詞", "This natural hot spring has been used for centuries.", "旅行", "400"),
    ("bathhouse", "銭湯・浴場", "名詞", "The public bathhouse opens at six in the morning.", "旅行", "500"),
    ("communal bath", "共同浴場", "名詞", "Guests share a communal bath at the inn.", "旅行", "600"),
    ("bathing etiquette", "入浴マナー", "名詞", "Learning the bathing etiquette helps you avoid awkward mistakes.", "旅行", "700"),
    ("rinse off", "体を洗い流す", "動詞", "You must rinse off before entering the bath.", "旅行", "500"),
    ("wash area", "洗い場", "名詞", "Sit on the stool in the wash area before you soak.", "旅行", "600"),
    ("modesty towel", "体を隠すための小さいタオル", "名詞", "Many bathers carry a small modesty towel.", "旅行", "850"),
    ("private bath", "貸切風呂・専用浴場", "名詞", "We booked a private bath for just the two of us.", "旅行", "600"),
    ("family bath", "家族風呂", "名詞", "The family bath lets parents bathe with young children.", "旅行", "600"),
    ("outdoor bath", "露天風呂", "名詞", "The outdoor bath overlooks the mountains.", "旅行", "600"),
    ("rotenburo", "露天風呂（日本式の呼称）", "名詞", "The inn is famous for its rotenburo with a forest view.", "旅行", "900"),
    ("mineral spring", "鉱泉", "名詞", "The mineral spring is said to ease muscle pain.", "旅行", "700"),
    ("therapeutic bathing", "療養目的の入浴", "名詞", "Therapeutic bathing has a long history in this region.", "旅行", "850"),
    ("spa town", "温泉町", "名詞", "The spa town draws visitors from across the country.", "旅行", "800"),
    ("hot spring resort", "温泉旅館・温泉リゾート", "名詞", "We stayed at a hot spring resort for the weekend.", "旅行", "600"),
    ("steam room", "スチームサウナ・蒸し風呂", "名詞", "The steam room is right next to the sauna.", "旅行", "600"),
    ("sauna", "サウナ", "名詞", "He alternates between the sauna and a cold plunge.", "旅行", "500"),
    ("cold plunge", "水風呂", "名詞", "A cold plunge after the sauna is invigorating.", "旅行", "800"),
    ("footbath", "足湯", "名詞", "Tourists relax their feet in the free footbath.", "旅行", "600"),
    ("soak", "浸かる・つかる", "動詞", "Take time to soak in the warm water.", "旅行", "500"),
    ("ryokan", "旅館（温泉付きの和風旅館）", "名詞", "The ryokan has its own private hot spring.", "旅行", "700"),
    ("yukata", "浴衣（湯上りに着る着物）", "名詞", "Guests wear a yukata after bathing.", "旅行", "700"),
    ("tattoo policy", "タトゥーに関する規則", "名詞", "Some facilities have a strict tattoo policy.", "旅行", "850"),
    ("mixed bathing", "男女混浴", "名詞", "Mixed bathing was once common but is now rare.", "旅行", "900"),
    ("hydrotherapy", "水療法", "名詞", "Hydrotherapy is used to relieve joint pain.", "旅行", "850"),
    ("wellness retreat", "保養・癒しの滞在施設", "名詞", "The resort markets itself as a wellness retreat.", "旅行", "700"),
    ("bather", "入浴者", "名詞", "Bathers are asked to shower before entering the pool.", "旅行", "700"),
    ("day-trip bathing", "日帰り入浴", "名詞", "Day-trip bathing lets visitors enjoy the hot spring without staying overnight.", "旅行", "700"),
    ("single-sex bathing", "男女別浴", "名詞", "Single-sex bathing is the norm at most Japanese hot springs today.", "旅行", "800"),
    ("nude bathing", "裸で入浴すること", "名詞", "Nude bathing is the traditional custom at most Japanese hot springs.", "旅行", "800"),
    # --- 沢登り・渓流 (domain: アウトドア・レジャー) ---
    ("wetsuit", "ウェットスーツ", "名詞", "Wear a wetsuit to stay warm in the cold stream.", "アウトドア・レジャー", "500"),
    ("helmet", "ヘルメット", "名詞", "A helmet is required for every canyoning trip.", "アウトドア・レジャー", "400"),
    ("harness", "ハーネス（安全帯）", "名詞", "Clip your harness to the rope before you rappel.", "アウトドア・レジャー", "700"),
    ("rappel", "懸垂下降する", "動詞", "We rappelled down the waterfall using a fixed rope.", "アウトドア・レジャー", "800"),
    ("rappelling", "懸垂下降", "名詞", "Rappelling into the waterfall was the highlight of the trip.", "アウトドア・レジャー", "800"),
    ("river crossing", "渡渉", "名詞", "The river crossing was the trickiest part of the route.", "アウトドア・レジャー", "700"),
    ("rock scrambling", "岩場をよじ登ること", "名詞", "Rock scrambling requires careful footing on wet stone.", "アウトドア・レジャー", "700"),
    ("scramble", "よじ登る", "動詞", "We had to scramble over slippery boulders.", "アウトドア・レジャー", "600"),
    ("wade", "水の中を歩く", "動詞", "We waded across the shallow stream.", "アウトドア・レジャー", "500"),
    ("plunge pool", "滝つぼ", "名詞", "Jumpers leapt into the plunge pool below the falls.", "アウトドア・レジャー", "850"),
    ("gorge", "峡谷", "名詞", "The narrow gorge echoed with the sound of rushing water.", "アウトドア・レジャー", "700"),
    ("ravine", "渓谷・小峡谷", "名詞", "The trail follows a steep, narrow ravine.", "アウトドア・レジャー", "700"),
    ("waterproof gear", "防水装備", "名詞", "Bring waterproof gear for the canyon trip.", "アウトドア・レジャー", "600"),
    ("river guide", "リバーガイド", "名詞", "A certified river guide led the group down the canyon.", "アウトドア・レジャー", "600"),
    ("water level", "水位", "名詞", "Check the water level before entering the gorge.", "アウトドア・レジャー", "500"),
    ("flow rate", "流量", "名詞", "The flow rate rises quickly after heavy rain.", "アウトドア・レジャー", "800"),
    ("flash flood warning", "鉄砲水警報", "名詞", "A flash flood warning was issued for the canyon this afternoon.", "アウトドア・レジャー", "850"),
    ("canyoning", "キャニオニング（沢を下るアウトドア活動）", "名詞", "Canyoning combines climbing, swimming, and jumping.", "アウトドア・レジャー", "800"),
    ("stream climbing", "沢登り", "名詞", "Stream climbing is popular among Japanese hikers in summer.", "アウトドア・レジャー", "850"),
    ("carabiner", "カラビナ", "名詞", "Attach the rope to the carabiner securely.", "アウトドア・レジャー", "800"),
    ("swift current", "急流", "名詞", "Be careful of the swift current near the falls.", "アウトドア・レジャー", "700"),
    ("submerged rock", "水面下の岩", "名詞", "Watch for submerged rocks in murky water.", "アウトドア・レジャー", "800"),
    ("canyon", "峡谷（沢登りのフィールド）", "名詞", "The canyon narrows sharply after the second waterfall.", "アウトドア・レジャー", "600"),
    ("throw rope", "救助用の投げ縄ロープ", "名詞", "The guide carries a throw rope for emergencies.", "アウトドア・レジャー", "800"),
    ("eddy", "淀み・反流", "名詞", "The kayaker rested in the eddy behind the rock.", "アウトドア・レジャー", "800"),
    ("undertow", "強い引き波・底流", "名詞", "A hidden undertow can pull swimmers off their feet.", "アウトドア・レジャー", "700"),
    ("keeper hydraulic", "水が渦を巻く危険な地点（キーパー）", "名詞", "Stay clear of the keeper hydraulic below the low-head dam.", "アウトドア・レジャー", "950"),
    # --- 水泳 (domain: スポーツ) ---
    ("freestyle", "自由形（クロール）", "名詞", "Freestyle is the fastest of the four competitive strokes.", "スポーツ", "500"),
    ("front crawl", "クロール", "名詞", "Front crawl and freestyle refer to the same stroke.", "スポーツ", "500"),
    ("backstroke", "背泳ぎ", "名詞", "She won the 100-meter backstroke final.", "スポーツ", "500"),
    ("breaststroke", "平泳ぎ", "名詞", "Breaststroke is often the first stroke beginners learn.", "スポーツ", "500"),
    ("butterfly stroke", "バタフライ", "名詞", "The butterfly stroke demands strong shoulders.", "スポーツ", "600"),
    ("flip turn", "フリップターン（クイックターン）", "名詞", "Competitive swimmers use a flip turn at the wall.", "スポーツ", "700"),
    ("pool lane", "プールのコースロープで区切られた区画", "名詞", "Stay in your pool lane during practice.", "スポーツ", "500"),
    ("lap", "1往復（プールの周回）", "名詞", "I swam twenty laps this morning.", "スポーツ", "400"),
    ("open water swimming", "オープンウォータースイミング（自然の水域での遠泳）", "名詞", "Open water swimming is very different from pool swimming.", "スポーツ", "700"),
    ("swim cap", "スイムキャップ", "名詞", "A swim cap keeps your hair out of your face.", "スポーツ", "400"),
    ("goggles", "ゴーグル", "名詞", "Adjust your goggles before diving in.", "スポーツ", "400"),
    ("buoyancy", "浮力", "名詞", "Body fat increases a swimmer's buoyancy slightly.", "スポーツ", "800"),
    ("tread water", "立ち泳ぎする", "動詞", "Tread water while you wait for the lifeguard.", "スポーツ", "600"),
    ("treading water", "立ち泳ぎ", "名詞", "Treading water for five minutes is a common fitness test.", "スポーツ", "600"),
    ("rip current", "離岸流", "名詞", "Swim parallel to the shore to escape a rip current.", "スポーツ", "800"),
    ("drowning", "溺れること", "名詞", "Drowning can happen silently and very quickly.", "スポーツ", "700"),
    ("drown", "溺れる", "動詞", "He nearly drowned before the lifeguard reached him.", "スポーツ", "600"),
    ("water rescue", "水難救助", "名詞", "The team practiced a water rescue drill.", "スポーツ", "700"),
    ("resuscitation", "蘇生", "名詞", "The lifeguard began resuscitation immediately.", "スポーツ", "850"),
    ("kickboard", "ビート板", "名詞", "Beginners often practice kicking with a kickboard.", "スポーツ", "500"),
    ("pool deck", "プールサイド", "名詞", "Running is not allowed on the pool deck.", "スポーツ", "500"),
    ("deep end", "プールの深い側", "名詞", "Only strong swimmers should use the deep end.", "スポーツ", "500"),
    ("shallow end", "プールの浅い側", "名詞", "Children practice in the shallow end.", "スポーツ", "500"),
    ("swimmer's ear", "水泳耳（外耳炎）", "名詞", "Swimmer's ear is common among frequent swimmers.", "スポーツ", "800"),
    ("surface dive", "水面から潜ること", "名詞", "Use a surface dive to reach the bottom of the pool.", "スポーツ", "700"),
    ("streamline position", "抵抗を減らす体勢（ストリームライン）", "名詞", "Keep a tight streamline position off every wall.", "スポーツ", "800"),
    ("pace clock", "プールサイドの時計（ペースクロック）", "名詞", "Check the pace clock to time your intervals.", "スポーツ", "700"),
    ("negative split", "ネガティブスプリット（後半を速く泳ぐペース配分）", "名詞", "She swam a negative split to finish strong.", "スポーツ", "900"),
    ("dolphin kick", "ドルフィンキック（バタフライで使う波打つキック）", "名詞", "The dolphin kick is essential for the butterfly stroke.", "スポーツ", "750"),
    # --- 釣り (domain: アウトドア・レジャー) ---
    ("fishing rod", "釣り竿", "名詞", "He bought a new fishing rod for the trip.", "アウトドア・レジャー", "400"),
    ("reel", "リール", "名詞", "Attach the reel to the rod before you start.", "アウトドア・レジャー", "500"),
    ("bait", "餌", "名詞", "We used worms as bait.", "アウトドア・レジャー", "500"),
    ("fishing lure", "ルアー", "名詞", "This fishing lure imitates a small injured fish.", "アウトドア・レジャー", "600"),
    ("tackle box", "釣り道具箱", "名詞", "Keep your hooks organized in a tackle box.", "アウトドア・レジャー", "500"),
    ("fishing line", "釣り糸", "名詞", "The fishing line snapped under the weight of the fish.", "アウトドア・レジャー", "500"),
    ("fish hook", "釣り針", "名詞", "Be careful not to prick yourself on the fish hook.", "アウトドア・レジャー", "400"),
    ("cast", "釣り糸を投げる", "動詞", "Cast your line near the rocks.", "アウトドア・レジャー", "500"),
    ("catch and release", "キャッチアンドリリース", "名詞", "Many anglers practice catch and release to protect fish populations.", "アウトドア・レジャー", "700"),
    ("fly fishing", "フライフィッシング", "名詞", "Fly fishing requires a special casting technique.", "アウトドア・レジャー", "700"),
    ("deep sea fishing", "沖釣り・深海釣り", "名詞", "Deep sea fishing boats often head out before dawn.", "アウトドア・レジャー", "700"),
    ("angler", "釣り人", "名詞", "The angler waited patiently for a bite.", "アウトドア・レジャー", "700"),
    ("bite", "魚が餌に食いつくこと", "名詞", "I felt a bite on my line a moment ago.", "アウトドア・レジャー", "500"),
    ("reel in", "巻き上げる", "動詞", "Slowly reel in the line once the fish is hooked.", "アウトドア・レジャー", "500"),
    ("fishing license", "釣り許可証", "名詞", "You need a fishing license to fish in this lake.", "アウトドア・レジャー", "600"),
    ("chum", "撒き餌（魚をおびき寄せる餌）", "名詞", "Fishermen scatter chum to attract fish to the boat.", "アウトドア・レジャー", "900"),
    ("trolling", "トローリング（船を動かしながら釣ること）", "名詞", "Trolling is common when fishing for large ocean fish.", "アウトドア・レジャー", "850"),
    ("ice fishing", "氷上釣り", "名詞", "Ice fishing is popular in cold northern regions.", "アウトドア・レジャー", "700"),
    ("freshwater fishing", "淡水釣り", "名詞", "Freshwater fishing usually targets rivers and lakes.", "アウトドア・レジャー", "600"),
    ("saltwater fishing", "海水釣り", "名詞", "Saltwater fishing requires more corrosion-resistant gear.", "アウトドア・レジャー", "600"),
    ("fishing net", "魚網・タモ網", "名詞", "Use the fishing net to land the fish safely.", "アウトドア・レジャー", "500"),
    ("bobber", "浮き（ウキ）", "名詞", "Watch the bobber closely for any movement.", "アウトドア・レジャー", "700"),
    ("sinker", "重り（シンカー）", "名詞", "Add a sinker to help the bait sink faster.", "アウトドア・レジャー", "700"),
    ("fillet", "魚をおろす", "動詞", "He filleted the fish right on the dock.", "アウトドア・レジャー", "700"),
    ("spawning season", "産卵期", "名詞", "Fishing is restricted during the spawning season.", "アウトドア・レジャー", "800"),
    ("baitfish", "餌用の小魚", "名詞", "Baitfish swim in tight schools near the shore.", "アウトドア・レジャー", "800"),
    ("fishing charter", "釣り船チャーター", "名詞", "We booked a fishing charter for deep sea fishing.", "アウトドア・レジャー", "700"),
    ("school of fish", "魚の群れ", "名詞", "Sonar showed a large school of fish below the boat.", "アウトドア・レジャー", "600"),
]


# --- insertion --------------------------------------------------------------

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")
_STOP = {
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on", "at",
    "for", "with", "from", "by", "as", "is", "are", "was", "were", "be", "been",
    "do", "does", "did", "have", "has", "had", "will", "would", "can", "could",
    "should", "may", "might", "must", "i", "you", "he", "she", "it", "we",
    "they", "me", "him", "her", "us", "them", "my", "your", "his", "its", "our",
    "their", "this", "that", "these", "those", "here", "there", "what", "when",
    "where", "who", "how", "why", "not", "no", "yes", "so", "up", "out", "off",
    "down", "let", "lets", "please", "thanks", "thank", "ok", "okay", "im",
    "ill", "id", "ive", "dont", "cant", "wont", "isnt", "thats", "whats",
    "very", "just", "too", "more", "some", "any", "all", "one", "two", "get",
    "got", "go", "going", "like", "want", "need", "make", "made", "take",
    "see", "now", "today", "tonight", "good", "well", "back", "about", "over",
    "into", "than", "then", "again", "really", "much", "many", "wish", "mind",
    "could", "would", "shall", "rather", "ever", "way", "one's", "off",
    "before", "later", "earlier", "second", "gist", "point", "way", "say",
    "saying", "sure", "understand", "following", "pick", "leave", "there",
}


def _content_words(phrases: list[tuple[str, str]]) -> set[str]:
    out: set[str] = set()
    for en, _ in phrases:
        for tok in _WORD_RE.findall(en.lower()):
            w = tok.strip("'-")
            if len(w) >= 4 and w not in _STOP:
                out.add(w)
    return out


def report_missing() -> None:
    """Print content words used in the new phrases that are not yet in `words`
    and not covered by the WORDS list above (authoring aid)."""
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
    covered = {w[0].lower() for w in WORDS}
    all_phrases = [p for lst in PHRASES_BY_SCENE.values() for p in lst]
    missing = sorted(
        w for w in _content_words(all_phrases)
        if w not in existing and w not in covered
    )
    print(f"missing content words ({len(missing)}):")
    print(", ".join(missing))


def main() -> int:
    if "--missing-words" in sys.argv:
        report_missing()
        return 0

    with db() as conn:
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
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

    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    print(f"words:   +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print("totals -> phrases:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0],
              "words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
