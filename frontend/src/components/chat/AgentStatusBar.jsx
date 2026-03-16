import React from "react";

export function AgentStatusBar({ steps }) {
  if (!steps || steps.length === 0) return null;

  return (
    <div className="border-b border-[#E5E7EB] bg-[#F9FAFB] px-4 py-2">
      <div className="flex flex-col gap-0.5">
        {steps.map((step) => (
          <div key={step.id} className="flex flex-col">
            <div className="flex items-center gap-2">
              {step.status === "loading" && (
                <span className="flex gap-0.5">
                  <span className="h-1 w-1 rounded-full bg-[#7C3AED] animate-bounce" />
                  <span className="h-1 w-1 rounded-full bg-[#7C3AED] animate-bounce [animation-delay:120ms]" />
                  <span className="h-1 w-1 rounded-full bg-[#7C3AED] animate-bounce [animation-delay:240ms]" />
                </span>
              )}
              {step.status === "success" && (
                <span className="text-[11px] text-[#16A34A]">✓</span>
              )}
              {step.status === "error" && (
                <span className="text-[11px] text-red-500">✗</span>
              )}
              {step.status === "info" && (
                <span className="text-[11px] text-[#7C3AED]">→</span>
              )}

              <span
                className={`text-[11px] font-mono ${
                  step.status === "loading"
                    ? "text-[#6B7280]"
                    : step.status === "success"
                      ? "text-[#16A34A]"
                      : step.status === "error"
                        ? "text-red-500"
                        : "text-[#7C3AED]"
                }`}
              >
                {step.text}
              </span>
            </div>

            {step.detail?.dimensions && (
              <div
                className="flex gap-3 mt-0.5 pl-6 font-mono text-[11px]"
                style={{ paddingLeft: "24px", marginTop: "3px" }}
              >
                <span
                  style={{
                    color: step.detail.dimensions.problem ? "#34d399" : "#f87171",
                  }}
                >
                  {step.detail.dimensions.problem ? "✓" : "✗"} problème
                </span>
                <span
                  style={{
                    color: step.detail.dimensions.target ? "#34d399" : "#f87171",
                  }}
                >
                  {step.detail.dimensions.target ? "✓" : "✗"} cible
                </span>
                <span
                  style={{
                    color: step.detail.dimensions.solution ? "#34d399" : "#f87171",
                  }}
                >
                  {step.detail.dimensions.solution ? "✓" : "✗"} solution
                </span>
              </div>
            )}

            {step.detail?.question && (
              <div
                className="font-mono text-[11px] italic mt-0.5 pl-6 text-[#7C3AED]"
                style={{ paddingLeft: "24px", marginTop: "3px", color: "#a78bfa" }}
              >
                &quot;{step.detail.question}&quot;
              </div>
            )}

            {step.detail?.model != null && (
              <div
                className="font-mono text-[11px] mt-0.5 pl-6 text-[#6B7280]"
                style={{ paddingLeft: "24px", marginTop: "3px", color: "#64748b" }}
              >
                ⏱ {step.detail.model}
                {step.detail.key != null && ` · clé ${step.detail.key}`}
                {step.detail.ms != null && ` · ${step.detail.ms}ms`}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

export default AgentStatusBar;
