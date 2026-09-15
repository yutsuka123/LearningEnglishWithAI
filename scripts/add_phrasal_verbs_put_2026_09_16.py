# ruff: noqa: E501
"""句動詞(put)を追加(2026-09-16)。

`scripts/add_phrasal_verbs_take_give_get_2026_09_09.py`(take/give/get)の
続き。当時のコメント「将来put/come/go等へ拡張する余地を残す設計」通り、
put単体で新しい分野「句動詞(put)」を追加する(app/services/taxonomy.py参照)。

基礎動詞72語拡充(scripts/add_basic_verbs_2026_09_15.py)でput自体(多義語
としての基本語義)は既に登録済みだが、put on/off/up等の句動詞は別語として
未登録だったため、take/give/getと同じ設計(同じ英語表現でも意味ごとに
別レコード・(english, japanese)完全一致で重複判定)で追加する。

No app / OpenAI API calls — 手書きデータをSQLiteへ直接投入。

Run:  python scripts/add_phrasal_verbs_put_2026_09_16.py

仕上げ: 音声生成が必要(build_audio.py)。levelは目安値を直接指定。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "句動詞(put)"

# (english, japanese, example, example_ja, explanation, level)
WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("put on", "着る・身につける",
     "She put on her coat before going out.", "彼女は出かける前にコートを着た。",
     "反対は take off。「（電気・音楽などを）つける」（put on the light）の意味もある。",
     "300"),
    ("put off", "延期する",
     "We had to put off the meeting until next week.", "会議を来週まで延期しなければならなかった。",
     "後ろは名詞または動名詞（put off doing）。「（人の）気をそぐ・嫌にさせる」の意味もある。",
     "450"),
    ("put up", "泊める（人を）",
     "Can you put me up for the night?", "一晩泊めてもらえますか。",
     "「（テント・看板・建物などを）設置する」の意味もある（put up a tent / a poster）。",
     "500"),
    ("put up with", "我慢する",
     "I can't put up with his rudeness anymore.", "彼の無礼さにこれ以上我慢できない。",
     "後ろは名詞または動名詞。put と up with の間に人を挟めない点に注意。",
     "500"),
    ("put away", "片付ける",
     "Please put away your toys before dinner.", "夕食の前におもちゃを片付けてください。",
     "口語で「（大量に）平らげる」の意味もある（He can really put away a pizza.）。",
     "350"),
    ("put out", "消す（火・タバコなどを）",
     "Firefighters put out the blaze in two hours.", "消防士たちは2時間でその火を消した。",
     "「（人に）迷惑・不便をかける」（I don't want to put you out.）の意味もある。",
     "450"),
    ("put through", "つなぐ（電話を）",
     "Could you put me through to the manager?", "マネージャーにおつなぎいただけますか。",
     "「（つらい経験を）経験させる」（put someone through a lot）の意味もある。",
     "550"),
    ("put together", "組み立てる・まとめる",
     "It took us an hour to put the shelf together.", "その棚を組み立てるのに1時間かかった。",
     "反対は take apart。「（資料・計画を）まとめる」にも使う（put together a report）。",
     "450"),
    ("put down", "下に置く",
     "He put down his bag and sat on the sofa.", "彼はかばんを下に置いてソファに座った。",
     "「（人を）けなす」（Stop putting me down.）、「（動物を）安楽死させる」の意味もある。",
     "400"),
    ("put forward", "提案する",
     "She put forward a new idea at the meeting.", "彼女は会議で新しいアイデアを提案した。",
     "put forward a proposal / a candidate の形でよく使う。",
     "550"),
    ("put across", "伝える・理解させる",
     "He struggled to put his point across clearly.", "彼は自分の考えをはっきり伝えるのに苦労した。",
     "put an idea across が典型的な形。put over とも言うがやや古風。",
     "600"),
    ("put aside", "取っておく・脇に置く",
     "Let's put aside our differences and work together.", "意見の違いは脇に置いて一緒に取り組みましょう。",
     "「（お金を）貯める」の意味もある（put aside money for a trip）。",
     "500"),
    ("put back", "元に戻す",
     "Please put the book back on the shelf.", "その本を棚に戻してください。",
     "「（予定・時計を）遅らせる」の意味もある（The clocks go back in autumn.）。",
     "350"),
    ("put in", "申し込む・申請する",
     "He put in an application for the new position.", "彼はその新しいポジションに応募した。",
     "「（時間・労力を）費やす」（put in a lot of effort）の意味も頻出。",
     "500"),
    ("put down to", "（～のせいだと）考える",
     "She put her success down to hard work.", "彼女は自分の成功を努力のおかげだと考えた。",
     "put A down to B で「AをBのせいだと考える」。",
     "600"),
]


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
                (english, japanese, "句動詞", example, DOMAIN, level,
                 json.dumps(detail, ensure_ascii=False)),
            )
            existing.add(key)
            inserted += 1
    print(f"inserted={inserted} skipped(dup)={skipped} total_source={len(WORDS)}")


if __name__ == "__main__":
    main()
