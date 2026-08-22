# ruff: noqa: E501
"""英会話（chat_stream）の応答速度をモデル別に実測する（2026-08-22新設）。

背景: ユーザーから「英会話の応答速度を上げたい（認識→応答）」との要望。
価格が上がる場合は「応答速度を上げる（pt消費アップ）」のオプション
チェックボックスにする方針で、既存の会話マージン（`CATEGORY_MULTIPLIER
["conversation"] = 2.5倍`）に準じてpt消費を計算する。まず候補モデルの
実際のレイテンシ（最初のチャンクが届くまで・全文完了まで）を計測して、
「速い」オプションにどのモデルを使うべきかを決める材料にする。

使い方:
    .venv/bin/python3 scripts/conversation_speed_test.py
    .venv/bin/python3 scripts/conversation_speed_test.py --models gpt-5.6-luna,gpt-4o-mini
    .venv/bin/python3 scripts/conversation_speed_test.py --runs 3   # 各モデルN回平均
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from openai import OpenAI  # noqa: E402

from app.config import load_settings  # noqa: E402
from app.services.ai import (  # noqa: E402
    PRICING, _temperature_kwarg, _token_kwarg, estimate_cost,
)

# app/routers/learn.py の _conversation_prompts() のシーン分岐と
# ほぼ同じ長さ・構造のプロンプトで、実運用に近い条件にする。
SYSTEM = (
    "あなたは親切な英会話パートナー兼コーチです。学習者のレベルはTOEIC"
    "600点前後です。専門用語は避け、平易な語彙・短い文で話してください。"
    " シーン: レストラン・カフェ / 注文する。"
    " 自然な英語で短めに返答し、次に【コーチ】として学習者の文の"
    "良い点と直すべき点を日本語で1〜2行。"
    " さらに最後の行に『【例】<学習者が言える改善後の自然な英文>』"
    "を必ず1文付けてください（この英文は読み上げ用）。"
    " 日本語では、暴力・自傷・性的な内容など不適切な要求には応じない。"
)
USER = (
    "## これまでの会話\n"
    "assistant: Hi there! Welcome in. Are you ready to order, "
    "or would you like a few more minutes?\n"
    "user: I want a coffee.\n"
    "assistant: Great choice! What size would you like — small, "
    "medium, or large?\n\n"
    "## 学習者の発話\n"
    "Medium size, and I want also a cake please."
)

DEFAULT_MODELS = ["gpt-5.6-luna", "gpt-4o-mini", "gpt-4.1-mini", "gpt-5.4-mini"]


def run_once(client: OpenAI, model: str) -> dict:
    t0 = time.monotonic()
    first_chunk_t = None
    text = []
    ptok = otok = 0
    stream = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": USER},
        ],
        **_temperature_kwarg(model, 0.8),
        **_token_kwarg(model, 700),
        stream=True,
        stream_options={"include_usage": True},
    )
    for chunk in stream:
        if chunk.usage is not None:
            ptok = chunk.usage.prompt_tokens or 0
            otok = chunk.usage.completion_tokens or 0
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        if delta and delta.content:
            if first_chunk_t is None:
                first_chunk_t = time.monotonic()
            text.append(delta.content)
    t1 = time.monotonic()
    cost = estimate_cost(model, ptok, otok)
    return {
        "model": model,
        "ttfc_ms": round((first_chunk_t - t0) * 1000) if first_chunk_t else None,
        "total_ms": round((t1 - t0) * 1000),
        "prompt_tokens": ptok,
        "output_tokens": otok,
        "cost_usd": round(cost, 6),
        "known_price": model in PRICING,
        "reply": "".join(text),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", default=",".join(DEFAULT_MODELS))
    ap.add_argument("--runs", type=int, default=2)
    args = ap.parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    settings = load_settings()
    if not settings.openai_api_key:
        print("OPENAI_API_KEY が未設定です。")
        return 1
    client = OpenAI(api_key=settings.openai_api_key)

    print(f"{'model':<16} {'run':>3} {'TTFC(ms)':>9} {'total(ms)':>10} "
          f"{'out_tok':>8} {'cost_usd':>10}")
    results: dict[str, list[dict]] = {}
    for model in models:
        results[model] = []
        for i in range(args.runs):
            try:
                r = run_once(client, model)
            except Exception as exc:
                print(f"{model:<16} run{i+1}: ERROR {exc}")
                continue
            results[model].append(r)
            print(f"{model:<16} {i+1:>3} {str(r['ttfc_ms']):>9} "
                  f"{r['total_ms']:>10} {r['output_tokens']:>8} "
                  f"{r['cost_usd']:>10}")

    print("\n=== 平均 ===")
    print(f"{'model':<16} {'avg TTFC':>9} {'avg total':>10} {'known_price':>12}")
    for model, rs in results.items():
        if not rs:
            continue
        ttfcs = [r["ttfc_ms"] for r in rs if r["ttfc_ms"] is not None]
        avg_ttfc = round(sum(ttfcs) / len(ttfcs)) if ttfcs else None
        avg_total = round(sum(r["total_ms"] for r in rs) / len(rs))
        print(f"{model:<16} {str(avg_ttfc):>9} {avg_total:>10} "
              f"{str(rs[0]['known_price']):>12}")

    print("\n=== 返答サンプル（最初のrunのみ） ===")
    for model, rs in results.items():
        if not rs:
            continue
        print(f"\n--- {model} ---")
        print(rs[0]["reply"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
