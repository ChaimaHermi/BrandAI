import { Card } from "@/shared/ui/Card";
import { useState } from "react";

const PALETTE = ["#1877F2", "#E1306C", "#0A66C2", "#F59E0B", "#EF4444", "#10B981", "#8B5CF6"];

function prettyLabel(key) {
  const map = {
    like: "Like",
    love: "Love",
    haha: "Haha",
    wow: "Wow",
    sad: "Sad",
    angry: "Angry",
    praise: "Praise",
    empathy: "Empathy",
    interest: "Interest",
    appreciation: "Appreciation",
    entertainment: "Entertainment",
  };
  return map[key] || key;
}

function toSegments(reactions) {
  const entries = Object.entries(reactions || {}).filter(([, v]) => Number(v) > 0);
  const total = entries.reduce((acc, [, v]) => acc + Number(v), 0);
  if (!total) return { total: 0, segments: [] };
  const segments = entries
    .sort((a, b) => Number(b[1]) - Number(a[1]))
    .map(([key, value], idx) => ({
      key,
      label: prettyLabel(key),
      value: Number(value),
      pct: (Number(value) / total) * 100,
      color: PALETTE[idx % PALETTE.length],
    }));
  return { total, segments };
}

export default function ReactionsDonut({ reactions, loading }) {
  const [hoveredKey, setHoveredKey] = useState(null);
  const [tooltipPos, setTooltipPos] = useState({ x: 0, y: 0 });
  const { total, segments } = toSegments(reactions);
  let cumulative = 0;
  const hovered = segments.find((s) => s.key === hoveredKey) || null;

  return (
    <Card padding="p-4" className="flex flex-col gap-4">
      <div>
        <p className="text-sm font-bold text-ink">Répartition des réactions</p>
        <p className="text-2xs text-ink-muted">Breakdown des réactions cumulées</p>
      </div>

      {loading ? (
        <div className="h-40 animate-pulse rounded-xl bg-brand-light/40" />
      ) : total <= 0 ? (
        <div className="flex h-40 items-center justify-center rounded-xl border border-dashed border-brand-border bg-brand-light/10 text-xs text-ink-muted">
          Aucune réaction disponible
        </div>
      ) : (
        <div className="flex flex-col gap-4 md:flex-row md:items-center">
          <div className="relative mx-auto h-40 w-40">
            <svg viewBox="0 0 42 42" className="h-40 w-40 -rotate-90">
              <circle cx="21" cy="21" r="15.915" fill="transparent" stroke="#E5E7EB" strokeWidth="4" />
              {segments.map((s) => {
                const dash = `${s.pct} ${100 - s.pct}`;
                const offset = -cumulative;
                cumulative += s.pct;
                return (
                  <circle
                    key={s.key}
                    cx="21"
                    cy="21"
                    r="15.915"
                    fill="transparent"
                    stroke={s.color}
                    strokeWidth={hoveredKey === s.key ? "5" : "4"}
                    strokeDasharray={dash}
                    strokeDashoffset={offset}
                    style={{ cursor: "pointer" }}
                    onMouseEnter={() => setHoveredKey(s.key)}
                    onMouseMove={(e) => {
                      const rect = e.currentTarget.ownerSVGElement?.getBoundingClientRect();
                      if (!rect) return;
                      setTooltipPos({
                        x: e.clientX - rect.left + 14,
                        y: e.clientY - rect.top - 8,
                      });
                    }}
                    onFocus={() => setHoveredKey(s.key)}
                    onMouseLeave={() => setHoveredKey(null)}
                  />
                );
              })}
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-xl font-extrabold text-ink">{total}</span>
              <span className="text-2xs text-ink-muted">réactions</span>
            </div>
            {hovered && (
              <div
                className="pointer-events-none absolute z-10 w-44 rounded-lg border border-brand-border bg-white px-3 py-2 shadow-lg"
                style={{
                  left: `${Math.max(6, Math.min(tooltipPos.x, 112))}px`,
                  top: `${Math.max(6, Math.min(tooltipPos.y, 132))}px`,
                }}
              >
                <p className="text-[11px] font-semibold text-ink">{hovered.label}</p>
                <p className="text-xs text-ink-muted">
                  {new Intl.NumberFormat("fr-FR").format(hovered.value)} réactions
                </p>
                <p className="text-xs font-bold text-ink">{hovered.pct.toFixed(1)}%</p>
              </div>
            )}
          </div>

          <div className="grid flex-1 grid-cols-1 gap-2">
            {segments.map((s) => (
              <div
                key={s.key}
                className={`flex items-center justify-between rounded-lg border px-2.5 py-1.5 ${
                  hoveredKey === s.key ? "border-brand bg-brand-light/20" : "border-brand-border"
                }`}
                onMouseEnter={() => setHoveredKey(s.key)}
                onMouseMove={(e) => {
                  const rect = e.currentTarget.getBoundingClientRect();
                  setTooltipPos({
                    x: 120,
                    y: Math.max(8, Math.min(e.clientY - rect.top + 8, 132)),
                  });
                }}
                onFocus={() => setHoveredKey(s.key)}
                onMouseLeave={() => setHoveredKey(null)}
              >
                <div className="flex items-center gap-2">
                  <span className="h-2.5 w-2.5 rounded-full" style={{ background: s.color }} />
                  <span className="text-xs text-ink">{s.label}</span>
                </div>
                <div className="text-right">
                  <p className="text-xs font-bold text-ink">{s.value}</p>
                  <p className="text-2xs text-ink-muted">{s.pct.toFixed(1)}%</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}
