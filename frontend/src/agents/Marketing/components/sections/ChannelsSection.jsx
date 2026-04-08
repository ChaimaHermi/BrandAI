import { FiRadio, FiShare2, FiFileText, FiEdit3 } from "react-icons/fi";
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

export function ChannelsSection({ plan }) {
  const c  = plan?.channels        ?? {};
  const cd = plan?.contentDirection ?? {};
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <AgentSection label="Canaux prioritaires">
        <div className="flex items-start gap-2">
          <FiRadio size={14} className="mt-0.5 shrink-0 text-brand" />
          <BulletList items={c.primaryChannels} />
        </div>
      </AgentSection>

      <AgentSection label="Canaux secondaires">
        <div className="flex items-start gap-2">
          <FiShare2 size={14} className="mt-0.5 shrink-0 text-ink-muted" />
          <BulletList items={c.secondaryChannels} />
        </div>
      </AgentSection>

      <AgentSection label="Justification">
        <div className="flex items-start gap-2">
          <FiFileText size={14} className="mt-0.5 shrink-0 text-amber-500" />
          <p className="text-sm leading-relaxed text-ink">{c.justification || "-"}</p>
        </div>
      </AgentSection>

      <AgentSection label="Ton éditorial">
        <div className="flex items-start gap-2">
          <FiEdit3 size={14} className="mt-0.5 shrink-0 text-success" />
          <p className="text-sm leading-relaxed text-ink">{cd.tone || "-"}</p>
        </div>
      </AgentSection>
    </div>
  );
}
