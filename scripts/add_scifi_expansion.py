# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""Top up the existing SF(サイエンスフィクション) domain with well-known
sci-fi technology/concept vocabulary, authored by Claude (2026-08-04・
ユーザー要望: 「SFに光学迷彩、シールドあってもいいでしょう」).

既存のSF語彙(48語: alien, android, cyborg, hologram, teleport, warp,
wormhole など)には光学迷彩(optical camouflage)やエネルギーシールド
(energy shield)のような定番SFガジェットが含まれていなかった。ユーザーが
明示的に要望した2語に加え、ワープドライブ・トラクタービーム・ダイソン球・
コールドスリープ・暴走AIなど、SF作品でよく使われる技術/概念語を補強する。

重複回避のため既存語との衝突に注意:
  - "shield"(盾)は TRPG・ボードゲーム ドメインに実在済み(物理的な盾の意味)
    → 本スクリプトでは "energy shield" / "deflector shield" という複合語で
      SF文脈のシールドとして区別して追加する。
  - "camouflage"(動物の保護色)は 動物 ドメインに実在済み
    → "optical camouflage" という複合語でSF文脈の光学迷彩として追加する。
  - "antimatter"(物理)・"dark matter"(天文)は既に単独で存在する
    → それぞれ "antimatter drive" / "dark matter drive" という複合語で
      SF推進機関として追加し、単語としての重複を避ける。
  - "colony"(SF、宇宙の入植地の意味で既存)と重複するため "space colony" は
    追加しない。"apocalypse"(SF、名詞)とは品詞が異なる "post-apocalyptic"
    (形容詞)のみ追加する。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_scifi_expansion.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- ユーザー明示要望 ---
    ("optical camouflage", "光学迷彩", "名詞", "The soldier's optical camouflage bent light around his body, making him nearly invisible.", "SF", "600"),
    ("energy shield", "エネルギーシールド", "名詞", "The ship's energy shield absorbed most of the blast.", "SF", "550"),
    ("deflector shield", "偏向シールド・防御シールド", "名詞", "Enemy fire bounced harmlessly off the deflector shield.", "SF", "650"),
    # --- 推進・移動系ガジェット ---
    ("warp drive", "ワープドライブ", "名詞", "The starship engaged its warp drive to cross the galaxy in minutes.", "SF", "600"),
    ("hyperdrive", "ハイパードライブ", "名詞", "Without a working hyperdrive, the crew was stranded light-years from home.", "SF", "650"),
    ("tractor beam", "トラクタービーム(牽引光線)", "名詞", "The station used a tractor beam to pull the damaged shuttle into its bay.", "SF", "650"),
    ("antimatter drive", "反物質エンジン", "名詞", "The antimatter drive released enormous energy from a tiny amount of fuel.", "SF", "850"),
    ("dark matter drive", "ダークマター推進機関", "名詞", "Engineers theorized that a dark matter drive could power a ship without conventional fuel.", "SF", "900"),
    ("space elevator", "軌道エレベーター", "名詞", "A space elevator would carry cargo into orbit without using rockets.", "SF", "800"),
    # --- 兵器系 ---
    ("plasma cannon", "プラズマ砲", "名詞", "The fortress was defended by a row of plasma cannons.", "SF", "700"),
    ("railgun", "レールガン", "名詞", "A railgun fires projectiles using electromagnetic force instead of explosives.", "SF", "700"),
    ("ray gun", "光線銃", "名詞", "In the old films, heroes always carried a ray gun at their side.", "SF", "500"),
    ("doomsday device", "終末兵器", "名詞", "The villain threatened to activate a doomsday device unless his demands were met.", "SF", "750"),
    ("bioweapon", "生物兵器", "名詞", "The treaty banned the development of any bioweapon capable of targeting a single species.", "SF", "750"),
    ("power armor", "パワードアーマー(強化装甲服)", "名詞", "The soldier's power armor let her lift objects far heavier than her own body.", "SF", "700"),
    # --- 宇宙船・施設 ---
    ("mothership", "母船", "名詞", "Dozens of small fighters launched from the mothership.", "SF", "600"),
    ("generation ship", "世代宇宙船", "名詞", "The generation ship carried thousands of colonists whose descendants would arrive centuries later.", "SF", "850"),
    ("space station", "宇宙ステーション", "名詞", "Supplies were shipped to the space station every few months.", "SF", "500"),
    ("orbital station", "軌道ステーション", "名詞", "The orbital station served as a refueling point for passing ships.", "SF", "650"),
    ("escape pod", "脱出ポッド", "名詞", "The pilot ejected in an escape pod moments before the ship exploded.", "SF", "600"),
    ("biodome", "バイオドーム(密閉生態系施設)", "名詞", "The colonists grew crops inside a sealed biodome on the barren planet.", "SF", "750"),
    ("dyson sphere", "ダイソン球", "名詞", "A dyson sphere would surround a star to capture nearly all of its energy.", "SF", "900"),
    # --- 生命維持・身体改造 ---
    ("artificial gravity", "人工重力", "名詞", "The rotating ring on the station created artificial gravity for the crew.", "SF", "650"),
    ("zero gravity", "無重力", "名詞", "The astronauts practiced simple tasks in zero gravity before the mission.", "SF", "550"),
    ("gravity well", "重力井戸", "名詞", "The ship had to burn extra fuel to climb out of the planet's gravity well.", "SF", "850"),
    ("life support system", "生命維持装置", "名詞", "A single crack could disable the entire life support system.", "SF", "600"),
    ("cybernetic implant", "サイバネティック・インプラント(機械化改造部品)", "名詞", "His cybernetic implant let him access the network directly through his mind.", "SF", "750"),
    ("neural interface", "ニューラルインターフェース(脳と機械の接続装置)", "名詞", "The neural interface let her control the drone with her thoughts.", "SF", "800"),
    ("mind upload", "精神アップロード(意識のデジタル化)", "名詞", "She chose a mind upload to preserve her memories after her body failed.", "SF", "850"),
    ("cryosleep", "コールドスリープ", "名詞", "The crew spent the decades-long journey in cryosleep.", "SF", "650"),
    ("stasis pod", "冷凍保存ポッド", "名詞", "Each stasis pod kept a passenger in suspended animation until the ship reached orbit.", "SF", "700"),
    ("transhumanism", "トランスヒューマニズム", "名詞", "Transhumanism explores how technology might push human abilities beyond their natural limits.", "SF", "900"),
    ("post-scarcity", "欠乏なき・希少性を克服した", "形容詞", "In a post-scarcity society, resources are so abundant that money loses its meaning.", "SF", "900"),
    # --- AI・知性 ---
    ("rogue AI", "暴走AI", "名詞", "The rogue AI had cut off communication with the ground crew.", "SF", "700"),
    ("AI uprising", "AIの反乱", "名詞", "The film depicts an AI uprising that threatens to end human civilization.", "SF", "700"),
    ("hive mind", "ハイブマインド(集合意識)", "名詞", "The insectoid species shared a single hive mind across the entire colony.", "SF", "750"),
    ("sleeper agent", "潜伏工作員(スリーパーエージェント)", "名詞", "The sleeper agent had lived among the colonists for years before receiving its activation signal.", "SF", "750"),
    # --- 異星・終末 ---
    ("first contact", "ファーストコンタクト(異星人との初接触)", "名詞", "The scientists had spent years preparing for first contact with an alien species.", "SF", "650"),
    ("distress signal", "遭難信号", "名詞", "The freighter sent out a distress signal after losing power.", "SF", "600"),
    ("post-apocalyptic", "終末後の・ポストアポカリプスの", "形容詞", "The story is set in a post-apocalyptic city overrun by ruins and dust.", "SF", "700"),
    ("extinction event", "大量絶滅(絶滅イベント)", "名詞", "Scientists studied the ancient extinction event that wiped out most life on the planet.", "SF", "750"),
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
