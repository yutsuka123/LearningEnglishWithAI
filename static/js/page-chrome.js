// SPA外の独立ページ(about/terms/privacy/tokushoho/login)共通の
// テーマ(ダーク/ライト)・文字サイズ切替(2026-09-05・opus照査提案)。
// static/js/app.jsのapplyTheme/applyFontSizeと同じロジックで、
// localStorageの"theme"/"fontSize"キーもSPA本体と共有する
// (ログイン前後で設定が引き継がれる)。
//
// 使い方: <head>内でこのファイルを<script defer>ではなく、テーマ確定を
// 描画前に行うため同期<script>で読み込む(FOUC対策)。呼び出し側は
// <body>内に以下を用意しておく:
//   <div class="pagebar">
//     <select id="fontSize">...</select>
//     <button type="button" id="themeToggle">🌙</button>
//   </div>
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

  // テーマだけは<head>内でこのファイルが読まれた時点(body描画前)に
  // 即適用し、ライト設定の人に一瞬ダークが見える問題(FOUC)を防ぐ。
  applyTheme(safeGetItem('theme') || 'dark');

  // ボタン/セレクトはbody側の要素なので、DOM構築後に配線する。
  document.addEventListener('DOMContentLoaded', function () {
    applyTheme(safeGetItem('theme') || 'dark');
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
  });
})();
