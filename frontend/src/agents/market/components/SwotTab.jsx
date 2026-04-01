import {
  HiArrowTrendingUp,
  HiExclamationTriangle,
  HiShieldCheck,
  HiSparkles,
} from "react-icons/hi2";

function readableSource(source) {
  const s = String(source || "").trim().toLowerCase();
  if (!s || s === "inference") return "";

  // Hide technical payload paths from UI.
  if (s.includes("[") || s.includes("]") || s.includes(".")) {
    if (s.startsWith("competitor")) return "analyse concurrents";
    if (s.startsWith("market_voc")) return "voix du marché";
    if (s.startsWith("tendances")) return "signaux tendances";
    if (s.startsWith("swot")) return "synthèse SWOT";
    return "";
  }

  return source;
}

function SwotColumn({ title, items = [], colorClass, icon: Icon }) {
  return (
    <div className="rounded-lg border border-[#e8e4ff] bg-white p-3 shadow-sm">
      <p className={`inline-flex items-center gap-1.5 text-[11px] font-medium uppercase tracking-[0.08em] ${colorClass}`}>
        {Icon ? <Icon className="h-3.5 w-3.5" /> : null}
        {title}
      </p>
      <ul className="mt-2 space-y-1.5 text-[13px] font-normal leading-[1.6] text-[#5f5a84]">
        {items.map((item, idx) => {
          const label = item.point || item;
          const src = readableSource(item?.source);
          return (
            <li key={idx}>
              - {label}
              {src ? (
                <span className="ml-1 rounded-full bg-slate-100 px-1.5 py-0.5 text-[11px] font-normal text-slate-600">
                  {src}
                </span>
              ) : null}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default function SwotTab({ report }) {
  const swot = report?.swot || {};

  return (
    <div className="grid gap-3 md:grid-cols-2">
      <SwotColumn title="Forces" items={swot.forces} colorClass="text-emerald-700" icon={HiShieldCheck} />
      <SwotColumn title="Faiblesses" items={swot.faiblesses} colorClass="text-rose-700" icon={HiExclamationTriangle} />
      <SwotColumn title="Opportunités" items={swot.opportunites} colorClass="text-blue-700" icon={HiSparkles} />
      <SwotColumn title="Menaces" items={swot.menaces} colorClass="text-amber-700" icon={HiArrowTrendingUp} />
    </div>
  );
}

