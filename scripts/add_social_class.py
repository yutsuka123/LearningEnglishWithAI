# ruff: noqa: E501  (data-heavy seed script: long word lines are fine)
"""階級社会(新設・欧米/日本/中国), authored by Claude (2026-08-05・ユーザー
要望:「階級社会の階級や用語、欧米、日本、中国他」).

既存の「歴史」ドメインに nobility/peasant/feudalism/samurai/shogun/daimyo
は既にあるため、それらの裸の語は避け、身分制度そのものの概念・用語
(制度名/身分間の移動/身分証明等)を中心に選定した。TONE: 特定の現代の
国・政治体制を序列化して評価するのではなく、歴史的・社会学的な事実・
用語として中立的に扱う（既存の軍事語彙と同じ前例）。

No app / OpenAI API calls — hand-written, inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words`
table.

Run:  python scripts/add_social_class.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

D = "階級社会"

WORDS: list[tuple[str, str, str, str, str, str]] = [
    # --- 概念・一般用語 ---
    ("social class", "社会階級", "名詞", "Social class often shapes a person's education and career opportunities.", D, "700"),
    ("social hierarchy", "社会的階層", "名詞", "The social hierarchy in the story places nobles far above ordinary farmers.", D, "750"),
    ("social stratification", "社会層化", "名詞", "Sociologists study social stratification to understand inequality in a society.", D, "900"),
    ("social mobility", "社会的流動性", "名詞", "Social mobility lets people move into a different class than the one they were born into.", D, "800"),
    ("class distinction", "階級的区別", "名詞", "Class distinction was once reinforced by strict rules about clothing and speech.", D, "800"),
    ("ruling class", "支配階級", "名詞", "The ruling class controlled most of the land and the army.", D, "750"),
    ("privileged class", "特権階級", "名詞", "Only the privileged class had access to formal education in that era.", D, "750"),
    ("underclass", "下層階級", "名詞", "The underclass had almost no legal protection under the old system.", D, "800"),
    ("hereditary status", "世襲的身分", "名詞", "Hereditary status meant a person's rank was fixed at birth, not earned.", D, "850"),
    ("birthright", "生得の権利・生まれによる特権", "名詞", "The title passed to him as a birthright, regardless of his ability.", D, "750"),
    # --- 欧米（貴族制度） ---
    ("aristocracy", "貴族階級", "名詞", "The aristocracy owned most of the farmland for centuries.", D, "700"),
    ("hereditary peerage", "世襲貴族位", "名詞", "A hereditary peerage passes automatically from parent to child.", D, "900"),
    ("landed gentry", "地主階級・ジェントリ", "名詞", "The landed gentry ranked just below the titled nobility.", D, "900"),
    ("commoner", "平民", "名詞", "As a commoner, she was not allowed to marry into the royal family.", D, "700"),
    ("serfdom", "農奴制", "名詞", "Serfdom bound peasants to the land they worked for a lord.", D, "850"),
    ("bourgeoisie", "ブルジョワジー（中産階級）", "名詞", "The rising bourgeoisie demanded a greater political voice.", D, "850"),
    ("working class", "労働者階級", "名詞", "The novel follows a working-class family during the industrial revolution.", D, "600"),
    ("middle class", "中産階級", "名詞", "The middle class grew rapidly as manufacturing jobs expanded.", D, "550"),
    ("upper class", "上流階級", "名詞", "Only the upper class could afford to send their children abroad to study.", D, "600"),
    ("class struggle", "階級闘争", "名詞", "Class struggle was a central idea in nineteenth-century political thought.", D, "850"),
    # --- 日本 ---
    ("feudal domain", "藩", "名詞", "Each feudal domain was ruled by its own daimyo under the shogun.", D, "800"),
    ("samurai class", "武士階級", "名詞", "The samurai class was expected to follow a strict code of honor.", D, "700"),
    ("four-tiered class system", "士農工商（四民の身分制度）", "名詞", "Edo-period Japan organized society into a four-tiered class system.", D, "900"),
    ("merchant class", "商人階級", "名詞", "The merchant class was ranked lowest despite often being the wealthiest.", D, "800"),
    ("artisan class", "職人階級", "名詞", "The artisan class produced the goods that both samurai and merchants relied on.", D, "800"),
    ("hereditary retainer", "世襲の家臣", "名詞", "A hereditary retainer served the same lord's family for generations.", D, "900"),
    ("court noble", "公家", "名詞", "A court noble held ceremonial rank at the imperial court in Kyoto.", D, "850"),
    # --- 中国 ---
    ("imperial examination", "科挙", "名詞", "The imperial examination let commoners rise into the scholar-official class through merit.", D, "900"),
    ("scholar-official", "士大夫・科挙官僚", "名詞", "A scholar-official earned his position by passing a series of difficult exams.", D, "900"),
    ("mandarin (official)", "科挙官僚（マンダリン）", "名詞", "A mandarin was expected to master classical texts before entering government service.", D, "900"),
    ("gentry class (China)", "郷紳階級", "名詞", "The gentry class managed local affairs on behalf of the imperial government.", D, "900"),
    ("peasant class (China)", "農民階級", "名詞", "The peasant class made up the vast majority of the population for centuries.", D, "800"),
    # --- その他の身分制度 ---
    ("caste system", "カースト制度", "名詞", "The caste system historically determined a person's occupation and social standing from birth.", D, "800"),
    ("untouchability", "不可触民制", "名詞", "Untouchability was officially outlawed, though its effects still linger in some areas.", D, "900"),
    ("social outcast", "社会的追放者", "名詞", "The character is treated as a social outcast because of his family's past.", D, "800"),
    ("status symbol", "ステータスシンボル", "名詞", "A private carriage was once an important status symbol among the elite.", D, "700"),
    ("noblesse oblige", "ノブレス・オブリージュ（貴族の義務）", "名詞", "Noblesse oblige held that the privileged had a duty to help those beneath them.", D, "950"),
]


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM words").fetchall()
        }
        added = skipped = 0
        for en, ja, pos, ex, domain, level in WORDS:
            if en.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (en, ja, pos, ex, domain, level),
            )
            existing.add(en.lower())
            added += 1
    print(f"words: +{added} (skipped {skipped})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
