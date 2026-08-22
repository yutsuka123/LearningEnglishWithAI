# ruff: noqa: E501
"""domain(分野)とexample(英語例文)の内容が食い違っていた語を、
英文・訳の両方まとめて修正する（2026-08-22発見・domainタグ自体は変更しない）。

背景: 例文訳の食い違い点検の副産物として、`words.domain`は正しい分類
（例: bechamelはフランス料理）なのに、`words.example`（英文そのもの）が
別の国・分野の内容になっている語が見つかった（`scripts/list_words_by_
domains.py`で発見、詳細はprivateリポジトリ`business_plan`の
`products/study_nyangailab/訳文点検_引き継ぎ.md`参照）。

`apply_example_ja_fixes.py`は「英文はそのまま・訳だけ直す」設計のため、
英文自体を差し替える今回は別スクリプトにした。音声はテキスト内容の
ハッシュでキャッシュされる(`audio_store.py`)ため、英文を変えても旧音声と
衝突する心配はない（新しい英文の音声は次回再生時にオンデマンド生成）。

入力JSON（配列。ファイルでもディレクトリでも可）:
    [{"id": 5020, "example": "The French chef used...",
      "example_ja": "フランス人シェフは..."}, ...]

使い方（VPSのコンテナ内）:
    docker cp fixes eigo-app:/data/domain_fixes
    docker exec -i eigo-app python scripts/fix_domain_mismatch_examples.py /data/domain_fixes
    docker exec -i eigo-app python scripts/fix_domain_mismatch_examples.py /data/domain_fixes --apply
既定はドライラン。--apply を付けたときだけ書き込む。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402


def load_items(path: Path) -> list[dict]:
    files = sorted(path.glob("*.json")) if path.is_dir() else [path]
    items: list[dict] = []
    for f in files:
        data = json.loads(f.read_text(encoding="utf-8"))
        if isinstance(data, list):
            items.extend(data)
    return items


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="修正JSON（ファイル or ディレクトリ）")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    items = load_items(Path(args.path))
    updated = missing = bad = 0
    with db() as conn:
        for it in items:
            wid = it.get("id")
            new_example = (it.get("example") or "").strip()
            new_ja = (it.get("example_ja") or "").strip()
            if not isinstance(wid, int) or not new_example or not new_ja:
                bad += 1
                continue
            row = conn.execute(
                "SELECT id, english, domain, example, detail FROM words "
                "WHERE id = ?", (wid,),
            ).fetchone()
            if not row:
                print(f"  [なし] id={wid}")
                missing += 1
                continue
            print(f"id={wid} ({row['english']} / {row['domain']})")
            print(f"  旧example: {row['example']}")
            print(f"  新example: {new_example}")
            try:
                d = json.loads(row["detail"] or "{}")
            except ValueError:
                d = {}
            if not isinstance(d, dict):
                d = {}
            d["example_ja"] = new_ja
            d["example_ja_src"] = new_example
            d["example_ja_checked"] = True
            if args.apply:
                conn.execute(
                    "UPDATE words SET example = ?, detail = ? WHERE id = ?",
                    (new_example, json.dumps(d, ensure_ascii=False), wid),
                )
            updated += 1
        if args.apply:
            conn.commit()

    print(f"\n{'実行' if args.apply else 'ドライラン'}: 更新 {updated} / "
          f"該当なし {missing} / 不正 {bad}")
    if not args.apply:
        print("※ 実際に更新するには --apply を付けてください。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
