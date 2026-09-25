"""ログイン/ログアウト/現在ユーザー（§A マルチユーザー化）。

MULTIUSER=1 のときに使う。ローカル単一ユーザー（既定）では認証は不要で、
常に owner として動くため、これらのエンドポイントは使われない（/me は owner を
返す）。セッションは stdlib hmac の署名Cookie（app/services/auth.py）。
"""

from __future__ import annotations

import secrets
import time

from fastapi import APIRouter, BackgroundTasks, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ..config import log
from ..database import db
from ..services import auth, geoip, messages, visitor_kind
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


def _record_signup_attempt(
    request: Request, ip: str, success: bool,
    background_tasks: BackgroundTasks,
    fail_reason: str = "", is_disposable_email: bool = False,
    user_id: int | None = None,
) -> None:
    """新規登録の試行(成否問わず)をlanding_visitsに記録する（2026-08-20・
    管理画面「未登録アクセス状況」の「登録しようとしたか」判定用）。
    2026-09-07・fail_reason(エラーコード)とis_disposable_emailを追加し、
    失敗理由を多角的に分析できるようにした(管理画面「登録に至らない
    原因分析」から失敗理由内訳として参照)。書き込み失敗は登録処理自体を
    妨げないよう握りつぶす。
    2026-09-19(計測設計3-M/3-D): 成功時はuser_id(登録されたユーザー)も
    行に残し、登録前の行動(guest_sid)と登録後の利用・課金を明示的に
    結べるようにした。内部端末(自分のテスト登録)ならis_internalも立てる。"""
    try:
        ua = request.headers.get("user-agent", "")[:300]
        with db() as conn:
            conn.execute(
                "INSERT INTO landing_visits "
                "(ip, kind, success, user_agent, guest_sid, fail_reason, "
                " is_disposable_email, accept_language, user_id, "
                " is_internal, bot_mark) "
                "VALUES (?, 'signup', ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (ip, 1 if success else 0, ua,
                 auth.current_guest_sid(), fail_reason,
                 1 if is_disposable_email else 0,
                 request.headers.get("accept-language", "")[:100],
                 user_id if success else None,
                 auth.current_is_internal(),
                 visitor_kind.classify_ua(ua)[0]),
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
    # 使い捨てメールかどうかは成否によらず記録する(下のfail()クロージャが
    # 参照するため、emailを解析した時点で更新する)。以前はここで登録自体を
    # 拒否していたが、プライバシー志向の正規利用者を誤って弾いている懸念が
    # 強く、実際の悪用有無をログで見極められるようにする方針に変更した
    # (2026-09-07ユーザー指示「使い捨ても許可したい、弊害ないか」)。
    is_disposable_email = False

    def fail(code: str, message: str | None = None):
        _record_signup_attempt(
            request, ip, False, background_tasks,
            fail_reason=code, is_disposable_email=is_disposable_email)
        return error_response(code, message)

    if not SIGNUP_OPEN:
        return fail("2016", messages.tr("auth.signup_closed"))
    if charge_keys.signup_redeem_locked(ip):
        log.warning("signup: rate-limited ip=%s", ip)
        return fail("2015")
    email = payload.email.strip().lower()
    password = payload.password
    if "@" not in email or "." not in email.split("@")[-1]:
        log.warning("signup: invalid email format ip=%s email=%r", ip, email)
        return fail("2010")
    is_disposable_email = auth.is_disposable_email_domain(email)
    if is_disposable_email:
        log.info(
            "signup: disposable email domain (許可・記録のみ) ip=%s email=%s",
            ip, email)
    pw_key = auth.password_policy_key(password)
    if pw_key:
        # ログは日本語(従来どおり)・利用者への文言は表示言語(X-Lang)。
        log.warning("signup: password policy error ip=%s email=%s reason=%s",
                     ip, email, messages.tr_ja(pw_key))
        return fail("2012", messages.tr(pw_key))
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
            # 登録時のゲストセッションCookieを明示的に保存する(2026-09-19・
            # 計測設計3-M)。登録前の行動(usage_events/landing_visits)と
            # 登録後の有効化・継続・課金をguest_sid経由で正確に結ぶため。
            conn.execute(
                "UPDATE users SET signup_guest_sid = ? WHERE id = ?",
                (auth.current_guest_sid(), uid))
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
    _record_signup_attempt(
        request, ip, True, background_tasks,
        is_disposable_email=is_disposable_email, user_id=uid)
    token = auth.make_session_token(
        secret, uid, u.get("session_epoch", 0), int(time.time()))
    resp = JSONResponse({"ok": True, "user": {
        "id": u["id"], "username": u["username"], "role": u["role"],
        "display_name": u["display_name"], "email": u["email"],
    }})
    resp.set_cookie(
        auth.SESSION_COOKIE, token, max_age=auth._SESSION_TTL,
        httponly=True, samesite="lax", path="/",
        secure=auth.cookie_secure(request),
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
        secure=auth.cookie_secure(request),
    )
    # 管理者/テストアカウントでのログイン成功時に「自分の端末」の目印
    # Cookieを付ける(2026-09-19・計測設計3-D)。以後この端末の記録は
    # ログアウト後・IPが変わっても分析から除外できる。
    if u.get("role") == "admin" or u.get("is_test"):
        resp.set_cookie(
            auth.INTERNAL_COOKIE, "1", max_age=auth.INTERNAL_TTL,
            httponly=True, samesite="lax", path="/",
            secure=auth.cookie_secure(request),
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


# 退会(アカウント削除)の理由の選択肢(2026-09-23・オーナー要望「設定に
# 退会を設けましょう。退会理由を選択肢で聞く、自由記入欄を設ける」)。
# key はDB(account_withdrawals.reasons、カンマ区切り複数可)・
# 管理画面の集計に使うので、一度公開したら安易に変えない
# (inquiries.KINDSと同じ方針)。
WITHDRAW_REASONS = {
    "not_enough_features": "使いたい機能が足りなかった",
    "hard_to_use": "操作が分かりにくかった",
    "bugs": "表示・音声などの不具合があった",
    "achieved_goal": "目的の学習を達成できた",
    "switching": "他のサービス・教材に移る",
    "price": "料金が合わなかった",
    "not_using": "最近あまり使わなくなった",
    "other": "その他",
}

# 退会時に削除する「学習データ」テーブル(user_id列で自分の行を特定できる
# もの)。決済記録(paypay_payments/balance_ledger)・AI利用ログ(ai_usage、
# 課金の裏付けとして決済記録と同様に扱う)は対象外(プライバシーポリシー
# §9「法令上保存が必要なものを除き」・2026-09-23オーナー確認)。
_WITHDRAW_PERSONAL_TABLES = (
    "user_word_progress", "user_phrase_progress", "user_material_progress",
    "user_category_progress", "user_listening_progress",
    "user_settings_backups", "user_settings",
    "word_attempts", "phrase_attempts", "study_sessions",
    "conversation_log", "deck_progress", "crossword_sessions",
    "crossword_sample_plays",
)


class WithdrawIn(BaseModel):
    reasons: list[str] = []
    detail: str = ""


@router.post("/withdraw")
def withdraw(payload: WithdrawIn):
    """自己サービスの退会(アカウント削除・2026-09-23・オーナー要望「登録は
    あるが登録を解除がない」への対応)。ログイン中の本人のみ実行できる。

    usersの行自体は削除しない(paypay_payments/balance_ledgerがuser_idを
    NOT NULLで参照しており、法令上の保存義務があるため=CLAUDE.md/
    プライバシーポリシー§9)。代わりに個人を特定できる列(username=登録
    メールアドレス・display_name・email・password_hash)を匿名化し
    is_active=0にしてログイン不可にする。学習データ(進捗・単語帳・AI会話
    ログ等)は削除する。理由(選択式+自由記入)はaccount_withdrawalsに
    記録し、オーナーが後から離脱理由を分析できるようにする。"""
    uid = auth.current_user_id()
    reasons = [r for r in payload.reasons if r in WITHDRAW_REASONS]
    detail = payload.detail.strip()[:1000]
    if not reasons and not detail:
        return error_response(
            "7002", "退会理由を1つ以上選択するか、自由記入欄にご記入くだ"
            "さい。")
    with db() as conn:
        if auth.is_guest_user_id(conn, uid):
            return error_response("2003", "要ログイン")
        u = auth.get_user(conn, uid)
        if not u or not u.get("is_active"):
            return error_response("2003", "要ログイン")
        if u.get("role") == "admin":
            # 唯一の管理者が誤ってセルフサービスで退会し、管理画面に誰も
            # 入れなくなる事故を避ける(多重防御・想定される利用者は一般
            # ユーザーのみ)。管理者の退会はお問い合わせ経由の手動対応。
            return error_response(
                "7002", "管理者アカウントはこの画面から退会できません。"
                "お問い合わせからご連絡ください。")
        conn.execute(
            "INSERT INTO account_withdrawals "
            "(user_id, username_at_withdrawal, reasons, detail) "
            "VALUES (?, ?, ?, ?)",
            (uid, u["username"], ",".join(reasons), detail),
        )
        for tbl in _WITHDRAW_PERSONAL_TABLES:
            conn.execute(f"DELETE FROM {tbl} WHERE user_id = ?", (uid,))
        # 自作の単語帳/フレーズ帳(配下のdeck_words/deck_progress等は
        # ON DELETE CASCADEで自動的に削除される)。
        conn.execute("DELETE FROM decks WHERE user_id = ?", (uid,))
        conn.execute("DELETE FROM phrase_decks WHERE user_id = ?", (uid,))
        # AI生成教材(materials)は他ユーザーも閲覧できる共有コンテンツの
        # ことがあるため削除せず、作成者としての紐付けだけ外す。
        conn.execute(
            "UPDATE materials SET user_id = NULL WHERE user_id = ?", (uid,))
        anon_username = f"withdrawn_{uid}_{secrets.token_hex(4)}"
        conn.execute(
            "UPDATE users SET username = ?, display_name = '', "
            " email = '', password_hash = '', is_active = 0 WHERE id = ?",
            (anon_username, uid),
        )
        auth.bump_session_epoch(conn, uid)
    resp = JSONResponse({"ok": True})
    resp.delete_cookie(auth.SESSION_COOKIE, path="/")
    return resp


def _require_admin(conn) -> None:
    me_row = auth.get_user(conn, auth.current_user_id())
    if not me_row or me_row.get("role") != "admin":
        from ..services import errors
        raise errors.http_error("2004", "管理者のみ閲覧できます。")


@router.get("/withdrawals")
def list_withdrawals(limit: int = 200):
    """管理者専用: 退会理由の一覧(新しい順)。離脱理由の分析用
    (2026-09-23)。reasonsはWITHDRAW_REASONSのkeyのカンマ区切りなので、
    フロント側でラベルに変換する。"""
    limit = max(1, min(limit, 500))
    with db() as conn:
        _require_admin(conn)
        rows = conn.execute(
            "SELECT id, username_at_withdrawal, reasons, detail, created_at "
            "FROM account_withdrawals ORDER BY id DESC LIMIT ?", (limit,),
        ).fetchall()
    return {
        "reason_labels": WITHDRAW_REASONS,
        "withdrawals": [dict(r) for r in rows],
    }


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
