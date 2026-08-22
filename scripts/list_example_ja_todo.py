# ruff: noqa: E501
"""例文訳の「人による点検」が残っている語を一覧に書き出す（読み取り専用）。

背景（2026-08-22）: 詳細画面の例文と訳が別の文になっていた問題
（CHANGELOG ver1.2.10 §1参照）。`detail.examples[]` に同じ英文の訳がある語は
`scripts/fix_example_ja.py` で機械的に直せたが、**照合先が無い語（本番6,666語）**
は人が英文を読んで訳を確認するしかない。

  ・確認して直したものは `scripts/apply_example_ja_fixes.py` が
    `detail.example_ja_checked = true` を付ける
  ・このスクリプトはその印が**無い**ものだけを出す

進捗がDBに入っているので、**作業機を変えても続きから再開できる**
（実測: 誤りはID 9000番台以降に強く偏っている。低いIDのTOEIC由来データは
無作為45件で誤り1件＝約2%、9400番以降は抽出したほぼ全件が別文の訳だった）。

使い方（VPSのコンテナ内）:
    docker cp scripts/list_example_ja_todo.py eigo-app:/app/scripts/
    docker exec -i eigo-app python scripts/list_example_ja_todo.py
    docker cp eigo-app:/data/example_ja_todo.json ./
オプション:
    --min-id 9000     このID以上だけ出す（誤りが集中している帯を先に片づける）
    --max-id 99999
    --limit 400       出力件数の上限
    --tsv             人が読みやすいタブ区切りでも出す（*.tsv）
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import paths  # noqa: E402
from app.database import db  # noqa: E402

OUT = paths.data_dir / "example_ja_todo.json"


def _txt(v) -> str:
    if isinstance(v, list):
        return " ".join(_txt(x) for x in v if x)
    if isinstance(v, dict):
        return _txt(v.get("ja") or v.get("en") or "")
    return str(v or "")


def _norm(s) -> str:
    t = _txt(s).strip().lower()
    return re.sub(r"[\s　]+", " ", t).rstrip(".!?").strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--min-id", type=int, default=0)
    ap.add_argument("--max-id", type=int, default=10 ** 9)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--tsv", action="store_true")
    args = ap.parse_args()

    todo: list[dict] = []
    checked = auto_ok = 0
    with db() as conn:
        rows = conn.execute(
            "SELECT id, english, japanese, domain, example, detail FROM words "
            "ORDER BY id"
        ).fetchall()
        for r in rows:
            ex = (r["example"] or "").strip()
            if not ex:
                continue
            try:
                d = json.loads(r["detail"] or "{}")
            except ValueError:
                continue
            if not isinstance(d, dict):
                continue
            eja = _txt(d.get("example_ja")).strip()
            if not eja:
                continue
            if d.get("example_ja_checked"):
                checked += 1
                continue
            # detail.examples[] に同じ英文があるものは fix_example_ja.py が
            # 面倒を見た（＝訳が英文と対で作られている）ので対象外。
            if any(isinstance(e, dict) and _norm(e.get("en")) == _norm(ex)
                   for e in (d.get("examples") or [])):
                auto_ok += 1
                continue
            if not (args.min_id <= r["id"] <= args.max_id):
                continue
            todo.append({
                "id": r["id"], "english": r["english"],
                "domain": r["domain"] or "", "example": ex, "example_ja": eja,
            })

    if args.limit:
        todo = todo[:args.limit]
    OUT.write_text(json.dumps(todo, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    if args.tsv:
        tsv = OUT.with_suffix(".tsv")
        tsv.write_text("\n".join(
            f'{t["id"]}\t{t["domain"]}\t{t["example"]}\t{t["example_ja"]}'
            for t in todo), encoding="utf-8")
        print(f"→ {tsv}")
    print(f"人が確認済み {checked} / 自動照合できた {auto_ok} / "
          f"残り(この条件) {len(todo)}")
    print(f"→ {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
