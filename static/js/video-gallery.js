// 未登録トップの「動画で見る」ギャラリー(2026-09-20)。
//
// 方式: ポスター画像を出しておき、押した動画だけをその場で再生する(自サーバー
// 配信・自動再生なし)。音ありなので「🔊 音が流れます」を出す。縦に並べる。
// トップの初期表示を重くしないよう、views.jsのwelcome()がコンテナが画面に近づいた
// ときにだけ動的import()で読み込む(このファイルは初期JSに含まれない)。
//
// 動画を1本足す手順(本体コードは触らない):
//   1. static/video/<name>.mp4 と static/video/posters/<name>.jpg を置く
//      (作り方は scripts/videos/README.md)。
//   2. 下の VIDEOS 配列に1要素足す。差し替え/撮り直したら src/poster の ?v= を
//      上げる(/static/video/ は1年キャッシュ・immutableなので版付きURLで更新する)。

import { api } from "./api.js";
import * as speech from "./speech.js";
import { escapeHtml, go } from "./app.js";

// 表示順=配列順。
//   name     : 動画の識別名(ファイル名・計測のlabelに使う。英数字と_のみ)
//   title    : 題(カード下の見出し)
//   desc     : 1行説明
//   src/poster: 動画とポスターのURL(?v=で版付け)
//   sound    : true=「🔊 音が流れます」を出す
//   tryTab   : 見終わった後の導線先タブ(app.jsのTABSのキー)
//   tryLabel : その導線ボタンの文言
export const VIDEOS = [
  {
    name: "phrase_polite",
    title: "失礼にならない お願いの英語",
    desc: "丁寧に頼むときの言い方と、使い分けのコツ",
    src: "/static/video/phrase_polite.mp4?v=1",
    poster: "/static/video/posters/phrase_polite.jpg?v=1",
    sound: true,
    tryTab: "phrases",
    tryLabel: "ミニフレーズを試す →",
  },
];

// 計測: 既存のapi.track(kind=click)の枠で送る。サーバーの許可リスト
// (_CLIENT_TRACK_KINDS)は広げず、categoryは「今いる画面」(トップ=welcome)、
// labelを "video:<name>:<event>" にする。"video:" で始まるので他のclickと
// 区別しやすい(LIKE 'video:%')。event = play(押下)/p25/p50/ended(=100%到達・
// 終了)/try(「試す」押下)/replay/error。送信失敗は再生を妨げない(best-effort)。
const TRACK_CATEGORY = "welcome";
function track(name, event) {
  try { api.track("click", TRACK_CATEGORY, `video:${name}:${event}`); }
  catch (e) { /* 計測失敗は無視 */ }
}

// 動画のポスター状態(ボタン)のHTML。ポスター全体が押せる<button>。
function posterHtml(v) {
  const label = `${v.title}を再生${v.sound ? "(音が流れます)" : ""}`;
  // 画像は寸法(540x960=9:16)を明示して場所を確保する(CLSを出さない)。
  return `
    <button type="button" class="vg-poster" aria-label="${escapeHtml(label)}">
      <img class="vg-poster-img" src="${escapeHtml(v.poster)}" alt=""
        width="540" height="960" loading="lazy" decoding="async" />
      <span class="vg-play" aria-hidden="true"></span>
    </button>
    ${v.sound ? `<span class="vg-badge" aria-hidden="true">🔊 音が流れます</span>` : ""}`;
}

function cardHtml(v) {
  return `
    <article class="vg-card" data-name="${escapeHtml(v.name)}">
      <div class="vg-stage">${posterHtml(v)}</div>
      <h3 class="vg-card-title">${escapeHtml(v.title)}</h3>
      <p class="vg-desc muted">${escapeHtml(v.desc)}</p>
    </article>`;
}

// ギャラリー全体の状態: いま再生用<video>を持っているカード(同時に1本だけ)。
function createController(root, videos) {
  let active = null;   // {card, video, v}

  // カードをポスター状態に戻す(再生用<video>・終了/エラー表示を捨てる)。
  function resetToPoster(card, v) {
    const stage = card.querySelector(".vg-stage");
    const vid = stage.querySelector("video");
    if (vid) { try { vid.pause(); } catch (e) { /* ignore */ } vid.removeAttribute("src"); vid.load(); }
    stage.innerHTML = posterHtml(v);
    bindPoster(card, v);
    if (active && active.card === card) active = null;
  }

  // 別の動画を再生する前に、いま再生中のものをポスターに戻す(同時再生は1本だけ)。
  function stopActive() {
    if (active) resetToPoster(active.card, active.v);
  }

  function showOverlay(stage, html, extraClass = "") {
    stage.querySelector(".vg-overlay")?.remove();
    const div = document.createElement("div");
    div.className = ("vg-overlay " + extraClass).trim();
    div.innerHTML = html;
    stage.append(div);
    return div;
  }

  function startPlayback(card, v) {
    stopActive();
    // ページ内の別の音(1語サンプルの再生・ブラウザ合成音)と重ならないよう止める。
    try { speech.stopSpeaking(); } catch (e) { /* ignore */ }
    const stage = card.querySelector(".vg-stage");
    const video = document.createElement("video");
    video.className = "vg-video";
    video.controls = true;
    video.setAttribute("playsinline", "");
    video.preload = "auto";
    video.poster = v.poster;
    video.setAttribute("aria-label", v.title);
    stage.replaceChildren(video);
    active = { card, video, v };

    let reached25 = false, reached50 = false;
    const resetProgress = () => { reached25 = false; reached50 = false; };

    video.addEventListener("timeupdate", () => {
      const d = video.duration;
      if (!d || !isFinite(d)) return;
      const r = video.currentTime / d;
      if (!reached25 && r >= 0.25) { reached25 = true; track(v.name, "p25"); }
      if (!reached50 && r >= 0.5) { reached50 = true; track(v.name, "p50"); }
    });

    // ポスターに戻した(=このvideoを捨てた)後に遅れて届いたイベントは無視する。
    const isCurrent = () => active && active.video === video;

    // 終了後に「もう一度見る」または動画のコントロールから再生し直したら、
    // 終了の重ね表示を消して25/50%の到達判定をやり直す。
    video.addEventListener("play", () => {
      if (!isCurrent()) return;
      const end = stage.querySelector(".vg-overlay-end");
      if (!end) return;
      end.remove();
      resetProgress();
      track(v.name, "replay");
    });

    video.addEventListener("ended", () => {
      if (!isCurrent()) return;
      track(v.name, "ended");
      const ov = showOverlay(stage, `
        <div class="vg-end">
          <button type="button" class="btn vg-try">${escapeHtml(v.tryLabel || "試してみる →")}</button>
          <button type="button" class="btn ghost vg-replay">もう一度見る</button>
        </div>`, "vg-overlay-end");
      ov.querySelector(".vg-try").addEventListener("click", () => {
        track(v.name, "try");
        go(v.tryTab);
      });
      ov.querySelector(".vg-replay").addEventListener("click", () => {
        // 重ね表示の片付け・計測は下のplayイベントが担当する(動画のコントロール
        // から再生し直された場合と同じ経路にするため)。
        video.currentTime = 0;
        video.play().catch(() => { /* 操作の直後なので通常は通る。失敗時はコントロールで再生できる */ });
      });
      ov.querySelector(".vg-try").focus({ preventScroll: true });
    });

    // 読み込み・デコード失敗(通信断・非対応形式など)。壊れた黒い枠のままに
    // せず、分かる文言とポスターに戻す手段を出す。
    video.addEventListener("error", () => {
      if (!isCurrent()) return;
      track(v.name, "error");
      const ov = showOverlay(stage, `
        <div class="vg-end">
          <p class="vg-err" role="alert">動画を再生できませんでした</p>
          <button type="button" class="btn ghost vg-back">ポスターに戻す</button>
        </div>`);
      ov.querySelector(".vg-back").addEventListener("click", () => resetToPoster(card, v));
    });

    video.src = v.src;
    track(v.name, "play");
    // このハンドラはユーザーの押下の中で動いているので、音ありでもplay()できる。
    const p = video.play();
    // 自動再生ポリシー等で拒否されても、コントロールから再生できる(読み込み
    // 失敗は上のerrorイベントが扱う)ので、ここでは何もしない。
    if (p && p.catch) p.catch(() => {});
    video.focus({ preventScroll: true });
  }

  function bindPoster(card, v) {
    card.querySelector(".vg-poster")
      .addEventListener("click", () => startPlayback(card, v));
  }

  // 描画済みのカードにポスターの動作をつなぐ。
  root.querySelectorAll(".vg-card").forEach((card) => {
    const v = videos.find((x) => x.name === card.dataset.name);
    if (v) bindPoster(card, v);
  });
}

// container にギャラリーを描画する。VIDEOSが空/不正なら何も出さず false を返す
// (壊れたUIを出さず、他の表示に影響しない)。描画したら true。
export function renderVideoGallery(container) {
  if (!container) return false;
  const videos = (Array.isArray(VIDEOS) ? VIDEOS : []).filter((v) =>
    v && v.name && v.src && v.poster && v.title);
  if (!videos.length) return false;
  container.innerHTML = `
    <section class="vg" aria-labelledby="vgHeading">
      <div class="vg-head">
        <h2 class="vg-heading" id="vgHeading">🎬 動画で見る</h2>
        <span class="vg-sub muted">各約20秒・押すと再生</span>
      </div>
      ${videos.map(cardHtml).join("")}
    </section>`;
  createController(container, videos);
  return true;
}
