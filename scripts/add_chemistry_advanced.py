# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""化学ドメインの大学専門課程レベルへの深化(2026-09-08・B24タスク・
authored by Claude、3並列サブエージェントで分野を分担しドラフト→WebSearchで
歴史的事実(人名・年代)を検証)。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_chemistry_advanced.py
仕上げ: relevel.pyは実行しない(他のB24バッチと同じ理由。既存の
H900/H990/H990Pリストに未対応でDOMAIN_BASEに一律で潰されるため)。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ('galvanic cell', '自発的に進む酸化還元反応の化学エネルギーを電気エネルギーへ変換する装置で、2つの半電池を導線と塩橋(または多孔質の隔壁)でつなぎ、外部回路に電流を取り出す仕組みを持つ。', '名詞句', 'In a galvanic cell, electrons flow spontaneously from the anode to the cathode through an external wire.', '化学', '870'),
    ('electrolytic cell', '熱力学的に非自発的な酸化還元反応を、外部電源から電気エネルギーを供給することで無理やり進行させる装置で、電気分解やめっき、金属精錬などに利用される。', '名詞句', 'An electrolytic cell uses an external power source to drive a non-spontaneous chemical reaction.', '化学', '870'),
    ('half-reaction', '酸化還元反応を「酸化される側」と「還元される側」の2つの反応式に分解したもので、それぞれで電子の数を合わせてから足し合わせることで全体の反応式を導く際に用いられる。', '名詞', 'Balancing a redox equation is much easier once you split it into two half-reactions.', '化学', '850'),
    ('standard reduction potential', '標準状態(25℃・1mol/L・1atm)のもとで、標準水素電極を基準(0V)としたときの、ある半反応(還元方向)の電位を表す量で、値が大きいほど酸化剤として強く働くことを示す。', '名詞句', 'A more positive standard reduction potential indicates a stronger tendency for a species to be reduced.', '化学', '900'),
    ('electrode potential', '電極が電解質溶液に浸されたときに界面で生じる電位差のことで、その大きさはイオンの種類・濃度・温度によって変化し、標準状態での値が標準電極電位と呼ばれる。', '名詞句', 'The electrode potential of a single half-cell cannot be measured directly; it must be compared with a reference electrode.', '化学', '870'),
    ('standard hydrogen electrode', '1atmの水素ガスを白金電極(白金黒でコーティング)上で水素イオン濃度1mol/Lの酸性溶液に接触させた電極で、電気化学において電極電位を測るための世界共通の基準点(0V)として使われる。', '名詞句', 'By international convention, the standard hydrogen electrode is assigned a potential of exactly zero volts at every temperature.', '化学', '900'),
    ('concentration cell', '同じ電極・同じ種類のイオンを使いながら両側の濃度だけを変えた2つの半電池を組み合わせた電池で、濃度の高い側から低い側へイオンが移動しようとする自由エネルギー変化が起電力として現れる。', '名詞句', 'A concentration cell produces a small voltage purely from the difference in ion concentration between its two half-cells.', '化学', '920'),
    ('overpotential', '電極反応の速度論的な抵抗(活性化エネルギーの壁)のために、熱力学的に計算される理論電位だけでは反応が実用的な速さで進まず、追加でかける必要のある電圧のことを指す。', '名詞', 'A high overpotential means extra voltage must be applied to drive the electrode reaction at a practical rate.', '化学', '930'),
    ("Faraday's laws of electrolysis", '(1)電極で変化する物質の量は流れた電気量に比例する、(2)同じ電気量に対して変化する物質の量は各物質の当量に比例する、という2つの法則からなり、電気分解の定量計算の基礎となっている。', '名詞句', "Faraday's laws of electrolysis let engineers calculate exactly how much metal will be deposited for a given amount of charge.", '化学', '900'),
    ('Faraday constant', '電子1モル(約6.022×10²³個)が運ぶ電気量の大きさを表す定数で、電気分解における物質量と電気量の変換や、ネルンストの式などの電気化学の計算に広く用いられる。', '名詞句', 'The Faraday constant links the amount of electric charge passed through a cell to the number of moles of electrons transferred.', '化学', '880'),
    ('reaction order', '実験的に求めた速度式v=k[A]^m[B]^nにおける指数m・nの値、およびそれらの和(全体の反応次数)を指し、反応速度が反応物濃度の変化にどれだけ敏感かを表す。', '名詞句', 'The reaction order with respect to a given reactant must be determined experimentally, not read off the balanced equation.', '化学', '850'),
    ('rate constant', '反応速度式において濃度項の前にかかる比例係数kのことで、反応物の濃度に依存せず、温度・触媒の有無・活性化エネルギーの大きさによって決まる値である。', '名詞句', 'The rate constant increases sharply with temperature, as described quantitatively by the Arrhenius equation.', '化学', '850'),
    ('molecularity', '素反応(1段階で完結する反応)において実際に衝突・関与する分子やイオンの数を表す整数値で、単分子反応(1)・二分子反応(2)・三分子反応(3)のように分類される。', '名詞', 'Unlike reaction order, molecularity is always a small whole number and is defined only for elementary reactions.', '化学', '900'),
    ('elementary reaction', '反応物から生成物へ中間体を経ずに一段階で直接進む反応のことで、複数の素反応が組み合わさって全体の反応機構を構成する。', '名詞句', 'A complex overall reaction is typically broken down into a series of simpler elementary reactions.', '化学', '870'),
    ('reaction mechanism', '出発物質が生成物へ変わるまでに実際にたどる素反応の連続した経路のことで、反応の速度式や律速段階を説明・予測するための土台となる。', '名詞句', 'Proposing a reaction mechanism requires identifying every intermediate formed along the way from reactants to products.', '化学', '850'),
    ('collision theory', '反応が起こるためには反応物の分子が(1)十分なエネルギー(活性化エネルギー以上)を持ち、(2)反応が進む適切な向きで衝突する必要がある、と説明する反応速度論の基本モデルである。', '名詞句', 'Collision theory explains why raising the temperature speeds up a reaction: more molecules collide with enough energy to react.', '化学', '850'),
    ('transition state theory', '反応物が生成物に変わる途中で必ず通過するエネルギー最大点(遷移状態・活性錯合体)を、反応物と平衡状態にある一種の化学種とみなし、統計力学を用いて速度定数を理論的に導出する反応速度論の理論である。', '名詞句', 'Transition state theory relates the rate constant to the free energy needed to reach the transition state.', '化学', '900'),
    ('pre-exponential factor', 'アレニウスの式k=Ae^(-Ea/RT)における定数Aのことで、活性化エネルギーとは独立に、分子がどれだけの頻度で反応に適した向きで衝突するかを表す。', '名詞句', 'In the Arrhenius equation, the pre-exponential factor accounts for how often molecules collide with the correct orientation.', '化学', '900'),
    ('pseudo-first-order reaction', '本来は複数の反応物の濃度に依存する高次の反応であるにもかかわらず、一方の反応物を大過剰に用いることでその濃度変化を無視できるようにし、実質的に一次反応の速度式で近似的に扱えるようにした反応のことである。', '名詞句', 'By using a huge excess of water, chemists can treat the hydrolysis reaction as a pseudo-first-order reaction.', '化学', '900'),
    ('steady-state approximation', '反応の途中で生成する不安定な中間体について、その生成速度と消費速度がほぼ釣り合い、濃度の正味の変化がゼロとみなせると仮定することで、複雑な多段階反応の速度式を、実験で測定可能な物質の濃度だけで表せる単純な形に書き直す手法である。', '名詞句', 'The steady-state approximation assumes that the concentration of a reactive intermediate stays roughly constant during most of the reaction.', '化学', '920'),
    ('autocatalysis', '化学反応の生成物の一つがその反応自体の触媒として機能する現象で、反応初期は触媒がほとんど存在しないため遅く、生成物が蓄積するにつれて反応速度が加速していくという特徴的な挙動を示す。', '名詞', 'In autocatalysis, the reaction starts out slowly but speeds up as the catalytic product accumulates.', '化学', '880'),
    ('heterogeneous catalysis', '固体の触媒表面に気体や液体の反応物が吸着し、表面上で反応が進行してから生成物が脱離するという過程をたどる触媒作用で、触媒と反応物が異なる相にあることが特徴である。', '名詞句', "Heterogeneous catalysis takes place on the surface of a solid catalyst, such as the platinum inside a car's catalytic converter.", '化学', '850'),
    ('homogeneous catalysis', '触媒が反応物と同じ気相または液相の中に均一に存在し、分子レベルで直接相互作用しながら反応を進める触媒作用のことで、固体表面を介する不均一触媒作用と対比される。', '名詞句', 'Homogeneous catalysis takes place entirely within a single phase, with the catalyst dissolved alongside the reactants.', '化学', '850'),
    ('Michaelis-Menten kinetics', '酵素(E)が基質(S)と可逆的に結合して酵素基質複合体(ES)を作り、それが生成物(P)へと変化して酵素が再生される、という反応スキームに基づいて酵素反応の速度を記述する理論で、低い基質濃度では反応速度が濃度にほぼ比例し、高濃度では酵素が飽和して速度が頭打ちになるという曲線を導く。', '名詞句', 'Michaelis-Menten kinetics explains why the reaction rate of many enzymes levels off as the substrate concentration keeps increasing.', '化学', '920'),
    ('Michaelis constant', 'Michaelis constant(Km)は、ミカエリス・メンテン反応速度論において、酵素反応の速度が最大速度Vmaxのちょうど半分になるときの基質濃度として定義される定数で、値が小さいほど酵素が基質と効率よく結合できることを示す。', '名詞句', 'A low Michaelis constant indicates that an enzyme reaches half its maximum rate at a very low substrate concentration.', '化学', '900'),
    ("Raoult's law", '理想溶液において、ある成分の蒸気圧がその成分単独のときの蒸気圧にその成分のモル分率を掛けた値に等しくなるという法則で、沸点上昇や凝固点降下といった溶液の束一的性質(colligative properties)を理解する基礎となる。', '名詞句', "Raoult's law predicts that dissolving a nonvolatile solute lowers the vapor pressure of the solvent.", '化学', '900'),
    ('Debye-Hückel theory', '電解質溶液中のイオンが完全に電離しているとみなし、イオン間の静電的な引力・反発力(イオン雰囲気の形成)を考慮することで、希薄溶液における活量係数のずれを理論的に計算する物理化学の理論である。', '名詞句', 'Debye-Hückel theory explains why the activity coefficients of ions deviate from one even in fairly dilute solutions.', '化学', '950'),
    ('activity coefficient', '実在の溶液が理想溶液からどれだけずれているかを補正するために濃度に掛ける係数で、理想溶液に近づくほど1に近づき、イオン濃度が高くなるほど1から離れていく。', '名詞句', 'As a solution becomes more concentrated, its activity coefficient typically drifts farther away from one.', '化学', '900'),
    ('ionic strength', '溶液中に存在するすべてのイオンについて、濃度とその電荷の2乗の積を合計し2で割ることで定義される量で、デバイ・ヒュッケル理論などで活量係数を計算する際の重要なパラメータとして使われる。', '名詞句', 'Increasing the ionic strength of a solution generally lowers the activity coefficients of the ions dissolved in it.', '化学', '880'),
    ('adsorption', '気体分子やイオン・分子が固体や液体の表面に物理的・化学的な力で付着し、表面付近の濃度が周囲より高くなる現象で、活性炭による脱色・脱臭や不均一触媒反応の第一段階など幅広い場面で重要な役割を果たす。', '名詞', 'Activated charcoal purifies water largely through the adsorption of impurities onto its enormous internal surface area.', '化学', '850'),
    ('adsorption isotherm', '温度を一定に保った条件で、平衡状態における固体表面への吸着量と、気体の圧力や溶液中の溶質濃度との関係を表した式(またはそのグラフ)で、触媒や吸着剤の表面特性を評価する際に用いられる。', '名詞句', 'The Langmuir adsorption isotherm assumes that adsorption stops once a single layer of molecules has covered the surface.', '化学', '900'),
    ('reaction quotient', '平衡定数の式とまったく同じ形をとりながら、平衡に達しているかどうかにかかわらず任意の時点での濃度や分圧を代入して計算する値で、Q(反応商)を平衡定数Kと比較することで反応が正方向・逆方向のどちらにさらに進むかを予測できる。', '名詞句', 'Comparing the reaction quotient with the equilibrium constant tells you which direction the reaction will shift to reach equilibrium.', '化学', '850'),
    ('chemical reaction', '原子の組み替えによって反応前の物質(反応物)とは化学的性質の異なる新しい物質(生成物)ができる変化のことで、状態変化(氷が溶けるなど)のように物質そのものは変わらない物理変化とは区別される。', '名詞句', 'Rust forms through a slow chemical reaction between iron and the oxygen in the air.', '化学', '400'),
    ('chemical equilibrium', '可逆反応において正反応の速度と逆反応の速度がちょうど等しくなり、反応物と生成物の濃度が時間とともに見かけ上変化しなくなった状態のことで、その濃度の比は平衡定数によって表される。', '名詞句', "At chemical equilibrium, the reaction hasn't stopped—the forward and reverse reactions are simply occurring at the same rate.", '化学', '650'),
    ('colloid', '直径がおよそ1ナノメートルから1マイクロメートルほどの微粒子(コロイド粒子)が、沈殿もせず完全に溶けきってもいない状態で他の物質の中に分散しているもので、牛乳・墨汁・霧・ゼリーなど身の回りに数多く存在する。', '名詞', 'Milk is a colloid in which tiny droplets of fat are dispersed throughout the surrounding water.', '化学', '600'),
    ('Grignard reaction', 'グリニャール反応とは、グリニャール試薬(R-MgX)がアルデヒド・ケトン・エステルなどのカルボニル炭素へ求核付加し、酸性水溶液での後処理を経てアルコールを与える反応。新たな炭素-炭素結合を形成する有機合成の基本反応の一つ。', '名詞句', 'The Grignard reaction between phenylmagnesium bromide and benzaldehyde produces a secondary alcohol after aqueous workup.', '化学', '870'),
    ('Wittig reaction', 'ウィッティヒ反応とは、リンイリド(ホスホニウムイリド)がアルデヒドやケトンのカルボニル基と反応し、四員環中間体(オキサホスフェタン)を経て炭素-炭素二重結合(アルケン)と酸化トリフェニルホスフィンを生じる反応。二重結合の位置を精密に制御できるため、複雑な天然物合成で頻用される。', '名詞句', 'The Wittig reaction converts an aldehyde into an alkene using a phosphorus ylide.', '化学', '900'),
    ('Friedel-Crafts acylation', 'フリーデル・クラフツアシル化とは、ルイス酸触媒(塩化アルミニウムなど)の存在下で酸塩化物や酸無水物が芳香環を求電子的にアシル化し、芳香族ケトンを生成する反応。生成するケトンが触媒と安定な錯体を作るため過剰付加が起こりにくく、位置選択性に優れる。', '名詞句', 'Friedel-Crafts acylation of benzene with acetyl chloride and AlCl3 gives acetophenone.', '化学', '860'),
    ('Friedel-Crafts alkylation', 'フリーデル・クラフツアルキル化とは、ルイス酸触媒下でハロゲン化アルキルなどから生じたカルボカチオンが芳香環を求電子的にアルキル化する反応。生成物の芳香環が活性化されるため多置換や、カルボカチオンの転位による副生成物が問題となりやすい。', '名詞句', 'Friedel-Crafts alkylation can suffer from polyalkylation and carbocation rearrangement side reactions.', '化学', '860'),
    ('Claisen condensation', 'クライゼン縮合とは、α水素を持つエステルが塩基によりエノラートとなり、別のエステルのカルボニル炭素を求核攻撃してβ-ケトエステルを生成する炭素-炭素結合形成反応。生成物の酸性プロトンが塩基に引き抜かれることで平衡が生成物側に片寄る。', '名詞句', 'Claisen condensation of ethyl acetate with sodium ethoxide gives ethyl acetoacetate.', '化学', '900'),
    ('Claisen rearrangement', 'クライゼン転位とは、アリルビニルエーテルを加熱すると[3,3]シグマトロピー転位により炭素-炭素結合が新生し、γ,δ-不飽和カルボニル化合物を与える反応。協奏的な周辺環状遷移状態を経るため、立体化学の制御に優れる。', '名詞句', 'Heating allyl phenyl ether induces a Claisen rearrangement to give an ortho-allylphenol.', '化学', '930'),
    ('Fischer esterification', 'フィッシャーエステル化とは、カルボン酸とアルコールを酸(硫酸など)触媒下で反応させ、エステルと水を生成する平衡反応。求核付加-脱離機構で進行し、過剰のアルコールの使用や生成した水の除去によって平衡を生成物側へ移動させる。', '名詞句', 'Fischer esterification of acetic acid with ethanol under acid catalysis yields ethyl acetate and water.', '化学', '850'),
    ('Curtius rearrangement', 'クルチウス転位とは、アシルアジドを加熱すると窒素ガスを放出しながら窒素原子上の置換基がカルボニル炭素へ協奏的に転位し、イソシアナートを生成する反応。イソシアナートを水やアルコールで捕捉すればアミンやカルバミン酸エステルへ導ける。', '名詞句', 'The Curtius rearrangement converts an acyl azide into an isocyanate with loss of nitrogen gas.', '化学', '970'),
    ('Beckmann rearrangement', 'ベックマン転位とは、ケトオキシムを酸触媒(五塩化リンや硫酸など)で処理すると、脱離基と反対側(アンチ)の置換基が窒素上へ立体特異的に転位し、アミド(環状ケトンの場合はラクタム)を与える反応。工業的にはシクロヘキサノンオキシムからナイロン6の原料カプロラクタムを製造する反応として重要。', '名詞句', 'The Beckmann rearrangement converts cyclohexanone oxime into caprolactam, a precursor of nylon 6.', '化学', '950'),
    ('Baeyer-Villiger oxidation', 'バイヤー・ビリガー酸化とは、ケトンを過酸(mCPBAなど)で酸化し、酸素原子をカルボニル基とアルキル基の間に挿入してエステルまたはラクトンを生成する反応。転位する基の電子密度・立体効果によって位置選択性が決まる。', '名詞句', 'Baeyer-Villiger oxidation of cyclohexanone with a peracid produces the seven-membered lactone caprolactone.', '化学', '960'),
    ('Wolff-Kishner reduction', 'ウォルフ・キッシュナー還元とは、アルデヒドやケトンから誘導したヒドラゾンを水酸化カリウムなどの強塩基とともに高温で加熱し、窒素ガスを放出させながらカルボニル基をメチレン基(CH2)へ完全に還元する反応。酸に不安定な基質にはクレメンゼン還元が代わりに用いられる。', '名詞句', 'Wolff-Kishner reduction converts the hydrazone of a ketone into a methylene group under strongly basic, high-temperature conditions.', '化学', '930'),
    ('Clemmensen reduction', 'クレメンゼン還元とは、アルデヒドやケトンを亜鉛アマルガム(Zn/Hg)と濃塩酸で処理し、カルボニル基をメチレン基(CH2)へ還元する反応。強酸性条件下で進行するため、酸に弱い官能基には不向きだが、強塩基に弱い基質にはウォルフ・キッシュナー還元の代替として有用である。', '名詞句', 'Clemmensen reduction with zinc amalgam and hydrochloric acid reduces the ketone from a Friedel-Crafts acylation to an alkyl chain.', '化学', '930'),
    ('Swern oxidation', 'スワーン酸化とは、ジメチルスルホキシド(DMSO)を塩化オキサリルで活性化して生じる求電子種を用い、低温・穏和な条件で第一級アルコールをアルデヒドへ、第二級アルコールをケトンへ酸化する反応。多くの官能基に対する許容性が高く、カルボン酸までの過剰酸化を避けられる点で有用。', '名詞句', 'Swern oxidation converts a primary alcohol into an aldehyde without over-oxidizing it to the carboxylic acid.', '化学', '920'),
    ('Grubbs catalyst', 'グラブス触媒とは、ルテニウムを中心金属とするカルベン錯体で、オレフィン(アルケン)メタセシス反応を温和な条件・高い官能基許容性のもとで進行させる触媒の総称。閉環メタセシス・交差メタセシスなど幅広い合成に用いられる。既出の「メタセシス(metathesis)」が化合物間の部分交換反応全般を指す一般名称であるのに対し、この語は炭素-炭素二重結合の組換えを促進する特定の金属錯体触媒を指す。', '名詞句', 'Grubbs catalyst enables olefin metathesis reactions to proceed under mild conditions with excellent functional group tolerance.', '化学', '970'),
    ('Cope rearrangement', 'コープ転位とは、1,5-ジエン化合物が加熱によって[3,3]シグマトロピー転位を起こし、炭素骨格上の二重結合の位置が入れ替わった異性体を与える反応。クライゼン転位の炭素版にあたり、いす形の周辺環状遷移状態を経て協奏的に進行する。', '名詞句', 'The Cope rearrangement of 1,5-hexadiene proceeds through a chair-like transition state to give an isomeric 1,5-diene.', '化学', '940'),
    ('Hofmann elimination', 'ホフマン脱離とは、アミンをヨウ化メチルで完全にメチル化して第四級アンモニウム塩とし、酸化銀と水で水酸化物に変換したのち加熱して脱離させる反応。かさ高い脱離基のために立体障害の少ない水素が引き抜かれ、通常のザイツェフ則とは逆に、より置換基の少ない安定性の低いアルケン(ホフマン生成物)が主生成物となる。', '名詞句', 'Hofmann elimination of a quaternary ammonium hydroxide preferentially gives the less substituted alkene.', '化学', '900'),
    ("Zaitsev's rule", 'ザイツェフ則とは、塩基による脱離反応(E1・E2)において、複数の脱離経路が可能な場合、二重結合上の置換基がより多い、熱力学的に安定なアルケンが主生成物として優先的に生成するという経験則。かさ高い塩基を用いる場合や第四級アンモニウム塩のホフマン脱離では、この規則とは逆の選択性(ホフマン則)が見られる。', '名詞句', "Zaitsev's rule predicts that E1 elimination of 2-bromobutane will favor the more substituted alkene, 2-butene.", '化学', '870'),
    ('Michael addition', 'マイケル付加とは、安定化されたカルバニオン(エノラートなど、マイケルドナー)がα,β-不飽和カルボニル化合物(マイケルアクセプター)のβ炭素へ共役的に求核付加(1,4-付加)し、新たな炭素-炭素結合を形成する反応。有機合成で炭素骨格を伸長する代表的な手法の一つ。', '名詞句', 'Michael addition of diethyl malonate to methyl vinyl ketone forms a new carbon-carbon bond at the beta position.', '化学', '880'),
    ('Mannich reaction', 'マンニッヒ反応とは、ケトン(またはアルデヒド)・ホルムアルデヒド(またはアルデヒド)・アミンの三成分が縮合し、β-アミノカルボニル化合物(マンニッヒ塩基)を生成する反応。エノールがアミンとアルデヒドから生じるイミニウムイオンを求核攻撃することで炭素-炭素結合が形成される。', '名詞句', 'The Mannich reaction combines formaldehyde, an amine, and a ketone to give a beta-amino carbonyl compound.', '化学', '910'),
    ('Sharpless epoxidation', 'シャープレス不斉エポキシ化とは、アリルアルコールをtert-ブチルヒドロペルオキシド・チタン(IV)イソプロポキシド・キラルな酒石酸ジエステルの組み合わせで処理し、高い立体選択性でエポキシドへ変換する不斉合成法。医薬品合成などで片方の鏡像異性体のみを必要とする場面で広く利用される。', '名詞句', 'Sharpless epoxidation uses a chiral titanium-tartrate catalyst to convert an allylic alcohol into an epoxide with high enantioselectivity.', '化学', '990'),
    ('anti-Markovnikov addition', '反マルコフニコフ付加とは、アルケンへの付加反応において、通常のマルコフニコフ則(水素がより多くの水素を持つ炭素へ付加する)とは逆に、求引原子が置換基の少ない炭素へ結合する位置選択性を指す。過酸化物存在下でのHBrのラジカル付加や、ヒドロホウ素化-酸化による水の付加がその代表例である。', '名詞句', 'Anti-Markovnikov addition of HBr to an alkene, promoted by peroxides, places the bromine on the less substituted carbon.', '化学', '870'),
    ('hydroboration-oxidation', 'ヒドロホウ素化-酸化とは、ボラン(BH3)などのホウ素試薬をアルケンにシン付加させて有機ホウ素化合物を生成させたのち、過酸化水素と塩基で酸化してアルコールへ変換する二段階反応。立体的に空いた炭素にホウ素が結合するため、酸触媒による水和とは逆の位置選択性(反マルコフニコフ型)でアルコールが得られる。', '名詞句', 'Hydroboration-oxidation of 1-hexene with BH3 followed by hydrogen peroxide gives 1-hexanol.', '化学', '880'),
    ('pericyclic reaction', '周辺環状反応とは、複数の結合の生成と切断が単一の環状遷移状態を経て協奏的に進行する反応の総称。イオンやラジカルなどの明確な中間体を経由しない点が特徴で、環化付加反応・電子環状反応・シグマトロピー転位の3種に大別される。反応の立体化学的な進行方向は分子軌道の対称性(ウッドワード・ホフマン則)によって支配される。', '名詞句', 'A pericyclic reaction proceeds through a single cyclic transition state without discrete ionic or radical intermediates.', '化学', '900'),
    ('sigmatropic rearrangement', 'シグマトロピー転位とは、パイ電子系に隣接するシグマ結合が切断されると同時に、電子系の反対側の末端に新たなシグマ結合が形成される周辺環状反応の一種。結合の移動距離は反応物の原子に番号を振った[i,j]表記で表され、クライゼン転位やコープ転位は代表的な[3,3]転位の例である。', '名詞句', 'The Claisen rearrangement is a well-known example of a [3,3]-sigmatropic rearrangement.', '化学', '930'),
    ('electrocyclic reaction', '電子環状反応とは、共役したポリエンの両末端の炭素間に新たなシグマ結合が1本形成され、環状化合物を生じる分子内の周辺環状反応。逆に環状化合物のシグマ結合が切れて開環しポリエンを生じる逆反応も含む。閉環時の立体化学(同旋的・逆旋的)はパイ電子数と反応条件によって決まる。', '名詞句', 'An electrocyclic reaction converts a conjugated polyene into a cyclic compound by forming a single new sigma bond at the chain ends.', '化学', '920'),
    ('cycloaddition', '環化付加反応とは、2つの独立したπ電子系が反応し、2本の新たなシグマ結合の形成を伴って環状生成物を与える周辺環状反応の総称。既出のDiels-Alder反応はこの分類に属する代表例([4+2]型)だが、環化付加自体はより広い反応群を指す上位概念である。', '名詞', 'The Diels-Alder reaction is the most well-known example of a [4+2] cycloaddition between a diene and a dienophile.', '化学', '880'),
    ('E1 reaction', 'E1反応とは、基質がまずイオン化してカルボカチオン中間体を生成し(律速段階)、続いて塩基が隣接炭素の水素を引き抜いてアルケンを与える、2段階で進行する脱離反応。反応速度は基質濃度のみに依存し、SN1反応と同じ中間体を共有するため両者が競合しやすい。', '名詞句', 'Tertiary alkyl halides in polar protic solvents tend to undergo E1 reaction, competing with SN1 substitution.', '化学', '850'),
    ('E2 reaction', 'E2反応とは、塩基が水素を引き抜くのと同時に脱離基が離れ、二重結合が協奏的に一段階で形成される脱離反応。反応速度は基質と塩基の両方の濃度に依存し、脱離基と水素がアンチ周平面の配置にあるときに最も進行しやすい。かさ高い塩基を用いるとザイツェフ則に反するホフマン型の生成物が優先することがある。', '名詞句', 'Treating 2-bromobutane with a strong, bulky base favors the E2 reaction over SN2 substitution.', '化学', '850'),
    ('epoxide', 'エポキシドとは、酸素原子1つと炭素原子2つからなる三員環構造を持つ環状エーテルの総称。環のひずみによって求核剤による開環反応を受けやすく、酸性・塩基性いずれの条件でも位置選択的に開環できるため、有機合成における官能基変換の要として利用される。', '名詞', 'Treating an alkene with mCPBA is a common way to synthesize an epoxide.', '化学', '850'),
    ('tautomerism', '互変異性とは、プロトンなど原子の移動を伴って2つの異性体(互変異性体)が急速に平衡的に相互変換する現象。最も代表的な例はケト形とエノール形の間で起こるケト・エノール互変異性であり、多くの場合ケト形の方が熱力学的に安定で優勢を占める。原子の位置が変わらない共鳴とは明確に区別される。', '名詞', 'Keto-enol tautomerism allows a ketone and its enol form to interconvert rapidly under acidic or basic conditions.', '化学', '850'),
    ('protecting group', '保護基とは、多段階合成の途中で反応させたくない官能基を一時的に別の安定な形へ変換しておくために導入する化学構造のこと。目的の反応が完了した後は脱保護によって元の官能基へ戻す。分子中に複数の反応性官能基が存在する場合の選択的な合成戦略に不可欠である。', '名詞句', 'A protecting group can temporarily mask a reactive hydroxyl group so that a Grignard reaction can proceed elsewhere in the molecule.', '化学', '900'),
    ('asymmetric synthesis', '不斉合成とは、キラルな触媒・試薬・出発物質などを用い、生成物として一方の鏡像異性体を優先的に(高いエナンチオ選択性で)作り出す合成手法の総称。ラセミ体を合成した後に分割する方法に比べ、効率よく目的の鏡像異性体を得られる利点がある。', '名詞句', 'Asymmetric synthesis using a chiral catalyst can produce a single enantiomer of a drug molecule in high optical purity.', '化学', '950'),
    ('regioselectivity', '位置選択性とは、複数の位置異性体が理論上生成しうる反応において、特定の位置での結合形成・開裂が優先的に起こる性質のこと。マルコフニコフ則・ザイツェフ則・ヒドロホウ素化の位置選択性などは、いずれも位置選択性の具体例である。', '名詞', 'The regioselectivity of hydroboration-oxidation places boron on the less hindered carbon of the alkene.', '化学', '900'),
    ('stereospecific reaction', '立体特異的反応とは、出発物質の立体化学(シス/トランスやRS配置など)が異なれば、生成物の立体化学も対応して異なる、明確な立体化学的対応関係を持つ反応のこと。SN2反応における配置の反転や、協奏的な周辺環状反応の立体特異的な進行がその代表例である。', '名詞句', 'The SN2 reaction is a stereospecific reaction because it always proceeds with inversion of configuration at the reacting carbon.', '化学', '920'),
    ('conformational isomer', '配座異性体とは、単結合まわりの回転によって生じる、原子の空間的な配置のみが異なる異性体のこと。エタンのねじれ形・重なり形や、シクロヘキサンのいす形・舟形などが代表例。結合の組み換えを伴わずに相互変換できる点で、鏡像異性体やジアステレオマーのような配置異性体とは区別される。', '名詞句', 'Rotation about the carbon-carbon single bond in ethane generates different conformational isomers without breaking any bonds.', '化学', '850'),
    ('Newman projection', 'ニューマン投影式とは、分子を特定の単結合の軸方向から眺めた図法で、手前の原子への結合を中心の点から、奥の原子への結合を円周から伸びる線として描く。ねじれ形・重なり形など、単結合まわりの立体配座(二面角)を視覚的に比較するために用いられる。', '名詞句', 'A Newman projection views a molecule along a carbon-carbon bond to clearly show the dihedral angle between substituents.', '化学', '870'),
    ('chair conformation', 'いす形配座とは、シクロヘキサンなどの六員環が取りうる立体配座のうち、環のひずみが最小で最も安定な形。各炭素原子の結合角が正四面体角に近く、置換基はアキシアル(軸方向)またはエクアトリアル(赤道方向)のいずれかに配置される。環反転(リングフリップ)によりアキシアルとエクアトリアルの位置が入れ替わったもう一方のいす形へ相互変換する。', '名詞句', 'In the chair conformation of cyclohexane, all bond angles are close to the ideal tetrahedral angle, making it the most stable form.', '化学', '860'),
    ('anomeric effect', 'アノマー効果とは、環内に酸素などのヘテロ原子を含む六員環化合物(ピラノースなど)において、ヘテロ原子に隣接する炭素(アノマー炭素)上の電気陰性な置換基が、立体障害の観点からは不利なはずのアキシアル配置を、超共役などの電子的要因によりむしろ好む現象。糖類の立体化学や反応性を理解するうえで重要な概念である。', '名詞句', 'The anomeric effect explains why an electronegative substituent at the anomeric carbon of a pyranose ring often prefers the axial orientation.', '化学', '950'),
    ('chemical formula', 'H2OやCO2のように元素記号と添字の数字を用いて物質を構成する原子の種類と数の割合を表したもの。中学理科で最初に学ぶ化学の基礎概念の一つ。', '名詞', 'The chemical formula for water is H2O.', '化学', '450'),
    ('chemical equation', '2H2 + O2 → 2H2Oのように反応物と生成物を化学式と矢印で表し、質量保存の法則に従って原子数のつり合いを取った式のこと。高校化学で学ぶ基本概念。', '名詞', 'This chemical equation shows how hydrogen and oxygen combine to form water.', '化学', '550'),
    ('chemical bond', 'イオン結合・共有結合・金属結合など、原子や分子を結びつけて安定な物質を作る力の総称。既存語のcovalent bond(共有結合)やionic bond(イオン結合)の上位概念にあたる。', '名詞', 'A chemical bond forms when atoms share or transfer electrons.', '化学', '600'),
    ('ligand field theory', '既存語のcrystal field theory(結晶場理論、静電的な相互作用のみを考える近似モデル)を発展させ、金属-配位子間の共有結合性(軌道の重なり)も取り込んだより精密な理論。d軌道分裂の程度や錯体の色・磁性を説明する基礎となる。', '名詞句', 'Ligand field theory explains the bonding in transition metal complexes more accurately than crystal field theory alone.', '化学', '930'),
    ('crystal field splitting energy', '既存語のcrystal field theory(結晶場理論)の枠組みで、配位子の作る場によって中心金属のd軌道が複数のエネルギー準位に分かれる際のエネルギー差のこと。この大小が錯体の色や磁性(高スピン・低スピン)を左右する。', '名詞句', 'The crystal field splitting energy determines whether a complex is high-spin or low-spin.', '化学', '940'),
    ('spectrochemical series', 'I⁻ < Br⁻ < Cl⁻ < H2O < NH3 < en < CN⁻ < COのように、配位子を結晶場分裂エネルギーの小さい順(弱い場)から大きい順(強い場)に並べた経験則の序列。錯体の色や高スピン・低スピンの予測に使われる。', '名詞句', 'In the spectrochemical series, cyanide produces a much stronger field than water.', '化学', '900'),
    ('Jahn-Teller effect', '電子配置が縮退している非直線分子が、エネルギーを下げるために自発的に対称性を崩して歪む現象。既存語のoctahedral complex(八面体錯体)が正八面体からわずかに歪んだ形をとる理由を説明する。', '名詞句', 'The Jahn-Teller effect causes many copper(II) complexes to adopt a distorted octahedral geometry.', '化学', '950'),
    ('high-spin complex', '弱い場の配位子(スペクトロ化学系列で下位)が中心金属に配位した際、d軌道間のエネルギー差が小さいため電子ができるだけ多くの軌道に不対で分散して入る錯体。既存語のoctahedral complexなどの磁性・色を理解する上で重要な分類。', '名詞句', 'Weak-field ligands such as water tend to form a high-spin complex with iron(II).', '化学', '870'),
    ('low-spin complex', '強い場の配位子(スペクトロ化学系列で上位)が中心金属に配位した際、d軌道間のエネルギー差が大きいため電子が低エネルギー軌道に対をなして優先的に詰まる錯体。high-spin complexと対をなす基本分類。', '名詞句', 'Strong-field ligands such as cyanide typically form a low-spin complex.', '化学', '870'),
    ('square planar complex', '既存語のoctahedral complex(配位数6)やtetrahedral complex(配位数4の正四面体形)と並ぶ代表的な錯体の立体構造の一つで、配位数4のうち4個の配位子が中心金属と同一平面上に正方形状に配置されたもの。trans effectによる配位子置換反応の主要な舞台でもある。', '名詞句', 'Many d8 metal ions such as platinum(II) form a square planar complex.', '化学', '860'),
    ('trans effect', '既存語のsquare planar complex(平面四配位錯体、本語彙集でも新規追加)において、特定の配位子が自身と180度反対側(トランス位)にある配位子の脱離・置換反応を速める現象。シスプラチンのような立体特異的な白金錯体を合成する上で重要な指導原理となっている。', '名詞句', 'The trans effect explains why certain ligands accelerate substitution at the position opposite them in a square planar complex.', '化学', '920'),
    ('organometallic compound', '金属原子と炭素原子の間に直接の共有結合(M-C結合)を持つ化合物の総称。既存語のGrignard reagentや本語彙集で扱うmetal carbonyl、sandwich compoundなどはいずれもこのカテゴリーに属する下位概念にあたる。', '名詞句', 'Grignard reagents are a classic example of an organometallic compound used in organic synthesis.', '化学', '850'),
    ('metal carbonyl', '既存語のcarbon monoxide(一酸化炭素)が配位子として金属に結合した有機金属化合物。18-electron ruleに従う配位数を取ることが多く、多くの遷移金属触媒反応の出発物質として利用される。', '名詞句', 'Nickel tetracarbonyl, Ni(CO)4, was one of the first metal carbonyl compounds ever synthesized.', '化学', '860'),
    ('sandwich compound', 'ferrocene(フェロセン)に代表されるように、平面状の環状配位子(多くはシクロペンタジエニル環)2枚が金属原子を上下から挟み込む構造を持つ有機金属化合物。metal-ring間の結合はhapticityの高い配位様式で説明される。', '名詞句', 'Ferrocene is the most famous sandwich compound, consisting of an iron atom between two cyclopentadienyl rings.', '化学', '870'),
    ('ferrocene', '鉄原子1個を2枚のシクロペンタジエニル環(C5H5)が上下から挟んだ構造を持つ、既存語のorganometallic compound(有機金属化合物)の代表例。安定性の高さと可逆な酸化還元特性から、電気化学の標準物質や高分子材料の原料としても利用される。', '名詞', 'Ferrocene was discovered by accident in 1951 while chemists were trying to synthesize a different compound.', '化学', '880'),
    ('hapticity', "既存語のligand(配位子)が中心金属に対して何個の連続した原子を介して結合しているかを示す概念・数値。Zeise's saltのエチレン配位子はη2、ferroceneのシクロペンタジエニル配位子はη5というように表記され、有機金属化合物の構造を理解する基本語彙となっている。", '名詞', 'The hapticity of the cyclopentadienyl ligand in ferrocene is five, written as eta-5.', '化学', '900'),
    ('pi-backbonding', "金属カルボニルやZeise's saltのようなアルケン錯体で見られる結合様式で、通常の配位子から金属への電子供与(σ供与)に加え、金属のd軌道から配位子の空のπ*軌道へ電子が「逆流」する現象。この相乗効果によって金属-配位子結合が強化される。", '名詞', 'Pi-backbonding from the metal to the carbon monoxide ligand strengthens the metal-carbon bond in metal carbonyls.', '化学', '910'),
    ('agostic interaction', '配位不飽和な遷移金属と、配位子上のC-H結合との間に生じる弱い相互作用。既存語のcoordination number(配位数)だけでは説明しきれない金属周辺の構造や反応性(特に重合触媒の活性種)を理解する鍵となる概念。', '名詞句', 'An agostic interaction can stabilize a coordinatively unsaturated metal center by donating electron density from a nearby C-H bond.', '化学', '950'),
    ('oxidative addition', 'A-B型の結合(H2、ハロゲン化アルキルなど)が金属中心に酸化的に付加し、金属の酸化数と配位数が2ずつ増加する反応。reductive elimination(還元的脱離)とペアで触媒サイクルの中心的な反応段階を構成する。', '名詞句', 'In oxidative addition, a metal complex inserts into a bond such as H-H or C-X, increasing both its oxidation state and coordination number.', '化学', '900'),
    ('reductive elimination', '金属上で隣り合う2つの配位子(多くは有機基)が結合を作りながら金属から脱離し、金属の酸化数と配位数がともに2ずつ減少する反応。oxidative additionと対をなし、触媒サイクルを閉じる役割を持つ。', '名詞句', 'Reductive elimination releases the coupled organic product and regenerates the active catalyst.', '化学', '900'),
    ('migratory insertion', '金属に配位した2つの配位子(例えばアルキル基とCO)の間で、片方が「移動」してもう一方の配位子との間に入り込み、新しい結合を作る反応。oxidative additionやreductive eliminationと並んで、有機金属触媒サイクルを構成する基本的な素反応の一つ。', '名詞句', 'Migratory insertion of carbon monoxide into a metal-alkyl bond is a key step in catalytic carbonylation reactions.', '化学', '920'),
    ('18-electron rule', '主族元素における8電子則(オクテット則)の遷移金属版にあたる経験則で、金属と配位子の価電子を合計すると希ガスと同じ18個になる錯体が特に安定になりやすいというもの。既存語のmetal carbonyl(金属カルボニル)など多くの有機金属化合物の組成・構造を予測する指針として使われる。', '名詞句', 'According to the 18-electron rule, many stable metal carbonyl complexes have a total valence electron count of 18.', '化学', '930'),
    ("Wade's rules", 'ボランやカルボラン、金属クラスターなどのかご状(多面体)化合物について、骨格を形成する電子対の数を数えることで、クロソ・ニド・アラクノといった構造の型を予測できる電子計数規則。既存語のmetal carbonylを含むクラスター化合物の構造化学で用いられる。', '名詞句', "Wade's rules predict that a cluster with seven skeletal electron pairs will adopt a closo structure.", '化学', '960'),
    ("Zeise's salt", '既存語のethylene(エチレン)が金属(白金)にη2(hapticity 2)の様式で側面から配位した錯体で、pi-backbondingを伴う金属-アルケン結合を示す最初期の実例として有機金属化学の歴史上重要な化合物とされる。', '名詞句', "Zeise's salt, K[PtCl3(C2H4)], is considered one of the earliest organometallic compounds ever discovered.", '化学', '970'),
    ('high-performance liquid chromatography', '既存語のchromatography(クロマトグラフィー)の一種で、高圧ポンプによって液体の移動相をカラムに送り込み、揮発しにくい化合物や熱に不安定な化合物も分離・定量できる分析法。医薬品分析や食品分析で広く使われる。', '名詞句', 'High-performance liquid chromatography can separate and quantify individual compounds in a complex mixture.', '化学', '870'),
    ('thin-layer chromatography', '既存語のchromatography(クロマトグラフィー)のうち、薄いシリカゲル層を固定相として用いる簡便な分離法。少量のサンプルで迅速に成分を確認できるため、high-performance liquid chromatographyのような機器分析の前段階として日常的に利用される。', '名詞句', 'Thin-layer chromatography is a quick and inexpensive way to monitor the progress of an organic reaction.', '化学', '850'),
    ('ion-exchange chromatography', '既存語のchromatography(クロマトグラフィー)のうち、固定相に結合した官能基と試料中のイオンとの間の静電的な引力の差を利用して分離する手法。水質分析や生体高分子(タンパク質・核酸)の精製で広く使われる。', '名詞句', 'Ion-exchange chromatography separates charged molecules based on their affinity for a charged stationary phase.', '化学', '870'),
    ('size-exclusion chromatography', '既存語のchromatography(クロマトグラフィー)のうち、多孔質の固定相の細孔に入り込める分子サイズの違いを利用して分離する手法。他の分離法と異なり分子と固定相の化学的な相互作用をほとんど利用しないため、高分子の分子量分布の測定によく用いられる。', '名詞句', 'Size-exclusion chromatography separates molecules by allowing smaller ones to enter the pores of the stationary phase while larger ones pass through faster.', '化学', '890'),
    ('atomic absorption spectroscopy', '既存語のspectroscopy(分光法)の一種で、試料を原子化した際に元素固有の波長の光がどれだけ吸収されるかを測定して濃度を求める分析法。atomic emission spectroscopyと対になる代表的な元素分析手法。', '名詞句', 'Atomic absorption spectroscopy can measure trace concentrations of metals such as lead in a water sample.', '化学', '880'),
    ('atomic emission spectroscopy', '既存語のspectroscopy(分光法)の一種で、試料を高温の炎やプラズマで励起し、原子が元の状態に戻る際に放出する元素固有の波長の光を測定して定性・定量分析する手法。atomic absorption spectroscopyと対をなす代表的な元素分析法。', '名詞句', 'Atomic emission spectroscopy identifies elements by analyzing the characteristic wavelengths of light they emit when excited.', '化学', '880'),
    ('potentiometry', '電流をほとんど流さない条件で2つの電極間の電位差を測定し、既存語のNernst equationを介してイオン濃度を求める電気化学的な分析法。voltammetryのように電流を流して測定する手法とは区別される。', '名詞', 'Potentiometry using a pH electrode is one of the most common ways to measure the acidity of a solution.', '化学', '860'),
    ('voltammetry', '作用電極の電位を掃引しながら流れる電流を測定し、そのグラフ(ボルタモグラム)から化学種の酸化還元挙動や濃度を分析する電気化学的手法の総称。potentiometry(電流をほぼ流さず電位のみを測る手法)と対比される。', '名詞', 'In voltammetry, the current is measured as the potential applied to the electrode is systematically varied.', '化学', '880'),
    ('cyclic voltammetry', 'voltammetryの中でも特に代表的な手法で、電極電位を一定の速度で往復させ、それに応じて流れる電流をプロットしたボルタモグラムから、酸化還元反応の可逆性や電子移動速度などを調べる分析法。電気化学の研究で最も基本的な測定法の一つ。', '名詞句', 'Cyclic voltammetry sweeps the electrode potential forward and then in reverse to reveal both oxidation and reduction processes.', '化学', '900'),
    ('coulometry', 'ファラデーの電気分解の法則に基づき、電気分解に消費された電気量(クーロン数)から反応した物質の物質量を求める分析法。既存語のelectrolysis(電気分解)を定量分析に応用した手法で、微量の水分定量に使われるKarl Fischer titrationの電量法版などで実用化されている。', '名詞', 'Coulometry determines the amount of substance by measuring the total electric charge consumed in an electrochemical reaction.', '化学', '890'),
    ('internal standard', '既知量を試料に添加し、目的成分(analyte)のシグナルとの比率を取ることで、注入量や装置感度の変動による誤差を補正するために使う基準物質。既存語のcalibration curve(検量線)を内部標準比で作成する手法(内部標準法)と組み合わせて使われることが多い。', '名詞句', 'Chemists add a known amount of an internal standard to correct for variations in sample preparation and instrument response.', '化学', '850'),
    ('standard addition method', '試料に既知量の標準物質を数段階に分けて添加し、信号強度の増加分から元の試料中の濃度を逆算する定量法。既存語のcalibration curve(検量線)を単純に外部標準で作成する方法では対応しにくい、マトリックス効果の大きい試料の分析に適している。', '名詞句', 'The standard addition method is especially useful when the sample matrix interferes with a simple calibration curve.', '化学', '900'),
    ('limit of quantitation', '既存語のlimit of detection(検出限界)よりも厳しい基準で、分析結果を許容できる精度・正確さで定量値として報告できる最小の濃度。医薬品や環境分析における分析法バリデーションで必須の指標の一つ。', '名詞句', 'The limit of quantitation is typically defined as ten times the standard deviation of the blank signal.', '化学', '910'),
    ('complexometric titration', '既存語のchelation(キレート化)の原理を利用し、金属イオンがEDTAのようなキレート剤と1対1で強く結合する反応を用いて金属イオンの濃度を求める滴定法。水の硬度分析などで広く使われる。', '名詞句', 'Complexometric titration with EDTA is a standard method for determining the hardness of water.', '化学', '890'),
    ('redox titration', '既存語のtitration(滴定)のうち、酸化剤と還元剤の間の電子の授受(酸化還元反応)を利用して未知試料の濃度を求める滴定法。酸塩基滴定や既存語のcomplexometric titration(錯滴定)と並ぶ代表的な滴定の分類の一つ。', '名詞句', 'Redox titration with potassium permanganate can determine the concentration of iron(II) ions in a solution.', '化学', '860'),
    ('Karl Fischer titration', 'ヨウ素と二酸化硫黄が水の存在下でのみ定量的に反応する性質を利用し、固体・液体・気体試料中のごく微量の水分含有量を求める滴定法。既存語のredox titration(酸化還元滴定)の応用例の一つで、少量の水分をcoulometry(電量分析法)の形式で測定することも多い。', '名詞句', 'Karl Fischer titration can accurately measure trace amounts of water in oils, solvents, and pharmaceutical powders.', '化学', '930'),
    ('nephelometry', '既存語のprecipitation reaction(沈殿反応)などで生じた微小な懸濁粒子に光を当て、粒子によって散乱される光を(入射方向とは異なる角度で)測定することで濃度を求める分析法。水質検査や臨床検査における抗原抗体反応の定量によく用いられる。', '名詞', 'Nephelometry measures the intensity of light scattered by suspended particles to estimate their concentration.', '化学', '920'),
]


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

    print(f"words:   +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print("totals -> words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
        if WORDS:
            dom = WORDS[0][4]
            print(f"totals -> {dom}:",
                  conn.execute(
                      "SELECT COUNT(*) FROM words WHERE domain=?", (dom,)
                  ).fetchone()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
