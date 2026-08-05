# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""Three new engineering domains: 土木工学(civil engineering)／都市工学
(urban engineering)／防災工学(disaster-prevention engineering), authored by
Claude (2026-08-05・ユーザー要望:「土木工学用語…都市工学…防災工学…増やし
ましょうか」＋「質は落とさないように、段階的に実装ください」).

既存の「建築・建物」(88語)は個々の建物・部屋・様式が中心なので、橋梁/
道路/測量/地盤といった土木工学、上下水道/都市計画/交通インフラといった
都市工学、耐震設計以外の防災工学(避難計画/水害対策等)は重複しない別分野
として新設した。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words`
table.

Run:  python scripts/add_civil_urban_disaster_eng.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

CIVIL = "土木工学"
URBAN = "都市工学"
DISASTER = "防災工学"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 土木工学 ---
    ("civil engineer", "土木技術者", "名詞", "A civil engineer designed the new bridge across the river.", CIVIL, "600"),
    ("civil engineering", "土木工学", "名詞", "Civil engineering covers roads, bridges, dams, and other public infrastructure.", CIVIL, "650"),
    ("infrastructure", "インフラ・社会基盤", "名詞", "The city invested heavily in infrastructure like roads and water systems.", CIVIL, "600"),
    ("surveying", "測量", "名詞", "Surveying determines the exact shape and elevation of the land before construction begins.", CIVIL, "700"),
    ("topographic survey", "地形測量", "名詞", "A topographic survey mapped every slope and contour of the site.", CIVIL, "800"),
    ("geotechnical engineering", "地盤工学", "名詞", "Geotechnical engineering studies how soil and rock behave under a structure's weight.", CIVIL, "850"),
    ("soil bearing capacity", "地盤の許容支持力", "名詞", "The soil bearing capacity determines how deep the foundation must go.", CIVIL, "900"),
    ("foundation (structure)", "基礎（構造物の）", "名詞", "The foundation must be strong enough to support the entire building above it.", CIVIL, "600"),
    ("pile foundation", "杭基礎", "名詞", "A pile foundation transfers the building's weight down to solid rock.", CIVIL, "850"),
    ("retaining wall", "擁壁", "名詞", "A retaining wall holds back the soil on the steep side of the road.", CIVIL, "700"),
    ("embankment", "堤・盛土", "名詞", "The embankment raises the railway above the level of the surrounding fields.", CIVIL, "800"),
    ("earthwork", "土工事", "名詞", "Earthwork moved thousands of tons of soil before construction even began.", CIVIL, "800"),
    ("grading (civil engineering)", "整地", "名詞", "Grading leveled the site so that rainwater would drain away properly.", CIVIL, "800"),
    ("bridge span", "橋のスパン（支柱間の距離）", "名詞", "The bridge span had to cross the river without a single support in the water.", CIVIL, "800"),
    ("suspension bridge", "吊り橋", "名詞", "A suspension bridge hangs its deck from huge cables strung between towers.", CIVIL, "700"),
    ("truss bridge", "トラス橋", "名詞", "A truss bridge distributes weight through a framework of triangular sections.", CIVIL, "800"),
    ("viaduct", "高架橋", "名詞", "The highway runs on a long viaduct above the valley floor.", CIVIL, "800"),
    ("tunnel boring machine", "トンネル掘進機", "名詞", "A tunnel boring machine cut through the mountain at a steady pace.", CIVIL, "850"),
    ("aggregate (construction material)", "骨材（建設材料）", "名詞", "Sand and gravel are mixed as aggregate to make concrete.", CIVIL, "800"),
    ("rebar", "鉄筋", "名詞", "Rebar is placed inside the concrete before it is poured to add strength.", CIVIL, "700"),
    ("asphalt paving", "アスファルト舗装", "名詞", "Asphalt paving covered the new road in a single afternoon.", CIVIL, "650"),
    ("culvert", "暗渠・カルバート", "名詞", "A culvert lets the stream pass safely under the new road.", CIVIL, "800"),
    ("dam spillway", "ダムの放水路・洪水吐き", "名詞", "The dam spillway releases excess water safely during heavy rain.", CIVIL, "850"),
    ("hydraulic structure", "水利構造物", "名詞", "Locks and dams are both examples of a hydraulic structure.", CIVIL, "900"),
    ("water treatment plant", "上水処理施設", "名詞", "The water treatment plant supplies clean drinking water to the whole city.", CIVIL, "700"),
    ("sewage system", "下水システム", "名詞", "The old sewage system could not handle the growing population.", CIVIL, "700"),
    # --- 都市工学 ---
    ("urban engineering", "都市工学", "名詞", "Urban engineering designs the systems that keep a city running smoothly.", URBAN, "800"),
    ("urban planner", "都市計画技師", "名詞", "An urban planner decides where new housing, roads, and parks should go.", URBAN, "700"),
    ("land use plan", "土地利用計画", "名詞", "The land use plan set aside certain areas for housing and others for industry.", URBAN, "800"),
    ("public works", "公共事業", "名詞", "Public works like roads and bridges are funded through the city budget.", URBAN, "700"),
    ("traffic engineering", "交通工学", "名詞", "Traffic engineering studies how to keep intersections safe and efficient.", URBAN, "800"),
    ("traffic flow", "交通流", "名詞", "A new roundabout improved traffic flow at the busy intersection.", URBAN, "700"),
    ("congestion (traffic)", "交通混雑", "名詞", "Congestion during rush hour added an extra hour to the commute.", URBAN, "600"),
    ("mass transit", "公共交通・大量輸送機関", "名詞", "Mass transit reduces the number of cars needed on the road each day.", URBAN, "650"),
    ("urban sprawl", "都市のスプロール化", "名詞", "Urban sprawl spread the city's low-density suburbs far into the countryside.", URBAN, "850"),
    ("gentrification", "ジェントリフィケーション（地域の高級化）", "名詞", "Gentrification raised rents in the neighborhood faster than wages grew.", URBAN, "900"),
    ("green space", "緑地", "名詞", "The new development set aside a large green space for residents.", URBAN, "600"),
    ("urban renewal", "都市再開発", "名詞", "Urban renewal replaced the old warehouses with apartments and shops.", URBAN, "800"),
    ("utility corridor", "ライフライン共同溝", "名詞", "Water, gas, and power lines all run through the same utility corridor.", URBAN, "850"),
    ("smart city", "スマートシティ", "名詞", "A smart city uses sensors and data to manage traffic and energy use.", URBAN, "700"),
    ("walkability", "歩きやすさ（街の）", "名詞", "Walkability is one reason people prefer to live near the old town center.", URBAN, "850"),
    # --- 防災工学 ---
    ("disaster prevention engineering", "防災工学", "名詞", "Disaster prevention engineering designs structures and systems that reduce harm from natural hazards.", DISASTER, "850"),
    ("hazard map", "ハザードマップ", "名詞", "The hazard map shows which areas are most likely to flood.", DISASTER, "700"),
    ("flood control", "洪水対策", "名詞", "Flood control along the river includes levees and a wide drainage channel.", DISASTER, "700"),
    ("storm surge barrier", "高潮防波堤", "名詞", "The storm surge barrier closes automatically before a typhoon reaches the coast.", DISASTER, "900"),
    ("evacuation route", "避難経路", "名詞", "Every building must post its evacuation route near the exits.", DISASTER, "600"),
    ("evacuation drill", "避難訓練", "名詞", "The school holds an evacuation drill twice a year.", DISASTER, "550"),
    ("early warning system", "早期警戒システム", "名詞", "The early warning system gives coastal towns extra minutes before a tsunami arrives.", DISASTER, "800"),
    ("tsunami wall", "防潮堤", "名詞", "A tsunami wall now protects the coastline where the old village once stood.", DISASTER, "800"),
    ("landslide prevention", "土砂崩れ防止", "名詞", "Landslide prevention on the hillside relies on drainage pipes and retaining walls.", DISASTER, "850"),
    ("liquefaction (soil)", "液状化（地盤の）", "名詞", "Liquefaction during the earthquake caused several buildings to sink into the ground.", DISASTER, "900"),
    ("disaster resilience", "防災上の強靭性・レジリエンス", "名詞", "Disaster resilience measures how quickly a city can recover after a major event.", DISASTER, "900"),
    ("emergency shelter", "避難所", "名詞", "The gymnasium was converted into an emergency shelter after the earthquake.", DISASTER, "600"),
    ("risk assessment (disaster)", "リスク評価（防災の）", "名詞", "A risk assessment identified the bridge as the most vulnerable structure in a flood.", DISASTER, "800"),
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
