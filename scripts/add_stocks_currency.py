# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add stock-market and currency/forex vocabulary to the existing "経済学"
domain, authored by Claude (2026-08-10・ユーザー要望: 「株式用語(暴落/
暴騰/ストップ高/ストックオプション/上場/非上場/NASDAQ/東証 他)」と
「為替・通貨用語(円高/円安/ドル高/ドル安/通貨/紙幣/造幣局/中央銀行)」)。

既存の`経済学`ドメイン(75語)はマクロ/ミクロ経済理論・ゲーム理論・市場
構造の学術用語が中心(GDP, Nash equilibrium, bear market, bond, exchange
rate等)。今回はより実務的な株式市場・為替の語を補う。

事前にDBを確認し、`circuit breaker`は`電気電子`(電気回路のブレーカーの
意味)、`currency`は`旅行`(両替の文脈)、`mint`は`植物(身近な)`(ハーブの
ミントの意味)で別語義として既存のため、株式・通貨の文脈と明示する
複合見出し(`circuit breaker (stock market)`, `the Mint`)にした。
`currency`は既存語をそのまま使う想定で重複追加していない。

実在の証券取引所名(NASDAQ, Tokyo Stock Exchange)は一般的な固有名詞として
使用(実在の個別銘柄・企業名は使わない)。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_stocks_currency.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 株式用語 ---
    ("market crash", "市場の暴落", "名詞", "The market crash wiped out years of gains in a single day.", "経済学", "600"),
    ("stock rally", "株価の急騰", "名詞", "Tech stocks led a strong rally this week.", "経済学", "650"),
    ("limit up", "ストップ高(値幅制限の上限)", "名詞", "The stock hit its limit up shortly after the market opened.", "経済学", "800"),
    ("limit down", "ストップ安(値幅制限の下限)", "名詞", "Trading was suspended after the stock hit limit down.", "経済学", "800"),
    ("circuit breaker (stock market)", "サーキットブレーカー(取引の一時停止措置)", "名詞", "A circuit breaker halted trading after the sharp drop.", "経済学", "800"),
    ("stock option", "ストックオプション", "名詞", "New employees receive stock options as part of their compensation.", "経済学", "650"),
    ("initial public offering (IPO)", "新規株式公開(IPO)", "名詞", "The company's initial public offering was oversubscribed.", "経済学", "650"),
    ("go public", "上場する", "動詞", "The startup plans to go public next year.", "経済学", "600"),
    ("listed company", "上場企業", "名詞", "Listed companies must disclose their quarterly earnings.", "経済学", "600"),
    ("unlisted company", "非上場企業", "名詞", "As an unlisted company, they aren't required to disclose as much.", "経済学", "650"),
    ("delisting", "上場廃止", "名詞", "The stock faced delisting after failing to meet requirements.", "経済学", "750"),
    ("stock exchange", "証券取引所", "名詞", "Shares are traded on a stock exchange.", "経済学", "500"),
    ("NASDAQ", "ナスダック(米国の株式市場)", "名詞", "Many tech companies are listed on the NASDAQ.", "経済学", "550"),
    ("Tokyo Stock Exchange", "東京証券取引所(東証)", "名詞", "The Tokyo Stock Exchange is one of the largest in the world.", "経済学", "550"),
    ("dividend", "配当金", "名詞", "The company paid a dividend to its shareholders.", "経済学", "550"),
    ("stock split", "株式分割", "名詞", "The stock split made shares more affordable for small investors.", "経済学", "700"),
    ("blue-chip stock", "優良株(ブルーチップ株)", "名詞", "She prefers investing in blue-chip stocks for stability.", "経済学", "700"),
    ("penny stock", "低位株(ペニー株)", "名詞", "Penny stocks are known for being highly volatile.", "経済学", "750"),
    ("market capitalization", "時価総額", "名詞", "The company's market capitalization doubled in two years.", "経済学", "650"),
    # --- 為替・通貨用語 ---
    ("yen appreciation", "円高", "名詞", "Yen appreciation makes imports cheaper but hurts exporters.", "経済学", "600"),
    ("yen depreciation", "円安", "名詞", "Yen depreciation boosted profits for many exporters.", "経済学", "600"),
    ("dollar appreciation", "ドル高", "名詞", "Dollar appreciation made overseas travel more expensive for Americans.", "経済学", "600"),
    ("dollar depreciation", "ドル安", "名詞", "Dollar depreciation helped US exporters compete abroad.", "経済学", "600"),
    ("strong currency", "通貨高", "名詞", "A strong currency can hurt a country's export competitiveness.", "経済学", "600"),
    ("weak currency", "通貨安", "名詞", "A weak currency tends to boost tourism.", "経済学", "600"),
    ("currency intervention", "為替介入", "名詞", "The central bank conducted a currency intervention to slow the yen's fall.", "経済学", "750"),
    ("banknote", "紙幣", "名詞", "He paid with a ten-thousand-yen banknote.", "経済学", "450"),
    ("coin (currency)", "硬貨", "名詞", "Keep some coins for the vending machine.", "経済学", "350"),
    ("legal tender", "法定通貨", "名詞", "The yen is the legal tender in Japan.", "経済学", "700"),
    ("the Mint", "造幣局", "名詞", "The Mint is responsible for producing the country's coins.", "経済学", "650"),
    ("central bank", "中央銀行", "名詞", "The central bank raised interest rates to fight inflation.", "経済学", "500"),
    ("foreign exchange market", "外国為替市場", "名詞", "Trillions of dollars change hands in the foreign exchange market every day.", "経済学", "650"),
    ("currency peg", "通貨ペッグ(固定相場制)", "名詞", "The country maintains a currency peg to the US dollar.", "経済学", "800"),
    ("floating exchange rate", "変動相場制", "名詞", "Most major economies use a floating exchange rate.", "経済学", "750"),
]

PHRASES: list[tuple[str, str]] = [
    ("The market crashed after the announcement.", "その発表の後、市場は暴落しました。"),
    ("The stock hit limit up right at the open.", "その株は寄り付き直後にストップ高になりました。"),
    ("Trading was halted by a circuit breaker.", "サーキットブレーカーによって取引が一時停止されました。"),
    ("The company is planning to go public next spring.", "その会社は来春の上場を計画しています。"),
    ("Is this stock listed on the NASDAQ or the Tokyo Stock Exchange?", "この株はナスダックと東証、どちらに上場していますか？"),
    ("We offer stock options to all full-time employees.", "全ての正社員にストックオプションを付与しています。"),
    ("The company announced a dividend increase.", "その会社は増配を発表しました。"),
    ("Yen appreciation is putting pressure on exporters.", "円高が輸出企業にとって圧力になっています。"),
    ("The dollar weakened against the yen today.", "今日、ドルは円に対して下落しました。"),
    ("The central bank kept interest rates unchanged.", "中央銀行は金利を据え置きました。"),
    ("Do you have any coins for the vending machine?", "自動販売機用の硬貨はありますか？"),
    ("Could you break this banknote into smaller bills?", "この紙幣を細かくしてもらえますか？"),
    ("The government intervened in the currency market.", "政府は為替市場に介入しました。"),
    ("Blue-chip stocks tend to be less volatile.", "優良株は値動きが比較的穏やかな傾向があります。"),
    ("The company's market cap surpassed one trillion yen.", "その会社の時価総額は1兆円を超えました。"),
    ("Penny stocks can be risky for beginners.", "ペニー株は初心者にとってリスクが高いことがあります。"),
    ("A weaker currency usually helps tourism.", "自国通貨が安くなると通常、観光業に追い風になります。"),
    ("The stock was delisted after missing several filing deadlines.", "その株は提出期限を何度も逃した後、上場廃止になりました。"),
]


def main() -> int:
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
                "VALUES (?, ?, '経済学の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
