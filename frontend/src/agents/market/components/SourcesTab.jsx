const SOURCE_LABELS = {
  google_trends: "Google Trends",
  tavily: "Tavily",
  tavily_weakness: "Tavily weaknesses",
  tavily_compare: "Tavily compare",
  reddit_via_tavily: "Reddit via Tavily",
  youtube: "YouTube",
  gnews: "GNews",
  worldbank: "World Bank",
  serpapi_search: "SerpAPI Search",
  serpapi_maps: "SerpAPI Maps",
};

function qualityBadge(interpretation) {
  const v = String(interpretation || "").toLowerCase();
  if (v.includes("elev")) return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/60 dark:text-emerald-300";
  if (v.includes("moy")) return "bg-amber-100 text-amber-700 dark:bg-amber-900/60 dark:text-amber-300";
  return "bg-rose-100 text-rose-700 dark:bg-rose-900/60 dark:text-rose-300";
}

function statusToReliability(status) {
  const s = String(status || "").toLowerCase();
  if (s === "llm_inference") return "llm";
  return "api";
}

function reliabilityDot(reliability) {
  return reliability === "llm"
    ? "bg-amber-500 dark:bg-amber-400"
    : "bg-emerald-600 dark:bg-emerald-400";
}

function sectionAccent(section) {
  if (section === "tendances") return "bg-blue-500 dark:bg-blue-400";
  if (section === "market_voc") return "bg-pink-500 dark:bg-pink-400";
  if (section === "competitor") return "bg-emerald-600 dark:bg-emerald-400";
  return "bg-slate-500 dark:bg-slate-400";
}

function prettySectionName(section) {
  if (section === "tendances") return "Tendances";
  if (section === "market_voc") return "Voix du marché";
  if (section === "competitor") return "Concurrents";
  return section.replaceAll("_", " ");
}

function prettyMetricName(metric) {
  return metric.replaceAll("_", " ");
}

function sourceToSection(source) {
  const s = String(source || "").toLowerCase();
  if (s.includes("trends")) return "tendances";
  if (s.includes("reddit") || s.includes("youtube") || s.includes("gnews") || s.includes("worldbank")) return "market_voc";
  if (s.includes("serpapi") || s.includes("tavily_weakness") || s.includes("tavily_compare")) return "competitor";
  if (s.includes("tavily")) return "tendances";
  return "market_voc";
}

function buildQualityStats(sections) {
  let api = 0;
  let llm = 0;
  Object.values(sections || {}).forEach((sectionData) => {
    Object.values(sectionData || {}).forEach((metricData) => {
      const reliability = statusToReliability(metricData?.status);
      if (reliability === "llm") llm += 1;
      else api += 1;
    });
  });
  return { api, llm };
}

export default function SourcesTab({ report }) {
  const sources = report?.meta?.sources || [];
  const dq = report?.dataQuality || {};
  const sections = dq?.sections || {};
  const score = dq?.score_global ?? "-";
  const interpretation = dq?.interpretation || "-";
  const stats = buildQualityStats(sections);

  const grouped = { tendances: [], market_voc: [], competitor: [] };

  sources.forEach((source) => {
    const section = sourceToSection(source);
    grouped[section].push({
      key: `source-${source}`,
      label: SOURCE_LABELS[source] || source.replaceAll("_", " "),
      reliability: "api",
    });
  });

  Object.entries(sections).forEach(([section, sectionData]) => {
    Object.entries(sectionData || {}).forEach(([metric, metricData]) => {
      grouped[section]?.push({
        key: `metric-${section}-${metric}`,
        label: `${prettyMetricName(metric)}${metricData?.count ? ` · ${metricData.count}` : ""}`,
        reliability: statusToReliability(metricData?.status),
      });
    });
  });

  return (
    <div className="space-y-4">
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-xl border border-slate-200 bg-slate-100 px-4 py-3 dark:border-slate-700 dark:bg-slate-800">
          <div className="flex items-center justify-between gap-2">
            <p className="text-4xl font-semibold leading-none text-slate-900 dark:text-slate-100">{score}</p>
            <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${qualityBadge(interpretation)}`}>
              {interpretation}
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Score qualité</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-slate-100 px-4 py-3 dark:border-slate-700 dark:bg-slate-800">
          <div className="flex items-center justify-between gap-2">
            <p className="text-4xl font-semibold leading-none text-slate-900 dark:text-slate-100">{sources.length}</p>
            <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-semibold text-blue-700 dark:bg-blue-900/60 dark:text-blue-300">
              {stats.llm === 0 ? "toutes API" : `${stats.api} API · ${stats.llm} LLM`}
            </span>
          </div>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">Sources utilisées</p>
        </div>
      </div>

      <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <p className="text-[11px] font-semibold uppercase tracking-[0.06em] text-blue-600 dark:text-blue-300">
          Sources par section
        </p>

        <div className="mt-3 space-y-4">
          {Object.entries(grouped).map(([section, items]) => (
            <div key={section} className="border-b border-slate-200 pb-3 last:border-b-0 last:pb-0 dark:border-slate-700">
              <p className="mb-2 inline-flex items-center gap-2 text-sm font-semibold text-slate-700 dark:text-slate-200">
                <span className={`h-2 w-2 rounded-full ${sectionAccent(section)}`} />
                {prettySectionName(section)}
              </p>
              <div className="flex flex-wrap gap-2">
                {items.map((item) => (
                  <span
                    key={item.key}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-slate-300 bg-slate-100 px-3 py-1 text-sm text-slate-800 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
                  >
                    <span className={`h-1.5 w-1.5 rounded-full ${reliabilityDot(item.reliability)}`} />
                    {item.label}
                  </span>
                ))}
                {items.length === 0 ? (
                  <span className="text-sm text-slate-500 dark:text-slate-400">Aucune donnée.</span>
                ) : null}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-3 flex flex-wrap gap-6 border-t border-slate-200 pt-3 text-sm text-slate-600 dark:border-slate-700 dark:text-slate-300">
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-emerald-600 dark:bg-emerald-400" />
            Donnée API vérifiable
          </span>
          <span className="inline-flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full bg-amber-500 dark:bg-amber-400" />
            Inférée par LLM
          </span>
        </div>
      </div>
    </div>
  );
}

