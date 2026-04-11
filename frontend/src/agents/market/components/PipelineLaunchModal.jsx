/**
 * PipelineLaunchModal
 * Full-screen overlay with backdrop blur showing real-time SSE pipeline progress.
 * Appears when the user launches the market analysis pipeline.
 */
import { useMemo } from "react";
import { createPortal } from "react-dom";

/* ── Pipeline stages definition (order matters) ─────────────────────────── */
const PIPELINE_STAGES = [
  { id: "keyword_extractor",       label: "Extraction des mots-clés",    desc: "Analyse sémantique de l'idée" },
  { id: "market_sizing",           label: "Dimensionnement du marché",   desc: "Taille, CAGR et revenus estimés" },
  { id: "competitor",              label: "Analyse des concurrents",     desc: "Forces, faiblesses, positionnement" },
  { id: "voc",                     label: "Voice of Customer",           desc: "Pain points et attentes utilisateurs" },
  { id: "trends_risks",            label: "Tendances & Risques",         desc: "Signaux marché et menaces identifiées" },
  { id: "strategy_analysis_agent", label: "Stratégie SWOT / PESTEL",    desc: "Analyse stratégique complète" },
  { id: "save_results",            label: "Finalisation du rapport",     desc: "Compilation et structuration des données" },
  { id: "persist_result",          label: "Sauvegarde du résultat",      desc: "Enregistrement en base de données" },
];

/* ── Icons ───────────────────────────────────────────────────────────────── */
function SpinnerIcon({ white = false }) {
  return (
    <svg
      width="14" height="14" viewBox="0 0 14 14" fill="none"
      className="animate-spin"
      style={{ animationDuration: "0.9s" }}
    >
      <circle cx="7" cy="7" r="5.5" stroke={white ? "rgba(255,255,255,0.3)"  : "#e8e4ff"} strokeWidth="1.5" />
      <path
        d="M7 1.5A5.5 5.5 0 0 1 12.5 7"
        stroke={white ? "white" : "#7C3AED"}
        strokeWidth="1.5"
        strokeLinecap="round"
      />
    </svg>
  );
}

function CheckIcon({ white = false, size = 12 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 12 12" fill="none">
      <path
        d="M1.5 6l3 3 6-6"
        stroke={white ? "white" : "currentColor"}
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function ErrorIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <circle cx="7" cy="7" r="5.5" stroke="white" strokeWidth="1.4" />
      <path d="M7 4v3.5M7 9.5v.5" stroke="white" strokeWidth="1.4" strokeLinecap="round" />
    </svg>
  );
}

/* ── Component ───────────────────────────────────────────────────────────── */
export default function PipelineLaunchModal({ isOpen, isLoading, isDone, xaiSteps, error, onClose }) {
  /* Build a map: stageId → { status, message } using latest step per stage */
  const stageMap = useMemo(() => {
    const map = {};
    xaiSteps.forEach((step) => {
      if (!step.stage) return;
      const existing = map[step.stage];
      // Prefer "done" status; otherwise always take the latest
      if (!existing || existing.status !== "done") {
        map[step.stage] = { status: step.status, message: step.message };
      }
    });
    return map;
  }, [xaiSteps]);

  /* Active stage = most recent non-done stage in the step stream */
  const activeStageId = useMemo(() => {
    for (let i = xaiSteps.length - 1; i >= 0; i--) {
      const s = xaiSteps[i];
      if (s.stage && s.status !== "done") return s.stage;
    }
    return null;
  }, [xaiSteps]);

  const doneCount = PIPELINE_STAGES.filter((s) => stageMap[s.id]?.status === "done").length;
  const progressPct = isDone ? 100 : Math.round((doneCount / PIPELINE_STAGES.length) * 100);

  if (!isOpen) return null;

  const headerState = error ? "error" : isDone ? "done" : "loading";

  const modal = (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-md" />

      {/* Card */}
      <div className="relative z-10 w-full max-w-md overflow-hidden rounded-3xl bg-white shadow-2xl animate-[slideUp_0.3s_ease_forwards]">

        {/* ── Header ─────────────────────────────────────────────────────── */}
        <div
          className={`px-6 py-5 ${
            headerState === "error"
              ? "bg-gradient-to-br from-red-500 to-red-700"
              : headerState === "done"
                ? "bg-gradient-to-br from-success to-success-dark"
                : "bg-gradient-to-br from-brand to-brand-dark"
          }`}
        >
          <div className="mb-4 flex items-center gap-3">
            {/* Status icon bubble */}
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-white/20">
              {headerState === "error" ? (
                <ErrorIcon />
              ) : headerState === "done" ? (
                <CheckIcon white size={16} />
              ) : (
                <SpinnerIcon white />
              )}
            </div>

            {/* Title + subtitle */}
            <div className="min-w-0 flex-1">
              <p className="text-sm font-extrabold text-white">
                Pipeline d'analyse de marché
              </p>
              <p className="mt-0.5 text-xs text-white/70">
                {headerState === "error"
                  ? "Une erreur est survenue"
                  : headerState === "done"
                    ? "Analyse terminée avec succès"
                    : "Analyse en cours…"}
              </p>
            </div>

            {/* Step counter badge */}
            <div className="shrink-0 rounded-full bg-white/20 px-2.5 py-1 text-xs font-bold text-white">
              {doneCount} / {PIPELINE_STAGES.length}
            </div>
          </div>

          {/* Progress bar */}
          <div className="h-1.5 overflow-hidden rounded-full bg-white/20">
            <div
              className="h-full rounded-full bg-white transition-[width] duration-700 ease-out"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>

        {/* ── Stages list ─────────────────────────────────────────────────── */}
        <div className="max-h-[360px] overflow-y-auto px-3 py-2">
          {PIPELINE_STAGES.map((stage, idx) => {
            const state      = stageMap[stage.id];
            const isDoneStage   = state?.status === "done";
            const isActiveStage = !isDoneStage && activeStageId === stage.id;
            const hasStarted    = !!state;
            const liveMessage   = state?.message;

            return (
              <div
                key={stage.id}
                className={`flex items-center gap-3 rounded-xl px-3 py-2.5 transition-all duration-300 ${
                  isActiveStage ? "bg-brand-light" : ""
                }`}
              >
                {/* ── Status badge ────────────────────────────────────────── */}
                <div
                  className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-[10px] font-bold transition-all duration-300 ${
                    isDoneStage
                      ? "bg-success text-white"
                      : isActiveStage
                        ? "bg-gradient-to-br from-brand to-brand-dark text-white shadow-pill"
                        : hasStarted
                          ? "border border-brand-muted bg-brand-light text-brand"
                          : "border border-gray-200 bg-gray-50 text-ink-subtle"
                  }`}
                >
                  {isDoneStage ? (
                    <CheckIcon />
                  ) : isActiveStage ? (
                    <SpinnerIcon />
                  ) : (
                    <span>{idx + 1}</span>
                  )}
                </div>

                {/* ── Label + live message ─────────────────────────────────── */}
                <div className="min-w-0 flex-1">
                  <p
                    className={`truncate text-xs font-bold ${
                      isDoneStage
                        ? "text-success"
                        : isActiveStage
                          ? "text-brand-darker"
                          : hasStarted
                            ? "text-ink"
                            : "text-ink-subtle"
                    }`}
                  >
                    {stage.label}
                  </p>
                  <p className="mt-0.5 truncate text-[10px] text-ink-subtle">
                    {liveMessage || stage.desc}
                  </p>
                </div>

                {/* ── Right indicator ──────────────────────────────────────── */}
                {isDoneStage && (
                  <div className="shrink-0 text-success">
                    <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                      <path d="M2 6.5l3 3 6-6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                    </svg>
                  </div>
                )}
                {isActiveStage && (
                  <div className="flex shrink-0 gap-[3px]">
                    {[0, 120, 240].map((delay) => (
                      <div
                        key={delay}
                        className="h-[5px] w-[5px] rounded-full bg-brand"
                        style={{ animation: `pulse-dot 1.2s ease-in-out infinite ${delay}ms` }}
                      />
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* ── Footer (done or error) ───────────────────────────────────────── */}
        {(isDone || error) && (
          <div
            className={`border-t px-5 py-4 ${
              isDone ? "border-success/20 bg-success/5" : "border-red-100 bg-red-50"
            }`}
          >
            <div className="flex items-center justify-between gap-3">
              <p className={`text-xs font-bold ${isDone ? "text-success" : "text-red-600"}`}>
                {isDone
                  ? "Rapport prêt — les résultats sont disponibles"
                  : error}
              </p>
              <button
                onClick={onClose}
                className={`shrink-0 rounded-full px-4 py-1.5 text-xs font-bold text-white transition-all hover:-translate-y-px ${
                  isDone
                    ? "bg-success hover:opacity-90"
                    : "bg-red-500 hover:bg-red-600"
                }`}
              >
                {isDone ? "Voir le rapport" : "Fermer"}
              </button>
            </div>
          </div>
        )}

        {/* ── Footer (loading — no close) ──────────────────────────────────── */}
        {!isDone && !error && (
          <div className="border-t border-brand-border px-5 py-3">
            <p className="text-center text-[10px] text-ink-subtle">
              L'analyse peut prendre quelques minutes — ne fermez pas cette fenêtre
            </p>
          </div>
        )}
      </div>
    </div>
  );

  return createPortal(modal, document.body);
}
