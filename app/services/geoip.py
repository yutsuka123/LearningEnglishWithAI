"""IPアドレスからの国・地域・組織名の付与（2026-08-20〜）。

管理画面「未登録アクセス状況」で、匿名訪問者のIPから国・場所・接続元の
プロバイダ/会社名をざっくり表示するために使う。外部API(HTTPS・サイン
アップ不要・無料枠あり)を1IPにつき1回だけ呼び出し、結果を
``ip_geo_cache`` に永続キャッシュする（ユーザー確認済み: 2026-08-20、
「外部APIで取得(推奨)」を選択）。

2026-08-21: 取りこぼしの一括補完(scripts/backfill_geoip.py)を流したところ
ipapi.co が **HTTP 429 をプレーンテキストで返す**（無料枠のバースト制限）
ことが判明。旧実装は ``resp.json()`` を無条件に呼んでいたため、
「Expecting value: line 1 column 1」という原因の分かりにくい例外が
error 列に入るだけで、レート制限だと気づけなかった。そこで
  1. HTTPステータス/非JSON応答を明示的に扱う
  2. ipapi.co が駄目なとき ipwho.is にフォールバックする
の2点を追加した。ipapi.co を第一候補に残しているのは、2026-08-20に
ユーザーが選択した事業者だから（フォールバックは失敗時のみ動く）。
どちらもIPを送るだけでプライバシーポリシー7項「サービス提供に必要な
範囲で外部サービスを利用する場合」の範囲内（事業者名は特定していない）。

呼び出しは必ずバックグラウンド(fire-and-forget)で行うこと。この関数の
失敗はアプリの主要機能（ページ表示・登録・ログイン）を一切妨げてはい
けない（例外はすべてここで握りつぶす）。
"""

from __future__ import annotations

import ipaddress
from typing import Callable

import httpx

from ..config import log
from ..database import db
from .auth import reverse_dns

_TIMEOUT = 5.0
_UA = "study-nyangailab-geoip/1.0"

# 取得結果。country が空なら「取得できなかった」とみなす（管理画面では
# 結局「—」表示になるので、backfill の再試行対象にもなる）。
_Geo = dict[str, str]


def _is_public_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return not (
        addr.is_private or addr.is_loopback or addr.is_link_local
        or addr.is_reserved or addr.is_multicast or addr.is_unspecified
    )


def _fetch_json(client: httpx.Client, name: str, url: str) -> tuple[dict, str]:
    """JSONを取って (data, error) を返す。errorが空でなければ失敗。
    ipapi.co はレート超過時に text/plain で 429 を返すため、
    status_code と Content-Type の両方を見てから json() を呼ぶ。"""
    resp = client.get(url, headers={"User-Agent": _UA})
    if resp.status_code != 200:
        # 429 は無料枠のレート制限。日を改めるか間隔を空ければ復帰する。
        return {}, f"{name} HTTP {resp.status_code}"
    try:
        data = resp.json()
    except ValueError:
        return {}, f"{name} 非JSON応答({resp.headers.get('content-type', '?')})"
    if not isinstance(data, dict):
        return {}, f"{name} 予期しない応答形式"
    return data, ""


def _lookup_ipapi(client: httpx.Client, ip: str) -> tuple[_Geo, str]:
    data, err = _fetch_json(client, "ipapi.co", f"https://ipapi.co/{ip}/json/")
    if err:
        return {}, err
    if data.get("error"):
        return {}, f"ipapi.co {data.get('reason') or 'unknown'}"
    return {
        "country": data.get("country_name") or "",
        "region": data.get("region") or "",
        "city": data.get("city") or "",
        "org": data.get("org") or "",
    }, ""


def _lookup_ipwhois(client: httpx.Client, ip: str) -> tuple[_Geo, str]:
    data, err = _fetch_json(client, "ipwho.is", f"https://ipwho.is/{ip}")
    if err:
        return {}, err
    if not data.get("success"):
        return {}, f"ipwho.is {data.get('message') or 'unknown'}"
    conn = data.get("connection") or {}
    return {
        "country": data.get("country") or "",
        "region": data.get("region") or "",
        "city": data.get("city") or "",
        # connection.org は「AS所有組織」、isp は「回線事業者」。
        # 管理画面は接続元の会社名が分かればよいので org を優先する。
        "org": conn.get("org") or conn.get("isp") or "",
    }, ""


# 第一候補は2026-08-20にユーザーが選んだ ipapi.co。失敗時のみ次を試す。
_PROVIDERS: tuple[tuple[str, Callable[[httpx.Client, str], tuple[_Geo, str]]], ...] = (
    ("ipapi.co", _lookup_ipapi),
    ("ipwho.is", _lookup_ipwhois),
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
    geo: _Geo = {}
    errors: list[str] = []
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            for name, lookup in _PROVIDERS:
                try:
                    geo, err = lookup(client, ip)
                except Exception as e:  # noqa: BLE001 — 個別事業者の失敗は次へ
                    geo, err = {}, f"{name} {e}"
                if geo.get("country"):
                    errors = []
                    break
                errors.append(err or f"{name} 空の応答")
    except Exception as e:  # noqa: BLE001 — 外部APIの失敗は握りつぶす
        errors.append(str(e))
    error = " / ".join(errors)
    if error:
        log.warning("geoip: lookup failed ip=%s reason=%s", ip, error)
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO ip_geo_cache "
            "(ip, country, region, city, org, hostname, error, fetched_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))",
            (ip, geo.get("country", ""), geo.get("region", ""),
             geo.get("city", ""), geo.get("org", ""), hostname, error),
        )
