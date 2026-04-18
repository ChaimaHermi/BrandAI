/** Classes alignées sur le design system BrandAI (inputs) */
export const inputClass =
  "w-full rounded-xl border border-brand-border bg-white px-3 py-2 text-sm text-ink placeholder:text-ink-subtle " +
  "focus:border-brand focus:outline-none focus:ring-2 focus:ring-brand/20 transition-all";

export const labelClass = "mb-1.5 block text-xs font-semibold text-ink";

export function FieldLabel({ htmlFor, children }) {
  return (
    <label htmlFor={htmlFor} className={labelClass}>
      {children}
    </label>
  );
}

export function ToggleRow({ id, label, checked, onChange, description }) {
  return (
    <div className="flex items-start justify-between gap-3 rounded-xl border border-brand-border bg-brand-light/30 px-3 py-2.5">
      <div>
        <p className="text-xs font-semibold text-ink">{label}</p>
        {description && <p className="mt-0.5 text-[11px] text-ink-subtle">{description}</p>}
      </div>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        id={id}
        onClick={() => onChange(!checked)}
        className={`relative h-6 w-11 shrink-0 rounded-full transition-colors ${
          checked ? "bg-brand" : "bg-ink-subtle/25"
        }`}
      >
        <span
          className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
            checked ? "translate-x-5" : "translate-x-0"
          }`}
        />
      </button>
    </div>
  );
}
