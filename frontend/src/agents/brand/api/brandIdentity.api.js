const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

/**
 * @param {number} ideaId
 * @param {string} token
 * @returns {Promise<object|null>} BrandIdentityOut ou null si 404
 */
export async function getLatestBrandIdentity(ideaId, token) {
  if (!ideaId || !token) return null;
  const res = await fetch(`${API_URL}/brand-identity/${ideaId}/latest`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (res.status === 404) return null;
  if (!res.ok) {
    console.error("[brand-identity] latest failed", res.status);
    return null;
  }
  return res.json();
}
