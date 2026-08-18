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
from dataclasses import dataclass
from datetime import date, timedelta

MASTERY_MIN = 0
MASTERY_MAX = 200
CORRECT_BOTH_BONUS = 5
WEEKLY_DECAY = 1            # 1日あたりの減衰(既定値)。旧名だが単位は日。
MASTERED_THRESHOLD = 100   # これ以上で「覚えた」。
KNOWN_MASTERY = 125        # 「覚えた」ボタン押下時の加点(既定値)。
VAGUE_BONUS = 25           # 「うろ覚え」ボタンで加点する mastery(既定値)。

# Forgetting-curve intervals in days, indexed by review level (box).
REVIEW_INTERVALS = [1, 2, 4, 8, 16, 35, 70, 150]

_DIRECTIONS = ("ja2en", "en2ja")


# ---------------------------------------------------------------------------
# per-user mastery設定(2026-08-18・ユーザー要望:「忘却曲線や、何回うろ覚え
# で覚えたとなるか」を詳細設定でユーザーが調整可能にしたい)。
# user_settings(JSON)の以下キーで上書き可能。未設定時はDEFAULTを使う。
#   mastery_max          : 満点(0..この値)。既定200、100〜300の範囲。
#   mastered_threshold   : これ以上で「覚えた」。既定100。
#   known_bonus          : 「覚えた」ボタンでの加点。既定125(閾値100を
#                           少し超えるだけにして、レビューしないと
#                           約25日で閾値を割る設計・2026-08-18)。
#   vague_bonus          : 「うろ覚え」ボタンでの加点。既定25。
#   decay_amount         : 忘却曲線の減衰量(pt)。既定1。
#   decay_interval_days  : 何日ごとに上の量を減衰させるか。既定1日
#                           (2026-08-18変更: 7日→1日)。
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class MasteryConfig:
    mastery_max: int = MASTERY_MAX
    mastered_threshold: int = MASTERED_THRESHOLD
    known_bonus: int = KNOWN_MASTERY
    vague_bonus: int = VAGUE_BONUS
    decay_amount: int = WEEKLY_DECAY
    decay_interval_days: int = 1


DEFAULT_MASTERY_CONFIG = MasteryConfig()

# ユーザーが指定できる範囲(ユーザー要望「100ptもありで300ptまであり」を
# 踏まえ、満点は100〜300に制限。他の値も暴走防止のため妥当な範囲に収める)。
_MASTERY_MAX_BOUNDS = (100, 300)
_THRESHOLD_MIN = 10
_BONUS_BOUNDS = (1, 300)
_DECAY_AMOUNT_BOUNDS = (0, 100)   # 0 = 忘却曲線オフ
_DECAY_INTERVAL_BOUNDS = (1, 90)


def _clampi(value, lo: int, hi: int, default: int) -> int:
    try:
        v = int(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, v))


def mastery_config_from_settings(settings: dict | None) -> MasteryConfig:
    """user_settings(JSON dict)から MasteryConfig を組み立てる。値は不正
    (範囲外・型違い・API直叩き等)でも安全な範囲にクランプするので、この
    関数を通した戻り値は常に信頼できる(呼び出し側での追加検証は不要)。"""
    s = settings or {}
    mastery_max = _clampi(
        s.get("mastery_max"), *_MASTERY_MAX_BOUNDS, DEFAULT_MASTERY_CONFIG.mastery_max)
    mastered_threshold = _clampi(
        s.get("mastered_threshold"), _THRESHOLD_MIN, mastery_max,
        min(DEFAULT_MASTERY_CONFIG.mastered_threshold, mastery_max))
    known_bonus = _clampi(
        s.get("known_bonus"), *_BONUS_BOUNDS, DEFAULT_MASTERY_CONFIG.known_bonus)
    vague_bonus = _clampi(
        s.get("vague_bonus"), *_BONUS_BOUNDS, DEFAULT_MASTERY_CONFIG.vague_bonus)
    decay_amount = _clampi(
        s.get("decay_amount"), *_DECAY_AMOUNT_BOUNDS,
        DEFAULT_MASTERY_CONFIG.decay_amount)
    decay_interval_days = _clampi(
        s.get("decay_interval_days"), *_DECAY_INTERVAL_BOUNDS,
        DEFAULT_MASTERY_CONFIG.decay_interval_days)
    return MasteryConfig(
        mastery_max=mastery_max, mastered_threshold=mastered_threshold,
        known_bonus=known_bonus, vague_bonus=vague_bonus,
        decay_amount=decay_amount, decay_interval_days=decay_interval_days,
    )


def clamp(value: int, mastery_max: int = MASTERY_MAX) -> int:
    return max(MASTERY_MIN, min(mastery_max, value))


def selection_weight(mastery: int, threshold: int = MASTERED_THRESHOLD) -> int:
    """Higher weight → more likely to be picked. ``threshold - mastery`` (min 1).
    「覚えた」(mastery>=threshold) は最小重み1で、まれにしか出題されない。"""
    return max(1, threshold - mastery)


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
    where_extra: str = "",
    params_extra: tuple = (),
    cfg: MasteryConfig | None = None,
) -> list[sqlite3.Row]:
    """Pick up to ``limit`` items for ``user_id``, prioritising due ones, then
    weighting the rest by (threshold - mastery). 進捗は per-user テーブルから
    マージ。When ``exclude_banned`` is set, 禁止用語 items are never selected.

    ``where_extra`` は追加の絞り込み条件（先頭の AND 不要・列は subquery の別名
    ``t`` を前提）。フラッシュカード等で分野/レベル/覚えた状態でフィルタするのに使う。
    ``cfg`` は呼び出し元ユーザーの MasteryConfig（未指定ならDEFAULT）。
    """
    from .progress import user_items_subquery

    cfg = cfg or DEFAULT_MASTERY_CONFIG
    today = date.today().isoformat()
    src = user_items_subquery(table)  # 1つの ? (=user_id) を取る
    ban = f" AND {banned_filter(table)}" if exclude_banned else ""
    extra = f" AND ({where_extra})" if where_extra else ""
    ep = tuple(params_extra)
    # Due items first (never reviewed -> next_review IS NULL counts as due).
    due = conn.execute(
        f"SELECT * FROM {src} AS t "
        f"WHERE (next_review IS NULL OR next_review <= ?){ban}{extra} "
        "ORDER BY mastery ASC, next_review ASC",
        (user_id, today, *ep),
    ).fetchall()

    chosen = list(due[:limit])
    if len(chosen) >= limit:
        return chosen

    # Fill remaining slots with not-yet-due items, weighted by 100 - mastery.
    remaining = limit - len(chosen)
    chosen_ids = {r["id"] for r in chosen}
    conds = []
    if exclude_banned:
        conds.append(banned_filter(table))
    if where_extra:
        conds.append(f"({where_extra})")
    where = (" WHERE " + " AND ".join(conds)) if conds else ""
    rest = [
        r
        for r in conn.execute(
            f"SELECT * FROM {src} AS t{where}", (user_id, *ep)).fetchall()
        if r["id"] not in chosen_ids
    ]
    chosen += _weighted_sample(rest, remaining, cfg.mastered_threshold)
    return chosen


def _weighted_sample(
    rows: list[sqlite3.Row], k: int, threshold: int = MASTERED_THRESHOLD,
) -> list[sqlite3.Row]:
    """Weighted sampling without replacement, weight ∝ (threshold - mastery)."""
    pool = list(rows)
    weights = [selection_weight(r["mastery"], threshold) for r in pool]
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
    cfg: MasteryConfig | None = None,
) -> list[sqlite3.Row]:
    return select_for_review(
        conn, table=table, limit=limit, exclude_banned=exclude_banned,
        user_id=user_id, cfg=cfg,
    )


# ---------------------------------------------------------------------------
# Recording attempts (generic for words & phrases)
# ---------------------------------------------------------------------------

# レベルを下げて「うろ覚え」を近いうちに再出題するための目標レベル。
VAGUE_REVIEW_LEVEL = 1  # 約2日後に再出題

_RESULTS = ("correct", "vague", "wrong")


def mark_vague(
    conn: sqlite3.Connection, item_id: int, *,
    table: str = "words", user_id: int,
    cfg: MasteryConfig | None = None,
) -> dict:
    """「うろ覚え」ボタン(per-user、words/phrases共通)。mastery を
    cfg.vague_bonus 加点するが、「覚えた」基準(cfg.mastered_threshold)を
    超えては伸びない(何度押しても閾値ちょうどで頭打ち。「うろ覚え」の
    連打だけで「覚えた」を明示的に押した扱いにはしない設計・2026-08-18)。
    既に閾値以上(「覚えた」「卒業」等)ならその値のまま変えない(下げない)。
    復習間隔も VAGUE_REVIEW_LEVEL（≒2日後）に更新する（以前はmasteryのみで
    フラッシュカード経由だと間隔が停滞していた）。"""
    from . import progress as P
    cfg = cfg or DEFAULT_MASTERY_CONFIG
    cur = P.get_progress(conn, user_id, table, item_id)
    capped = min(cur["mastery"] + cfg.vague_bonus, cfg.mastered_threshold)
    new_mastery = clamp(max(cur["mastery"], capped), cfg.mastery_max)
    next_review = _next_review_date(VAGUE_REVIEW_LEVEL)
    P.upsert_progress(conn, user_id, table, item_id, mastery=new_mastery,
                      review_level=VAGUE_REVIEW_LEVEL, next_review=next_review)
    return {"mastery": new_mastery, "review_level": VAGUE_REVIEW_LEVEL,
            "next_review": next_review,
            "mastered": new_mastery >= cfg.mastered_threshold}


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
    cfg: MasteryConfig | None = None,
) -> dict:
    """Log one attempt for ``user_id``, update per-user counters + per-direction
    stats, award the both-directions bonus, and advance the forgetting curve.
    進捗は per-user テーブル(user_word/phrase_progress)へ UPSERT。

    ``result`` は 'correct' / 'vague'(うろ覚え) / 'wrong'。未指定なら correct から。
    """
    from . import progress as P

    cfg = cfg or DEFAULT_MASTERY_CONFIG
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
        conn, user_id, item_id, today, table, attempts_table, id_column, cfg,
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
    cfg: MasteryConfig | None = None,
) -> bool:
    from . import progress as P

    cfg = cfg or DEFAULT_MASTERY_CONFIG

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
                      mastery=clamp(cur["mastery"] + CORRECT_BOTH_BONUS,
                                    cfg.mastery_max))
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
    cfg: MasteryConfig | None = None,
) -> dict:
    """「覚えた」ボタン(per-user)。known=True で mastery を
    max(現在値, cfg.known_bonus) にする(既に基準以上ならそのまま・下げない。
    加算ではないため「戻す→覚えた」を繰り返しても既定125を超えて積み上がる
    ことはない。「卒業」ボタンとの差を保つための設計・2026-08-18)。
    known=Falseで解除(cfg.mastered_threshold - 5)。復習間隔も連動させる:
    known=True は最長間隔(150日、以前はフラッシュカード経由だと更新されず
    間隔が停滞するバグがあった)、known=False（「戻す」＝復活）は最短間隔
    （すぐ出題対象に戻す）。known=Falseは「完全に覚えた」(perfect)も解除する
    (2026-08-18・中途半端にperfect=1だけ残る状態を防ぐ)。"""
    from . import progress as P
    cfg = cfg or DEFAULT_MASTERY_CONFIG
    if known:
        cur = P.get_progress(conn, user_id, table, item_id)
        new_mastery = clamp(max(cur["mastery"], cfg.known_bonus), cfg.mastery_max)
    else:
        new_mastery = max(MASTERY_MIN, cfg.mastered_threshold - 5)
    new_level = (len(REVIEW_INTERVALS) - 1) if known else 0
    next_review = _next_review_date(new_level)
    fields = dict(mastery=new_mastery, review_level=new_level,
                  next_review=next_review)
    if not known:
        fields["perfect"] = 0
    P.upsert_progress(conn, user_id, table, item_id, **fields)
    return {"mastery": new_mastery, "review_level": new_level,
            "next_review": next_review,
            "mastered": new_mastery >= cfg.mastered_threshold}


# ---------------------------------------------------------------------------
# 「完全に覚えた」宣言(2026-08-18・忘却曲線の対象から除外)
# ---------------------------------------------------------------------------

def set_perfect(
    conn: sqlite3.Connection, item_id: int, perfect: bool, *,
    table: str = "words", user_id: int,
    cfg: MasteryConfig | None = None,
) -> dict:
    """「完全に覚えた」ボタン(per-user)。perfect=Trueで満点(cfg.mastery_max)
    に固定し、以後 apply_forgetting_decay の対象から除外する(忘却曲線で
    減らない)。perfect=False（解除）で通常の「覚えた」相当
    (cfg.mastered_threshold - 5)に戻し、忘却曲線の対象にも戻す。"""
    from . import progress as P
    cfg = cfg or DEFAULT_MASTERY_CONFIG
    if perfect:
        new_mastery = cfg.mastery_max
        new_level = len(REVIEW_INTERVALS) - 1
    else:
        new_mastery = max(MASTERY_MIN, cfg.mastered_threshold - 5)
        new_level = 0
    next_review = _next_review_date(new_level)
    P.upsert_progress(
        conn, user_id, table, item_id, mastery=new_mastery,
        review_level=new_level, next_review=next_review,
        perfect=1 if perfect else 0,
    )
    return {"mastery": new_mastery, "review_level": new_level,
            "next_review": next_review, "perfect": perfect,
            "mastered": new_mastery >= cfg.mastered_threshold}


# ---------------------------------------------------------------------------
# Forgetting decay（忘却曲線・per-user設定対応・2026-08-18）
# ---------------------------------------------------------------------------

def _read_settings_json(conn: sqlite3.Connection, user_id: int) -> dict:
    import json
    row = conn.execute(
        "SELECT settings FROM user_settings WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not row or not row["settings"]:
        return {}
    try:
        d = json.loads(row["settings"])
        return d if isinstance(d, dict) else {}
    except (ValueError, TypeError):
        return {}


def _write_settings_json(
    conn: sqlite3.Connection, user_id: int, settings: dict,
) -> None:
    import json
    conn.execute(
        "INSERT INTO user_settings (user_id, settings, updated_at) "
        "VALUES (?, ?, datetime('now')) "
        "ON CONFLICT(user_id) DO UPDATE SET "
        "settings=excluded.settings, updated_at=excluded.updated_at",
        (user_id, json.dumps(settings)),
    )


def apply_forgetting_decay(conn: sqlite3.Connection) -> int:
    """ユーザーごとに設定された忘却曲線(decay_amount pt / decay_interval_days
    日)を適用する。各ユーザーの直近適用日(user_settings内の"_decay_anchor")
    からの経過日数ぶん、消化できた区間数だけまとめて減衰させる(複数区間分の
    未適用があっても一度で追いつく・以前の週次版と同じ考え方)。
    decay_amount=0(ユーザーが忘却曲線をオフに設定)の場合は減衰させず、
    アンカーだけ今日に進める(後で再度オンにしたときに過去分をまとめて
    減衰させてしまわないため)。呼び出し元(app起動時)ではRUNの都度全ユーザー
    分をチェックするため、通常は軽量(対象ユーザー数分のSELECT/UPDATE)。
    戻り値: 実際に減衰を適用したユーザー数。"""
    today = date.today()
    user_ids: set[int] = set()
    for tbl in ("user_settings", "user_word_progress", "user_phrase_progress"):
        user_ids |= {
            r["user_id"]
            for r in conn.execute(f"SELECT DISTINCT user_id FROM {tbl}")
            .fetchall()
        }

    applied = 0
    for uid in user_ids:
        settings = _read_settings_json(conn, uid)
        cfg = mastery_config_from_settings(settings)
        anchor_str = settings.get("_decay_anchor")
        if not anchor_str:
            settings["_decay_anchor"] = today.isoformat()
            _write_settings_json(conn, uid, settings)
            continue
        try:
            anchor = date.fromisoformat(anchor_str)
        except ValueError:
            anchor = today

        if cfg.decay_amount <= 0:
            # 忘却曲線オフ: 未適用日数を溜めない(将来オンにした際に大量に
            # 遡って減衰しないよう、アンカーだけ進める)。
            if anchor != today:
                settings["_decay_anchor"] = today.isoformat()
                _write_settings_json(conn, uid, settings)
            continue

        elapsed_days = (today - anchor).days
        intervals = elapsed_days // cfg.decay_interval_days
        if intervals <= 0:
            continue

        drop = intervals * cfg.decay_amount
        for tbl in ("user_word_progress", "user_phrase_progress"):
            # perfect=1(「完全に覚えた」)は忘却曲線の対象外(2026-08-18)。
            conn.execute(
                f"UPDATE {tbl} SET mastery = MAX({MASTERY_MIN}, mastery - ?) "
                "WHERE user_id = ? AND perfect = 0",
                (drop, uid),
            )
        new_anchor = anchor + timedelta(
            days=intervals * cfg.decay_interval_days)
        settings["_decay_anchor"] = new_anchor.isoformat()
        _write_settings_json(conn, uid, settings)
        applied += 1
    return applied


# 後方互換: 旧名で呼ばれても新しい忘却曲線ロジックを実行する。
def apply_weekly_decay(conn: sqlite3.Connection) -> int:
    return apply_forgetting_decay(conn)


def apply_monthly_decay(conn: sqlite3.Connection) -> int:
    return apply_forgetting_decay(conn)
