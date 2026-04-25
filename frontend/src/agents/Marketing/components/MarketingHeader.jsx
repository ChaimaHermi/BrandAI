import { AGENTS } from "@/agents";
import { AgentPageHeader } from "@/agents/shared/components/AgentPageHeader";
import { TabBar } from "@/shared/ui/TabBar";

const marketingAgent = AGENTS.find((a) => a.id === "marketing");

const SECTION_TABS = [
  { id: "positioning", label: "Positionnement" },
  { id: "targets",     label: "Cibles" },
  { id: "channels",    label: "Canaux & Budget" },
  { id: "content",     label: "Contenu" },
  { id: "gtm",         label: "Go-to-Market" },
  { id: "action",      label: "Plan d'action" },
];

/**
 * MarketingHeader
 * Agent identity header + project meta badges + tab navigation.
 */
export function MarketingHeader({ idea, plan, activeTab, onTabChange }) {
  const badge = (
    <div className="flex flex-wrap items-center gap-2">
      {(idea?.clarity_sector || idea?.sector) && (
        <span className="rounded-full bg-brand-light px-2.5 py-1 text-xs font-semibold text-brand-dark">
          {idea.clarity_sector || idea.sector}
        </span>
      )}
      {idea?.clarity_country_code && (
        <span className="rounded-full bg-success-light px-2.5 py-1 text-xs font-semibold text-success">
          {idea.clarity_country_code}
        </span>
      )}
      {plan?.confidenceLevel && (
        <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-700">
          Confiance {plan.confidenceLevel}
        </span>
      )}
    </div>
  );

  return (
    <div className="rounded-2xl border border-brand-border bg-white px-5 pb-4 pt-4 shadow-card">
      <AgentPageHeader
        agent={marketingAgent}
        subtitle="Plan marketing · Étape 3 sur 6"
        badge={badge}
        className="mb-3 border-0 p-0 shadow-none"
      />
      <TabBar tabs={SECTION_TABS} activeId={activeTab} onChange={onTabChange} />
    </div>
  );
}

export { SECTION_TABS };
