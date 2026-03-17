// Stub for a global XAI terminal for the multi-agent pipeline.
// TODO: connect to real pipeline logs/events when backend is ready.

import React from "react";

export function PipelineXaiTerminal({ logs = [] }) {
  if (!logs.length) {
    logs = [
      "Clarifier → sécurité OK",
      "Clarifier → description structurée",
      "Market → en attente…",
    ];
  }

  return (
    <div className="rounded-lg border border-[#E5E7EB] bg-[#0F172A] text-[#E5E7EB] text-xs font-mono p-3 space-y-1">
      {logs.map((line, i) => (
        <div key={i} className="flex gap-2">
          <span className="text-[#6366F1]">▌</span>
          <span>{line}</span>
        </div>
      ))}
    </div>
  );
}

export default PipelineXaiTerminal;

