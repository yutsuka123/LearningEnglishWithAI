# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Expand the existing "手芸" domain/scene with vocabulary and phrases for
adjacent craft hobbies not yet covered by the DB: pottery (陶芸), calligraphy
(書道), origami (折り紙), dollhouse/diorama miniatures, porcelain painting
(ポーセラーツ), and painting/sketching, authored by Claude (2026-08-10・
ユーザー要望).

対象語彙: 陶芸(clay、stoneware、earthenware、bisque firing、underglaze、
pinch pot、coil pot)、書道(ink stone、ink stick、brush pen、stroke order、
seal ink、felt mat)、折り紙(crease、valley fold、mountain fold、origami
paper、fold line)、ドールハウス・ジオラマ(dollhouse、miniature、scale
model、diorama、roombox、static grass、miniature figure)、ポーセラーツ
(china painting、porcelain paint、transfer sheet、gilding)、絵画・スケッチ
(watercolor paint、acrylic paint、gouache、gesso、sketchbook、charcoal
pencil、cross-hatching)。「陶芸」「書道」「折り紙」「絵画」の基礎語
(pottery、ceramics、kiln、glazing、potter's wheel、calligraphy、origami、
canvas、painting、sketch等)や、既存の「手芸」ドメイン26語(編み物・裁縫系)
はすでにDBに存在するため、重複を避けて一段深い・隣接する語彙のみを追加する。
固有名詞は使用しない。

フレーズは陶芸教室・書道教室・工作サークルなど制作中の教室で実際に使う
自然な口語表現("Could you show me how to center the clay on the wheel?"
"Fold along the dotted line first." など)。既存の「手芸コミュニティ英語」
sceneに追加する。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_crafts_expanded.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 陶芸(pottery) ---
    ("clay", "粘土", "名詞", "Shape the clay into a small bowl before it dries out.", "手芸", "350"),
    ("pinch pot", "手びねりの器(指でつまんで成形する)", "名詞", "Beginners often start with a simple pinch pot.", "手芸", "600"),
    ("coil pot", "紐作りの器", "名詞", "We built a tall coil pot by stacking rolled clay ropes.", "手芸", "650"),
    ("stoneware", "せっ器(高温で焼く丈夫な陶器)", "名詞", "This mug is made of durable stoneware.", "手芸", "700"),
    ("earthenware", "土器・素焼きの陶器", "名詞", "The earthenware pot cracked after the first firing.", "手芸", "700"),
    ("bisque firing", "素焼き(釉薬をかける前の一次焼成)", "名詞", "The bowl needs a bisque firing before you can glaze it.", "手芸", "800"),
    ("underglaze", "下絵の具・アンダーグレーズ", "名詞", "She painted a blue pattern with underglaze before the final firing.", "手芸", "850"),
    # --- 書道(calligraphy) ---
    ("brush pen", "筆ペン", "名詞", "A brush pen is easier for beginners than a traditional brush.", "手芸", "500"),
    ("stroke order", "筆順", "名詞", "Following the correct stroke order makes your characters look balanced.", "手芸", "600"),
    ("felt mat", "下敷き(書道用のフェルト)", "名詞", "Lay a felt mat under the paper to absorb extra ink.", "手芸", "550"),
    ("ink stone", "硯(すずり)", "名詞", "Grind the ink stick on the ink stone with a little water.", "手芸", "750"),
    ("ink stick", "墨(すみ)", "名詞", "The ink stick smells faintly of pine smoke.", "手芸", "750"),
    ("seal ink", "印泥(はんこ用の朱肉)", "名詞", "Press your name seal firmly into the seal ink before stamping.", "手芸", "750"),
    # --- 折り紙(origami) ---
    ("origami paper", "折り紙用紙", "名詞", "Use square origami paper with color on only one side.", "手芸", "400"),
    ("fold line", "折り線", "名詞", "Follow the dotted fold line printed on the diagram.", "手芸", "450"),
    ("crease", "折り目", "名詞", "Run your fingernail along the crease to make it sharp.", "手芸", "500"),
    ("valley fold", "谷折り", "名詞", "Start with a valley fold to form the base shape.", "手芸", "600"),
    ("mountain fold", "山折り", "名詞", "A mountain fold bends the paper away from you.", "手芸", "600"),
    # --- ドールハウス・ジオラマ ---
    ("dollhouse", "ドールハウス", "名詞", "She spent months furnishing every room of the dollhouse.", "手芸", "400"),
    ("miniature", "ミニチュアの", "形容詞", "He collects miniature furniture for his dollhouse.", "手芸", "450"),
    ("diorama", "ジオラマ", "名詞", "The class built a diorama of a forest scene.", "手芸", "500"),
    ("miniature figure", "ミニチュアフィギュア", "名詞", "Paint the miniature figure with a fine detail brush.", "手芸", "500"),
    ("scale model", "縮尺模型", "名詞", "The scale model is exactly one-twelfth the size of a real house.", "手芸", "600"),
    ("roombox", "ルームボックス(一部屋分の箱庭ミニチュア)", "名詞", "Her roombox recreates a tiny Parisian cafe.", "手芸", "800"),
    ("static grass", "スタティックグラス(電着植毛の芝)", "名詞", "Sprinkle static grass over the glue to add texture to the lawn.", "手芸", "850"),
    # --- ポーセラーツ(porcelain painting) ---
    ("transfer sheet", "転写シート", "名詞", "Soak the transfer sheet in water before applying the design to the plate.", "手芸", "750"),
    ("porcelain paint", "ポーセラーツ用絵の具", "名詞", "Porcelain paint needs to be fired in a kiln to become permanent.", "手芸", "800"),
    ("china painting", "ポーセラーツ・磁器絵付け", "名詞", "China painting lets you decorate plain white porcelain with your own design.", "手芸", "800"),
    ("gilding", "金彩・金付け", "名詞", "Gilding adds a delicate gold rim around the edge of the teacup.", "手芸", "850"),
    # --- 絵画・スケッチ ---
    ("sketchbook", "スケッチブック", "名詞", "I carry a small sketchbook wherever I go.", "手芸", "400"),
    ("watercolor paint", "水彩絵の具", "名詞", "Watercolor paint works best on thick, absorbent paper.", "手芸", "450"),
    ("acrylic paint", "アクリル絵の具", "名詞", "Acrylic paint dries much faster than oil paint.", "手芸", "450"),
    ("charcoal pencil", "木炭鉛筆", "名詞", "A charcoal pencil is great for soft, dark shading.", "手芸", "550"),
    ("gouache", "ガッシュ(不透明水彩絵の具)", "名詞", "Gouache gives flatter, more opaque colors than regular watercolor.", "手芸", "800"),
    ("gesso", "ジェッソ(下地材)", "名詞", "Coat the canvas with gesso before you start painting.", "手芸", "800"),
    ("cross-hatching", "クロスハッチング(交差斜線で陰影をつける技法)", "名詞", "Cross-hatching creates shadow by layering intersecting lines.", "手芸", "800"),
]

PHRASES: list[tuple[str, str]] = [
    ("Could you show me how to center the clay on the wheel?", "粘土をろくろの中心に据える方法を見せてもらえますか？"),
    ("I'm still working on getting the walls even.", "まだ器の厚さを均一にする練習をしています。"),
    ("This piece needs another firing before I glaze it.", "この作品は釉薬をかける前にもう一度焼成が必要です。"),
    ("Could you trim the excess clay from the bottom?", "底の余分な粘土を削ってもらえますか？"),
    ("I'm not sure if this is centered — could you check?", "これが中心に来ているか自信がないので、確認してもらえますか？"),
    ("Let's take a short break while the glaze dries.", "釉薬が乾く間、少し休憩しましょう。"),
    ("Could you demonstrate the correct stroke order for this character?", "この字の正しい筆順を見せていただけますか？"),
    ("Try to keep your brush at a steady angle.", "筆を一定の角度に保つようにしてください。"),
    ("How much water should I mix with the ink?", "墨にどれくらい水を混ぜればいいですか？"),
    ("Press down firmly, then lift the brush slowly.", "しっかり押し当てて、ゆっくり筆を上げてください。"),
    ("Fold along the dotted line first.", "まず点線に沿って折ってください。"),
    ("Make sure the crease is nice and sharp.", "折り目をしっかりつけてください。"),
    ("I keep losing track of which fold comes next.", "次にどの折り方をするのか分からなくなってしまいます。"),
    ("Could you show that step one more time, slowly?", "その手順をもう一度、ゆっくり見せてもらえますか？"),
    ("I'm building a tiny kitchen for my dollhouse.", "ドールハウス用に小さなキッチンを作っています。"),
    ("What scale are you working in?", "どのくらいの縮尺で作っていますか？"),
    ("The glue is still a little wet, so be careful.", "まだ接着剤が少し湿っているので気をつけてください。"),
    ("I love how tiny and detailed this piece turned out.", "この作品、細部まで小さく仕上がっていて気に入っています。"),
    ("Could you help me paint the gold trim on this cup?", "このカップの金の縁取りを塗るのを手伝ってもらえますか？"),
    ("How long does the paint need to be fired?", "この絵の具はどれくらい焼く必要がありますか？"),
    ("I love how the design turned out on this plate.", "このお皿の絵柄、仕上がりが気に入っています。"),
    ("Let the base coat dry completely before adding another layer.", "下地が完全に乾いてから次の層を塗ってください。"),
    ("Could you mix a slightly darker shade for me?", "もう少し濃い色を作ってもらえますか？"),
    ("I want to add more shading around the edges.", "縁の部分にもっと陰影をつけたいです。"),
    ("Do you have a reference photo I could look at?", "参考にできる写真はありますか？"),
    ("This sketch is just a rough draft for now.", "このスケッチは今のところ大まかな下書きです。"),
    ("Could I borrow your ruler for a minute?", "ちょっと定規を貸してもらえますか？"),
    ("I think I added too much water to the paint.", "絵の具に水を入れすぎたと思います。"),
    ("Let's set our pieces on the shelf to dry overnight.", "作品を棚に置いて一晩乾かしましょう。"),
    ("Which paper weight do you recommend for watercolor?", "水彩画にはどの重さの紙がおすすめですか？"),
    ("Could you write my name in the corner in pencil first?", "まず鉛筆で隅に私の名前を書いてもらえますか？"),
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
                "VALUES (?, ?, '手芸コミュニティ英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
