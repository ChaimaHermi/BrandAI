import React from "react";

/**
 * Button — the canonical interactive element for BrandAI.
 *
 * Variants:
 *   primary   — gradient brand button (main CTAs)
 *   secondary — outlined brand button (secondary actions)
 *   ghost     — text-only button (tertiary, nav)
 *   danger    — red outlined (delete/destructive)
 *   success   — green outlined (done states)
 *
 * Sizes:
 *   sm   — compact (11px text, px-3 py-1.5)
 *   md   — default (12px text, px-4 py-2)
 *   lg   — prominent (13px text, px-5 py-2.5)
 *
 * Shape:
 *   rounded   — rounded-full (default, pill shape)
 *   square    — rounded-xl
 */
export function Button({
  children,
  variant  = "primary",
  size     = "md",
  shape    = "rounded",
  type     = "button",
  disabled = false,
  fullWidth = false,
  className = "",
  onClick,
  ...rest
}) {
  // ── Base ──────────────────────────────────────────────────────────────────
  const base =
    "inline-flex items-center justify-center gap-1.5 font-semibold " +
    "transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed " +
    "focus:outline-none focus-visible:ring-2 focus-visible:ring-brand/50 ";

  // ── Shape ─────────────────────────────────────────────────────────────────
  const shapes = {
    rounded: "rounded-full",
    square:  "rounded-xl",
  };

  // ── Sizes ─────────────────────────────────────────────────────────────────
  const sizes = {
    sm: "text-xs   px-3    py-1.5",
    md: "text-sm   px-4    py-2",
    lg: "text-base px-5    py-2.5",
  };

  // ── Variants ──────────────────────────────────────────────────────────────
  const variants = {
    primary:
      "bg-gradient-to-br from-brand to-brand-dark text-white shadow-btn " +
      "hover:shadow-btn-hover hover:-translate-y-px active:translate-y-0",

    secondary:
      "border border-brand-border bg-white text-brand-darker " +
      "hover:border-brand-muted hover:bg-brand-light",

    ghost:
      "bg-transparent text-ink-muted " +
      "hover:text-brand hover:bg-brand-light",

    danger:
      "border border-red-200 bg-white text-red-600 " +
      "hover:bg-red-50 hover:border-red-300",

    success:
      "border border-success-border bg-white text-success " +
      "hover:bg-success-light",
  };

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={[
        base,
        shapes[shape],
        sizes[size],
        variants[variant],
        fullWidth ? "w-full" : "",
        className,
      ]
        .filter(Boolean)
        .join(" ")}
      {...rest}
    >
      {children}
    </button>
  );
}

export default Button;
