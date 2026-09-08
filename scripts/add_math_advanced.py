# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""数学ドメインの学部専門レベルへの深化(2026-09-08・B24タスク・authored by
Claude)。関数解析/超関数論・複素解析/解析的整数論・抽象代数/位相幾何・
測度論/確率論/微分方程式の4サブ分野を並列サブエージェントでドラフト→
WebSearchで歴史的事実(人名・年代・優先権)を検証済み。既存DB全体(206分野
すべて)とのenglish重複チェック済み(3語は他分野の既存語と同一概念のため
除外: convolution=AI分野の「畳み込み」、central limit theorem/random walk=
統計学分野の既存語)。

ユーザー指定の超関数(distribution/generalized function)・デルタ関数
(Dirac delta function)・ゼータ関数(Riemann zeta function)を含む。
既存の`distribution`(確率分布、レベル600)とは別概念のため
`distribution (generalized function)`として曖昧さ回避。

事実確認で優先権・初出年代を一次資料で確定できなかった語
(modular form, normal subgroup, cohomology, vector bundle,
characteristic function (probability), filtration (probability))は、
断定を避けた穏当な記述にとどめてある(detailのorigin欄参照)。

No app / OpenAI API calls — hand-written(並列サブエージェントでドラフト後に
人手でdedup・事実確認)、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_math_advanced.py
仕上げ: 投入後は relevel.py は実行しない(既存のH900/H990/H990Pリストに
今回の語が含まれておらず、DOMAIN_BASE="数学":800に一律で潰されてしまう
ため。add_academic_deepening.py実施時と同じ理由でlevelは各語のタプルで
直接指定した値を正としてそのまま使う)。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("analytic continuation", "ある領域上で定義された正則関数を、値の一致を保ったまま、より広い領域上の正則関数へ一意に拡張する操作。解析接続。", "名詞句", "Analytic continuation extends the Riemann zeta function, originally defined only for complex numbers with real part greater than 1, to a function defined on almost the entire complex plane.", "数学", "950"),
    ("branch cut", "多価関数(対数関数や平方根など)を一価の正則関数として扱うために、複素平面上に人為的に設ける、値が不連続に飛ぶ切断線。分岐切断。", "名詞句", "A branch cut along the negative real axis is commonly used to define a single-valued version of the complex logarithm.", "数学", "920"),
    ("Cauchy integral formula", "正則関数の値を、それを囲む閉曲線上での値の周回積分によって表す公式。コーシーの積分公式。", "名詞句", "The Cauchy integral formula expresses the value of a holomorphic function at a point inside a closed contour in terms of an integral of the function over the contour.", "数学", "920"),
    ("Cauchy-Riemann equations", "複素関数f(z)=u(x,y)+iv(x,y)が正則であるための必要条件を与える、実部uと虚部vに関する連立偏微分方程式(∂u/∂x=∂v/∂y, ∂u/∂y=-∂v/∂x)。コーシー・リーマンの方程式。", "名詞句", "A complex function satisfies the Cauchy-Riemann equations at a point if and only if it is complex differentiable there, provided its partial derivatives are continuous.", "数学", "910"),
    ("contour integral", "複素平面上の曲線(経路)に沿って複素関数を積分したもの。周回積分(特に閉曲線に沿う場合)。", "名詞句", "A contour integral of a holomorphic function around a closed curve that does not enclose any singularities is always zero.", "数学", "900"),
    ("holomorphic function", "複素平面のある開集合の各点で複素微分可能な関数。正則関数。", "名詞句", "A holomorphic function is infinitely differentiable and can be represented locally by a convergent power series.", "数学", "900"),
    ("Laurent series", "特異点を含む環状領域(アニュラス)で正則な関数を、負べきの項も含む無限級数として展開したもの。ローラン級数。", "名詞句", "The Laurent series of a function around an isolated singularity includes negative-power terms that reveal the nature of the singularity.", "数学", "950"),
    ("meromorphic function", "複素平面のある領域で、有限個(または可算個)の孤立した極を除いて正則な関数。有理型関数。", "名詞句", "A meromorphic function on the complex plane can be written locally as the ratio of two holomorphic functions.", "数学", "910"),
    ("pole (complex analysis)", "有理型関数において、そこで関数の値が無限大に発散する孤立特異点。極。", "名詞", "The function 1/(z-1) has a simple pole at z = 1, where its value diverges to infinity.", "数学", "900"),
    ("residue theorem", "閉曲線に沿った有理型関数の周回積分を、その閉曲線が囲む特異点における留数の総和の2πi倍として計算できるという定理。留数定理。", "名詞句", "The residue theorem reduces the calculation of a contour integral to summing the residues at the poles enclosed by the contour.", "数学", "930"),
    ("gamma function", "階乗の概念を正の整数以外の複素数(非正の整数を除く)へと拡張した特殊関数。Γ(n)=(n-1)!を満たす。ガンマ関数。", "名詞句", "The gamma function extends the factorial to complex numbers, satisfying Γ(n) = (n-1)! for every positive integer n.", "数学", "900"),
    ("algebraic number", "整数係数(または有理数係数)のある0でない多項式の根となる複素数。代数的数。", "名詞句", "Every rational number is an algebraic number, since p/q is a root of the polynomial qx - p.", "数学", "900"),
    ("Chinese remainder theorem", "互いに素な複数の法(mod)に関する連立合同式が、法の積を法として一意な解を持つことを示す定理。中国剰余定理。", "名詞句", "The Chinese remainder theorem guarantees a unique solution modulo 105 to a system of congruences modulo the pairwise coprime numbers 3, 5, and 7.", "数学", "910"),
    ("congruence (number theory)", "2つの整数の差がある整数(法)で割り切れるとき、その2つの整数は法を法として合同であるという関係。合同(数論)。", "名詞", "We say that 17 is congruent to 5 modulo 12, written 17 ≡ 5 (mod 12), because their difference 12 is divisible by 12.", "数学", "870"),
    ("Diophantine equation", "整数(または有理数)の解のみに関心を持つ、係数が整数であるような多項式方程式。ディオファントス方程式。", "名詞句", "The equation x^2 + y^2 = z^2 is a Diophantine equation whose integer solutions are called Pythagorean triples.", "数学", "900"),
    ("Dirichlet series", "Σ a_n / n^s の形の無限級数。解析的整数論における基本的な研究対象で、リーマンゼータ関数やディリクレのL関数はその特別な場合にあたる。ディリクレ級数。", "名詞句", "The Riemann zeta function is the simplest example of a Dirichlet series, obtained by taking all the coefficients a_n equal to 1.", "数学", "950"),
    ("Euclidean algorithm", "2つの整数の最大公約数を、大きい方を小さい方で割った余りを繰り返し求めることで効率的に計算する手順。ユークリッドの互除法。", "名詞句", "The Euclidean algorithm finds the greatest common divisor of two integers by repeatedly replacing the larger number with the remainder of dividing it by the smaller one.", "数学", "870"),
    ("Euler product formula", "リーマンゼータ関数を、すべての素数にわたる無限積として表す等式。ζ(s)=Π_p 1/(1-p^(-s))。オイラー積公式。", "名詞句", "The Euler product formula expresses the Riemann zeta function as an infinite product over all prime numbers.", "数学", "950"),
    ("Euler's totient function", "正の整数nに対し、n以下の正の整数のうちnと互いに素なものの個数を与える関数。φ(n)と書く。オイラーのφ関数(オイラーのトーシェント関数)。", "名詞句", "Euler's totient function φ(8) equals 4, since 1, 3, 5, and 7 are the positive integers up to 8 that are coprime to it.", "数学", "900"),
    ("Fermat's little theorem", "pが素数のとき、pで割り切れない任意の整数aについて a^(p-1)≡1 (mod p) が成り立つという定理(a^p≡a (mod p) の形でも表せる)。フェルマーの小定理。", "名詞句", "Fermat's little theorem tells us that 2^6 ≡ 1 (mod 7), since 7 is prime and 2 is not divisible by 7.", "数学", "900"),
    ("L-function", "リーマンゼータ関数やディリクレのL関数を特別な場合として含む、解析接続・関数等式・オイラー積といった性質を持つ複素関数の総称。数論的対象(数体・保型形式・楕円曲線など)と結びついた深い情報を持つ。L関数。", "名詞", "An L-function is typically defined by a Dirichlet series that has an Euler product and can be analytically continued to a meromorphic function on the whole complex plane.", "数学", "980"),
    ("modular arithmetic", "整数をある一定の数(法)で割った余りだけに着目して行う演算体系。時計の文字盤のように、法に達すると0に戻って計算する算術。合同算術(モジュラー演算)。", "名詞句", "In modular arithmetic with modulus 12, adding 5 hours to 9 o'clock gives 2 o'clock, since 9 + 5 = 14 ≡ 2 (mod 12).", "数学", "850"),
    ("modular form", "複素上半平面上で定義された正則関数で、モジュラー群(またはその部分群)の作用に対して特定の変換規則(重さkの保型性)に従い、かつ無限遠点で適切な増大条件を満たすもの。モジュラー形式。", "名詞句", "A modular form of weight k transforms in a precise way under the action of the modular group on the upper half-plane.", "数学", "990"),
    ("Möbius function", "正の整数nに対し、nが平方因子を持てば0、nが相異なるk個の素数の積であれば(-1)^k、n=1であれば1を与える数論的関数。μ(n)と書く。メビウス関数。", "名詞句", "The Möbius function μ(30) equals -1, since 30 = 2 × 3 × 5 is a product of three distinct primes.", "数学", "970"),
    ("p-adic number", "素数pを固定し、整数の「pで何回割り切れるか」に基づく距離(p進距離)によって有理数を完備化して得られる数の体系。実数とは異なる方法で有理数を拡張したもの。p進数。", "名詞句", "The p-adic numbers form a completion of the rational numbers with respect to the p-adic absolute value, distinct from the completion that yields the real numbers.", "数学", "970"),
    ("prime number theorem", "x以下の素数の個数π(x)が、xが大きくなるにつれてx/ln(x)に漸近的に近づくことを示す定理。素数定理。", "名詞句", "The prime number theorem states that π(x), the number of primes up to x, is asymptotically equal to x divided by the natural logarithm of x.", "数学", "930"),
    ("quadratic residue", "素数pを法として、ある整数の平方と合同になる数(0を除く)。すなわちx^2≡a (mod p)を満たす整数xが存在するような整数a。平方剰余。", "名詞句", "4 is a quadratic residue modulo 7, since 2^2 = 4 is congruent to 4 modulo 7.", "数学", "920"),
    ("Riemann hypothesis", "リーマンゼータ関数の自明でない零点(負の偶数以外の零点)は、すべて実部が1/2の直線上にあるという予想。1859年にリーマンが提起し、現在も未解決。リーマン予想。", "名詞句", "The Riemann hypothesis asserts that every non-trivial zero of the Riemann zeta function has real part exactly one-half.", "数学", "990+"),
    ("Riemann zeta function", "実部が1より大きい複素数sに対しΣ 1/n^s として定義され、解析接続によって複素平面全体(s=1の単純極を除く)へ拡張される特殊関数。リーマンゼータ関数。", "名詞句", "The Riemann zeta function was first studied by Euler for real values of s, before Riemann extended it to the complex plane in 1859.", "数学", "970"),
    ("transcendental number", "整数係数の0でない多項式の根にはなり得ない複素数。代数的数ではない数。超越数。", "名詞句", "Liouville proved in 1844 that certain specially constructed numbers, now called Liouville numbers, are transcendental.", "数学", "910"),
    ("coset", "群の部分群による分割で得られる同値類。部分群Hと群の元gに対し、gH(左剰余類)やHg(右剰余類)として定義される。剰余類。", "名詞", "Every coset of a subgroup H in a group G has the same number of elements as H itself.", "数学", "870"),
    ("cyclic group", "一つの元(生成元)のべき乗(加法群であれば整数倍)だけですべての元が表される群。巡回群。", "名詞句", "The group of integers modulo n under addition is a cyclic group generated by the element 1.", "数学", "870"),
    ("exact sequence", "準同型写像の列において、各写像の像が次の写像の核と一致するという性質を持つ列。完全列。", "名詞句", "In an exact sequence, the image of each homomorphism equals the kernel of the next one.", "数学", "950"),
    ("Galois theory", "体の拡大とその自己同型群(ガロア群)との対応関係を通じて、方程式の可解性などを研究する代数学の理論。ガロア理論。", "名詞句", "Galois theory shows that there is no general formula using radicals to solve polynomial equations of degree five or higher.", "数学", "990"),
    ("group action", "群の各元を、ある集合上の変換(全単射)として作用させる仕組み。群の演算が集合上の変換の合成に対応する。群作用。", "名詞句", "A group action allows the elements of a group to be realized concretely as symmetries of a given set.", "数学", "930"),
    ("ideal (ring theory)", "環の部分集合で、加法について部分群をなし、かつ環の任意の元をかけても集合内に留まるという性質を持つもの。イデアル。", "名詞", "An ideal of a ring is a subset that is closed under addition and absorbs multiplication by any element of the ring.", "数学", "950"),
    ("kernel (algebra)", "準同型写像によって単位元(または零元)に写される元全体からなる部分集合。核。", "名詞", "The kernel of a group homomorphism is always a normal subgroup of the domain.", "数学", "900"),
    ("Lie group", "群の構造と滑らかな多様体の構造を同時に備え、群の演算(積・逆元)が滑らかな写像になっている群。リー群。", "名詞句", "A Lie group combines the algebraic structure of a group with the smooth structure of a differentiable manifold.", "数学", "980"),
    ("module (algebra)", "ベクトル空間の概念を、係数体の代わりに環を使って一般化した代数構造。加群。", "名詞", "A module is defined like a vector space, but its scalars come from a ring instead of a field.", "数学", "950"),
    ("normal subgroup", "群の部分群のうち、群のどの元で共役を取っても自分自身と一致するもの。この部分群による左右の剰余類が一致し、剰余類全体が自然に群(剰余群)をなす。正規部分群。", "名詞句", "A normal subgroup is invariant under conjugation by every element of the group.", "数学", "910"),
    ("polynomial ring", "ある環(または体)の元を係数とする多項式全体からなる、多項式の加法と乗法によって環をなす代数構造。多項式環。", "名詞句", "The polynomial ring R[x] consists of all polynomials with coefficients in the ring R.", "数学", "900"),
    ("quotient group", "群をある正規部分群で類別してできる剰余類全体に、自然な演算を定めて得られる新しい群。剰余群/商群。", "名詞句", "The quotient group G/N is formed by the cosets of a normal subgroup N in G.", "数学", "920"),
    ("Sylow theorem", "有限群の位数を割り切る素数の冪に対して、その位数を持つ部分群(シロー部分群)の存在・共役性・個数に関する一連の定理。シローの定理。", "名詞句", "Sylow's theorem guarantees that a finite group has a subgroup of order equal to any prime power dividing the group's order.", "数学", "970"),
    ("cohomology", "空間や代数的対象に対して、鎖複体の双対(コチェイン複体)から定義される代数的不変量。ホモロジーと対をなし、積構造(カップ積)を持つ点が特徴。コホモロジー。", "名詞", "Cohomology assigns algebraic invariants to a space using cochains, and unlike homology it carries a natural ring structure.", "数学", "990+"),
    ("connectedness (topology)", "位相空間が、互いに交わらない2つ以上の空でない開集合に分割できない(=一つのまとまりとしてつながっている)という性質。連結性。", "名詞", "A topological space has connectedness if it cannot be divided into two disjoint nonempty open sets.", "数学", "870"),
    ("continuous function (topology)", "位相空間の間の写像で、行き先の空間の任意の開集合の逆像が、もとの空間でも開集合になるという性質を持つもの。位相空間論における連続関数。", "名詞句", "A continuous function between topological spaces is one for which the preimage of every open set is open.", "数学", "850"),
    ("curvature (geometry)", "曲線や曲面、多様体が「まっすぐな空間」からどれだけ曲がっているかを数量的に表す幾何学的な量。曲率。", "名詞", "The curvature of a circle of radius r is defined as the reciprocal of r.", "数学", "870"),
    ("diffeomorphism", "2つの多様体の間の全単射で、その写像自身も逆写像も何回でも微分可能(滑らか)であるもの。微分同相写像。", "名詞", "A diffeomorphism is a smooth bijection between manifolds whose inverse is also smooth.", "数学", "930"),
    ("differentiable manifold", "各点の近くでユークリッド空間と見なせる(局所座標が取れる)空間のうち、座標の取り替え(変換関数)が滑らかであるもの。微分可能多様体/可微分多様体。", "名詞句", "A differentiable manifold is a manifold equipped with coordinate charts whose transition functions are smooth.", "数学", "900"),
    ("fundamental group", "空間内の基点を通るループ(閉曲線)を、連続変形(ホモトピー)で同一視して得られる群。空間の「穴」の位置や種類を検出する位相不変量。基本群。", "名詞句", "The fundamental group of the circle is isomorphic to the group of integers under addition.", "数学", "950"),
    ("Hausdorff space", "相異なる2点に対して、それぞれを含む互いに交わらない開集合を必ず取れるという分離性を持つ位相空間。ハウスドルフ空間。", "名詞句", "In a Hausdorff space, any two distinct points can be separated by disjoint open sets.", "数学", "950"),
    ("homeomorphism", "2つの位相空間の間の全単射連続写像で、その逆写像も連続であるもの。この写像が存在するとき2つの空間は位相的に同じ(位相同型)とみなされる。同相写像/位相同型写像。準同型写像(homomorphism)が代数構造を保つ写像であるのに対し、同相写像は連続性という位相構造を保つ点が異なる。", "名詞", "A homeomorphism is a continuous bijection between topological spaces whose inverse is also continuous.", "数学", "900"),
    ("homology", "空間を単体や鎖などの図形の組み合わせに分解し、その境界を取る操作から定義される代数的不変量。空間に開いた「穴」の次元ごとの個数を検出する。ホモロジー。コホモロジーがコチェイン複体から定義される双対的な構成であるのに対し、ホモロジーは鎖複体から直接定義される。", "名詞", "Homology detects the number and dimension of holes in a space by analyzing chains of simplices and their boundaries.", "数学", "970"),
    ("Jacobian", "多変数関数の1階偏導関数を並べた行列(ヤコビ行列)、またはその行列式(ヤコビ行列式)。変数変換に伴う面積・体積の拡大率を表す。ヤコビアン。", "名詞", "The Jacobian determinant describes how a transformation scales area or volume near a given point.", "数学", "900"),
    ("manifold", "空間全体としては曲がっていたり複雑な形をしていても、各点の十分小さな近くだけを見ればユークリッド空間と見なせるような図形・空間。多様体。", "名詞", "A manifold is a space that locally resembles ordinary Euclidean space near every point.", "数学", "880"),
    ("Riemannian manifold", "各点の接空間に、内積(計量)が滑らかに定められた微分可能多様体。この計量によって曲線の長さや角度、曲率などが定義できる。リーマン多様体。", "名詞句", "A Riemannian manifold is a differentiable manifold equipped with a smoothly varying inner product on each tangent space.", "数学", "980"),
    ("simply connected", "空間が連結であり、かつその中のどんなループ(閉曲線)も、空間の中で連続的に変形して1点に縮められるという性質を持つこと。単連結。", "形容詞", "A space is simply connected if it is connected and every loop in it can be continuously shrunk to a point.", "数学", "900"),
    ("tangent space", "多様体上のある1点において、その点を通る曲線の速度ベクトル(接ベクトル)全体がなすベクトル空間。接空間。", "名詞句", "The tangent space at a point of a manifold consists of all the velocity vectors of curves passing through that point.", "数学", "910"),
    ("vector bundle", "空間(底空間)の各点にベクトル空間(ファイバー)を対応させ、それらが全体として滑らかに(または連続的に)つながるようにした構造。ベクトル束。", "名詞句", "A vector bundle assigns a vector space to each point of a base space in a way that varies smoothly from point to point.", "数学", "970"),
    ("adjoint operator", "ヒルベルト空間(または内積空間)上の有界線形作用素Tに対し、任意のベクトルx,yについて⟨Tx,y⟩=⟨x,T*y⟩を満たす作用素T*のこと。随伴作用素。", "名詞句", "For a bounded linear operator T on a Hilbert space, the adjoint operator T* is uniquely determined by the relation ⟨Tx, y⟩ = ⟨x, T*y⟩ for all x and y.", "数学", "920"),
    ("Banach space", "完備な(すべてのコーシー列がその空間内で収束する)ノルム空間のこと。バナッハ空間。", "名詞句", "Every Hilbert space is a Banach space, but not every Banach space carries an inner product that induces its norm.", "数学", "900"),
    ("bounded linear operator", "ノルム空間の間の線形写像Tであって、あるC>0が存在し、任意のxに対して‖Tx‖≤C‖x‖が成り立つもの。有界線形作用素。", "名詞句", "A linear operator between normed spaces is bounded if and only if it is continuous.", "数学", "910"),
    ("compact operator", "ノルム空間の任意の有界集合を、像の閉包が常にコンパクト集合になるような集合へ写す線形作用素のこと。コンパクト作用素。", "名詞句", "Compact operators can be approximated by finite-rank operators on a Hilbert space, which makes their spectral theory resemble that of matrices.", "数学", "970"),
    ("completeness (functional analysis)", "距離空間において、任意のコーシー列がその空間内の点に収束するという性質のこと。関数解析における完備性。", "名詞", "The completeness of a normed vector space is precisely the property that makes it a Banach space.", "数学", "900"),
    ("distribution (generalized function)", "(確率分布とは異なり)通常の関数の枠組みでは定義できない対象を、滑らかな試験関数への作用(線形汎関数)として定義することで扱えるようにした概念。超関数、一般化された関数。ディラックのデルタ関数はその代表例。", "名詞", "In distribution theory, a generalized function is defined not by its pointwise values but by how it acts as a linear functional on test functions.", "数学", "980"),
    ("dual space", "あるベクトル空間上で定義されたすべての(有界)線形汎関数からなる空間のこと。双対空間。", "名詞句", "The dual space of a normed vector space consists of all bounded linear functionals defined on it.", "数学", "910"),
    ("Fourier transform", "関数を、その関数に含まれる様々な周波数の成分(振幅と位相)を表す別の関数へと変換する積分変換のこと。フーリエ変換。", "名詞句", "The Fourier transform decomposes a function of time into the frequencies that make it up.", "数学", "850"),
    ("Green's function", "線形微分作用素に関する境界値問題において、点源(デルタ関数)に対する応答を表す関数のこと。この関数を用いると、一般の外力に対する解を積分によって構成できる。グリーン関数。", "名詞句", "A Green's function represents the response of a linear differential operator to a point source, modeled by a Dirac delta function.", "数学", "950"),
    ("Hilbert space", "内積が定義され、その内積から導かれるノルムに関して完備であるベクトル空間のこと。ヒルベルト空間。", "名詞句", "A Hilbert space generalizes the notion of Euclidean space to infinite dimensions while preserving the concepts of length and angle.", "数学", "870"),
    ("Hölder's inequality", "1/p+1/q=1を満たすp,q>1(またはp=1,q=∞などの端点)に対し、‖fg‖₁≤‖f‖ₚ‖g‖_qが成り立つという、Lp空間における基本的な不等式。ヘルダーの不等式。", "名詞句", "Hölder's inequality generalizes the Cauchy-Schwarz inequality and plays a central role in establishing that Lp spaces are normed vector spaces.", "数学", "930"),
    ("linear functional", "ベクトル空間からその係数体(実数や複素数)への線形写像のこと。線形汎関数。", "名詞句", "A linear functional maps vectors in a vector space to scalars while preserving addition and scalar multiplication.", "数学", "880"),
    ("Lp space", "p乗が積分可能な(可測)関数全体からなる、関数解析における基本的な関数空間のクラスのこと。Lp空間。", "名詞句", "An Lp space consists of measurable functions whose p-th power is integrable, equipped with the norm obtained by taking the p-th root of that integral.", "数学", "920"),
    ("Minkowski inequality", "Lp空間におけるノルムについて、三角不等式‖f+g‖ₚ≤‖f‖ₚ+‖g‖ₚが成り立つことを主張する不等式。ミンコフスキーの不等式。", "名詞句", "The Minkowski inequality shows that the Lp norm satisfies the triangle inequality, which is essential for Lp space to be a genuine normed vector space.", "数学", "930"),
    ("normed vector space", "各ベクトルに「長さ」に相当する非負の実数(ノルム)を対応させる関数が定義されたベクトル空間のこと。ノルム空間。", "名詞句", "A normed vector space equips each vector with a length-like quantity called a norm, satisfying positivity, scalability, and the triangle inequality.", "数学", "870"),
    ("orthogonal projection", "ヒルベルト空間の部分空間に対し、各ベクトルをその部分空間内で最も近い点へ対応させる写像のこと。直交射影。", "名詞句", "The orthogonal projection of a vector onto a closed subspace is the unique point in that subspace closest to the original vector.", "数学", "920"),
    ("orthonormal basis", "互いに直交し、かつ各ベクトルの長さが1であるようなベクトルの集合であって、空間全体を(ヒルベルト空間の意味で)張るもの。正規直交基底。", "名詞句", "An orthonormal basis consists of mutually orthogonal unit vectors that span the entire space in the sense relevant to Hilbert spaces.", "数学", "900"),
    ("Parseval's theorem", "関数(またはベクトル)を正規直交基底で展開したとき、その係数の2乗の和(積分)が元の関数のノルムの2乗に等しくなるという定理。パーセバルの定理。", "名詞句", "Parseval's theorem states that the sum of the squared Fourier coefficients of a function equals the squared norm of that function.", "数学", "900"),
    ("Plancherel theorem", "フーリエ変換が(適切な定数倍のもとで)L2空間のノルムを保つ、すなわちユニタリ変換であることを主張する定理。プランシュレルの定理。", "名詞句", "The Plancherel theorem states that the Fourier transform is a unitary operator on the space of square-integrable functions.", "数学", "930"),
    ("Riesz representation theorem", "ヒルベルト空間上の任意の有界線形汎関数が、ある一つのベクトルとの内積として一意に表せることを主張する定理。リースの表現定理。", "名詞句", "The Riesz representation theorem shows that every bounded linear functional on a Hilbert space can be written as the inner product with a unique vector.", "数学", "970"),
    ("self-adjoint operator", "随伴作用素が自分自身と一致する作用素、すなわちT=T*を満たす作用素のこと。自己随伴作用素。", "名詞句", "A self-adjoint operator satisfies T = T*, meaning it equals its own adjoint operator.", "数学", "930"),
    ("Sobolev space", "関数自身だけでなく、その(弱)微分もLp空間に属するという条件を課して定義される関数空間のこと。ソボレフ空間。", "名詞句", "A Sobolev space consists of functions whose weak derivatives up to a certain order also belong to an Lp space.", "数学", "950"),
    ("spectral theorem", "自己随伴作用素(や正規作用素・ユニタリ作用素)が、実数の固有値に対応する直交射影の重ね合わせとして表せる、あるいは適切な基底のもとで対角化できることを主張する一連の定理の総称。スペクトル定理。", "名詞句", "The spectral theorem states that every self-adjoint operator on a Hilbert space can be represented, in a suitable sense, as an integral over its real eigenvalues weighted by orthogonal projections.", "数学", "990"),
    ("tempered distribution", "シュワルツ空間(急減少関数の空間)上で定義された連続線形汎関数のこと。緩増加超関数、緩増加分布とも呼ばれる。フーリエ変換が自然に定義できる超関数のクラス。", "名詞句", "A tempered distribution is a continuous linear functional on the Schwartz space of rapidly decreasing smooth functions.", "数学", "990+"),
    ("test function", "超関数論において、コンパクトな台(値が0でない範囲が有界な閉集合)を持つ、無限回微分可能な関数のこと。試験関数。統計学における仮説検定とは無関係な概念である。", "名詞句", "A test function in distribution theory is an infinitely differentiable function with compact support, unrelated to statistical hypothesis testing.", "数学", "970"),
    ("unitary operator", "ヒルベルト空間上の全単射な線形作用素であって、内積(したがってノルム)を保つもの。すなわちU*U=UU*=Iを満たす作用素のこと。ユニタリ作用素。", "名詞句", "A unitary operator preserves the inner product of a Hilbert space and satisfies U*U = UU* = I.", "数学", "930"),
    ("weak convergence", "ノルム空間の点列(または関数列)が、任意の連続線形汎関数を通して見たときに収束するという、通常の(ノルムによる)収束よりも弱い収束の概念のこと。弱収束。", "名詞句", "A sequence converges weakly if, for every continuous linear functional, the sequence of values obtained by applying that functional converges.", "数学", "950"),
    ("weak derivative", "通常の意味では微分可能でない関数に対しても、部分積分の公式を満たすものとして定義される、一般化された意味での微分のこと。弱微分。", "名詞句", "The weak derivative of a function is defined by requiring it to satisfy the integration-by-parts formula against every test function.", "数学", "950"),
    ("Dirac delta function", "原点以外では値が0で、原点で無限大となり、全区間での積分が1となるという性質を持つ、厳密には通常の関数ではなく超関数として定義される「関数」。ディラックのデルタ関数。", "名詞句", "The Dirac delta function is often used to model an idealized point charge or an instantaneous impulse in physics.", "数学", "930"),
    ("Borel set", "位相空間の開集合から出発し、可算個の合併・共通部分・補集合をとる操作を繰り返すことで得られる集合。実数直線上ではボレル集合全体がシグマ集合体(ボレルσ-代数)をなし、測度論における「測定可能な集合」の標準的な出発点となる。", "名詞句", "Every open interval on the real line is a Borel set.", "数学", "970"),
    ("boundary value problem", "微分方程式に対して、解が満たすべき条件を独立変数の定義域の境界(端点や境界面)で与える問題。1点で条件をまとめて与える初期値問題と対比される。", "名詞句", "The boundary value problem specifies the temperature at both ends of the rod.", "数学", "880"),
    ("Brownian motion", "液体や気体中に浮遊する微粒子が、周囲の分子との衝突によって不規則に動き回る物理現象。また、その現象を数学的にモデル化した連続時間の確率過程(ウィーナー過程)を指すこともある。", "名詞句", "Robert Brown first observed Brownian motion in pollen grains suspended in water.", "数学", "910"),
    ("characteristic function (probability)", "確率変数Xの分布に対して φ(t) = E[e^{itX}] として定義される複素数値関数。確率密度関数が存在する場合はそのフーリエ変換に相当し、分布を一意に特徴づける。", "名詞句", "The characteristic function of a normal distribution is a Gaussian function of t.", "数学", "950"),
    ("conditional expectation", "ある事象や情報(シグマ集合体)が与えられた条件のもとでの確率変数の期待値。測度論的確率論では、シグマ集合体に関して定義される確率変数として厳密に定式化される。", "名詞句", "The conditional expectation of X given the sigma-algebra F is itself a random variable measurable with respect to F.", "数学", "930"),
    ("filtration (probability)", "時間とともに増加していくシグマ集合体の族{F_t}で、時刻tまでに観測可能な情報の全体を表す。確率過程の理論において、マルチンゲールや停止時刻の定義に不可欠な枠組み。", "名詞句", "A filtration represents the flow of information available to an observer over time.", "数学", "990+"),
    ("heat equation", "温度分布が時間とともにどのように拡散していくかを記述する偏微分方程式。∂u/∂t = k∇²u という形をとり、フーリエが熱伝導の研究の中で導入した。", "名詞句", "The heat equation describes how temperature diffuses through a solid object over time.", "数学", "880"),
    ("initial value problem", "微分方程式に対して、独立変数のある一点(通常は時刻の初期時点)における関数の値(および必要ならその導関数の値)を条件として与える問題。", "名詞句", "An initial value problem specifies the value of the solution at a single starting point.", "数学", "870"),
    ("Itô calculus", "ブラウン運動を含む確率過程、特に確率微分方程式を扱うための微積分体系。通常の微積分とは異なる補正項を持つ「伊藤の補題」と呼ばれる連鎖律を特徴とする。日本の数学者・伊藤清が1940年代に確立した。", "名詞句", "Itô calculus provides the mathematical tools needed to work with stochastic differential equations driven by Brownian motion.", "数学", "990+"),
    ("law of large numbers", "同じ確率分布に従う独立な確率変数の標本平均が、標本数を増やすにつれて母平均(期待値)に確率的に近づいていくという定理。大数の法則。", "名詞句", "The law of large numbers explains why the average of many coin flips approaches 0.5 as the number of flips increases.", "数学", "880"),
    ("Lebesgue integral", "測度の概念に基づいて定義される積分。関数の定義域(x軸)を分割するリーマン積分とは異なり、値域(y軸)側を分割することで、より広いクラスの関数に対して積分を定義できる。", "名詞句", "Henri Lebesgue introduced the Lebesgue integral in his 1902 doctoral dissertation.", "数学", "900"),
    ("martingale (probability)", "それまでの情報が与えられたとき、次の時点での値の条件付き期待値が現在の値と等しくなるという性質を持つ確率過程。「公平なゲーム」における財産の推移を数学的に一般化した概念。", "名詞句", "A martingale models a fair game in which the expected future fortune, given the past, equals the current fortune.", "数学", "970"),
    ("measurable function", "可測空間の間で定義される写像で、値域側の任意の可測集合の逆像が、定義域側でも可測集合になるという性質を持つ関数。確率論では、確率変数はこの意味で可測な関数として定義される。", "名詞句", "A random variable is defined mathematically as a measurable function from the sample space to the real numbers.", "数学", "950"),
    ("measure (mathematics)", "シグマ集合体の各元(集合)に対して非負の実数(または無限大)を対応させる関数で、可算加法性(互いに交わらない可算個の集合の和集合の値が、各集合の値の和に等しい)を満たすもの。長さ・面積・体積・確率を統一的に扱うための概念。", "名詞句", "A measure assigns a non-negative number to each set in a sigma-algebra, generalizing the notions of length, area, and volume.", "数学", "900"),
    ("moment generating function", "確率変数Xに対して M(t) = E[e^{tX}] として定義される関数。存在する場合、tによる微分を繰り返すことで、Xの各次のモーメント(平均・分散などの元になる量)を求めることができる。", "名詞句", "The moment generating function of a random variable, when it exists, uniquely determines its probability distribution.", "数学", "930"),
    ("ordinary differential equation", "1つの独立変数に関する未知関数とその導関数(1階以上)からなる方程式。複数の独立変数を含む偏微分方程式と対比される。", "名詞句", "An ordinary differential equation involves derivatives of a function of a single independent variable.", "数学", "850"),
    ("partial differential equation", "2つ以上の独立変数を持つ未知関数の偏導関数を含む方程式。熱方程式・波動方程式・ラプラス方程式などが代表例。", "名詞句", "A partial differential equation relates a function of several variables to its partial derivatives.", "数学", "870"),
    ("Poisson process", "一定期間内にランダムに発生する事象の回数を数える確率過程で、互いに交わらない時間区間での発生回数が独立であり、単位時間あたりの平均発生率が一定であるという性質を持つ。フランスの数学者シメオン・ドニ・ポアソンにちなむ。", "名詞句", "A Poisson process is often used to model the arrival of customers at a store over time.", "数学", "920"),
    ("sigma-algebra", "空集合を含み、補集合を取る操作と可算個の和集合を取る操作について閉じている集合族。測度論において「測定可能な集合の全体」を定める基礎的な概念。シグマ集合体(σ-代数)。", "名詞句", "A sigma-algebra must be closed under complementation and countable unions.", "数学", "990"),
    ("stationary distribution", "確率過程が時間発展しても分布が変化しないような確率分布。マルコフ連鎖のような確率過程では、初期分布によらず長期的に収束していく先の分布として現れることが多い。", "名詞句", "A stationary distribution remains unchanged as the underlying stochastic process evolves over time.", "数学", "920"),
    ("stochastic process", "時間や空間などの添字集合によってラベル付けされた確率変数の族。ランダムに変化する現象を数学的にモデル化するための枠組みで、マルコフ連鎖・ブラウン運動・ポアソン過程などは、いずれもこの一般的な枠組みに含まれる特殊な例にあたる。", "名詞句", "A stochastic process is a collection of random variables indexed by time or another parameter.", "数学", "900"),
    ("wave equation", "波の伝播を記述する偏微分方程式で、時間に関する2階の導関数が空間に関するラプラシアンに比例するという形をとる。ダランベールが弦の振動の研究の中で導いた。", "名詞句", "The wave equation describes how disturbances such as sound or light propagate through space over time.", "数学", "880"),
    ("dominated convergence theorem", "ある可積分な関数によって各項の絶対値が常に上から抑えられている関数列が概収束するならば、その極限関数も可積分であり、極限と積分の順序を交換できるという、ルベーグ積分論における基本定理。", "名詞句", "The dominated convergence theorem allows the limit and the integral to be interchanged when the sequence is bounded by an integrable function.", "数学", "980"),
    ("Radon-Nikodym derivative", "ある測度が別の測度に対して絶対連続であるとき、両者の関係を表す可測関数。ラドン=ニコディムの定理により存在が保証され、dν/dμ のように「密度」を表す記法で書かれる。", "名詞句", "The Radon-Nikodym derivative generalizes the notion of a probability density function to abstract measure spaces.", "数学", "990+"),
    ("Laplace transform", "関数f(t)に対して F(s) = ∫₀^∞ f(t)e^{-st}dt として定義される積分変換。微分方程式を代数方程式に変換して解く手法として、工学や物理学で広く用いられる。", "名詞句", "The Laplace transform converts a differential equation in the time domain into an algebraic equation in the s-domain.", "数学", "900"),
    ("Cauchy sequence", "数列の項番号が十分大きくなるにつれて、項同士の差がいくらでも小さくなっていくという性質を持つ数列。極限の存在をあらかじめ仮定せずに「収束しそうな数列」を特徴づけることができる。", "名詞句", "A Cauchy sequence is a sequence in which the terms become arbitrarily close to each other as the sequence progresses.", "数学", "850"),
    ("eigenfunction", "線形作用素(微分作用素など)Lに対して、Lf = λfを満たす、恒等的に0ではない関数fのこと。定数λはその固有関数に対応する固有値と呼ばれる。", "名詞句", "An eigenfunction of a linear differential operator satisfies the equation Lf equals lambda times f for some constant lambda.", "数学", "900"),
    ("vector field", "空間内の各点に対して1つのベクトルを対応させる写像。流体の速度分布や力の場(重力場・電場など)を数学的に表現する際に用いられる。", "名詞句", "A vector field assigns a vector to every point in space, such as the velocity of a fluid at each location.", "数学", "880"),]


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
        print("totals -> 数学:",
              conn.execute(
                  "SELECT COUNT(*) FROM words WHERE domain='数学'"
              ).fetchone()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
