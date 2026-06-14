// Reusable both-direction quiz engine for words and phrases.
//
// For each item we ask BOTH directions:
//   en2ja: show/speak English  -> answer in Japanese
//   ja2en: show Japanese       -> answer in English (then speak it)
// Answers can be typed or spoken (per the global input-mode toggle).
// We auto-judge leniently, then let the user confirm ⭕/❌ before recording.

import { api } from "./api.js";
import * as speech from "./speech.js";

function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

function norm(s) {
  return (s || "")
    .toLowerCase()
    .replace(/[\s.,!?。、！？・/（）()「」"']/g, "")
    .trim();
}

function autoJudge(direction, answer, item) {
  const a = norm(answer);
  if (!a) return false;
  if (direction === "ja2en") {
    const target = norm(item.english);
    return a === target || target.includes(a) || a.includes(target);
  }
  // en2ja: compare against each Japanese sense segment.
  const segs = (item.japanese || "").split(/[・,，、/]/).map(norm);
  return segs.some((seg) => seg && (seg.includes(a) || a.includes(seg)));
}

// config: { container, items, kind:'word'|'phrase', appState, onDone }
export function quizRunner(config) {
  const { container, items, kind, appState, onDone } = config;
  const idField = kind === "word" ? "word_id" : "phrase_id";
  const endpoint = kind === "word"
    ? "/api/words/attempt" : "/api/phrases/attempt";

  // Build the question queue: both directions per item, shuffled per item.
  const queue = [];
  items.forEach((it) => {
    const dirs = Math.random() < 0.5
      ? ["en2ja", "ja2en"] : ["ja2en", "en2ja"];
    dirs.forEach((d) => queue.push({ item: it, direction: d }));
  });

  let idx = 0;
  let correctCount = 0;
  let skippedCount = 0; // ノーカウント（集計から除外）
  const voiceName = speech.pickRoundVoice(); // one voice for this round

  function finish() {
    container.innerHTML = "";
    const counted = queue.length - skippedCount;
    const pct = counted ? Math.round((correctCount / counted) * 100) : 0;
    const skipNote = skippedCount
      ? `<p class="muted">ノーカウント ${skippedCount} 問</p>` : "";
    container.appendChild(el(`
      <div class="card quiz-card">
        <h2>おつかれさまでした！</h2>
        <p class="num" style="font-size:34px;color:var(--accent-2)">${pct}%</p>
        <p class="muted">${correctCount} / ${counted} 正解</p>
        ${skipNote}
      </div>`));
    if (onDone) {
      onDone({ total: counted, correct: correctCount, pct,
        skipped: skippedCount });
    }
  }

  function render() {
    if (idx >= queue.length) { finish(); return; }
    const { item, direction } = queue[idx];
    const isEn2ja = direction === "en2ja";
    const prompt = isEn2ja ? item.english : item.japanese;
    const dirLabel = isEn2ja ? "英語 → 日本語" : "日本語 → 英語";
    const answerLang = isEn2ja ? "ja-JP" : "en-US";

    container.innerHTML = "";
    const card = el(`
      <div class="card quiz-card">
        <div class="row" style="justify-content:space-between">
          <span class="pill">${idx + 1} / ${queue.length}</span>
          <span class="now-voice">🔊 声: <b>${voiceName || "なし"}</b></span>
        </div>
        <div class="quiz-dir">${dirLabel}</div>
        <div class="quiz-prompt">${prompt}</div>
        <div class="row center" style="justify-content:center">
          <button class="btn ghost" id="hear">🔊 英語を聞く</button>
        </div>
        <div id="answerArea" class="mt"></div>
      </div>`);
    container.appendChild(card);

    // Speak the English prompt for en2ja immediately.
    if (isEn2ja) speech.speak(item.english);
    card.querySelector("#hear").addEventListener("click", () =>
      speech.speak(item.english));

    renderAnswerInput(card.querySelector("#answerArea"), item, direction,
      answerLang);
  }

  function renderAnswerInput(area, item, direction, lang) {
    const voiceMode = appState.inputMode === "voice";
    const inp = el(`<input id="ans" placeholder="答えを入力" style="width:50%" />`);
    const ok = el(`<button class="btn">✓ 回答</button>`);
    const dk = el(`<button class="btn ghost">🤔 わからない</button>`);
    const row = el(`<div class="row center" style="justify-content:center"></div>`);
    const submit = () => reveal(area, item, direction, inp.value);
    ok.addEventListener("click", submit);
    dk.addEventListener("click", () => reveal(area, item, direction, ""));
    inp.addEventListener("keydown", (e) => { if (e.key === "Enter") submit(); });

    if (voiceMode) {
      // Toggle recording: ON=録音開始, OFF=認識して回答。
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
          } catch (e) { area.appendChild(el(`<p class="muted">${e.message}</p>`)); }
        } else {
          recording = false;
          mic.disabled = true; mic.textContent = "認識中…";
          const text = await recorder.stop();
          inp.value = text;
          if (speech.isVoiceAutoSubmit()) {
            reveal(area, item, direction, text); // 即判定
          } else {
            mic.disabled = false; mic.textContent = "🎤 録音開始";
            mic.classList.remove("bad"); mic.classList.add("good");
            inp.focus();
          }
        }
      });
      row.append(mic, inp, ok, dk);
    } else {
      row.append(inp, ok, dk);
      setTimeout(() => inp.focus(), 0);
    }
    area.appendChild(row);
  }

  function reveal(area, item, direction, answer) {
    const auto = autoJudge(direction, answer, item);
    const correctText = direction === "ja2en" ? item.english : item.japanese;
    area.innerHTML = `
      <p class="muted">あなたの答え: ${answer || "（なし）"}</p>
      <p class="quiz-answer">正解: ${correctText}</p>
      <p class="muted">${item.english} — ${item.japanese}</p>
      ${item.example ? `<p class="muted">例: ${item.example}</p>` : ""}
      <p>${auto ? "✅ 自動判定: 正解" : "❌ 自動判定: 不正解"}（必要なら修正）</p>
      <div class="row center" style="justify-content:center"></div>`;
    speech.speak(item.english);
    const row = area.querySelector(".row");
    const ok = el(`<button class="btn good">⭕ 正解</button>`);
    const ng = el(`<button class="btn bad">❌ 不正解</button>`);
    const skip = el(`<button class="btn ghost">🚫 ノーカウント</button>`);
    ok.addEventListener("click", () => record(item, direction, true));
    ng.addEventListener("click", () => record(item, direction, false));
    skip.addEventListener("click", () => { skippedCount++; idx++; render(); });
    row.append(ok, ng, skip);
  }

  async function record(item, direction, correct) {
    try {
      const body = { [idField]: item.id, direction, correct };
      const r = await api.post(endpoint, body);
      if (correct) correctCount++;
      if (r && r.bonus_awarded) {
        const t = document.getElementById("toast");
        if (t) { t.textContent = "🎉 両方向クリア +5"; t.classList.add("show");
          setTimeout(() => t.classList.remove("show"), 1500); }
      }
    } catch (e) { /* ignore, still advance */ }
    idx++;
    render();
  }

  render();
}
