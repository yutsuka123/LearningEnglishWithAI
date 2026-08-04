# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for MLB / OVERSEAS BASEBALL ENGLISH, authored by
Claude.

Focus (フレーズ集の手薄な領域を補強): MLB・海外野球特有の英語。日本の野球
ファンはMLBを日本語実況・日本語記事で追うことが多く、日本語の情報網羅性は
既に高い。差別化ポイントは「スコアを追う」ことではなく、英語の実況・記事・
ファンの会話を生で理解できること。既存の「スポーツ」ドメインには
referee/coach/tournament/marathon/penalty/podium/doping/lineup/rookie/
veteran/umpire など一般的なスポーツ語彙は既にあるが、野球固有の語彙・
言い回しは一つもカバーされていなかった（DB照会で確認済み）。

本バッチでは以下を体系的に強化する:

  - 試合展開・得点シーン（サヨナラ勝ち/満塁本塁打/ノーヒットノーラン/
    完全試合/ブルペン/代打/犠牲フライ/盗塁/牽制）
  - スタッツ・分析用語（防御率/WAR/OPS/打率/このペースでいくと〜）
  - 実況・解説でよく使われる言い回し（バッターボックスに入る/フルカウント/
    振り逃げ・チェックスイング/タッチアップ/三塁を回る）
  - 編成・ロースター関連用語（ウェイバー/トレード期限/FA/故障者リスト/
    リハビリ登板）
  - 現地観戦のための表現（外野自由席/ファウルボール/7回表のストレッチ/
    ボブルヘッド・ナイト/テールゲート）

ESPN・MLB Network のような、実際のMLB放送・ファンの話し方（乾いた規則集
ではなく、生きた実況・会話の register）に忠実になるよう心がけた。丁寧度や
専門用語の意味が分かるよう、日本語訳に〔注〕を付した。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_baseball_mlb.py
      python scripts/add_baseball_mlb.py --missing-words   # report only

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
    "野球・MLB": [
        # --- 試合展開・得点シーン ---
        ("He hit a walk-off home run in the bottom of the ninth!", "9回裏、彼がサヨナラ本塁打を放ちました！〔注: walk-off＝ホームチームがそのままフィールドを去る＝試合を決める一打〕"),
        ("Grand slam! The bases were loaded and he cleared them all.", "満塁本塁打！塁を埋めていたランナーを一気に全員かえしました。"),
        ("He's throwing a no-hitter through seven innings.", "7回まで、彼はノーヒットノーランのピッチングを続けています。"),
        ("It's a perfect game so far, twenty-one up, twenty-one down.", "ここまで完全試合、21人が打席に立って21人ともアウトです。〔注: perfect game＝一人も出塁を許さない完全試合〕"),
        ("The manager is going to the bullpen to bring in a fresh arm.", "監督はブルペンに新しい投手を要求しに行きます。〔注: bring in a fresh arm＝疲れていない新しい投手を投入する〕"),
        ("He's pinch-hitting for the pitcher in this spot.", "ここでピッチャーに代わって代打が送られます。"),
        ("That's a sacrifice fly, deep enough to score the runner from third.", "犠牲フライです、三塁ランナーが生還できるだけの十分な深さでした。"),
        ("He stole second base on the very first pitch.", "彼は初球で二塁への盗塁を決めました。"),
        ("The pitcher picked him off at first base.", "投手が一塁で彼を牽制アウトにしました。〔注: pick off＝牽制球でランナーをアウトにする〕"),
        ("He got caught stealing by a mile.", "彼は盗塁失敗、かなりの差でアウトになりました。〔注: by a mile＝口語で「大差で」〕"),
        ("The go-ahead run scored on a wild pitch.", "勝ち越し点は暴投で生まれました。"),
        ("He came around to score on a passed ball.", "彼はパスボールで一気にホームまで生還しました。"),
        ("It's a bang-bang play at first, but the umpire calls him out.", "一塁は際どいタイミングでしたが、審判はアウトを宣告しました。〔注: bang-bang play＝セーフかアウトかほぼ同時のきわどいプレー〕"),
        ("The bullpen has been lights-out all season.", "今シーズン、ブルペン陣はずっと完璧な働きをしています。〔注: lights-out＝ほぼ完璧に抑えている、口語表現〕"),
        ("He blew the save in the ninth.", "彼は9回にセーブを守れず逆転を許しました。〔注: blow a save＝守護神がリードを守りきれない〕"),
        ("It's a comebacker right back to the mound.", "打球は投手の元へまっすぐ戻るような当たりでした。〔注: comebacker＝投手方向への強い打球〕"),
        # --- スタッツ・分析用語 ---
        ("His ERA has dropped under three this season.", "今シーズン、彼の防御率は3を切りました。〔注: ERA＝earned run average、防御率〕"),
        ("He leads the league in WAR among all position players.", "野手の中でWARはリーグトップです。〔注: WAR＝wins above replacement、控え選手と比較した貢献度の総合指標〕"),
        ("His OPS is well over nine hundred this year.", "今年の彼のOPSは.900をゆうに超えています。〔注: OPS＝出塁率＋長打率〕"),
        ("He's hitting three-twenty on the season.", "今シーズンの打率は3割2分です。〔注: 打率は口語では小数点以下3桁を「〇〇〇」と数字で読む〕"),
        ("He's on pace for fifty home runs this year.", "今年のペースだと50本塁打に到達しそうです。〔注: on pace for〜＝このままのペースでいくと〜に達するという見込み表現〕"),
        ("His strikeout-to-walk ratio is the best in the rotation.", "彼の奪三振と与四球の比率は先発陣で最高です。"),
        ("He's slugging over five hundred this season.", "今シーズンの長打率は.500を超えています。〔注: slugging percentage、長打力の指標〕"),
        ("His exit velocity on that one was over a hundred and ten.", "あの打球の打球速度は時速110マイルを超えていました。〔注: exit velocity＝打球初速、Statcast由来の指標〕"),
        ("That ball had a launch angle that was almost too steep.", "あの打球は打ち出し角度がやや急すぎるくらいでした。〔注: launch angle＝打球の打ち出し角〕"),
        # --- 実況・解説フレーズ ---
        ("He's stepping into the box now.", "彼が今、バッターボックスに入ります。"),
        ("We've got a full count, three balls and two strikes.", "フルカウントです、3ボール2ストライク。"),
        ("That's a checked swing, and the umpire rules he went around.", "チェックスイングです、審判はスイングしたと判定しました。〔注: checked swing＝振りかけて止めたスイング。went around＝バットが振り切ったと見なされること〕"),
        ("He tags up and scores easily from third.", "彼はタッチアップして、三塁から難なく生還しました。〔注: tag up＝フライ捕球後にランナーが元の塁に戻ってから進塁すること〕"),
        ("He's rounding third and heading for home.", "三塁を回って本塁へ向かっています。"),
        ("The count is full, and here's the payoff pitch.", "フルカウントです、勝負の一球がここに来ます。〔注: payoff pitch＝フルカウントでの決定的な一球〕"),
        ("He fouls it off to stay alive at the plate.", "彼はファウルで粘って打席をつなぎます。"),
        ("That's a frozen rope right into the gap.", "外野の間を抜ける鋭いライナーです。〔注: frozen rope＝強烈なライナー性の打球を表す口語〕"),
        ("He golfed that one out for a home run.", "彼は低い球をすくい上げてホームランにしました。〔注: golf＝低めの球をゴルフのように振り抜いて打つこと〕"),
        ("That's a can of corn to center field.", "センターへの easy fly です。〔注: can of corn＝処理が簡単な緩いフライの口語表現〕"),
        ("He's really painting the corners tonight.", "今夜の彼はコースの隅々を突く投球ができています。〔注: paint the corners＝ストライクゾームの外角低めなどをうまく突くこと〕"),
        ("He struck him out swinging to end the inning.", "空振り三振でその回を終わらせました。"),
        ("He struck him out looking on a nasty slider.", "鋭いスライダーで見逃し三振に打ち取りました。"),
        # --- 編成・ロースター関連 ---
        ("He got claimed off waivers by a division rival.", "彼は地区のライバル球団にウェイバー公示から獲得されました。〔注: waiver wire＝戦力外・DFA選手を他球団が獲得できる公示制度〕"),
        ("The trade deadline is at the end of the month.", "トレード期限は今月末です。"),
        ("They're expected to be sellers at the deadline this year.", "今年、彼らはトレード期限に向けて主力を放出する立場になりそうです。〔注: sellers＝優勝が難しく主力を売却するチーム〕"),
        ("He's a free agent at the end of the season.", "シーズン終了後、彼はフリーエージェントになります。"),
        ("He got placed on the 10-day injured list with a hamstring strain.", "ハムストリングの肉離れで10日間の故障者リスト入りとなりました。〔注: IL＝injured list、故障者リスト〕"),
        ("He's starting a rehab assignment in the minors this week.", "今週からマイナーでリハビリ登板を始めます。"),
        ("He got called up from Triple-A yesterday.", "昨日、彼は3Aから昇格しました。"),
        ("He was optioned back down to the minors after the game.", "試合後、彼はマイナーへ降格（オプション）となりました。〔注: option down＝マイナー契約枠を使って降格させること〕"),
        ("He was designated for assignment to clear a roster spot.", "ロースター枠を空けるため、彼はDFA（戦力外指定）となりました。〔注: DFA＝designated for assignment、40人枠から一時的に外す措置〕"),
        ("The team has a logjam in the outfield right now.", "今、チームは外野手の人数過多で起用に頭を悩ませています。〔注: logjam＝同じポジションに有力選手が集中している状態〕"),
        # --- 現地観戦のための表現 ---
        ("Are the bleacher seats general admission?", "外野自由席は自由席（指定なし）ですか？〔注: bleacher seats＝外野の簡素な観客席〕"),
        ("Watch out, foul ball!", "危ない、ファウルボールです！"),
        ("He caught the foul ball bare-handed.", "彼は素手でファウルボールをキャッチしました。"),
        ("It's time for the seventh-inning stretch.", "7回表と裏の間、セブンスインニングストレッチの時間です。〔注: 観客が立ち上がって体を伸ばし、応援歌を歌う伝統〕"),
        ("Let's sing 'Take Me Out to the Ballgame.'", "「テイク・ミー・アウト・トゥ・ザ・ボールゲーム」を歌いましょう。〔注: セブンスインニングストレッチの定番曲〕"),
        ("Tonight's a bobblehead night, so get here early.", "今夜はボブルヘッド・ナイトなので、早めに来てください。〔注: 来場者先着でボブルヘッド人形が配られるプロモーション〕"),
        ("We're tailgating in the parking lot before the game.", "試合前、駐車場でテールゲートパーティーをします。〔注: tailgate＝車のトランクを開けて行う球場前の飲食パーティー〕"),
        ("Let's grab a hot dog and a beer before we head to our seats.", "席に着く前にホットドッグとビールを買いましょう。"),
        ("The kiss cam just landed on us!", "キスカムが私たちを映しました！〔注: kiss cam＝観客を映しキスを促す球場の名物演出〕"),
        ("Let's stick around for the postgame fireworks.", "試合後の花火まで残りましょう。"),
        ("The line for team merchandise is out the door.", "グッズ売り場の列がお店の外まで伸びています。"),
        ("We got upgraded to seats right behind home plate.", "本塁後方の席にアップグレードしてもらえました。"),
        ("The vendor is walking through the stands selling peanuts.", "売り子が観客席を歩いてピーナッツを売っています。"),
        # --- ファン・実況の会話表現 ---
        ("Did you see that catch? Robbery!", "あのキャッチ見た？完全に打球泥棒だよ！〔注: robbery＝好捕でホームランなどを阻止すること〕"),
        ("That umpire has a really tight strike zone tonight.", "今夜のあの審判はストライクゾーンがかなり狭いね。"),
        ("He's been in a real slump the last couple weeks.", "彼はここ数週間、本当にスランプに陥っている。"),
        ("He's been on a tear since the All-Star break.", "オールスター明けから彼はずっと絶好調だ。〔注: on a tear＝連続して好成績を残している状態〕"),
        ("This team is a real long shot to make the playoffs.", "このチームがプレーオフに進むのはかなり厳しそうだ。"),
        ("They clinched a playoff spot last night.", "彼らは昨夜プレーオフ進出を決めた。"),
        ("They got eliminated from postseason contention.", "彼らはポストシーズン進出の可能性がなくなった。"),
        ("Who do you think they'll name as the starting pitcher tomorrow?", "明日の先発は誰になると思う？"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("bullpen", "ブルペン（救援投手の待機・投球練習場所）", "名詞", "The bullpen has been overworked this week.", "野球", "600"),
    ("pinch hitter", "代打", "名詞", "He sent in a pinch hitter with the game on the line.", "野球", "600"),
    ("sacrifice fly", "犠牲フライ", "名詞", "He drove in the run with a sacrifice fly.", "野球", "700"),
    ("stolen base", "盗塁", "名詞", "He recorded his thirtieth stolen base of the season.", "野球", "600"),
    ("no-hitter", "ノーヒットノーラン", "名詞", "He carried a no-hitter into the eighth inning.", "野球", "600"),
    ("perfect game", "完全試合", "名詞", "Only a handful of pitchers have thrown a perfect game.", "野球", "700"),
    ("grand slam", "満塁本塁打", "名詞", "He hit a grand slam to put the game away.", "野球", "600"),
    ("walk-off", "サヨナラの（試合を決める一打の）", "形容詞", "That was his second walk-off hit this month.", "野球", "700"),
    ("earned run average", "防御率", "名詞", "His earned run average is the best in the division.", "野球", "800"),
    ("batting average", "打率", "名詞", "His batting average has climbed over the last month.", "野球", "600"),
    ("full count", "フルカウント", "名詞", "It's a full count with two outs in the ninth.", "野球", "600"),
    ("waiver wire", "ウェイバー公示（他球団が獲得できる制度）", "名詞", "He was picked up off the waiver wire in September.", "野球", "800"),
    ("trade deadline", "トレード期限", "名詞", "The team was active right up until the trade deadline.", "野球", "700"),
    ("free agency", "フリーエージェント（制度・身分）", "名詞", "He'll enter free agency after this season.", "野球", "700"),
    ("injured list", "故障者リスト", "名詞", "He was placed on the injured list with a shoulder issue.", "野球", "700"),
    ("rehab assignment", "リハビリ登板・出場", "名詞", "He's on a rehab assignment before rejoining the majors.", "野球", "800"),
    ("bleacher seats", "外野自由席", "名詞", "We watched the game from the bleacher seats.", "野球", "600"),
    ("foul ball", "ファウルボール", "名詞", "A kid in the front row caught the foul ball.", "野球", "500"),
    ("tailgating", "テールゲートパーティー（球場前の駐車場での飲食）", "名詞", "Tailgating before the game is a big tradition here.", "野球", "700"),
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
    "could", "would", "shall", "rather", "ever", "way", "before", "after",
    "still", "already", "even", "away", "right", "left", "next", "last",
    "each", "same", "own", "such", "only", "also", "both", "between",
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
