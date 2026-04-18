/**
 * AgentPageHeader
 * Standardized header card shown at the top of every agent page.
 *
 * Props:
 *   agent     — Agent object from @/agents/index.js  { label, short, gradient }
 *   subtitle          — Small muted text below the agent label (optional)
 *   subtitleClassName — Extra classes for the subtitle line (optional)
 *   badge     — React node rendered on the right side (optional)
 *   action    — React node rendered after the badge (optional)
 *   className — Extra classes on the wrapper (optional)
 */
export function AgentPageHeader({
  agent,
  subtitle,
  subtitleClassName = "",
  badge,
  action,
  className = "",
}) {
  const gradient = agent?.gradient || "linear-gradient(135deg,#7C3AED,#534AB7)";
  const short    = agent?.short    || "AI";
  const label    = agent?.label    || "Agent";
  const Icon     = agent?.icon     || null;

  return (
    <div
      className={`flex items-center gap-3 rounded-2xl border border-brand-border bg-white px-5 py-4 shadow-card ${className}`}
    >
      {/* Agent icon — gradient is dynamic from AGENTS registry */}
      <div
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full shadow-pill"
        style={{ background: gradient }}
      >
        {Icon ? (
          <Icon size={17} className="text-white" />
        ) : (
          <span className="text-[11px] font-bold text-white">{short}</span>
        )}
      </div>

      {/* Agent label + subtitle */}
      <div className="min-w-0 flex-1">
        <p className="text-sm font-extrabold text-ink">{label}</p>
        {subtitle && (
          <p className={`text-xs text-ink-subtle ${subtitleClassName}`.trim()}>{subtitle}</p>
        )}
      </div>

      {/* Right slot */}
      {badge}
      {action}
    </div>
  );
}

export default AgentPageHeader;
