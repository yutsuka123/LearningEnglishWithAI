"""Pre-generate & cache TTS audio for public sample materials (2026-08-19).

`GET /api/learn/samples/{id}/tts` (未ログイン含め誰でも読める・
`app/routers/learn.py`の`sample_material_tts`)は、`ai.synthesize_speech`の
ディスクキャッシュにヒットすれば無料、ミスすれば都度OpenAIへ課金される。
公開サンプル教材(materials.is_public_sample=1)は件数が少なく固定なので、
このスクリプトで全件・使用声ぶん先に合成しておけば、訪問者の初回再生でも
ライブ課金が発生しなくなる（在庫化）。

`ai.synthesize_speech`自体がキャッシュ済みなら即返す(コスト0)ため、この
スクリプトは何度でも安全に再実行できる（未生成分だけ実際にAPIを叩く）。
1日のコスト上限(AI_DAILY_COST_CAP_USD)に達したらそこで中断する。

使い方:
  python scripts/build_sample_audio.py                  # 既定 声=ash,nova
  python scripts/build_sample_audio.py --voices ash
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import db  # noqa: E402
from app.services import ai  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--voices", default="ash,nova")
    args = ap.parse_args()
    voices = [v.strip() for v in args.voices.split(",") if v.strip()]

    if not ai.is_enabled():
        print("OPENAI_API_KEY が未設定のため音声生成できません。")
        return 1

    with db() as conn:
        rows = conn.execute(
            "SELECT id, area, body FROM materials "
            "WHERE is_public_sample = 1 ORDER BY id",
        ).fetchall()

    made = 0
    for r in rows:
        text = (r["body"] or "").strip()
        if not text:
            continue
        feature = "listening_tts" if r["area"] == "listening" else "reading_tts"
        for v in voices:
            audio, error = ai.synthesize_speech(
                text, v, feature=feature, free_range=True)
            if error:
                if "上限" in error:
                    print(f"※1日のコスト上限に達したため中断しました "
                          f"(id={r['id']} voice={v})。翌日/次回に続きを生成します。")
                    print(f"---\n生成: {made}件")
                    return 0
                print(f"警告: id={r['id']} voice={v}: {error}")
                continue
            made += 1

    print(f"---\n生成(または既存確認): {made}件 "
          f"({len(rows)}件 × {len(voices)}声)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
