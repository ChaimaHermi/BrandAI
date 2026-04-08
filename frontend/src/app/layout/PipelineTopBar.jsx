/**
 * PipelineTopBar — fixed top bar inside the pipeline shell.
 * Purely presentational. Zero inline styles. Zero hardcoded hex.
 */

/* ── Chevron icon (breadcrumb separator) ─────────────────────────────────── */
function Chevron() {
  return (
    <svg width="12" height="12" viewBox="0 0 12 12" fill="none" className="shrink-0 text-brand-muted" aria-hidden>
      <path d="M4 2l4 4-4 4" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round" />
    </svg>
  );
}

/* ── Hamburger / close icon ──────────────────────────────────────────────── */
function MenuIcon({ open }) {
  if (open) {
    return (
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="text-brand">
        <path d="M3 3l8 8M11 3l-8 8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
      </svg>
    );
  }
  return (
    <div className="flex flex-col items-center gap-[3px]">
      <div className="h-[1.5px] w-[14px] rounded-full bg-brand" />
      <div className="h-[1.5px] w-[14px] rounded-full bg-brand" />
      <div className="h-[1.5px] w-[10px]  rounded-full bg-brand" />
    </div>
  );
}

/* ── Component ───────────────────────────────────────────────────────────── */
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
    <div className="flex h-[52px] shrink-0 items-center gap-3 border-b border-brand-border bg-white px-5 shadow-topbar">

      {/* Logo */}
      <div className="mr-1 flex shrink-0 items-center gap-2">
        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-brand to-brand-dark shadow-pill">
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none" aria-hidden>
            <path
              d="M7 1.5l1.2 3 3 .4-2.2 2.1.5 3L7 8.5l-2.5 1.5.5-3L2.8 5l3-.4L7 1.5z"
              stroke="white"
              strokeWidth="1.1"
              strokeLinejoin="round"
            />
          </svg>
        </div>
        <span className="text-sm font-extrabold text-ink">BrandAI</span>
      </div>

      {/* Breadcrumb */}
      <div className="flex flex-1 items-center gap-1.5 overflow-hidden">
        <button
          type="button"
          onClick={onNavigateDashboard}
          className="shrink-0 text-xs font-semibold text-brand transition-colors hover:text-brand-dark"
        >
          Mes idées
        </button>

        <Chevron />

        <span className="truncate text-xs font-medium text-ink-muted">
          {ideaTitle}…
        </span>

        <Chevron />

        {/* Active agent pill */}
        <div className="flex shrink-0 items-center gap-1.5">
          <div
            className="flex h-[18px] w-[18px] items-center justify-center rounded-full text-[7px] font-bold text-white"
            style={{ background: activeAgent.gradient }}
          >
            {activeAgent.short}
          </div>
          <span className="text-xs font-bold text-brand-darker">{activeAgent.label}</span>
        </div>
      </div>

      {/* Progress pill */}
      <div className="flex shrink-0 items-center gap-2 rounded-full bg-brand-light px-3 py-1.5">
        <div className="h-1 w-[50px] overflow-hidden rounded-full bg-white">
          <div
            className="h-full rounded-full bg-gradient-to-r from-brand to-brand-dark transition-[width] duration-500"
            style={{ width: `${progressPct}%` }}
          />
        </div>
        <span className="text-2xs font-bold text-brand-dark">
          {activeIndex + 1}/{agentsCount}
        </span>
      </div>

      {/* Sidebar toggle */}
      <button
        type="button"
        onClick={onToggle}
        aria-label={sidebarOpen ? "Fermer le panneau" : "Ouvrir le panneau"}
        className={`flex h-[34px] w-[34px] shrink-0 items-center justify-center rounded-xl border border-brand-border transition-all ${
          sidebarOpen ? "bg-brand-light" : "bg-white hover:bg-brand-light"
        }`}
      >
        <MenuIcon open={sidebarOpen} />
      </button>

      {/* User avatar */}
      <div className="flex h-8 w-8 shrink-0 cursor-default items-center justify-center rounded-full bg-gradient-to-br from-brand to-brand-dark text-2xs font-bold text-white shadow-pill">
        {userInitials}
      </div>
    </div>
  );
}
