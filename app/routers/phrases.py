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
from .vocabulary import LEVEL_ORDER, OUT_OF_RANGE, _level_range

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
    desc: bool = False,            # 降順にするか（昇順/降順トグル）
    level_min: str | None = None,
    level_max: str | None = None,
    out_of_range: bool = False,
    include_banned: bool = False,
    mastered: str | None = None,   # 'only' | 'hide' | None(=全部)
):
    col = {
        "mastery": "mastery",
        "english": "english COLLATE NOCASE",
        "scene": "scene",
        "recent": "last_studied",
        "accuracy": (
            "CASE WHEN times_asked > 0 "
            "THEN times_correct * 1.0 / times_asked ELSE -1 END"
        ),
    }.get(sort, "mastery")
    direction = "DESC" if desc else "ASC"
    order = f"{col} {direction}, english COLLATE NOCASE ASC"
    conds, params = [], []
    if scene:
        conds.append("scene = ?")
        params.append(scene)
    if level_min or level_max:
        allowed = _level_range(level_min, level_max)
        ph = ",".join("?" * len(allowed))
        cond = f"COALESCE(level, '') IN ({ph})"
        p = list(allowed)
        if out_of_range:
            cond = f"({cond} OR COALESCE(level, '') = ?)"
            p.append(OUT_OF_RANGE)
        conds.append(cond)
        params += p
    if not include_banned:
        if out_of_range:
            conds.append(
                "(COALESCE(scene, '') NOT LIKE '禁止%' "
                "OR COALESCE(level, '') = ?)")
            params.append(OUT_OF_RANGE)
        else:
            conds.append("COALESCE(scene, '') NOT LIKE '禁止%'")
    if mastered == "only":
        conds.append(f"mastery >= {MASTERED_THRESHOLD}")
    elif mastered == "hide":
        conds.append(f"mastery < {MASTERED_THRESHOLD}")
    where = (" WHERE " + " AND ".join(conds)) if conds else ""
    from ..services.auth import current_user_id
    from ..services.progress import user_items_subquery
    src = user_items_subquery("phrases")  # 先頭 ? = user_id
    with db() as conn:
        rows = conn.execute(
            f"SELECT * FROM {src} AS phrases{where} ORDER BY {order}",
            [current_user_id(), *params],
        ).fetchall()
        return [_phrase_dict(r) for r in rows]


@router.get("/facets")
def facets():
    """フィルタUI用: レベル範囲の選択肢（細スケール順・範囲外を除く）。"""
    with db() as conn:
        present = {
            r["level"] for r in conn.execute(
                "SELECT DISTINCT level FROM phrases WHERE COALESCE(level,'')<>''"
            ).fetchall()
        }
    return {"range_levels": [lv for lv in LEVEL_ORDER if lv in present]}


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
    """「覚えた」ボタン(per-user): mastery を満点(200)に。known=false で解除。"""
    from ..services.auth import current_user_id
    with db() as conn:
        exists = conn.execute(
            "SELECT id FROM phrases WHERE id = ?", (phrase_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(404, "フレーズが見つかりません")
        new = set_known(conn, phrase_id, payload.known, table="phrases",
                        user_id=current_user_id())
    return {"ok": True, "mastery": new, "known": payload.known}


@router.post("/{phrase_id}/vague")
def mark_vague(phrase_id: int):
    """「うろ覚え」ボタン(per-user): mastery を +10（0..200でクランプ）。"""
    from ..services.auth import current_user_id
    from ..services import progress as P
    with db() as conn:
        exists = conn.execute(
            "SELECT id FROM phrases WHERE id = ?", (phrase_id,)
        ).fetchone()
        if not exists:
            raise HTTPException(404, "フレーズが見つかりません")
        uid = current_user_id()
        cur = P.get_progress(conn, uid, "phrases", phrase_id)
        new = clamp(cur["mastery"] + VAGUE_BONUS)
        P.upsert_progress(conn, uid, "phrases", phrase_id, mastery=new)
    return {"ok": True, "mastery": new}


@router.delete("/{phrase_id}", status_code=204)
def delete_phrase(phrase_id: int):
    with db() as conn:
        cur = conn.execute("DELETE FROM phrases WHERE id = ?", (phrase_id,))
        if cur.rowcount == 0:
            raise HTTPException(404, "フレーズが見つかりません")


@router.get("/quiz")
def quiz(limit: int = 10, include_banned: bool = False):
    from ..services.auth import current_user_id
    with db() as conn:
        rows = select_for_review(
            conn, table="phrases", limit=limit,
            exclude_banned=not include_banned, user_id=current_user_id(),
        )
        return [_phrase_dict(r) for r in rows]


@router.post("/attempt")
def attempt(payload: PhraseAttempt):
    from ..services.auth import current_user_id
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
                user_id=current_user_id(),
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc))
        return result
