"""汎用DBスナップショット(cron用・2026-09-14・フェーズ0)。

`deploy/scheduled_deploy.sh`のデプロイ時バックアップと同じ
`sqlite3.Connection.backup()` API(稼働中のDBでも安全にコピーできる)を
使い、対象ファイル1つを`data/backups/`へスナップショットし、世代管理
(`--keep`)で古いものを削除する。`scripts/backup_user_data.py`と違い
テーブルを個別指定せず**ファイルまるごと**コピーする汎用スクリプト。

背景: 2026-09-13の本番DB誤上書き事故を受け、既存の「デプロイ時のみ」
バックアップに加えて、ピーク時間帯(19-24時)を避けた6時間おき
(03/09/15/21 JST)の短期バックアップ層を追加する(ユーザー指示)。
DB分割(docs/TODO.md「DB分割の検討」参照)後は、content.db/core.db/
logs.dbそれぞれに対して`--label`/`--keep`を変えて個別に実行する想定
（ログ3世代・コア(決済含む)5世代・コンテンツは更新の都度3世代以上）。
分割前の現状は`vocabulary.db`全体が対象。

使い方:
  python scripts/backup_snapshot.py --keep 5
  python scripts/backup_snapshot.py --source data/logs.db --label logs --keep 3
  docker exec eigo-app python3 scripts/backup_snapshot.py --keep 5
"""

from __future__ import annotations

import argparse
import datetime
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import paths  # noqa: E402


def backup_once(source: Path, backups_dir: Path, label: str) -> Path:
    backups_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    dst_path = backups_dir / f"snapshot_{label}_{stamp}.db"
    src = sqlite3.connect(str(source))
    dst = sqlite3.connect(str(dst_path))
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()
    return dst_path


def prune_old(backups_dir: Path, label: str, keep: int) -> list[Path]:
    files = sorted(
        backups_dir.glob(f"snapshot_{label}_*.db"),
        key=lambda p: p.name, reverse=True,
    )
    removed = []
    for f in files[keep:]:
        f.unlink(missing_ok=True)
        removed.append(f)
    return removed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--source", default=None,
        help="バックアップ対象のDBファイル(既定: paths.db_file=現行vocabulary.db)")
    ap.add_argument(
        "--label", default="db",
        help="ファイル名に使う識別子(分割後はcontent/core/logs等を想定)")
    ap.add_argument(
        "--keep", type=int, required=True, help="残す世代数")
    args = ap.parse_args()

    source = Path(args.source) if args.source else paths.db_file
    if not source.exists():
        print(f"バックアップ対象が見つかりません: {source}")
        return 1

    backups_dir = paths.data_dir / "backups"
    dst_path = backup_once(source, backups_dir, args.label)
    size_mb = dst_path.stat().st_size / 1e6
    removed = prune_old(backups_dir, args.label, args.keep)

    print(f"バックアップ作成: {dst_path.name}（{size_mb:.1f}MB）")
    if removed:
        print(f"古い世代を削除: {', '.join(p.name for p in removed)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
