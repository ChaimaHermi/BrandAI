import { AgentSection } from "@/agents/shared/components/AgentSection";

function BulletList({ items }) {
  if (!Array.isArray(items) || items.length === 0) {
    return <p className="text-[13px] text-gray-400">-</p>;
  }
  return (
    <ul className="space-y-1">
      {items.map((item, i) => (
        <li key={i} className="text-[13px] text-[#1a1040]">• {item}</li>
      ))}
    </ul>
  );
}

export function PricingSection({ plan }) {
  const ps = plan?.pricingStrategy ?? {};
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <AgentSection label="Modèle">
        <p className="text-[13px] text-[#1a1040]">{ps.model || "-"}</p>
      </AgentSection>
      <AgentSection label="Logique pricing">
        <p className="text-[13px] text-[#1a1040]">{ps.pricing_logic || "-"}</p>
      </AgentSection>
      <AgentSection label="Justification" colSpan={2}>
        <p className="text-[13px] text-[#1a1040]">{ps.justification || "-"}</p>
      </AgentSection>
      <AgentSection label="Hypothèses" colSpan={2}>
        <BulletList items={plan?.assumptions} />
      </AgentSection>
    </div>
  );
}
