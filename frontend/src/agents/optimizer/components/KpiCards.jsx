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
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)} M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)} K`;
  return String(value);
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

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {KPI_CONFIG.map(({ key, label, icon, isPercent }) => {
        const Icon = ICONS[icon];
        const value = kpis?.[key] ?? null;

        return (
          <Card key={key} padding="p-4" className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <p className="text-2xs font-bold uppercase tracking-wider text-ink-muted">
                {label}
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
              <p className="text-2xl font-extrabold text-ink">
                {formatKpi(value, isPercent)}
              </p>
            )}
          </Card>
        );
      })}
    </div>
  );
}

export default KpiCards;
