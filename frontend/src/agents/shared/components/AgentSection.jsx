import { SectionLabel } from "@/shared/ui/SectionLabel";

/**
 * AgentSection
 * A labeled content card — the primary data display unit in Market and Marketing modules.
 *
 * Props:
 *   label     — Uppercase section label text (optional)
 *   children  — Content below the label
 *   colSpan   — Number for md:col-span-{n} inside a CSS grid (optional)
 *   className — Extra classes on the wrapper (optional)
 */
export function AgentSection({ label, children, colSpan, className = "" }) {
  const spanClass = colSpan ? `md:col-span-${colSpan}` : "";
  return (
    <div className={`rounded-xl border border-brand-border bg-white p-5 ${spanClass} ${className}`}>
      {label && <SectionLabel>{label}</SectionLabel>}
      {children}
    </div>
  );
}

export default AgentSection;
