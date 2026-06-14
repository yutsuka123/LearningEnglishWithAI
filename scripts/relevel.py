# ruff: noqa: E501  (data-heavy maintenance script)
"""Re-level the vocabulary onto the fine scale, authored by Claude — no app/
OpenAI API calls.

Scale (per user, 2026-06-14):
  300- (300以下) / 300 / 400 / 500 / 600 / 700 / 800 / 900 / 990 / 990+ / 範囲外

Policy:
- 範囲外 : only truly problematic words — the 禁止用語 set. Used sparingly.
- 990+   : pure specialist jargon, well beyond TOEIC.
- 990    : very hard academic vocabulary.
- 900    : hard / advanced.
- 300–800: ordinary bands, assigned by a per-domain base with curated
  low-overrides so basic members of hard domains aren't over-rated.

Idempotent (reassigns every word). Run:  python scripts/relevel.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# Typical difficulty band per domain (a word's default unless overridden).
DOMAIN_BASE = {
    "動物": "400", "植物": "400", "料理": "400", "遊び": "400", "買い物": "400", "口語": "400",
    "交通": "500", "旅行": "500", "農業": "500", "スポーツ": "500", "音楽": "500", "公共": "500",
    "米英の違い": "500",
    "恋愛": "600", "教育": "600", "教養": "600", "文学": "600", "建築": "600", "建設": "600",
    "鉄道": "600", "船舶": "600", "航空・宇宙": "600", "医療": "600",
    "ビジネス": "700", "ニュース": "700", "管理": "700", "IT": "700", "政治": "700",
    "経済": "700", "法律": "700", "サスペンス": "700", "SF": "700", "歴史": "700", "科学": "700",
    "世界史": "800", "日本史": "800", "宗教": "800", "軍事": "800", "機械": "800",
    "電気電子": "800", "化学": "800", "物理": "800", "数学": "800", "哲学": "800",
    "病名": "800", "法律手続き": "800",
}
DEFAULT_BASE = "600"  # blank/unknown domain (mostly original common seed words)

# Curated low-overrides: basic members that should sit below their domain base.
LOW = {
    "300": {"cat", "dog"},
    "400": {"lion", "tiger", "bear", "elephant", "giraffe", "zebra", "monkey", "horse", "cow", "pig", "sheep", "goat", "rabbit", "mouse", "fox", "deer", "duck", "chicken", "frog", "snake", "bee", "ant", "fish", "bird"},
    "500": {
        # chemistry basics
        "oxygen", "hydrogen", "nitrogen", "carbon", "acid", "base", "element", "compound", "atom", "solution", "reaction", "salt",
        # math basics
        "addition", "subtraction", "multiplication", "division", "fraction", "decimal", "percentage", "angle", "triangle", "rectangle", "circle", "area", "volume", "average", "sum", "remainder",
        # physics basics
        "gravity", "mass", "velocity", "acceleration", "force", "energy", "friction", "speed",
        # religion basics
        "faith", "soul", "prayer", "blessing", "holy", "sin", "mercy", "worship", "monk", "grace",
    },
    "600": {
        # military common
        "weapon", "soldier", "army", "enemy", "tank", "bomb", "gun",
        # mechanical common
        "motor", "gear", "pump", "valve", "bolt", "nut", "shaft", "weld", "assembly",
        # electronics common
        "circuit", "voltage", "current", "signal", "battery", "wire", "terminal", "fuse", "ground", "resistance",
        # religion mid
        "ritual", "sacred", "divine", "doctrine", "deity", "clergy",
    },
    "700": {
        # military hardware (common-ish)
        "missile", "bomber", "radar", "submarine", "grenade", "armor", "infantry", "general", "captain", "commander", "strategy", "tactics", "artillery", "warship", "cavalry",
        # disease common
        "cancer", "allergy", "infection", "depression", "obesity", "asthma", "influenza", "stroke", "diarrhea", "constipation",
        # legal common
        "lawsuit", "attorney", "trial", "jury", "verdict", "appeal", "sentence", "hearing", "settlement", "custody", "warrant",
    },
}

# Hard / advanced bands.
H900 = {
    # serious medical / anatomy
    "artery", "abdomen", "inflammation", "numbness", "diagnosis", "anatomy", "concussion", "dehydration", "hypertension", "arthritis", "hepatitis", "tuberculosis", "dementia", "pneumonia", "tumor", "ulcer", "anemia", "migraine", "diabetes", "insomnia", "epidemic", "pandemic", "measles", "chickenpox",
    # legal heavy
    "indictment", "subpoena", "deposition", "litigation", "jurisdiction", "injunction", "arbitration", "mediation", "statute", "liability", "acquittal", "conviction", "plaintiff", "defendant", "prosecutor", "testimony", "damages",
    # aerospace
    "aerodynamics", "fuselage", "aileron", "propulsion", "telemetry", "reentry", "trajectory", "escape velocity", "supersonic", "turbine", "thrust", "cosmonaut", "spacewalk",
    # misc advanced
    "outrage", "ceasefire", "armistice",
}
H990 = {
    # math
    "calculus", "trigonometry", "derivative", "integral", "algebra", "geometry", "probability", "statistics", "exponent", "circumference", "prime number", "square root", "variable", "integer", "quotient",
    # physics
    "thermodynamics", "entropy", "isotope", "momentum", "inertia", "magnetism", "wavelength", "amplitude", "electron", "proton", "neutron", "particle", "vector", "relativity", "quantum", "fission", "fusion", "radioactivity", "kinematics", "statics", "dynamics",
    # history jargon
    "feudalism", "renaissance", "reformation", "colonialism", "crusade", "dynasty", "monarchy", "pharaoh", "gladiator", "shogunate", "daimyo", "vassal", "conscription", "antiquity",
    # SF jargon
    "hyperspace", "wormhole", "singularity", "terraform", "interstellar", "dystopia", "utopia", "exoskeleton", "telepathy", "extraterrestrial",
    # suspense
    "forensics", "autopsy", "homicide",
    # biology
    "photosynthesis", "chlorophyll", "deciduous", "perennial", "germinate", "herbivore", "carnivore", "omnivore", "nocturnal", "hibernate", "amphibian", "reptile",
}
H990P = {
    # chemistry
    "titration", "reagent", "precipitate", "catalyst", "oxidation", "reduction", "ion", "molecule", "solvent", "acetic acid", "nitric acid", "sulfuric acid", "hydrochloric acid", "sodium hydroxide", "sodium chloride", "ammonia", "corrosive", "neutralize", "alkali", "citric acid",
    # philosophy
    "metaphysics", "epistemology", "ontology", "existentialism", "rationalism", "empiricism", "idealism", "materialism", "nihilism", "stoicism", "determinism", "dualism", "dialectic", "syllogism", "deduction", "induction", "phenomenology", "utilitarianism", "skepticism", "axiom", "fallacy", "aesthetics", "premise", "transcendental",
    # electronics
    "capacitor", "inductor", "transistor", "diode", "semiconductor", "capacitance", "oscillator", "microcontroller", "firmware", "waveform", "baud rate", "voltage drop", "short circuit",
    # mechanical
    "actuator", "solenoid", "flange", "fluid dynamics", "tolerance", "viscosity", "gasket", "torque", "lubrication", "pneumatic", "hydraulic", "casting", "machining", "lathe", "fatigue", "deformation", "plating",
    # nautical
    "keel", "prow", "stern", "starboard", "port side", "helm", "rudder", "mast", "propeller", "buoy", "gangway", "capsize", "maritime", "nautical", "pantograph", "coupling",
    # theology
    "trinity", "resurrection", "crucifixion", "redemption", "communion", "baptism", "covenant", "messiah", "apostle", "parable", "repentance", "theology", "nirvana", "karma", "reincarnation", "dharma", "impermanence", "talmud", "torah", "quran", "sutra",
    # military hardware jargon
    "trebuchet", "galley", "crossbow", "longbow", "frigate", "amphibious assault ship", "self-propelled artillery", "reconnaissance", "garrison", "ballistic missile", "cruise missile", "nuclear warhead", "destroyer", "battleship",
}

# Flatten LOW into a word->band map for quick lookup.
LOW_MAP: dict[str, str] = {}
for band, words in LOW.items():
    for w in words:
        LOW_MAP[w] = band


def level_for(english: str, domain: str) -> str:
    w = (english or "").lower()
    if domain == "禁止用語":
        return "範囲外"
    if w in H990P:
        return "990+"
    if w in H990:
        return "990"
    if w in H900:
        return "900"
    if w in LOW_MAP:
        return LOW_MAP[w]
    return DOMAIN_BASE.get(domain, DEFAULT_BASE)


def main() -> int:
    with db() as conn:
        rows = conn.execute("SELECT id, english, COALESCE(domain,'') d FROM words").fetchall()
        for r in rows:
            conn.execute(
                "UPDATE words SET level = ? WHERE id = ?",
                (level_for(r["english"], r["d"]), r["id"]),
            )
        dist = dict(
            conn.execute(
                "SELECT level, COUNT(*) FROM words GROUP BY level ORDER BY level"
            ).fetchall()
        )
    print("level distribution:")
    for lv in ["300-", "300", "400", "500", "600", "700", "800", "900", "990", "990+", "範囲外"]:
        if lv in dist:
            print(f"  {lv:6} {dist[lv]}")
    other = {k: v for k, v in dist.items() if k not in {"300-", "300", "400", "500", "600", "700", "800", "900", "990", "990+", "範囲外"}}
    if other:
        print("  other:", other)
    return 0


if __name__ == "__main__":
    sys.exit(main())
