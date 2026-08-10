# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a new "経営学" domain/scene: vocabulary and phrases for management
studies (Business Administration) as an academic discipline, authored by
Claude (2026-08-10・ユーザー要望).

既存の`ビジネス`(職場実務語彙・メール/会議の定型表現中心)や`経営工学`
(オペレーションズリサーチ/生産管理寄り)とは異なり、本ファイルは**経営学
という学問分野の理論・フレームワーク用語**を扱う:
経営戦略論(SWOT分析、ポーターの5フォース、競争優位性、バリューチェーン、
コストリーダーシップ、差別化戦略、ブルーオーシャン戦略、コアコンピタンス、
垂直統合、水平統合、多角化戦略)、組織論・組織行動論(組織文化、組織構造、
マトリックス組織、統制範囲、中央集権化、分権化、チェンジマネジメント、
組織学習)、リーダーシップ論(変革型・サーバント・状況対応型・カリスマ型)、
人的資源管理論(人的資本、タレントマネジメント、人事考課、後継者育成計画、
従業員エンゲージメント)、マーケティング理論(マーケティングミックス、4P、
市場セグメンテーション、ターゲット市場、ブランドエクイティ、顧客生涯価値、
ポジショニング戦略)、経営管理・ガバナンス論(コーポレートガバナンス、
ステークホルダー理論、株主価値、エージェンシー理論、取締役会)、経営学の
基礎概念(経営理論、科学的管理法、コンティンジェンシー理論、リソース・
ベースド・ビュー)。

フレーズはMBAの講義・ケーススタディ討論・経営会議で実際に使われる自然な
英語表現("Let's conduct a SWOT analysis..." "What's our competitive
advantage in this market?" など)。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_management_studies.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 経営戦略論 ---
    ("SWOT analysis", "SWOT分析(強み・弱み・機会・脅威の分析)", "名詞", "We conducted a SWOT analysis before entering the new market.", "経営学", "700"),
    ("Porter's five forces", "ポーターの5フォース分析", "名詞", "Porter's five forces framework helps assess industry competitiveness.", "経営学", "800"),
    ("competitive advantage", "競争優位性", "名詞", "Cost efficiency gives the firm a competitive advantage over rivals.", "経営学", "650"),
    ("value chain", "バリューチェーン(価値連鎖)", "名詞", "Each activity in the value chain adds value to the final product.", "経営学", "700"),
    ("cost leadership", "コストリーダーシップ戦略", "名詞", "The company pursues cost leadership by minimizing production expenses.", "経営学", "750"),
    ("differentiation strategy", "差別化戦略", "名詞", "A differentiation strategy focuses on unique features rather than price.", "経営学", "700"),
    ("blue ocean strategy", "ブルーオーシャン戦略", "名詞", "Blue ocean strategy aims to create uncontested market space.", "経営学", "800"),
    ("core competence", "コアコンピタンス(中核的な強み)", "名詞", "Innovation is the firm's core competence.", "経営学", "750"),
    ("vertical integration", "垂直統合", "名詞", "The manufacturer pursued vertical integration by acquiring its suppliers.", "経営学", "800"),
    ("horizontal integration", "水平統合", "名詞", "Horizontal integration occurs when a firm acquires a competitor.", "経営学", "800"),
    ("diversification strategy", "多角化戦略", "名詞", "The conglomerate adopted a diversification strategy to reduce risk.", "経営学", "800"),
    # --- 組織論・組織行動論 ---
    ("organizational behavior", "組織行動論", "名詞", "Organizational behavior studies how people interact within groups.", "経営学", "750"),
    ("organizational culture", "組織文化", "名詞", "A strong organizational culture can improve employee retention.", "経営学", "650"),
    ("organizational structure", "組織構造", "名詞", "The company redesigned its organizational structure to speed up decisions.", "経営学", "650"),
    ("matrix organization", "マトリックス組織", "名詞", "In a matrix organization, employees report to two managers.", "経営学", "800"),
    ("span of control", "統制範囲(一人の管理者が管理する部下の数)", "名詞", "A wide span of control means one manager oversees many staff.", "経営学", "850"),
    ("centralization", "中央集権化", "名詞", "Centralization keeps decision-making power at the top of the hierarchy.", "経営学", "750"),
    ("decentralization", "分権化", "名詞", "Decentralization gives more authority to local branches.", "経営学", "750"),
    ("change management", "チェンジマネジメント(変革管理)", "名詞", "Effective change management reduces employee resistance to reform.", "経営学", "700"),
    ("organizational learning", "組織学習", "名詞", "Organizational learning allows a company to adapt from past mistakes.", "経営学", "800"),
    # --- リーダーシップ論 ---
    ("transformational leadership", "変革型リーダーシップ", "名詞", "Transformational leadership inspires employees to exceed expectations.", "経営学", "850"),
    ("servant leadership", "サーバントリーダーシップ", "名詞", "Servant leadership puts the needs of the team first.", "経営学", "850"),
    ("situational leadership", "状況対応型リーダーシップ", "名詞", "Situational leadership adapts the style to the follower's readiness.", "経営学", "850"),
    ("charismatic leadership", "カリスマ型リーダーシップ", "名詞", "Charismatic leadership relies on the leader's personal appeal.", "経営学", "850"),
    # --- 人的資源管理論 ---
    ("human capital", "人的資本", "名詞", "Investing in training builds the firm's human capital.", "経営学", "700"),
    ("talent management", "タレントマネジメント(人材管理)", "名詞", "Talent management focuses on recruiting and retaining top performers.", "経営学", "700"),
    ("performance appraisal", "人事考課(業績評価)", "名詞", "Managers conduct a performance appraisal once a year.", "経営学", "700"),
    ("succession planning", "後継者育成計画", "名詞", "Succession planning ensures leadership continuity after retirement.", "経営学", "750"),
    ("employee engagement", "従業員エンゲージメント", "名詞", "High employee engagement is linked to lower turnover.", "経営学", "700"),
    # --- マーケティング理論 ---
    ("marketing mix", "マーケティングミックス", "名詞", "The marketing mix includes product, price, place, and promotion.", "経営学", "700"),
    ("the four Ps", "マーケティングの4P", "名詞", "The four Ps are the core elements of the marketing mix.", "経営学", "700"),
    ("market segmentation", "市場セグメンテーション(市場細分化)", "名詞", "Market segmentation divides customers into groups with similar needs.", "経営学", "700"),
    ("target market", "ターゲット市場", "名詞", "The brand's target market is young professionals.", "経営学", "550"),
    ("brand equity", "ブランドエクイティ(ブランド資産価値)", "名詞", "Strong brand equity allows a company to charge premium prices.", "経営学", "800"),
    ("customer lifetime value", "顧客生涯価値", "名詞", "Customer lifetime value estimates the total revenue from one customer.", "経営学", "850"),
    ("positioning strategy", "ポジショニング戦略", "名詞", "The positioning strategy targets health-conscious consumers.", "経営学", "750"),
    # --- 経営管理・ガバナンス論 ---
    ("corporate governance", "コーポレートガバナンス(企業統治)", "名詞", "Strong corporate governance protects shareholders' interests.", "経営学", "800"),
    ("stakeholder theory", "ステークホルダー理論", "名詞", "Stakeholder theory argues firms should consider all stakeholders, not just shareholders.", "経営学", "850"),
    ("shareholder value", "株主価値", "名詞", "Maximizing shareholder value was once the dominant corporate goal.", "経営学", "800"),
    ("agency theory", "エージェンシー理論(依頼人-代理人理論)", "名詞", "Agency theory examines conflicts of interest between managers and owners.", "経営学", "900"),
    ("board of directors", "取締役会", "名詞", "The board of directors approved the merger unanimously.", "経営学", "650"),
    # --- 経営学の基礎概念 ---
    ("management theory", "経営理論", "名詞", "Management theory has evolved from classical to modern approaches.", "経営学", "750"),
    ("scientific management", "科学的管理法(テイラー主義)", "名詞", "Scientific management applies data to improve workplace efficiency.", "経営学", "850"),
    ("contingency theory", "コンティンジェンシー理論(環境適応理論)", "名詞", "Contingency theory holds that there is no single best way to organize a firm.", "経営学", "900"),
    ("resource-based view", "リソース・ベースド・ビュー(資源ベース理論)", "名詞", "The resource-based view links competitive advantage to unique internal resources.", "経営学", "900"),
]

PHRASES: list[tuple[str, str]] = [
    ("Let's conduct a SWOT analysis before we finalize the strategy.", "戦略を最終決定する前にSWOT分析を行いましょう。"),
    ("What's our competitive advantage in this market?", "この市場における我々の競争優位性は何でしょうか？"),
    ("How does this fit into our value chain?", "これは我々のバリューチェーンのどこに位置づけられますか？"),
    ("I'd like to walk you through the case study.", "このケーススタディを一緒に見ていきましょう。"),
    ("What would you do if you were the CEO in this case?", "もしあなたがこのケースのCEOだったら、どうしますか？"),
    ("Let's break into groups and discuss the strategic options.", "グループに分かれて戦略の選択肢を議論しましょう。"),
    ("Can you defend that assumption with data?", "その前提をデータで裏付けられますか？"),
    ("I think we should pursue a differentiation strategy instead.", "むしろ差別化戦略を取るべきだと思います。"),
    ("Let's table that for the board meeting next week.", "それは来週の取締役会に持ち越しましょう。"),
    ("The board approved the proposed merger unanimously.", "取締役会はその合併提案を全会一致で承認しました。"),
    ("How do we align this with our core competence?", "これを我々のコアコンピタンスとどう整合させますか？"),
    ("Let's revisit our organizational structure before scaling up.", "規模を拡大する前に組織構造を見直しましょう。"),
    ("We need better change management to get buy-in from staff.", "従業員の理解を得るには、より良いチェンジマネジメントが必要です。"),
    ("What leadership style would work best in this situation?", "この状況ではどのリーダーシップスタイルが最も効果的でしょうか？"),
    ("Let's segment the market before we set the target.", "ターゲットを設定する前に市場をセグメント化しましょう。"),
    ("How do we build stronger brand equity over time?", "時間をかけてどうブランドエクイティを強化していきますか？"),
    ("That's a classic agency problem between managers and shareholders.", "それは経営者と株主の間の典型的なエージェンシー問題ですね。"),
    ("Let's put ourselves in the customer's shoes for a moment.", "少し顧客の立場に立って考えてみましょう。"),
    ("I'd push back on that assumption — the data doesn't support it.", "その前提には異議を唱えたいです。データがそれを裏付けていません。"),
    ("Let's take this offline and discuss the details later.", "この件は場を改めて後で詳しく話しましょう。"),
    ("What's the return on investment for this initiative?", "この施策の投資収益率はどのくらいですか？"),
    ("I'll circulate the slide deck before the presentation.", "発表の前にスライド資料を共有しておきます。"),
    ("Let's align on the key performance indicators first.", "まず重要業績評価指標（KPI）についてすり合わせましょう。"),
    ("Can we get a show of hands on this proposal?", "この提案について挙手で確認してもよいですか？"),
    ("That's a good point — let's build on it.", "良い指摘ですね。それを踏まえてさらに議論しましょう。"),
    ("How does this decision affect our stakeholders?", "この決定はステークホルダーにどのような影響を与えますか？"),
    ("Let's benchmark ourselves against industry leaders.", "業界のリーダー企業と自分たちを比較してみましょう。"),
    ("I'll play devil's advocate for a moment.", "少しの間、あえて反対意見を言わせてください。"),
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
                "VALUES (?, ?, '経営学の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
