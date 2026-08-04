# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a new "TRPG・ボードゲーム" domain/scene: vocabulary and phrases for
tabletop role-playing games (D&D-style TRPGs, generically) and modern board
games / online tabletop play, authored by Claude (2026-08-04・ユーザー要望).

対象語彙: TRPGの基本用語(GM/ダンジョンマスター、キャンペーン、セッション、
キャラクターシート、ダイスロール、d20、セービングスロー、ヒットポイント、
イニシアチブ、パーティー、NPC、ホームブルー、ワンショット、ロールプレイ対
ロールプレイ、ハウスルール、ミンマックス、メタゲーミング、レールローディン
グ、サンドボックスキャンペーン)、ボードゲームの基本用語(ワーカープレイスメ
ント、デッキ構築、タイル配置、エンジンビルディング、勝利点、手番順、手札管
理、拡張セット、ミープル、ルールブック、セットアップ/片付けフェイズ、リプ
レイ性、協力型ゲーム、正体隠匿ギミック)。特定の商品・作品の固有名詞(クラス
名・呪文名など)は一切使用せず、すべて一般的な用語のみ。

フレーズはテーブルやオンラインセッションで実際に使う自然な口語表現("Whose
turn is it?" "I roll for perception." "Can we take a short rest?" など)。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_tabletop_trpg.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 基本語 ---
    ("turn", "順番・ターン", "名詞", "It's your turn to roll the dice.", "TRPG・ボードゲーム", "300"),
    ("dice", "サイコロ(複数形)", "名詞", "Shake the dice before you roll.", "TRPG・ボードゲーム", "300"),
    ("player", "プレイヤー", "名詞", "Each player chooses a character at the start.", "TRPG・ボードゲーム", "300"),
    ("rule", "ルール", "名詞", "Every game needs at least one rule everyone agrees on.", "TRPG・ボードゲーム", "300"),
    ("token", "トークン・コマ", "名詞", "Move your token three spaces forward.", "TRPG・ボードゲーム", "400"),
    ("quest", "クエスト・依頼", "名詞", "The party accepted a quest to find the missing merchant.", "TRPG・ボードゲーム", "450"),
    ("dungeon", "ダンジョン・地下迷宮", "名詞", "The party explored a dark dungeon in search of treasure.", "TRPG・ボードゲーム", "450"),
    # --- TRPG用語 ---
    ("game master", "ゲームマスター(GM)", "名詞", "The game master describes the scene at the start of every session.", "TRPG・ボードゲーム", "500"),
    ("dungeon master", "ダンジョンマスター(GMの呼称の一つ)", "名詞", "In some games, the game master is called the dungeon master.", "TRPG・ボードゲーム", "550"),
    ("campaign", "キャンペーン(長期シナリオ)", "名詞", "Our campaign has lasted for over a year now.", "TRPG・ボードゲーム", "550"),
    ("session", "セッション(プレイ回)", "名詞", "We meet every Friday for a three-hour session.", "TRPG・ボードゲーム", "400"),
    ("character sheet", "キャラクターシート", "名詞", "Fill out your character sheet before the first session.", "TRPG・ボードゲーム", "500"),
    ("dice roll", "ダイスロール・サイコロを振ること", "名詞", "The outcome depends on a single dice roll.", "TRPG・ボードゲーム", "400"),
    ("d20", "20面ダイス", "名詞", "Roll a d20 to determine whether your attack succeeds.", "TRPG・ボードゲーム", "600"),
    ("saving throw", "抵抗判定・セービングスロー", "名詞", "Make a saving throw to resist the trap's effect.", "TRPG・ボードゲーム", "700"),
    ("hit points", "ヒットポイント・体力値", "名詞", "Your character loses hit points when you take damage.", "TRPG・ボードゲーム", "500"),
    ("initiative", "行動順・イニシアチブ", "名詞", "Roll for initiative to see who acts first in combat.", "TRPG・ボードゲーム", "650"),
    ("party", "パーティー(仲間の一団)", "名詞", "The party decided to rest before entering the cave.", "TRPG・ボードゲーム", "400"),
    ("NPC", "ノンプレイヤーキャラクター", "名詞", "The NPC offered the party a quest.", "TRPG・ボードゲーム", "500"),
    ("homebrew", "自作ルール・オリジナル設定", "名詞", "This class is homebrew content the GM created herself.", "TRPG・ボードゲーム", "750"),
    ("one-shot", "単発セッション", "名詞", "We tried a one-shot before committing to a full campaign.", "TRPG・ボードゲーム", "700"),
    ("role-play", "ロールプレイをする", "動詞", "Try to role-play your character's personality, not just fight.", "TRPG・ボードゲーム", "500"),
    ("house rule", "ハウスルール(独自ルール)", "名詞", "Our group uses a house rule for critical hits.", "TRPG・ボードゲーム", "600"),
    ("min-maxing", "ミンマックス(数値最適化偏重のキャラ作成)", "名詞", "He spent an hour min-maxing his character's stats.", "TRPG・ボードゲーム", "850"),
    ("meta-gaming", "メタゲーミング(プレイヤー知識の悪用)", "名詞", "Using information your character doesn't know is called meta-gaming.", "TRPG・ボードゲーム", "850"),
    ("railroading", "レールローディング(強制的な筋書き誘導)", "名詞", "Players complained that the story felt like railroading.", "TRPG・ボードゲーム", "850"),
    ("sandbox campaign", "サンドボックス型キャンペーン", "名詞", "In a sandbox campaign, players choose their own goals.", "TRPG・ボードゲーム", "800"),
    # --- ボードゲーム用語 ---
    ("worker placement", "ワーカープレイスメント", "名詞", "Worker placement games ask you to assign limited workers each round.", "TRPG・ボードゲーム", "750"),
    ("deck-building", "デッキ構築", "名詞", "Deck-building games let you improve your deck as you play.", "TRPG・ボードゲーム", "700"),
    ("tile-laying", "タイル配置", "名詞", "Tile-laying games reward careful planning of the board's layout.", "TRPG・ボードゲーム", "750"),
    ("engine building", "エンジンビルディング", "名詞", "Engine building games get more powerful as your combo grows.", "TRPG・ボードゲーム", "800"),
    ("victory points", "勝利点", "名詞", "Count your victory points at the end of the game.", "TRPG・ボードゲーム", "600"),
    ("turn order", "手番の順番", "名詞", "Turn order goes clockwise around the table.", "TRPG・ボードゲーム", "450"),
    ("hand management", "手札管理", "名詞", "Hand management is key to winning this card game.", "TRPG・ボードゲーム", "700"),
    ("expansion", "拡張セット", "名詞", "The new expansion adds two more character options.", "TRPG・ボードゲーム", "500"),
    ("meeple", "ミープル(木製の人型コマ)", "名詞", "Place your meeple on any open space.", "TRPG・ボードゲーム", "700"),
    ("rulebook", "ルールブック", "名詞", "Let's check the rulebook before we argue about this.", "TRPG・ボードゲーム", "400"),
    ("setup phase", "セットアップ(準備)フェイズ", "名詞", "The setup phase alone can take fifteen minutes.", "TRPG・ボードゲーム", "500"),
    ("teardown", "後片付け", "名詞", "Teardown is quick once everyone helps.", "TRPG・ボードゲーム", "550"),
    ("replayability", "リプレイ性(何度も遊べる度合い)", "名詞", "This game has great replayability thanks to random setups.", "TRPG・ボードゲーム", "800"),
    ("co-op game", "協力型ゲーム", "名詞", "In a co-op game, all players win or lose together.", "TRPG・ボードゲーム", "600"),
    ("hidden traitor mechanic", "正体隠匿(裏切り者)ギミック", "名詞", "The hidden traitor mechanic keeps everyone suspicious of each other.", "TRPG・ボードゲーム", "850"),
]

PHRASES: list[tuple[str, str]] = [
    ("Whose turn is it?", "誰の番ですか？"),
    ("I roll for perception.", "〈知覚〉判定でダイスを振ります。"),
    ("Can we take a short rest?", "少し休憩を取ってもいいですか？"),
    ("Let's read the rulebook again.", "もう一度ルールブックを読みましょう。"),
    ("I'd like to trade this resource.", "この資源を交換したいのですが。"),
    ("Are we playing with the expansion?", "拡張セットも使ってプレイしますか？"),
    ("Can someone explain the house rules?", "誰かハウスルールを説明してくれますか？"),
    ("What's your character's backstory?", "あなたのキャラクターの背景設定は？"),
    ("I'll attack the nearest enemy.", "一番近い敵を攻撃します。"),
    ("Roll a d20 and add your modifier.", "d20を振って修正値を足してください。"),
    ("You need a saving throw here.", "ここでセービングスローが必要です。"),
    ("Let's set up the board.", "ボードをセットアップしましょう。"),
    ("It's time to tear down the game.", "そろそろ片付けの時間です。"),
    ("I'm out of hit points.", "ヒットポイントが尽きました。"),
    ("Can we go over the setup phase together?", "セットアップフェイズを一緒に確認しませんか？"),
    ("Let's roll for initiative.", "イニシアチブを振りましょう。"),
    ("I'll place my meeple here.", "ここにミープルを置きます。"),
    ("How many victory points do you have?", "勝利点は何点持っていますか？"),
    ("Can we do a one-shot this weekend?", "今週末、単発セッションをやりませんか？"),
    ("I'm new, can someone explain the basic rules?", "初心者なので、基本ルールを説明してもらえますか？"),
    ("Let's not railroad the story too much.", "あまりストーリーを一本道にしすぎないようにしましょう。"),
    ("Please mute yourself when it's not your turn.", "自分の番でないときはミュートにしてください。"),
    ("Can you share your screen for the map?", "マップを見せるために画面共有してもらえますか？"),
    ("I'll join the session online this time.", "今回はオンラインでセッションに参加します。"),
    ("Let's take a five-minute break before combat.", "戦闘の前に5分休憩を取りましょう。"),
    ("Who wants to be the game master next time?", "次回はだれがゲームマスターをやりたいですか？"),
    ("I think we're min-maxing too much.", "ちょっとミンマックスしすぎだと思います。"),
    ("Let's keep meta-gaming to a minimum.", "メタゲーミングはできるだけ控えましょう。"),
    ("Can we save our progress and continue next week?", "進行状況を保存して来週続きをやりませんか？"),
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
                "VALUES (?, ?, 'TRPG・ボードゲーム英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
