"""認証とユーザー管理（§A マルチユーザー化）。

- パスワードは標準ライブラリ ``hashlib.pbkdf2_hmac`` でハッシュ化（passlib/
  bcrypt 等の追加依存なし＝Win/Mac 可搬・ネイティブビルド不要）。
- 「現在のユーザー」は ``contextvars`` で1リクエスト単位に持つ。これにより
  ai.chat / synthesize_speech などの**呼び出しシグネチャを変えずに** user 別
  ガード（日次/月次上限・前払い残高）を効かせられる。
- ローカル単一ユーザー（MULTIUSER=0）は常に owner(id=1) として動く＝従来どおり
  無認証。MULTIUSER=1 のときだけログインを要求する（main.py で制御）。
"""

from __future__ import annotations

import contextvars
import hashlib
import hmac
import os
import secrets
import sqlite3
from typing import Optional

from ..database import OWNER_USER_ID

# pbkdf2 パラメータ（保存形式: ``pbkdf2_sha256$<iters>$<salt_hex>$<hash_hex>``）。
_PBKDF2_ALGO = "sha256"
_PBKDF2_ITERS = 200_000
_SALT_BYTES = 16

# 現在のリクエストのユーザーID（未設定時は owner）。バッチ/CLIでも owner 既定。
_current_user_id: contextvars.ContextVar[int] = contextvars.ContextVar(
    "current_user_id", default=OWNER_USER_ID
)

# 現在のリクエストの接続元IP（未設定時は空文字）。current_user_idと同じ
# contextvarパターンで、ai.py側の呼び出しシグネチャを変えずにai_usageへの
# IP記録（§E2・アカウント共有の異常検知用）を可能にする。
_current_ip: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_ip", default=""
)

# 現在の呼び出しがWebリクエスト経由か（未設定＝CLI/バッチ実行）。
# current_user_idはCLI実行時ownerにフォールバックするため、Web経由の
# owner本人の利用と区別がつかなかった問題を解消する（§CLIスクリプトの
# AI無料枠問題）。ai.py側の_user_guard()がこれを見て、CLI実行時はtier別
# 個別枠チェックをスキップする（サイト全体上限は引き続き有効）。
_in_web_request: contextvars.ContextVar[bool] = contextvars.ContextVar(
    "in_web_request", default=False
)


# ---------------------------------------------------------------------------
# パスワードハッシュ
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    """pbkdf2 でパスワードをハッシュ化して保存用文字列を返す。"""
    salt = secrets.token_bytes(_SALT_BYTES)
    dk = hashlib.pbkdf2_hmac(
        _PBKDF2_ALGO, password.encode("utf-8"), salt, _PBKDF2_ITERS
    )
    return (f"pbkdf2_{_PBKDF2_ALGO}${_PBKDF2_ITERS}$"
            f"{salt.hex()}${dk.hex()}")


def verify_password(password: str, stored: str) -> bool:
    """保存ハッシュと照合（定数時間比較）。空ハッシュ（未設定）は常に不一致。"""
    if not stored:
        return False
    try:
        algo_tag, iters_s, salt_hex, hash_hex = stored.split("$")
        algo = algo_tag.split("_", 1)[1]
        iters = int(iters_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
    except (ValueError, IndexError):
        return False
    dk = hashlib.pbkdf2_hmac(
        algo, password.encode("utf-8"), salt, iters)
    return hmac.compare_digest(dk, expected)


# ---------------------------------------------------------------------------
# 現在ユーザー（contextvar）
# ---------------------------------------------------------------------------
def set_current_user_id(user_id: int) -> contextvars.Token:
    return _current_user_id.set(int(user_id))


def reset_current_user_id(token: contextvars.Token) -> None:
    _current_user_id.reset(token)


def current_user_id() -> int:
    return _current_user_id.get()


def set_current_ip(ip: str) -> contextvars.Token:
    return _current_ip.set(ip or "")


def reset_current_ip(token: contextvars.Token) -> None:
    _current_ip.reset(token)


def current_ip() -> str:
    return _current_ip.get()


def mark_web_request() -> contextvars.Token:
    return _in_web_request.set(True)


def reset_web_request(token: contextvars.Token) -> None:
    _in_web_request.reset(token)


def is_web_request() -> bool:
    return _in_web_request.get()


def current_user_allow_banned() -> bool:
    """現在ユーザーが禁止用語コンテンツを閲覧してよいか（§E）。
    owner(id=1) と admin は常に可。一般ユーザーは ``allow_banned`` 列に従う。
    クライアントが ``include_banned=true`` を送っても、この関数が False を返す
    ユーザーには禁止用語を出さない（サーバー側で強制）。"""
    from ..database import db, OWNER_USER_ID as _OWNER

    uid = current_user_id()
    if uid == _OWNER:
        return True
    with db() as conn:
        u = get_user(conn, uid)
    if not u:
        return False
    if u.get("role") == "admin":
        return True
    return bool(u.get("allow_banned"))


# ---------------------------------------------------------------------------
# ユーザー CRUD
# ---------------------------------------------------------------------------
def get_user(conn: sqlite3.Connection, user_id: int) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    return dict(row) if row else None


def get_user_by_name(
    conn: sqlite3.Connection, username: str
) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM users WHERE username = ?", (username.strip(),)
    ).fetchone()
    return dict(row) if row else None


def get_user_by_email(
    conn: sqlite3.Connection, email: str
) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM users WHERE email = ? AND email <> ''",
        (email.strip().lower(),),
    ).fetchone()
    return dict(row) if row else None


def normalize_email_for_uniqueness(email: str) -> str:
    """サインアップ時の重複判定専用の正規化（§C2）。保存する値自体は
    変えない（表示・連絡用に入力どおりを保持）。Gmail/Googlemailは
    ドット除去・+タグ除去（本家の仕様に合わせる）、他ドメインは+タグ除去
    のみ行い、`alice+test@x.com`のようなエイリアスでの複垢作成を防ぐ。"""
    email = (email or "").strip().lower()
    if "@" not in email:
        return email
    local, _, domain = email.partition("@")
    local = local.split("+", 1)[0]
    if domain in ("gmail.com", "googlemail.com"):
        local = local.replace(".", "")
        domain = "gmail.com"
    return f"{local}@{domain}"


def find_user_by_normalized_email(
    conn: sqlite3.Connection, email: str
) -> Optional[dict]:
    """`get_user_by_email`の完全一致をすり抜けるエイリアス（dot/+tag）での
    重複登録を検出する（§C2）。ユーザー数が少ないため全走査で十分。"""
    target = normalize_email_for_uniqueness(email)
    if not target:
        return None
    rows = conn.execute(
        "SELECT * FROM users WHERE email <> ''"
    ).fetchall()
    for row in rows:
        if normalize_email_for_uniqueness(row["email"]) == target:
            return dict(row)
    return None


# 既知の使い捨て(一時)メールサービスのドメイン。網羅的ではない簡易
# ブロックリストのため「最初のハードル」程度の位置づけ（§C1）。
_DISPOSABLE_EMAIL_DOMAINS = {
    "mailinator.com", "guerrillamail.com", "guerrillamail.info",
    "10minutemail.com", "10minutemail.net", "temp-mail.org", "tempmail.com",
    "throwawaymail.com", "yopmail.com", "trashmail.com", "getnada.com",
    "sharklasers.com", "maildrop.cc", "dispostable.com", "fakeinbox.com",
    "mailnesia.com", "mintemail.com", "mytemp.email", "moakt.com",
    "tempinbox.com", "spamgourmet.com", "emailondeck.com", "burnermail.io",
    "temp-mail.io", "1secmail.com", "discard.email", "mohmal.com",
    "tempr.email", "luxusmail.org", "mailcatch.com", "mailnull.com",
    "spam4.me", "einrot.com", "fakemailgenerator.com", "emailfake.com",
}


def is_disposable_email_domain(email: str) -> bool:
    """使い捨てメールの既知ドメインかどうか（§C1）。"""
    email = (email or "").strip().lower()
    domain = email.rsplit("@", 1)[-1] if "@" in email else ""
    return domain in _DISPOSABLE_EMAIL_DOMAINS


def authenticate(
    conn: sqlite3.Connection, username: str, password: str
) -> Optional[dict]:
    """ユーザー名＋パスワードを検証。成功で user dict、失敗で None。"""
    u = get_user_by_name(conn, username)
    if not u or not u.get("is_active"):
        return None
    if not verify_password(password, u.get("password_hash") or ""):
        return None
    return u


def create_user(
    conn: sqlite3.Connection,
    username: str,
    password: str = "",
    *,
    role: str = "user",
    display_name: str = "",
    email: str = "",
    daily_cap_usd: Optional[float] = None,
    monthly_cap_usd: Optional[float] = None,
    balance_jpy: Optional[float] = None,
    allow_banned: bool = False,
) -> int:
    """ユーザーを作成して id を返す。username は一意。

    ``email`` は自己サインアップ(メアド+パス)ユーザー用（既定は空文字＝
    管理者(admin.py)作成の従来ユーザーと同じ扱い）。呼び出し元を増やさず
    後方互換を保つため、キーワード専用・既定空文字にしている。
    """
    pw = hash_password(password) if password else ""
    cur = conn.execute(
        "INSERT INTO users (username, password_hash, role, display_name, "
        " email, daily_cost_cap_usd, monthly_cost_cap_usd, balance_jpy, "
        " allow_banned) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (username.strip(), pw, role, display_name or username.strip(),
         email.strip().lower(), daily_cap_usd, monthly_cap_usd, balance_jpy,
         1 if allow_banned else 0),
    )
    return int(cur.lastrowid)


def set_password(
    conn: sqlite3.Connection, user_id: int, password: str
) -> None:
    conn.execute(
        "UPDATE users SET password_hash = ? WHERE id = ?",
        (hash_password(password) if password else "", user_id),
    )


def set_caps(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    daily_cap_usd: Optional[float] = None,
    monthly_cap_usd: Optional[float] = None,
) -> None:
    conn.execute(
        "UPDATE users SET daily_cost_cap_usd = ?, monthly_cost_cap_usd = ? "
        "WHERE id = ?",
        (daily_cap_usd, monthly_cap_usd, user_id),
    )


def add_balance(
    conn: sqlite3.Connection, user_id: int, delta_jpy: float
) -> float:
    """前払い残高を増減（チャージ/控除）し、更新後の残高を返す。
    残高 NULL（残高制を使っていない）の場合は delta から開始する。"""
    row = conn.execute(
        "SELECT balance_jpy FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    cur = row["balance_jpy"] if row and row["balance_jpy"] is not None else 0.0
    new = float(cur) + float(delta_jpy)
    conn.execute(
        "UPDATE users SET balance_jpy = ? WHERE id = ?", (new, user_id)
    )
    return new


def set_balance(
    conn: sqlite3.Connection, user_id: int, balance_jpy: Optional[float]
) -> None:
    conn.execute(
        "UPDATE users SET balance_jpy = ? WHERE id = ?",
        (balance_jpy, user_id),
    )


def set_active(
    conn: sqlite3.Connection, user_id: int, active: bool
) -> None:
    conn.execute(
        "UPDATE users SET is_active = ? WHERE id = ?",
        (1 if active else 0, user_id),
    )


def list_users(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        "SELECT id, username, role, is_active, display_name, email, "
        " daily_cost_cap_usd, monthly_cost_cap_usd, balance_jpy, created_at "
        "FROM users ORDER BY id"
    ).fetchall()
    users = [dict(r) for r in rows]
    for u in users:
        u["tier"] = user_tier(conn, u["id"])
    return users


def user_tier(conn: sqlite3.Connection, user_id: int) -> str:
    """ユーザーの階層を判定して返す（"legacy" | "email" | "charged"）。
    未ログイン("guest")はこの関数の対象外（呼び出し側で判定する）。

    - email が空 → "legacy"（admin.py が作成した従来ユーザー）
    - email が非空 → "email"（自己サインアップユーザー）
    - 上記に加え、残高>0 か チャージキー償還履歴があれば "charged"
      （管理者が直接残高を付与したケースも実質的に有償相当のため含める）。
    """
    u = get_user(conn, user_id)
    if not u:
        return "legacy"
    charged = bool(u.get("balance_jpy")) or conn.execute(
        "SELECT 1 FROM charge_keys WHERE used_by_user_id = ? LIMIT 1",
        (user_id,),
    ).fetchone() is not None
    if charged:
        return "charged"
    return "email" if (u.get("email") or "").strip() else "legacy"


def is_charged_or_admin(conn: sqlite3.Connection, user_id: int) -> bool:
    """単語帳・フレーズ帳等、課金ユーザー限定機能のゲートに使う判定。
    管理者(role='admin')は自身のアカウントで機能確認できるよう例外的に許可する。"""
    u = get_user(conn, user_id)
    if u and u.get("role") == "admin":
        return True
    return user_tier(conn, user_id) == "charged"


def multiuser_enabled() -> bool:
    """MULTIUSER=1 のときだけログインを要求（既定はローカル単一ユーザー）。"""
    return os.getenv("MULTIUSER", "0").strip().lower() in ("1", "true", "yes")


def get_user_settings(conn: sqlite3.Connection, user_id: int) -> dict:
    """per-user UI設定(JSON)を dict で返す（nickname / toeic_self / 音声設定 等）。"""
    import json
    row = conn.execute(
        "SELECT settings FROM user_settings WHERE user_id = ?", (user_id,)
    ).fetchone()
    if not row:
        return {}
    try:
        d = json.loads(row["settings"])
        return d if isinstance(d, dict) else {}
    except (ValueError, TypeError):
        return {}


# ---------------------------------------------------------------------------
# 署名Cookieセッション（stdlib hmac・itsdangerous 等の追加依存なし）
# 形式: ``<user_id>.<exp_unix>.<hmac_hex>``
# ---------------------------------------------------------------------------
SESSION_COOKIE = "ela_session"
_SESSION_TTL = 60 * 60 * 24 * 30  # 30日


def get_session_secret(conn: sqlite3.Connection) -> bytes:
    """セッション署名鍵。env SESSION_SECRET 優先、無ければ app_state に生成保存。"""
    env = os.getenv("SESSION_SECRET", "").strip()
    if env:
        return env.encode("utf-8")
    row = conn.execute(
        "SELECT value FROM app_state WHERE key = 'session_secret'"
    ).fetchone()
    if row and row["value"]:
        return bytes.fromhex(row["value"])
    sk = secrets.token_bytes(32)
    conn.execute(
        "INSERT OR REPLACE INTO app_state (key, value) VALUES "
        "('session_secret', ?)", (sk.hex(),)
    )
    return sk


def _sign(secret: bytes, payload: str) -> str:
    return hmac.new(secret, payload.encode("utf-8"),
                    hashlib.sha256).hexdigest()


def make_session_token(secret: bytes, user_id: int, now: int) -> str:
    exp = now + _SESSION_TTL
    payload = f"{user_id}.{exp}"
    return f"{payload}.{_sign(secret, payload)}"


# ---------------------------------------------------------------------------
# ログイン総当たり対策（簡易・プロセス内メモリ。単一プロセス想定）
# ---------------------------------------------------------------------------
import time as _time  # noqa: E402

# (user|ip) 単位: 3回連続失敗で5分ロック（成功でクリア）。
_LOGIN_FAILS: dict[str, list[float]] = {}
_LOGIN_MAX = 3          # 連続失敗がこの回数に達したら
_LOGIN_LOCK = 300.0     # 5分ロック（=直近この秒数の失敗を数える）

# IP 単位: ユーザー名総当たり(spray)対策。多数の失敗を出すIPを一時遮断。
_IP_FAILS: dict[str, list[float]] = {}
_IP_MAX = 15            # 1IPからの失敗が直近 _IP_WINDOW で15回に達したら
_IP_WINDOW = 300.0      # 5分
_IP_LOCK = 900.0        # 15分ロック

# username 単位: 複数IPに分散した低頻度パスワードスプレー対策(§B3)。
# (username,ip)単位・IP単位のどちらの閾値にも届かない「1IPあたり数回ずつ・
# 多数のIPから同一アカウントを狙う」攻撃を検知するため、IPを問わず
# username単独で失敗を合算する。
_USERNAME_FAILS: dict[str, list[float]] = {}
_USERNAME_MAX = 8       # 直近 _USERNAME_LOCK 内でこの回数に達したら
_USERNAME_LOCK = 900.0  # 15分（IP spray対策と揃える）


def _username_key(username: str) -> str:
    return (username or "").strip().lower()


def _login_key(username: str, ip: str) -> str:
    return f"{_username_key(username)}|{ip}"


def _recent(store: dict, key: str, window: float) -> list[float]:
    now = _time.monotonic()
    fails = [t for t in store.get(key, []) if now - t < window]
    store[key] = fails
    return fails


def login_locked(username: str, ip: str) -> bool:
    """3回連続失敗(user×IP)で5分、1IPから多数失敗(spray)で15分、または
    複数IPに分散した同一username狙いの失敗が続いた場合も15分ロック(§B3)。"""
    if len(_recent(_IP_FAILS, ip or "?", _IP_LOCK)) >= _IP_MAX:
        return True
    if len(_recent(_USERNAME_FAILS, _username_key(username),
                   _USERNAME_LOCK)) >= _USERNAME_MAX:
        return True
    return len(_recent(_LOGIN_FAILS, _login_key(username, ip),
                       _LOGIN_LOCK)) >= _LOGIN_MAX


def record_login_failure(username: str, ip: str) -> None:
    now = _time.monotonic()
    _LOGIN_FAILS.setdefault(_login_key(username, ip), []).append(now)
    _IP_FAILS.setdefault(ip or "?", []).append(now)
    _USERNAME_FAILS.setdefault(_username_key(username), []).append(now)


def clear_login_failures(username: str, ip: str) -> None:
    # 成功時は当該 user×IP の連続失敗のみ解除する。IPのsprayカウントも
    # username横断のsprayカウントも保持する（他IPからの同時進行中の攻撃を
    # 見逃さないため。正規ユーザーの成功はそれらの証拠を消す理由にならない）。
    _LOGIN_FAILS.pop(_login_key(username, ip), None)


def lockout_status() -> dict:
    """現在のログインロック状況（管理者ダッシュボード用）。プロセス内メモリ。"""
    now = _time.monotonic()
    locked_accounts = sum(
        1 for k, ts in _LOGIN_FAILS.items()
        if len([t for t in ts if now - t < _LOGIN_LOCK]) >= _LOGIN_MAX)
    locked_ips = sum(
        1 for ip, ts in _IP_FAILS.items()
        if len([t for t in ts if now - t < _IP_LOCK]) >= _IP_MAX)
    locked_usernames = sum(
        1 for uname, ts in _USERNAME_FAILS.items()
        if len([t for t in ts if now - t < _USERNAME_LOCK]) >= _USERNAME_MAX)
    return {
        "locked_accounts": locked_accounts,
        "locked_ips": locked_ips,
        "locked_usernames": locked_usernames,
    }


# 汎用 IP レート制限（DDoS/濫用の速度制限）。RATE_LIMIT_PER_MIN で調整。
# 0/未設定=無効（ローカル単一ユーザーは既定で無効＝通常利用に影響なし）。
# 公開時は env で 300 程度を推奨。真のDDoSは前段(Cloudflare/Caddy/fail2ban)で防ぐ。
_IP_HITS: dict[str, list[float]] = {}


def ip_rate_limited(ip: str) -> bool:
    cap_s = os.getenv("RATE_LIMIT_PER_MIN", "0").strip()
    try:
        cap = int(cap_s)
    except ValueError:
        cap = 0
    if cap <= 0:
        return False
    hits = _recent(_IP_HITS, ip or "?", 60.0)
    if len(hits) >= cap:
        return True
    hits.append(_time.monotonic())
    return False


def parse_session_token(
    secret: bytes, token: str, now: int
) -> Optional[int]:
    """トークンを検証して user_id を返す。無効/期限切れは None。"""
    try:
        uid_s, exp_s, sig = token.split(".")
        payload = f"{uid_s}.{exp_s}"
    except (ValueError, AttributeError):
        return None
    if not hmac.compare_digest(sig, _sign(secret, payload)):
        return None
    if int(exp_s) < now:
        return None
    return int(uid_s)
