"""① 英フレーズ「失礼にならない表現」(そっけない“No.”を上品に言い換える)。

ストーリーボード: scripts/videos/storyboards/phrase_polite.md

題材: ショーケース・フレーズ `I'm afraid that won't be possible.`
    (app/services/access_tiers.py の SHOWCASE_PHRASES。シーン=「直訳で失礼に響く
    表現→丁寧な言い方(1)」。ゲスト無料範囲の外だが例外で全員が無料再生できる1件。
    ゲストのミニフレーズ一覧の先頭に「✨まずはここから」として固定される。)
    ペア相手の `No.` はゲストには🔒なので画面には出さない(字幕で言及するだけ)。
    ローカルと本番でidが違うため、(英語, シーン)で解決する。
"""

from __future__ import annotations

from lib import poster as P
from lib.content import require_guest_playable_phrase
from lib.stage import DEFAULT_HIDE

NAME = "phrase_polite"
TITLE = "英フレーズ: そっけない“No.”を上品に言い換える(失礼にならない表現)"
DURATION = 19.6
HIDE = DEFAULT_HIDE

TARGET = "I'm afraid that won't be possible."
SCENE = "直訳で失礼に響く表現→丁寧な言い方(1)"


async def _nuance_scroll_target(stage) -> float:
    """ニュアンス段落がモーダルのヘッダ直下に来るスクロール量。"""
    return await stage.app.evaluate(
        """() => { const box = document.querySelector('.modal-box');
          const head = box.querySelector('.modal-head');
          const p1 = box.querySelectorAll('.modal-body p')[1];   // ニュアンス
          const want = box.scrollTop + p1.getBoundingClientRect().top
            - head.getBoundingClientRect().bottom - 6;
          return Math.min(want, box.scrollHeight - box.clientHeight); }""")


async def prepare(stage, ctx) -> None:
    """録画前: 画面を撮影開始の状態まで進め、ポスター用の実画面クロップを撮る。"""
    ctx["phrase"] = require_guest_playable_phrase(
        ctx["data_dir"], TARGET, SCENE)
    await stage.load_app("/")
    await stage.go_tab("phrases")
    app = stage.app
    await app.wait_for_selector("#rows tr.featured-row", timeout=20000)

    # 対象行に目印(data-vid)を付ける。ゲストの一覧では先頭に固定される
    # ("✨まずはここから"の見出し行の直後)。
    await stage.mark(
        """return [...document.querySelectorAll('#rows tr.featured-row')]
             .find(tr => tr.children[1].textContent.trim() === %r);""" % TARGET,
        "target")
    # 「✨まずはここから」の見出し行が見えるように、見出し行を上端に合わせる
    await app.evaluate(
        """() => { const row = document.querySelector('[data-vid="target"]');
          const head = row.previousElementSibling;
          const top = (head && head.classList.contains('lgh-row') ? head : row)
            .getBoundingClientRect().top + window.scrollY - 8;
          window.scrollTo(0, top); }""")
    await stage.page.wait_for_timeout(500)

    # --- ポスター用クロップ(カード上部=再生ボタン〜詳細ボタン) ---
    card = await stage.rect('[data-vid="target"]')
    det = await stage.rect('[data-vid="target"] .detail-cell button')
    clip = {"x": card["x"], "y": card["y"], "width": card["w"],
            "height": det["y"] + det["h"] + 8 - card["y"]}
    ctx["crop_card"] = await stage.page.screenshot(clip=clip, type="png")

    # --- モーダルを開いて、ニュアンス〜類似表現を切り出す(その後閉じる) ---
    await app.evaluate(
        "document.querySelector('[data-vid=\"target\"] .detail-cell button')"
        ".click()")
    await app.wait_for_selector(".modal-body p:nth-child(3)", timeout=15000)
    await stage.page.wait_for_timeout(500)
    await app.evaluate(
        "t => document.querySelector('.modal-box').scrollTo(0, t)",
        await _nuance_scroll_target(stage))
    await stage.page.wait_for_timeout(300)
    ps = await app.evaluate(
        """() => [...document.querySelectorAll('.modal-body p')].map(p => {
             const r = p.getBoundingClientRect();
             return {t: p.textContent.slice(0, 8), x: r.x, y: r.y, w: r.width,
                     h: r.height}; })""")
    # ps[0]=見出し(英日) ps[1]=ニュアンス ps[2]=類似表現 ps[3]=由来・背景
    box = await stage.rect(".modal-box")
    top = ps[1]["y"] - 8
    bottom = ps[2]["y"] + ps[2]["h"] + 8
    clip = {"x": box["x"], "y": top, "width": box["w"], "height": bottom - top}
    ctx["crop_modal"] = await stage.page.screenshot(clip=clip, type="png")
    ctx["modal_paragraphs"] = [p["t"] for p in ps]
    await app.evaluate("document.querySelector('#mClose').click()")
    await stage.page.wait_for_timeout(400)
    await app.evaluate(
        """() => { const row = document.querySelector('[data-vid="target"]');
          const head = row.previousElementSibling;
          const top = (head && head.classList.contains('lgh-row') ? head : row)
            .getBoundingClientRect().top + window.scrollY - 8;
          window.scrollTo(0, top); }""")
    await stage.page.wait_for_timeout(400)


async def perform(stage, ctx) -> None:
    """録画中のタイムライン(t=0 が動画の先頭)。"""
    T = stage
    row = '[data-vid="target"]'

    # 字幕(ページ側タイマーで壁時計に合わせて出し入れ・ゆっくりフェード)
    await T.caption(
        "そっけない“No.”を、<br><em>上品に言い換えるなら？</em>", 0.3, 4.6)
    await T.caption(
        "“I’m afraid”は「怖い」ではなく<br><em>「残念ながら」</em>", 4.9, 8.2)
    await T.caption(
        "ニュアンスや<br><em>似た言い方</em>もまとめて確認", 8.6, 12.7)
    await T.caption(
        "「残念ながら」の一言で<br><em>断りがやわらかく</em>なる", 13.0, 16.2)
    await T.end_card(
        "<div class='brand'>🐱 nyangailab</div>"
        "<div class='main'>登録なしで、<br>いますぐ試せます</div>"
        "<div class='sub'>閲覧と一部の音声は無料</div>", 16.4)

    # 1) 男声🆓をタップ(冒頭で即・音が鳴る)
    await T.at(0.6)
    await T.tap(row + " .voice-m")
    # 2) 女声🆓をタップ
    await T.at(4.7)
    await T.tap(row + " .voice-f")
    # 3) 詳細を開く
    await T.at(8.2)
    await T.tap(row + " .detail-cell button")
    # 4) モーダル内をゆっくりスクロール
    #    (ニュアンス→類似表現 → さらに下へ: 由来・背景=「怖い」ではなく「残念ながら」)
    await T.at(9.8)
    await T.scroll(await _nuance_scroll_target(T), 2200, ".modal-box")
    await T.at(12.9)
    bottom = await T.app.evaluate(
        "() => { const b = document.querySelector('.modal-box');"
        " return b.scrollHeight - b.clientHeight; }")
    await T.scroll(bottom, 2200, ".modal-box")
    await T.at(DURATION)


# ---- ポスター ---------------------------------------------------------------

POSTER_CSS = """
.brand { top:28px; }
.eyebrow { position:absolute; left:36px; top:66px; font-size:27px;
  font-weight:800; color:var(--muted); letter-spacing:.04em; }
.h1 { top:98px; font-size:56px; }
.chips { top:236px; }
.stack { position:absolute; left:0; right:0; top:296px; display:flex;
  flex-direction:column; gap:14px; }
.shot { position:relative; }
.shot.card { margin-left:24px; width:466px; }
.shot.modal { margin-left:50px; width:466px; }
"""


def poster_body(ctx) -> str:
    card = P.data_url(ctx["crop_card"])
    modal = P.data_url(ctx["crop_modal"])
    return f"""
<div class="brand">🐱 nyangailab</div>
<div class="eyebrow">そっけない</div>
<div class="h1"><em>“No.”</em>を<br>上品に言い換える</div>
<div class="chips"><span class="chip">AIの自然な英語音声</span>
<span class="chip g">登録なしで試せる</span></div>
<div class="stack">
<div class="shot card"><img src="{card}"></div>
<div class="shot modal"><img src="{modal}"></div>
</div>
"""
