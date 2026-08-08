"""チャージキー: BASE等で手売りする招待コードのセルフサービス償還。

キー形式（全16桁・大文字小文字は区別しない）::

    [4桁: 固定値(パターン)] + [7桁: ユニークID] + [1桁: CRC] + [4桁: シークレット]

- 文字セットは31種（``0 O 1 I L`` を除外した英数字）。人間が手入力しても
  間違えにくい。
- ユニークID7桁は、DBの連番(id)をFeistel型の可逆変換にかけて作る。連番から
  作るので衝突は原理的に起きないが、変換の鍵（``CHARGE_KEY_SECRET``）を知ら
  ない限り「次の連番がどの文字列になるか」は予測できない。常時表示してよい
  （これだけでは残高を奪えない）。
- CRC1桁は固定値+ユニークID(先頭11桁)から算出。入力ミスをDB照会前に検知する
  目的のみで、常時表示してよい（隠す意味がない）。
- シークレット4桁は独立した乱数で、これが実際の償還権。DBにはハッシュのみ
  保存し、発行時の送付以外の画面では常に伏字にすること。
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import sqlite3
from typing import Optional

from . import auth

# ---------------------------------------------------------------------------
# アルファベット（0 O 1 I L を除外した31種。大文字小文字は区別しない）
# ---------------------------------------------------------------------------
ALPHABET = "23456789ABCDEFGHJKMNPQRSTUVWXYZ"
_BASE = len(ALPHABET)  # 31
_CHAR_VALUE = {c: i for i, c in enumerate(ALPHABET)}

FIXED_DIGITS = 4
ID_DIGITS = 7
CRC_DIGITS = 1
SECRET_DIGITS = 4
KEY_ID_DIGITS = FIXED_DIGITS + ID_DIGITS + CRC_DIGITS       # 12
TOTAL_DIGITS = KEY_ID_DIGITS + SECRET_DIGITS                # 16

ID_DOMAIN = _BASE ** ID_DIGITS  # 31**7 ≈ 275億

# Feistel: 2^36 >= ID_DOMAIN の均等割り(18bit+18bit)にサイクルウォーキングで収める。
_FEISTEL_BITS = 36
_HALF_BITS = _FEISTEL_BITS // 2  # 18
_HALF_MASK = (1 << _HALF_BITS) - 1
_ROUNDS = 4


class ChargeKeyError(ValueError):
    """キー形式不正・見つからない・使用済み等、ユーザーに見せてよいエラー。"""


# ---------------------------------------------------------------------------
# Feistel（連番 -> 一見ランダムなユニークID。逆変換は不要なので一方向のみ実装）
# ---------------------------------------------------------------------------
def _feistel_secret() -> bytes:
    """Feistelのラウンド鍵。サーバー内(.envのCHARGE_KEY_SECRET)にのみ保管する。
    未設定のままだと開発用の固定値にフォールバックする（本番投入前に必ず設定
    すること。値を変えると既発行キーのユニークID対応が変わってしまうので、
    一度本番で使い始めたら変更しない）。"""
    env = os.getenv("CHARGE_KEY_SECRET", "").strip()
    if env:
        return env.encode("utf-8")
    return b"dev-only-charge-key-secret-please-set-CHARGE_KEY_SECRET-in-env"


def _round_fn(x: int, round_no: int, key: bytes) -> int:
    h = hmac.new(
        key, round_no.to_bytes(1, "big") + x.to_bytes(3, "big"), hashlib.sha256
    ).digest()
    return int.from_bytes(h[:3], "big") & _HALF_MASK


def _feistel_permute(x: int, key: bytes) -> int:
    """2^36 空間での全単射（何回適用しても可逆・Fの性質を問わない標準Feistel）。"""
    l = (x >> _HALF_BITS) & _HALF_MASK
    r = x & _HALF_MASK
    for round_no in range(_ROUNDS):
        l, r = r, l ^ _round_fn(r, round_no, key)
    return (l << _HALF_BITS) | r


def seq_to_pseudo_unique(seq: int) -> int:
    """連番(0以上)を [0, ID_DOMAIN) の一見ランダムな整数へ可逆変換する
    （サイクルウォーキング法）。全単射なので衝突しない。"""
    if seq < 0 or seq >= ID_DOMAIN:
        raise ValueError(f"seq must be in [0, {ID_DOMAIN})")
    key = _feistel_secret()
    x = seq
    while True:
        x = _feistel_permute(x, key)
        if x < ID_DOMAIN:
            return x


# ---------------------------------------------------------------------------
# 31進エンコード / CRC
# ---------------------------------------------------------------------------
def _encode(n: int, width: int) -> str:
    digits = []
    for _ in range(width):
        n, r = divmod(n, _BASE)
        digits.append(ALPHABET[r])
    if n != 0:
        raise ValueError("value too large for width")
    return "".join(reversed(digits))


def _crc_char(s: str) -> str:
    """先頭桁からのHorner法チェックサム(mod 31)。1文字誤字の大半・多くの
    入れ替わりを検知できる（31は素数なので分布が良い）。"""
    total = 0
    for ch in s:
        total = (total * _BASE + _CHAR_VALUE[ch]) % _BASE
    return ALPHABET[total]


def _normalize(s: str) -> str:
    """大文字小文字を無視し、区切り文字(- や空白)を許容して除去する。"""
    return "".join(ch for ch in s.upper() if ch not in "- ")


def _validate_pattern(pattern: str) -> str:
    p = _normalize(pattern)
    if len(p) != FIXED_DIGITS or any(c not in _CHAR_VALUE for c in p):
        raise ValueError(
            f"pattern must be {FIXED_DIGITS} chars from: {ALPHABET}")
    return p


def _random_secret() -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(SECRET_DIGITS))


# ---------------------------------------------------------------------------
# 生成・償還
# ---------------------------------------------------------------------------
def generate_key(
    conn: sqlite3.Connection, *, pattern: str, amount_jpy: int
) -> str:
    """新しいチャージキーを1つ生成しDBへ登録、平文キー(全16桁)を返す。
    平文が得られるのはこの返り値のみ（DBにはシークレットのハッシュしか
    保存されない）。呼び出し側は戻り値を控えたら画面/ログに残さないこと。"""
    p = _validate_pattern(pattern)
    if amount_jpy <= 0:
        raise ValueError("amount_jpy must be positive")
    secret = _random_secret()
    secret_hash = auth.hash_password(secret)
    cur = conn.execute(
        "INSERT INTO charge_keys (key_id, secret_hash, amount_jpy, pattern) "
        "VALUES ('', ?, ?, ?)",
        (secret_hash, amount_jpy, p),
    )
    seq = int(cur.lastrowid)
    pseudo = seq_to_pseudo_unique(seq)
    unique_id = _encode(pseudo, ID_DIGITS)
    crc = _crc_char(p + unique_id)
    key_id = p + unique_id + crc
    conn.execute(
        "UPDATE charge_keys SET key_id = ? WHERE id = ?", (key_id, seq)
    )
    return key_id + secret


# キーが「存在しない/使用済み/シークレット不一致」のどれであるかを応答から
# 区別できると、攻撃者が「有効かつ未償還のkey_id」だけに絞って総当たり対象を
# 絞り込めてしまう（error oracle）。2026-08-08: 不正利用分析で指摘され、
# この3ケースは同一の汎用メッセージに統一した（形式不正・CRC不一致は
# DBに触れる前に分かる純粋な入力ミスなので区別してよい）。
_INVALID_KEY_MSG = "キーが無効です。入力内容をご確認ください。"

# ---------------------------------------------------------------------------
# 償還の総当たり対策（簡易・プロセス内メモリ。ログイン総当たり対策
# (app/services/auth.py の _LOGIN_FAILS)と同じ方式）。
# シークレット4桁(31進数・約92万通り)への総当たりを、ユーザー単位で
# 一定回数の失敗後にロックすることで実用上不可能にする。
# ---------------------------------------------------------------------------
import time as _time  # noqa: E402

_REDEEM_FAILS: dict[int, list[float]] = {}
_REDEEM_MAX = 10        # 直近_REDEEM_WINDOW秒でこの回数失敗したらロック
_REDEEM_WINDOW = 3600.0  # 1時間

# サインアップ経由(POST /api/auth/signup)の償還失敗はIP単位で数える。
# signupは失敗するとユーザー行ごとロールバックされるため、上記のuser_id単位
# カウンタでは「毎回新規uidで試せてしまう」抜け道がある(2026-08-08発見)。
_SIGNUP_REDEEM_FAILS: dict[str, list[float]] = {}
_SIGNUP_REDEEM_MAX = 10
_SIGNUP_REDEEM_WINDOW = 3600.0


def signup_redeem_locked(ip: str) -> bool:
    now = _time.monotonic()
    key = ip or "?"
    fails = [t for t in _SIGNUP_REDEEM_FAILS.get(key, [])
             if now - t < _SIGNUP_REDEEM_WINDOW]
    _SIGNUP_REDEEM_FAILS[key] = fails
    return len(fails) >= _SIGNUP_REDEEM_MAX


def record_signup_redeem_failure(ip: str) -> None:
    _SIGNUP_REDEEM_FAILS.setdefault(ip or "?", []).append(_time.monotonic())


def _recent_fails(user_id: int) -> list[float]:
    now = _time.monotonic()
    fails = [t for t in _REDEEM_FAILS.get(user_id, []) if now - t < _REDEEM_WINDOW]
    _REDEEM_FAILS[user_id] = fails
    return fails


def redeem_locked(user_id: int) -> bool:
    """直近1時間に10回失敗していればロック。"""
    return len(_recent_fails(user_id)) >= _REDEEM_MAX


def _record_redeem_failure(user_id: int) -> None:
    _REDEEM_FAILS.setdefault(user_id, []).append(_time.monotonic())


def _clear_redeem_failures(user_id: int) -> None:
    _REDEEM_FAILS.pop(user_id, None)


def redeem_key(
    conn: sqlite3.Connection, user_id: int, raw_key: str
) -> float:
    """キーを償還してuser_idの残高(pt=balance_jpy)に加算し、更新後残高を返す。
    無効・入力ミス・使用済みは ChargeKeyError。失敗はユーザー単位で記録し、
    一定回数でロックする（呼び出し側は事前に`redeem_locked()`を確認）。"""
    try:
        raw = _normalize(raw_key)
        if len(raw) != TOTAL_DIGITS or any(c not in _CHAR_VALUE for c in raw):
            raise ChargeKeyError("キーの形式が正しくありません。")
        key_id, secret = raw[:KEY_ID_DIGITS], raw[KEY_ID_DIGITS:]
        if _crc_char(key_id[:-1]) != key_id[-1]:
            raise ChargeKeyError("キーが正しくありません（入力ミスの可能性）。")
        row = conn.execute(
            "SELECT * FROM charge_keys WHERE key_id = ?", (key_id,)
        ).fetchone()
        if not row:
            raise ChargeKeyError(_INVALID_KEY_MSG)
        if row["used_at"]:
            raise ChargeKeyError(_INVALID_KEY_MSG)
        if not auth.verify_password(secret, row["secret_hash"]):
            raise ChargeKeyError(_INVALID_KEY_MSG)
        cur = conn.execute(
            "UPDATE charge_keys SET used_at = datetime('now'), "
            "used_by_user_id = ? WHERE key_id = ? AND used_at IS NULL",
            (user_id, key_id),
        )
        if cur.rowcount == 0:
            # 同時償還などの競合。ここに来た時点で二重付与は防げている。
            raise ChargeKeyError(_INVALID_KEY_MSG)
    except ChargeKeyError:
        _record_redeem_failure(user_id)
        raise
    _clear_redeem_failures(user_id)
    return auth.add_balance(conn, user_id, float(row["amount_jpy"]))


def mask_key_id(key_id: str) -> str:
    """二次表示用: ユニークID+CRC部分を伏字にする（固定値4桁だけ見せる）。
    ※フルキー(シークレット込み)を渡さないこと。"""
    if len(key_id) != KEY_ID_DIGITS:
        return "*" * len(key_id)
    return key_id[:FIXED_DIGITS] + "*" * (KEY_ID_DIGITS - FIXED_DIGITS)
