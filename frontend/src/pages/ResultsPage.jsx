import React, { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { HiOutlineArrowLeft } from "react-icons/hi2";
import { Navbar } from "@/components/layout/Navbar";
import { Badge } from "@/shared/ui/Badge";
import { AgentTimeline } from "@/components/agents/AgentTimeline";
import { ResultDisplay } from "@/components/agents/ResultDisplay";
import { AGENTS } from "@/agents";
import { useAuth } from "@/shared/hooks/useAuth";
import { apiGetIdea, getErrorMessage } from "@/services/ideaApi";
import { getLatestMarketAnalysis } from "@/agents/market/api/market.api";
import { getLatestMarketingPlan } from "@/agents/Marketing/api/marketing.api";
import { fetchBrandingBundle } from "@/agents/brand/api/brandIdentity.api";

export default function ResultsPage() {
  const { id } = useParams();
  const { token } = useAuth();
  const [activeAgent, setActiveAgent] = useState("market");
  const [idea, setIdea] = useState(null);
  const [marketLatest, setMarketLatest] = useState(null);
  const [marketingLatest, setMarketingLatest] = useState(null);
  const [brandingBundle, setBrandingBundle] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!id || !token) return;
    let cancelled = false;
    (async () => {
      try {
        const [ideaData, marketData, marketingData, brandingData] = await Promise.all([
          apiGetIdea(id, token),
          getLatestMarketAnalysis(id, token),
          getLatestMarketingPlan(id, token),
          fetchBrandingBundle(id, token),
        ]);
        if (cancelled) return;
        setIdea(ideaData || null);
        setMarketLatest(marketData || null);
        setMarketingLatest(marketingData || null);
        setBrandingBundle(brandingData || null);
        setError("");
      } catch (e) {
        if (cancelled) return;
        setError(getErrorMessage(e));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id, token]);

  const statuses = useMemo(() => {
    const base = Object.fromEntries(AGENTS.map((a) => [a.id, "waiting"]));
    const ideaDone = Boolean(idea?.clarified_idea) || ["clarifier_done", "market_done", "done"].includes(idea?.status);
    if (ideaDone) base.clarifier = "done";
    if (marketLatest) base.market = "done";
    if (marketingLatest) base.marketing = "done";
    const hasBrand = Boolean(
      brandingBundle?.naming || brandingBundle?.slogan || brandingBundle?.palette || brandingBundle?.logo,
    );
    if (hasBrand) base.brand = "done";
    return base;
  }, [idea, marketLatest, marketingLatest, brandingBundle]);

  const project = useMemo(
    () => ({
      id,
      name: idea?.name || "Projet",
      status: idea?.status === "done" ? "completed" : "running",
    }),
    [id, idea],
  );

  const marketData = useMemo(() => {
    const payload = marketLatest?.result_json || marketLatest || {};
    const marketVoc = payload.market_voc || {};
    const competitors = payload.competitor || {};
    const demande = payload.overview?.demande || {};
    return {
      market_size: demande.taille || payload.market_size || "-",
      competitors: Array.isArray(competitors.top_competitors)
        ? competitors.top_competitors.length
        : payload.competitors || 0,
      growth: demande.cagr || payload.growth || "-",
      opportunity: competitors.opportunite_summary || payload.opportunity || "",
      top_competitors: competitors.top_competitors || payload.top_competitors || [],
      demand_summary: marketVoc.demand_summary || "",
    };
  }, [marketLatest]);

  const results = useMemo(
    () => ({
      clarifier: {
        initial: idea?.description || "",
        enhanced:
          idea?.clarified_idea?.solution_description ||
          idea?.clarified_idea?.short_pitch ||
          "",
        summary: idea?.clarified_idea?.problem || "",
      },
      market: marketData,
      marketing: marketingLatest?.result_json || marketingLatest || {},
      brand: brandingBundle || {},
      content: {},
      website: {},
      optimizer: {},
    }),
    [idea, marketData, marketingLatest, brandingBundle],
  );

  const currentData = results[activeAgent];
  const currentStatus = statuses[activeAgent] || "waiting";
  const runningIndex = AGENTS.findIndex((a) => statuses[a.id] === "running");
  const pipelineLabel =
    runningIndex >= 0
      ? `Pipeline en cours — agent ${runningIndex + 1}/${AGENTS.length}`
      : "Pipeline terminé";

  return (
    <div className="h-screen flex flex-col overflow-hidden bg-white">
      <Navbar variant="app" />
      <main className="flex flex-1 overflow-hidden">
        <div className="mx-auto w-full max-w-[1400px] px-6 py-4 flex flex-col lg:flex-row flex-1 min-h-0 overflow-hidden">
          <div className="border-b border-[#E5E7EB] bg-white px-0 py-4 lg:px-0 shrink-0 lg:border-b-0">
            <div className="flex flex-wrap items-center gap-3">
              <Link
                to="/dashboard"
                className="flex items-center gap-1 text-sm text-[#6B7280] hover:text-[#7C3AED]"
              >
                <HiOutlineArrowLeft className="h-4 w-4" /> Retour
              </Link>
              <h1 className="text-lg font-semibold text-[#111827]">
                {project.name}
              </h1>
              <Badge
                variant={project.status === "completed" ? "success" : "violet"}
              >
                {project.status === "completed" ? "Complété" : "En cours"}
              </Badge>
            </div>
            <p className="mt-1 text-sm text-[#6B7280]">{pipelineLabel}</p>
            {error ? <p className="mt-1 text-sm text-red-600">{error}</p> : null}
          </div>

          <div className="border-b border-[#E5E7EB] bg-[#F9FAFB] px-4 py-3 lg:hidden">
            <div className="flex gap-2 overflow-x-auto pb-1">
              {AGENTS.map((agent) => (
                <button
                  key={agent.id}
                  type="button"
                  onClick={() => setActiveAgent(agent.id)}
                  className={`shrink-0 rounded-lg border px-3 py-2 text-xs font-medium transition-all ${
                    activeAgent === agent.id
                      ? "border-[#7C3AED] bg-[#F5F3FF] text-[#7C3AED]"
                      : "border-[#E5E7EB] bg:white text-[#6B7280]"
                  }`}
                >
                  {agent.label}
                </button>
              ))}
            </div>
          </div>

          <aside className="hidden w-[240px] shrink-0 border-r border-[#E5E7EB] bg-[#F9FAFB] p-4 lg:block">
            <p className="mb-3 text-xs font-medium uppercase tracking-wider text-[#6B7280]">
              Agents
            </p>
            <AgentTimeline
              agents={AGENTS}
              agentStatuses={statuses}
              activeId={activeAgent}
              onSelect={setActiveAgent}
            />
          </aside>

          <div className="flex-1 min-h-0 overflow-y-auto p-4 lg:p-6">
            <ResultDisplay
              agentId={activeAgent}
              data={currentData}
              status={currentStatus}
            />
          </div>
        </div>
      </main>
    </div>
  );
}

