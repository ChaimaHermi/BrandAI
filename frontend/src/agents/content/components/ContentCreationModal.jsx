import { FaInstagram, FaFacebookF, FaLinkedinIn } from "react-icons/fa";
import { FiX, FiZap, FiEdit3, FiCalendar } from "react-icons/fi";
import { useEffect, useState } from "react";
import { usePipeline } from "@/context/PipelineContext";
import { ErrorBanner } from "@/shared/ui/ErrorBanner";
import { ContentWorkspace } from "./ContentWorkspace";
import ContentProjectContextBanner from "./ContentProjectContextBanner";
import PublishPlatformModal from "./PublishPlatformModal";
import { GenerationProgressModal } from "./generation-progress";
import { useContentGeneration } from "../hooks/useContentGeneration";
import { useSocialPublish } from "../hooks/useSocialPublish";

/* ── Platform data ──────────────────────────────────────────────────── */
const PLATFORMS = {
  instagram: {
    Icon: FaInstagram,
    label: "Instagram",
    activeBg: "linear-gradient(135deg,#833AB4,#E1306C,#FCB045)",
    inactiveBg: "#ffffff",
    inactiveBorder: "#e8e4ff",
    inactiveColor: "#6B7280",
    activeShadow: "0 4px 14px rgba(225,48,108,.45)",
  },
  facebook: {
    Icon: FaFacebookF,
    label: "Facebook",
    activeBg: "#1877F2",
    inactiveBg: "#ffffff",
    inactiveBorder: "#e8e4ff",
    inactiveColor: "#6B7280",
    activeShadow: "0 4px 14px rgba(24,119,242,.45)",
  },
  linkedin: {
    Icon: FaLinkedinIn,
    label: "LinkedIn",
    activeBg: "#0A66C2",
    inactiveBg: "#ffffff",
    inactiveBorder: "#e8e4ff",
    inactiveColor: "#6B7280",
    activeShadow: "0 4px 14px rgba(10,102,194,.45)",
  },
};

const PLATFORM_ORDER = ["instagram", "facebook", "linkedin"];

/* ── Stepper ────────────────────────────────────────────────────────── */
const STEPS = [
  { id: "brief", icon: FiEdit3, label: "Brief" },
  { id: "generate", icon: FiZap, label: "Générer" },
  { id: "schedule", icon: FiCalendar, label: "Planifier" },
];

function Stepper({ activeStep }) {
  return (
    <div className="flex items-center gap-0">
      {STEPS.map((step, i) => {
        const isDone = STEPS.findIndex((s) => s.id === activeStep) > i;
        const isActive = step.id === activeStep;
        return (
          <div key={step.id} className="flex items-center">
            <div
              className={[
                "flex items-center gap-1.5 rounded-full px-3 py-1.5 text-2xs font-semibold transition-all",
                isActive
                  ? "bg-brand text-white shadow-sm"
                  : isDone
                    ? "text-brand-dark"
                    : "text-ink-subtle",
              ].join(" ")}
            >
              <step.icon className="h-3 w-3 shrink-0" />
              <span className="hidden sm:inline">{step.label}</span>
            </div>
            {i < STEPS.length - 1 && (
              <div
                className={`mx-1 h-px w-4 transition-all ${isDone ? "bg-brand/40" : "bg-brand-border"}`}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}

/* ── Platform selector row ──────────────────────────────────────────── */
function PlatformSelector({ activePlatform, onSelect }) {
  return (
    <div className="flex items-center gap-2" role="tablist" aria-label="Plateforme">
      {PLATFORM_ORDER.map((id) => {
        const p = PLATFORMS[id];
        const active = activePlatform === id;
        return (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={active}
            onClick={() => onSelect(id)}
            className={[
              "flex items-center gap-2 rounded-xl border px-4 py-2.5 text-xs font-bold transition-all duration-200",
              active ? "text-white scale-[1.04]" : "hover:border-brand-muted hover:bg-brand-light/40",
            ].join(" ")}
            style={{
              background: active ? p.activeBg : p.inactiveBg,
              borderColor: active ? "transparent" : p.inactiveBorder,
              color: active ? "#fff" : p.inactiveColor,
              boxShadow: active ? p.activeShadow : undefined,
            }}
          >
            <p.Icon className="h-3.5 w-3.5 shrink-0" aria-hidden />
            {p.label}
          </button>
        );
      })}
    </div>
  );
}

/* ── Inner modal body ───────────────────────────────────────────────── */
function ContentCreationModalInner({ onClose, onScheduleCreated }) {
  const { idea, token } = usePipeline();
  const social = useSocialPublish(idea?.id ?? null);
  const [publishModalOpen, setPublishModalOpen] = useState(false);

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
    regenerate,
    publish,
    publishLoading,
    alignWithProject,
    setAlignWithProject,
    regenerationInstruction,
    setRegenerationInstruction,
    isEditing,
    draftCaption,
    setDraftCaption,
    startEditing,
    cancelEditing,
    saveEditing,
  } = useContentGeneration({
    idea,
    token,
    publishToPlatform: social.publishToPlatform,
  });

  const canPublish = Boolean(generated?.caption);
  const hasGenerated = Boolean(generated?.caption || generated?.imageUrl);

  /* Step tracking */
  const activeStep = hasGenerated ? "schedule" : isGenerating ? "generate" : "brief";

  useEffect(() => {
    setPublishModalOpen(false);
  }, [activePlatform]);

  const activePlat = PLATFORMS[activePlatform];

  return (
    <>
      <div
        className="flex w-full max-w-5xl flex-col overflow-hidden rounded-2xl shadow-2xl"
        style={{ maxHeight: "min(92vh, 940px)" }}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="ccm-title"
      >

        {/* ── Header — fond lavande clair (brand), pas de bleu ───────── */}
        <div className="shrink-0 bg-gradient-to-br from-brand-50 via-white to-brand-100">
          {/* Top bar */}
          <div className="flex items-start justify-between gap-3 px-5 pt-4 pb-3">
            <div className="flex items-center gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-brand-border bg-white shadow-sm ring-2 ring-brand/5">
                <FiEdit3 className="h-4 w-4 text-brand" />
              </div>
              <div>
                <h2
                  id="ccm-title"
                  className="text-base font-extrabold leading-tight text-brand-darker"
                >
                  Nouveau post
                </h2>
                <p className="text-2xs font-medium text-ink-muted">
                  Générez, modifiez puis publiez ou planifiez
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="flex h-9 w-9 items-center justify-center rounded-xl border border-brand-border bg-white text-ink-muted shadow-sm transition-all hover:bg-brand-light/50 hover:text-brand-dark"
                aria-label="Fermer"
              >
                <FiX className="h-4 w-4" />
              </button>
            </div>
          </div>

          {/* Platform selector + stepper row */}
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-brand-border/60 bg-white/60 px-5 py-3 backdrop-blur-sm">
            <PlatformSelector activePlatform={activePlatform} onSelect={setActivePlatform} />
            <Stepper activeStep={activeStep} />
          </div>
        </div>

        {/* ── Scrollable body ─────────────────────────────────── */}
        <div className="min-h-0 flex-1 overflow-y-auto bg-[#f7f8fb]">

          {/* Platform accent strip */}
          <div
            className="h-1 shrink-0 transition-all duration-300"
            style={{ background: activePlat?.activeBg || "#7C3AED" }}
          />

          <div className="space-y-4 px-4 py-4 sm:px-5 sm:py-5">
            {!idea?.id && (
              <ErrorBanner message="Chargez un projet pour générer du contenu." />
            )}
            {error && <ErrorBanner message={error} />}

            {/* Project context banner */}
            <ContentProjectContextBanner
              idea={idea}
              token={token}
              alignWithProject={alignWithProject}
              onAlignChange={setAlignWithProject}
            />

            {/* Workspace */}
          <ContentWorkspace
            idea={idea}
            ideaId={idea?.id}
            token={token}
              activePlatform={activePlatform}
              forms={forms}
              updateForm={updateForm}
              generated={generated}
              isGenerating={isGenerating}
              onGenerate={generate}
              onRegenerate={regenerate}
              onOpenPublishModal={() => setPublishModalOpen(true)}
              canPublish={canPublish}
              publishLoading={publishLoading}
              regenerationInstruction={regenerationInstruction}
              onRegenerationInstructionChange={setRegenerationInstruction}
              isEditing={isEditing}
              draftCaption={draftCaption}
              onDraftCaptionChange={setDraftCaption}
              onStartEditing={startEditing}
              onCancelEditing={cancelEditing}
              onSaveEditing={saveEditing}
              onScheduleCreated={onScheduleCreated}
            />
          </div>
        </div>
      </div>

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

      <GenerationProgressModal
        open={isGenerating}
        platform={activePlatform}
        steps={generationSteps}
        isStreaming={isGenerating}
        error={null}
      />
    </>
  );
}

/* ── Public export ──────────────────────────────────────────────────── */
export default function ContentCreationModal({ open, onClose, onScheduleCreated }) {
  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-[125] flex items-center justify-center p-3 sm:p-4"
      style={{ background: "rgba(15,12,40,0.55)" }}
      onClick={onClose}
      role="presentation"
    >
      {/* Backdrop blur via pseudo element approach – works in all browsers */}
      <div className="pointer-events-none absolute inset-0 backdrop-blur-[3px]" />
      <div className="relative z-10 flex w-full max-w-5xl flex-col" style={{ maxHeight: "min(92vh,940px)" }}>
        <ContentCreationModalInner onClose={onClose} onScheduleCreated={onScheduleCreated} />
      </div>
    </div>
  );
}
