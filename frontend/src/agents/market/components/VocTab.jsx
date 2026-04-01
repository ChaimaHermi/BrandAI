import { HiChatBubbleLeftRight, HiUserGroup } from "react-icons/hi2";

function recurrenceUi(recurrence) {
  const v = String(recurrence || "").toLowerCase();
  if (v.includes("tres")) {
    return {
      border: "border-rose-700",
      badge: "bg-rose-100 text-rose-700 dark:bg-rose-900/60 dark:text-rose-300",
    };
  }
  if (v.includes("elevee")) {
    return {
      border: "border-amber-500",
      badge: "bg-amber-100 text-amber-700 dark:bg-amber-900/60 dark:text-amber-300",
    };
  }
  return {
    border: "border-slate-400",
    badge: "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200",
  };
}

function signalBadge(signal) {
  const v = String(signal || "").toLowerCase();
  if (v.includes("fort")) return "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/60 dark:text-emerald-300";
  if (v.includes("mod")) return "bg-amber-100 text-amber-700 dark:bg-amber-900/60 dark:text-amber-300";
  return "bg-slate-200 text-slate-700 dark:bg-slate-700 dark:text-slate-200";
}

export default function VocTab({ report }) {
  const topVoc = report?.marketVoc?.topVoc || [];
  const personas = report?.marketVoc?.personas || [];
  const demandLevel = report?.marketVoc?.demandLevel || "-";

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900">
        <p className="inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.06em] text-slate-500 dark:text-slate-400">
          <HiChatBubbleLeftRight className="h-3.5 w-3.5" />
          Voix du marché — Top citations
        </p>
        <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
          Niveau de demande: <span className="font-semibold text-slate-900 dark:text-slate-100">{demandLevel}</span>
        </p>
      </div>

      <div className="space-y-2">
        {topVoc.map((voc, idx) => (
          <div
            key={`${voc.theme}-${idx}`}
            className={`rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-900`}
          >
            <div className={`mb-2 border-l-4 pl-3 ${recurrenceUi(voc.recurrence).border}`}>
              <p className="text-base font-semibold leading-tight text-slate-900 dark:text-slate-100">{voc.theme}</p>
              <p className="mt-1 text-sm italic text-slate-700 dark:text-slate-300">"{voc.citation}"</p>
            </div>
            <div className="mb-1.5 flex items-start gap-2">
              <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${recurrenceUi(voc.recurrence).badge}`}>
                {String(voc.recurrence || "").replaceAll("_", " ")}
              </span>
              <span className="text-xs text-slate-500 dark:text-slate-400">{voc.source}</span>
            </div>
          </div>
        ))}
      </div>

      <div>
        <p className="mb-2 inline-flex items-center gap-1.5 text-xs font-semibold uppercase tracking-[0.06em] text-slate-500 dark:text-slate-400">
          <HiUserGroup className="h-3.5 w-3.5" />
          Personas identifiés
        </p>
        <div className="grid gap-3 md:grid-cols-3">
          {personas.map((persona, idx) => (
            <div
              key={`${persona.segment}-${idx}`}
              className="rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-slate-800"
            >
              <div className="mb-2 flex items-start justify-between gap-2">
                <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${signalBadge(persona.signal_niveau)}`}>
                  signal {String(persona.signal_niveau || "").toLowerCase().replace("_", " ")}
                </span>
              </div>
              <p className="text-base font-semibold leading-tight text-slate-900 dark:text-slate-100">{persona.segment}</p>
              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">{persona.tranche_age || "N/A"}</p>
              <p className="mt-2 text-sm text-slate-700 dark:text-slate-300">{persona.comportement}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

