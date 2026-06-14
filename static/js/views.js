// All screen renderers. Each export takes the container element.

import { api } from "./api.js";
import * as speech from "./speech.js";
import { quizRunner } from "./quiz.js";
import {
  el, md, escapeHtml, toast, state, go, refreshCost, refreshAiState,
} from "./app.js";

// --- shared answer-input helper (voice or text) ----------------------------

function answerInput(onSubmit, { lang = "en-US", placeholder = "答えを入力" } = {}) {
  const wrap = el(`<div class="mt"></div>`);
  const ta = el(`<textarea placeholder="${placeholder}"></textarea>`);
  const row = el(`<div class="row"></div>`);
  const sendBtn = el(`<button class="btn">✓ 送信</button>`);
  sendBtn.addEventListener("click", () => onSubmit(ta.value));

  if (state.inputMode === "voice") {
    // Record → recognized text fills the box → review → ✓ send (or re-record).
    const mic = el(`<button class="btn good">🎤 録音</button>`);
    mic.addEventListener("click", async () => {
      mic.disabled = true; mic.textContent = "聞き取り中…";
      try {
        const said = await speech.listenOnce(lang);
        ta.value = ta.value ? ta.value + " " + said : said;
      } catch (e) { toast(e.message); }
      finally { mic.disabled = false; mic.textContent = "🎤 録音"; }
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
      <div class="bar mt"><span style="width:${v.avg_mastery}%"></span></div>
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
        <div class="num">${usage ? "$" + usage.today_cost_usd.toFixed(3) : "-"}</div>
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
  const data = await api.get("/api/learn/daily");
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
  render();
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

export async function vocab(root) {
  const words = await api.get("/api/words?sort=mastery");
  root.innerHTML = `
    <h1>英単語</h1>
    <p class="sub">両方向(英→日 / 日→英)で出題。習熟度・正答率・忘却曲線を管理。</p>
    <div class="row">
      <button class="btn" id="quiz">クイズ開始 (10語)</button>
    </div>
    <div class="card mt">
      <h2>単語を追加</h2>
      <div class="row">
        <input id="en" placeholder="English" />
        <input id="ja" placeholder="日本語" />
        <input id="pos" placeholder="品詞" style="width:80px" />
        <input id="ex" placeholder="例文" style="width:260px" />
        <button class="btn good" id="add">追加</button>
      </div>
    </div>
    <div class="card">
      <h2>単語一覧 (${words.length})</h2>
      <table><thead><tr>
        <th>英語</th><th>日本語</th><th>習熟度</th><th>正答率</th>
        <th>次回復習</th><th></th></tr></thead>
        <tbody id="rows"></tbody></table>
    </div>`;

  const rows = root.querySelector("#rows");
  words.forEach((w) => {
    const tr = el(`<tr>
      <td>${escapeHtml(w.english)}</td>
      <td>${escapeHtml(w.japanese)}</td>
      <td style="min-width:90px">
        <div class="bar"><span style="width:${w.mastery}%"></span></div>
        <small class="muted">${w.mastery}</small></td>
      <td>${w.accuracy == null ? "—" : w.accuracy + "%"}</td>
      <td class="muted">${w.next_review || "未"}</td>
      <td><button class="btn ghost" data-id="${w.id}">削除</button></td>
    </tr>`);
    tr.querySelector("button").addEventListener("click", async () => {
      await api.del("/api/words/" + w.id); go("vocab");
    });
    rows.appendChild(tr);
  });

  root.querySelector("#add").addEventListener("click", async () => {
    const en = root.querySelector("#en").value.trim();
    const ja = root.querySelector("#ja").value.trim();
    if (!en || !ja) { toast("英語と日本語は必須です"); return; }
    await api.post("/api/words", {
      english: en, japanese: ja,
      part_of_speech: root.querySelector("#pos").value,
      example: root.querySelector("#ex").value,
    });
    go("vocab");
  });

  root.querySelector("#quiz").addEventListener("click", async () => {
    const items = await api.get("/api/words/quiz?limit=10");
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
  const scenes = await api.get("/api/phrases/scenes");
  const list = await api.get("/api/phrases");
  root.innerHTML = `
    <h1>ミニフレーズ</h1>
    <p class="sub">場面別の短い表現。単語と同じく両方向＋忘却曲線で管理。</p>
    <div class="row">
      <button class="btn" id="quiz">クイズ開始 (10フレーズ)</button>
      <select id="scene"><option value="">全シーン</option>
        ${scenes.map((s) => `<option>${s}</option>`).join("")}</select>
    </div>
    <div class="card mt">
      <h2>フレーズを追加</h2>
      <div class="row">
        <input id="en" placeholder="English" style="width:260px" />
        <input id="ja" placeholder="日本語" style="width:220px" />
        <input id="sc" placeholder="シーン" style="width:120px" />
        <button class="btn good" id="add">追加</button>
      </div>
    </div>
    <div class="card">
      <h2>一覧 (${list.length})</h2>
      <table><thead><tr><th>英語</th><th>日本語</th><th>シーン</th>
        <th>習熟度</th><th></th></tr></thead><tbody id="rows"></tbody></table>
    </div>`;

  const renderRows = (items) => {
    const rows = root.querySelector("#rows"); rows.innerHTML = "";
    items.forEach((p) => {
      const tr = el(`<tr>
        <td>${escapeHtml(p.english)}</td>
        <td>${escapeHtml(p.japanese)}</td>
        <td><span class="pill">${escapeHtml(p.scene || "")}</span></td>
        <td><div class="bar"><span style="width:${p.mastery}%"></span></div></td>
        <td><button class="btn ghost" data-id="${p.id}">削除</button></td>
      </tr>`);
      tr.querySelector("button").addEventListener("click", async () => {
        await api.del("/api/phrases/" + p.id); go("phrases");
      });
      rows.appendChild(tr);
    });
  };
  renderRows(list);

  root.querySelector("#scene").addEventListener("change", async (e) => {
    const v = e.target.value;
    const items = await api.get("/api/phrases" + (v ? "?scene=" + encodeURIComponent(v) : ""));
    renderRows(items);
  });
  root.querySelector("#add").addEventListener("click", async () => {
    const en = root.querySelector("#en").value.trim();
    const ja = root.querySelector("#ja").value.trim();
    if (!en || !ja) { toast("英語と日本語は必須です"); return; }
    await api.post("/api/phrases", { english: en, japanese: ja,
      scene: root.querySelector("#sc").value });
    go("phrases");
  });
  root.querySelector("#quiz").addEventListener("click", async () => {
    const items = await api.get("/api/phrases/quiz?limit=10");
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
      const r = await api.post("/api/learn/generate", {
        area, field: root.querySelector("#field").value,
        instruction: root.querySelector("#inst").value,
      });
      if (!r.ok) { out.textContent = r.error; return; }
      out.innerHTML = md(r.body);
      const say = el(`<button class="btn ghost mt">🔊 読み上げ</button>`);
      say.addEventListener("click", () => speech.speak(r.body));
      out.appendChild(say);
      refreshCost();
    });
  };
}

export const reading = materialView(
  "リーディング", "分野別の長文と理解問題をAIが生成します。", "reading",
  ["一般", "新聞", "雑誌", "ビジネスメール", "技術文書", "API仕様書",
   "エラーメッセージ", "歴史", "文化"]);

export const news = (root) => materialView(
  "ニュース英語", "最新トピック風の記事を分野別に生成します。", "news",
  state.taxonomy.news_fields.length ? state.taxonomy.news_fields
    : ["政治", "経済", "AI", "IT"])(root);

export const literature = materialView(
  "文学", "古典・英文学の抜粋と語彙解説を生成します。", "literature",
  ["Shakespeare", "英文学", "古典文学"]);

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
    <p class="sub">AIの声: <b>${voice || "未取得"}</b>（毎回ランダム）</p>
    ${aiBadgeNote()}
    <div class="card">
      <div class="row">
        <select id="mode">
          <option value="scene">🎬 シーン会話</option>
          <option value="free">💬 自由会話</option>
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
  modeSel.addEventListener("change", () => {
    sceneSel.style.display = modeSel.value === "free" ? "none" : "";
  });

  function scene() {
    if (modeSel.value === "free") {
      return { grp: "自由会話", topic: "どんな話題でもOK・フリートーク" };
    }
    return { grp: root.querySelector("#grp").value, topic: topicSel.value };
  }

  const chat = root.querySelector("#chat");
  const history = [];
  function addMsg(role, text) {
    const m = el(`<div class="msg ${role}">
      <div class="who">${role === "user" ? "あなた" : "AI"}</div>
      <div class="body"></div></div>`);
    m.querySelector(".body").textContent = text;
    chat.appendChild(m); chat.scrollTop = chat.scrollHeight;
    return m.querySelector(".body");
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
      speech.speak(full);
    }
    refreshCost();
  }

  root.querySelector("#start").addEventListener("click", () => send("", true));

  const inputArea = root.querySelector("#inputArea");
  inputArea.appendChild(answerInput((t) => send(t),
    { lang: "en-US", placeholder: "英語で話しかける" }));
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
    const r = await api.post("/api/learn/generate",
      { area: "listening", field: label, instruction: "会話形式のスクリプト" });
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
      <p class="muted">ニックネームや個人情報は .env の USER_NICKNAME に記載してください
        （git管理ファイルには保存しません）。</p>
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
      <h2>API使用量・費用</h2>
      <p>累計 <b>$${usage.total_cost_usd.toFixed(4)}</b> /
         今日 <b>$${usage.today_cost_usd.toFixed(4)}</b> /
         呼び出し ${usage.calls} 回</p>
      <table><thead><tr><th>日時</th><th>機能</th><th>モデル</th>
        <th>in</th><th>out</th><th>費用</th></tr></thead><tbody>
        ${usage.recent.map((r) => `<tr><td class="muted">${r.created_at}</td>
          <td>${r.feature}</td><td>${r.model}</td><td>${r.prompt_tokens}</td>
          <td>${r.output_tokens}</td><td>$${r.cost_usd.toFixed(4)}</td></tr>`)
          .join("")}</tbody></table>
    </div>`;

  root.querySelector("#save").addEventListener("click", async () => {
    const body = { openai_model: root.querySelector("#model").value };
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
