# ruff: noqa: E501  (data-heavy seed script)
"""Add safety / danger English + famous quotes, authored by Claude.

No app/OpenAI API calls. Purpose is COMPREHENSION & SELF-PROTECTION:
- Recognize police/robber commands and threats abroad and in movies.
- Recognize firearm/military/crime terms in news and film.
- Recognize (and avoid) drug slang and slurs/strong profanity.

Policy split:
- VISIBLE normal scenes (always shown, testable): emergency/self-defense
  commands, threats, firearms, military, crime. These are survival/literacy
  English the learner explicitly wants to understand.
- HIDDEN behind the 禁止用語 toggle (default OFF): drug slang, slurs, and the
  strongest profanity. The user asked for these to be written plainly (an
  on/off switch guards them). Each entry is a warning, never usage.

Also replaces the earlier CENSORED placeholders with plain entries.

Run:  python scripts/add_danger.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

BANNED_DOMAIN = "禁止用語"

# Visible safety scenes (NOT prefixed with 禁止 → never hidden).
SCENE_EMERGENCY = "緊急・護身（警察/脅し）"
SCENE_MILITARY = "銃器・軍事"
SCENE_CRIME = "犯罪・事件"
SCENE_QUOTES = "名言・名台詞"
# Hidden scenes (prefixed 禁止 → hidden unless the toggle is on).
SCENE_DRUGS = "禁止用語（薬物）"

# --- VISIBLE: emergency / self-defense commands & threats -------------------

PHRASES_EMERGENCY: list[tuple[str, str]] = [
    ("Freeze!", "動くな！〔警察・強盗の静止命令。映画頻出〕"),
    ("Don't move!", "動くな！"),
    ("Put your hands up!", "手を上げろ！"),
    ("Hands up!", "手を上げろ！"),
    ("Get down!", "伏せろ！"),
    ("Get on the ground!", "地面に伏せろ！"),
    ("Drop the weapon!", "武器を捨てろ！"),
    ("Drop it!", "(それを)捨てろ！"),
    ("Put your hands where I can see them!", "手が見える所に出せ！"),
    ("Don't shoot!", "撃つな！"),
    ("Hands behind your back.", "後ろで手を組め。"),
    ("You're under arrest.", "逮捕する。"),
    ("Step out of the vehicle.", "車から降りろ。"),
    ("Show me your hands.", "手を見せろ。"),
    ("Stay where you are.", "そこを動くな。"),
    ("Nobody move!", "全員動くな！"),
    ("This is a robbery.", "これは強盗だ。"),
    ("Give me your money.", "金を出せ。"),
    ("Hand over your wallet.", "財布をよこせ。"),
    ("Don't make a sound.", "声を出すな。"),
    ("Do as I say.", "言う通りにしろ。"),
    ("Or else.", "さもないと(ひどい目に遭うぞ)。〔脅し〕"),
    ("You'll regret this.", "後悔するぞ。〔脅し〕"),
    ("I'm warning you.", "警告するぞ。"),
    ("Stay back!", "下がれ！"),
    ("Back off!", "離れろ！"),
    ("Leave me alone!", "放っておいて！"),
    ("Call the police!", "警察を呼んで！"),
    ("Help! Somebody!", "助けて！誰か！"),
    ("Watch your back.", "背後に気をつけろ。〔警告／脅し〕"),
    ("I'll call security.", "警備を呼ぶぞ。"),
    ("Get out of my way.", "どけ。"),
    ("Don't try anything.", "妙な真似はするな。"),
    ("Keep your mouth shut.", "黙っていろ。〔口外するな・脅し〕"),
    ("Cooperate and you won't get hurt.", "従えば手は出さない。〔強盗の常套句〕"),
]

# --- VISIBLE: firearms / military -------------------------------------------

PHRASES_MILITARY: list[tuple[str, str]] = [
    ("Open fire!", "撃て！"),
    ("Cease fire!", "撃ち方やめ！"),
    ("Hold your fire.", "撃つな（待て）。"),
    ("Take cover!", "物陰に隠れろ！"),
    ("Get down, incoming!", "伏せろ、来るぞ！"),
    ("Reload!", "再装填！"),
    ("Lock and load.", "弾を込めて構えろ。"),
    ("We're under attack.", "攻撃を受けている。"),
    ("Fall back!", "後退しろ！"),
    ("Cover me!", "援護しろ！"),
    ("Man down!", "負傷者あり！"),
    ("Stand down.", "戦闘態勢を解け／引け。"),
    ("Enemy spotted.", "敵を発見。"),
    ("Hold the line.", "戦線を維持しろ。"),
    ("Move out!", "出発！／前進！"),
    ("Roger that.", "了解。"),
    ("Copy that.", "了解（受信した）。"),
    ("Requesting backup.", "応援を要請する。"),
    ("Surrender now.", "今すぐ投降しろ。"),
    ("We have a hostage situation.", "人質事件が発生している。"),
    ("Stand by.", "待機せよ。"),
    ("Mission accomplished.", "任務完了。"),
    ("Friendly fire.", "同士討ち（味方への誤射）。"),
    ("Eyes on the target.", "目標を視認。"),
    ("Permission to engage?", "交戦の許可を？"),
]

# --- VISIBLE: crime / incidents ---------------------------------------------

PHRASES_CRIME: list[tuple[str, str]] = [
    ("He was arrested for robbery.", "彼は強盗で逮捕された。"),
    ("They demanded a ransom.", "彼らは身代金を要求した。"),
    ("The suspect is armed and dangerous.", "容疑者は武装しており危険だ。"),
    ("She was taken hostage.", "彼女は人質に取られた。"),
    ("It was a hit-and-run.", "ひき逃げだった。"),
    ("They broke into the house.", "彼らは家に押し入った。"),
    ("He's wanted by the police.", "彼は警察に指名手配されている。"),
    ("He's out on bail.", "彼は保釈中だ。"),
    ("The witness testified in court.", "証人が法廷で証言した。"),
    ("The gang was smuggling weapons.", "そのギャングは武器を密輸していた。"),
    ("He pleaded not guilty.", "彼は無罪を主張した。"),
    ("They're holding him for questioning.", "取り調べのため拘束している。"),
    ("The robber fled the scene.", "強盗は現場から逃走した。"),
    ("Put out an APB.", "全車両に手配を出せ。"),
    ("He has a criminal record.", "彼には前科がある。"),
]

# --- HIDDEN: drug slang (recognition / avoidance only) ----------------------

PHRASES_DRUGS: list[tuple[str, str]] = [
    ("Do you want some weed?", "大麻いる？〔誘い文句。きっぱり断り関わらない〕"),
    ("He's high.", "彼はラリっている／酔っている。〔薬物・酩酊〕"),
    ("She's a junkie.", "彼女は薬物中毒者だ。〔侮蔑的〕"),
    ("Where's my stash?", "隠してたヤク(在庫)はどこだ。〔隠語〕"),
    ("He's the dealer.", "あいつが売人だ。〔密売人〕"),
    ("Let's score some coke.", "コカインを手に入れよう。〔犯罪。絶対に関わらない〕"),
    ("He overdosed.", "彼は過剰摂取した。"),
    ("Don't do drugs.", "薬物に手を出すな。〔注意喚起〕"),
    ("Are you holding?", "ブツ持ってる？〔隠語。麻薬所持を尋ねる〕"),
    ("Stay clean.", "薬物に手を出すな（断ち続けろ）。"),
]

# --- words --------------------------------------------------------------------
# (english, japanese, pos, example, domain, level)

WORDS_VISIBLE: list[tuple[str, str, str, str, str, str]] = [
    ("rifle", "ライフル銃", "名詞", "He carried a hunting rifle.", "軍事", "700"),
    ("pistol", "拳銃", "名詞", "The officer drew his pistol.", "軍事", "700"),
    ("firearm", "銃器", "名詞", "Carrying a firearm requires a license.", "軍事", "700"),
    ("weapon", "武器", "名詞", "Drop the weapon!", "軍事", "600"),
    ("trigger", "引き金", "名詞", "He pulled the trigger.", "軍事", "600"),
    ("ammunition", "弾薬", "名詞", "They ran out of ammunition.", "軍事", "800"),
    ("magazine", "弾倉", "名詞", "He loaded a fresh magazine.", "軍事", "700"),
    ("bullet", "弾丸", "名詞", "The bullet missed him.", "軍事", "600"),
    ("armed", "武装した", "形容詞", "The suspect is armed.", "軍事", "700"),
    ("ambush", "待ち伏せ・奇襲", "名詞", "They walked into an ambush.", "軍事", "800"),
    ("retreat", "撤退する・退却", "動詞", "The troops retreated.", "軍事", "700"),
    ("surrender", "降伏する", "動詞", "The soldiers surrendered.", "軍事", "700"),
    ("casualty", "死傷者", "名詞", "There were heavy casualties.", "軍事", "800"),
    ("troops", "軍隊・部隊", "名詞", "Troops were deployed.", "軍事", "700"),
    ("frontline", "最前線", "名詞", "He reported from the frontline.", "軍事", "700"),
    ("reinforcements", "増援", "名詞", "We're requesting reinforcements.", "軍事", "800"),
    ("hostage", "人質", "名詞", "She was taken hostage.", "法律", "700"),
    ("ransom", "身代金", "名詞", "They demanded a ransom.", "法律", "700"),
    ("robbery", "強盗", "名詞", "He was arrested for robbery.", "法律", "600"),
    ("burglar", "押し込み・空き巣", "名詞", "A burglar broke in.", "法律", "700"),
    ("smuggle", "密輸する", "動詞", "They smuggled weapons.", "法律", "700"),
    ("bribe", "賄賂・買収する", "名詞", "He was caught taking a bribe.", "法律", "700"),
    ("arrest", "逮捕する", "動詞", "The police arrested him.", "法律", "600"),
    ("handcuffs", "手錠", "名詞", "The officer put on the handcuffs.", "法律", "700"),
    ("assault", "暴行・襲撃", "名詞", "He was charged with assault.", "法律", "700"),
    ("kidnap", "誘拐する", "動詞", "They kidnapped the heir.", "法律", "700"),
    ("threat", "脅迫・脅威", "名詞", "He made a threat.", "法律", "600"),
    ("hijack", "乗っ取る", "動詞", "Hijackers seized the plane.", "法律", "800"),
    ("overdose", "過剰摂取", "名詞", "He died of an overdose.", "医療", "700"),
    ("interrogate", "尋問する", "動詞", "Police interrogated the suspect.", "法律", "800"),
]

# Hidden vocabulary (domain 禁止用語). Drug slang + slurs + strong profanity,
# written plainly per the user's request; gated by the OFF-by-default toggle.
# Each is a WARNING entry: meaning + 〔...〕. No usage encouragement.

WORDS_HIDDEN: list[tuple[str, str, str]] = [
    # drug slang
    ("weed", "(俗)大麻", "〔薬物の隠語。関わらない〕"),
    ("pot", "(俗)大麻", "〔薬物の隠語〕"),
    ("coke", "(俗)コカイン", "〔薬物の隠語。Coca-Colaの意もあるが文脈注意〕"),
    ("dope", "(俗)麻薬／(俗)すごい", "〔薬物の隠語。形容詞で『イケてる』の俗用も〕"),
    ("junkie", "(俗・侮蔑)薬物中毒者", "〔侮蔑語〕"),
    ("stash", "(俗)隠した在庫", "〔麻薬等を隠した蓄え〕"),
    ("stoned", "(俗)大麻で酩酊した", "〔薬物による酩酊〕"),
    ("dealer", "密売人", "〔麻薬の売人の意で使われる〕"),
    # strong profanity
    ("cunt", "(英・最悪級)女性器／最低の罵り", "〔英語最強クラスの侮辱。タブー〕"),
    ("motherfucker", "(最大級)くそ野郎", "〔極めて下品な罵り〕"),
    ("dickhead", "(侮辱)ばか・最低なやつ", "〔下品な侮辱〕"),
    ("douchebag", "(俗・侮辱)嫌なやつ", "〔下品な侮辱〕"),
    # slurs — recognition & self-protection only; NEVER use
    ("nigger", "黒人への最悪の人種差別語", "〔絶対に使わない。言われたら明確な攻撃〕"),
    ("faggot", "同性愛者への差別語", "〔使用厳禁の侮辱語〕"),
    ("chink", "東アジア系への人種差別語", "〔使用厳禁。日本人にも向けられる〕"),
    ("gook", "アジア系への蔑称(軍事スラング)", "〔戦争映画頻出。差別語。使わない〕"),
    ("spic", "ヒスパニック系への差別語", "〔使用厳禁〕"),
    ("kike", "ユダヤ人への差別語", "〔使用厳禁〕"),
    ("cracker", "(俗)白人への蔑称", "〔侮蔑語〕"),
    ("redneck", "(蔑称)無教養な田舎の白人", "〔侮蔑的〕"),
]

# --- famous quotes (+100) ----------------------------------------------------

QUOTES: list[tuple[str, str]] = [
    ("To be, or not to be: that is the question.", "生きるべきか死ぬべきか、それが問題だ。〔シェイクスピア『ハムレット』〕"),
    ("All the world's a stage.", "この世はすべて舞台。〔シェイクスピア『お気に召すまま』〕"),
    ("What's in a name? A rose by any other name would smell as sweet.", "名前が何だというの。バラはどんな名でも甘く香る。〔『ロミオとジュリエット』〕"),
    ("The course of true love never did run smooth.", "真実の恋の道は平坦ではない。〔『夏の夜の夢』〕"),
    ("Lord, what fools these mortals be!", "ああ、人間とはなんと愚かなことか。〔『夏の夜の夢』〕"),
    ("We know what we are, but know not what we may be.", "我々は今の自分は知るが、なり得る姿は知らない。〔『ハムレット』〕"),
    ("Cowards die many times before their deaths.", "臆病者は死ぬ前に何度も死ぬ。〔『ジュリアス・シーザー』〕"),
    ("The fault, dear Brutus, is not in our stars, but in ourselves.", "ブルータスよ、罪は星にではなく我ら自身にある。〔『ジュリアス・シーザー』〕"),
    ("Friends, Romans, countrymen, lend me your ears.", "友よ、ローマ人よ、同胞よ、耳を貸してくれ。〔『ジュリアス・シーザー』〕"),
    ("Et tu, Brute?", "ブルータス、お前もか。〔シェイクスピア『ジュリアス・シーザー』〕"),
    ("Some are born great, some achieve greatness.", "生まれながらに偉大な者もいれば、努力で偉大になる者もいる。〔『十二夜』〕"),
    ("If music be the food of love, play on.", "音楽が恋の糧なら、奏で続けよ。〔『十二夜』〕"),
    ("Uneasy lies the head that wears a crown.", "王冠を戴く頭は安らかに眠れぬ。〔『ヘンリー四世』〕"),
    ("The better part of valour is discretion.", "勇気の大半は分別である。〔『ヘンリー四世』〕"),
    ("Love all, trust a few, do wrong to none.", "皆を愛し、少数を信じ、誰にも悪をなすな。〔『終わりよければすべてよし』〕"),
    ("Though she be but little, she is fierce.", "小柄でも、彼女は激しい。〔『夏の夜の夢』〕"),
    ("Nothing will come of nothing.", "無からは何も生まれぬ。〔『リア王』〕"),
    ("There is nothing either good or bad, but thinking makes it so.", "物事に善悪はなく、考え方がそうさせる。〔『ハムレット』〕"),
    ("Hell is empty and all the devils are here.", "地獄は空っぽだ、悪魔はみなここにいる。〔『テンペスト』〕"),
    ("Veni, vidi, vici. (I came, I saw, I conquered.)", "来た、見た、勝った。〔ユリウス・カエサル〕"),
    ("The die is cast.", "賽は投げられた。〔ルビコン川を渡るカエサル〕"),
    ("Experience is the teacher of all things.", "経験はすべての師である。〔カエサル〕"),
    ("Men freely believe that which they desire.", "人は自分が望むことを進んで信じる。〔カエサル〕"),
    ("It was the best of times, it was the worst of times.", "それは最良の時代であり、最悪の時代であった。〔ディケンズ『二都物語』〕"),
    ("It is a far, far better thing that I do, than I have ever done.", "私が今なすことは、これまでで最も善きことだ。〔『二都物語』〕"),
    ("Please, sir, I want some more.", "お願いです、もう少しください。〔ディケンズ『オリバー・ツイスト』〕"),
    ("No one is useless in this world who lightens the burdens of another.", "他人の重荷を軽くする者は、この世で無用ではない。〔ディケンズ〕"),
    ("Have a heart that never hardens, a temper that never tires.", "決して硬くならぬ心と、疲れぬ気質を持て。〔ディケンズ〕"),
    ("Take nothing on its looks; take everything on evidence.", "見かけで判断せず、証拠で判断せよ。〔『大いなる遺産』〕"),
    ("I think, therefore I am.", "我思う、ゆえに我あり。〔デカルト〕"),
    ("Know thyself.", "汝自身を知れ。〔古代ギリシャ／ソクラテス〕"),
    ("The only true wisdom is in knowing you know nothing.", "唯一の真の知恵は、自分が何も知らないと知ることだ。〔ソクラテス〕"),
    ("We are what we repeatedly do. Excellence is a habit.", "我々は繰り返す行いそのものだ。卓越は習慣である。〔アリストテレス〕"),
    ("Wise men speak because they have something to say.", "賢者は語るべきことがあるから語る。〔プラトン〕"),
    ("If I have seen further, it is by standing on the shoulders of giants.", "私が遠くを見えたのは、巨人の肩に乗ったからだ。〔ニュートン〕"),
    ("And yet it moves.", "それでも地球は動く。〔ガリレオ〕"),
    ("Simplicity is the ultimate sophistication.", "簡潔さは究極の洗練である。〔レオナルド・ダ・ヴィンチ〕"),
    ("Imagination is more important than knowledge.", "想像力は知識より重要だ。〔アインシュタイン〕"),
    ("A person who never made a mistake never tried anything new.", "失敗したことのない者は、新しいことに挑んだことがない。〔アインシュタイン〕"),
    ("Genius is one percent inspiration and ninety-nine percent perspiration.", "天才とは1%のひらめきと99%の努力だ。〔エジソン〕"),
    ("Government of the people, by the people, for the people.", "人民の、人民による、人民のための政治。〔リンカーン〕"),
    ("Whatever you are, be a good one.", "何になるにせよ、良いものになれ。〔リンカーン〕"),
    ("Ask not what your country can do for you—ask what you can do for your country.", "国があなたに何をできるかではなく、あなたが国に何をできるかを問え。〔J.F.ケネディ〕"),
    ("I have a dream.", "私には夢がある。〔キング牧師〕"),
    ("Injustice anywhere is a threat to justice everywhere.", "どこかの不正は、あらゆる場所の正義への脅威だ。〔キング牧師〕"),
    ("We shall fight on the beaches; we shall never surrender.", "我々は浜辺で戦い、決して降伏しない。〔チャーチル〕"),
    ("Never, never, never give up.", "決して、決して、決してあきらめるな。〔チャーチル〕"),
    ("Success is not final, failure is not fatal.", "成功は最終ではなく、失敗は致命的ではない。〔チャーチル〕"),
    ("If you're going through hell, keep going.", "地獄の中を進んでいるなら、進み続けろ。〔チャーチル〕"),
    ("The only thing we have to fear is fear itself.", "我々が恐れるべきは恐れそのものだけだ。〔F.ルーズベルト〕"),
    ("The future belongs to those who believe in the beauty of their dreams.", "未来は、自分の夢の美しさを信じる者のものだ。〔E.ルーズベルト〕"),
    ("Believe you can and you're halfway there.", "できると信じれば、半分は達成している。〔T.ルーズベルト〕"),
    ("Be the change you wish to see in the world.", "世界に見たい変化に、あなた自身がなりなさい。〔ガンジー〕"),
    ("An eye for an eye makes the whole world blind.", "目には目をでは、世界中が盲目になる。〔ガンジー〕"),
    ("It always seems impossible until it's done.", "成し遂げるまでは、いつも不可能に見える。〔マンデラ〕"),
    ("The secret of getting ahead is getting started.", "前進の秘訣は、まず始めることだ。〔マーク・トウェイン〕"),
    ("Twenty years from now you will be more disappointed by the things you didn't do.", "20年後、あなたはやらなかったことに、より後悔する。〔マーク・トウェイン〕"),
    ("Be yourself; everyone else is already taken.", "自分らしくあれ。他の誰かはもう埋まっている。〔オスカー・ワイルド〕"),
    ("We are all in the gutter, but some of us are looking at the stars.", "我々は皆どぶの中にいるが、星を見上げる者もいる。〔オスカー・ワイルド〕"),
    ("Experience is the name everyone gives to their mistakes.", "経験とは、誰もが自分の失敗につける名前だ。〔オスカー・ワイルド〕"),
    ("Common sense is not so common.", "常識はそれほど一般的ではない。〔ヴォルテール〕"),
    ("An investment in knowledge pays the best interest.", "知識への投資が最も高い利息を生む。〔フランクリン〕"),
    ("By failing to prepare, you are preparing to fail.", "準備を怠るのは、失敗の準備をしているのだ。〔フランクリン〕"),
    ("That which does not kill us makes us stronger.", "我々を殺さぬものは、我々を強くする。〔ニーチェ〕"),
    ("A journey of a thousand miles begins with a single step.", "千里の道も一歩から。〔老子〕"),
    ("Know your enemy and know yourself.", "敵を知り己を知れば、百戦危うからず。〔孫子〕"),
    ("Appear weak when you are strong, and strong when you are weak.", "強い時は弱く見せ、弱い時は強く見せよ。〔孫子〕"),
    ("It does not matter how slowly you go as long as you do not stop.", "止まりさえしなければ、どれだけ遅くても構わない。〔孔子〕"),
    ("Our greatest glory is in rising every time we fall.", "最大の栄光は倒れるたびに起き上がることにある。〔孔子〕"),
    ("Stay hungry, stay foolish.", "ハングリーであれ、愚かであれ。〔スティーブ・ジョブズ〕"),
    ("Your time is limited, so don't waste it living someone else's life.", "時間は限られている。他人の人生を生きて無駄にするな。〔ジョブズ〕"),
    ("Whether you think you can or you think you can't, you're right.", "できると思ってもできないと思っても、あなたは正しい。〔ヘンリー・フォード〕"),
    ("Life is what happens when you're busy making other plans.", "人生とは、別の計画に忙しい時に起こるものだ。〔ジョン・レノン〕"),
    ("Alone we can do so little; together we can do so much.", "一人でできることは少ないが、共になら多くを成せる。〔ヘレン・ケラー〕"),
    ("People will never forget how you made them feel.", "人は、あなたにどう感じさせられたかを決して忘れない。〔マヤ・アンジェロウ〕"),
    ("Go confidently in the direction of your dreams.", "自分の夢の方向へ、自信を持って進め。〔ソロー〕"),
    ("What lies within us matters more than what lies behind or before us.", "我々の内にあるものは、背後や前方にあるものより重要だ。〔エマソン〕"),
    ("Impossible is a word found only in the dictionary of fools.", "不可能とは愚者の辞書にのみある言葉だ。〔ナポレオン〕"),
    ("First, do no harm.", "まず、害をなすな。〔ヒポクラテス〕"),
    ("The unexamined life is not worth living.", "吟味されない人生は生きるに値しない。〔ソクラテス〕"),
    ("I came, I saw, I conquered.", "来た、見た、勝った。〔カエサル〕"),
    ("Veni, vidi, amavi.", "(もじり)来た、見た、愛した。〔ラテン語の決まり文句〕"),
    ("Fortune favors the bold.", "幸運は勇者に味方する。〔ラテン語の格言〕"),
    ("Carpe diem. (Seize the day.)", "今日という日を摘め（今を生きよ）。〔ホラティウス〕"),
    ("Memento mori. (Remember you must die.)", "死を忘れるな。〔ラテン語の格言〕"),
    ("Veritas. (Truth.)", "真実。〔ラテン語〕"),
    ("Cogito, ergo sum.", "我思う、ゆえに我あり（ラテン語原文）。〔デカルト〕"),
    ("The pen is mightier than the sword.", "ペンは剣よりも強し。〔E.B.リットン〕"),
    ("Knowledge is power.", "知は力なり。〔フランシス・ベーコン〕"),
    ("Give me liberty, or give me death!", "自由を与えよ、しからずんば死を。〔パトリック・ヘンリー〕"),
    ("That's one small step for man, one giant leap for mankind.", "これは一人の人間にとっては小さな一歩だが、人類にとっては偉大な飛躍だ。〔アームストロング〕"),
    ("Float like a butterfly, sting like a bee.", "蝶のように舞い、蜂のように刺す。〔モハメド・アリ〕"),
    ("Elementary, my dear Watson.", "初歩的なことだよ、ワトソン君。〔シャーロック・ホームズ〕"),
    ("Houston, we have a problem.", "ヒューストン、問題が発生した。〔アポロ13号〕"),
    ("May the Force be with you.", "フォースと共にあれ。〔『スター・ウォーズ』〕"),
    ("I'll be back.", "また戻ってくる。〔『ターミネーター』〕"),
    ("With great power comes great responsibility.", "大いなる力には大いなる責任が伴う。〔『スパイダーマン』〕"),
    ("Frankly, my dear, I don't give a damn.", "率直に言って、私はもうどうでもいい。〔『風と共に去りぬ』〕"),
    ("Here's looking at you, kid.", "君の瞳に乾杯。〔『カサブランカ』〕"),
    ("Keep your friends close, but your enemies closer.", "友は近くに、敵はもっと近くに置け。〔『ゴッドファーザー』〕"),
    ("Why so serious?", "なぜそんなに深刻なんだ？〔『ダークナイト』ジョーカー〕"),
    ("To infinity and beyond!", "無限の彼方へ、さあ行くぞ！〔『トイ・ストーリー』〕"),
    ("After all, tomorrow is another day.", "明日は明日の風が吹く。〔『風と共に去りぬ』〕"),
    ("The only way out is through.", "唯一の出口は、通り抜けることだ。〔ロバート・フロスト〕"),
    ("In the middle of difficulty lies opportunity.", "困難の中に好機がある。〔アインシュタイン〕"),
    ("Veni vidi, I conquered my fear.", "来て見て、恐れを克服した。〔現代の励まし表現〕"),
]


def main() -> int:
    with db() as conn:
        # 1) Replace earlier CENSORED placeholders (any english containing '*').
        del_w = conn.execute(
            "DELETE FROM words WHERE domain = ? AND english LIKE '%*%'",
            (BANNED_DOMAIN,),
        ).rowcount
        del_p = conn.execute(
            "DELETE FROM phrases WHERE scene LIKE '禁止%' AND english LIKE '%*%'"
        ).rowcount

        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }

        ph_added = ph_skipped = 0
        phrase_groups = [
            (SCENE_EMERGENCY, PHRASES_EMERGENCY),
            (SCENE_MILITARY, PHRASES_MILITARY),
            (SCENE_CRIME, PHRASES_CRIME),
            (SCENE_DRUGS, PHRASES_DRUGS),
            (SCENE_QUOTES, QUOTES),
        ]
        for scene, items in phrase_groups:
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
        for en, ja, pos, ex, domain, level in WORDS_VISIBLE:
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
        for en, ja, ex in WORDS_HIDDEN:
            if en.lower() in w_existing:
                w_skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, "", ex, BANNED_DOMAIN, "700"),
            )
            w_existing.add(en.lower())
            w_added += 1

    print(f"cleanup: removed censored words={del_w} phrases={del_p}")
    print(f"phrases: +{ph_added} (skipped {ph_skipped})  [quotes={len(QUOTES)}]")
    print(f"words:   +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print(
            "totals -> phrases:",
            conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0],
            "words:",
            conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
            "/ banned words:",
            conn.execute(
                "SELECT COUNT(*) FROM words WHERE domain = ?", (BANNED_DOMAIN,)
            ).fetchone()[0],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
