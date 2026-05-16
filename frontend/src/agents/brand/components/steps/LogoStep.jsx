import { useMemo, useState } from "react";
import SectionHeader from "../SectionHeader";
import RegenerateDialog from "../RegenerateDialog";

const STEP_LABELS = {
  context:     "Chargement du contexte",
  prompt:      "Génération du prompt image",
  image:       "Génération de l'image",
  background:  "Suppression du fond",
  originality: "Vérification d'originalité",
  upload:      "Sauvegarde Cloudinary",
  persist:     "Sauvegarde des résultats",
};

function StepIcon({ status }) {
  if (status === "running")
    return <span className="inline-block h-3 w-3 animate-spin rounded-full border-2 border-brand border-t-transparent" />;
  if (status === "done")
    return <span className="text-emerald-500 text-sm font-bold">✓</span>;
  if (status === "error")
    return <span className="text-red-400 text-sm font-bold">✗</span>;
  return <span className="inline-block h-3 w-3 rounded-full bg-ink-subtle/30" />;
}

export default function LogoStep({
  canGenerate,
  isGeneratingLogo,
  onGenerateLogo,
  logoGenMessage,
  logoPreviewUrl,
  logoPreviewTransparentUrl = null,
  logoConcept = null,
  hasLogoResult = false,
  logoSteps = [],
}) {
  const [variant, setVariant] = useState("with_bg");
  const [regenOpen, setRegenOpen] = useState(false);
  const [draftRemarks, setDraftRemarks] = useState("");

  const canShowTransparent = Boolean(logoPreviewTransparentUrl);
  const activeUrl = useMemo(() => {
    if (variant === "without_bg" && logoPreviewTransparentUrl) {
      return logoPreviewTransparentUrl;
    }
    return logoPreviewUrl;
  }, [variant, logoPreviewTransparentUrl, logoPreviewUrl]);

  function handlePrimaryClick() {
    if (isGeneratingLogo) return;
    if (hasLogoResult) {
      setDraftRemarks("");
      setRegenOpen(true);
    } else {
      onGenerateLogo?.({ remarks: "" });
    }
  }

  function handleRegenConfirm() {
    setRegenOpen(false);
    onGenerateLogo?.({ remarks: draftRemarks });
  }

  const primaryLabel = isGeneratingLogo
    ? "Génération en cours…"
    : hasLogoResult
    ? "Régénérer le logo"
    : "Générer le logo";

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
          onClick={handlePrimaryClick}
          disabled={!canGenerate || isGeneratingLogo}
        >
          {primaryLabel}
        </button>

        {/* Étapes SSE en temps réel */}
        {logoSteps.length > 0 && (
          <div className="w-full max-w-sm rounded-xl border border-brand-border bg-white/70 px-4 py-3 shadow-sm">
            <ul className="space-y-2">
              {logoSteps.map((step) => (
                <li key={step.id} className="flex items-center gap-2.5">
                  <StepIcon status={step.status} />
                  <span
                    className={`text-[13px] ${
                      step.status === "running"
                        ? "font-semibold text-ink"
                        : step.status === "error"
                        ? "text-red-500"
                        : "text-ink-muted"
                    }`}
                  >
                    {STEP_LABELS[step.id] ?? step.label}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

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

      <RegenerateDialog
        open={regenOpen}
        title="Régénérer le logo"
        description="Le logo actuel ne vous convient pas ? Décrivez ce que vous souhaitez changer et un nouveau logo complètement différent sera généré."
        placeholder="Ex : je veux quelque chose de plus minimaliste, avec une icône plus originale, style tech moderne…"
        draft={draftRemarks}
        onDraftChange={setDraftRemarks}
        confirmLabel="Régénérer"
        onCancel={() => setRegenOpen(false)}
        onConfirm={handleRegenConfirm}
        busy={isGeneratingLogo}
        busyHint="Génération du nouveau logo…"
      />
    </div>
  );
}
