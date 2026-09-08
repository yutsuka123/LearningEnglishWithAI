# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""生物学ドメインの大学専門課程レベルへの深化(2026-09-08・B24タスク・
authored by Claude)。`docs/B24_VOCAB_DRAFT_REVIEW.md`で先にドラフトされた
121語(既存DB全体との重複チェック済み)を2並列サブエージェントで
定義文・例文・detail生成→WebSearchで歴史的事実(人名・年代)を検証。

既存DBとの同一概念の重複14語を除外: antibody(論文・学術)、antigen
(医療(専門・学問))、biodiversity(論文・学術)、CRISPR(生物工学)、
DNA replication(生化学)、gene expression(生化学)、nitrogen fixation
(植物(他))、operon(生化学)、phloem(植物(他))、plasmid(生化学)、
recombinant DNA(生物工学)、symbiosis(植物(他))、telomerase(生化学)、
xylem(植物(他))。dendriteのみ、既存語(電池分野、金属の樹枝状析出物)
とは全く異なる意味(神経細胞の樹状突起)のため`dendrite (biology)`として
同綴り異義語(B17b)化して採用。

2026-09-08ユーザー指示「語彙拡充は各分野の中学高等学校相当の拡充、
小学校相当の拡充も多少あってもいいと思います」を受け、本バッチとは別に
`tag_domain_breadth_2026_09_08.py`(既存の中学・高校相当語をword_domain_
tagsで生物学ドメインにも追加タグ付け・27件と最多)と`add_domain_breadth_
elementary_2026_09_08.py`(小学校〜中学相当の基本語を新規追加)を実施済み
(詳細はdocs/TODO.md参照)。生物学は投入前時点で既にlevel 800+が
全体の76%を占めていたため、この2つの補完策を特に優先した。本バッチ
自体は当初の計画通り学部専門レベル(level 850〜990+)のみ。

一部の語(29/107件、`neurotransmitter`/`stem cell`/`transcription
(molecular biology)`等)はdetail.origin/detail.triviaが空文字のまま
(自然な由来・豆知識が見つからなかったため無理に作らなかった、との
方針。explanation欄は全件で内容あり)。事実の誤りではなく完成度の
軽微な差のため今回はそのまま採用し、次回の照査ついでの拡充候補として
残す。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_biology_advanced.py
仕上げ: relevel.pyは実行しない(add_math_advanced.pyと同じ理由)。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("action potential", "神経細胞や筋細胞の細胞膜で、刺激によって膜電位が一時的かつ急激に逆転し、その後もとに戻る一過性の変化。電位依存性イオンチャネルの開閉によって生じ、全か無かの法則に従って神経を伝わる電気信号(神経インパルス)の実体となる。活動電位。", "名詞", "An action potential occurs when a neuron's membrane potential rapidly rises and falls following a stimulus that reaches the threshold.", "生物学", "900"),
    ("active immunity", "病原体や抗原に自らの免疫系がさらされ、抗体産生や記憶細胞の形成を通じて長期的な防御力を獲得する免疫の仕組み。実際の感染によって成立する自然能動免疫と、ワクチン接種によって成立する人工能動免疫がある。能動免疫。", "名詞", "Active immunity develops when a person's own immune system produces antibodies in response to infection or vaccination.", "生物学", "920"),
    ("adaptive immunity", "特定の病原体・抗原を認識するリンパ球(T細胞・B細胞)を介して働き、一度出会った病原体を記憶して再侵入時により速く強力に反応できる免疫システム。獲得免疫とも呼ばれ、非特異的な自然免疫と対をなす概念。獲得免疫、適応免疫。", "名詞", "Adaptive immunity depends on T cells and B cells that recognize specific antigens and retain a memory of them.", "生物学", "900"),
    ("alternative splicing", "1つの遺伝子から転写された前駆mRNAにおいて、含めるエキソンの組み合わせを変えることで、複数の異なるmRNA、ひいては複数の異なるタンパク質(アイソフォーム)を作り出す遺伝子発現調節の仕組み。真核生物のタンパク質の多様性を大きく広げている。選択的スプライシング。", "名詞", "Alternative splicing enables a single gene to produce several different protein isoforms by combining exons in different ways.", "生物学", "950"),
    ("analogous structure", "系統的に近縁でない生物同士が、共通の祖先に由来するのではなく、似た環境・生活様式への適応の結果として独立に獲得した、機能や外見が似た器官・構造。収斂進化の産物であり、起源を共有する相同器官(homologous structure)とは区別される。相似器官。", "名詞", "The wings of birds and the wings of insects are analogous structures that evolved independently to serve the same function.", "生物学", "900"),
    ("apical dominance", "植物の茎の先端(頂芽)が成長している間、側芽(腋芽)の成長が抑制される現象。頂芽で合成されたオーキシンが下方へ輸送され、側芽の成長を抑制することで生じると考えられている。頂芽優勢。", "名詞", "Apical dominance keeps the lateral buds of a plant suppressed while the terminal bud continues to grow.", "生物学", "930"),
    ("apoptosis", "細胞が外傷や病気によってではなく、遺伝的にプログラムされた機構によって自ら計画的に死へと至る現象。プログラム細胞死、細胞の自然死とも呼ばれ、発生過程での不要な組織の除去や、損傷・老化した細胞の排除に重要な役割を果たす。アポトーシス。", "名詞", "Apoptosis eliminates the webbing between a developing embryo's fingers.", "生物学", "900"),
    ("autoimmune disease", "免疫系が自己と非自己を正しく区別できなくなり、本来攻撃すべきでない自分自身の細胞や組織を誤って攻撃してしまうことで生じる疾患の総称。関節リウマチ、1型糖尿病、全身性エリテマトーデス、橋本病などが代表例。自己免疫疾患。", "名詞", "In an autoimmune disease, the immune system mistakenly attacks the body's own healthy cells and tissues.", "生物学", "900"),
    ("auxin", "植物の成長や器官形成の多くの側面を調節する植物ホルモンの一群。細胞の伸長成長を促進し、頂芽優勢、屈光性、屈地性、側根の形成など幅広い過程に関与する。代表的な天然オーキシンはインドール-3-酢酸(IAA)。オーキシン。", "名詞", "Auxin produced in the shoot tip promotes cell elongation and helps the plant bend toward light.", "生物学", "910"),
    ("axon", "神経細胞(ニューロン)の細胞体から伸びる、通常は1本の長い突起。活動電位を細胞体から他の神経細胞や筋肉・腺などの標的細胞へと伝える役割を担う。多くは髄鞘(ミエリン鞘)に覆われ、伝導速度を高めている。軸索。", "名詞", "The axon carries electrical signals away from the neuron's cell body toward other neurons or muscle cells.", "生物学", "870"),
    ("B cell", "骨髄で産生・成熟し、抗原を認識すると形質細胞に分化して抗体(免疫グロブリン)を産生するリンパ球の一種。体液性免疫の中心的な担い手であり、一部は記憶B細胞として残り、同じ抗原の再侵入に備える。B細胞、Bリンパ球。", "名詞", "When a B cell encounters an antigen that matches its receptor, it can differentiate into a plasma cell that secretes antibodies.", "生物学", "880"),
    ("biogeochemical cycle", "炭素・窒素・リン・硫黄・水などの化学物質が、大気・水圏・地圏(非生物的環境)と生物(生物的環境)との間を循環する過程の総称。生態系における物質循環の基本的な枠組みであり、生物地球化学的循環とも呼ばれる。生物地球化学的循環。", "名詞句", "The carbon cycle and the nitrogen cycle are both examples of biogeochemical cycles that move elements between living organisms and the environment.", "生物学", "900"),
    ("biomagnification", "分解されにくい物質(DDTなどの残留性有機汚染物質や水銀など)が、食物連鎖の上位の捕食者ほど体内によりいっそう高濃度で蓄積していく現象。生物濃縮とも訳されるが、個体内での蓄積(bioaccumulation)とは区別され、栄養段階を通じた濃度上昇を指す。生物濃縮、生物学的濃縮。", "名詞", "Biomagnification caused DDT to reach dangerously high concentrations in top predators such as eagles, even though the pesticide was applied at much lower levels.", "生物学", "930"),
    ("bottleneck effect", "疫病・自然災害・乱獲などによって個体群のサイズが急激かつ大幅に減少した結果、生き残った少数の個体が持つ遺伝子構成によってその後の個体群の遺伝的多様性が大きく制限される現象。遺伝的浮動の一種。瓶首効果、ボトルネック効果。", "名詞", "A bottleneck effect can drastically reduce a population's genetic diversity even after the population size later recovers.", "生物学", "930"),
    ("carbon cycle", "炭素原子が、大気(二酸化炭素)・生物(有機物)・海洋・土壌・岩石などの間を移動しながら循環する過程。光合成による炭素の固定、呼吸・分解・燃焼による二酸化炭素の放出などを通じて、地球規模で炭素が循環している。炭素循環。", "名詞句", "Photosynthesis and respiration are two key processes that drive the carbon cycle between the atmosphere and living organisms.", "生物学", "870"),
    ("cell cycle", "細胞が分裂によって2つの娘細胞を生み出すまでの、DNA複製や細胞成長を含む一連の秩序立った過程。間期(G1期・S期・G2期)と分裂期(M期)からなり、チェックポイントによって厳密に制御されている。細胞周期。", "名詞句", "The cell cycle consists of interphase, during which the cell grows and copies its DNA, followed by mitosis, during which it divides.", "生物学", "870"),
    ("cell cycle checkpoint", "細胞周期の進行過程に設けられた監視機構で、DNAの損傷や複製の未完了、染色体の紡錘体への正しい結合などを確認し、異常があれば次の段階への移行を止める仕組み。主にG1/S期、G2/M期、M期(紡錘体形成)の3か所に存在する。細胞周期チェックポイント。", "名詞句", "The G1 checkpoint determines whether a cell has enough resources and undamaged DNA to proceed with division.", "生物学", "950"),
    ("cell fate", "発生の過程で、ある細胞(またはその子孫細胞)が最終的にどのような種類の細胞・組織になるかという運命。細胞系譜、周囲の細胞からの誘導シグナル、内部の遺伝子発現プログラムなどによって次第に決定づけられていく。細胞運命。", "名詞", "Cell fate is progressively restricted during development as cells become committed to specific lineages.", "生物学", "930"),
    ("cell-mediated immunity", "抗体を介さず、T細胞(特に細胞傷害性T細胞やヘルパーT細胞)が直接的に働くことで成立する免疫応答。ウイルス感染細胞やがん細胞、細胞内寄生体に感染した細胞などを直接排除する際に中心的な役割を果たす。細胞性免疫。", "名詞", "Cell-mediated immunity relies on cytotoxic T cells that directly destroy infected or abnormal cells.", "生物学", "950"),
    ("character displacement", "生態的地位が似通った近縁種同士が同じ地域に生息(同所的に分布)する場合、種間競争を避けるために、体の大きさや形質(くちばしの大きさなど)が両種で異なる方向に分化していく進化現象。同所的な集団では形質差が拡大し、異所的な(重ならない)集団では差が小さくなる。形質置換。", "名詞", "Character displacement can cause two similar species to evolve different beak sizes where their ranges overlap, reducing competition for the same food.", "生物学", "990"),
    ("chromatin", "真核生物の細胞核内で、DNAとヒストンなどのタンパク質が結合して形成される複合体。間期にはほどけた状態で核内に分散しており、細胞分裂期には凝縮して染色体を形成する。クロマチン、染色質。", "名詞", "Chromatin must be tightly packed to fit the enormous length of DNA into the small space of the nucleus.", "生物学", "910"),
    ("cladistics", "生物の分類を、共有された派生形質(共有派生形質)にもとづいて再構成した系統関係(分岐図)だけを基準に行うべきだとする系統分類学の方法論。祖先種から派生した子孫すべてを含む単系統群のみを正当な分類群と認める。分岐分類学。", "名詞", "Cladistics classifies organisms strictly according to their evolutionary branching relationships rather than overall similarity.", "生物学", "990"),
    ("climax community", "生態遷移が進行した末に到達する、その地域の気候条件のもとで安定して自己を維持し続けると考えられる、生物群集の最終段階。それ以上大きな種構成の変化を起こさず、優占種の構成がほぼ一定に保たれる。極相群集。", "名詞", "In many temperate regions, a climax community dominated by broadleaf trees develops after decades of ecological succession.", "生物学", "910"),
    ("coevolution", "相互に影響し合う2種(またはそれ以上)の生物が、互いの進化的変化に応じて自らも進化していく過程。捕食者と被食者、宿主と寄生者、花と送粉者などの関係でしばしば見られる、互恵的または敵対的な進化的相互作用。共進化。", "名詞", "The coevolution of flowers and their pollinators has produced remarkable matches between flower shape and pollinator anatomy.", "生物学", "900"),
    ("cytokine", "免疫細胞をはじめとするさまざまな細胞から分泌され、他の細胞の増殖・分化・機能を調節する小さなシグナル伝達タンパク質の総称。インターロイキン、インターフェロン、腫瘍壊死因子(TNF)などが含まれ、免疫応答や炎症反応の調節に中心的な役割を果たす。サイトカイン。", "名詞", "Cytokines released by immune cells coordinate the inflammatory response to infection.", "生物学", "930"),
    ("cytoskeleton", "真核生物の細胞質に張り巡らされた、タンパク質でできた繊維状の構造網。細胞の形の維持、細胞内での物質輸送、細胞分裂、細胞運動などに関与する。微小管・アクチンフィラメント・中間径フィラメントの3種類の主要な繊維から構成される。細胞骨格。", "名詞", "The cytoskeleton gives a cell its shape and provides the tracks along which organelles are transported.", "生物学", "900"),
    ("dendrite (biology)", "(電池分野で使われる、金属が針状・樹枝状に析出する現象を指す「デンドライト」とは異なり、)神経細胞(ニューロン)の細胞体から木の枝のように分岐して伸びる短い突起。他の神経細胞やシナプスから信号を受け取り、細胞体へと伝える役割を担う。樹状突起。", "名詞", "Dendrites receive signals from other neurons and carry them toward the cell body.", "生物学", "870"),
    ("differentiation (cell biology)", "未分化な細胞(幹細胞など)が、特定の形態的・機能的な特徴を持つ特殊化した細胞へと変化していく過程。遺伝子発現のパターンが変化することで生じ、細胞の種類ごとに異なる構造・機能が獲得される。細胞分化。", "名詞", "During embryonic development, stem cells undergo differentiation to become specialized cell types such as muscle cells or neurons.", "生物学", "900"),
    ("DNA polymerase", "DNAを鋳型として、ヌクレオチドを一つずつ結合させることで新しいDNA鎖を合成する酵素の総称。DNA複製やDNA修復に不可欠であり、PCR法などのバイオテクノロジーでも利用されている。DNAポリメラーゼ。", "名詞", "DNA polymerase reads an existing DNA strand as a template and adds complementary nucleotides to build a new strand.", "生物学", "900"),
    ("double fertilization (plant)", "被子植物に特有の受精様式で、花粉管内の2個の精細胞のうち1個が卵細胞と受精して二倍体の胚(将来の個体)を、もう1個が中央細胞(2個の極核を含む)と受精して三倍体の胚乳を形成する現象。1回の受精過程で胚と胚乳という2つの構造が同時に作られる。重複受精。", "名詞", "In double fertilization, one sperm cell fuses with the egg cell to form the embryo, while the other fuses with the central cell to form the endosperm.", "生物学", "980"),
    ("ecological succession", "ある地域の生物群集が、時間の経過とともに種構成を変えながら移り変わっていく過程。土壌のない裸地から始まる一次遷移と、既存の土壌が残る撹乱跡地から始まる二次遷移に大別され、最終的に比較的安定した極相群集に至るとされる。生態遷移。", "名詞", "Ecological succession after a volcanic eruption begins with pioneer species such as lichens that can survive on bare rock.", "生物学", "900"),
    ("embryogenesis", "受精卵が細胞分裂・分化を繰り返しながら、組織や器官の基本構造を備えた胚へと発生していく一連の過程。動物では卵割・胞胚形成・原腸形成・器官形成などの段階を経て進む。胚発生。", "名詞", "Embryogenesis begins with the fertilized egg and proceeds through cleavage, gastrulation, and organogenesis.", "生物学", "920"),
    ("endoplasmic reticulum", "真核生物の細胞質に広がる、膜で囲まれた網目状・管状の構造からなる細胞小器官。表面にリボソームが付着した粗面小胞体はタンパク質の合成・修飾を、リボソームを持たない滑面小胞体は脂質合成やカルシウムイオンの貯蔵などを担う。小胞体。", "名詞", "The rough endoplasmic reticulum is studded with ribosomes and plays a central role in the synthesis of proteins destined for secretion.", "生物学", "900"),
    ("epigenetic marker", "DNAの塩基配列そのものを変えることなく、DNAのメチル化やヒストンの化学修飾などを通じて遺伝子発現のオン・オフを調節する目印(標識)となる分子的な特徴。細胞分裂を経ても維持されることがあり、細胞の分化状態の記憶や、環境要因による遺伝子発現の変化に関わる。エピジェネティックマーカー、後成的標識。", "名詞", "DNA methylation is one of the most well-studied epigenetic markers that can silence gene expression without altering the underlying DNA sequence.", "生物学", "970"),
    ("exon", "遺伝子の中で、スプライシングの過程を経て成熟mRNAに残り、実際にタンパク質のアミノ酸配列情報として翻訳される(あるいは非翻訳領域として保持される)領域。前駆mRNAから取り除かれるイントロンと対をなす概念。エキソン、発現配列。", "名詞", "During RNA splicing, introns are removed while exons are joined together to form the mature mRNA.", "生物学", "900"),
    ("fitness (evolutionary biology)", "ある個体、あるいは特定の対立遺伝子や表現型が、次世代に自らの遺伝子をどれだけ効果的に伝えられるかを表す尺度。生存率だけでなく繁殖成功度も含めた、生存と繁殖を総合した相対的な指標として扱われる。適応度。", "名詞", "An individual's fitness is measured not just by survival but by how many offspring it successfully produces.", "生物学", "910"),
    ("fixation (genetics)", "集団中のある対立遺伝子の頻度が100%に達し、他の対立遺伝子がその集団から完全に失われた状態。自然選択や、特に小さな集団で強く働く遺伝的浮動によって生じる。固定。", "名詞", "An allele reaches fixation when every individual in the population carries that allele and no other version remains.", "生物学", "990"),
    ("founder effect", "もとの大きな個体群からごく少数の個体が移住・分離して新しい個体群を創始したとき、それら少数の始祖が偶然持っていた対立遺伝子の構成によって、新しい個体群の遺伝的多様性が大きく制限される現象。遺伝的浮動の一種。創始者効果。", "名詞", "The founder effect can leave a new population with a very different allele frequency from the original population it came from.", "生物学", "950"),
    ("gastrulation", "動物の胚発生において、胞胚が細胞の陥入や移動を伴う劇的な再配置を経て、外胚葉・中胚葉・内胚葉という3つの胚葉に分かれた原腸胚を形成する過程。その後のすべての組織・器官の形成の土台となる、発生上きわめて重要な段階。原腸形成。", "名詞", "Gastrulation transforms a simple ball of cells into an embryo with three distinct germ layers.", "生物学", "970"),
    ("gel electrophoresis", "DNA・RNA・タンパク質などの分子を、寒天(アガロース)やポリアクリルアミドなどのゲルの中で電場をかけて移動させ、分子の大きさ(や電荷)の違いにもとづいて分離する実験技術。分子生物学や法医学(DNA鑑定)などで広く利用される。ゲル電気泳動。", "名詞", "Gel electrophoresis separates DNA fragments by size as they migrate through a gel under an electric field.", "生物学", "900"),
    ("gene knockout", "特定の遺伝子の機能を人為的に破壊・不活性化し、その遺伝子が働かない生物(多くはマウス)を作り出す遺伝子工学の手法、およびそうして作られた生物。相同組換えを利用して胚性幹細胞の標的遺伝子を破壊し、それをもとに個体を作出する方法が代表的。遺伝子ノックアウト。", "名詞", "Researchers created a gene knockout mouse to study what happens when a specific gene is completely inactivated.", "生物学", "950"),
    ("gene pool", "ある個体群(集団)の中に存在する、すべての個体が持つ対立遺伝子全体の集まり。個体群の遺伝的多様性の総体を表し、集団遺伝学や進化生物学において進化の基盤となる概念として扱われる。遺伝子プール。", "名詞", "A large gene pool with many different alleles gives a population more raw material for adapting to environmental change.", "生物学", "870"),
    ("gene therapy", "疾患の治療や予防を目的として、正常な遺伝子を体内の細胞に導入したり、欠陥のある遺伝子を修復・置換したりする医療技術。ウイルスベクターなどを用いて遺伝子を細胞内に送り込む方法が代表的。遺伝子治療。", "名詞", "Gene therapy aims to treat genetic disorders by delivering a functional copy of a defective gene into a patient's cells.", "生物学", "880"),
    ("Golgi apparatus", "真核生物の細胞質にある、扁平な袋状の膜構造(層板)が積み重なった細胞小器官。小胞体で合成されたタンパク質や脂質を受け取り、修飾・選別したうえで、細胞内の目的地や細胞外への分泌に向けて包装・輸送する役割を担う。ゴルジ体、ゴルジ装置。", "名詞", "The Golgi apparatus modifies, sorts, and packages proteins received from the endoplasmic reticulum before sending them to their final destinations.", "生物学", "880"),
    ("histone", "真核生物の細胞核内でDNAと結合し、DNAを折りたたんでヌクレオソームという構造単位を作る塩基性のタンパク質。DNAを核内という限られた空間に収納するとともに、その化学修飾を通じて遺伝子発現の調節にも関わる。ヒストン。", "名詞", "DNA wraps around histone proteins to form nucleosomes, which allow the long DNA molecule to be compactly packaged in the nucleus.", "生物学", "910"),
    ("homeotic gene", "動物の体の中で、ある体節や部域が本来とは異なる体節・部域の構造に置き換わる「ホメオティック変異」を引き起こす遺伝子群。個体発生の初期段階で、体の前後軸に沿った各部域の位置的な「アイデンティティ」を決定する働きを持つ。ホメオティック遺伝子。", "名詞", "Mutations in a homeotic gene of the fruit fly can cause legs to grow in the place where antennae should be.", "生物学", "990"),
    ("homologous structure", "見た目や機能が異なっていても、共通の祖先に由来し、進化的な起源を共有する器官や構造。ヒトの腕、コウモリの翼、クジラの胸びれは、いずれも同じ骨格の基本設計(上腕骨・橈骨・尺骨など)を共有する相同器官の代表例である。相似器官(analogous structure)とは起源の点で区別される。相同器官。", "名詞", "The human arm, the bat wing, and the whale flipper are homologous structures that share the same underlying bone arrangement despite serving very different functions.", "生物学", "900"),
    ("Hox gene", "動物の体の前後軸に沿った各体節・部域のアイデンティティを決定するホメオティック遺伝子のうち、「ホメオボックス」と呼ばれる共通のDNA配列を持つ一群の遺伝子。染色体上に並ぶ順序が、体の前後軸上での発現順序とおおむね対応する「コリニアリティ」という性質で知られる。Hox遺伝子。", "名詞", "Hox genes are arranged on the chromosome in the same order as the body segments they control, from head to tail.", "生物学", "970"),
    ("humoral immunity", "B細胞から分化した形質細胞が産生する抗体(免疫グロブリン)を介して働く免疫応答。血液や体液(ラテン語でhumor)中に存在する抗体が、細菌やウイルス、毒素などの細胞外の病原体・異物を中和・排除する。体液性免疫。", "名詞", "Humoral immunity relies on antibodies secreted into the blood and other body fluids to neutralize pathogens.", "生物学", "950"),
    ("immune response", "病原体や異物(抗原)の侵入に対して、免疫系がそれを認識し、排除しようとして引き起こす一連の生体反応。自然免疫による即時的な反応と、適応免疫による特異的で記憶を伴う反応とに大別される。免疫応答。", "名詞", "The immune response to a viral infection typically begins with innate defenses and is later reinforced by a more specific adaptive response.", "生物学", "880"),
    ("immunoglobulin", "B細胞から分化した形質細胞によって産生される、抗体としての機能を持つタンパク質の総称。特定の抗原に結合する可変領域と、抗体の種類(クラス)を決める定常領域からなるY字型の構造を持つ。IgG・IgM・IgA・IgD・IgEの5つのクラスに分類される。免疫グロブリン。", "名詞", "Each immunoglobulin has a variable region that allows it to bind a specific antigen with high precision.", "生物学", "950"),
    ("induction (developmental biology)", "発生の過程で、ある一群の細胞(誘導体)が放出するシグナル分子が、隣接する別の細胞群(被誘導体)の発生運命に影響を与え、特定の組織・器官へと分化するよう仕向ける現象。誘導。", "名詞", "Induction occurs when one group of embryonic cells signals to a neighboring group, directing it to develop into a particular tissue.", "生物学", "950"),
    ("innate immunity", "特定の病原体を区別せず、生まれつき備わっている非特異的な防御機構による免疫。皮膚や粘膜による物理的バリア、好中球やマクロファージによる貪食、炎症反応などが含まれ、感染後ただちに働き始める。適応免疫のような免疫記憶は持たない。自然免疫、先天性免疫。", "名詞", "Innate immunity provides the body's first line of defense and responds to pathogens within minutes to hours.", "生物学", "900"),
    ("intron", "遺伝子の中で、転写された前駆mRNAからスプライシングによって取り除かれ、成熟mRNAには残らない、タンパク質をコードしない領域。成熟mRNAに残るエキソンと交互に並んでいることが多い。真核生物の遺伝子に広く見られる。イントロン、介在配列。", "名詞", "Introns are removed from the pre-mRNA during splicing before the mature mRNA leaves the nucleus.", "生物学", "900"),
    ("ion channel", "細胞膜を貫通する膜タンパク質で、特定のイオン(Na⁺・K⁺・Ca²⁺・Cl⁻など)を電気化学的勾配に従って受動的に透過させる孔を形成する。電位依存性チャネルやリガンド依存性チャネルなどがあり、神経細胞の静止電位の維持や活動電位の発生に不可欠である。", "名詞句", "Voltage-gated sodium ion channels open rapidly at the start of an action potential, allowing Na+ ions to rush into the neuron.", "生物学", "900"),
    ("kin selection", "個体が自らの直接的な繁殖成功を犠牲にしてでも、血縁関係にあり遺伝子を共有する可能性が高い近親個体の生存・繁殖を助ける行動が、包括適応度を通じて進化しうるとする自然選択の理論。血縁選択説。", "名詞句", "Kin selection helps explain why worker bees sacrifice their own reproduction to help raise their sisters.", "生物学", "970"),
    ("ligase", "2つの分子、あるいは分子内の2つの部位を、ATPなどのエネルギーを消費して共有結合で連結する酵素の総称。分子生物学ではDNAリガーゼが、DNA鎖の隣接するヌクレオチド間にホスホジエステル結合を形成し、岡崎フラグメントの連結・DNA修復・組換えDNA作製などに用いられる。", "名詞", "DNA ligase seals the nicks between Okazaki fragments during lagging-strand synthesis.", "生物学", "930"),
    ("limiting factor (ecology)", "生物の個体群の成長や分布を、他の要因に優先して制約する環境要因(光・水・栄養塩・温度・生息空間など)。複数の要因のうち最も供給が乏しい要因が、個体群の成長速度や環境収容力を決定するという考え方に基づく。", "名詞句", "Nitrogen is often the limiting factor for plant growth in temperate agricultural soils.", "生物学", "880"),
    ("lysosome", "加水分解酵素(酸性ヒドロラーゼ)を含む一重膜のオルガネラで、内部を酸性(pH約5)に保つことでタンパク質・脂質・多糖・核酸などの高分子を分解する。エンドサイトーシスで取り込んだ物質の消化や、オートファジーによる自己成分の分解に関与する。", "名詞", "Lysosomes fuse with phagosomes to digest engulfed bacteria using their acidic hydrolytic enzymes.", "生物学", "880"),
    ("major histocompatibility complex", "脊椎動物のゲノム上にある高度に多型な遺伝子群。コードされるMHC分子は細胞内で分解された抗原ペプチドを提示し、T細胞による自己・非自己の識別や免疫応答の誘導に中心的な役割を果たす。クラスI分子は全ての有核細胞に、クラスII分子は主に抗原提示細胞に発現する。ヒトではHLA(ヒト白血球抗原)と呼ばれる。", "名詞句", "The major histocompatibility complex presents processed antigen fragments on the cell surface for recognition by T cells.", "生物学", "990"),
    ("meristem", "植物体の特定部位に存在し、未分化な細胞が活発に細胞分裂を続ける組織。茎頂分裂組織・根端分裂組織などの頂端分裂組織は一次成長(伸長)を、維管束形成層やコルク形成層などの側部分裂組織は二次成長(肥大)をもたらす。", "名詞", "The apical meristem at the tip of a root continuously produces new cells that allow the root to grow longer.", "生物学", "930"),
    ("microtubule", "チューブリンという球状タンパク質(α-チューブリンとβ-チューブリンの二量体)が重合してできる、直径約25nmの中空の管状細胞骨格繊維。紡錘体形成による染色体分離、細胞内の物質輸送のレール、繊毛・鞭毛の軸糸(9+2構造)などを構成する。", "名詞", "During mitosis, spindle microtubules attach to kinetochores and pull sister chromatids toward opposite poles.", "生物学", "910"),
    ("morphogenesis", "発生過程において、細胞の増殖・移動・分化・アポトーシスなどを通じて生物の組織・器官・体全体の形や構造が作り出されていく過程。", "名詞", "Gastrulation is a key stage of morphogenesis during which the three germ layers are established.", "生物学", "950"),
    ("myelin sheath", "中枢神経系ではオリゴデンドロサイト、末梢神経系ではシュワン細胞の細胞膜が軸索に何重にも巻き付いてできる、脂質に富む絶縁性の被膜。髄鞘の切れ目であるランビエ絞輪において活動電位が跳躍伝導することで、伝導速度が大幅に向上する。", "名詞句", "The myelin sheath insulates the axon and enables saltatory conduction between the nodes of Ranvier.", "生物学", "900"),
    ("neuromuscular junction", "運動ニューロンの軸索末端と骨格筋線維との間に形成される化学シナプス。神経終末から放出されたアセチルコリンが筋線維終板のニコチン性アセチルコリン受容体に結合し、筋の脱分極と収縮を引き起こす。", "名詞句", "At the neuromuscular junction, acetylcholine released from the motor neuron binds to receptors on the muscle fiber, triggering contraction.", "生物学", "950"),
    ("neuron", "電気的・化学的シグナルの伝達に特化した神経系の基本的な細胞単位。細胞体・樹状突起・軸索からなり、細胞膜内外のイオン濃度差によって静止電位を維持し、閾値を超える刺激により活動電位を発生させて情報を伝える。", "名詞", "A neuron maintains a negative resting potential of about -70 mV by keeping intracellular K+ concentration high and Na+ concentration low.", "生物学", "850"),
    ("neuroplasticity", "学習・経験や環境の変化、あるいは脳損傷などに応じて、神経回路のシナプスの強度・数、あるいは神経細胞間の結合様式が変化する脳の能力。発達期に限らず、成体の脳でも一定程度生じる。", "名詞", "Neuroplasticity allows the brain to reorganize neural pathways in response to new experiences or injury.", "生物学", "950"),
    ("neurotransmitter", "シナプス前ニューロンの神経終末から放出され、シナプス間隙を拡散してシナプス後細胞の受容体に結合することで、興奮性または抑制性の信号を伝える化学物質。アセチルコリン・グルタミン酸・GABA・ドーパミン・セロトニンなどが代表例。", "名詞", "When an action potential reaches the axon terminal, it triggers the release of neurotransmitter into the synaptic cleft.", "生物学", "880"),
    ("niche partitioning", "生態的に類似した複数の種が同一の生息地に共存する際、食物・活動時間・空間利用などの資源利用の仕方を異ならせることで種間競争を緩和し、共存を可能にする現象。", "名詞句", "Robert MacArthur's classic study of warblers showed niche partitioning, as each species foraged in a different part of the same spruce trees.", "生物学", "950"),
    ("passive immunity", "自らの免疫系で抗体を産生するのではなく、他の個体で作られた抗体(または抗体を含む血清)を直接受け取ることで得られる一時的な免疫。母親から胎盤や母乳を介して新生児に移行する抗体(自然受動免疫)や、抗血清・抗毒素の投与(人工受動免疫)がこれにあたる。", "名詞句", "Newborn infants acquire passive immunity through antibodies that cross the placenta from the mother during pregnancy.", "生物学", "930"),
    ("peroxisome", "一重膜に包まれた球状のオルガネラで、内部にカタラーゼなどの酸化酵素を含み、脂肪酸のβ酸化(特に長鎖脂肪酸)や過酸化水素の生成・分解、コレステロールや胆汁酸の合成など多様な酸化的代謝を担う。", "名詞", "Peroxisomes break down very-long-chain fatty acids through beta-oxidation and neutralize the resulting hydrogen peroxide with catalase.", "生物学", "970"),
    ("photoperiodism", "生物が1日のうちの明期・暗期の長さ(日長)の季節変化を感知し、開花・休眠・渡り・繁殖などの生理的・行動的反応を調節する現象。植物では日長に対する反応から短日植物・長日植物・中性植物に分類される。", "名詞", "Photoperiodism allows short-day plants to flower only when the length of uninterrupted darkness exceeds a critical duration.", "生物学", "970"),
    ("phylogenetic tree", "生物種や遺伝子などの間の進化的な類縁関係を、共通祖先からの分岐の順序として枝分かれ図で表したもの。分子データ(DNA・タンパク質配列)や形態データに基づき、最節約法・最尤法・ベイズ法などの方法で推定される。", "名詞句", "A phylogenetic tree built from DNA sequence data can reveal how closely related two species are.", "生物学", "880"),
    ("pluripotency", "一つの細胞が、内胚葉・中胚葉・外胚葉という3つの胚葉すべてに由来する細胞種へと分化する能力を持つが、胎盤などの胚体外組織は形成できない状態。胚性幹細胞(ES細胞)や人工多能性幹細胞(iPS細胞)がこの性質を持つ。", "名詞", "Embryonic stem cells retain pluripotency, meaning they can differentiate into cells of all three germ layers.", "生物学", "950"),
    ("promoter (genetics)", "遺伝子の転写開始点の上流に位置するDNA配列で、RNAポリメラーゼや転写因子が結合することで転写の開始位置と頻度を制御する。真核生物ではTATAボックスなどのコアプロモーター配列がしばしば見られる。", "名詞", "RNA polymerase binds to the promoter region to initiate transcription of the downstream gene.", "生物学", "920"),
    ("punctuated equilibrium", "進化は一定の速度でゆっくり連続的に進むのではなく、長期間ほとんど変化しない安定期(平衡状態)と、比較的短期間に急速な種分化が起こる時期とが交互に現れるとする進化モデル。断続平衡説。", "名詞句", "The theory of punctuated equilibrium suggests that species can remain largely unchanged for millions of years before evolving rapidly.", "生物学", "980"),
    ("refractory period (neuroscience)", "神経細胞が活動電位を発生させた直後、次の活動電位を発生させることが一時的に困難、または通常より強い刺激を要する期間。新たな活動電位が全く発生しない絶対不応期と、通常より強い刺激があれば発火しうる相対不応期に分けられる。", "名詞句", "During the absolute refractory period, a neuron cannot fire another action potential no matter how strong the stimulus is.", "生物学", "970"),
    ("regeneration (biology)", "生物が失われた組織・器官・体の一部を、成体になってから新たに作り直す現象。プラナリアやイモリ・アホロートルなど再生能力の高い生物では、四肢や眼、さらには体全体に近い部分まで再生できる例が知られる。", "名詞", "Planarians are famous for their remarkable regeneration ability, as a single worm can regrow a whole body from a small fragment.", "生物学", "900"),
    ("reproductive isolation", "同種または近縁な集団間で、交配が妨げられたり、交配しても生存力・繁殖力のある子孫が生じなかったりすることで、遺伝子流動が妨げられている状態。種分化が完了したことを示す重要な基準の一つとされる。", "名詞句", "Reproductive isolation between two populations can arise from differences in mating season, habitat, or courtship behavior.", "生物学", "930"),
    ("resting potential", "神経細胞などの興奮性細胞が刺激を受けていない状態で細胞膜内外に維持している電位差。典型的な神経細胞では細胞内が細胞外に対して約-70mVとなっており、カリウムイオンに対する膜透過性の高さとNa+/K+-ATPaseによるイオン濃度勾配の維持によって生じる。", "名詞句", "A typical neuron maintains a resting potential of about -70 mV across its plasma membrane.", "生物学", "930"),
    ("restriction enzyme", "特定の塩基配列(認識配列)を識別し、その部位でDNAの二本鎖を切断する酵素。細菌が自らのDNAをメチル化によって保護する一方、外来のバクテリオファージDNAを切断して排除する「宿主による制限」という防御機構に由来する。", "名詞句", "EcoRI is a restriction enzyme that recognizes the palindromic sequence GAATTC and cuts the DNA backbone at a specific point within it.", "生物学", "900"),
    ("RNA interference", "二本鎖RNAが引き金となって、それと相補的な配列を持つmRNAを配列特異的に分解し、対応する遺伝子の発現を抑制する現象・機構。低分子干渉RNA(siRNA)やマイクロRNA(miRNA)がこの経路に関与し、遺伝子機能の研究や治療薬開発に広く応用されている。", "名詞句", "Researchers use RNA interference to silence a specific gene and observe the resulting phenotype.", "生物学", "950"),
    ("RNA splicing", "真核生物の一次転写産物(前駆mRNA)から、タンパク質をコードしない介在配列(イントロン)を除去し、コードする配列(エキソン)同士をつなぎ合わせてmRNAを完成させる過程。スプライソソームと呼ばれるRNA-タンパク質複合体によって触媒される。選択的スプライシングにより、1つの遺伝子から複数種類のタンパク質が作られ得る。", "名詞句", "During RNA splicing, the spliceosome removes introns from the pre-mRNA and joins the exons together.", "生物学", "930"),
    ("second messenger", "ホルモンや神経伝達物質などの細胞外シグナル分子(ファーストメッセンジャー)が細胞膜上の受容体に結合した際、細胞内で新たに産生・放出され、シグナルを増幅しながら細胞内の標的に伝える低分子。環状AMP(cAMP)、イノシトール三リン酸(IP3)、Ca2+イオンなどが代表例。", "名詞句", "Cyclic AMP acts as a second messenger that activates protein kinase A in response to hormone binding at the cell surface.", "生物学", "950"),
    ("selective pressure", "ある環境において特定の表現型・遺伝子型を持つ個体の生存や繁殖成功を優位または不利にし、集団内の対立遺伝子頻度の変化(自然選択)を引き起こす環境要因の強さ。捕食・病原体・気候・資源競争・配偶者選択などが淘汰圧として働く。", "名詞句", "Antibiotic overuse creates strong selective pressure that favors the survival and spread of resistant bacteria.", "生物学", "880"),
    ("sexual selection", "配偶相手をめぐる同性個体間の競争(同性内選択)や、異性による配偶相手の選り好み(異性間選択)によって生じる自然選択の一形態。生存に直接有利でなくても配偶成功を高める形質(クジャクの飾り羽など)を進化させうる。", "名詞句", "The elaborate tail of the peacock is a classic example of a trait favored by sexual selection through female mate choice.", "生物学", "900"),
    ("signal transduction", "細胞外からの化学的・物理的シグナル(ホルモン・神経伝達物質・光など)が細胞膜上または細胞内の受容体に受容された後、一連の分子的変化を経て細胞内の応答(酵素活性化・遺伝子発現変化など)に変換される過程全体。", "名詞句", "Signal transduction pathways often involve a cascade of protein kinases that amplify the original signal.", "生物学", "930"),
    ("Southern blot", "制限酵素で断片化したDNAをゲル電気泳動で分離した後、膜(通常ナイロン膜)に転写(ブロッティング)し、標識したプローブとのハイブリダイゼーションによって特定のDNA配列を検出する実験手法。", "名詞句", "A Southern blot can confirm whether a gene of interest has been successfully inserted into a genome.", "生物学", "970"),
    ("stem cell", "自己複製能(分裂して自分と同じ未分化な細胞を作る能力)と、複数種類の特殊化した細胞へ分化する能力を併せ持つ未分化な細胞。分化能の範囲によって全能性・多能性・多分化能などに分類され、胚性幹細胞や成体組織中の組織幹細胞(造血幹細胞など)がある。", "名詞", "Hematopoietic stem cells in the bone marrow can self-renew and differentiate into all types of blood cells.", "生物学", "850"),
    ("stem cell niche", "幹細胞が生体内で存在する特定の微小環境で、周囲の支持細胞・細胞外基質・シグナル分子との相互作用を通じて、幹細胞の自己複製能の維持や分化のタイミングを制御する場。", "名詞句", "The stem cell niche provides signals that keep hematopoietic stem cells in a quiescent, self-renewing state.", "生物学", "970"),
    ("stomata", "植物の葉や茎の表皮に存在する、一対の孔辺細胞に囲まれた小さな開口部(複数形。単数形はstoma)。二酸化炭素や酸素の交換、および蒸散による水蒸気の放出を行う経路であり、孔辺細胞の膨圧変化によって開閉が調節される。", "名詞", "Stomata typically open during the day to allow carbon dioxide uptake for photosynthesis and close at night to reduce water loss.", "生物学", "870"),
    ("synapse", "ニューロン(またはニューロンと効果器)の間で情報が伝達される特殊化した接合部位。化学シナプスでは、シナプス前細胞から放出された神経伝達物質がシナプス間隙を拡散してシナプス後細胞の受容体に結合することで信号が伝わり、電気シナプスではギャップ結合を通じてイオン電流が直接流れる。", "名詞", "At a chemical synapse, neurotransmitter molecules diffuse across the synaptic cleft to bind receptors on the postsynaptic cell.", "生物学", "870"),
    ("synaptic transmission", "シナプス前ニューロンで発生した活動電位が、シナプスを介してシナプス後細胞に信号を伝える過程。化学シナプスでは、Ca2+流入→シナプス小胞の開口放出→神経伝達物質の放出→受容体結合→シナプス後電位の発生、という一連の段階を経る。", "名詞句", "Synaptic transmission at a chemical synapse begins when an action potential opens voltage-gated calcium channels at the axon terminal.", "生物学", "920"),
    ("T cell", "骨髄で作られたリンパ球前駆細胞が胸腺(thymus)で成熟することから名付けられた免疫細胞。細胞表面のT細胞受容体によってMHC分子に提示された抗原を認識する。ウイルス感染細胞などを直接破壊するキラーT細胞(CD8陽性)、他の免疫細胞を活性化・調節するヘルパーT細胞(CD4陽性)、免疫応答を抑制する制御性T細胞などに分類される。", "名詞句", "Cytotoxic T cells recognize infected cells displaying viral antigens on MHC class I molecules and kill them directly.", "生物学", "880"),
    ("telomere", "真核生物の染色体の末端に存在する、反復配列(ヒトではTTAGGGの繰り返し)からなる特殊な構造。DNA複製の際に末端が徐々に短くなる「末端複製問題」を緩衝し、染色体末端が損傷したDNA末端と誤認されて融合・分解されるのを防ぐ。", "名詞", "Telomeres shorten with each round of cell division, which is thought to contribute to cellular aging.", "生物学", "900"),
    ("totipotency", "1つの細胞が、胎盤などの胚体外組織を含む個体を構成する全ての種類の細胞に分化する能力を持ち、単独で完全な1個体を発生させることができる状態。受精卵や初期卵割期の割球、多くの植物の体細胞がこの性質を持つ。", "名詞", "A fertilized egg has totipotency because it can develop into every cell type of the organism, including extraembryonic tissues like the placenta.", "生物学", "970"),
    ("transcription (molecular biology)", "DNAの塩基配列情報を鋳型として、RNAポリメラーゼが相補的なRNA鎖(mRNA・tRNA・rRNAなど)を合成する過程。真核生物では核内で行われ、mRNAの場合はその後5'キャップ付加・スプライシング・ポリA鎖付加などの修飾を受けてから細胞質へ輸送される。", "名詞", "RNA polymerase carries out transcription by reading the template strand of DNA and synthesizing a complementary RNA strand.", "生物学", "880"),
    ("transcription factor", "特定のDNA配列(プロモーターやエンハンサーなど)に結合し、RNAポリメラーゼの動員や活性を促進・抑制することで、標的遺伝子の転写を調節するタンパク質。DNA結合ドメインと転写活性化(または抑制)ドメインを持つものが多い。", "名詞句", "Transcription factors bind to specific DNA sequences to regulate whether a gene is transcribed.", "生物学", "920"),
    ("transgenic organism", "遺伝子工学的手法によって、他の生物由来の遺伝子(導入遺伝子)がゲノムに人為的に組み込まれ、その形質を発現するようになった生物。害虫抵抗性や除草剤耐性を持つ農作物、疾患モデル動物などに利用される。", "名詞句", "Transgenic organisms such as Bt corn produce a bacterial protein that is toxic to certain insect pests.", "生物学", "920"),
    ("translation (molecular biology)", "リボソーム上で、mRNAの塩基配列(コドン)の情報をもとに、対応するアミノ酸をtRNAが運搬し、ペプチド結合によってつなぎ合わせてポリペプチド鎖を合成する過程。", "名詞", "During translation, the ribosome reads mRNA codons and matches them with the corresponding amino acids carried by tRNA.", "生物学", "880"),
    ("transpiration", "植物体内の水分が、主に葉の気孔を通じて水蒸気として大気中に失われる現象。根からの水の吸収・道管を通じた通道を引き起こす原動力(蒸散流)となり、ミネラルの輸送にも寄与する。", "名詞", "Transpiration through the stomata creates a negative pressure that pulls water up from the roots through the xylem.", "生物学", "880"),
    ("trophic cascade", "食物連鎖の上位に位置する捕食者の個体数変化が、間接的に下位の複数の栄養段階(被食者やさらにその餌となる生物・植物など)にまで連鎖的な影響を及ぼす現象。捕食者の減少・消失が引き起こす影響が特に注目される。", "名詞句", "The reintroduction of wolves to Yellowstone triggered a trophic cascade that reduced elk browsing and allowed willow and aspen trees to recover.", "生物学", "930"),
    ("vaccine (immunology)", "病原体そのもの(弱毒化・不活化した病原体)やその抗原の一部、あるいはその情報を投与することで、自然感染することなく獲得免疫(能動免疫)を誘導し、将来の感染に備える医薬品・製剤。", "名詞", "The measles vaccine stimulates the immune system to produce memory cells that provide long-lasting protection against the virus.", "生物学", "870"),
    ("vector (molecular biology)", "目的の遺伝子(DNA断片)を細胞内に導入し、複製または発現させるための運び手となるDNA分子。プラスミド・バクテリオファージ・ウイルス由来のベクターなどがあり、複製起点や選択マーカー(薬剤耐性遺伝子など)、目的遺伝子を挿入するためのクローニング部位を備える。", "名詞", "Researchers inserted the gene of interest into a plasmid vector before transforming it into bacterial cells.", "生物学", "880"),
    ("vesicle (cell biology)", "細胞内で脂質二重膜に囲まれた小さな球状の構造で、タンパク質・脂質・その他の物質を細胞内の特定の区画間で輸送したり、細胞外へ分泌したりする役割を担う。小胞体・ゴルジ体間の輸送小胞や、神経終末のシナプス小胞などが代表例。", "名詞", "Transport vesicles bud off from the endoplasmic reticulum and fuse with the Golgi apparatus to move proteins between compartments.", "生物学", "900"),
    ("vestigial structure", "祖先の系統では機能を持っていたが、進化の過程でその機能の多くまたは全てを失い、縮小・単純化した形で現存する構造。ヒトの虫垂や尾骨、クジラの後肢の痕跡的な骨などが代表例で、進化の証拠の一つとされる。", "名詞句", "The vestigial pelvic bones found in some whale species are remnants of the hind limbs their land-dwelling ancestors once used to walk.", "生物学", "920"),
    ("Western blot", "タンパク質の混合物をゲル電気泳動(多くはSDS-PAGE)で分子量によって分離した後、膜に転写し、特異的な抗体を用いて目的のタンパク質を検出する実験手法。", "名詞句", "A Western blot can confirm the presence and approximate size of a specific protein in a cell lysate.", "生物学", "950"),]


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
