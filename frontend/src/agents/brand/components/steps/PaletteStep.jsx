import { useState } from "react";
import SectionHeader from "../SectionHeader";
import RegenerateDialog from "../RegenerateDialog";

function swatchHexes(palette) {
  const sw = palette?.swatches;
  if (!Array.isArray(sw)) return [];
  return sw.map((s) => s?.hex).filter(Boolean);
}

/**
 * @param {object} props
 * @param {Array<{ palette_name?: string, swatches?: Array<{ hex?: string, name?: string, role?: string, rationale?: string }> }>} props.paletteOptions
 * @param {string|null} props.selectedPaletteId
 * @param {(id: string) => void} props.onSelectPalette
 * @param {boolean} props.isGeneratingPalettes
 * @param {(opts?: { userRemarks?: string, fromRegeneratePopup?: boolean }) => Promise<{ ok?: boolean }|void>} props.onGeneratePalettes
 * @param {string} props.paletteGenMessage
 * @param {boolean} props.hasPaletteResults
 * @param {boolean} props.canGenerate
 * @param {string} props.brandNameLabel
 */
export default function PaletteStep({
  paletteOptions = [],
  selectedPaletteId,
  onSelectPalette,
  isGeneratingPalettes,
  onGeneratePalettes,
  paletteGenMessage,
  hasPaletteResults,
  canGenerate,
  brandNameLabel,
}) {
  const [regenOpen, setRegenOpen] = useState(false);
  const [draftRemarks, setDraftRemarks] = useState("");

  const barShowsGeneration = isGeneratingPalettes && !hasPaletteResults;

  function handlePrimaryClick() {
    if (!canGenerate || isGeneratingPalettes) return;
    if (hasPaletteResults) {
      setDraftRemarks("");
      setRegenOpen(true);
      return;
    }
    onGeneratePalettes?.({ fromRegeneratePopup: false });
  }

  async function confirmRegen() {
    const res = await onGeneratePalettes?.({
      fromRegeneratePopup: true,
    });
    if (res && res.ok) {
      setRegenOpen(false);
      setDraftRemarks("");
    }
  }

  return (
    <div className="bi-fade-up">
      <SectionHeader
        step={4}
        title="Palette de couleurs"
        sub="Trois propositions générées uniquement à partir de votre idée clarifiée (secteur, cible, offre) et de votre nom de marque — choisissez un kit."
      />

      {brandNameLabel ? (
        <p className="mb-4 text-center text-[12px] text-ink-muted">
          Marque :{" "}
          <strong className="font-semibold text-brand">{brandNameLabel}</strong>
        </p>
      ) : null}

      {hasPaletteResults && (
        <div className="mb-4">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-brand">
            Résultats — palettes
          </p>
          <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-3">
            {paletteOptions.map((p, idx) => {
              const id = `p-${idx}`;
              const hexes = swatchHexes(p);
              const selected = selectedPaletteId === id;
              const title = (p.palette_name || `Palette ${idx + 1}`).trim();
              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => onSelectPalette(id)}
                  className={`bi-name-card overflow-hidden rounded-xl border text-left transition-colors ${
                    selected
                      ? "border-brand ring-2 ring-brand/20"
                      : "border-brand-border"
                  }`}
                >
                  <div className="flex h-[72px]">
                    {hexes.length > 0 ? (
                      hexes.map((c, ci) => (
                        <div
                          key={ci}
                          className="flex-1"
                          style={{ background: c }}
                        />
                      ))
                    ) : (
                      <div className="flex-1 bg-brand-light" />
                    )}
                  </div>
                  <div className="bg-white px-4 py-3.5">
                    <div className="mb-1 flex items-center justify-between">
                      <span className="text-[13px] font-semibold text-ink">
                        {title}
                      </span>
                      {selected && <span className="text-brand">✦</span>}
                    </div>
                    <span className="bi-badge bg-brand-light text-brand-dark">
                      {hexes.length} couleur{hexes.length > 1 ? "s" : ""}
                    </span>
                    <div className="mt-2.5 flex flex-wrap gap-1.5">
                      {hexes.map((c, ci) => (
                        <div
                          key={ci}
                          className="h-[18px] w-[18px] rounded-full border border-brand-border"
                          style={{ background: c }}
                          title={c}
                        />
                      ))}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      )}

      <button
        type="button"
        disabled={!canGenerate || isGeneratingPalettes}
        onClick={handlePrimaryClick}
        className="bi-btn-primary mt-2 w-full"
      >
        {barShowsGeneration
          ? "Génération…"
          : !canGenerate
            ? "Connexion ou idée requise"
            : hasPaletteResults
              ? "Régénérer les palettes →"
              : "Générer les palettes →"}
      </button>

      {canGenerate && !hasPaletteResults && !isGeneratingPalettes && (
        <p className="mt-2 text-center text-[11px] text-ink-subtle">
          Trois palettes complètes (swatches avec codes hex) sont produites par l’IA.
        </p>
      )}

      {paletteGenMessage && (
        <p className="mt-3 rounded-lg bg-brand-light px-3 py-2 text-center text-[11px] font-medium text-brand-dark">
          {paletteGenMessage}
        </p>
      )}

      <RegenerateDialog
        open={regenOpen}
        title="Régénérer les palettes"
        description="Une nouvelle salve de trois palettes sera produite à partir de votre projet et de votre marque."
        placeholder=""
        draft={draftRemarks}
        onDraftChange={setDraftRemarks}
        confirmLabel="Générer"
        cancelLabel="Annuler"
        onCancel={() => !isGeneratingPalettes && setRegenOpen(false)}
        onConfirm={confirmRegen}
        busy={isGeneratingPalettes}
        busyHint="Génération en cours…"
      />
    </div>
  );
}
