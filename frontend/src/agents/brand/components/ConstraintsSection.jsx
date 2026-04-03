import PillSingleGroup from "./PillSingleGroup";
import {
  NAME_LANGUAGE_OPTIONS,
  NAME_LENGTH_OPTIONS,
} from "../constants/brandFormOptions";

/**
 * @param {boolean} [props.embedded]
 */
export default function ConstraintsSection({
  nameLanguage,
  nameLength,
  includeKeywords,
  excludeKeywords,
  onNameLanguageChange,
  onNameLengthChange,
  onIncludeChange,
  onExcludeChange,
  embedded = false,
}) {
  const inner = (
    <>
      {!embedded && (
        <div className="mb-4">
          <h2 className="text-[15px] font-bold text-[#111827]">
            Contraintes &amp; préférences
          </h2>
          <p className="text-[12px] text-[#6b7280]">
            Guidez la génération avec des règles précises
          </p>
        </div>
      )}

      <div className="mt-1 grid gap-6 sm:grid-cols-2">
        <div>
          <PillSingleGroup
            label="Langue du nom"
            options={NAME_LANGUAGE_OPTIONS}
            value={nameLanguage}
            onChange={onNameLanguageChange}
          />
          <PillSingleGroup
            label="Longueur"
            options={NAME_LENGTH_OPTIONS}
            value={nameLength}
            onChange={onNameLengthChange}
          />
        </div>
        <div className="flex flex-col gap-4">
          <div>
            <label
              className="mb-2 block text-[12px] font-semibold text-[#111827]"
              htmlFor="bi-inc-keywords"
            >
              Mots-clés à inclure
            </label>
            <input
              id="bi-inc-keywords"
              type="text"
              value={includeKeywords}
              onChange={(e) => onIncludeChange(e.target.value)}
              placeholder="Ex: stage, match"
              className="bi-inp"
            />
          </div>
          <div>
            <label
              className="mb-2 block text-[12px] font-semibold text-[#111827]"
              htmlFor="bi-exc-keywords"
            >
              Mots à éviter
            </label>
            <input
              id="bi-exc-keywords"
              type="text"
              value={excludeKeywords}
              onChange={(e) => onExcludeChange(e.target.value)}
              placeholder="Ex: work, job..."
              className="bi-inp"
            />
          </div>
        </div>
      </div>
    </>
  );

  if (embedded) {
    return <div className="bi-card bi-fade-up bi-d1">{inner}</div>;
  }

  return (
    <section className="rounded-xl border border-[#e5e7eb] bg-white p-5 shadow-sm">
      {inner}
    </section>
  );
}
