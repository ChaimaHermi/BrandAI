/**
 * Connexions sociales persistées (backend-api) — par idée de projet, jetons chiffrés au repos.
 */

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

function socialConnectionsBase(ideaId) {
  if (ideaId == null || ideaId === "") {
    throw new Error("ideaId est requis pour les connexions sociales.");
  }
  return `${API_URL}/ideas/${ideaId}/social-connections`;
}

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
    let msg = "Une erreur est survenue.";
    if (Array.isArray(detail)) {
      msg = detail
        .map((d) =>
          typeof d === "string"
            ? d
            : [d?.loc?.filter(Boolean).join("."), d?.msg || d?.message]
                .filter(Boolean)
                .join(" : "),
        )
        .join(" · ");
    } else if (typeof detail === "string") {
      msg = detail;
    } else if (detail && typeof detail === "object") {
      msg = detail.message || detail.msg || JSON.stringify(detail);
    }
    throw new Error(msg || `Erreur HTTP ${res.status}`);
  }
  return data;
}

/**
 * @param {string} token
 * @param {number|string} ideaId
 * @returns {Promise<{ meta?: object, linkedin?: object }>}
 */
export async function fetchSocialConnections(token, ideaId) {
  const res = await fetch(`${socialConnectionsBase(ideaId)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}

/**
 * @param {string} token
 * @param {number|string} ideaId
 * @param {{ user_access_token: string, pages: Array<{ id: string|number, name?: string, access_token: string }>, selected_page_id?: string|null }} body
 */
export async function putMetaSocialConnection(token, ideaId, body) {
  const res = await fetch(`${socialConnectionsBase(ideaId)}/meta`, {
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
 * @param {number|string} ideaId
 * @param {string} selectedPageId
 */
export async function patchMetaSelectedPage(token, ideaId, selectedPageId) {
  const res = await fetch(`${socialConnectionsBase(ideaId)}/meta`, {
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
 * @param {number|string} ideaId
 * @param {{ access_token: string, person_urn: string, name?: string|null }} body
 */
export async function putLinkedInSocialConnection(token, ideaId, body) {
  const res = await fetch(`${socialConnectionsBase(ideaId)}/linkedin`, {
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
 * @param {number|string} ideaId
 * @param {string|null|undefined} linkedinUrl — chaîne vide ou null pour effacer
 */
export async function patchLinkedInUrl(token, ideaId, profileUrl) {
  const profile_url =
    profileUrl == null || profileUrl === ""
      ? null
      : String(profileUrl).trim() || null;
  const res = await fetch(`${socialConnectionsBase(ideaId)}/linkedin/url`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ profile_url }),
  });
  return handleResponse(res);
}

export async function deleteMetaSocialConnection(token, ideaId) {
  const res = await fetch(`${socialConnectionsBase(ideaId)}/meta`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}

export async function deleteLinkedInSocialConnection(token, ideaId) {
  const res = await fetch(`${socialConnectionsBase(ideaId)}/linkedin`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}
