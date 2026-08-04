# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for F1 / MOTORSPORT ENGLISH, authored by Claude.

Focus (フレーズ集の手薄な領域を補強): F1・モータースポーツ特有の英語。
既存の「スポーツ」ドメインには referee/coach/tournament/marathon/penalty/
podium/doping など一般的なスポーツ語彙は既にあるが、F1固有の語彙・言い回しは
一つもカバーされていなかった。本バッチでは以下を体系的に強化する:

  - レースウィークの語彙（フリー走行/予選/パルクフェルメ/グリッド降格/
    ポールポジション）
  - ピットストップ・戦略用語（アンダーカット/オーバーカット/box box box/
    タイヤコンパウンド〔ソフト・ミディアム・ハード・ウェット・
    インターミディエイト〕/劣化/DRS/セーフティカー/バーチャルセーフティ
    カー/赤旗）
  - チーム無線特有の register（エンジニアとドライバーの間で交わされる、
    短く専門用語だらけの指示・報告フレーズ）
  - 実況・観戦者がよく耳にする語彙（表彰台/コンストラクターズ選手権/
    フォーメーションラップ/シケイン/エイペックス）
  - 現地観戦のための表現（サーキットへのアクセス、ゲート/座席/持ち込み
    制限、チームグッズ購入、ファンゾーン、レース後の渋滞対応）

Sky Sports F1 や Drive to Survive のような、実際のF1メディア・ファンの
話し方（乾いた技術用語集ではなく、生きた実況・会話の register）に忠実に
なるよう心がけた。丁寧度や専門用語の意味が分かるよう、日本語訳に〔注〕を
付した。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_f1_motorsport.py
      python scripts/add_f1_motorsport.py --missing-words   # report only

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
    "モータースポーツ・F1": [
        # --- レースウィーク：走行フォーマット ---
        ("Free practice starts on Friday morning.", "フリー走行（プラクティス）は金曜の朝に始まります。"),
        ("Qualifying is split into three sessions: Q1, Q2 and Q3.", "予選はQ1・Q2・Q3の3セッションに分かれています。"),
        ("She grabbed pole position by just two-tenths of a second.", "彼女はわずか0.2秒差でポールポジション（予選1位）を獲得した。"),
        ("He'll start from the back of the grid after the engine penalty.", "エンジン交換によるグリッド降格ペナルティで、彼は最後尾スタートになる。"),
        ("The car has to go straight into parc fermé after qualifying.", "予選後、車はそのままパルクフェルメへ運ばれる。〔注: parc fermé＝予選後にセットアップ変更が原則禁止される車両管理区画〕"),
        ("All the drivers complete a formation lap before the lights go out.", "スタート信号が消える前に、全ドライバーがフォーメーションラップ（隊列周回）を行う。"),
        ("It's lights out and away we go!", "シグナル消灯、レーススタートです！〔注: F1中継の定番実況フレーズ〕"),
        ("He made a great start and gained three places into Turn 1.", "彼は好スタートを切り、1コーナーまでに3台オーバーテイクした。"),
        # --- ピットストップ・戦略 ---
        ("The strategy team is looking at a one-stop versus a two-stop race.", "戦略チームは1ストップと2ストップのどちらにするか検討している。"),
        ("They pitted early to try an undercut on the car ahead.", "前を行く車にアンダーカットを仕掛けようと、早めにピットインした。〔注: undercut＝先にタイヤ交換し、新品タイヤの速さで前車を逆転する戦略〕"),
        ("The overcut worked because the new tyres came in just as the track opened up.", "コースが空いたタイミングで新品タイヤが効き、オーバーカットが決まった。〔注: overcut＝ピットインを遅らせ、長く走ることで有利を得る戦略〕"),
        # --- タイヤ ---
        ("Which tyre compound are they starting on, the soft or the medium?", "スタートのタイヤコンパウンドはソフトですか、ミディアムですか？"),
        ("The soft tyres offer more grip but degrade faster than the hards.", "ソフトタイヤはグリップが高い分、ハードタイヤより劣化（デグラデーション）が早い。"),
        ("It started to rain, so everyone switched to intermediates.", "雨が降り始めたので、みんなインターミディエイトタイヤに履き替えた。〔注: 小雨〜中程度の雨用タイヤ。土砂降りでは溝がさらに深いwet（フルウェット）を使う〕"),
        ("Tyre degradation is the big talking point this weekend.", "今週末はタイヤの劣化（デグラデーション）が大きな話題になっている。"),
        # --- DRS・セーフティカー・赤旗 ---
        ("He's got DRS open on the straight and he's right on the back of the car ahead.", "ストレートでDRSを開いていて、前の車にぴったり詰め寄っている。〔注: DRS＝Drag Reduction System。後方1秒以内で使用できる可変リアウィング〕"),
        ("The gap is within one second, so DRS is enabled.", "差が1秒以内なのでDRSが有効になっている。"),
        ("The safety car is out after contact between two cars.", "2台の接触を受けてセーフティカーが導入された。"),
        ("It's a virtual safety car, not a full safety car.", "これはバーチャルセーフティカーで、実車が出るセーフティカーではない。〔注: VSC＝コース上に危険がある際、全車に規定の減速タイムを守らせる制度〕"),
        ("The race has been red-flagged after a huge crash.", "大クラッシュにより赤旗中断となった。"),
        ("The stewards handed him a five-second time penalty.", "審判団（ステュワード）は彼に5秒のタイムペナルティを科した。"),
        # --- 実況・結果 ---
        ("He crossed the line to take the checkered flag.", "彼はチェッカーフラッグを受けてゴールした。"),
        ("It's a hard-fought podium finish for the home favorite.", "地元の人気ドライバーが激戦の末、表彰台に立った。"),
        ("They've locked out the front row in qualifying.", "予選でフロントロー（1・2番グリッド）を独占した。"),
        ("The team is fighting for the constructors' championship.", "チームはコンストラクターズ選手権（チーム部門）を争っている。"),
        ("He locked up and ran straight through the chicane.", "彼はロックアップ（タイヤをロックさせて）し、そのままシケインへ突っ込んでいった。"),
        ("You need to nail the apex to carry maximum speed onto the straight.", "ストレートへ最大速度を持ち込むには、エイペックス（コーナーの頂点）を正確に捉える必要がある。"),
    ],
    "モータースポーツ・無線交信": [
        # --- ピットイン指示 ---
        ("Box, box, box.", "ボックス、ボックス、ボックス。〔注: ピットインを指示する定番の無線コール。3回繰り返すのが伝統〕"),
        ("Copy that, boxing this lap.", "了解、このラップでピットインします。"),
        ("Box this lap for the hard tyre.", "このラップでピットイン、ハードタイヤに交換します。"),
        ("Confirm, hard tyre, box this lap.", "確認します、ハードタイヤ、このラップでピットイン。"),
        ("Car behind is faster, box this lap, box.", "後ろの車の方が速いです、このラップでピットイン、ボックス。"),
        # --- ペース・タイム指示 ---
        ("Push now, push, push.", "今プッシュ、プッシュ、プッシュ。〔注: 全力でペースを上げろという指示〕"),
        ("Gap to the car behind is one point two.", "後続車とのギャップは1.2秒です。"),
        ("You're losing time in sector two.", "セクター2でタイムを失っています。"),
        ("Plus point three on that lap.", "そのラップはプラス0.3秒でした。〔注: 目標タイムより0.3秒遅かったという意味〕"),
        ("We need to look after the tyres, target lap time is one thirty-two.", "タイヤをいたわる必要があります、目標ラップタイムは1分32秒です。"),
        ("Gap is coming down, he's within DRS range.", "差が縮まっています、彼はDRS圏内に入りました。"),
        # --- 戦略・車両状態の報告 ---
        ("We're going to plan B.", "プランBに切り替えます。"),
        ("Save fuel, lift and coast from Turn 8.", "燃料をセーブしてください、8コーナーからリフト＆コーストで。〔注: lift and coast＝早めにアクセルを離し惰性で走ることで燃料や部品への負担を抑える走法〕"),
        ("Deploy is not working, we have an issue with the battery.", "デプロイが機能していません、バッテリーに問題があります。〔注: deploy＝ハイブリッドシステムが蓄えた電力を放出すること〕"),
        ("Yellow flag, yellow flag, sector one.", "イエローフラッグ、イエローフラッグ、セクター1です。〔注: 追い越し禁止・減速を求める合図〕"),
        ("We are P3, gap to the leader is four seconds.", "現在3位です、トップとの差は4秒。"),
        # --- 無線チェック ---
        ("Radio check, how do you read?", "無線チェック、聞こえていますか？"),
        ("Copy, loud and clear.", "了解、クリアに聞こえています。"),
    ],
    "モータースポーツ・観戦": [
        # --- サーキット到着・入場 ---
        ("Which gate should we use to get into the circuit?", "サーキットに入るにはどのゲートを使えばいいですか？"),
        ("Gates open at eight, but the first session isn't until ten.", "ゲートは8時開場ですが、最初のセッションは10時からです。"),
        ("Do we need to print our tickets, or is mobile entry fine?", "チケットは印刷が必要ですか、それともモバイル入場で大丈夫ですか？"),
        ("Bags over a certain size aren't allowed inside.", "一定サイズを超えるバッグは持ち込み禁止です。"),
        ("You'll need to go through a security check at the gate.", "ゲートでセキュリティチェックを通る必要があります。"),
        # --- 座席・観戦エリア ---
        ("Where's the nearest grandstand to Turn 1?", "1コーナーに一番近いグランドスタンドはどこですか？"),
        ("We've got general admission tickets, so we can watch from the hill.", "自由席（指定席なし）チケットなので、丘の上から観戦できます。"),
        ("Bring ear plugs, it's really loud trackside.", "耳栓を持っていってください、コース脇はかなりの爆音です。"),
        # --- グッズ・ファンゾーン ---
        ("Let's grab some merchandise from the team store before the queue gets long.", "行列が長くなる前にチームストアでグッズを買いましょう。"),
        ("They sold out of that driver's cap already.", "あのドライバーのキャップはもう売り切れていました。"),
        ("There's a fan zone with driver appearances and simulators.", "ドライバー登場やシミュレーター体験があるファンゾーンがあります。"),
        ("We managed to catch the pit walk on Thursday.", "木曜のピットウォークに間に合いました。〔注: pit walk＝一般ファンがピットレーンを間近で見学できるイベント〕"),
        # --- 観戦体験 ---
        ("Let's head to our seats early to catch the support races too.", "前座レースも見られるように早めに席に着きましょう。"),
        ("Did you see the fly-past before the anthem?", "国歌の前のフライパスト見ましたか？〔注: fly-past＝式典で行われる航空機の祝賀飛行〕"),
        ("The atmosphere in the grandstand was electric during the last lap.", "最終ラップのグランドスタンドの熱狂はすごかった。"),
        ("Let's stay for the podium ceremony before we leave.", "帰る前に表彰式まで見ていきましょう。"),
        # --- 帰り・渋滞 ---
        ("The traffic getting out of the circuit was brutal.", "サーキットから出るときの渋滞はひどかった。"),
        ("It took us over two hours just to get out of the car park.", "駐車場を出るだけで2時間以上かかった。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("pole position", "ポールポジション（予選最速のスタート位置）", "名詞", "She started the race from pole position.", "モータースポーツ", "700"),
    ("grid penalty", "グリッド降格ペナルティ", "名詞", "He got a five-place grid penalty for an engine change.", "モータースポーツ", "800"),
    ("qualifying", "予選", "名詞", "Qualifying decides the starting grid for Sunday's race.", "モータースポーツ", "600"),
    ("parc fermé", "パルクフェルメ（予選後に車両規則が固定される管理区画）", "名詞", "The car has been in parc fermé since qualifying ended.", "モータースポーツ", "900"),
    ("undercut", "アンダーカットする（先にピットインし新品タイヤの速さで逆転を狙う）", "動詞", "They tried to undercut their rival by pitting one lap early.", "モータースポーツ", "800"),
    ("overcut", "オーバーカット（ピットインを遅らせて有利を得る戦略）", "名詞", "The strategy worked out perfectly thanks to a clever overcut.", "モータースポーツ", "900"),
    ("tyre compound", "タイヤコンパウンド（タイヤの配合種別）", "名詞", "Choosing the right tyre compound is key to race strategy.", "モータースポーツ", "700"),
    ("degradation", "（タイヤなどの）劣化", "名詞", "Tyre degradation was much higher than expected on this track.", "モータースポーツ", "800"),
    ("DRS", "DRS（可変リアウィングによる追い越し支援装置）", "名詞", "He opened the DRS and blew past the car ahead on the straight.", "モータースポーツ", "700"),
    ("safety car", "セーフティカー", "名詞", "The safety car came out after the crash at Turn 3.", "モータースポーツ", "600"),
    ("virtual safety car", "バーチャルセーフティカー", "名詞", "Under the virtual safety car, drivers must keep to a delta time.", "モータースポーツ", "800"),
    ("red flag", "赤旗（レース中断）", "名詞", "The race was stopped with a red flag due to heavy rain.", "モータースポーツ", "600"),
    ("formation lap", "フォーメーションラップ（隊列周回）", "名詞", "All the cars complete a formation lap before the start.", "モータースポーツ", "700"),
    ("chicane", "シケイン（S字状の減速コーナー）", "名詞", "He locked up and went straight through the chicane.", "モータースポーツ", "800"),
    ("apex", "エイペックス（コーナーの頂点、最も内側を通る点）", "名詞", "You need to hit the apex to carry maximum speed through the corner.", "モータースポーツ", "800"),
    ("constructor", "コンストラクター（車体を製造・運営するチーム）", "名詞", "The team is leading the constructors' championship.", "モータースポーツ", "700"),
    ("pit stop", "ピットストップ（タイヤ交換などのための短時間の停止）", "名詞", "A modern pit stop takes under three seconds.", "モータースポーツ", "600"),
    ("slipstream", "スリップストリーム（前車の後方にできる空気抵抗の少ない領域）", "名詞", "He used the slipstream to slingshot past on the straight.", "モータースポーツ", "800"),
    ("downforce", "ダウンフォース（車体を路面に押し付ける空力的な力）", "名詞", "More downforce means more grip but less top speed.", "モータースポーツ", "800"),
    ("grandstand", "グランドスタンド（コース沿いの観客席）", "名詞", "We booked seats in the grandstand overlooking the final corner.", "モータースポーツ", "600"),
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
