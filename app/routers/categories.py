"""Mastery-tracked categories for conversation / reading / writing / literature
and the listening topics (§4, §5, §6, §7, §9)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, HTTPException

from ..database import db
from ..schemas import CategoryStudyIn, ListeningStudyIn
from ..services.spaced_repetition import clamp

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("/{area}")
def list_categories(area: str):
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM categories WHERE area = ? ORDER BY grp, mastery ASC",
            (area,),
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("/study")
def study_category(payload: CategoryStudyIn):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM categories WHERE id = ?", (payload.category_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "カテゴリが見つかりません")
        new_mastery = clamp(row["mastery"] + payload.mastery_delta)
        conn.execute(
            "UPDATE categories SET mastery = ?, study_count = study_count + 1, "
            "last_studied = ? WHERE id = ?",
            (new_mastery, date.today().isoformat(), payload.category_id),
        )
        return {"id": payload.category_id, "mastery": new_mastery}


# --- Listening ---------------------------------------------------------------

listening = APIRouter(prefix="/api/listening", tags=["listening"])


@listening.get("")
def list_listening():
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM listening_topics ORDER BY source, accent"
        ).fetchall()
        return [dict(r) for r in rows]


@listening.post("/study")
def study_listening(payload: ListeningStudyIn):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM listening_topics WHERE id = ?", (payload.topic_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "トピックが見つかりません")
        comprehension = (
            clamp(payload.comprehension)
            if payload.comprehension is not None
            else row["comprehension"]
        )
        weak = payload.weak_areas if payload.weak_areas is not None else row["weak_areas"]
        conn.execute(
            "UPDATE listening_topics SET comprehension = ?, weak_areas = ?, "
            "study_count = study_count + 1, last_studied = ? WHERE id = ?",
            (comprehension, weak, date.today().isoformat(), payload.topic_id),
        )
        return {"id": payload.topic_id, "comprehension": comprehension}
