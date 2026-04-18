import { useEffect, useState, useCallback } from "react";
import { FiImage, FiRefreshCw } from "react-icons/fi";
import { Loader } from "@/shared/ui/Loader";
import { fetchBrandingBundle } from "@/agents/brand/api/brandIdentity.api";
import { buildContentProjectDisplay } from "../utils/projectContextFromDb";

/**
 * Bandeau contexte projet — nom, description, logo et slogan depuis la base.
 * L'idée est passée depuis ContentPage (PipelineContext) — aucun fetch redondant.
 * Seul le bundle branding est chargé en interne (logo + slogan).
 */
export default function ContentProjectContextBanner({
  idea,
  token,
  alignWithProject = true,
  onAlignChange,
}) {
  const [bundle, setBundle]               = useState(null);
  const [bundleLoading, setBundleLoading] = useState(false);
  const [bundleError, setBundleError]     = useState(null);

  const loadBundle = useCallback(async () => {
    if (!idea?.id || !token) return;
    setBundleLoading(true);
    setBundleError(null);
    try {
      const b = await fetchBrandingBundle(idea.id, token);
      setBundle(b);
    } catch (e) {
      setBundleError(e?.message || "Impossible de charger le kit de marque.");
    } finally {
      setBundleLoading(false);
    }
  }, [idea?.id, token]);

  useEffect(() => {
    loadBundle();
  }, [loadBundle]);

  /* Pas de projet dans le pipeline */
  if (!idea?.id) return null;

  const display = buildContentProjectDisplay(idea, bundle);
  const { brandName, ideaName, projectDescription, slogan, logoUrl, subtitle } = display;
  const desc =
    projectDescription ||
    subtitle ||
    "Aucune description renseignée pour cette idée.";

  return (
    <div className="rounded-2xl border border-brand-border bg-white shadow-card">

      {/* ── Corps : logo + nom + description + slogan ─────────────────────── */}
      <div className="flex flex-col gap-4 px-5 pt-5 sm:flex-row sm:items-start">

        {/* Logo ou placeholder */}
        <div className="mx-auto w-20 shrink-0 sm:mx-0">
          {bundleLoading ? (
            <div className="flex h-20 w-20 items-center justify-center rounded-xl border border-brand-border bg-brand-light/20">
              <Loader className="h-5 w-5" />
            </div>
          ) : logoUrl ? (
            <div className="flex h-20 w-20 items-center justify-center rounded-xl border border-brand-border bg-white">
              <img
                src={logoUrl}
                alt="Logo"
                className="max-h-full max-w-full object-contain"
              />
            </div>
          ) : (
            <div className="flex h-20 w-20 items-center justify-center rounded-xl border border-dashed border-brand-border bg-brand-light/20 text-brand-muted">
              <FiImage size={28} aria-hidden />
            </div>
          )}
        </div>

        {/* Infos textuelles */}
        <div className="min-w-0 flex-1">
          {/* Badge + nom */}
          <div className="mb-1.5 flex flex-wrap items-center gap-2">
            <span className="rounded-full bg-brand-light px-2.5 py-0.5 text-2xs font-bold uppercase tracking-wider text-brand-darker">
              Projet enregistré
            </span>
            {bundleError && (
              <button
                type="button"
                onClick={loadBundle}
                className="inline-flex items-center gap-1 rounded-full border border-brand-border bg-white px-2 py-0.5 text-2xs font-semibold text-ink-muted transition-all hover:border-brand-muted hover:text-brand-dark"
              >
                <FiRefreshCw size={10} aria-hidden />
                Réessayer
              </button>
            )}
          </div>

          <h2 className="text-base font-bold text-ink">{brandName}</h2>
          {ideaName && ideaName !== brandName && (
            <p className="text-xs text-ink-subtle">Idée : {ideaName}</p>
          )}
          <p className="mt-1.5 whitespace-pre-wrap text-sm leading-relaxed text-ink-body">
            {desc}
          </p>
          {slogan && (
            <p className="mt-1 text-sm italic text-ink-muted">« {slogan} »</p>
          )}
        </div>
      </div>

      {/* ── Pied : mode de génération ─────────────────────────────────────── */}
      <div className="mt-4 flex flex-col gap-2.5 border-t border-brand-border bg-brand-light/20 px-5 py-4">
        <p className="text-2xs font-semibold uppercase tracking-wider text-brand-dark">
          Mode de génération
        </p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => onAlignChange?.(true)}
            className={`rounded-full border px-4 py-1.5 text-xs font-semibold transition-all duration-150 ${
              alignWithProject
                ? "border-brand bg-gradient-to-br from-brand to-brand-dark text-white shadow-btn"
                : "border-brand-border bg-white text-ink-muted hover:border-brand-muted hover:text-brand-dark"
            }`}
          >
            Aligné sur mon projet
          </button>
          <button
            type="button"
            onClick={() => onAlignChange?.(false)}
            className={`rounded-full border px-4 py-1.5 text-xs font-semibold transition-all duration-150 ${
              !alignWithProject
                ? "border-brand bg-gradient-to-br from-brand to-brand-dark text-white shadow-btn"
                : "border-brand-border bg-white text-ink-muted hover:border-brand-muted hover:text-brand-dark"
            }`}
          >
            Contenu libre
          </button>
        </div>
        <p className="text-xs text-ink-subtle">
          {alignWithProject
            ? "Les posts utiliseront le contexte de votre projet (nom, pitch, secteur) pour rester cohérents."
            : "Les posts suivront uniquement le sujet saisi, sans lien forcé avec votre projet."}
        </p>
      </div>

    </div>
  );
}
