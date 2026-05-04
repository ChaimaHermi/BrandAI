const AI_URL = import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai";
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

/**
 * Récupère les statistiques sociales pour une idée et une plateforme.
 * @param {number} ideaId
 * @param {string} platform
 * @param {string|null} token
 * @returns {Promise<import('../types/optimizer.types').PlatformStats>}
 */
export async function fetchOptimizerStats(ideaId, platform, token) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(
    `${API_URL}/ideas/${ideaId}/optimizer/stats?platform=${platform}`,
    { method: "GET", headers },
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
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(
    `${AI_URL}/optimizer/recommendation`,
    {
      method: "POST",
      headers,
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
  const headers = { "Content-Type": "application/json" };
  if (token) headers.Authorization = `Bearer ${token}`;

  const res = await fetch(
    `${AI_URL}/optimizer/recommendation/regenerate`,
    {
      method: "POST",
      headers,
      body: JSON.stringify({ idea_id: ideaId, platform, force: true }),
    },
  );

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail || `Erreur ${res.status}`);
  }

  return res.json();
}
