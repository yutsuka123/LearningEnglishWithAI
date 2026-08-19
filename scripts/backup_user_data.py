"""ユーザー固有データの定期バックアップ（cron用・2026-08-19）。

単語・フレーズ本体や音声(audio_blobs)のような全ユーザー共有・
再生成可能なコンテンツは対象外。**失うと本人にしか復元できないデータ**
だけを対象に、独立したSQLiteファイルへスナップショットする:
- users（ユーザー登録情報。password_hashは既にハッシュ済みの値）
- user_settings（ユーザーごとのUI設定）
- user_word_progress / user_phrase_progress（習熟度・SRSの進捗）
- decks / deck_words / deck_progress（単語帳）
- phrase_decks / deck_phrases / phrase_deck_progress（フレーズ帳）

`data/backups/user_data_<timestamp>.db` に保存し、直近2世代だけ残す
（本体DB(vocabulary.db、audio_blobs等で数GB)とは別ファイルにすることで、
バックアップ自体は数MB程度に収まる）。

使い方(VPS上、eigo-appコンテナの中のpython3で実行を想定):
  docker exec eigo-app python3 scripts/backup_user_data.py
"""

from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import paths  # noqa: E402
from app.database import init_db  # noqa: E402

_TABLES = [
    "users", "user_settings",
    "user_word_progress", "user_phrase_progress",
    "decks", "deck_words", "deck_progress",
    "phrase_decks", "deck_phrases", "phrase_deck_progress",
]
_KEEP = 2


def _timestamp() -> str:
    # Date.now()相当を使えないスクリプト側の制約は無いが(app本体のJS
    # ワークフローとは無関係)、cron実行の再現性のためOS時刻をそのまま使う。
    import datetime
    return datetime.datetime.now().strftime("%Y%m%dT%H%M%S")


def backup_once(backups_dir: Path) -> Path:
    backups_dir.mkdir(parents=True, exist_ok=True)
    dst_path = backups_dir / f"user_data_{_timestamp()}.db"
    src = sqlite3.connect(str(paths.db_file))
    src.row_factory = sqlite3.Row
    dst = sqlite3.connect(str(dst_path))
    try:
        for table in _TABLES:
            schema_row = src.execute(
                "SELECT sql FROM sqlite_master "
                "WHERE type = 'table' AND name = ?", (table,),
            ).fetchone()
            if not schema_row or not schema_row[0]:
                continue  # テーブル未作成(古いDB)ならスキップ
            dst.execute(schema_row[0])
            cols = [r[1] for r in src.execute(f"PRAGMA table_info({table})")]
            placeholders = ", ".join("?" for _ in cols)
            rows = src.execute(f"SELECT {', '.join(cols)} FROM {table}")
            dst.executemany(
                f"INSERT INTO {table} ({', '.join(cols)}) "
                f"VALUES ({placeholders})",
                rows,
            )
        dst.commit()
    finally:
        src.close()
        dst.close()
    return dst_path


def prune_old(backups_dir: Path, keep: int = _KEEP) -> list[Path]:
    files = sorted(
        backups_dir.glob("user_data_*.db"),
        key=lambda p: p.name, reverse=True,
    )
    removed = []
    for f in files[keep:]:
        f.unlink(missing_ok=True)
        removed.append(f)
    return removed


def main() -> int:
    init_db()
    backups_dir = paths.data_dir / "backups"
    dst_path = backup_once(backups_dir)
    size_kb = dst_path.stat().st_size / 1024
    removed = prune_old(backups_dir)
    print(f"バックアップ作成: {dst_path.name}（{size_kb:.1f}KB）")
    if removed:
        print(f"古い世代を削除: {', '.join(p.name for p in removed)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
