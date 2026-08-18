"""FastAPI application: wires routers, static files, and startup tasks."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

import html as html_lib

from fastapi import FastAPI
from fastapi import Response
from fastapi.responses import (
    FileResponse, HTMLResponse, JSONResponse, PlainTextResponse,
    RedirectResponse,
)
from fastapi.staticfiles import StaticFiles

from .config import load_tokushoho_info, log, paths
from .database import OWNER_USER_ID, db, init_db
from .routers import (
    auth_routes, base_oauth, billing, categories, decks, fulfillment,
    inquiries, learn, phrase_decks, phrases, system, vocabulary,
)
from .services import auth as auth_svc
from .services.spaced_repetition import apply_forgetting_decay

# 認証なしで許可するパス（MULTIUSER=1 のとき）。
# 注: /static 配下は下の判定で別途常に許可される（terms.html もそこに置く）。
_AUTH_ALLOW = {
    "/login", "/api/auth/login", "/api/auth/signup", "/api/health",
    "/favicon.ico", "/tokushoho", "/robots.txt", "/api/system/taxonomy",
    "/sitemap.xml", "/llms.txt",
}

# ①(未ログイン/ゲスト)でも読める(=①向け無料範囲で動く)APIのパス接頭辞
# （2026-08-11・B1本実装）。単語/フレーズカタログの閲覧・詳細・音声
# （範囲内のみ）・出題(フラッシュ/クイズ)が対象。
#
# 注意(2026-08-11・実装時に発見した罠): prefixマッチなので、ここに
# 追加した接頭辞の**配下にある全エンドポイント**がゲストに開く。
# /api/words, /api/phrases 配下は棚卸し済み(create/update/delete/tags書換
# はadmin専用チェックで保護、/detail は未生成時のAI生成のみゲスト拒否、
# /retag は本来admin専用のはずがチェック漏れだったため追加保護した)。
# /api/learn は棚卸ししておらず(会話・作文添削等コストの高いAI機能を含む)
# 丸ごとは絶対に入れない — 音声再生の /tts/item だけをフルパスで個別指定
# する。新しい接頭辞を足すときは配下の全エンドポイントを必ず確認すること。
_GUEST_READ_PREFIXES = (
    "/api/words", "/api/phrases", "/api/system/my-usage",
    "/api/learn/tts/item", "/api/learn/samples",
    # 2026-08-13: reading/listening/writing/英会話タブのサンプル閲覧を
    # サイドバーから直接できるようにするため追加。カテゴリ/トピック自体は
    # 全ユーザー共有のマスタデータで、進捗だけがuser_id別
    # (categories.py参照)。/study への書き込みもゲスト疑似ユーザー自身の
    # 進捗を書くだけで既存のクイズ/デッキ同様に無害（訪問のたびリセット
    # される想定は既存の案内文の通り）。
    "/api/categories", "/api/listening", "/api/system/progress",
    # 2026-08-17: 画面表示/ボタン押下の利用状況イベント記録
    # (usage_events)。ゲストの行動も分析対象にするため読み取り専用
    # プレフィックス扱いに加える(実際はPOSTだが、admin専用の集計取得
    # ではなく誰でも書ける前提のログ用エンドポイントのため問題ない)。
    "/api/system/track",
)

# 特定商取引法ページ: 未記入欄のフォールバック文言(赤字表示)。
_TOKUSHOHO_PLACEHOLDERS = {
    "name": "[要記入: 個人事業主の氏名（本名・フルネーム）]",
    "supervisor": "[要記入: 上記と同一の場合は「同上」]",
    "address": (
        "[要記入: 住所。特定商取引法の2022年改正により、個人事業主は"
        "「請求があれば遅滞なく開示します」という表記で住所公開を省略"
        "できる場合があります（詳細は利用する決済窓口のガイドラインで"
        "確認）。]"
    ),
    "phone": (
        "[要記入: 電話番号。上記と同様、「請求があれば遅滞なく開示"
        "します」で省略できる場合があります。]"
    ),
    "email": "[要記入: 問い合わせ用メールアドレス]",
}
_TOKUSHOHO_DRAFT_BANNER = (
    '<div class="draft">⚠️ <strong>このページは作成中のたたき台です。</strong>'
    ' <span class="todo">赤字</span>の項目は事業者本人が.envで確認・記入する'
    "必要があります（正式公開前に必ず埋めてください）。</div>"
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialise DB + seed data, then apply the weekly forgetting decay.
    init_db()
    with db() as conn:
        apply_forgetting_decay(conn)
    yield


app = FastAPI(title="English Learning with AI", lifespan=lifespan)


@app.middleware("http")
async def _auth_context(request, call_next):
    """リクエスト毎に「現在のユーザー」を contextvar に設定する（§A）。
    - MULTIUSER=0（既定・ローカル）: 常に owner。認証なしで従来どおり動く。
    - MULTIUSER=1: 署名Cookieから user_id を復元。未ログインなら API は 401、
      ページは /login へリダイレクト（許可パスを除く）。"""
    # 汎用 IP レート制限（既定OFF・公開時に RATE_LIMIT_PER_MIN で有効化）。
    # real_client_ip: Caddy経由でも実クライアントIPを取る（§auth.py参照）。
    client_ip = auth_svc.real_client_ip(request)
    if auth_svc.ip_rate_limited(client_ip):
        return JSONResponse(
            {"ok": False, "error": "リクエストが多すぎます。少し待って"
             "ください。"}, status_code=429)
    multiuser = auth_svc.multiuser_enabled()
    uid = OWNER_USER_ID
    if multiuser:
        uid = None
        tok = request.cookies.get(auth_svc.SESSION_COOKIE)
        if tok:
            with db() as conn:
                secret = auth_svc.get_session_secret(conn)
                parsed = auth_svc.parse_session_token(
                    secret, tok, int(time.time()))
                if parsed is not None:
                    p_uid, p_epoch = parsed
                    # §B4: DB側のsession_epochと食い違えば無効化された
                    # セッション（強制ログアウト済み）として扱う。
                    if auth_svc.get_session_epoch(conn, p_uid) == p_epoch:
                        uid = p_uid
        if uid is None:
            path = request.url.path
            if path == "/":
                # 未ログインの訪問をIPで軽く記録する（2026-08-11・B1本
                # 実装。ログ書き込み失敗はトップページ表示自体を妨げない
                # よう握りつぶす。DBロック等の一過性エラー想定）。
                try:
                    with db() as conn:
                        conn.execute(
                            "INSERT INTO landing_visits "
                            "(ip, path, user_agent) VALUES (?, ?, ?)",
                            (client_ip, path,
                             request.headers.get("user-agent", "")[:300]),
                        )
                except Exception:
                    log.warning("landing_visits記録に失敗", exc_info=True)
            allowed = (
                path in _AUTH_ALLOW or path.startswith("/static")
                or path == "/"
            )
            guest_readable = any(
                path.startswith(p) for p in _GUEST_READ_PREFIXES)
            if guest_readable:
                # ①(未ログイン/ゲスト)向けに疑似ユーザーを割り当てる
                # （書き込み系・管理者専用操作は各エンドポイント内部の
                # チェックでそのまま拒否される・多重防御）。
                with db() as conn:
                    uid = auth_svc.ensure_guest_user_id(conn)
            elif not allowed:
                if path.startswith("/api"):
                    return JSONResponse(
                        {"ok": False, "error": "要ログイン"},
                        status_code=401)
                return RedirectResponse("/login")
    token = auth_svc.set_current_user_id(
        uid if uid is not None else OWNER_USER_ID)
    ip_token = auth_svc.set_current_ip(client_ip)
    web_token = auth_svc.mark_web_request()
    try:
        response = await call_next(request)
    finally:
        auth_svc.reset_current_user_id(token)
        auth_svc.reset_current_ip(ip_token)
        auth_svc.reset_web_request(web_token)
    path = request.url.path
    if path == "/" or path.startswith("/static"):
        response.headers["Cache-Control"] = "no-cache, must-revalidate"
    return response


# API routers
app.include_router(vocabulary.router)
app.include_router(phrases.router)
app.include_router(categories.router)
app.include_router(categories.listening)
app.include_router(learn.router)
app.include_router(system.router)
app.include_router(decks.router)
app.include_router(phrase_decks.router)
app.include_router(auth_routes.router)
app.include_router(billing.router)
app.include_router(inquiries.router)
app.include_router(fulfillment.router)
app.include_router(base_oauth.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/robots.txt")
def robots_txt():
    """クロール範囲を公開ページのみに明示的に絞る（2026-08-11・機密情報
    や内部画面が誤って索引されないようにするため）。それ以外の経路は
    ログイン必須(middlewareが/loginへ誘導)なので実害は薄いが、念のため
    クローラーに対しても明示しておく。"""
    lines = [
        "User-agent: *",
        "Disallow: /api/",
        "Disallow: /admin",
        "Disallow: /static/js/",
        "Disallow: /static/css/",
        "Disallow: /static/index.html",
        "Allow: /$",
        "Allow: /static/about.html",
        "Allow: /static/terms.html",
        "Allow: /static/privacy.html",
        "Allow: /tokushoho",
        "Allow: /login",
        "Sitemap: https://study.nyangailab.com/sitemap.xml",
    ]
    return PlainTextResponse("\n".join(lines) + "\n")


@app.get("/sitemap.xml")
def sitemap_xml():
    """検索エンジン向けのサイトマップ(2026-08-13)。robots.txtでAllowして
    いる公開ページのみ列挙する（ログイン必須ページ・APIは含めない）。"""
    pages = [
        ("https://study.nyangailab.com/", "1.0"),
        ("https://study.nyangailab.com/static/about.html", "0.9"),
        ("https://study.nyangailab.com/login", "0.5"),
        ("https://study.nyangailab.com/static/terms.html", "0.3"),
        ("https://study.nyangailab.com/static/privacy.html", "0.3"),
        ("https://study.nyangailab.com/tokushoho", "0.3"),
    ]
    urls = "".join(
        f"<url><loc>{loc}</loc><priority>{pri}</priority></url>"
        for loc, pri in pages
    )
    xml = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{urls}</urlset>"
    )
    return Response(content=xml, media_type="application/xml")


@app.get("/llms.txt")
def llms_txt():
    """生成AI(ChatGPT/Claude/Perplexity等)のクローラー・検索が本サービスを
    正しく要約・引用できるようにするための説明ファイル(2026-08-13、
    llmstxt.org提案の慣習に準拠)。robots.txtで許可している公開情報のみを
    書く(非公開のdocs/事業計画等は含めない)。"""
    lines = [
        "# nyangailab（にゃんがいらぼ）",
        "",
        "> 月額サブスクなしで使えるAI英語学習アプリ。サブスク疲れの人が"
        "前払い制で使った分だけ払う、廉価な英語学習アプリを目指しています。"
        "専門用語やマイナーな英単語まで学べるマニアックな語彙が特徴です。",
        "",
        "nyangailabは、月額サブスクリプション制ではなく使った分だけ払う"
        "都度課金制（前払いチャージ方式）のAI英語学習アプリです。ログイン"
        "不要・無料で英単語/フレーズの閲覧、発音のAI音声再生（無料範囲"
        "あり）、リーディング/リスニング/英会話/ライティングのサンプル"
        "教材を利用できます。日常会話の基礎語彙からTOEIC対策、資格・"
        "専門用語、さらには妖怪や絶滅種のようなニッチ・マニアックな分野"
        "まで幅広く扱います。AIを活用することで教材制作・運用コストを"
        "抑え、廉価な価格設定を実現しています。",
        "",
        "## こんな人におすすめ (Target audience)",
        "",
        "- 英語学習アプリのサブスクに疲れた人（サブスク疲れ・使わない月"
        "も課金される不満がある人）",
        "- 月額固定費を払いたくない人（前払いチャージ・都度課金を探して"
        "いる人）",
        "- 安い・廉価な英語学習アプリを探している人",
        "- 一般的な英会話アプリでは扱わない専門用語・マイナーな英単語・"
        "マニアックな分野の語彙を学びたい人",
        "- まず無料で試してから使うか判断したい人（無料体験・ログイン"
        "不要のお試し範囲あり）",
        "",
        "## FAQ",
        "",
        "Q. 月額サブスクリプションですか？",
        "A. いいえ。サブスクなしの都度課金制（前払いチャージ）です。"
        "使った分だけ残高から消費されます。",
        "",
        "Q. 無料で使えますか？",
        "A. はい。単語・フレーズの閲覧、フラッシュカード、一部の音声"
        "再生、リーディング/リスニング/英会話/ライティングのサンプル"
        "教材はログイン不要・無料で利用できます。",
        "",
        "Q. なぜ安いのですか？",
        "A. AIを活用して教材制作・運用コストを抑えているため、廉価な"
        "価格設定を実現しています。",
        "",
        "Q. 専門用語やマイナーな英語も学べますか？",
        "A. はい。日常会話やTOEIC対策の基礎語彙に加え、専門用語、妖怪"
        "や絶滅種などニッチ・マニアックな分野の単語・フレーズも扱って"
        "います。",
        "",
        "現在は無料試験公開中で、新規登録も受付中です"
        "（メールアドレスとパスワードで自己登録できます）。正式公開は"
        "2026年9月中を予定しています。",
        "",
        "## Pages",
        "",
        "- [トップページ](https://study.nyangailab.com/): "
        "サービス概要・アプリ本体（ログイン不要の範囲あり）",
        "- [このアプリについて](https://study.nyangailab.com/static/about.html): "
        "料金モデル・無料/課金の利用範囲・使い方ガイド",
        "- [ログイン](https://study.nyangailab.com/login): "
        "既存ユーザー向け（新規登録は現在停止中）",
        "- [利用規約](https://study.nyangailab.com/static/terms.html)",
        "- [プライバシーポリシー](https://study.nyangailab.com/static/privacy.html)",
        "- [特定商取引法に基づく表記](https://study.nyangailab.com/tokushoho): "
        "料金の目安",
        "- [nyangailab BASEショップ](https://nyangailab.base.shop/): "
        "前払いチャージ用のポイント購入窓口（決済専用・アプリ本体は"
        "study.nyangailab.comで稼働）",
    ]
    return PlainTextResponse("\n".join(lines) + "\n")


@app.get("/login")
def login_page():
    """ログイン画面（MULTIUSER=1 用）。単一ユーザー時は使われない。"""
    return FileResponse(str(paths.static_dir / "login.html"))


@app.get("/tokushoho")
def tokushoho_page():
    """特定商取引法に基づく表記。個人情報は .env(TOKUSHOHO_*)から読み込み、
    未記入の項目だけ赤字の案内文にフォールバックする（本文には一切書かない・
    コミットされない）。全項目が埋まると作成中バナーも自動で消える。"""
    info = load_tokushoho_info()
    page = (paths.root / "templates" / "tokushoho.html").read_text(
        encoding="utf-8")
    for key, value in info.items():
        if value:
            cell = f"<td>{html_lib.escape(value)}</td>"
        else:
            cell = (
                f'<td class="todo">'
                f"{html_lib.escape(_TOKUSHOHO_PLACEHOLDERS[key])}</td>"
            )
        page = page.replace("{{" + key.upper() + "_CELL}}", cell)
    banner = "" if all(info.values()) else _TOKUSHOHO_DRAFT_BANNER
    page = page.replace("{{DRAFT_BANNER}}", banner)
    return HTMLResponse(page)


@app.get("/admin/fulfillment")
def admin_fulfillment_page():
    """フルフィルメント管理画面（管理者専用）。未ログインは middleware が
    /login へ誘導。ログイン済みでも role=admin でなければ弾く。"""
    with db() as conn:
        me = auth_svc.get_user(conn, auth_svc.current_user_id())
    if not me or me.get("role") != "admin":
        return RedirectResponse("/login")
    return FileResponse(
        str(paths.root / "templates" / "admin_fulfillment.html"))


# Serve the SPA. Static assets under /static, index.html at root.
paths.static_dir.mkdir(parents=True, exist_ok=True)
app.mount(
    "/static",
    StaticFiles(directory=str(paths.static_dir)),
    name="static",
)


@app.get("/")
def index():
    return FileResponse(str(paths.static_dir / "index.html"))
