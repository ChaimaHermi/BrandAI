import {
  HiArrowTrendingUp,
  HiCalendarDays,
  HiChartBarSquare,
  HiChevronRight,
  HiExclamationTriangle,
  HiFire,
  HiHashtag,
  HiSignal,
} from "react-icons/hi2";

function KpiCard({ title, item = {}, icon: Icon, tone = "violet" }) {
  const toneMap = {
    emerald: {
      dot: "bg-emerald-500",
      text: "text-emerald-700",
      badge: "bg-emerald-50 text-emerald-700",
      border: "border-emerald-100",
    },
    rose: {
      dot: "bg-rose-500",
      text: "text-rose-700",
      badge: "bg-rose-50 text-rose-700",
      border: "border-rose-100",
    },
    amber: {
      dot: "bg-amber-500",
      text: "text-amber-700",
      badge: "bg-amber-50 text-amber-700",
      border: "border-amber-100",
    },
    blue: {
      dot: "bg-blue-500",
      text: "text-blue-700",
      badge: "bg-blue-50 text-blue-700",
      border: "border-blue-100",
    },
    violet: {
      dot: "bg-violet-500",
      text: "text-violet-700",
      badge: "bg-violet-50 text-violet-700",
      border: "border-violet-100",
    },
  };
  const toneUi = toneMap[tone] || toneMap.violet;

  return (
    <div className={`rounded-xl border bg-white p-3 shadow-sm ${toneUi.border}`}>
      <div className="mb-1 flex items-center justify-between">
        <p className="text-[11px] font-medium uppercase tracking-[0.08em] text-[#a09bc6]">{title}</p>
        {Icon ? <Icon className={`h-4 w-4 ${toneUi.text}`} /> : null}
      </div>
      <div className="mb-1 flex items-center gap-2">
        <span className={`inline-block h-2 w-2 rounded-full ${toneUi.dot}`} />
        <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${toneUi.badge}`}>
          {item?.niveau || "-"}
        </span>
      </div>
      <p className="text-[13px] font-normal leading-[1.6] text-[#5f5a84]">{item?.label || "-"}</p>
    </div>
  );
}

export default function OverviewTab({ report }) {
  const overview = report?.overview || {};
  const tendances = report?.tendances || {};
  const risingQueries = tendances?.risingQueries || [];
  const newsSignals = tendances?.newsSignals || [];

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-[#e8e4ff] bg-white p-4 text-[#4f4a75] shadow-sm">
        <div className="border-l-2 border-[#6a60d8] pl-3 text-[15px] leading-none text-[#6a60d8]">"</div>
        <p className="-mt-2 pl-3 text-[13px] font-normal leading-[1.6] text-[#4f4a75]">
          {report?.executiveSummary || "Résumé exécutif indisponible."}
        </p>
      </div>

      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
        <KpiCard title="Demande" item={overview.demande} icon={HiFire} tone="emerald" />
        <KpiCard title="Problème" item={overview.probleme} icon={HiExclamationTriangle} tone="rose" />
        <KpiCard title="Concurrence" item={overview.concurrence} icon={HiChartBarSquare} tone="amber" />
        <KpiCard title="Tendance" item={overview.tendance} icon={HiArrowTrendingUp} tone="blue" />
      </div>

      <div className="rounded-xl border border-[#e8e4ff] bg-white p-4 shadow-sm">
        <p className="mb-3 text-[11px] font-medium uppercase tracking-[0.08em] text-[#a09bc6]">Signaux tendance</p>

        <div className="grid gap-2 border-b border-[#efecff] pb-3 md:grid-cols-3">
          <div className="rounded-lg bg-[#faf9ff] p-2.5">
            <div className="mb-1 flex items-center gap-1.5 text-[11px] font-medium text-[#8f89bb]">
              <HiArrowTrendingUp className="h-3.5 w-3.5" />
              Direction
            </div>
            <div className="text-[13px] font-medium leading-none text-[#3C3489]">{tendances.direction || "-"}</div>
          </div>
          <div className="rounded-lg bg-[#faf9ff] p-2.5">
            <div className="mb-1 flex items-center gap-1.5 text-[11px] font-medium text-[#8f89bb]">
              <HiSignal className="h-3.5 w-3.5" />
              Signal
            </div>
            <div className="text-[13px] font-medium leading-none text-[#3C3489]">{tendances.signalStrength || "-"}</div>
          </div>
          <div className="rounded-lg bg-[#faf9ff] p-2.5">
            <div className="mb-1 flex items-center gap-1.5 text-[11px] font-medium text-[#8f89bb]">
              <HiCalendarDays className="h-3.5 w-3.5" />
              Pic
            </div>
            <div className="text-[13px] font-medium leading-none text-[#3C3489]">{tendances.peakPeriod || "-"}</div>
          </div>
        </div>

        <div className="mt-3 border-b border-[#efecff] pb-3">
          <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.08em] text-[#a09bc6]">Requêtes montantes</p>
          <div className="flex flex-wrap gap-1.5">
            {risingQueries.length > 0 ? (
              risingQueries.slice(0, 8).map((query, idx) => (
                <span
                  key={`${query}-${idx}`}
                  className="rounded-full bg-violet-50 px-2 py-0.5 text-[11px] font-medium text-violet-700"
                >
                  {query}
                </span>
              ))
            ) : (
              <span className="text-[12px] font-normal text-[#8f89bb]">Aucune requête montante disponible.</span>
            )}
          </div>
        </div>

        <div className="mt-3">
          <p className="mb-2 flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.08em] text-[#a09bc6]">
            <HiHashtag className="h-3.5 w-3.5" />
            Signaux news
          </p>
          <div className="space-y-1.5">
            {newsSignals.length > 0 ? (
              newsSignals.slice(0, 6).map((signal, idx) => (
                <p key={`${signal}-${idx}`} className="flex items-start gap-1.5 text-[13px] font-normal leading-[1.6] text-[#5f5a84]">
                  <HiChevronRight className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[#7F77DD]" />
                  <span>{signal}</span>
                </p>
              ))
            ) : (
              <p className="text-[12px] font-normal text-[#8f89bb]">Aucun signal news disponible.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

