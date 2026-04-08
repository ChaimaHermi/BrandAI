import { useEffect } from "react";

/**
 * Popup régénération — design system brand tokens.
 */
export default function RegenerateDialog({
  open,
  title,
  description,
  placeholder,
  draft,
  onDraftChange,
  confirmLabel = "Générer",
  cancelLabel  = "Annuler",
  onCancel,
  onConfirm,
  busy    = false,
  busyHint = "Génération en cours…",
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => { if (e.key === "Escape" && !busy) onCancel?.(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onCancel, busy]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="regen-dialog-title"
    >
      {/* Backdrop */}
      <button
        type="button"
        className="absolute inset-0 bg-ink/40 backdrop-blur-[2px]"
        aria-label="Fermer"
        onClick={() => !busy && onCancel?.()}
      />

      {/* Dialog card */}
      <div className="relative z-[1] w-full max-w-[420px] rounded-2xl border border-brand-border bg-white p-5 shadow-card-lg">
        <h2
          id="regen-dialog-title"
          className="mb-1 text-sm font-semibold text-ink"
        >
          {title}
        </h2>
        {description && (
          <p className="mb-3 text-xs leading-relaxed text-ink-muted">{description}</p>
        )}

        <label htmlFor="regen-dialog-remarks" className="sr-only">
          Remarques
        </label>
        <div className="relative mb-4">
          <textarea
            id="regen-dialog-remarks"
            className="bi-inp min-h-[100px] w-full resize-y py-2.5 text-sm leading-snug"
            value={draft}
            onChange={(e) => onDraftChange?.(e.target.value)}
            placeholder={placeholder}
            disabled={busy}
            aria-busy={busy}
          />
          {busy && (
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-2 rounded-[10px] bg-white/85">
              <span
                className="h-8 w-8 shrink-0 animate-spin rounded-full border-2 border-brand-border border-t-brand"
                aria-hidden
              />
              <span className="text-xs font-medium text-brand">{busyHint}</span>
            </div>
          )}
        </div>

        <div className="flex flex-wrap justify-end gap-2">
          <button
            type="button"
            className="bi-btn-outline"
            onClick={() => onCancel?.()}
            disabled={busy}
          >
            {cancelLabel}
          </button>
          <button
            type="button"
            className="bi-btn-primary"
            disabled={busy}
            onClick={() => onConfirm?.()}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
