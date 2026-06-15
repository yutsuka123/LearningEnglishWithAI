// All screen renderers. Each export takes the container element.

import { api } from "./api.js";
import * as speech from "./speech.js";
import { quizRunner } from "./quiz.js";
import {
  el, md, escapeHtml, toast, state, go, refreshCost, refreshAiState,
  showBanned, setShowBanned, testBanned, setTestBanned,
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
function readAloudBar(getText) {
  const bar = el(`<div class="row mt"></div>`);
  const play = el(`<button class="btn ghost">🔊 英文を読み上げ</button>`);
  const stop = el(`<button class="btn ghost">⏹ 停止</button>`);
  play.addEventListener("click", () => speech.speak(englishOnly(getText())));
  stop.addEventListener("click", () => speech.stopSpeaking());
  bar.append(play, stop, playbackSpeedControl());
  return bar;
}

// --- Dashboard --------------------------------------------------------------

export async function dashboard(root) {
  const p = await api.get("/api/system/progress");
  const usage = await api.get("/api/system/usage");
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

  root.innerHTML = `
    <h1>ダッシュボード</h1>
    <p class="sub">今日の学習を始めましょう。1回 約10分でOK。</p>

    <div class="grid cols-3">
      <div class="card stat">
        <div class="num">${p.toeic_estimate}</div>
        <div class="lbl">TOEIC換算(目安)</div></div>
      <div class="card stat">
        <div class="num">${p.overall_avg_mastery}</div>
        <div class="lbl">平均習熟度(単語+フレーズ)</div></div>
      <div class="card stat">
        <div class="num">${usage ? "¥" + usage.today_cost_jpy : "-"}</div>
        <div class="lbl">今日のAI費用</div></div>
    </div>

    <div class="card">
      <h2>単語の状況</h2>
      <div class="grid cols-3">
        <div class="stat"><div class="num">${w.total}</div>
          <div class="lbl">全件数</div></div>
        <div class="stat"><div class="num">${w.studied}</div>
          <div class="lbl">学習数(出題済み)</div></div>
        <div class="stat"><div class="num">${w.mastered}</div>
          <div class="lbl">習得数(80+)</div></div>
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
        <button class="btn" id="startDaily">⏱️ デイリー(10分)を始める</button>
        <button class="btn secondary" id="goConv">🗣️ 英会話する</button>
      </div>
    </div>

    <h2>項目別の習熟度</h2>
    <div class="grid cols-2">${areaCards}</div>`;
  root.querySelector("#startDaily").addEventListener("click", () => go("daily"));
  root.querySelector("#goConv").addEventListener("click",
    () => go("conversation"));
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
    out.querySelector("#say").addEventListener("click", () => speech.speak(r.body));
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
    await onDel();
    toast("削除しました");
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

// 単語の例文ポップアップ: 英語・訳・例文＋例文の再生(男女声)。例文が無ければ
// AIで生成（コストガードあり）。
function showWordExample(w) {
  openModal(w.english, (body) => {
    body.appendChild(el(`<p class="quiz-answer">${escapeHtml(w.english)}
      <span class="muted">${escapeHtml(w.japanese || "")}</span></p>`));
    const exLine = el(`<p>${w.example
      ? "例文: " + escapeHtml(w.example) : "（例文なし）"}</p>`);
    body.appendChild(exLine);
    const speedRow = el(`<div class="row">${speedSelect("exSpeed")}</div>`);
    const getMode = () => body.querySelector("#exSpeed").value;
    const tools = el(`<div class="row"></div>`);
    if (w.example) {
      tools.appendChild(voiceButtonsItem(
        "word", w.id, "example", () => w.example, getMode));
    } else {
      const gen = el(`<button class="btn ghost">📝 例文を作る(AI)</button>`);
      gen.addEventListener("click", async () => {
        exLine.textContent = "生成中…";
        try {
          const r = await api.post("/api/learn/example", { word: w.english });
          if (r.ok && r.english) {
            w.example = r.english;
            exLine.textContent = "例文: " + r.english;
            tools.innerHTML = "";
            tools.appendChild(voiceButtonsItem(
              "word", w.id, "example", () => w.example, getMode));
            refreshCost();
          } else { exLine.textContent = r.error || "生成失敗"; }
        } catch (e) { exLine.textContent = "生成失敗"; }
      });
      tools.appendChild(gen);
    }
    body.append(speedRow, tools);
  });
}

export async function vocab(root) {
  const facets = await api.get(
    "/api/words/facets" + (showBanned() ? "?include_banned=true" : ""));
  root.innerHTML = `
    <h1>英単語</h1>
    <p class="sub">両方向(英→日 / 日→英)で出題。習熟度・正答率・忘却曲線を管理。</p>
    <div class="row">
      <button class="btn" id="quiz">クイズ開始 (10語)</button>
      <span class="muted">単語の追加・一括インポートは ⚙️設定 に移動しました。</span>
    </div>
    <div class="card">
      <h2 id="listTitle">単語一覧</h2>
      <div class="row">
        <input id="kw" placeholder="🔍 英語・日本語で検索" style="width:200px" />
        <select id="fDomain"><option value="">全分野</option>
          ${facets.domains.map((d) =>
            `<option>${escapeHtml(d)}</option>`).join("")}</select>
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
        <select id="fSort">
          <option value="mastery">並び替え: 習熟度 ↑</option>
          <option value="accuracy">並び替え: 正答率 ↓</option>
          <option value="english">並び替え: 英語 A→Z</option>
          <option value="level">並び替え: レベル</option>
          <option value="domain">並び替え: 分野</option>
          <option value="recent">並び替え: 最近の学習</option>
        </select>
        <select id="fMastered" title="覚えた語の表示">
          <option value="">覚えた: 含む</option>
          <option value="hide">覚えた: 隠す</option>
          <option value="only">覚えた: のみ</option>
        </select>
        ${speedSelect("wSpeed", false)}
        ${pageSizeSelect("wPage")}
        <label class="toggle" title="禁止用語(注意喚起)を一覧に表示">
          <input type="checkbox" id="showBanned" ${showBanned() ? "checked" : ""} />
          🔞 禁止用語も表示</label>
      </div>
      <table class="mt"><thead><tr>
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
        <td>${escapeHtml(w.english)}</td>
        <td>${escapeHtml(w.japanese)}</td>
        <td class="muted">${w.level || ""}</td>
        <td>${w.domain ? `<span class="pill">${escapeHtml(w.domain)}</span>`
          : ""}</td>
        <td style="min-width:80px" data-mc="1">${masteryCell(w)}</td>
        <td>${w.accuracy == null ? "—" : w.accuracy + "%"}</td>
        <td><div class="ops-cell"></div></td>
      </tr>`);
      // 番号(ID)で再生。保存済みなら無料、無ければ合成して保存。
      tr.firstElementChild.appendChild(voiceButtonsItem(
        "word", w.id, "word", () => w.english,
        () => root.querySelector("#wSpeed").value));
      const ops = tr.querySelector("td:last-child .ops-cell");
      const mc = tr.querySelector("[data-mc]");
      const ex = el(`<button class="btn good">例文</button>`);
      ex.addEventListener("click", () => showWordExample(w));
      const repaint = () => { mc.innerHTML = masteryCell(w); };
      const vague = vagueButton("/api/words", w, repaint);
      const known = knownButton("/api/words", w, repaint);
      const del = deleteButton(w.english, async () => {
        await api.del("/api/words/" + w.id); load();
      });
      ops.append(ex, vague, known, del);
      rowsBody.appendChild(tr);
    });
  };

  // 分野/レベル/並び替え/禁止表示はサーバ側、キーワードはクライアント側。
  const load = async () => {
    const q = new URLSearchParams({ sort: root.querySelector("#fSort").value });
    const d = root.querySelector("#fDomain").value;
    if (d) q.set("domain", d);
    const lmin = root.querySelector("#fLevelMin").value;
    const lmax = root.querySelector("#fLevelMax").value;
    if (lmin) q.set("level_min", lmin);
    if (lmax) q.set("level_max", lmax);
    if (root.querySelector("#fOutRange").checked) q.set("out_of_range", "true");
    const ms = root.querySelector("#fMastered").value;
    if (ms) q.set("mastered", ms);
    if (showBanned()) q.set("include_banned", "true");
    const words = await api.get("/api/words?" + q.toString());
    const term = kw.value.trim().toLowerCase();
    curWords = term ? words.filter((w) =>
      w.english.toLowerCase().includes(term)
      || (w.japanese || "").toLowerCase().includes(term)) : words;
    wPage = 0;
    paint();
  };
  ["#fDomain", "#fLevelMin", "#fLevelMax", "#fOutRange", "#fSort",
   "#fMastered"].forEach((id) =>
    root.querySelector(id).addEventListener("change", load));
  root.querySelector("#wPage").addEventListener("change", () => {
    wPage = 0; paint();
  });
  // 禁止表示の切替で分野フィルタの候補(禁止用語)も変わるので作り直す。
  root.querySelector("#showBanned").addEventListener("change", (e) => {
    setShowBanned(e.target.checked); go("vocab");
  });
  kw.addEventListener("input", load);
  load();

  root.querySelector("#quiz").addEventListener("click", async () => {
    const tb = testBanned() ? "&include_banned=true" : "";
    const items = await api.get("/api/words/quiz?limit=10" + tb);
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
  const scenes = await api.get("/api/phrases/scenes" + (sb ? "?" + sb : ""));
  const list = await api.get("/api/phrases" + (sb ? "?" + sb : ""));
  root.innerHTML = `
    <h1>ミニフレーズ</h1>
    <p class="sub">場面別の短い表現。単語と同じく両方向＋忘却曲線で管理。</p>
    <div class="row">
      <button class="btn" id="quiz">クイズ開始 (10フレーズ)</button>
      <select id="scene"><option value="">全シーン</option>
        ${scenes.map((s) => `<option>${s}</option>`).join("")}</select>
      <label class="toggle" title="禁止用語(注意喚起)を一覧に表示">
        <input type="checkbox" id="showBanned" ${showBanned() ? "checked" : ""} />
        🔞 禁止用語も表示</label>
    </div>
    <div class="row">
      <span class="muted">フレーズの追加は ⚙️設定 に移動しました。</span>
    </div>
    <div class="card">
      <h2 id="listTitle">一覧 (${list.length})</h2>
      <div class="row">
        <input id="kw" placeholder="🔍 英語・日本語で検索" style="width:200px" />
        <select id="fSort">
          <option value="mastery">並び替え: 習熟度 ↑</option>
          <option value="accuracy">並び替え: 正答率 ↓</option>
          <option value="english">並び替え: 英語 A→Z</option>
          <option value="scene">並び替え: シーン</option>
          <option value="recent">並び替え: 最近の学習</option>
        </select>
        <select id="fMastered" title="覚えたフレーズの表示">
          <option value="">覚えた: 含む</option>
          <option value="hide">覚えた: 隠す</option>
          <option value="only">覚えた: のみ</option>
        </select>
        ${speedSelect("pSpeed")}
        ${pageSizeSelect("pPage")}
      </div>
      <table class="mt"><thead><tr><th>再生</th><th>英語</th><th>日本語</th>
        <th>シーン</th><th>習熟度</th><th>操作</th></tr></thead>
        <tbody id="rows"></tbody></table>
      <div id="pager" class="mt"></div>
    </div>`;

  const title = root.querySelector("#listTitle");
  const kw = root.querySelector("#kw");
  const pagerEl = root.querySelector("#pager");
  let curList = [];
  let pPage = 0;

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
        <td>${escapeHtml(p.english)}</td>
        <td>${escapeHtml(p.japanese)}</td>
        <td><span class="pill">${escapeHtml(p.scene || "")}</span></td>
        <td data-mc="1">${masteryCell(p)}</td>
        <td><div class="ops-cell"></div></td>
      </tr>`);
      tr.firstElementChild.appendChild(voiceButtonsItem(
        "phrase", p.id, "phrase", () => p.english,
        () => root.querySelector("#pSpeed").value));
      const ops = tr.querySelector("td:last-child .ops-cell");
      const mc = tr.querySelector("[data-mc]");
      const repaint = () => { mc.innerHTML = masteryCell(p); };
      const vague = vagueButton("/api/phrases", p, repaint);
      const known = knownButton("/api/phrases", p, repaint);
      const del = deleteButton(p.english, async () => {
        await api.del("/api/phrases/" + p.id); go("phrases");
      });
      ops.append(vague, known, del);
      rows.appendChild(tr);
    });
  };
  curList = list; pPage = 0; paint();

  // シーン・並び替え・禁止表示はサーバ側、キーワードはクライアント側。
  const load = async () => {
    const q = new URLSearchParams({ sort: root.querySelector("#fSort").value });
    const v = root.querySelector("#scene").value;
    if (v) q.set("scene", v);
    const ms = root.querySelector("#fMastered").value;
    if (ms) q.set("mastered", ms);
    if (showBanned()) q.set("include_banned", "true");
    const items = await api.get("/api/phrases?" + q.toString());
    const term = kw.value.trim().toLowerCase();
    curList = term ? items.filter((p) =>
      p.english.toLowerCase().includes(term)
      || (p.japanese || "").toLowerCase().includes(term)) : items;
    pPage = 0;
    paint();
  };
  root.querySelector("#scene").addEventListener("change", load);
  root.querySelector("#fSort").addEventListener("change", load);
  root.querySelector("#fMastered").addEventListener("change", load);
  root.querySelector("#pPage").addEventListener("change", () => {
    pPage = 0; paint();
  });
  // 禁止表示の切替はシーン候補も変わるので画面を作り直す。
  root.querySelector("#showBanned").addEventListener("change", (e) => {
    setShowBanned(e.target.checked); go("phrases");
  });
  kw.addEventListener("input", load);

  root.querySelector("#quiz").addEventListener("click", async () => {
    const tb = testBanned() ? "&include_banned=true" : "";
    const items = await api.get("/api/phrases/quiz?limit=10" + tb);
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

function materialView(title, sub, area, fields) {
  return async function (root) {
    root.innerHTML = `
      <h1>${title}</h1>
      <p class="sub">${sub}</p>
      ${aiBadgeNote()}
      <div class="card">
        <div class="row">
          <select id="field">${fields.map((f) =>
            `<option>${f}</option>`).join("")}</select>
          <input id="inst" placeholder="追加指示(任意)" style="width:280px" />
          <button class="btn" id="gen" ${state.aiEnabled ? "" : "disabled"}>
            生成</button>
        </div>
      </div>
      <div class="card"><div id="out" class="md">
        左上で分野を選んで「生成」を押してください。</div></div>`;
    root.querySelector("#gen").addEventListener("click", async () => {
      const out = root.querySelector("#out");
      out.textContent = "生成中…";
      // 文学/ニュースのトピックは適切な生成プロンプト(area)に振り分け。
      const field = root.querySelector("#field").value;
      let genArea = area;
      if (field.startsWith("文学(")) genArea = "literature";
      else if (field.startsWith("ニュース(")) genArea = "news";
      const r = await api.post("/api/learn/generate", {
        area: genArea, field,
        instruction: root.querySelector("#inst").value,
      });
      if (!r.ok) { out.textContent = r.error; return; }
      out.innerHTML = "";
      out.appendChild(readAloudBar(() => r.body)); // controls at top
      const body = el(`<div class="md mt"></div>`);
      body.innerHTML = md(r.body);
      out.appendChild(body);
      out.appendChild(readAloudBar(() => r.body)); // and at bottom
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
  ])(root);

// --- Writing ----------------------------------------------------------------

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
  const voice = speech.pickRoundVoice();
  root.innerHTML = `
    <h1>英会話</h1>
    <p class="sub">AIの声: <b id="voiceName">${voice || "未取得"}</b>
      <button class="btn ghost" id="changeVoice"
        style="padding:2px 8px">🔁 声を変える</button></p>
    ${aiBadgeNote()}
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
      <p id="freeHelp" class="muted" style="display:none">
        日本語でもOK。単語・フレーズ・リスニング・ライティング、何でも相談できます。
        「録音」で話し、「わからない」で答えを教えてもらえます。</p>
      <div class="chat" id="chat"></div>
      <div id="inputArea" class="mt"></div>
    </div>`;

  const modeSel = root.querySelector("#mode");
  const sceneSel = root.querySelector("#sceneSel");
  const topicSel = root.querySelector("#topic");
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

  // 声を変えるボタン: 別の声をランダムに選び直して表示。
  root.querySelector("#changeVoice").addEventListener("click", () => {
    const v = speech.pickRoundVoice();
    root.querySelector("#voiceName").textContent = v || "なし";
    toast("声: " + (v || "なし"));
  });

  function scene() {
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
    const m = el(`<div class="msg ${role}">
      <div class="who">${role === "user" ? "あなた" : "AI"}</div>
      <div class="body"></div></div>`);
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
      m.append(tools, tr);
    }
    chat.appendChild(m); chat.scrollTop = chat.scrollHeight;
    return body;
  }

  function addHelper(label, text) {
    const m = el(`<div class="msg ai" style="background:var(--panel)">
      <div class="who">${label}</div><div class="md"></div></div>`);
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
      grp: s.grp, topic: s.topic, history,
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
            ? await speech.createAIRecorder()
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
        <input id="theme" placeholder="テーマ(任意)" style="width:160px" />
        <label class="toggle">速度
          <input type="range" id="rate" min="0.6" max="1.2" step="0.05" value="0.95" />
        </label>
        <button class="btn" id="gen" ${state.aiEnabled ? "" : "disabled"}>
          スクリプト生成</button>
      </div>
      <div id="out" class="md mt"></div>
      <div class="row mt">
        <label class="toggle">理解度
          <input type="range" id="comp" min="0" max="100" value="50" /></label>
        <input id="weak" placeholder="苦手だった点" style="width:240px" />
        <button class="btn good" id="save">記録</button>
      </div>
    </div>`;
  let scriptText = "";
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
    let body;
    if (g) {
      body = {
        area: g.area, field: theme ? `${g.field}・${theme}` : g.field,
        instruction: g.inst + (theme ? `（テーマ: ${theme}）` : ""),
      };
    } else {
      body = {
        area: "listening", field: theme ? `${label}・${theme}` : label,
        instruction: "会話形式のスクリプト" +
          (theme ? `（テーマ: ${theme}）` : ""),
      };
    }
    const r = await api.post("/api/learn/generate", body);
    if (!r.ok) { out.textContent = r.error; return; }
    scriptText = r.body; out.innerHTML = md(r.body);
    const play = el(`<button class="btn mt">🔊 再生</button>`);
    play.addEventListener("click", () => speech.speak(scriptText,
      { rate: parseFloat(root.querySelector("#rate").value) }));
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
}

// --- Assessment + material generation --------------------------------------

export async function assess(root) {
  const p = await api.get("/api/system/progress");
  const w = p.words;
  root.innerHTML = `
    <h1>判定・教材作成</h1>
    <p class="sub">好きなタイミングで実力を判定し、苦手に合わせて教材を追加できます。</p>

    <div class="card">
      <h2>🎯 レベル判定</h2>
      <div class="grid cols-3">
        <div class="stat"><div class="num">${p.toeic_estimate}</div>
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
      <h2>memory.md（学習方針・目標・苦手）</h2>
      <textarea id="mem" style="min-height:160px">${escapeHtml(mem.content)}</textarea>
      <button class="btn secondary mt" id="saveMem">memoryを保存</button>
    </div>
    <div class="card">
      <h2>study_log.md</h2>
      <div class="md" style="max-height:320px;overflow:auto">${md(log.content)}</div>
    </div>`;

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
    await api.put("/api/system/memory",
      { content: root.querySelector("#mem").value });
    toast("memory.md を保存しました");
  });
}

// --- Settings (API key, model, nickname note, voices, usage) ---------------

export async function settings(root) {
  const s = await api.get("/api/system/settings");
  const usage = await api.get("/api/system/usage");
  root.innerHTML = `
    <h1>設定</h1>
    <p class="sub">APIキーは設定後 .env に保存されます（git管理外）。</p>
    <div class="card">
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
      <h2>音声入力</h2>
      <label class="toggle">
        <input type="checkbox" id="autoSubmit"
          ${speech.isVoiceAutoSubmit() ? "checked" : ""} />
        録音停止したら自動で判定/送信する（OFFなら内容を確認してから送信）</label>
    </div>
    <div class="card">
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
    <div class="card">
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
    <div class="card">
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

  root.querySelector("#save").addEventListener("click", async () => {
    const body = {
      openai_model: root.querySelector("#model").value,
      openai_quality_model: root.querySelector("#qmodel").value,
    };
    const key = root.querySelector("#key").value.trim();
    if (key) body.openai_api_key = key;
    await api.put("/api/system/settings", body);
    toast("保存しました"); await refreshAiState(); go("settings");
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
  const [list, facets] = await Promise.all([
    api.get("/api/decks"),
    api.get("/api/words/facets?include_banned=true"),
  ]);
  root.innerHTML = `
    <h1>単語帳</h1>
    <p class="sub">分野・レベルから自分用の単語帳(デッキ)を作って学習。
      デッキ別に出題方向や合格条件を設定できます。</p>
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
        <label class="toggle"><input type="checkbox" id="dbanned" />
          🔞 禁止用語も含める</label>
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
      const pct = d.total ? Math.round(d.done / d.total * 100) : 0;
      const dirLabel = { both: "両方向", en2ja: "英→日", ja2en: "日→英" }[
        d.settings.directions] || "両方向";
      const card = el(`<div class="card">
        <div class="row" style="justify-content:space-between">
          <b>${escapeHtml(d.name)}</b>
          <span class="muted">${d.done}/${d.total} 習得 (${pct}%)</span></div>
        <div class="bar mt"><span style="width:${pct}%"></span></div>
        <div class="muted mt">${dirLabel} ・ ${d.settings.pass_count}回正解で習得
          ・ 忘却曲線${d.settings.use_srs ? "ON" : "OFF"}
          ・ 出題${d.settings.quiz_size}</div>
        <div class="row mt">
          <button class="btn" data-act="study">▶ 学習する</button>
          <button class="btn ghost" data-act="settings">⚙️ 設定</button>
          <button class="btn ghost del-btn" data-act="del"
            title="削除">🗑️</button></div></div>`);
      card.querySelector('[data-act="study"]')
        .addEventListener("click", () => studyDeck(d));
      card.querySelector('[data-act="settings"]')
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
        include_banned: root.querySelector("#dbanned").checked,
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

  async function studyDeck(d) {
    const q = await api.get(`/api/decks/${d.id}/quiz`);
    if (!q.items.length) {
      toast("この単語帳は全て習得済みです🎉"); return;
    }
    root.innerHTML = `<h1>単語帳: ${escapeHtml(d.name)}</h1>`;
    const holder = el(`<div></div>`); root.appendChild(holder);
    quizRunner({
      container: holder, items: q.items, kind: "word", appState: state,
      directions: q.settings.directions,
      attemptEndpoint: `/api/decks/${d.id}/attempt`,
      onDone: () => {
        const b = el(`<button class="btn mt">単語帳へ戻る</button>`);
        b.addEventListener("click", () => go("deck")); holder.appendChild(b);
      },
    });
  }

  function editDeck(d) {
    openModal("設定: " + d.name, (body) => {
      const s = d.settings;
      body.appendChild(el(`<div class="row">
        <label>名前: <input id="en" value="${escapeHtml(d.name)}"
          style="width:200px" /></label></div>`));
      body.appendChild(el(`<div class="row mt">
        <label>出題方向: <select id="edir">
          <option value="both">両方向</option>
          <option value="en2ja">英→日</option>
          <option value="ja2en">日→英</option></select></label>
        <label>N回正解で習得: <input id="epass" type="number"
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
    });
  }
}
