"""パスワード再発行の通し試験(実ブラウザ・2026-10-04・ver1.5.12)。隔離サーバー専用(--baseは127.0.0.1/localhostのみ)。

依頼ページ→管理画面で依頼を見て本人確認の手がかりを確認→リンク発行→別のブラウザで再設定→新パスワードでログイン、を
WebKit/Chromiumで通す。Google宛て通信は遮断(gtag.js取得のみ通す)。サーバーには事前に次を作っておくこと:
  管理者 claude-verify-admin@example.test / AdminPass#1234、一般ユーザー claude-verify-taro@example.test / OldPass#1234(お名前=たろう)
使い方: .venv/bin/python scripts/check_password_reset_e2e.py --base http://127.0.0.1:8793 [--engine chromium|webkit]
(ユーザーのパスワードを変更するので、エンジンを変えて再実行するときはDBを作り直すこと)
"""
import argparse
import re
import sys
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

ap = argparse.ArgumentParser()
ap.add_argument("--base", required=True)
ap.add_argument("--engine", default="chromium", choices=["chromium", "webkit"])
_a = ap.parse_args()
BASE = _a.base.rstrip("/")
ENGINE = _a.engine
assert urlparse(BASE).hostname in ("127.0.0.1", "localhost"), "本番には向けられません"
ADMIN, ADMIN_PW = "claude-verify-admin@example.test", "AdminPass#1234"
USER, OLD_PW, NEW_PW = "claude-verify-taro@example.test", "OldPass#1234", "NewPass#5678"
RES = []


def check(name, cond, detail=""):
    RES.append(bool(cond))
    print(("  OK   " if cond else "  NG   ") + name + (f"  [{detail}]" if detail and not cond else ""))


def block(route):
    u = route.request.url
    if u.startswith(BASE) or "googletagmanager.com/gtag/js" in u:
        route.continue_()
    else:
        route.abort()


def ui_login(page, user, pw):
    page.goto(BASE + "/login")
    page.fill("#u", user)
    page.fill("#p", pw)
    page.click("#f button[type=submit]")
    try:
        page.wait_for_url(lambda u: "/login" not in u, timeout=8000)
        return True
    except Exception:
        return False


with sync_playwright() as p:
    for eng in (ENGINE,):
        print(f"== {eng}")
        b = getattr(p, eng).launch()
        seen_urls = []
        # --- 利用者: ログイン画面のリンク→依頼
        ctx = b.new_context(viewport={"width": 390, "height": 844}, locale="ja-JP"); ctx.route("**/*", block)
        pg = ctx.new_page()
        pg.on("request", lambda r: seen_urls.append(r.url))
        pg.goto(BASE + "/login")
        link = pg.query_selector("a[href='/static/password-help.html']")
        check(f"[{eng}] ログイン画面に「パスワードを忘れた方はこちら」のリンクがある", link is not None and "忘れた" in link.inner_text())
        link.click()
        pg.wait_for_selector("#hEmail")
        check(f"[{eng}] 依頼ページが開く(広告タグ・外部スクリプトなし)", "googletagmanager" not in pg.content() and pg.title().startswith("パスワードを忘れた方"))
        pg.fill("#hEmail", "not-an-email"); pg.click("#hSubmit")
        check(f"[{eng}] メールの形式が不正ならその場でエラー", "形式" in pg.inner_text("#hErr"))
        pg.fill("#hEmail", USER.upper()); pg.fill("#hNick", "たろう"); pg.fill("#hContact", f"alt-{eng}@example.test"); pg.fill("#hNote", "9月に登録・800円チャージ")
        pg.click("#hSubmit")
        pg.wait_for_selector("#hDone:not(.hidden)", timeout=8000)
        check(f"[{eng}] 依頼を送ると受付メッセージが出る", "受け付けました" in pg.inner_text("#hDone"))
        ctx.close()
        # --- 管理者: 依頼を見て、本人確認の手がかりを見て、リンクを発行
        ctx = b.new_context(viewport={"width": 1280, "height": 900}, locale="ja-JP"); ctx.route("**/*", block)
        pg = ctx.new_page(); pg.on("dialog", lambda d: d.accept())
        check(f"[{eng}] 管理者でログインできる", ui_login(pg, ADMIN, ADMIN_PW))
        pg.goto(BASE + "/?tab=admin"); pg.wait_for_selector(".step-chip[data-sec='inquiries']", timeout=15000)
        pg.click(".step-chip[data-sec='inquiries']")
        row = pg.query_selector("tr:has-text('パスワード再発行'):has(button.pr-from-inq)")
        check(f"[{eng}] 管理画面の問い合わせ表に依頼(パスワード再発行)が届いている", row is not None)
        row.query_selector("button.pr-from-inq").click()
        pg.wait_for_selector("#prResult [data-uid]", timeout=8000)
        txt = pg.inner_text("#prResult")
        check(f"[{eng}] 本人確認の手がかり(ニックネーム・登録日・チャージ履歴など)が表示される", "たろう" in txt and "登録日" in txt and "チャージ履歴" in txt and "最終ログイン" in txt, txt[:100])
        pg.fill("#prResult .pr-note", "登録メール・ニックネーム・補足が一致")
        pg.click("#prResult .pr-issue")
        pg.wait_for_selector("#prResult .pr-url", timeout=8000)
        url = pg.input_value("#prResult .pr-url")
        check(f"[{eng}] 再設定リンク(絶対URL・#t=トークン)が表示される", re.match(r"^https?://[^/]+/reset-password#t=[A-Za-z0-9_-]{40,}$", url) is not None, url[:60])
        check(f"[{eng}] 管理画面の説明にある注意(1回限り・再表示不可)が出る", "再表示できません" in pg.inner_text("#prResult"))
        ctx.close()
        # --- 利用者: リンクを開いて再設定
        ctx = b.new_context(viewport={"width": 390, "height": 844}, locale="ja-JP"); ctx.route("**/*", block)
        pg = ctx.new_page(); seen = []
        pg.on("request", lambda r: seen.append(r.url))
        pg.goto(url.replace(urlparse(url).netloc, urlparse(BASE).netloc))
        pg.wait_for_selector("#vForm:not(.hidden)", timeout=8000)
        token = url.split("#t=")[1]
        check(f"[{eng}] リンクを開くとパスワード入力欄が出る", pg.is_visible("#rNew"))
        check(f"[{eng}] アドレス欄からトークンが消えている(#以降が空)", pg.evaluate("location.hash") == "" and token not in pg.url)
        check(f"[{eng}] トークンがサーバーへのURLに含まれていない(フラグメントは送られない)", not any(token in u for u in seen), str([u for u in seen if token in u][:1]))
        pg.fill("#rNew", NEW_PW); pg.fill("#rConf", NEW_PW + "x"); pg.click("#rSubmit")
        check(f"[{eng}] 確認欄が違うとその場でエラー", "一致しません" in pg.inner_text("#rErr"))
        pg.fill("#rNew", "short"); pg.fill("#rConf", "short"); pg.click("#rSubmit")
        pg.wait_for_function("document.getElementById('rErr').textContent.length > 0 && !document.getElementById('rSubmit').disabled", timeout=8000)
        check(f"[{eng}] ポリシー違反のパスワードは理由つきで拒否される", len(pg.inner_text("#rErr")) > 5 and not pg.is_visible("#vDone"), pg.inner_text("#rErr"))
        pg.fill("#rNew", NEW_PW); pg.fill("#rConf", NEW_PW); pg.click("#rSubmit")
        pg.wait_for_selector("#vDone:not(.hidden)", timeout=8000)
        check(f"[{eng}] 再設定が完了し、ログイン画面へのリンクが出る", "設定しました" in pg.inner_text("#vDone") and pg.query_selector("#vDone a[href='/login']") is not None)
        # リンクの再利用
        pg2 = ctx.new_page(); pg2.goto(url.replace(urlparse(url).netloc, urlparse(BASE).netloc))
        pg2.wait_for_selector("#vInvalid:not(.hidden)", timeout=8000)
        check(f"[{eng}] 同じリンクをもう一度開くと「無効」と表示される(1回限り)", "無効" in pg2.inner_text("#vInvalid"))
        # 新旧パスワード
        pg3 = ctx.new_page()
        pg3.goto(BASE + "/login"); pg3.fill("#u", USER); pg3.fill("#p", OLD_PW); pg3.click("#f button[type=submit]")
        pg3.wait_for_function("document.getElementById('e').textContent.length > 0", timeout=8000)
        check(f"[{eng}] 古いパスワードではログインできない", "/login" in pg3.url)
        check(f"[{eng}] 新しいパスワードでログインできる", ui_login(pg3, USER, NEW_PW))
        ctx.close()
        # 不正なトークン・トークンなし
        ctx = b.new_context(locale="ja-JP"); ctx.route("**/*", block); pg = ctx.new_page()
        pg.goto(BASE + "/reset-password#t=" + "A" * 43); pg.wait_for_selector("#vInvalid:not(.hidden)", timeout=8000)
        check(f"[{eng}] でたらめなリンクは「無効」と表示される", True)
        pg.goto(BASE + "/reset-password"); pg.wait_for_selector("#vInvalid:not(.hidden)", timeout=8000)
        check(f"[{eng}] リンクなしで開いても「無効」", True)
        ctx.close(); b.close()
print(f"\n{sum(RES)}/{len(RES)} OK")
sys.exit(0 if all(RES) else 1)
