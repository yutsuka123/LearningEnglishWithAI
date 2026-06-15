# ruff: noqa: E501
"""Eiken (英検) vocabulary: 2級 / 準1級 / 1級. Authored by Claude — no
app/OpenAI API calls. Dedupe on english; back-fill empty examples. One domain
"英検", level by grade (2級=600 / 準1級=800 / 1級=900). 既存語と重複は自動
スキップ（基本語の多い2級は補充が中心）。

Run: python scripts/add_eiken.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# grade -> (level, [(english, japanese, example), ...])
GRADES: dict[str, tuple[str, list[tuple[str, str, str]]]] = {
    "英検2級": ("600", [
        ("achieve", "達成する", "She achieved her goal."),
        ("appreciate", "感謝する・理解する", "I appreciate your help."),
        ("aware", "気づいている", "Be aware of the risks."),
        ("benefit", "利益・恩恵", "Exercise has many benefits."),
        ("consider", "よく考える", "Please consider my offer."),
        ("decrease", "減少する", "Sales decreased last month."),
        ("encourage", "励ます・促す", "Teachers encourage students."),
        ("expand", "拡大する", "The company plans to expand."),
        ("familiar", "よく知っている", "I'm familiar with this area."),
        ("frequent", "頻繁な", "He is a frequent visitor."),
        ("gradually", "徐々に", "The sky gradually darkened."),
        ("ignore", "無視する", "Don't ignore the warning."),
        ("immediate", "即座の", "We need an immediate answer."),
        ("influence", "影響（する）", "Friends influence our choices."),
        ("obvious", "明らかな", "The mistake was obvious."),
        ("opportunity", "機会", "This is a great opportunity."),
        ("persuade", "説得する", "She persuaded him to stay."),
        ("prevent", "防ぐ", "Wash hands to prevent illness."),
        ("recognize", "認識する", "I recognized her voice."),
        ("require", "必要とする", "The job requires patience."),
        ("situation", "状況", "Explain the current situation."),
        ("suggest", "提案する", "I suggest we leave early."),
        ("survive", "生き延びる", "Few plants survive the cold."),
        ("various", "さまざまな", "We sell various products."),
        ("appropriate", "適切な", "Wear appropriate clothing."),
        ("attitude", "態度", "She has a positive attitude."),
        ("confident", "自信がある", "He felt confident before the test."),
        ("crucial", "極めて重要な", "Sleep is crucial for health."),
        ("efficient", "効率的な", "This engine is very efficient."),
        ("estimate", "見積もる", "Estimate the total cost."),
        ("generous", "気前のよい", "He is generous with his time."),
        ("intend", "意図する", "I intend to apply soon."),
        ("maintain", "維持する", "Maintain a steady speed."),
        ("occasion", "場合・行事", "Wear it on a special occasion."),
        ("permanent", "永久的な", "She found a permanent job."),
        ("reduce", "減らす", "We must reduce waste."),
        ("reliable", "信頼できる", "He is a reliable worker."),
        ("respond", "応答する", "Please respond by Friday."),
        ("specific", "具体的な", "Give a specific example."),
        ("tend", "〜しがちである", "Prices tend to rise in summer."),
    ]),
    "英検準1級": ("800", [
        ("abolish", "廃止する", "They voted to abolish the law."),
        ("accumulate", "蓄積する", "Dust accumulates over time."),
        ("alleviate", "和らげる", "The medicine alleviates the pain."),
        ("anticipate", "予期する", "We anticipate a busy season."),
        ("assess", "評価する", "Teachers assess each student."),
        ("attribute", "〜のせいにする・属性", "She attributes her success to luck."),
        ("compensate", "補償する", "The firm will compensate victims."),
        ("comply", "従う", "All staff must comply with the rules."),
        ("comprehensive", "包括的な", "A comprehensive plan is needed."),
        ("conceive", "思いつく・心に抱く", "He conceived a bold idea."),
        ("constitute", "構成する", "Twelve months constitute a year."),
        ("controversial", "論争を呼ぶ", "It was a controversial decision."),
        ("cope", "対処する", "She copes well under pressure."),
        ("deliberate", "意図的な・熟考する", "It was a deliberate act."),
        ("deteriorate", "悪化する", "His health deteriorated."),
        ("diminish", "減少する", "Interest gradually diminished."),
        ("distinguish", "区別する", "Distinguish fact from opinion."),
        ("enhance", "高める", "Spices enhance the flavor."),
        ("exaggerate", "誇張する", "Don't exaggerate the danger."),
        ("fluctuate", "変動する", "Prices fluctuate daily."),
        ("inevitable", "避けられない", "Change is inevitable."),
        ("integrate", "統合する", "We integrate the two systems."),
        ("intervene", "介入する", "The police intervened quickly."),
        ("justify", "正当化する", "Nothing can justify cruelty."),
        ("legitimate", "正当な・合法の", "She has a legitimate claim."),
        ("manipulate", "操作する", "He manipulated the data."),
        ("negotiate", "交渉する", "They negotiated a new deal."),
        ("obstacle", "障害", "Fear is the main obstacle."),
        ("persistent", "粘り強い・しつこい", "She made a persistent effort."),
        ("prominent", "著名な・目立つ", "He is a prominent scientist."),
        ("reluctant", "気が進まない", "She was reluctant to agree."),
        ("sufficient", "十分な", "We have sufficient supplies."),
        ("tremendous", "途方もない", "They made tremendous progress."),
        ("vulnerable", "傷つきやすい・脆弱な", "Children are vulnerable to scams."),
        ("advocate", "提唱する・支持者", "She advocates for reform."),
        ("ambiguous", "曖昧な", "The reply was ambiguous."),
        ("coincide", "同時に起こる・一致する", "Our visits coincided."),
        ("compatible", "互換性のある・相性のよい", "The parts are compatible."),
        ("contemplate", "熟考する", "He contemplated quitting."),
        ("inherent", "本来備わっている", "Risk is inherent in trade."),
    ]),
    "英検1級": ("900", [
        ("ubiquitous", "至る所にある", "Smartphones are now ubiquitous."),
        ("meticulous", "細心の・几帳面な", "She is meticulous about detail."),
        ("ephemeral", "はかない・短命の", "Fame can be ephemeral."),
        ("pragmatic", "実用的な・現実的な", "Take a pragmatic approach."),
        ("ambivalent", "相反する感情の", "He felt ambivalent about moving."),
        ("candid", "率直な", "She gave a candid opinion."),
        ("eloquent", "雄弁な", "He made an eloquent speech."),
        ("frugal", "倹約的な", "They live a frugal life."),
        ("gregarious", "社交的な", "She is naturally gregarious."),
        ("hamper", "妨げる", "Bad weather hampered the rescue."),
        ("impede", "妨げる", "Debt can impede growth."),
        ("inadvertent", "不注意の・うっかりした", "It was an inadvertent error."),
        ("lucrative", "もうかる", "It is a lucrative business."),
        ("nostalgia", "郷愁", "The song stirred nostalgia."),
        ("obsolete", "時代遅れの", "The format is now obsolete."),
        ("plausible", "もっともらしい", "That is a plausible excuse."),
        ("quintessential", "典型的な・真髄の", "It is the quintessential novel."),
        ("resilient", "回復力のある", "Children are remarkably resilient."),
        ("scrutinize", "綿密に調べる", "Auditors scrutinize the accounts."),
        ("tedious", "退屈な・単調な", "The work is tedious but easy."),
        ("unprecedented", "前例のない", "Sales hit unprecedented levels."),
        ("versatile", "多才な・万能の", "She is a versatile player."),
        ("austere", "厳格な・質素な", "The room had an austere look."),
        ("benevolent", "慈悲深い", "A benevolent donor helped them."),
        ("conspicuous", "目立つ", "He felt conspicuous in the crowd."),
        ("deteriorate", "悪化する", "Relations deteriorated further."),
        ("elusive", "とらえどころのない", "Success proved elusive."),
        ("fastidious", "気難しい・細かいことにこだわる", "He is fastidious about cleanliness."),
        ("gratuitous", "いわれのない・無償の", "The film has gratuitous violence."),
        ("hierarchy", "階層・序列", "The firm has a strict hierarchy."),
        ("impeccable", "完璧な・非の打ち所がない", "Her manners are impeccable."),
        ("juxtapose", "並置する", "The artist juxtaposes light and dark."),
        ("lethargic", "無気力な", "The heat made everyone lethargic."),
        ("meander", "曲がりくねる・とりとめなく進む", "The river meanders through the valley."),
        ("nonchalant", "無関心な・平然とした", "He gave a nonchalant shrug."),
        ("ostentatious", "見せびらかしの・派手な", "They live in an ostentatious house."),
        ("pertinent", "適切な・関連した", "Ask a pertinent question."),
        ("redundant", "余分な・冗長な", "Cut the redundant words."),
        ("sporadic", "散発的な", "There was sporadic applause."),
        ("tenacious", "粘り強い", "She is a tenacious negotiator."),
        ("vehement", "激しい・熱烈な", "He made a vehement protest."),
        ("whimsical", "気まぐれな", "The story has a whimsical tone."),
    ]),
}


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = filled = 0
        per_grade: dict[str, int] = {}
        for domain, (level, items) in GRADES.items():
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
                    (en, ja, "", ex, "英検", level),
                )
                existing.add(en.lower())
                added += 1
                per_grade[domain] = per_grade.get(domain, 0) + 1
    print(f"words: +{added} (例文補充 {filled})")
    print("内訳:", per_grade)
    with db() as conn:
        print("単語総数:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
