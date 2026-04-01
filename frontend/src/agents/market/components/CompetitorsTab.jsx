import {
  HiBuildingOffice2,
  HiLightBulb,
  HiLink,
} from "react-icons/hi2";

function normalizeUrl(url) {
  if (!url) return "";
  if (url.startsWith("http://") || url.startsWith("https://")) return url;
  return `https://${url}`;
}

function hostLabel(url) {
  try {
    return new URL(normalizeUrl(url)).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function limitItems(items, max = 4) {
  const list = Array.isArray(items) ? items.filter(Boolean) : [];
  return {
    shown: list.slice(0, max),
    remaining: Math.max(0, list.length - max),
  };
}

function typeBadge(type) {
  const t = String(type || "").toLowerCase();
  if (t.includes("international")) {
    return "bg-blue-100 text-blue-700 dark:bg-blue-900/60 dark:text-blue-300";
  }
  return "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200";
}

export default function CompetitorsTab({ report }) {
  const competitors = report?.competitor?.topCompetitors || [];
  const opportunityLevel = report?.competitor?.opportunityLevel || "-";
  const opportunitySummary = report?.competitor?.opportunitySummary || "-";

  return (
    <div className="space-y-4">
      <p className="text-xs font-semibold uppercase tracking-[0.06em] text-slate-500 dark:text-slate-400">
        {competitors.length} concurrents analysés
      </p>

      <div className="space-y-3">
        {competitors.map((c, idx) => {
          const strengths = limitItems(c.key_strengths, 4);
          const weaknesses = limitItems(c.weaknesses, 4);

          return (
            <div key={`${c.nom}-${idx}`} className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
              <div className="mb-2 flex items-center justify-between gap-2">
                <p className="flex items-center gap-1.5 text-base font-semibold leading-tight text-slate-900 dark:text-slate-100">
                  <HiBuildingOffice2 className="h-4 w-4 text-slate-500 dark:text-slate-400" />
                  {c.nom || "Concurrent"}
                </p>
                <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${typeBadge(c.type)}`}>{c.type}</span>
              </div>

              <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
                {c.website ? (
                  <a
                    href={normalizeUrl(c.website)}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 font-medium text-blue-700 underline-offset-2 hover:underline dark:text-blue-300"
                  >
                    <HiLink className="h-3.5 w-3.5" />
                    {hostLabel(c.website)}
                  </a>
                ) : null}
              </div>

              {c.description ? (
                <p className="line-clamp-2 text-sm text-slate-700 dark:text-slate-300">{c.description}</p>
              ) : null}

              <div className="mt-3">
                <p className="mb-1 text-xs font-semibold uppercase tracking-[0.06em] text-emerald-700 dark:text-emerald-300">Forces</p>
                <div className="flex flex-wrap gap-1.5">
                  {strengths.shown.length > 0 ? (
                    strengths.shown.map((s, i) => (
                      <span key={i} className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-900/60 dark:text-emerald-300">
                        {s}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-500 dark:text-slate-400">Aucune force explicite</span>
                  )}
                </div>
              </div>

              <div className="mt-2.5">
                <p className="mb-1 text-xs font-semibold uppercase tracking-[0.06em] text-rose-700 dark:text-rose-300">Faiblesses</p>
                <div className="flex flex-wrap gap-1.5">
                  {weaknesses.shown.length > 0 ? (
                    weaknesses.shown.map((w, i) => (
                      <span key={i} className="rounded-full bg-rose-100 px-2 py-0.5 text-xs font-semibold text-rose-700 dark:bg-rose-900/60 dark:text-rose-300">
                        {w}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-500 dark:text-slate-400">Aucune faiblesse explicite</span>
                  )}
                </div>
              </div>

            </div>
          );
        })}
      </div>

      <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 dark:border-emerald-900 dark:bg-emerald-950/30">
        <p className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.06em] text-emerald-700 dark:text-emerald-300">
          <HiLightBulb className="h-3.5 w-3.5" />
          Opportunité identifiée
        </p>
        <p className="mt-2 text-sm leading-relaxed text-emerald-800 dark:text-emerald-200">{opportunitySummary}</p>
        <span className="mt-2 inline-flex rounded-full bg-white px-2 py-0.5 text-xs font-semibold text-emerald-700 dark:bg-emerald-900/60 dark:text-emerald-300">
          opportunité {String(opportunityLevel).replaceAll("_", " ")}
        </span>
      </div>
    </div>
  );
}

