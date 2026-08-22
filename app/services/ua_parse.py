"""User-Agent から端末種別・ブラウザ名を推定する（2026-08-23ユーザー要望）。

管理画面「未登録アクセス状況」はIPから国/地域/接続元組織を解析して表示
しているが、それに加えて「iPad/Android/Windows/Mac」「Chrome/Safari/Edge」
のような端末・ブラウザも分かった方が実態を把握しやすい、という要望に
対応する。visitor_kind.py（ボット判定）と同様、外部ライブラリを使わず
User-Agent文字列の部分一致だけで判定する簡易パーサー。

**既知の限界**（判定材料がUAのみである以上、避けられない）:
- iPadOS 13以降のSafariは既定でデスクトップ版を名乗るため、UAだけでは
  実機のMacと区別できない（"Macintosh"と表示される。タッチ操作の有無等
  は取得していないため判定不可）。
- UAは詐称可能。あくまで「自己申告」の範囲の推定値として扱うこと。
"""

from __future__ import annotations

import re

_UNKNOWN = "不明"

# 判定順序が重要（例: EdgeもChromeもUAに"Safari"を含むため、先に固有の
# トークンを見る）。
_BROWSER_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Edge", re.compile(r"edg(a|ios)?/", re.IGNORECASE)),
    ("Opera", re.compile(r"(opr|opios)/|\bopera\b", re.IGNORECASE)),
    ("Samsung Internet", re.compile(r"samsungbrowser/", re.IGNORECASE)),
    ("Chrome", re.compile(r"(chrome|crios|headlesschrome)/", re.IGNORECASE)),
    ("Firefox", re.compile(r"(firefox|fxios)/", re.IGNORECASE)),
    # Safari判定はChrome系の後(ChromeもUAに"Safari/"を含むため)。
    ("Safari", re.compile(r"safari/", re.IGNORECASE)),
)

# 判定順序が重要（例: AndroidのUAにも"Linux"が含まれるため先に見る／
# iPadOS 13+はデフォルトで"iPad"を含まずMacintoshを名乗る点に注意）。
_DEVICE_RULES: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("iPad", re.compile(r"ipad", re.IGNORECASE)),
    ("iPhone", re.compile(r"iphone", re.IGNORECASE)),
    ("Android", re.compile(r"android", re.IGNORECASE)),
    ("Windows", re.compile(r"windows", re.IGNORECASE)),
    ("Mac", re.compile(r"macintosh|mac os x", re.IGNORECASE)),
    ("Linux", re.compile(r"linux", re.IGNORECASE)),
    ("ChromeOS", re.compile(r"cros", re.IGNORECASE)),
)


def parse_ua(user_agent: str) -> tuple[str, str]:
    """1つのUA文字列から (端末, ブラウザ) を返す。判定不可はどちらも"不明"。"""
    ua = user_agent or ""
    device = _UNKNOWN
    for label, pat in _DEVICE_RULES:
        if pat.search(ua):
            device = label
            break
    browser = _UNKNOWN
    for label, pat in _BROWSER_RULES:
        if pat.search(ua):
            browser = label
            break
    return device, browser


def summarize(user_agents: list[str]) -> tuple[str, str]:
    """同一IPで観測された複数UAから、代表的な (端末, ブラウザ) 表示文字列を作る。

    IP単位の集計なので同一IPに複数端末が混ざることがある。1種類なら
    そのまま、複数種類あれば "/" 区切りで全部並べる（"不明"は他に判定
    できたものがあれば除く）。"""
    devices: list[str] = []
    browsers: list[str] = []
    for ua in user_agents:
        d, b = parse_ua(ua)
        if d not in devices:
            devices.append(d)
        if b not in browsers:
            browsers.append(b)

    def _fmt(values: list[str]) -> str:
        known = [v for v in values if v != _UNKNOWN]
        if known:
            return "/".join(known)
        return _UNKNOWN if values else ""

    return _fmt(devices), _fmt(browsers)
