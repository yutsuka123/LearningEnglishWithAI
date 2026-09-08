# ruff: noqa: E501
"""B24語彙拡充の「レベル配分」方針(2026-09-08ユーザー指示)を物理・化学にも適用。

地学/天文/生物学で先行実施した`tag_domain_breadth_2026_09_08.py`と同じ手法。
物理・化学ドメインの学部専門レベル深化バッチ(add_physics_advanced.py・
add_chemistry_advanced.py)がlevel 850〜990+に偏っているため、DB全体を
調べて概念的に重なる中学・高校相当(level 300〜700)の既存語のうち、
他ドメインに分類されたままのものをword_domain_tagsで追加タグ付けする。

物理: `light`と`sound`(見出し語としてDB全体に一件も存在しなかった基礎語、
level 300)はadd_physics_advanced.py側のドラフト班が既に新規追加済みのため
本スクリプトの対象外(新規追加はしない)。ここでは既存語のタグ付けのみ。

既存語の定義・訳を書き換えるものではない(該当語の主分類(domain列)は
変更せず、word_domain_tagsへの追加行のみ)。

Run:  python scripts/tag_domain_breadth_physics_chem_2026_09_08.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# (english, 既存の主分類(domain), 追加でタグ付けする分野)
TAGS: list[tuple[str, str, str]] = [
    # --- 物理: 他ドメインにある物理関連の中学・高校相当語 ---
    ("wave", "アウトドア・レジャー", "物理"),
    ("electricity", "科学", "物理"),
    ("temperature", "科学", "物理"),
    ("friction", "基礎語彙", "物理"),
    ("resistance", "電気電子", "物理"),
    ("current", "基礎語彙", "物理"),
    ("conductor", "電気電子", "物理"),
    ("voltage", "電気電子", "物理"),
    ("battery", "電池", "物理"),
    ("sound wave", "音響工学", "物理"),
    ("resistor", "電気電子", "物理"),
    ("waveform", "電気電子", "物理"),
    # --- 化学: 他ドメインにある化学関連の中学・高校相当語 ---
    ("chemical", "科学", "化学"),
    ("solution", "IT", "化学"),
    ("fuel cell", "エネルギー", "化学"),
]


def main() -> int:
    tagged = already = missing = 0
    with db() as conn:
        for en, src_domain, tag_domain in TAGS:
            row = conn.execute(
                "SELECT id FROM words WHERE LOWER(english) = LOWER(?) "
                "AND domain = ?",
                (en, src_domain),
            ).fetchone()
            if not row:
                print(f"  [未検出] {en} (domain={src_domain})")
                missing += 1
                continue
            existing = conn.execute(
                "SELECT 1 FROM word_domain_tags WHERE word_id = ? "
                "AND domain = ?",
                (row["id"], tag_domain),
            ).fetchone()
            if existing:
                already += 1
                continue
            conn.execute(
                "INSERT INTO word_domain_tags (word_id, domain) "
                "VALUES (?, ?)",
                (row["id"], tag_domain),
            )
            tagged += 1
        conn.commit()
    print(f"タグ付け: 新規 {tagged} / 既存 {already} / 未検出 {missing} "
          f"(対象 {len(TAGS)} 件)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
