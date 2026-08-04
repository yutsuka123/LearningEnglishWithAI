# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add online-gaming & Discord/voice-chat vocabulary and phrases, authored by
Claude (2026-08-04・ユーザー要望).

対象はesports実況や特定タイトルの著作物ではなく、オンラインゲームで日常的に
使われる一般語彙(patch/nerf/buff/meta/matchmaking等)、Discord固有の用語
(server/channel/role/push to talk等)、そしてプレイ中に実際に交わされる自然な
会話フレーズ("Can you carry me this game?"等)。例文はすべてオリジナルで、
特定ゲームのテキストやパッチノートの引用・言い換えは含まない。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_gaming_discord.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "ゲーム・Discordの英語"
SCENE = "ゲーム・Discord英語"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 一般的なオンラインゲーム用語 ---
    ("patch", "パッチ(修正・更新プログラム)", "名詞", "The new patch fixes several bugs from last week.", DOMAIN, "500"),
    ("patch notes", "パッチノート(更新内容の説明文)", "名詞", "Always read the patch notes before you start playing.", DOMAIN, "550"),
    ("nerf", "弱体化する", "動詞", "They nerfed that weapon because it was too strong.", DOMAIN, "600"),
    ("buff", "強化する", "動詞", "The healer class got buffed in the latest update.", DOMAIN, "600"),
    ("meta", "メタ(その時点で最も強い戦術・構成)", "名詞", "This character isn't in the current meta.", DOMAIN, "650"),
    ("grind", "地道な作業を繰り返す・周回する", "動詞", "I had to grind for hours to get enough gold.", DOMAIN, "550"),
    ("respawn", "リスポーンする(復活する)", "動詞", "You'll respawn near the checkpoint after you die.", DOMAIN, "500"),
    ("spawn camp", "スポーンキャンプする(復活地点で待ち伏せする)", "動詞", "It's considered unfair to spawn camp new players.", DOMAIN, "800"),
    ("lag", "ラグ(通信の遅延)", "名詞", "The game keeps freezing because of lag.", DOMAIN, "450"),
    ("ping", "ピン(通信の応答速度)", "名詞", "My ping is over 200, so the game feels sluggish.", DOMAIN, "500"),
    ("matchmaking", "マッチメイキング(対戦相手の自動組み合わせ)", "名詞", "Matchmaking is taking a long time tonight.", DOMAIN, "600"),
    ("ranked", "ランク戦の", "形容詞", "I only play ranked matches on the weekend.", DOMAIN, "550"),
    ("smurf account", "スマーフアカウント(実力を隠すためのサブ垢)", "名詞", "That player is way too good; it's probably a smurf account.", DOMAIN, "850"),
    ("tilt", "冷静さを失う・自暴自棄になる", "動詞", "Don't tilt after one bad round; just refocus.", DOMAIN, "700"),
    ("clutch", "土壇場で決める・逆転勝利する", "動詞", "She clutched the round with the last player standing.", DOMAIN, "700"),
    ("GG", "ジージー(Good Gameの略。お疲れ様でした)", "間投詞", "GG everyone, that was a close match.", DOMAIN, "500"),
    ("AFK", "エーエフケー(離席中・操作していない状態)", "形容詞", "Sorry, I was AFK for a minute.", DOMAIN, "500"),
    ("DPS", "ディーピーエス(与ダメージ量、またはその役割)", "名詞", "We need more DPS to beat this boss in time.", DOMAIN, "700"),
    ("tank", "タンク(前線で敵の攻撃を受け止める役割)", "名詞", "Can someone play tank this round?", DOMAIN, "600"),
    ("healer", "ヒーラー(仲間を回復する役割)", "名詞", "We lost because we didn't have a healer.", DOMAIN, "500"),
    ("cooldown", "クールダウン(スキルの再使用までの待ち時間)", "名詞", "That ability has a long cooldown, so use it wisely.", DOMAIN, "600"),
    ("griefing", "グリーフィング(嫌がらせ目的の妨害行為)", "名詞", "Reported him for griefing our own team.", DOMAIN, "800"),
    ("toxic", "有害な・攻撃的な(言動が悪質な)", "形容詞", "Please don't be toxic in the chat.", DOMAIN, "600"),
    ("carry", "実力で試合を勝たせる・引っ張る", "動詞", "You basically carried the whole team that game.", DOMAIN, "600"),
    ("throw", "せっかくの優勢を自ら台無しにする", "動詞", "We were winning easily until he threw the game.", DOMAIN, "750"),
    ("queue", "待機列に並ぶ・キューに入る", "動詞", "Let's queue for the next match.", DOMAIN, "500"),
    ("party", "パーティー(一緒に遊ぶ仲間のグループ)", "名詞", "I'll invite you to my party once I log in.", DOMAIN, "450"),
    ("guild", "ギルド(協力して遊ぶプレイヤーの組織)", "名詞", "Our guild is recruiting new members this week.", DOMAIN, "550"),
    ("loot", "戦利品・ドロップアイテム", "名詞", "The final boss dropped some really good loot.", DOMAIN, "550"),
    ("exploit", "バグを悪用する・悪用行為", "名詞", "Using that exploit can get your account banned.", DOMAIN, "750"),
    ("speedrun", "スピードラン(最短クリアを目指すプレイ)", "名詞", "He's trying to speedrun the entire game in under an hour.", DOMAIN, "700"),
    ("mod", "MOD(有志が作る改造データ)", "名詞", "This mod adds a bunch of new maps to the game.", DOMAIN, "600"),
    ("DLC", "ディーエルシー(追加配信コンテンツ)", "名詞", "The new DLC adds a whole new storyline.", DOMAIN, "550"),
    ("early access", "早期アクセス(正式版前の先行公開)", "名詞", "The game is still in early access, so expect some bugs.", DOMAIN, "600"),
    ("beta", "ベータ版(試験公開版)", "名詞", "I signed up to test the closed beta.", DOMAIN, "450"),
    ("level up", "レベルアップする", "動詞", "You'll level up faster if you finish the daily quests.", DOMAIN, "400"),
    # --- Discord・ボイスチャット関連 ---
    ("server", "サーバー(Discordのコミュニティ単位)", "名詞", "Can you invite me to your Discord server?", DOMAIN, "450"),
    ("channel", "チャンネル(サーバー内の話題別スペース)", "名詞", "Let's move this conversation to the general channel.", DOMAIN, "450"),
    ("role", "ロール(サーバー内で付与される権限・肩書き)", "名詞", "You need the moderator role to pin messages here.", DOMAIN, "550"),
    ("mute", "ミュートにする(マイクの音を消す)", "動詞", "Could you mute yourself when you're not talking?", DOMAIN, "450"),
    ("deafen", "スピーカー音を遮断する(自分の耳を塞ぐ)", "動詞", "I deafened myself so I wouldn't hear the background noise.", DOMAIN, "700"),
    ("push to talk", "プッシュ・トゥ・トーク(押している間だけ発話する設定)", "名詞", "I switched to push to talk so my mic doesn't pick up noise.", DOMAIN, "700"),
    ("screen share", "画面共有", "名詞", "Can you turn on screen share so I can see the problem?", DOMAIN, "500"),
    ("voice chat", "ボイスチャット", "名詞", "Join the voice chat once you're ready to play.", DOMAIN, "450"),
    ("bot command", "ボットコマンド(Bot操作用の命令文)", "名詞", "Type the bot command to check everyone's rank.", DOMAIN, "600"),
]

PHRASES: list[tuple[str, str]] = [
    ("Can you carry me this game?", "この試合、僕を引っ張ってもらえる？"),
    ("Let's queue up.", "キューに入ろう(マッチングを始めよう)。"),
    ("I'll invite you to the party.", "パーティーに招待するね。"),
    ("My ping is terrible tonight.", "今夜はピンが本当にひどい。"),
    ("Report that guy for griefing.", "あいつをグリーフィングで通報して。"),
    ("Can you share your screen?", "画面を共有してもらえる？"),
    ("Push to talk isn't working for me.", "プッシュ・トゥ・トークがうまく動かないんだ。"),
    ("Let's switch to a different channel.", "別のチャンネルに移ろう。"),
    ("Sorry, I was AFK for a second.", "ごめん、少しの間離席してた。"),
    ("Can you mute your mic? There's an echo.", "マイクをミュートしてもらえる？ハウってるから。"),
    ("Who's tanking this round?", "今回誰がタンクをやる？"),
    ("I need a healer in my party.", "パーティーにヒーラーが欲しい。"),
    ("Watch out, that spot is a spawn camp.", "気をつけて、そこはスポーンキャンプされやすい場所だよ。"),
    ("Don't tilt, we can still win this.", "冷静さを失わないで、まだ勝てるよ。"),
    ("That was such a clutch play!", "あれは本当にクラッチプレイだったね！"),
    ("GG, that was a fun match.", "お疲れ様、楽しい試合だった。"),
    ("What's the current meta for this class?", "このクラスの今のメタは何？"),
    ("They nerfed my favorite character again.", "また私のお気に入りキャラが弱体化された。"),
    ("Did you read the patch notes yet?", "もうパッチノートは読んだ？"),
    ("This ability is still on cooldown.", "このスキルはまだクールダウン中だよ。"),
    ("Can someone invite me to the guild?", "誰かギルドに招待してくれる？"),
    ("I grinded all weekend for this gear.", "この装備のために週末ずっと周回した。"),
    ("Let's not queue into ranked tonight.", "今夜はランク戦に入るのはやめよう。"),
    ("He got banned for using an exploit.", "彼はバグ技を使って垢バンされた。"),
    ("Ping me when you're back online.", "オンラインに戻ったらメンションして。"),
    ("Could you pin that message for later?", "そのメッセージ、後で見返せるようにピン留めしてくれる？"),
    ("React with a thumbs-up if you're ready.", "準備ができたら親指アップのリアクションをつけて。"),
    ("Let's not be toxic even if we lose.", "負けても攻撃的な態度は取らないようにしよう。"),
    ("Sorry, I think I just threw that round.", "ごめん、今のラウンド台無しにしちゃったかも。"),
    ("This game is still in early access, so bugs happen.", "このゲームはまだ早期アクセスだから、バグが出るのも仕方ないね。"),
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
