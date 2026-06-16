"""Markdown persistence for memory.md and study_log.md.

These files hold the long-lived learner profile and the running study journal,
exactly as described in the requirements. They are plain Markdown so they stay
human-readable and easy to back up / sync (GitHub, Google Drive, ...).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from ..config import paths

# 新規ユーザーの memory は空テンプレート（各自が設定画面の入力欄で記入）。
# 旧版は yutakatsu 固有(TOEIC550等)だったため、共通の空欄に変更。
DEFAULT_MEMORY = """# 学習メモリ (memory.md)

## 学習方針

## 目標

## 苦手分野

## 学習傾向
"""

DEFAULT_STUDY_LOG = """# 学習履歴 (study_log.md)

学習セッションの記録がここに追記されます。
"""


def _user_dir() -> Path:
    """現在ユーザーの専用ディレクトリ data/users/<uid>/（per-user 化）。"""
    from .auth import current_user_id
    d = paths.data_dir / "users" / str(current_user_id())
    d.mkdir(parents=True, exist_ok=True)
    return d


def _memory_path() -> Path:
    return _user_dir() / "memory.md"


def _study_log_path() -> Path:
    return _user_dir() / "study_log.md"


def _read_or_create(path: Path, default: str) -> str:
    if not path.exists():
        path.write_text(default, encoding="utf-8")
        return default
    return path.read_text(encoding="utf-8")


def read_memory() -> str:
    return _read_or_create(_memory_path(), DEFAULT_MEMORY)


def write_memory(content: str) -> None:
    _memory_path().write_text(content, encoding="utf-8")


def read_study_log() -> str:
    return _read_or_create(_study_log_path(), DEFAULT_STUDY_LOG)


def append_study_log(entry: str) -> None:
    """Append a study-log entry (per-user), ensuring the file exists first."""
    current = read_study_log()
    separator = "" if current.endswith("\n") else "\n"
    _study_log_path().write_text(
        f"{current}{separator}\n{entry.rstrip()}\n", encoding="utf-8"
    )


def format_session_entry(
    *,
    content: str,
    accuracy: int | None,
    weak_points: str,
    next_topic: str,
    new_words: str = "",
    study_date: str | None = None,
) -> str:
    """Render a study-session record as the Markdown block from the spec."""
    d = study_date or date.today().isoformat()
    acc = f"{accuracy}%" if accuracy is not None else "—"
    lines = [
        f"## {d}",
        "",
        "### 学習内容",
        content.strip() or "- （記録なし）",
        "",
        f"### 正答率\n- {acc}",
        "",
        "### 苦手",
        weak_points.strip() or "- （特になし）",
    ]
    if new_words.strip():
        lines += ["", "### 新出単語", new_words.strip()]
    lines += ["", "### 次回", next_topic.strip() or "- （未定）"]
    return "\n".join(lines)
