# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for EUROPEAN FOOTBALL / SOCCER ENGLISH (Premier
League・Champions League register), authored by Claude.

Focus (フレーズ集の手薄な領域を補強): 欧州サッカー、特にプレミアリーグ /
チャンピオンズリーグを追う日本のファンに刺さる、実況・分析・移籍報道の
「生きた」英語。既存の「スポーツ」ドメインには referee/coach/tournament/
marathon/penalty/podium/doping/foul/dribble/jersey/halftime/lineup など
一般的なスポーツ語彙は既にあるが、サッカー（フットボール）に固有の戦術用語・
実況の決まり文句・移籍市場のビジネス英語は一つもカバーされていなかった。
本バッチでは以下を体系的に強化する:

  - 試合日・戦術語彙（オフサイドトラップ/ハイプレス/偽9番/クリーンシート/
    ロスタイム・アディショナルタイム/VARレビュー/セットピース）
  - 実況の決まり文句（What a strike! / He's through on goal! /
    stonewall penalty / sent off / away goals rule など）
  - 移籍市場・ビジネス英語（ローン移籍/リリース条項/メディカル/新加入発表/
    残留争い/CL出場権争い/移籍市場の締切日）
  - 現地観戦フレーズ（アウェイエンド/テラス/キックオフ時刻/ダフ屋/
    スタジアムの雰囲気）

Sky Sports や Match of the Day のような、実際の英語圏フットボールメディア・
ファンの話し方（乾いたルール集ではなく、生きた実況・会話の register）に
忠実になるよう心がけた。専門用語の意味やニュアンスが分かるよう、日本語訳に
〔注〕を付した。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_soccer_epl.py
      python scripts/add_soccer_epl.py --missing-words   # report only

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
    "サッカー・欧州フットボール": [
        # --- フォーメーション・戦術 ---
        ("They're set up in a back four today.", "今日は4バックのシステムで組んでいます。"),
        ("He's playing in the false nine role.", "彼はフォルスナイン（偽9番）の役割でプレーしている。〔注: false nine＝センターフォワードの位置から中盤に下がってプレーするタイプの選手〕"),
        ("They're pressing really high up the pitch.", "かなり高い位置からプレスをかけています。〔注: high press＝相手ゴールに近い高い位置からボールを奪いに行く守備戦術〕"),
        ("They caught him offside with a perfectly timed offside trap.", "見事なタイミングのオフサイドトラップで彼をオフサイドに引っかけた。〔注: offside trap＝守備ラインを一斉に上げ、相手をオフサイドの位置に誘い込む戦術〕"),
        ("They're playing a really high defensive line.", "かなり高いディフェンスラインを敷いています。"),
        ("They've switched to a back three after the substitution.", "選手交代後、3バックに切り替えました。"),
        ("He's dropped into the pocket between the lines.", "彼は相手の中盤と最終ラインの間のポケットスペースに下がってきている。〔注: 「ライン間」と呼ばれる、フリーになりやすいスペース〕"),
        ("They're overloading the left flank.", "左サイドに数的優位を作っています。〔注: overload＝特定エリアに人数をかけて数的優位を作る戦術〕"),
        ("It's a really well-worked set piece.", "非常によく練られたセットプレーです。"),
        ("They're sitting deep and hitting them on the counter.", "深めに構えて、カウンターで仕留めようとしています。"),
        # --- 試合結果・スコア関連語 ---
        ("They kept a clean sheet away from home.", "アウェイでクリーンシート（無失点）を達成した。"),
        ("It finished goalless, a real stalemate.", "0-0のスコアレスドロー、まさに膠着状態でした。"),
        ("We're deep into injury time now.", "もうインジャリータイム（負傷対応などによる追加時間）にかなり入っています。"),
        ("The fourth official's held up the board for four minutes of stoppage time.", "第4審判が4分間のストッページタイム（アディショナルタイム）のボードを掲げました。"),
        ("They've thrown away a two-goal lead.", "2点のリードを守り切れず、逃してしまった。"),
        # --- 実況の定番フレーズ ---
        ("What a strike!", "なんというシュートだ！"),
        ("He's through on goal!", "彼はゴール前に抜け出した！〔注: through on goal＝守備を突破し、キーパーと一対一の状況になること〕"),
        ("That's a stonewall penalty.", "あれは疑いようのないPKです。〔注: stonewall penalty＝誰の目にも明らかなPK〕"),
        ("He's been sent off for a second yellow card.", "彼は2枚目のイエローカードで退場になった。"),
        ("It's a straight red!", "一発退場（レッドカード）です！"),
        ("The referee's reaching for his pocket.", "レフェリーがポケットに手を伸ばしています（カードを出そうとしている）。"),
        ("VAR's having a look at this.", "VAR（ビデオ判定）がこのプレーを確認しています。"),
        ("The goal's been ruled out for offside.", "そのゴールはオフサイドで取り消されました。"),
        ("It's gone to a VAR review.", "VARレビューに入りました。"),
        ("That's been chalked off.", "そのゴールは（判定で）取り消されました。〔注: chalk off＝ゴールなどが判定によって無効になること〕"),
        ("He's been booked for a reckless challenge.", "彼は無謀なタックルでイエローカードを受けた。"),
        ("It's a game of two halves.", "前半と後半でまるで違う展開の試合です。〔注: サッカー実況の定番表現〕"),
        ("He's rattled the crossbar!", "クロスバーを叩いた！"),
        ("The keeper's pulled off a stunning save.", "キーパーが見事なセーブを見せた。"),
        ("It's in off the post!", "ポストに当たってゴールイン！"),
        ("He's buried it in the top corner.", "彼はゴール隅の高い位置に叩き込んだ。"),
        ("That's an absolute screamer from thirty yards!", "30ヤードからのとんでもないスーパーシュートだ！〔注: screamer＝豪快で見事な弾丸シュート〕"),
        ("It's squeaky bum time for the home fans.", "ホームのファンにとっては胃が痛くなるような終盤戦です。〔注: squeaky bum time＝シーズン終盤の緊迫した時期を指す英サッカー特有の表現〕"),
        ("The away goals rule used to decide ties like this, but it's been scrapped now.", "以前はこうした引き分けの場合アウェーゴールルールで決着がついていましたが、今は廃止されています。〔注: away goals rule＝2試合合計で同点の場合にアウェーでの得点を優先するルール。UEFAは2021年に廃止〕"),
        ("That's a hospital pass if ever I saw one.", "あれはまさに危険なパス（受け手が潰されかねないパス）でしたね。〔注: hospital pass＝受け手が激しいタックルを受けかねない、危険なタイミングのパス〕"),
    ],
    "サッカー・移籍市場": [
        ("He's completed a loan move until the end of the season.", "彼はシーズン終了までのローン移籍（期限付き移籍）を完了した。"),
        ("There's a release clause in his contract.", "彼の契約にはリリース条項（違約金条項）が含まれている。〔注: release clause＝規定の金額を払えば他クラブが選手を獲得できる契約条項〕"),
        ("He's due to have his medical tomorrow.", "彼は明日メディカルチェック（移籍前の健康診断）を受ける予定です。"),
        ("The club's unveiled their marquee signing.", "クラブは目玉となる新加入選手をお披露目した。〔注: unveil＝新加入選手を正式に発表・紹介すること〕"),
        ("They're in a real relegation battle with three games to go.", "残り3試合を残し、まさに残留争いの真っただ中にいる。"),
        ("It's shaping up to be a real top-four race.", "本当のトップ4争いになりそうな展開です。〔注: 主にチャンピオンズリーグ出場権をかけた上位4位以内の争い〕"),
        ("The transfer window slams shut at eleven o'clock tonight.", "移籍市場は今夜11時に締め切られます。"),
        ("He's put in a transfer request.", "彼は移籍を要望した。"),
        ("The move's gone through for an undisclosed fee.", "非公開の移籍金でその移籍が成立した。"),
        ("It's believed to be a club-record signing.", "クラブ史上最高額の獲得と見られている。"),
        ("He's out of contract at the end of the season.", "彼はシーズン終了で契約満了になる。"),
        ("They've triggered his release clause.", "彼らはリリース条項を発動した。"),
        ("The deal's subject to a medical and personal terms.", "その契約はメディカルチェックと個人条件（年俸交渉）合意が整うことが条件になっている。"),
        ("He's been strongly linked with a move to the Premier League.", "彼はプレミアリーグ移籍が強くうわさされている。"),
        ("The board's sanctioned a big-money move for the striker.", "取締役会はそのストライカー獲得への大型移籍を承認した。"),
        ("It's a permanent deal with an option to buy.", "買取オプション付きの完全移籍です。"),
        ("There's been no bids matching the club's valuation.", "クラブの希望額に見合うオファーはまだありません。"),
        ("The transfer's gone through right on deadline day.", "移籍市場の最終日ぎりぎりでその移籍が成立した。〔注: deadline day＝移籍市場最終日。争奪戦や土壇場の移籍が集中することで有名〕"),
    ],
    "サッカー・スタジアム観戦": [
        ("What time's kick-off?", "キックオフは何時ですか？"),
        ("We're in the away end today.", "今日はアウェイエンド（相手サポーター席）で観戦です。"),
        ("The atmosphere on the terraces was electric.", "テラス（立ち見席）の雰囲気は最高に盛り上がっていた。〔注: terraces＝伝統的な立ち見の観客席。現在多くのスタジアムは全席着席化されている〕"),
        ("Watch out for the ticket touts outside the ground.", "スタジアム外のダフ屋には気をつけて。〔注: ticket tout＝チケットを高額転売する業者・個人〕"),
        ("Have you got your season ticket sorted for next year?", "来シーズンのシーズンチケットはもう手配した？"),
        ("We're right up in the gods, at the back of the stand.", "スタンドの一番後ろ、かなり高い席です。〔注: up in the gods＝スタジアムの最上段付近の席を指すくだけた表現〕"),
        ("Let's grab a pie and a pint before kick-off.", "キックオフ前にパイとビールでも買っておこう。〔注: 英国のスタジアム観戦の定番〕"),
        ("The home end erupted when the winner went in.", "決勝点が決まった瞬間、ホームエンドが沸き返った。"),
        ("We got caught up in the crush leaving the ground.", "スタジアムを出るとき、人混みに巻き込まれてしまった。"),
        ("There's a real edge to the atmosphere between the two sets of fans.", "両サポーター間の空気にはピリピリした緊張感がある。"),
        ("The turnstiles opened an hour before kick-off.", "ターンスタイル（入場ゲート）はキックオフの1時間前に開いた。"),
        ("The away fans were in fine voice all match.", "アウェイサポーターは試合中ずっと声を張り上げていた。〔注: in fine voice＝声援が非常に盛んな様子〕"),
        ("It's all-seater now, you can't stand on the terraces anymore.", "今は全席着席制なので、もう立ち見はできません。〔注: all-seater＝立ち見席を廃止し全席着席にしたスタジアム〕"),
        ("We queued for ages just to get through the gate.", "ゲートを通るだけで、長時間並ばされた。"),
        ("Segregation's pretty tight for this one, it's a local derby.", "今回はダービーマッチなので、サポーターの分離がかなり厳重です。〔注: segregation＝対立するサポーター同士の衝突を防ぐための席・動線の分離〕"),
        ("We ended up watching it in the pub because tickets sold out in minutes.", "チケットが数分で売り切れたので、結局パブで観戦することになった。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("clean sheet", "クリーンシート（無失点試合）", "名詞", "The keeper kept a clean sheet in a hard-fought 1-0 win.", "サッカー", "700"),
    ("stoppage time", "ストッページタイム（アディショナルタイム）", "名詞", "The winning goal came deep into stoppage time.", "サッカー", "700"),
    ("offside trap", "オフサイドトラップ", "名詞", "The defence sprang the offside trap perfectly.", "サッカー", "800"),
    ("false nine", "フォルスナイン（偽9番）", "名詞", "He's been deployed as a false nine this season.", "サッカー", "900"),
    ("high press", "ハイプレス（高い位置からの守備）", "名詞", "Their high press forced a string of turnovers in the first half.", "サッカー", "800"),
    ("set piece", "セットプレー", "名詞", "They scored twice from set pieces in the first half.", "サッカー", "700"),
    ("VAR", "VAR（ビデオ判定システム）", "名詞", "VAR overturned the referee's original decision.", "サッカー", "600"),
    ("relegation", "降格", "名詞", "The club was fighting relegation right until the final day.", "サッカー", "700"),
    ("loan", "ローン移籍・期限付き移籍", "名詞", "He joined the club on a season-long loan.", "サッカー", "600"),
    ("release clause", "リリース条項（違約金条項）", "名詞", "His release clause is reportedly worth eighty million pounds.", "サッカー", "800"),
    ("medical", "メディカルチェック（移籍前の健康診断）", "名詞", "He passed his medical ahead of the move.", "サッカー", "600"),
    ("transfer window", "移籍市場（移籍が認められる期間）", "名詞", "The transfer window closes at the end of the month.", "サッカー", "700"),
    ("deadline day", "移籍市場最終日", "名詞", "Several clubs are still active on deadline day.", "サッカー", "700"),
    ("unveil", "（新加入選手などを）お披露目する", "動詞", "The club unveiled their new signing at a press conference.", "サッカー", "700"),
    ("terraces", "テラス（立ち見の観客席）", "名詞", "Fans used to stand on the terraces before all-seater stadiums.", "サッカー", "700"),
    ("ticket tout", "ダフ屋（チケット高額転売業者）", "名詞", "He bought his ticket from a tout outside the ground.", "サッカー", "800"),
    ("crossbar", "クロスバー", "名詞", "His shot cannoned off the crossbar.", "サッカー", "700"),
    ("screamer", "豪快なスーパーシュート", "名詞", "He scored an absolute screamer from outside the box.", "サッカー", "800"),
    ("stalemate", "膠着状態・スコアレスの引き分け", "名詞", "The match ended in a goalless stalemate.", "サッカー", "700"),
    ("derby", "ダービーマッチ（地元同士の対戦）", "名詞", "Sunday's local derby always draws a huge crowd.", "サッカー", "600"),
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
