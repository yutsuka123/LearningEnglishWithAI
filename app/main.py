"""FastAPI application: wires routers, static files, and startup tasks."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from .config import paths
from .database import OWNER_USER_ID, db, init_db
from .routers import (
    auth_routes, categories, decks, learn, phrases, system, vocabulary,
)
from .services import auth as auth_svc
from .services.spaced_repetition import apply_weekly_decay

# 認証なしで許可するパス（MULTIUSER=1 のとき）。
_AUTH_ALLOW = {"/login", "/api/auth/login", "/api/health", "/favicon.ico"}


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
            uid = auth_svc.parse_session_token(
                secret, tok, int(time.time()))
        if uid is None:
            path = request.url.path
            allowed = (path in _AUTH_ALLOW or path.startswith("/static"))
            if not allowed:
                if path.startswith("/api"):
                    return JSONResponse(
                        {"ok": False, "error": "要ログイン"},
                        status_code=401)
                return RedirectResponse("/login")
    token = auth_svc.set_current_user_id(
        uid if uid is not None else OWNER_USER_ID)
    try:
        response = await call_next(request)
    finally:
        auth_svc.reset_current_user_id(token)
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
app.include_router(auth_routes.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/login")
def login_page():
    """ログイン画面（MULTIUSER=1 用）。単一ユーザー時は使われない。"""
    return FileResponse(str(paths.static_dir / "login.html"))


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
