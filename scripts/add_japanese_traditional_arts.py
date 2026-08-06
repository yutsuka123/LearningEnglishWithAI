# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add JAPANESE TRADITIONAL ARTS / CRAFTS vocabulary, authored by Claude
(2026-08-06・ユーザー要望:「日本の伝統芸能・伝統工芸で、海外でも人気・
知名度のあるもの」を domain='芸術' に追加).

既存の domain='芸術'(31件)は ballet, ceramics, choreography, film director,
kiln, glazing (pottery), potter's wheel, throwing (pottery), lacquerware
など、演劇・映像・工芸寄りの語彙が中心だった。このスクリプトはそこに、
日本の伝統芸術・芸能・工芸を英語で「説明する」語彙を追加する:

- 盆栽: bonsai tree / bonsai pruning / bonsai wiring / bonsai pot /
  bonsai master
- 陶芸(産地銘・技法): raku ware / Imari ware / Kutani ware / celadon /
  wood-fired kiln (※ pottery / ceramics / kiln / glazing (pottery) /
  potter's wheel / throwing (pottery) は既存のため対象外)
- 能: Noh / Noh mask / Noh theater / chant (Noh) / hayashi ensemble
- 歌舞伎: Kabuki / Kabuki actor / onnagata / kumadori / mie
- 狂言: Kyogen
- その他、海外でも人気・知名度の高い伝統芸術・工芸: ikebana /
  flower arranging / calligraphy / sumi-e / ukiyo-e / woodblock print /
  kintsugi / washi / origami / furoshiki / netsuke / bunraku / shamisen /
  taiko drum

domain は既存の '芸術' に統一。level は ["300-","300","350","400","450",
"500","550","600","650","700","750","800","850","900","950","990","990+"]
のスケールに沿って付与しており、海外でも広く知られる語(bonsai tree,
origami, ikebana, Kabuki など)は450〜600、専門的な語(kumadori, mie,
raku ware, hayashi ensemble など)は750〜900とした。

例文は、外国人が日本文化を紹介・体験する文脈を想定して書いている。

事前に既存DB(words ~8100件)を全件チェックし、bonsai / tea ceremony /
pottery / geisha / sake / samurai / katana / sumo / lacquerware /
pruning / wiring などが既に(別domainも含め)存在することを確認済み。
それらと同一の語はこのリストから除外し、"bonsai tree" "bonsai pruning"
のような、より具体的な複合語に置き換えている。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_japanese_traditional_arts.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 盆栽 ---
    ("bonsai tree", "盆栽の木", "名詞", "She spent an hour trimming her bonsai tree on the balcony.", "芸術", "450"),
    ("bonsai pruning", "盆栽の剪定", "名詞", "Bonsai pruning shapes the tree's growth over many years.", "芸術", "700"),
    ("bonsai wiring", "盆栽の針金かけ", "名詞", "Bonsai wiring lets the artist bend branches into a desired shape.", "芸術", "750"),
    ("bonsai pot", "盆栽鉢", "名詞", "The tiny maple was planted in a shallow bonsai pot.", "芸術", "600"),
    ("bonsai master", "盆栽の師匠・名人", "名詞", "A bonsai master may spend decades training a single tree.", "芸術", "700"),
    # --- 陶芸(産地銘・技法) ---
    ("raku ware", "楽焼", "名詞", "Raku ware is fired quickly and often used in the tea ceremony.", "芸術", "850"),
    ("Imari ware", "伊万里焼", "名詞", "Imari ware is famous for its colorful, richly decorated porcelain.", "芸術", "850"),
    ("Kutani ware", "九谷焼", "名詞", "Kutani ware is known for its bold colors and gold accents.", "芸術", "850"),
    ("celadon", "青磁", "名詞", "The celadon vase had a soft, pale green glaze.", "芸術", "800"),
    ("wood-fired kiln", "登り窯・薪窯", "名詞", "The pottery was fired for three days in a wood-fired kiln.", "芸術", "800"),
    # --- 能 ---
    ("Noh", "能", "名詞", "Noh is one of the oldest surviving forms of theater in the world.", "芸術", "600"),
    ("Noh mask", "能面", "名詞", "The actor's expression seemed to change depending on the angle of the Noh mask.", "芸術", "650"),
    ("Noh theater", "能楽堂", "名詞", "We watched a slow, stylized performance at the Noh theater.", "芸術", "650"),
    ("chant (Noh)", "謡（うたい、能の声楽部分）", "名詞", "The chant in Noh is delivered in a slow, chanting rhythm unlike ordinary speech.", "芸術", "850"),
    ("hayashi ensemble", "囃子（能楽の伴奏音楽）", "名詞", "The hayashi ensemble uses drums and a flute to accompany the actors on stage.", "芸術", "900"),
    # --- 歌舞伎 ---
    ("Kabuki", "歌舞伎", "名詞", "Kabuki is famous for its bold makeup, elaborate costumes, and dramatic poses.", "芸術", "550"),
    ("Kabuki actor", "歌舞伎役者", "名詞", "A Kabuki actor often trains from childhood within a family lineage.", "芸術", "600"),
    ("onnagata", "女形（女性役を演じる男性役者）", "名詞", "An onnagata is a male actor who specializes in playing female roles in Kabuki.", "芸術", "850"),
    ("kumadori", "隈取り（歌舞伎の化粧法）", "名詞", "Kumadori uses bold lines of color to show a character's personality and mood.", "芸術", "900"),
    ("mie", "見得（決めのポーズ）", "名詞", "The actor froze in a mie, crossing his eyes to draw the audience's attention.", "芸術", "900"),
    # --- 狂言 ---
    ("Kyogen", "狂言", "名詞", "Kyogen is a comic form of traditional theater often performed between Noh plays.", "芸術", "700"),
    # --- その他、海外でも人気・知名度の高い伝統芸術・工芸 ---
    ("ikebana", "生け花", "名詞", "She took an ikebana class to learn the Japanese art of flower arranging.", "芸術", "550"),
    ("flower arranging", "生け花・花を生けること", "名詞", "Flower arranging in Japan follows strict rules about balance and space.", "芸術", "500"),
    ("calligraphy", "書道", "名詞", "He practices calligraphy every morning with an ink brush and rice paper.", "芸術", "500"),
    ("sumi-e", "墨絵・水墨画", "名詞", "Sumi-e paintings use only black ink to capture a scene with a few brushstrokes.", "芸術", "800"),
    ("ukiyo-e", "浮世絵", "名詞", "Ukiyo-e woodblock prints from the Edo period influenced many Western artists.", "芸術", "700"),
    ("woodblock print", "木版画", "名詞", "Each color in the woodblock print required a separate carved block.", "芸術", "650"),
    ("kintsugi", "金継ぎ", "名詞", "Kintsugi repairs broken pottery with gold, treating the cracks as part of its beauty.", "芸術", "750"),
    ("washi", "和紙", "名詞", "Washi is traditional Japanese paper made by hand from plant fibers.", "芸術", "600"),
    ("origami", "折り紙", "名詞", "She folded a paper crane using a simple origami technique.", "芸術", "450"),
    ("furoshiki", "風呂敷", "名詞", "A furoshiki is a square cloth used to wrap and carry gifts or bento boxes.", "芸術", "700"),
    ("netsuke", "根付", "名詞", "Netsuke are tiny carved figures once used as toggles on a kimono sash.", "芸術", "850"),
    ("bunraku", "文楽（人形浄瑠璃）", "名詞", "In bunraku, three puppeteers work together to control a single life-sized puppet.", "芸術", "800"),
    ("shamisen", "三味線", "名詞", "The shamisen is a three-stringed instrument often heard in traditional Japanese music.", "芸術", "650"),
    ("taiko drum", "太鼓", "名詞", "The performers struck the taiko drum in perfect, powerful unison.", "芸術", "550"),
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
