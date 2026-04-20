import { FaInstagram, FaFacebookF, FaLinkedinIn } from "react-icons/fa";
import { AGENTS } from "@/agents";
import { AgentPageHeader } from "@/agents/shared/components/AgentPageHeader";
import { SectionIntro } from "@/shared/ui/SectionIntro";
import { ErrorBanner } from "@/shared/ui/ErrorBanner";
import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { usePipeline } from "@/context/PipelineContext";
import { PlatformTabs } from "../components/PlatformTabs";
import { ContentWorkspace } from "../components/ContentWorkspace";
import ContentProjectContextBanner from "../components/ContentProjectContextBanner";
import PublishPlatformModal from "../components/PublishPlatformModal";
import GeneratedContentsHistoryModal from "../components/GeneratedContentsHistoryModal";
import { Button } from "@/shared/ui/Button";
import { useContentGeneration } from "../hooks/useContentGeneration";
import { useSocialPublish } from "../hooks/useSocialPublish";
import { GenerationProgressModal } from "../components/generation-progress";

const contentAgent = AGENTS.find((a) => a.id === "content");

const PLATFORM_INTROS = {
  instagram: {
    icon: FaInstagram,
    title: "Instagram",
    description:
      "Créez un post pour votre compte pro, puis publiez depuis Brand AI : connexion Facebook, choix de la Page liée, envoi du post.",
  },
  facebook: {
    icon: FaFacebookF,
    title: "Facebook",
    description:
      "Générez le texte (et lien d’aperçu si besoin), puis publiez sur votre Page : connexion Facebook dans la fenêtre, sélection de la Page, validation depuis cette plateforme.",
  },
  linkedin: {
    icon: FaLinkedinIn,
    title: "LinkedIn",
    description:
      "Contenu adapté au réseau B2B. Pour publier : connexion LinkedIn autorisée depuis Brand AI, puis envoi du post depuis ici.",
  },
};

export default function ContentPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { idea, token } = usePipeline();
  const social = useSocialPublish();
  const [publishModalOpen, setPublishModalOpen] = useState(false);
  const [historyOpen, setHistoryOpen] = useState(false);

  useEffect(() => {
    if (location.state?.openGeneratedHistory) {
      setHistoryOpen(true);
      navigate(".", { replace: true, state: {} });
    }
  }, [location.state, navigate]);

  const {
    activePlatform,
    setActivePlatform,
    forms,
    updateForm,
    generated,
    isGenerating,
    generationSteps,
    error,
    generate,
    publish,
    publishLoading,
    alignWithProject,
    setAlignWithProject,
  } = useContentGeneration({
    idea,
    token,
    publishToPlatform: social.publishToPlatform,
  });

  const canPublish = Boolean(generated?.caption);
  const platformIntro = PLATFORM_INTROS[activePlatform];

  useEffect(() => {
    setPublishModalOpen(false);
  }, [activePlatform]);

  return (
    <div className="app-content-scroll flex flex-1 flex-col gap-3">
      <AgentPageHeader
        agent={contentAgent}
        subtitle="Content Creator · Étape 5 sur 6"
        action={
          idea?.id && token ? (
            <Button
              type="button"
              variant="secondary"
              size="md"
              className="shrink-0"
              onClick={() => setHistoryOpen(true)}
            >
              Historique des publications
            </Button>
          ) : null
        }
      />

      {!idea?.id && (
        <ErrorBanner message="Chargez un projet pour générer du contenu." />
      )}

      <ContentProjectContextBanner
        idea={idea}
        token={token}
        alignWithProject={alignWithProject}
        onAlignChange={setAlignWithProject}
      />

      {error && <ErrorBanner message={error} />}

      <PlatformTabs activePlatform={activePlatform} onSelect={setActivePlatform} />

      {platformIntro && (
        <SectionIntro
          icon={platformIntro.icon}
          title={platformIntro.title}
          description={platformIntro.description}
        />
      )}

      <ContentWorkspace
        activePlatform={activePlatform}
        forms={forms}
        updateForm={updateForm}
        generated={generated}
        isGenerating={isGenerating}
        onGenerate={generate}
        onOpenPublishModal={() => setPublishModalOpen(true)}
        canPublish={canPublish}
        publishLoading={publishLoading}
      />

      <PublishPlatformModal
        open={publishModalOpen}
        onClose={() => setPublishModalOpen(false)}
        platform={activePlatform}
        generated={generated}
        publishLoading={publishLoading}
        social={social}
        onPublishNow={async () => {
          const ok = await publish();
          if (ok) setPublishModalOpen(false);
        }}
      />

      <GeneratedContentsHistoryModal
        open={historyOpen}
        onClose={() => setHistoryOpen(false)}
        ideaId={idea?.id}
        token={token}
      />

      <GenerationProgressModal
        open={isGenerating}
        platform={activePlatform}
        steps={generationSteps}
        isStreaming={isGenerating}
        error={null}
      />
    </div>
  );
}
