"""FastAPI application: wires routers, static files, and startup tasks."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

import html as html_lib

from fastapi import FastAPI
from fastapi.responses import (
    FileResponse, HTMLResponse, JSONResponse, PlainTextResponse,
    RedirectResponse,
)
from fastapi.staticfiles import StaticFiles

from .config import load_tokushoho_info, paths
from .database import OWNER_USER_ID, db, init_db
from .routers import (
    auth_routes, billing, categories, decks, fulfillment, inquiries, learn,
    phrase_decks, phrases, system, vocabulary,
)
from .services import auth as auth_svc
from .services.spaced_repetition import apply_weekly_decay

# 認証なしで許可するパス（MULTIUSER=1 のとき）。
# 注: /static 配下は下の判定で別途常に許可される（terms.html もそこに置く）。
_AUTH_ALLOW = {
    "/login", "/api/auth/login", "/api/auth/signup", "/api/health",
    "/favicon.ico", "/tokushoho", "/robots.txt",
}

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
        apply_weekly_decay(conn)
    yield


app = FastAPI(title="English Learning with AI", lifespan=lifespan)


@app.middleware("http")
async def _auth_context(request, call_next):
    """リクエスト毎に「現在のユーザー」を contextvar に設定する（§A）。
    - MULTIUSER=0（既定・ローカル）: 常に owner。認証なしで従来どおり動く。
    - MULTIUSER=1: 署名Cookieから user_id を復元。未ログインなら API は 401、
      ページは /login へリダイレクト（許可パスを除く）。"""
    # 汎用 IP レート制限（既定OFF・公開時に RATE_LIMIT_PER_MIN で有効化）。
    client_ip = request.client.host if request.client else "?"
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
            allowed = (path in _AUTH_ALLOW or path.startswith("/static"))
            if not allowed:
                if path.startswith("/api"):
                    return JSONResponse(
                        {"ok": False, "error": "要ログイン"},
                        status_code=401)
                if path == "/":
                    # 未ログインの初回訪問はログインへ即リダイレクトせず、
                    # まず案内(このアプリについて)を見せる（2026-08-11・
                    # B1着手前の暫定対応）。アクセスをIPで軽く記録する。
                    with db() as conn:
                        conn.execute(
                            "INSERT INTO landing_visits "
                            "(ip, path, user_agent) VALUES (?, ?, ?)",
                            (client_ip, path,
                             request.headers.get("user-agent", "")[:300]),
                        )
                    return RedirectResponse("/static/about.html")
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
        "Allow: /$",
        "Allow: /static/about.html",
        "Allow: /static/terms.html",
        "Allow: /static/privacy.html",
        "Allow: /tokushoho",
        "Allow: /login",
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
