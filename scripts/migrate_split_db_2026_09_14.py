"""単一`vocabulary.db`を content.db/core.db/logs.db の3ファイルへ分割する
一度きりの移行スクリプト(2026-09-14・DB分割フェーズ1)。

設計方針(ユーザー指示・本番メンテ枠での自動実行を前提):
- **完全自動・検証内蔵・高速**。ローカルで繰り返し試験した「同じ
  スクリプト」をそのまま本番メンテ枠でも実行し、10分以内に完了させる
  ことを目標にする。
- 元の`vocabulary.db`は**読み取り専用で開くだけ**(ATTACH元として使う
  のみ)。一切変更・削除しない。うまくいかなければ新3ファイルを消すだけで
  即座に旧構成へ戻せる。
- コピー後、(a)テーブルごとの件数一致、(b)content/core/logs各スキーマの
  PRAGMA foreign_key_check、(c)8列(元々REFERENCESがあったがATTACH間に
  なったため外した列)の孤児件数が移行前後で一致、(d)3スキーマ間で
  テーブル名の重複が無いこと、(e)金額系カラムの合計が一致、
  (f)想定外のテーブル/列が来ていないこと、を自動検証し、1つでも
  失敗したら新3ファイルを削除して非ゼロ終了する。検証に失敗した状態の
  ままコミットすることは無い(全体を1トランザクションにし、検証NGなら
  rollbackしてから新ファイルを削除する)。

⚠️2026-09-14 Fable指摘の重大バグ(C1)を修正: 当初、既存のcore/content/
logs.dbが(切替成功後に実データが書き込まれた状態であっても)無条件に
削除されてから移行が始まっていた。これは9/13の本番DB誤上書き事故と
同型の危険(2回目以降の実行で本番の実データが黙って消える)だったため、
出力ファイルが1つでも既に存在する場合は明示的な`--force-recreate`が
無い限り拒否するようにした。あわせて、移行成功時に`core.db`の
`app_state`へ`db_split_migrated_at`マーカーを書き込み、`--source`に
指定されたファイル自体がこのマーカーを持つ(=既に分割済みのcore.dbを
誤って「まだ分割前の単一DB」として扱おうとしている)場合も拒否する。

使い方:
  python scripts/migrate_split_db_2026_09_14.py
  python scripts/migrate_split_db_2026_09_14.py --source data/vocabulary.db
  python scripts/migrate_split_db_2026_09_14.py --force-recreate  # 既存の
      新3ファイルを消して最初からやり直す(内容を精査した上で明示指定時のみ)
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

# 既知の「使われなくなった列」の許可リスト。ここに無い、新schemaに
# 存在しない列が見つかった場合は(想定外の欠落の可能性があるため)
# 警告ではなく失敗として扱う(Fable指摘M2)。
KNOWN_DROPPED_COLUMNS = {
    ("crossword_sessions", "hint_pct"),
}

# ATTACH間になったため REFERENCES を外した8列(app/database.py参照)。
# 移行前後で「親が存在しない孤児行」の件数が変化していないことを
# 明示チェックする(Fable指摘M2: 通常のforeign_key_checkはこれらの列を
# 見ないため、別立てで検証する必要がある)。
DEREFERENCED_COLUMNS = [
    ("word_attempts", "word_id", "words"),
    ("deck_words", "word_id", "words"),
    ("deck_phrases", "phrase_id", "phrases"),
    ("user_word_progress", "word_id", "words"),
    ("user_phrase_progress", "phrase_id", "phrases"),
    ("user_category_progress", "category_id", "categories"),
    ("user_listening_progress", "topic_id", "listening_topics"),
    ("crossword_sample_plays", "sample_id", "crossword_samples"),
]

# 移行前後で合計額が一致することを確認する金額系カラム(Fable指摘M2)。
MONEY_COLUMNS = [
    ("users", "balance_jpy"),
    ("balance_ledger", "delta_jpy"),
    ("paypay_payments", "amount_jpy"),
    ("charge_keys", "amount_jpy"),
    ("base_orders", "amount_jpy"),
]

MIGRATED_MARKER_KEY = "db_split_migrated_at"


def _delete_new_files() -> None:
    """新3ファイル(前回の失敗分含む)を削除する。旧ファイル(source)は
    ここでは一切触らない。"""
    for p in (paths.db_file, paths.content_db_file, paths.logs_db_file):
        p.unlink(missing_ok=True)
        Path(str(p) + "-wal").unlink(missing_ok=True)
        Path(str(p) + "-shm").unlink(missing_ok=True)


def _existing_new_files() -> list[Path]:
    return [
        p for p in (paths.db_file, paths.content_db_file, paths.logs_db_file)
        if p.exists()
    ]


def _is_already_migrated(db_path: Path) -> bool:
    """指定ファイルが既にこのスクリプトで分割済みのcore.db(=app_stateに
    db_split_migrated_atマーカーがある)かどうか。"""
    if not db_path.exists():
        return False
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        row = conn.execute(
            "SELECT 1 FROM app_state WHERE key = ?", (MIGRATED_MARKER_KEY,)
        ).fetchone()
        conn.close()
        return row is not None
    except sqlite3.Error:
        return False


def _connect_new(attach_old: Path | None = None) -> sqlite3.Connection:
    """main=core(新規)、content/logs(新規)をATTACHした接続を返す。
    `attach_old`を渡すと、旧vocabulary.dbも読取専用でoldとしてATTACHする。
    uri=True: 後続のATTACH文がfile:...?mode=ro形式のURIを使うため
    (Fable指摘: これが無いとlibsqlite3のビルドによってはURI解釈が無効な
    ままになり得る。無効な場合は明示的なエラーになる=サイレントな危険
    ではないが、確実にread-onlyにするため付けておく)。"""
    conn = sqlite3.connect(str(paths.db_file), uri=True)
    conn.row_factory = sqlite3.Row  # _migrate()がr["name"]形式で読むため
    conn.execute(
        "ATTACH DATABASE ? AS content", (str(paths.content_db_file),))
    conn.execute("ATTACH DATABASE ? AS logs", (str(paths.logs_db_file),))
    if attach_old is not None:
        conn.execute(
            f"ATTACH DATABASE 'file:{attach_old}?mode=ro' AS old", ())
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


def _unexpected_source_tables(conn: sqlite3.Connection) -> list[str]:
    """oldにあるがTARGET_SCHEMAに列挙されていないテーブル。想定外の
    未知テーブルは黙ってスキップせず失敗させる(Fable指摘M2)。
    sqlite_sequenceは対象外(AUTOINCREMENT用の内部テーブルで、
    _copy_sqlite_sequenceで別途扱う)。"""
    known = set(TARGET_SCHEMA.keys())
    rows = conn.execute(
        "SELECT name FROM old.sqlite_master "
        "WHERE type = 'table' AND name != 'sqlite_sequence'"
    ).fetchall()
    return [r[0] for r in rows if r[0] not in known]


def _copy_all_tables(conn: sqlite3.Connection) -> dict[str, tuple[int, int]]:
    """oldの各テーブルを新3ファイルへコピーする。戻り値は
    {table: (old_count, new_count)}(コピー直後の実測)。

    列はold/new両方に存在するものだけをコピー対象にする(交差)。
    旧DBには、過去のmigrationで追加されたが現行のSCHEMA/_migrateでは
    もう作られない「使われなくなった列」が残っていることがあり
    (例: crossword_sessions.hint_pct、score_multiplier移行時のコメント
    参照)、そうした列は新側に存在しないため単純な列一致コピーでは
    エラーになる。既知の廃止列(KNOWN_DROPPED_COLUMNS)以外が新側に無い
    場合は、想定外の欠落の可能性があるため失敗扱いにする(Fable指摘M2)。"""
    conn.execute("PRAGMA foreign_keys = OFF")
    counts: dict[str, tuple[int, int]] = {}
    unexpected_dropped: list[tuple[str, str]] = []
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
        for c in dropped:
            if (table, c) in KNOWN_DROPPED_COLUMNS:
                print(f"  {table}: 既知の廃止列を除外 {c}")
            else:
                unexpected_dropped.append((table, c))
        col_list = ", ".join(cols)
        conn.execute(
            f"INSERT INTO {dest} ({col_list}) "
            f"SELECT {col_list} FROM old.{table}"
        )
        old_n = conn.execute(
            f"SELECT COUNT(*) FROM old.{table}").fetchone()[0]
        new_n = conn.execute(f"SELECT COUNT(*) FROM {dest}").fetchone()[0]
        counts[table] = (old_n, new_n)
    if unexpected_dropped:
        raise RuntimeError(
            f"想定外の列欠落(KNOWN_DROPPED_COLUMNSに無い): "
            f"{unexpected_dropped}"
        )
    return counts


def _copy_sqlite_sequence(conn: sqlite3.Connection) -> None:
    """AUTOINCREMENTの採番カウンタ(sqlite_sequence)をold→新3ファイルへ
    引き継ぐ(Fable指摘H2)。これを移行しないと、明示IDでのINSERTは
    「そのテーブルに今あるMAX(id)」までしかカウンタを進めないため、
    削除済みの最大IDより後の欠番が、移行後の新規行に再利用されてしまう
    (決済・チャージキー・ユーザー等のID取り違えリスク)。"""
    old_seq = {
        r["name"]: r["seq"]
        for r in conn.execute("SELECT name, seq FROM old.sqlite_sequence")
    }
    for table, schema in TARGET_SCHEMA.items():
        if table not in old_seq:
            continue
        prefix = f"{schema}." if schema != "main" else ""
        # 新側の実データからのMAX(id)と、oldのseq値の大きい方を採用する
        # (通常はoldのseqの方が大きいはずだが、念のため安全側に倒す)。
        cur_row = conn.execute(
            f"SELECT seq FROM {prefix}sqlite_sequence WHERE name = ?",
            (table,),
        ).fetchone()
        cur_seq = cur_row[0] if cur_row else 0
        new_seq = max(cur_seq, old_seq[table])
        # sqlite_sequenceはAUTOINCREMENT機構が内部管理する特殊テーブルで、
        # name列にON CONFLICTの対象にできる名前付き制約が無い(実行時に
        # "ON CONFLICT clause does not match any PRIMARY KEY or UNIQUE
        # constraint"で失敗することを実機確認済み)。UPDATE→無ければINSERT
        # の素朴な分岐にする。
        if cur_row is not None:
            conn.execute(
                f"UPDATE {prefix}sqlite_sequence SET seq = ? WHERE name = ?",
                (new_seq, table),
            )
        else:
            conn.execute(
                f"INSERT INTO {prefix}sqlite_sequence (name, seq) "
                f"VALUES (?, ?)",
                (table, new_seq),
            )


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


def _all_schema_fk_issues(conn: sqlite3.Connection
                           ) -> dict[tuple[str, str], int]:
    """main/content/logsの3スキーマすべてでforeign_key_checkを行う
    (Fable指摘M2: 無修飾のforeign_key_checkはmainしか見ないため、
    content側の孤児(例: word_domain_tags)を見逃していた)。"""
    merged: dict[tuple[str, str], int] = {}
    for schema in (None, "content", "logs"):
        for key, n in _fk_issue_counts(conn, schema).items():
            merged[key] = merged.get(key, 0) + n
    return merged


def _dereferenced_orphan_counts(
    conn: sqlite3.Connection, prefix: str = "",
) -> dict[tuple[str, str, str], int]:
    """REFERENCESを外した8列について、親が存在しない行数を数える
    (Fable指摘M2: 通常のforeign_key_checkはこれらの列を見ないため)。
    `prefix`が空ならold.*、"new_"ならATTACH済みの新3ファイル側を見る
    (呼び出し側でSQLを組み替える)。"""
    counts: dict[tuple[str, str, str], int] = {}
    for child, col, parent in DEREFERENCED_COLUMNS:
        if prefix == "old":
            child_ref, parent_ref = f"old.{child}", f"old.{parent}"
        else:
            child_schema = TARGET_SCHEMA[child]
            parent_schema = TARGET_SCHEMA[parent]
            child_ref = (
                f"{child_schema}.{child}" if child_schema != "main"
                else child
            )
            parent_ref = (
                f"{parent_schema}.{parent}" if parent_schema != "main"
                else parent
            )
        n = conn.execute(
            f"SELECT COUNT(*) FROM {child_ref} "
            f"WHERE {col} NOT IN (SELECT id FROM {parent_ref})"
        ).fetchone()[0]
        counts[(child, col, parent)] = n
    return counts


def _money_sums(conn: sqlite3.Connection, prefix: str = "") -> dict[str, float]:
    """金額系カラムの合計(Fable指摘M2)。"""
    sums: dict[str, float] = {}
    for table, col in MONEY_COLUMNS:
        if prefix == "old":
            ref = f"old.{table}"
        else:
            schema = TARGET_SCHEMA[table]
            ref = f"{schema}.{table}" if schema != "main" else table
        val = conn.execute(
            f"SELECT COALESCE(SUM({col}), 0) FROM {ref}"
        ).fetchone()[0]
        sums[f"{table}.{col}"] = val
    return sums


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
    ap.add_argument(
        "--force-recreate", action="store_true",
        help="既存のcore.db/content.db/logs.dbがあっても削除してやり直す"
             "(内容を精査した上で明示指定時のみ使うこと)")
    args = ap.parse_args()
    source = Path(args.source)

    if not source.exists():
        print(f"移行元が見つかりません: {source}")
        return 1

    # --- ガード1: 出力ファイルが既に存在する場合は拒否(Fable指摘C1) -------
    existing = _existing_new_files()
    if existing and not args.force_recreate:
        print("エラー: 出力ファイルが既に存在します:")
        for p in existing:
            print(f"  {p}")
        print(
            "既に切替済みの本番core.db等である可能性があります。内容を"
            "精査し、本当に作り直してよい場合のみ --force-recreate を"
            "付けて再実行してください。"
        )
        return 1

    # --- ガード2: sourceが既に分割済みのcore.dbでないか(Fable指摘C1) -----
    if _is_already_migrated(source):
        print(
            f"エラー: {source} は既にこのスクリプトで分割済みのファイル"
            f"(app_state.{MIGRATED_MARKER_KEY}マーカーあり)です。"
            "分割前の単一vocabulary.dbを--sourceに指定してください。"
        )
        return 1

    print(f"移行元: {source} ({source.stat().st_size / 1e6:.1f}MB)")

    # 移行前のold単体でのFK不整合を基準値として記録しておく(今回の分割
    # とは無関係な既存のデータ品質問題を、移行失敗と区別するため)。
    old_conn = sqlite3.connect(str(source))
    old_conn.row_factory = sqlite3.Row
    old_conn.execute("PRAGMA foreign_keys = ON")
    old_fk_baseline = _fk_issue_counts(old_conn)
    old_deref_baseline = {
        (child, col, parent): old_conn.execute(
            f"SELECT COUNT(*) FROM {child} "
            f"WHERE {col} NOT IN (SELECT id FROM {parent})"
        ).fetchone()[0]
        for child, col, parent in DEREFERENCED_COLUMNS
    }
    old_money = {
        f"{table}.{col}": old_conn.execute(
            f"SELECT COALESCE(SUM({col}), 0) FROM {table}"
        ).fetchone()[0]
        for table, col in MONEY_COLUMNS
    }
    old_conn.close()
    if old_fk_baseline:
        print(f"※移行元に既存のFK不整合あり(分割とは無関係・別途要対応): "
              f"{old_fk_baseline}")

    _delete_new_files()
    t0 = time.time()
    _init_new_schema()
    conn = _connect_new(attach_old=source)
    ok = False
    try:
        unexpected_tables = _unexpected_source_tables(conn)
        if unexpected_tables:
            raise RuntimeError(f"未知のテーブル: {unexpected_tables}")

        counts = _copy_all_tables(conn)
        _copy_sqlite_sequence(conn)
        elapsed_copy = time.time() - t0
        print(f"コピー所要時間: {elapsed_copy:.1f}秒")
        for table, (old_n, new_n) in counts.items():
            mark = "  ★不一致" if old_n != new_n else ""
            print(f"  {table}: old={old_n} new={new_n}{mark}")

        conn.execute("PRAGMA foreign_keys = ON")
        new_fk_counts = _all_schema_fk_issues(conn)
        new_fk_issues = _new_fk_issues(old_fk_baseline, new_fk_counts)
        dupes = _check_duplicate_names(conn)
        mismatches = [
            (t, o, n) for t, (o, n) in counts.items() if o != n
        ]
        new_deref = _dereferenced_orphan_counts(conn)
        deref_diff = {
            k: (old_deref_baseline[k], v)
            for k, v in new_deref.items() if v != old_deref_baseline[k]
        }
        new_money = _money_sums(conn)
        money_diff = {
            k: (old_money[k], v)
            for k, v in new_money.items() if abs(v - old_money[k]) > 1e-6
        }

        ok = (
            not mismatches and not new_fk_issues and not dupes
            and not deref_diff and not money_diff
        )
        if ok:
            # 成功マーカーをapp_stateへ記録(Fable指摘C1: 「これは既に
            # 分割済みのcore.dbでは?」を後から検知できるようにする)。
            conn.execute(
                "INSERT INTO app_state (key, value) VALUES (?, datetime('now')) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (MIGRATED_MARKER_KEY,),
            )
            conn.commit()
        else:
            conn.rollback()
    except Exception as exc:
        conn.rollback()
        conn.close()
        print(f"--- 例外発生、ロールバックしました: {exc} ---")
        print("新3ファイルを削除します。")
        _delete_new_files()
        return 1
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
        if deref_diff:
            print(f"参照整合性の変化(旧,新): {deref_diff}")
        if money_diff:
            print(f"金額合計の不一致(旧,新): {money_diff}")
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
