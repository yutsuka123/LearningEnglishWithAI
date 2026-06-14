"""Mastery + forgetting-curve (spaced repetition) logic.

Works identically for ``words`` and ``phrases`` (both have the same columns).

Rules implemented:

* Mastery is an integer 0..100, starting at 0.
* Items are tested in BOTH directions: ``ja2en`` (日本語→英語) and
  ``en2ja`` (英語→日本語). When both directions are answered correctly
  in a day, mastery gains +5 (capped at 100).
* Per-direction counters track accuracy for each direction.
* Forgetting curve (Leitner-style boxes): a correct review promotes the item
  to a longer interval; a wrong review sends it back to the start. The
  ``next_review`` date controls when an item resurfaces — mastered items come
  back rarely, but they DO come back (occasional review).
* Selection prioritises items that are *due* (next_review <= today), then
  weights remaining slots by ``100 - mastery`` (lower mastery → asked more).
* Monthly decay: once per month every word loses 5 mastery (floored at 0).
"""

from __future__ import annotations

import random
import sqlite3
from datetime import date, timedelta

MASTERY_MIN = 0
MASTERY_MAX = 100
CORRECT_BOTH_BONUS = 5
MONTHLY_DECAY = 5

# Forgetting-curve intervals in days, indexed by review level (box).
REVIEW_INTERVALS = [1, 2, 4, 8, 16, 35, 70, 150]

_DIRECTIONS = ("ja2en", "en2ja")


def clamp(value: int) -> int:
    return max(MASTERY_MIN, min(MASTERY_MAX, value))


def selection_weight(mastery: int) -> int:
    """Higher weight → more likely to be picked. ``100 - mastery`` (min 1)."""
    return max(1, MASTERY_MAX - mastery)


def interval_for_level(level: int) -> int:
    idx = max(0, min(level, len(REVIEW_INTERVALS) - 1))
    return REVIEW_INTERVALS[idx]


def _next_review_date(level: int) -> str:
    due = date.today() + timedelta(days=interval_for_level(level))
    return due.isoformat()


# ---------------------------------------------------------------------------
# Selection (forgetting curve aware)
# ---------------------------------------------------------------------------

def select_for_review(
    conn: sqlite3.Connection,
    table: str = "words",
    limit: int = 10,
) -> list[sqlite3.Row]:
    """Pick up to ``limit`` items, prioritising due ones, then weighting the
    rest by (100 - mastery)."""
    today = date.today().isoformat()
    # Due items first (never reviewed -> next_review IS NULL counts as due).
    due = conn.execute(
        f"SELECT * FROM {table} "
        "WHERE next_review IS NULL OR next_review <= ? "
        "ORDER BY mastery ASC, next_review ASC",
        (today,),
    ).fetchall()

    chosen = list(due[:limit])
    if len(chosen) >= limit:
        return chosen

    # Fill remaining slots with not-yet-due items, weighted by 100 - mastery.
    remaining = limit - len(chosen)
    chosen_ids = {r["id"] for r in chosen}
    rest = [
        r
        for r in conn.execute(f"SELECT * FROM {table}").fetchall()
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
    conn: sqlite3.Connection, limit: int = 10, table: str = "words"
) -> list[sqlite3.Row]:
    return select_for_review(conn, table=table, limit=limit)


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
) -> dict:
    """Log one attempt, update counters + per-direction stats, award the
    both-directions bonus, and advance the forgetting-curve schedule.

    ``result`` は 'correct' / 'vague'(うろ覚え) / 'wrong' のいずれか。未指定なら
    ``correct`` から決定。出現確率は次回復習日(SRS)で変わる:
      correct → 間隔を延ばす(出にくくなる) / vague → 約2日後 / wrong → 翌日
    """
    if direction not in _DIRECTIONS:
        raise ValueError("direction must be 'ja2en' or 'en2ja'")
    if result is None:
        result = "correct" if correct else "wrong"
    if result not in _RESULTS:
        raise ValueError("result must be correct/vague/wrong")

    # 正答としてカウントするのは 'correct' のみ（うろ覚えは正答に含めない）。
    counting = 1 if result == "correct" else 0

    today = date.today().isoformat()
    ask_col = f"ask_{direction}"
    ok_col = f"ok_{direction}"

    conn.execute(
        f"INSERT INTO {attempts_table} ({id_column}, direction, correct) "
        "VALUES (?, ?, ?)",
        (item_id, direction, counting),
    )
    conn.execute(
        f"UPDATE {table} SET "
        "times_asked = times_asked + 1, "
        "times_correct = times_correct + ?, "
        f"{ask_col} = {ask_col} + 1, "
        f"{ok_col} = {ok_col} + ?, "
        "last_studied = ? WHERE id = ?",
        (counting, counting, today, item_id),
    )

    # Advance / reset the forgetting-curve schedule per result.
    row = conn.execute(
        f"SELECT mastery, review_level FROM {table} WHERE id = ?", (item_id,)
    ).fetchone()
    if result == "correct":
        new_level = min(row["review_level"] + 1, len(REVIEW_INTERVALS) - 1)
    elif result == "vague":
        # うろ覚えは約2日後に再出題。高習熟の語は近くに引き戻し、
        # 新規語は wrong(翌日) より少し後にして「不正解 < うろ覚え < 正解」に。
        new_level = VAGUE_REVIEW_LEVEL
    else:  # wrong
        new_level = 0
    conn.execute(
        f"UPDATE {table} SET review_level = ?, next_review = ? WHERE id = ?",
        (new_level, _next_review_date(new_level), item_id),
    )

    # Both-directions-correct bonus (once per day per item).
    bonus_awarded = _maybe_award_bonus(
        conn, item_id, today, table, attempts_table, id_column
    )

    new = conn.execute(
        f"SELECT mastery, times_asked, times_correct, review_level, "
        f"next_review FROM {table} WHERE id = ?",
        (item_id,),
    ).fetchone()
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
    item_id: int,
    today: str,
    table: str,
    attempts_table: str,
    id_column: str,
) -> bool:
    # Compare on local calendar day. created_at is stored as UTC
    # (datetime('now')), so convert with 'localtime' to match the learner's
    # actual study day — otherwise the bonus silently never fires near UTC
    # midnight boundaries.
    correct_dirs = conn.execute(
        f"SELECT DISTINCT direction FROM {attempts_table} "
        f"WHERE {id_column} = ? AND correct = 1 "
        "AND date(created_at, 'localtime') = date('now', 'localtime')",
        (item_id,),
    ).fetchall()
    dirs = {r["direction"] for r in correct_dirs}
    if not {"ja2en", "en2ja"}.issubset(dirs):
        return False

    state_key = f"bonus:{table}:{item_id}:{today}"
    already = conn.execute(
        "SELECT value FROM app_state WHERE key = ?", (state_key,)
    ).fetchone()
    if already:
        return False

    row = conn.execute(
        f"SELECT mastery FROM {table} WHERE id = ?", (item_id,)
    ).fetchone()
    new_mastery = clamp(row["mastery"] + CORRECT_BOTH_BONUS)
    conn.execute(
        f"UPDATE {table} SET mastery = ? WHERE id = ?", (new_mastery, item_id)
    )
    conn.execute(
        "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, '1')",
        (state_key,),
    )
    return True


# ---------------------------------------------------------------------------
# Monthly decay
# ---------------------------------------------------------------------------

def apply_monthly_decay(conn: sqlite3.Connection) -> int:
    """If a new month has started since the last run, subtract 5 from every
    word's mastery (floored at 0). Returns the number of runs applied."""
    current_month = date.today().strftime("%Y-%m")
    row = conn.execute(
        "SELECT value FROM app_state WHERE key = 'last_decay_month'"
    ).fetchone()
    last_month = row["value"] if row else None

    if last_month == current_month:
        return 0

    conn.execute(
        f"UPDATE words SET mastery = MAX({MASTERY_MIN}, mastery - {MONTHLY_DECAY})"
    )
    conn.execute(
        f"UPDATE phrases SET mastery = MAX({MASTERY_MIN}, "
        f"mastery - {MONTHLY_DECAY})"
    )
    conn.execute(
        "INSERT OR REPLACE INTO app_state (key, value) VALUES "
        "('last_decay_month', ?)",
        (current_month,),
    )
    return 1
