import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { ContentForm } from "./ContentForm";
import { PostPreviewPanel } from "./preview/PostPreviewPanel";

export function ContentWorkspace({
  activePlatform,
  forms,
  updateForm,
  generated,
  isGenerating,
  onGenerate,
  onPublish,
  canPublish,
}) {
  const formValues = forms[activePlatform];

  return (
    <Card padding="p-5" className="shadow-card">
      <div className="grid gap-6 lg:grid-cols-2 lg:gap-8">
        <div className="flex min-w-0 flex-col gap-4">
          <ContentForm
            platform={activePlatform}
            values={formValues}
            onChange={updateForm}
          />

          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant="primary"
              size="md"
              disabled={isGenerating}
              onClick={onGenerate}
            >
              {isGenerating ? "Génération…" : "Générer"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              size="md"
              disabled={!canPublish}
              onClick={onPublish}
            >
              Publier
            </Button>
          </div>
        </div>

        <div className="min-w-0">
          <PostPreviewPanel
            platform={generated?.platform || activePlatform}
            caption={generated?.caption}
            imageUrl={generated?.imageUrl}
            emptyHint="Aucun aperçu pour l'instant"
          />
        </div>
      </div>
    </Card>
  );
}

export default ContentWorkspace;
