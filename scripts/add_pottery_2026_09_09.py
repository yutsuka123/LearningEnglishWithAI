# ruff: noqa: E501
"""陶芸新ドメイン(2026-09-09・authored by Claude)。ユーザー提起「陶芸は強化してもらえると、窯元の用語、趣味の陶芸の用語、用具の用語、釉薬土に関する用語、ドイツ、日本、他各地独特の陶芸に関する用語」。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_pottery_2026_09_09.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("wedging", "成形前の粘土から気泡を抜き、水分や硬さを均一にするために、手や機械で押し練りする準備作業。菊練りなど。", "名詞", "Before throwing a pot, she spent ten minutes wedging the clay to remove trapped air bubbles.", "陶芸", "550"),
    ("throwing", "ろくろを回転させながら、その遠心力を利用して粘土の塊から器の形を引き上げて成形する技法。", "名詞", "It took him months of practice before he could throw a perfectly centered bowl on the wheel.", "陶芸", "550"),
    ("trimming", "ろくろ挽きした器が生乾き(レザーハード)の状態になった後、逆さにして底や高台の余分な粘土を刃物で削り取り、形を整える工程。", "名詞", "After the bowl became leather-hard, she flipped it over on the wheel for trimming.", "陶芸", "550"),
    ("slip", "水を多く加えて泥状にした粘土。パーツ同士を接着したり、器の表面に化粧掛けしたり、鋳込み成形に用いたりする。", "名詞", "She joined the handle to the mug by scoring both surfaces and applying slip.", "陶芸", "550"),
    ("slip casting", "泥漿状にした粘土(スリップ)を石膏型に流し込み、型が水分を吸うことで型の内壁に沿って粘土が固まる性質を利用して器を成形する技法。複雑な形や同じ形を大量に作るのに向く。", "名詞", "Slip casting allows potters to reproduce the same intricate shape hundreds of times.", "陶芸", "650"),
    ("mold (ceramics)", "陶芸において、粘土やスリップを流し込んだり押し付けたりして特定の形を写し取るための型。多くは石膏製。", "名詞", "The plaster mold was made in two halves so the finished piece could be removed easily.", "陶芸", "600"),
    ("banding wheel", "ろくろのように回転するが、モーターは付いておらず手で回す小型の台。装飾を描いたり、成形途中の器を全方向から確認・仕上げたりするのに使う。", "名詞", "She placed the bowl on a banding wheel and slowly rotated it while painting a band of color around the rim.", "陶芸", "500"),
    ("rib (pottery)", "木・金属・ゴムなどでできた、湾曲した縁を持つ板状の道具。ろくろ成形中に器の表面をなめらかにしたり、余分な粘土をかき取ったりするのに使う。", "名詞", "He used a wooden rib to smooth the outside of the vase as it spun on the wheel.", "陶芸", "550"),
    ("cutting wire", "両端に持ち手が付いた細いワイヤー。ろくろから成形し終えた器を台から切り離したり、粘土の塊を切り分けたりするのに使う。", "名詞", "She pulled the cutting wire under the pot to separate it from the wheel head.", "陶芸", "500"),
    ("bisqueware", "釉薬をかける前に、一度低めの温度で焼成した(素焼きした)状態の陶磁器。多孔質でもろく、水を吸いやすいため、この状態で釉薬をかけやすい。", "名詞", "The bisqueware felt chalky and absorbent, perfect for soaking up the glaze.", "陶芸", "600"),
    ("kiln shelf", "窯の中に水平に設置し、焼成する器を並べて置くための平らな板。棚板。", "名詞", "He arranged a dozen mugs on the kiln shelf before closing the door for the firing.", "陶芸", "550"),
    ("saggar", "焼成中の器を炎や灰、煙などから直接触れないように守るために入れる、耐火性の箱や容器。逆に意図的に灰や塩などを詰めて特殊な発色効果を出すためにも使われる。", "名詞", "The delicate porcelain pieces were protected inside a saggar during the wood firing.", "陶芸", "700"),
    ("pyrometric cone", "特定の温度で先端が軟化して曲がるように作られた、細長い三角柱状の小さな道具。窯の中に立てて置き、実際にどれだけ熱が器に伝わったか(温度と時間の積算)を視覚的に確認するために使う。", "名詞", "When cone 6 bent completely over, she knew the glaze firing had reached the right temperature.", "陶芸", "700"),
    ("reduction firing", "窯の中の酸素量を意図的に不足させた状態で焼成する方法。不完全燃焼によって生じる一酸化炭素が釉薬や素地の金属酸化物から酸素を奪い、酸化焼成とは異なる色や質感を生み出す。", "名詞", "Reduction firing can turn a copper red glaze from green to a deep ox-blood red.", "陶芸", "700"),
    ("oxidation firing", "窯の中に十分な酸素を供給しながら焼成する、最も一般的な焼成方法。電気窯の多くはこの方式で焼かれる。", "名詞", "Electric kilns almost always fire in oxidation because they don't burn fuel that consumes oxygen.", "陶芸", "700"),
    ("kick wheel", "電動モーターを使わず、足で下部の重い円盤(はずみ車)を蹴って回転させる、伝統的な足踏み式のろくろ。", "名詞", "Before electricity, potters relied entirely on the kick wheel to spin their clay.", "陶芸", "600"),
    ("kiln wash", "アルミナや粘土などを水で溶いた液体で、棚板の表面に塗って乾かしておく保護剤。器から釉薬が垂れて棚板にくっつくのを防ぐ。", "名詞", "Always apply kiln wash to a new shelf before using it, or dripped glaze will fuse it to your pots.", "陶芸", "600"),
    ("pug mill", "粘土を練り、気泡を抜きながら円柱状に押し出す機械。手作業の菊練りより効率的に大量の粘土を均質な状態にできる。", "名詞", "The studio's pug mill can process a large bag of clay into an air-free cylinder in minutes.", "陶芸", "650"),
    ("clay body", "粘土に他の鉱物(長石・シリカ・グロッグなど)を配合して作られた、作陶に使う粘土の調合そのもの。使用目的や焼成温度に応じて様々な配合がある。", "名詞", "This stoneware clay body can withstand much higher firing temperatures than the earthenware body she used before.", "陶芸", "650"),
    ("kaolin", "カオリナイトを主成分とする白色の粘土鉱物。不純物(特に鉄分)が少なく、磁器の原料として欠かせない。中国磁器の原料採掘地に由来する名を持つ。", "名詞", "Kaolin gives porcelain its characteristic whiteness because it contains almost no iron impurities.", "陶芸", "700"),
    ("feldspar", "地殻に最も多く含まれる造岩鉱物の一group。陶磁器では釉薬や素地の融剤(フラックス)として使われ、焼成時にガラス化を促し器を硬く緻密にする。", "名詞", "Feldspar acts as a flux, melting at high temperatures and helping the clay body vitrify.", "陶芸", "700"),
    ("grog", "一度焼成した陶磁器を粉砕して粒状にしたもの。生の粘土に混ぜることで、乾燥・焼成時の収縮やひび割れを抑え、大型作品や彫刻に強度と質感を与える。", "名詞", "Adding grog to the clay body reduced cracking in her large sculptural pieces.", "陶芸", "650"),
    ("glaze (ceramics)", "陶磁器の表面に施す、焼成によってガラス質になる薬品(釉薬)。器を水漏れしないように密閉し、光沢や色、質感を与える。", "名詞", "She dipped the bisqueware into a bucket of clear glaze before the final firing.", "陶芸", "600"),
    ("engobe", "化粧掛けに使う、粘土を主成分とした泥状の被膜材。釉薬ほどガラス質にはならないが、器の色や質感を変えたり下地を整えたりするために生や素焼きの器の表面に塗る。", "名詞", "She brushed a layer of white engobe over the dark clay body before carving a design into it.", "陶芸", "700"),
    ("ash glaze", "木や植物を燃やした灰を主原料とする釉薬。灰に含まれるシリカや融剤成分を利用し、東アジアの高火度焼成の陶磁器で古くから使われてきた。", "名詞", "Wood ash glazes often produce unpredictable, richly textured surfaces that vary from pot to pot.", "陶芸", "700"),
    ("salt glaze", "焼成の最高温度に達した窯の中に食塩を投入し、蒸発した塩分が素地表面のシリカと反応してできる、薄いガラス質の釉薬。表面はしばしばオレンジピール状の凹凸を持つ。", "名詞", "German potters have used salt glaze on stoneware jugs and crocks since the medieval period.", "陶芸", "750"),
    ("extruder", "型(ダイ)を通して粘土を一定の断面形状に押し出す道具。取っ手や装飾用のパーツ、筒状の部品などを効率よく大量に作るのに使う。", "名詞", "She used a clay extruder to make dozens of identical mug handles.", "陶芸", "600"),
    ("porcelain", "カオリンを主原料とし、高温(1300度前後)で焼成することで得られる、白く緻密で半透光性を持つ高級な陶磁器。磁器。", "名詞", "Porcelain is fired at a much higher temperature than earthenware, giving it a hard, translucent quality.", "陶芸", "600"),
    ("terracotta", "鉄分を多く含む赤茶色の粘土を、比較的低温で釉薬をかけずに焼いた素焼きの陶器。植木鉢や屋根瓦、彫刻など古くから広く使われてきた。", "名詞", "Rows of terracotta pots lined the sunny windowsill, each planted with fresh herbs.", "陶芸", "600"),
    ("bone china", "牛骨などを焼いて作る骨灰(ボーンアッシュ)を配合した磁器の一種。18世紀末のイギリスで確立され、通常の磁器より白く、薄くても割れにくい丈夫さを持つ。", "名詞", "Bone china teacups are prized for being thin, light, and surprisingly chip-resistant.", "陶芸", "750"),
    ("majolica", "白く不透明な錫釉(すずゆう)をかけた上に絵付けを施す、イタリア発祥の陶器の様式。ルネサンス期に精緻な物語画を描いた作品などで発展した。", "名詞", "Renaissance majolica plates were often painted with elaborate scenes from mythology or history.", "陶芸", "800"),
    ("faience", "白く不透明な錫釉をかけた陶器で、特にフランスをはじめとするヨーロッパ大陸で発展した様式。イタリアのファエンツァという都市の名に由来する。", "名詞", "French faience workshops produced brightly painted tin-glazed pottery for centuries.", "陶芸", "800"),
    ("crackle glaze", "釉薬と素地の収縮率の差を利用して、意図的に表面に細かいひび割れの網目模様を生じさせた釉薬、またはその技法。", "名詞", "The crackle glaze gave the vase a network of fine, spiderweb-like lines across its surface.", "陶芸", "700"),
    ("matte glaze", "光沢がなく、つや消しのマットな質感に仕上がる釉薬。表面が半透明のガラス状にならず、しっとりとした触感を持つことが多い。", "名詞", "She prefers a matte glaze for tableware because it feels soft and doesn't reflect glare.", "陶芸", "650"),
    ("glossy glaze", "表面が滑らかにガラス化し、強い光沢を持つ釉薬。透明釉や多くのカラー釉に見られる、最も一般的な釉薬の質感。", "名詞", "The glossy glaze made the bowl's surface shine like glass under the studio lights.", "陶芸", "600"),
    ("overglaze", "本焼きで釉薬をかけて焼いた器の上に、さらに絵付け(顔料)を施し、より低い温度で再度焼き付ける装飾技法、またはそのための絵の具。", "名詞", "The delicate gold rim was added as an overglaze decoration after the main glaze firing.", "陶芸", "750"),
    ("sgraffito", "化粧土(エンゴーブ)や釉薬を器の表面に施した後、それを部分的に削り取って下の素地の色を見せることで模様を描く装飾技法。", "名詞", "She coated the dark clay with white slip, then used sgraffito to scratch a floral pattern that revealed the dark clay beneath.", "陶芸", "750"),
    ("raku", "16世紀の京都で、茶の湯のために生まれた日本発祥の陶器。ろくろを使わず手で成形し、比較的低温で急速に焼成・急冷することで作られる。欧米では窯から取り出した器を可燃物の中に入れて燻す独自の「ラクー焼成」技法としても発展した。", "名詞", "The tea master favored raku bowls for their simple, unpolished beauty.", "陶芸", "750"),
    ("terra sigillata", "非常に細かい粒子だけを沈殿させて作る、極めて滑らかな泥漿(でいしょう)。釉薬をかけずに、磨き(バニシング)によってつやを出す仕上げに使われる。", "名詞", "Ancient Roman terra sigillata tableware was famous for its glossy red surface and stamped maker's marks.", "陶芸", "800"),
    ("Meissen porcelain", "1710年にドイツ・ザクセン地方のマイセンで創設された名窯、およびそこで作られる磁器。ヨーロッパで初めて中国式の硬質磁器の製法を確立したことで知られる。", "名詞", "Meissen porcelain is often marked with a distinctive crossed-swords emblem on the base.", "陶芸", "850"),
    ("Bizen ware", "岡山県備前市周辺で作られる、日本を代表する古窯の一つ。釉薬を一切使わず、鉄分の多い赤みを帯びた土を高温で長時間焼き締めることで生まれる、灰の付着や炎の当たり方による自然な模様が特徴。", "名詞", "Bizen ware pieces get their earthy reddish-brown color entirely from the clay and the flames, without any glaze.", "陶芸", "800"),
    ("Hagi ware", "山口県萩市周辺で作られる陶器。柔らかく多孔質な土と淡い釉薬を使い、使い込むうちに釉薬の細かいひび(貫入)から茶などが染み込んで色合いが徐々に変化していくことで知られる。", "名詞", "Tea masters prize Hagi ware for the way its color slowly changes with years of daily use.", "陶芸", "800"),
    ("Arita ware", "佐賀県有田町周辺で作られる、日本で最初に生産された磁器。17世紀初頭、朝鮮人陶工によって近郊の泉山でカオリン(磁石)が発見されたことをきっかけに始まった。", "名詞", "Arita ware was Japan's first porcelain, and its export pieces greatly influenced European ceramics like Meissen.", "陶芸", "800"),
    ("Mino ware", "岐阜県東濃地方(多治見・土岐・瑞浪など)で作られる陶磁器の総称。桃山時代に志野・織部・黄瀬戸・瀬戸黒など多彩な様式を生み出したことで知られ、現在も日本の食器生産の大部分を占める一大産地。", "名詞", "Mino ware includes several distinct styles, from the milky white Shino glaze to the bold green Oribe glaze.", "陶芸", "800"),
    ("Shigaraki ware", "滋賀県甲賀市信楽町周辺で作られる、日本の六古窯の一つ。粗く長石の粒を多く含む土を釉薬なしで高温焼成し、自然な灰かぶりや焦げによる素朴な風合いを持つ。現在はたぬきの置物の産地としても広く知られる。", "名詞", "Shigaraki ware is known for its rough, gritty clay flecked with visible bits of feldspar.", "陶芸", "800"),
    ("Delftware", "オランダのデルフトを中心に17世紀に発展した、白い錫釉に青い絵付けを施した陶器。中国から輸入されていた染付磁器を模倣・代替する形で生まれた。", "名詞", "Delftware plates decorated with windmills and ships became iconic souvenirs of the Netherlands.", "陶芸", "800"),
    ("blue-and-white porcelain", "白い磁器の素地にコバルト顔料で下絵を描き、透明釉をかけて焼いた磁器。中国で完成され、以後世界各地の陶磁器に大きな影響を与えた様式。", "名詞", "Blue-and-white porcelain from Jingdezhen was exported across Asia, the Middle East, and eventually Europe.", "陶芸", "800"),
    ("jasperware", "18世紀後半にイギリスの陶工ジョサイア・ウェッジウッドが開発した、つや消しで無釉のせっ器。特に淡い青色の地に白い浮き彫りの装飾を施した様式で知られる。", "名詞", "Wedgwood's pale blue jasperware, decorated with white neoclassical figures, became instantly recognizable.", "陶芸", "800"),
    ("pottery studio", "ろくろや窯などの設備を備えた、陶芸を制作するための作業場・工房。個人の趣味の作陶から、教室やレンタル工房まで様々な形態がある。", "名詞", "She rents wheel time at a local pottery studio every Saturday morning.", "陶芸", "500"),
    ("pottery class", "陶芸の基本技術(ろくろ成形や手びねりなど)を教わる講座・教室。趣味として陶芸を始める人の入り口としてよく利用される。", "名詞", "He signed up for a beginner pottery class to learn how to center clay on the wheel.", "陶芸", "450"),
    ("greenware", "成形したばかりで、まだ一度も焼成していない、乾燥させただけの状態の粘土製品。非常にもろく、水にも弱い。", "名詞", "Greenware is so fragile that even a light bump can snap off a handle before it's fired.", "陶芸", "550"),
    ("leather-hard", "粘土が完全には乾いていないが、指で押しても跡がつきにくいほど硬くなった、革のような硬さの乾燥段階。取っ手付けや削り(トリミング)、化粧掛けなどに適した状態とされる。", "形容詞", "The mug handles are attached while both the cup and the handle are still leather-hard.", "陶芸", "550"),
    ("air-dry clay", "窯を使わず、常温で乾燥させるだけで固まる粘土。焼成の必要がないため、家庭や学校など窯を持たない環境での工作・趣味に広く使われる。", "名詞", "Air-dry clay is popular with beginners because it doesn't require access to a kiln.", "陶芸", "500"),
    ("pit firing", "地面に掘った穴の中に器を並べ、薪やおがくずなどの可燃物と一緒に燃やして焼成する、最も原始的な野焼きの一種。", "名詞", "The pit firing produced beautiful smoky black-and-orange patterns on the pot's surface.", "陶芸", "700"),
    ("glazing", "素焼きした器の表面に釉薬をかける作業、またはその過程。刷毛塗り・浸し掛け・吹き付けなど様々な方法がある。", "名詞", "Glazing is often considered the trickiest step, since the color can look completely different before and after firing.", "陶芸", "550"),
    ("hand-building", "ろくろを使わず、手びねり・紐作り・タタラ作りなど手作業だけで器を成形する技法の総称。", "名詞", "Hand-building lets you create irregular, sculptural shapes that would be difficult to throw on a wheel.", "陶芸", "550"),
    ("slab building", "粘土を均一な厚さの板状(タタラ)に伸ばし、それを切ったり組み合わせたりして器や箱型の作品を作る手びねりの技法。", "名詞", "She rolled the clay into flat slabs and joined the edges to build a rectangular box.", "陶芸", "600"),
    ("coiling", "粘土を細長い紐状に伸ばし、それを積み重ねながら指でなじませて器の壁を作っていく、古くから世界各地で使われてきた手びねりの技法。", "名詞", "She built the large pot by coiling rope-like strands of clay one on top of another.", "陶芸", "550"),
    ("burnishing", "生や素焼き前の粘土の表面を、なめらかな石やへらなどでこすって磨き、艶を出す仕上げ技法。釉薬を使わずに光沢を出す方法として、古代から世界各地で用いられてきた。", "名詞", "She burnished the leather-hard bowl with a smooth pebble until its surface gleamed.", "陶芸", "700"),
    ("test tile", "新しい釉薬や粘土の配合、焼成条件などを本番の作品に使う前に試すための、小さな試験用のタイル状の見本。", "名詞", "Before glazing the whole set of mugs, she fired a few test tiles to check the exact color.", "陶芸", "550"),
    ("damp box", "湿らせた布やビニールで密閉し、制作途中の作品を乾燥させすぎないように保湿しておくための箱や容器。数日〜数週間かけて作品を仕上げる際に使う。", "名詞", "She kept the unfinished teapot in a damp box overnight so she could attach the spout the next day.", "陶芸", "550"),
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
