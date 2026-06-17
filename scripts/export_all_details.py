# ruff: noqa: E501
"""ローカル DB の全 detail を import_details.py 用 JSON に書き出す(デプロイ同期用)。

本番(study)へ detail 列だけ同期する際に使う。english(見出し)＋detail オブジェクト
の配列を `data/_details_all.json` に出力。本番側で
`import_details.py /data/_details_all.json --force` すると detail だけ上書きされる
(english 小文字一致・進捗テーブルは不変)。新規語の本番反映は別途 add_*.py で。

Run: python scripts/export_all_details.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "data" / "_details_all.json"


def main() -> int:
    out: list[dict] = []
    with db() as conn:
        rows = conn.execute(
            "SELECT english, detail FROM words "
            "WHERE TRIM(COALESCE(detail,'')) <> '' ORDER BY id"
        ).fetchall()
        for r in rows:
            try:
                d = json.loads(r["detail"])
            except Exception:
                continue
            out.append({"english": r["english"], "detail": d})
    OUT.write_text(
        json.dumps(out, ensure_ascii=False), encoding="utf-8")
    print(f"全detail書き出し: {len(out)} 語 → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
