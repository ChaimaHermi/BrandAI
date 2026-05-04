const AI_URL = import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai";
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

function authHeaders(token) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;
  return headers;
}

/**
 * Résumé des connexions Meta / LinkedIn pour l’idée (sans jetons).
 * @param {number} ideaId
 * @param {string|null} token
 */
export async function fetchOptimizerConnections(ideaId, token) {
  const res = await fetch(`${API_URL}/ideas/${ideaId}/optimizer/connections`, {
    method: "GET",
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail || `Erreur ${res.status}`);
  }
  return res.json();
}

/**
 * Lance extraction + normalisation (fichiers sous backend-ai/social_etl/load/output/idea_{id}/).
 * @param {number} ideaId
 * @param {string|null} token
 */
export async function runOptimizerSocialEtlSync(ideaId, token) {
  const res = await fetch(`${API_URL}/ideas/${ideaId}/optimizer/sync-social-etl`, {
    method: "POST",
    headers: authHeaders(token),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail || `Erreur ${res.status}`);
  }
  return res.json();
}

/**
 * Lance le pipeline en SSE : appelle ``onEvent`` pour chaque événement JSON (type, …).
 * @param {number} ideaId
 * @param {string|null} token
 * @param {{ onEvent?: (ev: object) => void, signal?: AbortSignal }} options
 */
export async function runOptimizerSocialEtlSyncStream(ideaId, token, options = {}) {
  const { onEvent, signal } = options;
  const res = await fetch(`${API_URL}/ideas/${ideaId}/optimizer/sync-social-etl/stream`, {
    method: "POST",
    headers: authHeaders(token),
    signal,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail || `Erreur ${res.status}`);
  }
  if (!res.body) {
    throw new Error("Réponse streaming vide");
  }
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  const parseBlock = (block) => {
    const dataLine = block
      .split("\n")
      .map((l) => l.trim())
      .find((l) => l.startsWith("data:"));
    if (!dataLine) return;
    const jsonStr = dataLine.replace(/^data:\s*/, "").trim();
    if (!jsonStr) return;
    let ev;
    try {
      ev = JSON.parse(jsonStr);
    } catch {
      return;
    }
    onEvent?.(ev);
  };

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() ?? "";
    for (const block of blocks) {
      parseBlock(block);
    }
  }
  buffer += decoder.decode();
  if (buffer.trim()) {
    for (const block of buffer.split("\n\n")) {
      if (block.trim()) parseBlock(block);
    }
  }
}

/**
 * Récupère les statistiques sociales pour une idée et une plateforme.
 * @param {number} ideaId
 * @param {string} platform
 * @param {string|null} token
 * @returns {Promise<import('../types/optimizer.types').PlatformStats>}
 */
export async function fetchOptimizerStats(ideaId, platform, token) {
  const res = await fetch(
    `${API_URL}/ideas/${ideaId}/optimizer/stats?platform=${encodeURIComponent(platform)}`,
    { method: "GET", headers: authHeaders(token) },
  );

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail || `Erreur ${res.status}`);
  }

  return res.json();
}

/**
 * Récupère la recommandation agent pour une plateforme.
 * @param {number} ideaId
 * @param {string} platform
 * @param {string|null} token
 * @returns {Promise<import('../types/optimizer.types').Recommendation>}
 */
export async function fetchRecommendation(ideaId, platform, token) {
  const res = await fetch(
    `${AI_URL}/optimizer/recommendation`,
    {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify({ idea_id: ideaId, platform }),
    },
  );

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail || `Erreur ${res.status}`);
  }

  return res.json();
}

/**
 * Régénère la recommandation agent pour une plateforme.
 * @param {number} ideaId
 * @param {string} platform
 * @param {string|null} token
 * @returns {Promise<import('../types/optimizer.types').Recommendation>}
 */
export async function regenerateRecommendation(ideaId, platform, token) {
  const res = await fetch(
    `${AI_URL}/optimizer/recommendation/regenerate`,
    {
      method: "POST",
      headers: authHeaders(token),
      body: JSON.stringify({ idea_id: ideaId, platform, force: true }),
    },
  );

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail || `Erreur ${res.status}`);
  }

  return res.json();
}
