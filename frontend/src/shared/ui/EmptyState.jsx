import React from "react";

/**
 * EmptyState
 * Standardized empty state shown when a module has no data yet.
 *
 * Props:
 *   icon        — React node displayed inside a circle (optional)
 *   title       — Bold title text
 *   description — Muted description below the title (optional)
 *   action      — React node for a CTA button (optional)
 *   className   — Extra classes on the wrapper (optional)
 */
export function EmptyState({ icon, title, description, action, className = "" }) {
  return (
    <div
      className={`flex flex-col items-center justify-center rounded-2xl border border-[#e8e4ff] bg-white px-6 py-12 text-center ${className}`}
    >
      {icon && (
        <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-[#f0eeff]">
          {icon}
        </div>
      )}
      {title && (
        <p className="mb-1 text-[14px] font-bold text-[#1a1040]">{title}</p>
      )}
      {description && (
        <p className="mb-5 text-[12px] text-gray-400">{description}</p>
      )}
      {action}
    </div>
  );
}

export default EmptyState;
