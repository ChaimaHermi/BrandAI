import {
  FiUsers, FiActivity, FiGlobe, FiFileText,
} from "react-icons/fi";
import { Card } from "@/shared/ui/Card";
import { KPI_CONFIG, PLATFORMS } from "../constants";

const ICONS = {
  users: FiUsers,
  activity: FiActivity,
  globe: FiGlobe,
  file: FiFileText,
};

function formatKpi(value, isPercent) {
  if (value === null || value === undefined) return "—";
  if (isPercent) return `${Number(value).toFixed(1)} %`;
  return new Intl.NumberFormat("fr-FR").format(Number(value));
}

function SkeletonValue() {
  return (
    <div className="mt-1 h-7 w-20 animate-pulse rounded-lg bg-brand-light/60" />
  );
}

/**
 * @param {{
 *   kpis: Record<string, number|null> | null,
 *   loading: boolean,
 *   activePlatform: string
 * }} props
 */
export function KpiCards({ kpis, loading, activePlatform }) {
  const platform = PLATFORMS[activePlatform];
  const visibleConfig = KPI_CONFIG.filter(
    (item) => !item.hiddenOn || !item.hiddenOn.includes(activePlatform),
  );

  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-4">
      {visibleConfig.map(({ key, label, linkedinLabel, icon, isPercent, linkedinIsPercent }) => {
        const Icon = ICONS[icon];
        const value = kpis?.[key] ?? null;
        const displayLabel =
          activePlatform === "linkedin" && linkedinLabel ? linkedinLabel : label;
        const displayPercent =
          activePlatform === "linkedin" && linkedinIsPercent === false ? false : isPercent;

        return (
          <Card key={key} padding="p-4" className="flex flex-col gap-2 border border-brand-border bg-gradient-to-b from-white to-brand-light/10">
            <div className="flex items-center justify-between">
              <p className="text-2xs font-bold uppercase tracking-wider text-ink-muted">
                {displayLabel}
              </p>
              <span
                className="flex h-7 w-7 items-center justify-center rounded-xl"
                style={{ background: `${platform.color}15` }}
              >
                <Icon className="h-3.5 w-3.5" style={{ color: platform.color }} />
              </span>
            </div>

            {loading ? (
              <SkeletonValue />
            ) : (
              <p className="text-3xl font-black text-ink">
                {formatKpi(value, displayPercent)}
              </p>
            )}
          </Card>
        );
      })}
    </div>
  );
}

export default KpiCards;
