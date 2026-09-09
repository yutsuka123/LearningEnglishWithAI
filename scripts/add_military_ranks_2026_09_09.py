# ruff: noqa: E501
"""軍事ドメインへの階級網羅トップアップ(2026-09-09・authored by Claude)。ユーザー提起「軍事、階級すべてあるといいかも。海軍・空軍・陸軍、昔の階級など」。既存の軍事ドメイン(184語)への追加。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_military_ranks_2026_09_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("private", "陸軍・海兵隊・空軍で使われる最下級の階級。米陸軍ではPrivate(E-1、階級章なし)とPrivate Two/PV2(E-2)の2段階があり、その上のprivate first class(上等兵)、さらに上のcorporal(伍長)へと続く、下士官(NCO)より下に位置する兵卒の最下位。二等兵。", "名詞", "He enlisted as a private and hoped to be promoted within a year.", "軍事", "620"),
    ("private first class", "米陸軍・海兵隊の階級で、private(二等兵)の上、corporal(伍長)の下に位置する、兵卒として最上位の階級。上等兵。", "名詞句", "After eight months of service, she was promoted to private first class.", "軍事", "680"),
    ("corporal", "陸軍・海兵隊の階級で、下士官(NCO)の最下位に位置する。private first class(上等兵)の上、sergeant(軍曹)の下。米陸軍では給与等級E-4は、指揮系統に入るcorporal(伍長)と、専門技術職で部下を指揮しないspecialist(技術兵長、階級章は異なるが同じ給与等級)の2つの道に分かれる点が特徴的。伍長。", "名詞", "The corporal was responsible for training the four privates in his unit.", "軍事", "650"),
    ("staff sergeant", "陸軍・海兵隊・空軍で使われる下士官の階級。米陸軍・海兵隊ではsergeant/corporal(軍曹・伍長)の上、sergeant first class等のより上級の下士官の下に位置する中堅下士官(E-6)。空軍では同じ階級名がE-5に当たるなど、名称は共通でも軍種によって給与等級が異なる点に注意が必要。三等軍曹。", "名詞句", "As a staff sergeant, he supervised a squad of eight soldiers.", "軍事", "680"),
    ("sergeant first class", "米陸軍の下士官の階級(E-7)で、staff sergeant(三等軍曹)の上、master sergeant/first sergeant(二等軍曹・先任軍曹)の下に位置する上級下士官。しばしば小隊のプラトーンサージェント(platoon sergeant)として、小隊長を務める中尉・少尉を実務面で補佐する。二等軍曹。", "名詞句", "The platoon's sergeant first class mentored the young lieutenant on tactical decisions.", "軍事", "720"),
    ("master sergeant", "米陸軍の下士官の階級(E-8)で、sergeant first class(E-7)の上に位置し、同じ給与等級のfirst sergeant(先任軍曹)と並ぶ。master sergeantは主に参謀・専門職としての上級下士官で、中隊の指揮系統を直接担うfirst sergeantとは職務が異なる。この上はsergeant major(最上級曹長、E-9)。二等軍曹上位(先任曹長級)。", "名詞句", "The master sergeant advised the battalion staff on logistics matters.", "軍事", "700"),
    ("first sergeant", "米陸軍・海兵隊で中隊(company)の先任下士官を務める階級・役職(E-8)。master sergeant(参謀職の上級曹長)と同じ給与等級だが、first sergeantは中隊長(大尉)を補佐し、部隊の規律・実務を直接統括する指揮系統上の役職である点が異なる。兵士から「トップ(Top)」という愛称で呼ばれることも多い。先任軍曹。", "名詞句", "The first sergeant kept the whole company running smoothly.", "軍事", "720"),
    ("sergeant major", "陸軍・海兵隊の下士官最上位の階級(E-9)。master sergeant/first sergeant(E-8)の上に位置し、大隊以上の部隊で参謀レベルの上級曹長として勤務する。指揮官を直接補佐する役職であるcommand sergeant majorとは異なり、参謀職としての最上級曹長を指すことが多い。最上級曹長。", "名詞句", "The sergeant major coordinated logistics for the entire brigade staff.", "軍事", "700"),
    ("command sergeant major", "米陸軍で大隊・旅団などの部隊指揮官(中佐・大佐)を直接補佐する最上級下士官の役職・階級(E-9)。同じ給与等級のsergeant majorが主に参謀職であるのに対し、command sergeant majorは指揮官の右腕として部隊全体の下士官・兵の規律と士気に責任を持つ、より重い責任を伴う地位とされる。その頂点にsergeant major of the Army(陸軍先任伍長)がある。", "名詞句", "The colonel relied heavily on his command sergeant major for troop morale issues.", "軍事", "750"),
    ("sergeant major of the army", "米陸軍全体における下士官の最高位の役職(1966年新設、階級自体はsergeant majorと同じE-9の特別職)。陸軍参謀総長(Chief of Staff of the Army)に対し、下士官に関わる問題について助言する首席顧問を務める、陸軍にただ一人しか存在しない唯一無二の地位。陸軍先任伍長。", "名詞句", "The Sergeant Major of the Army advises the Chief of Staff on enlisted issues.", "軍事", "780"),
    ("second lieutenant", "陸軍・海兵隊・空軍における最下位の尉官(将校)の階級(O-1)。士官学校卒業者や新任将校が最初に任官する階級で、その上はfirst lieutenant(中尉)。既存語lieutenant(中尉・少尉)のうち「少尉」に当たる、より具体的な呼称。海軍の同等階級はensign。少尉。", "名詞句", "Fresh out of officer training, she was commissioned as a second lieutenant.", "軍事", "650"),
    ("first lieutenant", "陸軍・海兵隊・空軍の尉官の階級(O-2)で、second lieutenant(少尉)の上、captain(大尉)の下に位置する。既存語lieutenant(中尉・少尉)のうち「中尉」に当たる具体的な呼称。海軍の同等階級はlieutenant junior grade。中尉。", "名詞句", "After two years of service, he was promoted to first lieutenant.", "軍事", "660"),
    ("lieutenant colonel", "陸軍・海兵隊・空軍の佐官の階級(O-5)で、既存語colonel(大佐)の一つ下、major(少佐)の一つ上に位置する。大隊(battalion)長を務めることが多い階級。海軍の同等階級はcommander。中佐。", "名詞句", "The lieutenant colonel commanded a battalion of nearly a thousand soldiers.", "軍事", "680"),
    ("brigadier general", "米軍の階級の一つで、少将(major general)の下、大佐(colonel)の上に位置する将官(一つ星)。旅団を指揮する将官として設けられた階級で、英連邦軍のbrigadier(准将)に相当する。准将。", "名詞句", "A brigadier general typically commands a brigade of several thousand soldiers.", "軍事", "700"),
    ("major general", "米軍の階級の一つで、lieutenant general(中将)の下、brigadier general(准将)の上に位置する将官(二つ星)。師団(division)を指揮することが多い階級。少将。", "名詞句", "The major general oversaw an entire division during the campaign.", "軍事", "700"),
    ("lieutenant general", "米軍の階級で、既存語general(大将、四つ星)の下、major general(少将)の上に位置する将官(三つ星)。軍団(corps)を指揮することが多い。中将。", "名詞句", "The lieutenant general led an army corps of over forty thousand troops.", "軍事", "720"),
    ("general of the army", "米陸軍史上、既存語general(大将、四つ星)のさらに上に一時的に設けられた五つ星の元帥級階級。第二次世界大戦中の1944年に創設され、これまでマーシャル・マッカーサー・アイゼンハワー・アーノルド・ブラッドレーの5名のみが叙せられた、事実上運用されていない最高位の階級。米陸軍元帥。", "名詞句", "Only five men in American history have held the rank of General of the Army.", "軍事", "800"),
    ("seaman", "海軍の階級区分で、最も下位の非任命(non-rated)階級群(seaman recruit・seaman apprentice・seamanなど)の総称、またはその中で最上位のE-3階級を指す。その上はpetty officer(下士官)。陸軍のprivateに相当する。水兵。", "名詞", "As a young seaman, he spent most of his day chipping paint and standing watch.", "軍事", "630"),
    ("petty officer", "海軍の下士官階級区分(E-4~E-6、petty officer third/second/first class)の総称。seaman(水兵)の上、chief petty officer(上級下士官)の下に位置する、海軍で最初のリーダー職を担う階級。海軍下士官。", "名詞句", "The petty officer was in charge of training the newest sailors on the ship.", "軍事", "660"),
    ("chief petty officer", "米海軍の上級下士官の階級(E-7)。petty officer(下士官)の上、senior chief petty officer(E-8)の下に位置する。海軍で最も伝統と権威を重んじる階級とされ、昇任の際には特別な通過儀礼(CPO Initiation)が行われることで知られる。海軍上等下士官。", "名詞句", "The chief petty officer ran the department almost independently of the officers.", "軍事", "690"),
    ("senior chief petty officer", "米海軍の階級(E-8)で、chief petty officer(E-7)の上、master chief petty officer(E-9)の下に位置する。海軍上級下士官。", "名詞句", "The senior chief petty officer mentored several chief petty officers under his supervision.", "軍事", "740"),
    ("master chief petty officer", "米海軍の下士官最高位の階級(E-9)。senior chief petty officer(E-8)の上に位置し、艦や部隊の最上級下士官として指揮官を補佐する。海軍の全下士官の頂点にはmaster chief petty officer of the Navyがただ一人存在する。海軍最上級下士官。", "名詞句", "The master chief petty officer served as the ship's senior enlisted advisor.", "軍事", "750"),
    ("master chief petty officer of the navy", "米海軍全体における下士官の最高位の役職(1967年新設、階級自体はmaster chief petty officerと同じE-9の特別職)。海軍作戦部長(Chief of Naval Operations)に対し、下士官に関わる問題について助言する首席顧問を務める、海軍にただ一人しか存在しない地位。陸軍のsergeant major of the Armyに相当する。海軍先任伍長。", "名詞句", "The Master Chief Petty Officer of the Navy represents enlisted sailors before Congress.", "軍事", "800"),
    ("ensign", "米海軍・沿岸警備隊の最下位の士官の階級(O-1)。陸軍のsecond lieutenant(少尉)に相当し、その上はlieutenant junior grade(海軍中尉)。歴史的には陸軍でも「部隊の旗を掲げる最下級の歩兵将校」を指す語として使われていたが、現在ではもっぱら海軍の階級名として定着している。海軍少尉。", "名詞", "As a newly commissioned ensign, he reported aboard his first ship with great excitement.", "軍事", "660"),
    ("lieutenant junior grade", "米海軍・沿岸警備隊の士官の階級(O-2)で、ensign(海軍少尉)の上、既存語lieutenant(海軍では大尉相当)の下に位置する。陸軍のfirst lieutenant(中尉)に相当する。海軍中尉。", "名詞句", "The lieutenant junior grade was assigned as the ship's assistant navigator.", "軍事", "700"),
    ("lieutenant commander", "米海軍・沿岸警備隊の佐官の階級(O-4)で、既存語lieutenant(海軍大尉相当)の上、commander(海軍中佐相当)の下に位置する。陸軍のmajor(少佐)に相当する。海軍少佐。", "名詞句", "The lieutenant commander served as the executive officer of a small patrol ship.", "軍事", "700"),
    ("rear admiral", "米海軍の将官(flag officer)の階級で、既存語captain(海軍大佐相当)の上に位置する最初の将官級。米海軍では一つ星のrear admiral (lower half)(O-7)と二つ星のrear admiral (upper half)(O-8)の2段階に分かれ、その上はvice admiral(海軍中将相当、O-9)。陸軍のbrigadier general・major generalにそれぞれ相当する。海軍少将級。", "名詞句", "The rear admiral took command of the carrier strike group.", "軍事", "700"),
    ("vice admiral", "米海軍の将官の階級(O-9、三つ星)。rear admiral (upper half)(少将相当)の上、既存語admiral(海軍大将相当、O-10)の下に位置する。陸軍のlieutenant general(中将)に相当する。海軍中将。", "名詞句", "The vice admiral commanded the entire Pacific fleet's surface forces.", "軍事", "720"),
    ("fleet admiral", "米海軍史上、既存語admiral(海軍大将、四つ星)のさらに上に一時的に設けられた五つ星の最高位の階級。第二次世界大戦中に創設され、リーヒ・キング・ニミッツ・ハルゼーの4名のみが叙せられ、以降任命例がない事実上運用されていない階級。英連邦海軍における同格の階級はAdmiral of the Fleet(語順が異なる点に注意)。米海軍元帥。", "名詞句", "Chester Nimitz was one of only four men ever promoted to fleet admiral in the U.S. Navy.", "軍事", "800"),
    ("airman", "米空軍の下士官・兵卒を指す総称、または具体的には最下級の兵卒に次ぐ階級(E-2)を指す。米空軍ではairman basic(E-1、無階級章)の上、airman first class(E-3)の下に位置する。陸軍のprivateに相当する。空軍二等兵(総称としては空軍下士官兵)。", "名詞", "The young airman was still learning the basics of aircraft maintenance.", "軍事", "630"),
    ("airman first class", "米空軍の階級(E-3)で、airman(空軍二等兵、E-2)の上、senior airman(E-4)の下に位置する。陸軍のprivate first class(上等兵)に相当する。", "名詞句", "As an airman first class, she was responsible for basic radar system checks.", "軍事", "680"),
    ("wing commander", "英空軍(RAF)およびその伝統を受け継ぐ英連邦諸国空軍に特有の佐官の階級。squadron leader(飛行隊長級)の上、group captain(基地司令官級)の下に位置し、米空軍のlieutenant colonel(中佐)にほぼ相当するとされる。米空軍には存在しない、英連邦特有の階級呼称。", "名詞句", "The wing commander was responsible for three fighter squadrons at the base.", "軍事", "750"),
    ("air marshal", "英空軍(RAF)およびその伝統を受け継ぐ英連邦諸国空軍に特有の将官の階級(三つ星)。air vice-marshal(二つ星)の上、air chief marshal(四つ星)の下に位置し、米空軍のlieutenant general(中将)にほぼ相当するとされる。米空軍には存在しない、英連邦特有の階級呼称。", "名詞句", "The air marshal oversaw all fighter operations across the region.", "軍事", "760"),
    ("group captain", "英空軍(RAF)およびその伝統を受け継ぐ英連邦諸国空軍に特有の階級で、wing commander(佐官級)の上、air commodore(准将級)の下に位置する。基地司令官などを務めることが多く、米空軍のcolonel(大佐)にほぼ相当するとされる。米空軍には存在しない、英連邦特有の階級呼称。", "名詞句", "The group captain commanded the entire air base and its support units.", "軍事", "760"),
    ("gunnery sergeant", "米海兵隊特有の下士官の階級(E-7)。staff sergeant(三等軍曹)の上、master sergeant/first sergeant(E-8)の下に位置する。愛称で\"Gunny\"(ガニー)と呼ばれることが多い、海兵隊で伝統的に重んじられる階級。", "名詞句", "The gunnery sergeant drilled the recruits relentlessly on the rifle range.", "軍事", "730"),
    ("master gunnery sergeant", "米海兵隊の下士官最高位の技術系階級(E-9)。master sergeant(E-8)の上に位置し、同じE-9のsergeant major(最上級曹長)が指揮系統上の役職であるのに対し、master gunnery sergeantは専門技術分野における最上級の助言役という位置づけの違いがある。愛称で\"Master Guns\"と呼ばれる。", "名詞句", "The master gunnery sergeant was the unit's top expert on artillery systems.", "軍事", "780"),
    ("commissioned officer", "大統領などの元首から任官辞令(commission)を受けて任命される将校の総称。下士官(non-commissioned officer)や準士官(warrant officer)より上位に位置し、second lieutenant/ensign(少尉)からgeneral/admiral(大将)までの全ての士官階級を含む。将校。", "名詞句", "Only a commissioned officer can be given formal command of a military unit.", "軍事", "650"),
    ("non-commissioned officer", "下士官の総称。commissioned officer(将校)のような任官辞令を受けずに、兵卒から昇進して指揮・監督権を得た階級で、corporal(伍長)からsergeant major(最上級曹長)までが該当する。しばしばNCOと略される。下士官。", "名詞句", "Non-commissioned officers are often called the backbone of the military.", "軍事", "650"),
    ("enlisted personnel", "commissioned officer(将校)やwarrant officer(準士官)を除く、一般に入隊契約に基づいて勤務する兵士・水兵・下士官の総称。最も下位のprivate/seaman/airmanから最上位のsergeant major/master chief petty officerまでを含む。下士官兵。", "名詞句", "The vast majority of a country's armed forces consists of enlisted personnel.", "軍事", "650"),
    ("warrant officer", "下士官(NCO)と将校(commissioned officer)の中間に位置する専門技術者の階級区分。米陸軍ではWO1(准位官)からCW5まで5段階あり、ヘリコプター操縦など高度な専門技能を持つ将校として扱われる。米空軍は1959年以降この階級を廃止している一方、陸軍・海軍・海兵隊では現在も運用されている。准尉。", "名詞句", "The warrant officer was one of the most experienced helicopter pilots in the unit.", "軍事", "700"),
    ("chief warrant officer", "米陸軍・海軍・海兵隊のwarrant officer(准尉)階級のうち、CW2からCW5までの上級区分。最初の階級であるWO1(准位官、各軍種の長官から任命)と異なり、chief warrant officerは大統領から任官辞令を受ける点で通常の将校(commissioned officer)に近い扱いを受ける。上級准尉。", "名詞句", "The chief warrant officer had over twenty years of experience flying attack helicopters.", "軍事", "740"),
    ("chain of command", "組織の最上位から最下位まで、指揮命令が伝達される階層的な経路。将官から下士官・兵に至るまでの各階級が担う役割と権限の連鎖を指し、軍隊組織を成り立たせる基本原則の一つとされる。指揮系統。", "名詞句", "Every soldier is expected to follow the chain of command when reporting a problem.", "軍事", "640"),
    ("rank insignia", "階級を示すために制服の襟・肩・袖などに付ける記章の総称。下士官のchevron(山形章)や、将校のepaulette(肩章)に付く星・鷲などのデザインが、階級ごとに定められている。階級章。", "名詞句", "You can identify a soldier's rank at a glance by looking at the rank insignia on the uniform.", "軍事", "680"),
    ("chevron", "下士官(NCO)の階級を示すV字型の山形章。フランス語で「垂木」を意味する語に由来し、英陸軍で1803年頃に採用されたのち、米軍にも1821年に導入された。伍長は1本、軍曹は3本など、本数や組み合わせで具体的な階級を表す。山形章。", "名詞", "Three chevrons on his sleeve marked him as a sergeant.", "軍事", "700"),
    ("epaulette", "将校の階級を示すために肩に付ける飾り章。フランス語で「小さな肩」を意味する語に由来し、星の数などで具体的な階級を表す。下士官のchevron(山形章)に対応する、将校用の階級章。肩章。", "名詞", "The general's epaulettes were adorned with four silver stars.", "軍事", "720"),
    ("flag officer", "海軍・沿岸警備隊においてrear admiral(少将相当)以上の将官級士官を指す総称。座乗する艦に自らの階級を示す将官旗(flag)を掲げる権利を持つことに由来する呼称で、陸軍・空軍・海兵隊のgeneral officer(将官)に相当する概念。将官(海軍)。", "名詞句", "Only a small fraction of naval officers ever become flag officers.", "軍事", "740"),
    ("field officer", "陸軍・海兵隊・空軍でmajor(少佐)からcolonel(大佐)までの佐官級士官を指す総称(米軍の給与等級O-4~O-6に相当)。second lieutenant~captainのcompany grade officer(尉官)の上、brigadier general以上のgeneral officer(将官)の下に位置する。佐官。", "名詞句", "Field officers typically command battalions, regiments, or brigade-level staffs.", "軍事", "750"),
    ("company grade officer", "陸軍・海兵隊・空軍でsecond lieutenant(少尉)からcaptain(大尉)までの尉官級士官を指す総称(米軍の給与等級O-1~O-3に相当)。中隊(company)規模の部隊を指揮することが多いことに由来する。その上位はfield officer(佐官)。尉官。", "名詞句", "As a company grade officer, he was still gaining hands-on leadership experience.", "軍事", "750"),
    ("cadet", "士官学校などで将来の将校となるための教育・訓練を受けている学生・生徒を指す語。海軍版のmidshipman(生徒)に対し、陸軍・空軍ではcadetという呼称が使われる。まだ正式な階級を持たない、将校候補生の身分。士官候補生。", "名詞", "As a first-year cadet, she spent most of her time on drill and academics.", "軍事", "600"),
    ("commodore", "既存語captain(海軍大佐相当)の上、rear admiral(海軍少将相当)の下に相当する海軍の階級・役職。英海軍では現在も一つ星の正式な階級として使われているが、米海軍では19世紀に複数隻を指揮する大佐への一時的な役職名として始まり、1862~1899年および第二次世界大戦期に正式階級として運用された後廃止され、現在の米海軍ではrear admiral (lower half)がほぼ同等の階級に当たる。代将。", "名詞", "In the Royal Navy, a commodore ranks above a captain and below a rear admiral.", "軍事", "720"),
    ("brevet rank", "戦功などの功績に対する名誉として、給与や正式な権限を伴わずに一時的・名目的に与えられる上位の階級。フランス語で「短い証書」を意味する語に由来し、米陸軍では独立戦争期の1775年から1900年まで運用されていた歴史的な制度。名誉階級・仮階級。", "名詞句", "He held the brevet rank of colonel for his conduct during the battle, though his permanent rank remained major.", "軍事", "800"),
    ("quartermaster", "階級そのものではなく、補給・糧食・宿営などの兵站業務を担当する役職を指す語。陸軍では糧秣・物資の管理を担う将校・下士官の役職名として、海軍では操舵・航法を担当する下士官の職名(rating)として使われるなど、軍種によって意味が異なる歴史的な軍事用語。需品係、操舵員。", "名詞", "The regiment's quartermaster was responsible for supplying food and equipment to every company.", "軍事", "700"),
    ("table of ranks", "1722年にロシア皇帝ピョートル1世が制定した、軍事・文官・宮廷の官職を出自ではなく能力・勤続によって14の等級に序列化した制度。「Table of Ranks(官等表)」と呼ばれ、近代的な階級・序列制度の先駆けとして歴史的に重要とされる。官等表。", "名詞句", "Peter the Great's Table of Ranks allowed commoners to rise to the nobility through military or civil service.", "軍事", "820"),
    ("generalissimo", "一国の陸海空軍全てを統括する、将軍(general)の中でも最高位に位置づけられる称号。イタリア語で「最高位の将軍」を意味し、フランシスコ・フランコ(スペイン)や蔣介石(中国)、スターリン(ソ連、1945年に授与)など、国家元首や事実上の最高権力者に与えられることが多い、通常の階級体系の枠を超えた称号。大元帥。", "名詞", "Joseph Stalin was granted the title of Generalissimo of the Soviet Union in 1945.", "軍事", "750"),
    ("boatswain", "帆船時代から続く海軍最古の職名・下士官階級の一つで、甲板作業・索具(rigging)・小型艇の管理などを統括する。米海軍ではboatswain's mate(甲板科下士官)として1794年に正式化され、現在もchief petty officerなどの上級下士官まで続く階級区分を持つ。発音が「ボースン」に近いことでも知られる。掌帆兵曹、甲板長。", "名詞", "The boatswain supervised the crew as they secured the rigging before the storm.", "軍事", "750"),
    ("midshipman", "士官候補生を指す海軍特有の伝統的階級。帆船時代の17世紀に、船の中央部(amidships)で勤務していた経験豊富な水夫を指す語として生まれ、後に正式な士官候補生の階級として確立した。現在も米海軍兵学校(アナポリス)や英国の海軍兵学校の学生はmidshipmanと呼ばれる。陸軍・空軍のcadet(士官候補生)に相当する海軍版の階級。海軍生徒。", "名詞", "Midshipmen at the Naval Academy spend four years training to become commissioned officers.", "軍事", "720"),
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
