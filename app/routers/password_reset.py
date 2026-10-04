"""パスワード再発行(2026-10-04・ver1.5.12・仕組みは`app/services/password_reset.py`参照)。

利用者の流れ: ログイン画面の「パスワードを忘れた方」→ 依頼(`POST /api/auth/password-help`・お問い合わせとして保存)→
管理者が管理画面で本人確認 → 使い捨ての再設定リンクを発行して本人へ渡す →
本人が`/reset-password`で新しいパスワードを設定(`POST /api/auth/password-reset`)。

- 依頼の応答は、登録の有無によらず常に同じ(登録メールアドレスの存在を外部に漏らさない)。
- 公開エンドポイントはIPごとに回数を制限する(プロセス内メモリ・再起動でリセット)。
- 管理者用エンドポイントは全て管理者(role=admin)専用(サーバー側で強制)。
"""

from __future__ import annotations

import hashlib
import os
import re
import time
import unicodedata

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from ..config import log
from ..database import db
from ..services import auth, errors, messages, password_reset

router = APIRouter(prefix="/api/auth", tags=["password-reset"])

# ---- 回数制限(プロセス内メモリ・uvicornは単一プロセス) -------------------------------------
_HITS: dict[str, tuple[float, list[float]]] = {}      # キー -> (窓の秒数, 直近の時刻)


def _rate_limited(key: str, limit: int, window: float) -> bool:
    """直近`window`秒に`limit`回に達していれば真(真のときは数えない)。偽のときは1回数える。"""
    now = time.monotonic()
    hits = [t for t in _HITS.get(key, (window, []))[1] if now - t < window]
    if len(hits) >= limit:
        _HITS[key] = (window, hits)
        return True
    hits.append(now)
    _HITS[key] = (window, hits)
    if len(_HITS) > 5000:           # 古いキーを掃除(それぞれの窓の長さを過ぎて何もないキーだけ・メモリの肥大防止)
        for k in [k for k, (w, v) in _HITS.items() if not v or now - v[-1] > w]:
            _HITS.pop(k, None)
        if len(_HITS) > 20000:      # それでも多い(窓の内側のキーが大量=分散した荒らし)ときは、最後の記録が古い順に捨てる(上限の保険)
            for k, _ in sorted(_HITS.items(), key=lambda kv: kv[1][1][-1] if kv[1][1] else 0.0)[:len(_HITS) - 15000]:
                _HITS.pop(k, None)
    return False


def _require_admin(conn) -> int:
    me = auth.get_user(conn, auth.current_user_id())
    if not me or me.get("role") != "admin" or not me.get("is_active"):
        raise errors.http_error("2004", "管理者のみ利用できます。")
    return int(me["id"])


# 空白・制御文字・複数の@を許さない(依頼本文に偽の行を差し込ませない・2026-10-04独立照査M-1)。
_EMAIL_RE = re.compile(r"[^\s@]+@[^\s@]+\.[^\s@]+")
# 見えない・幅のない・行を区切る文字(Cf=書式制御/Co=私用/Cs=サロゲート)と、見た目が空白に近い「フィラー」類
# (結合書字素ジョイナー・ハングル/クメールのフィラー等)。メールの突き合わせや本文の見出し行の偽装に使わせない
# (2026-10-04再照査N-5)。異体字セレクタ(FE00-FE0F・E0100-E01EF)は絵文字の表示に使うので、メール/返信先(strict)だけ除く。
_STRIP_CP = {0x034F, 0x115F, 0x1160, 0x17B4, 0x17B5, 0x3164, 0xFFA0}


def _strip_invisible(text: str, keep_newline: bool = False, strict: bool = False) -> str:
    """見えない文字を除く。空白・改行・行区切り(\t \r \x0b \x0c NEL U+2028/2029 等)は空白に置き換え、
    `keep_newline`のときだけ\nを残す。`strict`(メール・返信先)は異体字セレクタも除き、NFKCで正規化する。"""
    out: list[str] = []
    for ch in (unicodedata.normalize("NFKC", text) if strict and text else (text or "")):
        o = ord(ch)
        cat = unicodedata.category(ch)
        if ch == "\n":
            out.append("\n" if keep_newline else " ")
        elif ch.isspace() or cat in ("Cc", "Zl", "Zp"):
            out.append(" ")
        elif (cat in ("Cf", "Co", "Cs") or o in _STRIP_CP or 0x180B <= o <= 0x180E or 0xE0000 <= o <= 0xE007F
              or (strict and (0xFE00 <= o <= 0xFE0F or 0xE0100 <= o <= 0xE01EF))):
            continue
        else:
            out.append(ch)
    return "".join(out)


def _email_ok(email: str) -> bool:
    return bool(email) and len(email) <= 254 and _EMAIL_RE.fullmatch(email) is not None


def _clean_line(text: str, limit: int, strict: bool = False) -> str:
    """1行の文字列に整える(見えない文字を除き、空白を詰める)。"""
    return " ".join(_strip_invisible(text, strict=strict).split())[:limit]


def _clean_note(text: str, limit: int) -> str:
    """補足(複数行可)。見えない文字を除き、行頭に「> 」を付けて、利用者の入力と本文の見出し行を見分けやすくする。"""
    raw = (text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.rstrip() for ln in _strip_invisible(raw, keep_newline=True).split("\n")]
    kept: list[str] = []
    for ln in lines:
        if ln or (kept and kept[-1]):      # 連続する空行は1つに
            kept.append(ln)
    return "\n".join("> " + ln for ln in kept).strip()[: limit + 200]


# ---- 利用者: 再発行の依頼 -----------------------------------------------------------
class PasswordHelpIn(BaseModel):
    email: str = Field(default="", max_length=300)          # 登録したメールアドレス(必須)
    nickname: str = Field(default="", max_length=100)       # 登録時の呼んでほしいお名前(任意)
    contact: str = Field(default="", max_length=300)        # 返信先(任意・空なら登録メール)
    note: str = Field(default="", max_length=1500)          # 登録時期・チャージの有無など本人確認の手がかり(任意)
    website: str = Field(default="", max_length=200)        # ハニーポット(人間には見えない欄・入っていたらボット)


_HELP_DAILY_CAP = 300       # 見知らぬIPからの依頼をプロセス全体で1日(24時間)に保存する上限(分散した荒らしで管理画面を埋められないように)
_HELP_PER_EMAIL_CAP = 10    # 同じ登録メールの依頼の上限(24時間)
_STORED: dict[str, float] = {}      # 重複判定: 保存に成功した依頼のキー -> 時刻(保存後にだけ記録する)
_DUP_WINDOW = 600.0


def _recently_stored(key: str) -> bool:
    t = _STORED.get(key)
    return t is not None and time.monotonic() - t < _DUP_WINDOW


def _remember_stored(key: str) -> None:
    now = time.monotonic()
    _STORED[key] = now
    if len(_STORED) > 5000:
        for k in [k for k, t in _STORED.items() if now - t >= _DUP_WINDOW]:
            _STORED.pop(k, None)


def _ip_known(conn, ip: str) -> bool:
    """このIPから直近30日にログイン成功があるか(忘れた本人は、いつもの回線から依頼することが多い)。"""
    if not ip:
        return False
    return conn.execute(
        "SELECT 1 FROM login_log WHERE ip = ? AND success = 1 AND created_at >= datetime('now', '-30 days') LIMIT 1",
        (ip,)).fetchone() is not None


@router.post("/password-help")
def password_help(payload: PasswordHelpIn, request: Request):
    ip = auth.real_client_ip(request)
    if _rate_limited(f"help-ip|{ip}", 5, 3600.0):
        return errors.error_response("2002")
    email = _clean_line(payload.email, 300, strict=True).lower()
    if not _email_ok(email):
        return errors.error_response("2010")
    contact = _clean_line(payload.contact, 300, strict=True).lower()
    reply = contact if _email_ok(contact) else email
    nickname = _clean_line(payload.nickname, 100)
    note = _clean_note(payload.note, 1500)
    # ハニーポット(人間には見えない欄)に入力があっても**捨てない**: ブラウザの自動入力が埋めることがあり、本人の依頼が
    # 「受け付けました」と返されたまま消えるのを防ぐ。代わりに本文へ印を付けて保存する(回数の上限は他と同じ・再照査N-2)。
    bot = bool(payload.website.strip())
    dup_key = f"{email}|{reply}|{ip}"
    # 全く同じ依頼(同じ登録メール・返信先・IP)の10分以内の再送は、保存済みなので同じ応答だけ返す(重複を積まない)。
    # 記録は**保存に成功したあとだけ**(上限で断られた依頼の再送を「受け付けました」で消さないため・再照査N-2)。
    if _recently_stored(dup_key):
        return {"ok": True}
    with db() as conn:
        n24 = conn.execute(
            "SELECT COUNT(*) FROM inquiries WHERE kind = 'パスワード再発行' "
            "AND created_at >= datetime('now', '-1 day') AND instr(content, ?) = 1",
            (password_reset.request_prefix(email),)).fetchone()[0]
        if n24 >= _HELP_PER_EMAIL_CAP:
            return errors.error_response("2002")          # 黙って捨てず、利用者に「しばらく待って」と伝える
        # プロセス全体の上限は、直近30日にログイン成功のあるIPには適用しない(荒らしに枯らされても本人は依頼できる・再照査N-3)
        if not _ip_known(conn, ip) and _rate_limited("help-global-day", _HELP_DAILY_CAP, 86400.0):
            log.warning("password-help: daily cap reached (not stored)")
            return errors.error_response("2002")
        multi = (f"同じ登録メールの依頼: 24時間で{n24 + 1}件目(返信先が違う依頼が混ざっていないか確認してください)\n"
                 if n24 >= 1 else "")
        content = (
            password_reset.request_prefix(email)                  # 先頭2行(見出し+登録メール)はサーバーだけが作る
            + f"ニックネーム: {nickname or '(未記入)'}\n"
            f"連絡先(返信先): {reply}{'  ※登録メールと異なります' if reply != email else ''}\n"
            f"{multi}"
            + ("※自動入力の疑い(人間には見えない欄に入力あり・ボットの可能性があります)\n" if bot else "")
            + "補足(登録時期・チャージの有無など): " + (note.replace("\n", " / ") if note else "(未記入)") + "\n"
            "--- 補足の原文 ---\n" + (note or "(未記入)"))
        conn.execute(
            "INSERT INTO inquiries (user_id, kind, name, email, content) VALUES (?, ?, ?, ?, ?)",
            # user_idは空にする: 認証不要のパスでは`current_user_id()`が運営者(id=1)になる仕様のため、使わない
            (None, "パスワード再発行", nickname, reply, content))
    _remember_stored(dup_key)
    log.info("password-help: request stored ip=%s bot_suspect=%s", ip, bot)   # メールアドレス・本文はログに出さない
    return {"ok": True}


# ---- 利用者: 再設定リンクの確認と新パスワードの設定 ------------------------------------------
class TokenIn(BaseModel):
    token: str = Field(default="", max_length=300)


class ResetIn(BaseModel):
    token: str = Field(default="", max_length=300)
    new_password: str = Field(default="", max_length=200)


@router.post("/password-reset/check")
def password_reset_check(payload: TokenIn, request: Request):
    """リンクがいま使えるか(新パスワードを入力する前に、無効なリンクだと分かるように)。"""
    if _rate_limited(f"reset-check|{auth.real_client_ip(request)}", 30, 600.0):
        return errors.error_response("2002")
    with db() as conn:
        return {"valid": password_reset.is_valid(conn, payload.token)}


@router.post("/password-reset")
def password_reset_apply(payload: ResetIn, request: Request):
    ip = auth.real_client_ip(request)
    if _rate_limited(f"reset-apply|{ip}", 20, 600.0):
        return errors.error_response("2002")
    with db() as conn:
        result, detail = password_reset.consume(conn, payload.token, payload.new_password, ip)
    if result == "invalid":
        log.warning("password-reset: invalid or expired link ip=%s", ip)
        return errors.error_response("2017")
    if result == "policy":
        return errors.error_response("2012", messages.tr(detail))
    auth.clear_all_login_failures_for_username(detail)
    return {"ok": True}      # 自動ログインはしない(新しいパスワードでログインし直してもらう)


# ---- 管理者: 本人確認の手がかりの表示・リンクの発行/取り消し ------------------------------------
@router.get("/admin/password-reset/lookup")
def admin_lookup(q: str = ""):
    with db() as conn:
        _require_admin(conn)
        return {"users": password_reset.lookup(conn, q)}


_DEFAULT_PUBLIC_BASE = "https://study.nyangailab.com"
_ALLOWED_HOSTS = {"study.nyangailab.com", "localhost", "127.0.0.1"}


def _public_base(request: Request) -> str:
    """発行するリンクの先頭(スキーム+ホスト)。環境変数PUBLIC_BASE_URLがあればそれ。無ければ、Hostヘッダが既知のホスト
    (本番ドメイン・localhost)のときだけ従い、それ以外は本番ドメインに固定する(Hostヘッダ注入でリンクの宛先を偽装されない・
    SSHトンネル等で壊れたURLを配らない・2026-10-04独立照査L-2)。"""
    base = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if base:
        return base
    host = request.headers.get("host", "").strip().lower()
    if host.rsplit(":", 1)[0] in _ALLOWED_HOSTS:
        scheme = auth.external_scheme(request) if host.startswith("study.") else "http"
        return f"{scheme}://{host}"
    return _DEFAULT_PUBLIC_BASE


class IssueIn(BaseModel):
    user_id: int
    hours: int = password_reset.DEFAULT_HOURS
    note: str = Field(default="", max_length=200)      # 何を根拠に本人と判断したか(監査用の控え)
    ack_reply_differs: bool = False                     # 「返信先が登録メールと異なる依頼がある」警告を見て続行する(画面の確認ダイアログ後にtrue)


@router.post("/admin/password-reset/link")
def admin_issue(payload: IssueIn, request: Request):
    with db() as conn:
        admin_id = _require_admin(conn)
        target = auth.get_user(conn, payload.user_id)
        if not target:
            raise errors.http_error("7001", "ユーザーが見つかりません。")
        blocker = password_reset.issue_blocker(conn, target)
        if blocker:
            raise errors.http_error("2018", blocker)
        # 返信先が登録メールと異なる依頼が直近30日にあるときは、警告を見たこと(ack)をサーバーでも要求し、控えにも
        # サーバー側で印を残す(クライアントの表示や接頭辞に頼らない・再照査N-4)。検索から時間が経って新しい依頼が
        # 届いていた場合も、ここで止まって再確認になる。
        differs = password_reset.reply_differs_count(conn, target)
        if differs and not payload.ack_reply_differs:
            raise errors.http_error("2018", password_reset.ack_required_message(differs))     # 管理者向けの文言
        note = payload.note.strip()
        if differs:
            note = ("[返信先相違あり] " + note)[:200]
        token, expires = password_reset.create_link(
            conn, admin_id, payload.user_id, payload.hours, note)
    path = f"/reset-password#t={token}"
    base = _public_base(request)
    return {"ok": True, "path": path, "url": base + path, "expires_at": expires,
            "hours": payload.hours if payload.hours in password_reset.ALLOWED_HOURS else password_reset.DEFAULT_HOURS}


class RevokeIn(BaseModel):
    user_id: int


@router.post("/admin/password-reset/revoke")
def admin_revoke(payload: RevokeIn):
    with db() as conn:
        _require_admin(conn)
        n = password_reset.revoke_all(conn, payload.user_id)
    return {"ok": True, "revoked": n}
