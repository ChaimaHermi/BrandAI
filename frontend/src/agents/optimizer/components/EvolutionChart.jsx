import { FiTrendingUp } from "react-icons/fi";
import { Card } from "@/shared/ui/Card";
import { PLATFORMS } from "../constants";

/**
 * Zone graphique d'évolution.
 * Structure prête à recevoir recharts ou chart.js.
 *
 * @param {{
 *   evolution: Array<{date: string, value: number}> | null,
 *   loading: boolean,
 *   activePlatform: string
 * }} props
 */
export function EvolutionChart({ evolution, loading, activePlatform }) {
  const platform = PLATFORMS[activePlatform];

  return (
    <Card padding="p-0" className="flex flex-col overflow-hidden">

      {/* Header — même pattern que ContentWorkspace */}
      <div className="flex items-center justify-between border-b border-brand-border bg-gradient-to-r from-brand-light/40 to-white px-5 py-3.5">
        <div className="flex items-start gap-3">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-brand-light">
            <FiTrendingUp className="h-4 w-4 text-brand" />
          </div>
          <div className="min-w-0 flex-1">
            <p className="text-sm font-bold text-ink">Évolution de l'engagement</p>
            <p className="text-2xs text-ink-muted">
              {platform.label} · 30 derniers jours
            </p>
          </div>
        </div>

        <span
          className="inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-2xs font-semibold"
          style={{
            background: `${platform.color}12`,
            borderColor: `${platform.color}30`,
            color: platform.color,
          }}
        >
          <span
            className="h-2 w-2 rounded-full"
            style={{ background: platform.color }}
          />
          {platform.label}
        </span>
      </div>

      {/* Chart zone */}
      <div className="flex flex-1 flex-col px-5 py-4">
        <div className="flex min-h-[180px] flex-1 items-center justify-center rounded-xl border border-dashed border-brand-border bg-brand-light/10">
          {loading ? (
            <div className="flex flex-col items-center gap-2">
              <div
                className="h-6 w-6 animate-spin rounded-full border-2 border-t-transparent"
                style={{ borderColor: `${platform.color}40`, borderTopColor: platform.color }}
              />
              <span className="text-2xs text-ink-muted">Chargement du graphique…</span>
            </div>
          ) : !evolution || evolution.length === 0 ? (
            <div className="flex flex-col items-center gap-2">
              <FiTrendingUp className="h-8 w-8 text-ink-muted/30" />
              <span className="text-2xs text-ink-muted">
                Aucune donnée d'évolution disponible
              </span>
            </div>
          ) : (
            /* Placeholder — brancher recharts/chart.js ici */
            <span className="text-2xs text-ink-muted">
              {evolution.length} points · graphique à brancher ici
            </span>
          )}
        </div>
      </div>

    </Card>
  );
}

export default EvolutionChart;
