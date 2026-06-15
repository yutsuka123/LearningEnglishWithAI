# ruff: noqa: E501
"""Consolidate over-fragmented word domains and phrase scenes (ユーザー要望:
分類が多すぎる→適度に統合)。DB直接UPDATE・冪等。宗教の4宗派(キリスト教/仏教/
ユダヤ教/イスラム教)は残す。

Run: python scripts/consolidate_tags.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

# 単語 domain: 旧→新（記載のないものは据え置き）
WORD_DOMAIN_MAP = {
    "法律手続き": "法律",
    "病名": "医療",
    "世界史": "歴史",
    "日本史": "歴史",
    "機械": "機械工学",
    "経済": "経済学",
    "公共": "生活",
    "買い物": "生活",
    "農業": "生物学",
    "建設": "建築",
    "政治": "ニュース",
    "教育": "教養",
}

# フレーズ scene: 旧→新
PHRASE_SCENE_MAP = {
    "病院・部位別症状": "病院・症状",
    "病院・病状": "病院・症状",
    "ニュース報道": "ニュース",
    "ニュース定型": "ニュース",
    "慣用句・イディオム": "慣用句",
    "慣用句・引用": "慣用句",
    "哲学": "哲学・名言",
    "レストラン": "レストラン・カフェ",
    "両替・買い物": "買い物",
    "スーパー": "買い物",
    "出入国": "出入国・税関",
    "日常": "日常会話",
    "ご近所": "日常会話",
    "IT開発": "IT・ビルド/エラー",
    "会議": "ビジネス",
    "犯罪・事件": "警察・トラブル",
    # 生活系 6→3 に集約
    "生活・住まい": "生活・手続き",
    "生活・銀行/郵便": "生活・手続き",
    "生活・手続き/会話": "生活・手続き",
    "生活・買い物": "生活・買い物/移動",
    "生活・交通": "生活・買い物/移動",
    # 生活・医療 は据え置き
}


def main() -> int:
    with db() as conn:
        wd = conn.execute(
            "SELECT COUNT(DISTINCT domain) FROM words"
        ).fetchone()[0]
        ps = conn.execute(
            "SELECT COUNT(DISTINCT scene) FROM phrases"
        ).fetchone()[0]
        wmoved = 0
        for old, new in WORD_DOMAIN_MAP.items():
            cur = conn.execute(
                "UPDATE words SET domain = ? WHERE domain = ?", (new, old)
            )
            wmoved += cur.rowcount
        pmoved = 0
        for old, new in PHRASE_SCENE_MAP.items():
            cur = conn.execute(
                "UPDATE phrases SET scene = ? WHERE scene = ?", (new, old)
            )
            pmoved += cur.rowcount
        wd2 = conn.execute(
            "SELECT COUNT(DISTINCT domain) FROM words"
        ).fetchone()[0]
        ps2 = conn.execute(
            "SELECT COUNT(DISTINCT scene) FROM phrases"
        ).fetchone()[0]
    print(f"単語 domain: {wd} → {wd2} 種  (移動 {wmoved} 語)")
    print(f"フレーズ scene: {ps} → {ps2} 種  (移動 {pmoved} 件)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
