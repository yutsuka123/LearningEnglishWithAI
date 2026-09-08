# ruff: noqa: E501  (data-heavy seed script: long phrase lines are fine)
"""Bulk-add curated phrases for「会話ニッチシーン追加」(2026-09-08ユーザー
ブレスト依頼)。一般的な英会話教材では薄いが実需要のある4シーンを新規追加
する。authored 2026-09-08, zero API cost (手作業で作成し、直接SQLiteに
投入する)。

## 投入前の重複調査で判明した重要事項(必読)
ユーザー依頼の原案は7シーン(角を立てない断り方/クレーム対応/値段交渉/
通院時の症状説明/TRPG/アマチュア無線/アニメ考察)だったが、投入前に
`phrases.scene`の既存一覧とサンプルを精査した結果、うち4件は既存シーンで
既にかなりの分量が手厚くカバー済みと判明したため、新規シーンの追加を
見送った(重複を避けるためのユーザー指示に従った判断)。詳細・根拠は
`docs/TODO.md`「フレーズ: 会話ニッチシーン追加」参照。

  - 角を立てない断り方 → 既存「やんわり断る英語」(29件、
    scripts/add_complaints_refusals.py)がほぼ同内容。ただし「営業・勧誘を
    断る」という切り口だけは既存29件に無かったため、それだけを新規
    シーン化した(下記シーン1)。
  - クレーム対応 → 既存「クレーム・抗議の英語」(42件、同スクリプト)は
    消費者側の視点のみ。店舗・サービス提供側の謝罪・対応の視点が
    存在しなかったため、そちらだけを新規シーン化した(下記シーン2)。
  - 通院時の症状説明 → 既存「医療(症状)の英語」(65件)・
    「医療(他)の英語」(41件、予約・受付・保険証・会計まで網羅)が
    非常に手厚い。ただし医師側が問診で尋ねる質問(いつから／10段階で
    痛みは／アレルギーは／内服薬は等)は既存に無かったため、それだけを
    新規シーン化した(下記シーン4)。
  - TRPGセッション中の会話 → 既存「TRPG・ボードゲーム英語」(29件)で
    GM/PLのやり取り・ダイスロール・ロールプレイ用語をすでに網羅。
    新規追加は見送り。
  - アマチュア無線交信 → 既存「アマチュア無線の交信」(72件)でQ符号・
    フォネティックコード・交信プロトコル・コンテスト・非常通信まで
    非常に広く正確にカバー済み。新規追加は見送り。
  - アニメ考察トーク → 既存「アニメ・海外ファン文化」(25件)＋
    「アニメ・視聴とファンダム作法」(26件)＋「アニメ・コンベンションと
    発信」(20件)の計71件で考察・実況・ファンダム作法まで網羅済み。
    新規追加は見送り。
  - 値段交渉 → 「買い物」に基本表現1〜2件、「海外オークション・
    コレクター英語」にオンラインオークション向けの交渉表現(reserve
    price/relist等)はあったが、フリマ・個人売買・対面でのカジュアルな
    値引き交渉は薄かったため新規シーン化した(下記シーン3)。オークション
    分野と表現が被らないよう文言を変えてある。

## 新規追加4シーン
  1. 営業・勧誘を断る英語 (22件)
     電話勧誘・訪問販売・メルマガ・取引先営業などを、感情的にならず
     丁寧かつ毅然と断る表現。社交的な誘い/依頼を断る既存シーンとは
     場面が異なる。
  2. クレーム対応(店舗側)の英語 (24件)
     店舗・サービス提供側として、苦情に対し謝罪し解決策を提示する
     視点の表現(消費者側は既存シーンでカバー済み)。
  3. 値段交渉(フリマ・個人売買)の英語 (28件)
     フリーマーケット・ガレージセール・個人間売買アプリでのカジュアルな
     値引き交渉。ビジネス商談のようなフォーマルな交渉、オンライン
     オークションの入札関連表現とは重複しないよう配慮。
  4. 受診時のやり取り(問診)の英語 (22件)
     医師が患者に症状を尋ねる問診の定型質問+簡単な診断・指示。
     薬剤名・用量など裏取りが必要な専門的事実には踏み込まず、一般的な
     問診の型のみを扱う(誤情報リスクを避けるため)。

感情が絡む内容(クレーム対応・断り方)は、攻撃的・失礼にならないよう
両論を尊重するトーンで統一した(ユーザー指示どおり)。

No app / OpenAI API calls — everything is hand-written and inserted
directly into the SQLite DB. Duplicates are skipped by english
(lowercased).

Run:  python scripts/add_conversation_niches.py

仕上げ:
  python scripts/relevel_phrases.py                      # 難易度再設定
  python scripts/import_phrase_details.py \
      scripts/data/conversation_niches_details.json       # detail投入
  python scripts/build_audio_by_scene.py --scene "営業・勧誘を断る英語" \
      --scene "クレーム対応(店舗側)の英語" \
      --scene "値段交渉(フリマ・個人売買)の英語" \
      --scene "受診時のやり取り(問診)の英語"              # 音声生成(新規分のみ)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "営業・勧誘を断る英語": [
        ("No thank you, I'm not interested.", "結構です、興味はありません。"),
        ("I appreciate you stopping by, but we're all set.", "わざわざありがとうございます、でも間に合っています。"),
        ("We're happy with our current provider, thanks.", "今の契約先で満足していますので、大丈夫です。"),
        ("Could you take my number off your call list, please?", "電話リストから私の番号を外していただけますか。"),
        ("I'm not in a position to make a decision today.", "今日は決められる立場にありません。"),
        ("Please don't call this number again.", "もうこの番号にはお電話しないでください。"),
        ("I'll have to say no, but thanks for the information.", "お断りしますが、ご説明ありがとうございました。"),
        ("We don't accept unsolicited sales calls at this number.", "この番号では、依頼していない営業電話はお断りしています。"),
        ("I'd rather not sign anything on the spot.", "その場でサインするのはご遠慮したいです。"),
        ("Can you send me something in writing instead?", "代わりに書面で送っていただけますか。"),
        ("I'm going to pass on the extended warranty.", "延長保証は見送ります。"),
        ("No, I don't want to upgrade my plan right now.", "いいえ、今はプランのアップグレードは希望しません。"),
        ("I'm not the person who handles these decisions.", "こういった決定を担当しているのは私ではありません。"),
        ("We already have someone who does that for us.", "それはすでに別の業者にお願いしています。"),
        ("I'm going to have to stop you there — we're not interested.", "申し訳ありませんが、そこで止めさせてください。興味はありません。"),
        ("Please remove me from your mailing list.", "メーリングリストから外してください。"),
        ("I get a lot of these calls, so I have a rule of saying no.", "こういう電話はよくかかってくるので、断ると決めています。"),
        ("Thanks, but we don't do cold calls here.", "ありがとうございます、でもここでは飛び込み営業はお断りしています。"),
        ("I'm not comfortable buying anything at the door.", "訪問販売でものを買うのは抵抗があります。"),
        ("If I'm interested later, I'll reach out myself.", "興味が出たら、こちらから連絡します。"),
        ("I hear this pitch a lot, so I'll pass this time.", "その説明はよく聞くので、今回は遠慮しておきます。"),
        ("We're not taking on new vendors this year.", "今年は新しい取引先の受け入れはしていません。"),
    ],
    "クレーム対応(店舗側)の英語": [
        ("I'm so sorry for the trouble this has caused you.", "このたびはご迷惑をおかけして誠に申し訳ございません。"),
        ("Let me look into this for you right away.", "すぐに確認させていただきます。"),
        ("You're absolutely right, and I apologize for the mistake.", "おっしゃる通りです、ミスをお詫び申し上げます。"),
        ("Let me see what I can do to make this right.", "どうすれば解決できるか、確認いたします。"),
        ("I completely understand your frustration.", "お気持ちはよく分かります。"),
        ("We'd like to offer you a full refund for the inconvenience.", "ご迷惑のお詫びとして全額返金させていただきます。"),
        ("Would a replacement work for you, or would you prefer a refund?", "交換と返金、どちらがよろしいでしょうか。"),
        ("I'll personally make sure this doesn't happen again.", "今後このようなことがないよう、私が責任を持って対応いたします。"),
        ("Thank you for bringing this to our attention.", "お知らせいただきありがとうございます。"),
        ("Let me get my manager, who can help resolve this.", "対応できる責任者を呼んでまいります。"),
        ("I apologize for the delay — let me explain what happened.", "遅れにつきましてお詫びいたします、経緯をご説明させてください。"),
        ("We take full responsibility for this error.", "この件については全面的に当方の責任です。"),
        ("Is there anything else I can do to fix this for you?", "ほかに何かできることはございますか。"),
        ("I'll follow up with you personally by tomorrow.", "明日までに私から改めてご連絡いたします。"),
        ("We'll cover the cost of the repair.", "修理費用はこちらで負担いたします。"),
        ("I'm going to escalate this to make sure it gets handled quickly.", "早急に対応されるよう、上に報告いたします。"),
        ("Please accept this discount as an apology for the inconvenience.", "お詫びの印として、こちらの割引をお受け取りください。"),
        ("I understand why you're upset, and I'd feel the same way.", "ご立腹なのはもっともです、私も同じ立場ならそう感じます。"),
        ("Let's find a solution that works for you.", "ご納得いただける解決策を一緒に探しましょう。"),
        ("We'll make sure your next visit goes more smoothly.", "次回のご来店ではスムーズにご案内できるようにいたします。"),
        ("I'd like to give you a call back once I have an update.", "進捗がございましたら、折り返しお電話いたします。"),
        ("That should never have happened, and I'm sorry it did.", "あってはならないことでした、申し訳ございません。"),
        ("Here's my direct contact in case this happens again.", "もしまた何かございましたら、こちらが私の直通の連絡先です。"),
        ("We appreciate your patience while we sort this out.", "解決するまでの間、ご辛抱いただきありがとうございます。"),
    ],
    "値段交渉(フリマ・個人売買)の英語": [
        ("Would you take 20 dollars for this?", "これ、20ドルでどうですか。"),
        ("Is that your final price?", "それが最終的なお値段ですか。"),
        ("I could do 15 if you can come down a little.", "もう少し下げていただければ15ドルでいいです。"),
        ("That's a bit steep for me — can we work something out?", "私にはちょっと高いです、何とかなりませんか。"),
        ("I'll give you cash right now if you knock off a few dollars.", "少し値引きしていただければ、今すぐ現金でお支払いします。"),
        ("What's the lowest you'd go on this?", "これ、一番安くしてもらえる価格はいくらですか。"),
        ("If I buy the whole set, can you give me a better deal?", "セットで全部買ったら、もっと安くしてもらえますか。"),
        ("I noticed a small scratch — would you take a bit less for it?", "小さな傷があるので、少し安くしてもらえますか。"),
        ("I really like it, but it's out of my budget at that price.", "とても気に入っていますが、その値段だと予算オーバーです。"),
        ("Let me think about it — could you hold it for me?", "少し考えさせてください、取り置きしてもらえますか。"),
        ("I'll take it if you can throw in the extra cable.", "予備のケーブルも付けてもらえるなら買います。"),
        ("Sorry, that price is firm — I can't go any lower.", "すみません、その価格は決まっていて、これ以上下げられません。"),
        ("I could let it go for 30, but that's as low as I can go.", "30ドルまでなら下げられますが、それが限界です。"),
        ("I'm willing to negotiate a little, but not by much.", "少しなら交渉に応じますが、大幅には無理です。"),
        ("How about we split the difference?", "お互い歩み寄って中間の値段にしませんか。"),
        ("It's already priced to sell, honestly.", "正直、もう十分お買い得な値段にしています。"),
        ("I found the same item cheaper somewhere else — can you match that?", "他で同じ商品をもっと安く見つけたのですが、その価格に合わせてもらえますか。"),
        ("If you can pick it up today, I'll take 25.", "今日中に取りに来てもらえるなら25ドルにします。"),
        ("I'm not going to haggle over a couple of dollars.", "数ドルの差でごちゃごちゃ言うつもりはありません。"),
        ("Cash only, and the price is non-negotiable.", "現金のみで、価格交渉はご遠慮ください。"),
        ("Would you consider trading instead of selling?", "売る代わりに交換、というのはどうですか。"),
        ("That seems fair — I'll take it at that price.", "それなら妥当ですね、その値段で買います。"),
        ("I'm on a tight budget, so anything you can do would help.", "予算があまりないので、少しでも安くしていただけると助かります。"),
        ("Let's call it 40 and shake on it.", "40ドルということで決めましょう。"),
        ("I can throw in free delivery if you pay the asking price.", "表示価格のままなら、配送は無料にします。"),
        ("Sorry, I already agreed on a price with someone else.", "すみません、もう別の方と値段が決まってしまいました。"),
        ("Could you give me a rough estimate before I decide?", "決める前に、おおよその見積もりをいただけますか。"),
        ("Is there any flexibility in your quote?", "お見積もりに融通は利きますか。"),
    ],
    "受診時のやり取り(問診)の英語": [
        ("When did the symptoms start?", "症状はいつから始まりましたか。"),
        ("How long have you had this pain?", "この痛みはどのくらい続いていますか。"),
        ("On a scale of one to ten, how would you rate the pain?", "痛みを1から10で表すとどのくらいですか。"),
        ("Does the pain come and go, or is it constant?", "痛みは出たり消えたりしますか、それともずっと続いていますか。"),
        ("Have you had this kind of pain before?", "以前にもこのような痛みがありましたか。"),
        ("Are you currently taking any medication?", "現在服用しているお薬はありますか。"),
        ("Do you have any allergies to medication?", "お薬のアレルギーはありますか。"),
        ("Does anything make the pain better or worse?", "何かすると痛みが良くなったり悪くなったりしますか。"),
        ("Have you noticed any other symptoms along with this?", "これと一緒に他の症状はありませんか。"),
        ("Has anyone in your family had something similar?", "ご家族にも同じようなことがありましたか。"),
        ("I'm going to check your temperature and blood pressure.", "体温と血圧を測らせていただきますね。"),
        ("Take a deep breath for me, please.", "深呼吸をしてください。"),
        ("Let me know if it hurts when I press here.", "ここを押して痛かったら教えてください。"),
        ("We'll need to run a few tests to be sure.", "確認のためいくつか検査が必要です。"),
        ("It looks like a mild case of the flu.", "軽いインフルエンザのようですね。"),
        ("I'm going to prescribe something to help with the symptoms.", "症状を和らげるお薬を処方しますね。"),
        ("Come back if it doesn't improve in a few days.", "数日で良くならなければまた来てください。"),
        ("Is there anything else that's been bothering you?", "他に気になることはありますか。"),
        ("Have you been under a lot of stress lately?", "最近ストレスが多いですか。"),
        ("Let's schedule a follow-up in two weeks.", "2週間後にフォローアップの予約を入れましょう。"),
        ("I'd like to refer you to a specialist just to be safe.", "念のため専門医をご紹介したいと思います。"),
        ("It's nothing serious, but let's keep an eye on it.", "深刻なものではありませんが、様子を見ましょう。"),
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
        conn.commit()

    print(f"phrases: +{added} (skipped {skipped})")
    for scene, n in per_scene.items():
        print(f"  {scene}: +{n}")
    with db() as conn:
        print("total phrases:",
              conn.execute("SELECT COUNT(*) FROM phrases").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
