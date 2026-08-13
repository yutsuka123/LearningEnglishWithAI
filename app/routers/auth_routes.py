"""ログイン/ログアウト/現在ユーザー（§A マルチユーザー化）。

MULTIUSER=1 のときに使う。ローカル単一ユーザー（既定）では認証は不要で、
常に owner として動くため、これらのエンドポイントは使われない（/me は owner を
返す）。セッションは stdlib hmac の署名Cookie（app/services/auth.py）。
"""

from __future__ import annotations

import os
import time

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..database import db
from ..services import auth

router = APIRouter(prefix="/api/auth", tags=["auth"])

# 2026-08-13〜: まだ試験公開中のため、新規登録の受付を一時停止する。
# 既存ユーザーのログイン（/api/auth/login 以下）には一切影響しない。
# 受付を再開するときはこの値を True に戻すだけでよい。
SIGNUP_OPEN = False
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


class LoginIn(BaseModel):
    username: str
    password: str


class SignupIn(BaseModel):
    email: str
    password: str
    charge_key: str = ""
    display_name: str = ""
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
def signup(payload: SignupIn, request: Request, response: Response):
    """自己サインアップ（メアド+パス）。チャージキーは任意（2026-08-13〜）:
    入力があればその場で償還してpt付与、空なら残高0の②ログイン無課金
    ユーザーとして登録する。チャージキーは設定画面の「💳 チャージ」
    （`POST /api/billing/redeem`）から後でいつでも入力できる。
    username にはメアドをそのまま使うため、既存の /api/auth/login や
    authenticate() は一切変更不要（従来ユーザーのログイン経路と共存する）。
    """
    if not SIGNUP_OPEN:
        return JSONResponse(
            {"ok": False, "error": SIGNUP_CLOSED_MESSAGE}, status_code=403,
        )
    from ..services import charge_keys

    ip = auth.real_client_ip(request)
    if charge_keys.signup_redeem_locked(ip):
        return JSONResponse(
            {"ok": False, "error": "失敗が続いたため、しばらく時間をおいて"
             "から再試行してください。"},
            status_code=429,
        )
    email = payload.email.strip().lower()
    password = payload.password
    if "@" not in email or "." not in email.split("@")[-1]:
        return JSONResponse(
            {"ok": False, "error": "メールアドレスの形式が正しくありません。"},
            status_code=400,
        )
    if auth.is_disposable_email_domain(email):
        return JSONResponse(
            {"ok": False, "error": "使い捨てメールアドレスでは登録できません。"},
            status_code=400,
        )
    pw_error = auth.password_policy_error(password)
    if pw_error:
        return JSONResponse({"ok": False, "error": pw_error}, status_code=400)
    full_name = payload.full_name.strip()
    furigana = payload.furigana.strip()
    if not full_name or not furigana:
        return JSONResponse(
            {"ok": False, "error": "氏名とフリガナを入力してください。"},
            status_code=400,
        )
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
                email=email, display_name=payload.display_name or email,
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
        if str(e) != "このメールアドレスは既に登録されています。":
            charge_keys.record_signup_redeem_failure(ip)
        return JSONResponse({"ok": False, "error": str(e)}, status_code=400)
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
def login(payload: LoginIn, request: Request, response: Response):
    ip = auth.real_client_ip(request)
    locked = auth.login_locked(payload.username, ip)
    if locked:
        return JSONResponse(
            {"ok": False, "error": "試行が多すぎます。しばらく待って"
             "から再試行してください。"}, status_code=429)
    with db() as conn:
        u = auth.authenticate(conn, payload.username, payload.password)
        if not u:
            auth.record_login_failure(payload.username, ip)
            auth.record_login_event(conn, payload.username, ip, False)
            return JSONResponse(
                {"ok": False, "error": "ユーザー名かパスワードが違います。"},
                status_code=401,
            )
        secret = auth.get_session_secret(conn)
        auth.record_login_event(conn, payload.username, ip, True)
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
        return JSONResponse({"ok": False, "error": "未ログイン"},
                            status_code=401)
    return {"ok": True, "user": {
        "id": u["id"], "username": u["username"], "role": u["role"],
        "display_name": u["display_name"], "email": u["email"],
        "tier": tier,
        "daily_cost_cap_usd": u["daily_cost_cap_usd"],
        "monthly_cost_cap_usd": u["monthly_cost_cap_usd"],
        "balance_jpy": u["balance_jpy"],
        "multiuser": auth.multiuser_enabled(),
    }}
