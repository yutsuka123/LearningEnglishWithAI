# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""制御工学の深掘り語(既存「機械工学」に追加)＋生物工学(新設)＋経営工学
(新設)＋生産工学(既存「製造」に追加), authored by Claude (2026-08-05・
ユーザー要望:「制御工学　生物工学…増やしましょうか」＋「質は落とさない
ように、段階的に実装ください」).

調査の結果、PID control/control engineering/feedback loop/setpoint/servo
motor等の制御工学基礎語は既に「機械工学」に、closed-loop/open-loopは
「車載組込み開発」にあったため、制御工学は一段深い理論語のみ追加。
「生物工学」はDNA/enzyme等の分子生物学語が中心の「生化学」「生物学」とは
別に、工学的応用語として新設。「経営工学」はプロジェクト管理語中心の
「管理」(19語)・品質手法中心の「品質工学」(72語)とは別に、生産システムの
最適化理論として新設。「生産工学」は既存「製造」がbatch/outsource/
supplier/workmanshipの4語のみだったため、量産・工場運営の語彙を大幅補強。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words`
table.

Run:  python scripts/add_control_bio_industrial_eng.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

MECH = "機械工学"
BIO = "生物工学"
INDUSTRIAL = "経営工学"
MANUFACTURING = "製造"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 制御工学の深掘り語（既存「機械工学」に追加） ---
    ("transfer function", "伝達関数", "名詞", "The transfer function describes how the system's output responds to its input.", MECH, "950"),
    ("block diagram", "ブロック図", "名詞", "The block diagram shows how each component of the control system connects.", MECH, "800"),
    ("state-space representation", "状態空間表現", "名詞", "A state-space representation describes the system using a set of internal variables.", MECH, "950"),
    ("stability (control theory)", "安定性（制御理論の）", "名詞", "Stability means the system's output settles down instead of oscillating forever.", MECH, "900"),
    ("step response", "ステップ応答", "名詞", "Engineers plot the step response to see how quickly the system reacts to a sudden change.", MECH, "900"),
    ("PID tuning", "PID調整", "名詞", "PID tuning adjusts three parameters until the controller responds quickly without overshooting.", MECH, "900"),
    ("control system", "制御系・制御システム", "名詞", "The control system keeps the room at exactly the temperature you set.", MECH, "700"),
    ("plant (control theory)", "制御対象（プラント）", "名詞", "In control theory, the plant is the physical system being controlled.", MECH, "950"),
    ("overshoot (control theory)", "オーバーシュート（行き過ぎ量）", "名詞", "A little overshoot is normal, but too much can make the system unstable.", MECH, "900"),
    ("digital control", "ディジタル制御", "名詞", "Digital control uses a microcontroller to sample and adjust the system many times per second.", MECH, "850"),
    # --- 生物工学（新設） ---
    ("bioengineering", "生物工学", "名詞", "Bioengineering applies engineering principles to living systems and medicine.", BIO, "800"),
    ("genetic engineering", "遺伝子工学", "名詞", "Genetic engineering can add, remove, or change specific genes in an organism.", BIO, "750"),
    ("gene editing", "ゲノム編集", "名詞", "Gene editing lets researchers correct a single faulty letter in a gene.", BIO, "800"),
    ("CRISPR", "CRISPR（ゲノム編集技術）", "名詞", "CRISPR made gene editing far cheaper and more precise than earlier methods.", BIO, "850"),
    ("recombinant DNA", "組換えDNA", "名詞", "Recombinant DNA technology lets bacteria produce human insulin.", BIO, "900"),
    ("tissue engineering", "組織工学", "名詞", "Tissue engineering aims to grow replacement organs in the laboratory.", BIO, "850"),
    ("biomaterial", "生体材料", "名詞", "A biomaterial must be safe for the body to accept without rejecting it.", BIO, "800"),
    ("scaffold (tissue engineering)", "スキャフォールド（足場材）", "名詞", "Cells grow around a scaffold that gives the new tissue its shape.", BIO, "900"),
    ("bioreactor", "バイオリアクター", "名詞", "A bioreactor keeps the temperature and nutrients steady while cells multiply.", BIO, "850"),
    ("synthetic biology", "合成生物学", "名詞", "Synthetic biology designs new genetic circuits that don't exist in nature.", BIO, "900"),
    ("biosensor", "バイオセンサー", "名詞", "A biosensor detects a specific molecule and converts it into an electrical signal.", BIO, "850"),
    ("biomedical engineering", "生体医工学", "名詞", "Biomedical engineering designs devices like pacemakers and artificial joints.", BIO, "800"),
    ("stem cell therapy", "幹細胞治療", "名詞", "Stem cell therapy uses cells that can develop into many different tissue types.", BIO, "800"),
    ("monoclonal antibody", "モノクローナル抗体", "名詞", "A monoclonal antibody is engineered to target one specific protein.", BIO, "900"),
    ("bioprocessing", "バイオプロセシング", "名詞", "Bioprocessing scales up a lab discovery into a factory that can produce it in bulk.", BIO, "850"),
    ("protein engineering", "タンパク質工学", "名詞", "Protein engineering redesigns an enzyme to work faster or in harsher conditions.", BIO, "900"),
    # --- 経営工学（新設） ---
    ("industrial engineering", "経営工学・産業工学", "名詞", "Industrial engineering makes factories and organizations run more efficiently.", INDUSTRIAL, "800"),
    ("operations research", "オペレーションズリサーチ", "名詞", "Operations research uses mathematical models to find the best way to allocate resources.", INDUSTRIAL, "900"),
    ("ergonomics", "人間工学・エルゴノミクス", "名詞", "Ergonomics designs workstations that reduce strain on the human body.", INDUSTRIAL, "800"),
    ("value engineering", "バリューエンジニアリング", "名詞", "Value engineering looks for ways to cut cost without losing the function customers want.", INDUSTRIAL, "900"),
    ("time and motion study", "時間動作研究", "名詞", "A time and motion study measures exactly how long each step of a task takes.", INDUSTRIAL, "900"),
    ("facility layout", "工場・施設レイアウト", "名詞", "A better facility layout shortens the distance materials travel between steps.", INDUSTRIAL, "850"),
    ("linear programming", "線形計画法", "名詞", "Linear programming finds the combination that maximizes profit under several constraints.", INDUSTRIAL, "900"),
    ("queuing theory", "待ち行列理論", "名詞", "Queuing theory predicts how long customers will wait in line at different arrival rates.", INDUSTRIAL, "950"),
    ("critical path method", "クリティカルパス法", "名詞", "The critical path method identifies which tasks, if delayed, will delay the whole project.", INDUSTRIAL, "900"),
    ("capacity planning", "生産能力計画", "名詞", "Capacity planning decides how many machines and workers a factory will need next year.", INDUSTRIAL, "850"),
    ("inventory management", "在庫管理", "名詞", "Good inventory management avoids both running out of stock and tying up too much cash.", INDUSTRIAL, "750"),
    ("economic order quantity", "経済的発注量", "名詞", "The economic order quantity balances ordering costs against storage costs.", INDUSTRIAL, "950"),
    ("systems engineering", "システムズエンジニアリング", "名詞", "Systems engineering coordinates every subsystem so the whole product works together.", INDUSTRIAL, "850"),
    # --- 生産工学（既存「製造」に追加） ---
    ("production line", "生産ライン", "名詞", "The factory added a second production line to double its output.", MANUFACTURING, "550"),
    ("assembly line", "組立ライン", "名詞", "Workers on the assembly line each handle one small step of the process.", MANUFACTURING, "550"),
    ("mass production", "量産・マスプロダクション", "名詞", "Mass production lowered the cost of the car so more people could afford one.", MANUFACTURING, "650"),
    ("factory automation", "工場の自動化", "名詞", "Factory automation replaced many repetitive tasks with robotic arms.", MANUFACTURING, "700"),
    ("industrial robot", "産業用ロボット", "名詞", "An industrial robot can weld the same joint thousands of times without a mistake.", MANUFACTURING, "700"),
    ("conveyor belt", "コンベアベルト", "名詞", "Parts move along the conveyor belt from one station to the next.", MANUFACTURING, "600"),
    ("cycle time", "サイクルタイム", "名詞", "Reducing the cycle time let the line produce more units every hour.", MANUFACTURING, "800"),
    ("takt time", "タクトタイム", "名詞", "Takt time tells each station exactly how much time it has to finish its task.", MANUFACTURING, "900"),
    ("work-in-process", "仕掛品（工程内在庫）", "名詞", "Too much work-in-process piles up between slow and fast stations on the line.", MANUFACTURING, "850"),
    ("lean production", "リーン生産方式", "名詞", "Lean production focuses on removing every step that doesn't add value for the customer.", MANUFACTURING, "800"),
    ("Toyota Production System", "トヨタ生産方式", "名詞", "The Toyota Production System pioneered just-in-time manufacturing.", MANUFACTURING, "850"),
    ("just-in-time production", "ジャストインタイム生産", "名詞", "Just-in-time production delivers parts to the line exactly when they are needed.", MANUFACTURING, "850"),
    ("overall equipment effectiveness (OEE)", "総合設備効率（OEE）", "名詞", "Overall equipment effectiveness combines availability, performance, and quality into one score.", MANUFACTURING, "900"),
    ("production scheduling", "生産スケジューリング", "名詞", "Production scheduling decides which orders each machine will run and when.", MANUFACTURING, "800"),
    ("bill of materials", "部品構成表（BOM）", "名詞", "The bill of materials lists every part needed to build one finished product.", MANUFACTURING, "800"),
    ("raw material", "原材料", "名詞", "A shortage of raw material delayed the entire production schedule.", MANUFACTURING, "550"),
    ("finished goods", "完成品", "名詞", "Finished goods are stored in the warehouse until they are shipped to customers.", MANUFACTURING, "600"),
    ("work order", "作業指示書", "名詞", "Each work order tells the technician exactly which parts to assemble.", MANUFACTURING, "650"),
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
