import {
  HiCheckBadge,
  HiChartBarSquare,
  HiChatBubbleLeftRight,
  HiGlobeAlt,
  HiMagnifyingGlass,
  HiMap,
  HiNewspaper,
  HiPresentationChartLine,
  HiServerStack,
} from "react-icons/hi2";

const SOURCE_META = {
  google_trends: {
    title: "Google Trends",
    description: "Direction tendance, requêtes montantes, score viral",
    details: "signal: MEDIUM · pic: juin 2025",
    icon: HiPresentationChartLine,
  },
  reddit_via_tavily: {
    title: "Reddit via Tavily",
    description: "Verbatims utilisateurs, pain points et frustrations",
    details: "VOC · 3 citations clés",
    icon: HiChatBubbleLeftRight,
  },
  tavily: {
    title: "Tavily Search",
    description: "Faiblesses concurrents, comparatifs produits",
    details: "4 concurrents analysés",
    icon: HiMagnifyingGlass,
  },
  serpapi_search: {
    title: "SerpAPI",
    description: "Résultats organiques, positionnement et URLs concurrents",
    details: "Search + Maps",
    icon: HiGlobeAlt,
  },
  worldbank: {
    title: "World Bank API",
    description: "Données macro officielles: PIB, population, internet",
    details: "Géo: US · 6 indicateurs",
    icon: HiChartBarSquare,
  },
  gnews: {
    title: "GNews + YouTube",
    description: "Signaux d'actualité récents et contenus vidéo sectoriels",
    details: "2 signaux news",
    icon: HiNewspaper,
  },
};

function statusDot(status) {
  if (status === "api") return "bg-emerald-500";
  if (status === "llm_inference") return "bg-violet-500";
  if (status === "desactive") return "bg-slate-400";
  return "bg-slate-400";
}

function statusLabel(status) {
  if (status === "api") return "api";
  if (status === "llm_inference") return "llm";
  if (status === "desactive") return "désactivé";
  return status || "-";
}

function prettySourceName(src) {
  return SOURCE_META[src]?.title || src.replaceAll("_", " ");
}

export default function SourcesTab({ report }) {
  const sources = report?.meta?.sources || [];
  const dq = report?.dataQuality || {};
  const sections = dq?.sections || {};
  const macro = report?.marketVoc?.macro || {};
  const formatInt = (value) =>
    value != null
      ? new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 }).format(value)
      : "-";
  const formatPercent = (value) =>
    value != null
      ? `${new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 }).format(value)}%`
      : "-";
  const formatUsd = (value) =>
    value != null
      ? `$${new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value)}`
      : "-";
  const formatNumber = (value) =>
    value != null
      ? new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 2 }).format(value)
      : "-";
  const macroRows = [
    { label: "Population", value: formatInt(macro.population) },
    { label: "PIB / habitant", value: formatUsd(macro.gdp_per_capita) },
    { label: "Internet", value: formatPercent(macro.internet_pct) },
    { label: "Mobile / 100 hab.", value: formatNumber(macro.mobile_per100) },
    { label: "Urbanisation", value: formatPercent(macro.urban_pct) },
    { label: "Part 15-64 ans", value: formatPercent(macro.youth_pct) },
  ];

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-[#e8e4ff] bg-white p-4 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-3">
            <div className="border-r border-[#ebe8ff] pr-3">
              <p className="text-xs font-bold uppercase tracking-[0.07em] text-[#a09bc6]">Score qualité</p>
              <p className="mt-1 text-3xl font-extrabold leading-none text-[#4f45c8]">
                {dq?.score_global ?? "-"}
              </p>
            </div>
            <p className="max-w-[560px] text-sm leading-relaxed text-[#5f5a84]">
              Toutes les sections clés couvertes par données API vérifiables. Personas et
              faiblesses concurrentes inférées par LLM depuis données brutes.
            </p>
          </div>
          <div className="flex flex-wrap gap-1.5 text-xs font-semibold">
            <span className="rounded-full bg-emerald-50 px-2 py-0.5 text-emerald-700">API vérifiable</span>
            <span className="rounded-full bg-violet-50 px-2 py-0.5 text-violet-700">Inféré LLM</span>
            <span className="rounded-full bg-slate-100 px-2 py-0.5 text-slate-600">Désactivé</span>
          </div>
        </div>
      </div>

      <div>
        <p className="mb-2 inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-[0.07em] text-[#5f57b3]">
          <HiServerStack className="h-3.5 w-3.5" />
          {sources.length} sources utilisées
        </p>
        <div className="grid gap-2 md:grid-cols-2">
          {sources.map((src) => {
            const meta = SOURCE_META[src] || null;
            const Icon = meta?.icon || HiGlobeAlt;
            return (
              <div key={src} className="rounded-xl border border-[#e8e4ff] bg-white p-3 shadow-sm">
                <div className="flex gap-3">
                  <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-[#f2f0ff]">
                    <Icon className="h-4 w-4 text-[#5e56ad]" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-lg font-semibold leading-tight text-[#2f285c]">
                      {prettySourceName(src)}
                    </p>
                    <p className="mt-0.5 text-sm text-[#5f5a84]">
                      {meta?.description || "Source de données utilisée dans cette analyse."}
                    </p>
                    <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
                      <span className="rounded-full bg-emerald-50 px-2 py-0.5 font-semibold text-emerald-700">
                        API directe
                      </span>
                      <span className="text-[#9a96bf]">{meta?.details || src}</span>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div>
        <p className="mb-2 inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-[0.07em] text-[#5f57b3]">
          <HiCheckBadge className="h-3.5 w-3.5" />
          Qualité par section
        </p>
        <div className="grid gap-2 md:grid-cols-3">
          {Object.entries(sections).map(([sectionName, sectionData]) => (
            <div key={sectionName} className="rounded-xl border border-[#e8e4ff] bg-white p-3 shadow-sm">
              <p className="mb-2 text-base font-semibold leading-tight text-[#2f285c]">
                {sectionName}
              </p>
              <div className="space-y-1.5">
                {Object.entries(sectionData || {}).map(([k, v]) => (
                  <div key={k} className="flex items-center justify-between gap-2 text-sm">
                    <span className="text-[#5f5a84]">{k.replaceAll("_", " ")}</span>
                    <span className="inline-flex items-center gap-1.5">
                      <span className={`inline-block h-2 w-2 rounded-full ${statusDot(v?.status)}`} />
                      <span className="rounded-full bg-[#f5f3ff] px-2 py-0.5 text-xs font-semibold text-[#5b53a9]">
                        {statusLabel(v?.status)}{v?.count ? ` · ${v.count}` : ""}
                      </span>
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div>
        <p className="mb-2 inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-[0.07em] text-[#5f57b3]">
          <HiMap className="h-3.5 w-3.5" />
          Contexte macro — {report?.meta?.geo || "N/A"}
        </p>
        <div className="grid gap-2 md:grid-cols-3">
          {macroRows.map((item) => (
            <div key={item.label} className="rounded-xl border border-[#e8e4ff] bg-white p-3 shadow-sm">
              <p className="text-lg font-semibold leading-tight text-[#2f285c]">{item.value}</p>
              <p className="mt-0.5 text-xs text-[#9a96bf]">{item.label}</p>
            </div>
          ))}
        </div>
      </div>

      <div className="rounded-xl border border-[#e8e4ff] bg-white px-3 py-2 text-xs text-[#6f6a97]">
        <div className="mb-1 flex items-center gap-2">
          <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
          Donnée extraite directement via API — vérifiable
          <span className="ml-3 inline-block h-2 w-2 rounded-full bg-violet-500" />
          Inférée par LLM depuis données brutes
        </div>
        <div>
          <span className="inline-block h-2 w-2 rounded-full bg-slate-400" /> Source désactivée dans cette version
        </div>
      </div>
      <div className="hidden">
        {sources.map((src) => (
          <div key={src} className="rounded-lg border border-[#e8e4ff] bg-white px-3 py-2 text-sm text-[#5f5a84]">
            {src}
          </div>
        ))}
      </div>
    </div>
  );
}

