# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""Web/SNS/ネット販売の宣伝文句＋SEO＋LLMO(新設ドメイン「Web・SEO・LLMO」),
authored by Claude (2026-08-05・ユーザー要望:「フレーズ　web　sns　ネット
販売などの宣伝文句　seo　llmoに関連したフレーズ英単語」).

LLMOはSEO(検索エンジン最適化)に対して、ChatGPT等のAIチャット/生成AI検索に
自社コンテンツが引用・言及されやすくする最適化を指す新しい概念。既存の
「call to action」(プレゼン・教える技術)は既存のため裸の語は避けた。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words`
table.

Run:  python scripts/add_web_marketing_seo_llmo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

D = "Web・SEO・LLMO"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- Web/SNS/ネット販売の宣伝文句 ---
    ("limited-time offer", "期間限定オファー", "名詞", "The limited-time offer expires at midnight on Sunday.", D, "600"),
    ("flash sale", "フラッシュセール（数時間限定の特売）", "名詞", "The flash sale sold out within twenty minutes.", D, "650"),
    ("early bird discount", "早期予約割引", "名詞", "Customers who order this week get an early bird discount.", D, "650"),
    ("free shipping", "送料無料", "名詞", "Free shipping applies to any order over fifty dollars.", D, "500"),
    ("money-back guarantee", "返金保証", "名詞", "The product comes with a thirty-day money-back guarantee.", D, "650"),
    ("best-seller", "ベストセラー・売れ筋商品", "名詞", "This model has been our best-seller for three years running.", D, "550"),
    ("game-changer", "ゲームチェンジャー（革新的な存在）", "名詞", "Reviewers called the new feature a real game-changer.", D, "700"),
    ("sold out", "売り切れ", "形容詞", "The limited edition sneakers were sold out within an hour.", D, "500"),
    ("restock", "再入荷（する）", "名詞・動詞", "The item will restock next Tuesday, according to the website.", D, "600"),
    ("coupon code", "クーポンコード", "名詞", "Enter the coupon code at checkout to get ten percent off.", D, "550"),
    ("referral program", "紹介プログラム", "名詞", "The referral program rewards both the friend and the new customer.", D, "700"),
    ("loyalty program", "ロイヤルティプログラム（会員特典制度）", "名詞", "Members of the loyalty program earn points on every purchase.", D, "700"),
    ("unboxing", "開封動画・アンボクシング", "名詞", "Her unboxing video of the new phone got millions of views.", D, "700"),
    ("testimonial", "利用者の声・推薦文", "名詞", "The landing page features a testimonial from a satisfied customer.", D, "700"),
    ("giveaway", "プレゼント企画", "名詞", "The brand ran a giveaway to celebrate reaching one million followers.", D, "650"),
    ("follower count", "フォロワー数", "名詞", "Her follower count doubled after the video went viral.", D, "600"),
    ("engagement rate", "エンゲージメント率", "名詞", "A high engagement rate matters more to brands than follower count alone.", D, "750"),
    ("viral post", "バイラル投稿・拡散した投稿", "名詞", "The viral post was shared over a hundred thousand times.", D, "650"),
    ("hashtag campaign", "ハッシュタグキャンペーン", "名詞", "The hashtag campaign encouraged fans to post their own photos.", D, "700"),
    ("influencer marketing", "インフルエンサーマーケティング", "名詞", "Influencer marketing let the small brand reach a much larger audience.", D, "750"),
    ("brand ambassador", "ブランドアンバサダー", "名詞", "The athlete became a brand ambassador for the sportswear company.", D, "700"),
    ("user-generated content", "ユーザー生成コンテンツ（UGC）", "名詞", "User-generated content feels more trustworthy than traditional advertising.", D, "800"),
    ("sponsored content", "スポンサードコンテンツ", "名詞", "The article was clearly labeled as sponsored content.", D, "750"),
    # --- ネット販売・EC ---
    ("e-commerce", "電子商取引・EC", "名詞", "E-commerce sales grew rapidly during the pandemic.", D, "600"),
    ("checkout page", "決済ページ", "名詞", "A confusing checkout page can cause customers to abandon their cart.", D, "650"),
    ("cart abandonment", "カート放棄", "名詞", "Cart abandonment often happens when shipping costs appear too late.", D, "800"),
    ("upsell", "アップセル（する）", "名詞・動詞", "The salesperson tried to upsell her to the premium package.", D, "750"),
    ("cross-sell", "クロスセル（する）", "名詞・動詞", "The website cross-sells accessories whenever a customer buys a phone.", D, "800"),
    ("product listing", "商品出品情報", "名詞", "A clear product listing includes accurate photos and measurements.", D, "650"),
    ("star rating", "星評価", "名詞", "The product has a 4.5 star rating from over a thousand reviews.", D, "550"),
    ("wishlist", "ウィッシュリスト・お気に入りリスト", "名詞", "She added the jacket to her wishlist to buy later.", D, "600"),
    ("one-click purchase", "ワンクリック購入", "名詞", "One-click purchase makes it dangerously easy to overspend.", D, "700"),
    ("subscription model", "サブスクリプションモデル", "名詞", "The company switched from one-time sales to a subscription model.", D, "750"),
    ("freemium", "フリーミアム（基本無料+有料機能）", "名詞", "The app uses a freemium model, charging only for advanced features.", D, "800"),
    # --- SEO ---
    ("search engine optimization (SEO)", "検索エンジン最適化（SEO）", "名詞", "Search engine optimization helped the blog climb to the first page of results.", D, "700"),
    ("keyword research", "キーワードリサーチ", "名詞", "Keyword research shows exactly what people are searching for.", D, "700"),
    ("backlink", "バックリンク（被リンク）", "名詞", "A backlink from a trusted website can improve search rankings.", D, "800"),
    ("meta description", "メタディスクリプション", "名詞", "The meta description appears as the short summary under the page title in search results.", D, "800"),
    ("meta title", "メタタイトル", "名詞", "A clear meta title helps both search engines and readers understand the page.", D, "800"),
    ("organic traffic", "オーガニックトラフィック（自然検索流入）", "名詞", "Organic traffic grew steadily after the site improved its content.", D, "800"),
    ("page ranking", "ページランキング（検索順位）", "名詞", "Page ranking depends on hundreds of different factors.", D, "700"),
    ("domain authority", "ドメインオーソリティ", "名詞", "A higher domain authority generally makes it easier to rank for competitive keywords.", D, "850"),
    ("alt text", "代替テキスト（alt属性）", "名詞", "Alt text describes an image for both search engines and visually impaired users.", D, "750"),
    ("sitemap", "サイトマップ", "名詞", "A sitemap helps search engines find every page on the site.", D, "700"),
    ("search engine crawler", "検索エンジンのクローラー", "名詞", "A search engine crawler visits and indexes pages automatically.", D, "750"),
    ("indexing (search engine)", "インデックス登録（検索エンジンの）", "名詞", "The new page took a few days to appear after indexing.", D, "800"),
    ("long-tail keyword", "ロングテールキーワード", "名詞", "A long-tail keyword is more specific and usually easier to rank for.", D, "800"),
    ("click-through rate (CTR)", "クリック率（CTR）", "名詞", "A stronger headline can noticeably raise the click-through rate.", D, "800"),
    ("bounce rate", "直帰率", "名詞", "A high bounce rate suggests visitors aren't finding what they expected.", D, "800"),
    ("dwell time", "滞在時間", "名詞", "Longer dwell time often signals that readers found the content valuable.", D, "850"),
    ("featured snippet", "強調スニペット", "名詞", "The recipe appeared as a featured snippet right at the top of the results.", D, "850"),
    ("search engine results page (SERP)", "検索結果ページ（SERP）", "名詞", "Ranking on the first search engine results page drives most of the clicks.", D, "800"),
    # --- LLMO ---
    ("LLM optimization (LLMO)", "LLM最適化（LLMO）", "名詞", "LLM optimization aims to get a brand mentioned accurately by AI chat assistants.", D, "900"),
    ("answer engine", "アンサーエンジン（AI回答エンジン）", "名詞", "An answer engine gives a direct answer instead of a list of links.", D, "900"),
    ("generative search", "生成AI検索", "名詞", "Generative search summarizes information from several sources into one answer.", D, "900"),
    ("AI-generated summary", "AI生成の要約", "名詞", "The search page now shows an AI-generated summary above the usual results.", D, "850"),
    ("citation (AI answer)", "引用（AI回答内の）", "名詞", "A citation in the AI's answer linked back to the original article.", D, "850"),
    ("structured data", "構造化データ", "名詞", "Structured data helps both search engines and AI systems understand a page's content.", D, "850"),
    ("schema markup", "スキーママークアップ", "名詞", "Schema markup tells search engines exactly what kind of content is on the page.", D, "900"),
    ("AI crawler", "AIクローラー", "名詞", "An AI crawler gathers web content to train or ground a language model.", D, "900"),
    ("brand mention", "ブランドの言及", "名詞", "A brand mention in a chatbot's answer can influence a customer before they even visit the site.", D, "850"),
    ("zero-click search", "ゼロクリック検索", "名詞", "A zero-click search answers the question without the user ever visiting a website.", D, "900"),
    ("AI overview", "AIオーバービュー（AIによる概要表示）", "名詞", "The AI overview at the top of the page summarized three different opinions.", D, "850"),
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
