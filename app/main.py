"""FastAPI application: wires routers, static files, and startup tasks."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .config import paths
from .database import db, init_db
from .routers import categories, learn, phrases, system, vocabulary
from .services.spaced_repetition import apply_monthly_decay


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialise DB + seed data, then apply the monthly forgetting decay.
    init_db()
    with db() as conn:
        apply_monthly_decay(conn)
    yield


app = FastAPI(title="English Learning with AI", lifespan=lifespan)

# API routers
app.include_router(vocabulary.router)
app.include_router(phrases.router)
app.include_router(categories.router)
app.include_router(categories.listening)
app.include_router(learn.router)
app.include_router(system.router)


@app.get("/api/health")
def health():
    return {"status": "ok"}


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
