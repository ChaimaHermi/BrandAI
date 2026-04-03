/**
 * Carte numérotée — alignée sur le studio Naming (bi-card, pastille indigo).
 */
export default function SloganSectionCard({ num, title, sub, children }) {
  return (
    <div className="bi-card bi-fade-up mb-2.5">
      <div className="mb-4 flex items-center gap-2.5">
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[#6366f1] text-[11px] font-bold text-white">
          {num}
        </span>
        <div>
          <p className="text-[13px] font-semibold text-[#111827]">{title}</p>
          {sub ? (
            <p className="m-0 text-[11px] text-[#9ca3af]">{sub}</p>
          ) : null}
        </div>
      </div>
      {children}
    </div>
  );
}
