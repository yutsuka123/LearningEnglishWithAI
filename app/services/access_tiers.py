"""B1(ゲスト/無料ユーザー)向けの「無料範囲」判定(2026-08-09、
2026-08-11に方針改訂)。

無料範囲 = レベルの低い順(基礎語優先)で①(未ログイン)単語1,000語・
フレーズ750件、②(ログイン無料)単語2,000語・フレーズ1,500件
（`docs/ACCESS_TIERS.md`参照）。固定フラグ列は持たせず、
`words.level`/`phrases.level`から都度計算する（語彙の追加・レベル
再判定があっても自動的に整合するようにするため）。

**2026-08-11の方針転換**: 一覧・検索・詳細は①②とも無料範囲に関わらず
常時無料公開に変更（ニッチ分野の広さを隠さないため）。この無料範囲は
**音声再生の可否のみ**を左右する: 無料範囲内の単語・フレーズは誰でも
(ゲスト相当含め)何度でも無料で再生できるが、範囲外は課金ユーザーの
チャージ残高を消費する（`app/services/ai.py`の
`charge_playback_if_needed`参照）。旧`detail_block_message`(詳細を
無料範囲外でブロックする関数)はこの方針転換により2026-08-11に削除した。
"""

from __future__ import annotations

import sqlite3

FREE_WORDS_LIMIT = 2000      # ②(ログイン無料)向け
FREE_PHRASES_LIMIT = 1500
GUEST_WORDS_LIMIT = 1000     # ①(未ログイン)向け・②の半分
GUEST_PHRASES_LIMIT = 750

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


def _table_and_limit(item_type: str, *, guest: bool = False) -> tuple[str, int]:
    if item_type == "phrase":
        return "phrases", (GUEST_PHRASES_LIMIT if guest else FREE_PHRASES_LIMIT)
    return "words", (GUEST_WORDS_LIMIT if guest else FREE_WORDS_LIMIT)


def is_free_range(
    conn: sqlite3.Connection, item_type: str, item_id: int, *,
    guest: bool = False,
) -> bool:
    """指定した単語/フレーズが無料範囲(レベル昇順の上位N件)に入っているか。
    ``guest=True``で①(未ログイン)向けのより狭い範囲を使う。"""
    table, limit = _table_and_limit(item_type, guest=guest)
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
