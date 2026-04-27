import { useState } from "react";
import { FiCheck } from "react-icons/fi";
import StyleAndToneSection from "../StyleAndToneSection";
import ConstraintsSection from "../ConstraintsSection";
import GenerateBar from "../GenerateBar";
import SectionHeader from "../SectionHeader";

/**
 * Étape unique Naming : formulaire complet (style, contraintes), génération, résultats.
 */
export default function NamingStep({
  styleTon,
  onStyleTon,
  constraints,
  onConstraints,
  canGenerate,
  isGenerating,
  onGenerate,
  lastMockMessage,
  record,
  names,
  status,
  errors,
  chosenBrandName,
  onChooseBrandName,
  hasNamingResults = false,
}) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const pipelineBadge = record?.status;

  const allNotExists =
    names.length > 0 &&
    names.every((n) => n?.availability === "not_exists");
  const someOtherAvailability = names.some(
    (n) => n?.availability != null && n.availability !== "not_exists",
  );

  return (
    <div className="bi-fade-up">
      <SectionHeader
        step={2}
        title="Naming"
        sub={
          hasNamingResults
            ? "Sélectionnez un nom ou ouvrez Régénérer pour affiner."
            : "Définissez le style et les contraintes, puis générez les noms."
        }
      />

      <div className="flex flex-col gap-4">
        {!hasNamingResults && (
          <>
            <div className="bi-card">
              <p className="mb-1 text-[11px] font-bold uppercase tracking-[0.08em] text-brand">
                Préférences principales
              </p>
              <p className="mb-3 text-xs text-ink-subtle">
                Définissez le style de marque, puis générez rapidement 3 noms.
              </p>
              <StyleAndToneSection
                embedded={false}
                brandValues={styleTon.brandValues}
                personality={styleTon.personality}
                userFeelings={styleTon.userFeelings}
                onBrandValuesChange={(v) =>
                  onStyleTon((s) => ({ ...s, brandValues: v }))
                }
                onPersonalityChange={(v) =>
                  onStyleTon((s) => ({ ...s, personality: v }))
                }
                onUserFeelingsChange={(v) =>
                  onStyleTon((s) => ({ ...s, userFeelings: v }))
                }
              />
            </div>

            <div className="bi-card">
              <button
                type="button"
                onClick={() => setShowAdvanced((v) => !v)}
                className="flex w-full items-center justify-between rounded-lg border border-brand-border bg-brand-light/40 px-3 py-2 text-left text-[12px] font-semibold text-brand-darker"
              >
                <span>Contraintes avancées (optionnel)</span>
                <span>{showAdvanced ? "−" : "+"}</span>
              </button>
              {showAdvanced && (
                <div className="mt-3">
                  <ConstraintsSection
                    embedded={false}
                    nameLanguage={constraints.nameLanguage}
                    nameLength={constraints.nameLength}
                    includeKeywords={constraints.includeKeywords}
                    excludeKeywords={constraints.excludeKeywords}
                    onNameLanguageChange={(v) =>
                      onConstraints((c) => ({ ...c, nameLanguage: v }))
                    }
                    onNameLengthChange={(v) =>
                      onConstraints((c) => ({ ...c, nameLength: v }))
                    }
                    onIncludeChange={(v) =>
                      onConstraints((c) => ({ ...c, includeKeywords: v }))
                    }
                    onExcludeChange={(v) =>
                      onConstraints((c) => ({ ...c, excludeKeywords: v }))
                    }
                  />
                </div>
              )}
            </div>
          </>
        )}

        {Object.keys(errors).length > 0 && (
          <div className="rounded-xl border border-red-100 bg-red-50/80 px-4 py-3 text-[13px] text-red-800">
            <div className="font-bold">Erreurs agent (dernier enregistrement)</div>
            <ul className="mt-2 list-inside list-disc">
              {Object.entries(errors).map(([k, v]) => (
                <li key={k}>
                  <span className="font-semibold">{k}</span>: {String(v)}
                </li>
              ))}
            </ul>
          </div>
        )}

        {names.length > 0 && (
          <div className="bi-card">
            <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-success" />
                <span className="text-xs font-semibold uppercase tracking-[0.08em] text-success">
                  Résultats — noms
                </span>
              </div>
              {pipelineBadge && (
                <span className="bi-badge bg-brand-light text-brand-dark">
                  {pipelineBadge}
                  {status ? ` · ${status}` : ""}
                </span>
              )}
            </div>

            {names.length > 0 && allNotExists && (
              <div className="mb-4 overflow-hidden rounded-xl border border-success-border bg-gradient-to-r from-success-light via-white to-brand-light px-4 py-3.5">
                <p className="text-sm font-semibold leading-snug text-success-dark">
                  Des pistes uniques sur le marché
                </p>
                <p className="mt-1.5 text-xs leading-relaxed text-ink-body">
                  Ces noms ne correspondent pas à des marques déjà référencées dans notre
                  analyse de marché — vous partez sur des bases plus distinctives pour votre
                  identité.
                </p>
              </div>
            )}

            {names.length > 0 && someOtherAvailability && !allNotExists && (
              <div className="mb-4 rounded-xl border border-amber-100 bg-amber-50/80 px-4 py-3 text-xs leading-relaxed text-amber-950">
                <span className="font-semibold">À croiser : </span>
                certaines propositions peuvent être proches d’une marque existante — les
                cartes concernées sont indiquées ci-dessous.
              </div>
            )}

            <div className="grid gap-3 sm:grid-cols-2">
              {names.map((opt, i) => {
                const n = opt?.name ?? "—";
                const selected = chosenBrandName === n;
                return (
                  <button
                    key={`${n}-${i}`}
                    type="button"
                    onClick={() => onChooseBrandName(n)}
                    className={`bi-name-card text-left rounded-xl border p-4 transition-all ${
                      selected
                        ? "border-brand bg-brand-light ring-2 ring-brand/20"
                        : "border-brand-border bg-brand-50 hover:border-brand-muted"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <span
                        className={`text-base font-bold ${
                          selected ? "text-brand-darker" : "text-ink"
                        }`}
                      >
                        {n}
                      </span>
                      {selected && (
                        <FiCheck size={16} className="mt-0.5 shrink-0 text-brand" aria-hidden />
                      )}
                    </div>
                    {opt?.availability != null &&
                      opt.availability !== "not_exists" && (
                        <div className="mt-1 text-xs font-medium text-amber-800">
                          {opt.availability === "exists"
                            ? "Proximité possible avec une marque référencée — à vérifier"
                            : `Statut marché : ${String(opt.availability)}`}
                        </div>
                      )}
                    {(opt?.rationale || opt?.description) && (
                      <p className="mt-2 text-xs leading-relaxed text-ink-muted">
                        {opt.rationale || opt.description}
                      </p>
                    )}
                  </button>
                );
              })}
            </div>
          </div>
        )}

        <GenerateBar
          disabled={!canGenerate}
          isGenerating={isGenerating}
          onGenerate={onGenerate}
          lastMockMessage={lastMockMessage}
          hasExistingResults={hasNamingResults}
        />
      </div>
    </div>
  );
}
