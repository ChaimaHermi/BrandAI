/**
 * Stepper horizontal (points + connecteurs) — design system brand tokens.
 */
export default function BrandStepper({ steps, current }) {
  return (
    <div className="mb-8 flex items-center justify-center px-4">
      {steps.map((label, i) => {
        const done   = i < current;
        const active = i === current;
        return (
          <div key={label} className="flex items-center">
            <div className="flex flex-col items-center gap-1.5">
              <div className={`bi-step-dot ${done ? "done" : active ? "active" : "pending"}`}>
                {done ? "✓" : i + 1}
              </div>
              <span
                className={`text-2xs font-semibold uppercase tracking-[0.06em] ${
                  done   ? "text-success"
                  : active ? "text-brand"
                           : "text-ink-subtle"
                }`}
              >
                {label}
              </span>
            </div>
            {i < steps.length - 1 && (
              <div className={`bi-connector ${done ? "done" : ""}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
