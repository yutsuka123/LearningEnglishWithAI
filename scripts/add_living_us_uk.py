# ruff: noqa: E501  (data-heavy seed script)
"""Survival/everyday-living English for the US & UK (+~100 words, +~100
phrases). Authored by Claude — no app/OpenAI API calls. Phrases dedupe on
english (lowercased); words dedupe on english and back-fill empty examples.

狙い: とりあえず米英で生活できるレベル（住まい・銀行/郵便・医療・買い物・
交通・各種手続き）。US/UK で語が違うものは両方収録（例: petrol/gas,
flat/apartment 系は既存にもあり、重複は自動スキップ）。

Run:  python scripts/add_living_us_uk.py   (then run scripts/relevel.py)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "生活・住まい": [
        ("I'd like to view the flat, please.", "部屋を内見したいのですが。"),
        ("How much is the monthly rent?", "家賃は月いくらですか。"),
        ("Is the deposit refundable?", "敷金は返金されますか。"),
        ("Are bills included in the rent?", "光熱費は家賃に含まれますか。"),
        ("When is the rent due?", "家賃の支払日はいつですか。"),
        ("The heating isn't working.", "暖房が効きません。"),
        ("Could you send someone to fix the boiler?", "ボイラーの修理に人をよこしてもらえますか。"),
        ("There's a leak under the sink.", "流しの下から水漏れがあります。"),
        ("I'd like to report a problem with the flat.", "部屋の不具合を報告したいのですが。"),
        ("How long is the tenancy?", "賃貸の契約期間はどのくらいですか。"),
        ("Is the flat furnished?", "部屋は家具付きですか。"),
        ("Could I have a copy of the contract?", "契約書の控えをいただけますか。"),
        ("The Wi-Fi keeps dropping out.", "Wi-Fiがすぐ切れてしまいます。"),
        ("Who do I contact about repairs?", "修理はどこに連絡すればいいですか。"),
    ],
    "生活・銀行/郵便": [
        ("I'd like to open a bank account.", "銀行口座を開設したいのですが。"),
        ("What do I need to open an account?", "口座開設には何が必要ですか。"),
        ("I'd like to set up a direct debit.", "口座引き落としを設定したいのですが。"),
        ("My card has been declined.", "カードが使えませんでした(拒否されました)。"),
        ("I've lost my debit card.", "デビットカードをなくしました。"),
        ("Could you help me transfer some money?", "送金を手伝ってもらえますか。"),
        ("Is there a fee for withdrawing cash?", "現金を引き出すのに手数料はかかりますか。"),
        ("I'd like to send this parcel to Japan.", "この小包を日本に送りたいのですが。"),
        ("How much is a stamp for a letter?", "手紙の切手はいくらですか。"),
        ("When will it arrive?", "いつ届きますか。"),
        ("Do you have proof of address?", "住所を証明するものはお持ちですか。"),
        ("I need to update my address.", "住所変更の手続きをしたいのですが。"),
        ("Is there a cash machine nearby?", "近くにATMはありますか。"),
        ("Could you break a twenty?", "20(ポンド/ドル)札をくずせますか。"),
    ],
    "生活・医療": [
        ("I'd like to register with a GP.", "かかりつけ医に登録したいのですが。"),
        ("Can I book an appointment, please?", "予約を取りたいのですが。"),
        ("I'd like to see a doctor today.", "今日、医師に診てもらいたいのですが。"),
        ("Do I need a prescription for this?", "これは処方箋が必要ですか。"),
        ("Where's the nearest pharmacy?", "一番近い薬局はどこですか。"),
        ("Do you have anything for a headache?", "頭痛に効くものはありますか。"),
        ("I've run out of my medication.", "薬を切らしてしまいました。"),
        ("Is this covered by insurance?", "これは保険でカバーされますか。"),
        ("How often should I take this?", "これはどのくらいの頻度で飲めばいいですか。"),
        ("I think I need to see a dentist.", "歯医者に診てもらう必要がありそうです。"),
        ("It's an emergency.", "緊急事態です。"),
        ("Could you call an ambulance?", "救急車を呼んでもらえますか。"),
    ],
    "生活・買い物": [
        ("Do you take card?", "カードは使えますか。"),
        ("Can I pay by contactless?", "タッチ決済できますか。"),
        ("Could I have a bag, please?", "袋をもらえますか。"),
        ("Where can I find the milk?", "牛乳はどこにありますか。"),
        ("Do you have this in a different size?", "これの別のサイズはありますか。"),
        ("Is this on offer?", "これは特売(セール)ですか。"),
        ("Can I get a refund?", "返金してもらえますか。"),
        ("I'd like to return this, please.", "これを返品したいのですが。"),
        ("Could you tell me where the checkout is?", "レジはどこか教えてもらえますか。"),
        ("What time do you close?", "何時に閉まりますか。"),
        ("Do you accept cash?", "現金は使えますか。"),
        ("Could I have a receipt, please?", "レシートをいただけますか。"),
        ("Is it in stock?", "在庫はありますか。"),
        ("That's a bit too expensive for me.", "ちょっと予算オーバーです。"),
    ],
    "生活・交通": [
        ("A single to King's Cross, please.", "キングス・クロスまで片道1枚お願いします。"),
        ("A return to Oxford, please.", "オックスフォードまで往復でお願いします。"),
        ("Where can I top up my travel card?", "交通カードはどこでチャージできますか。"),
        ("Which platform does the train leave from?", "電車はどのホームから出ますか。"),
        ("Does this bus go to the city centre?", "このバスは中心街に行きますか。"),
        ("How much is the fare?", "運賃はいくらですか。"),
        ("Could you tell me when to get off?", "降りる場所を教えてもらえますか。"),
        ("Is there a station near here?", "この近くに駅はありますか。"),
        ("Fill it up, please.", "満タンにしてください。"),
        ("Where's the nearest petrol station?", "一番近いガソリンスタンドはどこですか。"),
        ("Could you call me a taxi?", "タクシーを呼んでもらえますか。"),
        ("How long does it take to get there?", "そこまでどのくらいかかりますか。"),
        ("Is it within walking distance?", "そこは歩いて行ける距離ですか。"),
        ("How do I get to the station from here?", "ここから駅へはどう行きますか。"),
    ],
    "生活・手続き/会話": [
        ("Could you speak a bit more slowly, please?", "もう少しゆっくり話してもらえますか。"),
        ("Sorry, I didn't catch that.", "すみません、聞き取れませんでした。"),
        ("Could you repeat that, please?", "もう一度言ってもらえますか。"),
        ("Could you write it down for me?", "書いていただけますか。"),
        ("Sorry, I'm not from around here.", "すみません、この辺りの者ではないんです。"),
        ("Could you point me in the right direction?", "方向だけでも教えてもらえますか。"),
        ("I'd like to set up my broadband.", "ネット回線を開通させたいのですが。"),
        ("How do I top up my phone?", "携帯はどうやってチャージしますか。"),
        ("Is there free Wi-Fi here?", "ここに無料Wi-Fiはありますか。"),
        ("Where do I sign?", "どこにサインすればいいですか。"),
        ("What's the postcode here?", "ここの郵便番号は何ですか。"),
        ("Could you help me, please? I'm lost.", "すみません、道に迷いました。手伝ってもらえますか。"),
        ("Excuse me, where are the toilets?", "すみません、トイレはどこですか。"),
        ("Where's the restroom?", "お手洗いはどこですか。"),
        ("Could I get the bill, please?", "お会計をお願いします。"),
        ("Could we have a table for two?", "2名席をお願いできますか。"),
        ("I have a reservation under Tanaka.", "田中の名前で予約しています。"),
        ("Could I have it to go?", "持ち帰りにできますか。"),
        ("I'll have the same, please.", "私も同じものをお願いします。"),
        ("Is this seat taken?", "この席は空いていますか。"),
        ("After you.", "お先にどうぞ。"),
        ("Mind the gap.", "(電車とホームの)すき間にご注意ください。"),
        ("Could I borrow a pen?", "ペンを貸してもらえますか。"),
        ("My phone's about to die.", "携帯の充電が切れそうです。"),
        ("Could you turn the heating up?", "暖房を強めてもらえますか。"),
        ("The light bulb has gone.", "電球が切れました。"),
        ("How do I pay the electricity bill?", "電気代はどう払えばいいですか。"),
        ("Is there a launderette nearby?", "近くにコインランドリーはありますか。"),
        ("Could you transfer me to the right department?", "担当部署につないでもらえますか。"),
        ("I'd like to make a complaint.", "苦情を申し立てたいのですが。"),
        ("I'd like to make a follow-up appointment.", "再診の予約をしたいのですが。"),
        ("I've got a temperature.", "熱があります。"),
        ("Where are the changing rooms?", "試着室はどこですか。"),
        ("Could you gift-wrap this, please?", "ギフト包装してもらえますか。"),
        ("Does this train stop at every station?", "この電車は各駅停車ですか。"),
        ("I'd like a day pass, please.", "一日乗車券をください。"),
        ("Is this the right stop for the museum?", "博物館へはこの停留所で合っていますか。"),
        ("Can you recommend a good place to eat?", "おすすめの食事処はありますか。"),
        ("How much do I owe you?", "いくらお支払いすればいいですか。"),
        ("Could you keep an eye on my bag for a second?", "少しの間、荷物を見ていてもらえますか。"),
        ("I'll take it.", "これにします(買います)。"),
        ("Let me check and get back to you.", "確認してまたご連絡します。"),
        ("Is breakfast included?", "朝食は付いていますか。"),
        ("Could I have a wake-up call at seven?", "7時にモーニングコールをお願いできますか。"),
    ],
}

WORDS_BY_DOMAIN: dict[str, list[tuple[str, str, str]]] = {
    "生活": [
        ("landlord", "大家・家主", "The landlord raised the rent."),
        ("tenant", "借主・入居者", "The tenant signed the lease."),
        ("lease", "賃貸契約", "They signed a one-year lease."),
        ("tenancy", "賃借(期間)", "The tenancy runs for two years."),
        ("utilities", "公共料金(光熱費)", "Utilities are not included in the rent."),
        ("mortgage", "住宅ローン", "They took out a mortgage."),
        ("estate agent", "不動産屋(英)", "The estate agent showed us the flat."),
        ("landline", "固定電話", "We still have a landline at home."),
        ("broadband", "ブロードバンド・ネット回線", "The broadband is very fast."),
        ("council tax", "住民税(英)", "Council tax is paid every month."),
        ("boiler", "給湯ボイラー(英)", "The boiler broke down in winter."),
        ("radiator", "暖房器・ラジエーター", "The radiator keeps the room warm."),
        ("plumber", "配管工", "We called a plumber for the leak."),
        ("electrician", "電気工", "An electrician fixed the wiring."),
        ("tap", "蛇口(英)", "Please turn off the tap."),
        ("faucet", "蛇口(米)", "The faucet is dripping."),
        ("rubbish", "ごみ(英)", "Take out the rubbish, please."),
        ("bin", "ごみ箱(英)", "Put it in the bin."),
        ("recycling", "資源回収・リサイクル", "Recycling is collected on Fridays."),
        ("hoover", "掃除機(をかける)(英)", "I need to hoover the carpet."),
        ("furnished", "家具付きの", "We rented a furnished flat."),
        ("viewing", "内見", "We booked a viewing for Saturday."),
        ("flatmate", "ルームメイト(英)", "My flatmate cooks really well."),
        ("kettle", "やかん・電気ケトル", "Put the kettle on for some tea."),
        ("duvet", "掛け布団", "Buy a warm duvet for winter."),
        ("cutlery", "カトラリー・食器類", "Set out the cutlery for dinner."),
        ("wardrobe", "衣装だんす・クローゼット", "Hang your coat in the wardrobe."),
        ("jumper", "セーター(英)", "Put on a jumper; it's cold."),
        ("trainers", "スニーカー(英)", "I bought new trainers for running."),
        ("overdraft", "当座貸越", "He went into his overdraft."),
        ("debit card", "デビットカード", "I paid with my debit card."),
        ("current account", "当座預金口座(英)", "I opened a current account."),
        ("checking account", "当座預金口座(米)", "I opened a checking account."),
        ("sort code", "銀行支店コード(英)", "Enter the sort code and account number."),
        ("direct debit", "口座自動引き落とし(英)", "Set up a direct debit for the bills."),
        ("standing order", "定額自動送金(英)", "I pay my rent by standing order."),
        ("contactless", "非接触決済(タッチ)", "I paid contactless at the till."),
        ("withdraw", "引き出す", "I need to withdraw some cash."),
        ("cashpoint", "ATM・現金自動預払機(英)", "There's a cashpoint round the corner."),
        ("statement", "明細・取引明細", "Check your bank statement online."),
        ("invoice", "請求書", "They sent me an invoice by email."),
        ("GP", "かかりつけ医(英)", "I made an appointment with my GP."),
        ("surgery", "診療所(英)", "The surgery opens at nine."),
        ("prescription", "処方箋", "The doctor wrote a prescription."),
        ("pharmacy", "薬局", "Pick up the medicine at the pharmacy."),
        ("chemist", "薬局(英)", "Buy some plasters at the chemist."),
        ("NHS", "国民保健サービス(英)", "The NHS is free at the point of use."),
        ("referral", "紹介(医療)", "The GP gave me a referral to a specialist."),
        ("optician", "眼鏡店・検眼士", "I'm seeing the optician on Monday."),
        ("trolley", "ショッピングカート(英)", "Grab a trolley at the entrance."),
        ("cart", "ショッピングカート(米)", "Grab a cart at the entrance."),
        ("till", "レジ(英)", "Please pay at the till."),
        ("checkout", "レジ・会計", "The checkout queue was long."),
        ("queue", "行列(に並ぶ)(英)", "Please join the queue."),
        ("line", "行列(米)", "Please wait in line."),
        ("aisle", "通路(店内)", "The cereal is in aisle three."),
        ("expiry date", "賞味/消費期限", "Check the expiry date before buying."),
        ("off-licence", "酒販店(英)", "Buy some wine at the off-licence."),
        ("corner shop", "個人商店(英)", "Get some milk from the corner shop."),
        ("takeaway", "持ち帰り(料理)(英)", "Let's get a takeaway tonight."),
        ("takeout", "持ち帰り(料理)(米)", "Let's order takeout tonight."),
        ("voucher", "引換券・クーポン", "I used a voucher at the checkout."),
        ("loyalty card", "ポイントカード", "Do you have a loyalty card?"),
        ("tube", "地下鉄(ロンドン)", "Take the tube to Soho."),
        ("fare", "運賃", "The bus fare has gone up again."),
        ("single", "片道(切符)(英)", "A single to Leeds, please."),
        ("return", "往復(切符)(英)", "A day return to Oxford, please."),
        ("season ticket", "定期券", "I bought a monthly season ticket."),
        ("petrol", "ガソリン(英)", "I need to fill up with petrol."),
        ("motorway", "高速道路(英)", "We drove north on the motorway."),
        ("roundabout", "ロータリー(環状交差点)", "Take the second exit at the roundabout."),
        ("pavement", "歩道(英)", "Walk on the pavement, not the road."),
        ("sidewalk", "歩道(米)", "Walk on the sidewalk, not the road."),
        ("pedestrian", "歩行者", "Drivers must watch for pedestrians."),
        ("zebra crossing", "横断歩道(英)", "Cross at the zebra crossing."),
        ("crosswalk", "横断歩道(米)", "Cross at the crosswalk."),
        ("timetable", "時刻表", "Check the timetable for the next train."),
        ("platform", "ホーム・番線", "The train leaves from platform two."),
        ("MOT", "車検(英)", "The car is due for its MOT."),
        ("postcode", "郵便番号(英)", "What's your postcode, please?"),
        ("zip code", "郵便番号(米)", "Enter your zip code at checkout."),
        ("parcel", "小包", "A parcel arrived for you today."),
        ("stamp", "切手", "I need a first-class stamp."),
        ("top up", "チャージ/補充する", "I need to top up my phone."),
        ("SIM card", "SIMカード", "I bought a local SIM card."),
        ("proof of address", "住所証明", "Please bring proof of address."),
        ("driving licence", "運転免許証(英)", "Show your driving licence."),
        ("national insurance", "国民保険(番号)(英)", "Apply for a national insurance number."),
        ("council", "自治体・地方議会", "Contact your local council about the bins."),
        ("fortnight", "2週間(英)", "I'll see you in a fortnight."),
        ("bank holiday", "祝日(英)", "Monday is a bank holiday."),
        ("tip", "チップ", "Leave a tip for good service."),
        ("change", "釣り銭・小銭", "Keep the change, please."),
        ("drugstore", "ドラッグストア(米)", "Buy it at the drugstore."),
        ("cell phone", "携帯電話(米)", "My cell phone is almost dead."),
        ("mobile", "携帯電話(英)", "Give me a call on my mobile."),
        ("restroom", "トイレ(米)", "Where's the restroom, please?"),
        ("letting agency", "賃貸仲介業者(英)", "The letting agency handles repairs."),
        ("landlady", "女性の大家", "The landlady lives next door."),
        ("realtor", "不動産業者(米)", "The realtor showed us the house."),
        ("utility bill", "公共料金の請求書", "I need a utility bill as proof of address."),
        ("launderette", "コインランドリー(英)", "Is there a launderette nearby?"),
        ("laundromat", "コインランドリー(米)", "I do my washing at the laundromat."),
        ("light bulb", "電球", "The light bulb needs replacing."),
        ("plug", "電源プラグ", "Where can I buy a plug adapter?"),
        ("adapter", "変換アダプター", "Bring a UK plug adapter."),
        ("socket", "コンセント(英)", "There's a socket behind the sofa."),
        ("outlet", "コンセント(米)", "Plug it into the outlet."),
        ("washing-up", "食器洗い(英)", "I'll do the washing-up after dinner."),
        ("letterbox", "郵便受け(英)", "Post it through the letterbox."),
        ("plaster", "ばんそうこう(英)", "Put a plaster on the cut."),
        ("band-aid", "ばんそうこう(米)", "Put a band-aid on it."),
        ("jab", "予防接種(英・口語)", "I got my flu jab last week."),
        ("A&E", "救急外来(英)", "She was taken to A&E by ambulance."),
        ("ER", "救急外来(米)", "He was rushed to the ER."),
        ("waiting list", "順番待ちリスト", "There's a long waiting list for the clinic."),
        ("bargain", "掘り出し物・特売品", "That coat was a real bargain."),
        ("sale", "セール・特売", "The shop has a big winter sale."),
        ("fitting room", "試着室", "The fitting rooms are upstairs."),
        ("self-checkout", "セルフレジ", "Use the self-checkout to save time."),
        ("pay-as-you-go", "プリペイド式(英)", "I'm on a pay-as-you-go phone plan."),
        ("payslip", "給与明細(英)", "Keep your payslip for your records."),
        ("minimum wage", "最低賃金", "He earns the minimum wage."),
        ("petrol station", "ガソリンスタンド(英)", "Pull into the petrol station."),
        ("gas station", "ガソリンスタンド(米)", "Pull into the gas station."),
        ("car park", "駐車場(英)", "Park in the multi-storey car park."),
        ("parking lot", "駐車場(米)", "Park in the parking lot."),
        ("ground floor", "1階(英)", "The shop is on the ground floor."),
        ("first floor", "2階(英)・1階(米)", "Take the lift to the first floor."),
    ],
}


def main() -> int:
    with db() as conn:
        p_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        per_scene: dict[str, int] = {}
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in p_existing:
                    p_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                p_existing.add(en.lower())
                p_added += 1
                per_scene[scene] = per_scene.get(scene, 0) + 1

        w_existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        w_added = w_skipped = 0
        for domain, items in WORDS_BY_DOMAIN.items():
            for en, ja, ex in items:
                if en.lower() in w_existing:
                    conn.execute(
                        "UPDATE words SET example = ? WHERE "
                        "LOWER(english) = LOWER(?) "
                        "AND COALESCE(example, '') = ''",
                        (ex, en),
                    )
                    w_skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO words (english, japanese, part_of_speech, "
                    "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                    (en, ja, "", ex, domain, "500"),
                )
                w_existing.add(en.lower())
                w_added += 1

    print(f"phrases: +{p_added} (skipped {p_skipped})  {per_scene}")
    print(f"words:   +{w_added} (skipped {w_skipped})")
    with db() as conn:
        print(
            "totals -> phrases:",
            conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0],
            "/ words:",
            conn.execute("SELECT COUNT(*) FROM words").fetchone()[0],
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
