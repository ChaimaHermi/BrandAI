import { HiArrowPath, HiEye } from "react-icons/hi2";

export default function MarketHeader({
  meta = {},
  idea = {},
  onRelaunch,
  isLoading = false,
}) {
  const projectName = meta?.projet || idea?.name || "N/A";
  const sector = meta?.secteur || idea?.sector || "N/A";
  const geo = meta?.geo || "N/A";

  return (
    <div className="rounded-xl border border-[#e8e4ff] bg-white p-4 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-[15px] font-medium text-[#2f285c]">Market Analysis</h2>
          <p className="text-[11px] font-normal text-[#9a96bf]">Étape 2 sur 6 — Analyse en cours</p>
        </div>
        <button
          type="button"
          onClick={onRelaunch}
          disabled={isLoading || !onRelaunch}
          className="inline-flex items-center gap-2 rounded-xl border border-[#4f45c8] bg-[#5b50d6] px-3 py-2 text-[13px] font-medium text-white shadow-sm transition hover:bg-[#4f45c8] disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isLoading ? <HiArrowPath className="h-4 w-4 animate-spin" /> : <HiEye className="h-4 w-4" />}
          {isLoading ? "Relance en cours..." : "Relancer votre analyse de marché"}
        </button>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px]">
        <span className="rounded-full bg-emerald-50 px-2 py-1 font-medium text-emerald-700">
          Idee: {projectName}
        </span>
        <span className="rounded-full bg-amber-50 px-2 py-1 font-medium text-amber-700">
          Secteur: {sector}
        </span>
        <span className="rounded-full bg-violet-50 px-2 py-1 font-medium text-violet-700">
          Geo: {geo}
        </span>
      </div>
    </div>
  );
}

