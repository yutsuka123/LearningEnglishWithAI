"""ver1.5.16 の動作確認スクリプト(2026-10-16)。**隔離サーバー/隔離DATA_DIR専用・本番には絶対に向けない**。

背景(オーナー指示 10/16「フラッシュの既定・ゲストのクイズの案内・ゲストの有料合成・ログイン済みクイズの任意テキスト合成・
グラウンド118.9→121.9を修正しましょう」+「既定をOFF→ONにすると体験が変わる。ONを目立たせればOFFのままでよいのでは」):

  U (コード単体・--unit): `GET /api/learn/tts/item` と `GET /api/learn/samples/{id}/tts` の声の扱い
     U1 ゲスト+事前作成のない声(echo)+保存なし → 402でログインを案内・合成は一切走らない(合成関数が呼ばれない)・ファイルも作られない
     U2 ゲスト+事前作成の声(ash)+保存なし → 合成される(新しい語を追加した直後の取りこぼしを防ぐ・従来どおり)
     U3 未知の声(zzz9)→ ashにそろえる。保存ファイルが声の文字列ごとに増えない
     U4 ゲスト+echo+保存済み → 無料で返る(合成なし)
     U5 ゲストではない利用者+echo+保存なし → 従来どおり合成される(声の選択は変えていない)
     U6 公開サンプル教材: ゲスト+echo+未保存 → 拒否(合成しない)/ゲスト+echo+保存済み → 返る/未知の声はashにそろう
  B (ブラウザ・隔離サーバー): クイズ・絞り込みトグル
     B1 無料登録(残高0)のクイズ: 音声は項目ID指定(/tts/item)・声はash/novaの1つ・POST /api/learn/ttsを呼ばない・出題は絞らない
        範囲外の項目は402(チャージ案内)になり、トーストが出る
     B2 残高ありのクイズ: 範囲外の項目も200で鳴り、再生ごとに少額(0.5pt)が台帳に残る(一覧・フラッシュカードと同じ課金)
     B3 ゲストのクイズ: 「例文の訳」「例文を作る」を押してもAPIを呼ばず、理由と登録リンク(/login#signup)が出る
     B4 「🔊再生できるものだけ」: 既定はOFFのまま(単語一覧/フラッシュ単語/フレーズ一覧/フラッシュフレーズ・ゲスト/無料登録/残高あり)。
        全部は再生できない利用者(ゲスト・残高0)だけ目立つ見た目(.free-only-chip)・残高ありは通常の見た目
     B5 範囲外の再生を断られた(402)瞬間: 未ONのトグルが光り(.free-only-pulse)、トーストに案内が付く。ONにした後は光らない/案内なし
        (残高ありは範囲外でも鳴る=断られないので対象外)

使い方(.envの無いツリー=このworktreeで):
  S=/tmp/c1516_data ; PY=<repo>/.venv/bin/python
  DATA_DIR=$S OPENAI_API_KEY=preview-not-used $PY scripts/check_ver1516.py --unit
  $PY scripts/check_ver1516.py --prepare --data-dir $S
  ALLOW_FRESH_DB=1 MULTIUSER=1 SESSION_SECRET=preview OPENAI_API_KEY=preview-not-used DATA_DIR=$S \\
    $PY -m uvicorn app.main:app --port 8796 &
  $PY scripts/check_ver1516.py --prepare --data-dir $S     # 起動して空DBができてから(再実行しても安全)
  $PY scripts/check_ver1516.py --base http://127.0.0.1:8796 --data-dir $S
Googleタグが入ったページを動かすため、check_signup_form.pyのSessionと同じ遮断をかける。登録メールは`claude-verify-`接頭辞。
"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import sqlite3
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from check_signup_form import RESULTS, Session, check, signup_and_login  # noqa: E402

N_WORDS = 2100      # ログイン無料の範囲(単語2,000)をはみ出す件数
N_PHRASES = 1600    # 同(フレーズ1,500)
GUEST_WORDS, GUEST_PHRASES = 1000, 750
FREE_WORDS, FREE_PHRASES = 2000, 1500
VOICES = ("ash", "nova")
LEVEL_ORDER = ["300-", "300", "350", "400", "450", "500", "550", "600", "650",
               "700", "750", "800", "850", "900", "950", "990", "990+"]


def _h(t: str) -> str:
    return hashlib.sha256(t.encode("utf-8")).hexdigest()[:10]


# ----------------------------------------------------------------------------- U: コード単体
def unit() -> None:
    from app.database import db, init_db
    from app.routers import learn
    from app.services import ai, audio_store, auth

    init_db()
    calls: list[dict] = []
    real_synth = ai.synthesize_speech

    def fake_synth(text, voice="alloy", **kw):
        calls.append({"text": text, "voice": voice, "kw": kw})
        return b"\xff\xfb\x90\x64" + b"\x00" * 413, None

    audio_dir = Path(os.environ["DATA_DIR"]) / "audio"

    def files(pattern: str) -> list[str]:
        return sorted(p.name for p in audio_dir.glob(pattern)) if audio_dir.exists() else []

    with db() as conn:
        ids = [r["id"] for r in conn.execute("SELECT id FROM words WHERE example != '' ORDER BY id LIMIT 8")]
        guest_uid = auth.ensure_guest_user_id(conn)
        conn.execute("INSERT INTO materials (area, title, body, is_public_sample) VALUES "
                     "('reading', 'sample-a', 'This is a public sample passage for the voice test.', 1)")
        mid = conn.execute("SELECT MAX(id) FROM materials").fetchone()[0]
        text_of = {i: conn.execute("SELECT english FROM words WHERE id=?", (i,)).fetchone()["english"] for i in ids}
    w1, w2, w3, w4, w5 = ids[:5]
    sample_text = "This is a public sample passage for the voice test."

    tok = auth.set_current_user_id(guest_uid)
    ai.synthesize_speech = fake_synth
    try:
        # U1
        calls.clear()
        r = learn.tts_item(item_type="word", item_id=w1, voice="echo", kind="word", speed="learn")
        body = r.body.decode("utf-8", "replace")
        check("[U1] ゲスト+事前作成のない声(echo)+保存なし → 402", r.status_code == 402, f"{r.status_code} {body[:60]}")
        check("[U1] 案内はログインを促す文言", "ログイン" in body, body)
        check("[U1] 合成関数は呼ばれない(有料合成が走らない)", not calls, str(calls))
        check("[U1] echoの保存ファイルが作られない", not files(f"word{w1}_word_echo_*"), str(files("*echo*")))
        # U2
        calls.clear()
        r = learn.tts_item(item_type="word", item_id=w2, voice="ash", kind="word", speed="learn")
        check("[U2] ゲスト+事前作成の声(ash)+保存なし → 200", r.status_code == 200, str(r.status_code))
        check("[U2] 合成が1回走り、声はash", len(calls) == 1 and calls[0]["voice"] == "ash", str(calls))
        check("[U2] ash(学習速度)の保存ファイルができる", bool(files(f"word{w2}_word_ash_*")), str(files(f"word{w2}*")))
        calls.clear()
        r = learn.tts_item(item_type="word", item_id=w2, voice="nova", kind="word", speed="native")
        check("[U2] ゲスト+nova+ネイティブ速度+保存なし → 200(事前作成の声なら速度は問わない)",
              r.status_code == 200 and len(calls) == 1 and calls[0]["voice"] == "nova", f"{r.status_code} {calls}")
        # U3
        calls.clear()
        r = learn.tts_item(item_type="word", item_id=w3, voice="zzz9", kind="word", speed="learn")
        check("[U3] 未知の声(zzz9)でも200(ashにそろえる)", r.status_code == 200, str(r.status_code))
        check("[U3] 合成の声はash(任意文字列が合成側のalloyに化けない)", len(calls) == 1 and calls[0]["voice"] == "ash", str(calls))
        check("[U3] 保存ファイル名に未知の声の文字列が入らない", not files("*zzz9*") and bool(files(f"word{w3}_word_ash_*")),
              str(files("*zzz9*")))
        for v in ("a1", "b2", "../c3"):
            learn.tts_item(item_type="word", item_id=w3, voice=v, kind="word", speed="learn")
        check("[U3] 声の文字列を変えて何度呼んでも、保存ファイルは増えない(ashの1つのまま)",
              len(files(f"word{w3}_word_*")) == 1, str(files(f"word{w3}_*")))
        # U4
        with db() as conn:
            audio_store.put(conn, "word", w4, "word", "echo", text_of[w4], b"cached-echo")
        calls.clear()
        r = learn.tts_item(item_type="word", item_id=w4, voice="echo", kind="word", speed="learn")
        check("[U4] ゲスト+echo+保存済み → 無料で返る(保存済みの中身がそのまま)",
              r.status_code == 200 and r.body == b"cached-echo" and not calls, f"{r.status_code} calls={calls}")
        # U6 公開サンプル教材(実際の合成関数を使う=refuse_if_uncachedの経路)
        ai.synthesize_speech = real_synth
        r = learn.sample_material_tts(mid, voice="echo")
        body = r.body.decode("utf-8", "replace")
        check("[U6] 公開サンプル: ゲスト+echo+未保存 → 拒否(422・ログイン案内・合成しない)",
              r.status_code == 422 and "ログイン" in body, f"{r.status_code} {body[:60]}")
        ai.save_tts_cache(sample_text, "echo", b"sample-echo")
        r = learn.sample_material_tts(mid, voice="echo")
        check("[U6] 公開サンプル: ゲスト+echo+保存済み → 返る", r.status_code == 200 and r.body == b"sample-echo",
              f"{r.status_code} {r.body[:20]}")
        ai.save_tts_cache(sample_text, "ash", b"sample-ash")
        r = learn.sample_material_tts(mid, voice="qqq")
        check("[U6] 公開サンプル: 未知の声(qqq)はashにそろう(ashの保存済みが返る)",
              r.status_code == 200 and r.body == b"sample-ash", f"{r.status_code} {r.body[:20]}")
        ai.synthesize_speech = fake_synth
        # U5 ゲストではない利用者(オーナー=管理者)
        tok = auth.set_current_user_id(1)
        calls.clear()
        r = learn.tts_item(item_type="word", item_id=w5, voice="echo", kind="word", speed="learn")
        check("[U5] ゲストではない利用者+echo+保存なし → 従来どおり合成される(声の選択は変えていない)",
              r.status_code == 200 and len(calls) == 1 and calls[0]["voice"] == "echo", f"{r.status_code} {calls}")
    finally:
        ai.synthesize_speech = real_synth


# ----------------------------------------------------------------------------- B: ブラウザ
def prepare(data_dir: str) -> None:
    root = Path(data_dir)
    con = sqlite3.connect(root / "content.db")
    n_words = con.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    if n_words < N_WORDS:
        src = con.execute("SELECT english, japanese, part_of_speech, example FROM words ORDER BY id LIMIT 60").fetchall()
        for i in range(n_words + 1, N_WORDS + 1):
            e, j, pos, ex = src[i % len(src)]
            con.execute("INSERT INTO words (english, japanese, part_of_speech, example) VALUES (?,?,?,?)",
                        (f"{e}{i}", j, pos, ex))
    n_ph = con.execute("SELECT COUNT(*) FROM phrases").fetchone()[0]
    if n_ph < N_PHRASES:
        src = con.execute("SELECT english, japanese, scene FROM phrases ORDER BY id LIMIT 40").fetchall()
        for i in range(n_ph + 1, N_PHRASES + 1):
            e, j, sc = src[i % len(src)]
            con.execute("INSERT INTO phrases (english, japanese, scene) VALUES (?,?,?)", (f"{e} {i}", j, sc))
    # 先頭10件=最も高いレベル(=ゲストにもログイン無料にも範囲外)。本番の10/15確認と同じ「進捗の無い利用者の出題は表の先頭」
    # が範囲外になる形。ゲスト範囲=level 500の先頭1,000件(id 11〜)、ログイン無料=2,000件、残りは level 800。
    con.execute(f"UPDATE words SET level = CASE WHEN id <= 10 THEN '990' WHEN id <= {FREE_WORDS} THEN '500' ELSE '800' END")
    con.execute(f"UPDATE phrases SET level = CASE WHEN id <= 10 THEN '990' WHEN id <= {FREE_PHRASES} THEN '500' ELSE '800' END")
    # 「例文のある語」だけにそろえる(例文ボタンを確実に出す)
    con.execute("UPDATE words SET example = 'This is an example sentence.' WHERE COALESCE(example, '') = ''")
    con.commit()
    audio = root / "audio"
    audio.mkdir(parents=True, exist_ok=True)
    mp3 = bytes.fromhex("fffb9064") + b"\x00" * 413
    n = 0
    for vid, en, ex in con.execute("SELECT id, english, example FROM words"):
        for v in VOICES:
            (audio / f"word{vid}_word_{v}_{_h(en.strip())}.mp3").write_bytes(mp3)
            (audio / f"word{vid}_example_{v}_{_h(ex.strip())}.mp3").write_bytes(mp3)
            n += 2
    for pid, en in con.execute("SELECT id, english FROM phrases"):
        for v in VOICES:
            (audio / f"phrase{pid}_phrase_{v}_{_h(en.strip())}.mp3").write_bytes(mp3)
            n += 1
    con.close()
    print(f"prepared: words={N_WORDS} phrases={N_PHRASES} audio_files={n}")


def in_range(data_dir: str, table: str, limit: int) -> set[int]:
    con = sqlite3.connect(f"file:{data_dir}/content.db?mode=ro", uri=True)
    rank = {lv: i for i, lv in enumerate(LEVEL_ORDER)}
    rows = con.execute(f"SELECT id, level FROM {table}").fetchall()
    con.close()
    rows.sort(key=lambda r: (rank.get(r[1] or "", len(LEVEL_ORDER) + 1), r[0]))
    return {r[0] for r in rows[:limit]}


TOAST_RECORDER = """
(function () {
  window.__toasts = [];
  function start() {
    var t = document.getElementById('toast');
    if (!t) return false;
    var rec = function () { if (t.classList.contains('show') && t.textContent) window.__toasts.push(t.textContent); };
    new MutationObserver(rec).observe(t, {attributes: true, childList: true, characterData: true, subtree: true});
    return true;
  }
  if (!start()) document.addEventListener('DOMContentLoaded', start);
})();
"""


class Spy:
    def __init__(self, page):
        self.quiz_urls: list[str] = []
        self.raw_tts: list[str] = []
        self.ai_calls: list[str] = []
        self.items: list[dict] = []
        page.on("request", self._req)
        page.on("response", self._resp)

    def _req(self, r):
        u = urlparse(r.url)
        if u.path == "/api/learn/tts" and r.method == "POST":
            self.raw_tts.append(r.url)
        if u.path in ("/api/learn/translate", "/api/learn/example") and r.method == "POST":
            self.ai_calls.append(u.path)
        if u.path in ("/api/words/quiz", "/api/phrases/quiz"):
            self.quiz_urls.append(r.url)

    def _resp(self, r):
        u = urlparse(r.url)
        if u.path == "/api/learn/tts/item":
            q = parse_qs(u.query)
            self.items.append({"type": q.get("item_type", [""])[0], "id": int(q.get("item_id", ["0"])[0]),
                               "kind": q.get("kind", [""])[0], "voice": q.get("voice", [""])[0], "status": r.status})

    def reset(self):
        self.quiz_urls.clear(); self.raw_tts.clear(); self.ai_calls.clear(); self.items.clear()


def run_quiz(s: Session, spy: Spy, start_label: str) -> list[str]:
    """開始→「英語を聞く」→「わからない」(答え表示で自動再生)→「例文を聞く」→⭕→2問目→「英語を聞く」。"""
    p = s.page
    s.ctx.add_init_script(TOAST_RECORDER)
    p.goto(s.base + "/?tab=quiz", wait_until="networkidle")
    p.wait_for_timeout(1000)
    spy.reset()
    p.evaluate("window.__toasts = []")
    p.click(f"text={start_label}")
    p.wait_for_selector("#hear", timeout=10000)
    p.wait_for_timeout(1200)
    p.click("#hear")
    p.wait_for_timeout(800)
    p.click("button:has-text('わからない')")
    p.wait_for_selector("#exArea", timeout=10000)
    p.wait_for_timeout(1000)
    ex = p.query_selector("button:has-text('例文を聞く')")
    if ex:
        ex.click()
        p.wait_for_timeout(800)
    p.click("button:has-text('⭕')")
    p.wait_for_selector("#hear", timeout=10000)
    p.wait_for_timeout(1200)
    p.click("#hear")
    p.wait_for_timeout(800)
    return list(p.evaluate("window.__toasts") or [])


def core_db(data_dir: str) -> sqlite3.Connection:
    return sqlite3.connect(f"{data_dir}/core.db", timeout=10)


def set_balance(data_dir: str, email: str, yen: float) -> int:
    con = core_db(data_dir)
    row = con.execute("SELECT id FROM users WHERE email = ? OR username = ?", (email, email)).fetchone()
    assert row, email
    con.execute("UPDATE users SET balance_jpy = ? WHERE id = ?", (yen, row[0]))
    con.commit()
    con.close()
    return row[0]


def ledger(data_dir: str, uid: int) -> list[tuple]:
    con = core_db(data_dir)
    rows = con.execute("SELECT delta_jpy, reason, note FROM balance_ledger WHERE user_id = ? ORDER BY id", (uid,)).fetchall()
    bal = con.execute("SELECT balance_jpy FROM users WHERE id = ?", (uid,)).fetchone()[0]
    con.close()
    return rows, bal


def toggle_state(p) -> list[dict]:
    return p.evaluate("""() => [...document.querySelectorAll('input[type=checkbox][id$="FreeOnly"]')].map(cb => {
        const l = cb.closest('label');
        return {id: cb.id, checked: cb.checked, chip: !!(l && l.classList.contains('free-only-chip')),
                pulse: !!(l && l.classList.contains('free-only-pulse')), visible: !!(l && l.offsetParent !== null)};
    })""")


def open_tab(p, base: str, tab: str):
    p.goto(base + f"/?tab={tab}", wait_until="networkidle")
    p.wait_for_timeout(1200)


FREE_ONLY_TABS = ("vocab", "phrases", "flashcard", "flashphrase")   # 絞り込みトグルのある4画面


def check_toggles(pw, base: str, who: str, s: Session, expect_chip: bool):
    p = s.page
    seen = {}
    for tab in FREE_ONLY_TABS:
        open_tab(p, base, tab)
        for t in toggle_state(p):
            seen[f"{tab}:{t['id']}"] = t      # 単語一覧とフレーズ一覧は同じid(fFreeOnly)なので画面名つきで数える
    ids = sorted(seen)
    check(f"[B4 {who}] 絞り込みトグルが画面で見つかる(単語一覧/フレーズ一覧/フラッシュ単語/フラッシュフレーズの4つ)",
          len(ids) == 4, f"ids={ids}")
    check(f"[B4 {who}] 全てのトグルが既定でOFF(既定は変えていない)", all(not seen[i]["checked"] for i in ids),
          str({i: seen[i]["checked"] for i in ids}))
    if expect_chip:
        check(f"[B4 {who}] 全部は再生できない利用者には目立つ見た目(.free-only-chip)", all(seen[i]["chip"] for i in ids),
              str({i: seen[i]["chip"] for i in ids}))
    else:
        check(f"[B4 {who}] 残高のある利用者は通常の見た目(目立たせない)", all(not seen[i]["chip"] for i in ids),
              str({i: seen[i]["chip"] for i in ids}))


def check_nudge(s: Session, who: str, expect: bool, turn_on: bool = False):
    """範囲外の項目(id=5)を項目ID指定で再生 → 402。未ONのトグルがあれば1タップでONにできる案内(#freeOnlyNudge)が出る。
    ボタンを押すまでトグルは変わらない(勝手にONにしない)。turn_on=Trueなら先にONにしておく(案内は出ない)。"""
    p = s.page
    open_tab(p, s.base, "vocab")
    if turn_on:
        p.evaluate("() => { const d = document.getElementById('vocabFilters'); if (d) d.open = true; }")
        p.check("#fFreeOnly")
        p.wait_for_timeout(600)
    p.evaluate("window.__toasts = []")
    res = p.evaluate("""async () => {
        const m = await import('/static/js/speech.js');
        await m.sayItem('word', 5, 'word', 'ash', 'x');
        await new Promise(r => setTimeout(r, 700));
        const t = document.getElementById('toast');
        const n = document.getElementById('freeOnlyNudge');
        const cb = document.getElementById('fFreeOnly');
        return {toast: t ? t.textContent : '', nudge: n && n.classList.contains('show') ? n.textContent : '',
                checked: cb ? cb.checked : null,
                panelOpen: (document.getElementById('vocabFilters') || {}).open};
    }""")
    if not expect:
        check(f"[B5 {who}] すでにONなら「絞り込む」案内は出ず、断りは従来のトーストで出る",
              (not res["nudge"]) and bool(res["toast"]), str(res))
        return
    check(f"[B5 {who}] 断りの文(サーバーの案内)が吹き出しに入り、トーストと二重に出ない(重なって読めなくなるため)",
          bool(re.search(r"範囲外|チャージ|ログイン", res["nudge"])) and not res["toast"], str(res))
    check(f"[B5 {who}] 「再生できるものだけ」に絞り込める案内(ボタンつき)が出る",
          bool(re.search(r"再生できるものだけ", res["nudge"])) and "絞り込む" in res["nudge"], str(res))
    check(f"[B5 {who}] 案内が出ただけではトグルは変わらない(勝手にONにしない・既定OFFのまま)", res["checked"] is False, str(res))
    n_before = len(s.page.evaluate("performance.getEntriesByType('resource').filter(e => e.name.includes('/api/words?')).map(e => e.name)"))
    p.click("#freeOnlyNudge .free-only-nudge-btn")
    p.wait_for_timeout(1200)
    after = p.evaluate("""() => ({checked: document.getElementById('fFreeOnly').checked,
        panelOpen: document.getElementById('vocabFilters').open,
        shown: document.getElementById('freeOnlyNudge').classList.contains('show'),
        urls: performance.getEntriesByType('resource').filter(e => e.name.includes('/api/words?')).map(e => e.name)})""")
    check(f"[B5 {who}] 案内のボタンを押すとトグルがONになる", after["checked"] is True, str(after))
    check(f"[B5 {who}] 畳まれていた絞り込みパネルも開く(スマホでも結果が見える)", after["panelOpen"] is True, str(after))
    check(f"[B5 {who}] 案内は閉じる", after["shown"] is False, str(after))
    check(f"[B5 {who}] 一覧が free_range_only=true で取り直される", any("free_range_only=true" in u for u in after["urls"][n_before:]),
          str(after["urls"][-3:]))


def check_browser(pw, base: str, data_dir: str):
    w_free = in_range(data_dir, "words", FREE_WORDS)
    ph_free = in_range(data_dir, "phrases", FREE_PHRASES)

    # ---- ゲスト
    s = Session(pw, base, "chromium", dict(pw.devices["Pixel 5"]))
    try:
        check_toggles(pw, base, "ゲスト", s, expect_chip=True)
        check_nudge(s, "ゲスト", expect=True)
        # B3 ゲストのクイズ: 例文の訳/例文を作る
        spy = Spy(s.page)
        p = s.page
        p.goto(base + "/?tab=quiz", wait_until="networkidle")
        p.wait_for_timeout(800)
        spy.reset()
        p.click("text=クイズ開始 (10語)")
        p.wait_for_selector("#hear", timeout=10000)
        p.wait_for_timeout(500)
        p.click("button:has-text('わからない')")
        p.wait_for_selector("#exArea", timeout=10000)
        p.wait_for_timeout(500)
        btn = p.query_selector("#exArea button:has-text('例文の訳')")
        check("[B3] 例文のある語では「例文の訳」ボタンが出る", btn is not None)
        if btn:
            btn.click()
            p.wait_for_timeout(500)
            txt = p.inner_text("#exArea")
            href = p.get_attribute("#exArea a[href='/login#signup']", "href") if p.query_selector("#exArea a[href='/login#signup']") else None
            check("[B3] 押してもAPI(/api/learn/translate)は呼ばれない", "/api/learn/translate" not in spy.ai_calls, str(spy.ai_calls))
            check("[B3] 理由の案内(AI機能・無料登録・チャージしたpt)が出る",
                  "AI機能" in txt and "無料登録" in txt and "pt" in txt, txt)
            check("[B3] 「無料で登録する」リンクが /login#signup を指す", href == "/login#signup", str(href))
            check("[B3] 「ログインすれば使える」とは書かない(無料登録だけでは使えないため)", "ログインすると" not in txt, txt)
            check("[B3] 「失敗」だけの行き止まりの文言ではない", not re.search(r"^失敗$", txt, re.M), txt)
        # フレーズのクイズには項目の例文が無い → 「例文を作る」
        p.goto(base + "/?tab=quiz", wait_until="networkidle")
        p.wait_for_timeout(800)
        spy.reset()
        p.click("text=クイズ開始 (10フレーズ)")
        p.wait_for_selector("#hear", timeout=10000)
        p.click("button:has-text('わからない')")
        p.wait_for_selector("#exArea", timeout=10000)
        p.wait_for_timeout(500)
        gen = p.query_selector("#exArea button:has-text('例文を作る')")
        check("[B3] 例文のないフレーズでは「例文を作る」ボタンが出る", gen is not None)
        if gen:
            gen.click()
            p.wait_for_timeout(500)
            txt = p.inner_text("#exArea")
            check("[B3] 押してもAPI(/api/learn/example)は呼ばれない", "/api/learn/example" not in spy.ai_calls, str(spy.ai_calls))
            check("[B3] 案内と登録リンクが出る(「生成失敗」だけの行き止まりではない)",
                  "AI機能" in txt and p.query_selector("#exArea a[href='/login#signup']") is not None, txt)
    finally:
        s.close()

    # ---- 無料登録(残高0)
    s = Session(pw, base, "chromium", dict(pw.devices["Pixel 5"]))
    try:
        email = signup_and_login(s, "無料登録", "c1516a")
        p = s.page
        spy = Spy(p)
        check_toggles(pw, base, "無料登録(残高0)", s, expect_chip=True)
        check_nudge(s, "無料登録(残高0)", expect=True)
        check_nudge(s, "無料登録(トグルをONにした後)", expect=False, turn_on=True)
        toasts = run_quiz(s, spy, "クイズ開始 (10語)")
        tag = "[B1 無料登録 単語]"
        check(f"{tag} 任意テキストの合成 POST /api/learn/tts を呼ばない", not spy.raw_tts, str(spy.raw_tts))
        check(f"{tag} 項目ID指定の音声 /api/learn/tts/item が呼ばれる(3回以上)", len(spy.items) >= 3, str(spy.items))
        check(f"{tag} 声はash/novaのどちらか1つだけ(事前作成の声)",
              len({i["voice"] for i in spy.items}) == 1 and spy.items[0]["voice"] in VOICES, str(spy.items))
        check(f"{tag} 出題は絞らない(free_range_onlyが付かない・体験を変えない)",
              bool(spy.quiz_urls) and all("free_range_only" not in u for u in spy.quiz_urls), str(spy.quiz_urls))
        exp_ok = {i["id"]: (200 if i["id"] in w_free else 402) for i in spy.items}
        check(f"{tag} 無料範囲内は200・範囲外は402(残高0なので一覧と同じ扱い)",
              all(i["status"] == exp_ok[i["id"]] for i in spy.items), str(spy.items))
        check(f"{tag} 範囲外の項目が実際に含まれている(進捗の無い利用者の出題は表の先頭=範囲外)",
              any(i["id"] not in w_free for i in spy.items), str(spy.items))
        check(f"{tag} 範囲外の再生を断られたらトーストでチャージを案内する(全トーストを記録)",
              any("チャージ" in t for t in toasts), f"toasts={toasts}")
        bad = [t for t in toasts if t.lstrip().startswith("{")]
        check(f"{tag} 生のJSONのトーストは出ない", not bad, f"toasts={toasts}")
        # フレーズ
        toasts = run_quiz(s, spy, "クイズ開始 (10フレーズ)")
        tag = "[B1 無料登録 フレーズ]"
        check(f"{tag} /tts/item・種別phrase・POST /api/learn/tts なし",
              len(spy.items) >= 3 and all(i["type"] == "phrase" for i in spy.items) and not spy.raw_tts,
              f"{spy.items} raw={spy.raw_tts}")
        check(f"{tag} 無料範囲内は200・範囲外は402",
              all(i["status"] == (200 if i["id"] in ph_free else 402) for i in spy.items), str(spy.items))

        # ---- B2 残高あり(同じ利用者に100ptを付ける)
        uid = set_balance(data_dir, email, 100.0)
        p.goto(base + "/", wait_until="networkidle")
        check_toggles(pw, base, "残高あり", s, expect_chip=False)
        rows0, bal0 = ledger(data_dir, uid)
        toasts = run_quiz(s, spy, "クイズ開始 (10語)")
        rows1, bal1 = ledger(data_dir, uid)
        new = rows1[len(rows0):]
        tag = "[B2 残高あり 単語]"
        check(f"{tag} 範囲外の項目も200で鳴る(一覧・フラッシュカードと同じ)",
              bool(spy.items) and all(i["status"] == 200 for i in spy.items), str(spy.items))
        check(f"{tag} 範囲外の再生ごとに台帳へ tts_playback が少額(-0.5pt)で残る",
              bool(new) and all(r[1] == "tts_playback" and abs(r[0] + 0.5) < 1e-6 for r in new), str(new))
        distinct = {(i["id"], i["kind"]) for i in spy.items if i["id"] not in w_free}
        check(f"{tag} 同じ項目の聞き直しは5分以内なら再課金しない(台帳の件数=範囲外の延べ項目数)",
              len(new) == len(distinct), f"ledger={len(new)} distinct={len(distinct)} items={spy.items}")
        check(f"{tag} 残高の減りと台帳が一致する", abs((bal0 - bal1) - 0.5 * len(new)) < 1e-6, f"{bal0}->{bal1} rows={len(new)}")
        check(f"{tag} POST /api/learn/tts は呼ばない", not spy.raw_tts, str(spy.raw_tts))
    finally:
        s.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", action="store_true")
    ap.add_argument("--prepare", action="store_true")
    ap.add_argument("--base", default="")
    ap.add_argument("--data-dir", default="")
    a = ap.parse_args()
    if a.prepare:
        prepare(a.data_dir)
        return 0
    if a.unit:
        if not os.environ.get("DATA_DIR"):
            print("中止: DATA_DIR(隔離ディレクトリ)が必要です")
            return 2
        unit()
    else:
        if not a.data_dir or urlparse(a.base).hostname not in ("127.0.0.1", "localhost"):
            print("中止: --data-dir と 127.0.0.1/localhost の隔離サーバー(--base)が必要です(本番には向けない)")
            return 2
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            check_browser(pw, a.base, a.data_dir)
    ng = [r for r in RESULTS if not r[0]]
    print(f"\n合計 {len(RESULTS)} 項目 / NG {len(ng)}")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
