# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add vocabulary for now-vanished occupations of the early modern era
(2026-08-06・ユーザー要望: 「近代(産業革命期〜20世紀前半)の欧米・日本に
存在した、現代ではほぼ見られなくなった職業」の英単語を domain='職業' で
約30〜35語追加).

点灯夫(lamplighter)・煙突掃除人(chimney sweep)・触れ役(town crier)・
廃品回収人(rag-and-bone man)・電信技士(telegraph operator)・
エレベーター係(elevator operator)・タイピスト(typist)・
速記者(stenographer)・氷配達人(iceman)・牛乳配達人(milkman)・
鉄道信号手(railway signalman)・電話交換手(telephone operator)・
職業目覚まし係(knocker-upper)・無声映画の伴奏ピアニスト
(silent film pianist)・人力車夫(rickshaw puller)・
汲み取り業者(night soil collector)・ボウリングのピン立て係
(pinsetter)・葉巻工場の朗読係(lector)・石炭選別少年工(breaker boy)・
手回しオルガン弾き(organ grinder)・マッチ工場の女子工員(matchgirl)・
靴磨き少年(bootblack)・代書人(scrivener)・写字生(copyist)・
ライノタイプ植字工(linotype operator)・辻馬車の御者
(hansom cab driver)・灯台守(lighthouse keeper)・天然氷切り出し職人
(ice cutter)・路面電車の車掌(streetcar conductor)・電報配達少年
(telegram messenger boy)・計算手(human computer)・サンドイッチマン
(sandwich board man)・ネズミ捕り業者(rat catcher)・ヒル採取人
(leech collector)・銀板写真師(daguerreotypist)など、19世紀〜20世紀
前半のイギリス・アメリカ・日本を中心に実在した職業を集めた。

各語の example は、その職業がいつ・どこで(あるいはどのような技術的
背景の下で)成立していたかが伝わるよう、時代・地域を示す語
(Victorian England, Meiji-era Tokyo, industrial Manchester,
before electric refrigerators became common など)を含めた文にした。

domain は '職業' に統一。level は ["300-","300","350","400","450",
"500","550","600","650","700","750","800","850","900","950","990",
"990+"] のスケールに沿って 600〜850 の範囲で付与しており、milkman や
typist のように比較的なじみのある語は 600〜650、knocker-upper や
lector・leech collector・daguerreotypist のように語彙自体が難しく
背景知識も要する語は 800〜850 とした。

事前に既存DB(words ~7000件)を全件チェックし、switchboard operator・
miner・conductor・printer・blacksmith・cobbler・tanner・cooper・
wheelwright・computer は既に存在することを確認したため、それらと
概念が重複する語(switchboard operator そのもの、coal miner ≒ miner
など)はこのリストから除外している。computer と概念が重なる
human computer は、意味も綴りも別物(職業としての「計算手」)であり
既存の computer(家電)とは domain も語義も異なるため採用した。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_occupations_early_modern.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("lamplighter", "点灯夫(街灯のガス灯やランプを手作業で灯した人)", "名詞", "Every evening, the lamplighter walked down the London street lighting each gas lamp by hand.", "職業", "700"),
    ("chimney sweep", "煙突掃除人", "名詞", "In Victorian England, young boys often worked as chimney sweeps, climbing inside narrow flues.", "職業", "650"),
    ("town crier", "触れ役(鐘や太鼓を鳴らして布告を読み上げた人)", "名詞", "The town crier rang his bell in the square and announced the king's latest proclamation.", "職業", "750"),
    ("rag-and-bone man", "廃品回収人(古着や古金属を回収して回った)", "名詞", "The rag-and-bone man pushed his cart through the alleys of industrial Manchester, collecting scrap.", "職業", "800"),
    ("telegraph operator", "電信技士(モールス信号で通信を送受信した)", "名詞", "The telegraph operator tapped out the message in Morse code from the railway station office.", "職業", "700"),
    ("elevator operator", "エレベーター係(手動でレバーを操作して昇降機を動かした)", "名詞", "The elevator operator in the department store called out each floor as the doors opened.", "職業", "650"),
    ("typist", "タイピスト(タイプライターで文書を清書する専門職)", "名詞", "By the 1920s, thousands of young women worked as typists in the growing office buildings of American cities.", "職業", "600"),
    ("stenographer", "速記者(会議や裁判の発言を速記符号で記録した)", "名詞", "A stenographer sat beside the judge, recording every word of the courtroom testimony in shorthand.", "職業", "700"),
    ("iceman", "氷配達人(電気冷蔵庫が普及する前、氷塊を各家庭に配達した)", "名詞", "Before electric refrigerators became common, the iceman delivered blocks of ice to homes twice a week.", "職業", "650"),
    ("milkman", "牛乳配達人(瓶入り牛乳を各戸の玄関先に届けた)", "名詞", "The milkman left fresh glass bottles on doorsteps early each morning before most families woke up.", "職業", "600"),
    ("railway signalman", "鉄道信号手(信号所でレバーを操作し列車の進行を管理した)", "名詞", "The railway signalman pulled the heavy levers in his cabin to switch the tracks for the approaching train.", "職業", "800"),
    ("telephone operator", "電話交換手(交換台で通話をつないだ)", "名詞", "The telephone operator plugged the caller's line into the switchboard to connect the call.", "職業", "650"),
    ("knocker-upper", "職業目覚まし係(目覚まし時計の普及前、長い棒で窓を叩いて労働者を起こした)", "名詞", "In industrial England, a knocker-upper walked the streets before dawn, tapping on bedroom windows with a long pole to wake factory workers.", "職業", "850"),
    ("silent film pianist", "無声映画の伴奏ピアニスト", "名詞", "A silent film pianist improvised music in the theater pit as the images flickered silently on the screen.", "職業", "800"),
    ("rickshaw puller", "人力車夫(近代日本で客を乗せた二輪車を引いて走った)", "名詞", "In Meiji-era Tokyo, a rickshaw puller could carry passengers across the city faster than walking.", "職業", "700"),
    ("night soil collector", "汲み取り業者(下水道が普及する前、各家庭のし尿を回収した)", "名詞", "Before modern sewers were built, a night soil collector visited houses before dawn to empty the waste buckets.", "職業", "800"),
    ("pinsetter", "ボウリングのピン立て係(自動化以前、手作業でピンを並べた)", "名詞", "Before automatic machines existed, a young pinsetter reset the bowling pins by hand after every throw.", "職業", "750"),
    ("lector", "葉巻工場の朗読係(作業中の労働者に新聞や小説を読み聞かせた)", "名詞", "A lector sat on a raised platform in the cigar factory, reading newspapers and novels aloud to the workers rolling tobacco.", "職業", "850"),
    ("breaker boy", "石炭選別少年工(米国の炭鉱で石炭から不純物を手作業で取り除いた)", "名詞", "In Pennsylvania coal country, a breaker boy spent long hours picking slate out of coal with his bare hands.", "職業", "800"),
    ("organ grinder", "手回しオルガン弾き(街頭でハンドル式の楽器を回して演奏した)", "名詞", "The organ grinder cranked his handle on the street corner while his trained monkey collected coins from passersby.", "職業", "750"),
    ("matchgirl", "マッチ工場の女子工員(有害な黄リンを扱う過酷な労働で知られた)", "名詞", "The matchgirls at the London factory worked long shifts dipping matchsticks into dangerous white phosphorus.", "職業", "800"),
    ("bootblack", "靴磨き少年", "名詞", "A young bootblack set up his stand on the street corner, shining the shoes of businessmen for a few coins.", "職業", "700"),
    ("scrivener", "代書人(読み書きのできない人の代わりに書類を作成した)", "名詞", "For a small fee, the scrivener wrote letters and legal documents for customers who could not write themselves.", "職業", "800"),
    ("copyist", "写字生(印刷や複写機が普及する前、文書を手で書き写した)", "名詞", "Before typewriters were common, a copyist spent all day duplicating letters and contracts by hand.", "職業", "750"),
    ("linotype operator", "ライノタイプ植字工(活字を一行ずつ鋳造する機械を操作した)", "名詞", "The linotype operator sat at the keyboard, casting each line of type in molten metal for the morning newspaper.", "職業", "850"),
    ("hansom cab driver", "辻馬車の御者(二輪馬車のタクシーを操った)", "名詞", "A hansom cab driver waited outside the theater, ready to carry passengers through the foggy London streets.", "職業", "750"),
    ("lighthouse keeper", "灯台守(自動化以前、灯台に住み込みで灯りを管理した)", "名詞", "Before lighthouses were automated, a keeper lived on the remote island and tended the lamp every night.", "職業", "650"),
    ("ice cutter", "天然氷切り出し職人(冬に凍った湖から氷塊を切り出した)", "名詞", "Every winter, ice cutters sawed huge blocks from the frozen lake and stored them for summer delivery.", "職業", "800"),
    ("streetcar conductor", "路面電車の車掌(乗車券の販売や発車の合図を行った)", "名詞", "The streetcar conductor rang the bell twice to signal the driver it was safe to move on.", "職業", "700"),
    ("telegram messenger boy", "電報配達少年(自転車で電報を各家庭へ届けた)", "名詞", "A telegram messenger boy pedaled his bicycle through the neighborhood, delivering urgent telegrams door to door.", "職業", "700"),
    ("human computer", "計算手(電子計算機の登場前、手作業で科学計算を行った職業。多くは女性)", "名詞", "Long before electronic machines existed, a team of human computers calculated rocket trajectories by hand.", "職業", "800"),
    ("sandwich board man", "サンドイッチマン(体の前後に広告板を下げて街を歩いた)", "名詞", "A sandwich board man walked up and down the busy street, advertising the new department store sale.", "職業", "800"),
    ("rat catcher", "ネズミ捕り業者(害獣駆除を職業として行った)", "名詞", "The city rat catcher was paid for every rat he caught in the crowded tenement buildings.", "職業", "750"),
    ("leech collector", "ヒル採取人(医療用のヒルを湿地で採取して薬剤師に売った)", "名詞", "A leech collector waded barefoot through the marsh, letting leeches attach to her legs before selling them to apothecaries.", "職業", "850"),
    ("daguerreotypist", "銀板写真師(初期の写真技法ダゲレオタイプを扱った写真師)", "名詞", "A traveling daguerreotypist set up his camera in the town square, offering portraits on polished silver plates.", "職業", "850"),
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
    return 0


if __name__ == "__main__":
    sys.exit(main())
