"""SQLite database: connection management, schema, and seed data.

Uses the Python standard-library ``sqlite3`` module (no native build step),
so it works identically on Windows and macOS. The database file lives under
the data directory defined in :mod:`app.config`.
"""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date
from typing import Iterator

from .config import paths

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE IF NOT EXISTS words (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    english       TEXT    NOT NULL,
    japanese      TEXT    NOT NULL,
    part_of_speech TEXT   DEFAULT '',
    example       TEXT    DEFAULT '',
    mastery       INTEGER NOT NULL DEFAULT 0,   -- 0..100
    last_studied  TEXT,                          -- ISO date
    level         TEXT    DEFAULT '',            -- 600/700/800 等
    domain        TEXT    DEFAULT '',            -- 宗教/文学/口語/IT 等
    times_asked   INTEGER NOT NULL DEFAULT 0,
    times_correct INTEGER NOT NULL DEFAULT 0,
    -- Per-direction counters (英→日 / 日→英) for accuracy display.
    ask_en2ja     INTEGER NOT NULL DEFAULT 0,
    ok_en2ja      INTEGER NOT NULL DEFAULT 0,
    ask_ja2en     INTEGER NOT NULL DEFAULT 0,
    ok_ja2en      INTEGER NOT NULL DEFAULT 0,
    -- Forgetting-curve schedule (Leitner-style box + due date).
    review_level  INTEGER NOT NULL DEFAULT 0,
    next_review   TEXT,                          -- ISO date when due again
    created_at    TEXT    NOT NULL DEFAULT (date('now'))
);

-- Per-attempt log so we can award +5 only when BOTH directions are correct.
CREATE TABLE IF NOT EXISTS word_attempts (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id   INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    direction TEXT    NOT NULL,                  -- 'ja2en' | 'en2ja'
    correct   INTEGER NOT NULL,                  -- 0 | 1
    created_at TEXT   NOT NULL DEFAULT (datetime('now'))
);

-- Generic mastery-tracked categories for 会話/リーディング/ライティング/文学.
CREATE TABLE IF NOT EXISTS categories (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    area         TEXT    NOT NULL,   -- conversation/reading/writing/literature
    grp          TEXT    DEFAULT '', -- 日常会話 / ビジネス / IT / 旅行 ...
    name         TEXT    NOT NULL,
    mastery      INTEGER NOT NULL DEFAULT 0,
    last_studied TEXT,
    study_count  INTEGER NOT NULL DEFAULT 0,
    UNIQUE(area, grp, name)
);

-- Listening has extra fields (accent, weak areas, comprehension).
CREATE TABLE IF NOT EXISTS listening_topics (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source        TEXT NOT NULL,    -- 映画/ドラマ/YouTube/ニュース
    accent        TEXT DEFAULT '',  -- アメリカ英語 / イギリス英語
    comprehension INTEGER NOT NULL DEFAULT 0,  -- 0..100
    weak_areas    TEXT DEFAULT '',
    study_count   INTEGER NOT NULL DEFAULT 0,
    last_studied  TEXT,
    UNIQUE(source, accent)
);

-- Generated study materials (news / literature / reading passages, etc.).
CREATE TABLE IF NOT EXISTS materials (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    area        TEXT NOT NULL,      -- 'news' | 'reading' | 'literature' | ...
    field       TEXT DEFAULT '',    -- 経済/AI/IT/軍事/政治/文化 or category
    title       TEXT NOT NULL,
    body        TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- One row per study session (the daily 学習履歴).
CREATE TABLE IF NOT EXISTS study_sessions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    study_date   TEXT NOT NULL DEFAULT (date('now')),
    content      TEXT DEFAULT '',   -- 今日学んだ内容
    accuracy     INTEGER,           -- 0..100, nullable
    weak_points  TEXT DEFAULT '',
    next_topic   TEXT DEFAULT '',
    new_words    TEXT DEFAULT '',
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Mini-phrases (ミニフレーズ): short useful expressions, mastery-tracked
-- the same way as words (both directions + forgetting curve).
CREATE TABLE IF NOT EXISTS phrases (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    english      TEXT NOT NULL,
    japanese     TEXT NOT NULL,
    scene        TEXT DEFAULT '',   -- 日常 / 映画 / ニュース ...
    mastery      INTEGER NOT NULL DEFAULT 0,
    last_studied TEXT,
    study_count  INTEGER NOT NULL DEFAULT 0,
    times_asked   INTEGER NOT NULL DEFAULT 0,
    times_correct INTEGER NOT NULL DEFAULT 0,
    ask_en2ja     INTEGER NOT NULL DEFAULT 0,
    ok_en2ja      INTEGER NOT NULL DEFAULT 0,
    ask_ja2en     INTEGER NOT NULL DEFAULT 0,
    ok_ja2en      INTEGER NOT NULL DEFAULT 0,
    review_level  INTEGER NOT NULL DEFAULT 0,
    next_review   TEXT
);

CREATE TABLE IF NOT EXISTS phrase_attempts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    phrase_id  INTEGER NOT NULL REFERENCES phrases(id) ON DELETE CASCADE,
    direction  TEXT    NOT NULL,
    correct    INTEGER NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- AI token usage + estimated cost, one row per call (§ usage/cost display).
CREATE TABLE IF NOT EXISTS ai_usage (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    model         TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd      REAL NOT NULL DEFAULT 0,
    feature       TEXT DEFAULT '',
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Free-conversation log (used so the level judge can see real production).
CREATE TABLE IF NOT EXISTS conversation_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    role       TEXT NOT NULL,      -- 'user' | 'assistant'
    content    TEXT NOT NULL,
    mode       TEXT DEFAULT '',    -- 'free' | scene name
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Key/value store: decay bookkeeping, API key override, etc.
CREATE TABLE IF NOT EXISTS app_state (
    key   TEXT PRIMARY KEY,
    value TEXT
);

-- 単語帳(デッキ): 分野/レベル等で作る自分用の単語セット。設定は JSON。
CREATE TABLE IF NOT EXISTS decks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    settings   TEXT    DEFAULT '{}',   -- 出題方向/合格回数/SRS/出題数 等
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS deck_words (
    deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    PRIMARY KEY (deck_id, word_id)
);
-- デッキ別の進捗（N回正解で done。グローバルの mastery とは別管理）。
CREATE TABLE IF NOT EXISTS deck_progress (
    deck_id       INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    word_id       INTEGER NOT NULL,
    correct_count INTEGER NOT NULL DEFAULT 0,
    done_at       TEXT,
    PRIMARY KEY (deck_id, word_id)
);

-- Generated TTS audio, keyed by item (番号) + kind + voice. Lets repeated
-- playback be free (no API token) and supports DB(BLOB) storage as an
-- alternative to on-disk files (AUDIO_STORAGE=db|hybrid). One row per
-- (item_type, item_id, kind, voice).
CREATE TABLE IF NOT EXISTS audio_blobs (
    item_type  TEXT    NOT NULL,   -- 'word' | 'phrase'
    item_id    INTEGER NOT NULL,
    kind       TEXT    NOT NULL,   -- 'word' | 'example' | 'phrase'
    voice      TEXT    NOT NULL,   -- 'ash' | 'nova' ...
    mp3        BLOB    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (item_type, item_id, kind, voice)
);

-- ===== マルチユーザー化（§A）=====================================
-- コンテンツ(words/phrases/materials/audio)は全員共有のまま、進捗だけ
-- user 別に分離する。ローカル単一ユーザーは owner(id=1) に集約され、
-- MULTIUSER=0 のときは自動 owner ログインで従来どおり無認証で動く。
CREATE TABLE IF NOT EXISTS users (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    username            TEXT    NOT NULL UNIQUE,
    password_hash       TEXT    NOT NULL DEFAULT '',  -- pbkdf2$...（空=未設定）
    role                TEXT    NOT NULL DEFAULT 'user',  -- 'admin' | 'user'
    is_active           INTEGER NOT NULL DEFAULT 1,
    display_name        TEXT    DEFAULT '',
    email               TEXT    DEFAULT '',   -- 将来のメール/2FA用（任意）
    -- AI利用ガード（per-user）。NULL/0 ならグローバル既定にフォールバック。
    daily_cost_cap_usd   REAL,
    monthly_cost_cap_usd REAL,
    -- 前払いチャージ残高（¥）。日次/月次の無料枠とは別管理。枠に到達した後の
    -- 利用でのみ消費される（NULL/0 なら枠到達で停止）。
    balance_jpy         REAL,
    -- 禁止用語の許可（§E）。既定0=不可。1で表示/出題を許可。
    allow_banned        INTEGER NOT NULL DEFAULT 0,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- 単語の進捗（per-user）。words 本体の mastery/SRS 列の置き換え先。
CREATE TABLE IF NOT EXISTS user_word_progress (
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    word_id       INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    mastery       INTEGER NOT NULL DEFAULT 0,
    last_studied  TEXT,
    times_asked   INTEGER NOT NULL DEFAULT 0,
    times_correct INTEGER NOT NULL DEFAULT 0,
    ask_en2ja     INTEGER NOT NULL DEFAULT 0,
    ok_en2ja      INTEGER NOT NULL DEFAULT 0,
    ask_ja2en     INTEGER NOT NULL DEFAULT 0,
    ok_ja2en      INTEGER NOT NULL DEFAULT 0,
    review_level  INTEGER NOT NULL DEFAULT 0,
    next_review   TEXT,
    PRIMARY KEY (user_id, word_id)
);

-- リーディング/リスニング教材の学習履歴（per-user）。教材本文・音声は共有、
-- 既読/覚えた(mastery)だけ user 別。
CREATE TABLE IF NOT EXISTS user_material_progress (
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    material_id  INTEGER NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    mastery      INTEGER NOT NULL DEFAULT 0,
    last_studied TEXT,
    PRIMARY KEY (user_id, material_id)
);

-- per-user 設定（端末非依存。ブラウザlocalStorageの同期先）。JSON文字列。
CREATE TABLE IF NOT EXISTS user_settings (
    user_id   INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    settings  TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- フレーズの進捗（per-user）。
CREATE TABLE IF NOT EXISTS user_phrase_progress (
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    phrase_id     INTEGER NOT NULL REFERENCES phrases(id) ON DELETE CASCADE,
    mastery       INTEGER NOT NULL DEFAULT 0,
    last_studied  TEXT,
    study_count   INTEGER NOT NULL DEFAULT 0,
    times_asked   INTEGER NOT NULL DEFAULT 0,
    times_correct INTEGER NOT NULL DEFAULT 0,
    ask_en2ja     INTEGER NOT NULL DEFAULT 0,
    ok_en2ja      INTEGER NOT NULL DEFAULT 0,
    ask_ja2en     INTEGER NOT NULL DEFAULT 0,
    ok_ja2en      INTEGER NOT NULL DEFAULT 0,
    review_level  INTEGER NOT NULL DEFAULT 0,
    next_review   TEXT,
    PRIMARY KEY (user_id, phrase_id)
);
"""


def _seed_phrases(conn: sqlite3.Connection) -> None:
    """Top-up: insert any seed phrase whose English isn't already present."""
    from .seed_data import PHRASES

    existing = {
        r["english"].lower()
        for r in conn.execute("SELECT english FROM phrases").fetchall()
    }
    new_rows = [p for p in PHRASES if p[0].lower() not in existing]
    if new_rows:
        conn.executemany(
            "INSERT INTO phrases (english, japanese, scene) VALUES (?, ?, ?)",
            new_rows,
        )


def get_connection() -> sqlite3.Connection:
    """Open a connection with sensible defaults (FK on, row dicts, WAL)."""
    paths.ensure()
    conn = sqlite3.connect(paths.db_file)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def db() -> Iterator[sqlite3.Connection]:
    """Connection that commits on success and rolls back on error."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Seed data (categories from the requirements doc)
# ---------------------------------------------------------------------------

CONVERSATION_SEED = {
    "日常会話": [
        "挨拶", "買い物", "スーパー", "レストランの注文", "道案内",
        "電車", "ご近所さんとの会話",
    ],
    "外国人対応": [
        "道を聞かれたとき", "通してください", "聞き取れないとき",
        "ゆっくり話してほしい", "順路の説明", "写真を頼まれる",
    ],
    "旅行・出入国": [
        "入出国・税関", "空港", "ホテル", "観光", "両替・買い物",
    ],
    "ビジネス": [
        "一般会議", "プレゼン", "メール", "チャット", "電話", "雑談",
    ],
    "IT・開発": [
        "ソフトウェア開発", "組み込み開発", "ビルド", "ビルドエラー",
        "デバッグ", "開発会議", "AI", "API", "IT用語",
    ],
    "専門用語": [
        "機械系用語", "AI系用語", "AIへの指示で使う英語",
    ],
    "試験・進学": [
        "TOEIC頻出 (500-800)", "留学に必要な英語", "面接",
    ],
}

READING_SEED = {
    "一般": ["日常文書", "新聞", "雑誌"],
    "ビジネス": ["メール", "問い合わせ"],
    "IT": ["技術文書", "API仕様書", "エラーメッセージ", "ビルドログ"],
    "教養": ["歴史", "文化", "エンタメ", "科学"],
}

# News fields (topics + regions) the learner asked for.
NEWS_FIELDS = [
    "政治", "経済", "エンタメ", "軍事", "AI", "IT", "文化", "科学",
    "米国", "英国", "日本", "中国", "香港", "豪州", "ドイツ", "フランス",
]

# Accents to compare / practise (米語と英語 ほか).
ACCENTS = ["アメリカ英語", "イギリス英語", "オーストラリア英語"]

WRITING_SEED = {
    "": ["日常文章", "ビジネスメール", "IT文書", "技術仕様書"],
}

LITERATURE_SEED = {
    "": ["Shakespeare", "英文学", "古典文学"],
}

LISTENING_SEED = [
    ("映画", "アメリカ英語"),
    ("映画", "イギリス英語"),
    ("ドラマ", "アメリカ英語"),
    ("ドラマ", "イギリス英語"),
    ("YouTube", "アメリカ英語"),
    ("ニュース", "アメリカ英語"),
    ("ニュース", "イギリス英語"),
]


def _seed_categories(conn: sqlite3.Connection) -> None:
    rows: list[tuple[str, str, str]] = []
    for grp, names in CONVERSATION_SEED.items():
        rows += [("conversation", grp, n) for n in names]
    for grp, names in READING_SEED.items():
        rows += [("reading", grp, n) for n in names]
    for grp, names in WRITING_SEED.items():
        rows += [("writing", grp, n) for n in names]
    for grp, names in LITERATURE_SEED.items():
        rows += [("literature", grp, n) for n in names]
    conn.executemany(
        "INSERT OR IGNORE INTO categories (area, grp, name) VALUES (?, ?, ?)",
        rows,
    )


def _seed_listening(conn: sqlite3.Connection) -> None:
    conn.executemany(
        "INSERT OR IGNORE INTO listening_topics (source, accent) "
        "VALUES (?, ?)",
        LISTENING_SEED,
    )


def _seed_words(conn: sqlite3.Connection) -> None:
    """Top-up: insert any seed word whose English isn't already present.
    De-duplicates against the DB AND within the combined list (case-insensitive)
    so the seed can grow over time without creating duplicate rows."""
    from .seed_data import WORDS
    from .seed_toeic import TOEIC_WORDS

    seen = {
        r["english"].lower()
        for r in conn.execute("SELECT english FROM words").fetchall()
    }
    new_rows = []
    for w in [*WORDS, *TOEIC_WORDS]:
        key = w[0].strip().lower()
        if key and key not in seen:
            seen.add(key)
            new_rows.append(w)
    if new_rows:
        conn.executemany(
            "INSERT INTO words (english, japanese, part_of_speech, example) "
            "VALUES (?, ?, ?, ?)",
            new_rows,
        )


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns introduced after the first release (idempotent)."""
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(words)")}
    if "level" not in cols:
        conn.execute("ALTER TABLE words ADD COLUMN level TEXT DEFAULT ''")
    if "domain" not in cols:
        conn.execute("ALTER TABLE words ADD COLUMN domain TEXT DEFAULT ''")
    if "detail" not in cols:  # 詳細情報(JSON)のキャッシュ
        conn.execute("ALTER TABLE words ADD COLUMN detail TEXT DEFAULT ''")
    pcols = {r["name"] for r in conn.execute("PRAGMA table_info(phrases)")}
    if "level" not in pcols:  # フレーズの難易度
        conn.execute("ALTER TABLE phrases ADD COLUMN level TEXT DEFAULT ''")
    mcols = {r["name"] for r in conn.execute("PRAGMA table_info(materials)")}
    if "mastery" not in mcols:
        conn.execute(
            "ALTER TABLE materials ADD COLUMN mastery INTEGER DEFAULT 0")
    scols = {r["name"] for r in conn.execute(
        "PRAGMA table_info(study_sessions)")}
    if "session_key" not in scols:  # 会話の自動記録を上書きするためのキー
        conn.execute(
            "ALTER TABLE study_sessions ADD COLUMN session_key "
            "TEXT DEFAULT ''")
    _migrate_multiuser(conn)


def _add_col(conn: sqlite3.Connection, table: str, col: str,
             ddl: str) -> None:
    """Add a column if it does not yet exist (idempotent)."""
    have = {r["name"] for r in conn.execute(
        f"PRAGMA table_info({table})")}
    if col not in have:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {ddl}")


# owner(=ローカル単一ユーザー)の固定 id。MULTIUSER=0 はこの user で動く。
OWNER_USER_ID = 1


def _migrate_multiuser(conn: sqlite3.Connection) -> None:
    """§A: user_id 列の付与 / owner 作成 / 既存進捗の per-user 移行。
    すべて冪等（何度呼んでも安全）。"""
    # 1) 既存テーブルに user_id を付与（既定 owner=1）。
    for tbl in ("ai_usage", "word_attempts", "phrase_attempts",
                "study_sessions", "conversation_log", "deck_progress"):
        _add_col(conn, tbl, "user_id",
                 "user_id INTEGER NOT NULL DEFAULT 1")
    # users に allow_banned（§E・既定0=禁止用語不可）を後付け。
    _add_col(conn, "users", "allow_banned",
             "allow_banned INTEGER NOT NULL DEFAULT 0")
    # decks を per-user に（既存は owner=1）。
    _add_col(conn, "decks", "user_id",
             "user_id INTEGER NOT NULL DEFAULT 1")

    # 2) owner ユーザーを用意（無ければ作成。パスワードは admin.py で設定）。
    n = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if n == 0:
        from .config import settings
        owner = (settings.nickname or "owner").strip() or "owner"
        conn.execute(
            "INSERT INTO users (id, username, role, display_name) "
            "VALUES (?, ?, 'admin', ?)",
            (OWNER_USER_ID, owner, owner),
        )

    # 3) 既存の words/phrases 進捗を owner の per-user テーブルへ初期移行。
    #    PK 衝突は無視（=一度だけ実行され、以後は上書きしない）。進捗のある
    #    行だけ移す（未学習は accessor 側で既定0 として扱う）。
    conn.execute(
        "INSERT OR IGNORE INTO user_word_progress "
        "(user_id, word_id, mastery, last_studied, times_asked, "
        " times_correct, ask_en2ja, ok_en2ja, ask_ja2en, ok_ja2en, "
        " review_level, next_review) "
        "SELECT ?, id, mastery, last_studied, times_asked, times_correct, "
        " ask_en2ja, ok_en2ja, ask_ja2en, ok_ja2en, review_level, "
        " next_review FROM words "
        "WHERE mastery > 0 OR times_asked > 0 OR review_level > 0",
        (OWNER_USER_ID,),
    )
    conn.execute(
        "INSERT OR IGNORE INTO user_phrase_progress "
        "(user_id, phrase_id, mastery, last_studied, study_count, "
        " times_asked, times_correct, ask_en2ja, ok_en2ja, ask_ja2en, "
        " ok_ja2en, review_level, next_review) "
        "SELECT ?, id, mastery, last_studied, study_count, times_asked, "
        " times_correct, ask_en2ja, ok_en2ja, ask_ja2en, ok_ja2en, "
        " review_level, next_review FROM phrases "
        "WHERE mastery > 0 OR times_asked > 0 OR review_level > 0",
        (OWNER_USER_ID,),
    )


def init_db() -> None:
    """Create the schema and seed reference data. Safe to call repeatedly."""
    with db() as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)
        _seed_categories(conn)
        _seed_listening(conn)
        _seed_words(conn)
        _seed_phrases(conn)
        # Record install date for monthly-decay bookkeeping.
        conn.execute(
            "INSERT OR IGNORE INTO app_state (key, value) VALUES "
            "('last_decay_month', ?)",
            (date.today().strftime("%Y-%m"),),
        )
