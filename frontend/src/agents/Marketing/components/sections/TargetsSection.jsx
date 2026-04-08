import { FiUser, FiUsers, FiCompass } from "react-icons/fi";
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

export function TargetsSection({ plan }) {
  const t = plan?.targeting ?? {};
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <AgentSection label="Persona principal">
        <div className="flex items-start gap-2">
          <FiUser size={14} className="mt-0.5 shrink-0 text-brand" />
          <p className="text-sm leading-relaxed text-ink">{t.primary_persona || "-"}</p>
        </div>
      </AgentSection>

      <AgentSection label="Focus segment">
        <div className="flex items-start gap-2">
          <FiCompass size={14} className="mt-0.5 shrink-0 text-amber-500" />
          <p className="text-sm leading-relaxed text-ink">{t.market_segment_focus || "-"}</p>
        </div>
      </AgentSection>

      <AgentSection label="Personas secondaires" colSpan={2}>
        <div className="flex items-start gap-2">
          <FiUsers size={14} className="mt-0.5 shrink-0 text-ink-muted" />
          <BulletList items={t.secondary_personas} />
        </div>
      </AgentSection>
    </div>
  );
}
