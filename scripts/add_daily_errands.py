# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Bulk-add curated phrases for DAILY ERRANDS WHILE LIVING ABROAD,
authored by Claude (2026-08-04・ユーザー要望).

海外生活で実際に発生する「役所・公的機関・生活インフラ」まわりの手続き
フレーズを新規に補強する:

- 医療機関を受診する: 予約・受付・保険証提示・初診・待ち時間・会計・
  領収書（保険請求用）・支払い方法・次回予約など「受診の事務フロー」
  （既存の「病院・症状」は症状描写中心なので、そちらとは重複しない）
- 市役所・区役所での手続き: 転入/転出届、住民票、在留カード申請・更新、
  窓口案内、必要書類、処理時間、英語対応可否
- 税務署にいく: 確定申告、控除、納税証明書、期限、延滞税、英語資料、
  相談窓口
- 警察署での手続き: 遺失物届（盗難ではなく紛失）、保険用の証明書取得、
  自転車盗難、拾得物の手続き、交番への道案内（既存の「警察・トラブル」
  「緊急・護身」は事件性の高い場面・緊急対応中心なので、そちらとは
  別角度＝事務手続きとしての警察署利用）
- 消防・救急への連絡: 火災通報、救急要請、住所・状況の伝え方、
  再入館の可否、消防点検
- 郵便局での手続き: 書留・追跡、私書箱、国際発送費用・税関申告書、
  転送届、保管荷物の受け取り、再配達（既存の「生活・手続き」にある
  数件の小包・切手フレーズとは重複しない範囲で拡充）
- 食料品店で買い物: 特定商品の場所、賞味期限、地域特産品、
  オーガニック/アレルギー表示、量り売り、レジ袋・ポイントカード
- 雑貨屋で買い物: 生活雑貨、ラッピング、開封後の返品規定、
  おすすめ、陳列場所
- お土産を買いに行く: 人気のお土産、個包装、日持ち・要冷蔵、
  詰め合わせ、税関・機内持ち込み可否、予算別のおすすめ

加えて、既存の「鉄道・駅」シーンに手薄だった角度
（コインロッカー、駅の忘れ物取扱所、ホーム放送）を数件追加。
駅と一般的な服の買い物（試着・サイズ・色）は既存カバーが厚いため、
服の買い物は新規シーンを追加せず見送った。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_daily_errands.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# --- phrases: scene -> [(english, japanese)] --------------------------------

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "医療機関を受診する": [
        ("I have an appointment at ten o'clock.", "10時に予約をしています。"),
        ("I'd like to make an appointment for next week.", "来週の予約を取りたいのですが。"),
        ("Do you have any openings this afternoon?", "今日の午後、空きはありますか？"),
        ("I'm a new patient here.", "こちらは初めて受診します。"),
        ("This is my first time visiting this clinic.", "このクリニックを受診するのは初めてです。"),
        ("Here's my insurance card.", "こちらが保険証です。"),
        ("I don't have insurance here — how much would it cost to pay out of pocket?", "こちらの保険には入っていないのですが、自費だといくらぐらいかかりますか？"),
        ("Is my insurance accepted here?", "この保険はここで使えますか？"),
        ("Could you spell your name for me?", "お名前をアルファベットで教えていただけますか？〔受付が患者に〕"),
        ("Could I get a form for insurance reimbursement?", "保険の払い戻し用の書類をいただけますか？"),
        ("Please take a seat in the waiting room.", "待合室でお待ちください。"),
        ("How long is the wait right now?", "今、どのくらい待ちますか？"),
        ("Thank you for waiting, the doctor is ready for you now.", "お待たせいたしました、先生の準備ができました。〔受付が患者に〕"),
        ("The doctor will see you shortly.", "まもなく先生がお呼びします。"),
        ("How would you like to pay?", "お支払いはどうされますか？"),
        ("Can I pay by credit card?", "クレジットカードで支払えますか？"),
        ("Could I have a receipt for my insurance claim?", "保険請求用の領収書をいただけますか？"),
        ("Could you itemize the receipt, please?", "領収書の内訳を書いていただけますか？"),
        ("I'd like to schedule a follow-up visit.", "次回の通院を予約したいのですが。"),
        ("When should I come back for a check-up?", "次はいつ検査に来ればいいですか？"),
        ("Do I need to bring anything next time?", "次回、何か持ってくるものはありますか？"),
        ("Is there a cancellation fee?", "キャンセル料はかかりますか？"),
        ("Could you write the diagnosis in English?", "診断名を英語で書いていただけますか？"),
        ("I need this translated for my insurance company back home.", "本国の保険会社に出すため、これを翻訳してもらう必要があります。"),
        ("Is walk-in okay, or do I need an appointment?", "予約なしでも大丈夫ですか、それとも予約が必要ですか？"),
    ],
    "市役所・区役所での手続き": [
        ("I'd like to register my address.", "住所登録をしたいのですが。"),
        ("I just moved here and need to register my residence.", "最近こちらに引っ越してきたので、転入届を出したいです。"),
        ("I need to report a change of address.", "住所変更の届け出をしたいのですが。"),
        ("I'm moving out of this city — how do I deregister?", "この市から転出するのですが、どう手続きすればいいですか？"),
        ("Could I get a certificate of residence?", "住民票をいただけますか？"),
        ("How many copies of the residence certificate do I need?", "住民票は何通必要ですか？"),
        ("I'd like to apply for a resident card.", "在留カードの申請をしたいのですが。"),
        ("Which window should I go to for this?", "この手続きはどの窓口に行けばいいですか？"),
        ("What number window is this?", "これは何番の窓口ですか？"),
        ("Could you tell me which counter handles this?", "どちらの窓口で扱っているか教えていただけますか？"),
        ("What documents do I need to bring?", "どんな書類を持ってくる必要がありますか？"),
        ("Do I need my passport for this?", "これにはパスポートが必要ですか？"),
        ("How long does this usually take to process?", "手続きには通常どのくらいかかりますか？"),
        ("Will this be ready today, or do I need to come back?", "今日中にできますか、それとも出直す必要がありますか？"),
        ("I'd like to renew my residence card.", "在留カードを更新したいのですが。"),
        ("My residence card is about to expire.", "在留カードの期限がもうすぐ切れます。"),
        ("Is there anyone here who speaks English?", "英語が話せる方はいらっしゃいますか？"),
        ("Could you explain this form to me?", "この用紙について説明していただけますか？"),
        ("What's this box for?", "この欄は何を書くところですか？"),
        ("Please take a number and wait to be called.", "番号札を取って、お呼びするまでお待ちください。〔窓口が案内〕"),
        ("Your number is being called — please go to counter five.", "お呼びしています、5番窓口へお越しください。〔窓口が案内〕"),
        ("Is there a fee for this certificate?", "この証明書は手数料がかかりますか？"),
        ("How do I pay the fee?", "手数料はどう支払えばいいですか？"),
        ("Can I fill this out in English?", "これは英語で記入してもいいですか？"),
        ("Where do I submit this application?", "この申請書はどこに提出すればいいですか？"),
    ],
    "税務署にいく": [
        ("I'd like to file my tax return.", "確定申告をしたいのですが。"),
        ("This is my first time filing here — where do I start?", "ここで申告するのは初めてです、どこから始めればいいですか？"),
        ("What's the deadline for filing this year?", "今年の申告期限はいつですか？"),
        ("Can I get an extension on the deadline?", "期限を延長してもらうことはできますか？"),
        ("What happens if I file late?", "申告が遅れるとどうなりますか？"),
        ("Is there a penalty for paying after the due date?", "期限後に納付すると延滞税がかかりますか？"),
        ("Could you explain the deductions I'm eligible for?", "私が受けられる控除について説明していただけますか？"),
        ("Am I eligible for a dependent deduction?", "扶養控除の対象になりますか？"),
        ("Can I deduct my medical expenses?", "医療費控除は受けられますか？"),
        ("I need a certificate of tax payment.", "納税証明書が必要です。"),
        ("Could I get a copy of my tax record?", "私の納税記録の写しをいただけますか？"),
        ("Do you have a pamphlet in English?", "英語のパンフレットはありますか？"),
        ("Is there an English guide for this form?", "この用紙の英語版の記入案内はありますか？"),
        ("I have a question about my tax bracket.", "自分の税率区分について質問があります。"),
        ("Could I speak with someone about my tax return?", "確定申告について誰かに相談できますか？"),
        ("I'm not sure which form applies to me.", "自分にどの用紙が当てはまるかわかりません。"),
        ("How do I pay my tax bill?", "税金の支払いはどうすればいいですか？"),
        ("Can I pay in installments?", "分割で納付することはできますか？"),
        ("I think I overpaid — how do I request a refund?", "払いすぎたと思うのですが、還付はどう申請すればいいですか？"),
        ("Could you double-check I filled this out correctly?", "正しく記入できているか確認していただけますか？"),
    ],
    "警察署での手続き": [
        ("I lost my umbrella on the train — where should I report it?", "電車に傘を忘れたのですが、どこに届け出ればいいですか？"),
        ("I think I dropped my wallet somewhere around here.", "この辺りで財布を落としたと思うのですが。"),
        ("I'd like to file a report for my lost item.", "落とし物の届け出をしたいのですが。"),
        ("Could you give me a case number for this report?", "この届け出の受理番号をいただけますか？"),
        ("I need a police report for my travel insurance claim.", "旅行保険の請求のために警察の証明書が必要です。"),
        ("Could you stamp this form, please?", "この書類に押印していただけますか？"),
        ("My bike was stolen from outside the station.", "駅の外に停めていた自転車が盗まれました。"),
        ("Do you need the bike's registration number?", "自転車の防犯登録番号は必要ですか？"),
        ("Here's my bicycle registration certificate.", "こちらが自転車の防犯登録証です。"),
        ("Has anyone handed in a lost item matching this description?", "この特徴に合う落とし物は届いていますか？"),
        ("How long do you keep found items here?", "拾得物はこちらでどのくらいの期間保管されますか？"),
        ("If someone turns it in later, how will I be contacted?", "後で届けられた場合、どうやって連絡をいただけますか？"),
        ("Is there a koban near here?", "この近くに交番はありますか？"),
        ("Where's the nearest police box?", "一番近い交番はどこですか？"),
        ("I'd like to report some graffiti on my property.", "うちの敷地に落書きをされたので届け出たいのですが。"),
        ("My neighbor's dog keeps getting loose — who do I report that to?", "近所の犬がよく放し飼いになっているのですが、どこに相談すればいいですか？"),
        ("I'm not filing a complaint, I just want it on record.", "被害届は出しませんが、記録には残しておきたいです。"),
        ("Could I get a translated copy of this report?", "この届け出書の翻訳をいただけますか？"),
        ("Do you have an interpreter available?", "通訳をお願いできますか？"),
        ("What's the process if the item is found later?", "後で見つかった場合、どういう流れになりますか？"),
    ],
    "消防・救急への連絡": [
        ("There's a fire in my building!", "私の住むビルで火事です！"),
        ("I smell smoke coming from the apartment next door.", "隣の部屋から煙のにおいがします。"),
        ("I need to report a fire.", "火事の通報をしたいです。"),
        ("We need an ambulance right away.", "すぐに救急車が必要です。"),
        ("My address is 4-2-1 Midori-cho, on the third floor.", "住所は緑町4-2-1、3階です。"),
        ("The nearest cross street is Sakura Avenue.", "一番近い交差点はさくら通りです。"),
        ("It's a two-story house with a red roof.", "赤い屋根の2階建ての家です。"),
        ("Someone has collapsed and isn't breathing.", "人が倒れていて呼吸をしていません。"),
        ("He's conscious but in a lot of pain.", "意識はありますが、かなり痛がっています。"),
        ("How many people are trapped inside?", "中に何人閉じ込められていますか？〔消防が確認〕"),
        ("Stay on the line, help is on the way.", "電話を切らずにお待ちください、今向かっています。〔通信指令が対応〕"),
        ("Is it safe to go back inside now?", "もう中に戻っても安全ですか？"),
        ("When can we re-enter the building?", "いつ建物に戻れますか？"),
        ("Could you inspect our building for fire safety?", "うちの建物の消防点検をお願いできますか？"),
        ("The alarm went off — was it a false alarm?", "警報が鳴ったのですが、誤報だったのでしょうか？"),
    ],
    "郵便局での手続き": [
        ("I'd like to send this by registered mail.", "これを書留で送りたいのですが。"),
        ("Could I get tracking on this package?", "この荷物に追跡番号を付けていただけますか？"),
        ("I need this to arrive with a signature required.", "これは受け取りにサインが必要な形で送りたいです。"),
        ("How much would it cost to ship this overseas by air?", "これを航空便で海外に送るといくらかかりますか？"),
        ("What's the cheapest way to send this internationally?", "これを海外に送る一番安い方法は何ですか？"),
        ("Do I need to fill out a customs form for this?", "これには税関申告書の記入が必要ですか？"),
        ("What should I write for the customs declaration?", "税関申告書には何と書けばいいですか？"),
        ("Is this item allowed to be shipped overseas?", "これは海外に発送できるものですか？"),
        ("I'd like to rent a PO box.", "私書箱を借りたいのですが。"),
        ("How much is a PO box per year?", "私書箱は年間いくらですか？"),
        ("I'm moving — could you forward my mail to my new address?", "引っ越すので、郵便物を新しい住所に転送していただけますか？"),
        ("How long does mail forwarding take to set up?", "転送の手続きが有効になるまでどのくらいかかりますか？"),
        ("I got a notice that a package is being held for me.", "荷物が保管されているという不在票が届きました。"),
        ("I'd like to pick up this package, here's my slip.", "この荷物を受け取りたいのですが、こちらが不在票です。"),
        ("Could you redeliver this tomorrow instead?", "これを明日に再配達していただけますか？"),
        ("What time is the last pickup today?", "今日の最終集荷は何時ですか？"),
        ("How many days will it take to reach the US?", "アメリカに届くまで何日くらいかかりますか？"),
        ("Does this include express delivery?", "これは速達込みの料金ですか？"),
        ("Could I buy some padded envelopes?", "クッション封筒をいくつか購入できますか？"),
        ("I'd like to insure this package.", "この荷物に保険をかけたいのですが。"),
    ],
    "食料品店で買い物": [
        ("Do you carry gluten-free bread?", "グルテンフリーのパンは置いていますか？"),
        ("Where would I find soy sauce?", "醤油はどこにありますか？"),
        ("Is this a local specialty?", "これはこの地域の特産品ですか？"),
        ("What's this best eaten with?", "これは何と一緒に食べるのがおすすめですか？"),
        ("What's the best-before date on this?", "これの賞味期限はいつですか？"),
        ("Is this still good to eat?", "これはまだ食べられますか？"),
        ("Is this organic?", "これはオーガニックですか？"),
        ("Does this contain nuts?", "これにはナッツが入っていますか？"),
        ("Could you check the allergen label for me?", "アレルギー表示を確認していただけますか？"),
        ("Could I get a smaller portion of this cheese?", "このチーズをもう少し少なめに分けていただけますか？"),
        ("Could you cut me about 200 grams of that, please?", "それを200グラムくらい切っていただけますか？"),
        ("Could I get a bit more than that?", "もう少し多めにいただけますか？"),
        ("Do you sell things loose, without packaging?", "包装なしのばら売りはありますか？"),
        ("Do I need to pay for a bag?", "レジ袋は有料ですか？"),
        ("Do you have paper bags instead of plastic?", "ビニール袋の代わりに紙袋はありますか？"),
        ("Where do I return the shopping cart?", "カートはどこに返せばいいですか？"),
        ("Is there a deposit on this bottle?", "この瓶にはデポジットがかかっていますか？"),
        ("Do you have a loyalty card program?", "ポイントカードはありますか？"),
        ("Can I use my points today?", "今日、ポイントは使えますか？"),
        ("Is this on special this week?", "これは今週特売になっていますか？"),
    ],
    "雑貨屋で買い物": [
        ("I'm looking for a bottle opener — do you have one?", "栓抜きを探しているのですが、置いていますか？"),
        ("Do you sell storage boxes here?", "収納ボックスはこちらで売っていますか？"),
        ("Where would I find kitchen sponges?", "食器用スポンジはどこにありますか？"),
        ("Is this on the shelf over there, or in the back?", "これはあちらの棚にありますか、それとも奥にありますか？"),
        ("Do you have this in a different design?", "これは違うデザインもありますか？"),
        ("Could you recommend something for a housewarming gift?", "新築祝いに何かおすすめはありますか？"),
        ("What's popular with locals right now?", "今、地元の人たちに人気なのは何ですか？"),
        ("Do you offer gift-wrapping for an extra fee?", "追加料金でラッピングはしていただけますか？"),
        ("Can I return this if I've already opened the packaging?", "開封してしまった場合でも返品できますか？"),
        ("What's your return policy on opened items?", "開封済みの商品の返品規定はどうなっていますか？"),
        ("Is there a receipt required for returns?", "返品にはレシートが必要ですか？"),
        ("Do you have anything similar but cheaper?", "似たようなもので、もう少し安いものはありますか？"),
        ("Is this dishwasher safe?", "これは食洗機で洗えますか？"),
        ("Do you have this in a set?", "これはセットでの販売もありますか？"),
        ("Could you show me where the stationery is?", "文房具の場所を教えていただけますか？"),
    ],
    "お土産を買いに行く": [
        ("What's a popular souvenir from this area?", "この地域で人気のお土産は何ですか？"),
        ("What do locals usually buy as a gift?", "地元の人はよく何をお土産に買いますか？"),
        ("Do you have something individually wrapped?", "個包装になっているものはありますか？"),
        ("I need these individually packaged since they're for coworkers.", "職場に配るので、個包装のものが必要です。"),
        ("How long does this keep for?", "これはどのくらい日持ちしますか？"),
        ("Does this need to be refrigerated?", "これは冷蔵が必要ですか？"),
        ("Will this survive a two-day flight home?", "2日かかる帰りのフライトでも大丈夫ですか？"),
        ("Do you have a box with an assortment of flavors?", "いろいろな味が入った詰め合わせの箱はありますか？"),
        ("Could I get a mixed box of ten pieces?", "10個入りの詰め合わせをいただけますか？"),
        ("Is this okay to bring through customs?", "これは税関を通っても問題ないですか？"),
        ("Is this allowed in carry-on luggage?", "これは機内持ち込みできますか？"),
        ("Does this need to go in checked baggage?", "これは預け荷物にする必要がありますか？"),
        ("Do you have something around a thousand yen?", "1000円くらいのものはありますか？"),
        ("What would you recommend under two thousand yen?", "2000円以内でおすすめはありますか？"),
        ("I'm looking for something a bit more special, budget isn't an issue.", "予算は気にしないので、もう少し特別なものを探しています。"),
        ("Could you wrap these separately, they're for different people?", "それぞれ違う人へのものなので、別々に包んでいただけますか？"),
        ("Do you have a regional specialty I can't find elsewhere?", "他では手に入らないこの地域ならではのものはありますか？"),
        ("Is this made locally?", "これは地元で作られているものですか？"),
        ("Can I get this shipped directly to my hotel?", "これをホテルに直接配送してもらうことはできますか？"),
        ("Do you have a smaller size for a quick gift?", "ちょっとしたお礼用に、小さいサイズはありますか？"),
    ],
    "鉄道・駅": [
        ("Is there a left-luggage locker here?", "ここにコインロッカーはありますか？"),
        ("How much does a locker cost per day?", "ロッカーは1日いくらですか？"),
        ("I've lost something on the train — who do I ask?", "電車の中に忘れ物をしたのですが、どこに聞けばいいですか？"),
        ("Is there a lost-and-found office at this station?", "この駅に忘れ物取扱所はありますか？"),
        ("Could you check if anyone's turned in a black umbrella?", "黒い傘が届いていないか確認していただけますか？"),
        ("Attention passengers, the train bound for Shinjuku has been delayed.", "ご案内いたします、新宿行きの電車が遅れております。〔駅の放送〕"),
        ("Please refrain from running on the platform.", "ホームを走らないようご注意ください。〔駅の放送〕"),
        ("The elevator is out of service — please use the stairs.", "エレベーターが使用できません、階段をご利用ください。"),
    ],
}


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }

        added = skipped = 0
        per_scene: dict[str, int] = {}
        for scene, items in PHRASES_BY_SCENE.items():
            for en, ja in items:
                if en.lower() in existing:
                    skipped += 1
                    continue
                conn.execute(
                    "INSERT INTO phrases (english, japanese, scene) "
                    "VALUES (?, ?, ?)",
                    (en, ja, scene),
                )
                existing.add(en.lower())
                added += 1
                per_scene[scene] = per_scene.get(scene, 0) + 1

    print(f"phrases: +{added} (skipped {skipped})")
    for scene, n in per_scene.items():
        print(f"  {scene}: +{n}")
    with db() as conn:
        print("total phrases now:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
