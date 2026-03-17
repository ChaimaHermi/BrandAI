import React from "react";

export function ClarityScore({ score }) {
  if (typeof score !== "number") return null;

  const normalized = Math.max(0, Math.min(100, score));
  const label =
    normalized >= 85 ? "Très clair" : normalized >= 75 ? "Bonne base" : "À préciser";

  const barColor =
    normalized >= 85
      ? "bg-[#22C55E]"
      : normalized >= 75
        ? "bg-[#F59E0B]"
        : "bg-[#EF4444]";

  return (
    <div className="mt-3 rounded-[10px] border border-[#E5E7EB] bg-[#F9FAFB] p-3 text-xs text-[#374151]">
      <div className="flex items-center justify-between text-[11px] font-medium text-[#4B5563]">
        <span>Clarity Score</span>
        <span>
          {normalized}/100 — {label}
        </span>
      </div>
      <div className="mt-2 h-2 w-full overflow-hidden rounded-full bg-[#E5E7EB]">
        <div
          className={`h-full ${barColor} transition-all duration-300`}
          style={{ width: `${normalized}%` }}
        />
      </div>
    </div>
  );
}

export default ClarityScore;

