"""ver1.5.25 のブラウザ検査(隔離サーバー専用・本番には絶対に向けない・2026-11-08)。

確かめること(管理画面「ログ」→「🕵️ 怪しいアクセス」の実際の表示):
  B1 表の見出しに『国・地域』『過去の履歴』が出る・国あり/取得中/不明の3状態・日本は日本語表記
  B2 再来のIP=『🔁 再来 過去N日(直近・初回)』『自動遮断N回』『日ごとの記録』・今回だけのIP=『🆕 初めて(記録上)』
  B3 『再来だけ表示』のチェックで初めてのIPが消え、外すと戻る
  B4 外部サービス由来の文字列(接続元の会社名)にHTMLが入っていても要素にならず、文字として表示される
  B5 画面幅1280/390で、ページ全体が横にはみ出さない(表は自分の枠の中でスクロール)・スクリーンショットを保存
  B6 外部への通信を1件も通していない(アプリのページはGoogleタグ付き。URLのホスト名が127.0.0.1/localhostで、ポートも自分のサーバーのものだけ許可。gtag.jsも通さない)

使い方(.envの無いこのworktreeで):
  S=<使い捨てDATA_DIR> ; PY=<repo>/.venv/bin/python
  ALLOW_FRESH_DB=1 MULTIUSER=1 SESSION_SECRET=preview OPENAI_API_KEY=preview-not-used DATA_DIR=$S $PY -m uvicorn app.main:app --port 8795 &
  SESSION_SECRET=preview DATA_DIR=$S $PY scripts/check_ver1525_browser.py --base http://127.0.0.1:8795 --shots <保存先>
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

ap = argparse.ArgumentParser()
ap.add_argument("--base", required=True)
ap.add_argument("--shots", default="")
a = ap.parse_args()
base = a.base.rstrip("/")
assert urlparse(base).hostname in ("127.0.0.1", "localhost"), "隔離したローカルサーバー以外には向けない"
assert os.environ.get("DATA_DIR") and os.environ.get("SESSION_SECRET"), "サーバーと同じDATA_DIR/SESSION_SECRETが要る"

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from playwright.sync_api import sync_playwright  # noqa: E402

from app.database import db  # noqa: E402
from app.services import auth, ip_blocks  # noqa: E402

RESULTS: list[tuple[bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> bool:
    RESULTS.append((bool(cond), name))
    print(("  OK   " if cond else "  NG   ") + name + (f"  [{detail}]" if detail and not cond else ""))
    return bool(cond)


def utc(days_ago=0, minutes_ago=0):
    return ip_blocks.fmt_utc(ip_blocks.utc_now() - timedelta(days=days_ago, minutes=minutes_ago))


# ---- データ投入(サーバーと同じ使い捨てDB。本番・開発DBには触れない)
IP_REPEAT, IP_NEW, IP_UNKNOWN, IP_PENDING, IP_XSS = "45.33.32.156", "185.220.101.5", "91.92.109.43", "8.8.4.4", "103.21.244.7"
with db() as conn:
    row = conn.execute("SELECT id FROM users WHERE username = 'adm_browser'").fetchone()   # 再実行しても安全に
    if row:
        uid = row["id"]
    else:
        r = auth.create_user(conn, "adm_browser", "Passw0rd!x1", role="admin")
        uid = r["id"] if isinstance(r, dict) else r
    for t in ("suspicious_access", "suspicious_access_days", "security_events", "ip_geo_cache"):
        conn.execute(f"DELETE FROM {t}")
    for ip, probe, af in ((IP_REPEAT, 5, 0), (IP_NEW, 0, 6), (IP_UNKNOWN, 1, 0), (IP_PENDING, 2, 0), (IP_XSS, 3, 0)):
        conn.execute(
            "INSERT INTO suspicious_access (ip, first_seen, last_seen, total, probe, authfail, ratelimited, errors4xx, paths, ua, exempt) "
            "VALUES (?, ?, ?, 40, ?, ?, 0, 0, '[{\"m\":\"GET\",\"p\":\"/.env\",\"s\":307,\"n\":3}]', 'curl/8.0', 0)",
            (ip, utc(minutes_ago=30), utc(minutes_ago=5), probe, af))
        conn.execute("INSERT INTO suspicious_access_days (ip, day, total, probe, authfail) VALUES (?, ?, 40, ?, ?)",
                     (ip, ip_blocks.jst_day(utc(minutes_ago=5)), probe, af))
    for d in (3, 10):
        conn.execute("INSERT INTO suspicious_access_days (ip, day, total, probe) VALUES (?, ?, 20, 4)", (IP_REPEAT, ip_blocks.jst_day(utc(days_ago=d))))
    conn.execute("INSERT INTO security_events (ip, jail, action, mode, created_at) VALUES (?, 'eigo-probe', 'ban', 'ban', ?)", (IP_REPEAT, utc(days_ago=3)))
    conn.execute("INSERT INTO ip_geo_cache (ip, country, region, city, org) VALUES (?, 'Japan', 'Tokyo', 'Tokyo', 'Example ISP')", (IP_REPEAT,))
    conn.execute("INSERT INTO ip_geo_cache (ip, country, region, city, org) VALUES (?, 'Germany', 'Bavaria', 'Augsburg', 'Example Hosting SRL')", (IP_NEW,))
    conn.execute("INSERT INTO ip_geo_cache (ip, country, region, city, org, error) VALUES (?, '', '', '', '', 'ipapi.co HTTP 429')", (IP_UNKNOWN,))
    conn.execute("INSERT INTO ip_geo_cache (ip, country, region, city, org) VALUES (?, 'Belgium', 'Brussels Capital', 'Brussels', ?)",
                 (IP_XSS, '<img src=x onerror="window.__xss=1"><script>window.__xss=1</script>'))
    conn.execute("INSERT OR REPLACE INTO app_state (key, value) VALUES ('suspects_last_at', datetime('now'))")
    conn.commit()
    secret = auth.get_session_secret(conn)
    epoch = auth.get_session_epoch(conn, uid)
token = auth.make_session_token(secret, uid, epoch, int(time.time()))

shots = Path(a.shots) if a.shots else None
if shots:
    shots.mkdir(parents=True, exist_ok=True)
allowed_log: list[str] = []
blocked_log: list[str] = []


def run(pw, width: int, height: int, tag: str):
    u = urlparse(base)
    browser = pw.chromium.launch()
    ctx = browser.new_context(viewport={"width": width, "height": height}, locale="ja-JP")

    def guard(route):
        x = urlparse(route.request.url)
        if x.hostname in ("127.0.0.1", "localhost") and x.port == u.port:
            allowed_log.append(route.request.url)
            return route.continue_()
        blocked_log.append(route.request.url)
        return route.abort()

    ctx.route("**/*", guard)
    ctx.add_cookies([{"name": auth.SESSION_COOKIE, "value": token, "url": base}])
    p = ctx.new_page()
    p.on("dialog", lambda d: d.dismiss())
    p.goto(base + "/?tab=admin", wait_until="load")
    p.wait_for_selector('#adminTabs .step-chip[data-sec="logs"]', timeout=20000)
    p.click('#adminTabs .step-chip[data-sec="logs"]')
    p.evaluate("document.querySelector('#logSuspectsDetails').open = true")
    p.wait_for_selector("#suspectsWrap table", timeout=15000)
    p.wait_for_timeout(500)
    return browser, ctx, p


with sync_playwright() as pw:
    browser, ctx, p = run(pw, 1280, 900, "pc")
    heads = p.evaluate("[...document.querySelectorAll('#suspectsWrap thead th')].map(x => x.textContent.trim())")
    check("[B1] 表の見出しに『国・地域』『過去の履歴』がある", "国・地域" in heads and "過去の履歴" in heads, str(heads))
    rows = p.evaluate("""() => [...document.querySelectorAll('#suspectsWrap tbody tr')].map(tr => {
        const tds = [...tr.children]; return {ip: tds[2].textContent.trim(), geo: tds[3].innerText.replace(/\\s+/g,' ').trim(), hist: tds[4].innerText.replace(/\\s+/g,' ').trim()}; })""")
    by = {r["ip"]: r for r in rows}
    check("[B1] 5件とも表に出る", len(rows) == 5, str(rows))
    check("[B1] 日本は『日本』『東京都』・接続元の名前が出る", "日本" in by[IP_REPEAT]["geo"] and "東京都" in by[IP_REPEAT]["geo"] and "Example ISP" in by[IP_REPEAT]["geo"], by[IP_REPEAT]["geo"])
    check("[B1] 外国は『ドイツ（Germany）』のようにカタカナ+英文", "ドイツ" in by[IP_NEW]["geo"] and "Germany" in by[IP_NEW]["geo"], by[IP_NEW]["geo"])
    check("[B1] 問い合わせて取れなかったIPは『不明』", by[IP_UNKNOWN]["geo"] == "不明", by[IP_UNKNOWN]["geo"])
    check("[B1] まだ問い合わせていないIPは『取得中』", "取得中" in by[IP_PENDING]["geo"], by[IP_PENDING]["geo"])
    h = by[IP_REPEAT]["hist"]
    check("[B2] 再来のIP: 『🔁 再来』『過去2日』『自動遮断 1回』『eigo-probe』『日ごとの記録(3日)』",
          "🔁 再来" in h and "過去2日" in h and "自動遮断 1回" in h and "eigo-probe" in h and "日ごとの記録（3日）" in h, h)
    check("[B2] 今回だけのIP: 『🆕 初めて（記録上）』", "🆕 初めて" in by[IP_NEW]["hist"] and "再来" not in by[IP_NEW]["hist"], by[IP_NEW]["hist"])
    note = p.inner_text("#suspectsWrap")
    check("[B2] 表の下に『記録の始まり』の注記が出る", "履歴の記録の始まり" in note and "実際には過去にもあった可能性" in note)
    # B3 再来だけ表示
    p.check("#susRepeatOnly"); p.wait_for_timeout(900)
    only = p.evaluate("[...document.querySelectorAll('#suspectsWrap tbody tr')].map(tr => tr.children[2].textContent.trim())")
    check("[B3] 『再来だけ表示』で再来のIPだけになる", only == [IP_REPEAT], str(only))
    p.uncheck("#susRepeatOnly"); p.wait_for_timeout(900)
    check("[B3] チェックを外すと5件に戻る", p.evaluate("document.querySelectorAll('#suspectsWrap tbody tr').length") == 5)
    # B4 HTMLの無害化
    xss = p.evaluate("() => ({img: document.querySelectorAll('#suspectsWrap img').length, script: document.querySelectorAll('#suspectsWrap script').length, flag: window.__xss || 0})")
    cell = [r for r in rows if r["ip"] == IP_XSS][0]["geo"]
    check("[B4] 接続元の名前に入れたHTML(img onerror/script)は要素にならず、実行もされない", xss == {"img": 0, "script": 0, "flag": 0}, str(xss))
    check("[B4] その文字列はそのまま文字として表示される", "<img src=x" in cell and "<script>" in cell, cell)
    # B5 PC幅
    ov = p.evaluate("() => ({page: document.documentElement.scrollWidth - window.innerWidth, wrap: (() => { const w = document.querySelector('#suspectsWrap'); return w.scrollWidth - w.clientWidth; })()})")
    check("[B5] PC幅1280: ページ全体は横にはみ出さない", ov["page"] <= 1, str(ov))
    if shots:
        p.evaluate("document.querySelector('#suspectsWrap').scrollIntoView()")
        p.screenshot(path=str(shots / "suspects_pc.png"))
        p.locator("#suspectsWrap").screenshot(path=str(shots / "suspects_pc_table.png"))
    ctx.close(); browser.close()

    browser, ctx, p = run(pw, 390, 844, "sp")
    ov = p.evaluate("""() => { const w = document.querySelector('#suspectsWrap'); const cs = getComputedStyle(w);
        return {page: document.documentElement.scrollWidth - window.innerWidth, wrapOverflowX: cs.overflowX, wrapScroll: w.scrollWidth - w.clientWidth,
                table: w.querySelector('table').getBoundingClientRect().width}; }""")
    check("[B5] スマホ幅390: ページ全体は横にはみ出さない(表は枠の中でスクロールできる)", ov["page"] <= 1 and (ov["wrapOverflowX"] in ("auto", "scroll") or ov["wrapScroll"] <= 1), str(ov))
    if shots:
        p.evaluate("document.querySelector('#suspectsWrap').scrollIntoView()")
        p.screenshot(path=str(shots / "suspects_sp.png"))
    ctx.close(); browser.close()

external = [u for u in allowed_log if urlparse(u).hostname not in ("127.0.0.1", "localhost")]
check("[B6] 外部へ通した通信は0件(許可はホスト名が127.0.0.1/localhostで自分のサーバーのポートだけ)", not external, str(external[:3]))
print(f"       (遮断した外部通信 {len(blocked_log)}件・通した自サーバーへの通信 {len(allowed_log)}件)")
ng = [n for ok_, n in RESULTS if not ok_]
print(f"\n{len(RESULTS) - len(ng)} OK / {len(ng)} NG")
sys.exit(1 if ng else 0)
