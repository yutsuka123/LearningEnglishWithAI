# ruff: noqa: E501  (data-heavy seed script: long word/phrase lines are fine)
"""Add a new "災害" domain/scene: vocabulary and phrases for disaster
*response* — the human and social side of disasters (volunteering,
dispatch, evacuation life, recovery) — authored by Claude (2026-08-10・
ユーザー要望).

## 既存2ドメインとの住み分け
- `地学`ドメインには自然現象そのもの(`earthquake`は`科学`、`tsunami`・
  `torrential rain`・`landslide`・`drought`・`heat wave`等は既に`地学`に
  収録済み)が入っている。本スクリプトはそれらを**重複追加しない**。
- `防災工学`ドメインには防災インフラ・工学的対策(`hazard map`、
  `flood control`、`tsunami wall`、`storm surge barrier`、
  `evacuation route`/`evacuation drill`、`emergency shelter`等)が入って
  いる。
- 本スクリプトの`災害`ドメインは、上記どちらでもない**人・社会の側面**
  (災害対応・ボランティア活動・自衛隊派遣・避難生活・復興)を扱う。
  未収録の災害種別(`wildfire`・`heavy rain`・`heavy snowfall`・
  `cold wave`・`blizzard`・`mudslide`等)もあわせて収録する。
- `earthquake`(科学)、`disaster`・`flood`(domain空欄)、`evacuate`
  (ニュース)、`casualty`(軍事)、`victim`(サスペンス)、`magnitude`
  (天文)、`tsunami`・`torrential rain`(地学)は既存語として扱い、
  重複追加しない。

対象語彙: 災害種別(山火事、大雨、豪雪、寒波、猛吹雪、自然災害、浸水、
土石流)、ボランティア・災害派遣(災害ボランティア、ボランティアセンタ
ー、災害派遣、自衛隊派遣、救援物資、募金活動、復興活動、災害対応チー
ム、捜索救助)、避難生活(避難所、避難者、被災者、行方不明者、防災グッ
ズ、非常用物資、災害義援金、仮設住宅、災害宣言、避難指示、断水)、その
他(被災地、支援活動員、救援活動、災害管理、人道支援、相互扶助、非常持
ち出し袋、災害救援、復旧活動、初動対応者)。

フレーズはボランティアに参加する・被災地の様子を伝える・避難情報を案
内する等、実際に使う自然な英語表現("Where is the nearest evacuation
center?" "Please evacuate to higher ground immediately." など)。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_disaster_response.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 災害種別(未収録のもの) ---
    ("wildfire", "山火事", "名詞", "The wildfire spread quickly through the dry forest.", "災害", "500"),
    ("heavy rain", "大雨(警報級の強い雨)", "名詞", "Heavy rain is expected across the region tonight.", "災害", "400"),
    ("heavy snowfall", "大雪・豪雪", "名詞", "Heavy snowfall closed several highways overnight.", "災害", "500"),
    ("cold wave", "寒波", "名詞", "A cold wave is expected to hit the country next week.", "災害", "550"),
    ("blizzard", "猛吹雪", "名詞", "The blizzard made it impossible to see more than a few meters ahead.", "災害", "600"),
    ("natural disaster", "自然災害", "名詞", "Japan experiences many kinds of natural disasters every year.", "災害", "450"),
    ("flooding", "浸水・洪水被害", "名詞", "The flooding damaged hundreds of homes near the river.", "災害", "500"),
    ("mudslide", "土石流", "名詞", "A mudslide blocked the mountain road after the heavy rain.", "災害", "650"),
    # --- ボランティア・災害派遣 ---
    ("disaster relief volunteer", "災害ボランティア", "名詞", "She signed up as a disaster relief volunteer after the flood.", "災害", "600"),
    ("volunteer center", "ボランティアセンター", "名詞", "You can register at the volunteer center near the town hall.", "災害", "550"),
    ("disaster relief dispatch", "災害派遣", "名詞", "The prefecture requested a disaster relief dispatch from neighboring cities.", "災害", "700"),
    ("self-defense force deployment", "自衛隊派遣", "名詞", "The self-defense force deployment began within hours of the earthquake.", "災害", "750"),
    ("relief supplies", "救援物資", "名詞", "Trucks carrying relief supplies arrived at the shelter this morning.", "災害", "550"),
    ("donation drive", "募金活動", "名詞", "The school organized a donation drive for the affected families.", "災害", "600"),
    ("rebuilding effort", "復興活動", "名詞", "The rebuilding effort is expected to take several years.", "災害", "600"),
    ("disaster response team", "災害対応チーム", "名詞", "A disaster response team was sent to assess the damage.", "災害", "600"),
    ("search and rescue", "捜索救助", "名詞", "Search and rescue teams worked through the night to find survivors.", "災害", "550"),
    # --- 避難生活 ---
    ("evacuation center", "避難所(避難者が集まる場所)", "名詞", "Where is the nearest evacuation center from here?", "災害", "450"),
    ("evacuee", "避難者", "名詞", "The evacuees were given blankets and hot meals.", "災害", "500"),
    ("disaster victim", "被災者", "名詞", "Volunteers handed out food and water to disaster victims.", "災害", "500"),
    ("missing person", "行方不明者", "名詞", "Rescue crews are still searching for several missing persons.", "災害", "500"),
    ("disaster preparedness kit", "防災グッズ・非常持ち出し袋", "名詞", "Every household should keep a disaster preparedness kit ready.", "災害", "600"),
    ("emergency supplies", "非常用物資", "名詞", "We keep three days of emergency supplies at home.", "災害", "500"),
    ("disaster relief fund", "災害義援金", "名詞", "The disaster relief fund has already raised over ten million yen.", "災害", "650"),
    ("temporary housing", "仮設住宅", "名詞", "Many evacuees are still living in temporary housing a year later.", "災害", "550"),
    ("disaster declaration", "災害宣言", "名詞", "The governor issued a disaster declaration for the coastal area.", "災害", "700"),
    ("evacuation order", "避難指示", "名詞", "An evacuation order was issued for residents near the river.", "災害", "550"),
    ("water shortage", "断水・水不足", "名詞", "The water shortage forced the city to distribute bottled water.", "災害", "500"),
    # --- その他 ---
    ("disaster area", "被災地", "名詞", "Volunteers from all over the country traveled to the disaster area.", "災害", "450"),
    ("aid worker", "支援活動員", "名詞", "Aid workers distributed food and medicine to the affected village.", "災害", "550"),
    ("relief operation", "救援活動", "名詞", "The relief operation continued for several weeks after the typhoon.", "災害", "650"),
    ("disaster management", "災害管理・防災危機管理", "名詞", "The city improved its disaster management plan after the flood.", "災害", "700"),
    ("humanitarian aid", "人道支援", "名詞", "International humanitarian aid arrived within two days of the disaster.", "災害", "650"),
    ("mutual aid", "相互扶助", "名詞", "Neighbors relied on mutual aid when the roads were blocked.", "災害", "750"),
    ("go-bag", "非常持ち出し袋(すぐ持ち出せる防災バッグ)", "名詞", "Keep a go-bag by the front door in case you need to leave quickly.", "災害", "650"),
    ("disaster relief", "災害救援", "名詞", "The organization has provided disaster relief for over twenty years.", "災害", "500"),
    ("recovery effort", "復旧活動", "名詞", "The recovery effort focused first on restoring water and electricity.", "災害", "550"),
    ("first responder", "初動対応者(緊急対応要員)", "名詞", "First responders reached the scene within minutes of the earthquake.", "災害", "600"),
]

PHRASES: list[tuple[str, str]] = [
    ("I'd like to volunteer at the disaster area.", "被災地でボランティア活動をしたいのですが。"),
    ("Where is the nearest evacuation center?", "一番近い避難所はどこですか？"),
    ("Please evacuate to higher ground immediately.", "直ちに高台へ避難してください。"),
    ("The city has issued an evacuation order for this area.", "市はこの地域に避難指示を出しました。"),
    ("We are collecting relief supplies for the evacuees.", "避難者のための救援物資を集めています。"),
    ("How can I sign up at the volunteer center?", "ボランティアセンターにはどうやって登録すればいいですか？"),
    ("The self-defense force was deployed to help with the rescue operation.", "自衛隊が救助活動の支援のため派遣されました。"),
    ("Many roads are still closed due to the flooding.", "浸水の影響で多くの道路がまだ通行止めです。"),
    ("Is your family safe after the earthquake?", "地震のあと、ご家族はご無事ですか？"),
    ("We're still trying to locate several missing persons.", "数名の行方不明者をまだ捜索しています。"),
    ("The town is slowly recovering from the disaster.", "町は災害からゆっくりと復興しつつあります。"),
    ("Please prepare a disaster preparedness kit in case of emergency.", "万一に備えて防災グッズを準備しておいてください。"),
    ("Donations can be dropped off at the community center.", "寄付は公民館で受け付けています。"),
    ("The evacuees are currently staying in temporary housing.", "避難者は現在、仮設住宅で生活しています。"),
    ("Search and rescue teams worked through the night.", "捜索救助チームは夜通し作業を続けました。"),
    ("We need more hands to distribute the relief supplies.", "救援物資を配るのにもっと人手が必要です。"),
    ("The disaster relief fund has raised over ten million yen.", "災害義援金は1000万円以上集まりました。"),
    ("Local volunteers helped clear debris from the flooded homes.", "地元のボランティアが浸水した家屋のがれき撤去を手伝いました。"),
    ("The area was declared a disaster zone yesterday.", "その地域は昨日、被災地に指定されました。"),
    ("Please stay tuned to the radio for evacuation updates.", "避難情報についてはラジオで最新情報を確認してください。"),
    ("Aid workers are distributing food and water to the victims.", "支援活動員が被災者に食料と水を配布しています。"),
    ("The wildfire forced thousands of residents to evacuate.", "山火事のため、数千人の住民が避難を余儀なくされました。"),
    ("We're organizing a donation drive for the affected families.", "被災した家族のための募金活動を企画しています。"),
    ("It's important to check on your elderly neighbors during a cold wave.", "寒波の間はご近所の高齢の方の様子を確認することが大切です。"),
    ("The rebuilding effort will take several years.", "復興作業には数年かかるでしょう。"),
    ("Please bring your own gloves if you're volunteering for cleanup.", "清掃ボランティアに参加する場合は、ご自身の手袋をご持参ください。"),
]


def main() -> int:
    with db() as conn:
        existing_words = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing_words:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing_words.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")

    with db() as conn:
        existing_phrases = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        p_added = p_skipped = 0
        for en, ja in PHRASES:
            if en.lower() in existing_phrases:
                p_skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, '災害・防災の英語')",
                (en, ja),
            )
            existing_phrases.add(en.lower())
            p_added += 1
    print(f"phrases: +{p_added} (skipped {p_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
