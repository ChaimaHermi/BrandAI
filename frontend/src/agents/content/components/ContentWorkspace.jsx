import { FiZap, FiEye, FiSend, FiFileText } from "react-icons/fi";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { ContentForm } from "./ContentForm";
import { PostPreviewPanel } from "./preview/PostPreviewPanel";

/* ── Section header ────────────────────────────────────────────────────────── */
function SectionHeader({ icon: Icon, title, subtitle }) {
  return (
    <div className="flex items-start gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-brand-light">
        <Icon className="h-4 w-4 text-brand" />
      </div>
      <div>
        <p className="text-sm font-bold text-ink">{title}</p>
        {subtitle && (
          <p className="text-2xs text-ink-muted">{subtitle}</p>
        )}
      </div>
    </div>
  );
}

/* ── Main workspace ────────────────────────────────────────────────────────── */
export function ContentWorkspace({
  activePlatform,
  forms,
  updateForm,
  generated,
  isGenerating,
  onGenerate,
  onOpenPublishModal,
  canPublish,
  publishLoading,
}) {
  const formValues = forms[activePlatform];
  const hasGenerated = !!(generated?.caption || generated?.imageUrl);

  return (
    <div className="grid gap-4 lg:grid-cols-2 lg:gap-6">

      {/* ── Left column : form ─────────────────────────────────────────────── */}
      <Card padding="p-5" className="shadow-card flex flex-col gap-5">

        <SectionHeader
          icon={FiFileText}
          title="Brief de contenu"
          subtitle="Renseignez les paramètres pour guider la génération"
        />

        <div className="h-px bg-brand-border" />

        <ContentForm
          platform={activePlatform}
          values={formValues}
          onChange={updateForm}
        />

        {/* ── Actions ──────────────────────────────────────────────────────── */}
        <div className="mt-auto flex flex-col gap-2 pt-1">
          {/* Generate — primary CTA, full width */}
          <button
            type="button"
            disabled={isGenerating}
            onClick={onGenerate}
            className={`
              relative flex w-full items-center justify-center gap-2 overflow-hidden
              rounded-xl px-5 py-3 text-sm font-semibold text-white shadow-sm
              transition-all duration-200
              ${isGenerating
                ? "cursor-not-allowed bg-brand/60"
                : "bg-brand hover:bg-brand-dark active:scale-[0.98]"
              }
            `}
          >
            <FiZap
              className={`h-4 w-4 shrink-0 ${isGenerating ? "animate-pulse" : ""}`}
            />
            {isGenerating ? "Génération en cours…" : "Générer le contenu"}
            {/* subtle shimmer on idle */}
            {!isGenerating && (
              <span
                aria-hidden
                className="pointer-events-none absolute inset-0 rounded-xl opacity-0 transition-opacity duration-300 hover:opacity-100"
                style={{
                  background:
                    "linear-gradient(105deg,transparent 40%,rgba(255,255,255,.15) 50%,transparent 60%)",
                }}
              />
            )}
          </button>

          {/* Publish — secondary, full width, shown only when there's something to publish */}
          {hasGenerated && (
            <div className="flex flex-col gap-1.5">
              <Button
                type="button"
                variant="secondary"
                size="md"
                className="w-full"
                disabled={!canPublish || publishLoading}
                onClick={onOpenPublishModal}
              >
                <FiSend className="h-3.5 w-3.5 shrink-0" />
                {publishLoading ? "Publication…" : "Publier depuis la plateforme"}
              </Button>
              <p className="text-center text-2xs leading-snug text-ink-muted">
                Connexion Facebook ou LinkedIn si besoin, choix de votre Page ou compte, puis envoi du post.
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* ── Right column : preview ─────────────────────────────────────────── */}
      <Card padding="p-5" className="shadow-card flex flex-col gap-5">

        <div className="flex items-center justify-between">
          <SectionHeader
            icon={FiEye}
            title="Aperçu du post"
            subtitle="Rendu simulé sur la plateforme choisie"
          />
          {hasGenerated && !publishLoading && (
            <span className="inline-flex items-center gap-1 rounded-full bg-success/10 px-2.5 py-1 text-2xs font-semibold text-success">
              <span className="h-1.5 w-1.5 rounded-full bg-success" />
              Prêt
            </span>
          )}
        </div>

        <div className="h-px bg-brand-border" />

        <PostPreviewPanel
          platform={generated?.platform || activePlatform}
          caption={generated?.caption}
          imageUrl={generated?.imageUrl}
          emptyHint="Générez d'abord votre contenu"
        />
      </Card>

    </div>
  );
}

export default ContentWorkspace;
