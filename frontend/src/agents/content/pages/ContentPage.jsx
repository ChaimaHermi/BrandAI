import { FaInstagram, FaFacebookF, FaLinkedinIn } from "react-icons/fa";
import { AGENTS } from "@/agents";
import { AgentPageHeader } from "@/agents/shared/components/AgentPageHeader";
import { SectionIntro } from "@/shared/ui/SectionIntro";
import { ErrorBanner } from "@/shared/ui/ErrorBanner";
import { Loader } from "@/shared/ui/Loader";
import { usePipeline } from "@/context/PipelineContext";
import { PlatformTabs } from "../components/PlatformTabs";
import { ContentWorkspace } from "../components/ContentWorkspace";
import { useContentGeneration } from "../hooks/useContentGeneration";

const contentAgent = AGENTS.find((a) => a.id === "content");

const PLATFORM_INTROS = {
  instagram: {
    icon: FaInstagram,
    title: "Instagram",
    description: "Créez un post accrocheur pour votre feed — ton, hashtags et visuel au rendez-vous.",
  },
  facebook: {
    icon: FaFacebookF,
    title: "Facebook",
    description: "Rédigez un post engageant pour votre page Facebook avec call-to-action personnalisé.",
  },
  linkedin: {
    icon: FaLinkedinIn,
    title: "LinkedIn",
    description: "Publiez un contenu professionnel sur LinkedIn adapté à votre réseau B2B.",
  },
};

export default function ContentPage() {
  const { idea, token } = usePipeline();

  const {
    activePlatform,
    setActivePlatform,
    forms,
    updateForm,
    generated,
    isGenerating,
    error,
    generate,
    publish,
  } = useContentGeneration({ idea, token });

  const canPublish = Boolean(generated?.caption);
  const platformIntro = PLATFORM_INTROS[activePlatform];

  return (
    <div className="app-content-scroll flex flex-1 flex-col gap-3">
      <AgentPageHeader
        agent={contentAgent}
        subtitle="Content Creator · Étape 5 sur 6"
      />

      {!idea?.id && (
        <ErrorBanner message="Chargez un projet pour générer du contenu." />
      )}

      {error && <ErrorBanner message={error} />}

      <PlatformTabs activePlatform={activePlatform} onSelect={setActivePlatform} />

      {isGenerating && (
        <div className="flex items-center gap-3 rounded-2xl border border-brand-border bg-white px-5 py-4 shadow-card">
          <Loader className="h-5 w-5" />
          <span className="text-sm text-brand-dark">Génération du contenu…</span>
        </div>
      )}

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
        onPublish={publish}
        canPublish={canPublish}
      />
    </div>
  );
}
