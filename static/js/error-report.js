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
        keepalive: true,   // 直後の自己修復の再読込で送信が中断されないように
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kind, message: String(message || ""), stack: String(stack || ""),
          url: _noQuery(url || location.href), line: line || 0, col: col || 0,
        }),
      }).catch(() => {});
    } catch (e) { /* 報告自体の失敗はUIに影響させない */ }
  }

  // JSモジュールの読み込み失敗(新旧のファイルが混ざった状態)を自分で直す(2026-10-03)。
  // 背景: ブラウザの履歴移動・タブ復元は、サーバーが no-cache を返していても保存済みのファイルを
  //   再検証せずに使う。ブラウザに古い app.js が残ったまま新しい views.js だけ取得されると、
  //   「Importing binding name 'tabLabel' is not found」(Safari)等で起動できず、画面が動かない
  //   (2026-10-03 Mac Safari の実ユーザー1件・client_errors に記録)。
  // 対処: 該当するエラーのときだけ、モジュール群をキャッシュを使わず取り直してから1回だけ再読込する。
  //   直近5分に再読込済みなら何もしない(取り直しても直らない場合の無限ループ防止)。
  //   sessionStorage に印を残せない環境でも、ループを避けるため何もしない。
  // 「新旧のファイルが混ざった」ことを示す静的importの解決失敗だけを対象にする(Safari/Chrome/Firefoxの文言)。
  // 動的import()の「Failed to fetch dynamically imported module」等は回線断でも出るため含めない
  // (含めると、回線が不安定な人が会話/クイズ中に全画面リロードされる。独立照査 2026-10-03)。
  const MODULE_LOAD_ERROR = new RegExp(
    "Importing binding name|provide an export named|import not found", "i");
  // app.js のimport先(app.jsの先頭のimportと揃えること)。
  const MODULE_FILES = ["app.js", "views.js", "api.js", "speech.js", "quiz.js"];

  function healStaleModules(message) {
    if (!MODULE_LOAD_ERROR.test(String(message || ""))) return;
    const key = "module_heal_at";
    try {
      const last = Number(sessionStorage.getItem(key) || 0);
      if (Date.now() - last < 5 * 60 * 1000) return;
      sessionStorage.setItem(key, String(Date.now()));
    } catch (e) { return; }
    const reload = function () { location.reload(); };
    Promise.all(MODULE_FILES.map(function (f) {
      return fetch("/static/js/" + f, { cache: "reload" }).catch(function () {});
    })).then(reload, reload);
  }

  window.addEventListener("error", function (e) {
    report("jserror", e.message, e.error && e.error.stack,
      e.filename, e.lineno, e.colno);
    healStaleModules(e.message);
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
    healStaleModules(message);
  });
})();
