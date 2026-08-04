# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add digital/video-game RPG vocabulary and phrases — mechanics and genre
terminology for discussing JRPGs, action-RPGs, and open-world RPGs
generically — authored by Claude (2026-08-04・ユーザー要望).

This is a deliberate third leg alongside the two existing gaming scripts:
scripts/add_tabletop_trpg.py covers tabletop/board-game vocabulary (dice,
game master, worker placement, etc.) and scripts/add_gaming_discord.py
covers generic online-gaming/Discord slang (patch, nerf, matchmaking,
push to talk, etc.). Both WORDS lists were read first and cross-checked so
that nothing here duplicates an english term already present in either.

対象語彙: 経験値・レベルキャップ・スキルツリー/タレントツリーといった育成
要素、ボス戦/ラスボス/中ボスといった戦闘の節目、サブクエスト/メインクエス
トといった進行要素、インベントリ/装備スロット/キャラクタークラス/ステータ
ス振り分けといった管理要素、セーブデータ/セーブポイント/ニューゲームプラ
スといったセーブ・周回要素、ターン制/リアルタイム戦闘やアクションRPG/オー
プンワールド/サンドボックス/JRPGといったジャンル用語、パーマデス/ローグ
ライク/ローグライトといった特殊ジャンル用語、クラフト/エンチャント/強化
素材といった育成システム、実績/トロフィー/コンプリート/攻略情報といった
プレイスタイル関連語。特定の商品・作品の固有名詞は一切使用せず、すべて一
般的な用語のみ。

フレーズはRPGをプレイしながら実際に交わされる自然な口語表現("I'm still
grinding for XP." "Let's take down this boss together." など)。例文・
フレーズはすべてオリジナルで、特定ゲームのテキストの引用・言い換えは
含まない。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_rpg_videogame_terms.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "ゲーム・Discordの英語"
SCENE = "ゲーム・Discord英語"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 育成・進行要素 ---
    ("experience points", "経験値", "名詞", "You'll need more experience points to reach the next level.", DOMAIN, "500"),
    ("level cap", "レベルキャップ(到達可能な上限レベル)", "名詞", "Once you hit the level cap, you can't gain more experience points.", DOMAIN, "700"),
    ("skill tree", "スキルツリー", "名詞", "Choose carefully; this skill tree only lets you pick a few nodes early on.", DOMAIN, "650"),
    ("talent tree", "タレントツリー(スキルツリーに近い育成要素)", "名詞", "The talent tree lets you specialize your character's playstyle.", DOMAIN, "700"),
    ("stat point", "ステータスポイント", "名詞", "You gain a few stat points every time you level up.", DOMAIN, "650"),
    ("stat allocation", "ステータスの振り分け", "名詞", "Careful stat allocation early on makes the late game much easier.", DOMAIN, "750"),
    ("character build", "キャラクタービルド・育成方針", "名詞", "My character build focuses on speed and critical hits.", DOMAIN, "700"),
    ("crafting system", "クラフトシステム", "名詞", "The crafting system lets you turn materials into new equipment.", DOMAIN, "650"),
    ("enchantment", "エンチャント(付与効果)", "名詞", "This enchantment adds fire damage to your weapon.", DOMAIN, "700"),
    ("upgrade material", "強化素材", "名詞", "You'll need rare upgrade material to improve that armor further.", DOMAIN, "650"),
    ("class change", "クラスチェンジ・転職", "名詞", "A class change lets you try a completely different playstyle.", DOMAIN, "700"),
    # --- 戦闘・進行の節目 ---
    ("boss battle", "ボス戦", "名詞", "The boss battle at the end of this dungeon took us three tries.", DOMAIN, "500"),
    ("final boss", "ラスボス(最終ボス)", "名詞", "The final boss has multiple phases, so save your best items.", DOMAIN, "550"),
    ("mini-boss", "中ボス", "名詞", "A mini-boss guards the entrance to the last area.", DOMAIN, "600"),
    ("side quest", "サブクエスト", "名詞", "This side quest isn't required, but it gives great rewards.", DOMAIN, "500"),
    ("main quest", "メインクエスト・本筋のクエスト", "名詞", "Let's focus on the main quest before we explore any further.", DOMAIN, "550"),
    ("random encounter", "ランダムエンカウント", "名詞", "We got interrupted by a random encounter on the way to town.", DOMAIN, "700"),
    ("loot drop", "ドロップアイテム(敵から得られる戦利品)", "名詞", "Every loot drop from a mini-boss includes at least one useful item.", DOMAIN, "600"),
    ("turn-based combat", "ターン制バトル", "名詞", "This game uses turn-based combat instead of real-time action.", DOMAIN, "650"),
    ("real-time combat", "リアルタイム戦闘", "名詞", "Real-time combat requires faster reflexes than turn-based systems.", DOMAIN, "650"),
    # --- 管理要素 ---
    ("inventory", "持ち物・インベントリ", "名詞", "My inventory is full, so I need to sell some items.", DOMAIN, "500"),
    ("equipment slot", "装備スロット", "名詞", "This character only has four equipment slots at the start.", DOMAIN, "650"),
    ("character class", "キャラクタークラス・職業", "名詞", "Each character class has its own strengths and weaknesses.", DOMAIN, "550"),
    ("world map", "ワールドマップ", "名詞", "Check the world map to see which areas you haven't visited yet.", DOMAIN, "500"),
    ("fast travel", "ファストトラベル(瞬間移動機能)", "名詞", "Fast travel saves a lot of time once you've explored an area.", DOMAIN, "600"),
    # --- セーブ・周回要素 ---
    ("save file", "セーブデータ", "名詞", "Don't overwrite your old save file until you're sure.", DOMAIN, "500"),
    ("save point", "セーブポイント", "名詞", "There's a save point just before the next dungeon.", DOMAIN, "500"),
    ("New Game Plus", "ニューゲームプラス(クリア後の周回モード)", "名詞", "New Game Plus lets you replay the story with your old gear.", DOMAIN, "850"),
    ("difficulty setting", "難易度設定", "名詞", "You can change the difficulty setting at any time from the menu.", DOMAIN, "550"),
    ("character creation", "キャラクタークリエイション・キャラメイク", "名詞", "Character creation took me almost an hour because of all the options.", DOMAIN, "600"),
    # --- ジャンル用語 ---
    ("action RPG", "アクションRPG", "名詞", "This action RPG blends fast combat with deep character customization.", DOMAIN, "600"),
    ("open-world game", "オープンワールドゲーム", "名詞", "In an open-world game, you can explore almost anywhere from the start.", DOMAIN, "600"),
    ("sandbox game", "サンドボックスゲーム", "名詞", "A sandbox game gives players freedom instead of a fixed path.", DOMAIN, "650"),
    ("JRPG", "JRPG(日本産ロールプレイングゲーム)", "名詞", "This JRPG has a long story with dozens of side quests.", DOMAIN, "700"),
    ("dungeon crawler", "ダンジョンクロウラー(探索特化型RPG)", "名詞", "This dungeon crawler has dozens of randomly generated floors.", DOMAIN, "750"),
    ("non-linear story", "非線形なストーリー", "名詞", "The game has a non-linear story that changes based on your choices.", DOMAIN, "800"),
    ("branching dialogue", "分岐する会話選択肢", "名詞", "Branching dialogue options can change how NPCs treat you later.", DOMAIN, "800"),
    ("permadeath", "パーマデス(死亡でデータが消える仕様)", "名詞", "Permadeath means your character is gone for good if they die.", DOMAIN, "850"),
    ("roguelike", "ローグライク", "名詞", "In a roguelike, every run generates a new dungeon layout.", DOMAIN, "850"),
    ("roguelite", "ローグライト", "名詞", "A roguelite usually lets you keep some progress between runs.", DOMAIN, "850"),
    # --- キャラクター・パーティー ---
    ("party member", "パーティーメンバー", "名詞", "Each party member has a different role in combat.", DOMAIN, "500"),
    ("playable character", "プレイアブルキャラクター(操作可能なキャラクター)", "名詞", "You can switch between playable characters at any save point.", DOMAIN, "650"),
    # --- プレイスタイル関連 ---
    ("cutscene", "カットシーン(ムービーシーン)", "名詞", "The cutscene before the final battle explains the whole story.", DOMAIN, "550"),
    ("achievement", "実績", "名詞", "I unlocked a new achievement for finishing the game without dying.", DOMAIN, "500"),
    ("trophy", "トロフィー(達成記録)", "名詞", "This trophy is for completing every side quest in the game.", DOMAIN, "550"),
    ("completionist", "コンプリート主義者・やり込み勢", "名詞", "As a completionist, I won't stop until I've found every item.", DOMAIN, "800"),
    ("walkthrough", "攻略情報・攻略ガイド", "名詞", "I looked up a walkthrough after getting stuck on this puzzle.", DOMAIN, "600"),
]

PHRASES: list[tuple[str, str]] = [
    ("I'm still grinding for XP.", "まだXP(経験値)稼ぎをしています。"),
    ("Let's take down this boss together.", "一緒にこのボスを倒しましょう。"),
    ("Have you unlocked the skill tree yet?", "もうスキルツリーは解放しましたか？"),
    ("I saved right before the boss fight.", "ボス戦の直前でセーブしておきました。"),
    ("This is a roguelike, so death is permanent.", "これはローグライクだから、死んだら終わりだよ。"),
    ("Which character class are you playing?", "どのキャラクタークラスでプレイしていますか？"),
    ("I need to check my inventory for potions.", "ポーションがあるかインベントリを確認しないと。"),
    ("Let's finish this side quest before the main story.", "本筋を進める前にこのサブクエストを終わらせましょう。"),
    ("I put all my stat points into strength.", "ステータスポイントは全部力に振りました。"),
    ("Is there a fast travel point near here?", "この近くにファストトラベルできる地点はありますか？"),
    ("I want to start a New Game Plus run.", "ニューゲームプラスを始めたいです。"),
    ("What difficulty setting are you playing on?", "どの難易度設定でプレイしていますか？"),
    ("Watch out, that's a mini-boss, not the final boss.", "気をつけて、それは中ボスであってラスボスじゃないよ。"),
    ("I got a rare item from that loot drop.", "そのドロップアイテムからレアアイテムが手に入りました。"),
    ("This open-world game has so much to explore.", "このオープンワールドゲームは探索できる場所がたくさんある。"),
    ("I skipped the cutscene by accident.", "うっかりカットシーンを飛ばしてしまいました。"),
    ("Let's check a walkthrough if we get stuck.", "行き詰まったら攻略情報を確認しよう。"),
    ("I'm trying to be a completionist on this one.", "今回はコンプリート狙いでやってみています。"),
    ("My build focuses on magic instead of strength.", "私のビルドは力じゃなくて魔法重視です。"),
    ("Random encounters keep interrupting my exploration.", "ランダムエンカウントのせいで探索が何度も中断される。"),
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

    with db() as conn:
        existing_p = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        added_p = skipped_p = 0
        for en, ja in PHRASES:
            if en.lower() in existing_p:
                skipped_p += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) VALUES (?, ?, ?)",
                (en, ja, SCENE),
            )
            existing_p.add(en.lower())
            added_p += 1
    print(f"phrases: +{added_p} (skipped {skipped_p})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
