// frontend/src/services/ideaApi.js
// ─────────────────────────────────────────
// Appels HTTP vers /api/ideas/
// ─────────────────────────────────────────

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

/**
 * Message utilisateur à partir d'une erreur (réseau, API, etc.)
 */
export function getErrorMessage(err) {
  if (!err || !err.message) return "Une erreur inattendue s'est produite. Réessayez.";
  const m = String(err.message);
  if (m === "Failed to fetch" || m.includes("NetworkError") || m.toLowerCase().includes("network")) {
    return "Impossible de contacter le serveur. Vérifiez votre connexion internet et réessayez.";
  }
  if (m.toLowerCase().includes("introuvable") || m.includes("404")) {
    return "Cette idée est introuvable.";
  }
  return m;
}

async function handleResponse(res) {
  let data;
  try {
    data = await res.json();
  } catch {
    throw new Error("Réponse du serveur invalide. Réessayez plus tard.");
  }
  if (!res.ok) {
    const detail = data?.detail;
    const msg = Array.isArray(detail)
      ? detail.map((d) => d.msg || d.message || JSON.stringify(d)).join(". ")
      : typeof detail === "string"
        ? detail
        : "Une erreur est survenue. Réessayez.";
    throw new Error(msg);
  }
  return data;
}

/**
 * Soumettre une nouvelle idée
 * POST /api/ideas/
 * @returns {Promise<IdeaOut>}
 */
export async function apiCreateIdea({ name, sector, target_audience, description }, token) {
  const body = { name, sector, description };
  if (target_audience != null && String(target_audience).trim() !== "") {
    body.target_audience = String(target_audience).trim();
  }
  const res = await fetch(`${API_URL}/ideas/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}

/**
 * Récupérer toutes mes idées
 * GET /api/ideas/
 * @returns {Promise<{ ideas: IdeaOut[], total: number }>}
 */
export async function apiGetIdeas(token) {
  const res = await fetch(`${API_URL}/ideas/`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}

/**
 * Récupérer une idée par son ID
 * GET /api/ideas/{id}
 * @returns {Promise<IdeaOut>}
 */
export async function apiGetIdea(ideaId, token) {
  const res = await fetch(`${API_URL}/ideas/${ideaId}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}

/**
 * Supprimer une idée
 * DELETE /api/ideas/{id}
 * @returns {Promise<{ message: string }>}
 */
export async function apiDeleteIdea(ideaId, token) {
  const res = await fetch(`${API_URL}/ideas/${ideaId}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}
