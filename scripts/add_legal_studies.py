# ruff: noqa: E501  (data-heavy seed script: long word/example lines are fine)
"""Extend the 法律(law) domain with 法学(legal studies / jurisprudence)
vocabulary, authored by Claude (2026-08-04・ユーザー要望:「法学」の語彙追加).

既存の法律(法)ドメイン(78件)は刑事法・民事訴訟の実務語彙
(acquittal, arrest, lawsuit, plaintiff, warrant 等)にほぼ偏っており、
法学・法理論そのものの語彙(法体系、法学理論、比較法・国際法、企業法務、
民法の各分野、法律ラテン語句、法曹の役職、法的文書)が欠けていた。
本スクリプトはそのギャップを埋める新規60語を同じ domain='法律' に追加する
(新規ドメインは作らない)。

投入前に既存78件および data/vocabulary.db の words テーブル全件
(6,330件, 2026-08-04時点)と英単語(小文字化・完全一致)で重複チェック済み。
以下は既存語と紛らわしいため意図的に置き換えた語:
  - "treaty"(歴史ドメインに既存) → ratification / extradition / diplomatic
    immunity で代替(単体の treaty は追加しない)
  - "merger"/"acquisition"(ビジネスドメインに既存) → "mergers and
    acquisitions" というフレーズ形にして重複を回避
  - "due diligence"(ビジネスドメインに既存) → "legal due diligence" と
    法務文脈を明示したフレーズで代替
  - "bar exam"(試験・資格ドメインに既存) → 追加せず、"bar association" を
    採用
  - "settlement"(ドメイン未設定で既存) → "settlement agreement" という
    フレーズ形で代替
  - "legal precedent" は既存の "precedent"(法律ドメイン)と意味が重複する
    ため追加を見送った

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_legal_studies.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 法体系・法理論 ---
    ("common law", "コモンロー・英米法(判例法主義)", "名詞", "The United States follows a common law system based largely on judicial precedent.", "法律", "700"),
    ("civil law system", "大陸法・成文法主義", "名詞", "France and Germany use a civil law system built on comprehensive legal codes.", "法律", "750"),
    ("case law", "判例法", "名詞", "Case law plays a much larger role in common law jurisdictions than in civil law ones.", "法律", "700"),
    ("stare decisis", "先例拘束の原則", "名詞", "Under the principle of stare decisis, lower courts must follow precedents set by higher courts.", "法律", "950"),
    ("legal reasoning", "法的推論", "名詞", "The judge laid out her legal reasoning in a lengthy written opinion.", "法律", "750"),
    ("statutory interpretation", "制定法の解釈", "名詞", "Statutory interpretation involves working out what the exact wording of a law actually means.", "法律", "800"),
    ("rule of law", "法の支配", "名詞", "The rule of law requires that everyone, including government officials, be subject to the law.", "法律", "700"),
    ("natural law", "自然法", "名詞", "Natural law theory holds that certain rights exist independently of any government or statute.", "法律", "850"),
    # --- 比較法・国際法 ---
    ("comparative law", "比較法", "名詞", "She studies comparative law to understand how legal systems differ from country to country.", "法律", "800"),
    ("international law", "国際法", "名詞", "International law governs relations and disputes between sovereign states.", "法律", "650"),
    ("ratification", "(条約などの)批准", "名詞", "The treaty could not take effect until it received ratification by the Senate.", "法律", "750"),
    ("extradition", "犯罪人引渡し", "名詞", "The fugitive was arrested abroad and now faces extradition to stand trial at home.", "法律", "800"),
    ("diplomatic immunity", "外交特権", "名詞", "Diplomats generally cannot be prosecuted locally because they are protected by diplomatic immunity.", "法律", "750"),
    # --- 企業法務・ビジネス法 ---
    ("corporate law", "会社法", "名詞", "He specializes in corporate law, advising companies on governance and compliance.", "法律", "700"),
    ("fiduciary duty", "受託者責任・忠実義務", "名詞", "Company directors owe a fiduciary duty to act in the best interests of shareholders.", "法律", "800"),
    ("shareholder rights", "株主権", "名詞", "The lawsuit alleged that management had trampled on shareholder rights.", "法律", "750"),
    ("mergers and acquisitions", "企業の合併・買収(M&A)", "名詞", "She works in the mergers and acquisitions division of an investment bank.", "法律", "750"),
    ("legal due diligence", "法務デューデリジェンス", "名詞", "Before closing the deal, the buyer's lawyers carried out extensive legal due diligence.", "法律", "800"),
    ("non-disclosure agreement", "秘密保持契約(NDA)", "名詞", "New contractors are required to sign a non-disclosure agreement before viewing the source code.", "法律", "700"),
    ("indemnification clause", "補償条項", "名詞", "The contract's indemnification clause protects the vendor against certain third-party claims.", "法律", "850"),
    ("force majeure", "不可抗力", "名詞", "The supplier invoked force majeure after the factory was destroyed by the earthquake.", "法律", "850"),
    ("arbitration clause", "仲裁条項", "名詞", "Most commercial contracts include an arbitration clause to avoid the cost of a trial.", "法律", "800"),
    ("governing law clause", "準拠法条項", "名詞", "The governing law clause states that any dispute will be resolved under New York law.", "法律", "800"),
    ("severability clause", "分離可能性条項", "名詞", "Thanks to the severability clause, the rest of the agreement stayed valid even after one section was struck down.", "法律", "850"),
    # --- 民法の各分野 ---
    ("tort law", "不法行為法", "名詞", "Tort law lets a person injured by someone else's negligence sue for damages.", "法律", "700"),
    ("contract law", "契約法", "名詞", "Contract law sets out the rules for forming and enforcing legally binding agreements.", "法律", "650"),
    ("property law", "財産法・不動産法", "名詞", "Property law governs the ownership, use, and transfer of land and buildings.", "法律", "650"),
    ("family law", "家族法", "名詞", "The firm's family law practice handles divorce, custody, and adoption cases.", "法律", "600"),
    ("labor law", "労働法", "名詞", "Labor law protects workers' rights to fair wages and safe working conditions.", "法律", "650"),
    ("administrative law", "行政法", "名詞", "Administrative law governs how government agencies create and enforce regulations.", "法律", "750"),
    ("constitutional law", "憲法学・憲法", "名詞", "Constitutional law scholars still debate how the founding document should be interpreted today.", "法律", "750"),
    # --- 法律ラテン語句 ---
    ("habeas corpus", "人身保護令状", "名詞", "The prisoner's lawyer filed a petition for habeas corpus to challenge his detention.", "法律", "950"),
    ("pro bono", "無償の・公益のための", "形容詞/副詞", "The law firm offers pro bono services to clients who cannot afford legal fees.", "法律", "800"),
    ("amicus curiae", "法廷助言者(意見書)", "名詞", "Several civil rights groups filed an amicus curiae brief supporting the plaintiff.", "法律", "950"),
    ("ex parte", "一方当事者のみによる", "形容詞", "The judge granted an ex parte order without first hearing from the other side.", "法律", "900"),
    ("in camera", "非公開で(裁判官の私室で)", "副詞/形容詞", "The sensitive testimony was heard in camera to protect the witness's identity.", "法律", "900"),
    ("prima facie", "一見して明白な", "形容詞", "The prosecutor presented prima facie evidence that the defendant had committed the crime.", "法律", "900"),
    ("mens rea", "犯意・故意", "名詞", "To convict someone of murder, the prosecution must prove mens rea, or criminal intent.", "法律", "950"),
    ("actus reus", "犯罪行為(客観的要素)", "名詞", "A crime generally requires both actus reus, the guilty act, and mens rea, the guilty mind.", "法律", "950"),
    ("res judicata", "既判力", "名詞", "Once a case has been finally decided, the doctrine of res judicata bars it from being tried again.", "法律", "990"),
    ("bona fide", "善意の・誠実な", "形容詞", "The court ruled that he was a bona fide purchaser with no knowledge of the earlier fraud.", "法律", "850"),
    ("de facto", "事実上の", "形容詞/副詞", "Although never officially appointed, she became the de facto head of the department.", "法律", "800"),
    ("de jure", "法律上の", "形容詞/副詞", "The new government was recognized de jure, not merely de facto.", "法律", "850"),
    ("quid pro quo", "対価・見返り", "名詞", "The scandal centered on an alleged quid pro quo between the official and the company.", "法律", "850"),
    # --- 法曹の役職 ---
    ("judge", "裁判官", "名詞", "The judge sentenced the defendant to five years in prison.", "法律", "450"),
    ("magistrate", "治安判事", "名詞", "The magistrate handles minor criminal cases and preliminary hearings.", "法律", "750"),
    ("notary public", "公証人", "名詞", "You'll need to have this document signed in front of a notary public.", "法律", "700"),
    ("bar association", "弁護士会", "名詞", "The state bar association investigates complaints of attorney misconduct.", "法律", "750"),
    ("litigator", "訴訟弁護士", "名詞", "As a litigator, she spends most of her time preparing for trial rather than drafting contracts.", "法律", "750"),
    ("in-house counsel", "社内弁護士", "名詞", "As in-house counsel, he reviews every major contract the company signs.", "法律", "750"),
    ("general counsel", "法務部長・最高法務責任者", "名詞", "The general counsel advises the CEO on all major legal risks facing the company.", "法律", "750"),
    # --- 法的文書・概念 ---
    ("affidavit", "宣誓供述書", "名詞", "She signed an affidavit swearing that every statement in it was true.", "法律", "750"),
    ("power of attorney", "委任状", "名詞", "He gave his daughter power of attorney to manage his finances while he was abroad.", "法律", "700"),
    ("last will and testament", "遺言書", "名詞", "In his last will and testament, he left the house to his youngest son.", "法律", "700"),
    ("escrow", "エスクロー(第三者預託)", "名詞", "The buyer's deposit is held in escrow until the sale is finalized.", "法律", "800"),
    ("injunctive relief", "差止め救済", "名詞", "The company sought injunctive relief to stop its rival from using the trademark.", "法律", "850"),
    ("class action", "集団訴訟", "名詞", "Thousands of customers joined the class action filed against the manufacturer.", "法律", "700"),
    ("settlement agreement", "和解契約書", "名詞", "Both parties signed a settlement agreement instead of proceeding to trial.", "法律", "650"),
    ("plea bargain", "司法取引", "名詞", "The defendant accepted a plea bargain and pleaded guilty to a lesser charge.", "法律", "700"),
    ("cease and desist", "停止命令(を出す)", "動詞句", "The company sent a cease and desist letter demanding that the imitation product be pulled from shelves.", "法律", "750"),
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
    with db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM words WHERE domain='法律'"
        ).fetchone()[0]
        print("domain 法律 total now:", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
