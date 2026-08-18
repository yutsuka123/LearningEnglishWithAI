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

from .spaced_repetition import DEFAULT_MASTERY_CONFIG, MASTERED_THRESHOLD, MasteryConfig

# 「習得」のしきい値は詳細設定のmastered_threshold(既定はspaced_repetition.
# MASTERED_THRESHOLD)と統一する（以前は本モジュール独自に80を定義しており、
# 一覧/フラッシュカードの「覚えた」判定とダッシュボードの「習得」判定が
# ズレていた）。VAGUE_RATIOはmastered_thresholdに対する「うろ覚え」下限の
# 比率(2026-08-18・単語一覧の△バッジと同じ基準)。
MASTERED = MASTERED_THRESHOLD  # 後方互換用(未指定時の既定しきい値)。
VAGUE_RATIO = 0.4


def vague_floor(mastered_threshold: int) -> int:
    return round(mastered_threshold * VAGUE_RATIO)


def word_buckets(
    conn: sqlite3.Connection, table: str = "words", *, user_id: int,
    cfg: MasteryConfig | None = None,
) -> dict:
    """当該 user の習熟バケツ集計（進捗は per-user テーブルからマージ）。"""
    from .progress import user_items_subquery
    cfg = cfg or DEFAULT_MASTERY_CONFIG
    threshold = cfg.mastered_threshold
    vfloor = vague_floor(threshold)
    src = user_items_subquery(table)  # 先頭 ? = user_id
    row = conn.execute(
        f"SELECT "
        f"COUNT(*) AS total, "
        f"SUM(CASE WHEN times_asked > 0 THEN 1 ELSE 0 END) AS studied, "
        f"SUM(CASE WHEN mastery >= {threshold} THEN 1 ELSE 0 END) AS mastered, "
        f"SUM(CASE WHEN mastery >= {vfloor} AND mastery < {threshold} "
        f"         THEN 1 ELSE 0 END) AS vague, "
        f"COALESCE(AVG(mastery), 0) AS avg_mastery "
        f"FROM {src} AS t",
        (user_id,),
    ).fetchone()
    return {
        "total": row["total"] or 0,
        "studied": row["studied"] or 0,
        "mastered": row["mastered"] or 0,
        "vague": row["vague"] or 0,
        "avg_mastery": round(row["avg_mastery"], 1),
    }


def toeic_estimate(
    avg_mastery: float, mastered: int, total: int, *,
    studied: int = 0, self_declared: int | None = None,
) -> int | None:
    """目安のTOEICスコア。
    - 学習データが無い(studied==0)とき: 自己申告値をそのまま返す。自己申告も
      無ければ None（=未判定）。
    - データがあるとき: 自己申告(無ければ550)を起点に、実績(平均習熟度・習得率)で
      補正してブレンド。実応答や正答率は avg_mastery に反映されている前提。
    """
    if studied <= 0:
        return self_declared  # None なら未判定
    base = self_declared if self_declared else 550
    mastered_ratio = (mastered / total) if total else 0.0
    est = base + (avg_mastery / 100) * 150 + mastered_ratio * 50
    est = max(300, min(990, est))
    return int(round(est / 5) * 5)  # 5点刻みに丸める
