const FIELD_CONFIG = [
  { key: "market_size", label: "Taille du marché" },
  { key: "market_revenue", label: "Revenus 2024" },
  { key: "CAGR", label: "CAGR" },
  { key: "growth_rate", label: "Croissance" },
  { key: "number_of_users", label: "Nombre d'utilisateurs" },
  { key: "adoption_rate", label: "Taux d'adoption" },
];

export default function MarketApercu({ market }) {
  return (
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
              {source}
            </div>
          </div>
        );
      })}
    </div>
  );
}
