# ruff: noqa: E501
"""法律・経営学ドメイン深掘り追加(2026-09-13・authored by Claude)。

前セッションで「法律(52語)・経営学(55語)」の深掘り追加を下書きしたが、
セッションスクラッチパッドにしか保存しておらず消失したため、本セッションで
再作成した。既存の`法律`(137語)・`経営学`(85語)ドメインを深掘りし、以下の
サブ分野を中心に追加する。

法律(法律(生活)・知的財産（*）とは重複させない):
  憲法理論・国際比較法・税法・労働法・証拠法・法哲学

経営学(経営工学・経済学とは重複させない):
  組織論・動機づけ理論・生産管理/オペレーション戦略・マーケティング

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table。
既存15,263語全件と照合済み(法律(生活)・経営工学・経済学・知的財産（一般/著作権/
特許/米国/デザイン/商標）ドメインを含む)。

Run:  python scripts/add_law_management_topup_2026_09_13.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 法律: 憲法理論 (11) ---
    ("strict scrutiny", "人種による分類や表現の自由の制約など、疑わしい分類や基本的権利に関わる法律を裁判所が審査する際に用いる、最も厳格な違憲審査基準。政府側がやむにやまれぬ利益の存在と、規制が目的達成に必要最小限であることを立証しなければならない。", "名詞", "The court applied strict scrutiny because the law classified people by race.", "法律", "850"),
    ("substantive due process", "適正手続き条項が、単に手続きの公正さだけでなく、政府が個人の生命・自由・財産を制約する法律の内容自体にも合理性や正当な目的を要求するという、米国憲法上の考え方。", "名詞", "The court struck down the law under the doctrine of substantive due process.", "法律", "850"),
    ("equal protection clause", "すべての人を法の下で平等に取り扱うことを州政府に義務づける、米国憲法修正14条に定められた条項。人種・性別など特定の分類に基づく差別的な扱いを審査する際の根拠となる。", "名詞", "The law was challenged under the equal protection clause because it treated the two groups differently.", "法律", "800"),
    ("judicial activism", "裁判所が既存の判例や制定法の文言に厳格にとどまらず、社会状況の変化などを踏まえて積極的に新しい法解釈や政策判断を打ち出す姿勢を指す言葉。", "名詞", "Critics accused the court of judicial activism when it overturned decades of precedent.", "法律", "750"),
    ("judicial restraint", "裁判所が自らの判断で新たな政策や広範な法解釈を打ち出すことを避け、立法府の判断や既存の判例をできる限り尊重しようとする姿勢。", "名詞", "She believed in judicial restraint and rarely voted to overturn existing precedent.", "法律", "750"),
    ("eminent domain", "国や地方政府が、正当な補償を条件として、私有財産を公共の利益のために強制的に収用できる権限。", "名詞", "The city used eminent domain to acquire the land for the new highway.", "法律", "750"),
    ("takings clause", "私有財産を公共の使用のために収用する場合には、所有者に対して正当な補償を行わなければならないと定める、米国憲法修正5条の条項。", "名詞", "The landowner sued the city, arguing that the regulation violated the takings clause.", "法律", "800"),
    ("originalism", "憲法の条文は制定された当時の起草者の意図や、当時の一般的な理解に沿って解釈されるべきだとする、米国憲法解釈の立場。", "名詞", "As an originalist, the judge tried to interpret the amendment as it was understood in 1868.", "法律", "800"),
    ("police power", "公共の安全・健康・道徳・福祉を守るために、州や地方政府が住民の権利や財産の利用を規制できる、広範な統治権限。", "名詞", "States use their police power to regulate everything from zoning to public health.", "法律", "750"),
    ("rational basis review", "政府の行為が正当な目的と合理的に関連していれば足りるとする、違憲審査基準の中で最も緩やかな審査基準。基本的権利や疑わしい分類が関わらない事案に適用される。", "名詞", "Because no fundamental right was involved, the court applied only rational basis review.", "法律", "850"),
    ("dormant commerce clause", "米国憲法が連邦議会に州際通商を規制する権限を与えていることの裏返しとして、州が州際通商を不当に差別・負担する法律を制定することを禁じるとする理論。", "名詞", "The state law was struck down under the dormant commerce clause for favoring in-state businesses.", "法律", "900"),
    # --- 法律: 国際比較法 (8) ---
    ("act of state doctrine", "ある国が自国の領域内で行った公的な行為の有効性については、他国の裁判所がその是非を審査すべきではないとする国際法上の原則。", "名詞", "The court dismissed the case under the act of state doctrine, refusing to judge the foreign government's official act.", "法律", "850"),
    ("jus cogens", "ジェノサイドや奴隷制の禁止など、国際社会全体によって逸脱が許されないと認められている、最上位の国際法規範。強行規範。", "名詞", "The prohibition of genocide is widely recognized as a norm of jus cogens.", "法律", "900"),
    ("sovereign immunity", "国家やその機関は、原則として他国の裁判所において訴えられたり、その意に反して裁判権に服させられたりしないとする国際法上・国内法上の原則。", "名詞", "The foreign government invoked sovereign immunity to avoid being sued in the local court.", "法律", "800"),
    ("pacta sunt servanda", "有効に締結された条約や合意は当事者を拘束し、当事者はそれを誠実に履行しなければならないとする、条約法の根幹をなす国際法の基本原則。", "名詞", "The tribunal reminded both states of the principle of pacta sunt servanda.", "法律", "900"),
    ("most-favored-nation clause", "ある国が特定の相手国に対して関税など通商上の有利な待遇を与えた場合、同じ待遇を条約を結ぶ他の全ての締約国にも自動的に及ぼすことを定める条項。", "名詞", "Under the most-favored-nation clause, any tariff cut given to one trading partner must be extended to all WTO members.", "法律", "800"),
    ("comity", "法的な義務ではないものの、国家間や裁判所間が互いの法制度や判断を尊重し、礼譲として相手の判決や法令の効力を認めようとする姿勢や慣行。", "名詞", "Out of comity, the court recognized the judgment issued by the foreign tribunal.", "法律", "800"),
    ("universal jurisdiction", "ジェノサイドや戦争犯罪など特に重大な犯罪については、犯罪地や被告人・被害者の国籍にかかわらず、どの国の裁判所でも訴追できるとする国際法上の考え方。", "名詞", "The country invoked universal jurisdiction to prosecute the war crimes suspect, even though the crimes occurred abroad.", "法律", "850"),
    ("non-refoulement", "迫害や拷問を受ける危険がある国へ、難民や庇護希望者を強制的に送還してはならないとする、国際難民法上の基本原則。", "名詞", "The principle of non-refoulement prevents states from returning refugees to a country where they would face persecution.", "法律", "900"),
    # --- 法律: 税法 (7) ---
    ("progressive taxation", "所得や資産の額が大きくなるほど、より高い税率が適用される課税方式。所得の再分配や垂直的公平の実現を目的とすることが多い。", "名詞", "Under progressive taxation, high-income earners pay a larger percentage of their income in taxes than low-income earners.", "法律", "700"),
    ("regressive tax", "所得の額にかかわらず税率自体は一定であっても、所得に占める税負担の割合が低所得者ほど相対的に重くなる性質を持つ税。消費税などが代表例とされる。", "名詞", "Sales tax is often criticized as a regressive tax because it takes a larger share of income from the poor than from the rich.", "法律", "700"),
    ("tax evasion", "所得を隠したり虚偽の申告をしたりするなど、違法な手段によって本来納めるべき税を免れようとする行為。刑事罰の対象となる。", "名詞", "He was convicted of tax evasion after hiding millions of dollars in offshore accounts.", "法律", "700"),
    ("tax avoidance", "税法の定める控除や特例などの仕組みを利用して、合法的な範囲内で納税額を減らそうとする行為。違法な脱税(tax evasion)とは区別される。", "名詞", "Using legal deductions and tax credits is a form of tax avoidance, not tax evasion.", "法律", "700"),
    ("tax haven", "法人税や所得税の税率が極めて低く、あるいは実質的に課されず、金融取引の秘匿性も高いために、外国企業や個人資産の誘致に用いられる国や地域。", "名詞", "The company moved its headquarters to a tax haven to reduce its corporate tax bill.", "法律", "700"),
    ("double taxation", "同一の所得や財産に対して、複数の国や複数の課税段階(法人税と配当への所得税など)で二重に税が課されてしまうこと。", "名詞", "Without a tax treaty, the company's profits could be subject to double taxation in both countries.", "法律", "750"),
    ("transfer pricing", "多国籍企業の関連会社同士が製品やサービス、知的財産などを取引する際に設定する価格。各国の税務当局は、独立した企業間の取引価格(独立企業原則)と乖離していないかを審査する。", "名詞", "Tax authorities scrutinized the company's transfer pricing between its subsidiaries in different countries.", "法律", "800"),
    # --- 法律: 労働法 (9) ---
    ("wrongful termination", "労働契約や法律に違反する形で、使用者が従業員を不当に解雇すること。差別的理由や内部告発への報復などが典型例とされる。", "名詞", "She filed a lawsuit for wrongful termination after being fired for reporting safety violations.", "法律", "700"),
    ("at-will employment", "使用者・従業員のいずれの側からも、特段の理由を示すことなく、いつでも雇用関係を終了させることができるとする、米国の伝統的な雇用原則。", "名詞", "Because she was an at-will employee, the company could let her go without giving any reason.", "法律", "750"),
    ("collective bargaining", "労働組合が使用者と対等な立場で、賃金や労働条件について交渉し、労働協約という形で合意を取り決める仕組み。", "名詞", "The union entered collective bargaining with management to negotiate higher wages.", "法律", "700"),
    ("non-compete clause", "従業員が退職後、一定の期間・地域において競合する企業に就職したり、同業の事業を始めたりすることを制限する、雇用契約上の条項。", "名詞", "His employment contract included a non-compete clause preventing him from working for a rival company for one year.", "法律", "750"),
    ("whistleblower", "勤務先や組織内部の不正行為・違法行為・安全上の問題などを、監督官庁や報道機関に通報する人。内部告発者。多くの国で報復から保護する法律が整備されている。", "名詞", "The whistleblower revealed that the company had been falsifying its safety inspection records.", "法律", "700"),
    ("workers' compensation", "業務中の事故や職業病によって労働者が負傷・疾病を負った場合に、過失の有無を問わず一定の補償(治療費や休業補償など)を受けられる公的な保険制度。", "名詞", "After injuring his back at the factory, he filed a workers' compensation claim.", "法律", "700"),
    ("right-to-work law", "労働組合が組織されている職場であっても、従業員が組合に加入したり組合費を支払ったりすることを義務づけられないと定める、米国の一部の州の法律。", "名詞", "In right-to-work states, employees cannot be required to join a union or pay union dues as a condition of employment.", "法律", "800"),
    ("constructive dismissal", "使用者が形式的には解雇していなくても、労働条件を一方的に著しく悪化させるなどして従業員に退職せざるを得ない状況を作り出した場合に、実質的な不当解雇として扱われること。", "名詞", "She resigned and claimed constructive dismissal after her employer cut her salary in half without warning.", "法律", "800"),
    ("duty of fair representation", "労働組合が、組合員であるか否かを問わず、交渉単位に属するすべての労働者を差別なく、誠実かつ公正に代表しなければならないとする法的義務。", "名詞", "The union was sued for breaching its duty of fair representation when it refused to process a member's grievance.", "法律", "850"),
    # --- 法律: 証拠法 (9) ---
    ("chain of custody", "証拠物件が収集されてから法廷に提出されるまでの間、誰がいつどのように保管・移転したかを記録した経路。改ざんや取り違えがないことを証明するために重要となる。", "名詞", "The defense argued that a break in the chain of custody made the DNA evidence unreliable.", "法律", "700"),
    ("spoliation", "訴訟で証拠として使われることが予想される文書や物件を、当事者が故意または過失によって破棄・改変・隠匿してしまうこと。裁判所による制裁(不利な推定など)の対象となりうる。", "名詞", "The court sanctioned the company for spoliation after it deleted emails relevant to the lawsuit.", "法律", "850"),
    ("privilege against self-incrimination", "刑事手続きにおいて、被疑者・被告人が自らに不利益となる供述を強要されない権利。米国では憲法修正5条によって保障されている。", "名詞", "He invoked his privilege against self-incrimination and refused to answer the prosecutor's questions.", "法律", "800"),
    ("fruit of the poisonous tree", "違法な捜索・押収や違法な取調べなどによって最初に得られた証拠だけでなく、そこから派生的に得られた証拠も、原則として裁判で証拠として使用できないとする米国刑事訴訟法上の法理。", "名詞", "Because the confession was obtained illegally, the evidence found as a result was excluded as fruit of the poisonous tree.", "法律", "850"),
    ("probative value", "ある証拠が、争点となっている事実の存否を証明するのにどれだけ役立つかという証拠としての価値・重要性。", "名詞", "The judge ruled that the photograph's probative value outweighed any potential prejudice to the jury.", "法律", "800"),
    ("best evidence rule", "文書の内容を証明しようとする場合には、原則としてその文書の原本を提出しなければならず、写しや口頭での証言では足りないとする証拠法上のルール。", "名詞", "Under the best evidence rule, the court required the original contract rather than a photocopy.", "法律", "800"),
    ("judicial notice", "広く知られている事実や、容易かつ正確に確認できる事実については、当事者に立証させることなく裁判所が公式に事実として認めることができる制度。", "名詞", "The court took judicial notice of the fact that the accident occurred on a public holiday.", "法律", "800"),
    ("character evidence", "被告人や証人の日頃の性格・人格や過去の行状を示すことによって、事件当日にどのように行動したかを推認させようとする証拠。多くの法域で原則として使用が制限されている。", "名詞", "The prosecution was barred from introducing character evidence about the defendant's past conduct.", "法律", "750"),
    ("collateral estoppel", "ある訴訟で当事者間に争われ実際に判断が下された争点については、後の別の訴訟で同じ当事者間で再び争うことができないとする法理。争点効・争点排除効とも呼ばれる。", "名詞", "Because the issue of negligence had already been decided in the first trial, collateral estoppel barred relitigating it in the second.", "法律", "850"),
    # --- 法律: 不法行為法の関連理論 (3) ---
    ("duty of care", "ある人が、自らの行為によって他人に損害を与えないよう、合理的な注意を払うべきだとする、不法行為法(過失責任)の基礎となる法的義務。", "名詞", "As a driver, he owed a duty of care to other people on the road.", "法律", "750"),
    ("proximate cause", "被告の行為と損害との間に、法的責任を負わせるのに十分なほど直接的で相当な因果関係があると認められること。事実的な原因のすべてに責任を負わせるわけではない点がポイント。", "名詞", "The court found that the driver's negligence was not the proximate cause of the pedestrian's injury.", "法律", "800"),
    ("strict liability", "加害者に過失がなくても、一定の危険な活動や欠陥製品などについては、損害が生じた事実だけで法的責任を負わせる、無過失責任の原則。", "名詞", "Manufacturers can be held strictly liable for injuries caused by defective products, even without proof of negligence.", "法律", "750"),
    # --- 法律: 法哲学 (5) ---
    ("legal positivism", "法の正しさや妥当性は、道徳的な内容の善し悪しとは切り離され、正当な権限を持つ機関によって定められたという事実そのものによって決まるとする法哲学上の立場。", "名詞", "Legal positivists argue that a law can be valid even if it is unjust, as long as it was properly enacted.", "法律", "850"),
    ("legal realism", "法の条文や論理だけでなく、実際に裁判官がどのような社会的・心理的要因に影響されて判断を下すかという現実に注目すべきだとする、20世紀初頭の米国発の法哲学上の立場。", "名詞", "Legal realists argued that judges' decisions are shaped as much by their personal views as by legal rules.", "法律", "850"),
    ("social contract theory", "人々が自然状態での自由の一部を互いに譲り合い、統治への同意という合意(社会契約)に基づいて国家や法の正当性が成り立つとする政治哲学・法哲学上の理論。", "名詞", "According to social contract theory, government derives its legitimacy from the consent of the governed.", "法律", "750"),
    ("natural rights", "国家や法律によって与えられるのではなく、人間であるという事実だけに基づいて生まれながらに備わっているとされる権利。生命・自由・財産に対する権利などが代表例とされる。", "名詞", "The Declaration of Independence proclaims that all people are endowed with certain natural rights.", "法律", "750"),
    ("critical legal studies", "法は中立的・客観的なものではなく、既存の政治的・経済的な権力関係を反映し、それを正当化する道具として機能しているとする、1970年代以降の米国発の批判的な法学運動。", "名詞", "Scholars of critical legal studies argue that legal doctrine often masks underlying power imbalances in society.", "法律", "900"),
    # --- 経営学: 組織論 (12) ---
    ("institutional isomorphism", "同じ制度的環境の中にある組織が、正当性を得ようとする中で、互いに似通った構造や慣行を採用するようになり、結果として組織形態が同質化していく現象。", "名詞", "Institutional isomorphism explains why hospitals across the country tend to adopt very similar organizational structures.", "経営学", "950"),
    ("path dependence", "過去に行われた選択や投資が、その後より効率的な代替案が現れたとしても、変更コストの高さなどから組織や社会の進む方向を長期にわたり拘束し続ける現象。経路依存性。", "名詞", "The company's outdated IT system persisted for decades due to path dependence, even as better alternatives emerged.", "経営学", "900"),
    ("groupthink", "集団の結束や合意を重視するあまり、メンバーが異論を控えたり批判的な検討を怠ったりして、実際には質の低い意思決定を行ってしまう心理的傾向。集団浅慮。", "名詞", "Groupthink led the committee to approve a flawed plan without seriously considering the risks.", "経営学", "750"),
    ("organizational silos", "組織内の各部門や各チームが、互いに情報共有や連携をほとんど行わず、それぞれが孤立した状態で業務を進めてしまっている状況。縦割り組織。", "名詞", "Organizational silos made it difficult for the marketing and engineering teams to coordinate on the new product.", "経営学", "700"),
    ("flat organization", "中間管理職の階層を極力減らし、経営層と現場の従業員との間の意思決定の距離を短くした、階層の少ない組織構造。フラット組織。", "名詞", "The startup adopted a flat organization with almost no middle management.", "経営学", "700"),
    ("divisional structure", "製品分野・地域・顧客層などの単位ごとに、それぞれがある程度独立して意思決定を行う事業部を設け、その集合体として全体を構成する組織構造。事業部制組織。", "名詞", "The conglomerate reorganized into a divisional structure, with separate units for each product line.", "経営学", "750"),
    ("functional structure", "営業・製造・経理・人事といった職能(機能)ごとに部門を編成する、最も伝統的な組織構造。同じ専門性を持つ人材を一つの部門にまとめることで専門性の向上を図る。", "名詞", "In a functional structure, all the engineers report to the head of engineering, regardless of which product they work on.", "経営学", "700"),
    ("network organization", "一つの企業がすべての機能を内部に抱え込むのではなく、独立した複数の企業や個人が契約や提携によって緩やかに結びつき、全体として一つの事業を遂行する組織形態。", "名詞", "The fashion brand operates as a network organization, outsourcing manufacturing and logistics to independent partners.", "経営学", "800"),
    ("boundaryless organization", "部門間・階層間・さらには社外との間の壁(境界)をできる限り取り払い、情報や人材、アイデアが組織の内外を自由に行き来できるようにすることを目指す組織のあり方。", "名詞", "GE's former CEO Jack Welch popularized the idea of the boundaryless organization to encourage collaboration across departments.", "経営学", "850"),
    ("resource dependence theory", "組織は事業に必要な資源(資金・人材・情報など)を外部環境に依存しており、その依存関係をいかに管理し不確実性を減らすかによって組織の行動が説明できるとする組織理論。資源依存理論。", "名詞", "Resource dependence theory explains why companies form alliances with suppliers who control scarce raw materials.", "経営学", "950"),
    ("Hawthorne effect", "労働者が自分たちが観察されている、あるいは注目されていると意識するだけで、作業条件そのものの変化とは関係なく生産性や行動が変化してしまう現象。", "名詞", "The researchers noticed a Hawthorne effect: productivity rose simply because workers knew they were being studied.", "経営学", "800"),
    ("social loafing", "集団で共同作業を行う際に、個人の貢献度が明確に測定されないことなどから、一人で作業する場合に比べて一人当たりの努力の水準が低下してしまう現象。社会的手抜き。", "名詞", "Social loafing became a problem in the large team, where individual contributions were hard to track.", "経営学", "800"),
    # --- 経営学: 動機づけ理論・組織行動論 (8) ---
    ("Theory X and Theory Y", "人間は本来仕事を嫌い怠けたがるので統制・命令が必要だとする「X理論」と、人間は本来意欲的で自ら進んで働こうとするとする「Y理論」という、対照的な二つの人間観・管理観。", "名詞", "Managers who follow Theory X tend to closely supervise employees, while Theory Y managers trust them with more autonomy.", "経営学", "800"),
    ("Theory Z", "終身雇用や集団的な意思決定など日本的経営の要素を取り入れながら、従業員の長期的な信頼関係と組織への一体感を重視する経営理論。", "名詞", "Theory Z emphasizes long-term employment, consensus decision-making, and strong employee loyalty.", "経営学", "850"),
    ("escalation of commitment", "すでに多くの資金や時間、労力を投じてしまったという理由だけで、失敗が明らかになりつつあるプロジェクトへの追加投資をやめられず、かえって投資を拡大させてしまう心理的傾向。", "名詞", "Escalation of commitment led the executives to keep funding the failing project long after the warning signs appeared.", "経営学", "850"),
    ("organizational citizenship behavior", "職務として明確に定められてはいないものの、同僚を自発的に助けたり、組織の改善に協力したりするなど、組織全体の機能向上に資する従業員の自発的な行動。", "名詞", "Helping a new colleague learn the ropes, without being asked, is a classic example of organizational citizenship behavior.", "経営学", "850"),
    ("psychological contract", "雇用契約書には明記されていないものの、従業員と組織との間で暗黙のうちに共有されている、互いへの期待や義務についての心理的な了解・約束事。", "名詞", "When the company cut bonuses without explanation, many employees felt their psychological contract had been violated.", "経営学", "850"),
    ("equity theory", "従業員は自分の労力や貢献に対する報酬を、他者の労力と報酬の比率と比較し、その公平性の認識によってモチベーションが左右されるとする、動機づけに関する理論。", "名詞", "According to equity theory, an employee who feels underpaid relative to a coworker doing the same job may reduce their effort.", "経営学", "800"),
    ("expectancy theory", "努力すれば成果が上がる見込み、成果に応じて報酬が得られる見込み、そしてその報酬が自分にとって価値があるという期待の掛け合わせによって、人のモチベーションの強さが決まるとする理論。", "名詞", "Expectancy theory suggests that employees won't be motivated by a bonus they believe is nearly impossible to earn.", "経営学", "850"),
    ("goal-setting theory", "曖昧で簡単な目標よりも、具体的で適度に困難な目標を設定する方が、従業員のモチベーションとパフォーマンスを高めるとする理論。", "名詞", "Goal-setting theory suggests that telling someone to simply 'do your best' is less motivating than giving them a specific target.", "経営学", "800"),
    # --- 経営学: 生産管理 (8) ---
    ("kanban", "生産現場において、後工程が必要とする部品や仕掛品を、必要な時に必要な量だけ前工程から引き取るための指示情報を記したカードや仕組み。トヨタ生産方式に由来する。", "名詞", "The team used a kanban board to visualize which tasks were in progress and which were waiting to be started.", "経営学", "750"),
    ("business process reengineering", "既存の業務プロセスを部分的に改善するのではなく、コスト・品質・スピードなどの大幅な向上を目指して、業務の流れそのものを根本から見直し再設計する経営手法。BPR。", "名詞", "The company undertook business process reengineering, completely redesigning its order-to-delivery workflow.", "経営学", "800"),
    ("make-or-buy decision", "ある部品やサービスを自社の内部で生産・提供するか、それとも外部の企業から調達するかを、コストや戦略的重要性などを踏まえて判断する意思決定。内製か外部調達かの決定。", "名詞", "The make-or-buy decision came down to whether producing the component in-house would be cheaper than outsourcing it.", "経営学", "800"),
    ("economies of scale", "生産量や事業規模が拡大するにつれて、製品一単位あたりの平均費用が低下していく現象。規模の経済。", "名詞", "By building a much larger factory, the company achieved economies of scale and cut its per-unit production costs.", "経営学", "700"),
    ("diseconomies of scale", "企業や工場の規模がある程度を超えて拡大すると、組織の複雑化や調整コストの増大などにより、かえって製品一単位あたりの平均費用が上昇してしまう現象。", "名詞", "Beyond a certain size, the factory suffered from diseconomies of scale as coordination costs spiraled out of control.", "経営学", "800"),
    ("vendor-managed inventory", "従来は購入企業側が行っていた在庫の発注管理を、供給業者(ベンダー)自身が需要データをもとに担い、購入企業の在庫水準を維持・補充する仕組み。VMI。", "名詞", "Under vendor-managed inventory, the supplier monitors the retailer's stock levels and automatically replenishes them.", "経営学", "850"),
    ("enterprise resource planning", "会計・人事・生産・販売・在庫管理など、企業内の様々な業務プロセスのデータを一つの統合されたシステムで管理し、経営資源全体を効率的に計画・運用する仕組み。ERP。", "名詞", "The company implemented an enterprise resource planning system to unify its finance, HR, and inventory data.", "経営学", "800"),
    ("business continuity planning", "自然災害やシステム障害、パンデミックなど不測の事態が発生した場合でも、重要な事業活動を継続または早期に復旧できるよう、あらかじめ手順や体制を整備しておく計画。BCP。", "名詞", "After the earthquake, the company's business continuity planning allowed it to resume operations within days.", "経営学", "800"),
    # --- 経営学: サプライチェーン/オペレーション戦略 (4) ---
    ("offshoring", "製造や事務処理などの業務機能を、人件費の安い海外の拠点や海外の子会社に移転させること。海外移転。", "名詞", "The manufacturer cut costs significantly by offshoring production to a factory overseas.", "経営学", "750"),
    ("business process outsourcing", "コールセンター業務や経理事務、人事事務など、企業の特定の業務プロセスを丸ごと社外の専門業者に委託すること。BPO。", "名詞", "The bank relies on business process outsourcing to handle its customer service call center.", "経営学", "800"),
    ("demand forecasting", "過去の販売実績や市場動向などのデータをもとに、将来の製品・サービスに対する需要の量やタイミングを予測すること。生産計画や在庫管理の基礎となる。", "名詞", "Accurate demand forecasting helped the retailer avoid both stockouts and excess inventory during the holiday season.", "経営学", "750"),
    ("supply chain management", "原材料の調達から製造、物流、販売に至るまで、製品が消費者に届くまでの一連の流れ全体を、企業間の連携も含めて計画・調整・最適化すること。SCM。", "名詞", "Effective supply chain management ensured that the retailer's shelves stayed stocked despite a global shipping disruption.", "経営学", "700"),
    # --- 経営学: マーケティング (23) ---
    ("brand loyalty", "消費者が特定のブランドの製品やサービスを繰り返し選び続け、他のブランドに簡単には乗り換えようとしない、強い愛着や信頼の状態。", "名詞", "The company's strong brand loyalty meant customers kept buying its products even when competitors offered lower prices.", "経営学", "650"),
    ("customer acquisition cost", "新規顧客を一人獲得するために、広告費や営業費用など企業がどれだけの費用を投じたかを示す指標。CAC。", "名詞", "If the customer acquisition cost is higher than the profit from a typical customer, the business model isn't sustainable.", "経営学", "750"),
    ("net promoter score", "「この製品やサービスを友人や同僚に薦める可能性はどれくらいか」という質問への回答をもとに算出される、顧客ロイヤルティを測る指標。NPS。", "名詞", "The company's net promoter score rose significantly after it improved its customer support response times.", "経営学", "750"),
    ("churn rate", "ある一定期間のうちに、サービスの利用をやめたり契約を解約したりした顧客の割合。特にサブスクリプション型ビジネスで重視される指標。解約率。", "名詞", "The streaming service worked hard to lower its churn rate by improving its recommendation algorithm.", "経営学", "750"),
    ("product life cycle", "製品が市場に投入されてから、導入期・成長期・成熟期・衰退期という段階を経て売上や利益が変化していく過程を表すモデル。製品ライフサイクル。", "名詞", "As the product entered the maturity stage of its product life cycle, sales growth slowed and competition intensified.", "経営学", "700"),
    ("unique selling proposition", "競合他社の製品にはない、その製品やサービスだけが持つ独自の強みや便益であり、顧客に選ばれる決め手となる訴求点。USP。", "名詞", "The company's unique selling proposition was its 24-hour customer support, something no competitor offered.", "経営学", "700"),
    ("value proposition", "ある製品やサービスが、顧客のどのような課題を解決し、他の選択肢と比べてどのような価値を提供するのかを簡潔にまとめたもの。価値提案。", "名詞", "The startup's value proposition was clear: save small businesses time by automating their bookkeeping.", "経営学", "700"),
    ("loss leader", "原価割れに近い低価格で販売することで来店客や関心を集め、他の商品の購入につなげることを狙った、いわば客寄せ用の商品。", "名詞", "The supermarket sold milk as a loss leader, hoping shoppers would buy other, more profitable items while they were in the store.", "経営学", "750"),
    ("cross-selling", "ある商品を購入しようとしている顧客に対して、それと関連する別の商品も併せて提案し、購入してもらおうとする販売手法。", "名詞", "When customers bought a laptop, the store used cross-selling to also offer them a carrying case and extended warranty.", "経営学", "700"),
    ("upselling", "顧客が検討している商品よりも、価格の高い上位モデルやオプション追加された商品を提案し、購入単価を引き上げようとする販売手法。", "名詞", "The salesperson tried upselling the customer from the basic model to the premium version with more features.", "経営学", "700"),
    ("word-of-mouth marketing", "満足した顧客が友人や知人に自発的に製品やサービスを紹介・推薦することを通じて、評判が人から人へと広がっていくことを狙ったマーケティング手法。口コミマーケティング。", "名詞", "The small bakery grew entirely through word-of-mouth marketing, with no advertising budget at all.", "経営学", "650"),
    ("viral marketing", "面白い動画やユニークなコンテンツなどを通じて、消費者が自発的に他人へ共有・拡散したくなる仕掛けを作り、まるでウイルスのように急速に情報を広めようとするマーケティング手法。", "名詞", "The quirky commercial became viral marketing gold, racking up millions of shares within days.", "経営学", "700"),
    ("guerrilla marketing", "限られた予算の中で、街頭でのユニークなパフォーマンスや意表を突いた仕掛けなど、型破りで低コストな手法を用いて強い印象と話題性を生み出そうとするマーケティング手法。", "名詞", "The startup used guerrilla marketing, chalking eye-catching messages on sidewalks instead of buying expensive ads.", "経営学", "750"),
    ("niche marketing", "市場全体を対象にするのではなく、特定の関心や需要を持つ比較的小規模で明確に定義された顧客層(ニッチ市場)に絞り込んで展開するマーケティング戦略。", "名詞", "Rather than competing with mass-market brands, the company pursued niche marketing aimed at vegan athletes.", "経営学", "700"),
    ("mass marketing", "顧客層を細かく分けず、単一のメッセージや製品によって市場全体、できるだけ多くの潜在顧客に一斉に働きかけようとするマーケティング戦略。", "名詞", "Before the internet made targeted ads possible, most large brands relied on mass marketing through television commercials.", "経営学", "650"),
    ("brand awareness", "消費者が特定のブランドの存在をどれだけ知っているか、また商品カテゴリーを見聞きした際にそのブランドをどれだけ思い浮かべやすいかを示す度合い。ブランド認知度。", "名詞", "The advertising campaign was designed to boost brand awareness among young consumers, even before driving any sales.", "経営学", "650"),
    ("customer retention", "既存の顧客に離脱されることなく、繰り返し自社の製品やサービスを利用し続けてもらうこと、またその度合い。顧客維持。", "名詞", "The company invested in loyalty programs to improve customer retention rather than constantly chasing new customers.", "経営学", "700"),
    ("conversion rate", "ウェブサイトへの訪問者や広告の閲覧者のうち、購入や会員登録など企業が望む行動を実際に取った人の割合。転換率。", "名詞", "Redesigning the checkout page increased the website's conversion rate by fifteen percent.", "経営学", "700"),
    ("sales funnel", "見込み客が製品やサービスの認知から興味・比較検討を経て最終的な購入に至るまでの一連の段階を、入り口が広く出口が狭い漏斗(じょうご)の形にたとえて表したモデル。", "名詞", "The marketing team mapped out the sales funnel, from initial awareness to the final purchase decision.", "経営学", "700"),
    ("market penetration", "既存の製品を、まだ十分に取り込めていない既存市場の顧客層により深く浸透させ、市場占有率を高めていく成長戦略。市場浸透戦略。", "名詞", "The company pursued market penetration by lowering prices to win over customers from its competitors.", "経営学", "750"),
    ("penetration pricing", "新製品を市場に投入する際、当初は意図的に低い価格を設定して急速に顧客を獲得し、市場シェアを確保してから徐々に価格を引き上げていく価格戦略。", "名詞", "The streaming service used penetration pricing, offering a very low introductory rate to quickly build a large subscriber base.", "経営学", "800"),
    ("price skimming", "新製品を市場に投入する際、当初は高い価格を設定して早期に採用したい顧客層から大きな利益を得て、その後徐々に価格を引き下げてより幅広い顧客層を取り込んでいく価格戦略。上澄み価格戦略。", "名詞", "The electronics maker used price skimming, launching the new device at a premium price before gradually lowering it over time.", "経営学", "800"),
    ("relationship marketing", "一度きりの取引の獲得だけを目指すのではなく、顧客との長期的な信頼関係を築き、継続的な関わりを通じて生涯にわたる価値を生み出そうとするマーケティングの考え方。関係性マーケティング。", "名詞", "The company practiced relationship marketing, focusing on long-term customer engagement rather than one-time sales.", "経営学", "800"),
]


def main() -> None:
    with db() as conn:
        existing = set()
        for r in conn.execute("SELECT english FROM words").fetchall():
            existing.add(r["english"].lower())
        inserted = 0
        skipped = 0
        law_inserted = 0
        mgmt_inserted = 0
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
            if domain == "法律":
                law_inserted += 1
            elif domain == "経営学":
                mgmt_inserted += 1
        print(
            "inserted=" + str(inserted) + " (法律=" + str(law_inserted)
            + " 経営学=" + str(mgmt_inserted) + ") skipped=" + str(skipped)
        )


if __name__ == "__main__":
    main()
