"""Vocabulary management + quiz endpoints (§3 of the requirements)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from ..database import db
from ..schemas import AttemptIn, WordCreate, WordUpdate
from ..services.spaced_repetition import pick_weighted, record_attempt, selection_weight

router = APIRouter(prefix="/api/words", tags=["vocabulary"])


def _word_dict(row) -> dict:
    d = dict(row)
    d["selection_priority"] = selection_weight(d["mastery"])
    accuracy = (
        round(d["times_correct"] / d["times_asked"] * 100)
        if d["times_asked"]
        else None
    )
    d["accuracy"] = accuracy
    return d


@router.get("")
def list_words(sort: str = "mastery"):
    order = {
        "mastery": "mastery ASC, last_studied ASC",
        "english": "english COLLATE NOCASE ASC",
        "recent": "last_studied DESC",
    }.get(sort, "mastery ASC")
    with db() as conn:
        rows = conn.execute(f"SELECT * FROM words ORDER BY {order}").fetchall()
        return [_word_dict(r) for r in rows]


@router.post("", status_code=201)
def create_word(payload: WordCreate):
    with db() as conn:
        cur = conn.execute(
            "INSERT INTO words (english, japanese, part_of_speech, example) "
            "VALUES (?, ?, ?, ?)",
            (payload.english, payload.japanese, payload.part_of_speech, payload.example),
        )
        row = conn.execute(
            "SELECT * FROM words WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return _word_dict(row)


@router.put("/{word_id}")
def update_word(word_id: int, payload: WordUpdate):
    fields = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not fields:
        raise HTTPException(400, "更新する項目がありません")
    sets = ", ".join(f"{k} = ?" for k in fields)
    with db() as conn:
        cur = conn.execute(
            f"UPDATE words SET {sets} WHERE id = ?",
            (*fields.values(), word_id),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "単語が見つかりません")
        row = conn.execute("SELECT * FROM words WHERE id = ?", (word_id,)).fetchone()
        return _word_dict(row)


@router.delete("/{word_id}", status_code=204)
def delete_word(word_id: int):
    with db() as conn:
        cur = conn.execute("DELETE FROM words WHERE id = ?", (word_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "単語が見つかりません")


@router.get("/quiz")
def quiz(limit: int = 10):
    """Return a weighted set of words to quiz (probability ∝ 100 - mastery)."""
    with db() as conn:
        rows = pick_weighted(conn, limit=limit)
        return [_word_dict(r) for r in rows]


@router.post("/attempt")
def attempt(payload: AttemptIn):
    with db() as conn:
        try:
            result = record_attempt(
                conn, payload.word_id, payload.direction, payload.correct
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc))
        return result


@router.get("/stats")
def stats():
    from ..services.metrics import toeic_estimate, word_buckets

    with db() as conn:
        b = word_buckets(conn, "words")
    b["toeic_estimate"] = toeic_estimate(
        b["avg_mastery"], b["mastered"], b["total"]
    )
    return b
