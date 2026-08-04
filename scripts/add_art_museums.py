# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add ART MUSEUM / GALLERY vocabulary and phrases, authored by Claude
(2026-08-04・ユーザー要望)。

美術館・ギャラリーを訪れる際の実用語彙(exhibit, gallery, permanent
collection, docent, audio guide, curator, provenance, restoration など)と、
美術史・美術批評の語彙(brushstroke, composition, perspective, chiaroscuro,
impressionism, abstract art, forgery, authentication, avant-garde など)、
および美術館を訪れたときに自然に使える会話フレーズ(閉館時間を尋ねる、
撮影可否を確認する、おすすめの作品を尋ねる、ガイドツアーの有無を尋ねる、
作品への感想を述べるなど)をカバーする。

例文はすべてオリジナルで作成しており、実在する存命の作家の具体的な
作品を特定できる形で言及したり、架空の発言をその作家に帰属させる
ようなことはしていない。モネやレンブラントのような美術史上の画家・
美術運動については、事実として一般的に言及する範囲にとどめている。

words の domain は '美術・博物館'、phrases の scene は
'美術館・アートの英語' で統一する。level は
["300-","300","350","400","450","500","550","600","650","700","750",
"800","850","900","950","990","990+"] のスケールに沿って付与しており、
大半は 500〜750、chiaroscuro や provenance のような専門的な
美術史用語は 800 以上とした。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased). Note:
a handful of words below (e.g. "wing", "perspective", "restoration",
"authentication", "provenance") already exist in the DB under other
domains/senses (animal wing, business perspective, IT auth, collector
provenance, etc.); those rows will simply be skipped as duplicates, which
is expected and matches the existing convention in this codebase.

Run:  python scripts/add_art_museums.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 美術館ロジスティクス ---
    ("exhibit", "展示・展示品", "名詞", "The new exhibit features paintings from the 19th century.", "美術・博物館", "500"),
    ("gallery", "画廊・美術館の展示室", "名詞", "We spent an hour in the modern art gallery.", "美術・博物館", "500"),
    ("wing (of a museum)", "(美術館の)~棟・~館", "名詞", "The east wing houses the museum's Asian art collection.", "美術・博物館", "650"),
    ("permanent collection", "常設コレクション", "名詞", "The permanent collection includes works spanning three centuries.", "美術・博物館", "650"),
    ("temporary exhibition", "特別展・企画展", "名詞", "The temporary exhibition closes at the end of next month.", "美術・博物館", "650"),
    ("docent", "展示解説員・ボランティアガイド", "名詞", "A docent led us through the sculpture hall.", "美術・博物館", "800"),
    ("audio guide", "音声ガイド", "名詞", "You can rent an audio guide at the front desk.", "美術・博物館", "550"),
    ("curator", "学芸員・キュレーター", "名詞", "The curator chose to display the paintings in chronological order.", "美術・博物館", "700"),
    ("provenance", "来歴・作品の来歴情報", "名詞", "The museum label lists the painting's full provenance.", "美術・博物館", "850"),
    ("on loan", "貸し出し中の", "形容詞句", "This sculpture is on loan from a museum overseas.", "美術・博物館", "750"),
    ("restoration", "修復", "名詞", "The painting underwent years of careful restoration.", "美術・博物館", "700"),
    ("conservation", "(美術品の)保存・保存修復", "名詞", "The museum has its own conservation lab for fragile works.", "美術・博物館", "750"),
    ("gift shop", "ミュージアムショップ", "名詞", "We picked up some postcards at the gift shop.", "美術・博物館", "450"),
    # --- 美術史・美術批評の語彙 ---
    ("brushstroke", "筆致・筆遣い", "名詞", "You can see every brushstroke up close in this painting.", "美術・博物館", "750"),
    ("composition", "(絵の)構図", "名詞", "The composition draws your eye toward the center of the canvas.", "美術・博物館", "700"),
    ("perspective", "遠近法", "名詞", "The artist used perspective to create a sense of depth.", "美術・博物館", "750"),
    ("chiaroscuro", "明暗法(キアロスクーロ)", "名詞", "The dramatic use of chiaroscuro makes the figure seem to glow.", "美術・博物館", "900"),
    ("still life", "静物画", "名詞", "The gallery has an entire room devoted to still life paintings.", "美術・博物館", "700"),
    ("portraiture", "肖像画(技法・ジャンル)", "名詞", "This wing is dedicated to portraiture from the royal court.", "美術・博物館", "800"),
    ("abstract art", "抽象美術", "名詞", "Abstract art doesn't try to represent objects realistically.", "美術・博物館", "650"),
    ("impressionism", "印象派", "名詞", "Impressionism focused on capturing light and fleeting moments.", "美術・博物館", "700"),
    ("contemporary art", "現代美術", "名詞", "The new wing is dedicated entirely to contemporary art.", "美術・博物館", "650"),
    ("medium (art material)", "(美術の)画材・表現媒体", "名詞", "Oil paint was the artist's preferred medium.", "美術・博物館", "750"),
    ("sculpture", "彫刻", "名詞", "The bronze sculpture stands in the center of the courtyard.", "美術・博物館", "550"),
    ("installation art", "インスタレーションアート", "名詞", "The installation art fills the entire room with light and sound.", "美術・博物館", "800"),
    ("forgery", "贋作・偽造", "名詞", "Experts later discovered the painting was a forgery.", "美術・博物館", "800"),
    ("authentication", "真贋鑑定・真正性の確認", "名詞", "Authentication of the piece took the experts several months.", "美術・博物館", "850"),
    ("masterpiece", "傑作・名作", "名詞", "Critics consider this painting the artist's masterpiece.", "美術・博物館", "550"),
    ("avant-garde", "前衛的な・アバンギャルド", "形容詞", "The gallery is known for showing avant-garde work.", "美術・博物館", "850"),
    # --- 画材・様式・関連語彙 ---
    ("canvas", "キャンバス", "名詞", "The artist stretched a fresh canvas for the new painting.", "美術・博物館", "500"),
    ("easel", "イーゼル(画架)", "名詞", "The painting still rests on the artist's easel.", "美術・博物館", "700"),
    ("palette", "パレット・色使い", "名詞", "The artist mixed colors on a wooden palette.", "美術・博物館", "600"),
    ("oil painting", "油絵", "名詞", "This oil painting took the artist over a year to finish.", "美術・博物館", "500"),
    ("watercolor", "水彩画", "名詞", "The watercolor has soft, blurred edges.", "美術・博物館", "500"),
    ("fresco", "フレスコ画", "名詞", "The fresco was painted directly onto the wet plaster wall.", "美術・博物館", "850"),
    ("mural", "壁画", "名詞", "A huge mural covers the entire lobby wall.", "美術・博物館", "700"),
    ("landscape painting", "風景画", "名詞", "The landscape painting shows a quiet countryside at sunset.", "美術・博物館", "550"),
    ("self-portrait", "自画像", "名詞", "The artist painted dozens of self-portraits over his lifetime.", "美術・博物館", "600"),
    ("replica", "複製・レプリカ", "名詞", "The one on display in the lobby is a replica, not the original.", "美術・博物館", "700"),
    ("artifact", "遺物・工芸品", "名詞", "The museum displays ancient artifacts from the region.", "美術・博物館", "700"),
    ("exhibit label", "キャプション・解説パネル", "名詞", "Read the exhibit label for background on the artist.", "美術・博物館", "700"),
    ("exhibition catalogue", "展覧会カタログ・図録", "名詞", "You can buy the exhibition catalogue at the gift shop.", "美術・博物館", "700"),
    ("admission fee", "入場料", "名詞", "The admission fee includes access to all the galleries.", "美術・博物館", "450"),
    ("cloakroom", "クローク(手荷物預かり所)", "名詞", "You can leave your coat and bag at the cloakroom.", "美術・博物館", "600"),
    ("realism", "写実主義・リアリズム", "名詞", "Realism aims to depict subjects as accurately as possible.", "美術・博物館", "700"),
    ("surrealism", "シュルレアリスム", "名詞", "Surrealism often combines dreamlike images with everyday objects.", "美術・博物館", "750"),
    ("cubism", "キュビスム", "名詞", "Cubism breaks the subject into geometric shapes and angles.", "美術・博物館", "800"),
    ("engraving", "版画・彫版", "名詞", "The exhibit includes several engravings from the same period.", "美術・博物館", "800"),
]

PHRASES: list[tuple[str, str]] = [
    ("What time does the exhibit close?", "展示は何時に終わりますか。"),
    ("Is photography allowed here?", "ここでは写真撮影は許可されていますか。"),
    ("Is flash photography prohibited?", "フラッシュ撮影は禁止されていますか。"),
    ("Could you recommend a must-see piece?", "必見の作品を教えていただけますか。"),
    ("What period is this painting from?", "この絵はどの時代のものですか。"),
    ("Is there a guided tour available?", "ガイド付きツアーはありますか。"),
    ("This piece really speaks to me.", "この作品には本当に心を動かされます。"),
    ("Where can I pick up an audio guide?", "音声ガイドはどこで借りられますか。"),
    ("Is there an audio guide in Japanese?", "日本語の音声ガイドはありますか。"),
    ("How much is admission for adults?", "大人の入場料はいくらですか。"),
    ("Is there a student discount?", "学生割引はありますか。"),
    ("What's included in the permanent collection?", "常設コレクションには何が含まれていますか。"),
    ("The temporary exhibition runs through the end of the month.", "この特別展は今月末まで開催されています。"),
    ("Could you tell me more about the artist's technique?", "この画家の技法についてもっと教えていただけますか。"),
    ("I love how the light falls in this piece.", "この作品での光の当たり方が本当に好きです。"),
    ("The brushwork is incredibly delicate.", "筆致が非常に繊細ですね。"),
    ("This sculpture is on loan from another museum.", "この彫刻は別の美術館から貸し出されています。"),
    ("Let's meet at the gift shop afterward.", "あとでミュージアムショップで待ち合わせましょう。"),
    ("Where's the nearest cloakroom?", "一番近いクロークはどこですか。"),
    ("Could you point me toward the impressionist wing?", "印象派の展示室(棟)はどちらか教えていただけますか。"),
    ("I'd like to book tickets for the new exhibit.", "新しい展示のチケットを予約したいのですが。"),
    ("That painting is a total masterpiece.", "あの絵はまさに傑作ですね。"),
    ("The docent gave a fascinating talk about the collection.", "解説員(ドーセント)がコレクションについて興味深い話をしてくれました。"),
    ("I never really understood abstract art until I saw this.", "これを見るまで抽象美術を本当には理解していませんでした。"),
    ("Do you know if this piece is an original or a replica?", "これはオリジナルですか、それとも複製ですか。"),
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

        p_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in p_existing:
                p_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, '美術館・アートの英語')",
                (en, ja),
            )
            p_existing.add(en.lower())
            p_added += 1

    print(f"words:   +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
