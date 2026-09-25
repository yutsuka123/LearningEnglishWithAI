// 対応していないブラウザ向けの案内(2026-09-26)。
// 背景: 古いブラウザ(?. / ?? を解釈できない Chrome 79 以前・Safari 13.0 以前・Firefox 73 以前など)
//   では app.js の読み込み自体が SyntaxError で止まり、画面が真っ白のまま何の案内も出なかった
//   (2026-09-25 広告経由の訪問で実際に発生・client_errors に記録)。
// 設計: このファイルは古いブラウザでも必ず解釈できるよう ES5 の構文だけで書く(let/const・アロー関数・
//   テンプレート文字列・?. は使わない)。他のスクリプトより前に同期で読み込むこと(各HTMLのheadの先頭)。
//   外部への通信・記録は一切行わない(JSエラー自体は error-report.js が従来どおり報告する)。
// 表示: <script data-app="1"> のページ(=app.js で動くSPAのindex.html)は、アプリが動かないので全画面で案内する。
//   それ以外の静的ページ(概要・規約等)は本文を読めるため、上部の帯で案内するだけにする。
(function () {
  var script = document.currentScript;
  var isApp = !!(script && script.getAttribute("data-app"));

  // 何が使えないか。"old"=構文/モジュール非対応、"storage"=ブラウザのサイトデータ保存が無効(SPAのみ問題)。
  function detect() {
    try {
      // app.js が使っている最も新しい構文(?. と ??)を実際に解釈できるかを試す。
      // CSP等でevalが禁止されている場合はSyntaxError以外(EvalError)になるので、その時は対応扱いにする。
      new Function("var a=null;return (a?.b)??1;");
    } catch (e) {
      if (e instanceof SyntaxError) return "old";
    }
    // <script type="module"> を解釈できない古いブラウザは、app.js を無視して空白のままになる。
    if (!("noModule" in document.createElement("script"))) return "old";
    if (isApp) {
      try {
        var k = "__compat_guard__";
        localStorage.setItem(k, "1");
        localStorage.removeItem(k);
      } catch (e) {
        return "storage";
      }
    }
    return null;
  }

  var reason = detect();
  if (!reason) return;

  // 表示言語: 保存済みの選択(i18n.js と同じキー "lang")→ブラウザの言語設定 → 日本語。
  function pickLang() {
    var saved = null;
    try { saved = localStorage.getItem("lang"); } catch (e) { /* 使えない環境 */ }
    var tag = saved || (navigator.languages && navigator.languages[0]) || navigator.language || "ja";
    tag = String(tag).toLowerCase();
    if (tag.indexOf("ja") === 0) return "ja";
    if (tag.indexOf("zh") === 0) {
      return (tag.indexOf("tw") >= 0 || tag.indexOf("hk") >= 0 || tag.indexOf("mo") >= 0
        || tag.indexOf("hant") >= 0) ? "zh-TW" : "zh-CN";
    }
    if (tag.indexOf("en") === 0) return "en";
    return "ja";
  }

  var TEXT = {
    old: {
      "ja": ["お使いのブラウザには対応していません",
        "お使いのブラウザは古いため、このサイトの機能が正しく動作しません。Chrome・Edge・Safari・Firefox の最新版でお試しください。"],
      "en": ["Your browser is not supported",
        "Your browser is too old to run this site properly. Please try the latest version of Chrome, Edge, Safari, or Firefox."],
      "zh-CN": ["不支持您的浏览器",
        "您的浏览器版本过低，本网站无法正常运行。请使用最新版的 Chrome、Edge、Safari 或 Firefox 重新访问。"],
      "zh-TW": ["不支援您的瀏覽器",
        "您的瀏覽器版本過舊，本網站無法正常運作。請使用最新版的 Chrome、Edge、Safari 或 Firefox 重新開啟。"]
    },
    storage: {
      "ja": ["ブラウザのサイトデータの保存が無効になっています",
        "アプリを起動できません。プライベートモードの場合は通常のウィンドウで開くか、ブラウザの設定でこのサイトのデータ（Cookie・ローカルストレージ）の保存を許可してからお試しください。"],
      "en": ["Site data storage is turned off in your browser",
        "The app cannot start. If you are in private mode, open the site in a normal window, or allow this site to store data (cookies and local storage) in your browser settings, then try again."],
      "zh-CN": ["浏览器已禁用网站数据存储",
        "应用无法启动。如果处于隐私模式，请在普通窗口中打开；或在浏览器设置中允许此网站存储数据（Cookie 和本地存储）后重试。"],
      "zh-TW": ["瀏覽器已停用網站資料儲存",
        "應用程式無法啟動。若處於私密模式，請在一般視窗中開啟；或在瀏覽器設定中允許此網站儲存資料（Cookie 與本機儲存空間）後重試。"]
    }
  };

  var CLOSE = { "ja": "閉じる", "en": "Close", "zh-CN": "关闭", "zh-TW": "關閉" };

  var lang = pickLang();
  var msg = TEXT[reason][lang];

  function show() {
    if (document.getElementById("compatGuard")) return;
    // document.currentScript が無い古いブラウザでも、SPA(#viewがあるのはindex.htmlだけ)なら全画面にする。
    var app = isApp || !!document.getElementById("view");
    var box = document.createElement("div");
    box.id = "compatGuard";
    box.setAttribute("role", "alert");
    // 本サイトのCSS(テーマ)が読み込めなくても読めるよう、色・配置をすべてインラインで指定する。
    box.style.cssText = (app
      ? "position:fixed;top:0;left:0;right:0;bottom:0;z-index:2147483647;display:flex;"
        + "flex-direction:column;align-items:center;justify-content:center;padding:24px;"
      // 静的ページは本文を読めるので、上部に固定した閉じられる帯にする(login.htmlのbodyは横並びflexなので
      // 通常の流れには置かない)。
      : "position:fixed;top:0;left:0;right:0;z-index:2147483647;padding:12px 44px 12px 16px;"
        + "box-shadow:0 2px 8px rgba(0,0,0,.25);")
      + "background:#fff8e1;color:#3e2f00;text-align:center;"
      + "font:16px/1.7 -apple-system,BlinkMacSystemFont,'Segoe UI','Hiragino Sans',Meiryo,sans-serif;"
      + "border-bottom:2px solid #f0b400;box-sizing:border-box;";
    var h = document.createElement("div");
    h.style.cssText = "font-weight:bold;font-size:" + (app ? "18px" : "16px") + ";margin-bottom:6px;";
    h.appendChild(document.createTextNode(msg[0]));
    var p = document.createElement("div");
    p.style.cssText = "max-width:560px;margin:0 auto;";
    p.appendChild(document.createTextNode(msg[1]));
    box.appendChild(h);
    box.appendChild(p);
    if (!app) {
      var x = document.createElement("button");
      x.type = "button";
      x.setAttribute("aria-label", CLOSE[lang]);
      x.style.cssText = "position:absolute;top:6px;right:8px;width:32px;height:32px;border:0;"
        + "background:transparent;color:#3e2f00;font-size:22px;line-height:1;cursor:pointer;";
      x.appendChild(document.createTextNode("\u00d7"));
      x.onclick = function () { box.parentNode.removeChild(box); };
      box.appendChild(x);
    }
    document.body.insertBefore(box, document.body.firstChild);
  }

  if (document.body) show();
  else document.addEventListener("DOMContentLoaded", show);
})();
