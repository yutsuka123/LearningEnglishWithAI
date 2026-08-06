# ruff: noqa: E501  (data-heavy seed script: long phrase lines are fine)
"""Add MOVIE-GENRE PHRASES (映画文学芸術 大カテゴリの第一弾), authored by Claude
(2026-08-06・ユーザー要望: 「フレーズは、映画文学芸術 大カテゴリつくって
映画、文学、舞台 などとし、映画できく台詞など映画をみるためのフレーズを
充実させたい」「sf、ホラー、恋愛、ドラマ、サスペンス、他 映画のフレーズ」).

このスクリプトは「映画文学芸術」大カテゴリのうち、まず「映画」ジャンル別の
フレーズを5シーン投入する:

- SF映画のフレーズ  — 宇宙船・エイリアン・タイムトラベル・AI・未来社会
- ホラー映画のフレーズ — 緊迫感・恐怖描写・警告・「逃げろ」等
- 恋愛映画のフレーズ — 告白・すれ違い・再会・別れ
- ドラマ映画のフレーズ — 人間関係の葛藤・成長・和解
- サスペンス映画のフレーズ — 追跡・裏切り・真相解明・緊迫した対峙

【著作権への配慮】
実在の映画からの台詞そのものの直接引用は一切行っていない。各ジャンルで
「典型的に使われがちな言い回し・決まり文句のパターン」を参考に、すべて
オリジナルの例文として書き下ろしている。特定の作品名・キャラクター名・
実在の台詞の一字一句の引用は含まない。英語(en)は各ジャンルの雰囲気を
出しつつ映画で実際に聞かれそうな自然な英語、日本語訳(ja)は字幕調の
自然な日本語とした。

単語(words)は追加せず、phrases のみを追加する。scene は新規5種類
(上記)で、既存の '名言・名台詞'(127件, 出典を問わない名言集)や
'恋愛'(15件, 映画に限らない日常の恋愛フレーズ)とは重複しない、映画
ジャンル特化のフレーズ集として独立させた。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_movie_phrases_1.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- phrases: scene -> [(english, japanese)] --------------------------------

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "SF映画のフレーズ": [
        ("We don't have much time. We need to act now.", "時間がない。今すぐ行動しなければ。"),
        ("This goes beyond anything science has ever explained.", "これは科学がこれまで説明してきた範囲を超えている。"),
        ("The ship's systems are failing one by one.", "船のシステムが次々と機能を失っている。"),
        ("If we don't stabilize the reactor, we won't survive re-entry.", "反応炉を安定させなければ、大気圏再突入を生き延びられない。"),
        ("Something out there is watching us.", "何かが外からこちらを見ている。"),
        ("It's not from this planet. I'm sure of it.", "これはこの星のものじゃない。確信している。"),
        ("The signal is coming from somewhere that shouldn't exist.", "その信号は、存在するはずのない場所から発信されている。"),
        ("We've opened a door we can't close again.", "私たちは、二度と閉じられない扉を開けてしまった。"),
        ("Time isn't a straight line. Not anymore.", "時間はもう一直線ではない。"),
        ("If I go back now, I might erase everything we fought for.", "今戻れば、私たちが戦って手に入れたすべてが消えるかもしれない。"),
        ("The future isn't fixed. We can still change it.", "未来は決まっていない。まだ変えられる。"),
        ("This artificial intelligence has started making its own decisions.", "このAIは自分自身で判断を下し始めている。"),
        ("It was never designed to feel anything. And yet, here we are.", "これは何かを感じるようには作られていなかった。それなのに、こうなっている。"),
        ("Humanity is not the only intelligence in this universe.", "人類はこの宇宙で唯一の知的生命体ではない。"),
        ("We came in peace. That doesn't mean they did.", "私たちは平和のために来た。だが相手もそうとは限らない。"),
        ("The last transmission just went silent.", "最後の通信がふいに途絶えた。"),
        ("In this future, there's no going back to how things were.", "この未来では、もう元の世界には戻れない。"),
        ("Every choice we make now echoes a hundred years from now.", "今の一つひとつの選択が、百年後に響く。"),
        ("The machines were supposed to serve us. That's not what's happening anymore.", "機械は我々に仕えるはずだった。だがもうそうではない。"),
        ("We're not alone out here. We never were.", "私たちはこの宇宙で独りじゃない。最初からずっと。"),
        ("Prepare for atmospheric entry. This is going to be rough.", "大気圏突入に備えろ。かなり揺れるぞ。"),
    ],
    "ホラー映画のフレーズ": [
        ("Don't go down there. Please, just don't.", "そこには行かないで。お願いだから。"),
        ("Something's in the house with us.", "何かがこの家の中に私たちと一緒にいる。"),
        ("We have to get out of here. Now.", "ここから出なきゃ。今すぐに。"),
        ("Whatever you do, don't look behind you.", "何があっても、絶対に後ろを振り返らないで。"),
        ("It's not going to stop until we're all gone.", "私たち全員がいなくなるまで、それは止まらない。"),
        ("I heard something moving upstairs.", "二階で何かが動く音が聞こえた。"),
        ("Lock the door. Lock it and don't open it for anyone.", "ドアに鍵をかけて。誰が来ても絶対に開けないで。"),
        ("This house has a history none of us know about.", "この家には私たちの知らない過去がある。"),
        ("Run. Don't look back, just run.", "逃げて。振り返らずに、ただ走って。"),
        ("The lights keep going out on their own.", "明かりが勝手に消え続けている。"),
        ("Something followed us back from that place.", "あの場所から、何かが私たちについてきた。"),
        ("We shouldn't have come here.", "私たちはここに来るべきじゃなかった。"),
        ("It knows we're here. It's just waiting.", "あれは私たちがここにいるのを知っている。ただ待っているだけだ。"),
        ("I can feel it watching, even when I can't see it.", "姿が見えなくても、見られているのを感じる。"),
        ("There's no signal out here. No one's coming to help us.", "ここは電波が通じない。誰も助けに来てくれない。"),
        ("Whatever's in the basement, we're not going down there.", "地下室に何がいようと、私たちは絶対に降りない。"),
        ("You hear that? That's not the wind.", "聞こえる? あれは風の音じゃない。"),
        ("The last thing she said was that it was already too late.", "彼女が最後に言ったのは、もう手遅れだということだった。"),
        ("It only comes out when the lights go off.", "それは明かりが消えたときにしか現れない。"),
        ("We need to stay together. No matter what happens.", "何があっても、離れずにいましょう。"),
        ("Something's wrong. I can feel it in my bones.", "何かがおかしい。骨の髄まで感じる。"),
    ],
    "恋愛映画のフレーズ": [
        ("I've been in love with you since the day we met.", "出会ったあの日から、ずっとあなたを愛している。"),
        ("I never stopped thinking about you, not even for a day.", "一日たりとも、あなたのことを考えない日はなかった。"),
        ("What if we're just too late for each other?", "もし私たちが、お互いにとってもう遅すぎるとしたら?"),
        ("I should have told you how I felt a long time ago.", "もっと早く、この気持ちを伝えるべきだった。"),
        ("Some people search their whole lives for what we already have.", "みんな一生かけて探すものを、私たちはもう手に入れている。"),
        ("I don't want to spend another day without you.", "あなたのいない一日を、もう過ごしたくない。"),
        ("I know it's complicated. I don't care.", "複雑なのはわかってる。でも構わない。"),
        ("I came back because I couldn't imagine my life without you.", "あなたのいない人生なんて想像できなくて、戻ってきた。"),
        ("You were the best part of my worst year.", "あなたは、私の最悪の一年の中で、一番いいことだった。"),
        ("Maybe timing isn't everything. Maybe it's just an excuse.", "タイミングがすべてじゃないのかもしれない。ただの言い訳なのかもしれない。"),
        ("I let you go once. I'm not making that mistake again.", "一度あなたを手放した。もう二度と同じ過ちは繰り返さない。"),
        ("It took losing you to realize what I actually had.", "あなたを失って初めて、自分が何を持っていたか気づいた。"),
        ("I fell for you before I even realized it was happening.", "気づいたときにはもう、あなたに恋していた。"),
        ("I'm not asking you to choose me. I'm asking you to choose happiness.", "私を選んでとは言わない。ただ、幸せを選んでほしいだけ。"),
        ("We were never just friends, were we?", "私たち、ただの友達だったことなんてなかったよね?"),
        ("I waited for you longer than I probably should have.", "たぶん必要以上に長く、あなたを待っていた。"),
        ("Every road I take somehow leads back to you.", "どの道を選んでも、なぜかあなたのところに戻ってくる。"),
        ("If this is goodbye, I need you to know it was worth it.", "もしこれが最後だとしても、意味のあることだったと知っていてほしい。"),
        ("I'm done running from how I feel about you.", "あなたへの気持ちから逃げるのは、もうやめる。"),
        ("Some love stories don't end. They just find their way back.", "終わらない恋物語もある。ただ、また巡り会うだけ。"),
        ("I didn't come here to win you back. I came to tell the truth.", "あなたを取り戻しに来たんじゃない。本当のことを伝えに来たんだ。"),
    ],
    "ドラマ映画のフレーズ": [
        ("I spent so many years being angry at you. I'm tired of it.", "長い間あなたに怒りを抱いてきた。もう疲れた。"),
        ("We don't get to choose our family, but we get to choose how we treat them.", "家族は選べない。でも、どう接するかは選べる。"),
        ("I'm not the person I used to be, and I'm not sorry for that.", "私はもう昔の自分じゃない。それを謝るつもりはない。"),
        ("It's never too late to make things right.", "物事を正すのに、遅すぎるということはない。"),
        ("You don't have to forgive me. I just needed you to hear it.", "許してくれなくていい。ただ、聞いてほしかっただけ。"),
        ("I spent my whole life trying to make you proud.", "私はずっと、あなたに誇りに思ってもらおうと生きてきた。"),
        ("Sometimes the hardest person to forgive is yourself.", "一番許すのが難しい相手は、時に自分自身だ。"),
        ("We can't change what happened. We can only choose what happens next.", "起きたことは変えられない。変えられるのはこれからだけだ。"),
        ("I finally understand why you made the choices you did.", "あなたがなぜあの選択をしたのか、やっと理解できた。"),
        ("I lost so much time being afraid to say what I really meant.", "本音を言うのが怖くて、たくさんの時間を無駄にしてしまった。"),
        ("This family has kept too many secrets for too long.", "この家族は、あまりにも長い間、多くの秘密を抱えすぎてきた。"),
        ("I don't need you to fix it. I just need you to stay.", "直してほしいわけじゃない。ただそばにいてほしいだけ。"),
        ("Growing up meant realizing my parents were just people, too.", "大人になるということは、両親もただの一人の人間だと気づくことだった。"),
        ("I used to think strength meant never breaking down.", "かつては、強さとは決して崩れないことだと思っていた。"),
        ("We were both just doing the best we could with what we had.", "私たちは二人とも、持っているもので精一杯やっていただけだった。"),
        ("I'm not asking you to forget. I'm asking you to move forward.", "忘れてほしいとは言わない。ただ前に進んでほしいだけ。"),
        ("There's a version of this family that still has a chance.", "この家族には、まだやり直せる可能性が残っている。"),
        ("I finally said the words I'd been holding back for years.", "何年も言えずにいた言葉を、ついに口にした。"),
        ("Some wounds don't heal. You just learn to carry them differently.", "治らない傷もある。ただ、その抱え方を学んでいくだけだ。"),
        ("I came home to make peace, not to relive the past.", "私は仲直りをするために帰ってきた。過去を蒸し返すためじゃない。"),
        ("We're allowed to love each other and still get it wrong sometimes.", "愛し合っていても、時に間違えることはあっていい。"),
    ],
    "サスペンス映画のフレーズ": [
        ("Someone in this room isn't who they say they are.", "この部屋にいる誰かは、自分が言っている人物ではない。"),
        ("We've been chasing the wrong lead this whole time.", "私たちはずっと間違った手がかりを追っていた。"),
        ("Everything you told me was a lie, wasn't it?", "あなたが私に話したことは、全部嘘だったんだね?"),
        ("Someone's been one step ahead of us the entire time.", "誰かがずっと私たちの一歩先を行っていた。"),
        ("If you're telling the truth, then who set me up?", "もしあなたが本当のことを言っているなら、誰が私を陥れたんだ?"),
        ("I trusted you. That was my first mistake.", "あなたを信じた。それが最初の間違いだった。"),
        ("There's a mole inside this organization.", "この組織の内部に裏切り者がいる。"),
        ("We don't have much time before they realize we know.", "私たちが気づいたと相手に悟られる前に、時間がない。"),
        ("Everything points back to the same person.", "すべてが同じ人物を指し示している。"),
        ("You've been watching me this whole time, haven't you?", "あなたはずっと私を見張っていたんだね?"),
        ("The evidence was destroyed for a reason.", "証拠が処分されたのには理由がある。"),
        ("I need you to tell me the truth, right now.", "今すぐ本当のことを話してほしい。"),
        ("He's not the victim here. He's the one pulling the strings.", "彼は被害者じゃない。糸を引いているのは彼のほうだ。"),
        ("We're running out of time to stop this.", "これを止めるための時間が尽きかけている。"),
        ("Whoever did this knew exactly what they were doing.", "これをやったのは、自分が何をしているか正確にわかっていた人間だ。"),
        ("You're not going anywhere until you tell me who you're working for.", "誰のために動いているか話すまで、どこにも行かせない。"),
        ("The call came from inside the building.", "その電話は建物の中からかかってきていた。"),
        ("I've known for weeks. I just needed proof.", "何週間も前から気づいていた。ただ証拠が必要だっただけだ。"),
        ("Whatever happens next, don't trust anyone but me.", "この先何が起きても、私以外の誰も信じるな。"),
        ("This was never about the money. It was about revenge.", "これは金の問題じゃ決してなかった。復讐が目的だった。"),
        ("By the time they find the body, we'll be long gone.", "死体が発見される頃には、私たちはとうに姿を消している。"),
    ],
}


def main() -> int:
    with db() as conn:
        p_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }

        totals: dict[str, tuple[int, int]] = {}
        total_added = total_skipped = 0
        for scene, items in PHRASES_BY_SCENE.items():
            added = skipped = 0
            for en, ja in items:
                if en.lower() in p_existing:
                    skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                p_existing.add(en.lower())
                added += 1
            totals[scene] = (added, skipped)
            total_added += added
            total_skipped += skipped

    for scene, (added, skipped) in totals.items():
        print(f"{scene}: +{added} (skipped {skipped})")
    print(f"TOTAL phrases: +{total_added} (skipped {total_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
