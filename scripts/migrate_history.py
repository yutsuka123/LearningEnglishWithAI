"""ローカル(owner=既定user_id 1)の会話/学習履歴・memory/study_log を、
指定ユーザーへ複製する（per-user化後の「実績の引き継ぎ」用）。

進捗(mastery/SRS)は scripts/migrate_progress.py で複製済み。本スクリプトは
それ以外の履歴系を移す:
- conversation_log / study_sessions の owner 行を対象userへ複製。
- 旧 data/memory.md / data/study_log.md を data/users/<uid>/ へ配置(無ければ)。

使い方:
  python scripts/migrate_history.py --from 1 --to 3
  python scripts/migrate_history.py --from 1 --to 1 3   # owner自身にも配置
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import paths  # noqa: E402
from app.database import db, init_db  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--from", dest="src", type=int, default=1)
    ap.add_argument("--to", dest="dst", type=int, nargs="+", required=True)
    args = ap.parse_args()
    init_db()
    src = args.src
    with db() as conn:
        for dst in args.dst:
            if dst == src:
                # owner自身: 行の複製は不要（既に user_id=src のまま）。
                pass
            else:
                # 既存の複製を一旦消して二重登録を防ぐ（冪等）。
                conn.execute(
                    "DELETE FROM conversation_log WHERE user_id = ?", (dst,))
                conn.execute(
                    "DELETE FROM study_sessions WHERE user_id = ?", (dst,))
                conn.execute(
                    "INSERT INTO conversation_log "
                    "(role, content, mode, created_at, user_id) "
                    "SELECT role, content, mode, created_at, ? "
                    "FROM conversation_log WHERE user_id = ?", (dst, src))
                conn.execute(
                    "INSERT INTO study_sessions "
                    "(study_date, content, accuracy, weak_points, next_topic, "
                    " new_words, created_at, session_key, user_id) "
                    "SELECT study_date, content, accuracy, weak_points, "
                    " next_topic, new_words, created_at, session_key, ? "
                    "FROM study_sessions WHERE user_id = ?", (dst, src))
            c = conn.execute(
                "SELECT (SELECT COUNT(*) FROM conversation_log WHERE "
                " user_id=?) cl, (SELECT COUNT(*) FROM study_sessions WHERE "
                " user_id=?) ss", (dst, dst)).fetchone()
            print(f"user {dst}: conversation {c['cl']} / sessions {c['ss']}")

    # memory.md / study_log.md を per-user ディレクトリへ配置（無ければ）。
    legacy_mem = paths.data_dir / "memory.md"
    legacy_log = paths.data_dir / "study_log.md"
    for dst in args.dst:
        udir = paths.data_dir / "users" / str(dst)
        udir.mkdir(parents=True, exist_ok=True)
        for legacy, name in ((legacy_mem, "memory.md"),
                             (legacy_log, "study_log.md")):
            target = udir / name
            if legacy.exists() and not target.exists():
                shutil.copy2(legacy, target)
                print(f"copied {legacy.name} -> users/{dst}/{name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
