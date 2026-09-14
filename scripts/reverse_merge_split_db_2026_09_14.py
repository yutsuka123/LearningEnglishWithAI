"""content.db/core.db/logs.dbの3ファイルを単一vocabulary.dbへ統合する
「逆マージ」スクリプト(2026-09-14・DB分割フェーズ3のロールバック手段)。

## なぜ必要か(Fableレビュー指摘H3)
DB分割の切替後、本番でしばらく稼働してから重大な問題が見つかり「分割前の
コードに戻したい」となった場合、**単純に旧vocabulary.dbのバックアップへ
差し替えるだけでは、切替後にあった新規登録・決済・学習記録が全て消えて
しまう**(切替後の「新しいデータ」は3分割ファイル側にしか存在しないため)。
本スクリプトは3分割ファイルの現在の内容を単一ファイルへ統合し直すことで、
「分割前のコードに戻しつつ、切替後のデータも失わない」ロールバックを
可能にする。

## 設計方針(移行スクリプトscripts/migrate_split_db_2026_09_14.pyと対称)
- 出力(単一vocabulary.db)ファイルが既に存在する場合は`--force-recreate`
  無しでは拒否する(移行スクリプトのC1対応と同じ考え方)。
- スキーマは`scripts/pre_split_schema_2026_09_14.sql`(分割前の静的
  スナップショット)から作る。**git管理外(rsyncのみ配置)の本番環境でも
  動く必要がある**ため、gitのブランチ参照には一切依存しない。
- content.db/core.db/logs.dbは読み取り専用でATTACHするだけで、
  一切変更・削除しない(うまくいかなければ出力ファイルを消すだけで
  即座にやり直せる)。
- コピー後、(a)テーブルごとの件数一致、(b)復元されたFOREIGN KEY制約
  (分割時に外した8列+phrase_attempts.phrase_idの計9列を含む)での
  `PRAGMA foreign_key_check`、(c)金額系カラムの合計一致、を検証し、
  1つでも失敗したら出力ファイルを削除して非ゼロ終了する。
- sqlite_sequence(自動採番カウンタ)も3ファイルから引き継ぎ、最大値を
  採用する(移行スクリプトのH2対応と対称)。

## 使い方
  python scripts/reverse_merge_split_db_2026_09_14.py \\
      --content data/content.db --core data/core.db --logs data/logs.db \\
      --output data/vocabulary.db
  (既定では data/ 配下の content.db/core.db/logs.db → data/vocabulary.db)
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import paths  # noqa: E402

SCHEMA_FILE = Path(__file__).resolve().parent / "pre_split_schema_2026_09_14.sql"

# 移行スクリプトのTARGET_SCHEMAと同じ分類(逆方向のコピー元を示す)。
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
SOURCE_SCHEMA = (
    {t: "content" for t in CONTENT_TABLES}
    | {t: "logs" for t in LOGS_TABLES}
    | {t: "core" for t in CORE_TABLES}
)

MONEY_COLUMNS = [
    ("users", "balance_jpy"),
    ("balance_ledger", "delta_jpy"),
    ("paypay_payments", "amount_jpy"),
    ("charge_keys", "amount_jpy"),
    ("base_orders", "amount_jpy"),
]


def _connect_output(output: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(output), uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _attach_sources(
    conn: sqlite3.Connection, content: Path, core: Path, logs: Path,
) -> None:
    conn.execute(f"ATTACH DATABASE 'file:{content}?mode=ro' AS content", ())
    conn.execute(f"ATTACH DATABASE 'file:{core}?mode=ro' AS core", ())
    conn.execute(f"ATTACH DATABASE 'file:{logs}?mode=ro' AS logs", ())


def _copy_all_tables(conn: sqlite3.Connection) -> dict[str, tuple[int, int]]:
    """各ソースから出力ファイルへコピーする。FOREIGN KEYは分割時に外した
    9列を含めて全て復元されるため、コピー中は一時的にOFFにする(親→子の
    順序に依存せず一括コピーするため)。"""
    conn.execute("PRAGMA foreign_keys = OFF")
    counts: dict[str, tuple[int, int]] = {}
    for table, schema in SOURCE_SCHEMA.items():
        src_cols = [
            r[1] for r in conn.execute(f"PRAGMA {schema}.table_info({table})")
        ]
        if not src_cols:
            counts[table] = (0, 0)
            continue
        dst_cols = {r[1] for r in conn.execute(f"PRAGMA table_info({table})")}
        cols = [c for c in src_cols if c in dst_cols]
        dropped = [c for c in src_cols if c not in dst_cols]
        if dropped:
            print(f"  {table}: 出力schemaに無い列を除外 {dropped}")
        col_list = ", ".join(cols)
        conn.execute(
            f"INSERT INTO {table} ({col_list}) "
            f"SELECT {col_list} FROM {schema}.{table}"
        )
        src_n = conn.execute(
            f"SELECT COUNT(*) FROM {schema}.{table}").fetchone()[0]
        dst_n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        counts[table] = (src_n, dst_n)
    return counts


def _copy_sqlite_sequence(conn: sqlite3.Connection) -> None:
    for schema in ("content", "core", "logs"):
        rows = conn.execute(
            f"SELECT name, seq FROM {schema}.sqlite_sequence"
        ).fetchall()
        for name, seq in rows:
            cur = conn.execute(
                "SELECT seq FROM sqlite_sequence WHERE name = ?", (name,)
            ).fetchone()
            new_seq = max(seq, cur[0] if cur else 0)
            if cur is not None:
                conn.execute(
                    "UPDATE sqlite_sequence SET seq = ? WHERE name = ?",
                    (new_seq, name),
                )
            else:
                conn.execute(
                    "INSERT INTO sqlite_sequence (name, seq) VALUES (?, ?)",
                    (name, new_seq),
                )


def _money_sums(conn: sqlite3.Connection, from_sources: bool
                 ) -> dict[str, float]:
    sums: dict[str, float] = {}
    for table, col in MONEY_COLUMNS:
        ref = f"{SOURCE_SCHEMA[table]}.{table}" if from_sources else table
        val = conn.execute(
            f"SELECT COALESCE(SUM({col}), 0) FROM {ref}"
        ).fetchone()[0]
        sums[f"{table}.{col}"] = val
    return sums


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", default=str(paths.content_db_file))
    ap.add_argument("--core", default=str(paths.db_file))
    ap.add_argument("--logs", default=str(paths.logs_db_file))
    ap.add_argument(
        "--output", default=str(paths.data_dir / "vocabulary.db"))
    ap.add_argument("--force-recreate", action="store_true")
    args = ap.parse_args()

    content, core, logs = Path(args.content), Path(args.core), Path(args.logs)
    output = Path(args.output)

    for p in (content, core, logs):
        if not p.exists():
            print(f"入力ファイルが見つかりません: {p}")
            return 1
    if not SCHEMA_FILE.exists():
        print(f"スキーマ定義ファイルが見つかりません: {SCHEMA_FILE}")
        return 1

    if output.exists() and not args.force_recreate:
        print(f"エラー: 出力ファイルが既に存在します: {output}")
        print("本当に作り直してよい場合のみ --force-recreate を付けて"
              "再実行してください。")
        return 1
    if output.exists():
        output.unlink()
        Path(str(output) + "-wal").unlink(missing_ok=True)
        Path(str(output) + "-shm").unlink(missing_ok=True)

    # 統合前の金額基準値(3分割ファイル側から)を、出力ファイル作成前に
    # 別接続で取っておく(比較のため)。
    pre_conn = sqlite3.connect(":memory:")
    _attach_sources(pre_conn, content, core, logs)
    pre_money = _money_sums(pre_conn, from_sources=True)
    pre_conn.close()

    t0 = time.time()
    conn = _connect_output(output)
    try:
        conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
        _attach_sources(conn, content, core, logs)

        counts = _copy_all_tables(conn)
        _copy_sqlite_sequence(conn)
        elapsed = time.time() - t0
        print(f"コピー所要時間: {elapsed:.1f}秒")
        for table, (src_n, dst_n) in counts.items():
            mark = "  ★不一致" if src_n != dst_n else ""
            print(f"  {table}: src={src_n} dst={dst_n}{mark}")

        conn.execute("PRAGMA foreign_keys = ON")
        fk_issues = conn.execute("PRAGMA foreign_key_check").fetchall()
        mismatches = [
            (t, s, d) for t, (s, d) in counts.items() if s != d
        ]
        post_money = _money_sums(conn, from_sources=False)
        money_diff = {
            k: (pre_money[k], v)
            for k, v in post_money.items() if abs(v - pre_money[k]) > 1e-6
        }

        ok = not mismatches and not fk_issues and not money_diff
        if ok:
            conn.commit()
        else:
            conn.rollback()
    except Exception as exc:
        conn.rollback()
        conn.close()
        print(f"--- 例外発生、ロールバックしました: {exc} ---")
        output.unlink(missing_ok=True)
        return 1
    conn.close()

    if not ok:
        print("--- 検証失敗 ---")
        if mismatches:
            print(f"件数不一致: {mismatches}")
        if fk_issues:
            print(f"FK不整合: {[dict(r) for r in fk_issues]}")
        if money_diff:
            print(f"金額合計の不一致(統合前,統合後): {money_diff}")
        print("出力ファイルを削除します。")
        output.unlink(missing_ok=True)
        return 1

    print("--- 検証OK ---")
    print(f"統合ファイル: {output}")
    print("content.db/core.db/logs.dbは変更していません(そのまま残ります)。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
