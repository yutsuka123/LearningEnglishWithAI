"""Learning metrics: mastery buckets and a rough TOEIC-score estimate.

Mastery buckets (per item, mastery is 0..100):
  * 習得   (mastered) : mastery >= MASTERED
  * うろ覚え (vague)    : VAGUE <= mastery < MASTERED
  * 学習数 (studied)   : times_asked > 0 (一度でも出題した)
  * 全件数 (total)     : すべて（単語を足すと増える）

TOEIC estimate is a transparent heuristic — a 目安であって正確な予測ではない。
"""

from __future__ import annotations

import sqlite3

MASTERED = 80   # これ以上を「習得」
VAGUE = 40      # これ以上 MASTERED 未満を「うろ覚え」


def word_buckets(conn: sqlite3.Connection, table: str = "words") -> dict:
    row = conn.execute(
        f"SELECT "
        f"COUNT(*) AS total, "
        f"SUM(CASE WHEN times_asked > 0 THEN 1 ELSE 0 END) AS studied, "
        f"SUM(CASE WHEN mastery >= {MASTERED} THEN 1 ELSE 0 END) AS mastered, "
        f"SUM(CASE WHEN mastery >= {VAGUE} AND mastery < {MASTERED} "
        f"         THEN 1 ELSE 0 END) AS vague, "
        f"COALESCE(AVG(mastery), 0) AS avg_mastery "
        f"FROM {table}"
    ).fetchone()
    return {
        "total": row["total"] or 0,
        "studied": row["studied"] or 0,
        "mastered": row["mastered"] or 0,
        "vague": row["vague"] or 0,
        "avg_mastery": round(row["avg_mastery"], 1),
    }


def toeic_estimate(avg_mastery: float, mastered: int, total: int) -> int:
    """目安のTOEICスコア。現在レベル(約550)を起点に学習の進み具合で加点。

    base 550 + 平均習熟度で最大+200 + 習得率で最大+50 → 約800が上限の目安。
    """
    mastered_ratio = (mastered / total) if total else 0.0
    est = 550 + (avg_mastery / 100) * 200 + mastered_ratio * 50
    est = max(300, min(990, est))
    return int(round(est / 5) * 5)  # 5点刻みに丸める
