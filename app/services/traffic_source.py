"""流入元(どこから来た訪問か)の抽出と分類（2026-09-19・計測設計フェーズ1
3-A）。`visitor_kind`(ボット判定)に隣接して置く「誰が/どこから来たか」の
判定材料。

記録するのは**ホスト名だけ**のreferrerと、許可キーだけのutm_*、広告クリック
ID(gclid等)の**有無だけ**。URLのパス/クエリ全体・gclid等の値そのものは
どこにも保存しない（個人情報・広告主側の識別子を持ち込まないため）。

チャネル分類は`classify_channel`。集計側(app/routers/system.py)で
landing_visitsのreferrer_host/utm_*/has_gclid/landing_pathから都度計算する
（保存するのは生の材料だけ。判定リストを後から更新すれば過去分にも効く）。
"""

from __future__ import annotations

import re
from urllib.parse import parse_qs, urlsplit

# 記録を許可するutmキー。これ以外のクエリキーは一切保存しない。
UTM_KEYS = ("utm_source", "utm_medium", "utm_campaign", "utm_content")
UTM_MAX_LEN = 64

# 広告クリックIDのキー。値は保存せず「いずれかが付いていたか」だけを見る。
# gclid=Google広告のクリックID、gbraid/wbraid=iOS等のプライバシー制限下の
# 広告クリック識別子。
AD_CLICK_KEYS = ("gclid", "gbraid", "wbraid")

# 自サイトのホスト。referrerがこれなら「サイト内遷移」(例: 用語集→アプリ)。
_OWN_HOST_SUFFIXES = ("nyangailab.com",)
_OWN_HOSTS = ("localhost", "127.0.0.1")

# SEO/LLMO用の公開入口ページ(app/routers/seo_pages.py)。landing_visitsへの
# 記録対象を`/`・about・`/login`からここまで広げる(前方一致・/glossary/宇宙
# のような動的パスも含む)。
SEO_PATH_PREFIXES = ("/glossary", "/phrasebook", "/crossword")

# --- LLM(生成AI・AI検索)経由 ----------------------------------------------
# referrer_hostがこれらなら「LLM経由」。ChatGPTは出典リンクに
# utm_source=chatgpt.com を自動付与することがある【要確認・仕様は変わりうる】
# ため、utm_sourceも同じ語彙で見る。今後増えるので随時追記すること。
LLM_HOSTS = (
    "chatgpt.com", "chat.openai.com", "openai.com",
    "perplexity.ai", "www.perplexity.ai",
    "claude.ai", "gemini.google.com", "bard.google.com",
    "copilot.microsoft.com", "copilot.cloud.microsoft",
    "you.com", "phind.com", "poe.com", "chat.deepseek.com", "grok.com",
    "meta.ai",
)
_LLM_UTM_SOURCES = (
    "chatgpt.com", "chatgpt", "perplexity", "perplexity.ai", "claude",
    "claude.ai", "gemini", "copilot", "openai",
)

# --- 検索エンジン ----------------------------------------------------------
# google.*は素朴な部分一致だとmail.google.com等まで検索扱いになるため、
# 下の_GOOGLE_SEARCH_REで別途判定する。
_GOOGLE_SEARCH_RE = re.compile(r"^(www\.)?google\.[a-z.]{2,7}$")
# TLDが国別に変わるもの(yahoo.co.jp/yahoo.com・yandex.ru/.com等)。
_SEARCH_WILDCARD_RE = re.compile(r"(^|\.)(yahoo|yandex)\.[a-z.]{2,7}$")
_SEARCH_HOSTS = (
    "bing.com", "duckduckgo.com", "ecosia.org", "baidu.com", "naver.com",
    "search.brave.com", "startpage.com", "qwant.com", "goo.ne.jp",
    "biglobe.ne.jp", "sogou.com",
    "com.google.android.googlequicksearchbox",  # Androidの検索アプリ
)

# --- SNS・記事プラットフォーム ---------------------------------------------
# 宣伝に使っているnote/Qiita/X/Instagram/YouTubeを含める。
# t.co/x.comのような短いホストは部分一致だとmicrosoft.com等を巻き込むため、
# ホスト完全一致かサブドメイン一致(_host_in)だけで見る。
_SNS_HOSTS = (
    "twitter.com", "x.com", "t.co", "instagram.com", "facebook.com",
    "fb.com", "line.me", "youtube.com", "youtu.be", "note.com", "qiita.com",
    "zenn.dev", "hatena.ne.jp", "hatenablog.com", "reddit.com",
    "linkedin.com", "lnkd.in", "threads.net", "tiktok.com", "bsky.app",
    "discord.com", "slack.com", "medium.com",
)
_SNS_WILDCARD_RE = re.compile(r"(^|\.)pinterest\.[a-z.]{2,7}$")
_SNS_UTM_SOURCES = (
    "x", "twitter", "instagram", "facebook", "youtube", "note", "qiita",
    "zenn", "line", "threads", "tiktok", "reddit", "linkedin",
)

# チャネルのキーと表示名（画面は日本語表示・順序もこの並び）。
CHANNELS = (
    ("ad", "広告(Google広告等)"),
    ("llm", "生成AI(LLM)経由"),
    ("search", "検索"),
    ("sns", "SNS・記事"),
    ("internal", "サイト内遷移"),
    ("direct", "直接(参照元なし)"),
    ("other", "その他のサイト"),
)
CHANNEL_LABELS = dict(CHANNELS)

_CTRL_RE = re.compile(r"[\x00-\x1f\x7f]")


def _clean(value: str, limit: int) -> str:
    return _CTRL_RE.sub("", value or "").strip()[:limit]


def referrer_host_of(referer: str) -> str:
    """Refererヘッダ値からホスト名だけを取り出す（パス/クエリは捨てる）。
    不正な値・空は空文字。"""
    try:
        parts = urlsplit((referer or "").strip())
        host = (parts.hostname or "").lower()
    except ValueError:
        return ""
    return _clean(host, 100)


def extract(referer: str, query: str) -> dict:
    """1リクエストから流入元の材料を取り出す。返す値はすべて記録して
    よい形（ホスト名・許可utmキー・広告クリックIDの有無）に絞ってある。"""
    try:
        qs = parse_qs(query or "", keep_blank_values=True)
    except Exception:
        qs = {}
    out = {"referrer_host": referrer_host_of(referer)}
    for k in UTM_KEYS:
        vals = qs.get(k) or [""]
        out[k] = _clean(vals[0], UTM_MAX_LEN)
    # 値は見ない・保存しない（キーが存在するかだけ）。
    out["has_gclid"] = 1 if any(k in qs for k in AD_CLICK_KEYS) else 0
    return out


def is_own_host(host: str) -> bool:
    h = (host or "").lower()
    return h in _OWN_HOSTS or any(
        h == s or h.endswith("." + s) for s in _OWN_HOST_SUFFIXES)


def _host_in(host: str, names: tuple[str, ...]) -> bool:
    """ホストが names のいずれかと完全一致、またはそのサブドメインか。"""
    return any(host == n or host.endswith("." + n) for n in names)


def is_llm(referrer_host: str, utm_source: str = "") -> bool:
    h = (referrer_host or "").lower()
    if h and any(h == n or h.endswith("." + n) for n in LLM_HOSTS):
        return True
    return (utm_source or "").lower() in _LLM_UTM_SOURCES


def classify_channel(
    referrer_host: str, utm_source: str = "", utm_medium: str = "",
    has_gclid: int | bool = 0,
) -> str:
    """流入チャネルのキーを返す（CHANNELSのいずれか）。優先順位: 広告 >
    生成AI > 検索 > SNS・記事 > サイト内遷移 > その他 > 直接。"""
    host = (referrer_host or "").lower()
    source = (utm_source or "").lower()
    medium = (utm_medium or "").lower()
    if has_gclid or medium in ("cpc", "ppc", "paid", "paidsearch", "ad", "ads"):
        return "ad"
    if is_llm(host, source):
        return "llm"
    if (medium == "organic" or _GOOGLE_SEARCH_RE.match(host)
            or _SEARCH_WILDCARD_RE.search(host) or _host_in(host, _SEARCH_HOSTS)):
        return "search"
    if (source in _SNS_UTM_SOURCES or _host_in(host, _SNS_HOSTS)
            or _SNS_WILDCARD_RE.search(host)):
        return "sns"
    if host and is_own_host(host):
        return "internal"
    if host:
        return "other"
    # 参照元なしでもutm_sourceだけ付いた宣伝リンクは「その他」に寄せる
    # (直接アクセスと区別するため)。
    return "other" if source else "direct"


def is_seo_path(path: str) -> bool:
    """`/glossary` `/glossary/xxx` のようなSEO入口ページか。`/glossaryx`
    のような別パスを誤検出しないよう、完全一致か`/`区切りの配下だけを見る。"""
    p = path or ""
    return any(p == s or p.startswith(s + "/") for s in SEO_PATH_PREFIXES)


def landing_group(path: str) -> str:
    """着地ページの大分類（ページ別の入口の強さを見る用）。"""
    p = path or ""
    if p == "/":
        return "アプリ(トップ)"
    if p == "/static/about.html":
        return "このアプリについて"
    if p == "/login":
        return "ログイン/登録"
    for s in SEO_PATH_PREFIXES:
        if p == s or p.startswith(s + "/"):
            return {"/glossary": "用語集", "/phrasebook": "フレーズ集",
                    "/crossword": "クロスワード紹介"}[s]
    return p or "(不明)"
