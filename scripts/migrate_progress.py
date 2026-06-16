"""既存の words/phrases/materials の進捗列を per-user テーブルへ複製する。

§A ルーター配線で進捗が user_word/phrase_progress / user_material_progress に
移ったため、それ以前に words/phrases 本体列へ溜まっていたローカル進捗を、
指定ユーザーへ「継承」させる一回限りの移行。

使い方:
  python scripts/migrate_progress.py 1 3   # owner(1) と yutakatsu(3) へ複製
進捗のある行のみ複製（mastery>0 or times_asked>0 or review_level>0）。
INSERT OR REPLACE で当該ユーザーの該当行を上書き（冪等）。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db, init_db  # noqa: E402


def main() -> int:
    init_db()  # 新スキーマ(user_material_progress/user_settings/decks.user_id)適用
    uids = [int(a) for a in sys.argv[1:]] or [1]
    with db() as conn:
        for uid in uids:
            conn.execute(
                "INSERT OR REPLACE INTO user_word_progress "
                "(user_id, word_id, mastery, last_studied, times_asked, "
                " times_correct, ask_en2ja, ok_en2ja, ask_ja2en, ok_ja2en, "
                " review_level, next_review) "
                "SELECT ?, id, mastery, last_studied, times_asked, "
                " times_correct, ask_en2ja, ok_en2ja, ask_ja2en, ok_ja2en, "
                " review_level, next_review FROM words "
                "WHERE mastery>0 OR times_asked>0 OR review_level>0",
                (uid,),
            )
            conn.execute(
                "INSERT OR REPLACE INTO user_phrase_progress "
                "(user_id, phrase_id, mastery, last_studied, study_count, "
                " times_asked, times_correct, ask_en2ja, ok_en2ja, ask_ja2en, "
                " ok_ja2en, review_level, next_review) "
                "SELECT ?, id, mastery, last_studied, study_count, "
                " times_asked, times_correct, ask_en2ja, ok_en2ja, ask_ja2en, "
                " ok_ja2en, review_level, next_review FROM phrases "
                "WHERE mastery>0 OR times_asked>0 OR review_level>0",
                (uid,),
            )
            conn.execute(
                "INSERT OR REPLACE INTO user_material_progress "
                "(user_id, material_id, mastery) "
                "SELECT ?, id, mastery FROM materials "
                "WHERE COALESCE(mastery,0) > 0",
                (uid,),
            )
        # 確認用カウント
        for uid in uids:
            w = conn.execute(
                "SELECT COUNT(*) FROM user_word_progress WHERE user_id=?",
                (uid,)).fetchone()[0]
            p = conn.execute(
                "SELECT COUNT(*) FROM user_phrase_progress WHERE user_id=?",
                (uid,)).fetchone()[0]
            print(f"user {uid}: words進捗 {w} / phrases進捗 {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
