"""OpenAI integration with graceful no-key fallback + usage/cost tracking.

The whole app must run without an API key (per the requirements: "キーはまだ
無くてもOK"). Every AI call therefore returns a structured result that either
contains the model output or an ``ai_enabled=False`` marker, so the UI can show
a friendly "set your API key" message instead of crashing.

Token usage and an estimated USD cost are recorded for every successful call so
the UI can display API consumption (ユーザー要望: API使用量・費用の表示).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterator

from ..config import load_settings, log
from ..database import db

# Approx. USD price per 1M tokens (input, output). Update as needed.
# Source: OpenAI public pricing. Unknown models fall back to gpt-4o-mini.
PRICING = {
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
}


def _price_for(model: str) -> tuple[float, float]:
    return PRICING.get(model, PRICING["gpt-4o-mini"])


def estimate_cost(model: str, prompt_tokens: int, output_tokens: int) -> float:
    pin, pout = _price_for(model)
    return prompt_tokens / 1_000_000 * pin + output_tokens / 1_000_000 * pout


@dataclass
class AIResult:
    ok: bool
    text: str
    error: str | None = None
    cost_usd: float = 0.0
    prompt_tokens: int = 0
    output_tokens: int = 0


def _record_usage(
    model: str,
    prompt_tokens: int,
    output_tokens: int,
    feature: str,
) -> float:
    cost = estimate_cost(model, prompt_tokens, output_tokens)
    with db() as conn:
        conn.execute(
            "INSERT INTO ai_usage "
            "(model, prompt_tokens, output_tokens, cost_usd, feature) "
            "VALUES (?, ?, ?, ?, ?)",
            (model, prompt_tokens, output_tokens, cost, feature),
        )
    return cost


def _client():
    """Create an OpenAI client from current settings, or return None."""
    settings = load_settings()
    if not settings.ai_enabled:
        return None, settings
    try:
        from openai import OpenAI

        return OpenAI(api_key=settings.openai_api_key), settings
    except Exception:  # pragma: no cover - import/runtime guard
        log.exception("OpenAI クライアントの初期化に失敗")
        return None, settings


def is_enabled() -> bool:
    return load_settings().ai_enabled


def chat(
    system: str,
    user: str,
    *,
    temperature: float = 0.7,
    max_tokens: int = 1200,
    feature: str = "",
) -> AIResult:
    """Single-turn chat completion. Stateless by design — we never rely on
    server-side chat history; all context is passed in explicitly."""
    client, settings = _client()
    if client is None:
        if not settings.ai_enabled:
            return AIResult(
                ok=False,
                text="",
                error="OPENAI_API_KEY が未設定です。設定で登録してください。",
            )
        return AIResult(
            ok=False, text="", error="OpenAI クライアントを初期化できませんでした。"
        )

    try:
        resp = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        usage = resp.usage
        ptok = getattr(usage, "prompt_tokens", 0) or 0
        otok = getattr(usage, "completion_tokens", 0) or 0
        cost = _record_usage(settings.openai_model, ptok, otok, feature)
        return AIResult(
            ok=True,
            text=resp.choices[0].message.content or "",
            cost_usd=cost,
            prompt_tokens=ptok,
            output_tokens=otok,
        )
    except Exception as exc:
        log.error("chat 失敗 (feature=%s): %s", feature, exc)
        return AIResult(ok=False, text="", error=f"AI 呼び出しに失敗しました: {exc}")


def chat_stream(
    system: str,
    user: str,
    *,
    temperature: float = 0.7,
    max_tokens: int = 800,
    feature: str = "",
) -> Iterator[str]:
    """Yield text chunks as they arrive (improves perceived responsiveness).

    Yields plain text deltas. The final usage/cost is recorded at the end and
    is NOT yielded as text; callers stream text and can fetch usage separately.
    """
    client, settings = _client()
    if client is None:
        yield "[AI未設定] OPENAI_API_KEY を設定すると会話できます。"
        return

    try:
        stream = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
            stream_options={"include_usage": True},
        )
        ptok = otok = 0
        for chunk in stream:
            if chunk.usage is not None:
                ptok = chunk.usage.prompt_tokens or 0
                otok = chunk.usage.completion_tokens or 0
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta and delta.content:
                yield delta.content
        if ptok or otok:
            _record_usage(settings.openai_model, ptok, otok, feature)
    except Exception as exc:
        log.error("chat_stream 失敗 (feature=%s): %s", feature, exc)
        yield f"\n[エラー] {exc}"


# OpenAI TTS voices (ChatGPT-quality, natural). Names shown in the UI.
TTS_VOICES = [
    "alloy", "ash", "ballad", "coral", "echo",
    "fable", "nova", "onyx", "sage", "shimmer",
]

# Rough TTS cost estimate (USD per 1000 characters). gpt-4o-mini-tts is
# billed by tokens; we approximate from text length for the usage display.
_TTS_USD_PER_1K_CHARS = 0.015


def synthesize_speech(
    text: str, voice: str = "alloy"
) -> tuple[bytes | None, str | None]:
    """Return (audio_mp3_bytes, error). Uses OpenAI's natural TTS voices."""
    client, settings = _client()
    if client is None:
        if not settings.ai_enabled:
            return None, "OPENAI_API_KEY が未設定です。"
        return None, "OpenAI クライアントを初期化できませんでした。"
    if voice not in TTS_VOICES:
        voice = "alloy"
    try:
        resp = client.audio.speech.create(
            model=settings.tts_model,
            voice=voice,
            input=text[:4000],
            response_format="mp3",
        )
        audio = resp.read() if hasattr(resp, "read") else resp.content
        cost = len(text) / 1000 * _TTS_USD_PER_1K_CHARS
        with db() as conn:
            conn.execute(
                "INSERT INTO ai_usage "
                "(model, prompt_tokens, output_tokens, cost_usd, feature) "
                "VALUES (?, 0, 0, ?, 'tts')",
                (settings.tts_model, cost),
            )
        return audio, None
    except Exception as exc:
        log.error("TTS 失敗 (voice=%s, model=%s): %s",
                  voice, settings.tts_model, exc)
        return None, f"音声合成に失敗しました: {exc}"


def usage_summary() -> dict:
    """Return total + recent API usage and estimated cost for the UI."""
    with db() as conn:
        total = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) AS cost, "
            "COALESCE(SUM(prompt_tokens), 0) AS ptok, "
            "COALESCE(SUM(output_tokens), 0) AS otok, "
            "COUNT(*) AS calls FROM ai_usage"
        ).fetchone()
        today = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) AS cost "
            "FROM ai_usage WHERE date(created_at) = date('now')"
        ).fetchone()
        recent = conn.execute(
            "SELECT model, prompt_tokens, output_tokens, cost_usd, "
            "feature, created_at FROM ai_usage ORDER BY id DESC LIMIT 10"
        ).fetchall()
    return {
        "total_cost_usd": round(total["cost"], 4),
        "today_cost_usd": round(today["cost"], 4),
        "prompt_tokens": total["ptok"],
        "output_tokens": total["otok"],
        "calls": total["calls"],
        "recent": [dict(r) for r in recent],
    }
