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


# 一覧ルーターが「無料で聞ける順」ソートのSQLを組むために使う公開名
# （ここ以外で同じCASE式を再実装しない＝無料範囲の判定と並びの基準を
# 一致させるため・2026-09-20）。
level_rank_case = _level_rank_case


def billing_order(
    rows: list, guest_ids: set[int], free_ids: set[int], *, desc: bool = False,
) -> list:
    """一覧を「無料で聞ける順」(課金別ソート・2026-09-20)に並べ替える。

    並び = ①未登録ゲストが無料再生できる範囲(guest_ids) → ②ログイン無料の
    範囲(free_idsのうち①を除く) → ③それ以外(有料範囲)。各グループ内の
    並びは呼び出し側が渡した`rows`の順（レベル昇順→タイブレーク）を保つ
    (sortedは安定ソート)。`desc=True`ならグループ順も含め全体を反転する。
    無料範囲そのもの(どの語が①②か)はレベル昇順の上位N件という既存の
    判定(`free_range_ids`)をそのまま使うので、再生可否の表示(🆓/🔒)と
    必ず一致する。
    """
    def group(r) -> int:
        i = r["id"]
        if i in guest_ids:
            return 0
        return 1 if i in free_ids else 2

    ordered = sorted(rows, key=group)
    return ordered[::-1] if desc else ordered


def _table_and_limit(
    item_type: str, *, guest: bool = False,
) -> tuple[str, int]:
    if item_type == "phrase":
        limit = GUEST_PHRASES_LIMIT if guest else FREE_PHRASES_LIMIT
        return "phrases", limit
    return "words", (GUEST_WORDS_LIMIT if guest else FREE_WORDS_LIMIT)


def free_range_id_filter(
    item_type: str, *, guest: bool = False,
) -> tuple[str, list]:
    """一覧クエリに足せる「無料範囲内のみ」のWHERE断片とパラメータを返す
    （🔊再生できるものだけ表示フィルター用・2026-08-11）。"""
    table, limit = _table_and_limit(item_type, guest=guest)
    rank_expr = _level_rank_case()
    clause = (
        "id IN (SELECT id FROM ("
        f"  SELECT id, ROW_NUMBER() OVER (ORDER BY {rank_expr}, id) AS rn "
        f"  FROM {table}"
        ") WHERE rn <= ?)"
    )
    return clause, [limit]


def free_range_ids(
    conn: sqlite3.Connection, item_type: str, *, guest: bool = False,
) -> set[int]:
    """`free_range_id_filter`と同じ判定を、リクエスト単位で1回のSELECTだけ
    実行してidの集合として返す（一覧/quiz応答の各行に`is_free_range`を
    付与する用途。行ごとにランク計算するのを避けるため・2026-08-12）。"""
    table, limit = _table_and_limit(item_type, guest=guest)
    rank_expr = _level_rank_case()
    rows = conn.execute(
        f"SELECT id FROM ("
        f"  SELECT id, ROW_NUMBER() OVER (ORDER BY {rank_expr}, id) AS rn "
        f"  FROM {table}"
        f") WHERE rn <= ?",
        (limit,),
    ).fetchall()
    return {r["id"] for r in rows}


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
