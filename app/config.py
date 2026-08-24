"""Application configuration and cross-platform path handling.

All file-system paths go through :data:`paths` so the app behaves the same
on Windows and macOS (uses ``pathlib`` everywhere, no hard-coded separators).
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# アプリのバージョン（UI表示用）。バージョンを上げたら CHANGELOG.md に追記し、
# 必ず git commit + push をセットで行うこと（CLAUDE.md参照）。
APP_VERSION = "ver1.2.18"

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
    stt_model: str      # 音声認識(文字起こし)モデル
    quality_model: str  # 判定・教材生成など品質重視の処理に使うモデル
    conversation_model: str  # 英会話専用モデル（速度重視・2026-08-22新設）
    usd_jpy_rate: float
    usd_jpy_as_of: str
    # コスト暴走ガード（不意の高額課金を防ぐ）。.env で調整可能。
    ai_daily_cost_cap_usd: float   # 1日の合計AI費用の上限(USD)。超過で停止。
    ai_max_calls_per_min: int      # 1分あたりのAI呼び出し回数の上限。
    ai_max_output_tokens: int      # chat の max_tokens 上限（過大指定を抑制）。
    audio_storage: str             # 'file' | 'db' | 'hybrid'。MP3保存先の方式。
    balance_markup: float          # 枠外利用の残高控除倍率(原価×為替×この値)。
    # 個別上限未設定時の既定無料枠(円/日)。legacy/charged専用(email tierは0円)。
    ai_daily_free_jpy: float

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
# 枠外利用時の残高控除倍率（原価×為替×この値）。2026-08-08: 1.5→2.0に変更
# （粗利率33%→50%）。docs/COST_ESTIMATE.md §6参照。
DEFAULT_BALANCE_MARKUP = 2.0
# 個別上限未設定時の既定無料枠(円/日)。2026-08-08決定: legacy/charged
# ユーザーのみ適用（¥150/日）。email tier(自己サインアップ・未課金)は
# ai.py側で強制的に0円（無料枠なし・残高必須）とする。
DEFAULT_AI_DAILY_FREE_JPY = 150.0


def load_settings() -> Settings:
    """Read settings fresh from env (so a saved .env takes effect)."""
    load_dotenv(ROOT_DIR / ".env", override=True)
    model = os.getenv("OPENAI_MODEL", "gpt-5.4-mini").strip()
    host = os.getenv("HOST", "127.0.0.1").strip()
    tts = os.getenv("OPENAI_TTS_MODEL", "gpt-4o-mini-tts").strip()
    stt = os.getenv("OPENAI_STT_MODEL", "whisper-1").strip()
    # 品質重視の処理用。未設定なら通常モデルにフォールバック。
    quality = os.getenv("OPENAI_QUALITY_MODEL", "").strip()
    # 英会話専用（速度重視）。未設定なら通常モデルにフォールバック
    # （2026-08-22: ベンチマークの結果gpt-4o-miniがgpt-5.6-lunaより
    # 速く安いと判明したため新設。当面は管理者のみに適用し様子を見る
    # 方針、`app/routers/learn.py`の`_conversation_model()`参照）。
    conversation = os.getenv("OPENAI_CONVERSATION_MODEL", "").strip()
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
    markup = _parse_float(
        os.getenv("BALANCE_MARKUP", ""), DEFAULT_BALANCE_MARKUP
    )
    daily_free_jpy = _parse_float(
        os.getenv("AI_DAILY_FREE_JPY", ""), DEFAULT_AI_DAILY_FREE_JPY
    )
    return Settings(
        openai_api_key=os.getenv("OPENAI_API_KEY", "").strip(),
        openai_model=model or "gpt-5.4-mini",
        host=host or "127.0.0.1",
        port=int(os.getenv("PORT", "8000")),
        nickname=os.getenv("USER_NICKNAME", "").strip(),
        tts_model=tts or "gpt-4o-mini-tts",
        stt_model=stt or "whisper-1",
        quality_model=quality or (model or "gpt-5.4-mini"),
        conversation_model=conversation or (model or "gpt-5.4-mini"),
        usd_jpy_rate=rate,
        usd_jpy_as_of=as_of,
        ai_daily_cost_cap_usd=max(0.0, cap),
        ai_max_calls_per_min=max(1, cpm),
        ai_max_output_tokens=max(64, maxout),
        audio_storage=storage,
        balance_markup=max(1.0, markup),
        ai_daily_free_jpy=max(0.0, daily_free_jpy),
    )


settings = load_settings()


def load_admin_known_ips() -> set[str]:
    """管理者自身の既知ログイン元IP(.envのADMIN_KNOWN_IPS・カンマ区切り)。
    管理画面の利用状況分析で「これは管理者自身のアクセス」と識別する
    参考情報として使う(2026-08-18)。"""
    load_dotenv(ROOT_DIR / ".env", override=True)
    raw = os.getenv("ADMIN_KNOWN_IPS", "")
    return {ip.strip() for ip in raw.split(",") if ip.strip()}


def load_tokushoho_info() -> dict[str, str]:
    """特定商取引法ページ用の個人情報。.env にのみ記載する(コードに書かない)。
    空欄のフィールドは呼び出し側で「[要記入]」表示にフォールバックする。"""
    load_dotenv(ROOT_DIR / ".env", override=True)
    return {
        "name": os.getenv("TOKUSHOHO_NAME", "").strip(),
        "supervisor": os.getenv("TOKUSHOHO_SUPERVISOR", "").strip(),
        "address": os.getenv("TOKUSHOHO_ADDRESS", "").strip(),
        "phone": os.getenv("TOKUSHOHO_PHONE", "").strip(),
        "email": os.getenv("TOKUSHOHO_EMAIL", "").strip(),
    }


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
    # 100ユーザー規模で3ヶ月保持を狙って10MB×15世代(最大150MB)に拡張
    # (2026-08-19・旧1MB×3世代=最大4MBでは突発的なエラー多発時に不足しうる)。
    fh = RotatingFileHandler(
        paths.data_dir / "app.log",
        maxBytes=10_000_000, backupCount=15, encoding="utf-8",
    )
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    logger.addHandler(fh)
    logger.addHandler(sh)
    logger.propagate = False
    return logger


log = setup_logging()
