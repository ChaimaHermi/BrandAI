import { AGENTS } from "@/agents";
import { AgentPageHeader } from "@/agents/shared/components/AgentPageHeader";
import { ErrorBanner } from "@/shared/ui/ErrorBanner";
import { usePipeline } from "@/context/PipelineContext";
import { useOptimizer } from "../hooks/useOptimizer";
import { PlatformNav } from "../components/PlatformNav";
import { KpiCards } from "../components/KpiCards";
import { EvolutionChart } from "../components/EvolutionChart";
import { TopPostsTable } from "../components/TopPostsTable";
import { AgentRecommendation } from "../components/AgentRecommendation";

const optimizerAgent = AGENTS.find((a) => a.id === "optimizer");

export default function OptimizerPage() {
  const { idea, token } = usePipeline();

  const {
    activePlatform,
    onPlatformChange,
    stats,
    statsLoading,
    recommendation,
    recoLoading,
    onRegenerate,
  } = useOptimizer({ ideaId: idea?.id ?? null, token });

  return (
    <div className="app-content-scroll flex flex-1 flex-col gap-3">

      {/* Header — identique à tous les agents */}
      <AgentPageHeader
        agent={optimizerAgent}
        subtitle="Optimisation du contenu social · Analyse IA"
      />

      {!idea?.id && <ErrorBanner message="Chargez un projet pour accéder aux analyses." />}

      {/* Tabs de plateforme */}
      <PlatformNav
        activePlatform={activePlatform}
        onPlatformChange={onPlatformChange}
      />

      {/* Zone principale : contenu à gauche, recommandation à droite */}
      <div className="flex items-start gap-3">

        {/* Recommandation IA — panneau latéral toujours visible */}
        <AgentRecommendation
          recommendation={recommendation}
          loading={recoLoading}
          error={null}
          activePlatform={activePlatform}
          onRegenerate={onRegenerate}
        />

        {/* Contenu principal */}
        <div className="flex min-w-0 flex-1 flex-col gap-3">

          {/* KPIs */}
          <KpiCards
            kpis={stats?.kpis ?? null}
            loading={statsLoading}
            activePlatform={activePlatform}
          />

          {/* Graphique d'évolution */}
          <EvolutionChart
            evolution={stats?.evolution ?? null}
            loading={statsLoading}
            activePlatform={activePlatform}
          />

          {/* Tableau des tops posts */}
          <TopPostsTable
            posts={stats?.top_posts ?? []}
            loading={statsLoading}
          />

        </div>
      </div>

    </div>
  );
}
