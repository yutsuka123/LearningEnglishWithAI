# ruff: noqa: E501
"""Claudeが生成した訳を、id指定で安全にdetail.example_jaへ書き込む。

`scripts/backfill_example_ja.py` の `run_merge` はenglish名でマッチするため
同綴りが複数あると誤爆しうる。本スクリプトは **id直指定** + **書き込み直前に
現在のexample文と入力側のexample文が一致するか検証**することで、対象語の
取り違えと「別の文への訳の紐付け」事故(2026-08-22参照)の両方を防ぐ。

入力JSON: [{"id": 2, "example": "The firm acquired a startup.",
            "example_ja": "その会社はスタートアップを買収した。"}, ...]
  ("example"は突き合わせ用。実際の書き込み時はDBから取り直したexampleを
   example_ja_srcとして保存する。)

使い方(コンテナ内):
  docker exec -i eigo-app python scripts/apply_example_ja_by_id.py /data/batch.json           # 確認のみ
  docker exec -i eigo-app python scripts/apply_example_ja_by_id.py /data/batch.json --apply    # 実行
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402


def _norm(s: str) -> str:
    s = (s or "").strip().lower()
    return re.sub(r"[\s　]+", " ", s).rstrip(".!?").strip()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="訳JSON [{id, example, example_ja}, ...]")
    ap.add_argument("--apply", action="store_true", help="実際にDBへ書き込む")
    args = ap.parse_args()

    items = json.loads(Path(args.path).read_text(encoding="utf-8"))
    updated = mismatch = missing_row = bad_detail = no_ja = 0

    with db() as conn:
        for it in items:
            wid = it.get("id")
            expected_ex = (it.get("example") or "").strip()
            ja = (it.get("example_ja") or "").strip()
            if not ja:
                no_ja += 1
                print(f"  [skip] id={wid}: example_ja が空")
                continue
            row = conn.execute(
                "SELECT id, english, example, detail FROM words WHERE id = ?",
                (wid,),
            ).fetchone()
            if not row:
                missing_row += 1
                print(f"  [skip] id={wid}: words に存在しない")
                continue
            cur_ex = (row["example"] or "").strip()
            if _norm(cur_ex) != _norm(expected_ex):
                mismatch += 1
                print(
                    f"  [skip] id={wid} ({row['english']}): example が変化 "
                    f"想定=[{expected_ex}] 現在=[{cur_ex}]"
                )
                continue
            try:
                d = json.loads(row["detail"] or "{}")
            except Exception:
                bad_detail += 1
                print(f"  [skip] id={wid}: detail JSON 不正")
                continue
            if not isinstance(d, dict):
                bad_detail += 1
                continue
            print(f"  id={wid} {row['english']}: [{cur_ex}] -> {ja}")
            if args.apply:
                d["example_ja"] = ja
                d["example_ja_src"] = cur_ex
                conn.execute(
                    "UPDATE words SET detail = ? WHERE id = ?",
                    (json.dumps(d, ensure_ascii=False), wid),
                )
            updated += 1
        if args.apply:
            conn.commit()

    mode = "適用済み" if args.apply else "確認のみ(--applyで実行)"
    print(
        f"\n{mode}: 対象 {updated} / example不一致でskip {mismatch} / "
        f"行なし {missing_row} / detail不正 {bad_detail} / 訳が空 {no_ja}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
