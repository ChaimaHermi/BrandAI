import {
  HiBuildingOffice2,
  HiExclamationTriangle,
  HiGlobeAlt,
  HiLink,
  HiLightBulb,
  HiShieldCheck,
  HiSparkles,
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

function MetaBadge({ children }) {
  if (!children) return null;
  return (
    <span className="rounded-full bg-[#f5f3ff] px-2 py-0.5 text-[11px] font-semibold text-[#5b53a9]">
      {children}
    </span>
  );
}

export default function CompetitorsTab({ report }) {
  const competitors = report?.competitor?.topCompetitors || [];
  const opportunityLevel = report?.competitor?.opportunityLevel || "-";
  const opportunitySummary = report?.competitor?.opportunitySummary || "-";

  return (
    <div className="space-y-4">
      <p className="text-xs font-bold uppercase tracking-[0.07em] text-[#a09bc6]">
        {competitors.length} concurrents analysés
      </p>

      <div className="grid gap-3 md:grid-cols-2">
        {competitors.map((c, idx) => {
          const strengths = limitItems(c.key_strengths, 4);
          const weaknesses = limitItems(c.weaknesses, 4);

          return (
            <div key={`${c.nom}-${idx}`} className="rounded-xl border border-[#e8e4ff] bg-white p-4 shadow-sm">
              {/* Header */}
              <div className="mb-2 flex items-center justify-between gap-2">
                <p className="flex items-center gap-1.5 text-base font-semibold leading-tight text-[#2f285c]">
                  <HiBuildingOffice2 className="h-4 w-4 text-[#6a60d8]" />
                  {c.nom || "Concurrent"}
                </p>
                <MetaBadge>{c.type}</MetaBadge>
              </div>

              {/* Meta */}
              <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-[#8f89bb]">
                {c.website ? (
                  <a
                    href={normalizeUrl(c.website)}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 font-medium text-[#4d67d1] underline-offset-2 hover:underline"
                  >
                    <HiLink className="h-3.5 w-3.5" />
                    {hostLabel(c.website)}
                  </a>
                ) : null}
                {c.source ? (
                  <span className="inline-flex items-center gap-1">
                    <HiGlobeAlt className="h-3.5 w-3.5" />
                    source: {c.source}
                  </span>
                ) : null}
              </div>

              {/* Positioning + description */}
              {c.positioning ? (
                <p className="mb-1 inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.06em] text-[#4f45c8]">
                  <HiSparkles className="h-3.5 w-3.5" />
                  Positionnement
                </p>
              ) : null}
              {c.positioning ? (
                <p className="mb-1 rounded-md bg-violet-50 px-2 py-1 text-sm font-medium text-[#574fb2]">{c.positioning}</p>
              ) : null}
              {c.description ? (
                <p className="line-clamp-2 text-sm text-[#5f5a84]">{c.description}</p>
              ) : null}

              {/* Forces */}
              <div className="mt-3">
                <p className="mb-1 inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.06em] text-emerald-700">
                  <HiShieldCheck className="h-3.5 w-3.5" />
                  Forces clés
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {strengths.shown.length > 0 ? (
                    strengths.shown.map((s, i) => (
                      <span key={i} className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs font-semibold text-emerald-700">
                        {s}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-[#b0abc9]">Aucune force explicite</span>
                  )}
                  {strengths.remaining > 0 ? (
                    <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-xs font-semibold text-emerald-700">
                      +{strengths.remaining}
                    </span>
                  ) : null}
                </div>
              </div>

              {/* Weaknesses */}
              <div className="mt-2.5">
                <p className="mb-1 inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.06em] text-rose-700">
                  <HiExclamationTriangle className="h-3.5 w-3.5" />
                  Faiblesses clés
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {weaknesses.shown.length > 0 ? (
                    weaknesses.shown.map((w, i) => (
                      <span key={i} className="rounded-full bg-rose-50 px-2 py-0.5 text-xs font-semibold text-rose-700">
                        {w}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-[#b0abc9]">Aucune faiblesse explicite</span>
                  )}
                  {weaknesses.remaining > 0 ? (
                    <span className="rounded-full bg-rose-100 px-2 py-0.5 text-xs font-semibold text-rose-700">
                      +{weaknesses.remaining}
                    </span>
                  ) : null}
                </div>
              </div>

            </div>
          );
        })}
      </div>

      <div className="rounded-xl border border-[#e8e4ff] bg-white p-4 shadow-sm">
        <p className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-[0.07em] text-amber-700">
          <HiLightBulb className="h-3.5 w-3.5" />
          Opportunité identifiée
        </p>
        <p className="mt-2 text-sm leading-relaxed text-[#5f5a84]">{opportunitySummary}</p>
        <span className="mt-2 inline-flex rounded-full bg-amber-50 px-2 py-0.5 text-xs font-semibold text-amber-700">
          opportunité {String(opportunityLevel).replaceAll("_", " ")}
        </span>
      </div>
    </div>
  );
}

