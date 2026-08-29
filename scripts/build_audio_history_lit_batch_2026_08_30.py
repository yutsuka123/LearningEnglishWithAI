# ruff: noqa: E501
"""2026-08-30に追加した歴史/文学サブドメイン語彙151語だけを対象に、単語見出し
＋例文のTTS音声を生成する。

`scripts/build_audio.py`(既定)は`ORDER BY level ASC, id ASC`で**DB全体**の
未生成分から順に処理するため、このバッチ(level 550〜950)より低いlevelの
既存バックログが大量にあると、`--words 50 --examples 50`のような実行では
このバッチにまったく到達しない可能性が高い。実際、2026-08-30の先行実行
(`--words 50 --examples 50`)がこのバッチをどれだけ拾えたかは未検証だった
ため、本スクリプトで狙い撃ちして不足分だけを埋める。

対象の特定方法は`build_details_history_lit_batch_2026_08_30.py`と同じく、
`add_history_literature_subdomains_2026_08_30.py`のWORDS(151件の
english+domain組)をインポートしてidを正確に解決する(homographはdomainで
一意化)。

Run:  python scripts/build_audio_history_lit_batch_2026_08_30.py
      python scripts/build_audio_history_lit_batch_2026_08_30.py --voices ash,nova --force
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402
from app.services import ai, audio_store  # noqa: E402


def _load_batch_targets() -> list[tuple[str, str]]:
    add_script = Path(__file__).resolve().parent / \
        "add_history_literature_subdomains_2026_08_30.py"
    spec = importlib.util.spec_from_file_location("_add_batch", add_script)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return [(w[0], w[4]) for w in mod.WORDS]


def _gen_one(conn, item_type, item_id, skind, style, text, voices, force):
    """各声について音声が無ければ合成して保存。
    戻り値: (made, status)。status: 'ok'/'cap'/'aierr'。"""
    made = 0
    for v in voices:
        if not force and audio_store.get(
                conn, item_type, item_id, skind, v, text) is not None:
            continue
        audio, err = ai.synthesize_speech(text, v, style=style, rate_limit=False)
        if err:
            if "上限" in err:
                return made, "cap"
            if "未設定" in err or "初期化" in err:
                return made, "aierr"
            continue
        audio_store.put(conn, item_type, item_id, skind, v, text, audio)
        made += 1
    return made, "ok"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voices", default="ash,nova")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    voices = [v.strip() for v in args.voices.split(",") if v.strip()]

    if not ai.is_enabled():
        print("OPENAI_API_KEY が未設定のため音声生成できません。")
        return 1

    targets = _load_batch_targets()

    with db() as conn:
        rows = []
        notfound = 0
        for en, domain in targets:
            r = conn.execute(
                "SELECT id, english, example FROM words "
                "WHERE LOWER(english) = LOWER(?) AND domain = ?",
                (en, domain),
            ).fetchone()
            if r is None:
                notfound += 1
                continue
            rows.append(dict(r))
        print(f"対象 {len(targets)} 件中 DB照合成功 {len(rows)} 件 "
              f"(未検出 {notfound})")

        def _total_cost():
            return float(conn.execute(
                "SELECT COALESCE(SUM(cost_usd), 0) FROM ai_usage"
            ).fetchone()[0])

        start_cost = _total_cost()

        word_done = word_files = 0
        ex_done = ex_files = 0
        ex_skipped_empty = 0
        stopped = None

        for r in rows:
            text = (r["english"] or "").strip()
            if text and not (not args.force and all(
                    audio_store.get(conn, "word", r["id"], "word", v, text)
                    is not None for v in voices)):
                made, st = _gen_one(
                    conn, "word", r["id"], "word", "learn", text, voices,
                    args.force)
                word_files += made
                if st != "ok":
                    stopped = st
                    break
                word_done += 1
            elif text:
                word_done += 1  # 既に揃っていた

            ex_text = (r["example"] or "").strip()
            if not ex_text:
                ex_skipped_empty += 1
                continue
            if not args.force and all(
                    audio_store.get(conn, "word", r["id"], "example", v, ex_text)
                    is not None for v in voices):
                ex_done += 1
                continue
            made, st = _gen_one(
                conn, "word", r["id"], "example", "learn", ex_text, voices,
                args.force)
            ex_files += made
            if st != "ok":
                stopped = st
                break
            ex_done += 1

            if (word_done + ex_done) % 40 == 0:
                conn.commit()
                print(f"  進捗: 単語 {word_done}/{len(rows)} / "
                      f"例文 {ex_done}/{len(rows)}")

        conn.commit()
        end_cost = _total_cost()

    print("---")
    print(f"声: {voices}  force={args.force}")
    print(f"単語音声: カバー {word_done}/{len(rows)} (+{word_files}ファイル)")
    print(f"例文音声: カバー {ex_done}/{len(rows)} (+{ex_files}ファイル) "
          f"/ 例文なしでスキップ {ex_skipped_empty}")
    print(f"今回の概算費用: ${end_cost - start_cost:.4f}")
    if stopped == "cap":
        print("※1日のコスト上限に達したため中断しました。次回に続きを生成します。")
    elif stopped == "aierr":
        print("※AIを利用できず中断しました（キー設定等を確認）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
