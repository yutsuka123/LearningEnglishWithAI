# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""自動車工学(新設)＋熱工学/燃焼工学/流体工学の深掘り語（既存の「機械工学」
に追加）, authored by Claude (2026-08-05・ユーザー要望:「自動車工学…熱工学
　燃焼工学　流体工学…増やしましょうか」＋「質は落とさないように、段階的
に実装ください」).

調査の結果、既存の「機械工学」(162語)には既に thermal engineering/control
engineering/combustion/combustion chamber/internal combustion engine/
laminar flow/turbulent flow/viscosity/Reynolds number/Bernoulli's
principle/heat transfer/thermal conductivity 等、熱工学・燃焼工学・流体
工学の基礎語が広く含まれていた。よって3分野は**新規ドメインを作らず**、
まだ無い一段深い語彙だけを機械工学に追加する。自動車工学は逆に
「車載組込み開発」(70語=組込みソフト中心)にも「機械工学」にも自動車固有
の機構語(transmission/suspension/brake system等)が無かったため新設した。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words`
table.

Run:  python scripts/add_automotive_thermal_fluid_eng.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

AUTO = "自動車工学"
MECH = "機械工学"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 自動車工学（新設） ---
    ("transmission (automotive)", "トランスミッション・変速機", "名詞", "The transmission shifts automatically as the car speeds up.", AUTO, "600"),
    ("manual transmission", "マニュアルトランスミッション（MT）", "名詞", "A manual transmission requires the driver to shift gears by hand.", AUTO, "650"),
    ("automatic transmission", "オートマチックトランスミッション（AT）", "名詞", "Most new cars sold today come with an automatic transmission.", AUTO, "600"),
    ("differential (automotive)", "デファレンシャル・差動装置", "名詞", "The differential lets the two rear wheels turn at slightly different speeds.", AUTO, "800"),
    ("drivetrain", "ドライブトレイン・動力伝達系", "名詞", "The drivetrain carries power from the engine all the way to the wheels.", AUTO, "750"),
    ("all-wheel drive", "四輪駆動（AWD）", "名詞", "All-wheel drive sends power to all four wheels for better grip in snow.", AUTO, "700"),
    ("chassis", "シャシー・車台", "名詞", "The chassis forms the structural frame that everything else is built on.", AUTO, "700"),
    ("suspension (automotive)", "サスペンション・懸架装置", "名詞", "A good suspension absorbs bumps without making the ride feel soft.", AUTO, "650"),
    ("shock absorber", "ショックアブソーバー", "名詞", "Worn shock absorbers make the car bounce after every bump.", AUTO, "700"),
    ("brake system", "ブレーキシステム", "名詞", "The brake system must be inspected regularly for safety.", AUTO, "550"),
    ("disc brake", "ディスクブレーキ", "名詞", "A disc brake squeezes a pad against a spinning metal disc to slow the wheel.", AUTO, "700"),
    ("anti-lock braking system (ABS)", "アンチロックブレーキシステム（ABS）", "名詞", "The anti-lock braking system pulses the brakes to keep the tires from skidding.", AUTO, "750"),
    ("clutch", "クラッチ", "名詞", "The clutch disconnects the engine from the wheels while you change gears.", AUTO, "700"),
    ("turbocharger", "ターボチャージャー", "名詞", "A turbocharger uses exhaust gas to force more air into the engine.", AUTO, "800"),
    ("supercharger", "スーパーチャージャー", "名詞", "Unlike a turbocharger, a supercharger is driven directly by the engine's belt.", AUTO, "850"),
    ("fuel injection", "燃料噴射", "名詞", "Fuel injection sprays a precise amount of fuel directly into each cylinder.", AUTO, "750"),
    ("spark plug", "スパークプラグ・点火プラグ", "名詞", "A worn spark plug can make the engine misfire.", AUTO, "700"),
    ("cylinder head", "シリンダーヘッド", "名詞", "The cylinder head sits on top of the engine block and holds the valves.", AUTO, "800"),
    ("timing belt", "タイミングベルト", "名詞", "The timing belt keeps the camshaft and crankshaft rotating in perfect sync.", AUTO, "800"),
    ("catalytic converter", "触媒コンバーター", "名詞", "A catalytic converter reduces the harmful gases in the exhaust.", AUTO, "800"),
    ("electric vehicle battery", "電気自動車用バッテリー", "名詞", "The electric vehicle battery takes several hours to charge fully at home.", AUTO, "700"),
    ("regenerative braking", "回生ブレーキ", "名詞", "Regenerative braking recovers energy that would otherwise be lost as heat.", AUTO, "850"),
    ("crash test", "衝突試験", "名詞", "Every new model must pass a strict government crash test.", AUTO, "650"),
    ("airbag", "エアバッグ", "名詞", "The airbag deployed instantly in the front-end collision.", AUTO, "600"),
    ("wheel alignment", "ホイールアライメント", "名詞", "Poor wheel alignment causes a tire to wear unevenly.", AUTO, "800"),
    ("tire tread", "タイヤの溝・トレッド", "名詞", "Worn tire tread makes it harder to grip the road in the rain.", AUTO, "700"),
    ("odometer", "オドメーター・距離計", "名詞", "The odometer showed just over a hundred thousand kilometers.", AUTO, "650"),
    ("dashboard warning light", "ダッシュボードの警告灯", "名詞", "A dashboard warning light came on as soon as the engine started.", AUTO, "600"),
    # --- 熱工学・燃焼工学・流体工学（既存「機械工学」に追加） ---
    ("adiabatic process", "断熱過程", "名詞", "In an adiabatic process, no heat enters or leaves the system.", MECH, "950"),
    ("isothermal process", "等温過程", "名詞", "An isothermal process keeps the temperature constant while pressure and volume change.", MECH, "950"),
    ("entropy", "エントロピー", "名詞", "Entropy always increases in an isolated system over time.", MECH, "900"),
    ("Carnot cycle", "カルノーサイクル", "名詞", "No real engine can be more efficient than the theoretical Carnot cycle.", MECH, "950"),
    ("heat exchanger", "熱交換器", "名詞", "A heat exchanger transfers heat from the hot exhaust to the cooler intake air.", MECH, "850"),
    ("radiator (cooling)", "ラジエーター（冷却装置）", "名詞", "The radiator keeps the engine from overheating on a hot day.", MECH, "600"),
    ("Mach number", "マッハ数", "名詞", "A Mach number greater than one means the object is flying faster than sound.", MECH, "900"),
    ("cavitation", "キャビテーション", "名詞", "Cavitation can damage a pump's blades when bubbles collapse violently.", MECH, "950"),
    ("vortex", "渦・ボルテックス", "名詞", "A vortex forms behind the wing tip as the aircraft flies.", MECH, "800"),
    ("centrifugal pump", "遠心ポンプ", "名詞", "A centrifugal pump spins water outward using a rotating impeller.", MECH, "850"),
    ("venturi effect", "ベンチュリ効果", "名詞", "The venturi effect speeds up a fluid as the pipe narrows.", MECH, "900"),
    ("choked flow", "チョークド・フロー（臨界流）", "名詞", "Once the flow becomes choked, increasing the pressure further has no effect on its speed.", MECH, "950"),
    ("ignition timing", "点火タイミング", "名詞", "Adjusting the ignition timing can improve both power and fuel efficiency.", MECH, "850"),
    ("engine knock", "エンジンノック", "名詞", "Engine knock happens when fuel ignites unevenly inside the cylinder.", MECH, "850"),
    ("octane rating", "オクタン数", "名詞", "A higher octane rating resists knocking better under high compression.", MECH, "800"),
    ("flame front", "火炎面", "名詞", "The flame front spreads outward from the spark until all the fuel has burned.", MECH, "900"),
    ("afterburner", "アフターバーナー", "名詞", "An afterburner injects extra fuel into the exhaust for a burst of thrust.", MECH, "900"),
    ("thermal efficiency", "熱効率", "名詞", "A diesel engine generally has a higher thermal efficiency than a gasoline one.", MECH, "850"),
    ("heat sink", "ヒートシンク", "名詞", "A heat sink draws heat away from the chip and releases it into the air.", MECH, "750"),
    ("insulating material", "断熱材", "名詞", "An insulating material slows the flow of heat through the wall.", MECH, "700"),
]


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
