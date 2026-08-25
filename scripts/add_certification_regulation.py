# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""新規ドメイン「認証・規制」+ 新規フレーズシーン「認証・規格の英語」、
authored by Claude(2026-08-26・B23バックログ「認証・規制用語」対応)。

自動車(型式認証/排出ガス規制等)・航空/無線機器(耐空証明/技適/FCC等)・
EU規制/製品安全(RoHS/REACH/CE marking等)の3系統を横断する認証・規制
まわりの実務英語。DB全体でenglishが既存語と衝突するものは除外。

No app / OpenAI API calls — hand-written(並列サブエージェントでドラフト後に
人手でdedup), inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` /
`phrases` tables.

Run:  python scripts/add_certification_regulation.py
仕上げ: 投入後に `python scripts/relevel.py` と
        `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

CERT = "認証・規制"
CERT_SCENE = "認証・規格の英語"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("type approval", "型式認証。政府や認証機関が、ある型式の自動車が法令上の安全・環境基準を満たしていることを審査し正式に承認する制度。", "名詞句", "The new EV model received type approval from the regulatory authority before it could be sold in the market.", CERT, "800"),
    ("Euro 6", "ユーロ6。欧州連合(EU)が定める自動車の排出ガス規制の段階の一つで、窒素酸化物(NOx)や粒子状物質(PM)の排出量上限を厳しく定めている。", "名詞句(固有名詞)", "All new diesel cars sold in the EU must comply with the Euro 6 emission standard.", CERT, "850"),
    ("EPA Tier 3", "EPAティア3基準。米国環境保護庁(EPA)が定める自動車の排出ガス規制段階の一つで、燃料と車両の排出基準を一体的に規制する。", "名詞句(固有名詞)", "The vehicle's engine was redesigned to meet the EPA Tier 3 emission requirements.", CERT, "850"),
    ("NCAP (New Car Assessment Programme)", "NCAP(新車アセスメントプログラム)。新車の衝突安全性能を独立機関が試験・評価し、星の数などで格付けする制度(例: Euro NCAP)。", "名詞(略語)", "The sedan earned a five-star rating in the Euro NCAP crash test.", CERT, "750"),
    ("VIN (Vehicle Identification Number)", "車両識別番号(VIN)。各自動車に割り当てられる17桁の固有コードで、製造者・車種・製造年などの情報を含み、登録やリコール管理に使われる。", "名詞句(略語)", "You can check whether a used car has an open recall by entering its VIN online.", CERT, "700"),
    ("certificate of compliance", "適合証明書。製品が該当する規格・法令の要求事項を満たしていることを証明する公式文書。", "名詞句", "The importer had to submit a certificate of compliance before customs would release the vehicles.", CERT, "800"),
    ("self-certification", "自己認証。製造者自身が、自社製品が規制基準に適合していることを試験・宣言する制度(第三者機関の認証を介さない、米国の自動車規制などで採用)。", "名詞", "Under the U.S. system, manufacturers use self-certification to confirm that their vehicles meet FMVSS requirements.", CERT, "850"),
    ("third-party certification", "第三者認証。製造者から独立した認証機関が、製品の規制適合性を審査・証明する制度。", "名詞句", "Many export markets require third-party certification rather than accepting the manufacturer's own test results.", CERT, "800"),
    ("WLTP (Worldwide Harmonized Light Vehicles Test Procedure)", "WLTP(国際調和排出ガス・燃費試験手順)。実走行に近い条件で燃費と排出ガスを測定する国際的な試験サイクルで、従来のNEDCに代わって導入された。", "名詞(略語)", "Fuel economy figures are now measured under the WLTP test cycle, which better reflects real-world driving.", CERT, "850"),
    ("safety recall", "安全性リコール。安全上の欠陥が確認された車両について、無償修理・部品交換のために行われるリコール。", "名詞句", "Owners were notified of a safety recall affecting the vehicle's braking system.", CERT, "700"),
    ("conformity of production (CoP)", "生産一致性(CoP)。量産される車両が、型式認証を受けた仕様と継続して一致していることを確認する制度・審査。", "名詞句", "Regulators conduct conformity of production audits to make sure mass-produced cars still match the approved prototype.", CERT, "850"),
    ("technical service", "技術サービス機関。当局に代わって車両や部品の試験を実施し、規制適合性を評価する権限を与えられた試験機関・検査機関。", "名詞句", "The brake system was tested by an accredited technical service before the type approval was granted.", CERT, "800"),
    ("UN Regulation (UNECE Regulation)", "国連規則(UNECE規則)。国連欧州経済委員会(UNECE)が定める自動車の安全・環境に関する国際基準で、多くの国が相互承認している。", "名詞句", "The headlamp design must comply with the relevant UN Regulation before the vehicle can be sold in Japan or the EU.", CERT, "850"),
    ("NHTSA (National Highway Traffic Safety Administration)", "米国運輸省道路交通安全局(NHTSA)。米国内の自動車安全基準の策定やリコールの監督を行う連邦政府機関。", "固有名詞(略語)", "NHTSA opened an investigation into reports of engine fires in the affected vehicles.", CERT, "850"),
    ("FMVSS (Federal Motor Vehicle Safety Standards)", "連邦自動車安全基準(FMVSS)。米国で販売される自動車が満たすべき安全性能に関する連邦規制。", "名詞(略語)", "The seatbelt design must satisfy the requirements set out in FMVSS 208.", CERT, "900"),
    ("roadworthiness test", "保安基準適合検査(日本の車検に相当)。車両が安全基準を満たし、公道走行に適した状態であることを定期的に確認する検査。", "名詞句", "The van failed its roadworthiness test because of worn brake pads.", CERT, "750"),
    ("OBD (on-board diagnostics)", "OBD(車載式故障診断装置)。車両に搭載され、エンジンや排出ガス制御系統の不具合を自動検知・記録するシステム。", "名詞句(略語)", "The mechanic plugged a scanner into the OBD port to read the fault codes.", CERT, "750"),
    ("defeat device", "ディフィートデバイス(排出ガス規制無効化装置)。試験条件下でのみ排出ガス制御を作動させ、実走行時には規制値を超えるよう不正に設計されたソフトウェアや装置。", "名詞句", "The company was fined billions of dollars for installing a defeat device that cheated emissions tests.", CERT, "850"),
    ("whole vehicle type approval (WVTA)", "車両全体型式認証(WVTA)。エンジンや車体だけでなく完成車全体として、EU域内で販売するために必要な包括的な型式認証制度。", "名詞句", "Once the model receives whole vehicle type approval, it can be sold across all EU member states without further national testing.", CERT, "900"),
    ("aftermarket parts certification", "社外部品認証。純正部品ではない交換用・改造用部品が、安全・環境基準に適合していることを確認する認証。", "名詞句", "Only aftermarket parts with proper certification should be installed on vehicles used for commercial purposes.", CERT, "800"),
    ("e-mark", "Eマーク(欧州認証マーク)。UNECE規則に適合した自動車部品に付与される、円の中に国コード番号を記したヨーロッパの認証マーク。", "名詞", "Look for the e-mark on the headlamp lens to confirm it meets European approval standards.", CERT, "800"),
    ("crash test rating", "衝突試験評価。NCAPなどの機関が実施する衝突試験の結果に基づき、車両の安全性能を星の数などで示した格付け。", "名詞句", "Consumers often compare crash test ratings before deciding which family car to buy.", CERT, "700"),
    ("IIHS (Insurance Institute for Highway Safety)", "米国道路安全保険協会(IIHS)。保険業界が資金提供する米国の非営利団体で、独自の衝突試験により車両の安全性を評価する。", "固有名詞(略語)", "The pickup truck was named a Top Safety Pick by the IIHS after passing its rigorous crash tests.", CERT, "850"),
    ("field action", "フィールドアクション(市場措置)。リコールに至らない軽微な不具合について、メーカーが無償点検・修理・部品交換などを行う対応。", "名詞句", "The dealer contacted customers about a voluntary field action to update the vehicle's software.", CERT, "800"),
    ("dynamometer test", "シャシダイナモ試験。車両やエンジンをローラー上に固定し、実走行を模擬しながら出力・燃費・排出ガスなどを測定する試験。", "名詞句", "Emission levels are measured on a chassis dynamometer test under standardized driving conditions.", CERT, "850"),
    ("approval mark", "認証マーク。当該製品が特定の規制・規格に適合していることを示すために、車両や部品に表示される公式マーク。", "名詞句", "Every imported headlight must carry a valid approval mark before it can be sold.", CERT, "700"),
    ("Airworthiness Certificate", "耐空証明書。航空機が安全基準を満たし、飛行に適した状態にあることを証明する公的文書。国の航空当局(日本では国土交通省、米国ではFAA)が発行し、これがないと商業運航はできない。", "名詞句", "The aircraft cannot be operated commercially without a valid airworthiness certificate.", CERT, "800"),
    ("Type Certificate (TC)", "型式証明。航空機・エンジン・プロペラなどの設計が耐空性基準に適合していることを証明する認証。個々の機体ではなく設計そのものに対して発行される。", "名詞句", "Boeing had to obtain a type certificate from the FAA before delivering the new aircraft model to airlines.", CERT, "850"),
    ("Supplemental Type Certificate (STC)", "追加型式証明(STC)。既に型式証明を取得した航空機に対して、改造や追加装備を行う際に必要となる補足的な証明。", "名詞句", "The company obtained a supplemental type certificate to install the new avionics system on existing aircraft.", CERT, "900"),
    ("FAA Certification", "FAA(米国連邦航空局)による認証。航空機・部品・乗員資格などが米国の安全基準に適合していることを示す。米国内で運航・販売するための必須要件。", "名詞句", "Without FAA certification, the aircraft cannot be registered or flown in United States airspace.", CERT, "800"),
    ("EASA Certification", "EASA(欧州航空安全機関)による認証。欧州連合域内で航空機や部品を運航・販売するために必要な安全適合性の証明。", "名詞句", "The manufacturer needed both FAA and EASA certification to sell the aircraft in global markets.", CERT, "850"),
    ("Production Certificate (PC)", "製造証明。型式証明を取得した設計どおりに製品を一貫して製造できる能力があることを製造者に対して発行される認証。", "名詞句", "Holding a production certificate allows the manufacturer to build aircraft that conform to the approved type design without individual inspection of each unit.", CERT, "900"),
    ("Airworthiness Directive (AD)", "耐空性改善通報。安全上の不具合が判明した航空機・部品に対して、航空当局が発行する強制的な修理・改修・点検の指示。", "名詞句", "The FAA issued an airworthiness directive requiring immediate inspection of the engine mounts on all affected aircraft.", CERT, "850"),
    ("Continued Airworthiness", "継続耐空性。航空機が就航後も引き続き安全基準を満たし続けるよう、定期整備・点検・記録管理を通じて維持すること。", "名詞句", "Airlines are responsible for the continued airworthiness of their fleet through scheduled maintenance programs.", CERT, "850"),
    ("Technical Standard Order (TSO)", "技術基準書(TSO)。航空機部品(計器、装備品など)が満たすべき最低限の性能・設計基準をFAAが定めたもの。TSO認定を受けた部品は型式証明への組み込みが容易になる。", "名詞句", "The GPS unit was designed to meet the applicable Technical Standard Order before it could be installed in certified aircraft.", CERT, "900"),
    ("Parts Manufacturer Approval (PMA)", "部品製造者認定(PMA)。航空機オリジナル部品(OEM品)以外の代替部品を製造・販売するためにFAAから取得する認定。", "名詞句", "The supplier received Parts Manufacturer Approval to produce replacement brake components for the aircraft.", CERT, "900"),
    ("Export Certificate of Airworthiness", "輸出耐空証明。航空機や部品を輸出する際、輸出国の当局が「その製品が輸入国の耐空性要件も満たしている」ことを証明する書類。", "名詞句", "An export certificate of airworthiness was required before the used aircraft could be sold to the overseas buyer.", CERT, "900"),
    ("Airworthiness Limitations", "耐空性限界。型式証明の一部として定められる、部品の使用期限や点検間隔など、安全な運用のために遵守が義務付けられる制限事項。", "名詞句", "The maintenance manual's airworthiness limitations section specifies the mandatory replacement interval for the rotor blades.", CERT, "900"),
    ("Certificate of Conformity", "適合証明書。製品(部品や完成品)が承認された設計・仕様どおりに製造されたことを製造者が証明する書類。", "名詞句", "Each shipment of components must include a certificate of conformity signed by the quality assurance department.", CERT, "800"),
    ("Radio Equipment Directive (RED)", "無線機器指令(RED)。EU域内で販売される無線機器(Wi-Fi、Bluetooth、携帯電話等)が満たすべき安全性・EMC・電波利用効率の要件を定めたEU指令(2014/53/EU)。CEマーキングの根拠の一つ。", "名詞句", "Every wireless product sold in the EU must comply with the Radio Equipment Directive before it can carry the CE mark.", CERT, "900"),
    ("Technical Conformity Mark", "技術基準適合証明(通称「技適」)。日本国内で無線機器を使用するために電波法に基づき必要な認証、およびそれを受けたことを示すマーク。技適のない無線機器は原則として日本国内で電波を発射できず、海外で購入したスマートフォンなどを日本で使う際によく問題になる。", "名詞句", "The imported Wi-Fi router lacked the Technical Conformity Mark, so it could not legally be used in Japan without additional certification.", CERT, "850"),
    ("FCC Certification", "FCC(米国連邦通信委員会)認証。無線を発する電子機器が米国内の電波干渉・安全基準に適合していることを示す認証。米国で販売する無線機器には原則必須。", "名詞句", "The device had to pass FCC certification testing before it could be marketed in the United States.", CERT, "800"),
    ("FCC ID", "FCC ID。FCC認証を取得した無線機器に付与される固有の識別番号。製品本体や取扱説明書に表示され、FCCのデータベースで認証情報を検索できる。", "名詞句", "You can look up the FCC ID printed on the back of the router to see its certification details online.", CERT, "750"),
    ("CE Marking", "CEマーキング。製品がEUの関連指令(安全性、健康、環境保護等)の要求事項に適合していることを製造者自身が宣言する証。無線機器の場合はRED等への適合が前提となる。", "名詞句", "Products bearing the CE marking indicate that they meet the essential requirements of applicable EU directives.", CERT, "700"),
    ("Conformity Assessment", "適合性評価。製品が規制上の要求事項(安全性・EMC・電波利用等)を満たしているかどうかを検証する手続き全般。自己適合宣言や第三者機関による試験・認証などの方式がある。", "名詞句", "The manufacturer completed the conformity assessment procedure before affixing the CE mark to the product.", CERT, "850"),
    ("Notified Body", "認証機関(ノーティファイドボディ)。EU加盟国が指定し、欧州委員会に通知した、製品の適合性評価(試験・審査)を行う権限を持つ第三者機関。特定の高リスク製品ではノーティファイドボディの関与が義務付けられる。", "名詞句", "For certain high-risk radio equipment, a notified body must be involved in the conformity assessment procedure.", CERT, "900"),
    ("Declaration of Conformity (DoC)", "適合宣言書。製造者が自らの責任において、製品が該当する規制・指令の要求事項をすべて満たしていることを宣言する法的文書。", "名詞句", "The manufacturer issued a Declaration of Conformity stating that the device met all applicable EU directives.", CERT, "800"),
    ("Electromagnetic Compatibility (EMC)", "電磁両立性(EMC)。機器が周囲に有害な電磁妨害を発生させず、かつ他の機器からの電磁妨害に対しても正常に動作し続ける能力。無線機器の認証で必ず試験される項目の一つ。", "名詞句", "The device failed the electromagnetic compatibility test because it interfered with nearby radio receivers.", CERT, "850"),
    ("Specific Absorption Rate (SAR)", "比吸収率(SAR)。携帯電話など人体に近接して使用する無線機器から放射される電波を、人体組織がどれだけ吸収するかを示す指標。各国で上限値が定められ、認証の際に測定が義務付けられている。", "名詞句", "Regulators require smartphone manufacturers to keep the specific absorption rate below the legal limit to protect users from excessive radio-frequency exposure.", CERT, "850"),
    ("Spectrum Allocation", "周波数割り当て(スペクトラム割当)。特定の無線業務(放送、携帯電話、Wi-Fi等)が使用できる周波数帯域を国や国際機関(ITU等)が定めること。機器の認証は割り当てられた周波数帯内での使用を前提とする。", "名詞句", "The new 5G service could not launch until the government finalized its spectrum allocation for the relevant frequency band.", CERT, "850"),
    ("License-Exempt Device", "免許不要機器(無線局)。個別の無線局免許を取得しなくても使用できる無線機器。ただし技術基準への適合(技適等)は依然として必要な場合が多い。Wi-FiやBluetoothの多くがこれに該当する。", "名詞句", "Most Bluetooth headsets are license-exempt devices, but they must still comply with the applicable technical standards.", CERT, "800"),
    ("Telecommunications Business Act", "電気通信事業法。日本国内で電気通信事業(通信サービスの提供)を行う事業者を規律する法律。無線機器の技術基準とは別に、通信サービス提供者側の義務(登録・届出等)を定める。", "名詞句", "Companies offering telecommunications services in Japan must comply with the requirements set out in the Telecommunications Business Act.", CERT, "900"),
    ("Radio Act", "電波法。日本国内での無線局の開設・運用、無線設備の技術基準(技適の根拠法)を定める法律。技適マークはこの法律に基づく認証制度。", "名詞句", "Under Japan's Radio Act, any wireless device that transmits radio waves without the required certification is subject to penalties.", CERT, "900"),
    ("IC Certification", "IC認証(カナダ)。カナダの通信規制当局ISED(旧Industry Canada)が管轄する無線機器認証制度。米国のFCC認証、日本の技適に相当する、カナダ国内での無線機器販売・使用に必要な認証。", "名詞句", "Before shipping the wireless module to Canadian customers, the company obtained IC certification in addition to its existing FCC approval.", CERT, "900"),
    ("RoHS Directive", "EU指令。電気・電子機器に含まれる鉛、水銀、カドミウムなど特定の有害物質の使用を制限する規制(Restriction of Hazardous Substances)。電子機器メーカーが製品を欧州市場に投入する際に順守が必須。", "名詞句", "All our electronic components must comply with the RoHS Directive before they can be sold in the European Union.", CERT, "800"),
    ("REACH Regulation", "化学物質の登録・評価・認可・制限に関するEU規則(Registration, Evaluation, Authorisation and Restriction of Chemicals)。EU域内で年間1トン以上製造・輸入される化学物質に登録義務を課す。", "名詞句", "The chemical supplier confirmed that all substances in the coating are registered under REACH Regulation.", CERT, "850"),
    ("WEEE Directive", "廃電気電子機器指令(Waste Electrical and Electronic Equipment)。電子機器メーカーに対し、製品の回収・リサイクル・適正処理の責任を課すEU指令。", "名詞句", "Under the WEEE Directive, manufacturers are responsible for financing the collection and recycling of end-of-life electronics.", CERT, "850"),
    ("Machinery Directive", "機械類の安全に関するEU指令。設計・製造段階での安全要求事項を定め、CEマーク取得の根拠指令の一つ。", "名詞句", "The industrial robot arm was redesigned to satisfy the essential health and safety requirements of the Machinery Directive.", CERT, "800"),
    ("Low Voltage Directive", "低電圧指令(LVD)。特定の電圧範囲(交流50〜1000V等)で使用される電気機器の安全要求を定めるEU指令。CEマークの根拠指令の一つ。", "名詞句", "Household appliances sold in Europe must meet the electrical safety requirements set out in the Low Voltage Directive.", CERT, "850"),
    ("EMC Directive", "電磁両立性指令(Electromagnetic Compatibility)。機器が他の機器に電磁妨害を与えず、また外部からの妨害に対して適切な耐性を持つことを求めるEU指令。", "名詞句", "The device failed initial testing against the EMC Directive due to excessive electromagnetic emissions.", CERT, "850"),
    ("UL certification", "米国の規格・認証機関UL(Underwriters Laboratories)による製品安全認証。北米市場で製品を販売する際に事実上必須とされることが多い。", "名詞句", "Retailers in the U.S. often refuse to stock electrical products that lack UL certification.", CERT, "750"),
    ("ETL certification", "米国の認証機関Intertekが発行する製品安全認証マーク。ULと同様にOSHA承認のNRTL(国家認定試験機関)として認められている。", "名詞句", "Our power adapter carries ETL certification, which is recognized as an equivalent alternative to UL listing in North America.", CERT, "850"),
    ("ISO 14001", "環境マネジメントシステムに関する国際規格。組織が環境負荷を継続的に低減する仕組みを構築・運用していることを認証する。", "名詞句", "The company obtained ISO 14001 certification after implementing a formal environmental management system across all plants.", CERT, "750"),
    ("technical file", "製品がEU指令・規則の要求事項に適合していることを示す技術文書一式。設計図、リスク評価、試験報告書などを含み、市場監視当局の求めに応じて提示できるよう保管が義務付けられる。", "名詞句", "Regulators can request the technical file at any time to verify that the product genuinely meets the applicable directives.", CERT, "850"),
    ("harmonized standard", "欧州標準化機関(CEN, CENELEC, ETSI等)が策定し、EU官報に公示された規格。これに準拠すれば関連指令の必須要求事項を満たしていると推定される(適合性の推定)。", "名詞句", "By designing the product to a harmonized standard, the manufacturer can claim a presumption of conformity with the directive.", CERT, "900"),
    ("market surveillance authority", "市場に流通する製品が安全規制・法令に適合しているかを監視し、違反があれば是正措置やリコールを命じる各国の行政機関。", "名詞句", "The market surveillance authority ordered the importer to withdraw the non-compliant toys from sale immediately.", CERT, "850"),
    ("product recall", "安全上の欠陥や規制違反が判明した製品を、市場や消費者の手元から回収する措置。", "名詞句", "The company issued a product recall after discovering that the battery pack posed a fire risk.", CERT, "700"),
    ("safety data sheet (SDS)", "化学製品の危険有害性情報、取扱い上の注意、応急措置などをまとめた文書。かつてはMSDS(Material Safety Data Sheet)と呼ばれた。取引先や作業者への情報提供が法律で義務付けられている。", "名詞句", "You must review the safety data sheet before handling any of the solvents stored in this warehouse.", CERT, "750"),
    ("substance of very high concern (SVHC)", "REACH規則において、発がん性・生殖毒性・難分解性・生体蓄積性などの特に高い懸念を持つとして特定された化学物質。候補リストに掲載されると情報提供義務等が発生する。", "名詞句", "The supplier had to disclose whether the plastic housing contained any substance of very high concern above the 0.1% threshold.", CERT, "900"),
    ("Ecodesign Directive", "エネルギー関連製品の設計段階から環境負荷(省エネ性能等)を考慮することを求めるEU指令。エネルギーラベル制度と密接に連動している。", "名詞句", "New refrigerator models must meet minimum energy efficiency requirements under the Ecodesign Directive before they can be marketed in the EU.", CERT, "900"),
    ("energy label", "家電製品等のエネルギー効率を等級(A〜G等)で表示するEUのラベル制度。消費者が省エネ性能を比較しやすくするために義務付けられている。", "名詞句", "The washing machine's energy label shows it belongs to the highest efficiency class available on the market.", CERT, "700"),
    ("EU Battery Regulation", "EU域内で電池・バッテリーを販売する際の製造・回収・リサイクル・カーボンフットプリント表示等に関する規則。2023年に旧Battery Directiveを刷新する形で発効した。", "名詞句", "Under the EU Battery Regulation, manufacturers will eventually need to disclose the carbon footprint of each battery model.", CERT, "900"),
    ("Packaging and Packaging Waste Regulation", "包装材および包装廃棄物に関するEU規制(PPWR)。リサイクル可能性の確保や過剰包装の削減、リサイクル材使用率の目標などを定める。", "名詞句", "The logistics team redesigned the shipping boxes to comply with the Packaging and Packaging Waste Regulation.", CERT, "900"),
    ("conflict minerals reporting", "紛争地域や高リスク地域で採掘された鉱物(タンタル・スズ・タングステン・金等)が武装勢力の資金源になっていないかをサプライチェーン上で確認・開示する報告制度。", "名詞句", "The procurement department conducts conflict minerals reporting every year to trace the origin of tantalum used in our capacitors.", CERT, "850"),
    ("General Product Safety Regulation (GPSR)", "特定の指令が適用されない消費者向け製品全般に対して、一般的な安全要求事項を課すEU規則。2023年に旧General Product Safety Directiveを置き換えた。", "名詞句", "Even products without a dedicated EU directive still fall under the General Product Safety Regulation's general safety requirement.", CERT, "900"),
    ("authorized representative", "EU域外の製造者に代わり、規制当局とのやり取りや文書保管などの義務を担うEU域内に設立された者。EU市場に製品を投入する際に選任が求められる場合がある。", "名詞句", "As a Japanese manufacturer, we appointed an authorized representative in Germany to handle regulatory correspondence within the EU.", CERT, "850"),
    ("importer obligations", "EU域外から製品を持ち込み、自らの名前で市場に投入する輸入者に課される法的義務。適合性の確認、技術文書の保管、当局への協力などを含む。", "名詞句", "Importer obligations include verifying that the manufacturer has carried out the appropriate conformity assessment procedure.", CERT, "850"),
    ("non-conformity", "製品や工程が規格・規制・仕様に定められた要求事項を満たしていない状態。監査や試験で発見され、是正措置の対象となる。", "名詞句", "The auditor flagged a non-conformity in the labeling and gave the factory thirty days to correct it.", CERT, "800"),
    ("third-party testing lab", "製造者から独立した立場で製品試験や適合性評価を行う試験機関。客観性・信頼性を確保するために、規制上第三者試験が求められる場合がある。", "名詞句", "We sent samples to an accredited third-party testing lab to obtain independent verification of the product's safety performance.", CERT, "750"),
]

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    CERT_SCENE: [
        ("We're still waiting on the CE marking certificate before we can ship this batch to the EU.", "EU向けにこのロットを出荷する前に、CEマーキングの証明書をまだ待っている状況です。"),
        ("Could you confirm the current certification status of this product for the European market?", "この製品の欧州市場向けの認証状況を確認していただけますか?"),
        ("The notified body has scheduled our factory audit for the second week of September.", "認証機関(ノーティファイドボディ)が9月第2週に工場監査の予定を入れました。"),
        ("We need to submit a corrective action plan within 30 days of the non-conformity finding.", "不適合の指摘から30日以内に是正措置計画を提出する必要があります。"),
        ("The test report shows that the device passed the radiated emissions test but failed conducted emissions.", "試験報告書によると、この機器は放射エミッション試験には合格しましたが、伝導エミッション試験には不合格でした。"),
        ("Could you send us the Declaration of Conformity and the latest test reports for this component?", "この部品の適合宣言書(DoC)と最新の試験報告書を送っていただけますか?"),
        ("We can't release the product for shipment until the type approval is finalized.", "型式認証が完了するまで、この製品を出荷することはできません。"),
        ("The recall was triggered by a non-conformity found during routine market surveillance.", "今回のリコールは、通常の市場監視の際に発見された不適合がきっかけでした。"),
        ("Our engineer is preparing a root cause analysis for the failed EMC test.", "当社のエンジニアが、EMC試験不合格の根本原因分析を準備しています。"),
        ("In Japan, any wireless device must carry the Giteki mark before it can legally transmit radio waves.", "日本では、無線を発する機器は電波を発信する前に技適マークを取得している必要があります。"),
        ("Giteki is short for 技術基準適合証明, which roughly translates to 'technical conformity certification' for radio equipment.", "技適とは『技術基準適合証明』の略で、無線機器向けの技術基準適合認証にあたります。"),
        ("Without the Giteki certification mark, this Bluetooth module can't be sold or even tested over the air in Japan.", "技適マークがないと、このBluetoothモジュールは日本国内で販売はもちろん、電波を発する試験もできません。"),
        ("We're requesting an extension on the type approval timeline due to a delay in the test lab schedule.", "試験機関のスケジュール遅延のため、型式認証の期限延長を申請しています。"),
        ("The customs officer asked us to provide proof of RoHS compliance before releasing the shipment.", "税関の担当者から、貨物を通関させる前にRoHS適合の証明を提出するよう求められました。"),
        ("We're currently in negotiations with the regulatory authority regarding the classification of this device.", "この機器の分類について、規制当局と現在交渉を進めています。"),
        ("Please make sure all suppliers submit their REACH compliance statements before the audit.", "監査の前に、すべてのサプライヤーからREACH適合宣言書を提出してもらうようにしてください。"),
        ("The auditor flagged three minor non-conformities and one major finding during the compliance audit.", "監査担当者は、コンプライアンス監査で軽微な不適合を3件、重大な指摘事項を1件挙げました。"),
        ("We need to close out the corrective actions before the certification body issues the final certificate.", "認証機関が最終証明書を発行する前に、是正措置を完了させる必要があります。"),
        ("Can you walk me through the current certification status of the new model for the US and EU markets?", "新モデルの米国・EU市場向けの現在の認証状況について説明していただけますか?"),
        ("The battery pack failed the vibration test, so we had to redesign the mounting bracket.", "バッテリーパックが振動試験に不合格だったため、取り付けブラケットを再設計する必要がありました。"),
        ("This part requires E-mark approval before it can be installed in vehicles sold in the EU.", "この部品は、EUで販売される車両に搭載する前にEマーク認証を取得する必要があります。"),
        ("We're still waiting on the FAA to issue the supplemental type certificate for this avionics upgrade.", "このアビオニクスのアップグレードについて、FAAから追加型式証明書(STC)が発行されるのをまだ待っています。"),
        ("The radio module needs FCC certification before we can market it in the United States.", "この無線モジュールは、米国で販売する前にFCC認証を取得する必要があります。"),
        ("Let's schedule a call with the certification lab to clarify the EMC test requirements.", "EMC試験の要件を明確にするため、認証試験機関との電話会議を設定しましょう。"),
        ("The customer is asking why the shipment is delayed, and I need to explain that we're still pending CE certification.", "顧客から出荷遅延の理由を聞かれていて、CE認証がまだ完了していないことを説明する必要があります。"),
        ("Our compliance team is reviewing the supplier's test data before we accept the component.", "この部品を受け入れる前に、コンプライアンスチームがサプライヤーの試験データを確認しています。"),
        ("The notified body requested additional documentation to support our risk assessment.", "認証機関から、リスクアセスメントを裏付ける追加資料の提出を求められました。"),
        ("We failed the EMC test due to excessive noise on the power line, so the design team is investigating the filter circuit.", "電源ラインのノイズが基準を超えたためEMC試験に不合格となり、設計チームがフィルタ回路を調査しています。"),
        ("Could you clarify whether this product falls under the scope of the RoHS directive?", "この製品がRoHS指令の対象範囲に含まれるかどうか、明確にしていただけますか?"),
        ("The recall notice has to be filed with the regulatory authority within 24 hours of confirming the defect.", "不具合を確認してから24時間以内に、規制当局へリコール通知を提出しなければなりません。"),
        ("We're conducting an internal audit to make sure our documentation matches the certified configuration.", "認証された構成と当社の文書が一致していることを確認するため、社内監査を実施しています。"),
        ("The supplier hasn't provided the material declaration yet, so we can't finalize the REACH assessment.", "サプライヤーからまだ材料申告書が提出されていないため、REACHの評価を完了できません。"),
        ("Type approval for the new engine is expected to take another three months, given the current backlog at the test lab.", "試験機関の現在の混雑状況を考えると、新エンジンの型式認証にはあと3か月ほどかかる見込みです。"),
        ("We need to explain to the customer that the product can't be shipped until we receive the certificate of conformity.", "適合証明書を受領するまで製品を出荷できないことを、顧客に説明する必要があります。"),
        ("The auditor asked to see our calibration records for the test equipment used in the EMC chamber.", "監査担当者から、EMCチャンバーで使用した試験機器の校正記録の提示を求められました。"),
        ("Given the non-conformity, we've placed a hold on all outbound shipments of this batch.", "この不適合を受けて、このロットの出荷をすべて保留にしました。"),
        ("We're negotiating with customs to release the shipment under a temporary import permit while certification is pending.", "認証手続きが完了するまでの間、一時輸入許可のもとで貨物を通関させてもらえるよう税関と交渉しています。"),
        ("Our regulatory affairs team is preparing the technical file required for the CE self-declaration.", "規制対応チームが、CE自己適合宣言に必要な技術文書を準備しています。"),
        ("Please confirm that the accredited lab conducting the test is recognized under the mutual recognition agreement.", "試験を実施する認定試験機関が、相互承認協定のもとで認められている機関かどうかご確認ください。"),
        ("The customer wants a firm commitment on when we'll obtain UL certification for the power adapter.", "顧客は、電源アダプターのUL認証をいつ取得できるか明確な回答を求めています。"),
    ],
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
    raise SystemExit(main())
