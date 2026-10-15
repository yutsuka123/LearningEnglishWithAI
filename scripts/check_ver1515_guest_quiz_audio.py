"""ver1.5.15(ゲストのクイズの音声)の動作確認スクリプト(2026-10-15)。**隔離サーバー専用・本番には絶対に向けない**。

背景: 10/14に検索広告から来た訪問者(後に登録)が、ゲストのままクイズを始めた1秒後に音声の再生を拒否(401・要ログイン)され、
3秒でクイズを離れた。原因=クイズ画面だけが「任意テキストの合成(`POST /api/learn/tts`・設計上ログイン必須)」を呼んでいた。
一覧・フラッシュカードは「項目ID指定(`GET /api/learn/tts/item`・無料範囲ならゲストも可)」を使っている。

確かめること:
  A. ゲストの単語/フレーズのクイズ: 出題が無料範囲(ゲストは単語1,000・フレーズ750)だけになる(`free_range_only=true`)。
     音声は`/api/learn/tts/item`(ash/novaのどちらか1つ・語/例文)で、`POST /api/learn/tts`は呼ばない。応答は全て200。
     「要ログイン」の拒否トーストは出ない
  B. 範囲を絞らないと範囲外が混ざる(絞る意味がある)ことの確認(ゲストの`/api/words/quiz`を範囲指定なしで20回)
  C. 任意テキストの合成(`POST /api/learn/tts`)はゲストには従来どおり401のまま(門番は変えていない)
  B2. ゲストの出題は毎回同じ10件に固定されない(進捗が保存されないゲストは全語が同点=表の先頭N件になっていた。同点をランダムに)。
     ログイン済みの出題は従来どおり(同点は表の順=2回続けて同じ並び)
  D. ログイン済みユーザーのクイズは従来どおり(`POST /api/learn/tts`を呼ぶ・`/tts/item`は呼ばない・出題の範囲は絞らない)

使い方(.envの無いツリーで隔離サーバー。単語を1,300・フレーズを900まで増やし、全ての音声を偽の無音MP3で用意する):
  S=/tmp/quiz1515_data
  .venv/bin/python scripts/check_ver1515_guest_quiz_audio.py --prepare --data-dir $S   # 先にDBを作る(下の起動で作られた後に実行)
  ALLOW_FRESH_DB=1 MULTIUSER=1 SESSION_SECRET=preview OPENAI_API_KEY=preview-not-used \\
    DATA_DIR=$S .venv/bin/python -m uvicorn app.main:app --port 8795
  .venv/bin/python scripts/check_ver1515_guest_quiz_audio.py --prepare --data-dir $S   # 起動して空DBができてから(再実行しても安全)
  .venv/bin/python scripts/check_ver1515_guest_quiz_audio.py --base http://127.0.0.1:8795 --data-dir $S
Googleタグが入ったページを動かすため、check_signup_form.pyのSessionと同じ遮断をかける。テスト用の登録メールは
`claude-verify-`接頭辞(@example.test)。
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_signup_form import RESULTS, Session, check, signup_and_login  # noqa: E402

GUEST_WORDS = 1000
GUEST_PHRASES = 750
VOICES = ("ash", "nova")


def _silent_mp3() -> bytes:
    """ffmpegで作った短い無音MP3(無ければMPEGフレームを並べた最小のもの)。"""
    try:
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "s.mp3"
            subprocess.run(["ffmpeg", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=22050:cl=mono",
                            "-t", "0.3", "-q:a", "9", str(out)], check=True)
            return out.read_bytes()
    except Exception:
        return bytes.fromhex("fffb9064") + b"\x00" * 413


def prepare(data_dir: str) -> None:
    root = Path(data_dir)
    con = sqlite3.connect(root / "content.db")
    n_words = con.execute("SELECT COUNT(*) FROM words").fetchone()[0]
    if n_words < 1300:
        src = con.execute("SELECT english, japanese, part_of_speech, example FROM words ORDER BY id LIMIT 60").fetchall()
        for i in range(n_words + 1, 1301):
            e, j, pos, ex = src[i % len(src)]
            con.execute("INSERT INTO words (english, japanese, part_of_speech, example) VALUES (?,?,?,?)",
                        (f"{e}{i}", j, pos, ex))
    n_ph = con.execute("SELECT COUNT(*) FROM phrases").fetchone()[0]
    if n_ph < 900:
        src = con.execute("SELECT english, japanese, scene FROM phrases ORDER BY id LIMIT 40").fetchall()
        for i in range(n_ph + 1, 901):
            e, j, sc = src[i % len(src)]
            con.execute("INSERT INTO phrases (english, japanese, scene) VALUES (?,?,?)", (f"{e} {i}", j, sc))
    # 本番に近づける: クイズは「期限切れ→習熟度の低い順→表の並び」で選ぶため、進捗の無いゲストは先頭の語(小さいID)が
    # 毎回出る。本番(10/15確認)ではその10語(id 17〜26・level 500〜650)が全て無料範囲外だった。ここでも先頭10件を
    # 高いレベル(=範囲外)にし、それ以外はレベル昇順の範囲(単語1,000・フレーズ750)に収まる/はみ出す形にする。
    con.execute("UPDATE words SET level = CASE WHEN id <= 10 THEN '990' WHEN id <= 1000 THEN '500' ELSE '800' END")
    con.execute("UPDATE phrases SET level = CASE WHEN id <= 10 THEN '990' WHEN id <= 800 THEN '500' ELSE '800' END")
    con.commit()
    audio = root / "audio"
    audio.mkdir(parents=True, exist_ok=True)
    mp3 = _silent_mp3()

    def h(t: str) -> str:
        return hashlib.sha256(t.encode("utf-8")).hexdigest()[:10]

    n = 0
    for vid, en, ex in con.execute("SELECT id, english, example FROM words"):
        for v in VOICES:
            (audio / f"word{vid}_word_{v}_{h(en.strip())}.mp3").write_bytes(mp3)
            if (ex or "").strip():
                (audio / f"word{vid}_example_{v}_{h(ex.strip())}.mp3").write_bytes(mp3)
                n += 1
            n += 1
    for pid, en in con.execute("SELECT id, english FROM phrases"):
        for v in VOICES:
            (audio / f"phrase{pid}_phrase_{v}_{h(en.strip())}.mp3").write_bytes(mp3)
            n += 1
    con.close()
    print(f"prepared: words={1300} phrases={900} audio_files={n}")


LEVEL_ORDER = ["300-", "300", "350", "400", "450", "500", "550", "600", "650",
               "700", "750", "800", "850", "900", "950", "990", "990+"]


def guest_range(data_dir: str, table: str, limit: int) -> set[int]:
    """ゲストの無料範囲を、サーバーのコードを使わずにDBのlevelから独立に計算する(レベル昇順→id昇順の先頭limit件)。"""
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
    """ページの通信を記録する(クイズ出題API・音声API)。"""

    def __init__(self, page):
        self.quiz_urls: list[str] = []
        self.quiz_ids: list[int] = []
        self.raw_tts: list[str] = []
        self.items: list[dict] = []
        page.on("request", self._req)
        page.on("response", self._resp)

    def _req(self, r):
        u = urlparse(r.url)
        if u.path == "/api/learn/tts" and r.method == "POST":
            self.raw_tts.append(r.url)
        if u.path in ("/api/words/quiz", "/api/phrases/quiz"):
            self.quiz_urls.append(r.url)

    def _resp(self, r):
        u = urlparse(r.url)
        if u.path == "/api/learn/tts/item":
            q = parse_qs(u.query)
            self.items.append({"type": q.get("item_type", [""])[0], "id": int(q.get("item_id", ["0"])[0]),
                               "kind": q.get("kind", [""])[0], "voice": q.get("voice", [""])[0],
                               "status": r.status})
        if u.path in ("/api/words/quiz", "/api/phrases/quiz") and r.status == 200:
            try:
                data = r.json()
                self.quiz_ids += [int(x["id"]) for x in (data if isinstance(data, list) else data.get("items", []))]
            except Exception:
                pass

    def reset(self):
        self.quiz_urls.clear(); self.quiz_ids.clear(); self.raw_tts.clear(); self.items.clear()


def toast_text(p) -> str:
    return p.evaluate("(() => { const e = document.getElementById('toast');"
                      " return e && e.classList.contains('show') ? e.textContent : ''; })()") or ""


def run_quiz(s: Session, spy: Spy, start_label: str, kind: str):
    """クイズを2問進める: 開始→「英語を聞く」→「わからない」(答え表示で自動再生)→「例文を聞く」→⭕→2問目→「英語を聞く」。
    表示されたトーストは全てMutationObserverで記録する(サンプリングではない)。"""
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
    p.click("button:has-text('⭕')")          # 次の問題へ(2問目)
    p.wait_for_selector("#hear", timeout=10000)
    p.wait_for_timeout(1200)
    p.click("#hear")
    p.wait_for_timeout(800)
    return list(p.evaluate("window.__toasts") or [])


def check_guest(pw, base: str, data_dir: str):
    for kind, label, limit in (("word", "クイズ開始 (10語)", GUEST_WORDS),
                               ("phrase", "クイズ開始 (10フレーズ)", GUEST_PHRASES)):
        in_range = guest_range(data_dir, "words" if kind == "word" else "phrases", limit)
        s = Session(pw, base, "chromium", dict(pw.devices["Pixel 5"]))
        try:
            spy = Spy(s.page)
            toasts = run_quiz(s, spy, label, kind)
            tag = f"[guest {kind}]"
            check(f"{tag} 出題の取得に free_range_only=true が付く(無料範囲だけから出題)",
                  bool(spy.quiz_urls) and all("free_range_only=true" in u for u in spy.quiz_urls), str(spy.quiz_urls))
            check(f"{tag} 出題されたID全てが無料範囲内(DBのlevelから独立に計算・範囲外の先頭10件は出ない)",
                  bool(spy.quiz_ids) and set(spy.quiz_ids) <= in_range and not (set(spy.quiz_ids) & set(range(1, 11))),
                  f"out={sorted(set(spy.quiz_ids) - in_range)[:10]} n={len(spy.quiz_ids)}")
            check(f"{tag} 任意テキストの合成 POST /api/learn/tts を呼ばない", not spy.raw_tts, str(spy.raw_tts))
            check(f"{tag} 項目ID指定の音声 /api/learn/tts/item が呼ばれる(2問分の「英語を聞く」+答え表示で3回以上)",
                  len(spy.items) >= 3, str(spy.items))
            check(f"{tag} 音声の種別が項目の種類と合っている",
                  all(i["type"] == kind for i in spy.items), str(spy.items))
            check(f"{tag} 声はash/novaのどちらか1つだけ(事前作成済みの声)",
                  len({i["voice"] for i in spy.items}) == 1 and spy.items[0]["voice"] in VOICES, str(spy.items))
            check(f"{tag} 音声の応答は全て200(無料範囲なので拒否されない)",
                  all(i["status"] == 200 for i in spy.items), str(spy.items))
            check(f"{tag} 再生する項目のIDも無料範囲内(範囲外の先頭10件ではない)",
                  all(i["id"] in in_range for i in spy.items), str(spy.items))
            if kind == "word":
                check(f"{tag} 「例文を聞く」は項目の例文(kind=example)で再生される",
                      any(i["kind"] == "example" for i in spy.items), str(spy.items))
            bad = [t for t in toasts if re.search(r"要ログイン|Sign-in required|需要登", t) or t.lstrip().startswith("{")]
            check(f"{tag} 「要ログイン」や生のJSONのトーストが一度も出ない(全トーストを記録)", not bad, f"toasts={toasts}")
        finally:
            s.close()


def quiz_ids(page, base: str, path: str) -> list[int]:
    data = page.request.get(base + path).json()
    return [int(x["id"]) for x in (data if isinstance(data, list) else data.get("items", []))]


def check_range_matters(pw, base: str, data_dir: str):
    s = Session(pw, base, "chromium", dict(pw.devices["Pixel 5"]))
    try:
        s.page.goto(base + "/?tab=quiz", wait_until="networkidle")
        w_range = guest_range(data_dir, "words", GUEST_WORDS)
        ph_range = guest_range(data_dir, "phrases", GUEST_PHRASES)
        # 範囲を絞らない出題は、進捗の無いゲストでは範囲外の語(先頭10件)になる(本番の10/15確認と同じ)
        plain = [i for _ in range(10) for i in quiz_ids(s.page, base, "/api/words/quiz?limit=10")]
        check("[range] 範囲を絞らない出題は、進捗の無いゲストでは範囲外の語になる(本番の10/15確認と同じ・絞る意味がある)",
              any(i not in w_range for i in plain), f"outside={sum(i not in w_range for i in plain)}/{len(plain)}")
        for kind, api, rng in (("単語", "words", w_range), ("フレーズ", "phrases", ph_range)):
            sets = [tuple(sorted(quiz_ids(s.page, base, f"/api/{api}/quiz?limit=10&free_range_only=true"))) for _ in range(15)]
            allids = {i for t in sets for i in t}
            check(f"[range] {kind}: free_range_only=true の出題(15回×10)は全て無料範囲内(DBのlevelから独立に計算)",
                  allids <= rng, f"out={sorted(allids - rng)[:10]}")
            check(f"[variety] {kind}: ゲストの出題が毎回同じ10件に固定されない(15回で3種類以上の組・延べ30件以上の異なる項目)",
                  len(set(sets)) >= 3 and len(allids) >= 30, f"distinct_sets={len(set(sets))} distinct_ids={len(allids)}")
            check(f"[variety] {kind}: 1回の出題に重複が無く、ちょうど10件", all(len(set(t)) == 10 for t in sets), str(sets[:2]))
        r = s.page.request.post(base + "/api/learn/tts", data={"text": "hello", "voice": "ash"})
        check("[gate] ゲストの任意テキスト合成 POST /api/learn/tts は従来どおり401(門番は変えていない)", r.status == 401, str(r.status))
        r = s.page.request.get(base + f"/api/learn/tts/item?item_type=word&item_id={GUEST_WORDS + 50}&voice=ash&kind=word")
        check("[gate] ゲストの範囲外の項目音声は拒否される(402等・無料範囲の課金方針は変えていない)",
              r.status in (401, 402, 403), f"{r.status} {r.text()[:60]}")
    finally:
        s.close()


def check_logged_in(pw, base: str):
    s = Session(pw, base, "chromium", dict(pw.devices["Pixel 5"]))
    try:
        signup_and_login(s, "quiz-user", "quiz1515")
        spy = Spy(s.page)
        p = s.page
        p.goto(base + "/?tab=quiz", wait_until="networkidle")
        p.wait_for_timeout(1000)
        spy.reset()
        p.click("text=クイズ開始 (10語)")
        p.wait_for_selector("#hear", timeout=10000)
        p.wait_for_timeout(500)
        p.click("#hear")
        p.wait_for_timeout(800)
        check("[user] ログイン済みのクイズは従来どおり POST /api/learn/tts を呼ぶ(挙動を変えていない)",
              len(spy.raw_tts) >= 1, str(spy.raw_tts))
        check("[user] ログイン済みのクイズは /tts/item を呼ばない", not spy.items, str(spy.items))
        check("[user] ログイン済みの出題は範囲を絞らない(free_range_onlyが付かない)",
              bool(spy.quiz_urls) and all("free_range_only" not in u for u in spy.quiz_urls), str(spy.quiz_urls))
        for api in ("words", "phrases"):
            a = quiz_ids(p, base, f"/api/{api}/quiz?limit=10")
            b = quiz_ids(p, base, f"/api/{api}/quiz?limit=10")
            check(f"[user] ログイン済みの{api}の出題は従来どおり(同点は表の順=2回続けて同じ並び・乱数化していない)",
                  len(a) == 10 and a == b, f"{a} / {b}")
    finally:
        s.close()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="")
    ap.add_argument("--data-dir", default="")
    ap.add_argument("--prepare", action="store_true")
    a = ap.parse_args()
    if a.prepare:
        prepare(a.data_dir)
        return 0
    if not a.data_dir:
        print("中止: --data-dir(隔離サーバーのDATA_DIR・無料範囲の独立計算に使う)が必要です")
        return 2
    if urlparse(a.base).hostname not in ("127.0.0.1", "localhost"):
        print("中止: 127.0.0.1/localhost の隔離サーバーのみ(本番には向けない)")
        return 2
    with sync_playwright() as pw:
        print("== A. ゲストのクイズ(単語/フレーズ)")
        check_guest(pw, a.base, a.data_dir)
        print("== B/C. 出題範囲と門番")
        check_range_matters(pw, a.base, a.data_dir)
        print("== D. ログイン済みは従来どおり")
        check_logged_in(pw, a.base)
    ng = [r for r in RESULTS if not r[0]]
    print(f"\n合計 {len(RESULTS)} 項目 / NG {len(ng)}")
    return 1 if ng else 0


if __name__ == "__main__":
    sys.exit(main())
