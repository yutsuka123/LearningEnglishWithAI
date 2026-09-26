"""DB更新スクリプト共通の安全装置(2026-09-26・敵対的レビュー指摘)。

- default_backup_dir(): バックアップの既定の置き場。**コンテナ内のCWD相対`data/`は`docker compose run --rm`の終了で
  コンテナごと消える**(本番はホストの`~/eigo/data`が`/data`にマウントされている)ため、DATA_DIR(=マウントされた
  データディレクトリ)配下にする。これで実行後もバックアップが残り、`--rollback`が使える。
- key_counts()/print_counts(): CLAUDE.md「本番DBに書き込んだら直後に主要テーブルの件数を確認する」用。
  更新前後で件数が変わらないこと(語彙の1回限りの更新は行数を増減させない)を各スクリプトが確認する。
"""

from __future__ import annotations

from pathlib import Path

KEY_TABLES = ("words", "phrases", "users", "paypay_payments", "landing_visits", "usage_events")


def default_backup_dir() -> Path:
    from app.config import paths
    return Path(paths.data_dir) / "script_backups"


def key_counts(conn) -> dict[str, int]:
    out: dict[str, int] = {}
    for t in KEY_TABLES:
        try:
            out[t] = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except Exception:
            out[t] = -1   # そのDB構成に無い表
    return out


def print_counts(label: str, counts: dict[str, int]) -> None:
    print(f"  [{label}] " + " / ".join(f"{k}={v}" for k, v in counts.items() if v >= 0))


def same_counts(before: dict[str, int], after: dict[str, int]) -> bool:
    return before == after
