/**
 * SectionIntro
 * Lightweight header card shown at the top of each tab/section content.
 * Creates a consistent visual entry point across Market Analysis, Marketing Plan, and Branding.
 *
 * Props:
 *   icon        — react-icons component (e.g. FiBarChart2)
 *   title       — Section title
 *   description — Short description of what this section contains
 *   badge       — Optional React node (pill, count, etc.) rendered on the right
 *   className   — Extra classes on the wrapper (optional)
 */
export function SectionIntro({ icon: Icon, title, description, badge, className = "" }) {
  return (
    <div
      className={`flex items-center gap-4 rounded-2xl border border-brand-border bg-white px-5 py-4 shadow-card ${className}`}
    >
      {Icon && (
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-light">
          <Icon size={18} className="text-brand" />
        </span>
      )}
      <div className="min-w-0 flex-1">
        <p className="text-sm font-bold text-ink">{title}</p>
        {description && (
          <p className="mt-0.5 text-xs text-ink-muted">{description}</p>
        )}
      </div>
      {badge}
    </div>
  );
}

export default SectionIntro;
