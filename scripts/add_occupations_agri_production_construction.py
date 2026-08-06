# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add agriculture / production-process / construction occupation vocabulary,
authored by Claude (2026-08-06・ユーザー要望: 総務省日本標準職業分類の
「G 農林漁業従事者」「H 生産工程従事者」「J 建設・採掘従事者」を土台にした
職業語彙の拡充).

既存DBには domain='職業' の語が既に53語あり、fisherman / forester / miner /
roofer / stonemason / beekeeper / shepherd / crane operator / excavator
operator / scaffolder / assembly line worker / bricklayer など、農林漁業・
生産工程・建設の一部はすでにカバー済みだった。このスクリプトはそこに、
まだ手薄だった以下の職業語彙を追加する:

- 農林漁業従事者(G): farmer, dairy farmer, livestock farmer, pig farmer,
  poultry farmer, fruit grower, vegetable grower, rancher, lumberjack,
  forestry worker, aquaculture farmer, deckhand
- 生産工程従事者(H): sheet metal worker, machinist, press operator,
  textile worker, food processing worker, brewer, baker, butcher,
  seamstress, potter, woodworker, sawmill worker, packaging worker, glazier
- 建設・採掘従事者(J): construction worker, carpenter, plasterer,
  house painter, demolition worker, quarry worker, pipefitter, ironworker,
  paver, tiler, insulation installer, riveter

事前に既存DB(words ~7000件超)を全件チェックし、welder / printer /
electrician / plumber は domain='職業' 以外の場所(空domain・'生活'・
'家電'など)にすでに存在することを確認したため、このリストからは除外した
(スクリプトの重複スキップは english 列のみを見るため、そのまま入れても
domain='職業' には追加されない)。同様に既存53語(fisherman, forester,
miner, roofer, stonemason, beekeeper, shepherd など)とも重複しない語のみ
を採用している。

domain は '職業' に統一(既存の職業語彙と同じ domain)。level は
["300-","300","350","400","450","500","550","600","650","700","750","800",
"850","900","950","990","990+"] のスケールに沿って付与しており、farmer /
carpenter / baker のような日常的にも知られる職業語は350〜500、
press operator / pipefitter / riveter のようなより専門的な語は700〜800
とした。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_occupations_agri_production_construction.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 農林漁業従事者 (G) ---
    ("farmer", "農家", "名詞", "Her grandfather was a farmer who grew rice for over forty years.", "職業", "350"),
    ("dairy farmer", "酪農家", "名詞", "The dairy farmer milks the cows twice a day.", "職業", "450"),
    ("livestock farmer", "畜産農家", "名詞", "The livestock farmer raises cattle and pigs on a large pasture.", "職業", "550"),
    ("pig farmer", "養豚農家", "名詞", "The pig farmer feeds the herd early every morning.", "職業", "600"),
    ("poultry farmer", "養鶏農家", "名詞", "The poultry farmer collects fresh eggs from the henhouse each day.", "職業", "600"),
    ("fruit grower", "果樹栽培者", "名詞", "The fruit grower harvests apples every autumn.", "職業", "550"),
    ("vegetable grower", "野菜栽培者", "名詞", "The vegetable grower sells fresh tomatoes at the local market.", "職業", "550"),
    ("rancher", "牧場主", "名詞", "The rancher rides out on horseback to check the cattle every morning.", "職業", "500"),
    ("lumberjack", "きこり", "名詞", "The lumberjack felled the tall pine tree with a chainsaw.", "職業", "550"),
    ("forestry worker", "林業作業員", "名詞", "Forestry workers plant new trees to replace the ones that were cut down.", "職業", "600"),
    ("aquaculture farmer", "養殖業者", "名詞", "The aquaculture farmer raises salmon in large offshore pens.", "職業", "700"),
    ("deckhand", "甲板員(漁船の乗組員)", "名詞", "The deckhand hauled in the fishing nets as the boat rocked in the waves.", "職業", "650"),
    # --- 生産工程従事者 (H) ---
    ("sheet metal worker", "板金工", "名詞", "The sheet metal worker cut and shaped panels for the car body.", "職業", "700"),
    ("machinist", "機械工", "名詞", "The machinist operates a lathe to shape precise metal parts.", "職業", "650"),
    ("press operator", "プレス機オペレーター", "名詞", "The press operator runs a machine that stamps metal parts into shape.", "職業", "700"),
    ("textile worker", "繊維工", "名詞", "The textile worker operates looms that weave cotton into fabric.", "職業", "650"),
    ("food processing worker", "食品加工作業員", "名詞", "Food processing workers package and inspect products at the factory.", "職業", "600"),
    ("brewer", "醸造家", "名詞", "The brewer has been perfecting his craft beer recipe for years.", "職業", "600"),
    ("baker", "パン職人", "名詞", "The baker gets up at 4 a.m. to bake fresh bread every day.", "職業", "400"),
    ("butcher", "精肉店の職人", "名詞", "The butcher carefully cut the meat into thin slices for the customer.", "職業", "450"),
    ("seamstress", "縫製工", "名詞", "The seamstress altered the dress so it would fit perfectly.", "職業", "600"),
    ("potter", "陶芸家", "名詞", "The potter shaped the clay on a spinning wheel.", "職業", "550"),
    ("woodworker", "木工職人", "名詞", "The woodworker built a wooden chair entirely by hand.", "職業", "550"),
    ("sawmill worker", "製材工", "名詞", "Sawmill workers cut fallen logs into usable planks of wood.", "職業", "700"),
    ("packaging worker", "梱包作業員", "名詞", "Packaging workers seal and label boxes before they are shipped.", "職業", "550"),
    ("glazier", "ガラス工", "名詞", "The glazier fitted new glass panes into the broken window frame.", "職業", "750"),
    # --- 建設・採掘従事者 (J) ---
    ("construction worker", "建設作業員", "名詞", "The construction worker wore a hard hat and safety vest on site.", "職業", "400"),
    ("carpenter", "大工", "名詞", "The carpenter built a wooden deck behind the house.", "職業", "400"),
    ("plasterer", "左官職人", "名詞", "The plasterer smoothed a fresh layer of plaster onto the wall.", "職業", "700"),
    ("house painter", "(建築)塗装工", "名詞", "The house painter spent the whole day painting the outside walls.", "職業", "500"),
    ("demolition worker", "解体作業員", "名詞", "Demolition workers tore down the old building to make room for a new one.", "職業", "650"),
    ("quarry worker", "採石作業員", "名詞", "Quarry workers blast and cut large blocks of stone from the rock face.", "職業", "750"),
    ("pipefitter", "配管工事工", "名詞", "The pipefitter installed pipes for the building's water system.", "職業", "750"),
    ("ironworker", "鉄骨工", "名詞", "Ironworkers assembled the steel frame of the new skyscraper.", "職業", "750"),
    ("paver", "舗装工", "名詞", "The paver laid fresh asphalt over the damaged road.", "職業", "600"),
    ("tiler", "タイル職人", "名詞", "The tiler carefully arranged tiles across the bathroom floor.", "職業", "700"),
    ("insulation installer", "断熱工事作業員", "名詞", "The insulation installer lined the attic walls to keep the house warm.", "職業", "750"),
    ("riveter", "鋲打ち工", "名詞", "Riveters joined the steel beams together with hot metal rivets.", "職業", "800"),
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
