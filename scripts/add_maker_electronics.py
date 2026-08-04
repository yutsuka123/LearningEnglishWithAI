# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for MAKER / HOBBYIST ELECTRONICS English,
authored by Claude.

Focus (フレーズ集の手薄な領域を補強): 電子工作・Arduino/Raspberry Pi・3Dプリンター・
CNC・RC/ドローン・自作ロボット・自作キーボードなどを趣味とするメイカー
(hobbyist maker)向けの英語。GitHubのプロジェクトリポジトリ、r/arduino や
r/3Dprinting、r/MechanicalKeyboards のようなホビイストフォーラム、YouTube の
メイカー系チャンネルを読み・理解し、英語圏のフォーラムスレッドでトラブル
シューティングし、ビルドログ(製作記)を追えるようになることを目標とする。

既存の「電気・電子」「DIY・工具」フレーズシーンや「電気電子」「IT」「機械工学」
「半導体」ワードドメインには、抵抗器・コンデンサ・PCB・半導体・はんだ・
CNC・ブラケットなど汎用的な電気電子/機械工学語彙が既にかなり網羅されている
ため、本スクリプトはそれらと重複しない、メイカー特有のプロジェクト語彙
(breadboard, prototype, iteration, revision, BOM, open-source, fork a repo,
flash the firmware)、電子工作特有のトラブルシューティング表現(不足電流、
導通確認、冷はんだ接合、プルアップ抵抗の欠落、ショート)、3Dプリンター特有の
語彙(層の定着不良、糸引き、反り、ベッドレベリング、インフィル、サポート材、
スライサー設定)、そしてコミュニティ・フォーラム特有の言い回し(オープン
ソース化した、ビルドログ、YMMV、fork自由)に絞って補強する。

想定読者はハードウェア/組み込みエンジニアとしての実務知識を日本語では既に
持っている前提で、対応する「英語の言い回し」を身につけることに主眼を置く。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_maker_electronics.py
      python scripts/add_maker_electronics.py --missing-words   # report only

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- phrases: scene -> [(english, japanese)] --------------------------------

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "電子工作・Makerムーブメント": [
        # --- プロジェクト/ビルド全般の語彙 ---
        ("I threw together a quick prototype on a breadboard.", "ブレッドボードでとりあえずのプロトタイプを組んでみた。"),
        ("This is just a rough prototype — the real PCB comes later.", "これはただの試作段階で、本番のPCBは後で作ります。"),
        ("I'm already on revision three of the board.", "基板はもうリビジョン3です。"),
        ("Let's do another iteration on the design before we order boards.", "基板を発注する前に、もう一度設計を改良しましょう。"),
        ("Here's the BOM for this build.", "これがこのビルドの部品表(BOM)です。"),
        ("I sourced most of the parts on the BOM from AliExpress.", "部品表の部品はほとんどAliExpressで調達しました。"),
        ("It's fully open-source — schematics, firmware, all of it.", "完全にオープンソースです。回路図もファームウェアも全部公開しています。"),
        ("Feel free to fork the repo if you want to tweak it.", "カスタマイズしたければ、リポジトリを自由にフォークしてください。"),
        ("I forked the project and added a small display.", "そのプロジェクトをフォークして、小さいディスプレイを追加しました。"),
        ("Don't forget to flash the firmware once it's wired up.", "配線が終わったら、ファームウェアの書き込みを忘れずに。"),
        ("I bricked the board by flashing the wrong firmware.", "違うファームウェアを書き込んで、基板を文鎮化させてしまいました。"),
        ("Wire it up on a breadboard first before you commit to soldering.", "はんだ付けする前に、まずブレッドボードで配線を試して。"),
        ("Once it worked on the breadboard, I moved it to a perfboard.", "ブレッドボードで動作確認できたら、ユニバーサル基板に移しました。"),
        ("The enclosure is 3D printed; everything else is off-the-shelf.", "筐体は3Dプリント品で、それ以外は既製品です。"),
        # --- 電子工作特有のトラブルシューティング ---
        ("It's not getting enough current to drive the motor.", "モーターを駆動するのに十分な電流が来ていません。"),
        ("Check the continuity between these two points with a meter.", "テスターでこの2点間の導通を確認して。"),
        ("I traced it to a cold solder joint on the header pin.", "ヘッダーピンの冷はんだ接合が原因だと突き止めました。"),
        ("Looks like you're missing a pull-up resistor on that line.", "その配線にはプルアップ抵抗が足りていないようです。"),
        ("It's shorting out whenever the case closes.", "ケースを閉じるたびにショートしています。"),
        ("Double-check you didn't reverse the polarity on the connector.", "コネクタの極性を逆にしていないか、もう一度確認して。"),
        ("The board keeps browning out under load.", "負荷がかかると基板がブラウンアウト(電圧低下でリセット)を繰り返します。"),
        ("That trace is way too thin to carry that much current.", "そのパターン(配線)は、その電流を流すには細すぎます。"),
        ("I isolated it to a bad ground connection.", "原因はグラウンド接続の不良だと切り分けました。"),
        ("The regulator's getting way too hot to touch.", "レギュレータが熱くて触れないくらいです。"),
    ],
    "3Dプリンター・自作機材": [
        # --- 3Dプリンター特有の語彙・トラブルシューティング ---
        ("I'm getting some stringing between the towers.", "タワーの間に糸引きが出ています。"),
        ("The first layer isn't sticking to the bed.", "1層目がベッドに定着していません。"),
        ("You need to redo your bed leveling.", "ベッドレベリングをやり直す必要があります。"),
        ("It's warping badly at the corners.", "角のほうがひどく反っています。"),
        ("Try bumping the infill up to twenty percent.", "インフィルを20%まで上げてみて。"),
        ("Add some supports under that overhang.", "そのオーバーハングの下にサポートを追加して。"),
        ("Tree supports come off a lot cleaner than the regular ones.", "ツリーサポートのほうが通常のサポートより綺麗に外れます。"),
        ("Dial in your slicer settings before you run a big print.", "大きい造形の前に、スライサーの設定を詰めておいて。"),
        ("The nozzle's clogged — I need to do a cold pull.", "ノズルが詰まったので、コールドプル(冷却しながらの引き抜き清掃)をしないと。"),
        ("Swap in a fresh nozzle if the flow looks off.", "吐出量がおかしいなら、ノズルを新品に交換して。"),
        ("I switched from PLA to PETG for the outdoor parts.", "屋外用の部品はPLAからPETGに変えました。"),
        ("The print came out under-extruded.", "その造形は押出不足(アンダーエクストルージョン)気味に仕上がりました。"),
        ("Tuning the retraction settings fixed most of the stringing.", "リトラクション設定を調整したら、糸引きはほとんど直りました。"),
        ("I'm running a point-two millimeter layer height on this one.", "これは0.2mmのレイヤー高さで印刷しています。"),
        ("It warped because the bed wasn't hot enough.", "ベッドの温度が足りなくて反ってしまいました。"),
        ("Give the part a quick sand once it's off the bed.", "ベッドから外したら、軽くやすりがけして。"),
        ("I cut the enclosure out on a CNC router.", "筐体はCNCルーターで削り出しました。"),
        ("The tolerances are tight enough for a press-fit.", "圧入できるくらい公差が詰まっています。"),
        ("I designed it to print in place, so there's no assembly.", "組み立て不要になるように、プリント・イン・プレイスで設計しました。"),
        ("I modeled the bracket in CAD before printing it.", "印刷する前に、そのブラケットはCADで設計しました。"),
        ("The build plate needs a fresh coat of glue stick.", "ビルドプレートにスティックのりを塗り直す必要があります。"),
        ("Check that the Z-offset isn't set too low.", "Zオフセットが低すぎないか確認して。"),
    ],
    "メイカーコミュニティ・フォーラム発信": [
        # --- 公開・共有の定型表現 ---
        ("I've open-sourced all the files on GitHub.", "ファイル一式をGitHubでオープンソース公開しました。"),
        ("Here's my build log if you want to follow along.", "経過を追いたければ、こちらが製作記(ビルドログ)です。"),
        ("This worked for me — YMMV.", "私の環境ではこれでうまくいきました。ただし人によって結果は違うかもしれません(YMMV)。"),
        ("Feel free to fork this and make it your own.", "これは自由にフォークして、自分なりにアレンジしてください。"),
        ("I posted the full write-up on my blog.", "詳しい解説記事をブログに載せました。"),
        ("Thanks for the write-up — it saved me hours of debugging.", "その解説記事のおかげで、デバッグの時間が何時間も節約できました。"),
        ("Does anyone have a working STL for this bracket?", "このブラケットの動作確認済みのSTLを持っている人はいますか。"),
        ("I'll post an update once I've tested it more.", "もう少しテストしたら更新を投稿します。"),
        ("Credit to the original creator for the base design.", "元の設計については、オリジナルの作者にクレジットを。"),
        ("I remixed an existing design I found online.", "ネットで見つけた既存の設計をリミックス(改変)しました。"),
        ("Sharing this in case it helps someone else.", "誰かの役に立てばと思い共有します。"),
        # --- トラブルシューティングのやり取り ---
        ("I'm stuck — has anyone run into this before?", "行き詰まっています。同じ症状に遭遇した人はいますか。"),
        ("Turns out it was a cold solder joint the whole time.", "結局、原因はずっと冷はんだ接合でした。"),
        ("Solved it — turned out to be a loose connector.", "解決しました。原因はコネクタの緩みでした。"),
        ("I'll link the schematic in the comments.", "回路図はコメント欄にリンクしておきます。"),
        ("Bumping this thread — still looking for advice.", "このスレッドを上げます。まだアドバイスを探しています。"),
        ("Great write-up — thanks for documenting the whole process.", "素晴らしい解説記事ですね。工程を全部記録してくれてありがとう。"),
        ("I'll upload the Gerber files once I clean them up.", "ガーバーファイルは整理してからアップロードします。"),
        ("Consider this project vaporware until I actually finish it.", "完成するまでは、これはベーパーウェア(未完成の構想)だと思ってください。"),
        ("I'm chasing down a heisenbug that only shows up on some boards.", "一部の基板でしか出ないハイゼンバグ(観測すると消える謎バグ)を追いかけています。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("breadboard", "ブレッドボード(試作用基板)", "名詞", "I wired the sensor up on a breadboard first.", "電子工作", "600"),
    ("prototype", "試作品・プロトタイプ", "名詞", "This is just a rough prototype, not the final version.", "電子工作", "600"),
    ("iteration", "反復・改良版", "名詞", "We're already on the third iteration of the design.", "電子工作", "700"),
    ("revision", "改訂・リビジョン", "名詞", "I fixed the footprint error in this revision.", "電子工作", "700"),
    ("bill of materials", "部品表(BOM)", "名詞", "Check the bill of materials before you order parts.", "電子工作", "800"),
    ("open-source", "オープンソースの", "形容詞", "The whole project is open-source.", "電子工作", "600"),
    ("continuity", "導通", "名詞", "Check the continuity with a multimeter.", "電子工作", "700"),
    ("cold solder joint", "冷はんだ接合(はんだ不良)", "名詞", "A cold solder joint was causing the intermittent contact.", "電子工作", "800"),
    ("filament", "フィラメント(3Dプリンタ材料)", "名詞", "I ran out of filament halfway through the print.", "電子工作", "600"),
    ("nozzle", "ノズル", "名詞", "The nozzle clogged partway through the print.", "電子工作", "600"),
    ("infill", "インフィル・内部充填", "名詞", "I usually print with twenty percent infill.", "電子工作", "700"),
    ("warping", "反り(3Dプリント時の)", "名詞", "Warping is common with ABS on a cold bed.", "電子工作", "700"),
    ("stringing", "糸引き(3Dプリント時の)", "名詞", "Stringing usually means your retraction needs tuning.", "電子工作", "700"),
    ("slicer", "スライサー(3Dプリント用ソフト)", "名詞", "Load the model into the slicer before you print.", "電子工作", "600"),
    ("enclosure", "筐体・ケース", "名詞", "I printed an enclosure for the whole board.", "電子工作", "600"),
    ("brick", "文鎮化させる(誤操作で使用不能にする)", "動詞", "Don't flash that firmware, you'll brick the device.", "電子工作", "700"),
    ("remix", "既存の設計を改変する", "動詞", "I remixed his design to fit a bigger battery.", "電子工作", "700"),
    ("write-up", "まとめ記事・解説記事", "名詞", "I posted a full write-up of the build.", "電子工作", "600"),
    ("vaporware", "未完成のまま終わった構想(ベーパーウェア)", "名詞", "The project stayed vaporware for over a year.", "電子工作", "900"),
    ("heisenbug", "観測すると再現しなくなる不可解なバグ", "名詞", "It's a heisenbug — it vanishes the moment I attach the debugger.", "電子工作", "900"),
]


# --- insertion --------------------------------------------------------------

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")
_STOP = {
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on", "at",
    "for", "with", "from", "by", "as", "is", "are", "was", "were", "be", "been",
    "do", "does", "did", "have", "has", "had", "will", "would", "can", "could",
    "should", "may", "might", "must", "i", "you", "he", "she", "it", "we",
    "they", "me", "him", "her", "us", "them", "my", "your", "his", "its", "our",
    "their", "this", "that", "these", "those", "here", "there", "what", "when",
    "where", "who", "how", "why", "not", "no", "yes", "so", "up", "out", "off",
    "down", "let", "lets", "please", "thanks", "thank", "ok", "okay", "im",
    "ill", "id", "ive", "dont", "cant", "wont", "isnt", "thats", "whats",
    "very", "just", "too", "more", "some", "any", "all", "one", "two", "get",
    "got", "go", "going", "like", "want", "need", "make", "made", "take",
    "see", "now", "today", "tonight", "good", "well", "back", "about", "over",
    "into", "than", "then", "again", "really", "much", "many", "wish", "mind",
    "could", "would", "shall", "rather", "ever", "way", "everyone", "everybody",
    "minute", "minutes", "second", "seconds", "little", "bit", "few", "keep",
    "sorry", "still", "afterward", "instead", "else", "same", "time", "next",
}


def _content_words(phrases: list[tuple[str, str]]) -> set[str]:
    out: set[str] = set()
    for en, _ in phrases:
        for tok in _WORD_RE.findall(en.lower()):
            w = tok.strip("'-")
            if len(w) >= 4 and w not in _STOP:
                out.add(w)
    return out


def report_missing() -> None:
    """Print content words used in the new phrases that are not yet in `words`
    and not covered by the WORDS list above (authoring aid)."""
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
    covered = {w[0].lower() for w in WORDS}
    all_phrases = [p for lst in PHRASES_BY_SCENE.values() for p in lst]
    missing = sorted(
        w for w in _content_words(all_phrases)
        if w not in existing and w not in covered
    )
    print(f"missing content words ({len(missing)}):")
    print(", ".join(missing))


def main() -> int:
    if "--missing-words" in sys.argv:
        report_missing()
        return 0

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
