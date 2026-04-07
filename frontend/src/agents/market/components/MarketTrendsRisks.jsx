function isNonEmptyArray(value) {
  return Array.isArray(value) && value.length > 0;
}

function MarketSectionEmpty() {
  return (
    <span className="mt-2 inline-block rounded-lg border border-dashed border-gray-200 bg-gray-50 px-3 py-2 text-xs italic text-gray-400">
      Data non disponible
    </span>
  );
}

function TrendCard({ title, items, dotClass }) {
  const hasItems = isNonEmptyArray(items);
  return (
    <div className="mb-4 rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
      <div className="mb-3 flex items-center gap-2 text-sm font-bold text-gray-800">
        {title}
        {hasItems ? (
          <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
            {items?.length}
          </span>
        ) : null}
      </div>
      {hasItems ? (
        items?.map((item, idx) => (
          <div
            key={`${title}-${idx}`}
            className="flex items-start gap-2 border-b border-gray-50 py-2 last:border-0"
          >
            <span className={`mt-1.5 h-2 w-2 flex-shrink-0 rounded-full ${dotClass}`} />
            <p className="text-sm leading-relaxed text-gray-600">{item}</p>
          </div>
        ))
      ) : (
        <MarketSectionEmpty />
      )}
    </div>
  );
}

export default function MarketTrendsRisks({ trends }) {
  const insightsFr = trends?.insights_fr;
  const marketTrends = trends?.market_trends;
  const consumerTrends = trends?.consumer_trends;
  const technologyTrends = trends?.technology_trends;
  const regulatoryTrends = trends?.regulatory_trends;
  const emergingOpportunities = trends?.emerging_opportunities;
  const marketRisks = trends?.market_risks;

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-2xl border border-violet-100 bg-white p-5 shadow-sm">
        <div className="mb-3 text-sm font-bold text-gray-800">Insights FR</div>
        {isNonEmptyArray(insightsFr) ? (
          insightsFr?.map((insight, idx) => (
            <div
              key={`insight-${idx}`}
              className="mb-3 rounded-xl border-l-4 border-violet-400 bg-violet-50 p-4"
            >
              <div className="flex items-start gap-3">
                <span className="font-serif text-3xl leading-none text-violet-200">&quot;</span>
                <p className="text-sm font-medium leading-relaxed text-gray-700">{insight}</p>
              </div>
            </div>
          ))
        ) : (
          <MarketSectionEmpty />
        )}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <TrendCard title="Tendances marché" items={marketTrends} dotClass="bg-violet-500" />
          <TrendCard
            title="Tendances consommateurs"
            items={consumerTrends}
            dotClass="bg-blue-500"
          />
          <TrendCard
            title="Tendances technologiques"
            items={technologyTrends}
            dotClass="bg-amber-500"
          />
        </div>
        <div>
          <TrendCard
            title="Tendances réglementaires"
            items={regulatoryTrends}
            dotClass="bg-orange-500"
          />
          <TrendCard
            title="Opportunités émergentes"
            items={emergingOpportunities}
            dotClass="bg-emerald-500"
          />
        </div>
      </div>

      <div className="rounded-2xl border border-red-100 bg-red-50 p-5">
        <div className="mb-3 text-sm font-bold text-gray-800">Risques marché</div>
        {isNonEmptyArray(marketRisks) ? (
          marketRisks?.map((risk, idx) => (
            <div
              key={`risk-${idx}`}
              className="mb-2 flex items-start gap-3 rounded-lg border-b border-red-100 bg-white px-3 py-2 last:border-0"
            >
              <span className="flex-shrink-0 text-base text-amber-500">⚠</span>
              <p className="text-sm leading-relaxed text-gray-700">{risk}</p>
            </div>
          ))
        ) : (
          <MarketSectionEmpty />
        )}
      </div>
    </div>
  );
}
