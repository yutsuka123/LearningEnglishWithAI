"""JSモジュール読み込み失敗の自己修復(static/js/error-report.js)の検査(2026-10-03)。

背景: ブラウザの履歴移動・タブ復元で、古いapp.jsと新しいviews.jsが混ざると
「Importing binding name 'tabLabel' is not found」等で画面が動かなくなる(実ユーザー1件)。
error-report.js はこのエラーを検知すると、モジュールを取り直して1回だけ再読込する。

隔離した一時DB(DATA_DIR)の使い捨てサーバーとPlaywright(Chromium/WebKit)だけを使い、
本番・外部には一切通信しない(自サーバー以外の通信は全て遮断=Googleタグも飛ばない)。

  .venv/bin/python scripts/check_module_self_heal.py     # 0=全部OK
"""

from __future__ import annotations

import os
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FAILS: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    print(("  OK   " if cond else "  FAIL ") + name + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        FAILS.append(name)


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def start_server(port: int) -> subprocess.Popen:
    env = dict(os.environ, DATA_DIR=tempfile.mkdtemp(prefix="check_heal_"), MULTIUSER="0",
               OPENAI_API_KEY="")
    p = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port), "--log-level", "warning"],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=1)
            return p
        except Exception:  # noqa: BLE001 — 起動待ち
            time.sleep(0.2)
    p.kill()
    raise SystemExit("サーバーが起動しませんでした")


def run_scenario(browser, base: str, broken_times: int | None, label: str,
                 throw_plain_error: bool = False) -> dict:
    """broken_times: app.jsを「tabLabelをexportしない古い版」で返す回数(None=毎回)。0=正常。"""
    ctx = browser.new_context()
    page = ctx.new_page()
    seen = {"docs": 0, "client_errors": 0, "app_js": 0}

    def block_external(route):
        host = urlparse(route.request.url).hostname or ""
        if host in ("127.0.0.1", "localhost"):
            return route.continue_()
        return route.abort()

    def app_js(route):
        seen["app_js"] += 1
        if broken_times is not None and seen["app_js"] > broken_times:
            return route.continue_()
        if broken_times == 0:
            return route.continue_()
        body = route.fetch().text()
        old = body.replace("export function tabLabel", "function tabLabel")
        assert old != body, "app.jsにtabLabelのexportが見つからない(検査の前提が崩れた)"
        route.fulfill(status=200, content_type="application/javascript", body=old)

    ctx.route("**/*", block_external)           # 先に登録=後から登録した下の個別ルートが優先される
    ctx.route("**/static/js/app.js", app_js)

    def on_request(req):
        u = urlparse(req.url)
        if req.resource_type == "document" and u.path == "/":
            seen["docs"] += 1
        if u.path == "/api/system/client-error" and req.method == "POST":
            seen["client_errors"] += 1

    page.on("request", on_request)
    page.goto(base + "/", wait_until="domcontentloaded")
    if throw_plain_error:
        page.wait_for_selector("#nav [data-tab]", state="attached", timeout=15000)
        page.evaluate("setTimeout(() => { throw new Error('plain error not module related'); }, 0)")
    # 再読込が走るなら十分に待つ(ループしていれば docs が増え続ける)
    time.sleep(4)
    booted = False
    try:
        page.wait_for_selector("#nav [data-tab]", state="attached", timeout=8000)
        booted = True
    except Exception:  # noqa: BLE001
        pass
    healed_flag = page.evaluate("sessionStorage.getItem('module_heal_at')") is not None
    ctx.close()
    print(f"    [{label}] docs={seen['docs']} client_errors={seen['client_errors']} "
          f"app.js要求={seen['app_js']} 起動={booted} 印={healed_flag}")
    return {**seen, "booted": booted, "flag": healed_flag}


def main() -> int:
    port = free_port()
    srv = start_server(port)
    base = f"http://127.0.0.1:{port}"
    try:
        with sync_playwright() as p:
            for engine in ("chromium", "webkit"):
                print(f"■ {engine}")
                browser = getattr(p, engine).launch()
                try:
                    r = run_scenario(browser, base, 0, "正常")
                    check(f"{engine}: 正常時は再読込しない(docs=1)", r["docs"] == 1 and r["booted"] and not r["flag"], str(r))

                    r = run_scenario(browser, base, 1, "古いapp.jsが1回だけ混ざる")
                    check(f"{engine}: 混ざったら自動で1回再読込して起動する(docs=2)", r["docs"] == 2 and r["booted"], str(r))
                    check(f"{engine}: 再読込の印(module_heal_at)が残る", r["flag"], str(r))
                    check(f"{engine}: エラー報告は従来どおり1件記録される", r["client_errors"] == 1, str(r))

                    r = run_scenario(browser, base, None, "取り直しても直らない(毎回古い)")
                    check(f"{engine}: 直らない場合も再読込は1回だけ(無限ループしない: docs=2)", r["docs"] == 2, str(r))

                    r = run_scenario(browser, base, 0, "無関係のJSエラー", throw_plain_error=True)
                    check(f"{engine}: モジュールと無関係のエラーでは再読込しない(docs=1)", r["docs"] == 1 and not r["flag"], str(r))
                finally:
                    browser.close()
    finally:
        srv.kill()

    print()
    if FAILS:
        print(f"❌ 失敗 {len(FAILS)} 件: " + ", ".join(FAILS))
        return 1
    print("✅ すべて成功")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
