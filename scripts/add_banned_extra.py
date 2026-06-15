# ruff: noqa: E501
"""Enrich the "禁止用語" category (HIDDEN by default, excluded from quizzes):
vulgar/profanity, movie-violence, and drug terms — for COMPREHENSION and
self-protection only (understand media, know what to avoid). Each entry is a
term + Japanese meaning + warning; the English "example" is a neutral warning,
NOT a usage example. No instructions, no drug manufacture/usage guidance.
Authored by Claude — no app/OpenAI API calls. domain="禁止用語", hidden by the
existing banned filter. Run: python scripts/add_banned_extra.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WARN = "This word is offensive or sensitive — understand it, but do not use it."
WARN_DRUG = "This is a drug-related term; learn to recognize it, not to use it."
WARN_VIOL = "Violent media term — for comprehension only."

# (english, japanese)  ※example は警告文を一律付与
PROFANITY: list[tuple[str, str]] = [
    ("damn", "ちくしょう・くそ〔軽い罵り。下品〕"),
    ("hell (swear)", "くそっ・ちくしょう〔罵り〕"),
    ("crap", "くそ・がらくた〔下品な俗語〕"),
    ("piss off", "失せろ・うんざりさせる〔非常に無礼〕"),
    ("bastard", "野郎・ろくでなし〔強い侮辱〕"),
    ("son of a bitch", "この野郎・くそったれ〔強い罵り〕"),
    ("jerk", "嫌な奴・まぬけ〔侮辱〕"),
    ("scumbag", "クズ野郎〔強い侮辱〕"),
    ("douchebag", "嫌な奴・最低の奴〔下品な侮辱〕"),
    ("screw you", "くたばれ・ふざけるな〔無礼〕"),
    ("shut up", "黙れ〔失礼・強い命令〕"),
    ("freaking", "くそ〜・めちゃくちゃ〔強調の俗語・やや下品〕"),
]

VULGAR: list[tuple[str, str]] = [
    ("vulgar", "下品な・卑猥な", ),
    ("obscene", "わいせつな・卑猥な"),
    ("profanity", "冒涜的な言葉・口汚い言葉"),
    ("swear word", "罵り言葉・汚い言葉"),
    ("curse word", "罵り言葉"),
    ("slur", "侮蔑語・差別的な蔑称〔他者を傷つける語〕"),
    ("innuendo", "性的なほのめかし・あてこすり"),
    ("explicit", "露骨な・性的に明白な〔表現の警告に使う〕"),
    ("crude", "粗野な・露骨な"),
    ("filthy", "下品な・汚らわしい"),
    ("perverted", "変態的な・倒錯した"),
    ("lewd", "みだらな・好色な"),
]

VIOLENCE: list[tuple[str, str]] = [
    ("corpse", "死体"),
    ("gore", "(流血の)惨状・血のり"),
    ("bloodshed", "流血(の惨事)"),
    ("massacre", "虐殺(する)"),
    ("slaughter", "(大量)殺戮・畜殺(する)"),
    ("carnage", "大虐殺・殺戮"),
    ("mutilate", "(体を)切断する・損なう"),
    ("decapitate", "斬首する"),
    ("torture", "拷問(する)"),
    ("brutal", "残忍な・容赦ない"),
    ("savage", "獰猛な・残忍な"),
    ("stab", "刺す"),
    ("strangle", "絞め殺す"),
    ("hitman", "殺し屋"),
    ("execution", "処刑"),
    ("atrocity", "残虐行為"),
]

DRUGS: list[tuple[str, str]] = [
    ("narcotic", "麻薬"),
    ("cocaine", "コカイン"),
    ("heroin", "ヘロイン"),
    ("methamphetamine", "覚醒剤・メタンフェタミン"),
    ("cannabis", "大麻・カンナビス"),
    ("marijuana", "マリファナ・大麻"),
    ("weed (drug)", "(俗)大麻"),
    ("dope", "(俗)麻薬・ヤク"),
    ("LSD", "LSD(幻覚剤)"),
    ("ecstasy (drug)", "(薬物)エクスタシー・MDMA"),
    ("fentanyl", "フェンタニル(強力な合成麻薬)"),
    ("overdose", "薬物の過剰摂取"),
    ("addict", "中毒者・依存者"),
    ("junkie", "(俗)麻薬中毒者"),
    ("dealer", "(麻薬の)密売人"),
    ("high (on drugs)", "(俗)ラリった・キマった状態"),
    ("withdrawal", "禁断症状・離脱症状"),
]


def main() -> int:
    rows: list[tuple[str, str, str]] = []
    for en, ja in PROFANITY:
        rows.append((en, ja, WARN))
    for item in VULGAR:
        en, ja = item[0], item[1]
        rows.append((en, ja + "〔注意〕", WARN))
    for en, ja in VIOLENCE:
        rows.append((en, ja + "〔暴力〕", WARN_VIOL))
    for en, ja in DRUGS:
        rows.append((en, ja + "〔薬物〕", WARN_DRUG))

    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, ex in rows:
            if en.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, "", ex, "禁止用語", "範囲外"),
            )
            existing.add(en.lower())
            added += 1
    print(f"禁止用語 words: +{added} (skipped {skipped})")
    with db() as conn:
        print("禁止用語 計:",
              conn.execute("SELECT COUNT(*) FROM words WHERE domain='禁止用語'").fetchone()[0],
              "/ 単語総数:",
              conn.execute("SELECT COUNT(*) FROM words").fetchone()[0])
    return 0


if __name__ == "__main__":
    sys.exit(main())
