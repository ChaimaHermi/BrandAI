import {
  FiArrowUpRight, FiAlertTriangle, FiStar,
  FiThumbsUp, FiThumbsDown, FiTrendingUp, FiAlertOctagon, FiMessageSquare, FiExternalLink,
} from "react-icons/fi";

function isNonEmptyArray(v) { return Array.isArray(v) && v.length > 0; }
function hasText(v)         { return typeof v === "string" && v.trim().length > 0; }
function asArray(v)         { return Array.isArray(v) ? v : []; }
function asText(v)          { return typeof v === "string" ? v : ""; }
function lineFrom(item, keys = []) {
  if (typeof item === "string") return item;
  if (!item || typeof item !== "object") return "";
  for (const k of keys) {
    const val = item[k];
    if (typeof val === "string" && val.trim()) return val;
  }
  return "";
}

function toUrlOrNull(value) {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  if (!trimmed || trimmed.toLowerCase() === "web") return null;
  if (/^https?:\/\//i.test(trimmed)) return trimmed;
  if (/^[\w.-]+\.[a-z]{2,}(\/.*)?$/i.test(trimmed)) return `https://${trimmed}`;
  return null;
}

function EmptySlot() {
  return (
    <span className="mt-2 inline-block rounded-lg border border-dashed border-brand-border bg-brand-light px-3 py-2 text-xs italic text-ink-subtle">
      Data non disponible
    </span>
  );
}

function BulletList({ items }) {
  if (!isNonEmptyArray(items)) return <EmptySlot />;
  return (
    <div className="space-y-1.5">
      {items.map((item, idx) => (
        <div key={`${item}-${idx}`} className="flex items-start gap-2 text-sm leading-relaxed">
          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-ink-subtle" />
          <span className="text-ink-body">{item}</span>
        </div>
      ))}
    </div>
  );
}

function BulletListFromObjects({ items, textKeys = ["point", "signal", "driver", "barrier", "insight"] }) {
  const lines = asArray(items).map((it) => lineFrom(it, textKeys)).filter(Boolean);
  if (!isNonEmptyArray(lines)) return <EmptySlot />;
  return <BulletList items={lines} />;
}

function MetaBadges({ impact, type, source }) {
  const sourceUrl = toUrlOrNull(source);
  return (
    <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
      {impact && (
        <span className="rounded-full bg-amber-50 px-2 py-0.5 text-2xs font-semibold text-amber-700">
          impact: {impact}
        </span>
      )}
      {type && (
        <span className="rounded-full bg-indigo-50 px-2 py-0.5 text-2xs font-semibold text-indigo-700">
          type: {type}
        </span>
      )}
      {source && (
        sourceUrl ? (
          <a
            href={sourceUrl}
            target="_blank"
            rel="noreferrer"
            className="inline-flex items-center gap-1 text-2xs font-medium text-brand hover:underline"
          >
            <FiExternalLink size={10} />
            source
          </a>
        ) : (
          <span className="rounded-full bg-gray-100 px-2 py-0.5 text-2xs font-medium text-ink-muted">
            source: {source}
          </span>
        )
      )}
    </div>
  );
}

/* ── Strategic insight card ──────────────────────────────────────────────── */
function InsightCard({ icon: Icon, iconClass, borderClass, title, text }) {
  return (
    <div className={`rounded-2xl border bg-white p-5 shadow-card ${borderClass}`}>
      <div className="mb-2 flex items-center gap-2">
        <span className={`flex h-8 w-8 items-center justify-center rounded-lg ${iconClass}`}>
          <Icon size={14} />
        </span>
        <p className="text-sm font-bold text-ink">{title}</p>
      </div>
      {hasText(text) ? (
        <p className="text-sm leading-relaxed text-ink-body">{text}</p>
      ) : (
        <EmptySlot />
      )}
    </div>
  );
}

/* ── SWOT quadrant ───────────────────────────────────────────────────────── */
function SwotCard({ icon: Icon, iconClass, borderClass, bgClass, title, items }) {
  return (
    <div className={`rounded-2xl border p-5 ${bgClass} ${borderClass}`}>
      <div className="mb-3 flex items-center gap-2">
        <Icon size={15} className={iconClass} />
        <p className="text-sm font-bold text-ink">{title}</p>
        <span className="ml-auto rounded-full bg-white/60 px-2 py-0.5 text-xs text-ink-muted">
          {Array.isArray(items) ? items.length : 0}
        </span>
      </div>
      {isNonEmptyArray(items) ? (
        <div className="space-y-2">
          {items.map((item, idx) => {
            const text = lineFrom(item, ["point"]);
            if (!text) return null;
            return (
              <div key={`${title}-${idx}`} className="rounded-lg bg-white/60 px-2.5 py-2">
                <p className="text-sm leading-relaxed text-ink-body">{text}</p>
                <MetaBadges type={item?.type} source={item?.source} />
              </div>
            );
          })}
        </div>
      ) : (
        <EmptySlot />
      )}
    </div>
  );
}

const PESTEL_CONFIG = [
  { key: "politique",       fallbackKey: "political",      short: "P", label: "Politique",       cellClass: "bg-gray-50 border-l-4 border-l-gray-300" },
  { key: "economique",      fallbackKey: "economic",       short: "É", label: "Économique",      cellClass: "bg-emerald-50 border-l-4 border-l-emerald-400" },
  { key: "social",          fallbackKey: "social",         short: "S", label: "Social",          cellClass: "bg-blue-50 border-l-4 border-l-blue-400" },
  { key: "technologique",   fallbackKey: "technological",  short: "T", label: "Technologique",   cellClass: "bg-brand-light border-l-4 border-l-brand-muted" },
  { key: "environnemental", fallbackKey: "environmental",  short: "E", label: "Environnemental", cellClass: "bg-green-50 border-l-4 border-l-green-400" },
  { key: "legal",           fallbackKey: "legal",          short: "L", label: "Légal",           cellClass: "bg-orange-50 border-l-4 border-l-orange-400" },
];

export default function MarketStrategy({ strategy }) {
  const pestel  = strategy?.pestel;
  const swot    = strategy?.swot;
  const demand  = strategy?.demand_analysis;
  const insight = strategy?.strategic_insight;

  const swotForces = asArray(swot?.forces);
  const swotFaiblesses = asArray(swot?.faiblesses);
  const swotOpportunites = asArray(swot?.opportunites);
  const swotMenaces = asArray(swot?.menaces);

  const insightOpportunity = asText(insight?.main_opportunity);
  const insightRisk = asText(insight?.main_risk);
  const insightRecommendation = asText(insight?.recommendation);

  return (
    <div className="flex flex-col gap-6">

      {/* ── SWOT ─────────────────────────────────────────────────────────── */}
      <div>
        <h2 className="mb-4 text-base font-bold text-ink">Analyse SWOT</h2>
        <div className="grid grid-cols-2 gap-4">
          <SwotCard
            icon={FiThumbsUp}    iconClass="text-success"
            bgClass="bg-success-light" borderClass="border-success-border"
            title="Forces"      items={swotForces.map((x) => lineFrom(x, ["point"]))}
          />
          <SwotCard
            icon={FiThumbsDown}  iconClass="text-red-500"
            bgClass="bg-red-50"  borderClass="border-red-200"
            title="Faiblesses"  items={swotFaiblesses.map((x) => lineFrom(x, ["point"]))}
          />
          <SwotCard
            icon={FiTrendingUp}  iconClass="text-blue-600"
            bgClass="bg-blue-50" borderClass="border-blue-200"
            title="Opportunités" items={swotOpportunites.map((x) => lineFrom(x, ["point"]))}
          />
          <SwotCard
            icon={FiAlertOctagon} iconClass="text-amber-600"
            bgClass="bg-amber-50" borderClass="border-amber-200"
            title="Menaces"     items={swotMenaces.map((x) => lineFrom(x, ["point"]))}
          />
        </div>
      </div>

      {/* ── PESTEL ───────────────────────────────────────────────────────── */}
      <div>
        <h2 className="mb-4 text-base font-bold text-ink">Analyse PESTEL</h2>
        <div className="grid grid-cols-3 gap-4">
          {PESTEL_CONFIG.map((cfg) => (
            <div
              key={cfg.key}
              className={`relative overflow-hidden rounded-xl border p-4 ${cfg.cellClass}`}
            >
              <span className="absolute right-3 top-2 text-6xl font-black text-ink opacity-5">
                {cfg.short}
              </span>
              <p className="mb-2 text-sm font-bold text-ink">{cfg.label}</p>
              {isNonEmptyArray(pestel?.[cfg.key]) ? (
                <div className="space-y-2">
                  {pestel[cfg.key].map((item, idx) => (
                    <div key={`${cfg.key}-${idx}`} className="rounded-lg bg-white/70 px-2.5 py-2">
                      <p className="text-sm leading-relaxed text-ink-body">
                        {lineFrom(item, ["signal"])}
                      </p>
                      <MetaBadges impact={item?.impact} type={item?.type} source={item?.source} />
                    </div>
                  ))}
                </div>
              ) : (
                <EmptySlot />
              )}
            </div>
          ))}
        </div>
      </div>

      {/* ── Demand analysis ──────────────────────────────────────────────── */}
      <div>
        <h2 className="mb-4 text-base font-bold text-ink">Analyse de la demande</h2>
        <div className="grid grid-cols-3 gap-4">
          {/* Demand level + growth */}
          <div className="rounded-2xl border border-brand-border bg-white p-5 shadow-card">
            <p className="mb-2 text-sm font-bold text-ink">Niveau de demande</p>
            {hasText(demand?.demand_level) ? (
              <span className="inline-block rounded-full bg-brand-light px-3 py-1 text-sm font-medium text-brand-dark">
                {demand.demand_level}
              </span>
            ) : <EmptySlot />}
            {hasText(demand?.demand_justification) && (
              <p className="mt-2 text-sm leading-relaxed text-ink-body">{demand.demand_justification}</p>
            )}
            <p className="mb-2 mt-4 text-sm font-bold text-ink">Potentiel de croissance</p>
            {hasText(demand?.growth_potential) ? (
              <p className="text-sm leading-relaxed text-ink-body">{demand.growth_potential}</p>
            ) : <EmptySlot />}
          </div>

          {/* Drivers */}
          <div className="rounded-2xl border border-brand-border bg-white p-5 shadow-card">
            <p className="mb-3 text-sm font-bold text-ink">Drivers</p>
            {isNonEmptyArray(demand?.drivers) ? (
              demand.drivers.map((item, idx) => (
                <div key={`dr-${idx}`} className="flex items-start gap-2 py-1.5 text-sm">
                  <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-success" />
                  <span className="text-ink-body">
                    {lineFrom(item, ["driver"])}
                  </span>
                  <MetaBadges source={item?.source} />
                </div>
              ))
            ) : <EmptySlot />}
          </div>

          {/* Barriers + Insights */}
          <div className="rounded-2xl border border-brand-border bg-white p-5 shadow-card">
            <p className="mb-2 text-sm font-bold text-ink">Barrières</p>
            {isNonEmptyArray(demand?.barriers) ? (
              demand.barriers.map((item, idx) => (
                <div key={`ba-${idx}`} className="flex items-start gap-2 py-1.5 text-sm">
                  <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-red-500" />
                  <span className="text-ink-body">
                    {lineFrom(item, ["barrier"])}
                  </span>
                  <MetaBadges source={item?.source} />
                </div>
              ))
            ) : <EmptySlot />}

            <p className="mb-2 mt-4 text-sm font-bold text-ink">Customer insights</p>
            {isNonEmptyArray(demand?.customer_insights) ? (
              demand.customer_insights.map((item, idx) => (
                <div key={`ci-${idx}`} className="flex items-start gap-2 py-1.5 text-sm">
                  <span className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-blue-500" />
                  <span className="text-ink-body">
                    {lineFrom(item, ["insight"])}
                  </span>
                  <MetaBadges source={item?.source} />
                </div>
              ))
            ) : <EmptySlot />}
          </div>
        </div>
      </div>

      {/* ── Strategic insights — synthèse finale ─────────────────────────── */}
      <div>
        <h2 className="mb-1 text-base font-bold text-ink">Synthèse stratégique</h2>
        <p className="mb-4 text-xs text-ink-muted">
          Conclusions tirées de l&apos;analyse SWOT, PESTEL et de la demande.
        </p>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
          <InsightCard
            icon={FiArrowUpRight}
            iconClass="bg-success-light text-success"
            borderClass="border-success-border border-l-4 border-l-success"
            title="Opportunité"
            text={insightOpportunity}
          />
          <InsightCard
            icon={FiAlertTriangle}
            iconClass="bg-red-50 text-red-500"
            borderClass="border-red-200 border-l-4 border-l-red-400"
            title="Risque"
            text={insightRisk}
          />
          <InsightCard
            icon={FiStar}
            iconClass="bg-brand-light text-brand"
            borderClass="border-brand-border border-l-4 border-l-brand"
            title="Recommandation"
            text={insightRecommendation}
          />
        </div>
        <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <InsightCard
            icon={FiTrendingUp}
            iconClass="bg-blue-50 text-blue-600"
            borderClass="border-blue-200 border-l-4 border-l-blue-500"
            title="Segment prioritaire"
            text={insight?.segment_prioritaire}
          />
          <InsightCard
            icon={FiMessageSquare}
            iconClass="bg-indigo-50 text-indigo-600"
            borderClass="border-indigo-200 border-l-4 border-l-indigo-500"
            title="Message clé suggéré"
            text={insight?.message_cle_suggere}
          />
        </div>
      </div>
    </div>
  );
}
