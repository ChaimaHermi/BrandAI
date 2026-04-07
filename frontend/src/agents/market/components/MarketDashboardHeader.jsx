export default function MarketDashboardHeader({
  clarified_idea,
}) {
  const countryCode = clarified_idea?.country_code || "-";
  const sector = clarified_idea?.sector || "-";
  const shortPitch = clarified_idea?.short_pitch || "—";
  const problem = clarified_idea?.problem || "—";
  const country = clarified_idea?.country || "—";
  const targetUsers = clarified_idea?.target_users || "—";
  const solutionDescription = clarified_idea?.solution_description || "—";

  return (
    <div className="rounded-2xl bg-[#1E1B4B] p-5 text-white">
      <div className="mb-3 inline-flex items-center rounded-full bg-white/15 px-3 py-1 text-xs font-semibold text-violet-100">
        {countryCode} · {sector}
      </div>
      <h1 className="text-xl font-bold leading-tight text-white">{shortPitch}</h1>
      <p className="mt-2 text-sm text-violet-100">{problem}</p>
      <div className="mt-4 flex flex-wrap gap-2">
        <span className="rounded-full bg-white/10 px-3 py-1 text-xs text-violet-100">
          Country : {country}
        </span>
        <span className="rounded-full bg-white/10 px-3 py-1 text-xs text-violet-100">
          Sector : {sector}
        </span>
        <span className="rounded-full bg-white/10 px-3 py-1 text-xs text-violet-100">
          Solution : {solutionDescription}
        </span>
        <span className="rounded-full bg-white/10 px-3 py-1 text-xs text-violet-100">
          Cible : {targetUsers}
        </span>
      </div>
    </div>
  );
}
