"""Persistent store for generated TTS audio, keyed by 番号(ID)＋種別＋声＋
テキストのハッシュ.

Goal (ユーザー要望): 再生のたびに音声を保存していき、次回からはAPIトークンを
使わずに再生する。保存先は方式を抽象化して切り替え可能:

  * ``file``   … data/audio/{type}{id}_{kind}_{voice}_{hash}.mp3 に保存（既定）
  * ``db``     … audio_blobs テーブルに BLOB として保存
  * ``hybrid`` … 両方に保存（冗長化／移行用）

呼び出し側は :func:`get` / :func:`put` だけを使えばよく、方式の違いを意識
しなくてよい。

**なぜハッシュが要るか(2026-08-05・重大インシデントの再発防止)**: 以前は
ファイル名が番号(ID)だけで決まっていた。ローカルと本番でIDの割り当てが
分岐した際、番号だけで紐付けたrsyncコピーが「別の語の音声」を配ってしまう
事故が発生した(words 3,343件・phrases 1,489件が実際に誤配信された)。
テキストのハッシュをファイル名に含めることで、**IDが指す語が変わったら
（＝テキストが変わったら）キャッシュキーも自動的に変わり、古い音声は
二度と誤って返らない**（キャッシュミスとして扱われ、現在のテキストで
再合成される）。
"""

from __future__ import annotations

import hashlib
import sqlite3

from ..config import load_settings, paths

VALID_TYPES = ("word", "phrase")
# 基本種別。速度(native)は kind に "_native" を付けて区別する
# （例: phrase / phrase_native / example / example_native）。
VALID_KINDS = (
    "word", "example", "phrase",
    # 2026-08-22: 単語にもネイティブ速度の選択肢を出したので word_native を
    # 追加（押されたときに合成して貯まる。既存の音声在庫には影響しない）。
    "word_native", "example_native", "phrase_native",
)


def storage_kind(kind: str, speed: str) -> str:
    """基本種別＋速度 → 保存用の種別文字列。learn は無印、native は _native。"""
    base = kind if kind in ("word", "example", "phrase") else "phrase"
    return base if speed != "native" else f"{base}_native"


def _audio_dir():
    d = paths.data_dir / "audio"
    d.mkdir(parents=True, exist_ok=True)
    return d


def text_hash(text: str) -> str:
    """再生対象テキストの短いハッシュ。キャッシュキーに含めることで、
    番号(ID)が指すテキストが変わったら自動的に別キーになる（=古い音声を
    誤って返さない）。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:10]


def _file_path(
    item_type: str, item_id: int, kind: str, voice: str, thash: str,
):
    name = f"{item_type}{item_id}_{kind}_{voice}_{thash}.mp3"
    return _audio_dir() / name


def get(
    conn: sqlite3.Connection,
    item_type: str,
    item_id: int,
    kind: str,
    voice: str,
    text: str,
) -> bytes | None:
    """保存済み音声を返す（無ければ None）。file/db のどちらにあっても拾う。
    ``text`` の内容が保存時と変わっていれば別キーになりキャッシュミスする。"""
    thash = text_hash(text)
    mode = load_settings().audio_storage
    if mode in ("file", "hybrid"):
        fp = _file_path(item_type, item_id, kind, voice, thash)
        if fp.exists():
            try:
                return fp.read_bytes()
            except OSError:
                pass
    if mode in ("db", "hybrid"):
        row = conn.execute(
            "SELECT mp3 FROM audio_blobs WHERE item_type = ? AND item_id = ? "
            "AND kind = ? AND voice = ? AND text_hash = ?",
            (item_type, item_id, kind, voice, thash),
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
    text: str,
    mp3: bytes,
) -> None:
    """音声を保存（方式に応じて file / db / 両方）。"""
    thash = text_hash(text)
    mode = load_settings().audio_storage
    if mode in ("file", "hybrid"):
        try:
            _file_path(item_type, item_id, kind, voice, thash).write_bytes(mp3)
        except OSError:
            pass
    if mode in ("db", "hybrid"):
        conn.execute(
            "INSERT OR REPLACE INTO audio_blobs "
            "(item_type, item_id, kind, voice, text_hash, mp3) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (item_type, item_id, kind, voice, thash, sqlite3.Binary(mp3)),
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
