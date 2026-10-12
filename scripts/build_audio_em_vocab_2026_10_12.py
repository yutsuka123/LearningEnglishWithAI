# ruff: noqa: E501
"""電磁気・電力(B28・2026-10-12)の新規語144語・フレーズ40件だけを対象に、TTS音声を生成する。

`scripts/build_audio.py`(既定)はDB全体の未生成バックログを level 昇順で処理するため、狙った追加分には届かない
(他の追加バッチ用スクリプトと同じ課題)。このバッチの語・フレーズだけを`scripts/add_em_vocab_2026_10_12.json`から特定し、
既存の全件完了の基準(単語見出し learn / 例文 learn+native / フレーズ learn+native × 声 ash,nova)と同じ種類を作る。

- 対象の特定: JSONのenglish(+語はdomain)でDBを引いてidを解決する(語は同綴り多義語があるのでdomainで一意化)。
- 保存済みはスキップ(何度でも安全に再実行できる)。IDはローカルと本番で異なるので、**本番では本番上で同じスクリプトを実行する**
  (ローカルで作った音声ファイルをrsyncしても、本番のIDとは対応しない)。
- 費用の目安: 約1,000ファイル × 約$0.0005 ≒ $0.5。1日コスト上限(AI_DAILY_COST_CAP_USD・既定$1)に当たったら中断し、再実行で続きから進む。

Run:  AI_DAILY_COST_CAP_USD=3 .venv/bin/python scripts/build_audio_em_vocab_2026_10_12.py [--dry-run] [--voices ash,nova] [--force]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import db  # noqa: E402
from app.services import ai, audio_store  # noqa: E402
from build_audio import _gen_one  # noqa: E402

DATA_JSON = Path(__file__).resolve().parent / "add_em_vocab_2026_10_12.json"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voices", default="ash,nova")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="対象の特定と未生成数の表示だけ(生成しない)")
    args = ap.parse_args()
    voices = [v.strip() for v in args.voices.split(",") if v.strip()]

    data = json.loads(DATA_JSON.read_text(encoding="utf-8"))
    if not args.dry_run and not ai.is_enabled():
        print("OPENAI_API_KEY が未設定のため音声生成できません。")
        return 1

    # (item_type, id, 保存kind, style, 本文)
    jobs: list[tuple[str, int, str, str, str]] = []
    with db() as conn:
        miss_w = miss_p = 0
        for w in data["words"]:
            r = conn.execute(
                "SELECT id, english, example FROM words WHERE LOWER(english) = LOWER(?) AND domain = ?",
                (w["english"], w["domain"])).fetchone()
            if r is None:
                miss_w += 1
                continue
            jobs.append(("word", r["id"], audio_store.storage_kind("word", "learn"), "learn", r["english"].strip()))
            ex = (r["example"] or "").strip()
            if ex:
                jobs.append(("word", r["id"], audio_store.storage_kind("example", "learn"), "learn", ex))
                jobs.append(("word", r["id"], audio_store.storage_kind("example", "native"), "native", ex))
        for p in data["phrases"]:
            r = conn.execute(
                "SELECT id, english FROM phrases WHERE english = ? AND scene = ?",
                (p["english"], p["scene"])).fetchone()
            if r is None:
                miss_p += 1
                continue
            t = r["english"].strip()
            jobs.append(("phrase", r["id"], audio_store.storage_kind("phrase", "learn"), "learn", t))
            jobs.append(("phrase", r["id"], audio_store.storage_kind("phrase", "native"), "native", t))
        print(f"対象: 語 {len(data['words']) - miss_w}/{len(data['words'])}・フレーズ {len(data['phrases']) - miss_p}/{len(data['phrases'])} "
              f"(DB未検出 語{miss_w}・フレーズ{miss_p}) → 音声ジョブ {len(jobs)}種 × 声{len(voices)}")
        todo = [j for j in jobs if args.force or not all(
            audio_store.get(conn, j[0], j[1], j[2], v, j[4]) is not None for v in voices)]
        print(f"未生成のジョブ: {len(todo)} (最大 {len(todo) * len(voices)} ファイル)")
        if args.dry_run:
            return 0

        def _cost() -> float:
            return float(conn.execute("SELECT COALESCE(SUM(cost_usd), 0) FROM ai_usage").fetchone()[0])

        start = _cost()
        files = done = 0
        stopped = None
        for item_type, iid, skind, style, text in todo:
            made, st = _gen_one(conn, item_type, iid, skind, style, text, voices, args.force)
            files += made
            if st != "ok":
                stopped = st
                break
            done += 1
            if done % 25 == 0:
                conn.commit()
                print(f"  進捗 {done}/{len(todo)} (+{files}ファイル)", flush=True)
        conn.commit()
        print("---")
        print(f"生成: ジョブ {done}/{len(todo)}・+{files}ファイル・概算費用 ${_cost() - start:.4f}")
        if stopped == "cap":
            print("※1日のコスト上限に達したため中断しました。再実行で続きから生成します。")
            return 3
        if stopped == "aierr":
            print("※AIを利用できず中断しました(キー設定等を確認)。")
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
