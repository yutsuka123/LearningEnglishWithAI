"""Application configuration and cross-platform path handling.

All file-system paths go through :data:`paths` so the app behaves the same
on Windows and macOS (uses ``pathlib`` everywhere, no hard-coded separators).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# アプリのバージョン（UI表示用）。
APP_VERSION = "ver1.1.0-alpha02"

# Project root = the directory that contains the "app" package.
ROOT_DIR = Path(__file__).resolve().parent.parent

# Load .env from the project root if present (no error if missing).
load_dotenv(ROOT_DIR / ".env")


@dataclass(frozen=True)
class Paths:
    """Resolved, absolute paths used across the app."""

    root: Path
    data_dir: Path
    db_file: Path
    memory_file: Path
    study_log_file: Path
    static_dir: Path

    def ensure(self) -> None:
        """Create the data directory if it does not yet exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)


def _resolve_data_dir() -> Path:
    custom = os.getenv("DATA_DIR")
    if custom:
        return Path(custom).expanduser().resolve()
    return ROOT_DIR / "data"


_data_dir = _resolve_data_dir()

paths = Paths(
    root=ROOT_DIR,
    data_dir=_data_dir,
    db_file=_data_dir / "vocabulary.db",
    memory_file=_data_dir / "memory.md",
    study_log_file=_data_dir / "study_log.md",
    static_dir=ROOT_DIR / "static",
)


@dataclass(frozen=True)
class Settings:
    """Runtime settings, mostly sourced from environment variables."""

    openai_api_key: str
    openai_model: str
    host: str
    port: int
    nickname: str
    tts_model: str
    quality_model: str  # 判定・教材生成など品質重視の処理に使うモデル
    usd_jpy_rate: float
    usd_jpy_as_of: str
    # コスト暴走ガード（不意の高額課金を防ぐ）。.env で調整可能。
    ai_daily_cost_cap_usd: float   # 1日の合計AI費用の上限(USD)。超過で停止。
    ai_max_calls_per_min: int      # 1分あたりのAI呼び出し回数の上限。
    ai_max_output_tokens: int      # chat の max_tokens 上限（過大指定を抑制）。
    audio_storage: str             # 'file' | 'db' | 'hybrid'。MP3保存先の方式。

    @property
    def ai_enabled(self) -> bool:
        return bool(self.openai_api_key.strip())


# USD→JPY 為替レート（費用の円換算用）。週1回見直し、.env で更新可能。
# 既定は 2026-06-14 時点の概算値。
DEFAULT_USD_JPY = 155.0
DEFAULT_USD_JPY_AS_OF = "2026-06-14"


def _parse_float(value: str, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _parse_int(value: str, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# コスト暴走ガードの既定値（保守的）。.env で上書き可能。
DEFAULT_DAILY_COST_CAP_USD = 1.0   # 1日 約¥155 まで
DEFAULT_MAX_CALLS_PER_MIN = 20
DEFAULT_MAX_OUTPUT_TOKENS = 1500


def load_settings() -> Settings:
    """Read settings fresh from env (so a saved .env takes effect)."""
    load_dotenv(ROOT_DIR / ".env", override=True)
    model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini").strip()
    host = os.getenv("HOST", "127.0.0.1").strip()
    tts = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts").strip()
    # 品質重視の処理用。未設定なら通常モデルにフォールバック。
    quality = os.getenv("OPENAI_QUALITY_MODEL", "").strip()
    rate = _parse_float(os.getenv("USD_JPY_RATE", ""), DEFAULT_USD_JPY)
    as_of = os.getenv("USD_JPY_AS_OF", "").strip() or DEFAULT_USD_JPY_AS_OF
    cap = _parse_float(
        os.getenv("AI_DAILY_COST_CAP_USD", ""), DEFAULT_DAILY_COST_CAP_USD
    )
    cpm = _parse_int(
        os.getenv("AI_MAX_CALLS_PER_MIN", ""), DEFAULT_MAX_CALLS_PER_MIN
    )
    maxout = _parse_int(
        os.getenv("AI_MAX_OUTPUT_TOKENS", ""), DEFAULT_MAX_OUTPUT_TOKENS
    )
    storage = os.getenv("AUDIO_STORAGE", "file").strip().lower()
    if storage not in ("file", "db", "hybrid"):
        storage = "file"
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_model=model or "gpt-5.4-mini",
        host=host or "127.0.0.1",
        port=int(os.getenv("PORT", "8000")),
        nickname=os.getenv("USER_NICKNAME", "").strip(),
        tts_model=tts or "gpt-4o-mini-tts",
        quality_model=quality or (model or "gpt-5.4-mini"),
        usd_jpy_rate=rate,
        usd_jpy_as_of=as_of,
        ai_daily_cost_cap_usd=max(0.0, cap),
        ai_max_calls_per_min=max(1, cpm),
        ai_max_output_tokens=max(64, maxout),
        audio_storage=storage,
    )


settings = load_settings()


# ---------------------------------------------------------------------------
# Logging (file + console). Errors are written to data/app.log.
# ---------------------------------------------------------------------------

import logging  # noqa: E402
from logging.handlers import RotatingFileHandler  # noqa: E402


def setup_logging() -> logging.Logger:
    paths.ensure()
    logger = logging.getLogger("ela")
    if logger.handlers:  # already configured
        return logger
    logger.setLevel(logging.INFO)
    fmt = logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    fh = RotatingFileHandler(
        paths.data_dir / "app.log",
        maxBytes=1_000_000, backupCount=3, encoding="utf-8",
    )
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    logger.propagate = False
    return logger


log = setup_logging()
