import { useEffect, useState, useCallback } from "react";
import { FiImage, FiRefreshCw, FiTarget, FiEdit3 } from "react-icons/fi";
import { Loader } from "@/shared/ui/Loader";
import { fetchBrandingBundle } from "@/agents/brand/api/brandIdentity.api";
import { buildContentProjectDisplay } from "../utils/projectContextFromDb";

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

  useEffect(() => { loadBundle(); }, [loadBundle]);

  if (!idea?.id) return null;

  const display = buildContentProjectDisplay(idea, bundle);
  const { brandName, ideaName, projectDescription, slogan, logoUrl, subtitle } = display;
  const desc = projectDescription || subtitle || "Aucune description renseignée pour cette idée.";

  return (
    <div className="rounded-2xl border border-brand-border bg-white shadow-card">

      {/* ── Bande supérieure colorée ─────────────────────────────────────────── */}
      <div
        className="flex items-center justify-between rounded-t-2xl px-5 py-2"
        style={{ background: "linear-gradient(135deg,#6C63FF18,#a78bfa0d)" }}
      >
        <span className="inline-flex items-center gap-1.5 text-2xs font-bold uppercase tracking-widest text-brand">
          <span className="h-1.5 w-1.5 rounded-full bg-brand" />
          Projet enregistré
        </span>
        {bundleError && (
          <button
            type="button"
            onClick={loadBundle}
            className="inline-flex items-center gap-1 rounded-full border border-brand-border bg-white px-2.5 py-1 text-2xs font-semibold text-ink-muted transition-all hover:border-brand-muted hover:text-brand-dark"
          >
            <FiRefreshCw size={10} /> Réessayer
          </button>
        )}
      </div>

      {/* ── Corps : logo + nom + description + slogan ────────────────────────── */}
      <div className="flex flex-col gap-4 px-5 py-4 sm:flex-row sm:items-start">

        {/* Logo */}
        <div className="mx-auto shrink-0 sm:mx-0">
          {bundleLoading ? (
            <div className="flex h-[72px] w-[72px] items-center justify-center rounded-2xl border border-brand-border bg-brand-light/20 shadow-sm">
              <Loader className="h-5 w-5" />
            </div>
          ) : logoUrl ? (
            <div className="flex h-[72px] w-[72px] items-center justify-center rounded-2xl border border-brand-border bg-white p-1.5 shadow-sm ring-2 ring-brand/10">
              <img
                src={logoUrl}
                alt="Logo"
                className="max-h-full max-w-full object-contain"
              />
            </div>
          ) : (
            <div className="flex h-[72px] w-[72px] flex-col items-center justify-center gap-1 rounded-2xl border border-dashed border-brand-border bg-brand-light/20 text-brand-muted">
              <FiImage size={22} aria-hidden />
              <span className="text-[9px] font-semibold uppercase tracking-wide">Logo</span>
            </div>
          )}
        </div>

        {/* Infos textuelles */}
        <div className="min-w-0 flex-1 space-y-1">
          <h2 className="text-lg font-extrabold leading-tight text-ink">{brandName}</h2>
          {ideaName && ideaName !== brandName && (
            <p className="text-2xs font-medium text-ink-subtle">Idée : {ideaName}</p>
          )}
          <p className="text-sm leading-relaxed text-ink-muted">{desc}</p>

          {/* Slogan */}
          {slogan && (
            <div className="mt-2 inline-flex items-start gap-2 rounded-xl border border-brand-border/60 bg-brand-light/30 px-3 py-2">
              <span className="mt-0.5 text-xl font-black leading-none text-brand/40">"</span>
              <p className="text-xs italic leading-relaxed text-brand-dark">{slogan}</p>
              <span className="self-end text-xl font-black leading-none text-brand/40">"</span>
            </div>
          )}
        </div>
      </div>

      {/* ── Séparateur + Mode de génération ──────────────────────────────────── */}
      <div className="border-t border-brand-border bg-brand-light/10 px-5 py-4">
        <p className="mb-2.5 text-2xs font-bold uppercase tracking-widest text-ink-subtle">
          Mode de génération
        </p>

        {/* Segmented control */}
        <div className="flex rounded-xl border border-brand-border bg-white p-1 shadow-sm w-fit gap-1">
          <button
            type="button"
            onClick={() => onAlignChange?.(true)}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition-all duration-200 ${
              alignWithProject
                ? "bg-brand text-white shadow-sm"
                : "text-ink-muted hover:text-brand-dark"
            }`}
          >
            <FiTarget className={`h-3.5 w-3.5 shrink-0 ${alignWithProject ? "text-white" : "text-ink-muted"}`} />
            Aligné sur mon projet
          </button>
          <button
            type="button"
            onClick={() => onAlignChange?.(false)}
            className={`flex items-center gap-2 rounded-lg px-4 py-2 text-xs font-semibold transition-all duration-200 ${
              !alignWithProject
                ? "bg-brand text-white shadow-sm"
                : "text-ink-muted hover:text-brand-dark"
            }`}
          >
            <FiEdit3 className={`h-3.5 w-3.5 shrink-0 ${!alignWithProject ? "text-white" : "text-ink-muted"}`} />
            Contenu libre
          </button>
        </div>

        {/* Description du mode actif */}
        <p className="mt-2.5 text-xs text-ink-subtle">
          {alignWithProject
            ? "Les posts utiliseront le contexte de votre projet (nom, pitch, secteur) pour rester cohérents."
            : "Les posts suivront uniquement le sujet saisi, sans lien forcé avec votre projet."}
        </p>
      </div>

    </div>
  );
}
