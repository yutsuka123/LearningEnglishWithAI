# ruff: noqa: E501
"""Beauty & cosmetics vocabulary: products, skincare, hair & nails, salon/
industry, and general terms. Authored by Claude — no app/OpenAI API calls.
Dedupe on english; back-fill empty examples. domain="美容".

Run: python scripts/add_beauty.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

GROUPS: dict[str, tuple[str, list[tuple[str, str, str]]]] = {
    "化粧品": ("600", [
        ("cosmetics", "化粧品", "She sells cosmetics at a department store."),
        ("makeup", "化粧・メイク", "She does her makeup every morning."),
        ("foundation", "ファンデーション", "Foundation evens out the skin tone."),
        ("concealer", "コンシーラー", "Concealer hides dark circles."),
        ("primer", "化粧下地・プライマー", "Primer helps makeup last longer."),
        ("mascara", "マスカラ", "Mascara lengthens the eyelashes."),
        ("eyeliner", "アイライナー", "She drew a thin line of eyeliner."),
        ("eyeshadow", "アイシャドウ", "The eyeshadow is a soft pink."),
        ("lipstick", "口紅・リップスティック", "She wore a bright red lipstick."),
        ("lip gloss", "リップグロス", "Lip gloss adds a glossy shine."),
        ("blush", "チーク・頬紅", "A little blush brightens the face."),
        ("face powder", "フェイスパウダー", "Powder sets the foundation."),
        ("nail polish", "マニキュア(液)・ネイル", "She painted her nails with polish."),
        ("fragrance", "香り・フレグランス", "This fragrance smells of roses."),
        ("perfume", "香水", "She wears perfume on special days."),
    ]),
    "スキンケア": ("600", [
        ("skincare", "スキンケア", "A daily skincare routine matters."),
        ("moisturizer", "保湿クリーム", "Apply moisturizer after washing."),
        ("cleanser", "洗顔料・クレンザー", "Use a gentle cleanser at night."),
        ("toner", "化粧水・トナー", "Toner balances the skin."),
        ("serum", "美容液・セラム", "The serum brightens the skin."),
        ("sunscreen", "日焼け止め", "Wear sunscreen every day."),
        ("SPF", "紫外線防御指数(SPF)", "Use SPF 30 or higher."),
        ("exfoliate", "角質を除去する", "Exfoliate your skin once a week."),
        ("hydration", "水分補給・保湿", "Dry skin needs more hydration."),
        ("pore", "毛穴", "The toner tightens the pores."),
        ("wrinkle", "しわ", "This cream reduces fine wrinkles."),
        ("anti-aging", "アンチエイジング・抗加齢", "An anti-aging serum firms the skin."),
        ("collagen", "コラーゲン", "Collagen keeps skin firm."),
        ("hyaluronic acid", "ヒアルロン酸", "Hyaluronic acid holds moisture."),
        ("blemish", "吹き出物・肌の傷", "Concealer covers a small blemish."),
        ("acne", "にきび", "Acne is common during the teens."),
        ("complexion", "顔色・肌つや", "She has a clear complexion."),
        ("pigmentation", "色素沈着", "Sun exposure causes pigmentation."),
    ]),
    "ヘア・ネイル": ("600", [
        ("shampoo", "シャンプー", "Rinse the shampoo out thoroughly."),
        ("conditioner", "コンディショナー", "Conditioner softens the hair."),
        ("hair dye", "毛染め・ヘアカラー", "She used a brown hair dye."),
        ("perm", "パーマ", "She got a soft perm."),
        ("highlights", "ハイライト(髪)", "She added blonde highlights."),
        ("blow-dry", "ブロー(乾かす)", "Blow-dry the hair gently."),
        ("trim", "(髪を)そろえる・カット", "I just want a trim, please."),
        ("bangs", "前髪", "She cut her bangs short."),
        ("split ends", "枝毛", "Trimming removes split ends."),
        ("manicure", "マニキュア(施術)", "She got a manicure for the party."),
        ("pedicure", "ペディキュア", "A pedicure for her toes."),
        ("gel nail", "ジェルネイル", "Gel nails last for weeks."),
    ]),
    "施術・業界": ("700", [
        ("beauty salon", "美容院・サロン", "She works at a beauty salon."),
        ("hairdresser", "美容師(英)", "The hairdresser cut my hair."),
        ("hairstylist", "ヘアスタイリスト", "The hairstylist styled her hair."),
        ("beautician", "美容師・美容技術者", "A beautician gave her a facial."),
        ("esthetician", "エステティシャン", "The esthetician did a facial."),
        ("facial", "フェイシャル(エステ)", "She booked a facial treatment."),
        ("spa", "スパ", "We relaxed at the day spa."),
        ("treatment", "トリートメント・施術", "She had a hair treatment."),
        ("makeover", "イメチェン・メイクオーバー", "The show gives her a makeover."),
        ("cosmetic surgery", "美容整形", "Cosmetic surgery was her own choice."),
        ("dermatology", "皮膚科(学)", "She visited a dermatology clinic."),
        ("shade", "色味・シェード", "Pick a shade that suits your skin."),
        ("swatch", "色見本・試し塗り", "She swatched the lipstick on her hand."),
    ]),
    "一般": ("500", [
        ("beauty", "美しさ・美容", "Beauty is more than appearance."),
        ("grooming", "身だしなみ", "Good grooming makes a good impression."),
        ("radiant", "輝くような", "She had a radiant smile."),
        ("flawless", "完璧な・欠点のない", "She has a flawless complexion."),
        ("glamour", "華やかさ・魅力", "The gown added a touch of glamour."),
    ]),
}


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = filled = 0
        per_group: dict[str, int] = {}
        for group, (level, items) in GROUPS.items():
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
                    (en, ja, "", ex, "美容", level),
                )
                existing.add(en.lower())
                added += 1
                per_group[group] = per_group.get(group, 0) + 1
    print(f"words: +{added} (例文補充 {filled})  {per_group}")
    with db() as conn:
        print("単語総数:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
