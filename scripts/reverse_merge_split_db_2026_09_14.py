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
- スキーマは`scripts/pre_split_schema_2026_09_14.sql`(分割前の静的
  スナップショット)から作る。**git管理外(rsyncのみ配置)の本番環境でも
  動く必要がある**ため、gitのブランチ参照には一切依存しない。
- content.db/core.db/logs.dbは読み取り専用でATTACHするだけで、
  一切変更・削除しない。
- コピー後、(a)テーブルごとの件数一致、(b)復元されたFOREIGN KEY制約
  (分割時に外した9列を含む)での`PRAGMA foreign_key_check`、
  (c)金額系カラムの合計一致、(d)想定外のテーブル/列が無いこと、を検証し、
  1つでも失敗したら出力を破棄して非ゼロ終了する。
- sqlite_sequence(自動採番カウンタ)も3ファイルから引き継ぎ、最大値を
  採用する(移行スクリプトのH2対応と対称)。

## 2026-09-14 3回目Fableレビューで発見・修正した重大な欠陥
初版は以下3件の「本番DBを消しかねない」欠陥を持っていた(いずれも実機で
再現・修正確認済み):
- **HIGH-2**: 既定の`--output`が、切替スクリプトがロールバック用に温存する
  `vocabulary.db`そのものだった上、`--force-recreate`時に**マージ成功を
  確認する前に**既存ファイルを削除していたため、途中で失敗すると単一
  ファイルのDBが一つも残らない状態になり得た。
  → 一時ファイルに書き込み→検証成功後にのみ`os.replace`で原子的に置換
  する方式に変更。既存ファイルは検証成功まで一切削除しない。既定の
  出力名も`vocabulary.merged-<timestamp>.db`という新規名にし、
  `vocabulary.db`への配置は運用者の明示判断(mv)に委ねる。
- **HIGH-3**: `--output`が入力ファイル(例: core.db)自身を指せてしまい、
  `--force-recreate`と組み合わせると本番の生きているcore.dbを削除できた
  (移行スクリプトのL-3と対称の穴)。
  → 出力パスが3入力のいずれかと一致する場合は明示的に拒否する。
- **HIGH-1**: マージ成功後も3分割ファイルをそのまま残す設計だったため、
  「ロールバック→分割前コードでしばらく稼働→分割コードへ再デプロイ」
  という経路で、**古いまま凍結された分割ファイルの上で分割コードが
  黙って正常起動**してしまう(=切替直後のC3ガードと同種の「静かに古い
  データで健全起動する」危険)。
  → マージ成功後、既定で3入力ファイルを`.superseded-<timestamp>`という
  名前にリネームする(`--keep-split-files`で無効化可能)。あわせて
  移行済みマーカー(`app_state.db_split_migrated_at`)は出力へコピー
  せず、代わりに`db_reverse_merged_at`マーカーを書き込む(移行スクリプト
  の`_is_already_migrated`が誤反応しないようにするため)。

## 使い方
  python scripts/reverse_merge_split_db_2026_09_14.py \\
      --content data/content.db --core data/core.db --logs data/logs.db
  (出力は既定で data/vocabulary.merged-<timestamp>.db。確認後、運用者が
  明示的に data/vocabulary.db へリネームすること)
"""

from __future__ import annotations

import argparse
import datetime
import os
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import paths  # noqa: E402

SCHEMA_FILE = Path(__file__).resolve().parent / "pre_split_schema_2026_09_14.sql"
FORWARD_MARKER_KEY = "db_split_migrated_at"
REVERSE_MARKER_KEY = "db_reverse_merged_at"

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

# 分割時にREFERENCESを外した9列(移行スクリプトのDEREFERENCED_COLUMNSと
# 同一)。--prune-orphans指定時、親が存在しない子行をここに従って削除する
# (Fable指摘M-1: 復元されたFKにより、分割後に道連れ削除が効かない経路
# (例: content.db側を直接いじる一括削除スクリプト)で生じた孤児行が
# マージを無条件に止めてしまう問題への、明示オプトインの救済策)。
DEREFERENCED_COLUMNS = [
    ("word_attempts", "word_id", "words"),
    ("phrase_attempts", "phrase_id", "phrases"),
    ("deck_words", "word_id", "words"),
    ("deck_phrases", "phrase_id", "phrases"),
    ("user_word_progress", "word_id", "words"),
    ("user_phrase_progress", "phrase_id", "phrases"),
    ("user_category_progress", "category_id", "categories"),
    ("user_listening_progress", "topic_id", "listening_topics"),
    ("crossword_sample_plays", "sample_id", "crossword_samples"),
]


def _attach_sources(
    conn: sqlite3.Connection, content: Path, core: Path, logs: Path,
) -> None:
    conn.execute(f"ATTACH DATABASE 'file:{content}?mode=ro' AS content", ())
    conn.execute(f"ATTACH DATABASE 'file:{core}?mode=ro' AS core", ())
    conn.execute(f"ATTACH DATABASE 'file:{logs}?mode=ro' AS logs", ())


def _unexpected_source_objects(conn: sqlite3.Connection) -> list[str]:
    """3ソースに、静的スキーマ(=出力先)が知らないテーブルが無いか確認
    (Fable指摘M-3: 未知のテーブルを黙って落とすと、ロールバック後の
    データから静かに何かが消える)。"""
    known = set(SOURCE_SCHEMA.keys())
    problems = []
    for schema in ("content", "core", "logs"):
        rows = conn.execute(
            f"SELECT name FROM {schema}.sqlite_master "
            "WHERE type = 'table' AND name != 'sqlite_sequence'"
        ).fetchall()
        for (name,) in rows:
            if name not in known:
                problems.append(f"{schema}.{name}")
    return problems


def _copy_all_tables(conn: sqlite3.Connection) -> dict[str, tuple[int, int]]:
    """各ソースから出力ファイルへコピーする。FOREIGN KEYは分割時に外した
    9列を含めて全て復元されるため、コピー中は一時的にOFFにする(親→子の
    順序に依存せず一括コピーするため)。列は完全一致を要求する(Fable指摘
    M-3: 移行スクリプトと違い、逆マージ側は「出力(復元後の完全なスキーマ)
    に無い列がソースにある」状況が起きるはずが無い=起きたら移行後に
    加えられた想定外の変更なので、警告で済ませず失敗させる)。"""
    conn.execute("PRAGMA foreign_keys = OFF")
    counts: dict[str, tuple[int, int]] = {}
    for table, schema in SOURCE_SCHEMA.items():
        src_cols = [
            r[1] for r in conn.execute(f"PRAGMA {schema}.table_info({table})")
        ]
        if not src_cols:
            counts[table] = (0, 0)
            continue
        dst_cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]
        unexpected = [c for c in src_cols if c not in dst_cols]
        if unexpected:
            raise RuntimeError(
                f"{table}: 出力スキーマに無い列があります({unexpected})。"
                "分割後にスキーマが変更された可能性があります。"
                f"{SCHEMA_FILE.name}の更新が必要かもしれません。"
            )
        col_list = ", ".join(src_cols)
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


def _prune_orphans(conn: sqlite3.Connection) -> dict[tuple[str, str], int]:
    """--prune-orphans指定時、親が存在しない子行を削除する(Fable指摘M-1)。
    分割前のON DELETE CASCADEが本来やっていたはずの掃除を、統合時に
    肩代わりする形。削除件数を返す(0件のキーは表示しない想定)。"""
    removed: dict[tuple[str, str], int] = {}
    for child, col, parent in DEREFERENCED_COLUMNS:
        cur = conn.execute(
            f"DELETE FROM {child} WHERE {col} NOT IN "
            f"(SELECT id FROM {parent})"
        )
        if cur.rowcount:
            removed[(child, parent)] = cur.rowcount
    return removed


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--content", default=str(paths.content_db_file))
    ap.add_argument("--core", default=str(paths.db_file))
    ap.add_argument("--logs", default=str(paths.logs_db_file))
    ap.add_argument(
        "--output", default=None,
        help="既定: data/vocabulary.merged-<timestamp>.db"
             "(vocabulary.dbへの配置は運用者が確認後に手動で行うこと)")
    ap.add_argument(
        "--prune-orphans", action="store_true",
        help="親が存在しない子行(分割後にcontent側を直接操作した場合等に"
             "生じ得る)を削除してから統合する。既定はしない(=検出したら"
             "失敗して知らせる)")
    ap.add_argument(
        "--keep-split-files", action="store_true",
        help="成功後も3入力ファイルをそのまま残す(既定はsuperseded-<ts>へ"
             "リネームし、後から誤って『現在の分割状態』と混同されるのを"
             "防ぐ)")
    args = ap.parse_args()

    content, core, logs = Path(args.content), Path(args.core), Path(args.logs)
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    output = (
        Path(args.output) if args.output
        else paths.data_dir / f"vocabulary.merged-{stamp}.db"
    )

    for p in (content, core, logs):
        if not p.exists():
            print(f"入力ファイルが見つかりません: {p}")
            return 1
    if not SCHEMA_FILE.exists():
        print(f"スキーマ定義ファイルが見つかりません: {SCHEMA_FILE}")
        return 1

    # ガード(Fable指摘HIGH-3): 出力が入力ファイル自身を指していないか。
    input_paths = {content.resolve(), core.resolve(), logs.resolve()}
    if output.resolve() in input_paths:
        print(f"エラー: --output ({output}) が入力ファイル自身を指してい"
              "ます。別名を指定してください。")
        return 1

    if output.exists():
        print(f"エラー: 出力ファイルが既に存在します: {output}")
        print("別名を指定するか、不要であれば手動で削除してから"
              "再実行してください(このスクリプトは既存ファイルを"
              "自動削除しません)。")
        return 1

    # ガード(Fable指摘HIGH-2): 検証成功を確認するまで、出力の本当の
    # 置き場所には一切触れない。一時ファイルに書き、成功時のみ
    # os.replace()で原子的に配置する。
    tmp_output = output.with_name(output.name + f".tmp-{os.getpid()}")
    for stale in (tmp_output, Path(str(tmp_output) + "-wal"),
                  Path(str(tmp_output) + "-shm")):
        stale.unlink(missing_ok=True)

    # 統合前の金額基準値(3分割ファイル側から)を、出力ファイル作成前に
    # 別接続で取っておく(比較のため)。
    pre_conn = sqlite3.connect(":memory:")
    _attach_sources(pre_conn, content, core, logs)
    unexpected = _unexpected_source_objects(pre_conn)
    pre_money = _money_sums(pre_conn, from_sources=True)
    pre_conn.close()
    if unexpected:
        print(f"エラー: 静的スキーマに無いテーブルがあります: {unexpected}")
        print(f"{SCHEMA_FILE.name}の更新が必要な可能性があります。")
        return 1

    t0 = time.time()
    conn = sqlite3.connect(str(tmp_output), uri=True)
    conn.row_factory = sqlite3.Row
    pruned: dict[tuple[str, str], int] = {}
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
        if fk_issues and args.prune_orphans:
            pruned = _prune_orphans(conn)
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
            # 2026-09-14 3回目レビュー指摘HIGH-1/M-2対応: 移行済みマーカーを
            # 引き継がず、代わりに逆マージ済みマーカーを書く。これにより
            # 移行スクリプトの_is_already_migrated()がこの単一ファイルを
            # 誤って「まだ分割前」と誤認することはあっても「既に分割済み」
            # と誤認してブロックすることは無くなる(前者は安全側の誤り、
            # 後者は危険側の誤りだったため)。
            conn.execute(
                "DELETE FROM app_state WHERE key = ?", (FORWARD_MARKER_KEY,)
            )
            conn.execute(
                "INSERT INTO app_state (key, value) "
                "VALUES (?, datetime('now'))",
                (REVERSE_MARKER_KEY,),
            )
            conn.commit()
        else:
            conn.rollback()
    except Exception as exc:
        conn.rollback()
        conn.close()
        print(f"--- 例外発生、ロールバックしました: {exc} ---")
        tmp_output.unlink(missing_ok=True)
        return 1
    conn.close()

    if not ok:
        print("--- 検証失敗 ---")
        if mismatches:
            print(f"件数不一致: {mismatches}")
        if fk_issues:
            print(f"FK不整合: {[dict(r) for r in fk_issues]}")
            if not args.prune_orphans:
                print("--prune-orphansを付けると、親が存在しない子行を"
                      "削除してから再試行できます(内容を確認の上で"
                      "判断してください)。")
        if money_diff:
            print(f"金額合計の不一致(統合前,統合後): {money_diff}")
        print(f"一時ファイル({tmp_output})を削除します。"
              "入力ファイル・既存の出力候補は一切変更していません。")
        tmp_output.unlink(missing_ok=True)
        return 1

    if pruned:
        print(f"--prune-orphansにより削除した孤児行: {pruned}")

    # ここまで来て初めて、検証済みの一時ファイルを本来の場所へ原子的に
    # 配置する(Fable指摘HIGH-2)。
    os.replace(tmp_output, output)
    if Path(str(tmp_output) + "-wal").exists():
        os.replace(str(tmp_output) + "-wal", str(output) + "-wal")
    if Path(str(tmp_output) + "-shm").exists():
        os.replace(str(tmp_output) + "-shm", str(output) + "-shm")

    print("--- 検証OK ---")
    print(f"統合ファイル: {output}")
    print("このファイルを確認の上、必要であれば data/vocabulary.db へ"
          "手動でリネームしてください(自動では行いません)。")

    if not args.keep_split_files:
        # Fable指摘HIGH-1: 3分割ファイルを残したままだと、後で分割対応
        # コードへ再デプロイした際に「もう古くなった分割ファイル」の上で
        # 黙って正常起動してしまう(=切替直後のC3ガードと同種の危険)。
        # 既定でsuperseded-<ts>にリネームし、二度と「現在の分割状態」と
        # 混同されないようにする。
        for p in (content, core, logs):
            superseded = p.with_name(p.name + f".superseded-{stamp}")
            p.rename(superseded)
            print(f"リネーム: {p.name} -> {superseded.name}")
    else:
        print("--keep-split-files指定のため、3分割ファイルはそのまま"
              "残しています(取り扱い注意: 古い状態のまま今後誤って"
              "使われないようにしてください)。")

    return 0


if __name__ == "__main__":
    sys.exit(main())
