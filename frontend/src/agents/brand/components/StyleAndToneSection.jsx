import PillMultiGroup from "./PillMultiGroup";
import {
  BRAND_VALUE_OPTIONS,
  PERSONALITY_OPTIONS,
  USER_FEELING_OPTIONS,
} from "../constants/brandFormOptions";

/**
 * @param {boolean} [props.embedded] — contenu seul dans une bi-card parent
 */
export default function StyleAndToneSection({
  brandValues,
  personality,
  userFeelings,
  onBrandValuesChange,
  onPersonalityChange,
  onUserFeelingsChange,
  embedded = false,
}) {
  const inner = (
    <>
      {!embedded && (
        <div className="mb-4">
          <h2 className="text-sm font-bold text-ink">Style &amp; ton</h2>
          <p className="text-xs text-ink-muted">Définissez la personnalité de votre marque</p>
        </div>
      )}
      <PillMultiGroup
        label="Valeurs de marque (plusieurs choix)"
        options={BRAND_VALUE_OPTIONS}
        selected={brandValues}
        onChange={onBrandValuesChange}
      />
      <PillMultiGroup
        label="Personnalité (plusieurs choix)"
        options={PERSONALITY_OPTIONS}
        selected={personality}
        onChange={onPersonalityChange}
      />
      <PillMultiGroup
        label="Comment vos utilisateurs doivent se sentir"
        options={USER_FEELING_OPTIONS}
        selected={userFeelings}
        onChange={onUserFeelingsChange}
      />
    </>
  );

  if (embedded) {
    return <div className="bi-card bi-fade-up bi-d1">{inner}</div>;
  }

  return (
    <section className="rounded-xl border border-brand-border bg-white p-5 shadow-card">
      {inner}
    </section>
  );
}
