# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for NBA / BASKETBALL ENGLISH, authored by Claude.

Focus (フレーズ集の手薄な領域を補強): NBA・バスケットボール特有の英語。
日本人ファンの母数が大きく、特に日本人選手のNBA挑戦以降は視聴熱がさらに
高まっている領域。日本語実況・日本語記事での情報網羅性はすでに高いため、
差別化ポイントは「スコアを追う」ことではなく、英語の実況・ハイライト解説・
ファンの会話（ESPN/TNTのようなbroadcast register）を生で理解できること。
既存の「スポーツ」ドメインには referee/coach/tournament/penalty/foul/
dribble/halftime/lineup など一般的なスポーツ語彙・基礎バスケ語彙は
既にあるが、NBA/バスケットボール固有の語彙・言い回しは一つもカバーされて
いなかった（DB照会で確認済み。dribble/foul/halftime/lineup は既存のため
本バッチでは再追加していない）。

本バッチでは以下を体系的に強化する:

  - 試合展開・スタッツ用語（トリプルダブル/速攻/ピック・アンド・ロール/
    アリウープ/ブザービーター/ボックススコア/PER/トゥルーシューティング率）
  - 実況・解説でよく使われる言い回し（"He's on fire"/"And-one"/
    "That's a foul"/"He took that personally"/"clutch" など、乾いた
    ルール説明ではなく生きた実況の register）
  - 編成・契約関連用語（トレード期限/ラグジュアリータックス/
    ツーウェイ契約/Gリーグ配属/負荷管理/バード条項など）
  - 現地観戦のための表現（ローワーボウル席/シュートアラウンド/
    ハーフタイムショー/コートサイド/ジャンボトロン）

丁寧度や専門用語の意味が分かるよう、日本語訳に〔注〕を付した。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_basketball_nba.py
      python scripts/add_basketball_nba.py --missing-words   # report only

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
    "バスケットボール・NBA": [
        # --- 試合展開・スタッツ用語 ---
        ("He just recorded a triple-double — points, rebounds, and assists.", "彼はトリプルダブルを記録しました――得点、リバウンド、アシストの三部門で二桁です。〔注: triple-double＝3部門で二桁を記録すること〕"),
        ("They're pushing the fast break after that steal.", "スティールからそのまま速攻を仕掛けています。〔注: fast break＝相手が守備を整える前に一気にゴールへ攻め込む速攻〕"),
        ("That's a beautiful pick-and-roll right there.", "見事なピック・アンド・ロールですね。〔注: pick-and-roll＝スクリーンをかけてからゴールに切り込む連携プレー〕"),
        ("Alley-oop! He threw it down with authority.", "アリウープ！力強くたたき込みました。〔注: alley-oop＝味方が投げたパスを空中で受けてそのままダンクすること〕"),
        ("He drains the buzzer-beater at the horn!", "ブザーが鳴ると同時に決めました、ブザービーターです！〔注: buzzer-beater＝制限時間終了間際に決まるシュート〕"),
        ("Let's check the box score — he had thirty and ten.", "ボックススコアを見てみましょう――彼は30得点10リバウンドでした。〔注: box score＝各選手の個人成績表〕"),
        ("His PER is off the charts this season.", "今シーズンの彼のPERは驚異的な数字です。〔注: PER＝player efficiency rating、選手の総合的な効率を示す指標〕"),
        ("His true shooting percentage is the best in the league.", "彼のトゥルーシューティング率はリーグ最高です。〔注: true shooting percentage＝2P・3P・フリースローを加味した実質的なシュート効率の指標〕"),
        ("He hit the pick-and-pop for three.", "ピック・アンド・ポップから3ポイントを沈めました。〔注: pick-and-pop＝スクリーンをかけた後に外に開いてシュートを狙う戦術〕"),
        ("And-one! He finishes through the contact.", "エンドワン！接触を受けながらも決めきりました。〔注: and-one＝ファウルを受けながらシュートを決め、フリースロー1本が追加されること〕"),
        ("He grabs his own miss and puts it back in.", "自分のミスショットを拾って押し込みました。〔注: putback＝味方または自分のリバウンドをそのまま得点にすること〕"),
        ("He pulls up for the fadeaway jumper.", "フェイダウェイジャンパーを打ちます。〔注: fadeaway＝後ろに反りながら打つシュート〕"),
        ("He steps back behind the line and buries it.", "一歩下がって3ポイントラインの外から沈めました。〔注: step-back three＝ステップバックしてスペースを作って打つ3ポイントシュート〕"),
        ("That's an offensive foul, he was set for the charge.", "オフェンスファウルです、しっかり位置取りしてチャージを取りました。〔注: charge＝守備側が完全に静止していた場合に取られるオフェンスファウル〕"),
        ("He got called for a travel on that spin move.", "あのスピンムーブでトラベリングを取られました。〔注: travel＝ボールを保持したまま規定以上歩くバイオレーション〕"),
        ("They're bringing the double team as soon as he touches it.", "ボールを持った瞬間にダブルチームを仕掛けています。〔注: double team＝二人がかりで一人を守るディフェンス〕"),
        ("They're in a full-court press to force the turnover.", "ターンオーバーを狙ってオールコートプレスを仕掛けています。〔注: full-court press＝コート全体でプレッシャーをかけるディフェンス〕"),
        ("They switched to a zone defense in the second half.", "後半からゾーンディフェンスに切り替えました。〔注: zone defense＝特定のエリアを分担して守るディフェンス方式〕"),
        # --- 実況・解説の決まり文句 ---
        ("He's on fire right now, that's his fifth three in a row!", "彼は今、完全に乗っています。5本連続の3ポイントです！〔注: on fire＝好調が続いている状態を表す口語〕"),
        ("He's really cooking tonight.", "今夜の彼は絶好調ですね。〔注: cooking＝on fireと同様、絶好調を表す口語表現〕"),
        ("Downtown! Nothing but net!", "ダウンタウン！完全なスウィッシュです！〔注: downtown＝リングから遠い3ポイントシュートを指す口語。nothing but net＝リングにもボードにも触れず入るきれいなシュート〕"),
        ("Get that outta here! Incredible block!", "それは持って帰れ！信じられないブロックです！〔注: 相手のシュートを豪快にブロックした際の実況の決まり文句〕"),
        ("That's a poster right there!", "これはポスター級のダンクですね！〔注: poster＝相手を踏み台にするような豪快なダンクを指す口語表現〕"),
        ("He's got some serious hops.", "彼はものすごいジャンプ力を持っていますね。〔注: hops＝跳躍力を指すくだけた表現〕"),
        ("He took that personally.", "彼はあれを個人的な挑発として受け止めましたね。〔注: やられたことへの反発から本気モードになった選手を評する実況の定番フレーズ〕"),
        ("Ice in his veins, he never even blinked.", "冷静沈着、まったく動じませんでしたね。〔注: ice in his veins＝プレッシャー下でも冷静な様子を表す慣用句〕"),
        ("He's clutch, he wants the ball in his hands right now.", "彼はクラッチプレーヤーです、今この瞬間にボールを託されたがっています。〔注: clutch＝勝負どころで結果を出す能力・選手を指す〕"),
        ("Ball don't lie!", "ボールは嘘をつかない！〔注: 直前のファウル判定が正しかったことを、フリースローを外した選手を見て揶揄する決まり文句〕"),
        ("He's in the bonus, so this is two free throws.", "ボーナスに入っているので、これは2本のフリースローです。〔注: bonus＝1クォーターでのチームファウル数が規定を超え、以降のファウルでフリースローが与えられる状態〕"),
        ("He's got three fouls already, they need to watch his foul trouble.", "すでにファウル3つ、ファウルトラブルに気をつけないといけません。〔注: foul trouble＝退場につながりかねないファウル数がたまっている状態〕"),
        ("That's a technical foul on the bench.", "ベンチにテクニカルファウルが宣告されました。〔注: technical foul＝スポーツマンシップに反する言動などに科されるファウル〕"),
        ("That was a flagrant foul, no doubt about it.", "あれは間違いなくフレグラントファウルです。〔注: flagrant foul＝悪質・過度な接触とみなされる重いファウル〕"),
    ],
    "バスケットボール・移籍・契約": [
        ("The trade deadline is next Thursday, and rumors are swirling.", "トレード期限は来週木曜日、噂が飛び交っています。"),
        ("That contract would put them deep into the luxury tax.", "あの契約を結べば、彼らは大きくラグジュアリータックスの対象になります。〔注: luxury tax＝サラリーキャップの上限を超えて支払う罰金的な税〕"),
        ("He signed a two-way contract with the team this summer.", "彼はこの夏、チームとツーウェイ契約を結びました。〔注: two-way contract＝NBAとGリーグを行き来する若手向けの契約〕"),
        ("He's been assigned to the G League for some reps.", "出場機会を積むため、Gリーグへ配属されました。〔注: G League assignment＝下部組織であるGリーグへの一時的な配属〕"),
        ("He's out tonight for load management.", "今夜は負荷管理のため欠場です。〔注: load management＝故障予防のために計画的に休養させること〕"),
        ("He signed a max contract extension this offseason.", "このオフシーズン、彼は最大契約の延長にサインしました。〔注: max contract＝選手が受け取れる上限額の契約〕"),
        ("They're looking to negotiate a buyout with the veteran.", "彼らはそのベテラン選手とのバイアウト交渉を検討しています。〔注: buyout＝契約を打ち切る代わりに一定額を支払う合意〕"),
        ("He was the number one pick in the draft lottery.", "彼はドラフトくじ引きの結果、全体1位指名でした。〔注: draft lottery＝下位チームの指名順位を抽選で決める制度〕"),
        ("He's a restricted free agent this summer.", "今夏、彼は制限付きフリーエージェントです。〔注: restricted free agent＝元のチームが他球団のオファーに対抗できる権利を持つFA〕"),
        ("Once he hits unrestricted free agency, any team can sign him.", "完全FAになれば、どのチームとも契約できます。〔注: unrestricted free agent＝元のチームに優先権のないFA〕"),
        ("They worked out a sign-and-trade to get the deal done.", "契約合意のため、サイン・アンド・トレードを成立させました。〔注: sign-and-trade＝一度再契約してからトレードする手法〕"),
        ("He has a player option for next season.", "彼には来シーズンのプレーヤーオプションがあります。〔注: player option＝選手側が残留か契約解除かを選べる権利〕"),
        ("The team holds his Bird rights, so they can go over the cap to keep him.", "チームは彼のバード条項の権利を持っているので、キャップを超えて残留させられます。〔注: Bird rights＝一定年数在籍した選手に対し、サラリーキャップ超過での再契約を認める規定〕"),
        ("They're using the taxpayer mid-level exception to fill out the roster.", "ロースターを埋めるため、タックスペイヤー・ミッドレベル例外を使っています。〔注: mid-level exception＝キャップ超過チームでも一定額まで選手獲得を認める例外枠〕"),
        ("He was waived and stretched over the next three years.", "彼はウェイブされ、契約残額は今後3年に分割されます。〔注: stretch provision＝解雇した選手の残り契約金を複数年に分けて支払う仕組み〕"),
    ],
    "バスケットボール・現地観戦": [
        ("We got lower bowl seats right on the baseline.", "ベースライン沿いのローワーボウル席が取れました。〔注: lower bowl＝アリーナ下層の観客席〕"),
        ("The team is doing an open shootaround before the game.", "試合前、公開シュートアラウンドが行われます。〔注: shootaround＝試合前のウォームアップ練習〕"),
        ("Don't miss the halftime show, they've got a dunk contest planned.", "ハーフタイムショーをお見逃しなく、ダンクコンテストが予定されています。"),
        ("We splurged on courtside seats for his last game here.", "彼のここでのラストゲームにコートサイド席を奮発しました。〔注: courtside＝コートのすぐ脇にある最前列の高額席〕"),
        ("We're up in the upper deck tonight, but the view's still great.", "今夜はアッパーデッキ（上層階席）ですが、それでも眺めは十分です。"),
        ("Tip-off is at seven, so let's grab food before that.", "ティップオフは7時なので、それまでに食べ物を買っておきましょう。〔注: tip-off＝試合開始のジャンプボール〕"),
        ("Check the jumbotron, they're doing the dance cam.", "ジャンボトロンを見て、ダンスカムをやっています。〔注: jumbotron＝アリーナ中央に吊るされた大型映像スクリーン〕"),
        ("They shot t-shirts into the crowd with the t-shirt cannon.", "Tシャツ砲で観客席にTシャツを撃ち込んでいました。〔注: t-shirt cannon＝観客にグッズを撃ち出す名物演出〕"),
        ("The mascot is racing someone from the crowd during the timeout.", "タイムアウト中、マスコットが観客の一人と競走しています。"),
        ("Let's meet at will call to pick up the tickets.", "チケットを受け取るためウィルコールで待ち合わせましょう。〔注: will call＝当日窓口で受け取るチケット引換所〕"),
        ("The line to get to our section is backed up on the concourse.", "私たちのセクションへの列がコンコースまで伸びています。〔注: concourse＝観客席の外周にある通路・広場エリア〕"),
        ("They're giving out City Edition jerseys to the first ten thousand fans.", "最初の1万人にシティエディションのユニフォームが配られます。〔注: City Edition＝地域色を強く出した特別デザインのユニフォーム〕"),
        ("Everyone stand for the national anthem.", "国歌斉唱のため、皆さん起立してください。"),
        ("It's opening night, so they're raising the championship banner first.", "開幕戦なので、まず優勝バナーの掲揚が行われます。"),
        ("We're doing media day coverage before the season starts.", "シーズン開幕前のメディアデーの取材をしています。"),
        ("Keep an eye out, the kiss cam might land on us during the next timeout.", "気をつけて、次のタイムアウトでキスカムが私たちを映すかもしれません。〔注: kiss cam＝観客を映しキスを促す会場の名物演出〕"),
        ("Grab your rally towel, they hand them out at the door.", "ラリータオルを受け取ってください、入り口で配っています。〔注: rally towel＝応援用に配られるタオル〕"),
        ("We stuck around for the postgame player interviews.", "試合後の選手インタビューまで残っていました。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("triple-double", "トリプルダブル（3部門で二桁の成績）", "名詞", "He nearly had a triple-double last night.", "バスケットボール", "700"),
    ("fast break", "速攻", "名詞", "They scored easily on the fast break.", "バスケットボール", "600"),
    ("pick-and-roll", "ピック・アンド・ロール", "名詞", "Their pick-and-roll is nearly unstoppable.", "バスケットボール", "700"),
    ("alley-oop", "アリウープ", "名詞", "He caught the alley-oop and slammed it home.", "バスケットボール", "700"),
    ("buzzer-beater", "ブザービーター", "名詞", "He hit a buzzer-beater to win the game.", "バスケットボール", "700"),
    ("box score", "ボックススコア（個人成績表）", "名詞", "Check the box score for his final stat line.", "バスケットボール", "700"),
    ("rebound", "リバウンド", "名詞", "He grabbed the rebound and pushed the pace.", "バスケットボール", "600"),
    ("putback", "プットバック（自分・味方のリバウンドをそのまま得点にすること）", "名詞", "He scored on a quick putback after the miss.", "バスケットボール", "800"),
    ("fadeaway", "フェイダウェイ（後ろに反りながら打つシュート）", "名詞", "His fadeaway is nearly impossible to block.", "バスケットボール", "800"),
    ("screen", "スクリーン（味方のためにディフェンスを止める動き）", "名詞", "He set a hard screen to free up the shooter.", "バスケットボール", "700"),
    ("clutch", "勝負どころで結果を出す・土壇場に強い", "形容詞", "He's known as one of the most clutch players in the league.", "バスケットボール", "700"),
    ("the paint", "ペイントエリア（ゴール下の色付きエリア）", "名詞", "He's been dominant in the paint all night.", "バスケットボール", "700"),
    ("perimeter", "ペリメーター（3ポイントライン付近の外周エリア）", "名詞", "He's a great shooter from the perimeter.", "バスケットボール", "800"),
    ("possession", "ポゼッション（攻撃権・1回の攻撃機会）", "名詞", "They need to win every possession down the stretch.", "バスケットボール", "700"),
    ("starting five", "スターティングファイブ（先発5人）", "名詞", "He's been in the starting five all season.", "バスケットボール", "600"),
    ("mismatch", "ミスマッチ（体格差などによる有利な対決）", "名詞", "They're hunting for a mismatch in the post.", "バスケットボール", "700"),
    ("crossover", "クロスオーバー（ドリブルの切り返し）", "名詞", "His crossover left the defender flat-footed.", "バスケットボール", "700"),
    ("shot clock", "ショットクロック（攻撃制限時間）", "名詞", "The shot clock is winding down.", "バスケットボール", "600"),
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
