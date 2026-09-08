# ruff: noqa: E501
"""B24語彙拡充の「レベル配分」方針転換(2026-09-08ユーザー指示)への対応。

ユーザー指示:「語彙拡充は各分野の中学高等学校相当の拡充、小学校相当の拡充も
多少あってもいいと思います」(専門/上級(800+)一辺倒ではなく、中学・高校
相当(level 400〜700)を2〜3割程度、小学校相当(300前後)を数語〜1割程度
含めるという配分方針)。

地学・天文・生物学の3ドメインは、今回投入した学部専門レベルの深化バッチ
(add_geology_advanced.py / add_astronomy_advanced.py /
add_biology_advanced.py、いずれも2026-09-08)がすべてlevel 850〜990+に
偏っている。一方でDB全体を調べると、これらのドメインと概念的に重なる
中学・高校相当(level 300〜700)の既存語が**他ドメインに分類されたまま**
多数存在することが判明した(例: earthquake=科学domain, species=科学domain,
predator=動物(その他)domain 等)。

新規に定義文を書く(=事実確認コストが発生する)のではなく、B17a
(`word_domain_tags`)の複数分野タグ付け機構を使ってこれらの既存語を
地学/天文/生物学ドメインにも**追加で**紐付けることで、各ドメインの
アクセシブルな(中学・高校相当の)語彙層を厚くする。
`app/routers/vocabulary.py`の`_word_filter`(word_domain_tags経由のOR条件)
により、domain=地学 等でフィルタした際にこれらの語も一覧に含まれるように
なる。

既存語の定義・訳を書き換えるものではない(該当語の主分類(domain列)は
変更せず、word_domain_tagsへの追加行のみ)。

Run:  python scripts/tag_domain_breadth_2026_09_08.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# (english, 既存の主分類(domain), 追加でタグ付けする分野)
TAGS: list[tuple[str, str, str]] = [
    # --- 地学: 既に他ドメインにある地球科学関連語 ---
    ("earthquake", "科学", "地学"),
    ("valley", "基礎語彙", "地学"),
    ("continent", "地理", "地学"),
    ("peninsula", "地理", "地学"),
    ("delta", "地理", "地学"),
    ("plain", "地理", "地学"),
    ("canyon", "アウトドア・レジャー", "地学"),
    ("avalanche", "アウトドア・レジャー", "地学"),
    ("soil", "科学", "地学"),
    ("tide", "船舶", "地学"),
    ("natural disaster", "災害", "地学"),
    # --- 天文: 既に他ドメインにある天文関連語 ---
    ("galaxy", "SF", "天文"),
    ("asteroid", "SF", "天文"),
    ("orbit", "航空・宇宙", "天文"),
    ("astronaut", "航空・宇宙", "天文"),
    ("gravity", "物理", "天文"),
    ("telescope", "科学", "天文"),
    ("constellation", "科学", "天文"),
    ("meteor", "科学", "天文"),
    ("astronomy", "科学", "天文"),
    ("space station", "SF", "天文"),
    # --- 生物学: 既に他ドメインにある生物学関連語 ---
    ("species", "科学", "生物学"),
    ("evolution", "科学", "生物学"),
    ("predator", "動物(その他)", "生物学"),
    ("prey", "動物(その他)", "生物学"),
    ("habitat", "動物(その他)", "生物学"),
    ("food chain", "動物(その他)", "生物学"),
    ("mammal", "動物(その他)", "生物学"),
    ("reptile", "動物(その他)", "生物学"),
    ("amphibian", "動物(その他)", "生物学"),
    ("invertebrate", "動物(その他)", "生物学"),
    ("vertebrate", "動物(その他)", "生物学"),
    ("bacteria", "生物(その他)", "生物学"),
    ("virus", "生物(その他)", "生物学"),
    ("hormone", "生化学", "生物学"),
    ("protein", "化学", "生物学"),
    ("cell membrane", "生化学", "生物学"),
    ("brain", "科学", "生物学"),
    ("organ", "医療(その他)", "生物学"),
    ("heart", "医療(その他)", "生物学"),
    ("lung", "医療(その他)", "生物学"),
    ("muscle", "医療(その他)", "生物学"),
    ("nutrient", "医療(その他)", "生物学"),
    ("antibiotic", "医療(治療)", "生物学"),
    ("skeleton", "動物(絶滅)", "生物学"),
    ("extinct", "動物(その他)", "生物学"),
    ("offspring", "動物(その他)", "生物学"),
    ("endangered species", "動物(絶滅)", "生物学"),
]


def main() -> int:
    tagged = missing = already = 0
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
