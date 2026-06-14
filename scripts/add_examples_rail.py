# ruff: noqa: E501  (data-heavy seed script)
"""Fill example sentences for the technical/medical vocabulary added earlier,
and add railway (鉄道) vocabulary + phrases. Authored by Claude — no app/
OpenAI API calls.

- EXAMPLES: english -> example. Applied only where the word's example is
  currently empty (existing examples are never overwritten).
- RAIL_WORDS / RAIL_PHRASES: new railway study items (domain 鉄道 / scene 鉄道・駅).

Run:  python scripts/add_examples_rail.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

SCENE_RAIL = "鉄道・駅"

# --- examples for previously-added words (filled only if example is empty) ---

EXAMPLES: dict[str, str] = {
    # body / medical
    "organ": "The heart is a vital organ.",
    "chest": "I feel a tightness in my chest.",
    "rib": "He cracked a rib in the fall.",
    "heart": "The doctor listened to my heart.",
    "lung": "Smoking damages the lungs.",
    "liver": "The liver filters toxins from the blood.",
    "kidney": "He had a kidney stone removed.",
    "stomach": "My stomach is upset.",
    "intestine": "The small intestine absorbs nutrients.",
    "bowel": "She has a bowel disorder.",
    "spleen": "The spleen helps fight infection.",
    "pancreas": "The pancreas produces insulin.",
    "gallbladder": "They removed his gallbladder.",
    "bladder": "I have a bladder infection.",
    "uterus": "The fetus grows in the uterus.",
    "brain": "The brain controls the whole body.",
    "skull": "The skull protects the brain.",
    "forehead": "He has a high forehead.",
    "temple": "My temples are throbbing.",
    "jaw": "My jaw hurts when I chew.",
    "gum": "My gums are bleeding.",
    "tongue": "I burned my tongue on the soup.",
    "spine": "Sit up straight to protect your spine.",
    "joint": "My joints ache in cold weather.",
    "muscle": "I pulled a muscle in my back.",
    "nerve": "The nerve sends signals to the brain.",
    "artery": "An artery carries blood from the heart.",
    "vein": "Blood returns to the heart through veins.",
    "elbow": "I bumped my elbow on the door.",
    "wrist": "She sprained her wrist.",
    "knee": "My knee gives me trouble when I run.",
    "shoulder": "I carry my bag on my left shoulder.",
    "abdomen": "He felt a sharp pain in his abdomen.",
    "waist": "He bent at the waist to pick it up.",
    "hip": "She broke her hip in the fall.",
    "thigh": "The muscle in my thigh is sore.",
    "calf": "I got a cramp in my calf.",
    "palm": "She held the coin in her palm.",
    "inflammation": "The cream reduces inflammation.",
    "swelling": "Ice will reduce the swelling.",
    "rash": "The rash spread across his arm.",
    "numbness": "I feel numbness in my fingers.",
    "cramp": "I woke up with a leg cramp.",
    "sprain": "It's just a sprain, not a fracture.",
    "fracture": "The X-ray showed a small fracture.",
    "bruise": "He has a bruise on his knee.",
    "dizziness": "The medicine may cause dizziness.",
    "nausea": "The nausea passed after an hour.",
    "symptom": "A fever is a common symptom.",
    "diagnosis": "The diagnosis was confirmed by tests.",
    # chemistry
    "acid": "Lemon juice is a weak acid.",
    "alkali": "Soap is mildly alkali.",
    "base": "A base neutralizes an acid.",
    "sulfuric acid": "Car batteries contain sulfuric acid.",
    "nitric acid": "Nitric acid is highly corrosive.",
    "hydrochloric acid": "The stomach produces hydrochloric acid.",
    "citric acid": "Citric acid gives lemons their sour taste.",
    "acetic acid": "Vinegar is a dilute acetic acid.",
    "sodium hydroxide": "Sodium hydroxide is a strong base.",
    "sodium chloride": "Table salt is sodium chloride.",
    "ammonia": "Ammonia has a sharp smell.",
    "hydrogen": "Water is made of hydrogen and oxygen.",
    "oxygen": "We breathe in oxygen.",
    "nitrogen": "Air is mostly nitrogen.",
    "carbon": "Diamond is a form of carbon.",
    "compound": "Water is a chemical compound.",
    "element": "Gold is a chemical element.",
    "molecule": "A water molecule has three atoms.",
    "atom": "An atom has a nucleus and electrons.",
    "ion": "Salt dissolves into ions in water.",
    "solution": "Stir until it forms a clear solution.",
    "solvent": "Water is a common solvent.",
    "concentration": "Increase the concentration of the acid.",
    "oxidation": "Rust forms by oxidation of iron.",
    "reduction": "Reduction is the gain of electrons.",
    "catalyst": "A catalyst speeds up the reaction.",
    "reaction": "The reaction released heat.",
    "corrosive": "This chemical is highly corrosive.",
    "flammable": "Keep flammable liquids away from fire.",
    "toxic": "These fumes are toxic.",
    "dilute": "Dilute the acid with water.",
    "neutralize": "Add a base to neutralize the acid.",
    "titration": "We measured it by titration.",
    "reagent": "Add the reagent drop by drop.",
    "precipitate": "A white precipitate formed at the bottom.",
    # physics
    "mechanics": "He studies classical mechanics.",
    "dynamics": "Dynamics deals with forces and motion.",
    "statics": "Statics analyzes bodies at rest.",
    "kinematics": "Kinematics describes motion without forces.",
    "relativity": "Einstein's theory of relativity changed physics.",
    "quantum": "Quantum mechanics describes tiny particles.",
    "nuclear": "Nuclear power plants generate electricity.",
    "nuclear material": "Nuclear material must be stored safely.",
    "fission": "Nuclear fission splits an atom.",
    "fusion": "The sun is powered by nuclear fusion.",
    "radiation": "The workers wore shields against radiation.",
    "radioactivity": "They measured the radioactivity of the sample.",
    "gravity": "Gravity pulls objects toward the earth.",
    "mass": "Mass does not change with location.",
    "velocity": "The car reached a high velocity.",
    "acceleration": "Acceleration is the rate of change of velocity.",
    "force": "Apply a force to move the object.",
    "momentum": "A heavy truck has great momentum.",
    "energy": "Energy cannot be created or destroyed.",
    "friction": "Friction slows the sliding box.",
    "inertia": "A body at rest stays at rest due to inertia.",
    "vector": "Velocity is a vector with direction.",
    "frequency": "The wave has a high frequency.",
    "wavelength": "Red light has a long wavelength.",
    "amplitude": "A louder sound has a larger amplitude.",
    "magnetism": "Magnetism attracts iron filings.",
    "thermodynamics": "The engine obeys the laws of thermodynamics.",
    "entropy": "Entropy tends to increase over time.",
    "particle": "A photon is a particle of light.",
    "electron": "An electron carries a negative charge.",
    "proton": "A proton has a positive charge.",
    "neutron": "A neutron has no charge.",
    "isotope": "Carbon-14 is an isotope of carbon.",
    # mechanical
    "fluid dynamics": "Fluid dynamics studies how liquids flow.",
    "flange": "Bolt the pipe to the flange.",
    "motor": "The electric motor drives the pump.",
    "actuator": "The actuator opens the valve.",
    "solenoid": "The solenoid moves the plunger when energized.",
    "sheet metal": "The cover is made of sheet metal.",
    "surface treatment": "Surface treatment prevents corrosion.",
    "tolerance": "The part is machined to a tight tolerance.",
    "bearing": "The bearing reduces friction on the shaft.",
    "gear": "The gears transmit the engine's power.",
    "shaft": "The motor turns the drive shaft.",
    "valve": "Open the valve to release the pressure.",
    "pump": "The pump circulates the coolant.",
    "piston": "The piston moves inside the cylinder.",
    "cylinder": "Fuel burns inside the cylinder.",
    "torque": "Tighten the bolt to the specified torque.",
    "lubrication": "Proper lubrication extends the part's life.",
    "viscosity": "Oil has a higher viscosity than water.",
    "gasket": "Replace the gasket to stop the leak.",
    "bolt": "Tighten the bolt with a wrench.",
    "nut": "Screw the nut onto the bolt.",
    "weld": "Weld the two plates together.",
    "casting": "The engine block is made by casting.",
    "machining": "Machining gives the part its final shape.",
    "lathe": "He turned the shaft on a lathe.",
    "coolant": "Check the coolant level regularly.",
    "hydraulic": "A hydraulic press exerts huge force.",
    "pneumatic": "A pneumatic tool runs on compressed air.",
    "assembly": "The parts move down the assembly line.",
    "fatigue": "Metal fatigue caused the crack.",
    "deformation": "The load caused permanent deformation.",
    "plating": "Chrome plating protects the surface.",
    # electrical / electronic
    "circuit": "The current flows around the circuit.",
    "circuit board": "Components are soldered onto the circuit board.",
    "solder": "Solder the wire to the terminal.",
    "resistor": "A resistor limits the current.",
    "capacitor": "The capacitor stores electric charge.",
    "inductor": "An inductor resists changes in current.",
    "transistor": "A transistor can amplify a signal.",
    "diode": "A diode lets current flow one way.",
    "voltage": "Measure the voltage across the resistor.",
    "current": "Too much current can burn the wire.",
    "resistance": "Higher resistance lowers the current.",
    "conductor": "Copper is a good conductor of electricity.",
    "insulator": "Rubber is an electrical insulator.",
    "semiconductor": "Silicon is a common semiconductor.",
    "ground": "Connect the case to ground for safety.",
    "terminal": "Attach the wire to the positive terminal.",
    "relay": "The relay switches the motor on.",
    "fuse": "The fuse blew and cut the power.",
    "transformer": "A transformer steps the voltage down.",
    "capacitance": "A larger plate gives more capacitance.",
    "amplifier": "The amplifier boosts the weak signal.",
    "oscillator": "The oscillator generates a clock signal.",
    "microcontroller": "The microcontroller runs the firmware.",
    "firmware": "We updated the device's firmware.",
    "signal": "The sensor sends a signal to the controller.",
    "waveform": "The oscilloscope shows the waveform.",
    "short circuit": "A short circuit tripped the breaker.",
    "connector": "Plug the cable into the connector.",
    "voltage drop": "A long wire causes a voltage drop.",
    "printed circuit board": "The chips sit on a printed circuit board.",
}

# --- railway vocabulary (domain 鉄道) ---------------------------------------
# (english, japanese, example)

RAIL_WORDS: list[tuple[str, str, str]] = [
    ("railway", "鉄道", "The railway connects the two cities."),
    ("railroad", "鉄道(米)", "The railroad runs across the country."),
    ("track", "線路", "Do not walk on the track."),
    ("rail", "レール", "Sparks flew from the rail."),
    ("platform", "プラットホーム", "The train leaves from platform 3."),
    ("locomotive", "機関車", "A steam locomotive pulled the cars."),
    ("carriage", "客車・車両", "We sat in the first carriage."),
    ("freight", "貨物", "The freight train was very long."),
    ("timetable", "時刻表", "Check the timetable for the next train."),
    ("ticket gate", "改札", "Insert your ticket at the ticket gate."),
    ("turnstile", "回転式改札", "Tap your card at the turnstile."),
    ("terminus", "終着駅", "Tokyo is the terminus of this line."),
    ("junction", "分岐・接続駅", "Change trains at the next junction."),
    ("level crossing", "踏切", "Wait at the level crossing for the train."),
    ("derail", "脱線する", "The train derailed after the quake."),
    ("commuter", "通勤客", "The train was packed with commuters."),
    ("rush hour", "ラッシュアワー", "Avoid the trains during rush hour."),
    ("express", "急行", "Take the express to save time."),
    ("limited express", "特急", "The limited express skips small stations."),
    ("local train", "各駅停車", "The local train stops at every station."),
    ("bullet train", "新幹線", "The bullet train reaches 300 km/h."),
    ("transfer", "乗り換え(する)", "Transfer to the subway at the next stop."),
    ("delay", "遅延", "There was a 20-minute delay this morning."),
    ("sleeper car", "寝台車", "We booked a sleeper car for the night."),
    ("dining car", "食堂車", "Let's have lunch in the dining car."),
    ("conductor", "車掌", "The conductor checked our tickets."),
    ("subway", "地下鉄", "Take the subway downtown."),
    ("tram", "路面電車", "A tram runs down the main street."),
    ("pantograph", "パンタグラフ", "The pantograph collects power from the wire."),
    ("overhead wire", "架線", "Trains draw power from the overhead wire."),
    ("coupling", "連結器", "The coupling joins two carriages."),
    ("gauge", "軌間", "Japan uses a narrow gauge on many lines."),
    ("depot", "車両基地", "The trains are serviced at the depot."),
    ("reserved seat", "指定席", "I booked a reserved seat to Kyoto."),
    ("commuter pass", "定期券", "I bought a monthly commuter pass."),
]

# --- railway phrases (scene 鉄道・駅) ----------------------------------------

RAIL_PHRASES: list[tuple[str, str]] = [
    ("Which platform does the train leave from?", "電車はどのホームから出ますか？"),
    ("Where do I transfer for the Yamanote Line?", "山手線への乗り換えはどこですか？"),
    ("Does this train stop at Shibuya?", "この電車は渋谷に止まりますか？"),
    ("Is this the local or the express?", "これは各駅停車ですか、急行ですか？"),
    ("One ticket to Kyoto, please.", "京都まで1枚お願いします。"),
    ("I'd like a reserved seat.", "指定席をお願いします。"),
    ("The train is delayed by ten minutes.", "電車は10分遅れています。"),
    ("Please mind the gap.", "ホームと電車の隙間にご注意ください。"),
    ("The doors are closing.", "ドアが閉まります。"),
    ("Please stand behind the yellow line.", "黄色い線の内側にお下がりください。"),
    ("This train is bound for Tokyo.", "この電車は東京行きです。"),
    ("Where is the ticket gate?", "改札はどこですか？"),
    ("My train was canceled.", "電車が運休になりました。"),
    ("Is there a direct train?", "直通電車はありますか？"),
    ("How many stops to the airport?", "空港まで何駅ですか？"),
    ("Do I need to change trains?", "乗り換えは必要ですか？"),
    ("The next station is Ueno.", "次の駅は上野です。"),
    ("Please have your ticket ready.", "切符をご用意ください。"),
    ("I missed my train.", "電車に乗り遅れました。"),
    ("Where can I buy a commuter pass?", "定期券はどこで買えますか？"),
    ("This seat is reserved.", "この席は指定席です。"),
    ("Priority seats are for those who need them.", "優先席は必要な方のための席です。"),
]


def main() -> int:
    with db() as conn:
        # 1) Fill examples where empty.
        filled = 0
        for en, ex in EXAMPLES.items():
            cur = conn.execute(
                "UPDATE words SET example = ? "
                "WHERE LOWER(english) = LOWER(?) AND COALESCE(example, '') = ''",
                (ex, en),
            )
            filled += cur.rowcount

        # 2) Railway words.
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        w_added = w_skipped = 0
        for en, ja, ex in RAIL_WORDS:
            if en.lower() in w_existing:
                # still try to fill an empty example for the existing row.
                conn.execute(
                    "UPDATE words SET example = ? "
                    "WHERE LOWER(english) = LOWER(?) AND COALESCE(example, '') = ''",
                    (ex, en),
                )
                w_skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, "", ex, "鉄道", "700"),
            )
            w_existing.add(en.lower())
            w_added += 1

        # 3) Railway phrases.
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        ph_added = ph_skipped = 0
        for en, ja in RAIL_PHRASES:
            if en.lower() in ph_existing:
                ph_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) VALUES (?, ?, ?)",
                (en, ja, SCENE_RAIL),
            )
            ph_existing.add(en.lower())
            ph_added += 1

    print(f"examples filled: {filled}")
    print(f"rail words: +{w_added} (skipped {w_skipped})")
    print(f"rail phrases: +{ph_added} (skipped {ph_skipped})")
    with db() as conn:
        empty = conn.execute(
            "SELECT COUNT(*) FROM words WHERE COALESCE(example, '') = ''"
        ).fetchone()[0]
        print(
            "totals -> phrases:",
            conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0],
            "words:",
            conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
            "/ words still without example:", empty,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
