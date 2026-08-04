# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""Top up the existing 軍事(military) domain with war-crimes / international-
humanitarian-law / nuclear-nonproliferation / alliance / strategy vocabulary,
authored by Claude (2026-08-04・ユーザー要望:「戦争軍事になるのかもしれま
せんが、戦争犯罪とか大量虐殺 非人道兵器 戦争の負の部分の用語も追加した
い…核拡散防止条約 nato 同盟 非対称戦 戦略 戦術 他多面的に」).

既存の軍事語彙(116件超)は階級・装備・艦艇種別が中心で、戦争犯罪/国際人道
法/大量破壊兵器の規制/核不拡散/同盟・国際安全保障機構/戦略論といった
「戦争の負の側面・法的/国際関係的な語彙」が欠けていた。これを補強する。

TONE: このスクリプトの語彙・例文はすべて国際政治学/国際法の教科書用語集
と同じ、事実・歴史・法律に基づいた中立的な語り口とする。暴力を賛美したり
兵器の性能・設計・使用法を指南する内容は一切含めない。既存の化学兵器語彙
(sarin / mustard gas / nerve agent / chemical weapon — domain='化学')と同じ
「歴史的・教育的事実として扱う」前例を踏襲したもの。例文は特定の現在進行
中の紛争・特定国を「加害者」として名指しすること、特定の政治指導者名を出
すことを避け、史実(第二次世界大戦、ニュルンベルク裁判、冷戦期の軍拡競争
など)か一般化された記述にとどめている。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased) against
the full live `words` table (a dedup check confirmed "atrocity", "nuclear
warhead", "containment", "alliance", "strategy", "tactics", "armistice",
"ceasefire", "treaty" etc. already exist elsewhere in the DB, so this list
avoids the bare forms and uses military-specific compound terms instead,
e.g. "military strategy" / "military tactics" rather than the bare words).

Run:  python scripts/add_war_international_security.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 戦争犯罪・国際人道法 ---
    ("war crime", "戦争犯罪", "名詞", "The court found the officer guilty of a war crime.", "軍事", "600"),
    ("crime against humanity", "人道に対する罪", "名詞", "The prosecutor described the attacks as crimes against humanity.", "軍事", "750"),
    ("genocide", "集団殺害・ジェノサイド", "名詞", "The term genocide was coined in 1944 to describe the deliberate destruction of a national or ethnic group.", "軍事", "700"),
    ("ethnic cleansing", "民族浄化", "名詞", "Historians use the term ethnic cleansing for the forced removal of an ethnic group from an area.", "軍事", "800"),
    ("Geneva Convention", "ジュネーブ条約", "名詞", "The Geneva Convention sets rules for the treatment of wounded soldiers and prisoners in wartime.", "軍事", "700"),
    ("international humanitarian law", "国際人道法", "名詞", "International humanitarian law limits the methods and means of warfare.", "軍事", "850"),
    ("International Criminal Court", "国際刑事裁判所", "名詞", "The International Criminal Court was established in 2002 to prosecute genocide and war crimes.", "軍事", "800"),
    ("prisoner of war", "捕虜", "名詞", "The Geneva Convention protects the rights of a prisoner of war.", "軍事", "600"),
    ("combatant status", "戦闘員資格", "名詞", "Combatant status determines whether a captured fighter is treated as a prisoner of war.", "軍事", "850"),
    ("civilian casualty", "民間人の犠牲者", "名詞", "Reducing civilian casualties is a central goal of the laws of war.", "軍事", "700"),
    ("collateral damage", "(軍事作戦に伴う)巻き添え被害", "名詞", "Military planners try to minimize collateral damage to nearby homes and hospitals.", "軍事", "750"),
    ("war crimes tribunal", "戦争犯罪法廷", "名詞", "The Nuremberg trials were the first major war crimes tribunal in modern history.", "軍事", "800"),
    ("indict for war crimes", "戦争犯罪で起訴する", "動詞", "The tribunal indicted several former officials for war crimes.", "軍事", "800"),
    ("human rights violation", "人権侵害", "名詞", "The report documented numerous human rights violations during the conflict.", "軍事", "650"),
    ("forced displacement", "強制退去・強制移住", "名詞", "Forced displacement occurs when people are made to leave their homes against their will.", "軍事", "800"),
    ("refugee crisis", "難民危機", "名詞", "The war triggered a refugee crisis in neighboring countries.", "軍事", "650"),
    # --- 非人道兵器・軍備規制条約 ---
    ("inhumane weapon", "非人道的兵器", "名詞", "International law bans weapons considered inhumane because they cause unnecessary suffering.", "軍事", "750"),
    ("indiscriminate weapon", "無差別兵器", "名詞", "An indiscriminate weapon cannot distinguish between combatants and civilians.", "軍事", "800"),
    ("landmine", "地雷", "名詞", "A landmine can remain dangerous for decades after a war ends.", "軍事", "550"),
    ("cluster munition", "クラスター弾", "名詞", "A cluster munition scatters many small bomblets over a wide area.", "軍事", "800"),
    ("Chemical Weapons Convention", "化学兵器禁止条約", "名詞", "The Chemical Weapons Convention entered into force in 1997 and bans the production of chemical weapons.", "軍事", "850"),
    ("Biological Weapons Convention", "生物兵器禁止条約", "名詞", "The Biological Weapons Convention was the first treaty to ban an entire category of weapons.", "軍事", "850"),
    ("weapons of mass destruction", "大量破壊兵器", "名詞", "Weapons of mass destruction include nuclear, chemical, and biological weapons.", "軍事", "700"),
    ("WMD", "大量破壊兵器(略語)", "名詞", "Inspectors searched the site for evidence of WMD programs.", "軍事", "700"),
    # --- 核不拡散・軍縮 ---
    ("Non-Proliferation Treaty", "核拡散防止条約", "名詞", "The Non-Proliferation Treaty aims to prevent the spread of nuclear weapons.", "軍事", "750"),
    ("NPT", "核拡散防止条約(略語)", "名詞", "Nearly every country in the world has signed the NPT.", "軍事", "750"),
    ("nuclear disarmament", "核軍縮", "名詞", "Nuclear disarmament refers to the reduction or elimination of nuclear weapons.", "軍事", "700"),
    ("nuclear deterrence", "核抑止", "名詞", "Nuclear deterrence relies on the threat of retaliation to prevent an attack.", "軍事", "800"),
    ("mutually assured destruction", "相互確証破壊", "名詞", "Mutually assured destruction shaped nuclear strategy during the Cold War.", "軍事", "900"),
    ("arms control", "軍備管理", "名詞", "Arms control treaties limit the number or type of weapons a country may hold.", "軍事", "700"),
    ("arms race", "軍拡競争", "名詞", "The Cold War arms race pushed both superpowers to build ever larger nuclear arsenals.", "軍事", "650"),
    ("nuclear-armed state", "核保有国", "名詞", "Only a small number of countries are recognized as nuclear-armed states.", "軍事", "800"),
    # --- 同盟・国際安全保障機構 ---
    ("NATO", "NATO・北大西洋条約機構", "名詞", "NATO was founded in 1949 as a collective defense alliance.", "軍事", "550"),
    ("military alliance", "軍事同盟", "名詞", "A military alliance commits its members to defend one another if attacked.", "軍事", "600"),
    ("collective security", "集団安全保障", "名詞", "Collective security means that an attack on one member is treated as an attack on all.", "軍事", "800"),
    ("coalition forces", "連合軍", "名詞", "Coalition forces from several countries took part in the operation.", "軍事", "650"),
    ("peacekeeping force", "平和維持軍", "名詞", "A UN peacekeeping force was deployed to monitor the ceasefire.", "軍事", "650"),
    ("peacekeeping mission", "平和維持活動(ミッション)", "名詞", "The peacekeeping mission lasted for over a decade.", "軍事", "650"),
    ("UN Security Council", "国連安全保障理事会", "名詞", "The UN Security Council can authorize sanctions or the use of force.", "軍事", "600"),
    # --- 戦略・戦術・戦争の類型 ---
    ("military strategy", "軍事戦略", "名詞", "Military strategy concerns the overall planning of a war or campaign.", "軍事", "600"),
    ("military tactics", "軍事戦術", "名詞", "Military tactics deal with how individual battles are fought.", "軍事", "600"),
    ("asymmetric warfare", "非対称戦", "名詞", "Asymmetric warfare occurs when opposing forces differ greatly in size or strength.", "軍事", "850"),
    ("guerrilla warfare", "ゲリラ戦", "名詞", "Guerrilla warfare relies on small, mobile units rather than large conventional armies.", "軍事", "700"),
    ("proxy war", "代理戦争", "名詞", "During the Cold War, the two superpowers often fought through proxy wars in other countries.", "軍事", "750"),
    ("hybrid warfare", "ハイブリッド戦", "名詞", "Hybrid warfare combines conventional military force with cyberattacks and disinformation.", "軍事", "850"),
    ("cyberwarfare", "サイバー戦", "名詞", "Cyberwarfare targets computer networks and infrastructure rather than physical territory.", "軍事", "750"),
    ("containment strategy", "封じ込め戦略", "名詞", "The containment strategy aimed to limit the spread of a rival power's influence without direct war.", "軍事", "800"),
    ("scorched earth", "焦土作戦・焦土戦術", "名詞", "A scorched earth tactic involves destroying resources an advancing enemy might use.", "軍事", "800"),
    ("attrition warfare", "消耗戦", "名詞", "Attrition warfare aims to wear down the enemy's resources and manpower over time.", "軍事", "850"),
    ("preemptive strike", "先制攻撃", "名詞", "A preemptive strike is launched in anticipation of an imminent attack by an adversary.", "軍事", "750"),
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
