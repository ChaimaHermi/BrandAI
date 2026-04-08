/**
 * PipelineSidebar — collapsible left sidebar with agent list, progress, and CTA.
 * Purely presentational. Zero inline styles except dynamic agent.doneBg/doneBorder/doneColor
 * (runtime values from AGENTS registry — not expressible as static Tailwind).
 */
import { AGENTS } from "@/agents";
import { CLARITY_SCORE_MIN_PIPELINE } from "@/agents/clarifier/constants";

/* ── Lock icon (pipeline CTA) ────────────────────────────────────────────── */
function LockIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <rect x="2" y="5" width="8" height="6" rx="1" stroke="currentColor" strokeWidth="1.2" />
      <path d="M4 5V3.5a2 2 0 014 0V5" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" />
    </svg>
  );
}

/* ── Arrow icon (pipeline CTA) ───────────────────────────────────────────── */
function ArrowIcon() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
      <path d="M2 6h8M7 3l3 3-3 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ── Checkmark icon (agent done) ─────────────────────────────────────────── */
function CheckIcon() {
  return (
    <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
      <path d="M1.5 6l3 3 6-6" stroke="white" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* ── Component ───────────────────────────────────────────────────────────── */
export default function PipelineSidebar({
  ideaTitle,
  activeAgent,
  activeIndex,
  progressPct,
  sidebarOpen,
  getStatus,
  pipelineEnabled,
  pipelineCompleted,
  idea,
  onNavigateDashboard,
  onNavigateAgent,
  onLaunchPipeline,
}) {
  return (
    <div
      className={`app-sidebar flex shrink-0 flex-col overflow-hidden border-r border-brand-light bg-white transition-[width,min-width] duration-200 ease-in-out ${
        sidebarOpen ? "shadow-sidebar" : "is-collapsed shadow-none"
      }`}
    >
      {/* ── Header: back + title + progress ───────────────────────────────── */}
      <div
        className={`min-w-0 border-b border-brand-light px-3.5 pb-2.5 pt-3.5 ${
          sidebarOpen ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
      >
        {/* Back button */}
        <button
          onClick={onNavigateDashboard}
          className="mb-3 flex cursor-pointer items-center gap-1.5 whitespace-nowrap border-0 bg-transparent p-0 text-xs font-medium text-ink-subtle transition-colors hover:text-brand"
        >
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
            <path
              d="M9 2L4 7l5 5"
              stroke="currentColor"
              strokeWidth="1.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Retour
        </button>

        {/* Idea title */}
        <p className="mb-0.5 truncate text-sm font-bold text-ink">{ideaTitle}…</p>

        {/* Step info */}
        <p className="mb-2.5 text-xs text-ink-subtle">
          Étape {activeIndex + 1} · {activeAgent.label}
        </p>

        {/* Progress bar */}
        <div className="h-[5px] overflow-hidden rounded-full bg-brand-light">
          <div
            className="h-full rounded-full bg-gradient-to-r from-brand to-brand-dark transition-[width] duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* ── Agent list ────────────────────────────────────────────────────── */}
      <div className="flex min-w-0 flex-1 flex-col gap-[3px] overflow-y-auto p-2">
        {AGENTS.map((agent) => {
          const status  = getStatus(agent.id);
          const isActive  = agent.id === activeAgent.id;
          const isDone    = status === "done";
          const isPending = status === "pending";

          return (
            <div
              key={agent.id}
              onClick={() => onNavigateAgent(agent.id)}
              title={!sidebarOpen ? agent.label : undefined}
              className={`flex cursor-pointer items-center rounded-[10px] transition-all duration-150 ${
                sidebarOpen
                  ? `gap-2.5 px-2.5 py-[9px] ${
                      isDone
                        ? "border"
                        : isActive
                          ? "border border-brand-muted bg-gradient-to-br from-brand-light to-brand-50"
                          : "border border-transparent bg-transparent"
                    }`
                  : "justify-center py-1.5"
              } ${isPending ? "opacity-45" : "opacity-100"}`}
              /* dynamic done bg/border from AGENTS registry — not static Tailwind */
              style={sidebarOpen && isDone ? { background: agent.doneBg, borderColor: agent.doneBorder } : undefined}
            >
              {/* Icon bubble */}
              <div
                className={`flex shrink-0 items-center justify-center rounded-full transition-all duration-150 ${
                  sidebarOpen ? "h-7 w-7" : "h-8 w-8"
                } ${isPending ? "border border-gray-200 bg-gray-50" : "border-0"}`}
                style={
                  isDone
                    ? { background: "#1D9E75" }
                    : isActive
                      ? { background: agent.gradient, boxShadow: `0 2px 8px ${agent.color}44` }
                      : { background: "#f5f5f5" }
                }
              >
                {agent.icon ? (
                  <agent.icon
                    size={sidebarOpen ? (isDone || isActive ? 14 : 13) : 15}
                    className={isDone || isActive ? "text-white" : "text-ink-subtle"}
                  />
                ) : (
                  <span className={`text-[9px] font-bold ${isDone || isActive ? "text-white" : "text-ink-subtle"}`}>
                    {agent.short}
                  </span>
                )}
              </div>

              {/* Label + status text */}
              <div className={`min-w-0 flex-1 ${sidebarOpen ? "block" : "hidden"}`}>
                <p
                  className={`truncate text-xs ${isDone || isActive ? "font-bold" : "font-medium"} ${
                    isActive ? "text-brand-darker" : "text-ink-muted"
                  }`}
                  /* dynamic done color from AGENTS registry */
                  style={isDone ? { color: agent.doneColor } : undefined}
                >
                  {agent.label}
                </p>
                <p
                  className={`mt-0.5 flex items-center gap-[3px] text-[9px] ${
                    isDone ? "text-success" : isActive ? "text-brand" : "text-ink-subtle"
                  }`}
                >
                  {isActive && (
                    <span className="inline-block animate-[pulse_1.2s_infinite]">●</span>
                  )}
                  {isDone ? "Terminé ✓" : isActive ? "En cours" : "En attente"}
                </p>
              </div>
            </div>
          );
        })}
      </div>

      {/* ── Pipeline CTA ──────────────────────────────────────────────────── */}
      <div
        className={`min-w-0 border-t border-brand-light p-3 ${
          sidebarOpen ? "opacity-100" : "pointer-events-none opacity-0"
        }`}
      >
        <button
          onClick={onLaunchPipeline}
          disabled={!pipelineEnabled || pipelineCompleted}
          className={`flex w-full items-center justify-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-2.5 text-xs font-bold transition-all duration-200 ${
            pipelineEnabled && !pipelineCompleted
              ? "cursor-pointer bg-gradient-to-br from-brand to-brand-dark text-white shadow-btn hover:shadow-btn-hover hover:-translate-y-px"
              : "cursor-not-allowed border border-brand-border bg-brand-light text-brand-muted opacity-60"
          }`}
        >
          {pipelineEnabled && !pipelineCompleted ? <ArrowIcon /> : <LockIcon />}
          {pipelineCompleted
            ? "Pipeline terminé"
            : pipelineEnabled
              ? "Lancer le pipeline"
              : "Pipeline verrouillé"}
        </button>

        <p className="mt-1.5 text-center text-[10px] text-brand-muted">
          {pipelineCompleted
            ? "Résultat disponible depuis le backend"
            : idea?.clarity_status === "refused"
              ? "Idée refusée — non conforme"
              : idea?.clarity_status === "clarified" &&
                  (idea?.clarity_score ?? 0) < CLARITY_SCORE_MIN_PIPELINE
                ? `Score insuffisant (${idea.clarity_score}/100 < ${CLARITY_SCORE_MIN_PIPELINE})`
                : idea?.clarity_status === "questions"
                  ? "Répondez aux questions d'abord"
                  : "Disponible après clarification"}
        </p>
      </div>
    </div>
  );
}
