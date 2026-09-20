"""IPアドレスの保持期限(360日)を守る処理(2026-09-21・プライバシーポリシー§9)。

取得から360日を過ぎた行のIPアドレスを、復元できない変換値(HMAC-SHA256)へ
置き換える。毎日03:45の`scripts/prune_usage_events.py`から呼ぶ(cronの追加は不要)。

設計:
- **鍵付きHMAC**にする。IPv4は約43億通りしかなく、鍵の無いSHA-256は総当たりで
  元に戻せる(=匿名化にならない)ため。鍵は`get_session_secret`から用途別に派生
  させる(セッション鍵そのものはハッシュ計算に使わない)。鍵が取れなければ何も
  しない(鍵なしでハッシュ化することはしない)。
- 変換値は`h:`+16進20桁。`h:`で始まる値は処理済みとして再処理しない(冪等)。
  同じIPは同じ変換値になるので、期限後も「何種類のIPか」の集計はできる。
  セッション鍵を変えると以後の変換値は変わる(過去分との突き合わせは不可)。
- IPとして解釈できない値(空・`?`等)は触らない。既存コードはIPでない文字列を
  安全に扱える(geoip._is_public_ip/reverse_dnsで確認済み)。
- 位置情報のキャッシュ(ip_geo_cache)はIPが主キーの生IP保存なので、変換ではなく
  期限を過ぎたものを削除する(次回訪問時に再取得されるだけの派生データ)。
- 対象は「アクセス記録」に当たる、IPを持つ全テーブル。削除ではなく置き換えなので
  行数・集計(guest_sidベースのファネル等)は変わらない。
"""

from __future__ import annotations

import hashlib
import hmac
import ipaddress
import sqlite3
from datetime import datetime, timedelta

from .auth import get_session_secret

IP_KEEP_DAYS = 360
HASH_PREFIX = "h:"

# (テーブル, 日付列)。ATTACH済みのlogs/coreどちらのテーブルも修飾なしで引ける
# (テーブル名は全DBで一意・database._check_no_duplicate_table_names)。
_IP_TABLES = (
    ("landing_visits", "created_at"),
    ("login_log", "created_at"),
    ("usage_events", "created_at"),
    ("client_errors", "created_at"),
    ("ai_usage", "created_at"),
    ("charge_key_attempts", "created_at"),
)
_GEO_CACHE = ("ip_geo_cache", "fetched_at")


def _is_ip(value: str) -> bool:
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def derive_key(conn: sqlite3.Connection) -> bytes:
    """IP変換専用の鍵(セッション鍵から用途別に派生)。"""
    base = get_session_secret(conn)
    return hmac.new(base, b"ip-retention-v1", hashlib.sha256).digest()


def hash_ip(ip: str, key: bytes) -> str:
    return HASH_PREFIX + hmac.new(
        key, ip.encode("utf-8"), hashlib.sha256).hexdigest()[:20]


def anonymize_old_ips(
    conn: sqlite3.Connection, *, now: datetime,
    keep_days: int = IP_KEEP_DAYS, dry_run: bool = False,
) -> dict[str, int]:
    """期限(now-keep_days)より古い行のIPを変換し、テーブルごとの変換行数を
    返す(dry_run=Trueなら書き込まず、変換対象の行数を返す)。
    位置情報キャッシュは`ip_geo_cache`キーに削除件数(dry_runなら対象件数)。"""
    cutoff = (now - timedelta(days=keep_days)).strftime("%Y-%m-%d %H:%M:%S")
    key = derive_key(conn)
    out: dict[str, int] = {}
    for table, col in _IP_TABLES:
        ips = [r[0] for r in conn.execute(
            f"SELECT DISTINCT ip FROM {table} "
            f"WHERE {col} < ? AND ip IS NOT NULL AND ip <> '' "
            f"AND ip NOT LIKE '{HASH_PREFIX}%'", (cutoff,)).fetchall()]
        n = 0
        for ip in ips:
            if not _is_ip(ip):
                continue
            if dry_run:
                n += conn.execute(
                    f"SELECT COUNT(*) FROM {table} "
                    f"WHERE ip = ? AND {col} < ?", (ip, cutoff)).fetchone()[0]
            else:
                n += conn.execute(
                    f"UPDATE {table} SET ip = ? WHERE ip = ? AND {col} < ?",
                    (hash_ip(ip, key), ip, cutoff)).rowcount
        out[table] = n
    gtable, gcol = _GEO_CACHE
    if dry_run:
        out[gtable] = conn.execute(
            f"SELECT COUNT(*) FROM {gtable} WHERE {gcol} < ?",
            (cutoff,)).fetchone()[0]
    else:
        out[gtable] = conn.execute(
            f"DELETE FROM {gtable} WHERE {gcol} < ?", (cutoff,)).rowcount
    return out
