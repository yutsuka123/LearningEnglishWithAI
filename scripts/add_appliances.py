# ruff: noqa: E501
"""Home appliances / electronics (domain 家電) and house rooms & parts
(domain 建築・建物). Authored by Claude — no app/OpenAI API calls. Dedupe on
english; back-fill examples. Run: python scripts/add_appliances.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# (domain, level, [(english, japanese, example)])
SETS: list[tuple[str, str, list[tuple[str, str, str]]]] = [
    ("家電", "500", [
        ("refrigerator", "冷蔵庫", "Put the milk in the refrigerator."),
        ("fridge", "冷蔵庫(口語)", "The fridge is almost empty."),
        ("freezer", "冷凍庫", "Keep the ice cream in the freezer."),
        ("air conditioner", "エアコン", "Please turn on the air conditioner."),
        ("microwave", "電子レンジ", "Heat the soup in the microwave."),
        ("oven", "オーブン", "Bake the cake in the oven."),
        ("rice cooker", "炊飯器", "The rice cooker just beeped."),
        ("toaster", "トースター", "Pop the bread in the toaster."),
        ("washing machine", "洗濯機", "Put the clothes in the washing machine."),
        ("dryer", "乾燥機", "The dryer finished the towels."),
        ("vacuum cleaner", "掃除機", "He ran the vacuum cleaner over the rug."),
        ("dishwasher", "食器洗い機", "Load the plates into the dishwasher."),
        ("hair dryer", "ドライヤー", "She dried her hair with a hair dryer."),
        ("clothes iron", "アイロン", "Iron the shirt before the meeting."),
        ("sewing machine", "ミシン", "She mended the dress with a sewing machine."),
        ("television", "テレビ", "The television is on in the living room."),
        ("TV", "テレビ", "She watched TV all evening."),
        ("lighting", "照明", "The room has soft, warm lighting."),
        ("light fixture", "照明器具", "A light fixture hangs from the ceiling."),
        ("fan", "扇風機", "Turn on the fan; it's hot in here."),
        ("heater", "ヒーター・暖房器", "She switched on the electric heater."),
        ("humidifier", "加湿器", "A humidifier adds moisture to dry air."),
        ("computer", "コンピュータ・パソコン", "She bought a new computer."),
        ("desktop computer", "デスクトップパソコン", "A desktop computer sits on the desk."),
        ("laptop", "ノートパソコン", "He typed a report on his laptop."),
        ("smartphone", "スマートフォン・スマホ", "She checked her smartphone."),
        ("feature phone", "ガラケー(従来型携帯)", "He still uses an old feature phone."),
        ("tablet", "タブレット端末", "She reads novels on a tablet."),
        ("earphones", "イヤホン", "He put in his earphones."),
        ("headphones", "ヘッドホン", "She wore noise-canceling headphones."),
        ("earbuds", "ワイヤレスイヤホン", "He lost one of his earbuds."),
        ("remote control", "リモコン", "Where is the TV remote control?"),
        ("charger", "充電器", "I forgot my phone charger at home."),
        ("printer", "プリンター", "The printer is out of ink."),
        ("router", "ルーター", "The Wi-Fi router started blinking."),
        ("speaker", "スピーカー", "The speaker plays music loudly."),
        ("monitor", "モニター・画面", "The monitor displays the image clearly."),
    ]),
    ("建築・建物", "500", [
        ("bath", "風呂・入浴", "She relaxed in a hot bath."),
        ("bathtub", "浴槽", "He filled the bathtub with warm water."),
        ("bathroom", "浴室・洗面所", "The bathroom is upstairs."),
        ("toilet", "トイレ", "Where is the toilet, please?"),
        ("living room", "居間・リビング", "We watched a movie in the living room."),
        ("kitchen", "台所・キッチン", "She cooked dinner in the kitchen."),
        ("bedroom", "寝室", "The bedroom has a large window."),
        ("dining room", "食堂・ダイニング", "We ate together in the dining room."),
        ("garden", "庭", "Roses bloom in the garden."),
        ("yard", "庭・裏庭", "The children play in the yard."),
        ("garage", "車庫・ガレージ", "He parked the car in the garage."),
        ("entrance", "玄関・入口", "Leave your shoes at the entrance."),
        ("closet", "クローゼット・物入れ", "Hang your coat in the closet."),
        ("veranda", "ベランダ・縁側", "She hung the laundry on the veranda."),
        ("storeroom", "物置・収納部屋", "Old tools are kept in the storeroom."),
        ("gate", "門", "The front gate was locked at night."),
        ("fence", "塀・フェンス", "A wooden fence surrounds the yard."),
        ("driveway", "私道・車寄せ", "He parked in the driveway."),
        ("porch", "玄関ポーチ・縁側", "They sat on the porch in the evening."),
    ]),
]


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = filled = 0
        per_domain: dict[str, int] = {}
        for domain, level, items in SETS:
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
                    (en, ja, "", ex, domain, level),
                )
                existing.add(en.lower())
                added += 1
                per_domain[domain] = per_domain.get(domain, 0) + 1
    print(f"words: +{added} (例文補充 {filled})  {per_domain}")
    with db() as conn:
        print("単語総数:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
