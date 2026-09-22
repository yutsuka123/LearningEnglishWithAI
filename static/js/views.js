// All screen renderers. Each export takes the container element.

import { api } from "./api.js";
import * as speech from "./speech.js";
import { quizRunner } from "./quiz.js";
import {
  el, md, escapeHtml, toast, state, go, refreshCost, refreshAiState,
  showBanned, setShowBanned, testBanned, setTestBanned, onLeaveView,
  fmtDateJST, refreshMaintenanceBanner, TABS, infoIcon, tx, tabLabel,
} from "./app.js";

// 禁止用語クエリ: include_banned を付ける/付けないを返す小ヘルパー。
const bannedParam = (on) => (on ? "include_banned=true" : "");

// 「🔊再生できるものだけ」チェックボックス(単語/フレーズ一覧・
// フラッシュ単語/フラッシュフレーズの計4箇所で共通)。何が起きるのか
// 分かりにくいという指摘(2026-08-30)を受け、太字化+ⓘヒントアイコンを追加
// (app.jsのinfoIcon参照。クリック/タップでポップオーバー表示、
// 「今後表示しない」でユーザーごとに恒久的に消せる)。
function freeOnlyToggle(id, kind) {
  // kind: "word" | "phrase"（2026-09-23多言語化・以前は呼び出し側が
  // 日本語文言("単語"/"フレーズ"等)を直接渡していた）。
  const kindKey = kind === "phrase" ? "filter.kindPhrase" : "filter.kindWord";
  return `<label class="toggle" title="${escapeHtml(
      tx("filter.freeOnlyTitle", { kind: tx(kindKey) }))}">
    <input type="checkbox" id="${id}" />
    <b style="font-size:15px">${tx("filter.freeOnlyLabel")}</b></label>
    ${infoIcon("free-only-filter", tx("filter.freeOnlyHelp"))}`;
}

// ⓘヒント文言のうち複数画面で同じ内容を使うもの(2026-09-19・ヘルプ拡充)。
// 各画面のhintIdを共通にしてあるので、「今後表示しない」は全画面で共通に効く。
const QUIZ_GRADING_HINT =
  "答えを見たあと、自動判定を確認して採点します。⭕正解・🤔うろ覚え・"
  + "❌不正解は習熟度に記録され、✅覚えたは満点付近まで加点します。"
  + "🚫ノーカウントは記録も集計もしません。同じ語を両方向とも正解すると"
  + "ボーナスが付くことがあります。";
// 絞り込み・並び替えの使い方(2026-09-21・ユーザー要望「ⓘでフィルターのかけ方を
// 詳しく解説」)。改行はポップオーバー側(pre-line)で保たれる。挙動の根拠:
// 検索=読み込み済みの結果内(クライアント側)/複数分野=OR/大分類は分野未指定の
// ときだけ有効(app/routers/vocabulary.py `_word_filter`)。
const WORD_FILTER_HELP = [
  "【絞り込み・並び替えの使い方】",
  "🔍 検索：英語か日本語の一部を入力すると、いま表示中の一覧のなかから、その文字を含む語だけに絞ります。",
  "📁 大分類・分野：大分類を選ぶと、その中の分野すべてが対象になります。「全て ▾」を押すと分野を個別に複数選べます(選んだ分野のどれかに当てはまる語が出ます)。分野を個別に選んだときは、大分類よりそちらが優先されます。",
  "📶 Lv 下限〜上限：TOEICの目安レベルで範囲を指定します。下限だけ・上限だけでも使えます。",
  "🔊 再生できるものだけ：いまの状態で音声を無料で再生できる語だけに絞ります。",
  "🗂️ 単語帳：自分の単語帳に入れた語だけを表示します(ログイン後・単語帳を作っている場合)。",
  "↕ 並び替え：習熟度・正答率・英語A→Z・レベル・分野・最近の学習・無料で聞ける順から選べます。右の「昇順/降順」ボタンで逆順になります。",
  "✅ 覚えた：「含む/隠す/のみ」。覚えた語を除いて復習したいときは「隠す」を選びます。",
  "🐢 速度・件数：音声の再生速度と、1ページに表示する件数を変えられます。",
  "複数の条件は、すべてを満たす語に絞り込まれます。選択肢に出す分野そのものを減らしたいときは、設定の「表示する分野・シーン」で変更できます。",
].join("\n");
const PHRASE_FILTER_HELP = [
  "【絞り込み・並び替えの使い方】",
  "🔍 検索：英語か日本語の一部を入力すると、いま表示中の一覧のなかから、その文字を含むフレーズだけに絞ります。",
  "📁 大分類・シーン：大分類を選ぶと、その中のシーンすべてが対象になります。「全て ▾」を押すとシーンを個別に複数選べます(選んだシーンのどれかに当てはまるフレーズが出ます)。シーンを個別に選んだときは、大分類よりそちらが優先されます。",
  "📶 Lv 下限〜上限：TOEICの目安レベルで範囲を指定します。下限だけ・上限だけでも使えます。",
  "🔊 再生できるものだけ：いまの状態で音声を無料で再生できるフレーズだけに絞ります。",
  "🗂️ フレーズ帳：自分のフレーズ帳に入れたものだけを表示します(ログイン後・フレーズ帳を作っている場合)。",
  "↕ 並び替え：習熟度・正答率・英語A→Z・シーン・最近の学習・登録順・無料で聞ける順から選べます。「登録順」は、登録した順に並べるので、「失礼に響く言い方→ていねいな言い方」のように対になっているフレーズが続けて見られます。右の「昇順/降順」ボタンで逆順になります。",
  "✅ 覚えた：「含む/隠す/のみ」。覚えたフレーズを除いて復習したいときは「隠す」を選びます。",
  "複数の条件は、すべてを満たすフレーズに絞り込まれます。選択肢に出すシーンそのものを減らしたいときは、設定の「表示する分野・シーン」で変更できます。",
].join("\n");
const VISIBLE_DOMAINS_HELP = [
  "【表示する分野・シーンについて】",
  "チェックを外した分野(英単語)・シーン(フレーズ)は、英単語・ミニフレーズなどの画面の「絞り込みの選択肢」に出なくなります。興味のない分野で選択肢が長くなるのを防げます。",
  "データは消えません。あとからチェックを入れ直せば、いつでも選択肢に戻ります。",
  "選択肢から消えるだけなので、分野を「全て」にして一覧を見るときは、チェックを外した分野の語も一覧には含まれます。特定の分野だけを見たいときは、絞り込みで分野を選んでください。",
  "チェックを変えたあとは、このカードの「保存」を押すまで反映されません。",
  "「全てON/全てOFF/デフォルトに戻す」で英単語・フレーズ全体を一括で切り替えられ、各グループの一括ボタンで大分類ごとに切り替えられます。",
].join("\n");
const MASTERY_LEGEND_HINT =
  "習熟度バーは覚え具合(pt)を表します。赤=0pt・黄=1〜20pt・緑=21〜50pt・"
  + "青=51pt以上。表示は△うろ覚え→○覚えた→◎卒業の順に進みます。"
  + "ボタン: うろ覚え=少し加点／覚えた=満点付近まで加点(もう一度押すと"
  + "「戻す」)／卒業=満点で固定し、以後は時間が経っても減りません／"
  + "クリア=0ptに戻す。加点量や「覚えた」の基準は設定の詳細設定で"
  + "変えられます。";
const MASTERED_FILTER_HINT =
  "「覚えた」と判定された項目(習熟度が基準ptに達したもの)の扱いです。"
  + "含む=すべて出題、隠す=覚えた項目を除いて出題、のみ=覚えた項目だけを"
  + "復習用に出題します。基準は設定の詳細設定で変えられます。";
const DECK_PROGRESS_HINT =
  "「習得済み」は、習熟度が「覚えた」の基準pt(既定100pt)以上になった"
  + "数です。達成率=習得済み÷全体で、フラッシュやクイズで正解する・"
  + "「覚えた」「卒業」を押すと上がります。基準は設定の詳細設定で"
  + "変えられます。";
const COMPREHENSION_Q_HINT =
  "長文やスクリプトの内容を確認する理解問題です。OFFにすると問題の部分を"
  + "表示と読み上げから外します(問題は常に生成・保存されるので、あとで"
  + "ONにすれば見られます)。";

// 管理画面の各種集計フィルタ（2026-08-20ユーザー要望）。既定は管理者
// 自身/メール未登録の招待ユーザー/テストユーザーを除外(=実際の一般
// ユーザーの動向だけを見る)。管理者情報画面を開いている間・go("admin")
// での再描画をまたいで状態を保持するためモジュールレベルに置く。
const adminAggFilters = {
  include_admin: false, include_invited: false, include_test: false,
};
function adminAggQuery() {
  return `include_admin=${adminAggFilters.include_admin}`
    + `&include_invited=${adminAggFilters.include_invited}`
    + `&include_test=${adminAggFilters.include_test}`;
}

// 習熟度(mastery)設定の既定値。app/services/spaced_repetition.py の
// DEFAULT_MASTERY_CONFIG と同じ値に保つこと(2026-08-18)。
const MASTERY_DEFAULTS = {
  mastery_max: 200, mastered_threshold: 100, known_bonus: 125,
  vague_bonus: 25, decay_amount: 1, decay_interval_days: 1,
};

// マイク利用時のエラーを分かりやすい日本語に変換する(2026-08-18・
// getUserMediaの生の英語メッセージ(例:"Permission denied")がそのまま
// トーストに出て何をすればよいか分からない、との報告があったため)。
function micErrorMessage(e) {
  const name = e && e.name;
  if (name === "NotAllowedError" || name === "SecurityError"
    || /denied/i.test(e && e.message || "")) {
    return "マイクの使用が許可されていません。ブラウザまたはOSの設定で"
      + "このサイトのマイクがブロックされている可能性があります。\n\n"
      + "詳しい確認手順（Chrome/Edge/Firefox/Safari・Windows/Mac/"
      + "iOS/Android）はこちら:\n"
      + "https://study.nyangailab.com/static/about.html#trouble-mic";
  }
  if (name === "NotFoundError") {
    return "マイクが見つかりません。マイクが接続されているかご確認ください。";
  }
  if (name === "NotReadableError") {
    return "マイクを他のアプリが使用中の可能性があります。"
      + "他のアプリ/タブでマイクを使っていないかご確認ください。";
  }
  return (e && e.message) || "マイクを利用できません";
}

// 分野/レベル等の複数チェック可チェックボックス一覧(.chkbox)に添える
// 「すべてチェック」「選択済み全クリア」ボタン(2026-08-18・ユーザー要望・
// 単語帳/フレーズ帳の一括追加UIで項目数が多く手動チェックが大変だった
// ため)。targetId は対象の.chkboxを持つ要素のid。呼び出し側は生成した
// HTMLをその.chkbox要素の直前に挿入し、同じscope(rootまたはモーダルの
// body)に対して wireChkAllClear() を一度呼ぶ。
function chkAllClearHtml(targetId) {
  return `<div class="row" style="gap:6px; margin:2px 0 4px">
    <button type="button" class="btn ghost chk-all-btn" data-target="${targetId}"
      style="padding:2px 8px; font-size:12px">すべてチェック</button>
    <button type="button" class="btn ghost chk-clear-btn" data-target="${targetId}"
      style="padding:2px 8px; font-size:12px">選択済み全クリア</button>
  </div>`;
}
function wireChkAllClear(scope) {
  scope.querySelectorAll(".chk-all-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      scope.querySelectorAll(`#${btn.dataset.target} input[type="checkbox"]`)
        .forEach((c) => { c.checked = true; });
    });
  });
  scope.querySelectorAll(".chk-clear-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      scope.querySelectorAll(`#${btn.dataset.target} input[type="checkbox"]`)
        .forEach((c) => { c.checked = false; });
    });
  });
}

// --- shared answer-input helper (voice or text) ----------------------------

function answerInput(onSubmit, { lang = "en-US", placeholder = "答えを入力" } = {}) {
  const wrap = el(`<div class="mt"></div>`);
  const ta = el(`<textarea placeholder="${placeholder}"></textarea>`);
  const row = el(`<div class="row"></div>`);
  // ゲスト(サンプル閲覧のみ)や残高0のログインユーザーはAI呼び出し系の
  // 送信ができないため、押しても401/402で固まる/紛らわしいエラーになる
  // 前に鍵表示で分かりやすく無効化する（2026-08-13・要課金の案内は
  // 2026-08-23追加）。
  const sendBtn = el(aiGateDisabled()
    ? `<button class="btn" disabled>${aiGateLabel("送信")}</button>`
    : `<button class="btn">✓ 送信</button>`);
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
        } catch (e) { alert(micErrorMessage(e)); }
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

// AI呼び出し(生成・会話開始等、必ず課金が絡む操作)を行うボタンのラベル/
// 無効化判定(2026-08-23)。「要ログイン」とだけ書くとログインさえすれば
// 使えるように見えるが、実際はログイン後も残高(pt)が無いと使えないため、
// ログイン済みかつ残高0の場合は「要課金」と案内する（ユーザー指摘）。
function aiGateLabel(label) {
  if (state.isGuest) return `🔒 ${label}(要ログイン)`;
  if (!state.hasAiBalance) return `🔒 ${label}(要課金)`;
  return label;
}
function aiGateDisabled() {
  return state.isGuest || !state.hasAiBalance;
}

// 英会話/リーディング/ライティング/リスニングは無課金では使えないため、
// 上部の「生成」等が押せないだけでは気付きにくく、ページ下部の無料サンプル
// (sampleMaterialsCard)にたどり着けないまま離脱していた恐れがある
// (2026-08-29・実機ログ分析で判明)。当初は「こちら↓」リンクでサンプルまで
// スクロールする案内にしていたが、押しても既に画面内に見えていることが
// あり「反応していない」ように見えると指摘された(2026-08-30)。
// スクロールで誘導するのではなく、案内の直後(生成カードより上)に
// サンプル自体を差し込んで先頭に来るようにする(placeSampleCard参照)。
function sampleGateBanner() {
  if (!aiGateDisabled()) return "";
  return `<div class="sample-gate-banner">
    ⚠️ この機能はご登録・チャージが必要です。
    無課金でも見られるサンプルを下記にご用意しています。
  </div><div id="sampleSlotTop"></div>`;
}
// ゲート中(未登録/残高無し)はサンプルを冒頭のバナー直後(先頭)に、
// そうでなければ従来どおり末尾に補足として置く。
function placeSampleCard(root, card) {
  const top = root.querySelector("#sampleSlotTop");
  if (top) { top.replaceWith(card); return; }
  root.appendChild(card);
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

// --- Welcome（未ログインの初期表示。2026-08-24: ルート直アクセス時に説明
// 無しでいきなり単語一覧ツールが出て離脱を招いていた問題への対応。文章量は
// 抑え、詳しい説明はabout.htmlへ誘導する）------------------------------------

// メタ/ユーティリティ系タブは「収録機能」として数える意味が薄いので除外。
const WELCOME_HIDDEN_FEATURE_TABS = new Set([
  "welcome", "dashboard", "admin", "settings", "history", "release",
]);

// 動画ギャラリー(video-gallery.js)を、コンテナが画面に近づいたときにだけ
// 動的importして描画する(2026-09-20)。トップの初期JS・転送量・LCPに含めない
// ため。IntersectionObserverが無い環境・読み込み失敗・動画0本のときは何も出さず
// (場所取り用の空白も畳む)、他の表示に影響しない(壊れたUIを出さない)。
// コンテナは描画前も、出来上がりとほぼ同じ高さの空白を確保している
// (style.cssの.vg-slot:empty::before)。読み込み時に下の「収録語彙分野一覧」が
// 押し下げられて画面がガクッと動く(CLS)のを防ぐため。
function mountVideoGalleryLazily(box) {
  if (!box) return;
  const giveUp = () => box.classList.add("vg-empty");   // 場所取りを畳む
  if (typeof IntersectionObserver === "undefined") { giveUp(); return; }
  const io = new IntersectionObserver((entries) => {
    if (!entries.some((e) => e.isIntersecting)) return;
    io.disconnect();
    if (!box.isConnected) return;   // 既に別タブへ移動していた
    import("./video-gallery.js")
      .then((m) => { if (!m.renderVideoGallery(box)) giveUp(); })
      .catch(giveUp);
  }, { rootMargin: "0px" });   // 余白を取らない=折り下では何も読み込まない
  io.observe(box);
}

// ようこそ画面が「どこまで見られたか」の計測(2026-09-22)。「見て興味なし」と
// 「そもそも主ボタン/サンプル/動画に気づかれていない」を区別して、ようこそ画面から
// 次へ進まない原因を分析するため。送るのは次の種類の名前だけ(1人1ページ表示に
// つき各1回まで・入力内容や位置の座標は送らない):
//   seen:<部品>   その部品が画面に入った(cta/shots/sample/more/videos/domains/features)
//   scroll:first  実際にスクロールした(40px超)
//   depth:<n>     ようこそカードの何%まで画面に入ったか(25/50/75/100)
//   os:/theme:    OSの配色設定(dark/light)と実際に表示したテーマ
// kind="boot"・category="welcome_view"で送る(=操作ではない受動的な計測。
// kind="click"だと管理画面の「何か操作した人」に混ざるため・server側
// _WELCOME_LABEL_RE参照)。失敗しても画面には影響させない(api.trackはbest-effort)。
function trackWelcomeView(root) {
  const sent = new Set();
  const send = (label) => {
    // 別タブへ移動した後(rootが画面から外れた後)は何も送らない。
    if (sent.has(label) || !root.isConnected) return;
    sent.add(label);
    api.track("boot", "welcome_view", label);
  };
  try {
    const osDark = window.matchMedia
      && window.matchMedia("(prefers-color-scheme: dark)").matches;
    send(osDark ? "os:dark" : "os:light");
    send(document.documentElement.dataset.theme === "light"
      ? "theme:light" : "theme:dark");
  } catch (e) { /* 計測失敗は無視 */ }

  // 部品が画面に入ったか。縦に長い部品(動画欄)は半分に届かないことがあるので
  // 部品ごとに必要な割合を持つ。
  const need = new Map();   // element -> [key, 必要な表示割合]
  const io = typeof IntersectionObserver === "undefined" ? null
    : new IntersectionObserver((entries) => {
      entries.forEach((e) => {
        const it = need.get(e.target);
        if (!it || e.intersectionRatio < it[1]) return;
        send("seen:" + it[0]);
        io.unobserve(e.target);
        need.delete(e.target);
      });
    }, { threshold: [0.05, 0.5] });
  const watch = (el, key, ratio = 0.5) => {
    if (!io || !el) return;
    need.set(el, [key, ratio]);
    io.observe(el);
  };
  watch(root.querySelector(".welcome-cta-row"), "cta");
  watch(root.querySelector("#welcomeShots"), "shots");
  watch(root.querySelector(".welcome-more"), "more");
  watch(root.querySelector("#welcomeVideos"), "videos", 0.05);
  watch(root.querySelector("#welcomeDomainLabel"), "domains");
  watch(root.querySelector("#welcomeFeatureLabel"), "features");

  // スクロール量。どのスクロール枠でも同じ意味になるよう、ようこそカードの
  // 上端・高さと画面の高さから「カードの何%まで画面に入ったか」を出す。
  const card = root.querySelector(".welcome-card");
  const startY = window.scrollY;
  let ticking = false;
  const measure = () => {
    if (!root.isConnected || !card) return;
    if (Math.abs(window.scrollY - startY) > 40) send("scroll:first");
    const r = card.getBoundingClientRect();
    if (r.height <= 0) return;
    const seenRatio = (window.innerHeight - r.top) / r.height;
    [25, 50, 75, 100].forEach((d) => {
      if (seenRatio >= (d === 100 ? 0.98 : d / 100)) send("depth:" + d);
    });
  };
  const onScroll = () => {
    if (!root.isConnected) {
      window.removeEventListener("scroll", onScroll);
      return;
    }
    if (ticking) return;
    ticking = true;
    requestAnimationFrame(() => { ticking = false; measure(); });
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  // 最初の1画面ぶん(スクロールしなくても見えている量)。サンプル・一覧が
  // 差し込まれて高さが落ち着いてから測る(早すぎるとカードが低く見えて
  // 「最後まで見た」と誤判定するため)。
  setTimeout(measure, 2000);
  return { watch };
}

export async function welcome(root) {
  // facetsは本体表示に必須ではない「収録語彙分野一覧」の飾りチップにしか
  // 使わないため、これを待たずに先にヒーロー本体(見出し・CTA)を描画する
  // (2026-09-07・初期表示速度の改善。以前はfacets取得完了までroot自体が
  // 空のままで、直列3回目のAPI呼び出し待ちが白画面離脱の一因になって
  // いた)。取得でき次第、非同期にチップ部分だけ差し込む。
  const featureChips = TABS
    .filter(([tab]) => !WELCOME_HIDDEN_FEATURE_TABS.has(tab))
    .map((entry) => `<span class="pill">${escapeHtml(tabLabel(entry))}</span>`)
    .join("");
  // 文言の方針(2026-09-22・オーナー方針「英語学習で来た人にも、ニッチ・専門用語が
  // 好きな人にも見てもらう。ただし書きすぎると読まれない」): ファーストビューの文字は
  // 「一言のフック(見出し)+一行の補足+ボタン+ハードルを下げる一行」だけにし、
  // 語源・豆知識(うんちく)や目玉機能は文章ではなく実物(下のサンプル・動画サムネイル)で
  // 見せる。事実の裏付け(景表法配慮・公開する主張は検証可能なものだけ):
  //   - 妖怪=フレーズ場面「妖怪・日本の伝承の英語」/無線=単語「アマチュア無線・無線通信」等/
  //     歴史=「歴史（一般）」等/名言=「名言・名台詞」等が本番に収録されている(2026-09-22確認)。
  //   - 「音声の無料枠が2倍」=未登録は単語1,000語+フレーズ750件・無料登録は2,000語+1,500件
  //     (app/services/access_tiers.py)。「メールだけ・カード不要・ニックネームOK」=登録フォーム
  //     の実仕様(メール・パスワード・呼び名が必須。呼び名は仮名可・カード情報は取得しない)。
  //     ※「名前不要」とは書かない(呼び名は必須のため)。登録しても学習記録は保存されない
  //     (課金者のみ)ので「記録が残る」とも書かない。
  //   - 「語源・豆知識などの解説」は本番のほぼ全語(99.6%)に解説があり、語源は93%・豆知識は89%の
  //     語にあること(全語ではないので「など」で限定)、「¥800〜」は最小チャージ額
  //     (fulfillment.PRICE_TABLE)に基づく。「広告なし」等は書かない。
  // 日本語の文中でテンプレートリテラルを改行すると空白が表示されてしまう
  // (例: 「ニッチな 分野」)ため、長い文は文字列連結で組み立てる(tx()の
  // 訳文側も同じ理由で改行を入れない)。多言語化(2026-09-23)で全てtx()経由に
  // した(キーの根拠となる事実確認済みの日本語文言は元コメント参照)。
  const heroTitle = tx("welcome.heroTitle");
  const heroLead = tx("welcome.heroLead");
  const heroPrice = tx("welcome.heroPrice");
  // 収録数(2026-09-22・オーナー案「収録語数・フレーズ数・分野数を書いてもいいかも」)。
  // 根拠=2026-09-22の本番のゲスト表示: 単語16,420語(/api/words の一覧のid数。/api/words/stats
  // の16,510は禁止用語を含む・facetsの分野別合計16,517は複数分野タグの重複を含む=数え方で
  // 幅がある)・フレーズ7,646件(/api/phrases)・分野234(/api/words/facets)。**実数より小さく
  // 切り捨てて表示し、「以上」を付ける**(語彙は増える一方なので過大表示にならない・公開する
  // 数字は検証可能に)。語彙が大きく増えたらこの3つの数字(words/phrases/domains)を見直すこと。
  const heroCounts = tx("welcome.heroCounts",
    { words: "16,000", phrases: "7,500", domains: "230" });
  // 目玉機能の動画サムネイル(video-gallery.jsのVIDEOSのnameと揃える・軽量な専用画像)。
  const SHOTS = [
    ["flash_word", "welcome.shot.flashWord"],
    ["phrase_polite", "welcome.shot.phrasePolite"],
    ["crossword", "welcome.shot.crossword"],
  ];
  const shotsHtml = SHOTS.map(([name, key]) => `
    <button type="button" class="welcome-shot" data-name="${name}"
      aria-label="${escapeHtml(tx("welcome.shot.watchAria", { label: tx(key) }))}">
      <img src="/static/video/posters/thumb_${name}.jpg?v=1" alt=""
        width="200" height="356" decoding="async" />
      <span class="welcome-shot-cap">${escapeHtml(tx(key))}</span>
    </button>`).join("");
  root.innerHTML = `
    <div class="welcome-hero">
      <div class="card welcome-card">
        <div class="welcome-head">
          <img class="welcome-logo" src="/static/img/nyangailab_icon_128.png?v=1"
            alt="nyangailab" width="64" height="64" decoding="async" />
          <div class="welcome-head-text">
            <div class="welcome-brand">nyangailab</div>
            <h1>${heroTitle}</h1>
          </div>
        </div>
        <p class="muted welcome-lead">${heroLead}</p>
        <p class="welcome-counts">📚 ${heroCounts}</p>
        <div class="row welcome-cta-row">
          <a class="btn welcome-cta" href="/login#signup">
            ${tx("welcome.ctaSignup")}</a>
          <button class="btn ghost welcome-try" id="welcomeTryBtn">
            ${tx("welcome.ctaTry")}</button>
        </div>
        <p class="muted welcome-note">
          ${tx("welcome.noteLine1")}<br>
          <b>${tx("welcome.noteLine2")}</b></p>

        <div class="welcome-shots" id="welcomeShots">
          <div class="welcome-shots-label">🎬 ${tx("welcome.shotsLabel")}</div>
          <div class="welcome-shots-row">${shotsHtml}</div>
        </div>

        <div class="welcome-sample" id="welcomeSample" hidden></div>

        <p class="muted welcome-price">${heroPrice}</p>
        <p class="muted mt welcome-more">
          <a href="/static/about.html">${tx("welcome.moreLink")}</a></p>

        <div class="vg-slot" id="welcomeVideos"></div>

        <p class="welcome-scroll-label" style="margin-top:28px"
          id="welcomeDomainLabel">${tx("welcome.domainLabelLoading")}</p>
        <div class="row welcome-scroll-row" id="welcomeDomainChips"></div>

        <p class="welcome-scroll-label" id="welcomeFeatureLabel">${tx("welcome.featureLabel")}</p>
        <div class="row welcome-scroll-row">${featureChips}</div>
      </div>
    </div>`;
  const view = trackWelcomeView(root);
  // 目玉サムネイル: 押すと下の動画欄の該当カードまで移動して強調する(自動再生は
  // しない=音が急に出ないように。再生はカードのポスターを押してもらう)。動画欄は
  // 画面に近づいた時に遅延読み込みされるので、できるまで少し待つ。
  root.querySelectorAll(".welcome-shot").forEach((btn) => {
    btn.addEventListener("click", () => {
      const name = btn.dataset.name;
      api.track("click", "welcome", "shot:" + name);
      const box = root.querySelector("#welcomeVideos");
      if (!box) return;
      box.scrollIntoView({ behavior: "smooth", block: "start" });
      let tries = 0;
      const timer = setInterval(() => {
        const card = box.querySelector(`.vg-card[data-name="${name}"]`);
        if (card || ++tries > 20 || !root.isConnected) {
          clearInterval(timer);
          if (!card) return;
          card.scrollIntoView({ behavior: "smooth", block: "center" });
          card.classList.add("vg-flash");
          setTimeout(() => card.classList.remove("vg-flash"), 1800);
        }
      }, 150);
    });
  });
  // 管理画面の集計用に、文言が変わっても数え漏れない安定キーを送る(全ボタン
  // 共通のクリック計測(ボタン文言)とは別・2026-09-21)。
  root.querySelector("#welcomeTryBtn")?.addEventListener("click", () => {
    api.track("click", "welcome", "cta:try_without_signup");
    go("vocab");
  });
  root.querySelector(".welcome-cta")?.addEventListener("click", () =>
    api.track("click", "welcome", "cta:signup"));

  // 「本物の1語サンプル」(2026-09-20): 未登録ゲストが無料で再生できる語を
  // 1つ、既存の解説データ(語源/豆知識の一文)と一緒に見せ、登録前に
  // アプリ自体を体験してもらう。語の選定・解決はサーバー側
  // (featured_samples.resolve_hero_word)。条件を満たす語が無ければ何も出さず、
  // 解説が無い語は行ごと出さない(捏造しない)。画像・動画・動きは足さない。
  api.get("/api/words/hero-sample").then((r) => {
    const w = r && r.word;
    const box = root.querySelector("#welcomeSample");
    if (!w || !box) return;
    box.innerHTML = `
      <div class="welcome-sample-label">👂 ${tx("welcome.sampleLabel")}</div>
      <div class="welcome-sample-word">
        <b class="welcome-sample-en">${escapeHtml(w.english)}</b>
        <span class="welcome-sample-ja">${escapeHtml(w.japanese || "")}</span>
        <span class="pill">${escapeHtml(w.domain || "")}</span>
      </div>
      <div class="welcome-sample-play"></div>
      <p class="welcome-sample-note"><b>${escapeHtml(w.note_label)}:</b>
        ${escapeHtml(w.note)}</p>`;
    // 押す場所が分かるよう「▶ 男声/女声」のラベル付きにする(従来は🆓の絵文字だけで
    // 再生ボタンに見えなかった・2026-09-22)。
    const play = voiceButtonsItem(
      "word", w.id, "word", () => w.english, () => "std", true, true);
    // 全ボタン共通のクリック計測とは別に、トップの1語サンプル由来の再生で
    // あることが分かるよう1件残す(再生自体はサーバー側がplayとして記録)。
    play.addEventListener("click", () =>
      api.track("click", "welcome", "hero_sample_play:" + w.english));
    box.querySelector(".welcome-sample-play").append(play);
    box.hidden = false;
    view.watch(box, "sample");
  }).catch(() => { /* サンプルが出せなくてもトップは通常表示 */ })
    // 動画ギャラリーは1語サンプルの挿入で位置が動いた後に判定する(前だと
    // 折り下なのに画面内と誤判定して初期表示で読み込んでしまう)。
    .finally(() => mountVideoGalleryLazily(root.querySelector("#welcomeVideos")));

  // ここから先は非同期(fire-and-forget)。ユーザーが既に別タブへ移動して
  // rootの中身が差し替わっていた場合はquerySelectorがnullを返すだけなので
  // 安全（該当id要素が無ければ何もしない）。
  api.get("/api/words/facets").then((facets) => {
    const domains = facets.domains || [];
    const domainCounts = facets.domain_counts || {};
    const label = root.querySelector("#welcomeDomainLabel");
    const chips = root.querySelector("#welcomeDomainChips");
    if (label) {
      label.textContent = tx("welcome.domainLabel", { count: domains.length });
    }
    if (chips) {
      chips.innerHTML = domains.map((d) =>
        `<span class="pill">${escapeHtml(d)} ${domainCounts[d] ?? 0}</span>`)
        .join("");
    }
  }).catch(() => {
    const label = root.querySelector("#welcomeDomainLabel");
    if (label) label.remove();
  });
}

// --- Dashboard --------------------------------------------------------------

export async function dashboard(root) {
  // 6本のAPI呼び出しをすべて並列実行する(2026-09-07・以前はprogress→
  // my-usage→デッキ系4本の3段階直列で、初期表示までの待ち時間が
  // 積み上がっていた)。Promise.allSettledで、各呼び出しの成功/失敗
  // 判定・部分失敗時のフォールバックという元の挙動はそのまま保つ。
  const [pRes, muRes, decksRes] = await Promise.allSettled([
    api.get("/api/system/progress"),
    api.get("/api/system/my-usage"),
    Promise.all([
      api.get("/api/decks/summary"), api.get("/api/phrase-decks/summary"),
      api.get("/api/decks"), api.get("/api/phrase-decks"),
    ]),
  ]);
  if (pRes.status === "rejected") throw pRes.reason;
  const p = pRes.value;
  const mu = muRes.status === "fulfilled" ? muRes.value : null;
  let deckSummary = null, phraseDeckSummary = null;
  let myWordDecks = [], myPhraseDecks = [];
  if (decksRes.status === "fulfilled") {
    [deckSummary, phraseDeckSummary, myWordDecks, myPhraseDecks] =
      decksRes.value;
  } // 未ログイン等で失敗しても致命的ではない
  const isAdmin = mu && mu.role === "admin";
  // 習熟度・TOEIC換算等は登録後にユーザーごとに貯まる実績なので、未ログイン
  // (ゲスト)は「—」表示にする(2026-09-23・共有の疑似ユーザー行の残留実績が
  // 数値として見えてしまっていた不具合の修正・APIがNoneを返すようにした側)。
  // カタログの全件数(w.total等)はユーザー非依存なので対象外(従来通り)。
  const n0 = (v) => (v == null ? "—" : v);
  const toeic = (p.toeic_estimate == null) ? "未判定" : p.toeic_estimate;
  // 一般ユーザーには費用額を見せない（管理者のみ）。残高があれば残高を表示。
  let costNum = "—", costLbl = "今日のAI費用";
  if (isAdmin && mu) { costNum = "¥" + mu.today_jpy; }
  else if (mu && mu.balance_jpy != null) {
    costNum = Math.round(mu.balance_jpy) + "pt"; costLbl = "チャージ残高";
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
        <span class="muted">${n0(v.avg_mastery)} / 100</span></div>
      <div class="bar mt"><span style="width:${Math.min(100, v.avg_mastery || 0)}%">
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
    <h1>ダッシュボード ${infoIcon("help-dashboard",
      "今の学習状況を一覧で確認する画面です。「TOEIC換算」は学習データ" +
      "からの目安で、実際のスコアを保証するものではありません。" +
      "「平均習熟度」は単語+フレーズの習熟度ptの平均、「習得数」は" +
      "「覚えた」の基準(既定100pt)以上の数、「うろ覚え」はその手前の数" +
      "です。ログインすると学習するたびに更新されます。")}</h1>
    <p class="sub">今日の学習を始めましょう。1回 約10分でOK。</p>

    <div class="grid cols-3 stats-wrap">
      <div class="card stat">
        <div class="num">${toeic}</div>
        <div class="lbl">TOEIC換算(目安)</div></div>
      <div class="card stat">
        <div class="num">${n0(p.overall_avg_mastery)}</div>
        <div class="lbl">平均習熟度(単語+フレーズ)</div></div>
      <div class="card stat">
        <div class="num">${costNum}</div>
        <div class="lbl">${costLbl}</div></div>
    </div>

    <div class="card">
      <h2>単語の状況</h2>
      <div class="grid cols-3 stats-wrap">
        <div class="stat"><div class="num">${w.total}</div>
          <div class="lbl">全件数</div></div>
        <div class="stat"><div class="num">${n0(w.studied)}</div>
          <div class="lbl">学習数(出題済み)</div></div>
        <div class="stat"><div class="num">${n0(w.mastered)}</div>
          <div class="lbl">習得数(100+)</div></div>
        <div class="stat"><div class="num">${n0(w.vague)}</div>
          <div class="lbl">うろ覚え(40-79)</div></div>
        <div class="stat"><div class="num">${n0(w.avg_mastery)}</div>
          <div class="lbl">平均習熟度</div></div>
        <div class="stat"><div class="num">${p.phrases.total}</div>
          <div class="lbl">フレーズ全件</div></div>
      </div>
      <p class="muted mt">※全件数は単語を追加すると増えます。TOEIC換算は学習データに
        基づくあくまで目安です。実際のTOEICテストのスコアとの対応を
        保証するものではありません。</p>
    </div>

    ${state.isGuest ? `<div class="card">
      <h2>📁 単語帳・フレーズ帳</h2>
      <p class="muted">🔒 ログインすると使えます（自分専用の単語帳・
        フレーズ帳を作って学習できます）。</p>
    </div>` : (deckSummary || phraseDeckSummary) ? `<div class="card">
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

    <h2>項目別の習熟度 ${infoIcon("dash-areas",
      "英会話・リーディング・ライティング・リスニングなど、領域ごとの" +
      "習熟度の平均です。その領域を学習して記録が増えると伸びます。")}</h2>
    <div class="grid cols-2">${areaCards}</div>`;
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

// サンプル教材専用の読み上げバー(2026-08-13)。未ログイン・無課金でも
// 無料のOpenAI音声で聴けるよう、material.idベースの専用エンドポイント
// (speech.sayMaterial、/api/learn/samples/{id}/tts)を使う。単語/フレーズと
// 同じ男声(ash)/女声(nova)を選べ、速度(標準/ゆっくり/速い)も選べる。
function sampleReadAloudBar(material) {
  const bar = el(`<div class="row mt"></div>`);
  const playM = el(`<button class="btn ghost">🔊 男声で再生</button>`);
  const playF = el(`<button class="btn ghost">🔊 女声で再生</button>`);
  const stop = el(`<button class="btn ghost">⏹ 停止</button>`);
  // 初回再生は未キャッシュだとAI合成に数秒〜十数秒かかることがあり、
  // 無表示だと固まって見える(2026-08-13ユーザー指摘)。押した瞬間から
  // ボタンを無効化+「生成中…」表示にして、待ち時間を可視化する。
  const playing = async (btn, label, voice) => {
    const orig = btn.textContent;
    playM.disabled = true; playF.disabled = true;
    btn.textContent = "⏳ 生成中…";
    try {
      await speech.sayMaterial(material.id, voice);
    } finally {
      btn.textContent = orig;
      playM.disabled = false; playF.disabled = false;
    }
  };
  playM.addEventListener("click", () => playing(playM, "男声", MALE_VOICE));
  playF.addEventListener("click", () => playing(playF, "女声", FEMALE_VOICE));
  stop.addEventListener("click", () => speech.stopSpeaking());
  bar.append(playM, playF, stop, playbackSpeedControl());
  return bar;
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
//
// 【なぜ native に 1.15 を掛けるか（2026-08-22）】
// 「ネイティブ速度が標準とあまり変わらない」というユーザー指摘を受けて、
// 本番のTTSを実測した（scripts/tts_speed_test.py・12件×5条件）。結果:
//     learn         129.7 WPM
//     native(現行)  136.6 WPM  ← learn比 1.07倍。ほぼ差が無い＝指摘は正しい
//     指示文を強化   140.1 WPM  ← 1.11倍。効果が小さく、ばらつきも大きい
//                                （1語のとき無音同然になる事故も発生）
//     ＋速度1.15倍  151.2 WPM  ← 自然な会話の速さ(140〜170 WPM)に入る
//     ＋速度1.25倍  174.2 WPM  ← 速すぎ寄り
// TTS指示文を変えると (モデル,声,指示文,本文) のキャッシュが全部無効になり、
// 既にストックしてある native 音声 37,568件を作り直す費用が出る。一方、
// 再生速度は音程を保ったまま（speech.js の preservesPitch）即座に効き、
// 費用もかからないため、**指示文はそのまま・再生速度1.15倍**を採用した。
// 「ただ早送りにする」のとは違い、元音声は native 指示文で合成された
// リンキング・リズムのあるものなので、速さだけが会話の速度に寄る。
function speedOpts(mode) {
  if (mode === "native") return { speed: "native", rate: 1.15 };
  if (mode === "slow") return { speed: "learn", rate: 0.8 };
  return { speed: "learn", rate: 1.0 };
}

// 番号(ID)で再生する2ボタン。保存済みなら無料、無ければ合成して保存し
// 次回から無料。fallback はTTS不可時にブラウザ音声で読む英文。
// getMode() は 'slow'|'std'|'native' を返す（省略時 'std'）。
// isFreeRange===true のとき🆓表示（誰でも無料で再生できる範囲）。
// isFreeRange===false のとき、**実際にそのユーザーが再生できるかどうか**
// (state.hasAiBalance、app.jsのrefreshCost()参照)で🔒/🔊を出し分ける。
// 「再生できるのに🔒が出るのは変・再生できないなら🔒でよい」という指摘
// (2026-08-13)に沿い、ゲスト一律ではなく実際の可否(管理者=常に可・
// ゲスト=常に不可・それ以外は残高の有無)で判定する。
// 単語/フレーズ一覧の操作セルで「うろ覚え」と「覚えた/卒業」を別行に
// 分けるための0サイズの改行用要素。ボタン自体にflex-basis:100%を付けると
// ボタンの見た目まで幅いっぱいに伸びて他のボタンよりサイズが大きく見えて
// しまう(2026-09-09ユーザー指摘)ため、ボタンとは別に挟んで改行だけ起こす。
function opsBreak() {
  return el(`<span class="ops-break"></span>`);
}

function voiceButtonsItem(itemType, id, kind, fallback, getMode, isFreeRange,
  labelled = false) {
  const locked = isFreeRange === false && !state.hasAiBalance;
  const free = isFreeRange === true;
  const icon = locked ? "🔒" : (free ? "🆓" : "🔊");
  const lockNote = locked
    ? "・🔒無料範囲外（ログインすると再生できる場合があります）" : "";
  const freeNote = free ? "・🆓誰でも無料で再生できます" : "";
  const iconHtml = free
    ? `<span class="free-icon-glyph">${icon}</span>` : icon;
  // labelled=true: 文字付き(「▶ 男声」)。ようこそ画面の1語サンプル用で、他の画面は従来の
  // アイコンのみ。
  const mHtml = labelled ? "▶ 男声" : iconHtml;
  const fHtml = labelled ? "▶ 女声" : iconHtml;
  const cell = el(`<div class="voice-cell${labelled ? " voice-cell-labelled" : ""}">
    <button class="btn voice-m" title="男性の声 (ash)${lockNote}${freeNote}">${
      mHtml}</button>
    <button class="btn voice-f" title="女性の声 (nova)${lockNote}${freeNote}">${
      fHtml}</button></div>`);
  const [m, f] = cell.querySelectorAll("button");
  const play = (voice) => speech.sayItem(
    itemType, id, kind, voice, fallback(),
    speedOpts(getMode ? getMode() : "std"));
  m.addEventListener("click", () => play(MALE_VOICE));
  f.addEventListener("click", () => play(FEMALE_VOICE));
  return cell;
}

// 一覧の見出し行(2026-09-20)。未登録・未課金の既定表示で、先頭に固定した
// 厳選語と、その後の「無料で聞ける順」の一覧を区切る。
const FEATURED_HEAD = () => tx("list.featuredHeadWord");
const PHRASE_FEATURED_HEAD = () => tx("list.featuredHeadPhrase");
function listGroupHead(cols, text) {
  return el(`<tr class="lgh-row"><td class="lgh" colspan="${cols}">
    ${escapeHtml(text)}</td></tr>`);
}

// 一覧の並び(項目+昇順/降順)を画面ごとに端末(localStorage)へ記憶し、次に
// 開いたとき復元する(2026-09-20・オーナー決定)。保存が無い/使えない/不正な
// 値のときは既定(未登録・未課金=無料で聞ける順、それ以外=従来)に戻るだけで、
// 画面は常に正しく動く。localStorageは無効化・容量超過・プライベート
// ウィンドウ等で例外になりうるので、読み書きは必ずtry/catchで囲む。
// 許可する項目は各画面の<select id="fSort">のoption値と同じ(増減したら合わせる)。
const WORD_SORTS = ["mastery", "accuracy", "english", "level", "domain",
  "recent", "billing"];
const PHRASE_SORTS = ["mastery", "accuracy", "english", "scene", "recent",
  "added", "billing"];
function loadSavedSort(key, allowed) {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return null;
    const o = JSON.parse(raw);
    if (o && typeof o === "object" && allowed.includes(o.sort)) {
      return { sort: o.sort, desc: o.desc === true };
    }
  } catch (e) { /* 使えない・壊れている→既定に戻す */ }
  return null;
}
function saveSort(key, sort, desc) {
  try {
    localStorage.setItem(key, JSON.stringify({ sort, desc: !!desc }));
  } catch (e) { /* 保存できなくても画面は動く */ }
}

// --- ページネーション（1ページ20件 標準）---------------------------------
// 2026-09-07: 英単語・フレーズ一覧の初期表示速度改善のため既定を50→20に
// 変更(ユーザー指示)。1ページの描画件数を減らし体感速度を上げる狙い。

// 表示件数セレクト（20/50/100/500/全件、既定20）。value は数値 or 'all'。
function pageSizeSelect(id) {
  return `<select id="${id}" title="${escapeHtml(tx("filter.pageSizeTitle"))}">
    <option value="20" selected>${tx("filter.pageSize", { n: 20 })}</option>
    <option value="50">${tx("filter.pageSize", { n: 50 })}</option>
    <option value="100">${tx("filter.pageSize", { n: 100 })}</option>
    <option value="500">${tx("filter.pageSize", { n: 500 })}</option>
    <option value="all">${tx("filter.pageSizeAll")}</option></select>`;
}

// list を page/size で切り出す。size='all' は全件。
function pageSlice(list, page, size) {
  if (size === "all") return { slice: list, page: 0, pages: 1 };
  const n = parseInt(size, 10) || 20;
  const pages = Math.max(1, Math.ceil(list.length / n));
  const p = Math.min(Math.max(0, page), pages - 1);
  return { slice: list.slice(p * n, p * n + n), page: p, pages };
}

// 前/次ページのバーを作る。
function pagerBar(total, page, pages, onPrev, onNext) {
  const bar = el(`<div class="row pager"></div>`);
  const prev = el(`<button class="btn ghost">${tx("filter.prevPage")}</button>`);
  const next = el(`<button class="btn ghost">${tx("filter.nextPage")}</button>`);
  const info = el(`<span class="muted">${pages > 1
    ? tx("filter.pageOf", { page: page + 1, pages }) + " ・ " : ""}${tx("filter.totalCount", { n: total })}</span>`);
  prev.disabled = page <= 0;
  next.disabled = page >= pages - 1;
  prev.addEventListener("click", onPrev);
  next.addEventListener("click", onNext);
  bar.append(prev, info, next);
  return bar;
}

// 速度セレクト（ゆっくり/標準/ネイティブ）。value は slow/std/native。
// 2026-08-22: 単語・フラッシュカードにも「ネイティブ」を出すようにした
// （従来は「単語には native音声が無い」として隠していたが、実際には
// audio_store が word_native を保存できるので、押されたときに合成して
// 貯まる。ユーザーから「英単語のネイティブ速度が分からない」という
// 指摘があったのは、そもそも選択肢が無かったため）。
function speedSelect(id, withNative = true) {
  const nat = withNative
    ? `<option value="native">${tx("filter.speedNative")}</option>` : "";
  return `<select id="${id}" title="${escapeHtml(tx("filter.speedTitle"))}">
    <option value="std">${tx("filter.speedStd")}</option>
    <option value="slow">${tx("filter.speedSlow")}</option>${nat}</select>`;
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
  const badge = item.perfect
    ? `<span class="pill mastered" title="${escapeHtml(tx("mastery.perfectTitle"))}">
        ◎${tx("mastery.perfect")}</span>`
    : item.mastered
      ? `<span class="pill mastered">○${tx("mastery.known")}</span>`
      : item.vague
        ? `<span class="pill vague">△${tx("mastery.vague")}</span>` : "";
  return `<div class="mbar${cls}">
    <span style="width:${w}%;background:${color}"></span></div>
    <small class="muted">${m}</small> ${badge}`;
}

// 「覚えた / 戻す」トグルボタン。endpoint は /api/words or /api/phrases。
function knownButton(base, item, onChange) {
  const btn = el(`<button class="btn blue"></button>`);
  const paint = () => {
    btn.textContent = item.mastered ? tx("mastery.undo") : tx("mastery.known");
    btn.title = item.mastered
      ? tx("mastery.undoTitle")
      : tx("mastery.knownTitle");
  };
  paint();
  btn.addEventListener("click", async () => {
    const next = !item.mastered;
    try {
      const r = await api.post(`${base}/${item.id}/known`, { known: next });
      item.mastery = r.mastery;
      item.mastered = r.mastered;
      item.perfect = !!r.perfect;
      paint();
      if (onChange) onChange();
    } catch (e) { toast(tx("common.updateFailed")); }
  });
  return btn;
}

// 「うろ覚え」ボタン: 押すと mastery が少し加点される(既定+30・詳細設定で
// 調整可)。base は /api/words or /api/phrases。
function vagueButton(base, item, onChange) {
  const btn = el(`<button class="btn vague-btn"
    title="${escapeHtml(tx("mastery.vagueTitle"))}">${tx("mastery.vague")}</button>`);
  btn.addEventListener("click", async () => {
    try {
      const before = item.mastery;
      const r = await api.post(`${base}/${item.id}/vague`);
      item.mastery = r.mastery;
      item.mastered = r.mastered;
      item.perfect = !!r.perfect;
      if (onChange) onChange();
      toast(tx("mastery.vagueToast", { n: r.mastery - before }));
    } catch (e) { toast(tx("common.updateFailed")); }
  });
  return btn;
}

// 「卒業」ボタン(完全に覚えた): 満点に固定し、以後は忘却曲線で減らなく
// なる(2026-08-18)。「習得」は既存の「覚えた」表示(習得数/習得済み等)と
// 意味が被るため「卒業」を採用(ユーザー指示)。片方向のみ(解除ボタンは
// 無し・「クリア」してから「覚えた」を押せば通常の覚えた状態に戻せる)。
// base は /api/words or /api/phrases。
function perfectButton(base, item, onChange) {
  const btn = el(`<button class="btn good" title="${escapeHtml(
    tx("mastery.perfectBtnTitle"))}">${tx("mastery.perfect")}</button>`);
  btn.addEventListener("click", async () => {
    try {
      const r = await api.post(`${base}/${item.id}/perfect`,
        { perfect: true });
      item.mastery = r.mastery;
      item.mastered = r.mastered;
      item.perfect = r.perfect;
      if (onChange) onChange();
    } catch (e) { toast(tx("common.updateFailed")); }
  });
  return btn;
}

// 「クリア」ボタン: 習熟度を0ptにリセットする（1pt以上のときだけ表示）。
// base は /api/words or /api/phrases。
function clearButton(base, item, onChange) {
  const btn = el(`<button class="btn ghost"
    title="${escapeHtml(tx("mastery.clearTitle"))}">${tx("mastery.clear")}</button>`);
  const paint = () => {
    btn.style.display = item.mastery >= 1 ? "" : "none";
  };
  paint();
  btn.addEventListener("click", async () => {
    if (!confirm(tx("mastery.clearConfirm", { name: item.english }))) {
      return;
    }
    try {
      const r = await api.post(`${base}/${item.id}/restore`,
        { mastery: 0, review_level: 0, next_review: null });
      item.mastery = r.mastery;
      item.mastered = false;
      item.perfect = false;
      paint();
      if (onChange) onChange();
      toast(tx("mastery.clearedToast"));
    } catch (e) { toast(tx("common.updateFailed")); }
  });
  return { btn, paint };
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
// onClose: ✕/Esc/背景クリック/呼び出し元によるclose()呼び出しを問わず、
// 閉じられたときに必ず1回呼ばれる(2026-09-15・フラッシュ単語の開始前
// 選択ポップアップのように「閉じ方によらず後始末が要る」用途のため追加)。
function openModal(title, buildBody, onClose) {
  const ov = el(`<div class="modal-ov"></div>`);
  const box = el(`<div class="modal-box">
    <div class="row modal-head" style="justify-content:space-between">
      <h2 style="margin:0">${escapeHtml(title)}</h2>
      <button class="btn ghost" id="mClose">✕</button></div>
    <div class="modal-body mt"></div></div>`);
  const onKey = (e) => { if (e.key === "Escape") close(); };
  const close = () => {
    speech.stopSpeaking();
    document.removeEventListener("keydown", onKey);
    ov.remove();
    if (onClose) onClose();
  };
  // Escで閉じられない・長いモーダルで✕がスクロールアウトする指摘への対応
  // (2026-09-15・UIレビュー)。ヘッダーはCSS側でsticky化(.modal-head)。
  document.addEventListener("keydown", onKey);
  ov.addEventListener("click", (e) => { if (e.target === ov) close(); });
  box.querySelector("#mClose").addEventListener("click", close);
  buildBody(box.querySelector(".modal-body"));
  ov.appendChild(box);
  document.body.appendChild(ov);
  return close;
}

// フラッシュ単語/フラッシュフレーズの開始前に「無料で聴ける範囲のみ」か
// 「聴けないものも含める」かを毎回選んでもらうポップアップ(2026-09-15
// ユーザー要望: 音声無料範囲外の語が出題されて🔒でガッカリする事態を
// 避けたい)。戻り値: true=無料のみ/false=全部含める/null=キャンセル
// (✕・Esc・背景クリックで閉じた場合。呼び出し元は開始自体を中断する)。
function askFreeRangeChoice(kindLabel) {
  return new Promise((resolve) => {
    let resolved = false;
    const settle = (v) => { if (!resolved) { resolved = true; resolve(v); } };
    const close = openModal(`🔊 出題範囲を選択`, (body) => {
      body.innerHTML = `
        <p class="muted">音声無料範囲外の${kindLabel}も出題に含めますか？
          （範囲外は🔒で再生だけできません、表示・採点は変わりません）</p>
        <div class="row mt" style="flex-direction:column; gap:8px">
          <button class="btn" id="frcFreeOnly">🔊 無料で聴ける${kindLabel}のみ</button>
          <button class="btn ghost" id="frcAll">📚 聴けない${kindLabel}も含める</button>
        </div>`;
      body.querySelector("#frcFreeOnly").addEventListener("click", () => {
        settle(true); close();
      });
      body.querySelector("#frcAll").addEventListener("click", () => {
        settle(false); close();
      });
    }, () => settle(resolved ? undefined : null));
  });
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
  // 例文(英文＋日本語訳)。各例文に男声/女声の再生ボタンを付ける
  // (2026-09-09・多義語のように複数例文を持つ語で、それぞれの意味を
  // 音でも確認したいという要望に対応。POST /api/learn/tts はテキスト
  // 直接指定で都度合成するキャッシュ無し方式のため、再生のたびにAI
  // コストがかかる点に注意。頻繁に再生されるなら事前生成+キャッシュ化
  // を別途検討(docs/TODO.md参照)。
  // 先頭の読み上げ例文(primaryEn)と同じ文は重複表示しない。
  if (Array.isArray(d.examples) && d.examples.length) {
    const norm = (s) => (s || "").trim().toLowerCase().replace(/\.+$/, "");
    const exs = primaryEn
      ? d.examples.filter((x) => norm(x.en) !== norm(primaryEn))
      : d.examples;
    if (exs.length) {
      const wrap = el(`<div style="margin:6px 0"><b>例文:</b></div>`);
      exs.forEach((x) => {
        const row = el(`<div class="row" style="align-items:center; gap:8px; margin:4px 0">
          <div>${escapeHtml(x.en || "")}<br>
            <span class="muted">${escapeHtml(x.ja || "")}</span></div>
        </div>`);
        row.appendChild(voiceButtons(() => x.en || ""));
        wrap.appendChild(row);
      });
      box.appendChild(wrap);
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

// --- 管理者専用「メモ（管）」(2026-09-19ユーザー要望) ------------------------
// 単語/フレーズの詳細画面と設定画面に出す、管理者だけが押せるメモ入力。
// 外出先で「音声が間違っていた・訳を直したい」等の気づきをその場で記録し、
// あとで管理者画面の「📝 メモ（管）」タブで集計・検索する。記録先は
// POST /api/admin-memos(サーバー側でも管理者のみ許可。ここで非管理者に
// 出さないのは表示上の案内)。タグは下のクイック選択・自由入力・本文中の
// #タグのどれでも付けられ、画面ごとの自動タグ(単語/フレーズ/設定)も付く。
const ADMIN_MEMO_QUICK_TAGS = [
  "音声", "発音", "訳", "例文", "詳細", "分野・レベル", "表示", "バグ", "要望",
];
// ctx: { source: "word_detail"|"phrase_detail"|"settings",
//        kind?: "word"|"phrase", refId?, english?, japanese? }
function adminMemoWidget(ctx) {
  if (!state.isAdmin) return null;
  const wrap = el(`<div class="admin-memo mt">
    <button type="button" class="btn ghost am-open">📝 メモ（管）</button>
    <span class="muted am-done"></span>
    <div class="am-panel mt" style="display:none">
      <textarea class="am-text" style="width:100%; min-height:80px"
        placeholder="気づいたことをメモ（例: 音声が間違っている・訳を直したい）。本文に #タグ と書いてもタグになります"></textarea>
      <div class="row mt am-chips">${ADMIN_MEMO_QUICK_TAGS.map((t) =>
        `<label class="chk"><input type="checkbox" value="${escapeHtml(t)}"
          /> ${escapeHtml(t)}</label>`).join("")}</div>
      <input class="am-tags mt" style="width:100%"
        placeholder="タグを追加（スペース区切り 例: 要確認 ネイティブ）" />
      <div class="row mt">
        <button type="button" class="btn good am-ok">OK</button>
        <button type="button" class="btn ghost am-cancel">キャンセル</button>
        <span class="muted am-out"></span>
      </div>
    </div>
  </div>`);
  const q = (s) => wrap.querySelector(s);
  const panel = q(".am-panel");
  q(".am-open").addEventListener("click", () => {
    const open = panel.style.display === "none";
    panel.style.display = open ? "" : "none";
    if (open) q(".am-text").focus();
  });
  q(".am-cancel").addEventListener("click", () => {
    panel.style.display = "none";
  });
  q(".am-ok").addEventListener("click", async () => {
    const out = q(".am-out");
    const text = q(".am-text").value.trim();
    if (!text) { out.textContent = "メモを入力してください"; return; }
    const tags = [...wrap.querySelectorAll(".am-chips input:checked")]
      .map((c) => c.value)
      .concat(q(".am-tags").value.split(/[\s,、，]+/).filter(Boolean));
    const okBtn = q(".am-ok");
    okBtn.disabled = true;
    out.textContent = "記録中…";
    try {
      const r = await api.post("/api/admin-memos", {
        body: text, tags, source: ctx.source, ref_kind: ctx.kind || "",
        ref_id: ctx.refId ?? null, ref_english: ctx.english || "",
        ref_japanese: ctx.japanese || "",
      });
      q(".am-text").value = "";
      q(".am-tags").value = "";
      wrap.querySelectorAll(".am-chips input")
        .forEach((c) => { c.checked = false; });
      panel.style.display = "none";
      out.textContent = "";
      q(".am-done").textContent =
        `✅ 記録しました(#${r.id}・タグ: ${r.tags.join(" ")})`;
    } catch (e) {
      out.textContent = "記録に失敗しました: " + (e.message || "");
    } finally {
      okBtn.disabled = false;
    }
  });
  return wrap;
}

// 単語の詳細ポップアップ: 例文(再生)＋AI詳細(品詞/意味複数/派生/類義/対義/
// 由来/豆知識/解説)。詳細は押した時にAI生成→キャッシュ（2回目以降は無料）。
function showWordDetail(w) {
  // 登録に至らない原因分析(ファネル)の追加ステップ用(2026-09-13)。
  // 「英単語のページをみた」＝単語詳細を開いた回数(ゲストの guest_sid でも
  // 記録される。api.track内部でPOST /api/system/trackを叩くだけの
  // best-effort送信なので、失敗しても画面表示は妨げない)。
  api.track("page", "word_detail", w.english);
  openModal(w.english, (body) => {
    body.appendChild(el(`<p class="quiz-answer">${escapeHtml(w.english)}
      <span class="muted">${escapeHtml(w.japanese || "")}
      ${w.level ? "・Lv" + w.level : ""}</span></p>`));
    const memo = adminMemoWidget({
      source: "word_detail", kind: "word", refId: w.id,
      english: w.english, japanese: w.japanese,
    });
    if (memo) body.appendChild(memo);
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
        detailBox.innerHTML =
          `<p class="muted">失敗: ${escapeHtml(e.message || "")}</p>`;
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
  // showWordDetailのword_detailと対になる記録(2026-09-17・従来は
  // フレーズ詳細だけ汎用クリック記録(ボタン文言のみ)しか残らず、
  // どのフレーズを開いたか特定できなかった)。
  api.track("page", "phrase_detail", p.english);
  openModal(p.english, (body) => {
    body.appendChild(el(`<p class="quiz-answer">${escapeHtml(p.english)}
      <span class="muted">${escapeHtml(p.japanese || "")}
      ${p.scene ? "・" + escapeHtml(p.scene) : ""}</span></p>`));
    const memo = adminMemoWidget({
      source: "phrase_detail", kind: "phrase", refId: p.id,
      english: p.english, japanese: p.japanese,
    });
    if (memo) body.appendChild(memo);
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
        detailBox.innerHTML =
          `<p class="muted">失敗: ${escapeHtml(e.message || "")}</p>`;
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

  // トースト(「1つ戻りました」等)がカード下の採点ボタン列に重なって見えな
  // くなる指摘(2026-09-15・UIレビュー)への対応: このビュー滞在中だけ
  // トーストの表示位置を採点ボタンの上まで持ち上げる(CSS変数で調整・
  // 他画面のトーストには影響しない)。
  document.documentElement.style.setProperty("--toast-bottom", "128px");
  onLeaveView(() =>
    document.documentElement.style.removeProperty("--toast-bottom"));

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
      } catch (_) {
        // 2026-09-18修正: quiz.jsのmarkKnown/recordと同じ理由で、
        // 失敗が完全に無言だと採点未保存にユーザーが気づけないため
        // トーストを出す(それでも次のカードへは進む)。
        toast("⚠️ 記録に失敗しました(採点は保存されていません)");
      }
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
      // 採点時の手応え強化(2026-09-15・UIレビュー指摘: 反応が進捗の
      // 数字が増えるだけで薄かった)。カードが飛んでいく間だけ大きな
      // ラベルを重ねて表示する(次の描画までの150ms限定なので短く軽い)。
      const badgeText = { known: "⬆ 覚えた", wrong: "⬇ できない",
        vague: "➡ うろ覚え" }[action];
      const badgeCls = { known: "good", wrong: "bad", vague: "vague" }[action];
      cardEl.appendChild(
        el(`<div class="fc-grade-badge ${badgeCls}">${badgeText}</div>`));
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
        ・ できない <b>${counts.wrong}</b> ・ スキップ <b>${counts.skip}</b></p>
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
        スキップ${counts.skip}</div>
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
      kind, c.id, "word", () => c.english, () => speed, c.is_free_range));
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
    // セッション途中でフィルタを変更したくなっても、従来は全カードを
    // めくり終えるかメニューを再クリックするしかなかった(2026-09-15
    // ユーザー指摘)。プレイ中いつでも設定画面へ戻れるボタンを追加。
    const settingsBtn = el(`<button class="btn ghost">⚙️ 設定</button>`);
    settingsBtn.addEventListener("click",
      () => go(kind === "phrase" ? "flashphrase" : "flashcard"));
    tools.append(exBtn, detBtn, settingsBtn);
    // 採点ボタン(スワイプできない端末用)。
    const actions = stage.querySelector(".fc-actions");
    const mk = (cls, label, fn) => {
      const b = el(`<button class="btn ${cls}">${label}</button>`);
      b.addEventListener("click", fn);
      return b;
    };
    actions.append(
      mk("ghost", "⬅ 戻る", undo),
      mk("ghost", "⏭ 次へ（飛ばす）", () => grade("skip")),
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
  // 3本とも互いに依存が無いため並列実行する(2026-09-07・以前は直列3回で
  // 表示までの待ち時間が積み上がっていた)。
  const [facets, us, deckList] = await Promise.all([
    api.get(
      "/api/words/facets" + (showBanned() ? "?include_banned=true" : "")),
    // ゲストは/api/system/user-settingsを読めない(要ログイン)ため、既定は
    // オフ(=含む)・既定フィルターなしとして扱う。
    api.get("/api/system/user-settings")
      .catch(() => ({ settings: {} })).then((r) => r.settings || {}),
    // 自分の単語帳から選んでフラッシュする(2026-08-18・ユーザー要望:「作った
    // 単語帳のフラッシュをやることが多い」)。未ログイン/単語帳0件では
    // セレクタ自体を出さない。
    api.get("/api/decks").catch(() => []),
  ]);
  const hideMasteredDefault = !!us.hide_mastered;
  // 設定の既定フィルター(B10)を英単語一覧と同じ意味でフラッシュにも適用
  // (2026-09-14・TODO「既定フィルター拡張」対応)。
  const dfw = us.default_word_filters || {};
  const dfwActive = !!(dfw.category || dfw.level_min || dfw.level_max
    || dfw.mastered);
  const domainGroups = facets.domain_groups || {};
  const deckOpts = ['<option value="">-- 単語帳を使わない(分野・レベルで選ぶ) --</option>']
    .concat(deckList.map((d) =>
      `<option value="${d.id}">${escapeHtml(d.name)}（${d.total}語）</option>`))
    .join("");
  const catOpts = ['<option value="">全カテゴリ</option>']
    .concat(Object.keys(domainGroups).map((c) =>
      `<option>${escapeHtml(c)}</option>`))
    .join("");
  const lvOpts = '<option value="">--</option>' + facets.range_levels
    .map((l) => `<option>${escapeHtml(l)}</option>`).join("");
  const voiceOpts = speech.listOpenAIVoices().map((vn) => {
    const g = speech.voiceGender(vn);
    return `<option value="${vn}">声: ${vn}${g ? "（" + g + "）" : ""}</option>`;
  }).join("");

  root.innerHTML = `
    <h1>🃏 フラッシュ単語 ${infoIcon("help-flashcard",
      "単語カードを次々にめくって答え合わせする高速学習モードです。" +
      "分野・レベル・自分の単語帳から出題範囲を選べます。ログインすると" +
      "習熟度が記録され、覚えた語の出題を抑制できます。")}</h1>
    ${dfwActive ? `<p class="muted">⚙️ 設定の既定フィルターを適用中です。
      この画面でその場変更もできます。</p>` : ""}
    <div class="card" id="fcSetup">
      <p class="muted">単語帳をどんどんめくる高速学習。カードをタップで答え、
        スワイプ（または下のボタン）で採点します。</p>
      <div class="row">
        <select id="fcDir">
          <option value="en2ja">英和（英→日）</option>
          <option value="ja2en">和英（日→英）</option>
        </select>
        <select id="fcCategory" title="大分類">${catOpts}</select>
        <span class="cdrop">
          <button type="button" class="btn ghost" id="fcDomainBtn">分野: 全て ▾</button>
          <div class="cdrop-panel" id="fcDomainPanel"></div>
        </span>
      </div>
      ${deckList.length ? `<div class="row mt">
        <select id="fcDeck" title="自分の単語帳から選んでフラッシュする
          （選ぶと分野・レベルの絞り込みと併用できます）">${deckOpts}</select>
      </div>` : ""}
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
        ${infoIcon("mastered-filter", MASTERED_FILTER_HINT)}
      </div>
      <div class="row mt">
        <select id="fcSize">
          <option value="20">20枚</option>
          <option value="50">50枚</option>
          <option value="100">100枚</option>
        </select>
        ${speedSelect("fcSpeed")}
        <select id="fcVoice" title="読み上げの声（自然な声ONのとき）">
          ${voiceOpts}</select>
        <label class="toggle"><input type="checkbox" id="fcAuto"/>
          <b>答え表示で自動的に音声を再生する</b></label>
        <span style="color:var(--danger); font-weight:700;">
          ※ONにすると音量にご注意ください</span>
      </div>
      <div class="row mt">
        ${freeOnlyToggle("fcFreeOnly", "word")}
      </div>
      <div class="row mt">
        <button class="btn" id="fcStart">▶ 開始</button>
        <span class="muted" id="fcCount"></span>
      </div>
      <p class="muted fc-kbd-hint">PCキー操作: ↑覚えた ↓できない →うろ覚え
        ←戻る ／ Space・Enterで反転 ／ Sでスキップ</p>
    </div>
    <div id="fcStage"></div>`;

  const setVal = (id, v) => {
    const e = root.querySelector(id);
    if (e && v != null) e.value = v;
  };
  // 開始前に該当語数を表示する(2026-09-15・UIレビュー指摘: 開始するまで
  // 何件ヒットするか分からなかった)。フィルタを変えるたびに軽量な
  // count=trueクエリで再取得する(実データは取得しないので安価)。
  const fcFilterParams = () => {
    const v = (id) => root.querySelector(id).value;
    const dom = [...selectedDomains].join(",");
    const lvmin = v("#fcLvMin"), lvmax = v("#fcLvMax");
    const mastered = v("#fcMastered");
    const freeOnly = root.querySelector("#fcFreeOnly").checked;
    const deckId = fcDeckSel ? fcDeckSel.value : "";
    const p = {};
    if (dom) p.domain = dom;
    if (lvmin) p.level_min = lvmin;
    if (lvmax) p.level_max = lvmax;
    if (mastered) p.mastered = mastered;
    if (showBanned()) p.include_banned = "true";
    if (freeOnly) p.free_range_only = "true";
    if (deckId) p.deck_id = deckId;
    return p;
  };
  let fcCountSeq = 0;
  const refreshFcCount = async () => {
    const el2 = root.querySelector("#fcCount");
    if (!el2) return;
    const my = ++fcCountSeq;
    el2.textContent = "…";
    const q = new URLSearchParams({ count: "true", ...fcFilterParams() });
    try {
      const r = await api.get("/api/words/quiz?" + q.toString());
      if (my === fcCountSeq) el2.textContent = `該当 ${r.count}語`;
    } catch (_) { if (my === fcCountSeq) el2.textContent = ""; }
  };
  setVal("#fcDir", localStorage.getItem("fc_dir") || "en2ja");
  // 分野(複数選択可・大分類カスケード)。旧バージョンは単一分野文字列を
  // "fc_dom"に保存していたが、カンマ区切りの複数分野に対応(2026-08-13・
  // 一覧画面と同じinitCheckDropdownを流用)。
  const selectedDomains = new Set(
    (localStorage.getItem("fc_dom") || "").split(",").filter(Boolean));
  if (dfw.category) {
    // 既定フィルターの大分類は、クイズAPIがcategoryを受け付けないため
    // 配下の分野を全て選択した状態に展開する(前回の記憶より優先)。
    selectedDomains.clear();
    (domainGroups[dfw.category] || []).forEach((d) => selectedDomains.add(d));
    setVal("#fcCategory", dfw.category);
  } else {
    // 前回選んだ大分類の「表示」だけ復元する(2026-09-15・UIレビュー指摘:
    // 分野の選択自体はfc_domから復元済みなのに、大分類セレクトだけ毎回
    // 「全カテゴリ」に戻ってしまい紛らわしかった)。分野の絞り込み自体は
    // 既にselectedDomainsに入っているため、この表示合わせだけでよい。
    setVal("#fcCategory", localStorage.getItem("fc_category") || "");
  }
  const fcDomainDropdown = initCheckDropdown(root, "fcDomainBtn",
    "fcDomainPanel", () => {
      const cat = root.querySelector("#fcCategory").value;
      return cat ? { [cat]: domainGroups[cat] || [] } : domainGroups;
    }, selectedDomains, () => refreshFcCount(), "list.colDomain");
  root.querySelector("#fcCategory").addEventListener("change", () => {
    selectedDomains.clear();
    fcDomainDropdown.renderPanel();
    fcDomainDropdown.refreshLabel();
    refreshFcCount();
  });
  // 前回選んだ単語帳が今も存在する場合のみ復元(削除済みIDで空扱いになる
  // のを防ぐため、optionが実在するかをvalue設定後に確認)。
  const fcDeckSel = root.querySelector("#fcDeck");
  if (fcDeckSel) {
    const savedDeck = localStorage.getItem("fc_deck") || "";
    fcDeckSel.value = savedDeck;
    if (fcDeckSel.value !== savedDeck) fcDeckSel.value = "";
  }
  // 既定フィルターのレベル/覚えた状態も、localStorageの過去の選択より優先
  // する(下記マスタード済み判定と同じ考え方)。
  setVal("#fcLvMin", dfw.level_min || localStorage.getItem("fc_lvmin") || "");
  setVal("#fcLvMax", dfw.level_max || localStorage.getItem("fc_lvmax") || "");
  // 「詳細設定」がONなら毎回「隠す」を既定にする(localStorageの過去の選択
  // より優先。localStorageには開始のたび""でも上書き保存されるため、単純に
  // 「未設定なら」という判定だと2回目以降は永遠に効かなくなってしまう)。
  // その場でドロップダウンを変えれば、そのセッション限定で一時的に閲覧可能。
  setVal("#fcMastered", dfw.mastered || (hideMasteredDefault ? "hide" : "")
    || (localStorage.getItem("fc_mastered") || ""));
  setVal("#fcSize", localStorage.getItem("fc_size") || "50");
  setVal("#fcSpeed", localStorage.getItem("fc_speed") || "std");
  setVal("#fcVoice", localStorage.getItem("fc_voice")
    || speech.loadPreferredVoice() || "nova");
  // 既定OFF(2026-08-12〜): 開始した瞬間に音声が鳴って驚く、という指摘のため
  // （電車内等での利用を想定）。一度でも明示的に選んだ値はそちらを優先する。
  root.querySelector("#fcAuto").checked =
    (localStorage.getItem("fc_auto") ?? "0") === "1";
  root.querySelector("#fcFreeOnly").checked =
    localStorage.getItem("fc_free_only") === "1";
  // 件数表示を初期反映+以降フィルタ変更のたびに更新。
  ["#fcLvMin", "#fcLvMax", "#fcMastered", "#fcFreeOnly"].forEach((id) => {
    root.querySelector(id).addEventListener("change", refreshFcCount);
  });
  if (fcDeckSel) fcDeckSel.addEventListener("change", refreshFcCount);
  refreshFcCount();

  root.querySelector("#fcStart").addEventListener("click", async () => {
    // 開始前に毎回「無料で聴ける範囲のみ/聴けないものも含める」を選んで
    // もらう(2026-09-15ユーザー要望)。キャンセル(✕/Esc/背景クリック)
    // なら開始しない。選択結果は既存の#fcFreeOnlyへ反映するので、
    // 以降のロジック(fcFilterParams等)は変更不要。
    // 課金ユーザー・管理者は音声無料範囲の制限自体が無い(全語再生可)ため
    // この選択に意味が無く、聞かずにスキップする(2026-09-15ユーザー指摘)。
    if (state.isChargedTier) {
      root.querySelector("#fcFreeOnly").checked = false;
    } else {
      const choice = await askFreeRangeChoice("単語");
      if (choice === null) return;
      root.querySelector("#fcFreeOnly").checked = choice;
    }
    const v = (id) => root.querySelector(id).value;
    const dir = v("#fcDir"), dom = [...selectedDomains].join(",");
    const size = v("#fcSize");
    const speed = v("#fcSpeed"), voice = v("#fcVoice");
    const auto = root.querySelector("#fcAuto").checked;
    const fp = fcFilterParams();
    localStorage.setItem("fc_dir", dir);
    localStorage.setItem("fc_dom", dom);
    localStorage.setItem("fc_category", v("#fcCategory"));
    localStorage.setItem("fc_lvmin", fp.level_min || "");
    localStorage.setItem("fc_lvmax", fp.level_max || "");
    localStorage.setItem("fc_mastered", fp.mastered || "");
    localStorage.setItem("fc_size", size);
    localStorage.setItem("fc_speed", speed);
    localStorage.setItem("fc_voice", voice);
    localStorage.setItem("fc_auto", auto ? "1" : "0");
    localStorage.setItem("fc_free_only", fp.free_range_only ? "1" : "0");
    localStorage.setItem("fc_deck", fp.deck_id || "");

    const q = new URLSearchParams({ limit: size, ...fp });
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
    // 開始したら設定パネルを畳んでカードだけに集中できるようにする
    // (2026-09-15・UIレビュー指摘: 開始後も設定パネルが画面上部に残り、
    // カード・採点ボタンが画面外に押し出されていた)。
    root.querySelector("#fcSetup").style.display = "none";
    window.scrollTo({ top: 0, behavior: "instant" });
    runFlashcards(stage, queue, { dir, speed, auto, qs, voice, kind: "word" });
  });
}

export async function flashPhrase(root) {
  // 4本とも互いに依存が無いため並列実行する(2026-09-07・以前は末尾2本が
  // 直列だった)。
  const [sceneFacets, levelFacets, us, deckList] =
    await Promise.all([
      api.get(
        "/api/phrases/scenes" + (showBanned() ? "?include_banned=true" : "")),
      api.get("/api/phrases/facets"),
      // ゲストは/api/system/user-settingsを読めない(要ログイン)ため、既定は
      // オフ(=含む)・既定フィルターなしとして扱う。
      api.get("/api/system/user-settings")
        .catch(() => ({ settings: {} })).then((r) => r.settings || {}),
      // 自分のフレーズ帳から選んでフラッシュする(2026-08-18・フラッシュ単語と
      // 同じ理由)。未ログイン/フレーズ帳0件ではセレクタ自体を出さない。
      api.get("/api/phrase-decks").catch(() => []),
    ]);
  const hideMasteredDefault = !!us.hide_mastered;
  // 設定の既定フィルター(B10)をフレーズ一覧と同じ意味でフラッシュフレーズ
  // にも適用(2026-09-14・TODO「既定フィルター拡張」対応)。
  const dfp = us.default_phrase_filters || {};
  const dfpActive = !!(dfp.category || dfp.level_min || dfp.level_max
    || dfp.mastered);
  const deckOpts = ['<option value="">-- フレーズ帳を使わない(シーン・レベルで選ぶ) --</option>']
    .concat(deckList.map((d) =>
      `<option value="${d.id}">${escapeHtml(d.name)}（${d.total}件）</option>`))
    .join("");
  const sceneGroups = sceneFacets.scene_groups || {};
  const catOpts = ['<option value="">全カテゴリ</option>']
    .concat(Object.keys(sceneGroups).map((c) =>
      `<option>${escapeHtml(c)}</option>`))
    .join("");
  const lvOpts = '<option value="">--</option>' + levelFacets.range_levels
    .map((l) => `<option>${escapeHtml(l)}</option>`).join("");
  const voiceOpts = speech.listOpenAIVoices().map((vn) => {
    const g = speech.voiceGender(vn);
    return `<option value="${vn}">声: ${vn}${g ? "（" + g + "）" : ""}</option>`;
  }).join("");

  root.innerHTML = `
    <h1>🃏 フラッシュフレーズ ${infoIcon("help-flashphrase",
      "実用フレーズをカード形式で次々に答え合わせする高速学習モードです。" +
      "シーン・レベル・自分のフレーズ帳から出題範囲を選べます。")}</h1>
    ${dfpActive ? `<p class="muted">⚙️ 設定の既定フィルターを適用中です。
      この画面でその場変更もできます。</p>` : ""}
    <div class="card" id="fpSetup">
      <p class="muted">フレーズ帳をどんどんめくる高速学習。カードをタップで答え、
        スワイプ（または下のボタン）で採点します。</p>
      <div class="row">
        <select id="fpDir">
          <option value="en2ja">英和（英→日）</option>
          <option value="ja2en">和英（日→英）</option>
        </select>
        <select id="fpCategory" title="大分類">${catOpts}</select>
        <span class="cdrop">
          <button type="button" class="btn ghost" id="fpSceneBtn">シーン: 全て ▾</button>
          <div class="cdrop-panel" id="fpScenePanel"></div>
        </span>
      </div>
      ${deckList.length ? `<div class="row mt">
        <select id="fpDeck" title="自分のフレーズ帳から選んでフラッシュする
          （選ぶとシーン・レベルの絞り込みと併用できます）">${deckOpts}</select>
      </div>` : ""}
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
        ${infoIcon("mastered-filter", MASTERED_FILTER_HINT)}
      </div>
      <div class="row mt">
        <select id="fpSize">
          <option value="20">20枚</option>
          <option value="50">50枚</option>
          <option value="100">100枚</option>
        </select>
        ${speedSelect("fpSpeed")}
        <select id="fpVoice" title="読み上げの声（自然な声ONのとき）">
          ${voiceOpts}</select>
        <label class="toggle"><input type="checkbox" id="fpAuto"/>
          <b>答え表示で自動的に音声を再生する</b></label>
        <span style="color:var(--danger); font-weight:700;">
          ※ONにすると音量にご注意ください</span>
      </div>
      <div class="row mt">
        ${freeOnlyToggle("fpFreeOnly", "phrase")}
      </div>
      <div class="row mt">
        <button class="btn" id="fpStart">▶ 開始</button>
        <span class="muted" id="fpCount"></span>
      </div>
      <p class="muted fc-kbd-hint">PCキー操作: ↑覚えた ↓できない →うろ覚え
        ←戻る ／ Space・Enterで反転 ／ Sでスキップ</p>
    </div>
    <div id="fpStage"></div>`;

  const setVal = (id, v) => {
    const e = root.querySelector(id);
    if (e && v != null) e.value = v;
  };
  // 開始前に該当件数を表示する(flashcard()と同じ・2026-09-15)。
  const fpFilterParams = () => {
    const v = (id) => root.querySelector(id).value;
    const scene = [...selectedScenes].join(",");
    const lvmin = v("#fpLvMin"), lvmax = v("#fpLvMax");
    const mastered = v("#fpMastered");
    const freeOnly = root.querySelector("#fpFreeOnly").checked;
    const deckId = fpDeckSel ? fpDeckSel.value : "";
    const p = {};
    if (scene) p.scene = scene;
    if (lvmin) p.level_min = lvmin;
    if (lvmax) p.level_max = lvmax;
    if (mastered) p.mastered = mastered;
    if (showBanned()) p.include_banned = "true";
    if (freeOnly) p.free_range_only = "true";
    if (deckId) p.deck_id = deckId;
    return p;
  };
  let fpCountSeq = 0;
  const refreshFpCount = async () => {
    const el2 = root.querySelector("#fpCount");
    if (!el2) return;
    const my = ++fpCountSeq;
    el2.textContent = "…";
    const q = new URLSearchParams({ count: "true", ...fpFilterParams() });
    try {
      const r = await api.get("/api/phrases/quiz?" + q.toString());
      if (my === fpCountSeq) el2.textContent = `該当 ${r.count}件`;
    } catch (_) { if (my === fpCountSeq) el2.textContent = ""; }
  };
  setVal("#fpDir", localStorage.getItem("fp_dir") || "en2ja");
  // シーン(複数選択可・大分類カスケード)。flashcard()の分野と同じ設計。
  const selectedScenes = new Set(
    (localStorage.getItem("fp_scene") || "").split(",").filter(Boolean));
  if (dfp.category) {
    // 既定フィルターの大分類は、クイズAPIがcategoryを受け付けないため
    // 配下のシーンを全て選択した状態に展開する(前回の記憶より優先)。
    selectedScenes.clear();
    (sceneGroups[dfp.category] || []).forEach((s) => selectedScenes.add(s));
    setVal("#fpCategory", dfp.category);
  } else {
    // 前回選んだ大分類の「表示」だけ復元する(flashcard()と同じ・2026-09-15
    // UIレビュー指摘対応)。
    setVal("#fpCategory", localStorage.getItem("fp_category") || "");
  }
  const fpSceneDropdown = initCheckDropdown(root, "fpSceneBtn",
    "fpScenePanel", () => {
      const cat = root.querySelector("#fpCategory").value;
      return cat ? { [cat]: sceneGroups[cat] || [] } : sceneGroups;
    }, selectedScenes, () => refreshFpCount(), "list.colScene");
  root.querySelector("#fpCategory").addEventListener("change", () => {
    selectedScenes.clear();
    fpSceneDropdown.renderPanel();
    fpSceneDropdown.refreshLabel();
    refreshFpCount();
  });
  // 前回選んだフレーズ帳が今も存在する場合のみ復元(削除済みIDで空扱いに
  // なるのを防ぐ・flashcard()と同じ方式)。
  const fpDeckSel = root.querySelector("#fpDeck");
  if (fpDeckSel) {
    const savedDeck = localStorage.getItem("fp_deck") || "";
    fpDeckSel.value = savedDeck;
    if (fpDeckSel.value !== savedDeck) fpDeckSel.value = "";
  }
  // 既定フィルターのレベル/覚えた状態も、localStorageの過去の選択より優先
  // する(flashcard()と同じ考え方)。
  setVal("#fpLvMin", dfp.level_min || localStorage.getItem("fp_lvmin") || "");
  setVal("#fpLvMax", dfp.level_max || localStorage.getItem("fp_lvmax") || "");
  // 「詳細設定」がONなら毎回「隠す」を既定にする(理由はflashcard()と同じ)。
  setVal("#fpMastered", dfp.mastered || (hideMasteredDefault ? "hide" : "")
    || (localStorage.getItem("fp_mastered") || ""));
  setVal("#fpSize", localStorage.getItem("fp_size") || "50");
  setVal("#fpSpeed", localStorage.getItem("fp_speed") || "std");
  setVal("#fpVoice", localStorage.getItem("fp_voice")
    || speech.loadPreferredVoice() || "nova");
  // 既定OFF(2026-08-12〜): フラッシュ単語と同じ理由(開始直後に音声が鳴って
  // 驚くという指摘)。一度でも明示的に選んだ値はそちらを優先する。
  root.querySelector("#fpAuto").checked =
    (localStorage.getItem("fp_auto") ?? "0") === "1";
  root.querySelector("#fpFreeOnly").checked =
    localStorage.getItem("fp_free_only") === "1";
  ["#fpLvMin", "#fpLvMax", "#fpMastered", "#fpFreeOnly"].forEach((id) => {
    root.querySelector(id).addEventListener("change", refreshFpCount);
  });
  if (fpDeckSel) fpDeckSel.addEventListener("change", refreshFpCount);
  refreshFpCount();

  root.querySelector("#fpStart").addEventListener("click", async () => {
    // フラッシュ単語と同じく、開始前に毎回選んでもらう(2026-09-15)。
    // 課金ユーザー・管理者は無料範囲の制限自体が無いためスキップ。
    if (state.isChargedTier) {
      root.querySelector("#fpFreeOnly").checked = false;
    } else {
      const choice = await askFreeRangeChoice("フレーズ");
      if (choice === null) return;
      root.querySelector("#fpFreeOnly").checked = choice;
    }
    const v = (id) => root.querySelector(id).value;
    const dir = v("#fpDir"), scene = [...selectedScenes].join(",");
    const size = v("#fpSize");
    const speed = v("#fpSpeed"), voice = v("#fpVoice");
    const auto = root.querySelector("#fpAuto").checked;
    const fp = fpFilterParams();
    localStorage.setItem("fp_dir", dir);
    localStorage.setItem("fp_scene", scene);
    localStorage.setItem("fp_category", v("#fpCategory"));
    localStorage.setItem("fp_lvmin", fp.level_min || "");
    localStorage.setItem("fp_lvmax", fp.level_max || "");
    localStorage.setItem("fp_mastered", fp.mastered || "");
    localStorage.setItem("fp_size", size);
    localStorage.setItem("fp_speed", speed);
    localStorage.setItem("fp_voice", voice);
    localStorage.setItem("fp_auto", auto ? "1" : "0");
    localStorage.setItem("fp_free_only", fp.free_range_only ? "1" : "0");
    localStorage.setItem("fp_deck", fp.deck_id || "");

    const q = new URLSearchParams({ limit: size, ...fp });
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
    // 開始したら設定パネルを畳む(flashcard()と同じ・2026-09-15対応)。
    root.querySelector("#fpSetup").style.display = "none";
    window.scrollTo({ top: 0, behavior: "instant" });
    runFlashcards(stage, queue, { dir, speed, auto, qs, voice, kind: "phrase" });
  });
}

// 分野/シーンの複数選択チェックボックス・ドロップダウン（2026-08-06・
// ユーザー要望「フィルターを複数選択できるように」）。ボタンをクリックすると
// グループ分けされたチェックボックス一覧を開く。`selected`(Set)を直接
// ミューテートするので、呼び出し側はそのSetをフィルタ条件の組み立てに使う。
function initCheckDropdown(root, btnId, panelId, groupsGetter, selected,
  onChange, labelKey) {
  const btn = root.querySelector(`#${btnId}`);
  const panel = root.querySelector(`#${panelId}`);
  const refreshLabel = () => {
    const label = tx(labelKey);
    btn.textContent = selected.size
      ? tx("filter.dropdownSelected", { label, n: selected.size })
      : tx("filter.dropdownAll", { label });
  };
  const renderPanel = () => {
    const groups = groupsGetter();
    const allItems = Object.values(groups).flat();
    // 大分類を選んだ後、配下の分野を1つずつチェックしなくても済むように
    // 「すべて選択」を追加(2026-09-05ユーザー要望「大分類選んだらその下
    // の分類にすべて選択もあるといい」・initCheckDropdownは英単語/
    // フレーズ/クロスワードの分野・シーン選択で共通利用しているため、
    // ここを直せば全画面に反映される)。既に全件選択済みなら出さない。
    const allSelected = allItems.length > 0
      && allItems.every((it) => selected.has(it));
    const btnRow = (allItems.length > 1 && (!allSelected || selected.size))
      ? `<div class="cd-clear-row">
          ${allSelected ? "" : `<button type="button" class="btn ghost"
            id="${panelId}_all">${tx("filter.selectAllN", { n: allItems.length })}</button>`}
          ${selected.size ? `<button type="button" class="btn ghost"
            id="${panelId}_clear">${tx("filter.clearSelectionN", { n: selected.size })}
            </button>` : ""}
        </div>` : "";
    panel.innerHTML = btnRow + Object.entries(groups).map(([g, items]) => `
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
    panel.querySelector(`#${panelId}_all`)?.addEventListener("click", () => {
      allItems.forEach((it) => selected.add(it));
      refreshLabel();
      onChange();
      renderPanel();
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
    // 「すべて選択/クリア」ボタン押下時、その場のonChangeでrenderPanel()が
    // panel.innerHTMLを差し替えるためe.targetが既にDOMから外れており、
    // panel.contains(e.target)が誤ってfalseになりパネルが即座に閉じて
    // しまっていた(2026-09-15・UIレビュー指摘)。composedPath()は
    // イベント発火時点(=DOM書き換え前)の経路を保持しているため、これで
    // 判定すれば正しく「パネル内クリック」と認識できる。
    const path = e.composedPath ? e.composedPath() : [e.target];
    if (!path.includes(panel) && !path.includes(btn)) {
      panel.classList.remove("open");
    }
  });
  refreshLabel();
  renderPanel();
  return { renderPanel, refreshLabel };
}

export async function vocab(root) {
  // 3本とも互いに依存が無いため並列実行する(2026-09-07・以前は直列3回で
  // 表示までの待ち時間が積み上がっていた)。
  const [facets, myDecks, us] = await Promise.all([
    api.get(
      "/api/words/facets" + (showBanned() ? "?include_banned=true" : "")),
    api.get("/api/decks").catch(() => []),
    // ゲストは/api/system/user-settingsを読めない(要ログイン)ため、既定
    // フィルター無し(={})として扱う(2026-08-11・ゲスト実装で発見)。
    api.get("/api/system/user-settings")
      .catch(() => ({ settings: {} })).then((r) => r.settings || {}),
  ]);
  const domainGroups = facets.domain_groups || {};
  const dfw = us.default_word_filters || {};
  const dfwActive = !!(dfw.category || dfw.level_min || dfw.level_max
    || dfw.mastered);
  root.innerHTML = `
    <h1 id="pageTitle"><span id="pageTitleText">${tx("nav.vocab")}</span> ${infoIcon("help-vocab",
      tx("vocabList.helpText"))}</h1>
    ${dfwActive ? `<p class="muted">⚙️ ${tx("filter.defaultFilterActive")}</p>` : ""}
    <div class="card">
      <details class="log-group" id="vocabFilters"
        ${window.innerWidth <= 760 ? "" : "open"}>
      <summary>🔍 ${tx("filter.summary")} ${infoIcon("help-filter-words", WORD_FILTER_HELP)}</summary>
      <div class="row mt">
        <input id="kw" placeholder="${escapeHtml(tx("filter.searchPlaceholderWord"))}" style="width:140px" />
        <select id="fCategory" title="${escapeHtml(tx("filter.categoryTitle"))}"><option value="">${tx("filter.allCategories")}</option>
          ${Object.keys(domainGroups).map((c) =>
            `<option>${escapeHtml(c)}</option>`).join("")}</select>
        <span class="cdrop">
          <button type="button" class="btn ghost" id="fDomainBtn">${tx("filter.allDropdown")}</button>
          <div class="cdrop-panel" id="fDomainPanel"></div>
        </span>
        <span class="muted">Lv</span>
        <select id="fLevelMin" title="${escapeHtml(tx("filter.levelMinTitle"))}"><option value="">${tx("filter.lowerBound")}</option>
          ${(facets.range_levels || facets.levels).map((l) =>
            `<option>${escapeHtml(l)}</option>`).join("")}</select>
        <span class="muted">〜</span>
        <select id="fLevelMax" title="${escapeHtml(tx("filter.levelMaxTitle"))}"><option value="">${tx("filter.upperBound")}</option>
          ${(facets.range_levels || facets.levels).map((l) =>
            `<option>${escapeHtml(l)}</option>`).join("")}</select>
        ${state.isAdmin ? `<label class="toggle"
          title="${escapeHtml(tx("filter.outOfRangeTitle"))}">
          <input type="checkbox" id="fOutRange" /> ${tx("filter.outOfRange")}</label>
          ${infoIcon("out-of-range-filter", tx("filter.outOfRangeHelp"))}` : ""}
        ${freeOnlyToggle("fFreeOnly", "word")}
        ${myDecks.length ? `<select id="fDeck" title="${escapeHtml(tx("filter.deckFilterTitle"))}">
          <option value="">${tx("filter.deckAll")}</option>
          ${myDecks.map((d) =>
            `<option value="${d.id}">📘 ${escapeHtml(d.name)}</option>`)
            .join("")}</select>` : ""}
        <select id="fSort">
          <option value="mastery">${tx("filter.sortMastery")}</option>
          <option value="accuracy">${tx("filter.sortAccuracy")}</option>
          <option value="english">${tx("filter.sortEnglish")}</option>
          <option value="level">${tx("filter.sortLevel")}</option>
          <option value="domain">${tx("filter.sortDomain")}</option>
          <option value="recent">${tx("filter.sortRecent")}</option>
          <option value="billing">${tx("filter.sortBilling")}</option>
        </select>
        <button class="btn ghost" id="fDir"
          title="${escapeHtml(tx("filter.dirToggleTitle"))}">${tx("filter.ascending")}</button>
        <select id="fMastered" title="${escapeHtml(tx("filter.masteredFilterTitle"))}">
          <option value="">${tx("filter.masteredInclude")}</option>
          <option value="hide">${tx("filter.masteredHide")}</option>
          <option value="only">${tx("filter.masteredOnly")}</option>
        </select>
        ${infoIcon("mastery-legend", MASTERY_LEGEND_HINT)}
        ${speedSelect("wSpeed")}
        ${pageSizeSelect("wPage")}
        ${state.isAdmin ? `<label class="toggle"
          title="${escapeHtml(tx("filter.showBannedTitle"))}">
          <input type="checkbox" id="showBanned"
          ${showBanned() ? "checked" : ""} />
          🔞 ${tx("filter.showBanned")}</label>` : ""}
      </div>
      </details>
      <table class="mt rtable rtable-words"><thead><tr>
        <th>${tx("list.colPlay")}${infoIcon("voice-icon-legend", tx("list.voiceIconHelp"))}</th>
        <th>${tx("list.colEnglish")}</th><th>${tx("list.colJapanese")}</th><th>${tx("list.colDetail")}</th>
        <th>Lv</th>
        <th>${tx("list.colDomain")}</th><th>${tx("list.colMastery")}</th><th>${tx("list.colAccuracy")}</th><th>${tx("list.colActions")}</th></tr></thead>
        <tbody id="rows"></tbody></table>
      <div id="pager" class="mt"></div>
    </div>`;

  // 未登録・未課金は既定を「無料で聞ける順」にする(2026-09-20・お試し導線の
  // 着地改善)。課金者・管理者・テスターは従来の既定(習熟度)のまま。判定は
  // サーバー(state.freeFirstSort←/api/system/my-usage)。手動で選び直した
  // 並びはこの後の変更イベントでそのまま尊重される。
  if (state.freeFirstSort) root.querySelector("#fSort").value = "billing";
  // 前回手動で選んだ並びがあれば、既定より優先して復元する(2026-09-20)。
  const savedSort = loadSavedSort("vocab_sort", WORD_SORTS);
  if (savedSort) {
    root.querySelector("#fSort").value = savedSort.sort;
    if (savedSort.desc) {
      const dirBtn = root.querySelector("#fDir");
      dirBtn.dataset.desc = "1";
      dirBtn.textContent = tx("filter.descending");
    }
  }
  const rowsBody = root.querySelector("#rows");
  // 件数表示は専用spanだけを書き換える。h1ごとtextContentで上書きすると
  // 見出し内のⓘヘルプアイコンが最初の描画で消えてしまうため(2026-09-19修正)。
  const title = root.querySelector("#pageTitleText");
  const kw = root.querySelector("#kw");
  const pagerEl = root.querySelector("#pager");
  let curWords = [];
  let wPage = 0;
  const selectedDomains = new Set();

  const paint = () => {
    const size = root.querySelector("#wPage").value;
    const { slice, page, pages } = pageSlice(curWords, wPage, size);
    wPage = page;
    title.textContent = `${tx("nav.vocab")} (${curWords.length})`;
    // このページの直前の語(ページ境目で厳選語→そのほかに切り替わる場合に
    // 見出しを出すため)。
    const start = size === "all" ? 0 : page * (parseInt(size, 10) || 20);
    renderTable(slice, start > 0 ? curWords[start - 1] : null);
    pagerEl.innerHTML = "";
    pagerEl.appendChild(pagerBar(curWords.length, page, pages,
      () => { wPage = page - 1; paint(); },
      () => { wPage = page + 1; paint(); }));
  };

  const renderTable = (words, before = null) => {
    rowsBody.innerHTML = "";
    // 厳選語(featured)が先頭に固定されているときだけ見出し行を挟む。
    // キーワード検索中は絞り込み結果なので出さない。
    const groups = !kw.value.trim()
      && (words.some((w) => w.featured) || !!(before && before.featured));
    let prevFeatured = before ? !!before.featured : null;
    words.forEach((w) => {
      if (groups) {
        if (w.featured && prevFeatured === null) {
          rowsBody.appendChild(listGroupHead(9, FEATURED_HEAD()));
        } else if (!w.featured && prevFeatured === true) {
          rowsBody.appendChild(listGroupHead(9, tx("list.otherWords")));
        }
      }
      prevFeatured = !!w.featured;
      const tr = el(`<tr${w.featured ? ' class="featured-row"' : ""}>
        <td></td>
        <td data-label="${escapeHtml(tx("list.colEnglish"))}">${escapeHtml(w.english)}</td>
        <td data-label="${escapeHtml(tx("list.colJapanese"))}">${escapeHtml(w.japanese)}</td>
        <td><div class="detail-cell"></div></td>
        <td class="muted pair2" data-label="Lv">${w.level || ""}</td>
        <td class="pair2" data-label="${escapeHtml(tx("list.colDomain"))}">${w.domain
          ? `<span class="pill">${escapeHtml(w.domain)}</span>` : ""}</td>
        <td class="pair2" style="min-width:80px" data-mc="1"
          data-label="${escapeHtml(tx("list.colMastery"))}">${masteryCell(w)}</td>
        <td class="pair2" data-label="${escapeHtml(tx("list.colAccuracy"))}">${w.accuracy == null
          ? "—" : w.accuracy + "%"}</td>
        <td><div class="ops-cell"></div></td>
      </tr>`);
      // 番号(ID)で再生。保存済みなら無料、無ければ合成して保存。
      tr.firstElementChild.appendChild(voiceButtonsItem(
        "word", w.id, "word", () => w.english,
        () => root.querySelector("#wSpeed").value, w.is_free_range));
      const ops = tr.querySelector("td:last-child .ops-cell");
      const mc = tr.querySelector("[data-mc]");
      // 「詳細」は押し間違い防止のため他の操作ボタンから離し、日本語列の
      // すぐ横に専用列として表示する(2026-09-09ユーザー要望)。
      const ex = el(`<button class="btn good">${tx("list.detail")}</button>`);
      ex.addEventListener("click", () => showWordDetail(w));
      tr.querySelector(".detail-cell").appendChild(ex);
      let onChange = () => {};
      const { btn: clearBtn, paint: paintClear } =
        clearButton("/api/words", w, () => onChange());
      onChange = () => { mc.innerHTML = masteryCell(w); paintClear(); };
      const vague = vagueButton("/api/words", w, onChange);
      const known = knownButton("/api/words", w, onChange);
      const perfect = perfectButton("/api/words", w, onChange);
      ops.append(vague, opsBreak(), known, perfect, clearBtn);
      rowsBody.appendChild(tr);
    });
  };

  // 分野/レベル/並び替え/禁止表示はサーバ側、キーワードはクライアント側。
  // フィルタを連続で変更すると複数のload()が並行して発行され、後発の
  // 速い応答より先発の遅い応答が後から返って上書きしてしまうことがあった
  // (2026-08-30ユーザー報告「分野を選び直しても前の単語が残ることがある」)。
  // 呼び出しごとに連番を振り、自分より新しいload()が発行済みなら結果を
  // 捨てる(go()のmyRootと同じレースコンディション対策の考え方)。
  let loadSeq = 0;
  let baseWords = []; // 直近のサーバ取得結果(キーワード適用前)のキャッシュ
  // キーワードはサーバのクエリパラメータに含まれずクライアント側でしか
  // 絞り込んでいないため、1文字入力するたびにload()で全件再取得すると
  // 無駄な重いリクエストが積み重なり、体感で「検索し直しても反映されない」
  // ように見える不具合になっていた(2026-09-02ユーザー報告)。キーワード
  // 変更時はキャッシュ済みbaseWordsをその場でフィルタするだけにし、
  // サーバ再取得はキーワード以外のフィルタが変わったときだけ行う。
  const applyKeyword = () => {
    const term = kw.value.trim().toLowerCase();
    curWords = term ? baseWords.filter((w) =>
      w.english.toLowerCase().includes(term)
      || (w.japanese || "").toLowerCase().includes(term)) : baseWords;
    wPage = 0;
    paint();
  };
  const load = async () => {
    const seq = ++loadSeq;
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
    if (root.querySelector("#fOutRange")?.checked) q.set("out_of_range", "true");
    const ms = root.querySelector("#fMastered").value;
    if (ms) q.set("mastered", ms);
    if (root.querySelector("#fDir").dataset.desc === "1") q.set("desc", "true");
    if (showBanned()) q.set("include_banned", "true");
    if (root.querySelector("#fFreeOnly").checked) {
      q.set("free_range_only", "true");
    }
    const deckSel = root.querySelector("#fDeck");
    if (deckSel && deckSel.value) q.set("deck_id", deckSel.value);
    // 「まずはここから」の厳選語を先頭に固定するのは、未登録・未課金
    // (state.freeFirstSort)が「無料で聞ける順」・昇順で絞り込み・検索なしの
    // ときだけ(何か絞ったときに無関係な語が混ざらないように。課金者・
    // 管理者・テスターが手動でこの並びを選んだ場合も固定しない)。
    if (state.freeFirstSort && q.get("sort") === "billing"
        && !q.has("desc") && ![...q.keys()].some((k) => k !== "sort")) {
      q.set("featured_first", "true");
    }
    const words = await api.get("/api/words?" + q.toString());
    if (seq !== loadSeq) return; // 自分より新しい問い合わせが発行済み→破棄
    baseWords = words;
    applyKeyword();
  };
  const fDir = root.querySelector("#fDir");
  const rememberSort = () => saveSort("vocab_sort",
    root.querySelector("#fSort").value, fDir.dataset.desc === "1");
  fDir.addEventListener("click", () => {
    const d = fDir.dataset.desc === "1" ? "0" : "1";
    fDir.dataset.desc = d;
    fDir.textContent = d === "1" ? tx("filter.descending") : tx("filter.ascending");
    rememberSort();
    load();
  });
  root.querySelector("#fSort").addEventListener("change", rememberSort);
  ["#fLevelMin", "#fLevelMax", "#fOutRange", "#fFreeOnly", "#fSort",
   "#fMastered"].forEach((id) =>
    root.querySelector(id)?.addEventListener("change", load));
  root.querySelector("#fDeck")?.addEventListener("change", load);
  // 分野チェックボックス（複数選択可）。大分類を選ぶと候補が絞り込まれる
  // （大分類だけでもカテゴリ配下の全分野を検索対象にできる＝分野は
  // 「未選択」のままでよい）。
  const domainDropdown = initCheckDropdown(root, "fDomainBtn", "fDomainPanel",
    () => {
      const cat = root.querySelector("#fCategory").value;
      return cat ? { [cat]: domainGroups[cat] || [] } : domainGroups;
    }, selectedDomains, load, "list.colDomain");
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
  kw.addEventListener("input", applyKeyword);
  if (dfwActive) {
    if (dfw.category) root.querySelector("#fCategory").value = dfw.category;
    if (dfw.level_min) root.querySelector("#fLevelMin").value = dfw.level_min;
    if (dfw.level_max) root.querySelector("#fLevelMax").value = dfw.level_max;
    if (dfw.mastered) root.querySelector("#fMastered").value = dfw.mastered;
  }
  load();
}

// --- Phrases ----------------------------------------------------------------

export async function phrases(root) {
  const sb = bannedParam(showBanned());
  // 未登録・未課金は既定の並びを「無料で聞ける順」にする(2026-09-20・
  // 英単語一覧と同じ。判定はサーバー)。最初の一覧取得にも同じ並びを渡す。
  // 前回手動で選んだ並びがあれば既定より優先する(2026-09-20・保存は
  // loadSavedSort/saveSort参照)。最初の一覧取得にもその並びを渡す。
  const savedSort = loadSavedSort("phrase_sort", PHRASE_SORTS);
  const initSort = savedSort ? savedSort.sort
    : (state.freeFirstSort ? "billing" : "");
  // ショーケース・フレーズ(先頭に固定する1件)は、未登録・未課金の
  // 「無料で聞ける順・昇順」で絞り込みが無いときだけ(英単語の厳選語と同じ条件)。
  const pinFeatured = state.freeFirstSort && initSort === "billing"
    && !(savedSort && savedSort.desc) && !sb;
  const listQs = [sb, initSort ? "sort=" + initSort : "",
    savedSort && savedSort.desc ? "desc=true" : "",
    pinFeatured ? "featured_first=true" : ""]
    .filter(Boolean).join("&");
  // 5本とも互いに依存が無いため並列実行する(2026-09-07・以前は直列5回で
  // 表示までの待ち時間が積み上がっていた)。
  const [sceneData, pfacets, list, myDecks, usP] = await Promise.all([
    api.get("/api/phrases/scenes" + (sb ? "?" + sb : "")),
    api.get("/api/phrases/facets"),
    api.get("/api/phrases" + (listQs ? "?" + listQs : "")),
    api.get("/api/phrase-decks").catch(() => []),
    // ゲストは/api/system/user-settingsを読めない(要ログイン)ため、既定
    // フィルター無し(={})として扱う(2026-08-11・ゲスト実装で発見)。
    api.get("/api/system/user-settings")
      .catch(() => ({ settings: {} })).then((r) => r.settings || {}),
  ]);
  const sceneGroups = sceneData.scene_groups || {};
  const dfp = usP.default_phrase_filters || {};
  const dfpActive = !!(dfp.category || dfp.level_min || dfp.level_max
    || dfp.mastered);
  root.innerHTML = `
    <h1 id="pageTitle"><span id="pageTitleText">${tx("nav.phrases")} (${list.length})</span> ${infoIcon(
      "help-phrases", tx("phraseList.helpText"))}</h1>
    ${dfpActive ? `<p class="muted">⚙️ ${tx("filter.defaultFilterActive")}</p>` : ""}
    <div class="row">
      <select id="sceneCategory" title="${escapeHtml(tx("filter.categoryTitle"))}"><option value="">${tx("filter.allCategories")}</option>
        ${Object.keys(sceneGroups).map((c) =>
          `<option>${escapeHtml(c)}</option>`).join("")}</select>
      <span class="cdrop">
        <button type="button" class="btn ghost" id="fSceneBtn">${tx("filter.allDropdown")}</button>
        <div class="cdrop-panel" id="fScenePanel"></div>
      </span>
      ${state.isAdmin ? `<label class="toggle"
        title="${escapeHtml(tx("filter.showBannedTitle"))}">
        <input type="checkbox" id="showBanned"
        ${showBanned() ? "checked" : ""} />
        🔞 ${tx("filter.showBanned")}</label>` : ""}
    </div>
    <div class="card">
      <details class="log-group" id="phraseFilters"
        ${window.innerWidth <= 760 ? "" : "open"}>
      <summary>🔍 ${tx("filter.summary")} ${infoIcon("help-filter-phrases", PHRASE_FILTER_HELP)}</summary>
      <div class="row mt">
        <input id="kw" placeholder="${escapeHtml(tx("filter.searchPlaceholderPhrase"))}" style="width:140px" />
        <span class="muted">Lv</span>
        <select id="fLevelMin" title="${escapeHtml(tx("filter.levelMinTitle"))}"><option value="">${tx("filter.lowerBound")}</option>
          ${(pfacets.range_levels || []).map((l) =>
            `<option>${escapeHtml(l)}</option>`).join("")}</select>
        <span class="muted">〜</span>
        <select id="fLevelMax" title="${escapeHtml(tx("filter.levelMaxTitle"))}"><option value="">${tx("filter.upperBound")}</option>
          ${(pfacets.range_levels || []).map((l) =>
            `<option>${escapeHtml(l)}</option>`).join("")}</select>
        ${state.isAdmin ? `<label class="toggle"
          title="${escapeHtml(tx("filter.outOfRangeTitle"))}">
          <input type="checkbox" id="fOutRange" /> ${tx("filter.outOfRange")}</label>
          ${infoIcon("out-of-range-filter", tx("filter.outOfRangeHelpPhrase"))}` : ""}
        ${freeOnlyToggle("fFreeOnly", "phrase")}
        ${myDecks.length ? `<select id="fDeck" title="${escapeHtml(tx("filter.phraseDeckFilterTitle"))}">
          <option value="">${tx("filter.phraseDeckAll")}</option>
          ${myDecks.map((d) =>
            `<option value="${d.id}">🗂️ ${escapeHtml(d.name)}</option>`)
            .join("")}</select>` : ""}
        <select id="fSort">
          <option value="mastery">${tx("filter.sortMastery")}</option>
          <option value="accuracy">${tx("filter.sortAccuracy")}</option>
          <option value="english">${tx("filter.sortEnglish")}</option>
          <option value="scene">${tx("filter.sortScene")}</option>
          <option value="recent">${tx("filter.sortRecent")}</option>
          <option value="added">${tx("filter.sortAdded")}</option>
          <option value="billing">${tx("filter.sortBilling")}</option>
        </select>
        <button class="btn ghost" id="fDir"
          title="${escapeHtml(tx("filter.dirToggleTitle"))}">${tx("filter.ascending")}</button>
        <select id="fMastered" title="${escapeHtml(tx("filter.masteredPhraseFilterTitle"))}">
          <option value="">${tx("filter.masteredInclude")}</option>
          <option value="hide">${tx("filter.masteredHide")}</option>
          <option value="only">${tx("filter.masteredOnly")}</option>
        </select>
        ${infoIcon("mastery-legend", MASTERY_LEGEND_HINT)}
        ${speedSelect("pSpeed")}
        ${pageSizeSelect("pPage")}
      </div>
      </details>
      <table class="mt rtable"><thead><tr>
        <th>${tx("list.colPlay")}${infoIcon("voice-icon-legend", tx("list.voiceIconHelp"))}</th>
        <th>${tx("list.colEnglish")}</th><th>${tx("list.colJapanese")}</th><th>${tx("list.colDetail")}</th>
        <th>${tx("list.colScene")}</th><th>${tx("list.colMastery")}</th><th>${tx("list.colActions")}</th></tr></thead>
        <tbody id="rows"></tbody></table>
      <div id="pager" class="mt"></div>
    </div>`;

  if (initSort) root.querySelector("#fSort").value = initSort;
  if (savedSort && savedSort.desc) {
    const dirBtn = root.querySelector("#fDir");
    dirBtn.dataset.desc = "1";
    dirBtn.textContent = tx("filter.descending");
  }
  // 件数表示は専用spanだけを書き換える(英単語画面と同じ理由・2026-09-19)。
  const title = root.querySelector("#pageTitleText");
  const kw = root.querySelector("#kw");
  const pagerEl = root.querySelector("#pager");
  let curList = [];
  let pPage = 0;
  const selectedScenes = new Set();

  const paint = () => {
    const size = root.querySelector("#pPage").value;
    const { slice, page, pages } = pageSlice(curList, pPage, size);
    pPage = page;
    title.textContent = `${tx("nav.phrases")} (${curList.length})`;
    // このページの直前のフレーズ(ページ境目で見出しを出すため・英単語と同じ)。
    const start = size === "all" ? 0 : page * (parseInt(size, 10) || 20);
    renderRows(slice, start > 0 ? curList[start - 1] : null);
    pagerEl.innerHTML = "";
    pagerEl.appendChild(pagerBar(curList.length, page, pages,
      () => { pPage = page - 1; paint(); },
      () => { pPage = page + 1; paint(); }));
  };

  const renderRows = (items, before = null) => {
    const rows = root.querySelector("#rows"); rows.innerHTML = "";
    // 先頭に固定したショーケース・フレーズがあるときだけ見出し行を挟む
    // (キーワード検索中は絞り込み結果なので出さない)。
    const groups = !kw.value.trim()
      && (items.some((x) => x.featured) || !!(before && before.featured));
    let prevFeatured = before ? !!before.featured : null;
    items.forEach((p) => {
      if (groups) {
        if (p.featured && prevFeatured === null) {
          rows.appendChild(listGroupHead(7, PHRASE_FEATURED_HEAD()));
        } else if (!p.featured && prevFeatured === true) {
          rows.appendChild(listGroupHead(7,
            tx("list.otherPhrases")));
        }
      }
      prevFeatured = !!p.featured;
      const tr = el(`<tr${p.featured ? ' class="featured-row"' : ""}>
        <td></td>
        <td data-label="${escapeHtml(tx("list.colEnglish"))}">${escapeHtml(p.english)}</td>
        <td data-label="${escapeHtml(tx("list.colJapanese"))}">${escapeHtml(p.japanese)}</td>
        <td><div class="detail-cell"></div></td>
        <td data-label="${escapeHtml(tx("list.colScene"))}"><span class="pill">
          ${escapeHtml(p.scene || "")}</span></td>
        <td data-mc="1" data-label="${escapeHtml(tx("list.colMastery"))}">${masteryCell(p)}</td>
        <td><div class="ops-cell"></div></td>
      </tr>`);
      tr.firstElementChild.appendChild(voiceButtonsItem(
        "phrase", p.id, "phrase", () => p.english,
        () => root.querySelector("#pSpeed").value, p.is_free_range));
      const ops = tr.querySelector("td:last-child .ops-cell");
      const mc = tr.querySelector("[data-mc]");
      const det = el(`<button class="btn good">${tx("list.detail")}</button>`);
      det.addEventListener("click", () => showPhraseDetail(p));
      tr.querySelector(".detail-cell").appendChild(det);
      let onChange = () => {};
      const { btn: clearBtn, paint: paintClear } =
        clearButton("/api/phrases", p, () => onChange());
      onChange = () => { mc.innerHTML = masteryCell(p); paintClear(); };
      const vague = vagueButton("/api/phrases", p, onChange);
      const known = knownButton("/api/phrases", p, onChange);
      const perfect = perfectButton("/api/phrases", p, onChange);
      ops.append(vague, opsBreak(), known, perfect, clearBtn);
      rows.appendChild(tr);
    });
  };
  if (!dfpActive) { curList = list; pPage = 0; paint(); }

  // シーン・並び替え・禁止表示はサーバ側、キーワードはクライアント側。
  // vocab()と同じレースコンディション対策(連番ガード)。詳細はvocab()側の
  // コメント参照。
  let loadSeq = 0;
  let baseList = dfpActive ? [] : list; // 直近のサーバ取得結果のキャッシュ
  // キーワードはサーバのクエリパラメータに含まれずクライアント側でしか
  // 絞り込んでいないため、1文字入力するたびにload()で全件再取得すると
  // 無駄な重いリクエストが積み重なり、体感で「検索し直しても反映されない」
  // ように見える不具合になっていた(2026-09-02ユーザー報告・vocab()と同じ
  // 原因)。キーワード変更時はキャッシュ済みbaseListをその場でフィルタする
  // だけにし、サーバ再取得はキーワード以外のフィルタが変わったときだけ
  // 行う。
  const applyKeyword = () => {
    const term = kw.value.trim().toLowerCase();
    curList = term ? baseList.filter((p) =>
      p.english.toLowerCase().includes(term)
      || (p.japanese || "").toLowerCase().includes(term)) : baseList;
    pPage = 0;
    paint();
  };
  const load = async () => {
    const seq = ++loadSeq;
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
    if (root.querySelector("#fOutRange")?.checked) q.set("out_of_range", "true");
    const ms = root.querySelector("#fMastered").value;
    if (ms) q.set("mastered", ms);
    if (root.querySelector("#fDir").dataset.desc === "1") q.set("desc", "true");
    if (showBanned()) q.set("include_banned", "true");
    if (root.querySelector("#fFreeOnly").checked) {
      q.set("free_range_only", "true");
    }
    const deckSel = root.querySelector("#fDeck");
    if (deckSel && deckSel.value) q.set("deck_id", deckSel.value);
    // ショーケース・フレーズの先頭固定(英単語の厳選語と同じ条件)。
    if (state.freeFirstSort && q.get("sort") === "billing"
        && !q.has("desc") && ![...q.keys()].some((k) => k !== "sort")) {
      q.set("featured_first", "true");
    }
    const items = await api.get("/api/phrases?" + q.toString());
    if (seq !== loadSeq) return; // 自分より新しい問い合わせが発行済み→破棄
    baseList = items;
    applyKeyword();
  };
  const fDir = root.querySelector("#fDir");
  const rememberSort = () => saveSort("phrase_sort",
    root.querySelector("#fSort").value, fDir.dataset.desc === "1");
  fDir.addEventListener("click", () => {
    const d = fDir.dataset.desc === "1" ? "0" : "1";
    fDir.dataset.desc = d;
    fDir.textContent = d === "1" ? tx("filter.descending") : tx("filter.ascending");
    rememberSort();
    load();
  });
  // シーンチェックボックス（複数選択可）。大分類を選ぶと候補が絞り込まれる。
  const sceneDropdown = initCheckDropdown(root, "fSceneBtn", "fScenePanel",
    () => {
      const cat = root.querySelector("#sceneCategory").value;
      return cat ? { [cat]: sceneGroups[cat] || [] } : sceneGroups;
    }, selectedScenes, load, "list.colScene");
  root.querySelector("#sceneCategory").addEventListener("change", () => {
    selectedScenes.clear();
    sceneDropdown.renderPanel();
    sceneDropdown.refreshLabel();
    load();
  });
  root.querySelector("#fSort").addEventListener("change", rememberSort);
  root.querySelector("#fSort").addEventListener("change", load);
  root.querySelector("#fMastered").addEventListener("change", load);
  ["#fLevelMin", "#fLevelMax", "#fOutRange", "#fFreeOnly"].forEach((id) =>
    root.querySelector(id)?.addEventListener("change", load));
  root.querySelector("#fDeck")?.addEventListener("change", load);
  root.querySelector("#pPage").addEventListener("change", () => {
    pPage = 0; paint();
  });
  // 禁止表示の切替はシーン候補も変わるので画面を作り直す。
  const sbP = root.querySelector("#showBanned");
  if (sbP) sbP.addEventListener("change", (e) => {
    setShowBanned(e.target.checked); go("phrases");
  });
  kw.addEventListener("input", applyKeyword);
  if (dfpActive) {
    if (dfp.category) root.querySelector("#sceneCategory").value = dfp.category;
    if (dfp.level_min) root.querySelector("#fLevelMin").value = dfp.level_min;
    if (dfp.level_max) root.querySelector("#fLevelMax").value = dfp.level_max;
    if (dfp.mastered) root.querySelector("#fMastered").value = dfp.mastered;
    load();
  }
}

// --- Quiz (単語/フレーズ) -----------------------------------------------------
// 元は単語一覧・フレーズ一覧の画面内にボタンとして埋め込んでいたが、
// 一覧画面のスペースを圧迫するとの指摘(2026-08-23)を受け、独立したメニュー
// 項目に分離した。

export async function quiz(root) {
  const us = (await api.get("/api/system/user-settings")
    .catch(() => ({ settings: {} }))).settings || {};
  const hideMasteredDefault = !!us.hide_mastered;
  root.innerHTML = `
    <h1>クイズ ${infoIcon("help-quiz",
      "英単語またはフレーズから10問をランダムに出題します。同じ語を" +
      "「英→日」「日→英」の両方向で出題し、答えは文字入力か音声で" +
      "回答します(右上の「入力」で切替)。ログインすると結果が習熟度に" +
      "記録されます。")}</h1>
    <p class="sub">10問ランダム出題。英単語・フレーズどちらも両方向で出題します。</p>
    <div class="card">
      <div class="row">
        <b>🔤 英単語クイズ</b>
        <button class="btn" id="quizWord">クイズ開始 (10語)</button>
        ${infoIcon("quiz-grading", QUIZ_GRADING_HINT)}
      </div>
    </div>
    <div class="card">
      <div class="row">
        <b>💬 フレーズクイズ</b>
        <button class="btn" id="quizPhrase">クイズ開始 (10フレーズ)</button>
        ${infoIcon("quiz-grading", QUIZ_GRADING_HINT)}
      </div>
    </div>`;

  root.querySelector("#quizWord").addEventListener("click", async () => {
    const tb = testBanned() ? "&include_banned=true" : "";
    const mb = hideMasteredDefault ? "&mastered=hide" : "";
    const items = await api.get("/api/words/quiz?limit=10" + tb + mb);
    root.innerHTML = `<h1>単語クイズ</h1>`;
    const holder = el(`<div></div>`); root.appendChild(holder);
    quizRunner({ container: holder, items, kind: "word", appState: state,
      onDone: () => {
        const b = el(`<button class="btn mt">クイズに戻る</button>`);
        b.addEventListener("click", () => go("quiz")); holder.appendChild(b);
      } });
  });
  root.querySelector("#quizPhrase").addEventListener("click", async () => {
    const tb = testBanned() ? "&include_banned=true" : "";
    const mb = hideMasteredDefault ? "&mastered=hide" : "";
    const items = await api.get("/api/phrases/quiz?limit=10" + tb + mb);
    root.innerHTML = `<h1>フレーズクイズ</h1>`;
    const holder = el(`<div></div>`); root.appendChild(holder);
    quizRunner({ container: holder, items, kind: "phrase", appState: state,
      onDone: () => {
        const b = el(`<button class="btn mt">クイズに戻る</button>`);
        b.addEventListener("click", () => go("quiz")); holder.appendChild(b);
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

// help: [hintId, 説明文] を渡すと見出しにⓘヘルプを付ける(任意)。
function materialView(title, sub, area, fields, histAreas, help) {
  return async function (root) {
    root.innerHTML = `
      <h1>${title}${help ? " " + infoIcon(help[0], help[1]) : ""}</h1>
      ${sampleGateBanner()}
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
          ${infoIcon("comprehension-questions", COMPREHENSION_Q_HINT)}
          <input id="inst" placeholder="追加指示(任意)" style="width:160px" />
          <button class="btn" id="gen"
            ${(state.aiEnabled && !aiGateDisabled()) ? "" : "disabled"}>${
            aiGateLabel("生成")}</button>
          <button class="btn ghost" id="histBtn"
            ${state.isGuest ? "disabled" : ""}>${
            state.isGuest ? "🔒 履歴(要ログイン)" : "📚 履歴"}</button>
        </div>
      </div>
      <div id="histPanel" class="card" style="display:none"></div>
      <div class="card"><div id="out" class="md">
        左上で分野を選んで「生成」を押してください。</div></div>`;
    placeSampleCard(root, sampleMaterialsCard(area,
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
      try {
        const r = await api.post("/api/learn/generate", {
          area: genArea, field,
          difficulty: root.querySelector("#fdiff").value,
          instruction: (len ? `本文は${len}作成。` : "")
            + root.querySelector("#inst").value,
        });
        if (!r.ok) { out.textContent = r.error; return; }
        showInto(r.body);   // disp() で問題トグルを反映
        refreshCost();
      } catch (e) { out.textContent = "生成にはログインが必要です。" +
        "（" + e.message + "）"; }
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
  ], "reading,literature,news", [
    "help-reading",
    "分野・難易度・長さを選ぶと、AIが英語の長文と内容理解問題を作ります。"
    + "文学やニュースも選べます。サンプルは無料で見られますが、生成には"
    + "ログインとAI利用の残高が必要です。「履歴」から過去に作った教材を"
    + "無料で再表示でき、「覚えた」「うろ覚え」で習熟度も付けられます。",
  ])(root);

// --- Writing ----------------------------------------------------------------

// あらかじめ用意した「サンプル」教材(is_public_sample=1)だけを一覧表示
// する共通カード。AI課金は発生しない（既存の保存済み教材を表示するのみ）。
// クリックでカード内に直接表示(2026-08-13・従来はポップアップ表示
// だったが「課金ユーザーと同様に画面下に出したい」という指摘で変更)＋
// 🔊読み上げボタン付き。無課金/未ログインでも「どんな機能か」を確認
// できる（2026-08-12: 個人の生成履歴が混ざらないよう、専用の読み取り
// 専用API `/api/learn/samples` を使う。ログイン有無を問わず同じ結果）。
function sampleMaterialsCard(area, cardTitle, emptyLabel) {
  const card = el(`<div class="card" id="sampleCard-${escapeHtml(area)}">
    <h2>${escapeHtml(cardTitle)}</h2>
    <p class="muted">実際にAIを使わなくても内容を確認できるサンプルです。
      無課金でもご覧いただけます。</p>
    <div class="row" id="smList"><p class="muted">読み込み中…</p></div>
    <div id="smBody" class="md mt"></div>
  </div>`);
  (async () => {
    const list = card.querySelector("#smList");
    const bodyBox = card.querySelector("#smBody");
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
        bodyBox.innerHTML = "";
        bodyBox.appendChild(sampleReadAloudBar(m));
        const b = el(`<div class="md mt"></div>`);
        b.innerHTML = md(m.body);
        bodyBox.appendChild(b);
        bodyBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
      });
      list.appendChild(btn);
    });
  })();
  return card;
}

export async function writing(root) {
  root.innerHTML = `
    <h1>ライティング ${infoIcon("help-writing",
      "お題に対して英文を書き、AIが添削・フィードバックします。ゲスト" +
      "でもサンプル教材は試せますが、AIによる自由な添削にはログインと" +
      "AI利用の残高が必要です。")}</h1>
    ${sampleGateBanner()}
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
  placeSampleCard(root, sampleMaterialsCard("writing_sample",
    "📝 添削サンプルを見る", "サンプルがまだありません。"));
  const ansBox = root.querySelector("#ans");
  ansBox.appendChild(answerInput(async (txt) => {
    if (!txt.trim()) { toast("文章が空です"); return; }
    const fb = root.querySelector("#fb");
    if (!state.aiEnabled) { fb.textContent = "AI未設定です。"; return; }
    fb.textContent = "添削中…";
    try {
      const r = await api.post("/api/learn/writing-feedback", {
        category: root.querySelector("#cat").value,
        prompt: root.querySelector("#prompt").value,
        text: txt,
      });
      fb.innerHTML = r.ok ? md(r.feedback) : escapeHtml(r.error);
      if (r.ok) { const s = el(`<button class="btn ghost mt">🔊 読み上げ</button>`);
        s.addEventListener("click", () => speech.speak(r.feedback)); fb.appendChild(s); }
      refreshCost();
    } catch (e) { fb.textContent = "添削にはログインが必要です。" +
      "（" + e.message + "）"; }
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
    <h1>英会話 ${infoIcon("help-conversation",
      "AIと英語で会話練習ができます。シーン・レベルを選んでやり取りし、" +
      "終了後にフィードバックを受け取れます。AIとの会話にはログインと" +
      "AI利用の残高が必要です。")}</h1>
    ${sampleGateBanner()}
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
        ${infoIcon("conv-handsfree",
          "ボタンを押さずに話しかけるだけで会話が進むモードです。声の切れ目"
          + "(無音)を音量で判定して、AIが自動で応答します。使い終わったら"
          + "「終了」を押してください(つけっぱなしは利用料がかかり続けます。"
          + "無音や最大時間での自動終了はあくまで保険です)。")}
        <button class="btn good" id="hfStart"
          ${aiGateDisabled() ? "disabled" : ""}>${
          aiGateDisabled() ? aiGateLabel("開始") : "▶ 開始"}</button>
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
        <span class="muted">・声の切れ目を音量で判定します。</span>
      </div>
      <div class="row mt">
        <label>無音で自動終了(分):
          <input id="hfNoSpeechMin" type="number" value="2" step="0.5" min="0.5"
            style="width:64px" /></label>
        <label>最大会話時間(分):
          <input id="hfMaxMin" type="number" value="15" step="1" min="1"
            style="width:64px" /></label>
        <span class="muted">・話しかけないまま一定時間経つと自動終了します。
          発話中でも最大時間で自動終了し、つけっぱなしによる課金を防ぎます。</span>
      </div>
      <p class="muted mt">⚠️ 使い終わったら「⏹ 終了」を押すことをおすすめします
        （自動終了はあくまで保険です。つけっぱなしは利用料がかかり続ける
        原因になります）。</p>
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
        <label class="toggle"><input type="checkbox" id="speakSpeaker" />
          話者名を読み上げる（AI）</label>
        <label class="toggle"><input type="checkbox" id="fastMode" />
          ⚡ 応答を高速化（試験運用）</label>
        ${infoIcon("conv-fast-mode",
          "ONにすると、会話専用の応答が速いモデルを使います。試験運用のため、"
          + "返答の内容が通常と少し変わる場合があります。OFFなら通常の"
          + "モデルのままです。")}
        <button class="btn secondary" id="start"
          ${aiGateDisabled() ? "disabled" : ""}>${
          aiGateLabel("AIから始める")}</button>
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
  placeSampleCard(root, sampleMaterialsCard("conversation_sample",
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
  // 話者名(AI)を読み上げに含めるか（選択制・既定OFF・2026-08-27要望）。
  // AIの発話のみが読み上げ対象なので、話者は常に"AI"固定でよい。
  const withSpeaker = (t) =>
    root.querySelector("#speakSpeaker").checked ? "AI. " + t : t;
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
      say.addEventListener("click", () => speech.speak(
        withSpeaker(enText(body.textContent) || body.textContent)));
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

  // エラー時の表示を共通化(2026-09-18・Fableレビュー指摘への対応)。
  // addMsg("ai", ...)が付ける🌐翻訳/🔊読み上げ/添削例ボタンをそのまま
  // 残すと、エラー文を有料の翻訳APIへ送ったり音声で読み上げたりできて
  // しまう(自動では止めたが、手動クリックの経路が残っていた)ため、
  // エラー表示ではツール行ごと取り除く。
  function showTurnError(target, message) {
    target.textContent = "⚠️ " + message;
    const bubble = target.parentElement;
    const tools = bubble && bubble.querySelector(".row");
    if (tools) tools.remove();
  }

  // 1往復ぶんのAI応答を取得して吹き出し(target)へ流し込む(2026-09-19・案B)。
  // split=true(シーン会話/出張ロールプレイで学習者の発話がある時)は、
  // 「返答」と「アドバイス(【コーチ】+【例】)」を別リクエストで**並行**に
  // 取得し、返答が終わった時点でresolveする(=呼び出し元は先に読み上げ・
  // 履歴保存へ進める)。アドバイスは遅れて同じ吹き出しの下に追記され、
  // 失敗しても返答には影響しない。split=falseは従来どおり1本(自由会話・
  // 会話開始)。課金(1往復1回)・レート制限の扱いはサーバー側
  // (learn.py conversation_stream・ai._BUNDLED_FEATURES)を参照。
  // 戻り値: { reply, historyText(履歴に積む本文=返答のみ), coachDone(Promise) }
  async function streamTurn(body, target, { split }) {
    const url = "/api/learn/conversation/stream";
    let reply = "";
    let coach = "";
    let dead = false;   // 返答が失敗した後は吹き出しを書き換えない
    const paint = () => {
      if (dead) return;
      const c = coach && !coach.includes("【コーチ")
        ? "【コーチ】" + coach : coach;
      target.textContent = c ? `${reply}\n\n${c}` : reply;
      chat.scrollTop = chat.scrollHeight;
    };
    if (!split) {
      try {
        await api.stream(url, body, (chunk) => { reply += chunk; paint(); });
      } catch (e) { dead = true; throw e; }
      return { reply, historyText: reply, coachDone: Promise.resolve() };
    }
    const ctl = new AbortController();
    let coachDone = Promise.resolve();
    let coachStarted = false;
    // アドバイスは返答の最初のチャンクが届いてから開始する: サーバーは返答の
    // 事前チェック通過時にアドバイス1回分の権利を発行するため、この順序に
    // すると権利が必ず先に存在する。返答が事前チェックで拒否された/失敗した
    // ターンでは、アドバイスは最初から始まらない(無駄なAI呼び出しが無い)。
    // それでも返答の生成と重なって並行実行される(返答の完了を待たない)。
    const startCoach = () => {
      if (coachStarted) return;
      coachStarted = true;
      coachDone = api.stream(url, { ...body, part: "coach" },
        (chunk) => { coach += chunk; paint(); }, { signal: ctl.signal })
        .catch((e) => {
          if (dead || (e && e.name === "AbortError")) return;
          coach = "";   // 途中まで出ていたアドバイスは消し、失敗を静かに知らせる
          paint();
          const bubble = target.parentElement;
          if (bubble) {
            bubble.insertBefore(el(`<div class="muted coach-note"
              style="font-size:12px">アドバイスを取得できませんでした</div>`),
            bubble.querySelector(".row"));
          }
        });
    };
    try {
      await api.stream(url, { ...body, part: "reply" },
        (chunk) => { reply += chunk; paint(); startCoach(); });
    } catch (e) {
      dead = true;
      ctl.abort();    // 返答が途中で失敗したターンのアドバイスは不要
      throw e;
    }
    // 返答にコーチ部分が混ざってしまった場合に備え、履歴には返答部分だけ積む
    // (次のターンのAIに、コーチ付きの形式を真似させないため)。
    const historyText = reply.split("【コーチ")[0].trim() || reply;
    return { reply, historyText, coachDone };
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
      fast: root.querySelector("#fastMode").checked,
    };
    const target = addMsg("ai", kickoff ? "…" : "");
    let full = "";
    let turn = null;
    if (state.aiEnabled) {
      target.textContent = "";
      try {
        turn = await streamTurn(body, target, {
          split: !kickoff && s.grp !== "自由会話",
        });
        full = turn.reply;
      } catch (e) {
        // 2026-09-18修正: 従来はここでエラーを検知しておらず、エラー
        // 応答の本文がそのままAIの発言として表示され、会話履歴に積まれ
        // AIへ送信・自動保存・(設定次第で)読み上げまでされてしまう
        // 実害のあるバグだった(Fableレビューで発見)。エラー時は履歴に
        // 積まず、保存も読み上げもしない。
        showTurnError(target,
          e.message || "エラーが発生しました。もう一度お試しください。");
        // 積んだユーザー発言が(返答の無いまま)次回送信時のAIへの文脈に
        // 残り続けないよう戻す(kickoffは元々ユーザー発言を積んでいない)。
        if (!kickoff) history.pop();
        refreshCost();
        return;
      }
      if (!full.trim()) {
        // 生成が0文字で終わった場合(途中で切れた等)も、無言のAI発言を
        // 履歴に積まないようエラー扱いにする。
        showTurnError(target, "応答が空でした。もう一度お試しください。");
        if (!kickoff) history.pop();
        refreshCost();
        return;
      }
    } else {
      full = "（AI未設定）設定でAPIキーを登録すると会話できます。";
      target.textContent = full;
    }
    history.push({
      role: "assistant", content: turn ? turn.historyText : full,
    });
    if (root.querySelector("#autoTts").checked && state.aiEnabled) {
      // 【コーチ】以降と日本語は読み上げない（英語部分のみ）。
      speech.speak(withSpeaker(englishOnly(full.split("【コーチ")[0])));
    }
    refreshCost();
    // アドバイス(並行取得)が後から終わった分の費用表示も更新する。
    if (turn) turn.coachDone.then(() => refreshCost());
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
    const dk = el(state.isGuest
      ? `<button class="btn ghost" disabled>🔒 わからない</button>`
      : `<button class="btn ghost">🤔 わからない</button>`);
    const ex = el(state.isGuest
      ? `<button class="btn ghost" disabled>🔒 返答例</button>`
      : `<button class="btn ghost">💡 返答例</button>`);
    const sendBtn = el(state.isGuest
      ? `<button class="btn" disabled>🔒 送信(要ログイン)</button>`
      : `<button class="btn">✓ 送信</button>`);
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
        } catch (e) { alert(micErrorMessage(e)); }
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
    let turn = null;
    try {
      // sendと同じく、返答とアドバイスを並行取得し返答だけを先に読み上げる。
      turn = await streamTurn({
        grp: s.grp, topic: s.topic, history, persona: s.persona || "",
        message: text, fast: root.querySelector("#fastMode").checked,
      }, target, { split: s.grp !== "自由会話" });
      full = turn.reply;
    } catch (e) {
      // sendと同じ理由(2026-09-18修正)。従来はここでのエラーがそのまま
      // 「AIの発言」として画面表示・履歴保存され、さらに音声で読み上げ
      // までされていた(ハンズフリー機能のため実害が一番大きい経路)。
      showTurnError(target,
        e.message || "エラーが発生しました。もう一度お試しください。");
      history.pop();
      refreshCost();
      // ハンズフリー中は画面を見ていない前提の機能のため、テキスト表示
      // だけでは失敗に気づけない(Fableレビュー指摘)。固定の短い案内文
      // だけを読み上げる(エラーの生文言は読み上げない＝内部情報の
      // 音声経由の漏洩も防ぐ)。forceBrowser: エラー直後にまた有料AI音声
      // (/api/learn/tts)へ二重に頼らない(Fable2回目レビュー指摘)。
      await speech.speakAndWait("エラーが発生しました。もう一度お試しください。",
        { forceBrowser: true, lang: "ja-JP" });
      return;
    }
    if (!full.trim()) {
      showTurnError(target, "応答が空でした。もう一度お試しください。");
      history.pop();
      refreshCost();
      await speech.speakAndWait("応答が空でした。もう一度お試しください。",
        { forceBrowser: true, lang: "ja-JP" });
      return;
    }
    history.push({ role: "assistant", content: turn.historyText });
    refreshCost();
    turn.coachDone.then(() => refreshCost());
    scheduleAutoSave();
    await speech.speakAndWait(withSpeaker(englishOnly(full.split("【コーチ")[0])));
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
    const noSpeechMin = Math.max(0.5,
      parseFloat(root.querySelector("#hfNoSpeechMin").value) || 2);
    const maxMin = Math.max(1,
      parseFloat(root.querySelector("#hfMaxMin").value) || 15);
    const manual = root.querySelector("#hfManual").checked;
    try {
      hf = await speech.createVADSession({
        baseSilenceMs: sil, noSpeechEndMs: noSpeechMin * 60000,
        maxSessionMs: maxMin * 60000, manual,
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
          setHfStatus(`${noSpeechMin}分無音のため自動終了しました`); stopHF();
        },
        onMaxDuration: () => {
          setHfStatus(`最大会話時間(${maxMin}分)に達したため自動終了しました`);
          stopHF();
        },
      });
      await hf.start();
      hfStart.style.display = "none"; hfStop.style.display = "";
      hfEnd.style.display = manual ? "" : "none";
      setHfStatus("🎤 どうぞ話してください");
    } catch (e) { alert(micErrorMessage(e)); }
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
    <h1>リスニング ${infoIcon("help-listening",
      "AIがスクリプトを生成して読み上げ、聞き取れたかを記録します。" +
      "題材ジャンル・話者アクセント・速度を選べます。「聞き流し」は" +
      "英文/日本語訳を隠して繰り返し再生するモードです。")}</h1>
    ${sampleGateBanner()}
    <p class="sub">スクリプトを生成して読み上げ、理解度を記録します。</p>
    ${aiBadgeNote()}
    <div class="card">
      <div class="row">
        <select id="topic">${topics.map((t) =>
          // 未学習(理解度0)は毎回全選択肢に並んで意味を成さない見た目に
          // なっていたため、記録済み(1以上)のときだけ表示する
          // (2026-09-05ユーザー指摘「理解度0はいらないのでは・
          // なんだかわからない」)。
          `<option value="${t.id}">${t.source} / ${t.accent}${
            t.comprehension ? ` (理解度${t.comprehension})` : ""}</option>`
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
        ${infoIcon("comprehension-questions", COMPREHENSION_Q_HINT)}
        <button class="btn" id="gen"
          ${(state.aiEnabled && !aiGateDisabled()) ? "" : "disabled"}>${
          aiGateLabel("スクリプト生成")}
          </button>
        <button class="btn ghost" id="histBtn"
          ${state.isGuest ? "disabled" : ""}>${
          state.isGuest ? "🔒 履歴(要ログイン)" : "📚 履歴"}</button>
      </div>
      <div class="row mt" style="border-top:1px solid var(--panel-2);
        padding-top:8px">
        <b>🎧 聞き流し</b>
        ${infoIcon("listening-passive",
          "スクリプトを1文ずつ連続で読み上げるモードです(スクリプトが未生成の"
          + "ときは、約2分ぶんを自動で生成します)。英文・日本語訳の表示は"
          + "切り替えられ、「繰り返し」で最初から何度も再生します。画面を"
          + "離れると止まります。")}
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
        ${infoIcon("listening-comprehension",
          "聞き取れた度合いを0〜100で自己評価して「記録」します。苦手だった"
          + "点も一緒に残せます。記録すると、上の題材の選択肢に"
          + "「(理解度○○)」と表示されます。")}
        <input id="weak" placeholder="苦手だった点" style="width:240px" />
        <button class="btn good" id="save">記録</button>
      </div>
    </div>`;
  placeSampleCard(root, sampleMaterialsCard("listening",
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
    try {
      const r = await api.post("/api/learn/generate", body);
      if (!r.ok) { out.textContent = r.error; return; }
      scriptText = r.body; out.innerHTML = md(lDisp(r.body));
      const play = el(`<button class="btn mt">🔊 再生</button>`);
      play.addEventListener("click", () => lSpeak(scriptText));
      out.appendChild(play);
      refreshCost();
    } catch (e) { out.textContent = "生成にはログインが必要です。" +
      "（" + e.message + "）"; }
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
    const card = el(`<div class="card"><h3>💬 想定会話</h3>
      <label class="toggle"><input type="checkbox" id="scSpeaker" />
        話者名を読み上げる</label></div>`);
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
    // 話者名アナウンス: 選択制・既定OFF(2026-08-30ユーザー承認)。
    // このバーは/api/learn/ttsでその場合成する読み上げなので事前生成音声
    // の在庫は不要(チェック有無でgetText()に渡す文字列が変わるだけ)。
    const scSpeaker = card.querySelector("#scSpeaker");
    card.appendChild(readAloudBar(
      () => data.sample_conversation.map((t) =>
        (scSpeaker.checked && t.speaker ? `${t.speaker}. ` : "")
        + (t.en || "")).join(" ")));
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
    <h1>判定・教材作成 ${infoIcon("help-assess",
      "実力の判定と、苦手に合わせた教材の追加をまとめた画面です。" +
      "「レベル判定」はこれまでの学習データをもとにAIが実力を分析し、" +
      "「追加教材を作成」はAIが単語/フレーズを生成して追加します。" +
      "どちらもAIを使うため、AI利用の残高(pt)が必要です。")}</h1>
    <p class="sub">好きなタイミングで実力を判定し、苦手に合わせて教材を追加できます。</p>

    <div class="card">
      <h2>🎯 レベル判定 ${infoIcon("assess-level",
        "判定結果は「判定をmemoryに保存」を押すと、学習履歴画面の" +
        "「学習プロフィール」に残せます。保存した内容は、以後AIが会話や" +
        "教材作成で参考にします。")}</h2>
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
      <h2>📚 追加教材を作成 ${infoIcon("assess-generate",
        "テーマ・苦手分野(任意)を入れると、それに沿った単語/フレーズを" +
        "AIが作ります。件数は10/20/30から選べ、すでに登録済みのものは" +
        "自動でスキップします。高品質モデルで生成します。")}</h2>
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
  // 互いに依存が無いため並列実行する(2026-09-07)。
  const [log, mem] = await Promise.all([
    api.get("/api/system/study-log"),
    api.get("/api/system/memory"),
  ]);
  root.innerHTML = `
    <h1>学習履歴 ${infoIcon("help-history",
      "学習の記録を残す・見返す画面です。①「セッション終了→記録」に" +
      "今日の学習内容や苦手を書いて保存します(AIに要約も頼めます)。" +
      "②「学習プロフィール」に方針・目標・苦手を書くと、AIが会話や" +
      "教材作成で参考にします。③「学習ログ」には学習内容が自動で" +
      "記録されます。")}</h1>
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

  root.querySelector("#summary").addEventListener("click", async (ev) => {
    const btn = ev.currentTarget;
    const out = root.querySelector("#sumOut");
    // 2026-08-29修正: 失敗時に「要約中…」のまま固まって見えるバグを修正
    // (実機ログで、この直後にユーザーが離脱していた形跡があった)。
    // ボタンを連打できないようにし、失敗時も必ずメッセージを出す。
    btn.disabled = true;
    out.textContent = "要約中…";
    try {
      const r = await api.post("/api/learn/session/summary", payload());
      out.innerHTML = r.ok ? md(r.summary) : escapeHtml(r.error);
      refreshCost();
    } catch (e) {
      out.textContent = e.message || "要約に失敗しました。時間をおいて再度お試しください。";
    } finally {
      btn.disabled = false;
    }
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
// ---------------------------------------------------------------------------
// バージョン情報（2026-08-22ユーザー要望）
//
// 最新バージョンと修正内容を先頭に出し、それ以前は「更新履歴」を開くと
// 見えるようにする。一般ユーザーには当たり障りのない内容(public)だけ、
// 管理者にはそれに加えて細かい内容(admin)も出す。管理者の画面では、
// 一般ユーザーにも見えている行を**赤文字**、管理者だけに見える行を
// 通常の文字色で表示して区別する（ユーザー指定）。
//
// 掲載データはサーバーの release_notes.json（data/ に置けば再起動なしで
// 差し替え可能）。
// ---------------------------------------------------------------------------

function releaseEntryHtml(v, isAdmin, showHeading) {
  const pub = (v.public || []).map((t) =>
    `<li class="rel-public">${escapeHtml(t)}</li>`).join("");
  const adm = isAdmin
    ? (v.admin || []).map((t) =>
      `<li class="rel-admin">${escapeHtml(t)}</li>`).join("")
    : "";
  const heading = showHeading
    ? `<h3 style="margin:0 0 2px">${escapeHtml(v.version)}
        <span class="muted" style="font-weight:normal">
          ${escapeHtml(v.date || "")}</span></h3>` : "";
  return `<div class="rel-entry">
    ${heading}
    ${v.title ? `<p class="muted" style="margin:0 0 4px">${
      escapeHtml(v.title)}</p>` : ""}
    ${pub ? `<ul>${pub}</ul>` : ""}
    ${adm ? `<p class="muted" style="margin:6px 0 0">管理者向けの詳細</p>
      <ul>${adm}</ul>` : ""}
  </div>`;
}

export async function release(root) {
  root.innerHTML = `<h1>バージョン情報 ${infoIcon("help-release",
      "アプリの更新内容とメンテナンス予定のお知らせを確認できます。" +
      "最新版が先頭に表示され、過去の分は「更新履歴」から見られます。")}</h1>
    <p class="sub">更新内容とメンテナンス予定のお知らせ。</p>
    <div id="relBody"><p class="muted">読み込み中…</p></div>`;
  const body = root.querySelector("#relBody");
  let res;
  try {
    res = await api.get("/api/system/release-notes");
  } catch (e) {
    body.innerHTML = `<p class="muted">取得できませんでした: ${
      escapeHtml(e.message)}</p>`;
    return;
  }
  const list = res.versions || [];
  const latest = list[0];
  const rest = list.slice(1);
  const isAdmin = !!res.is_admin;

  let html = "";
  // --- メンテナンス予定 ---
  html += `<div class="card" id="relMaint">
    <h2>🗓️ メンテナンス予定</h2>
    <p class="muted">読み込み中…</p></div>`;
  // --- 最新バージョン ---
  html += `<div class="card">
    <h2>最新バージョン <span class="muted">${
      escapeHtml(res.current || "")}</span></h2>
    ${latest
      ? `<p class="muted" style="margin:0 0 8px">${escapeHtml(latest.version)}
          ・${escapeHtml(latest.date || "")}</p>`
        + releaseEntryHtml(latest, isAdmin, false)
      : `<p class="muted">情報がありません。</p>`}
    ${isAdmin
      ? `<p class="muted" style="font-size:.9em">
          <span class="rel-public">赤文字</span>＝一般ユーザーにも表示される
          内容 ／ 通常色＝管理者にだけ表示される詳細。</p>` : ""}
  </div>`;
  // --- 履歴 ---
  if (rest.length) {
    html += `<div class="card"><details>
      <summary>これまでの更新履歴（${rest.length}件）</summary>
      <div class="mt">${rest.map((v) =>
        releaseEntryHtml(v, isAdmin, true)).join("")}</div>
    </details></div>`;
  }
  body.innerHTML = html;

  // メンテナンス予定は別APIから（管理者はその場で編集できる）。
  const mbox = body.querySelector("#relMaint");
  try {
    const m = await api.get("/api/system/maintenance");
    const WD = ["月", "火", "水", "木", "金", "土", "日"];
    const notice = (m.notice && m.notice.show)
      ? `<p><strong>${escapeHtml(m.notice.text)}</strong></p>` : "";
    const regular = m.regular_enabled
      ? `毎週${WD[m.regular_weekday] || "月"}曜 ${
        escapeHtml(m.regular_start)}〜${escapeHtml(m.regular_end)}（日本時間）`
      : "設定なし";
    const adhoc = (m.adhoc_enabled && m.adhoc_start)
      ? `${escapeHtml(m.adhoc_start)}〜${escapeHtml(m.adhoc_end || "")}`
        + (m.adhoc_note ? `（${escapeHtml(m.adhoc_note)}）` : "")
      : "予定なし";
    mbox.innerHTML = `<h2>🗓️ メンテナンス予定</h2>
      ${notice}
      <p>定期メンテナンス: <strong>${regular}</strong><br>
      臨時メンテナンス: <strong>${adhoc}</strong></p>
      <p class="muted" style="font-size:.9em">
        メンテナンス中は数分程度つながりにくくなることがあります。
        （現在の日本時間 ${escapeHtml(m.now_jst || "")}）</p>
      ${isAdmin ? maintenanceEditorHtml(m) : ""}`;
    if (isAdmin) wireMaintenanceEditor(mbox);
  } catch (e) {
    mbox.innerHTML = `<h2>🗓️ メンテナンス予定</h2>
      <p class="muted">取得できませんでした。</p>`;
  }
}

// 管理者用のメンテナンス予定エディタ。保存はDBに書くだけなので
// **アプリの再起動なしで**利用者側に反映される（2026-08-22の要件）。
function maintenanceEditorHtml(m) {
  const WD = ["月", "火", "水", "木", "金", "土", "日"];
  return `<details class="mt"><summary>✏️ 予定を変更する（管理者）</summary>
    <div class="mt">
      <p class="muted">保存するとすぐ反映されます（再起動不要）。</p>
      <div class="row">
        <label><input type="checkbox" id="mRegOn"
          ${m.regular_enabled ? "checked" : ""}> 定期メンテナンスを行う</label>
        <label>曜日:
          <select id="mRegWd">${WD.map((w, i) =>
    `<option value="${i}" ${i === m.regular_weekday ? "selected" : ""}>${
      w}曜</option>`).join("")}</select></label>
        <label>開始: <input id="mRegStart" type="time"
          value="${escapeHtml(m.regular_start || "03:00")}"></label>
        <label>終了: <input id="mRegEnd" type="time"
          value="${escapeHtml(m.regular_end || "03:30")}"></label>
      </div>
      <div class="row mt">
        <input id="mRegNote" style="flex:1" placeholder="定期メンテナンスの補足"
          value="${escapeHtml(m.regular_note || "")}">
      </div>
      <div class="row mt">
        <label><input type="checkbox" id="mAdOn"
          ${m.adhoc_enabled ? "checked" : ""}> 臨時メンテナンスの予定あり</label>
        <label>開始: <input id="mAdStart" type="datetime-local"
          value="${escapeHtml((m.adhoc_start || "").replace(" ", "T"))}"></label>
        <label>終了: <input id="mAdEnd" type="datetime-local"
          value="${escapeHtml((m.adhoc_end || "").replace(" ", "T"))}"></label>
      </div>
      <div class="row mt">
        <input id="mAdNote" style="flex:1" placeholder="臨時メンテナンスの理由・補足"
          value="${escapeHtml(m.adhoc_note || "")}">
      </div>
      <div class="row mt">
        <label title="VPS側のcron(deploy/scheduled_deploy.sh)が予約時刻に
docker compose up -d --build を実行します。コードは事前に同期しておくこと。"
          ><input type="checkbox" id="mAdDeploy"
          ${m.adhoc_auto_deploy ? "checked" : ""}>
          この時刻に自動デプロイする（要: 事前のコード同期）</label>
      </div>
      <p class="muted" style="font-size:.9em;margin:2px 0 0">
        ${m.deploy && m.deploy.scheduled
          ? `予約中: ${escapeHtml(m.deploy.scheduled.run_at || "")}` : "予約なし"}
        ${m.deploy && m.deploy.last
          ? ` ／ 前回の実行: ${escapeHtml(m.deploy.last.status || "")}
              （${escapeHtml(m.deploy.last.at || "")} UTC
              ${escapeHtml(m.deploy.last.message || "")}）` : ""}
      </p>
      <div class="row mt">
        <label>お知らせを出す時間:
          <input id="mLead" type="number" min="0" max="336" style="width:80px"
            value="${Number(m.notice_hours_before || 24)}"> 時間前から</label>
        <button class="btn" id="mSave">保存</button>
        <span id="mSaved" class="muted"></span>
      </div>
    </div></details>`;
}

function wireMaintenanceEditor(box) {
  const q = (id) => box.querySelector(id);
  q("#mSave").addEventListener("click", async () => {
    const payload = {
      regular_enabled: q("#mRegOn").checked,
      regular_weekday: Number(q("#mRegWd").value),
      regular_start: q("#mRegStart").value,
      regular_end: q("#mRegEnd").value,
      regular_note: q("#mRegNote").value,
      adhoc_enabled: q("#mAdOn").checked,
      adhoc_start: q("#mAdStart").value.replace("T", " "),
      adhoc_end: q("#mAdEnd").value.replace("T", " "),
      adhoc_note: q("#mAdNote").value,
      adhoc_auto_deploy: q("#mAdDeploy").checked,
      notice_hours_before: Number(q("#mLead").value),
    };
    q("#mSaved").textContent = "保存中…";
    try {
      await api.put("/api/system/maintenance", payload);
      q("#mSaved").textContent = "保存しました（すぐ反映されます）";
      // 画面上部のバナーも即座に更新する。
      refreshMaintenanceBanner();
    } catch (e) {
      q("#mSaved").textContent = "保存できませんでした: " + e.message;
    }
  });
}


export async function admin(root) {
  // 3本とも互いに依存が無いため並列実行する(2026-09-07・以前は直列
  // 3回だった)。dの失敗だけは権限エラー画面に切り替える特別扱いが
  // 必要なため、Promise.allSettledで個別に結果を見る。
  const [dRes, inquiriesRes, ordersRes, alertsRes] = await Promise.allSettled([
    api.get(`/api/system/admin/overview?${adminAggQuery()}`),
    api.get("/api/inquiries"),
    // 購入キー発行待ち(BASE注文)の件数。フルフィルメント画面に行かなくても
    // 管理者情報画面の更新だけで気づけるようにする(2026-08-19ユーザー要望)。
    api.get("/api/fulfillment/orders?status=pending"),
    // 前回確認以降の新規登録・エラーログ件数(2026-09-16ユーザー要望
    // 「登録者が増えた/エラーがあった場合わかりやすく警告、確認ボタンを
    // 押すまで出続けてほしい」)。
    api.get("/api/system/admin/alerts"),
  ]);
  if (dRes.status === "rejected") {
    root.innerHTML = `<h1>管理者情報</h1>
      <p class="muted">管理者のみ閲覧できます
        （${escapeHtml(dRes.reason.message)}）。</p>`;
    return;
  }
  const d = dRes.value;
  const inquiries = inquiriesRes.status === "fulfilled"
    ? (inquiriesRes.value.inquiries || []) : [];
  const pendingOrders = ordersRes.status === "fulfilled"
    ? (ordersRes.value.pending || 0) : 0;
  const sec = d.security || {};
  const fmtDate = fmtDateJST;
  const pendingInquiries =
    inquiries.filter((q) => q.status !== "対応済み").length;
  let alerts = alertsRes.status === "fulfilled" ? alertsRes.value : null;

  // ユーザー別管理(操作)とユーザー別使用状況(閲覧)で列を分ける
  // (2026-08-19・従来は1つの表に混在していて見づらかった)。
  const flagsFor = (u) => {
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
    return flags.join(" ") || "—";
  };
  const nameCell = (u) => `${escapeHtml(u.display_name || u.username)}<br>
    <span class="muted">${escapeHtml(u.username)}</span>`;

  const mgmtRows = d.users.map((u) => `<tr>
      <td>${nameCell(u)}</td>
      <td>${u.role}</td>
      <td>${flagsFor(u)}</td>
      <td><label style="white-space:nowrap"><input type="checkbox"
        class="test-flag-cb" data-uid="${u.id}"
        ${u.is_test ? "checked" : ""} /> テスト</label></td>
      <td>
        <input type="number" class="chg-amt" data-uid="${u.id}"
          placeholder="pt" min="-10000" max="10000" step="100" style="width:74px" />
        <input type="text" class="chg-note" data-uid="${u.id}"
          placeholder="理由(必須)" style="width:110px" />
        <button class="btn good chg-btn" data-uid="${u.id}"
        style="padding:3px 8px">適用</button>
        <button class="btn ghost chg-log-btn" data-uid="${u.id}"
        style="padding:3px 8px">履歴</button>
      </td>
      <td><button class="btn ghost force-logout-btn" data-uid="${u.id}"
        style="padding:3px 8px">強制ログアウト</button></td>
    </tr>`).join("");

  const usageRows = d.users.map((u) => {
    // 2026-08-26: 残高・日次/月次上限はいずれも1pt=1円の同一単位のため、
    // 一般ユーザー向け表示(チャージ残高=pt表記)に合わせて管理画面も
    // ptに統一(ユーザー指示)。
    const bal = u.balance_jpy == null ? "—" : Math.round(u.balance_jpy) + "pt";
    const dcap = u.daily_cap_jpy ? u.daily_cap_jpy + "pt" : "—";
    const mcap = u.monthly_cap_jpy ? u.monthly_cap_jpy + "pt" : "—";
    return `<tr>
      <td>${nameCell(u)}</td>
      <td>${u.today_jpy}pt / ${dcap}</td>
      <td>${u.month_jpy}pt / ${mcap}</td>
      <td>${bal}</td>
      <td>${u.calls}</td>
      <td>${fmtDate(u.last_used)}</td>
      <td>${u.word_quizzes}</td>
      <td>${u.phrase_quizzes}</td>
      <td>${fmtDate(u.last_studied)}</td>
    </tr>`;
  }).join("");

  // メモ（管）の状態(サーバーの admin_memos.STATUSES と同じ並び・同じ名前)。
  const AM_STATUSES = ["起票", "対応済み", "対応不要", "ペンディング", "クローズ"];
  const TABS = [
    ["user-manage", "👤 ユーザー別管理"],
    ["user-usage", "📊 ユーザー別使用状況"],
    ["cost-report", "💰 コスト管理"],
    ["pl-report", "💹 実収支"],
    ["logs", `📜 ログ`],
    ["inquiries", `📮 問い合わせ対応${pendingInquiries ? ` (${pendingInquiries})` : ""}`],
    ["charge-keys", `🧾 購入チャージキー対応${pendingOrders ? ` (${pendingOrders})` : ""}`],
    ["memos", "📝 メモ（管）"],
    ["other", "🗂️ その他"],
  ];

  root.innerHTML = `
    <h1>👑 管理者情報</h1>
    <p class="sub">ユーザー別の利用状況・上限・残高・問題の把握（管理者専用）。</p>
    <div id="adminAlertBanner"></div>
    <div class="steps" id="adminTabs">${TABS.map(([key, label], i) => `
      <button type="button" class="step-chip${i === 0 ? " active" : ""}"
        data-sec="${key}">${label}</button>`).join("")}
    </div>

    <div class="card">
      <p class="muted">以下の集計フィルタは、ユーザー別管理/使用状況・
        利用状況分析・サーバー状態の同時アクセス数・ログイン履歴・
        チャージキー入力ログに共通で効きます（集計自体は全ユーザー分を
        保持しており、表示のみの絞り込みです）。</p>
      <div class="row">
        <label><input type="checkbox" id="aggIncludeAdmin"
          ${adminAggFilters.include_admin ? "checked" : ""} />
          管理者を含める</label>
        <label><input type="checkbox" id="aggIncludeInvited"
          ${adminAggFilters.include_invited ? "checked" : ""} />
          招待ユーザー(メール未登録)を含める</label>
        <label><input type="checkbox" id="aggIncludeTest"
          ${adminAggFilters.include_test ? "checked" : ""} />
          テストユーザーを含める</label>
      </div>
    </div>

    <div class="admin-sec" data-sec="user-manage">
      <div class="card">
        <h2>👤 ユーザー別管理</h2>
        <p class="muted">残高調整・強制ログアウトなど、ユーザーへの操作。</p>
        <table class="mt"><thead><tr>
          <th>担当者 / ID</th><th>権限</th><th>状態</th><th>テスト扱い</th>
          <th>チャージ(¥)</th><th>操作</th>
        </tr></thead><tbody>${mgmtRows}</tbody></table>
        <p class="muted mt">チャージは<b>1回 最大¥1000</b>・理由必須。
          「残高切れ/日上限/月上限」は利用が止まっている目安です。</p>
      </div>
    </div>

    <div class="admin-sec" data-sec="user-usage" style="display:none">
      <div class="card">
        <h2>📊 ユーザー別使用状況</h2>
        <p class="muted">閲覧専用。残高は日次/月次の無料枠（上限）とは
          別管理で、枠に到達した後の利用で消費されます。「AI回数」は
          会話等のAI機能利用のみを表し、無料の単語/フレーズクイズは
          含みません（そちらは「単語クイズ数」「フレーズクイズ数」列）。</p>
        <table class="mt"><thead><tr>
          <th>担当者 / ID</th><th>今日 / 上限</th><th>今月 / 上限</th>
          <th>残高</th><th>AI回数</th><th>AI最終利用(JST)</th>
          <th>単語クイズ数</th><th>フレーズクイズ数</th><th>最終学習(JST)</th>
        </tr></thead><tbody>${usageRows}</tbody></table>
      </div>
    </div>

    <div class="admin-sec" data-sec="logs" style="display:none">
      <div class="card">
        <h2>📜 ログ（概要）</h2>
        <div class="grid cols-4">
          <div class="stat"><div class="num">${pendingInquiries}</div>
            <div class="lbl">未対応の問い合わせ</div></div>
          <div class="stat"><div class="num">${sec.locked_accounts ?? 0}</div>
            <div class="lbl">ロック中アカウント</div></div>
          <div class="stat"><div class="num">${sec.locked_ips ?? 0}</div>
            <div class="lbl">ロック中IP(スプレー)</div></div>
          <div class="stat"><div class="num">${d.users.length}</div>
            <div class="lbl">登録ユーザー数</div></div>
        </div>
        <p class="muted mt">詳細は下の各項目を開いてください（開いたときに
          データを取得します）。期間・件数はそれぞれの項目内で指定できます。</p>
      </div>

      <details class="log-group" id="logServerStatusDetails">
        <summary>🖥️ サーバー状態（CPU/RAM/ディスク・同時アクセス）</summary>
        <p class="muted mt">サクラVPSはn8n・ecopy等の他プロジェクトと相乗り
          のため、ホスト全体の負荷をscripts/collect_server_stats.pyが
          VPS側cronで5分おきに収集したものを表示します。上位プランへの
          乗り換えが必要かどうかの判断材料用です。</p>
        <div id="serverStatusWrap" class="mt"><p class="muted">未読み込み</p></div>
        <div class="row mt">
          <button class="btn ghost server-hist-range" data-hours="24"
            style="padding:3px 10px">24時間</button>
          <button class="btn ghost server-hist-range active" data-hours="168"
            style="padding:3px 10px">1週間</button>
          <button class="btn ghost server-hist-range" data-hours="720"
            style="padding:3px 10px">1ヶ月</button>
        </div>
        <div id="serverStatusHistWrap" class="mt"><p class="muted">未読み込み</p></div>
      </details>

      <details class="log-group" id="logLoginDetails">
        <summary>🔑 ログイン履歴（直近100件）</summary>
        <div id="loginLogWrap" class="mt"><p class="muted">未読み込み</p></div>
      </details>

      <details class="log-group" id="logAnonAccessDetails">
        <summary>👤 未登録アクセス状況（未ログイン訪問者）</summary>
        <p class="muted mt">トップページ/取扱説明書(このアプリについて)の
          閲覧と新規登録の試行をIP単位で集計。国・場所・接続元組織名は
          外部API(ipapi.co・失敗時はipwho.is)の結果をキャッシュしたもの
          （初回アクセス時は未取得で空欄のことがあり、少し待って再読み込み
          すると埋まる。過去分はscripts/backfill_geoip.pyで補完できる）。
          端末・ブラウザはUser-Agentからの推定表示です。
          IPの右の「※1〜※4」は訪問者種別の推定（意味は表の下に記載）。
          同一IPを共有する複数人は1行にまとまる/同じ人でもIPが変われば
          複数行に分かれる、というIP単位ならではの目安であることに注意。</p>
        <div class="row">
          <label>直近:
            <select id="anonAccessDays">
              <option value="7">7日</option>
              <option value="30" selected>30日</option>
              <option value="90">90日</option>
              <option value="365">1年</option>
            </select></label>
          <label>表示件数（明細）:
            <select id="anonAccessLimit">
              <option value="50">50件</option>
              <option value="100">100件</option>
              <option value="200">200件</option>
              <option value="500" selected>500件</option>
              <option value="1000">1000件</option>
              <option value="2000">2000件</option>
            </select></label>
          <button class="btn ghost" id="anonAccessReload"
            style="padding:3px 10px">再読み込み</button>
        </div>
        <div id="anonAccessSummary" class="mt">
          <p class="muted">未読み込み</p></div>
        <details id="anonAccessDetailBox" class="log-group mt">
          <summary>📋 IPごとの明細（絞り込み・並べ替え）</summary>
          <div class="row mt" id="anonAccessFilters">
            <span class="muted">表示する種別:</span>
            <label><input type="checkbox" class="anon-mark" value="0" checked>
              人間（印なし）</label>
            <label><input type="checkbox" class="anon-mark" value="1">
              ※1 管理者</label>
            <label><input type="checkbox" class="anon-mark" value="2">
              ※2 機械クローラー</label>
            <label><input type="checkbox" class="anon-mark" value="3">
              ※3 AIクローラー</label>
            <label><input type="checkbox" class="anon-mark" value="4">
              ※4 その他</label>
          </div>
          <div id="anonAccessWrap" class="mt"><p class="muted">未読み込み</p></div>
        </details>
      </details>

      <details class="log-group" id="logRegFunnelDetails">
        <summary>🚪 登録に至らない原因分析</summary>
        <p class="muted mt">未登録訪問者を1人ずつ区別するCookie(2026-08-30
          導入)を使い、訪問→「このアプリについて」確認→登録試行→登録完了
          の各段階の人数を集計。導入前のデータには付いていないため、
          この機能導入以降のデータからのみ正確になります（それ以前は
          上の「未登録アクセス状況」(IP単位)を参照してください）。
          ボット・自分の端末(管理者/テストでログインした端末・内部
          Cookie)は除外しています。「JS到達」以降の流入元・表示ビーコンは
          計測開始以降のデータのみです。操作記録は約90日で古いものから削除
          されるため、それより長い期間を選ぶと「JS到達」「人間訪問」などの
          人数は実際より少なく出ます(訪問記録の方が長く残るため)。</p>
        <div class="row">
          <label>直近:
            <select id="regFunnelDays">
              <option value="7">7日</option>
              <option value="30" selected>30日</option>
              <option value="90">90日</option>
            </select></label>
          <button class="btn ghost" id="regFunnelReload"
            style="padding:3px 10px">再読み込み</button>
        </div>
        <div id="regFunnelWrap" class="mt"><p class="muted">未読み込み</p></div>
      </details>

      <details class="log-group" id="logRegistrantsDetails">
        <summary>🧑‍🎓 登録者一覧（アンケート込み）</summary>
        <p class="muted mt">新規登録時のアンケート回答も含めた登録者一覧
          （新しい順・最大200件）。上部の集計フィルタ
          （管理者/招待ユーザー/テストユーザーを含めるか）が効きます。</p>
        <button class="btn ghost" id="registrantsReload"
          style="padding:3px 10px">再読み込み</button>
        <div id="registrantsWrap" class="mt"><p class="muted">未読み込み</p></div>
      </details>

      <details class="log-group" id="logSurveySummaryDetails">
        <summary>📋 アンケート集計</summary>
        <p class="muted mt">登録時アンケートの回答を項目別に集計します。
          複数選択欄（職業詳細・利用目的・きっかけ・興味分野）は選択肢
          ごとの人数、単一選択欄（職業分類・年代・性別）はそのままの
          内訳です。</p>
        <button class="btn ghost" id="surveySummaryReload"
          style="padding:3px 10px">再読み込み</button>
        <div id="surveySummaryWrap" class="mt"><p class="muted">未読み込み</p></div>
      </details>

      <details class="log-group" id="logVisitTrendDetails">
        <summary>📊 訪問者数の推移（人間/クローラー別）</summary>
        <p class="muted mt">トップページ/取扱説明書/ログイン画面の閲覧
          (landing_visits・kind='visit')を日次集計。人間/クローラーの
          判定は上の「未登録アクセス状況」と同じ基準（管理者自身は除外）。</p>
        <div class="row">
          <button class="btn ghost visit-trend-range" data-days="7"
            style="padding:3px 10px">1週間</button>
          <button class="btn ghost visit-trend-range active" data-days="30"
            style="padding:3px 10px">1ヶ月</button>
          <button class="btn ghost visit-trend-range" data-days="90"
            style="padding:3px 10px">3ヶ月</button>
          <button class="btn ghost visit-trend-range" data-days="180"
            style="padding:3px 10px">6ヶ月</button>
          <button class="btn ghost" id="visitTrendReload"
            style="padding:3px 10px">🔄 再読み込み</button>
          <label><input type="checkbox" id="visitTrendCumulative" checked />
            累積(延べ)</label>
          <label><input type="checkbox" id="visitTrendShowBot" checked />
            クローラー表示</label>
        </div>
        <div id="visitTrendWrap" class="mt"><p class="muted">未読み込み</p></div>
      </details>

      <details class="log-group" id="logGrowthDailyDetails">
        <summary>📈 日次スナップショット（成長ログ・集計値を恒久保存）</summary>
        <p class="muted mt">毎日、前日分の集計(訪問・JS到達・操作あり・登録・
          ログイン・アクティブ人数・エラー数など)を、自分(管理者/テスト端末)
          とボットを除いた人数・件数だけで保存しています。操作記録(約90日で
          削除)が消えた後も過去の推移が変わりません。当日分は翌日の朝に入ります。
          「日別ユニーク」の合計は延べ人日で、同じ人が複数日に来れば重複して
          数えます。</p>
        <div class="row">
          <button class="btn ghost growth-range" data-days="14"
            style="padding:3px 10px">2週間</button>
          <button class="btn ghost growth-range active" data-days="30"
            style="padding:3px 10px">1ヶ月</button>
          <button class="btn ghost growth-range" data-days="90"
            style="padding:3px 10px">3ヶ月</button>
          <button class="btn ghost growth-range" data-days="180"
            style="padding:3px 10px">6ヶ月</button>
          <button class="btn ghost" id="growthDailyReload"
            style="padding:3px 10px">🔄 再読み込み</button>
        </div>
        <div id="growthDailyWrap" class="mt"><p class="muted">未読み込み</p></div>
      </details>

      <details class="log-group" id="logChargeKeyDetails">
        <summary>🧾 チャージキー入力ログ（直近100件・無期限保持）</summary>
        <p class="muted mt">キー番号(secretを含まない公開部分)は無期限保持
          しています。</p>
        <div id="chargeKeyLogWrap" class="mt"><p class="muted">未読み込み</p></div>
      </details>

      <details class="log-group" id="logWithdrawalDetails">
        <summary>🚪 退会理由（直近200件・無期限保持）</summary>
        <p class="muted mt">設定画面の「退会」から本人が選んだ理由と自由
          記入です。退会時に学習データは削除・個人情報は匿名化しています
          （username列は退会前のログイン用メールアドレスではなく匿名化後の
          値です）。</p>
        <div id="withdrawalLogWrap" class="mt"><p class="muted">未読み込み</p></div>
      </details>

      <details class="log-group" id="logErrorDetails">
        <summary>🐛 エラーログ（data/app.log）</summary>
        <div class="row mt">
          <label>表示件数:
            <select id="errLogLines">
              <option value="50">直近50件</option>
              <option value="100">直近100件</option>
              <option value="200" selected>直近200件</option>
              <option value="500">直近500件</option>
              <option value="1000">直近1000件</option>
            </select></label>
          <label>絞り込み:
            <select id="errLogLevel">
              <option value="ERROR" selected>エラーのみ</option>
              <option value="WARNING">警告以上</option>
              <option value="ALL">全件（INFO含む）</option>
            </select></label>
          <button class="btn ghost" id="errLogReload"
            style="padding:3px 10px">再読み込み</button>
        </div>
        <div id="errorLogWrap" class="mt"><p class="muted">未読み込み</p></div>
      </details>

      <details class="log-group" id="logClientErrorDetails">
        <summary>🐛 フロントエンドJSエラー（未捕捉例外）</summary>
        <p class="muted mt">画面のJSで捕捉されなかった例外(window.onerror/
          unhandledrejection)。従来ブラウザのコンソールにしか残らず
          気づけなかったバグを拾う目的(2026-08-30)。同じ内容が繰り返し
          起きている場合はメッセージ別の件数一覧で気づきやすくしている。</p>
        <div class="row">
          <label>直近:
            <select id="clientErrLogDays">
              <option value="1">1日</option>
              <option value="7" selected>7日</option>
              <option value="30">30日</option>
              <option value="90">90日</option>
            </select></label>
          <button class="btn ghost" id="clientErrLogReload"
            style="padding:3px 10px">再読み込み</button>
        </div>
        <div id="clientErrorLogWrap" class="mt"><p class="muted">未読み込み</p></div>
      </details>

      <details class="log-group" id="logAccessDetails">
        <summary>📈 アクセスログ集計（日別）</summary>
        <p class="muted mt">Caddyのアクセスログをscripts/analyze_access_log.py
          がVPSのcronで日次集計したもの。AIクローラー/検索botを除いた
          「人間らしきIP」が実際の訪問者の目安。</p>
        <div class="row">
          <label>直近:
            <select id="accLogDays">
              <option value="7">7日</option>
              <option value="30" selected>30日</option>
              <option value="90">90日</option>
              <option value="365">1年</option>
            </select></label>
          <span class="muted">または期間で指定:</span>
          <label>から <input type="date" id="accLogFrom" style="width:150px" /></label>
          <label>まで <input type="date" id="accLogTo" style="width:150px" /></label>
          <button class="btn ghost" id="accLogReload"
            style="padding:3px 10px">再読み込み</button>
          <button class="btn ghost" id="accLogClearRange"
            style="padding:3px 10px">期間指定をクリア</button>
        </div>
        <div id="accessLogWrap" class="mt"><p class="muted">未読み込み</p></div>
      </details>

      <details class="log-group" id="logAiSearchDetails">
        <summary>🔍 AI利用ログ検索</summary>
        <p class="muted mt">ユーザーID・期間・機能・モデル・IPで絞り込み。
          テスト/開発起因の利用と実利用の切り分けに使う。</p>
        <div class="grid cols-4 mt">
          <input type="number" id="auSearchUid" placeholder="ユーザーID" />
          <input type="date" id="auSearchFrom" />
          <input type="date" id="auSearchTo" />
          <input type="text" id="auSearchFeature" placeholder="機能(feature)" />
          <input type="text" id="auSearchModel" placeholder="モデル" />
          <input type="text" id="auSearchIp" placeholder="IP" />
          <button class="btn" id="auSearchBtn">検索</button>
        </div>
        <div id="aiUsageSearchWrap" class="mt">
          <p class="muted">条件を指定して検索してください（未指定は全件）。</p>
        </div>
      </details>

      <details class="log-group" id="logUsageAnalyticsDetails">
        <summary>📊 利用状況分析（画面別・機能別再生・ボタン押下・IP別・
          分野別・年代/性別）</summary>
        <p class="muted mt">アプリ内の操作ログ(usage_events)をその場で
          集計して表示（保存済みの集計ではなく毎回最新の内容）。項目ごとに
          折りたたんであるので、見たいものだけ開いてください。</p>
        <div class="grid cols-4 mt" style="align-items:end">
          <label>集計期間
            <select id="uaDays">
              <option value="7">直近7日</option>
              <option value="30" selected>直近30日</option>
              <option value="90">直近90日</option>
              <option value="365">直近1年</option>
            </select>
          </label>
          <button class="btn" id="uaRefreshBtn">🔄 更新</button>
        </div>
        <p id="uaSummaryWrap" class="muted mt">未読み込み</p>

        <details class="log-group">
          <summary>📄 画面別アクセス（page）</summary>
          <div id="uaPagesWrap" class="mt"><p class="muted">未読み込み</p></div>
        </details>
        <details class="log-group">
          <summary>🔊 機能別再生（play）</summary>
          <div id="uaPlaysWrap" class="mt"><p class="muted">未読み込み</p></div>
        </details>
        <details class="log-group">
          <summary>🖱️ ボタン押下（click・上位50）</summary>
          <div id="uaClicksWrap" class="mt"><p class="muted">未読み込み</p></div>
        </details>
        <details class="log-group">
          <summary>🔤 単語分野別（再生ベース）</summary>
          <div id="uaWordDomainsWrap" class="mt"><p class="muted">未読み込み</p></div>
        </details>
        <details class="log-group">
          <summary>💬 フレーズ分野別（シーン・再生ベース）</summary>
          <div id="uaPhraseScenesWrap" class="mt"><p class="muted">未読み込み</p></div>
        </details>
        <details class="log-group">
          <summary>🌐 IPアドレス別</summary>
          <div id="uaIpsWrap" class="mt"><p class="muted">未読み込み</p></div>
        </details>
        <details class="log-group">
          <summary>📅 日別推移（画面表示・再生・クリック・新規登録）</summary>
          <div id="uaDailyWrap" class="mt"><p class="muted">未読み込み</p></div>
        </details>
        <details class="log-group">
          <summary>⏰ 時間帯別（0〜23時・JST・期間合計）</summary>
          <div id="uaHourlyWrap" class="mt"><p class="muted">未読み込み</p></div>
        </details>
        <details class="log-group">
          <summary>🔗 流入経路（登録時アンケート）</summary>
          <p class="muted mt">サインアップ時「このアプリを何で知りましたか」
            の回答を集計（複数選択可のため延べ数）。Referer(参照元URL)の
            日別集計は上の「📈 アクセスログ集計（日別）」も参照。</p>
          <div id="uaReferralsWrap" class="mt"><p class="muted">未読み込み</p></div>
        </details>
        <details class="log-group">
          <summary>🧑‍🤝‍🧑 年代・性別 × 単語分野/フレーズシーン</summary>
          <p class="muted mt">サインアップ時の任意アンケート回答と
            突き合わせたクロス集計。回答が無いユーザーは「(未回答)」に
            まとめています。</p>
          <div id="uaDemoWrap" class="mt"><p class="muted">未読み込み</p></div>
        </details>
      </details>

      <details class="log-group" id="logPowerUsersDetails">
        <summary>⭐ お得意様の深掘り分析（複数回・複数日の利用者）</summary>
        <p class="muted mt">条件を満たす利用者を人単位（ログイン済みは
          アカウント、未ログインはCookie）でグルーピングし、閲覧タブ・
          単語の分野・フレーズのシーン等の内訳から興味の傾向を出します。
          2026-08-30より前の未ログイン操作やCookie不可の環境はIP単位に
          フォールバックするため、複数人が1人として混ざる場合があります
          （該当行に注記）。ログイン済みは表示名の下にログイン名(メール/
          ユーザー名)も併記します。上部の集計フィルタ(管理者/招待
          ユーザー/テストユーザーを含めるか)もこの一覧に反映されます。
          管理者/テストアカウントでログインしたことのある端末(ブラウザ)
          は、ログアウト中の操作も同じフィルタで一覧から分けています
          （含めた場合は「(管理者の端末)」等と表示）。</p>
        <div class="grid cols-4 mt" style="align-items:end">
          <label>集計期間
            <select id="puDays">
              <option value="30">直近30日</option>
              <option value="90" selected>直近90日</option>
              <option value="180">直近180日</option>
              <option value="365">直近1年</option>
            </select>
          </label>
          <label>最低イベント数
            <input type="number" id="puMinEvents" value="5" min="1"
              style="width:70px" />
          </label>
          <label>最低訪問日数
            <input type="number" id="puMinDays" value="2" min="1"
              style="width:70px" />
          </label>
          <button class="btn" id="puRefreshBtn">🔄 更新</button>
        </div>
        <div class="row mt">
          <label><input type="checkbox" id="puIncludeRegistered" checked />
            登録ユーザー(通常会員)を含める</label>
        </div>
        <p id="puSummaryWrap" class="muted mt">未読み込み</p>
        <div id="puItemsWrap" class="mt"><p class="muted">未読み込み</p></div>
      </details>

      <details class="log-group" id="logGuestIpDetails">
        <summary>🕵️ ゲストのIP別深掘り分析</summary>
        <p class="muted mt">未ログイン利用者をIP単位でグルーピングし、
          単語の分野・発声(単語/例文/フレーズの別)・再生に失敗した項目・
          「詳細」ボタンで開いた単語/フレーズ・発生したJSエラー等を
          集計します。表は概要のみで、行をクリックすると詳細が展開
          されます。同一Wi-Fi/会社等でIPを共有する複数人は1行に
          混ざる点にご注意ください。</p>
        <div class="grid cols-3 mt" style="align-items:end">
          <label>集計期間
            <select id="giDays">
              <option value="30">直近30日</option>
              <option value="90" selected>直近90日</option>
              <option value="180">直近180日</option>
              <option value="365">直近1年</option>
            </select>
          </label>
          <label>最低イベント数
            <input type="number" id="giMinEvents" value="1" min="1"
              style="width:70px" />
          </label>
          <button class="btn" id="giRefreshBtn">🔄 更新</button>
        </div>
        <div class="row mt">
          <label><input type="checkbox" id="giIncludeAdmin" />
            管理者のアクセスを含める</label>
          <label><input type="checkbox" id="giIncludeTest" />
            テストアカウントのアクセスを含める</label>
        </div>
        <p class="muted" style="margin:2px 0 0">管理者/テストアカウントで
          ログインしたことのある端末(ブラウザ)は、ログアウト中の操作も
          この一覧から自動的に分けています(管理者は既知IPも判定に使用)。
          一度もログインしていない端末は判別できません。</p>
        <p id="giSummaryWrap" class="muted mt">未読み込み</p>
        <div id="giItemsWrap" class="mt"><p class="muted">未読み込み</p></div>
      </details>
    </div>

    <div class="admin-sec" data-sec="inquiries" style="display:none">
      <div class="card">
        <h2>📮 お問い合わせ・ご要望</h2>
        <p class="muted">ユーザーからの送信を新しい順に表示（手動対応）。</p>
        <table class="mt"><thead><tr>
          <th>日時(JST)</th><th>ログインID</th><th>種別</th><th>お名前</th>
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
      </div>
    </div>

    <div class="admin-sec" data-sec="memos" style="display:none">
      <div class="card">
        <h2>📝 メモ（管）</h2>
        <p class="muted">単語/フレーズ詳細・設定画面の「メモ（管）」ボタンで
          記録した気づきの一覧です。キーワード・状態・タグで絞り込めます
          （タグはクリックで絞り込み／もう一度クリックで解除）。AIからは
          同じ内容を <code>/api/admin-memos</code> または
          <code>admin_memos</code>・<code>admin_memo_tags</code>テーブルで
          検索・集計できます。</p>
        <p class="muted">状態: <b>起票</b>(記録した直後) →
          <b>対応済み</b>(直した) / <b>対応不要</b> / <b>ペンディング</b>(保留)
          → <b>クローズ</b>(確認まで終わり)。各メモの状態欄から
          どの状態へも変更できます。</p>
        <div class="row">
          <input id="amQ" placeholder="🔍 キーワード" style="width:180px" />
          <select id="amStatus">
            <option value="">状態: 全て</option>
            ${AM_STATUSES.map((s) => `<option value="${s}"${
              s === "起票" ? " selected" : ""}>状態: ${s}</option>`).join("")}
          </select>
          <button type="button" class="btn ghost" id="amReload">再読込</button>
          <span class="muted" id="amCount"></span>
        </div>
        <div class="row mt" id="amTags"></div>
        <div class="mt" id="amList"><p class="muted">読み込み中…</p></div>
      </div>
    </div>

    <div class="admin-sec" data-sec="charge-keys" style="display:none">
      <div class="card">
        <h2>🧾 購入チャージキー対応</h2>
        <p class="muted">BASE注文の記録・チャージキー発行・配送管理はこちら
          （URLを直接知っていても管理者以外はアクセスできません）。
          BASE注文は30分おきに自動同期されるため、この画面を開いた時点の
          未配送件数がそのまま最新の目安になります。</p>
        <p>${pendingOrders ?
          `<span class="badge-warn">未配送 ${pendingOrders}件</span>` :
          `<span class="muted">未配送はありません。</span>`}</p>
        <a class="btn good" href="/admin/fulfillment">フルフィルメント管理を開く →</a>
      </div>
    </div>

    <div class="admin-sec" data-sec="cost-report" style="display:none">
      <div class="card">
        <h2>💰 コスト管理(原価・課金・粗利)</h2>
        <p class="muted">AI原価(ai_usage)と実際の課金控除額(balance_ledger)
          を突き合わせた、機能別・ユーザー別の粗利レポートです。粗利率
          0%未満は赤字(<span class="badge-bad">赤字</span>)、20%未満は
          低粗利(<span class="badge-warn">低粗利</span>)として警告表示
          します(閾値はapp/routers/system.pyのCOST_REPORT_*_MARGIN_PCT
          と対応)。無料枠内の利用(課金¥0)はそのぶん赤字寄りに出ますが、
          想定内の場合も多いため実態と合わせて確認してください。</p>
        <div class="row" style="align-items:center">
          <label>集計期間:
            <select id="costReportDays">
              <option value="7">直近7日</option>
              <option value="30" selected>直近30日</option>
              <option value="90">直近90日</option>
              <option value="365">直近1年</option>
            </select>
          </label>
        </div>
        <div id="costReportWrap" class="mt"><p class="muted">読み込み中…</p></div>
      </div>
    </div>

    <div class="admin-sec" data-sec="pl-report" style="display:none">
      <div class="card">
        <h2>💹 実収支(実際の売上-実際のコスト)</h2>
        <p class="muted">BASE注文・PayPay決済の実入金額(円)から、AI原価
          (為替換算)とサーバー代・広告費などの固定費(月額を集計期間で
          日割り)を差し引いた、本当の損益です。上の「コスト管理」は
          内部ポイント経済の粗利チェック(ポイント付与額とAI原価の
          突き合わせ)であり、これとは別の指標です。サーバー代の金額は
          app/routers/system.pyのFIXED_MONTHLY_SERVER_COST_JPYで管理して
          います。広告費は、下の「広告費の実額入力」で入れた日は実額、
          入力の無い日は予算スケジュール(AD_DAILY_BUDGET_SCHEDULE)で
          日割りした<b>予算(推定)</b>で計算します。</p>
        <div class="row" style="align-items:center">
          <label>集計期間:
            <select id="plReportDays">
              <option value="7">直近7日</option>
              <option value="30" selected>直近30日</option>
              <option value="90">直近90日</option>
              <option value="365">直近1年</option>
            </select>
          </label>
        </div>
        <div id="plReportWrap" class="mt"><p class="muted">読み込み中…</p></div>
      </div>
      <div class="card">
        <h2>📣 広告費の実額入力</h2>
        <p class="muted">Google広告の管理画面で確認した1日ごとの実際の
          費用(円)を入力します(日付はJST・同じ日に入れ直すと上書き)。
          入力した日は予算(推定)ではなくこの実額が使われ、上の実収支と
          広告のCPAに反映されます。入力の無い日は予算スケジュールで
          補われます。</p>
        <div class="row" style="align-items:center; gap:8px; flex-wrap:wrap">
          <label>日付 <input type="date" id="adSpendDate" /></label>
          <label>広告 <select id="adSpendSource">
            <option value="google_ads">Google広告</option>
            <option value="other">その他</option>
          </select></label>
          <label>金額(円) <input type="number" id="adSpendJpy" min="0"
            step="1" style="width:110px" /></label>
          <label>メモ <input type="text" id="adSpendNote" maxlength="200"
            style="width:160px" /></label>
          <button class="btn" id="adSpendSave"
            style="padding:4px 12px">登録</button>
          <span id="adSpendMsg" class="muted"></span>
        </div>
        <div id="adSpendList" class="mt"><p class="muted">読み込み中…</p></div>
      </div>
    </div>

    <div class="admin-sec" data-sec="other" style="display:none">
      <div class="card">
        <h2>💳 PayPay決済テスト</h2>
        <p class="muted">サンドボックス環境での結合テスト専用ページ
          (¥800/¥8,000のテスト決済・状態確認・キャンセル・返金)。</p>
        <a class="btn good" href="/admin/paypay-test">PayPayテストを開く →</a>
      </div>
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
        <h2>💾 ディスク使用量（ログ・バックアップ）</h2>
        <p class="muted">ログ・バックアップ用に確保した予算に対する使用量。
          DB本体（単語/フレーズ/音声等の共有コンテンツ含む・数GB規模）は
          予算の対象外で参考表示です。</p>
        <div id="diskUsageWrap" class="mt"><p class="muted">読み込み中…</p></div>
      </div>
    </div>`;

  // タブ切替（既に描画済みのDOMを表示/非表示するだけ・再取得なし）。
  root.querySelectorAll("#adminTabs .step-chip").forEach((btn) => {
    btn.addEventListener("click", () => {
      root.querySelectorAll("#adminTabs .step-chip")
        .forEach((b) => b.classList.toggle("active", b === btn));
      const target = btn.dataset.sec;
      root.querySelectorAll(".admin-sec").forEach((secEl) => {
        secEl.style.display = secEl.dataset.sec === target ? "" : "none";
      });
    });
  });

  // 📝 メモ（管）タブ(2026-09-19): 初めて開いたときに読み込む。記録は単語/
  // フレーズ詳細・設定画面のadminMemoWidgetから。タグ・キーワード・状態で
  // 絞り込み、対応済みへ切り替えられる(本文は編集・削除不可のログ)。
  {
    const amSelTags = new Set();
    const amList = root.querySelector("#amList");
    const amTagsBox = root.querySelector("#amTags");
    const AM_SRC = {
      word_detail: "単語詳細", phrase_detail: "フレーズ詳細",
      settings: "設定画面",
    };
    // 状態ピルの色(既存の.pillの色を流用): 起票=橙(要対応) / 対応済み・
    // クローズ=緑 / 対応不要・ペンディング=青。
    const AM_PILL = {
      "起票": "vague", "対応済み": "mastered", "クローズ": "mastered",
      "対応不要": "info", "ペンディング": "info",
    };
    const loadMemos = async () => {
      const q = new URLSearchParams({ limit: "200" });
      const kw = root.querySelector("#amQ").value.trim();
      const st = root.querySelector("#amStatus").value;
      if (kw) q.set("q", kw);
      if (st) q.set("status", st);
      if (amSelTags.size) q.set("tag", [...amSelTags].join(","));
      amList.innerHTML = `<p class="muted">読み込み中…</p>`;
      try {
        const [res, tg] = await Promise.all([
          api.get("/api/admin-memos?" + q.toString()),
          api.get("/api/admin-memos/tags"
            + (st ? "?status=" + encodeURIComponent(st) : "")),
        ]);
        root.querySelector("#amCount").textContent = `${res.total}件`;
        // 状態の選択肢に全体の件数を添える(絞り込みに関係なく全メモ分)。
        const stSel = root.querySelector("#amStatus");
        [...stSel.options].forEach((o) => {
          if (o.value) {
            o.textContent = `状態: ${o.value} (${
              (res.status_counts || {})[o.value] ?? 0})`;
          }
        });
        amTagsBox.innerHTML = tg.tags.map((t) => `<button type="button"
          class="step-chip am-tag${amSelTags.has(t.tag) ? " active" : ""}"
          data-tag="${escapeHtml(t.tag)}">#${escapeHtml(t.tag)}
          (${t.count})</button>`).join("")
          || `<span class="muted">タグはまだありません。</span>`;
        amList.innerHTML = res.memos.length ? res.memos.map((m) => `
          <div class="card" style="margin:8px 0">
            <div class="row" style="justify-content:space-between">
              <span class="muted">${fmtDate(m.created_at)}
                ・${AM_SRC[m.source] || "—"}${m.ref_english
                  ? ` ・<b>${escapeHtml(m.ref_english)}</b>
                    ${escapeHtml(m.ref_japanese)}` : ""}</span>
              <span class="pill ${AM_PILL[m.status] || "info"}">${
                escapeHtml(m.status)}</span>
            </div>
            <p style="white-space:pre-wrap; margin:6px 0">${
              escapeHtml(m.body)}</p>
            <div class="row">
              ${m.tags.map((t) => `<button type="button"
                class="step-chip am-tag" data-tag="${escapeHtml(t)}">#${
                escapeHtml(t)}</button>`).join("")}
              <label class="muted" style="margin-left:auto">状態:
                <select class="am-status" data-id="${m.id}"
                  style="padding:3px 6px">${AM_STATUSES.map((s) =>
                    `<option${s === m.status ? " selected" : ""}>${s}</option>`
                  ).join("")}</select></label>
            </div>
          </div>`).join("")
          : `<p class="muted">該当するメモはありません。</p>`;
      } catch (e) {
        amList.innerHTML = `<p class="muted">取得できませんでした: ${
          escapeHtml(e.message || "")}</p>`;
      }
    };
    root.querySelector("#amReload").addEventListener("click", loadMemos);
    root.querySelector("#amStatus").addEventListener("change", loadMemos);
    root.querySelector("#amQ").addEventListener("keydown", (e) => {
      if (e.key === "Enter") loadMemos();
    });
    // タグチップ(絞り込み用の一覧・各メモ内のタグ)と状態切替ボタン。
    root.querySelector('.admin-sec[data-sec="memos"]')
      .addEventListener("click", async (e) => {
        const tag = e.target.closest(".am-tag");
        if (tag) {
          const t = tag.dataset.tag;
          if (amSelTags.has(t)) amSelTags.delete(t); else amSelTags.add(t);
          loadMemos();
        }
      });
    // 状態の変更(各メモの状態セレクト)。
    root.querySelector('.admin-sec[data-sec="memos"]')
      .addEventListener("change", async (e) => {
        const st = e.target.closest("select.am-status");
        if (!st) return;
        st.disabled = true;
        try {
          await api.put(`/api/admin-memos/${st.dataset.id}/status`,
            { status: st.value });
          loadMemos();
        } catch (err) {
          st.disabled = false;
          toast("更新に失敗しました");
          loadMemos();
        }
      });
    let memosLoaded = false;
    root.querySelector('#adminTabs .step-chip[data-sec="memos"]')
      .addEventListener("click", () => {
        if (!memosLoaded) { memosLoaded = true; loadMemos(); }
      });
  }

  async function loadServerStatus() {
    const wrap = root.querySelector("#serverStatusWrap");
    wrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    try {
      const res = await api.get(
        `/api/system/admin/server-status?${adminAggQuery()}`);
      const h = res.host;
      if (!h) {
        wrap.innerHTML = `<p class="muted">まだ収集されていません
          （VPS側のcron設定が必要です）。</p>
          <div class="grid cols-4 mt">
            <div class="stat"><div class="num">${res.active_users_5min}</div>
              <div class="lbl">同時アクセス(直近5分)</div></div>
          </div>`;
        return;
      }
      const containerRows = h.containers
        ? Object.entries(h.containers).map(([name, c]) => `
          <tr><td>${escapeHtml(name)}</td>
            <td>${c.cpu_pct ?? "—"}%</td>
            <td>${escapeHtml(c.mem || "—")}</td></tr>`).join("")
        : "";
      wrap.innerHTML = `
        <p class="muted">最終収集: ${fmtDate(h.ts)}（JST）</p>
        <div class="grid cols-4 mt">
          <div class="stat"><div class="num">${h.load1}</div>
            <div class="lbl">load average(1分・${h.cpu_count}コア)</div></div>
          <div class="stat"><div class="num">${h.mem_pct}%</div>
            <div class="lbl">RAM使用率</div></div>
          <div class="stat"><div class="num">${h.disk_pct}%</div>
            <div class="lbl">ディスク使用率</div></div>
          <div class="stat"><div class="num">${res.active_users_5min}</div>
            <div class="lbl">同時アクセス(直近5分)</div></div>
        </div>
        <p class="muted mt">RAM: ${h.mem_used_mb}MB / ${h.mem_total_mb}MB
          ・ディスク: ${h.disk_used_gb}GB / ${h.disk_total_gb}GB</p>
        ${containerRows ? `<h3 class="mt">コンテナ別
          （相乗りの他プロジェクト含む）</h3>
          <table><thead><tr><th>コンテナ</th><th>CPU%</th>
            <th>メモリ</th></tr></thead>
            <tbody>${containerRows}</tbody></table>` : ""}`;
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
    }
  }

  // --- サーバー負荷の推移グラフ(2026-08-30) ---------------------------
  // buildVisitTrendSvgとは独立の1系列版(訪問者数グラフへの影響を避ける
  // ため既存関数は変更せず新設)。load1/mem_pct/disk_pctを縦に3本並べる。
  function buildMetricTrendSvg(points, key, color, unit) {
    const W = 680, H = 120, padL = 40, padR = 14, padT = 10, padB = 20;
    const innerW = W - padL - padR, innerH = H - padT - padB;
    const n = points.length;
    const vals = points.map((p) => p[key] ?? 0);
    const maxVal = Math.max(1, ...vals);
    const magnitude = Math.pow(10, Math.floor(Math.log10(maxVal || 1)));
    const niceMax = [1, 2, 5, 10].map((s) => s * magnitude)
      .find((v) => maxVal <= v) || 10 * magnitude;
    const x = (i) => padL + (n <= 1 ? innerW / 2 : (innerW * i) / (n - 1));
    const y = (v) => padT + innerH - (innerH * v) / niceMax;
    const gridLines = [0, 0.5, 1].map((f) => {
      const v = Math.round(niceMax * f);
      const yy = y(v);
      return `<line x1="${padL}" y1="${yy}" x2="${W - padR}" y2="${yy}"
          stroke="var(--line)" stroke-width="1" />
        <text x="${padL - 6}" y="${yy + 4}" text-anchor="end"
          font-size="10" fill="var(--muted)">${v}${unit}</text>`;
    }).join("");
    const labelStep = Math.max(1, Math.ceil(n / 6));
    const xLabels = points.map((p, i) => {
      if (i % labelStep !== 0 && i !== n - 1) return "";
      const short = fmtDate(p.ts).slice(5, 16);
      return `<text x="${x(i)}" y="${H - 4}" text-anchor="middle"
        font-size="9" fill="var(--muted)">${escapeHtml(short)}</text>`;
    }).join("");
    const linePath = points.map((p, i) =>
      `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p[key] ?? 0).toFixed(1)}`
    ).join(" ");
    return `<svg viewBox="0 0 ${W} ${H}" style="width:100%;height:auto">
      ${gridLines}${xLabels}
      <path d="${linePath}" fill="none" stroke="${color}" stroke-width="2"
        stroke-linecap="round" stroke-linejoin="round" />
    </svg>`;
  }

  let serverHistHours = 168;
  async function loadServerStatusHistory() {
    const wrap = root.querySelector("#serverStatusHistWrap");
    wrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    try {
      const res = await api.get(
        `/api/system/admin/server-status-history?hours=${serverHistHours}`);
      const points = res.points || [];
      if (!points.length) {
        wrap.innerHTML = `<p class="muted">この期間のデータはまだありません。</p>`;
        return;
      }
      const m = res.max || {};
      wrap.innerHTML = `
        <div class="grid cols-3 mt">
          <div class="stat"><div class="num">${m.load1 ?? "—"}</div>
            <div class="lbl">期間中の最大load average</div></div>
          <div class="stat"><div class="num">${m.mem_pct ?? "—"}%</div>
            <div class="lbl">期間中の最大RAM使用率</div></div>
          <div class="stat"><div class="num">${m.disk_pct ?? "—"}%</div>
            <div class="lbl">期間中の最大ディスク使用率</div></div>
        </div>
        <p class="muted mt">load average</p>
        ${buildMetricTrendSvg(points, "load1", "var(--accent)", "")}
        <p class="muted mt">RAM使用率</p>
        ${buildMetricTrendSvg(points, "mem_pct", "var(--accent-2)", "%")}
        <p class="muted mt">ディスク使用率</p>
        ${buildMetricTrendSvg(points, "disk_pct", "var(--vt-bot)", "%")}`;
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
    }
  }
  function loadServerStatusAll() {
    loadServerStatus();
    loadServerStatusHistory();
  }
  root.querySelectorAll(".server-hist-range").forEach((b) => {
    b.addEventListener("click", () => {
      serverHistHours = Number(b.dataset.hours);
      root.querySelectorAll(".server-hist-range").forEach((x) =>
        x.classList.toggle("active", x === b));
      loadServerStatusHistory();
    });
  });

  async function loadLoginLog() {
    const wrap = root.querySelector("#loginLogWrap");
    wrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    try {
      const rows = await api.get(
        `/api/system/admin/login-log?${adminAggQuery()}`);
      if (!rows.length) {
        wrap.innerHTML = `<p class="muted">まだありません。</p>`;
        return;
      }
      wrap.innerHTML = `<table><thead><tr>
        <th>日時(JST)</th><th>ユーザー名</th><th>IP</th><th>ホスト名</th>
        <th>結果</th>
        </tr></thead><tbody>${rows.map((r) => `
        <tr>
          <td class="muted">${fmtDate(r.created_at)}</td>
          <td>${escapeHtml(r.username)}</td>
          <td class="muted">${escapeHtml(r.ip || "—")}</td>
          <td class="muted">${escapeHtml(r.hostname || "—")}</td>
          <td>${r.success
            ? '<span class="badge-ok">成功</span>'
            : '<span class="badge-bad">失敗</span>'}</td>
        </tr>`).join("")}</tbody></table>`;
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
    }
  }

  // 訪問者種別（※1〜※4）の見出し。表を横に伸ばさないため、一覧では
  // IPの右に上付きの印だけを出し、意味はサマリと欄外の備考で説明する。
  const ANON_MARKS = {
    0: "人間とみなせるアクセス（印なし）",
    1: "※1 管理者自身",
    2: "※2 機械クローラー（検索エンジン・SNSのリンクプレビュー等）",
    3: "※3 AIクローラー（生成AIの検索/学習用）",
    4: "※4 その他（人間の普通のアクセスではないもの）",
  };
  // 一覧の並べ替え状態（列キーと昇順/降順）。既定は最終アクセスの新しい順。
  let anonSort = { key: "last_seen", asc: false };
  let anonData = null;   // 直近に取得したレスポンス（再描画用に保持）

  function anonSelectedMarks() {
    return new Set(Array.from(
      root.querySelectorAll(".anon-mark:checked"), (c) => Number(c.value)));
  }

  // 明細だけを描き直す（絞り込み・並べ替えのたびに再取得しないで済む）。
  function renderAnonRows() {
    const wrap = root.querySelector("#anonAccessWrap");
    if (!anonData) { wrap.innerHTML = `<p class="muted">未読み込み</p>`; return; }
    const marks = anonSelectedMarks();
    const rows = (anonData.items || []).filter((r) => marks.has(r.mark || 0));
    if (!rows.length) {
      wrap.innerHTML = `<p class="muted">この条件に当てはまるIPはありません。
        （上のチェックで種別を追加してください）</p>`;
      return;
    }
    const place = (r) => [r.country, r.region, r.city]
      .filter(Boolean).join(" / ") || "—";
    // Accept-Languageの先頭タグだけ抜き出す（例:
    // "ja-JP,ja;q=0.9,en-US;q=0.8" → "ja-JP"）。フルの値はtitleで見せる。
    const primaryLang = (r) => (r.accept_language || "").split(",")[0]
      .split(";")[0].trim();
    const val = (r, k) => {
      if (k === "place") return place(r);
      if (k === "org") return r.org || r.hostname || "";
      if (k === "signup") return (r.signup_attempted ? 1 : 0)
        + (r.signup_succeeded ? 1 : 0);
      if (k === "viewed_about") return r.viewed_about ? 1 : 0;
      if (k === "lang") return primaryLang(r);
      if (k === "viewed_word") return r.viewed_word ? 1 : 0;
      if (k === "tried_audio") return r.tried_audio ? 1 : 0;
      if (k === "shot_tapped" || k === "video_played" || k === "hero_played") {
        return r[k] ? 1 : 0;
      }
      if (k === "cta") return (r.cta_signup ? 1 : 0) + (r.cta_try ? 1 : 0);
      return r[k];
    };
    rows.sort((a, b) => {
      const x = val(a, anonSort.key), y = val(b, anonSort.key);
      let c;
      if (typeof x === "number" && typeof y === "number") c = x - y;
      else c = String(x ?? "").localeCompare(String(y ?? ""), "ja");
      return anonSort.asc ? c : -c;
    });
    const COLS = [
      ["ip", "IP"], ["place", "国/地域/市区"], ["org", "接続元組織・ホスト名"],
      ["device", "端末"], ["browser", "ブラウザ"], ["lang", "言語設定"],
      ["first_seen", "初回"], ["last_seen", "最終"], ["visit_count", "回数"],
      ["viewed_word", "単語ページ閲覧"], ["tried_audio", "音声再生"],
      // ようこそ画面の操作(2026-09-22): 目玉サムネイルを押したか・動画を再生したか・
      // 1語サンプルを再生したか・登録/体験ボタンを押したか。
      ["shot_tapped", "サムネ押下"], ["video_played", "動画再生"],
      ["hero_played", "1語聞いた"], ["cta", "登録・体験ボタン"],
      ["viewed_about", "説明書閲覧"], ["signup", "登録試行"],
    ];
    // 列幅(2026-09-22・オーナー要望「接続元組織・端末・ブラウザは6文字幅・IPは8文字幅で
    // 折り返して、表全体が見えるように」): 折り返し前提の固定幅。
    const NARROW = {
      ip: "anon-w-ip", org: "anon-w6", device: "anon-w6", browser: "anon-w6",
    };
    const head = COLS.map(([k, label]) => {
      const arrow = anonSort.key === k ? (anonSort.asc ? " ▲" : " ▼") : "";
      return `<th class="anon-sort ${NARROW[k] || ""}" data-key="${k}"
        style="cursor:pointer;user-select:none"
        title="クリックで並べ替え">${label}${arrow}</th>`;
    }).join("");
    wrap.innerHTML = `<p class="muted">表示中 ${rows.length} 件
      / 期間内 ${(anonData.items || []).length} 件</p>
      <table><thead><tr>${head}</tr></thead><tbody>${rows.map((r) => `
      <tr>
        <td class="muted anon-w-ip">${escapeHtml(r.ip)}${
          r.mark
            ? ` <sup title="${escapeHtml(ANON_MARKS[r.mark])}: ${
              escapeHtml(r.mark_reason || "")}">※${r.mark}</sup>` : ""}</td>
        <td class="muted">${escapeHtml(place(r))}</td>
        <td class="muted anon-w6">${escapeHtml(r.org || r.hostname || "—")}</td>
        <td class="muted anon-w6">${escapeHtml(r.device || "—")}</td>
        <td class="muted anon-w6">${escapeHtml(r.browser || "—")}</td>
        <td class="muted" title="${escapeHtml(r.accept_language || "")}">
          ${escapeHtml(primaryLang(r) || "—")}</td>
        <td class="muted">${fmtDate(r.first_seen)}</td>
        <td class="muted">${fmtDate(r.last_seen)}</td>
        <td>${r.visit_count}</td>
        <td>${r.viewed_word
          ? '<span class="badge-ok">見た</span>' : "—"}</td>
        <td>${r.tried_audio
          ? '<span class="badge-ok">再生した</span>' : "—"}</td>
        <td>${r.shot_tapped
          ? '<span class="badge-ok">押した</span>' : "—"}</td>
        <td>${r.video_played
          ? '<span class="badge-ok">再生した</span>' : "—"}</td>
        <td>${r.hero_played
          ? '<span class="badge-ok">聞いた</span>' : "—"}</td>
        <td>${[r.cta_signup ? "登録" : "", r.cta_try ? "体験" : ""]
          .filter(Boolean).map((t) => `<span class="badge-ok">${t}</span>`)
          .join(" ") || "—"}</td>
        <td>${r.viewed_about
          ? '<span class="badge-ok">見た</span>' : "—"}</td>
        <td>${r.signup_attempted
          ? (r.signup_succeeded
            ? '<span class="badge-ok">成功</span>'
            : '<span class="badge-bad">試行(未成立)</span>')
          : "—"}</td>
      </tr>`).join("")}</tbody></table>
      <p class="muted" style="font-size:.9em">判定材料はUser-Agentと接続元組織
      だけなので確実ではありません。UAは詐称できますし、VPN経由の人間が
      ※4になることもあります。「印なし＝機械的アクセスの兆候が
      見つからなかった」という意味で読んでください。各印にマウスを乗せると
      判定理由が出ます。端末・ブラウザもUAからの推定で、iPadOSのSafariは
      既定でMacと同じ名乗り方をするため区別できません。同一IPに複数
      端末/ブラウザが混ざる場合は「/」区切りで並べて表示します。</p>`;
    wrap.querySelectorAll(".anon-sort").forEach((th) => {
      th.addEventListener("click", () => {
        const k = th.dataset.key;
        if (anonSort.key === k) anonSort.asc = !anonSort.asc;
        else anonSort = { key: k, asc: k === "ip" || k === "org" };
        renderAnonRows();
      });
    });
  }

  async function loadAnonAccess() {
    const sumBox = root.querySelector("#anonAccessSummary");
    const wrap = root.querySelector("#anonAccessWrap");
    sumBox.innerHTML = `<p class="muted">読み込み中…</p>`;
    wrap.innerHTML = "";
    const days = root.querySelector("#anonAccessDays").value;
    const limit = root.querySelector("#anonAccessLimit").value;
    try {
      const res = await api.get(
        `/api/system/admin/anon-access?days=${days}&limit=${limit}`);
      anonData = res;
      const mc = res.mark_counts || {};
      const mv = res.mark_visits || {};
      // 総数は**先頭に固定**で出す（下の絞り込みや並べ替えの影響を受けない・
      // 2026-08-22ユーザー要望）。IP数と延べ回数の両方を出す。
      const cell = (n) => `<td>${mc[n] || 0} IP</td><td>${mv[n] || 0} 回</td>`;
      sumBox.innerHTML = `
        <p><strong>直近${res.days}日の合計:
          延べアクセス ${res.total_visits} 回 ／
          IP総数 ${res.unique_ips} 件</strong></p>
        <table><thead><tr><th>種別</th><th>IP数</th><th>延べ回数</th></tr>
        </thead><tbody>
          <tr><td>👤 人間のアクセス（管理者を除く・印なし）</td>${cell(0)}</tr>
          <tr><td class="muted">※1 管理者自身</td>${cell(1)}</tr>
          <tr><td>🤖 ※2 機械クローラー</td>${cell(2)}</tr>
          <tr><td>🧠 ※3 AIクローラー</td>${cell(3)}</tr>
          <tr><td>❓ ※4 その他（人間の普通のアクセスではないもの）</td>
            ${cell(4)}</tr>
        </tbody></table>`;
      renderAnonRows();
    } catch (e) {
      anonData = null;
      sumBox.innerHTML =
        `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
    }
  }
  root.querySelector("#anonAccessReload")
    .addEventListener("click", loadAnonAccess);
  root.querySelector("#anonAccessDays")
    .addEventListener("change", loadAnonAccess);
  root.querySelector("#anonAccessLimit")
    .addEventListener("change", loadAnonAccess);
  root.querySelectorAll(".anon-mark").forEach((c) =>
    c.addEventListener("change", renderAnonRows));

  // --- 登録に至らない原因分析(常設・2026-08-30) ------------------------
  async function loadRegFunnelGuestDetail(gsid, wrapEl) {
    wrapEl.innerHTML = `<p class="muted">読み込み中…</p>`;
    try {
      const res = await api.get(
        `/api/system/admin/registration-funnel/guest/${encodeURIComponent(gsid)}`);
      const rows = res.timeline.map((t) => `<tr>
        <td class="muted">${fmtDate(t.created_at)}</td>
        <td class="muted">${escapeHtml(t.src)}</td>
        <td>${escapeHtml(t.kind || "")}</td>
        <td>${escapeHtml(t.path || t.category || "")}</td>
        <td>${escapeHtml(t.desc || "")}</td>
        <td class="muted">${escapeHtml(t.label || "")}${
          t.value != null ? ` ${Math.round(t.value)}ms` : ""}${
          t.success != null ? `成否:${t.success ? "成功" : "失敗"}` : ""}${
          t.referrer_host ? ` ref:${escapeHtml(t.referrer_host)}` : ""}${
          t.utm_source ? ` utm:${escapeHtml(
            [t.utm_source, t.utm_medium, t.utm_campaign]
              .filter(Boolean).join("/"))}` : ""}${
          t.has_gclid ? " 広告クリック" : ""}${
          t.is_internal ? " (自分の端末)" : ""}${
          t.user_id ? ` user#${t.user_id}` : ""}</td>
      </tr>`).join("");
      wrapEl.innerHTML = rows
        ? `<table><thead><tr>
            <th>日時</th><th>種別</th><th>kind</th><th>画面/分野</th><th>内容</th><th>備考</th>
          </tr></thead><tbody>${rows}</tbody></table>`
        : `<p class="muted">行動ログがありません。</p>`;
    } catch (e) {
      wrapEl.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
    }
  }
  async function loadRegFunnel() {
    const wrap = root.querySelector("#regFunnelWrap");
    wrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    const days = root.querySelector("#regFunnelDays").value;
    try {
      const res = await api.get(
        `/api/system/admin/registration-funnel?days=${days}`);
      const stages = res.stages || [];
      if (!stages[0] || !stages[0].count) {
        wrap.innerHTML = `<p class="muted">この期間はまだデータが
          ありません(このCookieの導入後から集計されます)。</p>`;
        return;
      }
      const tilesHtml = `<div class="grid cols-4 mt">${stages.map((s) => `
        <div class="stat"><div class="num">${s.count}</div>
          <div class="lbl">${escapeHtml(s.label)}</div></div>`).join("")}
      </div>`;
      const barsHtml = stages.map((s) => `
        <div class="row mt" style="align-items:center; gap:8px">
          <span class="muted" style="width:200px; font-size:12px">
            ${escapeHtml(s.label)}</span>
          <div style="flex:1; background:var(--panel-2); border-radius:4px;
            overflow:hidden; height:14px">
            <div style="width:${s.rate_from_start}%; background:var(--accent);
              height:100%"></div>
          </div>
          <span class="muted" style="width:120px; font-size:12px">
            ${s.rate_from_start}%（前段階比${s.rate_from_prev}%）</span>
        </div>`).join("");
      const botExcluded = res.bot_excluded || 0;
      const internalExcluded = res.internal_excluded || 0;
      // --- JS到達・人間訪問・流入元別内訳(2026-09-19・計測設計3-A/3-B/3-D) ---
      const pct = (n, d) => (d ? `${(n / d * 100).toFixed(1)}%` : "—");
      const ms = (v) => (v == null ? "—" : `${Math.round(v).toLocaleString()}ms`);
      const jt = res.js_timing || {};
      const visitedN = stages[0].count;
      const jsKpiHtml = `
        <h3 class="mt">JS到達・人間訪問（「91%が無操作」の内訳を分解する指標）</h3>
        <div class="grid cols-4 mt">
          <div class="stat"><div class="num">${res.human_visited ?? 0}</div>
            <div class="lbl">人間訪問(基準)<br><span class="muted">JS到達 or
              2回以上閲覧</span></div></div>
          <div class="stat"><div class="num">${pct(res.js_reached ?? 0, visitedN)}</div>
            <div class="lbl">JS到達率<br><span class="muted">${res.js_reached ?? 0}/${visitedN}</span></div></div>
          <div class="stat"><div class="num">${pct(res.app_ready ?? 0, visitedN)}</div>
            <div class="lbl">初期表示完了率<br><span class="muted">${res.app_ready ?? 0}/${visitedN}</span></div></div>
          <div class="stat"><div class="num">${ms(jt.ready_ms_median)}</div>
            <div class="lbl">初期表示までの中央値<br><span class="muted">90%点
              ${ms(jt.ready_ms_p90)}</span></div></div>
        </div>
        <p class="muted" style="font-size:12px">
          HTMLは届いたがJSが動かなかった/表示前に離脱した訪問は「訪問」と
          「JS到達」の差です。JS到達の記録は計測開始後のデータのみ(それ以前の
          期間は0になり、JS到達率・人間訪問は低く出ます)。HTML到達までの
          中央値 ${ms(jt.html_ms_median)}。</p>`;
      // --- トップページでの行動・滞在時間(2026-09-21・ユーザー要望) ---
      const tb = res.top_behavior || {};
      const tbVideo = tb.video || {};
      const tbOther = tb.other_page || {};
      const tbDwell = tb.dwell || {};
      const jsN = res.js_reached ?? 0;
      const secFmt = (x) => {
        if (x == null) return "—";
        if (x < 60) return `${x}秒`;
        const t = Math.round(x);   // 先に丸める(119.6秒が「1分60秒」にならないように)
        return `${Math.floor(t / 60)}分${t % 60}秒`;
      };
      const tbTile = (n, title, hint) => `
        <div class="stat"><div class="num">${n ?? 0}</div>
          <div class="lbl">${title}<br><span class="muted">${
            jsN ? `JS到達${jsN}人中 ${pct(n ?? 0, jsN)}` : hint}</span></div>
        </div>`;
      const videoRows = (tbVideo.by_video || []).map((r) => `<tr>
        <td>${escapeHtml(r.title)}</td><td>${r.play}</td><td>${r.p25}</td>
        <td>${r.p50}</td><td>${r.p75 ?? 0}</td><td>${r.ended}</td>
        <td>${r.pause ?? 0}</td><td>${r.try}</td>
        <td>${r.replay}</td><td>${r.error}</td></tr>`).join("");
      const pageRows = (tbOther.by_page || []).map((r) => `<tr>
        <td>${escapeHtml(r.label)}</td><td>${r.count}</td></tr>`).join("");
      const dwellRow = (label, d) => `<tr><td>${label}</td><td>${d.n}</td>
        <td>${secFmt(d.min)}</td><td>${secFmt(d.p25)}</td>
        <td><b>${secFmt(d.median)}</b></td><td>${secFmt(d.mean)}</td>
        <td>${secFmt(d.p75)}</td><td>${secFmt(d.p90)}</td>
        <td>${secFmt(d.max)}</td></tr>`;
      // --- ようこそ画面から次へ進まない原因の分析(2026-09-22) ---
      const jr = tb.journey || {};
      const jrSteps = jr.steps || [];
      const jrRecorded = !!jr.seen_recorded;
      const barCell = (rate) => `<td style="min-width:90px">
        <div style="background:var(--panel-2); border-radius:3px; height:8px;
          overflow:hidden"><div style="width:${Math.min(100, rate || 0)}%;
          background:var(--accent); height:100%"></div></div></td>`;
      const stepRows = jrSteps.map((st) => `<tr>
        <td>${escapeHtml(st.label)}</td><td>${st.count}</td>
        <td class="muted">${st.rate}%</td>${barCell(st.rate)}</tr>`).join("");
      const cohortRows = (jr.cohorts || []).map((c) => `<tr>
        <td>${escapeHtml(c.label)}</td><td>${c.n}</td><td>${c.advanced}</td>
        <td><b>${c.rate == null ? "—" : c.rate + "%"}</b></td></tr>`).join("");
      const dh = tb.dwell_hist || { labels: [], engaged: [], not_engaged: [] };
      const dhSum = (a) => a.reduce((x, y) => x + y, 0);
      const dhCell = (a, i) => {
        const t = dhSum(a);
        return `<td>${a[i] ?? 0}<span class="muted"> (${
          t ? Math.round((a[i] ?? 0) / t * 100) : 0}%)</span></td>`;
      };
      const dhRows = [["操作せず離れた", dh.not_engaged],
        ["何か操作した", dh.engaged]].map(([lbl, a]) => `<tr>
        <td>${lbl}<span class="muted"> (${dhSum(a)}件)</span></td>${
          (dh.labels || []).map((_, i) => dhCell(a, i)).join("")}</tr>`)
        .join("");
      const devRows = (tb.by_device || []).map((d) => `<tr>
        <td>${escapeHtml(d.device)} / ${escapeHtml(d.browser)}</td>
        <td>${d.viewed}</td><td>${d.advanced}</td>
        <td>${d.leave_n ? `${d.quick_leave}/${d.leave_n}` : "—"}</td>
        <td>${secFmt(d.first_leave_median_s)}</td></tr>`).join("");
      const themeRows = (tb.by_theme || []).map((t) => `<tr>
        <td>${t.os === "dark" ? "ダーク" : "ライト"}</td>
        <td>${t.shown === "dark" ? "ダーク" : "ライト"}${
          t.os !== t.shown ? ' <span class="muted">(OSと不一致)</span>' : ""}</td>
        <td>${t.n}</td><td>${t.advanced}</td>
        <td>${secFmt(t.first_leave_median_s)}</td></tr>`).join("");
      const journeyHtml = `
        <h3 class="mt">ようこそ画面から次へ進まない原因の分析</h3>
        <p class="muted" style="font-size:12px">${[
          "母数=ようこそ画面を表示した人(ボット・自分の端末を除く)。",
          "「画面に入った」「スクロール」「最後まで」の記録は ver1.4.14 の公開以降のデータのみです",
          "(それ以前の期間は0になります)。「次の画面へ進んだ」は、無料登録/登録せず単語を見る/",
          "動画の「試す」を押した、または別の画面(このアプリについて・ログイン/登録ページ・各機能)を開いた人です。"
        ].join("")}</p>
        ${jr.viewed
          ? `<p class="muted" style="font-size:12px">ようこそ画面を見た人 ${jr.viewed}人
              (うちスマホ/タブレット ${jr.mobile}人)</p>
            ${jrRecorded ? "" : `<p class="muted" style="font-size:12px">
              この期間には「画面に入った・スクロール」の記録がまだありません。</p>`}
            <div style="overflow-x:auto"><table class="mt"><thead><tr>
              <th>段階</th><th>人数</th><th>表示した人比</th><th></th></tr></thead>
              <tbody>${stepRows}</tbody></table></div>
            <h3 class="mt" style="font-size:14px">どの行動をした人が次へ進んだか</h3>
            <div style="overflow-x:auto"><table class="mt"><thead><tr>
              <th>行動</th><th>人数</th><th>次の画面へ進んだ</th><th>進んだ割合</th>
              </tr></thead><tbody>${cohortRows}</tbody></table></div>
            <h3 class="mt" style="font-size:14px">最初に画面を離れるまでの時間の分布（読み込み回数）</h3>
            <div style="overflow-x:auto"><table class="mt"><thead><tr><th></th>${
              (dh.labels || []).map((l) => `<th>${l}</th>`).join("")}</tr></thead>
              <tbody>${dhRows}</tbody></table></div>
            <h3 class="mt" style="font-size:14px">端末/ブラウザ別（上位）</h3>
            <div style="overflow-x:auto"><table class="mt"><thead><tr>
              <th>端末 / ブラウザ</th><th>人数</th><th>次へ進んだ</th>
              <th>5秒未満で離れた</th><th>離れるまでの中央値</th></tr></thead>
              <tbody>${devRows}</tbody></table></div>
            ${themeRows
              ? `<h3 class="mt" style="font-size:14px">OSの配色設定と表示したテーマ別（初期テーマの判断材料）</h3>
                <div style="overflow-x:auto"><table class="mt"><thead><tr>
                  <th>OSの設定</th><th>表示したテーマ</th><th>人数</th>
                  <th>次へ進んだ</th><th>離れるまでの中央値</th></tr></thead>
                  <tbody>${themeRows}</tbody></table></div>` : ""}`
          : `<p class="muted">この期間にようこそ画面を表示した記録はありません。</p>`}`;
      const behaviorHtml = `${journeyHtml}
        <h3 class="mt">トップページでの行動・離脱までの時間</h3>
        <div class="grid cols-4 mt">
          ${tbTile(tbVideo.played, "動画を再生した人", "")}
          ${tbTile(tbOther.opened, "別の画面を開いた人", "")}
          ${tbTile(tb.try_without_signup, "「登録せず単語を見る」を押した人", "")}
          ${tbTile(tb.signup_cta, "「無料登録」ボタンを押した人", "")}
        </div>
        <p class="muted" style="font-size:12px">${[
          "人数は訪問した人(ボット・自分の端末を除く)のユニーク数です。",
          "動画・上記ボタンの記録は ver1.4.12 の公開(2026-09-21)以降のデータのみ、",
          "離脱までの時間は2026-09-19以降のみで、それ以前の期間は0になります。",
          "「別の画面」はようこそ画面以外(このアプリについて・ログイン/登録ページ・",
          "各機能の画面)の表示です。"].join("")}</p>
        ${videoRows
          ? `<h3 class="mt">動画別（何を見たか・人数）</h3>
            <div style="overflow-x:auto"><table class="mt"
              style="min-width:680px"><thead><tr>
              <th>動画</th><th>再生を押した</th><th>25%まで</th>
              <th>50%まで</th><th>75%まで</th><th>最後まで</th>
              <th>途中で止めた</th><th>「試す」を押した</th>
              <th>もう一度見た</th><th>再生エラー</th></tr></thead>
              <tbody>${videoRows}</tbody></table></div>`
          : `<p class="muted">この期間に動画を再生した人はいません。</p>`}
        ${pageRows
          ? `<details class="mt"><summary>開いた別の画面（人数・上位）</summary>
              <table class="mt"><thead><tr><th>画面</th><th>人数</th></tr>
              </thead><tbody>${pageRows}</tbody></table></details>` : ""}
        <h3 class="mt">離脱までの推定時間（秒・ページを開いてからの滞在）</h3>
        <div style="overflow-x:auto"><table class="mt"
          style="min-width:560px"><thead><tr>
          <th></th><th>件数</th><th>最小</th><th>25%点</th><th>中央値</th>
          <th>平均</th><th>75%点</th><th>90%点</th><th>最大</th></tr></thead>
          <tbody>${dwellRow("全体", tbDwell.all || { n: 0 })}
          ${dwellRow("何か操作した人", tbDwell.engaged || { n: 0 })}
          ${dwellRow("操作せず離れた人", tbDwell.not_engaged || { n: 0 })}
          </tbody></table></div>
        <p class="muted" style="font-size:12px">${[
          "「離脱」=ページを開いてから最初に画面を離れた(別のタブ/アプリへ切り替える・",
          "閉じる)時点までの経過時間の推定で、ページを開いた1回につき1件です",
          "(人数ではなく読み込み回数)。切り替えて戻る人もいるため実際の利用時間とは",
          "一致しません。タブを開いたまま放置すると最大値・平均が極端に長くなるので、",
          "目安は<b>中央値</b>です。"].join("")}</p>`;
      const chRows = (res.by_channel || []).map((c) => `<tr>
        <td>${escapeHtml(c.label)}</td><td>${c.visited}</td>
        <td>${c.human}</td>
        <td>${c.js_reached}<span class="muted"> (${pct(c.js_reached, c.visited)})</span></td>
        <td>${c.engaged}<span class="muted"> (${pct(c.engaged, c.visited)})</span></td>
        <td>${c.signup_attempted}</td><td>${c.signup_succeeded}</td>
      </tr>`).join("");
      const lpRows = (res.by_landing || []).map((c) => `<tr>
        <td>${escapeHtml(c.label)}</td><td>${c.visited}</td>
        <td>${c.js_reached}</td><td>${c.engaged}</td>
        <td>${c.signup_succeeded}</td>
      </tr>`).join("");
      const refRows = (res.top_referrers || []).map((r) => `<tr>
        <td>${escapeHtml(r.host)}</td><td>${r.count}</td></tr>`).join("");
      const utmRows = (res.utm_breakdown || []).map((r) => `<tr>
        <td>${escapeHtml(r.label)}</td><td>${r.count}</td></tr>`).join("");
      const seo = res.via_seo || {};
      const sourceHtml = `
        <h3 class="mt">流入元別の内訳（チャネル×人数・初回の訪問が基準）</h3>
        <p class="muted" style="font-size:12px">
          チャネル: 広告=広告クリックID(gclid等)付き/utm_medium=cpc、
          生成AI=chatgpt.com等のreferrer、検索・SNS/記事=referrerホスト、
          サイト内遷移=自ドメインのreferrer。referrerはホスト名のみ、広告
          クリックIDは「付いていたか」だけを保存しています(値は保存
          しません)。「流入元不明」は計測開始前の訪問です。
          操作あり=ボタン押下・再生・ようこそ以外の画面遷移のいずれか。</p>
        ${chRows
          ? `<div style="overflow-x:auto"><table class="mt"><thead><tr>
              <th>チャネル</th><th>訪問</th><th>人間訪問</th><th>JS到達</th>
              <th>操作あり</th><th>登録試行</th><th>登録完了</th>
              </tr></thead><tbody>${chRows}</tbody></table></div>`
          : `<p class="muted">この期間の訪問はありません。</p>`}
        <p class="muted" style="font-size:12px">
          広告(gclid)付きの訪問者: ${res.ad_click_visitors ?? 0}人 /
          SEOページ(用語集・フレーズ集・クロスワード紹介)に着地:
          ${seo.seo_landed ?? 0}人のうちアプリ等へも遷移: ${seo.seo_then_app ?? 0}人</p>
        ${lpRows
          ? `<h3 class="mt">着地ページ別</h3>
            <table class="mt"><thead><tr><th>着地ページ</th><th>訪問</th>
              <th>JS到達</th><th>操作あり</th><th>登録完了</th></tr></thead>
              <tbody>${lpRows}</tbody></table>` : ""}
        ${refRows
          ? `<details class="mt"><summary>参照元ホスト上位（初回訪問）</summary>
              <table class="mt"><thead><tr><th>ホスト</th><th>人数</th></tr>
              </thead><tbody>${refRows}</tbody></table></details>` : ""}
        ${utmRows
          ? `<details class="mt"><summary>utmパラメータ別（source / medium /
              campaign）</summary><table class="mt"><thead><tr>
              <th>utm</th><th>人数</th></tr></thead><tbody>${utmRows}</tbody>
              </table></details>` : ""}`;
      // --- 登録フォーム内の欄別の到達/離脱(2026-09-20・計測設計3-E) ---
      const sf = res.signup_form || {};
      const sfOpened = sf.opened || 0;
      const sfStallTotal = (sf.stalled || [])
        .reduce((a, b) => a + b.count, 0);
      const sfStepRows = (sf.steps || []).map((st) => {
        const showRate = st.key !== "opened" && st.key !== "success";
        const w = sfOpened && showRate
          ? Math.min(100, st.count / sfOpened * 100) : 0;
        return `<tr>
          <td>${escapeHtml(st.label)}</td><td>${st.count}</td>
          <td class="muted">${showRate ? pct(st.count, sfOpened) : ""}</td>
          <td style="min-width:90px"><div style="background:var(--panel-2);
            border-radius:3px; height:8px; overflow:hidden">
            <div style="width:${w}%; background:var(--accent); height:100%">
            </div></div></td></tr>`;
      }).join("");
      const sfStallRows = (sf.stalled || []).map((st) => `<tr>
        <td>${escapeHtml(st.label)}</td><td>${st.count}</td>
        <td class="muted">${pct(st.count, sfStallTotal)}</td></tr>`).join("");
      const sfErrRows = (sf.errors || []).map((er) => `<tr>
        <td>${escapeHtml(er.name)}</td>
        <td class="muted">${escapeHtml(er.label)}</td>
        <td>${er.count}</td></tr>`).join("");
      const formHtml = `
        <h3 class="mt">登録フォーム内の欄別の到達・離脱（2026-09-20〜記録）</h3>
        <p class="muted" style="font-size:12px">
          登録フォームを開いた人が、どの欄までふれたか/入力を始めたか、どこで
          止まったか。記録しているのは欄の名前と「ふれた・入力を始めた・送信
          した・エラーになった」の種類だけで、入力した内容・文字数・
          メールアドレス等は取得していません。記録開始前に登録した人は
          各段階に入りません(「登録完了(全体)」は期間内の実数)。</p>
        ${sfOpened
          ? `<div style="overflow-x:auto"><table class="mt"><thead><tr>
              <th>段階</th><th>人数</th><th>開いた人比</th><th></th></tr></thead>
              <tbody>${sfStepRows}</tbody></table></div>
            <h3 class="mt" style="font-size:14px">登録に至らなかった人が
              最後に到達していた所</h3>
            <div style="overflow-x:auto"><table class="mt"><thead><tr>
              <th>最後に到達</th><th>人数</th><th>割合</th></tr></thead>
              <tbody>${sfStallRows}</tbody></table></div>
            ${sfErrRows
              ? `<h3 class="mt" style="font-size:14px">入力エラー・登録拒否
                  （人数・重複あり）</h3>
                <div style="overflow-x:auto"><table class="mt"><thead><tr>
                  <th>内容</th><th>記録名</th><th>人数</th></tr></thead>
                  <tbody>${sfErrRows}</tbody></table></div>`
              : ""}`
          : `<p class="muted">この期間にフォームを開いた記録はまだありません
              (この計測を含むバージョンの本番反映後から溜まります)。</p>`}`;
      const deviceBreakdown = res.device_breakdown || [];
      const deviceRows = deviceBreakdown.map((d) => `<tr>
        <td>${escapeHtml(d.device)}</td><td>${escapeHtml(d.browser)}</td>
        <td>${d.count}</td>
      </tr>`).join("");
      const failReasons = res.fail_reasons || [];
      const failReasonRows = failReasons.map((f) => `<tr>
        <td>${escapeHtml(f.label)}</td>
        <td class="muted">${escapeHtml(f.code)}</td>
        <td>${f.count}</td>
      </tr>`).join("");
      const dispo = res.disposable_email_stats || {};
      const dropoffSummary = res.dropoff_summary || [];
      const summaryRows = dropoffSummary.map((d) => `<tr>
        <td>${escapeHtml(d.category)}</td><td>${d.count}</td>
      </tr>`).join("");
      const sessions = res.dropoff_sessions || [];
      const sessionRows = sessions.map((s) => `
        <tr class="reg-funnel-session" data-gsid="${escapeHtml(s.guest_sid)}"
          style="cursor:pointer">
          <td class="muted">${fmtDate(s.created_at)}</td>
          <td>${escapeHtml(s.category || "(不明)")}</td>
          <td class="muted">詳細 ▸</td>
        </tr>
        <tr class="reg-funnel-detail" data-gsid="${escapeHtml(s.guest_sid)}"
          hidden>
          <td colspan="3"><div class="reg-funnel-detail-wrap muted">
            未読み込み</div></td>
        </tr>`).join("");
      wrap.innerHTML = `${tilesHtml}${barsHtml}
        <p class="muted mt" style="font-size:12px">
          ⚙️ ボット・クローラー(curl等の機械的アクセス)と判定した
          ${botExcluded}件、自分の端末(管理者/テストアカウント・内部Cookie)
          ${internalExcluded}件は上記の集計から除外済みです。</p>
        ${jsKpiHtml}${behaviorHtml}${sourceHtml}
        <h3 class="mt">端末・ブラウザの内訳（「訪問」段階・人間判定分のみ）</h3>
        ${deviceBreakdown.length
          ? `<table class="mt"><thead><tr>
              <th>端末</th><th>ブラウザ</th><th>人数</th>
              </tr></thead><tbody>${deviceRows}</tbody></table>`
          : `<p class="muted">対象者がいません。</p>`}

        ${formHtml}

        <h3 class="mt">登録試行の失敗理由内訳（多角的分析用・2026-09-07〜
          記録開始）</h3>
        <p class="muted" style="font-size:12px">
          使い捨てメールは2026-09-07〜ブロックせず許可制に変更（弊害の
          方が大きいと判断）。参考として使用件数を記録: 使い捨てメールで
          登録成功 ${dispo.succeeded ?? 0}件・使い捨てメールで
          （別の理由により）失敗 ${dispo.failed_other_reason ?? 0}件。</p>
        ${failReasons.length
          ? `<table class="mt"><thead><tr>
              <th>理由</th><th>コード</th><th>件数</th>
              </tr></thead><tbody>${failReasonRows}</tbody></table>`
          : `<p class="muted">この期間の登録失敗はありません
              （2026-09-07より前のデータは対象外です）。</p>`}

        <h3 class="mt">離脱ポイント（訪問したが登録を試みなかった人が
          最後に見ていた画面）</h3>
        ${dropoffSummary.length
          ? `<table class="mt"><thead><tr><th>画面/分野</th><th>人数</th>
              </tr></thead><tbody>${summaryRows}</tbody></table>`
          : `<p class="muted">対象者がいません。</p>`}
        <details class="mt"><summary>📋 個別セッション一覧
          （クリックで行動ログを表示・最大${sessions.length}件）</summary>
          <table class="mt"><thead><tr>
            <th>最終確認</th><th>画面/分野</th><th></th>
          </tr></thead><tbody>${sessionRows}</tbody></table>
        </details>`;
      wrap.querySelectorAll(".reg-funnel-session").forEach((tr) => {
        tr.addEventListener("click", () => {
          const gsid = tr.dataset.gsid;
          const detailTr = wrap.querySelector(
            `.reg-funnel-detail[data-gsid="${CSS.escape(gsid)}"]`);
          const nowHidden = detailTr.hidden;
          detailTr.hidden = !nowHidden;
          if (nowHidden) {
            const inner = detailTr.querySelector(".reg-funnel-detail-wrap");
            if (inner.dataset.loaded !== "1") {
              inner.dataset.loaded = "1";
              loadRegFunnelGuestDetail(gsid, inner);
            }
          }
        });
      });
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
    }
  }
  root.querySelector("#regFunnelReload")
    .addEventListener("click", loadRegFunnel);
  root.querySelector("#regFunnelDays")
    .addEventListener("change", loadRegFunnel);

  async function loadRegistrants() {
    const wrap = root.querySelector("#registrantsWrap");
    wrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    try {
      const res = await api.get(
        `/api/system/admin/registrants?${adminAggQuery()}`);
      const items = res.items || [];
      if (!items.length) {
        wrap.innerHTML = `<p class="muted">登録者がいません。</p>`;
        return;
      }
      const cell = (s) => s ? escapeHtml(s) : "—";
      const rows = items.map((u) => `<tr>
        <td class="muted">${fmtDate(u.created_at)}</td>
        <td>${escapeHtml(u.display_name || "")}<br>
          <span class="muted">${escapeHtml(u.email || u.username)}</span></td>
        <td>${cell(u.survey_occupation_category)}${
          u.survey_occupation_detail
            ? `<br><span class="muted">${escapeHtml(u.survey_occupation_detail)}</span>`
            : ""}</td>
        <td>${cell(u.survey_age_group)}</td>
        <td>${cell(u.survey_gender)}</td>
        <td>${cell(u.survey_purpose)}</td>
        <td>${cell(u.survey_referral)}</td>
        <td>${cell(u.survey_interest_areas)}</td>
        <td>${cell(u.survey_free_text)}</td>
      </tr>`).join("");
      wrap.innerHTML = `<div style="overflow-x:auto"><table><thead><tr>
          <th>登録日時</th><th>担当者/メール</th><th>職業</th><th>年代</th>
          <th>性別</th><th>目的</th><th>きっかけ</th><th>興味分野</th>
          <th>自由記述</th>
        </tr></thead><tbody>${rows}</tbody></table></div>`;
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
    }
  }
  root.querySelector("#registrantsReload")
    .addEventListener("click", loadRegistrants);

  async function loadSurveySummary() {
    const wrap = root.querySelector("#surveySummaryWrap");
    wrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    try {
      const res = await api.get(
        `/api/system/admin/survey-summary?${adminAggQuery()}`);
      const barTable = (title, items) => {
        if (!items.length) {
          return `<h3 class="mt">${title}</h3>
            <p class="muted">データがありません。</p>`;
        }
        const max = Math.max(...items.map((i) => i.count));
        const rows = items.map((i) => `
          <div class="row mt" style="align-items:center; gap:8px">
            <span class="muted" style="width:160px; font-size:12px">
              ${escapeHtml(i.label)}</span>
            <div style="flex:1; background:var(--panel-2); border-radius:4px;
              overflow:hidden; height:14px">
              <div style="width:${max ? Math.round(i.count / max * 100) : 0}%;
                background:var(--accent); height:100%"></div>
            </div>
            <span class="muted" style="width:40px; font-size:12px">
              ${i.count}</span>
          </div>`).join("");
        return `<h3 class="mt">${title}</h3>${rows}`;
      };
      const freeText = res.free_text || [];
      const freeTextHtml = freeText.length
        ? `<table class="mt"><thead><tr><th>担当者</th><th>内容</th>
            </tr></thead><tbody>${freeText.map((f) => `<tr>
              <td>${escapeHtml(f.display_name || "")}</td>
              <td>${escapeHtml(f.text)}</td></tr>`).join("")}
          </tbody></table>`
        : `<p class="muted">自由記述の回答はありません。</p>`;
      wrap.innerHTML = `
        <div class="grid cols-4">
          <div class="stat"><div class="num">${res.total}</div>
            <div class="lbl">対象ユーザー数</div></div>
          <div class="stat"><div class="num">${res.answered}</div>
            <div class="lbl">アンケート回答あり</div></div>
        </div>
        ${barTable("職業分類", res.occupation_category)}
        ${barTable("職業詳細", res.occupation_detail)}
        ${barTable("年代", res.age_group)}
        ${barTable("性別", res.gender)}
        ${barTable("利用目的", res.purpose)}
        ${barTable("きっかけ", res.referral)}
        ${barTable("興味分野", res.interest_areas)}
        <h3 class="mt">自由記述</h3>
        ${freeTextHtml}`;
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
    }
  }
  root.querySelector("#surveySummaryReload")
    .addEventListener("click", loadSurveySummary);

  async function loadChargeKeyLog() {
    const wrap = root.querySelector("#chargeKeyLogWrap");
    wrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    try {
      const rows = await api.get(
        `/api/system/admin/charge-key-log?${adminAggQuery()}`);
      if (!rows.length) {
        wrap.innerHTML = `<p class="muted">まだありません。</p>`;
        return;
      }
      const RESULT_LABEL = {
        redeemed: '<span class="badge-ok">チャージ成功</span>',
        used: '<span class="badge-bad">使用済み(再利用試行)</span>',
        invalid: '<span class="badge-bad">無効なキー</span>',
      };
      wrap.innerHTML = `<table><thead><tr>
        <th>日時(JST)</th><th>ユーザー</th><th>結果</th><th>キー番号</th>
        </tr></thead><tbody>${rows.map((r) => `
        <tr>
          <td class="muted">${fmtDate(r.created_at)}</td>
          <td>${escapeHtml(r.username || "—")}</td>
          <td>${RESULT_LABEL[r.result] || escapeHtml(r.result)}</td>
          <td class="muted">${escapeHtml(
            r.charge_key_public_id
              ? r.charge_key_public_id + "…"
              : (r.key_id_hash ? r.key_id_hash.slice(0, 12) + "…" : "—"))}
          </td>
        </tr>`).join("")}</tbody></table>`;
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
    }
  }

  async function loadWithdrawalLog() {
    const wrap = root.querySelector("#withdrawalLogWrap");
    wrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    try {
      const res = await api.get("/api/auth/withdrawals");
      const rows = res.withdrawals || [];
      const labels = res.reason_labels || {};
      if (!rows.length) {
        wrap.innerHTML = `<p class="muted">まだありません。</p>`;
        return;
      }
      wrap.innerHTML = `<table><thead><tr>
        <th>日時(JST)</th><th>退会時のユーザー</th><th>理由</th><th>自由記入</th>
        </tr></thead><tbody>${rows.map((r) => `
        <tr>
          <td class="muted">${fmtDate(r.created_at)}</td>
          <td class="muted">${escapeHtml(r.username_at_withdrawal || "—")}</td>
          <td>${(r.reasons || "").split(",").filter(Boolean)
            .map((k) => escapeHtml(labels[k] || k)).join("、") || "—"}</td>
          <td>${escapeHtml(r.detail || "—")}</td>
        </tr>`).join("")}</tbody></table>`;
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
    }
  }

  // app.logの行頭タイムスタンプ("YYYY-MM-DD HH:MM:SS,mmm")はサーバー
  // (コンテナ)のシステム時刻=UTCで書かれている。行の他の書式には触れず、
  // 行頭だけJSTに変換して表示する(2026-08-19・ユーザー指摘: 他のログと
  // 同様UTCのまま出ていた)。
  function errLineToJst(line) {
    const m = line.match(
      /^(\d{4})-(\d{2})-(\d{2}) (\d{2}):(\d{2}):(\d{2}),(\d{3})(.*)$/s);
    if (!m) return line;
    const [, y, mo, da, h, mi, se, ms, rest] = m;
    const utc = Date.UTC(+y, +mo - 1, +da, +h, +mi, +se, +ms);
    const jst = new Date(utc + 9 * 60 * 60 * 1000);
    const p = (n, w = 2) => String(n).padStart(w, "0");
    const stamp = `${jst.getUTCFullYear()}-${p(jst.getUTCMonth() + 1)}-`
      + `${p(jst.getUTCDate())} ${p(jst.getUTCHours())}:`
      + `${p(jst.getUTCMinutes())}:${p(jst.getUTCSeconds())},`
      + `${p(jst.getUTCMilliseconds(), 3)}`;
    return stamp + rest;
  }

  async function loadErrorLog() {
    const wrap = root.querySelector("#errorLogWrap");
    wrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    const lines = root.querySelector("#errLogLines").value;
    const level = root.querySelector("#errLogLevel").value;
    try {
      const res = await api.get(
        `/api/system/admin/error-log?lines=${lines}&level=${level}`);
      if (!res.lines.length) {
        wrap.innerHTML = `<p class="muted">該当するログがありません。</p>`;
        return;
      }
      wrap.innerHTML = `<p class="muted">日時はJST表記です。</p>
        <pre style="max-height:320px; overflow:auto;
        font-size:12px; white-space:pre-wrap; background:var(--panel-2);
        padding:10px; border-radius:8px">${
        escapeHtml(res.lines.map(errLineToJst).join("\n"))}</pre>`;
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
    }
  }
  root.querySelector("#errLogReload").addEventListener("click", loadErrorLog);
  root.querySelector("#errLogLines").addEventListener("change", loadErrorLog);
  root.querySelector("#errLogLevel").addEventListener("change", loadErrorLog);

  const clientErrKindLabel = {
    jserror: "JS例外", unhandledrejection: "未処理rejection",
    api_error: "APIエラー",  // 2026-09-18〜(ボタン押下等のAPI失敗)
  };
  async function loadClientErrorLog() {
    const wrap = root.querySelector("#clientErrorLogWrap");
    wrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    const days = root.querySelector("#clientErrLogDays").value;
    try {
      const res = await api.get(
        `/api/system/admin/client-error-log?days=${days}`);
      if (!res.grouped.length) {
        wrap.innerHTML = `<p class="muted">この期間はまだありません。</p>`;
        return;
      }
      const groupedRows = res.grouped.map((g) => `<tr>
        <td class="muted">${clientErrKindLabel[g.kind] || escapeHtml(g.kind)}</td>
        <td>${escapeHtml(g.message)}</td>
        <td>${g.cnt}</td>
        <td class="muted">${fmtDate(g.last_seen)}</td>
      </tr>`).join("");
      const recentRows = res.recent.map((r) => `<tr>
        <td class="muted">${fmtDate(r.created_at)}</td>
        <td class="muted">${clientErrKindLabel[r.kind] || escapeHtml(r.kind)}</td>
        <td>${escapeHtml(r.message)}</td>
        <td class="muted">${escapeHtml(r.url || "")}${
          r.line ? `:${r.line}:${r.col}` : ""}</td>
        <td class="muted">${escapeHtml(r.ip || "")}</td>
      </tr>`).join("");
      wrap.innerHTML = `
        <h3>メッセージ別の件数（多い順）</h3>
        <table><thead><tr>
          <th>種別</th><th>メッセージ</th><th>件数</th><th>最終発生</th>
        </tr></thead><tbody>${groupedRows}</tbody></table>
        <details class="mt"><summary>📋 直近の生ログ（${res.recent.length}件）</summary>
          <table class="mt"><thead><tr>
            <th>日時</th><th>種別</th><th>メッセージ</th><th>発生箇所</th><th>IP</th>
          </tr></thead><tbody>${recentRows}</tbody></table>
        </details>`;
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
    }
  }
  root.querySelector("#clientErrLogReload")
    .addEventListener("click", loadClientErrorLog);
  root.querySelector("#clientErrLogDays")
    .addEventListener("change", loadClientErrorLog);

  async function loadAccessLog() {
    const wrap = root.querySelector("#accessLogWrap");
    wrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    const from = root.querySelector("#accLogFrom").value;
    const to = root.querySelector("#accLogTo").value;
    const days = root.querySelector("#accLogDays").value;
    const qs = (from || to)
      ? `date_from=${encodeURIComponent(from)}&date_to=${encodeURIComponent(to)}`
      : `days=${days}`;
    let res;
    try {
      res = await api.get(`/api/system/admin/access-log-summary?${qs}`);
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
      return;
    }
    if (!res.days.length) {
      wrap.innerHTML = `<p class="muted">まだ集計データがありません
        （VPSでcronの初回実行を待つか、ローカル開発環境では対象外です）。</p>`;
      return;
    }
    const cat = (res.summary && res.summary.by_category) || {};
    const summaryHtml = `<div class="grid cols-4 mt">
      <div class="stat"><div class="num">${cat.human ?? 0}</div>
        <div class="lbl">人間らしきアクセス(合計)</div></div>
      <div class="stat"><div class="num">${cat.ai_crawler ?? 0}</div>
        <div class="lbl">AIクローラー(合計)</div></div>
      <div class="stat"><div class="num">${cat.search_bot ?? 0}</div>
        <div class="lbl">検索bot(合計)</div></div>
      <div class="stat"><div class="num">${cat.other_bot ?? 0}</div>
        <div class="lbl">その他bot(合計)</div></div>
    </div>`;
    const rowsHtml = res.days.slice().reverse().map((d) => {
      const topPages = (d.top_human_paths || []).slice(0, 3)
        .map(([p, c]) => `${escapeHtml(p)}(${c})`).join(", ") || "—";
      const topRef = (d.top_referrers || []).slice(0, 1)
        .map(([r, c]) => escapeHtml(r) + "(" + c + ")").join("") || "—";
      const dcat = d.categories || {};
      const aiCrawlerCnt = Object.entries(dcat)
        .filter(([k]) => k.startsWith("ai_crawler:"))
        .reduce((sum, [, v]) => sum + v, 0);
      const searchBotCnt = Object.entries(dcat)
        .filter(([k]) => k.startsWith("search_bot:"))
        .reduce((sum, [, v]) => sum + v, 0);
      return `<tr>
        <td class="muted">${d.date}</td>
        <td>${d.total_requests}</td>
        <td>${d.unique_ips}</td>
        <td>${d.unique_human_ips}</td>
        <td>${aiCrawlerCnt}</td>
        <td>${searchBotCnt}</td>
        <td style="max-width:260px">${topPages}</td>
        <td>${topRef}</td>
      </tr>`;
    }).join("");
    wrap.innerHTML = `${summaryHtml}
      <table class="mt"><thead><tr>
      <th>日付</th><th>総リクエスト</th><th>ユニークIP</th>
      <th>人間らしきIP</th><th>AIクローラー</th><th>検索bot</th>
      <th>よく見られたページ</th><th>主な参照元</th>
      </tr></thead><tbody>${rowsHtml}</tbody></table>`;
  }
  root.querySelector("#accLogReload").addEventListener("click", loadAccessLog);
  root.querySelector("#accLogDays").addEventListener("change", loadAccessLog);
  root.querySelector("#accLogClearRange").addEventListener("click", () => {
    root.querySelector("#accLogFrom").value = "";
    root.querySelector("#accLogTo").value = "";
    loadAccessLog();
  });

  // --- 訪問者数の推移(2026-08-24) ------------------------------------------
  // クローラーは人間より桁が大きいことが多く、同じY軸に乗せると人間側の
  // 折れ線がほぼ潰れて見えなくなる問題があった(2026-09-09ユーザー指摘)。
  // Y軸2軸は異なる尺度を重ねると誤解を招きやすいため採用せず、代わりに
  // クローラー線の表示on/offでY軸の基準(maxVal)を人間側だけに合わせ
  // 直せるようにする。
  function buildVisitTrendSvg(daily, showBot) {
    const W = 680, H = 220, padL = 40, padR = 14, padT = 10, padB = 24;
    const innerW = W - padL - padR, innerH = H - padT - padB;
    const n = daily.length;
    const maxVal = Math.max(
      1, ...daily.map((d) =>
        Math.max(d.js_reached || 0,
          showBot ? Math.max(d.human_total, d.bot_total) : d.human_total)));
    const magnitude = Math.pow(10, Math.floor(Math.log10(maxVal || 1)));
    const niceMax = [1, 2, 5, 10].map((s) => s * magnitude)
      .find((v) => maxVal <= v) || 10 * magnitude;
    const x = (i) => padL + (n <= 1 ? innerW / 2 : (innerW * i) / (n - 1));
    const y = (v) => padT + innerH - (innerH * v) / niceMax;

    const gridCount = 4;
    const gridLines = Array.from({ length: gridCount + 1 }, (_, i) => {
      const v = Math.round((niceMax / gridCount) * i);
      const yy = y(v);
      return `<line x1="${padL}" y1="${yy}" x2="${W - padR}" y2="${yy}"
          stroke="var(--line)" stroke-width="1" />
        <text x="${padL - 6}" y="${yy + 4}" text-anchor="end"
          font-size="10" fill="var(--muted)">${v.toLocaleString()}</text>`;
    }).join("");

    const labelStep = Math.max(1, Math.ceil(n / 8));
    const xLabels = daily.map((d, i) => {
      if (i % labelStep !== 0 && i !== n - 1) return "";
      const short = d.date.slice(5).replace("-", "/");
      return `<text x="${x(i)}" y="${H - 6}" text-anchor="middle"
        font-size="10" fill="var(--muted)">${short}</text>`;
    }).join("");

    const hasJs = daily.some((d) => (d.js_reached || 0) > 0);
    const linePath = (key) => daily.map((d, i) =>
      `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(d[key]).toFixed(1)}`)
      .join(" ");
    const dots = (key, cls) => daily.map((d, i) =>
      `<circle cx="${x(i).toFixed(1)}" cy="${y(d[key]).toFixed(1)}" r="4"
        class="${cls}" stroke="var(--panel)" stroke-width="2" />`).join("");
    const last = n ? daily[n - 1] : null;
    const endLabel = (val, dy) => last
      ? `<text x="${x(n - 1) + 6}" y="${y(val) + dy}" font-size="11"
          font-weight="700" fill="var(--text)">${val}</text>`
      : "";

    return `
      <svg viewBox="0 0 ${W} ${H}" class="visit-trend-svg" role="img"
        aria-label="訪問者数(人間${
          showBot ? "/クローラー" : ""}・JS到達)の日別推移グラフ">
        ${gridLines}
        ${xLabels}
        ${showBot ? `<path d="${linePath("bot_total")}" fill="none"
          stroke="var(--vt-bot)" stroke-width="2"
          stroke-linecap="round" stroke-linejoin="round" />` : ""}
        <path d="${linePath("human_total")}" fill="none"
          stroke="var(--vt-human)" stroke-width="2"
          stroke-linecap="round" stroke-linejoin="round" />
        ${hasJs ? `<path d="${linePath("js_reached")}" fill="none"
          stroke="var(--vt-js)" stroke-width="2" stroke-dasharray="5 3"
          stroke-linecap="round" stroke-linejoin="round" />` : ""}
        ${showBot ? dots("bot_total", "vt-dot-bot") : ""}
        ${dots("human_total", "vt-dot-human")}
        ${last ? endLabel(last.human_total, -8) : ""}
        ${last && showBot ? endLabel(last.bot_total, 16) : ""}
        <line class="vt-crosshair" x1="-100" x2="-100"
          y1="${padT}" y2="${H - padB}" stroke="var(--line)"
          stroke-width="1" />
      </svg>`;
  }

  function wireVisitTrendHover(wrapEl, daily) {
    const svgEl = wrapEl.querySelector(".visit-trend-svg");
    const tip = wrapEl.querySelector(".vt-tooltip");
    const crosshair = svgEl.querySelector(".vt-crosshair");
    const W = 680, padL = 40, padR = 14;
    const innerW = W - padL - padR;
    const n = daily.length;
    const xAt = (i) => padL + (n <= 1 ? innerW / 2 : (innerW * i) / (n - 1));
    svgEl.addEventListener("mousemove", (e) => {
      const rect = svgEl.getBoundingClientRect();
      const relX = ((e.clientX - rect.left) / rect.width) * W;
      let idx = 0, best = Infinity;
      daily.forEach((d, i) => {
        const dist = Math.abs(xAt(i) - relX);
        if (dist < best) { best = dist; idx = i; }
      });
      const d = daily[idx];
      crosshair.setAttribute("x1", xAt(idx));
      crosshair.setAttribute("x2", xAt(idx));
      tip.style.display = "block";
      tip.style.left = `${e.clientX - rect.left + 10}px`;
      tip.style.top = `${e.clientY - rect.top - 10}px`;
      tip.innerHTML = `<b>${escapeHtml(d.date)}</b><br>
        🧑 人間: ${d.human_total}件(IP ${d.human_unique_ips})<br>
        🤖 クローラー: ${d.bot_total}件(IP ${d.bot_unique_ips})<br>
        ⚡ JS到達: ${d.js_reached ?? 0}人`;
    });
    svgEl.addEventListener("mouseleave", () => {
      tip.style.display = "none";
      crosshair.setAttribute("x1", -100);
      crosshair.setAttribute("x2", -100);
    });
  }

  let visitTrendDays = 30;
  // 延べ数(human_total/bot_total)は日次の単純合計なので累積和が取れるが、
  // ユニークIP数は日をまたぐ重複排除ができない(バックエンドがIP集合では
  // なく件数しか返さない)ため、累積表示は延べ数のみに適用する。
  function toCumulativeVisits(daily) {
    let h = 0, b = 0, j = 0;
    return daily.map((d) => {
      h += d.human_total;
      b += d.bot_total;
      // JS到達の日別値は日ごとのユニーク人数(日をまたぐ重複排除は
      // できない)ため、累積表示でも単純な累計にする(延べ人数の目安)。
      j += (d.js_reached || 0);
      return { ...d, human_total: h, bot_total: b, js_reached: j };
    });
  }
  async function loadVisitTrend() {
    const wrap = root.querySelector("#visitTrendWrap");
    wrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    let res;
    try {
      res = await api.get(
        `/api/system/admin/visit-trend?days=${visitTrendDays}`);
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
      return;
    }
    const rawDaily = res.daily || [];
    if (!rawDaily.length) {
      wrap.innerHTML = `<p class="muted">この期間のデータはまだありません。</p>`;
      return;
    }
    const cumulative = root.querySelector("#visitTrendCumulative").checked;
    const showBot = root.querySelector("#visitTrendShowBot").checked;
    const daily = cumulative ? toCumulativeVisits(rawDaily) : rawDaily;
    const s = res.summary || {};
    const summaryHtml = `<div class="grid cols-4 mt">
      <div class="stat"><div class="num">${s.human_total ?? 0}</div>
        <div class="lbl">人間(延べ)</div></div>
      <div class="stat"><div class="num">${s.human_unique_ips ?? 0}</div>
        <div class="lbl">人間(ユニークIP)</div></div>
      <div class="stat"><div class="num">${s.bot_total ?? 0}</div>
        <div class="lbl">クローラー(延べ)</div></div>
      <div class="stat"><div class="num">${s.bot_unique_ips ?? 0}</div>
        <div class="lbl">クローラー(ユニークIP)</div></div>
      <div class="stat"><div class="num">${s.js_reached ?? 0}</div>
        <div class="lbl">JS到達(ユニーク・計測開始後のみ)</div></div>
    </div>`;
    const legendHtml = `<div class="row mt visit-trend-legend">
      <span class="vt-legend-item"><span class="vt-swatch vt-dot-human">
        </span>人間</span>
      ${showBot ? `<span class="vt-legend-item">
        <span class="vt-swatch vt-dot-bot"></span>クローラー</span>` : ""}
      <span class="vt-legend-item"><span class="vt-swatch vt-dot-js">
        </span>JS到達(点線)</span>
    </div>`;
    const rowsHtml = daily.slice().reverse().map((d) => `<tr>
      <td class="muted">${escapeHtml(d.date)}</td>
      <td>${d.human_total}</td><td>${d.human_unique_ips}</td>
      <td>${d.bot_total}</td><td>${d.bot_unique_ips}</td>
      <td>${d.js_reached ?? 0}</td>
    </tr>`).join("");
    wrap.innerHTML = `${summaryHtml}${legendHtml}
      <div class="visit-trend-wrap mt">
        ${buildVisitTrendSvg(daily, showBot)}
        <div class="vt-tooltip" style="display:none"></div>
      </div>
      <div style="overflow-x:auto"><table class="mt" style="min-width:440px"><thead><tr>
        <th>日付</th><th>人間(${cumulative ? "累積" : "延べ"})</th>
        <th>人間(IP)</th>
        <th>クローラー(${cumulative ? "累積" : "延べ"})</th>
        <th>クローラー(IP)</th><th>JS到達</th>
      </tr></thead><tbody>${rowsHtml}</tbody></table></div>`;
    wireVisitTrendHover(wrap.querySelector(".visit-trend-wrap"), daily);
  }
  root.querySelectorAll(".visit-trend-range").forEach((b) => {
    b.addEventListener("click", () => {
      visitTrendDays = Number(b.dataset.days);
      root.querySelectorAll(".visit-trend-range").forEach((x) =>
        x.classList.toggle("active", x === b));
      loadVisitTrend();
    });
  });
  root.querySelector("#visitTrendReload")
    .addEventListener("click", loadVisitTrend);
  root.querySelector("#visitTrendCumulative")
    .addEventListener("change", loadVisitTrend);
  root.querySelector("#visitTrendShowBot")
    .addEventListener("change", loadVisitTrend);

  // --- 日次スナップショット(成長ログ・2026-09-20・計測設計3-F) ------------
  let growthDays = 30;
  async function loadGrowthDaily() {
    const wrap = root.querySelector("#growthDailyWrap");
    wrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    let res;
    try {
      res = await api.get(`/api/system/admin/growth-daily?days=${growthDays}`);
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
      return;
    }
    const n0 = (v) => (v == null ? "—" : Math.round(v).toLocaleString());
    const pct = (a, b) => (b ? `${(a / b * 100).toFixed(0)}%` : "—");
    const st = res.status;
    let statusHtml;
    if (!st) {
      statusHtml = `<p class="muted" style="font-size:12px">⏳ まだ一度も
        自動更新が実行されていません(初回のバックフィルと、毎日の更新待ち)。</p>`;
    } else if (!st.ok) {
      statusHtml = `<p style="font-size:13px; color:var(--danger)">
        ⚠️ 最後の自動更新は<b>失敗</b>しました(${escapeHtml(fmtDateJST(st.at))}
        JST・${escapeHtml(st.error || "")})。失敗した間は古い操作記録の
        削除も止まっています。</p>`;
    } else {
      statusHtml = `<p class="muted" style="font-size:12px">最終更新:
        ${escapeHtml(fmtDateJST(st.at))} JST・成功
        (${st.days ?? 0}日分・${st.rows ?? 0}行を更新)。保存済み
        ${res.coverage.days ?? 0}日分(${escapeHtml(res.coverage.first || "—")}
        〜${escapeHtml(res.coverage.last || "—")})。</p>`;
    }
    const missingHtml = res.missing_days > 0
      ? `<p class="muted" style="font-size:12px">この期間で未保存の日:
        ${res.missing_days}日(バックフィル前や、記録開始前の日を含みます)。</p>`
      : "";
    const daily = res.daily || [];
    if (!daily.length) {
      wrap.innerHTML = `${statusHtml}${missingHtml}<p class="muted">この期間に
        保存された日次データがまだありません。</p>`;
      return;
    }
    const sum = (k) => daily.reduce((a, d) => a + (d.m[k] || 0), 0);
    const tile = (v, lbl) => `<div class="stat"><div class="num">
      ${Math.round(v).toLocaleString()}</div><div class="lbl">${lbl}</div></div>`;
    const tilesHtml = `<div class="grid cols-4 mt">
      ${tile(sum("visitors"), "訪問(日別ユニークの合計)")}
      ${tile(sum("visitors_js"), "JS到達(同)")}
      ${tile(sum("visitors_engaged"), "操作あり(同)")}
      ${tile(sum("signup_done"), "登録完了")}
      ${tile(sum("new_users"), "新規登録(アカウント数)")}
      ${tile(sum("login_users"), "ログイン人日")}
      ${tile(Math.max(...daily.map((d) => d.m.active_users || 0)),
        "アクティブ人数の日最大")}
      ${tile(sum("revenue_jpy"), "入金(円)")}
    </div>`;
    const maxV = Math.max(1, ...daily.map((d) => d.m.visitors || 0));
    const rowsHtml = daily.slice().reverse().map((d) => {
      const m = d.m;
      const w = Math.round((m.visitors || 0) / maxV * 60);
      // 操作系の指標は計測開始(2026-08-17)前の日は保存していない(—表示)。
      return `<tr>
        <td class="muted">${escapeHtml(d.date)}</td>
        <td style="white-space:nowrap">${n0(m.visitors)} <span style="display:inline-block; height:8px;
          width:${w}px; background:var(--accent); border-radius:2px;
          vertical-align:middle"></span></td>
        <td>${n0(m.visitors_js)}</td><td>${n0(m.visitors_human)}</td>
        <td>${n0(m.visitors_engaged)}</td>
        <td>${n0(m.signup_started)}</td><td>${n0(m.signup_attempted)}</td>
        <td>${n0(m.signup_done)}</td><td>${n0(m.new_users)}</td>
        <td>${n0(m.login_users)}</td><td>${n0(m.active_users)}</td>
        <td>${n0(m.client_errors)}</td>
        <td class="muted">${n0(m.visitors_bot_excluded)}/${
          n0(m.visitors_internal_excluded)}</td>
      </tr>`;
    }).join("");
    const chRows = (res.channels || []).map((c) => `<tr>
      <td>${escapeHtml(c.label)}</td><td>${n0(c.visitors)}</td>
      <td>${n0(c.visitors_human)}</td><td>${n0(c.visitors_js)}</td>
      <td>${n0(c.visitors_engaged)}</td><td>${n0(c.signup_started)}</td>
      <td>${n0(c.signup_done)}</td></tr>`).join("");
    const ftRows = (res.features || []).map((f) => `<tr>
      <td>${escapeHtml(f.name)}</td><td>${n0(f.events)}</td>
      <td>${n0(f.actor_days)}</td></tr>`).join("");
    const cell = (c, k) => (c.cells[k] == null
      ? `<td class="muted">—</td>`
      : `<td>${c.cells[k]}<span class="muted"> (${pct(c.cells[k], c.size)})
        </span></td>`);
    const coRows = (res.cohorts || []).slice().reverse().map((c) => `<tr>
      <td class="muted">${escapeHtml(c.cohort_date)}</td><td>${c.size}</td>
      ${cell(c, "d1")}${cell(c, "d7")}${cell(c, "w1")}${cell(c, "w2")}
      ${cell(c, "w4")}</tr>`).join("");
    wrap.innerHTML = `${statusHtml}${missingHtml}${tilesHtml}
      <div style="overflow-x:auto"><table class="mt" style="min-width:760px">
        <thead><tr><th>日付(JST)</th><th>訪問</th><th>JS到達</th>
          <th>人間訪問</th><th>操作あり</th><th>登録開始</th><th>登録試行</th>
          <th>登録完了</th><th>新規登録</th><th>ログイン</th><th>アクティブ</th>
          <th>エラー</th><th>除外(ボット/自分)</th></tr></thead>
        <tbody>${rowsHtml}</tbody></table></div>
      <p class="muted" style="font-size:12px">訪問=その日のユニーク(ゲスト
        単位)。JS到達・人間訪問・操作あり・登録開始・アクティブ・エラーは
        操作記録の計測開始(2026-08-17)以降のみで、それ以前の日は「—」です。
        JS到達の記録は2026-09-19以降のため、それ以前は0です。除外=ボット判定/
        自分の端末として集計から外したゲスト数(除外が効いているかの確認用)。</p>
      ${chRows
        ? `<h3 class="mt">流入元チャネル別（期間合計・日別ユニークの延べ）</h3>
          <div style="overflow-x:auto"><table class="mt"><thead><tr>
            <th>チャネル</th><th>訪問</th><th>人間訪問</th><th>JS到達</th>
            <th>操作あり</th><th>登録開始</th><th>登録完了</th></tr></thead>
            <tbody>${chRows}</tbody></table></div>` : ""}
      ${ftRows
        ? `<details class="mt"><summary>機能別の利用回数（期間合計・上位）
          </summary><div style="overflow-x:auto"><table class="mt"><thead><tr>
            <th>機能</th><th>回数</th><th>人日</th></tr></thead>
            <tbody>${ftRows}</tbody></table></div></details>` : ""}
      <h3 class="mt">登録日コホート別の継続（登録した人のうち、その後に
        活動した人数）</h3>
      <p class="muted" style="font-size:12px">翌日=登録の翌日に活動 /
        7日目=登録から7日後の1日に活動 / W1=登録後7〜13日目のどこかで活動 /
        W2=14〜20日目 / W4=28〜34日目。活動=ログイン・単語/フレーズの学習・
        AI利用・画面操作のいずれか。「—」は、まだその日/週が来ていない
        か、生ログが残っておらず集計できなかったものです。人数が少ない間は
        率(％)は参考程度に。</p>
      ${coRows
        ? `<div style="overflow-x:auto"><table class="mt"><thead><tr>
            <th>登録日</th><th>登録人数</th><th>翌日</th><th>7日目</th>
            <th>W1</th><th>W2</th><th>W4</th></tr></thead>
            <tbody>${coRows}</tbody></table></div>`
        : `<p class="muted">この期間に登録した人のコホートはまだありません。</p>`}`;
  }
  root.querySelectorAll(".growth-range").forEach((b) => {
    b.addEventListener("click", () => {
      growthDays = Number(b.dataset.days);
      root.querySelectorAll(".growth-range").forEach((x) =>
        x.classList.toggle("active", x === b));
      loadGrowthDaily();
    });
  });
  root.querySelector("#growthDailyReload")
    .addEventListener("click", loadGrowthDaily);

  async function runAiUsageSearch() {
    const wrap = root.querySelector("#aiUsageSearchWrap");
    wrap.innerHTML = `<p class="muted">検索中…</p>`;
    const params = new URLSearchParams();
    const uid = root.querySelector("#auSearchUid").value.trim();
    if (uid) params.set("user_id", uid);
    const from = root.querySelector("#auSearchFrom").value;
    if (from) params.set("date_from", from);
    const to = root.querySelector("#auSearchTo").value;
    if (to) params.set("date_to", to);
    const feature = root.querySelector("#auSearchFeature").value.trim();
    if (feature) params.set("feature", feature);
    const model = root.querySelector("#auSearchModel").value.trim();
    if (model) params.set("model", model);
    const ip = root.querySelector("#auSearchIp").value.trim();
    if (ip) params.set("ip", ip);
    params.set("limit", "200");
    try {
      const res = await api.get(
        `/api/system/admin/ai-usage-search?${params.toString()}`);
      if (!res.rows.length) {
        wrap.innerHTML = `<p class="muted">該当する利用ログはありません。</p>`;
        return;
      }
      wrap.innerHTML = `<p class="muted">該当 ${res.total_count}件 /
        合計費用 $${res.total_cost_usd.toFixed(4)}
        （先頭${res.rows.length}件を表示）</p>
        <table><thead><tr>
        <th>日時(JST)</th><th>ユーザーID</th><th>IP</th><th>モデル</th>
        <th>機能</th><th>in</th><th>out</th><th>$</th>
        </tr></thead><tbody>${res.rows.map((r) => `
        <tr>
          <td class="muted">${fmtDate(r.created_at)}</td>
          <td>${r.user_id}</td>
          <td class="muted">${escapeHtml(r.ip || "—")}</td>
          <td>${escapeHtml(r.model)}</td>
          <td>${escapeHtml(r.feature || "—")}</td>
          <td>${r.prompt_tokens}</td>
          <td>${r.output_tokens}</td>
          <td>${r.cost_usd.toFixed(5)}</td>
        </tr>`).join("")}</tbody></table>`;
    } catch (e) {
      wrap.innerHTML = `<p class="muted">検索失敗: ${escapeHtml(e.message)}</p>`;
    }
  }
  root.querySelector("#auSearchBtn").addEventListener("click", runAiUsageSearch);

  // 利用状況分析（画面別/機能別再生/ボタン押下/IP別/分野別/年代・性別・
  // 2026-08-17新設、2026-08-19に項目ごとの折りたたみ表示へ再構成）。
  async function loadUsageAnalytics() {
    const setAll = (msg) => {
      ["uaPagesWrap", "uaPlaysWrap", "uaClicksWrap", "uaWordDomainsWrap",
        "uaPhraseScenesWrap", "uaIpsWrap", "uaDailyWrap", "uaHourlyWrap",
        "uaDemoWrap", "uaReferralsWrap",
      ].forEach((id) => {
        const el2 = root.querySelector(`#${id}`);
        if (el2) el2.innerHTML = `<p class="muted">${msg}</p>`;
      });
    };
    const days = root.querySelector("#uaDays").value;
    root.querySelector("#uaSummaryWrap").textContent = "読み込み中…";
    setAll("読み込み中…");
    let res;
    try {
      res = await api.get(
        `/api/system/admin/usage-analytics?days=${days}&${adminAggQuery()}`);
    } catch (e) {
      const msg = `取得失敗: ${escapeHtml(e.message)}`;
      root.querySelector("#uaSummaryWrap").innerHTML = msg;
      setAll(msg);
      return;
    }
    const filteredOut = res.filtered_out_events || 0;
    root.querySelector("#uaSummaryWrap").innerHTML =
      `対象期間の総イベント数: ${res.total_events}件`
      + (filteredOut > 0
        ? ` <span class="muted">（上のフィルタ条件で除外された分が別途
            ${filteredOut}件あります。0件が並ぶ場合はフィルタを
            緩めてご確認ください）</span>`
        : "");

    const groupTable = (rows, catLabel, opts) => {
      opts = opts || {};
      if (!rows.length) return `<p class="muted">まだありません。</p>`;
      const labelCol = opts.noLabel ? "" : "<th>詳細</th>";
      return `<table><thead><tr>
          <th>${catLabel}</th>${labelCol}<th>回数</th>
          <th>ユニークIP</th><th>ユニークユーザー</th>
        </tr></thead><tbody>${rows.map((r) => `
          <tr>
            <td>${escapeHtml(r.category)}</td>
            ${opts.noLabel ? "" :
              `<td class="muted">${escapeHtml(r.label || "—")}</td>`}
            <td>${r.cnt}</td>
            <td>${r.uniq_ip}</td>
            <td>${r.uniq_user}</td>
          </tr>`).join("")}</tbody></table>`;
    };
    root.querySelector("#uaPagesWrap").innerHTML =
      groupTable(res.pages, "画面(タブ)");
    root.querySelector("#uaPlaysWrap").innerHTML =
      groupTable(res.plays, "機能");
    root.querySelector("#uaClicksWrap").innerHTML =
      groupTable(res.clicks, "画面(タブ)");
    root.querySelector("#uaWordDomainsWrap").innerHTML =
      groupTable(res.word_domains || [], "単語の分野", { noLabel: true });
    root.querySelector("#uaPhraseScenesWrap").innerHTML =
      groupTable(res.phrase_scenes || [], "フレーズのシーン",
        { noLabel: true });

    root.querySelector("#uaIpsWrap").innerHTML = res.ips.length ?
      `<table><thead><tr>
        <th>IP</th><th>合計</th><th>画面表示</th><th>再生</th>
        <th>クリック</th><th>ユーザー名</th><th>最終アクセス(JST)</th>
      </tr></thead><tbody>${res.ips.map((r) => `
        <tr>
          <td class="muted">${escapeHtml(r.ip)}
            ${r.is_admin ? '<span class="badge-warn" title="管理者の既知IP(.envのADMIN_KNOWN_IPS)、または全ての行が自分の端末(内部Cookie)">👑管理者</span>' : ""}</td>
          <td>${r.total}</td>
          <td>${r.pages}</td>
          <td>${r.plays}</td>
          <td>${r.clicks}</td>
          <td>${escapeHtml(r.usernames || "—")}</td>
          <td class="muted">${fmtDate(r.last_seen)}</td>
        </tr>`).join("")}</tbody></table>` :
      `<p class="muted">まだありません。</p>`;

    // 上の総イベント数と同じ注意書き(2026-09-08追記)。この表は上の
    // フィルタ条件(管理者/招待/テスト除外)を継承しているため、フィルタが
    // 厳しいと「0件が並ぶ」だけになり、下にスクロールしてこの表だけ見た
    // 場合に上の注意書きを見落として「集計が壊れている」と誤解しやすい。
    const filterCaveat = filteredOut > 0
      ? `<p class="muted">（フィルタ条件で除外された分が別途${filteredOut}件
          あります。0件が並ぶ場合は上のフィルタを緩めてご確認ください）</p>`
      : "";
    root.querySelector("#uaDailyWrap").innerHTML = res.daily.length ?
      filterCaveat +
      `<table><thead><tr>
        <th>日付(JST)</th><th>画面表示</th><th>再生</th><th>クリック</th>
        <th>新規登録</th>
      </tr></thead><tbody>${res.daily.slice().reverse().map((d) => `
        <tr><td class="muted">${d.date}</td><td>${d.pages}</td>
          <td>${d.plays}</td><td>${d.clicks}</td>
          <td>${d.signups || 0}</td></tr>`).join("")}
      </tbody></table>` : `<p class="muted">まだありません。</p>`;

    const hourly = res.hourly || [];
    const hourlyMax = Math.max(1, ...hourly.map((h) =>
      h.pages + h.plays + h.clicks));
    root.querySelector("#uaHourlyWrap").innerHTML = hourly.length ?
      filterCaveat +
      `<table><thead><tr>
        <th>時</th><th>画面表示</th><th>再生</th><th>クリック</th>
        <th>合計</th><th></th>
      </tr></thead><tbody>${hourly.map((h) => {
        const total = h.pages + h.plays + h.clicks;
        const pct = Math.round(total / hourlyMax * 100);
        return `<tr><td class="muted">${h.hour}時</td>
          <td>${h.pages}</td><td>${h.plays}</td><td>${h.clicks}</td>
          <td>${total}</td>
          <td style="width:120px"><div class="bar">
            <span style="width:${pct}%"></span></div></td></tr>`;
      }).join("")}</tbody></table>` : `<p class="muted">まだありません。</p>`;

    const referrals = res.referrals || [];
    root.querySelector("#uaReferralsWrap").innerHTML = referrals.length ?
      `<table><thead><tr><th>回答</th><th>件数</th></tr></thead><tbody>
        ${referrals.map((r) => `
        <tr><td>${escapeHtml(r.label)}</td><td>${r.cnt}</td></tr>`).join("")}
      </tbody></table>` :
      `<p class="muted">まだありません（対象期間に登録した回答者がいません）。</p>`;

    const demo = res.demographics || [];
    const kindLabel = { word_domain: "単語", phrase_scene: "フレーズ" };
    root.querySelector("#uaDemoWrap").innerHTML = demo.length ?
      `<table><thead><tr>
        <th>年代</th><th>性別</th><th>種別</th><th>分野/シーン</th>
        <th>回数</th><th>ユニークユーザー</th>
      </tr></thead><tbody>${demo.map((r) => `
        <tr>
          <td>${escapeHtml(r.age_group)}</td>
          <td>${escapeHtml(r.gender)}</td>
          <td class="muted">${kindLabel[r.kind] || escapeHtml(r.kind)}</td>
          <td>${escapeHtml(r.category)}</td>
          <td>${r.cnt}</td>
          <td>${r.uniq_user}</td>
        </tr>`).join("")}</tbody></table>` :
      `<p class="muted">まだありません（サインアップ時のアンケートに
        回答したユーザーの再生履歴が必要です）。</p>`;
  }
  root.querySelector("#uaRefreshBtn")
    .addEventListener("click", loadUsageAnalytics);
  root.querySelector("#uaDays")
    .addEventListener("change", loadUsageAnalytics);

  // お得意様(複数回・複数日利用者)の深掘り分析(2026-09-16ユーザー要望)。
  async function loadPowerUsers() {
    const summaryWrap = root.querySelector("#puSummaryWrap");
    const itemsWrap = root.querySelector("#puItemsWrap");
    summaryWrap.textContent = "読み込み中…";
    itemsWrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    const days = root.querySelector("#puDays").value;
    const minEvents = root.querySelector("#puMinEvents").value || "5";
    const minDays = root.querySelector("#puMinDays").value || "2";
    const includeRegistered = root.querySelector("#puIncludeRegistered")
      .checked;
    let res;
    try {
      res = await api.get(`/api/system/admin/power-users?days=${days}`
        + `&min_events=${minEvents}&min_days=${minDays}`
        + `&include_registered=${includeRegistered}`
        + `&${adminAggQuery()}`);
    } catch (e) {
      const msg = `取得失敗: ${escapeHtml(e.message)}`;
      summaryWrap.innerHTML = msg;
      itemsWrap.innerHTML = "";
      return;
    }
    const topList = (rows, empty) => (rows && rows.length)
      ? rows.map(([k, v]) => `${escapeHtml(k)}(${v})`).join(" / ")
      : empty;
    summaryWrap.innerHTML = `対象: <b>${res.count}人</b>
      （直近${res.days}日・イベント${res.min_events}件以上・
      訪問${res.min_days}日以上が対象）<br>
      <span class="muted">対象者全体でよく見られた単語の分野:
      ${topList(res.summary.top_word_domains, "—")}<br>
      対象者全体でよく見られたフレーズのシーン:
      ${topList(res.summary.top_phrase_scenes, "—")}<br>
      対象者全体でよく開かれたタブ:
      ${topList(res.summary.top_tabs, "—")}</span>`;
    if (!res.items.length) {
      itemsWrap.innerHTML = `<p class="muted">条件に合う利用者はまだ
        いません（期間や件数条件を緩めてお試しください）。</p>`;
      return;
    }
    itemsWrap.innerHTML = `<table><thead><tr>
      <th>利用者</th><th>訪問日数</th><th>イベント数</th>
      <th>初回</th><th>最終</th>
      <th>単語の分野（多い順）</th><th>フレーズのシーン（多い順）</th>
      <th>よく開いたタブ</th><th>よく見た単語</th>
    </tr></thead><tbody>${res.items.map((it) => {
      // ログイン済みは表示名+ログイン名(username)を併記し、登録者か
      // 否かを一目で判別できるようにする(2026-09-18ユーザー要望)。
      const badges = [
        it.is_admin_user ? '<span class="muted">(管理者)</span>' : "",
        it.is_test_user ? '<span class="muted">(テスト)</span>' : "",
      ].filter(Boolean).join(" ");
      const who = it.identity_type === "user"
        ? `${escapeHtml(it.label)} ${badges}<br>
            <span class="muted">${escapeHtml(it.username || "")}</span>`
        : `${escapeHtml(it.label)}
            <span class="muted">(${it.identity_type === "guest"
              ? "未登録" : "旧IP単位"})${it.is_admin_device
              ? " (管理者の端末)" : ""}${it.is_test_device
              ? " (テストの端末)" : ""}</span>`;
      return `
      <tr>
        <td>${who}</td>
        <td>${it.distinct_days}</td>
        <td>${it.total_events}</td>
        <td>${fmtDate(it.first_seen)}</td>
        <td>${fmtDate(it.last_seen)}</td>
        <td>${topList(it.top_word_domains, "—")}</td>
        <td>${topList(it.top_phrase_scenes, "—")}</td>
        <td>${topList(it.top_tabs, "—")}</td>
        <td>${topList(it.top_words, "—")}</td>
      </tr>`;
    }).join("")}</tbody></table>`;
  }
  root.querySelector("#puRefreshBtn")
    .addEventListener("click", loadPowerUsers);
  ["puDays", "puMinEvents", "puMinDays", "puIncludeRegistered"].forEach(
    (id) => {
      root.querySelector(`#${id}`)
        .addEventListener("change", loadPowerUsers);
    });

  // ゲストのIP別深掘り分析(2026-09-17ユーザー要望)。一覧は概要のみ、
  // 行クリックで/admin/guest-ip-detailを遅延取得して展開する。
  const giCache = {};
  function renderGuestIpDetailHtml(d) {
    const topList = (rows, empty) => (rows && rows.length)
      ? rows.map(([k, v]) => `${escapeHtml(k)}(${v})`).join(" / ") : empty;
    const sumCount = (rows) =>
      (rows || []).reduce((s, [, v]) => s + v, 0);
    const errList = (rows, empty) => (rows && rows.length)
      ? `<ul style="margin:4px 0 0 18px">${rows.map((e) =>
        `<li>${fmtDate(e.at)}
          ${escapeHtml(e.category)}: ${escapeHtml(e.label)}</li>`)
        .join("")}</ul>`
      : `<p class="muted">${empty}</p>`;
    const jsErrList = (rows, empty) => (rows && rows.length)
      ? `<ul style="margin:4px 0 0 18px">${rows.map((e) =>
        `<li>${fmtDate(e.created_at)} [${escapeHtml(e.kind)}]
          ${escapeHtml(e.message || "")}
          <span class="muted">${escapeHtml(e.url || "")}${
            e.line ? ":" + e.line : ""}</span></li>`).join("")}</ul>`
      : `<p class="muted">${empty}</p>`;
    return `
      <div class="grid cols-2 mt" style="gap:12px">
        <div>
          <p><b>単語の分野</b>: ${topList(d.top_word_domains, "—")}</p>
          <p><b>フレーズのシーン</b>: ${topList(d.top_phrase_scenes, "—")}</p>
          <p><b>よく開いたタブ</b>: ${topList(d.top_tabs, "—")}</p>
          <p><b>クリックしたボタン</b>: ${topList(d.top_clicks, "—")}</p>
        </div>
        <div>
          <p><b>開いた単語の「詳細」</b>: ${topList(d.word_details, "—")}</p>
          <p><b>開いたフレーズの「詳細」</b>:
            ${topList(d.phrase_details, "—")}</p>
        </div>
      </div>
      <div class="grid cols-3 mt" style="gap:12px">
        <div><p><b>🔊 単語の発声</b>（${sumCount(d.word_plays)}回）</p>
          <p style="font-size:.9em">${topList(d.word_plays, "なし")}</p></div>
        <div><p><b>📖 例文の発声</b>（${sumCount(d.example_plays)}回）</p>
          <p style="font-size:.9em">
            ${topList(d.example_plays, "なし")}</p></div>
        <div><p><b>💬 フレーズの発声</b>（${sumCount(d.phrase_plays)}回）</p>
          <p style="font-size:.9em">
            ${topList(d.phrase_plays, "なし")}</p></div>
      </div>
      <div class="mt">
        <p><b>⚠️ 再生に失敗した項目</b>（${(d.play_errors || []).length}件・
          再生ボタンは押したが音声が出なかったケース。同じ対象への
          失敗回数が多いほど「何度も押した」ことを示します）</p>
        <p style="font-size:.9em">${
          topList(d.play_errors_by_target, "なし")}</p>
        <details style="margin-top:4px"><summary class="muted"
          style="cursor:pointer;font-size:.85em">時系列の生ログを見る</summary>
          ${errList(d.play_errors, "なし")}</details>
      </div>
      <div class="mt">
        <p><b>🐞 JS/APIエラー</b>（${(d.js_errors || []).length}件・
          ボタン押下等でAPIエラーになったケース[api_error]と、
          未捕捉のJS例外[jserror/unhandledrejection]の両方）</p>
        ${jsErrList(d.js_errors, "なし")}
      </div>`;
  }
  async function loadGuestIpAnalysis() {
    const summaryWrap = root.querySelector("#giSummaryWrap");
    const itemsWrap = root.querySelector("#giItemsWrap");
    summaryWrap.textContent = "読み込み中…";
    itemsWrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    const days = root.querySelector("#giDays").value;
    const minEvents = root.querySelector("#giMinEvents").value || "1";
    const includeAdmin = root.querySelector("#giIncludeAdmin").checked;
    const includeTest = root.querySelector("#giIncludeTest").checked;
    let res;
    try {
      res = await api.get(`/api/system/admin/guest-ip-analysis?days=${days}`
        + `&min_events=${minEvents}&include_admin=${includeAdmin}`
        + `&include_test=${includeTest}`);
    } catch (e) {
      summaryWrap.innerHTML = `取得失敗: ${escapeHtml(e.message)}`;
      itemsWrap.innerHTML = "";
      return;
    }
    summaryWrap.innerHTML = `対象IP: <b>${res.count}件</b>
      （直近${res.days}日・イベント${res.min_events}件以上が対象）`;
    if (!res.items.length) {
      itemsWrap.innerHTML = `<p class="muted">条件に合うゲストの
        アクセスはまだありません。</p>`;
      return;
    }
    const topList = (rows, empty) => (rows && rows.length)
      ? rows.map(([k, v]) => `${escapeHtml(k)}(${v})`).join(" / ") : empty;
    itemsWrap.innerHTML = `<table><thead><tr>
      <th></th><th>IP</th><th>訪問日数</th><th>イベント数</th>
      <th>発声</th><th>再生失敗</th><th>JSエラー</th>
      <th>単語詳細</th><th>フレーズ詳細</th>
      <th>初回</th><th>最終</th><th>単語の分野（多い順）</th>
    </tr></thead><tbody>${res.items.map((it) => `
      <tr class="gi-row" data-ip="${escapeHtml(it.ip)}"
        style="cursor:pointer">
        <td class="gi-arrow">▶</td>
        <td>${escapeHtml(it.ip)}${it.is_admin
          ? ' <span class="muted">(管理者)</span>' : ""}${it.is_test
          ? ' <span class="muted">(テスト)</span>' : ""}</td>
        <td>${it.distinct_days}</td>
        <td>${it.total_events}</td>
        <td>${it.total_plays}</td>
        <td>${it.total_play_errors > 0
          ? `<span class="badge-bad">${it.total_play_errors}</span>`
          : "0"}</td>
        <td>${it.total_client_errors > 0
          ? `<span class="badge-bad">${it.total_client_errors}</span>`
          : "0"}</td>
        <td>${it.word_detail_clicks}</td>
        <td>${it.phrase_detail_clicks}</td>
        <td>${fmtDate(it.first_seen)}</td>
        <td>${fmtDate(it.last_seen)}</td>
        <td>${topList(it.top_word_domains, "—")}</td>
      </tr>`).join("")}</tbody></table>`;
    itemsWrap.querySelectorAll(".gi-row").forEach((tr) => {
      tr.addEventListener("click", async () => {
        const existing = tr.nextElementSibling;
        if (existing && existing.classList.contains("gi-detail-row")) {
          existing.remove();
          tr.querySelector(".gi-arrow").textContent = "▶";
          return;
        }
        itemsWrap.querySelectorAll(".gi-detail-row")
          .forEach((r) => r.remove());
        itemsWrap.querySelectorAll(".gi-row .gi-arrow")
          .forEach((a) => { a.textContent = "▶"; });
        tr.querySelector(".gi-arrow").textContent = "▼";
        const ip = tr.dataset.ip;
        const detailTr = el(`<tr class="gi-detail-row"><td colspan="12">
          <p class="muted">読み込み中…</p></td></tr>`);
        tr.after(detailTr);
        try {
          const cacheKey = `${ip}:${days}`;
          let d = giCache[cacheKey];
          if (!d) {
            d = await api.get(`/api/system/admin/guest-ip-detail`
              + `?ip=${encodeURIComponent(ip)}&days=${days}`);
            giCache[cacheKey] = d;
          }
          detailTr.querySelector("td").innerHTML =
            renderGuestIpDetailHtml(d);
        } catch (e) {
          detailTr.querySelector("td").innerHTML =
            `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
        }
      });
    });
  }
  root.querySelector("#giRefreshBtn")
    .addEventListener("click", loadGuestIpAnalysis);
  ["giDays", "giMinEvents", "giIncludeAdmin", "giIncludeTest"].forEach((id) => {
    root.querySelector(`#${id}`)
      .addEventListener("change", loadGuestIpAnalysis);
  });

  // ログの各項目は開いたときに初めて取得する(2026-08-19・「概要をまず
  // だし、細かい項目は最初はたたんでおき」というユーザー要望に対応。
  // 併せて管理画面を開くたび無条件に5本のAPIを叩いていたのを解消)。
  const lazySections = [
    ["#logServerStatusDetails", loadServerStatusAll],
    ["#logLoginDetails", loadLoginLog],
    ["#logAnonAccessDetails", loadAnonAccess],
    ["#logRegFunnelDetails", loadRegFunnel],
    ["#logRegistrantsDetails", loadRegistrants],
    ["#logSurveySummaryDetails", loadSurveySummary],
    ["#logVisitTrendDetails", loadVisitTrend],
    ["#logGrowthDailyDetails", loadGrowthDaily],
    ["#logChargeKeyDetails", loadChargeKeyLog],
    ["#logWithdrawalDetails", loadWithdrawalLog],
    ["#logErrorDetails", loadErrorLog],
    ["#logClientErrorDetails", loadClientErrorLog],
    ["#logAccessDetails", loadAccessLog],
    ["#logUsageAnalyticsDetails", loadUsageAnalytics],
    ["#logPowerUsersDetails", loadPowerUsers],
    ["#logGuestIpDetails", loadGuestIpAnalysis],
  ];
  lazySections.forEach(([sel, loader]) => {
    const el2 = root.querySelector(sel);
    let loaded = false;
    el2.addEventListener("toggle", () => {
      if (el2.open && !loaded) { loaded = true; loader(); }
    });
  });

  // 管理概要の確認式アラートバナー(2026-09-16・新着登録/エラーログを
  // 確認ボタンを押すまで出し続ける。「詳細確認」はログタブの該当項目を
  // 開いてスクロールする)。
  function jumpToLogSection(detailsSelector) {
    const tabBtn = root.querySelector(
      '#adminTabs .step-chip[data-sec="logs"]');
    if (tabBtn) tabBtn.click();
    const details = root.querySelector(detailsSelector);
    if (details) {
      details.open = true;
      details.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }
  function renderAlertBanner() {
    const wrap = root.querySelector("#adminAlertBanner");
    if (!alerts) { wrap.innerHTML = ""; return; }
    const rows = [];
    if (alerts.registrants && alerts.registrants.count > 0) {
      rows.push(`<div class="alert-banner-row" data-kind="registrants"
        style="display:flex; align-items:center; gap:10px; padding:8px 12px;
        border-radius:8px; margin-bottom:8px; font-size:14px;
        background:rgba(54,201,141,.18); border:1px solid rgba(54,201,141,.5)">
        <span>🆕 新着登録者が <b>${alerts.registrants.count}件</b>
          あります（前回確認以降）。</span>
        <button type="button" class="btn ghost alert-detail-btn"
          data-kind="registrants" style="padding:2px 10px">詳細確認</button>
        <button type="button" class="btn alert-ack-btn"
          data-kind="registrants" style="padding:2px 10px">確認</button>
      </div>`);
    }
    if (alerts.errors && alerts.errors.count > 0) {
      rows.push(`<div class="alert-banner-row" data-kind="errors"
        style="display:flex; align-items:center; gap:10px; padding:8px 12px;
        border-radius:8px; margin-bottom:8px; font-size:14px;
        background:rgba(226,80,59,.18); border:1px solid rgba(226,80,59,.6)">
        <span>⚠️ エラーログが <b>${alerts.errors.count}件</b>
          発生しています（前回確認以降）。</span>
        <button type="button" class="btn ghost alert-detail-btn"
          data-kind="errors" style="padding:2px 10px">詳細確認</button>
        <button type="button" class="btn alert-ack-btn"
          data-kind="errors" style="padding:2px 10px">確認</button>
      </div>`);
    }
    wrap.innerHTML = rows.join("");
    wrap.querySelectorAll(".alert-detail-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        jumpToLogSection(btn.dataset.kind === "registrants"
          ? "#logRegistrantsDetails" : "#logErrorDetails");
      });
    });
    wrap.querySelectorAll(".alert-ack-btn").forEach((btn) => {
      btn.addEventListener("click", async () => {
        btn.disabled = true;
        try {
          alerts = await api.post("/api/system/admin/alerts/ack",
            { kind: btn.dataset.kind });
        } catch (e) {
          btn.disabled = false;
          alert(`確認処理に失敗しました: ${e.message}`);
          return;
        }
        renderAlertBanner();
      });
    });
  }
  renderAlertBanner();

  // ディスク使用量（「その他」タブを開いたときだけ取得・2026-08-19）。
  async function loadDiskUsage() {
    const wrap = root.querySelector("#diskUsageWrap");
    if (!wrap) return;
    wrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    try {
      const res = await api.get("/api/system/admin/disk-usage");
      const pct = Math.min(
        100, Math.round(res.tracked_total_mb / res.budget_mb * 100));
      const g = res.db_breakdown_mb || {};
      // 2026-09-14 DB分割後はファイルがそのままcontent/core/logsに
      // 分かれているため、キーもそれに合わせている(旧shared_content/
      // user_data/logs_history/otherから変更)。
      const groupLabel = {
        content: "コンテンツ(単語/フレーズ/音声等)",
        core: "コア(ユーザー/決済/単語帳/進捗等)",
        logs: "ログ(アクセス/ai_usage等)",
      };
      wrap.innerHTML = `
        <p><b>${res.tracked_total_mb}MB</b> / ${res.budget_mb}MB
          予算（${pct}%使用）</p>
        <div class="bar mt"><span style="width:${pct}%"></span></div>
        <div class="grid cols-4 mt">
          <div class="stat"><div class="num">${res.app_log_mb}</div>
            <div class="lbl">app.log(MB)</div></div>
          <div class="stat"><div class="num">${res.user_data_backups_mb}</div>
            <div class="lbl">ユーザーデータ バックアップ(MB)</div></div>
          <div class="stat"><div class="num">${res.db_file_total_mb}</div>
            <div class="lbl">DB本体 合計(MB・参考)</div></div>
        </div>
        ${res.dbstat_available ? `
        <h3 class="mt">DB本体の内訳（内容別・参考）</h3>
        <table><tbody>${Object.entries(g).map(([k, v]) => `
          <tr><td>${escapeHtml(groupLabel[k] || k)}</td>
            <td>${v}MB</td></tr>`).join("")}</tbody></table>` : ""}
        <p class="muted mt">${escapeHtml(res.note)}</p>`;
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
    }
  }
  let diskUsageLoaded = false;
  root.querySelector('.step-chip[data-sec="other"]')
    ?.addEventListener("click", () => {
      if (!diskUsageLoaded) { diskUsageLoaded = true; loadDiskUsage(); }
    });

  // --- コスト管理(原価/課金/粗利)レポート(2026-09-06新設) -------------
  function marginBadge(row) {
    if (row.is_loss) return `<span class="badge-bad">赤字</span>`;
    if (row.is_low_margin) return `<span class="badge-warn">低粗利</span>`;
    return `<span class="badge-ok">健全</span>`;
  }
  function costReportRow(label, row) {
    return `<tr>
      <td>${escapeHtml(label)}</td>
      <td>¥${row.cost_jpy.toLocaleString()}</td>
      <td>¥${row.charged_jpy.toLocaleString()}</td>
      <td>¥${row.profit_jpy.toLocaleString()}</td>
      <td>${row.margin_pct}%</td>
      <td>${marginBadge(row)}</td>
    </tr>`;
  }
  async function loadCostReport() {
    const wrap = root.querySelector("#costReportWrap");
    if (!wrap) return;
    wrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    const days = root.querySelector("#costReportDays")?.value || 30;
    try {
      const res = await api.get(`/api/system/admin/cost-report?days=${days}`);
      const head = `<thead><tr><th>対象</th><th>原価</th><th>課金額</th>
        <th>粗利</th><th>粗利率</th><th>状態</th></tr></thead>`;
      wrap.innerHTML = `
        <div class="grid cols-4 mt">
          <div class="stat"><div class="num">¥${res.total.cost_jpy.toLocaleString()}</div>
            <div class="lbl">総原価</div></div>
          <div class="stat"><div class="num">¥${res.total.charged_jpy.toLocaleString()}</div>
            <div class="lbl">総課金額</div></div>
          <div class="stat"><div class="num">¥${res.total.profit_jpy.toLocaleString()}</div>
            <div class="lbl">総粗利</div></div>
          <div class="stat"><div class="num">${res.total.margin_pct}%</div>
            <div class="lbl">粗利率 ${marginBadge(res.total)}</div></div>
        </div>
        <h3 class="mt">機能別</h3>
        ${res.by_feature.length ? `<table><tbody>` +
          `${head}${res.by_feature.map((r) =>
            costReportRow(r.feature, r)).join("")}</tbody></table>`
          : `<p class="muted">この期間のデータはありません。</p>`}
        <h3 class="mt">ユーザー別(粗利の低い順)</h3>
        ${res.by_user.length ? `<table><tbody>` +
          `${head}${res.by_user.map((r) =>
            costReportRow(
              `${r.username}${r.role === "admin" ? "(管理者)" : ""}`, r)
          ).join("")}</tbody></table>`
          : `<p class="muted">この期間のデータはありません。</p>`}`;
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
    }
  }
  let costReportLoaded = false;
  root.querySelector('.step-chip[data-sec="cost-report"]')
    ?.addEventListener("click", () => {
      if (!costReportLoaded) { costReportLoaded = true; loadCostReport(); }
    });
  root.querySelector("#costReportDays")
    ?.addEventListener("change", loadCostReport);

  // --- 実収支(実売上-実コスト)レポート(2026-09-09新設) ---------------
  async function loadPLReport() {
    const wrap = root.querySelector("#plReportWrap");
    if (!wrap) return;
    wrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    const days = root.querySelector("#plReportDays")?.value || 30;
    try {
      const res = await api.get(`/api/system/admin/pl-report?days=${days}`);
      const profitBadge = res.is_loss
        ? `<span class="badge-bad">赤字</span>`
        : `<span class="badge-ok">黒字</span>`;
      const yen = (n) => `¥${Math.round(n).toLocaleString()}`;
      const c = res.cost;
      const ad = res.ads || {};
      const goals = res.goals || {};
      const near = goals.near || {};
      const fin = goals.final || {};
      const goalPct = (n, t) => (t ? Math.min(100, Math.round(n / t * 100)) : 0);
      const goalHtml = `
        <h3 class="mt">🎯 数値目標の達成状況（累計）</h3>
        <table><thead><tr><th></th><th>現在</th><th>直近目標</th>
          <th>最終目標</th></tr></thead><tbody>
          <tr><td>登録者(管理者/テスト除く)</td><td>${goals.registrants ?? 0}人</td>
            <td>${near.registrants ?? "-"}人
              (${goalPct(goals.registrants ?? 0, near.registrants)}%)</td>
            <td>${fin.registrants ?? "-"}人
              (${goalPct(goals.registrants ?? 0, fin.registrants)}%)</td></tr>
          <tr><td>課金した人</td><td>${goals.payers ?? 0}人</td>
            <td>${near.payers ?? "-"}人
              (${goalPct(goals.payers ?? 0, near.payers)}%)</td>
            <td>${fin.payers ?? "-"}人
              (${goalPct(goals.payers ?? 0, fin.payers)}%)</td></tr>
        </tbody></table>`;
      const adsHtml = `
        <h3 class="mt">広告費の内訳（実額と予算(推定)）</h3>
        <table><tbody>
          <tr><td>実額（入力済み ${c.ads_actual_days ?? 0}日分）</td>
            <td>${yen(c.ads_actual_jpy ?? 0)}</td></tr>
          <tr><td>予算(推定)（入力の無い ${c.ads_estimated_days ?? 0}日分・
            予算スケジュールで日割り）</td>
            <td>${yen(c.ads_estimated_jpy ?? 0)}</td></tr>
          <tr><td>広告(gclid付き)経由の訪問者 / 登録者（自前計測）</td>
            <td>${ad.visitors ?? 0}人 / ${ad.signups ?? 0}人</td></tr>
          <tr><td>登録あたり広告費(CPA・参考値)</td>
            <td>${ad.cpa_jpy != null ? yen(ad.cpa_jpy) : "—"}</td></tr>
        </tbody></table>
        <p class="muted" style="font-size:12px">
          予算スケジュール: ${(res.budget_schedule || []).map((b) =>
            `${escapeHtml(b.from)}以降 ¥${b.jpy.toLocaleString()}/日`)
            .join("、")}。CPAは実額が入力されるまで予算(推定)ベースの
          参考値で、登録が少ないうちはぶれが大きい点に注意。</p>`;
      wrap.innerHTML = `
        <div class="grid cols-4 mt">
          <div class="stat"><div class="num">¥${res.revenue.total_jpy.toLocaleString()}</div>
            <div class="lbl">売上(BASE+PayPay)</div></div>
          <div class="stat"><div class="num">¥${res.cost.total_jpy.toLocaleString()}</div>
            <div class="lbl">コスト合計</div></div>
          <div class="stat"><div class="num">¥${res.profit_jpy.toLocaleString()}</div>
            <div class="lbl">損益 ${profitBadge}</div></div>
          <div class="stat"><div class="num">${res.days}日</div>
            <div class="lbl">集計期間</div></div>
        </div>
        <h3 class="mt">売上の内訳</h3>
        <table><tbody>
          <tr><td>BASE注文</td><td>¥${res.revenue.base_jpy.toLocaleString()}</td></tr>
          <tr><td>PayPay決済</td><td>¥${res.revenue.paypay_jpy.toLocaleString()}</td></tr>
        </tbody></table>
        <h3 class="mt">コストの内訳</h3>
        <table><tbody>
          <tr><td>AI原価(円換算)</td><td>¥${res.cost.ai_jpy.toLocaleString()}</td></tr>
          <tr><td>サーバー代(日割り)</td><td>¥${res.cost.server_jpy.toLocaleString()}</td></tr>
          <tr><td>広告費(実額+予算(推定))</td><td>¥${res.cost.ads_jpy.toLocaleString()}</td></tr>
        </tbody></table>
        ${adsHtml}${goalHtml}`;
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
    }
  }
  // --- 広告費の実額入力(2026-09-19・計測設計3-C) ---
  function jstToday() {
    // ブラウザのタイムゾーンによらずJSTの今日(YYYY-MM-DD)を得る。
    return new Date(Date.now() + 9 * 3600 * 1000).toISOString().slice(0, 10);
  }
  async function loadAdSpendList() {
    const wrap = root.querySelector("#adSpendList");
    if (!wrap) return;
    try {
      const res = await api.get("/api/system/admin/ad-spend?days=60");
      const items = res.items || [];
      if (!items.length) {
        wrap.innerHTML = `<p class="muted">実額の入力はまだありません
          (直近60日)。入力の無い日は予算(推定)で計算されます。</p>`;
        return;
      }
      wrap.innerHTML = `<table><thead><tr><th>日付(JST)</th><th>広告</th>
        <th>金額</th><th>メモ</th><th></th></tr></thead><tbody>${
        items.map((it) => `<tr>
          <td>${escapeHtml(it.date)}</td><td>${escapeHtml(it.source)}</td>
          <td>¥${Math.round(it.jpy).toLocaleString()}</td>
          <td class="muted">${escapeHtml(it.note || "")}</td>
          <td><button class="btn ghost ad-spend-del"
            data-date="${escapeHtml(it.date)}"
            data-source="${escapeHtml(it.source)}"
            style="padding:2px 8px">取消</button></td></tr>`).join("")
      }</tbody></table>`;
      wrap.querySelectorAll(".ad-spend-del").forEach((b) => {
        b.addEventListener("click", async () => {
          if (!confirm(`${b.dataset.date} の実額を取り消しますか？`
            + "(その日は予算(推定)に戻ります)")) return;
          try {
            await api.del(`/api/system/admin/ad-spend?date=${
              encodeURIComponent(b.dataset.date)}&source=${
              encodeURIComponent(b.dataset.source)}`);
            loadAdSpendList();
            loadPLReport();
          } catch (e) { toast(`取消に失敗: ${e.message}`); }
        });
      });
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
    }
  }
  const adSpendDateEl = root.querySelector("#adSpendDate");
  if (adSpendDateEl) adSpendDateEl.value = jstToday();
  root.querySelector("#adSpendSave")?.addEventListener("click", async () => {
    const msg = root.querySelector("#adSpendMsg");
    const date = root.querySelector("#adSpendDate").value;
    const jpy = root.querySelector("#adSpendJpy").value;
    if (!date || jpy === "") {
      msg.textContent = "日付と金額を入力してください。";
      return;
    }
    try {
      await api.post("/api/system/admin/ad-spend", {
        date, jpy: Number(jpy),
        source: root.querySelector("#adSpendSource").value,
        note: root.querySelector("#adSpendNote").value,
      });
      msg.textContent = `${date} を登録しました。`;
      root.querySelector("#adSpendJpy").value = "";
      loadAdSpendList();
      loadPLReport();
    } catch (e) { msg.textContent = `登録に失敗: ${e.message}`; }
  });
  let plReportLoaded = false;
  root.querySelector('.step-chip[data-sec="pl-report"]')
    ?.addEventListener("click", () => {
      if (!plReportLoaded) {
        plReportLoaded = true;
        loadPLReport();
        loadAdSpendList();
      }
    });
  root.querySelector("#plReportDays")
    ?.addEventListener("change", loadPLReport);

  root.querySelectorAll(".iq-done").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const id = btn.dataset.id;
      await api.put(`/api/inquiries/${id}/status`, { status: "対応済み" });
      root.querySelector(`.iq-status[data-id="${id}"]`).textContent = "対応済み";
      btn.remove();
    });
  });

  // 残高の手動調整（±10,000ptまで・理由必須・万が一の是正用）。
  root.querySelectorAll(".chg-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const uid = parseInt(btn.dataset.uid, 10);
      const inp = root.querySelector(`.chg-amt[data-uid="${uid}"]`);
      const noteInp = root.querySelector(`.chg-note[data-uid="${uid}"]`);
      let amt = parseInt(inp.value, 10);
      const note = (noteInp.value || "").trim();
      if (!Number.isFinite(amt) || amt === 0) { toast("金額を入力"); return; }
      if (Math.abs(amt) > 10000) {
        amt = Math.sign(amt) * 10000; toast("1回の上限は±10,000ptです");
      }
      if (!note) { toast("理由を入力してください"); return; }
      const verb = amt > 0 ? "増額" : "減額";
      if (!confirm(`残高を${amt}pt（${verb}）調整します。\n理由: ${note}\n`
        + `よろしいですか？`)) return;
      btn.disabled = true;
      try {
        const r = await api.post("/api/system/admin/charge",
          { user_id: uid, amount_jpy: amt, note });
        toast(`調整完了: 残高 ${Math.round(r.balance_jpy)}pt`);
        go("admin");  // 再描画
      } catch (e) { toast("失敗: " + e.message); btn.disabled = false; }
    });
  });

  // 残高変更履歴（監査用・直近20件）。
  root.querySelectorAll(".chg-log-btn").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const uid = parseInt(btn.dataset.uid, 10);
      try {
        const r = await api.get(
          `/api/system/admin/balance-ledger?user_id=${uid}&limit=20`);
        if (!r.entries.length) { alert("変更履歴はありません。"); return; }
        const lines = r.entries.map((e) => {
          const sign = e.delta_jpy > 0 ? "+" : "";
          const who = e.admin_username ? `管理者:${e.admin_username}` : "本人";
          return `${fmtDate(e.created_at)}  ${sign}¥${e.delta_jpy}`
            + `  → 残高¥${e.balance_after}  [${e.reason}/${who}]`
            + (e.note ? `  ${e.note}` : "");
        });
        alert("日時はJST表記です。\n\n" + lines.join("\n"));
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

  // 個々のユーザーの「テストユーザー」フラグ切り替え（2026-08-20・
  // 集計フィルタで除外/含める対象を管理者が手動で指定する）。
  root.querySelectorAll(".test-flag-cb").forEach((cb) => {
    cb.addEventListener("change", async () => {
      const uid = parseInt(cb.dataset.uid, 10);
      cb.disabled = true;
      try {
        await api.post(`/api/system/admin/users/${uid}/test-flag`,
          { is_test: cb.checked });
        toast(cb.checked ? "テストユーザーに設定しました"
          : "テストユーザー扱いを解除しました");
        go("admin");
      } catch (e) {
        toast("失敗: " + e.message);
        cb.checked = !cb.checked;
        cb.disabled = false;
      }
    });
  });

  // 集計フィルタ（管理者/招待ユーザー/テストユーザーを含めるか）。
  // 変更したら状態を保持したまま画面全体を再描画する(2026-08-20)。
  const aggFilterBoxes = [
    ["aggIncludeAdmin", "include_admin"],
    ["aggIncludeInvited", "include_invited"],
    ["aggIncludeTest", "include_test"],
  ];
  aggFilterBoxes.forEach(([elId, key]) => {
    root.querySelector(`#${elId}`).addEventListener("change", (e) => {
      adminAggFilters[key] = e.target.checked;
      go("admin");
    });
  });
}

// --- Settings (API key, model, nickname note, voices, usage) ---------------

// 大分類ごとにチェックボックス化した分野/シーン一覧のHTMLを組み立てる。
// hiddenSet に入っている項目は未チェック(=非表示設定)で描画する。
function fsetGroupsHtml(groups, hiddenSet, prefix) {
  return Object.entries(groups).map(([cat, items]) => `
    <details class="fset-group">
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
  // /api/system/settingsは管理者専用API化されている(2026-08-12・
  // マスク済みAPIキー等を含むため)。非管理者はここで403になり設定画面
  // 自体が開けなくなる不具合が発生していたため、フォールバックする
  // （2026-08-13修正）。値そのものは.admin-onlyカードでのみ使われ、
  // それらは後段でmu.role!=='admin'のとき非表示にされるので実害無い。
  // 6本とも互いに依存が無いため並列実行する(2026-09-07・以前は直列6回で
  // 設定画面の表示までの待ち時間が積み上がっていた、アプリ内で最も
  // 直列awaitが多い画面だった)。各々の元々のフォールバック挙動は
  // そのまま維持する。
  const [s, usage, wFacets, sceneGroups, pLevels, us0] = await Promise.all([
    api.get("/api/system/settings").catch(async () => {
      const mu2 = await api.get("/api/system/my-usage");
      return {
        ai_enabled: mu2.ai_enabled, model: "", quality_model: "",
        api_key_masked: "", host: "", port: "",
        tokushoho_ready: true, version: mu2.version,
      };
    }),
    // /api/system/usage is admin-only (全ユーザー横断の使用量のため); 一般
    // ユーザーは403になるので、その場合は空扱いにしてページ全体は描画する。
    api.get("/api/system/usage").catch(() => ({
      total_cost_usd: 0, today_cost_usd: 0, total_cost_jpy: 0,
      today_cost_jpy: 0, calls: 0, jpy_rate: 0, jpy_as_of: "", recent: [],
    })),
    api.get("/api/words/facets?include_hidden=true"),
    api.get("/api/phrases/scenes?include_hidden=true")
      .then((r) => r.scene_groups || {}),
    api.get("/api/phrases/facets").then((r) => r.range_levels || []),
    api.get("/api/system/user-settings").then((r) => r.settings || {}),
  ]);
  const domainGroups = wFacets.domain_groups || {};
  const wLevels = wFacets.range_levels || [];
  const hiddenDomains = new Set(us0.hidden_domains || []);
  const hiddenScenes = new Set(us0.hidden_scenes || []);
  const dfw = us0.default_word_filters || {};
  const dfp = us0.default_phrase_filters || {};
  const lvOptsHtml = (levels, cur) => '<option value="">--</option>'
    + levels.map((l) =>
      `<option ${l === cur ? "selected" : ""}>${escapeHtml(l)}</option>`)
      .join("");
  root.innerHTML = `
    <h1>設定 <span class="muted" id="roleBadge"></span> ${infoIcon(
      "help-settings",
      "プロフィール・チャージ・表示する分野やシーン・既定フィルター・" +
      "詳細設定(習熟度の基準など)・AIの声・お問い合わせをまとめた画面です。" +
      "分野・シーンや既定フィルターなどは、各カードの「保存」ボタンを" +
      "押すまで反映されません。")}</h1>
    <p class="sub">学習者プロフィールと音声・AIの設定。</p>
    <div id="adminMemoSlot"></div>
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
      <h2>🛟 設定のバックアップ</h2>
      <p class="muted">設定を保存するたび、直前の内容を自動で残します
        （直近3件まで）。誤操作等で設定がおかしくなったら、ここから
        戻せます。</p>
      <div id="settingsBackupWrap" class="mt">
        <p class="muted">読み込み中…</p>
      </div>
    </div>
    <div class="card" id="chargeCard" style="display:none">
      <h2>💳 チャージ</h2>
      <p>現在の残高: <b id="ptBalance">-</b> pt</p>
      ${state.canPaypayCharge ? `
      <div id="paypayChargeBlock" class="mt">
        <h3 style="margin-bottom:4px">① PayPayで購入(即時反映)</h3>
        <p class="muted" style="margin-top:0">支払いが完了すると、キーの
          発行・入力なしでそのまま残高に反映されます。</p>
        <div class="row">
          <button class="btn good" id="pp_pay_800">¥800で購入</button>
          <button class="btn good" id="pp_pay_8000">¥8000で購入</button>
        </div>
        <p class="muted" style="margin:4px 0 0;font-size:12px">
          ¥800→800pt付与 / ¥8000→<b>8,800pt付与(+10%お得)</b>
          （BASEでの購入と同じ付与数です）</p>
        <p class="muted mt" id="pp_out"></p>
        ${state.showPaypayDevTools ? `
        <details class="mt">
          <summary>✅ テスト確認チェックリスト
            <span id="pp_checklist_progress" class="muted"></span></summary>
          <p class="muted">実際に支払いを試すときに確認しておきたい項目
            です。チェック状態はこの端末のブラウザにのみ保存されます。
            「自動」印は下のボタンでその場検証できます(結果は正常/異常
            とも記録されます)。</p>
          <div class="row">
            <button class="btn ghost" id="pp_selfcheck_btn">🔍 自動チェックを実行</button>
          </div>
          <p class="muted mt" id="pp_selfcheck_err"></p>
          <div id="pp_checklist_items" class="mt"></div>
        </details>
        ` : ""}
      </div>
      <hr class="mt" />
      <h3 style="margin-bottom:4px">② BASEで購入してキーを入力</h3>
      ` : ""}
      <div class="row">
        <input id="ck_key" name="charge_key" type="text"
          autocomplete="one-time-code" autocapitalize="characters"
          autocorrect="off" spellcheck="false" data-lpignore="true"
          data-1p-ignore="true"
          placeholder="XXXX-XXXXXXX-X-XXXX" style="width:220px" />
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
    <div class="card">
      <h2>表示する分野・シーン ${infoIcon("help-visible-domains", VISIBLE_DOMAINS_HELP)}</h2>
      <p class="muted">興味のない分野・シーンのチェックを外すと、英単語/
        フレーズ画面のフィルター候補から消えます（データ自体は削除され
        ません・いつでも再表示できます）。<b>チェックの変更はこのカードの
        「保存」を押すまで反映されません。</b></p>
      <details class="fset-section fset-section-w mt">
        <summary><h3 style="display:inline">🔤 英単語の分野</h3></summary>
        <div class="row mt">
          <button type="button" class="btn ghost" id="fset_w_all1">全てON</button>
          <button type="button" class="btn ghost" id="fset_w_all0">全てOFF</button>
          <button type="button" class="btn ghost" id="fset_w_reset">デフォルトに戻す</button>
        </div>
        <div class="fset-wrap mt" id="fset_words">
          ${fsetGroupsHtml(domainGroups, hiddenDomains, "w")}
        </div>
      </details>
      <details class="fset-section fset-section-p mt">
        <summary><h3 style="display:inline">💬 フレーズのシーン</h3></summary>
        <div class="row mt">
          <button type="button" class="btn ghost" id="fset_p_all1">全てON</button>
          <button type="button" class="btn ghost" id="fset_p_all0">全てOFF</button>
          <button type="button" class="btn ghost" id="fset_p_reset">デフォルトに戻す</button>
        </div>
        <div class="fset-wrap mt" id="fset_phrases">
          ${fsetGroupsHtml(sceneGroups, hiddenScenes, "p")}
        </div>
      </details>
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

      <hr class="mt" />
      <h3>🧠 習熟度(mastery)・忘却曲線の設定 ${infoIcon("mastery-settings",
        "忘却曲線とは、時間が経つと習熟度ptが少しずつ自動で減っていく仕組み" +
        "です。復習しないと「覚えた」から外れていきます。「卒業」にした" +
        "項目は減りません。減らす量を0にするとオフにできます。")}</h3>
      <p class="muted">単語・フレーズの習熟度は0〜満点のpt(ポイント)で管理し、
        設定したpt以上を「覚えた」と判定します。「覚えた」「うろ覚え」
        ボタンでの加点量、時間経過で自然に減っていく忘却曲線の強さも
        ここで調整できます。ここでの変更は単語帳・フレーズ帳・
        フラッシュカードなど、アカウント全体の学習機能に共通で反映されます
        （単語帳/フレーズ帳ごとには設定しません）。数値は保存時に安全な
        範囲へ自動調整されます。</p>
      <div class="grid cols-2 mt">
        <label>満点(上限pt・100〜300): <input id="advMasteryMax"
          type="number" min="100" max="300" style="width:80px" /></label>
        <label>「覚えた」と判定するpt: <input id="advMasteredThreshold"
          type="number" min="10" style="width:80px" /></label>
        <label>「覚えた」ボタンでの加点(pt): <input id="advKnownBonus"
          type="number" min="1" max="300" style="width:80px" /></label>
        <label>「うろ覚え」ボタンでの加点(pt): <input id="advVagueBonus"
          type="number" min="1" max="300" style="width:80px" /></label>
      </div>
      <p class="mt">忘却曲線: <input id="advDecayAmount" type="number"
          min="0" max="100" style="width:70px" />pt を
        <input id="advDecayIntervalDays" type="number" min="1" max="90"
          style="width:70px" />日ごとに自動で減らす
        （0にすると忘却曲線をオフにできます）</p>
      <div class="row mt">
        <button class="btn good" id="advMasterySave">保存</button>
        <button class="btn ghost" id="advMasteryReset">既定値に戻す</button>
        <span class="muted" id="advMasteryOut"></span>
      </div>
    </div>
    <div class="card" id="securityCard" style="display:none">
      <h2>🔒 セキュリティ</h2>
      <p class="muted">端末を共有した後や、身に覚えのないログイン状態に
        気づいたときは、全端末から一括でログアウトできます
        （このボタンを押した端末も再ログインが必要になります）。</p>
      <button class="btn bad" id="logoutAllBtn">全端末からログアウト</button>
      <span class="muted mt" id="logoutAllOut"></span>
    </div>
    <div class="card" id="withdrawCard" style="display:none">
      <h2>🚪 退会</h2>
      <p class="muted">アカウントを削除します。学習履歴・単語帳・フレーズ帳・
        AI会話ログは削除され、登録メールアドレス等の個人情報も消去します
        （元に戻せません）。差し支えなければ理由を教えてください
        （任意・今後の改善に使わせていただきます）。</p>
      <div id="withdrawReasons" class="mt">${[
        ["not_enough_features", "使いたい機能が足りなかった"],
        ["hard_to_use", "操作が分かりにくかった"],
        ["bugs", "表示・音声などの不具合があった"],
        ["achieved_goal", "目的の学習を達成できた"],
        ["switching", "他のサービス・教材に移る"],
        ["price", "料金が合わなかった"],
        ["not_using", "最近あまり使わなくなった"],
        ["other", "その他"],
      ].map(([k, label]) => `
        <label class="toggle" style="display:block">
          <input type="checkbox" class="wd-reason" value="${k}" /> ${escapeHtml(label)}
        </label>`).join("")}</div>
      <textarea id="wd_detail" class="mt" style="min-height:60px"
        placeholder="自由記入(任意)"></textarea>
      <div class="row mt">
        <button class="btn bad" id="wd_submit">退会する</button>
        <span class="muted" id="wd_out"></span>
      </div>
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
        <input id="iq_email" placeholder="メール(必須・返信先)"
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
      <p><a href="/static/about.html">このアプリについて
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
      <table><thead><tr><th>日時(JST)</th><th>機能</th><th>モデル</th>
        <th>in</th><th>out</th><th>費用</th></tr></thead><tbody>
        ${usage.recent.map((r) => `<tr><td class="muted">${fmtDateJST(r.created_at)}</td>
          <td>${r.feature}</td><td>${r.model}</td><td>${r.prompt_tokens}</td>
          <td>${r.output_tokens}</td><td>$${r.cost_usd.toFixed(4)}</td></tr>`)
          .join("")}</tbody></table>
    </div>`;

  // 管理者専用「メモ（管）」(外出先での気づき記録用)。
  const settingsMemo = adminMemoWidget({ source: "settings" });
  if (settingsMemo) {
    root.querySelector("#adminMemoSlot").appendChild(settingsMemo);
  }

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
    const email = sq("#iq_email").value.trim();
    if (!content) { toast("内容を入力してください"); return; }
    if (!email || !email.includes("@") || !email.split("@").pop().includes(".")) {
      toast("メールアドレス（返信先）を入力してください"); return;
    }
    try {
      await api.post("/api/inquiries", {
        kind: sq("#iq_kind").value,
        name: sq("#iq_name").value.trim(),
        email,
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
    const mmax = root.querySelector("#advMasteryMax");
    if (mmax) {
      mmax.value = us.mastery_max ?? MASTERY_DEFAULTS.mastery_max;
      root.querySelector("#advMasteredThreshold").value =
        us.mastered_threshold ?? MASTERY_DEFAULTS.mastered_threshold;
      root.querySelector("#advKnownBonus").value =
        us.known_bonus ?? MASTERY_DEFAULTS.known_bonus;
      root.querySelector("#advVagueBonus").value =
        us.vague_bonus ?? MASTERY_DEFAULTS.vague_bonus;
      root.querySelector("#advDecayAmount").value =
        us.decay_amount ?? MASTERY_DEFAULTS.decay_amount;
      root.querySelector("#advDecayIntervalDays").value =
        us.decay_interval_days ?? MASTERY_DEFAULTS.decay_interval_days;
    }
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
    // 退会カード: securityCardと同条件(multiuser時のみ)に加えて、管理者は
    // 隠す(サーバー側もadmin roleの退会を拒否する・唯一の管理者が誤って
    // 退会し管理画面に誰も入れなくなる事故を防ぐ多重防御・2026-09-23)。
    const withdrawCard = root.querySelector("#withdrawCard");
    if (mu && mu.multiuser && mu.role !== "admin" && withdrawCard) {
      withdrawCard.style.display = "";
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

  const advMasterySave = root.querySelector("#advMasterySave");
  if (advMasterySave) advMasterySave.addEventListener("click", async () => {
    const settings = {};
    try { Object.assign(settings,
      (await api.get("/api/system/user-settings")).settings || {}); }
    catch (_) { /* */ }
    const num = (id) => parseInt(root.querySelector(id).value, 10);
    settings.mastery_max = num("#advMasteryMax");
    settings.mastered_threshold = num("#advMasteredThreshold");
    settings.known_bonus = num("#advKnownBonus");
    settings.vague_bonus = num("#advVagueBonus");
    settings.decay_amount = num("#advDecayAmount");
    settings.decay_interval_days = num("#advDecayIntervalDays");
    await api.put("/api/system/user-settings", { settings });
    const out = root.querySelector("#advMasteryOut");
    // 「覚えた」の加点が「覚えた」判定の基準を下回ると、ボタンを押しても
    // 基準に届かない本末転倒になるため警告(保存自体は妨げない・2026-08-18)。
    if (settings.known_bonus < settings.mastered_threshold) {
      out.textContent = "保存しました。ただし「覚えたボタンでの加点」が"
        + "「覚えたと判定するpt」を下回っているため、「覚えた」を押しても"
        + "「覚えた」判定にならない場合があります。ご注意ください。";
      out.style.color = "var(--danger, #e5534b)";
    } else {
      out.textContent = "保存しました（値は安全な範囲に自動調整されます）";
      out.style.color = "";
    }
  });

  const advMasteryReset = root.querySelector("#advMasteryReset");
  if (advMasteryReset) advMasteryReset.addEventListener("click", async () => {
    if (!confirm("習熟度・忘却曲線の設定を既定値に戻しますか？")) return;
    const settings = {};
    try { Object.assign(settings,
      (await api.get("/api/system/user-settings")).settings || {}); }
    catch (_) { /* */ }
    for (const k of ["mastery_max", "mastered_threshold", "known_bonus",
      "vague_bonus", "decay_amount", "decay_interval_days"]) {
      delete settings[k];
    }
    await api.put("/api/system/user-settings", { settings });
    root.querySelector("#advMasteryMax").value = MASTERY_DEFAULTS.mastery_max;
    root.querySelector("#advMasteredThreshold").value =
      MASTERY_DEFAULTS.mastered_threshold;
    root.querySelector("#advKnownBonus").value = MASTERY_DEFAULTS.known_bonus;
    root.querySelector("#advVagueBonus").value = MASTERY_DEFAULTS.vague_bonus;
    root.querySelector("#advDecayAmount").value =
      MASTERY_DEFAULTS.decay_amount;
    root.querySelector("#advDecayIntervalDays").value =
      MASTERY_DEFAULTS.decay_interval_days;
    root.querySelector("#advMasteryOut").textContent = "既定値に戻しました";
  });

  const logoutAllBtn = root.querySelector("#logoutAllBtn");
  if (logoutAllBtn) logoutAllBtn.addEventListener("click", async () => {
    if (!confirm("全端末からログアウトします。この端末も含めて"
      + "再ログインが必要になります。よろしいですか？")) return;
    try { await api.post("/api/auth/logout-all-devices"); }
    catch (_) { /* */ }
    location.href = "/login";
  });

  const wdSubmit = root.querySelector("#wd_submit");
  if (wdSubmit) wdSubmit.addEventListener("click", async () => {
    const out = root.querySelector("#wd_out");
    const reasons = [...root.querySelectorAll(".wd-reason:checked")]
      .map((el) => el.value);
    const detail = root.querySelector("#wd_detail").value.trim();
    if (!reasons.length && !detail) {
      out.textContent = "理由を選択するか、自由記入欄にご記入ください。";
      return;
    }
    if (!confirm("本当に退会しますか？学習履歴・単語帳・フレーズ帳・AI会話"
      + "ログはすべて削除され、元に戻せません。")) return;
    if (!confirm("最終確認です。この操作は取り消せません。退会してよろし"
      + "いですか？")) return;
    out.textContent = "処理中…";
    try {
      await api.post("/api/auth/withdraw", { reasons, detail });
    } catch (e) {
      out.textContent = "退会できませんでした: " + e.message;
      return;
    }
    alert("退会が完了しました。ご利用ありがとうございました。");
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

  // PayPayでの即時チャージ(管理者テスト中・2026-09-02)。作成後は
  // admin_paypay_test.htmlと同じ理由でモバイル判定してdeeplink/urlを
  // 出し分ける(PCブラウザではpaypay://が無反応になるため)。確定は
  // /paypay-charge(templates/paypay_charge.html)がredirect先で行う。
  const ppOut = root.querySelector("#pp_out");
  const startPayPayCharge = async (amountJpy) => {
    if (!ppOut) return;
    ppOut.textContent = "処理を開始しています…";
    try {
      const d = await api.post("/api/paypay/create", { amount_jpy: amountJpy });
      const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
      location.href = (isMobile && d.deeplink) ? d.deeplink : d.url;
    } catch (e) {
      ppOut.textContent = "失敗: " + e.message;
    }
  };
  const pp800 = root.querySelector("#pp_pay_800");
  if (pp800) pp800.addEventListener("click", () => startPayPayCharge(800));
  const pp8000 = root.querySelector("#pp_pay_8000");
  if (pp8000) pp8000.addEventListener("click", () => startPayPayCharge(8000));

  // ✅ テスト確認チェックリスト(2026-09-02・admin_paypay_test.htmlと同じ
  // 内容だが、そちらはURL自体がadmin専用でthis許可リスト対象者
  // (ytsuka-biz1@nyangailab.com等)が開けないため、実際に購入ボタンが
  // あるこの設定画面側にも表示する。「自動」印はapp/routers/
  // paypay_test.pyの/selfcheckを叩く(admin/許可リスト対象者どちらも
  // 実行可)。
  if (root.querySelector("#pp_checklist_items")) {
    const PP_CHECKLIST = [
      { id: 'official-pay', group: 'PayPay公式チェックリスト',
        text: '決済ができる(Get Payment Detailsでstatus=COMPLETEDを確認)' },
      { id: 'official-cancel', group: 'PayPay公式チェックリスト',
        text: '未払いのキャンセルができる(Delete a Code)' },
      { id: 'official-refund', group: 'PayPay公式チェックリスト',
        text: '返金ができる(Refund)' },
      { id: 'official-mobile', group: 'PayPay公式チェックリスト',
        text: 'スマートフォンでPayPayアプリが立ち上がり決済できる(deeplink)' },
      { id: 'official-redirect', group: 'PayPay公式チェックリスト',
        text: 'PayPayアプリでの決済後、加盟店サイトにリダイレクトできる' },
      { id: 'official-backend-status', group: 'PayPay公式チェックリスト',
        text: 'バックエンドのステータスで判定し、画面遷移が無いだけでは'
          + '一律キャンセル・返金しない' },
      { id: 'official-multi-confirm', group: 'PayPay公式チェックリスト',
        text: '確認ボタンを複数回押しても二重付与されない(冪等性)' },
      { id: 'irregular-user-cancel', group: 'イレギュラー操作の確認',
        text: 'PayPayアプリ側で支払いを途中キャンセルした場合、'
          + 'ptが付与されないことを確認' },
      { id: 'irregular-tab-close', group: 'イレギュラー操作の確認',
        text: '支払い完了後にブラウザを閉じて戻ってこなかった場合でも、'
          + '後から正しく付与されることを確認' },
      { id: 'irregular-success-display', group: 'イレギュラー操作の確認',
        text: '正常完了時、「完了しました」と分かりやすく伝わる表示に'
          + 'なっているか確認' },
      { id: 'app-wrong-user', group: '安全性の確認', auto: 'wrong_user_403',
        text: '他ユーザーの支払いを確認できないことを確認' },
      { id: 'app-rate-limit', group: '安全性の確認',
        auto: 'rate_limit_counter',
        text: '購入ボタンの連打制限(1時間10回)が効いていることを確認' },
      { id: 'app-amount', group: '安全性の確認', auto: 'amount_validation',
        text: '任意の金額(¥800/¥8000以外)を送っても拒否されることを確認' },
      { id: 'app-public-flag', group: '安全性の確認', auto: 'public_flag',
        text: '一般公開前に、他の一般ユーザーには見えていないことを確認' },
    ];
    const PP_CHECKLIST_KEY = 'paypaySettingsChecklist:v1';
    const loadPpState = () => {
      try { return JSON.parse(localStorage.getItem(PP_CHECKLIST_KEY) || '{}'); }
      catch (_) { return {}; }
    };
    const savePpState = (s) => {
      try { localStorage.setItem(PP_CHECKLIST_KEY, JSON.stringify(s)); }
      catch (_) { /* ignore */ }
    };
    const renderPpChecklist = () => {
      const state2 = loadPpState();
      let html = '';
      let lastGroup = null;
      for (const item of PP_CHECKLIST) {
        if (item.group !== lastGroup) {
          if (lastGroup !== null) html += '</div>';
          html += `<p class="muted" style="margin:10px 0 4px;font-weight:700">`
            + `${escapeHtml(item.group)}</p><div>`;
          lastGroup = item.group;
        }
        const checked = state2[item.id] ? 'checked' : '';
        const autoBadge = item.auto
          ? ' <span class="pill">自動</span>' : '';
        html += `<label style="display:flex;gap:8px;align-items:flex-start;`
          + `padding:3px 0;font-size:13px;cursor:pointer">`
          + `<input type="checkbox" data-pp-id="${escapeHtml(item.id)}" `
          + `${checked} style="margin-top:2px" />`
          + `<span>${escapeHtml(item.text)}${autoBadge}`
          + `<br><span class="muted" data-pp-note="${escapeHtml(item.id)}">`
          + `</span></span></label>`;
      }
      html += '</div>';
      root.querySelector('#pp_checklist_items').innerHTML = html;
      root.querySelectorAll('[data-pp-id]').forEach((cb) =>
        cb.addEventListener('change', () => {
          const s = loadPpState();
          s[cb.dataset.ppId] = cb.checked;
          savePpState(s);
          updatePpProgress();
        }));
      updatePpProgress();
    };
    const updatePpProgress = () => {
      const s = loadPpState();
      const done = PP_CHECKLIST.filter((i) => s[i.id]).length;
      const el = root.querySelector('#pp_checklist_progress');
      if (el) el.textContent = ` (${done}/${PP_CHECKLIST.length})`;
    };
    renderPpChecklist();
    const ppSelfcheckBtn = root.querySelector('#pp_selfcheck_btn');
    if (ppSelfcheckBtn) ppSelfcheckBtn.addEventListener('click', async () => {
      const errEl = root.querySelector('#pp_selfcheck_err');
      errEl.textContent = '';
      try {
        const d = await api.post('/api/paypay-test/selfcheck', {});
        const s = loadPpState();
        for (const r of d.results) {
          const item = PP_CHECKLIST.find((i) => i.auto === r.key);
          if (!item) continue;
          if (r.ok) s[item.id] = true;
        }
        savePpState(s);
        renderPpChecklist();
        for (const r of d.results) {
          const item = PP_CHECKLIST.find((i) => i.auto === r.key);
          if (!item) continue;
          const noteEl = root.querySelector(`[data-pp-note="${item.id}"]`);
          if (noteEl) {
            noteEl.textContent = (r.ok ? '✅ ' : '❌ ') + r.note;
            noteEl.style.color = r.ok ? '#3ddc84' : '#ff6b6b';
          }
        }
      } catch (e) {
        errEl.textContent = e.message;
      }
    });
  }

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

  // 設定のバックアップ一覧・復元（2026-08-19）。
  async function loadSettingsBackups() {
    const wrap = root.querySelector("#settingsBackupWrap");
    if (!wrap) return;
    wrap.innerHTML = `<p class="muted">読み込み中…</p>`;
    try {
      const res = await api.get("/api/system/user-settings/backups");
      if (!res.backups.length) {
        wrap.innerHTML = `<p class="muted">まだバックアップはありません
          （設定を保存すると次回から残ります）。</p>`;
        return;
      }
      wrap.innerHTML = `<ul class="links">${res.backups.map((b) => `
        <li style="justify-content:space-between; display:flex;
          align-items:center; gap:10px">
          <span>${fmtDateJST(b.created_at)} 時点の設定</span>
          <button class="btn ghost restore-settings-btn" data-id="${b.id}"
            style="padding:3px 10px">この内容に戻す</button>
        </li>`).join("")}</ul>`;
      wrap.querySelectorAll(".restore-settings-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
          if (!confirm("表示中の設定を、選んだ時点の内容に戻します。"
            + "（今の内容も自動でバックアップされるので、やり直せます）"
            + "よろしいですか？")) return;
          btn.disabled = true;
          try {
            await api.post("/api/system/user-settings/restore",
              { backup_id: parseInt(btn.dataset.id, 10) });
            toast("設定を復元しました。画面を再読み込みします。");
            go("settings");
          } catch (e) {
            toast("復元に失敗: " + e.message);
            btn.disabled = false;
          }
        });
      });
    } catch (e) {
      wrap.innerHTML = `<p class="muted">取得失敗: ${escapeHtml(e.message)}</p>`;
    }
  }
  loadSettingsBackups();
}

// --- 単語帳(デッキ) --------------------------------------------------------

export async function decks(root) {
  const [list, facets, summary] = await Promise.all([
    api.get("/api/decks"),
    api.get("/api/words/facets?include_banned=true"),
    api.get("/api/decks/summary"),
  ]);
  root.innerHTML = `
    <h1>単語帳 ${infoIcon("help-deck",
      "自分だけの単語リストを作って学習・出題に使えます。ログインが" +
      "必要で、無料範囲では1個・100語まで、チャージ済みなら個数・語数" +
      "とも無制限です。")}</h1>
    <p class="sub">分野・レベルから自分用の単語帳(デッキ)を作って学習。
      出題方向や忘却曲線・「覚えた」の基準は設定画面の詳細設定で
      アカウント共通に調整できます。
      無料範囲では1個・100語まで、チャージ済みなら個数・件数とも無制限です。</p>
    <div class="card">
      <h2>単語帳 全体の達成率 ${infoIcon("deck-progress", DECK_PROGRESS_HINT)}</h2>
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
          ${chkAllClearHtml("ddomains")}
          <div id="ddomains" class="chkbox">${facets.domains.map((d) =>
            `<label class="chk"><input type="checkbox" value="${escapeHtml(d)}"
              /> ${escapeHtml(d)}</label>`).join("")}</div></div>
        <div><div class="muted">レベル(複数チェック可)</div>
          ${chkAllClearHtml("dlevels")}
          <div id="dlevels" class="chkbox">${facets.levels.map((l) =>
            `<label class="chk"><input type="checkbox" value="${escapeHtml(l)}"
              /> ${escapeHtml(l)}</label>`).join("")}</div></div>
      </div>
      <div class="row mt">
        <label>件数(お任せ): <input id="dlimit" type="number" value="50"
          style="width:80px" min="1" /></label>
        <label class="toggle"><input type="checkbox" id="dlimitAll" />
          全件</label>
      </div>
      <div class="row mt">
        ${state.isAdmin ? `<label class="toggle">
          <input type="checkbox" id="dbanned" />
          🔞 禁止用語も含める</label>` : ""}
        <button class="btn good" id="dcreate">作成</button>
        <span id="dcreateOut" class="muted"></span>
      </div>
      <p class="muted mt">分野・レベルを選ばなければ全体から、件数ぶんランダムに
        「お任せ」で作ります（「全件」を選ぶと件数を無視して該当する
        すべての単語を追加します）。</p>
    </div>
    <div id="deckList" class="mt"></div>`;
  wireChkAllClear(root);
  const dlimitInput = root.querySelector("#dlimit");
  root.querySelector("#dlimitAll").addEventListener("change", (e) => {
    dlimitInput.disabled = e.target.checked;
  });

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
      const card = el(`<div class="card">
        <div class="row" style="justify-content:space-between">
          <b>${escapeHtml(d.name)}</b>
          <span class="muted">${d.mastered}/${d.total} 習得 (${pct}%)</span></div>
        <div class="bar mt"><span style="width:${pct}%"></span></div>
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
      const limitAll = root.querySelector("#dlimitAll").checked;
      const d = await api.post("/api/decks", {
        name: name || "新しい単語帳",
        domains: sels("#ddomains"),
        levels: sels("#dlevels"),
        include_banned: !!root.querySelector("#dbanned")?.checked,
        limit: limitAll ? null
          : (parseInt(root.querySelector("#dlimit").value, 10) || null),
      });
      out.textContent = `作成: ${d.name} (${d.total}語)`;
      go("deck");
    } catch (e) { out.textContent = "失敗: " + e.message; }
  });

  function editDeck(d) {
    openModal("編集: " + d.name, (body) => {
      body.appendChild(el(`<div class="row">
        <label>名前: <input id="en" value="${escapeHtml(d.name)}"
          style="width:200px" /></label></div>`));
      body.appendChild(el(`<p class="muted mt">出題方向・忘却曲線・
        「覚えた」の基準はデッキごとではなく、設定画面の詳細設定で
        アカウント共通に調整します。</p>`));
      const save = el(`<button class="btn good mt">保存</button>`);
      save.addEventListener("click", async () => {
        await api.put("/api/decks/" + d.id, {
          name: body.querySelector("#en").value.trim() || d.name,
        });
        go("deck");
      });
      body.appendChild(save);

      body.appendChild(el(`<hr class="mt" />`));
      body.appendChild(el(`<h3>🎯 分野・レベルで一括追加</h3>`));
      body.appendChild(el(`<div class="row" style="align-items:flex-start">
        <div><div class="muted">分野(複数チェック可)</div>
          ${chkAllClearHtml("addDomains")}
          <div id="addDomains" class="chkbox">${facets.domains.map((c) =>
            `<label class="chk"><input type="checkbox" value="${escapeHtml(c)}"
              /> ${escapeHtml(c)}</label>`).join("")}</div></div>
        <div><div class="muted">レベル(複数チェック可)</div>
          ${chkAllClearHtml("addLevels")}
          <div id="addLevels" class="chkbox">${facets.levels.map((l) =>
            `<label class="chk"><input type="checkbox" value="${escapeHtml(l)}"
              /> ${escapeHtml(l)}</label>`).join("")}</div></div>
      </div>`));
      wireChkAllClear(body);
      const bulkAddBtn = el(
        `<button class="btn good mt">選択した分野・レベルを全て追加</button>`);
      const bulkAddOut = el(`<span class="muted mt"></span>`);
      body.appendChild(bulkAddBtn);
      body.appendChild(bulkAddOut);

      body.appendChild(el(`<hr class="mt" />`));
      body.appendChild(el(`<h3>🔍 単語を検索して個別に追加</h3>`));
      body.appendChild(el(`<input id="addSearch"
        placeholder="英語・日本語で検索（3文字以上）" style="width:260px" />`));
      const addResults = el(`<div id="addResults" class="mt"></div>`);
      body.appendChild(addResults);

      body.appendChild(el(`<hr class="mt" />`));
      body.appendChild(el(`<h3>収録中の単語 (<span id="wcount">…</span>)</h3>`));
      const wlist = el(`<div id="wlist" class="mt"></div>`);
      body.appendChild(wlist);

      let memberIds = new Set();
      const loadWords = async () => {
        const words = await api.get(`/api/decks/${d.id}/words`);
        memberIds = new Set(words.map((w) => w.id));
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

      bulkAddBtn.addEventListener("click", async () => {
        const domains = [...body.querySelectorAll("#addDomains input:checked")]
          .map((o) => o.value);
        const levels = [...body.querySelectorAll("#addLevels input:checked")]
          .map((o) => o.value);
        if (!domains.length && !levels.length) {
          bulkAddOut.textContent = "分野かレベルを1つ以上選んでください。";
          return;
        }
        bulkAddOut.textContent = "追加中…";
        try {
          const res = await api.post(`/api/decks/${d.id}/words`,
            { domains, levels });
          bulkAddOut.textContent = `現在 ${res.total}語（無料範囲では` +
            `合計100語まで）。`;
          loadWords();
        } catch (e) { bulkAddOut.textContent = "失敗: " + e.message; }
      });

      const addSearchInput = body.querySelector("#addSearch");
      let allWordsCache = null;   // 初回検索時にのみ全件取得してキャッシュ
      const runAddSearch = async () => {
        const term = addSearchInput.value.trim();
        addResults.innerHTML = "";
        if (term.length < 3) return;
        if (!allWordsCache) {
          addResults.appendChild(el(`<p class="muted">検索中…</p>`));
          allWordsCache = await api.get("/api/words");
          addResults.innerHTML = "";
        }
        const t = term.toLowerCase();
        const matches = allWordsCache.filter((w) =>
          w.english.toLowerCase().includes(t)
          || (w.japanese || "").toLowerCase().includes(t)).slice(0, 30);
        if (!matches.length) {
          addResults.appendChild(el(`<p class="muted">見つかりません。</p>`));
          return;
        }
        matches.forEach((w) => {
          const inDeck = memberIds.has(w.id);
          const row = el(`<div class="row"
            style="justify-content:space-between;padding:4px 0">
            <span>${escapeHtml(w.english)}
              <span class="muted">${escapeHtml(w.japanese || "")}</span></span>
            <button class="btn ${inDeck ? "ghost" : "good"}" ${
              inDeck ? "disabled" : ""}>${
              inDeck ? "追加済み" : "➕ 追加"}</button></div>`);
          if (!inDeck) {
            row.querySelector("button").addEventListener("click", async () => {
              await api.post(`/api/decks/${d.id}/words`,
                { word_ids: [w.id] });
              loadWords();
              runAddSearch();
            });
          }
          addResults.appendChild(row);
        });
      };
      addSearchInput.addEventListener("input", runAddSearch);

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
    <h1>フレーズ帳 ${infoIcon("help-phrasedeck",
      "自分だけのフレーズリストを作って学習・出題に使えます。ログインが" +
      "必要で、無料範囲では1個・100件まで、チャージ済みなら個数・件数" +
      "とも無制限です。")}</h1>
    <p class="sub">シーン・レベルから自分用のフレーズ帳(デッキ)を作って学習。
      出題方向や忘却曲線・「覚えた」の基準は設定画面の詳細設定で
      アカウント共通に調整できます。
      無料範囲では1個・100件まで、チャージ済みなら個数・件数とも無制限です。</p>
    <div class="card">
      <h2>フレーズ帳 全体の達成率 ${infoIcon("deck-progress", DECK_PROGRESS_HINT)}</h2>
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
          ${chkAllClearHtml("pdscenes")}
          <div id="pdscenes" class="chkbox">${sceneFacets.scenes.map((s) =>
            `<label class="chk"><input type="checkbox" value="${escapeHtml(s)}"
              /> ${escapeHtml(s)}</label>`).join("")}</div></div>
        <div><div class="muted">レベル(複数チェック可)</div>
          ${chkAllClearHtml("pdlevels")}
          <div id="pdlevels" class="chkbox">${levelFacets.range_levels.map((l) =>
            `<label class="chk"><input type="checkbox" value="${escapeHtml(l)}"
              /> ${escapeHtml(l)}</label>`).join("")}</div></div>
      </div>
      <div class="row mt">
        <label>件数(お任せ): <input id="pdlimit" type="number" value="50"
          style="width:80px" min="1" /></label>
        <label class="toggle"><input type="checkbox" id="pdlimitAll" />
          全件</label>
      </div>
      <div class="row mt">
        ${state.isAdmin ? `<label class="toggle">
          <input type="checkbox" id="pdbanned" />
          🔞 禁止用語も含める</label>` : ""}
        <button class="btn good" id="pdcreate">作成</button>
        <span id="pdcreateOut" class="muted"></span>
      </div>
      <p class="muted mt">シーン・レベルを選ばなければ全体から、件数ぶんランダムに
        「お任せ」で作ります（「全件」を選ぶと件数を無視して該当する
        すべてのフレーズを追加します）。</p>
    </div>
    <div id="phraseDeckList" class="mt"></div>`;
  wireChkAllClear(root);
  const pdlimitInput = root.querySelector("#pdlimit");
  root.querySelector("#pdlimitAll").addEventListener("change", (e) => {
    pdlimitInput.disabled = e.target.checked;
  });

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
      const card = el(`<div class="card">
        <div class="row" style="justify-content:space-between">
          <b>${escapeHtml(d.name)}</b>
          <span class="muted">${d.mastered}/${d.total} 習得 (${pct}%)</span></div>
        <div class="bar mt"><span style="width:${pct}%"></span></div>
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
      const limitAll = root.querySelector("#pdlimitAll").checked;
      const d = await api.post("/api/phrase-decks", {
        name: name || "新しいフレーズ帳",
        scenes: sels("#pdscenes"),
        levels: sels("#pdlevels"),
        include_banned: !!root.querySelector("#pdbanned")?.checked,
        limit: limitAll ? null
          : (parseInt(root.querySelector("#pdlimit").value, 10) || null),
      });
      out.textContent = `作成: ${d.name} (${d.total}件)`;
      go("phrasedeck");
    } catch (e) { out.textContent = "失敗: " + e.message; }
  });

  function editDeck(d) {
    openModal("編集: " + d.name, (body) => {
      body.appendChild(el(`<div class="row">
        <label>名前: <input id="pen" value="${escapeHtml(d.name)}"
          style="width:200px" /></label></div>`));
      body.appendChild(el(`<p class="muted mt">出題方向・忘却曲線・
        「覚えた」の基準はデッキごとではなく、設定画面の詳細設定で
        アカウント共通に調整します。</p>`));
      const save = el(`<button class="btn good mt">保存</button>`);
      save.addEventListener("click", async () => {
        await api.put("/api/phrase-decks/" + d.id, {
          name: body.querySelector("#pen").value.trim() || d.name,
        });
        go("phrasedeck");
      });
      body.appendChild(save);

      body.appendChild(el(`<hr class="mt" />`));
      body.appendChild(el(`<h3>🎯 シーン・レベルで一括追加</h3>`));
      body.appendChild(el(`<div class="row" style="align-items:flex-start">
        <div><div class="muted">シーン(複数チェック可)</div>
          ${chkAllClearHtml("paddScenes")}
          <div id="paddScenes" class="chkbox">${sceneFacets.scenes.map((s) =>
            `<label class="chk"><input type="checkbox" value="${escapeHtml(s)}"
              /> ${escapeHtml(s)}</label>`).join("")}</div></div>
        <div><div class="muted">レベル(複数チェック可)</div>
          ${chkAllClearHtml("paddLevels")}
          <div id="paddLevels" class="chkbox">${levelFacets.range_levels.map((l) =>
            `<label class="chk"><input type="checkbox" value="${escapeHtml(l)}"
              /> ${escapeHtml(l)}</label>`).join("")}</div></div>
      </div>`));
      wireChkAllClear(body);
      const pBulkAddBtn = el(
        `<button class="btn good mt">選択したシーン・レベルを全て追加</button>`);
      const pBulkAddOut = el(`<span class="muted mt"></span>`);
      body.appendChild(pBulkAddBtn);
      body.appendChild(pBulkAddOut);

      body.appendChild(el(`<hr class="mt" />`));
      body.appendChild(el(`<h3>🔍 フレーズを検索して個別に追加</h3>`));
      body.appendChild(el(`<input id="paddSearch"
        placeholder="英語・日本語で検索（3文字以上）" style="width:260px" />`));
      const paddResults = el(`<div id="paddResults" class="mt"></div>`);
      body.appendChild(paddResults);

      body.appendChild(el(`<hr class="mt" />`));
      body.appendChild(el(`<h3>収録中のフレーズ (<span id="pcount">…</span>)</h3>`));
      const plist = el(`<div id="plist" class="mt"></div>`);
      body.appendChild(plist);

      let pMemberIds = new Set();
      const loadPhrases = async () => {
        const items = await api.get(`/api/phrase-decks/${d.id}/phrases`);
        pMemberIds = new Set(items.map((p) => p.id));
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

      pBulkAddBtn.addEventListener("click", async () => {
        const scenes = [...body.querySelectorAll("#paddScenes input:checked")]
          .map((o) => o.value);
        const levels = [...body.querySelectorAll("#paddLevels input:checked")]
          .map((o) => o.value);
        if (!scenes.length && !levels.length) {
          pBulkAddOut.textContent = "シーンかレベルを1つ以上選んでください。";
          return;
        }
        pBulkAddOut.textContent = "追加中…";
        try {
          const res = await api.post(`/api/phrase-decks/${d.id}/phrases`,
            { scenes, levels });
          pBulkAddOut.textContent = `現在 ${res.total}件（無料範囲では` +
            `合計100件まで）。`;
          loadPhrases();
        } catch (e) { pBulkAddOut.textContent = "失敗: " + e.message; }
      });

      const paddSearchInput = body.querySelector("#paddSearch");
      let allPhrasesCache = null;
      const runPaddSearch = async () => {
        const term = paddSearchInput.value.trim();
        paddResults.innerHTML = "";
        if (term.length < 3) return;
        if (!allPhrasesCache) {
          paddResults.appendChild(el(`<p class="muted">検索中…</p>`));
          allPhrasesCache = await api.get("/api/phrases");
          paddResults.innerHTML = "";
        }
        const t = term.toLowerCase();
        const matches = allPhrasesCache.filter((p) =>
          p.english.toLowerCase().includes(t)
          || (p.japanese || "").toLowerCase().includes(t)).slice(0, 30);
        if (!matches.length) {
          paddResults.appendChild(el(`<p class="muted">見つかりません。</p>`));
          return;
        }
        matches.forEach((p) => {
          const inDeck = pMemberIds.has(p.id);
          const row = el(`<div class="row"
            style="justify-content:space-between;padding:4px 0">
            <span>${escapeHtml(p.english)}
              <span class="muted">${escapeHtml(p.japanese || "")}</span></span>
            <button class="btn ${inDeck ? "ghost" : "good"}" ${
              inDeck ? "disabled" : ""}>${
              inDeck ? "追加済み" : "➕ 追加"}</button></div>`);
          if (!inDeck) {
            row.querySelector("button").addEventListener("click", async () => {
              await api.post(`/api/phrase-decks/${d.id}/phrases`,
                { phrase_ids: [p.id] });
              loadPhrases();
              runPaddSearch();
            });
          }
          paddResults.appendChild(row);
        });
      };
      paddSearchInput.addEventListener("input", runPaddSearch);

      loadPhrases();
    });
  }
}

// ---------------------------------------------------------------------------
// 🎮 ゲーム(2026-09-03・テストユーザー+管理者限定公開、第一弾はクロス
// ワード)。ハブ→設定→プレイの3段階を、トップレベルのタブは増やさず
// root.innerHTML の差し替えだけで遷移する(go(tab)のフルroot差し替え
// パターンと同じ考え方)。
// ---------------------------------------------------------------------------

// app/routers/games.pyのDEFAULT_WORD_COUNTと対応。
const DEFAULT_WORD_COUNT = 10;

// 2026-09-05ユーザー指示でヒント使用ごとの減点を一度廃止したが、
// 2026-09-06ユーザー指示で「追加ヒントは獲得スコアが減ることがある」
// 仕様に戻した(app/routers/games.pyのCW_HINT_PENALTY_PCT参照・同じ
// 種別を同じクリューで何度使っても減点は1回分だけ)。クリューモードで
// 決まる倍率(CW_CLUE_MODE_OPTSの説明文・CLUE_MODE_SCORE_MULTIPLIER
// 参照)とは別枠で加算される。先頭文字/末尾文字ヒントはマス目にも
// その場で反映される。
// 2026-09-05ユーザー指摘: 「(無料)」という表記は「点数は減らないか」
// という疑問に答えておらず紛らわしい(お金/ポイントの話なのか、得点の
// 話なのか判別できない)。得点に影響しないヒントは何も書かない(=書か
// ないことが「得点減なし」を意味する)。得点に影響する場合だけ
// 「(-10%)」等、影響の内容がわかる表記にする(「答えを見る」は既に
// 「0点」という実際の結果を表示済みなのでそのまま)。
const CW_HINT_LABELS = {
  audio: ["🔊 発音を聞く", "-10%"],
  first_letter: ["🔤 先頭文字", "-10%"],
  last_letter: ["🔡 末尾文字", "-10%"],
  japanese: ["🔎 日本語訳を見る", "-30%"],
  english: ["📖 英語ヒント(例文)", "-20%"],
  reveal: ["🔓 答えを見る", "0点"],
};

// 直近2件の設定(分野/単語帳選択に加え、語数・クリューモード・難易度等
// 設定一式)を覚えておき、設定画面を開いたときに前回の設定をそのまま
// 既定値として復元する(2026-09-05ユーザー要望「前の設定を反映して
// ほしい・記憶しておく」)。加えて「前回」「前々回」を選び直せる表を出す。
// ブラウザごとのローカル保存(localStorage)なので、他端末とは共有され
// ない簡易的な利便性機能(2026-09-03導入時からの方針を踏襲)。
const CW_RECENT_KEY = "cw_recent_sources";
const CW_RECENT_MAX = 2;
const CW_RECENT_LABELS = ["前回", "前々回"];

function cwLoadRecent() {
  try {
    const raw = JSON.parse(localStorage.getItem(CW_RECENT_KEY) || "[]");
    return Array.isArray(raw) ? raw : [];
  } catch {
    return [];
  }
}

function cwSaveRecent(entry) {
  try {
    const list = cwLoadRecent().filter((e) => e.label !== entry.label);
    list.unshift(entry);
    localStorage.setItem(
      CW_RECENT_KEY, JSON.stringify(list.slice(0, CW_RECENT_MAX)));
  } catch { /* localStorage不可(プライベートモード等)は無視 */ }
}

const CW_CLUE_MODE_LABELS = {
  always_ja: "日本語訳モード", always_english: "英英モード",
  always_audio: "音声モード", always_both: "両方モード",
};

// 設定画面のラジオ選択肢を「短いタイトル+補足(小文字・muted)」の2段
// レイアウトで統一して作る(2026-09-05ユーザー指摘「説明文が見づらい
// 長ったらしい・必要十分に」への対応・従来はタイトルの後ろに長い括弧
// 書きが続いていて一行が長くなりすぎていた)。
function cwRadioOpt(name, value, checked, title, desc) {
  return `<label class="cw-radio-opt">
    <input type="radio" name="${name}" value="${value}"
      ${checked ? "checked" : ""}/>
    <span><b>${title}</b>${desc
      ? `<small class="muted">${desc}</small>` : ""}</span>
  </label>`;
}

// 「ヒントの難易度」は独立設定ではなくクリューモード自体が兼ねる
// (2026-09-05ユーザー指示)。各モードの説明にスコア倍率を明記する
// (app/routers/games.pyのCLUE_MODE_SCORE_MULTIPLIER参照)。追加ヒント
// (発音/先頭文字/末尾文字/日本語訳/英語ヒント)による減点は
// CW_HINT_LABELS/CW_HINT_PENALTY_PCT参照(2026-09-06に復活・同じ種別を
// 同じクリューで何度使っても減点は1回分だけ)。
const CW_CLUE_MODE_OPTS = [
  ["always_ja", "日本語訳モード",
    "（常に日本語の意味のヒントが出るので、初めての方でも安心して" +
    "遊べます。スコア倍率0.8倍）"],
  ["always_english", "英英モード",
    "（常に英語の説明がヒントとして出ます。本格的な英語クロスワードに" +
    "近い遊び方です・該当データが無い語は出題から除外されます。" +
    "スコア倍率は等倍）"],
  ["always_audio", "音声モード",
    "（発音を聞いて単語を当てるモードです。聞き取り練習にぴったり。" +
    "スコア倍率は等倍）"],
  ["always_both", "両方モード",
    "（日本語訳・英語ヒントの両方が常に見え、プレイ中いつでも切り替え" +
    "られます。該当データが無い語は出題から除外されます。" +
    "スコア倍率0.9倍）"],
];
// ヒント(各語に常に表示される説明文)の難易度は、中身の手厚さで
// 調整する(2026-09-05ユーザー指示「簡単なヒントは複数のヒントの
// 組み合わせになって難易度が下がる」)。richは訳語/穴埋め文+説明を
// 両方まとめて出す、いちばん手厚い(易しい)選択肢。
const CW_JAPANESE_STYLE_OPTS = [
  ["simple", "訳語のみ", "例: 適切な"],
  ["explanation", "説明文", "AI作成・単語自体は使わない説明"],
  ["hybrid", "ハイブリッド", "穴埋め文/説明を混在・訳語は表示しません"],
  ["rich", "手厚い(易しい)", "訳語+説明を両方まとめて表示"],
];
const CW_ENGLISH_STYLE_OPTS = [
  ["fill_blank", "文章の穴埋め", "例文の対象単語をマスク"],
  ["definition", "語の説明", "AI作成の短い英語の定義"],
  ["hybrid", "ハイブリッド", "穴埋め文/語の説明を混在"],
  ["rich", "手厚い(易しい)", "穴埋め文+語の説明を両方まとめて表示"],
];

// 履歴テーブル・最近の選択ボタン用に、1件の設定を短い要約文にする。
function cwPresetSummary(r) {
  const parts = [r.label || "分野未選択"];
  if (r.wordCount) parts.push(`${r.wordCount}語`);
  if (r.clueMode) parts.push(CW_CLUE_MODE_LABELS[r.clueMode] || r.clueMode);
  if (r.levelMin || r.levelMax) {
    parts.push(`TOEIC${r.levelMin || "下限なし"}〜${r.levelMax || "上限なし"}`);
  }
  return parts.join(" ・ ");
}

export async function games(root) {
  await cwRenderHub(root);
}

async function cwRenderHub(root) {
  let sessions = [];
  try {
    sessions = await api.get("/api/games/crossword/sessions");
  } catch (e) { /* 未許可ユーザーはここで403、下のUIは出さない */ }
  // 完了済みも一覧に出し、見返し/作り直しができるようにする(2026-09-05
  // ユーザー要望「クリアしたものも再開可能」)。保存(ピン留め)は課金
  // ユーザー限定(上限は無料1件/課金10件・_enforce_session_cap参照)。
  root.innerHTML = `
    <h1>🎮 ゲーム ${infoIcon("help-games",
      "単語を使ったミニゲームで遊びながら学べる機能です。" +
      "分野・単語帳から出題範囲を選んで挑戦できます。")}</h1>
    <div class="grid cols-3 mt">
      <div class="card" id="cwCardStart"
        style="cursor:pointer;border-color:var(--accent);border-width:2px">
        <h2>✏️ クロスワード作成${state.isGuest
          ? ` <span class="pill vague">🔒 要登録+課金</span>`
          : (!state.isChargedTier
            ? ` <span class="pill vague">🔒 要課金</span>` : "")}</h2>
        <p class="muted">分野・単語帳から単語を選んで自由に出題。${
          state.isGuest
            ? "ゲストの方は登録(無料)に加えて課金が必要です。"
          : (!state.isChargedTier
            ? "作成のたびにAI利用料が発生するため、課金ユーザー限定です。"
            : "")}</p>
      </div>
      <div class="card" id="cwCardSamples" style="cursor:pointer">
        <h2>🧩 サンプルクロスワード</h2>
        <p class="muted">あらかじめ用意した固定のパズルで手軽に挑戦。
          ログイン不要(ゲストは5個まで)。</p>
      </div>
      <div class="card" id="cwCardRanking" style="cursor:pointer">
        <h2>🏆 ランキング</h2>
        <p class="muted">自分で作ったクロスワードの合計スコアで、他の
          課金ユーザーと比較できます。</p>
      </div>
    </div>
    ${sessions.length ? `<div class="card mt">
      <h3>再開できるゲーム</h3>
      <p class="muted">保存できるのは無料範囲で直近1件・課金ユーザーは
        直近10件まで(古いものから自動的に消えます)。「保存」に
        チェックすると、それ以降も消えずに残ります(課金ユーザー限定・
        保存できるのは最大50件までです)。</p>
      <table class="mt"><thead><tr>
        <th>対象</th><th>状態</th><th>語数</th><th>スコア</th><th>日時</th>
        <th>保存</th><th></th>
      </tr></thead><tbody>${sessions.map((s) => `<tr>
        <td>${escapeHtml(s.source_label || s.source_ref)}</td>
        <td class="muted">${s.status === "completed" ? "完了" : "進行中"}</td>
        <td>${s.word_count ?? "-"}</td>
        <td>${s.score}</td>
        <td class="muted">${escapeHtml(s.created_at)}</td>
        <td><label class="toggle"><input type="checkbox" data-pin="${s.id}"
          ${s.pinned ? "checked" : ""}/></label></td>
        <td>
          <button class="btn ghost" data-resume="${s.id}">${
            s.status === "completed" ? "見る" : "続きから"}</button>
          <button class="btn ghost" data-restart="${s.id}">最初から</button>
        </td>
      </tr>`).join("")}</tbody></table>
    </div>` : ""}
  `;
  root.querySelector("#cwCardSamples")
    .addEventListener("click", () => cwRenderSamples(root));
  root.querySelector("#cwCardStart")
    .addEventListener("click", () => cwRenderSetup(root));
  root.querySelector("#cwCardRanking")
    .addEventListener("click", () => cwRenderRanking(root));
  root.querySelectorAll("[data-resume]").forEach((b) => {
    b.addEventListener("click", () => {
      cwRenderPlay(root, Number(b.dataset.resume));
    });
  });
  root.querySelectorAll("[data-restart]").forEach((b) => {
    b.addEventListener("click", async () => {
      b.disabled = true;
      try {
        // 「画面に合わせる」モードだった場合に備え、その場の画面比を
        // 送っておく(screen_fitでないセッションではサーバー側で無視
        // される・_create_crossword_session参照)。
        const session = await api.post(
          `/api/games/crossword/${b.dataset.restart}/restart`,
          { screen_aspect: window.innerWidth / window.innerHeight });
        cwRenderPlay(root, session.session_id, session);
      } catch (e) {
        toast(e.message || "作り直しに失敗しました。");
        b.disabled = false;
      }
    });
  });
  root.querySelectorAll("[data-pin]").forEach((cb) => {
    cb.addEventListener("change", async () => {
      const wanted = cb.checked;
      try {
        await api.post(`/api/games/crossword/${cb.dataset.pin}/pin`,
          { pinned: wanted });
      } catch (e) {
        cb.checked = !wanted;
        toast(e.message || "保存の切り替えに失敗しました。");
      }
    });
  });
}

// クロスワードのスコアランキング(2026-09-06新設)。今月/トータルの
// 2種類、上位10位+自分の順位(圏外なら別枠で表示)。課金ユーザーのみが
// 集計対象・サンプルクロスワードのスコアは対象外(games.py
// crossword_ranking参照)。
async function cwRenderRanking(root, period) {
  period = period === "total" ? "total" : "month";
  root.innerHTML = `<p class="muted">読み込み中…</p>`;
  let data;
  try {
    data = await api.get(`/api/games/crossword/ranking?period=${period}`);
  } catch (e) {
    root.innerHTML = `<div class="card">読み込みに失敗しました: ${
      escapeHtml(e.message || "")}</div>`;
    return;
  }
  const rankRow = (e) => `<tr${e.is_me ? ' style="font-weight:bold"' : ""}>
    <td>${e.rank}</td>
    <td>${escapeHtml(e.display)}${e.is_me ? ` <span class="pill">自分</span>` : ""}</td>
    <td>${e.total_score}</td>
  </tr>`;
  root.innerHTML = `
    <div class="row">
      <button type="button" class="btn ghost" id="cwRankingBack">
        ← ゲームメニューに戻る</button>
    </div>
    <h1 class="mt">🏆 クロスワード ランキング ${infoIcon("help-cw-ranking",
      "自分で作ったクロスワードの合計スコアのランキングです。集計対象は"
      + "課金ユーザーのみ、サンプルクロスワードのスコアは対象外です。"
      + "他の方の名前は表示されません(ユーザー名の頭文字のみ)。")}</h1>
    <div class="sample-gate-banner">
      ⚠️ このランキングは<b>課金ユーザーのみ</b>が集計対象です。また
      <b>サンプルクロスワードのスコアは対象外</b>で、「✏️ クロスワード
      作成」で自分で作ったゲームのスコアのみ合計されます。他の方の
      お名前は表示されません(ユーザー名の頭文字のローマ字1文字のみ
      表示)。
    </div>
    <div class="row mt" style="align-items:center">
      <button type="button" class="btn ${period === "month" ? "primary" : "ghost"}"
        id="cwRankMonth">今月のランキング</button>
      <button type="button" class="btn ${period === "total" ? "primary" : "ghost"}"
        id="cwRankTotal">トータルランキング</button>
    </div>
    ${data.top.length ? `<table class="mt"><thead><tr>
      <th>順位</th><th>ユーザー</th><th>合計スコア</th>
    </tr></thead><tbody>${data.top.map(rankRow).join("")}</tbody></table>`
      : `<p class="muted mt">まだこの期間のランキングデータがありません。</p>`}
    ${data.me && !data.me_in_top ? `<p class="muted mt">あなたの順位:</p>
      <table><tbody>${rankRow(data.me)}</tbody></table>`
      : (!data.me ? `<p class="muted mt">あなたはまだ集計対象外です
        (課金ユーザーになると、自分で作ったゲームのスコアが集計対象に
        なります)。</p>` : "")}
  `;
  root.querySelector("#cwRankingBack")
    .addEventListener("click", () => cwRenderHub(root));
  root.querySelector("#cwRankMonth")
    .addEventListener("click", () => cwRenderRanking(root, "month"));
  root.querySelector("#cwRankTotal")
    .addEventListener("click", () => cwRenderRanking(root, "total"));
}

// サンプルクロスワード一覧(2026-09-05・集客用に一般公開する固定パズル)。
// ゲスト含め誰でも呼べるAPI(/api/games/crossword/samples)を使う。
// 導線(「ゲーム」タブ自体の表示)はテストユーザー限定のまま
// (app.js state.canUseGames)なので、この画面自体は実装済みでも
// 一般ユーザーはまだ辿り着けない(2026-09-05ユーザー指示「開放は説明書
// 等と一緒にするので、実装は本番通り・導線だけ隠す」)。
async function cwRenderSamples(root) {
  root.innerHTML = `<p class="muted">読み込み中…</p>`;
  let data;
  try {
    data = await api.get("/api/games/crossword/samples");
  } catch (e) {
    root.innerHTML = `<div class="card">読み込みに失敗しました: ${
      escapeHtml(e.message || "")}</div>`;
    return;
  }
  const { samples, play_limit: limit, played_count: played, tier } = data;
  const statusText = tier === "charged"
    ? "全部のサンプルが遊べます。保存(ピン留め)は10件まで。"
    : tier === "guest"
    ? `ゲストとして遊べます(残り${Math.max(limit - played, 0)}/${limit}個)。` +
      "登録者限定のサンプルは、ログイン(無料)すると遊べるようになります。"
    : `無料会員として遊べます(残り${Math.max(limit - played, 0)}/${limit}個)。` +
      "保存(ピン留め)は5件まで。チャージすると保存が10件までになります。";
  const levelText = (s) => (s.level_min || s.level_max)
    ? `TOEIC ${s.level_min || "下限なし"}〜${s.level_max || "上限なし"}` : "";
  const card = (s) => `<div class="card cw-sample-card" data-sample="${s.id}"
      style="cursor:${s.guest_locked ? "default" : "pointer"}">
    <h3>${escapeHtml(s.title)}${
      s.guest_locked ? ` <span class="pill vague">🔒 登録した方のみ</span>` : ""
    }${
      s.already_played ? ` <span class="pill vague">プレイ済み</span>` : ""
    }</h3>
    <p class="muted">${escapeHtml(s.description || "")}</p>
    <p class="muted">${s.word_count}語${
      levelText(s) ? ` ・ ${escapeHtml(levelText(s))}` : ""}</p>
    <p>${(s.domains || "").split(",").filter(Boolean).map((d) =>
      `<span class="pill">${escapeHtml(d)}</span>`).join(" ")}</p>
    <button type="button" class="btn ${s.guest_locked ? "ghost" : "primary"} mt"
      ${s.guest_locked ? "disabled" : ""}>${
      s.guest_locked ? "🔒 登録した方のみ"
        : s.already_played ? "🔁 もう一度プレイ" : "▶️ プレイする"}</button>
  </div>`;
  root.innerHTML = `
    <div class="row">
      <button type="button" class="btn ghost" id="cwSamplesBack">
        ← ゲームメニューに戻る</button>
    </div>
    <h1>🧩 サンプルクロスワード ${infoIcon("help-cw-samples",
      "あらかじめ用意した固定のクロスワードです。誰でも(ログイン不要で"
      + "も)遊べます。同じサンプルの再プレイは何度でも無料です。")}</h1>
    <p class="muted">${statusText}</p>
    <div class="row" style="align-items:center">
      <label class="toggle"><input type="checkbox" id="cwSampleBlockCat"/>
        未解答マスを猫にする</label>
      <span class="muted">(既定はオン。猫にしたくなければ
        チェックを外してください)</span>
    </div>
    ${samples.length ? `<div class="grid cols-3 mt">
      ${samples.map(card).join("")}
    </div>` : `<p class="muted">現在サンプルはありません。</p>`}
  `;
  root.querySelector("#cwSamplesBack")
    .addEventListener("click", () => cwRenderHub(root));
  const sampleBlockCat = root.querySelector("#cwSampleBlockCat");
  sampleBlockCat.checked = cwCatPrefGet(true, "block");
  sampleBlockCat.addEventListener("change", () => {
    cwCatPrefSet(true, "block", sampleBlockCat.checked);
  });
  root.querySelectorAll("[data-sample]").forEach((elm) => {
    const btn = elm.querySelector("button");
    if (btn.disabled) return;  // 登録者限定(guest_locked)は押しても何もしない
    btn.addEventListener("click", async () => {
      btn.disabled = true;
      try {
        const session = await api.post(
          `/api/games/crossword/samples/${elm.dataset.sample}/start`, {});
        cwRenderPlay(root, session.session_id, session);
      } catch (e) {
        toast(e.message || "開始できませんでした。");
        btn.disabled = false;
      }
    });
  });
}

// クロスワード生成の所要時間を語数/モードから概算し、進捗バーを動かす
// (2026-09-06ユーザー要望「語数から推測される最大所要時間×1.3でバーを
// 動かせば、バーが100%なのにまだ待たされる体験を減らせる」)。表は
// 実測(語数{3,5,10,20,40,50}×分野条件3パターンの計18件、always_both・
// english_style=japanese_style=rich=最もAI負荷が高い組み合わせ)での
// 各語数ごとの最大値(3語分野中の最大値等)。中間の語数は線形補間する。
// AI不要(fill_blank/simple等)なら盤面生成のみでほぼ即時(1.5秒と仮定)。
const CW_MAX_SECONDS_BOTH_PHASES = [
  [3, 17.3], [5, 11.8], [10, 16.9], [20, 18.1], [40, 22.5], [50, 30.2],
];
function cwMaxSecondsBothPhases(wordCount) {
  const pts = CW_MAX_SECONDS_BOTH_PHASES;
  if (wordCount <= pts[0][0]) return pts[0][1];
  if (wordCount >= pts[pts.length - 1][0]) return pts[pts.length - 1][1];
  for (let i = 0; i < pts.length - 1; i++) {
    const [x0, y0] = pts[i], [x1, y1] = pts[i + 1];
    if (wordCount >= x0 && wordCount <= x1) {
      return y0 + (y1 - y0) * (wordCount - x0) / (x1 - x0);
    }
  }
  return pts[pts.length - 1][1];
}
function cwEstimateSeconds(clueMode, englishStyle, japaneseStyle, wordCount) {
  const wantsJa = clueMode === "always_ja" || clueMode === "always_both";
  const wantsEn = clueMode === "always_english" || clueMode === "always_both";
  const jaNeedsAi = wantsJa
    && ["explanation", "hybrid", "rich"].includes(japaneseStyle);
  const enNeedsAi = wantsEn
    && ["definition", "hybrid", "rich"].includes(englishStyle);
  const aiPhases = (state.aiEnabled === false) ? 0
    : (jaNeedsAi ? 1 : 0) + (enNeedsAi ? 1 : 0);
  if (aiPhases === 0) return 1.5;
  const bothMax = cwMaxSecondsBothPhases(wordCount);
  return aiPhases === 2 ? bothMax : bothMax / 1.8;
}

// cwEstimateSecondsは実測の「最大値」ベースの見積もりなので、そこから
// さらに×1.3かけて0→99%まで進め、実際の完了時にcompleteFn側で100%に
// する(2026-09-06ユーザー指示「語数から推測される最大所要時間×1.3」)。
// バーが先に100%へ到達して「まだ待たされる」体験を避けるため、99%
// までしか自動では進めない。
function cwStartProgressBar(root, estimateSeconds) {
  const wrap = root.querySelector("#cwProgressWrap");
  const bar = root.querySelector("#cwProgressBar");
  if (!wrap || !bar) return () => {};
  const durationMs = Math.max(1000, estimateSeconds * 1.3 * 1000);
  const t0 = performance.now();
  wrap.style.display = "";
  bar.style.width = "0%";
  let raf = 0;
  const tick = () => {
    const pct = Math.min(99, ((performance.now() - t0) / durationMs) * 100);
    bar.style.width = pct + "%";
    raf = requestAnimationFrame(tick);
  };
  raf = requestAnimationFrame(tick);
  return (finished) => {
    cancelAnimationFrame(raf);
    if (finished) {
      bar.style.width = "100%";
      setTimeout(() => { wrap.style.display = "none"; }, 300);
    } else {
      wrap.style.display = "none";
    }
  };
}

async function cwRenderSetup(root, preset) {
  const [facets, decks] = await Promise.all([
    api.get("/api/words/facets"),
    api.get("/api/decks").catch(() => []),
  ]);
  const domainGroups = facets.domain_groups || {};
  const recent = cwLoadRecent();
  // 明示的なpreset(履歴の「この設定で作る」)が無ければ、前回使った設定を
  // 既定値として自動復元する(2026-09-05ユーザー要望「前の設定を反映して
  // ほしい・記憶しておく」)。
  const effective = preset || recent[0] || null;
  const isDeck = effective?.sourceType === "deck";
  const selectedDomains = new Set(
    effective?.sourceType === "domain" ? effective.domains || [] : []);
  const initialCategory = effective?.majorCategory || "";
  const wc = effective?.wordCount || DEFAULT_WORD_COUNT;
  // 語数の選択肢はシンプルな固定リストにする(2026-09-05ユーザー指示)。
  const WORD_COUNT_OPTS = [3, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50];
  const clueMode = effective?.clueMode || "always_ja";
  const englishStyle = effective?.englishStyle || "fill_blank";
  const japaneseStyle = effective?.japaneseStyle || "simple";
  const compact = effective?.compact || false;
  const screenFit = effective?.screenFit || false;
  const answerDifficulty = effective?.answerDifficulty || "normal";
  const catOpts = ['<option value="">全カテゴリ</option>']
    .concat(Object.keys(domainGroups).map((c) => `<option
      ${c === initialCategory ? "selected" : ""}>${escapeHtml(c)}</option>`))
    .join("");
  const lvOpts = (min) => '<option value="">指定なし</option>'
    + (facets.range_levels || []).map((l) => `<option
      ${l === (min ? effective?.levelMin : effective?.levelMax)
        ? "selected" : ""}>${escapeHtml(l)}</option>`).join("");

  root.innerHTML = `
    <button type="button" class="btn ghost" id="cwBack">
      ← ゲーム一覧に戻る</button>
    <h1 class="mt">🧩 クロスワード - 設定 ${infoIcon("help-cw-setup",
      "分野または単語帳から単語を選び、AIがクロスワードを作ります。語数・" +
      "盤面の詰め方・回答の難易度・ヒントの出し方を選べます。作成のたびに" +
      "AI利用料が発生するため課金ユーザー限定です。最近使った設定は" +
      "「この設定で作る」で再利用できます。")}</h1>
    ${state.isGuest ? `<div class="sample-gate-banner">
      ⚠️ この機能(自分で作る)はご登録(無料)に加えて課金が必要です
      (作成のたびにAI利用料が実際に発生するため)。
      ここで設定してもスタート時にエラーになります。
      <a href="/login#signup">登録(無料)はこちら</a>の上、設定画面から
      チャージいただくか、無料でも遊べるサンプルを下記にご用意して
      います。
    </div>
    <div class="row mt">
      <button type="button" class="btn ghost" id="cwGoSamplesFromSetup">
        🧩 サンプルクロスワードを見る</button>
    </div>` : (!state.isChargedTier ? `<div class="sample-gate-banner">
      ⚠️ この機能(自分で作る)は課金ユーザー限定です。作成のたびに
      AI利用料が実際に発生するため、無料登録だけでは開放していません。
      ここで設定してもスタート時にエラーになります。
      設定画面からチャージいただくか、登録済みなら無料で遊べる
      サンプルを下記にご用意しています。
    </div>
    <div class="row mt">
      <button type="button" class="btn ghost" id="cwGoSettingsFromSetup">
        ⚙️ 設定画面でチャージする</button>
      <button type="button" class="btn ghost" id="cwGoSamplesFromSetup">
        🧩 サンプルクロスワードを見る</button>
    </div>` : "")}
    ${recent.length ? `<table class="cw-recent-table mt"><tbody>
      ${recent.map((r, i) => `<tr>
        <td class="muted">${CW_RECENT_LABELS[i] || ""}</td>
        <td>${escapeHtml(cwPresetSummary(r))}</td>
        <td><button type="button" class="btn ghost"
          data-recent="${i}">この設定で作る</button></td>
      </tr>`).join("")}
    </tbody></table>` : ""}
    <div class="card mt">
      <div class="row">
        <label><input type="radio" name="cwSource" value="domain"
          ${isDeck ? "" : "checked"}/> 分野から選ぶ</label>
        <label><input type="radio" name="cwSource" value="deck"
          ${isDeck ? "checked" : ""}/> 単語帳から選ぶ</label>
      </div>
      <div id="cwDomainBlock" class="mt" ${isDeck ? 'style="display:none"' : ""}>
        <div class="row" style="align-items:center">
          <select id="cwCategory" title="大分類">${catOpts}</select>
          <span class="cdrop">
            <button type="button" class="btn ghost" id="cwDomainBtn">
              分野: 全て ▾</button>
            <div class="cdrop-panel" id="cwDomainPanel"></div>
          </span>
        </div>
        <div class="row mt" style="align-items:center">
          <span class="muted">難易度(TOEIC目安)</span>
          <select id="cwLevelMin">${lvOpts(true)}</select>
          <span class="muted">〜</span>
          <select id="cwLevelMax">${lvOpts(false)}</select>
        </div>
        <p class="muted mt" id="cwDomainCountWarn" style="display:none"></p>
      </div>
      <div id="cwDeckBlock" class="mt" ${isDeck ? "" : 'style="display:none"'}>
        ${decks.length ? `<select id="cwDeck">
          <option value="">選択してください</option>
          ${decks.map((d) => `<option value="${d.id}"
            ${isDeck && effective.deckId === d.id ? "selected" : ""}>
            ${escapeHtml(d.name)}(${d.total ?? "?"}語)</option>`)
            .join("")}
        </select>` : `<p class="muted">単語帳がありません。
          先に単語帳を作ってください。</p>`}
        <p class="muted mt" id="cwDeckCountInfo" style="display:none"></p>
      </div>
      <div class="row mt" style="align-items:center">
        <label>語数:</label>
        <select id="cwWordCount">
          ${WORD_COUNT_OPTS.map((n) =>
            `<option value="${n}" ${n === wc ? "selected" : ""}>${n}語</option>`
          ).join("")}
        </select>
        <span class="muted">(既定10語)</span>
      </div>
      <div class="cw-optgroup mt">
        <div class="cw-optgroup-title">パズルの詰め方</div>
        <div class="cw-radio-col">
          ${cwRadioOpt("cwShapeMode", "0", !compact && !screenFit, "普通",
            "交差(クロス)の多さを優先して配置します")}
          ${cwRadioOpt("cwShapeMode", "1", compact && !screenFit,
            "コンパクト(面積優先)",
            "できるだけ盤面の面積が小さくなるよう配置します")}
          ${cwRadioOpt("cwShapeMode", "screen", screenFit,
            "画面に合わせる(縦横比を考慮)",
            "今の画面の縦横比に近い形の盤面にします" +
            "(可能な範囲での近似・スマホ縦持ちなら縦長に)")}
        </div>
      </div>
      <div class="cw-optgroup mt">
        <div class="cw-optgroup-title">回答の難易度（不正解時にどれだけ
          ヒントが出るか）</div>
        <div class="cw-radio-col">
          ${cwRadioOpt("cwAnswerDifficulty", "easy",
            answerDifficulty === "easy", "低",
            "4割(40%)以上文字が合っていれば、合っている文字を表示" +
            "(1文字抜け・余分があってもズレを補正して判定)")}
          ${cwRadioOpt("cwAnswerDifficulty", "normal",
            answerDifficulty === "normal", "中(既定)",
            "6割(60%)以上文字が合っていれば、合っている文字を表示" +
            "(1文字抜け・余分があってもズレを補正して判定)")}
          ${cwRadioOpt("cwAnswerDifficulty", "hard",
            answerDifficulty === "hard", "高",
            "先頭文字が合っている場合のみ表示(それ以外は開示なし)")}
        </div>
      </div>
      <div class="row mt" style="align-items:center">
        <label class="toggle"><input type="checkbox" id="cwBlockCat"/>
          未解答マスを猫にする</label>
        <span class="muted">(既定はオン。猫にしたくなければ
          チェックを外してください)</span>
      </div>
      <div class="cw-optgroup mt">
        <div class="cw-optgroup-title">クリューモード（各問題のヒントの
          出し方）</div>
        <div class="cw-radio-col">
          ${CW_CLUE_MODE_OPTS.map(([v, t, d]) => cwRadioOpt(
            "cwClueMode", v, clueMode === v, t, d)).join("")}
        </div>
      </div>
      <div class="cw-optgroup mt" id="cwJapaneseStyleBlock"
        ${["always_ja", "always_both"].includes(clueMode)
          ? "" : 'style="display:none"'}>
        <div class="cw-optgroup-title">日本語ヒントのスタイル</div>
        <div class="cw-radio-col">
          ${CW_JAPANESE_STYLE_OPTS.map(([v, t, d]) => cwRadioOpt(
            "cwJapaneseStyle", v, japaneseStyle === v, t, d)).join("")}
        </div>
      </div>
      <div class="cw-optgroup mt" id="cwEnglishStyleBlock"
        ${["always_english", "always_both"].includes(clueMode)
          ? "" : 'style="display:none"'}>
        <div class="cw-optgroup-title">英語ヒントのスタイル</div>
        <div class="cw-radio-col">
          ${CW_ENGLISH_STYLE_OPTS.map(([v, t, d]) => cwRadioOpt(
            "cwEnglishStyle", v, englishStyle === v, t, d)).join("")}
        </div>
      </div>
      <button class="btn primary mt" id="cwStart" ${
        (state.isGuest || !state.isChargedTier) ? "disabled" : ""}>${
        state.isGuest ? "🔒 スタート(要登録+課金)"
        : (!state.isChargedTier ? "🔒 スタート(要課金)" : "スタート")
      }</button>
      <div class="bar mt" id="cwProgressWrap" style="display:none">
        <span id="cwProgressBar" style="width:0%"></span>
      </div>
      <p class="muted mt" id="cwError" style="display:none"></p>
    </div>
  `;
  root.querySelector("#cwBack")
    .addEventListener("click", () => cwRenderHub(root));
  root.querySelector("#cwGoSamplesFromSetup")
    ?.addEventListener("click", () => cwRenderSamples(root));
  root.querySelector("#cwGoSettingsFromSetup")
    ?.addEventListener("click", () => go("settings"));
  root.querySelectorAll("[data-recent]").forEach((b) => {
    b.addEventListener("click", () => {
      cwRenderSetup(root, recent[Number(b.dataset.recent)]);
    });
  });
  // 選択中の分野+TOEICレベル範囲で実際に絞り込まれる語数を表示する
  // (2026-09-05ユーザー要望「選択した総語数がわかるといい」で新設した
  // 際はfacets.domain_counts頼りでレベル範囲を無視していたため、レベルを
  // 変えても表示が更新されない不具合があった(2026-09-06ユーザー指摘
  // 「英単語画面と同様のチェックがあるとわかりやすい」)。英単語画面の
  // load()と同じ考え方で、/api/wordsを実際に叩いて正確な該当件数を出す
  // (_word_filterを共有しているため_fetch_candidate_wordsとほぼ同じ
  // 絞り込み結果になる)。
  let domainCountSeq = 0;
  async function updateDomainCountWarn() {
    const warnEl = root.querySelector("#cwDomainCountWarn");
    if (!warnEl) return;
    const sourceType = root.querySelector(
      'input[name="cwSource"]:checked').value;
    if (sourceType !== "domain") { warnEl.style.display = "none"; return; }
    const wordCount = Number(root.querySelector("#cwWordCount").value)
      || DEFAULT_WORD_COUNT;
    const domains = [...selectedDomains];
    const levelMin = root.querySelector("#cwLevelMin")?.value || "";
    const levelMax = root.querySelector("#cwLevelMax")?.value || "";
    const q = new URLSearchParams();
    if (domains.length) {
      q.set("domain", domains.join(","));
    } else {
      const cat = root.querySelector("#cwCategory").value;
      if (cat) q.set("category", cat);
    }
    if (levelMin) q.set("level_min", levelMin);
    if (levelMax) q.set("level_max", levelMax);
    const seq = ++domainCountSeq;
    warnEl.textContent = "語数を確認中…";
    warnEl.style.display = "";
    let total;
    try {
      total = (await api.get("/api/words?" + q.toString())).length;
    } catch (_) {
      return;
    }
    if (seq !== domainCountSeq) return;  // 新しい問い合わせが発行済み→破棄
    const levelText = (levelMin || levelMax)
      ? `(TOEIC ${levelMin || "下限なし"}〜${levelMax || "上限なし"})` : "";
    if (total < wordCount) {
      warnEl.textContent = `⚠️ 選択中の分野${levelText}の語数は合計${total}`
        + `語です。${wordCount}語を希望していますが、実際にはそれより`
        + `少ない語数で作られる可能性があります。`;
    } else {
      warnEl.textContent = `選択中の分野${levelText}の語数: 合計${total}語`;
    }
    warnEl.style.display = "";
  }
  // 単語帳選択時も同様に、選んだ単語帳の総語数を表示する(decks一覧の
  // optionテキストにも件数はあるが、選んだ後にも分かるようにする)。
  function updateDeckCountInfo() {
    const infoEl = root.querySelector("#cwDeckCountInfo");
    if (!infoEl) return;
    const sourceType = root.querySelector(
      'input[name="cwSource"]:checked').value;
    const deckSel = root.querySelector("#cwDeck");
    if (sourceType !== "deck" || !deckSel || !deckSel.value) {
      infoEl.style.display = "none";
      return;
    }
    const deck = decks.find((d) => String(d.id) === deckSel.value);
    infoEl.textContent = `選択中の単語帳の語数: 合計${
      deck && deck.total != null ? deck.total : "?"}語`;
    infoEl.style.display = "";
  }
  // 未解答マスの猫(2026-09-05ユーザー要望)。セッションの設定ではなく
  // 端末ごとの純粋な表示設定なので、cwSaveRecentとは別にlocalStorageで
  // 単純に持つ。
  const cwBlockCat = root.querySelector("#cwBlockCat");
  cwBlockCat.checked = cwCatPrefGet(false, "block");
  cwBlockCat.addEventListener("change", () => {
    cwCatPrefSet(false, "block", cwBlockCat.checked);
  });
  const cwDomainDropdown = initCheckDropdown(root, "cwDomainBtn",
    "cwDomainPanel", () => {
      const cat = root.querySelector("#cwCategory").value;
      return cat ? { [cat]: domainGroups[cat] || [] } : domainGroups;
    }, selectedDomains, updateDomainCountWarn, "list.colDomain");
  root.querySelector("#cwCategory").addEventListener("change", () => {
    selectedDomains.clear();
    cwDomainDropdown.renderPanel();
    cwDomainDropdown.refreshLabel();
    updateDomainCountWarn();
  });
  root.querySelector("#cwWordCount")
    .addEventListener("change", updateDomainCountWarn);
  root.querySelector("#cwLevelMin")
    .addEventListener("change", updateDomainCountWarn);
  root.querySelector("#cwLevelMax")
    .addEventListener("change", updateDomainCountWarn);
  root.querySelector("#cwDeck")
    ?.addEventListener("change", updateDeckCountInfo);
  root.querySelectorAll('input[name="cwSource"]').forEach((r) => {
    r.addEventListener("change", () => {
      const v = root.querySelector(
        'input[name="cwSource"]:checked').value;
      root.querySelector("#cwDomainBlock").style.display =
        v === "domain" ? "" : "none";
      root.querySelector("#cwDeckBlock").style.display =
        v === "deck" ? "" : "none";
      updateDomainCountWarn();
      updateDeckCountInfo();
    });
  });
  updateDomainCountWarn();
  updateDeckCountInfo();
  root.querySelectorAll('input[name="cwClueMode"]').forEach((r) => {
    r.addEventListener("change", () => {
      const v = root.querySelector(
        'input[name="cwClueMode"]:checked').value;
      root.querySelector("#cwEnglishStyleBlock").style.display =
        ["always_english", "always_both"].includes(v) ? "" : "none";
      root.querySelector("#cwJapaneseStyleBlock").style.display =
        ["always_ja", "always_both"].includes(v) ? "" : "none";
    });
  });
  const startBtn = root.querySelector("#cwStart");
  startBtn.addEventListener("click", async () => {
    if (startBtn.disabled) return;  // 2026-09-03: 生成中の連打対策
    const sourceType = root.querySelector(
      'input[name="cwSource"]:checked').value;
    const selClueMode = root.querySelector(
      'input[name="cwClueMode"]:checked').value;
    const wordCount = Number(root.querySelector("#cwWordCount").value)
      || DEFAULT_WORD_COUNT;
    const levelMin = root.querySelector("#cwLevelMin")?.value || "";
    const levelMax = root.querySelector("#cwLevelMax")?.value || "";
    const selEnglishStyle = root.querySelector(
      'input[name="cwEnglishStyle"]:checked')?.value || "fill_blank";
    const selJapaneseStyle = root.querySelector(
      'input[name="cwJapaneseStyle"]:checked')?.value || "simple";
    const selShapeMode = root.querySelector(
      'input[name="cwShapeMode"]:checked')?.value || "0";
    const selCompact = selShapeMode === "1";
    const selScreenFit = selShapeMode === "screen";
    // 画面の縦横比(可能な限りこれに近い盤面形状にする・
    // crossword_gen.generateのtarget_aspect参照)。
    const selScreenAspect = selScreenFit
      ? window.innerWidth / window.innerHeight : null;
    const selAnswerDifficulty = root.querySelector(
      'input[name="cwAnswerDifficulty"]:checked')?.value || "normal";
    const body = {
      source_type: sourceType, word_count: wordCount,
      clue_mode: selClueMode, english_style: selEnglishStyle,
      japanese_style: selJapaneseStyle, compact: selCompact,
      screen_fit: selScreenFit, screen_aspect: selScreenAspect,
      answer_difficulty: selAnswerDifficulty,
    };
    let recentEntry = {
      sourceType, wordCount, clueMode: selClueMode,
      englishStyle: selEnglishStyle, japaneseStyle: selJapaneseStyle,
      compact: selCompact, screenFit: selScreenFit,
      answerDifficulty: selAnswerDifficulty,
    };
    if (sourceType === "domain") {
      const selCategory = root.querySelector("#cwCategory").value;
      body.domains = [...selectedDomains];
      // 分野を個別に絞っていなければ大分類(あれば)、それも無ければ
      // 全分野を対象にする(2026-09-06ユーザー指摘「分野を1つ以上選んで
      // ください、というエラーが出る・全て選択も許容すべき」)。
      body.category = selCategory || null;
      body.level_min = levelMin || null;
      body.level_max = levelMax || null;
      recentEntry.domains = body.domains;
      recentEntry.majorCategory = selCategory;
      recentEntry.levelMin = levelMin;
      recentEntry.levelMax = levelMax;
      recentEntry.label = body.domains.length ? body.domains.join("・")
        : selCategory ? `${selCategory}(全分野)` : "すべて";
    } else {
      const deckSel = root.querySelector("#cwDeck");
      body.deck_id = deckSel ? Number(deckSel.value) || null : null;
      const deckName = deckSel?.selectedOptions[0]?.textContent || "単語帳";
      recentEntry.deckId = body.deck_id;
      recentEntry.label = `📔${deckName}`;
    }
    const errEl = root.querySelector("#cwError");
    errEl.style.display = "none";
    const origLabel = startBtn.textContent;
    startBtn.disabled = true;
    startBtn.textContent = "⏳ クロスワード生成中…(ヒント作成のため数十秒" +
      "かかる場合があります)";
    const estimateSeconds = cwEstimateSeconds(
      selClueMode, selEnglishStyle, selJapaneseStyle, wordCount);
    const finishProgress = cwStartProgressBar(root, estimateSeconds);
    try {
      const session = await api.post("/api/games/crossword/new", body);
      finishProgress(true);
      cwSaveRecent(recentEntry);
      cwRenderPlay(root, session.session_id, session);
    } catch (e) {
      finishProgress(false);
      errEl.textContent = e.message || "生成に失敗しました。";
      errEl.style.display = "";
      startBtn.disabled = false;
      startBtn.textContent = origLabel;
    }
  });
}

// マス目1つの表示サイズを盤面の大きさから動的に決める(2026-09-05
// ユーザー要望「表示長方形の面積はできるだけ小さくなるように最適化・
// 大きくなりすぎると見づらい」)。従来は28px固定だったため、語数上限を
// 50まで拡大した後は最大34x34マス(app/services/crossword_gen.pyの
// MAX_GRID)まで育ち、固定サイズのままだと表示が際限なく巨大になって
// いた。目標合計サイズ(TARGET_BOARD_PX)をマスの多い辺で割ってセルサイズを
// 決めることで、語数が増えるほどセルを縮小し、盤面全体の面積を一定
// 範囲に抑える(既定10語・20x20相当の盤面ではTARGET_BOARD_PX/20=28pxと
// なり、従来の見た目のまま)。
// 2026-09-06: 一時「14px未満に縮めず、大きい盤面はスクロールで見る」
// 方針(縮小なし)に変更したが、実際の40語盤面(34x29マス)を見た
// ユーザーから「大きすぎるのでもう少し縮めてよい・16pxぐらいなら
// 問題ない、最小は14px」との判断があり、上記の目標サイズ縮小方式に
// 戻した。猫画像はSVG化せず常に実写PNGを使う(SVGアイコン案は
// 「かわいさが失われる」との理由で不採用済み)。画面幅が狭い場合は
// そちらも考慮して更に縮める。
const CW_MAX_CELL_PX = 28;
const CW_MIN_CELL_PX = 14;
const CW_TARGET_BOARD_PX = 560;
function cwCellSizing(rows, cols) {
  const maxDim = Math.max(rows, cols);
  const availableWidth = Math.max(
    (typeof window !== "undefined" ? window.innerWidth : 600) - 32, 200);
  const cellPx = Math.max(CW_MIN_CELL_PX, Math.min(
    CW_MAX_CELL_PX,
    Math.floor(CW_TARGET_BOARD_PX / maxDim),
    Math.floor(availableWidth / cols),
  ));
  return {
    cellPx,
    letterPx: Math.max(8, Math.round(cellPx * 0.5)),
    numPx: Math.max(7, Math.round(cellPx * 0.32)),
  };
}

// 未解答マスに表示する猫の画像プール(2026-09-05ユーザー提供・
// 自社アプリ「Cat Math Block」の素材)。黒猫/三毛猫/白猫×複数ポーズの
// 21枚(以下cwCatHash()が語ごと・セッションごとに自動で振り分ける。
// 増やす場合はこの配列に追加するだけでよい)。
const CW_CAT_IMAGES = [
  "cat_black_back_01.png", "cat_black_back_02.png",
  "cat_black_front_01.png", "cat_black_front_02.png",
  "cat_black_left_02.png",
  "cat_black_right_01.png", "cat_black_right_02.png",
  "cat_black_right_03.png",
  "cat_black_up_01.png", "cat_black_up_02.png",
  "cat_mike_back_01.png", "cat_mike_front_01.png",
  "cat_mike_left_01.png",
  "cat_mike_right_01.png", "cat_mike_right_02.png",
  "cat_white_back_01.png", "cat_white_front_01.png",
  "cat_white_left_01.png", "cat_white_left_02.png",
  "cat_white_right_01.png", "cat_white_right_02.png",
  "cat_white_right_03.png",
].map((f) => `/static/img/cw-cats/${f}`);

function cwCatHash(key) {
  let hash = 0;
  for (let i = 0; i < key.length; i++) {
    hash = (hash * 31 + key.charCodeAt(i)) >>> 0;
  }
  return CW_CAT_IMAGES[hash % CW_CAT_IMAGES.length];
}

// 猫表示設定の既定値(2026-09-05ユーザー要望「サンプルも猫選べるといい、
// デフォ猫で」、同日追記「作成時も猫がデフォ」)。サンプル・自分で作る
// のどちらも既定オン(チェックを外した人だけオフ)。保存キーは分けて
// あるので、サンプル側で外しても自作側には影響しない(逆も同様)。
function cwCatPrefKey(isSample, kind) {
  return isSample ? `cw_sample_${kind}_cat` : `cw_${kind}_cat`;
}
function cwCatPrefGet(isSample, kind) {
  const raw = localStorage.getItem(cwCatPrefKey(isSample, kind));
  return raw === null ? true : raw === "1";
}
function cwCatPrefSet(isSample, kind, on) {
  localStorage.setItem(cwCatPrefKey(isSample, kind), on ? "1" : "0");
}

// クリュー(番号+方向)から、同じ語なら常に同じ猫画像を選ぶ。未解答マスの
// 猫は答えを見せてはいけないので、word_id/englishではなくクリュー番号+
// 方向という「答えを含まない」識別子でハッシュする(2026-09-05・交差点は
// 複数の語が同じマスを共有するため、同じ猫にできるとは限らない)。
function cwCatImageFor(clue) {
  return cwCatHash(`${clue.number}-${clue.direction}`);
}

// 選択したクリューのヒント(詳細カード)を見える位置までスクロールする
// (2026-09-05ユーザー要望「語を選ぶと、語のヒントが先頭にくるといい」)。
// 詳細カードはDOM上グリッド・一覧より上に置いてあるが、長い一覧を下の方
// までスクロールした状態で選ぶと画面外のままになるため、選択のたびに
// 呼び出して視界に戻す。
function cwScrollToDetail(root) {
  root.querySelector("#cwDetailCard")
    ?.scrollIntoView({ behavior: "smooth", block: "start" });
}

// app/services/crossword_gen.pyのDIRECTIONSと対応(ヨコ/タテ)。
const CW_DIRECTION_VECTORS = {
  across: [0, 1], down: [1, 0],
};

function cwCellsFor(clue) {
  const [dr, dc] = CW_DIRECTION_VECTORS[clue.direction];
  const cells = [];
  for (let i = 0; i < clue.length; i++) {
    cells.push([clue.row + dr * i, clue.col + dc * i]);
  }
  return cells;
}

async function cwRenderPlay(root, sessionId, initialState) {
  let session = initialState
    || await api.get(`/api/games/crossword/${sessionId}`);
  let selected = session.clues[0]
    ? { number: session.clues[0].number,
        direction: session.clues[0].direction }
    : null;
  let hintDisplay = null;   // 直近取得したヒントの表示内容(次の操作で消える)
  // 両方モード(always_both)で、日本語訳/英語ヒントのどちらを表示するか
  // (2026-09-05ユーザー要望「ゲーム中に英英・日本語切り替えられる」→
  // 同日追加要望「最初は英語で、クリューごとに個別に切替」により、
  // 単一のグローバル状態ではなくクリュー単位(number+direction)の
  // マップに変更。未設定(未操作)のクリューは既定で英語("en")を表示。
  const jaEnByClue = {};
  const cwLangKey = (c) => `${c.number}-${c.direction}`;
  const cwLangFor = (c) => jaEnByClue[cwLangKey(c)] || "en";

  function selectedClue() {
    if (!selected) return null;
    return session.clues.find(
      (c) => c.number === selected.number
        && c.direction === selected.direction) || null;
  }

  function render() {
    const cellSet = new Set(
      session.grid.cells.map(([r, c]) => `${r},${c}`));
    const numbering = {};
    session.clues.forEach((c) => { numbering[`${c.row},${c.col}`] = c.number; });
    // マス目クリックでも選択できるように(2026-09-03ユーザー要望)、
    // どのマスがどのクリューに属するかを引けるようにしておく
    // (交差点は複数クリューに属する)。
    const cellToClues = {};
    session.clues.forEach((c) => {
      cwCellsFor(c).forEach(([r, col]) => {
        const k = `${r},${col}`;
        (cellToClues[k] = cellToClues[k] || []).push(c);
      });
    });
    const cur = selectedClue();
    const curCells = new Set(
      cur ? cwCellsFor(cur).map(([r, c]) => `${r},${c}`) : []);

    const { cellPx, letterPx, numPx } = cwCellSizing(
      session.grid.rows, session.grid.cols);
    // 未解答マスを猫にする設定(2026-09-05)。マスの中に収まる不透明な
    // 画像にする。サンプルは既定オン・自作クロスワードは既定オフ
    // (cwCatPrefGet参照)。
    const isSampleSession = session.source_type === "sample";
    const blockCatOn = cwCatPrefGet(isSampleSession, "block");
    let gridHtml = `<div class="cw-grid" style="grid-template-columns:` +
      `repeat(${session.grid.cols}, ${cellPx}px);--cw-cell-size:${cellPx}px;` +
      `--cw-letter-size:${letterPx}px;--cw-num-size:${numPx}px">`;
    for (let r = 0; r < session.grid.rows; r++) {
      for (let c = 0; c < session.grid.cols; c++) {
        const key = `${r},${c}`;
        if (!cellSet.has(key)) {
          gridHtml += `<div class="cw-cell cw-black"></div>`;
          continue;
        }
        const letter = session.revealed_cells[key] || "";
        const num = numbering[key];
        let catImg = "";
        if (blockCatOn && !letter) {
          // 交差点(ヨコ・タテ両方に属する)では、同じ語の他マスと極力
          // 同じ猫になるようヨコを優先する(ユーザー了承済み「クロス
          // するのでその限りではない」)。
          const clues = cellToClues[key] || [];
          const primary = clues.find((cl) => cl.direction === "across")
            || clues[0];
          if (primary) {
            // 元画像に横顔/正面/背面などのポーズが揃っているため、
            // CSS回転はしない(2026-09-05ユーザー指摘)。SVGアイコンへの
            // フォールバックも試したが「SVGは厳しい」とのユーザー判断で
            // 不採用(2026-09-06)。マスが小さくなる問題自体は、盤面全体を
            // 縮めてでも詰め込む従来方式をやめ、セルサイズに14pxの下限を
            // 設けて盤面ごとスクロールで見る方式に変更して対応する
            // (cwCellSizing参照)。
            catImg = `<img class="cw-cell-cat" src="${
              cwCatImageFor(primary)}" alt=""/>`;
          }
        }
        gridHtml += `<div class="cw-cell${
          curCells.has(key) ? " cw-selected" : ""}${
          catImg ? " cw-cell-has-cat" : ""}" data-cell="${key}">` +
          (num ? `<span class="cw-num">${num}</span>` : "") +
          catImg +
          `<span class="cw-letter">${escapeHtml(letter)}</span></div>`;
      }
    }
    gridHtml += `</div>`;

    // 無料で常時表示されるヒント種別(app/routers/games.pyの
    // FREE_HINT_BY_MODEと対応・常に配列)。日本語/英語は文章表示、音声は
    // 「ボタンは出すが0%減点」という扱いなのでhintsリストからは除かない。
    const freeHint = { always_ja: ["japanese"], always_english: ["english"],
      always_audio: ["audio"], hints_only: [],
      always_both: ["japanese", "english"] }[session.clue_mode] || [];
    // バックエンドが生成時に選ばれたモード+スタイル(日本語訳/説明・
    // 穴埋め文/類義語説明/ハイブリッド)のテキストをfree_clue_ja/enに
    // まとめて入れてくれるので、フロントはモード別分岐が不要。
    // always_bothはjaEnToggleでどちらを表示するか選ぶ。
    const freeText = (c) => {
      if (session.clue_mode === "always_both") {
        return (cwLangFor(c) === "ja" ? c.free_clue_ja : c.free_clue_en) || "";
      }
      if (freeHint.includes("japanese")) return c.free_clue_ja || "";
      if (freeHint.includes("english")) return c.free_clue_en || "";
      return "";
    };

    const clueRow = (c) => {
      const mark = c.solved ? "✅" : (c.given_up ? "🏳️" : "");
      const isSel = cur && cur.number === c.number
        && cur.direction === c.direction;
      const txt = freeText(c);
      const jaText = txt
        ? ` <span class="muted">${escapeHtml(txt)}</span>` : "";
      // 両方モードは、クリューごとに日本語訳/英語ヒントを個別に切替
      // できる小さいボタンを付ける(2026-09-05ユーザー要望)。
      const langBtn = session.clue_mode === "always_both"
        ? ` <button type="button" class="btn ghost cw-lang-toggle"
            data-num="${c.number}" data-dir="${c.direction}"
            style="padding:0 5px;font-size:10px;line-height:1.6"
            >${cwLangFor(c) === "ja" ? "日本語→英語" : "英語→日本語"}</button>` : "";
      // 正解/ギブアップ済みの語の単語詳細は、一覧内の小さいアイコンでは
      // なく選択後の詳細カード側(cw-word-tools)に大きいボタンとして出す
      // (2026-09-05ユーザー要望・一覧の🔎はスマホで押しにくかったため)。
      return `<div class="cw-clue-item${isSel ? " cw-clue-selected" : ""}"
        data-num="${c.number}" data-dir="${c.direction}">
        ${c.number}. (${c.length}文字)${jaText}${langBtn} ${mark}</div>`;
    };
    const across = session.clues.filter((c) => c.direction === "across");
    const down = session.clues.filter((c) => c.direction === "down");

    let hintHtml = "";
    if (hintDisplay) {
      hintHtml = `<div class="pill mt">${escapeHtml(hintDisplay)}</div>`;
    }

    let detailHtml = "";
    if (cur) {
      // 英語ヒント(例文)は無料で既に表示済みならボタン一覧から外す
      // (音声は常にボタンを出す)。日本語訳を見る(japanese)は、無料の
      // 日本語ヒント(間接的な説明)とは役割が違う(英単語自体の直訳を
      // 見せる)ため、モードに関わらず常にボタンを出す(2026-09-06
      // ユーザー指摘)。
      const hints = ["audio", "first_letter", "last_letter", "japanese",
        "english", "reveal"].filter(
        (h) => h === "audio" || h === "japanese" || !freeHint.includes(h));
      const done = cur.solved || cur.given_up;
      const curText = freeText(cur);
      detailHtml = `
        <div class="card mt" id="cwDetailCard">
          <div><b>クリュー ${cur.number}
            (${cur.direction === "across" ? "ヨコ" : "タテ"})</b>
            ・${cur.length}文字
            ${curText ? ` — ${escapeHtml(curText)}` : ""}
            ${session.clue_mode === "always_both" ? `<button
              type="button" class="btn ghost" id="cwJaEnToggle"
              style="margin-left:6px">🔄 ${
                cwLangFor(cur) === "ja" ? "英語ヒントに切替" : "日本語ヒントに切替"
              }</button>` : ""}</div>
          ${hintHtml}
          <div class="row mt">
            <input type="text" id="cwAnswerInput" ${done ? "disabled" : ""}
              placeholder="英単語を入力" style="text-transform:uppercase"
              autocomplete="off" autocorrect="off" autocapitalize="off"
              spellcheck="false"/>
            <button class="btn primary" id="cwSubmit"
              ${done ? "disabled" : ""}>答える</button>
          </div>
          ${done ? "" : `
          <p class="muted" style="font-size:11px;margin:6px 0 0"
            >※追加ヒントを使うと、このクリューの獲得スコアが減ることが
            あります。</p>
          <div class="row mt" id="cwHintButtons">
            ${hints.map((h) => {
              const [label, costLabel] = CW_HINT_LABELS[h];
              const used = cur.hints_used.includes(h);
              return `<button class="btn ghost" data-hint="${h}"
                >${label}${costLabel ? ` (${costLabel})` : ""}${
                  used ? " ✓" : ""}</button>`;
            }).join("")}
            <button class="btn ghost" id="cwGiveup">🏳️ ギブアップ</button>
          </div>`}
          ${(done && cur.word_info) ? `<div class="row mt cw-word-tools"
            id="cwWordTools"></div>` : ""}
        </div>`;
    }

    const isSample = session.source_type === "sample";
    root.innerHTML = `
      <div class="row">
        <button type="button" class="btn ghost" id="cwBack2">${
          isSample ? "← サンプル一覧に戻る" : "← ゲーム一覧に戻る"}</button>
        ${isSample ? "" : `<button type="button" class="btn ghost"
          id="cwBackToSetup">🔄 新しいクロスワードを作る</button>`}
      </div>
      <div class="row mt" style="justify-content:space-between">
        <h1>🧩 クロスワード</h1>
        <div class="row" style="align-items:center">
          <div class="pill cw-score">スコア: ${session.score}</div>
          ${session.status === "in_progress" ? `<button type="button"
            class="btn ghost" id="cwGiveupAll">🔓 全部答えを見る</button>`
            : ""}
        </div>
      </div>
      ${session.notice ? `<div class="pill vague mt">
        ℹ️ ${escapeHtml(session.notice)}</div>` : ""}
      ${Object.values(session.revealed_cells).includes("_") ? `<p
        class="muted" style="font-size:12px">※ マス目の「_」は複数の単語
        から成る答えの区切りです。回答するときはそこにスペースを
        入れて入力してください(例: MILKY WAY)。</p>` : ""}
      ${detailHtml}
      <div class="cw-board mt">
        <div class="cw-board-grid">${gridHtml}</div>
        <div class="cw-board-clues">
          <b>ヨコ</b>
          ${across.map(clueRow).join("")}
          <b class="mt" style="display:block">タテ</b>
          ${down.map(clueRow).join("")}
        </div>
      </div>
      ${session.status === "completed"
        ? `<div class="card mt"><h2>🎉 クリア！</h2>
           <p>最終スコア: ${session.score}</p></div>` : ""}
    `;

    root.querySelector("#cwBack2")
      .addEventListener("click", () => isSample
        ? cwRenderSamples(root) : cwRenderHub(root));
    root.querySelector("#cwBackToSetup")
      ?.addEventListener("click", () => cwRenderSetup(root));
    root.querySelector("#cwJaEnToggle")?.addEventListener("click", () => {
      if (!cur) return;
      const key = cwLangKey(cur);
      jaEnByClue[key] = cwLangFor(cur) === "ja" ? "en" : "ja";
      render();
    });
    root.querySelectorAll(".cw-lang-toggle").forEach((elm) => {
      elm.addEventListener("click", (ev) => {
        ev.stopPropagation();
        const key = `${elm.dataset.num}-${elm.dataset.dir}`;
        const current = jaEnByClue[key] || "en";
        jaEnByClue[key] = current === "ja" ? "en" : "ja";
        render();
      });
    });
    root.querySelector("#cwGiveupAll")?.addEventListener("click", async () => {
      if (!confirm("全クリューの答えを表示します(未正解分は0点になりま" +
        "す)。よろしいですか？")) return;
      session = await api.post(
        `/api/games/crossword/${sessionId}/giveup-all`, {});
      hintDisplay = null;
      render();
    });
    root.querySelectorAll(".cw-clue-item").forEach((elm) => {
      elm.addEventListener("click", () => {
        selected = { number: Number(elm.dataset.num),
                      direction: elm.dataset.dir };
        hintDisplay = null;
        render();
        // 2026-09-05ユーザー要望「語を選ぶと、語のヒントが先頭にくる
        // といい」。詳細カード(クリューのヒント)は既にDOM上グリッドより
        // 上に置いてあるが、長い一覧を下の方までスクロールした状態から
        // 選ぶと画面外のままなので、選択のたびに見える位置まで戻す。
        cwScrollToDetail(root);
      });
    });
    // 正解/ギブアップ済みのクリューを選択すると、音声(男声/女声)・詳細
    // ボタンを詳細カード内に大きめに出す(2026-09-05ユーザー要望・
    // 一覧の小さい🔎アイコンはスマホで押しにくかったため置き換え)。
    const wordToolsEl = root.querySelector("#cwWordTools");
    if (wordToolsEl && cur && cur.word_info) {
      wordToolsEl.appendChild(voiceButtonsItem(
        "word", cur.word_id, "word", () => cur.english, () => "std"));
      const detBtn = el(`<button class="btn good">📖 詳細</button>`);
      detBtn.addEventListener("click", () => showWordDetail({
        id: cur.word_id, english: cur.english,
        japanese: cur.word_info.japanese, level: cur.word_info.level,
        example: cur.word_info.example, has_detail: cur.word_info.has_detail,
      }));
      wordToolsEl.appendChild(detBtn);
    }
    // マス目クリックでも選択できるように(2026-09-03ユーザー要望)。
    // 交差点(ヨコ/タテ両方に属するマス)では、今選んでいる方と違う
    // クリューがあればそちらへ切り替え、無ければヨコを優先する。
    root.querySelectorAll(".cw-cell[data-cell]").forEach((elm) => {
      elm.addEventListener("click", () => {
        const list = cellToClues[elm.dataset.cell] || [];
        if (!list.length) return;
        const other = cur && list.find(
          (c) => !(c.number === cur.number && c.direction === cur.direction));
        const pick = other || list.find((c) => c.direction === "across")
          || list[0];
        selected = { number: pick.number, direction: pick.direction };
        hintDisplay = null;
        render();
        cwScrollToDetail(root);
      });
    });
    const input = root.querySelector("#cwAnswerInput");
    const submit = root.querySelector("#cwSubmit");
    if (input && submit) {
      const doSubmit = async () => {
        const answer = input.value.trim();
        if (!answer || !cur) return;
        try {
          const res = await api.post(
            `/api/games/crossword/${sessionId}/answer`, {
              clue_number: cur.number, direction: cur.direction, answer,
            });
          session = res;
          if (res.correct) {
            hintDisplay = null;
            toast("正解！");
          } else if (res.forced_reveal) {
            hintDisplay = "不正解が続いたため、答えを開示しました(0点)。";
          } else {
            const pct = res.match_ratio != null
              ? `一致率${Math.round(res.match_ratio * 100)}%・` : "";
            hintDisplay = `不正解です。${pct}残り試行${res.attempts_left}回`;
          }
          render();
        } catch (e) {
          toast(e.message || "エラーが発生しました。");
        }
      };
      submit.addEventListener("click", doSubmit);
      input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") doSubmit();
      });
    }
    root.querySelectorAll("[data-hint]").forEach((btn) => {
      btn.addEventListener("click", async () => {
        if (!cur) return;
        try {
          const res = await api.post(
            `/api/games/crossword/${sessionId}/hint`, {
              clue_number: cur.number, direction: cur.direction,
              hint_type: btn.dataset.hint,
            });
          session = res.session;
          if (res.hint_type === "audio") {
            speech.sayItem("word", res.word_id, "word", MALE_VOICE, "",
              speedOpts("std"));
            hintDisplay = "🔊 発音を再生しました。";
          } else if (res.hint_type === "first_letter"
            || res.hint_type === "last_letter") {
            hintDisplay = `文字: ${res.letter}`;
          } else if (res.hint_type === "japanese") {
            hintDisplay = `意味: ${res.japanese}`;
          } else if (res.hint_type === "english") {
            hintDisplay = `例文: ${res.example}`;
          } else if (res.hint_type === "reveal") {
            hintDisplay = `答え: ${res.answer}`;
          }
          render();
        } catch (e) {
          toast(e.message || "ヒントを取得できませんでした。");
        }
      });
    });
    root.querySelector("#cwGiveup")?.addEventListener("click", async () => {
      if (!cur) return;
      try {
        session = await api.post(
          `/api/games/crossword/${sessionId}/giveup`, {
            clue_number: cur.number, direction: cur.direction,
          });
        hintDisplay = null;
        render();
      } catch (e) {
        toast(e.message || "エラーが発生しました。");
      }
    });
  }

  render();
}
