// SPA外の独立ページ(about/terms/privacy/tokushoho/login)共通の
// テーマ(ダーク/ライト)・文字サイズ・言語切替(2026-09-05・opus照査提案。
// 言語切替は2026-09-23追加)。
// static/js/app.jsのapplyTheme/applyFontSizeと同じロジックで、
// localStorageの"theme"/"fontSize"/"lang"キーもSPA本体と共有する
// (ログイン前後で設定が引き継がれる)。
//
// 使い方: <head>内でこのファイルを<script defer>ではなく、テーマ確定を
// 描画前に行うため同期<script>で読み込む(FOUC対策・i18n.js/i18n_dict.jsを
// このファイルより先に読み込むこと)。呼び出し側は<body>内に以下を用意:
//   <div class="pagebar">
//     <select id="fontSize">...</select>
//     <select class="i18n-lang-select"></select>
//     <button type="button" id="themeToggle">🌙</button>
//   </div>
// 本文の翻訳対象要素には data-i18n="key" 等を付ける(詳細はi18n.js参照)。
(function () {
  // iOS Safariの「すべてのCookieをブロック」等でlocalStorageが
  // SecurityErrorを投げることがある。同期scriptの先頭のため、無防備だと
  // 以降の全コードが止まる(2026-09-01 login.htmlで発見した既知の問題)。
  function safeGetItem(key) {
    try { return localStorage.getItem(key); } catch (_) { return null; }
  }
  function safeSetItem(key, value) {
    try { localStorage.setItem(key, value); } catch (_) { /* ignore */ }
  }

  function applyTheme(theme) {
    const btn = document.getElementById('themeToggle');
    if (theme === 'light') {
      document.documentElement.dataset.theme = 'light';
      if (btn) btn.textContent = '☀️';
    } else {
      delete document.documentElement.dataset.theme;
      if (btn) btn.textContent = '🌙';
    }
  }

  function applyFontSize(size) {
    if (size) document.documentElement.dataset.fontSize = size;
    else delete document.documentElement.dataset.fontSize;
    const sel = document.getElementById('fontSize');
    if (sel) sel.value = size;
  }

  // テーマ(2026-09-22〜): 保存された選択(ボタンで切替)があればそれ、無ければ端末
  // (OS/ブラウザ)の配色設定に合わせる(ライト設定ならライト・判定できない時はダーク)。
  function savedTheme() {
    const t = safeGetItem('theme');
    return t === 'light' || t === 'dark' ? t : null;
  }
  function resolveTheme() {
    const saved = savedTheme();
    if (saved) return saved;
    try {
      return window.matchMedia('(prefers-color-scheme: light)').matches
        ? 'light' : 'dark';
    } catch (_) { return 'dark'; }
  }

  // テーマだけは<head>内でこのファイルが読まれた時点(body描画前)に
  // 即適用し、ライト設定の人に一瞬ダークが見える問題(FOUC)を防ぐ。
  applyTheme(resolveTheme());

  // ボタン/セレクトはbody側の要素なので、DOM構築後に配線する。
  document.addEventListener('DOMContentLoaded', function () {
    applyTheme(resolveTheme());
    try {
      const mq = window.matchMedia('(prefers-color-scheme: light)');
      const onChange = function () {
        if (!savedTheme()) applyTheme(resolveTheme());
      };
      if (mq.addEventListener) mq.addEventListener('change', onChange);
      else if (mq.addListener) mq.addListener(onChange);
    } catch (_) { /* 追従できなくても動作に影響なし */ }
    applyFontSize(safeGetItem('fontSize') || '');
    document.getElementById('themeToggle')
      ?.addEventListener('click', function () {
        const next = document.documentElement.dataset.theme === 'light'
          ? 'dark' : 'light';
        safeSetItem('theme', next);
        applyTheme(next);
      });
    document.getElementById('fontSize')
      ?.addEventListener('change', function (e) {
        const v = e.target.value;
        safeSetItem('fontSize', v);
        applyFontSize(v);
      });
    // 言語切替(2026-09-23): i18n.js/i18n_dict.jsがこのファイルより先に
    // 読み込まれていれば window.I18N が使える。翻訳自体はi18n.jsの
    // initLangSwitchers/translateDomが行う(このファイルはウィジェットの
    // 存在確認だけ)。
    if (window.I18N) {
      window.I18N.initLangSwitchers();
      window.I18N.translateDom(document);
    }
  });
})();
