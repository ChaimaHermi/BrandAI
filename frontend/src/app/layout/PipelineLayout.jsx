import { useState } from "react";
import { useNavigate, useParams, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "@/shared/hooks/useAuth";
import { AGENTS } from "@/agents";
import { PipelineContext } from "@/context/PipelineContext";
import { usePipelineData } from "./hooks/usePipelineData";
import { usePipelineStatus } from "./hooks/usePipelineStatus";
import PipelineTopBar from "./PipelineTopBar";
import PipelineSidebar from "./PipelineSidebar";

export default function PipelineLayout() {
  const { id } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const { token, user } = useAuth();

  const [sidebarOpen, setSidebarOpen] = useState(true);

  const { idea, hasMarketResult, hasMarketingResult, hasBrandIdentityResult, refetch } =
    usePipelineData(id, token);

  const activeAgent =
    AGENTS.find((a) => location.pathname.includes("/" + a.id)) || AGENTS[0];
  const activeIndex = AGENTS.findIndex((a) => a.id === activeAgent.id);
  const contentSubRoute = location.pathname.includes("/content/connect")
    ? "connect"
    : "schedule";

  const {
    getStatus,
    progressPct,
    pipelineEnabled,
    pipelineCompleted,
  } = usePipelineStatus({
    idea,
    hasMarketResult,
    hasMarketingResult,
    hasBrandIdentityResult,
    activeAgentId: activeAgent.id,
  });

  const userInitials = (user?.name || user?.email || "U").slice(0, 2).toUpperCase();
  const ideaTitle = (idea?.description || "Votre projet").slice(0, 26);

  function handleLaunchPipeline() {
    if (!pipelineEnabled || pipelineCompleted) return;
    navigate(`/ideas/${id}/market`, {
      state: {
        autoStartMarket: true,
        sourceIdeaId: idea?.id,
        clarifiedIdea: {
          short_pitch: idea?.clarity_short_pitch || idea?.name || "",
          solution_description: idea?.clarity_solution || idea?.description || "",
          target_users: idea?.clarity_target_users || idea?.target_audience || "",
          problem: idea?.clarity_problem || idea?.description || "",
          sector: idea?.clarity_sector || idea?.sector || "",
          country: idea?.clarity_country || "",
          country_code: idea?.clarity_country_code || "TN",
          language: idea?.clarity_language || "fr",
        },
      },
    });
  }

  return (
    <PipelineContext.Provider value={{ idea, token, refetch, onLaunchPipeline: handleLaunchPipeline, pipelineEnabled, pipelineCompleted }}>
      <div className="app-shell">
        <PipelineTopBar
          ideaTitle={ideaTitle}
          activeAgent={activeAgent}
          progressPct={progressPct}
          activeIndex={activeIndex}
          agentsCount={AGENTS.length}
          sidebarOpen={sidebarOpen}
          onToggle={() => setSidebarOpen((v) => !v)}
          userInitials={userInitials}
          onNavigateDashboard={() => navigate("/dashboard")}
        />

        <div className="app-shell-body">
          <PipelineSidebar
            ideaTitle={ideaTitle}
            activeAgent={activeAgent}
            activeIndex={activeIndex}
            progressPct={progressPct}
            sidebarOpen={sidebarOpen}
            getStatus={getStatus}
            pipelineEnabled={pipelineEnabled}
            pipelineCompleted={pipelineCompleted}
            idea={idea}
            activeContentSubRoute={contentSubRoute}
            onNavigateDashboard={() => navigate("/dashboard")}
            onNavigateAgent={(agentId) =>
              navigate(
                agentId === "content"
                  ? `/ideas/${id}/content/schedule`
                  : `/ideas/${id}/${agentId}`
              )
            }
            onNavigateContentSubRoute={(subRoute) =>
              navigate(`/ideas/${id}/content/${subRoute}`)
            }
            onLaunchPipeline={handleLaunchPipeline}
          />

          <div className="app-shell-content">
            <Outlet />
          </div>
        </div>
      </div>
    </PipelineContext.Provider>
  );
}
