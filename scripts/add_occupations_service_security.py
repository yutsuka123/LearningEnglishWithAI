# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""Add SERVICE / SECURITY occupation vocabulary, authored by Claude
(2026-08-06・ユーザー要望: 総務省日本標準職業分類の「E サービス職業従事者」
「F 保安職業従事者」を土台にした職業語彙の追加).

既存の domain='職業' には53語(firefighter, prison guard, bartender,
tailor, customs officer, concierge, flight attendant, housekeeper 等)が
既に存在する。このスクリプトはそこに、日本標準職業分類の

- E サービス職業従事者(理容・美容・エステ、家事・介護、接客、
  対人サービス関連)
- F 保安職業従事者(自衛官・警察官・海上保安官・消防員・
  その他の保安職業)

の枠組みを土台にした、まだDBに存在しない職業語彙を追加する。

追加前に既存DB(words ~7000件超)を全件チェックし、hairdresser /
beautician / lifeguard / detective / barista / bartender / tailor /
customs officer / concierge / flight attendant / housekeeper / usher /
taxi driver は既に(domain='職業'または他domainに)存在することを確認済み。
それらはこのリストから除外している。

domain は '職業' に統一。level は ["300-","300","350","400","450","500",
"550","600","650","700","750","800","850","900","950","990","990+"] の
スケールに沿って付与しており、日常的でなじみのある職業(waiter,
babysitter, police officer等)は350〜500、専門性・特殊性の高い職業
(crime scene investigator, undercover agent, correctional officer等)は
700〜800程度とした。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_occupations_service_security.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- E サービス職業従事者 (service occupations) ---
    ("barber", "理容師", "名詞", "The barber gave him a fresh haircut and a close shave.", "職業", "400"),
    ("masseur", "マッサージ師(男性)", "名詞", "The masseur worked out the tension in his shoulders.", "職業", "700"),
    ("masseuse", "マッサージ師(女性)", "名詞", "The masseuse gave her a relaxing back massage.", "職業", "700"),
    ("massage therapist", "マッサージ療法士", "名詞", "A licensed massage therapist can help relieve chronic back pain.", "職業", "650"),
    ("funeral director", "葬祭ディレクター(葬儀の運営・進行管理者)", "名詞", "The funeral director arranged every detail of the ceremony.", "職業", "700"),
    ("tour guide", "ツアーガイド", "名詞", "Our tour guide explained the history of the old castle.", "職業", "450"),
    ("wedding planner", "ウェディングプランナー", "名詞", "The wedding planner coordinated the venue, catering, and flowers.", "職業", "550"),
    ("babysitter", "ベビーシッター", "名詞", "We hired a babysitter for Saturday night.", "職業", "350"),
    ("caregiver", "介護者・世話をする人", "名詞", "She became her mother's full-time caregiver after the surgery.", "職業", "550"),
    ("elderly care worker", "高齢者介護士", "名詞", "An elderly care worker helps residents with their daily routines.", "職業", "600"),
    ("house cleaner", "ハウスクリーナー", "名詞", "A house cleaner comes twice a week to tidy the apartment.", "職業", "400"),
    ("dog groomer", "ドッグトリマー", "名詞", "The dog groomer trimmed the poodle's coat neatly.", "職業", "500"),
    ("chef", "シェフ・料理長", "名詞", "The chef designed a new seasonal menu for the restaurant.", "職業", "450"),
    ("waiter", "ウェイター", "名詞", "The waiter recommended the daily special.", "職業", "350"),
    ("waitress", "ウェイトレス", "名詞", "The waitress refilled our water glasses without being asked.", "職業", "350"),
    ("hotel receptionist", "ホテルの受付係", "名詞", "The hotel receptionist checked us in and handed over the key cards.", "職業", "500"),
    ("cook", "調理師・コック", "名詞", "He works as a cook in a busy hotel kitchen.", "職業", "400"),
    ("nail technician", "ネイリスト", "名詞", "The nail technician applied a fresh coat of gel polish.", "職業", "550"),
    ("spa therapist", "スパセラピスト", "名詞", "The spa therapist offers hot stone treatments on weekends.", "職業", "650"),
    ("bellhop", "ベルボーイ", "名詞", "The bellhop carried our luggage up to the room.", "職業", "600"),
    ("porter", "ポーター(荷物運搬係)", "名詞", "A porter helped load the bags onto the train.", "職業", "550"),
    ("chauffeur", "お抱え運転手・専属運転手", "名詞", "A chauffeur drove the executives to the airport.", "職業", "650"),
    ("valet", "バレット係(駐車代行係)", "名詞", "The valet parked our car right in front of the hotel entrance.", "職業", "650"),
    # --- F 保安職業従事者 (security / protective service occupations) ---
    ("police officer", "警察官", "名詞", "The police officer directed traffic after the accident.", "職業", "350"),
    ("security guard", "警備員", "名詞", "A security guard checks IDs at the front entrance.", "職業", "400"),
    ("bodyguard", "ボディーガード", "名詞", "The celebrity was surrounded by bodyguards at the event.", "職業", "500"),
    ("coast guard officer", "海上保安官", "名詞", "A coast guard officer rescued the crew from the sinking boat.", "職業", "700"),
    ("prison officer", "刑務官(施設の日常管理を担う保安職)", "名詞", "A prison officer supervises inmates and enforces the facility's rules.", "職業", "700"),
    ("private investigator", "私立探偵", "名詞", "The private investigator was hired to track down the missing documents.", "職業", "700"),
    ("crime scene investigator", "鑑識官・現場検証官", "名詞", "A crime scene investigator collected fingerprints from the window.", "職業", "750"),
    ("immigration officer", "入国審査官", "名詞", "The immigration officer stamped his passport at the airport.", "職業", "600"),
    ("traffic warden", "駐車違反取締官", "名詞", "A traffic warden issued a ticket for the illegally parked car.", "職業", "650"),
    ("crossing guard", "学童擁護員(横断歩道の誘導員)", "名詞", "The crossing guard helped children cross the street safely near the school.", "職業", "450"),
    ("police dog handler", "警察犬訓練士", "名詞", "A police dog handler trains dogs to detect drugs and explosives.", "職業", "750"),
    ("SWAT officer", "特殊部隊(SWAT)隊員", "名詞", "SWAT officers stormed the building to rescue the hostages.", "職業", "750"),
    ("undercover agent", "覆面捜査官・潜入捜査官", "名詞", "The undercover agent infiltrated the smuggling ring.", "職業", "800"),
    ("correctional officer", "矯正施設職員(刑務官の米国式呼称)", "名詞", "A correctional officer maintains order and safety inside the facility.", "職業", "700"),
    ("airport security screener", "空港保安検査員", "名詞", "The airport security screener checked every bag for prohibited items.", "職業", "600"),
    ("store detective", "私服保安員(万引き監視員)", "名詞", "A store detective quietly watches for shoplifters in the mall.", "職業", "700"),
]


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

    print(f"words: +{w_added} (skipped {w_skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
