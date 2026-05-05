import { createPortal } from "react-dom";

function eventLabel(ev) {
  if (!ev || typeof ev !== "object") return "";
  const t = ev.type;
  if (t === "warnings") return `Avertissements : ${(ev.warnings || []).join(" · ")}`;
  if (t === "started") return `Démarrage · ${ev.platforms_total ?? "?"} plateforme(s)`;
  if (t === "platform_start") return `Extraction : ${ev.platform || "?"}`;
  if (t === "platform_done") return `Terminé : ${ev.platform || "?"} (${ev.posts_count ?? "?"} posts)`;
  if (t === "platform_error") return `Erreur ${ev.platform || "?"} : ${ev.error || ""}`;
  if (t === "complete") {
    const failed = Number(ev.platforms_failed || 0);
    const done = Number(ev.platforms_done || 0);
    const total = Number(ev.platforms_total || 0);
    if (failed > 0) return `Pipeline terminé avec erreurs (${done}/${total} réussies)`;
    return "Pipeline terminé avec succès";
  }
  if (t === "fatal") return `Erreur fatale : ${ev.detail || ""}`;
  return "";
}

function StepIcon({ type }) {
  if (type === "platform_done") return <span>✓</span>;
  if (type === "platform_error" || type === "fatal") return <span>✗</span>;
  if (type === "platform_start" || type === "started") {
    return (
      <span className="inline-flex gap-[2px]">
        <span className="animate-[pulse_1s_0ms_infinite]">·</span>
        <span className="animate-[pulse_1s_180ms_infinite]">·</span>
        <span className="animate-[pulse_1s_360ms_infinite]">·</span>
      </span>
    );
  }
  return <span>→</span>;
}

function CompleteIcon({ hasFailure }) {
  return <span>{hasFailure ? "✗" : "✓"}</span>;
}

export default function OptimizerSyncModal({ open, events, isLoading, onClose }) {
  if (!open) return null;

  const hasError = events.some((e) => e?.type === "fatal" || e?.type === "platform_error");
  const isDone = !isLoading && events.some((e) => e?.type === "complete");
  const completeEvent = [...events].reverse().find((e) => e?.type === "complete");
  const completeHasFailure = Number(completeEvent?.platforms_failed || 0) > 0;

  const title = hasError ? "Synchronisation échouée" : isDone ? "Synchronisation terminée" : "Synchronisation en cours";

  const modal = (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4" role="dialog" aria-modal="true">
      <div className="absolute inset-0 bg-black/50 backdrop-blur-md" />
      <div className="relative z-10 w-full max-w-md overflow-hidden rounded-3xl bg-white shadow-2xl animate-[slideUp_0.3s_ease_forwards]">
        <div className={`px-6 py-5 ${hasError ? "bg-gradient-to-br from-red-500 to-red-700" : "bg-gradient-to-br from-brand to-brand-dark"}`}>
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-sm font-extrabold text-white">Social ETL Optimizer</p>
              <p className="mt-0.5 text-xs text-white/80">{title}</p>
            </div>
            <div className="rounded-full bg-white/20 px-2.5 py-1 text-xs font-bold text-white">
              {events.length} étape{events.length > 1 ? "s" : ""}
            </div>
          </div>
        </div>

        <div className="max-h-[320px] overflow-y-auto px-4 py-3">
          {events.length === 0 ? (
            <p className="text-xs text-ink-subtle">Initialisation…</p>
          ) : (
            <div className="flex flex-col gap-2">
              {events.map((ev, i) => (
                <div key={`${ev.type}-${i}`} className="flex items-start gap-2 rounded-lg px-2 py-1.5">
                  <span className={`mt-[1px] w-[14px] text-[11px] ${
                    ev.type === "fatal" || ev.type === "platform_error"
                      ? "text-red-600"
                      : ev.type === "complete"
                        ? completeHasFailure
                          ? "text-red-600"
                          : "text-success"
                        : ev.type === "platform_done"
                          ? "text-success"
                          : "text-brand"
                  }`}>
                    {ev.type === "complete" ? (
                      <CompleteIcon hasFailure={completeHasFailure} />
                    ) : (
                      <StepIcon type={ev.type} />
                    )}
                  </span>
                  <p className="break-words text-xs text-ink">{eventLabel(ev)}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="border-t border-brand-border px-4 py-3">
          {isLoading ? (
            <p className="text-center text-[11px] text-ink-subtle">Synchronisation en cours…</p>
          ) : (
            <div className="flex justify-end">
              <button
                type="button"
                onClick={onClose}
                className="rounded-full bg-brand px-4 py-1.5 text-xs font-bold text-white hover:bg-brand-dark"
              >
                Fermer
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return createPortal(modal, document.body);
}
