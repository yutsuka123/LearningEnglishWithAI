"""ver1.5.18「関連リンク」タブ(サイエンスラボとの相互リンクの英語アプリ側)の動作確認スクリプト(2026-10-19)。
**隔離サーバー専用・本番には絶対に向けない**。

確かめること:
  A. メニューに「関連リンク」タブが出る(ゲスト・管理者の両方)。並びは「バージョン情報」の次・「管理者情報」の前
  B. サイエンスラボへのリンクは**タブの中だけ**にある(ようこそ画面・メニュー・ページ全体のHTMLに現れない)
  C. タブの中: 見出し・リンク先がサイエンスラボのトップ・別タブ(_blank)・rel=noopener・外部サイトの注意書き
  D. 4言語(日英中簡繁)で表示され、日本語以外にかなが混ざらない
  E. 押したことが記録される(click/related_links)・タブを開いたことが記録される(page/links)
  F. スマホ幅(320〜430px)で横にはみ出さない・ブラウザの戻るでタブが戻る
  G. リンクを押すとブラウザがサイエンスラボのURLへ遷移しようとする(この検査は外部通信を全て止めているので、
     止められたURLとして観測する=実際には外へ出ない)

使い方(.envの無いツリーで隔離サーバーを2つ起動する):
  ALLOW_FRESH_DB=1 MULTIUSER=1 SESSION_SECRET=preview OPENAI_API_KEY=preview-not-used \\
    DATA_DIR=<一時フォルダ>/g .venv/bin/python -m uvicorn app.main:app --port 8795
  ALLOW_FRESH_DB=1 MULTIUSER=0 OPENAI_API_KEY=preview-not-used \\
    DATA_DIR=<一時フォルダ>/a .venv/bin/python -m uvicorn app.main:app --port 8796
  .venv/bin/python scripts/check_ver1518.py --base http://127.0.0.1:8795 --admin-base http://127.0.0.1:8796

Googleタグが入ったページを動かすため、check_signup_form.pyのSessionと同じ遮断をかける
(google/doubleclick等への通信は全て止める。本番のGoogle広告アカウントへは何も届かない)。
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_signup_form import RESULTS, Session, check  # noqa: E402

SCIENCE_URL = "https://science.nyangailab.com/?src=study-tab"   # ?src=は先方の「宣伝用の印」(合意済み)
KANA = re.compile("[぀-ヺー-ヿ]")   # 中黒「・」(U+30FB)は除く(中国語の訳でも使う)

TITLES = {"ja": "関連リンク", "en": "Related Links", "zh-CN": "相关链接", "zh-TW": "相關連結"}
SCIENCE_NAMES = {"ja": "サイエンスラボ", "en": "Science Lab", "zh-CN": "科学实验室", "zh-TW": "科學實驗室"}
DESKTOP = {"viewport": {"width": 1280, "height": 800}}
PHONE = lambda w: {"viewport": {"width": w, "height": 760}, "is_mobile": True, "has_touch": True,  # noqa: E731
                   "device_scale_factor": 2}


def open_links_tab(s: Session):
    s.page.goto(s.base + "/", wait_until="networkidle")
    s.page.wait_for_timeout(600)
    s.page.evaluate("document.querySelector('#nav [data-tab=\"links\"]').click()")
    s.page.wait_for_selector("#view a[data-link-id]", timeout=5000)


def check_nav_and_isolation(pw, base: str, who: str):
    s = Session(pw, base, "chromium", DESKTOP, lang="ja")
    try:
        s.page.goto(base + "/", wait_until="networkidle")
        s.page.wait_for_timeout(600)
        tabs = s.page.evaluate("[...document.querySelectorAll('#nav .nav-item[data-tab]')].map(b => b.dataset.tab)")
        check(f"[{who}] A. メニューに「関連リンク」タブがある", "links" in tabs, str(tabs))
        if "release" in tabs and "links" in tabs:
            i, j = tabs.index("release"), tabs.index("links")
            ok = j == i + 1 and ("admin" not in tabs or tabs.index("admin") > j)
            check(f"[{who}] A. 並びは「バージョン情報」の次・「管理者情報」の前", ok, str(tabs))
        label = s.page.evaluate("document.querySelector('#nav [data-tab=\"links\"]').textContent.trim()")
        check(f"[{who}] A. メニューの表示は「🔗 関連リンク」", label == "🔗 関連リンク", label)
        # B. 開く前は、ページ全体のHTMLにサイエンスラボのURLが一切ない(ようこそ画面・メニュー・隠し要素とも)
        html = s.page.content()
        check(f"[{who}] B. タブを開く前のページ全体にサイエンスラボのURLがない(トップ/ようこそ/メニューに載せない)",
              "science.nyangailab.com" not in html and "サイエンスラボ" not in s.page.inner_text("body"))
        s.page.evaluate("document.querySelector('#nav [data-tab=\"links\"]').click()")
        s.page.wait_for_selector("#view a[data-link-id]", timeout=5000)
        view = s.page.inner_text("#view")
        h1 = s.page.inner_text("#view h1")
        check(f"[{who}] C. 見出しは「🔗 関連リンク」", h1.strip() == "🔗 関連リンク", h1)
        a = s.page.query_selector("#view a[data-link-id='science']")
        href = a.get_attribute("href") if a else None
        check(f"[{who}] C. リンク先はサイエンスラボのトップ", href == SCIENCE_URL, str(href))
        check(f"[{who}] C. 別タブで開き、rel=noopener", bool(a) and a.get_attribute("target") == "_blank"
              and "noopener" in (a.get_attribute("rel") or ""))
        check(f"[{who}] C. 外部サイトである旨の注意書きがある", "リンク先は別のサイト" in view, view[:120])
        check(f"[{who}] C. 紹介文は変わりうる事実を断定しない(「無料で見られます」「現在は日本語のみ」。すべて無料等の断定・版番号・広告への言及なし)",
              all(w in view for w in ("無料で見られます", "現在は日本語のみ", "α版", "未確認・未レビュー"))
              and not re.search(r"alpha\d|ver\d|広告|完全無料|すべて無料|ずっと無料|永久", view), view[:200])
        check(f"[{who}] B. リンクは「#view」の中だけ(メニューには載らない)",
              s.page.evaluate("document.querySelectorAll('a[href*=\"science.nyangailab.com\"]').length") == 1
              and s.page.evaluate("document.querySelectorAll('#view a[href*=\"science.nyangailab.com\"]').length") == 1)
        # E. 記録(ページ表示)
        pages = [b for b in s.beacons if b.get("kind") == "page" and b.get("category") == "links"]
        check(f"[{who}] E. タブを開いたことが記録される(page/links)", len(pages) >= 1, str(s.beacons[-3:]))
        # E. 押下の記録 + G. 遷移の試み
        before = len(s.blocked)
        with s.ctx.expect_page(timeout=5000) as pi:
            a.click()
        try:
            pi.value.wait_for_load_state("domcontentloaded", timeout=3000)
        except Exception:  # noqa: BLE001  遮断された遷移は読み込み失敗になる(想定どおり)
            pass
        s.page.wait_for_timeout(500)
        clicks = [b for b in s.beacons if b.get("kind") == "click" and b.get("category") == "related_links"]
        check(f"[{who}] E. リンクを押したことが記録される(click/related_links/science)",
              any(b.get("label") == "science" for b in clicks), str(clicks))
        tried = [u for u in s.blocked[before:] if urlparse(u).hostname == "science.nyangailab.com"]
        check(f"[{who}] G. 押すとサイエンスラボへ遷移しようとする(この検査では遮断=外へは出ない)", len(tried) >= 1,
              str(s.blocked[before:])[:200])
        # F. 戻る
        s.page.bring_to_front()
        s.page.evaluate("document.querySelector('#nav [data-tab=\"vocab\"]') && document.querySelector('#nav [data-tab=\"vocab\"]').click()")
        s.page.wait_for_timeout(500)
        s.page.go_back()
        s.page.wait_for_timeout(800)
        active = s.page.evaluate("document.querySelector('#nav .nav-item.active')?.dataset.tab")
        check(f"[{who}] F. ブラウザの戻るで「関連リンク」に戻る", active == "links", str(active))
    except Exception as e:  # noqa: BLE001
        check(f"[{who}] A〜G. 例外なし", False, f"{type(e).__name__}: {str(e)[:300]}")
    finally:
        s.close()


def check_languages(pw, base: str):
    for lang in ("ja", "en", "zh-CN", "zh-TW"):
        s = Session(pw, base, "chromium", DESKTOP, lang=lang)
        try:
            open_links_tab(s)
            view = s.page.inner_text("#view")
            nav = s.page.evaluate("document.querySelector('#nav [data-tab=\"links\"]').textContent.trim()")
            check(f"[lang {lang}] D. メニューと見出しが{TITLES[lang]}", TITLES[lang] in nav and TITLES[lang] in view, f"{nav!r}")
            check(f"[lang {lang}] D. サイエンスラボの名前が{SCIENCE_NAMES[lang]}", SCIENCE_NAMES[lang] in view)
            if lang != "ja":
                check(f"[lang {lang}] D. 日本語(かな)が混ざらない", not KANA.search(view.replace("α", "")), view[:160])
            check(f"[lang {lang}] D. 未訳キーの生表示がない", "links." not in view and "nav." not in view, view[:160])
        except Exception as e:  # noqa: BLE001
            check(f"[lang {lang}] D. 例外なし", False, f"{type(e).__name__}: {str(e)[:300]}")
        finally:
            s.close()


def check_phone(pw, base: str):
    for br in ("webkit", "chromium"):
        for w in (320, 360, 390, 430):
            s = Session(pw, base, br, PHONE(w), lang="ja")
            try:
                open_links_tab(s)
                r = s.page.evaluate("({sw: document.documentElement.scrollWidth, iw: window.innerWidth,"
                                    " b: (() => { const e = document.querySelector('#view a[data-link-id]');"
                                    " const x = e.getBoundingClientRect(); return {l: x.left, r: x.right, h: x.height}; })()})")
                check(f"[phone {br}/{w}] F. 横にはみ出さず、ボタンが画面内に収まる",
                      r["sw"] <= r["iw"] and r["b"]["l"] >= 0 and r["b"]["r"] <= r["iw"], str(r))
            except Exception as e:  # noqa: BLE001
                check(f"[phone {br}/{w}] F. 例外なし", False, f"{type(e).__name__}: {str(e)[:300]}")
            finally:
                s.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True, help="MULTIUSER=1 の隔離サーバー(ゲストとして見る)")
    ap.add_argument("--admin-base", help="MULTIUSER=0 の隔離サーバー(常に管理者)")
    a = ap.parse_args()
    for u in (a.base, a.admin_base):
        if u and urlparse(u).hostname not in ("127.0.0.1", "localhost"):
            print("中止: 127.0.0.1/localhost の隔離サーバーのみ(本番には向けない)")
            return 2
    base = a.base.rstrip("/")
    with sync_playwright() as pw:
        print("== ゲスト: タブ・隔離・中身・記録・戻る")
        check_nav_and_isolation(pw, base, "guest")
        print("== 4言語")
        check_languages(pw, base)
        print("== スマホ幅")
        check_phone(pw, base)
        if a.admin_base:
            print("== 管理者: タブの並び・中身")
            check_nav_and_isolation(pw, a.admin_base.rstrip("/"), "admin")
    ng = [r for r in RESULTS if not r[0]]
    print(f"\n{len(RESULTS) - len(ng)}/{len(RESULTS)} OK")
    for _, name, detail in ng:
        print("NG:", name, detail)
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
