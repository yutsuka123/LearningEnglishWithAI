# ruff: noqa: E501
"""B27特許用語ドメインの残りギャップを埋めるtopup(2026-09-13)。

`知的財産（特許）`は2026-09-09のIP6分野バッチで既に59語投入済みで、B27が
挙げていた用語(comprising/wherein/said/prior art/embodiment/disclosure/
office action/patent examiner等)はほぼ網羅済みと判明。唯一抜けていた
`patent prosecution`と、既存の`specification`(IT分野の「仕様書」の意味)
とは別に特許分野固有の意味(明細書)の同綴り異義語エントリを追加する。

Run:  python scripts/add_patent_topup_2026_09_13.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

WORDS: list[tuple[str, str, str, str, str, str]] = [
    (
        "patent prosecution",
        "特許出願人(代理人)が特許庁との間で、拒絶理由通知への応答やクレームの補正等を行いながら特許査定(または拒絶)に至るまでの一連の手続き。",
        "名詞句",
        "Patent prosecution can take several years, especially if the examiner issues multiple office actions.",
        "知的財産（特許）",
        "800",
    ),
    (
        "specification",
        "特許明細書。発明の内容を、その技術分野の専門家が実施できる程度に詳しく記載した、特許出願の中核となる文書部分。",
        "名詞",
        "The specification must describe the invention in enough detail for someone skilled in the art to reproduce it.",
        "知的財産（特許）",
        "800",
    ),
]


def main() -> None:
    with db() as conn:
        existing = set()
        for r in conn.execute(
            "SELECT english, domain FROM words"
        ).fetchall():
            existing.add((r["english"].lower(), r["domain"]))
        inserted = 0
        skipped = 0
        for english, japanese, pos, example, domain, level in WORDS:
            if (english.lower(), domain) in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO words (english, japanese, part_of_speech, "
                "example, domain, level) VALUES (?, ?, ?, ?, ?, ?)",
                (english, japanese, pos, example, domain, level),
            )
            existing.add((english.lower(), domain))
            inserted += 1
        print("inserted=" + str(inserted) + " skipped=" + str(skipped))


if __name__ == "__main__":
    main()
