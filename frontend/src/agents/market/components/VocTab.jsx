import { HiChatBubbleLeftRight, HiUserGroup } from "react-icons/hi2";

function recurrenceBadge(recurrence) {
  const v = String(recurrence || "").toLowerCase();
  if (v.includes("tres")) return "bg-rose-50 text-rose-700";
  if (v.includes("elevee")) return "bg-amber-50 text-amber-700";
  if (v.includes("mod")) return "bg-violet-50 text-violet-700";
  return "bg-slate-100 text-slate-600";
}

function signalBadge(signal) {
  const v = String(signal || "").toLowerCase();
  if (v.includes("fort")) return "bg-indigo-50 text-indigo-700";
  if (v.includes("mod")) return "bg-violet-50 text-violet-700";
  return "bg-slate-100 text-slate-600";
}

function Initials({ text = "" }) {
  const initials = text
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() || "")
    .join("");
  return (
    <div className="flex h-8 w-8 items-center justify-center rounded-full bg-[#ecebff] text-xs font-bold text-[#534AB7]">
      {initials || "P"}
    </div>
  );
}

export default function VocTab({ report }) {
  const topVoc = report?.marketVoc?.topVoc || [];
  const personas = report?.marketVoc?.personas || [];
  const demandLevel = report?.marketVoc?.demandLevel || "-";

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-[#e8e4ff] bg-white p-4 shadow-sm">
        <p className="inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-[0.07em] text-[#6a60d8]">
          <HiChatBubbleLeftRight className="h-3.5 w-3.5" />
          Voix du marché — Top citations
        </p>
        <p className="mt-1 text-sm text-[#5f5a84]">
          Niveau de demande: <span className="font-semibold text-[#3C3489]">{demandLevel}</span>
        </p>
      </div>

      <div className="space-y-2">
        {topVoc.map((voc, idx) => (
          <div key={`${voc.theme}-${idx}`} className="rounded-xl border border-[#e8e4ff] bg-white p-4 shadow-sm">
            <div className="mb-1.5 flex items-start gap-2">
              <span className={`rounded-full px-2 py-0.5 text-xs font-bold ${recurrenceBadge(voc.recurrence)}`}>
                {String(voc.recurrence || "").replaceAll("_", " ")}
              </span>
              <p className="text-base leading-none text-[#bcb8df]">"</p>
            </div>

            <p className="text-base font-semibold leading-tight text-[#3C3489]">{voc.theme}</p>
            <p className="mt-1 border-l-2 border-[#e6e2ff] pl-2 text-sm italic text-[#6b6791]">
              "{voc.citation}"
            </p>
            <p className="mt-1 text-xs text-[#9a96bf]">{voc.source}</p>
          </div>
        ))}
      </div>

      <div>
        <p className="mb-2 inline-flex items-center gap-1.5 text-xs font-bold uppercase tracking-[0.07em] text-[#5a52ad]">
          <HiUserGroup className="h-3.5 w-3.5" />
          Personas identifiés
        </p>
        <div className="grid gap-3 md:grid-cols-3">
          {personas.map((persona, idx) => (
            <div key={`${persona.segment}-${idx}`} className="rounded-xl border border-[#e8e4ff] bg-white p-4 shadow-sm">
              <div className="mb-2 flex items-start justify-between gap-2">
                <Initials text={persona.segment} />
                <span className={`rounded-full px-2 py-0.5 text-[11px] font-semibold ${signalBadge(persona.signal_niveau)}`}>
                  signal {String(persona.signal_niveau || "").toLowerCase().replace("_", " ")}
                </span>
              </div>
              <p className="text-base font-semibold leading-tight text-[#3C3489]">{persona.segment}</p>
              <p className="mt-0.5 text-xs text-[#9a96bf]">{persona.tranche_age || "N/A"}</p>
              <p className="mt-2 text-sm text-[#5f5a84]">{persona.comportement}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

