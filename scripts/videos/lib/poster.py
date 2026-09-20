"""ポスター画像(JPEG)の生成。

HTMLテンプレートを Playwright(Chromium)でスクリーンショットして作る
(Pillow が無いため)。日本語フォントは macOS 標準のヒラギノがそのまま使える。
容量上限(既定 60KB)に収まる最大の品質を探索する。

再生ボタン(▶)や「🔊 音が流れます」の注意書きは **焼き込まない**
(ページ側のUIが重ねるため)。
"""

from __future__ import annotations

import base64
from pathlib import Path

from playwright.async_api import async_playwright

# 動画のダークテーマ(アプリの --bg/--panel/--accent 等)に合わせた共通CSS。
BASE_CSS = """
:root { --bg:#10161e; --panel:#1f2733; --panel2:#29323f; --line:#38445a;
  --text:#e6edf3; --muted:#a7b6c8; --accent:#4da3ff; --accent2:#36c98d;
  --warn:#ffd166; }
* { box-sizing:border-box; }
html,body { margin:0; padding:0; }
body { width:540px; height:960px; overflow:hidden; background:var(--bg);
  color:var(--text);
  font-family:-apple-system,"Hiragino Sans","Hiragino Kaku Gothic ProN",
    "Yu Gothic UI",Meiryo,sans-serif; position:relative; }
.brand { position:absolute; left:36px; top:34px; font-size:23px;
  font-weight:800; color:var(--accent); letter-spacing:.03em; }
.h1 { position:absolute; left:36px; right:36px; top:88px; font-size:64px;
  font-weight:900; line-height:1.18; letter-spacing:.01em; }
.h1 em { font-style:normal; color:var(--warn); }
.lead { position:absolute; left:36px; right:36px; font-size:26px;
  line-height:1.5; color:var(--muted); font-weight:600; }
.shot { position:absolute; border-radius:16px; border:1.5px solid var(--line);
  box-shadow:0 14px 34px rgba(0,0,0,.55); overflow:hidden; background:#161c23; }
.shot img { display:block; width:100%; }
.chips { position:absolute; left:36px; right:36px; display:flex; gap:12px;
  flex-wrap:wrap; }
.chip { font-size:21px; font-weight:800; color:#0b1017; background:var(--accent);
  border-radius:999px; padding:9px 18px; }
.chip.g { background:var(--accent2); }
"""


def data_url(png_or_jpg: bytes, mime: str = "image/png") -> str:
    return f"data:{mime};base64," + base64.b64encode(png_or_jpg).decode()


async def render_poster(body_html: str, out: Path, *, css: str = "",
                        width: int = 540, height: int = 960,
                        max_bytes: int = 56_000) -> dict:
    """body_html を width x height の JPEG にする。max_bytes 以下で最大の
    品質を選ぶ(それでも収まらなければ例外)。"""
    html = (f"<!doctype html><html lang='ja'><head><meta charset='utf-8'>"
            f"<style>{BASE_CSS}{css}</style></head><body>{body_html}</body>"
            f"</html>")
    out.parent.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch()
        try:
            ctx = await browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=1, locale="ja-JP")
            page = await ctx.new_page()
            await page.set_content(html)
            await page.evaluate("document.fonts.ready")
            await page.wait_for_timeout(300)
            best = None
            for q in range(92, 39, -4):
                data = await page.screenshot(type="jpeg", quality=q)
                if len(data) <= max_bytes:
                    best = (q, data)
                    break
            if best is None:
                raise RuntimeError(
                    f"ポスターが{max_bytes}バイトに収まりません(q=40でも"
                    f"{len(data)}バイト)。デザインを単純にしてください")
            out.write_bytes(best[1])
            return {"path": str(out), "bytes": len(best[1]), "quality": best[0],
                    "size": f"{width}x{height}"}
        finally:
            await browser.close()
