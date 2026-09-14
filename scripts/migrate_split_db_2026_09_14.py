"""単一`vocabulary.db`を content.db/core.db/logs.db の3ファイルへ分割する
一度きりの移行スクリプト(2026-09-14・DB分割フェーズ1)。

設計方針(ユーザー指示・本番メンテ枠での自動実行を前提):
- **完全自動・検証内蔵・高速**。ローカルで繰り返し試験した「同じ
  スクリプト」をそのまま本番メンテ枠でも実行し、10分以内に完了させる
  ことを目標にする。
- 元の`vocabulary.db`は**読み取り専用で開くだけ**(ATTACH元として使う
  のみ)。一切変更・削除しない。うまくいかなければ新3ファイルを消すだけで
  即座に旧構成へ戻せる。
- コピー後、(a)テーブルごとの件数一致、(b)PRAGMA foreign_key_checkで
  ATTACH後の参照整合性、(c)3スキーマ間でテーブル名の重複が無いこと
  (`app.database._check_no_duplicate_table_names`と同じロジック)を
  自動検証し、1つでも失敗したら新3ファイルを削除して非ゼロ終了する。
  検証に失敗した状態のままコミットすることは無い(全体を1トランザクション
  にし、検証NGならrollbackしてから新ファイルを削除する)。

使い方:
  python scripts/migrate_split_db_2026_09_14.py
  python scripts/migrate_split_db_2026_09_14.py --source data/vocabulary.db
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import paths  # noqa: E402

# 対象テーブル → 分割後のスキーマ(schema-qualify不要な物は"main"=core)。
# app/database.py の SCHEMA で実際にどのスキーマにCREATEしているかと
# 完全一致させること(ズレると移行後にテーブルが見つからなくなる)。
CONTENT_TABLES = [
    "words", "phrases", "categories", "listening_topics",
    "word_domain_tags", "crossword_samples", "audio_blobs",
]
LOGS_TABLES = [
    "landing_visits", "ip_geo_cache", "login_log", "usage_events",
    "client_errors",
]
CORE_TABLES = [
    "word_attempts", "materials", "study_sessions", "phrase_attempts",
    "ai_usage", "conversation_log", "app_state", "decks", "deck_words",
    "deck_progress", "phrase_decks", "deck_phrases", "phrase_deck_progress",
    "users", "user_word_progress", "user_material_progress",
    "user_category_progress", "user_listening_progress", "user_settings",
    "user_settings_backups", "user_phrase_progress", "charge_keys",
    "balance_ledger", "charge_key_attempts", "base_order_actions",
    "paypay_actions", "paypay_payments", "inquiries", "base_api_tokens",
    "base_orders", "crossword_sessions", "crossword_sample_plays",
]

TARGET_SCHEMA = (
    {t: "content" for t in CONTENT_TABLES}
    | {t: "logs" for t in LOGS_TABLES}
    | {t: "main" for t in CORE_TABLES}
)


def _delete_new_files() -> None:
    """新3ファイル(前回の失敗分含む)を削除する。旧ファイル(source)は
    ここでは一切触らない。"""
    for p in (paths.db_file, paths.content_db_file, paths.logs_db_file):
        p.unlink(missing_ok=True)
        Path(str(p) + "-wal").unlink(missing_ok=True)
        Path(str(p) + "-shm").unlink(missing_ok=True)


def _connect_new(attach_old: Path | None = None) -> sqlite3.Connection:
    """main=core(新規)、content/logs(新規)をATTACHした接続を返す。
    `attach_old`を渡すと、旧vocabulary.dbも読取専用でoldとしてATTACHする。"""
    conn = sqlite3.connect(str(paths.db_file))
    conn.row_factory = sqlite3.Row  # _migrate()がr["name"]形式で読むため
    conn.execute(
        "ATTACH DATABASE ? AS content", (str(paths.content_db_file),))
    conn.execute("ATTACH DATABASE ? AS logs", (str(paths.logs_db_file),))
    if attach_old is not None:
        conn.execute(f"ATTACH DATABASE 'file:{attach_old}?mode=ro' AS old")
    return conn


def _init_new_schema() -> None:
    """新3ファイルにSCHEMA+_migrate(カラム追加等)を適用する。oldはまだ
    ATTACHしない(unqualifiedなテーブル名がoldの同名テーブルと衝突する
    リスクを避けるため、schema初期化とold読み込みは接続を分ける)。

    `_migrate`はusersが空の場合にplaceholderのownerを1行自動作成する
    副作用があるため、ここで作った直後に削除する(実データは後続の
    コピー処理でold.usersから入る)。"""
    conn = _connect_new()
    try:
        from app.database import SCHEMA, _migrate
        conn.executescript(SCHEMA)
        _migrate(conn)
        conn.execute("DELETE FROM users")
        conn.commit()
    finally:
        conn.close()


def _copy_all_tables(conn: sqlite3.Connection) -> dict[str, tuple[int, int]]:
    """oldの各テーブルを新3ファイルへコピーする。戻り値は
    {table: (old_count, new_count)}(コピー直後の実測)。

    列はold/new両方に存在するものだけをコピー対象にする(交差)。
    旧DBには、過去のmigrationで追加されたが現行のSCHEMA/_migrateでは
    もう作られない「使われなくなった列」が残っていることがあり
    (例: crossword_sessions.hint_pct、score_multiplier移行時のコメント
    参照)、そうした列は新側に存在しないため単純な列一致コピーでは
    エラーになる。新側に無い列は実害の無い廃止済み列とみなしコピー対象
    から除外し、標準出力に列名を明示する(サイレントに落とさない)。"""
    conn.execute("PRAGMA foreign_keys = OFF")
    counts: dict[str, tuple[int, int]] = {}
    for table, schema in TARGET_SCHEMA.items():
        old_cols = [
            r[1] for r in conn.execute(f"PRAGMA old.table_info({table})")
        ]
        if not old_cols:
            # 旧DBに存在しないテーブル(古いバックアップ等)はスキップ。
            counts[table] = (0, 0)
            continue
        dest = f"{schema}.{table}" if schema != "main" else table
        new_cols = {
            r[1] for r in conn.execute(f"PRAGMA {schema}.table_info({table})")
        }
        cols = [c for c in old_cols if c in new_cols]
        dropped = [c for c in old_cols if c not in new_cols]
        if dropped:
            print(f"  {table}: 新schemaに無い列を除外 {dropped}")
        col_list = ", ".join(cols)
        conn.execute(
            f"INSERT INTO {dest} ({col_list}) "
            f"SELECT {col_list} FROM old.{table}"
        )
        old_n = conn.execute(
            f"SELECT COUNT(*) FROM old.{table}").fetchone()[0]
        new_n = conn.execute(f"SELECT COUNT(*) FROM {dest}").fetchone()[0]
        counts[table] = (old_n, new_n)
    return counts


def _fk_issue_counts(conn: sqlite3.Connection, schema: str | None = None
                      ) -> dict[tuple[str, str], int]:
    """(table, parent)ごとの不整合件数。schema省略時はmain(暗黙)。
    fkidは「そのテーブルに定義されたFK制約の何番目か」という通し番号に
    過ぎず、今回の分割で他の列のREFERENCES句を削除するとズレる(実質
    同じ制約でも番号が変わる)ため、キーには含めない。"""
    stmt = (
        f"PRAGMA {schema}.foreign_key_check" if schema
        else "PRAGMA foreign_key_check"
    )
    counts: dict[tuple[str, str], int] = {}
    for r in conn.execute(stmt):
        key = (r["table"], r["parent"])
        counts[key] = counts.get(key, 0) + 1
    return counts


def _new_fk_issues(
    old_counts: dict[tuple[str, str], int],
    new_counts: dict[tuple[str, str], int],
) -> dict[tuple[str, str], int]:
    """移行前(旧ファイル単体)には無かった/増えた不整合だけを返す。
    旧DBに元から存在する不整合(今回の分割とは無関係な既存のデータ品質
    問題)は移行の合否判定に含めない(別途要修正としてTODOで扱う)。"""
    new_only = {}
    for key, n in new_counts.items():
        base = old_counts.get(key, 0)
        if n > base:
            new_only[key] = n - base
    return new_only


def _check_duplicate_names(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name, 'main' AS db FROM sqlite_master "
        "WHERE type='table' AND name != 'sqlite_sequence' "
        "UNION ALL "
        "SELECT name, 'content' FROM content.sqlite_master "
        "WHERE type='table' AND name != 'sqlite_sequence' "
        "UNION ALL "
        "SELECT name, 'logs' FROM logs.sqlite_master "
        "WHERE type='table' AND name != 'sqlite_sequence'"
    ).fetchall()
    seen: dict[str, str] = {}
    dupes = []
    for name, dbname in rows:
        if name in seen and seen[name] != dbname:
            dupes.append(f"{name}({seen[name]}/{dbname})")
        else:
            seen[name] = dbname
    return dupes


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--source", default=str(paths.data_dir / "vocabulary.db"),
        help="移行元(旧・単一DB)のパス")
    args = ap.parse_args()
    source = Path(args.source)

    if not source.exists():
        print(f"移行元が見つかりません: {source}")
        return 1
    print(f"移行元: {source} ({source.stat().st_size / 1e6:.1f}MB)")

    # 移行前のold単体でのFK不整合を基準値として記録しておく(今回の分割
    # とは無関係な既存のデータ品質問題を、移行失敗と区別するため)。
    old_conn = sqlite3.connect(str(source))
    old_conn.row_factory = sqlite3.Row
    old_conn.execute("PRAGMA foreign_keys = ON")
    old_fk_baseline = _fk_issue_counts(old_conn)
    old_conn.close()
    if old_fk_baseline:
        print(f"※移行元に既存のFK不整合あり(分割とは無関係・別途要対応): "
              f"{old_fk_baseline}")

    _delete_new_files()
    t0 = time.time()
    _init_new_schema()
    conn = _connect_new(attach_old=source)
    try:
        counts = _copy_all_tables(conn)
        elapsed_copy = time.time() - t0
        print(f"コピー所要時間: {elapsed_copy:.1f}秒")
        for table, (old_n, new_n) in counts.items():
            mark = "  ★不一致" if old_n != new_n else ""
            print(f"  {table}: old={old_n} new={new_n}{mark}")

        conn.execute("PRAGMA foreign_keys = ON")
        new_fk_counts = _fk_issue_counts(conn)
        new_fk_issues = _new_fk_issues(old_fk_baseline, new_fk_counts)
        dupes = _check_duplicate_names(conn)
        mismatches = [
            (t, o, n) for t, (o, n) in counts.items() if o != n
        ]

        ok = not mismatches and not new_fk_issues and not dupes
        if ok:
            conn.commit()
        else:
            conn.rollback()
    finally:
        conn.close()

    print(f"合計所要時間: {time.time() - t0:.1f}秒")

    if not ok:
        print("--- 検証失敗 ---")
        if mismatches:
            print(f"件数不一致: {mismatches}")
        if new_fk_issues:
            print(f"移行で新たに発生したFK不整合: {new_fk_issues}")
        if dupes:
            print(f"テーブル名重複: {dupes}")
        print("新3ファイルを削除してロールバックします。")
        _delete_new_files()
        return 1

    print("--- 検証OK ---")
    print(f"新ファイル: {paths.db_file}, {paths.content_db_file}, "
          f"{paths.logs_db_file}")
    print("旧ファイルはそのまま残しています(ロールバック用に保持)。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
