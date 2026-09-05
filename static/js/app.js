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
  // 安全側のデフォルト(2026-09-01): /api/system/my-usageが失敗すると
  // refreshCost()の内部try/catchで握りつぶされ、これらがundefinedの
  // まま残ってしまい、サイドバーのログイン導線(#loginBtnや🔑ログイン/
  // 登録リンク)が一切表示されないバグがあった(ゲスト訪問者が登録
  // 導線を完全に失う最悪のケース)。未確認の間はゲスト扱いにしておけば
  // 「本来ログイン中の人に一瞬ゲスト向け表示が出る」程度で済み、
  // 「本来ゲストの人がログイン導線を失う」よりずっと軽微。
  multiuser: true,
  isGuest: true,
  taxonomy: { news_fields: [], accents: [], models: [] },
  // B16: 出張・旅行準備の「ロールプレイを始める」から一時的にセットされる
  // 人物像。会話タブがこれを見て、シーン選択の代わりにpersonaで会話する。
  tripPrepPersona: null,
};

export const TABS = [
  ["welcome", "🏠 ようこそ"],   // 未ログインのみ表示（boot で挿入判定）
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
  ["quiz", "📝 クイズ"],
  ["reading", "📖 リーディング"],
  ["writing", "✍️ ライティング"],
  ["conversation", "🗣️ 英会話"],
  ["listening", "🎧 リスニング"],
  // ["tripprep", "🧳 出張・旅行準備"],
  ["assess", "🎯 判定・教材"],
  ["history", "📚 学習履歴"],
  ["games", "🎮 ゲーム"],   // 2026-09-05〜一般公開（誰でも表示）
  ["settings", "⚙️ 設定・チャージ"],
  // バージョン情報（更新履歴・メンテナンス予定）。未ログインでも見られる
  // ようにする（2026-08-22ユーザー要望）。
  ["release", "🆕 バージョン情報"],
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

export function toast(msg, ms = 2200) {
  const t = document.getElementById("toast");
  t.textContent = msg;
  t.classList.add("show");
  setTimeout(() => t.classList.remove("show"), ms);
}

export function escapeHtml(s) {
  return (s || "").replace(/[&<>"]/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
}

// バックエンドはSQLiteのdatetime('now')等でUTCのnaive文字列
// ("YYYY-MM-DD HH:MM:SS" または "...THH:MM:SS"、タイムゾーン表記なし)を
// 返す。素の文字列をそのまま表示するとUTCのまま出てしまい、管理画面の
// 各種ログ(ログイン履歴・AI利用ログ・お問い合わせ日時・最終アクセス等)が
// JSTより9時間遅れて見えていた(2026-08-19ユーザー指摘)。明示的にUTCとして
// パースし、常にJST(UTC+9)で "YYYY-MM-DD HH:MM" 表示する。
export function fmtDateJST(s) {
  if (!s) return "—";
  const iso = String(s).trim().replace(" ", "T");
  const withZone = /Z$|[+-]\d{2}:?\d{2}$/.test(iso) ? iso : iso + "Z";
  const d = new Date(withZone);
  if (Number.isNaN(d.getTime())) return s;
  const jst = new Date(d.getTime() + 9 * 60 * 60 * 1000);
  const p = (n) => String(n).padStart(2, "0");
  return `${jst.getUTCFullYear()}-${p(jst.getUTCMonth() + 1)}-`
    + `${p(jst.getUTCDate())} ${p(jst.getUTCHours())}:${p(jst.getUTCMinutes())}`;
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
// 左ペイン(サイドバー)の開閉。
// スマホ(<=760px)はオフキャンバス(.open で右へスライドイン)、
// それ以外の幅は常設表示だが折りたたみ可能(.collapsed で幅0)
// (2026-08-30ユーザー要望: 横幅の狭いPC/タブレットで各機能の表を見る際、
// 左ペイン分の横幅を空けたい)。
// ---------------------------------------------------------------------------

// この幅より狭いPC/タブレット画面では、ページ切替後に自動で左ペインを
// 畳む(ピン留め時を除く)。760px以下は上のオフキャンバス扱いなので対象外。
const SIDEBAR_AUTO_COLLAPSE_MAX_WIDTH = 1200;

let sidebarCollapsed = false;

function closeMobileNav() {
  document.getElementById("sidebar")?.classList.remove("open");
  document.getElementById("sidebarBackdrop")?.classList.remove("show");
}

function toggleMobileNav() {
  document.getElementById("sidebar")?.classList.toggle("open");
  document.getElementById("sidebarBackdrop")?.classList.toggle("show");
}

function isSidebarPinned() {
  return localStorage.getItem("sidebarPinned") === "1";
}

function setSidebarCollapsed(on) {
  sidebarCollapsed = on;
  document.getElementById("sidebar")?.classList.toggle("collapsed", on);
  document.body.classList.toggle("sidebar-collapsed", on);
}

function setSidebarPinned(on) {
  localStorage.setItem("sidebarPinned", on ? "1" : "0");
  const btn = document.getElementById("sidebarPin");
  if (btn) {
    btn.classList.toggle("active", on);
    btn.title = on
      ? "固定表示中（クリックで解除）"
      : "左メニューを固定表示（自動で畳まれないようにする）";
  }
  if (on) setSidebarCollapsed(false); // 固定するなら必ず開いた状態にする
}

// スマホは既存のオフキャンバス開閉、それ以外は折りたたみ開閉。
// 同じハンバーガーボタンで両方をまかなう(2026-08-30、見慣れたアイコンを
// 使い回すことで直感的にする)。ピン留め中は「固定表示」の名の通り
// ハンバーガーでも畳めないようにする(2026-08-30ユーザー指摘: ピン有効
// でもハンバーガーを押すと畳まれてしまい、ピンの意味が無いように見えた。
// 解除したければピン自体をオフにすればよい、という一貫した仕様にする)。
function toggleSidebar() {
  if (window.innerWidth <= 760) {
    toggleMobileNav();
  } else if (!isSidebarPinned()) {
    setSidebarCollapsed(!sidebarCollapsed);
  }
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
// メンテナンス予定のお知らせ（2026-08-22ユーザー要望）
//
// 予定はサーバー側のDB(app_state)に入っており、管理画面から変更すると
// **アプリを再起動せずに**利用者へ反映される。ここは表示だけを担当する。
// 「閉じる」を押した内容は localStorage に覚えて再表示しない（内容が
// 変わればまた出る）。
// ---------------------------------------------------------------------------

export async function refreshMaintenanceBanner() {
  const box = document.getElementById("maintBanner");
  if (!box) return;
  // お知らせはメニュー内にあり閉じたままだと気付けないため、ハンバーガー
  // ボタンに小さな丸印を出す(2026-08-23・お知らせがメイン画面を圧迫する
  // という指摘でメニュー内へ移動した際、気付けなくなるのを防ぐ対応)。
  const toggle = document.getElementById("navToggle");
  const setDot = (on, urgent) => {
    if (!toggle) return;
    toggle.classList.toggle("has-notice", on);
    toggle.classList.toggle("in-progress", on && !!urgent);
  };
  try {
    const m = await api.get("/api/system/maintenance");
    const n = (m && m.notice) || {};
    if (!n.show || !n.text) { box.style.display = "none"; setDot(false); return; }
    if (localStorage.getItem("maintDismissed") === n.text) {
      box.style.display = "none";
      setDot(false);
      return;
    }
    box.className = "maint-banner"
      + (n.state === "in_progress" ? " in-progress" : "");
    box.innerHTML = "";
    const icon = document.createElement("span");
    icon.textContent = n.state === "in_progress" ? "🛠️"
      : n.state === "completed" ? "✅" : "🗓️";
    const text = document.createElement("span");
    text.textContent = n.text;
    const close = document.createElement("button");
    close.className = "maint-close";
    close.title = "このお知らせを閉じる";
    close.textContent = "✕";
    close.addEventListener("click", () => {
      localStorage.setItem("maintDismissed", n.text);
      box.style.display = "none";
      setDot(false);
    });
    box.append(icon, text, close);
    box.style.display = "";
    setDot(true, n.state === "in_progress");
  } catch (e) {
    box.style.display = "none";
    setDot(false);
  }
}

// ---------------------------------------------------------------------------
// Routing
// ---------------------------------------------------------------------------

const ROUTES = {
  welcome: views.welcome,
  dashboard: views.dashboard,
  daily: views.daily,
  vocab: views.vocab,
  flashcard: views.flashcard,
  deck: views.decks,
  phrases: views.phrases,
  flashphrase: views.flashPhrase,
  phrasedeck: views.phraseDecks,
  quiz: views.quiz,
  reading: views.reading,
  writing: views.writing,
  conversation: views.conversation,
  listening: views.listening,
  tripprep: views.tripPrep,
  assess: views.assess,
  history: views.history,
  games: views.games,
  settings: views.settings,
  release: views.release,
  admin: views.admin,
};

// 入力:文字/音声セレクタを使う画面だけに絞ってトップバーへ表示する
// (2026-08-29・ユーザー指摘: 常時表示は他画面で意味を持たずスペースの
// 無駄+紛らわしい)。実際に state.inputMode を参照するのは
// daily()/quiz()/writing() の3画面(static/js/views.jsのanswerInput()と
// quiz.jsのrenderAnswerInput())。
const INPUT_MODE_TABS = new Set(["daily", "quiz", "writing"]);

let currentTab = "dashboard";
// boot()の末尾で無条件にgo("dashboard")するとboot()の非同期処理(タクソノミー
// 取得等)が終わる前にユーザーがタブをクリックした場合、そのビューの
// レンダリングをboot()が上書きしてしまい、後から解決するそのビューの
// load()/paint()等がDOMを見失ってエラーになる(2026-08-05発見)。boot()側で
// 既にユーザーがナビゲートしたか判定するためのフラグ。
let userNavigated = false;
// 左ペイン自動折りたたみ用: 最初の表示(起動直後の初回go())は開いたまま
// にし、2回目以降のページ切替からだけ幅が狭ければ畳む
// (2026-08-30ユーザー要望「最初の表示時は開いておき」)。
let hasNavigatedOnce = false;

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
  document.body.classList.toggle("tab-welcome", tab === "welcome");
  speech.stopSpeaking();
  document.querySelectorAll(".nav-item").forEach((b) =>
    b.classList.toggle("active", b.dataset.tab === tab));
  const inputModeWrap = document.getElementById("inputModeWrap");
  if (inputModeWrap) {
    inputModeWrap.style.display = INPUT_MODE_TABS.has(tab) ? "" : "none";
  }
  closeMobileNav();
  closeHintPopover();
  // 中間幅の画面(タブレット横・小さめノートPC等)では、各機能の表が
  // 横スクロールを要することが多いため、初回表示以降のページ切替では
  // 左ペイン分の横幅を返す(ピン留め時は自動で畳まない)。
  if (hasNavigatedOnce && !isSidebarPinned()
      && window.innerWidth > 760
      && window.innerWidth <= SIDEBAR_AUTO_COLLAPSE_MAX_WIDTH) {
    setSidebarCollapsed(true);
  }
  hasNavigatedOnce = true;
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
    // PayPay新チャージ画面の限定公開(2026-09-02)。管理者に加えて、
    // 個別に許可されたアカウントにも表示する
    // (app/services/paypay.pyのis_test_allowedと対応)。
    state.canTestPaypayCharge = isAdmin || !!u.paypay_charge_test_allowed;
    // ゲーム機能(クロスワード等)は2026-09-05〜一般公開(サンプルは
    // ゲスト含め誰でも、自分で作るはログイン済みユーザーなら誰でも。
    // ゲスト/未ログイン時の判定はapp.js側では行わずcwRenderHub内で
    // 出し分ける)。タブ自体は常に表示する。
    state.canUseGames = true;
    state.multiuser = !!u.multiuser;
    state.isGuest = !!u.is_guest;
    // AI呼び出し(会話・生成)や無料範囲外の語・フレーズ再生を「実際に
    // 使えるか」（🔒アイコン判定用・2026-08-13、要ログイン/要課金の
    // 出し分け用に2026-08-23汎用化）。管理者は常に課金対象外＝常に可。
    // ゲストは残高の概念自体が無く常に不可。それ以外（無課金/課金
    // ログインユーザー）は残高が少しでもあれば使える（1回の課金は
    // 最低0.5円程度の少額のため、厳密な残額計算ではなく「残高>0」で
    // 近似する）。
    state.hasAiBalance =
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
      balEl.textContent = `残り${remain}pt`;
      balEl.style.color = _usageColor(remain);
      balEl.title = u.balance_jpy != null
        ? `AI利用の残り目安: ${remain}pt（チャージ残高 ` +
          `${Math.round(u.balance_jpy)}pt 含む）`
        : `AI利用の残り目安: ${remain}pt`;
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

async function doLogout() {
  if (!confirm("本当にログアウトしますか？")) return;
  try { await api.post("/api/auth/logout"); } catch (_) { /* */ }
  // 共有端末で前のアカウントの選択履歴(分野名・単語帳名等)が次の
  // ログイン先に見えてしまわないようにする(2026-09-05fable監査指摘・
  // cw_recent_sourcesはユーザーごとに分けず端末単位で保存しているため)。
  try { localStorage.removeItem("cw_recent_sources"); } catch (_) { /* */ }
  location.href = "/login";
}

function setInputMode(mode) {
  state.inputMode = mode === "voice" ? "voice" : "text";
  localStorage.setItem("inputMode", state.inputMode);
  document.getElementById("inputMode").value = state.inputMode;
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

// ゲストが学習操作をある程度行った時点で「記録は保存されない」ことに
// 気づいてもらうナッジ(2026-08-24・ユーザー承認)。about.htmlには同種の
// 文言が既にあるが、実際に使っている最中に出す方が効果的という判断。
// 1セッションに1回だけ(タブ再読み込みでリセット)。
const STUDY_TABS = new Set(["vocab", "flashcard", "phrases", "flashphrase", "quiz"]);
let guestStudyClicks = 0;
let guestNudgeShown = false;

// ---------------------------------------------------------------------------
// ⓘ説明ヒント(2026-08-30〜)。選択肢/制限がある項目(例:「再生できるものだけ」
// 「範囲外」)の意味を、PCはマウスホバー(title属性、既存の仕組みのまま)、
// スマホ含め全端末はⓘクリック/タップでポップオーバー表示する。
// 「今後表示しない」を選ぶとⓘアイコン自体を消す(=同じ説明を得た人には
// 見せない、鬱陶しくしない設計)。ログイン済みは/api/system/user-settings
// (端末非依存のDB保存)、アカウントの無いゲストはlocalStorageに保存する。
// ---------------------------------------------------------------------------

let dismissedHints = new Set();

async function loadDismissedHints() {
  if (state.isGuest) {
    try {
      dismissedHints = new Set(
        JSON.parse(localStorage.getItem("dismissedHints") || "[]"));
    } catch (e) { dismissedHints = new Set(); }
    return;
  }
  try {
    const r = await api.get("/api/system/user-settings");
    dismissedHints = new Set((r.settings || {}).dismissed_hints || []);
  } catch (e) { dismissedHints = new Set(); }
}

export function isHintDismissed(hintId) {
  return dismissedHints.has(hintId);
}

// hint テキストは呼び出し側(views.js)が保持する固定文言なので引数で渡す
// (中央データベース化するほどの数がまだ無いため素朴にしてある)。
export function infoIcon(hintId, text) {
  if (dismissedHints.has(hintId)) return "";
  return `<span class="info-icon" data-hint-id="${hintId}" `
    + `title="${escapeHtml(text)}">ⓘ</span>`;
}

async function dismissHint(hintId) {
  dismissedHints.add(hintId);
  document.querySelectorAll(`.info-icon[data-hint-id="${hintId}"]`)
    .forEach((n) => n.remove());
  if (state.isGuest) {
    localStorage.setItem(
      "dismissedHints", JSON.stringify([...dismissedHints]));
    return;
  }
  try {
    const r = await api.get("/api/system/user-settings");
    const settings = r.settings || {};
    settings.dismissed_hints = [...dismissedHints];
    await api.put("/api/system/user-settings", { settings });
  } catch (e) { /* 保存に失敗しても表示上は既に消えているので致命的でない */ }
}

let openHintPopover = null;

function closeHintPopover() {
  if (openHintPopover) { openHintPopover.remove(); openHintPopover = null; }
}

function showHintPopover(icon) {
  closeHintPopover();
  const hintId = icon.dataset.hintId;
  const text = icon.title;
  const pop = el(`<div class="hint-popover">
    <div class="hint-popover-text"></div>
    <div class="hint-popover-actions">
      <button type="button" class="hint-dismiss">今後表示しない</button>
      <button type="button" class="hint-close">閉じる</button>
    </div>
  </div>`);
  pop.querySelector(".hint-popover-text").textContent = text;
  document.body.appendChild(pop);
  const r = icon.getBoundingClientRect();
  const top = r.bottom + window.scrollY + 6;
  const maxLeft = window.scrollX
    + document.documentElement.clientWidth - pop.offsetWidth - 8;
  const left = Math.max(8, Math.min(r.left + window.scrollX, maxLeft));
  pop.style.top = `${top}px`;
  pop.style.left = `${left}px`;
  pop.querySelector(".hint-close").addEventListener("click", closeHintPopover);
  pop.querySelector(".hint-dismiss").addEventListener("click", () => {
    dismissHint(hintId);
    closeHintPopover();
  });
  openHintPopover = pop;
}

function initHintIcons() {
  document.addEventListener("click", (e) => {
    if (e.target.closest(".hint-popover")) return;
    const icon = e.target.closest(".info-icon");
    if (icon) { showHintPopover(icon); return; }
    closeHintPopover();
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeHintPopover();
  });
}

function initClickTracking() {
  document.addEventListener("click", (e) => {
    const btn = e.target.closest("button, a.btn");
    if (!btn) return;
    const label = (btn.textContent || "").trim().replace(/\s+/g, " ")
      .slice(0, 60) || btn.id || btn.className || "?";
    api.track("click", currentTab, label);
    if (state.isGuest && !guestNudgeShown && STUDY_TABS.has(currentTab)) {
      guestStudyClicks++;
      if (guestStudyClicks >= 5) {
        guestNudgeShown = true;
        toast("💡 学習の記録は保存されていません。ログイン(無料・30秒)で失われなくなります");
      }
    }
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
  await loadDismissedHints(); // isGuestが決まった後(保存先の出し分けに必要)
  // pt残高は未登録/無課金でも0ptのまま常に表示され、何の数字か分かり
  // づらいという指摘(2026-08-30)を受けⓘヒントを追加。
  const balInfo = document.getElementById("usageBalanceInfo");
  if (balInfo) {
    balInfo.innerHTML = infoIcon("usage-balance-pt",
      "pt(ポイント)はAI機能(音声再生・英会話・添削等)に使える残高の単位"
      + "です。未登録は0ptですが、無料登録すると毎日一定量が使えるように"
      + "なり、チャージ(有料)するとさらに増えます。");
  }
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
    if (tab === "games" && !state.canUseGames) return;
    if (tab === "welcome" && !state.isGuest) return;
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
  // ログイン/ログアウトもサイドバー(ハンバーガーメニュー)に常設する。
  // トップバー右側は項目数が多くスマホ縦画面で折り返し/はみ出しが起き
  // やすいため、テーマ(ライト/ダーク)によらずどの画面幅でも確実に
  // たどり着ける経路をサイドバーにも用意する(2026-08-19ユーザー要望)。
  // 表示条件はトップバーのログイン/ログアウトボタンと同じ
  // (マルチユーザー時のみ・ゲストはログインのみ、ログイン済みはログアウトのみ)。
  if (state.multiuser) {
    if (state.isGuest) {
      nav.appendChild(el(
        '<a class="nav-item" href="/login">🔑 ログイン/登録</a>',
      ));
    } else {
      const navLogout = el('<button class="nav-item">🚪 ログアウト</button>');
      navLogout.addEventListener("click", doLogout);
      nav.appendChild(navLogout);
    }
  }

  // ハンバーガー: スマホはオフキャンバス開閉、それ以外は折りたたみ開閉。
  document.getElementById("navToggle")
    ?.addEventListener("click", toggleSidebar);
  document.getElementById("sidebarBackdrop")
    ?.addEventListener("click", closeMobileNav);
  document.getElementById("sidebarPin")
    ?.addEventListener("click", () => setSidebarPinned(!isSidebarPinned()));
  setSidebarPinned(isSidebarPinned()); // 保存済みの固定状態を反映

  // Topbar.
  document.getElementById("inputMode").value = state.inputMode;
  document.getElementById("inputMode")
    .addEventListener("change", (e) => setInputMode(e.target.value));
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) logoutBtn.addEventListener("click", doLogout);

  initClickTracking();
  initHintIcons();
  refreshMaintenanceBanner();
  speech.onUsage(refreshCost); // refresh cost after paid TTS calls
  speech.onPaymentRequired((msg) => toast(msg)); // 無料範囲外の再生でチャージ不足のとき
  // Pre-load voices for TTS.
  speech.getEnglishVoices();
  speech.pickRoundVoice();

  // 上記の非同期処理中にユーザーが既に別タブへナビゲートしていたら、
  // ダッシュボードで上書きしない（レースコンディション対策）。
  if (!userNavigated) go(state.isGuest ? "welcome" : "dashboard");
}

boot();
