import { FiInfo, FiBarChart2, FiRadio } from "react-icons/fi";
import { FaFacebook, FaInstagram, FaLinkedin, FaTwitter, FaTiktok, FaYoutube } from "react-icons/fa";

const CHANNEL_META = {
  facebook:  { Icon: FaFacebook,  iconColor: "#1877F2", color: "bg-blue-50 border-blue-200 text-blue-700",  accent: "border-l-blue-400"  },
  instagram: { Icon: FaInstagram, iconColor: "#E1306C", color: "bg-pink-50 border-pink-200 text-pink-700",  accent: "border-l-pink-400"  },
  linkedin:  { Icon: FaLinkedin,  iconColor: "#0A66C2", color: "bg-sky-50 border-sky-200 text-sky-700",     accent: "border-l-sky-400"   },
  twitter:   { Icon: FaTwitter,   iconColor: "#1DA1F2", color: "bg-cyan-50 border-cyan-200 text-cyan-700",  accent: "border-l-cyan-400"  },
  tiktok:    { Icon: FaTiktok,    iconColor: "#010101", color: "bg-rose-50 border-rose-200 text-rose-700",  accent: "border-l-rose-400"  },
  youtube:   { Icon: FaYoutube,   iconColor: "#FF0000", color: "bg-red-50 border-red-200 text-red-700",     accent: "border-l-red-400"   },
};

function getChannelMeta(name) {
  const key = (name || "").toLowerCase();
  return CHANNEL_META[key] || { Icon: FiRadio, iconColor: "var(--color-brand)", color: "bg-brand-light border-brand-border text-brand-dark", accent: "border-l-brand" };
}

function ChannelRow({ channel, rank }) {
  if (!channel || typeof channel !== "object") return null;
  const { name, role, justification } = channel;
  const meta = getChannelMeta(name);
  const ChannelIcon = meta.Icon;

  return (
    <div className={`overflow-hidden rounded-xl border ${meta.accent} border-l-4 bg-white shadow-sm`}>
      <div className="flex items-center gap-3 px-3 py-2.5">
        <span className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border ${meta.color}`}>
          <ChannelIcon size={16} style={{ color: meta.iconColor }} />
        </span>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p className="text-sm font-bold text-ink">{name || ""}</p>
            <span className={`rounded-full border px-2 py-0.5 text-[10px] font-bold ${meta.color}`}>
              #{rank}
            </span>
          </div>
          {role && (
            <p className="truncate text-[11px] text-ink-subtle">{role}</p>
          )}
        </div>
      </div>
      {justification && (
        <div className="flex items-start gap-2 border-t border-[color:var(--color-border,#ebebf5)] px-3 py-2">
          <FiInfo size={11} className="mt-0.5 shrink-0 text-ink-subtle" />
          <p className="text-[11px] leading-relaxed text-ink-body">{justification}</p>
        </div>
      )}
    </div>
  );
}

function BudgetSummaryCard({ budget }) {
  const { project_type_identified, reasoning, currency, total, breakdown } = budget;
  const rows = Array.isArray(breakdown) ? breakdown : [];
  const hasTop = project_type_identified || reasoning || currency || total;
  const totalLabel = String(total || "").includes(String(currency || ""))
    ? total
    : [total, currency].filter(Boolean).join(" ");

  return (
    <div className="rounded-2xl border border-brand-border bg-gradient-to-br from-brand-light via-white to-[#f3f0ff] shadow-card overflow-hidden">
      <div className="flex items-center gap-3 px-5 py-4">
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-brand to-brand-dark text-white shadow-pill">
          <FiBarChart2 size={16} />
        </span>
        <div>
          <p className="text-[10px] font-extrabold uppercase tracking-widest text-brand">
            Répartition du budget de lancement
          </p>
          {hasTop && <p className="mt-0.5 text-sm font-bold text-ink">{totalLabel || ""}</p>}
        </div>
      </div>
      <div className="border-t border-brand-border/50 bg-white/60 px-5 py-3 space-y-2">
        {project_type_identified && (
          <p className="text-[12px] leading-relaxed text-ink-body">
            <span className="font-semibold text-ink">Type de projet :</span>{" "}
            {project_type_identified}
          </p>
        )}
        {reasoning && (
          <p className="text-[12px] leading-relaxed text-ink-body">
            <span className="font-semibold text-ink">Justification :</span>{" "}
            {reasoning}
          </p>
        )}
        {rows.length > 0 && (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-brand-border/60">
                  <th className="py-2 pr-3 text-left font-semibold text-ink-muted">Poste</th>
                  <th className="py-2 pr-3 text-right font-semibold text-ink-muted">%</th>
                  <th className="py-2 pr-3 text-right font-semibold text-ink-muted">Montant</th>
                  <th className="py-2 text-left font-semibold text-ink-muted">Justification</th>
                </tr>
              </thead>
              <tbody>
                {rows.map((r, idx) => (
                  <tr key={`budget-row-${idx}`} className="border-b border-brand-border/30">
                    <td className="py-2 pr-3 text-ink">{r?.poste || ""}</td>
                    <td className="py-2 pr-3 text-right text-ink">{r?.percent ?? ""}</td>
                    <td className="py-2 pr-3 text-right text-ink">{r?.amount || ""}</td>
                    <td className="py-2 text-ink-body">{r?.justification || ""}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export function ChannelsSection({
  plan,
  showBudget = true,
  showChannels = true,
  showChannelsTitle = true,
}) {
  const c = plan?.channels ?? {};
  const budget = plan?.budgetAllocation ?? {};
  const primaryDetailed = Array.isArray(c?.primaryChannelsDetailed) ? c.primaryChannelsDetailed : [];
  const hasBudget = typeof budget === "object" && budget !== null;

  return (
    <div className="flex flex-col gap-4">
      {showBudget && hasBudget && <BudgetSummaryCard budget={budget} />}

      {showChannels && primaryDetailed.length > 0 && (
        <div>
          {showChannelsTitle && (
            <p className="mb-2 text-[11px] font-extrabold uppercase tracking-widest text-ink-muted">
              Canaux recommandés
            </p>
          )}
          <div className="flex flex-wrap gap-3">
            {primaryDetailed.map((ch, i) => (
              <div key={`channel-${i}`} className="flex-1 min-w-[180px]">
                <ChannelRow channel={ch} rank={i + 1} />
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
