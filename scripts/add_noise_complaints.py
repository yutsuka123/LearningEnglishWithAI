# ruff: noqa: E501  (data-heavy seed script: long phrase lines are fine)
"""Add NOISE-COMPLAINT (near neighbors) phrases, authored by Claude
(2026-08-06・ユーザー要望: 「近隣・騒音への抗議」という新規シーンを追加。
仕事や店員相手のクレームではなく、隣人・上階の住人・同居人・ホテルの
隣室・パーティーの騒音など、プライベートな対人関係での騒音・迷惑行為
への抗議・注意の英語表現がほしい、という依頼).

app/services/taxonomy.py の PHRASE_CATEGORIES["対人コミュニケーション"]
には、ほめる/注意する系のシーン("職場で注意する英語(部下・後輩・同僚)",
"子供を注意する英語", "ペットを注意する英語" など)が並んでいるが、
「近隣住民同士の騒音トラブル」に特化したシーンはまだ無かった。
このスクリプトは phrases テーブルに scene='近隣・騒音への抗議' という
新規シーンで、以下のニュアンスの表現を追加する:

- 「すみませんが、少し音を小さくしていただけますか」のような丁寧な依頼
- 「夜中にうるさくて眠れません」のような具体的な状況説明
- 「もう11時を過ぎています」のような時間帯を根拠にした指摘
- 「これで3回目です」のように繰り返しを指摘する強めの表現
- 「管理会社に連絡せざるを得ません」のような最終警告
- 逆に、注意された側が使う謝罪・言い訳・改善の約束の表現(会話の
  両側があると学習に役立つため少し含めている)

words の追加は無し(既存語彙で十分カバーできるため)。phrases のみ、
約28件。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_noise_complaints.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

PHRASES: list[tuple[str, str]] = [
    ("I'm sorry to bother you, but could you please turn the music down a little?", "すみませんが、音楽を少し小さくしていただけますか？"),
    ("Could you keep it down? It's pretty late.", "静かにしていただけますか？もうかなり遅い時間なので。"),
    ("I can't sleep because of the noise from your apartment.", "お宅からの物音がうるさくて眠れません。"),
    ("It's already past 11 pm, so could you lower the volume?", "もう夜11時を過ぎているので、音量を下げていただけますか？"),
    ("This is the third time this has happened.", "これで3回目です。"),
    ("If this keeps happening, I'll have to contact the management company.", "これが続くようなら、管理会社に連絡せざるを得ません。"),
    ("We can hear every footstep from upstairs.", "上の階の足音が全部聞こえてきます。"),
    ("Would you mind not running the washing machine so late at night?", "夜遅くに洗濯機を回さないでいただけますか？"),
    ("The walls here are pretty thin, so please be mindful of the noise.", "ここは壁が薄いので、物音に気を付けていただけると助かります。"),
    ("Sorry, we didn't realize it was so loud.", "すみません、そんなに大きい音だとは気づきませんでした。"),
    ("We'll try to keep it down from now on.", "これからは静かにするよう気を付けます。"),
    ("I apologize for the noise last night — we had some friends over.", "昨夜はうるさくしてすみません。友人を呼んでいたんです。"),
    ("Could you please ask your guests to lower their voices?", "お客様たちに声を小さくするよう言っていただけますか？"),
    ("The noise from your party woke up my kids.", "そちらのパーティーの音で子供が起きてしまいました。"),
    ("I understand it's the weekend, but some of us have to work early.", "週末なのは分かりますが、早くに仕事がある人もいるんです。"),
    ("Do you think you could move the furniture around during the day instead?", "家具を動かすのは昼間にしていただけませんか？"),
    ("I hate to complain, but the noise has been going on for hours.", "苦情を言いたくはないのですが、もう何時間も音が続いています。"),
    ("Quiet hours start at 10 pm in this building.", "この建物では夜10時から静粛時間になります。"),
    ("Next time, please give us a heads-up if you're having a party.", "次回パーティーをする際は、事前に一言いただけると助かります。"),
    ("I'm not trying to be difficult, I just really need to sleep.", "うるさく言うつもりはないのですが、本当に眠らなければならないんです。"),
    ("We'll turn it down right away — sorry about that.", "すぐに音量を下げます。申し訳ありません。"),
    ("It won't happen again.", "もう二度としません。"),
    ("Could you let your dog know it's a bit loud? The barking keeps waking us up.", "ちょっと音が大きいので、ワンちゃんに伝えていただけますか？鳴き声で何度も起こされてしまうんです。"),
    ("I know these walls aren't very soundproof, so I'll try to be more careful.", "この壁があまり防音でないのは分かっているので、もっと気を付けるようにします。"),
    ("If it happens again, I'm afraid I'll need to file a formal complaint.", "また同じことがあれば、正式に苦情を申し立てざるを得ません。"),
    ("Is everything okay? I heard some loud banging from your room earlier.", "大丈夫ですか？先ほどお部屋から大きな物音が聞こえたので。"),
    ("Sorry, we were just moving some boxes — we'll be done soon.", "すみません、ちょっと荷物を動かしていて。もうすぐ終わります。"),
    ("We've already asked a few times about the noise.", "騒音については、もう何度かお願いしています。"),
    ("I don't want to cause trouble, but this has been an ongoing issue.", "揉め事にしたくはないのですが、これはずっと続いている問題です。"),
    ("Could you please use headphones if you're going to watch TV this late?", "こんな遅くにテレビを見るなら、ヘッドホンをつけていただけますか？"),
    ("We're staying right next door — could you keep it down a bit?", "お隣に泊まっているのですが、少し静かにしていただけますか？"),
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
                "VALUES (?, ?, '近隣・騒音への抗議')",
                (en, ja),
            )
            p_existing.add(en.lower())
            p_added += 1

    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
