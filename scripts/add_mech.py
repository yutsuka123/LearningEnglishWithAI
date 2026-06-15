# ruff: noqa: E501
"""Mechanical-engineering specialist vocabulary: fluid mechanics, heat
transfer / thermodynamics, engines, machine elements, control. Authored by
Claude — no app/OpenAI API calls. Dedupe on english; back-fill empty examples.
domain="機械工学".

Run: python scripts/add_mech.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

GROUPS: dict[str, tuple[str, list[tuple[str, str, str]]]] = {
    "流体力学": ("900", [
        ("buckling", "座屈", "Buckling can collapse a slender column."),
        ("viscous fluid", "粘性流体", "Honey is a highly viscous fluid."),
        ("compressible fluid", "圧縮性流体", "Air acts as a compressible fluid at high speed."),
        ("incompressible fluid", "非圧縮性流体", "Water is nearly an incompressible fluid."),
        ("laminar flow", "層流", "Laminar flow is smooth and orderly."),
        ("turbulent flow", "乱流", "Turbulent flow is chaotic and mixing."),
        ("Reynolds number", "レイノルズ数", "The Reynolds number predicts the flow type."),
        ("Navier-Stokes equations", "ナビエ・ストークス方程式", "The Navier-Stokes equations describe fluid motion."),
        ("Bernoulli's principle", "ベルヌーイの定理", "Bernoulli's principle helps explain lift."),
        ("fluid dynamics", "流体力学", "Fluid dynamics studies flowing liquids and gases."),
        ("boundary layer", "境界層", "Friction drag arises in the boundary layer."),
        ("drag", "抗力", "Streamlining reduces aerodynamic drag."),
        ("lift", "揚力", "An airplane wing generates lift."),
        ("viscosity", "粘度", "Oil's viscosity falls as it heats up."),
    ]),
    "伝熱・熱力学": ("900", [
        ("heat conduction", "熱伝導", "Metal allows fast heat conduction."),
        ("thermal radiation", "熱放射", "The sun warms us by thermal radiation."),
        ("radiation", "放射", "Radiation transfers heat through empty space."),
        ("convection", "対流", "Convection carries heat in fluids."),
        ("heat transfer", "熱伝達・伝熱", "Heat transfer occurs by conduction, convection, and radiation."),
        ("first law of thermodynamics", "熱力学第一法則", "The first law of thermodynamics conserves energy."),
        ("second law of thermodynamics", "熱力学第二法則", "The second law of thermodynamics governs entropy."),
        ("thermal resistance", "熱抵抗", "Good insulation has high thermal resistance."),
        ("thermal engineering", "熱工学", "Thermal engineering manages heat flow."),
        ("thermodynamics", "熱力学", "Thermodynamics studies heat and energy."),
        ("heat engine", "熱機関", "A heat engine converts heat into work."),
        ("thermal conductivity", "熱伝導率", "Copper has a high thermal conductivity."),
        ("specific heat", "比熱", "Water has a high specific heat."),
        ("enthalpy", "エンタルピー", "Enthalpy measures the heat content."),
    ]),
    "エンジン": ("800", [
        ("intake", "吸気", "The intake valve lets fresh air in."),
        ("exhaust", "排気", "Exhaust gas leaves through the manifold."),
        ("combustion", "燃焼", "Combustion releases energy from fuel."),
        ("expansion", "膨張", "The hot gas does work during expansion."),
        ("top dead center", "上死点(TDC)", "The piston pauses at top dead center."),
        ("bottom dead center", "下死点(BDC)", "The crank reaches bottom dead center."),
        ("internal combustion engine", "内燃機関", "A car uses an internal combustion engine."),
        ("external combustion engine", "外燃機関", "A steam engine is an external combustion engine."),
        ("camshaft", "カムシャフト", "The camshaft opens and closes the valves."),
        ("cam", "カム", "The cam pushes the follower up."),
        ("combustion chamber", "燃焼室", "Fuel burns inside the combustion chamber."),
        ("steam engine", "蒸気機関", "The steam engine powered early trains."),
        ("piston", "ピストン", "The piston slides inside the cylinder."),
        ("crankshaft", "クランクシャフト", "The crankshaft turns piston motion into rotation."),
        ("stroke", "行程・ストローク", "A four-stroke engine has four steps."),
        ("compression ratio", "圧縮比", "A high compression ratio raises efficiency."),
        ("displacement", "排気量", "The engine has a two-liter displacement."),
    ]),
    "機械要素": ("800", [
        ("linear guide", "リニアガイド(LMガイド)", "A linear guide enables smooth straight motion."),
        ("cam follower", "カムフォロワ", "The cam follower traces the cam profile."),
        ("frictional heat", "摩擦熱", "Brakes produce a lot of frictional heat."),
        ("lubricant", "潤滑剤", "A lubricant reduces friction and wear."),
        ("coupling", "継手・カップリング", "A coupling joins two rotating shafts."),
        ("flywheel", "はずみ車・フライホイール", "The flywheel smooths the engine's rotation."),
        ("gearbox", "変速機・ギアボックス", "The gearbox changes the speed ratio."),
    ]),
    "制御工学": ("900", [
        ("deceleration", "減速・減速度", "Hard braking causes rapid deceleration."),
        ("control engineering", "制御工学", "Control engineering keeps systems stable."),
        ("PID control", "PID制御", "PID control uses error, integral, and derivative terms."),
        ("feedback", "フィードバック", "Feedback corrects the output toward the target."),
        ("feedforward", "フィードフォワード", "Feedforward anticipates a known disturbance."),
        ("servo", "サーボ機構", "A servo positions the arm precisely."),
        ("setpoint", "目標値・設定値", "The controller drives the value to the setpoint."),
        ("damping", "減衰", "Damping suppresses unwanted vibration."),
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
                    (en, ja, "", ex, "機械工学", level),
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
