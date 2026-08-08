# ruff: noqa: E501
"""地学ドメインの本格拡充(2026-08-09)。

ユーザー要望: 「地学は主な岩石の種類、地層の種類、地形の種類(扇状地など)
他追加。火山用語、破局的噴火などの用語、噴火の種類。台風・サイクロン・
高気圧・熱帯低気圧・低気圧・風速他(これは気象なのか)。地震・津波・
活断層・マントル・地割れ・P波」。

確認: 既存DBを調べたところ、台風/サイクロン/高気圧/低気圧/熱帯低気圧/
気圧等の**気象用語は既に`地学`domainに統合済み**（独立した`気象`domainは
存在しない）。本スクリプトも同じ方針を踏襲し、新規の岩石・地形・火山・
台風・地震用語をすべて`地学`domainに追加する。

既存語との重複回避のため事前にDBを精査し、未登録のものだけを追加:
岩石13種・構造地質学用語5・地形14種・火山用語13(破局的噴火/噴火の
種類等)・台風/風速関連7・地震/津波関連13。

No app / OpenAI API calls — hand-written。Duplicates skipped by english
(lowercased)。

Run:  python scripts/add_earthscience_deep_2026_08_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "地学"

# (english, japanese, part_of_speech, example, level)
WORDS: list[tuple[str, str, str, str, str]] = [
    # --- 岩石の種類 ---
    ("igneous rock", "火成岩", "名詞", "Granite is a common type of igneous rock formed from cooled magma.", "600"),
    ("sedimentary rock", "堆積岩", "名詞", "Sandstone and limestone are both types of sedimentary rock.", "600"),
    ("metamorphic rock", "変成岩", "名詞", "Marble is a metamorphic rock formed from limestone under heat and pressure.", "600"),
    ("granite", "花崗岩", "名詞", "Granite countertops are popular because the rock is so hard and durable.", "500"),
    ("basalt", "玄武岩", "名詞", "Much of the ocean floor is made of basalt.", "550"),
    ("limestone", "石灰岩", "名詞", "Limestone is often used to make cement.", "500"),
    ("sandstone", "砂岩", "名詞", "The canyon walls are made of layered sandstone.", "550"),
    ("shale", "頁岩（けつ岩）", "名詞", "Shale gas is extracted from fine-grained sedimentary rock deep underground.", "650"),
    ("marble", "大理石", "名詞", "The statue was carved from a single block of marble.", "450"),
    ("obsidian", "黒曜石", "名詞", "Obsidian is a naturally occurring volcanic glass with sharp edges.", "600"),
    ("pumice", "軽石", "名詞", "Pumice is so full of air pockets that it can float on water.", "600"),
    ("gneiss", "片麻岩", "名詞", "Gneiss shows distinct banding from intense heat and pressure.", "750"),
    ("quartzite", "石英岩", "名詞", "Quartzite forms when sandstone is metamorphosed under extreme pressure.", "750"),
    # --- 地層・構造地質学 ---
    ("unconformity", "不整合", "名詞", "An unconformity marks a gap in the geologic record where erosion removed layers of rock.", "750"),
    ("anticline", "背斜", "名詞", "Oil often accumulates in the arch of an anticline.", "750"),
    ("syncline", "向斜", "名詞", "A syncline is a fold in rock layers that curves downward like a bowl.", "750"),
    ("cross-bedding", "斜交層理", "名詞", "Cross-bedding in the sandstone reveals the direction ancient winds once blew.", "800"),
    ("varve", "年縞（縞状堆積物）", "名詞", "Scientists count varves in lake sediment to date the layers year by year.", "800"),
    # --- 地形の種類 ---
    ("alluvial fan", "扇状地", "名詞", "An alluvial fan forms where a fast river slows down and spreads out onto flat land.", "650"),
    ("floodplain", "氾濫原", "名詞", "Farmers value the floodplain for its rich, fertile soil.", "600"),
    ("mesa", "メサ（周囲が切り立った台地）", "名詞", "A flat-topped mesa rose sharply from the desert floor.", "650"),
    ("butte", "ビュート（孤立した尖塔状の岩山）", "名詞", "The lone butte stood out against the flat desert landscape.", "700"),
    ("caldera", "カルデラ", "名詞", "A huge caldera formed after the volcano's magma chamber collapsed.", "650"),
    ("crater", "クレーター（噴火口・噴出口）", "名詞", "Steam still rises from the crater of the active volcano.", "500"),
    ("fjord", "フィヨルド", "名詞", "Glaciers carved the deep, narrow fjords along the coast.", "650"),
    ("cliff", "崖", "名詞", "The lighthouse stands on a cliff overlooking the sea.", "400"),
    ("sinkhole", "シンクホール（陥没穴）", "名詞", "A sinkhole suddenly opened up in the middle of the road.", "600"),
    ("moraine", "モレーン（氷堆石）", "名詞", "The ridge of rocks and soil is a moraine left behind by a retreating glacier.", "750"),
    ("drumlin", "ドラムリン（氷河が作る細長い丘）", "名詞", "A drumlin is a smooth, elongated hill shaped by moving glacial ice.", "800"),
    ("esker", "エスカー（氷河の下を流れた水がつくる細長い丘）", "名詞", "An esker traces the path of a river that once flowed beneath a glacier.", "850"),
    ("isthmus", "地峡", "名詞", "The Isthmus of Panama connects North and South America.", "700"),
    ("atoll", "環礁", "名詞", "The atoll formed as a ring of coral around a sunken volcanic island.", "700"),
    # --- 火山用語・噴火の種類 ---
    ("supervolcanic eruption", "破局的噴火（カルデラを形成するような巨大噴火）", "名詞", "A supervolcanic eruption can eject enough ash to affect the climate worldwide.", "800"),
    ("Plinian eruption", "プリニー式噴火（巨大な噴煙柱を伴う爆発的噴火）", "名詞", "A Plinian eruption sends a towering column of ash and gas high into the atmosphere.", "850"),
    ("Strombolian eruption", "ストロンボリ式噴火（周期的に爆発する比較的穏やかな噴火）", "名詞", "A Strombolian eruption produces rhythmic bursts of glowing lava and gas.", "850"),
    ("Vulcanian eruption", "ブルカノ式噴火（短く激しい爆発を繰り返す噴火）", "名詞", "A Vulcanian eruption is short but violent, often hurling blocks of rock into the air.", "850"),
    ("Hawaiian eruption", "ハワイ式噴火（流動性の高い溶岩が穏やかに流れ出す噴火）", "名詞", "A Hawaiian eruption produces fast-flowing, runny lava rather than explosive blasts.", "800"),
    ("phreatic eruption", "水蒸気爆発", "名詞", "A phreatic eruption occurs when magma heats groundwater into a sudden explosion of steam.", "800"),
    ("pyroclastic flow", "火砕流", "名詞", "A fast-moving pyroclastic flow of hot gas and ash raced down the mountainside.", "700"),
    ("lahar", "火山泥流（ラハール）", "名詞", "A lahar swept through the valley after heavy rain mixed with volcanic ash.", "750"),
    ("volcanic ash", "火山灰", "名詞", "Volcanic ash from the eruption grounded flights across the region.", "500"),
    ("fumarole", "噴気孔", "名詞", "Sulfur crystals formed around the fumarole where gas escaped from underground.", "800"),
    ("lava dome", "溶岩ドーム", "名詞", "A lava dome slowly grew inside the crater as thick lava piled up around the vent.", "800"),
    ("tephra", "テフラ（噴出物の総称）", "名詞", "Layers of tephra in the soil record the history of past eruptions.", "850"),
    ("Volcanic Explosivity Index", "火山爆発指数（VEI）", "名詞", "The Volcanic Explosivity Index ranks eruptions on a scale from zero to eight.", "800"),
    # --- 台風・風速関連 ---
    ("hurricane", "ハリケーン（大西洋・北東太平洋の熱帯低気圧の呼称）", "名詞", "A hurricane is the same kind of storm as a typhoon, just given a different name in the Atlantic.", "500"),
    ("tropical depression", "熱帯低気圧（発達段階の弱い段階）", "名詞", "A tropical depression can strengthen into a tropical storm within a day or two.", "650"),
    ("eye of the storm", "台風の目", "名詞", "The wind suddenly calmed as the eye of the storm passed overhead.", "550"),
    ("storm surge", "高潮", "名詞", "The storm surge flooded the coastal town far worse than the rain did.", "650"),
    ("wind speed", "風速", "名詞", "The typhoon's wind speed reached over two hundred kilometers per hour.", "500"),
    ("Beaufort scale", "ビューフォート風力階級", "名詞", "The Beaufort scale estimates wind speed based on observed conditions at sea or on land.", "750"),
    ("Saffir-Simpson scale", "サファ・シンプソン・ハリケーン風力階級", "名詞", "The Saffir-Simpson scale ranks hurricanes from category one to category five.", "800"),
    # --- 地震・津波関連 ---
    ("tsunami", "津波", "名詞", "The earthquake triggered a tsunami that struck the coast within minutes.", "450"),
    ("active fault", "活断層", "名詞", "The city was built directly above an active fault.", "650"),
    ("P-wave", "P波（初期微動を起こす最初に到達する地震波）", "名詞", "The P-wave arrives first because it travels faster than other seismic waves.", "700"),
    ("S-wave", "S波（主要動を起こす地震波）", "名詞", "The S-wave causes stronger shaking than the P-wave that precedes it.", "700"),
    ("seismograph", "地震計", "名詞", "The seismograph recorded a sharp spike the moment the earthquake struck.", "600"),
    ("aftershock", "余震", "名詞", "Several aftershocks rattled the region in the days following the earthquake.", "550"),
    ("foreshock", "前震", "名詞", "In hindsight, the small tremor was a foreshock warning of the bigger quake to come.", "700"),
    ("liquefaction", "液状化", "名詞", "Liquefaction caused the waterlogged ground to behave like a liquid during the earthquake.", "750"),
    ("ground fissure", "地割れ", "名詞", "A long ground fissure opened up across the road after the quake.", "650"),
    ("hypocenter", "震源（地震が発生した地下の地点）", "名詞", "The hypocenter of the earthquake was about ten kilometers below the surface.", "700"),
    ("seismic intensity", "震度（揺れの強さを表す日本独自の階級）", "名詞", "Japan's seismic intensity scale runs from zero up to a maximum of seven.", "700"),
    ("Richter scale", "リヒタースケール", "名詞", "The earthquake measured 6.5 on the Richter scale.", "550"),
    ("plate boundary", "プレート境界", "名詞", "Most major earthquakes occur along a plate boundary.", "650"),
]


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, level in WORDS:
            if en.lower() in w_existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, DOMAIN, level),
            )
            w_existing.add(en.lower())
            added += 1
        print(f"words: +{added} (skipped {skipped})")

    with db() as conn:
        print("total words:", conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
        print("地学 domain count:",
              conn.execute("SELECT COUNT(*) FROM words WHERE domain=?", (DOMAIN,)).fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
