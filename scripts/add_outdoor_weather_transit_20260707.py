"""気象予報士/駅・バス公共アナウンス/アウトドアレジャーの語彙・フレーズ追加。

SESSION_HANDOFF.md の「未了・次の予定」に挙がっていた3分野をまとめて追加する。
domain は既存カテゴリに寄せる方針:

  気象予報士関連       → 地学（scene 気象）
  駅/バス/公共アナウンス → 交通（scene 公共アナウンス）
  登山/キャンプ/ハイキング/散歩/海遊び/遊園地 → アウトドア・レジャー（新規domain, scene アウトドア）

words.detail は空のまま挿入（後段 build_details.py で生成）。
再実行安全: 既存 english（小文字比較）と一致する語/フレーズはスキップする。

使い方:
  python scripts/add_outdoor_weather_transit_20260707.py            # 挿入
  python scripts/add_outdoor_weather_transit_20260707.py --dry-run  # 件数だけ確認
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# (english, japanese, part_of_speech, example, level, domain)
WORDS: list[tuple[str, str, str, str, str, str]] = []
# (english, japanese, scene)
PHRASES: list[tuple[str, str, str]] = []


def W(domain, level, rows):
    for en, ja, pos, ex in rows:
        WORDS.append((en, ja, pos, ex, level, domain))


def P(scene, rows):
    for en, ja in rows:
        PHRASES.append((en, ja, scene))


# ─────────────────────────────────────────────────────────────
# 気象予報士関連（→ 地学）
# ─────────────────────────────────────────────────────────────
W("地学", "700", [
    ("forecast", "予報", "名詞", "The forecast calls for rain tomorrow."),
    ("meteorologist", "気象予報士", "名詞",
     "The meteorologist explained the storm's path."),
    ("barometric pressure", "気圧", "名詞",
     "Barometric pressure is dropping rapidly."),
    ("low-pressure system", "低気圧", "名詞",
     "A low-pressure system is approaching from the west."),
    ("high-pressure system", "高気圧", "名詞",
     "A high-pressure system brings clear skies."),
    ("cold front", "寒冷前線", "名詞", "A cold front will pass through tonight."),
    ("warm front", "温暖前線", "名詞", "The warm front brought humid air."),
    ("precipitation", "降水", "名詞",
     "Precipitation is expected in the afternoon."),
    ("humidity", "湿度", "名詞", "Humidity levels will rise this weekend."),
    ("dew point", "露点", "名詞", "The dew point indicates how muggy it feels."),
    ("wind chill", "体感温度(風による)", "名詞",
     "The wind chill made it feel colder."),
    ("heat index", "暑さ指数", "名詞", "The heat index reached dangerous levels."),
    ("typhoon", "台風", "名詞",
     "The typhoon is expected to make landfall Friday."),
    ("tropical storm", "熱帯低気圧・熱帯暴風雨", "名詞",
     "The tropical storm weakened overnight."),
    ("torrential rain", "豪雨", "名詞",
     "Torrential rain caused flooding downtown."),
    ("thunderstorm", "雷雨", "名詞", "A thunderstorm is likely this evening."),
    ("visibility", "視程", "名詞", "Visibility dropped due to heavy fog."),
    ("cloud cover", "雲量", "名詞", "Cloud cover will increase overnight."),
    ("satellite image", "衛星画像", "名詞",
     "The satellite image shows the storm's eye clearly."),
    ("radar echo", "レーダーエコー", "名詞",
     "The radar echo shows heavy rain bands."),
    ("probability of precipitation", "降水確率", "名詞",
     "The probability of precipitation is sixty percent."),
    ("heat wave", "熱波", "名詞", "A heat wave is forecast for next week."),
    ("cold snap", "急な寒波", "名詞", "A cold snap hit the region overnight."),
    ("air mass", "気団", "名詞", "A cold air mass moved in from the north."),
    ("jet stream", "ジェット気流", "名詞",
     "The jet stream is steering the storm eastward."),
])
P("気象", [
    ("What's the weather forecast for tomorrow?", "明日の天気予報はどうですか?"),
    ("It looks like rain later today.", "今日は後で雨が降りそうです。"),
    ("A typhoon is approaching the region.", "台風がこの地域に近づいています。"),
    ("Please stay indoors during the storm.", "嵐の間は屋内にいてください。"),
    ("The temperature will drop sharply tonight.", "今夜は気温が急に下がります。"),
    ("There's a chance of thunderstorms this afternoon.",
     "今日の午後は雷雨の可能性があります。"),
    ("Visibility is poor due to fog.", "霧のため視界が悪いです。"),
    ("A heat wave warning has been issued.", "熱波警報が発令されました。"),
    ("The rainy season usually starts in June.", "梅雨は通常6月に始まります。"),
    ("Bring an umbrella just in case.", "念のため傘を持って行ってください。"),
    ("The wind is picking up.", "風が強くなってきています。"),
    ("It's freezing outside.", "外は凍えるほど寒いです。"),
    ("The forecast has been updated.", "予報が更新されました。"),
    ("A cold front is moving in.", "寒冷前線が近づいています。"),
    ("Snow is expected in the mountains.", "山では雪が予想されています。"),
])

# ─────────────────────────────────────────────────────────────
# 駅/バス/公共アナウンス（→ 交通）
# ─────────────────────────────────────────────────────────────
W("交通", "500", [
    ("platform", "ホーム", "名詞", "The train departs from platform three."),
    ("transfer", "乗り換え", "名詞", "Please transfer to the local line here."),
    ("terminal station", "終着駅", "名詞", "This is the terminal station."),
    ("express train", "急行", "名詞", "The express train doesn't stop here."),
    ("local train", "各駅停車", "名詞", "Take the local train for this stop."),
    ("delay", "遅延", "名詞", "There is a ten-minute delay."),
    ("suspension of service", "運転見合わせ", "名詞",
     "There is a suspension of service due to an accident."),
    ("fare adjustment", "精算", "名詞",
     "Use the fare adjustment machine before exiting."),
    ("IC card", "ICカード", "名詞", "Tap your IC card at the gate."),
    ("ticket gate", "改札", "名詞", "Meet me at the ticket gate."),
    ("last train", "終電", "名詞", "I need to catch the last train."),
    ("priority seat", "優先席", "名詞",
     "Please offer the priority seat to elderly passengers."),
    ("designated seat", "指定席", "名詞",
     "This is a designated seat reservation."),
    ("non-reserved seat", "自由席", "名詞",
     "Non-reserved seats are on cars one through three."),
    ("boarding", "乗車", "名詞", "Boarding will begin shortly."),
    ("alighting", "降車", "名詞", "Please watch your step when alighting."),
    ("bus stop", "バス停", "名詞", "The bus stop is around the corner."),
    ("next stop", "次の停留所・次の駅", "名詞",
     "The next stop is Central Station."),
    ("final destination", "終点", "名詞",
     "This bus's final destination is the airport."),
    ("route number", "系統番号", "名詞", "Check the route number before boarding."),
    ("accident", "事故", "名詞",
     "The delay is due to an accident at the last station."),
    ("overcrowding", "混雑", "名詞", "There is overcrowding on the morning train."),
    ("lost and found", "忘れ物・遺失物", "名詞",
     "Report it to lost and found at the station office."),
    ("emergency stop button", "非常停止ボタン", "名詞",
     "Do not press the emergency stop button unless necessary."),
    ("announcement", "アナウンス・案内放送", "名詞",
     "Listen carefully to the announcement."),
])
P("公共アナウンス", [
    ("The next station is Shibuya.", "次の駅は渋谷です。"),
    ("Please mind the gap between the train and the platform.",
     "電車とホームの隙間にご注意ください。"),
    ("This train will be delayed by approximately ten minutes.",
     "この電車は約10分遅れています。"),
    ("Please change to the Yamanote Line at this station.",
     "この駅で山手線にお乗り換えください。"),
    ("The doors are closing. Please stand clear.",
     "ドアが閉まります。ご注意ください。"),
    ("Please refrain from talking on your phone on the train.",
     "車内での通話はご遠慮ください。"),
    ("This is the last stop. All passengers please exit.",
     "終点です。お忘れ物のないようご注意ください。"),
    ("Attention passengers, the train is now boarding.",
     "ご案内します。まもなく発車します。"),
    ("Please have your ticket ready for inspection.",
     "切符をご用意ください。"),
    ("Due to heavy congestion, some trains are running late.",
     "混雑のため、一部の電車が遅れています。"),
    ("Please give up your seat to those who need it.",
     "席を必要とする方に譲ってください。"),
    ("The bus is now approaching the stop.", "バスが停留所に近づいています。"),
    ("Please hold the handrail while the bus is moving.",
     "バスが動いている間は手すりをお持ちください。"),
    ("We apologize for the inconvenience.", "ご迷惑をおかけして申し訳ございません。"),
    ("This service has been suspended due to an accident.",
     "事故のため運転を見合わせております。"),
])

# ─────────────────────────────────────────────────────────────
# 登山/キャンプ/ハイキング/散歩/海遊び/遊園地（→ アウトドア・レジャー 新規domain）
# ─────────────────────────────────────────────────────────────
W("アウトドア・レジャー", "500", [
    ("trailhead", "登山口", "名詞", "We met at the trailhead early in the morning."),
    ("summit", "山頂", "名詞", "We reached the summit by noon."),
    ("altitude sickness", "高山病", "名詞",
     "Altitude sickness can strike above 2,500 meters."),
    ("hiking boots", "登山靴", "名詞",
     "Wear sturdy hiking boots on rocky trails."),
    ("backpack", "リュックサック", "名詞", "Pack light in your backpack."),
    ("tent", "テント", "名詞", "We pitched the tent near the river."),
    ("sleeping bag", "寝袋", "名詞",
     "A warm sleeping bag is essential in winter."),
    ("campfire", "キャンプファイア", "名詞", "We gathered around the campfire."),
    ("campsite", "キャンプ場", "名詞",
     "The campsite has running water and toilets."),
    ("hiking trail", "ハイキングコース", "名詞",
     "This hiking trail takes about three hours."),
    ("walking stick", "杖・トレッキングポール", "名詞",
     "A walking stick helps on steep descents."),
    ("compass", "コンパス", "名詞", "Bring a compass in case your phone dies."),
    ("flashlight", "懐中電灯", "名詞", "Pack a flashlight for the night hike."),
    ("mosquito repellent", "虫よけ", "名詞",
     "Apply mosquito repellent before entering the forest."),
    ("sunscreen", "日焼け止め", "名詞", "Don't forget sunscreen at the beach."),
    ("beach umbrella", "ビーチパラソル", "名詞",
     "We rented a beach umbrella for the day."),
    ("swimsuit", "水着", "名詞", "Pack an extra swimsuit."),
    ("snorkeling", "シュノーケリング", "名詞", "We went snorkeling near the reef."),
    ("sandcastle", "砂の城", "名詞", "The kids built a sandcastle."),
    ("lifeguard", "ライフガード", "名詞", "The lifeguard blew the whistle."),
    ("roller coaster", "ジェットコースター", "名詞",
     "The roller coaster was terrifying."),
    ("Ferris wheel", "観覧車", "名詞", "We rode the Ferris wheel at sunset."),
    ("carousel", "メリーゴーランド", "名詞", "The little kids loved the carousel."),
    ("admission ticket", "入場券", "名詞",
     "Buy the admission ticket online in advance."),
    ("scenic route", "散歩道・景色の良い道", "名詞",
     "We took the scenic route along the river."),
])
P("アウトドア", [
    ("Let's go hiking this weekend.", "今週末ハイキングに行こう。"),
    ("Don't forget to bring enough water.", "水分を十分に持ってくるのを忘れないで。"),
    ("The trail gets steep near the top.", "頂上付近は道が急になります。"),
    ("We should pitch the tent before it gets dark.",
     "暗くなる前にテントを張ろう。"),
    ("Watch your step, the rocks are slippery.",
     "足元に気をつけて、岩が滑りやすいです。"),
    ("Let's take a break and enjoy the view.", "休憩して景色を楽しもう。"),
    ("The weather can change quickly in the mountains.",
     "山の天気は急に変わることがあります。"),
    ("Make sure to pack out all your trash.", "ゴミは必ず持ち帰ってください。"),
    ("Let's go for a walk along the beach.", "海沿いを散歩しよう。"),
    ("The water looks calm today, perfect for swimming.",
     "今日は波が穏やかで泳ぐのにぴったりです。"),
    ("Which ride do you want to go on first?", "最初にどの乗り物に乗りたい?"),
    ("The line for the roller coaster is really long.",
     "ジェットコースターの列がとても長い。"),
    ("Let's meet at the entrance at nine.", "9時に入口で会おう。"),
    ("Be careful of sunburn, it's really strong today.",
     "今日は日差しが強いから日焼けに気をつけて。"),
    ("This is a great spot for a picnic.", "ここはピクニックにぴったりの場所だね。"),
])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="件数だけ表示して挿入しない")
    args = ap.parse_args()

    with db() as conn:
        have_w = {r[0].strip().lower()
                  for r in conn.execute("SELECT english FROM words")}
        have_p = {r[0].strip().lower()
                  for r in conn.execute("SELECT english FROM phrases")}

        new_w = [w for w in WORDS if w[0].strip().lower() not in have_w]
        seen = set()
        uniq_w = []
        for w in new_w:
            k = w[0].strip().lower()
            if k in seen:
                continue
            seen.add(k)
            uniq_w.append(w)

        new_p = []
        seen_p = set()
        for p in PHRASES:
            k = p[0].strip().lower()
            if k in have_p or k in seen_p:
                continue
            seen_p.add(k)
            new_p.append(p)

        print(f"WORDS  : 定義 {len(WORDS)} / 新規 {len(uniq_w)} "
              f"(既存重複 {len(WORDS) - len(uniq_w)})")
        print(f"PHRASES: 定義 {len(PHRASES)} / 新規 {len(new_p)} "
              f"(既存重複 {len(PHRASES) - len(new_p)})")
        by_dom: dict[str, int] = {}
        for w in uniq_w:
            by_dom[w[5]] = by_dom.get(w[5], 0) + 1
        for d, n in sorted(by_dom.items(), key=lambda x: -x[1]):
            print(f"   {d}: {n}")

        if args.dry_run:
            print("[dry-run] 挿入しません。")
            return 0

        conn.executemany(
            "INSERT INTO words (english, japanese, part_of_speech, example, "
            "level, domain) VALUES (?, ?, ?, ?, ?, ?)", uniq_w,
        )
        conn.executemany(
            "INSERT INTO phrases (english, japanese, scene) VALUES (?, ?, ?)",
            new_p,
        )
        print(f"挿入完了: words +{len(uniq_w)} / phrases +{len(new_p)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
