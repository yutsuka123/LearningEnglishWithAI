# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add MANAGEMENT / CLERICAL / SALES occupation vocabulary, authored by Claude
(2026-08-06・ユーザー要望: 総務省日本標準職業分類の
「A 管理的職業従事者」「C 事務従事者」「D 販売従事者」を土台にした
職業語彙の追加)。

既存の domain='職業'(53語)は主に「B 専門的・技術的職業従事者」寄りの
専門職(actuary, air traffic controller, dietitian等)や、「G 生産工程」
「H 輸送・機械運転」「I 建設・採掘」寄りの現場職(blacksmith, roofer,
truck driver等)が中心で、オフィスワーク・経営管理・販売の語彙が
手薄だった。このスクリプトはそこに、日本標準職業分類の

- A 管理的職業従事者(経営・管理職) — department head, branch manager,
  general manager, HR manager, plant manager, board member,
  chief financial officer, chief operating officer, managing director,
  deputy manager, section chief, team leader
- C 事務従事者(一般事務・専門事務) — payroll clerk, accounting clerk,
  mail clerk, office administrator, administrative assistant,
  filing clerk, typist, bank teller, court clerk, inventory clerk,
  office clerk, billing clerk
- D 販売従事者(販売・営業) — insurance agent, sales representative,
  retail manager, purchasing agent, auctioneer, cashier, stockbroker,
  wholesaler, telemarketer, sales clerk, car salesperson, account manager

を中心にした語彙を追加する。domain は既存の職業語彙と同じ '職業' に
統一。level は ["300-","300","350","400","450","500","550","600","650",
"700","750","800","850","900","950","990","990+"] のスケールに沿って
付与しており、team leader / typist / cashier / sales clerk / office clerk
のような一般的な職業語は400〜550、chief financial officer / chief
operating officer / managing director / auctioneer / stockbroker /
court clerk のような専門性の高い語は650〜750とした。

事前に既存DB(words ~7000件)を全件チェックし、executive / CEO / director
/ supervisor / receptionist / secretary / vice president / real estate
agent / door-to-door salesperson / dispatcher / street vendor / real
estate broker / human resources manager 相当の語が既に存在する(domain
='ビジネス' 等)ことを確認済み。それらと重複する語はこのリストから除外
している。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_occupations_management_sales.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- A 管理的職業従事者(経営・管理職) ---
    ("department head", "部長", "名詞", "The department head approved the new budget proposal.", "職業", "550"),
    ("branch manager", "支店長", "名詞", "The branch manager oversees daily operations at this location.", "職業", "500"),
    ("general manager", "総支配人・統括マネージャー", "名詞", "She was promoted to general manager after five years with the company.", "職業", "550"),
    ("HR manager", "人事部長", "名詞", "The HR manager is handling all the new hire paperwork this week.", "職業", "550"),
    ("plant manager", "工場長", "名詞", "The plant manager is responsible for meeting the factory's production targets.", "職業", "600"),
    ("board member", "役員(取締役会メンバー)", "名詞", "Each board member votes on major company decisions.", "職業", "600"),
    ("chief financial officer", "最高財務責任者(CFO)", "名詞", "The chief financial officer presented the annual budget to shareholders.", "職業", "700"),
    ("chief operating officer", "最高執行責任者(COO)", "名詞", "As chief operating officer, he manages the company's day-to-day operations.", "職業", "700"),
    ("managing director", "常務取締役", "名詞", "The managing director signed off on the merger agreement.", "職業", "700"),
    ("deputy manager", "次長・副支店長", "名詞", "The deputy manager fills in whenever the manager is away.", "職業", "600"),
    ("section chief", "課長", "名詞", "The section chief reports directly to the department head.", "職業", "550"),
    ("team leader", "チームリーダー", "名詞", "Our team leader assigns tasks at the start of every week.", "職業", "400"),
    # --- C 事務従事者(一般事務・専門事務) ---
    ("payroll clerk", "給与計算事務員", "名詞", "The payroll clerk makes sure everyone is paid on time each month.", "職業", "600"),
    ("accounting clerk", "経理事務員", "名詞", "The accounting clerk enters invoices into the company's system.", "職業", "550"),
    ("mail clerk", "郵便係", "名詞", "The mail clerk sorts and delivers packages throughout the building.", "職業", "450"),
    ("office administrator", "総務担当者", "名詞", "The office administrator orders supplies and manages the front desk.", "職業", "550"),
    ("administrative assistant", "事務アシスタント", "名詞", "The administrative assistant scheduled the meeting for Thursday afternoon.", "職業", "500"),
    ("filing clerk", "ファイリング事務員", "名詞", "The filing clerk organizes documents by date and department.", "職業", "450"),
    ("typist", "タイピスト", "名詞", "The typist prepared the report from the manager's handwritten notes.", "職業", "400"),
    ("bank teller", "銀行窓口係", "名詞", "The bank teller helped me deposit a check this morning.", "職業", "450"),
    ("court clerk", "裁判所書記官", "名詞", "The court clerk recorded the judge's ruling in the case file.", "職業", "750"),
    ("inventory clerk", "棚卸し事務員", "名詞", "The inventory clerk counts stock in the warehouse every month.", "職業", "550"),
    ("office clerk", "事務員", "名詞", "The office clerk photocopies documents and answers the phone.", "職業", "400"),
    ("billing clerk", "請求書発行係", "名詞", "The billing clerk sends out invoices to customers each month.", "職業", "600"),
    # --- D 販売従事者(販売・営業) ---
    ("insurance agent", "保険代理店員", "名詞", "The insurance agent explained the different coverage options.", "職業", "550"),
    ("sales representative", "営業担当者", "名詞", "Our sales representative will contact you about the new product line.", "職業", "500"),
    ("retail manager", "小売店長", "名詞", "The retail manager trains new staff on customer service.", "職業", "550"),
    ("purchasing agent", "仕入れ担当者(購買担当者)", "名詞", "The purchasing agent negotiates prices with suppliers.", "職業", "600"),
    ("auctioneer", "競売人", "名詞", "The auctioneer sold the painting for twice its estimated value.", "職業", "750"),
    ("cashier", "レジ係", "名詞", "The cashier scanned my items and gave me the total.", "職業", "400"),
    ("stockbroker", "証券仲買人", "名詞", "The stockbroker advised her client to sell before the price dropped.", "職業", "700"),
    ("wholesaler", "卸売業者", "名詞", "The store buys most of its stock from a local wholesaler.", "職業", "600"),
    ("telemarketer", "テレマーケター(電話勧誘員)", "名詞", "A telemarketer called during dinner to offer a special deal.", "職業", "500"),
    ("sales clerk", "販売員", "名詞", "The sales clerk helped me find the right size.", "職業", "400"),
    ("car salesperson", "自動車販売員", "名詞", "The car salesperson showed us three different models.", "職業", "500"),
    ("account manager", "アカウントマネージャー(顧客担当者)", "名詞", "The account manager checks in with clients every quarter.", "職業", "650"),
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
