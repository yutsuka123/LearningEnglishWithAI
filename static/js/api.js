// Thin fetch wrapper around the backend API.

async function req(method, path, body) {
  const opts = { method, headers: {} };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const res = await fetch(path, opts);
  if (res.status === 204) return null;
  const text = await res.text();
  const data = text ? JSON.parse(text) : null;
  if (!res.ok) {
    const msg = (data && (data.detail || data.error)) || res.statusText;
    const text2 = typeof msg === "string" ? msg : JSON.stringify(msg);
    console.error(`API ${method} ${path} -> ${res.status}: ${text2}`);
    throw new Error(text2);
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
    if (!res.body) {
      onChunk(await res.text());
      return;
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      onChunk(decoder.decode(value, { stream: true }));
    }
  },
};
