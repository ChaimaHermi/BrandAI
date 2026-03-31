export default function VocTab({ report }) {
  const topVoc = report?.marketVoc?.topVoc || [];
  const personas = report?.marketVoc?.personas || [];

  return (
    <div className="space-y-3">
      <div className="rounded-lg border border-[#e8e4ff] bg-white p-4">
        <p className="text-sm text-[#5f5a84]">
          <b>Niveau de demande:</b> {report?.marketVoc?.demandLevel || "-"}
        </p>
        <p className="mt-1 text-sm text-[#5f5a84]">{report?.marketVoc?.demandSummary || "-"}</p>
      </div>

      <div className="space-y-2">
        {topVoc.map((voc, idx) => (
          <div key={`${voc.theme}-${idx}`} className="rounded-lg border border-[#e8e4ff] bg-white p-3">
            <p className="font-semibold text-[#3C3489]">{voc.theme}</p>
            <p className="text-xs text-[#9a96bf]">{voc.recurrence} · {voc.source}</p>
            <p className="mt-1 text-sm italic text-[#5f5a84]">"{voc.citation}"</p>
          </div>
        ))}
      </div>

      <div className="grid gap-2 md:grid-cols-3">
        {personas.map((persona, idx) => (
          <div key={`${persona.segment}-${idx}`} className="rounded-lg border border-[#e8e4ff] bg-white p-3">
            <p className="font-semibold text-[#3C3489]">{persona.segment}</p>
            <p className="text-xs text-[#9a96bf]">{persona.tranche_age || "N/A"}</p>
            <p className="mt-1 text-sm text-[#5f5a84]">{persona.comportement}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

