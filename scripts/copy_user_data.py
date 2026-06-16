"""あるユーザーの学習データを別ユーザーへ複製する。

進捗(words/phrases/materials)・会話/学習履歴・per-user設定・単語帳(decks)・
memory/study_log ファイルを SRC → DST へコピー（DSTの既存同種データは置換）。

使い方:
  python scripts/copy_user_data.py --from 3 --to 2 --allow-banned
  （yutakatsu(3) の実績を yutakatsuadmin(2) へ。--allow-banned で禁止項目ON）
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import paths  # noqa: E402
from app.database import db, init_db  # noqa: E402

# (table, id-ish columns to copy excluding user_id). user_id は dst で上書き。
_PROGRESS = {
    "user_word_progress": ("word_id", "mastery", "last_studied",
        "times_asked", "times_correct", "ask_en2ja", "ok_en2ja",
        "ask_ja2en", "ok_ja2en", "review_level", "next_review"),
    "user_phrase_progress": ("phrase_id", "mastery", "last_studied",
        "study_count", "times_asked", "times_correct", "ask_en2ja",
        "ok_en2ja", "ask_ja2en", "ok_ja2en", "review_level", "next_review"),
    "user_material_progress": ("material_id", "mastery", "last_studied"),
}
_HISTORY = {
    "conversation_log": ("role", "content", "mode", "created_at"),
    "study_sessions": ("study_date", "content", "accuracy", "weak_points",
        "next_topic", "new_words", "created_at", "session_key"),
}


def _copy_table(conn, table, cols, src, dst):
    conn.execute(f"DELETE FROM {table} WHERE user_id = ?", (dst,))
    collist = ", ".join(cols)
    conn.execute(
        f"INSERT INTO {table} (user_id, {collist}) "
        f"SELECT ?, {collist} FROM {table} WHERE user_id = ?",
        (dst, src),
    )


def _copy_decks(conn, src, dst):
    conn.execute(
        "DELETE FROM deck_progress WHERE deck_id IN "
        "(SELECT id FROM decks WHERE user_id = ?)", (dst,))
    conn.execute(
        "DELETE FROM deck_words WHERE deck_id IN "
        "(SELECT id FROM decks WHERE user_id = ?)", (dst,))
    conn.execute("DELETE FROM decks WHERE user_id = ?", (dst,))
    src_decks = conn.execute(
        "SELECT id, name, settings, created_at FROM decks WHERE user_id = ?",
        (src,)).fetchall()
    for d in src_decks:
        cur = conn.execute(
            "INSERT INTO decks (name, settings, created_at, user_id) "
            "VALUES (?, ?, ?, ?)",
            (d["name"], d["settings"], d["created_at"], dst))
        nid = cur.lastrowid
        conn.execute(
            "INSERT INTO deck_words (deck_id, word_id) "
            "SELECT ?, word_id FROM deck_words WHERE deck_id = ?",
            (nid, d["id"]))
        conn.execute(
            "INSERT INTO deck_progress "
            "(deck_id, word_id, correct_count, done_at, user_id) "
            "SELECT ?, word_id, correct_count, done_at, ? "
            "FROM deck_progress WHERE deck_id = ?", (nid, dst, d["id"]))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", type=int, required=True)
    ap.add_argument("--to", dest="dst", type=int, required=True)
    ap.add_argument("--allow-banned", action="store_true",
                    help="コピー先の allow_banned を1(禁止項目ON)にする")
    args = ap.parse_args()
    init_db()
    src, dst = args.src, args.dst
    with db() as conn:
        for t, cols in _PROGRESS.items():
            _copy_table(conn, t, cols, src, dst)
        for t, cols in _HISTORY.items():
            _copy_table(conn, t, cols, src, dst)
        # per-user 設定
        conn.execute(
            "INSERT OR REPLACE INTO user_settings (user_id, settings) "
            "SELECT ?, settings FROM user_settings WHERE user_id = ?",
            (dst, src))
        _copy_decks(conn, src, dst)
        if args.allow_banned:
            conn.execute(
                "UPDATE users SET allow_banned = 1 WHERE id = ?", (dst,))
        # 確認
        wp = conn.execute("SELECT COUNT(*) FROM user_word_progress "
                          "WHERE user_id=?", (dst,)).fetchone()[0]
        cl = conn.execute("SELECT COUNT(*) FROM conversation_log "
                          "WHERE user_id=?", (dst,)).fetchone()[0]
        ab = conn.execute("SELECT allow_banned FROM users WHERE id=?",
                          (dst,)).fetchone()[0]
        print(f"dst {dst}: word進捗 {wp} / 会話 {cl} / allow_banned {ab}")

    # memory/study_log ファイル: src -> dst
    sdir = paths.data_dir / "users" / str(src)
    ddir = paths.data_dir / "users" / str(dst)
    ddir.mkdir(parents=True, exist_ok=True)
    for name in ("memory.md", "study_log.md"):
        if (sdir / name).exists():
            shutil.copy2(sdir / name, ddir / name)
            print(f"copied users/{src}/{name} -> users/{dst}/{name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
