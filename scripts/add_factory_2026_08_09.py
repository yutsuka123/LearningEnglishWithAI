# ruff: noqa: E501
"""工場・製造現場語彙の拡充(2026-08-09)。

TODO.md「B20 工場・一次産業・手芸の語彙拡充」の工場用語部分に対応:
「品質管理／出荷検査／ライン／工程表／現場指導／移管(技術移管・生産
移管)」。既存の`製造`domain(21語)・`品質工学`domainには量産方式・
品質管理手法の基礎語は既にあったため、未登録の**現場運用・改善活動・
現場指導・移管**関連語を追加する。新規フレーズシーン`工場・製造現場の
英語`も新設。

Run:  python scripts/add_factory_2026_08_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "製造"
SCENE = "工場・製造現場の英語"

WORDS: list[tuple[str, str, str, str, str]] = [
    ("shipping inspection", "出荷検査", "名詞", "Every unit goes through a shipping inspection before it leaves the warehouse.", "550"),
    ("final inspection", "最終検査", "名詞", "The final inspection catches defects that earlier checks might have missed.", "550"),
    ("process chart", "工程表", "名詞", "The process chart shows every step from raw material to finished product.", "600"),
    ("routing sheet", "ルーティングシート（加工手順書）", "名詞", "The routing sheet lists which machines the part passes through and in what order.", "700"),
    ("on-site guidance", "現場指導", "名詞", "A senior engineer provided on-site guidance to the new operators.", "600"),
    ("technology transfer", "技術移管", "名詞", "The technology transfer took several months as engineers trained the local staff.", "650"),
    ("production transfer", "生産移管", "名詞", "The production transfer moved manufacturing from the old plant to the new one.", "650"),
    ("genba", "現場（実際に価値が生み出される作業現場）", "名詞", "Genba walks let managers see the actual work happening on the shop floor.", "650"),
    ("5S", "5S（整理・整頓・清掃・清潔・躾の職場改善活動）", "名詞", "The team practices 5S to keep the workstation organized and efficient.", "650"),
    ("andon", "アンドン（異常を知らせる表示灯・掲示板）", "名詞", "Pulling the andon cord stops the line the moment a problem is found.", "700"),
    ("jidoka", "自働化（異常検知で自動停止する仕組み）", "名詞", "Jidoka lets a machine stop itself automatically the instant it detects a defect.", "750"),
    ("muda", "ムダ（付加価値を生まない無駄）", "名詞", "Identifying muda is the first step toward a leaner process.", "700"),
    ("standard work", "標準作業", "名詞", "Standard work defines the safest, most efficient way to perform each task.", "600"),
    ("line balancing", "ラインバランシング（各工程の作業時間を均等化すること）", "名詞", "Line balancing spreads the workload evenly so no single station becomes a bottleneck.", "700"),
    ("changeover time", "段取り替え時間", "名詞", "Reducing changeover time lets the line switch between products faster.", "650"),
    ("preventive maintenance", "予防保全", "名詞", "Preventive maintenance is scheduled before a machine actually breaks down.", "600"),
    ("predictive maintenance", "予知保全", "名詞", "Predictive maintenance uses sensor data to predict failures before they happen.", "700"),
    ("work cell", "ワークセル（複数工程を担当する小規模な作業単位）", "名詞", "Workers in the work cell handle several steps of assembly in one compact area.", "700"),
    ("value stream mapping", "バリューストリームマッピング", "名詞", "Value stream mapping visualizes every step, delay, and handoff in the process.", "750"),
    ("manufacturing execution system", "製造実行システム（MES）", "名詞", "The manufacturing execution system tracks every unit in real time as it moves through the plant.", "750"),
    ("shop floor", "現場（工場の生産フロア）", "名詞", "Decisions made in the office don't always reflect what's happening on the shop floor.", "550"),
    ("production supervisor", "製造現場監督者", "名詞", "The production supervisor reassigned workers to cover the shortage.", "550"),
    ("skilled worker", "熟練工", "名詞", "It takes years for a skilled worker to master that level of precision.", "500"),
]

PHRASES: list[tuple[str, str]] = [
    ("We need to schedule a shipping inspection before the order goes out.", "出荷前に出荷検査を予定する必要があります。"),
    ("Can you walk me through the process chart for this part?", "この部品の工程表を説明してもらえますか。"),
    ("The engineer is here to give on-site guidance to the new hires.", "そのエンジニアは新人に現場指導をするために来ています。"),
    ("The technology transfer is scheduled to finish by the end of the quarter.", "技術移管は今四半期末までに完了する予定です。"),
    ("Let's go do a genba walk before the meeting.", "会議の前に現場を見て回りましょう。"),
    ("We're implementing 5S across the entire shop floor.", "工場全体で5Sを導入しています。"),
    ("Someone pulled the andon cord on line two.", "2号ラインでアンドンの紐が引かれました。"),
    ("Jidoka stopped the machine before it produced any more defective parts.", "自働化のおかげで、これ以上の不良品を作る前に機械が止まりました。"),
    ("Let's find and eliminate the muda in this process.", "この工程からムダを見つけて排除しましょう。"),
    ("We cut the changeover time in half after retraining the operators.", "オペレーターの再教育後、段取り替え時間を半分に短縮できました。"),
    ("Preventive maintenance is scheduled for this weekend.", "今週末に予防保全を予定しています。"),
    ("The MES flagged an anomaly on station four.", "MES（製造実行システム）が4番ステーションの異常を検知しました。"),
    ("What does the standard work sheet say about this step?", "この工程については標準作業手順書にどう書かれていますか。"),
    ("We're moving this task to a dedicated work cell.", "この作業は専用のワークセルに移す予定です。"),
    ("It takes at least three years to become a skilled worker on this line.", "このラインで熟練工になるには少なくとも3年かかります。"),
]


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }

        w_added = w_skipped = 0
        for en, ja, pos, ex, level in WORDS:
            if en.lower() in w_existing:
                w_skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, DOMAIN, level),
            )
            w_existing.add(en.lower())
            w_added += 1

        ph_added = ph_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in ph_existing:
                ph_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) VALUES (?, ?, ?)",
                (en, ja, SCENE),
            )
            ph_existing.add(en.lower())
            ph_added += 1

    print(f"words: +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
