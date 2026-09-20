"""② クロスワード(ゲストが遊べる公開サンプル「どうぶつ大集合クロスワード」)。

ストーリーボード: scripts/videos/storyboards/crossword.md

ゲストの導線: ゲームタブ → 「🧩 サンプルクロスワード」→ ゲストが遊べる5個
    (残りは「🔒 登録した方のみ」)。ゲームメニューには「クロスワード作成
    🔒 要登録+課金」のカードが並ぶので、その画面は映さず、サンプルの盤面から
    撮る(prepare で開始まで進めておく)。
題材: 「どうぶつ大集合」(語は全てゲスト無料範囲内・音声保存済み)の
    クリュー1(タテ・RABBIT)。例文ヒント→発音ヒント(実際のAI音声)→入力→正解。
"""

from __future__ import annotations

import json

from lib import poster as P
from lib.content import open_content, require_guest_playable_word
from lib.stage import DEFAULT_HIDE

NAME = "crossword"
TITLE = "クロスワード(ゲストが遊べるサンプル)"
DURATION = 19.6
# トースト(「正解！」)は正解の演出として映す。「🔓 全部答えを見る」「🔓 答えを見る」
# は錠前に見えて🔒と紛らわしいので撮影側で隠す(アプリ本体は無変更)。
HIDE = [h for h in DEFAULT_HIDE if h != "#toast"] + [
    "#cwGiveupAll", '[data-hint="reveal"]']

# 盤面より下が短いページだと盤面を画面の上端まで持ってこられず、上に前の
# カードの端(「ギブアップ」ボタンの断片)が写り込むため、撮影側で下余白を足す。
EXTRA_CSS = ".cw-board-clues { padding-bottom: 320px; }"

SAMPLE_TITLE = "どうぶつ大集合クロスワード"
CLUE_NUMBER, CLUE_DIR = 1, "down"


def _load_sample(data_dir) -> dict:
    conn = open_content(data_dir)
    try:
        row = conn.execute(
            "SELECT id, title, guest_playable, puzzle_json "
            "FROM crossword_samples WHERE title = ?",
            (SAMPLE_TITLE,)).fetchone()
    finally:
        conn.close()
    if row is None:
        raise RuntimeError(f"サンプルが見つかりません: {SAMPLE_TITLE}")
    if not row["guest_playable"]:
        raise RuntimeError("このサンプルはゲストに開放されていません(🔒になる)")
    puzzle = json.loads(row["puzzle_json"])
    clue = next(c for c in puzzle["clues"]
                if c["number"] == CLUE_NUMBER and c["direction"] == CLUE_DIR)
    return {"id": row["id"], "puzzle": puzzle, "clue": clue}


async def prepare(stage, ctx) -> None:
    sample = _load_sample(ctx["data_dir"])
    ctx["sample"] = sample
    clue = sample["clue"]
    # 盤面の全語が、ゲストの無料範囲内で音声保存済みであること(発音ヒント・
    # 正解後の音声ボタンを押しても🔒/エラーにならない)
    for c in sample["puzzle"]["clues"]:
        require_guest_playable_word(ctx["data_dir"], c["word_id"])
    ctx["answer"] = clue["english"]

    await stage.load_app("/")
    await stage.go_tab("games")
    app = stage.app
    await app.wait_for_selector("#cwCardSamples", timeout=20000)
    await app.evaluate("document.querySelector('#cwCardSamples').click()")
    await app.wait_for_selector(f'[data-sample="{sample["id"]}"] button',
                                timeout=20000)
    await app.evaluate(
        "id => document.querySelector(`[data-sample=\"${id}\"] button`)"
        ".click()", sample["id"])
    await app.wait_for_selector(".cw-board .cw-cell", timeout=20000)
    await stage.page.wait_for_timeout(600)

    # 撮影開始の見た目: 盤面(猫のマス)が画面の上端に来る位置
    await _scroll_board_top(stage)
    await stage.page.wait_for_timeout(500)

    # --- ポスター用クロップ: ①ヒントのカード(クリュー文と入力欄) ②盤面 ---
    await stage.app.evaluate("window.scrollTo(0, 0)")
    await stage.page.wait_for_timeout(300)
    await stage.app.evaluate(
        "document.querySelector('#cwDetailCard').scrollIntoView("
        "{block: 'start'})")
    await stage.page.wait_for_timeout(400)
    card = await stage.rect("#cwDetailCard")
    sub = await stage.rect("#cwSubmit")
    clip = {"x": card["x"], "y": card["y"], "width": card["w"],
            "height": sub["y"] + sub["h"] + 5 - card["y"]}
    ctx["crop_clue"] = await stage.page.screenshot(clip=clip, type="png")
    await _scroll_board_top(stage)
    await stage.page.wait_for_timeout(400)
    grid = await stage.rect(".cw-board-grid")
    clip = {"x": max(0, grid["x"] - 6), "y": grid["y"] - 6,
            "width": min(390, grid["w"] + 12), "height": grid["h"] + 12}
    ctx["crop_board"] = await stage.page.screenshot(clip=clip, type="png")


async def _scroll_board_top(stage) -> None:
    await stage.app.evaluate(
        """() => { const g = document.querySelector('.cw-board-grid');
          window.scrollTo(0, g.getBoundingClientRect().top + window.scrollY
            - 12); }""")


async def perform(stage, ctx) -> None:
    T = stage
    clue, answer = ctx["sample"]["clue"], ctx["answer"]
    start_cell = f'.cw-cell[data-cell="{clue["row"]},{clue["col"]}"]'

    await T.caption("猫のマスを埋める<br><em>英単語クロスワード</em>", 0.3, 3.9)
    await T.caption("例文のヒントから<br><em>単語を当てる</em>", 4.2, 6.4)
    await T.caption("<em>発音のヒント</em>も聞ける<br>(AIの自然な英語音声)", 6.8, 8.6)
    await T.caption("英単語を入力して<br><em>「答える」</em>", 8.9, 11.7)
    await T.caption("正解するとマスが埋まり<br><em>発音も聞ける</em>", 12.0, 16.2)
    await T.end_card(
        "<div class='brand'>🐱 nyangailab</div>"
        "<div class='main'>登録なしで、<br>いますぐ試せます</div>"
        "<div class='sub'>サンプルのクロスワードは<br>ゲストでも遊べます</div>",
        16.4)

    # 1) 盤面のマスをタップ → ヒント(クリュー)へ自動スクロール
    await T.at(1.8)
    await T.tap(start_cell)
    # 2) 発音ヒント(🔊)をタップ → AI音声
    await T.at(6.3)
    await T.tap('[data-hint="audio"]')
    # 3) 入力欄をタップして英単語を入力
    await T.at(8.4)
    await T.type_text("#cwAnswerInput", answer, per_char=0.2)
    # 4) 「答える」→ 正解(トースト+マスが文字で埋まる)
    await T.at(10.7)
    await T.tap("#cwSubmit")
    # 5) 正解した語の音声(女声)をタップ
    await T.at(12.3)
    await T.tap("#cwWordTools .voice-f")
    # 6) 盤面まで下へスクロール(マスが文字で埋まっている)
    await T.at(13.9)
    await T.app.evaluate(
        """() => { const g = document.querySelector('.cw-board-grid');
          return window.__vidScroll(null,
            g.getBoundingClientRect().top + window.scrollY - 12, 1600); }""")
    await T.at(DURATION)


# ---- ポスター ---------------------------------------------------------------

POSTER_CSS = """
.brand { top:28px; }
.h1 { top:64px; font-size:58px; }
.lead { top:212px; font-size:26px; }
.col { position:absolute; left:36px; right:36px; top:300px; display:flex;
  flex-direction:column; gap:16px; }
.shot { position:relative; }
"""


def poster_body(ctx) -> str:
    board = P.data_url(ctx["crop_board"])
    clue = P.data_url(ctx["crop_clue"])
    return f"""
<div class="brand">🐱 nyangailab</div>
<div class="h1"><em>猫のマス</em>を<br>単語で埋める</div>
<div class="lead">英単語クロスワードを、<br>登録なしで遊べる</div>
<div class="col">
<div class="shot"><img src="{clue}"></div>
<div class="shot"><img src="{board}"></div>
<div class="chips" style="position:static"><span class="chip">例文・発音ヒント</span>
<span class="chip g">登録なしで試せる</span></div>
</div>
"""
