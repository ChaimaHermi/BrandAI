import {
  FiBarChart2, FiUsers, FiCpu, FiShield, FiStar, FiAlertTriangle, FiExternalLink,
} from "react-icons/fi";

function isNonEmptyArray(v) {
  return Array.isArray(v) && v.length > 0;
}

function normalizeTrendItem(item) {
  if (typeof item === "string") return { insight: item, maturity: "", source: "" };
  if (item && typeof item === "object") {
    return {
      insight: typeof item.insight === "string" ? item.insight : "",
      maturity: typeof item.maturity === "string" ? item.maturity : "",
      source: typeof item.source === "string" ? item.source : "",
    };
  }
  return { insight: "", maturity: "", source: "" };
}

function normalizeRiskItem(item) {
  if (typeof item === "string") return { insight: item, level: "", source: "" };
  if (item && typeof item === "object") {
    return {
      insight: typeof item.insight === "string" ? item.insight : "",
      level: typeof item.level === "string" ? item.level : "",
      source: typeof item.source === "string" ? item.source : "",
    };
  }
  return { insight: "", level: "", source: "" };
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

/* ── Trend card ──────────────────────────────────────────────────────────── */
function TrendCard({ icon: Icon, iconClass, title, items, dotClass }) {
  const hasItems = isNonEmptyArray(items);
  return (
    <div className="rounded-2xl border border-brand-border bg-white p-5 shadow-card">
      <div className="mb-3 flex items-center gap-2">
        <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${iconClass}`}>
          <Icon size={14} />
        </span>
        <p className="text-sm font-bold text-ink">{title}</p>
        {hasItems && (
          <span className="ml-auto rounded-full bg-gray-100 px-2 py-0.5 text-xs text-ink-subtle">
            {items.length}
          </span>
        )}
      </div>
      {hasItems ? (
        items.map((item, idx) => (
          <div
            key={`${title}-${idx}`}
            className="flex items-start gap-2 border-b border-gray-50 py-2 last:border-0"
          >
            <span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${dotClass}`} />
            <div>
              <p className="text-sm leading-relaxed text-ink-body">{item.insight}</p>
              <div className="mt-1 flex flex-wrap gap-2">
                {item.maturity && (
                  <span className="rounded-full bg-gray-100 px-2 py-0.5 text-2xs font-semibold text-ink-muted">
                    {item.maturity}
                  </span>
                )}
                {item.source && (
                  toUrlOrNull(item.source) ? (
                    <a
                      href={toUrlOrNull(item.source)}
                      target="_blank"
                      rel="noreferrer"
                      className="text-2xs text-brand hover:underline"
                    >
                      source
                    </a>
                  ) : (
                    <span className="rounded-full bg-gray-100 px-2 py-0.5 text-2xs font-medium text-ink-muted">
                      source: {item.source}
                    </span>
                  )
                )}
              </div>
            </div>
          </div>
        ))
      ) : (
        <EmptySlot />
      )}
    </div>
  );
}

export default function MarketTrendsRisks({ trends }) {
  const marketTrends       = (trends?.market_trends ?? []).map(normalizeTrendItem).filter((x) => x.insight);
  const consumerTrends     = (trends?.consumer_trends ?? []).map(normalizeTrendItem).filter((x) => x.insight);
  const technologyTrends   = (trends?.technology_trends ?? []).map(normalizeTrendItem).filter((x) => x.insight);
  const regulatoryTrends   = (trends?.regulatory_trends ?? []).map(normalizeTrendItem).filter((x) => x.insight);
  const emergingOpportunities = (trends?.opportunities ?? []).map(normalizeTrendItem).filter((x) => x.insight);
  const marketRisks        = (trends?.risks ?? []).map(normalizeRiskItem).filter((x) => x.insight);
  const sources            = Array.isArray(trends?.sources) ? trends.sources : [];

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-4">
        {/* Left column */}
        <div className="flex flex-col gap-4">
          <TrendCard
            icon={FiBarChart2} iconClass="bg-brand-light text-brand"
            title="Tendances marché"      items={marketTrends}     dotClass="bg-brand-muted"
          />
          <TrendCard
            icon={FiUsers}    iconClass="bg-blue-50 text-blue-600"
            title="Tendances consommateurs" items={consumerTrends}  dotClass="bg-blue-500"
          />
          <TrendCard
            icon={FiCpu}      iconClass="bg-amber-50 text-amber-600"
            title="Tendances technologiques" items={technologyTrends} dotClass="bg-amber-500"
          />
        </div>

        {/* Right column */}
        <div className="flex flex-col gap-4">
          <TrendCard
            icon={FiShield}   iconClass="bg-orange-50 text-orange-600"
            title="Tendances réglementaires" items={regulatoryTrends} dotClass="bg-orange-500"
          />
          <TrendCard
            icon={FiStar}     iconClass="bg-success-light text-success"
            title="Opportunités émergentes" items={emergingOpportunities} dotClass="bg-success"
          />
        </div>
      </div>

      {/* ── Risks ──────────────────────────────────────────────────────────── */}
      <div className="rounded-2xl border border-red-200 bg-red-50 p-5">
        <div className="mb-3 flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-100">
            <FiAlertTriangle size={14} className="text-red-600" />
          </span>
          <p className="text-sm font-bold text-ink">Risques marché</p>
          {isNonEmptyArray(marketRisks) && (
            <span className="ml-auto rounded-full bg-red-100 px-2 py-0.5 text-xs text-red-600">
              {marketRisks.length}
            </span>
          )}
        </div>
        {isNonEmptyArray(marketRisks) ? (
          marketRisks.map((risk, idx) => (
            <div
              key={`risk-${idx}`}
              className="mb-2 flex items-start gap-3 rounded-lg border-b border-red-100 bg-white px-3 py-2 last:border-0"
            >
              <FiAlertTriangle size={14} className="mt-0.5 shrink-0 text-amber-500" />
              <div>
                <p className="text-sm leading-relaxed text-ink-body">{risk.insight}</p>
                <div className="mt-1 flex flex-wrap gap-2">
                  {risk.level && (
                    <span className="rounded-full bg-red-100 px-2 py-0.5 text-2xs font-semibold text-red-700">
                      {risk.level}
                    </span>
                  )}
                  {risk.source && (
                    toUrlOrNull(risk.source) ? (
                      <a
                        href={toUrlOrNull(risk.source)}
                        target="_blank"
                        rel="noreferrer"
                        className="text-2xs text-brand hover:underline"
                      >
                        source
                      </a>
                    ) : (
                      <span className="rounded-full bg-gray-100 px-2 py-0.5 text-2xs font-medium text-ink-muted">
                        source: {risk.source}
                      </span>
                    )
                  )}
                </div>
              </div>
            </div>
          ))
        ) : (
          <EmptySlot />
        )}
      </div>

      {/* ── Sources (Tavily) ─────────────────────────────────────────────── */}
      {sources.length > 0 && (
        <div className="rounded-xl border border-brand-border bg-white p-4 shadow-card">
          <p className="mb-3 border-l-2 border-brand-muted pl-2 text-xs font-semibold uppercase tracking-[0.07em] text-brand">
            Sources tendances & risques
          </p>
          <div className="grid grid-cols-1 gap-2">
            {sources.map((src, idx) => {
              const url = toUrlOrNull(src?.url);
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
