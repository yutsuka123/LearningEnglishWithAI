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

  // Build the question queue so the two directions of the SAME item are well
  // separated: first half = one direction per item, second half = the other.
  // Each half is shuffled independently. → 同じ単語の和英/英和が連続しない。
  const shuffle = (arr) => {
    for (let i = arr.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [arr[i], arr[j]] = [arr[j], arr[i]];
    }
    return arr;
  };
  const firstHalf = [];
  const secondHalf = [];
  items.forEach((it) => {
    const dirs = Math.random() < 0.5
      ? ["en2ja", "ja2en"] : ["ja2en", "en2ja"];
    firstHalf.push({ item: it, direction: dirs[0] });
    secondHalf.push({ item: it, direction: dirs[1] });
  });
  const queue = [...shuffle(firstHalf), ...shuffle(secondHalf)];

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
      <div id="exArea" class="mt"></div>
      <p>${auto ? "✅ 自動判定: 正解" : "❌ 自動判定: 不正解"}（必要なら修正）</p>
      <div class="row center" style="justify-content:center"></div>`;
    speech.speak(item.english);
    renderExample(area.querySelector("#exArea"), item);
    const row = area.querySelector(".row");
    const ok = el(`<button class="btn good">⭕ 正解</button>`);
    const vague = el(`<button class="btn" style="background:var(--warn);color:#3a2600">🤔 うろ覚え</button>`);
    const ng = el(`<button class="btn bad">❌ 不正解</button>`);
    const skip = el(`<button class="btn ghost">🚫 ノーカウント</button>`);
    ok.addEventListener("click", () => record(item, direction, "correct"));
    vague.addEventListener("click", () => record(item, direction, "vague"));
    ng.addEventListener("click", () => record(item, direction, "wrong"));
    skip.addEventListener("click", () => { skippedCount++; idx++; render(); });
    row.append(ok, vague, ng, skip);
  }

  function renderExample(box, item) {
    // 例文（フレーズ）＋読み上げ＋日本語訳。例文が無ければAIで生成。
    const phrase = (item.example || "").trim();
    box.innerHTML = "";
    const line = el(`<p class="muted">${phrase
      ? "例文: " + phrase : "（例文なし）"}</p>`);
    const tools = el(`<div class="row center" style="justify-content:center"></div>`);
    const say = el(`<button class="btn ghost">🔊 例文を聞く</button>`);
    const jp = el(`<button class="btn ghost">🌐 例文の訳</button>`);
    const gen = el(`<button class="btn ghost">📝 例文を作る</button>`);
    const tr = el(`<p class="muted"></p>`);

    const speakable = () => line.dataset.en || phrase;
    say.addEventListener("click", () => {
      const t = speakable(); if (t) speech.speak(t);
    });
    jp.addEventListener("click", async () => {
      const t = speakable(); if (!t) return;
      tr.textContent = "翻訳中…";
      try {
        const r = await api.post("/api/learn/translate", { text: t });
        tr.textContent = r.ok ? "訳: " + r.text : (r.error || "失敗");
      } catch (e) { tr.textContent = "失敗"; }
    });
    gen.addEventListener("click", async () => {
      line.textContent = "例文を生成中…";
      try {
        const r = await api.post("/api/learn/example",
          { word: item.english });
        if (r.ok && r.english) {
          line.textContent = "例文: " + r.english;
          line.dataset.en = r.english;
          if (r.japanese) tr.textContent = "訳: " + r.japanese;
          tools.append(say, jp);
          gen.remove();
        } else { line.textContent = r.error || "生成失敗"; }
      } catch (e) { line.textContent = "生成失敗"; }
    });

    box.append(line);
    if (phrase) { tools.append(say, jp); }
    else { tools.append(gen); }
    box.append(tools, tr);
  }

  async function record(item, direction, result) {
    try {
      const correct = result === "correct";
      const body = { [idField]: item.id, direction, correct, result };
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
