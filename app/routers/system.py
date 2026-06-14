"""System endpoints: settings, usage/cost, memory.md & study_log.md."""

from __future__ import annotations

from fastapi import APIRouter

from ..config import ROOT_DIR, load_settings
from ..database import ACCENTS, NEWS_FIELDS
from ..schemas import MemoryUpdateIn, SettingsIn
from ..services import ai, persistence

router = APIRouter(prefix="/api/system", tags=["system"])


@router.get("/taxonomy")
def taxonomy():
    """Selectable lists for UI dropdowns (news fields, accents, models)."""
    from ..services.ai import PRICING, TTS_VOICES

    return {
        "news_fields": NEWS_FIELDS,
        "accents": ACCENTS,
        "models": list(PRICING.keys()),
        "tts_voices": TTS_VOICES,
    }


@router.get("/settings")
def get_settings():
    s = load_settings()
    key = s.openai_api_key
    if len(key) > 8:
        masked = key[:4] + "…" + key[-2:]
    else:
        masked = "設定済み" if key else ""
    return {
        "ai_enabled": s.ai_enabled,
        "model": s.openai_model,
        "quality_model": s.quality_model,
        "api_key_masked": masked,
        "host": s.host,
        "port": s.port,
    }


def _write_env(updates: dict[str, str]) -> None:
    """Persist key/values to the project .env file (create/merge)."""
    env_path = ROOT_DIR / ".env"
    existing: dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.strip().startswith("#"):
                k, _, v = line.partition("=")
                existing[k.strip()] = v
    existing.update(updates)
    lines = [f"{k}={v}" for k, v in existing.items()]
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


@router.put("/settings")
def update_settings(payload: SettingsIn):
    updates: dict[str, str] = {}
    if payload.openai_api_key is not None and payload.openai_api_key.strip():
        updates["OPENAI_API_KEY"] = payload.openai_api_key.strip()
    if payload.openai_model is not None and payload.openai_model.strip():
        updates["OPENAI_MODEL"] = payload.openai_model.strip()
    if payload.openai_quality_model is not None:
        updates["OPENAI_QUALITY_MODEL"] = payload.openai_quality_model.strip()
    if updates:
        _write_env(updates)
    # Re-read so the response reflects the new state immediately.
    return get_settings()


@router.get("/usage")
def usage():
    return ai.usage_summary()


@router.get("/progress")
def progress():
    """項目別の習熟度サマリ + TOEIC換算(目安)。"""
    from ..database import db
    from ..services.metrics import toeic_estimate, word_buckets

    with db() as conn:
        words = word_buckets(conn, "words")
        phrases = word_buckets(conn, "phrases")
        # 会話/読/書/文学: エリア別の平均習熟度。
        area_rows = conn.execute(
            "SELECT area, COUNT(*) AS n, COALESCE(AVG(mastery),0) AS avg "
            "FROM categories GROUP BY area"
        ).fetchall()
        listening = conn.execute(
            "SELECT COALESCE(AVG(comprehension),0) AS avg, COUNT(*) AS n "
            "FROM listening_topics"
        ).fetchone()

    areas = {
        r["area"]: {"count": r["n"], "avg_mastery": round(r["avg"], 1)}
        for r in area_rows
    }
    areas["listening"] = {
        "count": listening["n"],
        "avg_mastery": round(listening["avg"], 1),
    }
    # 単語＋フレーズを合算してTOEIC目安を算出。
    total = words["total"] + phrases["total"]
    mastered = words["mastered"] + phrases["mastered"]
    avg = 0.0
    if total:
        avg = (words["avg_mastery"] * words["total"]
               + phrases["avg_mastery"] * phrases["total"]) / total
    return {
        "words": words,
        "phrases": phrases,
        "areas": areas,
        "toeic_estimate": toeic_estimate(avg, mastered, total),
        "overall_avg_mastery": round(avg, 1),
    }


@router.get("/memory")
def get_memory():
    return {"content": persistence.read_memory()}


@router.put("/memory")
def put_memory(payload: MemoryUpdateIn):
    persistence.write_memory(payload.content)
    return {"ok": True}


@router.get("/study-log")
def get_study_log():
    return {"content": persistence.read_study_log()}
