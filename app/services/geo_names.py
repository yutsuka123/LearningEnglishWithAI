"""アクセス地図・ランキングの地名を日本語表記にする(2026-09-29・オーナー指示)。

- 日本の地名: 日本語(都道府県=東京都、市区町村=千代田区)。
- 外国の地名: カタカナ(英文)。例: アメリカ合衆国（United States）、ロサンゼルス（Los Angeles）。
  中国語圏など漢字表記が定着している地名は、その漢字(英文)。例: 中国（China）、北京（Beijing）。
- 対応表に無い地名は**英語のまま**表示する(音訳を推測して誤った表記を出さないため)。
  新しい地名が出たら、このファイルの表に足す(scripts/check_geo_names.py が本番で見つかった地名の網羅を検査する)。

外部の位置情報API(ipapi.co / ipwho.is)が返す英語の地名を入力とする。「The Netherlands」と「Netherlands」、
「Turkey」と「Türkiye」のような表記ゆれは canonical_country() で1つにまとめる(ランキングで同じ国が
2行に分かれないようにするため)。DBの生の値(英語)は変えない(判定用の country == 'Japan' 等はそのまま使う)。
"""

from __future__ import annotations

import unicodedata


def _norm(s: str | None) -> str:
    """照合用に正規化(アクセント記号を除き小文字化・アポストロフィ統一・空白を1つに)。"""
    t = unicodedata.normalize("NFKD", (s or "").strip())
    t = "".join(ch for ch in t if not unicodedata.combining(ch))
    t = t.replace("’", "'").replace("`", "'")
    return " ".join(t.casefold().split())


def _table(raw: dict[str, str]) -> dict[str, str]:
    return {_norm(k): v for k, v in raw.items()}


# 国名の表記ゆれ → 代表の英語名
_COUNTRY_ALIAS = _table({
    "The Netherlands": "Netherlands", "Türkiye": "Turkey", "Czech Republic": "Czechia",
    "Republic of Korea": "South Korea", "Korea, Republic of": "South Korea",
    "United States of America": "United States", "USA": "United States",
    "UK": "United Kingdom", "Great Britain": "United Kingdom",
    "Russian Federation": "Russia", "Viet Nam": "Vietnam",
    "Côte d'Ivoire": "Ivory Coast", "Cote d'Ivoire": "Ivory Coast",
    "Hong Kong SAR": "Hong Kong", "Macau": "Macao", "Burma": "Myanmar",
    "Eswatini": "Swaziland", "Cabo Verde": "Cape Verde", "East Timor": "Timor-Leste",
})

# 国名(代表の英語名 → 日本語)
_COUNTRY_JA = _table({
    "Japan": "日本", "United States": "アメリカ合衆国", "Brazil": "ブラジル", "Germany": "ドイツ",
    "Singapore": "シンガポール", "France": "フランス", "Netherlands": "オランダ", "Hong Kong": "香港",
    "Canada": "カナダ", "United Kingdom": "イギリス", "Argentina": "アルゼンチン", "South Korea": "韓国",
    "Sweden": "スウェーデン", "China": "中国", "Belgium": "ベルギー", "Russia": "ロシア",
    "Indonesia": "インドネシア", "Venezuela": "ベネズエラ", "Ireland": "アイルランド",
    "Philippines": "フィリピン", "India": "インド", "Bangladesh": "バングラデシュ", "Pakistan": "パキスタン",
    "Poland": "ポーランド", "Turkey": "トルコ", "Ukraine": "ウクライナ", "Mexico": "メキシコ",
    "Vietnam": "ベトナム", "Oman": "オマーン", "Kazakhstan": "カザフスタン", "Slovenia": "スロベニア",
    "United Arab Emirates": "アラブ首長国連邦", "Afghanistan": "アフガニスタン",
    "Dominican Republic": "ドミニカ共和国", "Panama": "パナマ", "Finland": "フィンランド",
    "Andorra": "アンドラ", "Switzerland": "スイス", "Saudi Arabia": "サウジアラビア", "Taiwan": "台湾",
    "Senegal": "セネガル", "Honduras": "ホンジュラス", "Bolivia": "ボリビア", "Chile": "チリ",
    "Peru": "ペルー", "Algeria": "アルジェリア", "South Africa": "南アフリカ", "Spain": "スペイン",
    "Czechia": "チェコ", "Australia": "オーストラリア", "Malaysia": "マレーシア", "Nepal": "ネパール",
    "Hungary": "ハンガリー", "Angola": "アンゴラ", "Albania": "アルバニア", "Costa Rica": "コスタリカ",
    "Uruguay": "ウルグアイ", "Suriname": "スリナム", "Tunisia": "チュニジア", "Uzbekistan": "ウズベキスタン",
    "Morocco": "モロッコ", "Paraguay": "パラグアイ", "Jordan": "ヨルダン",
    "Saint Kitts and Nevis": "セントクリストファー・ネイビス", "Kyrgyzstan": "キルギス",
    "Ecuador": "エクアドル", "Kuwait": "クウェート", "Botswana": "ボツワナ", "Colombia": "コロンビア",
    "Ethiopia": "エチオピア", "Belarus": "ベラルーシ", "Italy": "イタリア", "Ivory Coast": "コートジボワール",
    # まだ観測していないが今後出うる国(表記の追加を減らすため)
    "Thailand": "タイ", "Egypt": "エジプト", "Nigeria": "ナイジェリア", "Kenya": "ケニア", "Israel": "イスラエル",
    "Iran": "イラン", "Iraq": "イラク", "Qatar": "カタール", "Bahrain": "バーレーン", "Sri Lanka": "スリランカ",
    "Myanmar": "ミャンマー", "Cambodia": "カンボジア", "Laos": "ラオス", "Mongolia": "モンゴル",
    "North Korea": "北朝鮮", "New Zealand": "ニュージーランド", "Norway": "ノルウェー", "Denmark": "デンマーク",
    "Iceland": "アイスランド", "Austria": "オーストリア", "Portugal": "ポルトガル", "Greece": "ギリシャ",
    "Romania": "ルーマニア", "Bulgaria": "ブルガリア", "Serbia": "セルビア", "Croatia": "クロアチア",
    "Slovakia": "スロバキア", "Lithuania": "リトアニア", "Latvia": "ラトビア", "Estonia": "エストニア",
    "Luxembourg": "ルクセンブルク", "Malta": "マルタ", "Cyprus": "キプロス", "Georgia": "ジョージア",
    "Armenia": "アルメニア", "Azerbaijan": "アゼルバイジャン", "Moldova": "モルドバ",
    "Bosnia and Herzegovina": "ボスニア・ヘルツェゴビナ", "North Macedonia": "北マケドニア",
    "Montenegro": "モンテネグロ", "Kosovo": "コソボ", "Cuba": "キューバ", "Jamaica": "ジャマイカ",
    "Haiti": "ハイチ", "Guatemala": "グアテマラ", "El Salvador": "エルサルバドル", "Nicaragua": "ニカラグア",
    "Trinidad and Tobago": "トリニダード・トバゴ", "Bahamas": "バハマ", "Puerto Rico": "プエルトリコ",
    "Ghana": "ガーナ", "Cameroon": "カメルーン", "Tanzania": "タンザニア", "Uganda": "ウガンダ",
    "Zambia": "ザンビア", "Zimbabwe": "ジンバブエ", "Mozambique": "モザンビーク", "Namibia": "ナミビア",
    "Libya": "リビア", "Sudan": "スーダン", "Lebanon": "レバノン", "Syria": "シリア", "Yemen": "イエメン",
    "Turkmenistan": "トルクメニスタン", "Tajikistan": "タジキスタン", "Bhutan": "ブータン",
    "Maldives": "モルディブ", "Brunei": "ブルネイ", "Macao": "マカオ", "Papua New Guinea": "パプアニューギニア",
    "Fiji": "フィジー", "Madagascar": "マダガスカル", "Mali": "マリ", "Niger": "ニジェール",
    "Democratic Republic of the Congo": "コンゴ民主共和国", "Congo": "コンゴ共和国",
    "Rwanda": "ルワンダ", "Somalia": "ソマリア", "Palestine": "パレスチナ", "Liechtenstein": "リヒテンシュタイン",
    "Monaco": "モナコ", "San Marino": "サンマリノ", "Guam": "グアム", "Guyana": "ガイアナ",
    "Belize": "ベリーズ", "Barbados": "バルバドス", "Mauritius": "モーリシャス",
})

# 都道府県(英語 → 日本語)
_JP_PREF = _table({
    "Hokkaido": "北海道", "Aomori": "青森県", "Iwate": "岩手県", "Miyagi": "宮城県", "Akita": "秋田県",
    "Yamagata": "山形県", "Fukushima": "福島県", "Ibaraki": "茨城県", "Tochigi": "栃木県", "Gunma": "群馬県",
    "Saitama": "埼玉県", "Chiba": "千葉県", "Tokyo": "東京都", "Kanagawa": "神奈川県", "Niigata": "新潟県",
    "Toyama": "富山県", "Ishikawa": "石川県", "Fukui": "福井県", "Yamanashi": "山梨県", "Nagano": "長野県",
    "Gifu": "岐阜県", "Shizuoka": "静岡県", "Aichi": "愛知県", "Mie": "三重県", "Shiga": "滋賀県",
    "Kyoto": "京都府", "Osaka": "大阪府", "Hyogo": "兵庫県", "Nara": "奈良県", "Wakayama": "和歌山県",
    "Tottori": "鳥取県", "Shimane": "島根県", "Okayama": "岡山県", "Hiroshima": "広島県",
    "Yamaguchi": "山口県", "Tokushima": "徳島県", "Kagawa": "香川県", "Ehime": "愛媛県", "Kochi": "高知県",
    "Fukuoka": "福岡県", "Saga": "佐賀県", "Nagasaki": "長崎県", "Kumamoto": "熊本県", "Oita": "大分県",
    "Miyazaki": "宮崎県", "Kagoshima": "鹿児島県", "Okinawa": "沖縄県",
})
# 都道府県名の付属語(「Tokyo Metropolis」「Osaka Prefecture」等)を除いて照合する
_PREF_SUFFIXES = (" prefecture", " metropolis", " metropolitan", " to", " fu", " ken", "-ken", "-fu", "-to")

# 日本の市区町村(英語のローマ字 → 日本語)。同じローマ字が別の市を指しうるので、都道府県で絞る必要が
# 出たら _JP_CITY_BY_PREF に足す(現状は市区町村名だけで一意)。
_JP_CITY = _table({
    "Tokyo": "東京", "Osaka": "大阪市", "Yokohama": "横浜市", "Nagoya": "名古屋市", "Kyoto": "京都市",
    "Saitama": "さいたま市", "Gifu-shi": "岐阜市", "Gifu": "岐阜市", "Nisshin": "日進市", "Hiroshima": "広島市",
    "Otsu": "大津市", "Chiba": "千葉市", "Okayama": "岡山市", "Takamatsu": "高松市", "Kumamoto": "熊本市",
    "Fukuoka": "福岡市", "Utsunomiya": "宇都宮市", "Sendai": "仙台市", "Shizuoka": "静岡市", "Kobe": "神戸市",
    "Yamaguchi": "山口市", "Shinagawa-ku": "品川区", "Nanao": "七尾市", "Nara-shi": "奈良市", "Nara": "奈良市",
    "Amagasaki": "尼崎市", "Toyama": "富山市", "Sapporo": "札幌市", "Tomiya": "富谷市", "Onomichi": "尾道市",
    "Shimonoseki": "下関市", "Kurihara": "栗原市", "Wakayama": "和歌山市", "Fukuyama": "福山市",
    "Maebashi": "前橋市", "Matsuyama": "松山市", "Matsumoto": "松本市", "Fukui-shi": "福井市", "Fukui": "福井市",
    "Chita": "知多市", "Numazu": "沼津市", "Niigata": "新潟市", "Tsu": "津市", "Chofu": "調布市", "Mito": "水戸市",
    "Anjo": "安城市", "Shibayama": "芝山町", "Tottori": "鳥取市", "Naha": "那覇市", "Hakodate": "函館市",
    "Oita": "大分市", "Yokkaichi": "四日市市", "Kanazawa": "金沢市", "Gero": "下呂市", "Narita": "成田市",
    "Toyohashi": "豊橋市", "Hikone": "彦根市", "Tsukuba": "つくば市", "Hino": "日野市", "Yonakuni": "与那国町",
    "Nagasaki": "長崎市", "Ube": "宇部市", "Hamamatsu": "浜松市", "Tatsunocho-tominaga": "たつの市龍野町富永",
    "Miyazaki": "宮崎市", "Fukushima": "福島市", "Hachioji": "八王子市", "Kuji": "久慈市",
    "Kakogawacho-honmachi": "加古川市加古川町本町", "Hatsukaichi": "廿日市市", "Kochi": "高知市",
    "Kurayoshi": "倉吉市", "Tachiarai": "大刀洗町", "Tosu": "鳥栖市", "Yamagata": "山形市",
    "Minami-Alps": "南アルプス市", "Hanno": "飯能市", "Akashi": "明石市", "Kagoshima": "鹿児島市",
    "Fujisawa": "藤沢市", "Nakagawa": "中川町", "Hanawa": "鹿角市花輪", "Matsue": "松江市", "Noda": "野田村",
    "Date": "伊達市", "Hirado": "平戸市", "Izumi": "出水市", "Fukuecho": "五島市福江町", "Shirakawa": "白河市",
    "Naganohara": "長野原町", "Tomakomai": "苫小牧市", "Kawasaki": "川崎市", "Iwashita": "岩下",
    "Togane": "東金市", "Onagawa Cho": "女川町", "Abashiri": "網走市", "Kasugai": "春日井市",
    "Higashimurayama": "東村山市", "Toyota": "豊田市", "Takeo": "武雄市", "Muroran": "室蘭市",
    "Shimabara": "島原市", "Maebaru-chuo": "糸島市前原中央", "Sukumo": "宿毛市",
    # 主な地名(今後出うるもの)
    "Kitakyushu": "北九州市", "Kumagaya": "熊谷市", "Kawagoe": "川越市", "Funabashi": "船橋市", "Sakai": "堺市",
    "Himeji": "姫路市", "Nishinomiya": "西宮市", "Machida": "町田市", "Tachikawa": "立川市", "Musashino": "武蔵野市",
    "Chiyoda": "千代田区", "Chuo-ku": "中央区", "Minato-ku": "港区", "Shinjuku-ku": "新宿区", "Shibuya-ku": "渋谷区",
    "Setagaya-ku": "世田谷区", "Koto-ku": "江東区", "Taito-ku": "台東区", "Sumida-ku": "墨田区",
    "Chiyoda-ku": "千代田区", "Suginami-ku": "杉並区", "Nerima-ku": "練馬区", "Ota-ku": "大田区",
    "Toshima-ku": "豊島区", "Bunkyo-ku": "文京区", "Meguro-ku": "目黒区", "Nakano-ku": "中野区",
    "Itabashi-ku": "板橋区", "Kita-ku": "北区", "Arakawa-ku": "荒川区", "Adachi-ku": "足立区",
    "Katsushika-ku": "葛飾区", "Edogawa-ku": "江戸川区",
})

# 米国の州(英語 → 日本語)
_US_STATE = _table({
    "Alabama": "アラバマ州", "Alaska": "アラスカ州", "Arizona": "アリゾナ州", "Arkansas": "アーカンソー州",
    "California": "カリフォルニア州", "Colorado": "コロラド州", "Connecticut": "コネチカット州",
    "Delaware": "デラウェア州", "Florida": "フロリダ州", "Georgia": "ジョージア州", "Hawaii": "ハワイ州",
    "Idaho": "アイダホ州", "Illinois": "イリノイ州", "Indiana": "インディアナ州", "Iowa": "アイオワ州",
    "Kansas": "カンザス州", "Kentucky": "ケンタッキー州", "Louisiana": "ルイジアナ州", "Maine": "メイン州",
    "Maryland": "メリーランド州", "Massachusetts": "マサチューセッツ州", "Michigan": "ミシガン州",
    "Minnesota": "ミネソタ州", "Mississippi": "ミシシッピ州", "Missouri": "ミズーリ州", "Montana": "モンタナ州",
    "Nebraska": "ネブラスカ州", "Nevada": "ネバダ州", "New Hampshire": "ニューハンプシャー州",
    "New Jersey": "ニュージャージー州", "New Mexico": "ニューメキシコ州", "New York": "ニューヨーク州",
    "North Carolina": "ノースカロライナ州", "North Dakota": "ノースダコタ州", "Ohio": "オハイオ州",
    "Oklahoma": "オクラホマ州", "Oregon": "オレゴン州", "Pennsylvania": "ペンシルベニア州",
    "Rhode Island": "ロードアイランド州", "South Carolina": "サウスカロライナ州", "South Dakota": "サウスダコタ州",
    "Tennessee": "テネシー州", "Texas": "テキサス州", "Utah": "ユタ州", "Vermont": "バーモント州",
    "Virginia": "バージニア州", "Washington": "ワシントン州", "West Virginia": "ウェストバージニア州",
    "Wisconsin": "ウィスコンシン州", "Wyoming": "ワイオミング州",
    "Washington, D.C.": "ワシントンD.C.", "District of Columbia": "ワシントンD.C.",
})

# 外国の都市: 代表の英語国名 → {都市(英語) → 日本語}
_FOREIGN_CITY_RAW: dict[str, dict[str, str]] = {
    "United States": {
        "Los Angeles": "ロサンゼルス", "Ashburn": "アッシュバーン", "New York City": "ニューヨーク",
        "New York": "ニューヨーク", "Santa Clara": "サンタクララ", "Boydton": "ボイドン",
        "Mountain View": "マウンテンビュー", "Dallas": "ダラス", "Atlanta": "アトランタ", "Boardman": "ボードマン",
        "Washington": "ワシントン", "Ann Arbor": "アナーバー", "Council Bluffs": "カウンシルブラッフス",
        "Quincy": "クインシー", "Cupertino": "クパチーノ", "San Jose": "サンノゼ", "Las Vegas": "ラスベガス",
        "Hillsboro": "ヒルズボロ", "San Francisco": "サンフランシスコ", "DeKalb": "デカルブ",
        "North Charleston": "ノースチャールストン", "Hilliard": "ヒリアード", "Columbus": "コロンバス",
        "Clifton": "クリフトン", "Springfield": "スプリングフィールド", "Social Circle": "ソーシャルサークル",
        "Gallatin": "ギャラティン", "Fort Worth": "フォートワース", "Mansfield": "マンスフィールド",
        "Huntsville": "ハンツビル", "North Bergen": "ノースバーゲン", "Seattle": "シアトル", "Hanover": "ハノーバー",
        "Wilmington": "ウィルミントン", "Altoona": "アルトゥーナ", "Huntingburg": "ハンティングバーグ",
        "The Dalles": "ザ・ダレス", "Brooklyn": "ブルックリン", "Jacksonville": "ジャクソンビル",
        "Baltimore": "ボルチモア", "Phoenix": "フェニックス", "Bend": "ベンド", "Portland": "ポートランド",
        "Buffalo": "バッファロー", "Kane": "ケイン", "Kansas City": "カンザスシティ", "Chicago": "シカゴ",
        "Oak Hill": "オークヒル", "Mesa": "メサ", "Secaucus": "セコーカス", "Silver Spring": "シルバースプリング",
        "Ogden": "オグデン", "Minnetonka": "ミネトンカ", "Salt Lake City": "ソルトレイクシティ",
        "Rancho Cucamonga": "ランチョクカモンガ", "Rochester": "ロチェスター", "Inglewood": "イングルウッド",
        "Detroit": "デトロイト", "Hicksville": "ヒックスビル", "Waldorf": "ウォルドーフ", "Houston": "ヒューストン",
        "Londonderry": "ロンドンデリー", "New Orleans": "ニューオーリンズ", "Orangeburg": "オレンジバーグ",
        "Mobile": "モービル", "Lexington": "レキシントン", "Charlotte": "シャーロット",
        "Willimantic": "ウィリマンティック", "Meridian": "メリディアン", "Pullman": "プルマン",
        "Alexandria": "アレクサンドリア", "Boston": "ボストン", "Miami": "マイアミ", "Denver": "デンバー",
        "San Diego": "サンディエゴ", "Philadelphia": "フィラデルフィア", "Pittsburgh": "ピッツバーグ",
        "Minneapolis": "ミネアポリス", "Austin": "オースティン", "San Antonio": "サンアントニオ",
    },
    "Singapore": {"Singapore": "シンガポール"},
    "Netherlands": {"Amsterdam": "アムステルダム", "Groningen": "フローニンゲン", "Kerkrade": "ケルクラーデ",
                    "Rotterdam": "ロッテルダム", "The Hague": "ハーグ", "Utrecht": "ユトレヒト"},
    "Hong Kong": {"Hong Kong": "香港"},
    "Germany": {"Neu-Isenburg": "ノイ・イーゼンブルク", "Falkenstein": "ファルケンシュタイン",
                "Falkenstein/Vogtl.": "ファルケンシュタイン", "Limburg an der Lahn": "リンブルク・アン・デア・ラーン",
                "Augsburg": "アウクスブルク", "Nuremberg": "ニュルンベルク", "Runkel": "ルンケル", "Berlin": "ベルリン",
                "Frankfurt am Main": "フランクフルト", "Frankfurt": "フランクフルト", "Munich": "ミュンヘン",
                "Hamburg": "ハンブルク", "Cologne": "ケルン", "Düsseldorf": "デュッセルドルフ",
                "Dusseldorf": "デュッセルドルフ", "Stuttgart": "シュトゥットガルト", "Dresden": "ドレスデン"},
    "Brazil": {"Sao Paulo": "サンパウロ", "Campinas": "カンピーナス", "Brasilia": "ブラジリア",
               "Rio de Janeiro": "リオデジャネイロ", "Fortaleza": "フォルタレザ", "Valenca": "バレンサ",
               "Curitiba": "クリチバ", "Coruja": "コルージャ", "Anapolis": "アナポリス",
               "Santo Andre": "サントアンドレ", "Ararangua": "アララングア", "Porto Alegre": "ポルトアレグレ",
               "Teresopolis": "テレゾポリス", "Fernandopolis": "フェルナンドポリス", "Brumado": "ブルマド",
               "Uberlandia": "ウベルランジア", "Cana Brava do Norte": "カナブラバ・ド・ノルテ",
               "Sao Jose dos Campos": "サンジョゼ・ドス・カンポス", "Piracicaba": "ピラシカバ",
               "Lauro de Freitas": "ラウロ・デ・フレイタス", "Papuda": "パプーダ",
               "Cachoeirinha": "カショエイリーニャ", "Salvador": "サルバドール", "Belo Horizonte": "ベロオリゾンテ",
               "Recife": "レシフェ", "Manaus": "マナウス"},
    "South Korea": {"Seoul": "ソウル", "Busan": "釜山", "Incheon": "仁川"},
    "Canada": {"Montreal": "モントリオール", "Toronto": "トロント", "Winkler": "ウィンクラー",
               "Vancouver": "バンクーバー", "Ottawa": "オタワ", "Calgary": "カルガリー"},
    "France": {"Paris": "パリ", "Roubaix": "ルーベ", "Lauterbourg": "ローターブール", "Saint-Denis": "サン＝ドニ",
               "Strasbourg": "ストラスブール", "Wattrelos": "ワトルロス", "Gravelines": "グラヴリーヌ",
               "Lyon": "リヨン", "Marseille": "マルセイユ"},
    "Sweden": {"Stockholm": "ストックホルム", "Uppsala": "ウプサラ", "Gothenburg": "ヨーテボリ"},
    "Belgium": {"Brussels": "ブリュッセル"},
    "China": {"Beijing": "北京", "Baoding": "保定", "Yangquan": "陽泉", "Shanghai": "上海", "Shenzhen": "深圳",
              "Guangzhou": "広州", "Hangzhou": "杭州", "Chengdu": "成都"},
    "Ireland": {"Dublin": "ダブリン", "Clonmany": "クロンマニー"},
    "United Kingdom": {"London": "ロンドン", "Harrietsham": "ハリエットシャム", "Edinburgh": "エディンバラ",
                       "York": "ヨーク", "Nottingham": "ノッティンガム", "Glasgow": "グラスゴー",
                       "Manchester": "マンチェスター", "Birmingham": "バーミンガム", "Slough": "スラウ"},
    "Indonesia": {"Jakarta": "ジャカルタ", "Trenggalek": "トレンガレク", "Bandung": "バンドン", "Bekasi": "ブカシ",
                  "Surabaya": "スラバヤ"},
    "Russia": {"Moscow": "モスクワ", "Vladivostok": "ウラジオストク", "Kol'chugino": "コルチュギノ",
               "Yekaterinburg": "エカテリンブルク", "Kirov": "キーロフ", "Saint Petersburg": "サンクトペテルブルク"},
    "Argentina": {"Castelar": "カステラル", "Buenos Aires": "ブエノスアイレス", "Bernal Oeste": "ベルナル・オエステ",
                  "Presidencia de la Plaza": "プレシデンシア・デ・ラ・プラサ", "Casilda": "カシルダ",
                  "El Galpon": "エル・ガルポン", "Santa Fe": "サンタフェ", "Laguna Paiva": "ラグナ・パイバ",
                  "Cordoba": "コルドバ", "Rosario": "ロサリオ"},
    "Afghanistan": {"Kabul": "カブール"},
    "Oman": {"Muscat": "マスカット", "Salalah": "サラーラ"},
    "Panama": {"Panama City": "パナマシティ"},
    "Pakistan": {"Karachi": "カラチ", "Haripur": "ハリプール", "Mirpur Khas": "ミルプール・カース",
                 "Jauharabad": "ジョハラバード", "Lahore": "ラホール", "Islamabad": "イスラマバード"},
    "Poland": {"Warsaw": "ワルシャワ", "Poznan": "ポズナン", "Debica": "デンビツァ", "Kielce": "キェルツェ",
               "Krakow": "クラクフ"},
    "Slovenia": {"Ljubljana": "リュブリャナ", "Maribor": "マリボル"},
    "United Arab Emirates": {"Dubai": "ドバイ", "Al Fujairah City": "フジャイラ", "Abu Dhabi": "アブダビ"},
    "India": {"Mumbai": "ムンバイ", "New Delhi": "ニューデリー", "Gurgaon": "グルガオン", "Agra": "アグラ",
              "Vizianagaram": "ビジャヤナガラム", "Delhi": "デリー", "Bengaluru": "ベンガルール",
              "Bangalore": "ベンガルール", "Chennai": "チェンナイ", "Hyderabad": "ハイデラバード",
              "Kolkata": "コルカタ"},
    "Andorra": {"Pas de la Casa": "パス・デ・ラ・カーサ"},
    "Switzerland": {"Zurich": "チューリッヒ", "Geneva": "ジュネーブ", "Basel": "バーゼル"},
    "Venezuela": {"Caracas": "カラカス", "Chacao": "チャカオ", "Maturin": "マトゥリン", "Guasipati": "グアシパティ",
                  "Barquisimeto": "バルキシメト", "Barinas": "バリナス", "Naguanagua": "ナグアナグア"},
    "Taiwan": {"Taipei": "台北", "Kaohsiung": "高雄", "Taichung": "台中"},
    "Senegal": {"Dakar": "ダカール"},
    "Bangladesh": {"Dhaka": "ダッカ", "Gaurnadi": "ガウルナディ", "Gaibandha": "ガイバンダ", "Natore": "ナトール",
                   "Noakhali": "ノアカリ"},
    "Turkey": {"Istanbul": "イスタンブール", "Adana": "アダナ", "Kirsehir": "クルシェヒル",
               "Asagidere": "アシャウデレ", "Ankara": "アンカラ", "Izmir": "イズミル"},
    "Honduras": {"Tegucigalpa": "テグシガルパ"},
    "Vietnam": {"Hanoi": "ハノイ", "Son La": "ソンラ", "Hai Duong": "ハイズオン", "Ho Chi Minh City": "ホーチミン"},
    "Peru": {"Lima": "リマ"},
    "Ukraine": {"Kyiv": "キーウ", "Kiev": "キーウ", "Khorostkiv": "ホロストキウ", "Kolodenka": "コロデンカ",
                "Sevastopol": "セヴァストポリ", "Kharkiv": "ハルキウ", "Odesa": "オデーサ"},
    "Czechia": {"Prague": "プラハ"},
    "Australia": {"Canberra": "キャンベラ", "Sydney": "シドニー", "Melbourne": "メルボルン"},
    "Finland": {"Helsinki": "ヘルシンキ", "Lappeenranta": "ラッペーンランタ"},
    "Malaysia": {"Kuala Lumpur": "クアラルンプール"},
    "Saudi Arabia": {"Riyadh": "リヤド", "Jeddah": "ジッダ"},
    "Nepal": {"Tulsipur": "トゥルシプル", "Kathmandu": "カトマンズ"},
    "Hungary": {"Budapest": "ブダペスト"},
    "Angola": {"Luanda": "ルアンダ"},
    "Albania": {"Tirana": "ティラナ"},
    "Mexico": {"Irapuato": "イラプアト", "Tlahuac": "トラワク", "Ciudad Nezahualcoyotl": "シウダー・ネサワルコヨトル",
               "Tlaxcala": "トラスカラ", "Mexico City": "メキシコシティ"},
    "Dominican Republic": {"Concepcion de La Vega": "コンセプシオン・デ・ラ・ベガ", "San Cristobal": "サンクリストバル",
                           "Hato Mayor": "ハトマヨール", "Santo Domingo": "サントドミンゴ"},
    "Costa Rica": {"Cartago": "カルタゴ", "San Jose": "サンホセ"},
    "Philippines": {"Irahuan": "イラウアン", "Balagtasin": "バラグタシン", "Aurora": "オーロラ",
                    "Cavite City": "カビテシティ", "Pintuyan": "ピントゥヤン", "Cebu City": "セブシティ",
                    "Palestina": "パレスティナ", "Manila": "マニラ", "Quezon City": "ケソンシティ"},
    "Uruguay": {"Maldonado": "マルドナド", "Montevideo": "モンテビデオ"},
    "Suriname": {"Paramaribo": "パラマリボ"},
    "Tunisia": {"Bizerte": "ビゼルト", "Tunis": "チュニス"},
    "Uzbekistan": {"Tashkent": "タシケント"},
    "Morocco": {"Meknes": "メクネス", "Casablanca": "カサブランカ", "Rabat": "ラバト"},
    "Paraguay": {"Fernando de la Mora": "フェルナンド・デ・ラ・モラ", "Asuncion": "アスンシオン"},
    "Bolivia": {"Cochabamba": "コチャバンバ", "Achocalla": "アチョカリャ", "La Paz": "ラパス"},
    "Jordan": {"Amman": "アンマン"},
    "Chile": {"Santiago": "サンティアゴ", "Molina": "モリーナ"},
    "Saint Kitts and Nevis": {"Newcastle": "ニューカッスル"},
    "Kyrgyzstan": {"Osh": "オシュ", "Bishkek": "ビシュケク"},
    "Kazakhstan": {"Shchuchinsk": "シュチンスク", "Astana": "アスタナ", "Almaty": "アルマトイ",
                   "Karagandy": "カラガンダ"},
    "Algeria": {"M'Sila": "ムシラ", "Annaba": "アンナバ", "Algiers": "アルジェ"},
    "South Africa": {"Hazelmere": "ヘーゼルミア", "Abbotsdale": "アボッツデール", "Johannesburg": "ヨハネスブルグ",
                     "Cape Town": "ケープタウン"},
    "Spain": {"Madrid": "マドリード", "Caceres": "カセレス", "Barcelona": "バルセロナ"},
    "Ecuador": {"Quito": "キト"},
    "Kuwait": {"Al Farwaniyah": "ファルワニーヤ"},
    "Botswana": {"Mogoditshane": "モゴディツァネ"},
    "Colombia": {"Pereira": "ペレイラ", "Bogota": "ボゴタ", "Medellin": "メデジン"},
    "Ethiopia": {"Addis Ababa": "アディスアベバ"},
    "Belarus": {"Minsk": "ミンスク"},
    "Italy": {"Taranto": "ターラント", "Rome": "ローマ", "Milan": "ミラノ"},
    "Ivory Coast": {"Abidjan": "アビジャン"},
    "Thailand": {"Bangkok": "バンコク"},
}
_FOREIGN_CITY: dict[str, dict[str, str]] = {
    _norm(country): {_norm(c): ja for c, ja in cities.items()}
    for country, cities in _FOREIGN_CITY_RAW.items()
}

# 外国の地域(州・県など。米国以外): 代表の英語国名 → {地域(英語) → 日本語}。
# 対応表に無く、同じ国の都市の表に同名があれば(例: Seoul)それを使う。それも無ければ英語のまま。
_FOREIGN_REGION_RAW: dict[str, dict[str, str]] = {
    "Netherlands": {"North Holland": "ノールトホラント州", "Provincie Noord-Holland": "ノールトホラント州",
                    "Noord-Holland": "ノールトホラント州", "Groningen": "フローニンゲン州",
                    "Provincie Groningen": "フローニンゲン州", "Limburg": "リンブルフ州"},
    "Brazil": {"Sao Paulo": "サンパウロ州", "Rio de Janeiro": "リオデジャネイロ州", "Federal District": "連邦区",
               "Bahia": "バイーア州", "Ceara": "セアラー州", "Minas Gerais": "ミナスジェライス州",
               "Parana": "パラナ州", "Goias": "ゴイアス州", "Santa Catarina": "サンタカタリーナ州",
               "Rio Grande do Sul": "リオグランデドスル州", "Mato Grosso": "マットグロッソ州",
               "Pernambuco": "ペルナンブコ州"},
    "Germany": {"Hesse": "ヘッセン州", "Hessen": "ヘッセン州", "Saxony": "ザクセン州", "Bavaria": "バイエルン州",
                "Berlin": "ベルリン"},
    "France": {"Ile-de-France": "イル＝ド＝フランス地域圏", "Hauts-de-France": "オー＝ド＝フランス地域圏",
               "Grand Est": "グラン・テスト地域圏"},
    "South Korea": {"Seoul": "ソウル特別市"},
    "Canada": {"Quebec": "ケベック州", "Ontario": "オンタリオ州", "Manitoba": "マニトバ州"},
    "United Kingdom": {"England": "イングランド", "Scotland": "スコットランド"},
    "Sweden": {"Stockholm": "ストックホルム県", "Uppsala": "ウプサラ県"},
    "China": {"Beijing": "北京市", "Hebei": "河北省", "Shanxi": "山西省"},
    "Ireland": {"Leinster": "レンスター", "Ulster": "アルスター"},
    "Belgium": {"Brussels Capital": "ブリュッセル首都圏地域", "Bruxelles-Capitale": "ブリュッセル首都圏地域"},
    "Indonesia": {"Jakarta": "ジャカルタ特別州", "West Java": "西ジャワ州", "East Java": "東ジャワ州"},
    "Argentina": {"Buenos Aires": "ブエノスアイレス州", "Santa Fe": "サンタフェ州",
                  "Buenos Aires F.D.": "ブエノスアイレス連邦区", "Chaco": "チャコ州", "Salta": "サルタ州"},
    "Russia": {"Moscow": "モスクワ", "Primorye": "沿海地方", "Vladimir Oblast": "ウラジーミル州",
               "Sverdlovsk Oblast": "スヴェルドロフスク州", "Kirov Oblast": "キーロフ州"},
    "Pakistan": {"Sindh": "シンド州", "Khyber Pakhtunkhwa": "ハイバル・パフトゥンハー州", "Punjab": "パンジャーブ州"},
    "Afghanistan": {"Kabul": "カブール州"},
    "Oman": {"Muscat": "マスカット県", "Dhofar": "ズファール県"},
    "Panama": {"Panama": "パナマ県"},
    "United Arab Emirates": {"Dubai": "ドバイ首長国", "Fujairah": "フジャイラ首長国"},
    "India": {"Maharashtra": "マハーラーシュトラ州", "Delhi": "デリー", "Haryana": "ハリヤーナー州",
              "Uttar Pradesh": "ウッタル・プラデーシュ州", "Andhra Pradesh": "アーンドラ・プラデーシュ州"},
    "Andorra": {"Encamp": "エンカンプ教区"},
    "Switzerland": {"Zurich": "チューリッヒ州"},
    "Venezuela": {"Distrito Federal": "首都区", "Miranda": "ミランダ州", "Monagas": "モナガス州",
                  "Bolivar": "ボリバル州", "Lara": "ララ州", "Barinas": "バリナス州", "Carabobo": "カラボボ州"},
    "Philippines": {"Calabarzon": "カラバルソン地域", "Mimaropa": "ミマロパ地域", "Caraga": "カラガ地域",
                    "Eastern Visayas": "東ビサヤ地域", "Central Visayas": "中部ビサヤ地域",
                    "Bicol Region": "ビコル地方"},
    "Senegal": {"Dakar": "ダカール州"},
    "Bangladesh": {"Dhaka Division": "ダッカ管区", "Barisal Division": "バリシャール管区",
                   "Rangpur Division": "ロングプル管区", "Rajshahi Division": "ラージシャーヒー管区",
                   "Chittagong": "チッタゴン管区"},
    "Turkey": {"Istanbul": "イスタンブール県", "Adana": "アダナ県", "Kirsehir": "クルシェヒル県",
               "Bartin": "バルトゥン県"},
    "Honduras": {"Francisco Morazan Department": "フランシスコ・モラサン県"},
    "Vietnam": {"Hanoi": "ハノイ", "Son La Province": "ソンラー省", "Hai Duong Province": "ハイズオン省"},
    "Peru": {"Lima Province": "リマ県"},
    "Singapore": {"Central Singapore": "シンガポール中部"},
    "Poland": {"Masovian Voivodeship": "マゾフシェ県", "Mazovia": "マゾフシェ県",
               "Greater Poland": "ヴィエルコポルスカ県", "Subcarpathia": "ポトカルパチェ県",
               "Swietokrzyskie": "シフィェントクシスキェ県"},
    "Ukraine": {"Kyiv": "キーウ", "Ternopil": "テルノーピリ州", "Rivne": "リウネ州", "Sevastopol City": "セヴァストポリ"},
    "Czechia": {"Prague": "プラハ"},
    "Slovenia": {"Mestna Obcina Ljubljana": "リュブリャナ市", "Ljubljana": "リュブリャナ",
                 "Maribor City Municipality": "マリボル市"},
    "Australia": {"Australian Capital Territory": "首都特別地域"},
    "Finland": {"Uusimaa": "ウーシマー県", "South Karelia": "南カレリア県"},
    "Malaysia": {"Kuala Lumpur": "クアラルンプール連邦直轄領"},
    "Saudi Arabia": {"Riyadh Region": "リヤド州", "Mecca Region": "メッカ州"},
    "Taiwan": {"Taipei": "台北市", "Taiwan": "台湾"},
    "Nepal": {"Lumbini Province": "ルンビニ州"},
    "Hungary": {"Budapest": "ブダペスト"},
    "Angola": {"Luanda": "ルアンダ州"},
    "Albania": {"Tirana": "ティラナ県"},
    "Mexico": {"Guanajuato": "グアナフアト州", "Mexico City": "メキシコシティ", "Mexico": "メキシコ州",
               "Tlaxcala": "トラスカラ州"},
    "Dominican Republic": {"La Vega": "ラ・ベガ県", "San Cristobal": "サンクリストバル県",
                           "Sanchez Ramirez": "サンチェス・ラミレス県"},
    "Costa Rica": {"Cartago Province": "カルタゴ県"},
    "Uruguay": {"Maldonado": "マルドナド県"},
    "Suriname": {"Paramaribo District": "パラマリボ地区"},
    "Tunisia": {"Bizerte Governorate": "ビゼルト県"},
    "Uzbekistan": {"Tashkent": "タシケント"},
    "Morocco": {"Fes-Meknes": "フェズ＝メクネス地方"},
    "Paraguay": {"Central Department": "セントラル県"},
    "Bolivia": {"Cochabamba": "コチャバンバ県", "La Paz Department": "ラパス県"},
    "Jordan": {"Amman": "アンマン県"},
    "Chile": {"Santiago Metropolitan": "サンティアゴ首都州", "Maule Region": "マウレ州"},
    "Saint Kitts and Nevis": {"Saint James Windwa": "セントジェームズ・ウィンドワード教区"},
    "Kyrgyzstan": {"Osh Region": "オシュ州"},
    "Kazakhstan": {"Aqmola": "アクモラ州", "Astana": "アスタナ", "Almaty": "アルマトイ", "Karaganda": "カラガンダ州"},
    "Algeria": {"M'Sila": "ムシラ県", "Annaba": "アンナバ県"},
    "South Africa": {"KwaZulu-Natal": "クワズール・ナタール州", "Western Cape": "西ケープ州"},
    "Spain": {"Madrid": "マドリード州", "Extremadura": "エストレマドゥーラ州"},
    "Ecuador": {"Pichincha": "ピチンチャ県"},
    "Kuwait": {"Al Farwaniyah": "ファルワニーヤ県"},
    "Botswana": {"Kweneng": "クウェネン地区"},
    "Colombia": {"Risaralda Department": "リサラルダ県"},
    "Ethiopia": {"Addis Ababa": "アディスアベバ"},
    "Belarus": {"Minsk City": "ミンスク市"},
    "Italy": {"Apulia": "プーリア州"},
    "Ivory Coast": {"Abidjan": "アビジャン"},
}
_FOREIGN_REGION: dict[str, dict[str, str]] = {
    _norm(country): {_norm(r): ja for r, ja in regions.items()}
    for country, regions in _FOREIGN_REGION_RAW.items()
}


def canonical_country(name: str | None) -> str:
    """表記ゆれを代表の英語名にそろえる(例: The Netherlands → Netherlands)。不明なら元の名前。"""
    n = (name or "").strip()
    return _COUNTRY_ALIAS.get(_norm(n), n) if n else ""


def _pref_key(region: str) -> str:
    k = _norm(region)
    for suf in _PREF_SUFFIXES:
        if k.endswith(suf) and len(k) > len(suf):
            return k[: -len(suf)]
    return k


def _paren(ja: str, en: str) -> str:
    """外国の地名は「カタカナ（英文）」。日本語と英語が同じ綴りなら括弧は付けない。"""
    return f"{ja}（{en}）" if en and ja != en else ja


def country_ja(name: str | None) -> str:
    """国名の日本語(英文なし)。対応表に無ければ英語のまま。"""
    c = canonical_country(name)
    return _COUNTRY_JA.get(_norm(c), c)


def country_label(name: str | None) -> str:
    """日本=「日本」/外国=「アメリカ合衆国（United States）」。対応表に無ければ英語のまま。"""
    c = canonical_country(name)
    if not c:
        return ""
    ja = _COUNTRY_JA.get(_norm(c))
    if not ja:
        return c
    return ja if _norm(c) == "japan" else _paren(ja, c)


def region_label(country: str | None, region: str | None) -> str:
    """日本=都道府県名/外国=「カリフォルニア州（California）」等/対応表に無ければ英語のまま。"""
    r = (region or "").strip()
    if not r:
        return ""
    c = _norm(canonical_country(country))
    if c == "japan":
        return _JP_PREF.get(_pref_key(r), r)
    if c == "united states":
        ja = _US_STATE.get(_norm(r))
        return _paren(ja, r) if ja else r
    # 米国以外の外国: 地域の表 → 同名の都市の表(例: 地域が「Seoul」)→ 英語のまま
    ja = (_FOREIGN_REGION.get(c, {}).get(_norm(r))
          or _FOREIGN_CITY.get(c, {}).get(_norm(r)))
    return _paren(ja, r) if ja else r


def city_label(country: str | None, region: str | None, city: str | None) -> str:
    """日本=市区町村名の日本語/外国=「ロサンゼルス（Los Angeles）」/不明=英語のまま。"""
    t = (city or "").strip()
    if not t:
        return ""
    c = _norm(canonical_country(country))
    if c == "japan":
        return _JP_CITY.get(_norm(t), t)
    ja = _FOREIGN_CITY.get(c, {}).get(_norm(t))
    return _paren(ja, t) if ja else t
