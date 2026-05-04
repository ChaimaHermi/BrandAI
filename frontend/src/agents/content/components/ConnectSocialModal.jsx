import { useEffect, useState } from "react";
import { FaFacebookF, FaInstagram, FaLinkedinIn } from "react-icons/fa";
import {
  FiCheck, FiCheckCircle, FiExternalLink, FiInfo, FiLink,
  FiLogOut, FiRefreshCw, FiShield, FiX,
} from "react-icons/fi";
import { Button } from "@/shared/ui/Button";

/* ── Meta-info per provider ─────────────────────────────────────────── */
const META_PLATFORM = {
  header: { background: "#1877F2" },
  Icon: FaFacebookF,
  label: "Facebook & Instagram",
  tagline: "Une connexion pour publier sur vos Pages Facebook et Instagram.",
};
const INSTAGRAM_PLATFORM = {
  header: { background: "linear-gradient(135deg,#833AB4,#E1306C,#FCB045)" },
  Icon: FaInstagram,
  label: "Instagram",
  tagline: "Profil professionnel lié à la Page Meta sélectionnée.",
};
const LINKEDIN_PLATFORM = {
  header: { background: "#0A66C2" },
  Icon: FaLinkedinIn,
  label: "LinkedIn",
  tagline: "Connexion dédiée pour publier sur votre profil ou Page LinkedIn.",
};

/* ── Reusable platform section ──────────────────────────────────────── */
function PlatformSection({ platform, connected, children }) {
  const { header, Icon, label, tagline } = platform;
  return (
    <div className="overflow-hidden rounded-2xl border border-brand-border bg-white shadow-sm">
      {/* Colored header */}
      <div className="flex items-center gap-3 px-4 py-3" style={header}>
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-white/20">
          <Icon className="h-4 w-4 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-bold text-white leading-tight">{label}</p>
          <p className="text-[11px] text-white/75 leading-tight mt-0.5">{tagline}</p>
        </div>
        {connected && (
          <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-white/25 px-2.5 py-1 text-[11px] font-bold text-white">
            <FiCheck className="h-3 w-3" />
            Connecté
          </span>
        )}
      </div>

      {/* Body */}
      <div className="p-4">{children}</div>
    </div>
  );
}

/* ── Connect button ─────────────────────────────────────────────────── */
function ConnectButton({ onClick, loading, label, color, hoverColor }) {
  return (
    <button
      type="button"
      disabled={loading}
      onClick={onClick}
      className={`flex w-full items-center justify-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white shadow-sm transition-all active:scale-[0.98] disabled:opacity-60`}
      style={{ background: loading ? "#aaa" : color }}
      onMouseEnter={(e) => { if (!loading) e.currentTarget.style.background = hoverColor; }}
      onMouseLeave={(e) => { if (!loading) e.currentTarget.style.background = color; }}
    >
      {loading ? (
        <span className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
      ) : (
        <FiExternalLink className="h-4 w-4" />
      )}
      {loading ? "Ouverture de la fenêtre…" : label}
    </button>
  );
}

/* ── Connected actions row ──────────────────────────────────────────── */
function ConnectedActions({ onDisconnect, onReconnect, loading }) {
  return (
    <div className="flex flex-wrap gap-2">
      <Button type="button" variant="ghost" size="sm" onClick={onDisconnect}>
        <FiLogOut className="h-3.5 w-3.5" />
        Déconnecter
      </Button>
      <Button
        type="button"
        variant="secondary"
        size="sm"
        disabled={loading}
        onClick={onReconnect}
      >
        <FiRefreshCw className="h-3.5 w-3.5" />
        Reconnecter
      </Button>
    </div>
  );
}

/* ── Main modal ─────────────────────────────────────────────────────── */
export default function ConnectSocialModal({ open, onClose, social }) {
  const [linkedinUrlDraft, setLinkedinUrlDraft] = useState("");

  useEffect(() => {
    if (open) {
      setLinkedinUrlDraft(social.linkedinProfileUrl || "");
    }
  }, [open, social.linkedinProfileUrl]);

  if (!open) return null;

  const metaConnected = social.metaConnected;
  const instagramConnected = social.instagramConnected;
  const linkedinConnected = social.linkedinConnected;
  const allReady = metaConnected && linkedinConnected;

  return (
    <div
      className="fixed inset-0 z-[120] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-labelledby="connect-social-title"
      onClick={(e) => { if (e.target === e.currentTarget) onClose(); }}
    >
      <div className="flex max-h-[90vh] w-full max-w-xl flex-col overflow-hidden rounded-2xl border border-brand-border bg-white shadow-2xl">

        {/* ── Header ────────────────────────────────────────────── */}
        <div className="flex shrink-0 items-center gap-3 border-b border-brand-border bg-gradient-to-r from-brand-light/60 to-white px-5 py-4">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-brand-light">
            <FiLink className="h-4 w-4 text-brand" />
          </div>
          <div className="flex-1 min-w-0">
            <h2 id="connect-social-title" className="text-sm font-bold text-brand-dark">
              Gérer les connexions sociales
            </h2>
            <p className="text-2xs text-ink-muted">
              Connectez une seule fois et publiez sans interruption.
            </p>
          </div>
          {allReady && (
            <span className="shrink-0 inline-flex items-center gap-1 rounded-full bg-success/10 px-2.5 py-1 text-2xs font-semibold text-success">
              <FiCheckCircle className="h-3.5 w-3.5" />
              Tout prêt
            </span>
          )}
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-brand-border bg-white text-ink-muted transition-colors hover:bg-brand-light hover:text-brand-dark"
            aria-label="Fermer"
          >
            <FiX className="h-4 w-4" />
          </button>
        </div>

        {/* ── Body (scrollable) ──────────────────────────────────── */}
        <div className="flex-1 space-y-3 overflow-y-auto bg-[#f9f8ff] p-5">

          {/* Facebook + Instagram (Meta) */}
          <PlatformSection platform={META_PLATFORM} connected={metaConnected}>
            {!metaConnected ? (
              <ConnectButton
                onClick={social.openMetaConnect}
                loading={social.connectBusy === "meta"}
                label="Connecter avec Facebook"
                color="#1877F2"
                hoverColor="#0f66d9"
              />
            ) : (
              <div className="space-y-3">
                <div className="flex items-center gap-2 rounded-xl bg-success/5 border border-success/20 px-3 py-2">
                  <FiCheckCircle className="h-4 w-4 shrink-0 text-success" />
                  <p className="text-xs font-semibold text-success">Compte Meta relié</p>
                </div>
                <div>
                  <label className="mb-1.5 block text-2xs font-semibold uppercase tracking-wider text-ink-muted">
                    Page Facebook pour la publication
                  </label>
                  <select
                    className="w-full rounded-lg border border-brand-border bg-white px-3 py-2 text-sm text-ink focus:outline-none focus:ring-2 focus:ring-brand/30"
                    value={social.selectedPageId}
                    onChange={(e) => social.setSelectedPageId(e.target.value)}
                  >
                    <option value="">Choisir une Page…</option>
                    {social.metaPages.map((page) => (
                      <option key={page.id} value={String(page.id)}>
                        {page.name || page.id}
                      </option>
                    ))}
                  </select>
                </div>
                <ConnectedActions
                  onDisconnect={social.disconnectMeta}
                  onReconnect={() => { social.disconnectMeta(); window.setTimeout(social.openMetaConnect, 0); }}
                  loading={social.connectBusy === "meta"}
                />
              </div>
            )}
          </PlatformSection>

          {/* Instagram info */}
          <PlatformSection platform={INSTAGRAM_PLATFORM} connected={instagramConnected}>
            <div className={`flex items-start gap-2 rounded-xl px-3 py-2.5 ${instagramConnected ? "bg-success/5 border border-success/20" : "bg-amber-50 border border-amber-200"}`}>
              <FiShield className={`mt-0.5 h-4 w-4 shrink-0 ${instagramConnected ? "text-success" : "text-amber-500"}`} />
              <p className="text-xs leading-relaxed text-ink-muted">
                {!metaConnected
                  ? "Connectez Meta ci-dessus pour activer Instagram Business."
                  : instagramConnected
                    ? "Compte Instagram Business détecté et lié à la Page sélectionnée."
                    : "Aucun compte Instagram Business lié à cette Page — vérifiez Meta Business ou choisissez une autre Page."}
              </p>
            </div>
          </PlatformSection>

          {/* LinkedIn */}
          <PlatformSection platform={LINKEDIN_PLATFORM} connected={linkedinConnected}>
            {!linkedinConnected ? (
              <ConnectButton
                onClick={social.openLinkedInConnect}
                loading={social.connectBusy === "linkedin"}
                label="Connecter avec LinkedIn"
                color="#0A66C2"
                hoverColor="#084e96"
              />
            ) : (
              <div className="space-y-3">
                <div className="flex items-center gap-2 rounded-xl bg-success/5 border border-success/20 px-3 py-2">
                  <FiCheckCircle className="h-4 w-4 shrink-0 text-success" />
                  <p className="text-xs font-semibold text-success">
                    {social.linkedinName || "Compte LinkedIn connecté"}
                  </p>
                </div>
                <div className="space-y-2 rounded-xl border border-brand-border bg-[#fafbff] px-3 py-2.5">
                  <label
                    htmlFor="linkedin-profile-url"
                    className="block text-2xs font-semibold uppercase tracking-wider text-ink-muted"
                  >
                    URL du profil LinkedIn (facultatif)
                  </label>
                  <input
                    id="linkedin-profile-url"
                    type="url"
                    inputMode="url"
                    autoComplete="url"
                    placeholder="https://www.linkedin.com/in/votre-profil/"
                    value={linkedinUrlDraft}
                    onChange={(e) => setLinkedinUrlDraft(e.target.value)}
                    disabled={social.linkedinProfileUrlSaving}
                    className="w-full rounded-lg border border-brand-border bg-white px-3 py-2 text-sm text-ink placeholder:text-ink-subtle focus:outline-none focus:ring-2 focus:ring-brand/30 disabled:opacity-60"
                  />
                  <p className="flex gap-2 text-2xs leading-relaxed text-ink-muted">
                    <FiInfo className="mt-0.5 h-3.5 w-3.5 shrink-0 text-brand" aria-hidden />
                    <span>
                      Ce lien n’est pas obligatoire. Il est utile pour que l’agent{" "}
                      <strong className="text-ink">Optimizer</strong> récupère vos
                      informations publiques lorsque l’URL détectée automatiquement est
                      absente ou incorrecte.
                    </span>
                  </p>
                  <div className="flex flex-wrap gap-2 pt-0.5">
                    <Button
                      type="button"
                      variant="primary"
                      size="sm"
                      disabled={social.linkedinProfileUrlSaving}
                      onClick={() => social.saveLinkedInProfileUrl(linkedinUrlDraft)}
                    >
                      {social.linkedinProfileUrlSaving ? "Enregistrement…" : "Enregistrer le lien"}
                    </Button>
                    {Boolean(linkedinUrlDraft || social.linkedinProfileUrl) && (
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        disabled={social.linkedinProfileUrlSaving}
                        onClick={() => {
                          setLinkedinUrlDraft("");
                          social.saveLinkedInProfileUrl("");
                        }}
                      >
                        Effacer
                      </Button>
                    )}
                  </div>
                </div>
                <ConnectedActions
                  onDisconnect={social.disconnectLinkedIn}
                  onReconnect={() => { social.disconnectLinkedIn(); window.setTimeout(social.openLinkedInConnect, 0); }}
                  loading={social.connectBusy === "linkedin"}
                />
              </div>
            )}
          </PlatformSection>
        </div>

        {/* ── Footer ────────────────────────────────────────────── */}
        <div className="shrink-0 flex items-center justify-end gap-2 border-t border-brand-border bg-brand-light/20 px-5 py-3">
          <Button type="button" variant="secondary" size="md" onClick={onClose}>
            Fermer
          </Button>
        </div>
      </div>
    </div>
  );
}
