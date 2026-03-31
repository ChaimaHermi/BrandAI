export default function MarketHeader({ meta = {}, overview = {} }) {
  const demand = overview?.demande?.label || "N/A";
  const competition = overview?.concurrence?.label || "N/A";

  return (
    <div className="rounded-xl border border-[#e8e4ff] bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="text-xl font-bold text-[#2f285c]">Market Analysis</h2>
          <p className="text-xs text-[#9a96bf]">Étape 2 sur 6 — Analyse en cours</p>
        </div>
        <div className="flex gap-2 text-[11px]">
          <span className="rounded-full bg-emerald-50 px-2 py-1 font-semibold text-emerald-700">
            Demande: {demand}
          </span>
          <span className="rounded-full bg-amber-50 px-2 py-1 font-semibold text-amber-700">
            Concurrence: {competition}
          </span>
          <span className="rounded-full bg-violet-50 px-2 py-1 font-semibold text-violet-700">
            {meta?.geo || "N/A"}
          </span>
        </div>
      </div>
    </div>
  );
}

