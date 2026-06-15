"""Mini-phrase (ミニフレーズ) management + quiz.

Phrases are practised exactly like words: both directions (英→日 / 日→英),
per-direction accuracy, and a forgetting-curve schedule.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..database import db
from ..services.spaced_repetition import (
    MASTERED_THRESHOLD,
    clamp,
    record_attempt,
    selection_weight,
    select_for_review,
    set_known,
)

VAGUE_BONUS = 10  # 「うろ覚え」ボタンで加点する mastery

router = APIRouter(prefix="/api/phrases", tags=["phrases"])


class PhraseCreate(BaseModel):
    english: str = Field(min_length=1)
    japanese: str = Field(min_length=1)
    scene: str = ""


class PhraseAttempt(BaseModel):
    phrase_id: int
    direction: str  # 'ja2en' | 'en2ja'
    correct: bool
    result: str | None = None  # 'correct' | 'vague' | 'wrong'


class KnownIn(BaseModel):
    known: bool = True


def _phrase_dict(row) -> dict:
    d = dict(row)
    d["selection_priority"] = selection_weight(d["mastery"])
    d["mastered"] = d["mastery"] >= MASTERED_THRESHOLD
    d["accuracy"] = (
        round(d["times_correct"] / d["times_asked"] * 100)
        if d["times_asked"]
        else None
    )
    return d


@router.get("")
def list_phrases(
    scene: str | None = None,
    sort: str = "mastery",
    include_banned: bool = False,
    mastered: str | None = None,   # 'only' | 'hide' | None(=全部)
):
    order = {
        "mastery": "mastery ASC, last_studied ASC",
        "english": "english COLLATE NOCASE ASC",
        "scene": "scene ASC, english COLLATE NOCASE ASC",
        "recent": "last_studied DESC",
        "accuracy": (
            "CASE WHEN times_asked > 0 "
            "THEN times_correct * 1.0 / times_asked ELSE -1 END DESC"
        ),
    }.get(sort, "mastery ASC, last_studied ASC")
    conds, params = [], []
    if scene:
        conds.append("scene = ?")
        params.append(scene)
    if not include_banned:
        conds.append("COALESCE(scene, '') NOT LIKE '禁止%'")
    if mastered == "only":
        conds.append(f"mastery >= {MASTERED_THRESHOLD}")
    elif mastered == "hide":
        conds.append(f"mastery < {MASTERED_THRESHOLD}")
    where = (" WHERE " + " AND ".join(conds)) if conds else ""
    with db() as conn:
        rows = conn.execute(
            f"SELECT * FROM phrases{where} ORDER BY {order}", params
        ).fetchall()
        return [_phrase_dict(r) for r in rows]


@router.get("/scenes")
def list_scenes(include_banned: bool = False):
    ban = "" if include_banned else "AND scene NOT LIKE '禁止%' "
    with db() as conn:
        rows = conn.execute(
            "SELECT DISTINCT scene FROM phrases WHERE scene <> '' "
            f"{ban}ORDER BY scene"
        ).fetchall()
        return [r["scene"] for r in rows]


@router.post("", status_code=201)
def create_phrase(payload: PhraseCreate):
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO phrases (english, japanese, scene) VALUES (?, ?, ?)",
            (payload.english, payload.japanese, payload.scene),
        )
        row = conn.execute(
            "SELECT * FROM phrases WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return _phrase_dict(row)


@router.post("/{phrase_id}/known")
def mark_known(phrase_id: int, payload: KnownIn):
    """「覚えた」ボタン: mastery を満点(200)に。known=false で解除。"""
    with db() as conn:
        exists = conn.execute(
            "SELECT id FROM phrases WHERE id = ?", (phrase_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(404, "フレーズが見つかりません")
        new = set_known(conn, phrase_id, payload.known, table="phrases")
    return {"ok": True, "mastery": new, "known": payload.known}


@router.post("/{phrase_id}/vague")
def mark_vague(phrase_id: int):
    """「うろ覚え」ボタン: mastery を +10（0..200でクランプ）。"""
    with db() as conn:
        row = conn.execute(
            "SELECT mastery FROM phrases WHERE id = ?", (phrase_id,)
        ).fetchone()
        if not row:
            raise HTTPException(404, "フレーズが見つかりません")
        new = clamp(row["mastery"] + VAGUE_BONUS)
        conn.execute(
            "UPDATE phrases SET mastery = ? WHERE id = ?", (new, phrase_id)
        )
    return {"ok": True, "mastery": new}


@router.delete("/{phrase_id}", status_code=204)
def delete_phrase(phrase_id: int):
    with db() as conn:
        cur = conn.execute("DELETE FROM phrases WHERE id = ?", (phrase_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "フレーズが見つかりません")


@router.get("/quiz")
def quiz(limit: int = 10, include_banned: bool = False):
    with db() as conn:
        rows = select_for_review(
            conn, table="phrases", limit=limit,
            exclude_banned=not include_banned,
        )
        return [_phrase_dict(r) for r in rows]


@router.post("/attempt")
def attempt(payload: PhraseAttempt):
    with db() as conn:
        try:
            result = record_attempt(
                conn,
                payload.phrase_id,
                payload.direction,
                payload.correct,
                result=payload.result,
                table="phrases",
                attempts_table="phrase_attempts",
                id_column="phrase_id",
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc))
        return result
