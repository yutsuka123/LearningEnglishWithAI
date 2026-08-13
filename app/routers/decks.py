"""単語帳(デッキ)機能。分野/レベル(複数可)や手動選択で自分用の単語セットを
作り、デッキ別の設定（出題方向・N回正解で習得・忘却曲線ON/OFF・出題数）で学習
する。進捗はデッキ別(deck_progress)に保持。

2026-08-09: 無料(ログインのみ)ユーザーは単語帳1個・100語までに制限し、
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

router = APIRouter(prefix="/api/decks", tags=["decks"])


FREE_MAX_DECKS = 1
FREE_MAX_ITEMS = 100


def _enforce_free_tier_limits(conn, p: "DeckCreate") -> "DeckCreate":
    """無料(ログインのみ)ユーザーは単語帳1個・100語までに制限する。
    課金ユーザー・管理者は無制限（新規作成時のみチェック、既存デッキの
    閲覧・学習・削除・設定変更には制限をかけない）。"""
    if auth.is_charged_or_admin(conn, current_user_id()):
        return p
    existing = conn.execute(
        "SELECT COUNT(*) c FROM decks WHERE user_id = ?", (current_user_id(),)
    ).fetchone()["c"]
    if existing >= FREE_MAX_DECKS:
        raise HTTPException(
            403, f"無料範囲では単語帳は{FREE_MAX_DECKS}個までです。"
            "追加で作るには設定画面からチャージしてください。",
        )
    if p.word_ids:
        p.word_ids = p.word_ids[:FREE_MAX_ITEMS]
    else:
        p.limit = min(p.limit, FREE_MAX_ITEMS) if p.limit else FREE_MAX_ITEMS
    return p


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
    # 2026-08-09: 達成率はダッシュボード等と同じグローバルmastery基準
    # (mastery>=MASTERED_THRESHOLD)に統一する。`done`(デッキ内N回正解)は
    # デッキ内クイズの優先出題に引き続き使うため別途保持する。
    mastered = conn.execute(
        "SELECT COUNT(*) c FROM deck_words dw "
        "JOIN user_word_progress p ON p.word_id = dw.word_id "
        "  AND p.user_id = (SELECT user_id FROM decks WHERE id = ?) "
        "WHERE dw.deck_id = ? AND p.mastery >= ?",
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
        "SELECT COUNT(DISTINCT dw.word_id) AS total, "
        "SUM(CASE WHEN COALESCE(p.mastery, 0) >= ? THEN 1 ELSE 0 END) "
        "  AS mastered "
        "FROM decks d JOIN deck_words dw ON dw.deck_id = d.id "
        "LEFT JOIN user_word_progress p "
        "  ON p.word_id = dw.word_id AND p.user_id = d.user_id "
        "WHERE d.user_id = ?",
        (MASTERED_THRESHOLD, uid),
    ).fetchone()
    total = row["total"] or 0
    mastered = row["mastered"] or 0
    deck_count = conn.execute(
        "SELECT COUNT(*) c FROM decks WHERE user_id = ?", (uid,)
    ).fetchone()["c"]
    return {
        "deck_count": deck_count,
        "total": total,
        "mastered": mastered,
        "pct": round(mastered / total * 100) if total else 0,
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


@router.get("/summary")
def deck_overall_summary():
    with db() as conn:
        return _overall_summary(conn)


@router.post("", status_code=201)
def create_deck(payload: DeckCreate):
    settings = dict(DEFAULT_SETTINGS)
    settings.update(payload.settings or {})
    with db() as conn:
        payload = _enforce_free_tier_limits(conn, payload)
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


@router.get("/{deck_id}/words")
def deck_words_list(deck_id: int):
    """デッキ内の単語一覧（編集画面: 個別に削除(デッキから除外)するため）。"""
    from ..services.progress import user_items_subquery
    with db() as conn:
        _owned_deck(conn, deck_id)
        src = user_items_subquery("words")
        rows = conn.execute(
            f"SELECT * FROM {src} AS w "
            "JOIN deck_words dw ON dw.word_id = w.id "
            "WHERE dw.deck_id = ? ORDER BY w.english COLLATE NOCASE",
            [current_user_id(), deck_id],
        ).fetchall()
        return [dict(r) for r in rows]


class DeckAddWords(BaseModel):
    # 個別追加: word_ids を指定。分野一括追加: domains/levels を指定
    # （word_ids指定時はそちらを優先、_select_word_idsと同じ判定ロジック）。
    domains: list[str] = []
    levels: list[str] = []
    include_banned: bool = False
    word_ids: list[int] = []


@router.post("/{deck_id}/words")
def add_deck_words(deck_id: int, payload: DeckAddWords):
    """既存の単語帳に単語を追加する（個別追加・分野/レベル一括追加の両方に
    対応、2026-08-13新設）。無料(ログインのみ)ユーザーは合計100語まで
    （既存の作成時制限`FREE_MAX_ITEMS`と揃える）。"""
    with db() as conn:
        _owned_deck(conn, deck_id)
        creation_like = DeckCreate(
            name="", domains=payload.domains, levels=payload.levels,
            include_banned=payload.include_banned, word_ids=payload.word_ids,
        )
        ids = _select_word_ids(conn, creation_like)
        if not auth.is_charged_or_admin(conn, current_user_id()):
            current = conn.execute(
                "SELECT COUNT(*) c FROM deck_words WHERE deck_id = ?",
                (deck_id,),
            ).fetchone()["c"]
            room = max(0, FREE_MAX_ITEMS - current)
            if len(ids) > room:
                ids = ids[:room]
        conn.executemany(
            "INSERT OR IGNORE INTO deck_words (deck_id, word_id) VALUES (?, ?)",
            [(deck_id, wid) for wid in ids],
        )
        row = conn.execute(
            "SELECT * FROM decks WHERE id = ?", (deck_id,)
        ).fetchone()
        return _deck_summary(conn, row)


@router.delete("/{deck_id}/words/{word_id}", status_code=204)
def remove_deck_word(deck_id: int, word_id: int):
    """デッキから単語を除外する（単語自体の削除ではない）。"""
    with db() as conn:
        _owned_deck(conn, deck_id)
        conn.execute(
            "DELETE FROM deck_words WHERE deck_id = ? AND word_id = ?",
            (deck_id, word_id),
        )
        conn.execute(
            "DELETE FROM deck_progress WHERE deck_id = ? AND word_id = ?",
            (deck_id, word_id),
        )


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
