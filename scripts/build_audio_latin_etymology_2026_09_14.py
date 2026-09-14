"""語源(ラテン語)ドメイン53語の音声を優先生成する(2026-09-14)。

新規追加した`語源(ラテン語)`ドメインの単語は、レベル順で処理する通常の
`build_audio.py`サイクルだと後回しになる(全16,444語中、現状レベル順で
まだ序盤しか終わっていないため)。本スクリプトはこのドメインの単語・
例文だけに絞り、学習速度+native速度の両方を一度に生成する。

`scripts/build_audio.py`の`_process`/`_gen_one`をそのまま再利用し、
コスト上限到達時の中断・スキップ済みの飛ばし方等の挙動を完全に揃えている。

使い方:
  python scripts/build_audio_latin_etymology_2026_09_14.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import db  # noqa: E402
from app.services import audio_store  # noqa: E402
from build_audio import _process, _total_cost  # noqa: E402

DOMAIN = "語源(ラテン語)"
VOICES = ["ash", "nova"]


def main() -> int:
    with db() as conn:
        rows = conn.execute(
            "SELECT id, english, example FROM words WHERE domain = ? "
            "ORDER BY id ASC",
            (DOMAIN,),
        ).fetchall()
        print(f"対象: {DOMAIN} {len(rows)}語")

        start_cost = _total_cost(conn)
        stopped = None

        jobs = [
            ("単語(学習)", "word", "word", "learn", rows, "english"),
            ("例文(学習)", "word", "example", "learn", rows, "example"),
            ("単語(native)", "word", "word_native", "native", rows, "english"),
            ("例文(native)", "word", "example_native", "native", rows,
             "example"),
        ]
        for label, item_type, skind, style, job_rows, text_key in jobs:
            if stopped is not None:
                break
            done, files, st = _process(
                conn, label, item_type, skind, style, job_rows, text_key,
                None, VOICES, False,
            )
            print(f"{label}: +{done} / +{files}ファイル (status={st})")
            if st != "ok":
                stopped = st

        end_cost = _total_cost(conn)

    print(f"今回の概算費用: ${end_cost - start_cost:.4f}")
    if stopped == "cap":
        print("※1日のコスト上限に達したため中断。")
    elif stopped == "aierr":
        print("※AIを利用できず中断しました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
