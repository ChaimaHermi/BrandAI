import { FiDollarSign, FiTrendingUp, FiFileText, FiCheckCircle } from "react-icons/fi";
import { AgentSection } from "@/agents/shared/components/AgentSection";

function BulletList({ items }) {
  if (!Array.isArray(items) || items.length === 0)
    return <p className="text-sm text-ink-subtle">N'existe pas</p>;
  return (
    <ul className="space-y-1.5">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2 text-sm text-ink">
          <FiCheckCircle size={13} className="mt-0.5 shrink-0 text-success" />
          {item}
        </li>
      ))}
    </ul>
  );
}

export function PricingSection({ plan }) {
  const ps = plan?.pricingStrategy ?? {};
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <AgentSection label="Budget minimum">
        <div className="flex items-start gap-2">
          <FiDollarSign size={14} className="mt-0.5 shrink-0 text-brand" />
          <p className="text-sm leading-relaxed text-ink">
            {ps.total_budget_min ?? "N'existe pas"} {ps.currency ?? ""}
          </p>
        </div>
      </AgentSection>

      <AgentSection label="Budget maximum">
        <div className="flex items-start gap-2">
          <FiTrendingUp size={14} className="mt-0.5 shrink-0 text-amber-500" />
          <p className="text-sm leading-relaxed text-ink">
            {ps.total_budget_max ?? "N'existe pas"} {ps.currency ?? ""}
          </p>
        </div>
      </AgentSection>

      <AgentSection label="Scénario budgétaire" colSpan={2}>
        <div className="flex items-start gap-2">
          <FiFileText size={14} className="mt-0.5 shrink-0 text-ink-muted" />
          <p className="text-sm leading-relaxed text-ink">{ps.budget_scenario ?? "N'existe pas"}</p>
        </div>
      </AgentSection>

      <AgentSection label="Hypothèses" colSpan={2}>
        <BulletList items={plan?.assumptions} />
      </AgentSection>
    </div>
  );
}
