const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const AI_URL =
  import.meta.env.VITE_AI_URL || "http://127.0.0.1:8001/api/ai";

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

/**
 * Lance la génération de noms (backend-ai) avec préférences one-shot + JWT.
 * @param {number} ideaId
 * @param {string} token JWT (même que backend-api)
 * @param {{ style_ton: object, constraints: object, user_remarks?: string }} payload Corps snake_case aligné NameAgent
 */
export async function generateBrandNames(ideaId, token, payload) {
  if (!ideaId || !token) {
    throw new Error("ideaId et token requis");
  }
  const res = await fetch(`${AI_URL}/naming/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      idea_id: ideaId,
      style_ton: payload.style_ton,
      constraints: payload.constraints,
      user_remarks: (payload.user_remarks || "").trim(),
      access_token: token,
      persist: true,
    }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data?.detail;
    let msg =
      typeof d === "string"
        ? d
        : Array.isArray(d)
          ? d.map((x) => x?.msg || JSON.stringify(x)).join("; ")
          : typeof data?.message === "string"
            ? data.message
            : null;
    if (!msg) msg = `Génération échouée (${res.status})`;
    throw new Error(msg);
  }
  return data;
}

/**
 * Génération de slogans (backend-ai) : nom choisi + préférences + contexte idée.
 */
export async function generateSlogans(ideaId, token, { brand_name, preferences }) {
  if (!ideaId || !token || !brand_name) {
    throw new Error("ideaId, token et brand_name requis");
  }
  const res = await fetch(`${AI_URL}/slogan/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      idea_id: ideaId,
      brand_name,
      preferences,
      access_token: token,
      persist: true,
    }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data?.detail;
    let msg =
      typeof d === "string"
        ? d
        : Array.isArray(d)
          ? d.map((x) => x?.msg || JSON.stringify(x)).join("; ")
          : typeof data?.message === "string"
            ? data.message
            : null;
    if (!msg) msg = `Génération slogan échouée (${res.status})`;
    throw new Error(msg);
  }
  return data;
}

/**
 * Génération de palettes (backend-ai) : nom + idée clarifiée + préférences.
 * @param {number} ideaId
 * @param {string} token
 * @param {{ brand_name: string, preferences?: object, slogan_hint?: string }} body
 */
export async function generatePalettes(ideaId, token, { brand_name, preferences = {}, slogan_hint = "" }) {
  if (!ideaId || !token || !brand_name) {
    throw new Error("ideaId, token et brand_name requis");
  }
  const res = await fetch(`${AI_URL}/palette/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      idea_id: ideaId,
      brand_name,
      preferences,
      slogan_hint: (slogan_hint || "").trim(),
      access_token: token,
      persist: true,
    }),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    const d = data?.detail;
    let msg =
      typeof d === "string"
        ? d
        : Array.isArray(d)
          ? d.map((x) => x?.msg || JSON.stringify(x)).join("; ")
          : typeof data?.message === "string"
            ? data.message
            : null;
    if (!msg) msg = `Génération palettes échouée (${res.status})`;
    throw new Error(msg);
  }
  return data;
}
