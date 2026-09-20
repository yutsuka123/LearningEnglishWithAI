"""撮影用の「ステージ」: アプリを iframe に入れ、字幕・タップ表示を重ねて録画する。

なぜ iframe か
    字幕は「撮影中のページにDOMオーバーレイとして描画して一緒に録画」する
    (ffmpegにdrawtext/libassが無いため)。アプリ本体の上に直接字幕を重ねると
    下端のUIが隠れるので、ステージページ(自前のHTML)の上部にアプリを
    iframeで置き、下部に字幕帯を確保する。アプリ本体のファイルは一切
    変更しない。iframe内のビューポート幅=390px なので、アプリは本番の
    スマホと同じレイアウトで動く。

録画方式
    Playwright の `record_video_dir` は CSSピクセル解像度(390幅)で低画質に
    なるため使わず、Chromiumの CDP `Page.startScreencast`(JPEG・
    deviceScaleFactor=2)で高解像度フレームを受け取り、各フレームの
    タイムスタンプ(エポック秒)を使って ffmpeg で一定fpsの動画に組む。
    フレームのタイムスタンプは、アプリ側の再生時刻(Date.now)と同じ
    壁時計なので、音との同期が数十ms以内で取れる。

音
    Playwrightは音を録れない。ページ内で HTMLMediaElement.play を
    フックして「実際に鳴った音声(mp3のバイト列)・開始時刻・再生速度・
    停止位置」を記録し、後で ffmpeg で映像の時刻に置いて重ねる。
    (アプリが実際に取得した音声をそのまま使うので、声・速度の取り違えが
    起きない。)
"""

from __future__ import annotations

import asyncio
import base64
import json
import time
from dataclasses import dataclass, field
from pathlib import Path

from playwright.async_api import async_playwright

STAGE_PATH = "/__stage.html"

# 撮影側で隠す、本番には出ない/出ても動画の主題に不要なヘッダ要素。
# (アプリ本体は変更せず、iframe内にCSSを足すだけ)
#   #usageBalance/#usageBalanceInfo … 「残り0pt」(ゲストには意味の薄い赤字)
#   #aiState … 開発用の「AI未設定」警告(ダミー鍵のため通常は空だが念のため)
#   #appVer … バージョン表記(動画が版と一緒に古くなるのを避ける)
#   #fontSize … 文字サイズ選択
#   #maintBanner/.toast … メンテナンス予告・トースト
DEFAULT_HIDE = [
    "#usageBalance", "#usageBalanceInfo", "#aiState", "#appVer",
    "#fontSize", "#inputModeWrap", "#maintBanner", "#toast",
]

STAGE_HTML = """<!doctype html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=%(W)d, initial-scale=1">
<title>stage</title>
<style>
  html, body { margin:0; height:100%%; background:#0b1017; overflow:hidden;
    font-family:-apple-system,"Hiragino Sans","Hiragino Kaku Gothic ProN",
      "Yu Gothic UI",Meiryo,sans-serif; }
  #stage { position:relative; width:%(W)dpx; height:%(H)dpx; overflow:hidden; }
  #app { position:absolute; left:0; top:0; width:%(W)dpx; height:%(APPH)dpx;
    border:0; background:#161c23; }
  /* 字幕帯: 常に同じ位置・高コントラスト。点滅させずゆっくりフェード。 */
  #band { position:absolute; left:0; right:0; bottom:0; height:%(BAND)dpx;
    background:#0b1017; border-top:2px solid #2a3a52; }
  #cap { position:absolute; left:16px; right:16px; bottom:0; height:%(BAND)dpx;
    display:flex; align-items:center; justify-content:center; text-align:center;
    color:#fff; font-weight:800; font-size:21px; line-height:1.38;
    letter-spacing:.02em; opacity:0; transition:opacity .6s ease;
    text-shadow:0 1px 2px rgba(0,0,0,.6); }
  #cap em { font-style:normal; color:#ffd166; }
  /* 音が鳴っている間だけ出る「🔊 AI音声」バッジ(音を出さずに見る人にも
     音声が再生されていることが伝わるように。実際の再生イベントに連動) */
  #snd { position:absolute; right:12px; bottom:%(BAND)dpx; margin-bottom:10px;
    z-index:5; padding:6px 13px;
    border-radius:999px; background:rgba(11,16,23,.88);
    border:1.5px solid #4da3ff; color:#fff; font-size:15px; font-weight:800;
    letter-spacing:.02em; opacity:0; transition:opacity .35s ease;
    pointer-events:none; }
  #snd.on { opacity:1; }
  /* タップ位置の表示: 半透明の円がふわっと現れて消える(点滅しない) */
  .rip { position:absolute; width:64px; height:64px; margin:-32px 0 0 -32px;
    border-radius:50%%; border:3px solid rgba(255,255,255,.95);
    background:rgba(255,255,255,.28); box-shadow:0 0 0 2px rgba(0,0,0,.28);
    opacity:0; pointer-events:none;
    animation:rip 1000ms ease-out forwards; }
  @keyframes rip { 0%% { opacity:0; transform:scale(.55); }
    22%% { opacity:1; transform:scale(1); }
    100%% { opacity:0; transform:scale(1.2); } }
  /* スワイプ中の指の表示(円が指に付いて動く) */
  #finger { position:absolute; width:64px; height:64px; margin:-32px 0 0 -32px;
    border-radius:50%%; border:3px solid rgba(255,255,255,.95);
    background:rgba(255,255,255,.28); box-shadow:0 0 0 2px rgba(0,0,0,.28);
    opacity:0; pointer-events:none; transition:opacity .25s ease; }
  #finger.on { opacity:1; }
  /* エンドカード(最後の締め) */
  #end { position:absolute; inset:0; display:flex; flex-direction:column;
    align-items:center; justify-content:center; text-align:center;
    background:radial-gradient(120%% 80%% at 50%% 30%%, #1f2c40 0%%, #0b1017 70%%);
    opacity:0; transition:opacity 1s ease; pointer-events:none; }
  #end.show { opacity:1; }
  #end .brand { font-size:34px; font-weight:800; color:#4da3ff;
    letter-spacing:.03em; margin-bottom:22px; }
  #end .main { font-size:29px; font-weight:800; color:#fff; line-height:1.4; }
  #end .sub { margin-top:16px; font-size:17px; color:#a7b6c8; line-height:1.5; }
</style></head>
<body>
<div id="stage">
  <iframe id="app" name="app" src="about:blank"></iframe>
  <div id="band"></div>
  <div id="cap"></div>
  <div id="snd">🔊 AI音声</div>
  <div id="rips"></div>
  <div id="finger"></div>
  <div id="end"></div>
</div>
</body></html>
"""

# すべてのフレームに入れる init script。
#  - 音声フック(実際に鳴った音声を記録)
#  - 滑らかなスクロール補助(window.__vidScroll)
#  - アプリ側フレームだけに「隠すCSS」を注入
INIT_JS = r"""
(() => {
  if (window.__vidInit) return;
  window.__vidInit = true;

  // ---- 音声フック --------------------------------------------------------
  const post = (o) => {
    try { if (window.__vidAudio) window.__vidAudio(JSON.stringify(o)); }
    catch (e) { /* ignore */ }
  };
  const sent = new Set();
  const origPlay = HTMLMediaElement.prototype.play;
  HTMLMediaElement.prototype.play = function () {
    const a = this;
    if (!a.__vidHooked) {
      a.__vidHooked = true;
      const info = (ev) => ({
        ev, t: Date.now() / 1000, src: a.currentSrc || a.src,
        rate: a.playbackRate, dur: a.duration, pos: a.currentTime,
      });
      const badge = (on) => {
        try {
          const b = window.top.document.getElementById('snd');
          if (b) b.classList.toggle('on', on);
        } catch (e) { /* ignore */ }
      };
      a.addEventListener('playing', () => {
        const o = info('playing');
        if (!o.src || o.src.startsWith('data:')) return;   // 無音のunlock用wav
        badge(true);
        post(o);
        if (!sent.has(o.src)) {
          sent.add(o.src);
          fetch(o.src).then((r) => r.blob()).then((b) => {
            const fr = new FileReader();
            fr.onload = () => post({
              ev: 'blob', src: o.src, b64: String(fr.result).split(',')[1] });
            fr.readAsDataURL(b);
          }).catch(() => {});
        }
      });
      a.addEventListener('pause', () => {
        badge(false);
        const o = info('pause');
        if (o.src && !o.src.startsWith('data:')) post(o);
      });
      a.addEventListener('ended', () => {
        badge(false);
        const o = info('ended');
        if (o.src && !o.src.startsWith('data:')) post(o);
      });
    }
    return origPlay.apply(this, arguments);
  };

  // ---- ゆっくり滑らかなスクロール(easeInOut) -------------------------------
  window.__vidScroll = (sel, top, ms) => new Promise((resolve) => {
    const el = sel ? document.querySelector(sel) : null;
    const get = () => el ? el.scrollTop : window.scrollY;
    const set = (v) => el ? el.scrollTo(0, v) : window.scrollTo(0, v);
    const from = get(), to = top, t0 = performance.now();
    const ease = (p) => p < .5 ? 2 * p * p : 1 - Math.pow(-2 * p + 2, 2) / 2;
    const step = (now) => {
      const p = Math.min(1, (now - t0) / ms);
      set(from + (to - from) * ease(p));
      if (p < 1) requestAnimationFrame(step); else resolve(get());
    };
    requestAnimationFrame(step);
  });

  // ---- アプリ側フレームだけ: scrollIntoView({behavior:'smooth'}) をゆっくりに --
  // (アプリ本来の滑らかスクロールは0.3秒ほどで速く、動画では急な動きに見える。
  //  見た目の到達位置は同じで、時間だけ1.1秒に延ばす)
  if (window.top !== window) {
    const origSIV = Element.prototype.scrollIntoView;
    Element.prototype.scrollIntoView = function (opts) {
      if (opts && typeof opts === 'object' && opts.behavior === 'smooth'
          && (opts.block === 'start' || !opts.block)) {
        const y = this.getBoundingClientRect().top + window.scrollY;
        window.__vidScroll(null, Math.max(0, y), 1100);
        return;
      }
      return origSIV.apply(this, arguments);
    };
  }

  // ---- アプリ側フレームだけ: 撮影用に不要なヘッダ要素を隠す ------------------
  if (window.top !== window) {
    const css = (window.__vidHideCss || '');
    const inject = () => {
      // init script は文書の解析前に走るので head/documentElement が
      // まだ無いことがある(その場合は DOMContentLoaded で再試行)。
      const host = document.head || document.documentElement;
      if (!host || document.getElementById('__vidHide')) return;
      const s = document.createElement('style');
      s.id = '__vidHide';
      s.textContent = css;
      host.appendChild(s);
    };
    document.addEventListener('DOMContentLoaded', inject);
    inject();
  }
})();
"""


@dataclass
class Frame:
    ts: float
    data: bytes


@dataclass
class AudioEvent:
    ev: str
    t: float
    src: str
    rate: float = 1.0
    dur: float = 0.0
    pos: float = 0.0


@dataclass
class Recording:
    """録画結果(エンコード前の生データ)。"""
    frames: list[Frame]
    t0: float            # 動画の t=0 に当たる壁時計(エポック秒)
    duration: float      # 動画の長さ(秒)
    audio_events: list[AudioEvent]
    audio_blobs: dict[str, bytes]
    taps: list[float] = field(default_factory=list)   # タップ時刻(t0基準の秒)


class Stage:
    def __init__(self, base_url: str, *, width: int = 390, height: int = 693,
                 band: int = 108, dsf: int = 2,
                 hide: list[str] | None = None, extra_css: str = ""):
        self.base = base_url.rstrip("/")
        self.W, self.H, self.BAND, self.DSF = width, height, band, dsf
        self.APPH = height - band
        self.hide = list(DEFAULT_HIDE if hide is None else hide)
        self.extra_css = extra_css   # アプリ側フレームに足す撮影用CSS(余白調整等)
        self.pw = None
        self.browser = None
        self.ctx = None
        self.page = None
        self.cdp = None
        self.frames: list[Frame] = []
        self.audio_events: list[AudioEvent] = []
        self.audio_blobs: dict[str, bytes] = {}
        self.taps: list[float] = []
        self.t0 = 0.0
        self._recording = False
        self._pending_acks: set = set()

    # ---- 起動/終了 -----------------------------------------------------------
    async def open(self) -> None:
        self.pw = await async_playwright().start()
        self.browser = await self.pw.chromium.launch()
        self.ctx = await self.browser.new_context(
            viewport={"width": self.W, "height": self.H},
            device_scale_factor=self.DSF, is_mobile=True, has_touch=True,
            locale="ja-JP", timezone_id="Asia/Tokyo", color_scheme="dark",
        )
        stage_html = STAGE_HTML % {
            "W": self.W, "H": self.H, "APPH": self.APPH, "BAND": self.BAND}
        base = self.base

        async def handler(route):
            url = route.request.url
            if url == base + STAGE_PATH:
                await route.fulfill(
                    status=200, body=stage_html,
                    content_type="text/html; charset=utf-8")
            elif url.startswith(base + "/") or url == base:
                await route.continue_()
            elif url.startswith(("data:", "blob:", "about:")):
                await route.continue_()
            else:
                # googletagmanager 等の外部通信は遮断(撮影中に外へ出さない)
                await route.abort()

        await self.ctx.route("**/*", handler)

        async def on_audio(source, payload):
            o = json.loads(payload)
            if o["ev"] == "blob":
                self.audio_blobs[o["src"]] = base64.b64decode(o["b64"])
            else:
                self.audio_events.append(AudioEvent(
                    ev=o["ev"], t=o["t"], src=o["src"],
                    rate=o.get("rate") or 1.0, dur=o.get("dur") or 0.0,
                    pos=o.get("pos") or 0.0))

        await self.ctx.expose_binding("__vidAudio", on_audio)
        # -webkit-tap-highlight-color: Chromiumのモバイルエミュレーションは
        # タップした要素を一瞬シアン色に塗る(実機のiOS Safariでは出ない)。
        # 点滅に見えるので撮影側で消す。
        hide_css = ((", ".join(self.hide) + " { display:none !important; }")
                    if self.hide else "") \
            + " * { -webkit-tap-highlight-color: transparent !important; }" \
            + self.extra_css
        await self.ctx.add_init_script(
            "window.__vidHideCss = " + json.dumps(hide_css) + ";")
        await self.ctx.add_init_script(INIT_JS)
        self.page = await self.ctx.new_page()
        await self.page.goto(base + STAGE_PATH)

    async def close(self) -> None:
        try:
            if self.ctx:
                await self.ctx.close()
            if self.browser:
                await self.browser.close()
        finally:
            if self.pw:
                await self.pw.stop()

    # ---- アプリ(iframe)操作 ----------------------------------------------------
    @property
    def app(self):
        return self.page.frame(name="app")

    async def load_app(self, path: str = "/") -> None:
        """iframeにアプリを読み込む(未ログインのゲスト視点)。"""
        await self.page.evaluate(
            "u => { document.getElementById('app').src = u; }",
            self.base + path)
        await self.page.wait_for_function(
            "() => { const f = document.getElementById('app');"
            " return f.contentDocument && f.contentDocument.readyState"
            " === 'complete' && f.contentDocument.querySelector('#view')"
            " && f.contentDocument.querySelector('#nav button, #nav a'); }",
            timeout=30000)

    async def go_tab(self, tab: str) -> None:
        """メニューのタブへ(ハンバーガーを開かずJSでクリック)。"""
        await self.app.evaluate(
            "t => document.querySelector(`#nav [data-tab=\"${t}\"]`).click()",
            tab)

    async def rect(self, selector: str, nth: int = 0) -> dict:
        r = await self.app.evaluate(
            """([sel, n]) => { const e = document.querySelectorAll(sel)[n];
              if (!e) return null; const r = e.getBoundingClientRect();
              return {x: r.x, y: r.y, w: r.width, h: r.height}; }""",
            [selector, nth])
        if r is None:
            raise RuntimeError(f"要素が見つかりません: {selector}[{nth}]")
        return r

    async def scroll(self, top: float, ms: int, selector: str | None = None):
        await self.app.evaluate(
            "([s, t, m]) => window.__vidScroll(s, t, m)",
            [selector, top, ms])

    async def scroll_element_to_top(
            self, selector: str, nth: int = 0, margin: int = 8) -> None:
        """要素がビューポートの上端(+margin)に来るように即時スクロール。"""
        await self.app.evaluate(
            """([sel, n, m]) => { const e = document.querySelectorAll(sel)[n];
              const y = e.getBoundingClientRect().top + window.scrollY - m;
              window.scrollTo(0, y); }""",
            [selector, nth, margin])

    # ---- 字幕・タップ表示・エンドカード -------------------------------------------
    async def caption(self, html: str, t_in: float, t_out: float) -> None:
        """字幕を t_in〜t_out(動画の秒)に表示。ページ側のタイマーで
        壁時計に合わせて出し入れする(Python側の遅れの影響を受けない)。"""
        await self.page.evaluate(
            """([h, a, b]) => {
              const cap = document.getElementById('cap');
              setTimeout(() => { cap.innerHTML = '<div>' + h + '</div>';
                                 cap.style.opacity = 1; },
                         Math.max(0, a - Date.now()));
              setTimeout(() => { cap.style.opacity = 0; },
                         Math.max(0, b - Date.now()));
            }""",
            [html, (self.t0 + t_in) * 1000, (self.t0 + t_out) * 1000])

    async def end_card(self, html: str, t_in: float) -> None:
        await self.page.evaluate(
            """([h, a]) => { const e = document.getElementById('end');
              e.innerHTML = h;
              setTimeout(() => e.classList.add('show'),
                         Math.max(0, a - Date.now())); }""",
            [html, (self.t0 + t_in) * 1000])

    async def _ripple(self, x: float, y: float) -> None:
        await self.page.evaluate(
            """([x, y]) => { const d = document.createElement('div');
              d.className = 'rip'; d.style.left = x + 'px';
              d.style.top = y + 'px';
              document.getElementById('rips').appendChild(d);
              setTimeout(() => d.remove(), 1200); }""",
            [x, y])

    async def tap(self, selector: str, nth: int = 0, *,
                  lead: float = 0.28, dx: float = 0.0, dy: float = 0.0) -> float:
        """要素をタップ。円のインジケータを先に出し(lead秒)、その後に
        本物のタッチタップを送る。戻り値=タップ時刻(動画の秒)。"""
        r = await self.rect(selector, nth)
        x, y = r["x"] + r["w"] / 2 + dx, r["y"] + r["h"] / 2 + dy
        await self._ripple(x, y)
        await asyncio.sleep(lead)
        await self.page.touchscreen.tap(x, y)
        t = time.time() - self.t0
        self.taps.append(t)
        return t

    async def type_text(self, selector: str, text: str, *,
                        per_char: float = 0.24, nth: int = 0) -> None:
        """入力欄をタップして(円を出す)、1文字ずつ入力する。"""
        await self.tap(selector, nth)
        await asyncio.sleep(0.25)
        await self.page.keyboard.type(text, delay=int(per_char * 1000))

    async def swipe(self, selector: str, dx: float, dy: float, *,
                    duration: float = 0.5, nth: int = 0) -> float:
        """要素の中心からスワイプ(CDPのタッチイベント)。指の円が動く。
        戻り値=指を離した時刻(動画の秒)。"""
        r = await self.rect(selector, nth)
        x0, y0 = r["x"] + r["w"] / 2, r["y"] + r["h"] / 2
        await self.page.evaluate(
            """([x, y]) => { const f = document.getElementById('finger');
              f.style.left = x + 'px'; f.style.top = y + 'px';
              f.classList.add('on'); }""", [x0, y0])
        await asyncio.sleep(0.35)
        cdp = await self.ctx.new_cdp_session(self.page)
        await cdp.send("Input.dispatchTouchEvent", {
            "type": "touchStart", "touchPoints": [{"x": x0, "y": y0}]})
        steps = 12
        for i in range(1, steps + 1):
            x, y = x0 + dx * i / steps, y0 + dy * i / steps
            await cdp.send("Input.dispatchTouchEvent", {
                "type": "touchMove", "touchPoints": [{"x": x, "y": y}]})
            await self.page.evaluate(
                """([x, y]) => { const f = document.getElementById('finger');
                  f.style.left = x + 'px'; f.style.top = y + 'px'; }""", [x, y])
            await asyncio.sleep(duration / steps)
        await cdp.send("Input.dispatchTouchEvent", {
            "type": "touchEnd", "touchPoints": []})
        t = time.time() - self.t0
        self.taps.append(t)
        await self.page.evaluate(
            "() => document.getElementById('finger').classList.remove('on')")
        return t

    async def mark(self, selector_js_predicate: str, name: str) -> None:
        """要素に data-vid を付けて、以後 [data-vid="name"] で指せるようにする。
        predicate は JS 式(関数本体・要素を返す)。"""
        ok = await self.app.evaluate(
            f"""(name) => {{ const e = (() => {{ {selector_js_predicate} }})();
                 if (!e) return false; e.setAttribute('data-vid', name);
                 return true; }}""", name)
        if not ok:
            raise RuntimeError(f"要素を特定できません: {name}")

    # ---- 録画 ---------------------------------------------------------------
    async def start_recording(self) -> None:
        self.cdp = await self.ctx.new_cdp_session(self.page)

        async def ack(sid):
            try:
                await self.cdp.send("Page.screencastFrameAck", {"sessionId": sid})
            except Exception:
                pass

        def on_frame(params):
            if not self._recording:
                return
            self.frames.append(Frame(
                ts=params["metadata"]["timestamp"],
                data=base64.b64decode(params["data"])))
            task = asyncio.ensure_future(ack(params["sessionId"]))
            self._pending_acks.add(task)
            task.add_done_callback(self._pending_acks.discard)

        self.cdp.on("Page.screencastFrame", on_frame)
        self._recording = True
        await self.cdp.send("Page.startScreencast", {
            "format": "jpeg", "quality": 92,
            "maxWidth": self.W * self.DSF, "maxHeight": self.H * self.DSF,
            "everyNthFrame": 1})
        # 最初のフレームが届くのを待ってから t=0 を決める。
        for _ in range(100):
            if self.frames:
                break
            await asyncio.sleep(0.02)
        if not self.frames:
            raise RuntimeError("スクリーンキャストのフレームが届きません")
        self.t0 = time.time() + 0.25

    async def at(self, t: float) -> None:
        """動画の t 秒になるまで待つ。"""
        await asyncio.sleep(max(0.0, self.t0 + t - time.time()))

    async def finish(self, duration: float) -> Recording:
        await self.at(duration)
        self._recording = False
        try:
            await self.cdp.send("Page.stopScreencast")
        except Exception:
            pass
        await asyncio.sleep(0.2)
        return Recording(
            frames=list(self.frames), t0=self.t0, duration=duration,
            audio_events=list(self.audio_events),
            audio_blobs=dict(self.audio_blobs), taps=list(self.taps))
