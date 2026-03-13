import React from "react";
import { AgentCard } from "./AgentCard";

export function AgentTimeline({ agents, agentStatuses, activeId, onSelect }) {
  return (
    <nav className="flex flex-col gap-2">
      {agents.map((agent) => (
        <AgentCard key={agent.id} agent={agent} status={agentStatuses[agent.id] || "waiting"} isActive={activeId === agent.id} onClick={() => onSelect(agent.id)} />
      ))}
    </nav>
  );
}

export default AgentTimeline;
