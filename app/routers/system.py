"""System endpoints: settings, usage/cost, memory.md & study_log.md."""

from __future__ import annotations

import json
import re

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..config import ROOT_DIR, load_admin_known_ips, load_settings, log, paths
from ..database import ACCENTS, NEWS_FIELDS, db
from ..schemas import MemoryUpdateIn, SettingsIn
from ..services import ai, auth, persistence, tracking

router = APIRouter(prefix="/api/system", tags=["system"])


def _latest_changelog_date() -> str | None:
    """CHANGELOG.mdの先頭エントリの日付(YYYY-MM-DD)。about.htmlの
    「バージョン/リリース日」表示をCHANGELOG更新に自動追従させるため
    （手動転記の同期漏れを防ぐ・2026-08-12）。"""
    try:
        text = (ROOT_DIR / "CHANGELOG.md").read_text(encoding="utf-8")
    except OSError:
        return None
    m = re.search(r"^## .*\((\d{4}-\d{2}-\d{2})", text, re.MULTILINE)
    return m.group(1) if m else None


def _require_admin() -> None:
    """管理者専用エンドポイントのガード（未管理者は403）。"""
    with db() as conn:
        me = auth.get_user(conn, auth.current_user_id())
    if not me or me.get("role") != "admin":
        raise HTTPException(403, "管理者のみ利用できます。")


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
    """管理者専用(2026-08-12セキュリティ修正・Wチェック監査で発見:
    マスク済みAPIキー・ホスト/ポート等を非管理者にも返していた)。
    非管理者向けのAI有効状態は`/api/system/my-usage`の`ai_enabled`で
    別途提供済み(static/js/app.jsのrefreshCost/refreshAiState参照)。"""
    _require_admin()
    from ..config import APP_VERSION, load_tokushoho_info

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
        "tokushoho_ready": all(load_tokushoho_info().values()),
        "version": APP_VERSION,
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
    _require_admin()
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
    _require_admin()
    return ai.usage_summary()


@router.get("/progress")
def progress():
    """項目別の習熟度サマリ + TOEIC換算(目安)。per-user。"""
    from ..database import db
    from ..services.auth import current_user_id
    from ..services.metrics import toeic_estimate, word_buckets
    from ..services.spaced_repetition import mastery_config_from_settings

    from ..services.auth import get_user_settings
    uid = current_user_id()
    with db() as conn:
        us = get_user_settings(conn, uid)
        cfg = mastery_config_from_settings(us)
        words = word_buckets(conn, "words", user_id=uid, cfg=cfg)
        phrases = word_buckets(conn, "phrases", user_id=uid, cfg=cfg)
        self_toeic = us.get("toeic_self")
        # 会話/読/書/文学: エリア別の平均習熟度（per-user、他ユーザーの
        # 学習は混ざらない。2026-08-08にcategories直書きから分離）。
        area_rows = conn.execute(
            "SELECT c.area, COUNT(*) AS n, "
            "COALESCE(AVG(ucp.mastery),0) AS avg "
            "FROM categories c LEFT JOIN user_category_progress ucp "
            "ON ucp.category_id = c.id AND ucp.user_id = ? "
            "GROUP BY c.area", (uid,)
        ).fetchall()
        listening = conn.execute(
            "SELECT COALESCE(AVG(ulp.comprehension),0) AS avg, "
            "COUNT(*) AS n FROM listening_topics lt "
            "LEFT JOIN user_listening_progress ulp "
            "ON ulp.topic_id = lt.id AND ulp.user_id = ?", (uid,)
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
    from ..services.auth import current_user_id, get_user, is_guest_user_id

    from ..config import APP_VERSION
    from ..services.auth import multiuser_enabled
    uid = current_user_id()
    s = load_settings()
    day = ai._user_cost_usd(uid, "day")
    month = ai._user_cost_usd(uid, "month")
    with db() as conn:
        u = get_user(conn, uid) or {}
        is_guest = is_guest_user_id(conn, uid)
    rate = s.usd_jpy_rate
    # 実効上限(USD)：_user_guardと同じロジック(個別設定→既定=旧ユーザーの
    # みEmail未設定なら¥150/日、それ以外0円)を使う。以前はここだけ別計算
    # (グローバル日次にフォールバック)で、実際は無料枠0円のユーザーにも
    # 上限が余裕あるように見えてしまう不整合があったため統一した
    # (2026-08-12)。
    dcap_usd, mcap_usd = ai._effective_caps(u, s)
    daily_cap_jpy = round(dcap_usd * rate)
    monthly_cap_jpy = round(mcap_usd * rate)
    today_jpy = round(day * rate, 1)
    month_jpy = round(month * rate, 1)
    balance_jpy = u.get("balance_jpy")
    # 「今日」「今月」の枠は個別に案内せず、実際にAIが止まるタイミングと
    # 一致する単一の残量に統合する(無料枠の残り＋チャージ残高)。無料枠は
    # 日次/月次どちらか厳しい方で頭打ちにする。
    quota_remain_jpy = min(max(0.0, daily_cap_jpy - today_jpy),
                            max(0.0, monthly_cap_jpy - month_jpy))
    remaining_jpy = round(quota_remain_jpy + (balance_jpy or 0), 1)
    return {
        "today_jpy": today_jpy,
        "month_jpy": month_jpy,
        "daily_cap_jpy": daily_cap_jpy,
        "monthly_cap_jpy": monthly_cap_jpy,
        "balance_jpy": (round(balance_jpy, 1)
                        if balance_jpy is not None else None),
        "remaining_jpy": remaining_jpy,
        "role": u.get("role", "user"),
        "username": u.get("username", ""),
        "model": s.openai_model,
        "version": APP_VERSION,
        "version_date": _latest_changelog_date(),
        "multiuser": multiuser_enabled(),
        "is_guest": is_guest,
        # ゲストは api_key_masked 等を含む /api/system/settings を読めない
        # ため、AI有効フラグだけはここ(秘匿情報なし)からも取れるようにする。
        "ai_enabled": s.ai_enabled,
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
            "  last_used, "
            " (SELECT COUNT(DISTINCT a.ip) FROM ai_usage a WHERE "
            "  a.user_id=u.id AND a.ip <> '' AND "
            "  a.created_at >= datetime('now','-30 days')) distinct_ips_30d, "
            " (SELECT COUNT(*) FROM word_attempts wa "
            "  WHERE wa.user_id=u.id) word_quizzes, "
            " (SELECT COUNT(*) FROM phrase_attempts pa "
            "  WHERE pa.user_id=u.id) phrase_quizzes, "
            " (SELECT MAX(x) FROM ("
            "   SELECT MAX(created_at) x FROM word_attempts "
            "    WHERE user_id=u.id "
            "   UNION ALL "
            "   SELECT MAX(created_at) FROM phrase_attempts "
            "    WHERE user_id=u.id"
            "  )) last_studied "
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
            "distinct_ips_30d": r["distinct_ips_30d"],
            "over_daily": over_daily, "over_monthly": over_monthly,
            "balance_empty": bal is not None and bal <= 0,
            "word_quizzes": r["word_quizzes"],
            "phrase_quizzes": r["phrase_quizzes"],
            "last_studied": r["last_studied"],
        })
    return {"users": users, "security": auth.lockout_status()}


class ChargeIn(BaseModel):
    user_id: int
    amount_jpy: float
    note: str = ""


@router.post("/admin/charge")
def admin_charge(payload: ChargeIn):
    """管理者が対象ユーザーの前払い残高を手動で増減する（1回 ±¥10,000まで）。
    残高は日次/月次の無料枠とは別管理で、枠到達後の利用で消費される。
    2026-08-18〜: チャージキー不具合等の万が一の是正のため負の値（減額調整）
    も許可。理由(note)は必須にし、balance_ledgerに監査記録を残す。"""
    from ..database import db
    from ..services import auth
    amt = payload.amount_jpy
    note = payload.note.strip()
    if amt == 0 or abs(amt) > 10000:
        raise HTTPException(400, "1回の変更額は ¥1〜¥10,000（減額は-¥10,000〜-¥1）です。")
    if not note:
        raise HTTPException(400, "理由(note)の入力は必須です。")
    with db() as conn:
        me = auth.get_user(conn, auth.current_user_id())
        if not me or me.get("role") != "admin":
            raise HTTPException(403, "管理者のみ操作できます。")
        target = auth.get_user(conn, payload.user_id)
        if not target:
            raise HTTPException(404, "ユーザーが見つかりません。")
        new = auth.add_balance(
            conn, payload.user_id, amt,
            reason="admin_adjustment", note=note, admin_user_id=me["id"])
    log.info("admin_charge: uid=%s delta=%s note=%s by_admin=%s new_balance=%s",
              payload.user_id, amt, note, me["id"], new)
    return {"ok": True, "balance_jpy": round(new, 1)}


@router.get("/admin/balance-ledger")
def admin_balance_ledger(user_id: int | None = None, limit: int = 50):
    """残高変更履歴（監査用）。user_id指定でその人のみ、未指定で全体の直近分。"""
    from ..database import db
    from ..services import auth
    limit = max(1, min(limit, 200))
    with db() as conn:
        me = auth.get_user(conn, auth.current_user_id())
        if not me or me.get("role") != "admin":
            raise HTTPException(403, "管理者のみ操作できます。")
        where = "WHERE l.user_id = ?" if user_id else ""
        args = (user_id,) if user_id else ()
        rows = conn.execute(
            "SELECT l.id, l.user_id, u.username, l.delta_jpy, "
            " l.balance_after, l.reason, l.note, l.charge_key_id, "
            " l.admin_user_id, a.username AS admin_username, l.created_at "
            "FROM balance_ledger l "
            "JOIN users u ON u.id = l.user_id "
            "LEFT JOIN users a ON a.id = l.admin_user_id "
            f"{where} ORDER BY l.id DESC LIMIT ?",
            (*args, limit),
        ).fetchall()
    return {"ok": True, "entries": [dict(r) for r in rows]}


class ForceLogoutIn(BaseModel):
    user_id: int


@router.post("/admin/force-logout")
def admin_force_logout(payload: ForceLogoutIn):
    """管理者が対象ユーザーの既存の全セッションを強制的に無効化する
    （§B4）。不正アクセスの疑い等で特定ユーザーだけを強制ログアウト
    させたい場合に使う（他ユーザーには影響しない）。"""
    from ..database import db
    from ..services import auth
    with db() as conn:
        me = auth.get_user(conn, auth.current_user_id())
        if not me or me.get("role") != "admin":
            raise HTTPException(403, "管理者のみ操作できます。")
        target = auth.get_user(conn, payload.user_id)
        if not target:
            raise HTTPException(404, "ユーザーが見つかりません。")
        epoch = auth.bump_session_epoch(conn, payload.user_id)
    return {"ok": True, "session_epoch": epoch}


@router.get("/admin/login-log")
def admin_login_log(limit: int = 100):
    """直近のログイン試行ログ（成功/失敗とも・管理画面のログ確認用・
    2026-08-13）。"""
    _require_admin()
    limit = max(1, min(limit, 500))
    with db() as conn:
        rows = conn.execute(
            "SELECT username, ip, success, created_at FROM login_log "
            "ORDER BY id DESC LIMIT ?", (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


@router.get("/admin/error-log")
def admin_error_log(lines: int = 200):
    """アプリのエラーログ(data/app.log)の末尾を返す（管理画面のログ確認用・
    2026-08-13）。ファイルが無い/空でも空配列を返す（起動直後等）。"""
    _require_admin()
    lines = max(1, min(lines, 1000))
    path = paths.data_dir / "app.log"
    if not path.exists():
        return {"lines": []}
    with path.open(encoding="utf-8", errors="replace") as f:
        all_lines = f.readlines()
    return {"lines": [ln.rstrip("\n") for ln in all_lines[-lines:]]}


@router.get("/admin/access-log-summary")
def admin_access_log_summary(
    days: int = 30, date_from: str = "", date_to: str = "",
):
    """アクセスログ日次集計の表示（管理画面用・2026-08-13）。
    scripts/analyze_access_log.py がVPS側でcron実行して生成する
    data/analytics/access_summary.jsonl を読むだけ（ここでは集計しない）。
    ファイルが無い場合(ローカル開発時・cron未実行時)は空配列。
    date_from/date_toを指定すると(YYYY-MM-DD)、daysより優先してその
    範囲（両端含む）で絞り込む（2026-08-18・年月日での期間指定に対応）。"""
    _require_admin()
    days = max(1, min(days, 365))
    path = paths.data_dir / "analytics" / "access_summary.jsonl"
    if not path.exists():
        return {"days": []}
    records = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except ValueError:
                continue
    records.sort(key=lambda r: r.get("date", ""))
    date_from = date_from.strip()
    date_to = date_to.strip()
    if date_from or date_to:
        picked = [
            r for r in records
            if (not date_from or r.get("date", "") >= date_from)
            and (not date_to or r.get("date", "") <= date_to)
        ]
    else:
        picked = records[-days:]

    # 各日の categories(集計値はあるが従来UI未表示だった内訳: 人間らしき
    # アクセス/AIクローラー/検索bot/その他bot)を期間合計してサマリ化
    # (2026-08-18)。個々のカテゴリキーは classify_ua() の戻り値そのもの
    # (例 "ai_crawler:GPTBot")なので、先頭区分だけにまとめて表示する。
    totals = {"human": 0, "ai_crawler": 0, "search_bot": 0,
              "other_bot": 0, "unknown": 0}
    total_requests = 0
    for r in picked:
        total_requests += r.get("total_requests", 0)
        for cat, cnt in (r.get("categories") or {}).items():
            bucket = cat.split(":", 1)[0]
            if bucket not in totals:
                bucket = "unknown"
            totals[bucket] += cnt
    summary = {"total_requests": total_requests, "by_category": totals}
    return {"days": picked, "summary": summary}


@router.get("/admin/ai-usage-search")
def admin_ai_usage_search(
    user_id: int | None = None,
    date_from: str = "",
    date_to: str = "",
    feature: str = "",
    model: str = "",
    ip: str = "",
    limit: int = 100,
    offset: int = 0,
):
    """ai_usageテーブルの検索・絞り込み（管理画面用・2026-08-13）。
    テスト/開発起因のノイズと実利用を切り分けやすいよう、ユーザーID・
    期間・機能・モデル・IPで絞り込み、該当件数と合計費用(USD)も返す。"""
    _require_admin()
    limit = max(1, min(limit, 500))
    offset = max(0, offset)

    where: list[str] = []
    params: list = []
    if user_id is not None:
        where.append("user_id = ?")
        params.append(user_id)
    if date_from:
        where.append("created_at >= ?")
        params.append(date_from)
    if date_to:
        where.append("created_at <= ?")
        params.append(date_to + " 23:59:59")
    if feature:
        where.append("feature = ?")
        params.append(feature)
    if model:
        where.append("model = ?")
        params.append(model)
    if ip:
        where.append("ip = ?")
        params.append(ip)
    clause = ("WHERE " + " AND ".join(where)) if where else ""

    with db() as conn:
        total = conn.execute(
            f"SELECT COUNT(*) AS n, COALESCE(SUM(cost_usd), 0) AS cost "
            f"FROM ai_usage {clause}", params,
        ).fetchone()
        rows = conn.execute(
            f"SELECT id, user_id, ip, model, feature, prompt_tokens, "
            f"output_tokens, cost_usd, created_at FROM ai_usage {clause} "
            f"ORDER BY id DESC LIMIT ? OFFSET ?",
            params + [limit, offset],
        ).fetchall()
    return {
        "total_count": total["n"],
        "total_cost_usd": total["cost"],
        "rows": [dict(r) for r in rows],
    }


class TrackEventIn(BaseModel):
    kind: str
    category: str = ""
    label: str = ""


@router.post("/track")
def track_event(payload: TrackEventIn):
    """画面表示・ボタン押下のイベント記録（管理画面の利用状況分析用・
    2026-08-17）。音声再生(play)は実際に音声を返した時点でサーバー側
    (learn.pyのtts系エンドポイント)が記録するため、ここではpage/click
    のみ受け付ける。ゲストも記録対象(_GUEST_READ_PREFIXESに追加済み)。
    記録失敗が画面操作を妨げないよう常に200を返すbest-effort。"""
    if payload.kind in ("page", "click"):
        tracking.log_event(payload.kind, payload.category, payload.label)
    return {"ok": True}


@router.get("/admin/usage-analytics")
def admin_usage_analytics(days: int = 30):
    """画面別アクセス・機能別再生・ボタン押下・IP別の集計（管理画面・
    2026-08-17）。usage_eventsテーブルからその場で集計するため常に最新
    （管理画面の「更新」ボタンはこのAPIを再取得するだけでよい）。"""
    _require_admin()
    days = max(1, min(days, 365))
    since = f"-{days} days"

    def _grouped(conn, kind: str, limit: int = 50) -> list[dict]:
        rows = conn.execute(
            "SELECT category, label, COUNT(*) AS cnt, "
            "COUNT(DISTINCT ip) AS uniq_ip, "
            "COUNT(DISTINCT user_id) AS uniq_user FROM usage_events "
            "WHERE kind = ? AND created_at >= datetime('now', ?) "
            "GROUP BY category, label ORDER BY cnt DESC LIMIT ?",
            (kind, since, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    with db() as conn:
        pages = _grouped(conn, "page")
        plays = _grouped(conn, "play")
        clicks = _grouped(conn, "click")

        ip_rows = conn.execute(
            "SELECT ue.ip AS ip, COUNT(*) AS total, "
            "SUM(CASE WHEN ue.kind='page' THEN 1 ELSE 0 END) AS pages, "
            "SUM(CASE WHEN ue.kind='play' THEN 1 ELSE 0 END) AS plays, "
            "SUM(CASE WHEN ue.kind='click' THEN 1 ELSE 0 END) AS clicks, "
            "GROUP_CONCAT(DISTINCT u.username) AS usernames, "
            "MAX(ue.created_at) AS last_seen FROM usage_events ue "
            "LEFT JOIN users u ON u.id = ue.user_id "
            "WHERE ue.created_at >= datetime('now', ?) AND ue.ip != '' "
            "GROUP BY ue.ip ORDER BY total DESC LIMIT 50",
            (since,),
        ).fetchall()

        daily_rows = conn.execute(
            "SELECT substr(created_at, 1, 10) AS date, "
            "SUM(CASE WHEN kind='page' THEN 1 ELSE 0 END) AS pages, "
            "SUM(CASE WHEN kind='play' THEN 1 ELSE 0 END) AS plays, "
            "SUM(CASE WHEN kind='click' THEN 1 ELSE 0 END) AS clicks "
            "FROM usage_events WHERE created_at >= datetime('now', ?) "
            "GROUP BY date ORDER BY date",
            (since,),
        ).fetchall()

        total_events = conn.execute(
            "SELECT COUNT(*) FROM usage_events "
            "WHERE created_at >= datetime('now', ?)", (since,),
        ).fetchone()[0]

    # 管理者自身の既知IP(.env の ADMIN_KNOWN_IPS)には is_admin フラグを
    # 立てる。実訪問者と管理者自身のテスト操作を見分けやすくするため
    # (2026-08-18・ユーザーからのフィードバック契機)。
    admin_ips = load_admin_known_ips()
    ip_list = [dict(r) for r in ip_rows]
    for row in ip_list:
        row["is_admin"] = row["ip"] in admin_ips

    return {
        "days": days,
        "total_events": total_events,
        "pages": pages,
        "plays": plays,
        "clicks": clicks,
        "ips": ip_list,
        "daily": [dict(r) for r in daily_rows],
    }
