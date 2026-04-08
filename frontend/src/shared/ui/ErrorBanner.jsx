import React from "react";

/**
 * ErrorBanner
 * Standardized inline error/warning/info message.
 * Replaces all ad-hoc inline error div blocks across modules.
 *
 * Props:
 *   message   — string to display (returns null if falsy)
 *   variant   — "error" | "warning" | "info"  (default: "error")
 *   className — extra classes on the wrapper (optional)
 */

const VARIANT_STYLES = {
  error:   { borderColor: "#fecaca", background: "#fef2f2", color: "#b91c1c" },
  warning: { borderColor: "#fde68a", background: "#fffbeb", color: "#92400e" },
  info:    { borderColor: "#AFA9EC", background: "#f0eeff", color: "#534AB7" },
};

export function ErrorBanner({ message, variant = "error", className = "" }) {
  if (!message) return null;
  const style = VARIANT_STYLES[variant] ?? VARIANT_STYLES.error;
  return (
    <div
      className={`rounded-xl border px-4 py-3 text-[13px] ${className}`}
      style={style}
    >
      {message}
    </div>
  );
}

export default ErrorBanner;
