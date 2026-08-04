# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add TAXI vocabulary and phrases, authored by Claude (2026-08-04・
ユーザー要望:「タクシー用語 乗るときなど」)。

既存DBを確認したところ、タクシー専用のdomain/sceneは存在せず、"cabinet"
"cabin crew" "hyperparameter" のような偶然の部分一致(cab, parameter等)
しかなかった。乗車前(呼び止め・配車アプリ・予約)から乗車中(行き先・
道順の指示・車内での依頼)、支払い、トラブル対応までをカバーする新規
domain='タクシー' の語彙と、新規scene='タクシーの英語' のフレーズを追加する。

事前にDB全体(words ~6976件, phrases ~4152件)をダンプし大文字小文字を
無視して重複チェック済み。"taxi stand" "fare" "toll" "detour" "trunk / boot"
"seatbelt" "curb" "driver" "tip" "receipt" "destination" "traffic jam"
"one-way street" "roundabout" "u-turn" "rush hour" は既に別ドメインに
存在するため、本ファイルには含めていない(または "taxi meter" "taxi fare"
のように文脈を限定した複合語に言い換えて重複を回避した)。フレーズも
同様に "Could you call me a taxi?" "How much is the fare?" "Keep the
change." "Could I get a receipt, please?" "Do you take card?" など既存
表現と完全一致しないよう言い回しを変えている。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

words の domain は 'タクシー'、phrases の scene は 'タクシーの英語' で
統一する。level は
["300-","300","350","400","450","500","550","600","650","700","750",
"800","850","900","950","990","990+"] のスケールに沿って付与しており、
乗車時によく使う基本語は300〜600、flag-down fare・ride-hailing app・
dispatch・surge pricingのような専門的/文脈限定の語は650〜800とした。

Run:  python scripts/add_taxi.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- タクシー・運転手の呼び方 ---
    ("taxi", "タクシー", "名詞", "Let's take a taxi to the airport.", "タクシー", "300"),
    ("cab", "タクシー(口語)", "名詞", "He hopped into a cab outside the station.", "タクシー", "400"),
    ("taxi driver", "タクシー運転手", "名詞", "The taxi driver knew a shortcut through downtown.", "タクシー", "350"),
    ("cabbie", "タクシー運転手(口語)", "名詞", "The cabbie chatted with us the whole way to the hotel.", "タクシー", "750"),
    ("taxi rank", "タクシー乗り場(イギリス英語)", "名詞", "There's usually a long line at the taxi rank on Friday nights.", "タクシー", "650"),
    ("black cab", "ブラックキャブ(ロンドンの認可タクシー)", "名詞", "Tourists often ride in a black cab to see London.", "タクシー", "750"),
    ("minicab", "ミニキャブ(事前予約制の私設タクシー・英)", "名詞", "We booked a minicab in advance instead of hailing one on the street.", "タクシー", "800"),
    ("licensed taxi", "認可タクシー", "名詞", "Always use a licensed taxi when traveling in an unfamiliar city.", "タクシー", "750"),
    ("unlicensed cab", "無認可タクシー・白タク", "名詞", "Avoid getting into an unlicensed cab at the airport.", "タクシー", "800"),
    ("airport taxi", "空港タクシー", "名詞", "We took an airport taxi straight to our hotel.", "タクシー", "500"),
    # --- 配車・アプリ ---
    ("ride-hailing app", "配車アプリ", "名詞", "She ordered a car through a ride-hailing app.", "タクシー", "700"),
    ("dispatch", "配車する", "動詞", "The company dispatched a taxi to the hotel within five minutes.", "タクシー", "700"),
    ("ride share", "相乗り・ライドシェア", "名詞", "We used a ride share instead of renting a car.", "タクシー", "650"),
    ("carpool", "相乗り(通勤の)", "名詞", "They carpool to work to save on gas.", "タクシー", "600"),
    # --- 料金・支払い ---
    ("taxi meter", "タクシーメーター", "名詞", "The taxi meter started running as soon as we got in.", "タクシー", "550"),
    ("taxi fare", "タクシー料金", "名詞", "The taxi fare from the airport was higher than expected.", "タクシー", "450"),
    ("flag-down fare", "初乗り運賃", "名詞", "The flag-down fare covers the first kilometer or so.", "タクシー", "800"),
    ("base fare", "基本料金", "名詞", "The base fare doesn't include tolls or extra charges.", "タクシー", "700"),
    ("minimum fare", "最低料金", "名詞", "There's a minimum fare even for very short trips.", "タクシー", "700"),
    ("surcharge", "追加料金", "名詞", "A surcharge applies for large pieces of luggage.", "タクシー", "700"),
    ("late-night surcharge", "深夜割増料金", "名詞", "A late-night surcharge kicks in after midnight.", "タクシー", "800"),
    ("toll road fee", "高速道路料金", "名詞", "The toll road fee will be added to your total fare.", "タクシー", "650"),
    ("luggage fee", "荷物料金", "名詞", "Some taxis charge a small luggage fee for large suitcases.", "タクシー", "650"),
    ("fare estimate", "料金の見積もり", "名詞", "The app gave me a fare estimate before I booked the ride.", "タクシー", "700"),
    ("surge pricing", "需要変動制料金(サージプライシング)", "名詞", "Prices go up during surge pricing on rainy evenings.", "タクシー", "800"),
    ("gratuity", "心付け・チップ", "名詞", "A gratuity is usually appreciated but not required.", "タクシー", "800"),
    # --- 車内・座席 ---
    ("backseat", "後部座席", "名詞", "She sat in the backseat and buckled her seatbelt.", "タクシー", "400"),
    ("front passenger seat", "助手席", "名詞", "He sat in the front passenger seat next to the driver.", "タクシー", "500"),
    ("roof light", "屋根灯(タクシーの空車表示灯)", "名詞", "You can tell a taxi is available by its lit roof light.", "タクシー", "750"),
    # --- 乗降・ルート ---
    ("drop-off point", "降車地点", "名詞", "The drop-off point is right in front of the terminal.", "タクシー", "550"),
    ("pick-up point", "乗車地点", "名詞", "Please meet me at the pick-up point outside the mall.", "タクシー", "550"),
    ("shortest route", "最短ルート", "名詞", "Could you take the shortest route to the station?", "タクシー", "600"),
]

PHRASES: list[tuple[str, str]] = [
    # --- タクシーを呼び止める・乗る ---
    ("Taxi!", "タクシー！"),
    ("Are you free?", "空いていますか？"),
    ("Is this taxi available?", "このタクシーは空車ですか？"),
    ("Could you take me to this address?", "この住所まで連れて行っていただけますか？"),
    ("Could you take me to the airport?", "空港まで連れて行っていただけますか？"),
    # --- 道順の指示 ---
    ("Could you take the highway?", "高速道路を使っていただけますか？"),
    ("Please go straight and turn left at the next light.", "まっすぐ進んで、次の信号を左に曲がってください。"),
    ("Could we avoid the toll road?", "有料道路は避けていただけますか？"),
    ("Is there a faster route?", "もっと早いルートはありますか？"),
    ("Please head toward downtown.", "中心街の方に向かってください。"),
    ("Could you go via Main Street?", "メイン・ストリート経由で行っていただけますか？"),
    # --- 乗車中のリクエスト ---
    ("Could you pull over here?", "ここで停めていただけますか？"),
    ("Could you wait here for a few minutes?", "ここで数分待っていただけますか？"),
    ("Could you turn on the AC?", "エアコンをつけていただけますか？"),
    ("I'm in a bit of a hurry.", "少し急いでいます。"),
    ("Could you roll down the window a little?", "窓を少し開けていただけますか？"),
    ("Could you turn down the radio, please?", "ラジオの音量を下げていただけますか？"),
    # --- 支払い ---
    ("How much will it be?", "おいくらになりますか？"),
    ("Does this taxi take card payment?", "このタクシーはカード払いできますか？"),
    ("Keep the rest.", "残りは取っておいてください。"),
    ("Could I have a receipt for this ride?", "この乗車の領収書をいただけますか？"),
    ("Could you break a fifty?", "50ドル札を崩していただけますか？"),
    ("I only have a card, is that okay?", "カードしか持っていないのですが、大丈夫ですか？"),
    # --- トラブル対応 ---
    ("I think the meter's wrong.", "メーターがおかしいと思います。"),
    ("This isn't the way I expected.", "思っていたルートと違います。"),
    ("I think I left something in the taxi.", "タクシーに忘れ物をしたと思います。"),
    ("Could you slow down, please?", "スピードを落としていただけますか？"),
    ("I don't think this is the shortest way.", "これが最短ルートだとは思えません。"),
    # --- 電話・予約 ---
    ("Could you call a taxi for me?", "私のためにタクシーを呼んでいただけますか？"),
    ("I'd like to book a taxi for 9 AM.", "9時にタクシーを予約したいのですが。"),
    ("How long will it take for the taxi to arrive?", "タクシーが到着するまでどのくらいかかりますか？"),
    ("Could you send a taxi to this address?", "この住所にタクシーを手配していただけますか？"),
]


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

        p_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in p_existing:
                p_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, 'タクシーの英語')",
                (en, ja),
            )
            p_existing.add(en.lower())
            p_added += 1

    print(f"words:   +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
