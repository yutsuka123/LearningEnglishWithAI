# ruff: noqa: E501
"""同綴り異義語(agent/magnitude/tangent)で、分野違いの detail が丸ごとコピー
されていたバグの修正(2026-09-13発見)。

`agent`(AI)に`ビジネス`側の代理人の説明が、`magnitude`(天文)に`災害(種類)`側の
地震マグニチュードの説明が、`tangent`(口語)に`数学`側の正接の説明がそのまま
入っていた(id違いの別行に同一detailが複製されていた)。english列だけでの
一致は同綴り異義語で誤爆するため(`scripts/import_details.py`はid非対応)、
ここでは id を指定して確実に対象行だけを更新する。

Run:  python scripts/fix_domain_mismatch_details_2026_09_13.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402

JSON_PATH = Path(__file__).parent / "data" / "fix_domain_mismatch_details_2026_09_13.json"


def main() -> None:
    items = json.loads(JSON_PATH.read_text(encoding="utf-8"))
    with db() as conn:
        for item in items:
            wid = item["id"]
            eng = item["english"]
            dom_expect = item.get("domain")
            row = conn.execute(
                "SELECT english, domain FROM words WHERE id = ?", (wid,)
            ).fetchone()
            if row is None:
                print(f"skip id={wid}: 該当行なし")
                continue
            if row["english"].lower() != eng.lower():
                print(f"skip id={wid}: english不一致 ({row['english']!r})")
                continue
            if dom_expect and row["domain"] != dom_expect:
                print(
                    f"skip id={wid}: domain不一致 "
                    f"(期待={dom_expect!r} 実際={row['domain']!r})"
                )
                continue
            conn.execute(
                "UPDATE words SET detail = ? WHERE id = ?",
                (json.dumps(item["detail"], ensure_ascii=False), wid),
            )
            print(f"更新: id={wid} english={eng} domain={row['domain']}")


if __name__ == "__main__":
    main()
