"""利用者に見せるバックエンドのメッセージの多言語化(2026-09-26)。

対応言語は日本語(ja)・英語(en)・中国語簡体字(zh-CN)・中国語繁体字(zh-TW)。
フロント(`static/js/i18n.js`)が現在の表示言語を`X-Lang`ヘッダで全ての
`/api/`リクエストに付与し、`app/main.py`の`_auth_context`ミドルウェアが
それをこのモジュールのcontextvarへ載せる。以後、同じリクエスト内では
`tr()`/`localize_error()`が現在の言語の文言を返す。

設計上の約束:
- **ヘッダが無い・未対応の値なら日本語(従来どおりの挙動)**。Accept-Language
  等からの推測はしない(表示言語の決定権はフロントの言語設定にある)。
- レスポンスのJSONの形(`detail`/`error`/`code`)は変えない。文言だけが変わる。
- 日本語の文言の**正**は、エラーコードなら`errors.ERROR_CODES`・個別の文言なら
  下の`MESSAGES`の`ja`。ログ(`log.*`)・管理画面向けの文言は日本語のまま
  (翻訳しない)。ログには`tr_ja()`を使う。
- 文言に個人情報・キー・内部パスを載せない(呼び出し側の責務)。
- 翻訳の抜けは`scripts/check_message_i18n.py`が検出する。

**フロント側が日本語メッセージの部分一致で分岐していないこと**は2026-09-26に
`static/js`全体をgrepして確認済み(メッセージ本文には依存していない。依存して
いるのは`X-Error-Code`ヘッダ・HTTPステータス・`ok`フラグのみ)。バックエンド内で
唯一あった文字列比較(auth_routes.signupの重複メール判定)は、`ChargeKeyError`の
`str(e)`(常に日本語)との比較のままで、利用者向けの訳は`user_message()`で別に返す。
"""

from __future__ import annotations

import contextvars
from typing import Optional

SUPPORTED = ("ja", "en", "zh-CN", "zh-TW")
DEFAULT_LANG = "ja"

_current_lang: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_lang", default=DEFAULT_LANG)


def normalize_lang(value: Optional[str]) -> str:
    """`X-Lang`ヘッダの値を対応4言語のどれかに正規化する。未指定・未対応は
    日本語。フロントが送るのは`ja`/`en`/`zh-CN`/`zh-TW`だが、手動の確認や
    別クライアントのために`zh`/`zh-Hans`/`zh-Hant`/`zh-HK`等も受け付ける。"""
    if not value:
        return DEFAULT_LANG
    v = value.strip().lower().replace("_", "-")
    if v in ("ja", "ja-jp"):
        return "ja"
    if v == "en" or v.startswith("en-"):
        return "en"
    if v.startswith("zh"):
        if any(t in v for t in ("tw", "hk", "mo", "hant")):
            return "zh-TW"
        return "zh-CN"
    return DEFAULT_LANG


def set_current_lang(header_value: Optional[str]) -> contextvars.Token:
    return _current_lang.set(normalize_lang(header_value))


def reset_current_lang(token: contextvars.Token) -> None:
    _current_lang.reset(token)


def current_lang() -> str:
    return _current_lang.get()


# ---------------------------------------------------------------------------
# エラーコードの既定文言の訳(日本語は errors.ERROR_CODES が正)。
# 値=(en, zh-CN, zh-TW)。管理者・運用者向けのコード(3005/3006/3010〜3015/
# 3017)は翻訳しない(日本語のまま)。
# ---------------------------------------------------------------------------
ERROR_TRANSLATIONS: dict[str, tuple[str, str, str]] = {
    "1001": ("A network error occurred. Please check your signal or Wi-Fi connection and try again.",
             "发生通信错误。请检查信号或Wi-Fi连接后重试。",
             "發生通訊錯誤。請檢查訊號或Wi-Fi連線後再試一次。"),
    "1002": ("There was no response from the server (timeout).",
             "服务器没有响应（超时）。",
             "伺服器沒有回應（逾時）。"),
    "1003": ("You are offline. Please check your network connection.",
             "当前处于离线状态。请检查网络连接。",
             "目前處於離線狀態。請檢查網路連線。"),
    "2001": ("The username or password is incorrect.",
             "用户名或密码错误。",
             "使用者名稱或密碼錯誤。"),
    "2002": ("Too many attempts. Please wait a while and try again.",
             "尝试次数过多。请稍候再试。",
             "嘗試次數過多。請稍候再試。"),
    "2003": ("Sign-in required", "需要登录", "需要登入"),
    "2004": ("Only administrators can use this.",
             "仅管理员可使用。",
             "僅管理員可使用。"),
    "2005": ("Your session has been invalidated. Please log in again.",
             "会话已失效。请重新登录。",
             "工作階段已失效。請重新登入。"),
    "2010": ("The email address format is invalid.",
             "邮箱地址格式不正确。",
             "電子郵件地址格式不正確。"),
    "2011": ("Disposable email addresses cannot be used to register.",
             "无法使用一次性邮箱地址注册。",
             "無法使用一次性電子郵件地址註冊。"),
    "2012": ("The password does not meet the password policy.",
             "密码不符合密码规则。",
             "密碼不符合密碼規則。"),
    "2013": ("Please enter the name you'd like to be called.",
             "请输入希望被称呼的姓名。",
             "請輸入希望被稱呼的姓名。"),
    "2014": ("This email address is already registered.",
             "该邮箱地址已注册。",
             "此電子郵件地址已註冊。"),
    "2015": ("Because of repeated failures, please wait a while before trying again.",
             "由于多次失败，请稍后再试。",
             "由於多次失敗，請稍後再試。"),
    "2016": ("New registrations are currently paused because the service is in a trial release.",
             "目前处于试运行阶段，暂停接受新用户注册。",
             "目前處於試營運階段，暫停接受新使用者註冊。"),
    "3001": ("The charge key is invalid.",
             "充值密钥无效。",
             "儲值金鑰無效。"),
    "3002": ("This charge key has already been used.",
             "该充值密钥已被使用。",
             "此儲值金鑰已被使用。"),
    "3003": ("Too many attempts. Please wait a while and try again.",
             "尝试次数过多。请稍候再试。",
             "嘗試次數過多。請稍候再試。"),
    "3004": ("Your balance is insufficient.", "余额不足。", "餘額不足。"),
    "3016": ("You have reached the limit of the free range. To use more, please top up from the Settings screen.",
             "已达到免费范围的上限。如需继续使用，请在设置页面充值。",
             "已達到免費範圍的上限。如需繼續使用，請在設定頁面儲值。"),
    "3018": ("An error occurred while communicating with PayPay.",
             "与PayPay通信时发生错误。",
             "與PayPay通訊時發生錯誤。"),
    "3019": ("The payment request is invalid.",
             "付款请求的内容无效。",
             "付款請求的內容無效。"),
    "3020": ("This feature is not available right now. We will let you know in the app when it is ready.",
             "此功能目前无法使用。准备就绪后会在应用内通知您。",
             "此功能目前無法使用。準備就緒後會在應用程式內通知您。"),
    "3021": ("You do not have permission to check this payment.",
             "您无权确认此付款。",
             "您無權確認此付款。"),
    "3023": ("You have used up the free trial of \"Details plus\" (10 words). Top up from the settings screen to keep using it.",
             "您已用完“详情plus”的免费试用(10个单词)。请在设置页面充值后继续使用。",
             "您已用完「詳情plus」的免費試用(10個單字)。請在設定頁面儲值後繼續使用。"),
    "3024": ("Your balance is too low for \"Details plus\" (0.25 pt per word). Please top up from the settings screen.",
             "余额不足以使用“详情plus”(每词0.25点)。请在设置页面充值。",
             "餘額不足以使用「詳情plus」(每字0.25點)。請在設定頁面儲值。"),
    "3022": ("Registration (free) is required to purchase with PayPay. Please log in or register first.",
             "使用PayPay购买需要注册(免费)。请先登录/注册后再使用。",
             "使用PayPay購買需要註冊(免費)。請先登入/註冊後再使用。"),
    "4001": ("AI features are not available right now (API key not set).",
             "AI功能目前无法使用(未设置API密钥)。",
             "AI功能目前無法使用(未設定API金鑰)。"),
    "4002": ("You have reached today's AI usage limit. Please wait until the date changes.",
             "已达到今日的AI使用上限。请等到日期变更后再试。",
             "已達到今日的AI使用上限。請等到日期變更後再試。"),
    "4003": ("You have reached this month's AI usage limit.",
             "已达到本月的AI使用上限。",
             "已達到本月的AI使用上限。"),
    "4004": ("AI calls are concentrated right now. Please wait a moment and try again.",
             "AI调用较为集中。请稍候再试。",
             "AI呼叫較為集中。請稍候再試。"),
    "4005": ("The call to the AI service failed. Please try again later.",
             "调用AI服务失败。请稍后重试。",
             "呼叫AI服務失敗。請稍後再試。"),
    "4006": ("The input/output is too long. Please shorten the content and try again.",
             "输入/输出过长。请缩短内容后重试。",
             "輸入/輸出過長。請縮短內容後再試。"),
    "4007": ("This range is not available for free. Please use it after topping up.",
             "此范围无法免费使用。请充值后使用。",
             "此範圍無法免費使用。請儲值後使用。"),
    "5001": ("Your browser does not support this feature.",
             "您的浏览器不支持此功能。",
             "您的瀏覽器不支援此功能。"),
    "5002": ("Failed to save the setting (please check your browser's storage capacity, etc.).",
             "保存设置失败（请检查浏览器的存储容量等）。",
             "儲存設定失敗（請檢查瀏覽器的儲存容量等）。"),
    "5003": ("Failed to access the clipboard.",
             "访问剪贴板失败。",
             "存取剪貼簿失敗。"),
    "6001": ("Microphone access is not allowed. Please check your device settings.",
             "未允许访问麦克风。请检查设备设置。",
             "未允許存取麥克風。請檢查裝置設定。"),
    "6002": ("Your device may be running low on free storage.",
             "设备的可用空间可能不足。",
             "裝置的可用空間可能不足。"),
    "7001": ("The requested data could not be found.",
             "找不到对应的数据。",
             "找不到對應的資料。"),
    "7002": ("There is an error in the input.", "输入内容有误。", "輸入內容有誤。"),
    "7003": ("Failed to update the data.", "更新数据失败。", "更新資料失敗。"),
    "7004": ("It cannot be deleted because it has study records.",
             "由于存在学习记录，无法删除。",
             "由於存在學習記錄，無法刪除。"),
    "7005": ("The selected range has too few words to create a crossword. Please add more fields or word lists.",
             "所选范围内的单词太少，无法制作填字游戏。请增加领域或单词本。",
             "所選範圍內的單字太少，無法製作填字遊戲。請增加領域或單字本。"),
    "7006": ("This sample is for registered users only. Log in (free) and you will be able to play it.",
             "此示例仅限注册用户。登录(免费)后即可游玩。",
             "此範例僅限註冊使用者。登入(免費)後即可遊玩。"),
    "7007": ("To use this feature (creating your own), you need to pay in addition to registering (free), because AI usage fees are actually incurred each time one is created. Guests, please try the sample crosswords.",
             "使用此功能(自己制作)除注册(免费)外还需要付费(因为每次制作都会实际产生AI使用费用)。访客请试玩示例填字游戏。",
             "使用此功能(自己製作)除註冊(免費)外還需要付費(因為每次製作都會實際產生AI使用費用)。訪客請試玩範例填字遊戲。"),
    "7008": ("To use this feature (creating your own), you need to top up. Because AI usage fees are actually incurred each time one is created, it is for users who have topped up. Registered users can try the sample crosswords for free.",
             "使用此功能(自己制作)需要付费。由于每次制作都会实际产生AI使用费用，仅限已充值的用户使用。已注册的用户可以免费试玩示例填字游戏。",
             "使用此功能(自己製作)需要付費。由於每次製作都會實際產生AI使用費用，僅限已儲值的使用者使用。已註冊的使用者可以免費試玩範例填字遊戲。"),
    "7999": ("An unexpected error occurred. Please tell us this code when contacting support.",
             "发生了意外错误。联系支持时请告知此代码。",
             "發生了非預期的錯誤。聯絡支援時請告知此代碼。"),
    "8001": ("Failed to generate the audio.", "生成语音失败。", "產生語音失敗。"),
    "8002": ("Failed to play the audio.", "播放语音失败。", "播放語音失敗。"),
    "8003": ("Recording / speech recognition failed.",
             "录音/语音识别失败。",
             "錄音/語音辨識失敗。"),
    "8004": ("No microphone was found. Please check the connection.",
             "找不到麦克风。请检查连接。",
             "找不到麥克風。請檢查連線。"),
    "9999": ("An unclassified error occurred.",
             "发生了无法分类的错误。",
             "發生了無法分類的錯誤。"),
}

_LANG_INDEX = {"en": 0, "zh-CN": 1, "zh-TW": 2}


def localize_error(code: str, ja_default: str, lang: Optional[str] = None) -> str:
    """エラーコードの既定文言を現在の言語で返す(日本語・未登録コードは
    `ja_default`=errors.ERROR_CODESの日本語)。"""
    lang = lang or current_lang()
    tr_ = ERROR_TRANSLATIONS.get(code)
    if lang == DEFAULT_LANG or tr_ is None:
        return ja_default
    return tr_[_LANG_INDEX[lang]]


# ---------------------------------------------------------------------------
# 個別のメッセージ(呼び出し側が文言を上書きしていたもの・エラーコード以外の
# 利用者向け文言)。キー→{lang: 文言}。{name}形式のプレースホルダーを
# `tr(key, name=...)`で埋める。
# ---------------------------------------------------------------------------
MESSAGES: dict[str, dict[str, str]] = {}


def _m(key: str, ja: str, en: str, zh_cn: str, zh_tw: str) -> None:
    assert key not in MESSAGES, f"重複キー: {key}"
    MESSAGES[key] = {"ja": ja, "en": en, "zh-CN": zh_cn, "zh-TW": zh_tw}


# 日本語の文言→キーの逆引き(下のlocalize_text用)。catalogのimport後に構築する。
_JA_INDEX: dict[str, str] = {}
# errors.ERROR_CODESの日本語既定文→コード(errors.pyがimport時に登録する)。
_JA_TO_CODE: dict[str, str] = {}


def register_error_defaults(error_codes: dict) -> None:
    """errors.ERROR_CODES({code: (日本語, status)})の日本語文を登録する。
    呼び出し側が既定文と同じ文言を明示的に渡していた場合(例: billingの3003)
    も`localize_text`で訳せるようにするため。"""
    for code, (ja, _status) in error_codes.items():
        _JA_TO_CODE.setdefault(ja, code)


def localize_text(ja_text: str) -> str:
    """呼び出し側が日本語の**定型文そのもの**を渡してくるコード(
    `errors.http_error("7001", "単語が見つかりません")`等)向け: 登録済みの
    日本語文と完全一致すれば現在の言語の訳を返し、未登録(管理者向け・
    動的に組み立てた文)はそのまま返す。**訳の抜けはエラーにならず日本語に
    フォールバックする**ので、抜けは`scripts/check_message_i18n.py`が検出する。"""
    if current_lang() == DEFAULT_LANG or not ja_text:
        return ja_text
    key = _JA_INDEX.get(ja_text)
    if key is not None:
        return tr_lang(current_lang(), key)
    code = _JA_TO_CODE.get(ja_text)
    if code is not None:
        return localize_error(code, ja_text)
    return ja_text


def tr(key: str, **params) -> str:
    """現在の言語の文言を返す(無ければ日本語)。未登録キーはKeyError
    (typoを実行時テストで即座に検出するため)。"""
    return tr_lang(current_lang(), key, **params)


def tr_ja(key: str, **params) -> str:
    """日本語の文言(ログ・管理者向け・内部比較用)。"""
    return tr_lang("ja", key, **params)


def tr_lang(lang: str, key: str, **params) -> str:
    entry = MESSAGES[key]
    text = entry.get(lang) or entry["ja"]
    return text.format(**params) if params else text


# ---- catalog は messages_catalog.py に置く(このファイルの肥大化を避ける)
from . import messages_catalog  # noqa: E402,F401  (import時にMESSAGESへ登録)

# 逆引きの構築(ja文が重複するキーは想定しない)。
for _k, _v in MESSAGES.items():
    assert _v["ja"] not in _JA_INDEX, f"日本語文が重複: {_v['ja']}"
    _JA_INDEX[_v["ja"]] = _k
