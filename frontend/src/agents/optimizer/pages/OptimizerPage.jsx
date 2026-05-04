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

const optimizerAgent = AGENTS.find((a) => a.id === "optimizer");

function formatSyncEvent(ev) {
  if (!ev || typeof ev !== "object") return JSON.stringify(ev);
  const t = ev.type;
  if (t === "warnings") return `Avertissements : ${(ev.warnings || []).join(" · ")}`;
  if (t === "started") return `Démarrage → ${ev.platforms_total ?? "?"} plateforme(s), dossier : ${ev.output_dir || ""}`;
  if (t === "platform_start") return `Extraction : ${ev.platform || "?"}`;
  if (t === "platform_done") {
    return `Terminé : ${ev.platform} (${ev.posts_count ?? "?"} posts) → ${ev.normalized_path || ""}`;
  }
  if (t === "platform_error") return `Erreur ${ev.platform} : ${ev.error || ""}`;
  if (t === "complete") return `Pipeline terminé. Sortie : ${ev.output_dir || ""}`;
  if (t === "fatal") return `Erreur fatale : ${ev.detail || ""}`;
  return JSON.stringify(ev);
}

export default function OptimizerPage() {
  const { idea, token } = usePipeline();

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
    runSocialEtlSync,
  } = useOptimizer({ ideaId: idea?.id ?? null, token });

  const connectHref = idea?.id ? `/ideas/${idea.id}/content/connect` : "#";

  return (
    <div className="app-content-scroll flex flex-1 flex-col gap-3">

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
          {syncEvents.length > 0 && (
            <div className="rounded border border-brand-light/50 bg-brand-light/10 p-3">
              <p className="text-2xs font-bold uppercase tracking-wider text-ink-muted">Progression (SSE)</p>
              <ul className="mt-2 max-h-48 list-inside list-decimal space-y-1 overflow-y-auto text-2xs text-ink">
                {syncEvents.map((ev, i) => (
                  <li key={`${ev.type}-${i}`} className="break-words">
                    {formatSyncEvent(ev)}
                  </li>
                ))}
              </ul>
            </div>
          )}
          {lastSyncResult?.output_dir && (
            <p className="text-2xs text-ink-muted">
              Données écrites côté serveur :{" "}
              <code className="rounded bg-brand-light/30 px-1 py-0.5">{lastSyncResult.output_dir}</code>
              {lastSyncResult.warnings?.length > 0 && (
                <span className="block pt-1">
                  Avertissements : {lastSyncResult.warnings.join(" · ")}
                </span>
              )}
            </p>
          )}
        </Card>
      )}

      <PlatformNav
        activePlatform={activePlatform}
        onPlatformChange={onPlatformChange}
      />

      <div className="flex items-start gap-3">

        <AgentRecommendation
          recommendation={recommendation}
          loading={recoLoading}
          error={null}
          activePlatform={activePlatform}
          onRegenerate={onRegenerate}
        />

      </div>

    </div>
  );
}
