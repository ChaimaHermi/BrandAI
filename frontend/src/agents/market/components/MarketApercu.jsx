const FIELD_CONFIG = [
  { key: "market_size", label: "Taille du marché" },
  { key: "market_revenue", label: "Revenus 2024" },
  { key: "CAGR", label: "CAGR" },
  { key: "growth_rate", label: "Croissance" },
  { key: "number_of_users", label: "Nombre d'utilisateurs" },
  { key: "adoption_rate", label: "Taux d'adoption" },
];

function isUrlLike(value) {
  return typeof value === "string" && /^https?:\/\//i.test(value.trim());
}

export default function MarketApercu({ market }) {
  const marketSources = Array.isArray(market?.sources) ? market.sources : [];

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-3 gap-4">
        {FIELD_CONFIG.map(({ key, label }) => {
          const metric = market?.[key];
          const value = metric?.value ?? "N/D";
          const unit = metric?.unit ?? "";
          const source = metric?.source ?? "";
          const isNd = value === "N/D";

          return (
            <div
              key={key}
              className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm"
            >
              <div className="text-xs font-medium uppercase tracking-wide text-gray-400">
                {label}
              </div>
              <div className="mt-2">
                {isNd ? (
                  <span className="text-lg italic text-gray-300">N/D</span>
                ) : (
                  <span className="text-2xl font-bold text-gray-900">
                    {value}
                    <span className="ml-1 text-sm text-gray-400">{unit}</span>
                  </span>
                )}
              </div>
              <div className="mt-2 text-xs leading-relaxed text-gray-400">
                {isUrlLike(source) ? (
                  <a
                    href={source}
                    target="_blank"
                    rel="noreferrer"
                    className="text-violet-600 hover:underline"
                  >
                    Source
                  </a>
                ) : (
                  source
                )}
              </div>
            </div>
          );
        })}
      </div>

      {marketSources.length > 0 && (
        <div className="rounded-xl border border-gray-100 bg-white p-4 shadow-sm">
          <div className="mb-3 text-xs font-medium uppercase tracking-wide text-gray-400">
            Sources du marché
          </div>
          <div className="grid grid-cols-1 gap-2">
            {marketSources.map((src, idx) => {
              const url = typeof src?.url === "string" ? src.url : "";
              if (!url) return null;
              const domain = typeof src?.domain === "string" ? src.domain : "";
              return (
                <a
                  key={`${url}-${idx}`}
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  className="flex items-center justify-between rounded-lg border border-gray-100 px-3 py-2 text-sm text-gray-700 hover:bg-gray-50"
                >
                  <span className="font-medium text-gray-500">{domain || "source"}</span>
                  <span className="ml-4 truncate text-violet-700">{url}</span>
                </a>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
