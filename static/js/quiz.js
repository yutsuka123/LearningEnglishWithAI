// Reusable both-direction quiz engine for words and phrases.
//
// For each item we ask BOTH directions:
//   en2ja: show/speak English  -> answer in Japanese
//   ja2en: show Japanese       -> answer in English (then speak it)
// Answers can be typed or spoken (per the global input-mode toggle).
// We auto-judge leniently, then let the user confirm ⭕/❌ before recording.

import { api } from "./api.js";
import * as speech from "./speech.js";

// index.html/app.jsの読み込み順により、このモジュール評価時にはwindow.I18Nが
// 既にセットアップ済みのはず(app.jsのtxと同じ定義。app.jsからのimportは
// app.js⇔quiz.jsの循環参照になるためここでも同じ1行を定義)。
const tx = (key, vars) => (window.I18N ? window.I18N.t(key, vars) : key);

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
  const idField = config.idField || (kind === "word" ? "word_id" : "phrase_id");
  const endpoint = config.attemptEndpoint || (kind === "word"
    ? "/api/words/attempt" : "/api/phrases/attempt");
  // 出題方向: 'both'(両方向) | 'en2ja' | 'ja2en'
  const directions = config.directions || "both";

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
  let queue;
  if (directions === "both") {
    const firstHalf = [];
    const secondHalf = [];
    items.forEach((it) => {
      const dirs = Math.random() < 0.5
        ? ["en2ja", "ja2en"] : ["ja2en", "en2ja"];
      firstHalf.push({ item: it, direction: dirs[0] });
      secondHalf.push({ item: it, direction: dirs[1] });
    });
    queue = [...shuffle(firstHalf), ...shuffle(secondHalf)];
  } else {
    // 片方向のみ（en2ja or ja2en）。1語1問。
    queue = shuffle(items.map((it) => ({ item: it, direction: directions })));
  }

  let idx = 0;
  let correctCount = 0;
  let skippedCount = 0; // ノーカウント（集計から除外）
  const voiceName = speech.pickRoundVoice(); // one voice for this round

  function finish() {
    container.innerHTML = "";
    const counted = queue.length - skippedCount;
    const pct = counted ? Math.round((correctCount / counted) * 100) : 0;
    const skipNote = skippedCount
      ? `<p class="muted">${tx("quiz.noCountNote", { n: skippedCount })}</p>` : "";
    container.appendChild(el(`
      <div class="card quiz-card">
        <h2>${tx("quiz.doneTitle")}</h2>
        <p class="num" style="font-size:34px;color:var(--accent-2)">${pct}%</p>
        <p class="muted">${tx("quiz.correctOfCount", { correct: correctCount, counted })}</p>
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
    const dirLabel = isEn2ja ? tx("quiz.dirEnToJa") : tx("quiz.dirJaToEn");
    const answerLang = isEn2ja ? "ja-JP" : "en-US";

    container.innerHTML = "";
    const card = el(`
      <div class="card quiz-card">
        <div class="row" style="justify-content:space-between">
          <span class="pill">${idx + 1} / ${queue.length}</span>
          <span class="now-voice">🔊 ${tx("settings.voiceTestPrefix")}<b>${voiceName || tx("settings.voiceTestNone")}</b></span>
        </div>
        <div class="quiz-dir">${dirLabel}</div>
        <div class="quiz-prompt">${prompt}</div>
        <div class="row center" style="justify-content:center">
          <button class="btn ghost" id="hear">🔊 ${tx("quiz.hearEnglishBtn")}</button>
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
    const inp = el(`<input id="ans" placeholder="${tx("quiz.answerPlaceholder")}" style="width:50%" />`);
    const ok = el(`<button class="btn">✓ ${tx("quiz.answerBtn")}</button>`);
    const dk = el(`<button class="btn ghost">🤔 ${tx("quiz.dontKnowBtn")}</button>`);
    const row = el(`<div class="row center" style="justify-content:center"></div>`);
    const submit = () => reveal(area, item, direction, inp.value);
    ok.addEventListener("click", submit);
    dk.addEventListener("click", () => reveal(area, item, direction, ""));
    inp.addEventListener("keydown", (e) => { if (e.key === "Enter") submit(); });

    if (voiceMode) {
      // Toggle recording: ON=録音開始, OFF=認識して回答。
      let recorder = null;
      let recording = false;
      const mic = el(`<button class="btn good">🎤 ${tx("quiz.recordStartBtn")}</button>`);
      mic.addEventListener("click", async () => {
        if (!recording) {
          try {
            recorder = speech.createRecorder(lang);
            recorder.start();
            recording = true;
            mic.textContent = "⏹ " + tx("quiz.recordStopBtn");
            mic.classList.remove("good"); mic.classList.add("bad");
          } catch (e) { area.appendChild(el(`<p class="muted">${e.message}</p>`)); }
        } else {
          recording = false;
          mic.disabled = true; mic.textContent = tx("quiz.recognizing");
          const text = await recorder.stop();
          inp.value = text;
          if (speech.isVoiceAutoSubmit()) {
            reveal(area, item, direction, text); // 即判定
          } else {
            mic.disabled = false; mic.textContent = "🎤 " + tx("quiz.recordStartBtn");
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
      <p class="muted">${tx("quiz.yourAnswer")}${answer || tx("quiz.noneAnswer")}</p>
      <p class="quiz-answer">${tx("quiz.correctAnswerLabel")}${correctText}</p>
      <p class="muted">${item.english} — ${item.japanese}</p>
      <div id="exArea" class="mt"></div>
      <p>${auto ? "✅ " + tx("quiz.autoJudgeCorrect") : "❌ " + tx("quiz.autoJudgeWrong")}${tx("quiz.autoJudgeNote")}</p>
      <div class="row center" style="justify-content:center"></div>`;
    speech.speak(item.english);
    renderExample(area.querySelector("#exArea"), item);
    const row = area.querySelector(".row");
    const ok = el(`<button class="btn good">⭕ ${tx("quiz.correctBtn")}</button>`);
    const vague = el(`<button class="btn" style="background:var(--warn);color:#3a2600">🤔 ${tx("quiz.vagueBtn")}</button>`);
    const ng = el(`<button class="btn bad">❌ ${tx("quiz.wrongBtn")}</button>`);
    const known = el(`<button class="btn" style="background:var(--accent-2);color:#fff">✅ ${tx("quiz.knownBtn")}</button>`);
    const skip = el(`<button class="btn ghost">🚫 ${tx("quiz.noCountBtn")}</button>`);
    ok.addEventListener("click", () => record(item, direction, "correct"));
    vague.addEventListener("click", () => record(item, direction, "vague"));
    ng.addEventListener("click", () => record(item, direction, "wrong"));
    known.addEventListener("click", () => markKnown(item));
    skip.addEventListener("click", () => { skippedCount++; idx++; render(); });
    row.append(ok, vague, ng, known, skip);
  }

  function renderExample(box, item) {
    // 例文（フレーズ）＋読み上げ＋日本語訳。例文が無ければAIで生成。
    const phrase = (item.example || "").trim();
    box.innerHTML = "";
    const line = el(`<p class="muted">${phrase
      ? tx("quiz.exampleLabel") + phrase : tx("quiz.noExample")}</p>`);
    const tools = el(`<div class="row center" style="justify-content:center"></div>`);
    const say = el(`<button class="btn ghost">🔊 ${tx("quiz.hearExampleBtn")}</button>`);
    const jp = el(`<button class="btn ghost">🌐 ${tx("quiz.exampleTranslationBtn")}</button>`);
    const gen = el(`<button class="btn ghost">📝 ${tx("quiz.makeExampleBtn")}</button>`);
    const tr = el(`<p class="muted"></p>`);

    const speakable = () => line.dataset.en || phrase;
    say.addEventListener("click", () => {
      const t = speakable(); if (t) speech.speak(t);
    });
    jp.addEventListener("click", async () => {
      const t = speakable(); if (!t) return;
      tr.textContent = tx("quiz.translating");
      try {
        const r = await api.post("/api/learn/translate", { text: t });
        tr.textContent = r.ok
          ? tx("quiz.translationLabel") + r.text
          : (r.error || tx("quiz.translationFailed"));
      } catch (e) { tr.textContent = tx("quiz.translationFailed"); }
    });
    gen.addEventListener("click", async () => {
      line.textContent = tx("quiz.generatingExample");
      try {
        const r = await api.post("/api/learn/example",
          { word: item.english });
        if (r.ok && r.english) {
          line.textContent = tx("quiz.exampleLabel") + r.english;
          line.dataset.en = r.english;
          if (r.japanese) tr.textContent = tx("quiz.translationLabel") + r.japanese;
          tools.append(say, jp);
          gen.remove();
        } else { line.textContent = r.error || tx("quiz.exampleGenFailed"); }
      } catch (e) { line.textContent = tx("quiz.exampleGenFailed"); }
    });

    box.append(line);
    if (phrase) { tools.append(say, jp); }
    else { tools.append(gen); }
    box.append(tools, tr);
  }

  async function markKnown(item) {
    // 「覚えた」: mastery を満点(200)にして次へ。正解として集計。
    const base = kind === "word" ? "/api/words" : "/api/phrases";
    try {
      await api.post(`${base}/${item.id}/known`, { known: true });
      correctCount++;
      const t = document.getElementById("toast");
      if (t) {
        t.textContent = "✅ " + tx("quiz.knownRegistered");
        t.classList.add("show");
        setTimeout(() => t.classList.remove("show"), 1500);
      }
    } catch (e) {
      // 2026-09-18修正: 従来は失敗しても完全に無言で次へ進んでいたため、
      // 採点(mastery加点)が保存されていないことにユーザーが気づけなかった
      // (ユーザー要望「その他のそうさも離脱を防ぐ重要な情報」への対応で
      // 監査した際に発見)。保存されなかったことが分かるようにする。
      const t = document.getElementById("toast");
      if (t) { t.textContent = "⚠️ " + tx("quiz.recordFailed");
        t.classList.add("show");
        setTimeout(() => t.classList.remove("show"), 2200); }
    }
    idx++;
    render();
  }

  async function record(item, direction, result) {
    try {
      const correct = result === "correct";
      const body = { [idField]: item.id, direction, correct, result };
      const r = await api.post(endpoint, body);
      if (correct) correctCount++;
      if (r && r.bonus_awarded) {
        const t = document.getElementById("toast");
        if (t) { t.textContent = "🎉 " + tx("quiz.bothDirectionsBonus"); t.classList.add("show");
          setTimeout(() => t.classList.remove("show"), 1500); }
      }
    } catch (e) {
      // markKnownと同じ理由(2026-09-18修正)。
      const t = document.getElementById("toast");
      if (t) { t.textContent = "⚠️ " + tx("quiz.recordFailed");
        t.classList.add("show");
        setTimeout(() => t.classList.remove("show"), 2200); }
    }
    idx++;
    render();
  }

  render();
}
