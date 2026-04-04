/**
 * Stepper horizontal (points + connecteurs) — même logique que la maquette indigo.
 */
export default function BrandStepper({ steps, current }) {
  return (
    <div className="mb-8 flex items-center justify-center px-4">
      {steps.map((label, i) => {
        const done = i < current;
        const active = i === current;
        return (
          <div key={label} className="flex items-center">
            <div className="flex flex-col items-center gap-1.5">
              <div
                className={`bi-step-dot ${
                  done ? "done" : active ? "active" : "pending"
                }`}
              >
                {done ? "✓" : i + 1}
              </div>
              <span
                className={`text-[10px] font-semibold uppercase tracking-[0.06em] ${
                  done
                    ? "text-[#22c55e]"
                    : active
                      ? "text-[#6366f1]"
                      : "text-[#9ca3af]"
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
