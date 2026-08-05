# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""醸造工学(新設)＋デザイン用語(新設), authored by Claude (2026-08-05・
ユーザー要望:「醸造工学…デザイン用語…増やしましょうか」＋「質は落とさない
ように、段階的に実装ください」).

醸造工学は発酵・蒸留の工程語彙が中心。既存の「コーヒー」(18語・抽出/焙煎
中心)とは重複しない発酵科学の語を選定。アルコール度数や年齢確認が必要な
具体的な酒類の宣伝要素は含めず、工程・科学用語に限定。デザイン用語は
UI/UX・グラフィックデザインの語彙で、既存分野に該当がなかったため新設。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words`
table.

Run:  python scripts/add_brewing_design.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

BREWING = "醸造工学"
DESIGN = "デザイン用語"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 醸造工学 ---
    ("brewing", "醸造", "名詞", "Brewing turns grain and water into beer through a controlled fermentation process.", BREWING, "600"),
    ("fermentation tank", "発酵タンク", "名詞", "The fermentation tank keeps the temperature steady while the yeast does its work.", BREWING, "700"),
    ("mashing", "糖化・マッシング", "名詞", "Mashing releases the sugars trapped inside the malted grain.", BREWING, "800"),
    ("wort", "ウォート（麦汁）", "名詞", "The wort is boiled with hops before it is cooled and fermented.", BREWING, "850"),
    ("malting", "モルティング（製麦）", "名詞", "Malting lets the barley grains sprout just enough to develop the right enzymes.", BREWING, "850"),
    ("mash tun", "マッシュタン（糖化槽）", "名詞", "Hot water and crushed grain are mixed together in the mash tun.", BREWING, "900"),
    ("lautering", "ろ過（麦汁の）", "名詞", "Lautering separates the liquid wort from the leftover grain husks.", BREWING, "900"),
    ("pitching yeast", "酵母の投入・ピッチング", "名詞", "Pitching yeast at the right temperature is critical for a clean fermentation.", BREWING, "900"),
    ("primary fermentation", "一次発酵", "名詞", "Primary fermentation usually takes about a week for most beer styles.", BREWING, "850"),
    ("secondary fermentation", "二次発酵", "名詞", "Secondary fermentation smooths out the flavor and clears the liquid further.", BREWING, "850"),
    ("carbonation", "炭酸化", "名詞", "Carbonation gives the finished drink its fizz, either naturally or by force.", BREWING, "700"),
    ("distillation column", "蒸留塔・蒸留カラム", "名詞", "The distillation column separates alcohol from water by their different boiling points.", BREWING, "900"),
    ("pot still", "単式蒸留器（ポットスチル）", "名詞", "A pot still produces a richer, more characterful spirit than a continuous still.", BREWING, "900"),
    ("cask aging", "木樽での熟成", "名詞", "Cask aging lets the spirit slowly absorb flavor and color from the wood.", BREWING, "850"),
    ("proof (alcohol)", "アルコール度数の指標（プルーフ）", "名詞", "In the US, proof is roughly double the alcohol percentage by volume.", BREWING, "900"),
    ("brewmaster", "ブルーマスター（醸造長）", "名詞", "The brewmaster decides exactly how long each batch should ferment.", BREWING, "700"),
    ("hop bittering", "ホップによる苦味付け", "名詞", "Hop bittering balances the natural sweetness of the malt.", BREWING, "900"),
    ("attenuation (brewing)", "減衰度（発酵の）", "名詞", "Higher attenuation means the yeast converted more sugar into alcohol.", BREWING, "950"),
    ("specific gravity (brewing)", "比重（醸造の）", "名詞", "Brewers measure specific gravity before and after fermentation to calculate alcohol content.", BREWING, "900"),
    ("malolactic fermentation", "乳酸発酵（ワインの）", "名詞", "Malolactic fermentation softens a wine's sharp acidity into a creamier taste.", BREWING, "950"),
    # --- デザイン用語 ---
    ("user experience (UX)", "ユーザーエクスペリエンス（UX）", "名詞", "Good user experience makes an app feel effortless to navigate.", DESIGN, "700"),
    ("user interface (UI)", "ユーザーインターフェース（UI）", "名詞", "The user interface was redesigned to make the buttons easier to tap.", DESIGN, "650"),
    ("wireframe", "ワイヤーフレーム", "名詞", "The team sketched a wireframe before writing a single line of code.", DESIGN, "750"),
    ("mockup", "モックアップ", "名詞", "The designer showed a mockup of the new homepage in the meeting.", DESIGN, "700"),
    ("typography", "タイポグラフィ", "名詞", "Good typography can make even simple text feel polished and readable.", DESIGN, "750"),
    ("color palette", "カラーパレット", "名詞", "The brand's color palette is limited to just three main shades.", DESIGN, "700"),
    ("grid system", "グリッドシステム", "名詞", "A grid system keeps every element aligned neatly across the page.", DESIGN, "800"),
    ("white space", "ホワイトスペース（余白）", "名詞", "Designers left plenty of white space so the page wouldn't feel cluttered.", DESIGN, "700"),
    ("visual hierarchy", "視覚的階層", "名詞", "Visual hierarchy guides the eye to the most important information first.", DESIGN, "850"),
    ("brand identity", "ブランドアイデンティティ", "名詞", "The logo, colors, and fonts together form the company's brand identity.", DESIGN, "750"),
    ("style guide", "スタイルガイド", "名詞", "Every new page must follow the company's official style guide.", DESIGN, "750"),
    ("design system", "デザインシステム", "名詞", "A design system keeps buttons, colors, and spacing consistent across the whole product.", DESIGN, "800"),
    ("responsive design", "レスポンシブデザイン", "名詞", "Responsive design lets the same page look good on a phone or a large monitor.", DESIGN, "750"),
    ("usability testing", "ユーザビリティテスト", "名詞", "Usability testing revealed that users couldn't find the checkout button.", DESIGN, "800"),
    ("accessibility (design)", "アクセシビリティ（デザインの）", "名詞", "Accessibility ensures the site works well for users with visual impairments too.", DESIGN, "800"),
    ("iconography", "アイコノグラフィ（アイコン体系）", "名詞", "Consistent iconography helps users recognize the same action across the app.", DESIGN, "850"),
    ("negative space", "ネガティブスペース", "名詞", "The logo cleverly uses negative space to hide a second image.", DESIGN, "850"),
    ("mood board", "ムードボード", "名詞", "The designer put together a mood board to capture the feel they were going for.", DESIGN, "800"),
    ("prototyping (design)", "プロトタイピング（デザインの）", "名詞", "Prototyping let the team test the flow before any real code was written.", DESIGN, "800"),
    ("A/B testing", "A/Bテスト", "名詞", "A/B testing showed that the red button got more clicks than the blue one.", DESIGN, "750"),
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
