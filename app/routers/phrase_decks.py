"""フレーズ帳(デッキ)機能。`decks.py`(単語帳)のフレーズ版で、構造は完全に
並行(scene/レベル(複数可)や手動選択で自分用のフレーズセットを作り、デッキ別
設定で学習)。進捗はデッキ別(phrase_deck_progress)に保持。

2026-08-09: 無料(ログインのみ)ユーザーはフレーズ帳1個・100件までに制限し、
課金ユーザー(または管理者)は無制限にする（`_enforce_free_tier_limits`）。
一覧閲覧・学習・削除・設定変更に階層制限は無く、**新規作成**時のみ適用する。
"""

from __future__ import annotations

import json
import random

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import db
from ..services import auth
from ..services.auth import current_user_id
from ..services.spaced_repetition import (
    MASTERED_THRESHOLD,
    banned_filter,
    record_attempt,
)

router = APIRouter(prefix="/api/phrase-decks", tags=["phrase_decks"])


FREE_MAX_DECKS = 1
FREE_MAX_ITEMS = 100


def _enforce_free_tier_limits(
    conn, p: "PhraseDeckCreate"
) -> "PhraseDeckCreate":
    """無料(ログインのみ)ユーザーはフレーズ帳1個・100件までに制限する。
    課金ユーザー・管理者は無制限（新規作成時のみチェック）。"""
    if auth.is_charged_or_admin(conn, current_user_id()):
        return p
    existing = conn.execute(
        "SELECT COUNT(*) c FROM phrase_decks WHERE user_id = ?",
        (current_user_id(),),
    ).fetchone()["c"]
    if existing >= FREE_MAX_DECKS:
        raise HTTPException(
            403, f"無料範囲ではフレーズ帳は{FREE_MAX_DECKS}個までです。"
            "追加で作るには設定画面からチャージしてください。",
        )
    if p.phrase_ids:
        p.phrase_ids = p.phrase_ids[:FREE_MAX_ITEMS]
    else:
        p.limit = min(p.limit, FREE_MAX_ITEMS) if p.limit else FREE_MAX_ITEMS
    return p


def _owned_deck(conn, deck_id: int):
    """現在ユーザーが所有するフレーズ帳行を返す（無ければ404）。"""
    row = conn.execute(
        "SELECT * FROM phrase_decks WHERE id = ? AND user_id = ?",
        (deck_id, current_user_id()),
    ).fetchone()
    if not row:
        raise HTTPException(404, "フレーズ帳が見つかりません")
    return row


DEFAULT_SETTINGS = {
    "directions": "both",   # 'both' | 'en2ja' | 'ja2en'
    "pass_count": 2,        # N回正解で「習得(done)」
    "use_srs": True,        # 忘却曲線(グローバルmastery/SRS)も更新するか
    "quiz_size": 10,
}


def _settings(raw: str | None) -> dict:
    out = dict(DEFAULT_SETTINGS)
    try:
        out.update(json.loads(raw or "{}"))
    except (json.JSONDecodeError, TypeError):
        pass
    return out


def _deck_summary(conn, row) -> dict:
    total = conn.execute(
        "SELECT COUNT(*) c FROM deck_phrases WHERE deck_id = ?", (row["id"],)
    ).fetchone()["c"]
    done = conn.execute(
        "SELECT COUNT(*) c FROM phrase_deck_progress "
        "WHERE deck_id = ? AND done_at IS NOT NULL", (row["id"],)
    ).fetchone()["c"]
    # 達成率はダッシュボード等と同じグローバルmastery基準
    # (mastery>=MASTERED_THRESHOLD)に統一する。`done`(デッキ内N回正解)は
    # デッキ内クイズの優先出題に引き続き使うため別途保持する。
    mastered = conn.execute(
        "SELECT COUNT(*) c FROM deck_phrases dp "
        "JOIN user_phrase_progress p ON p.phrase_id = dp.phrase_id "
        "  AND p.user_id = (SELECT user_id FROM phrase_decks WHERE id = ?) "
        "WHERE dp.deck_id = ? AND p.mastery >= ?",
        (row["id"], row["id"], MASTERED_THRESHOLD),
    ).fetchone()["c"]
    return {
        "id": row["id"],
        "name": row["name"],
        "settings": _settings(row["settings"]),
        "total": total,
        "done": done,
        "mastered": mastered,
        "created_at": row["created_at"],
    }


def _overall_summary(conn) -> dict:
    uid = current_user_id()
    row = conn.execute(
        "SELECT COUNT(DISTINCT dp.phrase_id) AS total, "
        "SUM(CASE WHEN COALESCE(p.mastery, 0) >= ? THEN 1 ELSE 0 END) "
        "  AS mastered "
        "FROM phrase_decks d JOIN deck_phrases dp ON dp.deck_id = d.id "
        "LEFT JOIN user_phrase_progress p "
        "  ON p.phrase_id = dp.phrase_id AND p.user_id = d.user_id "
        "WHERE d.user_id = ?",
        (MASTERED_THRESHOLD, uid),
    ).fetchone()
    total = row["total"] or 0
    mastered = row["mastered"] or 0
    deck_count = conn.execute(
        "SELECT COUNT(*) c FROM phrase_decks WHERE user_id = ?", (uid,)
    ).fetchone()["c"]
    return {
        "deck_count": deck_count,
        "total": total,
        "mastered": mastered,
        "pct": round(mastered / total * 100) if total else 0,
    }


class PhraseDeckCreate(BaseModel):
    name: str
    settings: dict = {}
    # 抽出条件（お任せ/フィルタ作成）。phrase_ids 指定なら手動。
    scenes: list[str] = []
    levels: list[str] = []
    include_banned: bool = False
    limit: int | None = None     # お任せ時の最大件数（Noneで全件）
    phrase_ids: list[int] = []


def _select_phrase_ids(conn, p: PhraseDeckCreate) -> list[int]:
    if p.phrase_ids:
        return list(dict.fromkeys(p.phrase_ids))
    from ..services.auth import current_user_allow_banned
    include_banned = p.include_banned and current_user_allow_banned()
    where, params = [], []
    if p.scenes:
        ph = ",".join("?" * len(p.scenes))
        where.append(f"COALESCE(scene,'') IN ({ph})")
        params += p.scenes
    if p.levels:
        ph = ",".join("?" * len(p.levels))
        where.append(f"COALESCE(level,'') IN ({ph})")
        params += p.levels
    if not include_banned:
        where.append(banned_filter("phrases"))
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    rows = conn.execute(
        f"SELECT id FROM phrases{clause}", params
    ).fetchall()
    ids = [r["id"] for r in rows]
    if p.limit and p.limit < len(ids):
        ids = random.sample(ids, p.limit)
    return ids


@router.get("")
def list_decks():
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM phrase_decks WHERE user_id = ? "
            "ORDER BY created_at DESC",
            (current_user_id(),),
        ).fetchall()
        return [_deck_summary(conn, r) for r in rows]


@router.get("/summary")
def deck_overall_summary():
    with db() as conn:
        return _overall_summary(conn)


@router.post("", status_code=201)
def create_deck(payload: PhraseDeckCreate):
    settings = dict(DEFAULT_SETTINGS)
    settings.update(payload.settings or {})
    with db() as conn:
        payload = _enforce_free_tier_limits(conn, payload)
        ids = _select_phrase_ids(conn, payload)
        cur = conn.execute(
            "INSERT INTO phrase_decks (name, settings, user_id) "
            "VALUES (?, ?, ?)",
            (payload.name.strip() or "新しいフレーズ帳", json.dumps(settings),
             current_user_id()),
        )
        deck_id = cur.lastrowid
        conn.executemany(
            "INSERT OR IGNORE INTO deck_phrases (deck_id, phrase_id) "
            "VALUES (?, ?)",
            [(deck_id, pid) for pid in ids],
        )
        row = conn.execute(
            "SELECT * FROM phrase_decks WHERE id = ?", (deck_id,)
        ).fetchone()
        return _deck_summary(conn, row)


@router.get("/{deck_id}")
def get_deck(deck_id: int):
    with db() as conn:
        return _deck_summary(conn, _owned_deck(conn, deck_id))


class PhraseDeckUpdate(BaseModel):
    name: str | None = None
    settings: dict | None = None


@router.put("/{deck_id}")
def update_deck(deck_id: int, payload: PhraseDeckUpdate):
    with db() as conn:
        row = _owned_deck(conn, deck_id)
        name = payload.name if payload.name is not None else row["name"]
        settings = _settings(row["settings"])
        if payload.settings is not None:
            settings.update(payload.settings)
        conn.execute(
            "UPDATE phrase_decks SET name = ?, settings = ? WHERE id = ?",
            (name, json.dumps(settings), deck_id),
        )
        row = conn.execute(
            "SELECT * FROM phrase_decks WHERE id = ?", (deck_id,)
        ).fetchone()
        return _deck_summary(conn, row)


@router.delete("/{deck_id}", status_code=204)
def delete_deck(deck_id: int):
    with db() as conn:
        cur = conn.execute(
            "DELETE FROM phrase_decks WHERE id = ? AND user_id = ?",
            (deck_id, current_user_id()),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "フレーズ帳が見つかりません")


@router.get("/{deck_id}/quiz")
def deck_quiz(deck_id: int, limit: int | None = None):
    """未習得(correct_count<pass_count)を優先して出題するフレーズを返す。"""
    with db() as conn:
        drow = _owned_deck(conn, deck_id)
        s = _settings(drow["settings"])
        n = limit or s.get("quiz_size", 10)
        rows = conn.execute(
            "SELECT ph.*, COALESCE(dp.correct_count,0) AS dp_correct, "
            "dp.done_at AS dp_done "
            "FROM deck_phrases dph JOIN phrases ph ON ph.id = dph.phrase_id "
            "LEFT JOIN phrase_deck_progress dp "
            "  ON dp.deck_id = dph.deck_id AND dp.phrase_id = dph.phrase_id "
            "WHERE dph.deck_id = ?", (deck_id,),
        ).fetchall()
        pool = [dict(r) for r in rows]
        undone = [p for p in pool if p["dp_done"] is None]
        src = undone if undone else pool
        random.shuffle(src)
        out = src[:n]
        for p in out:
            p["deck_correct"] = p.pop("dp_correct", 0)
        return {"settings": s, "items": out}


class PhraseDeckAttempt(BaseModel):
    phrase_id: int
    direction: str            # 'ja2en' | 'en2ja'
    correct: bool
    result: str | None = None  # 'correct' | 'vague' | 'wrong'


@router.post("/{deck_id}/attempt")
def deck_attempt(deck_id: int, payload: PhraseDeckAttempt):
    with db() as conn:
        drow = _owned_deck(conn, deck_id)
        s = _settings(drow["settings"])
        # 忘却曲線ONなら per-user の mastery/SRS も更新。
        if s.get("use_srs", True):
            try:
                record_attempt(
                    conn, payload.phrase_id, payload.direction,
                    payload.correct, result=payload.result,
                    table="phrases", attempts_table="phrase_attempts",
                    id_column="phrase_id", user_id=current_user_id(),
                )
            except ValueError:
                pass
        # デッキ別の正解カウント（'correct' のみ加算）。
        is_correct = (payload.result or
                      ("correct" if payload.correct else "wrong")) == "correct"
        conn.execute(
            "INSERT OR IGNORE INTO phrase_deck_progress (deck_id, phrase_id) "
            "VALUES (?, ?)", (deck_id, payload.phrase_id),
        )
        if is_correct:
            conn.execute(
                "UPDATE phrase_deck_progress "
                "SET correct_count = correct_count + 1 "
                "WHERE deck_id = ? AND phrase_id = ?",
                (deck_id, payload.phrase_id),
            )
        prow = conn.execute(
            "SELECT correct_count, done_at FROM phrase_deck_progress "
            "WHERE deck_id = ? AND phrase_id = ?",
            (deck_id, payload.phrase_id),
        ).fetchone()
        cc = prow["correct_count"]
        done = prow["done_at"] is not None
        if not done and cc >= int(s.get("pass_count", 2)):
            conn.execute(
                "UPDATE phrase_deck_progress SET done_at = datetime('now') "
                "WHERE deck_id = ? AND phrase_id = ?",
                (deck_id, payload.phrase_id),
            )
            done = True
        return {"correct_count": cc, "done": done,
                "pass_count": int(s.get("pass_count", 2))}
