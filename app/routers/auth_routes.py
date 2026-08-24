"""ログイン/ログアウト/現在ユーザー（§A マルチユーザー化）。

MULTIUSER=1 のときに使う。ローカル単一ユーザー（既定）では認証は不要で、
常に owner として動くため、これらのエンドポイントは使われない（/me は owner を
返す）。セッションは stdlib hmac の署名Cookie（app/services/auth.py）。
"""

from __future__ import annotations

import os
import time

from fastapi import APIRouter, BackgroundTasks, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..config import log
from ..database import db
from ..services import auth, geoip
from ..services.errors import error_response

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 2026-08-18〜: リリース前の最終テスト（本人によるテストアカウント登録）
# のため受付を再開。停止するときはこの値を False に戻すだけでよい。
SIGNUP_OPEN = True
SIGNUP_CLOSED_MESSAGE = (
    "現在は試験公開中のため、新規登録の受付を停止しています。"
    "正式公開は2026年9月中を予定しております。"
    "既にIDをお持ちの方はログインしてください。"
)


def _cookie_secure(request: Request) -> bool:
    """本番HTTPSでは Secure Cookie を必須にする。COOKIE_SECURE=1 で強制、
    auto（既定）はリバプロの X-Forwarded-Proto / scheme が https かで判定。"""
    mode = os.getenv("COOKIE_SECURE", "auto").strip().lower()
    if mode in ("1", "true", "yes"):
        return True
    if mode in ("0", "false", "no"):
        return False
    xfp = request.headers.get("x-forwarded-proto", "").split(",")[0].strip()
    return request.url.scheme == "https" or xfp == "https"


def _record_signup_attempt(
    request: Request, ip: str, success: bool,
    background_tasks: BackgroundTasks,
) -> None:
    """新規登録の試行(成否問わず)をlanding_visitsに記録する（2026-08-20・
    管理画面「未登録アクセス状況」の「登録しようとしたか」判定用）。
    書き込み失敗は登録処理自体を妨げないよう握りつぶす。"""
    try:
        with db() as conn:
            conn.execute(
                "INSERT INTO landing_visits "
                "(ip, kind, success, user_agent) VALUES (?, 'signup', ?, ?)",
                (ip, 1 if success else 0,
                 request.headers.get("user-agent", "")[:300]),
            )
        background_tasks.add_task(geoip.enrich_ip, ip)
    except Exception:
        log.warning("landing_visits(signup)記録に失敗", exc_info=True)


class LoginIn(BaseModel):
    username: str
    password: str


class SignupIn(BaseModel):
    email: str
    password: str
    charge_key: str = ""
    display_name: str = ""
    display_name_furigana: str = ""
    full_name: str = ""
    furigana: str = ""
    survey_occupation_category: str = ""
    survey_occupation_detail: str = ""
    survey_age_group: str = ""
    survey_gender: str = ""
    survey_purpose: str = ""
    survey_referral: str = ""
    survey_free_text: str = ""
    survey_interest_areas: str = ""


@router.post("/signup")
def signup(
    payload: SignupIn, request: Request, response: Response,
    background_tasks: BackgroundTasks,
):
    """自己サインアップ（メアド+パス）。チャージキーは任意（2026-08-13〜）:
    入力があればその場で償還してpt付与、空なら残高0の②ログイン無課金
    ユーザーとして登録する。チャージキーは設定画面の「💳 チャージ」
    （`POST /api/billing/redeem`）から後でいつでも入力できる。
    username にはメアドをそのまま使うため、既存の /api/auth/login や
    authenticate() は一切変更不要（従来ユーザーのログイン経路と共存する）。
    """
    from ..services import charge_keys

    ip = auth.real_client_ip(request)

    def fail(code: str, message: str | None = None):
        _record_signup_attempt(request, ip, False, background_tasks)
        return error_response(code, message)

    if not SIGNUP_OPEN:
        return fail("2016", SIGNUP_CLOSED_MESSAGE)
    if charge_keys.signup_redeem_locked(ip):
        log.warning("signup: rate-limited ip=%s", ip)
        return fail("2015")
    email = payload.email.strip().lower()
    password = payload.password
    if "@" not in email or "." not in email.split("@")[-1]:
        log.warning("signup: invalid email format ip=%s email=%r", ip, email)
        return fail("2010")
    if auth.is_disposable_email_domain(email):
        log.warning(
            "signup: disposable email domain ip=%s email=%s", ip, email)
        return fail("2011")
    pw_error = auth.password_policy_error(password)
    if pw_error:
        log.warning("signup: password policy error ip=%s email=%s reason=%s",
                     ip, email, pw_error)
        return fail("2012", pw_error)
    display_name = payload.display_name.strip()
    # フリガナは任意（2026-08-24・登録の入力項目を減らして離脱を防ぐ
    # ユーザー方針。お名前(呼んでほしい名前)は宛名として必要なため必須の
    # まま、フリガナだけ任意化）。
    display_name_furigana = payload.display_name_furigana.strip()
    if not display_name:
        log.warning("signup: missing display_name ip=%s email=%s",
                     ip, email)
        return fail("2013")
    full_name = payload.full_name.strip()
    furigana = payload.furigana.strip()
    # 注意: ChargeKeyError は with ブロックの外で捕まえること。ブロック内で
    # catch して return してしまうと、db() の contextmanager からは
    # "例外なく正常終了" に見えて create_user の INSERT がロールバックされず
    # コミットされてしまう（同じ except を with の内側に置いて早期return
    # した場合に発生する既知の落とし穴。実装時に一度この不具合を作り込み、
    # 検証で「無効キーでも登録失敗のはずがユーザー行が残る」ことを発見して
    # 修正した）。
    try:
        with db() as conn:
            if (auth.get_user_by_email(conn, email)
                    or auth.get_user_by_name(conn, email)
                    or auth.find_user_by_normalized_email(conn, email)):
                raise charge_keys.ChargeKeyError(
                    "このメールアドレスは既に登録されています。")
            uid = auth.create_user(
                conn, email, password,
                email=email, display_name=display_name,
                display_name_furigana=display_name_furigana,
                full_name=full_name, furigana=furigana,
                survey_occupation_category=payload.survey_occupation_category,
                survey_occupation_detail=payload.survey_occupation_detail,
                survey_age_group=payload.survey_age_group,
                survey_gender=payload.survey_gender,
                survey_purpose=payload.survey_purpose,
                survey_referral=payload.survey_referral,
                survey_free_text=payload.survey_free_text,
                survey_interest_areas=payload.survey_interest_areas,
            )
            if payload.charge_key.strip():
                charge_keys.redeem_key(conn, uid, payload.charge_key)
            secret = auth.get_session_secret(conn)
            u = auth.get_user(conn, uid)
    except charge_keys.ChargeKeyError as e:
        # 「メール登録済み」はチャージキー総当たりとは無関係なので数えない。
        is_dup_email = str(e) == "このメールアドレスは既に登録されています。"
        if not is_dup_email:
            charge_keys.record_signup_redeem_failure(ip)
        log.warning("signup: failed ip=%s email=%s reason=%s", ip, email, e)
        return fail("2014" if is_dup_email else "3001", str(e))
    log.info("signup: ok ip=%s email=%s uid=%s charge_key=%s",
              ip, email, uid, bool(payload.charge_key.strip()))
    _record_signup_attempt(request, ip, True, background_tasks)
    token = auth.make_session_token(
        secret, uid, u.get("session_epoch", 0), int(time.time()))
    resp = JSONResponse({"ok": True, "user": {
        "id": u["id"], "username": u["username"], "role": u["role"],
        "display_name": u["display_name"], "email": u["email"],
    }})
    resp.set_cookie(
        auth.SESSION_COOKIE, token, max_age=auth._SESSION_TTL,
        httponly=True, samesite="lax", path="/",
        secure=_cookie_secure(request),
    )
    return resp


@router.post("/login")
def login(
    payload: LoginIn, request: Request, response: Response,
    background_tasks: BackgroundTasks,
):
    ip = auth.real_client_ip(request)
    locked = auth.login_locked(payload.username, ip)
    if locked:
        log.warning(
            "login: rate-limited ip=%s username=%s", ip, payload.username)
        return error_response("2002")
    with db() as conn:
        u = auth.authenticate(conn, payload.username, payload.password)
        if not u:
            auth.record_login_failure(payload.username, ip)
            log_id = auth.record_login_event(
                conn, payload.username, ip, False)
            background_tasks.add_task(auth.update_login_hostname, log_id, ip)
            log.warning("login: failed ip=%s username=%s", ip, payload.username)
            return error_response("2001")
        secret = auth.get_session_secret(conn)
        log_id = auth.record_login_event(conn, payload.username, ip, True)
        background_tasks.add_task(auth.update_login_hostname, log_id, ip)
    log.info("login: ok ip=%s username=%s uid=%s", ip, payload.username, u["id"])
    auth.clear_login_failures(payload.username, ip)
    token = auth.make_session_token(
        secret, u["id"], u.get("session_epoch", 0), int(time.time()))
    resp = JSONResponse({"ok": True, "user": {
        "id": u["id"], "username": u["username"], "role": u["role"],
        "display_name": u["display_name"],
    }})
    # HttpOnly + SameSite=Lax + (本番HTTPSは)Secure。
    resp.set_cookie(
        auth.SESSION_COOKIE, token, max_age=auth._SESSION_TTL,
        httponly=True, samesite="lax", path="/",
        secure=_cookie_secure(request),
    )
    return resp


@router.post("/logout")
def logout():
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(auth.SESSION_COOKIE, path="/")
    return resp


@router.post("/logout-all-devices")
def logout_all_devices():
    """自分の既存の全セッションを一括で無効化する（§B4）。侵害された
    かもしれないセッションに心当たりがあるときのセルフサービス機能。
    このリクエスト自身のCookieも直後に削除するため、この端末でも
    再ログインが必要になる。"""
    uid = auth.current_user_id()
    with db() as conn:
        auth.bump_session_epoch(conn, uid)
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(auth.SESSION_COOKIE, path="/")
    return resp


@router.get("/me")
def me():
    """現在ログイン中のユーザー情報（残高・上限を含む）。未ログインは 401。"""
    uid = auth.current_user_id()
    with db() as conn:
        u = auth.get_user(conn, uid)
        tier = auth.user_tier(conn, uid) if u else None
    if not u:
        return error_response("2003", "未ログイン")
    return {"ok": True, "user": {
        "id": u["id"], "username": u["username"], "role": u["role"],
        "display_name": u["display_name"], "email": u["email"],
        "tier": tier,
        "daily_cost_cap_usd": u["daily_cost_cap_usd"],
        "monthly_cost_cap_usd": u["monthly_cost_cap_usd"],
        "balance_jpy": u["balance_jpy"],
        "multiuser": auth.multiuser_enabled(),
    }}
