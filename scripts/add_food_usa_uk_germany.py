# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated words & phrases for AMERICAN / BRITISH / GERMAN CUISINE,
authored by Claude.

Focus (料理ドメインを深掘り): 既存の「料理」ドメインには米国(hamburger, hot dog,
mac and cheese, buffalo wings, brownie, fried chicken, clam chowder)・英国
(fish and chips, full English breakfast, Yorkshire pudding, bangers and
mash, black pudding, shepherd's pie, scone, crumpet, trifle)・ドイツ
(schnitzel, sauerkraut, pretzel)の定番語がすでにある。本スクリプトはそれらを
再投入せず、さらに一段深い語彙を追加する。

- 米国: 地域性のあるBBQ(テキサス/キャロライナ/カンザスシティ)、南部の家庭料理
  (ソウルフード、grits、biscuits and gravy)、Tex-Mex、ケイジャン/クレオール
  料理、感謝祭の食卓語彙、ダイナー・フードトラック文化、doggy bag文化。
- 英国: アフタヌーンティー文化、パブ料理・パブ文化(pint, last orders,
  gastropub)、地方料理(ハギス、ウェルシュ・レアビット、コーニッシュ・パスティ)、
  chips/fries の米英差など食文化の勘所。
- ドイツ: ソーセージ・肉料理のバリエーション、ビール文化(ビアガーデン、
  Oktoberfest、ビールの種類)、パン文化(ライ麦パン、プンパーニッケル)、
  Kaffee und Kuchen(コーヒーとケーキ)の食文化。

料理を「注文する・尋ねる・説明する」ための実践フレーズも収録
(store/pub/diner etiquette、地域名物を尋ねる表現、米英の食文化の違いの
説明など)。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_food_usa_uk_germany.py
      python scripts/add_food_usa_uk_germany.py --missing-words   # report only

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- phrases: scene -> [(english, japanese)] --------------------------------

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "アメリカ料理": [
        ("What's today's special?", "本日のおすすめは何ですか？"),
        ("I'll have the biscuits and gravy, please.", "ビスケット・アンド・グレイビーをお願いします。"),
        ("Could I get that to go?", "それ、持ち帰りでお願いできますか？〔米: to go／英: takeaway〕"),
        ("Can I get a doggy bag for the rest?", "残りを持ち帰り用の袋に入れてもらえますか？〔米国では食べ残しを持ち帰るのが一般的〕"),
        ("How spicy is the chili?", "そのチリはどのくらい辛いですか？"),
        ("Is this Texas-style or Kansas City-style barbecue?", "これはテキサス風ですか、カンザスシティ風のバーベキューですか？"),
        ("What's the difference between Cajun and Creole cooking?", "ケイジャン料理とクレオール料理の違いは何ですか？"),
        ("The portions here are huge.", "ここは量がとても多いですね。〔米国は一人前の量が大きいことで知られる〕"),
        ("Southern comfort food is all about fried chicken and biscuits.", "南部のソウルフード的な家庭料理といえばフライドチキンとビスケットですね。"),
        ("Let's grab something from that food truck.", "あのフードトラックで何か買いましょう。"),
        ("We always have turkey and stuffing on Thanksgiving.", "感謝祭にはいつも七面鳥とスタッフィングを食べます。"),
        ("Don't forget the cranberry sauce.", "クランベリーソースを忘れずに。"),
        ("Save room for pumpkin pie.", "パンプキンパイのためにお腹を空けておいてね。"),
        ("We roasted marshmallows for s'mores over the campfire.", "キャンプファイヤーでスモア用にマシュマロを焼きました。"),
        ("A New England clam bake is cooked right on the beach.", "ニューイングランドのクラムベイクは浜辺でそのまま調理します。"),
        ("Grits are a Southern breakfast staple.", "グリッツは南部の朝食の定番です。"),
        ("This barbecue sauce is more vinegar-based, which is very Carolina.", "このバーベキューソースは酢ベースで、いかにもキャロライナ風です。"),
        ("The brisket has been in the smoker for twelve hours.", "ブリスケットは12時間燻製されています。"),
        ("In America, 'biscuit' means a soft bread roll, not a cookie.", "アメリカでは『biscuit』はクッキーではなく柔らかいパンのことです。〔英国のbiscuitはクッキーの意味〕"),
        ("Is the check separate or together?", "お会計は別々ですか、まとめてですか？"),
        ("A po' boy is stuffed with fried shrimp or oysters.", "ポーボーイは揚げたエビや牡蠣がぎっしり詰まっています。"),
        ("We finished with beignets and powdered sugar everywhere.", "最後はベニエを食べて粉砂糖だらけになりました。"),
    ],
    "イギリス料理": [
        ("Shall we book a table for afternoon tea?", "アフタヌーンティーの予約をしましょうか？"),
        ("Do you put the jam or the clotted cream on first?", "ジャムとクロテッドクリーム、どちらを先に塗りますか？〔デヴォン式/コーンウォール式で順番が違う定番論争〕"),
        ("We're having a proper Sunday roast this weekend.", "今週末はちゃんとしたサンデーローストを食べます。"),
        ("What's the local specialty here?", "この土地の名物料理は何ですか？"),
        ("Fancy a pint after work?", "仕事の後、一杯どうですか？〔pint=ビール一杯、パブ文化の定番の誘い文句〕"),
        ("What time is last orders?", "ラストオーダーは何時ですか？"),
        ("It's my round — what are you having?", "今回は私のおごりです。何を飲みますか？〔輪番でおごり合うパブ文化〕"),
        ("Shall we get some pub grub before we head home?", "帰る前にパブ料理でも食べましょうか？"),
        ("Is haggis really made from sheep's offal?", "ハギスは本当に羊の内臓からできているのですか？"),
        ("A ploughman's lunch usually comes with cheese, pickle, and bread.", "プラウマンズランチには普通チーズとピクルスとパンが付いてきます。"),
        ("Welsh rarebit is basically fancy cheese on toast.", "ウェルシュ・レアビットは要するに凝ったチーズトーストです。"),
        ("We picked up a couple of Cornish pasties for the train.", "電車の中で食べる用にコーニッシュ・パスティを買いました。"),
        ("In Britain, 'chips' are thick-cut fries, not crisps.", "英国で『chips』は太めのフライドポテトのことで、crispsとは別物です。〔米のfriesにあたる〕"),
        ("Careful — in the UK, 'chips' and 'fries' aren't quite the same thing.", "気をつけて、英国では『chips』と『fries』は微妙に違います。〔米chips=薄いポテトチップス、英chips=フライドポテト〕"),
        ("Let's pop down to the chippy for dinner.", "夕食に近所のフィッシュ・アンド・チップス屋に行きましょう。〔chippy=フィッシュ・アンド・チップス店のくだけた呼び方〕"),
        ("This carvery lets you choose your own cuts of roast meat.", "このカーヴェリーではローストした肉を好きな部位で選べます。"),
        ("Bubble and squeak is a great way to use up leftovers.", "バブル・アンド・スクィークは残り物を使うのにぴったりです。"),
        ("Fancy some elevenses before we carry on?", "続ける前にイレブンジス（午前のお茶休憩）でもどうですか？"),
        ("High tea was originally a working-class evening meal, not a fancy snack.", "ハイティーはもともと労働者階級の夕食で、上品な軽食ではありませんでした。〔afternoon teaとの混同注意〕"),
        ("Could we get the bill, please?", "お会計をお願いできますか？"),
        ("Would you like your steak and kidney pie with mushy peas?", "ステーキ・アンド・キドニーパイにマッシュド・ピーは添えますか？"),
        ("The pub does a proper Sunday carvery.", "そのパブはちゃんとしたサンデーカーヴェリーをやっています。"),
    ],
    "ドイツ料理": [
        ("What would you recommend — bratwurst or currywurst?", "ブラートヴルストとカリーヴルスト、どちらがおすすめですか？"),
        ("Could I get a beer stein as a souvenir?", "お土産にビアジョッキを買えますか？"),
        ("Is this a pilsner or a lager?", "これはピルスナーですか、それともラガーですか？"),
        ("We spent the afternoon at a beer garden.", "午後はビアガーデンで過ごしました。"),
        ("Everyone wears traditional dress during Oktoberfest.", "オクトーバーフェストの間はみんな伝統衣装を着ます。"),
        ("Prost!", "乾杯！〔ドイツ語の乾杯の掛け声、英語の会話でもそのまま使われる〕"),
        ("Sauerbraten needs to marinate for several days before cooking.", "ザワーブラーテンは調理前に数日間漬け込む必要があります。"),
        ("Rouladen is beef wrapped around bacon, onion, and pickles.", "ルーラーデンはベーコンと玉ねぎとピクルスを巻いた牛肉料理です。"),
        ("Spaetzle is a kind of soft egg noodle.", "シュペッツレは柔らかい卵麺の一種です。"),
        ("Black Forest cake gets its flavor from cherries and kirsch.", "黒い森のケーキはチェリーとキルシュで風味付けされています。"),
        ("Is this rye bread or pumpernickel?", "これはライ麦パンですか、それともプンパーニッケルですか？"),
        ("German bakeries open very early in the morning.", "ドイツのパン屋はとても早朝から開いています。"),
        ("Let's take a break for Kaffee und Kuchen.", "コーヒーとケーキの休憩にしましょう。〔ドイツの午後のお茶とケーキの習慣〕"),
        ("A slice of stollen is traditional at Christmas.", "シュトレンのひと切れはクリスマスの伝統です。"),
        ("Mulled wine really warms you up at the Christmas market.", "グリューワインはクリスマスマーケットで本当に体を温めてくれます。"),
        ("Could you recommend a good local brewery?", "地元のおすすめの醸造所を教えていただけますか？"),
        ("Is the schnitzel served with spaetzle or fries here?", "ここのシュニッツェルはシュペッツレとフライドポテトのどちらと一緒に出てきますか？"),
        ("We ordered a whole rouladen for the table to share.", "テーブルでシェアするためにルーラーデンを注文しました。"),
        ("What's the regional specialty here in Bavaria?", "ここバイエルンの地元の名物料理は何ですか？"),
        ("German beer is often brewed according to strict purity rules.", "ドイツのビールは厳格な純粋令に従って醸造されることが多いです。"),
        ("Weisswurst is traditionally eaten before noon, with sweet mustard.", "ヴァイスヴルストは伝統的に正午前に甘いマスタードと一緒に食べます。"),
        ("The red cabbage pairs really well with the roast pork.", "赤キャベツはローストポークによく合いますね。"),
    ],
}


# --- words: (english, japanese, part_of_speech, example, domain, level) -----

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 米国: BBQ地域差・Tex-Mex ---
    ("brisket", "ブリスケット（牛肩バラ肉、BBQで燻製する部位）", "名詞", "The brisket had been smoked for twelve hours.", "料理", "750"),
    ("pulled pork", "プルドポーク（豚肉を柔らかく煮込んでほぐした料理）", "名詞", "We piled pulled pork onto a soft bun.", "料理", "700"),
    ("spare ribs", "スペアリブ", "名詞", "The spare ribs fell right off the bone.", "料理", "650"),
    ("dry rub", "ドライラブ（焼く前にすり込む香辛料のミックス）", "名詞", "He coated the ribs with a dry rub.", "料理", "800"),
    ("barbecue sauce", "バーベキューソース", "名詞", "Kansas City barbecue sauce is thick and sweet.", "料理", "600"),
    ("smoker", "燻製器（バーベキュー用）", "名詞", "He left the brisket in the smoker overnight.", "料理", "700"),
    ("Texas-style barbecue", "テキサス風バーベキュー（牛肉中心、シンプルな塩胡椒の下味）", "名詞", "Texas-style barbecue focuses on beef brisket.", "料理", "850"),
    ("Carolina barbecue", "キャロライナ風バーベキュー（酢やマスタードベースのソースが特徴）", "名詞", "Carolina barbecue often uses a vinegar-based sauce.", "料理", "850"),
    ("Kansas City barbecue", "カンザスシティ風バーベキュー（甘めのトマトベースソースが特徴）", "名詞", "Kansas City barbecue is known for its sweet, thick sauce.", "料理", "850"),
    ("Tex-Mex", "テクスメクス料理（テキサス風にアレンジされたメキシコ料理）", "名詞", "Tex-Mex food blends Texan and Mexican flavors.", "料理", "700"),
    ("fajitas", "ファヒータ", "名詞", "The fajitas came sizzling on a hot skillet.", "料理", "650"),
    ("quesadilla", "ケサディーヤ", "名詞", "She ordered a cheese quesadilla.", "料理", "600"),
    ("nachos", "ナチョス", "名詞", "We shared a plate of nachos.", "料理", "550"),
    ("chili con carne", "チリコンカン", "名詞", "Chili con carne warms you up on a cold day.", "料理", "700"),
    # --- 米国: ケイジャン/クレオール(ルイジアナ) ---
    ("Cajun", "ケイジャン料理（の）（ルイジアナの田舎風料理）", "形容詞", "Cajun cooking uses a lot of cayenne pepper.", "料理", "800"),
    ("Creole", "クレオール料理（の）（ルイジアナの都会的な融合料理）", "形容詞", "Creole cuisine blends French, African, and Spanish influences.", "料理", "850"),
    ("gumbo", "ガンボ（ルイジアナのシチュー）", "名詞", "Gumbo is thickened with okra or a roux.", "料理", "800"),
    ("jambalaya", "ジャンバラヤ", "名詞", "Jambalaya mixes rice with sausage and shrimp.", "料理", "850"),
    ("beignet", "ベニエ（ニューオーリンズの揚げ菓子パン）", "名詞", "Beignets are dusted with powdered sugar.", "料理", "850"),
    ("po' boy", "ポーボーイ（ルイジアナの具だくさんサンドイッチ）", "名詞", "A po' boy is stuffed with fried shrimp or oysters.", "料理", "900"),
    # --- 米国: 南部・感謝祭・その他地域食文化 ---
    ("clam bake", "クラムベイク（浜辺で貝や魚介を蒸し焼きにする行事）", "名詞", "A clam bake is cooked over hot stones on the beach.", "料理", "900"),
    ("soul food", "ソウルフード（アフリカ系アメリカ人の伝統的な家庭料理）", "名詞", "Fried chicken and mac and cheese are classic soul food.", "料理", "750"),
    ("biscuits and gravy", "ビスケット・アンド・グレイビー", "名詞", "Biscuits and gravy is a popular Southern breakfast.", "料理", "800"),
    ("grits", "グリッツ（とうもろこしの粗挽き粉を煮た南部料理）", "名詞", "She had a bowl of cheesy grits.", "料理", "850"),
    ("cornbread", "コーンブレッド", "名詞", "Cornbread goes well with chili.", "料理", "650"),
    ("collard greens", "コラードグリーンズ（南部でよく食べる葉野菜）", "名詞", "Collard greens are simmered with smoked meat.", "料理", "850"),
    ("chicken and waffles", "チキン・アンド・ワッフル", "名詞", "Chicken and waffles combines fried chicken with a sweet waffle.", "料理", "800"),
    ("peach cobbler", "ピーチコブラー", "名詞", "Peach cobbler is a warm Southern dessert.", "料理", "800"),
    ("key lime pie", "キーライムパイ（フロリダ名物のライムパイ）", "名詞", "Key lime pie is tart and creamy.", "料理", "800"),
    ("diner", "ダイナー（アメリカの大衆食堂）", "名詞", "We stopped at a roadside diner for breakfast.", "料理", "550"),
    ("waffle", "ワッフル", "名詞", "He ordered a waffle with whipped cream.", "料理", "500"),
    ("maple syrup", "メープルシロップ", "名詞", "She poured maple syrup over her pancakes.", "料理", "500"),
    ("stuffing", "スタッフィング（七面鳥に詰める具材、感謝祭料理）", "名詞", "The stuffing was made with bread, celery, and herbs.", "料理", "700"),
    ("cranberry sauce", "クランベリーソース", "名詞", "Cranberry sauce is a Thanksgiving staple.", "料理", "650"),
    ("pumpkin pie", "パンプキンパイ", "名詞", "Pumpkin pie is the classic Thanksgiving dessert.", "料理", "600"),
    ("gravy", "グレイビー（肉汁で作るソース）", "名詞", "Pour some gravy over the mashed potatoes.", "料理", "600"),
    ("s'mores", "スモア（マシュマロとチョコをビスケットで挟んで焼くお菓子）", "名詞", "We made s'mores around the campfire.", "料理", "750"),
    ("food truck", "フードトラック", "名詞", "A food truck sells tacos on that corner.", "料理", "550"),
    ("doggy bag", "残り物持ち帰り用の袋", "名詞", "Could I get a doggy bag for this?", "料理", "650"),
    ("sourdough", "サワードウ（酸味のある発酵パン、サンフランシスコが有名）", "名詞", "San Francisco is famous for its sourdough bread.", "料理", "700"),
    ("biscuit", "ビスケット（米国式、ふわふわの塩味のパン。英国のbiscuitはクッキーの意味）", "名詞", "Southern biscuits are flaky and buttery.", "料理", "650"),
    # --- 英国: アフタヌーンティー ---
    ("afternoon tea", "アフタヌーンティー", "名詞", "They booked afternoon tea at a fancy hotel.", "料理", "550"),
    ("clotted cream", "クロテッドクリーム（濃厚なクリーム）", "名詞", "Scones are served with clotted cream and jam.", "料理", "750"),
    ("tea sandwich", "ティーサンドイッチ（アフタヌーンティーで出す小さなサンドイッチ）", "名詞", "The tea sandwiches had the crusts cut off.", "料理", "750"),
    ("cream tea", "クリームティー（スコーン、クロテッドクリーム、紅茶のセット）", "名詞", "A cream tea usually includes two scones.", "料理", "800"),
    ("high tea", "ハイティー（労働者階級の伝統的な夕食）", "名詞", "High tea was originally a hearty evening meal, not a light snack.", "料理", "850"),
    ("elevenses", "イレブンジス（午前11時頃のお茶休憩）", "名詞", "She always has a biscuit at elevenses.", "料理", "900"),
    ("tearoom", "ティールーム（お茶を提供する喫茶店）", "名詞", "We stopped at a tearoom in the village.", "料理", "700"),
    # --- 英国: パブ料理・パブ文化 ---
    ("Sunday roast", "サンデーロースト（日曜日の伝統的なロースト料理）", "名詞", "We always have a Sunday roast with the family.", "料理", "650"),
    ("pie and mash", "パイ・アンド・マッシュ（ロンドンの伝統的な肉パイとマッシュポテト）", "名詞", "Pie and mash is a traditional East London dish.", "料理", "900"),
    ("ploughman's lunch", "プラウマンズランチ（パン・チーズ・ピクルスなどの冷製ランチ）", "名詞", "A ploughman's lunch is a simple, cold pub meal.", "料理", "950"),
    ("toad in the hole", "トード・イン・ザ・ホール（ソーセージ入りヨークシャープディング）", "名詞", "Toad in the hole is sausages baked in batter.", "料理", "900"),
    ("bubble and squeak", "バブル・アンド・スクィーク（残り野菜を炒めた料理）", "名詞", "Bubble and squeak is made from leftover vegetables.", "料理", "900"),
    ("pub grub", "パブ料理（パブで出される軽食）", "名詞", "We had some pub grub before the match.", "料理", "800"),
    ("gastropub", "ガストロパブ（本格的な料理を出すパブ）", "名詞", "The gastropub serves upscale versions of pub classics.", "料理", "850"),
    ("pint", "パイント（ビールなどの単位、約568ml）", "名詞", "He ordered a pint of lager.", "料理", "600"),
    ("last orders", "ラストオーダー（閉店前の最終注文）", "名詞", "The bartender called last orders at eleven.", "料理", "800"),
    ("real ale", "リアルエール（伝統製法の生きた酵母入りビール）", "名詞", "The pub specializes in real ale.", "料理", "900"),
    ("steak and kidney pie", "ステーキ・アンド・キドニーパイ", "名詞", "Steak and kidney pie is a hearty pub classic.", "料理", "850"),
    ("mushy peas", "マッシュド・ピー（つぶしたグリーンピース）", "名詞", "Mushy peas are a classic side for fish and chips.", "料理", "800"),
    ("carvery", "カーヴェリー（ロースト肉を切り分けて提供する形式のレストラン）", "名詞", "We chose our meat at the carvery counter.", "料理", "850"),
    ("chippy", "フィッシュ・アンド・チップス店（くだけた呼び方）", "名詞", "Let's grab dinner from the chippy.", "料理", "800"),
    ("butty", "サンドイッチ（くだけた英国式の言い方）", "名詞", "He made himself a bacon butty.", "料理", "850"),
    # --- 英国: 地方料理・その他デザート ---
    ("haggis", "ハギス（スコットランドの伝統料理、羊の内臓を詰めた料理）", "名詞", "Haggis is traditionally served with neeps and tatties.", "料理", "900"),
    ("Welsh rarebit", "ウェルシュ・レアビット（チーズソースをかけたトースト）", "名詞", "Welsh rarebit is cheese sauce on toast.", "料理", "900"),
    ("Cornish pasty", "コーニッシュ・パスティ（肉と野菜を包んで焼いたパイ）", "名詞", "A Cornish pasty is a pastry filled with meat and vegetables.", "料理", "850"),
    ("Victoria sponge", "ヴィクトリアスポンジケーキ", "名詞", "Victoria sponge is filled with jam and cream.", "料理", "800"),
    ("golden syrup", "ゴールデンシロップ（英国の伝統的な糖蜜シロップ）", "名詞", "She drizzled golden syrup over her porridge.", "料理", "750"),
    ("treacle tart", "トリークルタルト（糖蜜のタルト）", "名詞", "Treacle tart is very sweet and sticky.", "料理", "850"),
    ("Scotch egg", "スコッチエッグ（ゆで卵をひき肉で包んで揚げたもの）", "名詞", "A Scotch egg makes a great pub snack.", "料理", "800"),
    ("sticky toffee pudding", "スティッキー・トフィー・プディング", "名詞", "Sticky toffee pudding is served warm with custard.", "料理", "850"),
    ("custard", "カスタード", "名詞", "Trifle is topped with a layer of custard.", "料理", "600"),
    # --- 米英の食文化差(注文まわり) ---
    ("starter", "前菜（英）（米ではappetizerと呼ぶ）", "名詞", "I'll have the soup as a starter.", "料理", "550"),
    ("entrée", "メインディッシュ（米）（英で古風に前菜の意味で使われることもある）", "名詞", "The entrée comes with a side salad.", "料理", "700"),
    # --- ドイツ: ソーセージ・肉料理 ---
    ("bratwurst", "ブラートヴルスト（ドイツの焼きソーセージ）", "名詞", "We grilled bratwurst at the barbecue.", "料理", "650"),
    ("currywurst", "カリーヴルスト（カレー粉をかけたソーセージ）", "名詞", "Currywurst is a popular Berlin street food.", "料理", "750"),
    ("Weisswurst", "ヴァイスヴルスト（バイエルンの白ソーセージ）", "名詞", "Weisswurst is traditionally eaten before noon.", "料理", "900"),
    ("sauerbraten", "ザワーブラーテン（酢に漬け込んだ牛肉の煮込み）", "名詞", "Sauerbraten is marinated for several days before cooking.", "料理", "900"),
    ("rouladen", "ルーラーデン（ベーコンや玉ねぎを巻いた牛肉料理）", "名詞", "Rouladen is rolled beef stuffed with bacon and pickles.", "料理", "900"),
    ("spaetzle", "シュペッツレ（南ドイツの卵麺）", "名詞", "The schnitzel was served with spaetzle.", "料理", "800"),
    ("red cabbage", "赤キャベツ（ドイツ料理の定番副菜）", "名詞", "Red cabbage is a classic side for roast pork.", "料理", "700"),
    ("German potato salad", "ジャーマンポテトサラダ（酢とベーコンで作る温かいポテトサラダ）", "名詞", "German potato salad is served warm with bacon and vinegar.", "料理", "750"),
    # --- ドイツ: 菓子・パン文化 ---
    ("Black Forest cake", "黒い森のケーキ（チェリーとチョコレートのケーキ）", "名詞", "Black Forest cake is layered with cherries and cream.", "料理", "750"),
    ("strudel", "シュトゥルーデル（薄い生地で果物を包んだ菓子、オーストリアとも重なる）", "名詞", "Apple strudel is a classic German and Austrian dessert.", "料理", "700"),
    ("stollen", "シュトレン（クリスマスに食べる菓子パン）", "名詞", "Stollen is a fruit bread eaten at Christmas.", "料理", "850"),
    ("Berliner", "ベルリーナー（ジャム入りドイツ風ドーナツ）", "名詞", "A Berliner is filled with jam instead of having a hole.", "料理", "850"),
    ("gingerbread", "ジンジャーブレッド（レープクーヘン、香辛料入りの焼き菓子）", "名詞", "Gingerbread is a Christmas market favorite in Germany.", "料理", "600"),
    ("pumpernickel", "プンパーニッケル（濃い色のライ麦パン）", "名詞", "Pumpernickel is dense and slightly sweet.", "料理", "800"),
    ("rye bread", "ライ麦パン", "名詞", "German rye bread is often dark and hearty.", "料理", "600"),
    ("Kaffee und Kuchen", "コーヒーとケーキの習慣（ドイツの午後のお茶の時間）", "名詞", "Kaffee und Kuchen is a beloved German afternoon tradition.", "料理", "900"),
    ("potato dumpling", "ポテトダンプリング（クネーデル）", "名詞", "Potato dumplings are a common side dish in Bavaria.", "料理", "800"),
    # --- ドイツ: ビール文化 ---
    ("beer garden", "ビアガーデン", "名詞", "We spent the evening at a beer garden.", "料理", "550"),
    ("Oktoberfest", "オクトーバーフェスト（ミュンヘンのビール祭り）", "名詞", "Millions of visitors attend Oktoberfest every year.", "料理", "600"),
    ("beer stein", "ビアジョッキ（陶器製の大きなジョッキ）", "名詞", "He collects decorative beer steins.", "料理", "700"),
    ("pilsner", "ピルスナー（すっきりした軽い口当たりのビール）", "名詞", "Pilsner is a pale, crisp lager.", "料理", "700"),
    ("lager", "ラガー（低温発酵させた一般的なビール）", "名詞", "Most mass-produced beer is lager.", "料理", "600"),
    ("wheat beer", "小麦ビール（ヴァイツェン）", "名詞", "Wheat beer is cloudy and often served with a lemon slice.", "料理", "700"),
    ("dark beer", "黒ビール（ドゥンケル）", "名詞", "Dark beer has a richer, toastier flavor.", "料理", "600"),
    ("brewery", "醸造所", "名詞", "The brewery offers tours on weekends.", "料理", "650"),
    ("mulled wine", "ホットワイン（グリューワイン、香辛料を入れて温めたワイン）", "名詞", "Mulled wine is popular at German Christmas markets.", "料理", "700"),
    # --- 料理を語る・注文する汎用語彙 ---
    ("hearty", "ボリュームのある・心のこもった", "形容詞", "It's a hearty stew, perfect for a cold day.", "料理", "600"),
    ("comfort food", "ほっとする家庭料理", "名詞", "Mac and cheese is classic American comfort food.", "料理", "650"),
    ("street food", "屋台料理・ストリートフード", "名詞", "Currywurst is popular German street food.", "料理", "550"),
    ("side dish", "付け合わせ・副菜", "名詞", "Mushy peas are a common side dish in Britain.", "料理", "500"),
    ("signature dish", "看板料理・名物料理", "名詞", "Brisket is the signature dish at this barbecue joint.", "料理", "750"),
    ("regional specialty", "地域の名物料理", "名詞", "Every state has its own regional specialty.", "料理", "800"),
    ("must-try", "ぜひ試すべき（もの）", "形容詞", "This bratwurst stand is a must-try.", "料理", "750"),
    ("portion size", "一人前の量", "名詞", "American portion sizes tend to be larger than in Europe.", "料理", "700"),
    ("all-you-can-eat", "食べ放題の", "形容詞", "The diner offers an all-you-can-eat pancake special.", "料理", "650"),
    ("pub culture", "パブ文化", "名詞", "Pub culture is central to British social life.", "料理", "800"),
]


# --- insertion --------------------------------------------------------------

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")
_STOP = {
    "the", "a", "an", "and", "or", "but", "if", "of", "to", "in", "on", "at",
    "for", "with", "from", "by", "as", "is", "are", "was", "were", "be", "been",
    "do", "does", "did", "have", "has", "had", "will", "would", "can", "could",
    "should", "may", "might", "must", "i", "you", "he", "she", "it", "we",
    "they", "me", "him", "her", "us", "them", "my", "your", "his", "its", "our",
    "their", "this", "that", "these", "those", "here", "there", "what", "when",
    "where", "who", "how", "why", "not", "no", "yes", "so", "up", "out", "off",
    "down", "let", "lets", "please", "thanks", "thank", "ok", "okay", "im",
    "ill", "id", "ive", "dont", "cant", "wont", "isnt", "thats", "whats",
    "very", "just", "too", "more", "some", "any", "all", "one", "two", "get",
    "got", "go", "going", "like", "want", "need", "make", "made", "take",
    "see", "now", "today", "tonight", "good", "well", "back", "about", "over",
    "into", "than", "then", "again", "really", "much", "many", "wish", "mind",
    "could", "would", "shall", "rather", "ever", "way", "one's", "off",
    "before", "later", "earlier", "second", "gist", "point", "way", "say",
    "saying", "sure", "understand", "following", "pick", "leave", "there",
}


def _content_words(phrases: list[tuple[str, str]]) -> set[str]:
    out: set[str] = set()
    for en, _ in phrases:
        for tok in _WORD_RE.findall(en.lower()):
            w = tok.strip("'-")
            if len(w) >= 4 and w not in _STOP:
                out.add(w)
    return out


def report_missing() -> None:
    """Print content words used in the new phrases that are not yet in `words`
    and not covered by the WORDS list above (authoring aid)."""
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
    covered = {w[0].lower() for w in WORDS}
    all_phrases = [p for lst in PHRASES_BY_SCENE.values() for p in lst]
    missing = sorted(
        w for w in _content_words(all_phrases)
        if w not in existing and w not in covered
    )
    print(f"missing content words ({len(missing)}):")
    print(", ".join(missing))


def main() -> int:
    if "--missing-words" in sys.argv:
        report_missing()
        return 0

    with db() as conn:
        ph_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
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

    print(f"phrases: +{ph_added} (skipped {ph_skipped})")
    print(f"words:   +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print("totals -> phrases:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0],
              "words:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
