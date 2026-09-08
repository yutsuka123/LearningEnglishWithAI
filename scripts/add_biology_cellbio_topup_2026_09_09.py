# ruff: noqa: E501
"""生物学/生化学の細胞生物学・光合成クラスタ補強(2026-09-09・authored by Claude)。ユーザー提起「光合成に関するもの、ATPとか、細胞に関するものミトコンドリアとか、転写とか」。既存の生物学(175語)/生化学(67語)への追加。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_biology_cellbio_topup_2026_09_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("cytoplasm", "真核細胞・原核細胞を問わず、細胞膜の内側で核(原核生物では核様体)を除いた領域を満たす部分。水・イオン・タンパク質などを含む半流動性の基質(細胞質基質、サイトゾル)と、その中に存在するミトコンドリアなどの細胞小器官を合わせて指す。細胞質。", "名詞", "The cytoplasm of a eukaryotic cell contains organelles such as mitochondria and the endoplasmic reticulum suspended in a jelly-like fluid.", "生物学", "550"),
    ("cell wall", "植物・菌類・多くの原核生物などの細胞で、細胞膜のさらに外側を覆う頑丈な構造。植物細胞ではセルロースを主成分とし、細胞の形を保ち、内部の浸透圧による膨圧を支えて細胞が破裂するのを防ぐ働きを持つ。細胞壁。", "名詞", "Plant cells are surrounded by a rigid cell wall made mainly of cellulose, unlike animal cells.", "生物学", "500"),
    ("vacuole", "細胞質内にある、一枚の膜(液胞膜)で囲まれた袋状の構造。植物細胞では成熟すると細胞体積の大部分を占める大きな中心液胞となり、水・イオン・老廃物などを蓄えて膨圧を生み出す。動物細胞や原生生物にも、物質の輸送や水分調節を担う小型の液胞が存在する。液胞。", "名詞", "In a mature plant cell, a single large central vacuole can take up more than 80 percent of the cell's volume.", "生物学", "600"),
    ("nucleolus", "真核細胞の核内に見られる、膜を持たない小さな構造体。リボソームRNA(rRNA)の転写と、rRNAとタンパク質からなるリボソームサブユニットの組み立てが行われる場であり、細胞分裂の際には一時的に消失し、分裂後に再形成される。核小体、核仁。", "名詞", "The nucleolus is the site inside the nucleus where ribosomal RNA is transcribed and assembled into ribosomal subunits.", "生物学", "700"),
    ("mitochondrion", "真核細胞内でATPを産生する細胞小器官、ミトコンドリアの単数形。二重の膜構造を持ち、内膜が「クリステ」と呼ばれる多数のひだを形成することで表面積を広げ、その内側の基質(マトリックス)とクリステ上で好気呼吸の後半段階(クエン酸回路や電子伝達系)が進行する。1つの細胞には通常、複数のミトコンドリアが存在する。", "名詞", "A single liver cell may contain more than a thousand mitochondria, but each individual organelle is called a mitochondrion.", "生物学", "850"),
    ("plastid", "植物や藻類の細胞に見られる、二重膜で囲まれた細胞小器官の総称。光合成を行う葉緑体(クロロプラスト)、色素を蓄えるクロモプラスト、デンプンなどを貯蔵するアミロプラストなど、機能の異なる複数の種類が含まれる。色素体。", "名詞", "Chloroplasts are just one type of plastid; others store starch or pigments instead of carrying out photosynthesis.", "生物学", "800"),
    ("rough endoplasmic reticulum", "小胞体のうち、細胞質側の表面に多数のリボソームが付着している部分。付着したリボソームで合成されたタンパク質が小胞体内腔に取り込まれ、正しい立体構造への折りたたみや糖鎖修飾を受けたのち、ゴルジ体などへ輸送される。粗面小胞体。", "名詞", "Ribosomes studding the surface of the rough endoplasmic reticulum give it a bumpy, granular appearance under an electron microscope.", "生物学", "900"),
    ("smooth endoplasmic reticulum", "小胞体のうち、表面にリボソームが付着していない滑らかな部分。脂質やステロイドホルモンの合成、炭水化物の代謝、筋細胞などにおけるカルシウムイオンの貯蔵・放出、肝細胞での薬物や毒物の解毒作用など、多様な役割を担う。滑面小胞体。", "名詞", "The smooth endoplasmic reticulum synthesizes lipids and, in muscle cells, stores calcium ions needed for contraction.", "生物学", "900"),
    ("cristae", "ミトコンドリアの内膜が内部に向かって何度も折りたたまれることで形成される、ひだ状の構造(複数形。単数形はクリスタ crista)。表面積を大幅に増やすことで、電子伝達系やATP合成酵素をより多く配置できるようにしており、好気呼吸の効率を高めている。クリステ。", "名詞", "The many folds called cristae greatly increase the surface area of the inner mitochondrial membrane.", "生物学", "900"),
    ("mitochondrial matrix", "ミトコンドリアの内膜に囲まれた内部の空間を満たす、ゲル状の基質。クエン酸回路(TCA回路)の酵素群、ミトコンドリア独自のDNA、リボソームなどを含み、クエン酸回路やピルビン酸の酸化的脱炭酸反応が進行する場となっている。ミトコンドリアマトリックス。", "名詞", "The citric acid cycle takes place in the mitochondrial matrix, not in the cristae themselves.", "生物学", "900"),
    ("granum (grana)", "葉緑体の内部で、チラコイド膜が硬貨を積み重ねたような形に密集した構造(単数形はgranum、複数形はgrana)。1つの葉緑体には数十個のグラナが存在し、グラナ同士はストロマチラコイドと呼ばれる管状の膜でつながっている。光合成の明反応の多くはこのグラナ内のチラコイド膜上で進行する。グラナ。", "名詞", "Each chloroplast contains dozens of grana, stacks of thylakoid membranes that resemble piles of coins.", "生物学", "900"),
    ("thylakoid", "葉緑体の内部にある、扁平な袋状の膜構造。膜上にクロロフィルなどの光合成色素や光化学系(フォトシステム)、電子伝達系のタンパク質複合体を配置しており、光合成の明反応(光依存反応)が進行する場となる。内部の空間はチラコイド内腔と呼ばれる。チラコイド。", "名詞", "Chlorophyll molecules embedded in the thylakoid membrane absorb light energy to drive the light-dependent reactions.", "生物学", "900"),
    ("stroma", "葉緑体の内膜の内側を満たす、ゲル状の基質。チラコイド(グラナ)がその中に浮かんだ状態で存在しており、カルビン回路の酵素(ルビスコを含む)や葉緑体独自のDNA・リボソームを含む。光合成の暗反応(光非依存反応、カルビン回路)が進行する場である。ストロマ。", "名詞", "The Calvin cycle takes place in the stroma, the fluid-filled space surrounding the thylakoids.", "生物学", "900"),
    ("photosystem", "葉緑体のチラコイド膜に埋め込まれた、光合成色素とタンパク質からなる巨大な複合体。光エネルギーを吸収し、その中心にある特殊なクロロフィル分子(反応中心)から高エネルギー電子を放出させる。吸収波長のピークの違いによってフォトシステムI(P700)とフォトシステムII(P680)の2種類が存在し、両者が協調して働くことで水の分解と電子伝達、そしてNADPHの生成を実現している。光化学系。", "名詞", "Photosystem II absorbs light most efficiently at a wavelength of 680 nanometers, while photosystem I peaks at 700 nanometers.", "生物学", "900"),
    ("NADPH", "ニコチンアミドアデニンジヌクレオチドリン酸の還元型を表す略称。光合成の明反応でNADP+が電子を受け取って生じ、葉緑体のストロマで進行するカルビン回路において、固定された二酸化炭素を糖へと還元するための還元力として使われる。NADPH。", "名詞", "NADPH generated during the light-dependent reactions supplies the reducing power needed to build sugars in the Calvin cycle.", "生物学", "900"),
    ("RuBisCO", "カルビン回路の最初の反応を触媒する酵素で、正式名称はリブロース-1,5-ビスリン酸カルボキシラーゼ/オキシゲナーゼ。大気中の二酸化炭素をリブロース1,5-ビスリン酸(RuBP)に結合させる炭素固定反応を触媒するが、酸素とも反応してしまう性質(光呼吸)を併せ持つため、触媒効率が低いことで知られる。ルビスコ。", "名詞", "RuBisCO catalyzes the very first step of the Calvin cycle by attaching carbon dioxide to a five-carbon sugar.", "生物学", "950"),
    ("carbon fixation", "大気中や水中に含まれる無機的な二酸化炭素を、生物が有機物(糖など)に変換して取り込む反応。光合成を行う植物・藻類・一部の細菌では、酵素ルビスコがカルビン回路の中で二酸化炭素をリブロース1,5-ビスリン酸に結合させることでこの反応が行われる。炭素固定。", "名詞", "Carbon fixation converts inorganic carbon dioxide into organic molecules that living things can use for energy and growth.", "生物学", "900"),
    ("photolysis", "光エネルギーによって分子が分解される反応。光合成の文脈では特に、フォトシステムIIにおいて光エネルギーを使って水分子を酸素・水素イオン(プロトン)・電子に分解する反応(水の光分解)を指し、ここで生じた電子が電子伝達系に供給され、副産物として酸素が放出される。光分解。", "名詞", "The photolysis of water inside photosystem II releases the oxygen that we breathe as a byproduct.", "生物学", "920"),
    ("light-dependent reactions", "光合成のうち、光エネルギーを直接利用する反応群の総称。葉緑体のチラコイド膜上で、フォトシステムが光エネルギーを吸収して水を分解(光分解)し、生じた電子を電子伝達系に受け渡すことでATPとNADPHを生成する。明反応。", "名詞", "The light-dependent reactions capture solar energy and convert it into the chemical energy of ATP and NADPH.", "生物学", "900"),
    ("light-independent reactions", "光合成のうち、光エネルギーを直接には利用しない反応群の総称。葉緑体のストロマで進行し、明反応で生成されたATPとNADPHのエネルギーを使って、酵素ルビスコによる炭素固定を出発点に二酸化炭素を糖へと還元する。カルビン回路と同義に使われる。暗反応。", "名詞", "The light-independent reactions use the ATP and NADPH produced earlier to convert carbon dioxide into sugar.", "生物学", "900"),
    ("ribosomal RNA (rRNA)", "リボソームを構成する主要な成分であるRNAの一種。核小体で転写され、タンパク質と結合してリボソームの大小2つのサブユニットを形成し、翻訳の際にmRNAとtRNAを正しい位置に配置しながらペプチド結合の形成を触媒する働きも担う。リボソームRNA。", "名詞", "Ribosomal RNA makes up a large part of the ribosome and even catalyzes the formation of peptide bonds during translation.", "生物学", "900"),
    ("RNA polymerase", "DNAの塩基配列を鋳型として、相補的なRNA鎖を合成する酵素。転写の際にDNAの二重らせんをほどきながら、鋳型鎖の配列に従ってヌクレオチドを次々とつなげ、mRNA・tRNA・rRNAなどのRNAを合成する。RNAポリメラーゼ。", "名詞", "RNA polymerase moves along the DNA template strand, synthesizing a complementary strand of messenger RNA.", "生物学", "900"),
    ("start codon", "mRNA上で翻訳の開始を指定する特定のコドン。多くの生物でAUG(アミノ酸のメチオニンを指定するコドンでもある)が使われ、リボソームがこの配列を認識することで、ここから読み枠(リーディングフレーム)に従って3塩基ずつ翻訳が進んでいく。開始コドン。", "名詞", "The ribosome scans the messenger RNA until it locates the start codon, AUG, and begins translation there.", "生物学", "870"),
    ("stop codon", "mRNA上で翻訳の終了を指定する3種類のコドン(UAA・UAG・UGA)の総称。これらのコドンに対応するtRNAは存在せず、代わりに解離因子と呼ばれるタンパク質が結合することで、リボソームからポリペプチド鎖が切り離され、翻訳が終結する。終止コドン。", "名詞", "When the ribosome reaches a stop codon such as UAA, no tRNA matches it and translation comes to an end.", "生物学", "870"),
    ("carotenoid", "植物・藻類・一部の細菌が持つ黄色・オレンジ・赤色系の脂溶性色素の総称。クロロフィルが吸収しにくい波長の光を吸収して光合成に利用する補助色素として働くほか、過剰な光エネルギーによる活性酸素の発生を抑える光防御の役割も担う。ニンジンの色素として知られるカロテンや、光合成色素キサントフィルなどが含まれる。カロテノイド。", "名詞", "Carotenoids absorb wavelengths of light that chlorophyll cannot capture efficiently, broadening the range of light plants can use for photosynthesis.", "生物学", "850"),
    ("nuclear envelope", "真核細胞の核を取り囲む二重の膜構造。外膜は小胞体とつながっており、内膜と外膜の間の空間は小胞体の内腔と連続している。膜には核膜孔と呼ばれる多数の穴が開いており、RNAやタンパク質などの物質が核と細胞質の間を選択的に行き来する通路となっている。核膜。", "名詞", "The nuclear envelope separates the DNA inside the nucleus from the rest of the cytoplasm.", "生物学", "800"),
    ("turgor pressure", "植物細胞などで、液胞に水が流入することで細胞内部の圧力が高まり、細胞膜が細胞壁を内側から押す圧力。この圧力によって細胞や組織に張りが生まれ、草本植物が茎や葉の形を保つのに役立っている。水が不足して膨圧が下がると、植物はしおれた状態になる。膨圧。", "名詞", "Turgor pressure keeps the stems and leaves of a non-woody plant upright and firm.", "生物学", "800"),
    ("plasmolysis", "植物細胞などを高濃度の溶液(高張液)に置いたとき、浸透によって細胞内の水が外に流出し、細胞膜が細胞壁から離れて収縮する現象。膨圧が失われて細胞がしおれた状態になり、細胞壁自体は変形しないまま原形質(細胞膜より内側の部分)だけが縮む点が特徴。原形質分離。", "名詞", "When a plant cell is placed in a highly concentrated salt solution, plasmolysis causes the cell membrane to pull away from the cell wall.", "生物学", "900"),
    ("anticodon", "転移RNA(tRNA)の一部にある、3つの塩基からなる配列。mRNA上のコドンと相補的に結合することで、コドンが指定するアミノ酸をtRNAが正しい位置に運ぶことを可能にしている。アンチコドン。", "名詞", "The anticodon on a transfer RNA molecule pairs with a complementary codon on the messenger RNA.", "生物学", "900"),
    ("pigment", "光の特定の波長を吸収し、それ以外の波長を反射・透過することで色として見える物質の総称。植物のクロロフィルやカロテノイド、動物の血液中のヘモグロビン、皮膚のメラニンなど、生物にはさまざまな色素が存在し、光合成やガス運搬、光からの保護といった機能を担っている。色素。", "名詞", "Chlorophyll is the main pigment responsible for the green color of most plant leaves.", "生物学", "600"),
    ("protein synthesis", "遺伝情報をもとに細胞内でタンパク質が作られる過程全体を指す語。狭義には、リボソーム上でmRNAの情報をもとにアミノ酸を連結する翻訳の段階のみを指すこともあるが、広義にはDNAからmRNAが作られる転写の段階も含めた一連の流れ全体を指す。タンパク質合成。", "名詞", "Protein synthesis begins with transcription in the nucleus and is completed by translation on ribosomes in the cytoplasm.", "生化学", "700"),
    ("template strand", "転写の際に、RNAポリメラーゼが読み取ってRNAを合成するための鋳型として使われるDNA鎖。合成されるRNAは、この鋳型鎖と相補的な塩基配列を持つことになる。鋳型鎖、アンチセンス鎖。", "名詞", "RNA polymerase reads the template strand in the 3' to 5' direction while synthesizing RNA in the 5' to 3' direction.", "生化学", "850"),
    ("coding strand", "転写の際に鋳型として使われない側のDNA鎖。塩基配列が、合成されるmRNAとほぼ同じ配列になる(チミンがウラシルに置き換わる点のみが異なる)ため、mRNAの配列を直接読み取りたいときの基準として使われる。非鋳型鎖、センス鎖。", "名詞", "The coding strand has almost the same sequence as the resulting mRNA, except that thymine is replaced by uracil.", "生化学", "850"),
    ("aminoacyl-tRNA", "特定のアミノ酸が結合した状態の転移RNA(tRNA)。アミノアシルtRNA合成酵素という酵素が、ATPのエネルギーを使ってアミノ酸をそれに対応するtRNAの3'末端に結合させることで作られ、リボソーム上でmRNAのコドンに応じたアミノ酸を運ぶ材料となる。アミノアシルtRNA。", "名詞", "Aminoacyl-tRNA synthetase attaches the correct amino acid to its matching tRNA, forming aminoacyl-tRNA.", "生化学", "900"),
    ("ATP synthase", "ミトコンドリアの内膜や葉緑体のチラコイド膜に埋め込まれた酵素複合体。膜を挟んだ水素イオン(プロトン)の濃度勾配にしたがってプロトンが酵素内部を通って流れ戻る際のエネルギーを利用し、ADPと無機リン酸からATPを合成する。ATP合成酵素。", "名詞", "As protons flow back through ATP synthase down their concentration gradient, the enzyme spins and synthesizes ATP.", "生化学", "900"),
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
