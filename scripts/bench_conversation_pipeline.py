# ruff: noqa: E501
"""英会話1往復(STT → 返答LLM → TTS)の各段の所要時間を実測する(2026-09-26新設)。

背景: 「英会話の応答速度を改善したい」。scripts/conversation_speed_test.py(2026-08-22)は
LLMのモデル比較だけだったので、①実際のプロンプト(app/routers/learn.py
`_conversation_prompts`・学習者コンテキスト込み)、②`gpt-5.x`系の推論(reasoning)量の
違い、③TTSの文の長さ・ストリーミングの違い、④STTのモデル差、をまとめて測れるようにした。
(結論と実測値は CHANGELOG.md「未リリース・conversation-latency」参照。)

- **OpenAIを実際に呼ぶ(費用がかかる)**。`--max-cost-usd`(既定0.30)を超えそうなら止まる。
  費用は概算(トークン数×PRICING・TTSは文字数×0.015/1000・STTは音声秒数)。
- 読み取り専用(DBへは書かない)。ただしプロンプトの学習者コンテキストは既定のDATA_DIRを読む
  ので、本番相当を測りたくなければ `DATA_DIR=/tmp/xxx` を付ける。
- 各条件はラウンドロビン(条件A,B,C,A,B,C…)で測る(時間帯によるOpenAI側の揺れを均すため)。

使い方:
    .venv/bin/python3 scripts/bench_conversation_pipeline.py llm --models gpt-5.6-luna,gpt-5.6-luna@none,gpt-4o-mini --runs 10
        (`モデル@none` = reasoning_effort="none"。--part reply|all・--scene "グループ/トピック")
    .venv/bin/python3 scripts/bench_conversation_pipeline.py tts --runs 4
    .venv/bin/python3 scripts/bench_conversation_pipeline.py stt --audio /path/to/speech.webm --runs 4
"""

from __future__ import annotations

import argparse
import io
import os
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import httpx  # noqa: E402
from openai import OpenAI  # noqa: E402

from app.config import load_settings  # noqa: E402
from app.database import init_db  # noqa: E402
from app.routers import learn  # noqa: E402
from app.schemas import ConversationIn  # noqa: E402
from app.services import ai  # noqa: E402

_spent = 0.0
_budget = 0.30


def _charge(usd: float) -> None:
    global _spent
    _spent += usd
    if _spent > _budget:
        print(f"\n[中止] 費用の概算が上限(${_budget:.2f})を超えました: ${_spent:.4f}")
        raise SystemExit(2)


def _client() -> OpenAI:
    s = load_settings()
    if not s.ai_enabled:
        raise SystemExit("OPENAI_API_KEY が未設定です")
    return OpenAI(api_key=s.openai_api_key, max_retries=0,
                  timeout=httpx.Timeout(60.0, connect=10.0))


def _med(xs):
    xs = [x for x in xs if x is not None]
    return statistics.median(xs) if xs else float("nan")


# --- LLM ---------------------------------------------------------------------
def bench_llm(a) -> None:
    init_db()
    c = _client()
    grp, _, topic = a.scene.partition("/")
    hist = [] if a.empty_history else [
        {"role": "assistant", "content": "Welcome to the Grand Hotel. How can I help you today?"},
        {"role": "user", "content": "Hi, I have a reservation under the name Tanaka."},
        {"role": "assistant", "content": "Of course, Mr. Tanaka. Could I see your passport, please?"}]
    payload = ConversationIn(grp=grp, topic=topic, history=hist, message=a.message, part=a.part)
    system, user = learn._conversation_prompts(payload, a.part)
    print(f"scene={a.scene} part={a.part} history={len(hist)} system={len(system)}字 user={len(user)}字")
    labels = a.models.split(",")
    res: dict[str, list] = {m: [] for m in labels}

    def one(label: str):
        model, _, eff = label.partition("@")
        kw = {**ai._temperature_kwarg(model, 0.8), **ai._token_kwarg(model, 700 if a.part == "all" else 400)}
        if eff:
            kw["reasoning_effort"] = eff
        t0 = time.monotonic()
        first = None
        ptok = otok = rtok = 0
        stream = c.chat.completions.create(
            model=model, stream=True, stream_options={"include_usage": True},
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}], **kw)
        for ch in stream:
            if ch.usage is not None:
                ptok, otok = ch.usage.prompt_tokens, ch.usage.completion_tokens
                rtok = getattr(ch.usage.completion_tokens_details, "reasoning_tokens", 0) or 0
            if first is None and ch.choices and ch.choices[0].delta and ch.choices[0].delta.content:
                first = time.monotonic() - t0
        _charge(ai.estimate_cost(model, ptok, otok))
        return first, time.monotonic() - t0, ptok, otok, rtok

    for label in labels:  # ウォームアップ(接続確立)
        c.chat.completions.create(model=label.partition("@")[0], messages=[{"role": "user", "content": "hi"}],
                                  **ai._token_kwarg(label.partition("@")[0], 5))
    for _ in range(a.runs):
        for label in labels:
            res[label].append(one(label))
    print(f"{'条件':22} {'n':>3} {'最初の文字 中央値':>16} {'p90':>6} {'最大':>6} {'全文 中央値':>10} {'出力tok':>8} {'うち思考tok':>10} {'$/回':>9}")
    for label in labels:
        rs = res[label]
        fs = sorted(r[0] for r in rs if r[0] is not None)
        model = label.partition("@")[0]
        cost = statistics.mean(ai.estimate_cost(model, r[2], r[3]) for r in rs)
        print(f"{label:22} {len(rs):>3} {_med(fs):16.2f} {fs[max(0, int(len(fs) * 0.9) - 1)]:6.2f} {fs[-1]:6.2f} "
              f"{_med([r[1] for r in rs]):10.2f} {_med([r[3] for r in rs]):8.0f} {_med([r[4] for r in rs]):10.0f} {cost:9.5f}")


# --- TTS ---------------------------------------------------------------------
def bench_tts(a) -> None:
    c = _client()
    s = load_settings()
    instr = ai._tts_instructions("learn")
    texts = {
        "1文(45字)": "Yes, breakfast is included in your room rate.",
        "2文(91字)": "Yes, breakfast is included in your room rate. It's served from seven to ten in the morning.",
        "3文(129字)": "Thank you. Yes, breakfast is included in your room rate. It's served from seven to ten a.m. in the restaurant on the first floor.",
    }
    extra = {"instructions": instr} if "gpt-4o" in s.tts_model else {}
    res: dict[str, list] = {k: [] for k in texts}
    for _ in range(a.runs):
        for k, t in texts.items():
            t0 = time.monotonic()
            r = c.audio.speech.create(model=s.tts_model, voice="nova", input=t, response_format="mp3", **extra)
            b = r.read() if hasattr(r, "read") else r.content
            res[k].append((time.monotonic() - t0, len(b)))
            _charge(len(t) / 1000 * ai._TTS_USD_PER_1K_CHARS)
    print(f"TTS model={s.tts_model}")
    for k, xs in res.items():
        print(f"{k:12} n={len(xs)} 合成完了まで 中央値 {_med([x[0] for x in xs]):.2f}s (最小 {min(x[0] for x in xs):.2f} 最大 {max(x[0] for x in xs):.2f}) "
              f"不良音声(<{ai._MIN_SPEECH_BYTES}B) {sum(1 for x in xs if x[1] < ai._MIN_SPEECH_BYTES)}件")


# --- STT ---------------------------------------------------------------------
def bench_stt(a) -> None:
    c = _client()
    data = Path(a.audio).read_bytes()
    dur = float(a.audio_seconds)
    configs = [("whisper-1", "verbose_json", None), ("whisper-1", "verbose_json", "en"),
               ("gpt-4o-mini-transcribe", "json", None), ("gpt-4o-transcribe", "json", None)]
    res: dict[tuple, list] = {cf: [] for cf in configs}
    texts: dict[tuple, str] = {}
    for _ in range(a.runs):
        for cf in configs:
            f = io.BytesIO(data)
            f.name = Path(a.audio).name
            kw = {"model": cf[0], "file": f, "response_format": cf[1]}
            if cf[2]:
                kw["language"] = cf[2]
            t0 = time.monotonic()
            r = c.audio.transcriptions.create(**kw)
            res[cf].append(time.monotonic() - t0)
            texts[cf] = r.text
            _charge(dur / 60 * (0.003 if "mini" in cf[0] else 0.006))
    for cf, xs in res.items():
        print(f"{cf[0]:24} fmt={cf[1]:12} lang={str(cf[2]):5} n={len(xs)} 中央値 {_med(xs):.2f}s (最小 {min(xs):.2f} 最大 {max(xs):.2f})  {texts[cf][:60]!r}")


def main() -> None:
    global _budget
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--max-cost-usd", type=float, default=0.30)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("llm")
    p.add_argument("--models", default="gpt-5.6-luna,gpt-5.6-luna@none,gpt-4o-mini")
    p.add_argument("--part", default="reply", choices=["reply", "all"])
    p.add_argument("--scene", default="旅行/ホテルのチェックイン")
    p.add_argument("--message", default="Here you are. Is breakfast included in my room rate?")
    p.add_argument("--empty-history", action="store_true", help="会話の1発話目(履歴なし)を想定")
    p.add_argument("--runs", type=int, default=8)
    p = sub.add_parser("tts")
    p.add_argument("--runs", type=int, default=4)
    p = sub.add_parser("stt")
    p.add_argument("--audio", required=True)
    p.add_argument("--audio-seconds", default="5", help="費用の概算用")
    p.add_argument("--runs", type=int, default=4)
    a = ap.parse_args()
    _budget = a.max_cost_usd
    {"llm": bench_llm, "tts": bench_tts, "stt": bench_stt}[a.cmd](a)
    print(f"\n費用の概算: ${_spent:.4f}")


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    main()
