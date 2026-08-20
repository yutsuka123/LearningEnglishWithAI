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


def _user_filter_sql(
    include_admin: bool, include_invited: bool, include_test: bool,
    alias: str = "u",
) -> str:
    """管理画面の各種集計から管理者/招待ユーザー/テストユーザーを除外する
    SQL条件（2026-08-20ユーザー要望・usersテーブルに`alias`でJOIN済みが
    前提）。行の主体がusersでない場合(usage_eventsの未ログイン操作等)は
    `{alias}.id IS NULL`になるため、常にフィルタの対象外＝含める。
    - include_admin=False: role='admin'を除外
    - include_invited=False: 「メール以外の招待ユーザー」= 自己サイン
      アップ(email列あり)ではない従来ユーザーを除外
    - include_test=False: 開発用テストアカウント(is_test=1)を除外
    """
    conds = []
    if not include_admin:
        conds.append(f"({alias}.role IS NULL OR {alias}.role != 'admin')")
    if not include_invited:
        conds.append(f"({alias}.id IS NULL OR {alias}.email != '')")
    if not include_test:
        conds.append(f"({alias}.id IS NULL OR {alias}.is_test = 0)")
    return " AND ".join(conds) if conds else "1=1"


@router.post("/admin/users/{user_id}/test-flag")
def admin_set_test_flag(user_id: int, payload: dict):
    """ユーザーの「テストユーザー」フラグを切り替える（管理画面の各種
    集計フィルタ用・2026-08-20）。開発用に作成したアカウントかどうかは
    機械的に判定できないため、管理者が手動でマークする設計。"""
    _require_admin()
    is_test = bool(payload.get("is_test"))
    with db() as conn:
        if not auth.get_user(conn, user_id):
            raise HTTPException(404, "ユーザーが見つかりません。")
        conn.execute(
            "UPDATE users SET is_test = ? WHERE id = ?",
            (1 if is_test else 0, user_id),
        )
    return {"ok": True, "user_id": user_id, "is_test": is_test}


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
# 上書きのたび変更前の値を user_settings_backups に退避し、直近3件だけ
# 残す(2026-08-19・誤操作/バグからの復旧用)。書き込み経路はここ1箇所に
# 集約し、PUT保存/復元のどちらもこの関数を通す。
_SETTINGS_BACKUP_KEEP = 3


def _save_user_settings(conn, user_id: int, settings: dict) -> None:
    prev = conn.execute(
        "SELECT settings FROM user_settings WHERE user_id = ?", (user_id,),
    ).fetchone()
    if prev is not None:
        conn.execute(
            "INSERT INTO user_settings_backups (user_id, settings) "
            "VALUES (?, ?)",
            (user_id, prev["settings"]),
        )
        conn.execute(
            "DELETE FROM user_settings_backups "
            "WHERE user_id = ? AND id NOT IN ("
            " SELECT id FROM user_settings_backups WHERE user_id = ? "
            " ORDER BY id DESC LIMIT ?)",
            (user_id, user_id, _SETTINGS_BACKUP_KEEP),
        )
    conn.execute(
        "INSERT INTO user_settings (user_id, settings, updated_at) "
        "VALUES (?, ?, datetime('now')) "
        "ON CONFLICT(user_id) DO UPDATE SET "
        "settings=excluded.settings, updated_at=excluded.updated_at",
        (user_id, json.dumps(settings)),
    )


@router.get("/user-settings")
def get_user_settings():
    """現在ユーザーのUI設定(JSON)。クライアントの localStorage 同期先。"""
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
    from ..services.auth import current_user_id
    with db() as conn:
        _save_user_settings(conn, current_user_id(), payload.settings)
    return {"ok": True}


@router.get("/user-settings/backups")
def list_user_settings_backups():
    """現在ユーザー自身の設定バックアップ一覧（直近3件・新しい順）。
    誤操作/バグで設定が壊れたとき、自分で見て復元できるようにする
    (2026-08-19)。"""
    from ..services.auth import current_user_id
    with db() as conn:
        rows = conn.execute(
            "SELECT id, settings, created_at FROM user_settings_backups "
            "WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (current_user_id(), _SETTINGS_BACKUP_KEEP),
        ).fetchall()
    out = []
    for r in rows:
        try:
            data = json.loads(r["settings"])
        except (ValueError, TypeError):
            data = {}
        out.append({
            "id": r["id"], "created_at": r["created_at"], "settings": data,
        })
    return {"backups": out}


class RestoreSettingsIn(BaseModel):
    backup_id: int


@router.post("/user-settings/restore")
def restore_user_settings(payload: RestoreSettingsIn):
    """指定バックアップの内容を現在の設定として復元する。復元前の現在値も
    同じ仕組みで退避されるので、復元自体もやり直しがきく。他ユーザーの
    バックアップは復元できない(user_idで絞り込み)。"""
    from ..services.auth import current_user_id
    uid = current_user_id()
    with db() as conn:
        row = conn.execute(
            "SELECT settings FROM user_settings_backups "
            "WHERE id = ? AND user_id = ?",
            (payload.backup_id, uid),
        ).fetchone()
        if not row:
            raise HTTPException(404, "指定のバックアップが見つかりません。")
        try:
            data = json.loads(row["settings"])
        except (ValueError, TypeError):
            raise HTTPException(400, "バックアップの内容を読み込めません。")
        _save_user_settings(conn, uid, data)
    return {"ok": True, "settings": data}


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
def admin_overview(
    include_admin: bool = False, include_invited: bool = False,
    include_test: bool = False,
):
    """管理者ダッシュボード: 全ユーザーの使用量・残高・上限・状態と、
    不正/問題の手がかり（上限到達・残高切れ・ログインロック）。管理者専用。
    既定では管理者自身/メール未登録の招待ユーザー/テストユーザーを一覧
    から除外する（2026-08-20ユーザー要望・include_*で個別に含められる。
    どのみち全ユーザー分を集計はしており、表示のみのフィルタ）。"""
    from ..database import db
    from ..services import auth
    s = load_settings()
    rate = s.usd_jpy_rate
    with db() as conn:
        me = auth.get_user(conn, auth.current_user_id())
        if not me or me.get("role") != "admin":
            raise HTTPException(403, "管理者のみ閲覧できます。")
        filter_sql = _user_filter_sql(include_admin, include_invited,
                                       include_test)
        rows = conn.execute(
            "SELECT u.id, u.username, u.display_name, u.role, u.is_active, "
            " u.email, u.is_test, "
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
            f"FROM users u WHERE {filter_sql} ORDER BY u.id"
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
            "has_email": bool(r["email"]),
            "is_test": bool(r["is_test"]),
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
def admin_login_log(
    limit: int = 100, include_admin: bool = False,
    include_invited: bool = False, include_test: bool = False,
):
    """直近のログイン試行ログ（成功/失敗とも・管理画面のログ確認用・
    2026-08-13。hostnameはIPのDNS逆引き結果・2026-08-20追加。ログイン
    直後はBackgroundTasksでの解決前のため空のことがあり、しばらくして
    再読み込みすると埋まる）。既定では他の集計と同じく管理者/招待
    ユーザー/テストユーザーの行を除外する（2026-08-20・login_logは
    user_idを持たずusernameで記録するため、usersとusernameでJOIN。
    存在しないユーザー名への誤ログイン試行はu.idがNULLになり、
    不正アクセス監視のため常に表示対象に含める）。"""
    _require_admin()
    limit = max(1, min(limit, 500))
    filter_sql = _user_filter_sql(include_admin, include_invited,
                                   include_test)
    with db() as conn:
        rows = conn.execute(
            "SELECT l.username, l.ip, l.hostname, l.success, l.created_at "
            "FROM login_log l LEFT JOIN users u ON u.username = l.username "
            f"WHERE {filter_sql} "
            "ORDER BY l.id DESC LIMIT ?", (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


@router.get("/admin/charge-key-log")
def admin_charge_key_log(
    limit: int = 100, include_admin: bool = False,
    include_invited: bool = False, include_test: bool = False,
):
    """チャージキー入力の試行ログ（成功/失敗とも・無期限保持・
    2026-08-19ユーザー要望「キー関係は無期限でログを残す」）。既定では
    他の集計と同じく管理者/招待ユーザー/テストユーザーを除外する
    （2026-08-20・従来は管理者のみ固定除外だったのを他の集計と揃えて
    切り替え可能にした）。"""
    _require_admin()
    limit = max(1, min(limit, 500))
    filter_sql = _user_filter_sql(include_admin, include_invited,
                                   include_test)
    with db() as conn:
        rows = conn.execute(
            "SELECT a.result, a.key_id_hash, a.created_at, "
            " u.username AS username, k.key_id AS charge_key_public_id "
            "FROM charge_key_attempts a "
            "LEFT JOIN users u ON u.id = a.user_id "
            "LEFT JOIN charge_keys k ON k.id = a.charge_key_id "
            f"WHERE {filter_sql} "
            "ORDER BY a.id DESC LIMIT ?", (limit,),
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
def admin_usage_analytics(
    days: int = 30, include_admin: bool = False,
    include_invited: bool = False, include_test: bool = False,
):
    """画面別アクセス・機能別再生・ボタン押下・IP別の集計（管理画面・
    2026-08-17）。usage_eventsテーブルからその場で集計するため常に最新
    （管理画面の「更新」ボタンはこのAPIを再取得するだけでよい）。
    既定では管理者自身/メール未登録の招待ユーザー/テストユーザーの
    イベントを集計から除外する（2026-08-20ユーザー要望・include_*で
    個別に含められる。未ログイン操作(user_id NULL)は常に含む）。"""
    _require_admin()
    days = max(1, min(days, 365))
    since = f"-{days} days"
    filter_sql = _user_filter_sql(include_admin, include_invited,
                                   include_test)

    def _grouped(conn, kind: str, limit: int = 50) -> list[dict]:
        rows = conn.execute(
            "SELECT category, label, COUNT(*) AS cnt, "
            "COUNT(DISTINCT ip) AS uniq_ip, "
            "COUNT(DISTINCT user_id) AS uniq_user FROM usage_events ue "
            "LEFT JOIN users u ON u.id = ue.user_id "
            "WHERE ue.kind = ? AND ue.created_at >= datetime('now', ?) "
            f"AND {filter_sql} "
            "GROUP BY category, label ORDER BY cnt DESC LIMIT ?",
            (kind, since, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def _grouped_by_category(conn, kind: str, limit: int = 50) -> list[dict]:
        """category単体での集計（word_domain/phrase_sceneはlabelを
        使わないため、page/play/clickと違いcategoryだけでまとめる）。"""
        rows = conn.execute(
            "SELECT category, COUNT(*) AS cnt, "
            "COUNT(DISTINCT ip) AS uniq_ip, "
            "COUNT(DISTINCT user_id) AS uniq_user FROM usage_events ue "
            "LEFT JOIN users u ON u.id = ue.user_id "
            "WHERE ue.kind = ? AND ue.created_at >= datetime('now', ?) "
            f"AND {filter_sql} "
            "GROUP BY category ORDER BY cnt DESC LIMIT ?",
            (kind, since, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    with db() as conn:
        pages = _grouped(conn, "page")
        plays = _grouped(conn, "play")
        clicks = _grouped(conn, "click")
        word_domains = _grouped_by_category(conn, "word_domain")
        phrase_scenes = _grouped_by_category(conn, "phrase_scene")

        # 年代・性別 × 分野/シーンのクロス集計（2026-08-19・「40代男性は
        # こんな分野をよく使っている」等を後から分析できるようにする用途）。
        # サインアップ時の任意アンケート(users.survey_age_group/gender)と
        # usage_events.user_idを突き合わせる。未回答は「(未回答)」扱い。
        demo_rows = conn.execute(
            "SELECT "
            " COALESCE(NULLIF(u.survey_age_group, ''), '(未回答)') AS age_group, "
            " COALESCE(NULLIF(u.survey_gender, ''), '(未回答)') AS gender, "
            " ue.kind AS kind, ue.category AS category, "
            " COUNT(*) AS cnt, COUNT(DISTINCT ue.user_id) AS uniq_user "
            "FROM usage_events ue JOIN users u ON u.id = ue.user_id "
            "WHERE ue.kind IN ('word_domain', 'phrase_scene') "
            f" AND ue.created_at >= datetime('now', ?) AND {filter_sql} "
            "GROUP BY age_group, gender, ue.kind, ue.category "
            "ORDER BY cnt DESC LIMIT 300",
            (since,),
        ).fetchall()

        # 登録時アンケート「このアプリを何で知りましたか」の集計（2026-08-19
        # ・複数選択のためsurvey_referralは", "区切りの文字列。Python側で
        # 分解してから件数を数える）。集計期間はusers.created_atで絞る。
        referral_text_rows = conn.execute(
            "SELECT survey_referral FROM users u "
            "WHERE survey_referral != '' AND username != 'guest' "
            f"AND created_at >= datetime('now', ?) AND {filter_sql}",
            (since,),
        ).fetchall()

        ip_rows = conn.execute(
            "SELECT ue.ip AS ip, COUNT(*) AS total, "
            "SUM(CASE WHEN ue.kind='page' THEN 1 ELSE 0 END) AS pages, "
            "SUM(CASE WHEN ue.kind='play' THEN 1 ELSE 0 END) AS plays, "
            "SUM(CASE WHEN ue.kind='click' THEN 1 ELSE 0 END) AS clicks, "
            "GROUP_CONCAT(DISTINCT u.username) AS usernames, "
            "MAX(ue.created_at) AS last_seen FROM usage_events ue "
            "LEFT JOIN users u ON u.id = ue.user_id "
            "WHERE ue.created_at >= datetime('now', ?) AND ue.ip != '' "
            f"AND {filter_sql} "
            "GROUP BY ue.ip ORDER BY total DESC LIMIT 50",
            (since,),
        ).fetchall()

        # created_atはSQLiteのdatetime('now')由来でUTC。日付の区切り
        # (0時境界)を日本時間で見たいので、集計キーだけ+9時間ずらして
        # から日付部分を取り出す(2026-08-19・UTC日境界のままだった不具合
        # を修正)。
        daily_rows = conn.execute(
            "SELECT substr(datetime(ue.created_at, '+9 hours'), 1, 10) "
            " AS date, "
            "SUM(CASE WHEN kind='page' THEN 1 ELSE 0 END) AS pages, "
            "SUM(CASE WHEN kind='play' THEN 1 ELSE 0 END) AS plays, "
            "SUM(CASE WHEN kind='click' THEN 1 ELSE 0 END) AS clicks "
            "FROM usage_events ue LEFT JOIN users u ON u.id = ue.user_id "
            "WHERE ue.created_at >= datetime('now', ?) "
            f"AND {filter_sql} "
            "GROUP BY date ORDER BY date",
            (since,),
        ).fetchall()

        # 日別の新規登録数（2026-08-19・ユーザー要望。ゲスト疑似ユーザー
        # は起動時に一度だけ作られる行なので実登録者数を歪めないよう除外）。
        signup_rows = conn.execute(
            "SELECT substr(datetime(created_at, '+9 hours'), 1, 10) AS date, "
            "COUNT(*) AS signups FROM users u "
            "WHERE created_at >= datetime('now', ?) AND username != 'guest' "
            f"AND {filter_sql} "
            "GROUP BY date ORDER BY date",
            (since,),
        ).fetchall()

        # 時間帯別(0〜23時・JST)の利用率（2026-08-19・ユーザー要望。対象
        # 期間全体を通した時間帯ごとの合計で、日をまたいで集計する）。
        hourly_rows = conn.execute(
            "SELECT CAST(substr(datetime(ue.created_at, '+9 hours'), 12, 2) "
            " AS INTEGER) AS hour, "
            "SUM(CASE WHEN kind='page' THEN 1 ELSE 0 END) AS pages, "
            "SUM(CASE WHEN kind='play' THEN 1 ELSE 0 END) AS plays, "
            "SUM(CASE WHEN kind='click' THEN 1 ELSE 0 END) AS clicks "
            "FROM usage_events ue LEFT JOIN users u ON u.id = ue.user_id "
            "WHERE ue.created_at >= datetime('now', ?) "
            f"AND {filter_sql} "
            "GROUP BY hour ORDER BY hour",
            (since,),
        ).fetchall()

        total_events = conn.execute(
            "SELECT COUNT(*) FROM usage_events ue "
            "LEFT JOIN users u ON u.id = ue.user_id "
            f"WHERE ue.created_at >= datetime('now', ?) AND {filter_sql}",
            (since,),
        ).fetchone()[0]

    # 管理者自身の既知IP(.env の ADMIN_KNOWN_IPS)には is_admin フラグを
    # 立てる。実訪問者と管理者自身のテスト操作を見分けやすくするため
    # (2026-08-18・ユーザーからのフィードバック契機)。
    admin_ips = load_admin_known_ips()
    ip_list = [dict(r) for r in ip_rows]
    for row in ip_list:
        row["is_admin"] = row["ip"] in admin_ips

    # usage_events由来(pages/plays/clicks)とusers由来(signups)は別集計
    # なので、日付をキーにマージする(どちらか一方にしか無い日も0埋めで
    # 出す)。
    daily_map: dict[str, dict] = {}
    for r in daily_rows:
        daily_map[r["date"]] = {
            "date": r["date"], "pages": r["pages"], "plays": r["plays"],
            "clicks": r["clicks"], "signups": 0,
        }
    for r in signup_rows:
        d = daily_map.setdefault(r["date"], {
            "date": r["date"], "pages": 0, "plays": 0, "clicks": 0,
            "signups": 0,
        })
        d["signups"] = r["signups"]
    daily_list = [daily_map[d] for d in sorted(daily_map)]

    # 0〜23時を0件でも埋めて返す(グラフ表示等で穴が空かないように)。
    hourly_map = {int(r["hour"]): dict(r) for r in hourly_rows}
    hourly_list = [
        hourly_map.get(h, {"hour": h, "pages": 0, "plays": 0, "clicks": 0})
        for h in range(24)
    ]

    # 複数選択のsurvey_referralを", "区切りで分解して件数化。
    referral_counts: dict[str, int] = {}
    for r in referral_text_rows:
        for v in (r["survey_referral"] or "").split(", "):
            v = v.strip()
            if v:
                referral_counts[v] = referral_counts.get(v, 0) + 1
    referrals = sorted(
        ({"label": k, "cnt": v} for k, v in referral_counts.items()),
        key=lambda x: -x["cnt"],
    )

    return {
        "days": days,
        "include_admin": include_admin,
        "include_invited": include_invited,
        "include_test": include_test,
        "total_events": total_events,
        "pages": pages,
        "plays": plays,
        "clicks": clicks,
        "word_domains": word_domains,
        "phrase_scenes": phrase_scenes,
        "demographics": [dict(r) for r in demo_rows],
        "ips": ip_list,
        "daily": daily_list,
        "hourly": hourly_list,
        "referrals": referrals,
    }


# ログ/バックアップ用に割り当てたディスク予算（2026-08-19・管理画面の
# 目安表示にのみ使う。強制的な上限ではない）。
_DISK_BUDGET_MB = 1024

# DB内のテーブルを用途別にグルーピングして表示する（管理画面の
# 「内容別使用量」用）。dbstat仮想テーブルが使えるSQLiteビルドでのみ
# 内訳を出せる（無ければテーブル合計サイズのみ返す）。
_TABLE_GROUPS = {
    "shared_content": [
        "words", "phrases", "materials", "categories", "listening_topics",
        "audio_blobs", "word_domain_tags",
    ],
    "user_data": [
        "users", "user_settings", "user_settings_backups",
        "user_word_progress", "user_phrase_progress",
        "user_material_progress", "user_listening_progress",
        "user_category_progress",
        "decks", "deck_words", "deck_progress",
        "phrase_decks", "deck_phrases", "phrase_deck_progress",
    ],
    "logs_history": [
        "usage_events", "ai_usage", "login_log", "balance_ledger",
        "landing_visits", "conversation_log", "phrase_attempts",
        "word_attempts", "study_sessions", "inquiries",
        "charge_key_attempts", "base_order_actions",
    ],
}


def _dir_size_bytes(path) -> int:
    if not path.exists():
        return 0
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


@router.get("/admin/disk-usage")
def admin_disk_usage():
    """ログ・バックアップ用に確保したディスク予算(既定1GB)に対する
    現在の使用量（管理画面の「その他」タブ表示用・2026-08-19）。
    Caddyのアクセスログは別コンテナ上にあるため集計対象外
    （件数等は「ログ」タブのアクセスログ集計を参照）。"""
    _require_admin()

    app_log_bytes = sum(
        f.stat().st_size for f in paths.data_dir.glob("app.log*")
        if f.is_file()
    )
    backups_dir = paths.data_dir / "backups"
    backups_bytes = _dir_size_bytes(backups_dir)
    db_file_bytes = (
        paths.db_file.stat().st_size if paths.db_file.exists() else 0
    )

    group_mb: dict[str, float] = {}
    dbstat_available = True
    with db() as conn:
        try:
            sizes = dict(conn.execute(
                "SELECT name, SUM(pgsize) FROM dbstat GROUP BY name"
            ).fetchall())
        except Exception:
            dbstat_available = False
            sizes = {}
        if dbstat_available:
            grouped_tables: set[str] = set()
            for group, tables in _TABLE_GROUPS.items():
                total = sum(sizes.get(t, 0) for t in tables)
                group_mb[group] = round(total / 1024 / 1024, 2)
                grouped_tables.update(tables)
            other_bytes = sum(
                v for k, v in sizes.items() if k not in grouped_tables
            )
            group_mb["other"] = round(other_bytes / 1024 / 1024, 2)

    app_log_mb = round(app_log_bytes / 1024 / 1024, 2)
    backups_mb = round(backups_bytes / 1024 / 1024, 2)
    db_total_mb = round(db_file_bytes / 1024 / 1024, 2)
    tracked_total_mb = round(app_log_mb + backups_mb, 2)  # DB本体は別枠表示

    return {
        "budget_mb": _DISK_BUDGET_MB,
        "app_log_mb": app_log_mb,
        "user_data_backups_mb": backups_mb,
        "tracked_total_mb": tracked_total_mb,
        "db_file_total_mb": db_total_mb,
        "db_breakdown_mb": group_mb,
        "dbstat_available": dbstat_available,
        "note": "Caddyのアクセスログは別コンテナ上にあるためここには含み"
                "ません（件数等は「ログ」タブを参照）。DB本体(音声等の"
                "共有コンテンツ含む)は予算の対象外の目安表示です。",
    }


@router.get("/admin/server-status")
def admin_server_status(
    include_admin: bool = False, include_invited: bool = False,
    include_test: bool = False,
):
    """VPSホストのCPU/RAM/ディスク負荷＋直近アクティブユーザー数
    （サーバー状態監視・2026-08-20ユーザー要望）。サクラVPSはn8n・ecopy
    等の他dockerプロジェクトと相乗りのため、コンテナ内からはホスト
    全体の負荷が見えない。CPU/RAM/ディスクは scripts/
    collect_server_stats.py がVPSホストのcronで定期収集して書き出す
    data/server_stats.jsonl の最新行を読むだけ（ここでは計測しない・
    analyze_access_log.py と同じ流儀）。ファイルが無い場合(ローカル
    開発時・cron未設定時)は host=null で返す。同時アクセス数は既定で
    管理者/招待ユーザー/テストユーザーを除く（他の集計と同じフィルタ・
    2026-08-20）。"""
    _require_admin()
    path = paths.data_dir / "server_stats.jsonl"
    latest = None
    if path.exists():
        with path.open(encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    latest = json.loads(line)
                except ValueError:
                    continue
    filter_sql = _user_filter_sql(include_admin, include_invited,
                                   include_test)
    with db() as conn:
        row = conn.execute(
            "SELECT COUNT(DISTINCT ue.user_id) AS c FROM usage_events ue "
            "JOIN users u ON u.id = ue.user_id "
            "WHERE ue.created_at >= datetime('now', '-5 minutes') "
            f"AND {filter_sql}"
        ).fetchone()
    return {"host": latest, "active_users_5min": row["c"]}
