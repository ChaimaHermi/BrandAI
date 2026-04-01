import {
  HiBolt,
  HiExclamationTriangle,
  HiLightBulb,
  HiScale,
  HiSparkles,
  HiShieldExclamation,
} from "react-icons/hi2";

function riskUi(type) {
  const t = String(type || "").toLowerCase();
  if (t.includes("reg")) {
    return {
      label: "RÉGLEMENTAIRE",
      icon: HiScale,
      iconBg: "bg-rose-50",
      iconColor: "text-rose-700",
      titleColor: "text-rose-700",
    };
  }
  if (t.includes("conc")) {
    return {
      label: "CONCURRENTIEL",
      icon: HiBolt,
      iconBg: "bg-amber-50",
      iconColor: "text-amber-700",
      titleColor: "text-amber-700",
    };
  }
  return {
    label: "MACRO",
    icon: HiExclamationTriangle,
    iconBg: "bg-blue-50",
    iconColor: "text-blue-700",
    titleColor: "text-blue-700",
  };
}

function probabilityBadge(prob) {
  const p = String(prob || "").toLowerCase();
  if (p.includes("elev")) return "bg-rose-50 text-rose-700";
  if (p.includes("moy")) return "bg-amber-50 text-amber-700";
  if (p.includes("faib")) return "bg-emerald-50 text-emerald-700";
  return "bg-slate-100 text-slate-600";
}

function horizonBadge(horizon) {
  const h = String(horizon || "").toLowerCase();
  if (h.includes("court")) return "bg-rose-50 text-rose-700";
  if (h.includes("moyen")) return "bg-amber-50 text-amber-700";
  if (h.includes("long")) return "bg-blue-50 text-blue-700";
  return "bg-slate-100 text-slate-600";
}

export default function RisksRecoTab({ report }) {
  const risques = report?.risques || [];
  const recos = report?.recommandations || [];

  return (
    <div className="space-y-3">
      <div className="space-y-2">
        <p className="inline-flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.08em] text-[#5f57b3]">
          <HiShieldExclamation className="h-3.5 w-3.5" />
          Risques identifiés
        </p>
        {risques.map((risk, idx) => (
          <div key={`${risk.type}-${idx}`} className="rounded-xl border border-[#e8e4ff] bg-white p-3 shadow-sm">
            {(() => {
              const ui = riskUi(risk.type);
              const Icon = ui.icon;
              return (
                <div className="flex items-start gap-3">
                  <div className={`mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md ${ui.iconBg}`}>
                    <Icon className={`h-4 w-4 ${ui.iconColor}`} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className={`text-[11px] font-medium uppercase tracking-[0.08em] ${ui.titleColor}`}>{ui.label}</p>
                    <p className="mt-0.5 text-[13px] font-medium leading-[1.6] text-[#2f285c]">{risk.cause || "-"}</p>
                    <p className="mt-1 text-[12px] font-normal text-[#6f6a97]">
                      Mitigation : {risk.mitigation || risk.impact || "-"}
                    </p>
                    <span className={`mt-1.5 inline-flex rounded-full px-2 py-0.5 text-[11px] font-medium ${probabilityBadge(risk.probabilite)}`}>
                      probabilité: {String(risk.probabilite || "-").replaceAll("_", " ")}
                    </span>
                  </div>
                </div>
              );
            })()}
          </div>
        ))}
      </div>

      <div className="space-y-2">
        <p className="inline-flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.08em] text-[#5f57b3]">
          <HiLightBulb className="h-3.5 w-3.5" />
          Recommandations
        </p>
        {recos.map((reco, idx) => (
          <div key={`${reco.action}-${idx}`} className="rounded-xl border border-[#e8e4ff] bg-white p-3 shadow-sm">
            <div className="flex items-start gap-3">
              <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-violet-50">
                <HiSparkles className="h-4 w-4 text-violet-700" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="mb-1 flex flex-wrap items-center gap-2">
                  <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium uppercase ${horizonBadge(reco.horizon)}`}>
                    {String(reco.horizon || "-").replaceAll("_", " ")}
                  </span>
                </div>
                <p className="text-[13px] font-medium leading-[1.6] text-[#2f285c]">{reco.action || "-"}</p>
                <p className="mt-1 text-[12px] font-normal text-[#6f6a97]">
                  Impact : {reco.impact_attendu || "-"}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

