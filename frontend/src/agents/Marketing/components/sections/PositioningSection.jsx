import { FiTarget, FiZap, FiStar, FiMessageSquare, FiAlertCircle, FiHeart } from "react-icons/fi";
import { AgentSection } from "@/agents/shared/components/AgentSection";

function TextValue({ value }) {
  return <p className="text-sm leading-relaxed text-ink">{value || "-"}</p>;
}

export function PositioningSection({ plan }) {
  const p = plan?.positioning ?? {};
  const m = plan?.messaging   ?? {};
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <AgentSection label="Segment cible">
        <div className="flex items-start gap-2">
          <FiTarget size={14} className="mt-0.5 shrink-0 text-brand" />
          <TextValue value={p.target_segment} />
        </div>
      </AgentSection>

      <AgentSection label="Différenciation">
        <div className="flex items-start gap-2">
          <FiZap size={14} className="mt-0.5 shrink-0 text-amber-500" />
          <TextValue value={p.differentiation} />
        </div>
      </AgentSection>

      <AgentSection label="Proposition de valeur" colSpan={2}>
        <div className="flex items-start gap-2">
          <FiStar size={14} className="mt-0.5 shrink-0 text-brand" />
          <TextValue value={p.value_proposition} />
        </div>
      </AgentSection>

      <AgentSection label="Message principal" colSpan={2}>
        <div className="mb-4 flex items-start gap-2">
          <FiMessageSquare size={14} className="mt-0.5 shrink-0 text-ink-muted" />
          <p className="text-sm leading-relaxed text-ink">{m.main_message || "-"}</p>
        </div>
        <div className="grid gap-2 md:grid-cols-2">
          <div className="flex items-start gap-2 rounded-xl border border-red-100 bg-red-50 p-3">
            <FiAlertCircle size={14} className="mt-0.5 shrink-0 text-red-500" />
            <p className="text-xs leading-relaxed text-red-700">{m.pain_point_focus || "-"}</p>
          </div>
          <div className="flex items-start gap-2 rounded-xl border border-success-border bg-success-light p-3">
            <FiHeart size={14} className="mt-0.5 shrink-0 text-success" />
            <p className="text-xs leading-relaxed text-success-dark">{m.emotional_hook || "-"}</p>
          </div>
        </div>
      </AgentSection>
    </div>
  );
}
