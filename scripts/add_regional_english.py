# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a new "地域別英語" niche covering British / Australian / Singapore /
Indian English (2026-08-12・TODO.md B13「地域別ニッチ候補」)。

既存の「イギリス料理」「インド料理」ドメインとは別に、実際の語彙・言い回しの
地域差(lift/elevator、queue、fortnight、servo、arvo、HDB、kiasu、prepone、
do the needful 等)を扱う。シンガポール・インド英語は「からかい」ではなく、
言語学的に確立された英語のバリエーションとして敬意を持って扱う方針
（各エージェントへの指示で明記済み）。

4地域を並列サブエージェント(Claude, 2026-08-12)で下書きし、本スクリプトで
まとめてローカルDBに投入する。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_regional_english.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` でフレーズの難易度を
再設定し、`python scripts/build_audio.py` で音声を生成すること。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- イギリス英語 ---
WORDS_UK: list[tuple[str, str, str, str, str, str]] = [
    ("lift (British English)", "エレベーター（イギリス英語、米:elevator）", "名詞", "Take the lift to the third floor.", "イギリス英語", "450"),
    ("flat (British English)", "アパート、マンションの一室（イギリス英語、米:apartment）", "名詞", "She lives in a small flat near the station.", "イギリス英語", "450"),
    ("queue (British English)", "列、行列（「並ぶ」という動詞としても使う）", "名詞", "There was a long queue outside the bakery.", "イギリス英語", "500"),
    ("fortnight", "2週間", "名詞", "I'm going on holiday for a fortnight.", "イギリス英語", "600"),
    ("cheers", "ありがとう／乾杯（軽い感謝の表現としてもよく使う）", "間投詞", "Cheers for the lift home, mate.", "イギリス英語", "500"),
    ("brilliant", "素晴らしい、最高だ（口語的な褒め言葉）", "形容詞", "That's brilliant news, well done!", "イギリス英語", "500"),
    ("rubbish (British English)", "ごみ／くだらないもの（米:garbage, trash）", "名詞", "Could you take the rubbish out, please?", "イギリス英語", "500"),
    ("bin (British English)", "ゴミ箱（米:trash can）", "名詞", "Put the wrapper in the bin.", "イギリス英語", "450"),
    ("pavement (British English)", "歩道（米:sidewalk）", "名詞", "Watch out for the bike on the pavement.", "イギリス英語", "550"),
    ("car park (British English)", "駐車場（米:parking lot）", "名詞", "The car park is just behind the office.", "イギリス英語", "500"),
    ("petrol (British English)", "ガソリン（米:gas, gasoline）", "名詞", "We should stop and get some petrol.", "イギリス英語", "550"),
    ("trousers", "ズボン（米では主にpants）", "名詞", "He wore a smart pair of trousers to the interview.", "イギリス英語", "500"),
    ("pants (British English)", "下着、パンツ（イギリスでは主に下着の意味。米のpants=ズボンとは異なるので注意）", "名詞", "He was standing there in his shirt and pants, looking for his trousers.", "イギリス英語", "600"),
    ("jumper (British English)", "セーター（米:sweater）", "名詞", "She put on a warm jumper before going outside.", "イギリス英語", "550"),
    ("torch", "懐中電灯（米:flashlight）", "名詞", "Bring a torch, it gets dark early in winter.", "イギリス英語", "550"),
    ("mobile (British English)", "携帯電話（米:cell phone）", "名詞", "Sorry, I didn't hear my mobile ring.", "イギリス英語", "500"),
    ("chemist (British English)", "薬局／薬剤師（米:drugstore, pharmacist）", "名詞", "I popped into the chemist for some paracetamol.", "イギリス英語", "550"),
    ("quid", "ポンド（イギリス通貨poundの口語表現）", "名詞", "The sandwich cost about three quid.", "イギリス英語", "600"),
    ("knackered", "へとへとに疲れた（くだけた表現）", "形容詞", "I'm absolutely knackered after that train journey.", "イギリス英語", "650"),
    ("gutted", "ひどくがっかりした（くだけた表現）", "形容詞", "She was gutted when her flight got delayed.", "イギリス英語", "650"),
    ("reckon (British English)", "〜だと思う（口語）", "動詞", "I reckon we should leave before the rush hour starts.", "イギリス英語", "600"),
    ("fancy", "〜が欲しい／〜する気がある（誘い文句としてもよく使う）", "動詞", "Do you fancy a cup of tea?", "イギリス英語", "550"),
    ("sorted", "解決済み、手配済み（口語）", "形容詞", "Don't worry about the tickets, it's all sorted.", "イギリス英語", "600"),
    ("redundant (British English)", "（人員整理で）解雇された（made redundantの形でよく使う）", "形容詞", "Two hundred staff were made redundant when the factory closed.", "イギリス英語", "700"),
    ("CV", "履歴書（米:resume）", "名詞", "Please attach your CV and a short cover letter.", "イギリス英語", "600"),
    ("drizzle (British English)", "霧雨、小雨", "名詞", "It's only drizzle, so we don't need an umbrella.", "イギリス英語", "550"),
]

PHRASES_UK: list[tuple[str, str]] = [
    ("Excuse me, is this the end of the queue?", "すみません、ここが列の最後尾ですか?"),
    ("Mind the gap between the train and the platform.", "電車とホームの間の隙間にご注意ください。"),
    ("Shall we pop to the pub for a quick pint after work?", "仕事の後、ちょっとパブに一杯飲みに行きませんか?"),
    ("It's a bit chilly out, isn't it? Typical British summer.", "外は少し肌寒いですね。いかにもイギリスの夏らしい。"),
    ("I'll ring you when I get home, cheers.", "家に着いたら電話するね、ありがとう。"),
    ("Sorry to bother you, could you point me to the toilet?", "お邪魔してすみません、お手洗いはどちらでしょうか?"),
    ("That film was absolutely brilliant, wasn't it?", "あの映画、本当に最高だったよね。"),
    ("I'm knackered, I think I'll have an early night.", "もうへとへとだから、今夜は早く寝ようと思う。"),
    ("Fancy going for a walk this afternoon?", "今日の午後、散歩に行きませんか?"),
    ("We're going on holiday to the seaside next fortnight.", "私たちは再来週、海辺へ休暇に出かけます。"),
    ("Could you keep an eye on my luggage while I queue for tickets?", "チケットの列に並んでいる間、荷物を見ていてもらえますか?"),
    ("It looks like rain, better bring a brolly.", "雨が降りそうだから、傘を持って行った方がいいよ。"),
    ("He got made redundant last year, but he's found a new job now.", "彼は去年解雇されたけど、もう新しい仕事を見つけたよ。"),
    ("I reckon the meeting will overrun, so let's leave a buffer.", "会議は予定より長引くと思うから、余裕を持たせておこう。"),
    ("Don't worry, I've sorted the hotel booking already.", "心配しないで、ホテルの予約はもう済ませてあるよ。"),
    ("She lives in a lovely flat just off the high street.", "彼女はメインストリートのすぐそばの素敵なアパートに住んでいます。"),
    ("Could you put the kettle on? I could murder a cup of tea.", "やかんをかけてくれる?お茶が本当に飲みたいの。"),
    ("The car park's full, we'll have to find somewhere else to park.", "駐車場が満車だから、どこか別の場所を探さないと。"),
    ("I'm gutted we missed the last train home.", "終電を逃してしまって本当に残念だ。"),
    ("Take the lift up to the second floor, the office is on your right.", "エレベーターで2階まで上がってください、オフィスは右手にあります。"),
]

# --- オーストラリア英語 ---
WORDS_AU: list[tuple[str, str, str, str, str, str]] = [
    ("servo", "コンビニ併設のガソリンスタンド(豪州)", "名詞", "We stopped at the servo on the highway to fill up the car and grab a coffee.", "オーストラリア英語", "450"),
    ("ute", "小型トラック、ピックアップトラック(豪州)", "名詞", "He loaded the tools into the back of his ute before heading to the job site.", "オーストラリア英語", "500"),
    ("footpath", "歩道(豪州・英式表現、米語のsidewalkに相当)", "名詞", "Watch out for cyclists riding along the footpath near the beach.", "オーストラリア英語", "450"),
    ("arvo", "午後(afternoonの略、豪州口語)", "名詞", "Let's catch up for a coffee this arvo if you're free.", "オーストラリア英語", "500"),
    ("brekkie", "朝食(breakfastの略、豪州口語)", "名詞", "We had a big brekkie of eggs and toast before the long drive.", "オーストラリア英語", "500"),
    ("barbie (barbecue)", "バーベキュー(豪州口語)", "名詞", "The neighbours invited us over for a barbie in the backyard on Saturday.", "オーストラリア英語", "450"),
    ("snag (sausage)", "ソーセージ(豪州口語、バーベキューでよく使う語)", "名詞", "Dad threw a few snags on the barbie for lunch.", "オーストラリア英語", "600"),
    ("capsicum", "ピーマン・パプリカ(豪州・英式表現、米語のbell pepperに相当)", "名詞", "The recipe calls for one red capsicum, sliced thinly.", "オーストラリア英語", "550"),
    ("esky", "クーラーボックス、保冷ボックス(豪州、元は商標名)", "名詞", "Don't forget to pack the esky with ice and drinks for the beach.", "オーストラリア英語", "600"),
    ("thongs (footwear)", "ビーチサンダル(豪州、米語のflip-flopsに相当)", "名詞", "She kicked off her thongs before walking onto the sand.", "オーストラリア英語", "550"),
    ("sunnies", "サングラス(sunglassesの略、豪州口語)", "名詞", "Grab your sunnies, it's going to be a bright day at the beach.", "オーストラリア英語", "500"),
    ("mozzie", "蚊(mosquitoの略、豪州口語)", "名詞", "Put on some repellent or the mozzies will eat you alive out here.", "オーストラリア英語", "550"),
    ("bottle-o", "酒屋(bottle shopの略、豪州口語)", "名詞", "Can you swing by the bottle-o and grab a case of beer for the party?", "オーストラリア英語", "600"),
    ("Maccas", "マクドナルドの愛称(豪州口語)", "名詞", "The kids wanted to stop at Maccas for a quick lunch on the road trip.", "オーストラリア英語", "500"),
    ("tradie", "職人、技能工(電気工・配管工など、豪州口語)", "名詞", "We called a tradie to fix the leaking pipe under the sink.", "オーストラリア英語", "650"),
    ("uni", "大学(universityの略、豪州・英口語)", "名詞", "She's studying marketing at uni in Melbourne.", "オーストラリア英語", "450"),
    ("smoko", "仕事中の小休憩(豪州口語)", "名詞", "The workers took a quick smoko before finishing the last job of the day.", "オーストラリア英語", "650"),
    ("bloke", "男、やつ(豪州のくだけた表現)", "名詞", "The bloke at the counter was really helpful when I asked for directions.", "オーストラリア英語", "550"),
    ("mate", "相棒、君(親しい呼びかけとして頻用、豪州)", "名詞", "Thanks for the lift, mate, I really appreciate it.", "オーストラリア英語", "450"),
    ("reckon", "~だと思う、考える(豪州の口語動詞)", "動詞", "I reckon it's going to rain later, so bring an umbrella.", "オーストラリア英語", "500"),
    ("chuck a sickie", "仮病を使って仕事を休む(豪州の口語表現)", "動詞", "He decided to chuck a sickie and go to the beach instead of the office.", "オーストラリア英語", "700"),
    ("flat out", "非常に忙しい、大忙しの(豪州でよく使う表現)", "形容詞", "We've been flat out at work all week preparing for the product launch.", "オーストラリア英語", "650"),
    ("keen", "乗り気で、やる気がある(豪州でよく使う口語表現)", "形容詞", "Are you keen to go for a swim before dinner?", "オーストラリア英語", "550"),
    ("fair dinkum", "本物の、正真正銘の、本当の(豪州の定番表現)", "形容詞", "Is that story fair dinkum, or are you having me on?", "オーストラリア英語", "700"),
    ("she'll be right", "きっと大丈夫、なんとかなるさ(豪州の定番表現)", "間投詞", "Don't worry about the small delay, she'll be right on the day.", "オーストラリア英語", "650"),
    ("no worries (Australian)", "問題ないよ、どういたしまして(豪州の定番表現)", "間投詞", "No worries, I can help you carry those bags.", "オーストラリア英語", "500"),
]

PHRASES_AU: list[tuple[str, str]] = [
    ("No worries, take your time.", "大丈夫だよ、ゆっくりでいいから。"),
    ("Where's the nearest servo? I'm almost out of petrol.", "一番近いガソリンスタンドはどこ?ガソリンがほとんど残ってないんだ。"),
    ("Fancy a barbie this weekend?", "今週末バーベキューでもどう?"),
    ("I reckon we should leave early to beat the traffic.", "渋滞を避けるために早めに出発した方がいいと思うよ。"),
    ("Cheers, mate, I owe you one.", "ありがとう、恩に着るよ。"),
    ("She'll be right, don't stress about it.", "きっと大丈夫だよ、そんなに心配しないで。"),
    ("Can you grab me a flat white on your way in?", "来る途中にフラットホワイトを買ってきてくれる?"),
    ("I'm heading to uni, do you want a lift?", "大学に行くところなんだけど、乗っていく?"),
    ("Chuck your thongs on, we're going down to the beach.", "ビーチサンダルを履いて、ビーチに行こうよ。"),
    ("Is that fair dinkum, or are you pulling my leg?", "それ本当の話?それともからかってるの?"),
    ("We've been flat out at work this week.", "今週は仕事でとても忙しかったんだ。"),
    ("Do you want to grab a snag at the sausage sizzle outside the shops?", "お店の前でやっているソーセージ販売でソーセージを買って食べない?"),
    ("Pop the drinks in the esky before we head off.", "出発する前に飲み物をクーラーボックスに入れておいて。"),
    ("Good on ya for finishing the marathon!", "マラソン完走、よくやったね!"),
    ("I'll see you this arvo around three.", "今日の午後3時ごろに会おうね。"),
    ("Watch out for mozzies near the river at dusk.", "夕方、川の近くでは蚊に気をつけてね。"),
    ("The tradie said he'll come around Tuesday to fix the fence.", "その職人さんは火曜日にフェンスを直しに来ると言っていたよ。"),
    ("Let's stop at the next roadhouse for brekkie.", "次の休憩施設で朝食を食べよう。"),
    ("He's a good bloke, always happy to lend a hand.", "彼はいいやつで、いつも快く手を貸してくれる。"),
    ("Don't forget your sunnies, it gets really bright out on the water.", "サングラスを忘れないで、水上はすごく眩しくなるから。"),
]

# --- シンガポール英語 ---
WORDS_SG: list[tuple[str, str, str, str, str, str]] = [
    ("HDB", "住宅開発庁(シンガポールの公営住宅公団)、またはその公営住宅のこと", "名詞", "Most Singaporeans live in HDB flats rather than private condominiums.", "シンガポール英語", "500"),
    ("void deck", "(高層住宅棟の)1階にある吹き抜けの共用スペース", "名詞", "The wedding dinner was held at the void deck downstairs.", "シンガポール英語", "650"),
    ("hawker centre", "屋台街・フードコート(シンガポールの大衆食堂街)", "名詞", "Let's grab lunch at the hawker centre near the MRT station.", "シンガポール英語", "500"),
    ("CPF", "中央積立基金(シンガポールの強制貯蓄型社会保障制度)", "名詞", "A portion of your monthly salary is automatically contributed to your CPF account.", "シンガポール英語", "700"),
    ("MRT", "MRT、シンガポールの都市鉄道(地下鉄)", "名詞", "You can take the MRT directly from the airport to the city centre.", "シンガポール英語", "450"),
    ("COE", "自動車保有権証明書(車を購入する際に入札で取得する権利証)", "名詞", "Owning a car in Singapore is expensive because of the high cost of a COE.", "シンガポール英語", "750"),
    ("ERP", "電子道路課金制度(混雑時に自動課金される道路料金システム)", "名詞", "The ERP gantry automatically deducts a toll when you drive through the city centre during peak hours.", "シンガポール英語", "700"),
    ("wet market", "生鮮市場(魚・肉・野菜などを売る伝統的な市場)", "名詞", "My grandmother still prefers buying fresh vegetables at the wet market.", "シンガポール英語", "550"),
    ("GST", "物品サービス税(日本の消費税に相当)", "名詞", "The price shown on the menu already includes GST and service charge.", "シンガポール英語", "600"),
    ("NS", "国民役務(シンガポールの男子に課される兵役・国民奉仕制度、National Serviceの略)", "名詞", "Most young men in Singapore serve two years of NS after finishing school.", "シンガポール英語", "650"),
    ("BTO flat", "新築公営住宅(政府への申込制で建設される公営住宅、Build-To-Orderの略)", "名詞", "The young couple applied for a BTO flat in a newly developed estate.", "シンガポール英語", "700"),
    ("town council", "タウンカウンシル(地区の公営住宅団地を管理する自治組織)", "名詞", "Residents can contact the town council to report a broken lift in the block.", "シンガポール英語", "650"),
    ("polyclinic", "ポリクリニック(政府運営の総合診療所)", "名詞", "You can see a general practitioner at the polyclinic for a subsidised fee.", "シンガポール英語", "600"),
    ("statutory board", "法定機関(政府から独立した権限を持つ公的機関)", "名詞", "The Building and Construction Authority is a statutory board under the Ministry of National Development.", "シンガポール英語", "750"),
    ("PR (permanent resident)", "永住権保持者(Permanent Residentの略)", "名詞", "As a PR, she is eligible for subsidised healthcare but cannot vote in elections.", "シンガポール英語", "600"),
    ("resale flat", "中古公営住宅(すでに人が住んでいたHDB住宅の再販物件)", "名詞", "Resale flats in mature estates tend to be more expensive than new BTO flats.", "シンガポール英語", "700"),
    ("lah", "文末に置いて語調を和らげたり強めたりする間投詞(シングリッシュの代表的な語)", "間投詞", "Don't worry lah, everything will be fine.", "シンガポール英語", "450"),
    ("lor", "「まあそういうものだ」という諦め・当然の気持ちを表す終助詞(シングリッシュ)", "間投詞", "If the boss says so, then we just follow lor.", "シンガポール英語", "500"),
    ("kiasu", "人に負けたくない、機会を逃したくないという競争心・心配性を表す語(福建語由来)", "形容詞", "He arrived two hours early because he is so kiasu about getting a good seat.", "シンガポール英語", "650"),
    ("shiok", "とても気持ちいい、最高だという満足感を表す語(マレー語由来)", "形容詞", "This laksa is really shiok on a hot day.", "シンガポール英語", "600"),
    ("kopi", "コーヒー(マレー語由来、シンガポール・マレーシアの喫茶文化で使われる語)", "名詞", "I'll have a kopi-o kosong, please, black coffee with no sugar.", "シンガポール英語", "500"),
    ("makan", "食べる、食事をする(マレー語由来の動詞・名詞)", "動詞", "Let's makan first before we continue shopping.", "シンガポール英語", "550"),
    ("auntie (Singapore)", "見知らぬ年配の女性に親しみを込めて呼びかける語", "名詞", "The auntie at the hawker stall gave me an extra portion of rice.", "シンガポール英語", "500"),
    ("blur", "状況を把握できていない、ぼんやりしている様子を表す語", "形容詞", "Sorry, I'm a bit blur, can you explain the instructions again?", "シンガポール英語", "600"),
    ("paiseh", "きまりが悪い、恥ずかしい、申し訳ないという気持ちを表す語(福建語由来)", "形容詞", "Paiseh, I'm running ten minutes late for our meeting.", "シンガポール英語", "650"),
    ("can (Singapore)", "「できる」「大丈夫」という肯定・承諾を簡潔に表す返答表現", "間投詞", "\"Can you finish this by Friday?\" \"Can, no problem.\"", "シンガポール英語", "450"),
]

PHRASES_SG: list[tuple[str, str]] = [
    ("Can I get a plate of chicken rice, less oily please?", "チキンライスを一皿ください、油を控えめでお願いします。"),
    ("Which MRT line goes to Orchard Road from here?", "ここからオーチャード・ロードへはどのMRT路線で行けますか。"),
    ("Eh, this hawker stall's laksa is shiok, you must try it.", "ねえ、この屋台のラクサは最高だよ、絶対食べてみて。"),
    ("Sorry ah, I'm a bit blur about the office dress code, is it smart casual?", "すみません、オフィスの服装規定がよく分かっていなくて、スマートカジュアルでいいですか。"),
    ("We're meeting at the void deck at six before dinner.", "6時に(棟の)1階の共用スペースで待ち合わせてから夕食に行きます。"),
    ("My parents are collecting the keys to their new BTO flat next month.", "うちの両親は来月、新築の公営住宅の鍵を受け取る予定です。"),
    ("Just top up your transit card before you go through the MRT gantry.", "MRTの改札を通る前に交通系ICカードをチャージしてください。"),
    ("He's very kiasu, he queued for two hours just to get the opening-day discount.", "彼はとても負けず嫌いで、開店初日の割引を受けるために2時間も並んだ。"),
    ("Don't worry lah, the meeting can start a bit late, no one will mind.", "心配しないで、会議は少し遅れて始まっても誰も気にしないよ。"),
    ("The town council sent a notice about the lift maintenance this weekend.", "タウンカウンシルから今週末のエレベーター点検についてのお知らせが届きました。"),
    ("I need to top up my CPF account before the end of the year for the tax relief.", "税控除を受けるために年末までにCPF口座に積み立てを追加しないといけません。"),
    ("Auntie, how much for two bowls of soup noodles?", "おばさん、スープ麺2杯でいくらですか。"),
    ("The company reimburses the GST when you claim your business expenses.", "経費精算の際、会社がGST(消費税相当)分も負担してくれます。"),
    ("Paiseh, can you say that again? I didn't quite catch it.", "すみません、もう一度言ってもらえますか。よく聞き取れませんでした。"),
    ("Since it's raining, let's just grab a cab instead of walking to the hawker centre.", "雨が降っているので、屋台街まで歩かずタクシーを拾いましょう。"),
    ("New PRs need to register their address with the relevant authorities within a set time.", "新しく永住権を取得した人は、定められた期間内に住所を関連当局に登録する必要があります。"),
    ("Resale flat prices in this estate have gone up quite a lot this year.", "この団地の中古公営住宅の価格は今年かなり上がりました。"),
    ("Can, I'll send you the report by tomorrow morning.", "大丈夫です、明日の朝までに報告書をお送りします。"),
    ("During peak hours, the ERP charges are higher along this expressway.", "ピーク時間帯は、この高速道路沿いのERP(電子道路課金)の料金が高くなります。"),
    ("Let's makan before the movie starts, there's a good kopi stall just outside.", "映画が始まる前に何か食べましょう、すぐ外に美味しいコーヒー屋台がありますよ。"),
]

# --- インド英語 ---
WORDS_IN: list[tuple[str, str, str, str, str, str]] = [
    ("prepone", "予定を繰り上げる、前倒しにする(インド英語。postponeの反対)", "動詞", "Can we prepone the meeting to Monday instead of Wednesday?", "インド英語", "550"),
    ("out of station", "出張中で、街を離れている(インド英語)", "表現", "Sorry, I'm out of station this week, can we reschedule the call?", "インド英語", "600"),
    ("do the needful", "必要な対応をする、よろしくお願いします(インド英語のビジネスメール表現)", "表現", "Please do the needful and send the invoice by Friday.", "インド英語", "650"),
    ("revert", "(メールなどに)返信する、折り返し連絡する(インド英語で頻用)", "動詞", "I will revert to you by end of day with the updated figures.", "インド英語", "600"),
    ("good name", "お名前(丁寧な自己紹介表現。\"What is your good name?\")", "名詞", "May I know your good name, please?", "インド英語", "500"),
    ("kindly", "どうか、〜してください(依頼を丁寧にする副詞。ビジネス文書で多用)", "副詞", "Kindly find the attached report for your review.", "インド英語", "450"),
    ("intimate", "(正式に)知らせる、通知する(インド英語でinformの代わりに使われる)", "動詞", "Please intimate the office if you will be absent tomorrow.", "インド英語", "650"),
    ("as such", "それゆえに、そのため(インド英語ではthereforeに近い意味で使われる)", "副詞", "The client did not confirm the order; as such, we have not shipped the goods.", "インド英語", "600"),
    ("the same (Indian English)", "それ、同上のもの(直前に述べた事柄を指す。ビジネス文書で頻用)", "代名詞", "Kindly review the contract and confirm the same by tomorrow.", "インド英語", "500"),
    ("cousin-brother", "男のいとこ(インド英語特有の表現)", "名詞", "My cousin-brother is visiting from Delhi next week.", "インド英語", "500"),
    ("native place", "出身地、故郷", "名詞", "My native place is a small town in Kerala.", "インド英語", "500"),
    ("pass out (Indian English)", "卒業する(インド英語でgraduateの意味で使われる)", "動詞", "She passed out of engineering college last year.", "インド英語", "550"),
    ("updation", "更新(すること)(標準英語のupdatingに相当するインド英語の造語)", "名詞", "The updation of the database will be completed by tonight.", "インド英語", "650"),
    ("avail", "(サービスなどを)利用する", "動詞", "Employees can avail the health insurance scheme after three months.", "インド英語", "600"),
    ("shift (Indian English)", "引っ越す、転居する", "動詞", "We are shifting to a new flat next month.", "インド英語", "500"),
    ("batch-mate", "同期(同じ年に入学・入社した仲間)", "名詞", "He is my batch-mate from college; we joined the same year.", "インド英語", "550"),
    ("fresher", "新卒者、新入社員", "名詞", "The company hires many freshers straight out of engineering colleges.", "インド英語", "550"),
    ("mail (Indian English)", "メールを送る(emailの動詞として使われる)", "動詞", "I will mail you the presentation before the meeting.", "インド英語", "450"),
    ("timepass", "暇つぶし、時間つぶし(インド英語特有の口語表現)", "名詞", "Watching cricket on weekends is just timepass for him.", "インド英語", "500"),
    ("tension (Indian English)", "心配、ストレス(worryの意味で日常的に使われる)", "名詞", "Don't take tension, the report will be ready on time.", "インド英語", "500"),
    ("felicitate", "(公式の場で)祝福する、表彰する", "動詞", "The company felicitated the top performers at the annual function.", "インド英語", "650"),
    ("vacate", "(部屋・建物を)明け渡す、退去する", "動詞", "Tenants must vacate the flat by the end of the month.", "インド英語", "600"),
    ("redressal", "(苦情などの)解決、救済(grievance redressalなどで使用)", "名詞", "The office has set up a grievance redressal cell for employees.", "インド英語", "700"),
    ("chalk out", "(計画を)練る、立案する", "動詞", "The team chalked out a plan for the product launch.", "インド英語", "650"),
    ("cabin (Indian English)", "個室オフィス(インド英語で個人用の仕切られたオフィス部屋を指す)", "名詞", "The manager is in his cabin; please knock before entering.", "インド英語", "550"),
    ("lakh", "10万(インドの数の単位。ビジネス文書で頻用)", "名詞", "The project budget is around fifteen lakh rupees.", "インド英語", "600"),
]

PHRASES_IN: list[tuple[str, str]] = [
    ("Kindly do the needful at the earliest.", "何卒よろしくご対応のほどお願いいたします。"),
    ("I am out of station till Monday, will revert once I'm back.", "月曜まで出張中ですので、戻り次第折り返しご連絡します。"),
    ("Can we prepone tomorrow's meeting to 10 AM?", "明日の会議を午前10時に繰り上げられますか。"),
    ("Please find the same attached for your reference.", "ご参考までに、同じものを添付いたしましたのでご確認ください。"),
    ("What is your good name, sir?", "お名前を伺ってもよろしいでしょうか。"),
    ("He passed out of IIT Delhi with a degree in computer science.", "彼はデリー工科大学をコンピューターサイエンスの学位を取って卒業しました。"),
    ("My native place is Chennai, but I work in Bangalore.", "私の出身はチェンナイですが、バンガロールで働いています。"),
    ("The manager is not in his cabin right now, please come back after lunch.", "マネージャーは今個室にいませんので、昼食後にまたお越しください。"),
    ("We are shifting to a bigger office next quarter.", "来四半期にはもっと広いオフィスに移転します。"),
    ("Kindly intimate HR if you are taking leave next week.", "来週休みを取る場合は人事に必ずお知らせください。"),
    ("The auto driver charged fifty rupees for the ride.", "オート(三輪タクシー)の運転手は乗車料金として50ルピーを請求しました。"),
    ("Let's chalk out the project timeline before the client call.", "クライアントとの電話の前にプロジェクトのスケジュールを練っておきましょう。"),
    ("The new joinees will complete their training this week.", "新入社員たちは今週研修を終える予定です。"),
    ("Don't take tension, everything will be sorted out.", "心配しないで、すべて何とかなりますから。"),
    ("My cousin-brother is getting married next month, so I'll be on leave.", "いとこ(男性)が来月結婚するので、休暇を取ります。"),
    ("The society has organized a small function to felicitate the retiring guard.", "自治会は退職する警備員を表彰するために小さな式を開催しました。"),
    ("Tenants are requested to vacate the premises by the 30th.", "入居者の方は30日までに物件を明け渡すようお願いいたします。"),
    ("The budget for the new project is around twenty lakh rupees.", "新規プロジェクトの予算は約20万ルピーです。"),
    ("I have written to the vendor twice, but they haven't reverted yet.", "業者に2回連絡しましたが、まだ返信がありません。"),
    ("As such, we cannot process the refund without the original receipt.", "そのため、原本の領収書がないと返金の手続きができません。"),
]

WORDS = WORDS_UK + WORDS_AU + WORDS_SG + WORDS_IN
PHRASES_BY_SCENE = [
    ("イギリス英語の言い回し", PHRASES_UK),
    ("オーストラリア英語の言い回し", PHRASES_AU),
    ("シンガポール英語の言い回し", PHRASES_SG),
    ("インド英語の言い回し", PHRASES_IN),
]


def main() -> int:
    with db() as conn:
        existing_words = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing_words:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing_words.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")

    with db() as conn:
        existing_phrases = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        for scene, phrases in PHRASES_BY_SCENE:
            for en, ja in phrases:
                if en.lower() in existing_phrases:
                    p_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                existing_phrases.add(en.lower())
                p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
