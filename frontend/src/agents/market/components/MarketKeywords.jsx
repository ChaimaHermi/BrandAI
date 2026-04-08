function isNonEmptyArray(value) {
  return Array.isArray(value) && value.length > 0;
}

function MarketEmptyState() {
  return (
    <span className="mt-2 inline-block rounded-lg border border-dashed border-gray-200 bg-gray-50 px-3 py-2 text-xs italic text-gray-400">
      Data non disponible
    </span>
  );
}

export default function MarketKeywords({ keywords }) {
  const groups = [
    {
      key: "primary_keywords",
      title: "Mots-clés primaires",
      items: keywords?.primary_keywords,
      pillClass: "bg-violet-100 text-violet-700",
    },
    {
      key: "market_keywords",
      title: "Mots-clés marché",
      items: keywords?.market_keywords,
      pillClass: "bg-blue-100 text-blue-700",
    },
    {
      key: "competitor_queries",
      title: "Requêtes compétiteurs",
      items: keywords?.competitor_queries,
      pillClass: "bg-rose-100 text-rose-700",
    },
    {
      key: "voc_keywords",
      title: "Mots-clés VOC",
      items: keywords?.voc_keywords,
      pillClass: "bg-orange-100 text-orange-700",
    },
    {
      key: "trend_keywords",
      title: "Mots-clés tendances",
      items: keywords?.trend_keywords,
      pillClass: "bg-gray-100 text-gray-600",
    },
  ];

  return (
    <div className="flex flex-col gap-4">
      <div className="grid grid-cols-3 gap-4">
        {groups.map((group) => (
          <div
            key={group.key}
            className="rounded-2xl border border-gray-100 bg-white p-5 shadow-sm"
          >
            <div className="mb-3 flex items-center text-sm font-bold text-gray-800">
              {group.title}
              <span className="ml-2 rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-500">
                {group.items?.length ?? 0}
              </span>
            </div>
            {isNonEmptyArray(group.items) ? (
              <div>
                {group.items?.map((item, idx) => (
                  <span
                    key={`${group.key}-${idx}`}
                    className={`m-1 inline-block rounded-full px-3 py-1 text-xs font-medium ${group.pillClass}`}
                  >
                    {item}
                  </span>
                ))}
              </div>
            ) : (
              <MarketEmptyState />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
