const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

const AI_URL =
  import.meta.env.VITE_AI_URL || "http://127.0.0.1:8001/api/ai";

const brandingBase = (ideaId) => `${API_URL}/branding/ideas/${ideaId}`;
const ideasBase = (ideaId) => `${API_URL}/ideas/${ideaId}`;

/**
 * GET agrégé `/bundle` (une requête 200, champs absents → null).
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
  const res = await fetch(`${brandingBase(ideaId)}/bundle`, { headers });
  if (!res.ok) {
    console.warn("[branding] GET bundle", res.status);
    return {
      naming: null,
      slogan: null,
      palette: null,
      logo: null,
      brandKit: null,
    };
  }
  const data = await res.json();
  return {
    naming: data.naming ?? null,
    slogan: data.slogan ?? null,
    palette: data.palette ?? null,
    logo: data.logo ?? null,
    brandKit: data.brand_kit ?? null,
  };
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
 * Indique si un kit d’identité a déjà été enregistré (aperçu final sauvegardé).
 * Utilisé pour ouvrir directement l’étape « Aperçu » au retour sur Brand Identity.
 */
export function hasSavedBrandIdentityPreview(bundle) {
  if (!bundle) return false;
  if (bundle.brandKit?.id) return true;
  const v = (row) => row?.status === "validated";
  if (
    v(bundle.naming) &&
    v(bundle.slogan) &&
    v(bundle.palette) &&
    v(bundle.logo)
  ) {
    return true;
  }
  const merged = mergeGeneratedFromBundle(bundle);
  const hasLogo =
    Array.isArray(merged.logo_concepts) && merged.logo_concepts.length > 0;
  return !!(hasLogo && bundle.naming?.chosen_name);
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

export async function patchIdeaPipelineProgress(ideaId, token, body) {
  const res = await fetch(`${ideasBase(ideaId)}/pipeline-progress`, {
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
 * Génération de palettes (backend-ai) : idée clarifiée + nom de marque uniquement (3 options alignées sur le projet).
 */
export async function generatePalettes(ideaId, token, { brand_name }) {
  if (!ideaId || !token || !brand_name) {
    throw new Error("ideaId, token et brand_name requis");
  }
  const res = await fetch(`${AI_URL}/palette/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      idea_id: ideaId,
      brand_name,
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

/**
 * Génération logo avec streaming SSE — émet les étapes en temps réel.
 * @param {number} ideaId
 * @param {string} token
 * @param {object} params
 * @param {{ onStep, onResult, onError, onDone }} callbacks
 */
export async function generateLogoStream(
  ideaId,
  token,
  {
    brand_name = null,
    slogan_hint = null,
    palette_color_hint = null,
    previous_image_prompt = null,
    user_remarks = null,
    persist = true,
    persist_image_base64 = false,
  } = {},
  { onStep, onResult, onError, onDone } = {},
) {
  if (!ideaId || !token) throw new Error("ideaId et token requis");

  const res = await fetch(`${AI_URL}/logo/generate/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "text/event-stream" },
    body: JSON.stringify({
      idea_id: ideaId,
      brand_name,
      slogan_hint,
      palette_color_hint,
      previous_image_prompt: previous_image_prompt || null,
      user_remarks: user_remarks || null,
      access_token: token,
      persist,
      persist_image_base64,
    }),
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data?.detail || `Erreur HTTP ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      let sepIdx;
      while ((sepIdx = buffer.indexOf("\n\n")) >= 0) {
        const raw = buffer.slice(0, sepIdx);
        buffer = buffer.slice(sepIdx + 2);
        const dataLine = raw.split(/\r?\n/).find((l) => l.startsWith("data:"));
        if (!dataLine) continue;
        try {
          const evt = JSON.parse(dataLine.slice(5).trimStart());
          if (evt.type === "step") onStep?.(evt);
          else if (evt.type === "result") onResult?.(evt.payload);
          else if (evt.type === "error") onError?.(new Error(evt.message || "Erreur SSE"));
          else if (evt.type === "done") { onDone?.(); return; }
        } catch { /* ignore lignes non-JSON */ }
      }
    }
  } finally {
    try { reader.releaseLock(); } catch { /* ignore */ }
  }
  onDone?.();
}

/**
 * Génération logo (backend-ai) : contexte idée + nom / slogan / palette → prompt LLM + image HF (Qwen).
 * Timeout client : VITE_LOGO_GENERATE_TIMEOUT_MS (défaut 11 min).
 */
export async function generateLogo(
  ideaId,
  token,
  {
    brand_name = null,
    slogan_hint = null,
    palette_color_hint = null,
    previous_image_prompt = null,
    user_remarks = null,
    persist = true,
    persist_image_base64 = false,
  } = {},
) {
  if (!ideaId || !token) {
    throw new Error("ideaId et token requis");
  }
  const timeoutMs = Number(import.meta.env.VITE_LOGO_GENERATE_TIMEOUT_MS) || 660000;
  const controller = new AbortController();
  const tid = setTimeout(() => controller.abort(), timeoutMs);
  let res;
  try {
    res = await fetch(`${AI_URL}/logo/generate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      signal: controller.signal,
      body: JSON.stringify({
        idea_id: ideaId,
        brand_name,
        slogan_hint,
        palette_color_hint,
        previous_image_prompt: previous_image_prompt || null,
        user_remarks: user_remarks || null,
        access_token: token,
        persist,
        persist_image_base64,
      }),
    });
  } catch (e) {
    if (e?.name === "AbortError") {
      throw new Error(
        `Délai dépassé (${Math.round(timeoutMs / 1000)} s). Vérifiez que backend-ai tourne et que la génération HF n’est pas bloquée.`,
      );
    }
    throw e;
  } finally {
    clearTimeout(tid);
  }
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
    if (!msg) msg = `Génération logo échouée (${res.status})`;
    throw new Error(msg);
  }
  return data;
}
