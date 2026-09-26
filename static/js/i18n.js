// 多言語化エンジン(2026-09-23・オーナー要望「非日本語話者にも良さが伝わる
// ように」)。対応言語=日本語(既定)・英語・中国語(簡体字)・中国語(繁体字)の
// 4つ(拡張の余地は残す)。
//
// 設計方針:
// - 通常scriptとして読み込む(ES moduleにしない)。<head>で同期読み込みして
//   おけば、静的ページ(about/privacy/terms/tokushoho/login)でも
//   SPA(index.html→app.js/views.js)でも同じ`window.I18N`を共有できる。
//   ES module側(app.js/views.js)からは`window.I18N.t(...)`をそのまま使う
//   (app.jsが`t`という短い名前で再エクスポートする)。
// - 保存された選択(セレクトで切替)があればそれ・無ければAccept-Language
//   (navigator.language/navigator.languages)から推定・それも無ければ日本語。
//   ver1.4.14で実装したテーマ(ダーク/ライト)のOS連動と同じ設計。
// - 静的ページ: 本文のJapaneseはHTMLにそのまま書いておき(JS無効環境や
//   クローラー向けのフォールバック・SEO上も日本語が本来の内容)、
//   `data-i18n="key"`を付けた要素をJSでtextContent置換する
//   (`data-i18n-html="key"`はリンク等のHTMLタグを含む場合に使う・
//   `data-i18n-placeholder`/`data-i18n-title`/`data-i18n-aria`は属性用)。
//   初回描画後に一瞬日本語が見えてから翻訳される(FOUC)が、テーマの色反転
//   ほど目立たない・辞書をhead内に埋め込む重複コストの方が大きいため許容する
//   (2026-09-23設計判断)。
// - SPA(views.js): テンプレート文字列内で`t("key")`を直接呼ぶ。切替時は
//   現在開いている画面を再描画する(既存のタブ切替と同じ仕組みを流用)。
//
// 辞書のキー命名: `画面や領域.項目`のドット区切り(例: "nav.dashboard"、
// "welcome.heroTitle")。共通で使う語(保存・削除・キャンセル等)は
// "common."prefixにまとめる。
(function (global) {
  "use strict";

  var LANGS = ["ja", "en", "zh-CN", "zh-TW"];
  var LANG_LABELS = {
    ja: "日本語", en: "English", "zh-CN": "简体中文", "zh-TW": "繁體中文",
  };
  var STORAGE_KEY = "lang";

  function safeGetItem(key) {
    try { return localStorage.getItem(key); } catch (e) { return null; }
  }
  function safeSetItem(key, value) {
    try { localStorage.setItem(key, value); } catch (e) { /* 保存できない環境 */ }
  }

  function savedLang() {
    var v = safeGetItem(STORAGE_KEY);
    return LANGS.indexOf(v) >= 0 ? v : null;
  }

  // ブラウザの言語設定(navigator.languages優先・無ければnavigator.language)
  // から対応4言語のどれかへ振り分ける。中国語は簡体字/繁体字の判定が
  // 難しい地域があるため、地域コード・スクリプトタグで判定し、
  // 曖昧な場合は簡体字(zh-CN、世界的な話者数が多い方)を既定にする。
  function bucketFromTag(tag) {
    if (!tag) return null;
    var t = tag.toLowerCase();
    if (t.indexOf("ja") === 0) return "ja";
    if (t.indexOf("zh") === 0) {
      if (t.indexOf("tw") >= 0 || t.indexOf("hk") >= 0 || t.indexOf("mo") >= 0
        || t.indexOf("hant") >= 0) return "zh-TW";
      return "zh-CN";
    }
    if (t.indexOf("en") === 0) return "en";
    return null;
  }

  function detectFromBrowser() {
    try {
      var tags = (global.navigator && global.navigator.languages)
        || [global.navigator && global.navigator.language];
      for (var i = 0; i < tags.length; i++) {
        var b = bucketFromTag(tags[i]);
        if (b) return b;
      }
    } catch (e) { /* ignore */ }
    return null;
  }

  // 未対応の地域言語は、このアプリの本来の言語である日本語へ戻す
  // (英語を既定にすると「日本語話者向けアプリ」という性質とずれるため・
  // 2026-09-23設計判断)。4言語のどれかに一致すればそれを使う。
  function resolveLang() {
    return savedLang() || detectFromBrowser() || "ja";
  }

  var currentLang = resolveLang();
  var listeners = [];

  function onChange(fn) { listeners.push(fn); }

  function interpolate(str, vars) {
    if (!vars) return str;
    return str.replace(/\{(\w+)\}/g, function (m, k) {
      return Object.prototype.hasOwnProperty.call(vars, k) ? vars[k] : m;
    });
  }

  function t(key, vars) {
    var byLang = DICT[currentLang] || {};
    var s = byLang[key];
    if (s == null) s = (DICT.ja || {})[key]; // 未翻訳キーは日本語へ
    if (s == null) s = key; // それも無ければキー名をそのまま出す(気づける)
    return interpolate(s, vars);
  }

  function translateDom(root) {
    root = root || document;
    root.querySelectorAll("[data-i18n]").forEach(function (el) {
      el.textContent = t(el.getAttribute("data-i18n"));
    });
    root.querySelectorAll("[data-i18n-html]").forEach(function (el) {
      el.innerHTML = t(el.getAttribute("data-i18n-html"));
    });
    root.querySelectorAll("[data-i18n-placeholder]").forEach(function (el) {
      el.setAttribute("placeholder", t(el.getAttribute("data-i18n-placeholder")));
    });
    root.querySelectorAll("[data-i18n-title]").forEach(function (el) {
      el.setAttribute("title", t(el.getAttribute("data-i18n-title")));
    });
    root.querySelectorAll("[data-i18n-aria]").forEach(function (el) {
      el.setAttribute("aria-label", t(el.getAttribute("data-i18n-aria")));
    });
    root.querySelectorAll("[data-i18n-alt]").forEach(function (el) {
      el.setAttribute("alt", t(el.getAttribute("data-i18n-alt")));
    });
  }

  function setLang(lang) {
    if (LANGS.indexOf(lang) < 0) return;
    currentLang = lang;
    safeSetItem(STORAGE_KEY, lang);
    try { document.documentElement.lang = lang; } catch (e) { /* ignore */ }
    translateDom(document);
    listeners.forEach(function (fn) { try { fn(lang); } catch (e) { /* ignore */ } });
    document.querySelectorAll(".i18n-lang-select").forEach(function (sel) {
      sel.value = lang;
    });
  }

  // ヘッダー等に置く言語切替セレクト。<select class="i18n-lang-select">を
  // 指すDOMを渡す(無ければ何もしない)。既存のfontSize/themeToggleと同じ
  // 「よくある見た目」(ドロップダウン)にする(2026-09-23オーナー指示)。
  function wireLangSelect(sel) {
    if (!sel) return;
    LANGS.forEach(function (l) {
      var opt = document.createElement("option");
      opt.value = l;
      opt.textContent = "🌐 " + LANG_LABELS[l];
      sel.appendChild(opt);
    });
    sel.value = currentLang;
    sel.addEventListener("change", function (e) { setLang(e.target.value); });
  }

  function initLangSwitchers() {
    document.querySelectorAll(".i18n-lang-select").forEach(wireLangSelect);
  }

  // ============================================================
  // バックエンドへ現在の表示言語を伝える(2026-09-26)。同一オリジンの
  // `/api/`宛てfetchに`X-Lang`ヘッダ(ja/en/zh-CN/zh-TW)を自動で付ける。
  // サーバー(app/main.pyの_auth_context・app/services/messages.py)が
  // これを見て、エラー/上限到達などの利用者向けメッセージを同じ言語で返す。
  // 個々のfetch呼び出し(api.js・speech.js・login.html等)を直さなくても
  // 新しい呼び出しを含め全てに効くよう、ここで一括して付与する。
  // 失敗しても(古い環境・特殊なinput等)元のfetchをそのまま呼ぶだけ。
  // 既に呼び出し側がX-Langを付けていればそれを優先する。
  // ============================================================
  (function patchFetchForLang() {
    var origFetch = global.fetch;
    if (typeof origFetch !== "function") return;
    global.fetch = function (input, init) {
      try {
        var url = typeof input === "string" ? input
          : (input && input.url) || String(input || "");
        var u = new URL(url, global.location.href);
        if (u.origin === global.location.origin
          && u.pathname.indexOf("/api/") === 0) {
          init = init ? Object.assign({}, init) : {};
          var h = new Headers(init.headers
            || (input && typeof input !== "string" && input.headers)
            || undefined);
          if (!h.has("X-Lang")) h.set("X-Lang", currentLang);
          init.headers = h;
        }
      } catch (e) { /* 付与できなければそのまま送る */ }
      return origFetch.call(this, input, init);
    };
  })();

  // ============================================================
  // 辞書。DICT[lang][key] = 文字列。ja以外で未登録のキーはjaへ自動fallback。
  // ============================================================
  var DICT = { ja: {}, en: {}, "zh-CN": {}, "zh-TW": {} };

  global.I18N = {
    LANGS: LANGS, LANG_LABELS: LANG_LABELS, DICT: DICT,
    t: t, resolveLang: resolveLang, currentLang: function () { return currentLang; },
    setLang: setLang, savedLang: savedLang, translateDom: translateDom,
    onChange: onChange, initLangSwitchers: initLangSwitchers,
    // <head>内で最速に呼ぶ用(documentElement.langだけ先に確定。本文の翻訳は
    // translateDomがDOMContentLoaded後に行う)。
    applyEarly: function () {
      try { document.documentElement.lang = currentLang; } catch (e) { /* ignore */ }
    },
  };
  global.I18N.applyEarly();
})(window);
