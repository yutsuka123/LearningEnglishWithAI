# ruff: noqa: E501  (data-heavy seed script: long phrase lines are fine)
"""Add "やんわり叱る英語" phrases, authored by Claude (2026-08-06・ユーザー
要望:「職場で上司・先輩・同僚が部下・後輩に対して、きつく叱るのではなく、
やんわりと・遠回しに・相手の面子を潰さずに注意・指摘する英語表現」).

既存の scene には "やんわり不満を伝える英語"(不満・愚痴寄り)、
"やんわり断る英語"(依頼を断る場面)、"職場で注意する英語(部下・後輩・同僚)"
(やや直接的な注意)などがあるが、いずれも「叱る」に特化した、クッション言葉
→事実確認→期待の共有→フォローという一連の流れを丁寧語で示すものではない。
このスクリプトは新規シーン "やんわり叱る英語" を追加し、以下のニュアンスを
持つフレーズを収録する:

- 「ちょっと確認したいんだけど」のようなクッション言葉から入る指摘
- 「次からは気をつけてもらえると助かります」のような柔らかい依頼形
- 「悪気はないと思うけど」で始める前置き
- 直接的な非難を避け、事実確認→期待の共有→今後への期待、という順で
  伝える言い回し
- 「みんな最初はそうだから」のようなフォローを添えるスタイル

domain/scene は phrases.scene = 'やんわり叱る英語'(新規)。
app/services/taxonomy.py の PHRASE_CATEGORIES["仕事・ビジネス"] には既に
"やんわり不満を伝える英語" "やんわり断る英語" が並んでおり、対応表に
シーン名を追記しなくても group_by_category() により自動的に「その他」に
分類されるため即座に壊れることはないが、taxonomy.py 側への追記は別途
検討する。

単語(words)は追加しない。フレーズのみ。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_gentle_scolding.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

PHRASES: list[tuple[str, str]] = [
    ("Can I check something with you real quick?", "ちょっと確認したいんだけど、いいかな？"),
    ("I noticed a small thing in the report — do you have a second?", "報告書でちょっと気になったことがあるんだけど、少し時間ある？"),
    ("I don't think you meant anything by it, but let's make sure it doesn't happen again.", "悪気はないと思うけど、次からは気をつけてもらえるかな。"),
    ("Just so we're on the same page going forward, could we double-check the numbers before sending?", "今後のために確認なんだけど、送る前に数字をダブルチェックしてもらえる？"),
    ("It might help to run this by someone before it goes out next time.", "次回は送る前に誰かに見てもらうといいかもね。"),
    ("No big deal, but let's tighten this up a bit for next time.", "大したことじゃないけど、次はもう少しきっちりやろうか。"),
    ("I get that things get busy — just wanted to flag this for next time.", "忙しいのは分かるんだけど、次に向けて一応伝えておきたくて。"),
    ("Everyone runs into this when they're starting out, so don't worry too much.", "最初はみんなこういうことがあるから、あまり気にしなくて大丈夫。"),
    ("Let's just make sure this doesn't slip through again, okay?", "これがまた漏れないように気をつけようね。"),
    ("I want to make sure we're aligned on this before it becomes a habit.", "癖になる前に、この点はすり合わせておきたいんだ。"),
    ("Would it be possible to get this done a little earlier next time?", "次回はもう少し早めに仕上げてもらうことってできるかな？"),
    ("I know you're doing your best — just a small tweak for next time.", "頑張ってくれているのは分かってる。次回はちょっとだけ調整してほしいんだ。"),
    ("Let's chat for a sec about how this went.", "これがどうだったか、ちょっと話そうか。"),
    ("This isn't a huge deal, but I wanted to mention it before it becomes a pattern.", "大したことではないんだけど、癖になる前に伝えておきたくて。"),
    ("Next time, it'd help a lot if you could loop me in earlier.", "次からはもっと早めに共有してもらえると助かる。"),
    ("I trust your judgment, but let's talk through this one.", "君の判断は信頼しているけど、これについては話し合っておこうか。"),
    ("Just something to keep in mind going forward.", "今後、頭の片隅に置いておいてほしいことがあって。"),
    ("Nothing to stress about, just wanted to touch base on this.", "気にしすぎなくていいから、この件について少し話したくて。"),
    ("It happens to everyone — let's just be more careful with this going forward.", "誰にでもあることだから、これからはもう少し気をつけていこう。"),
    ("Could we find a way to avoid this next time around?", "次回はこれを避ける方法を一緒に考えられるかな？"),
    ("I don't want to make a big thing of this, but it's worth a quick mention.", "大げさにしたくはないんだけど、ひとこと伝えておきたくて。"),
    ("You're clearly capable — I just want to make sure this doesn't become a habit.", "君の実力は分かっているから、これが癖にならないようにだけ気をつけてほしい。"),
    ("Let's use this as a learning moment rather than dwell on it.", "これはくよくよ考えるより、学びとして活かそうか。"),
    ("I'd love it if you could double-check this kind of thing before sending it out.", "こういうのは送る前にもう一度確認してもらえると嬉しいな。"),
    ("Just a heads-up for next time, nothing to worry about.", "次に向けての一言だから、心配しなくて大丈夫。"),
    ("Let's make sure we're on the same page so this doesn't come up again.", "これがまた起きないように、認識を合わせておこう。"),
    ("I appreciate the effort — let's just refine this piece a little.", "頑張ってくれてありがとう。ここだけ少し磨いていこうか。"),
    ("You're still getting the hang of this, so no worries — just keep this in mind next time.", "まだ慣れている途中だから心配ないよ。次はこれを意識してみて。"),
]


def main() -> int:
    with db() as conn:
        p_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in p_existing:
                p_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, 'やんわり叱る英語')",
                (en, ja),
            )
            p_existing.add(en.lower())
            p_added += 1

    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
