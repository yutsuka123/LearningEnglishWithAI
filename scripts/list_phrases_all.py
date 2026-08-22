# ruff: noqa: E501
"""フレーズ全件をenglish/japanese/sceneつきで書き出す（読み取り専用）。

背景（2026-08-22）: 単語(words)側の例文訳の食い違い・domain不一致の
点検が完了したのを受けて、フレーズ(phrases)側でも同種の点検を行う。
phrasesにはwordsのような別カラムのexample/example_jaは無く、
english/japanese自体が本体+訳のペアなので、点検対象はこの2列と
sceneの整合性になる。

使い方（VPSのコンテナ内）:
    docker cp scripts/list_phrases_all.py eigo-app:/app/scripts/
    docker exec -i eigo-app python scripts/list_phrases_all.py
    docker cp eigo-app:/data/phrases_all.json ./
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import paths  # noqa: E402
from app.database import db  # noqa: E402

OUT = paths.data_dir / "phrases_all.json"


def main() -> int:
    out: list[dict] = []
    with db() as conn:
        rows = conn.execute(
            "SELECT id, english, japanese, scene FROM phrases ORDER BY id"
        ).fetchall()
        for r in rows:
            out.append({
                "id": r["id"], "english": r["english"],
                "japanese": r["japanese"], "scene": r["scene"] or "",
            })
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    print(f"合計 {len(out)}件 → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
