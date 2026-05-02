/**
 * REST + SSE client — Website Builder.
 *
 * Phase 1   GET  /website/context?idea_id=...
 * Phase 2   POST /website/description/stream       (SSE)
 * Phase 2.5 POST /website/description/refine/stream (SSE)
 *           POST /website/description/approve
 * Phase 3   POST /website/generate/stream          (SSE)
 * Phase 4   POST /website/revise                   (REST — chat + édition manuelle)
 *           POST /website/revise/stream             (SSE — chat avec steps live)
 * Phase 5   POST /website/deploy
 *           POST /website/deploy/delete
 */

import {
  WEBSITE_BUILDER_ENDPOINTS,
  WEBSITE_BUILDER_TIMEOUTS_MS,
} from "../config/websiteBuilder.config";

const AI_URL = WEBSITE_BUILDER_ENDPOINTS.aiBaseUrl;
const API_URL = WEBSITE_BUILDER_ENDPOINTS.apiBaseUrl;
const TIMEOUTS = WEBSITE_BUILDER_TIMEOUTS_MS;

async function fetchWithTimeout(url, options = {}, timeoutMs = TIMEOUTS.default) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, { ...options, signal: controller.signal });
    return res;
  } catch (err) {
    if (err?.name === "AbortError") {
      throw new Error(
        `Timeout réseau (${Math.round(timeoutMs / 1000)}s). Vérifie : ` +
          `1) backend-ai lancé sur le port de VITE_AI_URL ; ` +
          `2) VITE_AI_URL = base complète avec /api/ai ; ` +
          `3) backend-api (port 8000) pour cette idée.`
      );
    }
    throw err;
  } finally {
    clearTimeout(timeout);
  }
}

async function handleResponse(res) {
  let data = null;
  try {
    data = await res.json();
  } catch {
    if (res.ok) return null;
  }
  if (!res.ok) {
    const detail = data?.detail;
    throw new Error(typeof detail === "string" ? detail : `Erreur HTTP ${res.status}.`);
  }
  return data;
}

function authHeaders(token) {
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

// ── Phase 1 ──────────────────────────────────────────────────────────────────

export async function apiFetchWebsiteContext(token, ideaId) {
  const url = `${AI_URL}/website/context?idea_id=${encodeURIComponent(ideaId)}`;
  const res = await fetchWithTimeout(url, { headers: authHeaders(token) }, TIMEOUTS.context);
  return handleResponse(res);
}

export async function apiFetchWebsiteProject(token, ideaId) {
  const url = `${API_URL}/website/ideas/${encodeURIComponent(ideaId)}`;
  const res = await fetchWithTimeout(url, { headers: authHeaders(token) });
  return handleResponse(res);
}

// ── Phase 2 approval ─────────────────────────────────────────────────────────

export async function apiApproveWebsiteDescription(token, { ideaId }) {
  const res = await fetchWithTimeout(`${AI_URL}/website/description/approve`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ idea_id: ideaId }),
  }, TIMEOUTS.default);
  return handleResponse(res);
}

// ── Phase 4 — Révision REST (édition manuelle → revise + QA) ─────────────────

export async function apiReviseWebsite(token, { ideaId, currentHtml, instruction }) {
  const res = await fetchWithTimeout(`${AI_URL}/website/revise`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ idea_id: ideaId, current_html: currentHtml, instruction }),
  }, TIMEOUTS.revision);
  return handleResponse(res);
}

// ── Phase 5 ───────────────────────────────────────────────────────────────────

export async function apiDeployWebsite(token, { ideaId, html }) {
  const res = await fetchWithTimeout(`${AI_URL}/website/deploy`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ idea_id: ideaId, html }),
  }, TIMEOUTS.deploy);
  return handleResponse(res);
}

export async function apiDeleteWebsiteDeployment(token, { ideaId, deploymentId }) {
  const res = await fetchWithTimeout(`${AI_URL}/website/deploy/delete`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ idea_id: ideaId, deployment_id: deploymentId }),
  }, TIMEOUTS.default);
  return handleResponse(res);
}

// ── SSE helpers ───────────────────────────────────────────────────────────────

async function consumeSseStream(url, { token, body, onEvent, signal } = {}) {
  const res = await fetch(url, {
    method: "POST",
    headers: { ...authHeaders(token), Accept: "text/event-stream" },
    body: JSON.stringify(body || {}),
    signal,
  });

  if (!res.ok) {
    let detail = `Erreur HTTP ${res.status}.`;
    try {
      const data = await res.json();
      if (data?.detail && typeof data.detail === "string") detail = data.detail;
    } catch { /* ignore */ }
    throw new Error(detail);
  }
  if (!res.body) {
    throw new Error("Le navigateur ne supporte pas le streaming HTTP (ReadableStream).");
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let sepIdx;
      while ((sepIdx = buffer.indexOf("\n\n")) >= 0) {
        const rawEvent = buffer.slice(0, sepIdx);
        buffer = buffer.slice(sepIdx + 2);

        const dataLines = rawEvent
          .split(/\r?\n/)
          .filter((l) => l.startsWith("data:"))
          .map((l) => l.slice(5).trimStart());
        if (dataLines.length === 0) continue;

        try {
          const obj = JSON.parse(dataLines.join("\n"));
          onEvent?.(obj);
          if (obj?.type === "done") return;
          if (obj?.type === "error") throw new Error(obj.message || "Erreur SSE inconnue.");
        } catch (parseErr) {
          if (parseErr instanceof Error && parseErr.message?.startsWith("Erreur SSE")) throw parseErr;
        }
      }
    }
  } finally {
    try { reader.releaseLock(); } catch { /* ignore */ }
  }
}

// ── SSE endpoints ─────────────────────────────────────────────────────────────

export async function apiStreamWebsiteDescription(token, { ideaId, onEvent, signal } = {}) {
  return consumeSseStream(`${AI_URL}/website/description/stream`, {
    token, body: { idea_id: ideaId }, onEvent, signal,
  });
}

export async function apiStreamRefineWebsiteDescription(
  token, { ideaId, description, instruction, onEvent, signal } = {}
) {
  return consumeSseStream(`${AI_URL}/website/description/refine/stream`, {
    token, body: { idea_id: ideaId, description, instruction }, onEvent, signal,
  });
}

export async function apiStreamGenerateWebsite(
  token, { ideaId, description = null, onEvent, signal } = {}
) {
  return consumeSseStream(`${AI_URL}/website/generate/stream`, {
    token,
    body: { idea_id: ideaId, ...(description ? { description } : {}) },
    onEvent,
    signal,
  });
}

export async function apiStreamReviseWebsite(
  token, { ideaId, currentHtml, instruction, onEvent, signal } = {}
) {
  return consumeSseStream(`${AI_URL}/website/revise/stream`, {
    token,
    body: { idea_id: ideaId, current_html: currentHtml, instruction },
    onEvent,
    signal,
  });
}
