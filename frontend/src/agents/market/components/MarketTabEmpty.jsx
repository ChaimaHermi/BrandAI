export default function MarketTabEmpty({ label }) {
  return (
    <div className="rounded-2xl border border-violet-200 bg-[#F5F3FF] p-10 text-center">
      <div className="text-lg font-semibold text-violet-700">{label || "Section"}</div>
      <div className="mt-2 text-sm text-violet-500">Contenu à venir</div>
    </div>
  );
}
