import SectionHeader from "../SectionHeader";

export default function LogoStep({
  canGenerate,
  isGeneratingLogo,
  onGenerateLogo,
  logoGenMessage,
  logoPreviewUrl,
}) {
  return (
    <div className="bi-fade-up">
      <SectionHeader
        step={5}
        title="Logo"
        sub="Générez une proposition de logo à partir de votre nom, slogan et palette (IA + image)."
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

        {logoPreviewUrl ? (
          <div className="w-full max-w-sm rounded-2xl border border-brand-border bg-brand-light/30 p-4 shadow-card">
            <p className="mb-3 text-center text-[11px] font-semibold uppercase tracking-[0.08em] text-ink-subtle">
              Aperçu
            </p>
            <img
              src={logoPreviewUrl}
              alt="Logo généré"
              className="mx-auto max-h-56 w-auto rounded-lg object-contain"
            />
          </div>
        ) : null}
      </div>
    </div>
  );
}
