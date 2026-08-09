"""B1(ゲスト/無料ユーザー)向けの「無料範囲」判定(2026-08-09)。

無料範囲 = レベルの低い順(基礎語優先)で単語2,000語・フレーズ1,500件
（ユーザー決定・`docs/ACCESS_TIERS.md`参照）。固定フラグ列は持たせず、
`words.level`/`phrases.level`から都度計算する（語彙の追加・レベル
再判定があっても自動的に整合するようにするため）。

音声再生課金(2026-08-09〜)はこの無料範囲を土台にする: 無料範囲内の
単語・フレーズは誰でも(ゲスト相当含め)何度でも無料で再生できるが、
範囲外は課金ユーザーのチャージ残高を消費する（`app/services/ai.py`の
`charge_playback_if_needed`参照）。
"""

from __future__ import annotations

import sqlite3

FREE_WORDS_LIMIT = 2000
FREE_PHRASES_LIMIT = 1500

# app/routers/vocabulary.py の LEVEL_ORDER と同一スケール(words/phrases共通)。
# ここで独自に持つのは循環インポート回避のため（vocabulary.py はルーター）。
LEVEL_ORDER = [
    "300-", "300", "350", "400", "450", "500", "550", "600", "650",
    "700", "750", "800", "850", "900", "950", "990", "990+",
]


def _level_rank_case(column: str = "level") -> str:
    """レベル文字列を昇順ソート可能な整数に変換するCASE式（未知の値・
    空欄は最後尾扱い＝無料範囲の優先対象にしない）。"""
    whens = " ".join(
        f"WHEN '{lv}' THEN {i}" for i, lv in enumerate(LEVEL_ORDER)
    )
    return f"(CASE {column} {whens} ELSE {len(LEVEL_ORDER) + 1} END)"


def _table_and_limit(item_type: str) -> tuple[str, int]:
    if item_type == "phrase":
        return "phrases", FREE_PHRASES_LIMIT
    return "words", FREE_WORDS_LIMIT


def is_free_range(
    conn: sqlite3.Connection, item_type: str, item_id: int,
) -> bool:
    """指定した単語/フレーズが無料範囲(レベル昇順の上位N件)に入っているか。"""
    table, limit = _table_and_limit(item_type)
    rank_expr = _level_rank_case()
    row = conn.execute(
        f"SELECT rn FROM ("
        f"  SELECT id, ROW_NUMBER() OVER (ORDER BY {rank_expr}, id) AS rn "
        f"  FROM {table}"
        f") WHERE id = ?",
        (item_id,),
    ).fetchone()
    if not row:
        return False
    return row["rn"] <= limit


def detail_block_message(
    conn: sqlite3.Connection, item_type: str, item_id: int,
) -> str | None:
    """無料範囲外の単語/フレーズの「詳細」表示制限(2026-08-09)。

    一覧・検索での閲覧は誰でも可能なまま（範囲外の存在自体は隠さない）
    だが、詳細ボタン押下と音声再生(`app/services/ai.py`の
    `charge_playback_if_needed`)は範囲外だと制限される。詳細は音声と
    異なり都度課金ではなく、課金ユーザー/管理者なら無条件で閲覧可
    （ユーザー案: 詳細はチャージ消費対象にしない）。
    ブロックする場合はユーザー向けメッセージを返す。許可する場合はNone。
    """
    from .auth import current_user_id, is_charged_or_admin

    if is_free_range(conn, item_type, item_id):
        return None
    if is_charged_or_admin(conn, current_user_id()):
        return None
    return (
        "この単語・フレーズの詳細は無料範囲外です。"
        "課金（チャージ）していただくとご覧いただけます。"
    )
