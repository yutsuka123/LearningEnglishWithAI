# ruff: noqa: E501
"""Railway specialist vocabulary (鉄道): block system, turnouts, signalling,
power, rolling stock, operations. Authored by Claude — no app/OpenAI API
calls. Dedupe on english; back-fill empty examples. domain="鉄道".
US/UK differences noted in the Japanese gloss.

Run: python scripts/add_railway.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

LEVEL = "800"
WORDS: list[tuple[str, str, str]] = [
    # 閉塞・信号
    ("block", "閉塞（区間）", "Only one train may occupy a block at a time."),
    ("block system", "閉塞方式", "A block system prevents rear-end collisions."),
    ("block signal", "閉塞信号", "The block signal turned red behind the train."),
    ("track circuit", "軌道回路", "A track circuit detects a train's position."),
    ("interlocking", "連動装置", "Interlocking prevents conflicting routes."),
    ("home signal", "場内信号", "The home signal protects the station throat."),
    ("starting signal", "出発信号", "The starting signal cleared the departure."),
    ("semaphore signal", "腕木式信号", "Old lines once used semaphore signals."),
    ("signal box", "信号扱所", "The signal box controls the junction."),
    ("aspect", "現示（信号の表示）", "A green aspect means proceed."),
    # 分岐器・軌道
    ("turnout", "分岐器", "A turnout lets a train change tracks."),
    ("points", "分岐器（英）", "The points were set for the loop line."),
    ("switch", "分岐器（米）", "The switch directs the train onto track two."),
    ("point machine", "転てつ機", "The point machine moves the switch rails."),
    ("crossing (track)", "クロッシング・轍叉", "The wheels rattle over the crossing."),
    ("gauge", "軌間", "Japan's narrow gauge is 1,067 millimeters."),
    ("standard gauge", "標準軌", "The Shinkansen uses standard gauge."),
    ("narrow gauge", "狭軌", "Many local lines are narrow gauge."),
    ("ballast", "道床・バラスト", "Ballast holds the track in place."),
    ("sleeper", "枕木（英）", "Concrete sleepers carry the rails."),
    ("railroad tie", "枕木（米）", "Wooden ties rot over time."),
    ("rail joint", "レール継目", "The clack comes from the rail joints."),
    ("gradient", "勾配", "The steep gradient slowed the freight train."),
    ("cant", "カント・軌道の傾き", "Cant helps trains lean into curves."),
    ("permanent way", "保線・軌道（英）", "Permanent way crews work at night."),
    # 電化・集電
    ("catenary", "架線", "The pantograph slides along the catenary."),
    ("overhead line", "架線・電車線", "The overhead line supplies power."),
    ("third rail", "第三軌条", "Some subways draw power from a third rail."),
    ("traction power", "き電・動力電源", "Traction power feeds the overhead line."),
    ("substation", "変電所", "A substation steps the voltage down."),
    ("electrification", "電化", "Electrification replaced the diesel fleet."),
    # 車両
    ("bogie", "台車（英）", "Each car rides on two bogies."),
    ("rolling stock", "車両（総称）", "The depot maintains the rolling stock."),
    ("multiple unit", "電車編成（動力分散）", "A multiple unit has motors under many cars."),
    ("railcar", "気動車・単行車両", "A diesel railcar serves the branch line."),
    ("formation", "編成", "The train formation has ten cars."),
    ("marshalling yard", "操車場", "Freight cars are sorted in the marshalling yard."),
    ("depot", "車両基地", "Trains are serviced at the depot overnight."),
    ("siding", "側線・待避線", "The freight train waited in a siding."),
    # 運行・保安
    ("single track", "単線", "Trains take turns on the single track."),
    ("double track", "複線", "The double track carries two-way traffic."),
    ("derailment", "脱線", "The derailment closed the line for hours."),
    ("dispatcher", "運転指令員", "The dispatcher reroutes delayed trains."),
    ("ATS", "自動列車停止装置(ATS)", "ATS stops a train that overruns a red signal."),
    ("ATC", "自動列車制御(ATC)", "ATC keeps the train within the speed limit."),
    ("CTC", "列車集中制御(CTC)", "CTC controls signals from one center."),
    ("terminus", "終端駅", "The line ends at a grand terminus."),
    ("rapid service", "快速", "The rapid service skips minor stations."),
    ("level crossing", "踏切（英）", "Cars wait at the level crossing."),
]


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = filled = 0
        for en, ja, ex in WORDS:
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
                (en, ja, "", ex, "鉄道", LEVEL),
            )
            existing.add(en.lower())
            added += 1
    print(f"words: +{added} (例文補充 {filled})")
    with db() as conn:
        print("単語総数:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
              "/ 鉄道:",
              conn.execute("SELECT COUNT(*) FROM words WHERE domain='鉄道'").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
