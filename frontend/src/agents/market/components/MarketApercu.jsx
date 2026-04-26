import { useState } from "react";
import {
  FiBarChart2, FiDollarSign, FiTrendingUp,
  FiActivity, FiUsers, FiPercent, FiExternalLink, FiZap, FiCalendar,
} from "react-icons/fi";

const FIELD_CONFIG = [
  { key: "market_size",     label: "Taille du marché",      Icon: FiBarChart2,  accent: "bg-brand-light text-brand" },
  { key: "market_revenue",  label: "Revenus",               Icon: FiDollarSign, accent: "bg-success-light text-success" },
  { key: "CAGR",            label: "CAGR",                  Icon: FiTrendingUp, accent: "bg-blue-50 text-blue-600" },
  { key: "growth_rate",     label: "Croissance",            Icon: FiActivity,   accent: "bg-amber-50 text-amber-600" },
  { key: "number_of_users", label: "Nb. utilisateurs",      Icon: FiUsers,      accent: "bg-rose-50 text-rose-600" },
  { key: "adoption_rate",   label: "Taux d'adoption",       Icon: FiPercent,    accent: "bg-emerald-50 text-emerald-600" },
];

function isUrlLike(value) {
  return typeof value === "string" && /^https?:\/\//i.test(value.trim());
}

function asMetricEntry(metric) {
  if (metric && typeof metric === "object" && !Array.isArray(metric)) {
    return {
      value: metric.value ?? null,
      unit: metric.unit ?? "",
      year: metric.year ?? "",
      description: typeof metric.description === "string" ? metric.description : "",
      source: metric.source ?? "",
    };
  }
  return {
    value: metric ?? null,
    unit: "",
    year: "",
    description: "",
    source: "",
  };
}

function toChartPoints(items) {
  if (!Array.isArray(items)) return [];
  const parsed = [];
  for (const item of items) {
    const year = Number(String(item?.year ?? "").replace(/[^\d.-]/g, ""));
    const value = Number(String(item?.value ?? "").replace(/[^\d.,-]/g, "").replace(",", "."));
    if (!Number.isFinite(year) || !Number.isFinite(value)) continue;
    parsed.push({
      year,
      value,
      unit: typeof item?.unit === "string" ? item.unit : "",
      source: typeof item?.source === "string" ? item.source : "",
    });
  }
  return parsed.sort((a, b) => a.year - b.year);
}

function SectorGrowthChart({ sectorName, chartPoints, unitLabel, sectorGrowth }) {
  const chartWidth = 680;
  const chartHeight = 200;
  const padX = 48;
  const padY = 28;
  const padTop = 36;

  const hasValidChart = chartPoints.length >= 2;
  const firstPt = chartPoints[0];
  const lastPt = chartPoints[chartPoints.length - 1];

  const minX = firstPt?.year ?? 0;
  const maxX = lastPt?.year ?? 1;
  const values = chartPoints.map((p) => p.value);
  const minY = values.length ? Math.min(...values) * 0.92 : 0;
  const maxY = values.length ? Math.max(...values) * 1.08 : 1;
  const xSpan = maxX - minX || 1;
  const ySpan = maxY - minY || 1;

  const toX = (year) => padX + ((year - minX) / xSpan) * (chartWidth - padX - 16);
  const toY = (val) => chartHeight - padY - ((val - minY) / ySpan) * (chartHeight - padY - padTop);

  const pointsAttr = chartPoints.map((p) => `${toX(p.year)},${toY(p.value)}`).join(" ");

  return (
    <div>
      <p className="mb-3 flex items-center gap-2 border-l-2 border-brand-muted pl-2 text-xs font-semibold uppercase tracking-[0.07em] text-brand">
        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
          <FiTrendingUp size={12} />
        </span>
        Croissance sectorielle
      </p>

      <div className="rounded-xl border border-emerald-100 bg-white p-4 shadow-sm">
        {/* Header: Sector name + unit (from backend only) */}
        <div className="mb-4">
          {sectorName ? (
            <h4 className="text-base font-bold text-ink">{sectorName}</h4>
          ) : (
            <h4 className="text-sm italic text-ink-muted">Secteur non renseigne par l&apos;agent</h4>
          )}
          {unitLabel && (
            <span className="text-xs text-ink-muted">Unite: {unitLabel}</span>
          )}
        </div>

        {hasValidChart ? (
          <>
            {/* Chart — affiche uniquement les points backend */}
            <div className="overflow-x-auto">
              <svg
                viewBox={`0 0 ${chartWidth} ${chartHeight}`}
                className="h-48 w-full min-w-[540px]"
                role="img"
                aria-label="Courbe croissance sectorielle"
              >
                {/* Axes */}
                <line x1={padX} y1={padTop} x2={padX} y2={chartHeight - padY} stroke="#e5e7eb" strokeWidth="1" />
                <line x1={padX} y1={chartHeight - padY} x2={chartWidth - 16} y2={chartHeight - padY} stroke="#e5e7eb" strokeWidth="1" />

                {/* Area fill */}
                <polygon
                  points={`${toX(firstPt.year)},${chartHeight - padY} ${pointsAttr} ${toX(lastPt.year)},${chartHeight - padY}`}
                  fill="url(#areaGradientSector)"
                />
                <defs>
                  <linearGradient id="areaGradientSector" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#10b981" stopOpacity="0.18" />
                    <stop offset="100%" stopColor="#10b981" stopOpacity="0.02" />
                  </linearGradient>
                </defs>

                {/* Line */}
                <polyline
                  fill="none"
                  stroke="#10b981"
                  strokeWidth="2"
                  points={pointsAttr}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />

                {/* Points + labels (valeurs exactes du backend) */}
                {chartPoints.map((p, idx) => {
                  const cx = toX(p.year);
                  const cy = toY(p.value);
                  return (
                    <g key={`pt-${p.year}-${idx}`}>
                      <circle cx={cx} cy={cy} r="4" fill="#fff" stroke="#10b981" strokeWidth="2" />
                      <text
                        x={cx}
                        y={cy - 8}
                        textAnchor="middle"
                        className="fill-emerald-700 text-[9px] font-medium"
                      >
                        {p.value}
                      </text>
                      <text
                        x={cx}
                        y={chartHeight - 10}
                        textAnchor="middle"
                        className="fill-ink-muted text-[9px]"
                      >
                        {p.year}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>

            {/* Table — donnees brutes backend uniquement */}
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-emerald-100">
                    <th className="py-2 pr-4 text-left font-semibold text-ink-muted">Annee</th>
                    <th className="py-2 pr-4 text-right font-semibold text-ink-muted">Valeur</th>
                    <th className="py-2 pr-4 text-right font-semibold text-ink-muted">Unite</th>
                    <th className="py-2 pr-4 text-left font-semibold text-ink-muted">Description</th>
                    <th className="py-2 text-left font-semibold text-ink-muted">Source</th>
                  </tr>
                </thead>
                <tbody>
                  {sectorGrowth.map((pt, idx) => (
                    <tr key={`row-${idx}`} className="border-b border-gray-50">
                      <td className="py-2 pr-4 font-medium text-ink">{pt?.year ?? "N/A"}</td>
                      <td className="py-2 pr-4 text-right text-ink">{pt?.value ?? "N/A"}</td>
                      <td className="py-2 pr-4 text-right text-ink-muted">{pt?.unit || "—"}</td>
                      <td className="py-2 pr-4 text-left text-ink-muted">
                        {typeof pt?.description === "string" && pt.description.trim()
                          ? pt.description
                          : "—"}
                      </td>
                      <td className="py-2 text-left">
                        {pt?.source && typeof pt.source === "string" && pt.source.startsWith("http") ? (
                          <a
                            href={pt.source}
                            target="_blank"
                            rel="noreferrer"
                            className="inline-flex items-center gap-1 text-brand hover:underline"
                          >
                            <FiExternalLink size={10} />
                            Lien
                          </a>
                        ) : pt?.source ? (
                          <span className="text-ink-muted">{pt.source}</span>
                        ) : (
                          <span className="text-ink-subtle">—</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        ) : (
          <div className="py-6 text-center">
            <FiBarChart2 size={28} className="mx-auto mb-2 text-ink-subtle" />
            <p className="text-sm italic text-ink-subtle">
              Donnees insuffisantes pour tracer la courbe.
            </p>
            {sectorGrowth.length > 0 && (
              <div className="mt-4 text-left">
                <p className="mb-2 text-xs font-medium text-ink-muted">Donnees brutes recues:</p>
                <ul className="space-y-1 text-xs text-ink-muted">
                  {sectorGrowth.map((pt, i) => (
                    <li key={i}>
                      Annee: {pt?.year ?? "?"} | Valeur: {pt?.value ?? "?"} | Unite: {pt?.unit ?? "?"}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

/** Libellé secours si pas de description FR (évite le Title Case anglais agressif) */
function formatMetricFallback(metric) {
  if (typeof metric !== "string" || !metric.trim()) return "Indicateur";
  return metric
    .replace(/_/g, " ")
    .replace(/\s+/g, " ")
    .trim()
    .toLowerCase();
}

const SIGNAL_BUBBLE_BASE =
  "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg";

/** Aligné sur les cartes métriques : Taux d'adoption / Revenus */
const ACCENT_ADOPTION = FIELD_CONFIG.find((c) => c.key === "adoption_rate")?.accent ?? "bg-emerald-50 text-emerald-600";
const ACCENT_REVENUE = FIELD_CONFIG.find((c) => c.key === "market_revenue")?.accent ?? "bg-success-light text-success";
const ACCENT_DEFAULT = FIELD_CONFIG.find((c) => c.key === "market_size")?.accent ?? "bg-brand-light text-brand";

/**
 * Icône + pastille : pourcentage = même couleur que « Taux d'adoption », revenus = « Revenus ».
 */
function getMarketSignalIconConfig(signal) {
  const metric = String(signal?.metric ?? "").toLowerCase();
  const unit = String(signal?.unit ?? "").toLowerCase();
  const desc = String(signal?.description ?? "").toLowerCase();
  const haystack = `${metric} ${unit} ${desc}`;

  const hasMoneyUnit =
    /[$€£]|usd|eur|tnd|dt\b|mdt|million|milliard|md\b|k€|m€|bn\b/.test(haystack + unit);

  if (
    /\b(revenue|revenu|revenus|chiffre|affaires|sales|ventes|turnover|earnings|profit|marge|ca\b)/.test(
      haystack,
    ) ||
    hasMoneyUnit
  ) {
    return { Icon: FiDollarSign, bubbleClass: `${SIGNAL_BUBBLE_BASE} ${ACCENT_REVENUE}` };
  }

  if (
    unit.includes("%") ||
    /\b(percent|percentage|pourcent|taux|ratio|proportion|part\s|share|adoption|wearing|portent)/.test(
      haystack,
    ) ||
    /_pct|pct\b|percent|percentage|rate|taux|adoption/.test(metric)
  ) {
    return { Icon: FiPercent, bubbleClass: `${SIGNAL_BUBBLE_BASE} ${ACCENT_ADOPTION}` };
  }

  if (/\b(users|utilisateur|utilisateurs|population|personnes|people|ménage|household)/.test(haystack)) {
    const a = FIELD_CONFIG.find((c) => c.key === "number_of_users")?.accent ?? ACCENT_DEFAULT;
    return { Icon: FiUsers, bubbleClass: `${SIGNAL_BUBBLE_BASE} ${a}` };
  }

  if (/\b(cagr|growth|croissance|cro[iî]t|augment)/.test(haystack)) {
    const a = FIELD_CONFIG.find((c) => c.key === "CAGR")?.accent ?? ACCENT_DEFAULT;
    return { Icon: FiTrendingUp, bubbleClass: `${SIGNAL_BUBBLE_BASE} ${a}` };
  }

  if (/\b(market\s*size|taille\s*du\s*marché|volume|valeur\s*du\s*marché)/.test(haystack)) {
    return { Icon: FiBarChart2, bubbleClass: `${SIGNAL_BUBBLE_BASE} ${ACCENT_DEFAULT}` };
  }

  return { Icon: FiZap, bubbleClass: `${SIGNAL_BUBBLE_BASE} ${ACCENT_DEFAULT}` };
}

export default function MarketApercu({ market }) {
  const [showSources, setShowSources] = useState(false);
  const marketSources = Array.isArray(market?.sources) ? market.sources : [];
  const marketSignals = Array.isArray(market?.market_signals) ? market.market_signals : [];
  const sectorGrowth = Array.isArray(market?.sector_growth) ? market.sector_growth : [];
  const sectorName = String(market?.sector_name || market?.sector || "").trim();
  const chartPoints = toChartPoints(sectorGrowth);
  const unitLabel = chartPoints[0]?.unit || "";

  return (
    <div className="flex flex-col gap-3">
      {/* ── Metric cards ──────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {FIELD_CONFIG.map(({ key, label, Icon, accent }) => {
          const metric = asMetricEntry(market?.[key]);
          const value  = metric.value;
          const unit   = metric.unit;
          const source = metric.source;
          const year   = metric.year;
          const description = metric.description?.trim?.() || "";
          const isMissing = value === null || value === undefined || value === "";

          if (isMissing) return null;

          return (
            <div
              key={key}
              className="flex flex-col gap-2 rounded-xl border border-brand-border bg-white p-3 shadow-sm"
            >
              {/* Icon bubble + label */}
              <div className="flex items-center gap-2">
                <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${accent}`}>
                  <Icon size={15} />
                </span>
                {/* Label — same style as SectionLabel for consistency */}
                <span className="border-l-2 border-brand-muted pl-2 text-xs font-semibold uppercase tracking-[0.07em] text-brand">
                  {label}
                </span>
              </div>

              {/* Value */}
              <div>
                <span className="text-xl font-bold text-ink">
                  {value}
                  {unit && (
                    <span className="ml-1 text-xs font-normal text-ink-muted">{unit}</span>
                  )}
                </span>
                {!!year && (
                  <span className="ml-2 inline-block rounded-full bg-brand-light px-2 py-0.5 text-2xs font-semibold text-brand">
                    {year}
                  </span>
                )}
              </div>

              {/* Description (metric standard) */}
              {description && (
                <p className="text-xs leading-relaxed text-ink-muted line-clamp-3">
                  {description}
                </p>
              )}

              {/* Source */}
              {source && (
                <div className="text-2xs leading-relaxed text-ink-subtle">
                  {isUrlLike(source) ? (
                    <a
                      href={source}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-brand hover:underline"
                    >
                      <FiExternalLink size={10} />
                      Source
                    </a>
                  ) : (
                    source
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* ── Sector growth (year/value extracted points) ─────────────────── */}
      {sectorGrowth.length > 0 && (
        <SectorGrowthChart
          sectorName={sectorName}
          chartPoints={chartPoints}
          unitLabel={unitLabel}
          sectorGrowth={sectorGrowth}
        />
      )}

      {/* ── Market signals ───────────────────────────────────────────────── */}
      {marketSignals.length > 0 && (
        <div className="rounded-xl border border-brand-border bg-white p-3 shadow-sm">
          <p className="mb-3 flex items-center gap-2 border-l-2 border-brand-muted pl-2 text-xs font-semibold uppercase tracking-[0.07em] text-brand">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-brand-light text-brand">
              <FiZap size={12} />
            </span>
            Signaux marché
          </p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {marketSignals.map((signal, idx) => {
              const signalValue = signal?.value;
              const isSignalMissing =
                signalValue === null || signalValue === undefined || signalValue === "";
              if (isSignalMissing) return null;

              const hasSource = typeof signal?.source === "string" && signal.source.trim();
              const desc = typeof signal?.description === "string" ? signal.description.trim() : "";
              const titleFr = desc || formatMetricFallback(signal.metric);
              const { Icon: SignalIcon, bubbleClass } = getMarketSignalIconConfig(signal);
              return (
                <div
                  key={idx}
                  className="flex flex-col gap-2 rounded-xl border border-brand-border bg-white p-3 shadow-sm"
                >
                  {/* Icône % = couleur Taux d'adoption ; revenu = couleur Revenus (FIELD_CONFIG) */}
                  <div className="flex items-start gap-2">
                    <span className={bubbleClass}>
                      <SignalIcon size={15} />
                    </span>
                    <span className="border-l-2 border-brand-muted pl-2 text-sm font-semibold leading-snug text-ink-body line-clamp-3">
                      {titleFr}
                    </span>
                  </div>

                  {/* Value + unit + year */}
                  <div className="flex flex-wrap items-baseline gap-1">
                    <span className="text-xl font-bold text-brand-dark">
                      {signal.value}
                    </span>
                    {signal.unit && (
                      <span className="text-xs font-normal text-ink-muted">{signal.unit}</span>
                    )}
                    {signal.year && (
                      <span className="ml-1 rounded-full bg-brand-light px-2 py-0.5 text-2xs font-semibold text-brand">
                        {signal.year}
                      </span>
                    )}
                  </div>

                  {/* Détail FR seulement si le titre était un fallback anglais (évite doublon) */}
                  {desc && titleFr !== desc && (
                    <p className="text-xs leading-relaxed text-ink-muted line-clamp-3">
                      {signal.description}
                    </p>
                  )}

                  {/* Source */}
                  {hasSource && (
                    <a
                      href={signal.source}
                      target="_blank"
                      rel="noreferrer"
                      className="mt-auto inline-flex items-center gap-1 text-2xs text-brand hover:underline"
                    >
                      <FiExternalLink size={10} />
                      Source
                    </a>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ── Market sources ────────────────────────────────────────────────── */}
      {marketSources.length > 0 && (
        <div className="rounded-xl border border-brand-border bg-white p-4 shadow-sm">
          <p className="mb-3 border-l-2 border-brand-muted pl-2 text-xs font-semibold uppercase tracking-[0.07em] text-brand">
            Sources du marché
          </p>
          <button
            type="button"
            onClick={() => setShowSources((v) => !v)}
            className="rounded-lg border border-brand-border px-3 py-1.5 text-xs font-semibold text-brand hover:bg-brand-light"
          >
            {showSources ? "Masquer sources" : "Voir sources"}
          </button>
          {showSources && (
            <div className="mt-3 grid grid-cols-1 gap-2">
              {marketSources.map((src, idx) => {
                const url    = typeof src?.url    === "string" ? src.url    : "";
                const domain = typeof src?.domain === "string" ? src.domain : "";
                if (!url) return null;
                return (
                  <a
                    key={`${url}-${idx}`}
                    href={url}
                    target="_blank"
                    rel="noreferrer"
                    className="flex items-center justify-between rounded-lg border border-brand-border px-3 py-2 text-sm transition-colors hover:bg-brand-light"
                  >
                    <span className="flex items-center gap-2 font-medium text-ink-muted">
                      <FiExternalLink size={12} className="text-brand-muted" />
                      {domain || "Source non disponible"}
                    </span>
                    <span className="ml-4 truncate text-brand">{url}</span>
                  </a>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
