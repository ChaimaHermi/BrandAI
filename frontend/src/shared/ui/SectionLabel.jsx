import React from "react";

/**
 * SectionLabel
 * The canonical "uppercase tracking" label used above data fields.
 * Replaces the 30+ inline copies of:
 *   <p className="text-[10px] font-semibold uppercase tracking-[0.08em] text-gray-400">
 *
 * Props:
 *   children  — label text
 *   className — extra classes (optional)
 */
export function SectionLabel({ children, className = "" }) {
  return (
    <p
      className={`mb-2 text-[10px] font-semibold uppercase tracking-[0.08em] text-gray-400 ${className}`}
    >
      {children}
    </p>
  );
}

export default SectionLabel;
