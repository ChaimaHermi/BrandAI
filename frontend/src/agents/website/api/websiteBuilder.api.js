/**
 * REST client pour les 5 phases du Website Builder.
 *  Phase 1 — GET  /website/context?idea_id=...   → BrandContext + résumé Markdown
 *  Phase 2 — POST /website/description           → concept créatif (JSON)
 *  Phase 3 — POST /website/generate              → HTML complet
 *  Phase 4 — POST /website/revise                → HTML révisé
 *  Phase 5 — POST /website/deploy                → URL Vercel publique
 */

const AI_URL = import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai";

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
  const res = await fetch(url, { headers: authHeaders(token) });
  return handleResponse(res);
}

export async function apiGenerateWebsiteDescription(token, { ideaId }) {
  const res = await fetch(`${AI_URL}/website/description`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ idea_id: ideaId }),
  });
  return handleResponse(res);
}

export async function apiGenerateWebsite(token, { ideaId, description = null }) {
  const res = await fetch(`${AI_URL}/website/generate`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({
      idea_id: ideaId,
      ...(description ? { description } : {}),
    }),
  });
  return handleResponse(res);
}

export async function apiReviseWebsite(token, { ideaId, currentHtml, instruction }) {
  const res = await fetch(`${AI_URL}/website/revise`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({
      idea_id: ideaId,
      current_html: currentHtml,
      instruction,
    }),
  });
  return handleResponse(res);
}

export async function apiDeployWebsite(token, { ideaId, html }) {
  const res = await fetch(`${AI_URL}/website/deploy`, {
    method: "POST",
    headers: authHeaders(token),
    body: JSON.stringify({ idea_id: ideaId, html }),
  });
  return handleResponse(res);
}
