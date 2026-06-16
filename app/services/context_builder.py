"""Builds the compact context handed to the AI on every request.

Per the requirements (§13), we never send the whole chat history. Instead we
assemble a small snapshot from our own persisted state:

* 現在レベル / 学習目標  (from memory.md)
* 苦手分野              (from memory.md + recent sessions)
* 最近の学習履歴        (last few study_sessions)
* 今日の復習対象        (low-mastery words due for review)
"""

from __future__ import annotations

from datetime import date

from ..config import load_settings
from ..database import db
from . import persistence
from .spaced_repetition import pick_weighted


def review_words_today(limit: int = 10) -> list[dict]:
    from .auth import current_user_id
    with db() as conn:
        rows = pick_weighted(conn, limit=limit, user_id=current_user_id())
        return [
            {
                "id": r["id"],
                "english": r["english"],
                "japanese": r["japanese"],
                "mastery": r["mastery"],
            }
            for r in rows
        ]


def recent_sessions(limit: int = 5) -> list[dict]:
    from .auth import current_user_id
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM study_sessions WHERE user_id = ? "
            "ORDER BY id DESC LIMIT ?", (current_user_id(), limit)
        ).fetchall()
        return [dict(r) for r in rows]


def build_context() -> str:
    """Return a Markdown snapshot suitable for prepending to an AI prompt."""
    from .auth import current_user_id, get_user_settings
    memory = persistence.read_memory()
    sessions = recent_sessions()
    review = review_words_today()
    with db() as conn:
        us = get_user_settings(conn, current_user_id())
    nickname = (us.get("nickname") or "").strip() or load_settings().nickname

    lines = [
        "# 学習者コンテキスト",
        f"日付: {date.today().isoformat()}",
        f"呼びかけ名: {nickname}" if nickname else "",
        "",
        "## メモリ (現在レベル・目標・苦手・傾向)",
        memory.strip(),
        "",
        "## 今日の復習対象 (習熟度の低い単語)",
    ]
    if review:
        for w in review:
            lines.append(
                f"- {w['english']} / {w['japanese']} (習熟度 {w['mastery']})"
            )
    else:
        lines.append("- （登録単語がありません）")

    lines += ["", "## 最近の学習履歴"]
    if sessions:
        for s in sessions:
            acc = f"{s['accuracy']}%" if s["accuracy"] is not None else "—"
            lines.append(
                f"- {s['study_date']}: {s['content'][:60]} "
                f"(正答率 {acc}, 苦手: {s['weak_points'][:40]})"
            )
    else:
        lines.append("- （まだ記録がありません）")

    return "\n".join(lines)
