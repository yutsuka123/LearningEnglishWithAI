"""native速度音声を「無料枠」優先で生成する(2026-09-13・ユーザー指示)。

native速度(例文・フレーズ)は`build_audio.py --native`だと単語のlevel昇順/
phraseはid昇順で処理するため、無料枠(`app/services/access_tiers.py`の
`free_range_ids`、レベル昇順で上位N件・誰でも無料で再生できる範囲)を必ずしも
先に埋められない。本スクリプトは`free_range_ids(guest=False)`
(②ログイン無料ユーザー向け=単語2,000語・フレーズ1,500件、①ゲストの
1,000語・750件はこの部分集合)に限定して例文native・フレーズnativeだけを
生成する。無料枠を使い切ったら`build_audio.py --examples <N> --phrases <N>
--native`で残り(無料枠外)を続けること。

`scripts/build_audio.py`の`_process`/`_gen_one`をそのまま再利用し、コスト
上限到達時の中断・スキップ済みの飛ばし方等の挙動を完全に揃えている。

使い方:
  python scripts/build_audio_free_range_native_2026_09_13.py
  python scripts/build_audio_free_range_native_2026_09_13.py --voices ash
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.database import db  # noqa: E402
from app.services import access_tiers, audio_store  # noqa: E402
from build_audio import _process, _total_cost  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voices", default="ash,nova")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    voices = [v.strip() for v in args.voices.split(",") if v.strip()]

    with db() as conn:
        word_ids = access_tiers.free_range_ids(conn, "word", guest=False)
        phrase_ids = access_tiers.free_range_ids(conn, "phrase", guest=False)
        print(f"無料枠: 単語 {len(word_ids)}件 / フレーズ {len(phrase_ids)}件")

        w_placeholders = ",".join("?" * len(word_ids))
        ex_rows = conn.execute(
            "SELECT id, example FROM words "
            f"WHERE id IN ({w_placeholders}) "
            "AND COALESCE(TRIM(example), '') <> '' "
            "ORDER BY level ASC, id ASC",
            list(word_ids),
        ).fetchall()

        p_placeholders = ",".join("?" * len(phrase_ids))
        ph_rows = conn.execute(
            "SELECT id, english FROM phrases "
            f"WHERE id IN ({p_placeholders}) "
            "ORDER BY level ASC, id ASC",
            list(phrase_ids),
        ).fetchall()

        start_cost = _total_cost(conn)
        stopped = None

        skind_ex = audio_store.storage_kind("example", "native")
        done, files, st = _process(
            conn, "例文native(無料枠)", "word", skind_ex, "native",
            ex_rows, "example", None, voices, args.force,
        )
        print(f"例文native(無料枠): +{done} / +{files}ファイル (status={st})")
        if st != "ok":
            stopped = st

        if stopped is None:
            skind_ph = audio_store.storage_kind("phrase", "native")
            done, files, st = _process(
                conn, "フレーズnative(無料枠)", "phrase", skind_ph, "native",
                ph_rows, "english", None, voices, args.force,
            )
            print(f"フレーズnative(無料枠): +{done} / +{files}ファイル "
                  f"(status={st})")
            if st != "ok":
                stopped = st

        end_cost = _total_cost(conn)

    print(f"今回の概算費用: ${end_cost - start_cost:.4f}")
    if stopped == "cap":
        print("※1日のコスト上限に達したため中断。翌日/次回に続きを生成します。")
    elif stopped == "aierr":
        print("※AIを利用できず中断しました。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
