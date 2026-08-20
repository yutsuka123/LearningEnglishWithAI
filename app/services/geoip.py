"""IPアドレスからの国・地域・組織名の付与（2026-08-20〜）。

管理画面「未登録アクセス状況」で、匿名訪問者のIPから国・場所・接続元の
プロバイダ/会社名をざっくり表示するために使う。外部API(ipapi.co・HTTPS・
サインアップ不要・無料枠あり)を1IPにつき1回だけ呼び出し、結果を
``ip_geo_cache`` に永続キャッシュする（ユーザー確認済み: 2026-08-20、
「外部APIで取得(推奨)」を選択）。

呼び出しは必ずバックグラウンド(fire-and-forget)で行うこと。この関数の
失敗はアプリの主要機能（ページ表示・登録・ログイン）を一切妨げてはい
けない（例外はすべてここで握りつぶす）。
"""

from __future__ import annotations

import ipaddress

import httpx

from ..config import log
from ..database import db
from .auth import reverse_dns

_GEO_URL = "https://ipapi.co/{ip}/json/"
_TIMEOUT = 3.0


def _is_public_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not (
        addr.is_private or addr.is_loopback or addr.is_link_local
        or addr.is_reserved or addr.is_multicast or addr.is_unspecified
    )


def enrich_ip(ip: str) -> None:
    """IPの位置情報を取得して ip_geo_cache に保存する（未キャッシュの
    公開IPのみ・キャッシュ済み/private/loopback等は即return）。
    BackgroundTasks / asyncio.create_task から呼ぶ想定。"""
    if not ip or not _is_public_ip(ip):
        return
    with db() as conn:
        if conn.execute(
            "SELECT 1 FROM ip_geo_cache WHERE ip = ?", (ip,)
        ).fetchone():
            return
    hostname = reverse_dns(ip)
    country = region = city = org = ""
    error = ""
    try:
        resp = httpx.get(
            _GEO_URL.format(ip=ip), timeout=_TIMEOUT,
            headers={"User-Agent": "study-nyangailab-geoip/1.0"},
        )
        data = resp.json()
        if data.get("error"):
            error = str(data.get("reason") or "unknown")
        else:
            country = data.get("country_name") or ""
            region = data.get("region") or ""
            city = data.get("city") or ""
            org = data.get("org") or ""
    except Exception as e:  # noqa: BLE001 — 外部APIの失敗は握りつぶす
        error = str(e)
        log.warning("geoip: lookup failed ip=%s reason=%s", ip, e)
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO ip_geo_cache "
            "(ip, country, region, city, org, hostname, error, fetched_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
            (ip, country, region, city, org, hostname, error),
        )
