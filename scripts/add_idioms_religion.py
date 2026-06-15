# ruff: noqa: E501
"""欧米人がよく使う慣用句の追加＋宗教フレーズのカテゴリ統合。著者は Claude
(app/OpenAI API は呼ばない)。english(小文字)で重複判定し、既存はスキップ。

やること:
1. 宗教系シーンを 1つの「宗教」に統合(キリスト教/ユダヤ教/仏教/イスラム教/
   宗教・古典)。ただし「宗教・古典」に紛れているシェイクスピア等の非宗教句は
   「名言・名台詞」へ退避してから統合する。
2. よく使う慣用句を追加。宗教的な祝福・聖句は scene="宗教"、一般の慣用句は
   scene="慣用句"。
3. レベルは別途 scripts/relevel_phrases.py で自動付与(宗教=800/慣用句=700)。

Run: python scripts/add_idioms_religion.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# 「宗教・古典」に入っているが宗教ではない句 → 名言・名台詞 へ退避
TO_QUOTES = [
    "To thine own self be true.",
    "Brevity is the soul of wit.",
    "All that glitters is not gold.",
]

# これらの scene を「宗教」に統合
MERGE_INTO_RELIGION = [
    "キリスト教", "ユダヤ教", "仏教", "イスラム教", "宗教・古典",
]

# 追加する宗教フレーズ (english, japanese)
RELIGION: list[tuple[str, str]] = [
    ("God bless you.", "神のご加護を・お大事に"),
    ("God bless America.", "神よ、アメリカに祝福を"),
    ("Bless your heart.", "なんていい人・かわいそうに(米南部)"),
    ("Thank God.", "ああよかった・ありがたい"),
    ("Thank heavens.", "ああ助かった・よかった"),
    ("Oh my God.", "なんてことだ・うわあ"),
    ("Oh my goodness.", "あらまあ・なんてこと(柔らかい)"),
    ("God forbid.", "そんなことありませんように"),
    ("Heaven forbid.", "まさか・とんでもない"),
    ("For God's sake.", "お願いだから・いいかげんにして"),
    ("For heaven's sake.", "頼むから・まったくもう"),
    ("God knows.", "神のみぞ知る・さっぱりわからない"),
    ("God only knows.", "神のみぞ知る"),
    ("Heaven knows.", "神のみぞ知る・誰にもわからない"),
    ("Godspeed.", "道中ご無事で・成功を祈る"),
    ("God willing.", "神の思し召しがあれば・うまくいけば"),
    ("Rest in peace.", "安らかに眠れ(R.I.P.)"),
    ("May he rest in peace.", "彼の冥福を祈ります"),
    ("Amen to that.", "まったく同感だ"),
    ("Praise the Lord.", "主をたたえよ・ありがたい"),
    ("The Lord works in mysterious ways.", "神の御業は計り知れない"),
    ("There but for the grace of God go I.", "一歩間違えば我が身だ"),
    ("Cleanliness is next to godliness.", "清潔は敬神に次ぐ美徳"),
    ("Bless you.", "お大事に(くしゃみの後に)"),
    ("Peace be with you.", "あなたに平安あれ"),
    ("In God we trust.", "我ら神を信ず"),
    ("Hallelujah.", "ハレルヤ・神をほめたたえよ"),
    ("So help me God.", "神に誓って(本当だ)"),
    ("Vengeance is mine, saith the Lord.", "復讐するは我にあり"),
    ("Man proposes, God disposes.", "計画は人、成敗は天"),
]

# 追加する一般慣用句 (english, japanese) ※既存と重複はスキップ
IDIOMS: list[tuple[str, str]] = [
    ("The best of both worlds.", "両方のいいとこ取り"),
    ("When pigs fly.", "ありえない・絶対にない"),
    ("Add insult to injury.", "泣きっ面に蜂・さらに悪化させる"),
    ("Barking up the wrong tree.", "見当違いをする"),
    ("A penny for your thoughts.", "何を考えているの?"),
    ("Better late than never.", "遅くてもやらないよりまし"),
    ("Two heads are better than one.", "三人寄れば文殊の知恵"),
    ("Don't cry over spilled milk.", "覆水盆に返らず"),
    ("Get cold feet.", "怖気づく・尻込みする"),
    ("Hit the sack.", "寝る・床につく"),
    ("Pull someone's leg.", "(人を)からかう"),
    ("Cut corners.", "手を抜く・経費を切り詰める"),
    ("Sit on the fence.", "日和見する・態度を決めない"),
    ("Jump on the bandwagon.", "時流に乗る・便乗する"),
    ("Miss the boat.", "好機を逃す"),
    ("We're on the same page.", "認識が一致している"),
    ("Back to square one.", "振り出しに戻る"),
    ("A ballpark figure.", "おおよその数字"),
    ("Burning the candle at both ends.", "無理をして働きづめだ"),
    ("Go the whole nine yards.", "何から何まで・徹底的に"),
    ("Bend over backwards.", "精一杯がんばる・骨を折る"),
    ("Break the ice.", "場の緊張をほぐす"),
    ("Call the shots.", "采配を振る・仕切る"),
    ("Get the ball rolling.", "物事を始動させる"),
    ("We're in the same boat.", "同じ境遇だ"),
    ("Off the top of my head.", "とっさに思いつくと"),
    ("Out of the blue.", "突然・思いがけず"),
    ("Pull some strings.", "コネを使う・手を回す"),
    ("Can I take a rain check?", "また今度にしてもいい?"),
    ("We see eye to eye.", "意見が一致する"),
    ("Steal someone's thunder.", "手柄を横取りする・お株を奪う"),
    ("Take it with a grain of salt.", "話半分に聞く"),
    ("Tie the knot.", "結婚する"),
    ("It's still up in the air.", "まだ未定だ"),
    ("Wrap your head around it.", "それを理解する・のみ込む"),
    ("Long story short.", "手短に言うと"),
    ("It is what it is.", "仕方がない・そういうものだ"),
    ("No worries.", "気にしないで・問題ないよ"),
    ("My bad.", "ごめん、私のミス"),
    ("Fair enough.", "なるほど・了解"),
    ("Knock on wood.", "(縁起担ぎで)うまくいきますように"),
    ("Fingers crossed.", "幸運を祈る・うまくいくといいね"),
    ("Easy does it.", "落ち着いて・慎重に"),
    ("You can say that again.", "まったくその通り"),
    ("That rings a bell.", "心当たりがある・聞き覚えがある"),
    ("It's a small world.", "世間は狭い"),
    ("The bottom line is this.", "要するに・肝心なのは"),
    ("Last but not least.", "最後に大事なことを言うと"),
    ("Speak of the devil.", "うわさをすれば(影)"),
    ("Let's play devil's advocate.", "あえて反対の立場で論じよう"),
    ("Don't be holier than thou.", "聖人ぶるな・独善的になるな"),
    ("It was an act of God.", "不可抗力・天災だった"),
    ("It's a blessing and a curse.", "良し悪しの両面がある"),
]


def main() -> int:
    with db() as conn:
        # 1) シェイクスピア等を名言へ退避
        moved_q = 0
        for en in TO_QUOTES:
            cur = conn.execute(
                "UPDATE phrases SET scene='名言・名台詞' "
                "WHERE english=? AND scene='宗教・古典'",
                (en,),
            )
            moved_q += cur.rowcount
        # 2) 宗教系シーンを「宗教」に統合
        qs = ",".join("?" for _ in MERGE_INTO_RELIGION)
        cur = conn.execute(
            f"UPDATE phrases SET scene='宗教' WHERE scene IN ({qs})",
            MERGE_INTO_RELIGION,
        )
        merged = cur.rowcount
        # 3) 追加(重複スキップ)
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        added_r = added_i = 0
        for en, ja in RELIGION:
            if en.lower() in existing:
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, '宗教')",
                (en, ja),
            )
            existing.add(en.lower())
            added_r += 1
        for en, ja in IDIOMS:
            if en.lower() in existing:
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, '慣用句')",
                (en, ja),
            )
            existing.add(en.lower())
            added_i += 1
    print(f"名言へ退避: {moved_q} / 宗教へ統合: {merged}")
    print(f"追加: 宗教 +{added_r} / 慣用句 +{added_i}")
    with db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0]
        rel = conn.execute(
            "SELECT COUNT(*) FROM phrases WHERE scene='宗教'").fetchone()[0]
    print(f"フレーズ総数: {total} / scene=宗教: {rel}")
    print("→ 次に: python scripts/relevel_phrases.py でレベル付与")
    return 0


if __name__ == "__main__":
    sys.exit(main())
