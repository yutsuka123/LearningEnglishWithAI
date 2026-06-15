# ruff: noqa: E501  (data-heavy seed script)
"""Add news/idiom/phone/daily phrases + philosopher quotes, with supporting
vocabulary. Authored by Claude — no app/OpenAI API calls. Phrases dedupe on
english (lowercased); words dedupe on english and back-fill empty examples.

カテゴリ(scene): ニュース報道30 / ニュース定型10 / 慣用句・イディオム20 /
電話10 / 日常会話30 / 哲学・名言30。加えて関連語をニュース/哲学ドメインで追加。

Run:  python scripts/add_news_quotes.py   (then run scripts/relevel.py)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# (english, japanese) grouped by scene.
PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "ニュース報道": [
        ("The government announced new measures to curb inflation.", "政府はインフレ抑制の新たな対策を発表した。"),
        ("Officials are weighing additional sanctions.", "当局は追加制裁を検討している。"),
        ("The central bank raised interest rates for the third time this year.", "中央銀行は今年3度目の利上げに踏み切った。"),
        ("Negotiators failed to reach an agreement overnight.", "交渉担当者は徹夜の協議で合意に至らなかった。"),
        ("The death toll has risen to more than fifty.", "死者数は50人を超えた。"),
        ("Authorities have launched an investigation into the incident.", "当局はこの事件の捜査を開始した。"),
        ("Lawmakers passed the bill by a narrow margin.", "議員らは僅差で法案を可決した。"),
        ("The company posted record quarterly profits.", "同社は四半期で過去最高益を計上した。"),
        ("Wildfires have forced thousands to evacuate.", "山火事で数千人が避難を余儀なくされた。"),
        ("The summit is expected to focus on climate change.", "首脳会議は気候変動に焦点を当てる見通しだ。"),
        ("Markets tumbled amid fears of a recession.", "景気後退への懸念から市場は急落した。"),
        ("The president is set to address the nation tonight.", "大統領は今夜、国民に向けて演説する予定だ。"),
        ("A ceasefire has been declared in the region.", "その地域で停戦が宣言された。"),
        ("Health officials warn of a new wave of infections.", "保健当局は新たな感染の波に警戒を呼びかけている。"),
        ("The court ruled the policy unconstitutional.", "裁判所はその政策を違憲と判断した。"),
        ("Unemployment fell to its lowest level in decades.", "失業率は数十年ぶりの低水準に低下した。"),
        ("Rescuers are searching for survivors in the rubble.", "救助隊はがれきの中で生存者を捜索している。"),
        ("The strike has disrupted train services nationwide.", "ストライキで全国の鉄道が乱れている。"),
        ("Diplomats are calling for an immediate de-escalation.", "外交官らは即時の緊張緩和を求めている。"),
        ("The new law takes effect at the start of next month.", "新法は来月初めに施行される。"),
        ("Voters head to the polls in a closely watched election.", "注目の選挙で有権者が投票に向かう。"),
        ("The agency downgraded its growth forecast.", "当局は成長見通しを下方修正した。"),
        ("Protesters gathered outside the parliament building.", "抗議する人々が議会の前に集まった。"),
        ("The merger is still subject to regulatory approval.", "その合併はなお規制当局の承認を要する。"),
        ("Scientists say the findings could be a breakthrough.", "科学者らはこの発見が画期的なものになり得ると述べている。"),
        ("Severe flooding has cut off several villages.", "激しい洪水でいくつかの村が孤立した。"),
        ("The minister resigned amid mounting pressure.", "圧力の高まりを受けて大臣は辞任した。"),
        ("Tech firms are racing to develop the technology.", "各テック企業がその技術の開発を競っている。"),
        ("The talks ended without a breakthrough.", "協議は進展のないまま終わった。"),
        ("Aid is finally reaching the hardest-hit areas.", "支援がようやく最も被害の大きい地域に届きつつある。"),
    ],
    "ニュース定型": [
        ("Breaking news.", "速報です。"),
        ("We interrupt this program for a special report.", "特別報道のため番組を中断します。"),
        ("Stay tuned for more details.", "続報にご注目ください。"),
        ("We'll keep you updated as the story develops.", "続報が入り次第お伝えします。"),
        ("More on this story after the break.", "このニュースの詳細はCMのあとで。"),
        ("according to sources familiar with the matter", "事情に詳しい関係者によると"),
        ("speaking on condition of anonymity", "匿名を条件に語った"),
        ("in a statement released earlier today", "本日先ほど発表された声明で"),
        ("This is a developing story.", "これは現在も動いているニュースです。"),
        ("Back to you in the studio.", "スタジオにお返しします。"),
    ],
    "慣用句・イディオム": [
        ("Let's play it by ear.", "臨機応変にやろう。"),
        ("That's the last straw.", "もう我慢の限界だ。"),
        ("He let the cat out of the bag.", "彼はうっかり秘密を漏らした。"),
        ("It costs an arm and a leg.", "とても高くつく。"),
        ("Don't beat around the bush.", "遠回しに言わないで(はっきり言って)。"),
        ("We're on the same page.", "認識は一致しているね。"),
        ("It's not rocket science.", "そんなに難しいことじゃない。"),
        ("Let's call it a day.", "今日はこれで切り上げよう。"),
        ("Get your act together.", "しっかりしてくれよ。"),
        ("That rings a bell.", "それは心当たりがある。"),
        ("I'm feeling under the weather.", "体調がすぐれないんだ。"),
        ("Break a leg!", "頑張って!(成功を祈るよ)"),
        ("Just bite the bullet.", "覚悟を決めてやってしまおう。"),
        ("Cut me some slack.", "少し大目に見てよ。"),
        ("It was a blessing in disguise.", "それは不幸中の幸いだった。"),
        ("You hit the nail on the head.", "まさに図星だ(的確だ)。"),
        ("Once in a blue moon.", "ごくまれにね。"),
        ("Speak of the devil.", "噂をすれば(影が差す)。"),
        ("The ball is in your court.", "次はあなたが決める番だ。"),
        ("Always go the extra mile.", "ひと手間を惜しまず努力しよう。"),
        ("Let's touch base next week.", "また来週、連絡を取り合おう。"),
        ("It's a win-win.", "それは双方に得な話だ。"),
        ("Don't jump to conclusions.", "早合点しないで。"),
        ("That's a real game changer.", "それは状況を一変させるものだ。"),
        ("Let's think outside the box.", "既成概念にとらわれず考えよう。"),
        ("He finally threw in the towel.", "彼はついに降参した。"),
        ("It's water under the bridge.", "それはもう済んだことだ。"),
        ("Don't put all your eggs in one basket.", "一つに賭けすぎないで。"),
        ("She's a tough cookie.", "彼女は芯が強い人だ。"),
        ("Let's wrap it up.", "そろそろまとめよう。"),
        ("I'm all ears.", "ぜひ聞かせて(興味津々だ)。"),
        ("It slipped through the cracks.", "それは見落とされてしまった。"),
        ("Don't count your chickens before they hatch.", "捕らぬ狸の皮算用はやめよう。"),
        ("Every cloud has a silver lining.", "どんな不運にも明るい面はある。"),
        ("Actions speak louder than words.", "行動は言葉よりも雄弁だ。"),
        ("When in Rome, do as the Romans do.", "郷に入っては郷に従え。"),
    ],
    "電話": [
        ("Hello, this is Taro from ABC Company.", "もしもし、ABC社の太郎です。"),
        ("May I speak to Mr. Smith, please?", "スミスさんをお願いできますか。"),
        ("Could you put me through to the sales department?", "営業部におつなぎいただけますか。"),
        ("Hold on a moment, please.", "少々お待ちください。"),
        ("I'm afraid she's not available right now.", "あいにく彼女は今、手が離せません。"),
        ("Can I take a message?", "ご伝言を承りましょうか。"),
        ("Could you call back later?", "のちほどおかけ直しいただけますか。"),
        ("I'll call you back in ten minutes.", "10分後にかけ直します。"),
        ("Sorry, I think you have the wrong number.", "すみません、番号をお間違えのようです。"),
        ("You're breaking up; I can't hear you well.", "電波が悪くて声が途切れています。"),
    ],
    "日常会話": [
        ("Could you give me a hand?", "ちょっと手を貸してくれる?"),
        ("It's totally up to you.", "完全にあなた次第だよ。"),
        ("Take your time.", "ゆっくりでいいよ。"),
        ("Let me think about it.", "ちょっと考えさせて。"),
        ("That works for me.", "それで大丈夫だよ。"),
        ("I couldn't agree more.", "まったく同感だ。"),
        ("Suit yourself.", "好きにすればいいよ。"),
        ("It slipped my mind.", "うっかり忘れてた。"),
        ("I'm just looking, thanks.", "見ているだけです、ありがとう。"),
        ("Keep the change.", "お釣りは取っておいて。"),
        ("Let's grab a bite.", "軽く何か食べに行こう。"),
        ("I'm running a bit late.", "少し遅れそうなんだ。"),
        ("Can you do me a favor?", "お願いがあるんだけど。"),
        ("It's on me today.", "今日は私のおごりだよ。"),
        ("Let's split the bill.", "割り勘にしよう。"),
        ("What's the catch?", "何か裏があるんじゃない?"),
        ("I'll take a rain check.", "また今度にさせてね。"),
        ("Make yourself at home.", "どうぞくつろいでね。"),
        ("That's a relief.", "それはほっとしたよ。"),
        ("Better safe than sorry.", "念には念を入れよう。"),
        ("It's a long story.", "話せば長くなるんだ。"),
        ("Let's keep in touch.", "これからも連絡を取り合おうね。"),
        ("I owe you one.", "今回は恩に着るよ。"),
        ("That's news to me.", "それは初耳だよ。"),
        ("I'm on my way.", "今、向かっているところだよ。"),
        ("Help yourself to the snacks.", "お菓子はご自由にどうぞ。"),
        ("Let's get down to business.", "さあ本題に入ろう。"),
        ("Don't get me wrong.", "誤解しないでほしいんだけど。"),
        ("It's worth a try.", "試してみる価値はあるよ。"),
        ("Let's call it even.", "これでおあいこにしよう。"),
        ("Could you speak up a little?", "もう少し大きな声で話してもらえる?"),
        ("Sounds good to me.", "それでいいと思うよ。"),
        ("Same here.", "私も同じだよ。"),
        ("Fingers crossed.", "うまくいくように祈ってるよ。"),
        ("Maybe next time.", "また次の機会にね。"),
        ("I can't make it today.", "今日は都合がつかないんだ。"),
        ("What are you up to?", "何してるの?"),
        ("Catch you later.", "またあとでね。"),
        ("It depends on the situation.", "状況によるね。"),
        ("Let me get back to you.", "あとで返事するね。"),
        ("I'm not sure yet.", "まだはっきりしないんだ。"),
        ("That makes sense.", "なるほど、筋が通ってるね。"),
        ("Just so you know, I'll be late.", "一応言っておくと、遅れるよ。"),
        ("Give me a second.", "ちょっと待ってね。"),
        ("Could be worse.", "まだマシなほうだよ。"),
        ("I'll keep that in mind.", "覚えておくよ。"),
        ("Let's not get ahead of ourselves.", "先走らないようにしよう。"),
        ("Whatever works.", "うまくいくなら何でもいいよ。"),
        ("I'll think it over.", "よく考えてみるよ。"),
        ("Let's wait and see.", "様子を見てみよう。"),
        ("I'm in no rush.", "別に急いでいないよ。"),
        ("Count me in.", "私も参加するよ。"),
        ("Count me out.", "私は遠慮しておくよ。"),
        ("Let's get going.", "そろそろ出かけよう。"),
    ],
    "哲学・名言": [
        ("The only true wisdom is in knowing you know nothing.", "唯一の真の知恵は、自分が何も知らないと知ることにある(無知の知)。（ソクラテス）"),
        ("The unexamined life is not worth living.", "吟味されない人生は、生きるに値しない。（ソクラテス）"),
        ("I think, therefore I am.", "我思う、ゆえに我あり。（デカルト）"),
        ("Man is the measure of all things.", "人間は万物の尺度である。（プロタゴラス）"),
        ("We are what we repeatedly do.", "我々は、繰り返し行うことそのものである。（アリストテレス）"),
        ("Knowing yourself is the beginning of all wisdom.", "己を知ることが、あらゆる知恵の始まりである。（アリストテレス）"),
        ("Happiness depends upon ourselves.", "幸福は、自分自身に左右される。（アリストテレス）"),
        ("God is dead.", "神は死んだ。（ニーチェ）"),
        ("That which does not kill us makes us stronger.", "我々を殺さないものは、我々をより強くする。（ニーチェ）"),
        ("He who has a why to live can bear almost any how.", "なぜ生きるかを持つ者は、ほぼどんな状況にも耐えられる。（ニーチェ）"),
        ("Two things fill the mind with awe: the starry heavens above and the moral law within.", "我が上なる星空と、我が内なる道徳法則の二つが心を畏敬で満たす。（カント）"),
        ("Act only on that maxim you can will to be a universal law.", "普遍的法則となることを意志しうる格率に従ってのみ行為せよ。（カント）"),
        ("Liberty consists in doing what one desires.", "自由とは、自分の望むことをなしうることにある。（J.S.ミル）"),
        ("Man is born free, and everywhere he is in chains.", "人間は自由なものとして生まれた。しかし、いたるところで鎖につながれている。（ルソー）"),
        ("Hell is other people.", "地獄とは、他人のことだ。（サルトル）"),
        ("Existence precedes essence.", "実存は本質に先立つ。（サルトル）"),
        ("Man is condemned to be free.", "人間は、自由の刑に処せられている。（サルトル）"),
        ("The life of man is solitary, poor, nasty, brutish, and short.", "人間の生は、孤独で貧しく、険悪で残忍、そして短い。（ホッブズ）"),
        ("Whereof one cannot speak, thereof one must be silent.", "語りえぬものについては、沈黙せねばならない。（ウィトゲンシュタイン）"),
        ("The limits of my language mean the limits of my world.", "私の言語の限界が、私の世界の限界を意味する。（ウィトゲンシュタイン）"),
        ("Knowledge is power.", "知は力なり。（フランシス・ベーコン）"),
        ("The heart has its reasons which reason knows nothing of.", "心には、理性の知らない道理がある。（パスカル）"),
        ("Man is a thinking reed.", "人間は考える葦である。（パスカル）"),
        ("Freedom is the insight into necessity.", "自由とは、必然の洞察である。（ヘーゲル）"),
        ("What is rational is real, and what is real is rational.", "理性的なものは現実的であり、現実的なものは理性的である。（ヘーゲル）"),
        ("The philosophers have only interpreted the world; the point is to change it.", "哲学者たちは世界を解釈してきたにすぎない。重要なのは、それを変えることだ。（マルクス）"),
        ("You cannot step into the same river twice.", "同じ川に二度入ることはできない。（ヘラクレイトス）"),
        ("The owl of Minerva spreads its wings only at dusk.", "ミネルヴァのふくろうは、黄昏になって初めて飛び立つ。（ヘーゲル）"),
        ("To be is to be perceived.", "存在するとは、知覚されることである。（バークリー）"),
        ("Entities should not be multiplied beyond necessity.", "存在を必要以上に増やすべきではない(オッカムの剃刀)。（オッカム）"),
        ("Happiness is the meaning and purpose of life.", "幸福こそ、人生の意味であり目的である。（アリストテレス）"),
        ("There is nothing permanent except change.", "変化のほかに、永遠なものは何もない。（ヘラクレイトス）"),
        ("No man's knowledge can go beyond his experience.", "人の知識は、その経験を超えることはできない。（ロック）"),
        ("Beauty exists merely in the mind which contemplates them.", "美は事物そのものにはなく、ただ眺める心の中に存在する。（ヒューム）"),
        ("Be the change you wish to see in the world.", "世界に望む変化に、あなた自身がなりなさい。（ガンジー）"),
        ("The greatest happiness of the greatest number is the foundation of morals.", "最大多数の最大幸福が、道徳と立法の基礎である。（ベンサム）"),
        ("Doubt is the origin of wisdom.", "疑うことが、知恵の始まりである。（デカルト）"),
        ("Wonder is the beginning of wisdom.", "驚きこそ、知恵の始まりである。（プラトン）"),
        ("Justice is giving each person his due.", "正義とは、各人にその人のものを与えることである。（プラトン）"),
        ("Time is the moving image of eternity.", "時間とは、永遠の動く似姿である。（プラトン）"),
        ("Anxiety is the dizziness of freedom.", "不安とは、自由のめまいである。（キルケゴール）"),
        ("Life can only be understood backwards, but it must be lived forwards.", "人生は振り返って初めて理解できるが、前を向いて生きねばならない。（キルケゴール）"),
        ("The greatest wealth is to live content with little.", "最大の富は、わずかなもので満ち足りて生きることだ。（プラトン）"),
        ("Know thyself.", "汝自身を知れ。（デルポイの神託／ソクラテス）"),
    ],
}

# Supporting vocabulary surfaced by the phrases above.
# (english, japanese, example) grouped by domain.
WORDS_BY_DOMAIN: dict[str, list[tuple[str, str, str]]] = {
    "ニュース": [
        ("sanction", "制裁・制裁措置", "The UN imposed sanctions on the regime."),
        ("inflation", "インフレ・物価上昇", "Inflation eroded their savings."),
        ("recession", "景気後退・不況", "The economy slipped into recession."),
        ("ceasefire", "停戦", "Both sides agreed to a ceasefire."),
        ("evacuate", "避難する・避難させる", "Residents were evacuated before the storm."),
        ("unconstitutional", "違憲の", "The law was ruled unconstitutional."),
        ("forecast", "予測・見通し", "The forecast predicts heavy rain."),
        ("merger", "合併", "The merger created a giant firm."),
        ("regulator", "規制当局", "Regulators approved the deal."),
        ("de-escalation", "緊張緩和", "Diplomats urged de-escalation."),
        ("toll", "死傷者数・通行料", "The death toll kept rising."),
        ("rubble", "がれき", "Rescuers dug through the rubble."),
        ("summit", "首脳会議", "World leaders met at the summit."),
        ("lawmaker", "議員・立法者", "Lawmakers debated the new bill."),
        ("margin", "差・余白・利幅", "He won by a slim margin."),
        ("quarterly", "四半期の", "They released quarterly results."),
        ("disrupt", "混乱させる・中断させる", "The strike disrupted travel."),
        ("mounting", "増大する・高まる", "Mounting pressure forced a decision."),
        ("breakthrough", "突破口・大発見", "Scientists made a major breakthrough."),
        ("anonymity", "匿名(性)", "The source spoke on anonymity."),
        ("turnout", "投票率・人出", "Voter turnout was unusually high."),
        ("downgrade", "格下げする・下方修正する", "The agency downgraded its outlook."),
    ],
    "哲学": [
        ("wisdom", "知恵", "True wisdom comes with humility."),
        ("virtue", "美徳・徳", "Courage is considered a virtue."),
        ("ethics", "倫理(学)", "Medical ethics guide the doctors."),
        ("morality", "道徳(性)", "He questioned conventional morality."),
        ("existence", "存在・実存", "They debated the meaning of existence."),
        ("essence", "本質", "Freedom is the essence of his thought."),
        ("consciousness", "意識", "The nature of consciousness is a mystery."),
        ("perception", "知覚・認識", "Reality may differ from our perception."),
        ("reason", "理性・理由", "Kant praised the power of reason."),
        ("rational", "理性的な・合理的な", "He gave a rational explanation."),
        ("necessity", "必然(性)・必要", "Freedom is the insight into necessity."),
        ("maxim", "格率・格言", "Act on a maxim you could universalize."),
        ("universal", "普遍的な", "He sought a universal moral law."),
        ("contradiction", "矛盾", "The argument contains a contradiction."),
        ("dialectic", "弁証法", "Hegel is known for his dialectic."),
        ("metaphysics", "形而上学", "Metaphysics asks what truly exists."),
        ("epistemology", "認識論", "Epistemology studies how we know."),
        ("skepticism", "懐疑(論)", "Descartes began with radical skepticism."),
        ("determinism", "決定論", "Determinism denies free will."),
        ("nihilism", "ニヒリズム・虚無主義", "Nietzsche warned against nihilism."),
    ],
}


def main() -> int:
    with db() as conn:
        # --- phrases ---
        p_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        per_scene: dict[str, int] = {}
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in p_existing:
                    p_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                p_existing.add(en.lower())
                p_added += 1
                per_scene[scene] = per_scene.get(scene, 0) + 1

        # --- supporting words ---
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        w_added = w_skipped = 0
        for domain, items in WORDS_BY_DOMAIN.items():
            for en, ja, ex in items:
                if en.lower() in w_existing:
                    conn.execute(
                        "UPDATE words SET example = ? WHERE "
                        "LOWER(english) = LOWER(?) "
                        "AND COALESCE(example, '') = ''",
                        (ex, en),
                    )
                    w_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO words (english, japanese, part_of_speech, "
                    "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                    (en, ja, "", ex, domain, "700"),
                )
                w_existing.add(en.lower())
                w_added += 1

    print(f"phrases: +{p_added} (skipped {p_skipped})  {per_scene}")
    print(f"words:   +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print(
            "totals -> phrases:",
            conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0],
            "/ words:",
            conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
