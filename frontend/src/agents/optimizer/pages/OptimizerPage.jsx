import { useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { AGENTS } from "@/agents";
import { AgentPageHeader } from "@/agents/shared/components/AgentPageHeader";
import { ErrorBanner } from "@/shared/ui/ErrorBanner";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { usePipeline } from "@/context/PipelineContext";
import { useOptimizer } from "../hooks/useOptimizer";
import { PlatformNav } from "../components/PlatformNav";
import { AgentRecommendation } from "../components/AgentRecommendation";
import OptimizerSyncModal from "../components/OptimizerSyncModal";
import KpiCards from "../components/KpiCards";
import TopPostsTable from "../components/TopPostsTable";
import EvolutionChart from "../components/EvolutionChart";
import ReactionsDonut from "../components/ReactionsDonut";

const optimizerAgent = AGENTS.find((a) => a.id === "optimizer");

function formatSyncEvent(ev) {
  if (!ev || typeof ev !== "object") return JSON.stringify(ev);
  const t = ev.type;
  if (t === "warnings") return `Avertissements : ${(ev.warnings || []).join(" · ")}`;
  if (t === "started") return `Démarrage → ${ev.platforms_total ?? "?"} plateforme(s)`;
  if (t === "platform_start") return `Extraction : ${ev.platform || "?"}`;
  if (t === "platform_done") {
    return `Terminé : ${ev.platform} (${ev.posts_count ?? "?"} posts)`;
  }
  if (t === "platform_error") return `Erreur ${ev.platform} : ${ev.error || ""}`;
  if (t === "complete") return "Pipeline terminé.";
  if (t === "fatal") return `Erreur fatale : ${ev.detail || ""}`;
  return JSON.stringify(ev);
}

export default function OptimizerPage() {
  const { idea, token } = usePipeline();
  const [showSyncModal, setShowSyncModal] = useState(false);
  const wasSyncLoadingRef = useRef(false);

  const {
    activePlatform,
    onPlatformChange,
    recommendation,
    recoLoading,
    onRegenerate,
    connections,
    connectionsLoading,
    syncLoading,
    syncError,
    lastSyncResult,
    syncEvents,
    stats,
    statsLoading,
    statsError,
    runSocialEtlSync,
  } = useOptimizer({ ideaId: idea?.id ?? null, token });

  const connectHref = idea?.id ? `/ideas/${idea.id}/content/connect` : "#";

  useEffect(() => {
    if (syncLoading) setShowSyncModal(true);
  }, [syncLoading]);

  useEffect(() => {
    if (syncLoading) {
      wasSyncLoadingRef.current = true;
      return;
    }

    if (!wasSyncLoadingRef.current) return;
    wasSyncLoadingRef.current = false;

    const hasError = syncEvents.some(
      (ev) => ev?.type === "fatal" || ev?.type === "platform_error",
    );
    const isComplete = syncEvents.some((ev) => ev?.type === "complete");

    // Auto-close only on successful completion.
    if (!hasError && isComplete) {
      const t = setTimeout(() => setShowSyncModal(false), 1300);
      return () => clearTimeout(t);
    }
  }, [syncLoading, syncEvents]);

  return (
    <div className="app-content-scroll flex flex-1 flex-col gap-3">
      <OptimizerSyncModal
        open={showSyncModal && (syncLoading || syncEvents.length > 0)}
        events={syncEvents}
        isLoading={syncLoading}
        onClose={() => setShowSyncModal(false)}
      />

      <AgentPageHeader
        agent={optimizerAgent}
        subtitle="Optimisation du contenu social · Analyse IA"
      />

      {!idea?.id && <ErrorBanner message="Chargez un projet pour accéder aux analyses." />}

      {idea?.id && (
        <Card padding="p-4" className="flex flex-col gap-3 border border-brand-light/40 bg-white">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="text-xs font-bold uppercase tracking-wider text-ink-muted">
                Connexions sociales (cette idée)
              </p>
              {connectionsLoading ? (
                <p className="mt-2 text-sm text-ink-muted">Chargement…</p>
              ) : connections ? (
                <ul className="mt-2 list-inside list-disc text-sm text-ink">
                  <li>
                    Facebook :{" "}
                    {connections.has_meta_facebook
                      ? (connections.facebook_page_label || "Page connectée")
                      : "non connecté"}
                  </li>
                  <li>
                    Instagram :{" "}
                    {connections.has_instagram
                      ? (connections.instagram_label || "Compte pro")
                      : "non connecté"}
                  </li>
                  <li>
                    LinkedIn :{" "}
                    {connections.has_linkedin
                      ? (connections.linkedin_profile_url || "profil")
                      : "non connecté"}
                  </li>
                </ul>
              ) : (
                <p className="mt-2 text-sm text-amber-700">Impossible de charger le résumé des connexions.</p>
              )}
              {connections?.blockers?.length > 0 && (
                <ul className="mt-2 list-inside list-disc text-sm text-amber-800">
                  {connections.blockers.map((b) => (
                    <li key={b}>{b}</li>
                  ))}
                </ul>
              )}
            </div>
            <div className="flex flex-col items-stretch gap-2 sm:items-end">
              <Button
                type="button"
                variant="primary"
                disabled={!connections?.can_run_social_etl || syncLoading}
                onClick={() => runSocialEtlSync()}
              >
                {syncLoading ? "Synchronisation en cours…" : "Lancer la 1ère analyse d'optimisation"}
              </Button>
              <Link
                to={connectHref}
                className="text-center text-xs font-semibold text-brand hover:underline"
              >
                Gérer les connexions (Meta / LinkedIn)
              </Link>
            </div>
          </div>
          {syncError && (
            <ErrorBanner message={syncError} />
          )}
          {lastSyncResult?.warnings?.length > 0 && (
            <p className="text-2xs text-ink-muted">
              Avertissements : {lastSyncResult.warnings.join(" · ")}
            </p>
          )}
        </Card>
      )}

      <PlatformNav
        activePlatform={activePlatform}
        onPlatformChange={onPlatformChange}
      />

      {statsError && <ErrorBanner message={statsError} />}

      <KpiCards
        kpis={stats?.kpis ?? null}
        loading={statsLoading}
        activePlatform={activePlatform}
      />

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-3">
        <div className={activePlatform !== "instagram" ? "lg:col-span-2" : "lg:col-span-3"}>
          <EvolutionChart
            evolution={stats?.evolution ?? []}
            loading={statsLoading}
            activePlatform={activePlatform}
          />
        </div>
        {activePlatform !== "instagram" && (
          <ReactionsDonut
            reactions={stats?.reactions_breakdown ?? {}}
            loading={statsLoading}
          />
        )}
      </div>

      <div className="grid grid-cols-1 gap-3">
        <TopPostsTable
          posts={stats?.top_posts ?? []}
          loading={statsLoading}
          activePlatform={activePlatform}
        />
      </div>

      <AgentRecommendation
        recommendation={recommendation}
        loading={recoLoading}
        error={null}
        activePlatform={activePlatform}
        onRegenerate={onRegenerate}
      />

    </div>
  );
}
