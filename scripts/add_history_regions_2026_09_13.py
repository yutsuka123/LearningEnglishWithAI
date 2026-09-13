# ruff: noqa: E501
"""歴史語彙(地域別)拡充バッチ(2026-09-13・authored by Claude, 8並列サブエージェントで分担執筆・
本エージェントがマージ/重複チェック/最終書き込みを実施)。
対象ドメイン: 中国史・米国史・世界史(近代)・英国史・日本史・世界史(古代)・世界史(中世)・
ローマ史(古代・帝国)。前セッションで下書きした約144語がスクラッチパッドのみに保存され
セッション間で失われた事故の再実施(教訓: 必ずリポジトリ配下の実ファイルに保存すること)。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_history_regions_2026_09_13.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ('Taiping Rebellion', '19世紀半ば(1850年代〜60年代)に洪秀全がキリスト教的な信仰を掲げて清朝に対して起こした大規模な反乱で、江南地方を中心に長期化し、犠牲者数は推定で数千万人規模にのぼるとされる、近代中国最大級の内乱。', '名詞', 'The Taiping Rebellion devastated much of southern China before Qing forces finally crushed it in 1864.', '中国史', '750'),
    ('Great Leap Forward', '1958年から毛沢東の指導のもとで進められた、農業の急速な集団化と工業生産の飛躍的拡大を目指した経済政策で、非現実的な生産目標や誤った農業政策などが原因となって深刻な飢饉を招き、推定で数千万人規模の死者を出したとされる。', '名詞', 'The Great Leap Forward aimed to rapidly transform China into an industrial power but instead led to widespread famine.', '中国史', '750'),
    ('Second Opium War', '1856年から1860年にかけて、イギリス・フランス連合軍が清朝と戦った戦争で、アロー号事件をきっかけに始まり、清朝はさらなる開港や外国公使の北京駐在などを認める北京条約の締結を強いられた。', '名詞', 'The Second Opium War ended with the Qing government agreeing to open more ports and allow foreign embassies in Beijing.', '中国史', '700'),
    ('Long March', '1934年から1936年にかけて、国民党軍の包囲攻撃を逃れるため、毛沢東率いる中国共産党の紅軍が中国南部から北西部の陝西省まで、約1年をかけて踏破した長距離の戦略的撤退・移動のこと。', '名詞', 'During the Long March, the Communist forces trekked thousands of miles across difficult terrain to escape Nationalist troops.', '中国史', '700'),
    ('Xinhai Revolution', '1911年から1912年にかけて起こった革命で、清朝を打倒して2000年以上続いた中国の帝政を終わらせ、アジア初の共和国である中華民国の成立につながった。', '名詞', 'The Xinhai Revolution overthrew the Qing dynasty and led to the establishment of the Republic of China.', '中国史', '750'),
    ("Hundred Days' Reform", '1898年に光緒帝が康有為らの提言を受けて実施した、政治・教育・軍事制度などの急進的な近代化改革運動で、わずか約100日間で保守派によるクーデター(戊戌の政変)によって挫折した。', '名詞', "The Hundred Days' Reform introduced sweeping modernization measures before conservative officials abruptly ended it.", '中国史', '800'),
    ('May Fourth Movement', '1919年5月4日、パリ講和会議で山東半島の権益がドイツから日本へ引き継がれることに反発した北京の学生を中心に起こった抗議運動で、反帝国主義・反封建の思想運動として中国の近代化に大きな影響を与えた。', '名詞', 'The May Fourth Movement began as student protests in Beijing and grew into a broader cultural and political movement.', '中国史', '750'),
    ('Treaty of Nanking', '1842年、第一次アヘン戦争の終結にあたってイギリスと清朝の間で結ばれた条約で、香港島の割譲、上海など5港の開港、多額の賠償金の支払いなどを清朝に義務づけた、近代中国最初の不平等条約とされる。', '名詞', 'Under the Treaty of Nanking, China ceded Hong Kong to Britain and opened five ports to foreign trade.', '中国史', '700'),
    ("Zheng He's voyages", '15世紀初頭、明の永楽帝の命を受けた宦官の武将・鄭和が率いた、大艦隊による東南アジアからインド洋、アフリカ東岸にまで及ぶ一連の大規模な航海のこと。', '名詞', "Zheng He's voyages brought Chinese fleets as far as the coast of East Africa decades before the European Age of Exploration.", '中国史', '750'),
    ('Battle of Yamen', '1279年、広東省沖の崖山で行われた、南宋の残存勢力とモンゴル帝国(元)の艦隊との最終決戦で、南宋側が壊滅し、これによって宋王朝は完全に滅亡した。', '名詞', 'The Battle of Yamen marked the final defeat of the Song dynasty at the hands of the Mongol fleet.', '中国史', '800'),
    ('Manchu conquest of China', '17世紀半ば、満洲族が建てた清が、内乱で弱体化した明を滅ぼし、南方の抵抗勢力も制圧して中国全土を支配下に置いていった、数十年にわたる一連の征服の過程。', '名詞', 'The Manchu conquest of China culminated in the establishment of the Qing dynasty, which would rule until 1912.', '中国史', '800'),
    ('Tang dynasty', '618年から907年まで中国を支配した王朝で、都の長安は当時世界最大級の国際都市として栄え、シルクロードを通じた交易や仏教文化、詩の隆盛などにより、中国史上最も繁栄した時代の一つとされる。', '名詞', 'The Tang dynasty is often regarded as a golden age of Chinese poetry, art, and international trade.', '中国史', '650'),
    ('Song dynasty', '960年から1279年まで中国を支配した王朝で、火薬・羅針盤・活版印刷などの技術革新や科挙制度の整備、商業・都市文化の発展が進んだ一方、軍事的には北方民族の圧迫に苦しみ、南方への遷都を余儀なくされた。', '名詞', 'The Song dynasty saw remarkable advances in technology and commerce, even as it faced constant military pressure from northern rivals.', '中国史', '650'),
    ('Yuan dynasty', '1271年にモンゴル帝国のフビライ・ハンが中国に建てた王朝で、南宋を滅ぼして中国全土を統一した、モンゴル人による初めての中国支配王朝。', '名詞', 'The Yuan dynasty was established by Kublai Khan and marked the first time all of China was ruled by a Mongol emperor.', '中国史', '650'),
    ('Ming dynasty', '1368年から1644年まで中国を支配した王朝で、モンゴル人の元を北方へ追いやった漢民族による王朝であり、紫禁城の建設や鄭和の大航海、万里の長城の大規模な改修などで知られる。', '名詞', 'The Ming dynasty built much of the Great Wall as it stands today and constructed the Forbidden City in Beijing.', '中国史', '650'),
    ('Grand Canal', '中国の南北を結ぶために建設された、世界最長級の人工水路で、隋の時代に大規模に整備され、江南の豊かな穀物を北方の都へ輸送する大動脈として長く重要な役割を果たした。', '名詞', 'The Grand Canal allowed grain from the fertile south to be shipped efficiently to the capital in the north.', '中国史', '700'),
    ('Warring States period', '紀元前5世紀頃から紀元前221年の秦による中国統一まで続いた、複数の有力諸侯国が覇権を争って絶え間なく戦争を繰り広げた分裂・動乱の時代。', '名詞', 'The Warring States period ended when the state of Qin conquered its rivals and unified China in 221 BCE.', '中国史', '700'),
    ('Self-Strengthening Movement', '19世紀後半、アヘン戦争などでの敗北を受け、清朝の官僚たちが西洋の軍事技術や工業技術を取り入れることで国力の立て直しを図った、一連の近代化運動。', '名詞', "The Self-Strengthening Movement attempted to modernize China's military and industry while preserving traditional political institutions.", '中国史', '800'),
    ('Articles of Confederation', '1789年に合衆国憲法が発効するまでの間、独立を宣言した13州の連合体を統治するために用いられていた最初の統治文書で、中央政府の権限があまりに弱かったため、より強い権限を持つ合衆国憲法に置き換えられた。', '名詞', 'The Articles of Confederation left the central government too weak to tax or regulate trade effectively.', '米国史', '750'),
    ('Bill of Rights', '1791年に批准された、合衆国憲法の最初の10か条の修正条項の総称。言論・信教の自由や適正手続きの保障など、国民の基本的な権利や自由を明文化したもの。', '名詞', 'The First Amendment, part of the Bill of Rights, protects freedom of speech and religion.', '米国史', '700'),
    ('Louisiana Purchase', '1803年、アメリカ合衆国がフランスからミシシッピ川流域を中心とする広大な西部の領土を買い取った取引。これによって合衆国の国土はほぼ倍増したとされる。', '名詞', 'The Louisiana Purchase roughly doubled the size of the young United States almost overnight.', '米国史', '700'),
    ('Trail of Tears', '1830年代、連邦政府の強制移住政策によって、チェロキー族をはじめとする複数の先住民族が東部の故地から西方のインディアン準州へと移送された過酷な道のりを指す語。移動中の劣悪な環境により多くの死者が出たとされる。', '名詞', 'Thousands of Cherokee people are believed to have died along the Trail of Tears from cold, disease, and exhaustion.', '米国史', '800'),
    ('American Civil War', '1861年から1865年にかけて、奴隷制の存続や州権を巡る対立から、アメリカ合衆国北部と、連邦から離脱した南部諸州(南部連合)との間で戦われた内戦。', '名詞', 'Slavery was the central issue that divided the North and South in the American Civil War.', '米国史', '750'),
    ('Mexican-American War', '1846年から1848年にかけて、テキサス併合や国境を巡る対立からアメリカ合衆国とメキシコの間で戦われた戦争。この戦争の結果、メキシコは現在のカリフォルニアやニューメキシコなどを含む広大な領土をアメリカに割譲した。', '名詞', 'The United States gained a huge stretch of territory in the Southwest after winning the Mexican-American War.', '米国史', '800'),
    ('Missouri Compromise', '1820年、奴隷州と自由州の数の均衡を保つため、ミズーリ州を奴隷州として、メインを自由州として連邦に加盟させるとともに、それより北の新たな准州では奴隷制を禁止すると定めた連邦議会の妥協案。', '名詞', 'The Missouri Compromise tried to balance the number of slave states and free states admitted to the Union.', '米国史', '800'),
    ('Compromise of 1850', '米墨戦争後に獲得した領土での奴隷制の扱いを巡る北部と南部の対立を一時的に鎮めるため、カリフォルニアを自由州として連邦に加盟させる一方で逃亡奴隷法を強化するなど、複数の法案を組み合わせて成立させた連邦議会の妥協案。', '名詞', 'The Compromise of 1850 admitted California as a free state while toughening the law on returning escaped slaves.', '米国史', '800'),
    ('Gettysburg Address', '南北戦争中の1863年、ゲティスバーグの戦いの戦没者墓地の献納式でリンカン大統領が行った演説。短いながらも民主主義の理念を格調高く語ったことで知られる。', '名詞', 'In the Gettysburg Address, Lincoln famously described a government of the people, by the people, and for the people.', '米国史', '750'),
    ('Gilded Age', '南北戦争後の1870年代から1900年頃にかけて、急速な工業化とともに一部の実業家が巨万の富を築く一方、労働環境の悪化や政治の腐敗も目立った、アメリカの経済発展の時代を指す語。表面の華やかさの裏に問題を隠しているという皮肉を込めて名付けられた。', '名詞', 'Industrialists amassed enormous fortunes during the Gilded Age, even as many factory workers lived in poverty.', '米国史', '800'),
    ('Progressive Era', '1890年代から1920年頃にかけて、都市化や産業化がもたらした労働環境の悪化・独占企業の弊害・政治腐敗などの社会問題を是正しようと、様々な改革運動が展開されたアメリカの時代。', '名詞', 'Reformers of the Progressive Era pushed for laws to break up monopolies and improve factory safety.', '米国史', '800'),
    ('Great Depression', '1929年の株式市場大暴落をきっかけに始まり、1930年代を通じて世界中に広がった、アメリカ史上最も深刻とされる経済不況。多数の失業者や銀行の破綻を生んだ。', '名詞', 'Millions of Americans lost their jobs during the Great Depression that followed the 1929 stock market crash.', '米国史', '700'),
    ('Civil Rights Movement', '1950年代から1960年代にかけて、人種による差別や隔離の撤廃、法の下の平等な権利の獲得を目指してアフリカ系アメリカ人を中心に展開された社会運動。', '名詞', 'The Civil Rights Movement used marches, boycotts, and legal challenges to fight racial segregation.', '米国史', '700'),
    ('Voting Rights Act', '1965年に制定された連邦法。人種を理由に投票を妨げてきた識字テストなどの手段を禁止し、特に南部諸州における投票権の実質的な保障を強化した。', '名詞', 'The Voting Rights Act of 1965 outlawed literacy tests that had long been used to keep Black voters from the polls.', '米国史', '800'),
    ('Cuban Missile Crisis', '1962年、ソ連がキューバに核ミサイル基地を建設していることが発覚し、アメリカとソ連の間で核戦争寸前まで緊張が高まった冷戦期の危機。', '名詞', 'The Cuban Missile Crisis brought the United States and the Soviet Union to the brink of nuclear war.', '米国史', '750'),
    ('Vietnam War', '1950年代半ばから1975年まで続いた、共産主義勢力の北ベトナムと、アメリカが支援した南ベトナムとの間の戦争。アメリカ国内で大規模な反戦運動を引き起こしたことでも知られる。', '名詞', 'The Vietnam War sparked massive antiwar protests across American college campuses.', '米国史', '700'),
    ('19th Amendment', '1920年に批准された合衆国憲法修正第19条。性別を理由に投票権を否定することを禁じ、女性に参政権を認めた。', '名詞', 'The 19th Amendment finally guaranteed American women the right to vote.', '米国史', '800'),
    ('McCarthyism', '1950年代前半、上院議員ジョセフ・マッカーシーを中心に、政府や社会の中に共産主義者が潜んでいると主張し、十分な証拠のないまま個人を告発・攻撃した政治的風潮。', '名詞', 'During McCarthyism, many people lost their jobs simply on suspicion of having communist sympathies.', '米国史', '850'),
    ('French Revolution', '1789年に始まり、絶対王政やアンシャン・レジーム(旧体制)を打倒して、自由・平等・国民主権の理念を掲げた一連のフランスの政治革命。', '名詞', 'The French Revolution overthrew the monarchy and introduced the radical idea that sovereignty belonged to the people, not the king.', '世界史（近代）', '700'),
    ('Reign of Terror', 'フランス革命期の1793年から1794年にかけて、ロベスピエールらを中心とする革命政府が「反革命容疑者」とみなした人々を次々と処刑するなど、恐怖による統治を行った時期。', '名詞', 'During the Reign of Terror, thousands of people suspected of opposing the revolution were sent to the guillotine.', '世界史（近代）', '750'),
    ('Napoleonic Wars', '1803年頃から1815年にかけて、フランス皇帝ナポレオン・ボナパルトの下でフランスとその同盟国が、イギリスやロシアなど諸国と繰り返し戦った一連の大規模な戦争。', '名詞', 'The Napoleonic Wars reshaped the map of Europe and spread revolutionary ideas across the continent.', '世界史（近代）', '750'),
    ('Congress of Vienna', '1814年から1815年にかけてオーストリアのウィーンで開かれた国際会議。ナポレオン戦争後のヨーロッパの国境や勢力均衡を再編し、保守的な旧体制の秩序を回復しようとした。', '名詞', "The Congress of Vienna redrew the map of Europe in an attempt to restore a balance of power after Napoleon's defeat.", '世界史（近代）', '800'),
    ('Scramble for Africa', '19世紀後半から20世紀初頭にかけて、ヨーロッパ列強がアフリカ大陸のほぼ全域を急速に植民地として分割・支配した動き。', '名詞', 'During the Scramble for Africa, European powers divided almost the entire continent into colonies within just a few decades.', '世界史（近代）', '800'),
    ('trench warfare', '敵味方が地面に掘った塹壕にこもって対峙し、その間の狭い無人地帯(ノーマンズランド)を挟んで膠着した戦闘を続ける戦争の形態。第一次世界大戦の西部戦線で典型的に見られた。', '名詞', 'Trench warfare on the Western Front often reduced fighting to a bloody stalemate over just a few hundred meters of land.', '世界史（近代）', '750'),
    ('World War I', '1914年から1918年にかけて、主にヨーロッパを舞台に同盟国側と協商国(連合国)側に分かれて戦われた、それまでにない規模の総力戦。', '名詞', 'World War I began in 1914 after the assassination of Archduke Franz Ferdinand triggered a chain of alliances across Europe.', '世界史（近代）', '700'),
    ('Treaty of Versailles', '1919年、第一次世界大戦の戦後処理としてドイツと連合国の間で結ばれた講和条約。ドイツに巨額の賠償金や領土の割譲、軍備制限などの厳しい条件を課した。', '名詞', 'The Treaty of Versailles imposed heavy reparations on Germany, which many historians see as a factor behind later resentment in the country.', '世界史（近代）', '800'),
    ('Bolshevik Revolution', '1917年、レーニン率いるボリシェヴィキ(のちの共産党)が臨時政府を打倒し、世界初の社会主義国家であるソビエト政権を樹立した革命。十月革命とも呼ばれる。', '名詞', "The Bolshevik Revolution of 1917 toppled Russia's provisional government and brought Lenin's Communist party to power.", '世界史（近代）', '800'),
    ('League of Nations', '第一次世界大戦後の1920年に発足した、国際紛争を平和的に解決し戦争を防止することを目的とした史上初の世界的な国際機関。', '名詞', 'The League of Nations was created after World War I to prevent future conflicts through diplomacy and collective security.', '世界史（近代）', '750'),
    ('World War II', '1939年から1945年にかけて、枢軸国(ドイツ・イタリア・日本など)と連合国の間で世界規模で戦われた、人類史上最大の戦争。', '名詞', 'World War II began in Europe in 1939 when Germany invaded Poland, drawing Britain and France into the conflict.', '世界史（近代）', '700'),
    ('Holocaust', '第二次世界大戦中、ナチス・ドイツがユダヤ人をはじめとする人々を組織的に迫害し、強制収容所などで大量に殺害した出来事。犠牲者はユダヤ人だけで推定600万人ともされる。', '名詞', 'The Holocaust refers to the systematic murder of millions of Jews and other targeted groups by Nazi Germany during World War II.', '世界史（近代）', '800'),
    ('Yalta Conference', '1945年2月、第二次世界大戦の終結が見え始めた時期に、アメリカ・イギリス・ソ連の首脳がソ連領クリミア半島のヤルタで開き、戦後のヨーロッパの秩序や国際連合の設立などを話し合った会談。', '名詞', 'At the Yalta Conference, Roosevelt, Churchill, and Stalin discussed how postwar Europe would be divided among the Allied powers.', '世界史（近代）', '850'),
    ('Potsdam Conference', '1945年7月から8月、ドイツ降伏後の戦後処理を話し合うため、アメリカ・イギリス・ソ連の首脳がベルリン郊外のポツダムで開いた会談。日本への降伏要求(ポツダム宣言)もここで発表された。', '名詞', 'The Potsdam Conference addressed how defeated Germany would be occupied and administered by the Allied powers.', '世界史（近代）', '850'),
    ('Marshall Plan', '第二次世界大戦後の1948年から、アメリカが戦争で疲弊した西ヨーロッパ諸国の経済復興を支援するために行った大規模な援助計画。冷戦下でソ連の影響力拡大を防ぐ狙いもあったとされる。', '名詞', 'The Marshall Plan provided billions of dollars in American aid to help rebuild the economies of war-torn Western Europe.', '世界史（近代）', '800'),
    ('Truman Doctrine', '1947年、アメリカ大統領トルーマンが表明した外交方針。共産主義の勢力拡大に対抗するため、脅威にさらされた自由主義諸国を軍事的・経済的に支援することを掲げた。', '名詞', 'The Truman Doctrine committed the United States to supporting countries threatened by the spread of communism.', '世界史（近代）', '850'),
    ('Berlin Wall', '1961年、東ドイツが東西ベルリンの境界に築いた壁。東側からの人々の流出を防ぐ目的があり、冷戦下でのヨーロッパ分断を象徴する存在となった。1989年に崩壊した。', '名詞', 'The Berlin Wall divided the city for nearly three decades before it finally fell in 1989.', '世界史（近代）', '700'),
    ('Warsaw Pact', '1955年、ソ連と東欧の社会主義諸国が結成した軍事同盟。西側諸国の軍事同盟であるNATO(北大西洋条約機構)に対抗する目的で作られた。', '名詞', 'The Warsaw Pact was formed as a Soviet-led military alliance to counterbalance NATO in Cold War Europe.', '世界史（近代）', '800'),
    ('Space Race', '冷戦下でアメリカとソ連が国家の威信をかけて繰り広げた、人工衛星の打ち上げや有人宇宙飛行、月面着陸などをめぐる技術開発競争。', '名詞', 'The Space Race between the United States and the Soviet Union led to major milestones like the first satellite launch and the first Moon landing.', '世界史（近代）', '700'),
    ('Tudor dynasty', '1485年のボズワースの戦いでの勝利を経てヘンリー7世が王位に就いてから、1603年にエリザベス1世が没するまで続いた、テューダー家によるイングランドの王朝。', '名詞', 'The Tudor dynasty began when Henry VII defeated Richard III at the Battle of Bosworth Field in 1485.', '英国史', '650'),
    ('Elizabethan era', 'エリザベス1世が統治した1558年から1603年までの時代を指す語で、シェイクスピアの演劇作品やスペイン無敵艦隊の撃退など、文化と国力の両面でイングランドが大きく発展した時期として知られる。', '名詞', "Many of Shakespeare's most famous plays were written during the Elizabethan era.", '英国史', '650'),
    ('Petition of Right', '1628年に議会がチャールズ1世に提出し、国王の同意なしに課税したり、法に基づかずに人を逮捕・投獄したりすることを禁じるよう求めた文書で、後のイギリス憲政史における重要な先例となった。', '名詞', 'Parliament drafted the Petition of Right to stop the king from imprisoning subjects without trial.', '英国史', '800'),
    ('English Civil War', '17世紀のイングランドで、国王チャールズ1世を支持する王党派と、議会の権限強化を求める議会派との間で戦われた一連の内戦(1642年頃〜1651年頃)。最終的に国王が処刑され、一時的に共和政が樹立された。', '名詞', 'The English Civil War ended with the execution of King Charles I and the establishment of a republic.', '英国史', '700'),
    ('Restoration of 1660', '共和政の崩壊後、1660年にチャールズ2世が亡命先から呼び戻されてイングランド国王に復位し、王政が再び樹立された出来事。', '名詞', 'The Restoration of 1660 brought Charles II back to the throne after years of republican rule.', '英国史', '750'),
    ('English Bill of Rights', '1689年に議会が制定した法で、国王の権限を制限し、議会の同意なき課税や平時の常備軍維持を禁じるとともに、議会での言論の自由などを保障した、イングランドの立憲君主制の基礎となった文書。', '名詞', 'The English Bill of Rights of 1689 limited royal power and strengthened the authority of Parliament.', '英国史', '750'),
    ('Acts of Union 1707', '1707年にイングランド議会とスコットランド議会がそれぞれ可決し、両王国を統合してグレートブリテン王国を成立させた一連の法律。', '名詞', 'The Acts of Union 1707 merged the kingdoms of England and Scotland into a single Kingdom of Great Britain.', '英国史', '800'),
    ('British Empire', '16世紀末以降イングランド(後にイギリス)が世界各地に築いた植民地・自治領・保護領などから成る広大な勢力圏で、最盛期の20世紀初頭には地球上の陸地の4分の1近くを占めたとされる。', '名詞', 'At its height, the British Empire was often described as the empire on which the sun never set.', '英国史', '600'),
    ('enclosure movement', '中世以来共同で利用されてきた開放耕地や共有地を、地主が生垣や柵で区切って個人所有の農地へと転換していった、イギリスで長期間にわたり進行した動き。効率的な農業経営を可能にした一方で、多くの小農民が土地を追われる結果になったとされる。', '名詞', 'The enclosure movement gradually turned open common fields into fenced private farmland.', '英国史', '750'),
    ('Corn Laws', '19世紀前半のイギリスで、輸入穀物に高い関税を課すことで国内の地主・農業者を保護していた一連の法律。都市労働者のパン価格を押し上げるとして反対運動が起こり、1846年に廃止された。', '名詞', 'The Corn Laws kept grain prices high by restricting cheap imports, until they were repealed in 1846.', '英国史', '800'),
    ('Chartism', '1838年に発表された「人民憲章」を掲げ、成人男性普通選挙権や議員への歳費支給など議会改革を求めた、19世紀イギリスの労働者階級による政治運動。', '名詞', 'Chartism called for universal male suffrage and other democratic reforms to the British Parliament.', '英国史', '850'),
    ('Peterloo Massacre', '1819年、選挙権拡大などを求めてマンチェスターのセント・ピーターズ・フィールドに集まっていた群衆に騎兵隊が突入し、推定で十数人が死亡、数百人が負傷したとされる事件。政府への批判が高まる契機となった。', '名詞', 'The Peterloo Massacre shocked the public and helped fuel the movement for parliamentary reform.', '英国史', '850'),
    ('Victorian era', 'ヴィクトリア女王が在位した1837年から1901年までの時代を指す語で、産業や大英帝国の拡大が進む一方、厳格な社会規範や道徳観が特徴とされる。', '名詞', 'Many grand railway stations and civic buildings in Britain were constructed during the Victorian era.', '英国史', '600'),
    ('suffragette', '20世紀初頭のイギリスで、女性参政権の獲得を目指し、デモ行進や投獄も辞さない直接行動を伴う活動を行った女性運動家。特に婦人社会政治連盟(WSPU)に参加した人々を指すことが多い。', '名詞', "The suffragette chained herself to the railings outside Parliament to demand women's right to vote.", '英国史', '700'),
    ('Battle of Britain', '1940年、ドイツ空軍によるイギリス本土上陸作戦の前提となる制空権の獲得を狙った大規模な航空攻撃を、イギリス空軍が防ぎきった戦い。', '名詞', 'The Royal Air Force won the Battle of Britain by preventing the Luftwaffe from gaining control of the skies.', '英国史', '650'),
    ('the Blitz', '第二次世界大戦中の1940年から1941年にかけて、ドイツ軍がロンドンをはじめとするイギリスの諸都市に対して行った集中的な夜間空爆。', '名詞', 'Thousands of Londoners sheltered in underground stations every night during the Blitz.', '英国史', '650'),
    ('Suez Crisis', '1956年、エジプトのナセル大統領がスエズ運河の国有化を宣言したことをきっかけに、イギリス・フランス・イスラエルがエジプトに軍事介入した事件。国際的な批判とアメリカの圧力により撤退に追い込まれ、イギリスの国際的な影響力の後退を象徴する出来事とされる。', '名詞', "The Suez Crisis is often seen as marking the end of Britain's status as a leading world power.", '英国史', '800'),
    ('Irish Home Rule', '19世紀後半から20世紀初頭にかけて、アイルランドに連合王国内での自治(独自の議会)を認めるよう求めた政治運動、およびそれをめぐる一連の立法上の動き。複数回にわたり法案が議会に提出されたが、その成立や施行の経緯は複雑であったとされる。', '名詞', 'Irish Home Rule became one of the most contentious political issues in British politics for decades.', '英国史', '800'),
    ('Yamato period', '3世紀ごろから710年まで、奈良盆地を中心とする大和政権が日本列島の統一を進めたとされる時代区分。', '名詞', 'During the Yamato period, powerful clans in the Nara basin gradually extended their influence across much of the Japanese archipelago.', '日本史', '750'),
    ('Taika Reform', '645年に中大兄皇子や中臣鎌足らが蘇我氏を打倒した後、唐の律令制度にならって天皇中心の中央集権国家を目指して進めたとされる一連の政治改革。', '名詞', "The Taika Reform aimed to strip powerful clans of their private landholdings and place all land under the emperor's direct control.", '日本史', '800'),
    ('Nara period', '710年に都が平城京(現在の奈良)に置かれてから794年まで続いたとされる時代。仏教文化が栄え、『古事記』『日本書紀』が編まれた。', '名詞', 'The great bronze Buddha statue at Todai-ji was cast during the Nara period as a symbol of Buddhist protection for the state.', '日本史', '700'),
    ('Heian period', '794年に都が平安京(現在の京都)に移されてから1185年ごろまで続いたとされる時代。藤原氏による摂関政治のもと、貴族的な宮廷文化が花開いた。', '名詞', 'Lady Murasaki wrote The Tale of Genji during the Heian period, when court culture and refined aesthetics flourished in Kyoto.', '日本史', '700'),
    ('Kamakura shogunate', '1185年前後に源頼朝が鎌倉に開いたとされる、日本で最初の武家政権。地方に守護・地頭を置き、朝廷とは別に武士による統治機構を築いた。', '名詞', 'The Kamakura shogunate marked the beginning of nearly seven centuries of military rule by samurai in Japan.', '日本史', '800'),
    ('Genpei War', '1180年から1185年にかけて、平氏(平家)と源氏(源家)という二つの武士団の間で争われたとされる内乱。源氏の勝利により平氏は滅び、鎌倉幕府成立への道が開かれた。', '名詞', 'The Genpei War ended with a decisive naval battle at Dan-no-ura, where the Taira clan was finally defeated.', '日本史', '800'),
    ('Mongol invasions of Japan', '1274年と1281年の二度にわたり、元(モンゴル帝国)の軍勢が九州北部への上陸を試みたとされる出来事。御家人らの抵抗に加え、暴風雨(後に神風と呼ばれた)にも助けられて撃退されたとされる。', '名詞', "During the Mongol invasions of Japan, samurai defenders on Kyushu built stone walls along the coast to block the enemy's landing.", '日本史', '800'),
    ('Muromachi period', '1336年から1573年まで、京都の室町に本拠を置いた足利氏の政権のもとで続いたとされる時代。金閣寺・銀閣寺に代表される文化や、能・茶の湯などが発展した。', '名詞', 'Zen-influenced arts such as the tea ceremony and ink painting matured during the Muromachi period.', '日本史', '750'),
    ('Onin War', '1467年から1477年にかけて、将軍家や有力守護大名の家督争いをめぐって京都を主戦場に繰り広げられたとされる内乱。都は焼け野原となり、以後の戦国時代の幕開けを招いたとされる。', '名詞', 'The Onin War left much of Kyoto in ashes and weakened the central authority of the shogunate for generations.', '日本史', '850'),
    ('Ashikaga shogunate', '1336年に足利尊氏が開いたとされる、京都の室町を拠点としたことから室町幕府とも呼ばれる武家政権。15世紀後半以降は次第に統制力を失っていった。', '名詞', 'The Ashikaga shogunate gradually lost control over powerful regional lords in the century following the Onin War.', '日本史', '800'),
    ('Tokugawa Ieyasu', '1600年の関ヶ原の戦いで勝利を収め、1603年に征夷大将軍に任じられて江戸幕府を開いたとされる武将。以後260年余り続く徳川家による支配の基礎を築いた。', '名詞', 'Tokugawa Ieyasu unified the country after decades of civil war and established a shogunate that would rule Japan for over 260 years.', '日本史', '750'),
    ('Battle of Sekigahara', '1600年に美濃国(現在の岐阜県)で行われたとされる合戦。徳川家康率いる東軍が石田三成率いる西軍を破り、徳川氏による全国支配を決定づけた「天下分け目の戦い」とされる。', '名詞', 'The Battle of Sekigahara is often called the battle that decided who would rule Japan for the next two and a half centuries.', '日本史', '800'),
    ('sankin-kotai', '江戸幕府が諸大名に課したとされる制度で、大名は一定期間ごとに江戸と自らの領国を往復して滞在することを義務づけられた。妻子を人質のように江戸に住まわせることも含め、大名統制の手段とされた。', '名詞', 'Under the sankin-kotai system, daimyo were required to spend alternate years in Edo, which placed a heavy financial burden on their domains.', '日本史', '850'),
    ('sakoku', '江戸幕府がキリスト教の禁止や貿易統制を目的として、長崎の出島などごく限られた窓口を除き、外国との交流や渡航を厳しく制限したとされる対外政策。後の時代にこう呼ばれるようになった。', '名詞', 'Under sakoku, ordinary Japanese people were forbidden to travel abroad, and foreign trade was confined almost entirely to the port of Nagasaki.', '日本史', '800'),
    ('Bakumatsu', '1853年のペリー来航前後から1868年の明治維新に至るまでの、江戸幕府の統治が揺らいだとされる江戸時代末期を指す言葉。', '名詞', 'During the Bakumatsu era, political factions clashed violently over whether Japan should open to the West or expel foreigners by force.', '日本史', '750'),
    ('Black Ships', '1853年、アメリカのペリー提督が率いて浦賀沖に来航したとされる艦隊を指す通称。船体を黒く塗った蒸気船を含んでいたことに由来し、日本に開国を迫るきっかけとなった。', '名詞', 'The arrival of the Black Ships in 1853 shocked the shogunate and forced Japan to reconsider more than two centuries of seclusion.', '日本史', '700'),
    ('Treaty of Kanagawa', '1854年、再来航したペリーと江戸幕府との間で結ばれたとされる条約。下田と函館の開港を定め、長く続いた鎖国政策に事実上の終止符を打った。', '名詞', 'The Treaty of Kanagawa opened two Japanese ports to American ships and ended over two centuries of national seclusion.', '日本史', '800'),
    ('zaibatsu', '明治時代以降に形成されたとされる、三井・三菱・住友などに代表される、特定の一族が出資・経営を独占する大規模な財閥企業集団。', '名詞', 'Zaibatsu conglomerates like Mitsui and Mitsubishi came to dominate banking, shipping, and heavy industry in modern Japan.', '日本史', '800'),
    ('Babylon', '現在のイラク中部、ユーフラテス川流域に位置した古代メソポタミアの都市で、ハンムラビ王の時代やのちの新バビロニア王国(ネブカドネザル2世の時代)に特に繁栄し、伝説的な空中庭園の伝承でも知られる。', '名詞', 'Babylon rose to become one of the most powerful cities in the ancient Near East under King Hammurabi.', '世界史（古代）', '600'),
    ('Akkadian Empire', '紀元前24世紀頃、サルゴン王がメソポタミアの複数の都市国家を征服して築いたとされる、史上最初期の広域帝国の一つ。アッカド語を公用語として広め、後のメソポタミア諸帝国のモデルとなったとされる。', '名詞', "The Akkadian Empire, founded by Sargon of Akkad, is often regarded as one of the world's first empires.", '世界史（古代）', '800'),
    ('Assyrian Empire', '古代メソポタミア北部を拠点に興り、特に紀元前8〜7世紀頃に強力な軍事力で中東の広い範囲を支配した帝国。高度に組織化された軍隊や行政制度、大規模な図書館(ニネヴェの王立図書館など)でも知られる。', '名詞', 'At its height, the Assyrian Empire controlled territory stretching from Mesopotamia to Egypt.', '世界史（古代）', '750'),
    ('Achaemenid Empire', '紀元前6世紀にキュロス2世が建国した、古代ペルシアを中心とする史上最大級の帝国の一つ。多様な民族・文化を包摂する広大な領土を、サトラップ(総督)による州制度や整備された道路網で統治したことで知られる。', '名詞', 'The Achaemenid Empire stretched from the Indus Valley to parts of Greece at its greatest extent.', '世界史（古代）', '850'),
    ('satrap', '古代ペルシアのアケメネス朝において、皇帝に代わって各州(サトラピー)を統治した総督のこと。徴税や治安維持など広い権限を任されていた。', '名詞', 'Each satrap governed a province of the Achaemenid Empire on behalf of the Persian king.', '世界史（古代）', '800'),
    ('Cyrus the Great', '紀元前6世紀にアケメネス朝ペルシア帝国を建国した王。メディアやリュディア、新バビロニアを征服して大帝国を築き、比較的寛容な統治方針で知られる。', '名詞', 'Cyrus the Great is often remembered for allowing conquered peoples to keep their own customs and religions.', '世界史（古代）', '750'),
    ('Darius I', 'アケメネス朝ペルシアの王で、帝国の領土を最大に広げ、サトラップ制度や「王の道」と呼ばれる道路網の整備など統治機構を確立した人物とされる。ギリシアへの遠征(マラトンの戦いなど)でも知られる。', '名詞', 'Darius I reorganized the Achaemenid Empire into provinces, each governed by a satrap.', '世界史（古代）', '800'),
    ('Xerxes I', 'アケメネス朝ペルシアの王で、父ダレイオス1世の跡を継ぎ、紀元前480年頃に大軍を率いてギリシアへ遠征した(第二次ペルシア戦争)ことで知られる。サラミスの海戦での敗北などが伝えられている。', '名詞', 'Xerxes I led a massive Persian invasion of Greece that included the famous battle at Thermopylae.', '世界史（古代）', '800'),
    ('Sparta', '古代ギリシアの有力なポリス(都市国家)の一つ。厳格な軍事教育制度と強力な陸軍で知られ、ペロポネソス戦争でアテナイと覇権を争った。', '名詞', 'Sparta was famous throughout ancient Greece for the rigorous military training given to its citizens.', '世界史（古代）', '600'),
    ('Delian League', '紀元前5世紀、ペルシア戦争後にアテナイを中心として結成された古代ギリシアの都市国家同盟。当初は対ペルシア防衛のための同盟だったが、次第にアテナイ主導の事実上の帝国的性格を強めていったとされる。', '名詞', 'The Delian League was originally formed to protect Greek city-states from future Persian attacks.', '世界史（古代）', '850'),
    ('Trojan War', '古代ギリシアの伝承・叙事詩(ホメロスの『イーリアス』など)に語られる、ギリシア諸都市とトロイア(トロヤ)との間の戦争。史実性については学術的に議論があるが、トロイの木馬の逸話などで広く知られる。', '名詞', 'According to legend, the Trojan War began after the Trojan prince Paris took Helen from Sparta.', '世界史（古代）', '650'),
    ('Minoan civilization', '紀元前3000年頃から前1100年頃にかけて、クレタ島を中心に栄えた古代エーゲ文明。クノッソス宮殿の壮麗な遺構などで知られ、ヨーロッパ最古級の高度な文明の一つとされる。', '名詞', 'The Minoan civilization on Crete built the elaborate palace complex at Knossos.', '世界史（古代）', '800'),
    ('Mycenaean civilization', '紀元前1600年頃から前1100年頃にかけて、ギリシア本土を中心に栄えた古代エーゲ文明。堅固な城塞王宮や線文字Bと呼ばれる文字体系を用いたことで知られ、後のホメロスの叙事詩の舞台とも関連づけられるとされる。', '名詞', "The Mycenaean civilization is often associated with the legendary heroes described in Homer's epics.", '世界史（古代）', '850'),
    ('Rosetta Stone', '1799年にエジプトで発見された古代の石碑で、同じ内容が古代エジプトのヒエログリフ・民衆文字(デモティック)・古代ギリシア語の三種類の文字で刻まれている。この石碑が手がかりとなり、19世紀にヒエログリフの解読が達成された。', '名詞', 'The Rosetta Stone provided scholars with the key to finally deciphering Egyptian hieroglyphics.', '世界史（古代）', '700'),
    ('Great Sphinx of Giza', 'エジプトのギザにある、ライオンの体と人間(とされる)の顔を持つ巨大な石灰岩の彫像。近くのピラミッド群と並び、古代エジプトを代表する記念建造物の一つとされ、正確な建造時期や目的については諸説ある。', '名詞', 'The Great Sphinx of Giza has stood near the pyramids for thousands of years, though its exact original purpose is still debated.', '世界史（古代）', '650'),
    ('Indus Valley Civilization', '紀元前2600年頃から前1900年頃にかけて、インダス川流域(現在のパキスタンから北西インドにかけて)に栄えた古代文明。モヘンジョダロやハラッパーなど計画的な都市遺構で知られるが、その文字はいまだ完全には解読されていない。', '名詞', 'The Indus Valley Civilization built well-planned cities like Mohenjo-daro with advanced drainage systems.', '世界史（古代）', '800'),
    ('Mauryan Empire', '紀元前4世紀末にチャンドラグプタが建国した、古代インド史上初めて広大な領域を統一した帝国。孫にあたるアショーカ王の時代に最盛期を迎えたとされる。', '名詞', 'The Mauryan Empire unified much of the Indian subcontinent for the first time under a single ruler.', '世界史（古代）', '800'),
    ('Ashoka', '古代インドのマウリヤ朝の王で、即位当初は積極的な征服活動を行ったが、激しい戦争の惨禍を目にしたことをきっかけに仏教に深く帰依し、以後は非暴力や寛容を説く統治方針に転じたと伝えられる。', '名詞', 'Ashoka is said to have converted to Buddhism after witnessing the devastation caused by his conquest of Kalinga.', '世界史（古代）', '750'),
    ('Abbasid Caliphate', '750年にウマイヤ朝を倒して成立し、バグダードを首都として学問・商業が大いに栄えた、イスラーム世界を代表する王朝(カリフ国)。1258年にモンゴル軍によって滅ぼされた。', '名詞', 'The Abbasid Caliphate moved its capital to Baghdad and presided over a golden age of science and scholarship.', '世界史（中世）', '750'),
    ('Umayyad Caliphate', '661年から750年までダマスカスを首都とし、地中海沿岸から中央アジアにまで広がる大帝国を築いた、イスラーム史上初の世襲王朝。', '名詞', 'At its height, the Umayyad Caliphate stretched from Spain to the borders of India.', '世界史（中世）', '750'),
    ('House of Wisdom', '9世紀のバグダードでアッバース朝の保護のもと栄えた学術機関。ギリシャ・ペルシャ・インドなどの文献をアラビア語に翻訳し、数学・天文学・医学などの研究が行われた。', '名詞', 'Scholars at the House of Wisdom translated countless Greek manuscripts into Arabic.', '世界史（中世）', '800'),
    ('Al-Andalus', '711年のウマイヤ朝による征服から1492年のグラナダ陥落まで、イスラーム勢力が支配したイベリア半島の地域を指す呼び名。コルドバなどを中心に学問・文化が栄えた。', '名詞', 'Under Muslim rule, Al-Andalus became a center of learning where Muslim, Christian, and Jewish scholars worked side by side.', '世界史（中世）', '750'),
    ('madrasa', 'イスラーム世界で発達した、主にイスラーム法学や神学を教える高等教育機関。11世紀にセルジューク朝の宰相が各地に設立したものが特によく知られる。', '名詞', 'He studied Islamic law for years at a madrasa before becoming a judge.', '世界史（中世）', '700'),
    ('Investiture Controversy', '聖職者(特に司教)の任命権をめぐって、11世紀後半から12世紀前半にかけてローマ教皇と神聖ローマ皇帝の間で争われた政治的対立。1122年のヴォルムス協約で一応の決着がついた。', '名詞', 'The Investiture Controversy pitted the pope against the emperor over who could appoint bishops.', '世界史（中世）', '850'),
    ('East-West Schism', '1054年、教皇の使節とコンスタンティノープル総主教が互いを破門し合ったことをきっかけに、キリスト教会が西方のローマ・カトリック教会と東方の正教会に分裂した出来事。', '名詞', 'The East-West Schism left a lasting divide between Catholic and Orthodox Christianity.', '世界史（中世）', '800'),
    ('Hanseatic League', '中世後期の北ヨーロッパで、リューベックを中心とする都市や商人の同業組合が結成した、バルト海・北海沿岸の交易を支配した都市同盟。', '名詞', 'Merchants of the Hanseatic League controlled trade in furs, grain, and timber across the Baltic.', '世界史（中世）', '750'),
    ('Holy Roman Empire', '962年のオットー1世の戴冠を起源とし、主に中央ヨーロッパを支配した政治体で、1806年にナポレオンによって解体されるまで存続した。実態は多数の領邦の緩やかな連合体だった。', '名詞', 'For centuries, the Holy Roman Empire remained a loose patchwork of German-speaking states rather than a unified nation.', '世界史（中世）', '700'),
    ('Charlemagne', '8世紀後半から9世紀初頭にかけてフランク王国を治め、西暦800年にローマ教皇から皇帝の冠を授かった王。西ヨーロッパの大部分を統一し、学芸の復興を奨励したことでも知られる。', '名詞', 'Charlemagne was crowned emperor by the pope on Christmas Day in the year 800.', '世界史（中世）', '650'),
    ('Viking Age', '8世紀末から11世紀にかけて、スカンディナヴィア半島出身のヴァイキングがヨーロッパ各地への襲撃・交易・植民を活発に行った時代。', '名詞', 'Longships allowed Norse raiders to travel far beyond Scandinavia during the Viking Age.', '世界史（中世）', '650'),
    ('monasticism', '世俗を離れ、共同体または個人で祈りと労働を中心とする信仰生活を送る宗教的な生き方。中世ヨーロッパでは、規律ある共同生活の規則を定めた修道会を通じて広まった。', '名詞', 'European monasticism spread rapidly after the Rule of St. Benedict set out guidelines for communal religious life.', '世界史（中世）', '700'),
    ('scholasticism', '中世ヨーロッパの大学を中心に発展した、キリスト教神学とアリストテレスなど古代ギリシャ哲学を体系的に結び付けようとする学問的な方法・思潮。', '名詞', 'Thomas Aquinas is often regarded as the greatest philosopher of medieval scholasticism.', '世界史（中世）', '800'),
    ('Pax Mongolica', '13世紀から14世紀にかけて、モンゴル帝国の支配によってユーラシア大陸の広い範囲で治安が保たれ、東西の交易や文化交流が活発化した時期を指す呼び名。', '名詞', 'Merchants and travelers moved more safely along the Silk Road during the Pax Mongolica.', '世界史（中世）', '800'),
    ('Golden Horde', 'チンギス・ハンの孫バトゥが築いた、ロシアや中央アジアの広大な地域を支配したモンゴル系の国家。', '名詞', 'The Golden Horde collected tribute from Russian princes for more than two centuries.', '世界史（中世）', '750'),
    ('First Crusade', '1095年の教皇ウルバヌス2世の呼びかけをきっかけに始まり、1099年にエルサレムを占領して終わった、最初の十字軍遠征。', '名詞', 'The First Crusade succeeded in capturing Jerusalem in 1099.', '世界史（中世）', '700'),
    ('Mali Empire', '13世紀から17世紀にかけて西アフリカで栄えた王国。14世紀の王マンサ・ムーサが、豊富な金を伴ってメッカ巡礼を行ったことで特に知られる。', '名詞', 'Timbuktu flourished as a center of trade and Islamic scholarship under the Mali Empire.', '世界史（中世）', '700'),
    ('Timurid Empire', '14世紀後半にティムールが中央アジアに築いた帝国。首都サマルカンドを中心に、建築や学問など文化面でも大きな発展を遂げた。', '名詞', 'Architecture and astronomy flourished under the Timurid Empire, especially in its capital, Samarkand.', '世界史（中世）', '800'),
    ('Twelve Tables', '共和政ローマ初期(前451‑450年頃)に成文化された最古のローマ法典で、慣習法を平民にも分かるよう公開の場に刻んで示したことで知られる。', '名詞', 'The Twelve Tables were displayed publicly in the Forum so that even ordinary plebeians could know the laws that governed them.', 'ローマ史（古代・帝国）', '700'),
    ('decemviri', '前451年、慣習法を成文化した十二表法を起草するためにローマで臨時に任命された、十人からなる特別な立法委員会。', '名詞', 'The decemviri were granted extraordinary power to draft a written code of law for Rome.', 'ローマ史（古代・帝国）', '800'),
    ('Gracchi', '前2世紀後半、貧しい市民への土地再分配を訴えて改革を試みたものの、いずれも政治的な暴力によって命を落としたとされる、護民官ティベリウスとその弟ガイウスの兄弟(グラックス兄弟)。', '名詞', 'The reforms proposed by the Gracchi aimed to redistribute public land to landless Roman citizens.', 'ローマ史（古代・帝国）', '750'),
    ('Social War', '前91‑88年、ローマ市民権を求めるイタリア半島の同盟諸都市(ソキイ)がローマに対して起こした戦争で、最終的にイタリア人への市民権拡大につながった。', '名詞', "The Social War broke out when Rome's Italian allies took up arms to demand full Roman citizenship.", 'ローマ史（古代・帝国）', '750'),
    ('Battle of Cannae', '前216年、第二次ポエニ戦争でカルタゴの将軍ハンニバルが、包囲殲滅戦術によってローマ軍に壊滅的な敗北を与えたとされる戦い。', '名詞', 'At the Battle of Cannae, Hannibal used a double envelopment to surround and crush the much larger Roman army.', 'ローマ史（古代・帝国）', '700'),
    ('Battle of Zama', '前202年、第二次ポエニ戦争の最終局面で、ローマの将軍スキピオ・アフリカヌスがハンニバル率いるカルタゴ軍を破り、戦争の帰趨を決定づけたとされる戦い。', '名詞', "The Battle of Zama ended the Second Punic War when Scipio Africanus defeated Hannibal's forces in North Africa.", 'ローマ史（古代・帝国）', '750'),
    ('Spartacus', '前73‑71年に剣闘士や奴隷たちを率いて大規模な反乱(第三次奴隷戦争)を起こしたとされる、トラキア出身の剣闘士。', '名詞', 'Spartacus led an army of escaped gladiators and enslaved people in a revolt that shook the Roman Republic.', 'ローマ史（古代・帝国）', '650'),
    ('proscription', '政敵などの氏名を公にリストとして公示し、法の保護を奪って財産の没収や殺害を合法とする、共和政末期のローマで行われた措置。', '名詞', "During Sulla's proscription, the names of his political enemies were posted in public, stripping them of legal protection.", 'ローマ史（古代・帝国）', '750'),
    ('First Triumvirate', '前60年、カエサル・ポンペイウス・クラッススの有力者3人が私的に結んだ、法的な裏付けのない非公式の権力分掌の同盟。', '名詞', 'The First Triumvirate was an unofficial alliance among Julius Caesar, Pompey, and Crassus to dominate Roman politics.', 'ローマ史（古代・帝国）', '700'),
    ('Second Triumvirate', '前43年、オクタウィアヌス・アントニウス・レピドゥスの3人が、法律(レックス・ティティア)によって独裁的な権限を正式に与えられて結成した同盟。', '名詞', 'The Second Triumvirate legally granted Octavian, Antony, and Lepidus dictatorial powers to govern Rome.', 'ローマ史（古代・帝国）', '750'),
    ('Battle of Actium', '前31年、オクタウィアヌスの艦隊がアントニウスとクレオパトラの連合艦隊を破った海戦で、内戦を終わらせ、後のアウグストゥスによる帝政開始への道を開いたとされる。', '名詞', "Octavian's decisive naval victory at the Battle of Actium left him the sole ruler of the Roman world.", 'ローマ史（古代・帝国）', '700'),
    ('Pontifex Maximus', 'ローマの国家祭祀を統括する神官団の最高位で、共和政期は選挙で選ばれる名誉職だったが、アウグストゥス以降は歴代皇帝が慣例として兼任するようになった称号。', '名詞', 'Julius Caesar was elected Pontifex Maximus years before he became the sole ruler of Rome.', 'ローマ史（古代・帝国）', '800'),
    ('Vestal Virgins', 'かまどの女神ウェスタを祀る神殿で聖なる炎を絶やさぬよう守り続けた、貞潔の誓いを立てた少数の女性神官たち。', '名詞', 'The Vestal Virgins were responsible for keeping the sacred fire in the Temple of Vesta burning at all times.', 'ローマ史（古代・帝国）', '700'),
    ('Pantheon', '元々アウグストゥスの腹心アグリッパによって建てられ、火災焼失後にハドリアヌス帝の時代に現在の姿へ再建された、巨大な無筋コンクリート製ドームを持つローマの神殿。', '名詞', "The Pantheon's massive dome, with its open oculus at the center, has survived largely intact for nearly two thousand years.", 'ローマ史（古代・帝国）', '650'),
    ('Diocletian', '3世紀後半の混乱期を収拾し、帝国を東西に分割統治する体制(テトラルキア)を導入するなど大規模な行政・軍事改革を行った、後に自ら退位した珍しい皇帝。', '名詞', "Diocletian ended decades of instability by reorganizing the Roman Empire's administration and military.", 'ローマ史（古代・帝国）', '750'),
    ('Tetrarchy', 'ディオクレティアヌス帝が293年に導入した、広大な帝国を2人の正帝と2人の副帝の計4人で分担統治させる体制。', '名詞', 'Under the Tetrarchy, the Roman Empire was divided among four rulers to make it easier to govern and defend.', 'ローマ史（古代・帝国）', '800'),
    ('Edict of Milan', '313年、皇帝コンスタンティヌスとリキニウスが合意した、それまで迫害されていたキリスト教を含むあらゆる宗教信仰の自由をローマ帝国内で認める布告。', '名詞', 'The Edict of Milan granted Christians and followers of other religions the freedom to worship openly across the Roman Empire.', 'ローマ史（古代・帝国）', '750'),
    ('Visigoths', 'ゲルマン系のゴート人の一派で、410年に王アラリック1世のもとローマ市を占領・略奪したことで知られる部族。', '名詞', 'The Visigoths, led by King Alaric, captured and looted the city of Rome in 410 AD.', 'ローマ史（古代・帝国）', '700'),
    ('Vandals', 'ゲルマン系の部族の一つで、455年に王ガイセリックのもとローマ市を略奪したことから、その名が破壊行為を意味する英単語の語源になったとされる。', '名詞', "The Vandals sacked Rome in 455 AD, and their name later became the source of the English word 'vandalism.'", 'ローマ史（古代・帝国）', '650'),
    ('fall of the Western Roman Empire', '476年、ゲルマン人の将軍オドアケルが最後の西ローマ皇帝ロムルス・アウグストゥルスを退位させた出来事を伝統的な区切りとする、西ローマ帝国の終焉。', '名詞', 'Historians traditionally date the fall of the Western Roman Empire to 476 AD, when Odoacer deposed the last emperor.', 'ローマ史（古代・帝国）', '700'),
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
