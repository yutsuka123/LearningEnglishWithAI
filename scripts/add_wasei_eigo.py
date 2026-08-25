# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""新規ドメイン「和製英語」+ 既存フレーズシーン「和製英語・誤用注意」の拡張、
authored by Claude(2026-08-26・B23バックログ「和製英語 vs 本物の英語」対応)。

デザイン: 見出し語(english)は常に「正しい英語表現」。japanese側で対応する
和製英語の誤りとその理由を明記する(既存の和製英語フレーズ25件と同じ設計)。
英語スペルがDB全体で既存語と衝突するものは意図的に除外(ホモグラフ化は
別プロジェクト(B17)の範囲のため今回は行わない)。

No app / OpenAI API calls — hand-written(並列サブエージェントでドラフト後に
人手でdedup), inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` /
`phrases` tables.

Run:  python scripts/add_wasei_eigo.py
仕上げ: 投入後に `python scripts/relevel.py` と
        `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WASEI = "和製英語"
WASEI_SCENE = "和製英語・誤用注意"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    ("flash drive", "USBメモリ(データを持ち運ぶ小型記憶装置)。和製英語で『USBメモリ』と言うが、英語のmemoryは主にRAM(作業用記憶)を指し、この意味では通じにくい。正しくはflash driveやUSB drive、thumb driveと言う。", "名詞", "Save the file to a flash drive before you leave the office.", WASEI, "500"),
    ("mechanical pencil", "シャープペンシル(芯を繰り出して使う筆記具)。和製英語で『シャープペンシル(sharp pencil)』と言うが、英語にsharp pencilという表現はない。正しくはmechanical pencilと言う。", "名詞", "He always writes with a mechanical pencil instead of a regular pencil.", WASEI, "400"),
    ("stapler", "ホッチキス(紙を綴じる文房具)。和製英語で『ホッチキス』と言うが、これは製造会社名(Hotchkiss)に由来する日本独自の呼び方で、英語では通じない。正しくはstaplerと言う。", "名詞", "Could you pass me the stapler? I need to bind these papers together.", WASEI, "400"),
    ("office worker", "会社員。日本語の『サラリーマン(salaryman)』は英語辞書に載るほど有名になったが、通常は男性の会社員を連想させ性別中立ではない。一般的な会社員を指すときはoffice workerやcompany employeeと言う方が自然。", "名詞", "Most office workers in the city commute by train every morning.", WASEI, "500"),
    ("business card", "名刺。和製英語で『ネームカード(name card)』と言う人がいるが、英語のname cardは名札(席や荷物につける名前カード)を指すことが多い。仕事用の名刺は正しくはbusiness cardと言う。", "名詞", "Let me give you my business card in case you need to contact me.", WASEI, "400"),
    ("unpaid overtime", "サービス残業(賃金が支払われない残業)。和製英語で直訳的に『サービス残業』を『service overtime』のように言ってしまうことがあるが、英語のserviceに『無給の』という意味はなく通じない。正しくはunpaid overtimeと言う。", "名詞句", "The company was criticized for forcing employees to work unpaid overtime.", WASEI, "650"),
    ("get promoted", "昇進する、キャリアを伸ばすこと。和製英語で『キャリアアップする』と言うが、英語にcareer upという表現は存在しない。正しくはget promotedやadvance one's careerと言う。", "動詞句", "She worked hard for years and finally got promoted to sales manager.", WASEI, "600"),
    ("be laid off", "会社の都合で解雇されること。和製英語で『リストラされる』と言うが、英語のrestructuringは本来『組織再編』全般を指し、必ずしも解雇を意味しない。人が解雇される場合はbe laid offと言う。", "動詞句", "Hundreds of workers were laid off when the factory shut down.", WASEI, "650"),
    ("website", "ウェブサイト全体。和製英語でサイト全体を指して『ホームページ』と言うが、英語のhomepageはサイトの表紙にあたるトップページだけを指す。サイト全体を指すときはwebsiteと言う。", "名詞", "You can find our business hours on our website.", WASEI, "400"),
    ("power bank", "モバイルバッテリー(外出先で使う携帯用充電器)。和製英語で『モバイルバッテリー(mobile battery)』と言うが、英語ではmobile batteryとは言わない。正しくはpower bankやportable chargerと言う。", "名詞", "I always carry a power bank so my phone doesn't die during the day.", WASEI, "500"),
    ("remote work", "在宅勤務・遠隔勤務。日本語の『テレワーク(telework)』は英語としても間違いではないが、やや古めかしい/フォーマルな響きがあり、日常会話ではremote workやwork from homeの方が圧倒的によく使われる。", "名詞句", "Many companies switched to remote work during the pandemic.", WASEI, "600"),
    ("female office worker", "女性事務員(いわゆるOL)。和製英語『OL(office lady)』は日本でのみ通じる略語で、英語には存在しない。英語では単にfemale office workerやwoman who works in an officeのように表現する。", "名詞句", "Several female office workers in her department were recently promoted.", WASEI, "650"),
    ("product tester", "新商品の試用者(商品を試して感想を提供する人)。和製英語で『モニター』と言うが、英語のmonitorは画面や機器、または『監視する人』を意味し、この意味では通じにくい。正しくはproduct testerと言う。", "名詞", "The cosmetics company recruited product testers to try its new cream.", WASEI, "700"),
    ("staff member", "従業員一人。日本語では『スタッフ』を『1人のスタッフ』のように数えられる名詞として使うが、英語のstaffは集合名詞で、a staffのようには数えない。一人を指すときはa staff memberやan employeeと言う。", "名詞", "We need to hire two more staff members before the busy season.", WASEI, "600"),
    ("cash register", "レジ(会計をする機械・場所)。和製英語で『レジ(register)』と略して言うが、英語で単にregisterだけでは通じにくい。正しくはcash registerと言い、支払う場所を指す場合はcheckoutとも言う。", "名詞", "Please bring your items to the cash register when you're ready to pay.", WASEI, "450"),
    ("touch typing", "キーボードを見ずに入力すること。和製英語で『ブラインドタッチ(blind touch)』と言うが、英語には存在しない表現な上、差別的と受け取られる可能性もある。正しくはtouch typingと言う。", "名詞", "She practiced touch typing every day and can now type without looking at the keyboard.", WASEI, "600"),
    ("catchphrase", "広告などの印象的な決まり文句。和製英語で『キャッチコピー(catch copy)』と言うが、英語にcatch copyという表現はない。正しくはcatchphraseやtaglineと言う。", "名詞", "The company's new catchphrase quickly became popular on social media.", WASEI, "650"),
    ("wake-up call", "指定した時間に起こしてもらう電話サービス。和製英語で『モーニングコール(morning call)』と言うが、英語のmorning callは一般的でない。正しくはwake-up callと言う。", "名詞", "I asked the hotel to give me a wake-up call at six in the morning.", WASEI, "500"),
    ("after-sales service", "販売後の顧客サポート。和製英語で『アフターサービス(after service)』と言うが、英語では通常after-sales serviceやcustomer supportと言う。", "名詞句", "The company is known for its excellent after-sales service.", WASEI, "650"),
    ("username", "インターネット上で使う名前。和製英語で『ハンドルネーム(handle name)』と言うが、英語ではnameを重ねず、単にusernameまたはhandleと言う。", "名詞", "Please enter your username and password to log in.", WASEI, "400"),
    ("hoodie", "フード付きのゆったりしたトップス。和製英語で『パーカー(parka)』と呼ぶことが多いが、英語のparkaは毛皮の縁取りが付いた分厚い防寒コートを指すため、フード付きスウェットはhoodieと呼ぶのが普通。", "名詞", "He was wearing a gray hoodie and jeans.", WASEI, "300"),
    ("sweatshirt", "フードのない、厚手の裏起毛トップス。和製英語で『トレーナー(trainer)』と呼ぶが、英語のtrainerは(1)コーチ・指導者、(2)イギリス英語でスニーカーを指す言葉で、この服自体はsweatshirtと呼ぶ。", "名詞", "She changed into a comfortable sweatshirt after the gym.", WASEI, "500"),
    ("down jacket", "羽毛入りの防寒アウター。和製英語で単に『ダウン』と略すが、英語のdownは羽毛そのもの(素材)を指す言葉なので、服そのものを指すときはdown jacket(またはdown coat, puffer jacket)と言う必要がある。", "名詞", "I always wear a down jacket in winter because it's so warm.", WASEI, "400"),
    ("dress shirt", "ビジネス用の襟付きシャツ。和製英語の『ワイシャツ』は英語のwhite shirtが訛った言葉で、色や柄に関係なく使われるが、英語には通じない。ビジネス用シャツはdress shirt(またはbutton-down shirt)と呼ぶ。", "名詞", "He wore a white dress shirt and a tie to the interview.", WASEI, "500"),
    ("earrings", "耳につける装身具(特にピアス穴に通すタイプ)。和製英語で『ピアス』と言うが、英語のpierceは「(穴を)開ける」という動詞で、装身具そのものを指す名詞としては使わない。装身具はearrings(区別する場合はpierced earrings)と呼ぶ。", "名詞", "She was wearing small gold earrings.", WASEI, "400"),
    ("scarf", "防寒・おしゃれ用に首に巻く布。和製英語で『マフラー』と呼ぶが、英語のmufflerは主に自動車の排気音を消す「消音装置」を指す言葉。首に巻く布はscarfと呼ぶのが普通。", "名詞", "She wrapped a warm scarf around her neck before going outside.", WASEI, "400"),
    ("sweatpants", "運動着として着る、裾がすぼまったズボン。和製英語で『ジャージ』と呼ぶが、英語のjerseyは編み地の生地、またはサッカー選手などが着るユニフォームのトップスを指す言葉。このズボンはsweatpants(上下セットならtracksuit)と呼ぶ。", "名詞", "He put on sweatpants and went for a jog.", WASEI, "500"),
    ("sweater", "編み地のトップス。和製英語で『ニット』を単独で名詞として使うが、英語のknitは主に動詞・形容詞(knit fabricなど)で、編み物のトップスそのものはsweater(イギリス英語ではjumper)と呼ぶ。", "名詞", "She was wearing a cozy wool sweater.", WASEI, "400"),
    ("buffet", "料金を払えば好きなだけ食べられる形式の食事。和製英語で『バイキング』と呼ぶが、これは1958年に帝国ホテルが北欧のスモーガスボードをヒントに名付けた日本独自の呼び方で、英語では通じない。英語ではbuffet(またはall-you-can-eat)と呼ぶ。", "名詞", "The hotel offers a breakfast buffet every morning.", WASEI, "500"),
    ("soft serve ice cream", "とろけるような食感で機械から絞り出すアイスクリーム。和製英語で『ソフトクリーム』と呼ぶが、英語では通じない。英語ではsoft serve、またはsoft serve ice creamと呼ぶ。", "名詞", "We got soft serve ice cream at the beach.", WASEI, "400"),
    ("corn dog", "串に刺したソーセージにとうもろこし粉の衣をつけて揚げた食べ物。和製英語で『アメリカンドッグ』と呼ぶが、英語では通じない。英語ではcorn dogと呼ぶ。", "名詞", "We bought a corn dog at the festival.", WASEI, "400"),
    ("hamburger steak", "ひき肉を焼いた、バンズに挟まない状態の料理。和製英語で『ハンバーグ』と呼ぶが、英語で単にhamburgerと言うとバンズに挟んだサンドイッチを指すのが普通。パティ単体の料理を指すときはhamburger steak(またはSalisbury steak)と呼ぶ。", "名詞", "The restaurant's hamburger steak comes with mashed potatoes and gravy.", WASEI, "500"),
    ("french fries", "細切りにして揚げたじゃがいも。和製英語で単に『ポテト』と呼ぶことが多いが、英語ではFrench fries(アメリカ英語)、またはchips(イギリス英語)と呼ぶ。日本語の『ポテトチップス』は英語のpotato chips(米)/crisps(英)にあたり、イギリス英語のchips(=fries)とは別物なので注意。", "名詞", "Can I get a burger with french fries, please?", WASEI, "400"),
    ("soft drink", "甘い炭酸飲料など、アルコールを含まない飲み物全般。和製英語で『ジュース』は炭酸飲料も含め幅広く使うが、英語のjuiceは果物・野菜のしぼり汁のみを指す。炭酸飲料などを含めて言うときはsoft drink(またはsoda)と呼ぶ。", "名詞", "Would you like a soft drink or some water with your meal?", WASEI, "500"),
    ("mug", "取っ手の付いた背の高いカップ。和製英語で『マグカップ』と言うが、英語のmug自体に「カップ」の意味が含まれているため、cupを重ねる必要はない。英語では単にmugと呼ぶ。", "名詞", "He poured himself a mug of hot coffee.", WASEI, "300"),
    ("front desk", "ホテルの受付・案内カウンター。和製英語で『フロント』と略すが、英語のfrontは「正面」「前方」という意味の言葉で、単独では受付を指さない。ホテルの受付はfront desk(またはreception)と呼ぶ。", "名詞", "Please leave your key at the front desk when you check out.", WASEI, "400"),
    ("signature", "書類などに書く署名。和製英語で『サイン』と呼ぶが、英語のsignは動詞(署名する)であり、書いたもの(署名)そのものを指す名詞はsignature。「ここにサインしてください」はPlease sign here(またはPlease put your signature here)と言う。", "名詞", "Please put your signature at the bottom of the contract.", WASEI, "500"),
    ("plastic bag", "薄いポリ製の買い物袋。和製英語で『ビニール袋』と呼ぶが、英語のvinylはレコード盤や床材などに使われる硬めの塩化ビニール素材を指す言葉で、薄いレジ袋には使わない。英語ではplastic bagと呼ぶ。", "名詞", "Do you need a plastic bag for your groceries?", WASEI, "400"),
    ("stroller", "赤ちゃんを乗せて押す乳母車。和製英語で『ベビーカー』と呼ぶが、英語では通じない。アメリカ英語ではstroller、イギリス英語ではpushchairまたはpramと呼ぶ。", "名詞", "She pushed the stroller through the park.", WASEI, "400"),
    ("score a goal", "ゴールを決める、得点する。和製英語の『ゴールイン』はgoalを動詞のように使った誤用で、英語ではscore a goal(または単にscore)と表現する。", "動詞句", "She scored the winning goal in the final minute of the match.", WASEI, "400"),
    ("walk", "四球(フォアボール)。野球で四球を選んで出塁すること。和製英語の『フォアボール』(four ball)は英語では通じず、正しくはwalk(またはbase on balls)と言う。", "名詞", "The pitcher walked the batter on four straight balls.", WASEI, "500"),
    ("hit by pitch", "死球(デッドボール)。投球が打者に当たって出塁すること。和製英語の『デッドボール』(dead ball)は英語では別の意味(プレー停止中のボール)になり、正しくはhit by pitch(略してHBP)と言う。", "名詞句", "He was awarded first base after being hit by pitch.", WASEI, "600"),
    ("warm up", "準備運動をする、ウォーミングアップする。和製英語の『アップする』のように英語のupだけを動詞的に使う言い方は通じず、正しくはwarm up(名詞はwarm-up)と表現する。", "動詞句", "The players warmed up on the field before the game started.", WASEI, "400"),
    ("tracksuit", "上下セットのスウェット、トレーニングウェア。和製英語の『ジャージ』(jersey)は英語では背番号入りの競技用シャツ1枚を指し、上下セットの部屋着・運動着はtracksuitやsweatsと言う。", "名詞", "He was wearing a gray tracksuit for his morning jog.", WASEI, "400"),
    ("TV personality", "テレビタレント。和製英語の『タレント』(talent)は英語では「才能」の意味で、テレビに出る有名人本人を指すには使えない。正しくはTV personalityやcelebrityと言う。", "名詞", "She became a popular TV personality after appearing on several talk shows.", WASEI, "500"),
    ("theme song", "主題歌、テーマソング。和製英語の『イメージソング』は英語では通じず、番組・映画などのテーマ曲は英語ではtheme songと言う。", "名詞", "The movie's theme song became a huge hit.", WASEI, "400"),
    ("concert", "コンサート、ライブ。和製英語で『ライブ』を単独の名詞として「ライブに行く」のように使うのは英語では不自然で、正しくはconcertやlive showと言う。", "名詞", "We're going to a concert this weekend.", WASEI, "300"),
    ("newscaster", "ニュースキャスター。和製英語の『キャスター』(caster)は英語では「(家具の)小さな車輪」などを指し、ニュース番組の司会者にはnewscasterやnews anchorを使う。", "名詞", "The newscaster reported live from the scene of the accident.", WASEI, "600"),
    ("host", "(番組の)司会者。和製英語の『MC』は日本のテレビ・ラジオでは番組の司会者を指すが、英語のMC(master of ceremonies)は主にイベントの進行役やラップの担い手を指し、番組の司会者は普通hostと言う。", "名詞", "The show's host introduced each guest before the interview.", WASEI, "400"),
    ("figurine", "小さな人形、フィギュア。和製英語の『フィギュア』(figure)は英語では「数字」や「体型」などの意味になり、可動式の人形はaction figure、置物のような人形はfigurineと言う。", "名詞", "He collects anime figurines and displays them on a shelf.", WASEI, "500"),
    ("physical contact", "身体的な触れ合い。和製英語の『スキンシップ』(skinship)は英語には存在しない造語で、正しくはphysical contactやphysical affectionと表現する。", "名詞", "Physical contact, like hugging, can help strengthen a bond between parent and child.", WASEI, "500"),
    ("go on a diet", "減量のために食事制限をする。英語のdietは「食事内容」全般を指し、必ずしも減量を意味しない。和製英語の『ダイエットする』(運動も含めて痩せる行為全般)を表すには、食事制限ならgo on a diet、運動も含む場合はlose weightと言う方が正確。", "動詞句", "I've decided to go on a diet and cut back on sweets.", WASEI, "400"),
    ("one-on-one", "1対1の。和製英語の『マンツーマン』(man-to-man)は英語ではバスケットボールなどの守備戦術を指す専門用語で、個人指導やパーソナルレッスンには使わない。一般的な1対1の指導にはone-on-one(lesson/coaching)と言う。", "形容詞", "The tutor offers one-on-one lessons twice a week.", WASEI, "500"),
    ("textbook", "教科書。和製英語の『テキスト』(text)は英語では「本文」や「携帯のメッセージ」を指すことが多く、授業で使う教科書はtextbookと言う。", "名詞", "Please open your textbook to page 42.", WASEI, "300"),
    ("essay", "小論文、エッセイ、作文。和製英語の『レポート』(report)は日本語では作文全般を指すことが多いが、英語のreportは事実に基づく報告書を意味し、自分の意見をまとめた文章はessayやpaperと言う。", "名詞", "Students were asked to write a 500-word essay on climate change.", WASEI, "500"),
    ("key ring", "キーホルダー、鍵をまとめる金具の輪。和製英語の『キーホルダー』(key holder)は英語では「鍵をかけておく壁掛けフック」などを指すことが多く、持ち歩く鍵の束をまとめるものはkey ring(またはkeychain)と言う。", "名詞", "She attached a small charm to her key ring.", WASEI, "300"),
    ("cream puff", "シュークリーム。和製英語の『シュークリーム』はフランス語choux à la crèmeが由来で、英語では通じない。正しくはcream puffと言う。", "名詞", "The bakery's cream puffs are filled with fresh custard.", WASEI, "400"),
]

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    WASEI_SCENE: [
        ("My sister works as an office worker at a trading company.", "「OL」(office lady)は和製英語。性別を限定せず英語ではoffice workerと言う。"),
        ("My father has been a company employee for thirty years.", "「サラリーマン」は和製英語。英語ではcompany employeeやoffice workerと言う。"),
        ("That manager is abusing his authority over the junior staff.", "「パワハラ」(power harassment)は和製英語の造語。英語ではabuse of authorityやworkplace bullyingと表現する。"),
        ("We need to negotiate the price with the client next week.", "「ネゴ」はnegotiationを略した和製語。英語では省略せずnegotiateと言う。"),
        ("What's your username on that forum?", "「ハンドルネーム」は和製英語。英語ではusernameやscreen nameと言う。"),
        ("Check out our company's website for more details.", "日本語の「ホームページ」はサイト全体を指すが、英語のhomepageはトップページのみ。サイト全体はwebsiteと言う。"),
        ("Can I borrow a mechanical pencil?", "「シャープペンシル」は商品名由来の和製英語。英語ではmechanical pencilと言う。"),
        ("Holding hands is a nice way to bond with your kids.", "「スキンシップ」は和製英語で英語に対応語がない。physical affectionやbondingなどで表現する。"),
        ("I got my ears pierced last week.", "「ピアス」は和製英語。英語ではearring(s)と言い、pierceは「(穴を)開ける」という動詞。"),
        ("I bought a new sweatshirt for the winter.", "「トレーナー」は和製英語。英語ではsweatshirtと言う。trainerは英語では指導者や運動靴の意味。"),
        ("She's wearing a beautiful blue dress.", "「ワンピース」は和製英語。英語では単にdressと言う。"),
        ("He always wears a white dress shirt to work.", "「Yシャツ」は\"white shirt\"が訛った和製英語。英語ではdress shirtと言う。"),
        ("Let's go to the buffet for lunch.", "「バイキング」は帝国ホテルの命名に由来する和製英語。英語ではbuffetと言う。"),
        ("Can I get a lemon-lime soda, please?", "日本語の「サイダー」は炭酸飲料だが、英語のciderはりんご酒/果汁を指す。炭酸飲料はlemon-lime sodaと言う。"),
        ("I'd like a corn dog, please.", "「アメリカンドッグ」は和製英語。英語ではcorn dogと言う。"),
        ("Turn on your hazard lights.", "日本語では「ハザード」だけで使うが、英語では必ずhazard lightsとlightsまで言う。"),
        ("We need to stop at a gas station soon.", "「ガソリンスタンド」は和製英語。英語ではgas station(米)/petrol station(英)と言う。"),
        ("Let's ride the roller coaster first.", "「ジェットコースター」は和製英語。英語ではroller coasterと言う。"),
        ("The doctor told him to stop playing sports for a while.", "「ドクターストップ」は和製英語。英語ではthe doctor told him to stopのように表現する。"),
        ("Could you turn on the air conditioner? It's hot in here.", "「クーラー」は和製英語(英語のcoolerは保冷ボックスの意味)。冷房機はair conditionerと言う。"),
        ("Her father walked her down the aisle.", "「バージンロード」は和製英語で英語に対応語がない。英語では単にaisleと言う。"),
        ("That seat is reserved for elderly or disabled passengers.", "「シルバーシート」は和製英語。英語ではpriority seatと言う。"),
        ("She was pushing a stroller through the park.", "「ベビーカー」は和製英語。英語ではstroller(米)/pram(英)と言う。"),
        ("Please put your phone on silent mode during the meeting.", "「マナーモード」は和製英語。英語ではsilent modeやvibrate modeと言う。"),
        ("Ask the front desk for extra towels.", "「フロント」だけで使うのは和製英語的用法。英語ではfront deskやreceptionと言う。"),
        ("She has an American father and a Japanese mother, so she's biracial.", "「ハーフ」は和製英語で失礼に響くこともある。英語ではmixed-raceやbiracialと言う。"),
        ("Call our toll-free number for customer support.", "「フリーダイヤル」は和製英語。英語ではtoll-free numberと言う。"),
        ("We're planning to renovate our kitchen next spring.", "「リフォーム」は和製英語(英語のreformは制度改革の意味)。改装はrenovateと言う。"),
        ("He's a popular TV personality in Japan.", "「タレント」は和製英語。英語ではTV personalityやcelebrityと言う。talentは「才能」の意味。"),
        ("That tabloid show covers a lot of celebrity gossip.", "「ワイドショー」は和製英語。英語ではtabloid showやentertainment news showと言う。"),
    ],
}


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

        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        ph_added = ph_skipped = 0
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in ph_existing:
                    ph_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                ph_existing.add(en.lower())
                ph_added += 1

    print(f"words:   +{w_added} (skipped {w_skipped})")
    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    with db() as conn:
        print("totals -> words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
              "phrases:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
