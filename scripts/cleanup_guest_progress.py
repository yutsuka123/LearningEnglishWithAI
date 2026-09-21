"""未登録ゲスト用の疑似ユーザー(`__guest__`)に残っている学習記録を掃除する(2026-09-21)。

背景(セキュリティ自己点検・オーナー承認2026-09-21): 未登録ゲストは全員が同じ疑似ユーザー
を共有するため、その学習記録は「全ゲストに他人の進捗として見える」。ver1.4.14からゲストの
学習記録は保存しない(`progress.upsert_progress`等)ので、それまでに溜まった分を消す。
対象=疑似ユーザーの user_word_progress / user_phrase_progress / word_attempts /
phrase_attempts / user_material_progress。**他のユーザーの行・他のテーブルには触れない。**

安全策(CLAUDE.mdの「本番DBに書き込む操作」の規則):
- 既定はdry-run(件数を出すだけ)。`--execute`を付けたときだけ削除する。
- `--execute`では、削除の前に core.db の整合したコピー(sqlite3 backup API)を
  `<DATA_DIR>/core.pre_guest_cleanup_<日時>.db`に作る。
- 主要テーブルの件数(users/balance_ledger/paypay_payments/各progress/attempts)を
  削除の前後で比べ、**減ったのが対象の行数ちょうど**であることを確認して表示する。
  想定外に減っていたらトランザクションをロールバックする。

使い方(VPS上・eigo-appコンテナ内):
  docker exec -i -w /app -e PYTHONPATH=/app eigo-app python3 - < scripts/cleanup_guest_progress.py
  docker exec -i -w /app -e PYTHONPATH=/app eigo-app python3 - --execute < scripts/cleanup_guest_progress.py
  # 進捗テーブルだけ(出題履歴は残す):
  docker exec -i -w /app -e PYTHONPATH=/app eigo-app python3 - --execute --progress-only < scripts/cleanup_guest_progress.py
"""

from __future__ import annotations

import sqlite3
import sys
from datetime import datetime

from app.config import paths
from app.database import db, init_db
from app.services import auth

# 削除対象(疑似ユーザー分だけ)。
TARGETS = ("user_word_progress", "user_phrase_progress", "word_attempts",
           "phrase_attempts", "user_material_progress")
# 前後で件数を比べる主要テーブル(全体の件数・削除対象以外は不変でなければならない)。
WATCH = ("users", "balance_ledger", "paypay_payments", "login_log",
         "conversation_log", "ai_usage")


def _count(conn, table: str, where: str = "", args: tuple = ()) -> int:
    return conn.execute(
        f"SELECT COUNT(*) FROM {table} {where}", args).fetchone()[0]


def main(argv: list[str]) -> int:
    execute = "--execute" in argv
    # --progress-only: 全ゲストに見えていた進捗(user_*_progress)だけを消し、出題履歴
    # (word_attempts等・他のゲストの画面には出ない統計用)は残す。
    targets = TARGETS[:2] if "--progress-only" in argv else TARGETS
    init_db()
    with db() as conn:
        gid = auth.ensure_guest_user_id(conn)
        per_table = {t: _count(conn, t, "WHERE user_id = ?", (gid,))
                     for t in targets}
        total = sum(per_table.values())
        print(f"ゲスト疑似ユーザー(id={gid})の学習記録: {per_table} 合計{total}行")
        if not execute:
            print("dry-run: 何も削除していません(--executeで削除)。")
            return 0
        if total == 0:
            print("対象なし。")
            return 0

    # 1) バックアップ(整合したコピー)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = paths.data_dir / f"core.pre_guest_cleanup_{stamp}.db"
    src = sqlite3.connect(str(paths.db_file))
    bak = sqlite3.connect(str(dest))
    with bak:
        src.backup(bak)
    bak.close()
    src.close()
    print(f"バックアップ: {dest.name}({dest.stat().st_size:,}バイト)")

    # 2) 削除(前後の件数を比べ、想定外ならロールバック)
    with db() as conn:
        # 書き込みロックを先に取り、件数を数えてから削除するまでの間に他の書き込みが
        # 入って件数比較がずれる(=誤ったロールバック)のを防ぐ。
        conn.execute("BEGIN IMMEDIATE")
        before_watch = {t: _count(conn, t) for t in WATCH}
        before_all = {t: _count(conn, t) for t in targets}
        for t in targets:
            conn.execute(f"DELETE FROM {t} WHERE user_id = ?", (gid,))
        after_all = {t: _count(conn, t) for t in targets}
        after_watch = {t: _count(conn, t) for t in WATCH}
        ok = all(before_all[t] - after_all[t] == per_table[t] for t in targets) \
            and before_watch == after_watch \
            and all(_count(conn, t, "WHERE user_id = ?", (gid,)) == 0
                    for t in targets)
        if not ok:
            conn.rollback()
            print("想定外の件数変化のためロールバックしました:",
                  before_all, after_all, before_watch, after_watch,
                  file=sys.stderr)
            return 1
        for t in targets:
            print(f"  {t}: {before_all[t]} -> {after_all[t]} "
                  f"(削除{per_table[t]}行)")
        print("主要テーブルの件数は不変:", after_watch)
    print("完了。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
