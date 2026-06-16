"""Per-user progress accessor (§A ルーター配線).

進捗(mastery/SRS/正答カウント)を words/phrases 本体の列ではなく
user_word_progress / user_phrase_progress に user 別で持つ。コンテンツ
(english/japanese/example/level/detail/音声)は全員共有のまま。

中核の考え方:
- 一覧/出題の SELECT は「コンテンツ × その user の進捗」を LEFT JOIN で
  マージしたサブクエリ(user_items_subquery)を FROM に使う。進捗行が無い項目は
  COALESCE で既定0扱い。これにより既存の WHERE/ORDER(mastery等)はほぼ無改造。
- 書き込みは upsert_progress() で進捗テーブルへ UPSERT。
"""

from __future__ import annotations

import sqlite3

# table -> (progress_table, id_column)
_MAP = {
    "words": ("user_word_progress", "word_id"),
    "phrases": ("user_phrase_progress", "phrase_id"),
}

# 進捗カラム（共通）。words/phrases 双方の per-user テーブルが持つ。
_PROGRESS_COLS = (
    "mastery", "last_studied", "times_asked", "times_correct",
    "ask_en2ja", "ok_en2ja", "ask_ja2en", "ok_ja2en",
    "review_level", "next_review",
)


def progress_table(table: str) -> tuple[str, str]:
    return _MAP[table]


def user_items_subquery(table: str) -> str:
    """コンテンツ×当該userの進捗をマージしたサブクエリ文字列を返す。
    1つの `?`(=user_id) を取る。``FROM <subquery> AS t`` で使う。
    返す行は本体のコンテンツ列＋進捗列(mastery等・既定0)を持つ。"""
    if table == "words":
        return (
            "(SELECT w.id, w.english, w.japanese, w.part_of_speech, "
            " w.example, w.level, w.domain, w.detail, w.created_at, "
            " COALESCE(p.mastery,0) AS mastery, p.last_studied AS last_studied, "
            " COALESCE(p.times_asked,0) AS times_asked, "
            " COALESCE(p.times_correct,0) AS times_correct, "
            " COALESCE(p.ask_en2ja,0) AS ask_en2ja, "
            " COALESCE(p.ok_en2ja,0) AS ok_en2ja, "
            " COALESCE(p.ask_ja2en,0) AS ask_ja2en, "
            " COALESCE(p.ok_ja2en,0) AS ok_ja2en, "
            " COALESCE(p.review_level,0) AS review_level, "
            " p.next_review AS next_review "
            " FROM words w "
            " LEFT JOIN user_word_progress p "
            "   ON p.word_id = w.id AND p.user_id = ?)"
        )
    if table == "phrases":
        return (
            "(SELECT ph.id, ph.english, ph.japanese, ph.scene, ph.level, "
            " COALESCE(p.mastery,0) AS mastery, p.last_studied AS last_studied, "
            " COALESCE(p.study_count,0) AS study_count, "
            " COALESCE(p.times_asked,0) AS times_asked, "
            " COALESCE(p.times_correct,0) AS times_correct, "
            " COALESCE(p.ask_en2ja,0) AS ask_en2ja, "
            " COALESCE(p.ok_en2ja,0) AS ok_en2ja, "
            " COALESCE(p.ask_ja2en,0) AS ask_ja2en, "
            " COALESCE(p.ok_ja2en,0) AS ok_ja2en, "
            " COALESCE(p.review_level,0) AS review_level, "
            " p.next_review AS next_review "
            " FROM phrases ph "
            " LEFT JOIN user_phrase_progress p "
            "   ON p.phrase_id = ph.id AND p.user_id = ?)"
        )
    raise ValueError(f"unknown table: {table}")


def get_progress(
    conn: sqlite3.Connection, user_id: int, table: str, item_id: int
) -> dict:
    """当該 user の item 進捗を返す(無ければ既定0)。"""
    ptable, idcol = _MAP[table]
    row = conn.execute(
        f"SELECT * FROM {ptable} WHERE user_id = ? AND {idcol} = ?",
        (user_id, item_id),
    ).fetchone()
    if row:
        return dict(row)
    d = {c: 0 for c in _PROGRESS_COLS}
    d["last_studied"] = None
    d["next_review"] = None
    if table == "phrases":
        d["study_count"] = 0
    return d


def ensure_row(
    conn: sqlite3.Connection, user_id: int, table: str, item_id: int
) -> None:
    """進捗行が無ければ作成（既定0）。"""
    ptable, idcol = _MAP[table]
    conn.execute(
        f"INSERT OR IGNORE INTO {ptable} (user_id, {idcol}) VALUES (?, ?)",
        (user_id, item_id),
    )


def upsert_progress(
    conn: sqlite3.Connection, user_id: int, table: str, item_id: int,
    **fields,
) -> None:
    """進捗を UPSERT（指定フィールドのみ更新）。"""
    if not fields:
        return
    ptable, idcol = _MAP[table]
    cols = list(fields.keys())
    placeholders = ", ".join("?" for _ in cols)
    updates = ", ".join(f"{c}=excluded.{c}" for c in cols)
    conn.execute(
        f"INSERT INTO {ptable} (user_id, {idcol}, {', '.join(cols)}) "
        f"VALUES (?, ?, {placeholders}) "
        f"ON CONFLICT(user_id, {idcol}) DO UPDATE SET {updates}",
        (user_id, item_id, *[fields[c] for c in cols]),
    )
