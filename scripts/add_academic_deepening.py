# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""既存6分野(化学・物理・数学・経済学・経営学・生物学)の大学教養レベル
以上への深化、authored by Claude(2026-08-26・B23バックログ「既存ドメインの
大学教養レベル以上への深化」対応)。既存分野が薄かった生物学・経済学・
経営学を中心に、化学・物理・数学も含めて全6分野に真に大学教養レベル以上の
語彙を追加する。DB全体でenglishが既存語と衝突するものは除外。

No app / OpenAI API calls — hand-written(並列サブエージェントでドラフト後に
人手でdedup), inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_academic_deepening.py
仕上げ: 投入後に `python scripts/relevel.py` を実行(既存ドメインの
        DOMAIN_BASE/H900/H990/H990Pセットを用いてレベル再設定)。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("ADP", "ADP(アデノシン二リン酸)。ATPがリン酸を1つ失ってできる分子で、ATPの加水分解や再合成に関わる。", "名詞", "When ATP releases energy, it breaks down into ADP and a phosphate group.", "生物学", "850"),
    ("Calvin cycle", "カルビン回路。光合成の暗反応(光非依存反応)で、二酸化炭素を固定してグルコースなどの有機物を合成する一連の化学反応。", "名詞句", "In the Calvin cycle, carbon dioxide is fixed into organic molecules using ATP and NADPH.", "生物学", "950"),
    ("electron transport chain", "電子伝達系。ミトコンドリア内膜(または葉緑体のチラコイド膜)にあるタンパク質複合体の連鎖で、電子の移動を利用してプロトン勾配を作り、ATP合成を駆動する。", "名詞句", "The electron transport chain uses the energy from electron transfer to pump protons across the membrane.", "生物学", "900"),
    ("Krebs cycle (citric acid cycle)", "クエン酸回路(クレブス回路)。ミトコンドリアのマトリックスで進行する代謝回路で、アセチルCoAを酸化してNADH・FADH2・少量のATPを生成する。", "名詞句", "The Krebs cycle, also called the citric acid cycle, generates most of the electron carriers used in oxidative phosphorylation.", "生物学", "950"),
    ("oxidative phosphorylation", "酸化的リン酸化。電子伝達系で生じたプロトン勾配を利用してATP合成酵素がATPを合成する過程。", "名詞句", "Oxidative phosphorylation produces the majority of ATP generated during cellular respiration.", "生物学", "950"),
    ("NADH", "ニコチンアミドアデニンジヌクレオチドの還元型。代謝反応で生じる電子を運搬し、電子伝達系に渡す補酵素。", "名詞", "NADH carries high-energy electrons to the electron transport chain.", "生物学", "950"),
    ("FADH2", "フラビンアデニンジヌクレオチドの還元型。クエン酸回路で生成され、電子伝達系に電子を供給する補酵素。", "名詞", "FADH2 donates electrons to the electron transport chain at a later point than NADH.", "生物学", "950"),
    ("messenger RNA (mRNA)", "メッセンジャーRNA。DNAの遺伝情報を核からリボソームへ運び、タンパク質合成の鋳型となる一本鎖RNA。", "名詞句", "Messenger RNA carries the genetic code from the nucleus to the ribosome for protein synthesis.", "生物学", "850"),
    ("transfer RNA (tRNA)", "転移RNA。特定のアミノ酸を運び、mRNAのコドンに対応するアンチコドンを持つ小さなRNA分子。", "名詞句", "Each transfer RNA molecule carries a specific amino acid to the ribosome during translation.", "生物学", "900"),
    ("codon", "コドン。mRNA上の3つの塩基からなる配列で、特定のアミノ酸または翻訳の開始・終止を指定する。", "名詞", "Each codon on the mRNA strand corresponds to a specific amino acid or a stop signal.", "生物学", "900"),
    ("point mutation", "点突然変異。DNA配列中の1つの塩基対が別の塩基に置き換わる、挿入される、または欠失する突然変異。", "名詞句", "A single point mutation in the hemoglobin gene can cause sickle cell anemia.", "生物学", "900"),
    ("gene regulation", "遺伝子調節。細胞が特定の遺伝子の発現を必要な時・場所でオンまたはオフに制御する仕組み。", "名詞句", "Gene regulation allows cells with identical DNA to develop into very different cell types.", "生物学", "900"),
    ("epigenetics", "エピジェネティクス。DNA塩基配列を変えずに、DNAメチル化やヒストン修飾などによって遺伝子発現が制御・継承される仕組みを研究する分野。", "名詞", "Epigenetics explains how identical twins can develop different traits despite sharing the same DNA.", "生物学", "950"),
    ("PCR (polymerase chain reaction)", "ポリメラーゼ連鎖反応(PCR)。DNAポリメラーゼを用いて特定のDNA配列を試験管内で指数関数的に増幅する技術。", "名詞句", "PCR can amplify a tiny sample of DNA into millions of copies within hours.", "生物学", "900"),
    ("allele frequency", "対立遺伝子頻度。ある集団内で特定の対立遺伝子が全対立遺伝子に占める割合。", "名詞句", "Allele frequency in a population can shift over generations due to natural selection.", "生物学", "950"),
    ("Hardy-Weinberg equilibrium", "ハーディ・ワインベルグ平衡。自然選択や突然変異などの進化的要因が働かない理想的な集団では、対立遺伝子頻度と遺伝子型頻度が世代を超えて一定に保たれるという原理。", "名詞句", "A population in Hardy-Weinberg equilibrium shows no change in allele frequencies over time.", "生物学", "990"),
    ("genetic drift", "遺伝的浮動。偶然の要因によって集団内の対立遺伝子頻度がランダムに変動する現象で、特に小さな集団で顕著。", "名詞句", "Genetic drift can cause allele frequencies to change randomly, especially in small populations.", "生物学", "950"),
    ("gene flow", "遺伝子流動。個体の移入・移出や交配を通じて、異なる集団間で対立遺伝子が移動すること。", "名詞句", "Gene flow between populations tends to reduce genetic differences between them.", "生物学", "900"),
    ("polygenic trait", "多遺伝子形質。複数の遺伝子の相互作用によって決定される形質で、連続的な変異を示すことが多い(身長など)。", "名詞句", "Human height is a polygenic trait influenced by many genes and environmental factors.", "生物学", "950"),
    ("genetic linkage", "遺伝的連鎖。同じ染色体上に近接して存在する遺伝子が、減数分裂の際に一緒に遺伝しやすい現象。", "名詞句", "Genetic linkage means that genes located close together on a chromosome are inherited together more often than expected by chance.", "生物学", "950"),
    ("speciation", "種分化。1つの祖先種から生殖的に隔離された新しい種が形成される進化的過程。", "名詞", "Geographic isolation can lead to speciation as populations evolve independently.", "生物学", "950"),
    ("phylogeny", "系統発生。生物種や分類群間の進化的な類縁関係の歴史。しばしば系統樹で表される。", "名詞", "Scientists use DNA sequence comparisons to reconstruct the phylogeny of related species.", "生物学", "950"),
    ("common descent", "共通祖先(共通起源)。すべての生物が単一またはごく少数の共通祖先から進化してきたとする概念。", "名詞句", "The theory of common descent holds that all living organisms share a single ancestral origin.", "生物学", "900"),
    ("adaptive radiation", "適応放散。1つの祖先種から短期間に多様な生態的地位に適応した多数の種が急速に分化する現象。", "名詞句", "The Galápagos finches are a classic example of adaptive radiation.", "生物学", "950"),
    ("convergent evolution", "収斂進化。系統的に離れた生物が、類似した環境に適応することで独立に似た形質を獲得する進化現象。", "名詞句", "The wings of bats and birds are a result of convergent evolution, not a shared ancestor with wings.", "生物学", "900"),
    ("trophic level", "栄養段階。食物連鎖における生物の位置づけ(生産者、一次消費者、二次消費者など)。", "名詞句", "Energy decreases significantly as it moves up each trophic level in an ecosystem.", "生物学", "900"),
    ("keystone species", "キーストーン種。その個体数や生物量に比して不釣り合いに大きな影響を生態系に与える種。", "名詞句", "Sea otters are a keystone species that help control sea urchin populations in kelp forests.", "生物学", "950"),
    ("mutualism", "相利共生。共生の一形態で、両方の種が利益を得る関係。", "名詞", "The relationship between bees and flowering plants is a classic example of mutualism.", "生物学", "900"),
    ("commensalism", "片利共生。共生の一形態で、一方の種が利益を得て、もう一方の種には利益も害もない関係。", "名詞", "Barnacles attaching to a whale without harming it is an example of commensalism.", "生物学", "950"),
    ("parasitism", "寄生。共生の一形態で、寄生者が宿主から利益(栄養など)を得る一方、宿主には害を及ぼす関係。", "名詞", "Tapeworms exhibit parasitism by living in a host's intestines and absorbing its nutrients.", "生物学", "900"),
    ("ecological niche", "生態的地位(ニッチ)。生物が生態系内で果たす役割や、利用する資源、生息環境の総体。", "名詞句", "No two species can occupy the exact same ecological niche indefinitely without competition.", "生物学", "900"),
    ("carrying capacity", "環境収容力。ある環境が持続的に支えられる最大の個体数。", "名詞句", "When a population exceeds the carrying capacity of its environment, resources become scarce.", "生物学", "900"),
    ("osmosis", "浸透。半透膜を通して、水が溶質濃度の低い側から高い側へ移動する現象。", "名詞", "Water moves into the cell by osmosis when the surrounding solution is hypotonic.", "生物学", "800"),
    ("diffusion", "拡散。分子が濃度の高い場所から低い場所へ自然に移動する現象。", "名詞", "Oxygen enters the bloodstream from the lungs by diffusion.", "生物学", "800"),
    ("active transport", "能動輸送。エネルギー(ATP)を消費して、物質を濃度勾配に逆らって細胞膜を通過させる輸送機構。", "名詞句", "The sodium-potassium pump uses active transport to move ions against their concentration gradient.", "生物学", "850"),
    ("cell signaling", "細胞シグナル伝達。細胞が化学的なシグナルを受け取り、伝達し、反応することで機能を調節する仕組み。", "名詞句", "Cell signaling allows cells to coordinate their behavior in response to hormones and other molecules.", "生物学", "950"),
    ("receptor (biology)", "受容体。細胞膜や細胞内に存在し、特定のシグナル分子(ホルモンや神経伝達物質など)と結合してその情報を細胞内に伝えるタンパク質。", "名詞句", "A hormone binds to its specific receptor on the surface of a target cell to trigger a response.", "生物学", "850"),
    ("general equilibrium", "一般均衡(理論)。個々の市場ごとの均衡(部分均衡)ではなく、経済内のすべての市場が相互に影響し合いながら同時に均衡する状態を分析する経済理論。", "名詞句", "General equilibrium theory examines how prices adjust simultaneously across all markets in an economy.", "経済学", "950"),
    ("welfare economics", "厚生経済学。資源配分が社会全体の厚生(well-being)にどう影響するかを、効率性や公平性の観点から分析する経済学の一分野。", "名詞句", "Welfare economics provides the theoretical foundation for evaluating whether a policy makes society better off overall.", "経済学", "900"),
    ("Pigouvian tax", "ピグー税。公害などの負の外部性を市場価格に内部化させるために課される税。外部費用を生産者・消費者に負担させ、社会的に最適な生産量に近づける。", "名詞句", "A carbon tax is a classic example of a Pigouvian tax designed to correct the externality of pollution.", "経済学", "950"),
    ("Coase theorem", "コースの定理。取引費用がゼロで財産権が明確に定義されていれば、外部性の問題は当事者間の自発的交渉によって効率的に解決されるとする定理。ロナルド・コースが提唱。", "名詞句", "The Coase theorem suggests that, absent transaction costs, private negotiation can resolve externality problems without government intervention.", "経済学", "970"),
    ("public goods", "公共財。非競合性(誰かの消費が他者の消費を妨げない)と非排除性(対価を払わない人を排除できない)という性質を持つ財。国防や灯台などが典型例。", "名詞句", "National defense is a textbook example of a public good because it is both non-excludable and non-rivalrous.", "経済学", "900"),
    ("tragedy of the commons", "共有地の悲劇。誰でも自由にアクセスできる共有資源(共有地、漁場など)が、個々の利己的な利用によって過剰に消費され、枯渇してしまう現象。", "名詞句", "Overfishing in international waters is often cited as a modern tragedy of the commons.", "経済学", "920"),
    ("monopolistic competition", "独占的競争。多数の企業が差別化された類似の財を供給し、それぞれがある程度の価格決定力を持つが参入・退出は自由である市場構造。完全競争と独占の中間形態。", "名詞句", "The restaurant industry is often modeled as monopolistic competition, with many firms offering differentiated products.", "経済学", "920"),
    ("price discrimination", "価格差別。同一の財・サービスに対して、消費者ごと・市場ごとに異なる価格を設定する慣行。企業が消費者余剰の一部を利潤に転化する手段となる。", "名詞句", "Airlines practice price discrimination by charging different fares depending on when a ticket is purchased.", "経済学", "900"),
    ("consumer surplus", "消費者余剰。消費者が財に対して支払ってもよいと考える金額(留保価格)と実際に支払った価格との差の合計。市場取引から消費者が得る便益を表す。", "名詞句", "A decrease in the market price generally increases consumer surplus for buyers.", "経済学", "880"),
    ("producer surplus", "生産者余剰。生産者が実際に受け取る価格と、その財を供給してもよいと考える最低価格(限界費用)との差の合計。市場取引から生産者が得る便益を表す。", "名詞句", "Producer surplus rises when the market price exceeds a firm's marginal cost of production.", "経済学", "880"),
    ("Edgeworth box", "エッジワース・ボックス。2人の消費者(または2財)の間での資源配分と交換を図示する分析ツール。契約曲線やパレート効率的な配分を視覚化する際に用いられる。", "名詞句", "The Edgeworth box is used in microeconomics to illustrate the set of Pareto-efficient allocations between two consumers.", "経済学", "970"),
    ("IS-LM model", "IS-LMモデル。財市場の均衡(IS曲線)と貨幣市場の均衡(LM曲線)を組み合わせ、利子率と国民所得の同時決定を分析するケインズ経済学のマクロモデル。", "名詞句", "The IS-LM model shows how shifts in fiscal and monetary policy affect interest rates and output in the short run.", "経済学", "950"),
    ("Solow growth model", "ソロー成長モデル。資本蓄積、労働人口の増加、技術進歩を要因として長期的な経済成長を説明する新古典派の成長理論。", "名詞句", "The Solow growth model predicts that, absent technological progress, economies will converge to a steady-state level of output per worker.", "経済学", "970"),
    ("endogenous growth theory", "内生的成長理論。技術進歩を外生的な要因としてではなく、研究開発や人的資本投資など経済システム内部の要因によって説明しようとする成長理論。", "名詞句", "Endogenous growth theory argues that government investment in education and R&D can permanently raise an economy's growth rate.", "経済学", "970"),
    ("Ricardian equivalence", "リカードの等価定理。政府が減税を国債発行で賄っても、将来の増税を予想する合理的な消費者は貯蓄を増やすため、総需要や消費行動には影響しないとする仮説。", "名詞句", "Ricardian equivalence implies that a deficit-financed tax cut may not stimulate consumption if households anticipate future tax increases.", "経済学", "980"),
    ("time inconsistency", "時間不整合性(動的不整合)。事前に最適とされた政策が、時間の経過とともに政策当局にとって遵守する誘因を失ってしまう問題。中央銀行のインフレ抑制のコミットメント問題などで議論される。", "名詞句", "The time inconsistency problem explains why central banks benefit from credible commitment devices like inflation targeting.", "経済学", "970"),
    ("inflation targeting", "インフレ・ターゲティング。中央銀行が特定のインフレ率(目標値)を公表し、それを達成するように金融政策を運営する枠組み。", "名詞句", "Many central banks adopted inflation targeting in the 1990s to anchor public expectations about future price stability.", "経済学", "900"),
    ("Taylor rule", "テイラー・ルール。インフレ率と産出ギャップに応じて中央銀行が政策金利をどう調整すべきかを示す経験則(数式)。ジョン・テイラーが提唱。", "名詞句", "According to the Taylor rule, the central bank should raise interest rates when inflation exceeds its target.", "経済学", "950"),
    ("real business cycle theory", "実物的景気循環理論。景気変動の主因を貨幣的要因ではなく、技術進歩などの実物的(供給側の)ショックに求める新古典派マクロ経済理論。", "名詞句", "Real business cycle theory attributes economic fluctuations to random shocks in productivity rather than changes in aggregate demand.", "経済学", "970"),
    ("sticky wages", "賃金の下方硬直性(名目賃金の粘着性)。労働市場において名目賃金が需給の変化に応じて即座には調整されない現象。ケインズ経済学における不況・失業の説明要因の一つ。", "名詞句", "Sticky wages help explain why labor markets do not clear immediately after a negative demand shock, resulting in involuntary unemployment.", "経済学", "920"),
    ("natural rate of unemployment", "自然失業率。経済がインフレを加速させることなく持続可能な水準にあるときの失業率。摩擦的失業と構造的失業から成り、循環的失業を含まない。", "名詞句", "The natural rate of unemployment reflects frictional and structural factors in the labor market rather than cyclical downturns.", "経済学", "920"),
    ("output gap", "GDPギャップ(産出ギャップ)。実際のGDPと、経済が潜在的に生産できる最大限の産出量(潜在GDP)との差。景気の過熱・停滞の度合いを示す指標。", "名詞句", "A positive output gap indicates that the economy is operating above its potential, often signaling inflationary pressure.", "経済学", "900"),
    ("bounded rationality", "限定合理性。人間の意思決定能力には情報処理能力・時間・知識などの制約があるため、完全に合理的な最適化ではなく満足できる水準で意思決定を行うという概念。ハーバート・サイモンが提唱。", "名詞句", "Herbert Simon's concept of bounded rationality challenges the assumption that individuals always make perfectly optimal decisions.", "経済学", "920"),
    ("prospect theory", "プロスペクト理論。人々は確率的な意思決定において絶対的な資産水準ではなく基準点からの利得・損失として評価し、損失を利得よりも重く感じる傾向があるとする行動経済学の理論。カーネマンとトベルスキーが提唱。", "名詞句", "Prospect theory explains why people often feel the pain of a loss more intensely than the pleasure of an equivalent gain.", "経済学", "950"),
    ("loss aversion", "損失回避性。同額の利得よりも損失のほうが心理的にはるかに大きな影響を与えるという行動経済学上の傾向。プロスペクト理論の中心的要素。", "名詞句", "Loss aversion can cause investors to hold onto losing stocks too long, hoping to avoid realizing a loss.", "経済学", "900"),
    ("anchoring bias", "アンカリング効果(係留バイアス)。意思決定の際、最初に提示された数値や情報(アンカー)に無意識に影響され、その後の判断がその値に近づいてしまう認知バイアス。", "名詞句", "Anchoring bias can lead consumers to judge a discounted price as a good deal simply because it is compared to a higher original price.", "経済学", "880"),
    ("nudge theory", "ナッジ理論。人々の選択の自由を制限したり経済的インセンティブを大きく変えたりすることなく、選択の環境(デフォルト設定など)を工夫して望ましい行動を促す行動経済学的アプローチ。セイラーとサンスティーンが提唱。", "名詞句", "Nudge theory suggests that simply making retirement savings the default option can significantly increase participation rates.", "経済学", "900"),
    ("institutional economics", "制度派経済学。法律、慣習、組織などの社会的制度が経済行動や資源配分に与える影響を重視する経済学の学派。", "名詞句", "Institutional economics emphasizes how property rights and legal frameworks shape economic outcomes over time.", "経済学", "920"),
    ("transaction cost economics", "取引費用の経済学。市場取引に伴う情報収集・交渉・契約履行監視などのコスト(取引費用)が、企業の組織形態や境界の決定に与える影響を分析する経済学の分野。オリバー・ウィリアムソンが発展させた。", "名詞句", "Transaction cost economics helps explain why firms choose to produce components in-house rather than purchasing them from external suppliers.", "経済学", "970"),
    ("Heckscher-Ohlin model", "ヘクシャー=オリーン・モデル。各国が相対的に豊富に保有する生産要素(資本や労働)を集約的に使用する財の生産に比較優位を持ち、それを輸出するとする国際貿易理論。", "名詞句", "The Heckscher-Ohlin model predicts that a capital-abundant country will export capital-intensive goods.", "経済学", "970"),
    ("terms of trade", "交易条件。ある国の輸出財価格と輸入財価格の比率。交易条件の改善は、同じ量の輸出でより多くの輸入財を購入できることを意味する。", "名詞句", "A rise in oil prices improved the terms of trade for oil-exporting nations.", "経済学", "920"),
    ("balance of payments", "国際収支。一定期間における一国の対外的な取引(財・サービス・資本の流出入)を体系的に記録した統計。経常収支と資本収支から構成される。", "名詞句", "A persistent balance of payments deficit can force a country to draw down its foreign exchange reserves.", "経済学", "900"),
    ("purchasing power parity", "購買力平価。異なる通貨間の為替レートは、同一の財・サービスバスケットが両国で同じ購買力を持つように決まるべきだとする理論。長期的な為替レートの決定理論として用いられる。", "名詞句", "According to purchasing power parity, exchange rates should adjust so that identical goods cost the same across countries.", "経済学", "900"),
    ("capital account", "資本収支。国際収支のうち、対外直接投資・証券投資・金融派生商品取引などの資本移動を記録する項目。", "名詞句", "Foreign direct investment inflows are recorded in the capital account of the balance of payments.", "経済学", "880"),
    ("trade liberalization", "貿易自由化。関税や輸入割当などの貿易障壁を撤廃・緩和し、国境を越えた財・サービスの取引を促進する政策。", "名詞句", "Trade liberalization under the WTO has significantly reduced average tariff rates across member countries.", "経済学", "850"),
    ("regression analysis", "回帰分析。従属変数と一つまたは複数の独立変数との関係を統計的に推定する手法。経済学における実証分析の基本的なツール。", "名詞句", "Economists use regression analysis to estimate how changes in interest rates affect consumer spending.", "経済学", "850"),
    ("endogeneity", "内生性。説明変数が誤差項と相関している統計的な問題。逆の因果関係、欠落変数、測定誤差などが原因となり、回帰推定の一致性を損なう。", "名詞", "Endogeneity between education and wages makes it difficult to estimate the true causal effect of schooling on earnings.", "経済学", "970"),
    ("instrumental variable", "操作変数。内生性の問題を解決するために用いられる、説明変数とは相関するが誤差項とは無相関である変数。因果効果の推定に用いられる。", "名詞句", "Researchers used rainfall as an instrumental variable to estimate the causal effect of agricultural income on conflict.", "経済学", "970"),
    ("causal inference", "因果推論。単なる相関関係ではなく、ある変数が別の変数に及ぼす真の因果的効果を統計的手法によって特定しようとする方法論。", "名詞句", "Causal inference methods allow economists to distinguish correlation from a genuine cause-and-effect relationship.", "経済学", "950"),
    ("natural experiment", "自然実験。研究者が意図的に操作したのではなく、政策変更や自然災害などによって偶発的に生じた状況を利用して因果関係を推定する実証研究の手法。", "名詞句", "The introduction of a minimum wage law in one state but not a neighboring state provided a natural experiment for economists.", "経済学", "920"),
    ("dynamic capabilities", "急速に変化する環境において、企業が内部・外部の資源を統合・構築・再構成する組織的能力。単なる資源保有ではなく「資源を動かす力」に注目する経営学の理論(ティースらが提唱)。", "名詞句", "The firm's dynamic capabilities allowed it to reconfigure its resources quickly when the market shifted.", "経営学", "950"),
    ("real options theory", "不確実性の高い投資判断において、将来の意思決定の柔軟性(延期・拡大・縮小・撤退の選択権)に経済的価値を認め、金融オプション理論を応用して評価する戦略理論。", "名詞句", "Using real options theory, the company valued the flexibility to delay its entry into the emerging market.", "経営学", "970"),
    ("disruptive innovation", "当初は主流市場で性能が劣るものの、低価格や利便性で新たな顧客層を開拓し、やがて既存の主要企業を市場から駆逐する革新のプロセス。クレイトン・クリステンセンが提唱。", "名詞句", "Streaming services were a disruptive innovation that eventually displaced traditional video rental chains.", "経営学", "900"),
    ("first-mover advantage", "新市場や新技術にいち早く参入することで得られる優位性(ブランド認知、規模の経済、顧客のスイッチングコストなど)。", "名詞句", "The company's first-mover advantage in electric vehicles gave it a dominant share before competitors caught up.", "経営学", "850"),
    ("network effects", "製品やサービスの利用者が増えるほど、各利用者にとっての価値が高まる現象。プラットフォームビジネスの競争優位の源泉として重視される。", "名詞句", "Social media platforms grow in value through network effects as more users join.", "経営学", "850"),
    ("economies of scope", "単一製品の生産量拡大による規模の経済(economies of scale)とは異なり、複数の製品・事業を同一企業内で展開することでコストを節約できる効果。", "名詞句", "The conglomerate achieved economies of scope by sharing R&D and distribution across multiple product lines.", "経営学", "900"),
    ("absorptive capacity", "企業が外部の新しい知識や情報を認識・吸収し、自社の事業に活用する能力。イノベーション研究で重視される概念。", "名詞句", "Firms with strong absorptive capacity are better able to exploit external research and turn it into new products.", "経営学", "970"),
    ("experience curve", "累積生産量が増えるほど単位当たりコストが一定の割合で低下するという経験則。規模の経済に加え、習熟効果や工程改善を含む広い概念(BCGが提唱)。", "名詞句", "Because of the experience curve, unit costs fell steadily as cumulative production volume doubled.", "経営学", "930"),
    ("coopetition", "競合企業同士が特定の領域では協力し合いながら、他の領域では競争を続ける戦略的関係。ブランデンバーガーとネイルバフが提唱した造語。", "名詞", "Coopetition between the two rival airlines allowed them to share maintenance facilities while still competing for passengers.", "経営学", "970"),
    ("net present value (NPV)", "将来のキャッシュフローを現在価値に割り引いて合計し、初期投資額を差し引いた値。投資案の採否を判断する代表的な企業金融の指標。", "名詞句", "The project was approved because its net present value was positive at the company's discount rate.", "経営学", "900"),
    ("internal rate of return (IRR)", "投資案の正味現在価値(NPV)がちょうどゼロになる割引率。資本コストと比較して投資の採算性を判断するために用いられる。", "名詞句", "The internal rate of return on the new plant exceeded the company's hurdle rate, so the investment went ahead.", "経営学", "900"),
    ("weighted average cost of capital (WACC)", "企業が資金調達に用いる負債と自己資本それぞれのコストを、資本構成の比率で加重平均した値。投資判断の割引率としてよく使われる。", "名詞句", "Analysts used the company's weighted average cost of capital to discount its projected free cash flows.", "経営学", "950"),
    ("capital asset pricing model (CAPM)", "資産のリスク(ベータ値)と市場全体のリスクプレミアムから、投資家が要求する期待収益率を算出するファイナンス理論のモデル。", "名詞句", "The capital asset pricing model was used to estimate the stock's expected return based on its beta.", "経営学", "970"),
    ("leveraged buyout (LBO)", "買収資金の大部分を借入金(負債)で調達し、対象企業の資産やキャッシュフローを担保に企業を買収する手法。プライベートエクイティファンドが多用する。", "名詞句", "The private equity firm financed the leveraged buyout mostly with debt secured against the target company's assets.", "経営学", "950"),
    ("mergers and acquisitions (M&A)", "企業の合併(merger)と買収(acquisition)の総称。企業戦略として事業拡大や多角化、シナジー獲得を目的に行われる。", "名詞句", "The tech giant grew rapidly through a series of mergers and acquisitions over the past decade.", "経営学", "850"),
    ("free cash flow", "営業活動によって生み出したキャッシュから、設備投資などの必要な支出を差し引いた後、企業が自由に使えるキャッシュフロー。企業価値評価の基礎となる。", "名詞句", "Investors valued the company based on its projected free cash flow over the next ten years.", "経営学", "900"),
    ("capital structure", "企業が事業資金をどのように負債と自己資本で構成しているかを示す割合。財務レバレッジや資本コストに影響する。", "名詞句", "The firm adjusted its capital structure by issuing more debt to take advantage of low interest rates.", "経営学", "900"),
    ("agency cost", "経営者(エージェント)と株主(プリンシパル)の利害が一致しないことから生じるコスト(監視コスト、契約コスト、機会損失など)。エージェンシー理論の中心概念。", "名詞句", "Stock options are often used to align management's interests with shareholders' and reduce agency costs.", "経営学", "950"),
    ("poison pill", "敵対的買収の脅威に対抗するため、対象企業が既存株主に割安で新株を発行する権利を与えるなどして、買収コストを引き上げる防衛策。", "名詞句", "The board adopted a poison pill to make a hostile takeover prohibitively expensive for the acquirer.", "経営学", "950"),
    ("capital budgeting", "企業がNPVやIRRなどの手法を用いて、長期的な設備投資やプロジェクトへの資金配分を計画・評価するプロセス。", "名詞句", "The finance team used capital budgeting techniques to rank competing investment projects.", "経営学", "900"),
    ("balanced scorecard", "財務指標だけでなく、顧客、内部プロセス、学習と成長という4つの視点から企業の業績を総合的に管理する経営管理手法(キャプランとノートンが提唱)。", "名詞句", "The company implemented a balanced scorecard to track performance across financial and non-financial dimensions.", "経営学", "900"),
    ("knowledge management", "組織内に散在する知識(暗黙知・形式知)を体系的に収集・共有・活用し、競争優位につなげる経営活動。", "名詞句", "The consulting firm invested heavily in knowledge management systems to capture lessons learned from past projects.", "経営学", "850"),
    ("organizational ambidexterity", "既存事業の効率化(exploitation)と新規事業の探索(exploration)という相反する活動を、組織として同時に高いレベルで両立させる能力。", "名詞句", "Organizational ambidexterity allowed the firm to keep improving its core business while investing in disruptive new ventures.", "経営学", "970"),
    ("psychological safety", "チームメンバーが対人関係上のリスク(意見の対立、失敗の告白、質問など)を恐れずに発言できると感じる職場の心理状態。エイミー・エドモンドソンの研究で有名。", "名詞句", "Teams with high psychological safety are more willing to admit mistakes and raise concerns early.", "経営学", "900"),
    ("high-reliability organization", "原子力発電所や航空管制のように、事故が許されない高リスク環境下でありながら、極めて低い事故率を維持する組織。組織論における研究対象。", "名詞句", "Aircraft carriers are often studied as high-reliability organizations because they operate safely under extreme complexity and risk.", "経営学", "970"),
    ("learning organization", "組織全体が継続的に知識を創造・獲得し、自らの行動を変化させていく能力を備えた組織のあり方。ピーター・センゲの著作で広まった概念(既存語の「organizational learning=組織学習」がそのプロセス自体を指すのに対し、こちらは組織のあり方・目指す姿を指す)。", "名詞句", "Senge argued that a true learning organization continuously expands its capacity to create its own future.", "経営学", "900"),
    ("tacit knowledge", "言語化・マニュアル化が難しい、経験や勘に基づく知識。野中郁次郎のSECIモデルなど、ナレッジマネジメント理論の中心概念で、形式知(explicit knowledge)と対比される。", "名詞句", "Much of the veteran engineer's expertise was tacit knowledge that was difficult to transfer through manuals alone.", "経営学", "950"),
    ("double-loop learning", "問題が生じた際に、行動そのものだけでなく、その行動の前提となる価値観や方針までさかのぼって見直す学習様式。単に誤りを修正するシングルループ学習と対比される(アージリスが提唱)。", "名詞句", "Double-loop learning pushed the team to question its underlying assumptions, not just fix the immediate error.", "経営学", "980"),
    ("customer relationship management (CRM)", "顧客との関係を体系的に管理し、顧客満足度やロイヤルティ、収益性を高めるための戦略・手法・システムの総称。", "名詞句", "The sales team relied on their customer relationship management software to track every interaction with clients.", "経営学", "800"),
    ("brand positioning", "競合他社と比較して、自社ブランドが顧客の心の中でどのような独自の位置づけを占めるかを設計するマーケティング戦略。", "名詞句", "The company's brand positioning emphasized affordability without sacrificing quality.", "経営学", "850"),
    ("disruptive technology", "既存の製品・サービスの前提を覆し、市場構造そのものを変えてしまう技術。「disruptive innovation」がそのプロセス・戦略理論を指すのに対し、こちらは技術そのものを指す。", "名詞句", "Digital photography was a disruptive technology that rendered traditional film cameras obsolete.", "経営学", "880"),
    ("switching costs", "顧客が現在利用している製品・サービスから他社のものへ乗り換える際に発生する金銭的・時間的・心理的コスト。高いほど顧客の維持率が高まる。", "名詞句", "High switching costs made customers reluctant to leave the software platform even when cheaper alternatives appeared.", "経営学", "850"),
    ("first-mover disadvantage", "市場に最初に参入した企業が、後発企業に比べてかえって不利になる現象(先行投資の負担、技術の陳腐化、後発企業による模倣・改良など)。", "名詞句", "The pioneer suffered a first-mover disadvantage as later entrants learned from its costly mistakes and offered cheaper alternatives.", "経営学", "930"),
    ("two-sided market", "プラットフォームが二つの異なる顧客グループ(例: 買い手と売り手)を結びつけ、双方のネットワーク効果によって価値を生み出す市場構造。", "名詞句", "Ride-hailing apps operate as a two-sided market, connecting drivers on one side with passengers on the other.", "経営学", "950"),
    ("just-in-time (JIT)", "必要な部品や製品を、必要な時に必要な量だけ生産・調達する生産管理方式。在庫を最小限に抑え、無駄を排除する。トヨタ生産方式の中核。", "名詞句", "The factory's just-in-time system meant parts arrived from suppliers only hours before they were needed on the line.", "経営学", "850"),
    ("lean management", "顧客にとって価値を生まない活動(ムダ)を徹底的に排除し、プロセス全体の効率と品質を高める経営手法。トヨタ生産方式を起源とする。", "名詞句", "The hospital adopted lean management principles to reduce patient waiting times and eliminate wasted steps.", "経営学", "850"),
    ("total quality management (TQM)", "品質向上を経営の中心課題と位置づけ、全社員が継続的に業務プロセスを改善していく経営哲学・手法。", "名詞句", "Under total quality management, every employee was responsible for identifying and fixing quality issues, not just the inspection team.", "経営学", "850"),
    ("supply chain resilience", "自然災害や地政学リスク、需要変動などの外部ショックに対して、供給網が機能を維持または迅速に回復する能力。", "名詞句", "The pandemic exposed weaknesses in supply chain resilience, prompting companies to diversify their suppliers.", "経営学", "900"),
    ("theory of constraints", "システム全体の産出量は、最も制約となっているボトルネック工程によって決まるとし、その制約を特定・改善することで全体最適を図る経営理論(ゴールドラットが提唱)。", "名詞句", "Applying the theory of constraints, the plant manager focused improvement efforts on the single bottleneck machine limiting output.", "経営学", "950"),
    ("bullwhip effect", "サプライチェーンの下流(小売)における需要の小さな変動が、上流(卸売・製造業者)にさかのぼるにつれて増幅されていく現象。在庫の過剰・不足を招く。", "名詞句", "Small fluctuations in retail demand were amplified into large swings in factory orders due to the bullwhip effect.", "経営学", "950"),
    ("nucleophile", "求核剤(電子対を与えて反応する、電子豊富な原子・分子・イオン)。求電子剤と対をなす有機反応機構の基本概念。", "名詞", "The hydroxide ion acts as a strong nucleophile in the SN2 reaction.", "化学", "950"),
    ("electrophile", "求電子剤(電子対を受け取ろうとする、電子不足の原子・分子・イオン)。求核剤の反応相手となる化学種。", "名詞", "The carbonyl carbon behaves as an electrophile, attracting nucleophilic attack.", "化学", "950"),
    ("SN1 reaction", "一分子求核置換反応。律速段階でカルボカチオン中間体を経由し、反応速度は基質濃度のみに依存する(SN2反応と対比される)。", "名詞句", "Tertiary alkyl halides typically react via an SN1 reaction rather than SN2.", "化学", "970"),
    ("enantiomer", "鏡像異性体(エナンチオマー)。互いに実像と鏡像の関係にあり、重ね合わせることができない一対の立体異性体。", "名詞", "The two enantiomers of a chiral molecule rotate plane-polarized light in opposite directions.", "化学", "970"),
    ("diastereomer", "ジアステレオマー(非鏡像立体異性体)。複数の不斉中心を持つ分子において、鏡像関係にない立体異性体。", "名詞", "Unlike enantiomers, diastereomers have different physical properties such as melting point.", "化学", "980"),
    ("racemic mixture", "ラセミ混合物。一対の鏡像異性体が等量(1:1)混ざり合った混合物で、全体としては旋光性を示さない。", "名詞句", "A racemic mixture of the drug showed no net optical rotation.", "化学", "970"),
    ("aromaticity", "芳香族性。環状で平面構造を持ち、共役したπ電子系が4n+2個の電子を持つ(ヒュッケル則)ことで著しく安定化される性質。", "名詞", "Benzene owes its exceptional stability to aromaticity.", "化学", "970"),
    ("resonance structure", "共鳴構造式。単一のルイス構造式では表せない電子の非局在化を示すために描かれる、複数の仮想的な構造式。", "名詞句", "The carboxylate ion is best described by two equivalent resonance structures.", "化学", "950"),
    ("aldol condensation", "アルドール縮合。エノラートがカルボニル化合物に求核付加した後、脱水してα,β-不飽和カルボニル化合物を生じる反応。", "名詞句", "Acetone undergoes aldol condensation under basic conditions to form diacetone alcohol.", "化学", "980"),
    ("leaving group", "脱離基。求核置換反応や脱離反応において、電子対を伴って分子から離れていく原子団。", "名詞句", "Iodide is an excellent leaving group because of its weak bond to carbon and its stability as an anion.", "化学", "940"),
    ("steric hindrance", "立体障害。かさ高い置換基が反応中心への接近を妨げることで、反応速度や選択性に影響を与える効果。", "名詞句", "Steric hindrance around the carbonyl carbon slows the rate of nucleophilic addition.", "化学", "930"),
    ("rate law", "速度式(反応速度式)。反応速度を各反応物濃度の関数として表した、実験的に決定される式。", "名詞句", "The rate law for the reaction was determined to be first order in each reactant.", "化学", "940"),
    ("Arrhenius equation", "アレニウスの式。反応速度定数が活性化エネルギーと絶対温度にどう依存するかを表す式(k = Ae^(-Ea/RT))。", "名詞句", "The Arrhenius equation shows that reaction rates increase exponentially with temperature.", "化学", "970"),
    ("colligative properties", "束一的性質(総括的性質)。溶質の種類ではなく粒子数のみに依存する溶液の性質(沸点上昇、凝固点降下、浸透圧など)。", "名詞句", "Boiling point elevation and freezing point depression are examples of colligative properties.", "化学", "960"),
    ("Hess's law", "ヘスの法則(総熱量保存の法則)。反応のエンタルピー変化は反応経路によらず、始状態と終状態のみで決まるという法則。", "名詞句", "Hess's law allows chemists to calculate reaction enthalpies indirectly using known steps.", "化学", "950"),
    ("Nernst equation", "ネルンストの式。電気化学セルの電極電位と、イオン濃度・温度との関係を表す式。", "名詞句", "The Nernst equation is used to calculate the cell potential under non-standard conditions.", "化学", "980"),
    ("rate-determining step", "律速段階。多段階反応において、最も遅く反応全体の速度を支配する素過程。", "名詞句", "The formation of the carbocation is the rate-determining step in the SN1 mechanism.", "化学", "950"),
    ("crystal field theory", "結晶場理論。配位子が作る静電場によって遷移金属イオンのd軌道が分裂する様子を説明する理論。", "名詞句", "Crystal field theory explains why transition metal complexes are often brightly colored.", "化学", "980"),
    ("lattice energy", "格子エネルギー。気体状のイオンが集まってイオン結晶を形成する際に放出されるエネルギーで、結晶の安定性の指標となる。", "名詞句", "The high lattice energy of magnesium oxide accounts for its very high melting point.", "化学", "960"),
    ("band theory", "バンド理論。固体中の電子のエネルギー準位が連続的な「バンド」を形成するとする理論で、導体・半導体・絶縁体の違いを説明する。", "名詞句", "Band theory explains why metals conduct electricity while insulators do not.", "化学", "980"),
    ("coordination number", "配位数。中心原子(イオン)に直接結合している配位子(または隣接原子)の数。", "名詞句", "In the complex [Co(NH3)6]3+, the cobalt ion has a coordination number of six.", "化学", "930"),
    ("Born-Haber cycle", "ボルン・ハーバーサイクル。イオン結晶の格子エネルギーを、昇華熱やイオン化エネルギーなど他の熱化学量から間接的に求めるための熱化学サイクル。", "名詞句", "The Born-Haber cycle can be used to estimate the lattice energy of sodium chloride.", "化学", "980"),
    ("octahedral complex", "八面体錯体。中心金属イオンに6個の配位子が正八面体の頂点方向から配位した錯体。", "名詞句", "Most six-coordinate transition metal complexes adopt an octahedral complex geometry.", "化学", "950"),
    ("Lewis acid", "ルイス酸。電子対を受け取ることができる化学種(ブレンステッド酸よりも広い酸の定義)。", "名詞句", "Aluminum chloride acts as a Lewis acid in Friedel-Crafts reactions.", "化学", "930"),
    ("spectroscopy", "分光法。物質と電磁波(光)との相互作用を利用して、その構造や組成を調べる分析手法の総称。", "名詞", "Spectroscopy is a powerful tool for identifying unknown organic compounds.", "化学", "850"),
    ("infrared spectroscopy", "赤外分光法(IR分光法)。分子の振動に伴う赤外線の吸収を利用して、官能基を同定する分析手法。", "名詞句", "Infrared spectroscopy revealed a strong absorption band characteristic of a carbonyl group.", "化学", "900"),
    ("gas chromatography", "ガスクロマトグラフィー。気化させた試料成分をキャリアガスで移動させ、固定相との相互作用の違いにより分離・分析する手法。", "名詞句", "Gas chromatography is commonly used to separate and quantify volatile organic compounds.", "化学", "900"),
    ("Beer-Lambert law", "ランベルト・ベールの法則(ベールの法則)。溶液の吸光度が濃度と光路長に比例するという法則で、分光光度分析の基礎となる。", "名詞句", "The Beer-Lambert law allows the concentration of a solution to be determined from its absorbance.", "化学", "960"),
    ("limit of detection", "検出限界。分析法によって統計的に有意に検出できる、対象物質の最小濃度または最小量。", "名詞句", "The new method lowered the limit of detection for trace metals in water samples.", "化学", "940"),
    ("mass-to-charge ratio", "質量電荷比(m/z)。質量分析において、イオンの質量を電荷で割った値で、スペクトルの横軸として用いられる。", "名詞句", "In mass spectrometry, ions are separated according to their mass-to-charge ratio.", "化学", "950"),
    ("UV-Vis spectroscopy", "紫外可視分光法(UV-Vis分光法)。紫外〜可視領域の光の吸収を利用して、物質の電子遷移や濃度を調べる分析手法。", "名詞句", "UV-Vis spectroscopy is often used to monitor the progress of a reaction involving colored compounds.", "化学", "900"),
    ("moment of inertia", "慣性モーメント。剛体の回転運動における「回転のしにくさ」を表す量で、質量分布と回転軸からの距離の2乗の積分で求められる。並進運動における質量に相当する。", "名詞句", "A figure skater's moment of inertia decreases when she pulls her arms in, causing her spin to speed up.", "物理", "870"),
    ("harmonic oscillator", "調和振動子。復元力が変位に比例する系(フックの法則に従うばね等)で、単振動を行う理想化されたモデル。量子力学でも基本的なモデル系として扱われる。", "名詞句", "The quantum harmonic oscillator is one of the few systems in quantum mechanics that can be solved exactly.", "物理", "900"),
    ("rigid body", "剛体。外力を加えても変形しない(粒子間の相対距離が変化しない)と仮定される理想化された物体。回転運動の力学を扱う際の基本的なモデル。", "名詞句", "In classical mechanics, a rigid body's motion can be decomposed into translation of its center of mass and rotation about it.", "物理", "860"),
    ("normal mode", "基準振動(モード)。多自由度の振動系において、すべての構成要素が同じ振動数で同位相(または逆位相)に振動する固有の振動パターン。", "名詞句", "Each normal mode of the coupled oscillators vibrates at its own characteristic frequency.", "物理", "920"),
    ("quantum field theory", "場の量子論。粒子を場の量子的励起として扱う理論的枠組みで、素粒子物理学の標準模型の数学的基盤となっている。", "名詞句", "Quantum field theory unifies quantum mechanics with special relativity to describe particle creation and annihilation.", "物理", "970"),
    ("Dirac equation", "ディラック方程式。相対論的量子力学における電子などのスピン1/2粒子を記述する波動方程式で、反粒子の存在を理論的に予言した。", "名詞句", "The Dirac equation predicted the existence of the positron years before it was experimentally discovered.", "物理", "980"),
    ("Born rule", "ボルンの規則。波動関数の絶対値の2乗が、粒子をある位置・状態で観測する確率を与えるという量子力学の基本的な解釈規則。", "名詞句", "According to the Born rule, the probability of finding the particle at a given point is proportional to the square of the wave function's amplitude.", "物理", "960"),
    ("qubit", "量子ビット。量子コンピュータにおける情報の基本単位で、古典ビットと異なり0と1の重ね合わせ状態を取ることができる。", "名詞", "Unlike a classical bit, a qubit can exist in a superposition of 0 and 1 simultaneously.", "物理", "900"),
    ("Zeeman effect", "ゼーマン効果。原子を磁場中に置くと、そのスペクトル線が複数の成分に分裂する現象。電子のスピンや軌道角運動量が磁場と相互作用することで生じる。", "名詞句", "The Zeeman effect splits a single spectral line into several closely spaced lines when the atom is placed in a magnetic field.", "物理", "970"),
    ("spin-orbit coupling", "スピン軌道相互作用。電子のスピン角運動量と軌道角運動量の間に働く相互作用で、原子スペクトルの微細構造やトポロジカル絶縁体などの物性を説明する上で重要。", "名詞句", "Spin-orbit coupling is responsible for the fine structure observed in atomic spectra.", "物理", "970"),
    ("Lorentz transformation", "ローレンツ変換。特殊相対性理論において、互いに等速運動する二つの慣性系の間で時間と空間の座標を変換する式。", "名詞句", "The Lorentz transformation shows how measurements of space and time differ between observers moving relative to each other.", "物理", "900"),
    ("gravitational redshift", "重力赤方偏移。強い重力場から放出された光が、観測者に届くまでに波長が長くなる(エネルギーが低下する)現象。一般相対性理論の予言の一つ。", "名詞句", "Gravitational redshift causes light escaping from near a massive star to shift toward longer wavelengths.", "物理", "910"),
    ("Poynting vector", "ポインティングベクトル。電場と磁場の外積(E×H)で表される、電磁波が単位面積・単位時間あたりに運ぶエネルギーの流れの向きと大きさを示すベクトル。", "名詞句", "The Poynting vector describes the direction and magnitude of energy flow in an electromagnetic wave.", "物理", "930"),
    ("permittivity", "誘電率。物質が電場をどれだけ「透過」または蓄積できるかを表す物理量で、真空中の誘電率は電磁気学の基本定数の一つ。", "名詞", "The permittivity of a dielectric material determines how much electric field it can support for a given charge.", "物理", "900"),
    ("permeability", "透磁率。物質が磁場をどれだけ「通しやすい」か、磁化されやすいかを表す物理量。", "名詞", "Ferromagnetic materials have a much higher permeability than air or vacuum.", "物理", "900"),
    ("phase transition", "相転移。物質が固体・液体・気体などの相(状態)の間で変化する現象。融解、凝固、蒸発、超伝導転移などが含まれる。", "名詞句", "Water undergoes a phase transition from liquid to gas when it boils at 100°C.", "物理", "830"),
    ("Fermi-Dirac statistics", "フェルミ・ディラック統計。パウリの排他律に従うフェルミオン(電子など)が、熱平衡状態でエネルギー準位を占める確率分布を記述する統計。", "名詞句", "Fermi-Dirac statistics explains why electrons in a metal fill energy states up to the Fermi level even at absolute zero.", "物理", "950"),
    ("Fermi energy", "フェルミエネルギー。絶対零度において、フェルミオンが占有する最高のエネルギー準位。固体物理学において電子の統計的振る舞いを理解する上で基本的な概念。", "名詞句", "At absolute zero, all electron states below the Fermi energy are filled and all states above it are empty.", "物理", "930"),
    ("phonon", "フォノン。結晶格子の振動を量子化した準粒子。固体中の熱伝導や電気伝導(超伝導のクーパー対形成など)に重要な役割を果たす。", "名詞", "Phonons carry heat through a crystal lattice much like photons carry electromagnetic energy through space.", "物理", "940"),
    ("Meissner effect", "マイスナー効果。超伝導体が超伝導状態に転移する際、内部の磁場を完全に排除する現象。超伝導体を単なる「完全導体」と区別する特徴的な性質。", "名詞句", "The Meissner effect causes a superconductor to expel all magnetic field lines from its interior, allowing a magnet to levitate above it.", "物理", "950"),
    ("polarization", "偏光。横波である電磁波(光)の電場の振動方向が特定の方向にそろっている状態、またはそのような状態を作り出す性質。", "名詞", "Polarized sunglasses block light waves that vibrate in a particular direction, reducing glare.", "物理", "830"),
    ("coherence", "コヒーレンス(可干渉性)。二つ以上の波が一定の位相関係を保ち、安定した干渉縞を生じさせることができる性質。レーザー光は高いコヒーレンスを持つ。", "名詞", "A laser produces light with a high degree of coherence, unlike an ordinary light bulb.", "物理", "910"),
    ("limit", "数列や関数の値が、変数がある値(または無限大)に近づくときに限りなく近づいていく値。極限。例: 数列{1/n}はn→∞のとき0に収束する(極限は0)。", "名詞", "As n approaches infinity, the limit of the sequence 1/n is zero.", "数学", "800"),
    ("differentiability", "関数がある点で微分可能である性質。微分可能性。微分可能な関数は必ず連続だが、逆は成り立たない。", "名詞", "The absolute value function fails differentiability at the origin, even though it is continuous there.", "数学", "850"),
    ("Riemann integral", "区間を細かく分割した小区間の面積の和(リーマン和)の極限として定義される積分。リーマン積分。", "名詞句", "The Riemann integral of a continuous function over a closed interval always exists.", "数学", "900"),
    ("convergence", "数列や級数が一定の値に近づいていくこと。収束。対義語は発散(divergence)。", "名詞", "The convergence of the infinite series was verified using the ratio test.", "数学", "830"),
    ("epsilon-delta definition", "極限や連続性を厳密に定義するための論法。任意の正の数ε(イプシロン)に対して、適切な正の数δ(デルタ)が存在することを示す。ε-δ論法。", "名詞句", "Students often struggle with the epsilon-delta definition of a limit when they first encounter real analysis.", "数学", "900"),
    ("uniform convergence", "関数列が定義域全体で一様な速さで極限関数に収束すること。一様収束。各点収束(pointwise convergence)より強い条件。", "名詞句", "Uniform convergence of the function sequence guarantees that the limit function is also continuous.", "数学", "930"),
    ("supremum", "ある集合の上界のうち最小のもの。上限。下限(infimum)と対をなす概念。", "名詞", "The supremum of the open interval (0, 1) is 1, even though 1 is not an element of the set.", "数学", "900"),
    ("eigenvector", "線形変換によって向きが変わらず、定数倍(固有値)だけされるゼロでないベクトル。固有ベクトル。", "名詞", "Each eigenvector of the matrix corresponds to a specific eigenvalue that scales it.", "数学", "850"),
    ("determinant", "正方行列に対して定義されるスカラー値で、行列が可逆かどうかや線形変換による体積の拡大率を表す。行列式。", "名詞", "If the determinant of a matrix is zero, the matrix is not invertible.", "数学", "820"),
    ("vector space", "ベクトルの加法とスカラー倍について閉じており、一定の公理を満たす集合。ベクトル空間(線形空間)。", "名詞句", "The set of all polynomials of degree at most three forms a vector space.", "数学", "850"),
    ("linear transformation", "ベクトル空間の間で加法とスカラー倍を保存する写像。線形写像。", "名詞句", "Every linear transformation between finite-dimensional vector spaces can be represented by a matrix.", "数学", "860"),
    ("basis", "ベクトル空間全体を線形結合で表せる、線形独立なベクトルの集合。基底。", "名詞", "The standard basis of three-dimensional space consists of three mutually perpendicular unit vectors.", "数学", "820"),
    ("ring", "加法と乗法という二つの演算が定義され、加法については群をなし、乗法については結合律と分配律を満たす代数構造。環。", "名詞", "The set of all integers, together with ordinary addition and multiplication, forms a ring.", "数学", "880"),
    ("field", "加法と乗法の両方について(零を除いて)逆元が存在する可換環。体。有理数・実数・複素数はいずれも体の例。", "名詞", "The rational numbers form a field because every nonzero element has a multiplicative inverse.", "数学", "880"),
    ("homomorphism", "二つの代数的構造の間で演算を保存する写像。準同型写像。", "名詞", "A group homomorphism maps the identity element of one group to the identity element of the other.", "数学", "920"),
    ("isomorphism", "全単射である準同型写像。二つの代数的構造が本質的に同じであることを示す。同型写像。", "名詞", "There exists an isomorphism between any two vector spaces of the same finite dimension.", "数学", "910"),
    ("abelian group", "演算が可換である(a*b=b*aが常に成り立つ)群。可換群。アーベル群。", "名詞句", "The integers under addition form an abelian group, but general matrices under multiplication do not.", "数学", "930"),
    ("open set", "集合内の任意の点について、その点を中心とした十分小さい近傍が完全にその集合に含まれるような集合。開集合。", "名詞句", "In the standard topology on the real line, every open interval is an open set.", "数学", "850"),
    ("closed set", "その補集合が開集合であるような集合。閉集合。境界を含む集合として直感的に理解できる。", "名詞句", "A closed interval such as [0, 1] is a closed set because it contains all of its boundary points.", "数学", "850"),
    ("compactness", "任意の開被覆が有限部分被覆を持つという位相空間の性質。コンパクト性。ユークリッド空間では有界かつ閉であることと同値(ハイネ・ボレルの定理)。", "名詞", "By the Heine-Borel theorem, compactness in Euclidean space is equivalent to being closed and bounded.", "数学", "900"),
    ("metric space", "集合とその上に定義された距離関数(2点間の距離を測る関数)の組。距離空間。", "名詞句", "Every normed vector space naturally becomes a metric space by defining distance as the norm of the difference.", "数学", "880"),
    ("topological space", "集合とその上の開集合の族(位相)の組で、位相公理を満たすもの。位相空間。距離空間より一般的な概念。", "名詞句", "A topological space need not have a notion of distance, unlike a metric space.", "数学", "920"),
    ("Bayes' theorem", "条件付き確率の間の関係を表す定理。事前確率から事後確率を計算する際に用いられる。ベイズの定理。", "名詞句", "Bayes' theorem is used to update the probability of a hypothesis as new evidence becomes available.", "数学", "870"),
    ("Markov chain", "次の状態への遷移確率が現在の状態のみに依存し、過去の履歴には依存しない確率過程。マルコフ連鎖。", "名詞句", "A Markov chain is often used to model systems in which the future state depends only on the present state.", "数学", "890"),
    ("probability density function", "連続型確率変数の確率分布を表す関数で、ある区間で積分するとその区間に値が入る確率になる。確率密度関数。", "名詞句", "The area under the probability density function between two points gives the probability that the random variable falls in that range.", "数学", "870"),
    ("set theory", "集合とその性質・演算(和集合・共通部分・補集合など)を研究する数学の基礎分野。集合論。", "名詞句", "Set theory provides the foundational language used throughout modern mathematics.", "数学", "850"),
    ("mathematical induction", "自然数に関する命題を証明する手法。基底段階(n=1で成立)と帰納段階(nで成立するならn+1でも成立)を示すことで、すべてのnについて成立することを証明する。数学的帰納法。", "名詞句", "The formula for the sum of the first n integers can be proved by mathematical induction.", "数学", "830"),
    ("combinatorics", "有限個の対象の組み合わせ方や配置の数を数える数学の分野。組合せ論。", "名詞", "Combinatorics is used to calculate the number of ways to arrange a deck of cards.", "数学", "860"),
    ("graph theory", "点(頂点)と点を結ぶ線(辺)からなるグラフの構造を研究する数学の分野。グラフ理論。", "名詞句", "Graph theory provides the mathematical framework for analyzing networks such as social media connections.", "数学", "850"),
    ("permutation", "有限個の対象を特定の順序で並べる並べ方。順列。", "名詞", "There are 120 permutations of five distinct objects arranged in a row.", "数学", "800"),
    ("bijection", "単射(1対1)かつ全射(上への写像)である写像。全単射。二つの集合の間に一対一の対応が存在することを示す。", "名詞", "A bijection between two finite sets proves that they have the same number of elements.", "数学", "900"),
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
