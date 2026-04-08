/**
 * En-tête d'étape — design system brand tokens.
 */
export default function SectionHeader({ step, title, sub }) {
  const stepLabel = String(step).padStart(2, "0");
  return (
    <div className="mb-6 bi-fade-up">
      <div className="mb-1.5 flex items-center">
        <span className="text-2xs font-semibold uppercase tracking-[0.08em] text-brand">
          Étape {stepLabel}
        </span>
        <div className="bi-sec-line" />
      </div>
      <h2 className="mb-1 text-xl font-bold text-ink">{title}</h2>
      {sub && <p className="m-0 text-sm text-ink-muted">{sub}</p>}
    </div>
  );
}
