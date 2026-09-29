"""app/services/geo_names.py の検査(2026-09-29)。

本番の位置情報キャッシュに実際にあった地名(2026-09-29時点: 国75・日本の都道府県45・日本の市区町村101・
外国の都市257・米国の州33)がすべて対応表にあること、表記の決まり(日本の地名=日本語のみ、外国の地名=
「カタカナ（英文）」)を守っていることを確認する。

  .venv/bin/python scripts/check_geo_names.py     # 0=全部OK
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.services import geo_names as g  # noqa: E402

OBS_COUNTRIES = """Japan; United States; Brazil; Germany; Singapore; France; The Netherlands; Hong Kong; Canada; United Kingdom; Argentina; South Korea; Sweden; China; Netherlands; Belgium; Russia; Indonesia; Venezuela; Ireland; Philippines; India; Bangladesh; Pakistan; Poland; Turkey; Ukraine; Mexico; Vietnam; Oman; Kazakhstan; Slovenia; United Arab Emirates; Afghanistan; Dominican Republic; Panama; Finland; Andorra; Switzerland; Saudi Arabia; Taiwan; Senegal; Honduras; Bolivia; Chile; Peru; Algeria; South Africa; Spain; Czechia; Türkiye; Australia; Malaysia; Nepal; Hungary; Angola; Albania; Costa Rica; Uruguay; Suriname; Tunisia; Uzbekistan; Morocco; Paraguay; Jordan; Saint Kitts and Nevis; Kyrgyzstan; Ecuador; Kuwait; Botswana; Colombia; Ethiopia; Belarus; Italy; Ivory Coast"""

OBS_PREFS = """Tokyo; Osaka; Aichi; Kanagawa; Hiroshima; Kyoto; Hyogo; Miyagi; Gifu; Chiba; Saitama; Yamaguchi; Hokkaido; Shizuoka; Shiga; Fukuoka; Okayama; Kagawa; Kumamoto; Ishikawa; Tochigi; Mie; Ibaraki; Nara; Nagasaki; Gunma; Toyama; Okinawa; Wakayama; Ehime; Fukushima; Nagano; Fukui; Tottori; Niigata; Iwate; Kochi; Oita; Saga; Kagoshima; Miyazaki; Yamagata; Yamanashi; Akita; Shimane"""

# 47都道府県(観測外も含めて全部)
ALL_PREFS = """Hokkaido; Aomori; Iwate; Miyagi; Akita; Yamagata; Fukushima; Ibaraki; Tochigi; Gunma; Saitama; Chiba; Tokyo; Kanagawa; Niigata; Toyama; Ishikawa; Fukui; Yamanashi; Nagano; Gifu; Shizuoka; Aichi; Mie; Shiga; Kyoto; Osaka; Hyogo; Nara; Wakayama; Tottori; Shimane; Okayama; Hiroshima; Yamaguchi; Tokushima; Kagawa; Ehime; Kochi; Fukuoka; Saga; Nagasaki; Kumamoto; Oita; Miyazaki; Kagoshima; Okinawa"""

OBS_JP_CITIES = """Tokyo|Tokyo; Osaka|Osaka; Kanagawa|Yokohama; Aichi|Nagoya; Kyoto|Kyoto; Saitama|Saitama; Gifu|Gifu-shi; Aichi|Nisshin; Hiroshima|Hiroshima; Shiga|Otsu; Chiba|Chiba; Okayama|Okayama; Kagawa|Takamatsu; Kumamoto|Kumamoto; Fukuoka|Fukuoka; Tochigi|Utsunomiya; Miyagi|Sendai; Shizuoka|Shizuoka; Hyogo|Kobe; Yamaguchi|Yamaguchi; Tokyo|Shinagawa-ku; Ishikawa|Nanao; Nara|Nara-shi; Hyogo|Amagasaki; Toyama|Toyama; Hokkaido|Sapporo; Miyagi|Tomiya; Hiroshima|Onomichi; Yamaguchi|Shimonoseki; Miyagi|Kurihara; Wakayama|Wakayama; Hiroshima|Fukuyama; Gunma|Maebashi; Ehime|Matsuyama; Nagano|Matsumoto; Fukui|Fukui-shi; Aichi|Chita; Shizuoka|Numazu; Niigata|Niigata; Mie|Tsu; Tokyo|Chofu; Ibaraki|Mito; Aichi|Anjo; Chiba|Shibayama; Tottori|Tottori; Okinawa|Naha; Hokkaido|Hakodate; Oita|Oita; Mie|Yokkaichi; Ishikawa|Kanazawa; Gifu|Gero; Chiba|Narita; Aichi|Toyohashi; Shiga|Hikone; Ibaraki|Tsukuba; Tokyo|Hino; Okinawa|Yonakuni; Nagasaki|Nagasaki; Yamaguchi|Ube; Shizuoka|Hamamatsu; Hyogo|Tatsunocho-tominaga; Miyazaki|Miyazaki; Fukushima|Fukushima; Tokyo|Hachioji; Iwate|Kuji; Hyogo|Kakogawacho-honmachi; Hiroshima|Hatsukaichi; Kochi|Kochi; Tottori|Kurayoshi; Fukuoka|Tachiarai; Saga|Tosu; Yamagata|Yamagata; Yamanashi|Minami-Alps; Saitama|Hanno; Hyogo|Akashi; Kagoshima|Kagoshima; Kanagawa|Fujisawa; Hokkaido|Nakagawa; Akita|Hanawa; Shimane|Matsue; Iwate|Noda; Hokkaido|Date; Nagasaki|Hirado; Kagoshima|Izumi; Nagasaki|Fukuecho; Fukushima|Shirakawa; Gunma|Naganohara; Hokkaido|Tomakomai; Kanagawa|Kawasaki; Fukushima|Iwashita; Chiba|Togane; Miyagi|Onagawa Cho; Hokkaido|Abashiri; Aichi|Kasugai; Tokyo|Higashimurayama; Aichi|Toyota; Saga|Takeo; Hokkaido|Muroran; Nagasaki|Shimabara; Fukuoka|Maebaru-chuo; Kochi|Sukumo"""

OBS_FOREIGN_CITIES = """United States|Los Angeles; United States|Ashburn; United States|New York City; United States|Santa Clara; United States|Boydton; United States|Mountain View; Singapore|Singapore; The Netherlands|Amsterdam; United States|Dallas; Hong Kong|Hong Kong; United States|Atlanta; Germany|Neu-Isenburg; United States|Boardman; Brazil|Sao Paulo; Germany|Falkenstein; United States|Washington; United States|Ann Arbor; United States|Council Bluffs; South Korea|Seoul; Canada|Montreal; France|Paris; United States|Quincy; Sweden|Stockholm; United States|Cupertino; United States|San Jose; Belgium|Brussels; United States|Las Vegas; China|Beijing; Netherlands|Amsterdam; United States|Hillsboro; Ireland|Dublin; United States|San Francisco; United States|DeKalb; United States|North Charleston; France|Roubaix; United Kingdom|London; Indonesia|Jakarta; United States|Hilliard; United States|Columbus; France|Lauterbourg; United States|Clifton; Russia|Moscow; United States|Springfield; United States|Social Circle; Argentina|Castelar; United States|Gallatin; United States|Fort Worth; United States|Mansfield; United States|Huntsville; United States|North Bergen; France|Saint-Denis; United States|Seattle; United States|Hanover; France|Wattrelos; United States|Wilmington; Afghanistan|Kabul; Brazil|Campinas; Oman|Muscat; Panama|Panama City; Pakistan|Karachi; Poland|Warsaw; Germany|Limburg an der Lahn; France|Strasbourg; Slovenia|Ljubljana; Brazil|Brasilia; United Arab Emirates|Dubai; United Kingdom|Harrietsham; United Kingdom|Edinburgh; United States|Altoona; India|Mumbai; Andorra|Pas de la Casa; United States|Huntingburg; The Netherlands|Groningen; Switzerland|Zurich; United States|The Dalles; Venezuela|Caracas; Taiwan|Taipei; United States|Brooklyn; Brazil|Rio de Janeiro; Brazil|Fortaleza; Brazil|Valenca; Senegal|Dakar; Bangladesh|Dhaka; Argentina|Buenos Aires; Turkey|Istanbul; Honduras|Tegucigalpa; United States|Jacksonville; United States|Baltimore; Vietnam|Hanoi; United States|Phoenix; Peru|Lima; China|Baoding; United States|Bend; Germany|Falkenstein/Vogtl.; United States|Portland; Netherlands|Groningen; United States|Buffalo; Ukraine|Kyiv; United States|Kane; Czechia|Prague; United States|Kansas City; Türkiye|Istanbul; Australia|Canberra; Finland|Helsinki; United States|Chicago; The Netherlands|Kerkrade; United Kingdom|York; Malaysia|Kuala Lumpur; United States|Oak Hill; United States|Mesa; Germany|Augsburg; Finland|Lappeenranta; Poland|Poznan; Germany|Nuremberg; United States|Secaucus; United States|Silver Spring; United States|Ogden; India|New Delhi; Saudi Arabia|Riyadh; Poland|Debica; Germany|Runkel; Brazil|Curitiba; India|Gurgaon; United States|Minnetonka; Indonesia|Trenggalek; France|Gravelines; China|Yangquan; Nepal|Tulsipur; India|Agra; Sweden|Uppsala; Hungary|Budapest; Angola|Luanda; Albania|Tirana; Indonesia|Bandung; United States|Salt Lake City; United States|Rancho Cucamonga; Germany|Berlin; Venezuela|Chacao; Argentina|Bernal Oeste; Mexico|Irapuato; Argentina|Presidencia de la Plaza; Vietnam|Son La; Dominican Republic|Concepcion de La Vega; Costa Rica|Cartago; Philippines|Irahuan; Philippines|Balagtasin; Philippines|Aurora; Dominican Republic|San Cristobal; Russia|Vladivostok; Venezuela|Maturin; Venezuela|Guasipati; Uruguay|Maldonado; Suriname|Paramaribo; Tunisia|Bizerte; Canada|Toronto; Uzbekistan|Tashkent; India|Vizianagaram; Philippines|Cavite City; Morocco|Meknes; Venezuela|Barquisimeto; Indonesia|Bekasi; Brazil|Coruja; Ukraine|Khorostkiv; Poland|Kielce; Paraguay|Fernando de la Mora; Bolivia|Cochabamba; Mexico|Tlahuac; Bangladesh|Gaurnadi; Saudi Arabia|Jeddah; Bangladesh|Gaibandha; Philippines|Pintuyan; Turkey|Adana; Turkey|Kirsehir; Jordan|Amman; Mexico|Ciudad Nezahualcoyotl; Brazil|Anapolis; Brazil|Santo Andre; Pakistan|Haripur; United States|Rochester; United States|Inglewood; Philippines|Cebu City; Slovenia|Maribor; Brazil|Ararangua; United Kingdom|Nottingham; Brazil|Porto Alegre; United States|Detroit; United States|Hicksville; United States|Waldorf; Chile|Santiago; Ireland|Clonmany; Brazil|Teresopolis; Dominican Republic|Hato Mayor; United States|Houston; Philippines|Palestina; Saint Kitts and Nevis|Newcastle; United States|Londonderry; United States|New Orleans; Russia|Kol'chugino; Argentina|Casilda; United States|Orangeburg; United States|Mobile; Ukraine|Kolodenka; Venezuela|Barinas; Kyrgyzstan|Osh; Russia|Yekaterinburg; Kazakhstan|Shchuchinsk; Canada|Winkler; United States|Lexington; Brazil|Fernandopolis; United States|Charlotte; United States|Willimantic; United States|Meridian; Algeria|M'Sila; United States|Pullman; Brazil|Brumado; Vietnam|Hai Duong; Bolivia|Achocalla; South Africa|Hazelmere; Oman|Salalah; Spain|Madrid; Brazil|Cana Brava do Norte; Ecuador|Quito; Argentina|El Galpon; Bangladesh|Natore; Pakistan|Mirpur Khas; Kuwait|Al Farwaniyah; Brazil|Uberlandia; United States|Alexandria; Argentina|Santa Fe; United Kingdom|Glasgow; Kazakhstan|Astana; Venezuela|Naguanagua; Ukraine|Sevastopol; Brazil|Sao Jose dos Campos; Botswana|Mogoditshane; Spain|Caceres; Kazakhstan|Almaty; Turkey|Asagidere; Colombia|Pereira; Argentina|Laguna Paiva; Ethiopia|Addis Ababa; Russia|Kirov; Chile|Molina; Brazil|Piracicaba; Belarus|Minsk; Bangladesh|Noakhali; Italy|Taranto; Brazil|Lauro de Freitas; United Arab Emirates|Al Fujairah City; Ivory Coast|Abidjan; Mexico|Tlaxcala; Brazil|Papuda; Algeria|Annaba; Kazakhstan|Karagandy; South Africa|Abbotsdale; Pakistan|Jauharabad; Brazil|Cachoeirinha"""

OBS_US_STATES = """California; Virginia; New York; Texas; Oregon; Georgia; Iowa; Washington; Michigan; Ohio; New Jersey; Nevada; Illinois; South Carolina; Washington, D.C.; District of Columbia; Alabama; Nebraska; New Hampshire; Maryland; Tennessee; Arizona; Delaware; Indiana; Utah; Florida; Missouri; Minnesota; Louisiana; Kentucky; North Carolina; Connecticut; Mississippi"""

OBS_FOREIGN_REGIONS = """The Netherlands|North Holland; Brazil|Sao Paulo; Germany|Hesse; Germany|Saxony; France|Ile-de-France; South Korea|Seoul; Canada|Quebec; France|Hauts-de-France; United Kingdom|England; Sweden|Stockholm; China|Beijing; Netherlands|Provincie Noord-Holland; France|Grand Est; Ireland|Leinster; Belgium|Brussels Capital; Indonesia|Jakarta; Argentina|Buenos Aires; Russia|Moscow; Brazil|Rio de Janeiro; Pakistan|Sindh; Brazil|Federal District; United Kingdom|Scotland; Afghanistan|Kabul; Brazil|Bahia; Oman|Muscat; Panama|Panama; Argentina|Santa Fe; Germany|Hessen; Belgium|Bruxelles-Capitale; United Arab Emirates|Dubai; India|Maharashtra; Germany|Bavaria; Andorra|Encamp; The Netherlands|Groningen; Switzerland|Zurich; Venezuela|Distrito Federal; Indonesia|West Java; Brazil|Ceara; Philippines|Calabarzon; Senegal|Dakar; Bangladesh|Dhaka Division; Brazil|Minas Gerais; Argentina|Buenos Aires F.D.; Turkey|Istanbul; Honduras|Francisco Morazan Department; Vietnam|Hanoi; Peru|Lima Province; China|Hebei; Netherlands|Provincie Groningen; Netherlands|Noord-Holland; Singapore|Central Singapore; Poland|Masovian Voivodeship; Ukraine|Kyiv; Czechia|Prague; Slovenia|Mestna Obcina Ljubljana; Türkiye|Istanbul; Australia|Australian Capital Territory; Finland|Uusimaa; Poland|Mazovia; The Netherlands|Limburg; Malaysia|Kuala Lumpur; Finland|South Karelia; Poland|Greater Poland; India|Delhi; Saudi Arabia|Riyadh Region; Poland|Subcarpathia; Slovenia|Ljubljana; Brazil|Parana; India|Haryana; Taiwan|Taipei; Indonesia|East Java; Taiwan|Taiwan; China|Shanxi; Nepal|Lumbini Province; India|Uttar Pradesh; Sweden|Uppsala; Hungary|Budapest; Angola|Luanda; Albania|Tirana; Germany|Berlin; Venezuela|Miranda; Mexico|Guanajuato; Argentina|Chaco; Vietnam|Son La Province; Dominican Republic|La Vega; Costa Rica|Cartago Province; Philippines|Mimaropa; Philippines|Caraga; Dominican Republic|San Cristobal; Russia|Primorye; Venezuela|Monagas; Venezuela|Bolivar; Uruguay|Maldonado; Suriname|Paramaribo District; Tunisia|Bizerte Governorate; Canada|Ontario; Uzbekistan|Tashkent; India|Andhra Pradesh; Morocco|Fes-Meknes; Venezuela|Lara; Ukraine|Ternopil; Poland|Swietokrzyskie; Paraguay|Central Department; Bolivia|Cochabamba; Mexico|Mexico City; Bangladesh|Barisal Division; Saudi Arabia|Mecca Region; Bangladesh|Rangpur Division; Philippines|Eastern Visayas; Turkey|Adana; Turkey|Kirsehir; Jordan|Amman; Mexico|Mexico; Brazil|Goias; Pakistan|Khyber Pakhtunkhwa; Philippines|Central Visayas; Slovenia|Maribor City Municipality; Brazil|Santa Catarina; Brazil|Rio Grande do Sul; Chile|Santiago Metropolitan; Ireland|Ulster; Dominican Republic|Sanchez Ramirez; Philippines|Bicol Region; Saint Kitts and Nevis|Saint James Windwa; Russia|Vladimir Oblast; Ukraine|Rivne; Venezuela|Barinas; Kyrgyzstan|Osh Region; Russia|Sverdlovsk Oblast; Kazakhstan|Aqmola; Canada|Manitoba; Algeria|M'Sila; Vietnam|Hai Duong Province; Bolivia|La Paz Department; South Africa|KwaZulu-Natal; Oman|Dhofar; Spain|Madrid; Brazil|Mato Grosso; Ecuador|Pichincha; Argentina|Salta; Bangladesh|Rajshahi Division; Kuwait|Al Farwaniyah; Kazakhstan|Astana; Venezuela|Carabobo; Ukraine|Sevastopol City; Botswana|Kweneng; Spain|Extremadura; Kazakhstan|Almaty; Turkey|Bartin; Colombia|Risaralda Department; Ethiopia|Addis Ababa; Russia|Kirov Oblast; Chile|Maule Region; Belarus|Minsk City; Bangladesh|Chittagong; Italy|Apulia; United Arab Emirates|Fujairah; Ivory Coast|Abidjan; Mexico|Tlaxcala; Algeria|Annaba; Kazakhstan|Karaganda; South Africa|Western Cape; Pakistan|Punjab; Brazil|Pernambuco"""

FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("  OK   " if cond else "  FAIL ") + name + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def items(s: str) -> list[str]:
    return [x.strip() for x in s.split("; ") if x.strip()]


ASCII = re.compile(r"[A-Za-z]")


def no_ascii(s: str) -> bool:
    return not ASCII.search(s.replace("D.C.", ""))   # 「ワシントンD.C.」だけは記号を許す


def kana_paren(label: str, en: str) -> bool:
    """「日本語（English）」の形で、日本語側に英字が無く、括弧内が元の英語であること。"""
    m = re.fullmatch(r"(.+?)（(.+)）", label)
    return bool(m) and no_ascii(m.group(1)) and m.group(2) == en


print("== 1. 国名(本番で見つかった75種類)")
bad = []
for c in items(OBS_COUNTRIES):
    lab, ja = g.country_label(c), g.country_ja(c)
    canon = g.canonical_country(c)
    ok = (lab == "日本") if canon == "Japan" else kana_paren(lab, canon)
    if not ok or not no_ascii(ja):
        bad.append(f"{c}→{lab}")
check("すべて対応表にあり、日本=「日本」/外国=「カタカナ（英文）」", not bad, "; ".join(bad[:8]))
check("表記ゆれを1つにまとめる(The Netherlands=Netherlands・Türkiye=Turkey)",
      g.canonical_country("The Netherlands") == g.canonical_country("Netherlands") == "Netherlands"
      and g.canonical_country("Türkiye") == g.canonical_country("Turkey") == "Turkey")
check("国のラベルも表記ゆれで同じになる", g.country_label("The Netherlands") == g.country_label("Netherlands") == "オランダ（Netherlands）")

print("== 2. 都道府県")
check("47都道府県すべてが日本語のみ(都/道/府/県で終わる)",
      all(no_ascii(g.region_label("Japan", p)) and g.region_label("Japan", p)[-1] in "都道府県" for p in items(ALL_PREFS)) and len(items(ALL_PREFS)) == 47)
check("本番で見つかった45種類が日本語になる", all(no_ascii(g.region_label("Japan", p)) for p in items(OBS_PREFS)))
check("都道府県名の付属語(Tokyo Metropolis / Osaka Prefecture / Kyōto)でも引ける",
      g.region_label("Japan", "Tokyo Metropolis") == "東京都" and g.region_label("Japan", "Osaka Prefecture") == "大阪府"
      and g.region_label("Japan", "Kyōto") == "京都府")

print("== 3. 日本の市区町村(本番で見つかった101種類)")
bad = [x for x in items(OBS_JP_CITIES) if not no_ascii(g.city_label("Japan", x.split("|")[0], x.split("|")[1]))]
check("すべて日本語のみで表示される", not bad, "; ".join(bad[:8]))

print("== 4. 外国の都市(本番で見つかった257種類)")
bad = []
for x in items(OBS_FOREIGN_CITIES):
    country, city = x.split("|")
    if not kana_paren(g.city_label(country, "", city), city):
        bad.append(x)
check("すべて「カタカナ（英文）」になる", not bad, "; ".join(bad[:8]))

print("== 5. 米国の州(本番で見つかった33種類)")
bad = [s for s in items(OBS_US_STATES) if not kana_paren(g.region_label("United States", s), s)]
check("すべて「〇〇州（英文）」になる", not bad, "; ".join(bad[:8]))

print("== 5b. 外国(米国以外)の地域名(本番で見つかった164種類)")
bad = []
for x in items(OBS_FOREIGN_REGIONS):
    country, region = x.split("|")
    if not kana_paren(g.region_label(country, region), region):
        bad.append(x)
check("すべて「カタカナ・日本語（英文）」になる", not bad, "; ".join(bad[:8]))

print("== 6. 代表的な表示例")
cases = [
    (g.country_label("Japan"), "日本"), (g.country_label("United States"), "アメリカ合衆国（United States）"),
    (g.region_label("Japan", "Tokyo"), "東京都"), (g.city_label("Japan", "Tokyo", "Tokyo"), "東京"),
    (g.city_label("Japan", "Osaka", "Osaka"), "大阪市"), (g.city_label("Japan", "Tokyo", "Shinagawa-ku"), "品川区"),
    (g.region_label("United States", "California"), "カリフォルニア州（California）"),
    (g.city_label("United States", "California", "Los Angeles"), "ロサンゼルス（Los Angeles）"),
    (g.city_label("China", "", "Beijing"), "北京（Beijing）"), (g.country_label("China"), "中国（China）"),
    (g.city_label("South Korea", "", "Seoul"), "ソウル（Seoul）"), (g.region_label("Netherlands", "North Holland"), "ノールトホラント州（North Holland）"),
    (g.region_label("The Netherlands", "Provincie Noord-Holland"), "ノールトホラント州（Provincie Noord-Holland）"), (g.city_label("Türkiye", "", "Istanbul"), "イスタンブール（Istanbul）"),
]
for got, want in cases:
    check(f"{want}", got == want, f"実際={got}")

print("== 7. 対応表に無い地名は英語のまま(誤った音訳を出さない)")
check("未知の市は英語のまま", g.city_label("Japan", "Tokyo", "Xyzzyville") == "Xyzzyville" and g.city_label("France", "", "Zzzville") == "Zzzville")
check("未知の国は英語のまま", g.country_label("Atlantis") == "Atlantis" and g.country_ja("Atlantis") == "Atlantis")
check("未知の州・地域は英語のまま", g.region_label("United States", "Nowhere") == "Nowhere" and g.region_label("Canada", "Nowhereland") == "Nowhereland")
check("空の値は空", g.country_label("") == "" and g.region_label("Japan", "") == "" and g.city_label("Japan", "", "") == "" and g.canonical_country(None) == "")

print()
if FAILS:
    print(f"❌ 失敗 {len(FAILS)} 件: " + ", ".join(FAILS))
    raise SystemExit(1)
print("✅ すべて成功")
