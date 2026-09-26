# ruff: noqa: E501
"""日本語由来と判定した293語に、語源の言語(origin_lang)と原語表記(native.text)を付与する(2026-09-26・設計§9.8 段階(b-2))。

判定=originに日本語/ローマ字/和製/Japaneseを含む443語をAI(gpt-4.1)で一次分類し、「語そのものが日本語由来」
(ja_loan/ja_romanized)かつ信頼度0.9以上の語だけ(scripts/data/origin_lang_ja_2026_09_26.json)。和製英語(wasei)や
「日本での使われ方」だけの語は含めない。オーナーの抜取り確認(docs/ORIGIN_LANG_PROPOSAL_2026-09-26.md)後に反映すること。

書き換える内容(words.detail のJSONに、無いキーだけを足す・既存の値は上書きしない):
  origin_lang="ja" / origin_lang_name="日本語" / native={"text":原語表記,"romaji":綴り}(原語表記が確かな語のみtext)。別の言語のorigin_langが既にある語は触らない。
  ※先に apply_ja_origin_pronunciation_2026_09_26.py を適用した33語は、native.ipa等を保持したままtext等の不足分だけ補う。

使い方(wordsテーブルのみ・dry-run既定・バックアップ(既定DATA_DIR/script_backups・コンテナが消えても残る)+ロールバック
(detail全体をバックアップ時点に戻す)・ID+綴りが一致した行だけ・冪等・前後で主要テーブルの件数を確認):
  python scripts/apply_origin_lang_2026_09_26.py [--apply | --rollback <バックアップJSON>] [--backup-dir data]
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

DATA = Path(__file__).resolve().parent / "data" / "origin_lang_ja_2026_09_26.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="実際に書き込む(既定はdry-run)")
    ap.add_argument("--rollback", metavar="BACKUP_JSON")
    ap.add_argument("--backup-dir", default=None, help="既定 DATA_DIR/script_backups")
    args = ap.parse_args()

    if args.rollback:
        rows = json.loads(Path(args.rollback).read_text(encoding="utf-8"))
        with db() as conn:
            n0 = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
            for r in rows:
                conn.execute("UPDATE words SET detail = ? WHERE id = ? AND english = ?",
                             (r["detail"], r["id"], r["english"]))
            conn.commit()
            n1 = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        print(f"ロールバック: {len(rows)}語(words件数 {n0}→{n1})")
        return 0

    items = json.loads(DATA.read_text(encoding="utf-8"))
    plan, backup, skipped = [], [], {}
    with db() as conn:
        n_words = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        before = key_counts(conn)
        for it in items:
            row = conn.execute("SELECT id, english, detail FROM words WHERE id = ?", (it["id"],)).fetchone()
            if not row or row["english"] != it["english"]:
                skipped.setdefault("IDまたは綴りが一致しない", []).append(it["english"])
                continue
            try:
                d = json.loads(row["detail"] or "")
            except Exception:
                skipped.setdefault("detailが無い/不正", []).append(it["english"])
                continue
            if d.get("origin_lang") not in (None, "", "ja"):
                skipped.setdefault("別の言語のorigin_langが既にある", []).append(it["english"])
                continue
            nd = dict(d)
            nd.setdefault("origin_lang", "ja")
            nd.setdefault("origin_lang_name", "日本語")
            native = dict(nd.get("native") or {})
            if it.get("native_text"):
                native.setdefault("text", it["native_text"])
            native.setdefault("romaji", it["english"])
            nd["native"] = native
            if nd == d:
                skipped.setdefault("反映済み", []).append(it["english"])
                continue
            plan.append((it["id"], it["english"], nd))
            backup.append({"id": it["id"], "english": it["english"], "detail": row["detail"]})
        for why, names in skipped.items():
            print(f"  スキップ({why}): {len(names)}語 {names[:6]}{'…' if len(names) > 6 else ''}")
        print(f"更新対象 {len(plan)}語 / 入力 {len(items)}語 / words件数 {n_words}")
        if not args.apply:
            print("dry-runです(何も書いていません)。反映するには --apply を付けてください。")
            return 0
        if not plan:
            return 0
        print_counts("更新前", before)
        bdir = Path(args.backup_dir) if args.backup_dir else default_backup_dir()
        bdir.mkdir(parents=True, exist_ok=True)
        bpath = bdir / f"backup_origin_lang_{time.strftime('%Y%m%d_%H%M%S')}.json"
        bpath.write_text(json.dumps(backup, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"バックアップ: {bpath}")
        for wid, english, nd in plan:
            conn.execute("UPDATE words SET detail = ? WHERE id = ? AND english = ?",
                         (json.dumps(nd, ensure_ascii=False), wid, english))
        conn.commit()
        n_after = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        after = key_counts(conn)
    print_counts("更新後", after)
    print(f"反映しました: {len(plan)}語(words件数 {n_words}→{n_after}・変わっていないこと)。")
    if not same_counts(before, after):
        print("⚠️ 主要テーブルの件数が更新前後で変わっています。直ちに--rollbackを検討してください。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
