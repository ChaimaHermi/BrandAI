import React, { useState } from "react";

export function AgentStatusBar({ steps }) {
  const [showXAI, setShowXAI] = useState(true);

  if (!steps || steps.length === 0) return null;

  return (
    <div className="border-b border-[#E5E7EB] bg-[#F9FAFB] px-4 py-2">
      <div
        role="button"
        tabIndex={0}
        onClick={() => setShowXAI(!showXAI)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            setShowXAI((v) => !v);
          }
        }}
        className="flex items-center gap-1.5 cursor-pointer select-none py-1 rounded hover:bg-[#EEF2FF]/60 transition-colors min-w-0"
        style={{ marginBottom: showXAI ? "6px" : 0 }}
      >
        <span className="text-[10px] text-[#6B7280] font-mono leading-none">
          {showXAI ? "▼" : "▶"}
        </span>
        <span className="text-[11px] font-medium text-[#4B5563]">
          XAI — Raisonnement de l&apos;agent
        </span>
      </div>
      {showXAI && (
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
                  {step.detail?.sector && ` · ${step.detail.sector}`}
                  {step.detail?.confidence != null &&
                    ` · confiance ${step.detail.confidence}%`}
                </span>
              </div>

              {step.detail?.dimensions && (
                <div
                  style={{
                    paddingLeft: "20px",
                    marginTop: "2px",
                    display: "flex",
                    gap: "12px",
                    fontFamily: "monospace",
                    fontSize: "11px",
                  }}
                >
                  {[
                    { key: "problem", label: "problème" },
                    { key: "target", label: "cible" },
                    { key: "solution", label: "solution" },
                  ].map(({ key, label }) => (
                    <span
                      key={key}
                      style={{
                        color: step.detail.dimensions[key] ? "#34d399" : "#f87171",
                      }}
                    >
                      {step.detail.dimensions[key] ? "✓" : "✗"} {label}
                    </span>
                  ))}
                </div>
              )}

              {(step.detail?.score != null || step.detail?.model) && (
                <div
                  style={{
                    paddingLeft: "20px",
                    marginTop: "2px",
                    fontFamily: "monospace",
                    fontSize: "11px",
                    color: "#64748b",
                    display: "flex",
                    gap: "10px",
                  }}
                >
                  {step.detail?.score != null && (
                    <span
                      style={{
                        color:
                          step.detail.score >= 80 ? "#34d399" : "#f59e0b",
                      }}
                    >
                      score : {step.detail.score}/100
                    </span>
                  )}
                  {step.detail?.model && (
                    <span>{step.detail.model}</span>
                  )}
                  {step.detail?.elapsed_ms != null && (
                    <span>{step.detail.elapsed_ms}ms</span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default AgentStatusBar;

