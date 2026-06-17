# ruff: noqa: E501
"""読み上げ例文(words.example)の日本語訳を detail.example_ja に埋める。

詳細ポップアップ先頭の「読み上げ可能な例文」に和訳を表示するための事前データ。
発声は不要(訳テキストのみ)。2モード:

  --auto : detail.examples の中に words.example と一致する英文があれば、その ja を
           detail.example_ja に流用(DB更新)。一致しない語は翻訳が必要なので
           data/example_ja_missing.json に [{english, example}] で書き出す。
  <file|dir> : Claude が生成した訳 [{english, example_ja}] を detail.example_ja に
           マージ(--force で既存も上書き)。english 小文字一致・他キー不変。

使い方:
  python scripts/backfill_example_ja.py --auto
  python scripts/backfill_example_ja.py data/example_ja_batches/
  python scripts/backfill_example_ja.py data/example_ja_batches/ --force
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

MISS = Path(__file__).resolve().parent.parent / "data" / "example_ja_missing.json"


def _norm(s: str) -> str:
    return (s or "").strip().lower().rstrip(".").strip()


def run_auto() -> int:
    filled = exported = skipped_have = noexample = 0
    remaining: list[dict] = []
    with db() as conn:
        rows = conn.execute(
            "SELECT id, english, example, detail FROM words "
            "WHERE TRIM(COALESCE(detail,'')) <> ''"
        ).fetchall()
        for r in rows:
            ex = (r["example"] or "").strip()
            try:
                d = json.loads(r["detail"])
            except Exception:
                continue
            if not ex:
                noexample += 1
                continue
            if (d.get("example_ja") or "").strip():
                skipped_have += 1
                continue
            ja = ""
            for e in (d.get("examples") or []):
                if _norm(e.get("en")) == _norm(ex):
                    ja = (e.get("ja") or "").strip()
                    break
            if ja:
                d["example_ja"] = ja
                conn.execute(
                    "UPDATE words SET detail = ? WHERE id = ?",
                    (json.dumps(d, ensure_ascii=False), r["id"]),
                )
                filled += 1
            else:
                remaining.append({"english": r["english"], "example": ex})
                exported += 1
        conn.commit()
    MISS.write_text(
        json.dumps(remaining, ensure_ascii=False, indent=0), encoding="utf-8")
    print(f"自動充填(流用) {filled} / 既にあり {skipped_have} / "
          f"例文なし {noexample}")
    print(f"翻訳が必要 {exported} 語 → {MISS}")
    return 0


def run_merge(path: Path, force: bool) -> int:
    paths = sorted(path.glob("*.json")) if path.is_dir() else [path]
    items: list[dict] = []
    for p in paths:
        data = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(data, list):
            items.extend(data)
    updated = skipped = missing = bad = 0
    with db() as conn:
        for it in items:
            eng = (it.get("english") or "").strip()
            ja = (it.get("example_ja") or it.get("ja") or "").strip()
            if not eng or not ja:
                bad += 1
                continue
            row = conn.execute(
                "SELECT id, detail FROM words WHERE LOWER(english) = ?",
                (eng.lower(),),
            ).fetchone()
            if not row or not (row["detail"] or "").strip():
                missing += 1
                continue
            try:
                d = json.loads(row["detail"])
            except Exception:
                bad += 1
                continue
            if (d.get("example_ja") or "").strip() and not force:
                skipped += 1
                continue
            d["example_ja"] = ja
            conn.execute(
                "UPDATE words SET detail = ? WHERE id = ?",
                (json.dumps(d, ensure_ascii=False), row["id"]),
            )
            updated += 1
        conn.commit()
    print(f"訳マージ: 更新 {updated} / 既存スキップ {skipped} / "
          f"未登録/detailなし {missing} / 不正 {bad}")
    return 0


def _coverage() -> None:
    with db() as conn:
        rows = conn.execute(
            "SELECT example, detail FROM words "
            "WHERE TRIM(COALESCE(detail,'')) <> ''"
        ).fetchall()
    have = need = 0
    for r in rows:
        if not (r["example"] or "").strip():
            continue
        try:
            d = json.loads(r["detail"])
        except Exception:
            continue
        if (d.get("example_ja") or "").strip():
            have += 1
        else:
            need += 1
    print(f"example_ja カバレッジ: {have} / {have + need} (例文ありのうち)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?", help="訳JSON(ファイル/ディレクトリ)")
    ap.add_argument("--auto", action="store_true",
                    help="detail.examples の一致から流用＋未訳を書き出し")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    if args.auto:
        run_auto()
    elif args.path:
        run_merge(Path(args.path), args.force)
    else:
        ap.error("--auto か 訳JSON のどちらかを指定してください。")
    _coverage()
    return 0


if __name__ == "__main__":
    sys.exit(main())
