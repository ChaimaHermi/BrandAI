function readableSource(source) {
  const s = String(source || "").trim().toLowerCase();
  if (!s || s === "inference") return "";

  // Hide technical payload paths from UI.
  if (s.includes("[") || s.includes("]") || s.includes(".")) {
    if (s.startsWith("competitor")) return "analyse concurrents";
    if (s.startsWith("market_voc")) return "voix du marché";
    if (s.startsWith("tendances")) return "signaux tendances";
    if (s.startsWith("swot")) return "synthèse SWOT";
    return "";
  }

  return source;
}

function SwotColumn({ title, items = [], symbol, containerClass, textClass }) {
  return (
    <div className={`rounded-xl border p-3 ${containerClass}`}>
      <p className={`text-xs font-semibold uppercase tracking-[0.06em] ${textClass}`}>
        {title}
      </p>
      <ul className="mt-2 space-y-1.5 text-sm text-slate-700 dark:text-slate-300">
        {items.map((item, idx) => {
          const label = item.point || item;
          const src = readableSource(item?.source);
          return (
            <li key={idx} className="flex items-start gap-2">
              <span className={`mt-0.5 text-xs font-semibold ${textClass}`}>{symbol}</span>
              <span>
                {label}
              {src ? (
                <span className="ml-1 text-[11px] text-slate-500 dark:text-slate-400">[{src}]</span>
              ) : null}
              </span>
            </li>
          );
        })}
        {items.length === 0 ? (
          <li className="text-sm text-slate-500 dark:text-slate-400">
            Aucun point disponible.
          </li>
        ) : null}
      </ul>
    </div>
  );
}

export default function SwotTab({ report }) {
  const swot = report?.swot || {};

  return (
    <div className="grid gap-3 md:grid-cols-2">
      <SwotColumn
        title="Forces"
        items={swot.forces}
        symbol="+"
        containerClass="border-emerald-200 bg-emerald-50 dark:border-emerald-900 dark:bg-emerald-950/30"
        textClass="text-emerald-700 dark:text-emerald-300"
      />
      <SwotColumn
        title="Faiblesses"
        items={swot.faiblesses}
        symbol="-"
        containerClass="border-rose-200 bg-rose-50 dark:border-rose-900 dark:bg-rose-950/30"
        textClass="text-rose-700 dark:text-rose-300"
      />
      <SwotColumn
        title="Opportunités"
        items={swot.opportunites}
        symbol="→"
        containerClass="border-blue-200 bg-blue-50 dark:border-blue-900 dark:bg-blue-950/30"
        textClass="text-blue-700 dark:text-blue-300"
      />
      <SwotColumn
        title="Menaces"
        items={swot.menaces}
        symbol="!"
        containerClass="border-amber-200 bg-amber-50 dark:border-amber-900 dark:bg-amber-950/30"
        textClass="text-amber-700 dark:text-amber-300"
      />
    </div>
  );
}

