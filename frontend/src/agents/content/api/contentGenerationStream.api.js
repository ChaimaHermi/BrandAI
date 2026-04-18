/**
 * SSE streaming client for POST /content/generate/stream
 *
 * Exports an async generator that yields parsed SSE events:
 *   { event: string, data: object | string }
 *
 * The existing `postContentGeneration` in contentGeneration.api.js is untouched.
 */

const AI_URL = import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai";

/**
 * Parse a single SSE block (the text between two blank lines).
 *
 * @param {string} block
 * @returns {{ event: string, data: object | string } | null}
 */
function parseSSEBlock(block) {
  let eventName = "message";
  const dataLines = [];

  for (const line of block.split("\n")) {
    if (!line || line.startsWith(":")) continue;
    if (line.startsWith("event:")) {
      eventName = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5));
    }
  }

  if (!dataLines.length) return null;

  const raw = dataLines.join("\n");
  try {
    return { event: eventName, data: JSON.parse(raw) };
  } catch {
    return { event: eventName, data: raw };
  }
}

/**
 * Async generator — POST to the streaming endpoint and yield SSE events.
 *
 * @param {object} payload  — same shape as postContentGeneration payload
 * @param {string | null} token  — JWT access token
 * @yields {{ event: string, data: object | string }}
 * @throws {Error} on non-ok HTTP response or network failure
 */
export async function* streamContentGeneration(payload, token) {
  if (!payload?.idea_id) {
    throw new Error("idea_id requis");
  }

  const headers = { "Content-Type": "application/json" };
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const body = {
    ...payload,
    ...(token ? { access_token: token } : {}),
  };

  const res = await fetch(`${AI_URL}/content/generate/stream`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    let detail = `Génération SSE échouée (${res.status})`;
    try {
      const err = await res.json();
      if (typeof err?.detail === "string") detail = err.detail;
      else if (Array.isArray(err?.detail))
        detail = err.detail.map((x) => x?.msg || JSON.stringify(x)).join("; ");
      else if (typeof err?.message === "string") detail = err.message;
    } catch {
      // ignore JSON parse error — keep the status-based message
    }
    throw new Error(detail);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE blocks are separated by double newlines
      const parts = buffer.split(/\n\n/);
      // Keep the last (possibly incomplete) chunk in the buffer
      buffer = parts.pop() ?? "";

      for (const part of parts) {
        const trimmed = part.trim();
        if (!trimmed) continue;
        const parsed = parseSSEBlock(trimmed);
        if (parsed) yield parsed;
      }
    }

    // Flush any remaining data in the buffer
    if (buffer.trim()) {
      const parsed = parseSSEBlock(buffer.trim());
      if (parsed) yield parsed;
    }
  } finally {
    reader.releaseLock();
  }
}
