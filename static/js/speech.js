// Speech: text-to-speech (output) and speech recognition (input).
//
// Two TTS engines:
//  1) OpenAI natural voices (ChatGPT-quality) via /api/learn/tts — used when
//     AI is enabled and "自然な声" is ON. Voices are named & user-toggleable,
//     and one is chosen at random per learning round.
//  2) Browser SpeechSynthesis — free fallback when AI is off or TTS fails.

const synth = window.speechSynthesis;

// index.html/app.jsの読み込み順により、このモジュール評価時にはwindow.I18Nが
// 既にセットアップ済みのはず(app.js/quiz.jsと同じtx定義。循環import回避のため
// ここでも同じ1行を定義)。
const tx = (key, vars) => (window.I18N ? window.I18N.t(key, vars) : key);

// --- state ------------------------------------------------------------------

let aiEnabled = false;
let openaiVoices = [
  "alloy", "ash", "ballad", "coral", "echo",
  "fable", "nova", "onyx", "sage", "shimmer",
];
let currentVoiceName = null;   // chosen voice for the current round
let currentIsOpenAI = false;
let audioEl = null;            // single reused <audio> element (unlocked once)
let audioUnlocked = false;     // true after first user-gesture unlock
let usageCb = null;            // called after a paid TTS call (cost refresh)
// 2026-08-09: 無料範囲外の単語/フレーズ再生でチャージ残高不足(HTTP 402)
// のとき呼ばれる。ブラウザ音声へのフォールバックは維持しつつ、ユーザーに
// 「なぜ自然な声が出ないか」を知らせるためのトースト表示等に使う。
let paymentRequiredCb = null;
// 再生要求の連番。複数箇所（一覧の各行の🔊ボタン等）が同じ<audio>要素を共有する
// ため、古い要求のfetchが後から解決すると別の語の音声が鳴ってしまう
// （テキストと音声が一致しない不具合の原因）。常に「最後に要求された再生」だけ
// 実際に鳴らし、古い要求は結果を捨てる。
let playSeq = 0;
// 動作中の文単位パイプライン読み上げ(createSegmentSpeaker)。stopSpeaking()から止める。
let activeSegSpeaker = null;

export function setAiEnabled(v) { aiEnabled = !!v; }
export function setOpenAIVoices(list) {
  if (Array.isArray(list) && list.length) openaiVoices = list;
}
export function listOpenAIVoices() { return openaiVoices.slice(); }
export function onUsage(cb) { usageCb = cb; }
export function onPaymentRequired(cb) { paymentRequiredCb = cb; }

// natural-voice preference (localStorage)
export function isNatural() {
  return localStorage.getItem("naturalVoice") !== "0";
}
export function setNatural(on) {
  localStorage.setItem("naturalVoice", on ? "1" : "0");
}

// Auto-submit after voice recognition (default ON for tempo).
export function isVoiceAutoSubmit() {
  return localStorage.getItem("voiceAutoSubmit") !== "0";
}
export function setVoiceAutoSubmit(on) {
  localStorage.setItem("voiceAutoSubmit", on ? "1" : "0");
}

// --- enabled OpenAI voice set ----------------------------------------------

const LS_OPENAI = "tts_openai_enabled";

export function loadEnabledOpenAI() {
  try {
    const raw = localStorage.getItem(LS_OPENAI);
    if (raw) return new Set(JSON.parse(raw));
  } catch (e) { /* ignore */ }
  return null; // null => all enabled
}
export function setOpenAIVoiceEnabled(name, enabled) {
  let set = loadEnabledOpenAI();
  if (set === null) set = new Set(openaiVoices);
  if (enabled) set.add(name); else set.delete(name);
  localStorage.setItem(LS_OPENAI, JSON.stringify([...set]));
}
export function isOpenAIVoiceEnabled(name) {
  const set = loadEnabledOpenAI();
  return set === null ? true : set.has(name);
}
function enabledOpenAIList() {
  const set = loadEnabledOpenAI();
  if (set === null) return openaiVoices;
  const f = openaiVoices.filter((v) => set.has(v));
  return f.length ? f : openaiVoices;
}

// --- browser voices ---------------------------------------------------------

export function ttsSupported() { return "speechSynthesis" in window; }

export function getEnglishVoices() {
  const all = synth ? synth.getVoices() : [];
  return all.filter((v) => v.lang && v.lang.toLowerCase().startsWith("en"));
}
if (synth) synth.onvoiceschanged = () => getEnglishVoices();

// --- per-round voice selection ---------------------------------------------

export function pickRoundVoice() {
  if (isNatural() && aiEnabled) {
    const pool = enabledOpenAIList();
    currentVoiceName = pool[Math.floor(Math.random() * pool.length)];
    currentIsOpenAI = true;
  } else {
    const pool = getEnglishVoices();
    currentVoiceName = pool.length
      ? pool[Math.floor(Math.random() * pool.length)].name : null;
    currentIsOpenAI = false;
  }
  return currentVoiceName;
}

export function currentVoice() { return currentVoiceName; }

// OpenAI音声のおおよその性別（UI表示用）。
const VOICE_GENDER_KEY = {
  alloy: "voice.genderNeutral", ash: "voice.genderMale",
  ballad: "voice.genderMale", coral: "voice.genderFemale",
  echo: "voice.genderMale", fable: "voice.genderMale",
  nova: "voice.genderFemale", onyx: "voice.genderMale",
  sage: "voice.genderFemale", shimmer: "voice.genderFemale",
};
export function voiceGender(name) {
  const key = VOICE_GENDER_KEY[name];
  return key ? tx(key) : "";
}

// 会話で使う声を明示選択して記憶（localStorage）。以後はこの声で読み上げる。
export function setVoice(name) {
  if (!openaiVoices.includes(name)) return false;
  currentVoiceName = name; currentIsOpenAI = true;
  localStorage.setItem("convVoice", name);
  return true;
}
export function loadPreferredVoice() {
  return localStorage.getItem("convVoice") || "";
}

// --- iOS/Safari audio unlock ------------------------------------------------
// iOS/iPadOS では「音声再生はユーザー操作の直後でないと禁止」される。iPad 上の
// Chrome/Edge も中身は WebKit なので同じ制限。対策は (1) <audio> を1つだけ使い回し
// (毎回 new Audio() しない)、(2) 最初のタップ等で無音を鳴らして「解錠」しておく。
// 解錠済みの要素なら、以後は await をまたいだ自動再生(会話の読み上げ等)も鳴る。
// デスクトップ各ブラウザ(Win/macOS/Android の Chrome/Edge/Firefox/Safari)では
// 実質 no-op で無害。
const SILENT_WAV =
  "data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQAAAAA=";

function audioElement() {
  if (!audioEl) {
    audioEl = new Audio();
    try { audioEl.setAttribute("playsinline", ""); } catch (e) { /* ignore */ }
    // 再生速度を変えても音程(ピッチ)は変えない。既定でtrueのブラウザが
    // ほとんどだが、明示しておかないと環境によっては声が高く/低くなり
    // 「早送り」に聞こえてしまう（2026-08-22・ネイティブ速度の調整時）。
    // 旧仕様のベンダー接頭辞付きプロパティにも同じ値を入れておく。
    try {
      audioEl.preservesPitch = true;
      audioEl.mozPreservesPitch = true;
      audioEl.webkitPreservesPitch = true;
    } catch (e) { /* ignore */ }
  }
  return audioEl;
}

export function unlockAudio() {
  try {
    const a = audioElement();
    if (!a.src) a.src = SILENT_WAV;
    const p = a.play();
    if (p && p.then) {
      p.then(() => { try { a.pause(); a.currentTime = 0; } catch (e) {} })
       .catch(() => { /* ignore — まだ操作が無い等 */ });
    }
  } catch (e) { /* ignore */ }
  try {
    if (synth && !audioUnlocked) synth.speak(new SpeechSynthesisUtterance(""));
  } catch (e) { /* ignore */ }
  audioUnlocked = true;
}

// 最初のユーザー操作(どのボタン/キーでもOK)で自動的に解錠する。
if (typeof window !== "undefined" && window.addEventListener) {
  const onceUnlock = () => {
    unlockAudio();
    window.removeEventListener("pointerdown", onceUnlock);
    window.removeEventListener("touchend", onceUnlock);
    window.removeEventListener("keydown", onceUnlock);
  };
  window.addEventListener("pointerdown", onceUnlock);
  window.addEventListener("touchend", onceUnlock);
  window.addEventListener("keydown", onceUnlock);
}

// Play a TTS Blob on the single reused (and unlocked) audio element.
async function playBlob(blob, rate, voice) {
  stopSpeaking();
  const a = audioElement();
  try { if (a._objUrl) URL.revokeObjectURL(a._objUrl); } catch (e) { /* ignore */ }
  a._objUrl = URL.createObjectURL(blob);
  a.onended = null; a.onerror = null;   // clear stale handlers (speakAndWait)
  a.src = a._objUrl;
  a.playbackRate = effectiveRate(voice, rate);
  await a.play();
}

// --- speaking ---------------------------------------------------------------

export function stopSpeaking() {
  // 文単位のパイプライン読み上げ(createSegmentSpeaker)が動いていれば、それも
  // 止める(⏹や画面遷移・別の読み上げの開始で、次の文が勝手に鳴り出さないように)。
  if (activeSegSpeaker) activeSegSpeaker._abort();
  stopAudioOnly();
}

function stopAudioOnly() {
  if (synth) synth.cancel();
  if (audioEl) { try { audioEl.pause(); } catch (e) { /* ignore */ } }
}

// --- 再生失敗の扱い(2026-09-26・オーナー決定「変な声が鳴るくらいなら無音のほうがよい」) -----------
// ブラウザ内蔵の音声(SpeechSynthesis)に切り替えるのは、**利用者が設定で「自然な音声」をOFFにしたときだけ**。
// 通信の失敗・再生の失敗・AI音声が使えない状態では、鳴らさず(無音)、短い案内を出し、サーバーへエラーとして
// 記録する(kind="playback_error"・管理画面のクライアントエラーログで検知できる)。以前は、通信失敗のほか
// 「新しい再生に取って代わられた(AbortError)」「自動再生の制限(NotAllowedError)」でも、catchがブラウザ音声へ
// 逃げていたため、しわがれ声(端末標準の古い声)が突然鳴ることがあった。
let playbackErrorCb = null;
export function onPlaybackError(cb) { playbackErrorCb = cb; }
const _playbackReportedAt = {};
function reportPlaybackError(reason, detail) {
  const now = Date.now();
  if (now - (_playbackReportedAt[reason] || 0) < 15000) return;   // 同じ理由は15秒に1回(連打で溢れさせない)
  _playbackReportedAt[reason] = now;
  try {
    const d = detail && (detail.message || detail.name) ? (detail.name || "") + " " + (detail.message || "") : String(detail || "");
    fetch("/api/system/client-error", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        kind: "playback_error",
        message: reason + (d.trim() ? ": " + d.trim().slice(0, 80) : ""),
        url: String(location.pathname || ""),   // クエリは送らない
      }),
    }).catch(() => {});
  } catch (e) { /* 記録の失敗で画面を妨げない */ }
}
const _playbackToastedAt = {};
function playbackFailed(reason, detail) {
  reportPlaybackError(reason, detail);
  // 同じ理由のトーストは5秒に1回(フラッシュ/クイズの自動読み上げでカードごとに出続けないように)。
  const now = Date.now();
  if (now - (_playbackToastedAt[reason] || 0) < 5000) return;
  _playbackToastedAt[reason] = now;
  // 理由別の文言: 通信の失敗だけ「通信状況を確認して」。自動再生の制限は「タップして」・それ以外は「今は再生できません」。
  const key = reason === "network" ? "voice.playbackFailed"
    : (reason === "autoplay_blocked" ? "voice.playbackTapToPlay" : "voice.playbackUnavailable");
  if (playbackErrorCb) playbackErrorCb(tx(key));
}
// 再生(fetch/デコード/play())の失敗の理由。"" = 失敗ではない(新しい再生に取って代わられた等)。
function playFailureReason(e, stage) {
  if (e && e.name === "AbortError") return "";
  if (stage === "network") return "network";
  return e && e.name === "NotAllowedError" ? "autoplay_blocked" : "play_error";
}
// ハンズフリー中は画面を見ていないので、声ではなく短い「ピッ」で失敗を知らせる(声は使わない)。
export function playErrorTone() {
  try {
    const AC = window.AudioContext || window.webkitAudioContext; if (!AC) return;
    const ctx = new AC();
    if (ctx.state === "suspended" && ctx.resume) ctx.resume().catch(() => {});
    const o = ctx.createOscillator(), g = ctx.createGain();
    o.type = "sine"; o.frequency.value = 330; g.gain.value = 0.08;
    o.connect(g); g.connect(ctx.destination); o.start(); o.stop(ctx.currentTime + 0.25);
    // suspendedのままだとonendedが来ないため、時間でも必ず閉じる(リソースを残さない)
    setTimeout(() => { try { ctx.close(); } catch (e) { /* ignore */ } }, 600);
  } catch (e) { /* 音が出せなくても無害 */ }
}

function browserSpeak(text, opts = {}) {
  if (!synth || !text) return;
  synth.cancel();
  const u = new SpeechSynthesisUtterance(text);
  const voices = getEnglishVoices();
  let chosen = !currentIsOpenAI && currentVoiceName
    ? voices.find((v) => v.name === currentVoiceName) : null;
  if (chosen) { u.voice = chosen; u.lang = chosen.lang; }
  else u.lang = "en-US";
  u.rate = opts.rate || playbackRate || 0.95;
  synth.speak(u);
}

// Main entry: speak with the best available engine.
// opts.feature: サーバー側の課金カテゴリのヒント（例: "reading_tts",
// "listening_tts"）。未指定なら汎用tts扱い（呼び出し元不明時の既定倍率）。
export async function say(text, opts = {}) {
  if (!text) return;
  if (!isNatural()) { browserSpeak(text, opts); return; }   // 利用者が設定で選んだブラウザ音声
  if (!aiEnabled) { playbackFailed("ai_unavailable"); return; }
  // Ensure we have an OpenAI voice selected for this round.
  if (!currentIsOpenAI || !currentVoiceName) pickRoundVoice();
  const myToken = ++playSeq;
  let stage = "network";
  try {
    const body = { text, voice: currentVoiceName };
    if (opts.feature) body.feature = opts.feature;
    const res = await fetch("/api/learn/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      // サーバーが明示的に拒否(要ログイン/要チャージ等の402/422)した場合は
      // ブラウザ音声へフォールバックしない。変な声で鳴るくらいなら案内
      // メッセージの方がよい、というsayItemと同じ方針に揃える(2026-08-13、
      // Reading/Listening/英会話/Writingがしわがれ声になっていた不具合対応)。
      if (myToken === playSeq && paymentRequiredCb) {
        const msg = await res.text().catch(() => "");
        paymentRequiredCb(msg || tx("voice.playbackUnavailable"));
      }
      return;
    }
    const blob = await res.blob();
    stage = "play";
    if (myToken !== playSeq) return; // 新しい再生要求が来ていた→古い音声は捨てる
    await playBlob(blob, opts.rate, currentVoiceName);
    if (usageCb) usageCb();
  } catch (e) {
    // ブラウザ音声へは逃げない(無音+案内+エラー記録)。新しい再生に取って代わられた場合は失敗ではない。
    if (myToken !== playSeq) return;
    const why = playFailureReason(e, stage);
    if (why) playbackFailed(why, e);
  }
}

// Speak text with a SPECIFIC OpenAI voice (used by the 男声/女声 play buttons
// in the word & phrase lists). Falls back to the browser voice when natural
// TTS is off or the call fails. Mirrors say()/previewOpenAIVoice().
export async function sayWithVoice(text, voice, opts = {}) {
  if (!text) return;
  if (!isNatural()) { browserSpeak(text, opts); return; }   // 利用者が設定で選んだブラウザ音声
  if (!aiEnabled) { playbackFailed("ai_unavailable"); return; }
  const myToken = ++playSeq;
  let stage = "network";
  try {
    const res = await fetch("/api/learn/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice }),
    });
    if (!res.ok) {
      // say()と同じ方針: 意図的な拒否ではブラウザ音声へ逃げない(2026-08-13)。
      if (myToken === playSeq && paymentRequiredCb) {
        const msg = await res.text().catch(() => "");
        paymentRequiredCb(msg || tx("voice.playbackUnavailable"));
      }
      return;
    }
    const blob = await res.blob();
    stage = "play";
    if (myToken !== playSeq) return; // 新しい再生要求が来ていた→古い音声は捨てる
    await playBlob(blob, opts.rate, voice);
    if (usageCb) usageCb();
  } catch (e) {
    if (myToken !== playSeq) return;
    const why = playFailureReason(e, stage);
    if (why) playbackFailed(why, e);
  }
}

// 声ごとの再生速度補正(2026-09-20)。男声(ash)は女声(nova)より発話が遅く
// 聞こえる(実測: 前後の無音を除いた発話区間の長さの中央値がash/nova=1.14、
// 単語1.17・例文1.09〜1.22・フレーズ1.14〜1.19)。音声ファイルは触らず、
// 再生時だけ速さを掛けて体感をそろえる(音程は変わらない)。元に戻す/
// 調整するときはこの値を変えるだけ(1にすれば補正なし)。
const VOICE_RATE_FACTOR = { ash: 1.15 };
function voiceFactor(voice) { return VOICE_RATE_FACTOR[voice] || 1; }
let playingVoice = "";   // 最後に再生した声(再生速度ボタンで再計算するため)
function effectiveRate(voice, rate) {
  playingVoice = voice || "";
  return (rate || playbackRate) * voiceFactor(voice);
}

// Global playback speed (再生速度ボタン用)。音程は変えず速さだけ変える。
let playbackRate = parseFloat(localStorage.getItem("playbackRate") || "1") || 1;
export function getPlaybackRate() { return playbackRate; }
export function setPlaybackRate(r) {
  playbackRate = r;
  localStorage.setItem("playbackRate", String(r));
  if (audioEl) audioEl.playbackRate = r * voiceFactor(playingVoice);
}

// Play by item 番号(ID): the server returns saved audio for free (no token)
// or synthesizes once and saves it, so 2回目以降は無料。Falls back to the
// browser voice when natural TTS is off / AI is unavailable / the call fails.
//   itemType: 'word' | 'phrase', kind: 'word' | 'example' | 'phrase'
//   speed: 'learn'(学習・ゆっくり明瞭) | 'native'(自然な速さ) — 別音声を取得
export async function sayItem(
  itemType, id, kind, voice, fallbackText, opts = {}
) {
  if (!isNatural()) {   // 利用者が設定で選んだブラウザ音声
    if (fallbackText) browserSpeak(fallbackText, opts);
    return;
  }
  if (!aiEnabled) { playbackFailed("ai_unavailable"); return; }
  const q = new URLSearchParams({
    item_type: itemType, item_id: id, kind, voice,
    speed: opts.speed || "learn",
  });
  const myToken = ++playSeq;
  let stage = "network";
  try {
    const res = await fetch("/api/learn/tts/item?" + q.toString());
    if (!res.ok) {
      // 無料範囲外・要ログイン(402)・合成失敗(422)等、サーバーが返した
      // 意図的なブロック/エラー。ブラウザ音声へのフォールバックはしない
      // （変な声で鳴るくらいなら無音の方がよい、という2026-08-11ユーザー
      // 指摘。422も同様に扱う: 2026-08-12・ゲスト無料枠0円化で未キャッシュ
      // の無料範囲フレーズが合成失敗→しわがれ声になっていた不具合対応）。
      if (paymentRequiredCb) {
        const msg = await res.text().catch(() => "");
        // サーバーからの案内文が必ず状況(要ログイン/要チャージ)に応じて
        // 出るので、ここでの既定文言は状況を決めつけない中立な文にする
        // （2026-08-11: 「ログインすると聴けます」固定だと、ログイン済み
        // ユーザーの要チャージのケースまで誤って「要ログイン」と案内して
        // しまい苦情の原因になるため）。
        paymentRequiredCb(msg || tx("voice.playbackUnavailable"));
      }
      return;
    }
    const blob = await res.blob();
    stage = "play";
    if (myToken !== playSeq) return; // 新しい再生要求が来ていた→古い音声は捨てる
    await playBlob(blob, opts.rate, voice);
    if (usageCb) usageCb();
  } catch (e) {
    if (myToken !== playSeq) return;
    const why = playFailureReason(e, stage);
    if (why) playbackFailed(why, e);
  }
}

// 原語の音声(詳細plus・VOICEVOX・2026-09-26)を専用URL(ログイン・開いた済みの検査つき)から再生する。
// 成功でtrue・失敗(未開封/要ログイン/ネットワーク等)でfalse。ブラウザ音声へのフォールバックはしない
// (原語は日本語なのでブラウザの英語音声で鳴らすと誤読になる)。速度は再生速度ボタンに従う。
export async function sayNativeAudio(url) {
  const myToken = ++playSeq;
  try {
    const res = await fetch(url);
    if (!res.ok) return false;
    const blob = await res.blob();
    if (myToken !== playSeq) return true;   // 新しい再生要求が来ていた→古い音声は捨てる
    await playBlob(blob, undefined, "native");
    return true;
  } catch (e) {
    // 連打で新しい再生要求が来ると、古い再生のplay()はAbortErrorで拒否される。それは失敗ではない(Fable指摘)。
    return myToken !== playSeq;
  }
}

// Play a public sample material(id)の読み上げ(2026-08-13)。サンプル教材は
// 誰が読んでも同じ固定テキストなので/api/learn/samples/{id}/ttsが未ログイン・
// 無課金でも無料(サーバー側でis_public_sample検証・単語/フレーズのsayItemと
// 同じ「意図的なエラーはブラウザ音声へフォールバックしない」方針を踏襲)。
export async function sayMaterial(materialId, voice, opts = {}) {
  const myToken = ++playSeq;
  try {
    const q = new URLSearchParams({ voice });
    const res = await fetch(
      `/api/learn/samples/${materialId}/tts?${q.toString()}`);
    if (!res.ok) {
      if (paymentRequiredCb) {
        const msg = await res.text().catch(() => "");
        paymentRequiredCb(msg || tx("voice.playbackUnavailable"));
      }
      return;
    }
    const blob = await res.blob();
    if (myToken !== playSeq) return; // 新しい再生要求が来ていた→古い音声は捨てる
    await playBlob(blob, opts.rate, voice);
    if (usageCb) usageCb();
  } catch (e) {
    // ネットワーク到達不能等。テキストは呼び出し側で保持していないため
    // ブラウザ音声へのフォールバックはしない(sayItemと異なりfallbackText
    // を受け取らない設計 — 案内なしの声質変化を避ける)。
  }
}

// Like sayItem(), but resolves when the audio FINISHES (ended/error). 連続読み上げ
// (単語→例文)に使う。stopSpeaking() で中断された場合は ended が来ないので、呼び側で
// シーケンス番号を見て打ち切ること。
export function sayItemAndWait(itemType, id, kind, voice, fallbackText, opts = {}) {
  return new Promise((resolve) => {
    let stage = "network";
    const browser = () => {
      if (!fallbackText || !synth) { resolve(); return; }
      synth.cancel();
      const u = new SpeechSynthesisUtterance(fallbackText);
      u.lang = "en-US"; u.rate = opts.rate || playbackRate || 0.95;
      u.onend = () => resolve(); u.onerror = () => resolve();
      synth.speak(u);
    };
    if (!isNatural()) { browser(); return; }   // 利用者が設定で選んだブラウザ音声
    if (!aiEnabled) { playbackFailed("ai_unavailable"); resolve(); return; }
    const q = new URLSearchParams({
      item_type: itemType, item_id: id, kind, voice,
      speed: opts.speed || "learn",
    });
    const myToken = ++playSeq;
    fetch("/api/learn/tts/item?" + q.toString())
      .then((res) => {
        if (res.ok) return res.blob();
        // 無料範囲外・要ログイン(402)・合成失敗(422)等、サーバーが返した
        // 意図的なブロック/エラー。ブラウザ音声へのフォールバックはせず、
        // 案内メッセージだけ出して静かに終える(2026-08-11ユーザー指摘。
        // 422も同様に扱う: 2026-08-12・しわがれ声バグ対応)。
        return res.text().then((msg) => {
          if (paymentRequiredCb) {
            // サーバーからの案内文が必ず状況(要ログイン/要チャージ)に応じて
            // 出るので、ここでの既定文言は状況を決めつけない中立な文にする
            // （2026-08-11: 「ログインすると聴けます」固定だと、ログイン済み
            // ユーザーの要チャージのケースまで誤って「要ログイン」と案内して
            // しまい苦情の原因になるため）。
            paymentRequiredCb(msg || tx("voice.playbackUnavailable"));
          }
          const err = new Error("payment required");
          err.paymentRequired = true;
          throw err;
        });
      })
      .then((blob) => {
        stage = "play";
        if (myToken !== playSeq) { resolve(); return; } // 古い要求→捨てて即解決
        stopSpeaking();
        const a = audioElement();
        try { if (a._objUrl) URL.revokeObjectURL(a._objUrl); } catch (e) {}
        a._objUrl = URL.createObjectURL(blob);
        a.src = a._objUrl;
        a.playbackRate = effectiveRate(voice, opts.rate);
        a.onended = () => resolve();
        a.onerror = () => resolve();
        const pl = a.play();
        if (pl && pl.catch) pl.catch((e) => {
          const why = myToken === playSeq ? playFailureReason(e, "play") : "";
          if (why) playbackFailed(why, e);
          resolve();
        });
        if (usageCb) usageCb();
      })
      .catch((err) => {
        if (err && err.paymentRequired) { resolve(); return; }
        const why = myToken === playSeq ? playFailureReason(err, stage) : "";
        if (why) playbackFailed(why, err);
        resolve();   // ブラウザ音声へは逃げない
      });
  });
}

// Speak with a specific OpenAI voice (for the settings preview button).
// Returns { ok, error } so the UI can show the real reason on failure.
export async function previewOpenAIVoice(voice, text) {
  const myToken = ++playSeq;
  try {
    const res = await fetch("/api/learn/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice }),
    });
    if (!res.ok) {
      const msg = await res.text();
      return { ok: false, error: msg || `HTTP ${res.status}` };
    }
    const blob = await res.blob();
    if (myToken !== playSeq) return { ok: true }; // 新しい要求が来ていた→捨てる
    await playBlob(blob, 1, voice);
    if (usageCb) usageCb();
    return { ok: true };
  } catch (e) {
    return { ok: false, error: e.message };
  }
}

// Back-compat alias used by older call sites.
export const speak = say;

// --- Speech recognition (input) --------------------------------------------

const SR = window.SpeechRecognition || window.webkitSpeechRecognition;

// Only one recognition can run at a time. Track it so we can always force-stop
// the previous one before starting a new one (fixes "2回目が動かない").
let activeRec = null;

export function sttSupported() { return !!SR; }

// Force-abort any running recognition (used as a global 強制中止).
export function abortListening() {
  if (activeRec) {
    try { activeRec.abort(); } catch (e) { /* ignore */ }
    activeRec = null;
  }
}

// AI recorder: records mic audio and transcribes via the backend (Whisper),
// which AUTO-DETECTS the language and handles non-native English far better
// than the browser recognizer. Same {start, stop()->text} shape.
export function aiSttSupported() {
  return !!(navigator.mediaDevices && window.MediaRecorder);
}

export async function createAIRecorder(language = "") {
  if (!aiSttSupported()) throw new Error(tx("voice.recordingUnsupported"));
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const chunks = [];
  const mr = new MediaRecorder(stream);
  mr.ondataavailable = (e) => { if (e.data && e.data.size) chunks.push(e.data); };
  mr.start();
  return {
    start() { /* already recording */ },
    stop() {
      return new Promise((resolve) => {
        mr.onstop = async () => {
          stream.getTracks().forEach((t) => t.stop());
          const blob = new Blob(chunks, { type: mr.mimeType || "audio/webm" });
          try {
            const fd = new FormData();
            fd.append("file", blob, "audio.webm");
            if (language) fd.append("language", language);
            const res = await fetch("/api/learn/transcribe", {
              method: "POST", body: fd,
            });
            const d = await res.json();
            if (usageCb) usageCb();
            resolve(d && d.ok ? (d.text || "") : "");
          } catch (e) { resolve(""); }
        };
        try { mr.stop(); } catch (e) { resolve(""); }
      });
    },
  };
}

// Like say(), but resolves when the audio FINISHES (for hands-free flow:
// resume listening only after the AI has stopped talking).
// 戻り値: true=再生し終えた/false=再生できなかった(呼び出し側=聞き流しのループは、続けて失敗したら止める・2026-09-26 Fable照査M1)。
export function speakAndWait(text, opts = {}) {
  return new Promise((resolve) => {
    let stage = "network";
    if (!text || !text.trim()) { resolve(true); return; }
    const browser = () => {
      if (!synth) { resolve(false); return; }
      synth.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = opts.lang || "en-US"; u.rate = opts.rate || playbackRate || 0.95;
      u.onend = () => resolve(true); u.onerror = () => resolve(false);
      synth.speak(u);
    };
    // opts.forceBrowser: 常にブラウザ内蔵音声のみを使う(2026-09-18・
    // 会話ストリームのエラー通知用に追加)。エラーが起きた直後に、また
    // 有料のAI音声(/api/learn/tts)を叩いて二重に失敗しうる経路へ入らない
    // ようにするため(Fable2回目レビュー指摘)。日本語文言なので
    // opts.langで発音言語も指定できるようにした。
    // 2026-09-26(オーナー決定): forceBrowserでもブラウザ音声(声)は使わない。ハンズフリー中のエラー通知は短い
    // 「ピッ」(声なし)で知らせる。画面のエラー表示は呼び出し側が出している。
    if (opts.forceBrowser) { playErrorTone(); setTimeout(() => resolve(true), 350); return; }
    if (!isNatural()) { browser(); return; }   // 利用者が設定で選んだブラウザ音声
    if (!aiEnabled) { playbackFailed("ai_unavailable"); resolve(false); return; }
    if (!currentIsOpenAI || !currentVoiceName) pickRoundVoice();
    const body = { text, voice: currentVoiceName };
    if (opts.feature) body.feature = opts.feature;
    fetch("/api/learn/tts", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(async (r) => {
      if (!r.ok) {
        // 意図的な拒否(402/422等)ではブラウザ音声へ逃げず、案内して
        // 終える(sayItem/say()と同じ方針・2026-08-13)。
        if (paymentRequiredCb) {
          const msg = await r.text().catch(() => "");
          paymentRequiredCb(msg || tx("voice.playbackUnavailable"));
        }
        resolve(false);
        return null;
      }
      return r.blob();
    }).then((blob) => {
        stage = "play";
        if (!blob) return; // 上のresolve()で既に終えている(意図的な拒否)
        stopSpeaking();
        const a = audioElement();
        try { if (a._objUrl) URL.revokeObjectURL(a._objUrl); } catch (e) {}
        a._objUrl = URL.createObjectURL(blob);
        a.src = a._objUrl;
        a.playbackRate = effectiveRate(currentVoiceName, opts.rate);
        a.onended = () => resolve(true);
        a.onerror = () => resolve(false);
        const pl = a.play();
        if (pl && pl.catch) pl.catch((e) => {
          const why = playFailureReason(e, "play");
          if (why) playbackFailed(why, e);
          resolve(false);
        });
        if (usageCb) usageCb();
      }).catch((e) => {
        // ブラウザ音声へは逃げない(無音+案内+エラー記録)
        const why = playFailureReason(e, stage);
        if (why) playbackFailed(why, e);
        resolve(false);
      });
  });
}

// --- 文単位のパイプライン読み上げ(2026-09-26・英会話の応答速度改善) -------------
// 会話の返答(LLM)が全部出るのを待たず、最初の文ができた時点でTTSを始める。
// add(text)で渡した「区切り(セグメント)」ごとに、その場で/api/learn/ttsを並行して
// 呼び(合成待ちが重ならない)、順番どおりに1つの<audio>で再生する。前の区切りを
// 再生している間に次の区切りの合成が終わるので、区切りの間はほぼ途切れない。
//   add(text)   … 区切りを1つ追加(直ちに合成を開始)
//   finish()    … もう追加しない(全部再生し終えたらdoneが解決)
//   cancel()    … 中断(再生中の音声も止める・以後の追加は無視)
//   done        … 再生が終わった/中断/失敗のいずれかで解決するPromise(ハンズフリーが
//                 「AIが話し終えてから聞き取りを再開する」ために待つ)
// 失敗時の扱いはsay()と同じ: サーバーが意図的に拒否(402/422等)したら案内だけ出し、ネットワーク到達不能でも
// ブラウザ音声へは逃げない(2026-09-26・無音+案内+エラー記録)。ブラウザ音声は利用者が設定でOFFにした場合のみ。
// グループID(group)は同じ返答のセグメントを束ねる使い捨ての乱数で、サーバーは
// 課金・分間レート制限をセグメントに分けなかった場合と同じにそろえる(ai.py参照)。
export function createSegmentSpeaker() {
  // wantBrowser=利用者が設定で選んだブラウザ音声(唯一の例外)。natural ONでAIが使えない状態は無音+案内+エラー記録。
  const wantBrowser = !isNatural();
  const aiDown = !wantBrowser && !aiEnabled;
  const useAI = !wantBrowser && aiEnabled;
  if (useAI && (!currentIsOpenAI || !currentVoiceName)) pickRoundVoice();
  const voice = currentVoiceName;
  const group = "rs" + Math.random().toString(36).slice(2, 12)
    + Date.now().toString(36);
  if (activeSegSpeaker) activeSegSpeaker._abort();
  const myToken = ++playSeq;
  const segs = [];
  let finished = false, cancelled = false, pumping = false;
  let blocked = false, noticeShown = false;
  let started = false, usageReported = false;
  let wake = null, endPlaying = null;
  let resolveDone;
  const done = new Promise((r) => { resolveDone = r; });
  const owns = () => !cancelled && myToken === playSeq;
  const notify = () => { if (wake) { const w = wake; wake = null; w(); } };

  function fetchSeg(text) {
    return fetch("/api/learn/tts", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice, group }),
    }).then(async (res) => {
      if (!res.ok) return { blocked: true, msg: await res.text().catch(() => "") };
      return { blob: await res.blob() };
    }).catch(() => ({ net: true }));
  }

  function speakBrowserSeg(text) {
    return new Promise((resolve) => {
      if (!synth || !text) { resolve(); return; }
      const u = new SpeechSynthesisUtterance(text);
      const chosen = !currentIsOpenAI && currentVoiceName
        ? getEnglishVoices().find((v) => v.name === currentVoiceName) : null;
      if (chosen) { u.voice = chosen; u.lang = chosen.lang; }
      else u.lang = "en-US";
      u.rate = playbackRate || 0.95;
      u.onend = () => resolve(); u.onerror = () => resolve();
      endPlaying = resolve;
      synth.speak(u);
    });
  }

  function playBlobSeg(blob) {
    return new Promise((resolve) => {
      const a = audioElement();
      try { if (a._objUrl) URL.revokeObjectURL(a._objUrl); } catch (e) { /* ignore */ }
      a._objUrl = URL.createObjectURL(blob);
      endPlaying = resolve;
      a.onended = () => resolve(); a.onerror = () => resolve();
      a.src = a._objUrl;
      a.playbackRate = effectiveRate(voice, undefined);
      const p = a.play();
      if (p && p.catch) p.catch((e) => {
        const why = playFailureReason(e, "play");
        if (why && !noticeShown) { noticeShown = true; playbackFailed(why, e); }
        resolve();
      });
    });
  }

  async function playSeg(seg) {
    if (wantBrowser) {
      await speakBrowserSeg(seg.text); started = true; return;
    }
    if (aiDown) {
      if (!noticeShown) { noticeShown = true; playbackFailed("ai_unavailable"); }
      blocked = true; return;
    }
    const r = await seg.p;
    if (!owns()) return;
    if (r.blob) {
      // 費用表示の更新はsay()と同様、最初の区切りを鳴らし始めた時点で1回
      // (区切りごとには呼ばない・全部終わった後にもう1回はpumpの最後で)。
      if (!usageReported) { usageReported = true; if (usageCb) usageCb(); }
      await playBlobSeg(r.blob); started = true;
      return;
    }
    if (r.blocked) {
      // 意図的な拒否(要ログイン/要チャージ等)。say()と同じく案内だけ出し、
      // ブラウザ音声へは逃げない。この区切りは飛ばし、以後の新しい合成も
      // 頼まない(blocked)。既に合成が済んだ(=課金済みの)後続の区切りは、
      // 鳴らさず捨てるのはもったいないので、そのまま順に再生する。
      if (!noticeShown && paymentRequiredCb) {
        noticeShown = true;
        paymentRequiredCb(r.msg || tx("voice.playbackUnavailable"));
      }
      blocked = true; return;
    }
    // ネットワーク到達不能: ブラウザ音声へは逃げない(2026-09-26・オーナー決定)。無音+案内+エラー記録で、
    // 以後の新しい合成は頼まない(blocked)。既に取得済みの後続の区切りはそのまま再生する。
    if (!noticeShown) { noticeShown = true; playbackFailed("network"); }
    blocked = true;
  }

  async function pump() {
    if (pumping) return;
    pumping = true;
    try {
      // 最初の区切りを鳴らす前に、鳴っている前の音声を止める(playBlobと同じ)。
      // 自分が現役のときだけ(別の読み上げに取って代わられていたら止めない)。
      if (owns()) stopAudioOnly();
      let i = 0;
      while (owns()) {
        if (i >= segs.length) {
          if (finished) break;
          await new Promise((r) => { wake = r; });
          continue;
        }
        await playSeg(segs[i++]);
      }
    } finally {
      pumping = false; endPlaying = null;
      if (activeSegSpeaker === api) activeSegSpeaker = null;
      // 区切りが複数あった分の費用表示を、最後にもう1回更新する。
      if (segs.length > 1 && usageReported && usageCb) usageCb();
      resolveDone();
    }
  }

  const api = {
    add(text) {
      if (cancelled || finished || !text || !text.trim()) return;
      // 生成中に別の読み上げ(🔊等)が始まっていたら、こちらは引退する(合成を頼んで
      // 課金だけされたり、相手の再生を止めたりしない)。サーバーが拒否した後も同様。
      if (!owns()) { api._abort(); return; }
      if (blocked) return;
      const seg = { text, p: null };
      if (useAI) seg.p = fetchSeg(text);
      segs.push(seg);
      if (!pumping) pump().catch((e) => console.error("segment speaker", e));
      else notify();
    },
    finish() {
      if (finished) return done;
      finished = true;
      if (!pumping && !segs.length) {
        if (activeSegSpeaker === api) activeSegSpeaker = null;
        resolveDone();
      } else notify();
      return done;
    },
    cancel() {
      const mine = owns();
      api._abort();
      if (mine) stopAudioOnly();
    },
    _abort() {
      if (cancelled) return;
      cancelled = true;
      if (endPlaying) endPlaying();
      notify();
      if (!pumping) {
        if (activeSegSpeaker === api) activeSegSpeaker = null;
        resolveDone();
      }
    },
    get done() { return done; },
    get started() { return started; },
  };
  activeSegSpeaker = api;
  return api;
}

// Transcribe an audio Blob via the backend (Whisper). Returns text ("" on
// fail). language: 認識言語ヒント("en" / "en,ja" / "" など)。
export async function transcribeBlob(blob, language = "") {
  try {
    const fd = new FormData();
    fd.append("file", blob, "audio.webm");
    if (language) fd.append("language", language);
    const res = await fetch("/api/learn/transcribe", { method: "POST",
      body: fd });
    const d = await res.json();
    if (usageCb) usageCb();
    return d && d.ok ? (d.text || "") : "";
  } catch (e) { return ""; }
}

// ---------------------------------------------------------------------------
// ハンズフリー会話: Web Audio で音量を監視し、ロジックで発話の切れ目(無音)を
// 検出する（AIは使わない）。無音が一定時間続いたら1発話として確定し onUtterance
// に音声Blobを渡す。発話なしが続いたら onNoSpeechEnd。AI応答中は pause() で監視
// を止め、AIの声を拾わないようにする。手動モードは forceEnd() で確定。
// ---------------------------------------------------------------------------
export function vadSupported() {
  return !!(navigator.mediaDevices && window.MediaRecorder &&
    (window.AudioContext || window.webkitAudioContext));
}

export async function createVADSession(opts = {}) {
  const baseSilenceMs = opts.baseSilenceMs || 2000;   // 無音しきい値(既定2s)
  const noSpeechEndMs = opts.noSpeechEndMs || 120000;  // 無音が続いたら自動終了(既定2分)
  // 無音・発話の有無に関わらず、つけっぱなしによる課金を防ぐための上限
  // (既定15分・2026-08-18)。0/未指定で上限なし。
  const maxSessionMs = opts.maxSessionMs || 0;
  const manual = !!opts.manual;                       // 手動発話終了モード
  if (!vadSupported()) throw new Error(tx("voice.handsfreeUnsupported"));
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const AC = window.AudioContext || window.webkitAudioContext;
  const ac = new AC();
  const source = ac.createMediaStreamSource(stream);
  const analyser = ac.createAnalyser();
  analyser.fftSize = 1024;
  source.connect(analyser);
  const buf = new Float32Array(analyser.fftSize);

  let running = false, paused = false, recording = false;
  let mr = null, chunks = [];
  let speechStart = 0, lastVoice = 0, lastUtterDur = 0;
  let noSpeechStart = 0, timer = null, ambient = 0.008;
  let sessionStart = 0;

  const rms = () => {
    analyser.getFloatTimeDomainData(buf);
    let s = 0;
    for (let i = 0; i < buf.length; i++) s += buf[i] * buf[i];
    return Math.sqrt(s / buf.length);
  };
  const startRec = () => {
    chunks = [];
    try { mr = new MediaRecorder(stream); } catch (e) { return; }
    mr.ondataavailable = (e) => { if (e.data && e.data.size) chunks.push(e.data); };
    mr.start(); recording = true;
  };
  const emitUtterance = () => {
    if (!recording || !mr) return;
    recording = false;
    const dur = lastUtterDur;
    mr.onstop = () => {
      const blob = new Blob(chunks, { type: mr.mimeType || "audio/webm" });
      if (opts.onUtterance) opts.onUtterance(blob, dur);
    };
    try { mr.stop(); } catch (e) { /* ignore */ }
  };
  const tick = () => {
    if (!running) return;
    const now = performance.now();
    // 無音・発話(AI応答中含む)の別なく、つけっぱなしによる課金を防ぐ上限。
    if (maxSessionMs && now - sessionStart >= maxSessionMs) {
      if (opts.onMaxDuration) opts.onMaxDuration();
      stop();
      return;
    }
    if (paused) return;
    const level = rms();
    const speaking = level > Math.max(0.013, ambient * 2.5 + 0.012);
    if (speaking) {
      lastVoice = now; noSpeechStart = 0;
      if (!recording) {
        speechStart = now; startRec();
        if (opts.onSpeechStart) opts.onSpeechStart();
      }
    } else if (recording) {
      lastUtterDur = lastVoice - speechStart;
      // 直前の発話が短いほど無音判定を少し長めに（早すぎる確定を防ぐ）。
      const eff = manual ? Infinity
        : baseSilenceMs + (lastUtterDur < 1200 ? 500 : 0);
      if (now - lastVoice >= eff) { emitUtterance(); noSpeechStart = now; }
    } else {
      if (!noSpeechStart) noSpeechStart = now;
      if (now - noSpeechStart >= noSpeechEndMs) {
        if (opts.onNoSpeechEnd) opts.onNoSpeechEnd();
        stop();
      }
    }
  };
  const calibrate = () => new Promise((res) => {
    let n = 0, sum = 0;
    const id = setInterval(() => {
      sum += rms(); n++;
      if (n >= 8) { clearInterval(id); ambient = sum / n; res(); }
    }, 50);
  });
  const start = async () => {
    if (ac.state === "suspended") { try { await ac.resume(); } catch (e) {} }
    await calibrate();
    running = true; noSpeechStart = performance.now();
    sessionStart = performance.now();
    timer = setInterval(tick, 60);
  };
  const stop = () => {
    running = false;
    if (timer) { clearInterval(timer); timer = null; }
    if (recording && mr) { try { mr.stop(); } catch (e) {} recording = false; }
    try { source.disconnect(); } catch (e) {}
    try { stream.getTracks().forEach((t) => t.stop()); } catch (e) {}
    try { ac.close(); } catch (e) {}
  };
  return {
    start, stop,
    pause() { paused = true; },
    resume() { paused = false; noSpeechStart = performance.now(); },
    forceEnd() { emitUtterance(); noSpeechStart = performance.now(); },
    isRunning() { return running; },
  };
}

// Toggle-style recorder: start() begins continuous recording, stop() ends it
// and resolves with the recognized text. Robust against onend not firing.
export function createRecorder(lang = "en-US") {
  if (!SR) throw new Error(tx("voice.recognitionUnsupported"));
  abortListening(); // release any previous session first
  const rec = new SR();
  activeRec = rec;
  rec.lang = lang;
  rec.continuous = true;
  rec.interimResults = true;
  let finalText = "";
  rec.onresult = (e) => {
    let t = "";
    for (let i = 0; i < e.results.length; i++) {
      if (e.results[i].isFinal) t += e.results[i][0].transcript + " ";
    }
    if (t.trim()) finalText = t.trim();
  };
  return {
    start() { try { rec.start(); } catch (e) { /* already started */ } },
    stop() {
      return new Promise((resolve) => {
        let settled = false;
        const done = () => {
          if (settled) return; settled = true;
          if (activeRec === rec) activeRec = null;
          clearTimeout(tid);
          resolve(finalText.trim());
        };
        rec.onend = done;
        rec.onerror = done;
        // If onend never fires, force-abort after 2.5s so the UI never
        // gets stuck on "認識中…".
        const tid = setTimeout(() => {
          try { rec.abort(); } catch (e) { /* ignore */ }
          done();
        }, 2500);
        try { rec.stop(); } catch (e) {
          try { rec.abort(); } catch (e2) { /* ignore */ }
          done();
        }
      });
    },
  };
}
