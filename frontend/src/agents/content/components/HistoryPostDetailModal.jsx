import { useEffect, useMemo, useState } from "react";
import { toast } from "react-toastify";
import {
  FiX, FiEdit3, FiRefreshCw, FiSend, FiCalendar, FiCheckCircle,
} from "react-icons/fi";
import { FaInstagram, FaFacebookF, FaLinkedinIn } from "react-icons/fa";
import { Button } from "@/shared/ui/Button";
import { PostPreviewPanel } from "./preview/PostPreviewPanel";
import PublishPlatformModal from "./PublishPlatformModal";
import { GenerationProgressModal } from "./generation-progress";
import { useSocialPublish } from "../hooks/useSocialPublish";
import { useContentGenerationSSE } from "../hooks/useContentGenerationSSE";
import { useContentBrandPreview } from "../hooks/useContentBrandPreview";
import { buildGenerationPayload, getInitialFormForPlatform } from "../contentFormConfig";
import { PLATFORM_LABELS } from "../constants";
import { apiPatchGeneratedContent } from "@/services/generatedContentApi";
import { apiCreateScheduledPublication } from "@/services/scheduledPublicationsApi";

const PLATFORM_META = {
  instagram: {
    Icon: FaInstagram,
    headerStyle: { background: "linear-gradient(135deg,#833AB4,#E1306C,#FCB045)" },
  },
  facebook: {
    Icon: FaFacebookF,
    headerStyle: { background: "#1877F2" },
  },
  linkedin: {
    Icon: FaLinkedinIn,
    headerStyle: { background: "#0A66C2" },
  },
};

function pad2(n) { return String(n).padStart(2, "0"); }
function toDatetimeLocalValue(d) {
  return `${d.getFullYear()}-${pad2(d.getMonth()+1)}-${pad2(d.getDate())}T${pad2(d.getHours())}:${pad2(d.getMinutes())}`;
}

function RegenModal({ open, value, onChange, onClose, onConfirm, loading }) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-[155] flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
      role="dialog" aria-modal="true"
    >
      <div className="w-full max-w-lg rounded-2xl border border-brand-border bg-white p-4 shadow-xl">
        <p className="mb-2 text-sm font-bold text-ink">Consigne de régénération</p>
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={4}
          className="mb-3 w-full rounded-lg border border-brand-border px-3 py-2 text-sm outline-none focus:border-brand"
          placeholder="Ex. : ton plus court, ajouter un emoji, CTA plus direct…"
        />
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" size="sm" onClick={onClose}>Annuler</Button>
          <Button type="button" variant="secondary" size="sm" onClick={onConfirm} disabled={loading}>
            <FiRefreshCw className="h-3.5 w-3.5" />
            {loading ? "…" : "Régénérer"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function ScheduleModal({ open, onClose, onConfirm, loading }) {
  const defaultDt = toDatetimeLocalValue(new Date(Date.now() + 24 * 60 * 60 * 1000));
  const [dt, setDt] = useState(defaultDt);
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-[155] flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
      role="dialog" aria-modal="true"
    >
      <div className="w-full max-w-sm rounded-2xl border border-brand-border bg-white p-4 shadow-xl">
        <p className="mb-3 text-sm font-bold text-ink">Planifier la publication</p>
        <input
          type="datetime-local"
          value={dt}
          onChange={(e) => setDt(e.target.value)}
          className="w-full rounded-lg border border-brand-border bg-white px-3 py-2 text-sm outline-none focus:border-brand"
        />
        <div className="mt-3 flex justify-end gap-2">
          <Button type="button" variant="ghost" size="sm" onClick={onClose}>Annuler</Button>
          <Button
            type="button" variant="primary" size="sm"
            disabled={loading || !dt}
            onClick={() => onConfirm(dt)}
          >
            <FiCalendar className="h-3.5 w-3.5" />
            {loading ? "…" : "Planifier"}
          </Button>
        </div>
      </div>
    </div>
  );
}

/**
 * @param {{ open: boolean, onClose: () => void, ideaId: number, token: string, row: object | null, onUpdated?: () => void }} props
 */
export default function HistoryPostDetailModal({ open, onClose, ideaId, token, row: initialRow, onUpdated }) {
  const social = useSocialPublish(ideaId);
  const { startStream, isStreaming, steps, resetSSE } = useContentGenerationSSE();

  const [caption, setCaption]             = useState("");
  const [imageUrl, setImageUrl]           = useState(null);
  const [isEditing, setIsEditing]         = useState(false);
  const [draftCaption, setDraftCaption]   = useState("");
  const [regenOpen, setRegenOpen]         = useState(false);
  const [regenInstruction, setRegenInstruction] = useState("");
  const [publishOpen, setPublishOpen]     = useState(false);
  const [publishLoading, setPublishLoading] = useState(false);
  const [scheduleOpen, setScheduleOpen]   = useState(false);
  const [scheduleLoading, setScheduleLoading] = useState(false);

  const previewIdea = useMemo(() => (ideaId ? { id: ideaId } : null), [ideaId]);
  const brandPreview = useContentBrandPreview(previewIdea, token);

  useEffect(() => {
    if (!open || !initialRow) return;
    resetSSE();
    setIsEditing(false);
    setRegenOpen(false);
    setPublishOpen(false);
    setScheduleOpen(false);
    setRegenInstruction("");
    setCaption(initialRow.caption || "");
    setImageUrl(initialRow.image_url || null);
    setDraftCaption(initialRow.caption || "");
  }, [open, initialRow, resetSSE]);

  if (!open || !initialRow) return null;

  const platform = initialRow.platform || "instagram";
  const meta     = PLATFORM_META[platform] || PLATFORM_META.instagram;
  const label    = PLATFORM_LABELS[platform] || platform;
  const isPublished = initialRow.status === "published";

  async function handleSaveEdit() {
    const next = (draftCaption || "").trim();
    if (!next) { toast.warning("La légende ne peut pas être vide."); return; }
    try {
      await apiPatchGeneratedContent(ideaId, initialRow.id, token, {
        caption: next,
        char_count: next.length,
        status: "edited",
      });
      setCaption(next);
      setIsEditing(false);
      toast.success("Modifications enregistrées.");
      onUpdated?.();
    } catch (e) {
      toast.error(e?.message || "Enregistrement échoué.");
    }
  }

  async function handleRegenerate() {
    const instruction = (regenInstruction || "").trim();
    if (!instruction) { toast.warning("Indiquez une consigne pour la régénération."); return; }
    const subjectSeed = (caption || "Post").slice(0, 200);
    const form = { ...getInitialFormForPlatform(platform), subject: subjectSeed };
    const payload = buildGenerationPayload(ideaId, platform, form, {
      alignWithProject: true,
      previousCaption: caption,
      regenerationInstruction: instruction,
    });
    setRegenOpen(false);
    resetSSE();
    await startStream(payload, token, {
      onResult: async (result) => {
        const cap = (result.caption || "").trim();
        const img = result.image_url || null;
        try {
          await apiPatchGeneratedContent(ideaId, initialRow.id, token, {
            caption: cap,
            image_url: img,
            char_count: result.char_count ?? cap.length,
            status: "edited",
          });
          setCaption(cap);
          setImageUrl(img);
          setDraftCaption(cap);
          setRegenInstruction("");
          toast.success("Contenu régénéré.");
          onUpdated?.();
        } catch (e) {
          toast.error(e?.message || "Sauvegarde après régénération échouée.");
        }
      },
      onError: (m) => toast.error(m),
    });
  }

  async function handlePublishNow() {
    setPublishLoading(true);
    try {
      await social.publishToPlatform(platform, { caption, imageUrl });
      try {
        await apiPatchGeneratedContent(ideaId, initialRow.id, token, { status: "published" });
      } catch { toast.warning("Publié, mais le statut n'a pas été mis à jour."); }
      toast.success(`Publié sur ${label} avec succès.`);
      setPublishOpen(false);
      onUpdated?.();
      onClose();
    } catch (e) {
      const msg = e?.message || "Publication échouée.";
      toast.error(msg);
      try {
        await apiPatchGeneratedContent(ideaId, initialRow.id, token, {
          status: "publish_failed",
          publish_error: msg.slice(0, 2000),
        });
      } catch { /* ignore */ }
    } finally {
      setPublishLoading(false);
    }
  }

  async function handleSchedule(datetimeLocal) {
    const instant = new Date(datetimeLocal);
    if (Number.isNaN(instant.getTime())) { toast.warning("Date invalide."); return; }
    setScheduleLoading(true);
    try {
      await apiCreateScheduledPublication(ideaId, token, {
        generated_content_id: initialRow.id,
        scheduled_at: instant.toISOString(),
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        title: caption.slice(0, 120) || undefined,
      });
      toast.success("Publication planifiée avec succès.");
      setScheduleOpen(false);
      onUpdated?.();
    } catch (e) {
      toast.error(e?.message || "Planification échouée.");
    } finally {
      setScheduleLoading(false);
    }
  }

  return (
    <>
      <div
        className="fixed inset-0 z-[150] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
        onClick={(e) => e.target === e.currentTarget && onClose()}
        role="dialog" aria-modal="true" aria-labelledby="hist-detail-title"
      >
        <div className="flex max-h-[92vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-brand-border bg-white shadow-2xl">

          {/* Header */}
          <div className="flex shrink-0 items-start justify-between gap-3 px-5 py-4 text-white" style={meta.headerStyle}>
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/20">
                <meta.Icon className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <h2 id="hist-detail-title" className="text-base font-bold leading-tight">
                  {label} · détail du post
                </h2>
                <p className="mt-0.5 text-xs text-white/85">
                  statut : {initialRow.status} · {new Date(initialRow.created_at).toLocaleDateString("fr-FR")}
                </p>
              </div>
            </div>
            <button
              type="button" onClick={onClose} aria-label="Fermer"
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/20 text-white hover:bg-white/30"
            >
              <FiX className="h-4 w-4" />
            </button>
          </div>

          {/* Body */}
          <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-5 lg:flex-row lg:gap-5">

            {/* Actions */}
            <div className="flex flex-1 flex-col gap-4 lg:max-w-sm">
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button" variant="secondary" size="md"
                  disabled={isPublished || isStreaming}
                  onClick={() => { setDraftCaption(caption); setIsEditing(true); }}
                >
                  <FiEdit3 className="h-3.5 w-3.5" /> Modifier le texte
                </Button>
                <Button
                  type="button" variant="secondary" size="md"
                  disabled={isPublished || isStreaming}
                  onClick={() => setRegenOpen(true)}
                >
                  <FiRefreshCw className="h-3.5 w-3.5" /> Régénérer
                </Button>
                <Button
                  type="button" variant="secondary" size="md"
                  disabled={!caption.trim() || publishLoading}
                  onClick={() => setPublishOpen(true)}
                >
                  <FiSend className="h-3.5 w-3.5" /> Publier maintenant
                </Button>
                {!isPublished && (
                  <Button
                    type="button" variant="primary" size="md"
                    disabled={!caption.trim() || scheduleLoading}
                    onClick={() => setScheduleOpen(true)}
                  >
                    <FiCalendar className="h-3.5 w-3.5" /> Planifier
                  </Button>
                )}
              </div>

              {/* Zone édition */}
              {isEditing && !isPublished && (
                <div className="rounded-xl border border-brand-border bg-brand-light/20 p-3">
                  <p className="mb-2 text-2xs font-bold uppercase text-brand">Édition</p>
                  <textarea
                    value={draftCaption}
                    onChange={(e) => setDraftCaption(e.target.value)}
                    rows={8}
                    className="w-full rounded-lg border border-brand-border bg-white px-3 py-2 text-sm outline-none focus:border-brand"
                  />
                  <div className="mt-2 flex justify-end gap-2">
                    <Button type="button" variant="ghost" size="sm"
                      onClick={() => { setDraftCaption(caption); setIsEditing(false); }}>
                      Annuler
                    </Button>
                    <Button type="button" variant="secondary" size="sm" onClick={handleSaveEdit}>
                      <FiCheckCircle className="h-3.5 w-3.5" /> Enregistrer
                    </Button>
                  </div>
                </div>
              )}
            </div>

            {/* Aperçu */}
            <div className="flex flex-1 flex-col gap-3 rounded-xl border border-brand-border bg-white p-4 shadow-sm">
              <p className="text-2xs font-bold uppercase tracking-wider text-ink-muted">
                Aperçu — {label}
              </p>
              <PostPreviewPanel
                platform={platform}
                caption={isEditing ? draftCaption : caption}
                imageUrl={imageUrl}
                emptyHint="Aucun contenu"
                brandDisplayName={brandPreview.brandName}
                brandLogoUrl={brandPreview.logoUrl}
              />
            </div>
          </div>
        </div>
      </div>

      <RegenModal
        open={regenOpen}
        value={regenInstruction}
        onChange={setRegenInstruction}
        onClose={() => setRegenOpen(false)}
        onConfirm={handleRegenerate}
        loading={isStreaming}
      />

      <ScheduleModal
        open={scheduleOpen}
        onClose={() => setScheduleOpen(false)}
        onConfirm={handleSchedule}
        loading={scheduleLoading}
      />

      <PublishPlatformModal
        open={publishOpen}
        onClose={() => setPublishOpen(false)}
        platform={platform}
        generated={{ caption, imageUrl, platform, dbId: initialRow.id }}
        publishLoading={publishLoading}
        social={social}
        onPublishNow={handlePublishNow}
      />

      <GenerationProgressModal
        open={isStreaming}
        platform={platform}
        steps={steps}
        isStreaming={isStreaming}
        error={null}
      />
    </>
  );
}
