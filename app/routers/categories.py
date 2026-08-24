"""Mastery-tracked categories for conversation / reading / writing / literature
and the listening topics (§4, §5, §6, §7, §9)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter

from ..services import errors

from ..database import db
from ..schemas import CategoryStudyIn, ListeningStudyIn
from ..services.auth import current_user_id
from ..services.spaced_repetition import clamp

router = APIRouter(prefix="/api/categories", tags=["categories"])

# 2026-08-08: mastery/study_count/last_studied は元々 categories/
# listening_topics の列に直書きで、全ユーザー共有になっていた（他人の学習
# 進捗と混ざるバグ）。カテゴリ・トピック自体(area/grp/name/source/accent)は
# 共有のまま、進捗だけ user_category_progress/user_listening_progress に
# 分離し、per-user の COALESCE 既定値(0/空)で返す。


@router.get("/{area}")
def list_categories(area: str):
    uid = current_user_id()
    with db() as conn:
        rows = conn.execute(
            "SELECT c.id, c.area, c.grp, c.name, "
            "COALESCE(ucp.mastery, 0) AS mastery, "
            "ucp.last_studied AS last_studied, "
            "COALESCE(ucp.study_count, 0) AS study_count "
            "FROM categories c LEFT JOIN user_category_progress ucp "
            "ON ucp.category_id = c.id AND ucp.user_id = ? "
            "WHERE c.area = ? ORDER BY c.grp, mastery ASC",
            (uid, area),
        ).fetchall()
        return [dict(r) for r in rows]


@router.post("/study")
def study_category(payload: CategoryStudyIn):
    uid = current_user_id()
    with db() as conn:
        cat = conn.execute(
            "SELECT id FROM categories WHERE id = ?", (payload.category_id,)
        ).fetchone()
        if not cat:
            raise errors.http_error("7001", "カテゴリが見つかりません")
        cur = conn.execute(
            "SELECT mastery FROM user_category_progress "
            "WHERE user_id = ? AND category_id = ?",
            (uid, payload.category_id),
        ).fetchone()
        new_mastery = clamp((cur["mastery"] if cur else 0)
                             + payload.mastery_delta)
        conn.execute(
            "INSERT INTO user_category_progress "
            "(user_id, category_id, mastery, last_studied, study_count) "
            "VALUES (?, ?, ?, ?, 1) "
            "ON CONFLICT(user_id, category_id) DO UPDATE SET "
            "mastery=excluded.mastery, last_studied=excluded.last_studied, "
            "study_count=user_category_progress.study_count + 1",
            (uid, payload.category_id, new_mastery, date.today().isoformat()),
        )
        return {"id": payload.category_id, "mastery": new_mastery}


# --- Listening ---------------------------------------------------------------

listening = APIRouter(prefix="/api/listening", tags=["listening"])


@listening.get("")
def list_listening():
    uid = current_user_id()
    with db() as conn:
        rows = conn.execute(
            "SELECT lt.id, lt.source, lt.accent, "
            "COALESCE(ulp.comprehension, 0) AS comprehension, "
            "COALESCE(ulp.weak_areas, '') AS weak_areas, "
            "COALESCE(ulp.study_count, 0) AS study_count, "
            "ulp.last_studied AS last_studied "
            "FROM listening_topics lt LEFT JOIN user_listening_progress ulp "
            "ON ulp.topic_id = lt.id AND ulp.user_id = ? "
            "ORDER BY lt.source, lt.accent",
            (uid,),
        ).fetchall()
        return [dict(r) for r in rows]


@listening.post("/study")
def study_listening(payload: ListeningStudyIn):
    uid = current_user_id()
    with db() as conn:
        topic = conn.execute(
            "SELECT id FROM listening_topics WHERE id = ?",
            (payload.topic_id,),
        ).fetchone()
        if not topic:
            raise errors.http_error("7001", "トピックが見つかりません")
        cur = conn.execute(
            "SELECT comprehension, weak_areas FROM user_listening_progress "
            "WHERE user_id = ? AND topic_id = ?",
            (uid, payload.topic_id),
        ).fetchone()
        comprehension = (
            clamp(payload.comprehension)
            if payload.comprehension is not None
            else (cur["comprehension"] if cur else 0)
        )
        weak = (
            payload.weak_areas if payload.weak_areas is not None
            else (cur["weak_areas"] if cur else "")
        )
        conn.execute(
            "INSERT INTO user_listening_progress "
            "(user_id, topic_id, comprehension, weak_areas, last_studied, "
            "study_count) VALUES (?, ?, ?, ?, ?, 1) "
            "ON CONFLICT(user_id, topic_id) DO UPDATE SET "
            "comprehension=excluded.comprehension, "
            "weak_areas=excluded.weak_areas, "
            "last_studied=excluded.last_studied, "
            "study_count=user_listening_progress.study_count + 1",
            (uid, payload.topic_id, comprehension, weak,
             date.today().isoformat()),
        )
        return {"id": payload.topic_id, "comprehension": comprehension}
