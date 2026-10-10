"""ver1.5.14のUX変更の動作確認スクリプト(2026-10-10)。**隔離サーバー専用・本番には絶対に向けない**。

確かめること:
  A. ようこそ画面のヘッダー: 幅320〜760pxで「ログイン/登録」ボタンが1行・他の項目と重ならない・横にはみ出さない
  B. ゲスト向けの登録案内(専用要素#guestNudge): 学習画面で5回操作すると出る/リンクは登録画面+今いたタブへ戻る?next=つき/
     10秒近く残る/5回目が再生でも失敗トーストに上書きされない/本体はタップを素通し・リンクだけタップできる/
     表示とタップが記録される。ゲストのクイズの拒否が生のJSONで出ない
  C. 登録完了後の着地: next指定なし=単語一覧(/?tab=vocab)、next指定あり=そのnext(従来どおり)
     (ログインの着地=従来どおりトップ('/')は check_signup_form.py のログイン確認が見る)
  D. 管理画面の登録ファネル: 「試した後に登録フォームを開いた人」(API: try_to_signup と画面の行)

使い方(.envの無いツリーで隔離サーバーを2つ起動する):
  # 通常の隔離サーバー(A〜C用)
  ALLOW_FRESH_DB=1 MULTIUSER=1 SESSION_SECRET=preview OPENAI_API_KEY=preview-not-used \\
    DATA_DIR=/tmp/ux_check_data .venv/bin/python -m uvicorn app.main:app --port 8793
  # 管理者として入れる隔離サーバー(D用・MULTIUSER=0は常に管理者扱い・ログイン不要)
  ALLOW_FRESH_DB=1 MULTIUSER=0 OPENAI_API_KEY=preview-not-used \\
    DATA_DIR=/tmp/ux_check_admin_data .venv/bin/python -m uvicorn app.main:app --port 8794
  .venv/bin/python scripts/check_ver1514_ux.py --base http://127.0.0.1:8793 \\
    --admin-base http://127.0.0.1:8794 --admin-data-dir /tmp/ux_check_admin_data

Googleタグが入ったページを動かすため、check_signup_form.pyのSessionと同じ遮断をかける
(gtag.jsの取得だけ通し、google/doubleclick等への通信は全て止める)。テスト用の登録メールは
`claude-verify-`接頭辞(@example.test)。
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_signup_form import PASSWORD, RESULTS, Session, check  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

HEADER_JS = """() => {
  const r = (s) => { const e = document.querySelector(s); if (!e) return null;
    const b = e.getBoundingClientRect();
    return {l: Math.round(b.left), r: Math.round(b.right), t: Math.round(b.top),
            b: Math.round(b.bottom), d: getComputedStyle(e).display}; };
  return {nav: r('#navToggle'), brand: r('.topbar-brand'), lang: r('#langSwitch'),
          theme: r('#themeToggle'), login: r('#loginBtn'),
          sw: document.documentElement.scrollWidth, iw: window.innerWidth}; }"""


def check_header(pw, base: str):
    # 4言語(ボタンの文言の長さが違う: 「ログイン/登録」「Log in / Sign up」「登录/注册」「登入/註冊」)。
    for lang in ("ja", "en", "zh-CN", "zh-TW"):
        for br in ("webkit", "chromium"):
            for w in (320, 340, 360, 375, 390, 400, 412, 430, 440, 600, 760):
                s = Session(pw, base, br, {"viewport": {"width": w, "height": 700}, "is_mobile": True,
                                          "has_touch": True, "device_scale_factor": 2}, lang=lang)
                try:
                    s.page.goto(base + "/", wait_until="networkidle")
                    s.page.wait_for_timeout(700)
                    r = s.page.evaluate(HEADER_JS)
                    items = [(k, r[k]) for k in ("nav", "brand", "lang", "theme", "login")
                             if r[k] and r[k]["d"] != "none"]
                    items.sort(key=lambda kv: kv[1]["l"])
                    overlaps = []
                    for (k1, a), (k2, c) in zip(items, items[1:]):
                        if a["r"] > c["l"] + 1 and not (a["b"] <= c["t"] or c["b"] <= a["t"]):
                            overlaps.append(f"{k1}/{k2}:{a['r'] - c['l']}px")
                    login = r["login"]
                    one_line = login["b"] - login["t"] < 36
                    check(f"[header {lang}/{br}/{w}] 「ログイン/登録」が1行で、他の項目と重ならず、横にはみ出さない",
                          one_line and not overlaps and r["sw"] <= r["iw"] and login["r"] <= r["iw"],
                          f"loginH={login['b'] - login['t']} overlaps={overlaps} scroll={r['sw']}/{r['iw']}")
                    if w <= 440:
                        check(f"[header {lang}/{br}/{w}] 幅440px以下ではブランド名を隠している(重なり防止)",
                              r["brand"] is None or r["brand"]["d"] == "none")
                finally:
                    s.close()


def _click_theme(p, n: int):
    for _ in range(n):
        p.click("#themeToggle")   # 学習タブでのボタン押下(音声は鳴らさない無害なボタン)
        p.wait_for_timeout(120)


def check_nudge(pw, base: str):
    s = Session(pw, base, "chromium", dict(pw.devices["Pixel 5"]))
    try:
        p = s.page
        p.goto(base + "/?tab=vocab", wait_until="networkidle")
        p.wait_for_timeout(1500)
        hidden_before = p.evaluate(
            "(() => { const n = document.getElementById('guestNudge');"
            " return !n || getComputedStyle(n).visibility === 'hidden'; })()")
        _click_theme(p, 5)
        p.wait_for_selector("#guestNudge.show", timeout=5000)
        t0 = time.time()
        link = p.evaluate(
            "() => { const a = document.querySelector('#guestNudge .guest-nudge-link');"
            " return a ? {text: a.textContent, href: a.getAttribute('href')} : null; }")
        check("[nudge] 学習画面で5回操作すると、専用の案内(#guestNudge)が出る(それまでは非表示)",
              hidden_before and bool(link), str(link))
        check("[nudge] リンクは登録画面へ・登録後は今いたタブへ戻る(?next=)・文言は「1分で無料登録 →」",
              bool(link) and link["href"] == "/login?next=%2F%3Ftab%3Dvocab#signup" and "無料登録" in link["text"],
              str(link))
        pe = p.evaluate(
            "() => ({n: getComputedStyle(document.getElementById('guestNudge')).pointerEvents,"
            " link: getComputedStyle(document.querySelector('#guestNudge .guest-nudge-link')).pointerEvents,"
            " role: document.getElementById('guestNudge').getAttribute('role')})")
        check("[nudge] 本体はタップを素通し・リンクだけタップできる・読み上げ対応(role=status)",
              pe["n"] == "none" and pe["link"] == "auto" and pe["role"] == "status", str(pe))
        box = p.evaluate(
            "(() => { const r = document.getElementById('guestNudge').getBoundingClientRect();"
            " return {w: Math.round(r.width), h: Math.round(r.height), iw: window.innerWidth}; })()")
        check("[nudge] 細長い箱にならない(幅が画面の6割以上・高さ120px以下=従来は幅約50%・高さ156px)",
              box["w"] >= box["iw"] * 0.6 and box["h"] <= 120, str(box))
        msg = p.evaluate("document.getElementById('guestNudge').textContent")
        check("[nudge] 案内の文面は従来どおり(学習の記録は保存されていません…)", "学習の記録は保存されていません" in msg, msg)
        p.wait_for_timeout(5200)
        still = p.evaluate("document.getElementById('guestNudge').classList.contains('show')")
        check("[nudge] 5秒たっても消えない(従来は2.2秒で消えていた)", still, f"elapsed={time.time() - t0:.1f}s")
        check("[nudge] 表示が記録される(boot/guest_nudge/shown)", "shown" in s.labels("boot", "guest_nudge"),
              str(s.beacons)[:300])
        p.click("#guestNudge .guest-nudge-link")
        p.wait_for_url(base + "/login?next=%2F%3Ftab%3Dvocab#signup", timeout=15000)
        p.wait_for_timeout(500)
        check("[nudge] リンクのタップで登録画面が開く(?next=を保ったまま)",
              p.evaluate("!document.getElementById('fSignup').classList.contains('hidden')"))
        check("[nudge] リンクのタップが記録される(click/guest_nudge/signup)",
              "signup" in s.labels("click", "guest_nudge"), str(s.labels("click", "guest_nudge")))
    finally:
        s.close()
    # 5回目の操作が「再生」でも、直後の失敗トーストに上書きされず案内が残る(独立照査MEDIUM-1)
    s3 = Session(pw, base, "chromium", dict(pw.devices["Pixel 5"]))
    try:
        p = s3.page
        p.goto(base + "/?tab=vocab", wait_until="networkidle")
        p.wait_for_timeout(1500)
        _click_theme(p, 4)
        p.click(".voice-m")   # 5回目=再生(隔離環境では音声を作れず、失敗のトーストが出る)
        p.wait_for_selector("#guestNudge.show", timeout=5000)
        toast_seen = False
        for _ in range(12):
            p.wait_for_timeout(300)
            toast_seen = toast_seen or p.evaluate(
                "document.getElementById('toast').classList.contains('show')")
        alive = p.evaluate(
            "document.getElementById('guestNudge').classList.contains('show')"
            " && !!document.querySelector('#guestNudge .guest-nudge-link')")
        check("[nudge] 5回目が再生で失敗トーストが出ても、案内は上書きされず残る(リンクも残る)",
              alive, f"failure_toast_seen={toast_seen}")
    finally:
        s3.close()
    # 2回目の操作で再表示されない(1セッション1回)
    s2 = Session(pw, base, "chromium", dict(pw.devices["Pixel 5"]))
    try:
        p = s2.page
        p.goto(base + "/?tab=vocab", wait_until="networkidle")
        p.wait_for_timeout(1200)
        _click_theme(p, 12)
        n = len([1 for b in s2.beacons if b.get("kind") == "boot" and b.get("category") == "guest_nudge"])
        check("[nudge] 1セッションに1回しか出ない(12回操作しても表示記録は1件)", n == 1, f"n={n}")
    finally:
        s2.close()
    # 案内→登録→今いたタブ(フレーズ)へ戻る
    s4 = Session(pw, base, "chromium", dict(pw.devices["Pixel 5"]))
    try:
        p = s4.page
        p.goto(base + "/?tab=phrases", wait_until="networkidle")
        p.wait_for_timeout(1500)
        _click_theme(p, 5)
        p.wait_for_selector("#guestNudge.show", timeout=5000)
        href = p.get_attribute("#guestNudge .guest-nudge-link", "href")
        check("[nudge] フレーズ画面の案内のリンクは、登録後にフレーズ画面へ戻る(?next=)",
              href == "/login?next=%2F%3Ftab%3Dphrases#signup", str(href))
        p.click("#guestNudge .guest-nudge-link")
        p.wait_for_selector("#fSignup:not(.hidden)")
        email = f"claude-verify-nudge-{int(time.time())}@example.test"
        p.fill("#su", email)
        p.fill("#su2", email)
        p.fill("#sp", PASSWORD)
        p.fill("#sp2", PASSWORD)
        p.fill("#sdisplay", "claude-verify")
        p.click("#fSignup button[type=submit]")
        p.wait_for_url(base + "/?tab=phrases", timeout=20000)
        check("[nudge] 案内から登録すると、今いたタブ(フレーズ)へ戻る", True)
    except Exception as e:  # noqa: BLE001
        check("[nudge] 案内から登録すると、今いたタブ(フレーズ)へ戻る", False,
              f"{type(e).__name__}: {str(e)[:150]} url={s4.page.url}")
    finally:
        s4.close()
    src = (ROOT / "static" / "js" / "app.js").read_text(encoding="utf-8")
    check("[nudge] toast()が直前の消去タイマーを止めている(短いトーストが長いトーストを途中で消さない)",
          "clearTimeout(toastTimer)" in src and "clearTimeout(nudgeTimer)" in src)


def check_quiz_toast(pw, base: str):
    """ゲストのクイズで、再生が拒否(401)されても生のJSON({"ok":false,...})がトーストに出ない。"""
    s = Session(pw, base, "chromium", dict(pw.devices["Pixel 5"]))
    try:
        p = s.page
        p.goto(base + "/?tab=quiz", wait_until="networkidle")
        p.wait_for_timeout(1200)
        p.click("text=クイズ開始 (10語)")
        seen = []
        for _ in range(12):
            p.wait_for_timeout(400)
            t = p.evaluate("(() => { const e = document.getElementById('toast');"
                           " return e.classList.contains('show') ? e.textContent : ''; })()")
            if t:
                seen.append(t)
        raw = [t for t in seen if t.lstrip().startswith("{")]
        check("[quiz] ゲストのクイズで、再生の拒否が生のJSONのままトーストに出ない",
              not raw, f"raw={raw[:1]} seen={seen[:2]}")
    finally:
        s.close()


def check_next_hardening(pw, base: str, email: str):
    """`next`は自サイトの相対パスだけ。TAB/改行・バックスラッシュ・//・絶対URL等は拒否し、
    従来の既定の行き先に倒す(独立照査HIGH-1: "/<TAB>/evil.example/" が検証を通って外部へ飛んだ)。"""
    bad_nexts = {
        "TAB": "%2F%09%2Fevil.example%2Fphish", "LF": "%2F%0A%2Fevil.example",
        "CR": "%2F%0D%2Fevil.example", "二重スラッシュ": "%2F%2Fevil.example",
        "バックスラッシュ": "%2F%5Cevil.example", "絶対URL": "https%3A%2F%2Fevil.example%2F",
        "javascript": "javascript%3Aalert(1)",
    }
    host = urlparse(base).netloc
    for label, enc in bad_nexts.items():
        s = Session(pw, base, "chromium", {"viewport": {"width": 1280, "height": 800}})
        try:
            s.page.goto(base + "/login?next=" + enc, wait_until="load")
            s.page.wait_for_timeout(300)
            s.page.fill("#u", email)
            s.page.fill("#p", PASSWORD)
            s.page.click("#f button[type=submit]")
            s.page.wait_for_url(base + "/", timeout=15000)
            check(f"[next] 不正なnext({label})のログインは自サイトのトップへ(外部へ飛ばない)",
                  urlparse(s.page.url).netloc == host and s.page.url.rstrip("/") == base.rstrip("/"), s.page.url)
        except Exception as e:  # noqa: BLE001
            check(f"[next] 不正なnext({label})のログインは自サイトのトップへ(外部へ飛ばない)", False,
                  f"{type(e).__name__}: {str(e)[:120]} url={s.page.url}")
        finally:
            s.close()
    # 登録側も同じ検証(TABの場合は単語一覧=登録の既定へ)
    for label, enc in (("TAB", bad_nexts["TAB"]), ("バックスラッシュ", bad_nexts["バックスラッシュ"])):
        s = Session(pw, base, "chromium", {"viewport": {"width": 1280, "height": 800}})
        try:
            em = f"claude-verify-nexthard-{int(time.time())}-{label[:1].lower() if label.isascii() else 'b'}@example.test"
            s.page.goto(base + "/login?next=" + enc + "#signup", wait_until="load")
            s.page.wait_for_selector("#fSignup:not(.hidden)")
            s.page.fill("#su", em)
            s.page.fill("#su2", em)
            s.page.fill("#sp", PASSWORD)
            s.page.fill("#sp2", PASSWORD)
            s.page.fill("#sdisplay", "claude-verify")
            s.page.click("#fSignup button[type=submit]")
            s.page.wait_for_url(base + "/?tab=vocab", timeout=20000)
            check(f"[next] 不正なnext({label})の登録は自サイトの単語一覧へ(外部へ飛ばない)",
                  urlparse(s.page.url).netloc == host, s.page.url)
        except Exception as e:  # noqa: BLE001
            check(f"[next] 不正なnext({label})の登録は自サイトの単語一覧へ(外部へ飛ばない)", False,
                  f"{type(e).__name__}: {str(e)[:120]} url={s.page.url}")
        finally:
            s.close()


def check_landing(pw, base: str):
    default_email = ""
    for next_q, want, label in ((None, "/?tab=vocab", "next指定なし=単語一覧"),
                                ("%2F%3Ftab%3Dsettings", "/?tab=settings", "next指定あり=そのnext(従来どおり)")):
        s = Session(pw, base, "chromium", {"viewport": {"width": 1280, "height": 800}})
        try:
            email = f"claude-verify-landing-{int(time.time())}-{'n' if next_q else 'd'}@example.test"
            if not next_q:
                default_email = email
            q = f"?next={next_q}" if next_q else ""
            s.page.goto(base + "/login" + q + "#signup", wait_until="load")
            s.page.wait_for_selector("#fSignup:not(.hidden)")
            s.page.fill("#su", email)
            s.page.fill("#su2", email)
            s.page.fill("#sp", PASSWORD)
            s.page.fill("#sp2", PASSWORD)
            s.page.fill("#sdisplay", "claude-verify")
            s.page.click("#fSignup button[type=submit]")
            s.page.wait_for_url(base + want, timeout=20000)
            check(f"[landing] 登録完了後の着地: {label}", True)
        except Exception as e:  # noqa: BLE001
            check(f"[landing] 登録完了後の着地: {label}", False, f"{type(e).__name__}: {str(e)[:150]} url={s.page.url}")
        finally:
            s.close()
    # ログインの戻り先: nextあり=そのnext(ver1.5.9の戻る対応以降は読み込み時にnextが消えていた=修正)、
    # nextなし=従来どおりトップ('/')。
    for next_q, want, label in (("%2F%3Ftab%3Dsettings", "/?tab=settings", "next指定あり=そのnext"),
                                (None, "/", "next指定なし=従来どおりトップ")):
        s = Session(pw, base, "chromium", {"viewport": {"width": 1280, "height": 800}})
        try:
            q = f"?next={next_q}" if next_q else ""
            s.page.goto(base + "/login" + q, wait_until="load")
            s.page.wait_for_timeout(500)
            kept = s.page.evaluate("location.search")
            if next_q:
                check("[login] 読み込み後もURLの?next=…が残る(従来は'/login'に書き換わっていた)",
                      "next=" in kept, repr(kept))
            s.page.fill("#u", default_email)
            s.page.fill("#p", PASSWORD)
            s.page.click("#f button[type=submit]")
            s.page.wait_for_url(base + want, timeout=20000)
            check(f"[login] ログイン後の着地: {label}", True)
        except Exception as e:  # noqa: BLE001
            check(f"[login] ログイン後の着地: {label}", False, f"{type(e).__name__}: {str(e)[:150]} url={s.page.url}")
        finally:
            s.close()
    # ログイン⇔登録の切り替えでも?next=…が残る(戻る/進むでも)
    s = Session(pw, base, "chromium", {"viewport": {"width": 1280, "height": 800}})
    try:
        s.page.goto(base + "/login?next=%2F%3Ftab%3Dsettings", wait_until="load")
        s.page.click("#toSignup")
        s.page.wait_for_timeout(300)
        u1 = s.page.url
        s.page.click("#toLogin")
        s.page.wait_for_timeout(300)
        u2 = s.page.url
        check("[login] ログイン→登録→ログインと切り替えても?next=…が残る",
              "next=" in u1 and u1.endswith("#signup") and "next=" in u2 and "#" not in u2, f"{u1} / {u2}")
    finally:
        s.close()
    return default_email


def _http_json(url: str):
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def check_admin_funnel(pw, admin_base: str, data_dir: str):
    db = Path(data_dir) / "logs.db"
    if not db.exists():
        check("[admin] 隔離サーバーのlogs.dbがある", False, str(db))
        return
    ua = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
          "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
    now = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    guests = {"gA": "203.0.113.11", "gB": "203.0.113.12", "gC": "203.0.113.13"}
    con = sqlite3.connect(str(db))
    cols_lv = {r[1] for r in con.execute("pragma table_info(landing_visits)")}
    cols_ue = {r[1] for r in con.execute("pragma table_info(usage_events)")}
    for g, ip in guests.items():
        row = {"ip": ip, "path": "/", "user_agent": ua, "kind": "visit", "success": 1, "created_at": now,
               "guest_sid": g, "landing_path": "/", "bot_mark": 0, "is_internal": 0}
        row = {k: v for k, v in row.items() if k in cols_lv}
        con.execute(f"insert into landing_visits ({','.join(row)}) values ({','.join('?' * len(row))})",
                    list(row.values()))

    def ev(g, kind, category, label=""):
        # user_idは存在しないID(管理者/テストアカウントのIDだと「自分の端末」として除外される)。
        row = {"user_id": 99999, "ip": guests[g], "kind": kind, "category": category, "label": label,
               "guest_sid": g, "is_internal": 0, "created_at": now}
        row = {k: v for k, v in row.items() if k in cols_ue}
        con.execute(f"insert into usage_events ({','.join(row)}) values ({','.join('?' * len(row))})",
                    list(row.values()))
    for g in guests:
        ev(g, "boot", "html")
    ev("gA", "page", "vocab")                  # 試した(学習画面)
    ev("gA", "click", "signup_form", "opened")  # → 登録フォームを開いた
    ev("gA", "click", "guest_nudge", "signup")  # → 案内のリンクをタップ
    ev("gB", "play", "word", "word:nova:learn")  # 試した(再生)・フォームは開いていない
    ev("gB", "boot", "guest_nudge", "shown")     # 案内の表示
    ev("gC", "click", "signup_form", "opened")  # 試していないがフォームを開いた
    con.commit()
    con.close()
    res = _http_json(admin_base + "/api/system/admin/registration-funnel?days=30")
    t = res.get("try_to_signup") or {}
    check("[admin] API: try_to_signup の件数が仕込んだ行動と一致(試した2・フォームを開いた2・両方1・案内表示1・案内タップ1)",
          t == {"tried": 2, "form_opened": 2, "tried_and_opened": 1, "nudge_shown": 1, "nudge_clicked": 1},
          str(t))
    check("[admin] API: 既存のキー(stages/via_seo/by_channel等)が残っている",
          all(k in res for k in ("stages", "via_seo", "by_channel", "signup_form", "top_behavior")),
          str(sorted(res.keys())))
    # 画面の行(管理者として入れる隔離サーバーで、ファネルを読み込んで文言を確認)
    s = Session(pw, admin_base, "chromium", {"viewport": {"width": 1280, "height": 900}})
    try:
        p = s.page
        p.goto(admin_base + "/?tab=admin", wait_until="networkidle")
        p.wait_for_selector("#regFunnelReload", state="attached", timeout=15000)
        p.evaluate("document.querySelector('#regFunnelReload').click()")
        p.wait_for_function(
            "document.getElementById('regFunnelWrap').textContent.includes('試した後に登録フォームを開いた人')",
            timeout=15000)
        txt = p.evaluate("document.getElementById('regFunnelWrap').innerText")
        m = re.search(r"2人のうち登録フォームを開いた人\s*1人", txt.replace("\n", ""))
        check("[admin] 画面: 「試した後に登録フォームを開いた人」の行が出て、2人のうち1人と表示される",
              bool(m), re.sub(r"\s+", " ", txt)[:400])
    except Exception as e:  # noqa: BLE001
        check("[admin] 画面: 「試した後に登録フォームを開いた人」の行が出る", False, f"{type(e).__name__}: {str(e)[:200]}")
    finally:
        s.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--admin-base")
    ap.add_argument("--admin-data-dir")
    a = ap.parse_args()
    for u in (a.base, a.admin_base):
        if u and urlparse(u).hostname not in ("127.0.0.1", "localhost"):
            print("中止: 127.0.0.1/localhost の隔離サーバーのみ(本番には向けない)")
            return 2
    base = a.base.rstrip("/")
    with sync_playwright() as pw:
        print("== A. ヘッダー")
        check_header(pw, base)
        print("== B. ゲスト向け登録案内")
        check_nudge(pw, base)
        print("== C. 登録完了後の着地")
        email = check_landing(pw, base)
        print("== C2. nextの安全性(照査HIGH-1)")
        check_next_hardening(pw, base, email)
        print("== B2. ゲストのクイズの拒否トースト")
        check_quiz_toast(pw, base)
        if a.admin_base and a.admin_data_dir:
            print("== D. 管理画面の登録ファネル")
            check_admin_funnel(pw, a.admin_base.rstrip("/"), a.admin_data_dir)
    ng = [r for r in RESULTS if not r[0]]
    print(f"\n{len(RESULTS) - len(ng)}/{len(RESULTS)} OK")
    for _, name, detail in ng:
        print("NG:", name, detail)
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
