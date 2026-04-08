/**
 * Groupe de pills multi-sélection — design system brand tokens.
 */
export default function PillMultiGroup({ label, options, selected, onChange, hint }) {
  const toggle = (value) => {
    const next = selected.includes(value)
      ? selected.filter((v) => v !== value)
      : [...selected, value];
    onChange(next);
  };

  return (
    <div className="mb-4 last:mb-0">
      {label && <p className="bi-lbl">{label}</p>}
      {hint  && <p className="mb-2 text-xs text-ink-subtle">{hint}</p>}
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => {
          const active = selected.includes(opt);
          return (
            <button
              key={opt}
              type="button"
              aria-pressed={active}
              onClick={() => toggle(opt)}
              className={`bi-opt-pill rounded-full border px-3 py-1.5 text-xs ${
                active
                  ? "border-brand bg-brand-light font-semibold text-brand-darker shadow-[0_1px_4px_rgba(124,58,237,0.15)]"
                  : "border-brand-border bg-white font-medium text-ink-muted hover:border-brand-muted hover:bg-brand-light hover:text-brand-dark"
              }`}
            >
              {opt}
            </button>
          );
        })}
      </div>
    </div>
  );
}
