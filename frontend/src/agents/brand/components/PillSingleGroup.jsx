/**
 * Pills à choix unique — aligné palette indigo.
 */
export default function PillSingleGroup({
  label,
  options,
  value,
  onChange,
  idKey = "id",
  labelKey = "label",
}) {
  return (
    <div className={label ? "mb-4 last:mb-0" : "mb-0"}>
      {label ? (
        <p className="mb-2 text-[12px] font-semibold text-[#111827]">{label}</p>
      ) : null}
      <div className="flex flex-wrap gap-2">
        {options.map((opt) => {
          const id = typeof opt === "string" ? opt : opt[idKey];
          const lbl = typeof opt === "string" ? opt : opt[labelKey];
          const active = value === id;
          return (
            <button
              key={id}
              type="button"
              aria-pressed={active}
              onClick={() => onChange(id)}
              className={`bi-opt-pill rounded-full border px-3 py-1.5 text-[12px] ${
                active
                  ? "border-[#6366f1] bg-[#eef2ff] font-semibold text-[#4f46e5]"
                  : "border-[#e5e7eb] bg-white font-medium text-[#6b7280] hover:border-[#a5b4fc]"
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
