import {
  WEBSITE_BUILDER_ENDPOINTS,
  WEBSITE_BUILDER_TIMEOUTS_MS,
} from "../config/websiteBuilder.config";

/**
 * Client HTTP du Website Builder (frontend).
 *
 * Flux réellement utilisés par l’UI :
 *  - GET  /website/context (backend-ai) — phase 1
 *  - GET  /website/ideas/:id (backend-api) — reprise de session
 *  - POST …/stream — description, refine, génération HTML, révision chat (SSE)
 *  - POST /website/description/approve, /save, /deploy, /deploy/delete (JSON court)
 */

const AI_URL = WEBSITE_BUILDER_ENDPOINTS.aiBaseUrl;
const API_URL = WEBSITE_BUILDER_ENDPOINTS.apiBaseUrl;
const TIMEOUTS = WEBSITE_BUILDER_TIMEOUTS_MS;

async function fetchWithTimeout(url, options = {}, timeoutMs = TIMEOUTS.default) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    return res;
  } catch (err) {
    if (err?.name === "AbortError") {
      throw new Error(
        `Timeout réseau (${Math.round(timeoutMs / 1000)}s). Vérifie : ` +
          `1) backend-ai lancé (ex. uvicorn sur le port de VITE_AI_URL) ; ` +
          `2) VITE_AI_URL = base complète avec /api/ai (ex. http://localhost:8001/api/ai) ; ` +
          `3) backend-api (port 8000) pour cette idée — le contexte site en dépend.`
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
    throw new Error(
      typeof detail === "string"
        ? detail
        : `Erreur HTTP ${res.status}.`
    );
  }
  return data;
}

function authHeaders(token) {
  return {
    "Content-Type": "application/json",
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
  };
}

export async function apiFetchWebsiteContext(token, ideaId) {
  const url = `${AI_URL}/website/context?idea_id=${encodeURIComponent(ideaId)}`;
  const res = await fetchWithTimeout(
    url,
    { headers: authHeaders(token) },
    TIMEOUTS.context
  );
  return handleResponse(res);
}

export async function apiFetchWebsiteProject(token, ideaId) {
  const url = `${API_URL}/website/ideas/${encodeURIComponent(ideaId)}`;
  const res = await fetchWithTimeout(url, { headers: authHeaders(token) });
  return handleResponse(res);
}

export async function apiApproveWebsiteDescription(token, { ideaId }) {
  const res = await fetchWithTimeout(`${AI_URL}/website/description/approve`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ idea_id: ideaId }),
  }, TIMEOUTS.default);
  return handleResponse(res);
}

export async function apiSaveWebsiteHtml(token, { ideaId, html }) {
  const res = await fetchWithTimeout(`${AI_URL}/website/save`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ idea_id: ideaId, html }),
  }, TIMEOUTS.save);
  return handleResponse(res);
}

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

// ── SSE helpers ─────────────────────────────────────────────────────────────

/**
 * Consomme un endpoint SSE POST et appelle `onEvent(eventObj)` à chaque
 * message JSON reçu. Renvoie une promesse qui se résout quand le flux est
 * fermé proprement (ou rejette en cas d'erreur réseau).
 *
 * Format attendu du serveur (par défaut FastAPI EventSource) :
 *     data: {"type": "step", ...}\n\n
 *
 * `body` est sérialisé en JSON et envoyé en POST.
 */
async function consumeSseStream(url, { token, body, onEvent, signal } = {}) {
  const res = await fetch(url, {
    method: "POST",
    headers: {
      ...authHeaders(token),
      Accept: "text/event-stream",
    },
    body: JSON.stringify(body || {}),
    signal,
  });

  if (!res.ok) {
    let detail = `Erreur HTTP ${res.status}.`;
    try {
      const data = await res.json();
      if (data?.detail && typeof data.detail === "string") detail = data.detail;
    } catch {
      // ignore
    }
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

      // Découpe par double newline (séparateur d'event SSE).
      let sepIdx;
      while ((sepIdx = buffer.indexOf("\n\n")) >= 0) {
        const rawEvent = buffer.slice(0, sepIdx);
        buffer = buffer.slice(sepIdx + 2);

        const lines = rawEvent.split(/\r?\n/);
        const dataLines = lines
          .filter((l) => l.startsWith("data:"))
          .map((l) => l.slice(5).trimStart());
        if (dataLines.length === 0) continue;

        const data = dataLines.join("\n");
        try {
          const obj = JSON.parse(data);
          onEvent?.(obj);
          if (obj?.type === "done") {
            return;
          }
          if (obj?.type === "error") {
            throw new Error(obj.message || "Erreur SSE inconnue.");
          }
        } catch (parseErr) {
          // Ignore les lignes non-JSON (heartbeats éventuels), mais relance
          // les erreurs explicites.
          if (parseErr instanceof Error && parseErr.message?.startsWith("Erreur SSE")) {
            throw parseErr;
          }
        }
      }
    }
  } finally {
    try {
      reader.releaseLock();
    } catch {
      // ignore
    }
  }
}

export async function apiStreamWebsiteDescription(token, { ideaId, onEvent, signal } = {}) {
  return consumeSseStream(`${AI_URL}/website/description/stream`, {
    token,
    body: { idea_id: ideaId },
    onEvent,
    signal,
  });
}

export async function apiStreamRefineWebsiteDescription(
  token,
  { ideaId, description, instruction, onEvent, signal } = {}
) {
  return consumeSseStream(`${AI_URL}/website/description/refine/stream`, {
    token,
    body: {
      idea_id: ideaId,
      description,
      instruction,
    },
    onEvent,
    signal,
  });
}

export async function apiStreamGenerateWebsite(
  token,
  { ideaId, description = null, onEvent, signal } = {}
) {
  return consumeSseStream(`${AI_URL}/website/generate/stream`, {
    token,
    body: {
      idea_id: ideaId,
      ...(description ? { description } : {}),
    },
    onEvent,
    signal,
  });
}

export async function apiStreamReviseWebsite(
  token,
  { ideaId, currentHtml, instruction, onEvent, signal } = {}
) {
  return consumeSseStream(`${AI_URL}/website/revise/stream`, {
    token,
    body: {
      idea_id: ideaId,
      current_html: currentHtml,
      instruction,
    },
    onEvent,
    signal,
  });
}
