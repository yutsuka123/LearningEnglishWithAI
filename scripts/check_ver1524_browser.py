"""ver1.5.24 のブラウザ検査(隔離サーバー専用・本番には絶対に向けない・2026-11-04)。

確かめること(実際の画面):
  B1 ゲスト: 無料範囲外の語は🔒で、説明に『無料登録すると、1日10件まで』が出る。再生を押すと402の案内(登録の理由)が出る
  B2 無料登録(残高0): 無料範囲外の語が🔊で『本日の無料枠で再生できます（あとN件）』。押すと音が返り、残りが1減る。
     10件使い切ると他の範囲外の語は🔒『本日の無料枠（10件）を使い切りました』に変わり、押すと案内が出る。聴いた語は🔊のまま(聴き直し可)
  B3 登録ページ(スマホ幅390・PC幅1280): 安心の案内が読める位置にあり、横にはみ出さない・送信ボタンが画面内・文言に『絶対に漏れないとは言い切れません』『使い捨て』が出る
  B4 外部への通信を1件も通していない(Googleタグ付きページを開くため。URLのホスト名が127.0.0.1/localhostで、ポートも自分のサーバーのものだけ許可。gtag.jsも通さない)

使い方(.envの無いこのworktreeで):
  S=<使い捨てDATA_DIR> ; PY=<repo>/.venv/bin/python
  ALLOW_FRESH_DB=1 MULTIUSER=1 SESSION_SECRET=preview OPENAI_API_KEY=preview-not-used DATA_DIR=$S $PY -m uvicorn app.main:app --port 8797 &
  $PY scripts/check_ver1516.py --prepare --data-dir $S      # 範囲外の語と保存済み音声を用意(再実行しても安全)
  $PY scripts/check_ver1524_browser.py --base http://127.0.0.1:8797 --shots <スクリーンショットの保存先>
"""
from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

RESULTS: list[tuple[bool, str, str]] = []


def check(name: str, cond: bool, detail: str = "") -> bool:
    RESULTS.append((bool(cond), name, detail))
    print(("  OK   " if cond else "  NG   ") + name + (f"  [{detail}]" if detail and not cond else ""))
    return bool(cond)


# 有効な無音MP3(MPEG-1 Layer III・128kbps/44.1kHzの1フレーム=417バイトを40個≒1秒)。ヘッドレスChromiumで再生を最後まで通すための差し替え用。
VALID_MP3 = (bytes.fromhex("fffb9064") + b"\x00" * 413) * 40


class Ctx:
    """外部通信を全て遮断するブラウザ文脈。許可はホスト名が127.0.0.1/localhostに完全一致し、ポートも自分のサーバーのものだけ。"""

    def __init__(self, pw, base: str, browser: str = "chromium", **kw):
        u = urlparse(base)
        self.host, self.port, self.base = u.hostname, u.port, base
        self.blocked: list[str] = []
        self.passed_external: list[str] = []
        self.browser = getattr(pw, browser).launch(args=["--autoplay-policy=no-user-gesture-required"] if browser == "chromium" else [])
        kw.setdefault("locale", "ja-JP")
        self.ctx = self.browser.new_context(**kw)
        self.ctx.route("**/*", self._guard)
        self.page = self.ctx.new_page()

    def _guard(self, route):
        u = urlparse(route.request.url)
        if u.hostname in ("127.0.0.1", "localhost") and u.port == self.port:
            if u.path == "/api/learn/tts/item":
                resp = route.fetch()   # 自分のサーバーへの実リクエスト。200のときだけ中身を有効なMP3に差し替える
                if resp.status == 200:
                    return route.fulfill(response=resp, body=VALID_MP3, headers={**resp.headers, "content-type": "audio/mpeg"})
                return route.fulfill(response=resp)
            return route.continue_()
        self.blocked.append(route.request.url)
        return route.abort()

    def close(self):
        try:
            self.ctx.close()
        finally:
            self.browser.close()


def search_word(page, kw: str):
    page.fill("#kw", kw)
    page.dispatch_event("#kw", "input")
    page.wait_for_timeout(1200)


def shown_message(page) -> str:
    """画面に出ている断りの案内。トースト(#toast)か、『再生できるものだけ』の吹き出し(#freeOnlyNudge .nudge-msg)のどちらか(前者は古い文が残ることがあるので後者を先に見る)。"""
    return page.evaluate(
        "() => { const n = document.querySelector('#freeOnlyNudge.show .nudge-msg, #freeOnlyNudge .nudge-msg');"
        " const t = document.getElementById('toast');"
        " return ((n && n.textContent) || '') + ' | ' + ((t && t.textContent) || ''); }")


def first_cell(page):
    return page.evaluate(
        "() => { const c = document.querySelector('.voice-cell .voice-m'); if (!c) return null;"
        " const row = c.closest('tr') || c.closest('.card') || c.parentElement;"
        " return {title: c.title, icon: c.textContent.trim(), row: (row ? row.textContent : '').replace(/\\s+/g, ' ').slice(0, 80)}; }")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--shots", default="")
    a = ap.parse_args()
    base = a.base.rstrip("/")
    assert urlparse(base).hostname in ("127.0.0.1", "localhost"), "隔離したローカルサーバー以外には向けない"
    shots = Path(a.shots) if a.shots else None
    if shots:
        shots.mkdir(parents=True, exist_ok=True)
    all_ctx: list[Ctx] = []
    with sync_playwright() as pw:
        # ---------------- B1 ゲスト
        g = Ctx(pw, base, viewport={"width": 1280, "height": 900}); all_ctx.append(g)
        p = g.page
        p.goto(base + "/?tab=vocab", wait_until="load"); p.wait_for_timeout(2000)
        search_word(p, "1500")
        c = first_cell(p)
        check("[B1] ゲスト: 無料範囲外の語の再生ボタンは🔒", c is not None and c["icon"] == "🔒", str(c))
        check("[B1] 説明に『無料登録すると聴けます。範囲外の語は1日10件まで』が出る(登録範囲内の語にも範囲外の語にも正しい文)",
              c is not None and "無料登録すると聴けます" in c["title"] and "1日10件まで" in c["title"], str(c))
        # 1500=ゲストには範囲外・ログイン無料の範囲内 → 従来どおり『ログインすると聴けます』(登録だけで制限なく聴ける語)
        r = p.evaluate("fetch('/api/learn/tts/item?item_type=word&item_id=1500&kind=word&voice=ash&speed=learn').then(async r => [r.status, await r.text()])")
        check("[B1] 登録範囲内の語: ゲストには402で『ログインすると聴けます』", r[0] == 402 and "ログインすると聴けます" in r[1], str(r))
        # 2050=ゲストにもログイン無料にも範囲外 → 『無料登録すると範囲外の語も1日10件まで聴けます』
        r = p.evaluate("fetch('/api/learn/tts/item?item_type=word&item_id=2050&kind=word&voice=ash&speed=learn').then(async r => [r.status, await r.text()])")
        check("[B1] 登録でも範囲外の語: ゲストには402で『無料の会員登録をすると、範囲外の語・フレーズも1日10件まで』",
              r[0] == 402 and "無料の会員登録" in r[1] and "1日10件まで" in r[1], str(r))
        search_word(p, "2050")
        p.evaluate("document.querySelector('.voice-cell .voice-m').click()")
        p.wait_for_timeout(900)
        toast = shown_message(p)
        check("[B1] 押すと画面にも同じ案内が出る(登録の理由『範囲外の語も1日10件まで』)", "1日10件まで" in toast, toast[:160])

        # ---------------- B2 無料登録
        u = Ctx(pw, base, viewport={"width": 1280, "height": 900}); all_ctx.append(u)
        p = u.page
        email = f"claude-verify-c1524-{int(time.time())}@example.test"
        p.goto(base + "/login#signup", wait_until="load")
        p.wait_for_selector("#fSignup:not(.hidden)"); p.wait_for_timeout(400)
        for sel, val in (("#su", email), ("#su2", email), ("#sp", "Verify-Pass-1234"), ("#sp2", "Verify-Pass-1234"), ("#sdisplay", "claude-verify")):
            p.fill(sel, val)
        p.click("#fSignup button[type=submit]")
        p.wait_for_url(base + "/?tab=vocab", timeout=20000); p.wait_for_timeout(2000)
        mu = p.evaluate("fetch('/api/system/my-usage').then(r => r.json())")
        check("[B2] 登録直後: 枠は上限10・残り10・使用済みなし", mu.get("outrange_free_limit") == 10 and mu.get("outrange_free_left") == 10 and mu.get("outrange_free_used") == [], str({k: v for k, v in mu.items() if k.startswith("outrange")}))
        search_word(p, "2050")
        c = first_cell(p)
        check("[B2] 無料登録: 範囲外の語は🔊(🔒ではない)で『本日の無料枠で再生できます（あと10件）』",
              c is not None and c["icon"] == "🔊" and "本日の無料枠で再生できます（あと10件）" in c["title"], str(c))
        # 実際に押して、音が返る(200)ことと残りが減ることを確認(ネットワークの応答を観測)
        with p.expect_response(lambda r: "/api/learn/tts/item" in r.url, timeout=8000) as ri:
            p.click(".voice-cell .voice-m")
        check("[B2] ボタンを押すと音声が200で返る", ri.value.status == 200, str(ri.value.status))
        p.wait_for_timeout(1200)
        check("[B2] 枠で再生した直後に『無料枠で再生しました（今日はあと9件）』と知らせる(スマホではhover説明が見えないため)",
              "無料枠で再生しました（今日はあと9件）" in shown_message(p), shown_message(p)[:120])
        mu = p.evaluate("fetch('/api/system/my-usage').then(r => r.json())")
        check("[B2] 1件使うと残り9・使用済みに載る", mu["outrange_free_left"] == 9 and len(mu["outrange_free_used"]) == 1, str(mu["outrange_free_left"]))
        # 残り9件を、別の語を直接APIで再生して使い切る(2001〜2100は無料登録にも範囲外)
        codes = []
        for wid in range(2051, 2060):
            codes.append(p.evaluate(f"fetch('/api/learn/tts/item?item_type=word&item_id={wid}&kind=word&voice=ash&speed=learn').then(r => r.status)"))
        check("[B2] 続けて9件も200(合計10件)", codes == [200] * 9, str(codes))
        r = p.evaluate("fetch('/api/learn/tts/item?item_type=word&item_id=2070&kind=word&voice=ash&speed=learn').then(async r => [r.status, await r.text()])")
        check("[B2] 11件目は402『今日の無料枠（10件）を使い切りました』", r[0] == 402 and "使い切りました" in r[1] and "10件" in r[1], str(r))
        p.reload(wait_until="load"); p.wait_for_timeout(2000)
        search_word(p, "2070")
        c = first_cell(p)
        check("[B2] 使い切った後、別の範囲外の語は🔒で『本日の無料枠（10件）を使い切りました』", c is not None and c["icon"] == "🔒" and "使い切りました" in c["title"], str(c))
        search_word(p, "2050")
        c = first_cell(p)
        check("[B2] すでに聴いた語は🔊のまま『今日は何度でも再生できます』", c is not None and c["icon"] == "🔊" and "何度でも再生できます" in c["title"], str(c))
        with p.expect_response(lambda r: "/api/learn/tts/item" in r.url, timeout=8000) as ri2:
            p.evaluate("document.querySelector('.voice-cell .voice-m').click()")
        check("[B2] 枠が尽きていても、聴いた語は押して200で再生できる", ri2.value.status == 200, str(ri2.value.status))
        search_word(p, "2070")
        p.evaluate("document.querySelector('.voice-cell .voice-m').click()")
        p.wait_for_timeout(900)
        toast = shown_message(p)
        check("[B2] 使い切った後で別の語を押すと、画面に案内が出る(『今日の無料枠（10件）を使い切りました』)", "使い切りました" in toast, toast[:160])
        if shots:
            p.screenshot(path=str(shots / "b2_free_user_vocab.png"))

        # ---------------- B3 登録ページ(スマホ/PC)
        for label, kw in (("スマホ390", dict(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)),
                          ("PC1280", dict(viewport={"width": 1280, "height": 900}))):
            s = Ctx(pw, base, **kw); all_ctx.append(s)
            p = s.page
            p.goto(base + "/login#signup", wait_until="load"); p.wait_for_selector("#fSignup:not(.hidden)"); p.wait_for_timeout(600)
            info = p.evaluate(
                "() => { const n = document.getElementById('signupInfo'); const t = n ? n.innerText : '';"
                " const bar = document.getElementById('submitBar').getBoundingClientRect();"
                " return {text: t, over: document.documentElement.scrollWidth > window.innerWidth + 1,"
                "  barBottom: bar.bottom, vh: window.innerHeight, hint: (document.querySelector('[data-i18n=\"signup.emailHint\"]')||{}).innerText||''}; }")
            check(f"[B3 {label}] 横にはみ出さない", not info["over"])
            check(f"[B3 {label}] 安心の案内に『ニックネーム』『使い捨て』『絶対に漏れないとは言い切れません』『退会』が出る",
                  all(w in info["text"] for w in ("ニックネーム", "使い捨て", "絶対に漏れないとは言い切れません", "退会")), info["text"][:60])
            check(f"[B3 {label}] 『できること』に1日10件が出る", "1日10件" in info["text"], info["text"][:60])
            check(f"[B3 {label}] メール欄の補足に『使い捨て・サブのメールアドレスでも大丈夫』が出る", "使い捨て・サブのメールアドレスでも大丈夫" in info["hint"], info["hint"][:60])
            check(f"[B3 {label}] 送信ボタンが画面内(固定バー)", info["barBottom"] <= info["vh"] + 1, f"{info['barBottom']}/{info['vh']}")
            if shots:
                p.evaluate("document.getElementById('signupInfo').scrollIntoView({block:'start'})"); p.wait_for_timeout(300)
                p.screenshot(path=str(shots / f"b3_signup_info_{label}.png"))
                p.screenshot(path=str(shots / f"b3_signup_full_{label}.png"), full_page=True)

        # ---------------- B5 4言語の登録ページ(安心の案内が各言語で出る)
        for lang, need in (("en", ("throwaway", "can’t promise", "10 words/phrases a day")), ("zh-CN", ("一次性邮箱", "不能保证", "每天也可收听10个")),
                           ("zh-TW", ("拋棄式信箱", "無法保證", "每天也可聆聽10個"))):
            s = Ctx(pw, base, viewport={"width": 390, "height": 844}, locale="en-US"); all_ctx.append(s)
            s.ctx.add_init_script(f"try {{ localStorage.setItem('lang', {lang!r}); }} catch (e) {{}}")
            p = s.page
            p.goto(base + "/login#signup", wait_until="load"); p.wait_for_selector("#fSignup:not(.hidden)"); p.wait_for_timeout(800)
            t = p.evaluate("(document.getElementById('signupInfo') || {}).innerText || ''")
            check(f"[B5 {lang}] 安心の案内と1日10件が言語どおりに出る(日本語のままではない)", all(w in t for w in need) and "安心してご登録" not in t, t[:80])

        # ---------------- B4 外部通信
        ext = sum(len(c.passed_external) for c in all_ctx)
        n_blocked = sum(len(c.blocked) for c in all_ctx)
        check("[B4] 外部へ通した通信が0件(許可はホスト名が127.0.0.1/localhostで自分のポートだけ・gtag.jsも通さない)", ext == 0, f"passed={ext}")
        print(f"       (遮断した外部通信 {n_blocked} 件)")
        for c in all_ctx:
            c.close()
    bad = [r for r in RESULTS if not r[0]]
    print(f"\n{len(RESULTS) - len(bad)}/{len(RESULTS)} 項目OK")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
