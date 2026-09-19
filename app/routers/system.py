"""System endpoints: settings, usage/cost, memory.md & study_log.md."""

from __future__ import annotations

import collections
import json
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool

from ..services import errors
from pydantic import BaseModel

from ..config import ROOT_DIR, load_admin_known_ips, load_settings, log, paths
from ..database import ACCENTS, NEWS_FIELDS, db
from ..schemas import MemoryUpdateIn, SettingsIn
from ..services import (
    ai, auth, persistence, traffic_source, tracking, ua_parse, visitor_kind,
)

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
        raise errors.http_error("2004", "管理者のみ利用できます。")


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

    2026-09-12修正: 未ログインの匿名アクセスはuser_idがNULLになる訳では
    なく、起動時に一度だけ作られる共有の「ゲスト疑似ユーザー」行
    (auth.GUEST_USERNAME・email=''・role='user')が入る
    (app/database.py の usage_events 定義コメント参照)。そのため
    include_invited=False時の`email != ''`条件がゲスト由来の行(＝実際の
    匿名訪問者のイベントの大半)を「メール未設定の招待ユーザー」と誤認して
    除外し、管理画面の日別/時間帯別集計等がほぼ空になる不具合があった。
    ゲスト行は`id IS NULL`と同様に常にフィルタ対象外(＝含める)とする。
    """
    conds = []
    if not include_admin:
        conds.append(f"({alias}.role IS NULL OR {alias}.role != 'admin')")
    if not include_invited:
        conds.append(
            f"({alias}.id IS NULL OR {alias}.username = "
            f"'{auth.GUEST_USERNAME}' OR {alias}.email != '')")
    if not include_test:
        conds.append(f"({alias}.id IS NULL OR {alias}.is_test = 0)")
    return " AND ".join(conds) if conds else "1=1"


def _own_device_sids(conn) -> dict[str, dict[str, bool]]:
    """管理者/テストアカウントでログインしたことのある端末(guest_sid
    Cookie)の一覧を返す: {guest_sid: {"admin": bool, "test": bool}}
    （2026-09-19ユーザー要望「お得意様・ゲストIP別の分析から、自分の
    テストアカウントと管理者を分離したい」対応）。

    guest_sid Cookieはログイン中の操作にも同じ値で記録される
    (app/main.py・tracking.log_event)ため、同じブラウザで管理者/
    テストアカウントとして操作した記録があれば「自分の端末」と分かる。
    これで、その端末で**ログアウト状態のまま**確認した操作(=ゲスト扱いで
    IPも一般ゲストと区別できない)も分析から分離できる。IPが変わりやすい
    モバイル回線でも効く点が、既知IP(ADMIN_KNOWN_IPS)判定との違い。
    限界: 一度もログインしていない端末・Cookieを消した直後の操作は
    判別できない(その端末でログインした時点から遡って効く)。"""
    rows = conn.execute(
        "SELECT ue.guest_sid AS sid, "
        " MAX(CASE WHEN u.role = 'admin' THEN 1 ELSE 0 END) AS is_admin, "
        " MAX(u.is_test) AS is_test "
        "FROM usage_events ue JOIN users u ON u.id = ue.user_id "
        "WHERE ue.guest_sid != '' AND (u.role = 'admin' OR u.is_test = 1) "
        "GROUP BY ue.guest_sid"
    ).fetchall()
    return {
        r["sid"]: {"admin": bool(r["is_admin"]), "test": bool(r["is_test"])}
        for r in rows
    }


# usage_eventsのうち「操作」ではない計測ビーコン(JS到達boot・離脱leave・
# 2026-09-19計測設計3-B)。画面/ボタン/再生の件数・イベント数の閾値・最後に
# 見ていた画面の判定などの「利用状況」集計からは除く。到達率・滞在時間を
# 見る専用の集計(admin_registration_funnel・admin_visit_trend)だけが読む。
_UE_ACTION_ONLY = "kind NOT IN ('boot', 'leave')"
_UE_ACTION_ONLY_UE = "ue.kind NOT IN ('boot', 'leave')"


@router.post("/admin/users/{user_id}/test-flag")
def admin_set_test_flag(user_id: int, payload: dict):
    """ユーザーの「テストユーザー」フラグを切り替える（管理画面の各種
    集計フィルタ用・2026-08-20）。開発用に作成したアカウントかどうかは
    機械的に判定できないため、管理者が手動でマークする設計。"""
    _require_admin()
    is_test = bool(payload.get("is_test"))
    with db() as conn:
        if not auth.get_user(conn, user_id):
            raise errors.http_error("7001", "ユーザーが見つかりません。")
        conn.execute(
            "UPDATE users SET is_test = ? WHERE id = ?",
            (1 if is_test else 0, user_id),
        )
    return {"ok": True, "user_id": user_id, "is_test": is_test}


@router.get("/admin/registrants")
def admin_registrants(
    include_admin: bool = False, include_invited: bool = False,
    include_test: bool = False, limit: int = 200,
):
    """登録者一覧(アンケート回答込み)。管理者画面④用(2026-09-01・
    ユーザー要望「登録者の確認」)。/admin/overviewは利用量・課金状態が
    主目的でメール本体やアンケート内容を含まないため、別エンドポイントに
    分離した。新しい登録から確認したいはずなのでcreated_at降順。"""
    _require_admin()
    limit = max(1, min(limit, 500))
    filter_sql = _user_filter_sql(include_admin, include_invited,
                                   include_test)
    with db() as conn:
        rows = conn.execute(
            "SELECT id, username, email, display_name, full_name, "
            "furigana, display_name_furigana, created_at, role, is_test, "
            "survey_occupation_category, survey_occupation_detail, "
            "survey_age_group, survey_gender, survey_purpose, "
            "survey_referral, survey_interest_areas, survey_free_text "
            f"FROM users u WHERE {filter_sql} "
            # ゲスト疑似ユーザー行そのものは登録者ではないので常に除外
            # (2026-09-12・_user_filter_sqlはinclude_invited=Falseでも
            # usage_events集計向けにゲストを常に含める仕様に変更したため、
            # ここは別途明示的に弾く)。
            f"AND u.username != '{auth.GUEST_USERNAME}' "
            "ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return {"ok": True, "items": [dict(r) for r in rows]}


def _split_multi(value: str) -> list[str]:
    """アンケートの複数選択欄(collectWithOtherが', '区切りで保存)を
    個別の値に分割する。空欄・前後空白は除く。"""
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


@router.get("/admin/survey-summary")
def admin_survey_summary(
    include_admin: bool = False, include_invited: bool = False,
    include_test: bool = False,
):
    """アンケート結果の集計表示。管理者画面⑤用(2026-09-01・ユーザー要望
    「アンケートの確認(内容詳しく集計表示)」)。単一選択欄はそのまま、
    複数選択欄(職業詳細/目的/きっかけ/興味分野)は', '区切りを分解して
    個別に集計する。"""
    _require_admin()
    from collections import Counter
    filter_sql = _user_filter_sql(include_admin, include_invited,
                                   include_test)
    with db() as conn:
        rows = conn.execute(
            "SELECT id, display_name, survey_occupation_category, "
            "survey_occupation_detail, survey_age_group, survey_gender, "
            "survey_purpose, survey_referral, survey_interest_areas, "
            "survey_free_text "
            f"FROM users u WHERE {filter_sql} "
            f"AND u.username != '{auth.GUEST_USERNAME}'"
        ).fetchall()
    total = len(rows)
    answered = 0
    occupation_category: Counter = Counter()
    occupation_detail: Counter = Counter()
    age_group: Counter = Counter()
    gender: Counter = Counter()
    purpose: Counter = Counter()
    referral: Counter = Counter()
    interest_areas: Counter = Counter()
    free_text: list[dict] = []
    for r in rows:
        has_any = any([
            r["survey_occupation_category"], r["survey_age_group"],
            r["survey_gender"], r["survey_purpose"], r["survey_referral"],
            r["survey_interest_areas"], r["survey_free_text"],
        ])
        if has_any:
            answered += 1
        if r["survey_occupation_category"]:
            occupation_category[r["survey_occupation_category"]] += 1
        for v in _split_multi(r["survey_occupation_detail"]):
            occupation_detail[v] += 1
        if r["survey_age_group"]:
            age_group[r["survey_age_group"]] += 1
        if r["survey_gender"]:
            gender[r["survey_gender"]] += 1
        for v in _split_multi(r["survey_purpose"]):
            purpose[v] += 1
        for v in _split_multi(r["survey_referral"]):
            referral[v] += 1
        for v in _split_multi(r["survey_interest_areas"]):
            interest_areas[v] += 1
        if (r["survey_free_text"] or "").strip():
            free_text.append({
                "user_id": r["id"], "display_name": r["display_name"],
                "text": r["survey_free_text"],
            })

    def _sorted(c: Counter) -> list[dict]:
        return [{"label": k, "count": v}
                for k, v in sorted(c.items(), key=lambda kv: -kv[1])]

    return {
        "ok": True,
        "total": total,
        "answered": answered,
        "occupation_category": _sorted(occupation_category),
        "occupation_detail": _sorted(occupation_detail),
        "age_group": _sorted(age_group),
        "gender": _sorted(gender),
        "purpose": _sorted(purpose),
        "referral": _sorted(referral),
        "interest_areas": _sorted(interest_areas),
        "free_text": free_text,
    }


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
            raise errors.http_error("7001", "指定のバックアップが見つかりません。")
        try:
            data = json.loads(row["settings"])
        except (ValueError, TypeError):
            raise errors.http_error("7002", "バックアップの内容を読み込めません。")
        _save_user_settings(conn, uid, data)
    return {"ok": True, "settings": data}


@router.get("/my-usage")
def my_usage():
    """現在ユーザーの当日/当月 AI利用・上限・前払い残高（コスト表示用）。"""
    from ..database import db
    from ..services import ai
    from ..services.auth import (
        current_user_id, get_user, is_guest_user_id, is_charged_or_admin)

    from ..config import APP_VERSION
    from ..services import paypay
    from ..services.auth import multiuser_enabled
    uid = current_user_id()
    s = load_settings()
    day = ai._user_cost_usd(uid, "day")
    month = ai._user_cost_usd(uid, "month")
    with db() as conn:
        u = get_user(conn, uid) or {}
        is_guest = is_guest_user_id(conn, uid)
        # クロスワード「自分で作る」等、課金ユーザー限定機能のフロント側
        # ゲート表示用(2026-09-06・AI原価が実際に発生する機能は無料登録
        # だけでは開放しない方針に変更。バックエンドのis_charged_or_admin
        # と完全に同じ判定をフロントにも渡し、表示と実際の可否がズレない
        # ようにする)。
        is_charged = is_charged_or_admin(conn, uid)
        # 2026-09-07・一般公開対応: can_chargeはconn(DB接続)を使うため、
        # withブロックの外(connクローズ後)で呼ぶと`Cannot operate on a
        # closed database`で毎回500になる(公開直後に発覚した重大な回帰。
        # 全ユーザーの/my-usageが失敗しログイン後に情報が引けずゲスト
        # 相当の表示になっていた)。ブロック内で計算して変数に保持する。
        can_paypay_charge = paypay.can_charge(
            conn, uid, u.get("username", ""), u.get("role", ""), is_guest)
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
        "is_charged_or_admin": is_charged,
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
        # PayPay実課金導線(新チャージ画面)の限定公開フラグ(2026-09-02)。
        # role='admin'は別途フロント側でstate.isAdminから判定済みのため
        # ここではテスト許可リストのみを見る
        # (app/routers/paypay_charge.pyのバックエンド側ガードと同じ判定)。
        "paypay_charge_test_allowed": paypay.is_test_allowed(
            u.get("username", "")),
        # 2026-09-07・一般公開対応: 実際に購入ボタンを表示してよいかどうか
        # (`app/routers/paypay_charge.py`の`_guard_not_yet_public`と同じ
        # `paypay.can_charge`を呼ぶため、表示可否と実際の可否がズレない)。
        # ゲスト(未登録)は常にFalse。
        "can_paypay_charge": can_paypay_charge,
    }


# ---------------------------------------------------------------------------
# バージョン情報 / メンテナンス予定（2026-08-22ユーザー要望）
#
# どちらも「アプリを再起動せずに変えられること」を要件にしている:
#   - リリースノートは data/release_notes.json を置けばそちらが優先される
#     （docker cp で入れるだけ。イメージの作り直し＝再起動が不要）
#   - メンテナンス予定は app_state テーブル（DB）に持つ
# ---------------------------------------------------------------------------

# メンテナンス予定を入れておく app_state のキー。
MAINTENANCE_KEY = "maintenance_plan"

# 定期メンテナンス枠の既定値（2026-08-21のメンテナンス計画で検討した
# 「毎週月曜 日本時間 03:00〜03:30」。ユーザーが画面から変更できる）。
DEFAULT_MAINTENANCE = {
    "regular_enabled": True,
    "regular_weekday": 0,      # 0=月曜（Python の weekday と同じ）
    "regular_start": "03:00",  # JST
    "regular_end": "03:30",    # JST
    "regular_note": "定期メンテナンス枠です。数分程度つながりにくくなる"
                    "ことがあります。",
    # 不定期メンテナンス（1件だけ持つ。予定が無いときは start が空）。
    "adhoc_enabled": False,
    "adhoc_start": "",         # "2026-08-25 03:00" 形式（JST）
    "adhoc_end": "",
    "adhoc_note": "",
    # 臨時メンテナンスの時刻に、VPS側のcron(deploy/scheduled_deploy.sh)で
    # 自動デプロイまで行うか（コードは事前にrsync済みであることが前提）。
    "adhoc_auto_deploy": False,
    # 利用者向けバナーを何時間前から出すか。
    "notice_hours_before": 24,
}

# VPS側の deploy/scheduled_deploy.sh が見張るファイル。data/ は永続ボリューム
# でホストからも見えるので、アプリ（コンテナ内）から予約を書ける。
DEPLOY_REQUEST_FILE = "deploy_request.json"
DEPLOY_LOG_FILE = "deploy_log.jsonl"

_WEEKDAY_JA = ["月", "火", "水", "木", "金", "土", "日"]


def _now_jst():
    from datetime import datetime, timedelta, timezone
    return datetime.now(timezone(timedelta(hours=9)))


def _parse_jst(text: str):
    """「2026-08-25 03:00」「2026-08-25T03:00」をJSTのdatetimeにする。"""
    from datetime import datetime, timedelta, timezone
    t = (text or "").strip().replace("T", " ")
    for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(t, fmt).replace(
                tzinfo=timezone(timedelta(hours=9)))
        except ValueError:
            continue
    return None


def _load_release_notes() -> dict:
    """リリースノートを読む。data/release_notes.json があればそれを優先。

    data/ は永続ボリュームなので、`docker cp` でこのファイルを差し替える
    だけで**コンテナを作り直さずに**掲載内容を更新できる（再起動を減らす
    という2026-08-22の方針）。無ければリポジトリ同梱版を読む。
    """
    for path in (paths.data_dir / "release_notes.json",
                 ROOT_DIR / "release_notes.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(data, dict) and isinstance(data.get("versions"), list):
            return data
    return {"versions": []}


@router.get("/release-notes")
def release_notes():
    """バージョン情報ページの中身。一般ユーザーには public だけ、
    管理者には admin（詳細）も返す。ゲストでも見られる。"""
    from ..config import APP_VERSION
    with db() as conn:
        me = auth.get_user(conn, auth.current_user_id())
    is_admin = bool(me and me.get("role") == "admin")
    out = []
    for v in _load_release_notes().get("versions", []):
        if not isinstance(v, dict):
            continue
        item = {
            "version": v.get("version", ""),
            "date": v.get("date", ""),
            "title": v.get("title", ""),
            "public": [str(x) for x in (v.get("public") or [])],
        }
        if is_admin:
            item["admin"] = [str(x) for x in (v.get("admin") or [])]
        out.append(item)
    return {"current": APP_VERSION, "is_admin": is_admin, "versions": out}


def _load_maintenance() -> dict:
    with db() as conn:
        row = conn.execute(
            "SELECT value FROM app_state WHERE key = ?", (MAINTENANCE_KEY,),
        ).fetchone()
    plan = dict(DEFAULT_MAINTENANCE)
    if row and (row["value"] or "").strip():
        try:
            saved = json.loads(row["value"])
            if isinstance(saved, dict):
                plan.update({k: saved[k] for k in saved if k in plan})
        except ValueError:
            pass
    return plan


def _maintenance_notice(plan: dict) -> dict:
    """いま利用者に出すべきお知らせ（無ければ show=False）。

    - 不定期メンテナンス: 予定の notice_hours_before 時間前から告知し、
      時間帯に入っている間は「作業中」として出し続ける。
    - 定期メンテナンス枠: 毎週のことなので常時は出さず、開始の
      notice_hours_before 時間前になってから出す。
    """
    from datetime import timedelta
    now = _now_jst()
    lead = timedelta(hours=int(plan.get("notice_hours_before") or 0))
    if plan.get("adhoc_enabled"):
        start = _parse_jst(plan.get("adhoc_start", ""))
        end = _parse_jst(plan.get("adhoc_end", ""))
        if start and end is None:
            end = start + timedelta(minutes=30)
        # 完了後6時間は「終了しました」を出し続け、それを過ぎたら消す
        # （2026-08-30ユーザー指示: 終了直後に即消すのではなく、しばらく
        # 完了報告を見せてから消えるようにしたい）。
        if start and now <= end + timedelta(hours=6):
            note = plan.get("adhoc_note") or ""
            if now > end:
                return {
                    "show": True, "state": "completed", "kind": "adhoc",
                    "text": (f"メンテナンスは終了しました"
                             f"（{start:%m/%d %H:%M}〜{end:%H:%M}"
                             f"・日本時間）。ご協力ありがとうございました。"
                             f"{note}"),
                }
            if now >= start:
                return {
                    "show": True, "state": "in_progress", "kind": "adhoc",
                    "text": (f"ただいまメンテナンス作業中です"
                             f"（{start:%m/%d %H:%M}〜{end:%H:%M}"
                             f"・日本時間）。{note}"),
                }
            if now >= start - lead:
                return {
                    "show": True, "state": "upcoming", "kind": "adhoc",
                    "text": (f"メンテナンス予定: {start:%Y/%m/%d %H:%M}〜"
                             f"{end:%H:%M}（日本時間）。{note}"),
                }
    if plan.get("regular_enabled"):
        wd = max(0, min(int(plan.get("regular_weekday") or 0), 6))
        hh, _, mm = (plan.get("regular_start") or "03:00").partition(":")
        try:
            days_ahead = (wd - now.weekday()) % 7
            start = (now + timedelta(days=days_ahead)).replace(
                hour=int(hh), minute=int(mm or 0), second=0, microsecond=0)
        except ValueError:
            return {"show": False}
        if start < now:
            start += timedelta(days=7)
        if now >= start - lead:
            return {
                "show": True, "state": "upcoming", "kind": "regular",
                "text": (f"定期メンテナンス予定: {start:%Y/%m/%d}"
                         f"（{_WEEKDAY_JA[wd]}）{plan.get('regular_start')}〜"
                         f"{plan.get('regular_end')}（日本時間）。"
                         f"{plan.get('regular_note') or ''}"),
            }
    return {"show": False}


@router.get("/maintenance")
def get_maintenance():
    """メンテナンス予定（誰でも取得可・利用者へのお知らせに使う）。"""
    plan = _load_maintenance()
    plan["now_jst"] = _now_jst().strftime("%Y-%m-%d %H:%M")
    plan["notice"] = _maintenance_notice(plan)
    plan["deploy"] = _deploy_status()
    return plan


def _sync_deploy_request(plan: dict) -> None:
    """自動デプロイの予約ファイルを作る/消す（VPSのcronが拾う）。

    アプリのコンテナからは docker コマンドを叩けないので、**予約だけを
    data/ に書き**、実際の入れ替えはホスト側の cron
    (`deploy/scheduled_deploy.sh`) に任せる。予約を消すのは「臨時
    メンテナンスを取り消した／自動デプロイのチェックを外した」とき。
    """
    req = paths.data_dir / DEPLOY_REQUEST_FILE
    want = (bool(plan.get("adhoc_enabled"))
            and bool(plan.get("adhoc_auto_deploy"))
            and bool((plan.get("adhoc_start") or "").strip()))
    try:
        if want:
            req.write_text(json.dumps({
                "run_at": (plan.get("adhoc_start") or "").strip(),
                "note": plan.get("adhoc_note") or "",
                "requested_at": _now_jst().strftime("%Y-%m-%d %H:%M"),
            }, ensure_ascii=False), encoding="utf-8")
        elif req.exists():
            req.unlink()
    except OSError as e:
        log.error("自動デプロイ予約の書き込みに失敗: %s", e)


def _deploy_status() -> dict:
    """自動デプロイの予約状況と直近の実行結果（管理画面の表示用）。"""
    out: dict = {"scheduled": None, "last": None}
    req = paths.data_dir / DEPLOY_REQUEST_FILE
    try:
        if req.exists():
            out["scheduled"] = json.loads(req.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    try:
        lines = (paths.data_dir / DEPLOY_LOG_FILE).read_text(
            encoding="utf-8").strip().splitlines()
        for line in reversed(lines[-50:]):
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if rec.get("status") in (
                    "success", "error", "fatal", "rolled_back"):
                out["last"] = rec
                break
    except OSError:
        pass
    return out


class MaintenanceIn(BaseModel):
    regular_enabled: bool | None = None
    regular_weekday: int | None = None
    regular_start: str | None = None
    regular_end: str | None = None
    regular_note: str | None = None
    adhoc_enabled: bool | None = None
    adhoc_start: str | None = None
    adhoc_end: str | None = None
    adhoc_note: str | None = None
    adhoc_auto_deploy: bool | None = None
    notice_hours_before: int | None = None


@router.put("/maintenance")
def put_maintenance(payload: MaintenanceIn):
    """メンテナンス予定の更新（管理者専用）。DBに書くだけなので
    **アプリの再起動は不要**、保存した瞬間から利用者側に反映される。"""
    _require_admin()
    plan = _load_maintenance()
    for k, v in payload.model_dump(exclude_none=True).items():
        plan[k] = v
    plan["regular_weekday"] = max(0, min(int(plan["regular_weekday"]), 6))
    plan["notice_hours_before"] = max(
        0, min(int(plan["notice_hours_before"]), 24 * 14))
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
            (MAINTENANCE_KEY, json.dumps(plan, ensure_ascii=False)),
        )
    _sync_deploy_request(plan)
    plan["now_jst"] = _now_jst().strftime("%Y-%m-%d %H:%M")
    plan["notice"] = _maintenance_notice(plan)
    plan["deploy"] = _deploy_status()
    return plan


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
            raise errors.http_error("2004", "管理者のみ閲覧できます。")
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
            f"FROM users u WHERE {filter_sql} "
            # ゲスト疑似ユーザー行は実在の利用者ではないので常に除外
            # (2026-09-12・admin_registrants と同じ理由。詳細は
            # _user_filter_sql のdocstring参照)。
            f"AND u.username != '{auth.GUEST_USERNAME}' ORDER BY u.id"
        ).fetchall()
    users = []
    for r in rows:
        # 2026-08-26: 「上限」列がサイト全体の上限(ai_daily_cost_cap_usd)を
        # そのままフォールバック表示していたため、個別未設定ユーザー全員が
        # 同じ巨大な値に見え「これは全体の上限では」と誤解を招いていた
        # （ユーザー指摘）。実際の利用制御(`ai._user_guard`)と同じ
        # `_effective_caps`を使い、role/emailに応じた実効値(100pt/日・
        # admin=1000pt/日・自己サインアップ=0円 等)を表示するよう統一。
        u_for_caps = {
            "email": r["email"], "username": r["username"],
            "role": r["role"],
            "daily_cost_cap_usd": r["dcap"],
            "monthly_cost_cap_usd": r["mcap"],
        }
        dcap, mcap = ai._effective_caps(u_for_caps, s)
        dcap = dcap or None
        mcap = mcap if r["mcap"] is not None else None
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
        raise errors.http_error("3005", "1回の変更額は ¥1〜¥10,000（減額は-¥10,000〜-¥1）です。")
    if not note:
        raise errors.http_error("3006", "理由(note)の入力は必須です。")
    with db() as conn:
        me = auth.get_user(conn, auth.current_user_id())
        if not me or me.get("role") != "admin":
            raise errors.http_error("2004", "管理者のみ操作できます。")
        target = auth.get_user(conn, payload.user_id)
        if not target:
            raise errors.http_error("7001", "ユーザーが見つかりません。")
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
            raise errors.http_error("2004", "管理者のみ操作できます。")
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
            raise errors.http_error("2004", "管理者のみ操作できます。")
        target = auth.get_user(conn, payload.user_id)
        if not target:
            raise errors.http_error("7001", "ユーザーが見つかりません。")
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


@router.get("/admin/anon-access")
def admin_anon_access(days: int = 30, limit: int = 500):
    """未ログイン(未登録)訪問者のアクセス状況（IP単位・2026-08-20
    ユーザー要望）。landing_visits(トップ/about.htmlの閲覧・新規登録の
    試行成否)を集計し、ip_geo_cache(国/地域/市区/接続元組織名・
    scripts不要でリクエスト時にバックグラウンド収集済みのものを読むだけ)
    と突き合わせて返す。端末・ブラウザ(iPad/Android/Windows/Mac、
    Chrome/Safari/Edge等)はlanding_visitsに記録済みのUser-Agentを
    ua_parse.summarize()で解析して付与する(2026-08-23ユーザー要望・
    IPからの国/組織解析に加えて端末種別も分かるように)。

    注意（IP単位の限界）: 同一Wi-Fi/会社等でIPを共有する複数人は1行に
    まとまり、逆に同じ人がモバイル回線切替等でIPが変われば複数行に
    分かれる。真の「端末単位」には別途トラッキングCookieの導入が必要
    （プライバシーポリシーの更新を伴うため未実装・必要なら別途検討）。"""
    _require_admin()
    days = max(1, min(days, 365))
    limit = max(1, min(limit, 2000))
    since = f"-{days} days"
    with db() as conn:
        rows = conn.execute(
            "SELECT ip, "
            " MIN(created_at) AS first_seen, MAX(created_at) AS last_seen, "
            " SUM(CASE WHEN kind='visit' THEN 1 ELSE 0 END) AS visit_count, "
            " MAX(CASE WHEN kind='visit' AND path='/static/about.html' "
            "      THEN 1 ELSE 0 END) AS viewed_about, "
            " MAX(CASE WHEN kind='signup' THEN 1 ELSE 0 END) "
            "     AS signup_attempted, "
            " MAX(CASE WHEN kind='signup' AND success=1 THEN 1 ELSE 0 END) "
            "     AS signup_succeeded, "
            " MAX(CASE WHEN accept_language != '' THEN accept_language "
            "     END) AS accept_language, "
            # 2026-09-19: そのIPの全行が内部Cookie(自分の端末)由来なら
            # 管理者(※1)扱いにする(ADMIN_KNOWN_IPSはIPが変わると効かない)。
            " MIN(is_internal) AS all_internal "
            "FROM landing_visits "
            "WHERE created_at >= datetime('now', ?) AND ip != '' "
            "GROUP BY ip ORDER BY last_seen DESC",
            (since,),
        ).fetchall()
        geo_rows = conn.execute(
            "SELECT ip, country, region, city, org, hostname "
            "FROM ip_geo_cache",
        ).fetchall()
        # 「英単語ページを開いたか」「音声再生を試みたか」(2026-09-13
        # ユーザー要望・登録ファネル同様の2シグナルをIP単位の明細にも追加)。
        # usage_eventsはip列を持つのでguest_sid無しでもIP単位に集計できる。
        usage_rows = conn.execute(
            "SELECT ip, "
            " MAX(CASE WHEN kind='page' AND category='word_detail' "
            "     THEN 1 ELSE 0 END) AS viewed_word, "
            " MAX(CASE WHEN kind='play' AND category='word' "
            "     THEN 1 ELSE 0 END) AS tried_audio "
            "FROM usage_events "
            "WHERE created_at >= datetime('now', ?) AND ip != '' "
            "GROUP BY ip",
            (since,),
        ).fetchall()
        # 訪問者種別(※1〜※4)の判定材料。1つのIPが複数のUAを名乗ることが
        # あるので DISTINCT で全部拾う（GROUP_CONCATはUA中のカンマで
        # 壊れるので使わない）。
        ua_rows = conn.execute(
            "SELECT DISTINCT ip, user_agent FROM landing_visits "
            "WHERE created_at >= datetime('now', ?) AND ip != ''",
            (since,),
        ).fetchall()
        summary = conn.execute(
            "SELECT COUNT(*) AS total_visits, COUNT(DISTINCT ip) AS "
            "unique_ips FROM landing_visits "
            "WHERE kind='visit' AND created_at >= datetime('now', ?)",
            (since,),
        ).fetchone()

    geo_map = {r["ip"]: dict(r) for r in geo_rows}
    ua_map: dict[str, list[str]] = {}
    for r in ua_rows:
        ua_map.setdefault(r["ip"], []).append(r["user_agent"] or "")
    usage_map = {r["ip"]: dict(r) for r in usage_rows}
    admin_ips = load_admin_known_ips()
    items = []
    # 印ごとのIP数と延べアクセス回数。画面先頭の「総数」に使うので、
    # 表示件数(limit)で切る前の**期間内の全IP**を数える（2026-08-22:
    # フィルタや表示件数に関わらず総数が変わらないこと、というユーザー要望）。
    mark_counts = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    mark_visits = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    for r in rows:
        d = dict(r)
        geo = geo_map.get(d["ip"], {})
        d["country"] = geo.get("country", "")
        d["region"] = geo.get("region", "")
        d["city"] = geo.get("city", "")
        d["org"] = geo.get("org", "")
        d["hostname"] = geo.get("hostname", "")
        d["is_admin"] = d["ip"] in admin_ips or bool(d.pop("all_internal", 0))
        # ※1〜※4 の推定（印なし=0＝人間が意識的に閲覧したとみなす）。
        d["mark"], d["mark_reason"] = visitor_kind.classify(
            ua_map.get(d["ip"], []), d["org"], d["hostname"], d["is_admin"],
        )
        # 端末・ブラウザ（2026-08-23・IPからの国/組織解析に加えて
        # 「iPad/Android/Windows/Macが分かるといい」という要望対応）。
        d["device"], d["browser"] = ua_parse.summarize(ua_map.get(d["ip"], []))
        usage = usage_map.get(d["ip"], {})
        d["viewed_word"] = usage.get("viewed_word", 0)
        d["tried_audio"] = usage.get("tried_audio", 0)
        mark_counts[d["mark"]] += 1
        mark_visits[d["mark"]] += d["visit_count"] or 0
        items.append(d)
    # 集計は期間内の全IPで行い、表示だけ limit で切る。
    items = items[:limit]

    return {
        "days": days,
        "total_visits": summary["total_visits"] if summary else 0,
        "unique_ips": summary["unique_ips"] if summary else 0,
        # 印ごとのIP数。0=印なし(人間とみなすもの)。画面のサマリで使う。
        "mark_counts": {str(k): v for k, v in mark_counts.items()},
        # 印ごとの延べアクセス回数（IP数だけだと、管理者自身の大量アクセスの
        # ような偏りが見えないため・2026-08-22ユーザー要望）。
        "mark_visits": {str(k): v for k, v in mark_visits.items()},
        "items": items,
    }


def _funnel_exclusions(conn, since: str):
    """登録ファネル・訪問推移の分母から除外するguest_sidを洗い出す
    （2026-09-19・計測設計3-D。従来admin_registration_funnelだけが持って
    いたUA単体のボット判定を切り出し、内部端末の除外を加えた）。

    戻り値: (ua_by_guest, bot_guests, internal_guests)
    - ua_by_guest: visit行の代表UA（端末/ブラウザ内訳用・判定には使わない）
    - bot_guests: UAがvisitor_kind.classify_uaで機械的と判定されたもの、
      または記録時のbot_markが立っているもの。visitを経由せずsignupへ直行
      したアクセスのUAも見る（2026-09-16修正の継承）。
    - internal_guests: 自分(管理者/テスト)の端末。内部Cookie由来の
      is_internal=1の行を持つもの＋管理者/テストアカウントでログインした
      ことのある端末(_own_device_sids)。従来のファネルは管理者IP・
      own端末の除外を一切していなかった。"""
    ua_by_guest: dict[str, str] = {}
    for r in conn.execute(
        "SELECT guest_sid, user_agent FROM landing_visits "
        "WHERE guest_sid != '' AND kind='visit' "
        "AND created_at >= datetime('now', ?)", (since,),
    ).fetchall():
        ua_by_guest.setdefault(r["guest_sid"], r["user_agent"] or "")
    # ボット判定用には、visitを経由せずsignupへ直行したアクセスのUAも
    # 合わせて見る(2026-09-16修正)。「訪問」段階の端末/ブラウザ内訳は
    # visit経由のua_by_guestのまま使うため、判定専用の別dictに分ける。
    ua_for_bot_check = dict(ua_by_guest)
    for r in conn.execute(
        "SELECT guest_sid, user_agent FROM landing_visits "
        "WHERE guest_sid != '' AND kind='signup' "
        "AND created_at >= datetime('now', ?)", (since,),
    ).fetchall():
        ua_for_bot_check.setdefault(r["guest_sid"], r["user_agent"] or "")
    bot_guests = {
        g for g, ua in ua_for_bot_check.items()
        if visitor_kind.classify_ua(ua)[0] != visitor_kind.MARK_NONE
    }
    # 記録時のbot_mark(新データのみ・旧行は0)。UA判定の方が最新のリストで
    # 見直せる分だけ広いが、リスト改訂で判定が変わった場合にも「記録時に
    # 機械的と判断していたもの」は除外し続ける。
    bot_guests |= {
        r["guest_sid"] for r in conn.execute(
            "SELECT DISTINCT guest_sid FROM landing_visits "
            "WHERE guest_sid != '' AND bot_mark != 0 "
            "AND created_at >= datetime('now', ?)", (since,),
        ).fetchall()
    }
    internal_guests = {
        r["guest_sid"] for r in conn.execute(
            "SELECT guest_sid FROM landing_visits "
            "WHERE guest_sid != '' AND is_internal = 1 "
            "AND created_at >= datetime('now', ?) "
            "UNION SELECT guest_sid FROM usage_events "
            "WHERE guest_sid != '' AND is_internal = 1 "
            "AND created_at >= datetime('now', ?)", (since, since),
        ).fetchall()
    }
    internal_guests |= set(_own_device_sids(conn))
    return ua_by_guest, bot_guests, internal_guests


def _load_excluded_guests(conn, sids: set[str]) -> str:
    """除外guest_sidを接続内のTEMPテーブルに載せ、WHERE句に足すSQL断片を
    返す。`NOT IN (?,?,...)`をそのまま並べると、Cookieを返さないボットが
    毎回別guest_sidになる分(SEOページ記録の追加で増える)で変数上限に
    当たりうるため。TEMPテーブルは接続(=リクエスト)限りで消える。"""
    conn.execute(
        "CREATE TEMP TABLE IF NOT EXISTS excl_guests "
        "(guest_sid TEXT PRIMARY KEY)")
    conn.execute("DELETE FROM temp.excl_guests")
    conn.executemany(
        "INSERT OR IGNORE INTO temp.excl_guests (guest_sid) VALUES (?)",
        [(g,) for g in sids])
    return " AND guest_sid NOT IN (SELECT guest_sid FROM temp.excl_guests)"


def _median(values: list[float]) -> float | None:
    if not values:
        return None
    v = sorted(values)
    n = len(v)
    return round(v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2, 1)


def _percentile(values: list[float], pct: float) -> float | None:
    if not values:
        return None
    v = sorted(values)
    return round(v[min(len(v) - 1, int(len(v) * pct))], 1)


@router.get("/admin/registration-funnel")
def admin_registration_funnel(days: int = 30):
    """登録に至らない原因分析(常設・2026-08-30)。未登録訪問者を1人ずつ
    区別するguest_sid Cookie(app/main.pyの_auth_contextミドルウェアで
    発行)を使い、訪問→about確認→登録試行→登録完了の各段階のユニーク
    guest_sid数を集計する。加えて「訪問はしたが登録を試みなかった」
    guest_sidについて、最後に触れていた画面(usage_events.category)を
    集計し離脱ポイントの見当をつける。既存のadmin_anon_access(IP単位)は
    guest_sid導入前のデータも見られるよう残したまま、こちらは導入後の
    正確な人単位集計を担う。

    **2026-09-07追記(ユーザー指摘「登録試行がほぼ無いのはなぜか」への
    調査対応)**: 従来はボット除外を一切行っておらず(admin_visit_trend等
    兄弟エンドポイントはvisitor_kind.classify()でボット除外済みなのに
    ここだけ漏れていた)、curl/HeadlessChrome等の機械的アクセスが素通り
    して分母(訪問数)を水増ししていた。UA単体判定のclassify_ua()で
    guest_sid単位のボット判定を行い、全段階の集計から除外する
    (IP単位のclassify()と違いip_geo_cache/管理者IP照合は行わない簡易
    判定だが、UAが無い/curl等の明白なボットは十分検出できる)。
    あわせて「訪問」段階の端末/ブラウザ内訳(ua_parse.parse_ua)も返す。

    **2026-09-19(計測設計フェーズ1 3-D/3-A/3-B)**:
    - 自分(管理者/テストの端末・内部Cookie)も分母から除外する
      (`_funnel_exclusions`)。
    - 「訪問」の次に「JS到達」段(インラインビーコン`boot/html`が届いた
      guest_sid)を追加。従来の「91%が無操作」は「JS未到達」と「見て
      興味なし」が区別できなかった。あわせて『人間訪問(基準)』=HTML着地
      のうちJS到達あり、または同一guest_sidで2回以上の閲覧、を返す
      (Cookieを返さないクライアントは毎回別guest_sidになるため1回きり
      になり、ここで落ちる)。JS到達の記録は本機能のリリース以降のデータ
      のみ(それ以前の期間は0)。
    - 流入元別の内訳(`by_channel`など): guest_sidごとの**初回**の
      visit行のreferrerホスト/utm/gclid有無/着地パスから、チャネル
      (広告/検索/SNS/LLM/サイト内/直接/その他)を判定して集計する。"""
    _require_admin()
    days = max(1, min(days, 365))
    since = f"-{days} days"
    with db() as conn:
        ua_by_guest, bot_guests, internal_guests = _funnel_exclusions(
            conn, since)
        excl = _load_excluded_guests(conn, bot_guests | internal_guests)

        def count_distinct_guest(where_sql: str) -> int:
            row = conn.execute(
                "SELECT COUNT(DISTINCT guest_sid) AS c FROM landing_visits "
                f"WHERE guest_sid != '' AND created_at >= datetime('now', ?) "
                f"AND {where_sql}{excl}",
                (since,),
            ).fetchone()
            return row["c"]

        def count_distinct_guest_usage(where_sql: str) -> int:
            """`count_distinct_guest`と同じ判定をusage_events向けに行う版
            (2026-09-13新設: 「英単語のページをみた」「音声再生を試みた」の
            ファネル追加ステップ用。usage_eventsはtracking.log_eventが
            page/play/click等を記録するテーブルで、landing_visitsとは別)。"""
            row = conn.execute(
                "SELECT COUNT(DISTINCT guest_sid) AS c FROM usage_events "
                f"WHERE guest_sid != '' AND created_at >= datetime('now', ?) "
                f"AND {where_sql}{excl}",
                (since,),
            ).fetchone()
            return row["c"]

        def guest_set(table: str, where_sql: str) -> set[str]:
            return {r["guest_sid"] for r in conn.execute(
                f"SELECT DISTINCT guest_sid FROM {table} "
                f"WHERE guest_sid != '' AND created_at >= datetime('now', ?) "
                f"AND {where_sql}{excl}", (since,),
            ).fetchall()}

        visited = count_distinct_guest("kind='visit'")
        viewed_word = count_distinct_guest_usage(
            "kind='page' AND category='word_detail'")
        tried_audio = count_distinct_guest_usage(
            "kind='play' AND category='word'")
        viewed_about = count_distinct_guest(
            "kind='visit' AND path='/static/about.html'")
        signup_attempted = count_distinct_guest("kind='signup'")
        signup_succeeded = count_distinct_guest(
            "kind='signup' AND success=1")

        # --- JS到達・人間訪問(2026-09-19) ---
        # 訪問した(HTML着地の)guest_sidと、その閲覧回数。
        visit_counts = {r["guest_sid"]: r["c"] for r in conn.execute(
            "SELECT guest_sid, COUNT(*) AS c FROM landing_visits "
            "WHERE guest_sid != '' AND kind='visit' "
            f"AND created_at >= datetime('now', ?){excl} "
            "GROUP BY guest_sid", (since,),
        ).fetchall()}
        visited_set = set(visit_counts)
        boot_set = guest_set("usage_events", "kind='boot' AND category='html'")
        ready_set = guest_set(
            "usage_events", "kind='boot' AND category='app_ready'")
        js_reached = len(boot_set & visited_set)
        app_ready = len(ready_set & visited_set)
        human_set = visited_set & (
            boot_set | {g for g, c in visit_counts.items() if c >= 2})
        # 意図的な操作(ボタン押下・再生・ようこそ以外の画面遷移)が1つでも
        # あったguest_sid。boot/leave/app_readyやwelcome表示は含めない。
        engaged_set = guest_set(
            "usage_events",
            "(kind IN ('click','play','word_domain','phrase_scene') "
            "OR (kind='page' AND category != 'welcome'))")
        signup_attempted_set = guest_set("landing_visits", "kind='signup'")
        signup_succeeded_set = guest_set(
            "landing_visits", "kind='signup' AND success=1")
        # 表示速度(ms)の分布: HTML到達(boot/html)と初期表示完了(app_ready)。
        html_ms = [r["value"] for r in conn.execute(
            "SELECT value FROM usage_events WHERE kind='boot' "
            "AND category='html' AND value IS NOT NULL "
            f"AND created_at >= datetime('now', ?){excl}", (since,),
        ).fetchall()]
        ready_ms = [r["value"] for r in conn.execute(
            "SELECT value FROM usage_events WHERE kind='boot' "
            "AND category='app_ready' AND value IS NOT NULL "
            f"AND created_at >= datetime('now', ?){excl}", (since,),
        ).fetchall()]

        # --- 流入元(初回のvisit行から) ---
        first_visit: dict[str, dict] = {}
        seo_guests: set[str] = set()   # 用語集等のSEOページに着地した人
        app_guests: set[str] = set()   # アプリ/その他ページにも来た人
        for r in conn.execute(
            "SELECT guest_sid, referrer_host, utm_source, utm_medium, "
            "utm_campaign, has_gclid, path, landing_path FROM landing_visits "
            "WHERE guest_sid != '' AND kind='visit' "
            f"AND created_at >= datetime('now', ?){excl} ORDER BY id",
            (since,),
        ).fetchall():
            g = r["guest_sid"]
            first_visit.setdefault(g, dict(r))
            if traffic_source.is_seo_path(r["path"]):
                seo_guests.add(g)
            else:
                app_guests.add(g)

        # 「訪問」段階(人間判定分のみ)の端末/ブラウザ内訳。
        device_counts: dict[tuple[str, str], int] = {}
        for g, ua in ua_by_guest.items():
            if g in bot_guests or g in internal_guests:
                continue
            device, browser = ua_parse.parse_ua(ua)
            key = (device, browser)
            device_counts[key] = device_counts.get(key, 0) + 1
        device_breakdown = sorted(
            [{"device": d, "browser": b, "count": c}
             for (d, b), c in device_counts.items()],
            key=lambda x: -x["count"],
        )

        # 離脱ポイント: boot/leave/app_readyは「操作」ではないので、最後の
        # 画面の判定からは外す(外さないと全員の最終イベントが離脱ビーコン
        # になってしまう)。
        dropoff_rows = conn.execute(
            "SELECT ue.guest_sid, ue.category, ue.created_at "
            "FROM usage_events ue "
            "WHERE ue.guest_sid != '' "
            "AND ue.kind NOT IN ('boot', 'leave') "
            "AND ue.created_at >= datetime('now', ?) "
            "AND ue.guest_sid IN ("
            "  SELECT guest_sid FROM landing_visits WHERE kind='visit' "
            "  AND guest_sid != '' AND created_at >= datetime('now', ?)"
            ") "
            "AND ue.guest_sid NOT IN ("
            "  SELECT guest_sid FROM landing_visits WHERE kind='signup' "
            "  AND guest_sid != '' AND created_at >= datetime('now', ?)"
            ") AND ue.guest_sid NOT IN "
            "(SELECT guest_sid FROM temp.excl_guests) "
            "ORDER BY ue.guest_sid, ue.created_at",
            (since, since, since),
        ).fetchall()

        # 登録試行の失敗理由内訳(2026-09-07・ユーザー要望「失敗理由を
        # 多角的に評価したい」)。fail_reasonはapp/services/errors.pyの
        # エラーコード(2026-09-07以前のデータは列が無いため空文字)。
        fail_reason_rows = conn.execute(
            "SELECT fail_reason, COUNT(*) AS c FROM landing_visits "
            "WHERE kind='signup' AND success=0 AND guest_sid != '' "
            f"AND created_at >= datetime('now', ?){excl} "
            "GROUP BY fail_reason ORDER BY c DESC",
            (since,),
        ).fetchall()
        fail_reasons = [{
            "code": r["fail_reason"] or "(不明・旧データ)",
            "label": errors.ERROR_CODES.get(
                r["fail_reason"], (r["fail_reason"] or "不明", 0))[0],
            "count": r["c"],
        } for r in fail_reason_rows]

        # 使い捨てメールドメイン使用の内訳(2026-09-07・以前はここで登録を
        # ブロックしていたが、正規利用者を弾く弊害の方が大きいと判断し
        # 許可制に変更。今後も悪用が増えていないか監視できるよう、
        # 成功/失敗別の件数を出す)。
        disposable_rows = conn.execute(
            "SELECT success, COUNT(*) AS c FROM landing_visits "
            "WHERE kind='signup' AND is_disposable_email=1 "
            f"AND guest_sid != '' AND created_at >= datetime('now', ?){excl} "
            "GROUP BY success",
            (since,),
        ).fetchall()
        disposable_email_stats = {
            "succeeded": next(
                (r["c"] for r in disposable_rows if r["success"] == 1), 0),
            "failed_other_reason": next(
                (r["c"] for r in disposable_rows if r["success"] == 0), 0),
        }
    # guest_sidごとに最後のイベントだけ残す(created_at昇順で走査して
    # 上書きしていくため、最後に残った値が最新になる)。
    last_event: dict[str, dict] = {}
    for r in dropoff_rows:
        last_event[r["guest_sid"]] = {
            "category": r["category"], "created_at": r["created_at"],
        }
    dropoff_sessions = sorted(
        [{"guest_sid": g, **v} for g, v in last_event.items()],
        key=lambda x: x["created_at"], reverse=True,
    )[:200]
    dropoff_counts: dict[str, int] = {}
    for v in last_event.values():
        key = v["category"] or "(不明)"
        dropoff_counts[key] = dropoff_counts.get(key, 0) + 1
    dropoff_summary = sorted(
        [{"category": k, "count": v} for k, v in dropoff_counts.items()],
        key=lambda x: -x["count"],
    )

    def rate(n: int, d: int) -> float:
        return round(n / d * 100, 1) if d else 0.0

    stages = [
        {"key": "visited", "label": "訪問(HTML着地)", "count": visited},
        {"key": "js_reached", "label": "JS到達(表示ビーコン受信)",
         "count": js_reached},
        {"key": "viewed_word", "label": "英単語のページをみた",
         "count": viewed_word},
        {"key": "tried_audio", "label": "音声再生を試みた",
         "count": tried_audio},
        {"key": "viewed_about", "label": "「このアプリについて」を確認",
         "count": viewed_about},
        {"key": "signup_attempted", "label": "登録を試みた",
         "count": signup_attempted},
        {"key": "signup_succeeded", "label": "登録完了",
         "count": signup_succeeded},
    ]
    human_visited = len(human_set)
    for i, s in enumerate(stages):
        prev = stages[i - 1]["count"] if i > 0 else visited
        s["rate_from_start"] = rate(s["count"], visited)
        s["rate_from_prev"] = rate(s["count"], prev) if i > 0 else 100.0
        # 人間訪問(基準)に対する比。JS到達の記録が無い期間(リリース前)は
        # human_visitedが小さくなるため、比が100%超になりうる点は画面の
        # 注記で読み手に伝える。
        s["rate_from_human"] = rate(s["count"], human_visited)

    # チャネル別・着地ページ別の内訳(guest_sidの初回visit行が基準)。
    def _blank() -> dict:
        return {"visited": 0, "human": 0, "js_reached": 0, "engaged": 0,
                "signup_attempted": 0, "signup_succeeded": 0}

    def _tally(bucket: dict, g: str) -> None:
        bucket["visited"] += 1
        if g in human_set:
            bucket["human"] += 1
        if g in boot_set:
            bucket["js_reached"] += 1
        if g in engaged_set:
            bucket["engaged"] += 1
        if g in signup_attempted_set:
            bucket["signup_attempted"] += 1
        if g in signup_succeeded_set:
            bucket["signup_succeeded"] += 1

    channel_buckets: dict[str, dict] = {}
    landing_buckets: dict[str, dict] = {}
    referrer_counts: dict[str, int] = {}
    utm_counts: dict[str, int] = {}
    ad_click_guests = 0
    for g, fv in first_visit.items():
        # landing_pathが空の行は流入元の記録を始める前(旧データ)。参照元
        # なしの「直接」と区別するため別枠にする。
        if not fv["landing_path"]:
            channel = "unknown"
        else:
            channel = traffic_source.classify_channel(
                fv["referrer_host"], fv["utm_source"], fv["utm_medium"],
                fv["has_gclid"])
        _tally(channel_buckets.setdefault(channel, _blank()), g)
        _tally(landing_buckets.setdefault(
            traffic_source.landing_group(fv["path"]), _blank()), g)
        if fv["referrer_host"]:
            referrer_counts[fv["referrer_host"]] = (
                referrer_counts.get(fv["referrer_host"], 0) + 1)
        if fv["utm_source"] or fv["utm_medium"] or fv["utm_campaign"]:
            k = " / ".join([
                fv["utm_source"] or "-", fv["utm_medium"] or "-",
                fv["utm_campaign"] or "-"])
            utm_counts[k] = utm_counts.get(k, 0) + 1
        if fv["has_gclid"]:
            ad_click_guests += 1

    channel_order = [k for k, _ in traffic_source.CHANNELS] + ["unknown"]
    by_channel = [
        {"key": k, "label": traffic_source.CHANNEL_LABELS.get(
            k, "計測開始前のデータ(流入元不明)"), **channel_buckets[k]}
        for k in channel_order if k in channel_buckets
    ]
    by_landing = sorted(
        [{"label": k, **v} for k, v in landing_buckets.items()],
        key=lambda x: -x["visited"])
    return {
        "days": days, "stages": stages,
        "dropoff_summary": dropoff_summary,
        "dropoff_sessions": dropoff_sessions,
        "bot_excluded": len(bot_guests),
        "internal_excluded": len(internal_guests - bot_guests),
        "device_breakdown": device_breakdown,
        "fail_reasons": fail_reasons,
        "disposable_email_stats": disposable_email_stats,
        # --- 2026-09-19追加 ---
        "human_visited": human_visited,
        "js_reached": js_reached,
        "app_ready": app_ready,
        "js_timing": {
            "html_ms_median": _median(html_ms),
            "html_ms_p90": _percentile(html_ms, 0.9),
            "ready_ms_median": _median(ready_ms),
            "ready_ms_p90": _percentile(ready_ms, 0.9),
        },
        "by_channel": by_channel,
        "by_landing": by_landing,
        "top_referrers": sorted(
            [{"host": k, "count": v} for k, v in referrer_counts.items()],
            key=lambda x: -x["count"])[:15],
        "utm_breakdown": sorted(
            [{"label": k, "count": v} for k, v in utm_counts.items()],
            key=lambda x: -x["count"])[:15],
        "ad_click_visitors": ad_click_guests,
        # 用語集/フレーズ集/クロスワード紹介(SEOページ)に着地し、その後
        # アプリやその他のページにも来た人＝「SEOページ経由でアプリへ」。
        "via_seo": {
            "seo_landed": len(seo_guests),
            "seo_then_app": len(seo_guests & app_guests),
        },
    }


@router.get("/admin/registration-funnel/guest/{guest_sid}")
def admin_registration_funnel_guest(guest_sid: str):
    """1人ぶんの行動ログ(landing_visits+usage_events)を時系列マージして
    返す(ファネル一覧からのドリルダウン用・「詳細に分析できるように」
    というユーザー要望対応)。"""
    _require_admin()
    with db() as conn:
        # 2026-09-19: 流入元(referrerホスト/utm/広告クリックの有無)・登録
        # 成功行のuser_id・ビーコンの数値(value)も返す(計測設計3-A/3-B/3-M)。
        lv = conn.execute(
            "SELECT 'landing_visits' AS src, kind, path, success, "
            "user_agent, referrer_host, utm_source, utm_medium, "
            "utm_campaign, has_gclid, is_internal, user_id, created_at "
            "FROM landing_visits "
            "WHERE guest_sid = ? ORDER BY created_at", (guest_sid,),
        ).fetchall()
        ue = conn.execute(
            "SELECT 'usage_events' AS src, kind, category, label, value, "
            "is_internal, created_at FROM usage_events "
            "WHERE guest_sid = ? ORDER BY created_at", (guest_sid,),
        ).fetchall()
    timeline = sorted(
        [dict(r) for r in lv] + [dict(r) for r in ue],
        key=lambda r: r["created_at"],
    )
    return {"guest_sid": guest_sid, "timeline": timeline}


@router.get("/admin/visit-trend")
def admin_visit_trend(days: int = 30):
    """訪問者数の推移（人間/クローラー別・延べ数とユニークIP数、日次・
    2026-08-24ユーザー要望「昔の訪問者カウンターに相当するものが欲しい・
    1週間/1ヶ月/3ヶ月/6ヶ月の推移を表とグラフで見たい」）。

    集計対象は landing_visits(kind='visit')。usage_events は画面遷移
    のたびのAPI呼び出しも含み「訪問」の実感と乖離するため、ページを開く
    たび1回だけ記録される landing_visits の方を採用した。人間/クローラー
    の判定は「未登録アクセス状況」(admin_anon_access)と同じ
    visitor_kind.classify() を使い、判定基準を統一する。管理者自身の
    アクセス(ADMIN_KNOWN_IPS)は訪問者数から除外する。

    2026-09-19(計測設計3-D/3-B): 内部Cookie(自分の端末)由来の行も除外
    (is_internal=1)。系列に「JS到達」(インラインビーコンboot/htmlが届いた
    guest_sidの日別ユニーク数・ボット/内部端末を除く)を追加した。JS到達は
    このリリース以降の日付にしか値が入らない。"""
    _require_admin()
    days = max(1, min(days, 366))
    since = f"-{days} days"
    with db() as conn:
        rows = conn.execute(
            "SELECT ip, user_agent, "
            "substr(datetime(created_at, '+9 hours'), 1, 10) AS date "
            "FROM landing_visits "
            "WHERE kind='visit' AND created_at >= datetime('now', ?) "
            "AND ip != '' AND is_internal = 0",
            (since,),
        ).fetchall()
        geo_rows = conn.execute(
            "SELECT ip, org, hostname FROM ip_geo_cache",
        ).fetchall()
        _, bot_guests, internal_guests = _funnel_exclusions(conn, since)
        js_rows = conn.execute(
            "SELECT guest_sid, "
            "substr(datetime(created_at, '+9 hours'), 1, 10) AS date "
            "FROM usage_events WHERE kind='boot' AND category='html' "
            "AND guest_sid != '' AND is_internal = 0 "
            "AND created_at >= datetime('now', ?)",
            (since,),
        ).fetchall()
    geo_map = {r["ip"]: dict(r) for r in geo_rows}
    admin_ips = load_admin_known_ips()

    ua_map: dict[str, list[str]] = {}
    for r in rows:
        ua_map.setdefault(r["ip"], []).append(r["user_agent"] or "")
    mark_cache: dict[str, int] = {}

    def ip_mark(ip: str) -> int:
        if ip not in mark_cache:
            geo = geo_map.get(ip, {})
            mark, _ = visitor_kind.classify(
                ua_map.get(ip, []), geo.get("org", ""),
                geo.get("hostname", ""), ip in admin_ips,
            )
            mark_cache[ip] = mark
        return mark_cache[ip]

    by_day: dict[str, dict] = {}

    def _day(date: str) -> dict:
        return by_day.setdefault(date, {
            "human_total": 0, "human_ips": set(),
            "bot_total": 0, "bot_ips": set(), "js_guests": set(),
        })

    for r in rows:
        mark = ip_mark(r["ip"])
        if mark == visitor_kind.MARK_ADMIN:
            continue
        d = _day(r["date"])
        if mark == visitor_kind.MARK_NONE:
            d["human_total"] += 1
            d["human_ips"].add(r["ip"])
        else:
            d["bot_total"] += 1
            d["bot_ips"].add(r["ip"])
    excluded = bot_guests | internal_guests
    js_all: set[str] = set()
    for r in js_rows:
        if r["guest_sid"] in excluded:
            continue
        _day(r["date"])["js_guests"].add(r["guest_sid"])
        js_all.add(r["guest_sid"])

    daily = []
    for date in sorted(by_day):
        d = by_day[date]
        daily.append({
            "date": date,
            "human_total": d["human_total"],
            "human_unique_ips": len(d["human_ips"]),
            "bot_total": d["bot_total"],
            "bot_unique_ips": len(d["bot_ips"]),
            "js_reached": len(d["js_guests"]),
        })
    # 期間合計のユニークIPは日次の単純合計だと複数日にまたがる同一IPを
    # 重複カウントしてしまうため、別途IP単位で数え直す。
    all_human_ips = {ip for ip in ua_map if ip_mark(ip) == visitor_kind.MARK_NONE}
    all_bot_ips = {
        ip for ip in ua_map
        if ip_mark(ip) not in (visitor_kind.MARK_NONE, visitor_kind.MARK_ADMIN)
    }
    summary = {
        "human_total": sum(d["human_total"] for d in daily),
        "human_unique_ips": len(all_human_ips),
        "bot_total": sum(d["bot_total"] for d in daily),
        "bot_unique_ips": len(all_bot_ips),
        "js_reached": len(js_all),
    }
    return {"days": days, "summary": summary, "daily": daily}


_LOG_LINE_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} (\w+) ")
_LOG_LEVEL_ORDER = {
    "DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50,
}


@router.get("/admin/error-log")
def admin_error_log(lines: int = 200, level: str = "ERROR"):
    """アプリのエラーログ(data/app.log)の末尾を返す（管理画面のログ確認用・
    2026-08-13）。ファイルが無い/空でも空配列を返す（起動直後等）。
    level: "ALL"|"WARNING"|"ERROR"（既定ERROR・2026-09-16追加）。INFO行
    (定期処理の正常ログ等)が大半を占めてエラーが埋もれる問題があった
    ため、既定でWARNING/ERROR/CRITICALのみに絞り込む。トレースバックの
    続き行（タイムスタンプ行頭を持たない行）は直前の判定に従える。"""
    _require_admin()
    lines = max(1, min(lines, 1000))
    path = paths.data_dir / "app.log"
    if not path.exists():
        return {"lines": []}
    with path.open(encoding="utf-8", errors="replace") as f:
        all_lines = [ln.rstrip("\n") for ln in f.readlines()]

    threshold = _LOG_LEVEL_ORDER.get((level or "ALL").upper())
    if threshold is None:
        picked = all_lines
    else:
        picked = []
        keep_current = False
        for ln in all_lines:
            m = _LOG_LINE_RE.match(ln)
            if m:
                keep_current = (
                    _LOG_LEVEL_ORDER.get(m.group(1), 0) >= threshold
                )
            if keep_current:
                picked.append(ln)
    return {"lines": picked[-lines:]}


# 管理概要バナー(2026-09-16・ユーザー要望「登録者が増えた/エラーが
# あった場合にわかりやすく警告を出したい、確認ボタンを押すまで出続けて
# ほしい」)。「確認済み」はapp_state(DB)に時刻で永続化するので、admin
# ページを再読み込みしても・別端末から見ても、確認するまで出続ける。
_ALERT_ACK_KEYS = {
    "registrants": "admin_alert_ack_registrants_at",
    "errors": "admin_alert_ack_errors_at",
}


def _get_alert_ack(conn, kind: str) -> str:
    key = _ALERT_ACK_KEYS[kind]
    row = conn.execute(
        "SELECT value FROM app_state WHERE key = ?", (key,),
    ).fetchone()
    if row and (row["value"] or "").strip():
        return row["value"]
    # 初回はこの機能の導入前からいた既存データを一気に「新着」扱いに
    # しないよう、「今より前は既読」として基準時刻を書き込む。
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
        (key, now),
    )
    return now


def _compute_alerts() -> dict:
    with db() as conn:
        reg_ack = _get_alert_ack(conn, "registrants")
        filter_sql = _user_filter_sql(False, False, False)
        reg_row = conn.execute(
            "SELECT COUNT(*) c, MAX(created_at) latest FROM users u "
            f"WHERE {filter_sql} AND u.username != '{auth.GUEST_USERNAME}' "
            "AND u.created_at > ?",
            (reg_ack,),
        ).fetchone()
        err_ack = _get_alert_ack(conn, "errors")

    err_count = 0
    err_latest: list[str] = []
    path = paths.data_dir / "app.log"
    if path.exists():
        with path.open(encoding="utf-8", errors="replace") as f:
            for ln in f:
                m = _LOG_LINE_RE.match(ln)
                if not m:
                    continue
                if _LOG_LEVEL_ORDER.get(m.group(1), 0) < \
                        _LOG_LEVEL_ORDER["ERROR"]:
                    continue
                if ln[:23] > err_ack:
                    err_count += 1
                    err_latest.append(ln.rstrip("\n"))
    return {
        "registrants": {
            "count": reg_row["c"] or 0, "since": reg_ack,
            "latest_at": reg_row["latest"],
        },
        "errors": {
            "count": err_count, "since": err_ack,
            "latest_lines": err_latest[-5:],
        },
    }


@router.get("/admin/alerts")
def admin_alerts():
    """管理概要バナー用: 前回確認以降の新規登録者数・エラーログ件数。"""
    _require_admin()
    return _compute_alerts()


class AlertAckIn(BaseModel):
    kind: Literal["registrants", "errors"]


@router.post("/admin/alerts/ack")
def admin_alerts_ack(payload: AlertAckIn):
    """バナーの「確認」ボタン用。確認時刻を今に更新し、消えた状態の
    最新集計を返す。"""
    _require_admin()
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    with db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
            (_ALERT_ACK_KEYS[payload.kind], now),
        )
    return _compute_alerts()


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
    # ms等の数値(boot/leaveビーコン用・2026-09-19)。壊れた値でイベント自体
    # を捨てないよう型は緩く受け、tracking._clean_valueで数値化(不正はNULL)。
    value: Any = None


# track_eventが受け付けるkind。音声再生(play)等はサーバー側が実際に処理を
# 返した時点で記録する設計（クライアントが偽装できない）なのでここには
# 入れない。boot/leaveは2026-09-19(計測設計3-B)にJS到達ビーコン用として
# 明示的に追加した。
_CLIENT_TRACK_KINDS = ("page", "click", "boot", "leave")
_TRACK_BODY_MAX = 4096


@router.post("/track")
async def track_event(request: Request):
    """画面表示・ボタン押下のイベント記録（管理画面の利用状況分析用・
    2026-08-17）。音声再生(play)は実際に音声を返した時点でサーバー側
    (learn.pyのtts系エンドポイント)が記録するため、ここでは
    page/click/boot/leaveのみ受け付ける。ゲストも記録対象
    (_GUEST_READ_PREFIXESに追加済み)。記録失敗が画面操作を妨げないよう
    常に200を返すbest-effort。

    2026-09-19(計測設計3-B): navigator.sendBeacon(ページ離脱時にも確実に
    送れる)はContent-Typeがtext/plainになる場合(文字列を渡した時や一部
    ブラウザ)があり、FastAPIのモデル引数のままだと422で捨てられてしまう。
    そのためContent-Typeを問わず本文をJSONとして読み、自前で検証する
    (application/jsonの従来クライアントもそのまま動く)。"""
    try:
        raw = await request.body()
        if len(raw) > _TRACK_BODY_MAX:
            return {"ok": True}
        payload = TrackEventIn(**json.loads(raw.decode("utf-8", "replace")))
    except Exception:
        return {"ok": True}
    if payload.kind in _CLIENT_TRACK_KINDS:
        # log_eventは同期のSQLite書き込みなのでイベントループを塞がない
        # ようスレッドプールで実行する(contextvarsは引き継がれる)。
        await run_in_threadpool(
            tracking.log_event, payload.kind, payload.category,
            payload.label, payload.value)
    return {"ok": True}


class ClientErrorIn(BaseModel):
    kind: str
    message: str = ""
    stack: str = ""
    url: str = ""
    line: int = 0
    col: int = 0


@router.post("/client-error")
def client_error(payload: ClientErrorIn):
    """フロントエンドの未捕捉JS例外・APIエラーの報告(2026-08-20発覚の
    「フロントのエラーがブラウザのコンソールにしか残らずサーバーからは
    見えない」穴への対応・2026-08-30)。static/js/error-report.jsの
    window.onerror/unhandledrejectionに加え、2026-09-18〜
    static/js/api.jsのreq()/stream()が非2xx応答を検知した時にも
    kind="api_error"で送られる(「ボタンでエラーになった」を広く拾う
    ため。401/402/429はゲスト操作等の正常なガードなので送信元で除外
    済み)。ゲストも送信対象(_GUEST_READ_PREFIXESに追加済み)。記録失敗が
    画面操作を妨げないよう常に200を返すbest-effort。"""
    if payload.kind in ("jserror", "unhandledrejection", "api_error"):
        tracking.record_client_error(
            payload.kind, payload.message, payload.stack, payload.url,
            payload.line, payload.col,
        )
    return {"ok": True}


@router.get("/admin/client-error-log")
def admin_client_error_log(days: int = 7, limit: int = 200):
    """フロントエンドJSエラーの一覧(管理画面用)。メッセージでGROUP BYした
    件数・最終発生時刻(よくあるバグを一目で把握する用)と、直近の生ログ
    (詳細調査用)の両方を返す。"""
    _require_admin()
    days = max(1, min(days, 365))
    limit = max(1, min(limit, 1000))
    since = f"-{days} days"
    with db() as conn:
        grouped = conn.execute(
            "SELECT kind, message, COUNT(*) AS cnt, "
            "MAX(created_at) AS last_seen, MIN(created_at) AS first_seen "
            "FROM client_errors WHERE created_at >= datetime('now', ?) "
            "GROUP BY kind, message ORDER BY cnt DESC LIMIT 100",
            (since,),
        ).fetchall()
        recent = conn.execute(
            "SELECT id, user_id, ip, kind, message, stack, url, line, col, "
            "created_at FROM client_errors "
            "WHERE created_at >= datetime('now', ?) "
            "ORDER BY id DESC LIMIT ?",
            (since, limit),
        ).fetchall()
    return {
        "days": days,
        "grouped": [dict(r) for r in grouped],
        "recent": [dict(r) for r in recent],
    }


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
    # 2026-09-19(計測設計3-D): 内部Cookie(自分の端末)由来の行も既定で除外
    # する(管理者/テストを含める指定のときは含める)。ログアウト状態で
    # 動作確認した分やIPが変わった分も、role/is_testのJOINだけでは
    # 落とせなかった。boot/leave(JS到達ビーコン)は「操作」ではないので
    # 件数系から除く。
    ue_internal = (
        "" if (include_admin or include_test) else " AND ue.is_internal = 0")

    def _grouped(conn, kind: str, limit: int = 50) -> list[dict]:
        rows = conn.execute(
            "SELECT category, label, COUNT(*) AS cnt, "
            "COUNT(DISTINCT ip) AS uniq_ip, "
            "COUNT(DISTINCT user_id) AS uniq_user FROM usage_events ue "
            "LEFT JOIN users u ON u.id = ue.user_id "
            "WHERE ue.kind = ? AND ue.created_at >= datetime('now', ?) "
            f"AND {filter_sql}{ue_internal} "
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
            f"AND {filter_sql}{ue_internal} "
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
            f" AND ue.created_at >= datetime('now', ?) AND {filter_sql}"
            f"{ue_internal} "
            "GROUP BY age_group, gender, ue.kind, ue.category "
            "ORDER BY cnt DESC LIMIT 300",
            (since,),
        ).fetchall()

        # 登録時アンケート「このアプリを何で知りましたか」の集計（2026-08-19
        # ・複数選択のためsurvey_referralは", "区切りの文字列。Python側で
        # 分解してから件数を数える）。集計期間はusers.created_atで絞る。
        referral_text_rows = conn.execute(
            "SELECT survey_referral FROM users u "
            "WHERE survey_referral != '' "
            f"AND username != '{auth.GUEST_USERNAME}' "
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
            f"AND {filter_sql}{ue_internal} AND {_UE_ACTION_ONLY_UE} "
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
            f"AND {filter_sql}{ue_internal} "
            "GROUP BY date ORDER BY date",
            (since,),
        ).fetchall()

        # 日別の新規登録数（2026-08-19・ユーザー要望。ゲスト疑似ユーザー
        # は起動時に一度だけ作られる行なので実登録者数を歪めないよう除外
        # 2026-09-12・除外条件が実際のユーザー名'__guest__'ではなく
        # 'guest'という誤った文字列と比較しており機能していなかったのを
        # 修正)。
        signup_rows = conn.execute(
            "SELECT substr(datetime(created_at, '+9 hours'), 1, 10) AS date, "
            "COUNT(*) AS signups FROM users u "
            "WHERE created_at >= datetime('now', ?) "
            f"AND username != '{auth.GUEST_USERNAME}' "
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
            f"AND {filter_sql}{ue_internal} "
            "GROUP BY hour ORDER BY hour",
            (since,),
        ).fetchall()

        total_events = conn.execute(
            "SELECT COUNT(*) FROM usage_events ue "
            "LEFT JOIN users u ON u.id = ue.user_id "
            f"WHERE ue.created_at >= datetime('now', ?) AND {filter_sql}"
            f"{ue_internal} AND {_UE_ACTION_ONLY_UE}",
            (since,),
        ).fetchone()[0]
        # フィルタ無しの総数(2026-09-07追記・ユーザー指摘「1時間に集中
        # している、集計が合っているか確認したい」への対応)。既定
        # (include_admin/invited/test=false)だとほぼ全イベントが除外
        # されるケースがあり(admin自身の操作+email未設定の招待ユーザー
        # だけで実運用では大半を占めていた)、above のtotal_eventsだけ
        # 見ると「ほぼ何も記録されていない」ように誤解されるため、
        # 差分(filtered_out_events)を管理画面に出して気づけるようにする。
        total_events_unfiltered = conn.execute(
            "SELECT COUNT(*) FROM usage_events "
            f"WHERE created_at >= datetime('now', ?) AND {_UE_ACTION_ONLY}",
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
        "filtered_out_events": total_events_unfiltered - total_events,
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


def _top(counter: collections.Counter, n: int = 5) -> list[list]:
    """Counterを[[key, count], ...]の多い順リストに変換する小ヘルパー
    （admin_power_users・admin_guest_ip_analysis共用）。"""
    return [[k, v] for k, v in counter.most_common(n)]


@router.get("/admin/power-users")
def admin_power_users(
    days: int = 90, min_events: int = 5, min_days: int = 2,
    include_admin: bool = False, include_invited: bool = False,
    include_test: bool = False, include_registered: bool = True,
    limit: int = 100,
):
    """複数回・複数日にわたって使ってくれている「お得意様」の深掘り分析
    （管理画面・2026-09-16ユーザー要望「複数回5回以上操作、複数日2日
    以上の方の深掘り分析」）。usage_eventsを人単位でグルーピングする:
    ログイン済みはuser_id、未ログインはguest_sid Cookie（2026-08-30
    導入・それ以前のデータやCookie不可の環境はip単位にフォールバック
    ＝同一IPの複数人が1人として混ざる可能性がある点に注意）。直近
    days日でイベント数min_events件以上・訪問日数(JST日付)min_days日
    以上の利用者を抽出し、各利用者の閲覧タブ・単語の分野・フレーズの
    シーン等の内訳から興味の傾向を返す。

    2026-09-18ユーザー要望「ログイン名がわかるように・登録者/テスト
    ユーザー/管理者を個別に入れる/入れないでフィルタリングしたい」対応:
    ログイン済み利用者はusername(ログイン名)をdisplay_nameと併せて返す。
    include_registered=Falseで「管理者でもテストユーザーでもない、普通の
    登録会員」の行を除外できる（ゲストは常に含む。テスト/管理者は
    include_test/include_adminで別途制御）。"""
    _require_admin()
    days = max(1, min(days, 365))
    min_events = max(1, min_events)
    min_days = max(1, min_days)
    limit = max(1, min(limit, 500))
    filter_sql = _user_filter_sql(include_admin, include_invited,
                                   include_test)

    with db() as conn:
        rows = conn.execute(
            "SELECT ue.user_id AS user_id, ue.guest_sid AS guest_sid, "
            "ue.ip AS ip, ue.kind AS kind, ue.category AS category, "
            "ue.label AS label, ue.created_at AS created_at, "
            "substr(datetime(ue.created_at, '+9 hours'), 1, 10) "
            " AS jst_date, "
            "u.username AS username, u.display_name AS display_name, "
            "u.role AS role, u.is_test AS is_test, "
            "ue.is_internal AS is_internal "
            "FROM usage_events ue LEFT JOIN users u ON u.id = ue.user_id "
            "WHERE ue.created_at >= datetime('now', ?) "
            f"AND {filter_sql} AND {_UE_ACTION_ONLY_UE} "
            "ORDER BY ue.created_at",
            (f"-{days} days",),
        ).fetchall()
        own_sids = _own_device_sids(conn)
    admin_ips = load_admin_known_ips()

    groups: dict[tuple[str, str], dict] = {}
    for r in rows:
        # 2026-09-18修正(Fableレビューで発覚): 未ログインアクセスは
        # user_idがNULLにはならず、全ゲスト共有の疑似ユーザー行
        # (auth.GUEST_USERNAME)のidが入る(_user_filter_sqlの
        # 2026-09-12コメント参照)。`if r["user_id"]:`だけで判定すると
        # 全ゲストがこの1つのuser_idに丸ごと集約されてしまい
        # (guest_sid/ip単位への分岐が実質デッドコード化していた)、
        # 「ゲスト」が常に1行に見えていた原因だった。
        if r["user_id"] and r["username"] != auth.GUEST_USERNAME:
            key = ("user", str(r["user_id"]))
        elif r["is_internal"] and not (include_admin or include_test):
            # 内部Cookie(自分の端末)由来の未ログイン操作(2026-09-19・
            # 計測設計3-D)。_own_device_sidsはログイン履歴のある端末しか
            # 拾えないが、Cookieならログアウト後・新しいguest_sidでも効く。
            continue
        elif r["guest_sid"]:
            key = ("guest", r["guest_sid"])
        elif r["ip"]:
            key = ("ip_legacy", r["ip"])
        else:
            continue
        g = groups.setdefault(key, {
            "events": [], "days": set(),
            "username": r["username"], "display_name": r["display_name"],
            "role": r["role"], "is_test": r["is_test"],
        })
        g["events"].append(r)
        g["days"].add(r["jst_date"])

    items = []
    for (id_type, ident), g in groups.items():
        # 「普通の登録会員」(管理者でもテストユーザーでもない)かどうか。
        # include_registered=Falseの時、このタイプだけを一覧から除外する
        # （テスト/管理者はinclude_test/include_adminで別途制御済み・
        # 既にSQL段階でフィルタされているのでここではidentity_typeが
        # "user"の行=常にその条件を満たしたアカウントである点に注意）。
        is_plain_registered = (
            id_type == "user" and g["role"] != "admin" and not g["is_test"]
        )
        if not include_registered and is_plain_registered:
            continue
        events = g["events"]
        # 管理者/テストアカウントの「端末」(=未ログインで動作確認した分)の
        # 分離(2026-09-19)。アカウントの行はSQL段階(_user_filter_sql)で
        # 既に分離済みなので、ここは未ログイン(guest/旧IP単位)の行が対象。
        # 端末の判定は_own_device_sids(ログイン履歴のあるguest_sid)に加え、
        # 全イベントが管理者の既知IPからのものでも管理者扱いにする。
        is_admin_dev = is_test_dev = False
        if id_type == "guest":
            own = own_sids.get(ident, {})
            is_admin_dev = bool(own.get("admin")) or all(
                e["ip"] in admin_ips for e in events)
            is_test_dev = bool(own.get("test"))
        elif id_type == "ip_legacy":
            is_admin_dev = ident in admin_ips
        if is_admin_dev and not include_admin:
            continue
        if is_test_dev and not include_test:
            continue
        if len(events) < min_events or len(g["days"]) < min_days:
            continue
        tabs: collections.Counter = collections.Counter()
        domains: collections.Counter = collections.Counter()
        scenes: collections.Counter = collections.Counter()
        words: collections.Counter = collections.Counter()
        plays = clicks = 0
        for e in events:
            if e["kind"] == "page" and e["category"] == "word_detail":
                words[e["label"]] += 1
            elif e["kind"] == "page":
                tabs[e["label"] or e["category"]] += 1
            elif e["kind"] == "word_domain":
                domains[e["category"]] += 1
            elif e["kind"] == "phrase_scene":
                scenes[e["category"]] += 1
            elif e["kind"] == "play":
                plays += 1
            elif e["kind"] == "click":
                clicks += 1
        if id_type == "user":
            label = g["display_name"] or g["username"] or f"user#{ident}"
        elif id_type == "guest":
            label = f"ゲスト({ident[:8]})"
        else:
            label = f"IP:{ident}（旧データ・複数人の可能性あり）"
        items.append({
            "identity_type": id_type,
            "identity": ident,
            "label": label,
            # ログイン名(username)を別出しで返す(2026-09-18ユーザー要望・
            # display_nameを設定していると本来のログイン名が分からない
            # ため、表示側で併記できるように)。
            "username": g["username"] if id_type == "user" else None,
            "display_name": g["display_name"] if id_type == "user" else None,
            "is_admin_user": g["role"] == "admin" if id_type == "user"
                else False,
            "is_test_user": bool(g["is_test"]) if id_type == "user"
                else False,
            # 未ログイン行のうち、管理者/テストアカウントの端末と判定した
            # もの(include_admin/include_testで含めた場合の注記用)。
            "is_admin_device": is_admin_dev,
            "is_test_device": is_test_dev,
            "total_events": len(events),
            "distinct_days": len(g["days"]),
            "first_seen": min(e["created_at"] for e in events),
            "last_seen": max(e["created_at"] for e in events),
            "plays": plays,
            "clicks": clicks,
            "top_tabs": _top(tabs),
            "top_word_domains": _top(domains),
            "top_phrase_scenes": _top(scenes),
            "top_words": _top(words, 8),
        })

    items.sort(key=lambda it: (-it["distinct_days"], -it["total_events"]))
    items = items[:limit]

    # 個々を見なくても傾向がわかるよう、対象者全員分の興味分野を合算。
    agg_domains: collections.Counter = collections.Counter()
    agg_scenes: collections.Counter = collections.Counter()
    agg_tabs: collections.Counter = collections.Counter()
    for it in items:
        for k, v in it["top_word_domains"]:
            agg_domains[k] += v
        for k, v in it["top_phrase_scenes"]:
            agg_scenes[k] += v
        for k, v in it["top_tabs"]:
            agg_tabs[k] += v

    return {
        "days": days, "min_events": min_events, "min_days": min_days,
        "count": len(items),
        "summary": {
            "top_word_domains": _top(agg_domains, 10),
            "top_phrase_scenes": _top(agg_scenes, 10),
            "top_tabs": _top(agg_tabs, 10),
        },
        "items": items,
    }


@router.get("/admin/guest-ip-analysis")
def admin_guest_ip_analysis(days: int = 90, min_events: int = 1,
                             include_admin: bool = False,
                             include_test: bool = False,
                             limit: int = 200):
    """ゲスト(未ログイン)利用者をIP単位で深掘り分析する一覧（管理画面
    「ゲストIP別分析」・2026-09-17ユーザー要望「ゲストのIP別に、単語の
    分野・発声の有無・エラーの有無・詳細ボタン押下・例文再生・再生失敗を
    できるだけ細かく分析したい、一覧はクリックで詳細が見えるように」への
    対応）。usage_eventsをip単位でグルーピングし、この一覧では概要だけを
    返す。単語ごとの内訳やエラーメッセージ一覧など詳しい内容は、この
    一覧のipを指定してadmin_guest_ip_detailを呼ぶ（画面側は行クリックで
    遅延取得する想定）。

    注意（IP単位の限界・admin_anon_accessと同じ）: 同一Wi-Fi/会社・モバイル
    回線の共有IP等では複数人が1行に混ざる。guest_sid単位（Cookie）で見たい
    場合はadmin_power_usersを使う。

    include_admin=False(既定)では、管理者の既知IP
    (load_admin_known_ips())からのアクセスを一覧から除外する
    （2026-09-18ユーザー要望「管理者も入れる/入れないをフィルタリング
    したい」対応・管理者自身の動作確認アクセスがゲスト分析のノイズに
    なるため）。

    2026-09-19ユーザー要望「自分のテストアカウントと管理者を分離したい」
    対応: 既知IPだけでは、IPの変わるモバイル回線等で未ログインのまま
    動作確認した分が一般ゲストと区別できなかった。管理者/テストアカウント
    でログインしたことのある端末(guest_sid・_own_device_sids)の未ログイン
    時のイベントも、include_admin/include_test=False(既定)で除外する。
    含めた場合は、該当IPの行にis_admin/is_testの印が付く。"""
    _require_admin()
    days = max(1, min(days, 365))
    min_events = max(1, min_events)
    limit = max(1, min(limit, 1000))
    since = f"-{days} days"

    with db() as conn:
        # 2026-09-18修正(Fableレビューで発覚): 未ログインアクセスの
        # user_idはNULLではなく、全ゲスト共有の疑似ユーザー行
        # (auth.GUEST_USERNAME)のid。`user_id IS NULL`では1件もヒット
        # せず一覧が常に空になっていた(_user_filter_sqlの2026-09-12
        # コメント・admin_power_usersの同型バグと同じ原因)。
        guest_uid = auth.ensure_guest_user_id(conn)
        rows = conn.execute(
            "SELECT ip, kind, category, label, created_at, guest_sid, "
            "is_internal, "
            "substr(datetime(created_at, '+9 hours'), 1, 10) AS jst_date "
            "FROM usage_events "
            "WHERE user_id = ? AND ip IS NOT NULL AND ip != '' "
            f"AND {_UE_ACTION_ONLY} "
            "AND created_at >= datetime('now', ?) "
            "ORDER BY created_at",
            (guest_uid, since),
        ).fetchall()
        own_sids = _own_device_sids(conn)
        err_rows = conn.execute(
            "SELECT ip, COUNT(*) AS n FROM client_errors "
            "WHERE user_id = ? AND ip IS NOT NULL AND ip != '' "
            "AND created_at >= datetime('now', ?) GROUP BY ip",
            (guest_uid, since),
        ).fetchall()

    client_error_map = {r["ip"]: r["n"] for r in err_rows}
    admin_ips = load_admin_known_ips()

    groups: dict[str, dict] = {}
    for r in rows:
        own = own_sids.get(r["guest_sid"] or "", {})
        # 管理者/テストアカウントの端末の未ログイン操作はイベント単位で
        # 除外する(同じIPを一般ゲストと共有していても巻き込まない)。
        if own.get("admin") and not include_admin:
            continue
        if own.get("test") and not include_test:
            continue
        # 内部Cookie(自分の端末)だけで分かる分(2026-09-19・計測設計3-D)。
        # 管理者かテストかは判別できないので、どちらかを含める指定の
        # ときだけ残し、その場合は管理者側の印を付ける。
        internal_only = bool(r["is_internal"]) and not own
        if internal_only and not (include_admin or include_test):
            continue
        g = groups.setdefault(r["ip"], {
            "events": [], "days": set(),
            "admin_dev": False, "test_dev": False,
        })
        g["events"].append(r)
        g["days"].add(r["jst_date"])
        g["admin_dev"] = (
            g["admin_dev"] or bool(own.get("admin")) or internal_only)
        g["test_dev"] = g["test_dev"] or bool(own.get("test"))

    items = []
    for ip, g in groups.items():
        if not include_admin and ip in admin_ips:
            continue
        events = g["events"]
        if len(events) < min_events:
            continue
        domains: collections.Counter = collections.Counter()
        total_plays = total_play_errors = 0
        word_detail_clicks = phrase_detail_clicks = 0
        for e in events:
            kind = e["kind"]
            category = e["category"] or ""
            if kind == "word_domain":
                domains[category] += 1
            elif kind == "play":
                total_plays += 1
            elif kind == "play_error":
                total_play_errors += 1
            elif kind == "page" and category == "word_detail":
                word_detail_clicks += 1
            elif kind == "page" and category == "phrase_detail":
                phrase_detail_clicks += 1
        items.append({
            "ip": ip,
            "is_admin": ip in admin_ips or g["admin_dev"],
            "is_test": g["test_dev"],
            "total_events": len(events),
            "distinct_days": len(g["days"]),
            "first_seen": min(e["created_at"] for e in events),
            "last_seen": max(e["created_at"] for e in events),
            "total_plays": total_plays,
            "total_play_errors": total_play_errors,
            "total_client_errors": client_error_map.get(ip, 0),
            "word_detail_clicks": word_detail_clicks,
            "phrase_detail_clicks": phrase_detail_clicks,
            "top_word_domains": _top(domains, 3),
        })

    items.sort(key=lambda it: (-it["distinct_days"], -it["total_events"]))
    items = items[:limit]
    return {
        "days": days, "min_events": min_events, "count": len(items),
        "items": items,
    }


@router.get("/admin/guest-ip-detail")
def admin_guest_ip_detail(ip: str, days: int = 90):
    """指定IP(ゲスト)1件分の深掘り詳細（admin_guest_ip_analysisの行を
    クリックした時に呼ぶ・2026-09-17）。単語/例文/フレーズのどれを再生
    したか、再生に失敗した項目、開いた単語・フレーズ詳細、発生したJS
    エラー等をできるだけ詳しく返す。"""
    _require_admin()
    days = max(1, min(days, 365))
    ip = (ip or "").strip()
    if not ip:
        return {"error": "ip is required"}
    since = f"-{days} days"

    with db() as conn:
        # admin_guest_ip_analysisと同じ理由(2026-09-18修正)でuser_id=
        # guest_uid判定に統一。
        guest_uid = auth.ensure_guest_user_id(conn)
        rows = conn.execute(
            "SELECT kind, category, label, created_at FROM usage_events "
            f"WHERE user_id = ? AND ip = ? AND {_UE_ACTION_ONLY} "
            "AND created_at >= datetime('now', ?) ORDER BY created_at",
            (guest_uid, ip, since),
        ).fetchall()
        js_error_rows = conn.execute(
            "SELECT kind, message, url, line, col, created_at "
            "FROM client_errors WHERE user_id = ? AND ip = ? "
            "AND created_at >= datetime('now', ?) "
            "ORDER BY created_at DESC LIMIT 50",
            (guest_uid, ip, since),
        ).fetchall()

    domains: collections.Counter = collections.Counter()
    scenes: collections.Counter = collections.Counter()
    word_plays: collections.Counter = collections.Counter()
    example_plays: collections.Counter = collections.Counter()
    phrase_plays: collections.Counter = collections.Counter()
    word_details: collections.Counter = collections.Counter()
    phrase_details: collections.Counter = collections.Counter()
    tabs: collections.Counter = collections.Counter()
    clicks: collections.Counter = collections.Counter()
    play_errors = []
    play_error_counts: collections.Counter = collections.Counter()
    for r in rows:
        kind = r["kind"]
        category = r["category"] or ""
        label = r["label"] or ""
        if kind == "word_domain":
            domains[category] += 1
        elif kind == "phrase_scene":
            scenes[category] += 1
        elif kind == "play":
            # labelは "word:実際のテキスト" / "example:実際のテキスト" /
            # "phrase:実際のテキスト" 形式(app/routers/learn.pyのtts_item)。
            # /api/learn/tts(読み上げ・音読機能)は item紐付けが無いため
            # "voice:テキスト" 形式のまま単語再生として扱う。
            base, sep, ident = label.partition(":")
            if sep and base == "example":
                example_plays[ident[:80]] += 1
            elif sep and base == "phrase":
                phrase_plays[ident[:80]] += 1
            elif sep and base == "word":
                word_plays[ident[:80]] += 1
            else:
                word_plays[label[:80]] += 1
        elif kind == "play_error":
            play_errors.append({
                "category": category, "label": label, "at": r["created_at"],
            })
            # 「再生できないものを何度も押下した」を一目で見えるように、
            # 同じ対象(category+label)への失敗回数も別途集計する
            # (2026-09-18ユーザー要望)。
            play_error_counts[f"{category}: {label}"] += 1
        elif kind == "page" and category == "word_detail":
            word_details[label] += 1
        elif kind == "page" and category == "phrase_detail":
            phrase_details[label] += 1
        elif kind == "page":
            tabs[label or category] += 1
        elif kind == "click":
            clicks[label or category] += 1

    return {
        "ip": ip,
        "days": days,
        "total_events": len(rows),
        "first_seen": rows[0]["created_at"] if rows else None,
        "last_seen": rows[-1]["created_at"] if rows else None,
        "top_word_domains": _top(domains, 10),
        "top_phrase_scenes": _top(scenes, 10),
        "top_tabs": _top(tabs, 10),
        "top_clicks": _top(clicks, 10),
        "word_plays": _top(word_plays, 20),
        "example_plays": _top(example_plays, 20),
        "phrase_plays": _top(phrase_plays, 20),
        "play_errors": play_errors[-50:],
        "play_errors_by_target": _top(play_error_counts, 20),
        "word_details": _top(word_details, 20),
        "phrase_details": _top(phrase_details, 20),
        "js_errors": [dict(r) for r in js_error_rows],
    }


# ログ/バックアップ用に割り当てたディスク予算（2026-08-19・管理画面の
# 目安表示にのみ使う。強制的な上限ではない）。
_DISK_BUDGET_MB = 1024

# 2026-09-14 DB分割前は、DB内のテーブルを用途別にグルーピングしてdbstat
# 仮想テーブルで内訳を出していた(dbstatはATTACH先を見ないため分割後は
# mainのテーブルしか見えなくなり、この分類自体も意味を失った)。分割後は
# ファイルが既にcontent/core/logsに分かれているため、`admin_disk_usage`
# はファイルサイズを直接見るだけで同じ目的(内容別の使用量把握)を
# より単純かつ確実に果たせる(dbstat拡張の有無にも依存しない)。


# コスト管理レポートの粗利率アラート閾値(2026-09-06新設)。0%未満=赤字
# (badge-bad)、これ以上でもWARN未満=低粗利(badge-warn)。目安は
# docs/COST_ESTIMATE.mdの目標粗利率(3〜5割)を踏まえた保守的な値。
COST_REPORT_LOSS_MARGIN_PCT = 0.0
COST_REPORT_WARN_MARGIN_PCT = 20.0

# 実収支(pl-report)用の固定費(2026-09-09新設・ユーザー指示の実額)。
# サーバー代はdocs/COST_ESTIMATE.md記載の月額¥1,958(n8n等との相乗り按分
# 込み)を、さらに他プロジェクト(n8n/ecopy/homeassistant等)との相乗り
# 実態に合わせて1/3按分。広告費はGoogle Ads(nyangailabアカウント)の
# 日予算¥100×30日。いずれも「月額」なので、pl-reportの集計期間(days)に
# 応じて日割りする。
# 2026-09-19: 広告費は下のAD_DAILY_BUDGET_SCHEDULE(予算スケジュール)と
# 実額(logs.ad_spend_daily・管理画面から入力)に置き換えた。
# FIXED_MONTHLY_AD_COST_JPYは「スケジュールの最初の日付より前」の日の
# 推定にだけ使う旧来の値として残している。
FIXED_MONTHLY_SERVER_COST_JPY = 1958.0 / 3
FIXED_MONTHLY_AD_COST_JPY = 3000.0

# Google広告の日予算スケジュール(円/日・「その日付以降」に適用)。
# オーナー申告(2026-09-19): 2026-09-12〜09-18は¥500/日、2026-09-19以降
# (当面)は¥1,000/日。実額(ad_spend_daily)が入力された日はそちらを優先し、
# 入力の無い日だけこの予算で日割りした「予算(推定)」にフォールバックする。
# 予算を変えたらここへ日付順に追記する。
AD_DAILY_BUDGET_SCHEDULE = [("2026-09-12", 500), ("2026-09-19", 1000)]

# 広告費入力の妥当な範囲(誤入力ガード)。1日あたり100万円まで。
_AD_SPEND_MAX_JPY = 1_000_000.0
_AD_SOURCES = ("google_ads", "other")

# 数値目標(オーナー回答・2026-09-19)。管理画面「実収支」の目標欄で使う。
GOAL_NEAR = {"registrants": 20, "payers": 2}
GOAL_FINAL = {"registrants": 300, "payers": 30}


def _ad_budget_for(date_str: str) -> float:
    """その日(JST暦日 YYYY-MM-DD)の広告費の予算(推定)日額。最初の
    スケジュール日付より前は従来の月額定数の日割り。"""
    amount = FIXED_MONTHLY_AD_COST_JPY / 30.0
    for start, jpy in sorted(AD_DAILY_BUDGET_SCHEDULE):
        if date_str >= start:
            amount = float(jpy)
    return amount


def _cost_report_feature_bucket(feature: str) -> str:
    """crossword_hint/crossword_hint_reviewは1ゲーム単位でまとめて
    課金される(balance_ledgerのreason='crossword_game'は機能別に
    分かれない)ため、原価側もcrossword一本にまとめて突き合わせる。"""
    return "crossword" if (feature or "").startswith("crossword") else (
        feature or "(不明)")


def _cost_report_margin(cost_jpy: float, charged_jpy: float) -> dict:
    profit = charged_jpy - cost_jpy
    margin_pct = (profit / charged_jpy * 100) if charged_jpy > 0 else (
        0.0 if cost_jpy <= 0 else -100.0)
    return {
        "cost_jpy": round(cost_jpy, 2),
        "charged_jpy": round(charged_jpy, 2),
        "profit_jpy": round(profit, 2),
        "margin_pct": round(margin_pct, 1),
        "is_loss": profit < 0,
        "is_low_margin": (
            COST_REPORT_LOSS_MARGIN_PCT
            <= margin_pct < COST_REPORT_WARN_MARGIN_PCT),
    }


@router.get("/admin/cost-report")
def admin_cost_report(days: int = 30):
    """機能別・ユーザー別の原価/課金(pt→円換算)/粗利レポート(2026-09-06
    新設)。原価は`ai_usage.cost_usd`(USD建て・為替換算)、課金は
    `balance_ledger`の実控除額(delta_jpy<0)の絶対値を突き合わせる。
    `balance_ledger`は呼び出し毎課金の全機能をまとめて
    reason='ai_usage'にしているため、機能別の内訳は`note`列
    (`f"{feature} (${cost:.5f})"`形式・`_maybe_deduct_balance`参照)の
    先頭トークンから復元する。クロスワードはreason='crossword_game'
    (1ゲームまとめて課金・`charge_crossword_game`参照)を別途集計し、
    原価側もcrossword_hint/crossword_hint_reviewをまとめて突き合わせる
    (`_cost_report_feature_bucket`)。"""
    _require_admin()
    days = max(1, min(days, 365))
    since = f"-{days} days"
    rate = load_settings().usd_jpy_rate

    with db() as conn:
        cost_rows = conn.execute(
            "SELECT user_id, feature, SUM(cost_usd) AS cost_usd "
            "FROM ai_usage WHERE created_at >= datetime('now', ?) "
            "GROUP BY user_id, feature",
            (since,),
        ).fetchall()
        ledger_rows = conn.execute(
            "SELECT user_id, reason, note, delta_jpy FROM balance_ledger "
            "WHERE created_at >= datetime('now', ?) "
            "AND reason IN ('ai_usage', 'crossword_game') "
            "AND delta_jpy < 0",
            (since,),
        ).fetchall()
        user_rows = conn.execute(
            "SELECT id, username, role FROM users").fetchall()

    usernames = {r["id"]: r["username"] for r in user_rows}
    roles = {r["id"]: r["role"] for r in user_rows}

    cost_by_uf: dict[tuple[int, str], float] = {}
    for r in cost_rows:
        key = (r["user_id"], _cost_report_feature_bucket(r["feature"]))
        cost_by_uf[key] = (
            cost_by_uf.get(key, 0.0) + (r["cost_usd"] or 0.0) * rate)

    charge_by_uf: dict[tuple[int, str], float] = {}
    for r in ledger_rows:
        if r["reason"] == "crossword_game":
            feature = "crossword"
        else:
            feature = (r["note"] or "").split(" ", 1)[0] or "(不明)"
        key = (r["user_id"], feature)
        charge_by_uf[key] = charge_by_uf.get(key, 0.0) + (-r["delta_jpy"])

    all_keys = set(cost_by_uf) | set(charge_by_uf)

    by_feature_totals: dict[str, list[float]] = {}
    by_user_totals: dict[int, list[float]] = {}
    for uid, feature in all_keys:
        cost = cost_by_uf.get((uid, feature), 0.0)
        charged = charge_by_uf.get((uid, feature), 0.0)
        f_tot = by_feature_totals.setdefault(feature, [0.0, 0.0])
        f_tot[0] += cost
        f_tot[1] += charged
        u_tot = by_user_totals.setdefault(uid, [0.0, 0.0])
        u_tot[0] += cost
        u_tot[1] += charged

    by_feature = sorted(
        (
            {"feature": feature, **_cost_report_margin(cost, charged)}
            for feature, (cost, charged) in by_feature_totals.items()
        ),
        key=lambda r: r["profit_jpy"],
    )
    by_user = sorted(
        (
            {
                "user_id": uid,
                "username": usernames.get(uid, f"(id={uid})"),
                "role": roles.get(uid, ""),
                **_cost_report_margin(cost, charged),
            }
            for uid, (cost, charged) in by_user_totals.items()
        ),
        key=lambda r: r["profit_jpy"],
    )
    total_cost = sum(c for c, _ in by_user_totals.values())
    total_charged = sum(g for _, g in by_user_totals.values())
    return {
        "days": days,
        "by_feature": by_feature,
        "by_user": by_user,
        "total": _cost_report_margin(total_cost, total_charged),
    }


@router.get("/admin/pl-report")
def admin_pl_report(days: int = 30):
    """実収支(実際に入金された円 - 実コスト)レポート(2026-09-09新設)。
    上の`cost-report`は内部ポイント経済の粗利チェック(AI原価 vs ポイント
    控除額)であって実際の円の売上/損益ではないため、別途こちらを新設した。
    売上はBASE注文(`base_orders`、status='cancelled'以外は入金済みとみなす。
    BASE側で決済が完了してから当システムに注文が記録されるため)と
    PayPay決済(`paypay_payments`、status='COMPLETED'のみ)の合計。コストは
    AI原価(`ai_usage.cost_usd`を為替換算)に、サーバー代・広告費等の固定費
    (`FIXED_MONTHLY_*_JPY`、月額を集計期間の日数で日割り)を加えたもの。"""
    _require_admin()
    days = max(1, min(days, 365))
    since = f"-{days} days"
    rate = load_settings().usd_jpy_rate

    # 広告費: 集計期間をJST暦日に展開し、実額のある日は実額、無い日は予算
    # (推定)で足す(2026-09-19・計測設計3-C)。今日も1日分として数える。
    today_jst = _now_jst().date()
    ad_dates = [
        (today_jst - timedelta(days=i)).isoformat()
        for i in range(days - 1, -1, -1)
    ]
    with db() as conn:
        ad_rows = conn.execute(
            "SELECT date, SUM(jpy) AS jpy FROM ad_spend_daily "
            "WHERE date >= ? AND date <= ? GROUP BY date",
            (ad_dates[0], ad_dates[-1]),
        ).fetchall()
        base_revenue = conn.execute(
            "SELECT COALESCE(SUM(amount_jpy), 0) FROM base_orders "
            "WHERE status != 'cancelled' "
            "AND detected_at >= datetime('now', ?)",
            (since,),
        ).fetchone()[0]
        paypay_revenue = conn.execute(
            "SELECT COALESCE(SUM(amount_jpy), 0) FROM paypay_payments "
            "WHERE status = 'COMPLETED' "
            "AND created_at >= datetime('now', ?)",
            (since,),
        ).fetchone()[0]
        ai_cost_usd = conn.execute(
            "SELECT COALESCE(SUM(cost_usd), 0) FROM ai_usage "
            "WHERE created_at >= datetime('now', ?)",
            (since,),
        ).fetchone()[0]
        # 広告(gclid付き)経由の訪問と登録(自前計測・Ads側の数字との
        # 突き合わせ/CPAの参考値用)。ボット・内部端末は除く。
        ad_visit_guests = {r["guest_sid"] for r in conn.execute(
            "SELECT DISTINCT guest_sid FROM landing_visits "
            "WHERE kind='visit' AND has_gclid=1 AND guest_sid != '' "
            "AND is_internal=0 AND bot_mark=0 "
            "AND created_at >= datetime('now', ?)", (since,),
        ).fetchall()}
        ad_signup_guests = {r["guest_sid"] for r in conn.execute(
            "SELECT DISTINCT guest_sid FROM landing_visits "
            "WHERE kind='signup' AND success=1 AND guest_sid != '' "
            "AND is_internal=0 AND bot_mark=0 "
            "AND created_at >= datetime('now', ?)", (since,),
        ).fetchall()} & ad_visit_guests
        # 数値目標の達成状況(累計): 管理者/テスト/ゲスト疑似ユーザーを
        # 除いた登録者数と、課金(BASE・PayPayのチャージ)した人数。
        registrants = conn.execute(
            "SELECT COUNT(*) FROM users u "
            f"WHERE {_user_filter_sql(False, False, False)} "
            f"AND u.username != '{auth.GUEST_USERNAME}'",
        ).fetchone()[0]
        payers = conn.execute(
            "SELECT COUNT(DISTINCT bl.user_id) FROM balance_ledger bl "
            "JOIN users u ON u.id = bl.user_id "
            "WHERE bl.reason IN ('charge_key_redeem', 'paypay_charge') "
            "AND bl.delta_jpy > 0 "
            f"AND {_user_filter_sql(False, False, False)}",
        ).fetchone()[0]

    revenue_jpy = int(base_revenue) + int(paypay_revenue)
    ai_cost_jpy = (ai_cost_usd or 0.0) * rate
    day_ratio = days / 30.0
    server_cost_jpy = FIXED_MONTHLY_SERVER_COST_JPY * day_ratio
    ads_actual = {r["date"]: float(r["jpy"] or 0) for r in ad_rows}
    ads_actual_jpy = sum(ads_actual.get(d, 0.0) for d in ad_dates
                         if d in ads_actual)
    est_dates = [d for d in ad_dates if d not in ads_actual]
    ads_estimated_jpy = sum(_ad_budget_for(d) for d in est_dates)
    ads_cost_jpy = ads_actual_jpy + ads_estimated_jpy
    fixed_cost_jpy = server_cost_jpy + ads_cost_jpy
    total_cost_jpy = ai_cost_jpy + fixed_cost_jpy
    profit_jpy = revenue_jpy - total_cost_jpy

    return {
        "days": days,
        "revenue": {
            "base_jpy": int(base_revenue),
            "paypay_jpy": int(paypay_revenue),
            "total_jpy": revenue_jpy,
        },
        "cost": {
            "ai_jpy": round(ai_cost_jpy, 2),
            "server_jpy": round(server_cost_jpy, 2),
            # 広告費 = 実額(入力のある日) + 予算(推定・入力の無い日)。
            "ads_jpy": round(ads_cost_jpy, 2),
            "ads_actual_jpy": round(ads_actual_jpy, 2),
            "ads_estimated_jpy": round(ads_estimated_jpy, 2),
            "ads_actual_days": len(ads_actual),
            "ads_estimated_days": len(est_dates),
            "total_jpy": round(total_cost_jpy, 2),
        },
        "profit_jpy": round(profit_jpy, 2),
        "is_loss": profit_jpy < 0,
        # 広告(gclid付き)経由の自前計測。登録が0件ならCPAはNone。
        # 実額の入力が無い期間は予算(推定)ベースなので参考値。
        "ads": {
            "visitors": len(ad_visit_guests),
            "signups": len(ad_signup_guests),
            "cpa_jpy": (round(ads_cost_jpy / len(ad_signup_guests), 1)
                        if ad_signup_guests else None),
        },
        "budget_schedule": [
            {"from": d, "jpy": j} for d, j in sorted(AD_DAILY_BUDGET_SCHEDULE)],
        "goals": {
            "registrants": registrants, "payers": payers,
            "near": GOAL_NEAR, "final": GOAL_FINAL,
        },
    }


class AdSpendIn(BaseModel):
    date: str
    jpy: float
    source: str = "google_ads"
    note: str = ""


@router.get("/admin/ad-spend")
def admin_ad_spend_list(days: int = 60):
    """広告費の実額入力の一覧(管理者専用・新しい日付順)。予算スケジュール
    で補っている日は含まれない(入力済みの日だけ)。"""
    _require_admin()
    days = max(1, min(days, 730))
    start = (_now_jst().date() - timedelta(days=days - 1)).isoformat()
    with db() as conn:
        rows = conn.execute(
            "SELECT date, source, jpy, note, updated_at FROM ad_spend_daily "
            "WHERE date >= ? ORDER BY date DESC, source", (start,),
        ).fetchall()
    return {"items": [dict(r) for r in rows]}


@router.post("/admin/ad-spend")
def admin_ad_spend_upsert(payload: AdSpendIn):
    """広告費の実額を1日1ソース単位で登録/上書きする(管理者専用・
    2026-09-19・計測設計3-C)。Ads APIは使わず、管理画面のCSV/手入力の
    数字を入れる運用。入力した日は予算(推定)ではなくこの実額が使われる。"""
    _require_admin()
    date = (payload.date or "").strip()
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise errors.http_error("7002", "日付はYYYY-MM-DDで指定してください。")
    if not (0 <= payload.jpy <= _AD_SPEND_MAX_JPY) or payload.jpy != payload.jpy:
        raise errors.http_error(
            "7002", f"金額は0〜{int(_AD_SPEND_MAX_JPY):,}円の範囲で指定して"
            "ください。")
    source = (payload.source or "google_ads").strip()
    if source not in _AD_SOURCES:
        raise errors.http_error("7002", "広告ソースが不正です。")
    with db() as conn:
        conn.execute(
            "INSERT INTO ad_spend_daily (date, source, jpy, note) "
            "VALUES (?, ?, ?, ?) ON CONFLICT(date, source) DO UPDATE SET "
            "jpy = excluded.jpy, note = excluded.note, "
            "updated_at = datetime('now')",
            (date, source, round(payload.jpy, 2), (payload.note or "")[:200]),
        )
    return {"ok": True, "date": date, "source": source, "jpy": payload.jpy}


@router.delete("/admin/ad-spend")
def admin_ad_spend_delete(date: str, source: str = "google_ads"):
    """入力済みの実額を取り消す(その日は予算(推定)に戻る)。"""
    _require_admin()
    with db() as conn:
        cur = conn.execute(
            "DELETE FROM ad_spend_daily WHERE date = ? AND source = ?",
            (date.strip(), source.strip()),
        )
    return {"ok": True, "deleted": cur.rowcount}


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

    # 2026-09-14 DB分割後は、ファイルが既にcontent(語彙等)/core(users・
    # 決済・単語帳・進捗等)/logs(アクセスログ等)に分かれているため、
    # ファイルサイズを直接見るだけで内容別の使用量が分かる
    # (dbstat仮想テーブル+テーブルグルーピングは不要になった)。
    file_sizes = {
        "content": paths.content_db_file,
        "core": paths.db_file,
        "logs": paths.logs_db_file,
    }
    group_mb = {
        label: round(
            (p.stat().st_size if p.exists() else 0) / 1024 / 1024, 2)
        for label, p in file_sizes.items()
    }
    db_file_bytes = sum(
        p.stat().st_size for p in file_sizes.values() if p.exists()
    )

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
        "dbstat_available": True,
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


@router.get("/admin/server-status-history")
def admin_server_status_history(hours: int = 24):
    """CPU/RAM/ディスクの過去推移+期間内の最大値（2026-08-30ユーザー
    要望「過去1ヶ月・過去1週間で最大の負荷も表示できるようにする」
    「24時間/1週間/1ヶ月切り替えできるグラフ表示」）。admin_server_status
    と同じ data/server_stats.jsonl(collect_server_stats.pyがVPSホスト
    cronで5分おきに追記)を読む。グラフ用に約120点へダウンサンプル
    するが、maxはダウンサンプル前の生データから算出する(平均に埋もれて
    瞬間的なピークを取りこぼさないため)。"""
    _require_admin()
    hours = max(1, min(hours, 24 * 31))
    path = paths.data_dir / "server_stats.jsonl"
    if not path.exists():
        return {"hours": hours, "max": None, "points": []}
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    records = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                ts = datetime.strptime(
                    rec["ts"], "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=timezone.utc)
            except (ValueError, KeyError):
                continue
            if ts >= since:
                records.append(rec)
    if not records:
        return {"hours": hours, "max": None, "points": []}
    max_stat = {
        "load1": max(r.get("load1", 0) for r in records),
        "mem_pct": max(r.get("mem_pct", 0) for r in records),
        "disk_pct": max(r.get("disk_pct", 0) for r in records),
    }
    target_points = 120
    bucket_size = max(1, len(records) // target_points)
    points = []
    for i in range(0, len(records), bucket_size):
        chunk = records[i:i + bucket_size]
        n = len(chunk)
        points.append({
            "ts": chunk[-1]["ts"],
            "load1": round(sum(r.get("load1", 0) for r in chunk) / n, 2),
            "mem_pct": round(sum(r.get("mem_pct", 0) for r in chunk) / n, 1),
            "disk_pct": round(sum(r.get("disk_pct", 0) for r in chunk) / n, 1),
        })
    return {"hours": hours, "max": max_stat, "points": points}
