function SwotColumn({ title, items = [], colorClass }) {
  return (
    <div className="rounded-lg border border-[#e8e4ff] bg-white p-3">
      <p className={`text-xs font-bold uppercase tracking-[0.07em] ${colorClass}`}>{title}</p>
      <ul className="mt-2 space-y-1.5 text-sm text-[#5f5a84]">
        {items.map((item, idx) => (
          <li key={idx}>- {item.point || item}</li>
        ))}
      </ul>
    </div>
  );
}

export default function SwotTab({ report }) {
  const swot = report?.swot || {};

  return (
    <div className="grid gap-3 md:grid-cols-2">
      <SwotColumn title="Forces" items={swot.forces} colorClass="text-emerald-700" />
      <SwotColumn title="Faiblesses" items={swot.faiblesses} colorClass="text-rose-700" />
      <SwotColumn title="Opportunités" items={swot.opportunites} colorClass="text-blue-700" />
      <SwotColumn title="Menaces" items={swot.menaces} colorClass="text-amber-700" />
    </div>
  );
}

