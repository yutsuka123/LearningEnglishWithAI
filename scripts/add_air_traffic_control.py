# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""航空管制(ATC)テーマの語彙+フレーズを新設、authored by Claude(2026-08-25・
ユーザー要望「航空管制の略語や用語、管制塔・飛行場などの機器の略語、誘導
装置、管制とパイロットの交信、航空の気象用語」)。

既存の「航空・宇宙」(128語)は機体工学・宇宙飛行が中心、「航空」(35語)は
旅客/搭乗手続き中心、フレーズ「航空・機内」(23件)は一般的な機内アナウンス
中心で、いずれも**管制官とパイロットの無線交信で実際に使われる標準用語
(ICAO/FAAフレーズ)そのもの**は手薄だったため、新ドメイン「航空管制」・
新シーン「航空管制・無線交信」として新設する。

出典(裏取り): FAA Pilot/Controller Glossary、ICAO Doc 4444(PANS-ATM)、
ICAO Doc 9432(Radiotelephony Manual)、FAA Aeronautical Information Manual
(AIM)第4章に準拠する標準略語・標準フレーズのみを採用。方言的/非標準の
言い回しは避けた。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` /
`phrases` tables.

Run:  python scripts/add_air_traffic_control.py
仕上げ: 投入後に `python scripts/relevel.py` と
        `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

ATC = "航空管制"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 略語(通信・気象情報) ---
    ("ATIS", "自動飛行場情報放送(Automatic Terminal Information Service、空港の気象・使用滑走路等の情報を継続的に自動放送するもの、到着・出発機の両方が対象)", "名詞", "Before contacting the tower, the pilot listened to the ATIS broadcast for the current wind and runway in use.", ATC, "850"),
    ("METAR", "定時飛行場実況気象通報式(空港の実測気象を定時報告する国際標準形式)", "名詞", "The dispatcher checked the latest METAR before filing the flight plan.", ATC, "850"),
    ("TAF", "飛行場予報(Terminal Aerodrome Forecast、空港周辺の気象予報)", "名詞", "The TAF predicted deteriorating visibility by early evening.", ATC, "850"),
    ("NOTAM", "航空情報通報(Notice to Airmen、滑走路閉鎖等の一時的な運用情報)", "名詞", "A NOTAM warned pilots that the main runway would be closed for repaving.", ATC, "850"),
    ("SIGMET", "重要気象情報(Significant Meteorological Information、悪天候に関する広域警報)", "名詞", "A SIGMET was issued for severe turbulence along the flight route.", ATC, "900"),
    ("AIRMET", "航空気象情報(Airmen's Meteorological Information、SIGMETより軽度の悪天候情報)", "名詞", "The AIRMET advised of moderate icing above ten thousand feet.", ATC, "900"),
    ("PIREP", "パイロット報告(Pilot Report、飛行中の実際の気象状況の報告)", "名詞", "Another crew's PIREP confirmed light turbulence at that altitude.", ATC, "850"),
    ("VOLMET", "航空機向け気象放送(飛行中の航空機に向けた継続的な気象情報の無線放送)", "名詞", "Over the ocean, the crew tuned in to VOLMET for weather updates.", ATC, "900"),
    ("squawk code", "スコーク・コード(トランスポンダーに設定する4桁の識別コード)", "名詞", "The controller assigned a new squawk code after the handoff.", ATC, "800"),
    ("wilco", "了解・その通り実施します(will complyの略、指示を実行する意思を示す標準応答)", "感嘆詞", "\"Descend and maintain flight level two eight zero.\" \"Wilco.\"", ATC, "800"),
    ("readback", "復唱(管制官の指示を復唱してパイロットが確認すること)", "名詞", "The controller listened carefully to the pilot's readback to catch any errors.", ATC, "800"),
    ("say again", "もう一度言ってください(無線交信で聞き取れなかった時の標準表現)", "連語", "\"Say again your last transmission, it was cut off.\"", ATC, "700"),
    ("unable", "対応できません(指示に従えない時の標準拒否表現)", "形容詞", "\"Unable, we need a higher altitude due to weather.\"", ATC, "750"),
    ("affirmative", "はい・その通りです(無線交信での標準的な「はい」)", "副詞", "\"Are you ready to copy the clearance?\" \"Affirmative.\"", ATC, "700"),
    ("negative", "いいえ(無線交信での標準的な「いいえ」)", "副詞", "\"Negative, we do not have the field in sight yet.\"", ATC, "700"),
    ("expedite", "急いで実施する(高度変更や滑走路横断を速やかに行うようパイロットに求める指示)", "動詞", "The controller asked the pilot to expedite the climb to clear following traffic.", ATC, "850"),
    ("mayday", "メーデー(生命に関わる緊急事態を示す国際的な遭難信号)", "感嘆詞", "\"Mayday, mayday, mayday, we have an engine fire.\"", ATC, "800"),
    ("pan-pan", "パンパン(生命の危険はないが緊急対応が必要な事態を示す緊急信号)", "感嘆詞", "\"Pan-pan, pan-pan, we have a medical emergency on board.\"", ATC, "850"),
    # --- 誘導装置・航法援助施設 ---
    ("ILS", "計器着陸装置(Instrument Landing System、視界不良時も精密進入を可能にする地上装置)", "名詞", "The aircraft flew an ILS approach through low cloud into the airport.", ATC, "850"),
    ("localizer", "ローカライザー(ILSの一部で滑走路中心線への左右方向のずれを示す電波)", "名詞", "The autopilot captured the localizer and began tracking the runway centerline.", ATC, "900"),
    ("glideslope", "グライドスロープ(ILSの一部で滑走路への上下方向の降下角を示す電波)", "名詞", "The pilot watched the needle to stay on the glideslope during the approach.", ATC, "900"),
    ("VOR", "超短波全方向式無線標識(VHF Omnidirectional Range、方位情報を発信する航法援助施設)", "名詞", "The aircraft tracked a radial inbound to the VOR.", ATC, "850"),
    ("NDB", "無指向性無線標識(Non-Directional Beacon、方位を持たない電波を発信する古典的な航法援助施設)", "名詞", "Older aircraft still use an NDB approach at some smaller airports.", ATC, "900"),
    ("DME", "距離測定装置(Distance Measuring Equipment、地上局までの斜め距離を測定する装置)", "名詞", "The DME readout showed twelve miles to the airport.", ATC, "850"),
    ("TACAN", "戦術航法装置(Tactical Air Navigation、軍用機向けの方位・距離航法援助施設)", "名詞", "The military aircraft navigated using TACAN instead of a civilian VOR.", ATC, "950"),
    ("RNAV", "広域航法(Area Navigation、地上局に頼らずGPS等で自由な経路を飛行する方式)", "名詞", "The flight followed an RNAV route directly to the destination.", ATC, "900"),
    ("RNP", "航法性能要件(Required Navigation Performance、経路精度をGPS等で自己監視しながら飛行する航法基準)", "名詞", "The approach required RNP capability that the older aircraft did not have.", ATC, "950"),
    ("FMS", "飛行管理装置(Flight Management System、経路・性能を統合管理するコンピューターシステム)", "名詞", "The pilot programmed the arrival procedure into the FMS.", ATC, "900"),
    ("waypoint", "ウェイポイント(飛行経路上に設定された通過地点)", "名詞", "The next waypoint on the route was fifty miles ahead.", ATC, "800"),
    ("fix (navigation)", "フィックス(航法上の特定地点、交差点や座標で定義される)", "名詞", "The controller cleared the aircraft direct to the next fix.", ATC, "850"),
    ("airway", "航空路(定められた幅と高度帯を持つ空の通り道)", "名詞", "The flight climbed to join the airway toward the coast.", ATC, "750"),
    ("holding fix", "待機フィックス(待機飛行の基準となる地点)", "名詞", "The aircraft circled the holding fix while waiting for a landing slot.", ATC, "850"),
    ("SID", "標準計器出発方式(Standard Instrument Departure、あらかじめ定められた出発経路)", "名詞", "The aircraft departed following the published SID.", ATC, "900"),
    ("STAR", "標準到着経路(Standard Terminal Arrival Route、あらかじめ定められた到着経路)", "名詞", "Air traffic control cleared the flight to descend via the STAR.", ATC, "900"),
    ("instrument approach procedure", "計器進入方式(視界不良時に計器のみで滑走路へ進入する定められた手順)", "名詞", "The crew briefed the instrument approach procedure before descending into cloud.", ATC, "900"),
    ("outer marker", "アウターマーカー(ILS進入経路上、滑走路から離れた位置に設置される電波標識)", "名詞", "The aircraft crossed the outer marker at the published altitude.", ATC, "900"),
    ("GPWS", "対地接近警報装置(Ground Proximity Warning System、地面への異常接近を検知し警告する装置)", "名詞", "The GPWS sounded a warning as the aircraft descended too quickly.", ATC, "900"),
    # --- 管制塔・飛行場の機器 ---
    ("PAPI", "進入角指示灯(Precision Approach Path Indicator、色の見え方で進入角の高低を示す灯火)", "名詞", "The pilot used the PAPI lights to judge the correct approach angle.", ATC, "850"),
    ("approach lighting system", "進入灯システム(滑走路手前に並ぶ、着陸進入を導く一連の灯火)", "名詞", "The approach lighting system guided the aircraft through the last mile of fog.", ATC, "850"),
    ("runway edge lights", "滑走路灯(滑走路の両端に沿って設置される白色の灯火)", "名詞", "The runway edge lights were clearly visible even in the rain.", ATC, "700"),
    ("threshold lights", "滑走路末端灯(滑走路の始点を示す緑色の灯火)", "名詞", "The threshold lights marked exactly where the runway began.", ATC, "750"),
    ("windsock", "吹き流し(風向・風速を目視で示す円錐形の布製の装置)", "名詞", "The windsock at the end of the runway was standing almost straight out.", ATC, "600"),
    ("airport beacon", "飛行場灯台(空港の位置を夜間に示す回転式の灯火)", "名詞", "Pilots at night can spot the airport beacon from many miles away.", ATC, "700"),
    ("surface movement radar", "地上移動レーダー(視界不良時に空港内の航空機・車両の動きを監視するレーダー)", "名詞", "Ground control used the surface movement radar to track aircraft in thick fog.", ATC, "900"),
    ("wind shear detection system", "ウィンドシア検知装置(急激な風向・風速の変化を検知し警報を出す空港設備)", "名詞", "The wind shear detection system triggered an alert during the thunderstorm.", ATC, "900"),
    ("jet blast deflector", "ジェットブラスト偏向板(エンジン排気を上方へそらす防護設備)", "名詞", "The jet blast deflector protected the fence line from the engine exhaust.", ATC, "900"),
    ("arresting gear", "着艦拘束装置(空母や緊急着陸帯で機体を短距離で停止させる装置)", "名詞", "The arresting gear caught the tailhook and brought the fighter to a stop.", ATC, "950"),
    # --- 管制とパイロットの交信用語 ---
    ("line up and wait", "滑走路に入って待機(離陸許可が出るまで滑走路上で待つよう指示する標準フレーズ)", "連語", "\"Line up and wait, runway two seven.\"", ATC, "850"),
    ("hold short", "手前で停止・待機(滑走路や交差点の手前で止まるよう指示する標準フレーズ)", "連語", "\"Hold short of runway one eight, traffic on final.\"", ATC, "800"),
    ("taxi clearance", "地上走行許可(誘導路上を移動する許可)", "名詞", "The pilot read back the taxi clearance before pushing back from the gate.", ATC, "800"),
    ("departure clearance", "出発許可(離陸後の経路・高度を含む管制上の許可)", "名詞", "The first officer copied the departure clearance while still at the gate.", ATC, "800"),
    ("radar contact", "レーダー識別(管制官がレーダー上で機体を識別したことを伝える標準フレーズ)", "名詞", "\"Radar contact, climb and maintain flight level three one zero.\"", ATC, "850"),
    ("traffic in sight", "他機を視認(付近の他機を目視で確認したことを伝える標準フレーズ)", "連語", "\"Traffic in sight, we'll maintain visual separation.\"", ATC, "800"),
    ("altimeter setting", "高度計規正値(気圧高度計を正しい値に合わせるための気圧設定値)", "名詞", "The controller passed the current altimeter setting before the approach.", ATC, "800"),
    ("descend and maintain", "降下して維持せよ(指定高度まで降下し、それを維持するよう求める標準指示)", "連語", "\"Descend and maintain eight thousand feet.\"", ATC, "800"),
    ("climb and maintain", "上昇して維持せよ(指定高度まで上昇し、それを維持するよう求める標準指示)", "連語", "\"Climb and maintain flight level two four zero.\"", ATC, "800"),
    ("cleared to land", "着陸許可(滑走路への着陸を許可する標準フレーズ)", "連語", "The tower gave the flight clearance to land on runway three three.", ATC, "750"),
    ("handoff", "引き継ぎ(管制セクター間で機体の管制業務を移管すること)", "名詞", "The controller performed a handoff to the next sector before the boundary.", ATC, "850"),
    ("frequency change", "周波数変更(交信する管制周波数を切り替えること)", "名詞", "\"Contact departure, frequency change approved.\"", ATC, "750"),
    ("position report", "位置通報(洋上等レーダーの届かない区域で定期的に行う位置の報告)", "名詞", "The crew sent a position report every ten degrees of longitude over the ocean.", ATC, "850"),
    ("flight following", "飛行追従(有視界飛行中に管制からレーダーによる交通情報提供を受けるサービス)", "名詞", "The pilot requested flight following from approach control.", ATC, "850"),
    ("separation minima", "管制間隔の最低基準(航空機同士に確保しなければならない最小の距離・高度差)", "名詞", "Controllers must keep aircraft outside the required separation minima.", ATC, "950"),
    ("wake turbulence category", "後方乱気流区分(機体の重量に基づく後方乱気流の強さの分類)", "名詞", "A lighter aircraft must wait longer behind a heavier wake turbulence category.", ATC, "950"),
    ("see and avoid", "視認・回避の原則(有視界飛行において目視で他機を発見し衝突を避ける基本原則)", "名詞", "In visual conditions, pilots rely on see and avoid to stay clear of other traffic.", ATC, "900"),
    ("non-towered airport", "管制塔のない空港(常時運用の管制塔を持たない飛行場)", "名詞", "Pilots announce their position on a common frequency at a non-towered airport.", ATC, "800"),
    ("pattern altitude", "場周高度(空港周辺の標準的な飛行経路(場周経路)を飛ぶ際の高度)", "名詞", "The trainee leveled off at pattern altitude before turning downwind.", ATC, "800"),
    ("downwind leg", "ダウンウィンド・レグ(滑走路と平行に、着陸方向と逆向きに飛ぶ場周経路の一区間)", "名詞", "The aircraft flew the downwind leg parallel to the runway.", ATC, "800"),
    ("base leg", "ベース・レグ(滑走路に対しほぼ直角に、最終進入へ向けて飛ぶ場周経路の一区間)", "名詞", "Turning onto the base leg, the pilot began configuring for landing.", ATC, "800"),
    ("final approach", "最終進入(場周経路の最後、滑走路へ真っ直ぐ向かう区間)", "名詞", "The aircraft was cleared to land while still on final approach.", ATC, "700"),
    # --- 航空気象用語 ---
    ("ceiling (aviation)", "シーリング(地表から最も低い雲層の底までの高さ)", "名詞", "The ceiling dropped to five hundred feet as the storm approached.", ATC, "800"),
    ("broken (cloud cover)", "ブロークン(空の5〜7割が雲に覆われている状態を示す気象用語)", "名詞", "The METAR reported broken clouds at three thousand feet.", ATC, "850"),
    ("overcast (cloud cover)", "オーバーキャスト(空全体が雲に覆われている状態を示す気象用語)", "名詞", "It was overcast all day, with the sun never breaking through.", ATC, "750"),
    ("scattered clouds", "スキャッタード(空の3〜4割(8分の3〜4)が雲に覆われている状態を示す気象用語)", "名詞", "Scattered clouds at four thousand feet posed no problem for the flight.", ATC, "800"),
    ("dew point", "露点(空気が冷やされて水蒸気が凝結し始める温度)", "名詞", "A small gap between temperature and dew point suggested fog was likely.", ATC, "750"),
    ("wind shear", "ウィンドシア(短い距離・時間で風向・風速が急激に変化する現象)", "名詞", "The crew went around after encountering wind shear on short final.", ATC, "850"),
    ("microburst", "マイクロバースト(積乱雲から吹き下ろす、局地的で強力な下降気流)", "名詞", "A microburst near the airport forced several flights to divert.", ATC, "900"),
    ("low-level wind shear", "低高度ウィンドシア(離着陸に直接影響する、地表付近で発生するウィンドシア)", "名詞", "The tower issued a low-level wind shear alert to all inbound traffic.", ATC, "900"),
    ("icing conditions", "着氷条件(機体表面に氷が付着しやすい気象条件)", "名詞", "The forecast warned of icing conditions above eight thousand feet.", ATC, "800"),
    ("freezing rain", "着氷性の雨(氷点下の地表付近で凍結しながら降る雨、強い着氷を引き起こす)", "名詞", "Freezing rain coated the runway and delayed all departures.", ATC, "800"),
    ("visibility (aviation)", "視程(水平方向にどれだけ遠くまで見通せるかを示す気象要素)", "名詞", "Visibility improved to six miles as the fog began to lift.", ATC, "700"),
    ("crosswind component", "横風成分(滑走路の方向に対して直角方向にかかる風の強さ)", "名詞", "The crosswind component exceeded the aircraft's limit for landing.", ATC, "900"),
    ("tailwind component", "追い風成分(滑走路の方向に対して背後からかかる風の強さ)", "名詞", "A strong tailwind component would have made the landing distance too long.", ATC, "900"),
    ("density altitude", "密度高度(気温・気圧を考慮した、大気密度に基づく実質的な高度)", "名詞", "High density altitude on the hot afternoon reduced the aircraft's climb performance.", ATC, "900"),
    ("thunderstorm cell", "雷雲セル(積乱雲の中で独立して発達する対流の単位)", "名詞", "The pilot requested a deviation to avoid a large thunderstorm cell.", ATC, "800"),
    ("gust front", "ガストフロント(発達した雷雲から吹き出す冷たい下降気流の先端)", "名詞", "A gust front ahead of the storm caused a sudden wind shift on the field.", ATC, "900"),
    # --- 追加: 飛行方式・空域・管制機関の略語 ---
    ("IFR", "計器飛行方式(Instrument Flight Rules、計器のみに頼って飛行する方式)", "名詞", "The flight was conducted under IFR due to low cloud cover.", ATC, "750"),
    ("VFR", "有視界飛行方式(Visual Flight Rules、目視で地表や他機を確認しながら飛行する方式)", "名詞", "Student pilots typically begin training under VFR.", ATC, "750"),
    ("AGL", "対地高度(Above Ground Level、地表面からの高さを示す高度表現)", "名詞", "The cloud base was reported at two thousand feet AGL.", ATC, "800"),
    ("QNH", "QNH(海面気圧に基づく高度計規正値、空港標高を示すように設定する)", "名詞", "The pilot set QNH to read the correct field elevation on landing.", ATC, "850"),
    ("QFE", "QFE(飛行場気圧に基づく高度計規正値、着陸すると高度計がゼロを示すように設定する)", "名詞", "Some military airfields still prefer pilots to use QFE rather than QNH.", ATC, "900"),
    ("RVR", "滑走路視距離(Runway Visual Range、滑走路上でどれだけ遠くまで視認できるかを示す計器測定値)", "名詞", "Landing was delayed until the RVR improved above the required minimum.", ATC, "900"),
    ("TCAS", "空中衝突防止装置(Traffic Collision Avoidance System、他機との衝突の恐れを検知し回避指示を出す機上装置)", "名詞", "The TCAS issued a climb instruction to avoid the converging traffic.", ATC, "900"),
    ("ADS-B", "放送型自動従属監視(Automatic Dependent Surveillance-Broadcast、機体のGPS位置情報を自動送信する監視技術)", "名詞", "ADS-B lets controllers track aircraft position more precisely than older radar.", ATC, "900"),
    ("ASR", "空港監視レーダー(Airport Surveillance Radar、空港周辺の航空機の位置を監視するレーダー)", "名詞", "Approach controllers used the ASR to sequence arriving traffic.", ATC, "900"),
    ("SSR", "二次監視レーダー(Secondary Surveillance Radar、トランスポンダーからの応答で機体を識別するレーダー)", "名詞", "The SSR displayed each aircraft's callsign and altitude on the scope.", ATC, "900"),
    ("MDA", "最低降下高度(Minimum Descent Altitude、精密でない進入方式で降下できる最低の高度)", "名詞", "The aircraft leveled off at the MDA and continued looking for the runway.", ATC, "950"),
    ("decision height", "デシジョンハイト(精密進入において着陸を続けるか復行するかを判断すべき高さ)", "名詞", "At decision height, the crew had the runway in sight and continued the landing.", ATC, "950"),
    ("decision altitude", "デシジョンアルティテュード(精密進入において着陸を続けるか復行するかを判断すべき高度、海面基準)", "名詞", "The approach chart listed a decision altitude of eight hundred feet.", ATC, "950"),
    ("IAF", "進入開始点(Initial Approach Fix、計器進入方式を開始する地点)", "名詞", "The aircraft was cleared direct to the IAF for the approach.", ATC, "900"),
    ("FAF", "最終進入点(Final Approach Fix、最終進入区間の始点となる地点)", "名詞", "Gear and flaps were configured before crossing the FAF.", ATC, "900"),
    ("missed approach point", "進入復行点(その地点を過ぎても滑走路が見えなければ復行しなければならない地点)", "名詞", "The crew initiated the go-around exactly at the missed approach point.", ATC, "900"),
    ("TRACON", "ターミナルレーダー進入管制所(Terminal Radar Approach Control、空港周辺の到着・出発機を管制する施設)", "名詞", "The flight was handed off to TRACON for the arrival sequence.", ATC, "900"),
    ("ARTCC", "航空路交通管制センター(Air Route Traffic Control Center、広域の巡航中の交通を管制する施設)", "名詞", "The high-altitude portion of the route was controlled by ARTCC.", ATC, "900"),
    ("CTAF", "共通交通情報周波数(Common Traffic Advisory Frequency、管制塔のない空港で使う共通の通報用周波数)", "名詞", "The pilot announced position on the CTAF before entering the pattern.", ATC, "900"),
    ("UNICOM", "ユニコム(管制塔のない小規模飛行場で使われる共通通信・情報提供の周波数)", "名詞", "The airport had no tower, so pilots used UNICOM to coordinate.", ATC, "900"),
    ("FSS", "飛行援助センター(Flight Service Station、飛行計画の受付や気象情報の提供を行う施設)", "名詞", "The pilot called the FSS to file a VFR flight plan.", ATC, "900"),
    ("FBO", "固定拠点事業者(Fixed-Base Operator、給油や駐機など空港での地上支援サービスを行う事業者)", "名詞", "The FBO arranged fuel and a rental car for the crew.", ATC, "850"),
    ("ELT", "緊急用位置指示送信機(Emergency Locator Transmitter、墜落等の衝撃で自動的に遭難信号を発信する装置)", "名詞", "The ELT activated automatically on impact and alerted search and rescue.", ATC, "900"),
    ("CAVOK", "キャブオーケー(Ceiling And Visibility OK、雲・視程・降水いずれも良好であることを一語で示す気象通報用語)", "名詞", "The METAR simply read CAVOK, so no weather delays were expected.", ATC, "900"),
    ("flight plan", "飛行計画(経路・高度・所要時間・搭載燃料などを記載し関係機関へ提出する計画書)", "名詞", "The dispatcher filed the flight plan an hour before departure.", ATC, "700"),
    ("controlled airspace", "管制空域(管制業務が提供される空域)", "名詞", "Entering controlled airspace requires a clearance from air traffic control.", ATC, "850"),
    ("restricted airspace", "制限空域(軍事訓練等のため飛行が制限される空域)", "名詞", "The route was adjusted to avoid a restricted airspace over the training range.", ATC, "850"),
    ("traffic pattern", "場周経路(空港周辺で離着陸機が飛ぶ標準的な長方形の経路)", "名詞", "New students practice takeoffs and landings in the traffic pattern.", ATC, "750"),
    ("upwind leg", "アップウィンド・レグ(離陸後、滑走路の延長線上を飛ぶ場周経路の一区間)", "名詞", "The aircraft climbed straight out on the upwind leg before turning crosswind.", ATC, "850"),
    ("crosswind leg", "クロスウィンド・レグ(離陸後、滑走路に対しほぼ直角に旋回して飛ぶ場周経路の一区間)", "名詞", "The pilot turned onto the crosswind leg at pattern altitude.", ATC, "850"),
    ("squawk", "スコークする(指定されたトランスポンダー・コードを設定する)", "動詞", "\"Squawk one two zero zero and remain this frequency.\"", ATC, "800"),
    # --- 無線音声符号(ICAO/NATOフォネティックコード、Annex 10準拠の正式綴り) ---
    ("Alfa (phonetic alphabet)", "アルファ(音声符号のA。ICAO正式綴りは'Alpha'ではなく'Alfa')", "名詞", "The registration ended in Alfa, so the controller read it back clearly.", ATC, "650"),
    ("Bravo (phonetic alphabet)", "ブラボー(音声符号のB)", "名詞", "\"Taxi to gate Bravo one two.\"", ATC, "650"),
    ("Charlie (phonetic alphabet)", "チャーリー(音声符号のC。ATISの識別に使われることも多い)", "名詞", "\"We have information Charlie.\"", ATC, "650"),
    ("Delta (phonetic alphabet)", "デルタ(音声符号のD)", "名詞", "\"Taxi via taxiway Delta to the runway.\"", ATC, "650"),
    ("Echo (phonetic alphabet)", "エコー(音声符号のE)", "名詞", "\"Hold short of taxiway Echo.\"", ATC, "650"),
    ("Foxtrot (phonetic alphabet)", "フォックストロット(音声符号のF)", "名詞", "\"Contact ground on frequency Foxtrot.\"", ATC, "650"),
    ("Golf (phonetic alphabet)", "ゴルフ(音声符号のG)", "名詞", "\"Park at stand Golf seven.\"", ATC, "650"),
    ("Hotel (phonetic alphabet)", "ホテル(音声符号のH)", "名詞", "\"Cross runway one eight at taxiway Hotel.\"", ATC, "650"),
    ("India (phonetic alphabet)", "インディア(音声符号のI)", "名詞", "\"Report crossing waypoint India.\"", ATC, "650"),
    ("Juliett (phonetic alphabet)", "ジュリエット(音声符号のJ。ICAO正式綴りは'Juliet'ではなく't'が2つの'Juliett')", "名詞", "\"Hold at intersection Juliett.\"", ATC, "650"),
    ("Kilo (phonetic alphabet)", "キロ(音声符号のK)", "名詞", "\"Squawk code four five Kilo, disregard, say again the digits.\"", ATC, "650"),
    ("Lima (phonetic alphabet)", "リマ(音声符号のL)", "名詞", "\"Taxiway Lima is closed for maintenance.\"", ATC, "650"),
    ("Mike (phonetic alphabet)", "マイク(音声符号のM)", "名詞", "\"Runway two two Mike is the shorter parallel runway.\"", ATC, "650"),
    ("November (phonetic alphabet)", "ノベンバー(音声符号のN。米国籍機の登録記号はNから始まる)", "名詞", "US-registered aircraft callsigns begin with November, as in \"November one two three Alfa Bravo.\"", ATC, "650"),
    ("Oscar (phonetic alphabet)", "オスカー(音声符号のO)", "名詞", "\"Hold short of runway two seven at Oscar.\"", ATC, "650"),
    ("Papa (phonetic alphabet)", "パパ(音声符号のP)", "名詞", "\"Contact the tower on frequency Papa.\"", ATC, "650"),
    ("Quebec (phonetic alphabet)", "ケベック(音声符号のQ)", "名詞", "\"Say again, was that gate Quebec or Golf?\"", ATC, "650"),
    ("Romeo (phonetic alphabet)", "ロメオ(音声符号のR)", "名詞", "\"Cleared to land, runway two seven, wind report on Romeo.\"", ATC, "650"),
    ("Sierra (phonetic alphabet)", "シエラ(音声符号のS)", "名詞", "\"Taxi to stand Sierra four via alpha.\"", ATC, "650"),
    ("Tango (phonetic alphabet)", "タンゴ(音声符号のT)", "名詞", "\"Hold short of taxiway Tango for crossing traffic.\"", ATC, "650"),
    ("Uniform (phonetic alphabet)", "ユニフォーム(音声符号のU)", "名詞", "\"Report over waypoint Uniform.\"", ATC, "650"),
    ("Victor (phonetic alphabet)", "ビクター(音声符号のV)", "名詞", "\"Follow the low-altitude airway Victor two three.\"", ATC, "650"),
    ("Whiskey (phonetic alphabet)", "ウィスキー(音声符号のW)", "名詞", "\"Contact approach on frequency Whiskey.\"", ATC, "650"),
    ("X-ray (phonetic alphabet)", "エックスレイ(音声符号のX)", "名詞", "\"Hold at spot X-ray until further instructions.\"", ATC, "650"),
    ("Yankee (phonetic alphabet)", "ヤンキー(音声符号のY)", "名詞", "\"Taxi to the ramp via taxiway Yankee.\"", ATC, "650"),
    ("Zulu (phonetic alphabet)", "ズールー(音声符号のZ。'Zulu time'はUTC(協定世界時)を表す慣用表現でもある)", "名詞", "Flight plans list departure times in Zulu to avoid confusion between time zones.", ATC, "700"),
]


PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "航空管制・無線交信": [
        # --- 出発準備・地上走行 ---
        ("Ground, request IFR clearance to Denver.", "グラウンド、デンバーまでの計器飛行方式の許可を要求します。"),
        ("Cleared to Denver as filed, climb and maintain five thousand, expect one two thousand ten minutes after departure.", "デンバーまで申請通り許可、5,000フィートまで上昇、離陸10分後に12,000フィートを予期してください。"),
        ("Readback correct, contact ground point niner when ready to taxi.", "復唱正確、地上走行の準備ができたらグラウンド118.9で連絡してください。"),
        ("Ground, request pushback and start.", "グラウンド、プッシュバックと始動を要求します。"),
        ("Pushback and start approved, expect a ten-minute delay.", "プッシュバックと始動を承認、10分の遅延を見込んでください。"),
        ("Taxi to runway two seven via taxiway alpha, hold short of runway one eight.", "誘導路アルファ経由で滑走路27へ地上走行、滑走路18の手前で待機してください。"),
        ("Taxi to runway two seven via alpha, hold short of one eight, readback.", "誘導路アルファ経由27へ地上走行、18手前で待機、復唱します。"),
        ("Continue taxiing, traffic is a company aircraft crossing ahead.", "地上走行を継続してください、前方を横断するのは自社機です。"),
        ("Give way to the aircraft on your right.", "右側の機体に進路を譲ってください。"),
        ("Hold short of runway two two for landing traffic.", "着陸機のため滑走路22の手前で待機してください。"),
        ("Holding short of two two.", "22の手前で待機中です。"),
        ("Cross runway one eight, without delay.", "滑走路18を速やかに横断してください。"),
        ("Contact tower now on one one eight point three.", "直ちにタワー118.3へ連絡してください。"),
        ("Tower, holding short of runway two seven, ready for departure.", "タワー、滑走路27の手前で待機中、出発準備完了です。"),
        ("Line up and wait, runway two seven.", "滑走路27に入って待機してください。"),
        ("Lining up and waiting, runway two seven.", "27に入って待機します。"),
        ("Number two for departure, behind the regional jet on final.", "出発順位2番目、最終進入中のリージョナルジェットの後です。"),
        ("Line up and wait, traffic will land and clear.", "所定の位置に入って待機してください、前の機は着陸後に離脱します。"),
        ("Fly runway heading, expect radar vectors after departure.", "滑走路方位のまま飛行し、離陸後はレーダー誘導を予期してください。"),
        ("Verify you have the current ATIS information.", "現在のATIS情報を確認していますか。"),
        ("We have information Charlie.", "情報チャーリーを受信しています。"),
        ("Say your gate for arrival.", "到着のゲート番号を伝えてください。"),
        ("Request pushback from gate seven.", "ゲート7からのプッシュバックを要求します。"),
        ("Brakes released, ready to push.", "ブレーキを解除、プッシュ準備完了です。"),
        ("Set parking brake, chocks in place.", "駐機ブレーキをセット、輪止めを設置してください。"),
        # --- 離陸 ---
        ("Runway two seven, cleared for takeoff, wind two four zero at eight.", "滑走路27、離陸を許可します、風向240度風速8ノット。"),
        ("Cleared for takeoff, runway two seven.", "滑走路27、離陸許可。"),
        ("Rolling, runway two seven.", "滑走路27、離陸滑走を開始します。"),
        ("Cancel takeoff clearance, traffic on the runway.", "離陸許可を取り消します、滑走路上に障害物があります。"),
        ("Stop immediately, stop immediately.", "直ちに停止せよ、直ちに停止せよ。"),
        ("After departure, fly heading zero niner zero, radar vectors.", "離陸後は方位090で飛行、レーダー誘導します。"),
        ("Contact departure, good day.", "デパーチャーへ連絡してください、では失礼します。"),
        ("Departure, climbing through three thousand for five thousand.", "デパーチャー、3,000フィートを通過して5,000フィートへ上昇中です。"),
        ("Radar contact, climb and maintain one zero thousand.", "レーダー識別、10,000フィートまで上昇維持してください。"),
        ("Traffic ten o'clock, two miles, opposite direction, altitude unknown.", "10時方向、2マイル、反対方向の交通、高度不明です。"),
        ("Looking for traffic.", "交通を確認中です。"),
        ("Traffic in sight.", "交通を視認しました。"),
        # --- 巡航・経路 ---
        ("Climb and maintain flight level three five zero.", "35,000フィートまで上昇し維持してください。"),
        ("Climbing to flight level three five zero.", "35,000フィートへ上昇します。"),
        ("Cross Denver VOR at or above one one thousand.", "デンバーVORを11,000フィート以上で通過してください。"),
        ("Request direct routing to the next waypoint.", "次のウェイポイントへの直行を要求します。"),
        ("Cleared direct, present position, restrictions cancelled.", "現在位置から直行を許可、制限を解除します。"),
        ("Request a higher altitude for smoother air.", "揺れの少ない高度への上昇を要求します。"),
        ("Unable higher due to traffic, maintain present altitude.", "交通のため上昇不可、現在の高度を維持してください。"),
        ("Request twenty degrees left for weather avoidance.", "気象回避のため左20度の変針を要求します。"),
        ("Deviation approved, advise when able direct.", "回避を承認、直行できる時点で連絡してください。"),
        ("Contact center on one three three point five.", "センターへ133.5で連絡してください。"),
        ("Switching to one three three point five, good day.", "133.5に切り替えます、では失礼します。"),
        ("Verify altitude, mode Charlie shows you level at flight level three one zero.", "高度を確認してください、モードCはフライトレベル310を示しています。"),
        # --- 降下・進入 ---
        ("Descend and maintain one one thousand.", "11,000フィートまで降下し維持してください。"),
        ("Descend via the STAR.", "定められた到着経路(STAR)に沿って降下してください。"),
        ("Descending via the STAR to cross Fox intersection at one zero thousand.", "STARに沿ってフォックス地点を10,000フィートで通過するよう降下します。"),
        ("Expect vectors for the ILS runway two seven approach.", "滑走路27ILS進入へのレーダー誘導を予期してください。"),
        ("Turn left heading three three zero, vector for final approach course.", "左旋回して方位330度、最終進入コースへ誘導します。"),
        ("Fly heading three three zero, intercept the localizer.", "方位330度で飛行し、ローカライザーに乗ってください。"),
        ("Cleared for the ILS runway two seven approach.", "滑走路27のILS進入を許可します。"),
        ("Report the field in sight.", "空港が見えたら報告してください。"),
        ("Field in sight, cancelling IFR.", "空港視認、計器飛行方式を取り消します。"),
        ("Report established on the localizer.", "ローカライザーに正規に乗ったら報告してください。"),
        ("Established on the localizer, glideslope alive.", "ローカライザーに正規に乗りました、グライドスロープ受信中です。"),
        ("Reduce speed to one eight zero knots.", "速度を180ノットまで減速してください。"),
        ("Slowing to one eight zero knots.", "180ノットまで減速します。"),
        ("Go around, traffic on the runway.", "着陸復行してください、滑走路上に障害物があります。"),
        ("Going around.", "着陸復行します。"),
        ("Missed approach, climb and maintain three thousand, fly runway heading.", "進入復行、3,000フィートまで上昇維持、滑走路方位で飛行してください。"),
        ("Request another approach after the go-around.", "着陸復行後、再進入を要求します。"),
        ("Vectors for a second approach, fly heading zero niner zero.", "2回目の進入のため誘導します、方位090で飛行してください。"),
        # --- 着陸 ---
        ("Runway two seven, cleared to land, wind two five zero at six.", "滑走路27、着陸を許可します、風向250度風速6ノット。"),
        ("Cleared to land, runway two seven.", "滑走路27、着陸許可。"),
        ("Continue, number two, traffic will clear the runway.", "続けてください、順位2番目、前の機は滑走路を離脱します。"),
        ("Caution, wake turbulence from the heavy departing ahead.", "注意、前方を離陸する大型機の後方乱気流に注意してください。"),
        ("Braking action reported good by the aircraft ahead.", "先行機の報告によりブレーキング状態は良好です。"),
        ("Exit at the next taxiway when able.", "できるだけ早く次の誘導路で滑走路を離脱してください。"),
        ("Vacated the runway.", "滑走路を離脱しました。"),
        ("Contact ground point niner.", "グラウンド118.9へ連絡してください。"),
        ("Welcome to the ground frequency, taxi to the gate via alpha.", "グラウンド周波数へようこそ、アルファ経由でゲートへ地上走行してください。"),
        ("Can you accept a land and hold short clearance, runway one eight?", "滑走路18の手前で停止する条件付き着陸は可能ですか。"),
        ("Unable to hold short, standard full length landing required.", "手前での停止は不可能、通常の滑走路全長での着陸が必要です。"),
        ("Check gear down.", "脚が下りているか確認してください。"),
        # --- 標準応答・交信作法 ---
        ("Say again your last transmission.", "直前の交信をもう一度お願いします。"),
        ("Verify you said flight level three three zero.", "35,000フィート、失礼、33,000フィートとおっしゃいましたか確認します。"),
        ("Confirm assigned altitude.", "指定された高度を確認してください。"),
        ("Roger, standby.", "了解、少々お待ちください。"),
        ("Stand by for further instructions.", "追って指示するまでお待ちください。"),
        ("Disregard my last transmission.", "直前の交信は無視してください。"),
        ("Break, break, all stations standby.", "割り込みます、全局待機してください。"),
        ("How do you read?", "感度いかがですか。"),
        ("Reading you five.", "感度良好、明瞭に受信しています。"),
        ("You're cutting in and out, say again.", "音声が途切れています、もう一度お願いします。"),
        ("Correction, runway two seven, not runway two five.", "訂正します、滑走路25ではなく滑走路27です。"),
        ("Readback correct.", "復唱は正確です。"),
        ("Negative contact, request vectors.", "視認できません、誘導を要求します。"),
        ("Request to change frequency for a moment.", "少しの間、周波数の変更を要求します。"),
        ("Approved as requested.", "要求通り承認します。"),
        # --- 緊急事態 ---
        ("Mayday, mayday, mayday, engine failure, requesting immediate landing.", "メーデー、メーデー、メーデー、エンジン故障、即時着陸を要求します。"),
        ("Declaring an emergency, request the nearest suitable runway.", "緊急事態を宣言します、最寄りの使用可能な滑走路を要求します。"),
        ("Say souls on board and fuel remaining.", "搭乗者数と残燃料を報告してください。"),
        ("Twelve souls on board, two hours of fuel remaining.", "搭乗者12名、残燃料2時間分です。"),
        ("Roger, emergency vehicles are standing by.", "了解、緊急車両が待機しています。"),
        ("Cleared to land any runway, emergency equipment is on scene.", "任意の滑走路への着陸を許可します、緊急車両は現場に到着しています。"),
        ("Pan-pan, pan-pan, pan-pan, we have a passenger with a medical emergency.", "パンパン、パンパン、パンパン、乗客に急病人が発生しました。"),
        ("Request priority handling for a medical emergency.", "急病人対応のため優先的な取扱いを要求します。"),
        ("Squawk seven seven zero zero.", "スコーク7700にセットしてください。"),
        ("Squawking seven seven zero zero.", "7700にセットしました。"),
        ("Squawk seven six zero zero for radio failure.", "無線故障の場合はスコーク7600にセットしてください。"),
        ("We have lost cabin pressure, requesting an emergency descent.", "客室与圧を喪失しました、緊急降下を要求します。"),
        ("Emergency descent approved, all other traffic will be advised.", "緊急降下を承認します、他の交通機には周知します。"),
        ("Fuel emergency, request priority landing.", "燃料緊急事態、優先着陸を要求します。"),
        ("Minimum fuel, unable to accept further delay.", "燃料が最小限です、これ以上の遅延は受け入れられません。"),
        # --- 気象通報・照会 ---
        ("Request current wind and altimeter.", "現在の風向風速と気圧設定を要求します。"),
        ("Wind two three zero at one two, altimeter three zero one two.", "風向230度風速12ノット、気圧設定は30.12インチです。"),
        ("Request ride reports ahead.", "前方の乗り心地報告を要求します。"),
        ("Previous aircraft reported light chop at this altitude.", "先行機はこの高度で軽い揺れを報告しています。"),
        ("Report any turbulence encountered on this route.", "この経路で遭遇した乱気流を報告してください。"),
        ("Moderate turbulence between flight level one eight zero and flight level two two zero.", "フライトレベル180から220の間で中程度の乱気流があります。"),
        ("Request a PIREP for icing conditions.", "着氷状況についてパイロット報告を要求します。"),
        ("Picked up light rime ice climbing through eight thousand.", "8,000フィート通過中に軽いラインアイスを確認しました。"),
        ("Advise if you need to deviate around weather.", "気象回避のため経路変更が必要な場合は知らせてください。"),
        ("Request thirty degrees right to avoid a cell.", "積乱雲を回避するため右30度を要求します。"),
        ("Ceiling one thousand, visibility two miles in mist.", "シーリング1,000フィート、視程2マイル、もやを伴います。"),
        ("Braking action poor, reported by the last aircraft.", "先行機によるとブレーキング状態は不良です。"),
        ("Runway visual range six hundred, decreasing.", "滑走路視距離600フィート、低下傾向です。"),
        ("Low-level wind shear alert, gain of fifteen knots on short final.", "低高度ウィンドシア警報、最終進入で15ノットの増速があります。"),
        ("Request the latest ATIS for wind and runway in use.", "使用滑走路と風向のため最新のATISを要求します。"),
        # --- グラウンドコントロール・空港内 ---
        ("Follow the taxi lead-in lines to your assigned gate.", "誘導路標示に従って指定のゲートまで進んでください。"),
        ("Contact ramp control once clear of the runway.", "滑走路離脱後はランプコントロールへ連絡してください。"),
        ("Give way to the tug crossing ahead.", "前方を横断するトーイングトラクターに進路を譲ってください。"),
        ("Remain this frequency, monitor for other traffic.", "この周波数のまま、他の交通を聞いていてください。"),
        ("Request progressive taxi instructions, unfamiliar with the airport.", "空港に不慣れなため、段階的な地上走行指示を要求します。"),
        ("Turn right on taxiway bravo, then left on delta to the gate.", "誘導路ブラボーで右折、その後デルタで左折してゲートへ進んでください。"),
        ("Confirm you are clear of all runways.", "全ての滑走路を離脱したか確認してください。"),
        ("Clear of all runways, on taxiway alpha.", "全滑走路を離脱、誘導路アルファ上です。"),
        ("Request de-icing prior to departure.", "出発前の除氷を要求します。"),
        ("Proceed to the de-icing pad and hold.", "除氷パッドへ進んで待機してください。"),
        ("De-icing complete, ready to taxi.", "除氷完了、地上走行の準備ができました。"),
        ("Expect a gate hold due to a ground stop at the destination.", "目的地の運航停止のため、ゲートでの待機を予期してください。"),
        # --- 交通情報・見張り ---
        ("Traffic alert, climb immediately, traffic one o'clock, one mile.", "衝突回避、直ちに上昇してください、1時方向1マイルに交通あり。"),
        ("Climbing to avoid traffic.", "交通回避のため上昇します。"),
        ("Traffic no longer a factor.", "交通は解消しました。"),
        ("Advisory only, traffic is not a factor at this time.", "参考情報のみです、現時点で交通の支障はありません。"),
        ("Request flight following to the destination airport.", "目的地空港までの飛行追従サービスを要求します。"),
        ("Squawk four five one two and ident.", "スコーク4512にセットし、アイデントを押してください。"),
        ("Identing.", "アイデントを押します。"),
        ("Radar service terminated, squawk VFR, frequency change approved.", "レーダーサービスを終了します、有視界飛行用コードにセットし、周波数変更を承認します。"),
        ("Maintain visual separation from traffic in sight.", "視認した交通との視覚間隔を維持してください。"),
        ("Unable visual separation, request vectors instead.", "視覚間隔の維持は不可能です、代わりに誘導を要求します。"),
        # --- 洋上・長距離 ---
        ("Position report, over.", "位置通報、どうぞ。"),
        ("Estimating the next reporting point at four five.", "次の通報地点の通過予想時刻は45分です。"),
        ("Request oceanic clearance for the North Atlantic track.", "北大西洋トラックの洋上許可を要求します。"),
        ("Oceanic clearance received, maintain mach point eight two.", "洋上許可を受領、マッハ0.82を維持してください。"),
        ("Unable to raise the next control on this frequency.", "この周波数では次の管制機関と交信できません。"),
        ("Relay our position through another aircraft on this frequency.", "この周波数の他機を通じて位置を中継してください。"),
    ]
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
    sys.exit(main())
