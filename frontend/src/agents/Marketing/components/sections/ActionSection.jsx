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

export function ActionSection({ plan }) {
  const a = plan?.actionPlan ?? {};
  return (
    <div className="grid gap-3 lg:grid-cols-3">
      <AgentSection label="Court terme">
        <BulletList items={a.shortTerm} />
      </AgentSection>
      <AgentSection label="Moyen terme">
        <BulletList items={a.midTerm} />
      </AgentSection>
      <AgentSection label="Long terme">
        <BulletList items={a.longTerm} />
      </AgentSection>
    </div>
  );
}
