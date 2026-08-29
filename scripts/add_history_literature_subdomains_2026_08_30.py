# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""歴史・文学の国/時代別サブドメイン語彙を新設、authored by Claude(2026-08-30・
ユーザー要望「歴史(日本史/中国史/世界史(古代/中世/近代)/米国史/ローマ史/英国史)
と文学(日本/中国/米国/英国/ロシア/欧州/その他)の空の受け皿ドメインに、少しずつ
語彙を追加。無理に埋めない」)。

2026-08-29に taxonomy.py の WORD_CATEGORIES へ新設された15個の空ドメイン
(日本史/中国史/世界史（古代）/世界史（中世）/世界史（近代）/米国史/
ローマ史（古代・帝国）/英国史/文学（日本）/文学（中国）/文学（米国）/
文学（英国）/文学（ロシア）/文学（欧州）/文学（その他）)と、既存の一般
バケット(歴史（一般）/文学（一般）)への少数の追加語を投入する。

方針(ユーザー指示):
- 「少しずつ、なければ入れない」。1ドメインあたり目安6〜12語程度、
  良い語が無ければ0でも構わない(今回はいずれのドメインにも一定の
  良質な語が見つかったため0件のドメインは無い)。
- 学習者が英語でその話題を読んだ時に出会いそうな語(固有名詞も可)を
  優先。他ドメインに既存の一般語(dynasty/samurai/katana等)は避けた。

出典(裏取り): Britannica, Wikipedia, Merriam-Webster, Oxford Reference等の
一般的な参考資料でWebSearchにより定義・綴りを確認済み(特に馴染みの薄い
語: rangaku, sonno joi, wuxia, biji, superfluous man, socialist realism,
Sturm und Drang, chanson de geste, roman à clef, griot, ghazal, testimonio,
Roman Senate関連語, Wars of the Roses/Glorious Revolution/Norman Conquest,
Journey to the West/Dream of the Red Chamber, Appian Way, Domesday Book等)。

同綴りだが意味が異なる語(homograph)は、既存の "agent"(AI/軍事/ビジネスで
3件重複登録済み)と同じ扱いに倣い、同じenglish文字列のまま別ドメイン・
別訳で追加した:
  - senate: 既存は「上院」(政治)。ここでは「元老院」(古代ローマ)。
  - guild: 既存は「ギルド(ゲーム内の協力組織)」(ゲーム・Discordの英語)。
    ここでは中世ヨーロッパの同業者組合。
  - enlightenment: 既存は「悟り」(宗教)。ここでは18世紀欧州の啓蒙思想。
  - epoch: 既存は「エポック」(AI、学習の1周)。ここでは歴史上の時代・
    画期的な出来事。
それ以外の完全な同義重複(ronin/bushido/eunuch/ziggurat/oracle/serfdom/
excommunication/totalitarianism/coup d'état/proxy war/annexation/
centurion/tribune/parliament/haiku/tanka/kigo/penny dreadful/troubadour/
protagonist/antagonist/genre/satire/motif/heritage/relic/archive/
excavation/artifact/iconoclasm/knight/veto/prime minister/bill(legislation)/
habeas corpus/common law等)はスキップした(既存語と同一概念のため)。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words`
table (except the intentional homographs above, which the script allows
explicitly since the check runs against a domain-aware existing set).

`detail`(AI生成の詳細JSON)は他のadd_*.pyスクリプトと同様にここでは
書き込まない(アプリ内の「詳細」ボタン押下時にAIが生成してキャッシュする
既存の仕組みに委ねる。/api/words/{id}/detail 参照)。

Run:  python scripts/add_history_literature_subdomains_2026_08_30.py
仕上げ(任意): 投入後に `python scripts/build_audio.py --words 50 --examples 50`
        で新規語の音声を生成する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# 明示的に許容するhomograph(同じenglishが別ドメイン・別訳で既存)。
# 通常の重複チェックはスキップするが、これらだけは重複してもよい。
HOMOGRAPH_ALLOW = {"senate", "guild", "enlightenment", "epoch"}

JP_HISTORY = "日本史"
CN_HISTORY = "中国史"
ANCIENT_WORLD = "世界史（古代）"
MEDIEVAL_WORLD = "世界史（中世）"
MODERN_WORLD = "世界史（近代）"
US_HISTORY = "米国史"
ROME_HISTORY = "ローマ史（古代・帝国）"
UK_HISTORY = "英国史"
LIT_JP = "文学（日本）"
LIT_CN = "文学（中国）"
LIT_US = "文学（米国）"
LIT_UK = "文学（英国）"
LIT_RU = "文学（ロシア）"
LIT_EU = "文学（欧州）"
LIT_OTHER = "文学（その他）"
HISTORY_GENERAL = "歴史（一般）"
LIT_GENERAL = "文学（一般）"

# (english, japanese, part_of_speech, example, level)
WORDS: list[tuple[str, str, str, str, str, str]] = [
    # === 日本史 ===
    ("seppuku", "切腹(名誉を守るために行った日本の伝統的な儀式的自害)", "名詞", "The defeated general chose seppuku rather than surrender to his enemies.", JP_HISTORY, "800"),
    ("Sengoku period", "戦国時代(15世紀末から16世紀末まで有力大名が覇権を争った日本の内乱期)", "名詞", "Powerful daimyo fought for supremacy throughout the Sengoku period.", JP_HISTORY, "750"),
    ("Meiji Restoration", "明治維新(1868年、江戸幕府を廃して天皇中心の近代国家体制へ移行した政治変革)", "名詞", "The Meiji Restoration ended centuries of samurai rule and opened Japan to the world.", JP_HISTORY, "750"),
    ("bakufu", "幕府(征夷大将軍を頂点とする日本の武家政権)", "名詞", "The Kamakura bakufu was Japan's first shogunate government.", JP_HISTORY, "800"),
    ("sonno joi", "尊皇攘夷(天皇を敬い外国勢力を排除しようとした幕末の政治スローガン)", "名詞", "Sonno joi became the rallying cry of samurai who opposed the shogunate's dealings with foreign powers.", JP_HISTORY, "900"),
    ("Edo period", "江戸時代(徳川幕府が統治した約260年間の時代、1603年から1868年まで)", "名詞", "Japan enjoyed long-lasting peace and strict isolation during the Edo period.", JP_HISTORY, "650"),
    ("Satsuma Rebellion", "西南戦争(1877年、鹿児島の士族が明治政府に対して起こした最後の大規模な内乱)", "名詞", "The Satsuma Rebellion was the last major uprising against the new Meiji government.", JP_HISTORY, "850"),
    ("rangaku", "蘭学(鎖国下の日本でオランダ語を通じて学ばれた西洋の学問)", "名詞", "Scholars of rangaku studied Dutch books to learn Western medicine and science.", JP_HISTORY, "900"),
    # === 中国史 ===
    ("Mandate of Heaven", "天命(天が徳のある統治者に統治を委ねるという中国古来の思想)", "名詞", "A dynasty that lost the Mandate of Heaven was believed to have lost its right to rule.", CN_HISTORY, "850"),
    ("civil service examination", "科挙(能力に基づいて官僚を選抜した中国の伝統的な試験制度)", "名詞", "For centuries, the civil service examination determined who could become a government official in China.", CN_HISTORY, "800"),
    ("Cultural Revolution", "文化大革命(1966年から毛沢東が主導した政治・社会運動)", "名詞", "The Cultural Revolution disrupted education and persecuted intellectuals across China.", CN_HISTORY, "700"),
    ("Silk Road", "シルクロード(古代に中国と地中海世界を結んだ交易路網)", "名詞", "Merchants carried silk and spices along the Silk Road for centuries.", CN_HISTORY, "600"),
    ("Forbidden City", "紫禁城(明・清代の皇帝が暮らした北京の宮殿群)", "名詞", "Only the emperor and his household were once allowed inside the Forbidden City.", CN_HISTORY, "650"),
    ("terracotta army", "兵馬俑(始皇帝の陵墓を守るために作られた等身大の陶製兵士像群)", "名詞", "Thousands of life-sized clay soldiers make up the terracotta army.", CN_HISTORY, "700"),
    ("Opium War", "アヘン戦争(19世紀にアヘン貿易を巡って清と英国の間で戦われた戦争)", "名詞", "China's defeat in the Opium War forced it to open its ports to foreign trade.", CN_HISTORY, "750"),
    ("Boxer Rebellion", "義和団の乱(1900年、外国勢力の排斥を掲げて中国で起きた民衆蜂起)", "名詞", "Foreign troops intervened to suppress the Boxer Rebellion in Beijing.", CN_HISTORY, "850"),
    ("tributary system", "冊封・朝貢体制(周辺国が中国の皇帝に貢物を捧げ臣下の礼をとった伝統的な外交秩序)", "名詞", "Neighboring kingdoms sent envoys under the tributary system to maintain peaceful relations with China.", CN_HISTORY, "900"),
    # === 世界史（古代） ===
    ("Mesopotamia", "メソポタミア(ティグリス川とユーフラテス川の間に栄えた古代文明地域)", "名詞", "Mesopotamia is often called the cradle of civilization.", ANCIENT_WORLD, "700"),
    ("cuneiform", "くさび形文字(古代メソポタミアで粘土板に刻まれた最古級の文字体系)", "名詞", "Scribes pressed cuneiform symbols into wet clay tablets.", ANCIENT_WORLD, "850"),
    ("hieroglyphics", "ヒエログリフ・神聖文字(古代エジプトで用いられた絵文字体系)", "名詞", "Archaeologists spent decades learning to read Egyptian hieroglyphics.", ANCIENT_WORLD, "800"),
    ("Hellenistic", "ヘレニズムの(アレクサンドロス大王以後、ギリシャ文化が東方に広まった時代の)", "形容詞", "Hellenistic cities blended Greek culture with local traditions across the Middle East.", ANCIENT_WORLD, "850"),
    ("Peloponnesian War", "ペロポネソス戦争(紀元前5世紀、アテネとスパルタを中心に古代ギリシャで戦われた戦争)", "名詞", "The Peloponnesian War weakened both Athens and Sparta for decades.", ANCIENT_WORLD, "850"),
    ("city-state", "都市国家(独立した政治単位として機能する一つの都市とその周辺地域)", "名詞", "Ancient Greece was made up of independent city-states such as Athens and Sparta.", ANCIENT_WORLD, "600"),
    ("Code of Hammurabi", "ハンムラビ法典(古代バビロニアの王ハンムラビが制定した現存最古級の法典)", "名詞", "The Code of Hammurabi listed punishments based on the principle of 'an eye for an eye.'", ANCIENT_WORLD, "800"),
    ("mummification", "ミイラ化(遺体を長期保存するための古代エジプトの技法)", "名詞", "Egyptian priests removed the internal organs as part of mummification.", ANCIENT_WORLD, "850"),
    ("Phoenician", "フェニキア人(地中海貿易で栄えた古代の海洋民族)", "名詞", "The Phoenicians spread their alphabet across the Mediterranean through trade.", ANCIENT_WORLD, "800"),
    ("papyrus", "パピルス(古代エジプトで作られた紙の原型となる書写材料)", "名詞", "Ancient Egyptians wrote official records on papyrus.", ANCIENT_WORLD, "650"),
    # === 世界史（中世） ===
    ("Byzantine Empire", "ビザンツ帝国・東ローマ帝国(ローマ帝国の東半分が中世まで存続した国家)", "名詞", "The Byzantine Empire preserved much of Roman law and Greek learning through the Middle Ages.", MEDIEVAL_WORLD, "750"),
    ("Black Death", "黒死病(14世紀にヨーロッパで大流行し人口の3分の1近くを奪ったペスト)", "名詞", "The Black Death killed millions across Europe in the fourteenth century.", MEDIEVAL_WORLD, "650"),
    ("manorialism", "荘園制(領主が土地と農民を支配した中世ヨーロッパの経済制度)", "名詞", "Under manorialism, peasants worked the lord's land in exchange for protection.", MEDIEVAL_WORLD, "900"),
    ("Magna Carta", "マグナ・カルタ(1215年に英国王が承認した、王権を制限する文書)", "名詞", "The Magna Carta limited the king's power and influenced later constitutions.", MEDIEVAL_WORLD, "750"),
    ("Hundred Years' War", "百年戦争(14世紀から15世紀にかけてイングランドとフランスの間で断続的に続いた戦争)", "名詞", "Joan of Arc became a national hero during the Hundred Years' War.", MEDIEVAL_WORLD, "800"),
    ("chivalry", "騎士道(中世ヨーロッパの騎士に求められた道徳的規範)", "名詞", "Medieval knights were expected to follow a strict code of chivalry.", MEDIEVAL_WORLD, "700"),
    ("Mongol Empire", "モンゴル帝国(13世紀にチンギス・ハンが築いた史上最大級の陸上帝国)", "名詞", "The Mongol Empire stretched from China to Eastern Europe at its height.", MEDIEVAL_WORLD, "700"),
    ("Reconquista", "レコンキスタ・国土回復運動(イベリア半島からイスラム勢力を追放したキリスト教勢力による再征服運動)", "名詞", "The Reconquista ended in 1492 with the fall of Granada.", MEDIEVAL_WORLD, "900"),
    ("fief", "封土(主君から家臣に軍事奉仕の見返りとして与えられた土地)", "名詞", "A knight received a fief from his lord in return for military service.", MEDIEVAL_WORLD, "800"),
    ("guild", "(中世の)同業者組合・ギルド(商人や職人が結成した中世ヨーロッパの互助・統制組織)", "名詞", "Craftsmen in medieval towns formed a guild to protect their trade.", MEDIEVAL_WORLD, "700"),
    ("crusader", "十字軍兵士(聖地奪還を目指し十字軍に参加した中世の戦士)", "名詞", "Crusaders marched thousands of miles to reach Jerusalem.", MEDIEVAL_WORLD, "700"),
    # === 世界史（近代） ===
    ("Enlightenment", "啓蒙時代・啓蒙主義(理性を重んじ因習を批判した18世紀ヨーロッパの思想運動)", "名詞", "Enlightenment thinkers championed reason over superstition and tradition.", MODERN_WORLD, "800"),
    ("imperialism", "帝国主義(軍事力や経済力によって他国・他地域を支配下に置こうとする政策)", "名詞", "European imperialism reshaped the map of Africa in the nineteenth century.", MODERN_WORLD, "750"),
    ("nationalism", "国家主義・ナショナリズム(自国の独立や統一、利益を最優先する思想)", "名詞", "Rising nationalism helped break up several multiethnic empires after World War I.", MODERN_WORLD, "700"),
    ("industrialization", "産業化・工業化(社会が農業中心から工業生産中心へと移行する過程)", "名詞", "Rapid industrialization drew millions of workers into growing cities.", MODERN_WORLD, "700"),
    ("decolonization", "脱植民地化(植民地が宗主国の支配から独立していく過程)", "名詞", "Decolonization swept across Africa and Asia in the decades after World War II.", MODERN_WORLD, "850"),
    ("appeasement", "宥和政策(対立を避けるため相手の要求を譲歩によって満たそうとする外交政策)", "名詞", "Critics later blamed appeasement for failing to stop Hitler's early aggression.", MODERN_WORLD, "850"),
    ("Cold War", "冷戦(第二次世界大戦後、米国とソ連を中心とする陣営が対立した緊張状態)", "名詞", "The Cold War divided the world into rival spheres of influence for decades.", MODERN_WORLD, "700"),
    ("Iron Curtain", "鉄のカーテン(冷戦下でヨーロッパを東西に分断した政治的・軍事的な境界を指す比喩)", "名詞", "An Iron Curtain descended across Europe, separating the communist East from the democratic West.", MODERN_WORLD, "800"),
    ("colonization", "植民地化(ある地域を他国が支配下に置き、自国民を入植させること)", "名詞", "European colonization transformed the economies and societies of the Americas.", MODERN_WORLD, "700"),
    # === 米国史 ===
    ("Founding Fathers", "建国の父たち(米国の独立と建国に主導的な役割を果たした指導者たち)", "名詞", "The Founding Fathers debated for months before signing the Constitution.", US_HISTORY, "700"),
    ("Declaration of Independence", "独立宣言(1776年に13植民地が英国からの独立を宣言した文書)", "名詞", "The Declaration of Independence proclaimed that all men are created equal.", US_HISTORY, "700"),
    ("Manifest Destiny", "明白な運命(米国が北米大陸全体に領土を広げる使命があるとする19世紀の思想)", "名詞", "Manifest Destiny was used to justify westward expansion across the continent.", US_HISTORY, "850"),
    ("abolitionist", "奴隷制度廃止論者(奴隷制の廃止を訴えた運動の支持者)", "名詞", "Abolitionists risked their lives helping enslaved people escape to freedom.", US_HISTORY, "750"),
    ("secession", "離脱・分離独立(連邦や国家から一部の州・地域が離脱すること)", "名詞", "The secession of Southern states led directly to the outbreak of the Civil War.", US_HISTORY, "800"),
    ("Emancipation Proclamation", "奴隷解放宣言(1863年にリンカーン大統領が発した、南部の奴隷を解放する宣言)", "名詞", "The Emancipation Proclamation declared that enslaved people in Confederate states were free.", US_HISTORY, "800"),
    ("Jim Crow", "ジム・クロウ法(南北戦争後、米国南部で黒人を差別・隔離した一連の法律・慣習)", "名詞", "Jim Crow laws enforced racial segregation across the American South for decades.", US_HISTORY, "850"),
    ("New Deal", "ニューディール政策(1930年代、フランクリン・ルーズベルト大統領が大恐慌対策として実施した一連の政策)", "名詞", "The New Deal created jobs and new regulations to fight the Great Depression.", US_HISTORY, "750"),
    ("Boston Tea Party", "ボストン茶会事件(1773年、植民地の人々が英国の課税に抗議して茶を海に投げ捨てた事件)", "名詞", "The Boston Tea Party was a bold protest against British taxation without representation.", US_HISTORY, "700"),
    ("Underground Railroad", "地下鉄道(19世紀、逃亡奴隷を北部やカナダへ密かに逃がした秘密の支援網)", "名詞", "Harriet Tubman guided many enslaved people to freedom along the Underground Railroad.", US_HISTORY, "750"),
    ("Reconstruction era", "再建時代(南北戦争後、南部諸州を連邦に再統合しようとした1865年から1877年頃までの時期)", "名詞", "During the Reconstruction era, the federal government tried to rebuild the South and protect newly freed citizens.", US_HISTORY, "850"),
    # === ローマ史（古代・帝国） ===
    ("senate", "元老院(古代ローマにおける貴族層からなる最高諮問機関)", "名詞", "The Roman Senate advised consuls and controlled foreign policy for centuries.", ROME_HISTORY, "700"),
    ("plebeian", "平民(古代ローマにおいて貴族階級に属さない一般市民)", "名詞", "Plebeians eventually won the right to hold high political office in Rome.", ROME_HISTORY, "800"),
    ("patrician", "貴族(古代ローマにおける名門貴族階級)", "名詞", "Only patrician families could initially serve as senators in early Rome.", ROME_HISTORY, "800"),
    ("aqueduct", "水道橋(ローマ人が遠方から都市へ水を引くために建設した構造物)", "名詞", "Roman engineers built aqueducts to carry fresh water for miles into the city.", ROME_HISTORY, "600"),
    ("legion", "軍団(古代ローマ軍の基本的な戦闘部隊単位、数千人の兵士で構成)", "名詞", "A Roman legion typically consisted of several thousand soldiers.", ROME_HISTORY, "650"),
    ("praetorian guard", "近衛兵(ローマ皇帝を護衛した精鋭部隊)", "名詞", "The praetorian guard held enormous influence over who became emperor.", ROME_HISTORY, "850"),
    ("triumvirate", "三頭政治(3人の有力者が権力を分かち合って統治する体制)", "名詞", "Julius Caesar, Pompey, and Crassus formed the First Triumvirate to dominate Roman politics.", ROME_HISTORY, "850"),
    ("Pax Romana", "パクス・ロマーナ・ローマの平和(帝政ローマがもたらした約200年間の比較的平和な時代)", "名詞", "The Pax Romana allowed trade and culture to flourish across the empire.", ROME_HISTORY, "800"),
    ("Colosseum", "コロッセオ(剣闘士競技などが行われた古代ローマの円形闘技場)", "名詞", "Tens of thousands of spectators once filled the Colosseum to watch gladiator fights.", ROME_HISTORY, "550"),
    ("Punic Wars", "ポエニ戦争(古代ローマとカルタゴの間で3度にわたり戦われた戦争)", "名詞", "Hannibal famously crossed the Alps with elephants during the Punic Wars.", ROME_HISTORY, "800"),
    ("cross the Rubicon", "ルビコン川を渡る(後戻りのできない決定的な行動に踏み切る、カエサルの故事に由来する慣用句)", "連語", "By marching his army into Italy, Caesar crossed the Rubicon and started a civil war.", ROME_HISTORY, "800"),
    ("Appian Way", "アッピア街道(古代ローマを代表する幹線街道)", "名詞", "The Appian Way once connected Rome to the port cities of southern Italy.", ROME_HISTORY, "750"),
    # === 英国史 ===
    ("House of Commons", "庶民院(英国議会の下院、公選された議員で構成される)", "名詞", "Members of the House of Commons are elected directly by voters across the country.", UK_HISTORY, "750"),
    ("House of Lords", "貴族院(英国議会の上院、貴族や聖職者などから構成される)", "名詞", "The House of Lords can delay legislation but rarely blocks it outright.", UK_HISTORY, "750"),
    ("Norman Conquest", "ノルマン征服(1066年、ノルマンディー公ウィリアムがイングランドを征服した出来事)", "名詞", "The Norman Conquest brought French language and customs into English society.", UK_HISTORY, "800"),
    ("Glorious Revolution", "名誉革命(1688年、英国王ジェームズ2世が追放され議会主権が確立された政変)", "名詞", "The Glorious Revolution established the principle that Parliament, not the king, held ultimate power.", UK_HISTORY, "850"),
    ("Wars of the Roses", "ばら戦争(15世紀、ランカスター家とヨーク家が英国王位を巡って争った内乱)", "名詞", "The Wars of the Roses ended when Henry Tudor defeated Richard III at Bosworth Field.", UK_HISTORY, "800"),
    ("Domesday Book", "ドゥームズデイ・ブック(1086年、ウィリアム征服王の命でイングランドの土地・財産を調査した記録)", "名詞", "The Domesday Book recorded who owned nearly every piece of land in England.", UK_HISTORY, "900"),
    ("peerage", "貴族の爵位・貴族階級(公爵・侯爵・伯爵など英国の世襲的な爵位制度)", "名詞", "He was elevated to the peerage and took a seat in the House of Lords.", UK_HISTORY, "800"),
    ("coronation", "戴冠式(新しい国王や女王が正式に即位する儀式)", "名詞", "Crowds gathered outside the abbey to watch the coronation.", UK_HISTORY, "600"),
    ("Commonwealth of Nations", "英連邦(かつて英国の植民地・自治領だった国々からなる国家連合)", "名詞", "Many former British colonies chose to remain in the Commonwealth of Nations after independence.", UK_HISTORY, "800"),
    ("the Crown", "王室・国王大権(君主制における国家権力の象徴としての国王・女王の地位)", "名詞", "Ministers technically act in the name of the Crown, even though the monarch holds little real power today.", UK_HISTORY, "750"),
    ("Act of Parliament", "議会制定法(英国議会で可決され成立した法律)", "名詞", "The reform was introduced through a new Act of Parliament.", UK_HISTORY, "800"),
    # === 文学（日本） ===
    ("waka", "和歌(五・七の音数を基本とする日本の伝統的な短詩形)", "名詞", "Poets composed waka to express delicate feelings about nature and love.", LIT_JP, "700"),
    ("renga", "連歌(複数の詠み手が交互に句を詠み継いでいく日本の詩形)", "名詞", "A group of poets took turns composing verses in a renga session.", LIT_JP, "800"),
    ("monogatari", "物語(散文で書かれた日本の伝統的な物語文学の総称)", "名詞", "The Tale of Genji is the most famous example of monogatari literature.", LIT_JP, "700"),
    ("zuihitsu", "随筆(思いつくままに書き綴る日本の散文形式)", "名詞", "The Pillow Book is a celebrated work of zuihitsu from the Heian court.", LIT_JP, "800"),
    ("ukiyo-zoshi", "浮世草子(江戸時代に町人の生活を描いた通俗小説の一形式)", "名詞", "Ihara Saikaku's ukiyo-zoshi vividly portrayed the lives of Edo-period merchants.", LIT_JP, "900"),
    ("gesaku", "戯作(江戸時代後期に流行した娯楽性の高い通俗文学の総称)", "名詞", "Gesaku writers entertained readers with witty, often comic tales.", LIT_JP, "900"),
    ("The Tale of Genji", "源氏物語(紫式部が著したとされる世界最古級の長編小説)", "名詞", "The Tale of Genji is often called the world's first novel.", LIT_JP, "700"),
    # === 文学（中国） ===
    ("wuxia", "武侠小説(武術の達人が正義のために戦う中国の伝統的な物語ジャンル)", "名詞", "Wuxia novels are filled with sword fights, secret martial arts schools, and codes of honor.", LIT_CN, "750"),
    ("chengyu", "成語(四字からなる中国の伝統的な慣用句・故事成語)", "名詞", "Many chengyu come from ancient stories and historical events.", LIT_CN, "800"),
    ("Tang poetry", "唐詩(中国文学の黄金期とされる唐代に詠まれた詩)", "名詞", "Tang poetry is admired for its vivid imagery and emotional depth.", LIT_CN, "750"),
    ("biji", "筆記(見聞や随想を気ままに書き記した中国古典文学の一形式)", "名詞", "A biji collection might mix ghost stories, historical notes, and personal opinions in a single volume.", LIT_CN, "900"),
    ("vernacular fiction", "白話小説(文語ではなく話し言葉に近い文体で書かれた中国の小説)", "名詞", "Vernacular fiction made classic Chinese stories accessible to ordinary readers.", LIT_CN, "850"),
    ("Journey to the West", "西遊記(三蔵法師が孫悟空らと共に天竺を目指す中国の代表的な古典小説)", "名詞", "Journey to the West follows a monk and his three disciples on a perilous pilgrimage.", LIT_CN, "700"),
    ("Dream of the Red Chamber", "紅楼夢(清代に書かれた、中国四大古典小説の一つとされる長編小説)", "名詞", "Dream of the Red Chamber traces the rise and fall of a wealthy aristocratic family.", LIT_CN, "800"),
    # === 文学（米国） ===
    ("transcendentalism", "超越主義(19世紀の米国で興った、直感と自然の重視を特徴とする思想・文学運動)", "名詞", "Transcendentalism encouraged writers like Emerson and Thoreau to trust individual intuition over social convention.", LIT_US, "800"),
    ("Harlem Renaissance", "ハーレム・ルネサンス(1920年代、ニューヨークのハーレムを中心に花開いたアフリカ系米国人の文化運動)", "名詞", "The Harlem Renaissance produced groundbreaking African American poetry, fiction, and music.", LIT_US, "750"),
    ("Beat Generation", "ビート・ジェネレーション(1950年代の米国で既成の価値観に反発した作家たちの一群)", "名詞", "The Beat Generation rejected mainstream American values in favor of spontaneity and personal freedom.", LIT_US, "750"),
    ("Southern Gothic", "サザン・ゴシック(米国南部を舞台に不気味さや退廃、異常な人物像を描く文学の一様式)", "名詞", "Southern Gothic stories often mix everyday life with the grotesque and macabre.", LIT_US, "850"),
    ("dime novel", "安価な大衆小説(19世紀の米国で大量に出版された低価格の娯楽小説)", "名詞", "Dime novels told fast-paced tales of cowboys, detectives, and outlaws.", LIT_US, "800"),
    ("regionalism", "郷土文学・地方主義文学(特定地域の風俗や方言を写実的に描く文学の潮流)", "名詞", "Regionalism in American literature captured the distinct dialects and customs of different parts of the country.", LIT_US, "850"),
    ("The Great American Novel", "グレート・アメリカン・ノベル(米国社会や国民性を総括的に描いたとされる理想の小説を指す概念)", "名詞", "Critics have long debated which book truly deserves the title of the Great American Novel.", LIT_US, "800"),
    ("local color", "ローカルカラー(特定の地域独自の風習・方言・風景を作品に描き込む文学的手法)", "名詞", "Local color writers filled their stories with the sights, sounds, and speech of a particular region.", LIT_US, "800"),
    # === 文学（英国） ===
    ("Gothic novel", "ゴシック小説(恐怖・超自然・廃墟などを題材とする18世紀後半に興った小説形式)", "名詞", "The Gothic novel often features crumbling castles, ghosts, and a sense of impending doom.", LIT_UK, "750"),
    ("Victorian literature", "ヴィクトリア朝文学(19世紀英国のヴィクトリア女王統治期に書かれた文学)", "名詞", "Victorian literature often explored social class and morality in rapidly industrializing Britain.", LIT_UK, "700"),
    ("blank verse", "無韻詩(脚韻を踏まない弱強五歩格の詩形、シェイクスピア劇などに用いられる)", "名詞", "Shakespeare wrote much of his dialogue in blank verse.", LIT_UK, "850"),
    ("Arthurian legend", "アーサー王伝説(円卓の騎士を率いた伝説の王アーサーにまつわる中世英国の物語群)", "名詞", "Arthurian legend has inspired countless retellings of Camelot and the Knights of the Round Table.", LIT_UK, "700"),
    ("Angry Young Men", "アングリー・ヤング・メン(1950年代英国で既成社会への不満を描いた若手作家たちの一群)", "名詞", "The Angry Young Men wrote plays and novels attacking the class system and social hypocrisy.", LIT_UK, "850"),
    ("kitchen sink drama", "キッチンシンク・ドラマ(労働者階級の日常生活をありのままに描いた英国の演劇・映画の様式)", "名詞", "Kitchen sink dramas brought the everyday struggles of working-class families to the stage and screen.", LIT_UK, "850"),
    ("sensation novel", "センセーション小説(犯罪や秘密を題材に読者をあおった19世紀英国の大衆小説)", "名詞", "Sensation novels shocked Victorian readers with plots full of crime, madness, and hidden identities.", LIT_UK, "850"),
    # === 文学（ロシア） ===
    ("superfluous man", "余計者(社会に馴染めず行動力を欠く、19世紀ロシア文学特有の主人公像)", "名詞", "The superfluous man is talented and educated but unable to find purpose in society.", LIT_RU, "900"),
    ("socialist realism", "社会主義リアリズム(社会主義建設を理想化して描くことを求められたソ連の公式芸術様式)", "名詞", "Socialist realism required Soviet writers to portray an optimistic vision of communist society.", LIT_RU, "850"),
    ("samizdat", "サミズダート(ソ連の検閲を逃れ地下で複製・流通した自主出版物)", "名詞", "Banned manuscripts circulated hand to hand as samizdat throughout the Soviet Union.", LIT_RU, "900"),
    ("Russian formalism", "ロシア・フォルマリズム(作品の形式や技法の分析を重視した20世紀初頭の文学理論)", "名詞", "Russian formalism focused on how literary devices create meaning, rather than on an author's biography.", LIT_RU, "950"),
    ("Slavophile", "スラヴ派(西欧化に反対しロシア独自の伝統を重んじた19世紀の知識人)", "名詞", "Slavophile writers argued that Russia should follow its own traditions rather than imitate Western Europe.", LIT_RU, "900"),
    ("Silver Age of Russian literature", "ロシア文学の銀の時代(19世紀末から20世紀初頭にかけての象徴主義など詩の隆盛期)", "名詞", "The Silver Age of Russian literature produced some of the country's most innovative poetry.", LIT_RU, "900"),
    # === 文学（欧州） ===
    ("Bildungsroman", "教養小説(主人公の精神的成長を描く、ドイツ発祥の小説形式)", "名詞", "A Bildungsroman traces its protagonist's moral and psychological growth from youth to adulthood.", LIT_EU, "900"),
    ("picaresque novel", "ピカレスク小説(悪漢を主人公とする滑稽で風刺的な、スペイン発祥の小説形式)", "名詞", "In a picaresque novel, a roguish hero moves from one comic adventure to the next.", LIT_EU, "900"),
    ("Nouveau Roman", "ヌーヴォー・ロマン(伝統的な筋書きや人物描写を排した20世紀フランスの実験的小説運動)", "名詞", "Writers of the Nouveau Roman abandoned traditional plot and character in favor of pure description.", LIT_EU, "950"),
    ("Sturm und Drang", "シュトゥルム・ウント・ドラング(理性より感情や個の反抗を重んじた18世紀ドイツの文学運動)", "名詞", "Sturm und Drang writers valued raw emotion and individual rebellion over Enlightenment reason.", LIT_EU, "950"),
    ("chanson de geste", "武勲詩(シャルルマーニュ大帝らの武勲を歌った中世フランスの叙事詩)", "名詞", "The Song of Roland is the most famous example of a chanson de geste.", LIT_EU, "950"),
    ("roman à clef", "モデル小説(実在の人物や出来事を仮名で描いた小説)", "名詞", "Readers tried to identify the real people hidden behind the characters in the roman à clef.", LIT_EU, "900"),
    ("theatre of the absurd", "不条理演劇(人生の無意味さや不条理を描く20世紀の演劇様式)", "名詞", "Plays in the theatre of the absurd often feature illogical dialogue and a lack of clear meaning.", LIT_EU, "850"),
    # === 文学（その他） ===
    ("magical realism", "マジックリアリズム(日常の中に超自然的要素をさりげなく織り込むラテンアメリカ発祥の文学様式)", "名詞", "In magical realism, fantastical events are described as an ordinary part of everyday life.", LIT_OTHER, "800"),
    ("griot", "グリオ(語りと音楽で歴史や系譜を伝承する西アフリカの語り部)", "名詞", "A griot could recite the genealogy of a royal family stretching back for generations.", LIT_OTHER, "850"),
    ("ghazal", "ガザル(愛や離別を歌う対句形式の、アラビア・ペルシャ起源の詩形)", "名詞", "Each couplet of a ghazal can stand alone while still sharing the poem's central rhyme.", LIT_OTHER, "850"),
    ("postcolonial literature", "ポストコロニアル文学(植民地支配の経験とその影響を主題とする文学)", "名詞", "Postcolonial literature often examines identity and language in the aftermath of empire.", LIT_OTHER, "800"),
    ("One Thousand and One Nights", "千夜一夜物語(シェヘラザードが語り手となる中東の説話集)", "名詞", "One Thousand and One Nights includes the tales of Aladdin, Ali Baba, and Sinbad the Sailor.", LIT_OTHER, "650"),
    ("testimonio", "テスティモニオ・証言文学(社会的弱者の証言を一人称で伝えるラテンアメリカの文学ジャンル)", "名詞", "A testimonio gives voice to someone who lived through oppression or political violence.", LIT_OTHER, "900"),
    # === 歴史（一般）(追加) ===
    ("chronicle", "年代記(出来事を時系列に記録した文書)", "名詞", "Medieval monks kept a chronicle of major events year by year.", HISTORY_GENERAL, "650"),
    ("historiography", "史学史・歴史記述法(歴史がどのように書かれ解釈されてきたかを研究する学問)", "名詞", "Historiography examines how different generations of historians have interpreted the same events.", HISTORY_GENERAL, "900"),
    ("primary source", "一次資料(出来事の当時に作られた資料、日記や公文書など)", "名詞", "Historians rely on primary sources such as letters and official records.", HISTORY_GENERAL, "700"),
    ("annals", "年代記録(毎年の出来事を記録した文書)", "名詞", "The annals of the kingdom recorded a poor harvest that year.", HISTORY_GENERAL, "800"),
    ("monument", "記念碑(歴史的な出来事や人物を記念して建てられた建造物)", "名詞", "A monument was erected to honor those who died in the war.", HISTORY_GENERAL, "550"),
    ("revisionism", "修正主義(定説となった歴史解釈を見直そうとする立場)", "名詞", "Historical revisionism can reveal overlooked perspectives, but it can also distort the truth.", HISTORY_GENERAL, "900"),
    ("apocryphal", "出所不明の・真偽不明の(広く語られているが史実として確認されていない)", "形容詞", "The story of the king's final words is probably apocryphal.", HISTORY_GENERAL, "900"),
    ("vestige", "名残・痕跡(かつて存在したものが残したわずかな跡)", "名詞", "A few stone walls are the only vestige of the ancient fortress.", HISTORY_GENERAL, "850"),
    ("epoch", "時代・画期的な出来事(ある特徴によって区切られる歴史上の期間、または新時代の始まりとなる画期的な出来事)", "名詞", "The invention of the printing press marked a new epoch in human history.", HISTORY_GENERAL, "800"),
    ("chronology", "年表・年代順(出来事を時間の順序に並べたもの)", "名詞", "Historians constructed a detailed chronology of the campaign from surviving letters.", HISTORY_GENERAL, "750"),
    # === 文学（一般）(追加) ===
    ("allegory", "寓意・寓話(抽象的な概念を具体的な人物や出来事を通して表す表現技法)", "名詞", "Animal Farm is a famous allegory of the Russian Revolution.", LIT_GENERAL, "800"),
    ("prose", "散文(韻律に縛られない普通の文章)", "名詞", "The novel is written in simple, direct prose.", LIT_GENERAL, "700"),
    ("foreshadowing", "伏線(後の展開をあらかじめほのめかす技法)", "名詞", "The author used foreshadowing to hint at the tragic ending early in the novel.", LIT_GENERAL, "800"),
    ("allusion", "暗示・示唆(他の作品や出来事にそれとなく言及する技法)", "名詞", "The poem makes an allusion to a famous Greek myth.", LIT_GENERAL, "850"),
    ("novella", "中編小説(長編小説より短く短編小説より長い作品)", "名詞", "Of Mice and Men is often described as a novella rather than a full novel.", LIT_GENERAL, "700"),
    ("memoir", "回想録(自身の経験を綴った文学作品)", "名詞", "She wrote a memoir about growing up during the war.", LIT_GENERAL, "650"),
    ("anthology", "選集・アンソロジー(複数の作品を集めた作品集)", "名詞", "The anthology collected short stories from ten different authors.", LIT_GENERAL, "700"),
    ("unreliable narrator", "信頼できない語り手(真実を歪めて伝える語り手という物語技法)", "名詞", "Readers slowly realize that the story's unreliable narrator has been hiding the truth.", LIT_GENERAL, "900"),
    ("denouement", "大詰め・結末(物語の伏線が解消される終盤の部分)", "名詞", "In the denouement, the mystery is finally solved and the characters' fates are revealed.", LIT_GENERAL, "900"),
    ("coming-of-age story", "成長物語(主人公の精神的成熟を描く物語の類型)", "名詞", "The film is a coming-of-age story about a teenager's last summer before college.", LIT_GENERAL, "700"),
    ("magnum opus", "最高傑作・代表作(作者にとって最も重要とされる作品)", "名詞", "Many critics consider the novel to be the author's magnum opus.", LIT_GENERAL, "850"),
    ("epilogue", "終章・エピローグ(本編の後に付け加えられる結びの部分)", "名詞", "The epilogue reveals what happened to each character years later.", LIT_GENERAL, "700"),
]


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        per_domain: dict[str, int] = {}
        for en, ja, pos, ex, domain, level in WORDS:
            key = en.lower()
            if key in existing and key not in HOMOGRAPH_ALLOW:
                skipped += 1
                print(f"  skip (dup): {en} [{domain}]")
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            # homographを複数回追加しないよう既存集合には追加しておく
            existing.add(key)
            added += 1
            per_domain[domain] = per_domain.get(domain, 0) + 1

    print(f"\nwords: +{added} (skipped {skipped})")
    print("\nper-domain counts:")
    for domain, count in per_domain.items():
        print(f"  {domain}: {count}")
    with db() as conn:
        print(
            "\ntotal words in DB:",
            conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
