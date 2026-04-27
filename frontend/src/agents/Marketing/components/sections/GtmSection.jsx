import { FiUsers, FiFlag, FiLink, FiTrendingUp, FiArrowRight } from "react-icons/fi";

const STEPS = [
  { key: "targetFirstUsers",  label: "Premiers utilisateurs",  icon: FiUsers,      color: "text-brand",       border: "border-l-brand"     },
  { key: "launchStrategy",    label: "Stratégie de lancement", icon: FiFlag,       color: "text-amber-500",   border: "border-l-amber-400" },
  { key: "partnerships",      label: "Partenariats",           icon: FiLink,       color: "text-success",     border: "border-l-success",  isList: true },
  { key: "earlyGrowthTactics",label: "Tactiques de croissance",icon: FiTrendingUp, color: "text-sky-500",     border: "border-l-sky-400",  isList: true },
];

export function GtmSection({ plan }) {
  const g = plan?.goToMarket ?? {};

  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {STEPS.map((s) => {
        const Icon = s.icon;
        const value = g[s.key];
        const isEmpty = s.isList ? !Array.isArray(value) || value.length === 0 : !value;
        return (
          <div key={s.key} className={`overflow-hidden rounded-xl border border-[color:var(--color-border,#ebebf5)] border-l-4 ${s.border} bg-white shadow-sm`}>
            <div className="flex items-center gap-2 px-3 py-2.5 border-b border-[color:var(--color-border,#ebebf5)]">
              <Icon size={13} className={s.color} />
              <p className="text-[12px] font-bold text-ink">{s.label}</p>
            </div>
            <div className="px-3 py-2.5">
              {isEmpty ? null : s.isList ? (
                <ul className="flex flex-col gap-1.5">
                  {value.map((item, i) => (
                    <li key={i} className="flex items-start gap-1.5">
                      <FiArrowRight size={10} className={`mt-0.5 shrink-0 ${s.color}`} />
                      <p className="text-[12px] leading-relaxed text-ink">{item}</p>
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-[12px] leading-relaxed text-ink">{value}</p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
