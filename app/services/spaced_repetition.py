"""Mastery + forgetting-curve (spaced repetition) logic.

Works identically for ``words`` and ``phrases`` (both have the same columns).

Rules implemented:

* Mastery is an integer 0..200, starting at 0.
* Items are tested in BOTH directions: ``ja2en`` (日本語→英語) and
  ``en2ja`` (英語→日本語). When both directions are answered correctly
  in a day, mastery gains +5 (capped at 200).
* 「覚えた」ボタン: 学習者が「もう覚えた」と宣言すると mastery を満点(200)に。
  週-1の減衰でも 100 を下回るまで約100週かかるため、長く「覚えた」状態を保つ。
* mastery >= 100 を「覚えた(mastered)」とみなす。一覧で表示/非表示を切替可能。
* Per-direction counters track accuracy for each direction.
* Forgetting curve (Leitner-style boxes): a correct review promotes the item
  to a longer interval; a wrong review sends it back to the start. The
  ``next_review`` date controls when an item resurfaces — mastered items come
  back rarely, but they DO come back (occasional review).
* Selection prioritises items that are *due* (next_review <= today), then
  weights remaining slots by ``100 - mastery`` (lower mastery → asked more).
* Weekly decay: every elapsed week each item loses 1 mastery (floored at 0).
"""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta

MASTERY_MIN = 0
MASTERY_MAX = 200
CORRECT_BOTH_BONUS = 5
WEEKLY_DECAY = 1            # 週あたりの減衰（忘却曲線）。
MASTERED_THRESHOLD = 100   # これ以上で「覚えた」。
KNOWN_MASTERY = 200        # 「覚えた」ボタン押下時の値（満点）。

# Forgetting-curve intervals in days, indexed by review level (box).
REVIEW_INTERVALS = [1, 2, 4, 8, 16, 35, 70, 150]

_DIRECTIONS = ("ja2en", "en2ja")


def clamp(value: int) -> int:
    return max(MASTERY_MIN, min(MASTERY_MAX, value))


def selection_weight(mastery: int) -> int:
    """Higher weight → more likely to be picked. ``100 - mastery`` (min 1).
    「覚えた」(mastery>=100) は最小重み1で、まれにしか出題されない。"""
    return max(1, MASTERED_THRESHOLD - mastery)


def interval_for_level(level: int) -> int:
    idx = max(0, min(level, len(REVIEW_INTERVALS) - 1))
    return REVIEW_INTERVALS[idx]


def _next_review_date(level: int) -> str:
    due = date.today() + timedelta(days=interval_for_level(level))
    return due.isoformat()


# ---------------------------------------------------------------------------
# Selection (forgetting curve aware)
# ---------------------------------------------------------------------------

def banned_filter(table: str) -> str:
    """SQL fragment (no leading AND) selecting only NON-banned rows.
    Banned = words.domain '禁止用語' / phrases.scene starting with '禁止'."""
    if table == "phrases":
        return "COALESCE(scene, '') NOT LIKE '禁止%'"
    return "COALESCE(domain, '') <> '禁止用語'"


def select_for_review(
    conn: sqlite3.Connection,
    table: str = "words",
    limit: int = 10,
    exclude_banned: bool = False,
    *,
    user_id: int,
) -> list[sqlite3.Row]:
    """Pick up to ``limit`` items for ``user_id``, prioritising due ones, then
    weighting the rest by (100 - mastery). 進捗は per-user テーブルからマージ。
    When ``exclude_banned`` is set, 禁止用語 items are never selected."""
    from .progress import user_items_subquery

    today = date.today().isoformat()
    src = user_items_subquery(table)  # 1つの ? (=user_id) を取る
    ban = f" AND {banned_filter(table)}" if exclude_banned else ""
    # Due items first (never reviewed -> next_review IS NULL counts as due).
    due = conn.execute(
        f"SELECT * FROM {src} AS t "
        f"WHERE (next_review IS NULL OR next_review <= ?){ban} "
        "ORDER BY mastery ASC, next_review ASC",
        (user_id, today),
    ).fetchall()

    chosen = list(due[:limit])
    if len(chosen) >= limit:
        return chosen

    # Fill remaining slots with not-yet-due items, weighted by 100 - mastery.
    remaining = limit - len(chosen)
    chosen_ids = {r["id"] for r in chosen}
    where = f" WHERE {banned_filter(table)}" if exclude_banned else ""
    rest = [
        r
        for r in conn.execute(
            f"SELECT * FROM {src} AS t{where}", (user_id,)).fetchall()
        if r["id"] not in chosen_ids
    ]
    chosen += _weighted_sample(rest, remaining)
    return chosen


def _weighted_sample(rows: list[sqlite3.Row], k: int) -> list[sqlite3.Row]:
    """Weighted sampling without replacement, weight ∝ (100 - mastery)."""
    pool = list(rows)
    weights = [selection_weight(r["mastery"]) for r in pool]
    out: list[sqlite3.Row] = []
    for _ in range(min(k, len(pool))):
        total = sum(weights)
        if total <= 0:
            break
        r = random.uniform(0, total)
        upto = 0.0
        for idx, w in enumerate(weights):
            upto += w
            if upto >= r:
                out.append(pool.pop(idx))
                weights.pop(idx)
                break
    return out


# Backwards-compatible alias used elsewhere.
def pick_weighted(
    conn: sqlite3.Connection, limit: int = 10, table: str = "words",
    exclude_banned: bool = False, *, user_id: int,
) -> list[sqlite3.Row]:
    return select_for_review(
        conn, table=table, limit=limit, exclude_banned=exclude_banned,
        user_id=user_id,
    )


# ---------------------------------------------------------------------------
# Recording attempts (generic for words & phrases)
# ---------------------------------------------------------------------------

# レベルを下げて「うろ覚え」を近いうちに再出題するための目標レベル。
VAGUE_REVIEW_LEVEL = 1  # 約2日後に再出題

_RESULTS = ("correct", "vague", "wrong")


def record_attempt(
    conn: sqlite3.Connection,
    item_id: int,
    direction: str,
    correct: bool,
    *,
    result: str | None = None,
    table: str = "words",
    attempts_table: str = "word_attempts",
    id_column: str = "word_id",
    user_id: int,
) -> dict:
    """Log one attempt for ``user_id``, update per-user counters + per-direction
    stats, award the both-directions bonus, and advance the forgetting curve.
    進捗は per-user テーブル(user_word/phrase_progress)へ UPSERT。

    ``result`` は 'correct' / 'vague'(うろ覚え) / 'wrong'。未指定なら correct から。
    """
    from . import progress as P

    if direction not in _DIRECTIONS:
        raise ValueError("direction must be 'ja2en' or 'en2ja'")
    if result is None:
        result = "correct" if correct else "wrong"
    if result not in _RESULTS:
        raise ValueError("result must be correct/vague/wrong")

    # 正答としてカウントするのは 'correct' のみ（うろ覚えは正答に含めない）。
    counting = 1 if result == "correct" else 0
    today = date.today().isoformat()

    conn.execute(
        f"INSERT INTO {attempts_table} ({id_column}, direction, correct, "
        "user_id) VALUES (?, ?, ?, ?)",
        (item_id, direction, counting, user_id),
    )

    cur = P.get_progress(conn, user_id, table, item_id)
    if result == "correct":
        new_level = min(cur["review_level"] + 1, len(REVIEW_INTERVALS) - 1)
    elif result == "vague":
        new_level = VAGUE_REVIEW_LEVEL
    else:  # wrong
        new_level = 0
    P.upsert_progress(
        conn, user_id, table, item_id,
        times_asked=cur["times_asked"] + 1,
        times_correct=cur["times_correct"] + counting,
        **{f"ask_{direction}": cur[f"ask_{direction}"] + 1,
           f"ok_{direction}": cur[f"ok_{direction}"] + counting},
        last_studied=today,
        review_level=new_level,
        next_review=_next_review_date(new_level),
    )

    bonus_awarded = _maybe_award_bonus(
        conn, user_id, item_id, today, table, attempts_table, id_column
    )

    new = P.get_progress(conn, user_id, table, item_id)
    return {
        "mastery": new["mastery"],
        "bonus_awarded": bonus_awarded,
        "times_asked": new["times_asked"],
        "times_correct": new["times_correct"],
        "review_level": new["review_level"],
        "next_review": new["next_review"],
    }


def _maybe_award_bonus(
    conn: sqlite3.Connection,
    user_id: int,
    item_id: int,
    today: str,
    table: str,
    attempts_table: str,
    id_column: str,
) -> bool:
    from . import progress as P

    # 当該ユーザーの本日(ローカル日)の正答方向を集計。両方向そろえば +5。
    correct_dirs = conn.execute(
        f"SELECT DISTINCT direction FROM {attempts_table} "
        f"WHERE {id_column} = ? AND user_id = ? AND correct = 1 "
        "AND date(created_at, 'localtime') = date('now', 'localtime')",
        (item_id, user_id),
    ).fetchall()
    dirs = {r["direction"] for r in correct_dirs}
    if not {"ja2en", "en2ja"}.issubset(dirs):
        return False

    state_key = f"bonus:{table}:{user_id}:{item_id}:{today}"
    if conn.execute(
        "SELECT 1 FROM app_state WHERE key = ?", (state_key,)
    ).fetchone():
        return False

    cur = P.get_progress(conn, user_id, table, item_id)
    P.upsert_progress(conn, user_id, table, item_id,
                      mastery=clamp(cur["mastery"] + CORRECT_BOTH_BONUS))
    conn.execute(
        "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, '1')",
        (state_key,),
    )
    return True


# ---------------------------------------------------------------------------
# 「覚えた」宣言
# ---------------------------------------------------------------------------

def set_known(
    conn: sqlite3.Connection, item_id: int, known: bool, *,
    table: str = "words", user_id: int,
) -> int:
    """「覚えた」ボタン(per-user)。known=True で満点(200)、False で解除(95)。"""
    from . import progress as P
    new = KNOWN_MASTERY if known else (MASTERED_THRESHOLD - 5)
    P.upsert_progress(conn, user_id, table, item_id, mastery=new)
    return new


# ---------------------------------------------------------------------------
# Weekly decay (忘却曲線)
# ---------------------------------------------------------------------------

def apply_weekly_decay(conn: sqlite3.Connection) -> int:
    """Subtract 1 mastery for every full week elapsed since the last run
    (floored at 0). Handles multiple missed weeks at once. Returns the number
    of weeks applied."""
    today = date.today()
    row = conn.execute(
        "SELECT value FROM app_state WHERE key = 'last_decay_date'"
    ).fetchone()
    if not row or not row["value"]:
        conn.execute(
            "INSERT OR REPLACE INTO app_state (key, value) VALUES "
            "('last_decay_date', ?)",
            (today.isoformat(),),
        )
        return 0
    try:
        last = date.fromisoformat(row["value"])
    except ValueError:
        last = today
    weeks = (today - last).days // 7
    if weeks <= 0:
        return 0

    drop = weeks * WEEKLY_DECAY
    # per-user 進捗テーブルを全行減衰（全ユーザー分まとめて）。
    for tbl in ("user_word_progress", "user_phrase_progress"):
        conn.execute(
            f"UPDATE {tbl} SET mastery = MAX({MASTERY_MIN}, mastery - ?)",
            (drop,),
        )
    # 端数日を保つため、消化した週数ぶんだけ基準日を進める。
    new_anchor = last + timedelta(weeks=weeks)
    conn.execute(
        "INSERT OR REPLACE INTO app_state (key, value) VALUES "
        "('last_decay_date', ?)",
        (new_anchor.isoformat(),),
    )
    return weeks


# 後方互換: 旧名で呼ばれても週次減衰を実行する。
def apply_monthly_decay(conn: sqlite3.Connection) -> int:
    return apply_weekly_decay(conn)
