import { FiUsers, FiFlag, FiLink, FiTrendingUp, FiZap, FiArrowRight } from "react-icons/fi";

const STEPS = [
  {
    key: "targetFirstUsers",
    label: "Premiers utilisateurs",
    sublabel: "Qui cibler en premier",
    icon: FiUsers,
    iconBg: "bg-brand-light",
    iconColor: "text-brand",
    borderAccent: "border-l-brand",
    isList: false,
  },
  {
    key: "launchStrategy",
    label: "Stratégie de lancement",
    sublabel: "Comment entrer sur le marché",
    icon: FiFlag,
    iconBg: "bg-amber-50",
    iconColor: "text-amber-500",
    borderAccent: "border-l-amber-400",
    isList: false,
  },
  {
    key: "partnerships",
    label: "Partenariats",
    sublabel: "Alliances & synergies",
    icon: FiLink,
    iconBg: "bg-success-light",
    iconColor: "text-success",
    borderAccent: "border-l-success",
    isList: true,
  },
  {
    key: "earlyGrowthTactics",
    label: "Tactiques de croissance",
    sublabel: "Actions semaines 1-4",
    icon: FiTrendingUp,
    iconBg: "bg-sky-50",
    iconColor: "text-sky-500",
    borderAccent: "border-l-sky-400",
    isList: true,
  },
];

function StepBullet({ text, iconColor }) {
  return (
    <li className="flex items-start gap-2.5">
      <FiArrowRight size={12} className={`mt-0.5 shrink-0 ${iconColor}`} />
      <p className="text-[13px] leading-relaxed text-ink">{text}</p>
    </li>
  );
}

function StepCard({ config, value }) {
  const Icon = config.icon;
  const isEmpty = config.isList
    ? !Array.isArray(value) || value.length === 0
    : !value;

  return (
    <div
      className={`overflow-hidden rounded-2xl border border-[color:var(--color-border,#ebebf5)] border-l-4 ${config.borderAccent} bg-white shadow-card`}
    >
      {/* Header */}
      <div className="flex items-center gap-3 px-4 py-3.5">
        <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-xl ${config.iconBg}`}>
          <Icon size={15} className={config.iconColor} />
        </span>
        <div>
          <p className="text-sm font-bold text-ink">{config.label}</p>
          <p className="text-[11px] text-ink-subtle">{config.sublabel}</p>
        </div>
      </div>

      {/* Content */}
      <div className="border-t border-[color:var(--color-border,#ebebf5)] px-4 py-3">
        {isEmpty ? (
          <p className="text-sm text-ink-subtle">N'existe pas</p>
        ) : config.isList ? (
          <ul className="space-y-2">
            {value.map((item, i) => (
              <StepBullet key={i} text={item} iconColor={config.iconColor} />
            ))}
          </ul>
        ) : (
          <p className="text-[13px] leading-relaxed text-ink">{value}</p>
        )}
      </div>
    </div>
  );
}

export function GtmSection({ plan }) {
  const g = plan?.goToMarket ?? {};

  return (
    <div className="flex flex-col gap-4">
      {/* Launch banner */}
      <div className="flex items-center gap-3 rounded-2xl border border-amber-200 bg-gradient-to-r from-amber-50 to-orange-50 px-5 py-4 shadow-card">
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-amber-400 to-orange-400 text-white shadow-pill">
          <FiZap size={15} />
        </span>
        <div>
          <p className="text-[10px] font-extrabold uppercase tracking-widest text-amber-500">
            Go-to-Market
          </p>
          <p className="mt-0.5 text-sm font-semibold text-ink">
            Stratégie d'entrée marché
          </p>
        </div>
      </div>

      {/* 2-column grid on md+ */}
      <div className="grid gap-3 md:grid-cols-2">
        {STEPS.map((s) => (
          <StepCard
            key={s.key}
            config={s}
            value={g[s.key]}
          />
        ))}
      </div>
    </div>
  );
}
