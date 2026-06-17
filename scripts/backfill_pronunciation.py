# ruff: noqa: E501
"""Claude が生成した発音記号(IPA)を既存 detail にマージする(他キーは保持)。

import_details.py は detail 全体を置換するが、これは **pronunciation だけ**を
既存 detail に追記する(meanings/examples 等は壊さない)。english(小文字一致)で
引き、detail.pronunciation が空のものだけ埋める(--force で上書き)。

JSON 形式: [{"english": "...", "pronunciation": "/.../"}, ...]
(または {"english": "...", "ipa": "/.../"} も可)

使い方:
  python scripts/backfill_pronunciation.py data/ipa_batches/ipa_001.json
  python scripts/backfill_pronunciation.py data/ipa_batches/   # ディレクトリ一括
  python scripts/backfill_pronunciation.py ... --force
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402


def _load(paths: list[Path]) -> list[dict]:
    items: list[dict] = []
    for p in paths:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            items.extend(data)
        else:
            print(f"警告: {p} は配列でないのでスキップ")
    return items


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="JSON ファイル または ディレクトリ")
    ap.add_argument("--force", action="store_true",
                    help="既に発音記号がある語も上書きする")
    args = ap.parse_args()

    p = Path(args.path)
    if p.is_dir():
        paths = sorted(p.glob("*.json"))
    else:
        paths = [p]
    items = _load(paths)

    updated = skipped = missing = bad = nodetail = 0
    with db() as conn:
        for item in items:
            eng = (item.get("english") or "").strip()
            ipa = (item.get("pronunciation") or item.get("ipa") or "").strip()
            if not eng or not ipa:
                bad += 1
                continue
            row = conn.execute(
                "SELECT id, detail FROM words WHERE LOWER(english) = ?",
                (eng.lower(),),
            ).fetchone()
            if not row:
                missing += 1
                continue
            raw = (row["detail"] or "").strip()
            if not raw:
                nodetail += 1
                continue
            try:
                d = json.loads(raw)
            except Exception:
                bad += 1
                continue
            if (d.get("pronunciation") or "").strip() and not args.force:
                skipped += 1
                continue
            d["pronunciation"] = ipa
            conn.execute(
                "UPDATE words SET detail = ? WHERE id = ?",
                (json.dumps(d, ensure_ascii=False), row["id"]),
            )
            updated += 1
        conn.commit()

    print(f"発音記号マージ: 更新 {updated} / 既存スキップ {skipped} / "
          f"DB未登録 {missing} / detailなし {nodetail} / 不正 {bad}")
    with db() as conn:
        rows = conn.execute(
            "SELECT detail FROM words WHERE TRIM(COALESCE(detail,'')) <> ''"
        ).fetchall()
    has = 0
    for (det,) in rows:
        try:
            if (json.loads(det).get("pronunciation") or "").strip():
                has += 1
        except Exception:
            pass
    print(f"発音記号カバレッジ: {has} / {len(rows)} (detail有のうち)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
