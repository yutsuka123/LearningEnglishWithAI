"""Incrementally pre-generate & save TTS audio for words and phrases.

音声DBを少しずつ増やすためのバッチ。番号(ID)＋種別＋声で `audio_store` に保存
するので、保存済みは飛ばして「次の未生成分」だけを作る（=何度でも安全に再実行
でき、毎回続きから進む）。再生時のオンデマンド保存とも共存する。

ガード: アプリの1日コスト上限(AI_DAILY_COST_CAP_USD)は常に有効。上限に達したら
そこで止まり、翌日/翌回に続きを生成（少しずつの方針どおり）。分間レート制限は
明示バッチなので外して連続生成する。

使い方:
  python scripts/build_audio.py                       # 既定 単語50 / フレーズ50
  python scripts/build_audio.py --words 300 --phrases 300
  python scripts/build_audio.py --examples 500        # 例文の音声も
  python scripts/build_audio.py --all                 # 全件(単語/例文/フレーズ)
  python scripts/build_audio.py --voices ash          # 片声だけ
対象: 単語見出し(kind=word) / 例文(kind=example) / フレーズ(kind=phrase)。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402
from app.services import ai, audio_store  # noqa: E402


def _total_cost(conn) -> float:
    return float(
        conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM ai_usage"
        ).fetchone()[0]
    )


def _gen_one(conn, item_type, item_id, kind, text, voices) -> tuple[int, str]:
    """Ensure audio exists for each voice. Returns (made, status).
    status: 'ok' / 'cap'（上限到達で中断）/ 'aierr'（AI不可で中断）。"""
    made = 0
    for v in voices:
        if audio_store.get(conn, item_type, item_id, kind, v) is not None:
            continue  # 既に保存済み → スキップ（無料）
        audio, err = ai.synthesize_speech(text, v, rate_limit=False)
        if err:
            if "上限" in err:
                return made, "cap"
            if "未設定" in err or "初期化" in err:
                return made, "aierr"
            # その他(一時的エラー等)はこの声だけ飛ばす
            continue
        audio_store.put(conn, item_type, item_id, kind, v, audio)
        made += 1
    return made, "ok"


def _process(conn, label, item_type, kind, rows, text_key, limit, voices):
    """rows を順に処理し、未生成分の音声を limit 件まで作る。
    Returns (done, files, status)。status: 'ok'/'cap'/'aierr'。"""
    done = files = 0
    for r in rows:
        if limit is not None and done >= limit:
            break
        text = (r[text_key] or "").strip()
        if not text:
            continue
        if all(audio_store.get(conn, item_type, r["id"], kind, v) is not None
               for v in voices):
            continue  # 全声そろい済み → 次の未生成へ
        made, st = _gen_one(conn, item_type, r["id"], kind, text, voices)
        files += made
        if st != "ok":
            return done, files, st
        done += 1
        if done % 25 == 0:
            conn.commit()
            tgt = limit if limit is not None else "全件"
            print(f"  {label} {done}/{tgt} … (+{files}ファイル)")
    conn.commit()
    return done, files, "ok"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--words", type=int, default=50)
    ap.add_argument("--phrases", type=int, default=50)
    ap.add_argument("--examples", type=int, default=0)
    ap.add_argument("--all", action="store_true",
                    help="単語/例文/フレーズを全件（件数指定を無視）")
    ap.add_argument("--voices", default="ash,nova")
    args = ap.parse_args()
    voices = [v.strip() for v in args.voices.split(",") if v.strip()]
    lim = (lambda n: None) if args.all else (lambda n: n)

    if not ai.is_enabled():
        print("OPENAI_API_KEY が未設定のため音声生成できません。")
        return 1

    # (label, item_type, kind, SQL, text_key, limit)
    jobs = [
        ("単語", "word", "word",
         "SELECT id, english FROM words ORDER BY level ASC, id ASC",
         "english", lim(args.words)),
        ("例文", "word", "example",
         "SELECT id, example FROM words "
         "WHERE COALESCE(TRIM(example), '') <> '' "
         "ORDER BY level ASC, id ASC",
         "example", lim(args.examples)),
        ("フレーズ", "phrase", "phrase",
         "SELECT id, english FROM phrases ORDER BY id ASC",
         "english", lim(args.phrases)),
    ]

    results = {}
    stopped = None
    with db() as conn:
        start_cost = _total_cost(conn)
        for label, item_type, kind, sql, key, limit in jobs:
            if stopped is not None or (limit is not None and limit <= 0):
                results[label] = (0, 0)
                continue
            rows = conn.execute(sql).fetchall()
            done, files, st = _process(
                conn, label, item_type, kind, rows, key, limit, voices)
            results[label] = (done, files)
            if st != "ok":
                stopped = st
        end_cost = _total_cost(conn)

    print("---")
    print(f"声: {voices}")
    for label in ("単語", "例文", "フレーズ"):
        d, f = results.get(label, (0, 0))
        print(f"{label}: +{d} / +{f}ファイル")
    print(f"今回の概算費用: ${end_cost - start_cost:.4f}")
    if stopped == "cap":
        print("※1日のコスト上限に達したため中断しました。"
              "翌日/次回に続きを生成します。")
    elif stopped == "aierr":
        print("※AIを利用できず中断しました（キー設定等を確認）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
