import { FaInstagram, FaFacebookF, FaLinkedinIn } from "react-icons/fa";
import {
  FiCheck, FiAlertTriangle, FiLink, FiSend, FiX, FiImage, FiRefreshCw, FiLogOut,
} from "react-icons/fi";
import { PLATFORMS, PLATFORM_LABELS } from "../constants";
import { Button } from "@/shared/ui/Button";

/* ── Méta visuelle par plateforme ─────────────────────────────────────────── */
const PLATFORM_META = {
  instagram: {
    Icon:        FaInstagram,
    headerStyle: { background: "linear-gradient(135deg,#833AB4,#E1306C,#FCB045)" },
    connectColor: "bg-[#E1306C]",
    connectHover: "hover:bg-[#c42a5e]",
  },
  facebook: {
    Icon:        FaFacebookF,
    headerStyle: { background: "#1877F2" },
    connectColor: "bg-[#1877F2]",
    connectHover: "hover:bg-[#0f66d9]",
  },
  linkedin: {
    Icon:        FaLinkedinIn,
    headerStyle: { background: "#0A66C2" },
    connectColor: "bg-[#0A66C2]",
    connectHover: "hover:bg-[#084e96]",
  },
};

/* ── Indicateur d'étape ───────────────────────────────────────────────────── */
function StepBadge({ n, done, active }) {
  return (
    <div
      className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[11px] font-bold
        ${done  ? "bg-success text-white"
        : active ? "bg-brand text-white"
        : "bg-brand-border text-ink-muted"}`}
    >
      {done ? <FiCheck className="h-3.5 w-3.5" /> : n}
    </div>
  );
}

/* ── Aperçu du contenu ────────────────────────────────────────────────────── */
function ContentPreview({ caption, imageUrl }) {
  if (!caption) return null;
  const preview = caption.length > 140 ? caption.slice(0, 140) + "…" : caption;
  return (
    <div className="rounded-xl border border-brand-border bg-brand-light/20 p-3">
      <p className="mb-1.5 text-2xs font-semibold uppercase tracking-wider text-ink-subtle">
        Contenu à publier
      </p>
      <div className="flex gap-3">
        {imageUrl?.startsWith("https") ? (
          <img
            src={imageUrl}
            alt=""
            className="h-14 w-14 shrink-0 rounded-lg object-cover"
          />
        ) : (
          <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-lg border border-dashed border-brand-border bg-white">
            <FiImage className="h-5 w-5 text-ink-subtle" />
          </div>
        )}
        <p className="text-xs leading-relaxed text-ink-muted">{preview}</p>
      </div>
    </div>
  );
}

/* ── Composant principal ──────────────────────────────────────────────────── */
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

  const label    = PLATFORM_LABELS[platform] || platform;
  const caption  = (generated?.caption || "").trim();
  const imageUrl = generated?.imageUrl || null;
  const meta     = PLATFORM_META[platform] || PLATFORM_META.instagram;
  const { Icon, headerStyle, connectColor, connectHover } = meta;

  const needsMeta     = platform === PLATFORMS.facebook || platform === PLATFORMS.instagram;
  const needsLinkedIn = platform === PLATFORMS.linkedin;

  const metaReady    = social.metaConnected && social.selectedPageId && social.selectedPage?.access_token;
  const linkedinReady = social.linkedinConnected;

  const isConnected = needsMeta ? social.metaConnected : needsLinkedIn ? social.linkedinConnected : false;
  const isReady     = needsMeta
    ? metaReady && (platform === PLATFORMS.facebook || (platform === PLATFORMS.instagram && imageUrl?.startsWith("https")))
    : needsLinkedIn ? linkedinReady : false;

  const canPublishNow = !!caption && isReady;

  const instagramMissingImage = platform === PLATFORMS.instagram && (!imageUrl || !imageUrl.startsWith("https"));

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="publish-modal-title"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="flex max-h-[90vh] w-full max-w-md flex-col overflow-hidden rounded-2xl border border-brand-border bg-white shadow-2xl">

        {/* ── Header avec couleur plateforme ─────────────────────────────── */}
        <div className="relative shrink-0 px-5 py-5" style={headerStyle}>
          <button
            type="button"
            onClick={onClose}
            className="absolute right-4 top-4 flex h-7 w-7 items-center justify-center rounded-full bg-white/20 text-white transition-colors hover:bg-white/30"
            aria-label="Fermer"
          >
            <FiX className="h-4 w-4" />
          </button>
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/20">
              <Icon className="h-5 w-5 text-white" />
            </div>
            <div>
              <h2 id="publish-modal-title" className="text-base font-bold text-white">
                Publier sur {label}
              </h2>
              <p className="text-xs text-white/75">
                Depuis Brand AI : connexion → votre Page ou compte → envoi du post
              </p>
            </div>
          </div>
        </div>

        {/* ── Contenu scrollable ──────────────────────────────────────────── */}
        <div className="flex-1 overflow-y-auto px-5 py-4 space-y-4">

          {/* Aperçu du contenu */}
          <ContentPreview caption={caption} imageUrl={imageUrl} />

          {!caption && (
            <div className="flex items-start gap-2 rounded-xl bg-red-50 border border-red-200 px-3 py-3">
              <FiAlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-red-500" />
              <p className="text-xs text-red-700">
                Aucun texte généré — utilisez « Générer » d'abord.
              </p>
            </div>
          )}

          {instagramMissingImage && (
            <div className="flex items-start gap-2 rounded-xl bg-amber-50 border border-amber-200 px-3 py-3">
              <FiAlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-amber-500" />
              <p className="text-xs text-amber-800">
                Instagram exige une image avec URL HTTPS — générez un post avec image.
              </p>
            </div>
          )}

          {(needsMeta || needsLinkedIn) && (
            <div className="rounded-xl border border-brand-border/80 bg-brand-light/30 px-3 py-2.5">
              <p className="text-2xs leading-relaxed text-ink-muted">
                <span className="font-semibold text-ink">Comment ça marche :</span>{" "}
                {needsMeta
                  ? "vous restez dans Brand AI. Une fenêtre Facebook s’ouvre pour vous connecter et autoriser l’application Brand AI à accéder à vos Pages. Nous affichons ensuite les Pages dont vous êtes gestionnaire — choisissez celle sur laquelle publier."
                  : "une fenêtre LinkedIn s’ouvre pour autoriser la publication sur votre compte. Tout se fait depuis cette plateforme."}
              </p>
            </div>
          )}

          {/* ── Étape 1 : Connexion ─────────────────────────────────────── */}
          <div className="rounded-xl border border-brand-border bg-white shadow-sm">
            <div className="flex items-center gap-3 px-4 py-3 border-b border-brand-border">
              <StepBadge n={1} done={isConnected} active={!isConnected} />
              <div className="flex-1">
                <p className="text-xs font-semibold text-ink">
                  {needsLinkedIn
                    ? "Connecter votre compte LinkedIn"
                    : "Connecter Facebook et choisir votre Page"}
                </p>
                <p className="text-2xs text-ink-muted">
                  {needsLinkedIn
                    ? "Autorisation de publication (w_member_social)"
                    : platform === PLATFORMS.instagram
                      ? "Instagram professionnel : sélectionnez la Page Facebook liée au compte"
                      : "Sélectionnez la Page Facebook sur laquelle publier ce post"}
                </p>
              </div>
              {isConnected && (
                <span className="inline-flex items-center gap-1 rounded-full bg-success/10 px-2 py-0.5 text-2xs font-semibold text-success">
                  <span className="h-1.5 w-1.5 rounded-full bg-success" />
                  Connecté
                </span>
              )}
            </div>

            <div className="px-4 py-3">
              {needsLinkedIn && (
                <>
                  {!social.linkedinConnected ? (
                    <button
                      type="button"
                      disabled={social.connectBusy === "linkedin"}
                      onClick={social.openLinkedInConnect}
                      className={`flex w-full items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all disabled:opacity-60 ${connectColor} ${connectHover}`}
                    >
                      <FiLink className="h-4 w-4" />
                      {social.connectBusy === "linkedin" ? "Ouverture…" : "Continuer avec LinkedIn"}
                    </button>
                  ) : (
                    <div className="space-y-3">
                      <p className="flex items-center gap-2 text-sm text-success">
                        <FiCheck className="h-4 w-4 shrink-0" />
                        {social.linkedinName ? `${social.linkedinName}` : "Compte LinkedIn connecté"}
                      </p>
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => social.disconnectLinkedIn()}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-brand-border bg-white px-3 py-1.5 text-2xs font-semibold text-ink-muted transition-colors hover:border-ink-muted hover:text-ink"
                        >
                          <FiLogOut className="h-3.5 w-3.5" />
                          Se déconnecter
                        </button>
                        <button
                          type="button"
                          disabled={social.connectBusy === "linkedin"}
                          onClick={() => {
                            social.disconnectLinkedIn();
                            window.setTimeout(() => social.openLinkedInConnect(), 0);
                          }}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-brand-border bg-white px-3 py-1.5 text-2xs font-semibold text-brand transition-colors hover:bg-brand-light/40 disabled:opacity-50"
                        >
                          <FiRefreshCw className="h-3.5 w-3.5" />
                          Reconnecter LinkedIn
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}

              {needsMeta && (
                <>
                  {!social.metaConnected ? (
                    <button
                      type="button"
                      disabled={social.connectBusy === "meta"}
                      onClick={social.openMetaConnect}
                      className={`flex w-full items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all disabled:opacity-60 ${connectColor} ${connectHover}`}
                    >
                      <FiLink className="h-4 w-4" />
                      {social.connectBusy === "meta" ? "Ouverture…" : "Continuer avec Facebook"}
                    </button>
                  ) : (
                    <div className="space-y-2">
                      <p className="flex items-center gap-2 text-sm text-success">
                        <FiCheck className="h-4 w-4 shrink-0" />
                        Compte relié — choisissez la Page cible
                      </p>
                      <select
                        className="w-full rounded-lg border border-brand-border bg-white px-3 py-2 text-sm text-brand-dark focus:outline-none focus:ring-2 focus:ring-brand/30"
                        value={social.selectedPageId}
                        onChange={(e) => social.setSelectedPageId(e.target.value)}
                        aria-label="Page Facebook pour la publication"
                      >
                        <option value="">Choisir une Page Facebook…</option>
                        {social.metaPages.map((p) => (
                          <option key={p.id} value={String(p.id)}>
                            {p.name || p.id}
                          </option>
                        ))}
                      </select>
                      <div className="flex flex-wrap gap-2 pt-1">
                        <button
                          type="button"
                          onClick={() => social.disconnectMeta()}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-brand-border bg-white px-3 py-1.5 text-2xs font-semibold text-ink-muted transition-colors hover:border-ink-muted hover:text-ink"
                        >
                          <FiLogOut className="h-3.5 w-3.5" />
                          Se déconnecter
                        </button>
                        <button
                          type="button"
                          disabled={social.connectBusy === "meta"}
                          onClick={() => {
                            social.disconnectMeta();
                            window.setTimeout(() => social.openMetaConnect(), 0);
                          }}
                          className="inline-flex items-center gap-1.5 rounded-lg border border-brand-border bg-white px-3 py-1.5 text-2xs font-semibold text-brand transition-colors hover:bg-brand-light/40 disabled:opacity-50"
                        >
                          <FiRefreshCw className="h-3.5 w-3.5" />
                          Reconnecter Facebook
                        </button>
                      </div>
                    </div>
                  )}
                </>
              )}
            </div>
          </div>

          {/* ── Étape 2 : Publication ───────────────────────────────────── */}
          <div className={`rounded-xl border shadow-sm transition-opacity ${isConnected ? "border-brand-border bg-white" : "border-brand-border/50 bg-brand-light/20 opacity-60"}`}>
            <div className="flex items-center gap-3 px-4 py-3">
              <StepBadge n={2} done={false} active={isConnected} />
              <div>
                <p className="text-xs font-semibold text-ink">Publier depuis Brand AI</p>
                <p className="text-2xs text-ink-muted">
                  {needsMeta
                    ? "Envoi sur la Page sélectionnée (via l’API Meta depuis cette plateforme)"
                    : needsLinkedIn
                      ? "Envoi sur votre profil LinkedIn depuis cette plateforme"
                      : "Le post sera envoyé immédiatement"}
                </p>
              </div>
            </div>
          </div>

        </div>

        {/* ── Footer ──────────────────────────────────────────────────────── */}
        <div className="shrink-0 flex items-center justify-between gap-3 border-t border-brand-border bg-brand-light/20 px-5 py-4">
          <Button type="button" variant="secondary" size="md" onClick={onClose}>
            Annuler
          </Button>
          <button
            type="button"
            disabled={!canPublishNow || publishLoading}
            onClick={async () => { await onPublishNow(); }}
            className={`flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition-all disabled:opacity-50 disabled:cursor-not-allowed ${connectColor} ${connectHover} active:scale-[0.98]`}
          >
            <FiSend className="h-4 w-4 shrink-0" />
            {publishLoading ? "Publication…" : "Publier maintenant"}
          </button>
        </div>

      </div>
    </div>
  );
}
