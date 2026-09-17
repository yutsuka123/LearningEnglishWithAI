// Thin fetch wrapper around the backend API.

// ボタン押下等が引き金のAPIエラーを自動でclient_errorsへ記録する
// (2026-09-18・「ボタンでエラーになった操作も含めて広くログを見直して
// ほしい」というユーザー要望への対応)。req()/stream()の失敗時にここを
// 通るだけで、呼び出し元を個別に直さなくても記録される。
//
// 注意点2つ(いずれも実装前にFableレビューで指摘された既知の落とし穴):
// ①ここから素のfetchで直接送る(api.post等・reqを経由しない)こと。
//   reqを経由するとエラー記録の送信自体がエラーになった時にまた記録
//   しようとして無限ループ/自己増殖しうる(static/js/error-report.jsの
//   冒頭コメントと同じ理由)。
// ②401(要ログイン)/402(残高不足)/403(招待制・禁忌設定・チャージ導線等の
//   ガード)/429(試行超過)はゲスト操作や課金導線の正常なガードで「エラー」
//   ではないため記録対象から除外する(除外しないと管理画面のランキングが
//   これらで埋まり、本当のバグが見えなくなる)。
const _EXPECTED_STATUSES = new Set([401, 402, 403, 429]);
// これ自体の失敗を記録しようとする自己参照を避けるための除外パス。
const _NO_REPORT_PATHS = new Set(
  ["/api/system/track", "/api/system/client-error"]);

// 集計時にID違いだけで別メッセージに分散しないよう、数値の
// パス断片を:idへ正規化する(例: /api/words/123/known -> /api/words/:id/known)。
function _normalizePath(path) {
  return path.split("?")[0].replace(/\/\d+(?=\/|$)/g, "/:id");
}

function _reportApiError(method, path, status, code) {
  if (_NO_REPORT_PATHS.has(path) || _EXPECTED_STATUSES.has(status)) return;
  try {
    fetch("/api/system/client-error", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        kind: "api_error",
        message: `${method} ${_normalizePath(path)} -> ${status}`
          + (code ? ` (E${code})` : ""),
        // 2026-09-18修正: 生のpath(クエリ文字列付き)をそのまま保存すると、
        // 将来「?q=検索語」のような自由入力を含むGETが増えた時に個人の
        // 入力内容がclient_errorsに残ってしまう(Fableレビュー指摘)。
        // messageと同じ正規化・クエリ除去済みのパスだけを保存する。
        url: _normalizePath(path),
      }),
    }).catch(() => {});
  } catch (e) { /* 報告自体の失敗はUIに影響させない */ }
}

// 2026-09-18追加: このアプリはHTTPを200のまま`{ok:false,error:"..."}`を
// 返す設計のエンドポイントが多数ある(翻訳・詳細生成・添削等)。「ボタンで
// エラーになった」操作の主要な経路の1つだが、res.okだけを見る
// _reportApiErrorでは拾えないため専用に用意する(Fableレビュー指摘)。
// 既存の呼び出し元の`if (r.ok) {...} else {...}`分岐は変えたくないので、
// req()側は投げ直さず記録だけ行う。
function _reportBodyError(method, path, errorText) {
  if (_NO_REPORT_PATHS.has(path)) return;
  try {
    fetch("/api/system/client-error", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        kind: "api_error",
        message: `${method} ${_normalizePath(path)} -> ok:false`
          + (errorText ? `: ${String(errorText).slice(0, 100)}` : ""),
        url: _normalizePath(path),
      }),
    }).catch(() => {});
  } catch (e) { /* 報告自体の失敗はUIに影響させない */ }
}

// ストリーミング応答の本文途中でサーバー側の例外が起きたことを示す印。
// app/services/ai.pyのSTREAM_ERROR_MARKERと完全に一致させること
// (2026-09-18・stream()のマーカー検出で使う)。
const STREAM_ERROR_MARKER = "§§STREAM_ERROR§§";

function _streamError(path, message) {
  if (!_NO_REPORT_PATHS.has(path)) {
    try {
      fetch("/api/system/client-error", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          kind: "api_error",
          message: `POST ${_normalizePath(path)} -> stream-error`,
          url: _normalizePath(path),
        }),
      }).catch(() => {});
    } catch (e) { /* 報告自体の失敗はUIに影響させない */ }
  }
  const err = new Error(message);
  err.apiErrorLogged = true;
  return err;
}

async function req(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  if (res.status === 204) return null;
  const text = await res.text();
  // 2026-09-18修正: 従来はres.okの判定より先にJSON.parseしていたため、
  // 本文がJSONでない障害(Caddyが返す502/504のHTMLページ・413等、
  // アプリに届く前のインフラ障害)ではJSON.parse自体が先に例外を投げ、
  // 下のエラー記録(_reportApiError)を素通りしてしまっていた
  // (Fableレビューで発見。一番気づきたい障害ほど記録から漏れる構造
  // だった)。parseの成否とres.okを両方見てから記録する。
  let data = null;
  let parseFailed = false;
  if (text) {
    try { data = JSON.parse(text); }
    catch (e) { parseFailed = true; }
  }
  if (!res.ok || parseFailed) {
    // parseFailed(本文がJSONでない障害)時は、Caddyの502/504等が返す
    // 生のHTMLをそのままユーザー向けメッセージにしない(2026-09-18・
    // Fable2回目レビュー指摘)。開発者向けにconsole.errorへは生本文を
    // 残しつつ、画面に出す文言は汎用のものにする。
    const msg = parseFailed
      ? "通信エラーが発生しました。しばらくしてから再度お試しください。"
      : ((data && (data.detail || data.error)) || res.statusText);
    const text2 = typeof msg === "string" ? msg : JSON.stringify(msg);
    // サーバー側が付与する4桁エラーコード(X-Error-Codeヘッダ)。問い合わせ
    // 時にユーザーがこのコードを伝えられるよう、メッセージ末尾に付記する
    // （2026-08-20〜共通エラーコード体系、docs/ERROR_CODES.md参照）。
    const code = res.headers.get("X-Error-Code");
    const withCode = code ? `${text2} (E${code})` : text2;
    console.error(`API ${method} ${path} -> ${res.status}: `
      + `${parseFailed ? text.slice(0, 300) : withCode}`);
    _reportApiError(method, path, res.status, code);
    const err = new Error(withCode);
    // error-report.jsのunhandledrejectionハンドラで二重記録しないための印。
    err.apiErrorLogged = true;
    throw err;
  }
  if (data && typeof data === "object" && data.ok === false) {
    _reportBodyError(method, path, data.error);
  }
  return data;
}

// 画面表示/ボタン押下の利用状況イベント記録（管理画面の分析用・
// 2026-08-17）。呼び出し元の操作を絶対に妨げないよう、結果を待たず
// 失敗も無視するfire-and-forget。
function track(kind, category, label = "") {
  req("POST", "/api/system/track", { kind, category, label })
    .catch(() => { /* 記録失敗は無視（UIに影響させない） */ });
}

export const api = {
  get: (p) => req("GET", p),
  post: (p, b) => req("POST", p, b),
  put: (p, b) => req("PUT", p, b),
  del: (p) => req("DELETE", p),
  track,

  // Streaming POST -> calls onChunk(textPiece) as data arrives.
  async stream(path, body, onChunk) {
    const res = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      // 2026-09-18修正: 従来はここでres.okを見ておらず、エラー応答の本文
      // (例: 402/500のエラーメッセージ)がそのままonChunkへ渡り、AIの発言
      // として画面に表示・会話履歴へ保存・自動保存・読み上げまでされて
      // しまうバグがあった(Fableレビューで指摘)。req()と同じ形でエラーを
      // 検出し、呼び出し元がtry/catchで拾えるようにする。
      const text = await res.text().catch(() => "");
      let msg = text;
      try {
        const data = text ? JSON.parse(text) : null;
        msg = (data && (data.detail || data.error)) || res.statusText;
      } catch (_) { /* JSONでなければテキストのまま使う */ }
      const code = res.headers.get("X-Error-Code");
      const withCode = code ? `${msg} (E${code})` : msg;
      _reportApiError("POST", path, res.status, code);
      const err = new Error(withCode);
      err.apiErrorLogged = true;
      throw err;
    }
    // ストリーム開始(HTTP 200)後にサーバー側で例外が起きたケースの検出
    // (2026-09-18・Fableレビューで発見)。req()と違いヘッダーは既に200で
    // 確定済みのため、本文中にSTREAM_ERROR_MARKERを混ぜる方式でサーバー
    // (ai.STREAM_ERROR_MARKER)と合図する。
    // 2026-09-18再修正(Fable2回目レビューで発見): 最初の判定だけで
    // 「以後は無条件にonChunkへ流す」実装だと、正常な応答が何文字か
    // 届いた**後**に例外が起きるケース(例: OpenAI側が生成途中で切断)を
    // 見逃し、元のバグ(エラー文がAIの発言として扱われる)がそのまま
    // 残っていた。マーカーはどの位置に現れても検出できるよう、常に
    // 直近(マーカー長-1)文字だけ確定を保留して全チャンクを走査する
    // (マーカーがチャンクの境目で分断されても跨いで検出できる)。
    if (!res.body) {
      const text = await res.text();
      const idx = text.indexOf(STREAM_ERROR_MARKER);
      if (idx !== -1) {
        throw _streamError(
          path, text.slice(idx + STREAM_ERROR_MARKER.length));
      }
      onChunk(text);
      return;
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    const markerLen = STREAM_ERROR_MARKER.length;
    let carry = "";  // マーカーの跨ぎ検出用に確定を保留している末尾分
    try {
      for (;;) {
        const { value, done } = await reader.read();
        const piece = value ? decoder.decode(value, { stream: !done }) : "";
        const combined = carry + piece;
        const idx = combined.indexOf(STREAM_ERROR_MARKER);
        if (idx !== -1) {
          // マーカー発見: これ以降は全てエラー本文として静かに読み切る
          // (途中まで正常に見えた内容がonChunkへ渡っていても、呼び出し
          // 元はこの例外を受けてエラー表示に切り替え、履歴には積まない
          // 設計にしてある)。
          let rest = combined.slice(idx + markerLen);
          if (!done) {
            for (;;) {
              const r = await reader.read();
              if (r.done) break;
              rest += decoder.decode(r.value, { stream: true });
            }
          }
          throw _streamError(path, rest
            || "エラーが発生しました。もう一度お試しください。");
        }
        if (combined.length > markerLen - 1) {
          const safeLen = combined.length - (markerLen - 1);
          onChunk(combined.slice(0, safeLen));
          carry = combined.slice(safeLen);
        } else {
          carry = combined;
        }
        if (done) {
          if (carry) onChunk(carry);
          break;
        }
      }
    } catch (e) {
      // 2026-09-18追加(Fable2回目レビューで発見): マーカーが届く前に
      // 接続そのものが切れた場合(reader.read()自体が失敗)は、従来
      // ここが未捕捉のままerror-report.js経由にもならず、記録が一切
      // 残らなかった。呼び出し元は必ずcatchする設計なので、ここで
      // 一度だけ記録してから投げ直す。
      if (!e.apiErrorLogged) {
        _reportApiError("POST", path, 0, "STREAM_READ");
        e.apiErrorLogged = true;
      }
      throw e;
    }
  },
};
