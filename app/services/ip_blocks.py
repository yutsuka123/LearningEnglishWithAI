"""管理画面の「怪しいアクセス」一覧と手動ブロックのロジック(2026-10-31・ver1.5.22)。

役割分担(アプリは「記録」だけ・遮断の実行はホスト側):
- ホスト側cron eigo-f2b-suspects(5分毎)がCaddyのアクセスログをIPごとに要約→アプリへPOST
  (suspicious_access・IPごとに上書き)。
- 管理者が管理画面から「このIPを・この期間ブロック」を押すと manual_blocks に記録するだけ。
- ホスト側cron eigo-f2b-manual-sync(1分毎)が「有効なブロックの一覧」を取得し、fail2banの
  eigo-manual-*のjailへ反映する(期限切れ・解除は一覧から消えるので解除する)。
  アプリからホストのコマンドを直接実行する経路は作らない(既存の解除ボタンと同じ非同期方式)。

安全装置(誤って実ユーザー・運営者を止めないための多重防御。ホスト側でも許可リスト/信頼IPを再確認する):
- 公開IPv4のみ(プライベート/ループバック/予約済み/IPv6は拒否)。
- いま操作している自分のIP・ADMIN_KNOWN_IPS・登録ユーザーのログイン実績のあるIP(信頼IP)は拒否。
- 過去30日に「人間らしい訪問」があるIP(携帯回線・学校/会社の共有IPかもしれない)は、確認(confirm_shared)が無ければ拒否。
- 有効なブロックの上限(合計500・永久200)。
"""

from __future__ import annotations

import ipaddress
import re
from datetime import datetime, timedelta, timezone

from . import auth, errors

# 選べる期間 → (期限までの長さ, ホスト側のjail名)。永久は期限なし。
# jailごとにbantimeが違う(install.shのjailテンプレート): 期限はfail2banが自分でも守る
# (ホスト側cronが止まっても一時ブロックが永久に残らない=安全側に倒れる)。
DURATIONS: dict[str, tuple[timedelta | None, str]] = {
    "1h": (timedelta(hours=1), "eigo-manual-1h"),
    "24h": (timedelta(hours=24), "eigo-manual-24h"),
    "7d": (timedelta(days=7), "eigo-manual-7d"),
    "30d": (timedelta(days=30), "eigo-manual-30d"),
    "permanent": (None, "eigo-manual-perm"),
}
DEFAULT_DURATION = "24h"
MANUAL_JAILS = {jail for _, jail in DURATIONS.values()}
MAX_ACTIVE = 500
MAX_PERMANENT = 200
HUMAN_VISIT_DAYS = 30

_FMT = "%Y-%m-%d %H:%M:%S"
_CTRL = re.compile(r"[\x00-\x1f\x7f]")


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def fmt_utc(dt: datetime) -> str:
    return dt.strftime(_FMT)


def epoch_to_utc(value: float | int | None, default: datetime | None = None) -> str:
    """ホストから来たUNIX秒をUTC文字列に。0・負・未来すぎ/過去すぎは default(既定=今)。"""
    now = default or utc_now()
    try:
        v = float(value or 0)
        if v <= 0:
            return fmt_utc(now)
        dt = datetime.fromtimestamp(v, tz=timezone.utc).replace(tzinfo=None)
    except (OverflowError, OSError, ValueError):
        return fmt_utc(now)
    if dt > now + timedelta(days=1) or dt < now - timedelta(days=400):
        return fmt_utc(now)
    return fmt_utc(dt)


def clean_text(value: str, limit: int) -> str:
    """攻撃者が決められる文字列(パス・UA)から制御文字を除いて切り詰める。
    HTMLの無害化は表示側(escapeHtml)で行う。ここは保存前の最小限の整形。"""
    return _CTRL.sub("", value or "")[:limit]


def parse_ip(value: str):
    """正規化したIPアドレスオブジェクト。不正なら None。"""
    try:
        return ipaddress.ip_address((value or "").strip())
    except ValueError:
        return None


def canonical_public_ipv4(value: str) -> str | None:
    """ブロックの対象にできる(公開IPv4)なら正規化した文字列、そうでなければ None。"""
    ip = parse_ip(value)
    # is_globalだけではマルチキャスト(224.0.0.0/4)を弾けない(Pythonではis_global=True)ため明示的に除く。
    if (ip is None or ip.version != 4 or not ip.is_global or ip.is_multicast
            or ip.is_reserved or ip.is_unspecified or ip.is_loopback or ip.is_link_local):
        return None
    return str(ip)


def suspect_level(row) -> str:
    """怪しさの目安(high/mid/low)。探索は『存在しないURLを叩く』=正規の利用者が踏む理由がないので
    重く見る。しきい値は既存のfail2banのjail(eigo-probe=3回・eigo-loginfail=12回・eigo-ratelimited=60回)
    を『高』の目安にした。"""
    if row["probe"] >= 3 or row["authfail"] >= 12 or row["ratelimited"] >= 60:
        return "high"
    if row["probe"] >= 1 or row["authfail"] >= 5 or row["ratelimited"] >= 10 or row["errors4xx"] >= 30:
        return "mid"
    return "low"


def active_where(alias: str = "") -> str:
    """有効なブロック(解除されておらず期限内)のWHERE条件。"""
    a = f"{alias}." if alias else ""
    return (f"{a}released_at IS NULL AND ({a}expires_at IS NULL "
            f"OR {a}expires_at > datetime('now'))")


def is_trusted_login_ip(conn, ip: str) -> bool:
    """登録ユーザー(アカウント作成から2日以上)が直近30日にログイン成功したIPか。
    ホスト側eigo-f2b-trusted-refreshと同じ条件(信頼IP=BANしない)。"""
    row = conn.execute(
        "SELECT 1 FROM login_log l JOIN users u ON u.username = l.username "
        "WHERE l.success = 1 AND l.ip = ? AND l.created_at >= datetime('now', '-30 days') "
        "AND u.created_at <= datetime(l.created_at, '-2 days') LIMIT 1", (ip,),
    ).fetchone()
    return bool(row)


def human_visit_count(conn, ip: str) -> int:
    """そのIPからの『人間らしい訪問』(botの印なし)の過去30日の件数。共有IPかの目安。"""
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM landing_visits WHERE ip = ? "
        "AND created_at >= datetime('now', ?) AND COALESCE(bot_mark, 0) = 0",
        (ip, f"-{HUMAN_VISIT_DAYS} days"),
    ).fetchone()
    return int(row["n"] or 0)


def create_block(conn, *, ip: str, duration: str, note: str, admin_name: str,
                 requester_ip: str, admin_known_ips: set[str],
                 confirm_shared: bool) -> dict:
    """手動ブロックを記録する(安全装置を通ったときだけ)。拒否は errors.http_error。
    同じIPに有効なブロックがあれば置き換える(旧い行は released_by='superseded')。"""
    if duration not in DURATIONS:
        raise errors.http_error("7002", "ブロックの期間が正しくありません。")
    parsed = parse_ip(ip)
    if parsed is None:
        raise errors.http_error("7002", "IPアドレスの形式が正しくありません。")
    if parsed.version != 4:
        raise errors.http_error("7002", "IPv6は未対応です(遮断の仕組みがIPv4のみ)。")
    canon = canonical_public_ipv4(ip)
    if canon is None:
        raise errors.http_error(
            "7002", "公開IPアドレスではないためブロックできません(社内・ローカル・予約済みの範囲)。")
    if canon == requester_ip or canon in admin_known_ips:
        raise errors.http_error(
            "7002", "運営者自身のIPのためブロックできません(自分が入れなくなります)。")
    if is_trusted_login_ip(conn, canon):
        raise errors.http_error(
            "7002", "登録ユーザーのログイン実績があるIPのためブロックできません"
            "(実ユーザーを巻き込みます)。本当に必要ならVPSで手動実行してください。")
    exempt = conn.execute(
        "SELECT exempt FROM suspicious_access WHERE ip = ?", (canon,)).fetchone()
    if exempt and exempt["exempt"]:
        raise errors.http_error(
            "7002", "許可リスト/信頼IPに当たるためブロックできません。")
    humans = human_visit_count(conn, canon)
    if humans and not confirm_shared:
        raise errors.http_error(
            "7002", f"このIPから過去{HUMAN_VISIT_DAYS}日に人間らしい訪問が{humans}件あります"
            "(携帯回線・学校/会社など共有IPの可能性)。確認のうえ、もう一度ブロックしてください。",
            status=409)
    active = conn.execute(
        f"SELECT COUNT(*) AS n, COALESCE(SUM(expires_at IS NULL), 0) AS perm "
        f"FROM manual_blocks WHERE {active_where()}").fetchone()
    mine = conn.execute(
        f"SELECT COUNT(*) AS n, COALESCE(SUM(expires_at IS NULL), 0) AS perm "
        f"FROM manual_blocks WHERE ip = ? AND {active_where()}", (canon,)).fetchone()
    if int(active["n"]) - int(mine["n"]) >= MAX_ACTIVE:
        raise errors.http_error("7002", f"有効なブロックが上限({MAX_ACTIVE}件)に達しています。不要なものを解除してください。")
    if (duration == "permanent"
            and int(active["perm"]) - int(mine["perm"]) >= MAX_PERMANENT):
        raise errors.http_error("7002", f"永久ブロックが上限({MAX_PERMANENT}件)に達しています。不要なものを解除してください。")
    conn.execute(
        f"UPDATE manual_blocks SET released_at = datetime('now'), released_by = 'superseded' "
        f"WHERE ip = ? AND {active_where()}", (canon,))
    delta, _ = DURATIONS[duration]
    expires = fmt_utc(utc_now() + delta) if delta else None
    cur = conn.execute(
        "INSERT INTO manual_blocks (ip, duration, expires_at, note, created_by) "
        "VALUES (?, ?, ?, ?, ?)",
        (canon, duration, expires, clean_text(note, 200), clean_text(admin_name, 60)))
    return {"id": cur.lastrowid, "ip": canon, "duration": duration, "expires_at": expires}


def require_admin_name(conn) -> str:
    me = auth.require_admin(conn, "管理者のみ利用できます。")
    return str(me.get("username") or "")
