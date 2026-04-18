/**
 * OAuth + publication Meta / LinkedIn — backend-ai (port 8001).
 */

const AI_URL =
  import.meta.env.VITE_AI_URL || "http://localhost:8001/api/ai";

const AI_ORIGIN = (() => {
  try {
    return new URL(AI_URL.replace(/\/api\/ai\/?$/, "") || AI_URL).origin;
  } catch {
    return "http://localhost:8001";
  }
})();

export { AI_ORIGIN };

export async function fetchMetaOAuthUrl() {
  const res = await fetch(`${AI_URL}/social/meta/oauth-url`);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : "OAuth Meta indisponible");
  }
  return data;
}

export async function fetchLinkedInOAuthUrl() {
  const res = await fetch(`${AI_URL}/social/linkedin/oauth-url`);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(typeof data?.detail === "string" ? data.detail : "OAuth LinkedIn indisponible");
  }
  return data;
}

/**
 * @param {object} body
 * @param {{ message: string, page_id?: string, page_access_token?: string, link?: string }} body
 */
export async function postPublishFacebook(body) {
  const res = await fetch(`${AI_URL}/social/publish/facebook`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data?.detail;
    throw new Error(typeof d === "string" ? d : `Facebook ${res.status}`);
  }
  return data;
}

/**
 * @param {{ caption: string, image_url: string, page_id: string, page_access_token: string }} body
 */
export async function postPublishInstagram(body) {
  const res = await fetch(`${AI_URL}/social/publish/instagram`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data?.detail;
    throw new Error(typeof d === "string" ? d : `Instagram ${res.status}`);
  }
  return data;
}

/**
 * @param {{ message: string, access_token?: string, person_urn?: string, image_url?: string }} body
 */
export async function postPublishLinkedIn(body) {
  const res = await fetch(`${AI_URL}/social/publish/linkedin`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data?.detail;
    throw new Error(typeof d === "string" ? d : `LinkedIn ${res.status}`);
  }
  return data;
}
