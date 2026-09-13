# ruff: noqa: E501
"""文学(地域別)新規追加語(2026-09-13・authored by Claude)。
前回セッションでドラフトしたが保存先がセッションスクラッチパッドだったため
失われた、日本・中国・ロシア・欧州・英国・米国・その他地域の文学用語
計141語を再ドラフトしたもの。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_literature_regions_2026_09_13.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("Man'yōshū", "8世紀後半に成立したとされる、現存する日本最古の和歌集で、天皇から農民まで幅広い身分の詠み手による約4500首を収める。", "固有名詞", "The Man'yōshū is the oldest surviving anthology of Japanese poetry, containing poems by emperors and anonymous commoners alike.", "文学（日本）", "750"),
    ("Kokin Wakashū", "905年に醍醐天皇の命により編纂されたとされる最初の勅撰和歌集で、優美で技巧的な歌風により後の和歌の規範となった。", "固有名詞", "The Kokin Wakashū, the first imperially commissioned anthology of waka, set the standard for elegant courtly poetry for centuries.", "文学（日本）", "800"),
    ("haikai", "連歌から発展した、こっけいさや卑俗な言葉遣いを特徴とする日本の詩の様式で、後に俳句や俳文が派生する母体となった。", "名詞", "Haikai poetry grew out of the more formal renga tradition by embracing humor and colloquial language.", "文学（日本）", "800"),
    ("haibun", "俳句と散文を組み合わせ、旅の記録や日常の出来事を情感豊かに綴る日本の文学形式で、松尾芭蕉の紀行文で広く知られる。", "名詞", "Bashō's travel diaries are the most famous examples of haibun, blending prose narrative with haiku.", "文学（日本）", "850"),
    ("Oku no Hosomichi", "松尾芭蕉が1689年頃の東北・北陸への旅をもとに著したとされる紀行俳文集で、日本の紀行文学の最高峰とされる。", "固有名詞", "Oku no Hosomichi records Bashō's journey through northern Japan in a series of prose passages punctuated by haiku.", "文学（日本）", "800"),
    ("senryu", "俳句と同じ五・七・五の音数律を用いながら、季語を必要とせず人間や世相への風刺・こっけいを主題とする日本の短詩形。", "名詞", "Unlike haiku, senryu do not require a seasonal word and often poke fun at human folly.", "文学（日本）", "750"),
    ("kyōka", "和歌と同じ五・七・五・七・七の形式を用いながら、こっけいさや言葉遊びを主題とする日本の戯れ歌の一様式。", "名詞", "Kyōka poets delighted in puns and absurd exaggeration while keeping the traditional waka form intact.", "文学（日本）", "850"),
    ("Heike Monogatari", "平氏一門の栄華と滅亡を描いた軍記物語で、琵琶法師によって語り伝えられ、日本の無常観を代表する作品とされる。", "固有名詞", "The Heike Monogatari opens with a famous passage on the impermanence of all worldly glory.", "文学（日本）", "750"),
    ("otogi-zōshi", "室町時代を中心に作られた、絵を伴う短編の物語群で、庶民にも親しみやすい教訓的・娯楽的な内容を持つ。", "名詞", "Otogi-zōshi tales, often illustrated, were written for a wider and less aristocratic audience than earlier court literature.", "文学（日本）", "850"),
    ("gunki monogatari", "武士同士の合戦や争乱を主題とし、その経緯や登場人物の心情を描く日本の物語文学の一ジャンル。", "名詞", "Gunki monogatari such as the Heike Monogatari combine historical battle accounts with reflections on fate and impermanence.", "文学（日本）", "800"),
    ("nikki bungaku", "作者自身の日々の出来事や心境を仮名文でつづった、平安時代に確立した日本の日記文学のジャンル。", "名詞", "Nikki bungaku gave Heian-era women writers a literary form in which to record their private thoughts and experiences.", "文学（日本）", "800"),
    ("Tosa Nikki", "紀貫之が土佐から都への帰路をもとに著したとされる日記文学で、男性でありながら女性の筆に仮託して仮名文で書いた点で知られる。", "固有名詞", "The Tosa Nikki is often cited as the first major work of nikki bungaku written in kana rather than classical Chinese.", "文学（日本）", "800"),
    ("Makura no Sōshi", "清少納言が宮廷生活での見聞や感想を機知に富んだ文章でつづった随筆で、日本の随筆文学の源流の一つとされる。", "固有名詞", "Makura no Sōshi is celebrated for its witty lists and vivid observations of court life, rather than a continuous narrative.", "文学（日本）", "750"),
    ("Konjaku Monogatarishū", "平安後期に成立したとされる、インド・中国・日本の説話を集めた膨大な説話集で、各話が「今は昔」の書き出しで始まることで知られる。", "固有名詞", "Every tale in the Konjaku Monogatarishū begins with the same formula, roughly translated as 'Now it is the past...'", "文学（日本）", "850"),
    ("setsuwa", "教訓や仏教的な因果応報、こっけいな出来事などを短くまとめた、日本の伝統的な説話・逸話文学のジャンル。", "名詞", "Setsuwa collections mix Buddhist moral lessons with earthy, sometimes humorous anecdotes about ordinary people.", "文学（日本）", "800"),
    ("kibyōshi", "江戸中期以降に流行した、大人向けの風刺やこっけいを主題とする絵入りの草双紙で、黄色い表紙が特徴とされる。", "名詞", "Kibyōshi combined witty illustrations with satirical text aimed at a sophisticated adult readership in Edo.", "文学（日本）", "900"),
    ("sharebon", "江戸の遊里での会話や作法を、通(つう)や粋(いき)といった美意識とともに描いた、洒落を主眼とする戯作文学の一形式。", "名詞", "Sharebon focused on witty dialogue set in the pleasure quarters, prizing sophistication and stylish nonchalance.", "文学（日本）", "900"),
    ("yomihon", "挿絵よりも文章そのものによる筋立てや教訓性を重んじた、江戸後期に流行した比較的長編の読み物ジャンル。", "名詞", "Yomihon placed more weight on elaborate plotting and moral themes than on the illustrations that filled other Edo-period genres.", "文学（日本）", "900"),
    ("ningyō jōruri", "太夫による語り(浄瑠璃)と三味線の伴奏に合わせ、人形遣いが操る人形で演じる日本の伝統的な人形劇。現在は文楽の名でも知られる。", "名詞", "Ningyō jōruri combines chanted narration, shamisen music, and elaborately operated puppets to tell dramatic stories.", "文学（日本）", "800"),
    ("shishōsetsu", "作者自身の実体験や心境を、脚色を控えてほぼそのままに描く、日本近代文学に特徴的な私小説というジャンル。", "名詞", "In shishōsetsu, the narrator's experiences are often assumed to closely mirror the author's own private life.", "文学（日本）", "850"),
    ("Japanese naturalism", "社会や人間の姿を美化せず、ありのままに描こうとした、20世紀初頭の日本文学における潮流。私小説の成立にも大きな影響を与えた。", "名詞", "Japanese naturalism drew inspiration from European naturalism but developed its own emphasis on unflinching self-exposure.", "文学（日本）", "850"),
    ("Japanese proletarian literature", "労働者・農民の困窮や資本家との対立を主題とし、社会変革を志向した、1920〜30年代の日本の文学潮流。", "名詞", "Japanese proletarian literature sought to depict the harsh conditions of factory and farm workers under capitalism.", "文学（日本）", "850"),
    ("Four Great Classical Novels", "明清時代に成立した中国長編白話小説の中でも特に高い評価を受ける4作品、すなわち『三国志演義』『西遊記』『水滸伝』『紅楼夢』を指す総称。", "名詞", "The Four Great Classical Novels are widely regarded as the pinnacle of pre-modern Chinese vernacular fiction.", "文学（中国）", "750"),
    ("Book of Songs", "紀元前11世紀から前6世紀頃の詩篇305編を集めたとされる、現存する中国最古の詩集で、儒教の経典(五経)の一つにも数えられる。", "固有名詞", "The Book of Songs preserves folk songs, courtly hymns, and sacrificial odes from the early Zhou dynasty.", "文学（中国）", "800"),
    ("ci", "唐代に起こり宋代に最盛期を迎えたとされる、特定の曲の旋律に合わせて字数や声調が定められた、長短句からなる中国の詩の形式。", "名詞", "Unlike the more regular lines of Tang poetry, ci verse follows the irregular rhythms of a specific pre-existing melody.", "文学（中国）", "850"),
    ("fu", "対句や誇張表現を駆使し、事物や情景を絢爛たる言葉で描写する、漢代を中心に栄えた中国の韻文と散文の中間的な文学形式。", "名詞", "A fu typically piles up ornate, parallel descriptions of a single subject, such as a capital city or an imperial hunt.", "文学（中国）", "900"),
    ("yuefu", "もともと漢代の音楽官庁「楽府」が民間から採集した歌謡に由来する、口語的で物語性を持つ中国の詩の一形式。", "名詞", "Yuefu poems often narrate the hardships of soldiers, travelers, or abandoned wives in a direct, folk-song style.", "文学（中国）", "850"),
    ("zaju", "歌・せりふ・仕草を組み合わせ、通常4幕で構成される、元代に隆盛した中国の伝統的な演劇形式。", "名詞", "Yuan dynasty zaju typically combined spoken dialogue with arias sung by a single lead performer.", "文学（中国）", "850"),
    ("chuanqi", "日常を超えた奇異な出来事や恋愛譚を、六朝時代の志怪より洗練された文体と構成で描いた、唐代に発展した文言小説の一形式。", "名詞", "Tang chuanqi tales are more elaborately plotted than earlier zhiguai anecdotes, often centering on romance or supernatural encounters.", "文学（中国）", "900"),
    ("zhiguai", "幽霊・妖怪・不思議な出来事についての短い逸話を記録した、六朝時代に流行した中国の志怪小説の一形式。", "名詞", "Zhiguai anecdotes typically record a brief, strange encounter with a ghost or spirit as though reporting a real event.", "文学（中国）", "900"),
    ("gong'an fiction", "清廉な裁判官が知略によって難事件の真相を解き明かす筋立てを主題とする、中国の伝統的な公案小説というジャンル。", "名詞", "Gong'an fiction centers on an incorruptible magistrate who uses cunning and careful reasoning to solve baffling crimes.", "文学（中国）", "850"),
    ("caizi jiaren", "学識豊かな若い書生と美しく才知に長けた女性との恋愛と試練を描く、中国の伝統的な通俗小説・戯曲の類型。", "名詞", "Caizi jiaren stories typically follow a talented young scholar who falls in love with an equally gifted, beautiful woman.", "文学（中国）", "850"),
    ("xiaoshuo", "もともと取るに足らない巷の噂話・雑説を意味したが、後に中国語で小説・フィクション一般を指す語として定着した用語。", "名詞", "The term xiaoshuo originally referred to trivial street gossip, long before it came to mean 'fiction' in general.", "文学（中国）", "800"),
    ("parallel prose", "対句を多用し、四字句と六字句を基調として整えられた、韻律と対称性を重んじる中国の伝統的な美文体。", "名詞", "Parallel prose relies heavily on paired phrases of matching length, tone, and grammatical structure.", "文学（中国）", "900"),
    ("New Culture Movement", "儒教的伝統を批判し、口語文(白話文)や西洋の思想・科学の導入を通じて中国社会の近代化を目指した、1910年代半ばから20年代の思想・文学運動。", "固有名詞", "The New Culture Movement called for replacing classical literary Chinese with vernacular writing accessible to ordinary readers.", "文学（中国）", "800"),
    ("scar literature", "文化大革命によって受けた心の傷や社会の混乱を、その終結後に率直に描いた、1970年代末以降の中国文学の潮流。", "名詞", "Scar literature gave voice to the trauma and disillusionment many Chinese citizens experienced during the Cultural Revolution.", "文学（中国）", "800"),
    ("root-seeking literature", "西洋化・近代化の中で失われつつある、中国の土着的な文化・民俗・伝統に立ち返ろうとした、1980年代半ばの中国文学の潮流。", "名詞", "Root-seeking literature turned to rural folklore and regional traditions in search of a distinctly Chinese cultural identity.", "文学（中国）", "850"),
    ("misty poetry", "文化大革命後、政治的スローガンを排し、暗示的で難解なイメージを多用した、1970年代末から80年代の中国の現代詩の潮流。", "名詞", "Misty poetry was criticized by some conservative critics for being deliberately obscure and emotionally opaque.", "文学（中国）", "900"),
    ("Yan'an literature", "毛沢東の「延安の文芸講話」の方針のもと、労働者・農民・兵士への奉仕を文学の使命として掲げた、1940年代の中国共産党根拠地の文学。", "名詞", "Yan'an literature was expected to serve the political goals of the Communist Party and to be accessible to peasants and soldiers.", "文学（中国）", "900"),
    ("reportage literature", "事実の取材に基づきながらも、文学的な表現技法を用いて社会の実情を描く、中国で独自に発展したノンフィクション文学のジャンル。", "名詞", "Reportage literature blends factual reporting with the narrative techniques and emotional appeal of fiction.", "文学（中国）", "850"),
    ("Golden Age of Russian literature", "プーシキンから始まりドストエフスキーやトルストイに至る、19世紀のロシア文学が世界的な水準に達した時代を指す呼称。", "名詞", "The Golden Age of Russian literature is generally said to begin with Pushkin and culminate in the novels of Tolstoy and Dostoevsky.", "文学（ロシア）", "800"),
    ("Westernizer", "ロシア独自の伝統よりも西欧の制度・思想を取り入れて近代化すべきだと主張した、19世紀ロシアの知識人の一派。", "名詞", "Westernizers argued that Russia's future lay in adopting European institutions, science, and rational thought.", "文学（ロシア）", "900"),
    ("yurodivy", "世俗の常識を超えた奇矯な言動を通じて神の真理を示すとされる、ロシア正教の伝統に見られる「聖なる愚者」という人物像。", "名詞", "The yurodivy figure speaks uncomfortable truths that no one else in the story dares to voice, hidden behind a mask of madness.", "文学（ロシア）", "900"),
    ("skaz", "教養のない語り手の口調や方言、話し癖をそのまま模写して物語を語る、ロシア文学に特徴的な語りの技法。", "名詞", "In skaz narration, the story is filtered through the distinctive voice, dialect, and quirks of an uneducated narrator.", "文学（ロシア）", "900"),
    ("thick journal", "小説・詩・評論・時事論考などを一冊にまとめて掲載する、ロシアで独自に発達した分厚い総合文芸雑誌。", "名詞", "Serialized in a thick journal, a single novel might reach readers across the entire Russian empire before appearing as a book.", "文学（ロシア）", "850"),
    ("Sinyavsky-Daniel trial", "西側で偽名により作品を発表した2人の作家が反ソ的宣伝の罪で起訴された、1965〜66年のソ連の裁判。文学統制の象徴的事件とされる。", "固有名詞", "The Sinyavsky-Daniel trial marked one of the first times Soviet writers were publicly tried specifically for the content of their fiction.", "文学（ロシア）", "950"),
    ("Russian Symbolism", "象徴やイメージを通じて言葉では言い尽くせない神秘的・精神的な真理を暗示しようとした、19世紀末から20世紀初頭のロシアの詩の潮流。", "名詞", "Russian Symbolism sought to evoke mystical and spiritual truths through suggestive imagery rather than direct statement.", "文学（ロシア）", "900"),
    ("Acmeism", "あいまいな象徴よりも明快で具体的な言葉遣いと形式の均整を重んじた、ロシア象徴主義への反動として起こった20世紀初頭の詩の潮流。", "名詞", "Acmeism rejected the mystical vagueness of Symbolism in favor of precise, concrete language.", "文学（ロシア）", "900"),
    ("Russian Futurism", "既存の言語や美意識を破壊し、新しい造語や過激な表現形式を追求した、20世紀初頭ロシアの前衛的な詩・芸術運動。", "名詞", "Russian Futurism called for throwing traditional poets 'overboard from the ship of modernity' in favor of radical new language.", "文学（ロシア）", "900"),
    ("OBERIU", "不条理な論理や意味の破壊を用いた前衛的な詩・演劇を追求したが、スターリン体制下で弾圧された1920年代末レニングラードの芸術家集団。", "固有名詞", "OBERIU embraced absurdist logic and deliberate nonsense at a time when Soviet culture increasingly demanded clarity and optimism.", "文学（ロシア）", "950"),
    ("village prose", "都市化・集団化によって失われゆく農村の伝統的な暮らしと道徳を、郷愁を込めて描いた、1960〜70年代ソ連の文学潮流。", "名詞", "Village prose mourned the disappearance of traditional rural life under Soviet urbanization and collectivization.", "文学（ロシア）", "850"),
    ("byliny", "伝説的な英雄(ボガトィーリ)の武勇を朗誦形式で語り伝える、ロシアに古くから伝わる口承の叙事詩。", "名詞", "Byliny recount the heroic exploits of legendary warriors known as bogatyrs in a distinctive chanted verse form.", "文学（ロシア）", "900"),
    ("chernukha", "ソ連末期から1990年代にかけて、社会の暗部や暴力、絶望的な貧困を過度なまでにあからさまに描いた文学・映画の潮流。", "名詞", "Chernukha works depict poverty, violence, and despair with an almost relentless, unfiltered bleakness.", "文学（ロシア）", "900"),
    ("Thaw literature", "スターリン死後の検閲緩和期に、それまでタブーとされてきた粛清や強制収容所の実態などを扱うようになった、1950〜60年代ソ連の文学。", "名詞", "Thaw literature was able to touch on subjects, such as the Stalinist purges, that had been unthinkable to publish only years before.", "文学（ロシア）", "850"),
    ("polyphonic novel", "登場人物それぞれの声や視点が、作者の単一の視点に統合されず対等に響き合う小説の形式。批評家バフチンがドストエフスキー作品の分析で提唱した概念。", "名詞", "In a polyphonic novel, no single character's worldview, including the narrator's, is granted final authority over the others.", "文学（ロシア）", "950"),
    ("Russian émigré literature", "ロシア革命や内戦を逃れて国外に亡命した作家たちによって、主にパリやベルリンなどで書き継がれたロシア語文学の潮流。", "名詞", "Russian émigré literature preserved pre-revolutionary literary traditions among writers who had fled abroad after 1917.", "文学（ロシア）", "900"),
    ("Petersburg text", "幻想性・不条理・非人間的な官僚機構といった、サンクトペテルブルクという都市を舞台に繰り返し描かれてきた文学的イメージ群を指す、ロシア文学研究上の概念。", "名詞", "Scholars use the term 'Petersburg text' to describe the recurring myths of madness, bureaucracy, and unreality attached to the city in Russian fiction.", "文学（ロシア）", "950"),
    ("Weltschmerz", "現実の世界が理想からあまりにもかけ離れていることに由来する、深い倦怠感や憂鬱を意味するドイツ発祥の文学用語。", "名詞", "The poet's letters are filled with a pervasive Weltschmerz, a weary sense that the world can never live up to his ideals.", "文学（欧州）", "900"),
    ("roman fleuve", "一人の人物や一家族の生涯・複数世代を、独立した長編小説を連ねる形で描く、フランス発祥の大河小説という形式。", "名詞", "A roman fleuve follows its characters across multiple linked novels, often spanning several generations of a family.", "文学（欧州）", "900"),
    ("epistolary novel", "手紙(書簡)のやり取りという形式によって物語が進行していく小説の様式。", "名詞", "An epistolary novel unfolds entirely through the letters its characters exchange, without any conventional narrator.", "文学（欧州）", "800"),
    ("French Symbolism", "直接的な描写ではなく暗示や音楽性を通じて、理念や感情を象徴的に表現しようとした、19世紀末フランスの詩の運動。", "名詞", "French Symbolism favored suggestion and musicality over direct description, aiming to evoke rather than to state.", "文学（欧州）", "850"),
    ("Nordic noir", "陰鬱な気候や社会批評的な視点を背景に、犯罪と社会の暗部を描く、北欧発祥の犯罪小説というジャンル。", "名詞", "Nordic noir novels typically pair a bleak Scandinavian setting with sharp criticism of social institutions.", "文学（欧州）", "800"),
    ("commedia dell'arte", "決まった台本を持たず、仮面をつけた道化的な定型人物が即興でせりふを演じる、16世紀イタリアに起こった演劇様式。", "名詞", "Commedia dell'arte relied on stock masked characters and improvised dialogue rather than a fixed, written script.", "文学（欧州）", "850"),
    ("decadent movement", "退廃や人工美、感覚の耽溺を美として称揚し、道徳的な進歩や自然賛美に反発した、19世紀末ヨーロッパの文学・芸術運動。", "名詞", "The decadent movement celebrated artifice and sensory excess in defiance of conventional morality and belief in progress.", "文学（欧州）", "850"),
    ("existentialist literature", "人間が本質を持たずに存在し、自らの選択と行動によって自己を作り上げていくという思想を主題とする、20世紀ヨーロッパの文学潮流。", "名詞", "Existentialist literature explores the anxiety and freedom that come from confronting a universe without inherent meaning.", "文学（欧州）", "800"),
    ("fabliau", "機知に富んだ滑稽な筋立てで、しばしば下世話な題材や性愛を扱う、中世フランスの韻文による短編物語というジャンル。", "名詞", "A fabliau typically features a clever trickster who outwits a foolish husband, priest, or merchant for comic effect.", "文学（欧州）", "900"),
    ("chivalric romance", "騎士の武勇・冒険・恋愛を理想化して描く、中世ヨーロッパに広まった物語文学のジャンル。", "名詞", "Chivalric romance idealizes the knight as a paragon of courage, loyalty, and devoted love.", "文学（欧州）", "800"),
    ("courtly love", "身分の高い既婚の貴婦人への、献身的でしばしば成就しない恋慕を理想化して描く、中世ヨーロッパの文学的な恋愛観。", "名詞", "Courtly love idealizes a knight's devoted, often unconsummated passion for a noble lady of higher rank.", "文学（欧州）", "850"),
    ("roman noir", "暗い雰囲気と道徳的な曖昧さ、暴力を特徴とする、フランス発祥の犯罪・ゴシック小説というジャンル。", "名詞", "A roman noir plunges its characters into a morally ambiguous world of crime, violence, and shadowy urban settings.", "文学（欧州）", "900"),
    ("Künstlerroman", "芸術家としての主人公が経験や苦悩を通じて自らの創造的な使命を見出していく過程を描く、教養小説の一種であるドイツ発祥の小説形式。", "名詞", "A Künstlerroman traces its protagonist's growth not merely as a person, but specifically as an emerging artist.", "文学（欧州）", "900"),
    ("littérature engagée", "芸術のための芸術ではなく、社会や政治への関与・責任を積極的に引き受けるべきだとする、フランス発祥の文学理念。", "名詞", "Littérature engagée holds that writers cannot remain neutral bystanders to the political struggles of their time.", "文学（欧州）", "900"),
    ("verismo", "理想化を避け、庶民の日常生活や情念をありのままに描こうとした、19世紀末イタリアの文学・オペラの写実主義運動。", "名詞", "Verismo writers turned away from Romantic idealization to portray the harsh, everyday lives of ordinary people.", "文学（欧州）", "900"),
    ("Kunstmärchen", "民間伝承として口承で伝わってきた昔話とは異なり、個々の作家が独自に創作した、芸術的意図を持つドイツ発祥の文学的おとぎ話。", "名詞", "Unlike a folk tale passed down anonymously, a Kunstmärchen is a fairy tale consciously composed by a single identifiable author.", "文学（欧州）", "900"),
    ("Schauerroman", "幽霊や超自然的な恐怖、陰謀を主題とする、18世紀末から19世紀初頭にかけて流行したドイツ発祥のゴシック小説の一様式。", "名詞", "The Schauerroman traded in ghosts, secret societies, and supernatural terror much like its English Gothic counterparts.", "文学（欧州）", "900"),
    ("feuilleton", "小説の連載や文芸評論、軽妙な時事随筆などを掲載する、ヨーロッパの新聞に設けられた文化欄、またはそこに掲載される文章。", "名詞", "Many 19th-century European novels were first serialized in the feuilleton section of a daily newspaper.", "文学（欧州）", "900"),
    ("flâneur", "目的を持たず都市の街路をぶらつきながら、群衆や風景をひそかに観察する都市生活者を指す、フランス文学に由来する人物像。", "名詞", "The flâneur wanders the city streets with no particular destination, quietly observing the crowd from a detached distance.", "文学（欧州）", "900"),
    ("Biedermeier", "政治的な混乱を避け、家庭的で穏やかな市民生活の情景を好んで描いた、19世紀前半のドイツ語圏における文学・美術の様式。", "名詞", "Biedermeier literature favored modest domestic scenes and quiet contentment over grand political or revolutionary themes.", "文学（欧州）", "900"),
    ("Poet Laureate", "国家的な行事や出来事のために詩を作る役割を担う、英国君主により任命される桂冠詩人という公的な称号。", "名詞", "As Poet Laureate, she was expected to write verse marking major royal and national occasions.", "文学（英国）", "750"),
    ("Golden Age of Detective Fiction", "公正な手がかりの提示と論理的な謎解きを重視した、1920〜30年代を中心とする英国推理小説の隆盛期を指す呼称。", "名詞", "The Golden Age of Detective Fiction prized fair-play puzzles in which readers had a genuine chance to solve the crime themselves.", "文学（英国）", "800"),
    ("Detection Club", "推理小説の公正な謎解きの原則を守ることを会員に誓わせた、1930年に英国で設立された推理作家の親睦団体。", "固有名詞", "Members of the Detection Club swore an oath to give their fictional detectives no supernatural aid in solving crimes.", "文学（英国）", "900"),
    ("locked-room mystery", "被害者が外部から出入り不可能な密室の中で発見される謎を、論理的な推理によって解き明かす推理小説のサブジャンル。", "名詞", "In a locked-room mystery, the detective must explain how a crime was committed inside a room sealed from the outside.", "文学（英国）", "800"),
    ("Newgate novel", "実在した犯罪者の生涯を題材とし、しばしば犯罪者に同情的な視点を交えて描いた、1830年代英国で流行した小説のジャンル。", "名詞", "The Newgate novel drew its plots from the lives of real criminals, sometimes portraying them with unsettling sympathy.", "文学（英国）", "900"),
    ("silver fork novel", "上流階級の洗練された作法・流行・社交界の様子を細かく描写した、1820〜40年代英国で流行した小説のジャンル。", "名詞", "Silver fork novels catered to readers curious about the minute details of upper-class manners and fashionable society.", "文学（英国）", "900"),
    ("triple-decker novel", "出版社と貸本文庫の商業的な都合から、一つの物語を3巻に分けて刊行する、19世紀英国で一般的だった長編小説の出版形式。", "名詞", "Publishers favored the triple-decker novel partly because circulating libraries would pay to lend out all three volumes separately.", "文学（英国）", "800"),
    ("nonsense literature", "論理や意味の一貫性をあえて崩し、言葉遊びや不条理な想像力そのものを楽しむ、英国で特に発展した文学のジャンル。", "名詞", "Nonsense literature delights in wordplay and absurd logic for their own sake, rather than for any deeper hidden meaning.", "文学（英国）", "800"),
    ("school story", "全寮制学校での生徒同士の友情や対立、成長を主題とする、英国で伝統的に人気を博してきた児童・青少年文学のジャンル。", "名詞", "The school story typically follows a pupil's friendships, rivalries, and moral growth within a boarding school setting.", "文学（英国）", "800"),
    ("golden age of children's literature", "質の高い挿絵とともに、教訓性よりも純粋な楽しみを重んじる児童文学が数多く生み出された、19世紀後半から20世紀初頭にかけての英国の時代を指す呼称。", "名詞", "The golden age of children's literature saw a shift away from heavily moralistic tales toward stories written purely to delight young readers.", "文学（英国）", "800"),
    ("Windrush generation", "1948年から1970年代初頭にかけて、労働力として英国に招かれ移住したカリブ海諸国出身者とその家族を指す呼称。", "名詞", "Writers of the Windrush generation brought Caribbean voices, rhythms, and experiences into British literature for the first time.", "文学（英国）", "800"),
    ("Commonwealth literature", "かつて大英帝国の一部であった英連邦諸国の作家たちによって、英語で書かれた文学の総称。", "名詞", "Commonwealth literature brought perspectives from India, Africa, and the Caribbean into the wider world of English-language writing.", "文学（英国）", "800"),
    ("Vorticism", "機械文明の力強さやエネルギーを、鋭角的で断片化された形で表現しようとした、20世紀初頭英国の前衛芸術・文学運動。", "名詞", "Vorticism sought to capture the dynamic energy of the machine age through fragmented, angular forms in both art and poetry.", "文学（英国）", "900"),
    ("little magazine", "商業的な成功よりも実験的な作品の発表を重視し、少部数で発行される英米の前衛的な文芸雑誌の総称。", "名詞", "Many now-canonical modernist writers first found an audience through a little magazine rather than a mainstream publisher.", "文学（英国）", "800"),
    ("in-yer-face theatre", "暴力や性、タブーとされる題材を露骨に舞台上に突きつけることで観客に衝撃を与える、1990年代英国演劇の潮流。", "名詞", "In-yer-face theatre confronted audiences directly with graphic violence and taboo subject matter, refusing to look away.", "文学（英国）", "850"),
    ("state-of-the-nation play", "現代英国が直面する社会問題や国家全体の状況を、時事的な視点から総括的に描こうとする演劇のジャンル。", "名詞", "A state-of-the-nation play attempts to take stock of the pressing social and political issues facing the country as a whole.", "文学（英国）", "850"),
    ("regional novel", "特定の地方の風景・方言・共同体の暮らしを、その土地に根ざした視点から詳細に描く小説のジャンル。", "名詞", "A regional novel roots its story firmly in the landscape, dialect, and community life of a particular part of the country.", "文学（英国）", "800"),
    ("American Gothic", "米国の風土や歴史に根ざした不気味さ、罪の意識、破滅的な過去の重みを主題とする、米国文学のゴシック小説の一潮流。", "名詞", "American Gothic fiction transplants the genre's haunted castles and family curses into the American landscape and its own troubled history.", "文学（米国）", "800"),
    ("Lost Generation", "第一次世界大戦への幻滅を抱え、多くがパリなどヨーロッパに移り住んで創作活動を行った、1920年代米国の作家たちの一群を指す呼称。", "名詞", "Writers of the Lost Generation shared a profound disillusionment with the ideals that had led to the First World War.", "文学（米国）", "750"),
    ("American Renaissance", "ホーソーン、メルヴィル、ホイットマンらの傑作が相次いで発表された、1850年前後の米国文学の飛躍的な開花期を指す呼称。", "名詞", "The American Renaissance produced masterworks such as Moby-Dick and Leaves of Grass within just a few remarkable years.", "文学（米国）", "850"),
    ("Fireside Poets", "19世紀の米国で、家庭で声に出して読まれるにふさわしい平易な韻律と道徳的な主題によって国民的な人気を博した詩人たちの一群。", "名詞", "The Fireside Poets wrote accessible, rhythmic verse meant to be read aloud to the whole family gathered around the hearth.", "文学（米国）", "850"),
    ("American naturalism", "人間の運命は遺伝や環境、社会階級によってほぼ決定づけられるという見方のもとに、社会の過酷な現実を描いた、19世紀末から20世紀初頭の米国文学の潮流。", "名詞", "American naturalism portrays characters whose fates are largely determined by heredity, environment, and social class rather than free will.", "文学（米国）", "800"),
    ("muckraking", "企業の不正や政治腐敗、劣悪な労働環境などの社会問題を、綿密な取材によって暴き告発する調査報道・文学の手法。", "名詞", "Muckraking journalists exposed unsanitary conditions in the meatpacking industry through painstaking, on-the-ground investigation.", "文学（米国）", "800"),
    ("slave narrative", "奴隷制のもとに置かれた人々が、自らの体験した虐待や逃亡、自由の獲得を一人称で語った、米国文学の自伝的ジャンル。", "名詞", "Slave narratives gave firsthand testimony to the brutality of slavery, often to advance the abolitionist cause.", "文学（米国）", "800"),
    ("captivity narrative", "先住民に捕らえられた入植者が、その体験を宗教的な試練として語る、植民地時代の米国に特有の自伝的物語のジャンル。", "名詞", "A captivity narrative typically frames the ordeal of being taken captive by Native Americans as a test of the settler's religious faith.", "文学（米国）", "850"),
    ("tall tale", "現実にはあり得ないほどの誇張を、あたかも実話であるかのように大真面目に語ることで笑いを生む、米国の民間伝承的な物語の様式。", "名詞", "A tall tale piles up wildly exaggerated details while the narrator insists, with a straight face, that every word is true.", "文学（米国）", "750"),
    ("hardboiled fiction", "皮肉に満ちた簡潔な文体と、道徳的に曖昧な世界を生きるタフな探偵を特徴とする、米国発祥の犯罪小説のジャンル。", "名詞", "Hardboiled fiction favors terse, cynical prose and a tough detective navigating a morally compromised world.", "文学（米国）", "800"),
    ("New Journalism", "小説の技法(場面描写・視点・会話の再現など)を取り入れながら事実を伝える、1960〜70年代米国のノンフィクションの潮流。", "名詞", "New Journalism borrowed novelistic techniques such as scene-setting and interior monologue while still reporting factual events.", "文学（米国）", "800"),
    ("confessional poetry", "精神的な苦悩や家庭内の葛藤、性といった私的な体験を、包み隠さず赤裸々に語る、1950〜60年代米国の詩の潮流。", "名詞", "Confessional poetry lays bare intensely private experiences, such as mental illness and family trauma, with unusual candor.", "文学（米国）", "800"),
    ("Black Arts Movement", "公民権運動と並行して、アフリカ系米国人としての誇りと自己決定を文学・芸術を通じて主張した、1960〜70年代の米国の文化運動。", "固有名詞", "The Black Arts Movement called for a distinctly Black aesthetic that spoke directly to and for Black communities.", "文学（米国）", "850"),
    ("Chicano literature", "メキシコ系米国人としての二重の文化的アイデンティティや、差別・移民の経験を主題とする、米国の文学ジャンル。", "名詞", "Chicano literature often explores the tension of living between Mexican heritage and mainstream American culture.", "文学（米国）", "850"),
    ("Native American Renaissance", "ネイティブ・アメリカンの作家たちによる文学が、より広い読者と批評的評価を得るようになった、1960年代末以降の米国文学の潮流。", "名詞", "The Native American Renaissance brought unprecedented critical and popular attention to fiction and poetry by Native American writers.", "文学（米国）", "900"),
    ("metafiction", "物語の中で自らがフィクションであることを意識的に示し、創作の過程や虚構性そのものを主題として扱う小説の様式。", "名詞", "Metafiction constantly reminds the reader that they are reading a constructed story, sometimes through a narrator who comments on the writing process itself.", "文学（米国）", "850"),
    ("American postmodernism", "単一の確固たる真実や物語を疑い、パロディ・断片化・自己言及を用いて描く、20世紀後半米国の実験的な小説の潮流。", "名詞", "American postmodernism delights in blending high and low culture, historical fact and outright invention, often with a playful irony.", "文学（米国）", "850"),
    ("campus novel", "大学というキャンパスを舞台に、教員や学生の生活・人間関係・知的な虚栄心を風刺的に描く小説のジャンル。", "名詞", "A campus novel typically satirizes the petty rivalries and intellectual vanity of professors and students within a university setting.", "文学（米国）", "800"),
    ("dirty realism", "装飾を排した簡潔な文体で、労働者階級の荒んだ日常生活をありのままに描く、1980年代米国の小説の潮流を指す呼称。", "名詞", "Dirty realism strips away ornamentation to depict the bleak, unglamorous daily lives of working-class characters.", "文学（米国）", "850"),
    ("literary minimalism", "修飾語や説明を極力削ぎ落とし、簡潔な文と会話を積み重ねることで、行間に意味を暗示しようとする、米国発祥の小説の文体的潮流。", "名詞", "Literary minimalism relies on sparse, unadorned sentences, trusting readers to infer emotion from what is left unsaid.", "文学（米国）", "850"),
    ("Southern Renaissance", "敗北の歴史や人種問題と向き合いながら、地域固有の文学的伝統を花開かせた、1920〜50年代の米国南部文学の隆盛期。", "名詞", "The Southern Renaissance produced a wave of ambitious fiction grappling with the region's history of defeat and racial injustice.", "文学（米国）", "850"),
    ("American proletarian literature", "世界恐慌下の労働者階級の困窮や労働争議を主題とし、社会変革を志向した、1930年代米国の文学潮流。", "名詞", "American proletarian literature depicted the struggles of factory workers, farmers, and the unemployed during the Great Depression.", "文学（米国）", "850"),
    ("boom latinoamericano", "ラテンアメリカ文学が国際的な注目と評価を一気に獲得した、1960〜70年代の文学的高揚を指す呼称。", "名詞", "The boom latinoamericano brought Latin American fiction unprecedented international attention in translation.", "文学（その他）", "800"),
    ("indigenismo", "植民地支配以降に周縁化されてきた先住民の文化・権利を主題とし、その視点から社会を描き直そうとした、ラテンアメリカの文学・思想潮流。", "名詞", "Indigenismo sought to give voice and dignity to indigenous peoples long marginalized since the colonial era.", "文学（その他）", "850"),
    ("dictator novel", "独裁者という人物像を通して、ラテンアメリカの政治的抑圧と権力の腐敗を描く、この地域に特徴的な小説のジャンル。", "名詞", "The dictator novel uses the figure of an all-powerful strongman to explore themes of political repression and corruption.", "文学（その他）", "850"),
    ("crónica", "日常の出来事や社会の一断面を、ジャーナリズムと文学的な語りの技法を組み合わせて描く、ラテンアメリカの短編ノンフィクションのジャンル。", "名詞", "A crónica blends journalistic observation with literary style to capture a fleeting slice of everyday urban life.", "文学（その他）", "850"),
    ("lo real maravilloso", "ラテンアメリカの歴史や自然そのものに内在する驚異を、誇張や技巧に頼らずそのまま描けば足りるとする、キューバの作家アレホ・カルペンティエルが提唱した文学概念。", "名詞", "Alejo Carpentier argued that lo real maravilloso already existed in Latin America's own history and landscape, without needing to be invented.", "文学（その他）", "900"),
    ("corrido", "実際の事件や英雄的な人物の物語を、伝統的な旋律に乗せて語り伝える、メキシコの物語性の強い民謡バラードの様式。", "名詞", "A corrido narrates real or legendary events, such as a revolutionary battle or a folk hero's exploits, set to traditional melody.", "文学（その他）", "850"),
    ("Créolité", "単一のアフリカやフランスへの帰属意識ではなく、多様な文化が混淆したクレオール性そのものをアイデンティティの核とすべきだと唱えた、カリブ海フランス語圏の文学運動。", "名詞", "Créolité celebrates the mixed, hybrid cultural identity of the Caribbean rather than looking back to a single ancestral homeland.", "文学（その他）", "900"),
    ("dastan", "英雄の武勇や恋愛、魔法的な冒険を長大な物語として語る、ペルシャ語・ウルドゥー語圏に伝わる伝統的な口承・書承の物語形式。", "名詞", "A dastan weaves together heroic battles, romance, and magical adventure into one long, elaborately embellished story.", "文学（その他）", "900"),
    ("qasida", "単一の脚韻を貫き、しばしば君主や庇護者への頌歌として詠まれる、アラビア語・ペルシャ語圏に伝わる伝統的な長編の頌詩形式。", "名詞", "A qasida maintains a single rhyme throughout dozens of lines, often building toward praise of a ruler or patron.", "文学（その他）", "900"),
    ("maqama", "韻を踏んだ華麗な散文(サジュウ)を用いて、機知に富む放浪の主人公の冒険を短い挿話の連作として語る、アラビア語文学の伝統的な様式。", "名詞", "A maqama recounts the adventures of a clever, roguish wanderer through short, self-contained episodes in ornate rhymed prose.", "文学（その他）", "950"),
    ("adab", "単なる情報の伝達を超え、教養と美的洗練、道徳的な指針を兼ね備えるべきだとされる、古典アラビア語圏の人文的な散文文学の伝統。", "名詞", "Classical adab literature aimed to entertain, educate, and refine the reader's manners all at once.", "文学（その他）", "900"),
    ("Nahda", "西洋の思想・技術との接触を背景に、アラビア語の文学・思想・出版が近代化・活性化した、19世紀半ばから20世紀初頭にかけての文化的復興運動。", "固有名詞", "The Nahda brought a wave of new newspapers, novels, and translations that modernized Arabic literary culture.", "文学（その他）", "900"),
    ("rubaiyat", "人生の無常や酒、快楽への耽溺を主題とすることが多い、独立した4行の詩(ルバーイー)を集めたペルシャ語の詩集の形式。", "名詞", "A rubaiyat collects independent four-line verses that often meditate on mortality, wine, and the fleeting pleasures of life.", "文学（その他）", "850"),
    ("bhakti poetry", "儀式や身分の別を超え、神への熱烈で個人的な献身を主題とする、中世インドの信愛詩の伝統。", "名詞", "Bhakti poetry expresses passionate, personal devotion to a chosen deity, often bypassing formal ritual and caste distinctions.", "文学（その他）", "900"),
    ("kavya", "精巧な修辞技巧と韻律美を凝らして書かれた、古典サンスクリット文学における技巧的な詩・美文の伝統。", "名詞", "Kavya poetry prizes intricate wordplay, elaborate metaphor, and technical virtuosity over plain narrative clarity.", "文学（その他）", "900"),
    ("rasa theory", "文学・演劇作品が観客・読者の中に呼び起こす美的な感情の本質を、体系的に分類・分析しようとした、古典インドの美学理論。", "名詞", "Rasa theory analyzes the distinct aesthetic emotions, such as love or heroism, that a work of literature or drama is meant to evoke in its audience.", "文学（その他）", "950"),
    ("nazm", "ガザルのような一節ごとの独立性にとらわれず、一貫した主題を通して展開する、ウルドゥー語・ペルシャ語の詩の形式。", "名詞", "Unlike the self-contained couplets of a ghazal, a nazm develops a single, unified theme from beginning to end.", "文学（その他）", "900"),
    ("Progressive Writers' Movement", "社会的不正義や貧困、封建的因習を批判し、文学を社会変革の手段とすべきだと唱えた、1930年代以降の南アジアの文学運動。", "固有名詞", "The Progressive Writers' Movement urged writers across the Indian subcontinent to confront poverty, feudal oppression, and social injustice directly.", "文学（その他）", "900"),
    ("Négritude", "植民地支配下で否定されてきたアフリカ系の文化・美意識・誇りを積極的に肯定しようとした、20世紀前半のフランス語圏の文学・思想運動。", "固有名詞", "Négritude asserted pride in Black African culture and identity in defiance of colonial denigration.", "文学（その他）", "850"),
    ("orature", "文字による文学と対等な芸術形式として、語り・歌・儀礼など口頭による表現の伝統を指す、アフリカの文学研究で提唱された概念。", "名詞", "The term orature was coined to recognize spoken and performed traditions as literature in their own right, not merely as a precursor to writing.", "文学（その他）", "900"),
    ("praise poetry", "首長や英雄、祖先の功績や系譜を、様式化された誇張表現とともに称える、アフリカ南部を中心に伝わる口承の詩の伝統。", "名詞", "Praise poetry recounts the deeds and lineage of chiefs and ancestors using highly stylized, often exaggerated language.", "文学（その他）", "900"),
    ("Onitsha market literature", "安価な小冊子として大量に出版され、恋愛・道徳訓・時事的な話題を庶民向けに扱った、1950〜60年代ナイジェリアの大衆出版文化。", "名詞", "Onitsha market literature consisted of cheaply printed pamphlets sold in the marketplace, covering everything from romance to practical moral advice.", "文学（その他）", "950"),
    ("pantun", "前半で情景を描写し後半でそれに呼応する意味を述べる、対句形式の伝統的なマレー語の詩形。", "名詞", "A pantun typically pairs an opening image drawn from nature with a second line that reveals its deeper meaning through wordplay or rhyme.", "文学（その他）", "850"),
    ("wayang", "ラーマーヤナやマハーバーラタを題材とすることが多い、革製の人形や生身の役者によって物語を演じる、インドネシア・マレーシアの伝統的な影絵・人形劇。", "名詞", "Wayang performances often adapt episodes from the Ramayana and Mahabharata to reflect local Javanese values and humor.", "文学（その他）", "850"),
    ("hikayat", "王族の年代記や英雄譚、宗教的な物語などを扱う、マレー語の伝統的な散文物語のジャンル。", "名詞", "A hikayat might recount the genealogy of a royal court, the exploits of a legendary hero, or an episode from Islamic history.", "文学（その他）", "900"),
]


def main() -> None:
    with db() as conn:
        existing = set()
        for r in conn.execute("SELECT english FROM words").fetchall():
            existing.add(r["english"].lower())
        inserted = 0
        skipped = 0
        for english, japanese, pos, example, domain, level in WORDS:
            if english.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (english, japanese, pos, example, domain, level),
            )
            existing.add(english.lower())
            inserted += 1
        print("inserted=" + str(inserted) + " skipped=" + str(skipped))


if __name__ == "__main__":
    main()
