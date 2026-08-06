# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""Add professional / technical occupation vocabulary, authored by Claude
(2026-08-06・ユーザー要望: 総務省日本標準職業分類の「B 専門的・技術的職業
従事者」を土台にした現代日本の専門職語彙の追加)。

既存の domain='職業'(53件)は bartender, blacksmith, firefighter,
truck driver など主にブルーカラー・サービス職を中心とした職業語彙だった。
このスクリプトはそこに、医療・法律会計・教育研究・建築技術・
クリエイティブ/専門技術といった、日本標準職業分類の「専門的・技術的
職業従事者」に相当する現代日本の専門職を追加する:

- 医療系: surgeon, dentist, pharmacist, physical therapist,
  occupational therapist, radiologist, midwife, psychiatrist,
  psychologist, pediatrician, anesthesiologist
- 法律・会計系: tax accountant, certified public accountant,
  patent attorney, judicial scrivener, financial planner,
  insurance underwriter
- 教育・研究系: professor, researcher, librarian, school counselor,
  lecturer, archivist
- 建築・技術系: structural engineer, systems engineer,
  software engineer, web developer, data scientist,
  real estate appraiser
- クリエイティブ・専門技術系: translator, appraiser, social worker,
  management consultant, graphic designer, industrial designer,
  fashion designer, editor, journalist, announcer, game designer,
  animator, pilot, chiropractor, optometrist, acupuncturist

domain は既存の職業語彙に合わせて '職業' に統一。
level は ["300-","300","350","400","450","500","550","600","650","700",
"750","800","850","900","950","990","990+"] のスケールに沿って付与して
おり、一般によく知られる職業(dentist, pilot, professor など)は
400〜550、日本特有の資格・専門性の高い職業(judicial scrivener,
patent attorney, real estate appraiser, archivist など)は
750〜850とした。

事前に既存DB(words ~7000件)を全件チェックし、physician, veterinarian,
lawyer, judge, notary public, paralegal, curator, interpreter,
civil engineer, urban planner, actuary, surveyor, dietitian, architect,
nurse practitioner, optician, voice actor, sommelier, choreographer は
既に(domain='職業'または他domainに)存在することを確認済みのため、
このリストから除外している。既存の domain='職業' 53語との重複は
自動スキップされる。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_occupations_professional.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # 医療系
    ("surgeon", "外科医", "名詞", "The surgeon spent nearly six hours performing the operation.", "職業", "500"),
    ("dentist", "歯科医", "名詞", "I have an appointment with the dentist tomorrow morning.", "職業", "400"),
    ("pharmacist", "薬剤師", "名詞", "The pharmacist explained how to take the medicine safely.", "職業", "450"),
    ("physical therapist", "理学療法士", "名詞", "A physical therapist helped him regain movement in his knee.", "職業", "600"),
    ("occupational therapist", "作業療法士", "名詞", "An occupational therapist helps patients relearn daily tasks after an injury.", "職業", "700"),
    ("radiologist", "放射線科医", "名詞", "The radiologist reviewed the X-ray images and found no fractures.", "職業", "750"),
    ("midwife", "助産師", "名詞", "The midwife stayed with her throughout the entire delivery.", "職業", "650"),
    ("psychiatrist", "精神科医", "名詞", "He started seeing a psychiatrist after struggling with anxiety.", "職業", "650"),
    ("psychologist", "心理学者・心理カウンセラー", "名詞", "The psychologist recommended weekly counseling sessions.", "職業", "600"),
    ("pediatrician", "小児科医", "名詞", "Our pediatrician says the baby is growing right on schedule.", "職業", "600"),
    ("anesthesiologist", "麻酔科医", "名詞", "The anesthesiologist monitored his vital signs throughout the surgery.", "職業", "800"),
    # 法律・会計系
    ("tax accountant", "税理士", "名詞", "A tax accountant helped the company file its annual return.", "職業", "750"),
    ("certified public accountant", "公認会計士", "名詞", "She passed the exam and became a certified public accountant.", "職業", "800"),
    ("patent attorney", "弁理士", "名詞", "A patent attorney drafted the application for the new invention.", "職業", "850"),
    ("judicial scrivener", "司法書士", "名詞", "A judicial scrivener handled the property registration paperwork.", "職業", "850"),
    ("financial planner", "ファイナンシャルプランナー", "名詞", "A financial planner helped them set up a retirement savings plan.", "職業", "650"),
    ("insurance underwriter", "保険引受査定人", "名詞", "The insurance underwriter assessed the risk before approving the policy.", "職業", "800"),
    # 教育・研究系
    ("professor", "大学教授", "名詞", "She became a professor of economics at the age of thirty-five.", "職業", "500"),
    ("researcher", "研究者", "名詞", "The researcher published her findings in an international journal.", "職業", "450"),
    ("librarian", "図書館司書", "名詞", "The librarian helped me find books on Japanese history.", "職業", "450"),
    ("school counselor", "スクールカウンセラー", "名詞", "Students can talk to the school counselor about any personal problems.", "職業", "550"),
    ("lecturer", "講師", "名詞", "He works as a part-time lecturer at two different universities.", "職業", "500"),
    ("archivist", "記録保管専門家(アーキビスト)", "名詞", "The archivist carefully preserved the century-old documents.", "職業", "850"),
    # 建築・技術系
    ("structural engineer", "構造技術者", "名詞", "A structural engineer checked whether the building could withstand an earthquake.", "職業", "750"),
    ("systems engineer", "システムエンジニア", "名詞", "The systems engineer designed the company's new server network.", "職業", "550"),
    ("software engineer", "ソフトウェアエンジニア", "名詞", "She works as a software engineer at a tech startup.", "職業", "450"),
    ("web developer", "Web開発者", "名詞", "The web developer redesigned the company's online store.", "職業", "500"),
    ("data scientist", "データサイエンティスト", "名詞", "The data scientist built a model to predict customer behavior.", "職業", "600"),
    ("real estate appraiser", "不動産鑑定士", "名詞", "A real estate appraiser determined the fair market value of the house.", "職業", "850"),
    # クリエイティブ・専門技術系
    ("translator", "翻訳者", "名詞", "The translator worked all night to finish the document by morning.", "職業", "500"),
    ("appraiser", "鑑定士", "名詞", "An appraiser estimated the painting's value at over one million yen.", "職業", "700"),
    ("social worker", "ソーシャルワーカー", "名詞", "The social worker visited the family once a week to check on the children.", "職業", "600"),
    ("management consultant", "経営コンサルタント", "名詞", "The company hired a management consultant to improve its efficiency.", "職業", "700"),
    ("graphic designer", "グラフィックデザイナー", "名詞", "The graphic designer created the logo for the new brand.", "職業", "500"),
    ("industrial designer", "工業デザイナー", "名詞", "An industrial designer decides how a product looks and feels to use.", "職業", "700"),
    ("fashion designer", "ファッションデザイナー", "名詞", "The fashion designer unveiled her spring collection in Paris.", "職業", "500"),
    ("editor", "編集者", "名詞", "The editor reviewed the manuscript before it went to print.", "職業", "450"),
    ("journalist", "ジャーナリスト", "名詞", "The journalist interviewed several witnesses for her report.", "職業", "450"),
    ("announcer", "アナウンサー", "名詞", "The announcer read the evening news in a calm, clear voice.", "職業", "500"),
    ("game designer", "ゲームデザイナー", "名詞", "The game designer spent months balancing the difficulty levels.", "職業", "550"),
    ("animator", "アニメーター", "名詞", "The animator drew hundreds of frames for a single short scene.", "職業", "500"),
    ("pilot", "パイロット", "名詞", "The pilot announced that the flight would land ten minutes early.", "職業", "400"),
    ("chiropractor", "カイロプラクター", "名詞", "The chiropractor adjusted his spine to relieve the back pain.", "職業", "750"),
    ("optometrist", "検眼士", "名詞", "The optometrist checked her eyesight and prescribed new glasses.", "職業", "750"),
    ("acupuncturist", "鍼灸師", "名詞", "The acupuncturist inserted thin needles to ease his shoulder tension.", "職業", "700"),
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
