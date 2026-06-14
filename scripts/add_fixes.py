# ruff: noqa: E501  (data-heavy maintenance/seed script)
"""(1) Improve / correct Japanese glosses (add second senses, fix narrow ones).
(2) Add American-vs-British English pairs (domain 米英の違い).
Authored by Claude — no app/OpenAI API calls.

Run:  python scripts/add_fixes.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# english (lowercased match) -> improved japanese gloss.
FIXES: dict[str, str] = {
    "decimal": "小数・10進数",
    "solution": "溶液・解決(策)",
    "compound": "化合物・複合の",
    "reaction": "反応・反作用",
    "deduction": "演繹・(金額の)控除",
    "induction": "帰納・誘導",
    "premise": "前提（premises で構内・敷地）",
    "galley": "ガレー船・(船内の)調理室",
    "knot": "ノット(速度)・結び目",
    "yield": "(進路を)譲る・産出する/利回り",
    "major": "(軍)少佐・主要な",
    "general": "将軍・大将（形: 一般の）",
    "pitch": "音の高さ・ピッチ（投球・売り込みの意も）",
    "chord": "和音・コード",
    "mass": "質量・大量（ミサの意も）",
    "root": "根・根源（数学の√も）",
    "trunk": "幹・(車の)トランク・(象の)鼻",
    "bark": "樹皮・(犬が)吠える",
    "bat": "コウモリ・バット",
    "seal": "アザラシ・印章／密封する",
    "relay": "リレー・中継（リレー競走）",
    "terminal": "端子・終着駅（形: 末期の）",
    "stroke": "脳卒中・一打／(水泳の)ストローク",
    "sentence": "判決・刑／(文法の)文",
    "appeal": "上訴・控訴／訴え・魅力",
    "hearing": "審理・公聴会／聴覚",
    "plea": "(法廷の)答弁・嘆願",
    "settlement": "和解／入植地・清算",
    "tank": "戦車・(貯水)タンク",
    "probe": "探査機・精査する",
    "booster": "補助ロケット・押し上げるもの",
    "current": "電流（形: 現在の／海流）",
    "vector": "ベクトル（生物では媒介動物）",
    "capsule": "宇宙カプセル・カプセル／被膜",
    "serve": "サーブ・給仕する／務める",
    "organ": "臓器・(楽器の)オルガン",
    "trial": "裁判・公判／試み",
    "vessel": "船舶・(体の)血管／容器",
    "calf": "ふくらはぎ・子牛",
    "temple": "こめかみ・寺院",
    "palm": "手のひら・ヤシ",
    "dynamics": "動力学・力学（音楽では強弱法）",
    "scale": "尺度・規模（音階・うろこの意も）",
    "note": "メモ・(音楽の)音符",
    "draft": "下書き・草案（製図・徴兵・すきま風の意も）",
    "spring": "春・ばね（泉・跳ねる）",
    "conductor": "指揮者・車掌・(電気の)導体",
}

# American / British pairs (domain 米英の違い).
USUK: list[tuple[str, str, str]] = [
    ("elevator / lift", "エレベーター（米 elevator / 英 lift）", "Take the elevator (US) to the top floor."),
    ("apartment / flat", "アパート・マンション（米 apartment / 英 flat）", "They rent a small apartment (US)."),
    ("truck / lorry", "トラック（米 truck / 英 lorry）", "A truck (US) blocked the road."),
    ("gasoline / petrol", "ガソリン（米 gas, gasoline / 英 petrol）", "We stopped to buy gas (US)."),
    ("subway / underground", "地下鉄（米 subway / 英 underground, the Tube）", "Take the subway (US) downtown."),
    ("cookie / biscuit", "クッキー（米 cookie / 英 biscuit）", "She baked some cookies (US)."),
    ("candy / sweets", "お菓子・あめ（米 candy / 英 sweets）", "The kids love candy (US)."),
    ("fall / autumn", "秋（米 fall / 英 autumn）", "Leaves turn red in the fall (US)."),
    ("vacation / holiday", "休暇（米 vacation / 英 holiday）", "We took a summer vacation (US)."),
    ("soccer / football", "サッカー（米 soccer / 英 football）", "He plays soccer (US) on weekends."),
    ("pants / trousers", "ズボン（米 pants / 英 trousers ※英で pants は下着）", "He wore black pants (US)."),
    ("diaper / nappy", "おむつ（米 diaper / 英 nappy）", "She changed the baby's diaper (US)."),
    ("flashlight / torch", "懐中電灯（米 flashlight / 英 torch）", "Bring a flashlight (US)."),
    ("trash / rubbish", "ごみ（米 trash, garbage / 英 rubbish）", "Take out the trash (US)."),
    ("line / queue", "(順番待ちの)列（米 line / 英 queue）", "We waited in line (US)."),
    ("store / shop", "店（米 store / 英 shop）", "I bought it at the store (US)."),
    ("sidewalk / pavement", "歩道（米 sidewalk / 英 pavement）", "Walk on the sidewalk (US)."),
    ("faucet / tap", "蛇口（米 faucet / 英 tap）", "Turn off the faucet (US)."),
    ("cell phone / mobile", "携帯電話（米 cell phone / 英 mobile）", "My cell phone (US) died."),
    ("movie / film", "映画（米 movie / 英 film）", "Let's watch a movie (US)."),
    ("french fries / chips", "フライドポテト（米 fries / 英 chips）", "I ordered fries (US)."),
    ("potato chips / crisps", "ポテトチップス（米 chips / 英 crisps）", "He opened a bag of chips (US)."),
    ("eraser / rubber", "消しゴム（米 eraser / 英 rubber）", "May I borrow your eraser (US)?"),
    ("mailbox / postbox", "郵便ポスト（米 mailbox / 英 postbox）", "Drop it in the mailbox (US)."),
    ("hood / bonnet", "(車の)ボンネット（米 hood / 英 bonnet）", "He opened the hood (US)."),
    ("trunk / boot", "(車の)トランク（米 trunk / 英 boot）", "Put the bags in the trunk (US)."),
    ("freeway / motorway", "高速道路（米 freeway, highway / 英 motorway）", "Take the freeway (US)."),
    ("check / bill", "(飲食店の)勘定（米 check / 英 bill）", "Could I get the check (US)?"),
    ("zip code / postcode", "郵便番号（米 zip code / 英 postcode）", "Write your zip code (US) here."),
    ("restroom / toilet", "トイレ（米 restroom / 英 toilet, loo）", "Where's the restroom (US)?"),
    ("sweater / jumper", "セーター（米 sweater / 英 jumper）", "Put on a sweater (US); it's cold."),
    ("sneakers / trainers", "スニーカー（米 sneakers / 英 trainers）", "He bought new sneakers (US)."),
    ("cart / trolley", "(買い物)カート（米 cart / 英 trolley）", "She pushed the cart (US)."),
    ("drugstore / chemist", "薬局（米 drugstore, pharmacy / 英 chemist）", "Buy it at the drugstore (US)."),
    ("parking lot / car park", "駐車場（米 parking lot / 英 car park）", "The parking lot (US) is full."),
    ("one-way / single", "片道(切符)（米 one-way / 英 single）", "A one-way (US) ticket, please."),
    ("round-trip / return", "往復(切符)（米 round-trip / 英 return）", "A round-trip (US) ticket, please."),
    ("first floor / ground floor", "1階（米 first floor / 英 ground floor ※英の1st floorは2階）", "The cafe is on the first floor (US)."),
    ("math / maths", "数学（米 math / 英 maths）", "I'm good at math (US)."),
    ("color / colour", "色（米 color / 英 colour）: つづりの違い", "What's your favorite color (US)?"),
    ("center / centre", "中心（米 center / 英 centre）: つづりの違い", "Meet at the town center (US)."),
    ("theater / theatre", "劇場（米 theater / 英 theatre）: つづりの違い", "We went to the theater (US)."),
    ("organize / organise", "整理する（米 organize / 英 organise）: つづりの違い", "Let's organize (US) the files."),
]


def main() -> int:
    with db() as conn:
        fixed = 0
        for en, ja in FIXES.items():
            fixed += conn.execute(
                "UPDATE words SET japanese = ? WHERE LOWER(english) = LOWER(?)",
                (ja, en),
            ).rowcount

        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, ex in USUK:
            if en.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, "", ex, "米英の違い", "500"),
            )
            existing.add(en.lower())
            added += 1

    print(f"glosses fixed: {fixed}")
    print(f"US/UK pairs: +{added} (skipped {skipped})")
    with db() as conn:
        print("totals -> words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
              "/ without example:",
              conn.execute("SELECT COUNT(*) FROM words WHERE COALESCE(example,'')=''").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
