# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Expand restaurant/wine vocabulary and phrases, authored by Claude
(2026-08-04・ユーザー要望:「レストラン 焼き具合や料理の種類やワイン 他用語
フレーズ充実 ワインなら年代のあるとか」).

既存の domain='料理' には料理用語が非常に豊富にあるが、肉・魚の「焼き具合」
の段階(rare/medium/well done等)がほぼ無く、ワイン語彙もvintage/sommelier/
wine pairing/decant程度に留まっていた。また scene='レストラン・カフェ' の
既存38フレーズは注文・会計・アレルギー等が中心で、焼き具合の細かい指定や
ヴィンテージ(収穫年)についての質問、コース/アラカルトの違いを尋ねる表現が
無かった。本スクリプトはユーザーが明示的に要望した「ワインの年代(ヴィン
テージ)」の質問フレーズを含め、この3領域を補強する:

  1. 肉・魚の焼き具合(rare〜well done、fish向けのflaky/opaque等)
  2. ワイン語彙(wine list、house wine、corkage fee、vintage year、
     tannic/oaky/crispなどテイスティング用語)
  3. コース/料理形態語彙(à la carte、prix fixe menu、chef's special等)

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased), checked
against the FULL words/phrases tables (not just this domain/scene).

Run:  python scripts/add_restaurant_wine.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 焼き具合(肉・魚) ---
    ("rare", "レア(ステーキ等の生焼け)", "形容詞", "I ordered my steak rare, so it was almost raw inside.", "料理", "500"),
    ("medium rare", "ミディアムレア", "形容詞句", "Medium rare gives the steak a warm red center.", "料理", "500"),
    ("medium", "ミディアム(焼き加減)", "形容詞", "I'll have my burger cooked medium, please.", "料理", "500"),
    ("medium well", "ミディアムウェル", "形容詞句", "She prefers her steak medium well, with just a hint of pink.", "料理", "550"),
    ("well done", "ウェルダン(よく焼いた)", "形容詞句", "He always orders his meat well done, with no pink at all.", "料理", "500"),
    ("blue rare", "ブルーレア(表面だけ焼いた生に近い状態)", "形容詞句", "Blue rare steak is seared for just a few seconds per side.", "料理", "700"),
    ("char-grilled", "直火でこんがり焼いた", "形容詞", "The char-grilled chicken had a smoky, slightly charred crust.", "料理", "650"),
    ("seared", "表面を強火で焼いた", "形容詞", "The tuna steak was seared rare on the outside.", "料理", "550"),
    ("flaky", "(魚が)ほろほろとほぐれる", "形容詞", "The salmon turns flaky and opaque once it's fully cooked.", "料理", "600"),
    ("opaque", "(魚の身が)不透明になった(火が通った目安)", "形容詞", "Cook the fish until the center is opaque, not translucent.", "料理", "650"),
    # --- ワイン語彙 ---
    ("wine list", "ワインリスト", "名詞", "Could you bring us the wine list?", "料理", "450"),
    ("house wine", "ハウスワイン(店の定番ワイン)", "名詞", "The house wine here is a decent, affordable choice.", "料理", "500"),
    ("wine by the glass", "グラスワイン", "名詞句", "They offer a good selection of wine by the glass.", "料理", "550"),
    ("wine by the bottle", "ボトルワイン", "名詞句", "It works out cheaper to order wine by the bottle.", "料理", "550"),
    ("vintage year", "ヴィンテージ年(収穫年)", "名詞", "The vintage year can make a big difference in flavor.", "料理", "600"),
    ("corkage fee", "持込ワインの栓抜き料金", "名詞", "There's a corkage fee if you bring your own bottle.", "料理", "700"),
    ("decanter", "デカンター(ワイン用の広口瓶)", "名詞", "The sommelier poured the young red into a decanter.", "料理", "650"),
    ("tasting notes", "テイスティングノート(味の特徴の記述)", "名詞", "The tasting notes describe hints of cherry and vanilla.", "料理", "700"),
    ("light-bodied", "ライトボディの(軽い口当たりの)", "形容詞", "A light-bodied white wine suits this delicate fish dish.", "料理", "750"),
    ("medium-bodied", "ミディアムボディの", "形容詞", "This medium-bodied red pairs nicely with roasted chicken.", "料理", "750"),
    ("dry wine", "辛口ワイン", "名詞", "I'd rather have a dry wine than something sweet.", "料理", "600"),
    ("off-dry", "オフドライ(やや甘口の)", "形容詞", "This Riesling is off-dry, with just a touch of sweetness.", "料理", "850"),
    ("tannic", "タンニンの強い、渋みのある", "形容詞", "Young Cabernets can taste quite tannic when they're too young.", "料理", "850"),
    ("oaky", "樽の香りがする", "形容詞", "This Chardonnay has an oaky aroma from barrel aging.", "料理", "800"),
    ("crisp", "(ワインが)キレのある、爽やかな", "形容詞", "This Sauvignon Blanc is crisp and refreshing.", "料理", "700"),
    ("wine pairing suggestion", "ワインペアリングの提案", "名詞句", "Could I get a wine pairing suggestion for the lamb?", "料理", "750"),
    ("sommelier's recommendation", "ソムリエのおすすめ", "名詞句", "We decided to go with the sommelier's recommendation.", "料理", "800"),
    ("aerate", "(ワインを)空気に触れさせる", "動詞", "Swirling the glass helps aerate the wine and open up its aroma.", "料理", "700"),
    ("cork taint", "ブショネ(コルク臭による劣化)", "名詞句", "Cork taint gives a wine a musty, wet-cardboard smell.", "料理", "900"),
    ("corked", "ブショネになった、コルク臭のある", "形容詞", "I think this bottle is corked; it smells a bit off.", "料理", "850"),
    ("sparkling wine", "スパークリングワイン", "名詞", "They opened a bottle of sparkling wine to celebrate.", "料理", "500"),
    ("still wine", "スティルワイン(非発泡性ワイン)", "名詞", "Unlike champagne, this rosé is a still wine.", "料理", "600"),
    ("wine blend", "ワインブレンド(複数品種の混合)", "名詞", "This wine blend mixes three different grape varieties.", "料理", "700"),
    # --- コース/料理形態 ---
    ("palate cleanser", "口直し", "名詞", "The lemon sorbet served as a palate cleanser between courses.", "料理", "750"),
    ("prix fixe menu", "プリフィクスメニュー(コース料金固定)", "名詞句", "We decided to try the prix fixe menu tonight.", "料理", "750"),
    ("à la carte", "アラカルトで(一品ごとに注文する)", "形容詞", "We chose to order à la carte instead of the set menu.", "料理", "700"),
    ("chef's special", "シェフのおすすめ料理", "名詞句", "Tonight's chef's special is pan-seared halibut with a citrus glaze.", "料理", "550"),
    ("sharing plate", "シェア用の大皿料理", "名詞句", "We ordered a few sharing plates for the whole table.", "料理", "600"),
    ("mains", "メイン料理(複数形・イギリス英語)", "名詞", "What is everyone having for mains?", "料理", "600"),
]

PHRASES: list[tuple[str, str]] = [
    # --- 焼き具合を尋ねる/指定する ---
    ("How would you like your salmon cooked?", "サーモンの焼き加減はいかがなさいますか？"),
    ("Could I get that well done, please?", "それをウェルダン(よく焼き)でお願いできますか？"),
    ("I'd like mine blue rare.", "私のはブルーレアでお願いします。"),
    ("Could you cook my steak medium well?", "ステーキをミディアムウェルで焼いていただけますか？"),
    ("Is the tuna served rare or seared?", "マグロはレアで出ますか、それとも表面を焼いてありますか？"),
    ("How would you like your burger cooked?", "ハンバーガーの焼き加減はいかがなさいますか？"),
    # --- ワインの注文・ヴィンテージ(年代) ---
    ("What vintage is this?", "これは何年のヴィンテージですか？"),
    ("Do you have an older vintage of this wine?", "このワインのもっと古いヴィンテージはありますか？"),
    ("Is there a 2018 vintage available?", "2018年のヴィンテージはありますか？"),
    ("Could I see the wine list?", "ワインリストを見せていただけますか？"),
    ("Could I get a glass of the house red?", "ハウスの赤ワインをグラスでいただけますか？"),
    ("What would you pair with the salmon?", "サーモンにはどのワインが合いますか？"),
    ("Could you recommend something dry?", "辛口のものを何かおすすめいただけますか？"),
    ("Is this wine corked?", "このワイン、コルク臭がしませんか？"),
    ("Could we get a bottle instead of glasses?", "グラスではなくボトルでいただけますか？"),
    ("Is there a corkage fee if we bring our own bottle?", "自分たちのワインを持ち込んだ場合、栓抜き料金はかかりますか？"),
    ("Could we get this wine decanted?", "このワインをデカンタージュしていただけますか？"),
    ("How many years has this wine been aged?", "このワインは何年熟成させていますか？"),
    ("Is this a blend or a single varietal?", "これはブレンドですか、それとも単一品種ですか？"),
    ("Could we start with a bottle of sparkling wine?", "まずスパークリングワインを一本お願いできますか？"),
    # --- コース/料理形態を尋ねる ---
    ("Is this on the tasting menu?", "これはテイスティングメニューに含まれていますか？"),
    ("Could I order à la carte instead?", "代わりにアラカルトで注文できますか？"),
    ("What's in the chef's special tonight?", "今夜のシェフのおすすめには何が入っていますか？"),
    ("Could we do a few small plates to share?", "シェアできる小皿料理をいくつかお願いできますか？"),
    ("Is the prix fixe menu available tonight?", "今夜はプリフィクスメニューはありますか？"),
    ("Could we get a couple of sharing plates for the table?", "テーブル用にシェアプレートを2、3お願いできますか？"),
    ("What comes with the mains?", "メイン料理には何が付きますか？"),
    ("Is there a palate cleanser between courses?", "コースの間に口直しは出ますか？"),
]


def main() -> int:
    with db() as conn:
        existing_words = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added_words = skipped_words = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing_words:
                skipped_words += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing_words.add(en.lower())
            added_words += 1

        existing_phrases = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        added_phrases = skipped_phrases = 0
        for en, ja in PHRASES:
            if en.lower() in existing_phrases:
                skipped_phrases += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, 'レストラン・カフェ')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            added_phrases += 1

    print(f"words: +{added_words} (skipped {skipped_words})")
    print(f"phrases: +{added_phrases} (skipped {skipped_phrases})")
    with db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM phrases WHERE scene='レストラン・カフェ'"
        ).fetchone()[0]
        print("scene total now:", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
