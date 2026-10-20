"""ver1.5.19 ログインの追加確認(step-up)の受け口(app/services/login_stepup.py・/api/auth/login のフック)の検査。

一時データ領域(DATA_DIR)で動かし、本番にも開発DBにも触れない。確認サービスは scripts/stepup_stub_gate.py の
偽物(何も聞かない・採点しない・形だけ同じ)をこのプロセス内で動かす。外部通信はしない。
使い方: リポジトリ直下で `.venv/bin/python scripts/check_login_stepup.py`(全項目OKなら終了コード0)。

確かめること:
  A. 未設定なら従来どおり(管理者もパスワードだけで入れる・確認サービスには一切触れない)
  B. 名簿(管理者・無効な管理者・おとり名・大文字小文字違い)は、パスワードの正誤にかかわらず同じ応答で確認へ進む
     (正誤の合図にならない)。実在する一般ユーザー(おとり名と同じ綴りでも)は従来どおり
  C. 確認サービスへの要求の形(Bearer・X-Forwarded-Forなし・ip/host/bind/proto・Cookieのノイズ除去)
  D. 通過→パスワード正→成功(セッション+確認サービスのCookieを値も属性もそのまま)/ 通過+パスワード誤・未通過・
     使い回し・IP違い・無効な管理者は全て同じ2001でCookieなし・失敗は従来どおり数える・ロックはstep-upより先
  E. 「確認済みの端末」はサーバー側で毎回確かめ直す(ブラウザの申告では通れない)
  F. 相手が落ちている/遅い/キーが違う/変な応答(危険なsrc・不正なCookie等)は全て2001(fail-closed)・一般ユーザーは無影響
  G. 多層防御(名簿の判定が空振りしても、有効時に確認なしで管理者は通らない)・signupで管理者は作れない
  H. ログに共有キー・チケット・Cookie値が出ない
  I. 公開コードの衛生(ゲートの形を示す語がコード・公開ファイルに無い)・ログイン画面のJSの安全な受け取り・辞書4言語
"""
import hashlib, logging, os, re, sys, tempfile, time
from pathlib import Path

tmp = tempfile.mkdtemp(prefix="eigo_stepup_")
os.environ["DATA_DIR"] = tmp
os.environ["MULTIUSER"] = "1"
# 空文字で上書き(app.config の load_dotenv が親ディレクトリの.envから補うのを防ぐ)
for k in ("LOGIN_STEPUP_URL", "LOGIN_STEPUP_KEY", "LOGIN_STEPUP_DECOYS", "ALLOWED_HOSTS", "PUBLIC_BASE_URL"):
    os.environ[k] = ""
REPO = os.environ.get("REPO") or str(Path(__file__).resolve().parents[1])
sys.path.insert(0, REPO)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from fastapi.testclient import TestClient
import app.main as m
from app.config import log as app_log
from app.database import db, init_db
from app.routers import auth_routes
from app.services import auth, login_stepup
import stepup_stub_gate as stub

init_db()
ok = fail = 0
def check(label, cond, extra=""):
    global ok, fail
    if cond: ok += 1; print("OK  ", label)
    else: fail += 1; print("FAIL", label, extra)

class Capture(logging.Handler):
    def __init__(self): super().__init__(); self.msgs = []
    def emit(self, rec): self.msgs.append(rec.getMessage())
cap = Capture(); app_log.addHandler(cap)

PW = "Passw0rd!x1"
def mk(name, role="user", active=True):
    with db() as conn:
        r = auth.create_user(conn, name, PW, role=role)
        uid = r["id"] if isinstance(r, dict) else r
        if not active: conn.execute("UPDATE users SET is_active=0 WHERE id=?", (uid,))
    return uid
mk("adm_su", "admin"); mk("adm_off", "admin", active=False)
mk("usr_su"); mk("decoyuser")          # decoyuser: おとり名と同じ綴りの実在する一般ユーザー

gate, url, srv = stub.serve()
_n = iter(range(1, 250))
def new_ip(): return f"203.0.113.{next(_n)}"
def reset_locks():
    auth._LOGIN_FAILS.clear(); auth._IP_FAILS.clear(); auth._USERNAME_FAILS.clear()
def set_env(enabled=True, decoys="ghostadmin,decoyuser"):
    os.environ["LOGIN_STEPUP_URL"] = url if enabled else ""
    os.environ["LOGIN_STEPUP_KEY"] = gate.key
    os.environ["LOGIN_STEPUP_DECOYS"] = decoys

def login(username, password=PW, ticket=None, ip=None, https=False, cookie=None, host="study.nyangailab.com"):
    c = TestClient(m.app)          # 呼び出しごとに新しい(Cookieを引き継がない)
    h = {"X-Forwarded-For": ip or new_ip(), "Host": host}
    if https: h["X-Forwarded-Proto"] = "https"
    if cookie: h["Cookie"] = cookie
    body = {"username": username, "password": password}
    if ticket is not None: body["ticket"] = ticket
    return c.post("/api/auth/login", json=body, headers=h)

def setcookies(r): return r.headers.get_list("set-cookie")
def authck(r):
    """ゲストの識別Cookie(ela_gsid・失敗の応答にも従来から付く)を除いたSet-Cookie。"""
    return [x for x in setcookies(r) if not x.startswith(auth.GUEST_SID_COOKIE + "=")]
def no_fail_counts(*users):
    return (all(len(v) == 0 for v in auth._LOGIN_FAILS.values()) and all(len(v) == 0 for v in auth._IP_FAILS.values())
            and all(len(v) == 0 for v in auth._USERNAME_FAILS.values()))
def has_cookie(r, name): return any(x.startswith(name + "=") for x in setcookies(r))
def shape(r):
    j = r.json()
    return (r.status_code, tuple(sorted(j)), tuple(sorted(j.get("stepup", {}))),
            r.headers.get("content-type"), r.headers.get("cache-control"),
            bool(re.fullmatch(r"/g-stub/e\?c=[A-Za-z0-9_\-]+", j.get("stepup", {}).get("src", ""))),
            len(authck(r)))
def err_code(r):
    try: return r.json().get("code")
    except Exception: return None

# ---------------- A. 未設定なら従来どおり ----------------
print("== A. 未設定(従来どおり)")
set_env(enabled=False)
r = login("adm_su")
check("A1 未設定: 管理者はパスワードだけで入れる(従来どおり)", r.status_code == 200 and r.json().get("ok") is True and has_cookie(r, auth.SESSION_COOKIE))
r = login("usr_su")
check("A2 未設定: 一般ユーザーも従来どおり", r.status_code == 200 and r.json().get("ok") is True)
r = login("usr_su", "wrong")
check("A3 未設定: 誤パスワードは従来どおり2001/401", r.status_code == 401 and err_code(r) == "2001")
check("A4 未設定: 確認サービスには一切触れない", len(gate.log) == 0)
check("A5 enabled()はURL未設定でFalse", login_stepup.enabled() is False)

# ---------------- B. 名簿の応答は正誤で変わらない ----------------
print("== B. 名簿(正誤の合図にならない)")
reset_locks(); set_env()
check("B0 enabled()はURL設定でTrue", login_stepup.enabled() is True)
r_ok = login("adm_su", PW)
check("B1 管理者+正しいパスワード(ticketなし)=確認へ進む(200・ok:false・stepup.src・Cookieなし)",
      r_ok.status_code == 200 and r_ok.json().get("ok") is False and shape(r_ok)[5] and shape(r_ok)[6] == 0
      and not has_cookie(r_ok, auth.SESSION_COOKIE), r_ok.text)
base = shape(r_ok)
check("B2 管理者+誤ったパスワード=正しいパスワードと同じ形・同じ応答", shape(login("adm_su", "wrong-pass")) == base)
check("B3 おとり名(実在しない)=同じ形", shape(login("ghostadmin", PW)) == base)
check("B4 無効な管理者名=同じ形", shape(login("adm_off", PW)) == base)
check("B5 管理者名の大文字小文字違い=同じ形(取りこぼし防止)", shape(login("ADM_SU", PW)) == base)
check("B6 前後に空白のある管理者名=同じ形", shape(login("  adm_su ", PW)) == base)
check("B7 ticketなしの確認開始は失敗に数えない(ロック対象外)", no_fail_counts())
n_begin = len(gate.calls("/internal/begin"))
r = login("decoyuser", PW)
check("B8 おとり名と同じ綴りの実在する一般ユーザーは従来どおり入れる・確認サービスに触れない",
      r.status_code == 200 and r.json().get("ok") is True and len(gate.calls("/internal/begin")) == n_begin)
r = login("usr_su", PW)
check("B9 一般ユーザーは従来どおり入れる・確認サービスに触れない",
      r.status_code == 200 and r.json().get("ok") is True and len(gate.calls("/internal/begin")) == n_begin)
r = login("usr_su", "wrong")
check("B10 一般ユーザーの誤パスワードは従来どおり2001/401", r.status_code == 401 and err_code(r) == "2001")
r = login("nobody_xyz", PW)
check("B11 名簿にも実在もしない名前は従来どおり2001/401(確認へ進まない)", r.status_code == 401 and err_code(r) == "2001")

# ---------------- C. 確認サービスへの要求の形 ----------------
print("== C. 確認サービスへの要求")
gate.log.clear()
ip = new_ip()
r = login("adm_su", PW, ip=ip, https=True, cookie="_ga=GA1; ela_session=zzz; gx=abc; _gcl_au=2; ela_gsid=g1")
b = gate.calls("/internal/begin")
check("C1 beginが1回呼ばれる", len(b) == 1)
if b:
    h, body = b[0]["headers"], b[0]["body"]
    check("C2 Authorization: Bearer <共有キー>", h.get("authorization") == "Bearer " + gate.key)
    check("C3 X-Forwarded-Forを付けない", "x-forwarded-for" not in h)
    check("C4 ip=X-Forwarded-Forの一番右(real_client_ip)", body["ip"] == ip)
    check("C5 host=Hostヘッダ(小文字・ポート無し)", body["host"] == "study.nyangailab.com")
    check("C6 bind=ユーザー名のSHA-256", body["bind"] == hashlib.sha256(b"adm_su").hexdigest())
    check("C7 cookie=広告タグ・このアプリ自身のCookieを除いた残り", body["cookie"] == "gx=abc", body["cookie"])
check("C8 cookie_for_gate: 上限を超えたら空(あふれて毎回失敗するより安全側)", login_stepup.cookie_for_gate("a=" + "x" * 4000) == "")
check("C9 bind_for: 前後の空白は除く・大文字小文字は区別(get_user_by_nameに合わせる)",
      login_stepup.bind_for(" Admin ") == hashlib.sha256(b"Admin").hexdigest() != login_stepup.bind_for("admin"))

# ---------------- D. 通過→成功/失敗 ----------------
print("== D. チケットを使った最終判定")
def ask(username="adm_su", password=PW, ip=None, https=False, cookie=None):
    ip = ip or new_ip()
    r = login(username, password, ip=ip, https=https, cookie=cookie)
    return ip, gate.ticket_from_src(r.json().get("stepup", {}).get("src", "")), r

reset_locks(); gate.log.clear()
ip, t, _ = ask(https=True)
gate.complete(t, True)
r = login("adm_su", PW, ticket=t, ip=ip, https=True)
check("D1 通過+正しいパスワード=成功(ok:true・管理者)", r.status_code == 200 and r.json().get("ok") is True and r.json()["user"]["role"] == "admin", r.text)
check("D2 セッションCookieが付く", has_cookie(r, auth.SESSION_COOKIE))
gc = [x for x in setcookies(r) if x.startswith("gtest=")]
check("D3 確認サービスのCookieが付く(値も属性もそのまま: Max-Age=2592000・Path=/・HttpOnly・SameSite=lax・Secure(https)・Domainなし)",
      len(gc) == 1 and "Max-Age=2592000" in gc[0] and "Path=/" in gc[0] and "HttpOnly" in gc[0]
      and "SameSite=lax" in gc[0] and "Secure" in gc[0] and "Domain" not in gc[0] and gc[0].split("=", 1)[1].startswith("signed"), gc)
rd = gate.calls("/internal/redeem")[-1]["body"]
check("D4 redeem: ticket/ip/host/proto/accepted=true・bindはbeginと同じ",
      rd["ticket"] == t and rd["ip"] == ip and rd["host"] == "study.nyangailab.com" and rd["proto"] == "https" and rd["accepted"] is True
      and rd["bind"] == gate.calls("/internal/begin")[-1]["body"]["bind"])
r2 = login("adm_su", PW, ticket=t, ip=ip)
check("D5 同じチケットの使い回しは失敗(2001・Cookieなし)", r2.status_code == 401 and err_code(r2) == "2001" and not has_cookie(r2, auth.SESSION_COOKIE) and not has_cookie(r2, "gtest"))

# http(Secure無し)
ip, t, _ = ask(https=False); gate.complete(t, True)
r = login("adm_su", PW, ticket=t, ip=ip)
gc = [x for x in setcookies(r) if x.startswith("gtest=")]
check("D6 httpのときはSecureが付かない(確認サービスが決めた属性どおり)", len(gc) == 1 and "Secure" not in gc[0], gc)

# 通過+パスワード誤り
reset_locks()
ip, t, _ = ask(); gate.complete(t, True)
r = login("adm_su", "wrong-pass", ticket=t, ip=ip)
plain = login("usr_su", "wrong-pass")
check("D7 通過+誤ったパスワード=一般の誤パスワードと同じ2001/401(本文も同じ)", r.status_code == 401 and err_code(r) == "2001" and r.json() == plain.json(), r.text)
check("D8 そのときCookieは何も付かない(確認サービスのCookieも付けない)", not authck(r))
check("D9 redeemにはaccepted=falseが渡る", gate.calls("/internal/redeem")[-1]["body"]["accepted"] is False)
check("D10 失敗は従来どおり数える(user×IP・IP・username)",
      len(auth._LOGIN_FAILS.get(auth._login_key("adm_su", ip), [])) == 1 and len(auth._IP_FAILS.get(ip, [])) == 1 and len(auth._USERNAME_FAILS.get("adm_su", [])) == 1)
ev = None
with db() as conn:
    ev = conn.execute("SELECT success FROM login_log WHERE username='adm_su' ORDER BY id DESC LIMIT 1").fetchone()
check("D11 login_logに失敗として記録される", ev is not None and ev["success"] == 0)

# 未通過
reset_locks()
ip, t, _ = ask(); gate.complete(t, False)
r = login("adm_su", PW, ticket=t, ip=ip)
check("D12 確認を通っていない(相手がok:false)+正しいパスワード=2001・Cookieなし", r.status_code == 401 and err_code(r) == "2001" and not authck(r))
check("D13 そのときaccepted=true(パスワードは合っていたので相手の失敗数を取り消せる側に倒さない=相手の仕様どおり渡す)", gate.calls("/internal/redeem")[-1]["body"]["accepted"] is True)
# 通過+無効な管理者
ip, t, _ = ask("adm_off"); gate.complete(t, True)
r = login("adm_off", PW, ticket=t, ip=ip)
check("D14 通過+正しいパスワードでも、無効な管理者は2001", r.status_code == 401 and err_code(r) == "2001" and not authck(r))
check("D15 無効な管理者ではaccepted=false(実在する有効なadminだけtrue)", gate.calls("/internal/redeem")[-1]["body"]["accepted"] is False)
# おとり名で通過
ip, t, _ = ask("ghostadmin"); gate.complete(t, True)
r = login("ghostadmin", PW, ticket=t, ip=ip)
check("D16 おとり名は通過しても必ず2001", r.status_code == 401 and err_code(r) == "2001" and not authck(r))
# IP違い(相手がbindの不一致で落とす)
ip, t, _ = ask(); gate.complete(t, True)
r = login("adm_su", PW, ticket=t, ip=new_ip())
check("D17 発行したIPと違うIPからの引き換えは失敗(2001)", r.status_code == 401 and err_code(r) == "2001")
# 別ユーザー名でチケットを使う
ip, t, _ = ask("adm_su"); gate.complete(t, True)
mk("adm_two", "admin")
r = login("adm_two", PW, ticket=t, ip=ip)
check("D18 別のユーザー名(bind違い)でチケットを使えない", r.status_code == 401 and err_code(r) == "2001")
# ロックはstep-upより先
reset_locks()
ip = new_ip()
for _ in range(3):
    _, t, _ = ask("adm_su", PW, ip=ip); gate.complete(t, True)
    login("adm_su", "wrong-pass", ticket=t, ip=ip)
n_begin = len(gate.calls("/internal/begin"))
r = login("adm_su", PW, ip=ip)
check("D19 3回失敗するとロック(2002/429)・確認サービスにも触れない(ロック判定はstep-upより先)",
      r.status_code == 429 and err_code(r) == "2002" and len(gate.calls("/internal/begin")) == n_begin)
reset_locks()

# ---------------- E. 確認済みの端末はサーバーで毎回確かめ直す ----------------
print("== E. skip(確認済みの端末)")
gate.log.clear()
ip = new_ip()
r = login("adm_su", PW, ip=ip, cookie=gate.valid_cookie)
check("E1 確認済みCookie+正しいパスワード=ticketなしでも成功(サーバーがbeginでskipと確認→引き換え)",
      r.status_code == 200 and r.json().get("ok") is True and has_cookie(r, auth.SESSION_COOKIE), r.text)
check("E2 skipのときは確認サービスのCookieを付け直さない(cookie=null)", not has_cookie(r, "gtest"))
check("E3 begin→redeemの順に1回ずつ呼ばれる", len(gate.calls("/internal/begin")) == 1 and len(gate.calls("/internal/redeem")) == 1)
r = login("adm_su", "wrong-pass", ip=new_ip(), cookie=gate.valid_cookie)
check("E4 確認済みでも誤ったパスワードは2001", r.status_code == 401 and err_code(r) == "2001" and not authck(r))
r = login("adm_su", PW, ip=new_ip(), cookie="gatetest=NG")
check("E5 確認済みCookieが無効ならskipにならず確認へ(ブラウザの申告では通れない)", r.status_code == 200 and r.json().get("ok") is False and "stepup" in r.json())
r = login("adm_su", PW, ip=new_ip(), ticket="")
check("E6 ticketを空で送っても通れない(確認へ進む)", r.json().get("ok") is False and "stepup" in r.json())
r = login("adm_su", PW, ip=new_ip(), ticket="A" * 40)
check("E7 でたらめなticketでは通れない(2001)", r.status_code == 401 and err_code(r) == "2001")

# ---------------- F. 相手の不調・誤動作(fail-closed) ----------------
print("== F. fail-closed")
def expect_fail(label, **kw):
    t0 = time.monotonic()
    r = login("adm_su", PW, **kw)
    check(label, r.status_code == 401 and err_code(r) == "2001" and not authck(r), (r.status_code, r.text, authck(r)))
    return time.monotonic() - t0
for ov, label in (("bad_src_slashes", "F1 srcが//で始まる(別サイトへ誘導)"), ("bad_src_absolute", "F2 srcが絶対URL"),
                  ("bad_src_backslash", "F3 srcにバックスラッシュ"), ("no_mode", "F4 modeが無い応答"),
                  ("bad_ticket_chars", "F5 skipのticketが不正な文字"), ("http500", "F6 相手が500")):
    reset_locks(); gate.override = ov
    expect_fail(label + " → 2001(ブラウザに中継しない)")
    gate.override = None
for ov, label in (("bad_cookie_value", "F7 redeemのCookie値に;を含む"), ("bad_cookie_missing", "F8 redeemのCookieに属性が欠ける"),
                  ("bad_cookie_name", "F9 redeemのCookie名が不正"), ("bad_cookie_age", "F10 redeemのCookieのmax_ageが不正")):
    reset_locks(); gate.override = None
    ip, t, _ = ask(); gate.complete(t, True); gate.override = ov
    expect_fail(label + " → 2001(不正な値をブラウザに渡さない・セッションも発行しない)", ticket=t, ip=ip)
    gate.override = None
reset_locks(); gate.override = "slow"
dt = expect_fail("F11 相手が遅い(3秒)→ 2001")
check("F11b タイムアウトは2秒前後で打ち切る(3.0秒未満)", dt < 3.0, f"{dt:.2f}s")
gate.override = None
reset_locks(); os.environ["LOGIN_STEPUP_KEY"] = "wrong-key"
expect_fail("F12 共有キーが違う(相手は404)→ 2001")
r = login("usr_su"); check("F12b そのとき一般ユーザーは無影響", r.status_code == 200 and r.json().get("ok") is True)
os.environ["LOGIN_STEPUP_KEY"] = ""
reset_locks(); expect_fail("F13 共有キーが未設定(URLだけ有効)→ 2001(素通しにならない)")
os.environ["LOGIN_STEPUP_KEY"] = gate.key

# ---------------- G. 多層防御 ----------------
print("== G. 多層防御")
reset_locks()
orig = login_stepup.in_roster
login_stepup.in_roster = lambda conn, u: False
r = login("adm_su", PW)
check("G1 名簿の判定が空振りしても、有効時は確認なしで管理者を通さない(2001)", r.status_code == 401 and err_code(r) == "2001" and not has_cookie(r, auth.SESSION_COOKIE))
r = login("usr_su", PW)
check("G2 そのとき一般ユーザーは通る", r.status_code == 200 and r.json().get("ok") is True)
login_stepup.in_roster = orig
import inspect
check("G3 signupはroleを受け取らない・渡さない(管理者を作れない)",
      "role" not in auth_routes.SignupIn.model_fields and "role=" not in inspect.getsource(auth_routes.signup))
check("G4 create_userの既定はrole=user", inspect.signature(auth.create_user).parameters["role"].default == "user")

# ---------------- 最後に落ちている相手 ----------------
print("== F'. 相手が落ちている")
srv.shutdown(); srv.server_close()
reset_locks()
t0 = time.monotonic()
r = login("adm_su", PW)
check("F14 相手が落ちている → 管理者は2001(素通しにならない)・数秒以内", r.status_code == 401 and err_code(r) == "2001" and time.monotonic() - t0 < 3.5)
r = login("usr_su"); check("F15 相手が落ちていても一般ユーザーは無影響", r.status_code == 200 and r.json().get("ok") is True)
set_env(enabled=False)
r = login("adm_su"); check("F16 URLを外すとフック無効(従来どおり=ブレーキの手順)", r.status_code == 200 and r.json().get("ok") is True)

# ---------------- H. ログ ----------------
print("== H. ログ")
secrets_seen = {gate.key, "wrong-key"}
for x in gate.log:
    b = x["body"]
    if isinstance(b.get("ticket"), str): secrets_seen.add(b["ticket"])
joined = "\n".join(cap.msgs)
check("H1 ログに共有キー・チケット・パスワードが出ていない", not any(s and s in joined for s in secrets_seen) and PW not in joined)
check("H2 ログに確認サービスのCookie値が出ていない", "signed" not in joined)

# ---------------- I. 公開コードの衛生・ログイン画面 ----------------
print("== I. 公開コードの衛生・画面")
root = Path(REPO)
# 「ゲートの形を示す語」の一覧は公開リポジトリに置かない(一覧自体が手がかりになるため)。非公開の語リスト
# (1行1語)のパスを環境変数 STEPUP_HYGIENE_WORDS で渡す。未指定ならこの項目だけ飛ばす(OK/FAILに数えない)。
words_file = os.environ.get("STEPUP_HYGIENE_WORDS", "")
if words_file and Path(words_file).is_file():
    banned = [w.strip() for w in Path(words_file).read_text(encoding="utf-8").splitlines() if w.strip()]
    # scripts/ には一般の単語を含む語彙の追加スクリプトが大量にあるので、このログイン統合の
    # 新規ファイルだけを対象にする(app/static/templates/deployは全体)。
    scan = [root / "app", root / "static", root / "templates", root / "README.md", root / "deploy", root / ".env.example",
            root / "scripts/check_login_stepup.py", root / "scripts/check_login_stepup_ui.py",
            root / "scripts/stepup_stub_gate.py", root / "CHANGELOG.md", root / "release_notes.json"]
    hits = []
    for base in scan:
        files = [base] if base.is_file() else [p for p in base.rglob("*") if p.is_file() and p.suffix in (".py", ".js", ".html", ".md", ".sh", ".yml", ".snippet", ".json", ".txt", ".example")]
        for p in files:
            try: txt = p.read_text(encoding="utf-8")
            except Exception: continue
            for w in banned:
                if w in txt: hits.append((str(p.relative_to(root)), w))
    check(f"I1 公開コード・公開ファイル(app/static/templates/deploy/このログイン統合のscripts/CHANGELOG/release_notes)に、非公開の語リスト{len(banned)}語が1つも無い", not hits, hits[:5])
else:
    print("SKIP I1 公開コードの語の混入検査(STEPUP_HYGIENE_WORDS=非公開の語リストのパスが未指定)")
leak = [str(p.relative_to(root)) for base in (root / ".env.example", root / "README.md", root / "deploy") if base.exists()
        for p in ([base] if base.is_file() else base.rglob("*")) if p.is_file() and "LOGIN_STEPUP" in p.read_text(encoding="utf-8", errors="ignore")]
check("I2 環境変数名(LOGIN_STEPUP_*)は.env.example・README・deployに載せていない", not leak, leak)
html = (root / "static/login.html").read_text(encoding="utf-8")
check("I3 画面: iframeからのメッセージは origin と source を両方検査する", "ev.origin !== location.origin" in html and "ev.source !== stepupFrame.contentWindow" in html)
check("I4 画面: srcは同一オリジンの相対パスだけ・ticketは形を検査", "STEPUP_SRC_RE" in html and "STEPUP_TICKET_RE" in html and r"^\/(?!\/)" in html)
check("I5 画面: iframeはno-referrer・キャンセルとEscで閉じられる", "no-referrer" in html and "closeStepup" in html and "Escape" in html)
d = (root / "static/js/i18n_dict.js").read_text(encoding="utf-8")
for key in ("login.stepup.title", "login.stepup.cancel", "login.stepup.locked"):
    check(f"I6 辞書に{key}が4言語ぶんある", d.count(f'"{key}"') == 4)
zh_cn_locked = re.search(r'"login\.stepup\.locked": "([^"]+)"', d.split('"login.networkError": "发生通信错误。"')[1]).group(1)
check("I7 簡体字の文言に繁体字が混ざらない(稍候/过/会儿)", "請" not in zh_cn_locked and "過" not in zh_cn_locked and "會" not in zh_cn_locked, zh_cn_locked)
check("I8 日本語以外の辞書にかなが混ざらない", not re.search(r"[぀-ヿ]", "".join(re.findall(r'"login\.stepup\.[a-z]+": "([^"]+)"', d)[3:])))

print(f"\n== 結果: OK {ok} / FAIL {fail}")
sys.exit(0 if fail == 0 else 1)
