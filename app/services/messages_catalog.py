"""利用者向けメッセージの翻訳カタログ(2026-09-26・仕組みは`messages.py`参照)。

`_m(キー, ja, en, zh-CN, zh-TW)`の並び。`{name}`は`tr(key, name=...)`で埋める
プレースホルダー(リテラルの波括弧は使わない)。日本語(ja)は**元の文言を一字一句
そのまま**にする(`localize_text()`が日本語の定型文からの逆引きに使うため)。
管理者向け・運用者向けの文言はここに載せない(日本語のまま)。
"""

from .messages import _m

# ---------------------------------------------------------------------------
# 共通・見つからない系
# ---------------------------------------------------------------------------
_m("rate.too_many",
   "リクエストが多すぎます。少し待ってください。",
   "Too many requests. Please wait a moment.",
   "请求过多。请稍等片刻。",
   "請求過多。請稍等片刻。")
_m("nf.category", "カテゴリが見つかりません",
   "Category not found", "找不到该类别", "找不到該類別")
_m("nf.topic", "トピックが見つかりません",
   "Topic not found", "找不到该主题", "找不到該主題")
_m("nf.deck", "単語帳が見つかりません",
   "Word list not found", "找不到该单词本", "找不到該單字本")
_m("nf.deck_p", "単語帳が見つかりません。",
   "Word list not found.", "找不到该单词本。", "找不到該單字本。")
_m("nf.phrase_deck", "フレーズ帳が見つかりません",
   "Phrase list not found", "找不到该短语本", "找不到該短語本")
_m("nf.word", "単語が見つかりません",
   "Word not found", "找不到该单词", "找不到該單字")
_m("nf.phrase", "フレーズが見つかりません",
   "Phrase not found", "找不到该短语", "找不到該短語")
_m("nf.material", "教材が見つかりません",
   "Material not found", "找不到该教材", "找不到該教材")
_m("nf.payment", "対象の支払いが見つかりません。",
   "The payment could not be found.", "找不到对应的付款。", "找不到對應的付款。")
_m("nf.generic_p", "見つかりません。",
   "Not found.", "找不到。", "找不到。")

# ---------------------------------------------------------------------------
# 認証・アカウント
# ---------------------------------------------------------------------------
_m("auth.signup_closed",
   "現在は試験公開中のため、新規登録の受付を停止しています。正式公開は2026年9月中を予定しております。既にIDをお持ちの方はログインしてください。",
   "New registrations are currently paused because the service is in a trial release. The official launch is planned for September 2026. If you already have an ID, please log in.",
   "目前处于试运行阶段，暂停接受新用户注册。预计2026年9月内正式公开。已有ID的用户请直接登录。",
   "目前處於試營運階段，暫停接受新使用者註冊。預計2026年9月內正式公開。已有ID的使用者請直接登入。")
_m("auth.pw_length",
   "パスワードは8文字以上32文字以下にしてください。",
   "The password must be between 8 and 32 characters long.",
   "密码长度须为8个字符以上、32个字符以下。",
   "密碼長度須為8個字元以上、32個字元以下。")
_m("auth.pw_chars",
   "パスワードに使用できない文字が含まれています（半角の英字・数字・記号のみ使用できます）。",
   "The password contains characters that cannot be used (only half-width letters, digits and symbols are allowed).",
   "密码中包含无法使用的字符（只能使用半角的字母、数字和符号）。",
   "密碼中包含無法使用的字元（只能使用半形的字母、數字和符號）。")
_m("auth.pw_kinds",
   "パスワードは英字・数字・記号のうち2種類以上を組み合わせてください。",
   "The password must combine at least two of letters, digits and symbols.",
   "密码须组合使用字母、数字、符号中的至少2种。",
   "密碼須組合使用字母、數字、符號中的至少2種。")
_m("auth.withdraw_need_reason",
   "退会理由を1つ以上選択するか、自由記入欄にご記入ください。",
   "Please select at least one reason for leaving or write in the free-text field.",
   "请至少选择一个退出原因，或在自由填写栏中填写。",
   "請至少選擇一個退出原因，或在自由填寫欄中填寫。")
_m("auth.withdraw_admin",
   "管理者アカウントはこの画面から退会できません。お問い合わせからご連絡ください。",
   "Administrator accounts cannot be closed from this screen. Please contact us via the inquiry form.",
   "管理员账号无法通过此页面退出。请通过咨询表单与我们联系。",
   "管理員帳號無法透過此頁面退出。請透過諮詢表單與我們聯繫。")
_m("inquiry.need_body",
   "内容を入力してください。",
   "Please enter the content.",
   "请输入内容。",
   "請輸入內容。")
_m("inquiry.bad_email",
   "メールアドレス（返信先）を正しく入力してください。",
   "Please enter a valid email address (for our reply).",
   "请正确输入邮箱地址(用于回复)。",
   "請正確輸入電子郵件地址(用於回覆)。")

# ---------------------------------------------------------------------------
# チャージキー・決済
# ---------------------------------------------------------------------------
_m("key.invalid",
   "キーが無効です。入力内容をご確認ください。",
   "The key is invalid. Please check what you entered.",
   "密钥无效。请确认输入的内容。",
   "金鑰無效。請確認輸入的內容。")
_m("key.used",
   "このキーは使用済みです。すでにチャージ済みの可能性があります。",
   "This key has already been used. It may already have been credited to your balance.",
   "该密钥已被使用。可能已经充值完成。",
   "此金鑰已被使用。可能已經儲值完成。")
_m("key.bad_format",
   "キーの形式が正しくありません。",
   "The key format is incorrect.",
   "密钥格式不正确。",
   "金鑰格式不正確。")
_m("key.bad_check",
   "キーが正しくありません（入力ミスの可能性）。",
   "The key is not correct (you may have made a typing mistake).",
   "密钥不正确（可能是输入有误）。",
   "金鑰不正確（可能是輸入有誤）。")
_m("pay.amount_choices",
   "金額は{amounts}のいずれかにしてください。",
   "The amount must be one of {amounts}.",
   "金额必须是{amounts}中的一个。",
   "金額必須是{amounts}其中之一。")
_m("pay.no_url",
   "PayPayからurlが返りませんでした: {detail}",
   "PayPay did not return a URL: {detail}",
   "PayPay没有返回网址: {detail}",
   "PayPay沒有回傳網址: {detail}")
_m("deck.free_limit",
   "無料範囲では単語帳は{n}個までです。追加で作るには設定画面からチャージしてください。",
   "In the free range you can have up to {n} word list(s). To create more, please top up from the Settings screen.",
   "免费范围内单词本最多{n}个。如需创建更多，请在设置页面充值。",
   "免費範圍內單字本最多{n}個。如需建立更多，請在設定頁面儲值。")
_m("phrasedeck.free_limit",
   "無料範囲ではフレーズ帳は{n}個までです。追加で作るには設定画面からチャージしてください。",
   "In the free range you can have up to {n} phrase list(s). To create more, please top up from the Settings screen.",
   "免费范围内短语本最多{n}个。如需创建更多，请在设置页面充值。",
   "免費範圍內短語本最多{n}個。如需建立更多，請在設定頁面儲值。")

# ---------------------------------------------------------------------------
# AI(ai.py)
# ---------------------------------------------------------------------------
_m("ai.no_key",
   "OPENAI_API_KEY が未設定です。",
   "OPENAI_API_KEY is not set.",
   "尚未设置 OPENAI_API_KEY。",
   "尚未設定 OPENAI_API_KEY。")
_m("ai.no_key_settings",
   "OPENAI_API_KEY が未設定です。設定で登録してください。",
   "OPENAI_API_KEY is not set. Please register it in Settings.",
   "尚未设置 OPENAI_API_KEY。请在设置中登记。",
   "尚未設定 OPENAI_API_KEY。請在設定中登錄。")
_m("ai.no_key_manual",
   "OPENAI_API_KEY が未設定です。手動入力で保存できます。",
   "OPENAI_API_KEY is not set. You can still save by entering it manually.",
   "尚未设置 OPENAI_API_KEY。可以手动输入后保存。",
   "尚未設定 OPENAI_API_KEY。可以手動輸入後儲存。")
_m("ai.client_init_failed",
   "OpenAI クライアントを初期化できませんでした。",
   "The OpenAI client could not be initialized.",
   "无法初始化 OpenAI 客户端。",
   "無法初始化 OpenAI 用戶端。")
_m("ai.free_quota",
   "{period}の無料利用枠の上限に達しました。設定画面でチャージキーを登録すると、残高で引き続きご利用いただけます。",
   "You have reached the free usage limit for {period}. If you register a charge key in Settings, you can keep using it with your balance.",
   "已达到{period}的免费使用额度上限。在设置页面登记充值密钥后，即可继续使用余额。",
   "已達到{period}的免費使用額度上限。在設定頁面登錄儲值金鑰後，即可繼續使用餘額。")
_m("ai.period_today", "本日", "today", "今日", "今日")
_m("ai.period_month", "今月", "this month", "本月", "本月")
_m("ai.site_cap",
   "本日のAI利用がサイト全体の上限に達しました。時間をおいて再試行してください。",
   "Today's AI usage for the whole site has reached its limit. Please try again later.",
   "今日全站的AI使用量已达到上限。请稍后再试。",
   "今日全站的AI使用量已達到上限。請稍後再試。")
_m("ai.rate_limit",
   "AI呼び出しが短時間に集中しています（上限 {n}回/分）。少し待ってから再試行してください。",
   "AI calls are concentrated in a short time (limit: {n} per minute). Please wait a moment and try again.",
   "短时间内AI调用过于集中（上限 {n}次/分钟）。请稍候再试。",
   "短時間內AI呼叫過於集中（上限 {n}次/分鐘）。請稍候再試。")
_m("ai.stream_error",
   "通信エラーが発生しました。もう一度お試しください。",
   "A communication error occurred. Please try again.",
   "发生通信错误。请重试。",
   "發生通訊錯誤。請再試一次。")
_m("ai.stt_failed",
   "文字起こしに失敗しました: {detail}",
   "Transcription failed: {detail}",
   "语音转文字失败: {detail}",
   "語音轉文字失敗: {detail}")
_m("ai.tts_login",
   "この単語・フレーズの音声はログインすると聴けます（無料の会員登録のみで再生できる範囲が広がります）。",
   "You can listen to the audio for this word/phrase once you log in (free registration alone widens the range you can play).",
   "登录后即可收听此单词/短语的语音（仅需免费注册，即可扩大可播放的范围）。",
   "登入後即可收聽此單字/短語的語音（僅需免費註冊，即可擴大可播放的範圍）。")
_m("ai.tts_outside_free",
   "この単語・フレーズの音声は無料の範囲外です。ログイン（無料の会員登録）だけでは聴けず、少額のチャージが必要になります。",
   "The audio for this word/phrase is outside the free range. Logging in (free registration) alone is not enough; a small top-up is needed.",
   "此单词/短语的语音不在免费范围内。仅登录（免费注册）无法收听，需要充值少量金额。",
   "此單字/短語的語音不在免費範圍內。僅登入（免費註冊）無法收聽，需要儲值少量金額。")
_m("ai.tts_need_credit",
   "この単語・フレーズの再生には少額のチャージ消費が必要です（必要額: 約¥{need}・残高: ¥{balance}）。設定画面からチャージしてください。",
   "Playing this word/phrase uses a small amount of your top-up balance (required: about ¥{need}, balance: ¥{balance}). Please top up from the Settings screen.",
   "播放此单词/短语需要消耗少量充值余额（所需金额: 约¥{need}・余额: ¥{balance}）。请在设置页面充值。",
   "播放此單字/短語需要消耗少量儲值餘額（所需金額: 約¥{need}・餘額: ¥{balance}）。請在設定頁面儲值。")

# ---------------------------------------------------------------------------
# 学習(learn.py / vocabulary.py / phrases.py)
# ---------------------------------------------------------------------------
_m("learn.parse_failed",
   "生成結果を解釈できませんでした。",
   "The generated result could not be interpreted.",
   "无法解析生成的结果。",
   "無法解析產生的結果。")
_m("learn.no_study_data",
   "まだ学習データがありません。クイズや会話をしてください。",
   "There is no study data yet. Please try a quiz or a conversation first.",
   "还没有学习数据。请先做测验或进行对话。",
   "還沒有學習資料。請先做測驗或進行對話。")
_m("learn.no_advice_input",
   "アドバイスを作れない入力です。",
   "This input cannot be turned into advice.",
   "这个输入无法生成建议。",
   "這個輸入無法產生建議。")
_m("learn.detail_login",
   "詳細の生成はログインすると利用できます。",
   "Generating details is available after you log in.",
   "登录后即可使用详情生成功能。",
   "登入後即可使用詳細內容產生功能。")
_m("learn.detail_failed",
   "詳細の生成に失敗しました。",
   "Failed to generate the details.",
   "生成详情失败。",
   "產生詳細內容失敗。")
_m("learn.daily_words", "英単語テスト", "English word test", "英语单词测试", "英語單字測驗")
_m("learn.daily_phrases", "ミニフレーズ", "Mini phrases", "迷你短语", "迷你短語")
_m("learn.daily_reading", "リーディング (1題)", "Reading (1 item)", "阅读（1题）", "閱讀（1題）")
_m("learn.daily_writing",
   "ライティング (1題・音声応答可)",
   "Writing (1 item, voice answers allowed)",
   "写作（1题・可语音作答）",
   "寫作（1題・可語音作答）")

# ---------------------------------------------------------------------------
# ゲーム(クロスワード・games.py)
# ---------------------------------------------------------------------------
_m("games.pick_deck", "単語帳を選んでください。",
   "Please choose a word list.", "请选择单词本。", "請選擇單字本。")
_m("games.few_words",
   "選んだ範囲に単語が{n}語未満しかありません。分野を増やす・単語帳を変える、またはレベル範囲を広げてください。",
   "The selected range has fewer than {n} words. Please add more fields, choose a different word list, or widen the level range.",
   "所选范围内的单词不足{n}个。请增加领域、更换单词本，或扩大等级范围。",
   "所選範圍內的單字不足{n}個。請增加領域、更換單字本，或擴大等級範圍。")
_m("games.cannot_make",
   "この単語の組み合わせではクロスワードを作れませんでした。語数を増やす(候補が増えて交差しやすくなります)・分野を増やす、またはレベル範囲を広げてみてください。",
   "A crossword could not be made from this combination of words. Try increasing the number of words (more candidates make crossings easier), adding more fields, or widening the level range.",
   "无法用这个单词组合制作填字游戏。请尝试增加单词数(候选变多后更容易交叉)、增加领域，或扩大等级范围。",
   "無法用這個單字組合製作填字遊戲。請嘗試增加單字數(候選變多後更容易交叉)、增加領域，或擴大等級範圍。")
_m("games.notice_fewer",
   "{want}語を希望しましたが、単語同士がうまく交差できず{placed}語だけ配置しました。分野を複数選ぶ・単語帳を変える、または語数を減らすと、希望語数に近づきやすくなります。",
   "You asked for {want} words, but the words did not cross well and only {placed} were placed. Choosing several fields, switching word lists, or reducing the word count makes it easier to get close to the number you want.",
   "您希望{want}个单词，但单词之间没能很好地交叉，只布置了{placed}个。选择多个领域、更换单词本或减少单词数，会更容易接近希望的单词数。",
   "您希望{want}個單字，但單字之間沒能很好地交叉，只佈置了{placed}個。選擇多個領域、更換單字本或減少單字數，會更容易接近希望的單字數。")
_m("games.pin_sample_login",
   "サンプルクロスワードの保存にはログイン(無料の会員登録)が必要です。",
   "Logging in (free registration) is required to save a sample crossword.",
   "保存示例填字游戏需要登录(免费注册)。",
   "儲存範例填字遊戲需要登入(免費註冊)。")
_m("games.pin_charged_only",
   "クロスワードの保存(ピン留め)は課金ユーザー限定です。設定画面からチャージすると使えるようになります。",
   "Saving (pinning) crosswords is for users who have topped up. You can use it after topping up from the Settings screen.",
   "保存(置顶)填字游戏仅限已充值的用户。在设置页面充值后即可使用。",
   "儲存(置頂)填字遊戲僅限已儲值的使用者。在設定頁面儲值後即可使用。")
_m("games.pin_cap",
   "保存できるのは{cap}件までです。他の保存を解除してからお試しください。",
   "You can save up to {cap}. Please remove another saved item first and try again.",
   "最多只能保存{cap}个。请先取消其他已保存的项目再试。",
   "最多只能儲存{cap}個。請先取消其他已儲存的項目再試。")
_m("games.hint_already",
   "このモードでは既に表示されているヒントです。",
   "This hint is already shown in this mode.",
   "此提示在当前模式下已经显示。",
   "此提示在目前模式下已經顯示。")
_m("games.no_clue", "存在しないクリューです。",
   "That clue does not exist.", "该提示题不存在。", "該提示題不存在。")
_m("games.no_example", "この語には例文がありません。",
   "This word has no example sentence.", "该单词没有例句。", "該單字沒有例句。")
_m("games.sample_limit_guest",
   "ゲストで試せるサンプルは{limit}個までです。ログイン(無料)すると{free_limit}個まで遊べるようになります。",
   "Guests can try up to {limit} samples. Log in (free) and you can play up to {free_limit}.",
   "访客最多可试玩{limit}个示例。登录(免费)后最多可游玩{free_limit}个。",
   "訪客最多可試玩{limit}個範例。登入(免費)後最多可遊玩{free_limit}個。")
_m("games.sample_limit_free",
   "無料で遊べるサンプルは{limit}個までです。チャージすると無制限に遊べるようになります。",
   "You can play up to {limit} samples for free. Top up and you can play without limit.",
   "免费最多可游玩{limit}个示例。充值后即可无限游玩。",
   "免費最多可遊玩{limit}個範例。儲值後即可無限遊玩。")
_m("games.source_all", "すべて", "All", "全部", "全部")
_m("games.source_cat_all", "{category}(全分野)",
   "{category} (all fields)", "{category}(全部领域)", "{category}(全部領域)")
_m("games.rank_anon", "{first}さん", "Player {first}", "玩家{first}", "玩家{first}")
_m("auth.not_logged_in", "未ログイン",
   "Not logged in", "未登录", "未登入")
