import { Card } from "@/shared/ui/Card";
import { PLATFORM_LABELS } from "../../constants";
import { CharacterCount } from "./CharacterCount";

export function PostPreviewPanel({ platform, caption, imageUrl, emptyHint }) {
  const hasCaption = (caption || "").trim().length > 0;
  const zone = PLATFORM_LABELS[platform] || platform;

  return (
    <Card variant="flat" padding="p-5" className="flex h-full min-h-[280px] flex-col">
      <p className="mb-3 text-xs font-extrabold uppercase tracking-wide text-ink-subtle">
        Aperçu — {zone}
      </p>

      {!hasCaption && !imageUrl && (
        <div className="flex flex-1 flex-col items-center justify-center rounded-xl border border-dashed border-brand-border bg-brand-light/20 px-4 py-10 text-center">
          <p className="text-sm font-medium text-ink-muted">{emptyHint}</p>
          <p className="mt-1 max-w-xs text-xs text-ink-subtle">
            Le texte et l’image apparaîtront ici après génération.
          </p>
        </div>
      )}

      {(hasCaption || imageUrl) && (
        <div className="flex flex-1 flex-col gap-3">
          {imageUrl && (
            <div className="overflow-hidden rounded-xl border border-brand-border bg-ink/5">
              <img
                src={imageUrl}
                alt="Aperçu visuel du post"
                className="max-h-56 w-full object-cover"
              />
            </div>
          )}

          {hasCaption && (
            <div className="rounded-xl border border-brand-border bg-white px-3 py-2.5">
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink">{caption}</p>
            </div>
          )}

          {hasCaption && (
            <CharacterCount text={caption} platform={platform} />
          )}
        </div>
      )}
    </Card>
  );
}

export default PostPreviewPanel;
