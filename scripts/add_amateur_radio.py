# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a new domain covering AMATEUR (HAM) RADIO and general two-way RADIO
COMMUNICATION PROCEDURE vocabulary, authored by Claude (2026-08-04・ユーザー
要望:「無線用語 アマチュア無線用語も追加ですね」).

既存語彙には amateur radio, radio telescope, radioactive, radioactive waste,
radioactivity など「radio」を含む語がいくつか散在するだけで、無線通信を
専門に扱う語彙ドメインは存在しなかった。また既存の一般語彙には antenna,
callsign / call sign, channel, dipole, frequency band, modulation, packet,
propagation, repeater, squelch, transmitter, receiver といった語がすでに
別ドメインで登録されている（電気電子/物理/ネットワークなど汎用語として）
ため、本スクリプトではそれらの裸の単語は追加せず、"repeater offset",
"dipole antenna", "radio propagation", "squelch level", "packet radio",
"radio channel" のような、より具体的でアマチュア無線特有の複合語に置き換
えて重複を避けている。

フレーズ側にも既存シーン「無線」(12件・一般的な無線手順)と「モータース
ポーツ・無線交信」(18件・F1ピット無線)がすでに存在するため、新規シーン
「無線通信の英語」では、それらと文字列が重複しないアマチュア無線的な
フレーズ（ネット運用、QSL、ラグチューなど）を中心に追加した。

対象は2領域:
  1) アマチュア無線の趣味語彙 (callsign文化, 機材, 運用, ライセンスなど)
  2) 航空・モータースポーツ・海事・一般業務無線にも通じる無線交信の
     プロトコル/手順語彙 (フォネティックコード, roger/over/out など)

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased), checked
independently against the `words` and `phrases` tables.

Run:  python scripts/add_amateur_radio.py
仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "アマチュア無線・無線通信"
SCENE = "無線通信の英語"

# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 1) アマチュア無線の趣味語彙 ---
    ("ham radio operator", "アマチュア無線家・ハム", "名詞", "My uncle has been a licensed ham radio operator for over twenty years.", DOMAIN, "500"),
    ("transceiver", "トランシーバー(送受信機)", "名詞", "He upgraded his old transceiver to a newer model with digital modes.", DOMAIN, "550"),
    ("repeater offset", "レピーターオフセット(送受信周波数の差)", "名詞句", "You need to set the correct repeater offset before you can access that machine.", DOMAIN, "800"),
    ("DX", "DX、遠距離交信", "名詞", "Working DX on the HF bands is one of the most exciting parts of the hobby.", DOMAIN, "800"),
    ("QSL card", "QSLカード(交信確認カード)", "名詞句", "She mailed a QSL card to confirm the contact with a station in Japan.", DOMAIN, "800"),
    ("band plan", "バンドプラン(周波数帯の利用計画)", "名詞句", "Check the band plan before you transmit near the edge of the segment.", DOMAIN, "750"),
    ("HF", "HF、短波帯", "名詞", "HF signals can travel thousands of miles by bouncing off the ionosphere.", DOMAIN, "700"),
    ("VHF", "VHF、超短波帯", "名詞", "Local repeaters are usually found on the VHF and UHF bands.", DOMAIN, "700"),
    ("UHF", "UHF、極超短波帯", "名詞", "UHF handhelds are popular for short-range communication around town.", DOMAIN, "700"),
    ("radio propagation", "電波伝搬", "名詞句", "Radio propagation changes a lot depending on the time of day and solar activity.", DOMAIN, "800"),
    ("dipole antenna", "ダイポールアンテナ", "名詞句", "He strung a simple dipole antenna between two trees in his backyard.", DOMAIN, "700"),
    ("Yagi antenna", "八木アンテナ", "名詞句", "A Yagi antenna on the roof really improved his signal strength.", DOMAIN, "750"),
    ("SWR", "SWR、定在波比", "名詞", "A high SWR reading usually means something is wrong with your antenna or feedline.", DOMAIN, "850"),
    ("squelch level", "スケルチレベル", "名詞句", "Turn down the squelch level a bit so you can hear the weaker stations.", DOMAIN, "800"),
    ("AM/FM/SSB", "AM・FM・SSB(変調方式)", "名詞句", "Most HF voice contacts use SSB rather than AM or FM.", DOMAIN, "750"),
    ("Morse code", "モールス信号", "名詞句", "Learning Morse code is still required for some amateur radio license classes abroad.", DOMAIN, "600"),
    ("CW", "CW、連続波(モールス通信)", "名詞", "He prefers CW because he can make contacts even with very low power.", DOMAIN, "800"),
    ("net", "ネット(定時交信の集まり)", "名詞", "The local ham club holds a net every Tuesday evening on the repeater.", DOMAIN, "700"),
    ("ragchew", "ラグチュー(気楽な雑談交信)", "名詞", "After the contest, they settled into a long ragchew about antenna projects.", DOMAIN, "850"),
    ("contest", "コンテスト(アマチュア無線の交信数を競うイベント)", "名詞", "He stayed up all weekend chasing contacts during the contest.", DOMAIN, "700"),
    ("grid square", "グリッドスクエア(位置を表す区画)", "名詞句", "Tell me your grid square so I can log the contact correctly.", DOMAIN, "850"),
    ("license class", "免許クラス", "名詞句", "Passing the exam let him upgrade to a higher license class with more privileges.", DOMAIN, "700"),
    ("elmer", "エルマー(初心者を指導する先輩無線家)", "名詞", "My elmer taught me how to solder my first antenna connector.", DOMAIN, "850"),
    ("rig", "リグ(無線機の俗称)", "名詞", "What kind of rig are you running from your car?", DOMAIN, "650"),
    ("shack", "シャック(無線室)", "名詞", "He spends most weekends in his shack chasing new countries on the air.", DOMAIN, "650"),
    ("field day", "フィールドデー(野外運用イベント)", "名詞句", "Our club sets up portable stations in the park for field day every June.", DOMAIN, "700"),
    ("emergency communications", "非常通信", "名詞句", "Many hams volunteer for emergency communications during natural disasters.", DOMAIN, "750"),
    ("digital mode", "デジタルモード", "名詞句", "This digital mode lets you make contacts even when the band is very noisy.", DOMAIN, "750"),
    ("packet radio", "パケット無線", "名詞句", "Packet radio was one of the earliest ways hams sent data over the air.", DOMAIN, "800"),
    ("coax cable", "同軸ケーブル", "名詞句", "Use good quality coax cable to reduce signal loss between the radio and the antenna.", DOMAIN, "650"),
    ("antenna tuner", "アンテナチューナー", "名詞句", "An antenna tuner can help match an imperfect antenna to the radio.", DOMAIN, "750"),
    ("dummy load", "ダミーロード(疑似負荷)", "名詞句", "Always test your transmitter into a dummy load before connecting the real antenna.", DOMAIN, "850"),
    ("sunspot cycle", "黒点周期", "名詞句", "The sunspot cycle has a big effect on how far HF signals can travel.", DOMAIN, "850"),
    ("portable operation", "移動運用", "名詞句", "He enjoys portable operation from mountaintops with just a battery and a small antenna.", DOMAIN, "700"),
    # --- 2) 無線交信のプロトコル/手順語彙 ---
    ("phonetic alphabet", "フォネティックコード(通話表)", "名詞句", "Pilots and hams both use a phonetic alphabet to spell out letters clearly.", DOMAIN, "550"),
    ("NATO alphabet", "NATOフォネティックコード", "名詞句", "The NATO alphabet uses words like Alpha, Bravo, and Charlie for each letter.", DOMAIN, "550"),
    ("roger", "ラジャー、了解", "間投詞", "Roger, I copy your last message.", DOMAIN, "400"),
    ("copy that", "了解、受信しました", "間投詞", "Copy that, we'll meet at the checkpoint at noon.", DOMAIN, "400"),
    ("over", "どうぞ(送信終わり、応答を求める合図)", "間投詞", "The weather here is clear, over.", DOMAIN, "400"),
    ("out", "通信終わり", "間投詞", "Message received, out.", DOMAIN, "400"),
    ("wilco", "了解し実行します", "間投詞", "Wilco, we'll change course immediately.", DOMAIN, "550"),
    ("say again", "もう一度お願いします", "動詞句", "Say again, your last transmission was garbled.", DOMAIN, "450"),
    ("standing by", "待機しています", "動詞句", "Standing by for further instructions.", DOMAIN, "450"),
    ("break, break", "ブレイク、ブレイク(緊急時の割り込み合図)", "間投詞", "Break, break, we have an emergency on the trail.", DOMAIN, "700"),
    ("radio check", "無線チェック(感度確認)", "名詞句", "Radio check, how do you copy?", DOMAIN, "450"),
    ("come in", "応答してください", "動詞句", "Come in, base, this is unit three.", DOMAIN, "450"),
    ("squelch break", "スケルチブレイク(短い送信で割り込む合図)", "名詞句", "He gave a quick squelch break to let the net control know he was listening.", DOMAIN, "850"),
    ("push-to-talk", "プッシュトゥトーク(送信ボタン)", "名詞句", "Hold down the push-to-talk button while you're speaking.", DOMAIN, "600"),
    ("PTT", "PTT、送信ボタン", "名詞", "Release the PTT as soon as you finish talking.", DOMAIN, "600"),
    ("Q-code", "Qコード(通信用の略号)", "名詞句", "Hams still use Q-code abbreviations like QRM and QSY on the air.", DOMAIN, "800"),
    ("transmit", "送信する", "動詞", "Do not transmit until the frequency is clear.", DOMAIN, "500"),
    ("receive", "受信する", "動詞", "This radio can transmit and receive on the same frequency.", DOMAIN, "450"),
    ("radio channel", "無線チャンネル", "名詞句", "Switch to radio channel five for the rest of the event.", DOMAIN, "450"),
    ("dead air", "デッドエア(無音状態)", "名詞句", "There were several seconds of dead air before he finally answered.", DOMAIN, "750"),
    ("cross-talk", "クロストーク(混信)", "名詞", "Cross-talk from a nearby station made it hard to understand him.", DOMAIN, "800"),
    ("read you loud and clear", "はっきり聞こえています", "動詞句", "I read you loud and clear, go ahead.", DOMAIN, "500"),
    ("garbled transmission", "不明瞭な送信(内容が聞き取れない)", "名詞句", "Static caused a garbled transmission that nobody could understand.", DOMAIN, "750"),
    ("base station", "基地局", "名詞句", "The base station can reach handhelds up to ten miles away.", DOMAIN, "600"),
    ("mobile station", "移動局", "名詞句", "He operates a mobile station from his car during long road trips.", DOMAIN, "650"),
    ("walkie-talkie", "トランシーバー(携帯型の無線機)", "名詞", "The kids used walkie-talkies to stay in touch while hiking.", DOMAIN, "400"),
    ("two-way radio", "双方向無線機", "名詞句", "Event staff carried two-way radios to coordinate the schedule.", DOMAIN, "450"),
]


# --- phrases: (english, japanese), all under SCENE --------------------------

PHRASES: list[tuple[str, str]] = [
    ("Radio check, how do you copy?", "無線チェック、感度はいかがですか？"),
    ("Copy that, standing by.", "了解、待機します。"),
    ("This is base, go ahead.", "こちらベース、どうぞ。"),
    ("Roger, out.", "了解、通信終わります。"),
    ("Say again, you're breaking up.", "もう一度お願いします、電波が途切れています。"),
    ("Wilco, will comply.", "了解、指示に従います。"),
    ("Come in, do you read me?", "応答願います、聞こえますか？"),
    ("Break, break, this is an emergency.", "ブレイク、ブレイク、緊急事態です。"),
    ("Over and out.", "送信終わり、これで通信終了です。"),
    ("Switch to the repeater on two meters.", "2メートル帯のレピーターに切り替えて。"),
    ("Give me a signal report.", "シグナルレポートをください。"),
    ("You're five by five.", "感度良好、はっきり聞こえています。"),
    ("Let's move to a clear frequency.", "空いている周波数に移りましょう。"),
    ("I'm going to key up now.", "今から送信します。"),
    ("Hold your traffic, we have priority.", "送信を控えてください、優先通信があります。"),
    ("That's a Roger.", "了解しました。"),
    ("Negative, say again.", "違います、もう一度お願いします。"),
    ("Break for a new station joining the net.", "ネットに新しく参加する局のためブレイクします。"),
    ("QSL, I copy your last transmission.", "QSL、直前の送信を受信しました。"),
    ("Let's do a quick net check-in.", "手早くネットのチェックインをしましょう。"),
    ("This net is now open for check-ins.", "このネットはただいまチェックイン受付中です。"),
    ("73, see you on the next net.", "73(挨拶)、また次のネットで。"),
    ("Please keep your transmissions short.", "送信は短めにお願いします。"),
    ("We're experiencing some QRM on this frequency.", "この周波数はQRM(混信)が発生しています。"),
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

        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        ph_added = ph_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in ph_existing:
                ph_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) VALUES (?, ?, ?)",
                (en, ja, SCENE),
            )
            ph_existing.add(en.lower())
            ph_added += 1

    print(f"words:   +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
