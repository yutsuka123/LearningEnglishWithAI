"""③ フラッシュ単語(ゲストが実際にできる流れ)。

ストーリーボード: scripts/videos/storyboards/flash_word.md

ゲストの流れ: 「フラッシュ単語」タブ → 設定パネル(既定値のまま)の「▶ 開始」→
    「🔊 出題範囲を選択」ポップアップで「無料で聴ける単語のみ」→ カード。
    設定パネルは長い(セレクト/チェック9個)ので、映さずに prepare で開始まで
    進めておき、動画はカードの表示から始める(設定を触る様子は映さない)。
    ポップアップの本文には🔒の文字が入るため、この動画ではポップアップ自体を
    映していない。
カード: アプリが実際に取得した出題キュー(/api/words/quiz)の先頭から使い、先頭3枚
    が「ゲスト無料範囲内・単語と例文の男声/女声の保存音声が8KB以上」であることを
    撮影前に確認する(満たさなければ失敗)。
"""

from __future__ import annotations

from lib import poster as P
from lib.content import require_guest_playable_word
from lib.stage import DEFAULT_HIDE

NAME = "flash_word"
TITLE = "フラッシュ単語(ゲストが実際にできる流れ)"
DURATION = 19.6
HIDE = DEFAULT_HIDE          # トースト(ゲスト向けの案内)は隠す
N_CARDS = 3


async def prepare(stage, ctx) -> None:
    await stage.load_app("/")
    await stage.go_tab("flashcard")
    app = stage.app
    await app.wait_for_selector("#fcStart", timeout=20000)
    await stage.page.wait_for_timeout(800)
    # 「▶ 開始」→ ポップアップで「無料で聴ける単語のみ」(アプリが実際に取得した
    # 出題キューをそのまま捕まえる)
    await app.evaluate("document.querySelector('#fcStart').click()")
    await app.wait_for_selector(".modal-box button", timeout=10000)
    async with stage.page.expect_response(
            lambda r: "/api/words/quiz" in r.url and "count=true" not in r.url
    ) as resp_info:
        await app.evaluate(
            """() => [...document.querySelectorAll('.modal-box button')]
                 .find(b => b.textContent.includes('無料で聴ける')).click()""")
    queue = await (await resp_info.value).json()
    ctx["queue"] = queue
    await app.wait_for_selector("#fcCard", timeout=15000)
    await stage.page.wait_for_timeout(500)

    cards = queue[:N_CARDS]
    ctx["cards"] = [
        require_guest_playable_word(
            ctx["data_dir"], c["id"], kinds=("word", "example"))
        for c in cards]
    for c in cards:
        if not c.get("is_free_range"):
            raise RuntimeError(f"🔒になる語が先頭にあります: {c['english']}")

    # --- ポスター用クロップ: 答えを表示したカード+ツール列 ---
    await stage.page.touchscreen.tap(
        *(await _center(stage, "#fcCard")))       # 本物のタップでめくる
    await stage.page.wait_for_timeout(900)        # 発音記号・例文訳の取得を待つ
    card = await stage.rect("#fcCard")
    tools = await stage.rect(".fc-tools")
    clip = {"x": card["x"], "y": card["y"], "width": card["w"],
            "height": tools["y"] + tools["h"] + 6 - card["y"]}
    ctx["crop_card"] = await stage.page.screenshot(clip=clip, type="png")
    await stage.page.touchscreen.tap(
        *(await _center(stage, "#fcCard")))       # 裏返して元に戻す
    await stage.page.wait_for_timeout(500)
    await stage.app.evaluate("window.scrollTo(0, 0)")


async def _center(stage, selector: str) -> tuple[float, float]:
    r = await stage.rect(selector)
    return r["x"] + r["w"] / 2, r["y"] + r["h"] / 2


async def perform(stage, ctx) -> None:
    T = stage
    voice_m, voice_f = ".fc-tools .voice-m", ".fc-tools .voice-f"

    await T.caption("単語カードを<br><em>次々にめくって</em>覚える", 0.3, 3.9)
    await T.caption("タップで<br><em>意味と例文</em>を確認", 4.1, 6.4)
    await T.caption("<em>例文の音声</em>も聞ける<br>(AIの自然な英語音声)", 6.7, 10.4)
    await T.caption("スワイプで採点<br><em>⬆覚えた ➡うろ覚え ⬇できない</em>", 10.7, 16.2)
    await T.end_card(
        "<div class='brand'>🐱 nyangailab</div>"
        "<div class='main'>登録なしで、<br>いますぐ試せます</div>"
        "<div class='sub'>閲覧と一部の音声は無料</div>", 16.4)

    # 1) 単語の音声(男声🆓)をタップ → 冒頭で即・音が鳴る
    await T.at(0.6)
    await T.tap(voice_m)
    # 2) カードをタップして答え(意味・例文)を表示
    await T.at(4.3)
    await T.tap("#fcCard", dy=-70)
    # 3) 例文の音声(🔊 例文)をタップ
    await T.at(6.9)
    await T.mark(
        """return [...document.querySelectorAll('.fc-tools button')]
             .find(b => b.textContent.includes('例文'));""", "ex")
    await T.tap('[data-vid="ex"]')
    # 4) 上へスワイプ=覚えた → 次のカード
    await T.at(10.5)
    await T.swipe("#fcCard", 0, -150, duration=0.45)
    # 5) 次のカードをタップで答え → 右へスワイプ=うろ覚え
    await T.at(12.4)
    await T.tap("#fcCard", dy=-70)
    await T.at(14.3)
    await T.swipe("#fcCard", 150, 0, duration=0.45)
    await T.at(DURATION)


# ---- ポスター ---------------------------------------------------------------

POSTER_CSS = """
.brand { top:28px; }
.h1 { top:64px; font-size:56px; }
.lead { top:212px; font-size:26px; }
.col { position:absolute; left:36px; right:36px; top:300px; display:flex;
  flex-direction:column; gap:18px; }
.shot { position:relative; }
"""


def poster_body(ctx) -> str:
    card = P.data_url(ctx["crop_card"])
    return f"""
<div class="brand">🐱 nyangailab</div>
<div class="h1">単語カードを<br><em>めくって</em>覚える</div>
<div class="lead">英語→日本語、例文の音声つき</div>
<div class="col">
<div class="shot"><img src="{card}"></div>
<div class="chips" style="position:static"><span class="chip">AIの自然な英語音声</span>
<span class="chip g">登録なしで試せる</span></div>
</div>
"""
