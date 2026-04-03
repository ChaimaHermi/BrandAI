import { useState } from "react";
import RegenerateDialog from "./RegenerateDialog";

/**
 * Première génération : clic direct. Régénération : popup ; chargement dans la zone texte ; fermeture seulement si succès.
 * `onGenerate` peut retourner `{ ok: true }` ou `{ ok: false }`.
 */
export default function GenerateBar({
  disabled,
  isGenerating,
  onGenerate,
  lastMockMessage,
  hasExistingResults = false,
}) {
  const [regenOpen, setRegenOpen] = useState(false);
  const [draftRemarks, setDraftRemarks] = useState("");

  const barShowsGeneration =
    isGenerating && !hasExistingResults;

  const label = barShowsGeneration
    ? "Génération…"
    : hasExistingResults
      ? "Régénérer les noms"
      : "Générer les noms";

  function handlePrimaryClick() {
    if (disabled || isGenerating) return;
    if (hasExistingResults) {
      setDraftRemarks("");
      setRegenOpen(true);
      return;
    }
    onGenerate?.({ userRemarks: "", fromRegeneratePopup: false });
  }

  function closeRegen() {
    if (isGenerating) return;
    setRegenOpen(false);
  }

  async function confirmRegen() {
    const res = await onGenerate?.({
      userRemarks: (draftRemarks || "").trim(),
      fromRegeneratePopup: true,
    });
    if (res && res.ok) {
      setRegenOpen(false);
      setDraftRemarks("");
    }
  }

  return (
    <>
      <div className="bi-card bi-fade-up bi-d2 border-[#c7d2fe] bg-gradient-to-br from-[#eef2ff] to-white">
        <div className="flex justify-end">
          <button
            type="button"
            disabled={disabled || isGenerating}
            onClick={handlePrimaryClick}
            className="bi-btn-primary shrink-0 whitespace-nowrap"
          >
            {label}
          </button>
        </div>
        {lastMockMessage && (
          <p className="mt-3 rounded-lg bg-[#eef2ff] px-3 py-2 text-[11px] font-medium text-[#4338ca]">
            {lastMockMessage}
          </p>
        )}
      </div>

      <RegenerateDialog
        open={regenOpen}
        title="Régénérer les noms"
        description="Ajoutez des remarques pour orienter la nouvelle salve (ton, style, longueur, mots à éviter…). Laissez vide pour une nouvelle proposition sans consigne supplémentaire."
        placeholder="Ex. : plus court, son premium, moins technique…"
        draft={draftRemarks}
        onDraftChange={setDraftRemarks}
        confirmLabel="Générer"
        cancelLabel="Annuler"
        onCancel={closeRegen}
        onConfirm={confirmRegen}
        busy={isGenerating}
        busyHint="Génération en cours…"
      />
    </>
  );
}
