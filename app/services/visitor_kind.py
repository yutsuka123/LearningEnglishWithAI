"""未登録アクセスの訪問者種別の推定（2026-08-21・ユーザー要望）。

管理画面「未登録アクセス状況」の一覧で、各行が「人間が意識的に見に来た
アクセス」なのか、クローラー等の機械的なアクセスなのかを見分けるための
分類。表を横に広げないよう、画面上は「※1」〜「※4」の印だけを出し、
意味は表の下の欄外備考で説明する。

  ※1 管理者自身          … .env の ADMIN_KNOWN_IPS に登録したIP
  ※2 検索エンジン等のクローラーの可能性
  ※3 AI検索クローラーの可能性
  ※4 その他、普通のユーザーではないものの可能性
  (印なし) … たまたま/興味を持って等を問わず、人間が意識的に閲覧したもの

**あくまで推定**である点に注意。判定材料は User-Agent と、IPの接続元組織
(ip_geo_cache.org / PTRホスト名)しかない。UAは詐称できるし、逆に
データセンター経由でアクセスする人間（VPN利用者等）を※4と誤判定しうる。
「印が付いていない＝確実に人間」ではなく「機械的アクセスの兆候が
見つからなかった」という意味で読むこと。

判定の優先順位は 管理者 > AI > 検索/SNS > その他ボット。1つのIPに複数の
UAがある場合は、機械的アクセスの兆候が1つでもあれば印を付ける
（IP単位の集計なので、共有IPで人間とボットが混ざる可能性はある）。
"""

from __future__ import annotations

import re

MARK_NONE = 0
MARK_ADMIN = 1
MARK_SEARCH_BOT = 2
MARK_AI_BOT = 3
MARK_OTHER_BOT = 4

# --- ※3 AI検索・AI学習クローラー ------------------------------------------
# 生成AIの検索/学習用クローラー。2026-08-21時点で実際に本番へ来ていたのは
# GPTBot と meta-externalagent。今後増えるので随時追記すること。
_AI_BOTS = (
    "gptbot", "oai-searchbot", "chatgpt-user",
    "claudebot", "claude-web", "claude-searchbot", "anthropic-ai",
    "perplexitybot", "perplexity-user",
    "google-extended", "meta-externalagent", "meta-externalfetcher",
    "applebot-extended", "bytespider", "ccbot", "cohere-ai",
    "amazonbot", "youbot", "diffbot", "timpibot", "omgili",
    "ai2bot", "imagesiftbot", "duckassistbot", "mistralai-user",
)

# --- ※2 検索エンジンのクローラー / SNSのリンクプレビュー ------------------
# SNSプレビュー(facebookexternalhit・Twitterbot・LINE・Chatwork等)もここに
# 含める。悪意のあるものではなく「誰かがURLを共有した結果」なので、
# ※4(普通のユーザーではない)より※2の方が実態に合う。
# 実際、本番の facebookexternalhit / line-poker / Chatwork LinkPreview は
# Instagram等での告知にURLを貼った結果と考えられる。
_SEARCH_BOTS = (
    "googlebot", "google-inspectiontool", "storebot-google",
    "adsbot-google", "mediapartners-google", "feedfetcher-google",
    "apis-google", "bingbot", "adidxbot", "bingpreview", "msnbot",
    "slurp", "duckduckbot", "duckduckgo", "baiduspider", "yandexbot",
    "sogou", "exabot", "petalbot", "seznambot", "naver", "yeti",
    "ia_archiver", "archive.org_bot", "applebot", "coccocbot", "mojeekbot",
    # SEO・マーケティング系の巡回。素性を名乗っている点で※4のスキャナとは
    # 性質が違うのでこちらに入れる。
    "ahrefsbot", "semrushbot", "mj12bot", "dotbot", "blexbot",
    "dataforseo", "serpstatbot", "sitecheckerbot", "screaming frog",
    # SNS・チャットのリンクプレビュー
    "facebookexternalhit", "twitterbot", "linkedinbot", "slackbot",
    "slack-imgproxy", "discordbot", "telegrambot", "whatsapp",
    "line-poker", "linespider", "chatwork", "skypeuripreview",
    "embedly", "pinterest", "redditbot", "tumblr", "vkshare",
    "flipboard", "hatena",
)

# --- ※4 その他（HTTPクライアント・脆弱性/インフラスキャナ等）-------------
# 本番で実際に来ていたもの: curl, l9scan(leakix), CensysInspect,
# Palo Alto Networks(Cortex Xpanse), NetcraftSurveyAgent,
# visionheight.com/scan, CMS-Checker。
_OTHER_BOTS = (
    # 素のHTTPクライアント（ブラウザではない＝人間が見に来てはいない）
    "curl/", "wget", "python-requests", "python-httpx", "aiohttp",
    "go-http-client", "java/", "libwww", "lwp::", "okhttp", "scrapy",
    "node-fetch", "axios", "guzzle", "postmanruntime", "insomnia",
    # ヘッドレスブラウザ（自動化）
    "headlesschrome", "phantomjs", "puppeteer", "playwright", "selenium",
    # スキャナ・調査系
    "masscan", "zgrab", "nmap", "censysinspect", "censys", "l9scan",
    "leakix", "netcraft", "paloaltonetworks", "expanse", "cortex",
    "internet-measurement", "shodan", "binaryedge", "projectdiscovery",
    "nuclei", "sqlmap", "nikto", "dirbuster", "gobuster", "wpscan",
    "cms-checker", "uptimerobot", "pingdom", "statuscake", "site24x7",
    # 2026-08-21に実際に来ていた/よく見かけるスキャナを追記。
    "rootevidence", "onyphe", "mandiant", "criminalip", "stretchoid",
    "netsystemsresearch", "securitytrails", "bufferover", "driftnet",
    "alphastrike", "zoominfobot", "sysscan", "odin",
)

# 汎用の取りこぼし用。単語境界で見るのは、Android端末の "CUBOT" のような
# 機種名を "bot" と誤検出しないため（\b があるので語中の bot は当たらない）。
_GENERIC_BOT_RE = re.compile(
    r"\b(bot|bots|spider|crawler|crawl|scraper|fetcher|scanner|scan"
    r"|probe|monitoring|checker)\b|[-+/]bot\b",
    re.IGNORECASE,
)

# データセンター/ホスティング/プラットフォーム事業者。ブラウザを名乗って
# いても、家庭用回線ではなくサーバーからのアクセスなので機械的アクセスの
# 可能性が高い。
# ※VPN経由の人間もここに入りうる（誤判定しうる点はUIの備考で明示する）。
# ※このリストは「見かけたら足す」性質のもの。管理画面で「印なし」なのに
#   明らかにサーバーからのアクセスに見える行があれば、ここに追記する。
_HOSTING_ORGS = (
    # 大手クラウド
    "amazon", "aws", "google llc", "google cloud", "microsoft", "azure",
    "digitalocean", "ovh", "linode", "hetzner", "contabo", "leaseweb",
    "vultr", "choopa", "oracle", "alibaba", "tencent", "scaleway",
    "g-core", "zenlayer", "m247",
    # SNS/プラットフォーム事業者のAS（一般家庭の回線ではない）
    "facebook", "twitter", "apple inc", "line corporation",
    # セキュリティ調査・スキャン事業者
    "censys", "palo alto", "onyphe", "mandiant", "carinet", "cari.net",
    # 2026-08-21に実際に来ていた小規模VPS/ホスティング事業者
    "racknerd", "packethub", "techoff", "code200", "egihosting",
    "hydra communications", "zkillu", "h4y technologies",
    "white label services", "netiface", "light node", "bestdc",
    "green floid", "bl networks", "valence technology",
    "storm industries", "buyvm", "frantech",
    # 汎用キーワード
    "hosting", "datacenter", "data center", "vps", "colo", "dedi",
)
# 意図的に入れていない語:
# - "llc" "limited" "inc" のような法人格の語、"cloud" "server" のような
#   一般語。組織名の大半に含まれてしまい家庭用回線の事業者まで誤判定する。
# - Cloudflare / Akamai / Fastly。**iCloudプライベートリレー**や
#   Cloudflare WARP の出口IPがこれらの事業者名になるため、実在するiPhone
#   ユーザーを※4と誤判定してしまう（2026-08-21・意図的な除外）。


def _match(haystack: str, needles: tuple[str, ...]) -> str:
    for n in needles:
        if n in haystack:
            return n
    return ""


def classify_ua(user_agent: str) -> tuple[int, str]:
    """User-Agent 単体での判定。(mark, 理由) を返す。該当なしは (0, "")。"""
    ua = (user_agent or "").strip().lower()
    if not ua:
        return MARK_OTHER_BOT, "User-Agentが空（通常のブラウザは必ず送る）"
    hit = _match(ua, _AI_BOTS)
    if hit:
        return MARK_AI_BOT, f"UAに「{hit}」を含む"
    hit = _match(ua, _SEARCH_BOTS)
    if hit:
        return MARK_SEARCH_BOT, f"UAに「{hit}」を含む"
    hit = _match(ua, _OTHER_BOTS)
    if hit:
        return MARK_OTHER_BOT, f"UAに「{hit}」を含む"
    # 実在するブラウザ（スマホアプリ内ブラウザ含む）はほぼ例外なく
    # "Mozilla/" で始まる文字列を送る。これが無いものはツール/スキャナと
    # 判断してよい。本番では "pc" だけのUAや "RootEvidence/1.0"、
    # "Hello from Palo Alto Networks" 等がこれで拾える（2026-08-21）。
    if "mozilla/" not in ua:
        return MARK_OTHER_BOT, "UAが実在ブラウザの体裁でない（Mozilla/ を含まない）"
    # "Mozilla/5.0 (compatible)" だけ等、名乗りが実質空のもの。
    if len(ua) < 32:
        return MARK_OTHER_BOT, "UAが短すぎ実在ブラウザの体裁でない"
    m = _GENERIC_BOT_RE.search(ua)
    if m:
        return MARK_OTHER_BOT, f"UAに「{m.group(0)}」を含む"
    return MARK_NONE, ""


def classify(
    user_agents: list[str], org: str, hostname: str, is_admin: bool
) -> tuple[int, str]:
    """1つのIPについての判定。(mark, 理由) を返す。

    user_agents はそのIPで観測された全UA。1つでも機械的アクセスの兆候が
    あれば印を付ける（優先度: 管理者 > AI > 検索/SNS > その他）。"""
    if is_admin:
        return MARK_ADMIN, "ADMIN_KNOWN_IPS に登録済み"

    best = MARK_NONE
    reason = ""
    # 優先度順に見たいので、mark の小さい方(=AI 3 より 検索 2)ではなく
    # 明示的な順序表で比較する。
    priority = {MARK_AI_BOT: 3, MARK_SEARCH_BOT: 2, MARK_OTHER_BOT: 1,
                MARK_NONE: 0}
    for ua in user_agents:
        mark, why = classify_ua(ua)
        if priority[mark] > priority[best]:
            best, reason = mark, why
    if best != MARK_NONE:
        return best, reason

    # UAからは分からなかったが、接続元がデータセンター/ホスティングの場合。
    # 家庭用回線・携帯キャリアではないので、サーバーからの自動アクセスの
    # 可能性が高い（VPN経由の人間の可能性も残るため「可能性」と表現する）。
    who = f"{org} {hostname}".lower()
    hit = _match(who, _HOSTING_ORGS)
    if hit:
        return MARK_OTHER_BOT, f"接続元がデータセンター/ホスティング（{org or hostname}）"
    return MARK_NONE, ""
