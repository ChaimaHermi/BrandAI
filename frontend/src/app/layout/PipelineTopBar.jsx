/**
 * PipelineTopBar
 * Extracted from PipelineLayout — the fixed top bar with logo, breadcrumb,
 * progress pill, sidebar toggle, and user avatar.
 *
 * Props:
 *   ideaTitle          — truncated idea description string
 *   activeAgent        — agent object { label, short, gradient, color }
 *   progressPct        — 0–100 number
 *   activeIndex        — 0-based index of current agent in AGENTS array
 *   agentsCount        — total number of agents
 *   sidebarOpen        — boolean
 *   onToggle           — () => void — toggles sidebar
 *   userInitials       — 2-char string for avatar
 *   onNavigateDashboard — () => void — navigates to dashboard
 */
export default function PipelineTopBar({
  ideaTitle,
  activeAgent,
  progressPct,
  activeIndex,
  agentsCount,
  sidebarOpen,
  onToggle,
  userInitials,
  onNavigateDashboard,
}) {
  return (
    <div className="flex h-[52px] shrink-0 items-center gap-3 border-b border-[#e8e4ff] bg-white px-5 shadow-[0_1px_8px_rgba(124,58,237,0.06)]">
      {/* Logo */}
      <div className="mr-1 flex shrink-0 items-center gap-[7px]">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-[#7F77DD] to-[#534AB7] shadow-[0_2px_8px_rgba(124,58,237,0.3)]">
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
            <path
              d="M7 1.5l1.2 3 3 .4-2.2 2.1.5 3L7 8.5l-2.5 1.5.5-3L2.8 5l3-.4L7 1.5z"
              stroke="white"
              strokeWidth="1.1"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <span className="text-sm font-extrabold text-[#1a1040]">BrandAI</span>
      </div>

      {/* Breadcrumb */}
      <div className="flex flex-1 items-center gap-1.5 overflow-hidden text-xs text-gray-400">
        <span
          onClick={onNavigateDashboard}
          className="shrink-0 cursor-pointer font-semibold text-[#7F77DD]"
        >
          Mes idées
        </span>
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          className="shrink-0"
        >
          <path
            d="M4 2l4 4-4 4"
            stroke="#AFA9EC"
            strokeWidth="1.2"
            strokeLinecap="round"
          />
        </svg>
        <span className="overflow-hidden text-ellipsis whitespace-nowrap font-medium text-gray-500">
          {ideaTitle}…
        </span>
        <svg
          width="12"
          height="12"
          viewBox="0 0 12 12"
          fill="none"
          className="shrink-0"
        >
          <path
            d="M4 2l4 4-4 4"
            stroke="#AFA9EC"
            strokeWidth="1.2"
            strokeLinecap="round"
          />
        </svg>
        <div className="flex shrink-0 items-center gap-[5px]">
          <div
            className="flex h-[18px] w-[18px] items-center justify-center rounded-full text-[7px] font-bold text-white"
            style={{ background: activeAgent.gradient }}
          >
            {activeAgent.short}
          </div>
          <span className="text-xs font-bold text-[#3C3489]">
            {activeAgent.label}
          </span>
        </div>
      </div>

      {/* Progress pill */}
      <div className="flex shrink-0 items-center gap-2 rounded-full bg-[#f0eeff] px-3 py-[5px]">
        <div className="h-1 w-[50px] overflow-hidden rounded-full bg-white">
          <div
            style={{
              height: "100%",
              width: progressPct + "%",
              transition: "width 0.5s ease",
            }}
            className="rounded-full bg-gradient-to-r from-[#7F77DD] to-[#534AB7]"
          />
        </div>
        <span className="text-[10px] font-bold text-[#534AB7]">
          {activeIndex + 1}/{agentsCount}
        </span>
      </div>

      {/* Sidebar toggle */}
      <button
        onClick={onToggle}
        className={`flex h-[34px] w-[34px] shrink-0 cursor-pointer flex-col items-center justify-center gap-1 rounded-lg border border-[#e8e4ff] transition-all ${
          sidebarOpen ? "bg-[#f0eeff]" : "bg-white"
        }`}
      >
        {sidebarOpen ? (
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
            <path
              d="M3 3l8 8M11 3l-8 8"
              stroke="#7F77DD"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
        ) : (
          <div className="flex flex-col items-center gap-1">
            <div className="h-[1.5px] w-[14px] rounded-full bg-[#7F77DD]" />
            <div className="h-[1.5px] w-[14px] rounded-full bg-[#7F77DD]" />
            <div className="h-[1.5px] w-[10px] rounded-full bg-[#7F77DD]" />
          </div>
        )}
      </button>

      {/* User avatar */}
      <div className="flex h-8 w-8 shrink-0 cursor-pointer items-center justify-center rounded-full bg-gradient-to-br from-[#7F77DD] to-[#534AB7] text-[10px] font-bold text-white shadow-[0_2px_6px_rgba(124,58,237,0.25)]">
        {userInitials}
      </div>
    </div>
  );
}
