/**
 * SectionLabel
 * Canonical section label used above data fields inside cards.
 * Visually prominent: brand color + left accent bar.
 *
 * Props:
 *   children  — label text
 *   className — extra classes (optional)
 */
export function SectionLabel({ children, className = "" }) {
  return (
    <p
      className={`mb-3 border-l-2 border-brand-muted pl-2 text-xs font-semibold uppercase tracking-[0.08em] text-brand ${className}`}
    >
      {children}
    </p>
  );
}

export default SectionLabel;
