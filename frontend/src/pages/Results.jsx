import React, { useState, useMemo } from "react";
import { useParams, Link } from "react-router-dom";
import { HiOutlineArrowLeft } from "react-icons/hi2";
import { Navbar } from "../components/layout/Navbar";
import { Badge } from "../components/ui/Badge";
import { AgentTimeline } from "../components/agents/AgentTimeline";
import { ResultDisplay } from "../components/agents/ResultDisplay";
import { AGENTS, PROJECTS, TECHMENTOR_RESULTS } from "../data/mockData";

function getProject(id) {
  return PROJECTS.find((p) => p.id === id) || { id, name: "Projet", status: "running", agentsDone: 2, totalAgents: 6 };
}

function getAgentStatuses(projectId) {
  if (projectId === "techmentor") return { idea: "done", market: "done", brand: "running", content: "waiting", website: "waiting", optimizer: "waiting" };
  if (projectId === "ecoshop" || projectId === "foodieapp") return { idea: "done", market: "done", brand: "done", content: "done", website: "done", optimizer: "done" };
  return { idea: "waiting", market: "waiting", brand: "waiting", content: "waiting", website: "waiting", optimizer: "waiting" };
}

export function Results() {
  const { id } = useParams();
  const [activeAgent, setActiveAgent] = useState("brand");
  const project = useMemo(() => getProject(id), [id]);
  const statuses = useMemo(() => getAgentStatuses(id), [id]);
  const results = id === "techmentor" ? TECHMENTOR_RESULTS : {};
  const currentData = results[activeAgent];
  const currentStatus = statuses[activeAgent] || "waiting";
  const runningIndex = AGENTS.findIndex((a) => statuses[a.id] === "running");
  const pipelineLabel = runningIndex >= 0 ? `Pipeline en cours — agent ${runningIndex + 1}/${AGENTS.length}` : "Pipeline terminé";

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-white">
      <Navbar variant="app" />
      <main className="flex flex-1 overflow-hidden">
        <div className="mx-auto w-full max-w-[1400px] px-6 py-4 flex flex-col lg:flex-row flex-1 min-h-0 overflow-hidden">
          <div className="border-b border-[#E5E7EB] bg-white px-0 py-4 lg:px-0 shrink-0 lg:border-b-0">
            <div className="flex flex-wrap items-center gap-3">
              <Link to="/dashboard" className="flex items-center gap-1 text-sm text-[#6B7280] hover:text-[#7C3AED]"><HiOutlineArrowLeft className="h-4 w-4" /> Retour</Link>
              <h1 className="text-lg font-semibold text-[#111827]">{project.name}</h1>
              <Badge variant={project.status === "completed" ? "success" : "violet"}>{project.status === "completed" ? "Complété" : "En cours"}</Badge>
            </div>
            <p className="mt-1 text-sm text-[#6B7280]">{pipelineLabel}</p>
          </div>
          <div className="border-b border-[#E5E7EB] bg-[#F9FAFB] px-4 py-3 lg:hidden">
            <div className="flex gap-2 overflow-x-auto pb-1">
              {AGENTS.map((agent) => (
                <button key={agent.id} type="button" onClick={() => setActiveAgent(agent.id)} className={`shrink-0 rounded-lg border px-3 py-2 text-xs font-medium transition-all ${activeAgent === agent.id ? "border-[#7C3AED] bg-[#F5F3FF] text-[#7C3AED]" : "border-[#E5E7EB] bg-white text-[#6B7280]"}`}>{agent.name}</button>
              ))}
            </div>
          </div>
          <aside className="hidden w-[240px] shrink-0 border-r border-[#E5E7EB] bg-[#F9FAFB] p-4 lg:block">
            <p className="mb-3 text-xs font-medium uppercase tracking-wider text-[#6B7280]">Agents</p>
            <AgentTimeline agents={AGENTS} agentStatuses={statuses} activeId={activeAgent} onSelect={setActiveAgent} />
          </aside>
          <div className="flex-1 min-h-0 overflow-y-auto p-4 lg:p-6">
            <ResultDisplay agentId={activeAgent} data={currentData} status={currentStatus} />
          </div>
        </div>
      </main>
    </div>
  );
}

export default Results;
