"""トップページ(`/`)の「クローラーが読める見出しと本文」の検査(2026-10-25・ver1.5.20)。

  .venv/bin/python scripts/check_index_crawler.py [--browsers chromium,webkit]   # 0=全部OK

**隔離サーバー専用・本番には向けない**。一時データ領域でアプリをuvicornとして起動し、アプリ(127.0.0.1)以外への
通信は全て止める(Googleタグの通信が本番の広告アカウントへ届かないように)。

A. 生のHTML(JSを動かさないクローラーが見るもの)
  1. h1がちょうど1つで、画面に出る(sr-only=視覚的に隠す指定ではない)・短い・「サブスクなし/前払い」を含む
  2. h2が5つ以上・質問形の見出しを含む・公開ページ(用語集/フレーズ集/クロスワード/about)への通常リンク
  3. 本文に書いた数字が、アプリ本体の定数・画面の文言と一致(無料範囲=access_tiers・最小チャージ=PRICE_TABLE・
     収録数=welcome画面のheroCounts)
  4. 誇大な断定語・他社名・禁止用語ドメイン名が無い。title/meta description/canonical/JSON-LDは従来どおり
  5. HEAD / も200
B. 実ブラウザ(JSあり/なし)
  6. JSなし: h1が実際に画面に出て(大きさ>0・クリップされない)、本文も見える
  7. JSあり・ゲストの `/`: 案内ブロックは消え、画面のh1はようこそ画面の1つだけ(二重にならない)
  8. JSあり・`/?tab=vocab`(広告の着地): 案内ブロックが最初から出ない・英単語の画面が出る
"""
import argparse, os, re, socket, subprocess, sys, tempfile, time, urllib.request
from html.parser import HTMLParser
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--browsers", default="chromium,webkit")
args = ap.parse_args()

REPO = os.environ.get("REPO") or str(Path(__file__).resolve().parents[1])
sys.path.insert(0, REPO)
tmp = tempfile.mkdtemp(prefix="eigo_index_crawler_")
os.environ.update({"DATA_DIR": tmp, "MULTIUSER": "1", "ALLOW_FRESH_DB": "1", "SESSION_SECRET": "preview",
                   "OPENAI_API_KEY": "preview-not-used", "ALLOWED_HOSTS": "", "PUBLIC_BASE_URL": ""})

ok = fail = 0


def check(label, cond, extra=""):
    global ok, fail
    if cond:
        ok += 1
        print("OK  ", label)
    else:
        fail += 1
        print("FAIL", label, extra)


class Outline(HTMLParser):
    """クローラーが見る形(script/styleを除いた文字・見出し・リンク)を取り出す。"""

    def __init__(self):
        super().__init__()
        self.skip = 0
        self.stack = []          # 開いている要素の(タグ, 属性)
        self.h = []              # (タグ, 文字, 属性)
        self.links = []          # 文書全体のリンク
        self.seo_links = []      # #seoStatic(クローラー向けブロック)の中のリンクだけ
        self._in_seo = 0
        self.text = []
        self._cur = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "noscript"):
            self.skip += 1
        if tag in ("h1", "h2", "h3"):
            self._cur = [tag, "", a]
        if tag == "article" and a.get("id") == "seoStatic":
            self._in_seo = 1
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self._in_seo:
                self.seo_links.append(a["href"])

    def handle_endtag(self, tag):
        if tag == "article":
            self._in_seo = 0
        if tag in ("script", "style", "noscript") and self.skip:
            self.skip -= 1
        if tag in ("h1", "h2", "h3") and self._cur:
            self.h.append(tuple(self._cur))
            self._cur = None

    def handle_data(self, d):
        if self.skip:
            return
        self.text.append(d)
        if self._cur:
            self._cur[1] += d


# ---- A. 生のHTML ----
from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402
from app.services import access_tiers  # noqa: E402
from app.routers.fulfillment import PRICE_TABLE  # noqa: E402

with TestClient(app) as tc:
    r = tc.get("/")
    raw = r.text
    check("A0 GET / は200", r.status_code == 200)
    check("A0 HEAD / も200", tc.head("/").status_code == 200)

o = Outline()
o.feed(raw)
h1 = [h for h in o.h if h[0] == "h1"]
h2 = [h for h in o.h if h[0] == "h2"]
body_text = re.sub(r"\s+", " ", "".join(o.text))

check("A1 h1はちょうど1つ", len(h1) == 1, str(len(h1)))
h1t = re.sub(r"\s+", " ", h1[0][1]).strip() if h1 else ""
check("A1 h1は視覚的に隠していない(sr-onlyなし)", "sr-only" not in (h1[0][2].get("class", "") if h1 else "sr-only")
      and "sr-only" not in raw[:raw.find("<div id=\"app\">")] , raw[:200])
check("A1 h1は70字以内(詰め込みでない)", 0 < len(h1t) <= 70, f"{len(h1t)}字: {h1t}")
check("A1 h1に『サブスクなし』『前払い』『nyangailab』を含む", all(w in h1t for w in ("サブスクなし", "前払い", "nyangailab")), h1t)
check("A2 h2が5つ以上", len(h2) >= 5, str(len(h2)))
check("A2 質問形の見出し(？)を3つ以上含む", sum("？" in h[1] for h in h2) >= 3)
for href in ("/glossary", "/phrasebook", "/crossword", "/static/about.html"):
    check(f"A2 案内ブロック内の通常リンク {href}", href in o.seo_links)
check("A2 本文は800字以上(JSなしで読める量)", len(body_text) >= 800, str(len(body_text)))

# 数字の整合(アプリ本体の定数・画面の文言と一致させる)
fmt = lambda n: f"{n:,}"
check("A3 未登録の無料音声=単語/フレーズの定数と一致",
      f"単語{fmt(access_tiers.GUEST_WORDS_LIMIT)}語・フレーズ{fmt(access_tiers.GUEST_PHRASES_LIMIT)}件" in body_text)
check("A3 無料登録の無料音声=定数と一致",
      f"単語{fmt(access_tiers.FREE_WORDS_LIMIT)}語・フレーズ{fmt(access_tiers.FREE_PHRASES_LIMIT)}件" in body_text)
check("A3 最小チャージ額=PRICE_TABLEの最小額", f"¥{min(PRICE_TABLE)}" in body_text, str(min(PRICE_TABLE)))
views = (Path(REPO) / "static/js/views.js").read_text(encoding="utf-8")
m = re.search(r'words:\s*"([\d,]+)",\s*phrases:\s*"([\d,]+)",\s*domains:\s*"([\d,]+)"', views)
check("A3 収録数の元(ようこそ画面のheroCounts)を読めた", bool(m))
if m:
    w, p, d = m.groups()
    check("A3 収録数=ようこそ画面と同じ(単語/フレーズ/分野)",
          f"単語{w}語以上" in body_text and f"フレーズ{p}件以上" in body_text and f"{d}分野以上" in body_text, str(m.groups()))

# 書いてはいけないもの
for bad in ("絶対", "必ず", "確実", "ペラペラ", "Duolingo", "スタディサプリ", "mikan", "世界一", "日本一", "最安"):
    check(f"A4 NG語『{bad}』なし", bad not in body_text)
check("A4 禁止用語ドメインの語を直接書いていない", "禁止用語" not in raw)
check("A4 title従来どおり", "<title data-i18n=\"meta.indexTitle\">サブスク疲れに前払い制の安いAI英語学習アプリ" in raw)
check("A4 meta description従来どおり", 'name="description"' in raw and "サブスク疲れなら前払い制へ" in raw)
check("A4 canonical従来どおり", '<link rel="canonical" href="https://study.nyangailab.com/" />' in raw)
check("A4 JSON-LD(SoftwareApplication+Organization)従来どおり", '"SoftwareApplication"' in raw and '"Organization"' in raw)
check("A4 案内ブロックは#viewの中にある(JSが描画し直すと置き換わる)",
      raw.find('<section id="view"') < raw.find('id="seoStatic"') < raw.find("</section>", raw.find('<section id="view"')))

# ---- B. 実ブラウザ ----
s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
BASE = f"http://127.0.0.1:{port}"
server = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(port), "--log-level", "warning"],
                          cwd=REPO, env=dict(os.environ), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
try:
    for _ in range(60):
        try:
            if urllib.request.urlopen(BASE + "/api/health", timeout=1).status == 200:
                break
        except Exception:
            time.sleep(0.5)
    else:
        raise SystemExit("サーバーが起動しない")

    from playwright.sync_api import sync_playwright

    def run(pw, bname):
        P = bname + ": "
        browser = getattr(pw, bname).launch()
        blocked = []

        def guard(route):
            if route.request.url.startswith(BASE):
                return route.continue_()
            blocked.append(route.request.url)
            return route.abort()

        def page_for(js, viewport):
            ctx = browser.new_context(locale="ja-JP", viewport=viewport, java_script_enabled=js)
            ctx.route("**/*", guard)
            return ctx, ctx.new_page()

        for label, vp in (("PC", {"width": 1100, "height": 800}), ("スマホ", {"width": 390, "height": 800})):
            # 6. JSなし
            ctx, pg = page_for(False, vp)
            pg.goto(BASE + "/", wait_until="load")
            box = pg.locator("#seoStatic h1").bounding_box()
            check(P + f"B6 {label} JSなし: h1が画面に出る(大きさ>0)", bool(box) and box["width"] > 50 and box["height"] > 10, str(box))
            check(P + f"B6 {label} JSなし: h1が横にはみ出さない", bool(box) and box["x"] >= 0 and box["x"] + box["width"] <= vp["width"] + 1, str(box))
            check(P + f"B6 {label} JSなし: 本文のリンクが見える", pg.locator("#seoStatic a[href='/glossary']").is_visible())
            hs = pg.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
            check(P + f"B6 {label} JSなし: 横スクロールが出ない", hs)
            if bname == "chromium" and label == "PC":
                pg.screenshot(path=os.path.join(tmp, "no_js_pc.png"), full_page=True)
            if bname == "chromium" and label == "スマホ":
                pg.screenshot(path=os.path.join(tmp, "no_js_phone.png"), full_page=True)
            ctx.close()

        # 7. JSあり・ゲストの /
        ctx, pg = page_for(True, {"width": 1100, "height": 800})
        pg.goto(BASE + "/", wait_until="load")
        try:
            pg.wait_for_selector(".welcome-hero", timeout=15000)
        except Exception:
            pass
        check(P + "B7 JSあり: ようこそ画面が出る", pg.locator(".welcome-hero").count() == 1)
        check(P + "B7 JSあり: 案内ブロックは置き換わって消える", pg.locator("#seoStatic").count() == 0)
        check(P + "B7 JSあり: 画面のh1はちょうど1つ(二重でない)", pg.locator("h1").count() == 1, str(pg.locator("h1").count()))
        check(P + "B7 JSあり: 隠しh1(.sr-only)は無い", pg.locator("h1.sr-only").count() == 0)
        ctx.close()

        # 8-a. app.jsを遮断しても、?tab=付きなら案内ブロックはインラインJSだけで最初から消える(速いAPIでの置き換えと競合しない厳密な検証)
        ctx, pg = page_for(True, {"width": 390, "height": 800})
        ctx.route("**/static/js/app.js*", lambda route: route.abort())
        pg.goto(BASE + "/?tab=vocab", wait_until="load")
        check(P + "B8a app.js遮断+/?tab=vocab: インラインJSだけで案内ブロックが消える", pg.locator("#seoStatic").count() == 0)
        pg.goto(BASE + "/?utm_source=x&gclid=1&tab=vocab", wait_until="load")
        check(P + "B8a app.js遮断+他のパラメータ付き: 同じく消える", pg.locator("#seoStatic").count() == 0)
        pg.goto(BASE + "/", wait_until="load")
        check(P + "B8a app.js遮断+/(tabなし): 案内ブロックは残る(クローラーと同じ見え方)", pg.locator("#seoStatic").count() == 1)
        ctx.close()

        # 8. 広告の着地 /?tab=vocab
        ctx, pg = page_for(True, {"width": 390, "height": 800})
        pg.goto(BASE + "/?tab=vocab", wait_until="domcontentloaded")
        # 描画前でも案内ブロックが出ていないこと(DOM構築直後に確認)
        check(P + "B8 /?tab=vocab: 案内ブロックが最初から無い", pg.locator("#seoStatic").count() == 0)
        try:
            pg.wait_for_selector("#pageTitle", timeout=15000)
        except Exception:
            pass
        check(P + "B8 /?tab=vocab: 英単語の画面が出る", pg.locator("#pageTitle").count() == 1)
        check(P + "B8 /?tab=vocab: h1は1つ", pg.locator("h1").count() == 1, str(pg.locator("h1").count()))
        ctx.close()
        browser.close()
        check(P + "アプリ以外への通信は全て止めた(止めた宛先はGoogleタグ系のみ・アプリ宛は止めていない)",
              all(not u.startswith(BASE) for u in blocked) and all(("google" in u or "gstatic" in u or "doubleclick" in u) for u in blocked),
              str(blocked[:5]))

    with sync_playwright() as pw:
        for b in [x.strip() for x in args.browsers.split(",") if x.strip()]:
            run(pw, b)
finally:
    server.terminate()
    try:
        server.wait(timeout=10)
    except Exception:
        server.kill()

print(f"\n{ok} OK / {fail} FAIL  (スクリーンショット: {tmp}/no_js_*.png)")
sys.exit(1 if fail else 0)
