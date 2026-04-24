import { useEffect, useState } from "react";
import { toast } from "react-toastify";
import {
  FiZap, FiEye, FiSend, FiFileText,
  FiEdit3, FiRefreshCw, FiCheckCircle, FiX, FiCalendar,
} from "react-icons/fi";
import { Card } from "@/shared/ui/Card";
import { Button } from "@/shared/ui/Button";
import { ContentForm } from "./ContentForm";
import { PostPreviewPanel } from "./preview/PostPreviewPanel";
import { apiCreateScheduledPublication } from "@/services/scheduledPublicationsApi";
import { PLATFORM_LABELS } from "../constants";

/* ── Step badge ─────────────────────────────────────────────────────── */
function StepBadge({ step }) {
  return (
    <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-brand text-[10px] font-black text-white">
      {step}
    </span>
  );
}

/* ── Section header ─────────────────────────────────────────────────── */
function SectionHeader({ icon: Icon, title, subtitle, step }) {
  return (
    <div className="flex items-start gap-3">
      <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-brand-light">
        <Icon className="h-4 w-4 text-brand" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <p className="text-sm font-bold text-ink">{title}</p>
          {step && <StepBadge step={step} />}
        </div>
        {subtitle && <p className="text-2xs text-ink-muted">{subtitle}</p>}
      </div>
    </div>
  );
}

/* ── Action chip ────────────────────────────────────────────────────── */
function ActionChip({ icon: Icon, label, onClick, disabled, active, variant = "default" }) {
  const base = "inline-flex items-center gap-1.5 rounded-xl border px-3 py-2 text-xs font-semibold transition-all duration-150 disabled:opacity-50 disabled:cursor-not-allowed";
  const variants = {
    default: active
      ? "border-brand bg-brand text-white shadow-sm"
      : "border-brand-border bg-white text-ink-muted hover:border-brand/50 hover:bg-brand-light/40 hover:text-brand-dark",
    publish: active
      ? "border-brand bg-brand text-white shadow-sm"
      : "border-brand/60 bg-brand/5 text-brand hover:bg-brand hover:text-white",
    danger: "border-red-200 bg-red-50 text-red-600 hover:bg-red-100",
  };
  return (
    <button type="button" onClick={onClick} disabled={disabled} className={`${base} ${variants[variant]}`}>
      <Icon className="h-3.5 w-3.5 shrink-0" />
      {label}
    </button>
  );
}

/* ── Regeneration modal ─────────────────────────────────────────────── */
function RegenerationModal({ open, value, onChange, onClose, onConfirm, loading }) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-[130] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="regen-modal-title"
    >
      <div className="w-full max-w-lg overflow-hidden rounded-2xl border border-brand-border bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-brand-border bg-gradient-to-r from-brand-light/50 to-white px-4 py-3">
          <div>
            <h3 id="regen-modal-title" className="text-sm font-bold text-brand-dark">
              Régénérer le post
            </h3>
            <p className="text-2xs text-ink-muted">
              Ajoutez les améliorations souhaitées avant de relancer.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full border border-brand-border bg-white text-ink-muted transition-colors hover:bg-brand-light hover:text-brand-dark"
            aria-label="Fermer"
          >
            <FiX className="h-4 w-4" />
          </button>
        </div>
        <div className="px-4 py-3">
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            rows={5}
            className="w-full resize-y rounded-lg border border-brand-border bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/10"
            placeholder="Ex : rends le ton plus professionnel, plus court, et ajoute un CTA clair."
          />
          <p className="mt-2 text-2xs text-ink-muted leading-relaxed">
            Le texte actuel sera utilisé comme base, puis amélioré selon votre consigne.
          </p>
        </div>
        <div className="flex items-center justify-end gap-2 border-t border-brand-border bg-brand-light/20 px-4 py-3">
          <Button type="button" variant="ghost" size="sm" onClick={onClose}>
            Annuler
          </Button>
          <Button type="button" variant="secondary" size="sm" onClick={onConfirm} disabled={loading}>
            <FiRefreshCw className="h-3.5 w-3.5" />
            {loading ? "Régénération…" : "Confirmer la régénération"}
          </Button>
        </div>
      </div>
    </div>
  );
}

/* ── Schedule modal ─────────────────────────────────────────────────── */
function pad2(n) {
  return String(n).padStart(2, "0");
}

function defaultDatetimeLocalValue() {
  const d = new Date();
  d.setSeconds(0, 0);
  d.setMinutes(0);
  d.setHours(d.getHours() + 1);
  return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(d.getDate())}T${pad2(d.getHours())}:${pad2(d.getMinutes())}`;
}

function SchedulePostModal({
  open,
  onClose,
  onScheduled,
  ideaId,
  token,
  generatedContentId,
}) {
  const [localDt, setLocalDt] = useState(defaultDatetimeLocalValue);
  const [title, setTitle] = useState("");
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      setLocalDt(defaultDatetimeLocalValue());
      setTitle("");
    }
  }, [open]);

  if (!open) return null;

  async function handleSubmit() {
    if (!ideaId || !token || !generatedContentId) return;
    const t = (localDt || "").trim();
    if (!t) {
      toast.warning("Choisissez une date et une heure.");
      return;
    }
    const instant = new Date(t);
    if (Number.isNaN(instant.getTime())) {
      toast.warning("Date ou heure invalide.");
      return;
    }
    setSubmitting(true);
    try {
      await apiCreateScheduledPublication(ideaId, token, {
        generated_content_id: generatedContentId,
        scheduled_at: instant.toISOString(),
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        title: title.trim() || undefined,
      });
      toast.success("Publication ajoutée au calendrier.");
      onScheduled?.();
      onClose();
    } catch (e) {
      toast.error(e?.message || "Impossible de planifier.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-[130] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
      role="dialog"
      aria-modal="true"
      aria-labelledby="schedule-modal-title"
    >
      <div className="w-full max-w-md overflow-hidden rounded-2xl border border-brand-border bg-white shadow-2xl">
        <div className="flex items-center justify-between border-b border-brand-border bg-gradient-to-r from-brand-light/50 to-white px-4 py-3">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-light">
              <FiCalendar className="h-4 w-4 text-brand" />
            </span>
            <div>
              <h3 id="schedule-modal-title" className="text-sm font-bold text-brand-dark">
                Planifier la publication
              </h3>
              <p className="text-2xs text-ink-muted">
                Date et heure d’envoi souhaitées (fuseau local du navigateur).
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full border border-brand-border bg-white text-ink-muted transition-colors hover:bg-brand-light hover:text-brand-dark"
            aria-label="Fermer"
          >
            <FiX className="h-4 w-4" />
          </button>
        </div>
        <div className="space-y-3 px-4 py-3">
          <div>
            <label className="mb-1 block text-2xs font-semibold uppercase tracking-wider text-ink-muted">
              Date et heure
            </label>
            <input
              type="datetime-local"
              value={localDt}
              onChange={(e) => setLocalDt(e.target.value)}
              className="w-full rounded-lg border border-brand-border bg-white px-3 py-2 text-sm text-ink outline-none focus:border-brand focus:ring-2 focus:ring-brand/10"
            />
          </div>
          <div>
            <label className="mb-1 block text-2xs font-semibold uppercase tracking-wider text-ink-muted">
              Titre (optionnel)
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Ex. Lancement printemps"
              className="w-full rounded-lg border border-brand-border bg-white px-3 py-2 text-sm text-ink outline-none focus:border-brand focus:ring-2 focus:ring-brand/10"
            />
          </div>
        </div>
        <div className="flex items-center justify-end gap-2 border-t border-brand-border bg-brand-light/20 px-4 py-3">
          <Button type="button" variant="ghost" size="sm" onClick={onClose}>
            Annuler
          </Button>
          <Button type="button" variant="secondary" size="sm" onClick={handleSubmit} disabled={submitting}>
            <FiCalendar className="h-3.5 w-3.5" />
            {submitting ? "Enregistrement…" : "Ajouter au calendrier"}
          </Button>
        </div>
      </div>
    </div>
  );
}

/* ── Edit caption zone ───────────────────────────────────────────────── */
function EditCaptionZone({ value, onChange, onCancel, onSave }) {
  return (
    <div className="rounded-xl border border-brand/30 bg-brand-light/20 p-3">
      <div className="mb-2 flex items-center justify-between">
        <p className="text-2xs font-bold uppercase tracking-wider text-brand">
          Mode édition
        </p>
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-brand" />
      </div>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={6}
        className="w-full resize-y rounded-lg border border-brand-border bg-white px-3 py-2 text-sm text-ink outline-none transition focus:border-brand focus:ring-2 focus:ring-brand/10"
      />
      <div className="mt-2 flex items-center justify-end gap-2">
        <Button type="button" variant="ghost" size="sm" onClick={onCancel}>
          Annuler
        </Button>
        <Button type="button" variant="secondary" size="sm" onClick={onSave}>
          <FiCheckCircle className="h-3.5 w-3.5" />
          Enregistrer
        </Button>
      </div>
    </div>
  );
}

/* ── Main workspace ─────────────────────────────────────────────────── */
export function ContentWorkspace({
  ideaId,
  token,
  activePlatform,
  forms,
  updateForm,
  generated,
  isGenerating,
  onGenerate,
  onRegenerate,
  onOpenPublishModal,
  canPublish,
  publishLoading,
  regenerationInstruction,
  onRegenerationInstructionChange,
  isEditing,
  draftCaption,
  onDraftCaptionChange,
  onStartEditing,
  onCancelEditing,
  onSaveEditing,
  onScheduleCreated,
}) {
  const formValues = forms[activePlatform];
  const hasGenerated = !!(generated?.caption || generated?.imageUrl);
  const [regenOpen, setRegenOpen] = useState(false);
  const [scheduleOpen, setScheduleOpen] = useState(false);

  function handleOpenRegenerateModal() {
    setRegenOpen(true);
  }

  async function handleConfirmRegenerate() {
    await onRegenerate();
    setRegenOpen(false);
  }

  const canSchedule = Boolean(ideaId && token && generated?.dbId);

  return (
    <div className="grid gap-4 lg:grid-cols-2 lg:gap-5">

      {/* ── Left column : brief + generate ──────────────────────── */}
      <Card padding="p-0" className="shadow-card flex flex-col overflow-hidden">

        {/* Card header */}
        <div className="flex items-center justify-between border-b border-brand-border bg-gradient-to-r from-brand-light/40 to-white px-5 py-3.5">
          <SectionHeader
            icon={FiFileText}
            title="Brief de contenu"
            subtitle="Décrivez ce que vous voulez publier"
            step="1"
          />
        </div>

        {/* Form body */}
        <div className="flex flex-1 flex-col gap-0 overflow-visible">
          <div className="px-5 py-4">
            <ContentForm
              platform={activePlatform}
              values={formValues}
              onChange={updateForm}
            />
          </div>

          {/* Divider */}
          <div className="mx-5 h-px bg-brand-border" />

          {/* Generate CTA */}
          <div className="px-5 py-4">
            <button
              type="button"
              disabled={isGenerating}
              onClick={onGenerate}
              className={[
                "relative flex w-full items-center justify-center gap-2 overflow-hidden",
                "rounded-xl px-5 py-3 text-sm font-bold text-white shadow-sm",
                "transition-all duration-200",
                isGenerating
                  ? "cursor-not-allowed bg-brand/60"
                  : "bg-brand hover:bg-brand-dark active:scale-[0.98]",
              ].join(" ")}
            >
              <FiZap className={`h-4 w-4 shrink-0 ${isGenerating ? "animate-pulse" : ""}`} />
              {isGenerating ? "Génération en cours…" : "Générer le contenu"}
              {!isGenerating && (
                <span
                  aria-hidden
                  className="pointer-events-none absolute inset-0 rounded-xl opacity-0 transition-opacity duration-300 hover:opacity-100"
                  style={{ background: "linear-gradient(105deg,transparent 40%,rgba(255,255,255,.15) 50%,transparent 60%)" }}
                />
              )}
            </button>
          </div>

          {/* Post-generation actions */}
          {hasGenerated && (
            <div className="border-t border-brand-border bg-brand-light/10 px-5 py-4 flex flex-col gap-3">
              <p className="text-2xs font-bold uppercase tracking-wider text-ink-muted">
                Actions post-génération
              </p>

              {/* Toolbar row */}
              <div className="flex flex-wrap gap-2">
                <ActionChip
                  icon={FiEdit3}
                  label="Modifier"
                  onClick={onStartEditing}
                  disabled={isGenerating || publishLoading}
                  active={isEditing}
                />
                <ActionChip
                  icon={FiRefreshCw}
                  label="Régénérer"
                  onClick={handleOpenRegenerateModal}
                  disabled={isGenerating || publishLoading}
                />
                <ActionChip
                  icon={FiCalendar}
                  label="Planifier"
                  onClick={() => {
                    if (!canSchedule) {
                      toast.warning("Enregistrez d’abord le post (génération avec historique) pour planifier.");
                      return;
                    }
                    setScheduleOpen(true);
                  }}
                  disabled={isGenerating || publishLoading}
                />
                <ActionChip
                  icon={FiSend}
                  label={publishLoading ? "Publication…" : "Publier"}
                  onClick={onOpenPublishModal}
                  disabled={!canPublish || publishLoading}
                  variant="publish"
                />
              </div>

              <p className="text-2xs text-ink-muted">
                {regenerationInstruction?.trim()
                  ? `Consigne active : "${regenerationInstruction.trim()}"`
                  : "Aucune consigne active. Cliquez sur Régénérer pour en ajouter une."
                }
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* ── Right column : preview ───────────────────────────────── */}
      <Card padding="p-0" className="shadow-card flex flex-col overflow-hidden">

        {/* Card header */}
        <div className="flex items-center justify-between border-b border-brand-border bg-gradient-to-r from-brand-light/40 to-white px-5 py-3.5">
          <SectionHeader
            icon={FiEye}
            title={`Aperçu — ${PLATFORM_LABELS[activePlatform] || activePlatform}`}
            subtitle="Rendu simulé sur la plateforme choisie"
            step="2"
          />
          {hasGenerated && !publishLoading && (
            <span className="inline-flex items-center gap-1 rounded-full bg-success/10 px-2.5 py-1 text-2xs font-semibold text-success">
              <FiCheckCircle className="h-3 w-3" />
              Prêt
            </span>
          )}
        </div>

        {/* Preview body */}
        <div className="flex flex-1 flex-col gap-4 px-5 py-4">
          <PostPreviewPanel
            platform={generated?.platform || activePlatform}
            caption={isEditing ? draftCaption : generated?.caption}
            imageUrl={generated?.imageUrl}
            emptyHint="Générez d'abord votre contenu"
          />

          {/* Edit zone — inside preview panel */}
          {hasGenerated && isEditing && (
            <EditCaptionZone
              value={draftCaption}
              onChange={onDraftCaptionChange}
              onCancel={onCancelEditing}
              onSave={onSaveEditing}
            />
          )}
        </div>
      </Card>

      <RegenerationModal
        open={regenOpen}
        value={regenerationInstruction}
        onChange={onRegenerationInstructionChange}
        onClose={() => setRegenOpen(false)}
        onConfirm={handleConfirmRegenerate}
        loading={isGenerating}
      />

      <SchedulePostModal
        open={scheduleOpen}
        onClose={() => setScheduleOpen(false)}
        onScheduled={onScheduleCreated}
        ideaId={ideaId}
        token={token}
        generatedContentId={generated?.dbId}
      />

    </div>
  );
}

export default ContentWorkspace;
