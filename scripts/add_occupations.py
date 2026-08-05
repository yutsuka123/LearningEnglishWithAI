# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""職業・職種(新設), authored by Claude (2026-08-05・ユーザー要望:「職業
職種　エンジニア　配管工…中世から現代までの主な職業や職人他　あとは分類表
の職種」＋総務省「日本標準職業分類」の大分類を参考に構成).

総務省の大分類(管理的職業/専門的・技術的職業/事務/販売/サービス/保安/
農林漁業/生産工程/輸送・機械運転/建設・採掘/運搬・清掃)を土台に、
(1) 中世〜近代の伝統的職人、(2) 各大分類の現代の代表的職業、の2軸で選定。
既存DBに architect/accountant/attorney/veterinarian/interpreter/
executive/receptionist/secretary/hairdresser/electrician/locksmith/
plumber等は既に別ドメインに存在するため、それらの裸の語は避けている。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words`
table.

Run:  python scripts/add_occupations.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

D = "職業"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 中世〜近代の伝統的職人 ---
    ("blacksmith", "鍛冶屋", "名詞", "The blacksmith hammered the glowing iron into the shape of a horseshoe.", D, "600"),
    ("cobbler", "靴職人", "名詞", "The cobbler repaired the torn leather boot in less than an hour.", D, "700"),
    ("tanner", "皮なめし職人", "名詞", "A tanner treats raw animal hide until it becomes soft, durable leather.", D, "800"),
    ("cooper", "樽職人", "名詞", "A skilled cooper can build a watertight wooden barrel without using any nails.", D, "850"),
    ("stonemason", "石工", "名詞", "The stonemason carved each block by hand to fit the cathedral wall perfectly.", D, "750"),
    ("thatcher", "茅葺き職人", "名詞", "A thatcher weaves bundles of straw into a roof that can last decades.", D, "850"),
    ("miller (occupation)", "粉屋・製粉業者", "名詞", "The miller ground the farmers' wheat into flour at the old water mill.", D, "700"),
    ("tailor", "仕立て屋", "名詞", "The tailor took careful measurements before cutting the expensive fabric.", D, "600"),
    ("wheelwright", "車輪職人", "名詞", "A wheelwright built and repaired the wooden wheels of carts and wagons.", D, "850"),
    ("glassblower", "ガラス職人", "名詞", "The glassblower shaped the molten glass with a long hollow pipe.", D, "800"),
    ("journeyman", "職人（見習いを終えた）", "名詞", "After finishing his apprenticeship, he worked as a journeyman for several more years.", D, "800"),
    ("apprenticeship", "見習い期間・徒弟制度", "名詞", "Her apprenticeship under the master carpenter lasted seven years.", D, "700"),
    ("blacksmithing", "鍛冶（技術）", "名詞", "Blacksmithing requires both physical strength and a great deal of patience.", D, "750"),
    ("candlemaker", "ろうそく職人", "名詞", "The candlemaker melted the wax and dipped each wick by hand.", D, "700"),
    # --- 専門的・技術的職業 ---
    ("civil servant", "公務員", "名詞", "She has worked as a civil servant at the city hall for fifteen years.", D, "600"),
    ("actuary", "アクチュアリー（保険数理士）", "名詞", "An actuary calculates the risk and cost of insuring a large group of people.", D, "900"),
    ("surveyor", "測量士", "名詞", "The surveyor marked the exact boundary of the property with small stakes.", D, "750"),
    ("dietitian", "栄養士", "名詞", "The hospital's dietitian planned every meal for patients with diabetes.", D, "700"),
    ("paralegal", "パラリーガル（弁護士助手）", "名詞", "The paralegal prepared the documents the lawyer needed for the trial.", D, "800"),
    # --- 事務 ---
    ("data entry clerk", "データ入力事務員", "名詞", "A data entry clerk typed the handwritten forms into the company's database.", D, "550"),
    ("bookkeeper", "簿記係", "名詞", "The bookkeeper recorded every transaction the small shop made that week.", D, "650"),
    ("switchboard operator", "電話交換手", "名詞", "The switchboard operator connected callers to the right department by hand.", D, "800"),
    # --- 販売 ---
    ("shop assistant", "店員・販売員", "名詞", "A shop assistant helped her find the right size in the back room.", D, "500"),
    ("street vendor", "行商人・屋台の売り手", "名詞", "The street vendor sold roasted chestnuts from a small cart.", D, "600"),
    ("door-to-door salesperson", "訪問販売員", "名詞", "A door-to-door salesperson used to visit every house on the block.", D, "700"),
    # --- サービス業 ---
    ("flight attendant", "客室乗務員", "名詞", "The flight attendant demonstrated how to use the oxygen mask.", D, "550"),
    ("concierge", "コンシェルジュ", "名詞", "The hotel concierge booked them a table at the city's best restaurant.", D, "700"),
    ("bartender", "バーテンダー", "名詞", "The bartender mixed the cocktail without even glancing at the recipe.", D, "550"),
    ("housekeeper", "家政婦・清掃係", "名詞", "The housekeeper cleaned every room before the next guests arrived.", D, "550"),
    ("undertaker", "葬儀屋", "名詞", "The undertaker arranged every detail of the funeral for the grieving family.", D, "750"),
    # --- 保安 ---
    ("firefighter", "消防士", "名詞", "The firefighter carried the child safely out of the burning building.", D, "500"),
    ("lifeguard", "ライフガード（監視員）", "名詞", "The lifeguard spotted the swimmer struggling and dove in immediately.", D, "550"),
    ("customs officer", "税関職員", "名詞", "The customs officer asked to see the receipts for everything in the suitcase.", D, "700"),
    ("prison guard", "刑務官", "名詞", "A prison guard walks the same corridors on every shift.", D, "700"),
    # --- 農林漁業 ---
    ("fisherman", "漁師", "名詞", "The fisherman set out before dawn to reach the best fishing grounds.", D, "500"),
    ("forester", "林業家・森林管理者", "名詞", "The forester decided which trees were ready to be harvested this year.", D, "750"),
    ("shepherd", "羊飼い", "名詞", "The shepherd led the flock down from the mountain before the storm hit.", D, "650"),
    ("beekeeper", "養蜂家", "名詞", "The beekeeper checked each hive for signs of disease.", D, "700"),
    # --- 生産工程 ---
    ("factory worker", "工場労働者", "名詞", "A factory worker assembles the same part hundreds of times a day.", D, "550"),
    ("machine operator", "機械オペレーター", "名詞", "The machine operator shut down the line as soon as the alarm sounded.", D, "650"),
    ("quality inspector", "品質検査員", "名詞", "A quality inspector checks every unit before it leaves the factory.", D, "700"),
    ("assembly line worker", "組立ライン作業員", "名詞", "An assembly line worker focuses on just one step of the whole process.", D, "600"),
    # --- 輸送・機械運転 ---
    ("truck driver", "トラック運転手", "名詞", "The truck driver had been on the road for nearly ten hours.", D, "500"),
    ("ship captain", "船長", "名詞", "The ship captain decided to wait out the storm before entering the harbor.", D, "600"),
    ("crane operator", "クレーン操縦士", "名詞", "The crane operator lifted the steel beam high above the construction site.", D, "700"),
    ("forklift operator", "フォークリフト運転手", "名詞", "A forklift operator moves heavy pallets around the warehouse all day.", D, "650"),
    ("air traffic controller", "航空管制官", "名詞", "The air traffic controller guided three planes safely through the storm.", D, "800"),
    # --- 建設・採掘 ---
    ("bricklayer", "煉瓦職人・左官", "名詞", "The bricklayer finished an entire wall before lunch.", D, "650"),
    ("roofer", "屋根職人", "名詞", "A roofer replaced every shingle after the hailstorm damaged the house.", D, "650"),
    ("scaffolder", "足場職人", "名詞", "The scaffolder assembled the metal framework around the tall building.", D, "800"),
    ("miner", "鉱山労働者", "名詞", "The miner worked hundreds of meters below the surface.", D, "600"),
    ("excavator operator", "掘削機オペレーター", "名詞", "The excavator operator dug the foundation for the new building.", D, "750"),
    # --- 運搬・清掃 ---
    ("mover (occupation)", "引越し業者", "名詞", "The movers carried the heavy sofa down three flights of stairs.", D, "550"),
    ("custodian", "用務員・清掃員", "名詞", "The school custodian unlocked the gym early every morning.", D, "600"),
    ("garbage collector", "ゴミ収集作業員", "名詞", "The garbage collector emptied every bin along the street before sunrise.", D, "600"),
    ("delivery driver", "配達員", "名詞", "The delivery driver dropped off packages at nearly forty houses that day.", D, "500"),
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
