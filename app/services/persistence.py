"""Markdown persistence for memory.md and study_log.md.

These files hold the long-lived learner profile and the running study journal,
exactly as described in the requirements. They are plain Markdown so they stay
human-readable and easy to back up / sync (GitHub, Google Drive, ...).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from ..config import paths

DEFAULT_MEMORY = """# 学習メモリ (memory.md)

## 現在レベル
- TOEIC 550〜600程度

## 学習方針
- 英単語・英会話・リスニング・リーディング・ライティングを総合的に学習する

## 目標
- 短期目標: TOEIC 700点
- 最終目標: TOEIC 800点以上

## 苦手分野
- （学習を進めると自動で追記されます）

## 学習傾向
- （学習を進めると自動で追記されます）
"""

DEFAULT_STUDY_LOG = """# 学習履歴 (study_log.md)

学習セッションの記録がここに追記されます。
"""


def _read_or_create(path: Path, default: str) -> str:
    paths.ensure()
    if not path.exists():
        path.write_text(default, encoding="utf-8")
        return default
    return path.read_text(encoding="utf-8")


def read_memory() -> str:
    return _read_or_create(paths.memory_file, DEFAULT_MEMORY)


def write_memory(content: str) -> None:
    paths.ensure()
    paths.memory_file.write_text(content, encoding="utf-8")


def read_study_log() -> str:
    return _read_or_create(paths.study_log_file, DEFAULT_STUDY_LOG)


def append_study_log(entry: str) -> None:
    """Append a study-log entry, ensuring the file exists first."""
    current = read_study_log()
    separator = "" if current.endswith("\n") else "\n"
    paths.study_log_file.write_text(
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
