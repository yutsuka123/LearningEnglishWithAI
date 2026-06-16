"""System endpoints: settings, usage/cost, memory.md & study_log.md."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

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
    """項目別の習熟度サマリ + TOEIC換算(目安)。per-user。"""
    from ..database import db
    from ..services.auth import current_user_id
    from ..services.metrics import toeic_estimate, word_buckets

    from ..services.auth import get_user_settings
    uid = current_user_id()
    with db() as conn:
        words = word_buckets(conn, "words", user_id=uid)
        phrases = word_buckets(conn, "phrases", user_id=uid)
        self_toeic = get_user_settings(conn, uid).get("toeic_self")
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
    studied = words["studied"] + phrases["studied"]
    avg = 0.0
    if total:
        avg = (words["avg_mastery"] * words["total"]
               + phrases["avg_mastery"] * phrases["total"]) / total
    return {
        "words": words,
        "phrases": phrases,
        "areas": areas,
        "toeic_estimate": toeic_estimate(
            avg, mastered, total, studied=studied, self_declared=self_toeic),
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


# --- per-user UI 設定（端末非依存・サーバ保存）---
@router.get("/user-settings")
def get_user_settings():
    """現在ユーザーのUI設定(JSON)。クライアントの localStorage 同期先。"""
    import json

    from ..database import db
    from ..services.auth import current_user_id
    with db() as conn:
        row = conn.execute(
            "SELECT settings FROM user_settings WHERE user_id = ?",
            (current_user_id(),),
        ).fetchone()
    try:
        data = json.loads(row["settings"]) if row else {}
    except (ValueError, TypeError):
        data = {}
    return {"settings": data}


class UserSettingsIn(BaseModel):
    settings: dict = {}


@router.put("/user-settings")
def put_user_settings(payload: UserSettingsIn):
    import json

    from ..database import db
    from ..services.auth import current_user_id
    with db() as conn:
        conn.execute(
            "INSERT INTO user_settings (user_id, settings, updated_at) "
            "VALUES (?, ?, datetime('now')) "
            "ON CONFLICT(user_id) DO UPDATE SET "
            "settings=excluded.settings, updated_at=excluded.updated_at",
            (current_user_id(), json.dumps(payload.settings)),
        )
    return {"ok": True}


@router.get("/my-usage")
def my_usage():
    """現在ユーザーの当日/当月 AI利用・上限・前払い残高（コスト表示用）。"""
    from ..database import db
    from ..services import ai
    from ..services.auth import current_user_id, get_user

    from ..config import APP_VERSION
    from ..services.auth import multiuser_enabled
    uid = current_user_id()
    s = load_settings()
    day = ai._user_cost_usd(uid, "day")
    month = ai._user_cost_usd(uid, "month")
    with db() as conn:
        u = get_user(conn, uid) or {}
    rate = s.usd_jpy_rate
    # 実効上限(USD)：user個別→無ければグローバル日次。
    dcap = u.get("daily_cost_cap_usd") or s.ai_daily_cost_cap_usd or None
    mcap = u.get("monthly_cost_cap_usd") or None
    daily_cap_jpy = round(dcap * rate) if dcap else None
    # 月次上限が未設定なら、表示用に日次×30をフォールバックして月バーも出す。
    if mcap:
        monthly_cap_jpy = round(mcap * rate)
    elif dcap:
        monthly_cap_jpy = round(dcap * rate * 30)
    else:
        monthly_cap_jpy = None
    return {
        "today_jpy": round(day * rate, 1),
        "month_jpy": round(month * rate, 1),
        "daily_cap_jpy": daily_cap_jpy,
        "monthly_cap_jpy": monthly_cap_jpy,
        "balance_jpy": (round(u["balance_jpy"], 1)
                        if u.get("balance_jpy") is not None else None),
        "role": u.get("role", "user"),
        "username": u.get("username", ""),
        "model": s.openai_model,
        "version": APP_VERSION,
        "multiuser": multiuser_enabled(),
    }


@router.get("/admin/overview")
def admin_overview():
    """管理者ダッシュボード: 全ユーザーの使用量・残高・上限・状態と、
    不正/問題の手がかり（上限到達・残高切れ・ログインロック）。管理者専用。"""
    from ..database import db
    from ..services import auth
    s = load_settings()
    rate = s.usd_jpy_rate
    with db() as conn:
        me = auth.get_user(conn, auth.current_user_id())
        if not me or me.get("role") != "admin":
            raise HTTPException(403, "管理者のみ閲覧できます。")
        rows = conn.execute(
            "SELECT u.id, u.username, u.display_name, u.role, u.is_active, "
            " u.daily_cost_cap_usd dcap, u.monthly_cost_cap_usd mcap, "
            " u.balance_jpy, u.allow_banned, "
            " (SELECT COALESCE(SUM(cost_usd),0) FROM ai_usage a WHERE "
            "  a.user_id=u.id AND date(created_at,'localtime')="
            "  date('now','localtime')) today, "
            " (SELECT COALESCE(SUM(cost_usd),0) FROM ai_usage a WHERE "
            "  a.user_id=u.id AND strftime('%Y-%m',created_at,'localtime')="
            "  strftime('%Y-%m','now','localtime')) month, "
            " (SELECT COUNT(*) FROM ai_usage a WHERE a.user_id=u.id) calls, "
            " (SELECT MAX(created_at) FROM ai_usage a WHERE a.user_id=u.id) "
            "  last_used "
            "FROM users u ORDER BY u.id"
        ).fetchall()
    users = []
    for r in rows:
        dcap = r["dcap"] or s.ai_daily_cost_cap_usd or None
        mcap = r["mcap"] or None
        today_jpy = r["today"] * rate
        month_jpy = r["month"] * rate
        over_daily = bool(dcap and r["today"] >= dcap)
        over_monthly = bool(mcap and r["month"] >= mcap)
        bal = r["balance_jpy"]
        users.append({
            "id": r["id"], "username": r["username"],
            "display_name": r["display_name"], "role": r["role"],
            "is_active": bool(r["is_active"]),
            "allow_banned": bool(r["allow_banned"]),
            "today_jpy": round(today_jpy, 1),
            "month_jpy": round(month_jpy, 1),
            "daily_cap_jpy": round(dcap * rate) if dcap else None,
            "monthly_cap_jpy": round(mcap * rate) if mcap else None,
            "balance_jpy": round(bal, 1) if bal is not None else None,
            "calls": r["calls"], "last_used": r["last_used"],
            "over_daily": over_daily, "over_monthly": over_monthly,
            "balance_empty": bal is not None and bal <= 0,
        })
    return {"users": users, "security": auth.lockout_status()}


class ChargeIn(BaseModel):
    user_id: int
    amount_jpy: float


@router.post("/admin/charge")
def admin_charge(payload: ChargeIn):
    """管理者が対象ユーザーの前払い残高をチャージ（1回 ¥1〜¥1000）。
    残高は日次/月次の無料枠とは別管理で、枠到達後の利用で消費される。"""
    from ..database import db
    from ..services import auth
    amt = payload.amount_jpy
    if amt <= 0 or amt > 1000:
        raise HTTPException(400, "1回のチャージは ¥1〜¥1000 です。")
    with db() as conn:
        me = auth.get_user(conn, auth.current_user_id())
        if not me or me.get("role") != "admin":
            raise HTTPException(403, "管理者のみ操作できます。")
        target = auth.get_user(conn, payload.user_id)
        if not target:
            raise HTTPException(404, "ユーザーが見つかりません。")
        new = auth.add_balance(conn, payload.user_id, amt)
    return {"ok": True, "balance_jpy": round(new, 1)}
