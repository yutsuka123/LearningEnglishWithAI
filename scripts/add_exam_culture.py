# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""Bulk-add curated words for EXAM CULTURE vocabulary, authored by Claude.

ユーザー要望(2026-08-09): 「試験のところには日本独特の偏差値、他追加、
米国英国独特なものも追加。あとは筆記試験・口頭試験・予備校・塾・合格・
不合格・補欠合格・試験官・カンニング、他」に対応。既存の`試験・資格`
domain(国際的な試験制度の実務語彙)を補う形で、(1)日本特有の受験文化語
(2)米国・英国特有の試験文化語 (3)一般的な試験語彙、の3カテゴリを追加する。

既存語との衝突に注意: "ronin"は既に職業domainで「浪人(主君を持たない
武士)」の意味で登録済みのため、受験の「浪人」は"exam ronin"として別語彙
にした(既存の`add_exam_certification.py`が"test admission ticket"等で
採った手法と同じ)。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased).

Run:  python scripts/add_exam_culture.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# (english, japanese, part_of_speech, example, domain, level)
WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 一般的な試験語彙 ---
    ("pass", "（試験に）合格する", "動詞", "She studied hard and passed the exam with a great score.", "試験・資格", "350"),
    ("flunk", "（試験に）落ちる・不合格になる（口語）", "動詞", "He flunked the final and had to retake the class.", "試験・資格", "700"),
    ("examiner", "試験官（口述・実技試験の評価者）", "名詞", "The examiner asked her to explain her answer in more detail.", "試験・資格", "600"),
    ("cheat", "（試験で）カンニングする・不正行為をする", "動詞", "He was caught cheating during the exam and disqualified.", "試験・資格", "450"),
    ("cheat sheet", "カンニングペーパー（本来は要点をまとめた虎の巻の意）", "名詞", "She smuggled a cheat sheet into the exam room.", "試験・資格", "550"),
    ("plagiarism", "剽窃・盗用", "名詞", "Copying a classmate's essay word for word is plagiarism.", "試験・資格", "750"),
    ("written exam", "筆記試験", "名詞", "The driving test includes both a written exam and a road test.", "試験・資格", "500"),
    ("oral exam", "口頭試験", "名詞", "He was nervous before his oral exam in French.", "試験・資格", "650"),
    ("viva", "口述試験（英、特に大学院の論文審査）", "名詞", "She successfully defended her thesis at her viva.", "試験・資格", "850"),
    ("pop quiz", "抜き打ちテスト", "名詞", "Nobody expected the pop quiz on Friday afternoon.", "試験・資格", "550"),
    ("midterm exam", "中間試験", "名詞", "Midterm exams are held in the seventh week of the semester.", "試験・資格", "500"),
    ("final exam", "期末試験・最終試験", "名詞", "I still have three final exams left this week.", "試験・資格", "450"),
    ("take-home exam", "持ち帰り試験", "名詞", "The professor gave us a take-home exam instead of an in-class one.", "試験・資格", "700"),
    ("cram", "（試験前に）一夜漬けで詰め込み勉強する", "動詞", "I crammed all night before the chemistry exam.", "試験・資格", "600"),
    # --- 米国・英国特有の試験文化語 ---
    ("SAT", "SAT（米国の大学進学適性試験）", "名詞", "Many American high schoolers take the SAT junior year.", "試験・資格", "600"),
    ("ACT", "ACT（米国のもう一つの大学進学適性試験）", "名詞", "Some students take both the SAT and the ACT.", "試験・資格", "650"),
    ("GPA", "GPA（成績評価平均値）", "名詞", "A high GPA can help with scholarship applications.", "試験・資格", "600"),
    ("valedictorian", "首席卒業生（卒業式で答辞を述べる成績最優秀の生徒、米）", "名詞", "The valedictorian gave a moving speech at graduation.", "試験・資格", "800"),
    ("legacy admission", "レガシー入学（卒業生の子女らが優遇される米大学の入学制度）", "名詞", "The university has faced criticism over legacy admission.", "試験・資格", "850"),
    ("Ivy League", "アイビーリーグ（米国東部の名門私立大学群）", "名詞", "He was accepted into an Ivy League university.", "試験・資格", "650"),
    ("A-level", "Aレベル（英国の大学進学に使われる科目別統一試験）", "名詞", "Her A-level grades were good enough for Oxford.", "試験・資格", "750"),
    ("GCSE", "GCSE（英国の中等教育修了資格試験）", "名詞", "Students in England sit their GCSE exams at around sixteen.", "試験・資格", "800"),
    ("Oxbridge", "オックスブリッジ（オックスフォード大学とケンブリッジ大学の総称、英）", "名詞", "Getting an Oxbridge offer is famously competitive.", "試験・資格", "750"),
    ("blue book", "ブルーブック（米大学の記述式試験で使う答案用の小冊子）", "名詞", "Please write your essay answers in the blue book provided.", "試験・資格", "800"),
    # --- 日本特有の受験文化語 ---
    ("hensachi", "偏差値（平均を50とする日本独自の相対的学力指標）", "名詞", "Her hensachi went up five points after the summer break.", "試験・資格", "750"),
    ("naishinten", "内申点（成績や態度など学校側の評価による点数、高校受験等で使う）", "名詞", "Naishinten is combined with the exam score for the final decision.", "試験・資格", "800"),
    ("safety school", "滑り止め校（確実に合格できそうな併願校）", "名詞", "He applied to a safety school just in case.", "試験・資格", "600"),
    ("exam ronin", "浪人（受験に失敗し翌年の再受験を目指して勉強する学生）", "名詞", "She spent a year as an exam ronin before getting into her first-choice university.", "試験・資格", "750"),
    ("cram school", "塾（学校外で行う補習・受験対策の塾）", "名詞", "Many kids in Japan go to cram school after regular school.", "試験・資格", "550"),
    ("exam prep school", "予備校（大学受験に特化した進学塾、浪人生も多く通う）", "名詞", "He enrolled in an exam prep school for his second attempt.", "試験・資格", "700"),
    ("waitlisted pass", "補欠合格（合格圏内だが定員超過のため繰り上げ合格を待つこと）", "名詞", "He got a waitlisted pass and was admitted a month later.", "試験・資格", "800"),
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

    print(f"words: +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print("total words:", conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
