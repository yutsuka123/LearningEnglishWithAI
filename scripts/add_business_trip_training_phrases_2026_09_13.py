# ruff: noqa: E501  (data-heavy seed script: long phrase lines are fine)
"""Add two new phrase scenes for overseas business-trip / training scenarios
(`docs/TODO.md` backlog items B14「海外出張・工場視察の英語」+
B15「海外研修・資格講習の英語」、2026-09-13対応)。

## 2シーンの狙い
- **海外出張・工場視察の英語**: 海外の工場を訪問するビジネスパーソン・
  エンジニアが実際に使う「渡航・訪問」に紐づくフレーズ。訪問日程の調整、
  工場入場時の安全説明・PPE、通訳を介した/直接のライン状況確認、
  設備の試運転(コミッショニング)立ち会い、訪問中の相手先との雑談、
  展示会ブースでの応対・名刺交換・フォローアップまでをカバーする。
- **海外研修・資格講習の英語**: 海外での複数日にわたる研修・資格講習に
  参加する側のフレーズ。会場での受付、講師への聞き返し・確認、グループ
  ワーク/ブレイクアウトセッション、試験形式・合格基準の確認、修了証・
  成績証明書の依頼、休憩時間の他の参加者とのネットワーキングをカバーする。

## 重複調査(投入前に実施済み・詳細はコミットメッセージ/セッション記録参照)
- 既存の「工場・製造現場の英語」(15件)は5S/アンドン/自働化/MUDA等の
  **工場現場の語彙そのもの**であり、出張・訪問という切り口のフレーズは
  含まれていないため重複なし。
- 既存の「現場設備デバッグ・安全確認」(14件)は配線確認・ロックアウト・
  アラーム原因確認等の**設備デバッグの実務フレーズ**であり、今回の
  「初回電源投入への立ち会い」「受入試験合格後のサインオフ」「メーカー
  エンジニアの現地サポート」といった**訪問側から見たコミッショニングの
  節目**のフレーズとは切り口が異なるため重複なし。
- 既存の「品質調査・海外サプライヤー対応」(53件)は不具合の根本原因分析・
  4M変化点・流出防止処置等の**深い品質調査の議論**であり、今回の
  「ラインの遅れの原因を尋ねる」程度の軽い切り口とは重複しない。
- 既存の「試験の手続き英語」(38件)・「試験の指示・出題フレーズ」(48件)は
  学校/資格試験一般の申込・出題手順であり、海外研修に参加している最中の
  講師とのやり取りやグループワークのフレーズは含まれていないため重複なし。
- 既存の「外交・国際交渉」(163件)は外交・国際交渉レジスターであり、
  工場視察・研修参加という切り口とは重ならないことを確認済み。
- 投入前に全7,654件の`english`(小文字化)と本バッチ46件を突き合わせ、
  完全一致の重複はゼロ、バッチ内の重複もゼロであることを確認済み。

No app / OpenAI API calls — everything is hand-written and inserted
directly into the SQLite DB. Duplicates are skipped by english
(lowercased), matching the pattern in `scripts/add_jokes.py`.

Run:  python scripts/add_business_trip_training_phrases_2026_09_13.py

仕上げ:
  python scripts/import_phrase_details.py \
      scripts/data/business_trip_training_phrase_details_2026_09_13.json
  python scripts/relevel_phrases.py            # 難易度再設定
  .venv/bin/python scripts/build_audio.py      # 音声生成(少しずつ)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

PHRASES_BY_SCENE: dict[str, list[tuple[str, str]]] = {
    "海外出張・工場視察の英語": [
        ("Could you send us the visit itinerary at least a week in advance?",
         "視察の日程表を、少なくとも1週間前までにお送りいただけますか。"),
        ("We'd like to confirm the schedule for the plant tour on Tuesday.",
         "火曜日の工場見学のスケジュールを確認させていただきたいのですが。"),
        ("Who will be our main point of contact during the site visit?",
         "現地訪問中の主な窓口はどなたになりますか。"),
        ("Is there a dress code we should be aware of before the visit?",
         "訪問前に知っておくべき服装の規定はありますか。"),
        ("Before we go onto the shop floor, we'll walk you through the safety briefing.",
         "現場に入る前に、安全に関する説明をさせていただきます。"),
        ("Safety glasses and earplugs are required in this area.",
         "このエリアでは保護メガネと耳栓の着用が必須です。"),
        ("In case of an emergency, please follow the yellow evacuation route painted on the floor.",
         "緊急時は、床に描かれた黄色い避難経路に従ってください。"),
        ("Photography is not permitted in this section of the plant.",
         "工場のこのエリアでは撮影は禁止されています。"),
        ("Could you ask him what's causing the delay on this line?",
         "このラインの遅れの原因を彼に聞いていただけますか。"),
        ("Would it be possible to speak with the line supervisor directly?",
         "ライン責任者と直接お話しすることは可能でしょうか。"),
        ("Sorry, could you say that more slowly? I want to make sure the interpreter catches every detail.",
         "すみません、もう少しゆっくり話していただけますか。通訳の方が細部まで正確に伝えられるようにしたいので。"),
        ("Is something getting lost in translation? Let me try rephrasing that.",
         "何か訳す際にニュアンスが失われていませんか。別の言い方をしてみます。"),
        ("We're ready to power on the equipment for the first time — is everyone clear of the machine?",
         "いよいよ設備の初回電源投入です――皆さん機械から十分離れていますか。"),
        ("The vendor engineer will be on-site to support the commissioning process.",
         "試運転(コミッショニング)にはメーカーのエンジニアが現地でサポートしてくれます。"),
        ("Once the acceptance test passes, we'll sign off on the handover documents.",
         "受入試験に合格したら、引き渡し書類にサインします。"),
        ("Could you have the operators trained on this new line before we leave?",
         "私たちが帰国する前に、この新ラインのオペレーター教育を済ませていただけますか。"),
        ("How long have you been working at this plant?",
         "この工場ではどのくらい働いていらっしゃるんですか。"),
        ("This is my first time visiting your country — do you have any recommendations for local food?",
         "御国を訪れるのは今回が初めてなのですが、おすすめの地元料理はありますか。"),
        ("Thank you for taking the time to show us around today.",
         "本日はお時間を割いてご案内いただき、ありがとうございました。"),
        ("We really appreciate the hospitality during our stay.",
         "滞在中は温かいおもてなしを本当にありがとうございました。"),
        ("Welcome to our booth — would you like a quick demo of our product?",
         "ブースへようこそ――弊社製品の簡単なデモをご覧になりますか。"),
        ("Here's my business card — please feel free to reach out with any questions.",
         "私の名刺です――ご質問があればいつでもご連絡ください。"),
        ("What industry are you in, if you don't mind me asking?",
         "差し支えなければ、どのような業界にいらっしゃるか伺ってもよろしいですか。"),
        ("We'll follow up with more detailed materials after the show.",
         "展示会の後で、より詳しい資料をお送りいたします。"),
        ("Thank you for stopping by — it was great talking with you.",
         "お立ち寄りいただきありがとうございました――お話しできて良かったです。"),
    ],
    "海外研修・資格講習の英語": [
        ("Hi, I'm here for the certification course — where do I check in?",
         "こんにちは、認定講習に参加するために来ました――受付はどちらですか。"),
        ("Could you tell me which room the training starts in?",
         "研修が始まる教室はどちらか教えていただけますか。"),
        ("Is there a Wi-Fi password we can use during the course?",
         "講習中に使えるWi-Fiのパスワードはありますか。"),
        ("Sorry, could you repeat that last part?",
         "すみません、最後の部分をもう一度言っていただけますか。"),
        ("Would you mind slowing down a little? I want to take notes.",
         "少しゆっくり話していただけますか。メモを取りたいので。"),
        ("Could you give us an example to make that clearer?",
         "それをもう少し分かりやすくするための例を挙げていただけますか。"),
        ("I'm sorry, I didn't quite follow that — could you explain it a different way?",
         "すみません、少し理解が追いつかなかったので、別の説明の仕方をしていただけますか。"),
        ("Let's split into groups of four for this exercise.",
         "この演習では4人ずつのグループに分かれましょう。"),
        ("Who would like to be the group's spokesperson for the report-back?",
         "発表担当として、グループの代表になってくれる人はいますか。"),
        ("We're running a bit behind — can we get five more minutes for the group discussion?",
         "少し予定より遅れているのですが、グループディスカッションにあと5分いただけますか。"),
        ("Let's compare answers before we present them to the whole class.",
         "クラス全体に発表する前に、答えを照らし合わせておきましょう。"),
        ("How is the final assessment structured — is it written, practical, or both?",
         "最終評価はどのような形式ですか――筆記ですか、実技ですか、それとも両方ですか。"),
        ("What score do we need to pass the certification exam?",
         "資格試験に合格するには何点必要ですか。"),
        ("Is there a retake option if we don't pass on the first attempt?",
         "一度目で合格しなかった場合、再受験の機会はありますか。"),
        ("Could I get a certificate of completion once I finish the course?",
         "講習を修了したら、修了証明書をいただけますか。"),
        ("How long does it usually take to receive the official transcript?",
         "正式な成績証明書が届くまで、通常どのくらいかかりますか。"),
        ("Will the certificate be issued in both English and Japanese?",
         "証明書は英語と日本語の両方で発行されますか。"),
        ("Mind if I join you for coffee during the break?",
         "休憩中、ご一緒してコーヒーをいただいても構いませんか。"),
        ("Where are you all traveling from for this course?",
         "皆さんはこの講習のためにどちらからいらっしゃったんですか。"),
        ("It's nice to meet other people in the same field — could we exchange contact information?",
         "同じ分野の方々とお会いできて嬉しいです――連絡先を交換してもよろしいですか。"),
        ("Are you planning to attend the follow-up session next year as well?",
         "来年のフォローアップ講習にも参加されるご予定ですか。"),
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
