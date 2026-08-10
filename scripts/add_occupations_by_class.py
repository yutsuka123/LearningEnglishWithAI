# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add more "職業" domain vocabulary, organized by five occupational classes
(社会階層・職種カテゴリ別の職業語彙拡充), authored by Claude (2026-08-10・
ユーザー要望).

対象カテゴリ(各カテゴリ25〜31語、合計145語):
1. エッセンシャルワーカー(30語): healthcare worker, paramedic, emergency
   medical technician (EMT), ambulance driver, grocery store worker,
   sanitation worker, public transit operator, bus driver, subway operator,
   utility worker, warehouse worker, food service worker, childcare worker,
   postal worker, mail carrier, emergency dispatcher, water treatment
   operator, power line technician, school bus driver, home health aide,
   distribution center worker, essential worker, meat processing worker,
   agricultural worker, frontline worker, critical infrastructure worker,
   telecommunications technician, shelter worker, food bank worker, blood
   bank technician。
2. ブルーカラー(27語): auto mechanic, diesel mechanic, HVAC technician,
   electrical lineman, dockworker, millwright, boilermaker, pipe layer,
   concrete finisher, rigger, CNC machine operator, toolmaker, upholsterer,
   flooring installer, drywall installer, elevator mechanic, freight
   handler, oil rig worker, pipeline worker, metal fabricator, asphalt
   worker, cable installer, industrial cleaner, industrial painter, power
   plant operator, sandblaster, shipyard worker。
3. ホワイトカラー(28語): financial analyst, HR specialist, marketing
   specialist, project manager, business analyst, office manager,
   executive assistant, compliance officer, risk manager, product manager,
   operations manager, sales manager, data analyst, corporate lawyer,
   investment banker, payroll manager, benefits coordinator, recruiter,
   customer success manager, supply chain manager, legal secretary, claims
   adjuster, financial controller, corporate trainer, public relations
   specialist, business development manager, logistics coordinator,
   training coordinator。
4. ITエンジニア職種(29語・肩書きのみ、プログラミング言語/ソフトウェア工学
   の技術用語とは別枠): backend engineer, frontend engineer, full-stack
   engineer, DevOps engineer, QA engineer, security engineer, data
   engineer, network engineer, site reliability engineer (SRE), machine
   learning engineer, mobile app developer, database administrator (DBA),
   cloud engineer, platform engineer, infrastructure engineer, solutions
   architect, systems administrator, IT support specialist, help desk
   technician, release engineer, data architect, network administrator,
   blockchain engineer, firmware engineer, technical writer, cybersecurity
   analyst, penetration tester, business intelligence analyst, software
   architect。
5. 職人(31語): dyer, lacquerware craftsman, tatami maker, ramen chef,
   shoemaker, bamboo craftsman, doll maker, washi papermaker, kimono maker,
   knife maker, woodcarver, silversmith, goldsmith, coppersmith, kite
   maker, fan maker, embroiderer, leatherworker, watchmaker, luthier,
   master craftsman, artisan, indigo dyer, soba noodle maker, miso maker,
   tofu maker, knife sharpener, bookbinder, seal carver, kintsugi
   craftsman, wagashi maker。

重複回避のため事前確認した既存語彙: DBの`words`テーブル全体
(`SELECT lower(english) FROM words`)に対して本ファイルの全候補語を
突き合わせ、完全一致するものは除外した。特に`職業`ドメインには既に
450語超が存在する(civil servant/police officer/engineer各種/designer/
teacher各種/researcher/professor各種/CTO/board director/YouTuber/doctor/
nurse/pastry chef/manga artist/florist/consultant/esports player/drone
operator/social media manager/UX designer/illustrator/cosplayer/content
creator等)ほか、`accountant`(ビジネス)/`actuary`・`administrative
assistant`・`office administrator`(職業)/`electrician`(生活)/
`technician`・`skilled worker`(製造/IT)等も既存。さらに`domain`が空欄の
既存語として`plumber`/`welder`/`receptionist`が、`法律`ドメインに
`paralegal`が、`薬学(処方薬)`ドメインに`pharmacy technician`が、
`和食`ドメインに`sushi chef`が判明したため、これらは対象から除外し、
代替語(ambulance driver/sandblaster・shipyard worker/logistics
coordinator・training coordinator/wagashi maker)に置き換えた。

実在の人物名・企業名は使用していない。

No app / OpenAI API calls — everything is hand-written. Duplicates are
skipped by english (lowercased), matching the pattern in
scripts/add_tabletop_trpg.py. This script only defines data; it is not
run as part of writing it (投入は別途 `python scripts/
add_occupations_by_class.py` を実行すること).

Run:  python scripts/add_occupations_by_class.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 1. エッセンシャルワーカー(社会機能を維持する必須職) ---
    ("healthcare worker", "医療従事者", "名詞", "Healthcare workers were essential during the pandemic.", "職業", "500"),
    ("paramedic", "救急救命士", "名詞", "The paramedic checked the patient's pulse immediately.", "職業", "650"),
    ("emergency medical technician (EMT)", "救急救命士(EMT)", "名詞", "An emergency medical technician arrived within minutes.", "職業", "750"),
    ("ambulance driver", "救急車の運転手", "名詞", "The ambulance driver navigated through heavy traffic.", "職業", "550"),
    ("grocery store worker", "スーパーの店員", "名詞", "Grocery store workers kept the shelves stocked during the shortage.", "職業", "450"),
    ("sanitation worker", "清掃作業員(ごみ収集等)", "名詞", "Sanitation workers collect trash early in the morning.", "職業", "550"),
    ("public transit operator", "公共交通機関の運行係員", "名詞", "Public transit operators kept the buses running on schedule.", "職業", "600"),
    ("bus driver", "バス運転手", "名詞", "The bus driver waited for the elderly passenger to sit down.", "職業", "400"),
    ("subway operator", "地下鉄の運転士", "名詞", "The subway operator announced the next station.", "職業", "600"),
    ("utility worker", "公益事業の作業員", "名詞", "Utility workers restored power after the storm.", "職業", "550"),
    ("warehouse worker", "倉庫作業員", "名詞", "Warehouse workers pack and ship online orders.", "職業", "450"),
    ("food service worker", "飲食サービス従事者", "名詞", "Food service workers prepared meals for hospital patients.", "職業", "450"),
    ("childcare worker", "保育従事者", "名詞", "Childcare workers look after young children while parents work.", "職業", "500"),
    ("postal worker", "郵便配達員", "名詞", "The postal worker delivers mail to every house on this street.", "職業", "450"),
    ("mail carrier", "郵便配達員", "名詞", "The mail carrier greeted us with a smile every morning.", "職業", "450"),
    ("emergency dispatcher", "緊急通報の指令係", "名詞", "The emergency dispatcher calmly guided the caller through CPR.", "職業", "700"),
    ("water treatment operator", "浄水場の運転員", "名詞", "Water treatment operators make sure tap water is safe to drink.", "職業", "650"),
    ("power line technician", "送電線技術者", "名詞", "Power line technicians repaired the damaged cables after the typhoon.", "職業", "650"),
    ("school bus driver", "スクールバスの運転手", "名詞", "The school bus driver checks that every child is seated safely.", "職業", "500"),
    ("home health aide", "訪問介護士", "名詞", "The home health aide visits the elderly man twice a week.", "職業", "600"),
    ("distribution center worker", "物流センターの作業員", "名詞", "Distribution center workers sort packages for next-day delivery.", "職業", "550"),
    ("essential worker", "エッセンシャルワーカー", "名詞", "Essential workers kept society running during the lockdown.", "職業", "500"),
    ("meat processing worker", "食肉加工作業員", "名詞", "Meat processing workers follow strict hygiene rules.", "職業", "600"),
    ("agricultural worker", "農業労働者", "名詞", "Agricultural workers harvest crops through the busy season.", "職業", "500"),
    ("frontline worker", "最前線で働く労働者", "名詞", "Frontline workers faced the highest risk during the outbreak.", "職業", "600"),
    ("critical infrastructure worker", "重要インフラの労働者", "名詞", "Critical infrastructure workers keep the power grid and water supply running.", "職業", "700"),
    ("telecommunications technician", "通信技術者", "名詞", "The telecommunications technician repaired the fiber-optic line.", "職業", "650"),
    ("shelter worker", "避難所の運営スタッフ", "名詞", "Shelter workers handed out blankets and hot meals.", "職業", "600"),
    ("food bank worker", "フードバンクの職員", "名詞", "Food bank workers sorted donations for families in need.", "職業", "600"),
    ("blood bank technician", "血液バンクの技師", "名詞", "The blood bank technician tested each donation for safety.", "職業", "700"),
    # --- 2. ブルーカラー(製造・建設・現場系の労働職) ---
    ("auto mechanic", "自動車整備士", "名詞", "The auto mechanic replaced the car's brake pads.", "職業", "500"),
    ("diesel mechanic", "ディーゼル整備士", "名詞", "The diesel mechanic services large trucks and buses.", "職業", "600"),
    ("HVAC technician", "空調設備技術者", "名詞", "The HVAC technician fixed the broken air conditioner.", "職業", "650"),
    ("electrical lineman", "電気配線工(架線工)", "名詞", "The electrical lineman climbed the pole to repair the wire.", "職業", "650"),
    ("dockworker", "港湾労働者", "名詞", "Dockworkers unloaded containers from the cargo ship.", "職業", "550"),
    ("millwright", "機械据付工", "名詞", "The millwright installed the new factory machinery.", "職業", "800"),
    ("boilermaker", "ボイラー製造工", "名詞", "The boilermaker welded the steel plates of the tank.", "職業", "800"),
    ("pipe layer", "配管敷設工", "名詞", "Pipe layers dug the trench and laid new water pipes.", "職業", "700"),
    ("concrete finisher", "コンクリート仕上げ工", "名詞", "The concrete finisher smoothed the surface before it hardened.", "職業", "700"),
    ("rigger", "玉掛け工", "名詞", "The rigger attached the cables before the crane lifted the beam.", "職業", "750"),
    ("CNC machine operator", "CNC工作機械オペレーター", "名詞", "The CNC machine operator programmed the cutting pattern.", "職業", "750"),
    ("toolmaker", "金型工", "名詞", "The toolmaker crafted a precise mold for the new part.", "職業", "750"),
    ("upholsterer", "家具張り職人", "名詞", "The upholsterer replaced the worn fabric on the sofa.", "職業", "750"),
    ("flooring installer", "床材施工工", "名詞", "The flooring installer laid new hardwood in the living room.", "職業", "600"),
    ("drywall installer", "石膏ボード施工工", "名詞", "The drywall installer finished the interior walls in a day.", "職業", "650"),
    ("elevator mechanic", "エレベーター整備士", "名詞", "The elevator mechanic inspects the cables every month.", "職業", "750"),
    ("freight handler", "貨物取扱作業員", "名詞", "Freight handlers load and unload trucks at the terminal.", "職業", "550"),
    ("oil rig worker", "石油掘削作業員", "名詞", "Oil rig workers often work far offshore for weeks at a time.", "職業", "700"),
    ("pipeline worker", "パイプライン建設作業員", "名詞", "Pipeline workers welded sections of pipe across the desert.", "職業", "700"),
    ("metal fabricator", "金属加工工", "名詞", "The metal fabricator cut and shaped steel beams for the bridge.", "職業", "700"),
    ("asphalt worker", "アスファルト舗装作業員", "名詞", "Asphalt workers repaved the road overnight to avoid traffic.", "職業", "600"),
    ("cable installer", "ケーブル配線工", "名詞", "The cable installer ran new wiring through the building.", "職業", "600"),
    ("industrial cleaner", "産業用清掃作業員", "名詞", "Industrial cleaners sanitize the factory floor after each shift.", "職業", "550"),
    ("industrial painter", "工業用塗装工", "名詞", "The industrial painter coated the bridge to prevent rust.", "職業", "650"),
    ("power plant operator", "発電所運転員", "名詞", "The power plant operator monitors the turbines around the clock.", "職業", "700"),
    ("sandblaster", "サンドブラスト作業員", "名詞", "The sandblaster removed old paint from the hull with high-pressure sand.", "職業", "750"),
    ("shipyard worker", "造船所作業員", "名詞", "Shipyard workers assembled the hull section by section.", "職業", "650"),
    # --- 3. ホワイトカラー(オフィス・専門職系) ---
    ("financial analyst", "財務アナリスト", "名詞", "The financial analyst reviewed the company's quarterly earnings.", "職業", "700"),
    ("HR specialist", "人事スペシャリスト", "名詞", "The HR specialist handled the new employee's paperwork.", "職業", "600"),
    ("marketing specialist", "マーケティング担当者", "名詞", "The marketing specialist launched a new social media campaign.", "職業", "600"),
    ("project manager", "プロジェクトマネージャー", "名詞", "The project manager set a deadline for the next milestone.", "職業", "550"),
    ("business analyst", "ビジネスアナリスト", "名詞", "The business analyst gathered requirements from each department.", "職業", "700"),
    ("office manager", "オフィスマネージャー", "名詞", "The office manager ordered new supplies for the team.", "職業", "500"),
    ("executive assistant", "エグゼクティブアシスタント", "名詞", "The executive assistant scheduled all of the CEO's meetings.", "職業", "600"),
    ("compliance officer", "コンプライアンス担当者", "名詞", "The compliance officer made sure the firm followed the new regulations.", "職業", "750"),
    ("risk manager", "リスクマネージャー", "名詞", "The risk manager assessed the potential losses from the merger.", "職業", "750"),
    ("product manager", "プロダクトマネージャー", "名詞", "The product manager decided which features to build next.", "職業", "650"),
    ("operations manager", "オペレーションマネージャー", "名詞", "The operations manager streamlined the warehouse workflow.", "職業", "650"),
    ("sales manager", "営業マネージャー", "名詞", "The sales manager set targets for the whole team this quarter.", "職業", "550"),
    ("data analyst", "データアナリスト", "名詞", "The data analyst built a dashboard to track website traffic.", "職業", "650"),
    ("corporate lawyer", "企業弁護士", "名詞", "The corporate lawyer reviewed the merger contract carefully.", "職業", "800"),
    ("investment banker", "投資銀行家", "名詞", "The investment banker advised the startup on its IPO.", "職業", "850"),
    ("payroll manager", "給与管理責任者", "名詞", "The payroll manager makes sure everyone is paid on time.", "職業", "650"),
    ("benefits coordinator", "福利厚生担当者", "名詞", "The benefits coordinator explained the health insurance options.", "職業", "650"),
    ("recruiter", "採用担当者", "名詞", "The recruiter reached out to several candidates online.", "職業", "550"),
    ("customer success manager", "カスタマーサクセスマネージャー", "名詞", "The customer success manager checked in with the client every month.", "職業", "650"),
    ("supply chain manager", "サプライチェーンマネージャー", "名詞", "The supply chain manager coordinated shipments from three factories.", "職業", "750"),
    ("legal secretary", "法律事務所の秘書", "名詞", "The legal secretary prepared the documents for tomorrow's hearing.", "職業", "650"),
    ("claims adjuster", "保険金査定人", "名詞", "The claims adjuster inspected the damaged car before approving payment.", "職業", "800"),
    ("financial controller", "財務統括責任者", "名詞", "The financial controller oversees the company's entire budget.", "職業", "800"),
    ("corporate trainer", "企業研修講師", "名詞", "The corporate trainer led a workshop on effective communication.", "職業", "650"),
    ("public relations specialist", "広報担当者", "名詞", "The public relations specialist drafted a statement for the press.", "職業", "700"),
    ("business development manager", "事業開発マネージャー", "名詞", "The business development manager pitched a new partnership deal.", "職業", "750"),
    ("logistics coordinator", "物流コーディネーター", "名詞", "The logistics coordinator tracked every shipment in real time.", "職業", "650"),
    ("training coordinator", "研修コーディネーター", "名詞", "The training coordinator scheduled onboarding sessions for new hires.", "職業", "600"),
    # --- 4. ITエンジニア職種(肩書き) ---
    ("backend engineer", "バックエンドエンジニア", "名詞", "The backend engineer optimized the database queries.", "職業", "650"),
    ("frontend engineer", "フロントエンドエンジニア", "名詞", "The frontend engineer built the new login screen.", "職業", "650"),
    ("full-stack engineer", "フルスタックエンジニア", "名詞", "A full-stack engineer works on both the server and the interface.", "職業", "700"),
    ("DevOps engineer", "DevOpsエンジニア", "名詞", "The DevOps engineer automated the deployment pipeline.", "職業", "750"),
    ("QA engineer", "QAエンジニア(品質保証)", "名詞", "The QA engineer found three bugs before the release.", "職業", "650"),
    ("security engineer", "セキュリティエンジニア", "名詞", "The security engineer patched the vulnerability overnight.", "職業", "750"),
    ("data engineer", "データエンジニア", "名詞", "The data engineer built a pipeline to clean the raw data.", "職業", "700"),
    ("network engineer", "ネットワークエンジニア", "名詞", "The network engineer configured the new office router.", "職業", "650"),
    ("site reliability engineer (SRE)", "サイト信頼性エンジニア(SRE)", "名詞", "The site reliability engineer kept the service running during peak traffic.", "職業", "800"),
    ("machine learning engineer", "機械学習エンジニア", "名詞", "The machine learning engineer trained a model to detect fraud.", "職業", "800"),
    ("mobile app developer", "モバイルアプリ開発者", "名詞", "The mobile app developer released an update to fix the crash.", "職業", "650"),
    ("database administrator (DBA)", "データベース管理者(DBA)", "名詞", "The database administrator backed up the server every night.", "職業", "700"),
    ("cloud engineer", "クラウドエンジニア", "名詞", "The cloud engineer migrated the app to a new server.", "職業", "750"),
    ("platform engineer", "プラットフォームエンジニア", "名詞", "The platform engineer maintains the tools every developer relies on.", "職業", "800"),
    ("infrastructure engineer", "インフラエンジニア", "名詞", "The infrastructure engineer upgraded the company's server racks.", "職業", "750"),
    ("solutions architect", "ソリューションアーキテクト", "名詞", "The solutions architect designed the system for a new client.", "職業", "800"),
    ("systems administrator", "システム管理者", "名詞", "The systems administrator resets passwords for locked accounts.", "職業", "600"),
    ("IT support specialist", "ITサポート担当者", "名詞", "The IT support specialist fixed my printer over the phone.", "職業", "550"),
    ("help desk technician", "ヘルプデスク担当者", "名詞", "The help desk technician walked me through resetting my password.", "職業", "550"),
    ("release engineer", "リリースエンジニア", "名詞", "The release engineer scheduled the software update for midnight.", "職業", "800"),
    ("data architect", "データアーキテクト", "名詞", "The data architect designed the structure of the new database.", "職業", "850"),
    ("network administrator", "ネットワーク管理者", "名詞", "The network administrator monitors traffic across all branches.", "職業", "650"),
    ("blockchain engineer", "ブロックチェーンエンジニア", "名詞", "The blockchain engineer wrote the smart contract for the app.", "職業", "850"),
    ("firmware engineer", "ファームウェアエンジニア", "名詞", "The firmware engineer wrote code that runs directly on the device.", "職業", "850"),
    ("technical writer", "テクニカルライター", "名詞", "The technical writer documented how to use the new API.", "職業", "650"),
    ("cybersecurity analyst", "サイバーセキュリティアナリスト", "名詞", "The cybersecurity analyst investigated the suspicious login attempt.", "職業", "750"),
    ("penetration tester", "ペネトレーションテスター", "名詞", "The penetration tester tried to break into the system legally.", "職業", "850"),
    ("business intelligence analyst", "ビジネスインテリジェンスアナリスト", "名詞", "The business intelligence analyst turned sales data into charts.", "職業", "750"),
    ("software architect", "ソフトウェアアーキテクト", "名詞", "The software architect decided how the modules would fit together.", "職業", "850"),
    # --- 5. 職人(伝統工芸・熟練の技を持つ職人) ---
    ("dyer", "染物職人", "名詞", "The dyer mixed natural pigments to color the fabric.", "職業", "700"),
    ("lacquerware craftsman", "漆器職人", "名詞", "The lacquerware craftsman applied dozens of thin coats by hand.", "職業", "800"),
    ("tatami maker", "畳職人", "名詞", "The tatami maker wove fresh rush grass into a new mat.", "職業", "800"),
    ("ramen chef", "ラーメン職人", "名詞", "The ramen chef has simmered the same broth recipe for decades.", "職業", "550"),
    ("shoemaker", "靴職人(製靴)", "名詞", "The shoemaker cut the leather by hand for each pair.", "職業", "650"),
    ("bamboo craftsman", "竹細工職人", "名詞", "The bamboo craftsman wove a basket from thin strips of bamboo.", "職業", "800"),
    ("doll maker", "人形職人", "名詞", "The doll maker carved each face with careful detail.", "職業", "750"),
    ("washi papermaker", "和紙職人", "名詞", "The washi papermaker dried each sheet in the sun by hand.", "職業", "850"),
    ("kimono maker", "着物職人", "名詞", "The kimono maker stitched the silk fabric with great precision.", "職業", "800"),
    ("knife maker", "刃物職人", "名詞", "The knife maker hammered the blade for hours to sharpen its edge.", "職業", "750"),
    ("woodcarver", "木彫職人", "名詞", "The woodcarver spent months carving the temple statue.", "職業", "700"),
    ("silversmith", "銀細工職人", "名詞", "The silversmith shaped the ring by hand.", "職業", "750"),
    ("goldsmith", "金細工職人", "名詞", "The goldsmith polished the necklace until it shone.", "職業", "750"),
    ("coppersmith", "銅細工職人", "名詞", "The coppersmith hammered the sheet into a round kettle.", "職業", "800"),
    ("kite maker", "凧職人", "名詞", "The kite maker painted a dragon on the bamboo frame.", "職業", "800"),
    ("fan maker", "扇子職人", "名詞", "The fan maker glued paper onto the thin bamboo ribs.", "職業", "800"),
    ("embroiderer", "刺繍職人", "名詞", "The embroiderer added gold thread to the ceremonial robe.", "職業", "800"),
    ("leatherworker", "革職人", "名詞", "The leatherworker stitched a wallet from a single piece of leather.", "職業", "700"),
    ("watchmaker", "時計職人", "名詞", "The watchmaker assembled the tiny gears under a magnifying glass.", "職業", "750"),
    ("luthier", "弦楽器製作者", "名詞", "The luthier carved the violin's body from a single block of wood.", "職業", "900"),
    ("master craftsman", "熟練職人", "名詞", "The master craftsman trained his apprentice for over ten years.", "職業", "750"),
    ("artisan", "職人(手仕事の専門家)", "名詞", "Every piece the artisan makes is slightly different from the last.", "職業", "600"),
    ("indigo dyer", "藍染め職人", "名詞", "The indigo dyer dipped the cloth into the vat again and again.", "職業", "850"),
    ("soba noodle maker", "そば職人", "名詞", "The soba noodle maker rolled the dough thin before cutting it.", "職業", "700"),
    ("miso maker", "味噌職人", "名詞", "The miso maker let the soybean paste ferment for over a year.", "職業", "800"),
    ("tofu maker", "豆腐職人", "名詞", "The tofu maker starts pressing soybeans before sunrise.", "職業", "700"),
    ("knife sharpener", "研ぎ師", "名詞", "The knife sharpener restored the old blade's edge in minutes.", "職業", "750"),
    ("bookbinder", "製本職人", "名詞", "The bookbinder repaired the antique book's torn spine.", "職業", "800"),
    ("seal carver", "印章彫刻師(はんこ職人)", "名詞", "The seal carver engraved the customer's name into the stone.", "職業", "850"),
    ("kintsugi craftsman", "金継ぎ職人", "名詞", "The kintsugi craftsman repaired the broken bowl with gold lacquer.", "職業", "900"),
    ("wagashi maker", "和菓子職人", "名詞", "The wagashi maker shaped the sweet dough into a delicate flower.", "職業", "750"),
]

PHRASES: list[tuple[str, str]] = [
    ("What kind of work do you do?", "どんなお仕事をされていますか？"),
    ("I work as a backend engineer for a software company.", "ソフトウェア会社でバックエンドエンジニアとして働いています。"),
    ("She's studying to become a paramedic.", "彼女は救急救命士になるために勉強しています。"),
    ("He switched careers from sales to project management.", "彼は営業からプロジェクトマネジメントへ転職しました。"),
    ("My uncle has worked as a shipyard worker for twenty years.", "私のおじは20年間、造船所の作業員として働いています。"),
    ("Could you tell me more about your job as a data analyst?", "データアナリストとしてのお仕事について、もっと教えていただけますか？"),
    ("He's training to become a sushi chef under a master craftsman.", "彼は熟練職人のもとで寿司職人になるための修業をしています。"),
    ("She recently got promoted to operations manager.", "彼女は最近、オペレーションマネージャーに昇進しました。"),
    ("What made you want to become a healthcare worker?", "なぜ医療従事者になろうと思ったのですか？"),
    ("He's applying for a job as a network engineer.", "彼はネットワークエンジニアの職に応募しています。"),
    ("The recruiter called me back about the interview.", "採用担当者が面接について折り返しの電話をくれました。"),
    ("She works long shifts as an emergency dispatcher.", "彼女は緊急通報の指令係として長時間の勤務をしています。"),
    ("My grandfather was a tatami maker in Kyoto.", "私の祖父は京都で畳職人をしていました。"),
    ("I'd like to work as a mobile app developer someday.", "いつかモバイルアプリ開発者として働きたいです。"),
    ("He's the only luthier in this small town.", "この小さな町で弦楽器製作者は彼だけです。"),
    ("Can you describe your daily tasks as a warehouse worker?", "倉庫作業員としての日々の仕事内容を教えてもらえますか？"),
    ("She's thinking about becoming a financial analyst after graduation.", "彼女は卒業後、財務アナリストになることを考えています。"),
    ("He trained for years to become a master craftsman.", "彼は熟練職人になるために何年も修業しました。"),
    ("Being a frontline worker during the pandemic was exhausting.", "パンデミックの間、最前線で働く労働者でいることは疲れることでした。"),
    ("I never expected to end up as a security engineer.", "セキュリティエンジニアになるとは思ってもいませんでした。"),
    ("She's the youngest goldsmith in her family's workshop.", "彼女は家業の工房で最年少の金細工職人です。"),
    ("He delivers packages every day as a freight handler.", "彼は貨物取扱作業員として毎日荷物を配送しています。"),
    ("What skills do you need to become a QA engineer?", "QAエンジニアになるにはどんなスキルが必要ですか？"),
    ("My sister works as a compliance officer at a bank.", "私の姉は銀行でコンプライアンス担当者として働いています。"),
    ("He apprenticed under a knife maker for five years.", "彼は5年間、刃物職人のもとで修業しました。"),
    ("I heard you're now working as a product manager.", "今はプロダクトマネージャーとして働いていると聞きました。"),
    ("She's proud to be an essential worker at the hospital.", "彼女は病院でエッセンシャルワーカーであることを誇りに思っています。"),
    ("He wants to become a site reliability engineer next year.", "彼は来年、サイト信頼性エンジニアになりたいと思っています。"),
    ("The tofu maker starts his work before dawn every day.", "その豆腐職人は毎日夜明け前から仕事を始めます。"),
    ("She's applying for a promotion to financial controller.", "彼女は財務統括責任者への昇進に応募しています。"),
    ("What does a supply chain manager actually do?", "サプライチェーンマネージャーとは実際に何をする仕事ですか？"),
    ("He learned kintsugi from a craftsman in his village.", "彼は村の職人から金継ぎを学びました。"),
    ("I'm interested in becoming a cybersecurity analyst.", "サイバーセキュリティアナリストになることに興味があります。"),
    ("She balances two jobs as a nurse and a home health aide.", "彼女は看護師と訪問介護士の2つの仕事を両立させています。"),
    ("He's proud of the family tradition of being a miso maker.", "彼は味噌職人という家業の伝統を誇りに思っています。"),
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
        for en, ja in PHRASES:
            if en.lower() in existing_phrases:
                p_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, '職業の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
