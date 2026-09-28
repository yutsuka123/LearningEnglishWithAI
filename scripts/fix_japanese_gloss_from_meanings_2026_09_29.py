# ruff: noqa: E501
"""`words.japanese`(短い訳語・一覧/クイズ/フラッシュカードで使われる)に、説明文がまるごと入ってしまっている行を修正する
(2026-09-29・管理画面メモ#6「13年ゼミの意味はシンプルにし、詳細情報は別に持ってくる。17年ゼミも同様。他にも同様のものがある」への対応)。

## 見つかった問題
`words.japanese`はクイズ(en→ja方向の正解)・単語一覧の「意味」列・フラッシュカード・crosswordのヒント等、
**短い訳語であることが前提の全箇所**で使われている。一部の語(主にID 13475以降のニッチ語彙拡張バッチ)で、
本来ここに入るべき短い訳語の代わりに、詳しい説明文がまるごと入っている(`detail.meanings[0]`には正しい
短い訳語が別途入っている=生成時にどちらの値を`japanese`列へ書くか取り違えたバグと推定)。
全16,510語を走査した結果、この対象は2,413語(生物学/天文/物理/金融/数学/化学/地学/五輪/陶芸/知財/軍事/経営学/法律等
広い範囲のドメインに分布)。

## 修正内容(対象語のみ・他は一切変更しない)
- `words.japanese` ← `detail.meanings[0]`(短い訳語に差し替え)
- 元の`japanese`の説明文は、情報を失わないよう`detail.trivia`の先頭に追記(既存trivia本文は保持)

## 対象の判定条件(このスクリプトが自動抽出)
`detail.meanings[0]`が存在し、`japanese != meanings[0]`、`japanese`に「。」を含み(=説明文の体裁)、
かつ`len(japanese) > len(meanings[0])*2`かつ`len(japanese) > 25`。多数のドメインでサンプル確認済み
(meanings[0]側が常に適切な短い訳語であること)。

使い方(dry-run既定・バックアップ(既定DATA_DIR/script_backups)+ロールバック・ID一致のみ・冪等・前後で件数確認):
  python scripts/fix_japanese_gloss_from_meanings_2026_09_29.py [--apply | --rollback <バックアップJSON>] [--limit N] [--ids 14892,14893,...]
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _db_safety import default_backup_dir, key_counts, print_counts, same_counts  # noqa: E402
from app.database import db  # noqa: E402


def is_affected(japanese: str, m0: str) -> bool:
    return bool(m0) and japanese != m0 and "。" in japanese and len(japanese) > len(m0) * 2 and len(japanese) > 25


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="実際に書き込む(既定はdry-run)")
    ap.add_argument("--rollback", metavar="BACKUP_JSON")
    ap.add_argument("--backup-dir", default=None, help="既定 DATA_DIR/script_backups")
    ap.add_argument("--limit", type=int, default=None, help="対象を先頭N件に絞る(動作確認用)")
    ap.add_argument("--ids", default=None, help="対象語IDをカンマ区切りで指定(未指定なら自動抽出した全件)")
    args = ap.parse_args()

    if args.rollback:
        rows = json.loads(Path(args.rollback).read_text(encoding="utf-8"))
        with db() as conn:
            n0 = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
            for r in rows:
                conn.execute("UPDATE words SET japanese = ?, detail = ? WHERE id = ? AND english = ?",
                             (r["japanese"], r["detail"], r["id"], r["english"]))
            conn.commit()
            n1 = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        print(f"ロールバック: {len(rows)}語(words件数 {n0}→{n1})")
        return 0

    want_ids = set(int(x) for x in args.ids.split(",")) if args.ids else None

    plan, backup, skipped = [], [], 0
    with db() as conn:
        before = key_counts(conn)
        rows = conn.execute("SELECT id, english, japanese, detail FROM words ORDER BY id").fetchall()
        for row in rows:
            if want_ids is not None and row["id"] not in want_ids:
                continue
            try:
                detail = json.loads(row["detail"]) if row["detail"] else {}
            except Exception:
                skipped += 1
                continue
            meanings = detail.get("meanings") or []
            m0 = meanings[0] if meanings else None
            jp = row["japanese"] or ""
            if not is_affected(jp, m0):
                continue
            new_detail = dict(detail)
            old_trivia = (new_detail.get("trivia") or "").strip()
            new_detail["trivia"] = (jp.strip() + ("　" + old_trivia if old_trivia else "")).strip()
            plan.append({
                "id": row["id"], "english": row["english"],
                "old_japanese": jp, "new_japanese": m0,
                "new_detail": json.dumps(new_detail, ensure_ascii=False),
            })
            backup.append({"id": row["id"], "english": row["english"], "japanese": jp, "detail": row["detail"]})
            if args.limit and len(plan) >= args.limit:
                break

    print(f"対象: {len(plan)}語(detailのJSON解析に失敗してスキップ: {skipped}件)")
    for p in plan[:10]:
        print(f"  id={p['id']:6d} {p['english']!r}")
        print(f"    旧japanese= {p['old_japanese']!r}")
        print(f"    新japanese= {p['new_japanese']!r}")
    if len(plan) > 10:
        print(f"  ...他 {len(plan) - 10}件")

    if not args.apply:
        print("\n(dry-run。実際に書き込むには --apply を付けて再実行)")
        return 0

    if not plan:
        print("対象0件のため何もしません。")
        return 0

    bdir = Path(args.backup_dir) if args.backup_dir else default_backup_dir()
    bdir.mkdir(parents=True, exist_ok=True)
    bpath = bdir / f"backup_fix_japanese_gloss_{time.strftime('%Y%m%d_%H%M%S')}.json"
    bpath.write_text(json.dumps(backup, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"バックアップ: {bpath}")

    with db() as conn:
        for p in plan:
            conn.execute("UPDATE words SET japanese = ?, detail = ? WHERE id = ? AND english = ?",
                         (p["new_japanese"], p["new_detail"], p["id"], p["english"]))
        conn.commit()
        after = key_counts(conn)

    print_counts("前", before)
    print_counts("後", after)
    if not same_counts(before, after):
        print("⚠️ 主要テーブルの件数が変わっています(想定外・rollbackを検討)", file=sys.stderr)
        return 1
    print(f"適用完了: {len(plan)}語(ロールバック: --rollback {bpath})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
