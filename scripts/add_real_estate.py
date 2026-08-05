# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""New 不動産(real estate) domain, authored by Claude (2026-08-05・ユーザー
要望:「不動産用語も　不動産のプロの用語　不動産売買用語　契約用語　不動産
の種類　不動産を買う借りる売るときに使う素人の用語」).

5カテゴリ構成: (1) 不動産業界のプロ用語、(2) 売買の実務用語、(3) 賃貸・
売買契約の用語、(4) 不動産の種類、(5) 買う/借りる/売るときに素人が実際に
使う語。既存DBには mortgage(ビジネス)/tenant・lease(生活)/apartment・
condominium・floor plan・duplex(建築・建物)/escrow・breach of contract
(法律)等が既に分散して存在するため、それらの裸の語は避け、不動産に特有の
複合語・専門語を中心に選定した。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words`
table.

Run:  python scripts/add_real_estate.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

D = "不動産"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 不動産のプロの用語 ---
    ("real estate agent", "不動産業者・仲介業者", "名詞", "A good real estate agent knows the neighborhood better than any website.", D, "500"),
    ("real estate broker", "不動産ブローカー・元受業者", "名詞", "A real estate broker can employ several agents under their license.", D, "700"),
    ("listing agent", "売主側の仲介業者", "名詞", "The listing agent represents the seller and markets the property.", D, "700"),
    ("buyer's agent", "買主側の仲介業者", "名詞", "A buyer's agent works only in the buyer's interest during the deal.", D, "700"),
    ("real estate commission", "仲介手数料", "名詞", "The real estate commission is usually a percentage of the sale price.", D, "700"),
    ("multiple listing service (MLS)", "不動産情報サービス（MLS）", "名詞", "Agents post new properties to the multiple listing service the same day.", D, "800"),
    ("comparable sales", "類似物件の取引事例", "名詞", "The agent used comparable sales in the area to set the asking price.", D, "800"),
    ("title search", "権利関係の調査", "名詞", "A title search confirms that the seller actually owns the property free and clear.", D, "800"),
    ("title insurance", "権利保険", "名詞", "Title insurance protects the buyer if a hidden ownership claim appears later.", D, "800"),
    ("fiduciary duty", "受託者としての義務・忠実義務", "名詞", "An agent's fiduciary duty means always acting in the client's best interest.", D, "850"),
    ("property appraiser", "不動産鑑定士", "名詞", "The property appraiser visited the house to estimate its current value.", D, "700"),
    ("property management company", "不動産管理会社", "名詞", "A property management company collects the rent and handles repairs for the owner.", D, "700"),
    ("due diligence (real estate)", "デューデリジェンス（不動産の事前調査）", "名詞", "Due diligence includes checking the title, the survey, and any zoning restrictions.", D, "800"),
    # --- 不動産売買用語 ---
    ("purchase offer", "購入の申し込み・オファー", "名詞", "The couple submitted a purchase offer just below the asking price.", D, "600"),
    ("counteroffer", "対抗提案・カウンターオファー", "名詞", "The seller sent back a counteroffer ten thousand dollars higher.", D, "700"),
    ("earnest money", "手付金", "名詞", "The buyer put down earnest money to show they were serious about the deal.", D, "800"),
    ("down payment", "頭金", "名詞", "They saved for years to afford a twenty percent down payment.", D, "500"),
    ("mortgage pre-approval", "住宅ローンの事前承認", "名詞", "Getting mortgage pre-approval tells sellers you can actually afford the house.", D, "800"),
    ("home inspection", "住宅診断・インスペクション", "名詞", "The home inspection found a small leak under the kitchen sink.", D, "600"),
    ("inspection contingency", "検査を条件とする特約", "名詞", "The inspection contingency lets the buyer walk away if serious problems turn up.", D, "850"),
    ("financing contingency", "融資を条件とする特約", "名詞", "The financing contingency protects the buyer if the mortgage loan falls through.", D, "850"),
    ("closing costs", "決済時諸費用", "名詞", "Closing costs usually add several thousand dollars on top of the purchase price.", D, "700"),
    ("closing date", "決済日・引渡し日", "名詞", "The closing date was pushed back two weeks because of a paperwork delay.", D, "600"),
    ("escrow account", "エスクロー口座", "名詞", "The deposit is held in an escrow account until the deal is finalized.", D, "800"),
    ("seller's disclosure", "売主による開示義務書類", "名詞", "The seller's disclosure listed a roof repair from three years earlier.", D, "800"),
    ("bidding war", "入札合戦・買付競争", "名詞", "Low inventory sparked a bidding war over the small starter home.", D, "750"),
    ("open house", "オープンハウス（内覧会）", "名詞", "Dozens of buyers walked through the open house on Sunday afternoon.", D, "500"),
    ("for-sale-by-owner (FSBO)", "仲介業者を通さない個人売買", "名詞", "Selling for-sale-by-owner saves the commission but means doing all the paperwork yourself.", D, "850"),
    # --- 契約用語 ---
    ("purchase agreement", "売買契約書", "名詞", "Both parties signed the purchase agreement in front of a notary.", D, "700"),
    ("lease agreement", "賃貸契約書", "名詞", "The lease agreement runs for exactly twelve months.", D, "600"),
    ("lease term", "賃貸借期間", "名詞", "The lease term can be renewed automatically unless either side gives notice.", D, "650"),
    ("security deposit", "敷金・保証金", "名詞", "The landlord kept part of the security deposit for cleaning fees.", D, "600"),
    ("notice to vacate", "退去通知", "名詞", "Tenants must give sixty days' notice to vacate before moving out.", D, "800"),
    ("renewal clause", "契約更新条項", "名詞", "The renewal clause lets the tenant extend the lease for another year.", D, "800"),
    ("termination clause", "契約解除条項", "名詞", "The termination clause allows either party to end the lease with proper notice.", D, "800"),
    ("sublease", "サブリース・転貸", "名詞", "She found someone to sublease her apartment while she studied abroad.", D, "750"),
    ("co-signer", "連署人・共同署名者", "名詞", "The landlord asked for a co-signer because the tenant had no rental history.", D, "800"),
    ("guarantor (lease)", "保証人（賃貸の）", "名詞", "A guarantor agrees to pay the rent if the tenant cannot.", D, "800"),
    ("month-to-month tenancy", "月次更新の賃貸借", "名詞", "A month-to-month tenancy can be ended by either side with short notice.", D, "850"),
    ("right of first refusal", "優先購入権", "名詞", "The right of first refusal lets the tenant buy the house before it's offered to anyone else.", D, "900"),
    # --- 不動産の種類 ---
    ("residential property", "住宅用不動産", "名詞", "Residential property includes everything from small apartments to large houses.", D, "650"),
    ("commercial property", "商業用不動産", "名詞", "Commercial property includes office buildings, shops, and warehouses.", D, "650"),
    ("detached house", "一戸建て（独立住宅）", "名詞", "They wanted a detached house with a yard for the dog.", D, "550"),
    ("semi-detached house", "セミデタッチトハウス（二軒続きの家）", "名詞", "A semi-detached house shares one wall with the house next door.", D, "800"),
    ("townhouse", "タウンハウス（連続住宅）", "名詞", "The townhouse has three floors but shares walls with its neighbors.", D, "650"),
    ("mixed-use building", "複合用途ビル", "名詞", "The mixed-use building has shops on the ground floor and apartments above.", D, "800"),
    ("vacant lot", "空き地・未利用地", "名詞", "The developer bought the vacant lot to build a new apartment complex.", D, "600"),
    ("investment property", "投資用不動産", "名詞", "They bought the small condo as an investment property to rent out.", D, "700"),
    ("single-family home", "一戸建て住宅（一世帯用）", "名詞", "The suburb is filled with single-family homes on quiet streets.", D, "600"),
    ("multi-family building", "多世帯住宅", "名詞", "A multi-family building can house several separate households under one roof.", D, "750"),
    # --- 買う・借りる・売るときの素人用語 ---
    ("move-in ready", "そのまま入居可能", "名詞", "The apartment was move-in ready, so they didn't need to fix anything first.", D, "600"),
    ("fixer-upper", "リフォーム前提の格安物件", "名詞", "They bought a cheap fixer-upper and spent a year renovating it.", D, "700"),
    ("curb appeal", "外観の第一印象・見栄え", "名詞", "Fresh paint and a tidy lawn can improve a house's curb appeal instantly.", D, "750"),
    ("square footage", "床面積（平方フィート）", "名詞", "The listing showed the square footage but not the number of bedrooms.", D, "650"),
    ("utilities included", "光熱費込み", "名詞", "The rent seemed high at first, but utilities included made it a fair deal.", D, "600"),
    ("pet-friendly rental", "ペット可の賃貸物件", "名詞", "They searched for months before finding a pet-friendly rental near the park.", D, "600"),
    ("walk-in closet", "ウォークインクローゼット", "名詞", "The main bedroom has a walk-in closet big enough for two people's clothes.", D, "550"),
    ("homeowners association fee (HOA fee)", "住宅所有者組合費（HOA費）", "名詞", "The monthly HOA fee covers landscaping and pool maintenance.", D, "800"),
    ("real estate listing", "不動産の売り物件情報", "名詞", "She scrolled through dozens of real estate listings before booking any viewings.", D, "600"),
    ("virtual property tour", "オンライン内覧・バーチャルツアー", "名詞", "A virtual property tour let them see the apartment without flying overseas.", D, "700"),
    ("lease renewal", "賃貸契約の更新", "名詞", "The landlord offered a lease renewal with only a small increase in rent.", D, "650"),
    ("rent increase", "賃料の値上げ", "名詞", "Tenants received a letter announcing a rent increase starting next month.", D, "600"),
    ("eviction notice", "立ち退き通知", "名詞", "The tenant received an eviction notice after missing three months of rent.", D, "800"),
    ("vacate the premises", "物件から退去する", "名詞", "The notice gave the tenant thirty days to vacate the premises.", D, "800"),
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
