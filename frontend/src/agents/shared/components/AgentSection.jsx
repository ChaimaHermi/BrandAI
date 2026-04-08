import React from "react";
import { SectionLabel } from "@/shared/ui/SectionLabel";

/**
 * AgentSection
 * A labeled content card — the primary data display unit in Market and Marketing modules.
 * Replaces the repeated <Card><SectionLabel>...</SectionLabel>{content}</Card> pattern
 * that appears ~30 times across MarketPage and MarketingPage.
 *
 * Props:
 *   label     — Uppercase section label text (optional — renders nothing if omitted)
 *   children  — Content below the label
 *   colSpan   — Number for md:col-span-{n} inside a CSS grid (optional)
 *   className — Extra classes on the wrapper (optional)
 *
 * Usage:
 *   <AgentSection label="Segment cible">
 *     <p className="text-sm text-[#1a1040]">{plan.positioning.target_segment}</p>
 *   </AgentSection>
 *
 *   <AgentSection label="Proposition de valeur" colSpan={2}>
 *     ...
 *   </AgentSection>
 */
export function AgentSection({ label, children, colSpan, className = "" }) {
  const spanClass = colSpan ? `md:col-span-${colSpan}` : "";
  return (
    <div
      className={`rounded-xl border border-[#e8e4ff] bg-white p-5 ${spanClass} ${className}`}
    >
      {label && <SectionLabel>{label}</SectionLabel>}
      {children}
    </div>
  );
}

export default AgentSection;
