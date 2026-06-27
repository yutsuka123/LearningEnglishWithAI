"""単語帳(デッキ)機能。分野/レベル(複数可)や手動選択で自分用の単語セットを
作り、デッキ別の設定（出題方向・N回正解で習得・忘却曲線ON/OFF・出題数）で学習
する。進捗はデッキ別(deck_progress)に保持。"""

from __future__ import annotations

import json
import random

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..database import db
from ..services.auth import current_user_id
from ..services.spaced_repetition import banned_filter, record_attempt

router = APIRouter(prefix="/api/decks", tags=["decks"])


def _owned_deck(conn, deck_id: int):
    """現在ユーザーが所有するデッキ行を返す（無ければ404）。"""
    row = conn.execute(
        "SELECT * FROM decks WHERE id = ? AND user_id = ?",
        (deck_id, current_user_id()),
    ).fetchone()
    if not row:
        raise HTTPException(404, "単語帳が見つかりません")
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
        "SELECT COUNT(*) c FROM deck_words WHERE deck_id = ?", (row["id"],)
    ).fetchone()["c"]
    done = conn.execute(
        "SELECT COUNT(*) c FROM deck_progress "
        "WHERE deck_id = ? AND done_at IS NOT NULL", (row["id"],)
    ).fetchone()["c"]
    return {
        "id": row["id"],
        "name": row["name"],
        "settings": _settings(row["settings"]),
        "total": total,
        "done": done,
        "created_at": row["created_at"],
    }


class DeckCreate(BaseModel):
    name: str
    settings: dict = {}
    # 抽出条件（お任せ/フィルタ作成）。word_ids 指定なら手動。
    domains: list[str] = []
    levels: list[str] = []
    include_banned: bool = False
    limit: int | None = None     # お任せ時の最大件数（Noneで全件）
    word_ids: list[int] = []


def _select_word_ids(conn, p: DeckCreate) -> list[int]:
    if p.word_ids:
        return list(dict.fromkeys(p.word_ids))
    from ..services.auth import current_user_allow_banned
    include_banned = p.include_banned and current_user_allow_banned()
    where, params = [], []
    if p.domains:
        ph = ",".join("?" * len(p.domains))
        where.append(f"COALESCE(domain,'') IN ({ph})")
        params += p.domains
    if p.levels:
        ph = ",".join("?" * len(p.levels))
        where.append(f"COALESCE(level,'') IN ({ph})")
        params += p.levels
    if not include_banned:
        where.append(banned_filter("words"))
    clause = (" WHERE " + " AND ".join(where)) if where else ""
    rows = conn.execute(
        f"SELECT id FROM words{clause}", params
    ).fetchall()
    ids = [r["id"] for r in rows]
    if p.limit and p.limit < len(ids):
        ids = random.sample(ids, p.limit)
    return ids


@router.get("")
def list_decks():
    with db() as conn:
        rows = conn.execute(
            "SELECT * FROM decks WHERE user_id = ? ORDER BY created_at DESC",
            (current_user_id(),),
        ).fetchall()
        return [_deck_summary(conn, r) for r in rows]


@router.post("", status_code=201)
def create_deck(payload: DeckCreate):
    settings = dict(DEFAULT_SETTINGS)
    settings.update(payload.settings or {})
    with db() as conn:
        ids = _select_word_ids(conn, payload)
        cur = conn.execute(
            "INSERT INTO decks (name, settings, user_id) VALUES (?, ?, ?)",
            (payload.name.strip() or "新しい単語帳", json.dumps(settings),
             current_user_id()),
        )
        deck_id = cur.lastrowid
        conn.executemany(
            "INSERT OR IGNORE INTO deck_words (deck_id, word_id) VALUES (?, ?)",
            [(deck_id, wid) for wid in ids],
        )
        row = conn.execute(
            "SELECT * FROM decks WHERE id = ?", (deck_id,)
        ).fetchone()
        return _deck_summary(conn, row)


@router.get("/{deck_id}")
def get_deck(deck_id: int):
    with db() as conn:
        return _deck_summary(conn, _owned_deck(conn, deck_id))


class DeckUpdate(BaseModel):
    name: str | None = None
    settings: dict | None = None


@router.put("/{deck_id}")
def update_deck(deck_id: int, payload: DeckUpdate):
    with db() as conn:
        row = _owned_deck(conn, deck_id)
        name = payload.name if payload.name is not None else row["name"]
        settings = _settings(row["settings"])
        if payload.settings is not None:
            settings.update(payload.settings)
        conn.execute(
            "UPDATE decks SET name = ?, settings = ? WHERE id = ?",
            (name, json.dumps(settings), deck_id),
        )
        row = conn.execute(
            "SELECT * FROM decks WHERE id = ?", (deck_id,)
        ).fetchone()
        return _deck_summary(conn, row)


@router.delete("/{deck_id}", status_code=204)
def delete_deck(deck_id: int):
    with db() as conn:
        cur = conn.execute(
            "DELETE FROM decks WHERE id = ? AND user_id = ?",
            (deck_id, current_user_id()),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "単語帳が見つかりません")


@router.get("/{deck_id}/quiz")
def deck_quiz(deck_id: int, limit: int | None = None):
    """未習得(correct_count<pass_count)を優先して出題する単語を返す。"""
    with db() as conn:
        drow = _owned_deck(conn, deck_id)
        s = _settings(drow["settings"])
        n = limit or s.get("quiz_size", 10)
        rows = conn.execute(
            "SELECT w.*, COALESCE(dp.correct_count,0) AS dp_correct, "
            "dp.done_at AS dp_done "
            "FROM deck_words dw JOIN words w ON w.id = dw.word_id "
            "LEFT JOIN deck_progress dp "
            "  ON dp.deck_id = dw.deck_id AND dp.word_id = dw.word_id "
            "WHERE dw.deck_id = ?", (deck_id,),
        ).fetchall()
        pool = [dict(r) for r in rows]
        undone = [w for w in pool if w["dp_done"] is None]
        src = undone if undone else pool
        random.shuffle(src)
        out = src[:n]
        for w in out:
            w["deck_correct"] = w.pop("dp_correct", 0)
        return {"settings": s, "items": out}


class DeckAttempt(BaseModel):
    word_id: int
    direction: str            # 'ja2en' | 'en2ja'
    correct: bool
    result: str | None = None  # 'correct' | 'vague' | 'wrong'


@router.post("/{deck_id}/attempt")
def deck_attempt(deck_id: int, payload: DeckAttempt):
    with db() as conn:
        drow = _owned_deck(conn, deck_id)
        s = _settings(drow["settings"])
        # 忘却曲線ONなら per-user の mastery/SRS も更新。
        if s.get("use_srs", True):
            try:
                record_attempt(
                    conn, payload.word_id, payload.direction,
                    payload.correct, result=payload.result,
                    user_id=current_user_id(),
                )
            except ValueError:
                pass
        # デッキ別の正解カウント（'correct' のみ加算）。
        is_correct = (payload.result or
                      ("correct" if payload.correct else "wrong")) == "correct"
        conn.execute(
            "INSERT OR IGNORE INTO deck_progress (deck_id, word_id) "
            "VALUES (?, ?)", (deck_id, payload.word_id),
        )
        if is_correct:
            conn.execute(
                "UPDATE deck_progress SET correct_count = correct_count + 1 "
                "WHERE deck_id = ? AND word_id = ?",
                (deck_id, payload.word_id),
            )
        prow = conn.execute(
            "SELECT correct_count, done_at FROM deck_progress "
            "WHERE deck_id = ? AND word_id = ?", (deck_id, payload.word_id),
        ).fetchone()
        cc = prow["correct_count"]
        done = prow["done_at"] is not None
        if not done and cc >= int(s.get("pass_count", 2)):
            conn.execute(
                "UPDATE deck_progress SET done_at = datetime('now') "
                "WHERE deck_id = ? AND word_id = ?",
                (deck_id, payload.word_id),
            )
            done = True
        return {"correct_count": cc, "done": done,
                "pass_count": int(s.get("pass_count", 2))}
