# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Bulk-add curated words & phrases for CHESS / SHOGI / GO / OTHELLO /
RUBIK'S CUBE, authored by Claude.

ユーザー要望(2026-08-09): 「チェス、将棋、囲碁、オセロ、ルービックキューブ
の用語とフレーズ追加」。既存の`TRPG・ボードゲーム`domain(TRPG・洋風
ボードゲーム機構語)とは別に、各ゲーム固有のdomain/sceneを新設した
(既存のサッカー/野球/バスケットボール/モータースポーツのように1ゲーム
1domainとする既存方針に合わせた)。

既存語との衝突に注意し、以下は意図的に別語彙として複合語化・曖昧回避した:
- "stalemate"(サッカーの膠着状態)とは別に"chess stalemate"
- "skewer"(料理の串)とは別に"chess skewer"
- "edge"(一般語)とは別に"edge square"(オセロ)
- "algorithm"(IT用語)とは別に"cubing algorithm"
- "lubricant"(機械工学の潤滑剤)とは別に"cube lube"
- "go"はそのままだと動詞"行く"と衝突必至のため辞書的表記に倣い"Go (board game)"
- "check"も一般語との将来衝突を避け"check (chess)"とした

No app / OpenAI API calls — hand-written. Duplicates skipped by english
(lowercased).

Run:  python scripts/add_board_games.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- words: (english, japanese, part_of_speech, example, domain, level) ----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- チェス ---
    ("checkmate", "チェックメイト・詰み（王が逃げられない状態）", "名詞", "He delivered checkmate in just twelve moves.", "チェス", "600"),
    ("check (chess)", "王手", "名詞", "Your king is in check.", "チェス", "500"),
    ("chess stalemate", "ステイルメイト（動ける駒がなく引き分けになる状態）", "名詞", "The game ended in a stalemate because no legal move remained.", "チェス", "700"),
    ("castling", "キャスリング（王と塔を同時に動かす特殊手）", "名詞", "She used castling to protect her king early in the game.", "チェス", "700"),
    ("en passant", "アンパッサン（特殊なポーンの取り方）", "名詞", "He captured the pawn en passant.", "チェス", "800"),
    ("chess opening", "序盤の定跡・オープニング", "名詞", "The Sicilian Defense is a popular chess opening.", "チェス", "600"),
    ("endgame", "終盤（駒が少なくなった局面）", "名詞", "Pawn endgames require very precise calculation.", "チェス", "650"),
    ("chess gambit", "ギャンビット（序盤で駒を犠牲にする戦法）", "名詞", "The Queen's Gambit sacrifices a pawn for central control.", "チェス", "700"),
    ("chess fork", "フォーク（一手で複数の駒を同時に狙う戦術）", "名詞", "The knight created a fork, attacking both the king and the rook.", "チェス", "650"),
    ("pin", "ピン（動くと後ろの駒が危険にさらされる状態）", "名詞", "The bishop pinned the knight to the king.", "チェス", "650"),
    ("chess skewer", "スキュワー（串刺し戦術、価値の高い駒を動かすと後ろの駒を取られる）", "名詞", "The rook skewered the king and queen.", "チェス", "750"),
    ("chess promotion", "プロモーション（ポーンが最終列に達し別の駒に昇格すること）", "名詞", "Her pawn reached the eighth rank and promoted to a queen.", "チェス", "650"),
    ("grandmaster", "グランドマスター（チェスの最高位の称号）", "名詞", "He became a grandmaster at the age of sixteen.", "チェス", "700"),
    ("algebraic notation", "代数記法（チェスの棋譜記録法）", "名詞", "Chess moves are recorded using algebraic notation.", "チェス", "750"),
    ("Elo rating", "イロレーティング（プレイヤーの実力を数値化する評価システム）", "名詞", "His Elo rating rose sharply after the tournament.", "チェス", "750"),
    # --- 将棋 ---
    ("shogi", "将棋（日本の伝統的な将棋、取った駒を自分の持ち駒として使える）", "名詞", "Shogi is often called 'Japanese chess.'", "将棋", "500"),
    ("piece drop", "打つ（持ち駒を盤上に置く、将棋独自のルール）", "名詞", "A piece drop is one of the most unique rules in shogi.", "将棋", "700"),
    ("pieces in hand", "持ち駒（取った相手の駒で、自分の駒として使えるもの）", "名詞", "He had three pieces in hand, ready to drop at any moment.", "将棋", "700"),
    ("gold general", "金将（将棋の駒の一つ）", "名詞", "The gold general moves one square in six directions.", "将棋", "650"),
    ("silver general", "銀将（将棋の駒の一つ）", "名詞", "The silver general can move diagonally forward and backward.", "将棋", "650"),
    ("lance", "香車（将棋の駒の一つ、前方に何マスでも進める）", "名詞", "The lance can move any number of squares straight forward.", "将棋", "650"),
    ("promotion zone", "敵陣（将棋で駒が成れる範囲）", "名詞", "Once a pawn enters the promotion zone, it can become a tokin.", "将棋", "700"),
    ("tokin", "と金（成った歩、金将と同じ動きになる）", "名詞", "A tokin moves just like a gold general.", "将棋", "750"),
    ("dragon king", "竜王（成った飛車）", "名詞", "The rook promoted into a dragon king.", "将棋", "750"),
    ("dragon horse", "竜馬（成った角行）", "名詞", "The bishop became a dragon horse after promoting.", "将棋", "750"),
    ("sente", "先手（先に指す側、または形勢が有利な側）", "名詞", "Keeping sente throughout the middlegame gave her an advantage.", "将棋", "750"),
    ("gote", "後手（後に指す側、または形勢が不利な側）", "名詞", "He was forced into gote after the exchange.", "将棋", "750"),
    ("tsumeshogi", "詰将棋（王を詰ますことだけを目的としたパズル）", "名詞", "She practices tsumeshogi every morning to sharpen her endgame skills.", "将棋", "800"),
    ("kifu", "棋譜（対局の指し手を記録したもの）", "名詞", "Professional games are always recorded as kifu.", "将棋", "750"),
    ("shogi board", "将棋盤", "名詞", "The shogi board has eighty-one squares.", "将棋", "550"),
    # --- 囲碁 ---
    ("Go (board game)", "囲碁（碁石を使って陣地を囲い合う対局ゲーム）", "名詞", "Go is one of the oldest board games still played today.", "囲碁", "500"),
    ("goban", "碁盤（囲碁を打つための盤）", "名詞", "The goban has nineteen lines in each direction.", "囲碁", "600"),
    ("go stone", "碁石", "名詞", "Black stones and white stones are placed one at a time.", "囲碁", "550"),
    ("territory", "地（碁盤上で自分の陣地として数えられる部分）", "名詞", "Whoever controls more territory at the end wins the game.", "囲碁", "650"),
    ("atari", "アタリ（次の一手で取られてしまう状態）", "名詞", "Your group is in atari, so you should respond immediately.", "囲碁", "700"),
    ("liberty", "呼吸点（石に隣接する空いた交点）", "名詞", "A stone with no liberties left is captured.", "囲碁", "700"),
    ("ko", "コウ（同一局面の反復を禁止するルール）", "名詞", "The ko rule prevents players from repeating the same capture forever.", "囲碁", "800"),
    ("seki", "セキ（互いに手を出せず共存する状態）", "名詞", "Neither player could capture the other's group, so it became seki.", "囲碁", "800"),
    ("eye", "眼（囲まれた一つの空点で、石を生かすために必要）", "名詞", "A group needs two eyes to live permanently.", "囲碁", "700"),
    ("dead stone", "死に石（最終的に取られると見なされる石）", "名詞", "The dead stones are removed from the board when counting territory.", "囲碁", "750"),
    ("komi", "コミ（後手の不利を補うために設定されるハンデ点）", "名詞", "In most rulesets, White receives 6.5 points of komi.", "囲碁", "800"),
    ("handicap stone", "置き石（実力差を埋めるために先に置く石）", "名詞", "Weaker players can start with a few handicap stones.", "囲碁", "700"),
    ("joseki", "定石（隅などでの最善とされる決まった手順）", "名詞", "This joseki is common in the corner during the opening.", "囲碁", "800"),
    ("fuseki", "布石（序盤全体の構想・配石）", "名詞", "Her fuseki focused on building influence toward the center.", "囲碁", "800"),
    ("dan rank", "段位（囲碁・将棋などの実力段位）", "名詞", "He recently reached five-dan rank.", "囲碁", "650"),
    # --- オセロ ---
    ("Othello", "オセロ（黒白の石を挟んでひっくり返す対局ゲーム）", "名詞", "Othello is easy to learn but hard to master.", "オセロ", "500"),
    ("reversi", "リバーシ（オセロの原型となったゲームの呼び名）", "名詞", "Othello is a commercial version of the older game reversi.", "オセロ", "700"),
    ("flip a disc", "挟んでひっくり返す（オセロの基本アクション）", "動詞句", "Placing your disc there will flip three of your opponent's discs.", "オセロ", "550"),
    ("disc", "ディスク・石（オセロで使う両面が黒白の駒）", "名詞", "Each disc is black on one side and white on the other.", "オセロ", "500"),
    ("corner (Othello)", "角（オセロで一度取ると絶対にひっくり返されない重要なマス）", "名詞", "Controlling the corners is a key strategy in Othello.", "オセロ", "600"),
    ("valid move", "有効な手（相手の石を1つ以上挟める手）", "名詞", "If you have no valid move, your turn is skipped.", "オセロ", "600"),
    ("mobility (Othello)", "着手可能数（自分が打てる手の多さ）", "名詞", "Keeping high mobility while limiting your opponent's is a core strategy.", "オセロ", "750"),
    ("edge square", "辺のマス（オセロで角の次に重要とされる盤の外周部分）", "名詞", "Taking an edge square safely can set up a corner later.", "オセロ", "700"),
    ("parity (Othello)", "パリティ（終盤の手数の偶奇による有利不利）", "名詞", "Advanced players think carefully about parity in the endgame.", "オセロ", "800"),
    ("stable disc", "安定石（もう二度とひっくり返されない石）", "名詞", "Corner discs are always stable discs.", "オセロ", "750"),
    # --- ルービックキューブ ---
    ("Rubik's Cube", "ルービックキューブ", "名詞", "The Rubik's Cube has six faces, each with nine stickers.", "パズル", "500"),
    ("speedcubing", "スピードキューブ（できるだけ速く揃える競技）", "名詞", "Speedcubing competitions are held all over the world.", "パズル", "650"),
    ("cube scramble", "スクランブル（競技前にランダムに崩す操作・手順）", "名詞", "The judge read out the cube scramble before the timer started.", "パズル", "650"),
    ("cubing algorithm", "アルゴリズム（決まった揃え方の手順）", "名詞", "She memorized dozens of algorithms to solve the cube faster.", "パズル", "650"),
    ("cross (cube)", "クロス（キューブ攻略の最初のステップ、十字を揃えること）", "名詞", "A good cross sets up the rest of the solve.", "パズル", "600"),
    ("F2L", "F2L（ファースト・ツー・レイヤーズ、最初の2段を揃える工程）", "名詞", "F2L stands for 'first two layers.'", "パズル", "750"),
    ("OLL", "OLL（最終段の面を揃える工程）", "名詞", "OLL means orienting the last layer.", "パズル", "750"),
    ("PLL", "PLL（最終段の位置を揃える工程）", "名詞", "PLL is the final step: permuting the last layer.", "パズル", "750"),
    ("personal best", "自己ベストタイム", "名詞", "He set a new personal best of eight seconds.", "パズル", "550"),
    ("cube lube", "キューブ用の潤滑剤（回転を滑らかにするために使う、通称「ルブ」）", "名詞", "Cubers often apply cube lube to make turns smoother.", "パズル", "700"),
    ("finger trick", "フィンガートリック（指先だけで素早く回す技術）", "名詞", "Finger tricks let you turn the cube without repositioning your hands.", "パズル", "700"),
    ("cubing notation", "キューブ記法（面の回転を表す記号、例:R,U,F等）", "名詞", "Cubing notation uses letters like R, U, and F for each face.", "パズル", "700"),
]

# --- phrases: scene -> [(english, japanese)] --------------------------------

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "チェスの英語": [
        ("Checkmate!", "チェックメイト！"),
        ("It's your move.", "あなたの番です。"),
        ("I'll castle kingside.", "キングサイドにキャスリングします。"),
        ("That's a stalemate, so it's a draw.", "それはステイルメイトなので引き分けです。"),
        ("Would you like to play a game of chess?", "チェスを一局しませんか？"),
        ("I resign.", "投了します。"),
        ("Can we set up the board again?", "もう一度盤面をセットし直しましょうか。"),
        ("She's a chess grandmaster.", "彼女はチェスのグランドマスターです。"),
    ],
    "将棋の英語": [
        ("Let's play a game of shogi.", "将棋を一局しませんか。"),
        ("I'll drop my gold general here.", "ここに金を打ちます。"),
        ("Your king is in checkmate.", "あなたの玉は詰みです。"),
        ("I have to resign.", "投了しなければなりません。"),
        ("That piece can promote here.", "この駒はここで成れます。"),
        ("Do you want to play with a handicap?", "駒落ちで対局しませんか。"),
        ("Whose turn is it, sente or gote?", "先手と後手、どちらの番ですか。"),
        ("Can you explain how the knight moves in shogi?", "将棋の桂馬の動き方を説明してもらえますか。"),
    ],
    "囲碁の英語": [
        ("Would you like to play a game of Go?", "囲碁を一局打ちませんか。"),
        ("I'll pass this turn.", "この手番はパスします。"),
        ("That group looks like it's in atari.", "あの石はアタリになっているようです。"),
        ("Let's count the territory.", "地を数えましょう。"),
        ("I think this group is already dead.", "この石はもう死んでいると思います。"),
        ("What's your rank in Go?", "囲碁の段位はどのくらいですか。"),
        ("This is a classic joseki in the corner.", "これは隅の定石です。"),
        ("Shall we play with a handicap?", "置き石で打ちましょうか。"),
    ],
    "オセロの英語": [
        ("Let's play a game of Othello.", "オセロを一局しませんか。"),
        ("That move flips four discs.", "その手で4つの石がひっくり返ります。"),
        ("Never give up a corner for free.", "角はただでは絶対に渡さないで。"),
        ("I don't have a valid move, so I'll pass.", "有効な手がないのでパスします。"),
        ("Let's count the discs at the end.", "最後に石の数を数えましょう。"),
        ("Black moves first in Othello.", "オセロでは黒が先手です。"),
    ],
    "パズル・キューブの英語": [
        ("How fast can you solve a Rubik's Cube?", "ルービックキューブはどのくらい速く揃えられますか。"),
        ("I finally solved it in under a minute.", "ついに1分以内で揃えられました。"),
        ("Can you teach me an algorithm for this step?", "このステップのアルゴリズムを教えてもらえますか。"),
        ("My cube feels a bit stiff, I should lubricate it.", "キューブが少し硬いので潤滑剤を差した方がよさそうです。"),
        ("Let's time your solve with a scramble.", "スクランブルしてタイムを計りましょう。"),
        ("This is my personal best so far.", "これが今のところの自己ベストです。"),
    ],
}


def main() -> int:
    with db() as conn:
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }

        ph_added = ph_skipped = 0
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in ph_existing:
                    ph_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                ph_existing.add(en.lower())
                ph_added += 1

        w_added = w_skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in w_existing:
                w_skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            w_existing.add(en.lower())
            w_added += 1

    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    print(f"words:   +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print("totals -> phrases:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0],
              "words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
