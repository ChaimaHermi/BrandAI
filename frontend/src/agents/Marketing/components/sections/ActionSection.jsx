import { FiClock, FiCalendar, FiTrendingUp, FiCheckCircle, FiFlag } from "react-icons/fi";

const HORIZONS = [
  {
    key: "shortTerm",
    milestoneKey: "shortTermMilestone",
    durationKey:  "shortTermDuration",
    label:  "Court terme",
    icon:   FiClock,
    color:  "text-brand",
    border: "border-l-brand",
    badge:  "bg-brand-light text-brand-dark border-brand-border",
    milestone: "bg-brand-light/60",
  },
  {
    key: "midTerm",
    milestoneKey: "midTermMilestone",
    durationKey:  "midTermDuration",
    label:  "Moyen terme",
    icon:   FiCalendar,
    color:  "text-amber-500",
    border: "border-l-amber-400",
    badge:  "bg-amber-50 text-amber-700 border-amber-200",
    milestone: "bg-amber-50/60",
  },
  {
    key: "longTerm",
    milestoneKey: "longTermMilestone",
    durationKey:  "longTermDuration",
    label:  "Long terme",
    icon:   FiTrendingUp,
    color:  "text-success",
    border: "border-l-success",
    badge:  "bg-success-light text-success-dark border-success-border",
    milestone: "bg-success-light/60",
  },
];

export function ActionSection({ plan }) {
  const a = plan?.actionPlan ?? {};

  return (
    <div className="grid gap-3 sm:grid-cols-3">
      {HORIZONS.map((h) => {
        const Icon = h.icon;
        const actions = a[h.key] ?? [];
        const milestone = a[h.milestoneKey];
        const duration = a[h.durationKey];
        return (
          <div key={h.key} className={`flex flex-col overflow-hidden rounded-xl border border-[color:var(--color-border,#ebebf5)] border-l-4 ${h.border} bg-white shadow-sm`}>
            {/* Header */}
            <div className="flex items-center justify-between gap-2 border-b border-[color:var(--color-border,#ebebf5)] px-3 py-2.5">
              <div className="flex items-center gap-1.5">
                <Icon size={12} className={h.color} />
                <p className="text-[12px] font-bold text-ink">{h.label}</p>
              </div>
              {duration && (
                <span className={`rounded-full border px-2 py-0.5 text-[10px] font-semibold ${h.badge}`}>
                  {duration}
                </span>
              )}
            </div>

            {/* Actions */}
            {actions.length > 0 && (
              <ul className="flex flex-col gap-1.5 px-3 py-2.5">
                {actions.map((action, i) => (
                  <li key={i} className="flex items-start gap-1.5">
                    <FiCheckCircle size={11} className={`mt-0.5 shrink-0 ${h.color}`} />
                    <p className="text-[11px] leading-relaxed text-ink">{action}</p>
                  </li>
                ))}
              </ul>
            )}

            {/* Milestone */}
            {milestone && (
              <div className={`flex items-start gap-1.5 border-t border-[color:var(--color-border,#ebebf5)] px-3 py-2 ${h.milestone}`}>
                <FiFlag size={10} className={`mt-0.5 shrink-0 ${h.color}`} />
                <p className="text-[11px] font-semibold leading-relaxed text-ink">{milestone}</p>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
