# ruff: noqa: E501
"""Mechanical engineering: machine tools & manufacturing processes. Authored by
Claude — no app/OpenAI API calls. Dedupe on english; back-fill examples.
domain="機械工学". Run: python scripts/add_mech2.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

LEVEL = "800"
WORDS: list[tuple[str, str, str]] = [
    ("milling machine", "フライス盤", "A milling machine cuts flat and shaped surfaces."),
    ("lathe", "旋盤", "A lathe turns a rotating workpiece."),
    ("NC lathe", "NC旋盤", "An NC lathe cuts to programmed dimensions."),
    ("CNC", "数値制御(CNC)", "CNC machines follow a digital program."),
    ("machining center", "マシニングセンター", "A machining center changes tools automatically."),
    ("drilling machine", "ボール盤", "A drilling machine bores holes in metal."),
    ("drill press", "直立ボール盤", "Clamp the part on the drill press."),
    ("drill", "ドリル", "The drill made a clean round hole."),
    ("drill bit", "ドリル刃・きり", "Replace the worn drill bit."),
    ("end mill", "エンドミル", "The end mill cut a narrow slot."),
    ("tap", "タップ(ねじ切り工具)", "A tap cuts internal threads."),
    ("cutting tool", "切削工具", "The cutting tool gradually wore out."),
    ("machining", "機械加工", "Machining removes metal to shape a part."),
    ("cutting", "切削加工", "Cutting shapes the metal precisely."),
    ("casting", "鋳造", "Casting pours molten metal into a mold."),
    ("die casting", "ダイカスト", "Die casting makes precise metal parts."),
    ("sand casting", "砂型鋳造", "Sand casting uses a mold made of sand."),
    ("forging", "鍛造", "Forging hammers heated metal into shape."),
    ("mold", "鋳型・金型", "Molten metal fills the mold."),
    ("grinding", "研削", "Grinding gives a smooth, accurate finish."),
    ("grinder", "研削盤・グラインダー", "The grinder smooths the rough edge."),
    ("grinding wheel", "砥石(といし)", "The grinding wheel spins at high speed."),
    ("surface grinding", "平面研削", "Surface grinding flattens the part."),
    ("cylindrical grinding", "円筒研削", "Cylindrical grinding finishes round shafts."),
    ("abrasive", "研磨材・研削材", "An abrasive wears down the surface."),
    ("polishing", "研磨・つや出し", "Polishing makes the metal shine."),
    ("honing", "ホーニング", "Honing finishes the cylinder bore."),
    ("lapping", "ラッピング(精密研磨)", "Lapping produces a very flat surface."),
    ("welding", "溶接", "Welding joins two steel plates."),
    ("spindle", "主軸(スピンドル)", "The spindle holds the rotating tool."),
    ("feed rate", "送り速度", "Set a safe feed rate for the cut."),
    ("jig", "治具(ジグ)", "A jig guides the tool accurately."),
    ("workpiece", "工作物・ワーク", "Clamp the workpiece firmly before cutting."),
    ("swarf", "切りくず", "Machining produces metal swarf."),
    ("milling", "フライス加工", "Milling removes metal with a rotating cutter."),
    ("turning", "旋削", "Turning shapes a part on a lathe."),
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
                (en, ja, "", ex, "機械工学", LEVEL),
            )
            existing.add(en.lower())
            added += 1
    print(f"words: +{added} (例文補充 {filled})")
    with db() as conn:
        print("単語総数:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
