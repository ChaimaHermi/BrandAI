import { AGENTS } from "@/agents";
import { AgentPageHeader } from "@/agents/shared/components/AgentPageHeader";
import { TabBar } from "@/shared/ui/TabBar";

const marketingAgent = AGENTS.find((a) => a.id === "marketing");

const SECTION_TABS = [
  { id: "positioning", label: "Positionnement" },
  { id: "targets",     label: "Cibles" },
  { id: "channels",    label: "Canaux" },
  { id: "pricing",     label: "Pricing" },
  { id: "gtm",         label: "Go-to-Market" },
  { id: "action",      label: "Plan d'action" },
];

/**
 * MarketingHeader
 * Shows the agent identity header + project meta badges + tab navigation.
 *
 * Props:
 *   idea        — idea object (for sector/country/confidence)
 *   plan        — mapped marketing plan (for confidenceLevel)
 *   activeTab   — currently active section id
 *   onTabChange — (id) => void
 */
export function MarketingHeader({ idea, plan, activeTab, onTabChange }) {
  const badge = (
    <div className="flex flex-wrap items-center gap-2">
      {(idea?.clarity_sector || idea?.sector) && (
        <span className="rounded-full bg-[#f0eeff] px-2.5 py-1 text-[11px] font-semibold text-[#534AB7]">
          {idea.clarity_sector || idea.sector}
        </span>
      )}
      <span className="rounded-full bg-[#f0fdf4] px-2.5 py-1 text-[11px] font-semibold text-[#1D9E75]">
        {idea?.clarity_country_code || "TN"}
      </span>
      {plan?.confidenceLevel && plan.confidenceLevel !== "-" && (
        <span className="rounded-full bg-amber-100 px-2.5 py-1 text-[11px] font-semibold text-amber-700">
          Confiance {plan.confidenceLevel}
        </span>
      )}
    </div>
  );

  return (
    <div className="rounded-[14px] border border-[#e8e4ff] bg-white px-5 pb-4 pt-4 shadow-[0_2px_8px_rgba(124,58,237,0.05)]">
      <AgentPageHeader
        agent={marketingAgent}
        subtitle="Plan marketing · Étape 3 sur 6"
        badge={badge}
        className="border-0 shadow-none p-0 mb-3"
      />
      <TabBar tabs={SECTION_TABS} activeId={activeTab} onChange={onTabChange} />
    </div>
  );
}

export { SECTION_TABS };
