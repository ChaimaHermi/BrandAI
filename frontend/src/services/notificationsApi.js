/**
 * Notifications REST API — backend-api `/notifications`
 */

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

function headers(token) {
  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

async function handle(res) {
  if (res.status === 204) return null;
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg =
      typeof data?.detail === "string" ? data.detail : "Erreur notifications";
    throw new Error(msg);
  }
  return data;
}

export async function apiListNotifications(token, { limit = 50, unreadOnly = false } = {}) {
  const params = new URLSearchParams();
  if (limit) params.set("limit", limit);
  if (unreadOnly) params.set("unread_only", "true");
  const q = params.toString();
  const res = await fetch(`${API_URL}/notifications${q ? `?${q}` : ""}`, {
    headers: headers(token),
  });
  return handle(res);
}

export async function apiMarkRead(token, notificationId) {
  const res = await fetch(`${API_URL}/notifications/${notificationId}/read`, {
    method: "PATCH",
    headers: headers(token),
  });
  return handle(res);
}

export async function apiMarkAllRead(token) {
  const res = await fetch(`${API_URL}/notifications/read-all`, {
    method: "PATCH",
    headers: headers(token),
  });
  return handle(res);
}

export function buildSSEUrl(token) {
  return `${API_URL}/notifications/stream?token=${encodeURIComponent(token)}`;
}
