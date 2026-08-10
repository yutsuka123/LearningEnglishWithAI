# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add job-title vocabulary requested by the user to the existing "職業"
domain (公務員/技官/官僚/エンジニア各種/教師各種/経営陣の役職名等),
authored by Claude (2026-08-10)。

既存の`職業`ドメイン(386語)には`civil servant`/`police officer`/
`prosecutor`/`judicial scrivener`/`sales representative`/`lecturer`/
`carpenter`/`potter`/`woodworker`/`babysitter`/`systems engineer`/
`managing director`等が既に含まれる(重複追加しない)。`CEO`/`president`/
`chairman`/`director`/`vice president`は`ビジネス`ドメインに、
`electrician`は`生活`ドメインに、`technician`は`IT`ドメインに、
`skilled worker`は`製造`ドメインに既に存在するため、それらも重複追加
しない。

追加語: 公務員・官僚系(bureaucrat、technical government official
(技官)、budget examiner(主計官、財務省主計局の予算査定官)、
administrative scrivener(行政書士)、local government employee、
national government employee、bureau chief(局長)、institute
director(所長))、エンジニア各種(engineer(総称)、embedded engineer、
mechanical engineer、electrical engineer、electronic engineer、
designer、architect(既存だがdomain空欄のため実質未分類、ここでは
再追加せず既存語のまま)、radio operator(無線技士)、boiler engineer
(ボイラー技師)、lathe operator(旋盤工))、教師各種(elementary school
teacher、junior high school teacher、high school teacher、cram
school instructor(塾講師)、nursery teacher(保育士))、経営陣の役職名
(CTO、CPO、CIO、executive officer、senior managing director(専務)、
representative director(代表取締役)、board director(取締役))。

`architect`と`chairman`は既存だがdomainが空欄(過去のデータ不整合)の
ままだったため、このスクリプトで`職業`ドメインへ補正する(UPDATE)。

No app / OpenAI API calls — everything is hand-written and inserted/updated
directly in the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_occupations_expanded.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "職業"

# 既存語だがdomainが空欄のため補正する見出し(英語小文字で一致判定)。
FIX_DOMAIN_FOR = {"architect", "chairman"}

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 公務員・官僚系 ---
    ("bureaucrat", "官僚", "名詞", "The bureaucrat drafted the new regulation.", DOMAIN, "700"),
    ("technical government official", "技官", "名詞", "A technical government official reviewed the engineering plans.", DOMAIN, "800"),
    ("budget examiner", "主計官(財務省の予算査定官)", "名詞", "The budget examiner scrutinized every ministry's spending request.", DOMAIN, "850"),
    ("administrative scrivener", "行政書士", "名詞", "An administrative scrivener helped him prepare the visa application.", DOMAIN, "750"),
    ("local government employee", "地方公務員", "名詞", "She works as a local government employee in the city hall.", DOMAIN, "600"),
    ("national government employee", "国家公務員", "名詞", "He passed the exam to become a national government employee.", DOMAIN, "600"),
    ("bureau chief", "局長", "名詞", "The bureau chief approved the new policy.", DOMAIN, "700"),
    ("institute director", "所長", "名詞", "The institute director oversees all research projects.", DOMAIN, "650"),
    # --- エンジニア各種 ---
    ("engineer", "エンジニア・技師", "名詞", "She works as an engineer at a manufacturing company.", DOMAIN, "400"),
    ("embedded engineer", "組み込みエンジニア", "名詞", "The embedded engineer wrote firmware for the new device.", DOMAIN, "700"),
    ("mechanical engineer", "機械エンジニア", "名詞", "A mechanical engineer designed the new engine.", DOMAIN, "600"),
    ("electrical engineer", "電気エンジニア", "名詞", "The electrical engineer inspected the power system.", DOMAIN, "600"),
    ("electronic engineer", "電子エンジニア", "名詞", "The electronic engineer designed the circuit board.", DOMAIN, "600"),
    ("designer", "設計者・デザイナー", "名詞", "The designer created a new layout for the product.", DOMAIN, "400"),
    ("radio operator", "無線技士", "名詞", "A licensed radio operator manages the ship's communication equipment.", DOMAIN, "750"),
    ("boiler engineer", "ボイラー技師", "名詞", "The boiler engineer inspected the factory's heating system.", DOMAIN, "750"),
    ("lathe operator", "旋盤工", "名詞", "The lathe operator shaped the metal part with precision.", DOMAIN, "700"),
    # --- 教師各種 ---
    ("elementary school teacher", "小学校教師", "名詞", "She has been an elementary school teacher for ten years.", DOMAIN, "450"),
    ("junior high school teacher", "中学校教師", "名詞", "He teaches math as a junior high school teacher.", DOMAIN, "450"),
    ("high school teacher", "高校教師", "名詞", "The high school teacher prepared the students for their exams.", DOMAIN, "450"),
    ("cram school instructor", "塾講師", "名詞", "She works part-time as a cram school instructor.", DOMAIN, "600"),
    ("nursery teacher", "保育士", "名詞", "The nursery teacher looks after toddlers all day.", DOMAIN, "500"),
    # --- 経営陣の役職名 ---
    ("Chief Technology Officer (CTO)", "最高技術責任者(CTO)", "名詞", "The CTO oversees all of the company's engineering teams.", DOMAIN, "700"),
    ("Chief Product Officer (CPO)", "最高製品責任者(CPO)", "名詞", "The CPO decides the company's product roadmap.", DOMAIN, "750"),
    ("Chief Information Officer (CIO)", "最高情報責任者(CIO)", "名詞", "The CIO manages the company's IT strategy.", DOMAIN, "750"),
    ("executive officer", "執行役員", "名詞", "She was promoted to executive officer last year.", DOMAIN, "650"),
    ("senior managing director", "専務(取締役)", "名詞", "The senior managing director reports directly to the president.", DOMAIN, "750"),
    ("representative director", "代表取締役", "名詞", "He was appointed representative director of the company.", DOMAIN, "700"),
    ("board director", "取締役", "名詞", "She was elected as a board director at the shareholders' meeting.", DOMAIN, "650"),
    # --- 研究系(既存の"professor"/"researcher"とは別に、指示によりユーザーが
    #     追加を明示的に要望) ---
    ("research scientist", "研究員(自然科学系)", "名詞", "She works as a research scientist at a pharmaceutical company.", DOMAIN, "650"),
    ("postdoctoral researcher", "博士研究員(ポスドク)", "名詞", "He spent three years as a postdoctoral researcher before joining industry.", DOMAIN, "750"),
    ("lab technician", "実験技術員(ラボ技師)", "名詞", "The lab technician prepared the samples for testing.", DOMAIN, "600"),
    ("research assistant", "研究補助員", "名詞", "She worked as a research assistant during graduate school.", DOMAIN, "550"),
    ("principal investigator", "研究代表者(PI)", "名詞", "The principal investigator secured funding for the project.", DOMAIN, "800"),
    ("research fellow", "研究フェロー", "名詞", "He was appointed as a research fellow at the institute.", DOMAIN, "700"),
    ("associate professor", "准教授", "名詞", "She was promoted to associate professor last year.", DOMAIN, "650"),
    ("assistant professor", "助教", "名詞", "He just started as an assistant professor this semester.", DOMAIN, "650"),
    ("scholar", "学者・研究者", "名詞", "The scholar published a book on ancient history.", DOMAIN, "550"),
    ("graduate student", "大学院生", "名詞", "As a graduate student, she spends most of her time in the lab.", DOMAIN, "450"),
    ("doctoral student", "博士課程の学生", "名詞", "He's a doctoral student researching climate change.", DOMAIN, "550"),
]

PHRASES: list[tuple[str, str]] = [
    ("What do you do for a living?", "お仕事は何をされていますか？"),
    ("I work as an engineer at a tech company.", "テック企業でエンジニアとして働いています。"),
    ("She just passed the exam to become a civil servant.", "彼女はちょうど公務員試験に合格しました。"),
    ("He was promoted to bureau chief this spring.", "彼はこの春、局長に昇進しました。"),
    ("My father is a local government employee.", "父は地方公務員です。"),
    ("She's training to become a nursery teacher.", "彼女は保育士になるための研修を受けています。"),
    ("He teaches at a cram school in the evenings.", "彼は夜、塾で講師をしています。"),
    ("The CTO will present the new product roadmap.", "CTOが新しい製品ロードマップを発表します。"),
    ("She was appointed representative director last month.", "彼女は先月、代表取締役に就任しました。"),
    ("He's been a lathe operator for over twenty years.", "彼は20年以上、旋盤工をしています。"),
    ("We need a mechanical engineer for this project.", "このプロジェクトには機械エンジニアが必要です。"),
    ("An administrative scrivener can help with that paperwork.", "その書類は行政書士に手伝ってもらえます。"),
    ("He works as a boiler engineer at the plant.", "彼はその工場でボイラー技師として働いています。"),
]


def main() -> int:
    with db() as conn:
        fixed = 0
        for r in conn.execute(
            "SELECT id, english FROM words WHERE domain=''"
        ).fetchall():
            if r["english"].lower() in FIX_DOMAIN_FOR:
                conn.execute(
                    "UPDATE words SET domain=? WHERE id=?", (DOMAIN, r["id"])
                )
                fixed += 1
    print(f"domain fixed for orphaned rows: {fixed}")

    with db() as conn:
        existing_words = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing_words:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing_words.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")

    with db() as conn:
        existing_phrases = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in existing_phrases:
                p_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, '職業の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
