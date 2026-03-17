import { mapClarifierToSections } from "@/agents/clarifier/utils/mapClarifierResult";

function ClarityBar({ score }) {
  if (typeof score !== "number") return null;
  const color =
    score >= 80 ? "#16A34A" : score >= 55 ? "#7C3AED" : "#DC2626";
  return (
    <div className="mt-1.5 flex items-center gap-1.5 rounded-lg bg-[#F9FAFB] py-1 px-2">
      <span className="text-xs font-medium text-[#6B7280]">
        Clarity Score
      </span>
      <div className="h-1 flex-1 overflow-hidden rounded-full bg-[#E5E7EB]">
        <div
          className="h-full rounded-full"
          style={{ width: `${score}%`, background: color }}
        />
      </div>
      <span className="text-xs font-semibold" style={{ color }}>
        {score}/100
      </span>
    </div>
  );
}

function Section({ label, value }) {
  if (!value) return null;
  return (
    <div className="rounded-lg bg-[#F9FAFB] p-2">
      <p className="text-[10px] font-semibold uppercase tracking-wide text-[#9CA3AF]">
        {label}
      </p>
      <p className="mt-0.5 text-sm text-[#111827]">→ {value}</p>
    </div>
  );
}

export default function ClarifiedCard({ structured }) {
  const score = structured.score;
  const sections = structured.sections || mapClarifierToSections(
    structured.clarifiedIdea || structured,
  );

  return (
    <div className="mt-2 flex flex-col gap-1.5">
      {sections?.pitch && (
        <div
          style={{
            background: "var(--color-bg-secondary, #F9FAFB)",
            borderLeft: "2px solid #7F77DD",
            borderRadius: 0,
            padding: "10px 12px",
            marginBottom: "8px",
          }}
        >
          <div
            style={{
              fontSize: "10px",
              color: "#534AB7",
              fontWeight: 500,
              letterSpacing: "0.08em",
              marginBottom: "4px",
              textTransform: "uppercase",
            }}
          >
            EN RÉSUMÉ
          </div>
          <div
            style={{
              fontSize: "13px",
              fontStyle: "italic",
              color: "var(--color-text-primary, #111827)",
            }}
          >
            &quot;{sections.pitch}&quot;
          </div>
        </div>
      )}
      <Section label="Ce que vous proposez" value={sections.what} />
      <Section label="Pour qui ?" value={sections.who} />
      <Section label="Le problème résolu" value={sections.problem} />
      <ClarityBar score={score} />
    </div>
  );
}

