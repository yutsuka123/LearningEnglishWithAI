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
  // B16: 出張・旅行準備の「ロールプレイを始める」から一時的にセットされる
  // 人物像。会話タブがこれを見て、シーン選択の代わりにpersonaで会話する。
  tripPrepPersona: null,
};

const TABS = [
  ["dashboard", "🏠 ダッシュボード"],
  // 2026-08-09: ユーザー指示により当面非表示（機能・ルートは温存、再表示は
  // この2行のコメントアウトを外すだけでよい）。
  // ["daily", "⏱️ デイリー(10分)"],
  ["vocab", "🔤 英単語"],
  ["flashcard", "🃏 フラッシュ単語"],
  ["deck", "🗂️ 単語帳"],
  ["phrases", "💬 ミニフレーズ"],
  ["flashphrase", "🃏 フラッシュフレーズ"],
  ["phrasedeck", "🗂️ フレーズ帳"],
  ["reading", "📖 リーディング"],
  ["writing", "✍️ ライティング"],
  ["conversation", "🗣️ 英会話"],
  ["listening", "🎧 リスニング"],
  // ["tripprep", "🧳 出張・旅行準備"],
  ["assess", "🎯 判定・教材"],
  ["history", "📚 学習履歴"],
  ["settings", "⚙️ 設定・チャージ"],
  ["admin", "👑 管理者情報"],   // 管理者のみ表示（boot で非adminは隠す）
];

const TAB_LABELS = Object.fromEntries(TABS);

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
// スマホ向けハンバーガーメニュー（狭い画面でのみCSSが有効化する）。
// ---------------------------------------------------------------------------

function closeMobileNav() {
  document.getElementById("sidebar")?.classList.remove("open");
  document.getElementById("sidebarBackdrop")?.classList.remove("show");
}

function toggleMobileNav() {
  document.getElementById("sidebar")?.classList.toggle("open");
  document.getElementById("sidebarBackdrop")?.classList.toggle("show");
}

// ---------------------------------------------------------------------------
// ダーク/ライト表示テーマ（既定はダーク。切替はlocalStorageに記憶）。
// ---------------------------------------------------------------------------

function applyTheme(theme) {
  const btn = document.getElementById("themeToggle");
  if (theme === "light") {
    document.documentElement.dataset.theme = "light";
    if (btn) btn.textContent = "☀️";
  } else {
    delete document.documentElement.dataset.theme;
    if (btn) btn.textContent = "🌙";
  }
}

function initTheme() {
  applyTheme(localStorage.getItem("theme") || "dark");
  document.getElementById("themeToggle")?.addEventListener("click", () => {
    const next = document.documentElement.dataset.theme === "light"
      ? "dark" : "light";
    localStorage.setItem("theme", next);
    applyTheme(next);
  });
}

// ---------------------------------------------------------------------------
// 文字の大きさ（小/中/大/特大。既定は中。未ログインでも使える設定にしたい
// という要望のためtopbarに常設、settings画面(要ログイン)には置かない
// ・2026-08-12）。
// ---------------------------------------------------------------------------

function applyFontSize(size) {
  if (size) document.documentElement.dataset.fontSize = size;
  else delete document.documentElement.dataset.fontSize;
  const sel = document.getElementById("fontSize");
  if (sel) sel.value = size;
}

function initFontSize() {
  applyFontSize(localStorage.getItem("fontSize") || "");
  document.getElementById("fontSize")?.addEventListener("change", (e) => {
    const v = e.target.value;
    localStorage.setItem("fontSize", v);
    applyFontSize(v);
  });
}

// トップバーの残高(pt)表示をクリックしたらチャージ画面へ誘導する
// （2026-08-13ユーザー指摘「ptをクリックしてもチャージしますかとポップアップ
// を出してはい押下したら飛ぶように」）。要素自体はindex.htmlの静的DOMで
// 一度きりなので、リスナーは起動時に一度だけ登録すればよい
// （refreshCost()は毎回textContentを書き換えるだけ）。
function initBalanceClick() {
  const balEl = document.getElementById("usageBalance");
  if (!balEl) return;
  balEl.style.cursor = "pointer";
  balEl.title = "クリックでチャージ画面へ";
  balEl.addEventListener("click", () => {
    if (state.isGuest) {
      if (confirm("チャージにはログインが必要です。ログイン画面へ" +
          "移動しますか？")) {
        location.href = "/login";
      }
      return;
    }
    if (confirm("チャージしますか？")) go("settings");
  });
}

// ---------------------------------------------------------------------------
// Routing
// ---------------------------------------------------------------------------

const ROUTES = {
  dashboard: views.dashboard,
  daily: views.daily,
  vocab: views.vocab,
  flashcard: views.flashcard,
  deck: views.decks,
  phrases: views.phrases,
  flashphrase: views.flashPhrase,
  phrasedeck: views.phraseDecks,
  reading: views.reading,
  writing: views.writing,
  conversation: views.conversation,
  listening: views.listening,
  tripprep: views.tripPrep,
  assess: views.assess,
  history: views.history,
  settings: views.settings,
  admin: views.admin,
};

let currentTab = "dashboard";
// boot()の末尾で無条件にgo("dashboard")するとboot()の非同期処理(タクソノミー
// 取得等)が終わる前にユーザーがタブをクリックした場合、そのビューの
// レンダリングをboot()が上書きしてしまい、後から解決するそのビューの
// load()/paint()等がDOMを見失ってエラーになる(2026-08-05発見)。boot()側で
// 既にユーザーがナビゲートしたか判定するためのフラグ。
let userNavigated = false;

// 画面を離れるときに一度だけ呼ばれるクリーンアップ。views が登録する
// (例: 英会話の自動記録の確定保存)。次の go() で消費される。
let leaveHook = null;
export function onLeaveView(fn) { leaveHook = fn; }

export async function go(tab) {
  userNavigated = true;
  if (!ROUTES[tab]) tab = "dashboard";
  if (leaveHook) {
    const fn = leaveHook; leaveHook = null;
    try { fn(); } catch (e) { /* ignore */ }
  }
  currentTab = tab;
  speech.stopSpeaking();
  document.querySelectorAll(".nav-item").forEach((b) =>
    b.classList.toggle("active", b.dataset.tab === tab));
  closeMobileNav();
  // 各ビュー関数には view() 本体ではなく専用のラッパーdivを渡す。views
  // の中には内部でawaitを挟んでから root.innerHTML を書くものがあり
  // (例: dashboard() の /api/system/progress 取得後)、その間に別タブへ
  // 素早く切り替えると、古いawaitが後から解決して新しいビューのDOMを
  // 上書きし、後続のquerySelectorがnullを返してクラッシュしていた
  // (2026-08-05発見)。ラッパーを毎回差し替えることで、古い呼び出しが
  // 書き込む先は表示から切り離された(=無害な)自分専用のdivになる。
  const myRoot = document.createElement("div");
  myRoot.innerHTML = '<p class="muted">読み込み中…</p>';
  view().replaceChildren(myRoot);
  api.track("page", tab, TAB_LABELS[tab] || tab);
  try {
    await ROUTES[tab](myRoot);
  } catch (e) {
    myRoot.innerHTML = `<div class="card">エラー: ${escapeHtml(e.message)}</div>`;
  }
}

// Shared services exposed to views.
export { api, speech, quizRunner };

// ---------------------------------------------------------------------------
// Topbar wiring
// ---------------------------------------------------------------------------

// 残量(¥)の色: 人によって上限(チャージ額)が違うため比率ではなく絶対額で
// 判定する。50円以下は赤、100円以下はオレンジ、それ以上は緑。
function _usageColor(remainJpy) {
  if (remainJpy <= 50) return "#e2503b";   // 赤(残りわずか)
  if (remainJpy <= 100) return "#f2994a";  // オレンジ(少ない)
  return "#36c98d";                         // 緑(十分)
}

export async function refreshCost() {
  try {
    const u = await api.get("/api/system/my-usage");
    const isAdmin = u.role === "admin";
    state.isAdmin = isAdmin;       // 各ビューのロール別表示に使う
    state.multiuser = !!u.multiuser;
    state.isGuest = !!u.is_guest;
    // 無料範囲外の語・フレーズを「実際に再生できるか」（🔒アイコン判定用・
    // 2026-08-13）。管理者は常に課金対象外＝常に再生可。ゲストは残高の
    // 概念自体が無く常に不可。それ以外（無課金/課金ログインユーザー）は
    // 残高が少しでもあれば再生できる（1回の課金は最低0.5円程度の少額
    // のため、厳密な残額計算ではなく「残高>0」で近似する）。
    state.canPlayOutOfRange =
      isAdmin || (!state.isGuest && (u.remaining_jpy || 0) > 0);
    if (!isAdmin) {
      // 非管理者(ゲスト・無課金/課金の一般ユーザー)は/api/system/settings
      // を読めない(api_key_masked等を含むため管理者専用・2026-08-12)。
      // AI有効状態はここ(my-usage)経由で取得する(元は2026-08-11にゲスト
      // 向けだけの対応だったが、非管理者全体に拡張)。
      state.aiEnabled = !!u.ai_enabled;
      speech.setAiEnabled(u.ai_enabled);
      const node = document.getElementById("aiState");
      if (node) {
        node.textContent = u.ai_enabled ? "" : "⚠️ AI未設定";
        node.className = "ai-state " + (u.ai_enabled ? "ai-on" : "ai-off");
      }
    }
    const balEl = document.getElementById("usageBalance");
    if (balEl) {
      const remain = Math.max(0, Math.round(u.remaining_jpy || 0));
      balEl.textContent = `${remain}pt`;
      balEl.style.color = _usageColor(remain);
      balEl.title = u.balance_jpy != null
        ? `AI利用の残り目安: ${remain}pt（チャージ残高 ` +
          `${Math.round(u.balance_jpy)}pt 含む）`
        : `AI利用の残り目安: ${remain}pt`;
    }
    // 管理者のみ金額表示。一般ユーザーは残量表示のみ。
    const badge = document.getElementById("costBadge");
    if (badge) {
      badge.textContent = isAdmin
        ? `💰 今日 ¥${u.today_jpy} / 今月 ¥${u.month_jpy}`
        : "";
    }
    const ver = document.getElementById("appVer");
    if (ver) ver.textContent = u.version || "";
    // ログアウト/ログインボタン（マルチユーザー時のみ表示。ゲストは
    // ログイン導線のみ、ログイン済みはログアウトのみを見せる）。
    const lo = document.getElementById("logoutBtn");
    if (lo) {
      lo.style.display = (u.multiuser && !state.isGuest) ? "" : "none";
      lo.title = u.username ? `${u.username} としてログイン中` : "";
    }
    const li = document.getElementById("loginBtn");
    if (li) li.style.display = (u.multiuser && state.isGuest) ? "" : "none";
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
    // モデル名は非表示。未設定のときだけ警告を出す。
    node.textContent = s.ai_enabled ? "" : "⚠️ AI未設定";
    node.className = "ai-state " + (s.ai_enabled ? "ai-on" : "ai-off");
  } catch (e) { /* ignore */ }
}

// ---------------------------------------------------------------------------
// ボタン押下数の記録（管理画面の利用状況分析用・2026-08-17）。個別の
// ボタンごとにハンドラを書き足す代わりに、document全体で1回だけ委譲する
// （4800行超あるviews.jsの全ボタンを回らずに済む・textContentを label に
// する設計上、動的な文言(クイズの選択肢等)は個別行に分散するが、ORDER BY
// カウント降順+上位のみ表示なので、実際によく押される共通UIボタンは自然に
// 上位へ集まる）。
// ---------------------------------------------------------------------------

function initClickTracking() {
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("button, a.btn");
    if (!btn) return;
    const label = (btn.textContent || "").trim().replace(/\s+/g, " ")
      .slice(0, 60) || btn.id || btn.className || "?";
    api.track("click", currentTab, label);
  });
}

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------

// ①(未ログイン/ゲスト)は単語・フレーズの閲覧とフラッシュカードのみ無料公開。
// それ以外はログインが要る機能なのでnavに出さない(2026-08-11・B1本実装。
// バックエンド側も個別に要ログインを強制しているので、これは表示上の案内
// であり多重防御の一枚)。
// reading/writing/conversation/listeningは2026-08-13にゲスト開放
// （サンプル閲覧をサイドバーから直接できるように・ユーザー要望）。
// 各ビューの生成・履歴系の操作は要ログインのまま(クリック時にエラー/
// ログイン案内で自然にガードされる、サンプルカードのみ`/api/learn/samples`
// 経由でゲストにも動作する)。
const GUEST_HIDDEN_TABS = new Set([
  "deck", "phrasedeck", "assess", "history", "settings",
]);

async function boot() {
  initTheme();
  initFontSize();

  try {
    state.taxonomy = await api.get("/api/system/taxonomy");
    if (state.taxonomy.tts_voices) {
      speech.setOpenAIVoices(state.taxonomy.tts_voices);
    }
  } catch (e) { /* ignore */ }

  // ロール/ゲスト判定を先に済ませてからnavを組み立てる（先にnavを全件
  // 描画してから隠す順序だと、未ログインでも一瞬「管理者」「設定」等が
  // 見えてちらつく問題があったため・2026-08-12ユーザー指摘）。
  await refreshCost();      // sets state.isAdmin / state.multiuser / state.isGuest
  if (state.isAdmin) {
    // 非管理者は/api/system/settingsを読めない(2026-08-12・管理者専用化)。
    // AI有効状態はrefreshCost()内でmy-usage経由により既に取得済み。
    await refreshAiState();   // sets speech aiEnabled
  }

  // Build nav（管理者タブ・ゲスト非公開タブは、隠すのではなくそもそも
  // 挿入しない）。
  const nav = document.getElementById("nav");
  TABS.forEach(([tab, label]) => {
    if (tab === "admin" && !state.isAdmin) return;
    if (state.isGuest && GUEST_HIDDEN_TABS.has(tab)) return;
    const b = el(`<button class="nav-item" data-tab="${tab}">${label}</button>`);
    b.addEventListener("click", () => go(tab));
    nav.appendChild(b);
  });
  // メニューに常時表示する「このアプリについて」（別タブで開く外部ページ）。
  // トップバー右のバージョン表記からも行けるが分かりにくいため
  // (2026-08-11ユーザー指摘)、メニュー本体にも入れる。
  nav.appendChild(el(
    '<a class="nav-item" href="/static/about.html">'
    + "📄 このアプリについて</a>",
  ));

  // スマホ向けハンバーガーメニュー: ボタン/背景タップで開閉。
  document.getElementById("navToggle")
    ?.addEventListener("click", toggleMobileNav);
  document.getElementById("sidebarBackdrop")
    ?.addEventListener("click", closeMobileNav);

  // Topbar.
  document.getElementById("inputMode").value = state.inputMode;
  document.getElementById("inputMode")
    .addEventListener("change", (e) => setInputMode(e.target.value));
  document.getElementById("micCmd").addEventListener("click", runCommand);
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) logoutBtn.addEventListener("click", async () => {
    try { await api.post("/api/auth/logout"); } catch (_) { /* */ }
    location.href = "/login";
  });

  initClickTracking();
  speech.onUsage(refreshCost); // refresh cost after paid TTS calls
  speech.onPaymentRequired((msg) => toast(msg)); // 無料範囲外の再生でチャージ不足のとき
  // Pre-load voices for TTS.
  speech.getEnglishVoices();
  speech.pickRoundVoice();

  // 上記の非同期処理中にユーザーが既に別タブへナビゲートしていたら、
  // ダッシュボードで上書きしない（レースコンディション対策）。
  if (!userNavigated) go(state.isGuest ? "vocab" : "dashboard");
}

boot();
