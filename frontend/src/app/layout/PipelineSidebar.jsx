/**
 * PipelineSidebar
 * Extracted from PipelineLayout — the collapsible left sidebar with:
 *   - Back button + idea title + step info + progress bar
 *   - Agent list (done / active / pending states)
 *   - Pipeline CTA button ("Lancer" / "Terminé" / "Verrouillé")
 *
 * Props:
 *   ideaTitle         — truncated idea description string
 *   activeAgent       — agent object { id, label, short, gradient, color, doneBg, doneBorder, doneColor }
 *   activeIndex       — 0-based index in AGENTS array
 *   progressPct       — 0–100 number
 *   sidebarOpen       — boolean
 *   getStatus         — (agentId: string) => "done" | "active" | "pending"
 *   pipelineEnabled   — boolean
 *   pipelineCompleted — boolean
 *   idea              — the idea object (for building navigate state)
 *   ideaId            — string (route :id param)
 *   onNavigateDashboard — () => void
 *   onNavigateAgent   — (agentId: string) => void
 *   onLaunchPipeline  — () => void
 *   clarityScoreMin   — number (for locked hint text)
 */
import { AGENTS } from "@/agents";
import { CLARITY_SCORE_MIN_PIPELINE } from "@/agents/clarifier/constants";

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
      className={`app-sidebar flex shrink-0 flex-col overflow-hidden border-r border-[#f0eeff] bg-white transition-[width,min-width] duration-200 ease-in-out ${
        sidebarOpen
          ? "shadow-[2px_0_16px_rgba(124,58,237,0.06)]"
          : "is-collapsed shadow-none"
      }`}
    >
      {/* Header: back + title + progress */}
      <div
        className={`min-w-0 border-b border-[#f0eeff] px-[14px] pb-[10px] pt-[14px] ${
          sidebarOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
      >
        <button
          onClick={onNavigateDashboard}
          className="mb-3 flex cursor-pointer items-center gap-[5px] whitespace-nowrap border-0 bg-transparent p-0 font-[var(--font-sans)] text-xs font-medium text-gray-400"
        >
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
            <path
              d="M9 2L4 7l5 5"
              stroke="#9ca3af"
              strokeWidth="1.4"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          Retour
        </button>

        <div className="mb-0.5 overflow-hidden text-ellipsis whitespace-nowrap text-[13px] font-bold text-[#1a1040]">
          {ideaTitle}…
        </div>
        <div className="mb-[10px] text-[11px] text-gray-400">
          Étape {activeIndex + 1} · {activeAgent.label}
        </div>

        <div className="h-[5px] overflow-hidden rounded-full bg-[#f0eeff]">
          <div
            style={{
              height: "100%",
              width: progressPct + "%",
              transition: "width 0.5s ease",
            }}
            className="rounded-full bg-gradient-to-r from-[#7F77DD] to-[#534AB7]"
          />
        </div>
      </div>

      {/* Agent list */}
      <div className="flex min-w-0 flex-1 flex-col gap-[3px] overflow-y-auto p-2">
        {AGENTS.map((agent) => {
          const status = getStatus(agent.id);
          const isActive = agent.id === activeAgent.id;
          const isDone = status === "done";
          const isPending = status === "pending";

          return (
            <div
              key={agent.id}
              onClick={() => onNavigateAgent(agent.id)}
              className={`flex cursor-pointer items-center gap-[10px] rounded-[10px] px-[10px] py-[9px] transition-all duration-150 ${
                isDone
                  ? "border"
                  : isActive
                    ? "border border-[#AFA9EC] bg-gradient-to-br from-[#f0eeff] to-[#fafafe]"
                    : "border border-transparent bg-transparent"
              } ${isPending ? "opacity-45" : "opacity-100"}`}
              style={
                isDone
                  ? { background: agent.doneBg, borderColor: agent.doneBorder }
                  : undefined
              }
            >
              {/* Icon */}
              <div
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full transition-all duration-150 ${
                  isPending ? "border border-[#e5e7eb]" : "border-0"
                }`}
                style={{
                  background: isDone
                    ? "#1D9E75"
                    : isActive
                      ? agent.gradient
                      : "#f5f5f5",
                  boxShadow: isActive ? `0 2px 8px ${agent.color}44` : "none",
                }}
              >
                {isDone ? (
                  <svg width="11" height="11" viewBox="0 0 12 12" fill="none">
                    <path
                      d="M1.5 6l3 3 6-6"
                      stroke="white"
                      strokeWidth="1.6"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                ) : (
                  <span
                    className={`text-[9px] font-bold ${isActive ? "text-white" : "text-gray-400"}`}
                  >
                    {agent.short}
                  </span>
                )}
              </div>

              {/* Label */}
              <div
                className={`min-w-0 flex-1 ${sidebarOpen ? "block" : "hidden"}`}
              >
                <div
                  className={`overflow-hidden text-ellipsis whitespace-nowrap text-[11px] ${
                    isDone || isActive ? "font-bold" : "font-medium"
                  } ${isActive ? "text-[#3C3489]" : "text-gray-500"}`}
                  style={isDone ? { color: agent.doneColor } : undefined}
                >
                  {agent.label}
                </div>
                <div
                  className={`mt-0.5 flex items-center gap-[3px] text-[9px] ${
                    isDone
                      ? "text-[#1D9E75]"
                      : isActive
                        ? "text-[#7F77DD]"
                        : "text-gray-400"
                  }`}
                >
                  {isActive && (
                    <span className="inline-block animate-[pulse_1.2s_infinite]">
                      ●
                    </span>
                  )}
                  {isDone ? "Terminé ✓" : isActive ? "En cours" : "En attente"}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Pipeline CTA */}
      <div
        className={`min-w-0 border-t border-[#f0eeff] p-3 ${
          sidebarOpen ? "opacity-100" : "opacity-0 pointer-events-none"
        }`}
      >
        <button
          onClick={onLaunchPipeline}
          disabled={!pipelineEnabled || pipelineCompleted}
          className={`flex w-full items-center justify-center gap-1.5 whitespace-nowrap rounded-full px-[10px] py-2.5 text-xs font-bold transition-all duration-200 ${
            pipelineEnabled && !pipelineCompleted
              ? "cursor-pointer bg-gradient-to-br from-[#7F77DD] to-[#534AB7] text-white shadow-[0_2px_10px_rgba(124,58,237,0.25)] opacity-100"
              : "cursor-not-allowed border border-[#e8e4ff] bg-[#f3f0ff] text-[#AFA9EC] opacity-60"
          }`}
        >
          {pipelineEnabled && !pipelineCompleted ? (
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path
                d="M2 6h8M7 3l3 3-3 3"
                stroke="white"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          ) : (
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <rect
                x="2"
                y="5"
                width="8"
                height="6"
                rx="1"
                stroke="#AFA9EC"
                strokeWidth="1.2"
              />
              <path
                d="M4 5V3.5a2 2 0 014 0V5"
                stroke="#AFA9EC"
                strokeWidth="1.2"
                strokeLinecap="round"
              />
            </svg>
          )}
          {pipelineCompleted
            ? "Pipeline terminé"
            : pipelineEnabled
              ? "Lancer le pipeline"
              : "Pipeline verrouillé"}
        </button>

        <div className="mt-1.5 text-center text-[10px] text-[#AFA9EC]">
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
        </div>
      </div>
    </div>
  );
}
