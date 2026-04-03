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
    onGeneratePalettes?.({ userRemarks: "", fromRegeneratePopup: false });
  }

  async function confirmRegen() {
    const res = await onGeneratePalettes?.({
      userRemarks: (draftRemarks || "").trim(),
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
        sub="Trois propositions générées à partir de votre projet et de votre nom de marque — choisissez un kit cohérent."
      />

      {brandNameLabel ? (
        <p className="mb-4 text-center text-[12px] text-[#6b7280]">
          Marque :{" "}
          <strong className="font-semibold text-[#6366f1]">{brandNameLabel}</strong>
        </p>
      ) : null}

      {hasPaletteResults && (
        <div className="mb-4">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#6366f1]">
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
                      ? "border-[#6366f1] ring-2 ring-[#c7d2fe]"
                      : "border-[#e5e7eb]"
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
                      <div className="flex-1 bg-[#f3f4f6]" />
                    )}
                  </div>
                  <div className="bg-white px-4 py-3.5">
                    <div className="mb-1 flex items-center justify-between">
                      <span className="text-[13px] font-semibold text-[#111827]">
                        {title}
                      </span>
                      {selected && <span className="text-[#6366f1]">✦</span>}
                    </div>
                    <span className="bi-badge bg-[#eef2ff] text-[#4338ca]">
                      {hexes.length} couleur{hexes.length > 1 ? "s" : ""}
                    </span>
                    <div className="mt-2.5 flex flex-wrap gap-1.5">
                      {hexes.map((c, ci) => (
                        <div
                          key={ci}
                          className="h-[18px] w-[18px] rounded-full border border-[#e5e7eb]"
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
        <p className="mt-2 text-center text-[11px] text-[#9ca3af]">
          Trois palettes complètes (swatches avec codes hex) sont produites par l’IA.
        </p>
      )}

      {paletteGenMessage && (
        <p className="mt-3 rounded-lg bg-[#eef2ff] px-3 py-2 text-center text-[11px] font-medium text-[#4338ca]">
          {paletteGenMessage}
        </p>
      )}

      <RegenerateDialog
        open={regenOpen}
        title="Régénérer les palettes"
        description="Indiquez des contraintes (ambiance, teintes à éviter…). Laissez vide pour une nouvelle salve."
        placeholder="Ex. : plus chaud, éviter le rose, style premium sombre…"
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
