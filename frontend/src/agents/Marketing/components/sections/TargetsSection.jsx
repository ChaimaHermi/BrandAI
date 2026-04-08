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

export function TargetsSection({ plan }) {
  const t = plan?.targeting ?? {};
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <AgentSection label="Persona principal">
        <p className="text-[13px] text-[#1a1040]">{t.primary_persona || "-"}</p>
      </AgentSection>
      <AgentSection label="Focus segment">
        <p className="text-[13px] text-[#1a1040]">{t.market_segment_focus || "-"}</p>
      </AgentSection>
      <AgentSection label="Personas secondaires" colSpan={2}>
        <BulletList items={t.secondary_personas} />
      </AgentSection>
    </div>
  );
}
