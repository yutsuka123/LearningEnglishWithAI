# ruff: noqa: E501
"""物理ドメインの本格拡充(2026-08-09)。

ユーザー要望: 「物理は量子物理学・原子・素粒子他用語追加。電磁波・ガンマ線・
X線他追加。電磁気学・マックスウェルの方程式他追加。主な方程式・定理を
追加。熱力学の法則他追加。相対性理論関係追加」。

既存の`物理`domainは量子力学・素粒子物理の専門語(Lagrangian/Hamiltonian/
Higgs boson/quark/neutrino等)が既にかなり充実していたため、既存語を
精査した上で**未登録のものだけ**を追加する: 電磁波の種類(X線・紫外線・
赤外線・電波等)、マクスウェルの方程式/ガウスの法則/アンペールの法則、
熱力学第零法則・第三法則、相対性理論の主要概念(ローレンツ収縮・双子の
パラドックス・測地線等)、ニュートンの運動の三法則・保存則等の基礎的な
「主な方程式・定理」。

No app / OpenAI API calls — hand-written。Duplicates skipped by english
(lowercased)。

Run:  python scripts/add_physics_deep_2026_08_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "物理"

# (english, japanese, part_of_speech, example, level)
WORDS: list[tuple[str, str, str, str, str]] = [
    ("tau", "タウ粒子（タウレプトン）", "名詞", "The tau is the heaviest of the three charged leptons.", "800"),
    ("x-ray", "エックス線", "名詞", "Doctors used an x-ray to check for a broken bone.", "450"),
    ("ultraviolet", "紫外線", "名詞", "Ultraviolet light can cause sunburn after long exposure.", "500"),
    ("infrared", "赤外線", "名詞", "Infrared cameras can detect heat even in complete darkness.", "500"),
    ("radio wave", "電波", "名詞", "Radio waves carry signals to your car's radio.", "450"),
    ("electromagnetic spectrum", "電磁スペクトル", "名詞", "Visible light is just a small part of the electromagnetic spectrum.", "650"),
    ("electromagnetic wave", "電磁波", "名詞", "Light itself is a type of electromagnetic wave.", "600"),
    ("Maxwell's equations", "マクスウェルの方程式", "名詞", "Maxwell's equations unify electricity, magnetism, and light into a single theory.", "850"),
    ("Gauss's law", "ガウスの法則", "名詞", "Gauss's law relates the electric flux through a closed surface to the charge it encloses.", "850"),
    ("Ampere's law", "アンペールの法則", "名詞", "Ampere's law relates a magnetic field to the electric current that produces it.", "850"),
    ("zeroth law of thermodynamics", "熱力学第零法則", "名詞", "The zeroth law of thermodynamics defines what it means for two systems to be in thermal equilibrium.", "800"),
    ("third law of thermodynamics", "熱力学第三法則", "名詞", "The third law of thermodynamics states that entropy approaches zero as temperature approaches absolute zero.", "800"),
    ("absolute zero", "絶対零度", "名詞", "Absolute zero is the coldest temperature theoretically possible.", "600"),
    ("length contraction", "ローレンツ収縮（長さの収縮）", "名詞", "Length contraction causes a fast-moving object to appear shorter along its direction of motion.", "800"),
    ("mass-energy equivalence", "質量とエネルギーの等価性", "名詞", "Mass-energy equivalence is famously expressed by the equation E equals m c squared.", "750"),
    ("Lorentz factor", "ローレンツ因子", "名詞", "The Lorentz factor increases sharply as an object's speed approaches the speed of light.", "850"),
    ("equivalence principle", "等価原理", "名詞", "The equivalence principle states that gravity and acceleration are locally indistinguishable.", "850"),
    ("gravitational lensing", "重力レンズ効果", "名詞", "Gravitational lensing bends light as it passes near a massive object.", "750"),
    ("spacetime curvature", "時空の曲率", "名詞", "General relativity describes gravity as spacetime curvature caused by mass and energy.", "800"),
    ("proper time", "固有時", "名詞", "Proper time is the time measured by a clock moving along with the observer.", "850"),
    ("twin paradox", "双子のパラドックス", "名詞", "In the twin paradox, the traveling twin ages more slowly than the twin who stays on Earth.", "800"),
    ("geodesic", "測地線", "名詞", "In curved spacetime, a free-falling object follows a geodesic.", "850"),
    ("Schrödinger equation", "シュレーディンガー方程式", "名詞", "The Schrödinger equation describes how a quantum system's wave function changes over time.", "800"),
    ("quantum entanglement", "量子もつれ", "名詞", "Quantum entanglement links two particles so that measuring one instantly affects the other.", "700"),
    ("quantum number", "量子数", "名詞", "Each electron in an atom is described by a unique set of quantum numbers.", "700"),
    ("de Broglie wavelength", "ド・ブロイ波長", "名詞", "The de Broglie wavelength shows that even particles like electrons have wave-like properties.", "800"),
    ("Pauli exclusion principle", "パウリの排他原理", "名詞", "The Pauli exclusion principle states that no two electrons can occupy the same quantum state.", "800"),
    ("blackbody radiation", "黒体放射", "名詞", "Blackbody radiation played a key role in the discovery of quantum mechanics.", "800"),
    ("Newton's laws of motion", "ニュートンの運動の法則", "名詞", "Newton's laws of motion form the foundation of classical mechanics.", "600"),
    ("Newton's first law", "ニュートンの第一法則（慣性の法則）", "名詞", "Newton's first law states that an object at rest stays at rest unless acted on by a force.", "550"),
    ("Newton's second law", "ニュートンの第二法則", "名詞", "Newton's second law states that force equals mass times acceleration.", "550"),
    ("Newton's third law", "ニュートンの第三法則（作用反作用の法則）", "名詞", "Newton's third law says that every action has an equal and opposite reaction.", "550"),
    ("conservation of energy", "エネルギー保存の法則", "名詞", "The conservation of energy states that energy cannot be created or destroyed.", "550"),
    ("conservation of momentum", "運動量保存の法則", "名詞", "The conservation of momentum explains what happens when two billiard balls collide.", "600"),
    ("angular momentum", "角運動量", "名詞", "A spinning ice skater speeds up by conserving angular momentum as she pulls in her arms.", "650"),
    ("centripetal force", "向心力", "名詞", "Centripetal force keeps a car moving in a circular path around a curve.", "600"),
    ("centrifugal force", "遠心力", "名詞", "Passengers feel a centrifugal force pushing them outward on a spinning amusement park ride.", "600"),
    ("work-energy theorem", "仕事とエネルギーの定理", "名詞", "The work-energy theorem states that the work done on an object equals its change in kinetic energy.", "750"),
]


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, level in WORDS:
            if en.lower() in w_existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, DOMAIN, level),
            )
            w_existing.add(en.lower())
            added += 1
        print(f"words: +{added} (skipped {skipped})")

    with db() as conn:
        print("total words:", conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
        print("物理 domain count:",
              conn.execute("SELECT COUNT(*) FROM words WHERE domain=?", (DOMAIN,)).fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
