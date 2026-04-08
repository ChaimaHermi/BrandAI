/**
 * Pills à choix unique — design system brand tokens.
 */
export default function PillSingleGroup({
  label,
  options,
  value,
  onChange,
  idKey    = "id",
  labelKey = "label",
}) {
  return (
    <div className={label ? "mb-4 last:mb-0" : "mb-0"}>
      {label && (
        <p className="mb-2 text-xs font-semibold text-ink">{label}</p>
      )}
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => {
          const id     = typeof opt === "string" ? opt : opt[idKey];
          const lbl    = typeof opt === "string" ? opt : opt[labelKey];
          const active = value === id;
          return (
            <button
              key={id}
              type="button"
              aria-pressed={active}
              onClick={() => onChange(id)}
              className={`bi-opt-pill rounded-full border px-3 py-1.5 text-xs ${
                active
                  ? "border-brand bg-brand-light font-semibold text-brand-darker shadow-[0_1px_4px_rgba(124,58,237,0.15)]"
                  : "border-brand-border bg-white font-medium text-ink-muted hover:border-brand-muted hover:bg-brand-light hover:text-brand-dark"
              }`}
            >
              {lbl}
            </button>
          );
        })}
      </div>
    </div>
  );
}
