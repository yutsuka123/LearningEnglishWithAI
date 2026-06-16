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
    daily_cap_usd: Optional[float] = None,
    monthly_cap_usd: Optional[float] = None,
    balance_jpy: Optional[float] = None,
    allow_banned: bool = False,
) -> int:
    """ユーザーを作成して id を返す（管理者が割当）。username は一意。"""
    pw = hash_password(password) if password else ""
    cur = conn.execute(
        "INSERT INTO users (username, password_hash, role, display_name, "
        " daily_cost_cap_usd, monthly_cost_cap_usd, balance_jpy, "
        " allow_banned) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (username.strip(), pw, role, display_name or username.strip(),
         daily_cap_usd, monthly_cap_usd, balance_jpy,
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
        "SELECT id, username, role, is_active, display_name, "
        " daily_cost_cap_usd, monthly_cost_cap_usd, balance_jpy, created_at "
        "FROM users ORDER BY id"
    ).fetchall()
    return [dict(r) for r in rows]


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


def _login_key(username: str, ip: str) -> str:
    return f"{(username or '').strip().lower()}|{ip}"


def _recent(store: dict, key: str, window: float) -> list[float]:
    now = _time.monotonic()
    fails = [t for t in store.get(key, []) if now - t < window]
    store[key] = fails
    return fails


def login_locked(username: str, ip: str) -> bool:
    """3回連続失敗(user×IP)で5分、または1IPから多数失敗(spray)で15分ロック。"""
    if len(_recent(_IP_FAILS, ip or "?", _IP_LOCK)) >= _IP_MAX:
        return True
    return len(_recent(_LOGIN_FAILS, _login_key(username, ip),
                       _LOGIN_LOCK)) >= _LOGIN_MAX


def record_login_failure(username: str, ip: str) -> None:
    now = _time.monotonic()
    _LOGIN_FAILS.setdefault(_login_key(username, ip), []).append(now)
    _IP_FAILS.setdefault(ip or "?", []).append(now)


def clear_login_failures(username: str, ip: str) -> None:
    # 成功時は当該 user×IP の連続失敗のみ解除（IPの spray カウントは保持）。
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
    return {"locked_accounts": locked_accounts, "locked_ips": locked_ips}


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
