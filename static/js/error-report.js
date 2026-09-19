// フロントエンドの未捕捉JS例外をサーバーへ報告する(2026-08-30)。
// api.jsのreq()を経由すると自己参照的にエラー処理でエラーが起きうる
// ため、素のfetchで直接POLLし失敗は握りつぶす(常にbest-effort)。
// classicスクリプトとしてapp.js(type="module")より前に読み込むことで、
// 他のスクリプトの実行前からハンドラを有効にする(index.html参照)。
(function () {
  // gclid等の広告クリックIDを含むクエリ文字列をエラー記録へ残さない
  // (2026-09-19・Fable敵対的レビューS1)。パスのみ送る。
  function _noQuery(u) { return String(u || "").split("?")[0].split("#")[0]; }

  function report(kind, message, stack, url, line, col) {
    try {
      fetch("/api/system/client-error", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kind, message: String(message || ""), stack: String(stack || ""),
          url: _noQuery(url || location.href), line: line || 0, col: col || 0,
        }),
      }).catch(() => {});
    } catch (e) { /* 報告自体の失敗はUIに影響させない */ }
  }

  window.addEventListener("error", function (e) {
    report("jserror", e.message, e.error && e.error.stack,
      e.filename, e.lineno, e.colno);
  });

  window.addEventListener("unhandledrejection", function (e) {
    const reason = e.reason;
    // api.jsのreq()/stream()が投げたエラーは、投げる前に既に
    // POST /client-errorで(kind="api_error"として)記録済みなので、
    // ここでunhandledrejectionとして二重記録しない(2026-09-18)。
    if (reason && reason.apiErrorLogged) return;
    const message = reason && reason.message ? reason.message : String(reason);
    const stack = reason && reason.stack ? reason.stack : "";
    report("unhandledrejection", message, stack, _noQuery(location.href), 0, 0);
  });
})();
