# ruff: noqa: E501  (data-heavy seed script: long phrase/word lines are fine)
"""Top up the existing "IT・ビルド/エラー" phrase scene (40件) toward ~50件,
authored by Claude (2026-08-04・ユーザー要望).

既存40件で未カバーだった領域を補強: 環境変数・設定ミス、競合状態(race
condition)、CORSエラー、DBマイグレーション失敗、git rebase/detached HEAD、
不安定なテスト(flaky test)、無限ループ・ハング、メモリリーク、Dockerビルド
失敗、Lint/フォーマットチェック失敗、DNS解決失敗など。

No app / OpenAI API calls — everything is hand-written and inserted directly
into the SQLite DB. Duplicates are skipped by english (lowercased).

Run:  python scripts/add_it_build_errors2.py

仕上げ: 投入後に `python scripts/relevel_phrases.py` で難易度を再設定する。
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

PHRASES: list[tuple[str, str]] = [
    ("It's an environment variable issue.", "環境変数の問題です。"),
    ("Did you set the .env file correctly?", ".envファイルは正しく設定しましたか？"),
    ("This looks like a race condition.", "これは競合状態(レースコンディション)のようです。"),
    ("We're hitting a CORS error.", "CORSエラーが発生しています。"),
    ("The database migration failed halfway through.", "DBマイグレーションが途中で失敗しました。"),
    ("Could you run the migration again?", "マイグレーションをもう一度実行していただけますか？"),
    ("I've got a rebase conflict.", "リベースで競合が起きています。"),
    ("You're in a detached HEAD state.", "detached HEAD状態になっています。"),
    ("This test is flaky.", "このテストは不安定です(たまに失敗する)。"),
    ("It passes locally but fails in CI.", "ローカルでは通るのにCIで失敗します。"),
    ("The app is stuck in an infinite loop.", "アプリが無限ループにはまっています。"),
    ("The process just hangs.", "処理がハングしたままです。"),
    ("There's a memory leak somewhere.", "どこかでメモリリークが起きています。"),
    ("The Docker image failed to build.", "Dockerイメージのビルドに失敗しました。"),
    ("The linter is failing on this file.", "この linter チェックがこのファイルで失敗しています。"),
    ("Could you run the formatter before committing?", "コミット前にフォーマッタを実行していただけますか？"),
    ("DNS resolution is failing.", "DNS解決に失敗しています。"),
    ("The connection keeps timing out.", "接続が何度もタイムアウトします。"),
    ("It's a race between two requests.", "2つのリクエストの間で競合が起きています。"),
    ("Let's add some logging to narrow it down.", "原因を絞り込むためにログを追加しましょう。"),
    ("Can you share a minimal reproduction?", "最小限の再現手順を共有していただけますか？"),
    ("The feature flag is still off in production.", "本番ではまだこの機能フラグがOFFのままです。"),
]


def main() -> int:
    with db() as conn:
        existing = {
            r["english"].lower()
            for r in conn.execute("SELECT english FROM phrases").fetchall()
        }
        added = skipped = 0
        for en, ja in PHRASES:
            if en.lower() in existing:
                skipped += 1
                continue
            conn.execute(
                "INSERT INTO phrases (english, japanese, scene) "
                "VALUES (?, ?, 'IT・ビルド/エラー')",
                (en, ja),
            )
            existing.add(en.lower())
            added += 1
    print(f"phrases: +{added} (skipped {skipped})")
    with db() as conn:
        total = conn.execute(
            "SELECT COUNT(*) FROM phrases WHERE scene='IT・ビルド/エラー'"
        ).fetchone()[0]
        print("scene total now:", total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
