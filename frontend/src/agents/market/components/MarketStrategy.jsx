function isNonEmptyArray(value) {
  return Array.isArray(value) && value.length > 0;
}

function hasText(value) {
  return typeof value === "string" && value.trim().length > 0;
}

function MarketEmptyState() {
  return (
    <span className="mt-2 inline-block rounded-lg border border-dashed border-gray-200 bg-gray-50 px-3 py-2 text-xs italic text-gray-400">
      Data non disponible
    </span>
  );
}

function MarketBulletList({ items }) {
  if (!isNonEmptyArray(items)) return <MarketEmptyState />;
  return (
    <div>
      {items?.map((item, idx) => (
        <div key={`${item}-${idx}`} className="flex items-start gap-2 py-1.5 text-sm leading-relaxed">
          <span className="text-gray-400">—</span>
          <span className="text-gray-600">{item}</span>
        </div>
      ))}
    </div>
  );
}

export default function MarketStrategy({ strategy }) {
  const pestel = strategy?.pestel;
  const swot = strategy?.swot;
  const demand = strategy?.demand_analysis;
  const insight = strategy?.strategic_insight;

  const pestelConfig = [
    {
      key: "political",
      short: "P",
      label: "Politique",
      cellClass: "bg-gray-50 border-l-4 border-gray-300",
    },
    {
      key: "economic",
      short: "E",
      label: "Économique",
      cellClass: "bg-emerald-50 border-l-4 border-emerald-400",
    },
    {
      key: "social",
      short: "S",
      label: "Social",
      cellClass: "bg-blue-50 border-l-4 border-blue-400",
    },
    {
      key: "technological",
      short: "T",
      label: "Technologique",
      cellClass: "bg-violet-50 border-l-4 border-violet-400",
    },
    {
      key: "environmental",
      short: "E",
      label: "Environnemental",
      cellClass: "bg-green-50 border-l-4 border-green-400",
    },
    {
      key: "legal",
      short: "L",
      label: "Légal",
      cellClass: "bg-orange-50 border-l-4 border-orange-400",
    },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-3 gap-4">
        <div className="rounded-2xl border border-gray-100 border-l-4 border-l-emerald-400 bg-white p-5 shadow-sm">
          <div className="mb-2 flex items-center gap-2 text-sm font-bold text-gray-800">
            <span>→</span>
            <span>Opportunité</span>
          </div>
          {hasText(insight?.opportunity) ? (
            <p className="text-sm leading-relaxed text-gray-600">{insight?.opportunity}</p>
          ) : (
            <MarketEmptyState />
          )}
        </div>

        <div className="rounded-2xl border border-gray-100 border-l-4 border-l-red-400 bg-white p-5 shadow-sm">
          <div className="mb-2 flex items-center gap-2 text-sm font-bold text-gray-800">
            <span>⚠</span>
            <span>Risque</span>
          </div>
          {hasText(insight?.risk) ? (
            <p className="text-sm leading-relaxed text-gray-600">{insight?.risk}</p>
          ) : (
            <MarketEmptyState />
          )}
        </div>

        <div className="rounded-2xl border border-gray-100 border-l-4 border-l-violet-400 bg-white p-5 shadow-sm">
          <div className="mb-2 flex items-center gap-2 text-sm font-bold text-gray-800">
            <span>✦</span>
            <span>Recommandation</span>
          </div>
          {hasText(insight?.recommendation) ? (
            <p className="text-sm leading-relaxed text-gray-600">{insight?.recommendation}</p>
          ) : (
            <MarketEmptyState />
          )}
        </div>
      </div>

      <div>
        <h2 className="mb-4 mt-6 text-base font-bold text-gray-800">Analyse SWOT</h2>
        <div className="grid grid-cols-2 gap-4">
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-5">
            <div className="mb-3 flex items-center text-sm font-bold text-gray-800">
              Forces
              <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                {swot?.strengths?.length ?? 0}
              </span>
            </div>
            <MarketBulletList items={swot?.strengths} />
          </div>

          <div className="rounded-2xl border border-red-200 bg-red-50 p-5">
            <div className="mb-3 flex items-center text-sm font-bold text-gray-800">
              Faiblesses
              <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                {swot?.weaknesses?.length ?? 0}
              </span>
            </div>
            <MarketBulletList items={swot?.weaknesses} />
          </div>

          <div className="rounded-2xl border border-blue-200 bg-blue-50 p-5">
            <div className="mb-3 flex items-center text-sm font-bold text-gray-800">
              Opportunités
              <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                {swot?.opportunities?.length ?? 0}
              </span>
            </div>
            <MarketBulletList items={swot?.opportunities} />
          </div>

          <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5">
            <div className="mb-3 flex items-center text-sm font-bold text-gray-800">
              Menaces
              <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                {swot?.threats?.length ?? 0}
              </span>
            </div>
            <MarketBulletList items={swot?.threats} />
          </div>
        </div>
      </div>

      <div>
        <h2 className="mb-4 mt-6 text-base font-bold text-gray-800">Analyse PESTEL</h2>
        <div className="grid grid-cols-3 gap-4">
          {pestelConfig.map((cfg) => (
            <div
              key={cfg.key}
              className={`relative overflow-hidden rounded-xl border p-4 ${cfg.cellClass}`}
            >
              <span className="absolute right-3 top-2 text-6xl font-black text-gray-800 opacity-5">
                {cfg.short}
              </span>
              <div className="mb-2 text-sm font-bold text-gray-800">{cfg.label}</div>
              <MarketBulletList items={pestel?.[cfg.key]} />
            </div>
          ))}
        </div>
      </div>

      <div>
        <h2 className="mb-4 mt-6 text-base font-bold text-gray-800">Analyse de la demande</h2>
        <div className="grid grid-cols-3 gap-4">
          <div className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
            <div className="mb-2 text-sm font-bold text-gray-800">Niveau de demande</div>
            {hasText(demand?.demand_level) ? (
              <span className="inline-block rounded-full bg-gray-100 px-3 py-1 text-sm text-gray-700">
                {demand?.demand_level}
              </span>
            ) : (
              <MarketEmptyState />
            )}
            <div className="mb-2 mt-4 text-sm font-bold text-gray-800">Potentiel de croissance</div>
            {hasText(demand?.growth_potential) ? (
              <p className="text-sm leading-relaxed text-gray-600">{demand?.growth_potential}</p>
            ) : (
              <MarketEmptyState />
            )}
          </div>

          <div className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
            <div className="mb-2 text-sm font-bold text-gray-800">Drivers</div>
            {isNonEmptyArray(demand?.drivers) ? (
              demand?.drivers?.map((item, idx) => (
                <div key={`${item}-${idx}`} className="flex items-start gap-2 py-1.5 text-sm">
                  <span className="mt-1.5 h-2 w-2 flex-shrink-0 rounded-full bg-emerald-500" />
                  <span className="text-gray-600">{item}</span>
                </div>
              ))
            ) : (
              <MarketEmptyState />
            )}
          </div>

          <div className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm">
            <div>
              <div className="mb-2 text-sm font-bold text-gray-800">Barrières</div>
              {isNonEmptyArray(demand?.barriers) ? (
                demand?.barriers?.map((item, idx) => (
                  <div key={`${item}-${idx}`} className="flex items-start gap-2 py-1.5 text-sm">
                    <span className="mt-1.5 h-2 w-2 flex-shrink-0 rounded-full bg-red-500" />
                    <span className="text-gray-600">{item}</span>
                  </div>
                ))
              ) : (
                <MarketEmptyState />
              )}
            </div>
            <div className="mt-4">
              <div className="mb-2 text-sm font-bold text-gray-800">Customer insights</div>
              {isNonEmptyArray(demand?.customer_insights) ? (
                demand?.customer_insights?.map((item, idx) => (
                  <div key={`${item}-${idx}`} className="flex items-start gap-2 py-1.5 text-sm">
                    <span className="mt-1.5 h-2 w-2 flex-shrink-0 rounded-full bg-blue-500" />
                    <span className="text-gray-600">{item}</span>
                  </div>
                ))
              ) : (
                <MarketEmptyState />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
