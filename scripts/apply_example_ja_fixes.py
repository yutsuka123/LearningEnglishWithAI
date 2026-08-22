# ruff: noqa: E501
"""人が確認して作り直した例文訳をDBに反映する（DBのみ変更・再起動不要）。

`scripts/fix_example_ja.py` は「detail.examples[] に同じ英文の訳がある」語だけを
自動で直せる。それが無い語（本番で6,666語）は照合先が無いため、人が英文を読んで
訳を作り直すしかない。このスクリプトはその訳をまとめて反映する。

入力JSON（配列。ファイルでもディレクトリでも可）:
    [{"id": 9068, "example_ja": "その2つのライバル企業は…"}, ...]

反映時に必ず次の2つを記録する:
  * `detail.example_ja_src`      … その訳が対応する英文。あとで例文を差し替えたら
                                    表示側(`_resolve_example_ja`)が不一致を検出して
                                    古い訳を出さなくなる。
  * `detail.example_ja_checked`  … 人が確認済みの印。残作業の一覧
                                    (`scripts/list_example_ja_todo.py`)から外れる。
                                    **進捗をDBに持つので、作業機を変えても続きから
                                    再開できる。**

使い方（VPSのコンテナ内）:
    docker cp fixes eigo-app:/data/fixes
    docker exec -i eigo-app python scripts/apply_example_ja_fixes.py /data/fixes
    docker exec -i eigo-app python scripts/apply_example_ja_fixes.py /data/fixes --apply
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
            wid = it.get("id")
            ja = (it.get("example_ja") or "").strip()
            if not isinstance(wid, int) or not ja:
                bad += 1
                continue
            row = conn.execute(
                "SELECT id, english, example, detail FROM words WHERE id = ?",
                (wid,),
            ).fetchone()
            if not row:
                print(f"  [なし] id={wid}")
                missing += 1
                continue
            try:
                d = json.loads(row["detail"] or "{}")
            except ValueError:
                d = {}
            if not isinstance(d, dict):
                d = {}
            ex = (row["example"] or "").strip()
            if (d.get("example_ja") == ja and d.get("example_ja_src") == ex
                    and d.get("example_ja_checked")):
                same += 1
                continue
            d["example_ja"] = ja
            d["example_ja_src"] = ex
            # 「人が英文と突き合わせて確認済み」の印。次の作業機で
            # scripts/list_example_ja_todo.py を流すと、この印が無いものだけが
            # 残作業として出てくる（別マシンでも続きから再開できる）。
            d["example_ja_checked"] = True
            if args.apply:
                conn.execute(
                    "UPDATE words SET detail = ? WHERE id = ?",
                    (json.dumps(d, ensure_ascii=False), wid),
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
