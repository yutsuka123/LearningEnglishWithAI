"""全単語の TOEIC レベルを AI で 50点刻みに再判定する（2026-07-01）。

禁止用語(domain='禁止用語')・範囲外(level='範囲外')は対象外（据置）。
それ以外の全語を 25語ずつバッチで AI に渡し、各語の TOEIC 難易度を
50点刻み(300〜950 の 50 刻み、超高難度は 990)で判定して level を更新する。

- 1バッチ = AI 1回。バッチごとにコミット（ロック回避・中断安全）。
- 日次コスト上限に達したら中断（次回続き）。
- 既存 level と同じでも上書きするが、実質変化がある語のみ表示。

使い方:
  python scripts/relevel_all_20260701.py               # 全件
  python scripts/relevel_all_20260701.py --limit 100   # 今回100語まで
  python scripts/relevel_all_20260701.py --batch 25    # バッチサイズ
  python scripts/relevel_all_20260701.py --dry-run
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

ALLOWED = {"300", "350", "400", "450", "500", "550", "600", "650", "700",
           "750", "800", "850", "900", "950", "990"}

SYSTEM = (
    "あなたは英語語彙のTOEIC難易度判定器。渡された英単語/連語の一覧に対し、"
    "各語が概ね何点レベルのTOEIC学習者向けかを判定する。出力は JSON のみ："
    '{"英単語": "レベル", ...}。レベルは次のいずれかの文字列を厳守: '
    "300,350,400,450,500,550,600,650,700,750,800,850,900,950,990。"
    "50点刻み。判定基準の目安: 300-450=基礎日常語(hammer,trash,browser), "
    "500-600=よく使う一般語(refrigerator,forecast,router), "
    "650-750=中上級・ビジネス/時事(recession,liability,altitude), "
    "800-850=上級・専門(jurisdiction,semiconductor,referendum), "
    "900-950=高度な専門用語(kinematics,subduction,avionics), "
    "990=極めて専門的で稀(cumulonimbus,dosimeter)。"
    "頻度と専門性で判断し、必ず一覧の全語にレベルを付ける。"
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
    ap.add_argument("--limit", type=int, default=0, help="0=全件")
    ap.add_argument("--batch", type=int, default=25)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not ai.is_enabled():
        print("OPENAI_API_KEY が未設定です。")
        return 1
    model = load_settings().quality_model

    with db() as conn:
        rows = conn.execute(
            "SELECT id, english, japanese, domain, level FROM words "
            "WHERE COALESCE(domain,'') <> '禁止用語' "
            "AND COALESCE(level,'') <> '範囲外' "
            "ORDER BY id"
        ).fetchall()
    if args.limit:
        rows = rows[:args.limit]
    total = len(rows)
    print(f"対象 {total} 語 / batch {args.batch} / model {model}")

    changed = same = failed = 0
    t0 = time.monotonic()
    with db() as conn:
        for i in range(0, total, args.batch):
            chunk = rows[i:i + args.batch]
            listing = "\n".join(
                f"- {r['english']} | {r['japanese']} | {r['domain'] or ''}"
                for r in chunk)
            res = ai.chat(SYSTEM, listing, temperature=0.0, max_tokens=900,
                          feature="detail", model=model, rate_limit=False)
            if not res.ok:
                if res.error and "上限" in res.error:
                    print("※日次コスト上限に到達。中断。")
                    break
                failed += len(chunk)
                continue
            data = _json_object(res.text) or {}
            # 大文字小文字を無視して引けるように
            low = {str(k).strip().lower(): str(v).strip() for k, v in
                   data.items()}
            for r in chunk:
                lv = low.get(r["english"].strip().lower())
                if lv not in ALLOWED:
                    failed += 1
                    continue
                if lv == (r["level"] or ""):
                    same += 1
                    continue
                changed += 1
                if not args.dry_run:
                    conn.execute("UPDATE words SET level=? WHERE id=?",
                                 (lv, r["id"]))
            if not args.dry_run:
                conn.commit()
            done = min(i + args.batch, total)
            if (done // args.batch) % 4 == 0:
                print(f"  {done}/{total} … 変更{changed} 据置{same} 失敗{failed}")

    dt = time.monotonic() - t0
    print("---")
    print(f"変更 {changed} / 据置 {same} / 失敗 {failed} / 所要 {dt:.1f}s")
    if args.dry_run:
        print("[dry-run] 保存していません。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
