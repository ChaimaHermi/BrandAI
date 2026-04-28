import { useState } from "react";
import { AGENTS } from "@/agents";
import { AgentPageHeader } from "@/agents/shared/components/AgentPageHeader";
import { ErrorBanner } from "@/shared/ui/ErrorBanner";
import { useWebsiteBuilder } from "../hooks/useWebsiteBuilder";
import { ChatPanel } from "../components/ChatPanel";
import { PreviewPanel } from "../components/PreviewPanel";

const websiteAgent = AGENTS.find((a) => a.id === "website");

export default function WebsiteBuilderPage() {
  const {
    phase,
    isBusy,
    canChatSubmit,
    html,
    htmlStats,
    deployment,
    messages,
    error,
    submitChatMessage,
    saveManualEdits,
    deployWebsite,
    clearDeployment,
    handleAction,
  } = useWebsiteBuilder();

  // Force iframe reload manuellement (clé dérivée du HTML, on toggle un nonce).
  const [reloadNonce, setReloadNonce] = useState(0);
  const handleRefresh = () => setReloadNonce((n) => n + 1);

  const headerSubtitle =
    phase === "deployed"
      ? "Website Builder · Site en ligne"
      : phase === "ready"
        ? "Website Builder · Itère via le chat ou édite directement le site"
        : phase === "description_ready"
          ? "Website Builder · Discute le concept puis approuve pour générer"
          : "Website Builder · Concept → Génération → Déploiement";

  return (
    <div className="app-content-scroll flex flex-1 flex-col gap-3">
      <AgentPageHeader
        agent={websiteAgent}
        subtitle={headerSubtitle}
        badge={
          deployment?.full_url ? (
            <a
              href={deployment.full_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex shrink-0 items-center gap-1 rounded-full bg-success/10 px-2.5 py-1 text-2xs font-semibold text-success transition-colors hover:bg-success/15"
            >
              <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-success" />
              En ligne
            </a>
          ) : null
        }
      />

      {error && (
        <ErrorBanner>
          {error}
        </ErrorBanner>
      )}

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-3 lg:grid-cols-[minmax(360px,_2fr)_3fr]">
        <div className="min-h-0 lg:min-h-[640px]">
          <ChatPanel
            phase={phase}
            isBusy={isBusy}
            canChatSubmit={canChatSubmit}
            messages={messages}
            onAction={handleAction}
            onSubmit={submitChatMessage}
          />
        </div>

        <div key={reloadNonce} className="min-h-[480px] lg:min-h-[640px]">
          <PreviewPanel
            html={html}
            phase={phase}
            isBusy={isBusy}
            htmlStats={htmlStats}
            deployment={deployment}
            onDeploy={deployWebsite}
            onClearDeployment={clearDeployment}
            onRefresh={handleRefresh}
            onSaveEdits={saveManualEdits}
          />
        </div>
      </div>
    </div>
  );
}
