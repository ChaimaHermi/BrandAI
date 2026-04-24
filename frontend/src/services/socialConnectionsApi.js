/**
 * Connexions sociales persistées (backend-api) — jetons chiffrés au repos côté serveur.
 */

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function handleResponse(res) {
  if (res.status === 204) return null;
  let data;
  try {
    data = await res.json();
  } catch {
    data = {};
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
 * @param {string} token
 * @returns {Promise<{ meta?: object, linkedin?: object }>}
 */
export async function fetchSocialConnections(token) {
  const res = await fetch(`${API_URL}/me/social-connections`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}

/**
 * @param {string} token
 * @param {{ user_access_token: string, pages: Array<{ id: string|number, name?: string, access_token: string }>, selected_page_id?: string|null }} body
 */
export async function putMetaSocialConnection(token, body) {
  const res = await fetch(`${API_URL}/me/social-connections/meta`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}

/**
 * @param {string} token
 * @param {string} selectedPageId
 */
export async function patchMetaSelectedPage(token, selectedPageId) {
  const res = await fetch(`${API_URL}/me/social-connections/meta`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ selected_page_id: selectedPageId }),
  });
  return handleResponse(res);
}

/**
 * @param {string} token
 * @param {{ access_token: string, person_urn: string, name?: string|null }} body
 */
export async function putLinkedInSocialConnection(token, body) {
  const res = await fetch(`${API_URL}/me/social-connections/linkedin`, {
    method: "PUT",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  return handleResponse(res);
}

export async function deleteMetaSocialConnection(token) {
  const res = await fetch(`${API_URL}/me/social-connections/meta`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}

export async function deleteLinkedInSocialConnection(token) {
  const res = await fetch(`${API_URL}/me/social-connections/linkedin`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}
