# ruff: noqa: E501
"""動物(類人猿)・動物(旧人類)新ドメイン(2026-09-09・authored by Claude)。ユーザー提起「動物（類人猿）動物（旧人類）が必要かも」。既存動物(哺乳類)のgorilla/chimpanzee/orangutan/monkeyとは重複させない方針で新設。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_apes_archaic_humans_2026_09_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("bonobo", "ボノボ", "名詞", "Bonobos, unlike common chimpanzees, are known for resolving social conflicts through affectionate behavior rather than aggression.", "動物(類人猿)", "600"),
    ("gibbon", "テナガザル", "名詞", "Gibbons swing gracefully from branch to branch using their long arms, a movement called brachiation.", "動物(類人猿)", "500"),
    ("siamang", "フクロテナガザル(シアマン)", "名詞", "The siamang is the largest species of gibbon and can be recognized by its loud, booming calls.", "動物(類人猿)", "750"),
    ("mountain gorilla", "マウンテンゴリラ", "名詞", "Mountain gorillas live in the cool, high-altitude forests of the Virunga Mountains in central Africa.", "動物(類人猿)", "550"),
    ("western lowland gorilla", "ニシローランドゴリラ", "名詞", "The western lowland gorilla is the gorilla subspecies most commonly seen in zoos around the world.", "動物(類人猿)", "700"),
    ("silverback", "背中の毛が銀白色になった、群れを率いる成熟したオスのゴリラを指す「シルバーバック」", "名詞", "The silverback is usually the dominant male who leads and protects the gorilla troop.", "動物(類人猿)", "550"),
    ("Sumatran orangutan", "スマトラオランウータン", "名詞", "The Sumatran orangutan is critically endangered due to the destruction of its rainforest habitat.", "動物(類人猿)", "650"),
    ("Bornean orangutan", "ボルネオオランウータン", "名詞", "The Bornean orangutan has a broader face and shorter beard than its Sumatran relative.", "動物(類人猿)", "650"),
    ("great ape", "ゴリラ・チンパンジー・ボノボ・オランウータン・ヒトなど、体が大きく尾を持たない類人猿のグループを指す「大型類人猿」", "名詞", "Humans are classified as great apes, along with gorillas, chimpanzees, bonobos, and orangutans.", "動物(類人猿)", "600"),
    ("lesser ape", "テナガザル科に属する、大型類人猿より体の小さい類人猿のグループを指す「小型類人猿」", "名詞", "Gibbons and siamangs are known as lesser apes because of their smaller size compared to great apes.", "動物(類人猿)", "700"),
    ("knuckle-walking", "指の関節(拳)を地面につけて体を支えながら歩く、ゴリラやチンパンジーに見られる四足歩行を指す「ナックルウォーキング」", "名詞", "Gorillas and chimpanzees move on the ground mainly by knuckle-walking, supporting their weight on their curled fingers.", "動物(類人猿)", "750"),
    ("brachiation", "長い腕を使って枝から枝へと勢いよく渡り歩く移動方法を指す「腕渡り(ブラキエーション)」", "名詞", "Brachiation lets gibbons travel through the treetops faster than almost any other mammal.", "動物(類人猿)", "800"),
    ("tailless", "尾を持たないことを表す語で、多くのサルと類人猿を区別する特徴とされる「無尾」", "形容詞", "One easy way to tell an ape from a monkey is that apes are tailless.", "動物(類人猿)", "600"),
    ("arboreal", "木の上で生活し、ほとんどの時間を樹上で過ごす性質を表す「樹上性の」", "形容詞", "Orangutans are the most arboreal of the great apes, spending most of their lives in the trees.", "動物(類人猿)", "800"),
    ("opposable thumb", "他の指と向かい合わせに動かして物をしっかりつかめる親指の構造を指す「対向性母指」", "名詞", "An opposable thumb allows apes to grip branches, tools, and food with precision.", "動物(類人猿)", "600"),
    ("opposable big toe", "他の指と向かい合わせに動かして枝などをつかめる足の親指の構造を指す「対向性の足の親指(母趾)」", "名詞", "Unlike humans, most apes have an opposable big toe that works almost like a second thumb.", "動物(類人猿)", "750"),
    ("mirror test", "動物が鏡に映った姿を自分自身だと認識できるかどうかを調べる実験を指す「ミラーテスト(鏡像自己認知テスト)」", "名詞", "Chimpanzees are one of the few animals that can pass the mirror test, recognizing their own reflection.", "動物(類人猿)", "800"),
    ("self-recognition", "鏡に映った自分の姿を自分だと理解する能力を指す「自己認識」", "名詞", "Self-recognition in mirrors is considered a sign of advanced cognitive ability in great apes.", "動物(類人猿)", "800"),
    ("tool use", "枝や石などの物を道具として利用する行動を指す「道具使用」", "名詞", "Jane Goodall's observation of tool use in wild chimpanzees changed how scientists viewed animal intelligence.", "動物(類人猿)", "650"),
    ("alpha male", "群れの中で最も優位な地位にあるオスを指す「アルファオス」", "名詞", "The alpha male chimpanzee often maintains his rank through alliances rather than strength alone.", "動物(類人猿)", "600"),
    ("social grooming", "仲間の毛づくろいをして絆を強め合う社会的行動を指す「社会的毛づくろい」", "名詞", "Social grooming helps apes strengthen bonds and reduce tension within the group.", "動物(類人猿)", "700"),
    ("chest-beating", "両手で自分の胸を叩いて威嚇や自己主張を示す、ゴリラなどに見られる行動を指す「胸叩き(チェストビーティング)」", "名詞", "A gorilla's chest-beating display is often a warning rather than a sign of imminent attack.", "動物(類人猿)", "700"),
    ("critically endangered", "絶滅の危険性が最も高い分類に位置づけられていることを表す「絶滅寸前種の」", "形容詞", "All species of orangutan are now classified as critically endangered by conservationists.", "動物(類人猿)", "700"),
    ("poacher", "野生動物を違法に狩猟する人(密猟者)", "名詞", "A poacher was arrested after setting snares in the gorillas' protected forest.", "動物(類人猿)", "600"),
    ("bushmeat", "食用として狩られた野生動物の肉を指す「ブッシュミート」", "名詞", "The illegal bushmeat trade has pushed several ape populations toward extinction.", "動物(類人猿)", "800"),
    ("sanctuary", "傷ついたり保護が必要になったりした野生動物のための保護区・保護施設", "名詞", "The sanctuary provides a safe home for orphaned orangutans until they can be released back into the wild.", "動物(類人猿)", "550"),
    ("wildlife rehabilitation", "けがをしたり親を失ったりした野生動物を保護・訓練して自然に戻す取り組みを指す「野生復帰支援(リハビリテーション)」", "名詞", "Wildlife rehabilitation centers teach orphaned young apes the skills they need to survive in the forest.", "動物(類人猿)", "800"),
    ("primatologist", "サルや類人猿など霊長類を研究する専門家を指す「霊長類学者」", "名詞", "Primatologist Jane Goodall spent decades studying wild chimpanzees in Tanzania.", "動物(類人猿)", "750"),
    ("captive breeding program", "動物園などの飼育下で計画的に繁殖させ、絶滅危惧種を守る取り組みを指す「飼育下繁殖計画」", "名詞", "Zoos around the world take part in captive breeding programs to help save endangered ape species.", "動物(類人猿)", "800"),
    ("conservation status", "ある生物種がどれほど絶滅の危機にあるかを段階的に示す分類を指す「保全状況」", "名詞", "Scientists regularly review the conservation status of great apes based on population surveys.", "動物(類人猿)", "800"),
    ("rewilding", "飼育されていた動物や失われた生態系を自然な状態に戻す取り組みを指す「野生復帰(リワイルディング)」", "名詞", "Rewilding projects aim to return captive-born apes to a life in their natural habitat.", "動物(類人猿)", "800"),
    ("ape", "類人猿。また、(動詞として)人の真似をする、模倣するという意味でも使われる", "名詞・動詞", "Apes, unlike monkeys, do not have tails and generally have larger brains relative to their body size.", "動物(類人猿)", "500"),
    ("simian", "サルや類人猿に関すること、またはそれらに似ていることを表す語「類人猿の、サル類の」", "形容詞・名詞", "The zoo's simian house is home to gorillas, chimpanzees, and several species of monkey.", "動物(類人猿)", "850"),
    ("troop", "サルや類人猿などが作る群れを指す「群れ」", "名詞", "A gorilla troop is usually led by a single dominant silverback male.", "動物(類人猿)", "600"),
    ("vocalization", "動物が声を出してコミュニケーションをとることを指す「発声、鳴き声」", "名詞", "Gibbon vocalizations can carry for great distances through dense forest.", "動物(類人猿)", "800"),
    ("fission-fusion society", "群れの構成員が状況に応じて分裂したり再び合流したりする、チンパンジーなどに見られる社会構造を指す「離合集散型社会」", "名詞", "Chimpanzees live in a fission-fusion society, splitting into small groups during the day and reuniting later.", "動物(類人猿)", "900"),
    ("sexual dimorphism", "オスとメスで体の大きさや外見が大きく異なることを指す「性的二形」", "名詞", "Gorillas show strong sexual dimorphism, with males often much larger than females.", "動物(類人猿)", "850"),
    ("illegal wildlife trade", "絶滅危惧種を含む野生動物を違法に売買・密輸することを指す「違法な野生生物取引」", "名詞", "Baby chimpanzees captured for the illegal wildlife trade often lose their entire family in the process.", "動物(類人猿)", "800"),
    ("Neanderthal", "約24万年前(諸説あり)から4万年前頃までヨーロッパから西アジア・中央アジアにかけて生息していた絶滅人類。現生人類(ホモ・サピエンス)より頑丈な体格と平均してやや大きな脳を持ち、道具の使用や死者の埋葬などの行動が確認されている。現生人類との交雑が起きたことがDNA研究で明らかになっており、非アフリカ系現代人のゲノムの約1.8~2.6%はネアンデルタール人由来とされる。ネアンデルタール人。", "名詞", "Genetic studies suggest that most people of non-African descent carry a small percentage of Neanderthal DNA.", "動物(旧人類)", "650"),
    ("Homo erectus", "約190万年前から数十万年前(一部の化石は約11万年前)まで生息していたとされる絶滅人類。アフリカで誕生した後、人類として初めてアフリカを出てアジア・ヨーロッパへと拡散したと考えられている。直立した姿勢と現代人に近い体型を持ち、アシューリアン型の握斧(ハンドアックス)を製作した。ホモ・エレクトス(直立原人)。", "名詞", "Homo erectus is widely regarded as the first hominin species to migrate out of Africa and spread across Asia.", "動物(旧人類)", "680"),
    ("Homo habilis", "約240万年前から160万年前頃まで東アフリカに生息していたとされる絶滅人類。石器を製作していた証拠が確認された最初期の人類種の一つとして知られ、その種小名は「器用な人」を意味する。オルドワン石器文化と関連づけられる。ホモ・ハビリス(器用な人)。", "名詞", "Homo habilis takes its name, meaning 'handy man,' from its association with early stone tools.", "動物(旧人類)", "700"),
    ("Homo sapiens", "現生人類を指す正式な学名(種名)。「賢い人」を意味するラテン語に由来し、日常語の「人間(human)」よりも、生物学的な種としての現生人類を明確に指す語として使われる。モロッコのジェベル・イルード遺跡の化石研究(2017年発表)などから、少なくとも約30万年前にはアフリカで出現していたと考えられている。ホモ・サピエンス。", "名詞", "Homo sapiens is the scientific name for modern humans, distinguishing our species from extinct relatives like Neanderthals.", "動物(旧人類)", "620"),
    ("Australopithecus", "約420万年前から200万年前頃までアフリカに生息していた化石人類の属名。直立二足歩行をしていたが、脳容量は現代人の3分の1程度と小さく、樹上生活に適応した特徴も一部残していた。ホモ属やパラントロプス属の祖先にあたると考えられている。アウストラロピテクス属。", "名詞", "Australopithecus walked upright on two legs but still had a brain only about the size of a modern chimpanzee's.", "動物(旧人類)", "700"),
    ("Australopithecus afarensis", "約390万年前から290万年前頃まで東アフリカに生息していたアウストラロピテクス属の一種。有名な化石「ルーシー」が属することで知られ、直立二足歩行をしていたことが骨格の特徴から確認されている。アウストラロピテクス・アファレンシス。", "名詞", "Australopithecus afarensis is best known through the famous fossil skeleton nicknamed 'Lucy.'", "動物(旧人類)", "720"),
    ("Denisovan", "2010年にDNA解析によって存在が確認された絶滅人類の一集団。シベリアのデニソワ洞窟で発見された指の骨などの少量の化石から知られ、ネアンデルタール人とも現生人類とも異なる独自の系統であることが判明した。現生人類やネアンデルタール人と交雑していたことが分かっており、メラネシアの人々など一部の現代人集団のゲノムに数%程度のデニソワ人由来のDNAが受け継がれている。デニソワ人。", "名詞", "Denisovans are known almost entirely from DNA rather than complete skeletons.", "動物(旧人類)", "720"),
    ("Cro-Magnon", "ヨーロッパに現れた初期の現生人類(ホモ・サピエンス)を指す通称。正式な分類学上の名称ではなく、化石が発見された地名にちなむ通俗的な呼び名だが、一般向けの解説では今も広く使われる。約4万年前から1万年ほど前にかけてヨーロッパで暮らし、洞窟壁画などの文化を残したとされる。クロマニョン人。", "名詞", "Cro-Magnon people are often credited with creating some of the earliest known cave art in Europe.", "動物(旧人類)", "680"),
    ("Homo floresiensis", "2003年にインドネシアのフローレス島リアンブア洞窟で発見された小型の絶滅人類。身長約1メートルほどしかない極端に小柄な体格から「ホビット」の愛称で知られる。約5万年前頃まで生息していたとされ、その起源についてはホモ・エレクトスが島で小型化(島嶼矮小化)したとする説が有力視されているが、より原始的な系統に由来するとの説も一部で唱えられている。ホモ・フロレシエンシス。", "名詞", "Homo floresiensis, nicknamed 'the hobbit,' stood only about a meter tall.", "動物(旧人類)", "700"),
    ("Paranthropus", "約290万年前から100万年前頃までアフリカに生息していた化石人類の属。頑丈な顎と大きな臼歯、頭骨の正中線上に隆起した矢状稜(さじょうりょう)を持ち、これらは強力な咀嚼筋を支えるための構造と考えられている。硬い木の実を噛み砕いていたとする従来の見方は近年見直され、実際には柔らかい植物を主に食べていた可能性が指摘されている。パラントロプス属(頑丈型アウストラロピテクス)。", "名詞", "Paranthropus species had massive jaws and large molars adapted for heavy chewing.", "動物(旧人類)", "780"),
    ("Homo naledi", "2013年に南アフリカのライジングスター洞窟群で発見された絶滅人類。脳容量が約465~610cm³とアウストラロピテクス並みに小さいにもかかわらず、化石の年代測定(2017年発表)では約33万5000年前から23万6000年前という比較的新しい時代のものと判明し、原始的な特徴を持つ人類が現生人類の登場と近い時代までアフリカで生き残っていたことを示す発見として注目された。仲間の遺体を洞窟の奥深くに意図的に運び込んでいた可能性も指摘されているが、この「埋葬説」には異論も出ており議論が続いている。ホモ・ナレディ。", "名詞", "Homo naledi had a brain roughly the size of an orange, yet it lived far more recently than its primitive anatomy would suggest.", "動物(旧人類)", "780"),
    ("hominid", "分類学上の科(ヒト科、Hominidae)に属する動物の総称。現生種ではオランウータン・ゴリラ・チンパンジー(ボノボ含む)・ヒトが含まれ、それぞれの絶滅した近縁種も含む、比較的広い範囲を指す語。かつてはヒトだけ、あるいは大型類人猿からヒトを除いた意味で使われていた時期もあり、用語の指す範囲は歴史的に変化してきた。ヒト科(の動物)。", "名詞", "Gorillas, chimpanzees, orangutans, and humans are all classified as hominids.", "動物(旧人類)", "750"),
    ("hominin", "分類学上の族(ヒト族、Hominini)に属する動物を指す語で、「hominid(ヒト科)」よりも狭い範囲を示す。現在広く使われている用法では、チンパンジーの系統と分かれた後のヒトの系統に連なる、ホモ属とその近縁の絶滅種(アウストラロピテクス属なども含む)を指すことが多く、ゴリラは含まれない。学術的な文脈によってはチンパンジー・ボノボの系統(Pan属)を含める分類もあり、用語の厳密な範囲は文献によって差がある。ヒト族(の動物)。", "名詞", "Neanderthals, Homo erectus, and Australopithecus are all considered hominins, but gorillas are not.", "動物(旧人類)", "830"),
    ("human evolution", "類人猿と共通の祖先を持つ系統から、現在の現生人類(ホモ・サピエンス)に至るまでの、数百万年にわたる生物学的な進化の過程全体を指す語。アウストラロピテクスなどの初期猿人から、ホモ・エレクトスなどの原人、ネアンデルタール人などの旧人を経て現生人類へと至る、枝分かれの多い系統関係として理解されている。人類進化。", "名詞", "Fossil discoveries in Africa have reshaped our understanding of human evolution many times over the past century.", "動物(旧人類)", "620"),
    ("common ancestor", "複数の異なる種や系統が、進化の過程をさかのぼると行き着く、共通の祖先種を指す語。例えば現生人類とチンパンジーは、数百万年前に存在した共通祖先から分かれて進化したと考えられている。かつて俗に使われた「ミッシングリンク」という表現に代わり、学術的な文脈ではこの語がより適切な表現として好まれる。共通祖先。", "名詞", "Humans and chimpanzees share a common ancestor that lived several million years ago, rather than one species evolving directly into the other.", "動物(旧人類)", "680"),
    ("evolutionary lineage", "ある生物種や集団が、進化の過程で祖先から子孫へとたどってきた系統のつながりを指す語。人類進化の文脈では、共通祖先から枝分かれした複数の系統のうち、現生人類につながる特定の系譜を指して使われることが多い。進化系統、系統。", "名詞", "Neanderthals represent a separate evolutionary lineage that diverged from the ancestors of modern humans hundreds of thousands of years ago.", "動物(旧人類)", "760"),
    ("interbreeding", "異なる種や、地理的・生殖的に隔てられていた集団同士が交配し、子孫を残すこと。人類進化の文脈では、現生人類とネアンデルタール人、あるいは現生人類とデニソワ人といった、別々に進化してきた人類集団同士の交配を指すことが多い。古代DNAの解析技術の発達により、こうした交雑が実際に起きていたことが2010年代以降に相次いで明らかになった。交雑、異種交配。", "名詞", "DNA evidence indicates that interbreeding occurred between modern humans and Neanderthals tens of thousands of years ago.", "動物(旧人類)", "700"),
    ("ancient DNA", "化石や遺骨など、数千年から数十万年前の古い生物学的試料から抽出・解析される、劣化・断片化したDNA。ネアンデルタール人やデニソワ人のゲノム解読など、骨や歯の化石だけでは分からなかった絶滅人類の姿や、現生人類との交雑の実態を明らかにする上で重要な役割を果たしてきた。古代DNA。", "名詞", "Advances in extracting ancient DNA from fossils have transformed our understanding of human evolution over the past two decades.", "動物(旧人類)", "720"),
    ("fossil record", "ある地域や時代について、これまでに発見・記録されてきた化石全体の集積を指す語。人類進化の研究は主にこの化石記録に基づいて行われるが、化石として残る条件は非常に限られているため、記録には大きな空白(欠落)が存在することが知られている。化石記録。", "名詞", "The human fossil record is remarkably incomplete, since fossilization requires very specific conditions.", "動物(旧人類)", "700"),
    ("missing link", "進化の系統において、ある種から別の種へとつながる、まだ発見されていない中間段階の生物を指す通俗的な表現。特に「サルとヒトの間をつなぐ生物」という意味で広く使われてきたが、進化は一本の鎖のように直線的に進むものではなく枝分かれする樹木のように進むため、専門家はこの表現を科学的に不正確なものとして避け、代わりに「共通祖先(common ancestor)」という語を好んで使う。ミッシングリンク。", "名詞", "The term 'missing link' is popular in the media, but most paleoanthropologists consider it misleading.", "動物(旧人類)", "780"),
    ("bipedalism", "二本の後肢だけを使って直立して歩く移動様式。人類進化の初期段階、脳が大きくなるよりも先に獲得された特徴とされ、アウストラロピテクスの骨盤や脚の骨の構造から、少なくとも約390万年前にはすでに直立二足歩行が確立していたことが分かっている。直立二足歩行。", "名詞", "Bipedalism freed the hands of early hominins for carrying objects and using tools.", "動物(旧人類)", "700"),
    ("stone tool", "石を打ち欠いたり磨いたりして作られた道具の総称。人類の技術発展を示す最古級の証拠の一つとされ、現在確認されている最古の石器は約330万年前(ロメクウィ遺跡)まで遡るとされる。狩猟や解体、加工など幅広い用途に使われた。石器。", "名詞", "The earliest known stone tools predate the genus Homo, suggesting that even earlier hominins were capable of toolmaking.", "動物(旧人類)", "620"),
    ("Paleolithic", "人類が石器を使い始めた時代から、農耕が始まる以前までの、旧石器時代を指す語。一般には約260万年前(あるいはそれ以前)から、農耕や定住が始まる約1万年前頃までの、非常に長い期間を指す。狩猟採集を生活の基盤としていた時代にあたる。旧石器時代(の)。", "名詞", "Most of human history took place during the Paleolithic, long before agriculture was invented.", "動物(旧人類)", "700"),
    ("Stone Age", "金属器が本格的に使われるようになる以前の、石器を主要な道具とした先史時代全体を指す通俗的な区分。旧石器時代・中石器時代・新石器時代に細分され、地域によって終了時期は大きく異なる。石器時代。", "名詞", "The Stone Age is traditionally divided into the Paleolithic, Mesolithic, and Neolithic periods.", "動物(旧人類)", "620"),
    ("cave painting", "洞窟の壁や天井に描かれた先史時代の絵画。フランスのショーヴェ洞窟(約3万~3万5000年前)やラスコー洞窟(約1万7000年前)が有名だが、インドネシアのスラウェシ島では5万年以上前に遡るとされる絵が見つかっている。スペインの一部の洞窟壁画については、現生人類がヨーロッパに到達する以前の年代が示され、ネアンデルタール人が描いた可能性を指摘する研究もあり、議論が続いている。洞窟壁画。", "名詞", "The cave paintings at Chauvet in France are among the oldest and best-preserved examples of Ice Age art.", "動物(旧人類)", "630"),
    ("hunter-gatherer", "農耕や牧畜を行わず、野生の動植物を狩猟・採集することで食料を得て生活する人々、またはその生活様式を指す語。人類の歴史の大部分はこの狩猟採集の生活様式のもとで営まれてきたとされ、約1万年前に農耕が始まって以降も、一部の集団は現在に至るまでこの生活様式を続けている。狩猟採集民、狩猟採集の。", "名詞", "For most of human history, people lived as hunter-gatherers rather than farmers.", "動物(旧人類)", "650"),
    ("Out of Africa theory", "現生人類(ホモ・サピエンス)がアフリカで進化し、そこから世界各地へ拡散していったとする学説。約30万~20万年前にアフリカで出現した現生人類が、約7万~5万年前頃にアフリカを出て世界に広がったとする内容で、現在のところ人類の起源に関する学説の中で最も広く支持されている。対立する仮説である「多地域進化説」に代わって主流となった。「アフリカ単一起源説」、「出アフリカ説」。", "名詞", "The Out of Africa theory holds that all modern humans outside Africa descend from a population that left the continent tens of thousands of years ago.", "動物(旧人類)", "800"),
    ("multiregional hypothesis", "現生人類は単一の起源地から拡散したのではなく、ホモ・エレクトスなどの旧い人類集団が世界各地で並行して現生人類へと進化し、その間も地域間で継続的な遺伝子の交流(遺伝子流動)があったとする仮説。1980年代にミルフォード・ウォルポフらによって提唱されたが、その後の遺伝学研究の進展により、現在では「アフリカ単一起源説」が主流となり、この仮説の元の形は支持を失っている。多地域進化説。", "名詞", "The multiregional hypothesis proposed that modern humans evolved simultaneously in several parts of the world, connected by ongoing gene flow.", "動物(旧人類)", "870"),
    ("Lucy", "1974年にエチオピアのハダール遺跡で発見された、アウストラロピテクス・アファレンシスの有名な化石(標本番号AL 288-1)の愛称。全身骨格の約40%が保存されており、約320万年前のものと推定される。骨盤や脚の骨の構造から、既にこの時代に直立二足歩行が確立していたことを示す代表的な証拠として知られる。「ルーシー」。", "名詞", "Lucy's skeleton provided some of the strongest early evidence that our ancestors walked upright long before they had large brains.", "動物(旧人類)", "680"),
    ("Neanderthal extinction", "約4万年前頃までにヨーロッパ・西アジアからネアンデルタール人が姿を消した出来事、およびその原因をめぐる研究上の論点。単一の決定的な原因が特定されているわけではなく、現生人類の到来にともなう資源競争や交雑による同化、もともと個体数が少なかったことによる近親交配や遺伝的な不利、気候変動など、複数の要因が組み合わさった結果と考えられている。ネアンデルタール人の絶滅。", "名詞", "The causes of Neanderthal extinction remain debated, with researchers pointing to competition with modern humans, small population size, and climate change as likely contributing factors.", "動物(旧人類)", "780"),
    ("brow ridge", "眼窩(眼球が収まる骨のくぼみ)の上部に張り出した、骨の隆起部分。ホモ・エレクトスやネアンデルタール人など多くの絶滅人類種で顕著に発達していたのに対し、現生人類(ホモ・サピエンス)では大きく縮小している特徴の一つ。頑丈な咀嚼に伴う力を分散させる構造的な役割や、他個体への視覚的な誇示・威嚇の役割など複数の仮説が唱えられているが、その機能については今も研究が続いている。眉弓(びきゅう)、眉庇(びさし)。", "名詞", "Neanderthals had a much more pronounced brow ridge than modern humans do.", "動物(旧人類)", "760"),
    ("cranial capacity", "頭骨の内部の容積、すなわち脳を収めていた空間の大きさを立方センチメートル(cm³)で表した数値。人類進化の研究において、脳の大きさの変化を比較する基本的な指標として用いられる。興味深いことに、ネアンデルタール人の平均的な脳容量(約1200~1750cm³)は、現代人の平均(約1400cm³)を上回っていたと考えられている。脳容量。", "名詞", "Cranial capacity increased dramatically over the course of human evolution, from under 500 cubic centimeters in early hominins to around 1,400 in modern humans.", "動物(旧人類)", "760"),
    ("paleoanthropology", "化石やその他の物的証拠に基づいて、人類の起源と進化の過程を研究する学問分野。人類学・考古学・地質学・遺伝学など複数の分野にまたがる学際的な性格を持つ。古人類学。", "名詞", "Paleoanthropology relies heavily on fossil discoveries, but modern research increasingly incorporates ancient DNA analysis as well.", "動物(旧人類)", "820"),
    ("mitochondrial Eve", "現在生きているすべての人類が、母から娘、そのまた娘へと途切れることなく母系をたどっていくと行き着く、最も新しい共通の女性祖先を指す学術的な概念。実際の推定年代には幅があるが、およそ10万~23万年前(近年の研究では約15万年前とする推定もある)にアフリカに生きていたとされる。当時「唯一生きていた女性」だったという意味ではなく、同時代には他にも多くの女性が存在していたが、その子孫の母系の系譜がどこかで途切れてしまった結果として、この一人の女性だけが現代人全員の共通の母系祖先として残った、という点に注意が必要である。ミトコンドリア・イブ。", "名詞", "Mitochondrial Eve was not the only woman alive at the time; she was simply the one whose unbroken maternal line survives in every person living today.", "動物(旧人類)", "870"),
    ("archaic human", "現生人類(解剖学的現代人)とは異なる身体的特徴を持つ、旧人・原人段階の人類を総称する語。ネアンデルタール人やデニソワ人、ホモ・エレクトスなど、現生人類の系統から分かれた後に絶滅した人類種・集団を指すことが多い。文脈によっては、現生人類の中でも原始的な特徴を残した初期の集団(いわゆる「古代型ホモ・サピエンス」)を指して使われることもあり、範囲がやや曖昧な語である点に注意したい。古代型人類、旧人類。", "名詞", "Neanderthals and Denisovans are the two archaic humans we know the most about, thanks to ancient DNA research.", "動物(旧人類)", "750"),
    ("anatomically modern human", "骨格などの身体的特徴が、現在生きている人類とほぼ同じ水準に達した段階の現生人類(ホモ・サピエンス)を指す学術用語。約30万年前以降のアフリカの化石に見られる特徴で定義され、道具や芸術など文化的な意味での「現代的な行動」を獲得していたかどうかを問う「行動的現代性」とは区別して論じられる。解剖学的現代人。", "名詞", "The earliest anatomically modern humans appeared in Africa long before they developed the complex symbolic behavior associated with later prehistoric cultures.", "動物(旧人類)", "800"),
    ("control of fire", "人類が自然に発生した火を維持・利用したり、自ら火をおこしたりする能力を指す語。火の日常的な利用の痕跡は少なくとも約40万~30万年前以降の遺跡でより広く確実に確認されるようになるが、それ以前の火の利用については証拠の解釈をめぐって議論が続いている。マッチなどを使わずに自力で火を起こす「発火」の技術についても、少なくとも約40万年前まで遡る証拠がイギリスの遺跡から報告されている。火の利用、火の管理。", "名詞", "The control of fire allowed early humans to cook food, stay warm, and ward off predators.", "動物(旧人類)", "720"),
    ("toolmaking", "特定の目的のために材料を加工し、道具を意図的に作り出す行為。単に木の枝や石をそのまま使う「道具の使用」とは区別され、一定の形に成形する技術や、その技術を仲間内で共有・伝承する行動を伴う点が特徴とされる。チンパンジーなど一部の霊長類も簡単な道具を使用するが、石器のように規格化された形状を持つ道具を継続的に作り出す能力は、人類の系統で特に発達したと考えられている。道具製作。", "名詞", "Toolmaking, as opposed to simple tool use, requires shaping raw materials into a consistent, intentional form.", "動物(旧人類)", "700"),
    ("Rift Valley", "アフリカ大陸東部を南北に縦断する巨大な地溝帯(グレート・リフト・バレー)。オルドヴァイ渓谷(タンザニア)やハダール(エチオピア)、トゥルカナ湖畔(ケニア)など、著名な人類化石の発見地の多くがこの地域に集中しており、古人類学において特に重要な地域とされる。地殻変動にともなう火山活動で堆積した火山灰の層が、化石の精密な年代測定を可能にしていることも、この地域で発見が相次ぐ一因とされる。大地溝帯、リフトバレー。", "名詞", "Many of the most important hominin fossils have been unearthed along Africa's Rift Valley.", "動物(旧人類)", "780"),
    ("sagittal crest", "頭骨の正中線に沿って前後に走る、骨の隆起部分。強力な咀嚼筋(側頭筋)を頭骨に固定するための土台となる構造で、パラントロプス属やゴリラの雄など、硬い植物質を大量に咀嚼する必要のある種で発達している。ホモ属ではほとんど見られない特徴である。矢状稜(しじょうりょう)。", "名詞", "The prominent sagittal crest on a Paranthropus skull anchored powerful jaw muscles used for heavy chewing.", "動物(旧人類)", "820"),
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
