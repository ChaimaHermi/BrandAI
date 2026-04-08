import {
  FiBarChart2, FiUsers, FiCpu, FiShield, FiStar, FiAlertTriangle,
} from "react-icons/fi";

function isNonEmptyArray(v) {
  return Array.isArray(v) && v.length > 0;
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
            <p className="text-sm leading-relaxed text-ink-body">{item}</p>
          </div>
        ))
      ) : (
        <EmptySlot />
      )}
    </div>
  );
}

export default function MarketTrendsRisks({ trends }) {
  const marketTrends       = trends?.market_trends;
  const consumerTrends     = trends?.consumer_trends;
  const technologyTrends   = trends?.technology_trends;
  const regulatoryTrends   = trends?.regulatory_trends;
  const emergingOpportunities = trends?.emerging_opportunities;
  const marketRisks        = trends?.market_risks;

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
              <p className="text-sm leading-relaxed text-ink-body">{risk}</p>
            </div>
          ))
        ) : (
          <EmptySlot />
        )}
      </div>
    </div>
  );
}
