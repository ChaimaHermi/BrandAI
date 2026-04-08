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

export function ChannelsSection({ plan }) {
  const c = plan?.channels ?? {};
  const cd = plan?.contentDirection ?? {};
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <AgentSection label="Canaux prioritaires">
        <BulletList items={c.primaryChannels} />
      </AgentSection>
      <AgentSection label="Canaux secondaires">
        <BulletList items={c.secondaryChannels} />
      </AgentSection>
      <AgentSection label="Justification">
        <p className="text-[13px] text-[#1a1040]">{c.justification || "-"}</p>
      </AgentSection>
      <AgentSection label="Ton éditorial">
        <p className="text-[13px] text-[#1a1040]">{cd.tone || "-"}</p>
      </AgentSection>
    </div>
  );
}
