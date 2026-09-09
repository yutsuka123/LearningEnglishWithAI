# ruff: noqa: E501
"""句動詞(phrasal verb)を新規テーマとして追加(2026-09-09・ユーザー指示)。

基本動詞take/give/getそれぞれについて、前置詞/副詞との組み合わせで
意味が大きく変わる句動詞を収録する(take off=離陸する/脱ぐ、等)。
「多義語」(bank=銀行/土手のように1つの綴りが文脈で全く異なる意味を
持つもの)とは別カテゴリとして扱う方針(ユーザー指示・別スクリプトで対応)。

大分類は既存の「英語表現」(和製英語・口語等と同じ「英語表現のニュアンス」
系)に合流させ、分野は基本動詞ごとに分ける(句動詞(take)/句動詞(give)/
句動詞(get)。将来put/come/go等へ拡張する余地を残す設計・
app/services/taxonomy.py参照)。

同じ英単語(例: take off)が複数の異なる意味を持つ場合は、意味ごとに
別レコードとして登録する(既存の`agent`(3件・意味ごとに別レコード)と
同じ設計)。重複チェックは(english, japanese)の完全一致で行う
(englishだけで弾くと同じ句動詞の別の意味を登録できなくなるため)。

内容はclaude-fable-5(Agent経由)が作成・自己レビュー済み。断定を避け、
米英差がある項目にはdetail(explanation)で言及している。

No app / OpenAI API calls — 手書きデータをSQLiteへ直接投入。

Run:  python scripts/add_phrasal_verbs_take_give_get_2026_09_09.py

仕上げ: 音声生成が必要(build_audio.py等)。levelは目安値を直接指定
(relevel.pyは未実行・既存のB24バッチと同じ運用)。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# (english, japanese, example, example_ja, explanation, level)
# domainは先頭の基本動詞から自動判定(verb_of参照)。
WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("take off", "離陸する（飛行機が）",
     "The plane took off an hour late.", "飛行機は1時間遅れて離陸した。",
     "比喩的に「（事業・人気などが）急に伸びる」の意味でも使う（Her business really took off.）。",
     "400"),
    ("take off", "脱ぐ（服・靴などを）",
     "Please take off your shoes at the door.", "玄関で靴を脱いでください。",
     "反対は put on。目的語が代名詞のときは take it off / take them off の語順になる。",
     "350"),
    ("take on", "引き受ける（仕事・責任などを）",
     "I can't take on any more projects this month.", "今月はこれ以上プロジェクトを引き受けられない。",
     "「（人を）雇う」（take on extra staff）、「（相手と）対戦する」（take on the champions）の意味もある。",
     "500"),
    ("take up", "始める（趣味・習い事などを）",
     "I took up yoga to deal with stress.", "ストレス対策にヨガを始めた。",
     "take up a hobby / a sport / an instrument の形が定番。",
     "450"),
    ("take up", "占める（場所・時間を）",
     "This old sofa takes up too much space.", "この古いソファは場所を取りすぎる。",
     "時間にも使う（It takes up a lot of my time.）。",
     "450"),
    ("take after", "似ている（親や親族に）",
     "Everyone says I take after my dad.", "みんな、私は父親似だと言う。",
     "外見にも性格にも使う。目的語を間に挟めない（× take him after）。",
     "500"),
    ("take in", "理解する・飲み込む（情報を）",
     "That was a lot of information to take in at once.", "一度に飲み込むには多すぎる情報量だった。",
     "「だます」（受け身 be taken in by ～ が多い）、「（人・動物を）家に引き取る」の意味もある。",
     "600"),
    ("take over", "引き継ぐ・支配権を握る（仕事・会社などを）",
     "Who will take over when the manager retires?", "部長が退職したら、誰が後を引き継ぐの？",
     "take over from ～ で「～から引き継ぐ」。会社の買収は名詞 takeover。",
     "550"),
    ("take out", "取り出す",
     "He took out his wallet and paid for the coffee.", "彼は財布を取り出してコーヒー代を払った。",
     "「（ローン・保険を）契約する」（take out a loan）も頻出。持ち帰り料理は名詞で米 takeout / 英 takeaway。",
     "400"),
    ("take out", "連れ出す（食事・デートなどに）",
     "I'm taking my parents out for dinner on Sunday.", "日曜日は両親を食事に連れて行く。",
     "take ～ out for dinner / to dinner のどちらも使う。",
     "400"),
    ("take back", "撤回する（発言を）",
     "I'm sorry, I take back what I said.", "ごめん、さっき言ったことは撤回するよ。",
     "「（買った物を店に）返品する」（take it back to the store）の意味もある。",
     "450"),
    ("take down", "書き留める",
     "Let me take down your phone number.", "電話番号を控えさせてください。",
     "「（飾り・テントなどを）取り外す・解体する」（take down the tent）の意味もよく使う。",
     "450"),
    ("take apart", "分解する",
     "He took the old radio apart to see how it worked.", "彼は仕組みを知るために古いラジオを分解した。",
     "反対は put together（組み立てる）。",
     "500"),
    ("take away", "取り上げる・奪う",
     "The teacher took away his phone during class.", "先生は授業中に彼のスマホを取り上げた。",
     "英では「（料理を）持ち帰る」の意味でも使う（Eat in or take away?）。米は For here or to go? と言う。名詞 takeaway は米英共通で「（会議などの）要点」。",
     "450"),
    ("take to", "好きになる・なつく",
     "The kids took to their new teacher right away.", "子どもたちはすぐに新しい先生になついた。",
     "take to doing で「～するのが習慣になる」（He took to walking every morning.）。",
     "600"),
    ("take someone up on", "（申し出・誘いに）応じる、お言葉に甘える",
     "I'll take you up on that offer.", "その申し出、お言葉に甘えます。",
     "人を間に挟む語順が必須（take + 人 + up on + 申し出）。",
     "650"),
    ("give up", "あきらめる",
     "Don't give up. You're almost there.", "あきらめないで、もう少しだよ。",
     "", "300"),
    ("give up", "やめる（習慣・嗜好品などを）",
     "He gave up smoking last year.", "彼は去年たばこをやめた。",
     "後ろは名詞または動名詞（give up drinking）。",
     "400"),
    ("give in", "屈する・折れる",
     "After hours of arguing, she finally gave in.", "何時間も言い争った末、彼女はついに折れた。",
     "英では「提出する」（give in your homework）の意味もある。米は hand in / turn in が普通。",
     "500"),
    ("give in to", "（誘惑・要求などに）負ける",
     "I gave in to temptation and ate the whole cake.", "誘惑に負けてケーキを丸ごと食べてしまった。",
     "", "550"),
    ("give away", "ただであげる・寄付する",
     "She gave away most of her old clothes.", "彼女は古い服のほとんどを人に譲った。",
     "", "400"),
    ("give away", "漏らす・ばらす（秘密などを）",
     "Don't give away the ending of the movie!", "映画の結末をばらさないで！",
     "give oneself away で「ぼろを出す」。名詞 giveaway は「景品・無料配布品」。",
     "500"),
    ("give out", "配る",
     "They were giving out free samples at the entrance.", "入り口で無料サンプルを配っていた。",
     "hand out とほぼ同義。",
     "400"),
    ("give out", "動かなくなる・尽きる（体力・機械などが）",
     "My knees gave out halfway through the marathon.", "マラソンの途中で膝が言うことを聞かなくなった。",
     "供給が「底をつく」意味でも使う（The water supply gave out.）。",
     "600"),
    ("give back", "返す",
     "Can you give me back my pen?", "ペンを返してくれる？",
     "give back to the community で「社会に恩返しをする」。",
     "350"),
    ("give off", "発する・放つ（におい・光・熱などを）",
     "These flowers give off a lovely scent at night.", "この花は夜になると素敵な香りを放つ。",
     "口語では give off a ～ vibe「～な雰囲気を醸し出す」もよく使う。",
     "550"),
    ("give up on", "見限る・見切りをつける（人・計画などに）",
     "Her teachers never gave up on her.", "先生たちは決して彼女を見限らなかった。",
     "", "550"),
    ("get over", "立ち直る・乗り越える（病気・ショックなどから）",
     "It took her months to get over the breakup.", "彼女が失恋から立ち直るのに何か月もかかった。",
     "I can't get over how ～ で「～が信じられない（驚き）」。",
     "500"),
    ("get through", "乗り切る・切り抜ける（つらい時期・仕事などを）",
     "I don't know how I got through that week.", "あの一週間をどう乗り切ったのか自分でも分からない。",
     "「電話がつながる」の意味も（I couldn't get through to him.）。",
     "550"),
    ("get away", "逃げる・その場を離れる",
     "The burglar got away before the police arrived.", "警察が到着する前に泥棒は逃げてしまった。",
     "「休暇で遠出する」の意味も（get away for the weekend）。",
     "450"),
    ("get away with", "（悪いことをしても）罰を免れる、うまく逃げおおせる",
     "He always gets away with being late.", "彼は遅刻してもいつもお咎めなしだ。",
     "", "550"),
    ("get along", "仲良くやる・うまくやっていく",
     "Do you get along with your coworkers?", "同僚とはうまくやっていますか？",
     "相手は get along with ～。英では get on (with) が同じ意味で一般的。",
     "450"),
    ("get by", "何とかやっていく・切り抜ける",
     "We don't earn much, but we get by.", "稼ぎは多くないけれど、何とかやっている。",
     "get by on ～ で「～でどうにか暮らす」（get by on a small salary）。",
     "500"),
    ("get down to", "本腰を入れて取りかかる",
     "OK, let's get down to business.", "さて、本題に入りましょう。",
     "get down to work / get down to business が定番。",
     "500"),
    ("get around", "移動する・あちこち回る",
     "It's easy to get around the city by bike.", "この街は自転車で移動しやすい。",
     "英では get round とも言う。「（規則などを）うまく回避する」の意味もある。",
     "450"),
    ("get around to", "ようやく～に手をつける",
     "I finally got around to cleaning the garage.", "やっとガレージの掃除に手をつけた。",
     "後ろは動名詞。英では get round to とも言う。",
     "600"),
    ("get up", "起きる（寝床から出る）",
     "I usually get up at six on weekdays.", "平日はたいてい6時に起きる。",
     "wake up は「目が覚める」、get up は「起き上がる」で区別する。",
     "300"),
    ("get on", "乗る（バス・電車・飛行機・自転車などに）",
     "We got on the wrong bus.", "間違ったバスに乗ってしまった。",
     "車・タクシーには get in を使う。英では get on (with) で「仲良くやる／続ける」の意味も。",
     "350"),
    ("get off", "降りる（バス・電車などから）",
     "Get off at the next stop and turn left.", "次の停留所で降りて左に曲がってください。",
     "車・タクシーからは get out of を使う。",
     "350"),
    ("get off", "退勤する・仕事を終える",
     "What time do you get off work?", "仕事は何時に終わるの？",
     "口語表現で、特に米でよく使う。英では finish work もよく使われる。",
     "450"),
    ("get into", "夢中になる・ハマる",
     "I got really into cooking last year.", "去年、料理にすっかりハマった。",
     "「（学校に）合格する」（get into college）、「（車に）乗り込む」の意味もある。",
     "450"),
    ("get out of", "（嫌なことを）免れる・逃れる",
     "He tried to get out of doing the dishes.", "彼は皿洗いから逃れようとした。",
     "後ろは名詞または動名詞。文字どおり「（車・建物から）出る」の意味でも使う。",
     "500"),
    ("get back to", "折り返し連絡する",
     "I'll get back to you by tomorrow.", "明日までに折り返しご連絡します。",
     "get back（to）は「戻る」が基本義（get back to work＝仕事に戻る）。",
     "400"),
]


def verb_of(english: str) -> str:
    for v in ("take", "give", "get"):
        if english.startswith(v):
            return v
    raise ValueError(f"unexpected headword: {english}")


def main() -> None:
    with db() as conn:
        existing = {
            (r["english"].lower(), r["japanese"])
            for r in conn.execute(
                "SELECT english, japanese FROM words").fetchall()
        }
        inserted = 0
        skipped = 0
        for english, japanese, example, example_ja, note, level in WORDS:
            key = (english.lower(), japanese)
            if key in existing:
                skipped += 1
                continue
            domain = f"句動詞({verb_of(english)})"
            detail = {
                "pos": "句動詞",
                "meanings": [japanese],
                "examples": [{"en": example, "ja": example_ja}],
            }
            if note:
                detail["explanation"] = note
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level, detail) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (english, japanese, "句動詞", example, domain, level,
                 json.dumps(detail, ensure_ascii=False)),
            )
            existing.add(key)
            inserted += 1
    print(f"inserted={inserted} skipped(dup)={skipped} total_source={len(WORDS)}")


if __name__ == "__main__":
    main()
