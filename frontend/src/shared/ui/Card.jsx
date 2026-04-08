import React from "react";

/**
 * Card — the canonical content container for BrandAI.
 *
 * Design system values:
 *   border  : brand-border (#e8e4ff) — violet-tinted, NOT gray
 *   shadow  : shadow-card (rgba(124,58,237,0.06))
 *   radius  : rounded-xl (14px)
 *
 * Variants:
 *   default  — white card, brand border + soft shadow
 *   flat     — white card, brand border, no shadow (for nested cards)
 *   ghost    — no border, no shadow, transparent bg
 *
 * Props:
 *   variant  — "default" | "flat" | "ghost"
 *   hover    — adds hover lift animation (default: false)
 *   padding  — tailwind padding class override (default: "p-5")
 *   className — extra classes
 */
export function Card({
  children,
  variant = "default",
  hover = false,
  padding = "p-5",
  className = "",
  ...rest
}) {
  const base = "rounded-xl bg-white transition-all duration-200";

  const variants = {
    default: "border border-brand-border shadow-card",
    flat:    "border border-brand-border",
    ghost:   "bg-transparent",
  };

  const hoverClass = hover
    ? "hover:shadow-card-md hover:-translate-y-px hover:border-brand-muted cursor-pointer"
    : "";

  return (
    <div
      className={`${base} ${variants[variant]} ${padding} ${hoverClass} ${className}`}
      {...rest}
    >
      {children}
    </div>
  );
}

export default Card;
