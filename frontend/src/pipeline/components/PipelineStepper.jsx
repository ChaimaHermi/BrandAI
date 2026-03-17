// Simple visual stub for the multi-agent pipeline stepper.
// TODO: replace with real steps once pipeline stages are defined.

import React from "react";

export function PipelineStepper({ steps = [], activeIndex = 0 }) {
  if (!steps.length) {
    steps = ["Clarifier", "Market", "Brand", "Content", "Website"];
  }

  return (
    <div className="flex items-center gap-2 text-[11px] text-[#6B7280]">
      {steps.map((label, index) => {
        const isActive = index === activeIndex;
        const isDone = index < activeIndex;
        return (
          <React.Fragment key={label}>
            {index > 0 && (
              <div
                className={`h-px flex-1 ${
                  isDone ? "bg-[#7C3AED]" : "bg-[#E5E7EB]"
                }`}
              />
            )}
            <div
              className={`flex h-6 w-6 items-center justify-center rounded-full border text-[10px] ${
                isDone
                  ? "bg-[#7C3AED] border-[#7C3AED] text-white"
                  : isActive
                    ? "border-[#7C3AED] bg-[#F5F3FF] text-[#7C3AED]"
                    : "border-[#E5E7EB] bg-white text-[#9CA3AF]"
              }`}
            >
              {index + 1}
            </div>
          </React.Fragment>
        );
      })}
    </div>
  );
}

export default PipelineStepper;

