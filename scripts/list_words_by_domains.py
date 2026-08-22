# ruff: noqa: E501
"""指定したdomain群に属する単語を全件書き出す（読み取り専用）。

背景（2026-08-22）: 例文訳の食い違い点検の副産物として、id 4906(fish
sauce)・4930(shrimp paste)・4934(condensed milk)の3件が`domain`は
「ベトナム料理」なのに`example`の内容はタイ料理だった、という
domainタグ不一致の疑いが見つかった。国・地域名を分野名に持つ
（料理・文化・地域別英語の）domainは、`example`の内容が本当にその
国・地域のものかを客観的にチェックできるため、まずこのクラスタから
機械的に候補を洗い出す。

**注意**: 1つの見出し語が複数domainに属すること自体は許可されている
（B17`word_domain_tags`機構）ので、ここで出てくる「不一致っぽい」候補は
即バグ確定ではない。人（AIエージェント）が1件ずつ、意図的な設計か単純な
ミスかを判断すること。

使い方（VPSのコンテナ内）:
    docker cp scripts/list_words_by_domains.py eigo-app:/app/scripts/
    docker exec -i eigo-app python scripts/list_words_by_domains.py \
        --domains "ベトナム料理,タイ料理,中華料理"
    docker cp eigo-app:/data/words_by_domains.json ./
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import paths  # noqa: E402
from app.database import db  # noqa: E402

OUT = paths.data_dir / "words_by_domains.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--domains", required=True,
                     help="カンマ区切りのdomain名リスト")
    args = ap.parse_args()
    domains = [d.strip() for d in args.domains.split(",") if d.strip()]

    out: list[dict] = []
    with db() as conn:
        qmarks = ",".join("?" for _ in domains)
        rows = conn.execute(
            f"SELECT id, english, japanese, domain, example FROM words "
            f"WHERE domain IN ({qmarks}) ORDER BY domain, id",
            domains,
        ).fetchall()
        for r in rows:
            out.append({
                "id": r["id"], "english": r["english"],
                "japanese": r["japanese"] or "",
                "domain": r["domain"] or "", "example": r["example"] or "",
            })

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                    encoding="utf-8")
    by_domain: dict[str, int] = {}
    for o in out:
        by_domain[o["domain"]] = by_domain.get(o["domain"], 0) + 1
    for d, n in sorted(by_domain.items()):
        print(f"  {d}: {n}件")
    print(f"合計 {len(out)}件 → {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
