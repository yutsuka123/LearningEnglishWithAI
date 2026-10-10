"""登録フォーム(static/login.html)の動作確認スクリプト(ver1.5.11・2026-10-04)。

実ブラウザ(Playwright: WebKit=Safari系 / Chromium)で、スマホ(iPhone SE幅・iPhone 13・
Pixel 5)とPC幅について次を確かめる:
  1. 送信ボタンが開いた直後・キーボード想定の縮めた画面・文字サイズ特大でも画面内にあり、
     Tab移動した入力欄が固定した送信ボタンの裏に隠れない
  2. 「登録せずに試す」リンク(同一タブ・/?tab=vocab)がトップの「登録せず単語を見る」と同じ画面に着く
  3. パスワード表示切替(登録の2欄は連動)・確認欄の不一致のその場表示・メールの打ち間違い案内
  4. 従来どおり登録が完了する(完了後ログインできる)・送信時の検証エラー/サーバー拒否の表示
  5. 既存の計測ビーコン(opened/focus/input/first_input/submit_seen/submit_attempt/
     leave signup:pagehide等)とGoogle広告のコンバージョン送信が従来どおり出る
  6. 4言語(ja/en/zh-CN/zh-TW)で新しい文言が出る・login.htmlが使う辞書キーが全言語に揃っている

**本番には絶対に向けない**(--baseは127.0.0.1/localhostのみ受け付ける)。使い方:
  # 隔離サーバー(.envの無いツリーで、DATA_DIRは捨てられる一時フォルダ)
  ALLOW_FRESH_DB=1 MULTIUSER=1 SESSION_SECRET=preview OPENAI_API_KEY=preview-not-used \\
    DATA_DIR=/tmp/signup_check_data .venv/bin/python -m uvicorn app.main:app --port 8791
  # 別のターミナルで
  .venv/bin/python scripts/check_signup_form.py --base http://127.0.0.1:8791

Googleタグ(gtag)が入っているページを動かすため、実際のGoogle広告アカウントへ通信が飛ばない
ようにする(CLAUDE.md「Googleタグ(広告)まわりの必須ルール」): googletagmanager.comのgtag.js取得
だけ通し、それ以外の外部宛て(google/doubleclick/googleadservices/gstatic等)は全て遮断する。
テスト用の登録メールは`claude-verify-`接頭辞(@example.test)。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
LOGIN_HTML = ROOT / "static" / "login.html"
PASSWORD = "Verify#12345"

RESULTS: list[tuple[bool, str, str]] = []


def check(name: str, cond: bool, detail: str = "") -> bool:
    RESULTS.append((bool(cond), name, detail))
    print(("  OK   " if cond else "  NG   ") + name + (f"  [{detail}]" if detail and not cond else ""))
    return bool(cond)


class Session:
    """1つのブラウザ文脈(ネットワーク遮断・ビーコン記録つき)。"""

    def __init__(self, pw, base: str, browser_name: str, kw: dict, lang: str | None = None):
        self.base = base
        self.browser = getattr(pw, browser_name).launch()
        kw = {k: v for k, v in kw.items() if k != "default_browser_type"}
        kw.setdefault("locale", "ja-JP")
        self.ctx = self.browser.new_context(**kw)
        self.beacons: list[dict] = []
        self.blocked: list[str] = []
        self.allowed_external: list[str] = []
        self.gtag_calls: list[list] = []
        self.ctx.route("**/*", self._guard)
        # gtagの呼び出し(登録完了のコンバージョン送信)が従来どおり行われるかを、ページを
        # 離れても残るsendBeacon経由で記録する(/__gtag_probeは遮断側で受けるだけの偽の宛先)。
        self.ctx.add_init_script(
            "window.addEventListener('load', function () {"
            " var g = window.gtag; if (typeof g !== 'function') return;"
            " window.gtag = function () { try { navigator.sendBeacon('/__gtag_probe',"
            " JSON.stringify(Array.prototype.slice.call(arguments))); } catch (e) {}"
            " return g.apply(this, arguments); }; });")
        # WebKitはsendBeaconをroute側で観測できないため、ページ側でも送信内容を控える。
        self.ctx.add_init_script(
            "window.__sb = []; (function () { var o = navigator.sendBeacon;"
            " if (!o) return; navigator.sendBeacon = function (u, d) {"
            " try { if (d && d.text) d.text().then(function (t) { window.__sb.push([u, t]); });"
            " else window.__sb.push([u, String(d)]); } catch (e) {}"
            " return o.apply(navigator, arguments); }; })();")
        if lang:
            self.ctx.add_init_script(
                f"try {{ localStorage.setItem('lang', {json.dumps(lang)}); }} catch (e) {{}}")
        self.page = self.ctx.new_page()

    def _guard(self, route):
        u = route.request.url
        if u.startswith(self.base):
            if urlparse(u).path == "/api/system/track" and route.request.method == "POST":
                try:
                    self.beacons.append(json.loads(route.request.post_data or "{}"))
                except Exception:
                    pass
            if urlparse(u).path == "/__gtag_probe":
                try:
                    self.gtag_calls.append(json.loads(route.request.post_data or "[]"))
                except Exception:
                    self.gtag_calls.append(["?"])
                return route.fulfill(status=204, body="")
            return route.continue_()
        if ("googletagmanager.com" in u and "/gtag/js" in u
                and route.request.method == "GET"):
            self.allowed_external.append(u)
            return route.continue_()
        self.blocked.append(u)
        return route.abort()

    def labels(self, kind: str = "click", category: str = "signup_form") -> list[str]:
        return [b.get("label", "") for b in self.beacons
                if b.get("kind") == kind and b.get("category") == category]

    def close(self):
        try:
            self.ctx.close()
        finally:
            self.browser.close()

    # --- よく使う操作 ---
    def open_signup(self):
        self.page.goto("about:blank")   # 同じURLへの移動だとハッシュ変更だけで再読込されないため
        self.page.goto(self.base + "/login#signup", wait_until="load")
        self.page.wait_for_selector("#fSignup:not(.hidden)")
        self.page.wait_for_timeout(400)

    def rect(self, sel: str):
        return self.page.evaluate(
            "(s) => { const e = document.querySelector(s); if (!e) return null;"
            " const r = e.getBoundingClientRect();"
            " return {top: r.top, bottom: r.bottom, height: r.height}; }", sel)

    def inner_h(self) -> int:
        return self.page.evaluate("window.innerHeight")


def button_in_view(s: Session) -> tuple[bool, str]:
    r = s.rect("#fSignup button[type=submit]")
    vh = s.inner_h()
    ok = r is not None and r["top"] >= 0 and r["bottom"] <= vh + 0.5
    return ok, f"top={r and round(r['top'])} bottom={r and round(r['bottom'])} vh={vh}"


def active_not_covered(s: Session) -> tuple[bool, str]:
    d = s.page.evaluate(
        "() => { const a = document.activeElement; const bar = document.getElementById('submitBar');"
        " if (!a || a === document.body) return null;"
        " const r = a.getBoundingClientRect(); const b = bar.getBoundingClientRect();"
        " return {tag: a.tagName, id: a.id, top: r.top, bottom: r.bottom, barTop: b.top,"
        "  barBottom: b.bottom, inBar: bar.contains(a)}; }")
    if d is None or d["inBar"]:
        return True, "bar/none"
    # 固定バー(の矩形)と重なっていなければ隠れていない(バーより後ろにある補足リンク等は対象外)。
    ok = not (d["bottom"] > d["barTop"] + 1 and d["top"] < d["barBottom"]) and d["top"] >= 0
    return ok, (f"{d['tag']}#{d['id']} top={round(d['top'])} bottom={round(d['bottom'])} "
                f"barTop={round(d['barTop'])} barBottom={round(d['barBottom'])}")


def tab_walk(s: Session) -> list[str]:
    """メール欄からTabで進み、フォーカスした要素が固定バーに隠れていないかを見る。"""
    bad = []
    s.page.focus("#su")
    for _ in range(9):
        s.page.keyboard.press("Tab")
        s.page.wait_for_timeout(120)
        ok, d = active_not_covered(s)
        if not ok:
            bad.append(d)
    return bad


# ---------------------------------------------------------------- 検証本体


def check_layout(s: Session, label: str, is_mobile: bool, vw: int, vh0: int):
    s.open_signup()
    ok, d = button_in_view(s)
    check(f"[{label}] 開いた直後に送信ボタンが画面内", ok, d)
    # キーボード表示を想定して画面の高さを55%に縮める(キーボードの分だけレイアウトの高さが
    # 縮むブラウザ=Android Chrome(resizes-content)等の再現)。
    vh = s.inner_h()
    s.page.set_viewport_size({"width": vw, "height": int(vh * 0.55)})
    s.page.wait_for_timeout(300)
    ok, d = button_in_view(s)
    check(f"[{label}] キーボード想定(高さ55%)でも送信ボタンが画面内", ok, d)
    # 入力欄にフォーカスしたとき、固定した送信ボタンの裏に隠れない
    bad = tab_walk(s)
    check(f"[{label}] Tabで移動した欄が送信ボタン(固定バー)の裏に隠れない", not bad, "; ".join(bad))
    s.page.focus("#sdisplay")
    s.page.wait_for_timeout(150)
    ok3, d3 = active_not_covered(s)
    check(f"[{label}] 最後の必須欄(お名前)にフォーカスしても隠れない", ok3, d3)
    s.page.set_viewport_size({"width": vw, "height": vh})
    s.page.wait_for_timeout(200)
    # 一番下までスクロール: 固定バーが補足文・リンクと重ならず元の位置に収まる
    s.page.evaluate("window.scrollTo(0, document.documentElement.scrollHeight)")
    s.page.wait_for_timeout(200)
    bar = s.rect("#submitBar")
    nxt = s.page.evaluate(
        "() => { const n = document.getElementById('submitBar').nextElementSibling;"
        " const r = n.getBoundingClientRect(); return {top: r.top}; }")
    check(f"[{label}] 最下部でバーが下の補足文と重ならない", bar["bottom"] <= nxt["top"] + 1,
          f"barBottom={round(bar['bottom'])} nextTop={round(nxt['top'])}")
    if is_mobile:
        # 文字サイズ「特大」(zoom 1.63)でも送信ボタンが画面内
        s.page.evaluate("localStorage.setItem('fontSize', 'xlarge')")
        s.open_signup()
        ok4, d4 = button_in_view(s)
        check(f"[{label}] 文字サイズ特大でも送信ボタンが画面内", ok4, d4)
        s.page.set_viewport_size({"width": vw, "height": int(vh * 0.55)})
        s.page.wait_for_timeout(300)
        ok5, d5 = button_in_view(s)
        bad = tab_walk(s)
        check(f"[{label}] 文字サイズ特大+キーボード想定でも送信ボタンが画面内・Tab移動した欄が隠れない",
              ok5 and not bad, f"{d5} {'; '.join(bad)}")
        s.page.set_viewport_size({"width": vw, "height": vh})
        s.page.evaluate("localStorage.removeItem('fontSize')")


ORDER_JS = (
    "() => { const q = (s) => document.querySelector(s);"
    " const info = q('#signupInfo'), su = q('#su'), su2 = q('#su2'), bar = q('#submitBar'),"
    " sv = q('details.survey'), tr = q('p.try-link');"
    " const before = (a, b) => !!(a && b && (a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING));"
    " return {"
    "  emailBeforeInfo: before(su, info), infoBeforeBar: before(info, bar),"
    "  surveyBeforeInfo: before(sv, info), infoBeforeEmail: before(info, su),"
    "  infoBeforeTry: before(info, tr), infoNextIsTry: !!info && info.nextElementSibling === tr,"
    "  benefits: !!q('#signupInfo [data-i18n-html=\"signup.benefits\"]'),"
    "  safeNote: !!q('#signupInfo [data-i18n-html=\"signup.safeNote\"]'),"
    "  outsideInfo: document.querySelectorAll('#fSignup > [data-i18n-html=\"signup.benefits\"],"
    " #fSignup > [data-i18n-html=\"signup.safeNote\"]').length }; }")


def check_info_position(s: Session, label: str):
    """ver1.5.13: 説明文2つ(#signupInfo)は入力欄の後ろ・送信ボタンの直前。最初の画面に入力欄が入る。"""
    s.open_signup()
    o = s.page.evaluate(ORDER_JS)
    check(f"[{label}] 説明文(登録でできること・安心の案内)は入力欄より後ろ・アンケートの後・送信ボタンの前",
          o["emailBeforeInfo"] and o["surveyBeforeInfo"] and o["infoBeforeBar"], str(o))
    check(f"[{label}] 説明文2つの文言(辞書キー)は#signupInfoの中にあり、フォーム直下には残っていない",
          o["benefits"] and o["safeNote"] and o["outsideInfo"] == 0, str(o))
    vh = s.inner_h()
    r1, r2 = s.rect("#su"), s.rect("#su2")
    check(f"[{label}] 開いた直後の最初の画面にメール欄とメール確認欄が入る",
          bool(r1 and r2 and r1["top"] >= 0 and r2["bottom"] <= vh),
          f"su={r1} su2={r2} innerHeight={vh}")


def check_info_restore(pw, base: str):
    """SIGNUP_INFO_ON_TOP=true にすると、説明文が元の位置(見出しの直下・副導線の前)に戻る。"""
    s = Session(pw, base, "chromium", dict(pw.devices["Pixel 5"]))
    hit = {"n": 0}

    def tweak(route):
        resp = route.fetch()
        body = resp.text()
        if "const SIGNUP_INFO_ON_TOP = false;" in body:
            hit["n"] += 1
            body = body.replace("const SIGNUP_INFO_ON_TOP = false;", "const SIGNUP_INFO_ON_TOP = true;")
        route.fulfill(response=resp, body=body)

    try:
        s.ctx.route("**/login", tweak)   # 後から登録した経路が先に呼ばれる
        s.open_signup()
        check("[restore] login.htmlに定数 SIGNUP_INFO_ON_TOP(既定false)がある", hit["n"] == 1, str(hit))
        o = s.page.evaluate(ORDER_JS)
        check("[restore] SIGNUP_INFO_ON_TOP=true で説明文が見出しの直下(副導線の前・入力欄の前)に戻る",
              o["infoBeforeEmail"] and o["infoBeforeTry"] and o["infoNextIsTry"], str(o))
        check("[restore] 戻した状態でも説明文2つの文言が揃っている", o["benefits"] and o["safeNote"], str(o))
    finally:
        s.close()


def check_password_toggles(s: Session, label: str):
    s.open_signup()
    p = s.page
    p.fill("#sp", "Abcdef#123")
    p.fill("#sp2", "Abcdef#123")
    types = lambda: p.evaluate(  # noqa: E731
        "[document.getElementById('sp').type, document.getElementById('sp2').type]")
    check(f"[{label}] パスワード欄は初期は伏せ字", types() == ["password", "password"], str(types()))
    p.click(".pwd-toggle[data-target=sp]")
    check(f"[{label}] 表示トグル(パスワード欄)で確認欄も一緒に表示", types() == ["text", "text"], str(types()))
    p.click(".pwd-toggle[data-target=sp2]")
    check(f"[{label}] 確認欄のトグルで両方とも伏せ字に戻る", types() == ["password", "password"], str(types()))
    # ログインフォーム側は従来どおり単独(登録欄に影響しない)
    p.click("#toLogin")
    p.wait_for_selector("#f:not(.hidden)")
    p.fill("#p", "x")
    p.click(".pwd-toggle[data-target=p]")
    after = p.evaluate(
        "[document.getElementById('p').type, document.getElementById('sp').type]")
    check(f"[{label}] ログイン欄のトグルは単独で動く", after == ["text", "password"], str(after))


def check_live_messages(s: Session, label: str):
    s.open_signup()
    p = s.page
    msg = lambda i: p.evaluate(  # noqa: E731
        "(i) => { const e = document.getElementById(i); return {t: e.textContent, c: e.className,"
        " shown: getComputedStyle(e).display !== 'none'}; }", i)
    # --- メール確認欄 ---
    p.click("#su")
    p.keyboard.type("taro@example.test")
    p.click("#su2")
    p.keyboard.type("taro@example.tes")
    m = msg("su2Msg")
    check(f"[{label}] メール確認: 打ちかけ(先頭が一致)の間は何も出さない", m["t"] == "" and not m["shown"], str(m))
    p.keyboard.type("t")
    m = msg("su2Msg")
    check(f"[{label}] メール確認: 一致したら✓", "ok" in m["c"] and m["t"].startswith("✓"), str(m))
    p.keyboard.press("Backspace")
    p.keyboard.type("x")
    m = msg("su2Msg")
    check(f"[{label}] メール確認: 違う文字を打つと穏やかな注意(warn)", "warn" in m["c"] and "違" in m["t"], str(m))
    p.click("#su2", click_count=3)
    p.keyboard.type("TARO@Example.Test ")
    m = msg("su2Msg")
    check(f"[{label}] メール確認: 大文字小文字・前後の空白は送信時の検証と同じく無視", "ok" in m["c"], str(m))
    # 打ちかけのまま欄を離れたら知らせる
    p.click("#su2", click_count=3)
    p.keyboard.type("taro@example.tes")
    p.click("#sdisplay")
    m = msg("su2Msg")
    check(f"[{label}] メール確認: 打ちかけのまま欄を離れたら知らせる", "warn" in m["c"] and m["t"] != "", str(m))
    # --- パスワード確認欄 ---
    p.click("#sp")
    p.keyboard.type("Abcdef#123")
    p.click("#sp2")
    p.keyboard.type("Abcdef#12")
    m = msg("sp2Msg")
    check(f"[{label}] パスワード確認: 打ちかけの間は何も出さない", m["t"] == "", str(m))
    p.keyboard.type("3")
    m = msg("sp2Msg")
    check(f"[{label}] パスワード確認: 一致したら✓", "ok" in m["c"], str(m))
    p.click("#sp")
    p.keyboard.press("End")
    p.keyboard.type("x")
    m = msg("sp2Msg")
    check(f"[{label}] パスワード確認: 上の欄を直して食い違ったら注意", "warn" in m["c"], str(m))
    # --- メールの打ち間違い(もしかして) ---
    cases = [
        ("taro@gmial.com", True, "gmail.com"),
        ("TARO@GMIAL.COM ", True, "gmail.com"),
        ("taro@yaho.co.jp", True, "yahoo.co.jp"),
        ("taro@gmail.com", False, ""),
        ("taro@example.test", False, ""),
        ("taro@gmail.co.jp", False, ""),
        ("gmial.com", False, ""),
        ("taro@gmial.com@x", False, ""),
    ]
    for val, expect, sug in cases:
        p.fill("#su", val)
        p.click("#sdisplay")
        m = msg("suMsg")
        got = m["t"] != "" and m["shown"]
        okk = got == expect and (not expect or (sug in m["t"] and "{" not in m["t"]))
        check(f"[{label}] もしかして案内 {val!r} -> {'あり' if expect else 'なし'}", okk, str(m))
    p.fill("#su", "taro@gmial.com")
    p.click("#sdisplay")
    p.click("#su")
    p.keyboard.type("x")
    m = msg("suMsg")
    check(f"[{label}] もしかして案内は入力を始めると消える", m["t"] == "", str(m))
    # 打ち間違い案内は登録を止めない(送信時の検証には関与しない)
    check(f"[{label}] もしかして案内は送信を止めない(フォームにnovalidate/disabledを足していない)",
          s.page.evaluate("!document.getElementById('fSignup').noValidate"
                          " && !document.querySelector('#fSignup button[type=submit]').disabled"))


def check_try_link(s: Session, label: str):
    s.open_signup()
    p = s.page
    href = p.get_attribute("#tryWithoutSignup", "href")
    check(f"[{label}] 副導線のhrefが /?tab=vocab", href == "/?tab=vocab", str(href))
    check(f"[{label}] 副導線は同一タブ(target指定なし)", p.get_attribute("#tryWithoutSignup", "target") is None)
    # leaveビーコン: 実際のページ離脱(pagehide)の送信はPlaywrightから観測できないため、pagehideを
    # 手動で発火して送信内容(ラベル・滞在ms)を確かめる(実離脱がサーバーに届くことは、隔離サーバーの
    # logs.dbのusage_eventsで別途確認する)。
    p.evaluate("window.dispatchEvent(new Event('pagehide'))")
    p.wait_for_timeout(300)
    sent = []
    for u, txt in p.evaluate("window.__sb"):
        if u.endswith("/api/system/track"):
            try:
                sent.append(json.loads(txt))
            except Exception:
                pass
    lv = [b for b in s.beacons + sent
          if b.get("kind") == "leave" and b.get("category") == "login_page"]
    check(f"[{label}] leaveビーコン(signup:pagehide・滞在ms)が従来どおり送られる",
          any(b.get("label") == "signup:pagehide" and isinstance(b.get("value"), (int, float))
              for b in lv), str(lv))
    r = s.ctx.request.get(s.base + "/?tab=vocab")
    check(f"[{label}] /?tab=vocab は200", r.status == 200, str(r.status))
    p.click("#tryWithoutSignup")
    p.wait_for_function(
        "() => { const a = document.querySelector('.nav-item.active');"
        " return !!a && a.dataset.tab === 'vocab'; }", timeout=20000)
    parsed = urlparse(p.url)
    check(f"[{label}] 副導線→同一タブで単語一覧(未登録ゲスト)に着く",
          parsed.path == "/" and "tab=vocab" in parsed.query and len(s.ctx.pages) == 1, p.url)
    p.wait_for_function("() => document.querySelectorAll('#rows tr').length > 0", timeout=20000)
    nrows = p.evaluate("document.querySelectorAll('#rows tr').length")
    check(f"[{label}] 着いた先に単語行が表示される(ゲストで閲覧できる)", nrows > 0, str(nrows))
    p.wait_for_timeout(500)
    check(f"[{label}] 副導線クリックの計測(try_without_signup)が飛ぶ",
          "try_without_signup" in s.labels(), str(s.labels()))
    # ブラウザの「戻る」で登録フォームに戻れる(試してから登録に進める)
    p.go_back()
    p.wait_for_selector("#fSignup:not(.hidden)", timeout=15000)
    check(f"[{label}] 試した後にブラウザの「戻る」で登録フォームへ戻れる", True)
    # 比較: トップの「登録せず単語を見る」ボタンも同じ画面
    p.goto(s.base + "/", wait_until="load")
    p.wait_for_selector("#welcomeTryBtn", timeout=20000)
    p.click("#welcomeTryBtn")
    p.wait_for_function(
        "() => { const a = document.querySelector('.nav-item.active');"
        " return !!a && a.dataset.tab === 'vocab'; }", timeout=20000)
    check(f"[{label}] (比較)トップの「登録せず単語を見る」も同じ単語一覧", True)


def check_validation_errors(s: Session, label: str):
    s.open_signup()
    p = s.page
    p.fill("#su", "claude-verify-mm@example.test")
    p.fill("#su2", "claude-verify-mm2@example.test")
    p.fill("#sp", PASSWORD)
    p.fill("#sp2", PASSWORD)
    p.fill("#sdisplay", "claude-verify")
    p.click("#fSignup button[type=submit]")
    p.wait_for_timeout(300)
    t = p.text_content("#se")
    ok, d = button_in_view(s)
    se = s.rect("#se")
    vh = s.inner_h()
    check(f"[{label}] メール不一致で送信すると既存のエラー文が出て、画面内に見える",
          "一致" in (t or "") and se["top"] >= 0 and se["bottom"] <= vh, f"{t!r} {se}")
    check(f"[{label}] invalid:email_mismatch が従来どおり記録される",
          "invalid:email_mismatch" in s.labels(), str(s.labels()))
    p.fill("#su2", "claude-verify-mm@example.test")
    p.fill("#sp2", PASSWORD + "x")
    p.click("#fSignup button[type=submit]")
    p.wait_for_timeout(300)
    check(f"[{label}] パスワード不一致の送信時エラーと invalid:pw_mismatch",
          "一致" in (p.text_content("#se") or "") and "invalid:pw_mismatch" in s.labels(),
          f"{p.text_content('#se')!r} {s.labels()}")
    p.fill("#sp", "abcdefgh")
    p.fill("#sp2", "abcdefgh")
    p.click("#fSignup button[type=submit]")
    p.wait_for_timeout(300)
    check(f"[{label}] パスワード規則違反の送信時エラーと invalid:pw_policy",
          "invalid:pw_policy" in s.labels() and (p.text_content("#se") or "") != "", str(s.labels()))
    # ボタンはエラー表示で動かない(エラー文はボタンの上)
    ok2, d2 = button_in_view(s)
    check(f"[{label}] エラー表示中も送信ボタンは画面内", ok2, d2)


def signup_and_login(s: Session, label: str, tag: str):
    email = f"claude-verify-{tag}-{int(time.time())}@example.test"
    s.open_signup()
    p = s.page
    p.fill("#su", email)
    p.fill("#su2", email)
    p.fill("#sp", PASSWORD)
    p.fill("#sp2", PASSWORD)
    p.fill("#sdisplay", "claude-verify")
    p.click("#fSignup button[type=submit]")
    p.wait_for_url(s.base + "/", timeout=20000)
    p.wait_for_timeout(500)
    me = p.evaluate("fetch('/api/auth/me').then(r => r.json())")
    user = (me or {}).get("user") or me
    check(f"[{label}] 登録が完了し、ログイン状態でトップへ進む",
          bool(user) and (user.get("email") == email or user.get("username") == email), str(me)[:200])
    lb = s.labels()
    need = ["opened", "focus:email", "input:email", "first_input", "submit_seen", "submit_attempt"]
    miss = [x for x in need if x not in lb]
    check(f"[{label}] 既存の計測ビーコン(opened/focus/input/first_input/submit_seen/submit_attempt)", not miss,
          f"missing={miss} got={lb}")
    check(f"[{label}] 登録完了のコンバージョン送信(gtag event conversion)が従来どおり呼ばれる",
          any(c[:2] == ["event", "conversion"] for c in s.gtag_calls), str(s.gtag_calls))
    # 同じメールの再登録=サーバー拒否はエラーコード付きで表示・fail:<4桁>が記録される
    s.beacons.clear()
    s.open_signup()
    p.fill("#su", email)
    p.fill("#su2", email)
    p.fill("#sp", PASSWORD)
    p.fill("#sp2", PASSWORD)
    p.fill("#sdisplay", "claude-verify")
    p.click("#fSignup button[type=submit]")
    p.wait_for_function("document.getElementById('se').textContent.length > 0", timeout=15000)
    t = p.text_content("#se") or ""
    check(f"[{label}] 登録済みメールの再登録はサーバーの拒否文が従来どおり表示される", t != "", repr(t))
    check(f"[{label}] fail:<4桁コード> が従来どおり記録される",
          any(re.fullmatch(r"fail:\d{4}", l) for l in s.labels()), str(s.labels()))
    return email


def check_login_flow(pw, base: str, email: str):
    s = Session(pw, base, "chromium", {"viewport": {"width": 1280, "height": 800}})
    try:
        s.page.goto(base + "/login", wait_until="load")
        s.page.fill("#u", email)
        s.page.fill("#p", PASSWORD)
        s.page.click("#f button[type=submit]")
        s.page.wait_for_url(base + "/", timeout=20000)
        me = s.page.evaluate("fetch('/api/auth/me').then(r => r.json())")
        user = (me or {}).get("user") or me
        check("[login] 登録したアカウントで従来どおりログインできる",
              bool(user) and (user.get("email") == email or user.get("username") == email), str(me)[:200])
        check("[login] ログイン画面に新しい固定バー等が混ざらない(ログインフォームに.submit-barなし)",
              s.page.evaluate("document.querySelector('#f .submit-bar') === null"))
    finally:
        s.close()


def used_i18n_keys() -> set[str]:
    src = LOGIN_HTML.read_text(encoding="utf-8")
    keys = set(re.findall(r'data-i18n(?:-html|-placeholder|-title|-aria|-alt)?="([^"]+)"', src))
    keys |= set(re.findall(r"i18nT\(\s*'([^']+)'", src))
    keys |= set(re.findall(r"'((?:login|signup|meta|fontSize|topbar)\.[A-Za-z0-9_.]+)'", src))
    keys |= set(re.findall(r"tx\(\s*'([^']+)'", src))
    return {k for k in keys if k and "$" not in k}


def check_i18n(pw, base: str):
    new_keys = ["signup.tryWithoutSignup", "signup.emailConfirmDiff", "signup.pwConfirmDiff",
                "signup.confirmMatch", "signup.emailTypoHint"]
    for lang, loc in (("ja", "ja-JP"), ("en", "en-US"), ("zh-CN", "zh-CN"), ("zh-TW", "zh-TW")):
        s = Session(pw, base, "chromium", {"viewport": {"width": 390, "height": 800}, "locale": loc}, lang=lang)
        try:
            s.open_signup()
            p = s.page
            dic = p.evaluate("window.I18N.DICT")
            cur = p.evaluate("window.I18N.currentLang()")
            check(f"[i18n {lang}] 表示言語が{lang}", cur == lang, cur)
            if lang == "ja":
                for other in ("en", "zh-CN", "zh-TW"):
                    miss = sorted(k for k in used_i18n_keys() if k not in dic[other])
                    check(f"[i18n] login.htmlが使う辞書キーが{other}に揃っている", not miss, f"missing={miss}")
                miss_ja = sorted(k for k in used_i18n_keys() if k not in dic["ja"])
                check("[i18n] login.htmlが使う辞書キーがjaに揃っている", not miss_ja, f"missing={miss_ja}")
            for k in new_keys:
                v = dic[lang].get(k, "")
                check(f"[i18n {lang}] 新キー {k} がある", bool(v))
            hint = dic[lang]["signup.emailTypoHint"]
            check(f"[i18n {lang}] emailTypoHintに{{typed}}/{{suggest}}がある", "{typed}" in hint and "{suggest}" in hint)
            txt = p.text_content("#tryWithoutSignup")
            check(f"[i18n {lang}] 副導線の文言が辞書どおり", txt == dic[lang]["signup.tryWithoutSignup"], txt)
            p.fill("#su", "a@example.test")
            p.fill("#su2", "b@example.test")
            p.click("#sdisplay")
            t = p.text_content("#su2Msg")
            check(f"[i18n {lang}] メール不一致のその場表示が{lang}", t == dic[lang]["signup.emailConfirmDiff"], t)
            p.fill("#su2", "a@example.test")
            p.click("#sdisplay")
            t = p.text_content("#su2Msg")
            check(f"[i18n {lang}] 一致表示が{lang}", t == "✓ " + dic[lang]["signup.confirmMatch"], t)
            p.fill("#sp", "Abcdef#123")
            p.fill("#sp2", "Abcdef#124")
            p.click("#sdisplay")
            t = p.text_content("#sp2Msg")
            check(f"[i18n {lang}] パスワード不一致のその場表示が{lang}", t == dic[lang]["signup.pwConfirmDiff"], t)
            p.fill("#su", "taro@gmial.com")
            p.click("#sdisplay")
            t = p.text_content("#suMsg")
            exp = hint.replace("{typed}", "gmial.com").replace("{suggest}", "gmail.com")
            check(f"[i18n {lang}] 打ち間違い案内が{lang}で差し込み済み", t == exp, t)
            # 言語切替で表示中のメッセージも切り替わる(別言語へ)
            other = "en" if lang != "en" else "ja"
            p.select_option(".i18n-lang-select", other)
            p.wait_for_timeout(200)
            t2 = p.text_content("#su2Msg")
            t3 = p.text_content("#suMsg")
            check(f"[i18n {lang}] 言語を切り替えると表示中の案内も{other}に切り替わる",
                  t2 == dic[other]["signup.emailConfirmDiff"] and
                  t3 == dic[other]["signup.emailTypoHint"].replace("{typed}", "gmial.com").replace("{suggest}", "gmail.com"),
                  f"{t2!r} {t3!r}")
        finally:
            s.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--quick", action="store_true", help="WebKitのPC幅など一部を省く")
    a = ap.parse_args()
    host = urlparse(a.base).hostname
    if host not in ("127.0.0.1", "localhost"):
        print("中止: --base は 127.0.0.1/localhost の隔離サーバーのみ(本番には向けない)")
        return 2
    base = a.base.rstrip("/")
    last_email = ""
    with sync_playwright() as pw:
        devices = [
            ("webkit", "iPhone SE 375x667", {"viewport": {"width": 375, "height": 667},
                                              "device_scale_factor": 2, "is_mobile": True,
                                              "has_touch": True}, True),
            ("webkit", "iPhone SE(旧) 320x568", dict(pw.devices["iPhone SE"]), True),
            ("webkit", "iPhone 13", dict(pw.devices["iPhone 13"]), True),
            ("chromium", "Pixel 5", dict(pw.devices["Pixel 5"]), True),
            ("chromium", "PC 1280x800", {"viewport": {"width": 1280, "height": 800}}, False),
            ("webkit", "PC 1280x800", {"viewport": {"width": 1280, "height": 800}}, False),
        ]
        for i, (br, name, kw, mobile) in enumerate(devices):
            label = f"{br}/{name}"
            print(f"== {label}")
            s = Session(pw, base, br, kw)
            try:
                vp = kw.get("viewport") or {"width": 390, "height": 664}
                check_layout(s, label, mobile, vp["width"], vp["height"])
                check_info_position(s, label)
                check_password_toggles(s, label)
                check_live_messages(s, label)
                check_validation_errors(s, label)
                s.beacons.clear()
                check_try_link(s, label)
                s.beacons.clear()
                last_email = signup_and_login(s, label, f"{br}-{i}")
                ext = [u for u in s.allowed_external]
                check(f"[{label}] 外部宛ての通信はgtag.js取得だけ(それ以外は遮断済み・Google広告アカウントへ飛ばない)",
                      all("googletagmanager.com" in u and "/gtag/js" in u for u in ext), str(ext))
            finally:
                s.close()
        print("== restore(SIGNUP_INFO_ON_TOP)")
        check_info_restore(pw, base)
        print("== login")
        check_login_flow(pw, base, last_email)
        print("== i18n")
        check_i18n(pw, base)
    ng = [r for r in RESULTS if not r[0]]
    print(f"\n{len(RESULTS) - len(ng)}/{len(RESULTS)} OK")
    for _, name, detail in ng:
        print("NG:", name, detail)
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
