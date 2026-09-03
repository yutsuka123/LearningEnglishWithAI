"""古いDBバックアップ/デプロイ前スナップショットを世代管理で削除する
（cron用・2026-09-03）。

背景: デプロイ前(`vocabulary.predeploy-*.db`)・DB一括修正前
(`backup_vocabulary_pre_*.db`)の安全策としてのバックアップ取得は徹底
されていたが、作業成功後にそれを消す工程が無く、6/16以降ずっと蓄積し
続けて本番VPSで3.3GB(109件)に達していた（2026-09-03のVPS総点検で発覚）。
各カテゴリごとに「直近KEEP件を残し、それより古いものだけ削除する」
世代管理を導入し、VPSのcrontabで定期実行することで再発を防ぐ。

安全策（誤って大事なファイルを消さないため）:
- 対象パターンは明示的に3つだけ。稼働中の`vocabulary.db`本体や、
  `data/backups/`配下のuser_data定期バックアップ(既に少量・別枠)は
  意図的に対象外(このパターンには一致しない)。
- 各パターンごとに独立してKEEP件数を保証（1カテゴリでも想定外の
  状態でも他のカテゴリに影響しない）。
- 既定はdry-run。実際に削除するには `--execute` を明示する。
- 削除件数・削除ファイル名を必ず標準出力に記録する（cron経由で
  ログに残るようにするため）。

使い方:
  python scripts/prune_old_backups.py                # dry-run（確認のみ）
  python scripts/prune_old_backups.py --execute       # 実際に削除
  python scripts/prune_old_backups.py --data-dir /home/ubuntu/eigo/data --execute
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# (glob パターン, 残す件数)
TARGETS = [
    ("backup_vocabulary_2*.db", 5),      # 定期/作業前アドホックのバックアップ
    ("backup_vocabulary_pre_*.db", 5),   # DB一括修正前のアドホックバックアップ
    ("vocabulary.predeploy-*.db", 5),    # デプロイ前スナップショット
]


def prune_pattern(data_dir: Path, pattern: str, keep: int, execute: bool) -> None:
    files = sorted(
        data_dir.glob(pattern),
        key=lambda p: p.stat().st_mtime,
        reverse=True,  # 新しい順
    )
    to_delete = files[keep:]
    if not to_delete:
        print(f"{pattern}: {len(files)}件（削除対象なし、KEEP={keep}）")
        return
    total_bytes = sum(p.stat().st_size for p in to_delete)
    label = "削除" if execute else "[dry-run] 削除予定"
    print(f"{pattern}: {len(files)}件中 {len(to_delete)}件を{label} "
          f"({total_bytes / 1e6:.1f}MB) — 残すのは最新{keep}件")
    for p in to_delete:
        print(f"  {label}: {p.name}")
        if execute:
            p.unlink()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-dir", default="data")
    ap.add_argument("--execute", action="store_true",
                     help="指定しない場合はdry-run（何も削除しない）")
    args = ap.parse_args()
    data_dir = Path(args.data_dir)
    if not data_dir.is_dir():
        print(f"data-dirが見つかりません: {data_dir}")
        return 1
    for pattern, keep in TARGETS:
        prune_pattern(data_dir, pattern, keep, args.execute)
    return 0


if __name__ == "__main__":
    sys.exit(main())
