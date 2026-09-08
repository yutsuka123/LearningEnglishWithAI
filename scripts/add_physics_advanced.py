# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""物理ドメインの大学専門課程レベルへの深化(2026-09-08・B24タスク・
authored by Claude、3並列サブエージェントで分野を分担しドラフト→WebSearchで
歴史的事実(人名・年代)を検証)。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_physics_advanced.py
仕上げ: relevel.pyは実行しない(他のB24バッチと同じ理由。既存の
H900/H990/H990Pリストに未対応でDOMAIN_BASEに一律で潰されるため)。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ('generalized coordinates', '力学系の配置を過不足なく指定する、束縛条件に応じて自由に選べる独立変数の組。デカルト座標である必要はなく、角度や長さなど系の対称性に合わせて選ぶことで運動方程式を簡単にできる。一般化座標。', '名詞句', 'For a pendulum, the angle from the vertical is a natural choice of generalized coordinate.', '物理', '850'),
    ('virtual work', '実際には起こらない、束縛条件と矛盾しない微小な仮想変位に対して力がなす仕事。静力学において、釣り合いの状態にある系では、任意の仮想変位に対する仮想仕事の総和がゼロになるという原理(仮想仕事の原理)に用いられる。', '名詞句', 'The principle of virtual work states that a system is in equilibrium if the virtual work done by all forces vanishes for any virtual displacement.', '物理', '860'),
    ('Poisson bracket', 'ハミルトン力学において、位相空間上の2つの物理量(位置と運動量の関数)から新しい物理量を作る演算。ある量のポアソン括弧がハミルトニアンとの間でゼロになるとき、その量は保存量であることを示す。量子力学における交換関係の古典的な対応物ともされる。', '名詞句', 'The time evolution of any observable can be written using its Poisson bracket with the Hamiltonian.', '物理', '950'),
    ('action (physics)', '系がある経路をたどる際の、ラグランジアンを時間について積分した量。実際に系がたどる経路は、この作用の値を停留(多くの場合は最小)にする経路であるという「最小作用の原理」の中心となる量。単位はエネルギー×時間。', '名詞', 'The principle of least action states that a system evolves along the path that makes the action stationary.', '物理', '900'),
    ('Noether current', 'ネーターの定理において、連続的な対称性から導かれる、時間的・空間的に保存される流れ(カレント)。その時間成分を空間全体で積分すると、対応する保存量(エネルギーや電荷など)が得られる。場の理論で用いられる概念。', '名詞句', 'The Noether current associated with time-translation symmetry is directly related to the energy density of the field.', '物理', '940'),
    ('Euler-Lagrange equation', '汎関数(ラグランジアンの時間積分である作用)を停留させる関数(実際の運動の軌道)が満たすべき微分方程式。変分法の基本方程式であり、これを力学系のラグランジアンに適用すると、ニュートンの運動方程式と等価な運動方程式が得られる。', '名詞句', 'Applying the Euler-Lagrange equation to the Lagrangian of a simple pendulum reproduces its familiar equation of motion.', '物理', '870'),
    ('normal coordinates', '複数の質点や振動子が互いに結合した系(連成振動系)において、運動方程式が互いに独立な単振動の式に分離されるように選んだ一般化座標。これを用いると、複雑に絡み合った振動を、独立ないくつかの基準振動(基準モード)の重ね合わせとして記述できる。', '名詞句', 'By switching to normal coordinates, the coupled equations of motion for two connected pendulums decouple into two independent oscillators.', '物理', '920'),
    ('precession', '自転する物体の回転軸自体が、外力によるトルクを受けて、円錐を描くようにゆっくりと向きを変えていく運動。独楽(こま)の首振り運動や、地球の自転軸が約2万6千年周期で向きを変える現象などが代表例。歳差(運動)。', '名詞', 'A spinning top exhibits precession, slowly tracing out a cone as gravity exerts a torque on its axis.', '物理', '860'),
    ("Hamilton's equations", 'ハミルトニアンを用いて力学系の時間発展を記述する、位置と運動量それぞれについての1階連立微分方程式。ラグランジュ形式の2階微分方程式(オイラー・ラグランジュ方程式)と等価だが、位相空間上での運動を扱いやすい形で表す。正準方程式。', '名詞句', "Hamilton's equations describe how the position and momentum of a system evolve together in phase space.", '物理', '870'),
    ('holonomic constraint', '系の座標とおそらく時間のみの関係式として表せる束縛条件。速度を含まず、位置座標間の等式関係だけで表せるため、その関係式を用いて独立な一般化座標の数を減らすことができる。ホロノミック拘束。', '名詞句', 'A bead constrained to slide along a fixed wire is subject to a holonomic constraint that can be written purely in terms of position.', '物理', '900'),
    ("D'Alembert's principle", '束縛力による仮想仕事が常にゼロになることを利用し、動力学の問題を、慣性力を導入することで見かけ上の静力学の釣り合い問題として扱う原理。ニュートンの運動方程式を仮想仕事の原理と組み合わせた形で表したものとされ、ラグランジュ力学を導く出発点の一つとなった。', '名詞句', "D'Alembert's principle treats the term mass times acceleration as an inertial force, turning a dynamics problem into an equivalent statics problem.", '物理', '880'),
    ('canonical transformation', 'ハミルトン力学において、位置と運動量の組を別の位置と運動量の組へ変換する際、ハミルトンの正準方程式の形を保つような特別な変換。作用・角変数への変換など、複雑な問題を解きやすい座標系に移すために用いられる。', '名詞句', "A canonical transformation can map a complicated Hamiltonian into a much simpler form while preserving the structure of Hamilton's equations.", '物理', '930'),
    ('generalized momentum', 'ラグランジアンを、対応する一般化座標の時間微分(一般化速度)で偏微分して定義される量。デカルト座標に対しては通常の運動量(質量×速度)に一致するが、角度のような座標に対しては角運動量に対応するなど、座標の選び方に応じて意味が変わる。共役運動量。', '名詞句', 'The generalized momentum conjugate to an angular coordinate turns out to be the corresponding angular momentum.', '物理', '890'),
    ('Coriolis force', '回転する座標系(非慣性系)の中で運動する物体に対して、その運動方向と回転軸の両方に垂直な向きに働く見かけ上の力。地球の自転する座標系で大気や海流の運動を考える際に現れ、台風の渦の向きなどに影響する。コリオリ力。', '名詞句', 'The Coriolis force deflects moving air to the right in the Northern Hemisphere and to the left in the Southern Hemisphere.', '物理', '850'),
    ('Biot-Savart law', '電流が流れる導線の微小部分が、周囲の各点に作る磁場を与える法則。導線全体が作る磁場は、この法則を導線に沿って積分することで求められる。任意の形状の導線が作る磁場を計算する基本法則で、アンペールの法則と並ぶ静磁場の基礎法則。', '名詞句', 'The Biot-Savart law gives the magnetic field created by a small segment of current-carrying wire at any point in space.', '物理', '860'),
    ('Lorentz force', '電場と磁場の中を運動する荷電粒子が受ける力。電場による力(電荷×電場)と、磁場による力(電荷×速度と磁場の外積)の和として表される。電磁気学における力の法則の中心的な式。', '名詞句', 'The Lorentz force causes a charged particle moving through a magnetic field to travel in a circular or helical path.', '物理', '850'),
    ("Lenz's law", '電磁誘導によって導体に生じる誘導電流の向きは、その誘導電流が作る磁場が、もとの磁場の変化を打ち消す向きになる、という法則。ファラデーの電磁誘導の法則における起電力の符号(向き)を定める規則であり、エネルギー保存則の帰結でもある。', '名詞句', "According to Lenz's law, the induced current always flows in a direction that opposes the change in magnetic flux that created it.", '物理', '850'),
    ('electromotive force', '電池や発電機などが、回路に電流を流し続けるために単位電荷あたりに与えるエネルギー。電圧と同じ単位(ボルト)で表されるが、回路の抵抗による電圧降下とは区別され、電流を生み出す「源」としての働きを表す。起電力(EMF)。', '名詞句', 'The electromotive force of a battery represents the energy it supplies to each unit of charge that passes through it.', '物理', '860'),
    ('self-inductance', 'コイルなどの導体に流れる電流自身が変化したとき、その変化を妨げる向きに、その導体自身に生じる誘導起電力の大きさを表す係数。電流の時間変化率に比例した起電力が生じ、その比例定数を自己インダクタンスと呼ぶ。単位はヘンリー。', '名詞句', 'The self-inductance of a coil determines how strongly it opposes a change in the current flowing through it.', '物理', '880'),
    ('mutual inductance', '2つの回路(コイル)の一方を流れる電流が変化したとき、もう一方の回路に誘導される起電力の大きさを表す係数。変圧器はこの相互インダクタンスを利用して、一次側コイルの交流電流から二次側コイルに電圧を発生させる。単位はヘンリー。', '名詞句', "Mutual inductance is the physical principle that allows a transformer's primary coil to induce a voltage in its secondary coil.", '物理', '890'),
    ('displacement current', 'コンデンサの充電・放電時のように、実際の電荷の移動(伝導電流)がない空間でも、電場が時間変化することで、あたかも電流が流れているかのように磁場を作り出す効果。マクスウェルがアンペールの法則を修正するために導入した項。', '名詞句', 'Maxwell introduced the displacement current to explain how a changing electric field between capacitor plates produces a magnetic field.', '物理', '870'),
    ('continuity equation (electromagnetism)', '電荷や質量、確率などの保存される量について、ある領域内の量の時間変化が、その境界を通って出入りする流れ(電流密度など)の収支と等しくなることを表す微分方程式。電磁気学では電荷保存則を局所的な形で表現するために用いられる。', '名詞句', 'The continuity equation expresses charge conservation as a local relationship between charge density and current density.', '物理', '900'),
    ('boundary condition (electromagnetism)', '異なる媒質(誘電体や導体など)の境界面において、電場や磁場の各成分(境界に平行な成分・垂直な成分)が満たすべき関係式。マクスウェル方程式を積分形で境界面に適用することで導かれ、異なる媒質にまたがる電磁場の問題を解く際に必須となる。(一般的な数学用語としての「境界条件」とは別の、電磁気学特有の具体的な条件を指す)', '名詞句', 'At the boundary between two dielectrics, the tangential component of the electric field must be continuous.', '物理', '910'),
    ('eddy current', '導体内部を貫く磁束が時間変化することで、導体内部に渦を巻くように誘導される電流。電磁誘導によってジュール熱を発生させエネルギーを消費するため、変圧器の鉄心などでは損失(渦電流損)の原因となる一方、電磁ブレーキや誘導加熱にも応用される。', '名詞句', "Eddy currents induced in a metal plate create a braking force that opposes the plate's motion through a magnetic field.", '物理', '860'),
    ('ferromagnetism', '鉄・コバルト・ニッケルなどの物質が持つ、外部磁場がなくても物質内部で多数の電子スピンの向きがそろい、強い磁化を示す性質。外部磁場を取り去った後も磁化が残ることがあり(永久磁石)、キュリー温度以上に加熱するとこの性質が失われる。', '名詞', 'Ferromagnetism allows materials like iron to be magnetized and to retain a strong magnetic field even after the external field is removed.', '物理', '870'),
    ('diamagnetism', '外部から磁場をかけると、電磁誘導によって、その磁場を打ち消す(反発する)向きにわずかに磁化する性質。強磁性や常磁性のような電子スピンの整列によるものではなく、あらゆる物質が本質的に持つ弱い性質で、超伝導体はこの性質を完全な形で示す(マイスナー効果)。', '名詞', 'Diamagnetism causes a material to be weakly repelled by an external magnetic field.', '物理', '880'),
    ('paramagnetism', '物質中に、向きがそろっていない電子スピン(磁気モーメント)が存在し、外部から磁場をかけるとその磁場の向きにわずかに磁化する性質。磁場を取り去ると熱運動によって向きが再びばらばらになり、磁化も消える。強磁性のような自発磁化は持たない。', '名詞', 'Paramagnetism causes a material to be weakly attracted toward an external magnetic field, unlike diamagnetic materials.', '物理', '880'),
    ('magnetic domain', '強磁性体の内部で、多数の原子スピンの向きがそろって同じ方向を向いている微小な領域。隣り合う磁区どうしは互いに異なる向きを向いていることが多く、外部磁場をかけると磁場の向きに近い磁区が拡大することで、物質全体としての磁化が現れる。', '名詞句', 'Even an unmagnetized piece of iron contains many magnetic domains, each magnetized in a different direction.', '物理', '880'),
    ('Curie temperature', '強磁性体を加熱していったとき、熱運動によってスピンの配列が完全に乱され、強磁性を失って常磁性に転じる臨界温度。物質固有の値を持ち、鉄は約770℃、ニッケルは約358℃とされる。キュリー点。', '名詞句', 'Above the Curie temperature, a ferromagnetic material loses its spontaneous magnetization and behaves as a paramagnet.', '物理', '890'),
    ('magnetic hysteresis', '強磁性体に外部磁場を加えて磁化し、その後磁場を減少させても、磁化が磁場の変化に対して遅れて追随し、もとの経路を通らずに履歴が残る現象。磁化の大きさを外部磁場に対してプロットすると、ループ状の曲線(ヒステリシスループ)を描く。(遅延一般を指す既存語「hysteresis」とは異なり、強磁性体の磁化過程に特有のこの現象を指す)', '名詞句', 'A plot of magnetization against applied field for a ferromagnet traces out a loop, a phenomenon known as magnetic hysteresis.', '物理', '890'),
    ('standing wave', '互いに逆向きに進む同じ波長の波が重なり合うことで生じる、時間が経っても振動の腹と節の位置が空間的に移動しない波。両端を固定した弦の振動や、共振空洞・伝送線路内で反射波と入射波が干渉することで生じる。定在波。', '名詞句', 'Reflections at the closed end of a transmission line combine with the incoming wave to form a standing wave.', '物理', '860'),
    ('group velocity', '波長のわずかに異なる複数の波が重なり合ってできる「波束(波のかたまり)」全体が、空間を伝わっていく速度。個々の波の山や谷が進む速さである位相速度とは異なり、波束の形(エネルギーや情報)が実際に伝わる速さを表す。', '名詞句', 'In a dispersive medium, the group velocity of a wave packet can differ significantly from its phase velocity.', '物理', '920'),
    ('phase velocity', 'ある波の、位相が一定の点(たとえば波の山や谷)が空間を進んでいく速度。角周波数を波数で割った値として定義される。分散のある媒質中では、波長(周波数)によって位相速度が異なり、群速度とは一般に異なる値になる。', '名詞句', 'The phase velocity of a wave is found by dividing its angular frequency by its wave number.', '物理', '910'),
    ('dispersion relation', '波の角周波数と波数(あるいは波長)との間の関係式。真空中の光のように角周波数が波数に比例する場合は「分散がない」といい、関係が比例からずれる場合は媒質や系に「分散がある」という。群速度や位相速度は、この関係式から導かれる。', '名詞句', 'The dispersion relation of a wave describes how its angular frequency depends on its wave number.', '物理', '930'),
    ('skin effect', '導体に交流電流を流したとき、電流密度が導体の表面付近に集中し、内部ほど電流が流れにくくなる現象。周波数が高いほど、電流が集中する表面付近の層(表皮深さ)が薄くなり、実効的な導体の断面積が減ることで交流抵抗が増加する。', '名詞句', 'The skin effect causes high-frequency current to flow mainly near the surface of a conductor, increasing its effective resistance.', '物理', '900'),
    ('waveguide', '内部が中空または誘電体で満たされた金属製の管などを用いて、マイクロ波やミリ波といった高周波の電磁波を、外部に漏らさずに特定の方向へ効率よく伝送する構造。管の断面の形状や寸法によって、伝わることができる電磁波のモードや周波数帯が決まる。', '名詞', 'A rectangular waveguide confines microwave energy and guides it from a transmitter to an antenna with minimal loss.', '物理', '900'),
    ('multipole expansion', '電荷や電流の分布が作る電場・磁場を、観測点が分布から十分離れている場合に、単極子・双極子・四重極子…という項の級数として近似的に表す数学的手法。観測点が遠いほど、より低次の項(特に双極子項)が支配的になる。', '名詞句', 'A multipole expansion approximates the potential of a complicated charge distribution as a sum of monopole, dipole, quadrupole, and higher-order terms.', '物理', '960'),
    ('retarded potential', '電荷や電流の分布が変化したとき、その変化の影響が光速で有限の時間をかけて空間を伝わることを考慮した電位・ベクトルポテンシャル。観測点でのポテンシャルは、電荷分布の「現在」の状態ではなく、光がその距離を伝わるのにかかる時間だけ過去の状態(遅延時刻)によって決まる。', '名詞句', 'The retarded potential at a point depends on the state of the charge distribution at an earlier time, delayed by the time light takes to travel that distance.', '物理', '980'),
    ('vector potential', '磁場を、その回転(curl)として表すことができる補助的なベクトル量。磁場には湧き出し(単磁極)が存在しないため、常にこのようなベクトルポテンシャルを用いて表すことができ、電磁気学の様々な計算を見通しよくする。量子力学ではアハラノフ・ボーム効果を通じて、それ自体に物理的な意味があることが示されている。', '名詞句', 'The magnetic field can always be written as the curl of a vector potential, since magnetic field lines have no beginning or end.', '物理', '940'),
    ('electric dipole moment', '大きさが等しく符号が反対の2つの電荷が、微小な距離だけ離れて対になっている系(電気双極子)の、電荷の偏りの大きさと向きを表すベクトル量。電荷の大きさと、正負の電荷を結ぶ距離ベクトルの積として定義され、極性分子や多重極展開の基本的な構成要素となる。', '名詞句', 'A water molecule has a permanent electric dipole moment because its oxygen and hydrogen atoms share electrons unequally.', '物理', '900'),
    ('light', '目に見える電磁波、あるいはより広く、赤外線・紫外線なども含む電磁波のうち、物を照らし、見ることを可能にするもの。光。', '名詞', 'Light travels much faster than sound, which is why we see lightning before we hear thunder.', '物理', '300'),
    ('sound', '物体の振動が空気などの媒質を伝わり、耳(鼓膜)を振動させることで知覚される現象。真空中は伝わらず、必ず空気・水・固体などの媒質を必要とする。音。', '名詞', 'Sound cannot travel through the vacuum of space because there is no medium for it to move through.', '物理', '300'),
    ('motion', '物体の位置が時間とともに変化すること。物理学では、力と運動の関係を扱うニュートンの運動の法則など、力学の中心的な研究対象となる基本概念。運動。', '名詞', "Newton's laws of motion describe how the motion of an object changes in response to the forces acting on it.", '物理', '350'),
    ('weight (physics)', '物体に働く重力の大きさを表す力。単位はニュートン(N)で表され、物体そのものが持つ量である質量(単位キログラム)とは区別される。同じ物体でも、月面など重力の弱い場所では重さは小さくなるが、質量は変わらない。(既存の「weight」=AI分野のパラメータの重み、とは別の力学的な意味)', '名詞', "An astronaut's weight on the Moon is much less than on Earth, even though their mass stays exactly the same.", '物理', '400'),
    ('vacuum (physics)', '物質(空気などの気体分子)がほとんど、あるいはまったく存在しない空間。完全な真空は理想的な概念であり、実際には人工的に作られた真空も、わずかに気体分子が残っている。宇宙空間はほぼ真空に近い状態にある。(既存の「vacuum」=掃除機をかける、とは別の物理学上の意味)', '名詞', 'Sound cannot travel through a vacuum because there are no particles to carry the vibration.', '物理', '450'),
    ('electric charge', '物質が持つ、電気的な現象を引き起こす基本的な性質を表す量。正の電荷と負の電荷があり、同符号どうしは反発し、異符号どうしは引き合う。単位はクーロン(C)。電子は負の電荷を、陽子は正の電荷を持つ。', '名詞句', 'Two objects with the same electric charge repel each other, while objects with opposite charges attract.', '物理', '450'),
    ('magnetic force', '磁石や、電流が流れる導線どうしの間で働く、引き合う、または反発し合う力。磁石のN極どうし・S極どうしは反発し、異なる極どうしは引き合う。方位磁針が北を指すのも、地球自体が持つ磁力によるもの。', '名詞句', 'The magnetic force between two magnets grows weaker as the distance between them increases.', '物理', '450'),
    ('static electricity', '物体の表面に電荷が偏って蓄積し、その電荷が移動せずにとどまっている状態の電気。異なる材質の物をこすり合わせる(摩擦)ことで発生しやすく、乾燥した冬場に金属に触れるとパチッと感じる放電現象などを引き起こす。', '名詞句', 'Rubbing a balloon against your hair generates static electricity that makes your hair stand up.', '物理', '480'),
    ('microcanonical ensemble', 'エネルギー・体積・粒子数が厳密に一定に保たれた孤立系を扱う統計集団。許容されるすべての微視的状態(ミクロ状態)が等しい確率で実現するという「等重率の仮定」に基づき、エントロピーを状態数の対数として定義する統計力学の出発点となる。ミクロカノニカル集団、小正準集団。', '名詞句', 'In the microcanonical ensemble, every accessible microstate of an isolated system with fixed energy is assumed to be equally probable.', '物理', '870'),
    ('canonical ensemble', '一定温度の巨大な熱浴と接触し、エネルギーのやり取りは自由だが、粒子数と体積は一定に保たれた系を扱う統計集団。各微視的状態が実現する確率はボルツマン因子exp(-E/kT)に比例する。カノニカル集団、正準集団。', '名詞句', 'In the canonical ensemble, the probability of a microstate is proportional to the Boltzmann factor exp(-E/kT).', '物理', '860'),
    ('grand canonical ensemble', '熱浴と粒子溜め(粒子だまり)の両方に接触し、エネルギーだけでなく粒子数の出入りも自由な開いた系を扱う統計集団。化学ポテンシャルを用いて粒子数の変動を記述する。グランドカノニカル集団、大正準集団。', '名詞句', 'The grand canonical ensemble allows both energy and particle number to fluctuate, making it useful for open systems.', '物理', '880'),
    ('Boltzmann distribution', '熱平衡状態にある系において、エネルギーEを持つ状態の相対的な出現確率がexp(-E/kT)に比例するという分布則。統計力学のもっとも基本的な結果の一つで、カノニカル集団における確率分布を与える。ボルツマン分布。', '名詞句', 'The Boltzmann distribution shows that higher-energy states become exponentially less populated as temperature decreases.', '物理', '850'),
    ('chemical potential', '系の体積とエントロピー(あるいは温度)を一定に保ったまま、粒子(あるいは物質量)を1つ(1モル)加えたときの自由エネルギーの変化量として定義される熱力学量。物質が高い方から低い方へ移動しようとする駆動力となる示強性の量。化学ポテンシャル。', '名詞句', 'Particles spontaneously flow from a region of higher chemical potential to one of lower chemical potential.', '物理', '860'),
    ('equipartition theorem', '古典統計力学において、熱平衡状態にある系の熱エネルギーが、各自由度(運動エネルギーやポテンシャルエネルギーの二次形式で表される項)に平均して(1/2)kTずつ等しく分配されるという定理。エネルギー等分配則。', '名詞句', 'The equipartition theorem predicts that each quadratic degree of freedom contributes one-half kT to the average energy of a system.', '物理', '870'),
    ('ergodic hypothesis', '十分に長い時間にわたって系を観測したときの時間平均が、同じエネルギーを持つすべての微視的状態にわたる集団平均(位相空間平均)と等しくなるという仮定。統計力学において時間平均と統計集団平均を結びつける基礎的な仮説。エルゴード仮説。', '名詞句', 'The ergodic hypothesis assumes that, given enough time, a system will visit every accessible microstate with equal frequency.', '物理', '900'),
    ("Liouville's theorem", 'ハミルトン力学に従う系において、位相空間内の点の集まりが時間発展しても、その占める体積(位相空間密度)は保存されるという定理。統計集団が時間とともにどう変化するかを記述する基礎となる。リウヴィルの定理。', '名詞句', "Liouville's theorem states that the volume occupied by a cloud of points in phase space remains constant as the system evolves in time.", '物理', '910'),
    ('order parameter', '相転移の前後で系の対称性がどのように変化したかを定量的に表す物理量。転移温度より高温の対称性の高い相ではゼロとなり、低温の対称性が破れた相では非ゼロの値をとる。秩序変数、オーダーパラメータ。', '名詞句', 'In a ferromagnet, the net magnetization serves as the order parameter, vanishing above the Curie temperature.', '物理', '880'),
    ('universality class', '相転移の臨界点付近で、系ごとの詳細な相互作用によらず、次元や対称性など少数の共通した性質だけで臨界指数の値が一致するような系の集まり。くりこみ群の考え方によって理論的に説明される。普遍性クラス。', '名詞句', 'Despite their very different microscopic interactions, the liquid-gas transition and the Ising ferromagnet belong to the same universality class.', '物理', '920'),
    ('Ising model', '格子上に並んだ、上向きか下向きかの二値だけをとるスピンが、隣接するスピン同士の相互作用によって同じ向きに揃おうとする、強磁性を説明するための簡略化された統計力学の模型。相転移や臨界現象を調べる基本モデルとして広く使われる。イジング模型。', '名詞句', 'The Ising model represents magnetic spins as simple up-or-down variables arranged on a lattice.', '物理', '900'),
    ('critical exponent', '相転移の臨界点近傍で、比熱・秩序変数・相関長などの物理量が、臨界点までの温度差のべき乗則に従って発散したり消失したりするときの、そのべき指数。同じ普遍性クラスに属する系では共通の値をとる。臨界指数。', '名詞句', 'Near the critical point, the correlation length diverges according to a power law characterized by a critical exponent.', '物理', '910'),
    ('correlation length', '系の中で、ある点における揺らぎ(スピンの向きや密度など)が、離れた点における揺らぎとどの程度の距離まで相関を持つかを示す特徴的な長さのスケール。相転移の臨界点に近づくにつれて発散する。相関長。', '名詞句', 'As the system approaches its critical point, the correlation length grows and eventually diverges.', '物理', '900'),
    ('fluctuation-dissipation theorem', '熱平衡状態にある系において、外部からの微小な摂動に対する応答(散逸)の大きさと、その系が平衡状態で自発的に示す熱的揺らぎの大きさとが、一定の関係式で結びついているという定理。ブラウン運動における摩擦と熱雑音の関係などに現れる。揺動散逸定理。', '名詞句', 'The fluctuation-dissipation theorem relates the friction a particle experiences to the size of its random thermal fluctuations.', '物理', '950'),
    ('Helmholtz free energy', '系の内部エネルギーから、温度とエントロピーの積を差し引いた熱力学ポテンシャル(F = U - TS)。体積と温度を一定に保った過程で系がなしうる最大仕事を表す。ヘルムホルツ自由エネルギー。', '名詞句', 'The Helmholtz free energy represents the maximum work a system can perform at constant temperature and volume.', '物理', '870'),
    ('internal energy', '系を構成する分子・原子がもつ運動エネルギーと、それらの間に働く相互作用のポテンシャルエネルギーの総和として定義される、系そのものが内部に保持するエネルギー。熱力学第一法則において、加えられた熱と系がした仕事によってその変化量が決まる状態量。内部エネルギー。', '名詞句', 'The first law of thermodynamics states that the change in internal energy equals the heat added to the system minus the work done by the system.', '物理', '850'),
    ('isobaric process', '系の圧力を一定に保ちながら状態を変化させる熱力学的過程。定圧過程。', '名詞句', 'In an isobaric process, the gas expands or contracts while its pressure remains constant.', '物理', '860'),
    ('triple point', 'ある物質の固相・液相・気相の3つの相が、特定の温度と圧力のもとで同時に安定して共存する状態(点)。物質ごとに一意に定まるため、温度の基準点としても利用される。三重点。', '名詞句', 'The triple point of water occurs at exactly 0.01 degrees Celsius and about 611.7 pascals of pressure, where ice, liquid water, and vapor all coexist.', '物理', '870'),
    ('critical point', '物質の気相と液相を隔てる相境界線が消滅し、両者の区別がつかなくなる、温度と圧力で定まる終端点。この点を超えると、いくら加圧しても凝縮が起こらない超臨界状態になる。(物理学における)臨界点。', '名詞句', 'Above the critical point, there is no distinction between liquid and gas, and the substance exists as a single supercritical fluid.', '物理', '880'),
    ('van der Waals equation', '理想気体の状態方程式を、分子自身の体積(排除体積)による補正と、分子間に働く弱い引力(ファンデルワールス力)による補正を加えることで拡張した、実在気体の振る舞いをより正確に記述する状態方程式。ファンデルワールスの状態方程式。', '名詞句', 'The van der Waals equation corrects the ideal gas law by accounting for the finite size of molecules and the attractive forces between them.', '物理', '880'),
    ('Clausius-Clapeyron relation', '物質の相転移(蒸発・昇華など)における圧力と温度の関係を、その転移に伴う潜熱と体積変化を用いて表す微分方程式。相図上の相境界線の傾きを与える。クラウジウス・クラペイロンの関係式。', '名詞句', 'The Clausius-Clapeyron relation explains why water boils at a lower temperature at high altitude, where atmospheric pressure is reduced.', '物理', '920'),
    ('Joule-Thomson effect', '気体を、外部との熱のやり取りなしに、小さな穴や弁を通して高圧側から低圧側へ絞り膨張させたときに、その温度が変化する現象。多くの気体は室温付近で膨張とともに冷却され、この効果は冷凍機や気体の液化に応用される。ジュール・トムソン効果。', '名詞句', 'The Joule-Thomson effect causes most gases to cool as they expand through a throttling valve at room temperature.', '物理', '900'),
    ('phase diagram', '温度・圧力などの条件に応じて、物質がどの相(固相・液相・気相など)として安定に存在するかを示す図。相境界線・三重点・臨界点などが描かれる。相図。', '名詞句', 'The phase diagram of water shows the boundaries between ice, liquid water, and water vapor as functions of temperature and pressure.', '物理', '860'),
    ('mean free path', '気体分子などの粒子が、他の粒子と衝突してから次に衝突するまでの間に進む距離の平均値。気体分子運動論において、粘性・熱伝導・拡散といった輸送現象を特徴づける基本的な量。平均自由行程。', '名詞句', 'At higher pressure, gas molecules collide more frequently, so the mean free path becomes shorter.', '物理', '870'),
    ('Navier-Stokes equation', '粘性を持つ流体の運動を記述する基礎方程式で、流体の各点における速度の時間変化を、圧力勾配・粘性による内部摩擦力・外力の効果によって表す。ナビエ-ストークス方程式。', '名詞句', 'The Navier-Stokes equations describe how the velocity of a viscous fluid changes in response to pressure gradients and internal friction.', '物理', '950'),
    ('continuity equation (fluid dynamics)', '流体力学において、質量が生成も消滅もしないという質量保存則を、流れの速度と密度を用いて数式で表したもの。定常な非圧縮性流れでは、流路の断面積と流速の積が一定になることを示す。(流体力学における)連続の式。', '名詞句', 'The continuity equation expresses the conservation of mass, requiring that fluid entering a pipe must equal fluid leaving it.', '物理', '870'),
    ('vorticity', '流体の各点における局所的な回転の強さと向きを表すベクトル量で、速度場の回転(カール)として定義される。渦度。', '名詞', 'Vorticity measures how much a small parcel of fluid is spinning at a given point in the flow.', '物理', '890'),
    ('compressible flow', '流れの中で流体の密度が場所や時間によって無視できないほど変化する流れ。音速に近い、あるいはそれを超える高速の気体の流れなどで重要となる。圧縮性流れ。', '名詞句', 'At speeds approaching the speed of sound, air can no longer be treated as incompressible, and compressible flow effects become important.', '物理', '890'),
    ('incompressible flow', '流れの中で流体の密度がほぼ一定とみなせる流れ。低速の気体や、通常の液体の流れの多くはこの近似がよく成り立つ。非圧縮性流れ。', '名詞句', "Most everyday flows of water can be treated as incompressible flow because water's density changes very little under normal pressures.", '物理', '870'),
    ('shock wave', '圧縮性流体中を、音速を超える速さで圧力・密度・温度が急激に(不連続に)変化しながら伝わる、非常に薄い波面。超音速の飛行体の周囲などに生じる。衝撃波。', '名詞句', 'A supersonic aircraft generates a shock wave that produces the loud sonic boom heard on the ground.', '物理', '880'),
    ('hydrostatic pressure', '静止した流体中で、その流体自身の重さによって生じる圧力。深さに比例して増加し、流体の密度と重力加速度、深さの積で与えられる。静水圧。', '名詞句', 'Hydrostatic pressure increases with depth because deeper water must support the weight of all the water above it.', '物理', '860'),
    ('surface tension', '液体の表面が、あたかも薄い弾性膜のように振る舞い、その表面積をできるだけ小さくしようとする性質。液体分子間に働く引力に由来する。表面張力。', '名詞句', 'Surface tension allows small insects like water striders to walk on the surface of a pond without sinking.', '物理', '860'),
    ('capillary action', '表面張力と、液体が固体表面を濡らそうとする付着力(接着力)との組み合わせによって、細い管や隙間の中を液体が重力に逆らって上昇(あるいは下降)する現象。毛細管現象。', '名詞句', "Capillary action draws water up through the narrow tubes inside a plant's stem, from the roots to the leaves.", '物理', '870'),
    ("Stokes' law", '小さな球形の物体が、粘性のある流体中を非常に遅い速度(低いレイノルズ数)で運動するときに受ける粘性抵抗力を、物体の半径・流体の粘性係数・速度の積として与える法則。ストークスの法則。', '名詞句', "Stokes' law gives the viscous drag force on a small sphere moving slowly through a fluid as proportional to its radius and velocity.", '物理', '900'),
    ('Froude number', '流れの慣性力と重力の相対的な大きさを比較する無次元数で、代表速度を(重力加速度と代表長さの積)の平方根で割って定義される。船舶の造波抵抗や、開水路の流れが射流か常流かを判定する際などに用いられる。フルード数。', '名詞句', 'The Froude number compares the inertial forces of a flow to the force of gravity acting on it.', '物理', '900'),
    ('Prandtl number', '流体固有の性質を表す無次元数で、運動量が拡散する速さ(動粘性係数)と熱が拡散する速さ(熱拡散率)の比として定義される。値が大きいほど、熱よりも運動量の拡散(粘性による影響)が優勢であることを示す。プラントル数。', '名詞句', 'A fluid with a high Prandtl number diffuses momentum much more readily than it diffuses heat.', '物理', '910'),
    ('no-slip condition', '粘性を持つ流体が固体表面に接する境界で、流体の速度が固体表面の速度と一致し、相対的なすべりが生じないとする境界条件。粘性流体力学における基本的な仮定で、境界層の形成の原因となる。無すべり条件。', '名詞句', 'The no-slip condition requires that the layer of fluid in direct contact with a solid surface has zero velocity relative to that surface.', '物理', '890'),
    ('drag coefficient', '物体が流体中を運動する際に受ける抗力の大きさを、物体の形状や表面の性質によって決まる無次元の量として表したもの。抗力は、流体の密度・速度の2乗・物体の代表面積とこの係数の積で与えられる。抗力係数。', '名詞句', 'A streamlined shape has a much lower drag coefficient than a flat, blunt object of the same size.', '物理', '880'),
    ('refractive index', '光が媒質中を進む速さが真空中の速さに対してどれだけ遅くなるかを表す無次元の量。物質の光学的性質を特徴づける基本的な指標で、スネルの法則における屈折角の計算に用いられる。', '名詞句', 'The refractive index of water is about 1.33, which is why a straw appears bent when placed in a glass of water.', '物理', '850'),
    ('birefringence', 'ある種の結晶や材料が、光の振動方向(偏光方向)によって異なる屈折率を示す性質。1本の光線が入射すると常光線と異常光線という2つの光線に分かれて進む現象を指す。複屈折。', '名詞', 'Calcite crystals exhibit strong birefringence, splitting a single beam of light into two separate rays.', '物理', '920'),
    ('dispersion (optics)', '光の屈折率が波長(色)によって異なるために、白色光がプリズムを通過する際に虹色のスペクトルに分かれる現象。物質の光学的性質の波長依存性を指す物理学用語。(注: 統計学などで使われる「ばらつき」を意味するdispersionとは別の、光学分野での意味。)', '名詞句', 'A glass prism separates white light into a rainbow of colors through dispersion, since each wavelength refracts by a slightly different amount.', '物理', '870'),
    ('diffraction grating', '等間隔に並んだ多数の細いスリットや溝によって光を回折・干渉させ、波長ごとに異なる角度に分解する光学素子。分光器の中核部品として、スペクトル分析に広く用いられる。回折格子。', '名詞句', 'A diffraction grating splits incoming light into its component wavelengths, producing a spectrum much like a prism but with greater precision.', '物理', '880'),
    ('polarizability', '外部から電場をかけられたとき、原子や分子の電子雲がどれだけ変形して電気双極子モーメントを誘起されやすいかを表す物理量。物質の屈折率や光の散乱、分子間力(ファンデルワールス力)の強さを左右する。分極率。', '名詞', 'The polarizability of a molecule determines how strongly its electron cloud shifts in response to an external electric field.', '物理', '900'),
    ('coherence length', '光源から出た波が、位相のそろった(コヒーレントな)状態を保っていられる進行距離の目安。この距離を超えると波の位相関係が崩れ、干渉縞のコントラストが失われる。コヒーレンス長。', '名詞句', 'A laser has a much longer coherence length than an ordinary light bulb, allowing it to produce sharp interference patterns even over long optical paths.', '物理', '910'),
    ('holography', '物体で反射・散乱した光(物体光)と、それと干渉させる基準光との干渉縞を記録媒体に記録し、後にその干渉縞に光を当てることで元の物体の三次元的な像を再生する技術・原理。ホログラフィー。', '名詞', 'Holography records both the amplitude and phase of light waves, allowing a fully three-dimensional image to be reconstructed.', '物理', '860'),
    ('stimulated emission', 'すでに励起状態にある原子や分子に、その遷移エネルギーに等しいエネルギーを持つ光子が入射すると、入射光子と全く同じ位相・波長・進行方向を持つ光子が新たに放出される現象。レーザー発振の基本原理となる。誘導放出。', '名詞句', 'Stimulated emission produces a new photon that is identical in phase, wavelength, and direction to the photon that triggered it.', '物理', '870'),
    ('population inversion', '通常は熱平衡状態でより多くの原子・分子が存在する低いエネルギー準位よりも、高いエネルギー準位(励起状態)にある原子・分子の数の方が多くなっている、非平衡な状態。レーザー発振を実現するための必要条件。反転分布。', '名詞句', 'Population inversion must be achieved before a laser medium can amplify light through stimulated emission rather than simply absorbing it.', '物理', '900'),
    ('wavefront', 'ある瞬間において、波源から出た波の位相が等しい点を結んでできる面(等位相面)。光や音などの波の伝わり方や進行方向を視覚的に捉えるための基本概念。波面。', '名詞', 'As light spreads out from a point source, its wavefronts form expanding spheres centered on the source.', '物理', '880'),
    ("Huygens' principle", '波面上のすべての点が、それ自体新たな球面波(素元波)の波源になっており、次の瞬間の波面はそれら無数の素元波が重なり合う共通の接面として決まる、とする波動伝搬に関する原理。ホイヘンスの原理。', '名詞句', "Huygens' principle explains diffraction by treating every point on a wavefront as a source of new spherical wavelets.", '物理', '890'),
    ('Fresnel equations', '光が屈折率の異なる2つの媒質の境界面に入射したとき、その入射角と偏光状態(s偏光・p偏光)に応じて、反射光と透過光の強度の比率がどのように決まるかを記述する一群の方程式。フレネルの式。', '名詞句', "The Fresnel equations predict that at a certain angle, called Brewster's angle, p-polarized light is transmitted almost entirely with no reflection.", '物理', '950'),
    ('total internal reflection', '光が屈折率の大きい媒質から小さい媒質へ進む際、入射角がある臨界角を超えると、光が境界面で屈折して外に出ることができず、すべて反射される現象。全反射。', '名詞句', 'Total internal reflection occurs when light traveling in glass strikes the glass-air boundary at an angle greater than the critical angle.', '物理', '850'),
    ('evanescent wave', '全反射が起こる境界面のすぐ近くで、透過側の媒質中にわずかににじみ出す、伝搬せずに境界面から離れるにつれて指数関数的に急速に減衰する電磁波。エバネッセント波、しみ出し波。', '名詞句', 'Although total internal reflection sends nearly all the light back, a thin evanescent wave still penetrates a short distance into the second medium.', '物理', '940'),
    ('nonlinear optics', '非常に強い光(通常はレーザー光)を物質に照射した際に、物質の応答(分極)が入射光の強度に比例しなくなり、第二高調波発生や光の周波数混合など、通常の(線形)光学では起こらない現象を扱う光学の分野。非線形光学。', '名詞句', 'Nonlinear optics became a major field of research only after the invention of the laser provided light intense enough to reveal these effects.', '物理', '900'),
    ('second-harmonic generation', '非線形光学結晶に強いレーザー光を入射させたとき、入射光と同じ周波数の光の一部が、その2倍の周波数(半分の波長)を持つ光に変換される現象。第二高調波発生(SHG)。', '名詞句', 'Second-harmonic generation converts infrared laser light at 1064 nanometers into green light at exactly half that wavelength, 532 nanometers.', '物理', '960'),
    ('photonic crystal', '屈折率が光の波長程度の周期で規則的に変化するように人工的に設計された構造体。特定の波長帯の光がその内部を伝搬できなくなる「フォトニックバンドギャップ」を持つことができ、光を自在に制御する材料として研究されている。フォトニック結晶。', '名詞句', 'A photonic crystal can be engineered to block certain wavelengths of light entirely, much as a semiconductor blocks certain energies of electrons.', '物理', '930'),
    ("Snell's law", '光が屈折率の異なる2つの媒質の境界面で屈折するとき、入射角の正弦と屈折角の正弦の比が、2つの媒質の屈折率の比によって一定に定まるという法則。スネルの法則(屈折の法則)。', '名詞句', "Snell's law lets engineers calculate exactly how much a light ray will bend when it passes from air into glass.", '物理', '850'),
    ("Brewster's angle", '光が屈折率の異なる2つの媒質の境界面に入射する際、その入射角で反射した光が完全に直線偏光となる特定の角度。この角度では、境界面に平行な偏光成分(p偏光)がまったく反射されない。ブリュースター角。', '名詞句', "At Brewster's angle, light reflected off a glass surface becomes completely polarized, with no component vibrating parallel to the plane of incidence.", '物理', '900'),
    ('Brillouin zone', '結晶の逆格子空間において、原点(逆格子点の一つ)に最も近いすべての等価な逆格子点との垂直二等分面によって囲まれた、原点を含む領域(ウィグナー・ザイツ胞)。結晶中の電子や格子振動の波数(運動量)がとりうる値を過不足なく表す基本単位となる。ブリルアンゾーン。', '名詞句', 'Electron energy bands are typically plotted as a function of wavevector within the first Brillouin zone.', '物理', '950'),
    ('reciprocal lattice', '結晶を構成する原子の周期的な配列(実空間の結晶格子)に対応して定義される、波数空間(運動量空間)上の格子。結晶によるX線・電子線の回折パターンや、電子・格子振動の波数状態を扱う際に用いられる数学的な概念。逆格子。', '名詞句', 'The diffraction pattern produced by X-rays scattering off a crystal directly reveals the geometry of its reciprocal lattice.', '物理', '940'),
    ('exciton', '半導体や絶縁体において、光の吸収などによって伝導帯に励起された電子と、価電子帯に残された正孔(ホール)とが、クーロン力によって互いに束縛され、あたかも一つの粒子(準粒子)のように振る舞う電子・正孔対。励起子。', '名詞', 'An exciton forms when an electron absorbs a photon and jumps to the conduction band, remaining bound to the hole it leaves behind by their mutual electric attraction.', '物理', '900'),
    ('band structure', '結晶中の電子がとりうるエネルギーを、波数(結晶運動量)の関数として表した関係。原子が周期的に配列することで、電子のエネルギーが特定の範囲(エネルギーバンド)にのみ許され、その間に電子が存在できない禁制帯(バンドギャップ)が生じる。バンド構造。', '名詞句', 'The band structure of a material determines whether it behaves as a metal, a semiconductor, or an insulator.', '物理', '890'),
    ('density of states', 'ある物理系(結晶中の電子など)において、単位エネルギー幅あたりに存在できる量子状態の数を、エネルギーの関数として表した量。状態密度。', '名詞句', 'The density of states tells physicists how many electron states are available at each energy level within a material.', '物理', '920'),
    ('Fermi surface', '金属や縮退した電子系において、絶対零度で電子によって占有された状態と占有されていない状態との境界を、波数空間(運動量空間)上に描いた曲面。金属の電気伝導・熱伝導・磁気的性質の多くを決定する。フェルミ面。', '名詞句', "The shape of a metal's Fermi surface strongly influences how it conducts electricity and responds to magnetic fields.", '物理', '930'),
    ('Fermi level', '電子系において、ある温度・状態のもとで電子がその準位を占有する確率がちょうど50%になるエネルギー準位(化学ポテンシャル)。絶対零度における占有・非占有の境界そのものを指す「フェルミエネルギー」とは異なり、温度や不純物濃度(ドーピング)によって位置が変化しうる。フェルミ準位。', '名詞句', 'In an intrinsic semiconductor, the Fermi level sits roughly midway between the valence band and the conduction band.', '物理', '900'),
    ('quantum Hall effect', '極低温・強磁場のもとに置かれた二次元電子系において、ホール伝導率(電流に垂直な方向に生じる電圧と電流の比の逆数)が連続的にではなく、基礎物理定数のみで決まる特定の値の整数倍(または分数倍)に量子化された階段状の値をとる現象。量子ホール効果。', '名詞句', 'The quantum Hall effect reveals Hall conductance quantized in steps so precise that it is now used to define a standard of electrical resistance.', '物理', '970'),
    ('spintronics', '電子の持つ電荷だけでなく、スピン(自転に似た内部自由度で、磁性の起源となる)という性質も情報の記録・伝達に積極的に利用しようとする、エレクトロニクスの一分野。スピントロニクス。', '名詞', 'Spintronics aims to exploit the spin of electrons, not just their charge, to store and process information more efficiently.', '物理', '910'),
    ('metamaterial', '天然の物質には見られない特異な電磁気的性質(負の屈折率など)を実現するために、光や電波の波長よりも小さい人工的な構造単位を周期的に配列して作られた複合材料。メタマテリアル。', '名詞', 'A metamaterial can be engineered to bend light in the opposite direction from any naturally occurring material.', '物理', '900'),
    ('plasmon', '金属中に大量に存在する自由電子の集団が、外部からの光の電場に応答して一体となって振動する現象を、量子化された準粒子として捉えたもの。特に金属表面近くに局在する振動は「表面プラズモン」と呼ばれる。プラズモン。', '名詞', 'A plasmon is the quantum of a collective oscillation of free electrons at the surface of a metal.', '物理', '890'),
    ('doping (semiconductor)', '半導体の結晶に、価電子数の異なる微量の不純物元素を意図的に加えることで、電気伝導を担う自由電子や正孔の濃度を人為的に制御する技術・処理。ドーピング(半導体)。(注: 一般語彙・スポーツ分野のdoping「(禁止薬物などによる)不正な使用」とは全く別の意味の同綴り異義語。)', '名詞', 'Doping silicon with phosphorus atoms, which have one extra valence electron, creates n-type semiconductor material with an excess of free electrons.', '物理', '870'),
    ('p-n junction', 'p型半導体とn型半導体を接合させた構造。接合面付近で電子と正孔が拡散・再結合し、電流を一方向にしか流さない整流作用や、光を当てると起電力が生じる光起電力効果を示す。pn接合。', '名詞句', 'A p-n junction allows electric current to flow easily in one direction while blocking it almost completely in the other.', '物理', '860'),
    ('hole (semiconductor physics)', '半導体の価電子帯において、電子が1個欠けている状態を、あたかも正の電荷を持つ粒子のように扱う概念上の粒子。正孔。(注: 一般語彙のhole「穴」とは異なる、半導体物理学に特有の専門的な意味の同綴り異義語。)', '名詞', 'When an electron is excited into the conduction band, it leaves behind a hole that behaves as if it carries a positive charge.', '物理', '870'),
    ('work function', '金属や半導体の表面から、1個の電子を真空中(表面のすぐ外側)まで取り出すために必要な最小のエネルギー。物質の表面電子状態を特徴づける基本的な物理量。仕事関数。', '名詞句', 'The work function of a metal determines the minimum photon energy needed to eject an electron from its surface in the photoelectric effect.', '物理', '900'),
    ('Josephson junction', '2つの超伝導体の間に、非常に薄い絶縁層(またはごく細い常伝導金属)を挟んだ構造。この薄い障壁を、電圧をかけなくても超伝導電子対(クーパー対)がトンネル効果によって通り抜け、超伝導電流(ジョセフソン電流)が流れる。ジョセフソン接合。', '名詞句', 'A Josephson junction allows a supercurrent to tunnel between two superconductors separated by an extremely thin insulating barrier, even with no applied voltage.', '物理', '960'),
    ('magnetoresistance', '物質に外部から磁場をかけたときに、その電気抵抗が変化する現象。特に、強磁性金属の薄膜を非磁性の薄い層で挟んだ多層構造で観測される、抵抗が数十%も大きく変化する「巨大磁気抵抗効果(GMR)」はハードディスクの読み取り技術に革命をもたらした。磁気抵抗。', '名詞', "Magnetoresistance describes how a material's electrical resistance changes when it is placed in a magnetic field.", '物理', '920'),
    ('magnon', '強磁性体などの磁性体において、隣り合う原子のスピンの向きが波のように連続的にずれていく集団的な励起(スピン波)を、量子化された準粒子として捉えたもの。マグノン。', '名詞', 'A magnon is the quantized unit of a spin wave, much as a phonon is the quantized unit of a lattice vibration.', '物理', '950'),
    ('quantum dot', '数ナノメートルほどの大きさに人工的に作られた、半導体などからなる微小な結晶。内部の電子・正孔の運動が三次元すべての方向で強く閉じ込められるため、原子のように離散的なエネルギー準位を持ち、その大きさによって発光する光の色(波長)を自在に制御できる。量子ドット。', '名詞句', "A quantum dot's emission color can be tuned simply by changing its physical size, with smaller dots emitting bluer light.", '物理', '880'),
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
