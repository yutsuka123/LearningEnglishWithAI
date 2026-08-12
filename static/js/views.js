// All screen renderers. Each export takes the container element.

import { api } from "./api.js";
import * as speech from "./speech.js";
import { quizRunner } from "./quiz.js";
import {
  el, md, escapeHtml, toast, state, go, refreshCost, refreshAiState,
  showBanned, setShowBanned, testBanned, setTestBanned, onLeaveView,
} from "./app.js";

// 禁止用語クエリ: include_banned を付ける/付けないを返す小ヘルパー。
const bannedParam = (on) => (on ? "include_banned=true" : "");

// --- shared answer-input helper (voice or text) ----------------------------

function answerInput(onSubmit, { lang = "en-US", placeholder = "答えを入力" } = {}) {
  const wrap = el(`<div class="mt"></div>`);
  const ta = el(`<textarea placeholder="${placeholder}"></textarea>`);
  const row = el(`<div class="row"></div>`);
  const sendBtn = el(`<button class="btn">✓ 送信</button>`);
  sendBtn.addEventListener("click", () => onSubmit(ta.value));

  if (state.inputMode === "voice") {
    // Toggle: ON=録音開始, OFF=認識して回答(送信)。テキストは確認用に残る。
    let recorder = null;
    let recording = false;
    const mic = el(`<button class="btn good">🎤 録音開始</button>`);
    mic.addEventListener("click", async () => {
      if (!recording) {
        try {
          recorder = speech.createRecorder(lang);
          recorder.start();
          recording = true;
          mic.textContent = "⏹ 停止して回答";
          mic.classList.remove("good"); mic.classList.add("bad");
        } catch (e) { toast(e.message); }
      } else {
        recording = false;
        mic.disabled = true; mic.textContent = "認識中…";
        const said = await recorder.stop();
        ta.value = said;
        mic.disabled = false; mic.textContent = "🎤 録音開始";
        mic.classList.remove("bad"); mic.classList.add("good");
        if (said.trim() && speech.isVoiceAutoSubmit()) onSubmit(said);
      }
    });
    row.append(mic, sendBtn);
    wrap.append(ta, row);
  } else {
    row.append(sendBtn);
    wrap.append(ta, row);
  }
  return wrap;
}

function aiBadgeNote() {
  return state.aiEnabled ? ""
    : `<p class="muted">⚠️ AI未設定のため、この機能は設定でAPIキーを登録すると使えます。</p>`;
}

// Keep mostly-English lines (skip Japanese-only lines & markdown headers) so
// read-aloud sounds natural. Falls back to the whole text if nothing matches.
function englishOnly(text) {
  const lines = (text || "").split("\n")
    .map((l) => l.replace(/^[#>*\-\d.]+\s*/, "").trim())
    .filter((l) => l);
  const en = lines.filter((l) => {
    const ascii = (l.match(/[A-Za-z]/g) || []).length;
    const jp = (l.match(/[぀-ヿ一-鿿]/g) || []).length;
    return ascii >= 8 && ascii > jp;
  });
  return (en.length ? en.join(" ") : text).slice(0, 3500);
}

// 読み上げ速度の共通コントロール（playbackRate を全再生に適用・音程不変）。
// 一度設定すると localStorage に保存され、会話など他の読み上げにも効く。
function playbackSpeedControl() {
  const sel = el(`<select title="読み上げ速度">
    <option value="1">速度: 標準</option>
    <option value="0.8">速度: ゆっくり</option>
    <option value="1.2">速度: 速い(native寄り)</option></select>`);
  sel.value = String(speech.getPlaybackRate());
  sel.addEventListener("change", () =>
    speech.setPlaybackRate(parseFloat(sel.value) || 1));
  return sel;
}

// A reusable 🔊読み上げ / ⏹停止 control bar for generated material.
function readAloudBar(getText, feature) {
  const bar = el(`<div class="row mt"></div>`);
  const play = el(`<button class="btn ghost">🔊 英文を読み上げ</button>`);
  const stop = el(`<button class="btn ghost">⏹ 停止</button>`);
  play.addEventListener("click",
    () => speech.speak(englishOnly(getText()), { feature }));
  stop.addEventListener("click", () => speech.stopSpeaking());
  bar.append(play, stop, playbackSpeedControl());
  return bar;
}

// --- Dashboard --------------------------------------------------------------

export async function dashboard(root) {
  const p = await api.get("/api/system/progress");
  let mu = null;
  try { mu = await api.get("/api/system/my-usage"); } catch (_) { /* */ }
  let deckSummary = null, phraseDeckSummary = null;
  let myWordDecks = [], myPhraseDecks = [];
  try {
    [deckSummary, phraseDeckSummary, myWordDecks, myPhraseDecks] =
      await Promise.all([
        api.get("/api/decks/summary"), api.get("/api/phrase-decks/summary"),
        api.get("/api/decks"), api.get("/api/phrase-decks"),
      ]);
  } catch (_) { /* 未ログイン等で失敗しても致命的ではない */ }
  const isAdmin = mu && mu.role === "admin";
  const toeic = (p.toeic_estimate == null) ? "未判定" : p.toeic_estimate;
  // 一般ユーザーには費用額を見せない（管理者のみ）。残高があれば残高を表示。
  let costNum = "—", costLbl = "今日のAI費用";
  if (isAdmin && mu) { costNum = "¥" + mu.today_jpy; }
  else if (mu && mu.balance_jpy != null) {
    costNum = "¥" + Math.round(mu.balance_jpy); costLbl = "チャージ残高";
  }
  const w = p.words;
  const areaLabels = {
    conversation: "英会話", reading: "リーディング", writing: "ライティング",
    literature: "文学", listening: "リスニング",
  };
  const areaCards = Object.entries(p.areas).map(([k, v]) => `
    <div class="card">
      <div class="row" style="justify-content:space-between">
        <b>${areaLabels[k] || k}</b>
        <span class="muted">${v.avg_mastery} / 100</span></div>
      <div class="bar mt"><span style="width:${Math.min(100, v.avg_mastery)}%">
        </span></div>
    </div>`).join("");
  // 2026-08-09: 単語帳/フレーズ帳の達成率はドリルダウンせず、デッキ別に
  // ダッシュボード最上位でフラット表示する（ユーザー要望）。
  const deckRow = (d, icon) => {
    const pct = d.total ? Math.round(d.mastered / d.total * 100) : 0;
    return `<div class="mt">
      <div class="row" style="justify-content:space-between">
        <span class="muted">${icon} ${escapeHtml(d.name)}
          (${d.mastered}/${d.total})</span>
        <b>${pct}%</b>
      </div>
      <div class="bar mt"><span style="width:${pct}%"></span></div>
    </div>`;
  };

  root.innerHTML = `
    <h1>ダッシュボード</h1>
    <p class="sub">今日の学習を始めましょう。1回 約10分でOK。</p>

    <div class="grid cols-3">
      <div class="card stat">
        <div class="num">${toeic}</div>
        <div class="lbl">TOEIC換算(目安)</div></div>
      <div class="card stat">
        <div class="num">${p.overall_avg_mastery}</div>
        <div class="lbl">平均習熟度(単語+フレーズ)</div></div>
      <div class="card stat">
        <div class="num">${costNum}</div>
        <div class="lbl">${costLbl}</div></div>
    </div>

    <div class="card">
      <h2>単語の状況</h2>
      <div class="grid cols-3">
        <div class="stat"><div class="num">${w.total}</div>
          <div class="lbl">全件数</div></div>
        <div class="stat"><div class="num">${w.studied}</div>
          <div class="lbl">学習数(出題済み)</div></div>
        <div class="stat"><div class="num">${w.mastered}</div>
          <div class="lbl">習得数(100+)</div></div>
        <div class="stat"><div class="num">${w.vague}</div>
          <div class="lbl">うろ覚え(40-79)</div></div>
        <div class="stat"><div class="num">${w.avg_mastery}</div>
          <div class="lbl">平均習熟度</div></div>
        <div class="stat"><div class="num">${p.phrases.total}</div>
          <div class="lbl">フレーズ全件</div></div>
      </div>
      <p class="muted mt">※全件数は単語を追加すると増えます。TOEIC換算は学習データに
        基づく目安です。</p>
    </div>

    <div class="card">
      <h2>クイックスタート</h2>
      <div class="row">
        <button class="btn secondary" id="goConv">🗣️ 英会話する</button>
      </div>
    </div>

    ${(deckSummary || phraseDeckSummary) ? `<div class="card">
      <h2>単語帳の状況</h2>
      <div class="row" style="justify-content:space-between">
        <span class="muted">単語帳 全体(${deckSummary ? deckSummary.deck_count : 0}個・
          ${deckSummary ? deckSummary.mastered : 0}/${deckSummary ? deckSummary.total : 0}語)</span>
        <b>${deckSummary ? deckSummary.pct : 0}%</b>
      </div>
      <div class="bar mt"><span style="width:${deckSummary ? deckSummary.pct : 0}%"></span></div>
      ${myWordDecks.map((d) => deckRow(d, "📘")).join("")}
      <div class="row mt">
        <button class="btn ghost" id="goDeck">単語帳を作成・編集</button>
      </div>
    </div>
    <div class="card">
      <h2>フレーズ帳の状況</h2>
      <div class="row" style="justify-content:space-between">
        <span class="muted">フレーズ帳 全体(${phraseDeckSummary ? phraseDeckSummary.deck_count : 0}個・
          ${phraseDeckSummary ? phraseDeckSummary.mastered : 0}/${phraseDeckSummary ? phraseDeckSummary.total : 0}件)</span>
        <b>${phraseDeckSummary ? phraseDeckSummary.pct : 0}%</b>
      </div>
      <div class="bar mt"><span style="width:${phraseDeckSummary ? phraseDeckSummary.pct : 0}%"></span></div>
      ${myPhraseDecks.map((d) => deckRow(d, "🗂️")).join("")}
      <div class="row mt">
        <button class="btn ghost" id="goPhraseDeck">フレーズ帳を作成・編集</button>
      </div>
    </div>` : ""}

    <h2>項目別の習熟度</h2>
    <div class="grid cols-2">${areaCards}</div>`;
  root.querySelector("#goConv").addEventListener("click",
    () => go("conversation"));
  root.querySelector("#goDeck")?.addEventListener("click", () => go("deck"));
  root.querySelector("#goPhraseDeck")?.addEventListener("click",
    () => go("phrasedeck"));
}

// --- Daily 10-minute session ------------------------------------------------

export async function daily(root) {
  const q = testBanned() ? "?include_banned=true" : "";
  const data = await api.get("/api/learn/daily" + q);
  const steps = data.plan;
  let current = 0;

  function chips() {
    return `<div class="steps">${steps.map((s, i) =>
      `<span class="step-chip ${i === current ? "active" : i < current
        ? "done" : ""}">${i + 1}. ${s.label}</span>`).join("")}</div>`;
  }

  function next() { current++; render(); }

  function render() {
    if (current >= steps.length) {
      root.innerHTML = `${chips()}
        <div class="card center">
          <h2>デイリー完了！🎉</h2>
          <p class="muted">学習履歴に記録を残せます。</p>
          <button class="btn" id="toHist">学習履歴へ</button>
        </div>`;
      root.querySelector("#toHist").addEventListener("click", () => go("history"));
      refreshCost();
      return;
    }
    const step = steps[current];
    root.innerHTML = `<h1>デイリーセッション</h1>${chips()}
      <div id="stepArea"></div>`;
    const area = root.querySelector("#stepArea");

    if (step.step === "vocab" || step.step === "phrases") {
      if (!step.items.length) {
        area.innerHTML = `<div class="card">項目がありません。</div>`;
        area.appendChild(el(`<button class="btn" id="sk">次へ</button>`));
        area.querySelector("#sk").addEventListener("click", next);
        return;
      }
      const holder = el(`<div></div>`);
      area.appendChild(holder);
      quizRunner({
        container: holder, items: step.items,
        kind: step.step === "vocab" ? "word" : "phrase",
        appState: state,
        onDone: () => {
          const b = el(`<button class="btn mt" id="cont">次のステップへ</button>`);
          holder.appendChild(b);
          b.addEventListener("click", next);
        },
      });
    } else if (step.step === "reading") {
      readingStep(area, next);
    } else {
      writingStep(area, next);
    }
  }

  // 開いた直後は発声しない。開始ボタンを押してから render() を始める。
  // （以降は単語表示と同時に読み上げてOK、というご要望どおりの挙動。）
  function intro() {
    root.innerHTML = `<h1>デイリーセッション</h1>${chips()}
      <div class="card center">
        <h2>今日の学習（約10分）</h2>
        <p class="muted">単語・フレーズ・読み書きを順番に進めます。
          音声は開始後に再生されます。</p>
        <button class="btn" id="startDaily">▶ 開始する</button>
      </div>`;
    root.querySelector("#startDaily")
      .addEventListener("click", () => render());
  }
  intro();
}

async function readingStep(area, next) {
  area.innerHTML = `<div class="card"><h2>リーディング (1題)</h2>
    ${aiBadgeNote()}
    <div class="row">
      <button class="btn" id="gen" ${state.aiEnabled ? "" : "disabled"}>
        教材を生成</button>
      <button class="btn secondary" id="skip">スキップ</button>
    </div>
    <div id="out" class="md mt"></div></div>`;
  area.querySelector("#skip").addEventListener("click", next);
  area.querySelector("#gen").addEventListener("click", async () => {
    const out = area.querySelector("#out");
    out.textContent = "生成中…";
    const r = await api.post("/api/learn/generate",
      { area: "reading", field: "一般", instruction: "短めの長文1題" });
    if (!r.ok) { out.textContent = r.error; return; }
    out.innerHTML = md(r.body);
    out.appendChild(el(`<button class="btn ghost mt" id="say">🔊 読み上げ</button>`));
    out.querySelector("#say").addEventListener("click",
      () => speech.speak(r.body, { feature: "reading_tts" }));
    out.appendChild(el(`<button class="btn mt" id="done">次へ</button>`));
    out.querySelector("#done").addEventListener("click", next);
    refreshCost();
  });
}

async function writingStep(area, next) {
  area.innerHTML = `<div class="card"><h2>ライティング (1題・音声応答可)</h2>
    ${aiBadgeNote()}
    <p class="muted">お題: 今日あったことを3文で英語で書いて(話して)みましょう。</p>
    <div id="ans"></div><div id="fb" class="md mt"></div>
    <button class="btn secondary mt" id="skip">スキップ</button></div>`;
  area.querySelector("#skip").addEventListener("click", next);
  const ansBox = area.querySelector("#ans");
  ansBox.appendChild(answerInput(async (txt) => {
    const fb = area.querySelector("#fb");
    if (!txt.trim()) { toast("文章が空です"); return; }
    if (!state.aiEnabled) {
      fb.innerHTML = md("AI未設定のため添削は省略。よく書けました！");
      const nb = el(`<button class="btn mt">次へ</button>`);
      nb.addEventListener("click", next); fb.appendChild(nb);
      return;
    }
    fb.textContent = "添削中…";
    const r = await api.post("/api/learn/writing-feedback",
      { category: "日常", prompt: "今日あったこと", text: txt });
    fb.innerHTML = r.ok ? md(r.feedback) : escapeHtml(r.error);
    fb.appendChild(el(`<button class="btn mt" id="done">次へ</button>`));
    fb.querySelector("#done").addEventListener("click", next);
    refreshCost();
  }, { lang: "en-US", placeholder: "英語で入力" }));
}

// --- Vocabulary -------------------------------------------------------------

// 男声=ash(青) / 女声=nova(赤)。一覧の2つの再生ボタンに対応。
const MALE_VOICE = "ash";
const FEMALE_VOICE = "nova";

// 2つの再生ボタン(男声=青 / 女声=赤)を作って返す。getText() は再生する英文。
function voiceButtons(getText) {
  const cell = el(`<div class="voice-cell">
    <button class="btn voice-m" title="男性の声 (ash)">🔊</button>
    <button class="btn voice-f" title="女性の声 (nova)">🔊</button></div>`);
  const [m, f] = cell.querySelectorAll("button");
  m.addEventListener("click", () => speech.sayWithVoice(getText(), MALE_VOICE));
  f.addEventListener("click", () => speech.sayWithVoice(getText(), FEMALE_VOICE));
  return cell;
}

// 教材の長さ（5段階）。1=短め(1〜2文) … 5=長文(約2分)。
const LENGTH_INSTR = {
  "1": "ごく短く1〜2文（約20語）で",
  "2": "短め（約50語）で",
  "3": "標準的な長さ（約100語）で",
  "4": "やや長め（約180語）で",
  "5": "長文（約300語・朗読で約2分）で",
};
function lengthSelect(id) {
  return `<select id="${id}" title="長さ(5段階)">
    <option value="1">長さ: 短め(1〜2文)</option>
    <option value="2">長さ: やや短め</option>
    <option value="3" selected>長さ: 標準</option>
    <option value="4">長さ: やや長め</option>
    <option value="5">長さ: 長文(約2分)</option></select>`;
}

// 生成時の難易度セレクト（おまかせ＝学習者プロフィール）。
function diffSelect(id) {
  return `<select id="${id}" title="難易度">
    <option value="">難易度: おまかせ</option>
    <option value="入門(TOEIC 300-400)">難易度: 入門</option>
    <option value="初級(TOEIC 500)">難易度: 初級</option>
    <option value="中級(TOEIC 600)">難易度: 中級</option>
    <option value="中上級(TOEIC 700)">難易度: 中上級</option>
    <option value="上級(TOEIC 800)">難易度: 上級</option>
    <option value="最上級(TOEIC 900+)">難易度: 最上級</option></select>`;
}

// 内容理解問題の見出し以降を取り除く（保存はフル、表示だけ問題を隠す用）。
function stripQuestions(body) {
  const m = (body || "").match(
    /^#{1,6}\s*.*(Comprehension|内容理解|理解問題|設問|Questions).*$/im);
  return (m && m.index != null)
    ? body.slice(0, m.index).trimEnd() : body;
}

// 速度モード → sayItem オプション。learn音声/native音声＋再生速度を決める。
//   slow=学習ゆっくり / std=学習標準 / native=ネイティブ音声(自然な速さ)
function speedOpts(mode) {
  if (mode === "native") return { speed: "native", rate: 1.0 };
  if (mode === "slow") return { speed: "learn", rate: 0.8 };
  return { speed: "learn", rate: 1.0 };
}

// 番号(ID)で再生する2ボタン。保存済みなら無料、無ければ合成して保存し
// 次回から無料。fallback はTTS不可時にブラウザ音声で読む英文。
// getMode() は 'slow'|'std'|'native' を返す（省略時 'std'）。
function voiceButtonsItem(itemType, id, kind, fallback, getMode) {
  const cell = el(`<div class="voice-cell">
    <button class="btn voice-m" title="男性の声 (ash)">🔊</button>
    <button class="btn voice-f" title="女性の声 (nova)">🔊</button></div>`);
  const [m, f] = cell.querySelectorAll("button");
  const play = (voice) => speech.sayItem(
    itemType, id, kind, voice, fallback(),
    speedOpts(getMode ? getMode() : "std"));
  m.addEventListener("click", () => play(MALE_VOICE));
  f.addEventListener("click", () => play(FEMALE_VOICE));
  return cell;
}

// --- ページネーション（1ページ50件 標準）---------------------------------

// 表示件数セレクト（20/50/100/500/全件、既定50）。value は数値 or 'all'。
function pageSizeSelect(id) {
  return `<select id="${id}" title="1ページの表示件数">
    <option value="20">20件/ページ</option>
    <option value="50" selected>50件/ページ</option>
    <option value="100">100件/ページ</option>
    <option value="500">500件/ページ</option>
    <option value="all">全件</option></select>`;
}

// list を page/size で切り出す。size='all' は全件。
function pageSlice(list, page, size) {
  if (size === "all") return { slice: list, page: 0, pages: 1 };
  const n = parseInt(size, 10) || 50;
  const pages = Math.max(1, Math.ceil(list.length / n));
  const p = Math.min(Math.max(0, page), pages - 1);
  return { slice: list.slice(p * n, p * n + n), page: p, pages };
}

// 前/次ページのバーを作る。
function pagerBar(total, page, pages, onPrev, onNext) {
  const bar = el(`<div class="row pager"></div>`);
  const prev = el(`<button class="btn ghost">← 前</button>`);
  const next = el(`<button class="btn ghost">次 →</button>`);
  const info = el(`<span class="muted">${pages > 1
    ? page + 1 + " / " + pages + " ページ ・ " : ""}全 ${total} 件</span>`);
  prev.disabled = page <= 0;
  next.disabled = page >= pages - 1;
  prev.addEventListener("click", onPrev);
  next.addEventListener("click", onNext);
  bar.append(prev, info, next);
  return bar;
}

// 速度セレクト（ゆっくり/標準/ネイティブ）。value は slow/std/native。
// withNative=false で「ネイティブ」を出さない（単語は native音声が無い）。
function speedSelect(id, withNative = true) {
  const nat = withNative
    ? `<option value="native">速度: ネイティブ</option>` : "";
  return `<select id="${id}" title="再生速度">
    <option value="std">速度: 標準(学習)</option>
    <option value="slow">速度: ゆっくり</option>${nat}</select>`;
}

// 習熟度バー: 色＋サイズで段階を表す（全長は従来の約半分）。
//   0       → 赤・極小
//   1〜20   → 黄、20で基準サイズ(=200と同じ)に達する
//   20超〜50 → 緑、基準サイズ
//   50超〜200 → 青、基準サイズ＋バーを太くしてサイズ感を変える
function masteryCell(item) {
  const m = item.mastery;
  let color, w, cls = "";
  if (m <= 0) { color = "#e5534b"; w = 8; }
  else if (m <= 20) { color = "#ffb454"; w = 8 + (m / 20) * 92; }
  else if (m <= 50) { color = "#36c98d"; w = 100; }
  else { color = "#3b82f6"; w = 100; cls = " blue"; }
  const badge = item.mastered
    ? `<span class="pill mastered">✅ 覚えた</span>` : "";
  return `<div class="mbar${cls}">
    <span style="width:${w}%;background:${color}"></span></div>
    <small class="muted">${m}</small> ${badge}`;
}

// 「覚えた / 戻す」トグルボタン。endpoint は /api/words or /api/phrases。
function knownButton(base, item, onChange) {
  const btn = el(`<button class="btn blue"></button>`);
  const paint = () => {
    btn.textContent = item.mastered ? "戻す" : "覚えた";
    btn.title = item.mastered
      ? "覚えた状態を解除（閾値直下に戻す）" : "覚えた（満点200・出題を抑制）";
  };
  paint();
  btn.addEventListener("click", async () => {
    const next = !item.mastered;
    try {
      const r = await api.post(`${base}/${item.id}/known`, { known: next });
      item.mastery = r.mastery;
      item.mastered = r.known;
      paint();
      if (onChange) onChange();
    } catch (e) { toast("更新に失敗しました"); }
  });
  return btn;
}

// 「うろ覚え」ボタン: 押すと mastery +10。base は /api/words or /api/phrases。
function vagueButton(base, item, onChange) {
  const btn = el(`<button class="btn vague-btn"
    title="うろ覚え（+10ポイント）">うろ覚え</button>`);
  btn.addEventListener("click", async () => {
    try {
      const r = await api.post(`${base}/${item.id}/vague`);
      item.mastery = r.mastery;
      item.mastered = item.mastery >= 100;
      if (onChange) onChange();
      toast("うろ覚え +10");
    } catch (e) { toast("更新に失敗しました"); }
  });
  return btn;
}

// 削除ボタン: ゴミ箱マーク＋二重確認。基本は削除させたくないので、押し間違い
// 防止に他のボタンから少し離し、確認を2段階にする。onDel() は実際の削除処理。
function deleteButton(name, onDel) {
  // ゴミ箱マークは赤（背景はそのまま）。絵文字は色を変えられないのでSVGを使う。
  const btn = el(`<button class="btn ghost del-btn"
    title="削除（確認を2回します）">
    <svg viewBox="0 0 24 24" width="15" height="15" fill="currentColor"
      aria-hidden="true"><path d="M9 3h6l1 2h4v2H4V5h4l1-2zM6 9h12l-1 11a2 2
      0 0 1-2 2H9a2 2 0 0 1-2-2L6 9z"/></svg></button>`);
  btn.addEventListener("click", async () => {
    const label = (name || "").slice(0, 40);
    if (!confirm(
      `「${label}」を削除しますか？\n` +
      "※基本的に削除は不要です。本当に消す場合のみ進めてください。")) return;
    if (!confirm(
      `最終確認です。「${label}」を完全に削除します。\n` +
      "この操作は元に戻せません。よろしいですか？")) return;
    try {
      await onDel();
      toast("削除しました");
    } catch (e) {
      toast(e.message || "削除に失敗しました");
    }
  });
  return btn;
}

// 簡易モーダル（例文ポップアップ等）。閉じるとDOMから消える。
function openModal(title, buildBody) {
  const ov = el(`<div class="modal-ov"></div>`);
  const box = el(`<div class="modal-box">
    <div class="row" style="justify-content:space-between">
      <h2 style="margin:0">${escapeHtml(title)}</h2>
      <button class="btn ghost" id="mClose">✕</button></div>
    <div class="modal-body mt"></div></div>`);
  const close = () => { speech.stopSpeaking(); ov.remove(); };
  ov.addEventListener("click", (e) => { if (e.target === ov) close(); });
  box.querySelector("#mClose").addEventListener("click", close);
  buildBody(box.querySelector(".modal-body"));
  ov.appendChild(box);
  document.body.appendChild(ov);
  return close;
}

// 詳細(JSON)を整形して描画。類義語/対義語/派生語のうちDB登録済みの語は、
// 描画後に linkifyJumps() でクリック可能化し、その語の詳細へジャンプできる。
function renderWordDetail(box, d, primaryEn) {
  box.innerHTML = "";
  const sec = (label, html) => {
    if (!html) return;
    box.appendChild(el(`<p style="margin:6px 0"><b>${label}</b> ${html}</p>`));
  };
  const arr = (a) => Array.isArray(a) ? a.map(escapeHtml).join("、") : "";
  // ジャンプ候補の語を span で包む（後で登録済みのみリンク化）。
  const jw = (word) => {
    const w = word || "";
    return `<span class="jw" data-w="${escapeHtml(w)}">${escapeHtml(w)}</span>`;
  };
  // 類義語/対義語: 文字列(旧形式) と {word,note}(新形式・ニュアンス併記)に対応。
  const wn = (a) => Array.isArray(a) ? a.map((x) => typeof x === "string"
    ? jw(x)
    : `${jw(x.word || "")}${x.note
      ? "（" + escapeHtml(x.note) + "）" : ""}`).join(" / ") : "";
  sec("発音:", d.pronunciation ? escapeHtml(d.pronunciation) : "");
  sec("品詞:", d.pos ? escapeHtml(d.pos) : "");
  sec("意味:", arr(d.meanings));
  // 例文(英文＋日本語訳)。訳は淡色で英文の下に。発声は不要なので再生ボタンなし。
  // 先頭の読み上げ例文(primaryEn)と同じ文は重複表示しない。
  if (Array.isArray(d.examples) && d.examples.length) {
    const norm = (s) => (s || "").trim().toLowerCase().replace(/\.+$/, "");
    const exs = primaryEn
      ? d.examples.filter((x) => norm(x.en) !== norm(primaryEn))
      : d.examples;
    if (exs.length) {
      const exHtml = exs.map((x) =>
        `${escapeHtml(x.en || "")}<br>`
        + `<span class="muted">${escapeHtml(x.ja || "")}</span>`)
        .join(`<br>`);
      sec("例文:", exHtml);
    }
  }
  if (Array.isArray(d.derivatives) && d.derivatives.length) {
    sec("派生:", d.derivatives.map((x) =>
      `${jw(x.word || "")}（${escapeHtml(x.pos || "")}: `
      + `${escapeHtml(x.ja || "")}）`).join(" / "));
  }
  sec("類義語:", wn(d.synonyms));
  sec("対義語:", wn(d.antonyms));
  sec("語源・由来:", d.origin ? escapeHtml(d.origin) : "");
  sec("豆知識:", d.trivia ? escapeHtml(d.trivia) : "");
  sec("解説:", d.explanation ? escapeHtml(d.explanation) : "");
  linkifyJumps(box);
}

// 詳細内の語(.jw)のうちDB登録済みのものをクリック可能にし、その語の詳細へ。
// 同綴りで複数の意味(word行)が登録されている場合は選択メニューを挟む
// （§B17・論点1-b、例: agentのIT用語/スパイ用語/代理人）。
async function linkifyJumps(box) {
  const spans = Array.from(box.querySelectorAll(".jw"));
  if (!spans.length) return;
  const words = Array.from(new Set(
    spans.map((s) => s.dataset.w).filter(Boolean)));
  try {
    const r = await api.post("/api/words/resolve", { words });
    const found = (r && r.found) || {};
    for (const s of spans) {
      const hits = found[(s.dataset.w || "").toLowerCase()];
      if (hits && hits.length) {
        s.classList.add("jw-link");
        if (hits.length === 1) {
          s.title = `「${hits[0].english}」の詳細へ`;
          s.addEventListener("click", () => showWordDetail(hits[0]));
        } else {
          s.title = `「${hits[0].english}」の詳細へ（${hits.length}件の意味）`;
          s.addEventListener("click", () => showWordChoices(hits));
        }
      }
    }
  } catch (_) { /* 解決失敗時はリンク化しないだけ（表示はそのまま） */ }
}

// 同綴りで複数の意味がある語の選択メニュー（分野で見分けてもらう）。
function showWordChoices(hits) {
  openModal(hits[0].english, (body) => {
    body.appendChild(el(
      `<p class="muted">同じ綴りで複数の意味があります。選んでください。</p>`));
    const list = el(
      `<div class="row" style="flex-direction:column;align-items:stretch;gap:6px"></div>`);
    hits.forEach((h) => {
      const btn = el(`<button class="btn ghost" style="text-align:left">
        ${escapeHtml(h.japanese || "")}
        <span class="muted">（${escapeHtml(h.domain || "分野未設定")}）</span>
      </button>`);
      btn.addEventListener("click", () => showWordDetail(h));
      list.appendChild(btn);
    });
    body.appendChild(list);
  });
}

// 単語の詳細ポップアップ: 例文(再生)＋AI詳細(品詞/意味複数/派生/類義/対義/
// 由来/豆知識/解説)。詳細は押した時にAI生成→キャッシュ（2回目以降は無料）。
function showWordDetail(w) {
  openModal(w.english, (body) => {
    body.appendChild(el(`<p class="quiz-answer">${escapeHtml(w.english)}
      <span class="muted">${escapeHtml(w.japanese || "")}
      ${w.level ? "・Lv" + w.level : ""}</span></p>`));
    const exLine = el(`<p style="margin-bottom:2px">${w.example
      ? "例文: " + escapeHtml(w.example) : "（例文なし）"}</p>`);
    body.appendChild(exLine);
    // 読み上げ例文の日本語訳（詳細の example_ja。読み込み後に埋める・発声なし）。
    const exJa = el(`<p class="muted" style="margin:0 0 4px"></p>`);
    if (w.example) body.appendChild(exJa);
    const speedRow = el(`<div class="row">${speedSelect("exSpeed")}</div>`);
    const getMode = () => body.querySelector("#exSpeed").value;
    // タブレット操作性: 速度セレクトの直下なので、発話ボタンを文字一行分
    // (約1.4em)下げて誤タップを防ぐ。
    const tools = el(`<div class="row" style="margin-top:1.4em"></div>`);
    if (w.example) {
      tools.appendChild(voiceButtonsItem(
        "word", w.id, "example", () => w.example, getMode));
    }
    body.append(speedRow, tools);

    // --- AI詳細 ---
    const detailBox = el(`<div class="mt"></div>`);
    body.appendChild(detailBox);
    // 詳細は事前生成方式（キャッシュ済みのみ表示）。AI生成/作り直しボタンは廃止。
    const loadDetail = async () => {
      detailBox.innerHTML = `<p class="muted">詳細を取得中…</p>`;
      try {
        const r = await api.post(`/api/words/${w.id}/detail`);
        if (r.ok) {
          renderWordDetail(detailBox, r.detail, w.example);
          if (w.example && r.detail && r.detail.example_ja) {
            exJa.textContent = "訳: " + r.detail.example_ja;
          }
          w.has_detail = true;
        } else {
          detailBox.innerHTML =
            `<p class="muted">${escapeHtml(r.error || "失敗")}</p>`;
        }
      } catch (e) {
        detailBox.innerHTML = `<p class="muted">失敗: ${e.message}</p>`;
      }
    };
    if (w.has_detail) {
      loadDetail();  // キャッシュ済み → 無料で表示
    } else {
      detailBox.appendChild(el(
        `<p class="muted">この単語の詳細は準備中です。</p>`));
    }

    // 同綴りで意味が異なる別エントリがあれば案内する（§B17・論点1-b）。
    (async () => {
      try {
        const r = await api.post(
          "/api/words/resolve", { words: [w.english] });
        const hits = (r && r.found && r.found[w.english.toLowerCase()])
          || [];
        const others = hits.filter((h) => h.id !== w.id);
        if (!others.length) return;
        const box2 = el(`<p class="muted mt">🔀 同じ綴りの別の意味: </p>`);
        others.forEach((h, i) => {
          if (i > 0) box2.appendChild(document.createTextNode(" / "));
          const link = el(`<span class="jw-link" style="cursor:pointer;
            text-decoration:underline">${escapeHtml(h.japanese || "")}
            （${escapeHtml(h.domain || "分野未設定")}）</span>`);
          link.addEventListener("click", () => showWordDetail(h));
          box2.appendChild(link);
        });
        body.appendChild(box2);
      } catch (_) { /* 取得失敗時は何も表示しない */ }
    })();
  });
}

// フレーズ詳細の中身を描画（ニュアンス/類似表現/由来・歴史的背景/注意点/
// 豆知識/解説）。格言・慣用句・誤解されやすい表現・マナー系は内容が
// 濃くなり、普通のフレーズは該当欄が空になる想定（サーバー側で調整済み）。
function renderPhraseDetail(box, d) {
  box.innerHTML = "";
  const sec = (label, html) => {
    if (!html) return;
    box.appendChild(el(`<p style="margin:6px 0"><b>${label}</b> ${html}</p>`));
  };
  sec("ニュアンス:", d.nuance ? escapeHtml(d.nuance) : "");
  if (Array.isArray(d.similar_expressions) && d.similar_expressions.length) {
    const html = d.similar_expressions.map((x) =>
      `${escapeHtml(x.en || "")}（${escapeHtml(x.ja || "")}）`
      + (x.diff ? ` — ${escapeHtml(x.diff)}` : "")).join("<br>");
    sec("類似表現:", html);
  }
  sec("由来・背景:", d.background ? escapeHtml(d.background) : "");
  sec("⚠️ 注意:", d.caution ? escapeHtml(d.caution) : "");
  sec("豆知識:", d.trivia ? escapeHtml(d.trivia) : "");
  sec("解説:", d.explanation ? escapeHtml(d.explanation) : "");
}

// フレーズの詳細ポップアップ（単語のshowWordDetailと同じ方式）。
function showPhraseDetail(p) {
  openModal(p.english, (body) => {
    body.appendChild(el(`<p class="quiz-answer">${escapeHtml(p.english)}
      <span class="muted">${escapeHtml(p.japanese || "")}
      ${p.scene ? "・" + escapeHtml(p.scene) : ""}</span></p>`));
    const detailBox = el(`<div class="mt"></div>`);
    body.appendChild(detailBox);
    const loadDetail = async () => {
      detailBox.innerHTML = `<p class="muted">詳細を取得中…</p>`;
      try {
        const r = await api.post(`/api/phrases/${p.id}/detail`);
        if (r.ok) {
          renderPhraseDetail(detailBox, r.detail);
          p.has_detail = true;
        } else {
          detailBox.innerHTML =
            `<p class="muted">${escapeHtml(r.error || "失敗")}</p>`;
        }
      } catch (e) {
        detailBox.innerHTML = `<p class="muted">失敗: ${e.message}</p>`;
      }
    };
    if (p.has_detail) {
      loadDetail();  // キャッシュ済み → 無料で表示
    } else {
      detailBox.appendChild(el(
        `<p class="muted">このフレーズの詳細は準備中です。</p>`));
    }
  });
}

// --- 🃏 フラッシュ単語 -------------------------------------------------------
// 英単語ページの「高速めくり」版。大きなカードをタップで答え表示、スワイプ
// (またはカード欄外のボタン)で採点してテンポよく次々めくる。
//   上=覚えた(満点200・出題から外す) / 下=できない(不正解・すぐ再出題) /
//   右=うろ覚え(+10) / 左=1つ戻る(採点やり直し=直前の習得度を復元)。
// 出題はポイントが低い語ほど高確率(比例)＋復習期限を優先(/api/words/quiz)。

// カードへスワイプ/タップ操作を付与。pointer events で touch/mouse 両対応。
function attachSwipe(elm, h) {
  const TH = 45;            // スワイプ確定の最小移動距離(px)
  let sx = 0, sy = 0, active = false;
  const pt = (e) => ({ x: e.clientX, y: e.clientY });
  elm.addEventListener("pointerdown", (e) => {
    active = true; const p = pt(e); sx = p.x; sy = p.y;
    try { elm.setPointerCapture(e.pointerId); } catch (_) { /* ignore */ }
  });
  elm.addEventListener("pointerup", (e) => {
    if (!active) return; active = false;
    const p = pt(e), dx = p.x - sx, dy = p.y - sy;
    const adx = Math.abs(dx), ady = Math.abs(dy);
    if (adx < TH && ady < TH) { h.onTap && h.onTap(); return; }
    if (adx > ady) (dx > 0 ? h.onRight : h.onLeft)();
    else (dy > 0 ? h.onDown : h.onUp)();
  });
}

// 1セッション分のカードを回す。queue は /api/words/quiz または
// /api/phrases/quiz の結果（opts.kind で切り替え、既定は 'word'）。
function runFlashcards(stage, initialQueue, opts) {
  const { dir, speed, auto, qs, voice } = opts;   // dir: 'en2ja' | 'ja2en'
  const kind = opts.kind || "word";               // 'word' | 'phrase'
  const apiBase = kind === "phrase" ? "/api/phrases" : "/api/words";
  const idField = kind === "phrase" ? "phrase_id" : "word_id";
  let queue = initialQueue;
  let pos = 0, revealed = false;
  const history = [];                       // {index, snapshot, action}
  const counts = { known: 0, vague: 0, wrong: 0, skip: 0 };
  const card = () => queue[pos];

  // 連続読み上げ(単語→例文)の中断管理。speakSeq が変わると進行中の読み上げを打切り。
  let speakSeq = 0;
  function stopAudio() { speakSeq++; speech.stopSpeaking(); }

  // parts: [[kind, fallbackText], ...] を順番に(終わってから次へ)読み上げる。
  async function readParts(c, parts) {
    if (!auto) return;
    const my = ++speakSeq;
    for (const [partKind, fb] of parts) {
      if (my !== speakSeq) return;          // スワイプ等で打切り
      await speech.sayItemAndWait(kind, c.id, partKind, voice, fb,
        speedOpts(speed));
    }
  }

  // 出題時: 英和は英語(単語)を先読み。和英は答えを出すまで無音。
  function readFront(c) {
    if (dir === "en2ja") readParts(c, [["word", c.english]]);
  }

  // 答え表示時の読み上げ: 単語＋例文(英和は単語を先読み済みなので例文のみ)。
  function readAnswer(c) {
    const parts = [];
    if (dir === "ja2en") parts.push(["word", c.english]);
    if (c.example) parts.push(["example", c.example]);
    if (parts.length) readParts(c, parts);
  }

  // 答えを表示: 発音記号/例文訳を埋め、単語＋例文を読み上げる。
  // フレーズには発音記号/example_ja に相当する項目が無いため、その部分は
  // 単語(kind==='word')のときだけ行う。
  async function reveal(c) {
    readAnswer(c);
    if (kind !== "word" || !c.has_detail) return;
    let d = c._detail;
    if (!d) {
      try {
        const r = await api.post(`${apiBase}/${c.id}/detail`);
        if (r.ok) d = c._detail = r.detail;
      } catch (_) { /* 詳細なしでも続行 */ }
    }
    if (!d || card() !== c) return;             // 先に進んでいたら無視
    const ipa = stage.querySelector("#fcIpa");
    const exja = stage.querySelector("#fcExJa");
    if (ipa && d.pronunciation) ipa.textContent = "発音 " + d.pronunciation;
    if (exja && d.example_ja) exja.textContent = "訳: " + d.example_ja;
  }

  function applyGrade(c, action) {
    (async () => {
      try {
        if (action === "known") {
          const r = await api.post(`${apiBase}/${c.id}/known`, { known: true });
          c.mastery = r.mastery; c.mastered = true;
          c.review_level = r.review_level; c.next_review = r.next_review;
        } else if (action === "vague") {
          const r = await api.post(`${apiBase}/${c.id}/vague`);
          c.mastery = r.mastery;
          c.review_level = r.review_level; c.next_review = r.next_review;
        } else {
          const r = await api.post(`${apiBase}/attempt`, {
            [idField]: c.id, direction: dir, correct: false, result: "wrong" });
          c.mastery = r.mastery;
          c.review_level = r.review_level; c.next_review = r.next_review;
        }
      } catch (_) { /* 失敗しても次へ進む */ }
    })();
  }

  function grade(action) {
    const c = card();
    if (!c) return;
    stopAudio();                              // スワイプしたら即停止
    history.push({ index: pos, action, snapshot: {
      mastery: c.mastery, review_level: c.review_level,
      next_review: c.next_review } });
    if (action === "known") counts.known++;
    else if (action === "vague") counts.vague++;
    else if (action === "skip") counts.skip++;
    else counts.wrong++;
    if (action !== "skip") applyGrade(c, action);
    const fly = { known: "fly-up", wrong: "fly-down", vague: "fly-right" }[action];
    const cardEl = stage.querySelector("#fcCard");
    pos++; revealed = false;
    if (cardEl && fly) {
      cardEl.classList.add(fly);
      setTimeout(render, 150);
    } else render();
  }

  async function undo() {
    if (!history.length) { toast("これ以上戻れません"); return; }
    stopAudio();                              // スワイプしたら即停止
    const { index, snapshot, action } = history.pop();
    if (action === "known") counts.known = Math.max(0, counts.known - 1);
    else if (action === "vague") counts.vague = Math.max(0, counts.vague - 1);
    else if (action === "skip") counts.skip = Math.max(0, counts.skip - 1);
    else counts.wrong = Math.max(0, counts.wrong - 1);
    const c = queue[index];
    c.mastery = snapshot.mastery; c.mastered = c.mastery >= 100;
    c.review_level = snapshot.review_level; c.next_review = snapshot.next_review;
    if (action !== "skip") {
      try { await api.post(`${apiBase}/${c.id}/restore`, snapshot); }
      catch (_) { /* ignore */ }
    }
    pos = index; revealed = true; render();
    toast("1つ戻りました（採点やり直し）");
  }

  async function fetchMore() {
    stage.innerHTML = `<p class="muted">読み込み中…</p>`;
    let more;
    try { more = await api.get(`${apiBase}/quiz?` + qs); }
    catch (_) { stage.innerHTML = `<div class="card">取得に失敗しました</div>`; return; }
    if (!more.length) {
      stage.innerHTML = `<div class="card">対象の${
        kind === "phrase" ? "フレーズ" : "単語"}がありません。</div>`; return;
    }
    queue = more; pos = 0; revealed = false; history.length = 0;
    render();
  }

  function renderDone() {
    stage.innerHTML = `<div class="card fc-done">
      <h2 style="margin-top:0">お疲れさまでした 🎉</h2>
      <p>覚えた <b>${counts.known}</b> ・ うろ覚え <b>${counts.vague}</b>
        ・ できない <b>${counts.wrong}</b> ・ 保留 <b>${counts.skip}</b></p>
      <div class="row">
        <button class="btn" id="fcMore">▶ もっと続ける</button>
        <button class="btn ghost" id="fcBack">設定に戻る</button>
      </div></div>`;
    stage.querySelector("#fcMore").addEventListener("click", fetchMore);
    stage.querySelector("#fcBack").addEventListener("click",
      () => go(kind === "phrase" ? "flashphrase" : "flashcard"));
  }

  function render() {
    const c = card();
    if (!c) { renderDone(); return; }
    const qText = dir === "en2ja" ? c.english : c.japanese;
    const aText = dir === "en2ja" ? c.japanese : c.english;
    stage.innerHTML = `<div class="fc-wrap">
      <div class="fc-progress muted">${pos + 1} / ${queue.length}
        ・ 覚${counts.known} うろ${counts.vague} ✗${counts.wrong}
        保留${counts.skip}</div>
      <div class="fc-card${revealed ? " flip" : ""}" id="fcCard">
        <div class="fc-q">${escapeHtml(qText)}</div>
        <div class="fc-side muted">${dir === "en2ja" ? "英→日" : "日→英"}</div>
        <div class="fc-a">
          <div class="fc-ans">${escapeHtml(aText)}</div>
          <div class="fc-ipa muted" id="fcIpa"></div>
          <div class="fc-ex" id="fcEx">${c.example
            ? escapeHtml(c.example) : ""}</div>
          <div class="fc-exja muted" id="fcExJa"></div>
        </div>
        <div class="fc-hint muted">タップで答え</div>
      </div>
      <div class="fc-legend muted">⬆ 覚えた ・ ⬇ できない ・ ➡ うろ覚え
        ・ ⬅ 戻る ／ カードをタップで答え</div>
      <div class="row fc-tools"></div>
      <div class="row fc-actions"></div>
    </div>`;
    const cardEl = stage.querySelector("#fcCard");
    attachSwipe(cardEl, {
      onTap: () => {
        stopAudio();
        revealed = !revealed;
        cardEl.classList.toggle("flip", revealed);
        if (revealed) reveal(c);
      },
      onUp: () => grade("known"),
      onDown: () => grade("wrong"),
      onRight: () => grade("vague"),
      onLeft: () => undo(),
    });
    // ツール: 音声(男/女)・例文再生・詳細。
    const tools = stage.querySelector(".fc-tools");
    tools.appendChild(voiceButtonsItem(
      kind, c.id, "word", () => c.english, () => speed));
    const exBtn = el(`<button class="btn ghost">🔊 例文</button>`);
    exBtn.disabled = !c.example;
    exBtn.addEventListener("click", () => { if (c.example) {
      stopAudio();
      speech.sayItem(kind, c.id, "example", voice, c.example,
        speedOpts(speed));
    } });
    const detBtn = el(`<button class="btn ghost">📖 詳細</button>`);
    detBtn.addEventListener("click",
      () => (kind === "phrase" ? showPhraseDetail(c) : showWordDetail(c)));
    tools.append(exBtn, detBtn);
    // 採点ボタン(スワイプできない端末用)。
    const actions = stage.querySelector(".fc-actions");
    const mk = (cls, label, fn) => {
      const b = el(`<button class="btn ${cls}">${label}</button>`);
      b.addEventListener("click", fn);
      return b;
    };
    actions.append(
      mk("ghost", "⬅ 戻る", undo),
      mk("ghost", "⏸ 保留", () => grade("skip")),
      mk("danger", "⬇ できない", () => grade("wrong")),
      mk("vague-btn", "➡ うろ覚え", () => grade("vague")),
      mk("good", "⬆ 覚えた", () => grade("known")),
    );
    if (revealed) reveal(c); else readFront(c);
  }

  // キーボード(PC)対応。← → ↑ ↓ で採点、Space/Enter で反転。
  const onKey = (e) => {
    if (e.key === "ArrowUp") { e.preventDefault(); grade("known"); }
    else if (e.key === "ArrowDown") { e.preventDefault(); grade("wrong"); }
    else if (e.key === "ArrowRight") { e.preventDefault(); grade("vague"); }
    else if (e.key === "ArrowLeft") { e.preventDefault(); undo(); }
    else if (e.key === "s" || e.key === "S") { e.preventDefault(); grade("skip"); }
    else if (e.key === " " || e.key === "Enter") {
      e.preventDefault();
      const cardEl = stage.querySelector("#fcCard");
      if (!cardEl) return;
      stopAudio();
      revealed = !revealed;
      cardEl.classList.toggle("flip", revealed);
      if (revealed) reveal(card());
    }
  };
  document.addEventListener("keydown", onKey);
  onLeaveView(() => document.removeEventListener("keydown", onKey));

  render();
}

export async function flashcard(root) {
  const facets = await api.get(
    "/api/words/facets" + (showBanned() ? "?include_banned=true" : ""));
  // ゲストは/api/system/user-settingsを読めない(要ログイン)ため、既定は
  // オフ(=含む)として扱う。
  const hideMasteredDefault = !!(await api.get("/api/system/user-settings")
    .catch(() => ({ settings: {} }))).settings?.hide_mastered;
  const domOpts = ['<option value="">分野: すべて</option>']
    .concat(facets.domains.map((d) => `<option>${escapeHtml(d)}</option>`))
    .join("");
  const lvOpts = '<option value="">--</option>' + facets.range_levels
    .map((l) => `<option>${escapeHtml(l)}</option>`).join("");
  const voiceOpts = speech.listOpenAIVoices().map((vn) => {
    const g = speech.voiceGender(vn);
    return `<option value="${vn}">声: ${vn}${g ? "（" + g + "）" : ""}</option>`;
  }).join("");

  root.innerHTML = `
    <h1>🃏 フラッシュ単語</h1>
    <div class="card" id="fcSetup">
      <p class="muted">単語帳をどんどんめくる高速学習。カードをタップで答え、
        スワイプ（または下のボタン）で採点します。</p>
      <div class="row">
        <select id="fcDir">
          <option value="en2ja">英和（英→日）</option>
          <option value="ja2en">和英（日→英）</option>
        </select>
        <select id="fcDom">${domOpts}</select>
      </div>
      <div class="row mt">
        <span class="muted">レベル</span>
        <select id="fcLvMin">${lvOpts}</select>
        <span class="muted">〜</span>
        <select id="fcLvMax">${lvOpts}</select>
        <select id="fcMastered">
          <option value="">覚えた: 含む</option>
          <option value="hide">覚えた: 隠す</option>
          <option value="only">覚えた: のみ</option>
        </select>
      </div>
      <div class="row mt">
        <select id="fcSize">
          <option value="20">20枚</option>
          <option value="50">50枚</option>
          <option value="100">100枚</option>
        </select>
        ${speedSelect("fcSpeed", false)}
        <select id="fcVoice" title="読み上げの声（自然な声ONのとき）">
          ${voiceOpts}</select>
        <label class="toggle"><input type="checkbox" id="fcAuto"/>
          答え表示で自動読み上げ</label>
      </div>
      <div class="row mt">
        <button class="btn" id="fcStart">▶ 開始</button>
      </div>
    </div>
    <div id="fcStage"></div>`;

  const setVal = (id, v) => {
    const e = root.querySelector(id);
    if (e && v != null) e.value = v;
  };
  setVal("#fcDir", localStorage.getItem("fc_dir") || "en2ja");
  setVal("#fcDom", localStorage.getItem("fc_dom") || "");
  setVal("#fcLvMin", localStorage.getItem("fc_lvmin") || "");
  setVal("#fcLvMax", localStorage.getItem("fc_lvmax") || "");
  // 「詳細設定」がONなら毎回「隠す」を既定にする(localStorageの過去の選択
  // より優先。localStorageには開始のたび""でも上書き保存されるため、単純に
  // 「未設定なら」という判定だと2回目以降は永遠に効かなくなってしまう)。
  // その場でドロップダウンを変えれば、そのセッション限定で一時的に閲覧可能。
  setVal("#fcMastered", hideMasteredDefault
    ? "hide" : (localStorage.getItem("fc_mastered") || ""));
  setVal("#fcSize", localStorage.getItem("fc_size") || "50");
  setVal("#fcSpeed", localStorage.getItem("fc_speed") || "std");
  setVal("#fcVoice", localStorage.getItem("fc_voice")
    || speech.loadPreferredVoice() || "nova");
  // 既定OFF(2026-08-12〜): 開始した瞬間に音声が鳴って驚く、という指摘のため
  // （電車内等での利用を想定）。一度でも明示的に選んだ値はそちらを優先する。
  root.querySelector("#fcAuto").checked =
    (localStorage.getItem("fc_auto") ?? "0") === "1";

  root.querySelector("#fcStart").addEventListener("click", async () => {
    const v = (id) => root.querySelector(id).value;
    const dir = v("#fcDir"), dom = v("#fcDom");
    const lvmin = v("#fcLvMin"), lvmax = v("#fcLvMax");
    const mastered = v("#fcMastered"), size = v("#fcSize");
    const speed = v("#fcSpeed"), voice = v("#fcVoice");
    const auto = root.querySelector("#fcAuto").checked;
    localStorage.setItem("fc_dir", dir);
    localStorage.setItem("fc_dom", dom);
    localStorage.setItem("fc_lvmin", lvmin);
    localStorage.setItem("fc_lvmax", lvmax);
    localStorage.setItem("fc_mastered", mastered);
    localStorage.setItem("fc_size", size);
    localStorage.setItem("fc_speed", speed);
    localStorage.setItem("fc_voice", voice);
    localStorage.setItem("fc_auto", auto ? "1" : "0");

    const q = new URLSearchParams({ limit: size });
    if (dom) q.set("domain", dom);
    if (lvmin) q.set("level_min", lvmin);
    if (lvmax) q.set("level_max", lvmax);
    if (mastered) q.set("mastered", mastered);
    if (showBanned()) q.set("include_banned", "true");
    const qs = q.toString();

    const stage = root.querySelector("#fcStage");
    stage.innerHTML = `<p class="muted">読み込み中…</p>`;
    let queue;
    try { queue = await api.get("/api/words/quiz?" + qs); }
    catch (_) {
      stage.innerHTML = `<div class="card">取得に失敗しました</div>`; return;
    }
    if (!queue.length) {
      stage.innerHTML = `<div class="card">該当する単語がありません。
        フィルタを緩めてください。</div>`;
      return;
    }
    runFlashcards(stage, queue, { dir, speed, auto, qs, voice, kind: "word" });
  });
}

export async function flashPhrase(root) {
  const [sceneFacets, levelFacets] = await Promise.all([
    api.get("/api/phrases/scenes" + (showBanned() ? "?include_banned=true" : "")),
    api.get("/api/phrases/facets"),
  ]);
  // ゲストは/api/system/user-settingsを読めない(要ログイン)ため、既定は
  // オフ(=含む)として扱う。
  const hideMasteredDefault = !!(await api.get("/api/system/user-settings")
    .catch(() => ({ settings: {} }))).settings?.hide_mastered;
  const sceneOpts = ['<option value="">シーン: すべて</option>']
    .concat(sceneFacets.scenes.map((s) => `<option>${escapeHtml(s)}</option>`))
    .join("");
  const lvOpts = '<option value="">--</option>' + levelFacets.range_levels
    .map((l) => `<option>${escapeHtml(l)}</option>`).join("");
  const voiceOpts = speech.listOpenAIVoices().map((vn) => {
    const g = speech.voiceGender(vn);
    return `<option value="${vn}">声: ${vn}${g ? "（" + g + "）" : ""}</option>`;
  }).join("");

  root.innerHTML = `
    <h1>🃏 フラッシュフレーズ</h1>
    <div class="card" id="fpSetup">
      <p class="muted">フレーズ帳をどんどんめくる高速学習。カードをタップで答え、
        スワイプ（または下のボタン）で採点します。</p>
      <div class="row">
        <select id="fpDir">
          <option value="en2ja">英和（英→日）</option>
          <option value="ja2en">和英（日→英）</option>
        </select>
        <select id="fpScene">${sceneOpts}</select>
      </div>
      <div class="row mt">
        <span class="muted">レベル</span>
        <select id="fpLvMin">${lvOpts}</select>
        <span class="muted">〜</span>
        <select id="fpLvMax">${lvOpts}</select>
        <select id="fpMastered">
          <option value="">覚えた: 含む</option>
          <option value="hide">覚えた: 隠す</option>
          <option value="only">覚えた: のみ</option>
        </select>
      </div>
      <div class="row mt">
        <select id="fpSize">
          <option value="20">20枚</option>
          <option value="50">50枚</option>
          <option value="100">100枚</option>
        </select>
        ${speedSelect("fpSpeed", false)}
        <select id="fpVoice" title="読み上げの声（自然な声ONのとき）">
          ${voiceOpts}</select>
        <label class="toggle"><input type="checkbox" id="fpAuto"/>
          答え表示で自動読み上げ</label>
      </div>
      <div class="row mt">
        <button class="btn" id="fpStart">▶ 開始</button>
      </div>
    </div>
    <div id="fpStage"></div>`;

  const setVal = (id, v) => {
    const e = root.querySelector(id);
    if (e && v != null) e.value = v;
  };
  setVal("#fpDir", localStorage.getItem("fp_dir") || "en2ja");
  setVal("#fpScene", localStorage.getItem("fp_scene") || "");
  setVal("#fpLvMin", localStorage.getItem("fp_lvmin") || "");
  setVal("#fpLvMax", localStorage.getItem("fp_lvmax") || "");
  // 「詳細設定」がONなら毎回「隠す」を既定にする(理由はflashcard()と同じ)。
  setVal("#fpMastered", hideMasteredDefault
    ? "hide" : (localStorage.getItem("fp_mastered") || ""));
  setVal("#fpSize", localStorage.getItem("fp_size") || "50");
  setVal("#fpSpeed", localStorage.getItem("fp_speed") || "std");
  setVal("#fpVoice", localStorage.getItem("fp_voice")
    || speech.loadPreferredVoice() || "nova");
  // 既定OFF(2026-08-12〜): フラッシュ単語と同じ理由(開始直後に音声が鳴って
  // 驚くという指摘)。一度でも明示的に選んだ値はそちらを優先する。
  root.querySelector("#fpAuto").checked =
    (localStorage.getItem("fp_auto") ?? "0") === "1";

  root.querySelector("#fpStart").addEventListener("click", async () => {
    const v = (id) => root.querySelector(id).value;
    const dir = v("#fpDir"), scene = v("#fpScene");
    const lvmin = v("#fpLvMin"), lvmax = v("#fpLvMax");
    const mastered = v("#fpMastered"), size = v("#fpSize");
    const speed = v("#fpSpeed"), voice = v("#fpVoice");
    const auto = root.querySelector("#fpAuto").checked;
    localStorage.setItem("fp_dir", dir);
    localStorage.setItem("fp_scene", scene);
    localStorage.setItem("fp_lvmin", lvmin);
    localStorage.setItem("fp_lvmax", lvmax);
    localStorage.setItem("fp_mastered", mastered);
    localStorage.setItem("fp_size", size);
    localStorage.setItem("fp_speed", speed);
    localStorage.setItem("fp_voice", voice);
    localStorage.setItem("fp_auto", auto ? "1" : "0");

    const q = new URLSearchParams({ limit: size });
    if (scene) q.set("scene", scene);
    if (lvmin) q.set("level_min", lvmin);
    if (lvmax) q.set("level_max", lvmax);
    if (mastered) q.set("mastered", mastered);
    if (showBanned()) q.set("include_banned", "true");
    const qs = q.toString();

    const stage = root.querySelector("#fpStage");
    stage.innerHTML = `<p class="muted">読み込み中…</p>`;
    let queue;
    try { queue = await api.get("/api/phrases/quiz?" + qs); }
    catch (_) {
      stage.innerHTML = `<div class="card">取得に失敗しました</div>`; return;
    }
    if (!queue.length) {
      stage.innerHTML = `<div class="card">該当するフレーズがありません。
        フィルタを緩めてください。</div>`;
      return;
    }
    runFlashcards(stage, queue, { dir, speed, auto, qs, voice, kind: "phrase" });
  });
}

// 分野/シーンの複数選択チェックボックス・ドロップダウン（2026-08-06・
// ユーザー要望「フィルターを複数選択できるように」）。ボタンをクリックすると
// グループ分けされたチェックボックス一覧を開く。`selected`(Set)を直接
// ミューテートするので、呼び出し側はそのSetをフィルタ条件の組み立てに使う。
function initCheckDropdown(root, btnId, panelId, groupsGetter, selected,
  onChange, label) {
  const btn = root.querySelector(`#${btnId}`);
  const panel = root.querySelector(`#${panelId}`);
  const refreshLabel = () => {
    btn.textContent = selected.size
      ? `${label}: ${selected.size}件選択中 ▾` : `${label}: 全て ▾`;
  };
  const renderPanel = () => {
    const groups = groupsGetter();
    const clearRow = selected.size
      ? `<div class="cd-clear-row">
          <button type="button" class="btn ghost" id="${panelId}_clear">
            選択をクリア（${selected.size}件）</button>
        </div>` : "";
    panel.innerHTML = clearRow + Object.entries(groups).map(([g, items]) => `
      <div class="cd-group">
        <div class="cd-group-label">${escapeHtml(g)}</div>
        ${items.map((it) => `<label class="cd-item">
          <input type="checkbox" value="${escapeHtml(it)}"
            ${selected.has(it) ? "checked" : ""}/> ${escapeHtml(it)}</label>`)
          .join("")}
      </div>`).join("");
    panel.querySelectorAll("input[type=checkbox]").forEach((cb) => {
      cb.addEventListener("change", () => {
        if (cb.checked) selected.add(cb.value); else selected.delete(cb.value);
        refreshLabel();
        onChange();
        renderPanel();
      });
    });
    panel.querySelector(`#${panelId}_clear`)?.addEventListener("click", () => {
      selected.clear();
      refreshLabel();
      onChange();
      renderPanel();
    });
  };
  btn.addEventListener("click", (e) => {
    e.stopPropagation();
    panel.classList.toggle("open");
  });
  document.addEventListener("click", (e) => {
    if (!panel.contains(e.target) && e.target !== btn) {
      panel.classList.remove("open");
    }
  });
  refreshLabel();
  renderPanel();
  return { renderPanel, refreshLabel };
}

export async function vocab(root) {
  const facets = await api.get(
    "/api/words/facets" + (showBanned() ? "?include_banned=true" : ""));
  const domainGroups = facets.domain_groups || {};
  const myDecks = await api.get("/api/decks").catch(() => []);
  // ゲストは/api/system/user-settingsを読めない(要ログイン)ため、既定
  // フィルター無し(={})として扱う(2026-08-11・ゲスト実装で発見)。
  const us = (await api.get("/api/system/user-settings")
    .catch(() => ({ settings: {} }))).settings || {};
  const dfw = us.default_word_filters || {};
  const hideMasteredDefault = !!us.hide_mastered;
  const dfwActive = !!(dfw.category || dfw.level_min || dfw.level_max
    || dfw.mastered);
  root.innerHTML = `
    <h1>英単語</h1>
    <p class="sub">両方向(英→日 / 日→英)で出題。習熟度・正答率・忘却曲線を管理。</p>
    <div class="row">
      <button class="btn" id="quiz">クイズ開始 (10語)</button>
      <span class="muted">単語の追加・一括インポートは ⚙️設定 に移動しました。</span>
    </div>
    ${dfwActive ? `<p class="muted">⚙️ 設定の既定フィルターを適用中です。
      この画面でその場変更もできます。</p>` : ""}
    <div class="card">
      <h2 id="listTitle">単語一覧</h2>
      <div class="row">
        <input id="kw" placeholder="🔍 英語・日本語で検索" style="width:200px" />
        <select id="fCategory" title="大分類"><option value="">全カテゴリ</option>
          ${Object.keys(domainGroups).map((c) =>
            `<option>${escapeHtml(c)}</option>`).join("")}</select>
        <span class="cdrop">
          <button type="button" class="btn ghost" id="fDomainBtn">全て ▾</button>
          <div class="cdrop-panel" id="fDomainPanel"></div>
        </span>
        <span class="muted">Lv</span>
        <select id="fLevelMin" title="レベル下限"><option value="">下限</option>
          ${(facets.range_levels || facets.levels).map((l) =>
            `<option>${escapeHtml(l)}</option>`).join("")}</select>
        <span class="muted">〜</span>
        <select id="fLevelMax" title="レベル上限"><option value="">上限</option>
          ${(facets.range_levels || facets.levels).map((l) =>
            `<option>${escapeHtml(l)}</option>`).join("")}</select>
        <label class="toggle" title="範囲外(禁止用語相当)も含める">
          <input type="checkbox" id="fOutRange" /> 範囲外</label>
        <label class="toggle" title="無料で🔊再生できる語だけに絞り込む
          （未ログイン/ログイン無料ユーザー向け）">
          <input type="checkbox" id="fFreeOnly" /> 🔊再生できるものだけ</label>
        ${myDecks.length ? `<select id="fDeck" title="単語帳で絞り込み">
          <option value="">単語帳: 全て</option>
          ${myDecks.map((d) =>
            `<option value="${d.id}">📘 ${escapeHtml(d.name)}</option>`)
            .join("")}</select>` : ""}
        <select id="fSort">
          <option value="mastery">並び替え: 習熟度 ↑</option>
          <option value="accuracy">並び替え: 正答率 ↓</option>
          <option value="english">並び替え: 英語 A→Z</option>
          <option value="level">並び替え: レベル</option>
          <option value="domain">並び替え: 分野</option>
          <option value="recent">並び替え: 最近の学習</option>
        </select>
        <button class="btn ghost" id="fDir"
          title="昇順/降順を切替">昇順 ▲</button>
        <select id="fMastered" title="覚えた語の表示">
          <option value="">覚えた: 含む</option>
          <option value="hide">覚えた: 隠す</option>
          <option value="only">覚えた: のみ</option>
        </select>
        ${speedSelect("wSpeed", false)}
        ${pageSizeSelect("wPage")}
        ${state.isAdmin ? `<label class="toggle"
          title="禁止用語(注意喚起)を一覧に表示">
          <input type="checkbox" id="showBanned"
          ${showBanned() ? "checked" : ""} />
          🔞 禁止用語も表示</label>` : ""}
      </div>
      <table class="mt rtable rtable-words"><thead><tr>
        <th>再生</th><th>英語</th><th>日本語</th><th>Lv</th><th>分野</th>
        <th>習熟度</th><th>正答率</th><th>操作</th></tr></thead>
        <tbody id="rows"></tbody></table>
      <div id="pager" class="mt"></div>
    </div>`;

  const rowsBody = root.querySelector("#rows");
  const title = root.querySelector("#listTitle");
  const kw = root.querySelector("#kw");
  const pagerEl = root.querySelector("#pager");
  let curWords = [];
  let wPage = 0;
  const selectedDomains = new Set();

  const paint = () => {
    const size = root.querySelector("#wPage").value;
    const { slice, page, pages } = pageSlice(curWords, wPage, size);
    wPage = page;
    title.textContent = `単語一覧 (${curWords.length})`;
    renderTable(slice);
    pagerEl.innerHTML = "";
    pagerEl.appendChild(pagerBar(curWords.length, page, pages,
      () => { wPage = page - 1; paint(); },
      () => { wPage = page + 1; paint(); }));
  };

  const renderTable = (words) => {
    rowsBody.innerHTML = "";
    words.forEach((w) => {
      const tr = el(`<tr>
        <td></td>
        <td data-label="英語">${escapeHtml(w.english)}</td>
        <td data-label="日本語">${escapeHtml(w.japanese)}</td>
        <td class="muted pair2" data-label="Lv">${w.level || ""}</td>
        <td class="pair2" data-label="分野">${w.domain
          ? `<span class="pill">${escapeHtml(w.domain)}</span>` : ""}</td>
        <td class="pair2" style="min-width:80px" data-mc="1"
          data-label="習熟度">${masteryCell(w)}</td>
        <td class="pair2" data-label="正答率">${w.accuracy == null
          ? "—" : w.accuracy + "%"}</td>
        <td><div class="ops-cell"></div></td>
      </tr>`);
      // 番号(ID)で再生。保存済みなら無料、無ければ合成して保存。
      tr.firstElementChild.appendChild(voiceButtonsItem(
        "word", w.id, "word", () => w.english,
        () => root.querySelector("#wSpeed").value));
      const ops = tr.querySelector("td:last-child .ops-cell");
      const mc = tr.querySelector("[data-mc]");
      const ex = el(`<button class="btn good">詳細</button>`);
      ex.addEventListener("click", () => showWordDetail(w));
      const repaint = () => { mc.innerHTML = masteryCell(w); };
      const vague = vagueButton("/api/words", w, repaint);
      const known = knownButton("/api/words", w, repaint);
      ops.append(ex, vague, known);
      rowsBody.appendChild(tr);
    });
  };

  // 分野/レベル/並び替え/禁止表示はサーバ側、キーワードはクライアント側。
  const load = async () => {
    const q = new URLSearchParams({ sort: root.querySelector("#fSort").value });
    if (selectedDomains.size) {
      q.set("domain", [...selectedDomains].join(","));
    } else {
      const cat = root.querySelector("#fCategory").value;
      if (cat) q.set("category", cat);
    }
    const lmin = root.querySelector("#fLevelMin").value;
    const lmax = root.querySelector("#fLevelMax").value;
    if (lmin) q.set("level_min", lmin);
    if (lmax) q.set("level_max", lmax);
    if (root.querySelector("#fOutRange").checked) q.set("out_of_range", "true");
    const ms = root.querySelector("#fMastered").value;
    if (ms) q.set("mastered", ms);
    if (root.querySelector("#fDir").dataset.desc === "1") q.set("desc", "true");
    if (showBanned()) q.set("include_banned", "true");
    if (root.querySelector("#fFreeOnly").checked) {
      q.set("free_range_only", "true");
    }
    const deckSel = root.querySelector("#fDeck");
    if (deckSel && deckSel.value) q.set("deck_id", deckSel.value);
    const words = await api.get("/api/words?" + q.toString());
    const term = kw.value.trim().toLowerCase();
    curWords = term ? words.filter((w) =>
      w.english.toLowerCase().includes(term)
      || (w.japanese || "").toLowerCase().includes(term)) : words;
    wPage = 0;
    paint();
  };
  const fDir = root.querySelector("#fDir");
  fDir.addEventListener("click", () => {
    const d = fDir.dataset.desc === "1" ? "0" : "1";
    fDir.dataset.desc = d;
    fDir.textContent = d === "1" ? "降順 ▼" : "昇順 ▲";
    load();
  });
  ["#fLevelMin", "#fLevelMax", "#fOutRange", "#fFreeOnly", "#fSort",
   "#fMastered"].forEach((id) =>
    root.querySelector(id).addEventListener("change", load));
  root.querySelector("#fDeck")?.addEventListener("change", load);
  // 分野チェックボックス（複数選択可）。大分類を選ぶと候補が絞り込まれる
  // （大分類だけでもカテゴリ配下の全分野を検索対象にできる＝分野は
  // 「未選択」のままでよい）。
  const domainDropdown = initCheckDropdown(root, "fDomainBtn", "fDomainPanel",
    () => {
      const cat = root.querySelector("#fCategory").value;
      return cat ? { [cat]: domainGroups[cat] || [] } : domainGroups;
    }, selectedDomains, load, "分野");
  root.querySelector("#fCategory").addEventListener("change", () => {
    selectedDomains.clear();
    domainDropdown.renderPanel();
    domainDropdown.refreshLabel();
    load();
  });
  root.querySelector("#wPage").addEventListener("change", () => {
    wPage = 0; paint();
  });
  // 禁止表示の切替で分野フィルタの候補(禁止用語)も変わるので作り直す。
  const sbW = root.querySelector("#showBanned");
  if (sbW) sbW.addEventListener("change", (e) => {
    setShowBanned(e.target.checked); go("vocab");
  });
  kw.addEventListener("input", load);
  if (dfwActive) {
    if (dfw.category) root.querySelector("#fCategory").value = dfw.category;
    if (dfw.level_min) root.querySelector("#fLevelMin").value = dfw.level_min;
    if (dfw.level_max) root.querySelector("#fLevelMax").value = dfw.level_max;
    if (dfw.mastered) root.querySelector("#fMastered").value = dfw.mastered;
  }
  load();

  root.querySelector("#quiz").addEventListener("click", async () => {
    const tb = testBanned() ? "&include_banned=true" : "";
    const mb = hideMasteredDefault ? "&mastered=hide" : "";
    const items = await api.get("/api/words/quiz?limit=10" + tb + mb);
    const c = root; c.innerHTML = `<h1>単語クイズ</h1>`;
    const holder = el(`<div></div>`); c.appendChild(holder);
    quizRunner({ container: holder, items, kind: "word", appState: state,
      onDone: () => {
        const b = el(`<button class="btn mt">単語一覧へ戻る</button>`);
        b.addEventListener("click", () => go("vocab")); holder.appendChild(b);
      } });
  });
}

// --- Phrases ----------------------------------------------------------------

export async function phrases(root) {
  const sb = bannedParam(showBanned());
  const sceneData = await api.get(
    "/api/phrases/scenes" + (sb ? "?" + sb : ""));
  const sceneGroups = sceneData.scene_groups || {};
  const pfacets = await api.get("/api/phrases/facets");
  const list = await api.get("/api/phrases" + (sb ? "?" + sb : ""));
  const myDecks = await api.get("/api/phrase-decks").catch(() => []);
  // ゲストは/api/system/user-settingsを読めない(要ログイン)ため、既定
  // フィルター無し(={})として扱う(2026-08-11・ゲスト実装で発見)。
  const usP = (await api.get("/api/system/user-settings")
    .catch(() => ({ settings: {} }))).settings || {};
  const dfp = usP.default_phrase_filters || {};
  const hideMasteredDefault = !!usP.hide_mastered;
  const dfpActive = !!(dfp.category || dfp.level_min || dfp.level_max
    || dfp.mastered);
  root.innerHTML = `
    <h1>ミニフレーズ</h1>
    <p class="sub">場面別の短い表現。単語と同じく両方向＋忘却曲線で管理。</p>
    ${dfpActive ? `<p class="muted">⚙️ 設定の既定フィルターを適用中です。
      この画面でその場変更もできます。</p>` : ""}
    <div class="row">
      <button class="btn" id="quiz">クイズ開始 (10フレーズ)</button>
      <select id="sceneCategory" title="大分類"><option value="">全カテゴリ</option>
        ${Object.keys(sceneGroups).map((c) =>
          `<option>${escapeHtml(c)}</option>`).join("")}</select>
      <span class="cdrop">
        <button type="button" class="btn ghost" id="fSceneBtn">全て ▾</button>
        <div class="cdrop-panel" id="fScenePanel"></div>
      </span>
      ${state.isAdmin ? `<label class="toggle"
        title="禁止用語(注意喚起)を一覧に表示">
        <input type="checkbox" id="showBanned"
        ${showBanned() ? "checked" : ""} />
        🔞 禁止用語も表示</label>` : ""}
    </div>
    <div class="row">
      <span class="muted">フレーズの追加は ⚙️設定 に移動しました。</span>
    </div>
    <div class="card">
      <h2 id="listTitle">一覧 (${list.length})</h2>
      <div class="row">
        <input id="kw" placeholder="🔍 英語・日本語で検索" style="width:180px" />
        <span class="muted">Lv</span>
        <select id="fLevelMin" title="レベル下限"><option value="">下限</option>
          ${(pfacets.range_levels || []).map((l) =>
            `<option>${escapeHtml(l)}</option>`).join("")}</select>
        <span class="muted">〜</span>
        <select id="fLevelMax" title="レベル上限"><option value="">上限</option>
          ${(pfacets.range_levels || []).map((l) =>
            `<option>${escapeHtml(l)}</option>`).join("")}</select>
        <label class="toggle" title="範囲外も含める">
          <input type="checkbox" id="fOutRange" /> 範囲外</label>
        <label class="toggle" title="無料で🔊再生できるフレーズだけに絞り込む
          （未ログイン/ログイン無料ユーザー向け）">
          <input type="checkbox" id="fFreeOnly" /> 🔊再生できるものだけ</label>
        ${myDecks.length ? `<select id="fDeck" title="フレーズ帳で絞り込み">
          <option value="">フレーズ帳: 全て</option>
          ${myDecks.map((d) =>
            `<option value="${d.id}">🗂️ ${escapeHtml(d.name)}</option>`)
            .join("")}</select>` : ""}
        <select id="fSort">
          <option value="mastery">並び替え: 習熟度 ↑</option>
          <option value="accuracy">並び替え: 正答率 ↓</option>
          <option value="english">並び替え: 英語 A→Z</option>
          <option value="scene">並び替え: シーン</option>
          <option value="recent">並び替え: 最近の学習</option>
          <option value="added">並び替え: 登録順(ペア対応)</option>
        </select>
        <button class="btn ghost" id="fDir"
          title="昇順/降順を切替">昇順 ▲</button>
        <select id="fMastered" title="覚えたフレーズの表示">
          <option value="">覚えた: 含む</option>
          <option value="hide">覚えた: 隠す</option>
          <option value="only">覚えた: のみ</option>
        </select>
        ${speedSelect("pSpeed")}
        ${pageSizeSelect("pPage")}
      </div>
      <table class="mt rtable"><thead><tr><th>再生</th><th>英語</th><th>日本語</th>
        <th>シーン</th><th>習熟度</th><th>操作</th></tr></thead>
        <tbody id="rows"></tbody></table>
      <div id="pager" class="mt"></div>
    </div>`;

  const title = root.querySelector("#listTitle");
  const kw = root.querySelector("#kw");
  const pagerEl = root.querySelector("#pager");
  let curList = [];
  let pPage = 0;
  const selectedScenes = new Set();

  const paint = () => {
    const size = root.querySelector("#pPage").value;
    const { slice, page, pages } = pageSlice(curList, pPage, size);
    pPage = page;
    title.textContent = `一覧 (${curList.length})`;
    renderRows(slice);
    pagerEl.innerHTML = "";
    pagerEl.appendChild(pagerBar(curList.length, page, pages,
      () => { pPage = page - 1; paint(); },
      () => { pPage = page + 1; paint(); }));
  };

  const renderRows = (items) => {
    const rows = root.querySelector("#rows"); rows.innerHTML = "";
    items.forEach((p) => {
      const tr = el(`<tr>
        <td></td>
        <td data-label="英語">${escapeHtml(p.english)}</td>
        <td data-label="日本語">${escapeHtml(p.japanese)}</td>
        <td data-label="シーン"><span class="pill">
          ${escapeHtml(p.scene || "")}</span></td>
        <td data-mc="1" data-label="習熟度">${masteryCell(p)}</td>
        <td><div class="ops-cell"></div></td>
      </tr>`);
      tr.firstElementChild.appendChild(voiceButtonsItem(
        "phrase", p.id, "phrase", () => p.english,
        () => root.querySelector("#pSpeed").value));
      const ops = tr.querySelector("td:last-child .ops-cell");
      const mc = tr.querySelector("[data-mc]");
      const det = el(`<button class="btn good">詳細</button>`);
      det.addEventListener("click", () => showPhraseDetail(p));
      const repaint = () => { mc.innerHTML = masteryCell(p); };
      const vague = vagueButton("/api/phrases", p, repaint);
      const known = knownButton("/api/phrases", p, repaint);
      ops.append(det, vague, known);
      rows.appendChild(tr);
    });
  };
  if (!dfpActive) { curList = list; pPage = 0; paint(); }

  // シーン・並び替え・禁止表示はサーバ側、キーワードはクライアント側。
  const load = async () => {
    const q = new URLSearchParams({ sort: root.querySelector("#fSort").value });
    if (selectedScenes.size) {
      q.set("scene", [...selectedScenes].join(","));
    } else {
      const cat = root.querySelector("#sceneCategory").value;
      if (cat) q.set("category", cat);
    }
    const lmin = root.querySelector("#fLevelMin").value;
    const lmax = root.querySelector("#fLevelMax").value;
    if (lmin) q.set("level_min", lmin);
    if (lmax) q.set("level_max", lmax);
    if (root.querySelector("#fOutRange").checked) q.set("out_of_range", "true");
    const ms = root.querySelector("#fMastered").value;
    if (ms) q.set("mastered", ms);
    if (root.querySelector("#fDir").dataset.desc === "1") q.set("desc", "true");
    if (showBanned()) q.set("include_banned", "true");
    if (root.querySelector("#fFreeOnly").checked) {
      q.set("free_range_only", "true");
    }
    const deckSel = root.querySelector("#fDeck");
    if (deckSel && deckSel.value) q.set("deck_id", deckSel.value);
    const items = await api.get("/api/phrases?" + q.toString());
    const term = kw.value.trim().toLowerCase();
    curList = term ? items.filter((p) =>
      p.english.toLowerCase().includes(term)
      || (p.japanese || "").toLowerCase().includes(term)) : items;
    pPage = 0;
    paint();
  };
  const fDir = root.querySelector("#fDir");
  fDir.addEventListener("click", () => {
    const d = fDir.dataset.desc === "1" ? "0" : "1";
    fDir.dataset.desc = d;
    fDir.textContent = d === "1" ? "降順 ▼" : "昇順 ▲";
    load();
  });
  // シーンチェックボックス（複数選択可）。大分類を選ぶと候補が絞り込まれる。
  const sceneDropdown = initCheckDropdown(root, "fSceneBtn", "fScenePanel",
    () => {
      const cat = root.querySelector("#sceneCategory").value;
      return cat ? { [cat]: sceneGroups[cat] || [] } : sceneGroups;
    }, selectedScenes, load, "シーン");
  root.querySelector("#sceneCategory").addEventListener("change", () => {
    selectedScenes.clear();
    sceneDropdown.renderPanel();
    sceneDropdown.refreshLabel();
    load();
  });
  root.querySelector("#fSort").addEventListener("change", load);
  root.querySelector("#fMastered").addEventListener("change", load);
  ["#fLevelMin", "#fLevelMax", "#fOutRange", "#fFreeOnly"].forEach((id) =>
    root.querySelector(id).addEventListener("change", load));
  root.querySelector("#fDeck")?.addEventListener("change", load);
  root.querySelector("#pPage").addEventListener("change", () => {
    pPage = 0; paint();
  });
  // 禁止表示の切替はシーン候補も変わるので画面を作り直す。
  const sbP = root.querySelector("#showBanned");
  if (sbP) sbP.addEventListener("change", (e) => {
    setShowBanned(e.target.checked); go("phrases");
  });
  kw.addEventListener("input", load);
  if (dfpActive) {
    if (dfp.category) root.querySelector("#sceneCategory").value = dfp.category;
    if (dfp.level_min) root.querySelector("#fLevelMin").value = dfp.level_min;
    if (dfp.level_max) root.querySelector("#fLevelMax").value = dfp.level_max;
    if (dfp.mastered) root.querySelector("#fMastered").value = dfp.mastered;
    load();
  }

  root.querySelector("#quiz").addEventListener("click", async () => {
    const tb = testBanned() ? "&include_banned=true" : "";
    const mb = hideMasteredDefault ? "&mastered=hide" : "";
    const items = await api.get("/api/phrases/quiz?limit=10" + tb + mb);
    root.innerHTML = `<h1>フレーズクイズ</h1>`;
    const holder = el(`<div></div>`); root.appendChild(holder);
    quizRunner({ container: holder, items, kind: "phrase", appState: state,
      onDone: () => {
        const b = el(`<button class="btn mt">一覧へ戻る</button>`);
        b.addEventListener("click", () => go("phrases")); holder.appendChild(b);
      } });
  });
}

// --- Generic AI material view (reading / news / literature / listening) -----

// 生成済み題材の履歴パネル。再表示(無料)＋覚えた/うろ覚え/削除。
// areas: カンマ区切りの領域。showInto(body): 本文を表示するコールバック。
async function renderHistory(panel, areas, showInto) {
  panel.innerHTML = `<p class="muted">読み込み中…</p>`;
  const list = await api.get(
    "/api/learn/materials?areas=" + encodeURIComponent(areas) + "&limit=100");
  panel.innerHTML = "";
  const head = el(`<div class="row" style="justify-content:space-between">
    <h3 style="margin:0">履歴 (${list.length})</h3></div>`);
  panel.appendChild(head);
  if (!list.length) {
    panel.appendChild(el(`<p class="muted">まだ履歴がありません。</p>`));
    return;
  }
  list.forEach((m) => {
    const badge = m.mastery >= 100
      ? `<span class="pill mastered">覚えた</span>`
      : (m.mastery > 0 ? `<span class="pill">${m.mastery}</span>` : "");
    const row = el(`<div class="hist-row">
      <span class="hist-title">${escapeHtml(m.title)} ${badge}</span>
      <span class="ops-cell"></span></div>`);
    const ops = row.querySelector(".ops-cell");
    const show = el(`<button class="btn ghost">再表示</button>`);
    show.addEventListener("click", () => showInto(m.body));
    const vague = el(`<button class="vague-btn btn">うろ覚え</button>`);
    vague.addEventListener("click", async () => {
      const r = await api.post(`/api/learn/materials/${m.id}/vague`);
      m.mastery = r.mastery; renderHistory(panel, areas, showInto);
      toast("うろ覚え +10");
    });
    const known = el(`<button class="btn blue">覚えた</button>`);
    known.addEventListener("click", async () => {
      await api.post(`/api/learn/materials/${m.id}/known`);
      m.mastery = 200; renderHistory(panel, areas, showInto); toast("覚えた");
    });
    const del = deleteButton(m.title, async () => {
      await api.del(`/api/learn/materials/${m.id}`);
      renderHistory(panel, areas, showInto);
    });
    ops.append(show, vague, known, del);
    panel.appendChild(row);
  });
}

function materialView(title, sub, area, fields, histAreas) {
  return async function (root) {
    root.innerHTML = `
      <h1>${title}</h1>
      <p class="sub">${sub}</p>
      ${aiBadgeNote()}
      <div class="card">
        <div class="row">
          <select id="field">${fields.map((f) =>
            `<option>${f}</option>`).join("")}</select>
          ${diffSelect("fdiff")}
          ${lengthSelect("flen")}
          <label class="toggle" title="内容理解問題を表示(常に生成・保存)">
            <input type="checkbox" id="showQ" checked /> 内容理解問題</label>
          <input id="inst" placeholder="追加指示(任意)" style="width:160px" />
          <button class="btn" id="gen" ${state.aiEnabled ? "" : "disabled"}>
            生成</button>
          <button class="btn ghost" id="histBtn">📚 履歴</button>
        </div>
      </div>
      <div id="histPanel" class="card" style="display:none"></div>
      <div class="card"><div id="out" class="md">
        左上で分野を選んで「生成」を押してください。</div></div>`;
    root.appendChild(sampleMaterialsCard(area,
      "📖 サンプルを見る", "サンプルがまだありません。"));
    // 内容理解問題トグル: OFFなら表示・読み上げから問題部分を除く（保存はフル）。
    const disp = (b) =>
      root.querySelector("#showQ").checked ? b : stripQuestions(b);
    const showInto = (body) => {
      const out = root.querySelector("#out");
      out.innerHTML = "";
      out.appendChild(readAloudBar(() => disp(body), "reading_tts"));
      const b = el(`<div class="md mt"></div>`); b.innerHTML = md(disp(body));
      out.appendChild(b);
      out.appendChild(readAloudBar(() => disp(body), "reading_tts"));
    };
    const panel = root.querySelector("#histPanel");
    root.querySelector("#histBtn").addEventListener("click", () => {
      if (panel.style.display === "none") {
        panel.style.display = "";
        renderHistory(panel, histAreas || area, showInto);
      } else { panel.style.display = "none"; }
    });
    root.querySelector("#gen").addEventListener("click", async () => {
      const out = root.querySelector("#out");
      out.textContent = "生成中…";
      // 文学/ニュースのトピックは適切な生成プロンプト(area)に振り分け。
      const field = root.querySelector("#field").value;
      let genArea = area;
      if (field.startsWith("文学(")) genArea = "literature";
      else if (field.startsWith("ニュース(")) genArea = "news";
      const len = LENGTH_INSTR[root.querySelector("#flen").value] || "";
      const r = await api.post("/api/learn/generate", {
        area: genArea, field,
        difficulty: root.querySelector("#fdiff").value,
        instruction: (len ? `本文は${len}作成。` : "")
          + root.querySelector("#inst").value,
      });
      if (!r.ok) { out.textContent = r.error; return; }
      showInto(r.body);   // disp() で問題トグルを反映
      refreshCost();
    });
  };
}

// リーディングに「文学」「ニュース」も統合（独立タブは廃止）。
export const reading = (root) => materialView(
  "リーディング",
  "分野別の長文（文学・ニュースも含む）と理解問題をAIが生成します。",
  "reading",
  [
    "一般", "新聞", "雑誌", "ビジネスメール", "技術文書", "API仕様書",
    "エラーメッセージ", "歴史", "文化",
    "文学(シェイクスピア)", "文学(英文学)", "文学(古典)",
    ...(state.taxonomy.news_fields.length
      ? state.taxonomy.news_fields.map((f) => "ニュース(" + f + ")")
      : ["ニュース(政治)", "ニュース(経済)", "ニュース(AI)",
         "ニュース(IT)"]),
  ], "reading,literature,news")(root);

// --- Writing ----------------------------------------------------------------

// あらかじめ用意した「サンプル」教材(is_public_sample=1)だけを一覧表示
// する共通カード。AI課金は発生しない（既存の保存済み教材を表示するのみ）。
// クリックでモーダル表示。無課金/未ログインでも「どんな機能か」を確認
// できる（2026-08-12: 個人の生成履歴が混ざらないよう、専用の読み取り
// 専用API `/api/learn/samples` を使う。ログイン有無を問わず同じ結果）。
function sampleMaterialsCard(area, cardTitle, emptyLabel) {
  const card = el(`<div class="card">
    <h2>${escapeHtml(cardTitle)}</h2>
    <p class="muted">実際にAIを使わなくても内容を確認できるサンプルです。
      無課金でもご覧いただけます。</p>
    <div class="row" id="smList"><p class="muted">読み込み中…</p></div>
  </div>`);
  (async () => {
    const list = card.querySelector("#smList");
    let items = [];
    try {
      items = await api.get(
        `/api/learn/samples?area=${encodeURIComponent(area)}&limit=50`);
    } catch (_) { /* 未ログイン等 */ }
    if (!items.length) {
      list.innerHTML = `<p class="muted">${escapeHtml(emptyLabel)}</p>`;
      return;
    }
    list.innerHTML = "";
    items.forEach((m) => {
      const btn = el(`<button class="btn ghost"
        style="margin:2px">${escapeHtml(m.field || m.title)}</button>`);
      btn.addEventListener("click", () => {
        openModal(m.title, (box) => { box.innerHTML = md(m.body); });
      });
      list.appendChild(btn);
    });
  })();
  return card;
}

export async function writing(root) {
  root.innerHTML = `
    <h1>ライティング</h1>
    <p class="sub">英文を書く(または話す)とAIが添削します。音声応答可。</p>
    ${aiBadgeNote()}
    <div class="card">
      <div class="row">
        <select id="cat">
          ${["日常文章", "ビジネスメール", "IT文書", "技術仕様書"]
            .map((c) => `<option>${c}</option>`).join("")}</select>
        <input id="prompt" placeholder="お題(任意)" style="width:320px" />
      </div>
      <div id="ans"></div>
      <div id="fb" class="md mt"></div>
    </div>`;
  root.appendChild(sampleMaterialsCard("writing_sample",
    "📝 添削サンプルを見る", "サンプルがまだありません。"));
  const ansBox = root.querySelector("#ans");
  ansBox.appendChild(answerInput(async (txt) => {
    if (!txt.trim()) { toast("文章が空です"); return; }
    const fb = root.querySelector("#fb");
    if (!state.aiEnabled) { fb.textContent = "AI未設定です。"; return; }
    fb.textContent = "添削中…";
    const r = await api.post("/api/learn/writing-feedback", {
      category: root.querySelector("#cat").value,
      prompt: root.querySelector("#prompt").value,
      text: txt,
    });
    fb.innerHTML = r.ok ? md(r.feedback) : escapeHtml(r.error);
    if (r.ok) { const s = el(`<button class="btn ghost mt">🔊 読み上げ</button>`);
      s.addEventListener("click", () => speech.speak(r.feedback)); fb.appendChild(s); }
    refreshCost();
  }, { lang: "en-US", placeholder: "英語で入力" }));
}

// --- Conversation (streaming) ----------------------------------------------

export async function conversation(root) {
  const cats = await api.get("/api/categories/conversation");
  const grps = [...new Set(cats.map((c) => c.grp))];
  // 記憶した声があればそれを使う。無ければランダムで1つ選ぶ。
  const pref = speech.loadPreferredVoice();
  if (pref) speech.setVoice(pref); else speech.pickRoundVoice();
  const vlist = speech.listOpenAIVoices();
  root.innerHTML = `
    <h1>英会話</h1>
    <p class="sub">AIの声:
      <select id="voiceSel">${vlist.map((v) =>
        `<option value="${v}" ${v === speech.currentVoice() ? "selected" : ""}
          >${v}（${speech.voiceGender(v)}）</option>`).join("")}</select>
      <button class="btn ghost" id="changeVoice"
        style="padding:2px 8px">🔁 ランダム</button></p>
    ${aiBadgeNote()}
    ${state.tripPrepPersona ? `<div class="card" id="personaBanner">
      <div class="row">
        <b>🧳 出張ロールプレイ中</b>
        <span class="muted">${escapeHtml(state.tripPrepPersona)}</span>
        <button class="btn ghost" id="endPersona"
          style="padding:2px 8px">終了して通常の会話に戻る</button>
      </div>
    </div>` : ""}
    <div class="card" id="hfCard">
      <div class="row">
        <b>🎙️ ハンズフリー会話</b>
        <button class="btn good" id="hfStart">▶ 開始</button>
        <button class="btn bad" id="hfStop" style="display:none">⏹ 終了</button>
        <button class="btn" id="hfEnd" style="display:none">発話終了</button>
        <label class="toggle"><input type="checkbox" id="autoLog" />
          ✓ 自動で記録</label>
        <button class="btn ghost" id="hfSave"
          style="padding:2px 8px">📝 今すぐ記録</button>
        <span id="hfStatus" class="muted"></span>
      </div>
      <div class="row mt">
        <label>無音しきい値(秒):
          <input id="hfSil" type="number" value="2" step="0.5" min="0.5"
            style="width:64px" /></label>
        <label class="toggle"><input type="checkbox" id="hfManual" />
          発話終了ボタンで応答(手動)</label>
        <span class="muted">・20秒無音で自動終了。声の切れ目を音量で判定します。</span>
      </div>
    </div>
    <div class="card">
      <div class="row">
        <select id="mode">
          <option value="scene">🎬 シーン会話</option>
          <option value="free">💬 自由会話(なんでも相談)</option>
        </select>
        <span id="sceneSel" class="row">
          <select id="grp">${grps.map((g) =>
            `<option>${g}</option>`).join("")}</select>
          <select id="topic"></select>
        </span>
        <label class="toggle"><input type="checkbox" id="autoTts" checked />
          AI返答を読み上げ</label>
        <button class="btn secondary" id="start">AIから始める</button>
      </div>
      <div class="row mt">
        <label>🎤 認識言語:
          <select id="sttLang">
            <option value="en,ja">英語もしくは日本語</option>
            <option value="en">英語</option>
            <option value="ja">日本語</option>
            <option value="zh,en">中国語もしくは英語</option>
            <option value="zh">中国語</option>
            <option value="ko,en">韓国語もしくは英語</option>
            <option value="ko">韓国語</option>
            <option value="">自動判定(すべて)</option>
          </select></label>
        <span class="muted">音声入力(AI認識)の言語。誤認識(例: 韓国語に
          化ける)時はここを絞ると改善します。</span>
      </div>
      <p id="freeHelp" class="muted" style="display:none">
        日本語でもOK。単語・フレーズ・リスニング・ライティング、何でも相談できます。
        「録音」で話し、「わからない」で答えを教えてもらえます。</p>
      <div class="chat" id="chat"></div>
      <div id="inputArea" class="mt"></div>
    </div>`;
  root.appendChild(sampleMaterialsCard("conversation_sample",
    "💬 会話サンプルを見る", "サンプルがまだありません。"));

  const modeSel = root.querySelector("#mode");
  const sceneSel = root.querySelector("#sceneSel");
  const topicSel = root.querySelector("#topic");
  if (state.tripPrepPersona) {
    // ペルソナ指定中はシーン/自由の選択を隠す（scene()がpersonaを優先する）。
    // 「AIから始める」ボタン等、同じ行の他の操作はそのまま使える。
    modeSel.style.display = "none";
    sceneSel.style.display = "none";
    root.querySelector("#endPersona").addEventListener("click", () => {
      state.tripPrepPersona = null;
      go("conversation");
    });
  }
  const fillTopics = () => {
    const g = root.querySelector("#grp").value;
    topicSel.innerHTML = cats.filter((c) => c.grp === g)
      .map((c) => `<option>${c.name}</option>`).join("");
  };
  root.querySelector("#grp").addEventListener("change", fillTopics);
  fillTopics();
  const buildInput = () => renderInput();
  modeSel.addEventListener("change", () => {
    const free = modeSel.value === "free";
    sceneSel.style.display = free ? "none" : "";
    root.querySelector("#freeHelp").style.display = free ? "" : "none";
    buildInput();
  });

  // 声プルダウン: 選んだ声を記憶して以後の読み上げに使う。
  const voiceSel = root.querySelector("#voiceSel");
  voiceSel.addEventListener("change", () => {
    speech.setVoice(voiceSel.value);
    toast("声: " + voiceSel.value + "（" + speech.voiceGender(voiceSel.value)
      + "）");
  });
  // 🔁 ランダム: 別の声を選び、プルダウンと記憶も更新。
  root.querySelector("#changeVoice").addEventListener("click", () => {
    const v = speech.pickRoundVoice();
    if (v) { speech.setVoice(v); voiceSel.value = v; }
    toast("声: " + (v || "なし"));
  });

  // 🎤 認識言語: localStorage に記憶。既定は「英語もしくは日本語」。
  const sttLangSel = root.querySelector("#sttLang");
  sttLangSel.value = localStorage.getItem("convSttLang") ?? "en,ja";
  const sttLang = () => sttLangSel.value;
  sttLangSel.addEventListener("change", () => {
    localStorage.setItem("convSttLang", sttLangSel.value);
  });

  function scene() {
    if (state.tripPrepPersona) {
      // B16: 出張準備画面からの「困難な相手とのロールプレイ」。
      // grp/topicは表示・記録ラベル用、実際の人物像はpersonaで渡す。
      return {
        grp: "出張ロールプレイ",
        topic: state.tripPrepPersona.slice(0, 40),
        persona: state.tripPrepPersona,
      };
    }
    if (modeSel.value === "free") {
      return { grp: "自由会話", topic: "どんな話題でもOK・フリートーク" };
    }
    return { grp: root.querySelector("#grp").value, topic: topicSel.value };
  }

  const chat = root.querySelector("#chat");
  const history = [];
  const enText = (t) => englishOnly((t || "").split("【コーチ")[0]);
  // コーチの改善後の英文例（【例】以降の1文）を取り出す。
  const coachExample = (t) => {
    const i = (t || "").indexOf("【例】");
    if (i === -1) return "";
    return (t.slice(i + 3).split("\n")[0] || "").trim();
  };

  function addMsg(role, text) {
    // ラベルは吹き出しの外。本文・ツール類は bubble の中。
    const m = el(`<div class="msg ${role}">
      <div class="who">${role === "user" ? "あなた" : "AI"}</div>
      <div class="bubble"><div class="body"></div></div></div>`);
    const bubble = m.querySelector(".bubble");
    const body = m.querySelector(".body");
    body.textContent = text;
    if (role === "ai") {
      const tools = el(`<div class="row" style="margin-top:6px"></div>`);
      const jp = el(`<button class="btn secondary">🌐 日本語訳を表示</button>`);
      const say = el(`<button class="btn ghost">🔊 読み上げ</button>`);
      const sayEx = el(`<button class="btn ghost">🔊 添削例を読む</button>`);
      const tr = el(`<div class="md" style="margin-top:6px;
        border-left:3px solid var(--accent);padding-left:8px"></div>`);
      jp.addEventListener("click", async () => {
        // 英文を訳す。英語が取れなければ本文全体を訳す。
        const en = enText(body.textContent) || body.textContent;
        if (!en.trim()) return;
        tr.textContent = "翻訳中…";
        const r = await api.post("/api/learn/translate", { text: en });
        tr.innerHTML = r.ok
          ? "🌐 " + md(r.text) : escapeHtml(r.error || "翻訳失敗");
        refreshCost();
      });
      say.addEventListener("click", () =>
        speech.speak(enText(body.textContent) || body.textContent));
      sayEx.addEventListener("click", () => {
        const ex = coachExample(body.textContent);
        if (ex) speech.speak(ex); else toast("添削例がありません");
      });
      tools.append(jp, say, sayEx);
      bubble.append(tools, tr);
    }
    chat.appendChild(m); chat.scrollTop = chat.scrollHeight;
    return body;
  }

  function addHelper(label, text) {
    const m = el(`<div class="msg ai">
      <div class="who">${label}</div>
      <div class="bubble" style="background:var(--panel)">
        <div class="md"></div></div></div>`);
    m.querySelector(".md").innerHTML = md(text);
    chat.appendChild(m); chat.scrollTop = chat.scrollHeight;
  }

  // message can be a user turn, or an AI-initiated opener (kickoff=true).
  async function send(text, kickoff = false) {
    if (!kickoff) {
      if (!text.trim()) return;
      addMsg("user", text);
      history.push({ role: "user", content: text });
    }
    const s = scene();
    const body = {
      grp: s.grp, topic: s.topic, history, persona: s.persona || "",
      message: kickoff
        ? "(会話を自然に始めてください。まず1つ質問してください)" : text,
    };
    const target = addMsg("ai", kickoff ? "…" : "");
    let full = "";
    if (state.aiEnabled) {
      target.textContent = "";
      await api.stream("/api/learn/conversation/stream", body, (chunk) => {
        full += chunk; target.textContent = full;
        chat.scrollTop = chat.scrollHeight;
      });
    } else {
      full = "（AI未設定）設定でAPIキーを登録すると会話できます。";
      target.textContent = full;
    }
    history.push({ role: "assistant", content: full });
    if (root.querySelector("#autoTts").checked && state.aiEnabled) {
      // 【コーチ】以降と日本語は読み上げない（英語部分のみ）。
      speech.speak(englishOnly(full.split("【コーチ")[0]));
    }
    refreshCost();
    scheduleAutoSave();
  }

  root.querySelector("#start").addEventListener("click", () => send("", true));

  // Custom input bar: input language, record toggle, わからない, send, auto.
  const inputArea = root.querySelector("#inputArea");
  function renderInput() {
    const free = modeSel.value === "free";
    inputArea.innerHTML = "";
    const ta = el(`<textarea placeholder="${free
      ? "英語でも日本語でもOK" : "英語で話しかける"}"></textarea>`);
    const bar = el(`<div class="row mt"></div>`);
    const aiStt = speech.aiSttSupported() && state.aiEnabled;
    const langSel = el(`<select title="音声入力の言語">
      ${aiStt ? '<option value="auto">🎤 自動(AI・高精度)</option>' : ""}
      <option value="en-US">🎤 英語</option>
      <option value="ja-JP">🎤 日本語</option></select>`);
    const mic = el(`<button class="btn good">🎤 録音</button>`);
    const dk = el(`<button class="btn ghost">🤔 わからない</button>`);
    const ex = el(`<button class="btn ghost">💡 返答例</button>`);
    const sendBtn = el(`<button class="btn">✓ 送信</button>`);
    const auto = el(`<label class="toggle"><input type="checkbox" id="cAuto"
      ${speech.isVoiceAutoSubmit() ? "checked" : ""}/> 録音後に自動送信</label>`);

    sendBtn.addEventListener("click", () => {
      const t = ta.value; ta.value = ""; send(t);
    });
    dk.addEventListener("click", () => {
      send(free ? "わかりません。やさしく教えてください。"
        : "I don't know. Could you tell me the answer?");
    });
    auto.querySelector("input").addEventListener("change", (e) =>
      speech.setVoiceAutoSubmit(e.target.checked));

    let recorder = null;
    let recording = false;
    mic.addEventListener("click", async () => {
      if (!recording) {
        try {
          recorder = langSel.value === "auto"
            ? await speech.createAIRecorder(sttLang())
            : speech.createRecorder(langSel.value);
          recorder.start(); recording = true;
          mic.textContent = "⏹ 停止"; mic.classList.replace("good", "bad");
        } catch (e) { toast(e.message); }
      } else {
        recording = false; mic.disabled = true; mic.textContent = "認識中…";
        const said = await recorder.stop();
        ta.value = said;
        mic.disabled = false; mic.textContent = "🎤 録音";
        mic.classList.replace("bad", "good");
        if (said.trim() && speech.isVoiceAutoSubmit()) {
          ta.value = ""; send(said);
        }
      }
    });

    // 返答例: 直近のAI発話に対して、どう答えればよいか例を表示。
    ex.addEventListener("click", async () => {
      if (!state.aiEnabled) { toast("AI未設定です"); return; }
      toast("返答例を生成中…");
      const s = scene();
      const r = await api.post("/api/learn/reply-examples", {
        grp: s.grp, topic: s.topic, history, message: "",
      });
      if (r.ok) addHelper("💡 返答例", r.text);
      refreshCost();
    });

    bar.append(langSel, mic, dk, ex, sendBtn, auto);
    inputArea.append(ta, bar);
  }
  renderInput();

  // --- ハンズフリー会話（無音検出ベース・ロジック） ---
  // 1発話を文字起こし→AI応答→読み上げ。AI発話中は監視を止めて拾わない。
  async function handsfreeTurn(text) {
    addMsg("user", text);
    history.push({ role: "user", content: text });
    const s = scene();
    const target = addMsg("ai", "");
    let full = "";
    await api.stream("/api/learn/conversation/stream",
      { grp: s.grp, topic: s.topic, history, persona: s.persona || "",
        message: text }, (chunk) => {
        full += chunk; target.textContent = full;
        chat.scrollTop = chat.scrollHeight;
      });
    history.push({ role: "assistant", content: full });
    refreshCost();
    scheduleAutoSave();
    await speech.speakAndWait(englishOnly(full.split("【コーチ")[0]));
  }

  // --- 会話の自動記録 -------------------------------------------------------
  // ✓「自動で記録」をONにすると、ターンごとに学習履歴へ自動保存する(同じ
  // session_key で上書きするので行は増えない)。直近の会話はそのまま、古い
  // 部分は要約して保存。音声は保存しない(テキストのみ)。
  const KEEP_RECENT = 8;        // 直近この数の発言はそのまま記録
  const RESUMMARIZE_EVERY = 6;  // 古い部分がこの数増えたら要約し直す
  const recKey = "conv-" + Date.now() + "-"
    + Math.random().toString(36).slice(2, 8);
  let archivedSummary = "";     // 古い部分の要約(キャッシュ)
  let archivedCount = 0;        // 要約に畳み込み済みの history 件数
  let saveTimer = null;
  let saving = false;
  let lastSavedLen = 0;         // 最後に保存した時点の history 件数
  let finalLogged = false;      // study_log.md へ確定追記したか

  // 記録用に1発言を整形(AI側は英語のみ・コーチ注記は落とす)。
  const lineFor = (m) => {
    const t = m.role === "assistant"
      ? (enText(m.content) || m.content) : m.content;
    return (m.role === "user" ? "あなた" : "AI") + ": " + (t || "").trim();
  };

  async function buildRecordContent() {
    const total = history.length;
    const oldEnd = Math.max(0, total - KEEP_RECENT);
    // 古い部分が十分増えたら、まとめて要約に畳み込む(古い=要約)。
    if (state.aiEnabled && oldEnd - archivedCount >= RESUMMARIZE_EVERY) {
      const older = history.slice(0, oldEnd).map(lineFor).join("\n");
      try {
        const r = await api.post("/api/learn/summarize", { text: older });
        if (r.ok && r.summary) {
          archivedSummary = r.summary; archivedCount = oldEnd;
        }
      } catch (e) { /* 失敗時はそのまま直近側に全文を残す */ }
    }
    // 直近(=まだ要約していない分)はそのまま記録。
    const recent = history.slice(archivedCount).map(lineFor).join("\n");
    let out = "🗣️ 英会話の記録";
    const s = scene();
    if (s.topic) out += "（" + s.grp + " / " + s.topic + "）";
    if (archivedSummary) {
      out += "\n\n## これまでの要約\n" + archivedSummary;
    }
    out += "\n\n## 直近の会話（そのまま）\n" + recent;
    return out;
  }

  async function doSave(final) {
    if (saving || !history.length) return;
    if (!final && history.length === lastSavedLen) return;
    saving = true;
    try {
      const content = await buildRecordContent();
      await api.post("/api/learn/session/save", {
        content, accuracy: null, weak_points: "", next_topic: "",
        new_words: "", session_key: recKey, final: !!final,
      });
      lastSavedLen = history.length;
      if (final) finalLogged = true;
    } catch (e) { /* ignore */ }
    finally { saving = false; refreshCost(); }
  }

  const autoLogOn = () => root.querySelector("#autoLog").checked;
  // ターン完了時に呼ぶ。ONなら少し待ってから自動保存(連打を抑制)。
  function scheduleAutoSave() {
    if (!autoLogOn()) return;
    if (saveTimer) clearTimeout(saveTimer);
    saveTimer = setTimeout(() => { saveTimer = null; doSave(false); }, 4000);
  }

  // タブを閉じる等で離脱するとき、未保存分をベストエフォートで送る。
  const beforeUnload = () => {
    if (!autoLogOn() || history.length === lastSavedLen) return;
    const recent = history.slice(archivedCount).map(lineFor).join("\n");
    let content = "🗣️ 英会話の記録";
    if (archivedSummary) content += "\n\n## これまでの要約\n" + archivedSummary;
    content += "\n\n## 直近の会話（そのまま）\n" + recent;
    try {
      const blob = new Blob([JSON.stringify({
        content, accuracy: null, weak_points: "", next_topic: "",
        new_words: "", session_key: recKey, final: true,
      })], { type: "application/json" });
      navigator.sendBeacon("/api/learn/session/save", blob);
    } catch (e) { /* ignore */ }
  };
  window.addEventListener("beforeunload", beforeUnload);

  // 画面を離れたら確定保存(study_log.md へ1度だけ追記)。
  onLeaveView(() => {
    window.removeEventListener("beforeunload", beforeUnload);
    if (saveTimer) { clearTimeout(saveTimer); saveTimer = null; }
    if (autoLogOn() && history.length && !finalLogged) doSave(true);
  });

  // ✓「自動で記録」: 状態を localStorage に保存。ONにした時点で一度保存。
  const autoLogCb = root.querySelector("#autoLog");
  autoLogCb.checked = localStorage.getItem("convAutoLog") === "1";
  autoLogCb.addEventListener("change", () => {
    localStorage.setItem("convAutoLog", autoLogCb.checked ? "1" : "0");
    if (autoLogCb.checked) { toast("自動で記録します"); doSave(false); }
  });

  let hf = null;
  const hfStatus = root.querySelector("#hfStatus");
  const hfStart = root.querySelector("#hfStart");
  const hfStop = root.querySelector("#hfStop");
  const hfEnd = root.querySelector("#hfEnd");
  const setHfStatus = (t) => { hfStatus.textContent = t; };
  const stopHF = () => {
    if (hf) { hf.stop(); hf = null; }
    hfStart.style.display = ""; hfStop.style.display = "none";
    hfEnd.style.display = "none";
  };
  hfStart.addEventListener("click", async () => {
    if (!state.aiEnabled) { toast("AI未設定です"); return; }
    if (!speech.vadSupported()) {
      toast("このブラウザはハンズフリーに未対応です"); return;
    }
    const sil = Math.max(0.5,
      parseFloat(root.querySelector("#hfSil").value) || 2) * 1000;
    const manual = root.querySelector("#hfManual").checked;
    try {
      hf = await speech.createVADSession({
        baseSilenceMs: sil, noSpeechEndMs: 20000, manual,
        onSpeechStart: () => setHfStatus("🎤 聞き取り中…"),
        onUtterance: async (blob) => {
          if (!hf) return;
          hf.pause(); setHfStatus("認識中…");
          const text = await speech.transcribeBlob(blob, sttLang());
          if (!text.trim()) {
            if (hf) { hf.resume(); setHfStatus("🎤 どうぞ話してください"); }
            return;
          }
          setHfStatus("AI応答中…");
          await handsfreeTurn(text);
          if (hf && hf.isRunning()) {
            hf.resume(); setHfStatus("🎤 どうぞ話してください");
          }
        },
        onNoSpeechEnd: () => {
          setHfStatus("20秒無音で自動終了しました"); stopHF();
        },
      });
      await hf.start();
      hfStart.style.display = "none"; hfStop.style.display = "";
      hfEnd.style.display = manual ? "" : "none";
      setHfStatus("🎤 どうぞ話してください");
    } catch (e) { toast(e.message || "マイクを利用できません"); }
  });
  hfStop.addEventListener("click", () => {
    stopHF(); setHfStatus("終了しました");
  });
  hfEnd.addEventListener("click", () => { if (hf) hf.forceEnd(); });
  // 📝 今すぐ記録: その場で確定保存(直近そのまま＋古い部分は要約)。
  root.querySelector("#hfSave").addEventListener("click", async () => {
    if (!history.length) { toast("まだ会話がありません"); return; }
    setHfStatus("要点をまとめています…");
    await doSave(true);
    setHfStatus("会話を記録しました（学習履歴に保存）");
    toast("会話を記録しました");
  });
}

// --- Listening --------------------------------------------------------------

export async function listening(root) {
  const topics = await api.get("/api/listening");
  root.innerHTML = `
    <h1>リスニング</h1>
    <p class="sub">スクリプトを生成して読み上げ、理解度を記録します。</p>
    ${aiBadgeNote()}
    <div class="card">
      <div class="row">
        <select id="topic">${topics.map((t) =>
          `<option value="${t.id}">${t.source} / ${t.accent} (理解度${t.comprehension})</option>`
        ).join("")}</select>
        <select id="genre" title="題材ジャンル">
          <option value="">（題材: トピックのまま）</option>
          <option value="lit_uk">文学（英文学）</option>
          <option value="lit_us">文学（米国文学）</option>
          <option value="lit_rand">文学（ランダム）</option>
          <option value="news">ニュース風</option>
          <option value="business">ビジネス</option>
        </select>
        <input id="theme" placeholder="テーマ(任意)" style="width:120px" />
        ${diffSelect("ldiff")}
        ${lengthSelect("llen")}
        <label class="toggle">速度
          <input type="range" id="rate" min="0.6" max="1.2" step="0.05" value="0.95" />
        </label>
        <label class="toggle" title="内容理解問題を表示(常に生成・保存)">
          <input type="checkbox" id="showQ" checked /> 内容理解問題</label>
        <button class="btn" id="gen" ${state.aiEnabled ? "" : "disabled"}>
          スクリプト生成</button>
        <button class="btn ghost" id="histBtn">📚 履歴</button>
      </div>
      <div class="row mt" style="border-top:1px solid var(--panel-2);
        padding-top:8px">
        <b>🎧 聞き流し</b>
        <button class="btn secondary" id="plStart">▶ 開始(約2分)</button>
        <button class="btn bad" id="plStop" style="display:none">⏹ 停止</button>
        <label class="toggle"><input type="checkbox" id="plEn" checked />
          英文表示</label>
        <label class="toggle"><input type="checkbox" id="plJa" checked />
          日本語訳</label>
        <label class="toggle"><input type="checkbox" id="plLoop" />
          繰り返し</label>
        <span id="plStatus" class="muted"></span>
      </div>
      <div id="plBox" class="mt" style="display:none"></div>
      <div id="histPanel" class="mt" style="display:none"></div>
      <div id="out" class="md mt"></div>
      <div class="row mt">
        <label class="toggle">理解度
          <input type="range" id="comp" min="0" max="100" value="50" /></label>
        <input id="weak" placeholder="苦手だった点" style="width:240px" />
        <button class="btn good" id="save">記録</button>
      </div>
    </div>`;
  root.appendChild(sampleMaterialsCard("listening",
    "🎧 サンプルを見る", "サンプルがまだありません。"));
  let scriptText = "";
  // 内容理解問題トグル＋読み上げは英語のみ(englishOnly)で統一。
  const lDisp = (b) =>
    root.querySelector("#showQ").checked ? b : stripQuestions(b);
  const lSpeak = (b) => speech.speak(englishOnly(lDisp(b)),
    { rate: parseFloat(root.querySelector("#rate").value),
      feature: "listening_tts" });
  {
    const panel = root.querySelector("#histPanel");
    const showInto = (body) => {
      scriptText = body;
      const out = root.querySelector("#out");
      out.innerHTML = md(lDisp(body));
      const play = el(`<button class="btn mt">🔊 再生</button>`);
      play.addEventListener("click", () => lSpeak(body));
      out.appendChild(play);
    };
    root.querySelector("#histBtn").addEventListener("click", () => {
      if (panel.style.display === "none") {
        panel.style.display = "";
        renderHistory(panel, "listening", showInto);
      } else { panel.style.display = "none"; }
    });
  }
  root.querySelector("#gen").addEventListener("click", async () => {
    const sel = root.querySelector("#topic");
    const label = sel.options[sel.selectedIndex].textContent;
    const out = root.querySelector("#out"); out.textContent = "生成中…";
    const theme = root.querySelector("#theme").value.trim();
    const genre = root.querySelector("#genre").value;
    // 文学などのジャンルは適切な area/field・指示に振り分け。
    const GENRES = {
      lit_uk: { area: "literature", field: "英文学",
        inst: "英文学の有名作品(著作権切れ)風の朗読スクリプト" },
      lit_us: { area: "literature", field: "米国文学",
        inst: "アメリカ文学(著作権切れ)風の朗読スクリプト" },
      lit_rand: { area: "literature", field: "文学(ランダム)",
        inst: "古典文学からランダムに題材を選んだ朗読スクリプト" },
      news: { area: "news", field: "ニュース風",
        inst: "ニュース風のオリジナル原稿(創作・実在の記事を使わない)" },
      business: { area: "listening", field: "ビジネス",
        inst: "ビジネスシーンの会話形式スクリプト" },
    };
    const g = GENRES[genre];
    const len = LENGTH_INSTR[root.querySelector("#llen").value] || "";
    const lenNote = len ? ` 本文は${len}。` : "";
    const diff = root.querySelector("#ldiff").value;
    let body;
    if (g) {
      body = {
        area: g.area, field: theme ? `${g.field}・${theme}` : g.field,
        instruction: g.inst + (theme ? `（テーマ: ${theme}）` : "") + lenNote,
      };
    } else {
      body = {
        area: "listening", field: theme ? `${label}・${theme}` : label,
        instruction: "会話形式のスクリプト" +
          (theme ? `（テーマ: ${theme}）` : "") + lenNote,
      };
    }
    body.difficulty = diff;
    const r = await api.post("/api/learn/generate", body);
    if (!r.ok) { out.textContent = r.error; return; }
    scriptText = r.body; out.innerHTML = md(lDisp(r.body));
    const play = el(`<button class="btn mt">🔊 再生</button>`);
    play.addEventListener("click", () => lSpeak(scriptText));
    out.appendChild(play);
    refreshCost();
  });
  root.querySelector("#save").addEventListener("click", async () => {
    await api.post("/api/listening/study", {
      topic_id: parseInt(root.querySelector("#topic").value),
      comprehension: parseInt(root.querySelector("#comp").value),
      weak_areas: root.querySelector("#weak").value,
    });
    toast("記録しました"); go("listening");
  });

  // --- 🎧 聞き流しモード (§D3) ------------------------------------------------
  // 生成済みスクリプト(無ければ約2分ぶんを生成)を文単位で連続再生。再生中の文を
  // ハイライト(文単位カラオケ=Whisper不要で確実)。英文/日本語訳の表示はトグル。
  // 日本語は英文の直後に交互表示(英→日→次の英)。音声は英語のみ読み上げる。
  const plBox = root.querySelector("#plBox");
  const plStart = root.querySelector("#plStart");
  const plStop = root.querySelector("#plStop");
  const plStatus = root.querySelector("#plStatus");
  let plRunning = false;
  const jaCache = new Map();  // 英文 → 日本語訳(使い回し)

  // 英文を文に分割(英語のみ抽出→. ! ? で区切り)。
  const splitSentences = (text) => englishOnly(stripQuestions(text))
    .split(/(?<=[.!?])\s+/)
    .map((s) => s.trim())
    .filter((s) => (s.match(/[A-Za-z]/g) || []).length >= 3);

  async function ensureScript() {
    if (scriptText && splitSentences(scriptText).length) return scriptText;
    if (!state.aiEnabled) { toast("AI未設定です"); return ""; }
    plStatus.textContent = "約2分ぶんを生成中…";
    const sel = root.querySelector("#topic");
    const label = sel.options[sel.selectedIndex].textContent;
    const theme = root.querySelector("#theme").value.trim();
    const r = await api.post("/api/learn/generate", {
      area: "listening",
      field: theme ? `${label}・${theme}` : label,
      instruction: "会話形式のスクリプト" +
        (theme ? `（テーマ: ${theme}）` : "") +
        ` 本文は${LENGTH_INSTR["5"]}。`,
      difficulty: root.querySelector("#ldiff").value,
    });
    refreshCost();
    if (!r.ok) { toast(r.error || "生成失敗"); return ""; }
    scriptText = r.body;
    return scriptText;
  }

  async function jaFor(sentence) {
    if (jaCache.has(sentence)) return jaCache.get(sentence);
    try {
      const r = await api.post("/api/learn/translate", { text: sentence });
      const t = r.ok ? r.text : "";
      jaCache.set(sentence, t); refreshCost();
      return t;
    } catch (e) { return ""; }
  }

  const stopPL = () => {
    plRunning = false; speech.stopSpeaking();
    plStart.style.display = ""; plStop.style.display = "none";
  };

  async function runPassive() {
    const text = await ensureScript();
    if (!text) { stopPL(); return; }
    const sents = splitSentences(text);
    if (!sents.length) { toast("読み上げる英文がありません"); stopPL(); return; }
    const showEn = () => root.querySelector("#plEn").checked;
    const showJa = () => root.querySelector("#plJa").checked;
    const rate = () => parseFloat(root.querySelector("#rate").value) || 0.95;
    // セグメントを並べて描画(本文はハイライト用に span 化)。
    plBox.style.display = "";
    plBox.innerHTML = "";
    const segEls = sents.map((s, i) => {
      const seg = el(`<div class="pl-seg">
        <div class="pl-en"></div><div class="pl-ja muted"></div></div>`);
      seg.querySelector(".pl-en").textContent = s;
      segEls_set(seg, showEn(), showJa());
      plBox.appendChild(seg);
      return seg;
    });
    function segEls_set(seg, en, ja) {
      seg.querySelector(".pl-en").style.display = en ? "" : "none";
      seg.querySelector(".pl-ja").style.display = ja ? "" : "none";
    }
    // トグル変更を即時反映。
    const applyToggles = () => segEls.forEach((seg) =>
      segEls_set(seg, showEn(), showJa()));
    root.querySelector("#plEn").onchange = applyToggles;
    root.querySelector("#plJa").onchange = applyToggles;

    do {
      for (let i = 0; i < sents.length; i++) {
        if (!plRunning) return;
        const seg = segEls[i];
        segEls.forEach((s) => s.classList.remove("active"));
        seg.classList.add("active");
        seg.scrollIntoView({ block: "nearest", behavior: "smooth" });
        plStatus.textContent = `再生中 ${i + 1}/${sents.length}`;
        // 日本語訳トグルがONなら、その文の訳を直後に出す(英→日)。
        if (showJa()) {
          const jaEl = seg.querySelector(".pl-ja");
          if (!jaEl.textContent) jaEl.textContent = "訳: " +
            (await jaFor(sents[i]) || "—");
        }
        if (!plRunning) return;
        await speech.speakAndWait(sents[i],
          { rate: rate(), feature: "listening_tts" });
      }
    } while (plRunning && root.querySelector("#plLoop").checked);
    if (plRunning) { plStatus.textContent = "完了"; stopPL(); }
  }

  plStart.addEventListener("click", async () => {
    if (plRunning) return;
    plRunning = true;
    plStart.style.display = "none"; plStop.style.display = "";
    await runPassive();
  });
  plStop.addEventListener("click", () => {
    stopPL(); plStatus.textContent = "停止しました";
  });
  // 画面を離れたら聞き流しを止める(go() も stopSpeaking するが、ループ継続を防ぐ)。
  onLeaveView(() => { plRunning = false; });
}

// --- Assessment + material generation --------------------------------------

// --- B16: 出張・旅行準備（状況入力型パーソナライズ生成） ------------------

function renderTripPrepData(panel, data) {
  panel.innerHTML = "";
  if (!data || typeof data !== "object") {
    panel.appendChild(el(`<p class="muted">表示できる内容がありません。</p>`));
    return;
  }
  if (Array.isArray(data.checklist) && data.checklist.length) {
    const card = el(`<div class="card"><h3>✅ チェックリスト</h3></div>`);
    const ul = el(`<ul></ul>`);
    data.checklist.forEach((item) => {
      ul.appendChild(el(`<li><label><input type="checkbox" /> `
        + `${escapeHtml(String(item))}</label></li>`));
    });
    card.appendChild(ul);
    panel.appendChild(card);
  }
  if (Array.isArray(data.vocabulary) && data.vocabulary.length) {
    const card = el(`<div class="card"><h3>🔤 必要語彙</h3></div>`);
    const list = el(`<div></div>`);
    data.vocabulary.forEach((v) => {
      list.appendChild(el(`<div class="row mt"><b>`
        + `${escapeHtml(v.en || "")}</b><span class="muted">`
        + `${escapeHtml(v.ja || "")}</span></div>`));
    });
    card.appendChild(list);
    card.appendChild(
      readAloudBar(() => data.vocabulary.map((v) => v.en).join(". ")));
    panel.appendChild(card);
  }
  if (Array.isArray(data.cheat_sheet) && data.cheat_sheet.length) {
    const card = el(`<div class="card"><h3>📝 当日用カンペ</h3></div>`);
    const ul = el(`<ul></ul>`);
    data.cheat_sheet.forEach((item) =>
      ul.appendChild(el(`<li>${escapeHtml(String(item))}</li>`)));
    card.appendChild(ul);
    card.appendChild(readAloudBar(() => data.cheat_sheet.join(". ")));
    panel.appendChild(card);
  }
  if (Array.isArray(data.questions) && data.questions.length) {
    const card = el(`<div class="card"><h3>❓ 質問一覧</h3></div>`);
    const ul = el(`<ul></ul>`);
    data.questions.forEach((item) =>
      ul.appendChild(el(`<li>${escapeHtml(String(item))}</li>`)));
    card.appendChild(ul);
    panel.appendChild(card);
  }
  if (Array.isArray(data.sample_conversation)
      && data.sample_conversation.length) {
    const card = el(`<div class="card"><h3>💬 想定会話</h3></div>`);
    const chat = el(`<div class="chat"></div>`);
    data.sample_conversation.forEach((turn) => {
      const you = String(turn.speaker || "").toLowerCase().startsWith("you");
      const m = el(`<div class="msg ${you ? "user" : "ai"}">`
        + `<div class="who">${escapeHtml(turn.speaker || "")}</div>`
        + `<div class="bubble"><div class="body"></div>`
        + `<div class="muted" style="font-size:12px"></div></div></div>`);
      m.querySelector(".body").textContent = turn.en || "";
      m.querySelector(".muted").textContent = turn.ja || "";
      chat.appendChild(m);
    });
    card.appendChild(chat);
    card.appendChild(readAloudBar(
      () => data.sample_conversation.map((t) => t.en).join(". ")));
    panel.appendChild(card);
  }
  if (data.follow_up_email
      && (data.follow_up_email.subject || data.follow_up_email.body)) {
    const card = el(`<div class="card"><h3>✉️ フォローメール</h3></div>`);
    const subj = el(`<p><b>件名:</b> `
      + `${escapeHtml(data.follow_up_email.subject || "")}</p>`);
    const body = el(`<textarea style="min-height:140px"></textarea>`);
    body.value = data.follow_up_email.body || "";
    card.append(subj, body);
    panel.appendChild(card);
  }
}

export async function tripPrep(root) {
  root.innerHTML = `
    <h1>🧳 出張・旅行準備</h1>
    <p class="sub">渡航先や状況を入力すると、AIがチェックリスト・語彙・
      想定会話などを一括で作成します。</p>
    ${aiBadgeNote()}
    <div class="card">
      <div class="row"><label class="toggle" style="width:110px">渡航先
        <span style="color:#c00">*</span></label>
        <input id="tp_dest" placeholder="例: ドイツ・シュツットガルト"
          style="width:260px" /></div>
      <div class="row mt"><label class="toggle" style="width:110px">日程</label>
        <input id="tp_dates" placeholder="例: 2026-09-01〜09-05"
          style="width:260px" /></div>
      <div class="row mt"><label class="toggle" style="width:110px">訪問目的</label>
        <input id="tp_purpose" placeholder="例: 装置の立上げ・現地デバッグ"
          style="width:340px" /></div>
      <div class="row mt"><label class="toggle" style="width:110px">訪問先URL</label>
        <input id="tp_url" placeholder="任意・参考として渡すのみ(取得はしません)"
          style="width:340px" /></div>
      <div class="row mt"><label class="toggle" style="width:110px">自分の役割</label>
        <input id="tp_role" placeholder="例: 品質保証エンジニア"
          style="width:260px" /></div>
      <div class="row mt"><label class="toggle" style="width:110px">会う相手</label>
        <input id="tp_counterpart" placeholder="例: 現地工場の品質責任者"
          style="width:260px" /></div>
      <div class="row mt"><label class="toggle" style="width:110px">心配なこと</label>
        <input id="tp_concerns"
          placeholder="例: 原因を断定した根拠を聞き返せるか不安"
          style="width:340px" /></div>
      <div class="row mt"><label class="toggle" style="width:110px">英語レベル</label>
        <input id="tp_level" placeholder="例: TOEIC 600程度"
          style="width:200px" /></div>
      <div class="row mt"><label class="toggle" style="width:110px">
        自社資料等</label></div>
      <textarea id="tp_materials"
        placeholder="製品概要や資料の抜粋(任意・そのままプロンプトに渡ります)"
        style="min-height:80px"></textarea>
      <div class="row mt">
        <button class="btn good" id="tp_gen">生成する</button>
        <span id="tp_status" class="muted"></span>
      </div>
    </div>
    <div id="tp_result"></div>
    <h2 class="mt">履歴</h2>
    <div id="tp_hist"></div>`;

  // 前回入力の復元（user_settings.trip_prep_last）。
  try {
    const s = (await api.get("/api/system/user-settings")).settings || {};
    const last = s.trip_prep_last;
    if (last) {
      const set = (sel, v) => {
        const e = root.querySelector(sel);
        if (e && v) e.value = v;
      };
      set("#tp_dest", last.destination);
      set("#tp_dates", last.dates);
      set("#tp_purpose", last.purpose);
      set("#tp_url", last.destination_url);
      set("#tp_role", last.role);
      set("#tp_counterpart", last.counterpart);
      set("#tp_concerns", last.concerns);
      set("#tp_level", last.english_level);
      set("#tp_materials", last.own_materials);
    }
  } catch (_) { /* 初回は設定が無いので無視 */ }

  const resultPanel = root.querySelector("#tp_result");
  let lastForm = null;

  function showInto(body) {
    let data = null;
    try { data = JSON.parse(body); } catch (_) { data = null; }
    if (!data) {
      resultPanel.innerHTML =
        `<p class="muted">この履歴は表示できませんでした。</p>`;
      return;
    }
    renderTripPrepData(resultPanel, data);
    const rp = el(`<div class="row mt"></div>`);
    const startBtn = el(
      `<button class="btn secondary">🎭 この内容でロールプレイを始める`
      + `</button>`);
    startBtn.addEventListener("click", () => {
      const role = (lastForm && lastForm.role) || "出張者";
      const counterpart = (lastForm && lastForm.counterpart) || "相手役";
      const concerns = (lastForm && lastForm.concerns) || "特になし";
      state.tripPrepPersona =
        `${counterpart}（相手はこの状況で対応する人物として振る舞う。`
        + `ユーザーの役割: ${role}。ユーザーの懸念点: ${concerns}）`;
      go("conversation");
    });
    rp.appendChild(startBtn);
    resultPanel.appendChild(rp);
  }

  const histPanel = root.querySelector("#tp_hist");

  root.querySelector("#tp_gen").addEventListener("click", async () => {
    if (!state.aiEnabled) { toast("AI未設定です"); return; }
    const dest = root.querySelector("#tp_dest").value.trim();
    if (!dest) { toast("渡航先を入力してください"); return; }
    const form = {
      destination: dest,
      dates: root.querySelector("#tp_dates").value.trim(),
      purpose: root.querySelector("#tp_purpose").value.trim(),
      destination_url: root.querySelector("#tp_url").value.trim(),
      role: root.querySelector("#tp_role").value.trim(),
      counterpart: root.querySelector("#tp_counterpart").value.trim(),
      concerns: root.querySelector("#tp_concerns").value.trim(),
      own_materials: root.querySelector("#tp_materials").value.trim(),
      english_level: root.querySelector("#tp_level").value.trim(),
    };
    const status = root.querySelector("#tp_status");
    status.textContent = "生成中…(数十秒かかることがあります)";
    try {
      const r = await api.post("/api/learn/trip-prep", form);
      if (!r.ok) { status.textContent = "失敗: " + r.error; return; }
      status.textContent = "";
      lastForm = form;
      showInto(JSON.stringify(r.data));
      renderHistory(histPanel, "trip_prep", showInto);
      refreshCost();
    } catch (e) { status.textContent = "失敗: " + e.message; }
  });

  renderHistory(histPanel, "trip_prep", showInto);
}

export async function assess(root) {
  const p = await api.get("/api/system/progress");
  const w = p.words;
  root.innerHTML = `
    <h1>判定・教材作成</h1>
    <p class="sub">好きなタイミングで実力を判定し、苦手に合わせて教材を追加できます。</p>

    <div class="card">
      <h2>🎯 レベル判定</h2>
      <div class="grid cols-3">
        <div class="stat"><div class="num">${
          p.toeic_estimate == null ? "未判定" : p.toeic_estimate}</div>
          <div class="lbl">TOEIC換算(目安)</div></div>
        <div class="stat"><div class="num">${w.studied}</div>
          <div class="lbl">学習済み単語</div></div>
        <div class="stat"><div class="num">${w.mastered}</div>
          <div class="lbl">習得(80+)</div></div>
      </div>
      ${aiBadgeNote()}
      <div class="row mt">
        <button class="btn" id="run" ${state.aiEnabled ? "" : "disabled"}>
          AIで判定実施</button>
        <button class="btn secondary" id="saveMem" style="display:none">
          判定をmemoryに保存</button>
      </div>
      <div id="out" class="md mt"></div>
    </div>

    <div class="card">
      <h2>📚 追加教材を作成</h2>
      <p class="muted">AIが今のレベル・苦手に合わせて単語/フレーズを生成し、
        そのままDBに追加します（重複は自動でスキップ）。</p>
      <div class="row">
        <select id="kind">
          <option value="word">英単語</option>
          <option value="phrase">フレーズ</option>
        </select>
        <select id="count">
          <option>10</option><option>20</option><option>30</option>
        </select>
        <input id="focus" placeholder="テーマ・苦手分野(任意 例: IT会議, 旅行)"
          style="width:300px" />
        <button class="btn good" id="gen" ${state.aiEnabled ? "" : "disabled"}>
          生成して追加</button>
      </div>
      <div id="genOut" class="md mt"></div>
    </div>`;

  let lastAssessment = "";
  root.querySelector("#run").addEventListener("click", async () => {
    const out = root.querySelector("#out");
    out.textContent = "判定中…（品質モデルを使用）";
    const r = await api.get("/api/learn/assess");
    if (!r.ok) { out.textContent = r.error || "判定できませんでした"; refreshCost(); return; }
    lastAssessment = r.assessment;
    out.innerHTML = md(r.assessment) +
      `<p class="muted">使用モデル: ${r.model || "-"} / 学習済み ${r.studied_words}語</p>`;
    root.querySelector("#saveMem").style.display = "";
    refreshCost();
  });

  root.querySelector("#saveMem").addEventListener("click", async () => {
    const cur = (await api.get("/api/system/memory")).content;
    const stamp = "\n\n## AI判定メモ\n" + lastAssessment + "\n";
    await api.put("/api/system/memory", { content: cur + stamp });
    toast("memory.md に保存しました");
  });

  root.querySelector("#gen").addEventListener("click", async () => {
    const out = root.querySelector("#genOut");
    out.textContent = "生成中…（品質モデルを使用）";
    const r = await api.post("/api/learn/generate-items", {
      kind: root.querySelector("#kind").value,
      count: parseInt(root.querySelector("#count").value),
      focus: root.querySelector("#focus").value,
    });
    if (!r.ok) { out.textContent = r.error || "生成失敗"; refreshCost(); return; }
    const list = r.added.map((x) =>
      `- ${escapeHtml(x.english)} — ${escapeHtml(x.japanese)}`).join("\n");
    out.innerHTML = md(
      `**${r.added.length}件 追加**（重複スキップ ${r.skipped}件 / モデル ${r.model}）\n\n`
      + (list || "（追加なし）"));
    refreshCost();
  });
}

// --- History (study log + memory + session end) ----------------------------

export async function history(root) {
  const log = await api.get("/api/system/study-log");
  const mem = await api.get("/api/system/memory");
  root.innerHTML = `
    <h1>学習履歴</h1>
    <p class="sub">学習の記録・メモリ・セッション終了処理。</p>
    <div class="card">
      <h2>セッション終了 → 記録</h2>
      <div class="grid cols-2">
        <textarea id="content" placeholder="今日学んだ内容"></textarea>
        <textarea id="weak" placeholder="苦手だった点"></textarea>
      </div>
      <div class="row mt">
        <input id="acc" type="number" min="0" max="100" placeholder="正答率%" style="width:120px" />
        <input id="next" placeholder="次回の課題" style="width:240px" />
        <input id="neww" placeholder="新出単語(カンマ区切り)" style="width:240px" />
      </div>
      <div class="row mt">
        <button class="btn" id="summary" ${state.aiEnabled ? "" : "disabled"}>
          AIに要約してもらう</button>
        <button class="btn good" id="save">記録を保存</button>
      </div>
      <div id="sumOut" class="md mt"></div>
    </div>
    <div class="card">
      <h2>学習プロフィール（AIが参考にします）</h2>
      <p class="muted">記入すると会話・教材作成でAIが考慮します。空欄でOK。</p>
      <label class="toggle">学習方針</label>
      <textarea id="mem_policy"
        placeholder="例: 英会話とリスニングを重点的に"></textarea>
      <label class="toggle mt">目標</label>
      <textarea id="mem_goal"
        placeholder="例: 半年でTOEIC700点"></textarea>
      <label class="toggle mt">苦手分野</label>
      <textarea id="mem_weak"
        placeholder="例: 長文読解、前置詞の使い分け"></textarea>
      <label class="toggle mt">学習の傾向・自由メモ</label>
      <textarea id="mem_note"
        placeholder="その他、AIに伝えたいこと"></textarea>
      <button class="btn good mt" id="saveMem">プロフィールを保存</button>
    </div>
    <div class="card">
      <h2>学習ログ（自動記録）</h2>
      <div class="md" style="max-height:320px;overflow:auto">${md(log.content)}</div>
    </div>`;

  // memory.md(セクション形式) ⇄ 入力欄 の相互変換。
  const MEM_MAP = [["学習方針", "mem_policy"], ["目標", "mem_goal"],
    ["苦手分野", "mem_weak"], ["学習傾向", "mem_note"]];
  const parseMem = (text) => {
    const out = {}; let cur = null;
    (text || "").split("\n").forEach((line) => {
      const m = line.match(/^##\s*(.+?)\s*$/);
      if (m) { cur = m[1]; out[cur] = out[cur] || ""; return; }
      if (line.startsWith("# ")) { cur = null; return; }
      if (cur != null) out[cur] = (out[cur] ? out[cur] + "\n" : "") + line;
    });
    return out;
  };
  const buildMem = () => {
    let s = "# 学習メモリ (memory.md)\n";
    for (const [title, id] of MEM_MAP) {
      const v = (root.querySelector("#" + id).value || "").trim();
      s += `\n## ${title}\n${v}\n`;
    }
    return s;
  };
  const parsed = parseMem(mem.content);
  for (const [title, id] of MEM_MAP) {
    root.querySelector("#" + id).value = (parsed[title] || "").trim();
  }

  const payload = () => ({
    content: root.querySelector("#content").value,
    accuracy: root.querySelector("#acc").value
      ? parseInt(root.querySelector("#acc").value) : null,
    weak_points: root.querySelector("#weak").value,
    next_topic: root.querySelector("#next").value,
    new_words: root.querySelector("#neww").value,
  });

  root.querySelector("#summary").addEventListener("click", async () => {
    const out = root.querySelector("#sumOut"); out.textContent = "要約中…";
    const r = await api.post("/api/learn/session/summary", payload());
    out.innerHTML = r.ok ? md(r.summary) : escapeHtml(r.error);
    refreshCost();
  });
  root.querySelector("#save").addEventListener("click", async () => {
    await api.post("/api/learn/session/save", payload());
    toast("学習履歴に保存しました"); go("history");
  });
  root.querySelector("#saveMem").addEventListener("click", async () => {
    await api.put("/api/system/memory", { content: buildMem() });
    toast("プロフィールを保存しました");
  });
}

// --- 管理者ダッシュボード（管理者のみ）---------------------------------------
export async function admin(root) {
  let d;
  try {
    d = await api.get("/api/system/admin/overview");
  } catch (e) {
    root.innerHTML = `<h1>管理者情報</h1>
      <p class="muted">管理者のみ閲覧できます（${escapeHtml(e.message)}）。</p>`;
    return;
  }
  let inquiries = [];
  try { inquiries = (await api.get("/api/inquiries")).inquiries || []; }
  catch (_) { /* */ }
  const sec = d.security || {};
  const fmtDate = (s) => s ? s.replace("T", " ").slice(0, 16) : "—";
  const rows = d.users.map((u) => {
    const flags = [];
    if (!u.is_active) flags.push('<span class="badge-off">無効</span>');
    if (u.balance_empty) flags.push('<span class="badge-bad">残高切れ</span>');
    if (u.over_daily) flags.push('<span class="badge-bad">日上限</span>');
    if (u.over_monthly) flags.push('<span class="badge-bad">月上限</span>');
    if (u.allow_banned) flags.push('<span class="badge-warn">禁止可</span>');
    if (u.distinct_ips_30d >= 3) {
      flags.push(`<span class="badge-warn" title="直近30日のAI利用IP数">
        IP${u.distinct_ips_30d}種</span>`);
    }
    const bal = u.balance_jpy == null ? "—" : "¥" + Math.round(u.balance_jpy);
    const dcap = u.daily_cap_jpy ? "¥" + u.daily_cap_jpy : "—";
    const mcap = u.monthly_cap_jpy ? "¥" + u.monthly_cap_jpy : "—";
    return `<tr>
      <td>${escapeHtml(u.display_name || u.username)}<br>
        <span class="muted">${escapeHtml(u.username)}</span></td>
      <td>${u.role}</td>
      <td>¥${u.today_jpy} / ${dcap}</td>
      <td>¥${u.month_jpy} / ${mcap}</td>
      <td>${bal}</td>
      <td><input type="number" class="chg-amt" data-uid="${u.id}"
        value="1000" min="1" max="1000" step="100" style="width:74px" />
        <button class="btn good chg-btn" data-uid="${u.id}"
        style="padding:3px 8px">＋</button></td>
      <td>${u.calls}</td>
      <td>${fmtDate(u.last_used)}</td>
      <td>${u.word_quizzes}</td>
      <td>${u.phrase_quizzes}</td>
      <td>${fmtDate(u.last_studied)}</td>
      <td>${flags.join(" ") || "—"}</td>
      <td><button class="btn ghost force-logout-btn" data-uid="${u.id}"
        style="padding:3px 8px">強制ログアウト</button></td>
    </tr>`;
  }).join("");
  root.innerHTML = `
    <h1>👑 管理者情報</h1>
    <p class="sub">ユーザー別の利用状況・上限・残高・問題の把握（管理者専用）。</p>
    <div class="card">
      <h2>セキュリティ</h2>
      <div class="grid cols-4">
        <div class="stat"><div class="num">${sec.locked_accounts ?? 0}</div>
          <div class="lbl">ロック中アカウント</div></div>
        <div class="stat"><div class="num">${sec.locked_ips ?? 0}</div>
          <div class="lbl">ロック中IP(スプレー)</div></div>
        <div class="stat"><div class="num">${sec.locked_usernames ?? 0}</div>
          <div class="lbl">ロック中ユーザー名(分散スプレー)</div></div>
        <div class="stat"><div class="num">${d.users.length}</div>
          <div class="lbl">登録ユーザー数</div></div>
      </div>
      <p class="muted mt">ログイン3回連続失敗→5分ロック / 1IP15回失敗→15分
        ロック / 同一ユーザー名を複数IPから計8回失敗→15分ロック。</p>
    </div>
    <div class="card">
      <h2>ユーザー別 利用状況</h2>
      <table class="mt"><thead><tr>
        <th>担当者 / ID</th><th>権限</th><th>今日 / 上限</th>
        <th>今月 / 上限</th><th>残高</th><th>チャージ(¥)</th>
        <th>AI回数</th><th>AI最終利用</th>
        <th>単語クイズ数</th><th>フレーズクイズ数</th><th>最終学習</th>
        <th>状態</th><th>操作</th>
      </tr></thead><tbody>${rows}</tbody></table>
      <p class="muted mt">残高は日次/月次の<b>無料枠（上限）とは別管理</b>で、枠に
        到達した後の利用で消費されます。チャージは<b>1回 最大¥1000</b>。
        「残高切れ/日上限/月上限」は利用が止まっている目安です。「AI回数」は
        会話等のAI機能利用のみを表し、無料の単語/フレーズクイズは含まない
        （そちらは「単語クイズ数」「フレーズクイズ数」「最終学習」列を参照）。</p>
    </div>
    <div class="card">
      <h2>📮 お問い合わせ・ご要望</h2>
      <p class="muted">ユーザーからの送信を新しい順に表示（手動対応）。</p>
      <table class="mt"><thead><tr>
        <th>日時</th><th>ログインID</th><th>種別</th><th>お名前</th>
        <th>メール</th><th>内容</th><th>状態</th><th>操作</th>
      </tr></thead><tbody>${inquiries.length ? inquiries.map((q) => `
        <tr>
          <td class="muted">${fmtDate(q.created_at)}</td>
          <td>${escapeHtml(q.display_name || q.username || "—")}</td>
          <td>${escapeHtml(q.kind)}</td>
          <td>${escapeHtml(q.name || "—")}</td>
          <td>${escapeHtml(q.email || "—")}</td>
          <td style="white-space:pre-wrap">${escapeHtml(q.content)}</td>
          <td class="iq-status" data-id="${q.id}">${escapeHtml(q.status)}</td>
          <td>${q.status === "対応済み" ? "" :
            `<button class="btn ghost iq-done" data-id="${q.id}"
              style="padding:3px 8px">対応済みにする</button>`}</td>
        </tr>`).join("") :
        `<tr><td colspan="8" class="muted">まだありません。</td></tr>`}
      </tbody></table>
    </div>`;

  root.querySelectorAll(".iq-done").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      await api.put(`/api/inquiries/${id}/status`, { status: "対応済み" });
      root.querySelector(`.iq-status[data-id="${id}"]`).textContent = "対応済み";
      btn.remove();
    });
  });

  // チャージ（1回最大¥1000）。
  root.querySelectorAll(".chg-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const uid = parseInt(btn.dataset.uid, 10);
      const inp = root.querySelector(`.chg-amt[data-uid="${uid}"]`);
      let amt = parseInt(inp.value, 10);
      if (!Number.isFinite(amt) || amt <= 0) { toast("金額を入力"); return; }
      if (amt > 1000) { amt = 1000; toast("1回の上限は¥1000です"); }
      try {
        const r = await api.post("/api/system/admin/charge",
          { user_id: uid, amount_jpy: amt });
        toast(`チャージ完了: 残高 ¥${Math.round(r.balance_jpy)}`);
        go("admin");  // 再描画
      } catch (e) { toast("失敗: " + e.message); }
    });
  });

  // 強制ログアウト（対象ユーザーの既存の全セッションを無効化・§B4）。
  root.querySelectorAll(".force-logout-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const uid = parseInt(btn.dataset.uid, 10);
      if (!confirm("このユーザーを全端末から強制ログアウトさせます。"
        + "よろしいですか？")) return;
      try {
        await api.post("/api/system/admin/force-logout", { user_id: uid });
        toast("強制ログアウトしました");
      } catch (e) { toast("失敗: " + e.message); }
    });
  });
}

// --- Settings (API key, model, nickname note, voices, usage) ---------------

// 大分類ごとにチェックボックス化した分野/シーン一覧のHTMLを組み立てる。
// hiddenSet に入っている項目は未チェック(=非表示設定)で描画する。
function fsetGroupsHtml(groups, hiddenSet, prefix) {
  return Object.entries(groups).map(([cat, items]) => `
    <details class="fset-group" open>
      <summary>${escapeHtml(cat)}
        <span class="muted">(${items.length})</span></summary>
      <div class="fset-actions">
        <button type="button" class="btn ghost fset-cat-all"
          data-prefix="${prefix}" data-cat="${escapeHtml(cat)}"
          data-val="1">このカテゴリを全てON</button>
        <button type="button" class="btn ghost fset-cat-all"
          data-prefix="${prefix}" data-cat="${escapeHtml(cat)}"
          data-val="0">このカテゴリを全てOFF</button>
      </div>
      <div class="fset-items" data-cat="${escapeHtml(cat)}">
        ${items.map((it) => `<label class="fset-item">
          <input type="checkbox" class="fset-${prefix}"
            value="${escapeHtml(it)}"
            ${hiddenSet.has(it) ? "" : "checked"} />
          ${escapeHtml(it)}</label>`).join("")}
      </div>
    </details>`).join("");
}

export async function settings(root) {
  const s = await api.get("/api/system/settings");
  // /api/system/usage is admin-only (全ユーザー横断の使用量のため); 一般
  // ユーザーは403になるので、その場合は空扱いにしてページ全体は描画する。
  let usage = {
    total_cost_usd: 0, today_cost_usd: 0, total_cost_jpy: 0,
    today_cost_jpy: 0, calls: 0, jpy_rate: 0, jpy_as_of: "", recent: [],
  };
  try { usage = await api.get("/api/system/usage"); } catch (_) { /* not admin */ }
  const wFacets = await api.get("/api/words/facets?include_hidden=true");
  const domainGroups = wFacets.domain_groups || {};
  const wLevels = wFacets.range_levels || [];
  const sceneGroups = (await api.get(
    "/api/phrases/scenes?include_hidden=true")).scene_groups || {};
  const pLevels = (await api.get("/api/phrases/facets")).range_levels || [];
  const us0 = (await api.get("/api/system/user-settings")).settings || {};
  const hiddenDomains = new Set(us0.hidden_domains || []);
  const hiddenScenes = new Set(us0.hidden_scenes || []);
  const dfw = us0.default_word_filters || {};
  const dfp = us0.default_phrase_filters || {};
  const lvOptsHtml = (levels, cur) => '<option value="">--</option>'
    + levels.map((l) =>
      `<option ${l === cur ? "selected" : ""}>${escapeHtml(l)}</option>`)
      .join("");
  root.innerHTML = `
    <h1>設定 <span class="muted" id="roleBadge"></span></h1>
    <p class="sub">学習者プロフィールと音声・AIの設定。</p>
    <div class="card">
      <h2>プロフィール</h2>
      <div class="row">
        <label class="toggle">呼んでほしい名前</label>
        <input id="pf_nick" placeholder="例: ゆうた" style="width:200px" />
      </div>
      <div class="row mt">
        <label class="toggle">TOEIC自己申告(任意)</label>
        <input id="pf_toeic" type="number" min="0" max="990" step="5"
          placeholder="例: 550" style="width:120px" />
        <button class="btn good" id="pf_save">保存</button>
      </div>
      <p class="muted">TOEICは出題題材のレベルの手がかりにします（学習が進むと
        実績も加味）。名前はAIが会話で呼びかける際に使います。</p>
    </div>
    <div class="card">
      <h2>表示する分野・シーン</h2>
      <p class="muted">興味のない分野・シーンのチェックを外すと、英単語/
        フレーズ画面のフィルター候補から消えます（データ自体は削除され
        ません・いつでも再表示できます）。<b>チェックの変更はこのカードの
        「保存」を押すまで反映されません。</b></p>
      <div class="fset-section fset-section-w mt">
        <h3>🔤 英単語の分野</h3>
        <div class="row">
          <button type="button" class="btn ghost" id="fset_w_all1">全てON</button>
          <button type="button" class="btn ghost" id="fset_w_all0">全てOFF</button>
          <button type="button" class="btn ghost" id="fset_w_reset">デフォルトに戻す</button>
        </div>
        <div class="fset-wrap mt" id="fset_words">
          ${fsetGroupsHtml(domainGroups, hiddenDomains, "w")}
        </div>
      </div>
      <div class="fset-section fset-section-p mt">
        <h3>💬 フレーズのシーン</h3>
        <div class="row">
          <button type="button" class="btn ghost" id="fset_p_all1">全てON</button>
          <button type="button" class="btn ghost" id="fset_p_all0">全てOFF</button>
          <button type="button" class="btn ghost" id="fset_p_reset">デフォルトに戻す</button>
        </div>
        <div class="fset-wrap mt" id="fset_phrases">
          ${fsetGroupsHtml(sceneGroups, hiddenScenes, "p")}
        </div>
      </div>
      <button class="btn good mt" id="fset_save">保存</button>
      <span class="muted mt" id="fset_out"></span>
    </div>
    <div class="card">
      <h2>既定フィルター</h2>
      <p class="muted">英単語・フレーズの画面を開いたときに自動で適用される
        フィルターです。開いた後にその場でフィルターを変更することも
        今まで通りできます（その場の変更はここでは保存されません。
        既定を変えたいときはこのカードで「保存」してください）。</p>
      <h3 class="mt">英単語</h3>
      <div class="row">
        <select id="dfWCategory">
          <option value="">大分類: 指定なし</option>
          ${Object.keys(domainGroups).map((c) =>
            `<option ${c === dfw.category ? "selected" : ""}>
              ${escapeHtml(c)}</option>`).join("")}
        </select>
        <select id="dfWLvMin">${lvOptsHtml(wLevels, dfw.level_min)}</select>
        <span class="muted">〜</span>
        <select id="dfWLvMax">${lvOptsHtml(wLevels, dfw.level_max)}</select>
        <select id="dfWMastered">
          <option value="">覚えた: 含む</option>
          <option value="hide" ${dfw.mastered === "hide" ? "selected" : ""}>
            覚えた: 隠す</option>
          <option value="only" ${dfw.mastered === "only" ? "selected" : ""}>
            覚えた: のみ</option>
        </select>
      </div>
      <h3 class="mt">フレーズ</h3>
      <div class="row">
        <select id="dfPCategory">
          <option value="">大分類: 指定なし</option>
          ${Object.keys(sceneGroups).map((c) =>
            `<option ${c === dfp.category ? "selected" : ""}>
              ${escapeHtml(c)}</option>`).join("")}
        </select>
        <select id="dfPLvMin">${lvOptsHtml(pLevels, dfp.level_min)}</select>
        <span class="muted">〜</span>
        <select id="dfPLvMax">${lvOptsHtml(pLevels, dfp.level_max)}</select>
        <select id="dfPMastered">
          <option value="">覚えた: 含む</option>
          <option value="hide" ${dfp.mastered === "hide" ? "selected" : ""}>
            覚えた: 隠す</option>
          <option value="only" ${dfp.mastered === "only" ? "selected" : ""}>
            覚えた: のみ</option>
        </select>
      </div>
      <div class="row mt">
        <button class="btn good" id="df_save">保存</button>
        <button class="btn ghost" id="df_clear">既定を使わない(クリア)</button>
        <span class="muted" id="df_out"></span>
      </div>
    </div>
    <div class="card">
      <h2>詳細設定</h2>
      <label><input type="checkbox" id="advHideMastered" />
        「覚えた」判定の語彙・フレーズはクイズ/フラッシュカードに出題しない
        （忘却曲線オフ）</label>
      <p class="muted">オンにすると、単語帳/フレーズ帳一覧の「覚えた」ボタンで
        満点にした項目は、クイズ・フラッシュカードに二度と出てこなくなります。
        また出題したくなったら、一覧画面でその項目の「戻す」ボタンを押すと
        個別に復活します。</p>
      <div class="row mt">
        <button class="btn good" id="adv_save">保存</button>
        <span class="muted" id="adv_out"></span>
      </div>
    </div>
    <div class="card" id="chargeCard" style="display:none">
      <h2>💳 チャージ</h2>
      <p>現在の残高: <b id="ptBalance">-</b> pt</p>
      <div class="row">
        <input id="ck_key" placeholder="XXXX-XXXXXXX-X-XXXX"
          style="width:220px" />
        <button class="btn good" id="ck_redeem">チャージする</button>
      </div>
      <p class="muted mt" id="ck_out"></p>
      <p class="muted">BASE等で購入したチャージキーを入力すると、
        pt（1pt=1円）が残高に加算されます。AI英会話・reading・listening
        等の生成でこの残高が消費されます（単語/フレーズのクイズは無料）。
        消費ペースは為替やAI提供元のAPI価格改定により変動することが
        あります。
        <a href="/static/terms.html" target="_blank">利用規約・免責事項</a></p>
    </div>
    <div class="card" id="securityCard" style="display:none">
      <h2>🔒 セキュリティ</h2>
      <p class="muted">端末を共有した後や、身に覚えのないログイン状態に
        気づいたときは、全端末から一括でログアウトできます
        （このボタンを押した端末も再ログインが必要になります）。</p>
      <button class="btn bad" id="logoutAllBtn">全端末からログアウト</button>
      <span class="muted mt" id="logoutAllOut"></span>
    </div>
    <div class="card admin-only" id="openaiCard">
      <h2>OpenAI</h2>
      <div class="row">
        <input id="key" type="password" placeholder="APIキー (${s.api_key_masked || "未設定"})"
          style="width:340px" />
        <select id="model">${state.taxonomy.models.map((m) =>
          `<option ${m === s.model ? "selected" : ""}>${m}</option>`).join("")}</select>
        <button class="btn good" id="save">保存</button>
      </div>
      <div class="row mt">
        <label class="toggle">判定・教材用モデル(高品質)</label>
        <input id="qmodel" placeholder="例: gpt-4o（空欄なら通常モデル）"
          value="${escapeHtml(s.quality_model || "")}" style="width:280px" />
      </div>
      <p class="muted">通常の会話/クイズは上の安価なモデル、判定・教材作成だけ
        この高品質モデルを使います。お使いのアカウントで有効なモデル名を入力。</p>
      <p class="muted">ニックネームや個人情報は .env の USER_NICKNAME に記載してください
        （git管理ファイルには保存しません）。</p>
    </div>
    <div class="card">
      <h2>お問い合わせ・ご要望</h2>
      <p class="muted">不具合報告・追加してほしい語彙/機能など、お気軽に
        送信してください（個人開発のため対応は手動・ベストエフォートです）。</p>
      <div class="row">
        <select id="iq_kind">
          ${["要望", "お問い合わせ", "ログインできない", "技術的トラブル",
             "課金トラブル", "機能に関する要望",
             "訳・音声の間違えに関する報告", "応援メッセージ", "感想",
             "その他"].map((k) => `<option>${escapeHtml(k)}</option>`)
             .join("")}
        </select>
        <input id="iq_name" placeholder="お名前(任意)" style="width:140px" />
        <input id="iq_email" placeholder="メール(任意・返信が必要な場合)"
          style="width:220px" />
      </div>
      <textarea id="iq_content" class="mt" style="min-height:80px"
        placeholder="内容を入力してください"></textarea>
      <div class="row mt">
        <button class="btn good" id="iq_send">送信</button>
        <span class="muted" id="iq_out"></span>
      </div>
    </div>
    <div class="card">
      <h2>ℹ️ このアプリについて</h2>
      <p class="muted">バージョン ${escapeHtml(s.version || "")}
        （個人開発・ベストエフォート対応）。</p>
      <p><a href="/static/about.html" target="_blank">このアプリについて
        （まとめページ）</a></p>
      <p><a href="/static/terms.html" target="_blank">利用規約・免責事項</a></p>
      <p><a href="/tokushoho" target="_blank">特定商取引法に基づく表記</a>
        ${s.tokushoho_ready ? "" : `<span class="muted">
        （現在たたき台・記入中です）</span>`}</p>
      <p class="muted">取扱説明書・使い方ガイドは準備中です。ご不明な点は
        上の「お問い合わせ・ご要望」からお気軽にどうぞ。</p>
    </div>
    <div class="card">
      <h2>音声入力</h2>
      <label class="toggle">
        <input type="checkbox" id="autoSubmit"
          ${speech.isVoiceAutoSubmit() ? "checked" : ""} />
        録音停止したら自動で判定/送信する（OFFなら内容を確認してから送信）</label>
    </div>
    <div class="card admin-only">
      <h2>🔞 禁止用語（注意喚起）</h2>
      <p class="muted">罵り・スラング・差別語など、映画やドラマで出会うが
        使うと危険な表現です。学習(理解・回避)のため最小限・伏字で収録しています。
        既定では一覧・クイズの両方から除外しています。</p>
      <label class="toggle">
        <input type="checkbox" id="banShow" ${showBanned() ? "checked" : ""} />
        一覧（英単語・フレーズ）に表示する</label><br/>
      <label class="toggle">
        <input type="checkbox" id="banTest" ${testBanned() ? "checked" : ""} />
        クイズ・デイリーの出題に含める</label>
      <p class="muted mt">※ 和製英語・発音注意（安全な学習項目）は常に表示されます。</p>
    </div>
    <div class="card">
      <h2>AIの声（読み上げ）</h2>
      <label class="toggle">
        <input type="checkbox" id="natural" ${speech.isNatural() ? "checked" : ""} />
        自然な声(AI / ChatGPT相当)を使う（OFFでブラウザ標準の声）</label>
      <p class="muted mt">使いたい声をON/OFF。学習回ごとに有効な声から
        ランダムで選ばれ、画面に名前が出ます。</p>
      <div class="voice-list" id="voices"></div>
      <p id="voiceErr" class="muted" style="color:var(--warn)"></p>
      <button class="btn secondary mt" id="testVoice">🔊 ランダムな声でテスト</button>
      <p class="muted">自然な声にはOpenAIの利用枠（課金/クレジット）が必要です。
        失敗時は自動でブラウザ標準の声に切り替わります。</p>
    </div>
    <div class="card admin-only" id="vocabAddCard">
      <h2>語彙の追加・インポート</h2>
      <h3>単語を追加</h3>
      <div class="row">
        <input id="sa_en" placeholder="English" />
        <input id="sa_ja" placeholder="日本語" />
        <input id="sa_pos" placeholder="品詞" style="width:80px" />
        <input id="sa_ex" placeholder="例文" style="width:240px" />
        <button class="btn good" id="sa_add">追加</button>
        <span id="sa_out" class="muted"></span>
      </div>
      <h3 class="mt">単語の一括インポート</h3>
      <p class="muted">「英単語 [タブ/カンマ] 日本語」を1行ずつ貼り付け。
        番号付き一覧でもOK。AIが訳を精査し例文を自動生成します。</p>
      <textarea id="sa_bulk" style="min-height:110px"
        placeholder="例:\ncompany\t会社\nseveral\tいくつかの"></textarea>
      <div class="row mt">
        <label class="toggle"><input type="checkbox" id="sa_gen" checked />
          例文をAI生成・訳を精査（要API）</label>
        <button class="btn" id="sa_imp">インポート</button>
      </div>
      <div id="sa_impout" class="muted mt"></div>
      <h3 class="mt">フレーズを追加</h3>
      <div class="row">
        <input id="sp_en" placeholder="English" style="width:240px" />
        <input id="sp_ja" placeholder="日本語" style="width:200px" />
        <input id="sp_sc" placeholder="シーン" style="width:120px" />
        <button class="btn good" id="sp_add">追加</button>
        <span id="sp_out" class="muted"></span>
      </div>
    </div>
    <div class="card admin-only">
      <h2>API使用量・費用</h2>
      <p>累計 <b>¥${usage.total_cost_jpy}</b>（$${usage.total_cost_usd.toFixed(4)}）
         / 今日 <b>¥${usage.today_cost_jpy}</b>（$${usage.today_cost_usd.toFixed(4)}）
         / 呼び出し ${usage.calls} 回</p>
      <p class="muted">為替レート: ¥${usage.jpy_rate}/$（${usage.jpy_as_of} 時点・
        .env の USD_JPY_RATE で更新可。週1回見直し推奨）</p>
      <table><thead><tr><th>日時</th><th>機能</th><th>モデル</th>
        <th>in</th><th>out</th><th>費用</th></tr></thead><tbody>
        ${usage.recent.map((r) => `<tr><td class="muted">${r.created_at}</td>
          <td>${r.feature}</td><td>${r.model}</td><td>${r.prompt_tokens}</td>
          <td>${r.output_tokens}</td><td>$${r.cost_usd.toFixed(4)}</td></tr>`)
          .join("")}</tbody></table>
    </div>`;

  // 語彙の追加・インポート（英単語/フレーズ画面から移動）。
  const sq = (s) => root.querySelector(s);
  sq("#sa_add").addEventListener("click", async () => {
    const en = sq("#sa_en").value.trim(), ja = sq("#sa_ja").value.trim();
    if (!en || !ja) { toast("英語と日本語は必須です"); return; }
    await api.post("/api/words", {
      english: en, japanese: ja,
      part_of_speech: sq("#sa_pos").value, example: sq("#sa_ex").value,
    });
    sq("#sa_out").textContent = `追加: ${en}`;
    ["#sa_en", "#sa_ja", "#sa_pos", "#sa_ex"].forEach((i) => {
      sq(i).value = "";
    });
  });
  sq("#sa_imp").addEventListener("click", async () => {
    const text = sq("#sa_bulk").value;
    if (!text.trim()) { toast("貼り付けてください"); return; }
    const out = sq("#sa_impout");
    out.textContent = "インポート中…（AI生成は数十秒かかることがあります）";
    try {
      const r = await api.post("/api/words/import", {
        text, generate_examples: sq("#sa_gen").checked,
      });
      out.textContent =
        `解析 ${r.parsed} / 追加 ${r.added} / 重複 ${r.skipped}`
        + ` / 例文生成 ${r.examples}`;
      refreshCost();
    } catch (e) { out.textContent = "失敗: " + e.message; }
  });
  sq("#sp_add").addEventListener("click", async () => {
    const en = sq("#sp_en").value.trim(), ja = sq("#sp_ja").value.trim();
    if (!en || !ja) { toast("英語と日本語は必須です"); return; }
    await api.post("/api/phrases", {
      english: en, japanese: ja, scene: sq("#sp_sc").value,
    });
    sq("#sp_out").textContent = `追加: ${en}`;
    ["#sp_en", "#sp_ja", "#sp_sc"].forEach((i) => { sq(i).value = ""; });
  });

  sq("#iq_send").addEventListener("click", async () => {
    const content = sq("#iq_content").value.trim();
    if (!content) { toast("内容を入力してください"); return; }
    try {
      await api.post("/api/inquiries", {
        kind: sq("#iq_kind").value,
        name: sq("#iq_name").value.trim(),
        email: sq("#iq_email").value.trim(),
        content,
      });
      sq("#iq_out").textContent = "送信しました。ありがとうございます！";
      sq("#iq_content").value = "";
      sq("#iq_name").value = ""; sq("#iq_email").value = "";
    } catch (e) { sq("#iq_out").textContent = "送信失敗: " + e.message; }
  });

  // --- 表示する分野・シーン（チェックボックス、保存を押すまで反映しない）---
  const fsetAll = (prefix, val) => {
    root.querySelectorAll(`.fset-${prefix}`).forEach((cb) => {
      cb.checked = !!val;
    });
  };
  root.querySelector("#fset_w_all1").addEventListener("click",
    () => fsetAll("w", true));
  root.querySelector("#fset_w_all0").addEventListener("click",
    () => fsetAll("w", false));
  root.querySelector("#fset_w_reset").addEventListener("click",
    () => fsetAll("w", true));
  root.querySelector("#fset_p_all1").addEventListener("click",
    () => fsetAll("p", true));
  root.querySelector("#fset_p_all0").addEventListener("click",
    () => fsetAll("p", false));
  root.querySelector("#fset_p_reset").addEventListener("click",
    () => fsetAll("p", true));
  root.querySelectorAll(".fset-cat-all").forEach((btn) => {
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      const prefix = btn.dataset.prefix, cat = btn.dataset.cat;
      const val = btn.dataset.val === "1";
      root.querySelectorAll(
        `.fset-items[data-cat="${CSS.escape(cat)}"] .fset-${prefix}`,
      ).forEach((cb) => { cb.checked = val; });
    });
  });
  root.querySelector("#fset_save").addEventListener("click", async () => {
    const hidden_domains = [...root.querySelectorAll(".fset-w")]
      .filter((cb) => !cb.checked).map((cb) => cb.value);
    const hidden_scenes = [...root.querySelectorAll(".fset-p")]
      .filter((cb) => !cb.checked).map((cb) => cb.value);
    const settings = {};
    try { Object.assign(settings,
      (await api.get("/api/system/user-settings")).settings || {}); }
    catch (_) { /* */ }
    settings.hidden_domains = hidden_domains;
    settings.hidden_scenes = hidden_scenes;
    await api.put("/api/system/user-settings", { settings });
    root.querySelector("#fset_out").textContent =
      `保存しました（非表示: 分野${hidden_domains.length}件 / `
      + `シーン${hidden_scenes.length}件）`;
  });

  // 単語/フレーズの既定フィルター（2026-08-08・2026-08-04要望のB10）。
  const readDefaultFilters = (prefix) => {
    const v = (id) => root.querySelector(id).value;
    return {
      category: v(`#df${prefix}Category`),
      level_min: v(`#df${prefix}LvMin`),
      level_max: v(`#df${prefix}LvMax`),
      mastered: v(`#df${prefix}Mastered`),
    };
  };
  root.querySelector("#df_save").addEventListener("click", async () => {
    const settings = {};
    try { Object.assign(settings,
      (await api.get("/api/system/user-settings")).settings || {}); }
    catch (_) { /* */ }
    settings.default_word_filters = readDefaultFilters("W");
    settings.default_phrase_filters = readDefaultFilters("P");
    await api.put("/api/system/user-settings", { settings });
    root.querySelector("#df_out").textContent = "保存しました";
  });
  root.querySelector("#df_clear").addEventListener("click", async () => {
    ["#dfWCategory", "#dfPCategory"].forEach((s) => {
      root.querySelector(s).value = "";
    });
    ["#dfWLvMin", "#dfWLvMax", "#dfPLvMin", "#dfPLvMax"].forEach((s) => {
      root.querySelector(s).value = "";
    });
    ["#dfWMastered", "#dfPMastered"].forEach((s) => {
      root.querySelector(s).value = "";
    });
    const settings = {};
    try { Object.assign(settings,
      (await api.get("/api/system/user-settings")).settings || {}); }
    catch (_) { /* */ }
    settings.default_word_filters = {};
    settings.default_phrase_filters = {};
    await api.put("/api/system/user-settings", { settings });
    root.querySelector("#df_out").textContent = "既定フィルターをクリアしました";
  });

  const saveBtn = root.querySelector("#save");
  if (saveBtn) saveBtn.addEventListener("click", async () => {
    const body = {
      openai_model: root.querySelector("#model").value,
      openai_quality_model: root.querySelector("#qmodel").value,
    };
    const key = root.querySelector("#key").value.trim();
    if (key) body.openai_api_key = key;
    await api.put("/api/system/settings", body);
    toast("保存しました"); await refreshAiState(); go("settings");
  });

  // --- プロフィール(per-user 設定) のロード/保存 + ロール別表示 ---
  (async () => {
    let mu = null, us = {};
    try { mu = await api.get("/api/system/my-usage"); } catch (_) { /* */ }
    try { us = (await api.get("/api/system/user-settings")).settings || {}; }
    catch (_) { /* */ }
    const nick = root.querySelector("#pf_nick");
    const toeic = root.querySelector("#pf_toeic");
    if (nick) nick.value = us.nickname || "";
    if (toeic) toeic.value = us.toeic_self || "";
    const advHide = root.querySelector("#advHideMastered");
    if (advHide) advHide.checked = !!us.hide_mastered;
    // 管理者表示。一般ユーザーには管理者向けカードを隠す。
    const badge = root.querySelector("#roleBadge");
    if (mu && mu.role === "admin") {
      if (badge) badge.textContent = "（管理者）";
    } else {
      root.querySelectorAll(".admin-only").forEach((c) => {
        c.style.display = "none";
      });
    }
    // 単語/フレーズの手動追加・一括インポート、OpenAI(APIキー/モデル)設定は
    // 2026-08-08よりとりあえず非表示（メンテ負荷を下げ機能を簡潔に保つ方針・
    // ユーザー指示。APIキー/モデルは今後 .env 編集+再デプロイで運用）。
    // 管理者でも表示しない。復活させる場合はこのブロックを削除するだけでよい。
    const vac = root.querySelector("#vocabAddCard");
    if (vac) vac.style.display = "none";
    const oac = root.querySelector("#openaiCard");
    if (oac) oac.style.display = "none";
    // チャージカード: ローカル単一ユーザー(multiuser=false)では非表示
    // （残高の概念が無いため）。ログイン中の全ユーザーに表示する
    // （admin-onlyではない）。
    const chargeCard = root.querySelector("#chargeCard");
    if (mu && mu.multiuser && chargeCard) {
      chargeCard.style.display = "";
      const bal = root.querySelector("#ptBalance");
      if (bal) {
        bal.textContent = mu.balance_jpy != null
          ? Math.round(mu.balance_jpy) : "0";
      }
    }
    // セキュリティカード: chargeCardと同じくmultiuser時のみ表示
    // （ローカル単一ユーザーはセッション/Cookieの概念が無いため）。
    const securityCard = root.querySelector("#securityCard");
    if (mu && mu.multiuser && securityCard) {
      securityCard.style.display = "";
    }
  })();

  const pfSave = root.querySelector("#pf_save");
  if (pfSave) pfSave.addEventListener("click", async () => {
    const settings = {};
    // 既存設定とマージ（他キーを消さない）。
    try { Object.assign(settings,
      (await api.get("/api/system/user-settings")).settings || {}); }
    catch (_) { /* */ }
    settings.nickname = root.querySelector("#pf_nick").value.trim();
    const t = parseInt(root.querySelector("#pf_toeic").value, 10);
    settings.toeic_self = Number.isFinite(t) ? t : null;
    await api.put("/api/system/user-settings", { settings });
    toast("プロフィールを保存しました");
  });

  const advSave = root.querySelector("#adv_save");
  if (advSave) advSave.addEventListener("click", async () => {
    const settings = {};
    try { Object.assign(settings,
      (await api.get("/api/system/user-settings")).settings || {}); }
    catch (_) { /* */ }
    settings.hide_mastered =
      root.querySelector("#advHideMastered").checked;
    await api.put("/api/system/user-settings", { settings });
    root.querySelector("#adv_out").textContent = "保存しました";
  });

  const logoutAllBtn = root.querySelector("#logoutAllBtn");
  if (logoutAllBtn) logoutAllBtn.addEventListener("click", async () => {
    if (!confirm("全端末からログアウトします。この端末も含めて"
      + "再ログインが必要になります。よろしいですか？")) return;
    try { await api.post("/api/auth/logout-all-devices"); }
    catch (_) { /* */ }
    location.href = "/login";
  });

  const ckBtn = root.querySelector("#ck_redeem");
  if (ckBtn) ckBtn.addEventListener("click", async () => {
    const keyInput = root.querySelector("#ck_key");
    const out = root.querySelector("#ck_out");
    const key = keyInput.value.trim();
    if (!key) { toast("チャージキーを入力してください"); return; }
    out.textContent = "";
    try {
      const r = await api.post("/api/billing/redeem", { key });
      out.textContent = `チャージしました。現在の残高: `
        + `${Math.round(r.balance_jpy)} pt`;
      const bal = root.querySelector("#ptBalance");
      if (bal) bal.textContent = Math.round(r.balance_jpy);
      keyInput.value = "";
      toast("チャージが完了しました");
      refreshCost();
    } catch (e) { out.textContent = "失敗: " + e.message; }
  });

  // Friendly descriptions for the OpenAI voices.
  const VOICE_DESC = {
    alloy: "中性的・クリア", ash: "落ち着いた男性的", ballad: "表情豊か",
    coral: "明るい女性的", echo: "穏やかな男性的", fable: "物語的",
    nova: "明るい女性的", onyx: "低め・男性的", sage: "落ち着いた",
    shimmer: "やわらかい女性的",
  };
  const TEST_LINE = "Hi! This is your study voice for today.";

  const renderVoices = () => {
    const box = root.querySelector("#voices");
    box.innerHTML = "";
    if (state.aiEnabled && speech.isNatural()) {
      speech.listOpenAIVoices().forEach((name) => {
        const row = el(`<div class="voice-row">
          <input type="checkbox" ${speech.isOpenAIVoiceEnabled(name)
            ? "checked" : ""} />
          <span class="name">${name}</span>
          <span class="lang">${VOICE_DESC[name] || ""}</span>
          <button class="btn ghost">▶</button></div>`);
        row.querySelector("input").addEventListener("change", (e) =>
          speech.setOpenAIVoiceEnabled(name, e.target.checked));
        row.querySelector("button").addEventListener("click", async () => {
          const r = await speech.previewOpenAIVoice(name, TEST_LINE);
          if (!r.ok) {
            const errBox = root.querySelector("#voiceErr");
            errBox.textContent = "音声エラー: " + (r.error || "不明");
            console.error("TTS preview failed:", r.error);
          }
        });
        box.appendChild(row);
      });
      return;
    }
    // Browser voices (fallback / when natural is off).
    const voices = speech.getEnglishVoices();
    if (!voices.length) {
      box.innerHTML = `<p class="muted">利用可能な音声が見つかりません。
        （AIキー設定＋「自然な声」ONを推奨）</p>`;
      return;
    }
    voices.forEach((v) => {
      const row = el(`<div class="voice-row">
        <span class="name">${escapeHtml(v.name)}</span>
        <span class="lang">${v.lang}</span>
        <button class="btn ghost">▶</button></div>`);
      row.querySelector("button").addEventListener("click", () => {
        const u = new SpeechSynthesisUtterance(TEST_LINE);
        u.voice = v; u.lang = v.lang; window.speechSynthesis.cancel();
        window.speechSynthesis.speak(u);
      });
      box.appendChild(row);
    });
  };
  renderVoices();
  if (window.speechSynthesis) {
    window.speechSynthesis.onvoiceschanged = renderVoices;
  }
  root.querySelector("#autoSubmit").addEventListener("change", (e) => {
    speech.setVoiceAutoSubmit(e.target.checked);
    toast(e.target.checked ? "音声→自動判定 ON" : "音声→確認してから送信");
  });
  root.querySelector("#banShow").addEventListener("change", (e) => {
    setShowBanned(e.target.checked);
    toast(e.target.checked ? "禁止用語を一覧に表示" : "禁止用語を一覧から除外");
  });
  root.querySelector("#banTest").addEventListener("change", (e) => {
    setTestBanned(e.target.checked);
    toast(e.target.checked ? "禁止用語を出題に含める" : "禁止用語を出題から除外");
  });
  root.querySelector("#natural").addEventListener("change", (e) => {
    speech.setNatural(e.target.checked);
    speech.pickRoundVoice();
    renderVoices();
  });
  root.querySelector("#testVoice").addEventListener("click", () => {
    const name = speech.pickRoundVoice();
    toast("声: " + (name || "なし"));
    speech.speak(TEST_LINE);
  });
}

// --- 単語帳(デッキ) --------------------------------------------------------

export async function decks(root) {
  const [list, facets, summary] = await Promise.all([
    api.get("/api/decks"),
    api.get("/api/words/facets?include_banned=true"),
    api.get("/api/decks/summary"),
  ]);
  root.innerHTML = `
    <h1>単語帳</h1>
    <p class="sub">分野・レベルから自分用の単語帳(デッキ)を作って学習。
      デッキ別に出題方向や合格条件を設定できます。
      無料範囲では1個・100語まで、チャージ済みなら個数・件数とも無制限です。</p>
    <div class="card">
      <h2>単語帳 全体の達成率</h2>
      <div class="row" style="justify-content:space-between">
        <span class="muted">${summary.deck_count}個の単語帳・
          全${summary.total}語のうち${summary.mastered}語が習得済み</span>
        <b>${summary.pct}%</b>
      </div>
      <div class="bar mt"><span style="width:${summary.pct}%"></span></div>
    </div>
    <div class="card">
      <h2>新しい単語帳を作る</h2>
      <input id="dname" placeholder="単語帳の名前" style="width:240px" />
      <div class="row mt" style="align-items:flex-start">
        <div><div class="muted">分野(複数チェック可)</div>
          <div id="ddomains" class="chkbox">${facets.domains.map((d) =>
            `<label class="chk"><input type="checkbox" value="${escapeHtml(d)}"
              /> ${escapeHtml(d)}</label>`).join("")}</div></div>
        <div><div class="muted">レベル(複数チェック可)</div>
          <div id="dlevels" class="chkbox">${facets.levels.map((l) =>
            `<label class="chk"><input type="checkbox" value="${escapeHtml(l)}"
              /> ${escapeHtml(l)}</label>`).join("")}</div></div>
      </div>
      <div class="row mt">
        <label>件数(お任せ): <input id="dlimit" type="number" value="50"
          style="width:80px" min="1" /></label>
        <label>出題方向: <select id="ddir">
          <option value="both">両方向</option>
          <option value="en2ja">英→日</option>
          <option value="ja2en">日→英</option></select></label>
        <label>N回正解で習得: <input id="dpass" type="number" value="2"
          style="width:60px" min="1" /></label>
        <label class="toggle"><input type="checkbox" id="dsrs" checked />
          忘却曲線を使う</label>
        <label>1回の出題数: <input id="dsize" type="number" value="10"
          style="width:60px" min="1" /></label>
      </div>
      <div class="row mt">
        ${state.isAdmin ? `<label class="toggle">
          <input type="checkbox" id="dbanned" />
          🔞 禁止用語も含める</label>` : ""}
        <button class="btn good" id="dcreate">作成</button>
        <span id="dcreateOut" class="muted"></span>
      </div>
      <p class="muted mt">分野・レベルを選ばなければ全体から、件数ぶんランダムに
        「お任せ」で作ります。</p>
    </div>
    <div id="deckList" class="mt"></div>`;

  const sels = (id) =>
    [...root.querySelectorAll(id + " input:checked")].map((o) => o.value);

  const renderList = (decksArr) => {
    const box = root.querySelector("#deckList");
    box.innerHTML = `<h2>マイ単語帳 (${decksArr.length})</h2>`;
    if (!decksArr.length) {
      box.appendChild(el(`<p class="muted">まだ単語帳がありません。</p>`));
      return;
    }
    decksArr.forEach((d) => {
      const pct = d.total ? Math.round(d.mastered / d.total * 100) : 0;
      const dirLabel = { both: "両方向", en2ja: "英→日", ja2en: "日→英" }[
        d.settings.directions] || "両方向";
      const card = el(`<div class="card">
        <div class="row" style="justify-content:space-between">
          <b>${escapeHtml(d.name)}</b>
          <span class="muted">${d.mastered}/${d.total} 習得 (${pct}%)</span></div>
        <div class="bar mt"><span style="width:${pct}%"></span></div>
        <div class="muted mt">${dirLabel} ・ ${d.settings.pass_count}回正解で
          クイズ優先度リセット ・ 忘却曲線${d.settings.use_srs ? "ON" : "OFF"}
          ・ 出題${d.settings.quiz_size}</div>
        <div class="row mt">
          <button class="btn ghost" data-act="edit">✏️ 編集</button>
          <button class="btn ghost del-btn" data-act="del"
            title="削除">🗑️</button></div></div>`);
      card.querySelector('[data-act="edit"]')
        .addEventListener("click", () => editDeck(d));
      card.querySelector('[data-act="del"]').addEventListener("click",
        async () => {
          if (!confirm(`「${d.name}」を削除しますか？`)) return;
          await api.del("/api/decks/" + d.id);
          go("deck");
        });
      box.appendChild(card);
    });
  };
  renderList(list);

  root.querySelector("#dcreate").addEventListener("click", async () => {
    const name = root.querySelector("#dname").value.trim();
    const out = root.querySelector("#dcreateOut");
    out.textContent = "作成中…";
    try {
      const d = await api.post("/api/decks", {
        name: name || "新しい単語帳",
        domains: sels("#ddomains"),
        levels: sels("#dlevels"),
        include_banned: !!root.querySelector("#dbanned")?.checked,
        limit: parseInt(root.querySelector("#dlimit").value, 10) || null,
        settings: {
          directions: root.querySelector("#ddir").value,
          pass_count: parseInt(root.querySelector("#dpass").value, 10) || 2,
          use_srs: root.querySelector("#dsrs").checked,
          quiz_size: parseInt(root.querySelector("#dsize").value, 10) || 10,
        },
      });
      out.textContent = `作成: ${d.name} (${d.total}語)`;
      go("deck");
    } catch (e) { out.textContent = "失敗: " + e.message; }
  });

  function editDeck(d) {
    openModal("編集: " + d.name, (body) => {
      const s = d.settings;
      body.appendChild(el(`<div class="row">
        <label>名前: <input id="en" value="${escapeHtml(d.name)}"
          style="width:200px" /></label></div>`));
      body.appendChild(el(`<div class="row mt">
        <label>出題方向: <select id="edir">
          <option value="both">両方向</option>
          <option value="en2ja">英→日</option>
          <option value="ja2en">日→英</option></select></label>
        <label>N回正解でクイズ優先度リセット: <input id="epass" type="number"
          value="${s.pass_count}" style="width:60px" min="1" /></label></div>`));
      body.appendChild(el(`<div class="row mt">
        <label class="toggle"><input type="checkbox" id="esrs"
          ${s.use_srs ? "checked" : ""} /> 忘却曲線を使う</label>
        <label>出題数: <input id="esize" type="number" value="${s.quiz_size}"
          style="width:60px" min="1" /></label></div>`));
      body.querySelector("#edir").value = s.directions;
      const save = el(`<button class="btn good mt">保存</button>`);
      save.addEventListener("click", async () => {
        await api.put("/api/decks/" + d.id, {
          name: body.querySelector("#en").value.trim() || d.name,
          settings: {
            directions: body.querySelector("#edir").value,
            pass_count: parseInt(body.querySelector("#epass").value, 10) || 2,
            use_srs: body.querySelector("#esrs").checked,
            quiz_size: parseInt(body.querySelector("#esize").value, 10) || 10,
          },
        });
        go("deck");
      });
      body.appendChild(save);

      body.appendChild(el(`<hr class="mt" />`));
      body.appendChild(el(`<h3>収録中の単語 (<span id="wcount">…</span>)</h3>`));
      const wlist = el(`<div id="wlist" class="mt"></div>`);
      body.appendChild(wlist);
      const loadWords = async () => {
        const words = await api.get(`/api/decks/${d.id}/words`);
        body.querySelector("#wcount").textContent = words.length;
        wlist.innerHTML = "";
        if (!words.length) {
          wlist.appendChild(el(`<p class="muted">単語がありません。</p>`));
          return;
        }
        words.forEach((w) => {
          const row = el(`<div class="row"
            style="justify-content:space-between;padding:4px 0">
            <span>${escapeHtml(w.english)}
              <span class="muted">${escapeHtml(w.japanese || "")}</span></span>
            <button class="btn ghost del-btn" title="単語帳から外す">🗑️</button>
            </div>`);
          row.querySelector("button").addEventListener("click", async () => {
            if (!confirm(`「${w.english}」を単語帳から外しますか？`)) return;
            await api.del(`/api/decks/${d.id}/words/${w.id}`);
            loadWords();
          });
          wlist.appendChild(row);
        });
      };
      loadWords();
    });
  }
}

export async function phraseDecks(root) {
  const [list, sceneFacets, levelFacets, summary] = await Promise.all([
    api.get("/api/phrase-decks"),
    api.get("/api/phrases/scenes?include_banned=true"),
    api.get("/api/phrases/facets"),
    api.get("/api/phrase-decks/summary"),
  ]);
  root.innerHTML = `
    <h1>フレーズ帳</h1>
    <p class="sub">シーン・レベルから自分用のフレーズ帳(デッキ)を作って学習。
      デッキ別に出題方向や合格条件を設定できます。
      無料範囲では1個・100件まで、チャージ済みなら個数・件数とも無制限です。</p>
    <div class="card">
      <h2>フレーズ帳 全体の達成率</h2>
      <div class="row" style="justify-content:space-between">
        <span class="muted">${summary.deck_count}個のフレーズ帳・
          全${summary.total}件のうち${summary.mastered}件が習得済み</span>
        <b>${summary.pct}%</b>
      </div>
      <div class="bar mt"><span style="width:${summary.pct}%"></span></div>
    </div>
    <div class="card">
      <h2>新しいフレーズ帳を作る</h2>
      <input id="pdname" placeholder="フレーズ帳の名前" style="width:240px" />
      <div class="row mt" style="align-items:flex-start">
        <div><div class="muted">シーン(複数チェック可)</div>
          <div id="pdscenes" class="chkbox">${sceneFacets.scenes.map((s) =>
            `<label class="chk"><input type="checkbox" value="${escapeHtml(s)}"
              /> ${escapeHtml(s)}</label>`).join("")}</div></div>
        <div><div class="muted">レベル(複数チェック可)</div>
          <div id="pdlevels" class="chkbox">${levelFacets.range_levels.map((l) =>
            `<label class="chk"><input type="checkbox" value="${escapeHtml(l)}"
              /> ${escapeHtml(l)}</label>`).join("")}</div></div>
      </div>
      <div class="row mt">
        <label>件数(お任せ): <input id="pdlimit" type="number" value="50"
          style="width:80px" min="1" /></label>
        <label>出題方向: <select id="pddir">
          <option value="both">両方向</option>
          <option value="en2ja">英→日</option>
          <option value="ja2en">日→英</option></select></label>
        <label>N回正解でクイズ優先度リセット: <input id="pdpass" type="number"
          value="2" style="width:60px" min="1" /></label>
        <label class="toggle"><input type="checkbox" id="pdsrs" checked />
          忘却曲線を使う</label>
        <label>1回の出題数: <input id="pdsize" type="number" value="10"
          style="width:60px" min="1" /></label>
      </div>
      <div class="row mt">
        ${state.isAdmin ? `<label class="toggle">
          <input type="checkbox" id="pdbanned" />
          🔞 禁止用語も含める</label>` : ""}
        <button class="btn good" id="pdcreate">作成</button>
        <span id="pdcreateOut" class="muted"></span>
      </div>
      <p class="muted mt">シーン・レベルを選ばなければ全体から、件数ぶんランダムに
        「お任せ」で作ります。</p>
    </div>
    <div id="phraseDeckList" class="mt"></div>`;

  const sels = (id) =>
    [...root.querySelectorAll(id + " input:checked")].map((o) => o.value);

  const renderList = (decksArr) => {
    const box = root.querySelector("#phraseDeckList");
    box.innerHTML = `<h2>マイフレーズ帳 (${decksArr.length})</h2>`;
    if (!decksArr.length) {
      box.appendChild(el(`<p class="muted">まだフレーズ帳がありません。</p>`));
      return;
    }
    decksArr.forEach((d) => {
      const pct = d.total ? Math.round(d.mastered / d.total * 100) : 0;
      const dirLabel = { both: "両方向", en2ja: "英→日", ja2en: "日→英" }[
        d.settings.directions] || "両方向";
      const card = el(`<div class="card">
        <div class="row" style="justify-content:space-between">
          <b>${escapeHtml(d.name)}</b>
          <span class="muted">${d.mastered}/${d.total} 習得 (${pct}%)</span></div>
        <div class="bar mt"><span style="width:${pct}%"></span></div>
        <div class="muted mt">${dirLabel} ・ ${d.settings.pass_count}回正解で
          クイズ優先度リセット ・ 忘却曲線${d.settings.use_srs ? "ON" : "OFF"}
          ・ 出題${d.settings.quiz_size}</div>
        <div class="row mt">
          <button class="btn ghost" data-act="edit">✏️ 編集</button>
          <button class="btn ghost del-btn" data-act="del"
            title="削除">🗑️</button></div></div>`);
      card.querySelector('[data-act="edit"]')
        .addEventListener("click", () => editDeck(d));
      card.querySelector('[data-act="del"]').addEventListener("click",
        async () => {
          if (!confirm(`「${d.name}」を削除しますか？`)) return;
          await api.del("/api/phrase-decks/" + d.id);
          go("phrasedeck");
        });
      box.appendChild(card);
    });
  };
  renderList(list);

  root.querySelector("#pdcreate").addEventListener("click", async () => {
    const name = root.querySelector("#pdname").value.trim();
    const out = root.querySelector("#pdcreateOut");
    out.textContent = "作成中…";
    try {
      const d = await api.post("/api/phrase-decks", {
        name: name || "新しいフレーズ帳",
        scenes: sels("#pdscenes"),
        levels: sels("#pdlevels"),
        include_banned: !!root.querySelector("#pdbanned")?.checked,
        limit: parseInt(root.querySelector("#pdlimit").value, 10) || null,
        settings: {
          directions: root.querySelector("#pddir").value,
          pass_count: parseInt(root.querySelector("#pdpass").value, 10) || 2,
          use_srs: root.querySelector("#pdsrs").checked,
          quiz_size: parseInt(root.querySelector("#pdsize").value, 10) || 10,
        },
      });
      out.textContent = `作成: ${d.name} (${d.total}件)`;
      go("phrasedeck");
    } catch (e) { out.textContent = "失敗: " + e.message; }
  });

  function editDeck(d) {
    openModal("編集: " + d.name, (body) => {
      const s = d.settings;
      body.appendChild(el(`<div class="row">
        <label>名前: <input id="pen" value="${escapeHtml(d.name)}"
          style="width:200px" /></label></div>`));
      body.appendChild(el(`<div class="row mt">
        <label>出題方向: <select id="pedir">
          <option value="both">両方向</option>
          <option value="en2ja">英→日</option>
          <option value="ja2en">日→英</option></select></label>
        <label>N回正解でクイズ優先度リセット: <input id="pepass" type="number"
          value="${s.pass_count}" style="width:60px" min="1" /></label></div>`));
      body.appendChild(el(`<div class="row mt">
        <label class="toggle"><input type="checkbox" id="pesrs"
          ${s.use_srs ? "checked" : ""} /> 忘却曲線を使う</label>
        <label>出題数: <input id="pesize" type="number" value="${s.quiz_size}"
          style="width:60px" min="1" /></label></div>`));
      body.querySelector("#pedir").value = s.directions;
      const save = el(`<button class="btn good mt">保存</button>`);
      save.addEventListener("click", async () => {
        await api.put("/api/phrase-decks/" + d.id, {
          name: body.querySelector("#pen").value.trim() || d.name,
          settings: {
            directions: body.querySelector("#pedir").value,
            pass_count: parseInt(body.querySelector("#pepass").value, 10) || 2,
            use_srs: body.querySelector("#pesrs").checked,
            quiz_size: parseInt(body.querySelector("#pesize").value, 10) || 10,
          },
        });
        go("phrasedeck");
      });
      body.appendChild(save);

      body.appendChild(el(`<hr class="mt" />`));
      body.appendChild(el(`<h3>収録中のフレーズ (<span id="pcount">…</span>)</h3>`));
      const plist = el(`<div id="plist" class="mt"></div>`);
      body.appendChild(plist);
      const loadPhrases = async () => {
        const items = await api.get(`/api/phrase-decks/${d.id}/phrases`);
        body.querySelector("#pcount").textContent = items.length;
        plist.innerHTML = "";
        if (!items.length) {
          plist.appendChild(el(`<p class="muted">フレーズがありません。</p>`));
          return;
        }
        items.forEach((p) => {
          const row = el(`<div class="row"
            style="justify-content:space-between;padding:4px 0">
            <span>${escapeHtml(p.english)}
              <span class="muted">${escapeHtml(p.japanese || "")}</span></span>
            <button class="btn ghost del-btn" title="フレーズ帳から外す">🗑️</button>
            </div>`);
          row.querySelector("button").addEventListener("click", async () => {
            if (!confirm(`「${p.english}」をフレーズ帳から外しますか？`)) return;
            await api.del(`/api/phrase-decks/${d.id}/phrases/${p.id}`);
            loadPhrases();
          });
          plist.appendChild(row);
        });
      };
      loadPhrases();
    });
  }
}
