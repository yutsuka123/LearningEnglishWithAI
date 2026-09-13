# ruff: noqa: E501
"""天文ドメイン topup(2026-09-13・authored by Claude): 宇宙論・宇宙の終焉。

2026-09-07セッションでドラフトされた同テーマ3語がスクラッチパッド保存のまま
消失したため再ドラフト(経緯は docs/B24_VOCAB_DRAFT_REVIEW.md 参照)。

No app / OpenAI API calls — hand-written、inserted directly into SQLite.
Duplicates skipped by english (lowercased) against the full live `words` table.

Run:  python scripts/add_astronomy_topup_2026_09_13.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    (
        "heat death of the universe",
        "宇宙全体のエントロピーが最大に達し、もはやどこにもエネルギーの偏り(自由エネルギー)が残らず、あらゆる物理的・化学的変化が実質的に停止するとされる、宇宙の終焉に関する仮説。",
        "名詞",
        "According to the heat death hypothesis, the universe will eventually reach a state of maximum entropy where no more work can be extracted from it.",
        "天文",
        "950",
    ),
    (
        "Big Rip",
        "「ファントムエネルギー」と呼ばれる特殊なダークエネルギーの働きで宇宙の膨張が加速し続け、最終的に銀河・恒星・原子までもがばらばらに引き裂かれてしまうとする、宇宙の終焉に関する仮説。",
        "名詞",
        "In the Big Rip scenario, phantom dark energy grows so strong that it eventually tears apart galaxies, stars, and even atoms.",
        "天文",
        "950",
    ),
    (
        "Big Crunch",
        "宇宙の膨張がいずれ減速して反転し、全ての物質とエネルギーが再び一点に向かって収縮していくとする、ビッグバンとは逆向きの宇宙の終焉に関する仮説。",
        "名詞",
        "If the universe's expansion were to reverse, the Big Crunch would compress all matter back into an extremely hot, dense state.",
        "天文",
        "930",
    ),
]


def main() -> None:
    with db() as conn:
        existing = set()
        for r in conn.execute("SELECT english FROM words").fetchall():
            existing.add(r["english"].lower())
        inserted = 0
        skipped = 0
        for english, japanese, pos, example, domain, level in WORDS:
            if english.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (english, japanese, pos, example, domain, level),
            )
            existing.add(english.lower())
            inserted += 1
        print("inserted=" + str(inserted) + " skipped=" + str(skipped))


if __name__ == "__main__":
    main()
