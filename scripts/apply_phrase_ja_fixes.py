# ruff: noqa: E501
"""点検で作り直したフレーズの日本語訳(`phrases.japanese`)を反映する
（DBのみ変更・再起動不要）。

背景: 2026-08-22、単語(words)側の点検完了を受けてフレーズ(phrases)側も
全件点検した。phrasesは`english`/`japanese`が直接ペアで、wordsのような
別カラムのexample/example_jaは無いため、`words`用の
`apply_example_ja_fixes.py`とは別スクリプトにした。

入力JSON（配列。ファイルでもディレクトリでも可）:
    [{"id": 786, "japanese": "敵を知り、己を知れ。"}, ...]

使い方（VPSのコンテナ内）:
    docker cp fixes eigo-app:/data/phrase_fixes
    docker exec -i eigo-app python scripts/apply_phrase_ja_fixes.py /data/phrase_fixes
    docker exec -i eigo-app python scripts/apply_phrase_ja_fixes.py /data/phrase_fixes --apply
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
    ap.add_argument("path", help="訳JSON（ファイル or ディレクトリ）")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    items = load_items(Path(args.path))
    updated = same = missing = bad = 0
    with db() as conn:
        for it in items:
            pid = it.get("id")
            ja = (it.get("japanese") or "").strip()
            if not isinstance(pid, int) or not ja:
                bad += 1
                continue
            row = conn.execute(
                "SELECT id, english, japanese FROM phrases WHERE id = ?",
                (pid,),
            ).fetchone()
            if not row:
                print(f"  [なし] id={pid}")
                missing += 1
                continue
            if row["japanese"] == ja:
                same += 1
                continue
            if args.apply:
                conn.execute(
                    "UPDATE phrases SET japanese = ? WHERE id = ?",
                    (ja, pid),
                )
            updated += 1
        if args.apply:
            conn.commit()

    print(f"{'実行' if args.apply else 'ドライラン'}: 更新 {updated} / "
          f"変更なし {same} / 該当なし {missing} / 不正 {bad}")
    if not args.apply:
        print("※ 実際に更新するには --apply を付けてください。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
