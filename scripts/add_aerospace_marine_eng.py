# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""Two engineering topics: 宇宙工学/航空工学(space & aeronautical
engineering — top up the existing 航空・宇宙 domain)／海洋工学(ocean/marine
engineering — new domain), authored by Claude (2026-08-05・ユーザー要望:
「宇宙工学　航空工学　海洋工学…増やしましょうか」＋「質は落とさないよう
に、段階的に実装ください」).

既存の「航空・宇宙」(63語)は飛行運用・空港・宇宙飛行士の実務語が中心
だったので、機体・ロケット・衛星の設計工学語彙を補強する。「海洋工学」は
既存の「船舶」(43語・帆船から現代船舶までの一般的な航海・船体語)とは別に、
海洋構造物・浮体工学・水中探査といった工学分野として新設した。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words`
table.

Run:  python scripts/add_aerospace_marine_eng.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

AEROSPACE = "航空・宇宙"
MARINE = "海洋工学"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 航空工学・宇宙工学（既存ドメインに追加） ---
    ("wind tunnel", "風洞", "名詞", "Engineers test a scale model in a wind tunnel before building the real aircraft.", AEROSPACE, "750"),
    ("lift-to-drag ratio", "揚抗比", "名詞", "A higher lift-to-drag ratio lets a glider travel farther without power.", AEROSPACE, "900"),
    ("hypersonic", "極超音速の", "形容詞", "A hypersonic vehicle travels at more than five times the speed of sound.", AEROSPACE, "850"),
    ("ramjet", "ラムジェットエンジン", "名詞", "A ramjet has no moving parts and only works once it is already moving fast.", AEROSPACE, "900"),
    ("solid rocket motor", "固体燃料ロケットモーター", "名詞", "A solid rocket motor cannot be shut off once it has been ignited.", AEROSPACE, "900"),
    ("liquid propellant", "液体燃料", "名詞", "Liquid propellant gives engineers finer control over a rocket's thrust.", AEROSPACE, "900"),
    ("cryogenic fuel", "極低温燃料", "名詞", "Cryogenic fuel must be kept at extremely low temperatures to stay liquid.", AEROSPACE, "900"),
    ("delta-v", "デルタV（速度変化量）", "名詞", "The mission needed extra delta-v to slow down and enter orbit.", AEROSPACE, "950"),
    ("orbital mechanics", "軌道力学", "名詞", "Orbital mechanics determines exactly when a spacecraft must fire its engines.", AEROSPACE, "900"),
    ("geostationary orbit", "静止軌道", "名詞", "A satellite in geostationary orbit stays above the same point on Earth.", AEROSPACE, "850"),
    ("low Earth orbit", "低軌道（低地球軌道）", "名詞", "The space station orbits in low Earth orbit, just a few hundred kilometers up.", AEROSPACE, "800"),
    ("payload fairing", "ペイロードフェアリング（衛星カバー）", "名詞", "The payload fairing protects the satellite as the rocket climbs through the atmosphere.", AEROSPACE, "900"),
    ("heat shield", "耐熱シールド", "名詞", "The capsule's heat shield glowed red hot as it reentered the atmosphere.", AEROSPACE, "800"),
    ("solar array", "太陽電池パネル（衛星の）", "名詞", "The satellite unfolded its solar array shortly after reaching orbit.", AEROSPACE, "800"),
    ("attitude control", "姿勢制御", "名詞", "Attitude control keeps the spacecraft pointed in exactly the right direction.", AEROSPACE, "900"),
    ("gyroscope", "ジャイロスコープ", "名詞", "A gyroscope helps the aircraft's instruments sense how it is turning.", AEROSPACE, "800"),
    ("space debris", "スペースデブリ", "名詞", "Space debris from old satellites poses a growing risk to new missions.", AEROSPACE, "800"),
    ("launch window", "発射可能時間帯・打ち上げウインドウ", "名詞", "The mission has a launch window of only a few minutes each day.", AEROSPACE, "850"),
    ("abort system", "緊急脱出システム", "名詞", "The abort system can pull the crew capsule away from a failing rocket.", AEROSPACE, "900"),
    ("reusable rocket", "再使用型ロケット", "名詞", "A reusable rocket lands itself so it can fly again on a future mission.", AEROSPACE, "800"),
    ("stage separation", "段分離", "名詞", "Stage separation drops the empty first stage once its fuel is used up.", AEROSPACE, "900"),
    ("flutter (aerodynamics)", "フラッター（空気力学的振動）", "名詞", "Flutter can tear a wing apart if it is not damped correctly.", AEROSPACE, "950"),
    ("wing loading", "翼面荷重", "名詞", "A lower wing loading lets an aircraft turn more tightly.", AEROSPACE, "900"),
    ("composite airframe", "複合材製の機体", "名詞", "A composite airframe is lighter and stronger than an equivalent aluminum one.", AEROSPACE, "850"),
    ("payload capacity", "ペイロード容量・搭載可能重量", "名詞", "The rocket's payload capacity determines how heavy a satellite it can carry.", AEROSPACE, "800"),
    # --- 海洋工学（新設） ---
    ("naval architecture", "造船工学・船体設計", "名詞", "Naval architecture combines physics, materials science, and design to build safe ships.", MARINE, "850"),
    ("offshore platform", "海洋プラットフォーム", "名詞", "The offshore platform pumps oil from beneath the seabed.", MARINE, "800"),
    ("ballast tank", "バラストタンク", "名詞", "Filling the ballast tank with water helps keep the ship stable.", MARINE, "800"),
    ("buoyancy", "浮力", "名詞", "Buoyancy keeps the ship afloat even when it is fully loaded with cargo.", MARINE, "700"),
    ("displacement (ship)", "排水量（船の）", "名詞", "The tanker's displacement is measured by the weight of water it pushes aside.", MARINE, "850"),
    ("draft (ship depth)", "喫水", "名詞", "The ship's draft was too deep to enter the shallow harbor.", MARINE, "800"),
    ("freeboard", "フリーボード（乾舷）", "名詞", "Freeboard is the distance between the waterline and the deck of the ship.", MARINE, "900"),
    ("ship stability", "船の復原性", "名詞", "Ship stability engineers calculate how far a vessel can lean before it capsizes.", MARINE, "850"),
    ("cathodic protection", "電気防食", "名詞", "Cathodic protection uses a small electric current to stop the steel hull from rusting.", MARINE, "950"),
    ("remotely operated vehicle (ROV)", "遠隔操作型無人潜水機（ROV）", "名詞", "A remotely operated vehicle inspected the pipeline on the seabed.", MARINE, "850"),
    ("submersible", "潜水艇", "名詞", "The submersible carried three researchers down to the ocean floor.", MARINE, "800"),
    ("subsea pipeline", "海底パイプライン", "名詞", "The subsea pipeline carries natural gas from the platform to the coast.", MARINE, "850"),
    ("mooring system", "係留システム", "名詞", "The mooring system keeps the floating platform in place against strong currents.", MARINE, "900"),
    ("wave energy converter", "波力発電装置", "名詞", "A wave energy converter turns the motion of the ocean into electricity.", MARINE, "900"),
    ("tidal power", "潮力発電", "名詞", "Tidal power generates electricity from the rise and fall of the sea.", MARINE, "800"),
    ("seabed survey", "海底調査", "名詞", "A seabed survey mapped the ocean floor before the cable was laid.", MARINE, "850"),
    ("dredging", "しんせつ・海底掘削", "名詞", "Dredging deepened the channel so larger ships could enter the port.", MARINE, "800"),
    ("breakwater", "防波堤", "名詞", "The breakwater absorbs most of the wave energy before it reaches the harbor.", MARINE, "800"),
    ("dry dock", "ドライドック", "名詞", "The ship was moved into a dry dock so its hull could be repainted.", MARINE, "750"),
    ("shipbuilding", "造船", "名詞", "Shipbuilding has been one of the country's major industries for a century.", MARINE, "650"),
    ("classification society", "船級協会", "名詞", "A classification society inspects the ship and certifies that it meets safety standards.", MARINE, "900"),
    ("load line", "満載喫水線", "名詞", "The load line marked on the hull shows how deep the ship may safely sit.", MARINE, "900"),
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
