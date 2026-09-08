# ruff: noqa: E501
"""2026-09-09に追加した残りのバッチ(知財4分野・VR/AR・AI安全性トップアップ・
組み込みソフト/エレキ・動物(類人猿)/動物(旧人類)・セミ・生物学/生化学
トップアップ・新語/流行語)の単語見出し＋例文のTTS音声をまとめて生成する。
動物学ニッチ6分野は別スクリプト(build_audio_zoology_niche_2026_09_09.py)で
対応済み。

`scripts/build_audio.py`(既定)はDB全体の未生成バックログを`ORDER BY
level ASC, id ASC`で順に処理するため、新規バッチのlevel帯によっては
到達が遅い可能性がある(過去バッチと同じ課題)。同じ方式で狙い撃ちする。

Run:  python scripts/build_audio_batch_2026_09_09.py
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402
from app.services import ai, audio_store  # noqa: E402

BATCH_SCRIPTS = [
    "add_ip_domains_2026_09_09.py",
    "add_vr_ar_2026_09_09.py",
    "add_ai_safety_topup_2026_09_09.py",
    "add_embedded_2026_09_09.py",
    "add_apes_archaic_humans_2026_09_09.py",
    "add_cicada_2026_09_09.py",
    "add_biology_cellbio_topup_2026_09_09.py",
    "add_slang_trends_2026_09_09.py",
]


def _load_batch_targets() -> list[tuple[str, str]]:
    targets: list[tuple[str, str]] = []
    for name in BATCH_SCRIPTS:
        add_script = Path(__file__).resolve().parent / name
        spec = importlib.util.spec_from_file_location("_add_batch_" + name, add_script)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        targets.extend((w[0], w[4]) for w in mod.WORDS)
    return targets


def _gen_one(conn, item_type, item_id, skind, style, text, voices, force):
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
                word_done += 1

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
