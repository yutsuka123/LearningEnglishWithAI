# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated words & phrases for WINTER SPORTS and
MOUNTAINEERING / HIKING / TREKKING / CLIMBING, authored by Claude.

Focus (アウトドア語彙の手薄な領域を補強):
  1) ウィンタースポーツ — スキー（滑走・技術・ギア・リフト）、スノーボード、
     クロスカントリースキー、そり遊び、氷上競技、防寒・低体温症/凍傷など
     一般的な冬山・雪上の安全語彙まで。
  2) 登山・トレッキング・クライミング — 本格的な登山技術（アイゼン、ピッケル、
     ビレイ、懸垂下降など）、日帰り〜長距離のハイキング/トレッキング、
     フリークライミング（ボルダリング〜リードクライミング）の語彙。

既存の `アウトドア・レジャー` domain（キャンプ/ハイキング/道具など22語）と
`スポーツ` domain（審判・大会などの一般スポーツ語彙）は重複しないよう事前に
確認済み。新規語彙も同じ `アウトドア・レジャー` domain に合わせて追加する。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_winter_mountain_sports.py
      python scripts/add_winter_mountain_sports.py --missing-words   # report only

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
    "ウィンタースポーツ": [
        # --- ギア・準備 ---
        ("Do you have your own skis, or do you need to rent?", "自分のスキー板は持ってる？それともレンタルが必要？"),
        ("Let's rent snowboard boots at the shop.", "お店でスノーボードブーツを借りましょう。"),
        ("Can you adjust my bindings? They feel too loose.", "ビンディングを調整してもらえますか？緩い気がします。"),
        ("I need to wax my skis before tomorrow's race.", "明日のレースの前にスキーにワックスをかけないと。"),
        ("Don't forget your goggles — the glare is intense today.", "ゴーグルを忘れないで。今日は照り返しがすごいから。"),
        ("Wear thermal layers under your jacket; it's brutally cold today.", "今日はものすごく寒いから、ジャケットの下に防寒インナーを着て。"),
        # --- コース状況・天候 ---
        ("What are the trail conditions like today?", "今日のコース状況はどうですか？"),
        ("Check the avalanche forecast before we go off-piste.", "コース外に出る前に雪崩予報を確認しよう。"),
        ("The powder is amazing after last night's snowfall.", "昨夜の降雪のあと、パウダーが最高だよ。"),
        ("That black run looks too icy for me today.", "あの黒コース、今日は凍結しすぎてて自分には無理そう。"),
        ("Visibility is dropping fast — we should head down.", "視界がどんどん悪くなってる。下山した方がいいね。"),
        ("A winter storm warning was just issued for this area.", "この地域に冬季暴風雪警報が出たばかりです。"),
        # --- リフト・レッスン ---
        ("Which lift takes us to the intermediate slopes?", "どのリフトに乗れば中級コースに行けますか？"),
        ("Grab the safety bar on the chairlift.", "チェアリフトの安全バーをつかんで。"),
        ("I'm still a beginner, so let's stick to the green runs.", "まだ初心者だから、初級コースにしておこう。"),
        ("Could I book a private ski lesson for tomorrow?", "明日、プライベートスキーレッスンを予約できますか？"),
        ("Bend your knees more when you carve.", "カービングするときはもっと膝を曲げて。"),
        ("Try a snowplow turn to control your speed.", "スピードを抑えるためにスノープラウターンをしてみて。"),
        # --- 安全 ---
        ("Ski patrol closed that run because of avalanche danger.", "雪崩の危険があるためスキーパトロールがそのコースを閉鎖しました。"),
        ("Always ski with a buddy in the backcountry.", "バックカントリーでは必ず仲間と一緒に滑ること。"),
        ("If you get frostbite symptoms, get inside immediately.", "凍傷の症状が出たら、すぐに室内に入って。"),
        ("Watch out for that icy patch near the lift line.", "リフト待ちの列の近くの凍結箇所に気をつけて。"),
        ("My fingers are going numb — I think I need warmer gloves.", "指の感覚がなくなってきた。もっと暖かい手袋が必要かも。"),
        # --- アプレスキー・雑談 ---
        ("Let's warm up at the lodge with some hot cocoa.", "ロッジでホットココアを飲んで温まろう。"),
        ("That was an incredible run — let's do it again!", "今の滑走、最高だった！もう一回行こう！"),
        ("I'm exhausted. Let's call it a day after this run.", "もうくたくた。この滑走で今日は終わりにしよう。"),
        ("How was the snow up top?", "上の方の雪の状態はどうだった？"),
        ("Are you up for a night skiing session?", "ナイタースキーやる？"),
    ],
    "登山・トレッキング・クライミング": [
        # --- 計画・トレイル状況 ---
        ("What are the trail conditions like this time of year?", "この時期のトレイルの状況はどうですか？"),
        ("How much elevation gain does this route have?", "このルートの獲得標高はどのくらいですか？"),
        ("Is the trailhead accessible by car, or do we need a shuttle?", "登山口は車で行けますか、それともシャトルが必要ですか？"),
        ("We should start before sunrise to beat the afternoon storms.", "午後の雷雨を避けるために日の出前に出発しよう。"),
        ("Check the weather forecast before we commit to the summit push.", "登頂を決める前に天気予報を確認しよう。"),
        ("Is the pass still snowed in this late in the season?", "この時期でも峠はまだ雪で塞がっていますか？"),
        # --- 装備チェック ---
        ("Do you have your crampons and ice axe ready?", "アイゼンとピッケルの準備はできてる？"),
        ("Let's do a gear check before we rope up.", "ロープを結ぶ前に装備チェックをしよう。"),
        ("Make sure your harness is double-backed.", "ハーネスがちゃんとダブルバックになってるか確認して。"),
        ("I packed extra layers in case it gets colder up there.", "上で寒くなった場合に備えて予備の防寒着を詰めた。"),
        ("Don't forget your headlamp — we might finish after dark.", "ヘッドランプを忘れないで。日没後になるかもしれないから。"),
        ("These new boots are already giving me a blister.", "この新しい靴、もう靴擦れができてきた。"),
        # --- 安全・引き返し判断 ---
        ("We need to turn back — the weather's closing in.", "引き返さないと。天気が悪くなってきてる。"),
        ("Rope up here; the glacier gets crevassed ahead.", "ここでロープを結ぼう。この先氷河にクレバスが増えるから。"),
        ("Watch for loose rock on this scree slope.", "このガレ場では落石に気をつけて。"),
        ("Let's set our turnaround time now, no matter how far we've gotten.", "どこまで進んでいても、今のうちに引き返す時刻を決めておこう。"),
        ("That ridge has serious exposure — stay close to the rock.", "あの尾根は切れ落ちていて危険だから、岩際に寄って歩いて。"),
        ("If anyone shows signs of altitude sickness, we descend immediately.", "誰かに高山病の症状が出たら、すぐに下山します。"),
        ("I'll belay you on this next pitch.", "次のピッチは私がビレイするよ。"),
        ("On belay?", "ビレイの準備はできましたか？〔登る前の確認の掛け声〕"),
        ("Belay on. Climb when ready.", "確保できました。いつでも登ってください。〔ビレイヤーの返答〕"),
        # --- 行程・トレイルトーク ---
        ("How much farther to the summit?", "山頂まであとどのくらいですか？"),
        ("We're making good time — we should reach the hut by noon.", "いいペースで進んでいる。正午までに山小屋に着けそうだ。"),
        ("This switchback section really tests your legs.", "このつづら折りの区間は本当に脚にくる。"),
        ("Let's refill our water bottles at the spring.", "湧き水のところで水筒に補給しよう。"),
        ("Take a short break here before the final ascent.", "最後の登りの前にここで小休止しよう。"),
        ("The view from the ridgeline is worth every step.", "尾根からの景色はここまで歩いた甲斐がある。"),
        # --- クライミング特有 ---
        ("What grade is this route?", "このルートのグレードはどのくらい？"),
        ("Chalk up before you try that crux move.", "あの核心部の動きを試す前にチョークをつけて。"),
        ("I'll spot you until you clip the first bolt.", "最初のボルトにクリップするまでスポットするよ。"),
        ("Are you top-roping this, or do you want to lead it?", "これはトップロープでやる？それともリードで登りたい？"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

_DOMAIN = "アウトドア・レジャー"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # ============================= ウィンタースポーツ =============================
    # --- スキー基礎 ---
    ("ski", "スキーをする・滑る", "動詞", "We ski every weekend in winter.", _DOMAIN, "300"),
    ("skiing", "スキー（競技・活動）", "名詞", "Skiing is popular in Nagano.", _DOMAIN, "300"),
    ("skier", "スキーヤー", "名詞", "The skier carved smoothly down the slope.", _DOMAIN, "400"),
    ("ski resort", "スキー場", "名詞", "The ski resort opens in early December.", _DOMAIN, "400"),
    ("ski slope", "ゲレンデ・スキー斜面", "名詞", "Beginners should stick to the gentle ski slope.", _DOMAIN, "500"),
    ("piste", "ピステ（整備された滑走コース）", "名詞", "The piste was freshly groomed this morning.", _DOMAIN, "800"),
    ("chairlift", "チェアリフト", "名詞", "We rode the chairlift to the summit.", _DOMAIN, "500"),
    ("ski lift", "スキーリフト（総称）", "名詞", "The line for the ski lift was long today.", _DOMAIN, "450"),
    ("gondola", "ゴンドラ", "名詞", "The gondola carries eight passengers at a time.", _DOMAIN, "550"),
    ("ski poles", "ストック（スキーポール）", "名詞", "Plant your ski poles for balance on turns.", _DOMAIN, "550"),
    ("ski boots", "スキーブーツ", "名詞", "My ski boots feel too tight today.", _DOMAIN, "500"),
    ("bindings", "ビンディング", "名詞", "Make sure your bindings are adjusted to your weight.", _DOMAIN, "700"),
    ("mogul", "モーグル（コブ状の雪面）", "名詞", "He skied straight through a field of moguls.", _DOMAIN, "750"),
    ("powder snow", "パウダースノー", "名詞", "We got fresh powder snow overnight.", _DOMAIN, "600"),
    ("black run", "上級者用コース（黒マーク）", "名詞", "That black run is too steep for beginners.", _DOMAIN, "750"),
    ("avalanche", "雪崩", "名詞", "The resort closed the back bowl due to avalanche risk.", _DOMAIN, "700"),
    ("ski patrol", "スキーパトロール", "名詞", "Ski patrol closed the trail after the storm.", _DOMAIN, "750"),
    ("apres-ski", "アプレスキー（滑走後の社交）", "名詞", "We had hot chocolate for apres-ski.", _DOMAIN, "900"),
    ("snowplow turn", "スノープラウターン（ハの字ターン）", "名詞", "Beginners learn the snowplow turn first.", _DOMAIN, "800"),
    ("ski wax", "スキーワックス", "名詞", "He waxed his skis with fresh ski wax before the race.", _DOMAIN, "800"),
    ("ski edge", "エッジ（スキー板の縁）", "名詞", "Dig your ski edges into the snow to slow down.", _DOMAIN, "750"),
    ("traverse", "斜滑降・トラバース", "動詞", "We traversed the slope to avoid the icy patch.", _DOMAIN, "800"),
    ("downhill skiing", "滑降（アルペンスキー）", "名詞", "Downhill skiing is the resort's most popular sport.", _DOMAIN, "500"),
    ("alpine skiing", "アルペンスキー", "名詞", "Alpine skiing includes downhill, slalom, and giant slalom.", _DOMAIN, "700"),
    ("slalom", "スラローム（回転）", "名詞", "She won the women's slalom by half a second.", _DOMAIN, "800"),
    ("giant slalom", "大回転", "名詞", "The giant slalom course has widely spaced gates.", _DOMAIN, "850"),
    ("ski jump", "スキージャンプ", "名詞", "The ski jump venue was built for the Olympics.", _DOMAIN, "600"),
    # --- スノーボード ---
    ("snowboard", "スノーボード", "名詞", "He strapped on his snowboard and headed to the lift.", _DOMAIN, "350"),
    ("snowboarding", "スノーボード（競技）", "名詞", "Snowboarding became an Olympic sport in 1998.", _DOMAIN, "400"),
    ("halfpipe", "ハーフパイプ", "名詞", "She landed a huge jump in the halfpipe.", _DOMAIN, "700"),
    ("freestyle", "フリースタイル（スキー・スノボ）", "名詞", "He competes in freestyle skiing events.", _DOMAIN, "600"),
    ("carving", "カービング（ターン技術）", "名詞", "Carving turns look smooth and fast.", _DOMAIN, "750"),
    ("rail / box (jib)", "レール・ボックス（ジブ）", "名詞", "She slid across the rail without falling.", _DOMAIN, "850"),
    # --- クロスカントリー ---
    ("cross-country skiing", "クロスカントリースキー", "名詞", "Cross-country skiing is great cardio exercise.", _DOMAIN, "600"),
    ("Nordic skiing", "ノルディックスキー", "名詞", "Nordic skiing includes cross-country and ski jumping.", _DOMAIN, "800"),
    ("ski track", "スキートラック（整備された走路）", "名詞", "Stay in the ski track when passing other skiers.", _DOMAIN, "800"),
    ("biathlon", "バイアスロン", "名詞", "Biathlon combines cross-country skiing and rifle shooting.", _DOMAIN, "750"),
    # --- そり・氷上競技 ---
    ("luge", "リュージュ", "名詞", "Luge athletes reach speeds over 140 kilometers per hour.", _DOMAIN, "850"),
    ("bobsled", "ボブスレー", "名詞", "The bobsled team pushed off hard at the start.", _DOMAIN, "800"),
    ("sled", "そり", "名詞", "The kids pulled their sled up the hill.", _DOMAIN, "350"),
    ("sledding", "そり遊び", "名詞", "We went sledding after the snowstorm.", _DOMAIN, "400"),
    ("toboggan", "トボガン（細長いそり）", "名詞", "The toboggan run was fast and bumpy.", _DOMAIN, "800"),
    ("snow tube", "スノーチューブ", "名詞", "We rode a snow tube down the hill and laughed the whole way.", _DOMAIN, "550"),
    # --- 一般的な冬季安全・装備 ---
    ("frostbite", "凍傷", "名詞", "Cover your fingers and toes to prevent frostbite.", _DOMAIN, "800"),
    ("hypothermia", "低体温症", "名詞", "Wet clothes in the cold can lead to hypothermia.", _DOMAIN, "800"),
    ("snow chains", "スノーチェーン", "名詞", "Put snow chains on your tires before crossing the pass.", _DOMAIN, "600"),
    ("thermal layers", "防寒インナー（保温レイヤー）", "名詞", "Wear thermal layers under your ski jacket.", _DOMAIN, "700"),
    ("base layer", "ベースレイヤー（肌着）", "名詞", "A moisture-wicking base layer keeps you dry and warm.", _DOMAIN, "750"),
    ("snowshoeing", "スノーシューイング", "名詞", "We tried snowshoeing through the quiet forest.", _DOMAIN, "750"),
    ("snowshoe", "スノーシュー（かんじき）", "名詞", "Strap on your snowshoes before we head into deep snow.", _DOMAIN, "750"),
    ("ice skating", "アイススケート", "名詞", "The whole family went ice skating on the frozen pond.", _DOMAIN, "400"),
    ("ice rink", "スケートリンク", "名詞", "The outdoor ice rink opens in November.", _DOMAIN, "450"),
    ("figure skating", "フィギュアスケート", "名詞", "She has practiced figure skating since she was five.", _DOMAIN, "500"),
    ("speed skating", "スピードスケート", "名詞", "Speed skating demands powerful leg muscles.", _DOMAIN, "600"),
    ("goggles", "ゴーグル", "名詞", "Wear goggles to protect your eyes from the glare.", _DOMAIN, "500"),
    ("balaclava", "目出し帽・バラクラバ", "名詞", "He wore a balaclava against the freezing wind.", _DOMAIN, "850"),
    ("gaiters", "ゲイター（防雪スパッツ）", "名詞", "Gaiters keep snow out of your boots.", _DOMAIN, "850"),
    ("snowdrift", "吹きだまり", "名詞", "The car got stuck in a snowdrift.", _DOMAIN, "700"),
    ("icy patch", "凍結箇所", "名詞", "Watch out for that icy patch near the lodge entrance.", _DOMAIN, "600"),
    ("black ice", "ブラックアイス（見えにくい路面凍結）", "名詞", "Black ice on the road is very hard to see.", _DOMAIN, "700"),
    ("ski lodge", "山小屋・ロッジ", "名詞", "We warmed up by the fire at the ski lodge.", _DOMAIN, "550"),
    ("groomed trail", "圧雪されたコース", "名詞", "The groomed trail was perfectly smooth this morning.", _DOMAIN, "800"),
    ("ice fishing", "氷上釣り", "名詞", "We went ice fishing on the frozen lake.", _DOMAIN, "600"),
    ("winter storm warning", "冬季暴風雪警報", "名詞", "A winter storm warning was issued for the mountains.", _DOMAIN, "700"),

    # ===================== 登山・トレッキング・クライミング =====================
    # --- 登山技術 ---
    ("mountaineering", "登山（本格的な）", "名詞", "Mountaineering requires both technical skill and endurance.", _DOMAIN, "700"),
    ("summit attempt", "登頂アタック", "名詞", "Bad weather forced them to abandon the summit attempt.", _DOMAIN, "850"),
    ("base camp", "ベースキャンプ", "名詞", "Climbers rest at base camp before the final push.", _DOMAIN, "700"),
    ("crampons", "アイゼン（クランポン）", "名詞", "Put on your crampons before crossing the ice field.", _DOMAIN, "900"),
    ("ice axe", "ピッケル", "名詞", "Use your ice axe to arrest a slide on the slope.", _DOMAIN, "900"),
    ("carabiner", "カラビナ", "名詞", "Clip the rope into the carabiner.", _DOMAIN, "850"),
    ("harness", "ハーネス", "名詞", "Double-check your harness before you start climbing.", _DOMAIN, "800"),
    ("belay", "ビレイ（確保する・確保）", "動詞", "I'll belay you while you lead this pitch.", _DOMAIN, "900"),
    ("belayer", "ビレイヤー（確保者）", "名詞", "The belayer kept the rope taut the whole time.", _DOMAIN, "900"),
    ("rappel", "懸垂下降する", "動詞", "We rappelled down the cliff face to reach the trail.", _DOMAIN, "900"),
    ("abseil", "懸垂下降する（英式表現）", "動詞", "They abseiled into the narrow canyon.", _DOMAIN, "900"),
    ("rope team", "ロープパーティー（連結登攀チーム）", "名詞", "The rope team crossed the glacier together, roped up.", _DOMAIN, "900"),
    ("altitude acclimatization", "高度順応", "名詞", "We spent two extra days on altitude acclimatization.", _DOMAIN, "900"),
    ("switchback", "つづら折り（九十九折り）", "名詞", "The trail climbed the ridge in tight switchbacks.", _DOMAIN, "750"),
    ("scree", "ガレ場（崩れた岩くず）", "名詞", "We slid and stumbled down the loose scree.", _DOMAIN, "900"),
    ("ridgeline", "尾根筋", "名詞", "The trail follows the ridgeline for two miles.", _DOMAIN, "800"),
    ("col", "鞍部・コル（尾根の低くなった部分）", "名詞", "We crossed the col before the afternoon clouds rolled in.", _DOMAIN, "900"),
    ("mountain pass", "峠", "名詞", "Snow blocked the mountain pass all winter.", _DOMAIN, "600"),
    ("crevasse", "クレバス", "名詞", "The glacier was riddled with hidden crevasses.", _DOMAIN, "850"),
    ("bivouac", "ビバーク（緊急野営）", "名詞", "They had to bivouac just below the summit overnight.", _DOMAIN, "950"),
    ("via ferrata", "ビアフェラータ（鉄製の足場付きルート）", "名詞", "The via ferrata has steel cables and rungs for protection.", _DOMAIN, "950"),
    ("glissade", "グリセード（雪面を滑り降りる下山技術）", "名詞", "We glissaded down the snowfield to save an hour.", _DOMAIN, "950"),
    ("couloir", "クーロワール（急峻な岩溝・雪渓）", "名詞", "The route follows a steep couloir to the summit ridge.", _DOMAIN, "950"),
    ("false summit", "偽ピーク（頂上と見誤る地点）", "名詞", "They reached a false summit and had to keep climbing.", _DOMAIN, "900"),
    ("exposure", "危険な高度感・切れ落ちた地形", "名詞", "The narrow ridge had serious exposure on both sides.", _DOMAIN, "900"),
    ("avalanche transceiver", "雪崩ビーコン", "名詞", "Everyone in the group carried an avalanche transceiver.", _DOMAIN, "900"),
    ("rockfall", "落石", "名詞", "Rockfall is a real danger in that gully after noon.", _DOMAIN, "800"),
    ("gully", "ガリー（岩溝）", "名詞", "They climbed a narrow gully to reach the ridge.", _DOMAIN, "850"),
    ("talus", "岩塊斜面（タラス）", "名詞", "The trail crossed a field of talus below the peak.", _DOMAIN, "950"),
    ("self-arrest", "セルフアレスト（滑落停止）", "動詞", "Practice self-arrest with your ice axe before the climb.", _DOMAIN, "950"),
    ("fixed rope", "フィックスロープ（固定ロープ）", "名詞", "Climbers clip into the fixed rope on the steep section.", _DOMAIN, "900"),
    ("climbing pitch", "ピッチ（ロープ一区間）", "名詞", "The route has six pitches of moderate climbing.", _DOMAIN, "900"),
    ("approach trail", "アプローチ（登山口から取付までの道）", "名詞", "The approach trail alone took two hours over loose rock.", _DOMAIN, "850"),
    # --- ハイキング・トレッキング ---
    ("day hike", "日帰りハイキング", "名詞", "We planned a day hike to the waterfall.", _DOMAIN, "500"),
    ("thru-hike", "長距離縦走（通し歩き）", "名詞", "She completed a thru-hike of the entire trail in four months.", _DOMAIN, "850"),
    ("trekking poles", "トレッキングポール", "名詞", "Trekking poles ease the strain on your knees going downhill.", _DOMAIN, "700"),
    ("elevation gain", "標高差（獲得標高）", "名詞", "The route has 800 meters of elevation gain.", _DOMAIN, "750"),
    ("refuge", "山小屋（避難小屋）", "名詞", "We stayed overnight at a mountain refuge.", _DOMAIN, "800"),
    ("mountain hut", "山小屋", "名詞", "The mountain hut serves hot meals to tired hikers.", _DOMAIN, "600"),
    ("blister", "まめ（靴擦れ）", "名詞", "New boots gave her a painful blister on her heel.", _DOMAIN, "600"),
    ("trail marker", "トレイルマーカー（道標）", "名詞", "Follow the trail markers to stay on route.", _DOMAIN, "650"),
    ("cairn", "ケルン（石積みの道標）", "名詞", "A stone cairn marked the junction above the tree line.", _DOMAIN, "850"),
    ("trekking", "トレッキング", "名詞", "We went trekking in the foothills of the Himalayas.", _DOMAIN, "500"),
    ("hiker", "ハイカー", "名詞", "The hiker filled her bottle at a mountain spring.", _DOMAIN, "400"),
    ("hike", "ハイキングする・歩く", "動詞", "We hiked six miles before stopping for lunch.", _DOMAIN, "350"),
    ("peak", "山頂・ピーク", "名詞", "They reached the peak just before sunset.", _DOMAIN, "500"),
    ("ascent", "登り・登頂", "名詞", "The final ascent took three grueling hours.", _DOMAIN, "750"),
    ("descent", "下山・下り", "名詞", "The descent is often harder on the knees than the climb up.", _DOMAIN, "700"),
    ("headlamp", "ヘッドランプ", "名詞", "We started the climb before dawn with headlamps on.", _DOMAIN, "600"),
    ("backcountry", "バックカントリー（山岳未圧雪エリア）", "名詞", "They skied in the backcountry, far from the resort lifts.", _DOMAIN, "800"),
    # --- ロッククライミング ---
    ("bouldering", "ボルダリング", "名詞", "Bouldering doesn't require ropes, just crash pads.", _DOMAIN, "750"),
    ("crag", "クラッグ（岩場）", "名詞", "The crag was crowded with climbers on Saturday.", _DOMAIN, "900"),
    ("climbing route", "クライミングルート", "名詞", "This route has a tricky overhang halfway up.", _DOMAIN, "700"),
    ("grade", "グレード（難易度）", "名詞", "This climb has a grade of 5.10a.", _DOMAIN, "750"),
    ("difficulty rating", "難易度評価", "名詞", "Check the difficulty rating before you commit to a route.", _DOMAIN, "700"),
    ("chalk bag", "チョークバッグ", "名詞", "She reached into her chalk bag before the crux move.", _DOMAIN, "850"),
    ("climbing shoes", "クライミングシューズ", "名詞", "Climbing shoes fit much tighter than ordinary sneakers.", _DOMAIN, "700"),
    ("top rope", "トップロープ", "名詞", "Beginners usually start out on top rope.", _DOMAIN, "800"),
    ("lead climbing", "リードクライミング", "名詞", "Lead climbing means clipping the rope in as you go up.", _DOMAIN, "900"),
    ("free solo", "フリーソロ（ロープなし単独登攀）", "名詞", "Free solo climbing leaves almost no margin for error.", _DOMAIN, "950"),
    ("crux", "クラックス（核心部・最難関の動き）", "名詞", "The crux of the route is a tiny overhang near the top.", _DOMAIN, "900"),
    ("overhang", "オーバーハング（せり出した岩壁）", "名詞", "He struggled on the steep overhang for ten minutes.", _DOMAIN, "800"),
    ("climbing anchor", "アンカー（登攀の支点）", "名詞", "Build a solid climbing anchor before you lower off.", _DOMAIN, "850"),
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
