# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a new 車載組込み開発 (automotive / in-vehicle embedded development)
domain, authored by Claude (2026-08-04・ユーザー要望「車載開発用語。hils sils
mils他ですね」).

ユーザーは組込み系エンジニアであり、この分野は生成AIの一般的な語彙補完ではなく
実務精度が求められる。カバー範囲:
  1. V字モデル/シミュレーション・テストレベル（MILS/SILS/HILS/PILS,
     requirement traceability, back-to-back testing, fault injection testing 等）
  2. 車載ネットワーク・プロトコル（CAN/LIN/FlexRay/車載Ethernet, DTC, OBD-II,
     UDS 等）
  3. 機能安全・規格（ISO 26262, ASIL, FMEA, redundancy, watchdog timer 等）
  4. ECU/ファームウェア開発（AUTOSAR, BSW, RTOS, cross-compilation,
     board support package 等）
  5. 車両システム文脈（ADAS, drive-by-wire, telematics, OTA, torque/actuator
     の車載文脈での使い方等）

既存語彙との重複チェック実施済み（実行前に data/vocabulary.db を SELECT で確認）。
以下は既に他ドメインに存在するため本ファイルには含めていない:
  flash memory, EEPROM, torque, actuator, firmware, sensor, interrupt,
  embedded, bootloader, calibrate, real-time
（"sensor fusion" "sensor signal" "torque" と紛らわしい語は車載文脈の複合語
  として書き分けている: sensor fusion, sensor signal は残し、単体の
  "actuator"・"torque" は既存語と衝突するため省いた。）

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_automotive_embedded.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "車載組込み開発"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 1. V字モデル / シミュレーション・テストレベル ---
    ("V-model", "V字モデル（要件定義からテストまでを対応付けて進める開発プロセス）", "名詞", "Our development process follows the V-model, from requirements down to system test.", DOMAIN, "700"),
    ("MILS", "MILS（モデルインザループシミュレーション：制御モデルをPC上で検証する手法）", "名詞", "We validate the control logic in MILS before any code is generated.", DOMAIN, "850"),
    ("SILS", "SILS（ソフトウェアインザループシミュレーション：生成後のコードをPC上で検証する手法）", "名詞", "The generated code passed all the SILS test cases yesterday.", DOMAIN, "850"),
    ("HILS", "HILS（ハードウェアインザループシミュレーション：実ECUを模擬環境で検証する手法）", "名詞", "Can we run this on the HILS bench before we test it in the actual vehicle?", DOMAIN, "800"),
    ("PILS", "PILS（プロセッサインザループシミュレーション：実プロセッサ上でコードを検証する手法）", "名詞", "PILS testing showed a timing difference that never appeared in SILS.", DOMAIN, "950"),
    ("requirement traceability", "要求トレーサビリティ（要求から設計・テストまでの対応関係を追跡できること）", "名詞", "The safety auditor asked us to demonstrate requirement traceability from the hazard analysis to the test cases.", DOMAIN, "800"),
    ("unit test level", "単体テストレベル", "名詞", "This bug should have been caught at the unit test level.", DOMAIN, "700"),
    ("integration test level", "結合テストレベル", "名詞", "The two modules worked fine alone but failed at the integration test level.", DOMAIN, "700"),
    ("system test level", "システムテストレベル", "名詞", "We're seeing intermittent failures only at the system test level.", DOMAIN, "700"),
    ("acceptance test", "受け入れテスト", "名詞", "The customer will run their own acceptance test before sign-off.", DOMAIN, "650"),
    ("back-to-back testing", "バックトゥバックテスト（モデルと実装、または旧版と新版の出力を突き合わせて検証する手法）", "名詞", "We found the root cause during back-to-back testing between the model and the generated code.", DOMAIN, "850"),
    ("fault injection testing", "フォールト注入テスト（意図的に故障を発生させて安全機構を検証する手法）", "名詞", "Fault injection testing confirmed the ECU enters a safe state when the sensor signal is lost.", DOMAIN, "850"),
    # --- 2. 車載ネットワーク・プロトコル ---
    ("CAN bus", "CANバス（車載ネットワークの標準的な通信バス）", "名詞", "The instrument cluster reads vehicle speed from the CAN bus.", DOMAIN, "700"),
    ("CAN frame", "CANフレーム（CANバス上を流れるデータの単位）", "名詞", "Let's check the CAN trace for the frame that was sent right before the fault occurred.", DOMAIN, "750"),
    ("LIN bus", "LINバス（低コストな車載ネットワークで、CANより低速な補助的通信に使われる）", "名詞", "The window motor is controlled over a LIN bus, not the main CAN bus.", DOMAIN, "800"),
    ("FlexRay", "FlexRay（高速かつ確定的な通信を保証する車載ネットワーク規格）", "名詞", "FlexRay was chosen for the chassis domain because it guarantees deterministic timing.", DOMAIN, "900"),
    ("automotive Ethernet", "車載イーサネット（大容量データ通信向けの車載ネットワーク規格）", "名詞", "The camera streams raw video to the ADAS unit over automotive Ethernet.", DOMAIN, "850"),
    ("gateway ECU", "ゲートウェイECU（複数の車載ネットワークを中継・変換する制御ユニット）", "名詞", "The gateway ECU routes diagnostic requests from OBD-II to the correct network segment.", DOMAIN, "800"),
    ("in-vehicle network", "車載ネットワーク", "名詞", "The in-vehicle network connects dozens of ECUs across several buses.", DOMAIN, "700"),
    ("diagnostic trouble code", "故障診断コード（DTC）", "名詞", "The scan tool showed a diagnostic trouble code for the oxygen sensor circuit.", DOMAIN, "700"),
    ("DTC", "DTC（故障診断コードの略）", "名詞", "Clear the DTC and see if it comes back after the drive cycle.", DOMAIN, "750"),
    ("OBD-II", "OBD-II（車両の自己診断・故障情報を外部から読み取るための標準規格）", "名詞", "You can read live sensor data through the OBD-II port.", DOMAIN, "700"),
    ("UDS", "UDS（統合診断サービス：車載ECUの診断通信を定めた標準プロトコル）", "名詞", "We use UDS services to flash new calibration data onto the ECU.", DOMAIN, "850"),
    ("CAN ID", "CAN ID（CANメッセージを識別するための番号で、優先度も兼ねる）", "名詞", "Two suppliers accidentally used the same CAN ID, so the messages kept colliding.", DOMAIN, "800"),
    ("bus load", "バス負荷（通信バスの使用率）", "名詞", "Adding the new sensor pushed the bus load above eighty percent.", DOMAIN, "800"),
    ("network topology", "ネットワークトポロジー（車載ネットワークの接続構成）", "名詞", "The new network topology adds a dedicated bus just for the ADAS sensors.", DOMAIN, "800"),
    # --- 3. 機能安全・規格 ---
    ("ISO 26262", "ISO 26262（自動車の機能安全に関する国際規格）", "名詞", "This project must comply with ISO 26262 because it controls the brakes.", DOMAIN, "800"),
    ("ASIL", "ASIL（自動車安全水準：ISO 26262で定義されるリスクの深刻度に応じた等級）", "名詞", "What's the ASIL rating for this function?", DOMAIN, "800"),
    ("functional safety", "機能安全", "名詞", "The functional safety team reviewed our design before we started coding.", DOMAIN, "750"),
    ("fail-safe", "フェールセーフ（故障時に安全な状態へ移行する設計）", "形容詞", "Is this a fail-safe or fail-operational requirement?", DOMAIN, "750"),
    ("fail-operational", "フェールオペレーショナル（故障時も機能を継続できる設計）", "形容詞", "A fail-operational system needs redundant actuators, not just a safe shutdown.", DOMAIN, "850"),
    ("safety goal", "安全目標（ハザード分析から導かれる最上位の安全要求）", "名詞", "The safety goal states that unintended acceleration shall not occur.", DOMAIN, "800"),
    ("hazard analysis", "ハザード分析（危険事象を洗い出し、リスクを評価する活動）", "名詞", "We reran the hazard analysis after the new sensor was added to the design.", DOMAIN, "800"),
    ("FMEA", "FMEA（故障モード影響解析：起こりうる故障とその影響を体系的に洗い出す手法）", "名詞", "The FMEA flagged the connector as a single point of failure.", DOMAIN, "800"),
    ("redundancy", "冗長性（同じ機能を複数系統で持たせること）", "名詞", "We added redundancy on the sensor line to meet the ASIL D requirement.", DOMAIN, "700"),
    ("watchdog timer", "ウォッチドッグタイマー（ソフトウェアの異常を検知してリセットする監視回路）", "名詞", "The watchdog timer reset the ECU unexpectedly during the overnight soak test.", DOMAIN, "750"),
    ("safe state", "安全状態（故障発生時に遷移する、リスクを最小化した状態）", "名詞", "When communication is lost, the actuator moves to its safe state.", DOMAIN, "750"),
    # --- 4. ECU/ファームウェア開発 ---
    ("ECU", "ECU（電子制御ユニット）", "名詞", "The ECU needs to be reflashed with the latest calibration.", DOMAIN, "650"),
    ("ECU flashing", "ECUフラッシング（ECUに新しいソフトウェアを書き込む作業）", "名詞", "ECU flashing takes about ten minutes over the diagnostic connector.", DOMAIN, "750"),
    ("calibration data", "適合データ（制御パラメータのデータセット）", "名詞", "We loaded the updated calibration data before starting the cold start test.", DOMAIN, "750"),
    ("A2L file", "A2Lファイル（適合・測定用の変数情報を記述するファイル）", "名詞", "Make sure the A2L file matches this software build exactly, or the labels won't line up.", DOMAIN, "950"),
    ("RTOS", "RTOS（リアルタイムオペレーティングシステム）", "名詞", "The RTOS guarantees this task runs within a fixed time budget.", DOMAIN, "800"),
    ("task scheduling", "タスクスケジューリング（複数の処理をどの順序・タイミングで実行するかの制御）", "名詞", "Poor task scheduling caused the higher-priority interrupt to be delayed.", DOMAIN, "750"),
    ("interrupt latency", "割り込みレイテンシ（割り込み発生からハンドラ実行開始までの遅延）", "名詞", "The interrupt latency spiked whenever the logging task was running.", DOMAIN, "800"),
    ("memory footprint", "メモリフットプリント（プログラムが消費するメモリ量）", "名詞", "Adding that library nearly doubled our memory footprint.", DOMAIN, "700"),
    ("AUTOSAR", "AUTOSAR（車載ソフトウェアの標準アーキテクチャ）", "名詞", "This project's basic software is generated from an AUTOSAR configuration tool.", DOMAIN, "800"),
    ("basic software", "ベーシックソフトウェア（AUTOSARにおけるハードウェア寄りの共通ソフトウェア層）", "名詞", "The basic software handles the CAN driver and diagnostic stack.", DOMAIN, "800"),
    ("application software layer", "アプリケーションソフトウェア層（車両機能のロジックを実装する上位層）", "名詞", "The application software layer shouldn't need to know which microcontroller it's running on.", DOMAIN, "800"),
    ("hardware abstraction layer", "ハードウェア抽象化層（上位ソフトウェアをハードウェア差異から切り離す層）", "名詞", "Porting to the new microcontroller was easy because everything went through the hardware abstraction layer.", DOMAIN, "800"),
    ("board support package", "ボードサポートパッケージ（特定のハードウェア向けの基本ドライバ・起動コード一式）", "名詞", "The supplier delivered a board support package along with the evaluation board.", DOMAIN, "850"),
    ("cross-compilation", "クロスコンパイル（開発PC上で、別のターゲット向けの実行コードを生成すること）", "名詞", "We use cross-compilation to build code on Windows that runs on the ARM target.", DOMAIN, "800"),
    ("target hardware", "ターゲットハードウェア（実際にソフトウェアを動かす実機）", "名詞", "It works fine on the simulator but hasn't been verified on the target hardware yet.", DOMAIN, "700"),
    ("bench test", "ベンチテスト（車両に搭載せず、机上の治具・実機構成で行う試験）", "名詞", "Let's do a bench test first before we install this on the mule vehicle.", DOMAIN, "700"),
    ("in-vehicle test", "車両搭載試験（実車に組み込んで行う試験）", "名詞", "The last remaining issue only shows up during the in-vehicle test.", DOMAIN, "700"),
    ("cold start test", "コールドスタート試験（低温状態からの始動試験）", "名詞", "The cold start test is scheduled for the climate chamber next week.", DOMAIN, "750"),
    ("key-on/key-off cycle", "キーオン・キーオフサイクル（イグニッションのオン・オフを繰り返す試験サイクル）", "名詞", "We ran a thousand key-on/key-off cycles to check for wake-up failures.", DOMAIN, "850"),
    # --- 5. 車両システム文脈 ---
    ("powertrain", "パワートレイン（エンジン・モーターから駆動輪までの動力伝達系）", "名詞", "The powertrain team owns the torque request interface.", DOMAIN, "700"),
    ("chassis control", "シャシー制御（ブレーキ・ステアリング・サスペンションなど車両挙動の制御）", "名詞", "Chassis control and powertrain control exchange vehicle speed over the CAN bus.", DOMAIN, "750"),
    ("body control module", "ボディ制御モジュール（ドア・ライト・パワーウィンドウ等を統括するECU）", "名詞", "The body control module handles everything from the door locks to the interior lighting.", DOMAIN, "750"),
    ("ADAS", "ADAS（先進運転支援システム）", "名詞", "The ADAS camera lost tracking of the lane markings in heavy rain.", DOMAIN, "750"),
    ("sensor fusion", "センサーフュージョン（複数のセンサー情報を統合して認識精度を高める処理）", "名詞", "Sensor fusion combines the radar and camera data to reduce false detections.", DOMAIN, "800"),
    ("drive-by-wire", "ドライブバイワイヤ（機械的なリンクではなく電子制御で駆動系を操作する方式）", "名詞", "There's no mechanical throttle cable at all — it's fully drive-by-wire.", DOMAIN, "800"),
    ("brake-by-wire", "ブレーキバイワイヤ（機械的・油圧的なリンクではなく電子制御でブレーキを操作する方式）", "名詞", "Brake-by-wire systems need a fail-operational backup path.", DOMAIN, "850"),
    ("telematics", "テレマティクス（車両の通信・位置情報などを活用するシステム）", "名詞", "The telematics unit uploads mileage and fault data over the cellular network.", DOMAIN, "750"),
    ("over-the-air update", "OTAアップデート（無線通信を通じてソフトウェアを更新すること）", "名詞", "The infotainment bug was fixed with an over-the-air update, no dealer visit required.", DOMAIN, "750"),
    ("OTA", "OTA（over-the-air updateの略）", "名詞", "This ECU isn't OTA-capable yet, so it still needs a cable at the dealer.", DOMAIN, "750"),
    ("infotainment system", "インフォテインメントシステム（車内の情報・娯楽機能を統合したシステム）", "名詞", "The infotainment system froze during the software update.", DOMAIN, "700"),
    ("sensor signal", "センサー信号", "名詞", "The ECU enters a safe state whenever the sensor signal drops out.", DOMAIN, "650"),
    ("closed-loop control", "閉ループ制御（出力を測定してフィードバックし、目標値との差を補正する制御方式）", "名詞", "The throttle position is regulated with closed-loop control.", DOMAIN, "750"),
    ("open-loop control", "開ループ制御（フィードバックを用いず、あらかじめ決めた指令のみで動かす制御方式）", "名詞", "During the cold start, the fuel injection briefly runs in open-loop control.", DOMAIN, "750"),
]

PHRASES: list[tuple[str, str]] = [
    ("Can we run this on the HILS bench first?", "まずHILSベンチで実行できますか？"),
    ("What's the ASIL rating for this function?", "この機能のASIL格付けは何ですか？"),
    ("Let's check the CAN trace for that error frame.", "そのエラーフレームのCANトレースを確認しましょう。"),
    ("The ECU needs to be reflashed with the latest calibration.", "ECUに最新の適合データを再書き込みする必要があります。"),
    ("Is this a fail-safe or fail-operational requirement?", "これはフェールセーフ要求ですか、それともフェールオペレーショナル要求ですか？"),
    ("We found the root cause during back-to-back testing.", "バックトゥバックテストで根本原因が見つかりました。"),
    ("The watchdog timer reset the ECU unexpectedly.", "ウォッチドッグタイマーが予期せずECUをリセットしました。"),
    ("Can you share the A2L file for this build?", "このビルド用のA2Lファイルを共有していただけますか？"),
    ("We're seeing bus-off errors on the CAN network.", "CANネットワークでバスオフエラーが発生しています。"),
    ("Let's move this test case from SILS to HILS.", "このテストケースをSILSからHILSへ移しましょう。"),
    ("What's causing the interrupt latency spike?", "この割り込みレイテンシのスパイクの原因は何でしょうか？"),
    ("The DTC cleared itself after the next drive cycle.", "次のドライブサイクル後にDTCは自動的に消えました。"),
    ("Can you pull the fault code with the OBD-II scanner?", "OBD-IIスキャナーで故障コードを読み出してもらえますか？"),
    ("We need to update the requirement traceability matrix.", "要求トレーサビリティマトリクスを更新する必要があります。"),
    ("This issue only shows up in the in-vehicle test, not on the bench.", "この問題は車両搭載試験でのみ発生し、ベンチでは再現しません。"),
    ("Let's schedule a cold start test in the climate chamber.", "恒温槽でコールドスタート試験を予定しましょう。"),
    ("The gateway ECU is dropping messages under high bus load.", "ゲートウェイECUがバス負荷の高い状況でメッセージを取りこぼしています。"),
    ("Could you send over the latest AUTOSAR configuration?", "最新のAUTOSAR設定を送っていただけますか？"),
    ("We're cross-compiling for the target hardware this afternoon.", "今日の午後、ターゲットハードウェア向けにクロスコンパイルします。"),
    ("The safety goal wasn't fully covered by the current test cases.", "現在のテストケースでは安全目標が十分にカバーされていませんでした。"),
    ("Let's run an FMEA on the new sensor architecture.", "新しいセンサー構成についてFMEAを実施しましょう。"),
    ("Is the redundant actuator wired to a separate power supply?", "冗長側のアクチュエータは別系統の電源に接続されていますか？"),
    ("We can push this fix out as an over-the-air update.", "この修正はOTAアップデートで配信できます。"),
    ("Let's check whether it's still in open-loop control at that point.", "その時点でまだ開ループ制御のままかどうか確認しましょう。"),
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
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, '車載組込み開発の英語')",
                (en, ja),
            )
            ph_existing.add(en.lower())
            ph_added += 1

    print(f"words: +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
