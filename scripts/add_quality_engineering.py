# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Top up the thin 品質工学(quality engineering) domain, authored by Claude
(2026-08-04・ユーザー要望: 「品質工学...も必要かな」).

既存の品質工学ドメインは14語のみで、しかも scripts/add_quality_supplier.py が
入れた不具合調査・是正処置まわりの語彙(root cause, countermeasure,
traceability, containment...)に偏っていた。統計的工程管理(SPC)と品質
マネジメントシステム(QMS)側の語彙が丸ごと欠けていたため、この2領域を
中心に補強する:

  - Six Sigma / DMAIC / SPC / 管理図 / 工程能力(Cpk) / 実験計画法(DOE) /
    タグチメソッド / ポカヨケ / カイゼン / なぜなぜ分析 / 特性要因図 /
    パレート図 といった統計的品質管理の手法群
  - QC/QA、ISO 9001、QMS、検査(受入・工程内・出荷)、校正証明書、
    ゲージR&R、破壊/非破壊試験、8Dレポート、CAPA、根本原因分析といった
    品質マネジメント・監査の定型語彙
  - 歩留まり率・不良率・PPM・廃棄率・手直しといった品質指標

重複回避のため、投入前に既存 words テーブルを実際にクエリして確認済み。
"benchmark"（ビジネス domain）と "quarantine"（IT domain, サイバー
セキュリティの意味で既存）は完全一致の重複になるため、より具体的な
"benchmarking" と "quarantine area" に言い換えて別語として追加している。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_quality_engineering.py

仕上げ: 投入後に必要なら `python scripts/relevel.py` 等で難易度を確認する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 統計的品質管理(SPC)・改善手法 ---
    ("Six Sigma", "シックスシグマ", "名詞", "The plant adopted Six Sigma to reduce variation across all production lines.", "品質工学", "750"),
    ("DMAIC", "DMAIC(定義・測定・分析・改善・管理)", "名詞", "We're following the DMAIC framework: define, measure, analyze, improve, control.", "品質工学", "900"),
    ("statistical process control", "統計的工程管理(SPC)", "名詞", "Statistical process control lets us catch drift before it becomes a defect.", "品質工学", "800"),
    ("control chart", "管理図", "名詞", "The control chart showed three consecutive points above the upper limit.", "品質工学", "700"),
    ("process capability", "工程能力", "名詞", "We ran a process capability study before approving the new supplier.", "品質工学", "750"),
    ("Cpk", "工程能力指数(Cpk)", "名詞", "A Cpk below 1.33 means the process isn't capable enough for this tolerance.", "品質工学", "900"),
    ("design of experiments", "実験計画法(DOE)", "名詞", "We used design of experiments to find the optimal weld parameters.", "品質工学", "850"),
    ("Taguchi method", "タグチメソッド・田口メソッド", "名詞", "The Taguchi method helped us find a robust setting despite material variation.", "品質工学", "900"),
    ("poka-yoke", "ポカヨケ", "名詞", "We added a poka-yoke fixture so the part can't be installed backwards.", "品質工学", "800"),
    ("kaizen", "カイゼン・改善", "名詞", "Our kaizen event cut the changeover time in half.", "品質工学", "650"),
    ("five whys", "なぜなぜ分析・5why分析", "名詞", "The five whys took us from 'the machine stopped' to a worn sensor.", "品質工学", "750"),
    ("Ishikawa diagram", "特性要因図(石川ダイアグラム)", "名詞", "We built an Ishikawa diagram to map every possible cause of the defect.", "品質工学", "850"),
    ("fishbone diagram", "フィッシュボーン図", "名詞", "The fishbone diagram grouped the causes into material, method, machine, and man.", "品質工学", "750"),
    ("Pareto chart", "パレート図", "名詞", "The Pareto chart showed that two defect types account for eighty percent of complaints.", "品質工学", "800"),
    ("PDCA cycle", "PDCAサイクル", "名詞", "We run a PDCA cycle every time we introduce a new countermeasure.", "品質工学", "800"),
    ("quality circle", "品質サークル・QCサークル", "名詞", "The quality circle meets every week to discuss small process improvements.", "品質工学", "800"),
    ("continuous improvement", "継続的改善", "名詞", "Continuous improvement is part of the culture here, not just a slogan.", "品質工学", "650"),
    ("benchmarking", "ベンチマーキング", "名詞", "We did some benchmarking against two other suppliers before choosing this process.", "品質工学", "700"),
    # --- 品質マネジメントシステム(QMS)・認証 ---
    ("quality control", "品質管理", "名詞", "Quality control rejected the batch for exceeding the porosity limit.", "品質工学", "600"),
    ("quality assurance", "品質保証", "名詞", "Quality assurance signed off on the process before mass production started.", "品質工学", "650"),
    ("ISO 9001", "ISO9001", "名詞", "Our supplier is ISO 9001 certified, so their QMS is audited every year.", "品質工学", "750"),
    ("quality management system", "品質マネジメントシステム(QMS)", "名詞", "Their quality management system covers everything from incoming inspection to shipping.", "品質工学", "750"),
    ("standard operating procedure", "標準作業手順(SOP)", "名詞", "The operator wasn't following the standard operating procedure.", "品質工学", "700"),
    ("cost of quality", "品質コスト", "名詞", "The cost of quality includes both prevention and the cost of failures.", "品質工学", "850"),
    ("critical to quality", "品質に重要な(特性)", "名詞句", "This dimension is critical to quality, so it gets one-hundred-percent inspection.", "品質工学", "900"),
    # --- 検査・測定 ---
    ("sampling inspection", "抜取検査", "名詞", "We switched from one-hundred-percent inspection to sampling inspection once the process stabilized.", "品質工学", "750"),
    ("acceptance criteria", "合格基準", "名詞", "The acceptance criteria for this dimension is plus or minus 0.05 millimeters.", "品質工学", "700"),
    ("incoming inspection", "受入検査", "名詞", "This defect should have been caught at incoming inspection.", "品質工学", "700"),
    ("outgoing inspection", "出荷検査", "名詞", "Outgoing inspection missed the scratch because it was under the label.", "品質工学", "700"),
    ("in-process inspection", "工程内検査", "名詞", "In-process inspection catches most defects before final assembly.", "品質工学", "750"),
    ("first article inspection", "初品検査", "名詞", "First article inspection is required before we approve mass production.", "品質工学", "800"),
    ("inspection lot", "検査ロット", "名詞", "The entire inspection lot was quarantined pending the investigation.", "品質工学", "750"),
    ("quality gate", "品質ゲート", "名詞", "The part can't move to the next station until it clears the quality gate.", "品質工学", "700"),
    ("calibration certificate", "校正証明書", "名詞", "Every gauge on the floor needs a valid calibration certificate.", "品質工学", "750"),
    ("gauge R&R", "測定システム分析(ゲージR&R)", "名詞", "We ran a gauge R&R study and found the measurement system itself was the problem.", "品質工学", "950"),
    ("destructive testing", "破壊試験", "名詞", "Destructive testing confirmed the weld strength met the requirement.", "品質工学", "750"),
    ("non-destructive testing", "非破壊試験", "名詞", "We use non-destructive testing so the part can still be shipped afterward.", "品質工学", "750"),
    ("batch record", "バッチ記録・製造記録", "名詞", "Please attach the batch record to the deviation report.", "品質工学", "750"),
    # --- 統計限界・ばらつき ---
    ("control limit", "管理限界", "名詞", "The measurement fell outside the control limit, so we stopped the line.", "品質工学", "800"),
    ("upper specification limit", "上限規格値", "名詞", "Anything above the upper specification limit gets scrapped.", "品質工学", "850"),
    ("lower specification limit", "下限規格値", "名詞", "This reading is right at the lower specification limit.", "品質工学", "850"),
    ("out-of-control process", "管理外れの工程", "名詞句", "An out-of-control process needs an assignable cause before you can fix it.", "品質工学", "800"),
    ("common cause variation", "偶然原因によるばらつき", "名詞", "Common cause variation is built into the process and can't be fixed by blaming operators.", "品質工学", "850"),
    ("special cause variation", "異常原因によるばらつき", "名詞", "A tool change usually shows up as special cause variation on the chart.", "品質工学", "850"),
    # --- 指標・不具合対応 ---
    ("first pass yield", "初回良品率", "名詞", "First pass yield dropped after we switched to the new resin.", "品質工学", "850"),
    ("defect rate", "不良率", "名詞", "The defect rate on line two is higher than on line one.", "品質工学", "700"),
    ("parts per million", "百万分率(PPM)", "名詞", "We're targeting a defect level below fifty parts per million.", "品質工学", "750"),
    ("defect density", "欠陥密度", "名詞", "Defect density per unit dropped after we improved the fixture.", "品質工学", "800"),
    ("escape rate", "流出率", "名詞", "The escape rate to the customer is the number we really care about.", "品質工学", "800"),
    ("yield rate", "歩留まり率", "名詞", "The yield rate improved after we adjusted the oven temperature profile.", "品質工学", "700"),
    ("scrap rate", "廃棄率・スクラップ率", "名詞", "The scrap rate on this line is well above the target.", "品質工学", "750"),
    ("rework", "手直し・再加工", "名詞/動詞", "These units need rework before they can be shipped.", "品質工学", "650"),
    ("quarantine area", "隔離保管エリア", "名詞", "Move the suspect parts to the quarantine area until we finish sorting.", "品質工学", "750"),
    ("zero defects", "ゼロディフェクト・欠陥ゼロ", "名詞句", "Zero defects is the goal, even if it's rarely fully achieved.", "品質工学", "750"),
    ("right first time", "一発合格・初回合格", "名詞句", "Our target is to get it right first time, not to rely on inspection.", "品質工学", "800"),
    ("8D report", "8Dレポート", "名詞", "Please submit the 8D report within five business days of the complaint.", "品質工学", "900"),
    ("corrective and preventive action", "是正予防処置(CAPA)", "名詞", "The audit finding requires a corrective and preventive action within thirty days.", "品質工学", "850"),
    ("root cause analysis", "根本原因分析", "名詞", "A thorough root cause analysis takes longer than everyone would like.", "品質工学", "750"),
]


# --- phrases: (english, japanese), scene='品質工学の英語' -------------------

PHRASES: list[tuple[str, str]] = [
    ("What's the Cpk for this process?", "この工程のCpkはいくつですか。"),
    ("We need a corrective action plan by Friday.", "金曜日までに是正処置計画が必要です。"),
    ("This defect escaped to the customer.", "この不具合は顧客まで流出してしまいました。"),
    ("Is this within the control limits?", "これは管理限界内に収まっていますか。"),
    ("The process went out of control on the night shift.", "夜勤の時間帯に工程が管理外れを起こしました。"),
    ("Let's run a gauge R&R study before we trust these measurements.", "この測定値を信用する前にゲージR&R試験を実施しましょう。"),
    ("Can you show me the control chart for the last month?", "先月分の管理図を見せていただけますか。"),
    ("We need an 8D report for this complaint.", "このクレームについて8Dレポートが必要です。"),
    ("What's driving the defect rate up this quarter?", "今四半期、不良率が上昇している要因は何ですか。"),
    ("Let's do a five-whys to get to the real root cause.", "本当の根本原因にたどり着くため5whys分析をしましょう。"),
    ("This lot failed the incoming inspection.", "このロットは受入検査で不合格でした。"),
    ("We're implementing poka-yoke to prevent this from happening again.", "再発防止のためポカヨケを導入します。"),
    ("How many PPM are we running on this line?", "このラインの不良率は何PPMですか。"),
    ("These parts are on quality hold until we finish the investigation.", "調査が完了するまで、この部品は品質保留の状態です。"),
    ("We passed the ISO 9001 surveillance audit.", "ISO 9001のサーベイランス監査に合格しました。"),
    ("This looks like a special cause, not normal variation.", "これは特殊原因のようで、通常のばらつきではなさそうです。"),
]


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        w_added = w_skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in w_existing:
                w_skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            w_existing.add(en.lower())
            w_added += 1

        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        ph_added = ph_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in ph_existing:
                ph_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, '品質工学の英語')",
                (en, ja),
            )
            ph_existing.add(en.lower())
            ph_added += 1

    print(f"words:   +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    with db() as conn:
        print(
            "domain total now:",
            conn.execute(
                "SELECT COUNT(*) FROM words WHERE domain='品質工学'"
            ).fetchone()[0],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
