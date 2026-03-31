export default function CompetitorsTab({ report }) {
  const competitors = report?.competitor?.topCompetitors || [];

  return (
    <div className="space-y-3">
      <div className="grid gap-3 md:grid-cols-2">
        {competitors.map((c, idx) => (
          <div key={`${c.nom}-${idx}`} className="rounded-lg border border-[#e8e4ff] bg-white p-3">
            <p className="font-semibold text-[#3C3489]">{c.nom}</p>
            <p className="text-sm text-[#5f5a84]">{c.description || "-"}</p>
            <div className="mt-2 flex flex-wrap gap-1">
              {(c.key_strengths || []).slice(0, 3).map((s, i) => (
                <span key={i} className="rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700">
                  {s}
                </span>
              ))}
            </div>
            <div className="mt-1 flex flex-wrap gap-1">
              {(c.weaknesses || []).slice(0, 3).map((w, i) => (
                <span key={i} className="rounded-full bg-rose-50 px-2 py-0.5 text-xs text-rose-700">
                  {w}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="rounded-lg border border-[#e8e4ff] bg-white p-4">
        <p className="text-xs font-bold uppercase tracking-[0.07em] text-[#a09bc6]">Opportunité identifiée</p>
        <p className="mt-1 text-sm text-[#5f5a84]">{report?.competitor?.opportunitySummary || "-"}</p>
      </div>
    </div>
  );
}

