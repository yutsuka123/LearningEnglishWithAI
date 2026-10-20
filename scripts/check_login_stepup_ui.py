"""ver1.5.19 ログインの追加確認(step-up)の画面側(static/login.html)の実ブラウザ検査。

**隔離サーバー専用・本番には絶対に向けない**。アプリを一時データ領域でuvicornとして起動し、確認サービスは
scripts/stepup_stub_gate.py の偽物をこのプロセス内で動かす。iframeの中身(確認サービスの画面)は
Playwrightのrouteで「合否にかかわらず終了したらpostMessageを送るだけの偽の画面」に差し替える。
Googleタグ入りのページを動かすため、アプリ(127.0.0.1)以外への通信は**全て止める**(本番のGoogle広告アカウントへは何も届かない)。

使い方: リポジトリ直下で `.venv/bin/python scripts/check_login_stepup_ui.py [--browsers chromium,webkit]`
確かめること:
  1. 一般ユーザー: 従来どおり(iframeは出ない)
  2. 管理者: iframeが開く→終了のpostMessage→同じ入力で再送→成功(セッション+確認サービスのCookie)
  3. 管理者(誤パスワード)・おとり名: iframeが同じように開き、最後に同じ失敗文言(正誤が画面に出ない)
  4. キャンセル/Escで閉じる・閉じた後は再送しない
  5. 待ち(st-locked)の表示・自分のiframe以外(ページ自身)からのメッセージは無視
  6. 確認済みの端末(skip)はiframeなしで入れる
  7. 相手が落ちていても画面は固まらず失敗文言を出す
  8. 4言語の文言・スマホ幅でiframeの枠が画面に収まる
"""
import argparse, json, os, socket, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ap = argparse.ArgumentParser()
ap.add_argument("--browsers", default="chromium,webkit")
args = ap.parse_args()

tmp = tempfile.mkdtemp(prefix="eigo_stepup_ui_")
REPO = os.environ.get("REPO") or str(Path(__file__).resolve().parents[1])
sys.path.insert(0, REPO); sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.update({"DATA_DIR": tmp, "MULTIUSER": "1", "LOGIN_STEPUP_URL": "", "LOGIN_STEPUP_KEY": "",
                   "LOGIN_STEPUP_DECOYS": "", "ALLOWED_HOSTS": "", "PUBLIC_BASE_URL": ""})
from app.database import db, init_db
from app.services import auth
import stepup_stub_gate as stub

init_db()
PW = "Passw0rd!x1"
with db() as conn:
    for name, role in (("ui_admin", "admin"), ("ui_user", "user")):
        auth.create_user(conn, name, PW, role=role)

gate, gate_url, gate_srv = stub.serve()
s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
BASE = f"http://127.0.0.1:{port}"
env = dict(os.environ, ALLOW_FRESH_DB="1", SESSION_SECRET="preview", OPENAI_API_KEY="preview-not-used",
           LOGIN_STEPUP_URL=gate_url, LOGIN_STEPUP_KEY=gate.key, LOGIN_STEPUP_DECOYS="ui_ghost")
server = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port), "--log-level", "warning"],
                          cwd=REPO, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(60):
        try:
            if urllib.request.urlopen(BASE + "/api/health", timeout=1).status == 200: break
        except Exception: time.sleep(0.5)
    else:
        raise SystemExit("サーバーが起動しない")

    from playwright.sync_api import sync_playwright
    ok = fail = 0
    def check(label, cond, extra=""):
        global ok, fail
        if cond: ok += 1; print("OK  ", label)
        else: fail += 1; print("FAIL", label, extra)

    def run(pw, bname):
        P = bname + ": "
        state = {"mode": "pass", "delay": 700}
        blocked = []
        def guard(route):
            u = route.request.url
            if u.startswith(BASE): return route.continue_()
            blocked.append(u); return route.abort()
        def gate_page(route):
            c = parse_qs(urlparse(route.request.url).query).get("c", [""])[0]
            mode = state["mode"]
            if mode in ("pass", "fail") and c in gate.tickets:
                gate.complete(c, mode == "pass")
            msg = {"t": "st-locked"} if mode == "locked" else {"t": "st", "ticket": c}
            html = ("<!doctype html><meta charset=utf-8><body>stub<script>setTimeout(function(){parent.postMessage("
                    + json.dumps(msg) + ", location.origin)}, " + str(state["delay"]) + ")</script>")
            route.fulfill(status=200, content_type="text/html", body=html,
                          headers={"X-Frame-Options": "SAMEORIGIN", "Content-Security-Policy": "frame-ancestors 'self'"})
        browser = getattr(pw, bname).launch()
        def new_page(lang=None, viewport=None, cookies=None):
            ctx = browser.new_context(locale="ja-JP", viewport=viewport or {"width": 1100, "height": 800})
            ctx.route("**/*", guard)
            ctx.route("**/g-stub/e**", gate_page)
            if lang: ctx.add_init_script(f"try {{ localStorage.setItem('lang', {json.dumps(lang)}); }} catch (e) {{}}")
            if cookies: ctx.add_cookies(cookies)
            page = ctx.new_page()
            reqs = []
            page.on("request", lambda r: reqs.append(r) if r.url.endswith("/api/auth/login") else None)
            page.goto(BASE + "/login"); page.wait_for_selector("#u")
            return ctx, page, reqs
        def fill_submit(page, u, p):
            page.fill("#u", u); page.fill("#p", p)
            page.click("#f button[type=submit]")
        def cookie_names(ctx): return {c["name"] for c in ctx.cookies()}

        # 1. 一般ユーザー
        state.update(mode="pass", delay=700); ctx, page, reqs = new_page()
        fill_submit(page, "ui_user", PW)
        page.wait_for_url(lambda u: "/login" not in u, timeout=15000)
        check(P + "1 一般ユーザー: iframeなしで従来どおり入れる", auth.SESSION_COOKIE in cookie_names(ctx) and len(reqs) == 1)
        ctx.close()

        # 2. 管理者の成功
        ctx, page, reqs = new_page()
        fill_submit(page, "ui_admin", PW)
        page.wait_for_selector(".stepup-box iframe", timeout=5000)
        src = page.get_attribute(".stepup-box iframe", "src")
        check(P + "2a 管理者: 確認のiframeが開く(同一オリジンの相対パス)", src.startswith("/g-stub/e?c="), src)
        check(P + "2b iframeにはno-referrerとtitleが付く", page.get_attribute(".stepup-box iframe", "referrerpolicy") == "no-referrer"
              and bool(page.get_attribute(".stepup-box iframe", "title")))
        check(P + "2c iframeが開いている間は再送していない(ログイン要求は1回だけ)", len(reqs) == 1)
        page.wait_for_url(lambda u: "/login" not in u, timeout=15000)
        names = cookie_names(ctx)
        check(P + "2d 終了後に同じ入力で再送→成功(セッションCookie+確認サービスのCookie)", auth.SESSION_COOKIE in names and "gtest" in names, names)
        check(P + "2e 再送にはticketが付く・パスワードも付く", len(reqs) == 2 and '"ticket"' in (reqs[1].post_data or "") and '"password"' in (reqs[1].post_data or ""))
        ctx.close()

        # 3. 失敗は正誤が画面に出ない
        def failing(user, pw_, label):
            state.update(mode="pass", delay=700); c2, pg, rq = new_page()
            fill_submit(pg, user, pw_)
            pg.wait_for_selector(".stepup-box iframe", timeout=5000)
            pg.wait_for_function("() => !document.querySelector('.stepup-box')", timeout=8000)
            pg.wait_for_function("() => document.getElementById('e').textContent.length > 0", timeout=8000)
            msg = pg.inner_text("#e")
            out = ("/login" in pg.url, msg, auth.SESSION_COOKIE in cookie_names(c2) or "gtest" in cookie_names(c2), len(rq))
            c2.close(); return out
        a = failing("ui_admin", "wrong-pass", "wrong")
        b = failing("ui_ghost", PW, "decoy")
        c_ = failing("ui_admin", "wrong-pass2", "wrong2")
        check(P + "3a 管理者(誤パスワード): iframe→失敗文言・ログインされない", a[0] and a[1] != "" and not a[2] and a[3] == 2, a)
        check(P + "3b おとり名・誤パスワードの管理者は、同じ流れ(iframe→2回送信)・同じ失敗文言(正誤が画面に出ない)", a == b == c_ or (a[1] == b[1] == c_[1] and a[3] == b[3] == c_[3]), (a, b, c_))

        # 4. キャンセル・Esc
        state.update(mode="pass", delay=3000); ctx, page, reqs = new_page()
        fill_submit(page, "ui_admin", PW)
        page.wait_for_selector(".stepup-box iframe", timeout=5000)
        page.click(".stepup-cancel")
        check(P + "4a キャンセルでiframeが閉じる", page.query_selector(".stepup-box") is None)
        time.sleep(3.6)
        check(P + "4b 閉じた後は再送されない(ログイン要求は最初の1回だけ)", len(reqs) == 1 and "/login" in page.url)
        fill_submit(page, "ui_admin", PW)
        page.wait_for_selector(".stepup-box iframe", timeout=5000)
        page.keyboard.press("Escape")
        check(P + "4c Escでも閉じる", page.query_selector(".stepup-box") is None)
        ctx.close()

        # 5. 待ち表示・自分のiframe以外からのメッセージは無視
        state.update(mode="locked", delay=500); ctx, page, reqs = new_page()
        fill_submit(page, "ui_admin", PW)
        page.wait_for_function("() => !document.querySelector('.stepup-box') && document.getElementById('e').textContent.length > 0", timeout=8000)
        check(P + "5a st-locked: iframeを閉じて待ちの文言を出す・再送しない", len(reqs) == 1 and "しばらく" in page.inner_text("#e"), page.inner_text("#e"))
        ctx.close()
        state.update(mode="pass", delay=3000); ctx, page, reqs = new_page()
        fill_submit(page, "ui_admin", PW)
        page.wait_for_selector(".stepup-box iframe", timeout=5000)
        page.evaluate("window.postMessage({t:'st', ticket:'AAAAAAAAAAAAAAAAAAAA'}, location.origin)")
        time.sleep(0.6)
        check(P + "5b ページ自身(iframe以外)からのメッセージは無視する(再送されない)", len(reqs) == 1 and page.query_selector(".stepup-box") is not None)
        page.keyboard.press("Escape"); ctx.close()

        # 6. skip(確認済みの端末)
        ctx, page, reqs = new_page(cookies=[{"name": "gatetest", "value": "OK", "url": BASE}])
        fill_submit(page, "ui_admin", PW)
        page.wait_for_url(lambda u: "/login" not in u, timeout=15000)
        check(P + "6 確認済みの端末: iframeなしで入れる(サーバーが確かめた結果)", auth.SESSION_COOKIE in cookie_names(ctx) and len(reqs) == 1)
        ctx.close()

        # 8. 4言語・スマホ幅
        for lang, cancel, locked in (("ja", "キャンセル", "しばらく"), ("en", "Cancel", "Please wait"),
                                     ("zh-CN", "取消", "请稍候"), ("zh-TW", "取消", "請稍候")):
            state.update(mode="pass", delay=3000)
            ctx, page, reqs = new_page(lang=lang, viewport={"width": 360, "height": 640})
            fill_submit(page, "ui_admin", PW)
            page.wait_for_selector(".stepup-box iframe", timeout=5000)
            txt = page.inner_text(".stepup-cancel")
            geo = page.evaluate("""() => { const p = document.querySelector('.stepup-panel').getBoundingClientRect();
              const f = document.querySelector('.stepup-box iframe').getBoundingClientRect();
              return {pl: p.left, pr: p.right, fw: f.width, vw: window.innerWidth, ph: p.bottom,
                      vh: window.innerHeight, sw: document.scrollingElement.scrollWidth, cw: document.scrollingElement.clientWidth}; }""")
            check(P + f"8 {lang}: キャンセルの文言・360px幅で枠が画面に収まり横スクロールなし",
                  txt == cancel and geo["pl"] >= 0 and geo["pr"] <= geo["vw"] and geo["ph"] <= geo["vh"] + 1 and geo["sw"] <= geo["cw"], (txt, geo))
            page.keyboard.press("Escape")
            state.update(mode="locked", delay=300)
            fill_submit(page, "ui_admin", PW)
            page.wait_for_function("() => !document.querySelector('.stepup-box') && document.getElementById('e').textContent.length > 0", timeout=8000)
            check(P + f"8 {lang}: 待ちの文言", locked in page.inner_text("#e"), page.inner_text("#e"))
            ctx.close()

        print(f"INFO {P}アプリ以外への通信を遮断した件数: {len(blocked)}(Googleタグ等・全て中断済み=外へは出ていない)")
        browser.close()

    with sync_playwright() as pw:
        for b in [x.strip() for x in args.browsers.split(",") if x.strip()]:
            print(f"== {b}")
            run(pw, b)

    # 7. 相手が落ちている(最後に1回だけ・chromiumで)
    with sync_playwright() as pw:
        browser = pw.chromium.launch()
        ctx = browser.new_context(); ctx.route("**/*", lambda r: r.continue_() if r.request.url.startswith(BASE) else r.abort())
        gate_srv.shutdown(); gate_srv.server_close()
        page = ctx.new_page(); page.goto(BASE + "/login"); page.wait_for_selector("#u")
        page.fill("#u", "ui_admin"); page.fill("#p", PW); page.click("#f button[type=submit]")
        page.wait_for_function("() => document.getElementById('e').textContent.length > 0", timeout=10000)
        check("7 相手が落ちている: 画面は固まらず失敗文言を出す・iframeは出ない・ログインされない",
              page.query_selector(".stepup-box") is None and "/login" in page.url and auth.SESSION_COOKIE not in {c["name"] for c in ctx.cookies()})
        browser.close()
    print(f"\n== 結果: OK {ok} / FAIL {fail}")
    sys.exit(0 if fail == 0 else 1)
finally:
    server.terminate()
    try: server.wait(timeout=5)
    except Exception: server.kill()
