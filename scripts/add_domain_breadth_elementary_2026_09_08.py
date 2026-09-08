# ruff: noqa: E501
"""B24語彙拡充の「レベル配分」方針転換(2026-09-08ユーザー指示)への対応・後半。

ユーザー指示:「語彙拡充は各分野の中学高等学校相当の拡充、小学校相当の拡充も
多少あってもいいと思います」。`scripts/tag_domain_breadth_2026_09_08.py`
(既存の他ドメイン語をword_domain_tagsで地学/天文/生物学に追加タグ付け・
48件)に続き、こちらは**DB全体を探しても該当する語がまだ存在しなかった**
小学校〜中学相当(level 300〜550)の基本語17語(地学6・天文5・生物学6)を
新規追加する。

rock (geology) は既存の`rock`(音楽(ジャンル)、レベル300)と同綴り異義語
(B17b)のため曖昧さ回避。他16語はDB全体で重複なしを確認済み(animal・
plant・space・universe・biologyのような極めて基本的な語がこれまで
未収録だったのは、既存のvocabularyが「個別の動物名」「個別の天体名」等の
具体語を中心に構築されてきたためと考えられる)。

No app / OpenAI API calls — hand-written、事実確認不要な一般常識レベルの
定義のみ(WebSearchでの追加裏取りは実施していない。オゾン層のモントリオール
議定書(1987年)採択年のみ一般常識として記載、誤りがあれば次回訂正)。

Run:  python scripts/add_domain_breadth_elementary_2026_09_08.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("rock (geology)", "地球の地殻を構成する、鉱物などが集まってできた固い物質。岩石。(音楽ジャンルの「ロック」とは別の意味)", "名詞", "Geologists study different types of rock to understand the history of the Earth.", "地学", "300"),
    ("fossil fuel", "大昔の生物の遺骸が長い年月をかけて地中で変化してできた燃料。石炭・石油・天然ガスなど。化石燃料。", "名詞句", "Coal, oil, and natural gas are all examples of fossil fuels.", "地学", "500"),
    ("ozone layer", "地球の成層圏にあり、太陽からの有害な紫外線の大部分を吸収する、オゾンを多く含む大気の層。オゾン層。", "名詞句", "The ozone layer absorbs most of the sun's harmful ultraviolet radiation.", "地学", "500"),
    ("landform", "山・谷・平野・海岸など、地表に見られる自然の地形。", "名詞", "Mountains, valleys, and plateaus are all examples of landforms.", "地学", "500"),
    ("silt", "砂よりも細かく粘土よりも粗い粒子からなる堆積物。川の流れによって運ばれ、河口や氾濫原に堆積することが多い。シルト。", "名詞", "The river deposits fine silt along its banks whenever it floods.", "地学", "550"),
    ("pebble", "水の流れなどによって角が取れて丸くなった、小石。", "名詞", "Children collected smooth pebbles along the riverbank.", "地学", "400"),
    ("universe", "存在するすべての物質・エネルギー・空間・時間を含む、あらゆるものの総体。宇宙。", "名詞", "Scientists believe the universe began with an event known as the Big Bang.", "天文", "400"),
    ("rocket", "燃料を燃焼させて生じるガスを噴射する反動で推進する乗り物や兵器。人工衛星や探査機の打ち上げに用いられる。ロケット。", "名詞", "The rocket lifted off from the launch pad and headed into orbit.", "天文", "400"),
    ("spacecraft", "宇宙空間を移動するために設計された乗り物。有人・無人を問わず、人工衛星や探査機、宇宙船などを含む。宇宙船・宇宙機。", "名詞", "The spacecraft traveled for several months before reaching Mars.", "天文", "500"),
    ("space", "地球の大気圏の外に広がる、天体が存在する広大な領域。宇宙空間。", "名詞", "Astronauts train for years before they travel into space.", "天文", "300"),
    ("moon phase", "地球から見た月の見かけの形が、新月から満月へと周期的に変化すること。新月・上弦・満月・下弦などの段階がある。月相。", "名詞句", "The moon phase changes gradually over about 29.5 days.", "天文", "500"),
    ("biology", "生物の構造・機能・成長・進化などを研究する自然科学の一分野。生物学。", "名詞", "Biology is the scientific study of living organisms.", "生物学", "400"),
    ("life cycle", "生物が誕生してから成長し、繁殖し、死に至るまでの一連の段階。生活環・ライフサイクル。", "名詞句", "A butterfly's life cycle includes the egg, caterpillar, pupa, and adult stages.", "生物学", "500"),
    ("food web", "生態系内の複数の生物種の食物連鎖が互いに複雑に絡み合ってできた、網目状の関係全体。食物網。", "名詞句", "A food web shows how many different food chains are connected within an ecosystem.", "生物学", "550"),
    ("living thing", "生命を持ち、成長・繁殖・代謝などを行う存在。生物。", "名詞句", "Plants and animals are both living things that need energy to survive.", "生物学", "400"),
    ("animal", "他の生物を食べて栄養を得る、自ら動くことができる多細胞生物。動物。", "名詞", "A dog is a common type of animal kept as a pet.", "生物学", "300"),
    ("plant", "光合成によって自ら栄養を作り出す、根・茎・葉などを持つ生物。植物。", "名詞", "Most plants need sunlight, water, and soil to grow.", "生物学", "300"),
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

    print(f"words:   +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print("totals -> words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
