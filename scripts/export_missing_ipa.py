# ruff: noqa: E501
"""detail はあるが発音記号(pronunciation/IPA)が空の語を一覧出力する。

バックフィル用。Claude が IPA を生成しやすいよう、english/level/domain を
JSON 配列で `data/ipa_missing.json` に書き出す(level,id 昇順)。

Run: python scripts/export_missing_ipa.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "data" / "ipa_missing.json"


def main() -> int:
    rows_out: list[dict] = []
    with db() as conn:
        rows = conn.execute(
            "SELECT id, english, level, domain, detail FROM words "
            "WHERE TRIM(COALESCE(detail,'')) <> '' "
            "ORDER BY CAST(level AS INTEGER), id"
        ).fetchall()
        for r in rows:
            try:
                d = json.loads(r["detail"])
            except Exception:
                continue
            if (d.get("pronunciation") or "").strip():
                continue
            rows_out.append({
                "english": r["english"],
                "level": r["level"],
                "domain": r["domain"] or "",
            })
    OUT.write_text(
        json.dumps(rows_out, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"発音記号なし: {len(rows_out)} 語 → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
