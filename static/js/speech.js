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
let audioEl = null;            // currently playing <audio>
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

// --- speaking ---------------------------------------------------------------

export function stopSpeaking() {
  if (synth) synth.cancel();
  if (audioEl) { audioEl.pause(); audioEl = null; }
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
  u.rate = opts.rate || 0.95;
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
    stopSpeaking();
    audioEl = new Audio(URL.createObjectURL(blob));
    audioEl.playbackRate = opts.rate || 1;
    await audioEl.play();
    if (usageCb) usageCb();
  } catch (e) {
    browserSpeak(text, opts); // graceful fallback
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
    stopSpeaking();
    audioEl = new Audio(URL.createObjectURL(blob));
    await audioEl.play();
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

export function sttSupported() { return !!SR; }

export function listenOnce(lang = "en-US") {
  return new Promise((resolve, reject) => {
    if (!SR) { reject(new Error("音声認識に未対応のブラウザです")); return; }
    const rec = new SR();
    rec.lang = lang;
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    let done = false;
    rec.onresult = (e) => { done = true; resolve(e.results[0][0].transcript); };
    rec.onerror = (e) => reject(new Error(e.error || "認識エラー"));
    rec.onend = () => { if (!done) reject(new Error("聞き取れませんでした")); };
    rec.start();
  });
}
