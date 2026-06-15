"""Persistent store for generated TTS audio, keyed by 番号(ID)＋種別＋声.

Goal (ユーザー要望): 再生のたびに音声を保存していき、次回からはAPIトークンを
使わずに再生する。保存先は方式を抽象化して切り替え可能:

  * ``file``   … data/audio/{type}{id}_{kind}_{voice}.mp3 に保存（既定）
  * ``db``     … audio_blobs テーブルに BLOB として保存
  * ``hybrid`` … 両方に保存（冗長化／移行用）

呼び出し側は :func:`get` / :func:`put` だけを使えばよく、方式の違いを意識
しなくてよい。ファイル名は番号(ID)＋声で一元管理する（DESIGN §9.7）。
"""

from __future__ import annotations

import sqlite3

from ..config import load_settings, paths

VALID_TYPES = ("word", "phrase")
VALID_KINDS = ("word", "example", "phrase")


def _audio_dir():
    d = paths.data_dir / "audio"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _file_path(item_type: str, item_id: int, kind: str, voice: str):
    name = f"{item_type}{item_id}_{kind}_{voice}.mp3"
    return _audio_dir() / name


def get(
    conn: sqlite3.Connection,
    item_type: str,
    item_id: int,
    kind: str,
    voice: str,
) -> bytes | None:
    """保存済み音声を返す（無ければ None）。file/db のどちらにあっても拾う。"""
    mode = load_settings().audio_storage
    if mode in ("file", "hybrid"):
        fp = _file_path(item_type, item_id, kind, voice)
        if fp.exists():
            try:
                return fp.read_bytes()
            except OSError:
                pass
    if mode in ("db", "hybrid"):
        row = conn.execute(
            "SELECT mp3 FROM audio_blobs WHERE item_type = ? AND item_id = ? "
            "AND kind = ? AND voice = ?",
            (item_type, item_id, kind, voice),
        ).fetchone()
        if row and row["mp3"] is not None:
            return bytes(row["mp3"])
    return None


def put(
    conn: sqlite3.Connection,
    item_type: str,
    item_id: int,
    kind: str,
    voice: str,
    mp3: bytes,
) -> None:
    """音声を保存（方式に応じて file / db / 両方）。"""
    mode = load_settings().audio_storage
    if mode in ("file", "hybrid"):
        try:
            _file_path(item_type, item_id, kind, voice).write_bytes(mp3)
        except OSError:
            pass
    if mode in ("db", "hybrid"):
        conn.execute(
            "INSERT OR REPLACE INTO audio_blobs "
            "(item_type, item_id, kind, voice, mp3) VALUES (?, ?, ?, ?, ?)",
            (item_type, item_id, kind, voice, sqlite3.Binary(mp3)),
        )


def stats(conn: sqlite3.Connection) -> dict:
    """保存済み音声の件数（設定画面の表示用）。"""
    files = len(list(_audio_dir().glob("*.mp3"))) if _audio_dir().exists() \
        else 0
    db_rows = conn.execute(
        "SELECT COUNT(*) AS c FROM audio_blobs"
    ).fetchone()["c"]
    return {
        "mode": load_settings().audio_storage,
        "files": files,
        "db_rows": db_rows,
    }
