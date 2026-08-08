# ruff: noqa: E501
"""「組み込み開発」「車載開発」拡充＋新設「自動車産業」ドメイン追加(2026-08-09)。

ユーザー要望: 「車載組み込み開発は→組み込み開発・車載開発用語・自動車
産業とし、それぞれ適切に分類し単語、フレーズ拡張しましょう。例えば
組み込み開発はブート・ブートローダー・フラッシュROM・ジャンプ・揮発性
メモリ・不揮発性メモリ・GPIO・割込・ベクターテーブル他」。

既存語の再分類は`split_automotive_embedded_2026_08_09.py`で実施済み
(車載組込み開発109語→組み込み開発55語+車載開発54語)。本スクリプトは
その3ドメイン(組み込み開発/車載開発/自動車産業=新設)へ新規語彙・
フレーズを追加する。

Run:  python scripts/add_embedded_automotive_expand_2026_08_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# (english, japanese, part_of_speech, example, domain, level)
WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 組み込み開発（一般） ---
    ("boot", "起動する・ブート", "動詞", "The device takes about three seconds to boot.", "組み込み開発", "450"),
    ("flash ROM", "フラッシュROM（書き換え可能な不揮発性メモリ）", "名詞", "The firmware is stored in flash ROM so it survives a power cycle.", "組み込み開発", "550"),
    ("jump", "ジャンプする（プログラムカウンタを別のアドレスへ移すこと）", "動詞", "The bootloader jumps to the application's entry point once the checksum passes.", "組み込み開発", "550"),
    ("vector table", "ベクターテーブル（割り込み・例外ごとのハンドラアドレスを並べた表）", "名詞", "Each interrupt has its own entry in the vector table.", "組み込み開発", "700"),
    ("embedded system", "組込みシステム", "名詞", "An embedded system is a computer built into a larger device to perform a specific task.", "組み込み開発", "500"),
    ("peripheral", "周辺機器・周辺回路（マイコンに内蔵/接続されるI/O機能）", "名詞", "The microcontroller has several built-in peripherals, including timers and ADCs.", "組み込み開発", "550"),
    ("heap", "ヒープ（動的に確保されるメモリ領域）", "名詞", "Allocating too much memory on the heap can fragment it over time.", "組み込み開発", "600"),
    ("endianness", "エンディアン（マルチバイトデータのバイト順）", "名詞", "Little-endian and big-endian systems store multi-byte values in opposite byte order.", "組み込み開発", "700"),
    ("memory map", "メモリマップ（アドレス空間の割り当て一覧）", "名詞", "Check the memory map to see which address range the peripheral registers occupy.", "組み込み開発", "650"),
    ("crystal oscillator", "水晶発振子", "名詞", "A crystal oscillator provides the stable clock signal the microcontroller needs.", "組み込み開発", "650"),
    ("power-on reset", "パワーオンリセット（電源投入時の初期化リセット）", "名詞", "A power-on reset ensures the chip starts from a known state every time.", "組み込み開発", "650"),
    ("brown-out reset", "ブラウンアウトリセット（電圧低下を検知して行うリセット）", "名詞", "A brown-out reset protects the chip from misbehaving during a voltage dip.", "組み込み開発", "700"),
    ("stack pointer", "スタックポインタ", "名詞", "The stack pointer keeps track of the top of the call stack.", "組み込み開発", "600"),
    ("ADC", "ADC（アナログ・デジタル変換器）", "名詞", "The ADC converts the sensor's analog voltage into a digital value the CPU can read.", "組み込み開発", "550"),
    ("DAC", "DAC（デジタル・アナログ変換器）", "名詞", "A DAC turns the digital audio signal back into an analog waveform.", "組み込み開発", "600"),
    # --- 車載開発 ---
    ("start-stop system", "アイドリングストップシステム", "名詞", "The start-stop system shuts off the engine automatically at red lights.", "車載開発", "600"),
    ("adaptive cruise control", "アダプティブクルーズコントロール（先行車との車間を自動調整する追従走行機能）", "名詞", "Adaptive cruise control slows the car down automatically when traffic ahead brakes.", "車載開発", "650"),
    ("lane keep assist", "レーンキープアシスト（車線逸脱を防ぐ操舵支援機能）", "名詞", "Lane keep assist gently steers the car back if it starts to drift out of its lane.", "車載開発", "650"),
    ("blind spot monitoring", "ブラインドスポットモニター（死角検知）", "名詞", "Blind spot monitoring warns the driver before they change lanes into another vehicle.", "車載開発", "650"),
    ("parking sensor", "パーキングセンサー", "名詞", "The parking sensor beeps faster as the car gets closer to the wall.", "車載開発", "500"),
    ("tire pressure monitoring system", "タイヤ空気圧監視システム（TPMS）", "名詞", "The tire pressure monitoring system alerted her to a slow leak.", "車載開発", "650"),
    ("immobilizer", "イモビライザー（盗難防止用のエンジン始動制御装置）", "名詞", "The immobilizer prevents the engine from starting without the correct key chip.", "車載開発", "700"),
    ("keyless entry system", "キーレスエントリーシステム", "名詞", "The keyless entry system unlocks the doors as soon as you touch the handle.", "車載開発", "550"),
    ("electronic stability control", "横滑り防止装置（ESC）", "名詞", "Electronic stability control automatically applies individual brakes to prevent a skid.", "車載開発", "700"),
    ("anti-lock braking system", "アンチロックブレーキシステム（ABS）", "名詞", "The anti-lock braking system pulses the brakes to prevent the wheels from locking up.", "車載開発", "600"),
    ("traction control", "トラクションコントロール（駆動輪の空転を防ぐ制御）", "名詞", "Traction control reduces engine power when a wheel starts to spin on ice.", "車載開発", "650"),
    ("regenerative braking", "回生ブレーキ", "名詞", "Regenerative braking recovers energy that would otherwise be lost as heat.", "車載開発", "650"),
    ("battery management system", "バッテリーマネジメントシステム（BMS）", "名詞", "The battery management system monitors each cell to prevent overcharging.", "車載開発", "700"),
    ("inverter", "インバーター（直流と交流を変換する電力変換装置）", "名詞", "The inverter converts the battery's DC power into AC power for the motor.", "車載開発", "650"),
    ("motor controller", "モーターコントローラー", "名詞", "The motor controller adjusts current to the electric motor based on the accelerator input.", "車載開発", "700"),
    ("zonal architecture", "ゾーンアーキテクチャ（車両を機能ではなく物理区画ごとに制御する電子アーキテクチャ）", "名詞", "Zonal architecture replaces dozens of individual ECUs with a few powerful zone controllers.", "車載開発", "800"),
    ("domain controller", "ドメインコントローラー（複数の関連機能をまとめて処理する高性能ECU）", "名詞", "A single domain controller now handles all the functions that used to need several separate ECUs.", "車載開発", "750"),
    ("software-defined vehicle", "ソフトウェア定義車両（SDV）", "名詞", "A software-defined vehicle can gain new features through updates long after it leaves the factory.", "車載開発", "750"),
    ("vehicle-to-everything", "V2X（車車間・路車間通信）", "名詞", "Vehicle-to-everything communication lets cars warn each other about hazards ahead.", "車載開発", "750"),
    ("event data recorder", "イベントデータレコーダー（自動車のブラックボックス）", "名詞", "The event data recorder captured the car's speed just before the collision.", "車載開発", "700"),
    # --- 自動車産業（新設ドメイン） ---
    ("automaker", "自動車メーカー", "名詞", "The automaker announced a new electric SUV for next year.", "自動車産業", "450"),
    ("assembly line", "組立ライン", "名詞", "Workers on the assembly line install one part every few seconds.", "自動車産業", "500"),
    ("supply chain", "サプライチェーン", "名詞", "A single supplier's shutdown disrupted the entire supply chain.", "自動車産業", "550"),
    ("Tier 1 supplier", "ティア1サプライヤー（完成車メーカーに直接部品を納入する一次請け企業）", "名詞", "A Tier 1 supplier delivers complete subsystems directly to the automaker.", "自動車産業", "650"),
    ("Tier 2 supplier", "ティア2サプライヤー（Tier1にさらに部品を供給する二次請け企業）", "名詞", "A Tier 2 supplier often makes individual components that a Tier 1 supplier assembles.", "自動車産業", "700"),
    ("OEM", "相手先ブランド製造（自動車業界では完成車メーカー自体を指すことも多い）", "名詞", "In the auto industry, OEM often just means the vehicle manufacturer itself.", "自動車産業", "600"),
    ("just-in-time manufacturing", "ジャストインタイム生産方式", "名詞", "Just-in-time manufacturing keeps inventory low by delivering parts exactly when needed.", "自動車産業", "700"),
    ("recall", "リコール", "名詞", "The automaker issued a recall over a faulty airbag sensor.", "自動車産業", "500"),
    ("homologation", "型式認証（各国の基準への適合確認手続き）", "名詞", "The car had to pass homologation in each country before it could go on sale.", "自動車産業", "800"),
    ("crash test", "衝突試験", "名詞", "The vehicle earned a five-star rating in the crash test.", "自動車産業", "500"),
    ("emissions standard", "排出ガス基準", "名詞", "New emissions standards are pushing automakers toward electric vehicles.", "自動車産業", "600"),
    ("electric vehicle", "電気自動車（EV）", "名詞", "Sales of electric vehicles have grown rapidly over the past decade.", "自動車産業", "450"),
    ("hybrid vehicle", "ハイブリッド車", "名詞", "A hybrid vehicle combines a gasoline engine with an electric motor.", "自動車産業", "450"),
    ("plug-in hybrid", "プラグインハイブリッド車", "名詞", "A plug-in hybrid can be charged from an outlet and driven short distances on electricity alone.", "自動車産業", "550"),
    ("fuel cell vehicle", "燃料電池車", "名詞", "A fuel cell vehicle generates electricity from hydrogen instead of storing it in a battery.", "自動車産業", "650"),
    ("internal combustion engine", "内燃機関", "名詞", "Many automakers are gradually phasing out the internal combustion engine.", "自動車産業", "550"),
    ("charging station", "充電ステーション", "名詞", "The number of public charging stations has increased sharply in recent years.", "自動車産業", "450"),
    ("range anxiety", "航続距離不安（EVの充電切れへの不安）", "名詞", "Range anxiety is one of the biggest concerns for first-time EV buyers.", "自動車産業", "650"),
    ("autonomous driving", "自動運転", "名詞", "Autonomous driving technology is being tested on public roads in several cities.", "自動車産業", "500"),
    ("self-driving car", "自動運転車", "名詞", "A self-driving car uses cameras, radar, and sensors to navigate without a human driver.", "自動車産業", "500"),
    ("driving automation level", "運転自動化レベル", "名詞", "SAE defines six driving automation levels, from zero to full automation.", "自動車産業", "700"),
    ("dealership", "ディーラー（販売店）", "名詞", "She test-drove three cars at the dealership before making a decision.", "自動車産業", "500"),
    ("trade-in", "下取り", "名詞", "He got a good price for his trade-in when he bought the new car.", "自動車産業", "550"),
    ("lease", "リース契約", "名詞", "Many drivers prefer a lease over buying because the monthly payment is lower.", "自動車産業", "550"),
    ("warranty", "保証（保証書）", "名詞", "The car comes with a five-year warranty on the powertrain.", "自動車産業", "500"),
    ("model year", "モデルイヤー（年式）", "名詞", "The dealership was clearing out the previous model year to make room for new inventory.", "自動車産業", "600"),
    ("facelift", "マイナーチェンジ（外観を中心とした改良）", "名詞", "The sedan received a facelift with a new front grille and headlights.", "自動車産業", "650"),
    ("platform", "シャシー・プラットフォーム（複数車種で共有される基本設計）", "名詞", "Several different models are built on the same platform to save development costs.", "自動車産業", "600"),
    ("badge engineering", "バッジエンジニアリング（基本設計を共有し外装や名称だけ変えて複数ブランドで販売すること）", "名詞", "Badge engineering lets automakers sell nearly identical cars under different brand names.", "自動車産業", "750"),
    ("production capacity", "生産能力", "名詞", "The new factory doubled the company's production capacity.", "自動車産業", "550"),
    ("vehicle inventory", "在庫車両", "名詞", "Rising interest rates left dealers with more vehicle inventory than usual.", "自動車産業", "600"),
    ("residual value", "残存価値（リース終了時等に想定される車両の価値）", "名詞", "Cars with a high residual value tend to have lower lease payments.", "自動車産業", "700"),
    ("total cost of ownership", "総所有コスト（TCO）", "名詞", "The total cost of ownership includes fuel, insurance, and maintenance, not just the sticker price.", "自動車産業", "700"),
    ("automotive supplier", "自動車部品サプライヤー", "名詞", "The strike at the automotive supplier delayed production at three factories.", "自動車産業", "550"),
    ("powertrain electrification", "パワートレインの電動化", "名詞", "Powertrain electrification is reshaping which suppliers automakers rely on.", "自動車産業", "750"),
    ("platform sharing", "プラットフォーム共用", "名詞", "Platform sharing across brands is one of the biggest ways automakers cut costs.", "自動車産業", "700"),
]

# --- phrases: scene -> [(english, japanese)] --------------------------------

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "組み込み開発の英語": [
        ("The device won't boot after the last firmware update.", "前回のファームウェア更新後、デバイスが起動しなくなりました。"),
        ("Let's check the vector table for that fault handler.", "その障害ハンドラについてベクターテーブルを確認しましょう。"),
        ("We're running low on heap space.", "ヒープ領域の残りが少なくなっています。"),
        ("Double check the memory map before you write to that address.", "そのアドレスに書き込む前にメモリマップを確認してください。"),
        ("The crystal oscillator might be out of spec.", "水晶発振子が規格外になっているかもしれません。"),
        ("Is this platform little-endian or big-endian?", "このプラットフォームはリトルエンディアンですか、それともビッグエンディアンですか。"),
        ("The stack pointer got corrupted somehow.", "スタックポインタが何らかの原因で壊れてしまいました。"),
        ("Read the ADC value and convert it to voltage.", "ADCの値を読み取り、電圧に変換してください。"),
    ],
    "車載開発の英語": [
        ("The lane keep assist kept nudging the wheel on the highway.", "高速道路でレーンキープアシストが何度もハンドルを補正していました。"),
        ("Adaptive cruise control makes long highway drives much less tiring.", "アダプティブクルーズコントロールのおかげで長距離の高速道路運転がずっと楽になります。"),
        ("The immobilizer won't let the engine start without the right key.", "イモビライザーが正しいキーでないとエンジンを始動させません。"),
        ("Regenerative braking is why EVs feel different when you lift off the accelerator.", "回生ブレーキがあるからこそ、EVはアクセルを離したときの感覚が違います。"),
        ("The battery management system shut down the pack to prevent overheating.", "バッテリーマネジメントシステムが過熱を防ぐためにバッテリーパックを停止させました。"),
        ("This model finally moves to a zonal architecture instead of dozens of separate ECUs.", "この車種はついに個別のECUを大量に積む方式からゾーンアーキテクチャへ移行しました。"),
        ("The car can now receive new features through software updates, just like a smartphone.", "この車はスマートフォンのように、ソフトウェア更新で新機能を追加できるようになりました。"),
        ("Pull the data from the event data recorder to see what happened before the crash.", "衝突前に何が起きたか確認するため、イベントデータレコーダーからデータを取り出してください。"),
    ],
    "自動車産業の英語": [
        ("What's the fuel economy on this model?", "この車の燃費はどのくらいですか。"),
        ("Does this trim come with adaptive cruise control?", "このグレードにはアダプティブクルーズコントロールは付いていますか。"),
        ("How long is the warranty on the battery?", "バッテリーの保証期間はどのくらいですか。"),
        ("We're offering a great trade-in value this month.", "今月は下取り価格がとてもお得です。"),
        ("Would you like to lease or finance this vehicle?", "この車はリースにしますか、それともローンにしますか。"),
        ("The automaker recalled thousands of vehicles over a brake defect.", "その自動車メーカーはブレーキの不具合で数千台をリコールしました。"),
        ("Chip shortages forced several automakers to slow production.", "半導体不足により複数の自動車メーカーが生産を減速させました。"),
        ("The company is investing billions in electric vehicle production.", "その企業は電気自動車の生産に数十億ドルを投資しています。"),
        ("Range anxiety is still holding back some EV buyers.", "航続距離への不安が一部のEV購入希望者をためらわせています。"),
        ("The new model shares its platform with two other cars in the lineup.", "この新型車はラインナップの他の2車種とプラットフォームを共有しています。"),
        ("This plant runs on a just-in-time manufacturing system.", "この工場はジャストインタイム生産方式で稼働しています。"),
        ("Homologation delays pushed the launch back by six months.", "型式認証の遅れにより発売が半年延期されました。"),
        ("The car earned a top score in independent crash tests.", "その車は第三者機関の衝突試験で最高評価を獲得しました。"),
        ("Stricter emissions standards are reshaping the whole industry.", "より厳しい排出ガス基準が業界全体を作り変えつつあります。"),
        ("The dealership offered a loaner car while mine was in for service.", "点検の間、ディーラーが代車を用意してくれました。"),
        ("This is the last model year before the redesign.", "これは新型に切り替わる前の最後のモデルイヤーです。"),
        ("The sedan just got a facelift with new headlights.", "そのセダンは新しいヘッドライトを備えたマイナーチェンジを受けました。"),
        ("Total cost of ownership matters more than the sticker price alone.", "車両価格だけでなく総所有コストの方が重要です。"),
        ("The plant's production capacity will double next year.", "その工場の生産能力は来年倍増する予定です。"),
        ("Level 3 autonomous driving is now legal on certain highways.", "レベル3の自動運転は一部の高速道路で合法になりました。"),
    ],
}


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
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

    print(f"words: +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    with db() as conn:
        for d in ["組み込み開発", "車載開発", "自動車産業"]:
            print(d, "words:",
                  conn.execute("SELECT COUNT(*) FROM words WHERE domain=?", (d,)).fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
