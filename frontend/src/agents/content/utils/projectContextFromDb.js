/**
 * Dérive l’affichage du bandeau depuis les réponses GET (idée + bundle branding, backend-api).
 */
import { mergeGeneratedFromBundle } from "@/agents/brand/api/brandIdentity.api";

/**
 * @param {object | null} idea — GET /api/ideas/:id
 * @param {object | null} bundle — GET /api/branding/ideas/:id/bundle
 */
export function buildContentProjectDisplay(idea, bundle) {
  const merged = mergeGeneratedFromBundle(bundle || {});
  const ideaName = (idea?.name || "").trim();
  const chosen = (bundle?.naming?.chosen_name || "").trim();
  const brandName = chosen || ideaName || "Projet";
  return {
    brandName,
    ideaName,
    projectDescription: pickProjectDescription(idea),
    slogan: pickSlogan(bundle, merged),
    logoUrl: pickLogoDataUrl(merged),
    subtitle: pickSubtitle(idea),
  };
}

function pickProjectDescription(idea) {
  if (!idea) return "";
  const d = (idea.description || "").trim();
  if (d) return d;
  return (idea.clarity_short_pitch || idea.clarity_problem || "").trim();
}

function pickSlogan(bundle, merged) {
  const c = bundle?.slogan?.chosen_slogan;
  if (typeof c === "string" && c.trim()) return c.trim();
  const opts = merged?.slogan_options;
  if (Array.isArray(opts) && opts.length) {
    const first = opts[0];
    if (typeof first === "string") return first.trim();
    return (first?.text || "").trim();
  }
  return "";
}

function pickLogoDataUrl(merged) {
  const lc = merged?.logo_concepts;
  if (!Array.isArray(lc) || !lc.length) return null;
  const c0 = lc[0];
  if (c0?.image_base64 && c0?.image_mime) {
    return `data:${c0.image_mime};base64,${c0.image_base64}`;
  }
  return null;
}

function pickSubtitle(idea) {
  if (!idea) return "";
  const pitch = (idea.clarity_short_pitch || "").trim();
  if (pitch) return pitch;
  return (idea.clarity_sector || idea.sector || "").trim();
}
