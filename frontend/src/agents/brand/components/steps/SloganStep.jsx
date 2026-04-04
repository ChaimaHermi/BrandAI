import { useState } from "react";
import SectionHeader from "../SectionHeader";
import SloganSectionCard from "../SloganSectionCard";
import RegenerateDialog from "../RegenerateDialog";
import PillMultiGroup from "../PillMultiGroup";
import PillSingleGroup from "../PillSingleGroup";
import {
  SLOGAN_FORMAT_OPTIONS,
  SLOGAN_LANGUE_OPTIONS,
  SLOGAN_LONGUEUR_OPTIONS,
  SLOGAN_MESSAGE_USP_OPTIONS,
  SLOGAN_POSITIONNEMENT_OPTIONS,
  SLOGAN_STYLE_LING_OPTIONS,
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
  customSlogan,
  onSelectSlogan,
  onCustomSlogan,
  hasSloganResults = false,
}) {
  const [regenOpen, setRegenOpen] = useState(false);
  const [draftRemarks, setDraftRemarks] = useState("");

  const usingCustom = Boolean(customSlogan?.trim());
  const activeSlogan = usingCustom ? customSlogan.trim() : selectedSlogan;

  const canGenerate =
    Boolean(sloganForm.positionnement) &&
    Boolean(sloganForm.longueur) &&
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
      <div className="mb-3.5 flex items-center gap-2.5 rounded-[10px] border-[1.5px] border-[#c7d2fe] bg-[#eef2ff] px-3.5 py-2.5">
        <div className="flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-lg bg-[#6366f1] text-[13px] font-bold text-white">
          {initial}
        </div>
        <div className="min-w-0 flex-1">
          <p className="mb-px text-[10px] font-semibold uppercase tracking-[0.06em] text-[#818cf8]">
            Nom choisi
          </p>
          <p className="truncate text-[13px] font-bold text-[#4f46e5]">
            {brandName || "—"}
          </p>
        </div>
        <span className="bi-badge shrink-0 border border-[#c7d2fe] bg-white text-[#6366f1]">
          Naming ✓
        </span>
      </div>

      {/* Aperçu nom + slogan sélectionné */}
      {brandName && activeSlogan && (
        <div className="bi-card bi-fade-up mb-4 flex flex-wrap items-center gap-3 bg-[#f9fafb]">
          <span className="text-[11px] font-semibold uppercase tracking-[0.06em] text-[#9ca3af]">
            Aperçu
          </span>
          <span className="text-[15px] font-bold text-[#6366f1]">{brandName}</span>
          <span className="text-[#d1d5db]">→</span>
          <span className="text-[13px] italic text-[#374151]">
            &ldquo;{activeSlogan}&rdquo;
          </span>
        </div>
      )}

      {!hasSloganResults && (
        <>
          <SloganSectionCard
            num="1"
            title="Positionnement"
            sub="Un seul choix — l'axe principal de votre marque"
          >
            <PillSingleGroup
              label={null}
              options={SLOGAN_POSITIONNEMENT_OPTIONS}
              value={sloganForm.positionnement}
              onChange={(v) =>
                setSloganForm((s) => ({ ...s, positionnement: v }))
              }
            />
          </SloganSectionCard>

          <SloganSectionCard
            num="2"
            title="Style & ton"
            sub="Comment votre slogan doit sonner (plusieurs choix)"
          >
            <PillMultiGroup
              label={null}
              options={SLOGAN_STYLE_TON_OPTIONS}
              selected={sloganForm.sloganStyleTones}
              onChange={(v) =>
                setSloganForm((s) => ({ ...s, sloganStyleTones: v }))
              }
            />
          </SloganSectionCard>

          <SloganSectionCard
            num="3"
            title="Message à transmettre"
            sub="Ce que votre slogan doit communiquer (plusieurs choix)"
          >
            <PillMultiGroup
              label={null}
              options={SLOGAN_MESSAGE_USP_OPTIONS}
              selected={sloganForm.messageUsp}
              onChange={(v) =>
                setSloganForm((s) => ({ ...s, messageUsp: v }))
              }
            />
          </SloganSectionCard>

          <SloganSectionCard
            num="4"
            title="Format du slogan"
            sub="Structure grammaticale souhaitée (plusieurs choix)"
          >
            <PillMultiGroup
              label={null}
              options={SLOGAN_FORMAT_OPTIONS}
              selected={sloganForm.sloganFormats}
              onChange={(v) =>
                setSloganForm((s) => ({ ...s, sloganFormats: v }))
              }
            />
          </SloganSectionCard>

          <SloganSectionCard
            num="5"
            title="Style linguistique"
            sub="Effets de langage pour la mémorisation (plusieurs choix)"
          >
            <PillMultiGroup
              label={null}
              options={SLOGAN_STYLE_LING_OPTIONS}
              selected={sloganForm.styleLinguistique}
              onChange={(v) =>
                setSloganForm((s) => ({ ...s, styleLinguistique: v }))
              }
            />
          </SloganSectionCard>

          <div className="mb-2.5 grid gap-2.5 sm:grid-cols-2">
            <SloganSectionCard
              num="6"
              title="Longueur"
              sub="Taille cible du slogan"
            >
              <PillSingleGroup
                label={null}
                options={SLOGAN_LONGUEUR_OPTIONS}
                value={sloganForm.longueur}
                onChange={(v) =>
                  setSloganForm((s) => ({ ...s, longueur: v }))
                }
              />
            </SloganSectionCard>
            <SloganSectionCard
              num="7"
              title="Langue"
              sub="Langue de rédaction"
            >
              <PillSingleGroup
                label={null}
                options={SLOGAN_LANGUE_OPTIONS}
                value={sloganForm.langue}
                onChange={(v) =>
                  setSloganForm((s) => ({ ...s, langue: v }))
                }
              />
            </SloganSectionCard>
          </div>

          <SloganSectionCard
            num="8"
            title="Mots à éviter"
            sub="Termes à exclure de la génération"
          >
            <input
              className="bi-inp"
              value={sloganForm.motsEviter}
              onChange={(e) =>
                setSloganForm((s) => ({ ...s, motsEviter: e.target.value }))
              }
              placeholder="Ex: facile, simple, révolutionnaire…"
            />
          </SloganSectionCard>
        </>
      )}

      {generatedSlogans.length > 0 && (
        <div className="bi-card mt-1">
          <div className="mb-4 flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-[#22c55e]" />
            <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#22c55e]">
              Résultats — slogans
            </span>
          </div>
          <div className="flex flex-col gap-2.5">
            {generatedSlogans.map((s) => (
              <button
                key={s}
                type="button"
                onClick={() => {
                  onSelectSlogan(s);
                  onCustomSlogan("");
                }}
                className={`bi-name-card bi-card flex items-center justify-between gap-3 text-left ${
                  !usingCustom && selectedSlogan === s
                    ? "border-[#6366f1] bg-[#eef2ff]"
                    : ""
                }`}
              >
                <span
                  className={`text-[14px] font-medium italic ${
                    !usingCustom && selectedSlogan === s
                      ? "text-[#4f46e5]"
                      : "text-[#374151]"
                  }`}
                >
                  &ldquo;{s}&rdquo;
                </span>
                {!usingCustom && selectedSlogan === s && (
                  <span className="text-[#6366f1]">✦</span>
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
            ? "Complétez Positionnement, Longueur et Langue pour continuer"
            : hasSloganResults
              ? "Régénérer mes slogans →"
              : "Générer mes slogans →"}
      </button>

      {canClickPrimary && !hasSloganResults && (
        <p className="mt-2 text-center text-[11px] text-[#9ca3af]">
          Cinq propositions sont générées à partir du contexte projet et de vos
          choix.
        </p>
      )}

      {sloganGenMessage && (
        <p className="mt-3 rounded-lg bg-[#eef2ff] px-3 py-2 text-center text-[11px] font-medium text-[#4338ca]">
          {sloganGenMessage}
        </p>
      )}

      <div className="bi-card bi-fade-up mt-4 border border-dashed border-[#d1d5db]">
        <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.08em] text-[#6366f1]">
          Ou votre slogan personnalisé
        </p>
        <input
          className="bi-inp"
          value={customSlogan}
          onChange={(e) => {
            onCustomSlogan(e.target.value);
            if (e.target.value.trim()) onSelectSlogan("");
          }}
          placeholder="Saisissez votre propre phrase…"
        />
      </div>

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
