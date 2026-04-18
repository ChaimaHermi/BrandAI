import { PLATFORMS, PLATFORM_LABELS } from "../constants";
import { Button } from "@/shared/ui/Button";

/**
 * Flux : « Publier sur [plateforme] » → connexion dédiée → Publier maintenant.
 */
export default function PublishPlatformModal({
  open,
  onClose,
  platform,
  generated,
  publishLoading,
  social,
  onPublishNow,
}) {
  if (!open) return null;

  const label = PLATFORM_LABELS[platform] || platform;
  const caption = (generated?.caption || "").trim();
  const imageUrl = generated?.imageUrl || null;

  const needsMeta =
    platform === PLATFORMS.facebook || platform === PLATFORMS.instagram;
  const needsLinkedIn = platform === PLATFORMS.linkedin;

  const metaReady =
    social.metaConnected &&
    social.selectedPageId &&
    social.selectedPage?.access_token;
  const linkedinReady = social.linkedinConnected;

  const canPublishNow =
    caption &&
    (needsMeta
      ? metaReady &&
        (platform === PLATFORMS.facebook ||
          (platform === PLATFORMS.instagram && imageUrl?.startsWith("https")))
      : needsLinkedIn
        ? linkedinReady
        : false);

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/45 p-4"
      role="dialog"
      aria-modal="true"
      aria-labelledby="publish-modal-title"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="max-h-[90vh] w-full max-w-md overflow-y-auto rounded-2xl border border-brand-border bg-white shadow-xl">
        <div className="border-b border-brand-border bg-brand-light/50 px-5 py-4">
          <h2 id="publish-modal-title" className="text-lg font-bold text-brand-dark">
            Publier sur {label}
          </h2>
          <p className="mt-1 text-xs text-brand-muted">
            Connectez-vous pour cette plateforme, puis validez la publication.
          </p>
        </div>

        <div className="space-y-4 px-5 py-4">
          {needsLinkedIn && (
            <div className="rounded-xl border border-brand-border bg-[#FAFAFC] p-4">
              <p className="text-sm font-medium text-brand-dark">LinkedIn — votre profil</p>
              <p className="mt-1 text-xs text-brand-muted">
                Autorisation <code className="text-[11px]">w_member_social</code> pour publier sur
                votre profil.
                {imageUrl?.startsWith("https") ? (
                  <> Une image HTTPS (aperçu) sera incluse au post.</>
                ) : null}
              </p>
              {!social.linkedinConnected ? (
                <Button
                  type="button"
                  variant="primary"
                  size="md"
                  className="mt-3 w-full"
                  disabled={social.connectBusy === "linkedin"}
                  onClick={social.openLinkedInConnect}
                >
                  {social.connectBusy === "linkedin" ? "Ouverture…" : "Se connecter à LinkedIn"}
                </Button>
              ) : (
                <p className="mt-2 text-sm text-emerald-700">
                  Compte LinkedIn connecté
                  {social.linkedinName ? ` (${social.linkedinName})` : ""}.
                </p>
              )}
            </div>
          )}

          {needsMeta && (
            <div className="rounded-xl border border-brand-border bg-[#FAFAFC] p-4">
              <p className="text-sm font-medium text-brand-dark">
                {platform === PLATFORMS.instagram ? "Instagram (via Page Facebook)" : "Facebook Page"}
              </p>
              <p className="mt-1 text-xs text-brand-muted">
                Connexion Meta : choisissez ensuite la Page sur laquelle publier
                {platform === PLATFORMS.instagram
                  ? " (compte Instagram professionnel lié à cette Page)."
                  : "."}
              </p>
              {!social.metaConnected ? (
                <Button
                  type="button"
                  variant="primary"
                  size="md"
                  className="mt-3 w-full"
                  disabled={social.connectBusy === "meta"}
                  onClick={social.openMetaConnect}
                >
                  {social.connectBusy === "meta" ? "Ouverture…" : "Se connecter avec Facebook (Meta)"}
                </Button>
              ) : (
                <>
                  <label className="mt-3 block text-2xs font-semibold uppercase text-brand-muted">
                    Page Facebook
                  </label>
                  <select
                    className="mt-1 w-full rounded-lg border border-brand-border bg-white px-3 py-2 text-sm text-brand-dark"
                    value={social.selectedPageId}
                    onChange={(e) => social.setSelectedPageId(e.target.value)}
                  >
                    <option value="">Sélectionner une page…</option>
                    {social.metaPages.map((p) => (
                      <option key={p.id} value={String(p.id)}>
                        {p.name || p.id}
                      </option>
                    ))}
                  </select>
                </>
              )}
            </div>
          )}

          {platform === PLATFORMS.instagram && (!imageUrl || !imageUrl.startsWith("https")) && (
            <p className="rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-900">
              Instagram exige une image avec URL HTTPS (générez un post avec image).
            </p>
          )}

          {!caption && (
            <p className="text-sm text-red-700">Aucun texte généré — utilisez « Générer » d’abord.</p>
          )}
        </div>

        <div className="flex flex-wrap justify-end gap-2 border-t border-brand-border bg-[#FAFAFC] px-5 py-4">
          <Button type="button" variant="secondary" size="md" onClick={onClose}>
            Annuler
          </Button>
          <Button
            type="button"
            variant="primary"
            size="md"
            disabled={!canPublishNow || publishLoading}
            onClick={async () => {
              await onPublishNow();
            }}
          >
            {publishLoading ? "Publication…" : "Publier maintenant"}
          </Button>
        </div>
      </div>
    </div>
  );
}
