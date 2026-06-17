"""Claude（本チャット）が生成した単語詳細(JSON)を words.detail に投入する。

事前DB作成は「本チャットの Claude が直接生成を優先（API原価¥0）」の方針
（[[project-english-learning-app]] / docs/COST_ESTIMATE.md）。私が作った詳細を
JSON ファイルにまとめ、このスクリプトで一括投入する。英語見出し（小文字一致）で
該当語を引き、`detail` が空のものだけ更新する（既存は保持、--force で上書き）。

JSON 形式: オブジェクトの配列。各要素は
  {"english": "...", "detail": {pos, meanings, examples[{en,ja}],
    derivatives[{word,pos,ja}], synonyms[{word,note}], antonyms[{word,note}],
    origin, trivia, explanation}}
（detail のキーは vocabulary.py の word_detail と同じ＝app側の表示と互換）

使い方:
  python scripts/import_details.py path/to/details_batch.json
  python scripts/import_details.py batch.json --force   # 既存も上書き
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

_DETAIL_KEYS = {
    "pronunciation", "pos", "meanings", "examples", "example_ja",
    "derivatives", "synonyms", "antonyms", "origin", "trivia",
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
            # 想定外キーが無いか軽くチェック（厳密検証はしない）。
            if not (_DETAIL_KEYS & set(detail.keys())):
                bad += 1
                continue
            row = conn.execute(
                "SELECT id, detail FROM words WHERE LOWER(english) = ?",
                (eng.lower(),),
            ).fetchone()
            if not row:
                missing += 1
                continue
            if (row["detail"] or "").strip() and not args.force:
                skipped += 1
                continue
            conn.execute(
                "UPDATE words SET detail = ? WHERE id = ?",
                (json.dumps(detail, ensure_ascii=False), row["id"]),
            )
            updated += 1
        conn.commit()

    print(f"投入: 更新 {updated} / 既存スキップ {skipped} / "
          f"DB未登録 {missing} / 不正 {bad}")
    with db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM words").fetchone()[0]
        has = conn.execute(
            "SELECT COUNT(*) FROM words WHERE TRIM(COALESCE(detail,'')) <> ''"
        ).fetchone()[0]
    print(f"現在の詳細カバレッジ: {has} / {total} 語")
    return 0


if __name__ == "__main__":
    sys.exit(main())
