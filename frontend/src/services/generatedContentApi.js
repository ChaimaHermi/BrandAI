/**
 * Historique des contenus générés (traçabilité) — backend-api FastAPI.
 */

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function handleResponse(res) {
  let data;
  try {
    data = await res.json();
  } catch {
    throw new Error("Réponse du serveur invalide.");
  }
  if (!res.ok) {
    const detail = data?.detail;
    const msg = Array.isArray(detail)
      ? detail.map((d) => d.msg || d.message || JSON.stringify(d)).join(". ")
      : typeof detail === "string"
        ? detail
        : "Une erreur est survenue.";
    throw new Error(msg);
  }
  return data;
}

/**
 * @param {number} ideaId
 * @param {{ platform: string, caption: string, image_url?: string|null, char_count?: number }} body
 */
export async function apiCreateGeneratedContent(ideaId, token, body) {
  const res = await fetch(`${API_URL}/ideas/${ideaId}/generated-contents`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}

export async function apiListGeneratedContents(ideaId, token) {
  const res = await fetch(`${API_URL}/ideas/${ideaId}/generated-contents`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}

export async function apiCountGeneratedContents(ideaId, token) {
  const res = await fetch(`${API_URL}/ideas/${ideaId}/generated-contents/count`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}

/**
 * @param {{ status?: string, publish_error?: string|null }} body
 */
export async function apiPatchGeneratedContent(ideaId, contentId, token, body) {
  const res = await fetch(
    `${API_URL}/ideas/${ideaId}/generated-contents/${contentId}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    },
  );
  return handleResponse(res);
}
