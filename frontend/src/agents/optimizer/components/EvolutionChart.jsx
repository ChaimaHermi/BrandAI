import { FiTrendingUp } from "react-icons/fi";
import { useState } from "react";
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
  const [hoverIdx, setHoverIdx] = useState(null);
  const platform = PLATFORMS[activePlatform];
  const points = Array.isArray(evolution)
    ? evolution
      .filter((p) => p?.date && p?.value !== null && p?.value !== undefined)
      .map((p) => ({ date: String(p.date).slice(0, 10), value: Number(p.value) }))
      .sort((a, b) => a.date.localeCompare(b.date))
    : [];
  const maxValue = points.reduce((m, p) => Math.max(m, p.value), 0);
  const peakThreshold = maxValue > 0 ? maxValue * 0.8 : 0;
  const peakPoints = points.filter((p) => p.value >= peakThreshold && p.value > 0);
  const chartW = 560;
  const chartH = 180;
  const padX = 20;
  const padY = 12;
  const plotW = chartW - padX * 2;
  const plotH = chartH - padY * 2;
  const linePoints = points.map((p, idx) => {
    const x = padX + (idx * plotW) / Math.max(points.length - 1, 1);
    const y = padY + (1 - (maxValue > 0 ? p.value / maxValue : 0)) * plotH;
    return { ...p, x, y };
  });
  const linePath = linePoints.length > 0
    ? linePoints
    .map((p, idx) => `${idx === 0 ? "M" : "L"} ${p.x.toFixed(2)} ${p.y.toFixed(2)}`)
    .join(" ")
    : "";
  const areaPath = linePoints.length
    ? `${linePath} L ${linePoints[linePoints.length - 1].x.toFixed(2)} ${(padY + plotH).toFixed(2)} L ${linePoints[0].x.toFixed(2)} ${(padY + plotH).toFixed(2)} Z`
    : "";
  const hoveredPoint = hoverIdx !== null && hoverIdx >= 0 && hoverIdx < linePoints.length
    ? linePoints[hoverIdx]
    : null;

  const handleMouseMove = (e) => {
    if (!linePoints.length) return;
    const svg = e.currentTarget;
    const rect = svg.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const ratio = rect.width > 0 ? x / rect.width : 0;
    const idx = Math.round(ratio * (linePoints.length - 1));
    setHoverIdx(Math.max(0, Math.min(linePoints.length - 1, idx)));
  };

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
              {platform.label} · au fil du temps (données réelles)
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
            <div className="w-full">
              <svg
                viewBox={`0 0 ${chartW} ${chartH}`}
                className="h-[180px] w-full"
                onMouseMove={handleMouseMove}
                onMouseLeave={() => setHoverIdx(null)}
              >
                <defs>
                  <linearGradient id="engagementArea" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={platform.color} stopOpacity="0.25" />
                    <stop offset="100%" stopColor={platform.color} stopOpacity="0.03" />
                  </linearGradient>
                </defs>

                <line x1={padX} y1={padY + plotH} x2={padX + plotW} y2={padY + plotH} stroke="#D1D5DB" strokeWidth="1" />
                <line x1={padX} y1={padY} x2={padX} y2={padY + plotH} stroke="#E5E7EB" strokeWidth="1" />

                {areaPath && <path d={areaPath} fill="url(#engagementArea)" />}
                {linePath && <path d={linePath} fill="none" stroke={platform.color} strokeWidth="2.5" strokeLinecap="round" />}

                {linePoints.filter((_, idx) => idx % 2 === 0 || idx === linePoints.length - 1).map((p) => (
                  <g key={p.date}>
                    <text x={p.x} y={chartH - 2} textAnchor="middle" fontSize="8" fill="#6B7280">
                      {p.date.slice(5)}
                    </text>
                  </g>
                ))}
                {linePoints.map((p, idx) => (
                  <g
                    key={`${p.date}-${idx}`}
                    onMouseEnter={() => setHoverIdx(idx)}
                    onFocus={() => setHoverIdx(idx)}
                  >
                    {/* Larger invisible hit area to make hover easier on every point */}
                    <circle cx={p.x} cy={p.y} r="9" fill="transparent" />
                    <circle cx={p.x} cy={p.y} r={hoverIdx === idx ? "3.8" : "2.2"} fill={platform.color} />
                  </g>
                ))}
                {hoveredPoint && (
                  <g pointerEvents="none">
                    <line
                      x1={hoveredPoint.x}
                      y1={padY}
                      x2={hoveredPoint.x}
                      y2={padY + plotH}
                      stroke={platform.color}
                      strokeOpacity="0.35"
                      strokeDasharray="3 3"
                    />
                    <circle cx={hoveredPoint.x} cy={hoveredPoint.y} r="5" fill={platform.color} fillOpacity="0.15" />
                    <circle cx={hoveredPoint.x} cy={hoveredPoint.y} r="3.2" fill={platform.color} />
                    {(() => {
                      const cardW = 170;
                      const cardH = 42;
                      const gap = 10;
                      const toRight = hoveredPoint.x + cardW + gap <= chartW - 4;
                      const x = toRight ? hoveredPoint.x + gap : hoveredPoint.x - cardW - gap;
                      const y = Math.max(4, Math.min(hoveredPoint.y - cardH / 2, chartH - cardH - 4));
                      return (
                        <>
                          <rect
                            x={x}
                            y={y}
                            width={cardW}
                            height={cardH}
                            rx="8"
                            fill="white"
                            stroke="#D1D5DB"
                          />
                          <text x={x + 8} y={y + 16} fontSize="9" fill="#6B7280">
                            Date: {hoveredPoint.date}
                          </text>
                          <text x={x + 8} y={y + 31} fontSize="10" fill="#111827" fontWeight="700">
                            Engagement: {new Intl.NumberFormat("fr-FR").format(Math.round(hoveredPoint.value))}
                          </text>
                        </>
                      );
                    })()}
                  </g>
                )}
                {linePoints
                  .filter((p) => peakPoints.some((pk) => pk.date === p.date && pk.value === p.value))
                  .map((p) => (
                    <g key={`peak-${p.date}`}>
                      <circle cx={p.x} cy={p.y} r="4" fill={platform.color} opacity="0.25" />
                      <circle cx={p.x} cy={p.y} r="2.6" fill={platform.color} />
                    </g>
                  ))}
              </svg>
              <p className="mt-2 text-right text-[11px] text-ink-subtle">
                Pics affichés: {peakPoints.length} · points: {points.length}
              </p>
            </div>
          )}
        </div>
      </div>

    </Card>
  );
}

export default EvolutionChart;
