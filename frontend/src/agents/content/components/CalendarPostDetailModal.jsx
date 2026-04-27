import { useEffect, useMemo, useState } from "react";
import { toast } from "react-toastify";
import {
  FiX, FiEdit3, FiRefreshCw, FiSend, FiClock, FiCalendar, FiCheckCircle, FiTrash2,
} from "react-icons/fi";
import { FaInstagram, FaFacebookF, FaLinkedinIn } from "react-icons/fa";
import { Button } from "@/shared/ui/Button";
import { PostPreviewPanel } from "./preview/PostPreviewPanel";
import PublishPlatformModal from "./PublishPlatformModal";
import { GenerationProgressModal } from "./generation-progress";
import { useSocialPublish } from "../hooks/useSocialPublish";
import { useContentGenerationSSE } from "../hooks/useContentGenerationSSE";
import { buildGenerationPayload, getInitialFormForPlatform } from "../contentFormConfig";
import { PLATFORMS, PLATFORM_LABELS } from "../constants";
import {
  apiGetScheduledPublication,
  apiDeleteScheduledPublication,
  apiPatchScheduledPublication,
} from "@/services/scheduledPublicationsApi";
import { apiPatchGeneratedContent } from "@/services/generatedContentApi";
import { useContentBrandPreview } from "../hooks/useContentBrandPreview";

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

function pad2(n) {
  return String(n).padStart(2, "0");
}

function toDatetimeLocalValue(d) {
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}T${pad2(d.getHours())}:${pad2(d.getMinutes())}`;
}

function RegenModal({ open, value, onChange, onClose, onConfirm, loading }) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-[145] flex items-center justify-center bg-black/40 p-4 backdrop-blur-sm"
      onClick={(e) => e.target === e.currentTarget && onClose()}
      role="dialog"
      aria-modal="true"
    >
      <div className="w-full max-w-lg rounded-2xl border border-brand-border bg-white p-4 shadow-xl">
        <p className="mb-2 text-sm font-bold text-ink">Consigne de régénération</p>
        <textarea
          value={value}
          onChange={(e) => onChange(e.target.value)}
          rows={4}
          className="mb-3 w-full rounded-lg border border-brand-border px-3 py-2 text-sm outline-none focus:border-brand"
          placeholder="Ex. : ton plus court, CTA plus direct…"
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

/**
 * @param {{ open: boolean, onClose: () => void, ideaId: number, token: string, scheduleId: number | null, onUpdated?: () => void }} props
 */
export default function CalendarPostDetailModal({
  open,
  onClose,
  ideaId,
  token,
  scheduleId,
  onUpdated,
}) {
  const social = useSocialPublish();
  const { startStream, isStreaming, steps, resetSSE } = useContentGenerationSSE();

  const [row, setRow] = useState(null);
  const [loading, setLoading] = useState(false);
  const [caption, setCaption] = useState("");
  const [imageUrl, setImageUrl] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [draftCaption, setDraftCaption] = useState("");
  const [rescheduleLocal, setRescheduleLocal] = useState("");
  const [regenOpen, setRegenOpen] = useState(false);
  const [regenInstruction, setRegenInstruction] = useState("");
  const [publishOpen, setPublishOpen] = useState(false);
  const [publishLoading, setPublishLoading] = useState(false);

  const previewIdea = useMemo(() => (ideaId ? { id: ideaId } : null), [ideaId]);
  const brandPreview = useContentBrandPreview(previewIdea, token);

  useEffect(() => {
    if (!open || !scheduleId || !ideaId || !token) return;
    let cancelled = false;
    resetSSE();
    setIsEditing(false);
    setRegenOpen(false);
    setPublishOpen(false);
    setRegenInstruction("");
    setLoading(true);
    (async () => {
      try {
        const r = await apiGetScheduledPublication(ideaId, scheduleId, token);
        if (cancelled) return;
        setRow(r);
        setCaption(r.caption_snapshot || "");
        setImageUrl(r.image_url_snapshot || null);
        setDraftCaption(r.caption_snapshot || "");
        const d = new Date(r.scheduled_at);
        setRescheduleLocal(toDatetimeLocalValue(d));
      } catch (e) {
        if (!cancelled) {
          toast.error(e?.message || "Chargement impossible.");
          onClose();
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, [open, scheduleId, ideaId, token, onClose, resetSSE]);

  if (!open || !scheduleId || !ideaId || !token) return null;

  const platform = row?.platform || PLATFORMS.instagram;
  const meta = PLATFORM_META[platform] || PLATFORM_META.instagram;
  const label = PLATFORM_LABELS[platform] || platform;
  const canMutate = row?.status === "scheduled";

  async function handleSaveEdit() {
    if (!row) return;
    const next = (draftCaption || "").trim();
    if (!next) {
      toast.warning("La légende ne peut pas être vide.");
      return;
    }
    try {
      await apiPatchGeneratedContent(ideaId, row.generated_content_id, token, {
        caption: next,
        char_count: next.length,
      });
      await apiPatchScheduledPublication(ideaId, scheduleId, token, {
        caption_snapshot: next,
      });
      setCaption(next);
      setIsEditing(false);
      toast.success("Modifications enregistrées.");
      onUpdated?.();
    } catch (e) {
      toast.error(e?.message || "Enregistrement échoué.");
    }
  }

  async function handleReschedule() {
    const t = (rescheduleLocal || "").trim();
    if (!t) return;
    const instant = new Date(t);
    if (Number.isNaN(instant.getTime())) {
      toast.warning("Date invalide.");
      return;
    }
    try {
      await apiPatchScheduledPublication(ideaId, scheduleId, token, {
        scheduled_at: instant.toISOString(),
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      });
      toast.success("Date de publication mise à jour.");
      const r = await apiGetScheduledPublication(ideaId, scheduleId, token);
      setRow(r);
      onUpdated?.();
    } catch (e) {
      toast.error(e?.message || "Impossible de reporter.");
    }
  }

  async function handleRegenerate() {
    if (!row) return;
    const instruction = (regenInstruction || "").trim();
    if (!instruction) {
      toast.warning("Indiquez une consigne pour la régénération.");
      return;
    }
    const gcId = row.generated_content_id;
    const subjectSeed = (row.title || caption || "Post planifié").slice(0, 200);
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
          await apiPatchGeneratedContent(ideaId, gcId, token, {
            caption: cap,
            image_url: img,
            char_count: result.char_count ?? cap.length,
          });
          await apiPatchScheduledPublication(ideaId, scheduleId, token, {
            caption_snapshot: cap,
            image_url_snapshot: img,
          });
          setCaption(cap);
          setImageUrl(img);
          setDraftCaption(cap);
          setRegenInstruction("");
          toast.success("Contenu régénéré.");
          onUpdated?.();
          const r2 = await apiGetScheduledPublication(ideaId, scheduleId, token);
          setRow(r2);
        } catch (e) {
          toast.error(e?.message || "Sauvegarde après régénération échouée.");
        }
      },
      onError: (m) => toast.error(m),
    });
  }

  async function handlePublishNow() {
    if (!row) return;
    setPublishLoading(true);
    try {
      await social.publishToPlatform(platform, {
        caption,
        imageUrl,
      });
      try {
        await apiPatchGeneratedContent(ideaId, row.generated_content_id, token, {
          status: "published",
        });
      } catch (err) {
        console.warn(err);
        toast.warning("Publié, mais le statut en base n’a pas été mis à jour.");
      }
      try {
        await apiPatchScheduledPublication(ideaId, scheduleId, token, {
          status: "cancelled",
        });
      } catch (err) {
        console.warn(err);
      }
      toast.success(`Publié sur ${label}. La planification a été annulée.`);
      setPublishOpen(false);
      onUpdated?.();
      onClose();
    } catch (e) {
      const msg = e?.message || "Publication échouée.";
      toast.error(msg);
      try {
        await apiPatchGeneratedContent(ideaId, row.generated_content_id, token, {
          status: "publish_failed",
          publish_error: msg.slice(0, 2000),
        });
      } catch {
        /* ignore */
      }
    } finally {
      setPublishLoading(false);
    }
  }

  async function handleDeleteSchedule() {
    if (!row || !canMutate) return;
    const ok = window.confirm(
      "Supprimer cette post planifiée du calendrier ? Cette action est irréversible.",
    );
    if (!ok) return;
    try {
      await apiDeleteScheduledPublication(ideaId, scheduleId, token);
      toast.success("Post supprimée du calendrier.");
      onUpdated?.();
      onClose();
    } catch (e) {
      toast.error(e?.message || "Suppression impossible.");
    }
  }

  return (
    <>
      <div
        className="fixed inset-0 z-[140] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
        onClick={(e) => e.target === e.currentTarget && onClose()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="cal-detail-title"
      >
        <div className="flex max-h-[92vh] w-full max-w-4xl flex-col overflow-hidden rounded-2xl border border-brand-border bg-white shadow-2xl">
          <div className="flex shrink-0 items-start justify-between gap-3 px-5 py-4 text-white" style={meta.headerStyle}>
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/20">
                <meta.Icon className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <h2 id="cal-detail-title" className="text-base font-bold leading-tight">
                  {label} · détail du post planifié
                </h2>
                {row && (
                  <p className="mt-0.5 text-xs text-white/85">
                    {row.title ? `${row.title} · ` : ""}
                    statut : {row.status}
                  </p>
                )}
              </div>
            </div>
            <button
              type="button"
              onClick={onClose}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-white/20 text-white hover:bg-white/30"
              aria-label="Fermer"
            >
              <FiX className="h-4 w-4" />
            </button>
          </div>

          <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-5 lg:flex-row lg:gap-5">
            {loading || !row ? (
              <p className="text-sm text-ink-muted">Chargement…</p>
            ) : (
              <>
                <div className="flex flex-1 flex-col gap-4 lg:max-w-sm">
                  <div className="rounded-xl border border-brand-border bg-brand-light/15 p-3">
                    <p className="mb-2 text-2xs font-bold uppercase tracking-wider text-ink-muted">
                      Publication prévue
                    </p>
                    <div className="flex items-center gap-2 text-xs text-ink">
                      <FiClock className="h-3.5 w-3.5 text-brand" />
                      {new Date(row.scheduled_at).toLocaleString("fr-FR", {
                        dateStyle: "medium",
                        timeStyle: "short",
                      })}
                    </div>
                    {canMutate && (
                      <div className="mt-3 flex flex-col gap-2">
                        <input
                          type="datetime-local"
                          value={rescheduleLocal}
                          onChange={(e) => setRescheduleLocal(e.target.value)}
                          className="w-full rounded-lg border border-brand-border bg-white px-2 py-1.5 text-xs"
                        />
                        <Button type="button" variant="secondary" size="sm" onClick={handleReschedule}>
                          <FiCalendar className="h-3.5 w-3.5" />
                          Mettre à jour la date
                        </Button>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-2">
                    <Button
                      type="button"
                      variant="secondary"
                      size="md"
                      disabled={!canMutate || isStreaming}
                      onClick={() => {
                        setDraftCaption(caption);
                        setIsEditing(true);
                      }}
                    >
                      <FiEdit3 className="h-3.5 w-3.5" />
                      Modifier le texte
                    </Button>
                    <Button
                      type="button"
                      variant="secondary"
                      size="md"
                      disabled={!canMutate || isStreaming}
                      onClick={() => setRegenOpen(true)}
                    >
                      <FiRefreshCw className="h-3.5 w-3.5" />
                      Régénérer
                    </Button>
                    <Button
                      type="button"
                      variant="secondary"
                      size="md"
                      disabled={!canMutate || !caption.trim() || publishLoading}
                      onClick={() => setPublishOpen(true)}
                    >
                      <FiSend className="h-3.5 w-3.5" />
                      Publier maintenant
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="md"
                      disabled={!canMutate}
                      onClick={handleDeleteSchedule}
                    >
                      <FiTrash2 className="h-3.5 w-3.5" />
                      Supprimer du calendrier
                    </Button>
                  </div>

                  {isEditing && canMutate && (
                    <div className="rounded-xl border border-brand-border bg-brand-light/20 p-3">
                      <p className="mb-2 text-2xs font-bold uppercase text-brand">Édition</p>
                      <textarea
                        value={draftCaption}
                        onChange={(e) => setDraftCaption(e.target.value)}
                        rows={8}
                        className="w-full rounded-lg border border-brand-border bg-white px-3 py-2 text-sm outline-none focus:border-brand"
                      />
                      <div className="mt-2 flex justify-end gap-2">
                        <Button
                          type="button"
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            setDraftCaption(caption);
                            setIsEditing(false);
                          }}
                        >
                          Annuler
                        </Button>
                        <Button type="button" variant="secondary" size="sm" onClick={handleSaveEdit}>
                          <FiCheckCircle className="h-3.5 w-3.5" />
                          Enregistrer
                        </Button>
                      </div>
                    </div>
                  )}
                </div>

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
              </>
            )}
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

      <PublishPlatformModal
        open={publishOpen}
        onClose={() => setPublishOpen(false)}
        platform={platform}
        generated={{
          caption,
          imageUrl,
          platform,
          dbId: row?.generated_content_id,
        }}
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
