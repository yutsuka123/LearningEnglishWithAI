"""OpenAI integration with graceful no-key fallback + usage/cost tracking.

The whole app must run without an API key (per the requirements: "キーはまだ
無くてもOK"). Every AI call therefore returns a structured result that either
contains the model output or an ``ai_enabled=False`` marker, so the UI can show
a friendly "set your API key" message instead of crashing.

Token usage and an estimated USD cost are recorded for every successful call so
the UI can display API consumption (ユーザー要望: API使用量・費用の表示).
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass
from typing import Iterator

from ..config import load_settings, log
from ..database import db

# ---------------------------------------------------------------------------
# Cost / rate guards — prevent runaway spend if something loops or misbehaves.
# Two independent limits, both configurable via .env:
#   * AI_DAILY_COST_CAP_USD — refuse once today's spend reaches the cap.
#   * AI_MAX_CALLS_PER_MIN  — refuse if calls arrive too fast (loop guard).
# Refusals are returned as a normal "AI unavailable" result so the UI shows a
# friendly message and (for TTS) falls back to the free browser voice.
# ---------------------------------------------------------------------------

_call_times: deque[float] = deque(maxlen=240)  # recent call timestamps (mono)


def _today_cost_usd() -> float:
    with db() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) AS c FROM ai_usage "
            "WHERE date(created_at, 'localtime') = date('now', 'localtime')"
        ).fetchone()
    return float(row["c"] or 0.0)


def _user_cost_usd(user_id: int, period: str) -> float:
    """Sum of a single user's AI cost over 'day' (local day) or 'month'."""
    if period == "month":
        clause = ("strftime('%Y-%m', created_at, 'localtime') = "
                  "strftime('%Y-%m', 'now', 'localtime')")
    else:
        clause = ("date(created_at, 'localtime') = "
                  "date('now', 'localtime')")
    with db() as conn:
        row = conn.execute(
            f"SELECT COALESCE(SUM(cost_usd), 0) AS c FROM ai_usage "
            f"WHERE user_id = ? AND {clause}", (user_id,)
        ).fetchone()
    return float(row["c"] or 0.0)


def _effective_caps(u: dict, s) -> tuple:
    """ユーザーの実効 日次/月次 上限(USD)。日次は個別→無ければグローバル既定。
    月次は個別のみ(未設定=なし)。"""
    dcap = u.get("daily_cost_cap_usd")
    dcap = float(dcap) if dcap else (s.ai_daily_cost_cap_usd or None)
    mcap = u.get("monthly_cost_cap_usd")
    mcap = float(mcap) if mcap else None
    return dcap, mcap


def _user_guard(s) -> str | None:
    """課金モデル: 日次/月次の上限は「無料枠」。枠に到達したら**前払いチャージ
    残高**を消費して継続（残高は枠とは別管理）。残高が無ければ停止。
    Owner(個別上限なし)はグローバル日次上限のみが効く。"""
    from .auth import current_user_id, get_user

    uid = current_user_id()
    with db() as conn:
        u = get_user(conn, uid)
    if not u:
        return None
    dcap, mcap = _effective_caps(u, s)
    over_daily = bool(dcap and dcap > 0 and _user_cost_usd(uid, "day") >= dcap)
    over_monthly = bool(
        mcap and mcap > 0 and _user_cost_usd(uid, "month") >= mcap)
    if over_daily or over_monthly:
        bal = u.get("balance_jpy")
        if bal is not None and float(bal) > 0:
            return None  # 枠到達だがチャージ残高で継続（_record_usageで消費）
        which = "本日" if over_daily else "今月"
        return (f"{which}の利用上限に達しました。管理者によるチャージ(¥500)で"
                "継続できます。")
    return None


def budget_status() -> dict:
    """Today's spend vs. the configured cap (for the UI / settings display)."""
    s = load_settings()
    spent = _today_cost_usd()
    cap = s.ai_daily_cost_cap_usd
    return {
        "today_cost_usd": round(spent, 4),
        "cap_usd": cap,
        "remaining_usd": round(max(0.0, cap - spent), 4),
        "blocked": cap > 0 and spent >= cap,
        "calls_per_min_cap": s.ai_max_calls_per_min,
    }


def _guard(feature: str, *, rate_limit: bool = True) -> str | None:
    """Return a refusal message if a guard trips, else None. The daily cost
    cap is ALWAYS enforced. The per-minute rate limit can be skipped for an
    explicit, user-authorized batch (``rate_limit=False``) — the cap still
    stops it once the day's budget is spent, so it resumes next run."""
    s = load_settings()
    # ユーザー別ガード（日次/月次上限・前払い残高）。owner で個別設定が無ければ
    # グローバル日次上限のみが効く＝従来のローカル単一ユーザー動作と同じ。
    refusal = _user_guard(s)
    if refusal:
        return refusal
    if rate_limit:
        now = time.monotonic()
        window = [t for t in _call_times if now - t < 60.0]
        if len(window) >= s.ai_max_calls_per_min:
            return (
                f"AI呼び出しが短時間に集中しています（上限 "
                f"{s.ai_max_calls_per_min}回/分）。少し待ってから再試行して"
                "ください。"
            )
        _call_times.append(now)
    return None


# Approx. USD price per 1M tokens (input, output). Update as needed.
# Source: OpenAI public pricing. Unknown models fall back to gpt-4o-mini.
PRICING = {
    # 既定(標準ティア)。4o/4o-mini を使っていた箇所はこれに統一。
    "gpt-5.4-mini": (0.75, 4.50),
    # 高品質ティア(gpt-5.4 フル)。<272K context の標準レート。
    "gpt-5.4": (2.50, 15.00),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1-mini": (0.40, 1.60),
    "gpt-4.1": (2.00, 8.00),
}


def _price_for(model: str) -> tuple[float, float]:
    return PRICING.get(model, PRICING["gpt-5.4-mini"])


def _token_kwarg(model: str, n: int) -> dict:
    """新しめのモデル(gpt-5系 / o系)は max_tokens 非対応で
    max_completion_tokens を使う。旧モデル(4o/4.1)は従来どおり max_tokens。"""
    m = (model or "").lower()
    if m.startswith("gpt-5") or m.startswith(("o1", "o3", "o4")):
        return {"max_completion_tokens": n}
    return {"max_tokens": n}


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
    from .auth import current_user_id

    cost = estimate_cost(model, prompt_tokens, output_tokens)
    uid = current_user_id()
    s = load_settings()
    with db() as conn:
        conn.execute(
            "INSERT INTO ai_usage "
            "(model, prompt_tokens, output_tokens, cost_usd, feature, "
            " user_id) VALUES (?, ?, ?, ?, ?, ?)",
            (model, prompt_tokens, output_tokens, cost, feature, uid),
        )
        # チャージ残高は「無料枠（日次/月次上限）に到達した後の利用」でのみ消費
        # する（枠とは別管理）。枠内の利用では残高を減らさない。
        from .auth import get_user
        u = get_user(conn, uid)
        if u and u.get("balance_jpy") is not None:
            dcap, mcap = _effective_caps(u, s)
            # _user_cost_usd は別接続でコミット済み分のみ参照する＝この呼び出し
            # 直前(この分を除く)の累計。直前で枠到達済みなら「枠外利用」として控除。
            prior_day = _user_cost_usd(uid, "day")
            prior_mon = _user_cost_usd(uid, "month")
            over = ((dcap and dcap > 0 and prior_day >= dcap)
                    or (mcap and mcap > 0 and prior_mon >= mcap))
            if over:
                charge = cost * s.usd_jpy_rate * 1.5  # 原価×為替×1.5
                conn.execute(
                    "UPDATE users SET balance_jpy = "
                    "MAX(0, balance_jpy - ?) WHERE id = ?", (charge, uid),
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
    model: str | None = None,
    rate_limit: bool = True,
) -> AIResult:
    """Single-turn chat completion. Stateless by design — we never rely on
    server-side chat history; all context is passed in explicitly.

    ``model`` overrides the configured chat model (used for判定/教材生成).
    ``rate_limit=False`` skips the per-minute cap for an explicit, authorized
    batch (the daily cost cap still applies and will stop it once spent)."""
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

    refusal = _guard(feature, rate_limit=rate_limit)
    if refusal:
        return AIResult(ok=False, text="", error=refusal)

    use_model = model or settings.openai_model
    capped = min(max_tokens, settings.ai_max_output_tokens)
    try:
        resp = client.chat.completions.create(
            model=use_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            **_token_kwarg(use_model, capped),
        )
        usage = resp.usage
        ptok = getattr(usage, "prompt_tokens", 0) or 0
        otok = getattr(usage, "completion_tokens", 0) or 0
        cost = _record_usage(use_model, ptok, otok, feature)
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

    refusal = _guard(feature)
    if refusal:
        yield f"[停止] {refusal}"
        return

    try:
        stream = client.chat.completions.create(
            model=settings.openai_model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            **_token_kwarg(
                settings.openai_model,
                min(max_tokens, settings.ai_max_output_tokens),
            ),
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


# 読み上げの話し方プリセット（gpt-4o-mini-tts の品質を安定させる）。
#   learn  … 学習用。落ち着いた一定ペース・やや遅め・明瞭（指示なしだと文の
#            抑揚が過剰・不自然になるのを防ぐ）。
#   native … ネイティブの自然な速さ・リズム・リンキング（少し速い）。
TTS_STYLES = {
    "learn": (
        "You are a clear, friendly English teacher reading for a learner. "
        "Speak in natural, standard English with calm, even intonation and a "
        "steady, slightly slower pace. Pronounce every word clearly and "
        "distinctly. Do not rush, do not add emotion, drama, whispering, or "
        "any accent."
    ),
    "native": (
        "Speak in natural, native English at a normal conversational pace "
        "and rhythm, with the natural linking, stress, and flow a native "
        "speaker uses in everyday speech. Keep it clear and easy to follow. "
        "Neutral, friendly tone; no exaggeration, drama, or strong accent."
    ),
}
TTS_STYLE_DEFAULT = "learn"


def _tts_instructions(style: str = TTS_STYLE_DEFAULT) -> str:
    import os
    if style == "learn":
        env = os.getenv("OPENAI_TTS_INSTRUCTIONS", "").strip()
        if env:
            return env
    return TTS_STYLES.get(style, TTS_STYLES["learn"])


def _tts_cache_path(model: str, voice: str, text: str, instr: str = ""):
    import hashlib

    from ..config import paths

    key = f"{model}|{voice}|{instr}|{text}".encode("utf-8")
    digest = hashlib.sha256(key).hexdigest()[:32]
    cache_dir = paths.data_dir / "tts_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir / f"{digest}.mp3"


def synthesize_speech(
    text: str, voice: str = "alloy", *,
    style: str = TTS_STYLE_DEFAULT, rate_limit: bool = True
) -> tuple[bytes | None, str | None]:
    """Return (audio_mp3_bytes, error). Uses OpenAI's natural TTS voices.

    Audio is cached on disk by (model, voice, instructions, text); a cache hit
    costs nothing and makes repeated playback free。``style`` で読み上げの
    話し方を選ぶ（'learn'=学習用ゆっくり明瞭 / 'native'=ネイティブの自然な速さ）。
    """
    client, settings = _client()
    if client is None:
        if not settings.ai_enabled:
            return None, "OPENAI_API_KEY が未設定です。"
        return None, "OpenAI クライアントを初期化できませんでした。"
    if voice not in TTS_VOICES:
        voice = "alloy"

    instr = _tts_instructions(style)
    cache = _tts_cache_path(settings.tts_model, voice, text[:4000], instr)
    if cache.exists():
        return cache.read_bytes(), None  # cache hit → no API call, no cost

    # only a real (paid) synthesis hits the guard
    refusal = _guard("tts", rate_limit=rate_limit)
    if refusal:
        return None, refusal

    # instructions は gpt-4o-mini-tts 系のみ対応（tts-1系は非対応なので付けない）
    extra = {}
    if instr and "gpt-4o" in settings.tts_model:
        extra["instructions"] = instr
    try:
        resp = client.audio.speech.create(
            model=settings.tts_model,
            voice=voice,
            input=text[:4000],
            response_format="mp3",
            **extra,
        )
        audio = resp.read() if hasattr(resp, "read") else resp.content
        try:
            cache.write_bytes(audio)
        except Exception:  # caching is best-effort
            pass
        cost = len(text) / 1000 * _TTS_USD_PER_1K_CHARS
        from .auth import current_user_id
        with db() as conn:
            conn.execute(
                "INSERT INTO ai_usage "
                "(model, prompt_tokens, output_tokens, cost_usd, feature, "
                " user_id) VALUES (?, 0, 0, ?, 'tts', ?)",
                (settings.tts_model, cost, current_user_id()),
            )
        return audio, None
    except Exception as exc:
        log.error("TTS 失敗 (voice=%s, model=%s): %s",
                  voice, settings.tts_model, exc)
        return None, f"音声合成に失敗しました: {exc}"


# 認識言語ヒント: ISO-639-1 コード → Whisper が verbose_json で返す言語名。
_LANG_NAMES = {
    "en": "english", "ja": "japanese", "zh": "chinese", "ko": "korean",
}


def transcribe(
    audio_bytes: bytes, filename: str = "audio.webm", language: str = "",
) -> tuple[str | None, str | None]:
    """Speech-to-text via OpenAI Whisper. Returns (text, error).

    ``language`` は認識言語のヒント(誤認識対策):
    * ""            … 完全自動判定(従来動作)
    * "en"          … その言語に固定(例: 英語以外に化けるのを防ぐ)
    * "en,ja" など  … 候補を限定。自動判定し、候補外(例:韓国語)に化けたら
                       先頭の言語で取り直す。
    """
    import io

    client, settings = _client()
    if client is None:
        if not settings.ai_enabled:
            return None, "OPENAI_API_KEY が未設定です。"
        return None, "OpenAI クライアントを初期化できませんでした。"
    refusal = _guard("stt")
    if refusal:
        return None, refusal
    allowed = [c.strip().lower() for c in (language or "").split(",")
               if c.strip()]

    def _call(lang: str | None, verbose: bool):
        f = io.BytesIO(audio_bytes)
        f.name = filename
        kw: dict = {"model": "whisper-1", "file": f}
        if lang:
            kw["language"] = lang
        if verbose:
            kw["response_format"] = "verbose_json"
        return client.audio.transcriptions.create(**kw)

    try:
        calls = 1
        if len(allowed) == 1:
            resp = _call(allowed[0], False)
            text = resp.text
        elif len(allowed) >= 2:
            # 候補が複数: 自動判定し、候補外に化けたら先頭言語で取り直す。
            resp = _call(None, True)
            detected = (getattr(resp, "language", "") or "").lower()
            names = {_LANG_NAMES.get(c, c) for c in allowed} | set(allowed)
            if detected and detected not in names:
                resp = _call(allowed[0], False)
                calls = 2
            text = resp.text
        else:
            resp = _call(None, False)
            text = resp.text
        # whisper-1 ≈ $0.006/min。長さ不明のため概算（音声バイト数から推定）。
        minutes = max(len(audio_bytes) / (16000 * 60), 0.05)
        cost = minutes * 0.006 * calls
        from .auth import current_user_id
        with db() as conn:
            conn.execute(
                "INSERT INTO ai_usage "
                "(model, prompt_tokens, output_tokens, cost_usd, feature, "
                " user_id) VALUES ('whisper-1', 0, 0, ?, 'stt', ?)",
                (cost, current_user_id()),
            )
        return text, None
    except Exception as exc:
        log.error("STT 失敗: %s", exc)
        return None, f"文字起こしに失敗しました: {exc}"


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
            "SELECT COALESCE(SUM(cost_usd), 0) AS cost FROM ai_usage "
            "WHERE date(created_at, 'localtime') = date('now', 'localtime')"
        ).fetchone()
        recent = conn.execute(
            "SELECT model, prompt_tokens, output_tokens, cost_usd, "
            "feature, created_at FROM ai_usage ORDER BY id DESC LIMIT 10"
        ).fetchall()
    s = load_settings()
    rate = s.usd_jpy_rate
    return {
        "total_cost_usd": round(total["cost"], 4),
        "today_cost_usd": round(today["cost"], 4),
        "total_cost_jpy": round(total["cost"] * rate, 1),
        "today_cost_jpy": round(today["cost"] * rate, 1),
        "jpy_rate": rate,
        "jpy_as_of": s.usd_jpy_as_of,
        "prompt_tokens": total["ptok"],
        "output_tokens": total["otok"],
        "calls": total["calls"],
        "recent": [dict(r) for r in recent],
        "daily_cap_usd": s.ai_daily_cost_cap_usd,
        "daily_cap_jpy": round(s.ai_daily_cost_cap_usd * rate, 1),
        "cap_blocked": (
            s.ai_daily_cost_cap_usd > 0
            and today["cost"] >= s.ai_daily_cost_cap_usd
        ),
    }
