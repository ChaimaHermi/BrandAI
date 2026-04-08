/**
 * TabBar
 * Standardized tab navigation bar used across all agent modules.
 * Active tab uses brand gradient (same visual weight as the sidebar CTA).
 *
 * Props:
 *   tabs      — Array of { id: string, label: string }
 *   activeId  — id of the currently active tab
 *   onChange  — (id: string) => void
 *   className — extra classes on the wrapper (optional)
 */
export function TabBar({ tabs, activeId, onChange, className = "" }) {
  return (
    <div className={`flex flex-wrap gap-2 ${className}`}>
      {tabs.map((tab) => (
        <button
          key={tab.id}
          type="button"
          onClick={() => onChange(tab.id)}
          className={`rounded-full border px-4 py-1.5 text-xs font-semibold transition-all duration-150 ${
            activeId === tab.id
              ? "border-brand bg-gradient-to-br from-brand to-brand-dark text-white shadow-btn"
              : "border-brand-border bg-white text-ink-muted hover:border-brand-muted hover:text-brand-dark"
          }`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

export default TabBar;
