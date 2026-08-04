# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated words & phrases for INTERNATIONAL EXAMS / CERTIFICATIONS,
authored by Claude.

Focus (フレーズ集・単語集の手薄な領域を補強): 海外の資格試験・検定試験まわりの
語彙と、試験そのもので使われる「指示文・出題文の型」（メタ言語）。既存の
`英検`ドメイン（英検の語彙レベルに合わせた一般的な高難度語彙）とは別に、
"proctor"（試験監督官・米）/"invigilator"（同・英）、"band score"（IELTS）、
"testing accommodation"（受験上の配慮＝宿泊施設の意味の accommodation とは別）、
"test admission ticket"（受験票＝遊園地等の入場券の意味の admission ticket とは
別）など、国際的な試験・資格制度に特有の語彙を扱う（domain="試験・資格"）。

フレーズは2つの場面に分けた:
  - 「試験の指示・出題フレーズ」: 試験問題・試験監督が使う指示文・出題文の
    定型表現。内容（英語力）がわかっていても、この「試験特有の言い回し」に
    不慣れだと戸惑う受験者が多いため、意図的に手厚くしてある。
  - 「試験の手続き英語」: 受験申し込み・スコア照会・再採点依頼・日程変更・
    配慮申請・資格更新など、試験を取り巻く実務的なやり取りの表現。

既存語との衝突を避けるため、"admission ticket"（アウトドア・レジャー domain
の遊園地入場券の意味で既存）は "test admission ticket" に、"accommodation"
（旅行 domain の宿泊施設の意味で既存）は "testing accommodation" にそれぞれ
言い換えて別語彙として登録した。同様に "candidate" "certificate" "transcript"
"deadline" "registration" "reschedule" "appeal" 等の一般語も既存語と重複しない
よう、"exam candidate" "certificate of completion" "official transcript"
"registration deadline" "grade appeal" 等の複合語で試験文脈の語義を補った。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_exam_certification.py
      python scripts/add_exam_certification.py --missing-words   # report only

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- phrases: scene -> [(english, japanese)] --------------------------------

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "試験の指示・出題フレーズ": [
        # --- 出題形式・選択の指示 ---
        ("Choose the best answer from the following options.", "次の選択肢の中から最も適切な答えを選びなさい。"),
        ("Which of the following is NOT true?", "次のうち正しくないものはどれですか。"),
        ("Choose the correct option (A, B, C, or D).", "正しい選択肢（A、B、C、Dのいずれか）を選びなさい。"),
        ("Which choice best completes the sentence?", "どの選択肢が文を最も適切に完成させますか。"),
        ("Select all that apply.", "該当するものをすべて選びなさい。"),
        ("This question has multiple correct answers.", "この問題には複数の正解があります。"),
        ("True or False: ...", "正誤問題：〜"),
        # --- 長文読解の定型表現 ---
        ("According to the passage, ...", "文章によると、〜"),
        ("The word 'X' in paragraph 2 is closest in meaning to...", "第2段落の「X」という単語に意味が最も近いのは〜"),
        ("Read the following passage and answer the questions below.", "次の文章を読み、下の設問に答えなさい。"),
        ("Based on the information in the passage, what can be inferred?", "文章の情報から、何が推測できますか。"),
        ("The passage suggests that...", "文章は〜であることを示唆している。"),
        ("What is the main idea of the passage?", "文章の要旨は何ですか。"),
        ("In the context of the passage, 'X' most nearly means...", "文章の文脈において「X」に最も近い意味は〜"),
        # --- 記入・マーク方法の指示 ---
        ("Mark your answer on the answer sheet.", "解答用紙に解答をマークしなさい。"),
        ("Fill in the blank with the correct word.", "正しい単語で空欄を埋めなさい。"),
        ("Circle the correct answer.", "正しい答えを丸で囲みなさい。"),
        ("Write your answer in the space provided.", "指定のスペースに解答を記入しなさい。"),
        ("Please write your name in the box provided.", "指定された枠内に氏名を記入してください。"),
        ("Use a No. 2 pencil to fill in the bubbles.", "マーク欄はNo.2の鉛筆で塗りつぶしてください。"),
        ("Erase completely if you change your answer.", "解答を変更する場合は完全に消してください。"),
        ("Do not write outside the designated area.", "指定された範囲の外には書き込まないでください。"),
        ("Match the words on the left with their definitions on the right.", "左の単語と右の定義を一致させなさい。"),
        ("Complete the sentence with the correct form of the verb.", "動詞を正しい形にして文を完成させなさい。"),
        ("Answer in complete sentences.", "完全な文で答えなさい。"),
        ("Show your work for full credit.", "満点を得るには途中の計算過程を示しなさい。"),
        ("Round your answer to the nearest whole number.", "答えを最も近い整数に四捨五入しなさい。"),
        # --- 時間・配点・構成 ---
        ("You have 30 minutes to complete this section.", "このセクションを終えるのに30分の時間があります。"),
        ("Time is up. Please put your pencils down.", "時間切れです。鉛筆を置いてください。"),
        ("Stop working when time is called.", "時間になったら作業をやめてください。"),
        ("Each question is worth X points.", "各問題の配点はX点です。"),
        ("This section is worth 25% of your total score.", "このセクションは総得点の25%を占めます。"),
        ("If you finish early, you may review your answers.", "早く終わった場合は解答を見直して構いません。"),
        ("This exam consists of three sections.", "この試験は3つのセクションで構成されています。"),
        # --- 持ち込み物・電子機器・不正行為 ---
        ("You may not use a calculator for this section.", "このセクションでは電卓の使用は認められません。"),
        ("No electronic devices are permitted in the exam room.", "試験室内では電子機器の使用は認められません。"),
        ("This is a closed-book exam.", "これは持ち込み不可の試験です。"),
        ("You may refer to your notes during this section.", "このセクションではノートを参照して構いません。"),
        ("There is no penalty for guessing.", "推測して解答しても減点はありません。"),
        ("Cheating will result in disqualification.", "カンニングをすると失格になります。"),
        # --- 開始・進行・リスニング ---
        ("Do not open this booklet until instructed.", "指示があるまでこの冊子を開かないでください。"),
        ("Keep your booklet closed until told to begin.", "開始の合図があるまで冊子を閉じたままにしてください。"),
        ("Turn to the next page and continue.", "次のページに進み、続けてください。"),
        ("You will hear each recording only once.", "各録音は一度しか流れません。"),
        ("You will hear each recording twice.", "各録音は二度流れます。"),
        ("Please remain seated until all papers are collected.", "すべての解答用紙が回収されるまで着席していてください。"),
        ("Raise your hand if you have a question.", "質問がある場合は挙手してください。"),
        ("Read each question carefully before answering.", "解答する前に各設問をよく読みなさい。"),
    ],
    "試験の手続き英語": [
        # --- 申し込み・料金・日程 ---
        ("How do I register for the exam?", "試験にはどうやって申し込めばいいですか。"),
        ("What is the registration deadline?", "申し込みの締め切りはいつですか。"),
        ("How much is the exam fee?", "受験料はいくらですか。"),
        ("Is there a late registration fee?", "遅延登録料はかかりますか。"),
        ("Is walk-in registration available?", "当日受付は可能ですか。"),
        ("Can I get a refund if I cancel?", "キャンセルした場合、返金してもらえますか。"),
        ("Can I reschedule my exam date?", "試験日を変更することはできますか。"),
        ("Is there a waitlist for this exam date?", "この受験日にはキャンセル待ちがありますか。"),
        ("Can I switch testing centers?", "試験会場を変更することはできますか。"),
        ("What happens if I miss my exam?", "試験を欠席した場合はどうなりますか。"),
        ("Do you accept exam fee waivers for low-income applicants?", "低所得の受験者向けの受験料免除は受け付けていますか。"),
        # --- 当日の持ち物・受験環境 ---
        ("What ID do I need to bring?", "どの身分証明書を持参する必要がありますか。"),
        ("Do I need to bring my own calculator?", "自分の電卓を持参する必要がありますか。"),
        ("Do I need to arrive early on exam day?", "試験当日は早めに到着する必要がありますか。"),
        ("I never received my admission ticket.", "受験票がまだ届いていません。"),
        ("Can I take the exam remotely?", "試験をリモートで受けることはできますか。"),
        ("What's the difference between the paper-based and computer-based test?", "紙ベースの試験とコンピューターベースの試験の違いは何ですか。"),
        # --- 配慮申請 ---
        ("I'd like to request testing accommodations.", "受験上の配慮をお願いしたいのですが。"),
        ("Do you offer extended time for students with disabilities?", "障がいのある受験者に延長時間の措置はありますか。"),
        # --- 結果・スコア照会 ---
        ("When will the results be released?", "結果はいつ発表されますか。"),
        ("Where can I check my exam status online?", "オンラインで受験状況を確認できるのはどこですか。"),
        ("Can you email me a copy of my score report?", "スコアレポートのコピーをメールで送ってもらえますか。"),
        ("What should I do if I lose my score report?", "スコアレポートを紛失した場合はどうすればいいですか。"),
        ("How long is my score valid?", "私のスコアはいつまで有効ですか。"),
        ("Can I send my scores to multiple universities?", "スコアを複数の大学に送付することはできますか。"),
        ("What's the passing score for this certification?", "この資格の合格点はいくつですか。"),
        ("What's the difference between a pass mark and a scaled score?", "合格基準点と換算得点の違いは何ですか。"),
        # --- 再採点・異議申し立て・再受験 ---
        ("How do I request a rescore?", "再採点はどのように依頼すればいいですか。"),
        ("How do I appeal my grade?", "成績にはどうやって異議申し立てをすればいいですか。"),
        ("I'd like to file an appeal for question 12.", "12番の問題について異議申し立てをしたいのですが。"),
        ("How many times can I retake the exam?", "この試験は何回まで再受験できますか。"),
        # --- 資格・免許の有効性と更新 ---
        ("Is my certification still valid?", "私の資格はまだ有効ですか。"),
        ("Is this certification recognized internationally?", "この資格は国際的に認められていますか。"),
        ("When does my license expire?", "私の免許はいつ失効しますか。"),
        ("How do I renew my professional license?", "職業免許はどうやって更新すればいいですか。"),
        ("Do I need continuing education credits to renew?", "更新には継続教育単位が必要ですか。"),
        ("How do I get my transcript sent to the certification body?", "成績証明書を認定機関に送付してもらうにはどうすればいいですか。"),
        # --- 申請状況の確認 ---
        ("I'd like to check the status of my application.", "申請状況を確認したいのですが。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("proctor", "試験監督官（米）", "名詞", "The proctor collected all the answer sheets at the end.", "試験・資格", "700"),
    ("invigilator", "試験監督官（英）", "名詞", "The invigilator walked around the room during the exam.", "試験・資格", "750"),
    ("exam candidate", "受験者", "名詞", "Each exam candidate must show a valid photo ID.", "試験・資格", "600"),
    ("testing center", "試験会場・受験センター", "名詞", "The testing center opens thirty minutes before the exam.", "試験・資格", "550"),
    ("test admission ticket", "受験票", "名詞", "Print your test admission ticket before exam day.", "試験・資格", "600"),
    ("score report", "成績報告書・スコアレポート", "名詞", "Your score report will be available online in two weeks.", "試験・資格", "600"),
    ("band score", "バンドスコア（IELTSの得点）", "名詞", "She got a band score of 7.5 on the IELTS.", "試験・資格", "700"),
    ("superscore", "スーパースコア（複数回の最高点合算）", "名詞", "Some universities superscore your SAT results across attempts.", "試験・資格", "850"),
    ("retake", "再受験する・再受験", "動詞", "You can retake the exam after ninety days.", "試験・資格", "600"),
    ("exam fee", "受験料", "名詞", "The exam fee must be paid before registration closes.", "試験・資格", "550"),
    ("testing accommodation", "受験上の配慮", "名詞", "She requested a testing accommodation for extra time.", "試験・資格", "750"),
    ("exam waitlist", "受験のキャンセル待ち", "名詞", "I put my name on the exam waitlist for that date.", "試験・資格", "700"),
    ("certification body", "認定機関", "名詞", "The certification body sets the standards for the exam.", "試験・資格", "700"),
    ("accreditation", "認定", "名詞", "The program lost its accreditation last year.", "試験・資格", "750"),
    ("passing score", "合格点", "名詞", "You need a passing score of 60% to pass.", "試験・資格", "550"),
    ("pass mark", "合格基準点（英）", "名詞", "The pass mark for this test is 70 out of 100.", "試験・資格", "600"),
    ("scaled score", "換算得点", "名詞", "Your raw score is converted into a scaled score.", "試験・資格", "800"),
    ("percentile rank", "パーセンタイル順位", "名詞", "A percentile rank of 90 means you scored higher than 90% of test takers.", "試験・資格", "850"),
    ("cut score", "合格基準スコア", "名詞", "The committee raised the cut score this year.", "試験・資格", "850"),
    ("exam waiver", "試験免除", "名詞", "She qualified for an exam waiver based on her work experience.", "試験・資格", "800"),
    ("prerequisite", "履修前提条件", "名詞", "This course is a prerequisite for the certification exam.", "試験・資格", "700"),
    ("continuing education credit", "継続教育単位", "名詞", "Nurses must earn continuing education credits every year.", "試験・資格", "800"),
    ("professional certification", "職業資格認定", "名詞", "He earned a professional certification in project management.", "試験・資格", "700"),
    ("license renewal", "免許更新", "名詞", "License renewal is required every three years.", "試験・資格", "650"),
    ("proctored exam", "監督付き試験", "名詞", "The course ends with a proctored exam.", "試験・資格", "700"),
    ("multiple-choice question", "選択式問題", "名詞", "Most of the test consists of multiple-choice questions.", "試験・資格", "500"),
    ("essay section", "記述式セクション", "名詞", "The essay section is graded separately.", "試験・資格", "600"),
    ("listening section", "リスニングセクション", "名詞", "The listening section comes first in the test.", "試験・資格", "500"),
    ("speaking test", "スピーキングテスト", "名詞", "The speaking test is conducted one-on-one with an examiner.", "試験・資格", "550"),
    ("writing prompt", "ライティング課題文", "名詞", "Read the writing prompt carefully before you start.", "試験・資格", "700"),
    ("answer sheet", "解答用紙", "名詞", "Make sure your name is on the answer sheet.", "試験・資格", "450"),
    ("answer key", "模範解答", "名詞", "The teacher posted the answer key after class.", "試験・資格", "500"),
    ("scratch paper", "下書き用紙・計算用紙", "名詞", "You may use scratch paper for calculations.", "試験・資格", "650"),
    ("photo ID", "写真付き身分証明書", "名詞", "Bring a valid photo ID to the testing center.", "試験・資格", "500"),
    ("exam registration", "受験申し込み", "名詞", "Exam registration closes two weeks before the test date.", "試験・資格", "600"),
    ("registration deadline", "出願締切", "名詞", "Don't miss the registration deadline for the spring exam.", "試験・資格", "600"),
    ("score validity", "スコアの有効期限", "名詞", "Check the score validity period before you apply.", "試験・資格", "800"),
    ("official transcript", "公式成績証明書", "名詞", "Universities require an official transcript with your application.", "試験・資格", "700"),
    ("standardized test", "標準化試験", "名詞", "The SAT is a well-known standardized test.", "試験・資格", "650"),
    ("grading curve", "採点調整（下駄を履かせる）", "名詞", "The professor applied a grading curve to the final exam.", "試験・資格", "800"),
    ("grade appeal", "成績への異議申し立て", "名詞", "He filed a grade appeal after reviewing his exam.", "試験・資格", "800"),
    ("rescore", "再採点する", "動詞", "You can request to rescore your essay for a fee.", "試験・資格", "750"),
    ("no-show fee", "無断欠席料", "名詞", "A no-show fee applies if you don't attend without notice.", "試験・資格", "800"),
    ("late registration fee", "遅延登録料", "名詞", "A late registration fee is charged after the deadline.", "試験・資格", "700"),
    ("testing window", "受験可能期間", "名詞", "The testing window is open for three months.", "試験・資格", "750"),
    ("exam session", "試験回・セッション", "名詞", "She chose the earliest available exam session.", "試験・資格", "600"),
    ("credential evaluation", "資格評価", "名詞", "A credential evaluation compares your degree to local standards.", "試験・資格", "850"),
    ("accredited institution", "認定校", "名詞", "Make sure the school is an accredited institution.", "試験・資格", "750"),
    ("certificate of completion", "修了証明書", "名詞", "You will receive a certificate of completion after the course.", "試験・資格", "550"),
    ("recertification", "資格更新", "名詞", "Recertification is required every five years.", "試験・資格", "800"),
    ("exam anxiety", "試験不安", "名詞", "Deep breathing can help reduce exam anxiety.", "試験・資格", "650"),
    ("open-book exam", "持ち込み可の試験", "名詞", "This is an open-book exam, so you can use your textbook.", "試験・資格", "600"),
    ("closed-book exam", "持ち込み不可の試験", "名詞", "The final is a closed-book exam.", "試験・資格", "600"),
    ("timed test", "時間制限付き試験", "名詞", "Practice with a timed test to build speed.", "試験・資格", "550"),
    ("score cancellation", "スコア取り消し", "名詞", "Score cancellation must be requested within a few days of the test.", "試験・資格", "850"),
    ("entrance exam", "入学試験", "名詞", "She studied for months for the entrance exam.", "試験・資格", "500"),
    ("placement test", "プレースメントテスト", "名詞", "New students take a placement test before classes begin.", "試験・資格", "550"),
    ("mock exam", "模擬試験", "名詞", "We took a mock exam last weekend.", "試験・資格", "550"),
    ("pass rate", "合格率", "名詞", "The pass rate for the bar exam dropped this year.", "試験・資格", "650"),
    ("bar exam", "司法試験", "名詞", "He is studying for the bar exam.", "試験・資格", "700"),
    ("board exam", "（医師等の）国家試験", "名詞", "Doctors must pass a board exam to practice.", "試験・資格", "700"),
    ("diagnostic test", "診断テスト", "名詞", "The diagnostic test shows your current level.", "試験・資格", "600"),
]


# --- insertion --------------------------------------------------------------

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")
_STOP = {
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on", "at",
    "for", "with", "from", "by", "as", "is", "are", "was", "were", "be", "been",
    "do", "does", "did", "have", "has", "had", "will", "would", "can", "could",
    "should", "may", "might", "must", "i", "you", "he", "she", "it", "we",
    "they", "me", "him", "her", "us", "them", "my", "your", "his", "its", "our",
    "their", "this", "that", "these", "those", "here", "there", "what", "when",
    "where", "who", "how", "why", "not", "no", "yes", "so", "up", "out", "off",
    "down", "let", "lets", "please", "thanks", "thank", "ok", "okay", "im",
    "ill", "id", "ive", "dont", "cant", "wont", "isnt", "thats", "whats",
    "very", "just", "too", "more", "some", "any", "all", "one", "two", "get",
    "got", "go", "going", "like", "want", "need", "make", "made", "take",
    "see", "now", "today", "tonight", "good", "well", "back", "about", "over",
    "into", "than", "then", "again", "really", "much", "many", "wish", "mind",
    "could", "would", "shall", "rather", "ever", "way", "one's", "off",
    "before", "later", "earlier", "second", "gist", "point", "way", "say",
    "saying", "sure", "understand", "following", "pick", "leave", "there",
}


def _content_words(phrases: list[tuple[str, str]]) -> set[str]:
    out: set[str] = set()
    for en, _ in phrases:
        for tok in _WORD_RE.findall(en.lower()):
            w = tok.strip("'-")
            if len(w) >= 4 and w not in _STOP:
                out.add(w)
    return out


def report_missing() -> None:
    """Print content words used in the new phrases that are not yet in `words`
    and not covered by the WORDS list above (authoring aid)."""
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
    covered = {w[0].lower() for w in WORDS}
    all_phrases = [p for lst in PHRASES_BY_SCENE.values() for p in lst]
    missing = sorted(
        w for w in _content_words(all_phrases)
        if w not in existing and w not in covered
    )
    print(f"missing content words ({len(missing)}):")
    print(", ".join(missing))


def main() -> int:
    if "--missing-words" in sys.argv:
        report_missing()
        return 0

    with db() as conn:
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }

        ph_added = ph_skipped = 0
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in ph_existing:
                    ph_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                ph_existing.add(en.lower())
                ph_added += 1

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

    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    print(f"words:   +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print("totals -> phrases:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0],
              "words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
