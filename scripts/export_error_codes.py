"""app/services/errors.py のエラーコード registry から
docs/ERROR_CODES.md と docs/ERROR_CODES.csv を生成する（2026-08-20〜）。

このスクリプトが唯一の生成元。docs側のファイルは直接手で編集しない
（errors.py を更新したら、このスクリプトを再実行するだけで両方が揃う）。

実行: .venv/bin/python scripts/export_error_codes.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from app.services.errors import CATEGORIES, ERROR_CODES, category_of  # noqa: E402

OUT_MD = ROOT_DIR / "docs" / "ERROR_CODES.md"
OUT_CSV = ROOT_DIR / "docs" / "ERROR_CODES.csv"


def main() -> None:
    rows = sorted(ERROR_CODES.items(), key=lambda kv: int(kv[0]))

    OUT_MD.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# エラーコード一覧（自動生成・手で編集しない）",
        "",
        "`scripts/export_error_codes.py` が `app/services/errors.py` から",
        "生成する。追加/変更は必ず `errors.py` 側で行い、このスクリプトを",
        "再実行すること。",
        "",
    ]
    for base, category in CATEGORIES.items():
        cat_rows = [
            (code, msg, status) for code, (msg, status) in rows
            if category_of(code) == category
        ]
        if not cat_rows:
            continue
        lines.append(f"## {base} {category}")
        lines.append("")
        lines.append("| コード | 既定メッセージ | HTTPステータス |")
        lines.append("| --- | --- | --- |")
        for code, msg, status in cat_rows:
            status_s = str(status) if status else "(フロント側で使用)"
            lines.append(f"| {code} | {msg} | {status_s} |")
        lines.append("")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")

    with OUT_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["code", "category", "message", "http_status"])
        for code, (msg, status) in rows:
            w.writerow([code, category_of(code), msg, status])

    print(f"wrote {OUT_MD} ({len(rows)} codes)")
    print(f"wrote {OUT_CSV} ({len(rows)} codes)")


if __name__ == "__main__":
    main()
