import { useMemo, useState } from "react";
import SectionHeader from "../SectionHeader";

export default function LogoStep({
  canGenerate,
  isGeneratingLogo,
  onGenerateLogo,
  logoGenMessage,
  logoPreviewUrl,
  logoPreviewTransparentUrl = null,
  logoConcept = null,
}) {
  const [variant, setVariant] = useState("with_bg");
  const canShowTransparent = Boolean(logoPreviewTransparentUrl);
  const activeUrl = useMemo(() => {
    if (variant === "without_bg" && logoPreviewTransparentUrl) {
      return logoPreviewTransparentUrl;
    }
    return logoPreviewUrl;
  }, [variant, logoPreviewTransparentUrl, logoPreviewUrl]);

  return (
    <div className="bi-fade-up">
      <SectionHeader
        step={5}
        title="Logo"
        sub="Générez une proposition de logo à partir de votre nom, palette et contexte projet."
      />

      <div className="flex flex-col items-center gap-6 py-2">
        <button
          type="button"
          className="bi-btn-primary min-w-[220px] px-8 py-3 text-[15px] font-semibold"
          onClick={() => onGenerateLogo?.()}
          disabled={!canGenerate || isGeneratingLogo}
        >
          {isGeneratingLogo ? "Génération en cours…" : "Générer le logo"}
        </button>

        {logoGenMessage ? (
          <p
            className={`max-w-md text-center text-[13px] ${
              logoGenMessage.includes("échou") || logoGenMessage.includes("Erreur")
                ? "text-red-600"
                : "text-ink-muted"
            }`}
          >
            {logoGenMessage}
          </p>
        ) : null}

        {(logoPreviewUrl || logoPreviewTransparentUrl) ? (
          <div className="w-full max-w-sm rounded-2xl border border-brand-border bg-brand-light/30 p-4 shadow-card">
            <p className="mb-3 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-subtle">
              Aperçu
            </p>
            <div className="mb-3 flex items-center justify-center gap-2">
              <button
                type="button"
                onClick={() => setVariant("with_bg")}
                className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                  variant === "with_bg"
                    ? "bg-brand text-white"
                    : "border border-brand-border bg-white text-ink-muted hover:bg-brand-light"
                }`}
              >
                Avec fond
              </button>
              <button
                type="button"
                onClick={() => canShowTransparent && setVariant("without_bg")}
                disabled={!canShowTransparent}
                className={`rounded-full px-3 py-1 text-xs font-semibold transition ${
                  variant === "without_bg"
                    ? "bg-brand text-white"
                    : "border border-brand-border bg-white text-ink-muted hover:bg-brand-light"
                } ${!canShowTransparent ? "cursor-not-allowed opacity-50" : ""}`}
              >
                Sans fond
              </button>
            </div>
            {activeUrl ? (
              <img
                src={activeUrl}
                alt="Logo généré"
                className="mx-auto max-h-56 w-auto rounded-lg object-contain"
              />
            ) : null}
            {logoConcept?.image_attribution ? (
              <p className="mt-3 text-center text-[11px] leading-snug text-ink-subtle">
                {logoConcept.image_attribution}
              </p>
            ) : null}
          </div>
        ) : null}
      </div>
    </div>
  );
}
