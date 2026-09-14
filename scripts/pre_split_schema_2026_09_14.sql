-- DB分割(2026-09-14)前の単一vocabulary.db用スキーマの静的スナップショット。
-- `git checkout main -- app/database.py`でinit_db()を実行した直後のDBに
-- `sqlite3 vocabulary.db ".schema"`を実行して生成(データは含まない・
-- 構造のみ)。scripts/reverse_merge_split_db_2026_09_14.py(DB分割の
-- ロールバック/逆マージ用)が、本番のようにgit管理外(rsync配置)の環境
-- でも動くよう、gitのブランチ参照(`git show main:...`等)に頼らず
-- このファイルを直接読む設計にするために保存した。
-- 分割後のapp/database.pyのSCHEMA/_migrate()を変更した場合、このファイルも
-- 追随させること(でないと逆マージ後のvocabulary.dbが最新の列を持たない)。
CREATE TABLE words (
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
, detail TEXT DEFAULT '');
CREATE TABLE word_attempts (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    word_id   INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    direction TEXT    NOT NULL,                  -- 'ja2en' | 'en2ja'
    correct   INTEGER NOT NULL,                  -- 0 | 1
    created_at TEXT   NOT NULL DEFAULT (datetime('now'))
, user_id INTEGER NOT NULL DEFAULT 1);
CREATE TABLE categories (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    area         TEXT    NOT NULL,   -- conversation/reading/writing/literature
    grp          TEXT    DEFAULT '', -- 日常会話 / ビジネス / IT / 旅行 ...
    name         TEXT    NOT NULL,
    mastery      INTEGER NOT NULL DEFAULT 0,
    last_studied TEXT,
    study_count  INTEGER NOT NULL DEFAULT 0,
    UNIQUE(area, grp, name)
);
CREATE TABLE listening_topics (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    source        TEXT NOT NULL,    -- 映画/ドラマ/YouTube/ニュース
    accent        TEXT DEFAULT '',  -- アメリカ英語 / イギリス英語
    comprehension INTEGER NOT NULL DEFAULT 0,  -- 0..100
    weak_areas    TEXT DEFAULT '',
    study_count   INTEGER NOT NULL DEFAULT 0,
    last_studied  TEXT,
    UNIQUE(source, accent)
);
CREATE TABLE materials (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    area        TEXT NOT NULL,      -- 'news' | 'reading' | 'literature' | ...
    field       TEXT DEFAULT '',    -- 経済/AI/IT/軍事/政治/文化 or category
    title       TEXT NOT NULL,
    body        TEXT NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
, mastery INTEGER DEFAULT 0, is_public_sample INTEGER NOT NULL DEFAULT 0, user_id INTEGER);
CREATE TABLE study_sessions (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    study_date   TEXT NOT NULL DEFAULT (date('now')),
    content      TEXT DEFAULT '',   -- 今日学んだ内容
    accuracy     INTEGER,           -- 0..100, nullable
    weak_points  TEXT DEFAULT '',
    next_topic   TEXT DEFAULT '',
    new_words    TEXT DEFAULT '',
    created_at   TEXT NOT NULL DEFAULT (datetime('now'))
, session_key TEXT DEFAULT '', user_id INTEGER NOT NULL DEFAULT 1);
CREATE TABLE phrases (
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
, level TEXT DEFAULT '', detail TEXT DEFAULT '');
CREATE TABLE word_domain_tags (
    word_id    INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    domain     TEXT    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (word_id, domain)
);
CREATE TABLE landing_visits (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ip         TEXT    DEFAULT '',
    path       TEXT    DEFAULT '',
    user_agent TEXT    DEFAULT '',
    kind       TEXT    NOT NULL DEFAULT 'visit',
    success    INTEGER,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
, guest_sid TEXT DEFAULT '', fail_reason TEXT DEFAULT '', is_disposable_email INTEGER DEFAULT 0, accept_language TEXT DEFAULT '');
CREATE INDEX idx_landing_visits_ip ON landing_visits(ip);
CREATE TABLE ip_geo_cache (
    ip         TEXT PRIMARY KEY,
    country    TEXT DEFAULT '',
    region     TEXT DEFAULT '',
    city       TEXT DEFAULT '',
    org        TEXT DEFAULT '',
    hostname   TEXT DEFAULT '',
    error      TEXT DEFAULT '',
    fetched_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE login_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    username   TEXT    NOT NULL,
    ip         TEXT    DEFAULT '',
    hostname   TEXT    DEFAULT '',
    success    INTEGER NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE phrase_attempts (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    phrase_id  INTEGER NOT NULL REFERENCES phrases(id) ON DELETE CASCADE,
    direction  TEXT    NOT NULL,
    correct    INTEGER NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
, user_id INTEGER NOT NULL DEFAULT 1);
CREATE TABLE ai_usage (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    model         TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL DEFAULT 0,
    output_tokens INTEGER NOT NULL DEFAULT 0,
    cost_usd      REAL NOT NULL DEFAULT 0,
    feature       TEXT DEFAULT '',
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
, user_id INTEGER NOT NULL DEFAULT 1, ip TEXT DEFAULT '');
CREATE TABLE conversation_log (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    role       TEXT NOT NULL,      -- 'user' | 'assistant'
    content    TEXT NOT NULL,
    mode       TEXT DEFAULT '',    -- 'free' | scene name
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
, user_id INTEGER NOT NULL DEFAULT 1);
CREATE TABLE app_state (
    key   TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE decks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    settings   TEXT    DEFAULT '{}',   -- 出題方向/合格回数/SRS/出題数 等
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
, user_id INTEGER NOT NULL DEFAULT 1);
CREATE TABLE deck_words (
    deck_id INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    word_id INTEGER NOT NULL REFERENCES words(id) ON DELETE CASCADE,
    PRIMARY KEY (deck_id, word_id)
);
CREATE TABLE deck_progress (
    deck_id       INTEGER NOT NULL REFERENCES decks(id) ON DELETE CASCADE,
    word_id       INTEGER NOT NULL,
    correct_count INTEGER NOT NULL DEFAULT 0,
    done_at       TEXT, user_id INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (deck_id, word_id)
);
CREATE TABLE phrase_decks (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name       TEXT    NOT NULL,
    settings   TEXT    DEFAULT '{}',
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE deck_phrases (
    deck_id   INTEGER NOT NULL REFERENCES phrase_decks(id) ON DELETE CASCADE,
    phrase_id INTEGER NOT NULL REFERENCES phrases(id) ON DELETE CASCADE,
    PRIMARY KEY (deck_id, phrase_id)
);
CREATE TABLE phrase_deck_progress (
    deck_id       INTEGER NOT NULL REFERENCES phrase_decks(id) ON DELETE CASCADE,
    phrase_id     INTEGER NOT NULL,
    correct_count INTEGER NOT NULL DEFAULT 0,
    done_at       TEXT,
    PRIMARY KEY (deck_id, phrase_id)
);
CREATE TABLE audio_blobs (
    item_type  TEXT    NOT NULL,   -- 'word' | 'phrase'
    item_id    INTEGER NOT NULL,
    kind       TEXT    NOT NULL,   -- 'word' | 'example' | 'phrase'
    voice      TEXT    NOT NULL,   -- 'ash' | 'nova' ...
    mp3        BLOB    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now')), text_hash TEXT DEFAULT '',
    PRIMARY KEY (item_type, item_id, kind, voice)
);
CREATE TABLE users (
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
, is_test INTEGER NOT NULL DEFAULT 0, session_epoch INTEGER NOT NULL DEFAULT 0, full_name TEXT DEFAULT '', furigana TEXT DEFAULT '', survey_occupation TEXT DEFAULT '', survey_occupation_category TEXT DEFAULT '', survey_occupation_detail TEXT DEFAULT '', survey_age_group TEXT DEFAULT '', survey_gender TEXT DEFAULT '', survey_purpose TEXT DEFAULT '', survey_referral TEXT DEFAULT '', survey_free_text TEXT DEFAULT '', survey_interest_areas TEXT DEFAULT '', display_name_furigana TEXT DEFAULT '', membership_tier TEXT NOT NULL DEFAULT 'bronze', membership_tier_since TEXT, membership_tier_change_count INTEGER NOT NULL DEFAULT 0, membership_title_reserve TEXT, usage_seconds_total INTEGER NOT NULL DEFAULT 0, status_reserve_1 TEXT, status_reserve_2 TEXT);
CREATE TABLE user_word_progress (
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
CREATE TABLE user_material_progress (
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    material_id  INTEGER NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    mastery      INTEGER NOT NULL DEFAULT 0,
    last_studied TEXT,
    PRIMARY KEY (user_id, material_id)
);
CREATE TABLE user_category_progress (
    user_id      INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category_id  INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    mastery      INTEGER NOT NULL DEFAULT 0,
    last_studied TEXT,
    study_count  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (user_id, category_id)
);
CREATE TABLE user_listening_progress (
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    topic_id      INTEGER NOT NULL REFERENCES listening_topics(id) ON DELETE CASCADE,
    comprehension INTEGER NOT NULL DEFAULT 0,
    weak_areas    TEXT DEFAULT '',
    study_count   INTEGER NOT NULL DEFAULT 0,
    last_studied  TEXT,
    PRIMARY KEY (user_id, topic_id)
);
CREATE TABLE user_settings (
    user_id   INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    settings  TEXT NOT NULL DEFAULT '{}',
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE user_settings_backups (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    settings   TEXT    NOT NULL,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_user_settings_backups_user
    ON user_settings_backups(user_id, created_at);
CREATE TABLE user_phrase_progress (
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
CREATE TABLE charge_keys (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    key_id          TEXT    NOT NULL UNIQUE,
    secret_hash     TEXT    NOT NULL,
    amount_jpy      INTEGER NOT NULL,
    pattern         TEXT    NOT NULL,
    created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
    used_at         TEXT,
    used_by_user_id INTEGER REFERENCES users(id)
, revoked_at TEXT);
CREATE TABLE balance_ledger (
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
CREATE TABLE charge_key_attempts (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id        INTEGER REFERENCES users(id),
    ip             TEXT    DEFAULT '',
    result         TEXT    NOT NULL,
    charge_key_id  INTEGER REFERENCES charge_keys(id),
    key_id_hash    TEXT    DEFAULT '',
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_charge_key_attempts_user
    ON charge_key_attempts(user_id, created_at);
CREATE TABLE base_order_actions (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id       INTEGER NOT NULL REFERENCES base_orders(id) ON DELETE CASCADE,
    action         TEXT    NOT NULL,
    admin_user_id  INTEGER REFERENCES users(id),
    note           TEXT    DEFAULT '',
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_base_order_actions_order
    ON base_order_actions(order_id, created_at);
CREATE TABLE paypay_actions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    action              TEXT    NOT NULL,
    admin_user_id       INTEGER REFERENCES users(id),
    merchant_payment_id TEXT    DEFAULT '',
    code_id             TEXT    DEFAULT '',
    payment_id          TEXT    DEFAULT '',
    amount_jpy          INTEGER,
    status              TEXT    DEFAULT '',
    ok                  INTEGER NOT NULL DEFAULT 1,
    note                TEXT    DEFAULT '',
    created_at          TEXT    NOT NULL DEFAULT (datetime('now'))
, user_id INTEGER REFERENCES users(id));
CREATE INDEX idx_paypay_actions_mpid
    ON paypay_actions(merchant_payment_id, created_at);
CREATE INDEX idx_paypay_actions_created
    ON paypay_actions(created_at);
CREATE TABLE paypay_payments (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL REFERENCES users(id),
    merchant_payment_id TEXT    NOT NULL UNIQUE,
    code_id             TEXT    DEFAULT '',
    payment_id          TEXT    DEFAULT '',
    amount_jpy          INTEGER NOT NULL,
    status              TEXT    NOT NULL DEFAULT 'CREATED',
    credited_at         TEXT,
    created_at          TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at          TEXT    NOT NULL DEFAULT (datetime('now'))
, refunded_at TEXT);
CREATE INDEX idx_paypay_payments_user
    ON paypay_payments(user_id, created_at);
CREATE INDEX idx_paypay_payments_pending
    ON paypay_payments(credited_at, created_at);
CREATE TABLE inquiries (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER REFERENCES users(id) ON DELETE SET NULL,
    kind       TEXT    NOT NULL DEFAULT '要望',
    name       TEXT    NOT NULL DEFAULT '',
    email      TEXT    NOT NULL DEFAULT '',
    content    TEXT    NOT NULL,
    status     TEXT    NOT NULL DEFAULT '未対応',
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE base_api_tokens (
    id            INTEGER PRIMARY KEY CHECK (id = 1),
    access_token  TEXT    NOT NULL,
    refresh_token TEXT    NOT NULL,
    expires_at    TEXT    NOT NULL,
    scope         TEXT    NOT NULL DEFAULT '',
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE base_orders (
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
CREATE TABLE usage_events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER,
    ip         TEXT    DEFAULT '',
    kind       TEXT    NOT NULL,
    category   TEXT    NOT NULL DEFAULT '',
    label      TEXT    NOT NULL DEFAULT '',
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
, guest_sid TEXT DEFAULT '');
CREATE INDEX idx_usage_events_kind
    ON usage_events(kind, created_at);
CREATE INDEX idx_usage_events_ip ON usage_events(ip);
CREATE TABLE client_errors (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER,
    ip         TEXT    DEFAULT '',
    guest_sid  TEXT    DEFAULT '',
    kind       TEXT    NOT NULL,   -- 'jserror' | 'unhandledrejection'
    message    TEXT    DEFAULT '',
    stack      TEXT    DEFAULT '',
    url        TEXT    DEFAULT '',
    line       INTEGER,
    col        INTEGER,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_client_errors_created
    ON client_errors(created_at);
CREATE TABLE crossword_sessions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    -- ゲスト(__guest__)は全員user_idを共有するため、user_id一致だけでは
    -- 個々のゲストを区別できない(2026-09-05・サンプルクロスワードを
    -- ゲストにも公開したことで表面化。app/main.pyのミドルウェアが発行する
    -- guest_sid Cookieで個別に区別する。ログイン済みユーザーは常に''。
    -- games.pyの_owned_session参照)。
    guest_sid     TEXT    NOT NULL DEFAULT '',
    source_type   TEXT    NOT NULL,              -- 'domain' | 'deck' | 'sample'
    source_ref    TEXT    NOT NULL DEFAULT '',    -- カンマ区切り分野名 or deck_id or sample_id
    -- 大分類(2026-09-06)。source_ref(分野)が空でもcategoryだけ指定
    -- されていれば大分類配下の全分野が対象、両方空なら全分野が対象
    -- (games.py _fetch_candidate_words参照)。一覧表示の短縮ラベル
    -- (_crossword_source_label)にも使う。
    category      TEXT    NOT NULL DEFAULT '',
    clue_mode     TEXT    NOT NULL DEFAULT 'always_ja',  -- 'always_ja'|'hints_only'
    -- クリューモードで決まる最終スコア倍率(2026-09-05・
    -- games.pyのCLUE_MODE_SCORE_MULTIPLIER参照。「ヒントの難易度」は
    -- 独立設定ではなくclue_mode自体が兼ねる、というユーザー指示に基づく)。
    score_multiplier REAL NOT NULL DEFAULT 1.0,
    -- 「最初から」(/restart)で同じ設定を再現するために保存する生成条件
    -- (2026-09-05)。source_type/source_ref/clue_modeと合わせて
    -- NewGamePayload一式を復元できるようにする。
    word_count     INTEGER NOT NULL DEFAULT 10,
    english_style  TEXT    NOT NULL DEFAULT 'fill_blank',
    japanese_style TEXT    NOT NULL DEFAULT 'simple',
    level_min      TEXT,
    level_max      TEXT,
    -- パズルの詰め方(2026-09-05)。1なら面積優先(コンパクトモード)。
    compact        INTEGER NOT NULL DEFAULT 0,
    -- 画面サイズを考慮した盤面形状(2026-09-06)。1なら作成時の画面幅/
    -- 高さ比に近い縦横比になるよう試みる(compactとは独立・両立可)。
    screen_fit     INTEGER NOT NULL DEFAULT 0,
    -- 不正解時の部分一致開示の甘さ(2026-09-05・'easy'|'normal'|'hard'。
    -- games.pyのPARTIAL_MATCH_THRESHOLD_BY_DIFFICULTY参照)。
    answer_difficulty TEXT NOT NULL DEFAULT 'normal',
    -- 保存(ピン留め、2026-09-05)。1なら_enforce_session_capの上限・
    -- 自動削除の対象から常に除外する(課金ユーザー限定機能)。
    pinned        INTEGER NOT NULL DEFAULT 0,
    puzzle_json   TEXT    NOT NULL,
    progress_json TEXT    NOT NULL DEFAULT '{}',
    score         INTEGER NOT NULL DEFAULT 0,
    status        TEXT    NOT NULL DEFAULT 'in_progress',  -- 'in_progress'|'completed'
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    completed_at  TEXT
);
CREATE INDEX idx_crossword_sessions_user
    ON crossword_sessions(user_id, created_at);
CREATE TABLE crossword_samples (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    title          TEXT    NOT NULL,
    description    TEXT    NOT NULL DEFAULT '',
    domains        TEXT    NOT NULL DEFAULT '',
    level_min      TEXT,
    level_max      TEXT,
    word_count     INTEGER NOT NULL,
    clue_mode      TEXT    NOT NULL DEFAULT 'always_ja',
    english_style  TEXT    NOT NULL DEFAULT 'fill_blank',
    japanese_style TEXT    NOT NULL DEFAULT 'simple',
    compact        INTEGER NOT NULL DEFAULT 0,
    puzzle_json    TEXT    NOT NULL,
    sort_order     INTEGER NOT NULL DEFAULT 0,
    is_active      INTEGER NOT NULL DEFAULT 1,
    created_at     TEXT    NOT NULL DEFAULT (datetime('now'))
, guest_playable INTEGER NOT NULL DEFAULT 0);
CREATE TABLE crossword_sample_plays (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    guest_sid   TEXT    NOT NULL DEFAULT '',
    sample_id   INTEGER NOT NULL REFERENCES crossword_samples(id),
    session_id  INTEGER,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_crossword_sample_plays_user
    ON crossword_sample_plays(user_id, sample_id);
CREATE INDEX idx_crossword_sample_plays_guest
    ON crossword_sample_plays(guest_sid, sample_id);
CREATE TRIGGER trg_words_example_ja_invalidate
        AFTER UPDATE OF example ON words
        FOR EACH ROW
        WHEN NEW.example IS NOT OLD.example
          AND json_valid(NEW.detail)
          AND (json_extract(NEW.detail, '$.example_ja_src') IS NULL
               OR json_extract(NEW.detail, '$.example_ja_src') != NEW.example)
        BEGIN
            UPDATE words
            SET detail = json_remove(detail, '$.example_ja', '$.example_ja_src')
            WHERE id = NEW.id;
        END;
