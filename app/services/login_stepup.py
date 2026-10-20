"""ログインの追加確認(step-up)の受け口(2026-10-20・ver1.5.19)。

管理者アカウント(と「おとり名」)のログインだけ、別サービスの確認を通してからでないとセッションを
発行しない。確認の中身(何を聞くか・何段か・時間・判定)はこのコードには無く、別サービス側にある。
ここにあるのは「名簿に載っている名前か」の判定と、別サービスの内部APIを2つ呼ぶ薄いクライアント、
応答の厳格な検査だけ。

- 環境変数 LOGIN_STEPUP_URL が空/未設定なら何もしない(従来どおりのログイン)。
- LOGIN_STEPUP_KEY: 内部APIの共有キー(Bearer)。値はログ・例外・画面に出さない。
- LOGIN_STEPUP_DECOYS: おとり名(カンマ区切り)。実在しない名前でも管理者名と同じ流れにするためのもの。
- 内部APIはdockerの内部網だけで呼ぶ。X-Forwarded-Forは付けない(付いていると相手は404にする)。
- 失敗・タイムアウト・想定外の応答は全て「確認できなかった」(None)にし、呼び出し側が通常の
  ログイン失敗(2001)と同じ扱いにする(fail-closed)。
"""
from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import secrets
import threading
import time
import urllib.parse
import urllib.request
from typing import Optional

from ..config import log
from . import auth

_TIMEOUT_SEC = 2.0
_MAX_BODY = 65536
# 別サービスから受け取る値は、ブラウザや Set-Cookie にそのまま渡すので形を厳しく検査する。
_SRC_RE = re.compile(r"^/(?!/)[A-Za-z0-9_\-./~%=&?]{1,500}$")
_TICKET_RE = re.compile(r"^[A-Za-z0-9_\-]{8,200}$")
_COOKIE_NAME_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
# Cookie値は「引用符で囲まれずにそのまま出る文字」だけ(英数字と _ - . : ~)。RFC 6265のcookie-octetは
# `/` `=` `(` 等も許すが、PythonのSimpleCookie(StarletteのSet-Cookie)は、それらを含む値を"..."で囲んで出し、
# ブラウザはそのクォートごと保存して送り返すため、相手がその値を自分のCookieと認識できず無言で壊れる
# (2026-10-20 独立照査M-1)。相手の値はbase64url(英数字と _ -)なので、この範囲で足りる。
_COOKIE_VALUE_RE = re.compile(r"^[A-Za-z0-9_\-.:~]{1,2048}$")
_COOKIE_PATH_RE = re.compile(r"^/[A-Za-z0-9_\-./]{0,100}$")
_MAX_COOKIE_AGE = 60 * 60 * 24 * 400
# 相手に渡すCookieヘッダは、広告タグ等のノイズを除いてから上限で切る(あふれて確認が毎回失敗するのを避ける)
_COOKIE_NOISE_PREFIXES = ("_ga", "_gid", "_gcl", "__utm", "_fbp", "_clck", "_clsk")
_COOKIE_HEADER_MAX = 12000   # 相手のボディ上限は16KB(Cookie項目は12KB)
_dummy_hash: Optional[str] = None


def _raw_url() -> str:
    return os.getenv("LOGIN_STEPUP_URL", "").strip()


def _url() -> str:
    return _raw_url().rstrip("/")


def _key() -> str:
    return os.getenv("LOGIN_STEPUP_KEY", "").strip()


def enabled() -> bool:
    """未設定(空)ならフック無効(従来どおり)。値が空でないときは有効のまま扱う:
    キーが無い・URLが`/`だけ・スキームが不正などの誤設定は、呼び出しが全て失敗して管理者は
    通れない(=安全側)。黙ってフック無効(パスワードだけで入れる状態)にはしない
    (2026-10-21 独立照査2回目L-3)。"""
    return bool(_raw_url())


def describe() -> str:
    """起動ログ用の1行(キーは出さない。ホスト名だけ)。誤設定に気づけるようにする。"""
    if not enabled():
        return "無効(従来どおりのログイン)"
    base = _url()
    if not base.lower().startswith(("http://", "https://")):
        return "有効だがURLの形が不正(管理者は入れません・設定を確認してください)"
    try:
        host = urllib.parse.urlparse(base).hostname or "?"
    except ValueError:
        host = "?"
    return "有効(宛先ホスト=%s・キー%s)" % (host, "あり" if _key() else "なし=管理者は入れません")


def _decoys() -> set[str]:
    raw = os.getenv("LOGIN_STEPUP_DECOYS", "")
    return {n.strip().lower() for n in raw.split(",") if n.strip()}


def in_roster(conn, username: str) -> bool:
    """このユーザー名は追加確認の名簿(管理者全員 ∪ おとり名)に載っているか。
    - 実在する名前: role が admin のときだけ(有効/無効は問わない)。実在する一般ユーザーは、
      おとり名と同じ綴りでも名簿に入れない(本物の利用者がログインできなくなるのを防ぐ)。
    - 実在しない名前: おとり名、または管理者名と大文字小文字だけ違う名前(取りこぼし防止)。
    照合は既存のログイン(get_user_by_name=前後空白除去・大文字小文字は区別)に合わせる。"""
    u = (username or "").strip()
    if not u:
        return False
    row = conn.execute("SELECT role FROM users WHERE username = ?", (u,)).fetchone()
    if row is not None:
        return row["role"] == "admin"
    low = u.lower()
    if low in _decoys():
        return True
    hit = conn.execute(
        "SELECT 1 FROM users WHERE role = 'admin' AND lower(username) = ? LIMIT 1",
        (low,)).fetchone()
    return hit is not None


def bind_for(username: str) -> str:
    """beginとredeemで同じ値を使う束縛値(ユーザー名のSHA-256)。"""
    return hashlib.sha256((username or "").strip().encode("utf-8")).hexdigest()


def request_host(request) -> str:
    """要求のHostヘッダ(小文字・ポート無し)。"""
    h = (request.headers.get("host") or "").strip().lower()
    if h.startswith("["):      # IPv6リテラル(想定外・そのまま)
        return h
    return h.split(":", 1)[0]


def cookie_for_gate(header: str) -> str:
    """リクエストのCookieヘッダから、ノイズ(広告タグ・このアプリ自身のCookie)を除いて上限内に収める。
    相手のCookie名はこちらでは分からないので、それ以外は全て渡す。"""
    own = {auth.SESSION_COOKIE, auth.GUEST_SID_COOKIE, auth.INTERNAL_COOKIE}
    kept = []
    for part in (header or "").split(";"):
        part = part.strip()
        if not part or "=" not in part:
            continue
        name = part.split("=", 1)[0].strip()
        if name in own or name.startswith(_COOKIE_NOISE_PREFIXES):
            continue
        kept.append(part)
    out = "; ".join(kept)
    return out if len(out) <= _COOKIE_HEADER_MAX else ""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """3xxに追従しない(追従するとurllibは共有キーを転送先へそのまま送り、転送先の応答を相手の答えとして
    受け入れてしまう。2026-10-21 独立照査2回目L-1)。追従しない=HTTPErrorになり、呼び出し側が失敗にする。"""

    def redirect_request(self, req, fp, code, msg, headers, newurl):   # noqa: D401
        return None


# 環境の http(s)_proxy を通さない(内部網の宛先なので)
_opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect)
# 1回の呼び出しの総時間の上限。_TIMEOUT_SECはソケット操作ごとの待ちなので、1バイトずつ細切れに返す相手は
# それだけでは打ち切れず枠(下の8)を長く占有できる(2026-10-21 独立照査2回目L-2)。本文の読み込みに総時間の上限を設ける。
_TOTAL_SEC = 2.5


# 相手への同時呼び出しの上限。相手が遅い/落ちていると1回ごとに最大2秒スレッドを占有するので、
# 多数の同時ログインでアプリ全体の処理枠(同期エンドポイントのスレッド)を使い切らせない。
# 枠が空かなければ待たずに(最大1秒)失敗(2001)にする(2026-10-20 独立照査M-2)。
_gate_slots = threading.BoundedSemaphore(8)
_SLOT_WAIT_SEC = 1.0


def _post(path: str, payload: dict) -> Optional[dict]:
    base, key = _url(), _key()
    if not base:
        return None
    if not _gate_slots.acquire(timeout=_SLOT_WAIT_SEC):
        log.warning("login_stepup: 確認サービスの同時呼び出しが上限(枠が空かない)")
        return None
    try:
        # URLの誤設定(スキーム無し・http/https以外)も失敗にする。例外を外へ出さない(500にしない)・
        # ファイル等へ読みに行かせない。有効/無効の判定(enabled)はURLが空かどうかだけなので、
        # 誤設定は「フック無効」ではなく「全て失敗=管理者は入れない」(fail-closed)になる。
        if not base.lower().startswith(("http://", "https://")):
            log.warning("login_stepup: 確認サービスのURLの形が不正(http/httpsで始まらない)")
            return None
        req = urllib.request.Request(
            base + path, data=json.dumps(payload).encode("utf-8"), method="POST",
            headers={"Content-Type": "application/json",
                     "Authorization": "Bearer " + key})
        deadline = time.monotonic() + _TOTAL_SEC
        with _opener.open(req, timeout=_TIMEOUT_SEC) as r:
            if r.status != 200:
                return None
            chunks, size = [], 0
            while True:
                if time.monotonic() > deadline:
                    raise TimeoutError("total time exceeded")
                # read1: 届いた分だけで返る(read(n)はn byteたまるまで戻らず、細切れに返す相手だと
                # 総時間の判定が遅れる)
                chunk = r.read1(4096)
                if not chunk:
                    break
                size += len(chunk)
                if size > _MAX_BODY:
                    raise ValueError("body too large")
                chunks.append(chunk)
            data = json.loads(b"".join(chunks).decode("utf-8"))
    except Exception as e:   # 失敗の理由(キー・チケットを含みうる)は書かず、種類だけ残す
        log.warning("login_stepup: 確認サービスの呼び出しに失敗(%s)", type(e).__name__)
        return None
    finally:
        _gate_slots.release()
    return data if isinstance(data, dict) else None


# 確認の開始(ticketなしのログイン)のIP別の上限。ここは失敗として数えない(正規の利用者が確認画面を
# 開いただけで締め出されないように)が、無制限だと相手サービスと同期スレッドを消費させ放題になる
# ので、別の上限で止める(超えたら通常のロックと同じ2002)。記録も残す(2026-10-20 独立照査M-2)。
_ASK_MAX = 20
_ASK_WINDOW_SEC = 300.0
_ASK_KEYS_SOFT = 5000        # これを超えたら期限切れのIPを捨てる
_ASK_KEYS_HARD = 20000       # 期限切れを捨てても超えるなら、最終ヒットが古い順に捨てる(メモリの硬い上限)
_ask_hits: dict[str, list[float]] = {}
_ask_lock = threading.Lock()


def _rate_key(ip: str) -> str:
    """上限を数えるときのキー。IPv6は/64(1つの回線に配られる単位)でまとめる(同じ/64内でアドレスを
    変えても上限を回避できないように。仕様§5・2026-10-21 独立照査2回目M-3)。IPv4はそのまま。
    解釈できない文字列もそのまま。相手サービスへ送るipは生の文字列のまま(ここは数えるキーだけ)。"""
    s = (ip or "?").strip()
    try:
        a = ipaddress.ip_address(s.split("%", 1)[0])
    except ValueError:
        return s[:64]        # 解釈できない文字列は(長大でも)短く切ってキーにする
    if a.version == 6:
        if a.ipv4_mapped is not None:
            return str(a.ipv4_mapped)
        return "v6/" + a.packed[:8].hex()
    return str(a)


def ask_allowed(ip: str) -> bool:
    """このIPが確認を始めてよいか(許されるなら1回ぶん数える)。"""
    now = time.monotonic()
    key = _rate_key(ip)
    with _ask_lock:
        hits = [t for t in _ask_hits.get(key, []) if now - t < _ASK_WINDOW_SEC]
        if len(hits) >= _ASK_MAX:
            _ask_hits[key] = hits
            return False
        hits.append(now)
        _ask_hits[key] = hits
        if len(_ask_hits) > _ASK_KEYS_SOFT:      # 溜まりすぎたら古いIPから捨てる(メモリの上限)
            for k in [k for k, v in _ask_hits.items() if not v or now - v[-1] >= _ASK_WINDOW_SEC][:2500]:
                _ask_hits.pop(k, None)
            if len(_ask_hits) > _ASK_KEYS_HARD:
                oldest = sorted(_ask_hits, key=lambda k: _ask_hits[k][-1] if _ask_hits[k] else 0.0)
                for k in oldest[:len(_ask_hits) - _ASK_KEYS_HARD + 2500]:
                    if k != key:
                        _ask_hits.pop(k, None)
        return True


def ask_refund(ip: str) -> None:
    """確認の開始として数えた1回を取り消す。相手が「確認済みの端末(skip)」と答えたときに呼ぶ=
    本人のいつもの端末の連続ログインや、同じNAT・同じ/64の第三者の開始が、本人の上限を消費しないように
    (2026-10-21 独立照査3回目N-3)。"""
    with _ask_lock:
        hits = _ask_hits.get(_rate_key(ip))
        if hits:
            hits.pop()


def begin(ip: str, host: str, bind: str, cookie_header: str) -> Optional[dict]:
    """確認を始める。戻り値: {"mode":"ask","src":相対パス} / {"mode":"skip","ticket":..} / None(失敗)。"""
    d = _post("/internal/begin", {
        "ip": ip, "host": host, "bind": bind,
        "cookie": cookie_for_gate(cookie_header)})
    if not d:
        return None
    mode = d.get("mode")
    if mode == "ask":
        # askには、ブラウザをこの確認に束縛する短命のCookie(bind_cookie)が付く。これが無い/不正だと
        # 相手の画面は開けないので、失敗(2001)にする。
        src, bind_cookie = d.get("src"), _valid_cookie(d.get("bind_cookie"))
        if isinstance(src, str) and _SRC_RE.match(src) and bind_cookie is not None:
            return {"mode": "ask", "src": src, "bind_cookie": bind_cookie}
    elif mode == "skip":
        ticket = d.get("ticket")
        if isinstance(ticket, str) and _TICKET_RE.match(ticket):
            return {"mode": "skip", "ticket": ticket}
    log.warning("login_stepup: beginの応答が想定外")
    return None


def _valid_cookie(c) -> Optional[dict]:
    if not isinstance(c, dict):
        return None
    name, value = c.get("name"), c.get("value")
    max_age, path = c.get("max_age"), c.get("path")
    samesite = str(c.get("samesite", "")).lower()
    if not (isinstance(name, str) and _COOKIE_NAME_RE.match(name)):
        return None
    # このアプリ自身のCookie(セッション等)を相手の応答で上書きさせない
    if name in {auth.SESSION_COOKIE, auth.GUEST_SID_COOKIE, auth.INTERNAL_COOKIE}:
        return None
    if not (isinstance(value, str) and _COOKIE_VALUE_RE.match(value)):
        return None
    if not (isinstance(max_age, int) and not isinstance(max_age, bool)
            and 0 < max_age <= _MAX_COOKIE_AGE):
        return None
    if not (isinstance(path, str) and _COOKIE_PATH_RE.match(path)):
        return None
    if samesite not in ("lax", "strict", "none"):
        return None
    if not (isinstance(c.get("httponly"), bool) and isinstance(c.get("secure"), bool)):
        return None
    if samesite == "none" and not c["secure"]:      # ブラウザは保存しない組み合わせ(相手の値を疑う)
        return None
    return {"name": name, "value": value, "max_age": max_age, "path": path,
            "samesite": samesite, "httponly": c["httponly"], "secure": c["secure"]}


def redeem(ticket: str, ip: str, host: str, bind: str,
           accepted: bool) -> Optional[dict]:
    """チケットを引き換えて結果を得る(合否はここで初めて分かる)。
    戻り値: {"ok":bool,"cookie":検査済みの辞書|None} / None(失敗)。okなのにCookieが不正なら
    失敗(ok=False)にする(不正な値をブラウザに渡さない)。"""
    if not (isinstance(ticket, str) and _TICKET_RE.match(ticket)):
        return None
    d = _post("/internal/redeem", {
        "ticket": ticket, "ip": ip, "host": host, "bind": bind,
        "accepted": bool(accepted)})
    if not d or not isinstance(d.get("ok"), bool):
        return None
    if d["ok"] is not True:
        return {"ok": False, "cookie": None}
    raw = d.get("cookie")
    if raw is None:
        return {"ok": True, "cookie": None}
    cookie = _valid_cookie(raw)
    if cookie is None:
        log.warning("login_stepup: redeemのCookieが想定外の形(破棄)")
        return {"ok": False, "cookie": None}
    return {"ok": True, "cookie": cookie}


def check_password(user: Optional[dict], password: str) -> bool:
    """パスワードの検証。実在するかどうかにかかわらず必ずpbkdf2を1回走らせて時間を揃える
    (名簿の名前同士=管理者名とおとり名で、応答時間から区別されないようにする)。"""
    global _dummy_hash
    stored = (user or {}).get("password_hash") or ""
    if stored:
        return auth.verify_password(password, stored)
    if _dummy_hash is None:
        _dummy_hash = auth.hash_password(secrets.token_hex(16))
    auth.verify_password(password, _dummy_hash)
    return False
