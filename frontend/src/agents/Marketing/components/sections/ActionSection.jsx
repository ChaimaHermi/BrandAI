import { FiClock, FiCalendar, FiTrendingUp } from "react-icons/fi";
import { AgentSection } from "@/agents/shared/components/AgentSection";

function BulletList({ items, dotClass }) {
  if (!Array.isArray(items) || items.length === 0)
    return <p className="text-sm text-ink-subtle">-</p>;
  return (
    <ul className="space-y-1.5">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2 text-sm text-ink">
          <span className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${dotClass}`} />
          {item}
        </li>
      ))}
    </ul>
  );
}

export function ActionSection({ plan }) {
  const a = plan?.actionPlan ?? {};
  return (
    <div className="grid gap-3 lg:grid-cols-3">
      <AgentSection label="Court terme">
        <div className="mb-3 flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-light">
            <FiClock size={14} className="text-brand" />
          </span>
          <span className="text-xs font-semibold text-brand">Immédiat</span>
        </div>
        <BulletList items={a.shortTerm} dotClass="bg-brand" />
      </AgentSection>

      <AgentSection label="Moyen terme">
        <div className="mb-3 flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50">
            <FiCalendar size={14} className="text-amber-500" />
          </span>
          <span className="text-xs font-semibold text-amber-600">3–6 mois</span>
        </div>
        <BulletList items={a.midTerm} dotClass="bg-amber-400" />
      </AgentSection>

      <AgentSection label="Long terme">
        <div className="mb-3 flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-success-light">
            <FiTrendingUp size={14} className="text-success" />
          </span>
          <span className="text-xs font-semibold text-success">6–12 mois</span>
        </div>
        <BulletList items={a.longTerm} dotClass="bg-success" />
      </AgentSection>
    </div>
  );
}
