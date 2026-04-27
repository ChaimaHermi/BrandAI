import { FiSearch } from "react-icons/fi";

function isNonEmptyArray(v) {
  return Array.isArray(v) && v.length > 0;
}

function EmptySlot() {
  return (
    <span className="inline-block rounded-lg border border-dashed border-brand-border bg-brand-light px-3 py-2 text-xs italic text-ink-subtle">
      Data non disponible
    </span>
  );
}

const GROUPS = [
  { key: "primary_keywords",  title: "Mots-clés primaires",    pillClass: "bg-brand-light text-brand-dark border border-brand-border" },
  { key: "market_keywords",   title: "Mots-clés marché",       pillClass: "bg-blue-50 text-blue-700 border border-blue-100" },
  { key: "sector_growth_keywords", title: "Mots-clés croissance sectorielle", pillClass: "bg-emerald-50 text-emerald-700 border border-emerald-100" },
  { key: "competitor_queries",title: "Requêtes compétiteurs",  pillClass: "bg-rose-50 text-rose-700 border border-rose-100" },
  { key: "voc_keywords",      title: "Mots-clés VOC",          pillClass: "bg-orange-50 text-orange-700 border border-orange-100" },
  { key: "trend_keywords",    title: "Mots-clés tendances",    pillClass: "bg-gray-50 text-ink-muted border border-brand-border" },
  { key: "risk_keywords",     title: "Mots-clés risques",      pillClass: "bg-red-50 text-red-700 border border-red-100" },
];

export default function MarketKeywords({ keywords }) {
  return (
    <div className="grid grid-cols-3 gap-4">
      {GROUPS.map((group) => {
        const items = keywords?.[group.key];
        const count = isNonEmptyArray(items) ? items.length : 0;
        return (
          <div
            key={group.key}
            className="rounded-2xl border border-brand-border bg-white p-5 shadow-card"
          >
            {/* Header */}
            <div className="mb-3 flex items-center gap-2">
              <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-light">
                <FiSearch size={13} className="text-brand" />
              </span>
              <p className="text-sm font-bold text-ink">{group.title}</p>
              <span className="ml-auto rounded-full bg-gray-100 px-2 py-0.5 text-xs text-ink-subtle">
                {count}
              </span>
            </div>

            {/* Pills */}
            {isNonEmptyArray(items) ? (
              <div className="flex flex-wrap gap-1.5">
                {items.map((item, idx) => (
                  <span
                    key={`${group.key}-${idx}`}
                    className={`inline-block rounded-full px-3 py-1 text-xs font-medium ${group.pillClass}`}
                  >
                    {item}
                  </span>
                ))}
              </div>
            ) : (
              <EmptySlot />
            )}
          </div>
        );
      })}
    </div>
  );
}
