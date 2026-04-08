import { AgentSection } from "@/agents/shared/components/AgentSection";

function TextRow({ label, value }) {
  return (
    <AgentSection label={label}>
      <p className="text-[13px] text-[#1a1040]">{value || "-"}</p>
    </AgentSection>
  );
}

export function PositioningSection({ plan }) {
  const p = plan?.positioning ?? {};
  const m = plan?.messaging ?? {};
  return (
    <div className="grid gap-3 md:grid-cols-2">
      <TextRow label="Segment cible"        value={p.target_segment} />
      <TextRow label="Différenciation"      value={p.differentiation} />
      <AgentSection label="Proposition de valeur" colSpan={2}>
        <p className="text-[13px] text-[#1a1040]">{p.value_proposition || "-"}</p>
      </AgentSection>
      <AgentSection label="Message principal" colSpan={2}>
        <p className="mb-3 text-[13px] text-[#1a1040]">{m.main_message || "-"}</p>
        <div className="grid gap-2 md:grid-cols-2">
          <div className="rounded-lg bg-rose-50 p-3 text-[12px] text-rose-700">
            {m.pain_point_focus || "-"}
          </div>
          <div className="rounded-lg bg-emerald-50 p-3 text-[12px] text-emerald-700">
            {m.emotional_hook || "-"}
          </div>
        </div>
      </AgentSection>
    </div>
  );
}
