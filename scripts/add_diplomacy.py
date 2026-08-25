# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""外交(diplomacy)テーマの語彙+フレーズを新設、authored by Claude(2026-08-25・
ユーザー要望「外交用語集」、航空管制バッチと同じ作成→裏取り→詳細・音声作成→
照査→照査の照査のプロセスで作成)。

既存の「政治」(143語)は選挙・議会・国内統治機構が中心で、外交儀礼・条約・
国際機関・交渉実務の語彙は手薄だったため、新ドメイン「外交」・新シーン
「外交・国際交渉」として新設する。マニア向け候補にあった「国際機関」
(国連・国際司法裁判所・ユネスコ等)もこのバッチに統合した。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` /
`phrases` tables.

Run:  python scripts/add_diplomacy.py
仕上げ: 投入後に `python scripts/relevel.py` と
        `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DIP = "外交"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 外交官・公館の役職・階級 ---
    ("ambassador", "大使(派遣国を代表する最高位の外交官)", "名詞", "The new ambassador presented her credentials to the president.", DIP, "700"),
    ("ambassador extraordinary and plenipotentiary", "特命全権大使(大使の正式な肩書)", "名詞", "Her official title is Ambassador Extraordinary and Plenipotentiary to Japan.", DIP, "950"),
    ("deputy chief of mission", "首席公使(大使館ナンバー2、大使不在時に代理を務める)", "名詞", "As deputy chief of mission, he ran the embassy while the ambassador was away.", DIP, "900"),
    ("minister-counselor", "公使参事官(大使館の上級外交官の階級の一つ)", "名詞", "She was promoted from counselor to minister-counselor after five years.", DIP, "950"),
    ("counselor (diplomacy)", "参事官(外交官の中級階級)", "名詞", "The counselor handled trade negotiations on behalf of the embassy.", DIP, "900"),
    ("first secretary", "一等書記官(外交官の階級の一つ)", "名詞", "The first secretary drafted the diplomatic note overnight.", DIP, "900"),
    ("second secretary", "二等書記官(外交官の階級の一つ)", "名詞", "As a second secretary, he covered political affairs at the embassy.", DIP, "900"),
    ("third secretary", "三等書記官(外交官の初任階級の一つ)", "名詞", "She joined the foreign ministry and was posted abroad as a third secretary.", DIP, "900"),
    ("attaché", "随行員・専門担当官(軍事・文化等特定分野を担当する外交スタッフ)", "名詞", "The defense attaché briefed the ambassador on regional security.", DIP, "850"),
    ("consul general", "総領事(領事館のうち規模の大きいものを統括する役職)", "名詞", "The consul general issued an emergency travel document.", DIP, "800"),
    ("vice consul", "副領事(領事館の下級職員)", "名詞", "The vice consul handled the visa application in person.", DIP, "850"),
    ("honorary consul", "名誉領事(非常勤で領事業務の一部を担う現地の名士)", "名詞", "The honorary consul, a local businessman, assisted stranded citizens.", DIP, "900"),
    ("chargé d'affaires", "臨時代理大使(大使不在時に公館を代表する外交官)", "名詞", "With the ambassador recalled, the chargé d'affaires managed the embassy.", DIP, "950"),
    ("envoy", "特使・使節(特定の任務のために派遣される外交代表)", "名詞", "The president sent a special envoy to mediate the ceasefire talks.", DIP, "750"),
    ("plenipotentiary", "全権委任された(条約締結等の全権を委任された使節を指す語)", "形容詞", "The plenipotentiary was authorized to sign the treaty on the spot.", DIP, "950"),
    ("head of delegation", "代表団長(交渉や会議に臨む代表団のトップ)", "名詞", "The head of delegation opened the talks with a formal statement.", DIP, "750"),
    ("diplomatic corps", "外交団(ある国に駐在する全外交使節の総体)", "名詞", "The diplomatic corps attended the state funeral together.", DIP, "850"),
    ("doyen of the diplomatic corps", "外交団長(外交団の中で最も在任期間の長い大使が務める代表格)", "名詞", "As the longest-serving ambassador, he served as doyen of the diplomatic corps.", DIP, "950"),
    # --- 外交儀礼・実務 ---
    ("credentials (diplomatic)", "信任状(大使が着任時に元首へ提出する公式文書)", "名詞", "The ambassador presented her credentials at a formal ceremony.", DIP, "800"),
    ("letter of credence", "信任状(大使を正式に信任することを示す文書、credentialsとほぼ同義)", "名詞", "The letter of credence was signed by the head of state.", DIP, "900"),
    ("agrément", "アグレマン(大使を受け入れる国が事前に与える同意)", "名詞", "The host country granted its agrément before the ambassador's appointment was announced.", DIP, "950"),
    ("accreditation (diplomacy)", "信任・認可(外交官として正式に受け入れられること)", "名詞", "The ambassador's accreditation was finalized after she presented her credentials to the head of state.", DIP, "850"),
    ("persona non grata", "好ましからざる人物(受け入れ国が拒否・追放を宣言する外交官)", "名詞", "The diplomat was declared persona non grata and given a week to leave.", DIP, "900"),
    ("diplomatic immunity", "外交特権(外交官が接受国の刑事裁判権等から免除される特権)", "名詞", "The driver could not be prosecuted because he claimed diplomatic immunity.", DIP, "800"),
    ("extraterritoriality", "治外法権(接受国の法律の適用を受けない地位。現代の国際法では大使館用地は接受国の主権下にあり、正確には'不可侵'とされる点に注意)", "名詞", "Under 19th-century unequal treaties, foreign nationals in some countries were granted extraterritoriality from local courts.", DIP, "950"),
    ("diplomatic pouch", "外交行嚢(検査を免除される外交公文書等の輸送用バッグ)", "名詞", "Sensitive documents were sent home in the diplomatic pouch.", DIP, "900"),
    ("recall (a diplomat)", "召還する(自国の外交官を本国へ呼び戻す)", "動詞", "The government recalled its ambassador in protest.", DIP, "800"),
    ("expel a diplomat", "外交官を追放する(接受国が外交官の国外退去を命じること)", "連語", "The two countries expelled each other's diplomats amid rising tensions.", DIP, "800"),
    ("break off diplomatic relations", "国交を断絶する", "連語", "The two nations broke off diplomatic relations after the incident.", DIP, "800"),
    ("establish diplomatic relations", "国交を樹立する", "連語", "The countries established diplomatic relations for the first time in decades.", DIP, "750"),
    ("normalize relations", "国交を正常化する", "連語", "The two former rivals agreed to normalize relations.", DIP, "750"),
    ("state visit", "公式訪問・国賓訪問(元首クラスによる正式な外国訪問)", "名詞", "The king's state visit included a banquet at the palace.", DIP, "700"),
    ("official visit", "公式訪問(state visitより格式がやや低い公式訪問)", "名詞", "The foreign minister's official visit focused on trade issues.", DIP, "700"),
    ("goodwill visit", "親善訪問(友好関係を示すことを目的とした訪問)", "名詞", "The delegation's goodwill visit strengthened cultural ties.", DIP, "700"),
    ("21-gun salute", "21発の礼砲(国賓歓迎等で行われる儀礼的な祝砲)", "名詞", "A 21-gun salute greeted the visiting head of state.", DIP, "800"),
    ("order of precedence", "席次(儀礼上の序列)", "名詞", "Seating at the banquet followed strict order of precedence.", DIP, "900"),
    # --- 条約・国際法 ---
    ("treaty", "条約(国家間の正式な合意文書)", "名詞", "The two nations signed a treaty ending decades of hostility.", DIP, "700"),
    ("convention (treaty)", "条約・協定(特定分野を扱う多国間条約)", "名詞", "The convention set global standards for refugee protection.", DIP, "800"),
    ("protocol (treaty)", "議定書(既存の条約に付随・補足する文書)", "名詞", "The additional protocol expanded the scope of the original agreement.", DIP, "850"),
    ("ratify", "批准する(条約を国内手続きを経て正式に承認する)", "動詞", "The senate voted to ratify the treaty.", DIP, "800"),
    ("ratification", "批准", "名詞", "Ratification requires approval from two-thirds of the senate.", DIP, "800"),
    ("accede to a treaty", "条約に加入する(既に発効している条約に後から参加する)", "連語", "Several new members acceded to the treaty last year.", DIP, "900"),
    ("reservation (treaty)", "留保(条約の一部条項の適用を除外する意思表示)", "名詞", "The country signed the treaty but entered a reservation on one clause.", DIP, "900"),
    ("entry into force", "発効(条約が法的効力を持ち始めること)", "名詞", "The treaty's entry into force required ratification by 55 countries.", DIP, "900"),
    ("denounce a treaty", "条約を廃棄する(一方的に条約から離脱する)", "連語", "The government formally denounced the treaty with six months' notice.", DIP, "900"),
    ("bilateral treaty", "二国間条約", "名詞", "The bilateral treaty covered trade and investment.", DIP, "750"),
    ("multilateral treaty", "多国間条約", "名詞", "Dozens of nations are party to the multilateral treaty.", DIP, "800"),
    ("non-aggression pact", "不可侵条約", "名詞", "The two rivals signed a non-aggression pact.", DIP, "850"),
    ("mutual defense treaty", "相互防衛条約", "名詞", "The alliance is built on a mutual defense treaty.", DIP, "850"),
    ("extradition treaty", "犯罪人引渡し条約", "名詞", "The suspect was returned under an extradition treaty.", DIP, "850"),
    ("most-favored-nation status", "最恵国待遇", "名詞", "Granting most-favored-nation status lowered tariffs between the two countries.", DIP, "950"),
    ("sovereignty", "主権", "名詞", "The dispute touches on questions of national sovereignty.", DIP, "800"),
    ("territorial integrity", "領土保全", "名詞", "The resolution reaffirmed the country's territorial integrity.", DIP, "850"),
    ("non-interference", "内政不干渉", "名詞", "The principle of non-interference is central to the organization's charter.", DIP, "850"),
    ("customary international law", "国際慣習法", "名詞", "Diplomatic immunity is rooted in customary international law.", DIP, "950"),
    ("diplomatic note", "外交文書(政府間でやり取りされる公式書簡の総称)", "名詞", "The embassy delivered a diplomatic note protesting the decision.", DIP, "900"),
    ("note verbale", "口上書(第三人称形式で書かれる外交文書)", "名詞", "The ministry sent a note verbale requesting clarification.", DIP, "950"),
    ("communiqué", "コミュニケ(会談・会議後に発表される公式声明)", "名詞", "The two leaders issued a joint communiqué after the summit.", DIP, "850"),
    # --- 国際機関 ---
    ("United Nations", "国際連合(国連)", "名詞", "The United Nations was founded in 1945 to maintain international peace.", DIP, "600"),
    ("UN Security Council", "国連安全保障理事会", "名詞", "The UN Security Council debated a resolution on the crisis.", DIP, "750"),
    ("permanent member (UN)", "常任理事国(国連安保理の5大国)", "名詞", "As a permanent member, the country holds veto power in the Security Council.", DIP, "800"),
    ("veto power", "拒否権", "名詞", "One permanent member used its veto power to block the resolution.", DIP, "750"),
    ("UN General Assembly", "国連総会", "名詞", "The UN General Assembly adopted the resolution by a wide margin.", DIP, "750"),
    ("Secretary-General", "事務総長(国連などの国際機関のトップ)", "名詞", "The Secretary-General called for an immediate ceasefire.", DIP, "700"),
    ("peacekeeping operation", "平和維持活動(PKO)", "名詞", "UN troops were deployed on a peacekeeping operation.", DIP, "800"),
    ("UN resolution", "国連決議", "名詞", "The council passed a binding UN resolution.", DIP, "700"),
    ("International Court of Justice", "国際司法裁判所(ICJ、国連の主要な司法機関)", "名詞", "The dispute was referred to the International Court of Justice.", DIP, "800"),
    ("International Criminal Court", "国際刑事裁判所(ICC、個人の戦争犯罪等を裁く常設法廷)", "名詞", "The International Criminal Court issued an arrest warrant.", DIP, "800"),
    ("UNESCO", "国連教育科学文化機関(ユネスコ)", "名詞", "UNESCO added the ruins to its World Heritage list.", DIP, "700"),
    ("World Health Organization", "世界保健機関(WHO)", "名詞", "The World Health Organization declared a global health emergency.", DIP, "700"),
    ("International Monetary Fund", "国際通貨基金(IMF)", "名詞", "The country requested a loan from the International Monetary Fund.", DIP, "750"),
    ("World Bank", "世界銀行", "名詞", "The World Bank funded the new infrastructure project.", DIP, "700"),
    ("World Trade Organization", "世界貿易機関(WTO)", "名詞", "The two countries filed a dispute with the World Trade Organization.", DIP, "750"),
    ("International Atomic Energy Agency", "国際原子力機関(IAEA)", "名詞", "Inspectors from the International Atomic Energy Agency visited the facility.", DIP, "800"),
    ("Interpol", "国際刑事警察機構(インターポール)", "名詞", "Interpol issued a red notice for the fugitive.", DIP, "750"),
    ("International Committee of the Red Cross", "赤十字国際委員会(ICRC)", "名詞", "The International Committee of the Red Cross visited the prisoners of war.", DIP, "800"),
    ("NATO", "北大西洋条約機構(ナトー)", "名詞", "NATO member states agreed to increase defense spending.", DIP, "700"),
    ("European Union", "欧州連合(EU)", "名詞", "The European Union imposed new sanctions.", DIP, "650"),
    ("ASEAN", "東南アジア諸国連合(アセアン)", "名詞", "ASEAN leaders met to discuss regional trade.", DIP, "750"),
    ("G7", "主要7カ国(先進7カ国首脳会議)", "名詞", "The G7 leaders issued a joint statement on the economy.", DIP, "700"),
    ("G20", "主要20カ国・地域", "名詞", "The G20 summit focused on climate financing.", DIP, "700"),
    ("OECD", "経済協力開発機構(OECD)", "名詞", "The OECD published its annual economic outlook.", DIP, "800"),
    # --- 交渉・会議実務 ---
    ("summit meeting", "首脳会談", "名詞", "The two presidents held a summit meeting in Geneva.", DIP, "650"),
    ("bilateral talks", "二国間協議", "名詞", "The foreign ministers opened bilateral talks on trade.", DIP, "700"),
    ("multilateral negotiation", "多国間交渉", "名詞", "The climate accord emerged from years of multilateral negotiation.", DIP, "800"),
    ("agenda (negotiation)", "議題(交渉・会議で扱う項目)", "名詞", "Human rights topped the agenda for the talks.", DIP, "600"),
    ("delegation", "代表団", "名詞", "A delegation of ten officials attended the conference.", DIP, "650"),
    ("plenary session", "本会議(全参加者が出席する会議)", "名詞", "The plenary session opened with remarks from the chair.", DIP, "800"),
    ("working group", "作業部会", "名詞", "A working group was set up to draft the final text.", DIP, "700"),
    ("joint communiqué", "共同声明", "名詞", "The leaders released a joint communiqué at the end of the summit.", DIP, "800"),
    ("memorandum of understanding", "覚書(MOU、正式な条約に至らない合意文書)", "名詞", "The two governments signed a memorandum of understanding on trade.", DIP, "850"),
    ("framework agreement", "枠組み合意", "名詞", "The framework agreement laid the groundwork for a formal treaty.", DIP, "800"),
    ("roadmap (diplomacy)", "ロードマップ(段階的な合意への道筋)", "名詞", "Negotiators agreed on a roadmap toward a lasting peace.", DIP, "750"),
    ("mediator", "調停者", "名詞", "A neutral mediator helped bring both sides to the table.", DIP, "700"),
    ("arbitration (international)", "仲裁(第三者が拘束力のある裁定を下す紛争解決手続)", "名詞", "The border dispute was settled through international arbitration.", DIP, "850"),
    ("good offices", "あっせん(第三者が対話の場を提供する外交上の支援)", "名詞", "The UN offered its good offices to facilitate talks.", DIP, "900"),
    ("shuttle diplomacy", "シャトル外交(仲介者が両国間を往復して交渉を進める外交手法)", "名詞", "The envoy conducted shuttle diplomacy between the two capitals.", DIP, "900"),
    ("track II diplomacy", "トラック2外交(政府関係者以外による非公式な対話)", "名詞", "Track II diplomacy kept communication open when official talks stalled.", DIP, "950"),
    ("back-channel negotiation", "裏交渉(非公式・非公開の交渉ルート)", "名詞", "A back-channel negotiation helped secure the prisoner exchange.", DIP, "900"),
    ("stalemate (negotiation)", "行き詰まり(交渉が進展しない状態)", "名詞", "The talks reached a stalemate over the border issue.", DIP, "800"),
    ("breakthrough (diplomacy)", "打開・突破口", "名詞", "Negotiators announced a breakthrough after months of talks.", DIP, "700"),
    ("deadlock", "膠着状態", "名詞", "The negotiations remained in deadlock for weeks.", DIP, "800"),
    ("concession (negotiation)", "譲歩", "名詞", "Both sides made concessions to reach the agreement.", DIP, "750"),
    ("détente", "デタント・緊張緩和(対立関係にある国家間の緊張が和らぐこと)", "名詞", "The 1970s saw a period of détente between the two superpowers.", DIP, "900"),
    ("rapprochement", "関係改善・和解(疎遠だった国家間の関係が改善すること)", "名詞", "The historic visit marked a rapprochement between the former enemies.", DIP, "950"),
    ("brinkmanship", "瀬戸際政策", "名詞", "Critics accused the leader of dangerous brinkmanship.", DIP, "950"),
    ("saber-rattling", "武力を誇示すること・威嚇", "名詞", "The military exercise was widely seen as saber-rattling.", DIP, "950"),
    # --- 追加: 承認・保護・国際秩序の用語 ---
    ("foreign ministry", "外務省", "名詞", "The foreign ministry summoned the ambassador for an explanation.", DIP, "600"),
    ("head of mission", "公館長(大使館・領事館などの長を包括的に指す語)", "名詞", "As head of mission, the ambassador is responsible for all embassy staff.", DIP, "900"),
    ("letter of recall", "召還状(外交官を本国へ呼び戻すことを通知する文書)", "名詞", "The letter of recall was delivered to the host government.", DIP, "950"),
    ("full powers (diplomacy)", "全権委任状(条約交渉・署名の権限を証明する文書)", "名詞", "The delegate presented her full powers before signing the accord.", DIP, "950"),
    ("signatory", "署名国・署名者", "名詞", "Over a hundred countries are signatories to the convention.", DIP, "800"),
    ("depositary (treaty)", "寄託者(条約の正本を保管し手続きを管理する国・機関)", "名詞", "The United Nations serves as the depositary for the convention.", DIP, "950"),
    ("diplomatic recognition", "外交承認", "名詞", "The new government sought diplomatic recognition from its neighbors.", DIP, "850"),
    ("de facto recognition", "事実上の承認", "名詞", "Several countries extended de facto recognition without formal ties.", DIP, "950"),
    ("de jure recognition", "法律上の承認", "名詞", "De jure recognition followed years of informal cooperation.", DIP, "950"),
    ("safe conduct", "安全通行(外交上、身の安全を保障して通行させること)", "名詞", "The negotiators were granted safe conduct to attend the talks.", DIP, "900"),
    ("political asylum", "政治亡命(の受け入れ)", "名詞", "The dissident was granted political asylum by the embassy.", DIP, "800"),
    ("consular access", "領事アクセス(拘束された自国民に領事が面会する権利)", "名詞", "The embassy demanded consular access to the detained citizen.", DIP, "900"),
    ("Vienna Convention on Diplomatic Relations", "外交関係に関するウィーン条約(外交特権・免除等を定めた基本条約)", "名詞", "Diplomatic immunity is codified in the Vienna Convention on Diplomatic Relations.", DIP, "950"),
    ("balance of power", "勢力均衡", "名詞", "The alliance was designed to maintain a balance of power in the region.", DIP, "800"),
    ("sphere of influence", "勢力圏", "名詞", "The region was long considered within the larger power's sphere of influence.", DIP, "850"),
    ("buffer state", "緩衝国", "名詞", "The small nation served as a buffer state between the two powers.", DIP, "900"),
    ("non-aligned movement", "非同盟運動", "名詞", "The country was a founding member of the non-aligned movement.", DIP, "900"),
    ("neutral country", "中立国", "名詞", "The talks were held in a neutral country acceptable to both sides.", DIP, "700"),
    ("quiet diplomacy", "静かな外交(公にせず水面下で進める外交)", "名詞", "Quiet diplomacy secured the release of the detained journalist.", DIP, "850"),
    ("public diplomacy", "パブリック・ディプロマシー(相手国の世論・国民に直接働きかける外交)", "名詞", "The cultural exchange program is a form of public diplomacy.", DIP, "850"),
    ("cultural diplomacy", "文化外交", "名詞", "The film festival was part of a broader cultural diplomacy effort.", DIP, "800"),
    ("economic diplomacy", "経済外交", "名詞", "Economic diplomacy focused on securing new trade agreements.", DIP, "800"),
    ("high commissioner", "高等弁務官(英連邦諸国間で大使に相当する役職)", "名詞", "The high commissioner represents her country within the Commonwealth.", DIP, "900"),
    ("high commission", "高等弁務官事務所(英連邦諸国間での大使館に相当する公館)", "名詞", "The high commission issued a statement on the visa policy change.", DIP, "900"),
    ("special representative", "特別代表", "名詞", "The special representative was tasked with resolving the border dispute.", DIP, "800"),
    ("cordon sanitaire", "防疫線・外交的孤立化(ある国家や勢力を意図的に孤立させる策)", "名詞", "Neighboring states formed a cordon sanitaire around the isolated regime.", DIP, "950"),
]


PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "外交・国際交渉": [
        # --- 首脳会談・公式訪問 ---
        ("The two leaders held a summit to discuss trade relations.", "両首脳は貿易関係について協議するため首脳会談を開いた。"),
        ("The president will pay a state visit to the country next month.", "大統領は来月その国を公式訪問する予定である。"),
        ("The prime minister was greeted with full military honors.", "首相は軍による正式な儀礼をもって迎えられた。"),
        ("The two heads of state exchanged gifts as a gesture of goodwill.", "両国の元首は友好の証として贈り物を交換した。"),
        ("The visiting delegation was welcomed at the airport by the foreign minister.", "訪問団は外務大臣に空港で出迎えられた。"),
        ("The ambassador presented her credentials to the head of state.", "大使は元首に信任状を提出した。"),
        ("The two countries agreed to upgrade relations to the ambassadorial level.", "両国は関係を大使級に格上げすることで合意した。"),
        ("The president reviewed the honor guard upon arrival.", "大統領は到着時に儀仗兵を閲兵した。"),
        ("A red carpet was rolled out for the visiting dignitary.", "来賓のためにレッドカーペットが敷かれた。"),
        ("The state banquet was attended by foreign dignitaries from across the region.", "国賓晩餐会には地域各国からの要人が出席した。"),
        ("The two leaders posed for photographs before entering the talks.", "両首脳は会談に入る前に写真撮影に応じた。"),
        ("The visit is expected to strengthen bilateral ties.", "この訪問は二国間関係の強化につながると見られている。"),
        ("The king's tour included stops in three allied nations.", "国王の外遊には同盟国3か国への訪問が含まれていた。"),
        ("The delegation was briefed on protocol before the ceremony.", "代表団は式典前に儀礼上の作法について説明を受けた。"),
        ("The two countries signed a joint declaration marking the visit.", "両国は訪問を記念して共同宣言に署名した。"),
        ("Security was tightened ahead of the head of state's arrival.", "元首の到着を前に警備が強化された。"),
        ("The visit was postponed due to a change in the travel schedule.", "訪問は日程変更のため延期された。"),
        ("The ambassador hosted a reception to mark the national day.", "大使は建国記念日を祝うレセプションを主催した。"),
        ("The two sides agreed to hold annual leader-level talks.", "両国は首脳レベルの会談を毎年開催することで合意した。"),
        ("The itinerary included a wreath-laying ceremony at the war memorial.", "日程には戦没者慰霊碑への献花式が含まれていた。"),
        # --- 記者会見・声明 ---
        ("The spokesperson declined to comment on the ongoing negotiations.", "報道官は進行中の交渉についてコメントを差し控えた。"),
        ("The foreign ministry issued a statement condemning the attack.", "外務省は攻撃を非難する声明を発表した。"),
        ("The two leaders held a joint press conference after the summit.", "両首脳は首脳会談後に共同記者会見を開いた。"),
        ("The government summoned the ambassador to explain the incident.", "政府はその事件について説明を求め大使を呼び出した。"),
        ("The ministry called the remarks 'unacceptable and provocative.'", "同省はその発言を「受け入れがたく挑発的だ」と評した。"),
        ("Officials refused to confirm or deny the reports.", "当局はその報道について肯定も否定もしなかった。"),
        ("The statement was carefully worded to avoid escalating tensions.", "声明は緊張を高めないよう慎重に文言が選ばれていた。"),
        ("The press release was issued jointly by both foreign ministries.", "プレスリリースは両外務省の連名で発表された。"),
        ("The spokesperson reiterated the country's long-standing position.", "報道官は自国の従来からの立場を改めて表明した。"),
        ("Reporters pressed the minister on the details of the agreement.", "記者団は大臣に合意内容の詳細を問いただした。"),
        ("The government welcomed the announcement as a positive step.", "政府はその発表を前向きな一歩として歓迎した。"),
        ("The remarks were later walked back by an official spokesperson.", "その発言は後に公式報道官によって撤回された。"),
        ("The statement fell short of a full apology.", "その声明は全面的な謝罪には至らなかった。"),
        ("Diplomats described the talks as 'candid and constructive.'", "外交筋はその協議を「率直かつ建設的」と評した。"),
        ("The two sides issued separate statements after the meeting broke down.", "会談が決裂した後、両者は別々に声明を発表した。"),
        ("The embassy released a statement urging calm.", "大使館は冷静な対応を呼びかける声明を発表した。"),
        ("The minister's comments were seen as a signal of shifting policy.", "大臣の発言は政策転換の兆しと受け止められた。"),
        ("The government demanded a formal explanation from its neighbor.", "政府は隣国に対し正式な説明を求めた。"),
        ("The briefing was held on condition of anonymity.", "その説明は匿名を条件に行われた。"),
        ("Officials on both sides declined to elaborate further.", "双方の当局者はそれ以上の詳細を明らかにしなかった。"),
        # --- 交渉・協議 ---
        ("The two delegations sat down for a second round of talks.", "両代表団は2回目の協議のため着席した。"),
        ("Negotiators worked through the night to finalize the text.", "交渉担当者たちは文書を確定させるため夜通し作業した。"),
        ("The talks stalled over disagreements on border demarcation.", "協議は国境線をめぐる意見の相違で行き詰まった。"),
        ("Both sides agreed to set up a working group on trade.", "両者は貿易に関する作業部会を設置することで合意した。"),
        ("The negotiations dragged on for over a decade.", "交渉は10年以上にわたって長引いた。"),
        ("A compromise was reached after weeks of shuttle diplomacy.", "数週間にわたるシャトル外交の末、妥協が成立した。"),
        ("Neither side was willing to make the first concession.", "どちらの側も最初に譲歩しようとはしなかった。"),
        ("The mediator proposed a framework acceptable to both parties.", "調停者は双方が受け入れ可能な枠組みを提案した。"),
        ("The two governments agreed to resume talks next quarter.", "両国政府は来四半期に協議を再開することで合意した。"),
        ("The final draft was hammered out in a closed-door session.", "最終案は非公開の会合で練り上げられた。"),
        ("The negotiations broke down without a resolution.", "交渉は決着のないまま決裂した。"),
        ("A last-minute breakthrough saved the summit from failure.", "土壇場での打開により首脳会談は決裂を免れた。"),
        ("Both sides walked back from the brink of a trade war.", "両国は貿易戦争の瀬戸際から後退した。"),
        ("The delegation was given a mandate to negotiate on all issues.", "代表団は全ての議題について交渉する権限を与えられた。"),
        ("The chief negotiator flew home for consultations with the government.", "首席交渉官は本国政府と協議するため帰国した。"),
        ("The two sides remain far apart on key sticking points.", "両者は主要な争点で依然として大きく隔たっている。"),
        ("A ceasefire was brokered after months of shuttle diplomacy.", "数か月にわたるシャトル外交の末、停戦が仲介された。"),
        ("The agreement was initialed but not yet formally signed.", "合意文書には仮署名がなされたが、正式な署名はまだである。"),
        ("The two countries agreed to disagree on the disputed territory.", "両国は係争地について見解の相違を認め合った。"),
        ("The talks were extended by another 48 hours.", "協議はさらに48時間延長された。"),
        ("Officials described the atmosphere as tense but professional.", "当局者はその雰囲気を緊迫していたが節度を保っていたと述べた。"),
        ("The two delegations exchanged position papers ahead of the meeting.", "両代表団は会合に先立ち立場表明文書を交換した。"),
        ("The negotiator refused to budge on the core demand.", "交渉担当者は中心的な要求について一切譲らなかった。"),
        ("The talks collapsed after one side walked out.", "一方が途中退席したことで協議は決裂した。"),
        ("The two sides reached a tentative agreement pending final approval.", "両者は最終承認待ちの暫定合意に達した。"),
        # --- 条約・署名式 ---
        ("The two presidents signed the treaty in a formal ceremony.", "両大統領は正式な式典で条約に署名した。"),
        ("The treaty will enter into force once ratified by both parliaments.", "条約は両国議会で批准されれば発効する。"),
        ("Fifty-five countries have ratified the convention so far.", "これまでに55か国がこの条約を批准している。"),
        ("The senate is expected to vote on ratification next week.", "上院は来週、批准について採決する見通しである。"),
        ("The agreement was signed with reservations on two clauses.", "合意は2つの条項について留保付きで署名された。"),
        ("The country formally acceded to the convention last year.", "その国は昨年、正式にこの条約に加入した。"),
        ("The pact commits both sides to reduce tariffs gradually.", "この協定は双方に段階的な関税引き下げを義務付けている。"),
        ("The treaty was denounced by the new administration.", "その条約は新政権によって廃棄が通告された。"),
        ("The signing ceremony was delayed due to last-minute objections.", "署名式は土壇場での異議申し立てにより延期された。"),
        ("Both governments exchanged instruments of ratification.", "両国政府は批准書を交換した。"),
        ("The agreement includes a clause allowing either party to withdraw.", "合意にはいずれの当事者も離脱を認める条項が含まれている。"),
        ("The pact was hailed as a historic step toward peace.", "この協定は平和への歴史的な一歩として称賛された。"),
        ("The two sides initialed the draft agreement pending legal review.", "両者は法的審査待ちの草案に仮署名した。"),
        ("The treaty text was finalized after a marathon session.", "条約文は長時間に及ぶ会合の末に確定した。"),
        ("The agreement takes effect thirty days after signature.", "この合意は署名から30日後に発効する。"),
        # --- 国連・国際会議 ---
        ("The Security Council will vote on the resolution this afternoon.", "安全保障理事会は本日午後、決議案を採決する予定である。"),
        ("One permanent member vetoed the draft resolution.", "常任理事国の1か国が決議案に拒否権を行使した。"),
        ("The General Assembly adopted the resolution by consensus.", "総会はコンセンサスによりその決議を採択した。"),
        ("The Secretary-General called on all parties to exercise restraint.", "事務総長は全当事者に自制を求めた。"),
        ("The council held an emergency session on the crisis.", "理事会はその危機について緊急会合を開いた。"),
        ("A peacekeeping mission was deployed under a UN mandate.", "国連の委任に基づき平和維持部隊が派遣された。"),
        ("The ambassador took the floor to respond to the accusation.", "大使は発言権を得てその非難に反論した。"),
        ("The resolution passed with fifteen votes in favor and none against.", "決議は賛成15票、反対0票で可決された。"),
        ("The delegation walked out in protest during the speech.", "代表団はその演説の間、抗議のため退席した。"),
        ("The organization suspended the country's voting rights.", "その機関は当該国の投票権を停止した。"),
        ("The summit produced a nonbinding declaration on climate goals.", "首脳会議は気候目標に関する法的拘束力のない宣言を採択した。"),
        ("Member states pledged additional funding for humanitarian aid.", "加盟国は人道支援への追加拠出を約束した。"),
        ("The tribunal issued an arrest warrant for the former leader.", "法廷は前指導者に対する逮捕状を発付した。"),
        ("The organization dispatched observers to monitor the election.", "同機関は選挙を監視するため監視団を派遣した。"),
        ("The council extended the sanctions regime for another year.", "理事会は制裁体制をさらに1年延長した。"),
        ("The conference was attended by delegates from over a hundred nations.", "この会議には100を超える国々からの代表が出席した。"),
        ("The panel of experts submitted its findings to the council.", "専門家パネルはその調査結果を理事会に提出した。"),
        ("The proposal failed to gain the two-thirds majority required.", "その提案は必要な3分の2の多数を得られなかった。"),
        ("The agency issued a report documenting the humanitarian situation.", "同機関は人道状況を記録した報告書を発表した。"),
        ("The summit concluded without a formal joint statement.", "首脳会議は正式な共同声明のないまま終了した。"),
        # --- 抗議・外交摩擦 ---
        ("The government lodged a formal protest with the embassy.", "政府は大使館に対し正式な抗議を申し入れた。"),
        ("The ambassador was summoned to the foreign ministry for a reprimand.", "大使は厳重注意のため外務省に呼び出された。"),
        ("Relations between the two countries have deteriorated sharply.", "両国関係は急速に悪化している。"),
        ("The country recalled its ambassador for consultations.", "その国は協議のため大使を召還した。"),
        ("Diplomatic ties were severed following the coup.", "クーデターを受け国交は断絶された。"),
        ("The incident sparked a diplomatic row between the two capitals.", "この事件は両国首都間の外交摩擦を引き起こした。"),
        ("The foreign ministry rejected the allegations as baseless.", "外務省はその主張を根拠がないとして退けた。"),
        ("The two nations traded accusations of espionage.", "両国はスパイ活動をめぐって互いに非難し合った。"),
        ("Several diplomats were declared persona non grata and expelled.", "複数の外交官が好ましからざる人物とされ追放された。"),
        ("The government imposed sanctions in response to the violation.", "政府はその違反に対応して制裁を科した。"),
        ("The rift threatens to undo years of careful diplomacy.", "この対立は長年の慎重な外交努力を無に帰しかねない。"),
        ("The two countries remain locked in a tense standoff.", "両国は依然として緊迫したにらみ合いを続けている。"),
        ("The embassy was evacuated amid the escalating unrest.", "騒乱の激化に伴い大使館は避難した。"),
        ("The dispute has simmered for years without resolution.", "この対立は解決されないまま何年もくすぶり続けている。"),
        ("The government demanded an apology and compensation.", "政府は謝罪と賠償を要求した。"),
        # --- 儀礼・レセプション ---
        ("The reception was held to mark the embassy's anniversary.", "レセプションは大使館の記念日を祝って開かれた。"),
        ("Guests were seated according to strict order of precedence.", "来賓は厳格な席次に従って着席した。"),
        ("The national anthem was played as the flag was raised.", "国旗掲揚に合わせて国歌が演奏された。"),
        ("The ambassador proposed a toast to lasting friendship.", "大使は末永い友好関係を祝して乾杯の音頭を取った。"),
        ("Diplomats from dozens of countries mingled at the gala.", "数十か国からの外交官たちがそのレセプションで歓談した。"),
        ("The dress code for the state dinner was formal attire.", "国賓晩餐会の服装規定はフォーマルウェアだった。"),
        ("The honor guard stood at attention throughout the ceremony.", "儀仗兵は式典の間ずっと直立不動の姿勢を保った。"),
        ("The visiting delegation was presented with a ceremonial gift.", "訪問団には儀礼的な贈答品が贈られた。"),
        ("Protocol officers coordinated every detail of the arrival.", "儀典官が到着に関するあらゆる詳細を調整した。"),
        ("The event closed with a formal exchange of pleasantries.", "式典は正式な社交辞令の交換をもって締めくくられた。"),
        # --- 危機対応・仲介 ---
        ("The international community called for an immediate ceasefire.", "国際社会は即時停戦を求めた。"),
        ("A neutral country offered to mediate the dispute.", "中立国がその紛争の仲介を申し出た。"),
        ("The envoy shuttled between the two capitals to broker a truce.", "特使は休戦を仲介するため両国首都間を往復した。"),
        ("The crisis prompted an emergency meeting of foreign ministers.", "この危機は外相たちの緊急会合を招いた。"),
        ("Evacuation flights were arranged for stranded nationals.", "取り残された自国民のため退避便が手配された。"),
        ("The government offered its good offices to facilitate dialogue.", "政府は対話を促進するためあっせんを申し出た。"),
        ("A humanitarian corridor was negotiated to allow aid through.", "支援物資の通行を認める人道回廊が交渉により設けられた。"),
        ("The hostage situation was resolved through back-channel talks.", "人質事件は裏交渉を通じて解決された。"),
        ("International observers were deployed to monitor the ceasefire.", "停戦を監視するため国際監視団が派遣された。"),
        ("The mediator's proposal was rejected by both sides.", "調停者の提案は双方から拒否された。"),
        # --- 大使館・領事業務 ---
        ("The embassy issued an emergency travel document for the stranded tourist.", "大使館は取り残された旅行者のため緊急旅行文書を発給した。"),
        ("Citizens abroad were advised to register with the local embassy.", "在外自国民は現地の大使館に登録するよう勧告された。"),
        ("The consulate assisted with the repatriation of the remains.", "領事館は遺体の本国送還を支援した。"),
        ("The embassy issued a travel advisory urging caution.", "大使館は注意を促す渡航情報を発表した。"),
        ("The consular section processed hundreds of visa applications daily.", "領事部は毎日何百件ものビザ申請を処理した。"),
        ("The embassy arranged for legal counsel for the detained citizen.", "大使館は拘束された自国民のため弁護士を手配した。"),
        ("Consular officials visited the prisoner to check on his welfare.", "領事担当官はその受刑者の安否確認のため訪問した。"),
        ("The embassy remained closed following the security threat.", "大使館は治安上の脅威を受けて閉鎖されたままだった。"),
        # --- 追加: 承認・原則をめぐる表現 ---
        ("The new government is seeking diplomatic recognition from major powers.", "新政権は主要国からの外交承認を求めている。"),
        ("The country extended de facto recognition without establishing formal ties.", "その国は正式な国交樹立なしに事実上の承認を与えた。"),
        ("The dissident sought political asylum at the foreign embassy.", "その反体制活動家は外国大使館に政治亡命を求めた。"),
        ("The two nations have maintained a careful balance of power for decades.", "両国は何十年もの間、慎重な勢力均衡を維持してきた。"),
        ("The small nation has long served as a buffer between rival powers.", "その小国は長らく対立する大国間の緩衝地帯としての役割を果たしてきた。"),
        ("Officials pursued quiet diplomacy rather than public confrontation.", "当局者たちは公然たる対立ではなく静かな外交を追求した。"),
        ("The exchange program is part of a broader public diplomacy strategy.", "この交流プログラムはより大きなパブリック・ディプロマシー戦略の一環である。"),
        ("The special representative was dispatched to defuse the crisis.", "特別代表はその危機を鎮静化させるため派遣された。"),
        ("The talks were held under a guarantee of safe conduct for both delegations.", "その協議は両代表団に安全通行が保証された上で行われた。"),
        ("The convention requires signatories to report annually on compliance.", "この条約は署名国に対し毎年の遵守状況の報告を義務付けている。"),
        ("The ambassador's full powers were verified before the signing began.", "署名開始前に大使の全権委任状が確認された。"),
        ("The government issued a letter of recall for its ambassador abroad.", "政府は在外大使に対する召還状を発給した。"),
        # --- 追加: 一般的な交渉・儀礼フレーズ ---
        ("The two sides agreed on a face-saving compromise.", "双方は面目を保てる妥協案で合意した。"),
        ("The dispute was ultimately settled through quiet, behind-the-scenes diplomacy.", "この対立は最終的に静かな水面下の外交によって解決された。"),
        ("The delegation was received with the customary formalities.", "代表団は慣例に従った儀礼をもって迎えられた。"),
        ("The two foreign ministers shook hands for the cameras.", "両国の外相はカメラの前で握手を交わした。"),
        ("The talks were conducted through an interpreter on both sides.", "協議は双方とも通訳を介して行われた。"),
        ("The agreement was reached just hours before the deadline.", "合意は期限のわずか数時間前に成立した。"),
        ("The two countries pledged to deepen economic and cultural ties.", "両国は経済・文化面での関係深化を約束した。"),
        ("The visiting minister laid a wreath at the memorial site.", "訪問中の大臣は記念碑に花輪を捧げた。"),
    ]
}


def main() -> int:
    with db() as conn:
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        w_added = w_skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
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

        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        ph_added = ph_skipped = 0
        for scene, items in PHRASES_BY_SCENE.items():
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

    print(f"words:   +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    with db() as conn:
        print("totals -> words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
              "phrases:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
