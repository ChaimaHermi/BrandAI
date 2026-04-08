import { FiGlobe, FiTag, FiUsers, FiZap, FiAlertCircle, FiBarChart2 } from "react-icons/fi";

export default function MarketDashboardHeader({ clarified_idea, competitorsCount }) {
  const countryCode         = clarified_idea?.country_code || "";
  const sector              = clarified_idea?.sector || "";
  const shortPitch          = clarified_idea?.short_pitch || "—";
  const problem             = clarified_idea?.problem || "—";
  const country             = clarified_idea?.country || "—";
  const targetUsers         = clarified_idea?.target_users || "—";
  const solutionDescription = clarified_idea?.solution_description || "—";

  return (
    <div className="rounded-2xl bg-gradient-to-br from-brand to-brand-darker text-white shadow-card-md">
      {/* ── Top section ───────────────────────────────────────────────────── */}
      <div className="px-5 pb-4 pt-5">
        {/* Meta pills */}
        <div className="mb-3 flex flex-wrap items-center gap-2">
          {countryCode && (
            <span className="inline-flex items-center gap-1 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold text-white/90 backdrop-blur-sm">
              <FiGlobe size={11} />
              {countryCode} · {country}
            </span>
          )}
          {sector && (
            <span className="inline-flex items-center gap-1 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold text-white/90 backdrop-blur-sm">
              <FiTag size={11} />
              {sector}
            </span>
          )}
          {competitorsCount > 0 && (
            <span className="inline-flex items-center gap-1 rounded-full bg-white/15 px-3 py-1 text-xs font-semibold text-white/90 backdrop-blur-sm">
              <FiBarChart2 size={11} />
              {competitorsCount} compétiteurs
            </span>
          )}
        </div>

        {/* Short pitch */}
        <h1 className="text-lg font-bold leading-snug text-white sm:text-xl">{shortPitch}</h1>

        {/* Problem */}
        <p className="mt-2 flex items-start gap-1.5 text-sm text-white/75">
          <FiAlertCircle size={14} className="mt-0.5 shrink-0 opacity-70" />
          <span>{problem}</span>
        </p>
      </div>

      {/* ── Bottom detail row — responsive: 1 col on mobile, 2 on md+ ─────── */}
      <div className="grid grid-cols-1 divide-y divide-white/10 border-t border-white/10 md:grid-cols-2 md:divide-x md:divide-y-0">
        <div className="flex items-start gap-3 px-5 py-4">
          <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/15">
            <FiUsers size={13} className="text-white" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-2xs font-semibold uppercase tracking-widest text-white/50">Cible</p>
            <p className="mt-0.5 line-clamp-3 text-sm font-medium leading-snug text-white/90">{targetUsers}</p>
          </div>
        </div>
        <div className="flex items-start gap-3 px-5 py-4">
          <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/15">
            <FiZap size={13} className="text-white" />
          </span>
          <div className="min-w-0 flex-1">
            <p className="text-2xs font-semibold uppercase tracking-widest text-white/50">Solution</p>
            <p className="mt-0.5 line-clamp-3 text-sm font-medium leading-snug text-white/90">{solutionDescription}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
