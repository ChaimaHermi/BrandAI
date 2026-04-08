import { FiUsers, FiFlag, FiLink, FiTrendingUp } from "react-icons/fi";
import { AgentSection } from "@/agents/shared/components/AgentSection";

function BulletList({ items }) {
  if (!Array.isArray(items) || items.length === 0)
    return <p className="text-sm text-ink-subtle">-</p>;
  return (
    <ul className="space-y-1.5">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2 text-sm text-ink">
          <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-brand-muted" />
          {item}
        </li>
      ))}
    </ul>
  );
}

export function GtmSection({ plan }) {
  const g = plan?.goToMarket ?? {};
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <AgentSection label="Premiers utilisateurs" colSpan={2}>
        <div className="flex items-start gap-2">
          <FiUsers size={14} className="mt-0.5 shrink-0 text-brand" />
          <p className="text-sm leading-relaxed text-ink">{g.targetFirstUsers || "-"}</p>
        </div>
      </AgentSection>

      <AgentSection label="Stratégie de lancement" colSpan={2}>
        <div className="flex items-start gap-2">
          <FiFlag size={14} className="mt-0.5 shrink-0 text-amber-500" />
          <p className="text-sm leading-relaxed text-ink">{g.launchStrategy || "-"}</p>
        </div>
      </AgentSection>

      <AgentSection label="Partenariats">
        <div className="flex items-start gap-2">
          <FiLink size={14} className="mt-0.5 shrink-0 text-success" />
          <BulletList items={g.partnerships} />
        </div>
      </AgentSection>

      <AgentSection label="Tactiques de croissance">
        <div className="flex items-start gap-2">
          <FiTrendingUp size={14} className="mt-0.5 shrink-0 text-blue-500" />
          <BulletList items={g.earlyGrowthTactics} />
        </div>
      </AgentSection>
    </div>
  );
}
