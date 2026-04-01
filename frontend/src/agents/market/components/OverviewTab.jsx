import {
  HiArrowTrendingUp,
  HiCalendarDays,
  HiChevronRight,
  HiHashtag,
  HiSignal,
} from "react-icons/hi2";

function indicatorTone(niveau = "") {
  const v = String(niveau).toLowerCase();
  if (v.includes("fort") || v.includes("hausse")) return "text-emerald-700 dark:text-emerald-300";
  if (v.includes("important") || v.includes("critique") || v.includes("tres")) return "text-rose-700 dark:text-rose-300";
  if (v.includes("mod") || v.includes("partiel") || v.includes("discute")) return "text-amber-700 dark:text-amber-300";
  return "text-blue-700 dark:text-blue-300";
}

function IndicatorCard({ title, item = {} }) {
  const tone = indicatorTone(item?.niveau);
  return (
    <div className="rounded-2xl border border-slate-300 bg-slate-100 p-4 dark:border-slate-700 dark:bg-slate-800">
      <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-blue-600 dark:text-blue-300">
        {title}
      </p>
      <p className={`mt-2 text-3xl font-semibold leading-none ${tone}`}>
        {item?.niveau || "-"}
      </p>
      <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">{item?.label || "-"}</p>
    </div>
  );
}

function formatInt(value) {
  if (value == null) return "-";
  return new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 }).format(value);
}

function formatPercent(value) {
  if (value == null) return "-";
  return `${new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 1 }).format(value)}%`;
}

export default function OverviewTab({ report }) {
  const overview = report?.overview || {};
  const tendances = report?.tendances || {};
  const macro = report?.marketVoc?.macro || {};
  const risingQueries = tendances?.risingQueries || [];
  const newsSignals = tendances?.newsSignals || [];

  const macroItems = [
    { label: "Population", value: formatInt(macro.population) },
    { label: "Internet", value: formatPercent(macro.internet_pct) },
    { label: "Mobile / 100 hab.", value: formatInt(macro.mobile_per100) },
  ];

  return (
    <div className="space-y-4">
      <div className="rounded-xl border-l-2 border-blue-500 bg-slate-200/80 p-4 dark:border-blue-400 dark:bg-slate-800">
        <p className="text-[15px] font-semibold uppercase tracking-[0.05em] text-blue-600 dark:text-blue-300">
          Synthèse stratégique
        </p>
        <p className="mt-2 text-[15px] leading-relaxed text-slate-800 dark:text-slate-100">
          {report?.executiveSummary || "Résumé exécutif indisponible."}
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <IndicatorCard title="Demande" item={overview.demande} />
        <IndicatorCard title="Problème" item={overview.probleme} />
        <IndicatorCard title="Concurrence" item={overview.concurrence} />
        <IndicatorCard title="Tendance" item={overview.tendance} />
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-slate-500 dark:text-slate-400">
          Signaux tendance
        </p>

        <div className="mt-3 grid gap-2 border-b border-slate-200 pb-3 md:grid-cols-3 dark:border-slate-700">
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800">
            <div className="mb-1 flex items-center gap-1.5 text-[11px] font-semibold text-slate-500 dark:text-slate-400">
              <HiArrowTrendingUp className="h-3.5 w-3.5" />
              Direction
            </div>
            <div className="text-lg font-semibold leading-none text-slate-900 dark:text-slate-100">
              {tendances.direction || "-"}
            </div>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800">
            <div className="mb-1 flex items-center gap-1.5 text-[11px] font-semibold text-slate-500 dark:text-slate-400">
              <HiSignal className="h-3.5 w-3.5" />
              Signal
            </div>
            <div className="text-lg font-semibold leading-none text-slate-900 dark:text-slate-100">
              {tendances.signalStrength || "-"}
            </div>
          </div>
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-3 dark:border-slate-700 dark:bg-slate-800">
            <div className="mb-1 flex items-center gap-1.5 text-[11px] font-semibold text-slate-500 dark:text-slate-400">
              <HiCalendarDays className="h-3.5 w-3.5" />
              Pic
            </div>
            <div className="text-lg font-semibold leading-none text-slate-900 dark:text-slate-100">
              {tendances.peakPeriod || "-"}
            </div>
          </div>
        </div>

        <div className="mt-3 border-b border-slate-200 pb-3 dark:border-slate-700">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.06em] text-slate-500 dark:text-slate-400">
            Requêtes montantes
          </p>
          <div className="flex flex-wrap gap-1.5">
            {risingQueries.length > 0 ? (
              risingQueries.slice(0, 8).map((query, idx) => (
                <span
                  key={`${query}-${idx}`}
                  className="rounded-full border border-blue-200 bg-blue-50 px-2 py-0.5 text-xs font-semibold text-blue-700 dark:border-blue-900 dark:bg-blue-950/40 dark:text-blue-300"
                >
                  {query}
                </span>
              ))
            ) : (
              <span className="text-sm text-slate-500 dark:text-slate-400">Aucune requête montante disponible.</span>
            )}
          </div>
        </div>

        <div className="mt-3">
          <p className="mb-2 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.06em] text-slate-500 dark:text-slate-400">
            <HiHashtag className="h-3.5 w-3.5" />
            Signaux news
          </p>
          <div className="space-y-1.5">
            {newsSignals.length > 0 ? (
              newsSignals.slice(0, 6).map((signal, idx) => (
                <p key={`${signal}-${idx}`} className="flex items-start gap-1.5 text-sm text-slate-700 dark:text-slate-300">
                  <HiChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-blue-600 dark:text-blue-300" />
                  <span>{signal}</span>
                </p>
              ))
            ) : (
              <p className="text-sm text-slate-500 dark:text-slate-400">Aucun signal news disponible.</p>
            )}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-slate-500 dark:text-slate-400">
          Métriques macro
        </p>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          {macroItems.map((item) => (
            <div
              key={item.label}
              className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800"
            >
              <p className="text-2xl font-semibold text-slate-900 dark:text-slate-100">{item.value}</p>
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">{item.label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

