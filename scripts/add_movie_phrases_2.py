# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for "映画・文学・芸術" domain, MOVIE GENRE PHRASES
(part 2), authored by Claude.

Focus: 映画の台詞回しをテーマにしたフレーズを、ジャンルごとに深掘りする。

  1. ディズニー・ファミリー映画のフレーズ — 夢・魔法・冒険・友情・希望をテーマに
     した、ファミリー向けアニメーション映画で使われがちな前向きな言い回し。
  2. クライムサスペンス映画のフレーズ — 犯罪捜査・尋問・裏社会・取引など、
     クライム映画特有の緊迫した言い回し。
  3. 戦争映画のフレーズ — 戦場の指揮・仲間との絆・犠牲・帰還などの言い回し。
  4. 歴史映画のフレーズ — 時代劇・伝記映画で使われる、格式ばった/古風な
     ニュアンスを含む言い回し。
  5. 西部劇のフレーズ — 決闘・保安官・荒野など、西部劇特有の言い回し。
  6. アメコミ映画のフレーズ — ヒーロー・悪役の対峙・使命感など、スーパー
     ヒーロー映画で使われがちな言い回し。

著作権への配慮: すべてのフレーズは特定の実在する映画・作品からの台詞の引用では
なく、各ジャンルで典型的に使われる言い回しを参考にしたオリジナルの例文である。
版権キャラクターの固有名詞（人名・団体名など）は一切使用していない。

暴力表現への配慮: 特に「戦争映画」「クライムサスペンス」「西部劇」ジャンルの
フレーズは、緊張感やドラマ性を伝えることを目的としつつ、暴力そのものを美化・
賛美する表現は避け、仲間との絆・犠牲・帰還・正義といった事実的・教育的な
トーンを保つよう配慮した。

単語（words テーブル）への追加は行わない。フレーズのみを追加する。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_movie_phrases_2.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- phrases: scene -> [(english, japanese)] --------------------------------

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "ディズニー・ファミリー映画のフレーズ": [
        ("Believe in yourself, and anything is possible.", "自分を信じれば、何だって可能よ。"),
        ("Every dream is worth chasing, no matter how big.", "どんな夢も、追いかける価値がある。"),
        ("Sometimes the smallest heart holds the biggest courage.", "小さな心が、一番大きな勇気を持っていることもある。"),
        ("Magic lives in the people who believe in it.", "魔法は、それを信じる人の中に生きている。"),
        ("You don't need wings to fly, just the courage to try.", "飛ぶのに翼はいらない、挑戦する勇気だけでいい。"),
        ("No matter how far you go, you can always find your way home.", "どんなに遠くへ行っても、家への道はきっと見つかる。"),
        ("True friends stick together, no matter what.", "本当の友達は、何があっても離れない。"),
        ("Every ending is just a new beginning in disguise.", "すべての終わりは、姿を変えた新しい始まりに過ぎない。"),
        ("Hope is the one thing no one can take from you.", "希望だけは、誰にも奪えないものよ。"),
        ("The greatest adventures start with a single brave step.", "最高の冒険は、たった一歩の勇気から始まる。"),
        ("Even the smallest star can light up the darkest night.", "どんなに小さな星でも、一番暗い夜を照らせる。"),
        ("Family isn't just who you're born with, it's who you choose.", "家族とは生まれで決まるものじゃない、選ぶものよ。"),
        ("As long as you keep dreaming, you're never truly lost.", "夢を見続ける限り、本当に道に迷うことはない。"),
        ("It only takes one act of kindness to change everything.", "たった一つの優しさが、すべてを変えることもある。"),
        ("The world is full of wonders, if you just open your eyes.", "目を開きさえすれば、世界は驚きに満ちている。"),
        ("Never let anyone tell you your dreams are too big.", "自分の夢が大きすぎるなんて、誰にも言わせちゃだめ。"),
        ("Every hero was once just an ordinary kid with a dream.", "どんな英雄も、かつては夢を持つただの子どもだった。"),
        ("Follow your heart, and it will never lead you astray.", "心に従えば、決して道を誤ることはない。"),
    ],
    "クライムサスペンス映画のフレーズ": [
        ("Where were you last night between nine and midnight?", "昨夜9時から12時の間、どこにいた？"),
        ("We have a witness who puts you at the scene.", "お前を現場で見た目撃者がいるんだ。"),
        ("Talk now, or talk to your lawyer later.", "今話すか、後で弁護士に話すか、選べ。"),
        ("Everyone in this city owes somebody something.", "この街じゃ、誰もが誰かに借りがある。"),
        ("I don't do favors, I do deals.", "俺は施しはしない、取引をするだけだ。"),
        ("The evidence doesn't lie, but people do.", "証拠は嘘をつかない、だが人は嘘をつく。"),
        ("You've got one chance to walk away from this clean.", "これから手を引くチャンスは一度だけだ。"),
        ("Somebody in this room isn't telling the truth.", "この部屋の中に、本当のことを言っていない奴がいる。"),
        ("Follow the money, and you'll find your killer.", "金の流れを追えば、犯人にたどり着く。"),
        ("I want a name, and I want it tonight.", "名前を教えろ、今夜中にだ。"),
        ("This goes all the way to the top.", "これは組織の上層部にまで繋がっている。"),
        ("Nobody double-crosses me and walks away.", "俺を裏切って、無事でいられる奴はいない。"),
        ("The deal's off the table the moment you lie to me.", "嘘をついた瞬間、この取引は終わりだ。"),
        ("You've got until sundown to make your choice.", "日没までに決断しろ。"),
        ("There's no such thing as a clean getaway.", "完璧な逃走なんてものは存在しない。"),
        ("Somebody's going to talk, it's just a matter of time.", "誰かが口を割る、時間の問題だ。"),
        ("I've seen enough crime scenes to know when something's off.", "現場を見れば、何かがおかしいとすぐ分かる。"),
        ("Trust is a currency, and yours just ran out.", "信頼は通貨だ、お前のはもう底をついた。"),
    ],
    "戦争映画のフレーズ": [
        ("Hold the line, no matter what happens.", "何があっても、この陣を死守しろ。"),
        ("We don't leave anyone behind.", "誰も置き去りにはしない。"),
        ("Keep your head down and stay close to me.", "頭を低くして、俺のそばを離れるな。"),
        ("Every soldier here has a family waiting at home.", "ここにいる兵士全員に、家で待つ家族がいる。"),
        ("We fight so that others won't have to.", "他の誰かが戦わずに済むよう、俺たちが戦う。"),
        ("Orders are orders, but I won't leave a man behind.", "命令は命令だが、仲間を見捨てはしない。"),
        ("Courage isn't the absence of fear, it's moving forward anyway.", "勇気とは恐怖がないことじゃない、それでも前へ進むことだ。"),
        ("We lost good men today, and we'll remember every one of them.", "今日、良き仲間を失った、その一人一人を忘れない。"),
        ("Just get home safe. That's an order.", "無事に帰れ。これは命令だ。"),
        ("The war may end, but the memories never do.", "戦争は終わっても、記憶は消えない。"),
        ("We're not fighting for glory, we're fighting for each other.", "俺たちは名誉のためじゃなく、仲間のために戦っているんだ。"),
        ("Stay sharp, the quiet ones are the most dangerous.", "気を抜くな、静かな時ほど危険だ。"),
        ("I made a promise to bring my men home, and I intend to keep it.", "部下を家に連れて帰ると誓った、それを守るつもりだ。"),
        ("This uniform means something, don't ever forget that.", "この軍服には意味がある、決して忘れるな。"),
        ("After everything we've been through, you're not just my unit, you're my family.", "これだけのことを乗り越えた今、お前たちは仲間じゃなく家族だ。"),
        ("We survived the battle, now we have to survive coming home.", "戦闘は生き延びた、今度は帰還後を生き延びる番だ。"),
        ("Freedom always comes at a price someone else paid.", "自由には、誰かが払った代償が必ずある。"),
        ("When it's over, all that matters is who's still standing beside you.", "終わった時に大事なのは、誰がまだ隣に立っているかだ。"),
    ],
    "歴史映画のフレーズ": [
        ("History will remember what we do here today.", "今日ここで我々が為すことを、歴史は記憶するだろう。"),
        ("I did not seek this crown, but I shall not abandon it.", "この王冠を望んだわけではないが、放棄するつもりもない。"),
        ("A kingdom is not built in a single lifetime.", "王国は一代で築かれるものではない。"),
        ("Loyalty to the crown must never waver, my lord.", "王家への忠誠は、決して揺らいではならぬ、閣下。"),
        ("We stand at the threshold of a new era.", "我々は新しい時代の入り口に立っている。"),
        ("Let it be known that I never broke my word.", "私が約束を違えたことは一度もないと、記録に留めよ。"),
        ("The people will judge us long after we are gone.", "我々が去った後も、民は我々を裁くだろう。"),
        ("Power, once seized, is rarely given back willingly.", "一度掴んだ権力は、自ら手放されることは滅多にない。"),
        ("I was born into duty, not into choice.", "私は選択の余地なく、義務の中に生まれた。"),
        ("Even kings must answer to something greater than themselves.", "王たる者も、己より大きな何かに応える義務がある。"),
        ("Our ancestors bled for this land, and we shall not forsake it.", "先祖はこの地のために血を流した、我々は決して見捨てぬ。"),
        ("The court whispers, but the throne must remain silent.", "宮廷は囁くが、玉座は沈黙を守らねばならぬ。"),
        ("I have signed my name to history, for better or worse.", "良くも悪くも、私は歴史に名を刻んだ。"),
        ("A true leader is measured by what he sacrifices, not what he gains.", "真の指導者は、得たものではなく捧げたもので測られる。"),
        ("Let the record show that I stood for what was right.", "私が正義のために立ったことを、記録に残せ。"),
        ("Empires rise on ambition and fall on pride.", "帝国は野心によって興り、驕りによって滅びる。"),
        ("We are but a single page in a much longer story.", "我々は、もっと長い物語のたった一頁に過ぎない。"),
        ("Some battles are fought with swords, others with silence.", "剣で戦う戦いもあれば、沈黙で戦う戦いもある。"),
    ],
    "西部劇のフレーズ": [
        ("This town ain't big enough for the both of us.", "この町は、俺たち二人には狭すぎる。"),
        ("Draw your gun, or walk away while you still can.", "銃を抜くか、まだ歩けるうちに立ち去るかだ。"),
        ("I've got no quarrel with you, mister, but don't push your luck.", "あんたに恨みはないが、運試しはやめておけ。"),
        ("The sheriff's badge don't mean much out here.", "保安官のバッジも、この荒野じゃ大した意味はない。"),
        ("Nobody rides into my town and starts trouble.", "俺の町に来て、揉め事を起こす奴はいない。"),
        ("You've got until noon to get out of town.", "正午までにこの町を出て行け。"),
        ("Out here, a man's word is worth more than gold.", "ここでは、男の言葉は金より重い。"),
        ("I didn't come here looking for a fight, but I won't back down from one.", "争いを求めて来たわけじゃないが、退きはしない。"),
        ("The desert doesn't forgive mistakes.", "この砂漠は、過ちを許さない。"),
        ("Justice out here comes from the barrel of a gun, not a courtroom.", "ここの正義は法廷じゃなく、銃口から生まれる。"),
        ("Keep your hand near your holster and your eyes on the horizon.", "手はホルスターの近くに、目は地平線に向けておけ。"),
        ("There's a bounty on my head, but I aim to die free.", "俺の首には賞金がかかっているが、自由なまま死ぬつもりだ。"),
        ("This land belonged to no one before it belonged to everyone who fought for it.", "この土地は、それを守るために戦った者たちのものになる前は、誰のものでもなかった。"),
        ("A gunslinger's reputation rides ahead of him into every town.", "早撃ちの評判は、本人より先にどの町にも届く。"),
        ("I've buried enough friends in this dirt to know when trouble's coming.", "この土地に十分な数の友を埋めてきた、揉め事が近づく気配は分かる。"),
        ("The law ends where the frontier begins.", "法律の力が及ぶのは、この辺境が始まるところまでだ。"),
        ("Whoever draws first walks away, whoever hesitates doesn't.", "先に抜いた者が生き残り、躊躇した者は生き残らない。"),
        ("Out here, you're judged by your aim, not your name.", "ここでは、名前じゃなく腕前で評価される。"),
    ],
    "アメコミ映画のフレーズ": [
        ("I never asked for this gift, but I refuse to waste it.", "この力は望んで得たものじゃない、だが無駄にはしない。"),
        ("Every city needs someone willing to stand in the shadows for it.", "どんな街にも、陰に立って守る誰かが必要だ。"),
        ("You think a mask makes me any less human?", "仮面をつけているからって、俺が人間じゃないとでも？"),
        ("I didn't choose to be a hero, the world just left me no choice.", "英雄になろうと選んだわけじゃない、世界が他の道を残さなかっただけだ。"),
        ("Villains are made the same way heroes are, one choice at a time.", "悪役も英雄と同じように、一つひとつの選択で作られていく。"),
        ("This city doesn't need a legend, it needs someone who shows up.", "この街に必要なのは伝説じゃない、駆けつけてくれる誰かだ。"),
        ("You can take my identity, but you'll never take what I stand for.", "俺の正体は奪えても、俺が信じるものは決して奪えない。"),
        ("Real strength isn't in the powers themselves, it's in knowing when to hold back.", "本当の強さは力そのものではなく、いつ抑えるかを知ることだ。"),
        ("I've fallen more times than anyone knows, but I always get back up.", "誰も知らないほど何度も倒れてきたが、俺はいつも立ち上がる。"),
        ("Somebody has to say no when everyone else says it's impossible.", "みんなが不可能だと言う時、誰かがノーと言わなければならない。"),
        ("We don't get to choose the threats, only how we face them.", "脅威は選べない、どう立ち向かうかだけが選べる。"),
        ("Behind every mask is someone still trying to do the right thing.", "どんな仮面の下にも、正しいことをしようとしている誰かがいる。"),
        ("This isn't about being unstoppable, it's about never stopping.", "無敵になることじゃない、決して諦めないことだ。"),
        ("A hero's greatest battle is usually the one nobody sees.", "英雄の一番の戦いは、たいてい誰の目にも触れない戦いだ。"),
        ("I may have powers, but it's the choices that make me who I am.", "力は持っているが、俺を俺たらしめるのは選択だ。"),
        ("The city doesn't need to know my name, just that someone's watching.", "この街は俺の名前を知る必要はない、誰かが見守っていると知ればいい。"),
        ("Every villain believes they're the hero of their own story.", "どんな悪役も、自分こそが物語の主人公だと信じている。"),
        ("One person can't save the world alone, but they can start.", "一人で世界を救うことはできない、だが始めることはできる。"),
    ],
}


# --- insertion --------------------------------------------------------------


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }

        total_added = total_skipped = 0
        scene_counts: dict[str, tuple[int, int]] = {}
        for scene, items in PHRASES_BY_SCENE.items():
            added = skipped = 0
            for en, ja in items:
                if en.lower() in existing:
                    skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                existing.add(en.lower())
                added += 1
            scene_counts[scene] = (added, skipped)
            total_added += added
            total_skipped += skipped

    for scene, (added, skipped) in scene_counts.items():
        print(f"{scene}: +{added} (skipped {skipped})")
    print(f"phrases total: +{total_added} (skipped {total_skipped})")
    with db() as conn:
        print("totals -> phrases:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
