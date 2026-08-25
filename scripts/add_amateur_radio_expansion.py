# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""既存「アマチュア無線・無線通信」ドメイン(68語)の拡充、authored by
Claude(2026-08-25・ユーザー要望「無線はアマチュア無線用語集、充実略語や
更新用語、機材など。フレーズは、コールサインとか使うフレーズを充実」、
航空管制バッチと対になる無線テーマ第2弾)。

既存語(call sign/Q-code/QSL card/SWR/dipole/Yagi antenna/repeater/
propagation/digital mode/contest/field day等)と重複しない、より専門的な
略語・現行のデジタルモード・アワード制度・伝搬現象・機材語を追加する。
フレーズは新シーン「アマチュア無線の交信」として、コールサインを使った
実際のQSO(交信)の型を多数収録する。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` /
`phrases` tables.

Run:  python scripts/add_amateur_radio_expansion.py
仕上げ: 投入後に `python scripts/relevel.py` と
        `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

HAM = "アマチュア無線・無線通信"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 略語・Qコード等 ---
    ("QRP", "小電力運用(出力を絞って行う運用スタイル、Qコードの一つ)", "名詞", "He enjoys the challenge of making long-distance contacts on QRP power.", HAM, "900"),
    ("QRM", "混信(他局からの人為的な電波による妨害、Qコードの一つ)", "名詞", "Heavy QRM on the band made it hard to copy the weak station.", HAM, "900"),
    ("QRN", "空電雑音(雷などの自然現象による雑音、Qコードの一つ)", "名詞", "Static crashes and QRN got worse as the storm approached.", HAM, "900"),
    ("QSY", "周波数を変更する(Qコードの一つ)", "動詞", "Let's QSY to a clearer frequency and continue the conversation.", HAM, "850"),
    ("QTH", "所在地(現在地を尋ねる/伝えるためのQコード)", "名詞", "\"What's your QTH?\" \"My QTH is Osaka, Japan.\"", HAM, "850"),
    ("73", "さようなら・よろしく(交信終了時に使う伝統的な挨拶の符号)", "名詞", "He signed off the contact with a friendly \"73\".", HAM, "800"),
    ("DXCC", "DXCCアワード(100以上の国・地域と交信したことを証明する権威あるアワード)", "名詞", "After decades on the air, she finally completed DXCC on ten different bands.", HAM, "950"),
    ("POTA", "Parks on the Air(公園などの野外から運用するアクティビティプログラムの略称)", "名詞", "He activated a national park for POTA and logged forty contacts in an hour.", HAM, "900"),
    ("SOTA", "Summits on the Air(山頂から運用するアクティビティプログラムの略称)", "名詞", "Climbing to the summit with a handheld radio is the whole appeal of SOTA.", HAM, "900"),
    ("APRS", "自動位置情報伝送システム(GPS位置情報等を無線で自動送信するシステムの略称)", "名詞", "His APRS beacon let friends track his position during the long drive.", HAM, "900"),
    ("EchoLink", "エコーリンク(インターネット経由でアマチュア無線局同士を接続するシステム)", "名詞", "She used EchoLink to talk with a station on the other side of the world.", HAM, "900"),
    ("D-STAR", "D-STAR(音声とデータを扱うデジタル無線通信規格の一つ)", "名詞", "The club's repeater was upgraded to support D-STAR.", HAM, "900"),
    ("DMR", "デジタル移動無線(Digital Mobile Radioの略、業務用由来のデジタル無線規格)", "名詞", "Many newer handheld radios support both analog FM and DMR.", HAM, "900"),
    ("FT8", "FT8(弱い信号でも交信を成立させやすい人気のデジタル通信モード)", "名詞", "FT8 lets operators make contacts even under very weak signal conditions.", HAM, "900"),
    ("WSJT-X", "WSJT-X(FT8等のデジタルモードで広く使われる無料の通信ソフトウェア)", "名詞", "He downloaded WSJT-X to try FT8 for the first time.", HAM, "900"),
    ("PSK31", "PSK31(キーボードでチャットのようにやり取りできる古参のデジタル通信モード)", "名詞", "Before FT8 became popular, PSK31 was a favorite digital mode for keyboard contacts.", HAM, "900"),
    ("RTTY", "無線テレタイプ(Radio Teletypeの略、古くからあるデジタル通信モード)", "名詞", "RTTY contests remain popular among operators who enjoy the classic digital mode.", HAM, "900"),
    ("ARES", "アマチュア無線非常通信隊(Amateur Radio Emergency Serviceの略称)", "名詞", "Local ARES volunteers provided backup communications during the power outage.", HAM, "900"),
    ("IARU", "国際アマチュア無線連合(各国のアマチュア無線団体を束ねる国際組織)", "名詞", "The IARU coordinates band plans and represents hams at international conferences.", HAM, "900"),
    ("ITU region", "ITUリージョン(国際電気通信連合が世界を3つに分けた周波数管理区分)", "名詞", "Band allocations can differ slightly between ITU regions.", HAM, "950"),
    ("no-code license", "モールス試験免除の免許(モールス符号の実技試験が不要になった現行制度の免許)", "名詞", "Since the code requirement was dropped, getting a no-code license has become much easier.", HAM, "900"),
    # --- 誘導装置・機材 ---
    ("vertical antenna", "垂直アンテナ", "名詞", "A vertical antenna radiates its signal more or less equally in all directions.", HAM, "800"),
    ("beam antenna", "ビームアンテナ(特定方向へ電波を集中させる指向性アンテナ)", "名詞", "Rotating the beam antenna toward Europe improved his signal reports considerably.", HAM, "850"),
    ("ground plane", "グランドプレーン(垂直アンテナの接地面代わりとなるラジアル線の構造)", "名詞", "The ground plane consisted of four radials extending from the base of the antenna.", HAM, "900"),
    ("counterpoise", "カウンターポイズ(接地の代わりとなる導線、アンテナシステムの一部)", "名詞", "He laid out a counterpoise on the ground to improve his portable antenna's performance.", HAM, "950"),
    ("antenna rotor", "アンテナローテーター(指向性アンテナの向きを回転させるモーター装置)", "名詞", "The antenna rotor let him turn the beam toward any direction from his desk.", HAM, "850"),
    ("linear amplifier", "リニアアンプ(送信出力を増幅する装置)", "名詞", "A linear amplifier can boost a signal well beyond the radio's built-in output.", HAM, "900"),
    ("SWR meter", "SWR計(アンテナの整合状態を示す定在波比を測定する計器)", "名詞", "He checked the SWR meter before keying up to make sure the antenna was properly matched.", HAM, "850"),
    ("software defined radio", "ソフトウェア無線(信号処理の多くをソフトウェアで行う無線機の方式)", "名詞", "A software defined radio can be reconfigured for new modes with just a software update.", HAM, "900"),
    ("mesh network (radio)", "メッシュネットワーク(無線局同士が網の目状に相互接続するデータ通信網)", "名詞", "The club set up a mesh network to relay data between several hilltop stations.", HAM, "900"),
    ("balun", "バラン(平衡・不平衡変換を行うアンテナ用の部品)", "名詞", "A balun at the antenna feed point helped reduce unwanted noise on the line.", HAM, "900"),
    ("feed line", "給電線(無線機とアンテナをつなぐケーブル)", "名詞", "Losses in a long feed line can noticeably reduce the power reaching the antenna.", HAM, "800"),
    ("tower (antenna)", "アンテナタワー(大型アンテナを支える鉄塔)", "名詞", "He climbed the tower to adjust the beam antenna at the top.", HAM, "700"),
    ("HT (handheld transceiver)", "ハンディ機(handheld transceiverの略称)", "名詞", "He keeps an HT in his car for emergencies and local nets.", HAM, "800"),
    # --- 伝搬・アワード・運用スタイル ---
    ("sporadic E", "スポラディックE層(短期間に発生し電波を異常に反射させるE層の現象)", "名詞", "A sudden sporadic E opening let him work stations hundreds of miles away on VHF.", HAM, "950"),
    ("meteor scatter", "流星散乱通信(流星が大気中で発生させる電離を利用した通信方式)", "名詞", "Meteor scatter allows brief VHF contacts by bouncing signals off ionized meteor trails.", HAM, "950"),
    ("moonbounce", "月面反射通信(EME、月面に電波を反射させて行う長距離通信)", "名詞", "Moonbounce contacts require a large antenna and very sensitive receiving equipment.", HAM, "950"),
    ("solar flux index", "太陽電波束指数(太陽活動の指標の一つで、電波伝搬状況の目安になる)", "名詞", "A high solar flux index usually means better conditions on the higher HF bands.", HAM, "950"),
    ("skip (propagation)", "スキップ(電波が電離層で反射して遠方まで届く伝搬現象)", "名詞", "Thanks to skip off the ionosphere, his signal reached the other side of the country.", HAM, "850"),
    ("NVIS", "近距離垂直入射伝搬(Near Vertical Incidence Skywaveの略、山間部などでの近距離通信に使われる伝搬方式)", "名詞", "NVIS propagation is especially useful for emergency communications in mountainous terrain.", HAM, "950"),
    ("DXpedition", "DXペディション(電波の届きにくい遠隔地から運用する遠征活動)", "名詞", "The team spent months planning a DXpedition to a remote Pacific island.", HAM, "900"),
    ("pileup", "パイルアップ(珍しい局と交信しようと多くの局が一斉に呼びかける状態)", "名詞", "The rare DX station's pileup grew so large that hundreds of operators were calling at once.", HAM, "900"),
    ("WAS award", "WASアワード(米国50州すべてと交信したことを証明するアワード)", "名詞", "It took her three years to complete her WAS award on the 20-meter band.", HAM, "950"),
    ("IOTA award", "IOTAアワード(世界各地の島から/島と交信・運用したことを証明するアワード)", "名詞", "Chasing the IOTA award took him to some of the rarest islands on the air.", HAM, "950"),
    ("split operation", "スプリット運用(送信と受信で異なる周波数を使う運用方式)", "名詞", "The DX station was working split operation to manage the huge pileup.", HAM, "900"),
    ("fox hunting (radio)", "フォックスハンティング(方向探知の技術を使い隠された送信機を探す競技)", "名詞", "The radio club held a fox hunting event to practice direction-finding skills.", HAM, "900"),
    ("elmering", "エルメリング(経験豊富な局が初心者を指導する慣習、elmerの動名詞形)", "名詞", "Elmering new hams is considered an important tradition in the hobby.", HAM, "900"),
    ("ragchewing", "ラグチューイング(雑談のように長く続ける交信、ragchewの動名詞形)", "名詞", "The two old friends spent an hour ragchewing about their latest antenna projects.", HAM, "900"),
    ("logbook", "運用記録簿(交信内容を記録する台帳)", "名詞", "He carefully entered each contact into his logbook after the contest.", HAM, "700"),
    ("Logbook of The World", "Logbook of The World(交信記録を照合しアワードの証明に使うARRLのオンラインシステム)", "名詞", "Uploading contacts to Logbook of The World made confirming his DXCC award much faster.", HAM, "950"),
]


PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "アマチュア無線の交信": [
        # --- CQを出す・呼応する ---
        ("CQ CQ CQ, this is Kilo Six Alfa Bravo Charlie calling CQ and standing by.", "CQ CQ CQ、こちらK6ABC、CQを送信し応答を待っています。"),
        ("Kilo Six Alfa Bravo Charlie, this is Whiskey One X-ray Yankee Zulu, go ahead.", "K6ABCさん、こちらW1XYZ、どうぞ。"),
        ("Whiskey One X-ray Yankee Zulu, this is Kilo Six Alfa Bravo Charlie, you are five nine, go ahead.", "W1XYZさん、こちらK6ABC、レポートは59です、どうぞ。"),
        ("Is this frequency in use?", "この周波数は使用中ですか。"),
        ("This frequency is in use, please QSY.", "この周波数は使用中です、周波数を変更してください。"),
        ("QRZ? Who's calling?", "QRZ?(誰か呼びましたか?)"),
        ("Station calling, please say your call sign again.", "呼び出し局、コールサインをもう一度お願いします。"),
        ("Break, break, is anyone monitoring this frequency?", "割り込みます、この周波数を聞いている方はいますか。"),
        ("Any station, any station, this is a general call.", "どちらの局でも結構です、一般呼び出しです。"),
        ("I'll listen up five for callers.", "呼び出しは5キロヘルツ上で聞きます。"),
        ("Thanks for the call, you're my first contact today.", "呼んでいただきありがとうございます、本日最初の交信です。"),
        ("Please stand by, I have a station calling.", "少々お待ちください、呼んでいる局がいます。"),
        # --- 信号レポート・コールサインの確認 ---
        ("Your signal report is five nine.", "あなたのレポートは59です。"),
        ("You're five nine plus twenty here.", "こちらでは59プラス20です。"),
        ("I'm only copying you at three by three, it's very weak.", "こちらでは33でしか受信できません、とても弱いです。"),
        ("Please confirm my call sign, it's Juliett Alfa One Alfa Bravo Charlie.", "私のコールサインをご確認ください、JA1ABCです。"),
        ("Copy your call as Juliett Alfa One Alfa Bravo Charlie, is that correct?", "そちらのコールをJA1ABCと受信しましたが、合っていますか。"),
        ("That's affirmative, you copied it correctly.", "その通りです、正しく受信されています。"),
        ("Negative, let me spell it phonetically for you.", "いいえ、フォネティックコードで綴りますね。"),
        ("My call sign is Whiskey One X-ray Yankee Zulu, spelled Whiskey, One, X-ray, Yankee, Zulu.", "私のコールサインはW1XYZ、ウィスキー、1、エックスレイ、ヤンキー、ズールーと綴ります。"),
        ("Your audio is a little distorted, could you back off the microphone?", "音声が少し歪んでいます、マイクを少し離していただけますか。"),
        ("You're clipping a bit, please reduce your gain.", "少し音割れしています、ゲインを下げてください。"),
        # --- QSLカード・アワード関連 ---
        ("Please QSL via the bureau.", "QSLカードはビューローでお願いします。"),
        ("I'll send my QSL card direct with return postage.", "QSLカードは返信用切手を同封して直接お送りします。"),
        ("Do you upload your contacts to Logbook of The World?", "交信記録はLogbook of The Worldにアップロードされていますか。"),
        ("I need your grid square for the log.", "ログに記入するためグリッドスクエアを教えてください。"),
        ("My grid square is PM95.", "私のグリッドスクエアはPM95です。"),
        ("This contact will complete my Worked All States award.", "この交信でWorked All Statesアワードが完成します。"),
        ("Please confirm the QSO details before we sign off.", "終了する前に交信内容を確認させてください。"),
        ("Date, time, frequency, and mode all match my log.", "日付、時刻、周波数、モードともにこちらのログと一致します。"),
        # --- 混信・伝搬状況・機材の話題 ---
        ("There's a lot of QRM on this frequency tonight.", "今夜はこの周波数、混信がひどいですね。"),
        ("Static crashes from the storm are causing heavy QRN.", "嵐による雑音でひどいQRNが発生しています。"),
        ("Propagation has been excellent on twenty meters all week.", "この一週間、20メートルバンドの伝搬状況はとても良好です。"),
        ("We had a nice sporadic E opening on six meters this afternoon.", "今日の午後は6メートルバンドで良いスポラディックE伝搬がありました。"),
        ("What antenna are you running there?", "そちらではどんなアンテナを使っていますか。"),
        ("I'm running a dipole up about thirty feet.", "高さ約30フィートのダイポールアンテナを使っています。"),
        ("What's your power output?", "出力はどのくらいですか。"),
        ("I'm running barefoot, just a hundred watts from the rig.", "アンプなしで、無線機からの100ワットそのままです。"),
        ("He runs QRP, just five watts, and still works the world.", "彼はQRP、わずか5ワットで世界中と交信しています。"),
        ("My SWR is a little high, I need to check the antenna.", "SWRが少し高いので、アンテナを確認する必要があります。"),
        # --- 交信の終了・お礼 ---
        ("Thanks for the QSO, it was a real pleasure.", "交信ありがとうございました、とても楽しかったです。"),
        ("Nice to work you again, hope to catch you next contest.", "また交信できて良かったです、次のコンテストでもお会いしましょう。"),
        ("Thanks for the contact, and 73 to you and your family.", "交信ありがとうございました、あなたとご家族に73(よろしく)。"),
        ("This is Whiskey One X-ray Yankee Zulu, clear and standing by.", "こちらW1XYZ、交信終了、待機します。"),
        ("Seventy-three, and see you down the log.", "73(さようなら)、また交信しましょう。"),
        ("That's all from this end, thanks for the ragchew.", "こちらからは以上です、長話にお付き合いいただきありがとうございました。"),
        ("Good signal both ways, let's make this our last overs.", "双方良好な信号でした、これで最後にしましょう。"),
        ("Station calling, this frequency is closing down, thanks for listening.", "呼び出し局へ、この周波数は終了します、聞いていただきありがとうございました。"),
        # --- 緊急通信・ネット運用 ---
        ("This net is now in session, please check in with your call sign.", "このネットはただいまより開始します、コールサインでチェックインしてください。"),
        ("Net control, this is Kilo Six Alfa Bravo Charlie, checking in.", "ネットコントロール、こちらK6ABC、チェックインします。"),
        ("Any emergency or priority traffic, please call now.", "緊急または優先の通信がある方は今すぐお呼びください。"),
        ("We have emergency traffic, please stand by and keep this frequency clear.", "緊急通信があります、待機してこの周波数を空けておいてください。"),
        ("Relay this message to the county emergency coordinator.", "このメッセージを郡の緊急対策責任者へ中継してください。"),
        ("ARES volunteers are standing by on this repeater for the drill.", "ARESのボランティアが訓練のためこのレピーターで待機しています。"),
        ("Please give your name, location, and equipment when you check in.", "チェックイン時にお名前、所在地、使用機材をお知らせください。"),
        ("Net control will now close the net, thanks everyone for checking in.", "ネットコントロールがただいまよりネットを終了します、チェックインいただきありがとうございました。"),
        # --- コンテスト・レピーター運用 ---
        ("This is a contest exchange: five nine and my grid square.", "コンテストの交換情報です、59とグリッドスクエアです。"),
        ("What's your exchange for this contest?", "このコンテストの交換情報は何ですか。"),
        ("I need a multiplier from your state for the contest.", "コンテストのため、そちらの州のマルチプライヤーが必要です。"),
        ("Kilo Six Alfa Bravo Charlie is listening on the repeater input.", "K6ABCはレピーターの入力周波数を聞いています。"),
        ("What's the repeater offset and tone for this machine?", "このレピーターのオフセットとトーンは何ですか。"),
        ("The offset is minus six hundred with a tone of one hundred point zero.", "オフセットはマイナス600、トーンは100.0です。"),
        ("Please identify with your call sign every ten minutes.", "10分ごとにコールサインで局を識別してください。"),
        ("This repeater is open, feel free to join the conversation.", "このレピーターはオープンです、会話にご自由にご参加ください。"),
        # --- ライセンス・機材の相談 ---
        ("I just upgraded to my General class license.", "先日ジェネラルクラスの免許にアップグレードしました。"),
        ("Congratulations on passing your Technician exam.", "テクニシャン試験合格おめでとうございます。"),
        ("My elmer helped me put up my first antenna.", "私のエルマー(指導役)が最初のアンテナ設置を手伝ってくれました。"),
        ("Would you recommend a good HT for a new operator?", "初心者向けに良いハンディ機を教えていただけますか。"),
        ("I'm thinking about trying FT8 for the first time this weekend.", "今週末、初めてFT8に挑戦しようと思っています。"),
        ("Let's set up a schedule to try meteor scatter next month.", "来月、流星散乱通信を試すためスケジュールを組みましょう。"),
        ("Field day is coming up, are you setting up a station this year?", "フィールドデーが近づいていますが、今年は局を設営しますか。"),
        ("I activated a summit for SOTA and logged twenty contacts.", "SOTAのため山頂から運用し、20交信をログしました。"),
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
