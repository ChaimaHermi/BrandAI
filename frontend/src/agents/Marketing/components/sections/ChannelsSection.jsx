import { FiRadio, FiInfo, FiBarChart2 } from "react-icons/fi";

function ChannelCard({ channel, rank, variant = "primary" }) {
  if (!channel || typeof channel !== "object") return null;
  const name = channel.name;
  const role = channel.role;
  const justification = channel.justification;
  const isPrimary    = variant === "primary";

  const borderAccent = isPrimary ? "border-l-brand" : "border-l-amber-400";
  const badgeClass   = isPrimary ? "bg-brand-light text-brand-dark" : "bg-amber-50 text-amber-700";

  return (
    <div
      className={`overflow-hidden rounded-2xl border border-[color:var(--color-border,#ebebf5)] border-l-4 ${borderAccent} bg-white shadow-card`}
    >
      {/* Header */}
      <div className="flex items-start justify-between gap-2 px-4 pt-4 pb-3">
        <div className="flex items-center gap-2">
          <span className={`flex h-7 w-7 items-center justify-center rounded-lg ${badgeClass}`}>
            {isPrimary ? <FiRadio size={13} /> : <FiShare2 size={13} />}
          </span>
          <p className="text-sm font-bold text-ink">{name || "N'existe pas"}</p>
        </div>
        <span className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] font-bold ${badgeClass}`}>
          {isPrimary ? `#${rank} Prioritaire` : "Secondaire"}
        </span>
      </div>

      {/* Role */}
      {role && (
        <div className="px-4 pb-3">
          <span className="inline-block rounded-full bg-ink/[0.05] px-2.5 py-1 text-[11px] font-medium text-ink-body">
            Rôle : <span className="font-semibold text-ink">{role}</span>
          </span>
        </div>
      )}

      {/* Justification */}
      {justification && (
        <div className="flex items-start gap-2 border-t border-[color:var(--color-border,#ebebf5)] px-4 py-3">
          <FiInfo size={11} className="mt-0.5 shrink-0 text-ink-subtle" />
          <p className="text-[12px] leading-relaxed text-ink-body">{justification}</p>
        </div>
      )}
    </div>
  );
}

function BudgetSummaryCard({ budget }) {
  const { project_type_identified, reasoning, currency, total, breakdown } = budget;
  const rows = Array.isArray(breakdown) ? breakdown : [];
  const hasTop = project_type_identified || reasoning || currency || total;

  return (
    <div className="rounded-2xl border border-brand-border bg-gradient-to-br from-brand-light via-white to-[#f3f0ff] shadow-card overflow-hidden">
      <div className="flex items-center gap-3 px-5 py-4">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand to-brand-dark text-white shadow-pill">
          <FiBarChart2 size={16} />
        </span>
        <div>
          <p className="text-[10px] font-extrabold uppercase tracking-widest text-brand">
            Synthèse budgétaire
          </p>
          {hasTop && <p className="mt-0.5 text-sm font-bold text-ink">{total} {currency}</p>}
        </div>
      </div>
      <div className="border-t border-brand-border/50 bg-white/60 px-5 py-3 space-y-2">
        <p className="text-[12px] leading-relaxed text-ink-body">
          <span className="font-semibold text-ink">Type de projet :</span>{" "}
          {project_type_identified || "N'existe pas"}
        </p>
        <p className="text-[12px] leading-relaxed text-ink-body">
          <span className="font-semibold text-ink">Reasoning :</span>{" "}
          {reasoning || "N'existe pas"}
        </p>
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-brand-border/60">
                <th className="py-2 pr-3 text-left font-semibold text-ink-muted">Poste</th>
                <th className="py-2 pr-3 text-right font-semibold text-ink-muted">%</th>
                <th className="py-2 pr-3 text-right font-semibold text-ink-muted">Amount</th>
                <th className="py-2 text-left font-semibold text-ink-muted">Justification</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r, idx) => (
                <tr key={`budget-row-${idx}`} className="border-b border-brand-border/30">
                  <td className="py-2 pr-3 text-ink">{r?.poste || "N'existe pas"}</td>
                  <td className="py-2 pr-3 text-right text-ink">{r?.percent ?? "N'existe pas"}</td>
                  <td className="py-2 pr-3 text-right text-ink">{r?.amount || "N'existe pas"}</td>
                  <td className="py-2 text-ink-body">{r?.justification || "N'existe pas"}</td>
                </tr>
              ))}
              {rows.length === 0 && (
                <tr>
                  <td className="py-2 text-ink-subtle" colSpan={4}>N'existe pas</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export function ChannelsSection({ plan }) {
  const c = plan?.channels ?? {};
  const budget = plan?.budgetAllocation ?? {};
  const primaryDetailed = Array.isArray(c?.primaryChannelsDetailed) ? c.primaryChannelsDetailed : [];
  const hasBudget = typeof budget === "object" && budget !== null;

  return (
    <div className="flex flex-col gap-5">

      {hasBudget && <BudgetSummaryCard budget={budget} />}

      {primaryDetailed.length > 0 && (
        <div>
          <p className="mb-2.5 flex items-center gap-1.5 text-[11px] font-extrabold uppercase tracking-widest text-ink-muted">
            <FiRadio size={10} /> Canaux fixes (Facebook, Instagram, LinkedIn)
          </p>
          <div className="flex flex-col gap-3">
            {primaryDetailed.map((ch, i) => (
              <ChannelCard key={`primary-${i}`} channel={ch} rank={i + 1} variant="primary" />
            ))}
          </div>
        </div>
      )}

      {primaryDetailed.length === 0 && (
        <p className="text-sm text-ink-subtle">N'existe pas</p>
      )}
    </div>
  );
}
