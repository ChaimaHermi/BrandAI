/**
 * Publications planifiées — backend-api `/ideas/:id/scheduled-publications`
 */

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

async function handleResponse(res) {
  let data;
  try {
    data = await res.json();
  } catch {
    if (res.status === 204) return null;
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
 * @param {string} token
 * @param {{ generated_content_id: number, scheduled_at: string, timezone?: string, title?: string, notes?: string }} body
 */
export async function apiCreateScheduledPublication(ideaId, token, body) {
  const res = await fetch(`${API_URL}/ideas/${ideaId}/scheduled-publications`, {
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
 * @param {number} ideaId
 * @param {string} token
 * @param {{ date_from?: string, date_to?: string }} [range]
 */
/**
 * @param {number} ideaId
 * @param {number} scheduleId
 * @param {string} token
 */
export async function apiGetScheduledPublication(ideaId, scheduleId, token) {
  const res = await fetch(
    `${API_URL}/ideas/${ideaId}/scheduled-publications/${scheduleId}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  return handleResponse(res);
}

export async function apiListScheduledPublications(ideaId, token, range = {}) {
  const params = new URLSearchParams();
  if (range.date_from) params.set("date_from", range.date_from);
  if (range.date_to) params.set("date_to", range.date_to);
  const q = params.toString();
  const url = `${API_URL}/ideas/${ideaId}/scheduled-publications${q ? `?${q}` : ""}`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
  });
  return handleResponse(res);
}

/**
 * @param {number} ideaId
 * @param {number} scheduleId
 * @param {string} token
 * @param {{ scheduled_at?: string, timezone?: string, title?: string, notes?: string, status?: string }} body
 */
export async function apiPatchScheduledPublication(ideaId, scheduleId, token, body) {
  const res = await fetch(
    `${API_URL}/ideas/${ideaId}/scheduled-publications/${scheduleId}`,
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

/**
 * @param {number} ideaId
 * @param {number} scheduleId
 * @param {string} token
 */
export async function apiDeleteScheduledPublication(ideaId, scheduleId, token) {
  const res = await fetch(
    `${API_URL}/ideas/${ideaId}/scheduled-publications/${scheduleId}`,
    {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    },
  );
  if (!res.ok) {
    let data;
    try {
      data = await res.json();
    } catch {
      throw new Error("Suppression impossible.");
    }
    const detail = data?.detail;
    throw new Error(typeof detail === "string" ? detail : "Suppression impossible.");
  }
}
