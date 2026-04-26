import { useState } from "react";
import SectionHeader from "../SectionHeader";
import RegenerateDialog from "../RegenerateDialog";
import PillMultiGroup from "../PillMultiGroup";
import PillSingleGroup from "../PillSingleGroup";
import {
  SLOGAN_LANGUE_OPTIONS,
  SLOGAN_LONGUEUR_OPTIONS,
  SLOGAN_POSITIONNEMENT_OPTIONS,
  SLOGAN_STYLE_TON_OPTIONS,
} from "../../constants/brandFormOptions";

/**
 * Formulaire slogan (prefs) + génération + sélection — UI comme Naming (bi-*).
 */
export default function SloganStep({
  brandName,
  sloganForm,
  setSloganForm,
  generatedSlogans,
  isGeneratingSlogans,
  onGenerateSlogans,
  sloganGenMessage,
  selectedSlogan,
  onSelectSlogan,
  hasSloganResults = false,
}) {
  const [regenOpen, setRegenOpen] = useState(false);
  const [draftRemarks, setDraftRemarks] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);

  const activeSlogan = selectedSlogan?.trim() || "";

  const canGenerate =
    Boolean(sloganForm.positionnement) &&
    Boolean(sloganForm.langue);

  const canClickPrimary =
    hasSloganResults || canGenerate;

  const barShowsSloganGeneration =
    isGeneratingSlogans && !hasSloganResults;

  const initial = (brandName && brandName[0] ? brandName[0] : "B").toUpperCase();

  function handlePrimarySloganClick() {
    if (isGeneratingSlogans) return;
    if (hasSloganResults) {
      setDraftRemarks("");
      setRegenOpen(true);
      return;
    }
    if (!canGenerate) return;
    onGenerateSlogans?.({ userRemarks: "", fromRegeneratePopup: false });
  }

  function closeRegen() {
    if (isGeneratingSlogans) return;
    setRegenOpen(false);
  }

  async function confirmRegen() {
    const res = await onGenerateSlogans?.({
      userRemarks: (draftRemarks || "").trim(),
      fromRegeneratePopup: true,
    });
    if (res?.ok) {
      setRegenOpen(false);
      setDraftRemarks("");
    }
  }

  return (
    <div className="bi-fade-up">
      <SectionHeader
        step={3}
        title="Slogan"
        sub={
          hasSloganResults
            ? "Sélectionnez un slogan ou ouvrez Régénérer pour affiner."
            : "Renseignez les préférences, puis générez les slogans."
        }
      />

      {/* Nom choisi — bandeau comme maquette */}
      <div className="mb-3.5 flex items-center gap-2.5 rounded-[10px] border-[1.5px] border-brand/30 bg-brand-light px-3.5 py-2.5">
        <div className="flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-lg bg-brand text-[13px] font-bold text-white">
          {initial}
        </div>
        <div className="min-w-0 flex-1">
          <p className="mb-px text-[10px] font-semibold uppercase tracking-[0.06em] text-brand-muted">
            Nom choisi
          </p>
          <p className="truncate text-[13px] font-bold text-brand-darker">
            {brandName || "—"}
          </p>
        </div>
        <span className="bi-badge shrink-0 border border-brand/30 bg-white text-brand">
          Naming ✓
        </span>
      </div>

      {/* Aperçu nom + slogan sélectionné */}
      {brandName && activeSlogan && (
        <div className="bi-card bi-fade-up mb-4 flex flex-wrap items-center gap-3 bg-brand-light/40">
          <span className="text-[11px] font-semibold uppercase tracking-[0.06em] text-ink-subtle">
            Aperçu
          </span>
          <span className="text-[15px] font-bold text-brand">{brandName}</span>
          <span className="text-ink-subtle">→</span>
          <span className="text-[13px] italic text-ink-body">
            &ldquo;{activeSlogan}&rdquo;
          </span>
        </div>
      )}

      {!hasSloganResults && (
        <>
          <div className="bi-card mb-3">
            <p className="mb-1 text-[11px] font-bold uppercase tracking-[0.08em] text-brand">
              Préférences essentielles
            </p>
            <p className="mb-3 text-xs text-ink-subtle">
              Renseignez seulement ces champs pour générer rapidement des slogans.
            </p>

            <div className="mb-3">
              <PillSingleGroup
                label="Positionnement"
                options={SLOGAN_POSITIONNEMENT_OPTIONS}
                value={sloganForm.positionnement}
                onChange={(v) =>
                  setSloganForm((s) => ({ ...s, positionnement: v }))
                }
              />
            </div>

            <div className="mb-3">
              <PillSingleGroup
                label="Langue"
                options={SLOGAN_LANGUE_OPTIONS}
                value={sloganForm.langue}
                onChange={(v) =>
                  setSloganForm((s) => ({ ...s, langue: v }))
                }
              />
            </div>

            <PillMultiGroup
              label="Style & ton"
              options={SLOGAN_STYLE_TON_OPTIONS}
              selected={sloganForm.sloganStyleTones}
              onChange={(v) =>
                setSloganForm((s) => ({ ...s, sloganStyleTones: v }))
              }
            />
          </div>

          <div className="bi-card">
            <button
              type="button"
              onClick={() => setShowAdvanced((v) => !v)}
              className="flex w-full items-center justify-between rounded-lg border border-brand-border bg-brand-light/40 px-3 py-2 text-left text-[12px] font-semibold text-brand-darker"
            >
              <span>Options avancées (optionnel)</span>
              <span>{showAdvanced ? "−" : "+"}</span>
            </button>

            {showAdvanced && (
              <div className="mt-3 grid gap-2.5 sm:grid-cols-2">
              <PillSingleGroup
                label="Longueur"
                options={SLOGAN_LONGUEUR_OPTIONS}
                value={sloganForm.longueur}
                onChange={(v) =>
                  setSloganForm((s) => ({ ...s, longueur: v }))
                }
              />
              <div>
                <label className="mb-2 block text-xs font-semibold text-ink" htmlFor="slogan-avoid-words">
                  Mots à éviter
                </label>
                <input
                  id="slogan-avoid-words"
                  className="bi-inp"
                  value={sloganForm.motsEviter}
                  onChange={(e) =>
                    setSloganForm((s) => ({ ...s, motsEviter: e.target.value }))
                  }
                  placeholder="Ex: facile, simple, révolutionnaire…"
                />
              </div>
            </div>
            )}
          </div>
        </>
      )}

      {generatedSlogans.length > 0 && (
        <div className="bi-card mt-1">
          <div className="mb-4 flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-success" />
            <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-success">
              Résultats — slogans
            </span>
          </div>
          <div className="flex flex-col gap-2.5">
            {generatedSlogans.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => onSelectSlogan(s)}
                className={`bi-name-card bi-card flex items-center justify-between gap-3 text-left ${
                  selectedSlogan === s ? "border-brand bg-brand-light" : ""
                }`}
              >
                <span
                  className={`text-[14px] font-medium italic ${
                    selectedSlogan === s ? "text-brand-darker" : "text-ink-body"
                  }`}
                >
                  &ldquo;{s}&rdquo;
                </span>
                {selectedSlogan === s && (
                  <span className="text-brand">✦</span>
                )}
              </button>
            ))}
          </div>
        </div>
      )}

      <button
        type="button"
        disabled={!canClickPrimary || isGeneratingSlogans}
        onClick={handlePrimarySloganClick}
        className="bi-btn-primary mt-4 w-full"
      >
        {barShowsSloganGeneration
          ? "Génération…"
          : !hasSloganResults && !canGenerate
            ? "Complétez Positionnement et Langue pour continuer"
            : hasSloganResults
              ? "Régénérer mes slogans →"
              : "Générer mes slogans →"}
      </button>

      {canClickPrimary && !hasSloganResults && (
        <p className="mt-2 text-center text-[11px] text-ink-subtle">
          Trois propositions sont générées à partir du contexte projet et de vos
          choix.
        </p>
      )}

      {sloganGenMessage && (
        <p className="mt-3 rounded-lg bg-brand-light px-3 py-2 text-center text-[11px] font-medium text-brand-dark">
          {sloganGenMessage}
        </p>
      )}

      <RegenerateDialog
        open={regenOpen}
        title="Régénérer les slogans"
        description="Précisez ce que vous voulez changer (ton, longueur, message…). Laissez vide pour une nouvelle salve sans consigne supplémentaire."
        placeholder="Ex. : plus punchy, moins formel, insister sur la communauté…"
        draft={draftRemarks}
        onDraftChange={setDraftRemarks}
        confirmLabel="Générer"
        cancelLabel="Annuler"
        onCancel={closeRegen}
        onConfirm={confirmRegen}
        busy={isGeneratingSlogans}
        busyHint="Génération en cours…"
      />
    </div>
  );
}
