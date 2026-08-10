"""Claude（本チャット）が生成したフレーズ詳細(JSON)を phrases.detail に
投入する。単語のimport_details.pyと同じ方針(本チャットのClaudeが直接
生成＝API原価¥0)をフレーズ側にも適用する初回スクリプト。

`app/routers/phrases.py`の`phrase_detail`が生成するJSONと同じキー構成:
{english, detail: {nuance, similar_expressions[{en,ja,diff}], background,
caution, trivia, explanation}}
（similar_expressionsは配列、他は文字列。格言・ことわざ・慣用句は濃く、
普通の日常フレーズは軽くでよい＝空文字を許容）。

英語見出し（小文字一致）で該当フレーズを引き、`detail`が空のものだけ
更新する（既存は保持、--forceで上書き）。

使い方:
  python scripts/import_phrase_details.py path/to/phrase_details_batch.json
  python scripts/import_phrase_details.py batch.json --force
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

_DETAIL_KEYS = {
    "nuance", "similar_expressions", "background", "caution", "trivia",
    "explanation",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("json_file")
    ap.add_argument("--force", action="store_true",
                    help="既に detail がある語も上書きする")
    args = ap.parse_args()

    data = json.loads(Path(args.json_file).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        print("エラー: JSON はオブジェクトの配列にしてください。")
        return 1

    updated = skipped = missing = bad = 0
    with db() as conn:
        for item in data:
            eng = (item.get("english") or "").strip()
            detail = item.get("detail")
            if not eng or not isinstance(detail, dict):
                bad += 1
                continue
            if not (_DETAIL_KEYS & set(detail.keys())):
                bad += 1
                continue
            row = conn.execute(
                "SELECT id, detail FROM phrases WHERE LOWER(english) = ?",
                (eng.lower(),),
            ).fetchone()
            if not row:
                missing += 1
                continue
            if (row["detail"] or "").strip() and not args.force:
                skipped += 1
                continue
            conn.execute(
                "UPDATE phrases SET detail = ? WHERE id = ?",
                (json.dumps(detail, ensure_ascii=False), row["id"]),
            )
            updated += 1
        conn.commit()

    print(f"投入: 更新 {updated} / 既存スキップ {skipped} / "
          f"DB未登録 {missing} / 不正 {bad}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
