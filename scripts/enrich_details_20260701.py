"""既存語の detail を「現状を崩さず」リッチ化する（語源分解＋豆知識）。

方針:
  - 既存 detail の meanings/examples/derivatives/synonyms/antonyms/explanation
    などは **そのまま保持**する（上書きしない）。
  - AI で `origin`(語源・接頭辞/語根分解) と `trivia`(豆知識・著名人/聖書/哲学/
    技術/名言/書籍との関連) だけを作り直してマージする。
  - `pronunciation`(IPA) が既存に無い場合のみ補う（あれば触らない）。

これにより「崩さずリッチに」できる。所要時間の計測用に per 語の平均時間と
500語換算の見積もりを表示する。1語ごとにコミット（ロック回避）。

使い方:
  python scripts/enrich_details_20260701.py --limit 5            # まず5語で試す
  python scripts/enrich_details_20260701.py --limit 500          # 500語
  python scripts/enrich_details_20260701.py --limit 5 --dry-run  # 生成のみ・非保存
  # 対象は既定で「本日以外に追加された detail 済みの語」（=既存語）。id昇順。
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import load_settings  # noqa: E402
from app.database import db  # noqa: E402
from app.services import ai  # noqa: E402

SYSTEM = (
    "英単語の『語源』と『豆知識』だけを日本語でJSONのみ作成。キー: "
    "origin(語源・由来。可能なら接頭辞/語根/接尾辞に分解し各要素の意味を示す"
    "(例: abnormal = ab-「離れて」+ normal「正常」)。語源に出てくる語があれば"
    "その意味も一言添える), "
    "trivia(豆知識。関連が本当にあれば、著名人・聖書・哲学・有名な技術・歴史上の"
    "名言や出来事・有名な書籍や映画のセリフとの結びつきを1つ挙げる。無理に作らず"
    "自然なものだけ), "
    "pronunciation(発音記号・IPA。米音を基本にスラッシュで囲む 例: /əˈbændən/). "
    "簡潔に。必ず完結したJSONのみを出力（途中で切らない）。"
)


def _json_object(text: str) -> dict | None:
    a, b = text.find("{"), text.rfind("}")
    if a == -1 or b == -1:
        return None
    try:
        d = json.loads(text[a:b + 1])
        return d if isinstance(d, dict) else None
    except (json.JSONDecodeError, ValueError):
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--order", choices=["id", "level"], default="id")
    ap.add_argument("--include-today", action="store_true",
                    help="本日追加分も対象に含める（既定は既存語のみ）")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not ai.is_enabled():
        print("OPENAI_API_KEY が未設定です。")
        return 1

    model = load_settings().quality_model
    date_cond = "" if args.include_today else "AND created_at < date('now')"
    order = "id ASC" if args.order == "id" else "level ASC, id ASC"
    sql = (f"SELECT id, english, japanese, detail FROM words "
           f"WHERE COALESCE(TRIM(detail), '') <> '' {date_cond} "
           f"ORDER BY {order} LIMIT ?")

    made = failed = 0
    t0 = time.monotonic()
    with db() as conn:
        rows = conn.execute(sql, (args.limit,)).fetchall()
        print(f"対象 {len(rows)} 語 / モデル {model} / dry_run={args.dry_run}")
        for r in rows:
            old = _json_object(r["detail"])
            if old is None:
                failed += 1
                print(f"  [skip] {r['english']}: 既存detailがJSONでない")
                continue
            user = (
                f"単語: {r['english']}\n訳: {r['japanese']}\n"
                f"主な意味: {'; '.join(old.get('meanings', [])) or 'なし'}"
            )
            res = ai.chat(SYSTEM, user, temperature=0.3, max_tokens=700,
                          feature="detail", model=model, rate_limit=False)
            if not res.ok:
                if res.error and "上限" in res.error:
                    print("※日次コスト上限に到達。中断。")
                    break
                failed += 1
                continue
            new = _json_object(res.text)
            if not new:
                failed += 1
                continue
            # ── 崩さずマージ：origin/trivia は差し替え、pronunciation は不足時のみ
            merged = dict(old)
            if new.get("origin"):
                merged["origin"] = new["origin"]
            if new.get("trivia"):
                merged["trivia"] = new["trivia"]
            if not merged.get("pronunciation") and new.get("pronunciation"):
                merged["pronunciation"] = new["pronunciation"]

            if args.dry_run:
                print(f"--- {r['english']} ---")
                print("  origin :", merged.get("origin"))
                print("  trivia :", merged.get("trivia"))
                print("  保持キー:", [k for k in old
                                      if k not in ("origin", "trivia")])
            else:
                conn.execute(
                    "UPDATE words SET detail = ? WHERE id = ?",
                    (json.dumps(merged, ensure_ascii=False), r["id"]),
                )
                conn.commit()
            made += 1

    dt = time.monotonic() - t0
    per = dt / made if made else 0.0
    print("---")
    print(f"処理 {made} 語 / 失敗 {failed} / 所要 {dt:.1f}s "
          f"（1語あたり {per:.2f}s）")
    if per:
        print(f"500語換算の目安: 約 {per * 500 / 60:.1f} 分")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
