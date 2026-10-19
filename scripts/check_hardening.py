"""ver1.5.17(セキュリティ向上P4: パス判定をscope["path"]へ・許可Host制限・PayPay戻りURLの固定化)のローカル検査。
一時データ領域(DATA_DIR)で動かし、本番にも開発DBにも触れない。PayPay APIは差し替えて外部へ出さない。
使い方: リポジトリ直下で `.venv/bin/python scripts/check_hardening.py`(全項目OKなら終了コード0)。
内部で自分自身を `child` モード(ALLOWED_HOSTS/PUBLIC_BASE_URL設定あり)でも別プロセス実行する。"""
import os, subprocess, sys, tempfile, time
from pathlib import Path

CHILD = len(sys.argv) > 1 and sys.argv[1] == "child"
tmp = tempfile.mkdtemp(prefix="eigo_hard_")
os.environ["DATA_DIR"] = tmp
os.environ["MULTIUSER"] = "1"
# 空文字で上書き(popだと app.config の load_dotenv が親ディレクトリの.envから補ってしまう)
os.environ["PUBLIC_BASE_URL"] = ""
os.environ["ALLOWED_HOSTS"] = ""
if CHILD:
    os.environ["ALLOWED_HOSTS"] = "study.nyangailab.com"
    os.environ["PUBLIC_BASE_URL"] = "https://study.nyangailab.com/"
REPO = os.environ.get("REPO") or str(Path(__file__).resolve().parents[1])
sys.path.insert(0, REPO)

from fastapi.testclient import TestClient
from starlette.requests import Request
import app.main as m
from app.database import db, init_db
from app.routers import paypay_charge, paypay_test
from app.services import auth, paypay

init_db()
ok = fail = 0
def check(label, cond, extra=""):
    global ok, fail
    if cond: ok += 1; print("OK  ", label)
    else: fail += 1; print("FAIL", label, extra)

def mk(name, role):
    with db() as conn:
        r = auth.create_user(conn, name, "Passw0rd!x1", role=role)
        return r["id"] if isinstance(r, dict) else r
admin, normal = mk("adm_h", "admin"), mk("usr_h", "user")

def cookie(uid):
    with db() as conn:
        secret = auth.get_session_secret(conn)
        epoch = auth.get_session_epoch(conn, uid)
    return {auth.SESSION_COOKIE: auth.make_session_token(secret, uid, epoch, int(time.time()))}

def fake_request(headers: dict, scheme="http", host="testserver"):
    hs = [(k.lower().encode(), v.encode()) for k, v in {"host": host, **headers}.items()]
    return Request({"type": "http", "method": "POST", "path": "/", "headers": hs,
                    "scheme": scheme, "server": (host, 80), "query_string": b""})

# --- A. public_base_url(PayPay戻りURLの土台) ---
def pb(req): return auth.public_base_url(req)
if not CHILD:
    check("未設定: 本番ドメインのHost+X-Forwarded-Protoから組み立てる(従来どおり)",
          pb(fake_request({"x-forwarded-proto": "https"}, host="study.nyangailab.com")) == "https://study.nyangailab.com")
    check("未設定: localhostは直接のスキーム(http)", pb(fake_request({}, host="localhost:8000")) == "http://localhost:8000")
    check("未設定: 知らないHostは本番ドメインに固定(Host偽装で戻り先をすり替えられない)",
          pb(fake_request({"x-forwarded-proto": "https"}, host="evil.example")) == "https://study.nyangailab.com")
    os.environ["PUBLIC_BASE_URL"] = "https://study.nyangailab.com/"
    check("設定あり: 末尾/を除いた固定URLを返す",
          pb(fake_request({"x-forwarded-proto": "http"}, host="evil.example")) == "https://study.nyangailab.com")
    os.environ["PUBLIC_BASE_URL"] = "HTTPS://Study.Nyangailab.com:8443"
    check("大文字のスキームも受け付け、正規化して返す", pb(fake_request({}, host="x")) == "https://Study.Nyangailab.com:8443")
    for bad in ("study.nyangailab.com", "https://study.nyangailab.com/app", "https://u:p@study.nyangailab.com",
                "https://study.nyangailab.com?x=1", "https://study nyangailab.com", "ftp://study.nyangailab.com"):
        os.environ["PUBLIC_BASE_URL"] = bad
        got = pb(fake_request({"x-forwarded-proto": "https"}, host="evil.example"))
        check(f"不正な設定 '{bad}' は無視して本番ドメインに固定(壊れたリンクを配らない)", got == "https://study.nyangailab.com", got)
    os.environ["PUBLIC_BASE_URL"] = ""
    from app.routers import password_reset
    os.environ["PUBLIC_BASE_URL"] = "https://study.nyangailab.com"
    check("パスワード再発行リンクと決済の戻りURLが同じ組み立て",
          password_reset._public_base(fake_request({}, host="evil.example")) == pb(fake_request({}, host="evil.example")))
    os.environ["PUBLIC_BASE_URL"] = ""

# --- B. PayPayの作成APIが渡す戻りURL(エンドツーエンド・外部APIは差し替え) ---
captured = []
def fake_create_code(mpid, amount, redirect_url, order_description=""):
    captured.append(redirect_url)
    return {"data": {"url": "https://pay.example/x", "codeId": "c1"}}
paypay.create_code = fake_create_code

def create_urls(c, path):
    captured.clear()
    r = c.post(path, json={"amount_jpy": 800}, headers=HDR)
    return r, (captured[-1] if captured else None)

base = "https://study.nyangailab.com" if CHILD else "http://testserver"
HDR = {"host": "evil.example", "x-forwarded-proto": "https"} if not CHILD else {"host": "study.nyangailab.com", "x-forwarded-proto": "http"}
with TestClient(m.app, base_url=base, follow_redirects=False) as c:
    c.cookies.update(cookie(admin))
    for label, path, ret in (("PayPay課金", "/api/paypay/create", "/api/paypay/return"),
                             ("PayPayテスト", "/api/paypay-test/create", "/api/paypay-test/return")):
        r, url = create_urls(c, path)
        if CHILD:
            check(f"固定URL設定あり: {label}の戻りURLはHost/プロキシヘッダに左右されない",
                  url is not None and url.startswith("https://study.nyangailab.com" + ret + "?mpid="), (r.status_code, url))
        else:
            # 未設定: 知らないHostは本番ドメインに固定される(Host偽装で戻り先を変えられない)
            check(f"未設定: {label}の戻りURLは知らないHostでも本番ドメイン",
                  url is not None and url.startswith("https://study.nyangailab.com" + ret + "?mpid="), (r.status_code, url))

    # --- C. 認可のパス判定: 変なHostでも通常のHostと同じ判定 ---
    c.cookies.clear()
    if not CHILD:
        weird = ["a/api/health#", "evil.com/api/health?", "x.com\\@y/api/health", "/api/health", "[::1]/api/health"]
        for h in weird:
            try:
                r = c.get("/api/auth/me", headers={"host": h})
                good = r.status_code in (401, 400, 404, 307, 303)
                check(f"変なHost '{h}' でも未ログインの/api/auth/meは通らない", good, r.status_code)
            except Exception as e:  # httpx側がHostを拒否する形も許容(到達しない=安全)
                check(f"変なHost '{h}' はクライアント側で拒否(到達せず)", True, str(e)[:60])
        r = c.get("/api/auth/me", headers={"host": "testserver"})
        check("通常Host: 未ログインの/api/auth/meは401", r.status_code == 401, r.status_code)
        r = c.get("/api/health", headers={"host": "evil.example"})
        check("許可Host未設定: 任意のHostでも/api/healthは200(従来どおり)", r.status_code == 200, r.status_code)
        check("main.pyにrequest.url.pathが残っていない", "request.url.path" not in Path(REPO, "app/main.py").read_text(encoding="utf-8"))

    # --- D. 許可Host制限(childのみ) ---
    if CHILD:
        r = c.get("/api/health", headers={"host": "study.nyangailab.com"})
        check("許可Host: 200", r.status_code == 200, r.status_code)
        r = c.get("/api/health", headers={"host": "study.nyangailab.com:443"})
        check("許可Host(ポート付き): 200", r.status_code == 200, r.status_code)
        for h in ("evil.example", "study.nyangailab.com.evil.example", "ailab.nyangailab.com"):
            r = c.get("/api/health", headers={"host": h})
            check(f"許可外Host '{h}': 400", r.status_code == 400, r.status_code)
        for h in ("127.0.0.1:8000", "localhost:8000"):
            r = c.get("/api/health", headers={"host": h})
            check(f"ループバック '{h}'(Dockerのヘルスチェック): 200", r.status_code == 200, r.status_code)
        r = c.get("/admin/fulfillment", headers={"host": "evil.example"})
        check("許可外Hostでは管理ページの手前で400(認証処理に入らない)", r.status_code == 400, r.status_code)

print(f"\n{'child' if CHILD else 'main'}: ok={ok} fail={fail}")
rc = 1 if fail else 0
if not CHILD:
    p = subprocess.run([sys.executable, __file__, "child"], env={**os.environ, "REPO": REPO})
    rc = rc or p.returncode
sys.exit(rc)
