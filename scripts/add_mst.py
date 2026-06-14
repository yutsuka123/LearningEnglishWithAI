# ruff: noqa: E501  (data-heavy seed script)
"""Add military / ship (船舶) / traffic (交通) vocabulary with examples.
Authored by Claude — no app/OpenAI API calls. Distinct english keys are used
where a plain word would clash with an existing different meaning
(e.g. army division vs division=割り算, prow vs bow=弓).

Run:  python scripts/add_mst.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS_BY_DOMAIN: dict[str, list[tuple[str, str, str]]] = {
    "軍事": [
        ("tank", "戦車", "The tank rolled across the field."),
        ("battleship", "戦艦", "The battleship fired its huge guns."),
        ("destroyer", "駆逐艦", "A destroyer escorted the convoy."),
        ("submarine", "潜水艦", "The submarine dived beneath the waves."),
        ("aircraft carrier", "空母", "Jets took off from the aircraft carrier."),
        ("cruiser", "巡洋艦", "The cruiser patrolled the coast."),
        ("frigate", "フリゲート艦", "The frigate intercepted the vessel."),
        ("warship", "軍艦", "Several warships entered the strait."),
        ("amphibious assault ship", "強襲揚陸艦", "Marines launched from the amphibious assault ship."),
        ("fleet", "艦隊", "The enemy fleet appeared on the horizon."),
        ("missile", "ミサイル", "The missile struck its target."),
        ("ballistic missile", "弾道ミサイル", "They test-fired a ballistic missile."),
        ("cruise missile", "巡航ミサイル", "A cruise missile hugged the terrain."),
        ("warhead", "弾頭", "The missile carries a heavy warhead."),
        ("nuclear warhead", "核弾頭", "The treaty limits nuclear warheads."),
        ("grenade", "手榴弾", "He threw a grenade into the bunker."),
        ("artillery", "砲兵・大砲", "Artillery pounded the enemy lines."),
        ("self-propelled artillery", "自走砲", "Self-propelled artillery moved into position."),
        ("fighter jet", "戦闘機", "A fighter jet roared overhead."),
        ("attack aircraft", "攻撃機", "Attack aircraft struck the convoy."),
        ("bomber", "爆撃機", "The bomber dropped its payload."),
        ("radar", "レーダー", "Radar detected the incoming planes."),
        ("sonar", "ソナー", "Sonar located the submarine."),
        ("battalion", "大隊", "The battalion advanced at dawn."),
        ("army division", "師団", "The army division held the front."),
        ("regiment", "連隊", "His regiment was sent to the border."),
        ("brigade", "旅団", "A brigade reinforced the city."),
        ("platoon", "小隊", "The platoon took cover."),
        ("squad", "分隊", "The squad cleared the building."),
        ("infantry", "歩兵", "The infantry marched for miles."),
        ("cavalry", "騎兵", "The cavalry charged the flank."),
        ("armed forces", "軍隊・軍", "The armed forces were on alert."),
        ("special forces", "特殊部隊", "Special forces freed the hostages."),
        ("general", "将軍・大将", "The general ordered an advance."),
        ("admiral", "提督・(海軍)大将", "The admiral commanded the fleet."),
        ("marshal", "元帥", "The marshal led the whole army."),
        ("colonel", "大佐", "The colonel briefed his officers."),
        ("major", "少佐", "The major relayed the orders."),
        ("captain", "大尉・艦長", "The captain saluted his men."),
        ("lieutenant", "中尉・少尉", "The lieutenant led the patrol."),
        ("sergeant", "軍曹", "The sergeant drilled the recruits."),
        ("commander", "司令官", "The commander studied the map."),
        ("command center", "司令部・司令室", "Orders came from the command center."),
        ("strategy", "戦略", "The general's strategy won the war."),
        ("tactics", "戦術", "They changed tactics under fire."),
        ("reconnaissance", "偵察", "A reconnaissance drone scouted ahead."),
        ("siege", "包囲(攻撃)", "The city was under siege for months."),
        ("garrison", "駐屯地・守備隊", "A small garrison defended the fort."),
        ("fortress", "要塞", "The fortress guarded the harbor."),
        ("armor", "装甲", "The tank's armor deflected the round."),
        ("catapult", "投石機・カタパルト", "The catapult hurled stones at the wall."),
        ("trebuchet", "トレビュシェット(投石機)", "The trebuchet smashed the gate."),
        ("crossbow", "弩(クロスボウ)", "He loaded a bolt into the crossbow."),
        ("bow", "弓", "The archer drew his bow."),
        ("longbow", "長弓", "English archers used the longbow."),
        ("galley", "ガレー船", "Slaves rowed the ancient galley."),
    ],
    "船舶": [
        ("ship", "船", "The ship sailed at dawn."),
        ("vessel", "船舶", "A fishing vessel entered the bay."),
        ("ferry", "フェリー", "We crossed the strait by ferry."),
        ("cargo ship", "貨物船", "The cargo ship carried containers."),
        ("tanker", "タンカー", "An oil tanker docked at the port."),
        ("container ship", "コンテナ船", "The container ship was fully loaded."),
        ("cruise ship", "クルーズ船", "The cruise ship visited many islands."),
        ("yacht", "ヨット", "They sailed a yacht around the cape."),
        ("tugboat", "タグボート", "A tugboat guided the ship to the dock."),
        ("barge", "はしけ・荷船", "A barge carried gravel up the river."),
        ("freighter", "貨物船", "The freighter unloaded its cargo."),
        ("hull", "船体", "The hull was painted bright red."),
        ("deck", "甲板", "Passengers strolled on the deck."),
        ("prow", "船首・へさき", "The prow cut through the waves."),
        ("stern", "船尾・とも", "He stood at the stern and waved."),
        ("port side", "左舷", "Land appeared on the port side."),
        ("starboard", "右舷", "Turn the wheel to starboard."),
        ("bridge", "船橋・操舵室", "The captain stood on the bridge."),
        ("helm", "舵輪・操舵", "She took the helm in the storm."),
        ("rudder", "舵", "The rudder steers the ship."),
        ("anchor", "錨(いかり)", "Drop the anchor in the bay."),
        ("mast", "帆柱・マスト", "The sailor climbed the mast."),
        ("sail", "帆", "They raised the sail in the wind."),
        ("keel", "竜骨", "The keel runs along the ship's bottom."),
        ("propeller", "スクリュー・プロペラ", "The propeller churned the water."),
        ("cabin", "船室", "We rested in our cabin below deck."),
        ("buoy", "ブイ・浮標", "A red buoy marked the channel."),
        ("harbor", "港・港湾", "The boats sheltered in the harbor."),
        ("dock", "波止場・ドック", "The ship was repaired in dry dock."),
        ("pier", "桟橋", "We walked out onto the pier."),
        ("wharf", "埠頭", "Goods were unloaded on the wharf."),
        ("crew", "乗組員", "The crew prepared to set sail."),
        ("sailor", "船員・水兵", "The sailor tied a strong knot."),
        ("navigation", "航行・航法", "Modern navigation uses GPS."),
        ("knot", "ノット(速度)", "The ship cruised at twenty knots."),
        ("voyage", "航海", "The voyage took three weeks."),
        ("lighthouse", "灯台", "The lighthouse warned of the rocks."),
        ("lifeboat", "救命ボート", "Passengers boarded the lifeboats."),
        ("life jacket", "救命胴衣", "Put on your life jacket before boarding."),
        ("tide", "潮・潮流", "We sailed out on the high tide."),
        ("capsize", "転覆する", "The small boat capsized in the storm."),
        ("shipwreck", "難破(船)", "Divers explored the old shipwreck."),
        ("aboard", "乗船して", "Welcome aboard!"),
        ("maritime", "海事の・海の", "Maritime law governs the seas."),
        ("gangway", "タラップ・舷門", "Passengers walked down the gangway."),
    ],
    "交通": [
        ("traffic light", "信号機", "Stop when the traffic light is red."),
        ("intersection", "交差点", "Turn left at the next intersection."),
        ("crosswalk", "横断歩道", "Cross only at the crosswalk."),
        ("pedestrian", "歩行者", "Drivers must yield to pedestrians."),
        ("sidewalk", "歩道", "Walk on the sidewalk, not the road."),
        ("highway", "幹線道路", "The highway was busy this morning."),
        ("freeway", "高速道路", "Take the freeway to save time."),
        ("expressway", "高速道路", "The expressway has a toll."),
        ("lane", "車線", "Stay in the right lane."),
        ("roundabout", "ロータリー", "Yield to traffic in the roundabout."),
        ("overpass", "陸橋・高架", "The road crosses on an overpass."),
        ("underpass", "地下道", "Use the underpass to cross safely."),
        ("traffic jam", "渋滞", "We were stuck in a traffic jam."),
        ("congestion", "混雑・渋滞", "Traffic congestion is worst at five."),
        ("gridlock", "大渋滞", "An accident caused total gridlock."),
        ("speed limit", "制限速度", "The speed limit here is 40."),
        ("road sign", "道路標識", "Obey every road sign."),
        ("one-way street", "一方通行路", "You can't turn here; it's a one-way street."),
        ("U-turn", "Uターン", "No U-turn is allowed here."),
        ("detour", "迂回路", "We took a detour around the roadwork."),
        ("toll", "通行料", "Pay the toll at the booth."),
        ("parking lot", "駐車場", "The parking lot is full."),
        ("traffic violation", "交通違反", "He was fined for a traffic violation."),
        ("speeding", "スピード違反", "She got a ticket for speeding."),
        ("seatbelt", "シートベルト", "Fasten your seatbelt before driving."),
        ("brake", "ブレーキ", "He slammed on the brakes."),
        ("accelerator", "アクセル", "Press the accelerator gently."),
        ("horn", "クラクション", "He honked the horn in frustration."),
        ("headlight", "ヘッドライト", "Turn on your headlights at night."),
        ("turn signal", "ウインカー・方向指示器", "Use your turn signal before turning."),
        ("driver's license", "運転免許(証)", "Show me your driver's license."),
        ("overtake", "追い越す", "Don't overtake on a curve."),
        ("yield", "(進路を)譲る", "Yield to oncoming traffic."),
        ("traffic cone", "カラーコーン", "Traffic cones blocked the lane."),
        ("guardrail", "ガードレール", "The car hit the guardrail."),
        ("median", "中央分離帯", "A barrier runs along the median."),
        ("bypass", "バイパス", "Take the bypass around the town."),
        ("jaywalk", "(信号無視で)横断する", "Don't jaywalk across a busy street."),
        ("tow truck", "レッカー車", "A tow truck removed the wreck."),
        ("vehicle", "車両", "Heavy vehicles use the left lane."),
        ("motorcycle", "オートバイ", "He rides a motorcycle to work."),
        ("bicycle", "自転車", "She commutes by bicycle."),
        ("bus stop", "バス停", "Wait for the bus at the bus stop."),
        ("taxi stand", "タクシー乗り場", "There's a taxi stand by the station."),
        ("pedestrian bridge", "歩道橋", "Use the pedestrian bridge to cross."),
        ("commute", "通勤(する)", "My commute takes an hour."),
    ],
}


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        w_added = w_skipped = 0
        per_domain: dict[str, int] = {}
        for domain, items in WORDS_BY_DOMAIN.items():
            level = {"軍事": "800", "船舶": "700", "交通": "600"}[domain]
            for en, ja, ex in items:
                if en.lower() in w_existing:
                    conn.execute(
                        "UPDATE words SET example = ? "
                        "WHERE LOWER(english) = LOWER(?) AND COALESCE(example, '') = ''",
                        (ex, en),
                    )
                    w_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO words (english, japanese, part_of_speech, "
                    "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                    (en, ja, "", ex, domain, level),
                )
                w_existing.add(en.lower())
                w_added += 1
                per_domain[domain] = per_domain.get(domain, 0) + 1

    print(f"words: +{w_added} (skipped {w_skipped})  {per_domain}")
    with db() as conn:
        print(
            "totals -> words:",
            conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
            "/ without example:",
            conn.execute("SELECT COUNT(*) FROM words WHERE COALESCE(example,'')=''").fetchone()[0],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
