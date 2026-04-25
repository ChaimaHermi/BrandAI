import { FiClock, FiCalendar, FiTrendingUp, FiCheckCircle, FiFlag } from "react-icons/fi";

const HORIZONS = [
  {
    key: "shortTerm",
    milestoneKey: "shortTermMilestone",
    durationKey: "shortTermDuration",
    step: "01",
    label: "Court terme",
    sublabel: "Installation & lancement",
    icon: FiClock,
    iconGradient: "from-brand to-brand-dark",
    iconBg: "bg-brand-light",
    iconColor: "text-brand",
    borderAccent: "border-l-brand",
    stepColor: "text-brand",
    stepBg: "bg-brand-light",
    milestoneClass: "bg-brand-light text-brand-dark border-brand-border",
    badgeClass: "bg-brand-light text-brand-dark",
    connectorColor: "bg-brand/20",
  },
  {
    key: "midTerm",
    milestoneKey: "midTermMilestone",
    durationKey: "midTermDuration",
    step: "02",
    label: "Moyen terme",
    sublabel: "Croissance & tests",
    icon: FiCalendar,
    iconGradient: "from-amber-400 to-orange-400",
    iconBg: "bg-amber-50",
    iconColor: "text-amber-500",
    borderAccent: "border-l-amber-400",
    stepColor: "text-amber-500",
    stepBg: "bg-amber-50",
    milestoneClass: "bg-amber-50 text-amber-700 border-amber-200",
    badgeClass: "bg-amber-50 text-amber-700",
    connectorColor: "bg-amber-200",
  },
  {
    key: "longTerm",
    milestoneKey: "longTermMilestone",
    durationKey: "longTermDuration",
    step: "03",
    label: "Long terme",
    sublabel: "Scale & optimisation",
    icon: FiTrendingUp,
    iconGradient: "from-success to-emerald-600",
    iconBg: "bg-success-light",
    iconColor: "text-success",
    borderAccent: "border-l-success",
    stepColor: "text-success",
    stepBg: "bg-success-light",
    milestoneClass: "bg-success-light text-success-dark border-success-border",
    badgeClass: "bg-success-light text-success-dark",
    connectorColor: "bg-success/20",
  },
];

function HorizonCard({ config, actions, milestone, duration }) {
  const Icon = config.icon;
  const hasActions = Array.isArray(actions) && actions.length > 0;

  return (
    <div
      className={`flex flex-col overflow-hidden rounded-2xl border border-[color:var(--color-border,#ebebf5)] border-l-4 ${config.borderAccent} bg-white shadow-card`}
    >
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-4">
        <span className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br ${config.iconGradient} text-white shadow-sm`}>
          <Icon size={16} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <span className={`text-[10px] font-extrabold tracking-widest ${config.stepColor}`}>
              {config.step}
            </span>
            <p className="text-sm font-extrabold text-ink">{config.label}</p>
          </div>
          <p className="text-[11px] text-ink-subtle">{config.sublabel}</p>
        </div>
        <span className={`shrink-0 rounded-full px-2.5 py-1 text-[11px] font-bold ${config.badgeClass}`}>
          {duration || "N'existe pas"}
        </span>
      </div>

      {/* Actions */}
      <div className="flex-1 border-t border-[color:var(--color-border,#ebebf5)] px-4 py-3">
        {hasActions ? (
          <ul className="space-y-2.5">
            {actions.map((action, i) => (
              <li key={i} className="flex items-start gap-2.5">
                <FiCheckCircle size={13} className={`mt-0.5 shrink-0 ${config.iconColor}`} />
                <p className="text-[13px] leading-relaxed text-ink">{action}</p>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-sm text-ink-subtle">N'existe pas</p>
        )}
      </div>

      {/* Milestone footer */}
      {milestone && (
        <div
          className={`flex items-start gap-2 border-t border-[color:var(--color-border,#ebebf5)] px-4 py-3 ${config.milestoneClass}`}
        >
          <FiFlag size={12} className="mt-0.5 shrink-0" />
          <p className="text-[12px] font-semibold leading-relaxed">{milestone}</p>
        </div>
      )}
    </div>
  );
}

export function ActionSection({ plan }) {
  const a = plan?.actionPlan ?? {};

  return (
    <div className="flex flex-col gap-4">
      {/* Desktop timeline header */}
      <div className="hidden md:block">
        <div className="relative flex items-center justify-between px-[calc(50%/3)]">
          {HORIZONS.map((h, idx) => (
            <div key={h.key} className="relative flex flex-1 flex-col items-center gap-1">
              {/* connecting line */}
              {idx < HORIZONS.length - 1 && (
                <span
                  className={`absolute left-1/2 top-3 h-px w-full ${h.connectorColor}`}
                  style={{ zIndex: 0 }}
                />
              )}
              {/* step dot */}
              <span
                className={`relative z-10 flex h-6 w-6 items-center justify-center rounded-full bg-gradient-to-br ${h.iconGradient} text-[10px] font-extrabold text-white shadow-sm`}
              >
                {idx + 1}
              </span>
              <span className={`text-[10px] font-bold ${h.stepColor}`}>{h.label}</span>
            </div>
          ))}
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {HORIZONS.map((h) => (
          <HorizonCard
            key={h.key}
            config={h}
            actions={a[h.key]}
            milestone={a[h.milestoneKey]}
            duration={a[h.durationKey]}
          />
        ))}
      </div>
    </div>
  );
}
