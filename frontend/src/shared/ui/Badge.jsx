import React from "react";

/**
 * Badge — pill-shaped label for statuses, sectors, tags.
 *
 * Variants:
 *   brand   — violet (default)
 *   success — green
 *   warning — amber
 *   neutral — gray
 *   outline — white + brand border
 *
 * Legacy aliases (backward-compatible):
 *   violet  → brand
 *   waiting → warning
 *   danger  → uses red-100/red-600
 */
export function Badge({
  children,
  variant   = "brand",
  className = "",
  ...rest
}) {
  const base = "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-semibold";

  const variants = {
    brand:   "bg-brand-light text-brand-darker",
    violet:  "bg-brand-light text-brand-darker",   // legacy alias
    success: "bg-success-light text-success-dark",
    warning: "bg-amber-100 text-amber-700",
    waiting: "bg-amber-100 text-amber-700",         // legacy alias
    neutral: "bg-gray-100 text-gray-600",
    outline: "border border-brand-border bg-white text-brand-darker",
    danger:  "bg-red-100 text-red-600",
  };

  return (
    <span
      className={`${base} ${variants[variant] ?? variants.brand} ${className}`}
      {...rest}
    >
      {children}
    </span>
  );
}

export default Badge;
