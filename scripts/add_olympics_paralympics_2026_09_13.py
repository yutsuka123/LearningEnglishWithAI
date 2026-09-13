# ruff: noqa: E501
"""オリンピック・パラリンピック新ドメイン(2026-09-13・authored by Claude)。

ユーザー提起のバックログ項目(B26): 既存の`スポーツ`(58語)・`スポーツ科学`(32語)・
`モータースポーツ`(20語)・`球技・アウトドアスポーツ`(36語)にはオリンピック・
パラリンピック固有の語彙(大会運営用語、種目名、パラ競技のクラス分けなど)が
無いため、新ドメイン`オリンピック・パラリンピック`として追加する。

対象は東京2020〜ミラノ・コルティナ2026前後の直近の大会を中心に、
- 大会運営・IOC/IPC関連の一般オリンピック語彙
- パラリンピック固有の競技・用具・クラス分け語彙
- 夏季・冬季それぞれの種目名(直近の新規採用・除外種目を含む)
をカバーする。

事実確認について: 種目の採用・除外年やクラス分けコードなど、確度の高い事実は
断定的に記述し、将来の大会(2028年ロサンゼルス大会など)に関する予定事項や
未確定に近い事実は「とされる」等の表現でヘッジしている。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table
(16,038語、2026-09-13時点)。以下は特に重複を確認済み:
  - 既存の`スポーツ`ドメインに既にある: medal, torch, podium, doping,
    personal best, athlete, oath, relay, marathon, badminton, volleyball,
    equestrian, golf, gymnastics, handball, rugby, skateboarding, surfing,
    table tennis, triathlon (→ いずれも本バッチには含めない)
  - 既存の`アウトドア・レジャー`ドメインに既にある: BMX, alpine skiing,
    cross-country skiing, snowboarding, biathlon, bobsled, luge, skeleton,
    speed skating, figure skating, halfpipe (→ 同様に含めない)
  - その他: classification(`AI`ドメイン), pictogram(`インバウンド`ドメイン)

Run:  python scripts/add_olympics_paralympics_2026_09_13.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

DOMAIN = "オリンピック・パラリンピック"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 一般オリンピック語彙 ---
    ("Olympic Games", "国際オリンピック委員会(IOC)が主催し、夏季・冬季それぞれ4年に一度開催される世界最大級の総合スポーツ競技大会。", "名詞", "Over 10,000 athletes from around the world compete in the Olympic Games every four years.", DOMAIN, "600"),
    ("Olympiad", "オリンピック競技大会と次回大会までの4年間の周期そのものを指す語。古代ギリシャの暦の単位に由来する。", "名詞", "The 2020 Games, delayed by a year, were still officially called the Games of the XXXII Olympiad.", DOMAIN, "750"),
    ("Olympic Village", "大会期間中、参加する選手や役員が滞在するために大会組織委員会が用意する専用の宿泊施設群。", "名詞", "Athletes from rival countries often become friends while staying together in the Olympic Village.", DOMAIN, "550"),
    ("torch relay", "開催地に聖火を運ぶため、多数のランナーが区間ごとにトーチを引き継ぎながら国内外を巡る行事。", "名詞", "The torch relay traveled through hundreds of towns before reaching the opening ceremony.", DOMAIN, "550"),
    ("torchbearer", "聖火リレーにおいて、区間ごとに聖火を持って走る一人ひとりのランナー。", "名詞", "She was chosen as a torchbearer to carry the flame through her hometown.", DOMAIN, "650"),
    ("cauldron", "開会式で聖火が最終的に点火され、大会期間中燃え続ける大型の聖火台。", "名詞", "The final torchbearer lit the Olympic cauldron as fireworks lit up the night sky.", DOMAIN, "650"),
    ("opening ceremony", "各国選手団の入場行進や聖火点火などを含む、大会の開幕を祝う式典。", "名詞", "Millions of viewers around the world watched the opening ceremony live on television.", DOMAIN, "500"),
    ("closing ceremony", "全競技の終了後に開催される、大会の締めくくりとして行われる式典。次回開催地への引き継ぎも行われる。", "名詞", "Flags were lowered and the Olympic flame was extinguished during the closing ceremony.", DOMAIN, "500"),
    ("parade of nations", "開会式で各国・地域の選手団が自国の旗を先頭に会場内を行進すること。", "名詞", "Greece traditionally leads the parade of nations, and the host country's team enters last.", DOMAIN, "650"),
    ("flag bearer", "開会式の入場行進などで、自国・地域の旗を掲げて選手団の先頭を歩く選手。", "名詞", "The veteran swimmer was honored to be chosen as the flag bearer for her country.", DOMAIN, "600"),
    ("mascot", "大会を象徴するために作られた、その土地や文化にちなんだ架空のキャラクター。", "名詞", "Children lined up to take photos with the Olympic mascot outside the stadium.", DOMAIN, "500"),
    ("medal table", "各国・地域が獲得した金・銀・銅メダルの数を集計し、順位付けして示す一覧表。", "名詞", "The host nation topped the medal table with the highest number of gold medals.", DOMAIN, "550"),
    ("medal ceremony", "競技終了後、上位入賞者にメダルを授与し、優勝国の国歌が演奏される式典。", "名詞", "Tears filled her eyes during the medal ceremony as her national anthem played.", DOMAIN, "550"),
    ("gold medalist", "ある種目で優勝し、金メダルを獲得した選手。", "名詞", "The reigning gold medalist returned to defend her title at the next Games.", DOMAIN, "500"),
    ("world record", "特定の種目において、これまでに人類が達成した中で最も優れた公式記録。", "名詞", "She broke the world record by nearly a full second in the final.", DOMAIN, "550"),
    ("host city", "大会の開催地として正式に選ばれた都市。", "名詞", "Paris was selected as the host city for the 2024 Summer Games.", DOMAIN, "550"),
    ("host city contract", "IOCと開催都市・開催国のオリンピック委員会などが締結する、大会開催に関する権利義務を定めた正式契約。", "名詞", "The host city contract outlines the financial and organizational responsibilities of the local organizing committee.", DOMAIN, "750"),
    ("International Olympic Committee", "オリンピック競技大会の開催地選定や運営統括を担う国際組織(略称IOC)。スイスのローザンヌに本部を置く。", "名詞", "The International Olympic Committee decides which sports will be added to future Games.", DOMAIN, "700"),
    ("International Paralympic Committee", "パラリンピック競技大会の運営統括を担う国際組織(略称IPC)。障がいのある選手のクラス分けなど競技規則の管理も行う。", "名詞", "The International Paralympic Committee sets the classification rules used across all para sports.", DOMAIN, "700"),
    ("World Anti-Doping Agency", "スポーツにおけるドーピングの防止・取り締まりを世界的に統括する機関(略称WADA)。禁止物質リストの策定などを行う。", "名詞", "Athletes are tested under rules established by the World Anti-Doping Agency.", DOMAIN, "750"),
    ("doping control", "禁止薬物の使用を防ぐため、大会前後に選手の尿や血液を検査する一連の手続き。", "名詞", "Every medalist must undergo doping control immediately after the competition.", DOMAIN, "650"),
    ("anti-doping", "禁止薬物の使用を防止・摘発することに関わる、あるいはそれを目的とする。", "形容詞", "The organization runs an extensive anti-doping education program for young athletes.", DOMAIN, "650"),
    ("Olympic Charter", "オリンピック運動の基本原則・IOCやNOCの役割・大会運営規則などを定めた基本文書。", "名詞", "According to the Olympic Charter, no political demonstration is permitted at Olympic sites.", DOMAIN, "800"),
    ("Olympic Truce", "古代ギリシャの慣習(エケケイリア)に由来し、大会期間中は戦争や紛争を一時停止するよう国連決議で呼びかけられる休戦の理念。", "名詞", "The United Nations calls for an Olympic Truce before every edition of the Games.", DOMAIN, "800"),
    ("Olympic motto", "「より速く、より高く、より強く」に、2021年から「ともに(Together)」が加えられた、大会の理念を表す標語。", "名詞", "The Olympic motto encourages athletes to constantly strive to improve themselves.", DOMAIN, "700"),
    ("Olympism", "スポーツを文化や教育と結びつけ、平和で人間の尊厳を尊重する社会の実現を目指す、オリンピック運動全体の理念。", "名詞", "Olympism is built on the idea that sport can promote peace and mutual understanding.", DOMAIN, "800"),
    ("athlete's oath", "開会式で選手代表が読み上げる、フェアプレー精神とルール遵守を誓う宣誓。", "名詞", "A veteran athlete recited the athlete's oath on behalf of every competitor at the Games.", DOMAIN, "700"),
    ("mixed-gender event", "男女の選手が同じチームを組んだり、同じ種目で共に競い合ったりする形式の種目。", "名詞", "The mixed-gender relay pairs two male and two female runners on the same team.", DOMAIN, "650"),
    ("Refugee Olympic Team", "特定の国を代表できない難民選手のために2016年リオ大会から編成されている、IOC旗の下で競技する特別チーム。", "名詞", "A member of the Refugee Olympic Team carried the Olympic flag into the stadium.", DOMAIN, "750"),
    ("chef de mission", "各国・地域の選手団を統括し、大会期間中の運営や生活面を取り仕切る代表責任者。", "名詞", "The chef de mission met with officials to resolve a scheduling conflict for the team.", DOMAIN, "800"),
    ("qualifying round", "本戦や決勝に進む選手・チームを絞り込むために行われる予選の試合や種目。", "名詞", "She barely advanced past the qualifying round before winning gold in the final.", DOMAIN, "550"),
    ("repechage", "予選や序盤の試合で敗れた選手に、決勝進出の可能性を残すために設けられる敗者復活戦。", "名詞", "He lost his first match but earned a bronze medal after winning through the repechage.", DOMAIN, "800"),
    ("Olympic rings", "五大陸の団結を象徴する、青・黄・黒・緑・赤の五つの輪から成るオリンピックの公式シンボル。", "名詞", "The five interlocking Olympic rings appeared on banners throughout the city.", DOMAIN, "500"),
    ("Olympic flame", "採火式でギリシャのオリンピアから採火され、聖火リレーを経て開会式の聖火台に灯される炎。", "名詞", "The Olympic flame burned continuously in the cauldron until the closing ceremony.", DOMAIN, "500"),
    ("national anthem", "表彰式で優勝した選手・チームの国を称えるために演奏される、その国の国歌。", "名詞", "The stadium fell silent as the national anthem of the gold medalist's country played.", DOMAIN, "500"),

    # --- パラリンピック固有語彙 ---
    ("Paralympic Games", "身体・視覚・知的障がいのある選手が参加する、オリンピックと同じ都市で直後に開催される国際総合競技大会。", "名詞", "The Paralympic Games take place in the same host city just weeks after the Olympics.", DOMAIN, "550"),
    ("Paralympic motto", "「Spirit in Motion(スピリット・イン・モーション)」という、2004年アテネ大会から採用されているパラリンピックの標語。", "名詞", "The Paralympic motto, Spirit in Motion, reflects the determination of every competing athlete.", DOMAIN, "750"),
    ("Agitos", "赤・青・緑の三本の曲線から成るパラリンピックの公式シンボル。ラテン語で「私は動く」を意味し、標語Spirit in Motionを象徴する。", "名詞", "The three Agitos swirl around a central point, symbolizing athletes in motion.", DOMAIN, "800"),
    ("sport class", "障がいの種類や程度に応じて選手を公平に競わせるために設けられる、種目ごとの区分。", "名詞", "Athletes are grouped into a sport class so that competitors have a similar level of impairment.", DOMAIN, "700"),
    ("classification code", "選手の障がいの種類・程度を示す、種目記号と数字を組み合わせたパラスポーツ独自の識別コード。数字が小さいほど障がいの程度が重いとされることが多い。", "名詞", "Her classification code, T11, indicates that she competes as a totally blind athlete in track events.", DOMAIN, "750"),
    ("boccia", "重度の脳性まひなど四肢に重い障がいのある選手を中心に行われる、目標球にどれだけ近づけて球を投げるかを競う球技。", "名詞", "Boccia requires incredible precision as players roll or throw balls toward a target ball.", DOMAIN, "650"),
    ("goalball", "視覚障がいのある選手が、鈴の入ったボールの音を頼りに相手ゴールへ転がし入れる、視覚障がい者スポーツ独自の球技。", "名詞", "Goalball players wear blindfolds and listen carefully for the bell inside the ball.", DOMAIN, "650"),
    ("sitting volleyball", "床に臀部をつけた姿勢で行う、立位で行うバレーボールを障がいのある選手向けに改良した競技。", "名詞", "Sitting volleyball is played on a smaller court with a lower net than standard volleyball.", DOMAIN, "650"),
    ("wheelchair basketball", "競技用車いすに乗った選手が行う、通常のバスケットボールとほぼ同じルールで行われる競技。", "名詞", "Wheelchair basketball players must master handling both the ball and their chair at the same time.", DOMAIN, "600"),
    ("wheelchair rugby", "四肢に障がいのある選手が競技用車いすを激しくぶつけ合いながらボールを運ぶ、コンタクトの強い球技。", "名詞", "Wheelchair rugby is known for its intense chair-to-chair collisions.", DOMAIN, "650"),
    ("wheelchair tennis", "競技用車いすに乗って行うテニス。ボールが2バウンドするまでの返球が認められている点が通常のテニスと異なる。", "名詞", "In wheelchair tennis, a player is allowed to return the ball after it bounces twice.", DOMAIN, "600"),
    ("wheelchair fencing", "車いすを固定した状態で行うフェンシング。上半身の動きと剣さばきだけで攻防を競う。", "名詞", "In wheelchair fencing, both competitors' chairs are locked to a frame so only their upper bodies move.", DOMAIN, "700"),
    ("wheelchair curling", "ストーンを投げる際の助走や滑走を行わず、車いすに座ったまま専用の器具でストーンを送り出す形式のカーリング。", "名詞", "Wheelchair curling does not allow sweeping, so precise delivery of the stone is essential.", DOMAIN, "700"),
    ("para ice hockey", "座ったまま滑走できる専用のそりに乗り、両手に持った短いスティックで氷上を進みながら行うアイスホッケー。", "名詞", "Para ice hockey players propel themselves across the ice using two short sticks.", DOMAIN, "700"),
    ("para-alpine skiing", "視覚・知的・肢体に障がいのある選手が、それぞれの障がいに応じた用具やクラスで滑走タイムを競うアルペンスキー競技。", "名詞", "In para-alpine skiing, visually impaired competitors race down the course with a guide skiing just ahead of them.", DOMAIN, "700"),
    ("para-nordic skiing", "クロスカントリースキーとバイアスロンを含む、障がいのある選手向けのノルディックスキー競技の総称。", "名詞", "Para-nordic skiing includes both cross-country races and biathlon events adapted for athletes with disabilities.", DOMAIN, "750"),
    ("para-snowboard", "義足や下肢の障がいがある選手などが出場する、スノーボードクロスなどの種目から成るパラリンピックの雪上競技。", "名詞", "Para-snowboard athletes race head-to-head down a course full of jumps and turns.", DOMAIN, "700"),
    ("para-athletics", "陸上競技を障がいのある選手向けに調整した種目の総称。義足を使った走り幅跳びや、投てき種目用の固定椅子なども用いられる。", "名詞", "Para-athletics events range from wheelchair racing to seated throwing competitions.", DOMAIN, "650"),
    ("para-swimming", "視覚・知的・肢体に障がいのある選手が、それぞれの障がいの程度に応じたクラスで競う水泳競技。", "名詞", "Because she cannot see the wall approaching, a coach taps her with a pole during para-swimming races.", DOMAIN, "650"),
    ("para-cycling", "手だけでこぐハンドサイクルやタンデム自転車など、様々な専用機材を用いて行われる障がい者向け自転車競技。", "名詞", "Para-cycling includes events on standard bicycles, tricycles, and hand-powered cycles.", DOMAIN, "650"),
    ("para-equestrian", "視覚・肢体などに障がいのある選手が馬を操って演技する馬場馬術競技。障がいの程度に応じたクラス分けが行われる。", "名詞", "Para-equestrian riders are judged on the precision and grace of their horse's movements.", DOMAIN, "700"),
    ("para-table tennis", "座位や立位など、選手の障がいの種類・程度に応じたクラスに分かれて行う卓球競技。", "名詞", "Para-table tennis includes both seated classes for wheelchair users and standing classes.", DOMAIN, "650"),
    ("para-taekwondo", "視覚や上肢に障がいのある選手が出場する、キョルギ(組手)形式のテコンドー競技。", "名詞", "Para-taekwondo made its Paralympic debut at the Tokyo 2020 Games.", DOMAIN, "700"),
    ("para-triathlon", "水泳・自転車・長距離走を組み合わせた競技を、義足や競技用車いすなど選手の障がいに応じた用具で行うパラトライアスロン。", "名詞", "In para-triathlon, some athletes switch from a handcycle to a racing wheelchair between the cycling and running legs.", DOMAIN, "700"),
    ("para-badminton", "車いすクラスや立位クラスなど、障がいの種類・程度に応じたクラスで争われるバドミントン競技。", "名詞", "Para-badminton was added to the Paralympic program for the first time at Tokyo 2020.", DOMAIN, "650"),
    ("para-canoe", "下肢などに障がいのある選手が、専用のシートやパドルを使ってタイムを競うカヌー・スプリント競技。", "名詞", "Para-canoe athletes are strapped into a stabilized seat before racing down the sprint course.", DOMAIN, "700"),
    ("para-archery", "車いす使用者や上肢に障がいのある選手も出場できるよう、用具の調整やクラス分けが行われるアーチェリー競技。", "名詞", "Some para-archery competitors release the bowstring with their mouth or foot instead of their hand.", DOMAIN, "650"),
    ("guide runner", "視覚障がいのある陸上競技の選手と一本のテザー(ひも)でつながり、並走してコースを導くパートナー。", "名詞", "The guide runner and the visually impaired sprinter crossed the finish line together, hand in hand.", DOMAIN, "700"),
    ("running blade", "下肢を切断した選手が短距離走などで使用する、板ばね状のカーボン製義足。", "名詞", "Her carbon-fiber running blade stores and releases energy with every stride.", DOMAIN, "700"),
    ("handcycle", "手でクランクを回して進む、下肢に障がいのある選手が使用する自転車。", "名詞", "He leaned low over his handcycle to reduce wind resistance on the final climb.", DOMAIN, "700"),
    ("tandem cycling", "視覚障がいのある選手が後部座席に乗り、晴眼者のパイロットが前部座席で操縦・こぎながら二人で走る自転車競技。", "名詞", "In tandem cycling, the visually impaired athlete and the sighted pilot must pedal in perfect sync.", DOMAIN, "650"),
    ("racing wheelchair", "3つの車輪と長く傾斜したハンドリムを備えた、陸上競技のトラック種目やロードレース用に設計された軽量の競技用車いす。", "名詞", "She switched from her everyday wheelchair to a racing wheelchair built specifically for speed.", DOMAIN, "650"),
    ("throwing frame", "投てき種目で、体幹を保持できない選手が座ったまま安定して投げられるように固定する専用の椅子・フレーム。", "名詞", "The javelin thrower strapped himself into a throwing frame before his final attempt.", DOMAIN, "750"),

    # --- 夏季種目・種目名 ---
    ("sport climbing", "スピード・ボルダリング・リードという異なる要素を組み合わせて争う、2020年東京大会から正式種目となったクライミング競技。", "名詞", "Sport climbing made its Olympic debut at the Tokyo 2020 Games.", DOMAIN, "600"),
    ("artistic swimming", "音楽に合わせて水中で演技を行う採点競技。2017年に国際水泳連盟が「シンクロナイズドスイミング」から名称を変更した。", "名詞", "Artistic swimming combines strength, flexibility, and split-second timing underwater.", DOMAIN, "600"),
    ("rhythmic gymnastics", "リボンやボールなどの手具を用いて音楽に合わせた演技を行う、採点制の体操競技。", "名詞", "The rhythmic gymnastics routine incorporated a ribbon that seemed to float through the air.", DOMAIN, "600"),
    ("artistic gymnastics", "跳馬・鉄棒・平均台など複数の種目で演技の技術と芸術性を競う、いわゆる「体操競技」。", "名詞", "Artistic gymnastics events include the vault, uneven bars, balance beam, and floor exercise.", DOMAIN, "600"),
    ("trampoline", "跳躍しながら宙返りなどの技を連続して行い、高さと技の難度・完成度を採点する体操競技。", "名詞", "The trampoline gymnast performed a series of twisting somersaults high above the frame.", DOMAIN, "550"),
    ("3x3 basketball", "3人対3人で行う、通常より小さいコートと短い試合時間で争われるバスケットボール競技。2020年東京大会から正式種目。", "名詞", "3x3 basketball games are fast-paced and typically last only ten minutes.", DOMAIN, "600"),
    ("breaking", "ヒップホップ文化から生まれたダンス(ブレイクダンス)を競技化したもので、2024年パリ大会で新種目として初めて採用された。", "名詞", "Breaking made its first appearance on the Olympic program at the Paris 2024 Games.", DOMAIN, "600"),
    ("modern pentathlon", "フェンシング・水泳・馬術・射撃と走行を組み合わせたレーザーランの5種目を1日で行う複合競技。", "名詞", "Modern pentathlon was created to test the skills a 19th-century cavalry officer might need.", DOMAIN, "700"),
    ("canoe slalom", "流れの速い人工の急流コースに設置されたゲートを、決められた順序で通過しながらタイムを競うカヌー競技。", "名詞", "The paddler navigated a dozen gates on the whitewater course during the canoe slalom final.", DOMAIN, "650"),
    ("canoe sprint", "静水の直線コースで着順やタイムを競う、カヌーとカヤックによる競漕競技。", "名詞", "Canoe sprint races are held on a calm, straight course over set distances such as 200 or 500 meters.", DOMAIN, "650"),
    ("synchronized diving", "2人の選手が同じ演技をタイミングを揃えて行い、技の完成度と同調性を採点する飛び込み競技。", "名詞", "The pair's synchronized diving routine impressed the judges with its perfect timing.", DOMAIN, "650"),
    ("beach volleyball", "屋外の砂浜コートで2人1組のチーム同士が行うバレーボール競技。", "名詞", "Beach volleyball is played barefoot on sand courts, usually two against two.", DOMAIN, "550"),
    ("judo", "相手を投げたり抑え込んだりして技の効果を競う、日本発祥の格闘技・オリンピック競技。", "名詞", "Judo has been part of the Olympic program for men since 1964 and for women since 1988.", DOMAIN, "500"),
    ("karate", "突き・蹴りの正確さや威力を競う組手と、一連の型の技術を競う形から成る、沖縄・日本発祥の武道。", "名詞", "Karate appeared on the Olympic program only once so far, at the Tokyo 2020 Games.", DOMAIN, "500"),
    ("taekwondo", "主に足技を使った打撃を得点源とする、韓国発祥の格闘技・オリンピック競技。", "名詞", "Taekwondo scoring focuses heavily on kicks landed to the body and head.", DOMAIN, "550"),
    ("wrestling", "相手を組み倒したり抑え込んだりして得点を競う、フリースタイルとグレコローマンの2形式があるオリンピック格闘技。", "名詞", "Wrestling has been part of the modern Olympics since the first Games in 1896.", DOMAIN, "500"),
    ("Greco-Roman wrestling", "腰から下への攻撃や足を使った技を禁止し、上半身の力だけで相手を投げたり抑え込んだりする形式のレスリング。", "名詞", "Greco-Roman wrestling forbids holding an opponent below the waist.", DOMAIN, "700"),
    ("fencing", "フルーレ・エペ・サーブルの3種目があり、剣で相手の有効面を突いたり切ったりして得点を競う競技。", "名詞", "Fencing bouts are scored electronically the instant a valid touch is registered.", DOMAIN, "550"),
    ("shooting", "ピストルやライフル、散弾銃を用いて標的の中心にどれだけ近く命中させられるかを競う射撃競技。", "名詞", "Olympic shooting events include both pistol and rifle competitions at various distances.", DOMAIN, "500"),
    ("weightlifting", "スナッチとクリーン&ジャークの2種目でどれだけ重いバーベルを頭上に持ち上げられるかを競う競技。", "名詞", "Weightlifting competitors get three attempts each in the snatch and the clean and jerk.", DOMAIN, "550"),
    ("rowing", "1人から8人までの漕手がボートに乗り、オールを漕いでタイムを競う競技。", "名詞", "Rowing crews must move in perfect unison to keep the boat gliding smoothly.", DOMAIN, "500"),
    ("sailing", "風を利用してヨットを操り、決められたコースを最も早く周回することを競う競技。", "名詞", "Sailing competitors must constantly read the wind and adjust their course.", DOMAIN, "500"),
    ("field hockey", "曲がったスティックでボールを操り、相手ゴールに入れて得点を競う球技。", "名詞", "Field hockey is played on artificial turf with a small, hard ball.", DOMAIN, "550"),
    ("decathlon", "2日間で10種目の陸上競技を行い、それぞれの記録を得点に換算して合計点で競う男子の複合競技。", "名詞", "The decathlon is often called the ultimate test of an athlete's all-around ability.", DOMAIN, "650"),
    ("heptathlon", "2日間で7種目の陸上競技を行い、それぞれの記録を得点に換算して合計点で競う女子の複合競技。", "名詞", "She set a personal best in the long jump on her way to winning the heptathlon.", DOMAIN, "650"),
    ("archery", "一定の距離から的を狙って矢を放ち、命中した位置の得点を競う競技。", "名詞", "Archery competitors must control their breathing to keep the bow perfectly steady.", DOMAIN, "500"),
    ("boxing", "リング上で相手と拳を交え、有効打の数やノックアウトによって勝敗を決める格闘競技。", "名詞", "Olympic boxing matches are shorter than professional bouts, usually lasting three rounds.", DOMAIN, "500"),
    ("baseball", "9人制のチームで打撃・投球・守備を行う球技。2020年東京大会で復帰したが2024年パリ大会では実施されず、2028年ロサンゼルス大会で再び正式種目となる予定とされる。", "名詞", "Baseball returned to the Olympics at Tokyo 2020 after a 12-year absence.", DOMAIN, "500"),
    ("softball", "野球と似たルールで、より大きなボールを下手投げで投げる球技。近年はオリンピックで野球と同時に実施・除外が繰り返されている。", "名詞", "Softball, like baseball, was dropped from the Paris 2024 program but is expected to return for Los Angeles 2028.", DOMAIN, "500"),
    ("diving", "飛び込み台や飛び板から飛び込み、空中での技の難度と完成度を採点する競技。", "名詞", "Diving judges score both the difficulty of the dive and the cleanness of the entry into the water.", DOMAIN, "500"),
    ("cycling", "トラック・ロード・マウンテンバイク・BMXなど、複数の種目に分かれる自転車競技の総称。", "名詞", "Olympic cycling is divided into track, road, mountain bike, and BMX disciplines.", DOMAIN, "500"),

    # --- 冬季種目・種目名 ---
    ("ice hockey", "6人制のチームがスケートで滑りながらパックをスティックで操り、相手ゴールに入れて得点を競う競技。", "名詞", "Ice hockey games at the Winter Olympics are played on a rink slightly larger than the NHL standard.", DOMAIN, "500"),
    ("curling", "氷上でストーンを滑らせて的の中心に近づけることを競い、ブラシで氷面をこすって軌道を調整する競技。", "名詞", "Teammates sweep the ice furiously to guide the curling stone toward the target.", DOMAIN, "550"),
    ("mixed doubles curling", "男女1人ずつの2人1組で行う、通常のカーリングより少ない石数で行われる種目。2018年平昌大会から正式種目となった。", "名詞", "Mixed doubles curling was added to the Winter Olympic program at PyeongChang 2018.", DOMAIN, "700"),
    ("nordic combined", "ジャンプの飛距離と得点をクロスカントリースキーのタイムに反映させて総合順位を決める複合競技。", "名詞", "In Nordic combined, the ski jump results determine each skier's starting time gap in the cross-country race.", DOMAIN, "750"),
    ("ski jumping", "助走路を滑り降りた勢いで空中に飛び出し、その飛距離と姿勢の美しさを採点するウィンタースポーツ。", "名詞", "Ski jumping combines the thrill of flight with the precision of a landing judged for style.", DOMAIN, "650"),
    ("short track speed skating", "狭い楕円形のリンクで複数の選手が同時に滑走し、着順を競う接触の多いスピードスケート競技。", "名詞", "Short track speed skating is notorious for dramatic crashes as skaters jostle for position on the tight turns.", DOMAIN, "650"),
    ("moguls", "こぶ状に整備された急斜面を滑り降りながら、ターンの技術と2回のジャンプの完成度を採点するフリースタイルスキー種目。", "名詞", "The skier launched into a twisting jump halfway down the moguls course.", DOMAIN, "650"),
    ("aerials", "ジャンプ台から高く飛び上がり、宙返りやひねりを組み合わせた技の難度と着地を採点するフリースタイルスキー種目。", "名詞", "Aerials competitors can flip and twist several times before landing on the steep slope below.", DOMAIN, "700"),
    ("slopestyle", "ジャンプやレールなどの障害物が連続するコースを滑り降り、技の難度や独創性を採点するスキー・スノーボード種目。", "名詞", "Slopestyle riders link tricks over a series of rails and jumps down the course.", DOMAIN, "650"),
    ("big air", "巨大な単独のジャンプ台から飛び出し、1回の跳躍の高さと技の完成度を採点するスキー・スノーボード種目。", "名詞", "The snowboarder landed a difficult triple flip to win the big air final.", DOMAIN, "650"),
    ("snowboard cross", "複数の選手が同時にコースを滑り降り、障害物をよけながら着順を競うスノーボード種目。", "名詞", "Snowboard cross riders often collide as they battle for position through the course's banked turns.", DOMAIN, "650"),
    ("ski cross", "複数の選手が同時にコースを滑り降り、ジャンプやバンクを越えながら着順を競うフリースタイルスキー種目。", "名詞", "Ski cross combines the speed of alpine skiing with the head-to-head racing of motocross.", DOMAIN, "650"),
    ("monobob", "1人乗りで行うボブスレー種目で、2022年北京大会から女子種目として正式に採用された。", "名詞", "Monobob made its Olympic debut as a women's event at the Beijing 2022 Games.", DOMAIN, "750"),
    ("ski mountaineering", "山岳地帯を登り(クライミングスキンを貼った板で登行し)、滑り降りることを繰り返してタイムを競う競技。2026年ミラノ・コルティナ大会から冬季オリンピックの新種目として採用されたとされる。", "名詞", "Ski mountaineering requires athletes to switch quickly between climbing gear and downhill skis.", DOMAIN, "800"),
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
