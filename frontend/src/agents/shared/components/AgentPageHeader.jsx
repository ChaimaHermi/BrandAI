import React from "react";

/**
 * AgentPageHeader
 * Standardized header card shown at the top of every agent page.
 * Replaces the custom header blocks in ClarifierPage, MarketPage, MarketingPage.
 *
 * Props:
 *   agent     — Agent object from @/agents/index.js  { label, short, gradient }
 *   subtitle  — Small muted text below the agent label (optional)
 *   badge     — React node rendered on the right side (optional)
 *   action    — React node rendered after the badge (optional)
 *   className — Extra classes on the wrapper (optional)
 *
 * Usage:
 *   import { AGENTS } from "@/agents";
 *   import { AgentPageHeader } from "@/agents/shared/components/AgentPageHeader";
 *
 *   const agent = AGENTS.find(a => a.id === "market");
 *   <AgentPageHeader agent={agent} subtitle="Analyse de marché · Étape 2 sur 6" />
 */
export function AgentPageHeader({ agent, subtitle, badge, action, className = "" }) {
  const gradient = agent?.gradient || "linear-gradient(135deg,#7F77DD,#534AB7)";
  const short    = agent?.short    || "AI";
  const label    = agent?.label    || "Agent";

  return (
    <div
      className={`flex items-center gap-3 rounded-[14px] border border-[#e8e4ff] bg-white px-5 py-4 shadow-[0_2px_8px_rgba(124,58,237,0.05)] ${className}`}
    >
      {/* Agent icon */}
      <div
        className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full"
        style={{ background: gradient }}
      >
        <span className="text-[11px] font-bold text-white">{short}</span>
      </div>

      {/* Agent label + subtitle */}
      <div className="min-w-0 flex-1">
        <p className="text-[14px] font-extrabold text-[#1a1040]">{label}</p>
        {subtitle && (
          <p className="text-[11px] text-gray-400">{subtitle}</p>
        )}
      </div>

      {/* Right slot */}
      {badge}
      {action}
    </div>
  );
}

export default AgentPageHeader;
