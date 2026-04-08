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

export function GtmSection({ plan }) {
  const g = plan?.goToMarket ?? {};
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <AgentSection label="Premiers utilisateurs" colSpan={2}>
        <p className="text-[13px] text-[#1a1040]">{g.targetFirstUsers || "-"}</p>
      </AgentSection>
      <AgentSection label="Stratégie de lancement" colSpan={2}>
        <p className="text-[13px] text-[#1a1040]">{g.launchStrategy || "-"}</p>
      </AgentSection>
      <AgentSection label="Partenariats">
        <BulletList items={g.partnerships} />
      </AgentSection>
      <AgentSection label="Tactiques de croissance">
        <BulletList items={g.earlyGrowthTactics} />
      </AgentSection>
    </div>
  );
}
