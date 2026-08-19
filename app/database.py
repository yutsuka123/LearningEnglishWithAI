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

-- 単語の複数分野タグ付け（§B17・論点1-a）。words.domain は「主分類」
-- として残したまま、同じ意味で複数分野に該当する語をここに追加登録する
-- （例: engagement を「恋愛」を主分類にしつつ「冠婚葬祭」にもタグ付け）。
-- 「同綴りだが意味が違う語」(agentのIT用語/スパイ用語等)は、この仕組みでは
-- なく別々のwords行として登録する(§論点1-b、resolve API側で対応)。
CREATE TABLE IF NOT EXISTS word_domain_tags (
    word_id    INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    domain     TEXT    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (word_id, domain)
);

-- 未ログイン訪問者向けランディング(このアプリについて)ページのアクセス
-- ログ（2026-08-11・B1着手前の状況把握用）。IPで同一人物かどうかの
-- 目安を付ける（厳密な識別ではないが最低限の可視化には十分）。
CREATE TABLE IF NOT EXISTS landing_visits (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ip         TEXT    DEFAULT '',
    path       TEXT    DEFAULT '',
    user_agent TEXT    DEFAULT '',
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- ログイン試行ログ（成功/失敗とも記録・管理画面のログ確認用・
-- 2026-08-13ユーザー要望）。失敗ロックの判定(auth.login_locked)は
-- 従来通りメモリ上のカウンタで行い、こちらは可視化専用の記録。
CREATE TABLE IF NOT EXISTS login_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT    NOT NULL,
    ip         TEXT    DEFAULT '',
    success    INTEGER NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
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

-- フレーズ帳(deckのフレーズ版・2026-08-09)。分野の代わりにscene、単語の
-- 代わりにphraseで、decks/deck_words/deck_progressと全く同じ構造にする。
CREATE TABLE IF NOT EXISTS phrase_decks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name       TEXT    NOT NULL,
    settings   TEXT    DEFAULT '{}',
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS deck_phrases (
    deck_id   INTEGER NOT NULL REFERENCES phrase_decks(id) ON DELETE CASCADE,
    phrase_id INTEGER NOT NULL REFERENCES phrases(id) ON DELETE CASCADE,
    PRIMARY KEY (deck_id, phrase_id)
);
CREATE TABLE IF NOT EXISTS phrase_deck_progress (
    deck_id       INTEGER NOT NULL REFERENCES phrase_decks(id) ON DELETE CASCADE,
    phrase_id     INTEGER NOT NULL,
    correct_count INTEGER NOT NULL DEFAULT 0,
    done_at       TEXT,
    PRIMARY KEY (deck_id, phrase_id)
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
    -- 「完全に覚えた」フラグ(2026-08-18)。1のときは忘却曲線の対象から
    -- 除外される(apply_forgetting_decayが減衰させない)。「解除」で0に戻す。
    perfect       INTEGER NOT NULL DEFAULT 0,
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

-- 会話/読/書/文学カテゴリの習熟度（per-user）。カテゴリ名自体(area/grp/name)は
-- 共有、習熟度だけ user 別（旧: categories.mastery 直書きは全員で共有/混在
-- していたバグのため2026-08-08に分離）。
CREATE TABLE IF NOT EXISTS user_category_progress (
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id  INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    mastery      INTEGER NOT NULL DEFAULT 0,
    last_studied TEXT,
    study_count  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, category_id)
);

-- リスニングトピックの理解度（per-user）。トピック自体(source/accent)は
-- 共有、理解度・弱点メモだけ user 別（同上の理由で分離）。
CREATE TABLE IF NOT EXISTS user_listening_progress (
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id      INTEGER NOT NULL REFERENCES listening_topics(id) ON DELETE CASCADE,
    comprehension INTEGER NOT NULL DEFAULT 0,
    weak_areas    TEXT DEFAULT '',
    study_count   INTEGER NOT NULL DEFAULT 0,
    last_studied  TEXT,
    PRIMARY KEY (user_id, topic_id)
);

-- per-user 設定（端末非依存。ブラウザlocalStorageの同期先）。JSON文字列。
CREATE TABLE IF NOT EXISTS user_settings (
    user_id   INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    settings  TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- user_settingsの変更前スナップショット(直近3件・2026-08-19)。設定の
-- 誤操作/バグからの復旧用。上書きのたび古い値をここへ退避し、4件目
-- 以降は古い順に削除する
-- (app/routers/system.pyの_save_user_settings)。
CREATE TABLE IF NOT EXISTS user_settings_backups (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    settings   TEXT    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_user_settings_backups_user
    ON user_settings_backups(user_id, created_at);

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
    perfect       INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, phrase_id)
);

-- チャージキー（BASE等で手売りする招待コードのセルフサービス償還用）。
-- key_id = 固定値4+ユニークID7+CRC1桁(常時表示可・伏字にしない)。
-- id(AUTOINCREMENT)をFeistel変換した値からユニークIDを作るため、id自体が
-- 事実上の連番シード。シークレット4桁は平文を保存せずハッシュのみ保持。
CREATE TABLE IF NOT EXISTS charge_keys (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id          TEXT    NOT NULL UNIQUE,
    secret_hash     TEXT    NOT NULL,
    amount_jpy      INTEGER NOT NULL,
    pattern         TEXT    NOT NULL,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    used_at         TEXT,
    used_by_user_id INTEGER REFERENCES users(id)
);

-- 残高(balance_jpy)増減の台帳（2026-08-18・不正/入力ミスがあったとき
-- 「いつ・誰の残高が・何によって・いくら変わったか」を追跡できるようにする
-- 目的。auth.add_balance() を呼ぶ全経路（キー償還・管理者による手動調整）が
-- 必ず1行ずつ記録する。delta_jpyは符号付き（マイナス=減額調整）。
CREATE TABLE IF NOT EXISTS balance_ledger (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER NOT NULL REFERENCES users(id),
    delta_jpy      REAL    NOT NULL,
    balance_after  REAL    NOT NULL,
    reason         TEXT    NOT NULL,  -- 'charge_key_redeem' | 'admin_adjustment'
    note           TEXT    NOT NULL DEFAULT '',
    charge_key_id  INTEGER REFERENCES charge_keys(id),
    admin_user_id  INTEGER REFERENCES users(id),
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- チャージキー入力の試行ログ（成功/失敗とも・2026-08-19・ユーザー要望
-- 「キー関係は無期限でログを残す」。app.logはローテーション
-- (10MB×15世代)で古い分が消えるため、監査目的ではこちらのDBテーブルを
-- 正とする（pruneスクリプトの対象にも入れない＝無期限保持）。
-- result: 'redeemed'(成功) | 'used'(使用済み/失効済み)
--         | 'invalid'(存在しない/シークレット不一致・入力ミス含む)。
-- charge_key_idはkey_idがDB上の既存キーに一致した場合のみ埋まる
-- (redeemed/usedは常に埋まる。invalidはシークレット不一致なら埋まり、
-- key_id自体が存在しなければNULL)。key_id_hashは平文のキー番号を残さず
-- 「同じキーへの再試行か」を追えるようにするための一方向ハッシュ
-- (secretは含めない＝ハッシュからオフライン総当たりの近道にならない)。
CREATE TABLE IF NOT EXISTS charge_key_attempts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER REFERENCES users(id),
    ip             TEXT    DEFAULT '',
    result         TEXT    NOT NULL,
    charge_key_id  INTEGER REFERENCES charge_keys(id),
    key_id_hash    TEXT    DEFAULT '',
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_charge_key_attempts_user
    ON charge_key_attempts(user_id, created_at);

-- BASE注文フルフィルメントの操作ログ（2026-08-19・ユーザー要望「無期限で
-- 残す」）。base_orders自体は元々削除されない設計だが、「誰が/いつ」
-- 発行・配送済み・キャンセルにしたかは記録していなかったため追加する。
-- action: 'added'(注文追加・手入力) | 'synced'(BASE API自動検知)
--         | 'issued'(キー発行) | 'reissued'(再発行) | 'delivered'(配送済み)
--         | 'cancelled'(キャンセル)。admin_user_idは自動同期(synced)では
-- NULL(人手の操作ではないため)。
CREATE TABLE IF NOT EXISTS base_order_actions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id       INTEGER NOT NULL REFERENCES base_orders(id) ON DELETE CASCADE,
    action         TEXT    NOT NULL,
    admin_user_id  INTEGER REFERENCES users(id),
    note           TEXT    DEFAULT '',
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_base_order_actions_order
    ON base_order_actions(order_id, created_at);

-- お問い合わせ・要望フォーム（2026-08-06・手動対応前提。自動振り分け等は
-- 将来検討）。管理者が一覧で確認し、status を手動で更新する運用。
CREATE TABLE IF NOT EXISTS inquiries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    kind       TEXT    NOT NULL DEFAULT '要望',
    name       TEXT    NOT NULL DEFAULT '',
    email      TEXT    NOT NULL DEFAULT '',
    content    TEXT    NOT NULL,
    status     TEXT    NOT NULL DEFAULT '未対応',
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- BASE API連携のOAuthトークン保管（2026-08-18・注文自動検知用）。
-- 単一ショップ運用のため1行のみ想定(id=1固定)。平文で保持するが本テーブルは
-- 管理者専用API/内部処理からしか読めない(通常のuser向けAPIには一切露出しない)。
CREATE TABLE IF NOT EXISTS base_api_tokens (
    id            INTEGER PRIMARY KEY CHECK (id = 1),
    access_token  TEXT    NOT NULL,
    refresh_token TEXT    NOT NULL,
    expires_at    TEXT    NOT NULL,
    scope         TEXT    NOT NULL DEFAULT '',
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- BASE注文のフルフィルメント台帳（2026-08-09・チャージキーの手動/半自動
-- 配送を「見逃さない」ための管理用）。base_order_id はBASE APIまたは手入力で
-- 記録。charge_key_id は割り当てたキーの参照のみ（平文はここに保存しない・
-- 発行APIの応答で一度だけ返す）。status = pending / delivered / cancelled。
CREATE TABLE IF NOT EXISTS base_orders (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    base_order_id  TEXT    UNIQUE,
    amount_jpy     INTEGER NOT NULL,
    pt_to_grant    INTEGER NOT NULL,
    product_label  TEXT    NOT NULL DEFAULT '',
    buyer_name     TEXT    NOT NULL DEFAULT '',
    buyer_email    TEXT    NOT NULL DEFAULT '',
    charge_key_id  INTEGER REFERENCES charge_keys(id),
    status         TEXT    NOT NULL DEFAULT 'pending',
    note           TEXT    NOT NULL DEFAULT '',
    detected_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    delivered_at   TEXT
);

-- 利用状況イベントログ（2026-08-17・管理画面の分析用）。
-- kind: 'page'(画面表示) | 'play'(音声再生) | 'click'(ボタン押下)。
-- category/label の意味は kind により異なる（記録元を参照）:
--   page:  category=タブID(例 'vocab') / label=タブの日本語名
--   play:  category=再生機能(例 'word'/'word_example'/'phrase'/
--          'reading_tts'/'listening_tts'/'tts') / label=声・速度等の詳細
--   click: category=押されたときの画面(タブID) / label=ボタンの文言
-- user_id は auth.current_user_id() をそのまま入れる（ゲストは疑似ユーザー
-- idが入るため、users.username='guest'等で判別可能）。集計はSQL側で
-- created_at/ip/user_id/category/labelを自由に組み合わせて行う。
CREATE TABLE IF NOT EXISTS usage_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER,
    ip         TEXT    DEFAULT '',
    kind       TEXT    NOT NULL,
    category   TEXT    NOT NULL DEFAULT '',
    label      TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_usage_events_kind
    ON usage_events(kind, created_at);
CREATE INDEX IF NOT EXISTS idx_usage_events_ip ON usage_events(ip);
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
    if "detail" not in pcols:  # 詳細情報(JSON)のキャッシュ（フレーズ版）
        conn.execute("ALTER TABLE phrases ADD COLUMN detail TEXT DEFAULT ''")
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
    acols = {r["name"] for r in conn.execute(
        "PRAGMA table_info(audio_blobs)")}
    if "text_hash" not in acols:  # 番号↔テキストのズレ対策(2026-08-05)
        conn.execute(
            "ALTER TABLE audio_blobs ADD COLUMN text_hash "
            "TEXT DEFAULT ''")
    # 「完全に覚えた」フラグ(2026-08-18・忘却曲線から除外する用)。
    _add_col(conn, "user_word_progress", "perfect",
             "perfect INTEGER NOT NULL DEFAULT 0")
    _add_col(conn, "user_phrase_progress", "perfect",
             "perfect INTEGER NOT NULL DEFAULT 0")
    # チャージキーの無効化(2026-08-18・注文の再発行時に旧キーを失効させ、
    # 1注文につき常に「有効なキーは最大1本」にするため)。
    _add_col(conn, "charge_keys", "revoked_at", "revoked_at TEXT")
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
    # ai_usage に ip を付与（既定空文字＝アカウント共有の異常検知用・E2）。
    _add_col(conn, "ai_usage", "ip", "ip TEXT DEFAULT ''")
    # users に session_epoch を付与（既定0＝セッション個別無効化用・B4）。
    # ログインCookieにこの世代番号を埋め込み、DB側の現在値と食い違えば
    # 無効なセッションとして扱う。値を+1すると、そのユーザーの既存の
    # 全セッションだけを一括で強制ログアウトできる。
    _add_col(conn, "users", "session_epoch",
             "session_epoch INTEGER NOT NULL DEFAULT 0")
    # 登録画面拡充（2026-08-13・ユーザー指示）: 氏名/フリガナ(必須項目)＋
    # 任意アンケート(職業/年代/性別/目的/流入経路/自由記入欄)。
    # survey_occupation_category/detail・survey_interest_areasは同日中に
    # 職業の大分類→小分類(複数チェック)＋興味のある分野(複数チェック)へ
    # 拡張した際の追加列（旧survey_occupationは新フォームでは未使用だが
    # 列自体は互換のため残す）。
    for col in ("full_name", "furigana", "survey_occupation",
                "survey_occupation_category", "survey_occupation_detail",
                "survey_age_group", "survey_gender", "survey_purpose",
                "survey_referral", "survey_free_text",
                "survey_interest_areas"):
        _add_col(conn, "users", col, f"{col} TEXT DEFAULT ''")
    _migrate_membership_status(conn)
    _migrate_public_samples(conn)


def _migrate_public_samples(conn: sqlite3.Connection) -> None:
    """未ログインでも安全に見せられる「サンプル教材」の印(2026-08-12)。
    `materials`は本来ログイン必須(実際の生成物を含みうる)だが、意図的に
    作成したサンプル(area='reading'/'listening'/'writing_sample'/
    'conversation_sample')だけは`GET /api/learn/samples`
    (`app/routers/learn.py`)経由でゲストにも公開する。area単体では
    reading/listeningの実データと区別できないため、この列で明示的に
    印を付ける。"""
    have_col = "is_public_sample" in {
        r["name"] for r in conn.execute("PRAGMA table_info(materials)")}
    _add_col(conn, "materials", "is_public_sample",
             "is_public_sample INTEGER NOT NULL DEFAULT 0")
    if not have_col:
        # 2026-08-12に作成した40件のサンプルは、タイトルに共通の
        # 「・サンプル)」マーカーが入っている（生成時の命名規則）。
        # 列を新規追加したこの瞬間の一回限りでバックフィルする
        # (Wチェック監査(fable)で指摘・2026-08-12修正: 以前は毎起動で
        # このUPDATEが走り続けており、field/destination等の自由入力欄
        # (`app/routers/learn.py`の`generate`/`trip_prep`)にユーザーが
        # 偶然/意図的に同じ文字列を含めると、次回起動時に**自分の生成物
        # が全ユーザー・未ログインゲストにまで公開されてしまう**穴が
        # あった。今後この文字列一致による自動公開は二度と走らない)。
        conn.execute(
            "UPDATE materials SET is_public_sample = 1 "
            "WHERE is_public_sample = 0 AND title LIKE '%・サンプル)%'"
        )
    # セキュリティ修正(2026-08-12・第2回監査で発見): materialsに所有者が
    # 無く、/api/learn/materials系が全ユーザーの生成物(出張準備で貼り付けた
    # 自社資料等の機密を含みうる)を無差別に返していた重大な情報漏えい。
    # user_idを追加しread側で絞り込む(app/routers/learn.py参照)。
    # 既存行(所有者不明)はis_public_sample=1のもの以外、暫定でオーナー
    # (id=1)に帰属させる(このバグの発生当時は実質オーナー本人の生成物が
    # 大半だったため。以後の生成は都度current_user_id()を記録する)。
    _add_col(conn, "materials", "user_id", "user_id INTEGER")
    conn.execute(
        "UPDATE materials SET user_id = ? "
        "WHERE user_id IS NULL AND is_public_sample = 0",
        (OWNER_USER_ID,),
    )


def _migrate_membership_status(conn: sqlite3.Connection) -> None:
    """会員ステータス（ゴールド/シルバー/ブロンズ等）の土台(2026-08-12)。
    称号の判定条件・pt割引率・達成時のpt付与ロジックは今後検討・未実装。
    ここでは値を保持するための列だけを用意する（拡張の余地を残す目的）。
    会員登録年月日は既存の`users.created_at`を流用し、学習数は
    `word_attempts`/`phrase_attempts`等から算出可能なため、ここでは
    重複して持たない。"""
    _add_col(conn, "users", "membership_tier",
             "membership_tier TEXT NOT NULL DEFAULT 'bronze'")
    _add_col(conn, "users", "membership_tier_since",
             "membership_tier_since TEXT")
    _add_col(conn, "users", "membership_tier_change_count",
             "membership_tier_change_count INTEGER NOT NULL DEFAULT 0")
    # ゴールド/シルバー/ブロンズとは別軸の称号用リザーブ（用途未定）。
    _add_col(conn, "users", "membership_title_reserve",
             "membership_title_reserve TEXT")
    # 利用時間の累計（秒）。集計ロジック(セッション計測等)は未実装で常に0。
    _add_col(conn, "users", "usage_seconds_total",
             "usage_seconds_total INTEGER NOT NULL DEFAULT 0")
    # 汎用リザーブ（用途未定・将来の項目追加用）。
    _add_col(conn, "users", "status_reserve_1", "status_reserve_1 TEXT")
    _add_col(conn, "users", "status_reserve_2", "status_reserve_2 TEXT")

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
