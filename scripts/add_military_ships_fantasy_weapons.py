# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add modern naval/military hardware vocabulary to the existing 軍事(military)
domain, plus classic Western/medieval-fantasy melee & ranged weapon vocabulary
to the existing TRPG・ボードゲーム domain, authored by Claude
(2026-08-04・ユーザー要望: 「イージス艦は追加であってもいいねえ」「トライデントとか
バトルアックスの類で欧米圏の武器多いじゃないそれも追加しておくといいかも RPG系」)。

GROUP A (domain='軍事'): 既存70語(admiral, aircraft carrier, ... warship,
weapon など)には現代の艦艇・装備の語彙が薄かったため、イージス艦・コルベット・
掃海艇・魚雷・爆雷などの現代海軍ハードウェア用語を追加する。既存70語との重複
(destroyer, frigate, armor など)は含めない。

GROUP B (domain='TRPG・ボードゲーム'): scripts/add_tabletop_trpg.py で追加した
既存語彙(TRPG基本用語・ボードゲーム基本用語)には武器そのものの語彙がなかった
ため、トライデント・バトルアックス・メイス・ハルバードなど、RPG/TRPG/ファン
タジー作品でよく見る欧米圏の近接・投射武器の語彙を追加する。

すべて実在の一般語彙で、製造・運用手順などの実用的な内容は含まない(用語の意味
のみを扱う中立的な語彙・例文)。例文はすべてオリジナルで、暴力的・扇動的な表現
を避けた説明的な内容にしている。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_military_ships_fantasy_weapons.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- GROUP A: 軍事(現代の艦艇・装備) ---
    ("Aegis-class destroyer", "イージス艦", "名詞", "The Aegis-class destroyer joined the fleet for a joint naval exercise.", "軍事", "850"),
    ("guided-missile destroyer", "ミサイル駆逐艦", "名詞", "The guided-missile destroyer escorted the carrier through international waters.", "軍事", "800"),
    ("Aegis combat system", "イージス戦闘システム", "名詞", "The Aegis combat system can track multiple targets at once using radar.", "軍事", "900"),
    ("corvette", "コルベット艦", "名詞", "A corvette is smaller and faster than a frigate.", "軍事", "800"),
    ("minesweeper", "掃海艇", "名詞", "The minesweeper cleared the harbor entrance of old naval mines.", "軍事", "800"),
    ("landing craft", "上陸用舟艇", "名詞", "Landing craft carried troops and vehicles from ship to shore.", "軍事", "750"),
    ("torpedo", "魚雷", "名詞", "The submarine was designed to fire torpedoes underwater.", "軍事", "700"),
    ("depth charge", "爆雷", "名詞", "A depth charge explodes underwater to damage a submerged submarine.", "軍事", "800"),
    ("anti-ship missile", "対艦ミサイル", "名詞", "The anti-ship missile is designed to target vessels at sea.", "軍事", "800"),
    ("surface-to-air missile", "地対空(艦対空)ミサイル", "名詞", "A surface-to-air missile can intercept aircraft from the ground or a ship.", "軍事", "850"),
    ("phased array radar", "フェーズドアレイレーダー", "名詞", "The phased array radar can scan the sky in several directions at once.", "軍事", "900"),
    ("flagship", "旗艦", "名詞", "The admiral commanded the fleet from the flagship.", "軍事", "700"),
    ("escort ship", "護衛艦", "名詞", "An escort ship protects larger vessels such as carriers from attack.", "軍事", "700"),
    ("patrol boat", "哨戒艇", "名詞", "The patrol boat monitors the coastline for illegal fishing.", "軍事", "650"),
    ("hovercraft", "ホバークラフト", "名詞", "A hovercraft can travel over both water and land.", "軍事", "600"),
    ("naval base", "海軍基地", "名詞", "Sailors returned to the naval base after a six-month deployment.", "軍事", "600"),
    ("port call", "寄港", "名詞", "The ship made a port call in Singapore for supplies and repairs.", "軍事", "750"),
    ("task force", "機動部隊・任務部隊", "名詞", "A task force of several ships was assembled for the joint exercise.", "軍事", "700"),
    ("carrier strike group", "空母打撃群", "名詞", "A carrier strike group usually includes destroyers and cruisers for protection.", "軍事", "900"),
    ("underway replenishment", "洋上補給", "名詞", "Underway replenishment lets ships refuel without returning to port.", "軍事", "950"),
    ("vertical launching system", "垂直発射装置(VLS)", "名詞", "The vertical launching system fires missiles straight up from the deck.", "軍事", "900"),
    ("flotilla", "小艦隊", "名詞", "A flotilla of small boats escorted the larger vessel into harbor.", "軍事", "850"),
    # --- GROUP B: TRPG・ボードゲーム(欧米圏の近接・投射武器) ---
    ("trident", "三叉槍(トライデント)", "名詞", "In many fantasy stories, sea gods are shown carrying a trident.", "TRPG・ボードゲーム", "650"),
    ("battle-axe", "戦斧(バトルアックス)", "名詞", "The dwarf character in the game wielded a heavy battle-axe.", "TRPG・ボードゲーム", "650"),
    ("mace", "メイス・棍棒", "名詞", "A mace is a blunt weapon with a heavy head on a handle.", "TRPG・ボードゲーム", "650"),
    ("halberd", "ハルバード(斧槍)", "名詞", "Medieval guards in old paintings are often shown holding a halberd.", "TRPG・ボードゲーム", "800"),
    ("flail", "フレイル(連接棍棒)", "名詞", "A flail has a spiked ball attached to a handle by a chain.", "TRPG・ボードゲーム", "800"),
    ("rapier", "レイピア(細身の剣)", "名詞", "The rapier was popular among duelists in the sixteenth century.", "TRPG・ボードゲーム", "700"),
    ("broadsword", "ブロードソード(幅広剣)", "名詞", "The knight's character sheet listed a broadsword as his main weapon.", "TRPG・ボードゲーム", "700"),
    ("longsword", "ロングソード(長剣)", "名詞", "He chose a longsword for his character in the new campaign.", "TRPG・ボードゲーム", "650"),
    ("warhammer", "ウォーハンマー(戦鎚)", "名詞", "The warhammer deals extra damage against armored enemies in the game.", "TRPG・ボードゲーム", "700"),
    ("scimitar", "シミター(三日月刀)", "名詞", "The scimitar is a curved sword often associated with desert warriors in fiction.", "TRPG・ボードゲーム", "800"),
    ("quarterstaff", "クォータースタッフ(棒術用の長い棒)", "名詞", "A quarterstaff is a simple wooden weapon used in many fantasy settings.", "TRPG・ボードゲーム", "800"),
    ("dagger", "短剣・ダガー", "名詞", "Her rogue character preferred a dagger over a heavier weapon.", "TRPG・ボードゲーム", "550"),
    ("shield", "盾", "名詞", "A shield can block attacks in both real combat and tabletop games.", "TRPG・ボードゲーム", "400"),
    ("buckler", "バックラー(小型の盾)", "名詞", "A buckler is small enough to be strapped to the forearm.", "TRPG・ボードゲーム", "800"),
    ("spear", "槍", "名詞", "The party's fighter carried a long spear into the dungeon.", "TRPG・ボードゲーム", "500"),
    ("javelin", "投げ槍(ジャベリン)", "名詞", "A javelin is a light spear meant to be thrown at a target.", "TRPG・ボードゲーム", "650"),
    ("sling", "スリング(投石具)", "名詞", "In the story, the hero defeats the giant with a simple sling.", "TRPG・ボードゲーム", "650"),
    ("morning star", "モーニングスター(棘付き棍棒)", "名詞", "A morning star combines a club with metal spikes on the head.", "TRPG・ボードゲーム", "850"),
    ("glaive", "グレイブ(長柄武器)", "名詞", "A glaive has a long blade mounted on a pole.", "TRPG・ボードゲーム", "850"),
    ("pike", "パイク(長槍)", "名詞", "Soldiers in some historical battles formed lines using long pikes.", "TRPG・ボードゲーム", "700"),
    ("claymore", "クレイモア(両手持ちの大剣)", "名詞", "A claymore is a large two-handed sword from Scottish history.", "TRPG・ボードゲーム", "800"),
    ("kite shield", "カイトシールド(凧型盾)", "名詞", "The kite shield's long shape protects the legs as well as the torso.", "TRPG・ボードゲーム", "800"),
    ("chainmail", "鎖帷子(チェインメイル)", "名詞", "Chainmail is made of many small interlocking metal rings.", "TRPG・ボードゲーム", "700"),
    ("plate armor", "プレートアーマー(板金鎧)", "名詞", "Plate armor covers the body with solid metal plates.", "TRPG・ボードゲーム", "700"),
]

PHRASES: list[tuple[str, str]] = [
    ("The fleet was escorted by two destroyers.", "艦隊は2隻の駆逐艦に護衛されていた。"),
    ("He wielded a longsword in the final battle.", "彼は最後の戦いでロングソードを振るった。"),
    ("The corvette patrolled the coastline all night.", "そのコルベット艦は一晩中沿岸を哨戒していた。"),
    ("She chose a shield and a short spear for her character.", "彼女はキャラクターに盾と短い槍を選んだ。"),
    ("The carrier strike group left port at dawn.", "空母打撃群は夜明けに出港した。"),
    ("A dagger is easier to conceal than a sword.", "短剣は剣よりも隠しやすい。"),
    ("The minesweeper cleared a safe path through the harbor.", "掃海艇は港内に安全な航路を確保した。"),
    ("The knight's plate armor gleamed in the sunlight.", "その騎士のプレートアーマーは日差しを受けて輝いていた。"),
    ("The submarine fired a single torpedo during the drill.", "その潜水艦は訓練中に魚雷を1発発射した。"),
    ("In the story, the hero relies on a trident, not a sword.", "その物語では、主人公は剣ではなく三叉槍を頼りにしている。"),
    ("The task force included three frigates and one destroyer.", "その任務部隊にはフリゲート艦3隻と駆逐艦1隻が含まれていた。"),
    ("A battle-axe is heavier and slower than a longsword.", "戦斧はロングソードより重く、扱いに時間がかかる。"),
    ("The ship made a brief port call before heading out again.", "その船は再び出港する前に短時間寄港した。"),
    ("The GM described a guard holding a halberd at the gate.", "GMは門に立つ衛兵がハルバードを持っていると描写した。"),
]


def main() -> int:
    with db() as conn:
        existing_words = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing_words:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing_words.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")

    with db() as conn:
        existing_phrases = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in existing_phrases:
                p_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, '軍事・ファンタジー武器の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
