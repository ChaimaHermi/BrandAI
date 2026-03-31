function KpiCard({ title, item = {} }) {
  return (
    <div className="rounded-lg border border-[#e8e4ff] bg-white p-3">
      <p className="text-[11px] font-bold uppercase tracking-[0.07em] text-[#a09bc6]">{title}</p>
      <p className="mt-1 text-lg font-bold text-[#3C3489]">{item?.niveau || "-"}</p>
      <p className="text-sm text-[#5f5a84]">{item?.label || "-"}</p>
    </div>
  );
}

export default function OverviewTab({ report }) {
  const overview = report?.overview || {};
  const tendances = report?.tendances || {};

  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-[#e8e4ff] bg-white p-4 text-[#4f4a75]">
        {report?.executiveSummary || "Résumé exécutif indisponible."}
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard title="Demande" item={overview.demande} />
        <KpiCard title="Problème" item={overview.probleme} />
        <KpiCard title="Concurrence" item={overview.concurrence} />
        <KpiCard title="Tendance" item={overview.tendance} />
      </div>

      <div className="rounded-lg border border-[#e8e4ff] bg-white p-4">
        <p className="mb-2 text-xs font-bold uppercase tracking-[0.07em] text-[#a09bc6]">Signaux tendance</p>
        <div className="grid gap-2 md:grid-cols-3">
          <p className="text-sm text-[#5f5a84]">Direction: <b>{tendances.direction}</b></p>
          <p className="text-sm text-[#5f5a84]">Signal: <b>{tendances.signalStrength}</b></p>
          <p className="text-sm text-[#5f5a84]">Pic: <b>{tendances.peakPeriod}</b></p>
        </div>
      </div>
    </div>
  );
}

