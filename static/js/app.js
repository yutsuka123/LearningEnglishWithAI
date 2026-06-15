import { api } from "./api.js";
import * as speech from "./speech.js";
import { quizRunner } from "./quiz.js";
import * as views from "./views.js";

// ---------------------------------------------------------------------------
// Global state
// ---------------------------------------------------------------------------

export const state = {
  inputMode: localStorage.getItem("inputMode") || "text", // 'text' | 'voice'
  aiEnabled: false,
  taxonomy: { news_fields: [], accents: [], models: [] },
};

const TABS = [
  ["dashboard", "🏠 ダッシュボード"],
  ["daily", "⏱️ デイリー(10分)"],
  ["vocab", "🔤 英単語"],
  ["deck", "🗂️ 単語帳"],
  ["phrases", "💬 ミニフレーズ"],
  ["reading", "📖 リーディング"],
  ["writing", "✍️ ライティング"],
  ["conversation", "🗣️ 英会話"],
  ["listening", "🎧 リスニング"],
  ["assess", "🎯 判定・教材"],
  ["history", "📚 学習履歴"],
  ["settings", "⚙️ 設定"],
];

// ---------------------------------------------------------------------------
// Small DOM / util helpers (shared, exported for view modules)
// ---------------------------------------------------------------------------

export function el(html) {
  const t = document.createElement("template");
  t.innerHTML = html.trim();
  return t.content.firstElementChild;
}

export function toast(msg) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), 2200);
}

export function escapeHtml(s) {
  return (s || "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// Minimal Markdown -> HTML (headings, bold, bullets, line breaks).
export function md(text) {
  const lines = escapeHtml(text || "").split("\n");
  const out = [];
  let inList = false;
  for (let line of lines) {
    line = line.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
    const h = line.match(/^(#{1,4})\s+(.*)$/);
    if (h) {
      if (inList) { out.push("</ul>"); inList = false; }
      out.push(`<h${h[1].length + 1}>${h[2]}</h${h[1].length + 1}>`);
    } else if (/^\s*[-*]\s+/.test(line)) {
      if (!inList) { out.push("<ul>"); inList = true; }
      out.push("<li>" + line.replace(/^\s*[-*]\s+/, "") + "</li>");
    } else if (line.trim() === "") {
      // 連続する空行は1つの改行に集約（縦に伸びすぎないように）。
      if (inList) { out.push("</ul>"); inList = false; }
      if (out.length && out[out.length - 1] !== "<br/>") out.push("<br/>");
    } else {
      if (inList) { out.push("</ul>"); inList = false; }
      out.push(line + "<br/>");
    }
  }
  if (inList) out.push("</ul>");
  return out.join("\n");
}

export const view = () => document.getElementById("view");

// 禁止用語(注意喚起)の表示・出題トグル。既定は両方OFF（＝除外）。
// showBanned: 一覧に表示するか / testBanned: クイズ・デイリーに出すか。
export function showBanned() {
  return localStorage.getItem("showBanned") === "1";
}
export function setShowBanned(on) {
  localStorage.setItem("showBanned", on ? "1" : "0");
}
export function testBanned() {
  return localStorage.getItem("testBanned") === "1";
}
export function setTestBanned(on) {
  localStorage.setItem("testBanned", on ? "1" : "0");
}

// ---------------------------------------------------------------------------
// Routing
// ---------------------------------------------------------------------------

const ROUTES = {
  dashboard: views.dashboard,
  daily: views.daily,
  vocab: views.vocab,
  deck: views.decks,
  phrases: views.phrases,
  reading: views.reading,
  writing: views.writing,
  conversation: views.conversation,
  listening: views.listening,
  assess: views.assess,
  history: views.history,
  settings: views.settings,
};

let currentTab = "dashboard";

// 画面を離れるときに一度だけ呼ばれるクリーンアップ。views が登録する
// (例: 英会話の自動記録の確定保存)。次の go() で消費される。
let leaveHook = null;
export function onLeaveView(fn) { leaveHook = fn; }

export async function go(tab) {
  if (!ROUTES[tab]) tab = "dashboard";
  if (leaveHook) {
    const fn = leaveHook; leaveHook = null;
    try { fn(); } catch (e) { /* ignore */ }
  }
  currentTab = tab;
  speech.stopSpeaking();
  document.querySelectorAll(".nav-item").forEach((b) =>
    b.classList.toggle("active", b.dataset.tab === tab));
  view().innerHTML = '<p class="muted">読み込み中…</p>';
  try {
    await ROUTES[tab](view());
  } catch (e) {
    view().innerHTML = `<div class="card">エラー: ${escapeHtml(e.message)}</div>`;
  }
}

// Shared services exposed to views.
export { api, speech, quizRunner };

// ---------------------------------------------------------------------------
// Topbar wiring
// ---------------------------------------------------------------------------

export async function refreshCost() {
  try {
    const u = await api.get("/api/system/usage");
    const badge = document.getElementById("costBadge");
    const cap = u.daily_cap_jpy
      ? ` / 上限 ¥${u.daily_cap_jpy}${u.cap_blocked ? "（停止中）" : ""}` : "";
    badge.textContent =
      `💰 今日 ¥${u.today_cost_jpy}${cap} / 累計 ¥${u.total_cost_jpy}`;
    badge.title =
      `今日 $${u.today_cost_usd.toFixed(4)} / 累計 $${u.total_cost_usd.toFixed(4)}` +
      ` (レート ¥${u.jpy_rate}/$ @${u.jpy_as_of})\n` +
      `1日の上限 $${(u.daily_cap_usd || 0).toFixed(2)}` +
      `（暴走防止ガード・.envで変更可）\n` +
      `呼び出し ${u.calls} 回 / 入力 ${u.prompt_tokens} tok / ` +
      `出力 ${u.output_tokens} tok`;
  } catch (e) { /* ignore */ }
}

function setInputMode(mode) {
  state.inputMode = mode === "voice" ? "voice" : "text";
  localStorage.setItem("inputMode", state.inputMode);
  document.getElementById("inputMode").value = state.inputMode;
}

// Voice command -> action.
async function runCommand() {
  const btn = document.getElementById("micCmd");
  const status = document.getElementById("cmdStatus");
  if (!speech.sttSupported()) {
    toast("このブラウザは音声認識に未対応です");
    return;
  }
  btn.classList.add("listening");
  status.textContent = "聞き取り中…";
  try {
    const text = await speech.listenOnce("ja-JP");
    status.textContent = `「${text}」`;
    const intent = await api.post("/api/learn/command", { text });
    await execCommand(intent);
  } catch (e) {
    status.textContent = e.message;
  } finally {
    btn.classList.remove("listening");
    setTimeout(() => (status.textContent = ""), 4000);
  }
}

export async function execCommand(intent) {
  if (!intent || !intent.action) return;
  const { action, args = {}, say } = intent;
  if (say) { toast(say); speech.speak(say, { rate: 1 }); }
  switch (action) {
    case "navigate":
      if (args.tab) go(args.tab);
      break;
    case "set_input_mode":
      setInputMode(args.mode);
      toast("入力モード: " + state.inputMode);
      break;
    case "set_model":
      if (args.model) {
        await api.put("/api/system/settings", { openai_model: args.model });
        toast("モデルを " + args.model + " に変更しました");
        refreshAiState();
      }
      break;
    case "start_daily":
      go("daily");
      break;
    case "save_session":
      go("history");
      toast("学習履歴タブで保存できます");
      break;
    case "speak":
      if (args.text) speech.speak(args.text);
      break;
    default:
      break;
  }
}

export async function refreshAiState() {
  try {
    const s = await api.get("/api/system/settings");
    state.aiEnabled = s.ai_enabled;
    speech.setAiEnabled(s.ai_enabled);
    const node = document.getElementById("aiState");
    node.textContent = s.ai_enabled
      ? `AI: ${s.model}` : "AI: 未設定";
    node.className = "ai-state " + (s.ai_enabled ? "ai-on" : "ai-off");
  } catch (e) { /* ignore */ }
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

async function boot() {
  // Build nav.
  const nav = document.getElementById("nav");
  TABS.forEach(([tab, label]) => {
    const b = el(`<button class="nav-item" data-tab="${tab}">${label}</button>`);
    b.addEventListener("click", () => go(tab));
    nav.appendChild(b);
  });

  // Topbar.
  document.getElementById("inputMode").value = state.inputMode;
  document.getElementById("inputMode")
    .addEventListener("change", (e) => setInputMode(e.target.value));
  document.getElementById("micCmd").addEventListener("click", runCommand);

  try {
    state.taxonomy = await api.get("/api/system/taxonomy");
    if (state.taxonomy.tts_voices) {
      speech.setOpenAIVoices(state.taxonomy.tts_voices);
    }
  } catch (e) { /* ignore */ }

  await refreshAiState();   // sets speech aiEnabled
  await refreshCost();
  speech.onUsage(refreshCost); // refresh cost after paid TTS calls
  // Pre-load voices for TTS.
  speech.getEnglishVoices();
  speech.pickRoundVoice();

  go("dashboard");
}

boot();
