const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const AI_URL =
  import.meta.env.VITE_AI_URL || "http://127.0.0.1:8001/api/ai";

const brandingBase = (ideaId) => `${API_URL}/branding/ideas/${ideaId}`;

/**
 * GET parallèle des 4 résultats + brand-kit (404 → null).
 * @returns {Promise<{ naming: object|null, slogan: object|null, palette: object|null, logo: object|null, brandKit: object|null }>}
 */
export async function fetchBrandingBundle(ideaId, token) {
  if (!ideaId || !token) {
    return {
      naming: null,
      slogan: null,
      palette: null,
      logo: null,
      brandKit: null,
    };
  }
  const headers = { Authorization: `Bearer ${token}` };
  const getJson = async (path) => {
    const res = await fetch(`${brandingBase(ideaId)}/${path}`, { headers });
    if (res.status === 404) return null;
    if (!res.ok) {
      console.warn(`[branding] GET ${path}`, res.status);
      return null;
    }
    return res.json();
  };
  const [naming, slogan, palette, logo, brandKit] = await Promise.all([
    getJson("naming"),
    getJson("slogan"),
    getJson("palette"),
    getJson("logo"),
    getJson("brand-kit"),
  ]);
  return { naming, slogan, palette, logo, brandKit };
}

/**
 * Fusionne les `generated` comme le front legacy attendait `result_json`.
 */
export function mergeGeneratedFromBundle(bundle) {
  if (!bundle) return {};
  const parts = [bundle.naming, bundle.slogan, bundle.palette, bundle.logo].map(
    (x) =>
      x && x.generated && typeof x.generated === "object" ? x.generated : {},
  );
  return Object.assign({}, ...parts);
}

/**
 * Objet compatible avec l’ancien usage `record` + `result_json` dans BrandPage.
 */
export function buildLegacyRecordFromBundle(ideaId, bundle) {
  if (!bundle) return null;
  const merged = mergeGeneratedFromBundle(bundle);
  const status =
    bundle.naming?.status ||
    bundle.slogan?.status ||
    bundle.palette?.status ||
    "draft";
  return {
    idea_id: ideaId,
    status,
    result_json: merged,
  };
}

async function patchJson(ideaId, token, path, body) {
  const res = await fetch(`${brandingBase(ideaId)}/${path}`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    const d = err?.detail;
    const msg =
      typeof d === "string"
        ? d
        : Array.isArray(d)
          ? d.map((x) => x?.msg || JSON.stringify(x)).join("; ")
        : `Erreur ${res.status}`;
    throw new Error(msg);
  }
  return res.json();
}

export function patchNamingResult(ideaId, token, body) {
  return patchJson(ideaId, token, "naming", body);
}

export function patchSloganResult(ideaId, token, body) {
  return patchJson(ideaId, token, "slogan", body);
}

export function patchPaletteResult(ideaId, token, body) {
  return patchJson(ideaId, token, "palette", body);
}

export function patchLogoResult(ideaId, token, body) {
  return patchJson(ideaId, token, "logo", body);
}

export function patchBrandKit(ideaId, token, body) {
  return patchJson(ideaId, token, "brand-kit", body);
}

/**
 * Lance la génération de noms (backend-ai) avec préférences one-shot + JWT.
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
