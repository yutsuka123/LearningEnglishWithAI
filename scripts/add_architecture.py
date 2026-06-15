# ruff: noqa: E501
"""Architecture & buildings: building/facility types, housing, structural &
architectural terms, and architecture as a discipline/styles. Authored by
Claude — no app/OpenAI API calls. Dedupe on english; back-fill examples.
domain="建築・建物" (also renames existing "建築"→"建築・建物").
Run: python scripts/add_architecture.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "建築・建物"
GROUPS: dict[str, tuple[str, list[tuple[str, str, str]]]] = {
    "建物・施設": ("500", [
        ("building", "建物・ビル", "The office building has twenty floors."),
        ("skyscraper", "超高層ビル", "Skyscrapers tower over the city."),
        ("high-rise", "高層ビル", "They live in a high-rise apartment."),
        ("library", "図書館", "She borrowed a book from the library."),
        ("city hall", "市役所", "Pay the city tax at city hall."),
        ("town hall", "町役場・公会堂", "The town hall meeting is tonight."),
        ("village office", "村役場", "He works at the village office."),
        ("the Diet building", "国会議事堂(日本)", "The Diet building stands in Tokyo."),
        ("parliament building", "議事堂", "Protesters gathered at the parliament building."),
        ("capitol", "議事堂(米・州議会)", "The state capitol has a white dome."),
        ("prefectural assembly", "県議会", "The prefectural assembly passed the budget."),
        ("state legislature", "州議会(米)", "The state legislature meets each year."),
        ("courthouse", "裁判所(建物)", "The trial is held at the courthouse."),
        ("station", "駅", "We met at the train station."),
        ("hospital", "病院", "She was rushed to the hospital."),
        ("museum", "博物館・美術館", "The museum displays ancient art."),
        ("stadium", "競技場・スタジアム", "The stadium seats fifty thousand."),
        ("warehouse", "倉庫", "Goods are stored in the warehouse."),
        ("office building", "オフィスビル", "He works in a downtown office building."),
        ("shopping mall", "ショッピングモール", "We spent the day at the shopping mall."),
        ("park", "公園", "Children played in the park."),
        ("tower", "塔・タワー", "The tower offers a sweeping view."),
        ("factory", "工場", "The factory makes auto parts."),
        ("cathedral", "大聖堂", "The cathedral has soaring spires."),
    ]),
    "住宅": ("600", [
        ("detached house", "一戸建て", "They bought a detached house in the suburbs."),
        ("house", "家・住宅", "Their house has a small garden."),
        ("condominium", "分譲マンション", "She owns a condominium downtown."),
        ("apartment", "アパート・マンション(賃貸)", "He rents a small apartment."),
        ("studio apartment", "ワンルームマンション", "A studio apartment is a single room."),
        ("rental", "賃貸(物件)", "This flat is a monthly rental."),
        ("rented house", "借家", "They live in a rented house."),
        ("land", "土地", "They bought land to build a house."),
        ("plot", "区画・敷地", "Each plot is a hundred square meters."),
        ("real estate", "不動産", "Real estate prices keep rising."),
        ("duplex", "二世帯住宅・連棟", "Two families share the duplex."),
        ("terraced house", "テラスハウス・長屋(英)", "A terraced house shares side walls."),
        ("mansion", "豪邸・大邸宅", "The actor owns a huge mansion."),
    ]),
    "構造・建築用語": ("700", [
        ("architecture", "建築・建築学", "She studies architecture at university."),
        ("architect", "建築家", "The architect designed the new museum."),
        ("blueprint", "設計図・青写真", "The architect unrolled the blueprint."),
        ("floor plan", "間取り図", "The floor plan shows three bedrooms."),
        ("foundation", "基礎・土台", "A strong foundation supports the house."),
        ("pillar", "柱", "Marble pillars hold up the roof."),
        ("column", "円柱", "The temple has tall stone columns."),
        ("beam", "梁(はり)", "Steel beams span the ceiling."),
        ("girder", "桁(けた)・大梁", "Girders carry the bridge deck."),
        ("facade", "(建物の)正面・ファサード", "The facade is made of glass."),
        ("roof", "屋根", "The roof leaks during heavy rain."),
        ("ceiling", "天井", "The hall has a very high ceiling."),
        ("staircase", "階段", "A spiral staircase leads upstairs."),
        ("corridor", "廊下", "The corridor connects the rooms."),
        ("basement", "地下室・地階", "The parking lot is in the basement."),
        ("attic", "屋根裏", "Old boxes are stored in the attic."),
        ("balcony", "バルコニー", "She watered plants on the balcony."),
        ("scaffold", "足場", "Workers climbed the scaffold."),
        ("reinforced concrete", "鉄筋コンクリート", "The wall is reinforced concrete."),
        ("steel frame", "鉄骨", "The tower has a steel frame."),
        ("load-bearing wall", "耐力壁", "Never remove a load-bearing wall."),
        ("span", "スパン・支間", "The bridge has a very long span."),
        ("arch", "アーチ", "The gateway has a stone arch."),
        ("dome", "ドーム・丸屋根", "The capitol is topped by a dome."),
        ("cantilever", "片持ち梁(カンチレバー)", "The balcony is built as a cantilever."),
        ("insulation", "断熱(材)", "Good insulation cuts heating costs."),
        ("ventilation", "換気", "The room needs better ventilation."),
        ("earthquake-resistant", "耐震の", "The building is earthquake-resistant."),
        ("seismic isolation", "免震", "Seismic isolation protects the structure."),
    ]),
    "建築学・様式": ("800", [
        ("urban planning", "都市計画", "Urban planning shapes how a city grows."),
        ("elevation", "立面図", "The elevation shows the front of the house."),
        ("cross-section", "断面図", "The cross-section reveals the inner layers."),
        ("Gothic", "ゴシック様式", "The Gothic cathedral has pointed arches."),
        ("Baroque", "バロック様式", "Baroque buildings are richly ornate."),
        ("modernism", "モダニズム建築", "Modernism favors clean, simple forms."),
        ("proportion", "比率・均整", "Good proportion makes a building pleasing."),
        ("renovation", "改修・リノベーション", "The old house is under renovation."),
    ]),
}


def main() -> int:
    with db() as conn:
        # 既存の「建築」も統一
        conn.execute(
            "UPDATE words SET domain = ? WHERE domain = '建築'", (DOMAIN,)
        )
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
                    (en, ja, "", ex, DOMAIN, level),
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
