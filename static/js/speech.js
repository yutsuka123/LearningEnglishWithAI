// Speech: text-to-speech (output) and speech recognition (input).
//
// Two TTS engines:
//  1) OpenAI natural voices (ChatGPT-quality) via /api/learn/tts — used when
//     AI is enabled and "自然な声" is ON. Voices are named & user-toggleable,
//     and one is chosen at random per learning round.
//  2) Browser SpeechSynthesis — free fallback when AI is off or TTS fails.

const synth = window.speechSynthesis;

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

export function setAiEnabled(v) { aiEnabled = !!v; }
export function setOpenAIVoices(list) {
  if (Array.isArray(list) && list.length) openaiVoices = list;
}
export function listOpenAIVoices() { return openaiVoices.slice(); }
export function onUsage(cb) { usageCb = cb; }

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
const VOICE_GENDER = {
  alloy: "中性", ash: "男声", ballad: "男声", coral: "女声", echo: "男声",
  fable: "男声", nova: "女声", onyx: "男声", sage: "女声", shimmer: "女声",
};
export function voiceGender(name) { return VOICE_GENDER[name] || ""; }

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
async function playBlob(blob, rate) {
  stopSpeaking();
  const a = audioElement();
  try { if (a._objUrl) URL.revokeObjectURL(a._objUrl); } catch (e) { /* ignore */ }
  a._objUrl = URL.createObjectURL(blob);
  a.onended = null; a.onerror = null;   // clear stale handlers (speakAndWait)
  a.src = a._objUrl;
  a.playbackRate = rate || playbackRate;
  await a.play();
}

// --- speaking ---------------------------------------------------------------

export function stopSpeaking() {
  if (synth) synth.cancel();
  if (audioEl) { try { audioEl.pause(); } catch (e) { /* ignore */ } }
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
export async function say(text, opts = {}) {
  if (!text) return;
  if (!(isNatural() && aiEnabled)) { browserSpeak(text, opts); return; }
  // Ensure we have an OpenAI voice selected for this round.
  if (!currentIsOpenAI || !currentVoiceName) pickRoundVoice();
  try {
    const res = await fetch("/api/learn/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice: currentVoiceName }),
    });
    if (!res.ok) throw new Error("tts failed");
    const blob = await res.blob();
    await playBlob(blob, opts.rate);
    if (usageCb) usageCb();
  } catch (e) {
    browserSpeak(text, opts); // graceful fallback
  }
}

// Speak text with a SPECIFIC OpenAI voice (used by the 男声/女声 play buttons
// in the word & phrase lists). Falls back to the browser voice when natural
// TTS is off or the call fails. Mirrors say()/previewOpenAIVoice().
export async function sayWithVoice(text, voice, opts = {}) {
  if (!text) return;
  if (!(isNatural() && aiEnabled)) { browserSpeak(text, opts); return; }
  try {
    const res = await fetch("/api/learn/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice }),
    });
    if (!res.ok) throw new Error("tts failed");
    const blob = await res.blob();
    await playBlob(blob, opts.rate);
    if (usageCb) usageCb();
  } catch (e) {
    browserSpeak(text, opts); // graceful fallback
  }
}

// Global playback speed (再生速度ボタン用)。音程は変えず速さだけ変える。
let playbackRate = parseFloat(localStorage.getItem("playbackRate") || "1") || 1;
export function getPlaybackRate() { return playbackRate; }
export function setPlaybackRate(r) {
  playbackRate = r;
  localStorage.setItem("playbackRate", String(r));
  if (audioEl) audioEl.playbackRate = r;
}

// Play by item 番号(ID): the server returns saved audio for free (no token)
// or synthesizes once and saves it, so 2回目以降は無料。Falls back to the
// browser voice when natural TTS is off / AI is unavailable / the call fails.
//   itemType: 'word' | 'phrase', kind: 'word' | 'example' | 'phrase'
//   speed: 'learn'(学習・ゆっくり明瞭) | 'native'(自然な速さ) — 別音声を取得
export async function sayItem(
  itemType, id, kind, voice, fallbackText, opts = {}
) {
  if (!(isNatural() && aiEnabled)) {
    if (fallbackText) browserSpeak(fallbackText, opts);
    return;
  }
  const q = new URLSearchParams({
    item_type: itemType, item_id: id, kind, voice,
    speed: opts.speed || "learn",
  });
  try {
    const res = await fetch("/api/learn/tts/item?" + q.toString());
    if (!res.ok) throw new Error("tts item failed");
    const blob = await res.blob();
    await playBlob(blob, opts.rate);
    if (usageCb) usageCb();
  } catch (e) {
    if (fallbackText) browserSpeak(fallbackText, opts);
  }
}

// Speak with a specific OpenAI voice (for the settings preview button).
// Returns { ok, error } so the UI can show the real reason on failure.
export async function previewOpenAIVoice(voice, text) {
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
    await playBlob(blob, 1);
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

export function listenOnce(lang = "en-US") {
  return new Promise((resolve, reject) => {
    if (!SR) { reject(new Error("音声認識に未対応のブラウザです")); return; }
    abortListening();
    const rec = new SR();
    activeRec = rec;
    rec.lang = lang;
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    let done = false;
    const finish = (fn) => {
      if (done) return; done = true;
      if (activeRec === rec) activeRec = null;
      clearTimeout(tid);
      fn();
    };
    rec.onresult = (e) =>
      finish(() => resolve(e.results[0][0].transcript));
    rec.onerror = (e) =>
      finish(() => reject(new Error(e.error || "認識エラー")));
    rec.onend = () =>
      finish(() => reject(new Error("聞き取れませんでした")));
    // Safety: never hang forever.
    const tid = setTimeout(() => {
      try { rec.abort(); } catch (e) { /* ignore */ }
      finish(() => reject(new Error("タイムアウトしました")));
    }, 15000);
    rec.start();
  });
}

// AI recorder: records mic audio and transcribes via the backend (Whisper),
// which AUTO-DETECTS the language and handles non-native English far better
// than the browser recognizer. Same {start, stop()->text} shape.
export function aiSttSupported() {
  return !!(navigator.mediaDevices && window.MediaRecorder);
}

export async function createAIRecorder(language = "") {
  if (!aiSttSupported()) throw new Error("録音に未対応のブラウザです");
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
export function speakAndWait(text, opts = {}) {
  return new Promise((resolve) => {
    if (!text || !text.trim()) { resolve(); return; }
    const browser = () => {
      if (!synth) { resolve(); return; }
      synth.cancel();
      const u = new SpeechSynthesisUtterance(text);
      u.lang = "en-US"; u.rate = opts.rate || playbackRate || 0.95;
      u.onend = () => resolve(); u.onerror = () => resolve();
      synth.speak(u);
    };
    if (!(isNatural() && aiEnabled)) { browser(); return; }
    if (!currentIsOpenAI || !currentVoiceName) pickRoundVoice();
    fetch("/api/learn/tts", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice: currentVoiceName }),
    }).then((r) => r.ok ? r.blob() : Promise.reject(new Error("tts")))
      .then((blob) => {
        stopSpeaking();
        const a = audioElement();
        try { if (a._objUrl) URL.revokeObjectURL(a._objUrl); } catch (e) {}
        a._objUrl = URL.createObjectURL(blob);
        a.src = a._objUrl;
        a.playbackRate = opts.rate || playbackRate;
        a.onended = () => resolve();
        a.onerror = () => resolve();
        a.play();
        if (usageCb) usageCb();
      }).catch(() => browser());
  });
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
  const noSpeechEndMs = opts.noSpeechEndMs || 20000;  // 20s無音で自動終了
  const manual = !!opts.manual;                       // 手動発話終了モード
  if (!vadSupported()) throw new Error("ハンズフリーに未対応のブラウザです");
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
    if (!running || paused) return;
    const now = performance.now();
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
  if (!SR) throw new Error("音声認識に未対応のブラウザです");
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
