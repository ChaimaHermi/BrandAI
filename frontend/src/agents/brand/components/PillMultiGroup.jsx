/**
 * Groupe de pills multi-sélection — style « Studio » (indigo / équilibre).
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
      {label ? <p className="bi-lbl">{label}</p> : null}
      {hint && <p className="mb-2 text-[11px] text-[#9ca3af]">{hint}</p>}
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => {
          const active = selected.includes(opt);
          return (
            <button
              key={opt}
              type="button"
              aria-pressed={active}
              onClick={() => toggle(opt)}
              className={`bi-opt-pill rounded-full border px-3 py-1.5 text-[12px] ${
                active
                  ? "border-[#6366f1] bg-[#eef2ff] font-semibold text-[#4f46e5] shadow-[0_1px_4px_rgba(99,102,241,0.15)]"
                  : "border-[#e5e7eb] bg-white font-medium text-[#6b7280] hover:border-[#a5b4fc]"
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
