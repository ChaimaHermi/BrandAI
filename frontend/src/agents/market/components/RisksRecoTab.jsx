import {
  HiLightBulb,
  HiShieldExclamation,
} from "react-icons/hi2";

function riskUi(type) {
  const t = String(type || "").toLowerCase();
  if (t.includes("reg")) {
    return {
      label: "RÉGLEMENTAIRE",
      border: "border-blue-500",
      titleColor: "text-blue-700 dark:text-blue-300",
    };
  }
  if (t.includes("conc")) {
    return {
      label: "CONCURRENTIEL",
      border: "border-rose-500",
      titleColor: "text-rose-700 dark:text-rose-300",
    };
  }
  return {
    label: "MACRO",
    border: "border-amber-500",
    titleColor: "text-amber-700 dark:text-amber-300",
  };
}

function probabilityBadge(prob) {
  const p = String(prob || "").toLowerCase();
  if (p.includes("elev")) return "bg-rose-100 text-rose-700 dark:bg-rose-900/60 dark:text-rose-300";
  if (p.includes("moy")) return "bg-amber-100 text-amber-700 dark:bg-amber-900/60 dark:text-amber-300";
  if (p.includes("faib")) return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/60 dark:text-emerald-300";
  return "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200";
}

function horizonBadge(horizon) {
  const h = String(horizon || "").toLowerCase();
  if (h.includes("court")) return "bg-rose-100 text-rose-700 dark:bg-rose-900/60 dark:text-rose-300";
  if (h.includes("moyen")) return "bg-amber-100 text-amber-700 dark:bg-amber-900/60 dark:text-amber-300";
  if (h.includes("long")) return "bg-blue-100 text-blue-700 dark:bg-blue-900/60 dark:text-blue-300";
  return "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200";
}

export default function RisksRecoTab({ report }) {
  const risques = report?.risques || [];
  const recos = report?.recommandations || [];

  return (
    <div className="space-y-3">
      <div className="space-y-2">
        <p className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.06em] text-slate-500 dark:text-slate-400">
          <HiShieldExclamation className="h-3.5 w-3.5" />
          Risques identifiés
        </p>
        {risques.map((risk, idx) => (
          <div
            key={`${risk.type}-${idx}`}
            className={`rounded-xl border border-slate-200 border-l-4 bg-white p-3 dark:border-slate-700 ${riskUi(risk.type).border}`}
          >
            {(() => {
              const ui = riskUi(risk.type);
              return (
                <div className="min-w-0">
                  <p className={`text-[11px] font-semibold uppercase tracking-[0.06em] ${ui.titleColor}`}>{ui.label}</p>
                  <p className="mt-0.5 text-[15px] font-semibold leading-snug text-slate-900 dark:text-slate-100">{risk.cause || "-"}</p>
                  <p className="mt-1 text-[13px] text-slate-600 dark:text-slate-300">
                    Mitigation : {risk.mitigation || risk.impact || "-"}
                  </p>
                  <span className={`mt-1.5 inline-flex rounded-full px-2 py-0.5 text-[11px] font-semibold ${probabilityBadge(risk.probabilite)}`}>
                    probabilité: {String(risk.probabilite || "-").replaceAll("_", " ")}
                  </span>
                </div>
              );
            })()}
          </div>
        ))}
      </div>

      <div className="space-y-2">
        <p className="inline-flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.06em] text-slate-500 dark:text-slate-400">
          <HiLightBulb className="h-3.5 w-3.5" />
          Recommandations
        </p>
        {recos.map((reco, idx) => (
          <div key={`${reco.action}-${idx}`} className="rounded-xl border border-slate-200 bg-white p-3 dark:border-slate-700 dark:bg-slate-900">
            <div className="min-w-0">
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <span className={`rounded-md px-2 py-0.5 text-[11px] font-semibold uppercase ${horizonBadge(reco.horizon)}`}>
                  {String(reco.horizon || "-").replaceAll("_", " ")}
                </span>
              </div>
              <p className="text-[15px] font-semibold leading-snug text-slate-900 dark:text-slate-100">{reco.action || "-"}</p>
              <p className="mt-1 text-[13px] text-slate-600 dark:text-slate-300">
                Impact : {reco.impact_attendu || "-"}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

