# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""天文ドメインの大学専門課程レベルへの深化(2026-09-08・B24タスク・
authored by Claude)。`docs/B24_VOCAB_DRAFT_REVIEW.md`で先にドラフトされた
118語(既存DB全体との重複チェック済み)を2並列サブエージェントで
定義文・例文・detail生成→WebSearchで歴史的事実(人名・年代)を検証。

既存DBとの同一概念の重複2語を除外: Chandrasekhar limit/magnetar
(いずれも物理分野の既存語と同一概念)。sunspot cycleのみ、既存語
(アマチュア無線・無線通信分野、電波伝搬への影響という文脈)とは着眼点が
異なる(天文学・太陽物理学としての活動周期そのもの)ため
`sunspot cycle (astronomy)`として同綴り異義語(B17b)化して採用。

2026-09-08ユーザー指示「語彙拡充は各分野の中学高等学校相当の拡充、
小学校相当の拡充も多少あってもいいと思います」を受け、本バッチとは別に
`tag_domain_breadth_2026_09_08.py`(既存の中学・高校相当語をword_domain_
tagsで天文ドメインにも追加タグ付け)と`add_domain_breadth_elementary_
2026_09_08.py`(小学校〜中学相当の基本語を新規追加)を実施済み
(詳細はdocs/TODO.md参照)。本バッチ自体は当初の計画通り学部専門
レベル(level 850〜990+)のみ。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_astronomy_advanced.py
仕上げ: relevel.pyは実行しない(add_math_advanced.pyと同じ理由)。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("active galactic nucleus", "銀河の中心部にある超大質量ブラックホールへのガス降着によって、通常の恒星の光を上回るほど明るく輝く領域。電波・赤外線・可視光・X線・ガンマ線など広い波長域で強い放射を示し、クエーサーやセイファート銀河などはその一種とされる。", "名詞句", "The intense radiation from an active galactic nucleus can outshine the combined light of every star in its host galaxy.", "天文", "920"),
    ("adaptive optics", "大気のゆらぎによって生じる星像のぼやけをリアルタイムで検出し、可変形鏡などを用いて瞬時に補正することで、地上望遠鏡でも回折限界に近い鮮明な像を得るための技術。", "名詞句", "Adaptive optics allows ground-based telescopes to correct for atmospheric turbulence and achieve images nearly as sharp as those from space telescopes.", "天文", "900"),
    ("angular resolution", "望遠鏡や観測機器が、空間的に近接した2つの点(天体)を別々のものとして識別できる能力。通常は角度(秒角など)で表され、値が小さいほど分解能が高いことを意味する。", "名詞句", "A telescope's angular resolution depends on both its aperture size and the wavelength of light being observed.", "天文", "900"),
    ("astrobiology", "地球上および地球外における生命の起源・進化・分布・未来を、生物学・化学・惑星科学・天文学を統合して研究する学際的な学問分野。系外惑星の探査やハビタブルゾーンの研究などと密接に関わる。", "名詞", "Astrobiology combines biology, chemistry, and planetary science to investigate whether life could exist beyond Earth.", "天文", "850"),
    ("astrometry", "恒星や天体の位置・距離・固有運動・視差などを高精度に測定する天文学の分野。年周視差の測定による距離決定や、恒星の空間運動の解明などに用いられる。", "名詞", "Astrometry measures the precise positions and motions of stars, allowing astronomers to determine their distances through parallax.", "天文", "900"),
    ("astronomical spectroscopy", "天体からの光をプリズムや回折格子で波長ごとに分解し、そのスペクトルを解析することで、天体の組成・温度・密度・視線速度・磁場などを調べる観測手法。", "名詞句", "Astronomical spectroscopy reveals the chemical composition of distant stars by analyzing the dark absorption lines in their spectra.", "天文", "880"),
    ("asymptotic giant branch", "恒星が赤色巨星段階の後、中心にできた炭素・酸素の核の周りでヘリウムと水素の殻状の核融合を交互に起こしながら、ヘルツシュプルング・ラッセル図上で赤色巨星分枝のさらに上方(高光度側)へと進化していく段階。太陽程度からやや大きい質量の恒星が最終的にたどる進化段階の一つ。", "名詞句", "Stars on the asymptotic giant branch undergo dramatic pulsations and mass loss that eventually expose their hot cores as white dwarfs.", "天文", "930"),
    ("baryon acoustic oscillation", "初期宇宙において光子と重粒子(バリオン)が強く結合したプラズマ中を音波として伝わった密度ゆらぎが、宇宙の晴れ上がり以降に残した痕跡。銀河分布の統計的な相関に特徴的な長さのスケールとして現れ、宇宙論的距離の測定に利用される。", "名詞句", "Baryon acoustic oscillations leave a characteristic scale in the distribution of galaxies that can be used as a cosmic ruler.", "天文", "970"),
    ("biosignature", "ある天体に過去または現在生命が存在したことを示唆する、大気組成・地質学的特徴・分子構造などの観測可能な痕跡。系外惑星の大気中の酸素とメタンの組み合わせなどが候補として挙げられる。", "名詞", "The detection of oxygen and methane together in an exoplanet's atmosphere could serve as a potential biosignature.", "天文", "900"),
    ("bolometric magnitude", "恒星などの天体が、可視光だけでなく赤外線・紫外線・X線などあらゆる波長の電磁波として放射する全エネルギー(全放射光度)を、等級のスケールで表したもの。", "名詞句", "Bolometric magnitude accounts for radiation emitted across the entire electromagnetic spectrum, not just visible light.", "天文", "950"),
    ("chromosphere", "太陽や恒星の光球の外側に位置する、薄く不規則な大気層。皆既日食の際に赤みがかった光として観測されることがあり、光球より高温だが密度は非常に低い。", "名詞", "The chromosphere appears as a thin reddish layer around the Sun that becomes visible for a few seconds during a total solar eclipse.", "天文", "900"),
    ("circumbinary planet", "単独の恒星ではなく、互いの周りを公転する連星系全体を取り囲む軌道を持つ惑星。", "名詞句", "A circumbinary planet orbits both stars of a binary system rather than just one of them.", "天文", "900"),
    ("CNO cycle", "炭素・窒素・酸素を触媒として、4個の水素原子核をヘリウム原子核に変換する核融合反応。太陽よりも質量が大きく中心温度の高い恒星で、陽子-陽子連鎖反応に代わる主要なエネルギー源となる。", "名詞句", "In stars more massive than the Sun, the CNO cycle becomes the dominant source of nuclear energy because it is more sensitive to temperature than the proton-proton chain.", "天文", "950"),
    ("common envelope evolution", "近接連星系において、一方の星が膨張して他方の伴星を自らの外層(エンベロープ)の中に取り込んでしまい、共通の希薄なガス層の中を両者の中心核が互いの周りを公転しながら軌道を縮めていく進化段階。", "名詞句", "Common envelope evolution can dramatically shrink the orbit of a binary system in a very short astronomical timescale.", "天文", "980"),
    ("comoving distance", "宇宙膨張による見かけの距離の変化を取り除き、共に膨張する座標系(共動座標)上で測った2点間の距離。宇宙膨張とともに変化しない「地図上の距離」に相当する。", "名詞句", "Comoving distance factors out the expansion of the universe, so it remains constant over time for objects that are not moving relative to the cosmic expansion.", "天文", "950"),
    ("convective zone", "恒星内部で、放射によるエネルギー輸送だけでは十分な熱を運びきれず、高温のガスが浮力によって上昇し低温のガスが沈み込む対流によってエネルギーが輸送される層。", "名詞句", "In the Sun, the convective zone lies just below the photosphere and is responsible for the granulation pattern visible on its surface.", "天文", "900"),
    ("core-collapse supernova", "太陽の8倍以上の質量を持つ大質量星が、中心核での核融合燃料を使い果たして鉄の核が自らの重力を支えきれなくなり、急激に崩壊した後に激しく爆発する現象。", "名詞句", "A core-collapse supernova occurs when a massive star's iron core can no longer support itself against gravity and collapses in less than a second.", "天文", "930"),
    ("coronal heating problem", "太陽表面の光球(約6000K)よりも外側にあるコロナの温度が、なぜ100万度以上にまで加熱されているのかという、太陽物理学における未解決問題。", "名詞句", "The coronal heating problem asks why the Sun's outer atmosphere is hundreds of times hotter than its visible surface.", "天文", "950"),
    ("coronal mass ejection", "太陽コロナから、磁場を伴った大量のプラズマが宇宙空間へ爆発的に放出される現象。地球に到達すると磁気嵐や通信障害、オーロラの活発化などを引き起こすことがある。", "名詞句", "A coronal mass ejection can hurl billions of tons of magnetized plasma into space at speeds of several million kilometers per hour.", "天文", "900"),
    ("cosmic distance ladder", "天体までの距離を測定する複数の手法を、近距離から遠距離へと段階的につなぎ合わせた体系。年周視差、セファイド変光星の周期光度関係、Ia型超新星などを順に用いることで、宇宙論的な距離までを較正する。", "名詞句", "The cosmic distance ladder relies on nearby, well-calibrated distance indicators to determine the distances to progressively more remote objects.", "天文", "900"),
    ("cosmic inflation", "ビッグバン直後のごく短い時間に、宇宙が指数関数的に急激に膨張したとする理論。宇宙の平坦性や大規模構造の一様性、地平線問題などを自然に説明する枠組みとして提唱された。", "名詞句", "Cosmic inflation proposes that the universe expanded exponentially in a tiny fraction of a second after the Big Bang.", "天文", "930"),
    ("cosmic recombination", "ビッグバンからおよそ38万年後、宇宙の温度が下がったことで自由電子と陽子が結合して中性水素原子が形成され、それまで光子を散乱させていたプラズマが晴れ上がり、宇宙が光に対して透明になった出来事。", "名詞句", "Cosmic recombination allowed photons to travel freely through space for the first time, producing the light we now observe as the cosmic microwave background.", "天文", "930"),
    ("cosmic scale factor", "宇宙の膨張にともなって、任意の2点間の共動距離が実際の物理的距離へと変換される際の比例係数。フリードマン方程式における基本的な変数で、慣習的に現在の値を1に規格化する。", "名詞句", "The cosmic scale factor describes how distances between galaxies grow over time as the universe expands.", "天文", "950"),
    ("cosmic web", "銀河やダークマターが、フィラメント状・シート状に連なりながら網目のような巨大な構造を形成し、その間に銀河がほとんど存在しない広大なボイド(空洞)が広がっている、宇宙最大スケールの物質分布のパターン。", "名詞句", "The cosmic web consists of vast filaments of galaxies and dark matter separated by enormous empty voids.", "天文", "900"),
    ("critical density", "宇宙全体の平均密度がこの値に等しいとき、宇宙の幾何学が平坦(ユークリッド的)になるとされる、宇宙膨張率(ハッブル定数)によって決まる密度の基準値。", "名詞句", "If the universe's average density exceeds the critical density, space would be positively curved and the expansion would eventually reverse.", "天文", "930"),
    ("dark matter halo", "銀河やその集団を取り囲むように分布する、光を発しないダークマターの巨大な球状の構造。可視光では直接見えないが、銀河の回転曲線や重力レンズ効果などを通じてその存在が推定される。", "名詞句", "A galaxy's dark matter halo extends far beyond its visible stars and dominates its total mass.", "天文", "920"),
    ("degeneracy pressure", "パウリの排他原理により、電子や中性子などのフェルミ粒子が同じ量子状態を取れないために生じる、天体を極端に圧縮しても消えない圧力。通常の熱による圧力とは異なり、温度にほとんど依存しない。", "名詞句", "Degeneracy pressure, rather than thermal pressure, supports white dwarfs and neutron stars against further gravitational collapse.", "天文", "930"),
    ("diffraction limit", "レンズや鏡の有限の口径によって光が回折するために生じる、光学系が原理的に達成できる最高の角分解能の限界。口径が大きいほど、また波長が短いほど回折限界による分解能は向上する。", "名詞句", "The diffraction limit sets the theoretical best angular resolution a telescope can achieve, regardless of how well its optics are manufactured.", "天文", "930"),
    ("direct imaging", "中心星からの明るい光を遮ったり打ち消したりする技術を用いて、系外惑星そのものが放つ、または反射する微弱な光を直接とらえて撮影する観測手法。", "名詞句", "Direct imaging has successfully photographed several young, massive exoplanets orbiting far from their host stars.", "天文", "900"),
    ("Drake equation", "天の川銀河内で、電波などを通じて人類と交信可能な技術文明の数を、恒星形成率や惑星を持つ恒星の割合、生命が誕生する確率など複数の要因の積として見積もるための式。", "名詞句", "The Drake equation breaks down the number of communicative civilizations in our galaxy into a series of estimated probabilities and rates.", "天文", "900"),
    ("dwarf spheroidal galaxy", "恒星の数が少なく、明確な渦巻き構造を持たない、非常に暗く低質量な楕円形の矮小銀河。天の川銀河などの大きな銀河の周りを衛星銀河として公転しているものが多く見つかっている。", "名詞句", "Dwarf spheroidal galaxies are among the least luminous and most dark-matter-dominated galaxies known.", "天文", "950"),
    ("Eddington luminosity", "天体が球対称かつ静水圧平衡にあると仮定したとき、内向きの重力と外向きの放射圧がつり合う限界の光度。この光度を超えるとエネルギーの放射圧が重力を上回り、周囲の物質が吹き飛ばされる。", "名詞句", "A star or accreting black hole radiating above its Eddington luminosity would blow away its own surrounding gas through radiation pressure.", "天文", "950"),
    ("exomoon", "太陽系外の惑星(系外惑星)の周りを公転する衛星。理論的には存在が予測されているが、確実に確認された例はまだ非常に少ない。", "名詞", "Astronomers have proposed several candidate exomoons, but confirming their existence has proven extremely difficult with current technology.", "天文", "900"),
    ("Fermi paradox", "天の川銀河には知的文明が生まれる条件を満たす恒星や惑星が数多く存在すると考えられるにもかかわらず、地球外知的生命体からの明確な兆候や接触の証拠がこれまで一切見つかっていないという矛盾。", "名詞句", "The Fermi paradox highlights the tension between the high estimated probability of extraterrestrial civilizations and the total lack of evidence for them.", "天文", "900"),
    ("flat universe", "宇宙全体の幾何学的な曲率がゼロであり、平行線が交わることも発散することもなく、ユークリッド幾何学がそのまま成り立つとされる宇宙のモデル。宇宙の平均密度がちょうど臨界密度に等しい場合に対応する。", "名詞句", "Observations of the cosmic microwave background strongly suggest that we live in a flat universe, or one very close to it.", "天文", "930"),
    ("flatness problem", "標準ビッグバン理論では、宇宙が観測されるようにほぼ完全に平坦であるためには、初期宇宙の密度が臨界密度と極めて高い精度で一致している必要があり、その精密な初期条件がなぜ実現したのかを自然には説明できないという理論的な問題。", "名詞句", "The flatness problem asks why the early universe's density was fine-tuned so precisely close to the critical density.", "天文", "970"),
    ("Friedmann equations", "一般相対性理論に基づき、宇宙が一様かつ等方であると仮定したときの宇宙全体の膨張(または収縮)の時間変化を記述する2つの微分方程式。宇宙の物質・エネルギー密度と曲率、膨張率の関係を与える。", "名詞句", "The Friedmann equations relate the expansion rate of the universe to its density, curvature, and cosmological constant.", "天文", "980"),
    ("frost line", "原始惑星系円盤の中で、水や二酸化炭素、メタンなどの揮発性物質が固体の氷として存在できる温度以下になる、中心星からの距離の境界線。太陽系ではこの外側で木星型のガス惑星や氷天体が形成されやすいと考えられている。", "名詞句", "Beyond the frost line, water can freeze into solid ice, providing extra solid material for giant planets to form.", "天文", "910"),
    ("galactic bar", "渦巻銀河の中心部を貫くように恒星やガスが棒状に密集して分布している構造。棒の両端から渦状腕が伸びていることが多く、天の川銀河もこの棒状構造を持つ棒渦巻銀河に分類される。", "名詞句", "The galactic bar channels gas from the outer disk toward the center, potentially fueling star formation and feeding the central black hole.", "天文", "930"),
    ("galactic bulge", "渦巻銀河の中心部に見られる、円盤よりも厚みがあり恒星が密集して球状またはやや扁平に分布する領域。年老いた恒星を多く含むことが多い。", "名詞句", "The galactic bulge at the center of the Milky Way is densely packed with old, metal-rich stars.", "天文", "900"),
    ("galactic center", "銀河の質量・恒星分布の中心にあたる領域。天の川銀河の場合はいて座の方向に位置し、超大質量ブラックホールであるいて座A*が存在する。", "名詞句", "At the galactic center of the Milky Way lies Sagittarius A*, a supermassive black hole with a mass of about four million Suns.", "天文", "880"),
    ("galactic disk", "渦巻銀河において、恒星・ガス・ちりが薄い円盤状に分布し、その中に渦状腕が形成されている構造。銀河全体の質量の大部分を占め、若い恒星の形成が活発に起きている領域でもある。", "名詞句", "The galactic disk contains most of a spiral galaxy's gas, dust, and young stars, along with its characteristic spiral arms.", "天文", "900"),
    ("galactic halo", "銀河の円盤やバルジを取り囲むように、球状に広がる希薄な領域。年老いた恒星や球状星団が散らばっているほか、目に見えないダークマターの大部分もこの領域に存在すると考えられている。", "名詞句", "The galactic halo contains some of the oldest stars in a galaxy, along with globular clusters that orbit far above and below the disk.", "天文", "900"),
    ("galactic rotation curve", "銀河の中心からの距離に対して、その距離にあるガスや恒星が銀河を公転する速度をプロットしたグラフ。通常の物質だけから予測される分布とは異なり、多くの渦巻銀河で外側でも回転速度が落ちずほぼ一定に保たれる「平坦な回転曲線」が観測されている。", "名詞句", "Galactic rotation curves remain flat at large distances from the center, contrary to what would be expected if only visible matter were present.", "天文", "930"),
    ("galaxy merger", "2つ以上の銀河が互いの重力に引かれて衝突し、最終的に1つの銀河へと合体していく現象。合体の過程でガスが圧縮されて爆発的な星形成(スターバースト)が引き起こされることが多い。", "名詞句", "Galaxy mergers can trigger intense bursts of star formation as clouds of gas from both galaxies collide and compress.", "天文", "900"),
    ("giant impact hypothesis", "太陽系形成初期に、火星ほどの大きさを持つ原始惑星が原始地球に斜めに衝突し、そのとき飛び散った破片が地球の周りで集積して月が形成されたとする、月の起源に関する現在最も有力な仮説。", "名詞句", "The giant impact hypothesis proposes that debris from a collision between the young Earth and a Mars-sized protoplanet coalesced to form the Moon.", "天文", "900"),
    ("gravitational microlensing", "手前にある恒星などの重力によって背景の遠方天体からの光の経路が曲げられ、一時的に増光して見える現象。背景の恒星に系外惑星が伴っている場合、光度変化のパターンにその影響が現れることを利用して惑星を検出できる。", "名詞句", "Gravitational microlensing can reveal the presence of an exoplanet through a brief, characteristic distortion in the brightening of a background star's light.", "天文", "950"),
    ("habitable zone", "恒星からの距離が適度で、惑星表面に液体の水が安定して存在しうる温度範囲となる軌道領域。生命が存在しうる条件の一つの目安として用いられる。", "名詞句", "A planet within the habitable zone of its star could have surface temperatures that allow liquid water to exist.", "天文", "850"),
    ("heliopause", "太陽から吹き出す太陽風の圧力と、恒星間空間を満たす星間物質の圧力とがつり合う境界面。この境界を太陽圏(ヘリオスフィア)の外縁とみなし、その外側は恒星間空間とされる。", "名詞", "Beyond the heliopause, the solar wind's influence gives way to the surrounding interstellar medium.", "天文", "900"),
    ("helioseismology", "太陽の表面に現れる微小な振動(太陽内部を伝わる音波によって生じる)を精密に観測・解析することで、太陽内部の温度・密度・自転などの構造を調べる学問分野。地震学の手法を太陽に応用したことからこの名がある。", "名詞", "Helioseismology has revealed detailed information about the Sun's internal structure, including the depth of its convective zone.", "天文", "950"),
    ("heliosphere", "太陽から吹き出す太陽風の影響が及ぶ、太陽を取り囲む広大な空間領域。太陽系の惑星軌道をはるかに超えて広がり、その外縁はヘリオポーズと呼ばれる境界で恒星間空間と接している。", "名詞", "The heliosphere acts as a protective bubble that shields the solar system from much of the galactic cosmic radiation outside it.", "天文", "900"),
    ("helium flash", "太陽程度の質量を持つ恒星が赤色巨星段階の末期に、電子の縮退状態にある中心核でヘリウムの核融合(トリプルアルファ反応)が暴走的に点火し、極めて短時間に爆発的なエネルギーを放出する現象。", "名詞句", "The helium flash occurs when helium fusion ignites suddenly in the electron-degenerate core of a low-mass red giant star.", "天文", "930"),
    ("Hertzsprung-Russell diagram", "恒星の表面温度(またはスペクトル型)を横軸に、絶対等級(または光度)を縦軸にとって多数の恒星をプロットした図。主系列星・赤色巨星・白色矮星などの分布から恒星の進化段階を読み取ることができる。ヘルツシュプルング・ラッセル図(HR図)。", "名詞句", "On the Hertzsprung-Russell diagram, most stars, including the Sun, fall along a band called the main sequence.", "天文", "900"),
    ("Hill sphere", "ある天体(惑星など)が、より大きな中心天体(恒星など)の重力の影響下にありながらも、自らの重力によって衛星などの小天体を安定してとらえておける範囲を表す球状の領域。", "名詞句", "A moon must orbit within its planet's Hill sphere to remain gravitationally bound to it rather than being pulled away by the host star.", "天文", "930"),
    ("horizon problem", "宇宙の晴れ上がり時点で、互いに光や情報のやり取りが物理的に不可能だったはずの離れた領域が、観測される宇宙マイクロ波背景放射においてほぼ同じ温度を示しているのはなぜかという、標準ビッグバン理論では説明が難しい問題。", "名詞句", "The horizon problem asks how regions of the universe that could never have been in causal contact ended up at nearly the same temperature.", "天文", "970"),
    ("horizontal branch", "質量の小さい恒星が赤色巨星段階でヘリウムフラッシュを経た後にたどる進化段階。ヘルツシュプルング・ラッセル図上でほぼ水平に帯状に分布することからこの名がある。中心核でヘリウムを、その周りの殻で水素を核融合している。", "名詞句", "Stars on the horizontal branch are fusing helium in their cores after passing through the helium flash at the tip of the red giant branch.", "天文", "950"),
    ("hot Jupiter", "木星ほどの質量を持ちながら、中心星のごく近く(水星よりも内側の軌道に相当する距離)を数日程度の短い周期で公転している、表面温度が非常に高いガス惑星。", "名詞句", "Hot Jupiters orbit so close to their host stars that a single year can last only a few Earth days.", "天文", "870"),
    ("Hubble constant", "現在の宇宙の膨張率を表す定数で、遠方銀河までの距離とその後退速度が比例するというハッブルの法則における比例定数。単位は一般に「km/s/Mpc(メガパーセクあたり秒速何km)」で表される。", "名詞句", "The Hubble constant tells us how fast the universe is currently expanding for every unit of distance between galaxies.", "天文", "910"),
    ("Hubble sequence", "銀河の視覚的形態(見た目の形)に基づいて、楕円銀河・レンズ状銀河・渦巻銀河・不規則銀河などに分類する体系。エドウィン・ハッブルが考案した「音叉図(チューニングフォーク図)」として知られる。", "名詞句", "In the Hubble sequence, galaxies are arranged along a tuning-fork diagram running from elliptical galaxies through lenticulars to spiral and barred spiral galaxies.", "天文", "930"),
    ("Hubble's law", "銀河までの距離が遠いほど、その銀河が地球から遠ざかる速度(後退速度)が比例して大きくなるという観測的法則。宇宙膨張の直接的な証拠とされる。ハッブルの法則。", "名詞句", "According to Hubble's law, a galaxy twice as far away is receding from us roughly twice as fast.", "天文", "900"),
    ("hydrostatic equilibrium", "恒星や惑星などの天体内部で、外向きに働く圧力(ガス圧や放射圧)と、内向きに働く自己重力とがつり合い、天体の形状が静的に保たれている状態。", "名詞句", "A main-sequence star maintains hydrostatic equilibrium because the outward pressure from its hot core balances the inward pull of gravity.", "天文", "930"),
    ("hypernova", "太陽質量の数十倍以上ある大質量星が起こす、通常の超新星をはるかに上回るエネルギーを放出する極めて明るい爆発現象。長時間継続型ガンマ線バーストの発生源の一つと考えられている。", "名詞", "The 1998 supernova SN 1998bw was recognized as the first hypernova after astronomers linked it to a gamma-ray burst.", "天文", "950"),
    ("instability strip", "HR図(恒星の明るさと表面温度の関係図)上で、恒星がケフェイド型変光星やこと座RR型変光星のように脈動を起こして明るさを周期的に変化させる、ほぼ縦に伸びた帯状の領域。", "名詞句", "When a star's evolutionary track crosses the instability strip, its outer layers begin to pulsate and its brightness varies periodically.", "天文", "970"),
    ("interferometry", "複数の望遠鏡で受信した電磁波(光や電波)を干渉させることで、単一の望遠鏡では得られない高い角分解能を実現する観測技術。", "名詞", "Radio astronomers use interferometry to combine signals from widely separated telescopes and achieve resolution far beyond that of any single dish.", "天文", "920"),
    ("Kelvin-Helmholtz mechanism", "恒星やガス惑星が自己重力によってゆっくり収縮する際に、重力エネルギーの一部が熱に変換されて放射されるしくみ。原始星が核融合を始める前の主なエネルギー源とされる。", "名詞句", "Before nuclear fusion ignites in its core, a young star shines mainly through energy released by the Kelvin-Helmholtz mechanism.", "天文", "950"),
    ("Kuiper belt object", "海王星より外側、太陽から約30〜50天文単位の領域に広がる「カイパーベルト」に存在する氷天体の総称。冥王星もその代表例の一つとされる。", "名詞句", "Pluto is the largest known Kuiper belt object, but thousands of smaller icy bodies share that same distant region of the solar system.", "天文", "870"),
    ("Lambda-CDM model", "宇宙の進化を説明する現在の標準的な宇宙論モデル。宇宙定数Λ(ダークエネルギーに相当)と、光速に比べて遅い速度で運動する冷たい暗黒物質(CDM)を主成分として含む。", "名詞句", "The Lambda-CDM model successfully explains the cosmic microwave background, the large-scale structure of the universe, and the accelerating cosmic expansion.", "天文", "950"),
    ("large-scale structure", "銀河団・超銀河団・フィラメント状構造・ボイド(超空洞)などが織りなす、宇宙全体に広がる銀河分布の網目状パターン。「宇宙の大規模構造」とも呼ばれる。", "名詞句", "Galaxy redshift surveys have revealed that the large-scale structure of the universe resembles a cosmic web of filaments, walls, and voids.", "天文", "920"),
    ("late heavy bombardment", "太陽系形成初期、約41億〜38億年前ごろに、月や地球型惑星が小惑星・彗星による衝突を集中的に受けたとされる時代。「後期重爆撃期」。", "名詞句", "Evidence for the late heavy bombardment comes largely from the ages of impact melt rocks collected during the Apollo missions to the Moon.", "天文", "920"),
    ("Local Group", "天の川銀河(銀河系)とアンドロメダ銀河(M31)を中心に、さんかく座銀河(M33)や多数の矮小銀河を含む、直径約1000万光年程度の銀河の集団。", "固有名詞", "The Milky Way and the Andromeda Galaxy are the two most massive members of the Local Group.", "天文", "900"),
    ("main-sequence turnoff", "星団のHR図上で、主系列星が水素核融合を終えて主系列から外れ始める境目の点。星団の年齢を推定する際の重要な指標となる。", "名詞句", "By locating the main-sequence turnoff on a star cluster's HR diagram, astronomers can estimate how old the cluster is.", "天文", "950"),
    ("mass-luminosity relation", "主系列星において、恒星の質量が大きいほどその光度(明るさ)が急激に大きくなるという関係。おおよそ光度は質量のおよそ3.5乗に比例する。", "名詞句", "The mass-luminosity relation shows that a star twice as massive as the Sun can be roughly ten times more luminous.", "天文", "930"),
    ("Oort cloud", "太陽系の最も外側、太陽から数千〜10万天文単位にも及ぶ球殻状の領域に、無数の氷天体が分布していると考えられている仮説上の領域。長周期彗星の起源とされる。", "名詞句", "Long-period comets are thought to originate in the distant, spherical region known as the Oort cloud.", "天文", "870"),
    ("pair-instability supernova", "太陽質量のおよそ130〜250倍という極めて大質量な星の中心核で、高エネルギーのガンマ線光子が電子・陽電子対を生成することで圧力が急減し、星全体が中性子星やブラックホールを残さず完全に吹き飛ばされる特殊な超新星爆発。", "名詞句", "In a pair-instability supernova, the star is completely disrupted by a thermonuclear explosion and leaves no compact remnant behind.", "天文", "980"),
    ("panspermia", "生命の起源(あるいはその材料となる有機物・微生物)が地球上で独自に発生したのではなく、隕石や彗星などを介して宇宙空間から運ばれてきたとする仮説。", "名詞", "Panspermia proposes that microbial life, or at least its chemical building blocks, could have been transported between planets by comets and asteroids.", "天文", "900"),
    ("photometric redshift", "分光観測(スペクトル分析)を行わず、複数の波長帯での明るさ(測光データ)だけから統計的・モデル的に推定した銀河の赤方偏移(見かけの後退速度)。", "名詞句", "Large galaxy surveys often rely on photometric redshifts because obtaining a spectrum for every single galaxy would take far too much telescope time.", "天文", "930"),
    ("photometry", "天体が放つ光の明るさを、望遠鏡と検出器を用いて定量的に測定する観測手法。", "名詞", "Photometry allows astronomers to track subtle changes in a star's brightness over time, such as those caused by an orbiting planet.", "天文", "870"),
    ("photosphere", "太陽や恒星において、光が直接宇宙空間へ放出される、目に見える「表面」に相当する薄いガス層。", "名詞", "Most of the sunlight we see comes from the photosphere, a thin layer only a few hundred kilometers thick.", "天文", "870"),
    ("planetary differentiation", "惑星が形成される過程で、内部が融解した際に密度の高い金属成分が中心に沈み、密度の低い岩石成分が外側に浮くことで、核・マントル・地殻のような層構造が作られる過程。", "名詞句", "Planetary differentiation explains why Earth has a dense iron-nickel core surrounded by a lighter rocky mantle and crust.", "天文", "900"),
    ("planetary migration", "惑星が誕生した際の軌道位置から、原始惑星系円盤のガスとの重力相互作用や、他の惑星・微惑星との重力的な影響によって、現在の軌道位置まで移動する過程。", "名詞句", "Planetary migration is now widely used to explain why so many known exoplanets, called hot Jupiters, orbit extremely close to their host stars.", "天文", "920"),
    ("planetary transit", "系外惑星が地球から見て主星(中心星)の前を横切ることで、主星の明るさがわずかに周期的に減少する現象。この減光を観測することで惑星の存在を検出する手法(トランジット法)としても用いられる。", "名詞句", "Astronomers first confirmed a planetary transit in 1999, when the star HD 209458 dimmed slightly as its planet passed in front of it.", "天文", "880"),
    ("planetesimal", "原始惑星系円盤の中でちりやガスが集積してできた、直径数kmから数百kmほどの小天体。これらが衝突・合体を繰り返すことで、より大きな原始惑星や惑星が形成されると考えられている。", "名詞", "Over millions of years, countless planetesimals collided and merged within the young solar system to build up the terrestrial planets.", "天文", "900"),
    ("proton-proton chain", "太陽のような比較的軽い恒星の中心核で主に働く核融合反応の連鎖で、水素原子核(陽子)どうしが段階的に融合し、最終的にヘリウム原子核を作り出す過程。", "名詞句", "The proton-proton chain is the dominant source of energy in stars with masses similar to or less than that of the Sun.", "天文", "930"),
    ("protoplanet", "微惑星どうしの衝突・合体が進んだ結果できた、月から火星程度の大きさを持つ、惑星形成の途上にある天体。", "名詞", "Many scientists believe the Moon formed when a Mars-sized protoplanet collided with the early Earth.", "天文", "900"),
    ("protostar", "分子雲の中で自己重力によってガスとちりが収縮している段階にあり、まだ中心核で水素の核融合反応が始まっていない、誕生途上の星。", "名詞", "A protostar is heated mainly by the gravitational energy released as it slowly contracts, not yet by nuclear fusion.", "天文", "870"),
    ("r-process", "中性子星どうしの合体や超新星爆発などの環境で、原子核が中性子を非常に速いペースで次々に捕獲することで、鉄より重い元素(金・プラチナ・ウランなど)を作り出す元素合成過程。「速い中性子捕獲過程」。", "名詞句", "The r-process is responsible for producing roughly half of all elements heavier than iron, including gold and uranium.", "天文", "950"),
    ("radial velocity method", "恒星が、その周りを公転する惑星の重力によってわずかに揺れ動く際に生じる、恒星のスペクトル線のドップラー偏移(視線速度の周期的変化)を検出することで、系外惑星の存在を明らかにする観測手法。", "名詞句", "The radial velocity method led to the discovery of 51 Pegasi b in 1995, the first exoplanet ever found around a Sun-like star.", "天文", "900"),
    ("radiative zone", "恒星内部において、中心核で生成されたエネルギーが対流ではなく光子の吸収・再放出(輻射拡散)によって外側へ運ばれる層。", "名詞句", "In the Sun, energy generated in the core takes hundreds of thousands of years to random-walk its way out through the radiative zone.", "天文", "910"),
    ("ram pressure stripping", "銀河団の中を運動する銀河が、銀河団内を満たす高温の銀河団内ガス(intracluster medium)から受ける「風圧」によって、自らが持つガスを剥ぎ取られてしまう現象。", "名詞句", "Ram pressure stripping can remove most of a galaxy's cold gas within a few hundred million years of it falling into a galaxy cluster.", "天文", "970"),
    ("reionization", "宇宙初期に中性水素でほぼ満たされていた宇宙空間が、最初期の星や銀河・クェーサーからの紫外線によって再びイオン化されていった時代・過程。", "名詞", "Reionization is thought to have been largely completed by about one billion years after the Big Bang.", "天文", "930"),
    ("Roche limit", "ある天体が別の天体に近づきすぎたとき、後者の潮汐力が前者自身の自己重力を上回り、前者が構造的にばらばらに破壊されてしまう限界となる距離。", "名詞句", "A comet that passes within a planet's Roche limit can be torn apart by tidal forces before it ever reaches the surface.", "天文", "910"),
    ("s-process", "主に漸近巨星分枝(AGB)星の内部で、原子核が中性子を比較的ゆっくりとしたペースで捕獲し、その間にベータ崩壊を挟みながら鉄より重い元素を作り出していく元素合成過程。「遅い中性子捕獲過程」。", "名詞句", "The s-process takes place slowly enough that unstable nuclei usually have time to undergo beta decay before capturing another neutron.", "天文", "950"),
    ("Sagittarius A*", "天の川銀河の中心に位置する、太陽質量の約400万倍という超大質量ブラックホールに付随する電波源。", "固有名詞", "Sagittarius A* sits at the very center of the Milky Way, roughly 26,000 light-years from Earth.", "天文", "900"),
    ("satellite galaxy", "より質量の大きい主銀河の重力に束縛され、その周りを公転している比較的小さな銀河。", "名詞句", "The Large and Small Magellanic Clouds are the two most famous satellite galaxies of the Milky Way.", "天文", "880"),
    ("solar flare", "太陽表面の黒点付近に蓄積された磁気エネルギーが、磁力線のつなぎ替え(磁気リコネクション)によって急激に解放されることで生じる、突発的で激しい増光現象。", "名詞句", "A powerful solar flare can release as much energy as billions of hydrogen bombs in just a few minutes.", "天文", "880"),
    ("solar prominence", "太陽の彩層からコロナにかけて突き出すように存在する、磁力線に支えられた比較的低温・高密度のプラズマの構造物。太陽の縁でループ状やアーチ状に見える。", "名詞句", "A solar prominence can hang suspended above the Sun's surface for weeks, held up by the star's magnetic field.", "天文", "900"),
    ("solar wind", "太陽のコロナから絶えず吹き出している、陽子・電子などの荷電粒子の超音速の流れ。", "名詞句", "The solar wind constantly streams outward from the Sun at speeds of several hundred kilometers per second.", "天文", "850"),
    ("spectrograph", "天体からの光をプリズムや回折格子などで波長ごとに分解し、そのスペクトル(波長ごとの明るさの分布)を記録するための観測装置。", "名詞", "A spectrograph splits incoming starlight into its component wavelengths, revealing dark absorption lines that identify the elements present.", "天文", "880"),
    ("spiral arm", "渦巻銀河の円盤部に見られる、若い星やガス・ちりが集中して明るく見える、渦を巻くように伸びた腕状の構造。", "名詞句", "The bright blue stars that trace out a galaxy's spiral arms are young and massive, since such stars burn out long before they can drift far from where they formed.", "天文", "880"),
    ("starburst galaxy", "銀河同士の衝突・合体や重力的な相互作用などをきっかけに、通常よりもはるかに高い割合で爆発的に星が誕生している銀河。", "名詞句", "Starburst galaxies can form new stars at a rate tens or even hundreds of times faster than a typical spiral galaxy like the Milky Way.", "天文", "930"),
    ("stellar nucleosynthesis", "恒星内部の核融合反応によって、水素やヘリウムよりも重い元素が次々と作り出されていく過程の総称。", "名詞句", "Stellar nucleosynthesis inside massive stars gradually builds up elements from carbon and oxygen all the way up to iron.", "天文", "930"),
    ("stellar population", "恒星をその年齢・金属量(重元素の含有量)・銀河内での分布や運動といった性質に基づいて分類したグループ。主に若く金属に富む「種族I」と、古く金属に乏しい「種族II」に大別される。", "名詞句", "Young, metal-rich stars found in a galaxy's spiral arms are classified as Population I, while old, metal-poor stars in globular clusters belong to Population II.", "天文", "930"),
    ("stellar wind", "太陽風と同様に、太陽以外の恒星からも絶えず放出されている、荷電粒子やガスの流れの総称。", "名詞句", "The stellar wind from a massive, hot star can be millions of times stronger than the Sun's own solar wind.", "天文", "870"),
    ("sunspot cycle (astronomy)", "(無線通信への影響ではなく、天文学・太陽物理学における現象として)太陽表面に現れる黒点の数が、平均して約11年の周期で増減を繰り返す太陽活動の周期。", "名詞句", "The sunspot cycle runs for about eleven years on average, from one solar minimum to the next.", "天文", "870"),
    ("super-Earth", "質量が地球より大きいものの、天王星・海王星のような巨大氷惑星よりは小さい範囲(おおよそ地球の1〜10倍程度)にある系外惑星の総称。", "名詞", "A super-Earth is defined purely by mass, so the term says nothing about whether such a planet is rocky, ocean-covered, or blanketed in a thick atmosphere.", "天文", "870"),
    ("supermassive black hole", "太陽質量の数十万倍から数百億倍という桁外れの質量を持つブラックホールで、天の川銀河を含むほとんどの大きな銀河の中心に存在すると考えられている。", "名詞句", "Nearly every large galaxy, including our own Milky Way, is thought to harbor a supermassive black hole at its center.", "天文", "900"),
    ("surface of last scattering", "宇宙が誕生してから約38万年後、それまで自由に飛び交っていた光子が電子・陽子と結びつき中性の原子ができたことで、光子が物質に散乱されずに直進できるようになった宇宙論的な「面」。宇宙マイクロ波背景放射として現在観測される光は、この面から届いたものである。", "名詞句", "The cosmic microwave background is essentially a snapshot of the universe's surface of last scattering, dating back roughly 380,000 years after the Big Bang.", "天文", "950"),
    ("tidal disruption event", "恒星がたまたま銀河中心の超大質量ブラックホールに接近しすぎた際、潮汐力によって恒星がばらばらに引き裂かれ、その破片の一部が明るいフレアとして観測される現象。", "名詞句", "A tidal disruption event occurs when a star wanders too close to a supermassive black hole and is torn apart by tidal forces.", "天文", "950"),
    ("tidal heating", "衛星や惑星が、公転する天体との重力的な相互作用(潮汐力)によって内部が周期的に伸び縮みさせられ、その摩擦によって内部が加熱される現象。", "名詞句", "Tidal heating keeps Jupiter's moon Io the most volcanically active body in the entire solar system.", "天文", "900"),
    ("tidal locking", "衛星や惑星が、公転する天体からの潮汐力によって自転周期と公転周期が一致するようになり、常に同じ面を相手に向け続けるようになる現象。", "名詞句", "The Moon is tidally locked to Earth, which is why we always see the same side of it from the ground.", "天文", "870"),
    ("triple-alpha process", "恒星が赤色巨星の段階に達した際、中心核でヘリウム原子核(アルファ粒子)が3個結合して炭素原子核を作り出す核融合反応。", "名詞句", "The triple-alpha process only becomes possible once a star's core has contracted and heated enough to fuse helium into carbon.", "天文", "950"),
    ("Type Ia supernova", "連星系の中で白色矮星が伴星から物質を受け取って質量を増やし、限界質量(チャンドラセカール限界)に近づいた結果、暴走的な核融合反応によって星全体が爆発的に破壊される現象。明るさがほぼ一定であるため、宇宙の距離を測る「標準光源」として使われる。", "名詞句", "Because Type Ia supernovae reach nearly the same peak brightness every time, astronomers use them as standard candles to measure vast cosmic distances.", "天文", "920"),
    ("Type II supernova", "太陽の8倍以上の質量を持つ大質量星が、中心核の核融合燃料を使い果たして重力崩壊を起こすことで生じる超新星爆発。スペクトルに水素の吸収線が見られることが特徴。", "名詞句", "A Type II supernova occurs when a massive star's core runs out of nuclear fuel and collapses under its own gravity.", "天文", "920"),
    ("very long baseline interferometry", "地球上の遠く離れた複数の電波望遠鏡で同時に観測を行い、原子時計で記録した信号を後から組み合わせることで、単一の望遠鏡では実現できない極めて高い角分解能を得る観測技術。", "名詞句", "Very long baseline interferometry combines signals from radio telescopes scattered across different continents to achieve extraordinarily fine angular resolution.", "天文", "950"),
    ("Virgo Cluster", "おとめ座の方向、地球から約5000万〜6000万光年の距離にある、数千個の銀河からなる巨大な銀河団。局所銀河群が属する「おとめ座超銀河団」の中心を成す。", "固有名詞", "The Virgo Cluster lies at the heart of the larger Virgo Supercluster, the same supercluster that contains our own Local Group.", "天文", "910"),
    ("zero-age main sequence", "恒星が重力収縮を終えて中心核で安定的な水素の核融合を開始した直後、まだ内部の化学組成がほとんど変化していない時点でのHR図上の位置。", "名詞句", "A star first joins the main sequence at its zero-age main sequence position, before any nuclear burning has altered its internal composition.", "天文", "950"),]


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
