# ruff: noqa: E501
"""Physics: particle physics, quantum mechanics, physical phenomena, forces &
theories (incl. Schrödinger's cat, neutrino, graviton). Authored by Claude —
no app/OpenAI API calls. Dedupe on english; back-fill examples. domain="物理".
Run: python scripts/add_physics2.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

GROUPS: dict[str, tuple[str, list[tuple[str, str, str]]]] = {
    "素粒子": ("900", [
        ("elementary particle", "素粒子", "An electron is an elementary particle."),
        ("quark", "クォーク", "Protons are made of quarks."),
        ("lepton", "レプトン", "The electron belongs to the lepton family."),
        ("neutrino", "ニュートリノ", "Neutrinos rarely interact with matter."),
        ("boson", "ボソン", "The photon is a kind of boson."),
        ("fermion", "フェルミオン", "Electrons are fermions."),
        ("gluon", "グルーオン", "Gluons bind quarks together."),
        ("Higgs boson", "ヒッグス粒子", "The Higgs boson gives particles their mass."),
        ("muon", "ミュー粒子(ミュオン)", "A muon is like a heavy electron."),
        ("positron", "陽電子", "A positron is the electron's antiparticle."),
        ("antimatter", "反物質", "Antimatter annihilates with ordinary matter."),
        ("antiparticle", "反粒子", "Every particle has an antiparticle."),
        ("graviton", "重力子", "The graviton is a hypothetical particle."),
        ("hadron", "ハドロン", "A proton is a type of hadron."),
        ("photon", "光子", "Light is made of photons."),
        ("quantum", "量子", "Energy comes in tiny packets called quanta."),
    ]),
    "量子・現象": ("900", [
        ("quantum mechanics", "量子力学", "Quantum mechanics describes the tiny world."),
        ("wave-particle duality", "波動粒子二重性", "Light shows wave-particle duality."),
        ("superposition", "重ね合わせ", "A quantum state can be in superposition."),
        ("entanglement", "量子もつれ", "Entanglement links distant particles."),
        ("uncertainty principle", "不確定性原理", "The uncertainty principle limits measurement."),
        ("Schrödinger's cat", "シュレディンガーの猫", "Schrödinger's cat is alive and dead at once."),
        ("wave function", "波動関数", "The wave function describes a particle's state."),
        ("quantum tunneling", "量子トンネル効果", "Quantum tunneling lets particles cross barriers."),
        ("spin", "スピン(量子的角運動量)", "Electrons carry a property called spin."),
        ("observer effect", "観測者効果", "Measurement itself can change a quantum system."),
    ]),
    "物理現象": ("800", [
        ("superconductivity", "超伝導", "Superconductivity removes electrical resistance."),
        ("diffraction", "回折", "Diffraction bends waves around edges."),
        ("resonance", "共鳴・共振", "Resonance amplifies a vibration."),
        ("Doppler effect", "ドップラー効果", "The Doppler effect changes a siren's pitch."),
        ("photoelectric effect", "光電効果", "Einstein explained the photoelectric effect."),
        ("nuclear fission", "核分裂", "Nuclear fission splits heavy atoms."),
        ("nuclear fusion", "核融合", "Nuclear fusion powers the Sun."),
        ("radioactivity", "放射能", "Radioactivity emits particles or rays."),
        ("half-life", "半減期", "Carbon-14 has a very long half-life."),
        ("annihilation", "対消滅", "Annihilation turns mass into pure energy."),
        ("interference", "干渉", "Two waves can interfere with each other."),
    ]),
    "力・理論": ("900", [
        ("fundamental force", "基本的な力", "There are four fundamental forces."),
        ("electromagnetism", "電磁気力・電磁気学", "Electromagnetism unites electricity and magnetism."),
        ("strong force", "強い力(強い相互作用)", "The strong force binds the nucleus."),
        ("weak force", "弱い力(弱い相互作用)", "The weak force causes some radioactive decay."),
        ("standard model", "標準模型", "The Standard Model lists the known particles."),
        ("general relativity", "一般相対性理論", "General relativity treats gravity as curved space."),
        ("special relativity", "特殊相対性理論", "Special relativity links space and time."),
        ("spacetime", "時空", "Mass bends the fabric of spacetime."),
        ("time dilation", "時間の遅れ", "Time dilation slows fast-moving clocks."),
        ("string theory", "弦理論", "String theory models particles as tiny strings."),
    ]),
}


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = filled = 0
        per_group: dict[str, int] = {}
        for group, (level, items) in GROUPS.items():
            for en, ja, ex in items:
                if en.lower() in existing:
                    conn.execute(
                        "UPDATE words SET example = ? WHERE "
                        "LOWER(english)=LOWER(?) AND COALESCE(example,'')=''",
                        (ex, en),
                    )
                    filled += 1
                    continue
                conn.execute(
                    "INSERT INTO words (english, japanese, part_of_speech, "
                    "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                    (en, ja, "", ex, "物理", level),
                )
                existing.add(en.lower())
                added += 1
                per_group[group] = per_group.get(group, 0) + 1
    print(f"words: +{added} (例文補充 {filled})  {per_group}")
    with db() as conn:
        print("単語総数:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
