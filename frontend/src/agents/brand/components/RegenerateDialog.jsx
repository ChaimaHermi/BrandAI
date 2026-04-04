import { useEffect } from "react";

/**
 * Popup : remarques + confirmation. En charge : indicateur sur la zone de saisie (pas sur le libellé du bouton principal).
 */
export default function RegenerateDialog({
  open,
  title,
  description,
  placeholder,
  draft,
  onDraftChange,
  confirmLabel = "Générer",
  cancelLabel = "Annuler",
  onCancel,
  onConfirm,
  busy = false,
  busyHint = "Génération en cours…",
}) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => {
      if (e.key === "Escape" && !busy) onCancel?.();
    };
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
      <button
        type="button"
        className="absolute inset-0 bg-[#0f172a]/45 backdrop-blur-[2px]"
        aria-label="Fermer"
        onClick={() => !busy && onCancel?.()}
      />
      <div className="relative z-[1] w-full max-w-[420px] rounded-2xl border border-[#e5e7eb] bg-white p-5 shadow-xl">
        <h2
          id="regen-dialog-title"
          className="mb-1 text-[15px] font-semibold text-[#111827]"
        >
          {title}
        </h2>
        {description ? (
          <p className="mb-3 text-[12px] leading-relaxed text-[#6b7280]">
            {description}
          </p>
        ) : null}
        <label htmlFor="regen-dialog-remarks" className="sr-only">
          Remarques
        </label>
        <div className="relative mb-4">
          <textarea
            id="regen-dialog-remarks"
            className="bi-inp min-h-[100px] w-full resize-y py-2.5 text-[13px] leading-snug disabled:bg-[#f9fafb] disabled:text-[#6b7280]"
            value={draft}
            onChange={(e) => onDraftChange?.(e.target.value)}
            placeholder={placeholder}
            disabled={busy}
            aria-busy={busy}
          />
          {busy ? (
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center gap-2 rounded-[10px] bg-white/85">
              <span
                className="h-8 w-8 shrink-0 animate-spin rounded-full border-2 border-[#e5e7eb] border-t-[#6366f1]"
                aria-hidden
              />
              <span className="text-[12px] font-medium text-[#6366f1]">
                {busyHint}
              </span>
            </div>
          ) : null}
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
