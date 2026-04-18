import {
  FiBarChart2, FiDollarSign, FiTrendingUp,
  FiActivity, FiUsers, FiPercent, FiExternalLink, FiZap,
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
  const marketSources = Array.isArray(market?.sources) ? market.sources : [];
  const marketSignals = Array.isArray(market?.market_signals) ? market.market_signals : [];

  return (
    <div className="flex flex-col gap-4">
      {/* ── Metric cards ──────────────────────────────────────────────────── */}
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        {FIELD_CONFIG.map(({ key, label, Icon, accent }) => {
          const metric = market?.[key];
          const value  = metric?.value ?? "N/D";
          const unit   = metric?.unit  ?? "";
          const source = metric?.source ?? "";
          const isNd   = value === "N/D";

          if (isNd) return null;

          return (
            <div
              key={key}
              className="flex flex-col gap-3 rounded-xl border border-brand-border bg-white p-4 shadow-card transition-shadow hover:shadow-card-md"
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
                {isNd ? (
                  <span className="text-lg font-medium italic text-ink-subtle">N/D</span>
                ) : (
                  <span className="text-2xl font-bold text-ink">
                    {value}
                    {unit && (
                      <span className="ml-1 text-sm font-normal text-ink-muted">{unit}</span>
                    )}
                  </span>
                )}
              </div>

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

      {/* ── Market signals ───────────────────────────────────────────────── */}
      {marketSignals.length > 0 && (
        <div>
          <p className="mb-3 flex items-center gap-2 border-l-2 border-brand-muted pl-2 text-xs font-semibold uppercase tracking-[0.07em] text-brand">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-brand-light text-brand">
              <FiZap size={12} />
            </span>
            Signaux marché
          </p>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {marketSignals.map((signal, idx) => {
              const hasSource = typeof signal?.source === "string" && signal.source.trim();
              const desc = typeof signal?.description === "string" ? signal.description.trim() : "";
              const titleFr = desc || formatMetricFallback(signal.metric);
              const { Icon: SignalIcon, bubbleClass } = getMarketSignalIconConfig(signal);
              return (
                <div
                  key={idx}
                  className="flex flex-col gap-3 rounded-xl border border-brand-border bg-white p-4 shadow-card transition-shadow hover:shadow-card-md"
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
                    <span className="text-2xl font-bold text-brand-dark">
                      {signal.value ?? "N/D"}
                    </span>
                    {signal.unit && (
                      <span className="text-sm font-normal text-ink-muted">{signal.unit}</span>
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
        <div className="rounded-xl border border-brand-border bg-white p-4 shadow-card">
          <p className="mb-3 border-l-2 border-brand-muted pl-2 text-xs font-semibold uppercase tracking-[0.07em] text-brand">
            Sources du marché
          </p>
          <div className="grid grid-cols-1 gap-2">
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
                    {domain || "source"}
                  </span>
                  <span className="ml-4 truncate text-brand">{url}</span>
                </a>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
