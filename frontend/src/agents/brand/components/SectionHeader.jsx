/**
 * En-tête d’étape aligné sur « Brand Identity Studio » (indigo + ligne).
 */
export default function SectionHeader({ step, title, sub }) {
  const stepLabel = String(step).padStart(2, "0");
  return (
    <div className="mb-6 bi-fade-up">
      <div className="mb-1.5 flex items-center">
        <span className="text-[11px] font-semibold uppercase tracking-[0.08em] text-[#6366f1]">
          Étape {stepLabel}
        </span>
        <div className="bi-sec-line" />
      </div>
      <h2 className="mb-1 text-xl font-bold text-[#111827]">{title}</h2>
      {sub && <p className="m-0 text-[13px] text-[#6b7280]">{sub}</p>}
    </div>
  );
}
