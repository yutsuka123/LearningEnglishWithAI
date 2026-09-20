"""① 英フレーズ「失礼にならない表現」(丁寧なお願いの英語)。

ストーリーボード: scripts/videos/storyboards/phrase_polite.md

題材の選定について(重要):
    本来の「直訳で失礼に響く表現→丁寧な言い方」ペアのシーン(phrases.id 2983〜・
    レベル600)は、2026-09-20時点で **ゲストの無料範囲(フレーズ750件=レベル昇順)
    に1件も入っていない**(押すと🔒)。動画で映した操作をゲストが同じように
    体験できることを優先し、無料範囲内で「丁寧な依頼」の使い分け・角が立たない
    添え方(類似表現・注意)まで詳細が書かれているフレーズを使う。
    ペアのシーンを主題にするには、そのシーンを無料再生の対象にする実装が必要。
"""

from __future__ import annotations

from lib import poster as P
from lib.content import require_guest_playable_phrase

NAME = "phrase_polite"
TITLE = "英フレーズ: 失礼にならない(丁寧な)お願いの表現"
DURATION = 19.6

TARGET = "Could you speak more slowly, please?"


async def prepare(stage, ctx) -> None:
    """録画前: 画面を撮影開始の状態まで進め、ポスター用の実画面クロップを撮る。"""
    ctx["phrase"] = require_guest_playable_phrase(ctx["data_dir"], TARGET)
    await stage.load_app("/")
    await stage.go_tab("phrases")
    app = stage.app
    await app.wait_for_selector("#rows tr", timeout=20000)

    async def find_idx() -> int:
        return await app.evaluate(
            """(en) => [...document.querySelectorAll('#rows tr')].findIndex(
                 tr => tr.children[1].textContent.trim() === en)""", TARGET)

    idx = await find_idx()
    if idx < 0:   # 先頭ページに無ければ検索で絞る(順序の変化に強くする)
        await app.evaluate(
            """(en) => { const k = document.querySelector('#kw'); k.value = en;
                 k.dispatchEvent(new Event('input', {bubbles: true})); }""",
            TARGET)
        await stage.page.wait_for_timeout(600)
        idx = await find_idx()
    if idx < 0:
        raise RuntimeError("対象フレーズの行が一覧に見つかりません")
    ctx["idx"] = idx

    # 撮影開始の見た目: 対象カードが画面の上端に来る位置
    await stage.scroll_element_to_top("#rows tr", idx, margin=10)
    await stage.page.wait_for_timeout(400)

    # --- ポスター用クロップ(カード上部=再生ボタン〜詳細ボタン) ---
    card = await stage.rect("#rows tr", idx)
    det = await stage.rect("#rows tr .detail-cell button", idx)
    clip = {"x": card["x"], "y": card["y"], "width": card["w"],
            "height": det["y"] + det["h"] + 8 - card["y"]}
    ctx["crop_card"] = await stage.page.screenshot(clip=clip, type="png")

    # --- モーダルを開いて、ニュアンス〜類似表現を切り出す(その後閉じる) ---
    await app.evaluate(
        "i => document.querySelectorAll('#rows tr .detail-cell button')[i].click()",
        idx)
    await app.wait_for_selector(".modal-body p:nth-child(3)", timeout=15000)
    await stage.page.wait_for_timeout(500)
    ps = await app.evaluate(
        """() => [...document.querySelectorAll('.modal-body p')].map(p => {
             const r = p.getBoundingClientRect();
             return {t: p.textContent.slice(0, 8), x: r.x, y: r.y, w: r.width,
                     h: r.height}; })""")
    # ps[0]=見出し(英日) ps[1]=ニュアンス ps[2]=類似表現
    box = await stage.rect(".modal-box")
    top = ps[1]["y"] - 8
    bottom = ps[2]["y"] + ps[2]["h"] + 8
    clip = {"x": box["x"], "y": top, "width": box["w"], "height": bottom - top}
    ctx["crop_modal"] = await stage.page.screenshot(clip=clip, type="png")
    await app.evaluate("document.querySelector('#mClose').click()")
    await stage.page.wait_for_timeout(400)
    await stage.scroll_element_to_top("#rows tr", idx, margin=10)
    await stage.page.wait_for_timeout(400)


async def perform(stage, ctx) -> None:
    """録画中のタイムライン(t=0 が動画の先頭)。"""
    T, idx = stage, ctx["idx"]

    # 字幕(ページ側タイマーで壁時計に合わせて出し入れ・ゆっくりフェード)
    await T.caption("丁寧な“お願い”の英語を<br><em>タップして聞ける</em>", 0.3, 4.6)
    await T.caption("<em>男声・女声</em>を選べる<br>AIの自然な英語音声", 4.9, 8.0)
    await T.caption("ニュアンスや<br><em>似た表現との使い分け</em>も", 8.4, 12.7)
    await T.caption("注意点や<br><em>角が立たない添え方</em>も", 13.0, 16.2)
    await T.end_card(
        "<div class='brand'>🐱 nyangailab</div>"
        "<div class='main'>登録なしで、<br>いますぐ試せます</div>"
        "<div class='sub'>閲覧と一部の音声は無料</div>", 16.4)

    # 1) 男声🆓をタップ(冒頭で即・音が鳴る)
    await T.at(0.6)
    await T.tap(".voice-m", idx)
    # 2) 女声🆓をタップ
    await T.at(4.7)
    await T.tap(".voice-f", idx)
    # 3) 詳細を開く
    await T.at(8.1)
    await T.tap("#rows tr .detail-cell button", idx)
    # 4) モーダル内をゆっくりスクロール(類似表現→注意まで)
    await T.at(9.6)
    target = await T.app.evaluate(
        """() => { const box = document.querySelector('.modal-box');
          const head = box.querySelector('.modal-head');
          const p1 = box.querySelectorAll('.modal-body p')[1];   // ニュアンス
          const want = box.scrollTop + p1.getBoundingClientRect().top
            - head.getBoundingClientRect().bottom - 6;
          return Math.min(want, box.scrollHeight - box.clientHeight); }""")
    await T.scroll(target, 2600, ".modal-box")
    await T.at(DURATION)


# ---- ポスター ---------------------------------------------------------------

POSTER_CSS = """
.brand { top:30px; }
.h1 { top:62px; font-size:58px; }
.chips { top:212px; }
.stack { position:absolute; left:0; right:0; top:270px; display:flex;
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
<div class="h1"><em>失礼にならない</em><br>お願いの英語</div>
<div class="chips"><span class="chip">AIの自然な英語音声</span>
<span class="chip g">登録なしで試せる</span></div>
<div class="stack">
<div class="shot card"><img src="{card}"></div>
<div class="shot modal"><img src="{modal}"></div>
</div>
"""
