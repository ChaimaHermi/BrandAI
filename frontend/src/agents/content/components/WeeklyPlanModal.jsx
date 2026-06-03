import { useMemo, useState, useCallback } from "react";
import {
  FiAlertCircle,
  FiCalendar,
  FiCheck,
  FiCheckCircle,
  FiClock,
  FiEdit3,
  FiImage,
  FiLoader,
  FiPlus,
  FiRefreshCw,
  FiSend,
  FiTrash2,
  FiX,
} from "react-icons/fi";
import { toast } from "react-toastify";
import { Button } from "@/shared/ui/Button";
import {
  apiApproveWeeklyPlan,
  apiGenerateWeeklyPlan,
  apiGenerateWeeklyPlanContent,
  apiRegenerateWeeklyItem,
  apiRetryWeeklyVariantImage,
} from "../api/weeklyPlan.api";

const PLATFORMS = {
  linkedin: { label: "LinkedIn", color: "#0a66c2" },
  facebook: { label: "Facebook", color: "#1877f2" },
  instagram: { label: "Instagram", color: "#e1306c" },
};

/** Construit une date ISO à partir de scheduled_date + HH:MM (fuseau local navigateur). */
function localSlotFromPlan(item, platform, refVariant) {
  const times = item?.platform_times || {};
  const dateStr = item?.scheduled_date;
  const hhmm = times[platform] || times[refVariant?.platform];
  if (dateStr && hhmm && /^\d{1,2}:\d{2}$/.test(String(hhmm))) {
    const [h, m] = String(hhmm).split(":").map(Number);
    const d = new Date(`${dateStr}T00:00:00`);
    if (!Number.isNaN(d.getTime())) {
      d.setHours(h, m || 0, 0, 0);
      if (d.getTime() > Date.now()) return d.toISOString();
    }
  }
  if (refVariant?.scheduled_at_utc) return refVariant.scheduled_at_utc;
  const d = new Date();
  d.setMinutes(d.getMinutes() + 90);
  d.setSeconds(0, 0);
  return d.toISOString();
}

function toLocalDatetimeInputValue(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${y}-${m}-${day}T${hh}:${mm}`;
}

function formatDateShort(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleDateString("fr-FR", { weekday: "short", day: "numeric", month: "short" });
}

function formatTime(iso) {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });
}

function ProgressModal({ open, title, items, currentIndex }) {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-2xl border border-brand-border bg-white p-6 shadow-2xl">
        <div className="mb-4 flex items-center gap-3">
          <FiLoader className="h-6 w-6 animate-spin text-brand" />
          <h3 className="text-lg font-bold text-ink">{title}</h3>
        </div>
        <div className="space-y-2">
          {items.map((item, idx) => (
            <div
              key={item.id}
              className={`flex items-center gap-3 rounded-xl border px-3 py-2 ${
                idx < currentIndex
                  ? "border-emerald-200 bg-emerald-50"
                  : idx === currentIndex
                    ? "border-brand bg-brand/5"
                    : "border-brand-border bg-white"
              }`}
            >
              {idx < currentIndex ? (
                <FiCheckCircle className="h-5 w-5 text-emerald-600" />
              ) : idx === currentIndex ? (
                <FiLoader className="h-5 w-5 animate-spin text-brand" />
              ) : (
                <FiClock className="h-5 w-5 text-ink-muted" />
              )}
              <span className="flex-1 text-sm font-medium text-ink">{item.label}</span>
              <span className="text-xs text-ink-muted">
                {idx < currentIndex ? "Terminé" : idx === currentIndex ? "En cours..." : "En attente"}
              </span>
            </div>
          ))}
        </div>
        <p className="mt-4 text-center text-xs text-ink-muted">
          {currentIndex + 1} / {items.length} — Ne fermez pas cette fenêtre
        </p>
      </div>
    </div>
  );
}

function FeedbackModal({ open, onClose, onSubmit, platform }) {
  const [feedback, setFeedback] = useState("");
  const [loading, setLoading] = useState(false);

  if (!open) return null;

  async function handleSubmit() {
    if (!feedback.trim()) return toast.warning("Entrez un feedback.");
    setLoading(true);
    try {
      await onSubmit(feedback.trim());
      setFeedback("");
      onClose();
    } catch (e) {
      toast.error(e?.message || "Régénération impossible.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/60 backdrop-blur-sm" onClick={(e) => e.target === e.currentTarget && onClose()}>
      <div className="w-full max-w-lg rounded-2xl border border-brand-border bg-white p-5 shadow-2xl">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="text-lg font-bold text-ink">
            <FiRefreshCw className="mr-2 inline h-5 w-5 text-brand" />
            Régénérer pour {platform}
          </h3>
          <button type="button" onClick={onClose} className="rounded-full p-1 hover:bg-brand-light">
            <FiX className="h-5 w-5 text-ink-muted" />
          </button>
        </div>
        <p className="mb-3 text-sm text-ink-muted">Décrivez comment améliorer ce post :</p>
        <textarea
          rows={4}
          value={feedback}
          onChange={(e) => setFeedback(e.target.value)}
          placeholder="Ex: Rends le plus engageant, ajoute un appel à l'action, raccourcis le texte..."
          className="mb-4 w-full resize-none rounded-xl border border-brand-border px-3 py-2 text-sm focus:border-brand focus:outline-none"
          autoFocus
        />
        <div className="flex justify-end gap-2">
          <Button type="button" variant="ghost" size="sm" onClick={onClose} disabled={loading}>
            Annuler
          </Button>
          <Button type="button" variant="secondary" size="sm" onClick={handleSubmit} disabled={loading || !feedback.trim()}>
            {loading ? <FiLoader className="h-4 w-4 animate-spin" /> : <FiRefreshCw className="h-4 w-4" />}
            {loading ? "Régénération..." : "Régénérer"}
          </Button>
        </div>
      </div>
    </div>
  );
}

function PlatformBadge({ platform, active, onClick }) {
  const p = PLATFORMS[platform] || {};
  return (
    <button
      type="button"
      onClick={onClick}
      className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-semibold transition ${
        active
          ? "border-transparent text-white shadow"
          : "border-brand-border bg-white text-ink-muted hover:border-brand hover:text-brand-dark"
      }`}
      style={active ? { backgroundColor: p.color || "#6366f1" } : {}}
    >
      {active ? <FiCheck className="h-3 w-3" /> : <FiPlus className="h-3 w-3" />}
      {p.label || platform}
    </button>
  );
}

function PlanningCard({ item, index, onPatch, onTogglePlatform, onRemove }) {
  const activeVariants = (item.variants || []).filter((v) => v.status !== "removed_by_user");
  const detectedDate = item.scheduled_date || item.date_hint || item.day_hint;
  const rationale = item.platform_rationale || {};

  return (
    <div className="overflow-hidden rounded-2xl border border-brand-border bg-white shadow-sm">
      <div className="flex items-center gap-3 border-b border-brand-border bg-gradient-to-r from-brand-light/40 to-white px-4 py-3">
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-brand text-sm font-bold text-white">
          {index + 1}
        </span>
        <input
          className="flex-1 bg-transparent text-sm font-semibold text-ink placeholder:text-ink-muted focus:outline-none"
          value={item.objective || ""}
          onChange={(e) => onPatch({ objective: e.target.value })}
          placeholder="Objectif du post..."
        />
        <button type="button" onClick={onRemove} className="rounded-full p-1.5 text-ink-muted hover:bg-red-50 hover:text-red-600">
          <FiTrash2 className="h-4 w-4" />
        </button>
      </div>

      <div className="p-4">
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="text-xs font-semibold uppercase text-ink-muted">Plateformes :</span>
          {Object.keys(PLATFORMS).map((p) => {
            const v = (item.variants || []).find((x) => x.platform === p);
            const active = !!v && v.status !== "removed_by_user";
            return <PlatformBadge key={p} platform={p} active={active} onClick={() => onTogglePlatform(p)} />;
          })}
        </div>

        {detectedDate && (
          <div className="mb-3 inline-flex items-center gap-1.5 rounded-full bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
            <FiCalendar className="h-3.5 w-3.5" />
            {item.user_time_specified ? "Créneau demandé" : "Date proposée"} :{" "}
            <span className="font-bold">{detectedDate}</span>
          </div>
        )}

        {item.content_type && (
          <p className="mb-2 text-xs text-ink-muted">
            Type : <span className="font-semibold text-ink">{item.content_type}</span>
          </p>
        )}

        {Object.keys(rationale).length > 0 && (
          <ul className="mb-3 space-y-1 rounded-lg border border-brand-border/60 bg-brand-light/10 px-3 py-2 text-xs text-ink-muted">
            {activeVariants.map((v) =>
              rationale[v.platform] ? (
                <li key={v.variant_id}>
                  <span className="font-semibold text-ink">{PLATFORMS[v.platform]?.label || v.platform}</span>
                  {" — "}
                  {rationale[v.platform]}
                </li>
              ) : null
            )}
          </ul>
        )}

        {activeVariants.length === 0 ? (
          <p className="rounded-lg border border-dashed border-brand-border bg-brand-light/10 py-3 text-center text-xs text-ink-muted">
            Sélectionnez au moins une plateforme
          </p>
        ) : (
          <div className="space-y-2">
            {activeVariants.map((v) => {
              const pl = PLATFORMS[v.platform] || {};
              return (
                <div
                  key={v.variant_id}
                  className="flex flex-wrap items-center gap-3 rounded-xl border border-brand-border bg-brand-light/5 px-3 py-2"
                >
                  <span
                    className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-bold text-white"
                    style={{ backgroundColor: pl.color || "#6366f1" }}
                  >
                    {pl.label}
                  </span>
                  <div className="flex items-center gap-2">
                    <FiClock className="h-3.5 w-3.5 text-ink-muted" />
                    <input
                      type="datetime-local"
                      className="rounded-lg border border-brand-border bg-white px-2 py-1 text-xs focus:border-brand focus:outline-none"
                      value={toLocalDatetimeInputValue(v.scheduled_at_utc)}
                      onChange={(e) => {
                        const d = new Date(e.target.value);
                        if (!Number.isNaN(d.getTime())) {
                          onPatch({
                            variants: (item.variants || []).map((x) =>
                              x.variant_id === v.variant_id
                                ? { ...x, scheduled_at_utc: d.toISOString(), timing_source: "user_defined" }
                                : x
                            ),
                          });
                        }
                      }}
                    />
                  </div>
                  {v.platform === "instagram" ? (
                    <span
                      className="inline-flex items-center gap-1 rounded-lg border border-brand-border bg-brand-light/10 px-2 py-1 text-xs font-medium text-ink"
                      title="Instagram nécessite toujours une image"
                    >
                      <FiImage className="h-3 w-3" />
                      Avec image
                    </span>
                  ) : (
                    <select
                      className="rounded-lg border border-brand-border bg-white px-2 py-1 text-xs"
                      value={v.image_mode || "required"}
                      onChange={(e) =>
                        onPatch({
                          variants: (item.variants || []).map((x) =>
                            x.variant_id === v.variant_id ? { ...x, image_mode: e.target.value } : x
                          ),
                        })
                      }
                    >
                      <option value="required">Avec image</option>
                      <option value="none">Sans image</option>
                    </select>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function ContentCard({
  item,
  index,
  onPatchVariant,
  onRegenerate,
  onRetryImage,
  retryingVariantId,
  onToggleRemoved,
}) {
  const activeVariants = (item.variants || []).filter((v) => v.status !== "removed_by_user");

  return (
    <div className="overflow-hidden rounded-2xl border border-brand-border bg-white shadow-sm">
      <div className="flex items-center gap-3 border-b border-brand-border bg-gradient-to-r from-emerald-50 to-white px-4 py-3">
        <span className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-600 text-sm font-bold text-white">
          {index + 1}
        </span>
        <span className="flex-1 text-sm font-semibold text-ink">{item.objective}</span>
        <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 text-xs font-bold text-emerald-700">
          {activeVariants.filter((v) => v.content_generated).length}/{activeVariants.length} générés
        </span>
      </div>

      <div className="divide-y divide-brand-border">
        {activeVariants.map((v) => {
          const pl = PLATFORMS[v.platform] || {};
          return (
            <div key={v.variant_id} className="p-4">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <span
                  className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-bold text-white"
                  style={{ backgroundColor: pl.color || "#6366f1" }}
                >
                  {pl.label}
                </span>
                <span className="inline-flex items-center gap-1 text-xs text-ink-muted">
                  <FiCalendar className="h-3.5 w-3.5" />
                  {formatDateShort(v.scheduled_at_utc)}
                </span>
                <span className="inline-flex items-center gap-1 text-xs text-ink-muted">
                  <FiClock className="h-3.5 w-3.5" />
                  {formatTime(v.scheduled_at_utc)}
                </span>
                {v.content_generated ? (
                  <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[10px] font-bold text-emerald-700">
                    <FiCheckCircle className="h-3 w-3" />
                    Prêt
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 rounded-full bg-amber-100 px-2 py-0.5 text-[10px] font-bold text-amber-700">
                    <FiAlertCircle className="h-3 w-3" />
                    En attente
                  </span>
                )}
                <div className="ml-auto flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => onToggleRemoved(v.variant_id)}
                    className="rounded-full p-1.5 text-ink-muted hover:bg-red-50 hover:text-red-600"
                    title="Retirer"
                  >
                    <FiTrash2 className="h-4 w-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => onRegenerate(v)}
                    disabled={!v.content_generated}
                    className="rounded-full p-1.5 text-ink-muted hover:bg-brand-light hover:text-brand disabled:opacity-40"
                    title={
                      v.image_mode !== "none" || v.platform === "instagram"
                        ? "Régénérer texte et image"
                        : "Régénérer le texte"
                    }
                  >
                    <FiRefreshCw className="h-4 w-4" />
                  </button>
                </div>
              </div>

              {v.content_generated ? (
                <div className="grid gap-3 md:grid-cols-[1fr_180px]">
                  <div>
                    <label className="mb-1 flex items-center gap-1 text-[10px] font-bold uppercase text-ink-muted">
                      <FiEdit3 className="h-3 w-3" />
                      Caption
                    </label>
                    <textarea
                      rows={5}
                      className="w-full resize-y rounded-lg border border-brand-border px-3 py-2 text-sm focus:border-brand focus:outline-none"
                      value={v.caption || ""}
                      onChange={(e) => onPatchVariant(v.variant_id, { caption: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="mb-1 flex items-center gap-1 text-[10px] font-bold uppercase text-ink-muted">
                      <FiImage className="h-3 w-3" />
                      Image
                    </label>
                    {v.image_url ? (
                      <img
                        src={v.image_url}
                        alt=""
                        className="h-32 w-full rounded-lg border border-brand-border object-cover"
                      />
                    ) : v.image_error ? (
                      <div className="flex h-32 flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-red-300 bg-red-50 px-2 text-center text-[10px] text-red-600">
                        <p className="line-clamp-3">{v.image_error}</p>
                        <button
                          type="button"
                          disabled={retryingVariantId === v.variant_id}
                          onClick={() => onRetryImage?.(v)}
                          className="inline-flex items-center gap-1 rounded-full bg-white px-2.5 py-1 text-[10px] font-bold text-brand shadow-sm hover:bg-brand-light disabled:opacity-50"
                        >
                          {retryingVariantId === v.variant_id ? (
                            <FiLoader className="h-3 w-3 animate-spin" />
                          ) : (
                            <FiRefreshCw className="h-3 w-3" />
                          )}
                          Réessayer l&apos;image
                        </button>
                      </div>
                    ) : (
                      <div className="flex h-32 items-center justify-center rounded-lg border border-dashed border-brand-border bg-brand-light/10 text-center text-[10px] text-ink-muted">
                        {v.image_mode === "none" ? "Sans image" : "En attente"}
                      </div>
                    )}
                  </div>
                </div>
              ) : (
                <div className="rounded-lg border border-dashed border-brand-border bg-brand-light/5 py-4 text-center text-xs text-ink-muted">
                  Le contenu sera généré après approbation des recommandations
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function WeeklyPlanModal({ open, onClose, ideaId, token, onApproved }) {
  const [prompt, setPrompt] = useState("");
  const [loading, setLoading] = useState(false);
  const [plan, setPlan] = useState(null);
  const [stage, setStage] = useState("planning");

  const [progressOpen, setProgressOpen] = useState(false);
  const [progressTitle, setProgressTitle] = useState("");
  const [progressItems, setProgressItems] = useState([]);
  const [progressIndex, setProgressIndex] = useState(0);

  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [feedbackVariant, setFeedbackVariant] = useState(null);
  const [retryingVariantId, setRetryingVariantId] = useState(null);

  const timezone = useMemo(() => Intl.DateTimeFormat().resolvedOptions().timeZone || "UTC", []);

  const activeVariantsCount = useMemo(
    () => (plan?.items || []).reduce((a, i) => a + (i.variants || []).filter((v) => v.status !== "removed_by_user").length, 0),
    [plan]
  );
  const generatedCount = useMemo(
    () =>
      (plan?.items || []).reduce(
        (a, i) => a + (i.variants || []).filter((v) => v.status !== "removed_by_user" && v.content_generated).length,
        0
      ),
    [plan]
  );

  const buildVariant = useCallback((itemIndex, platform, refVariant, item) => {
    const scheduled = localSlotFromPlan(item, platform, refVariant);
    const wantImage =
      platform === "instagram" ||
      Boolean((item?.platform_images || {})[platform]);
    return {
      variant_id: `wp-${itemIndex + 1}-${platform}-${Date.now()}`,
      platform,
      caption: "",
      scheduled_at_utc: scheduled,
      timing_source: "user_added",
      status: "added_by_user",
      image_mode: wantImage ? "required" : "none",
      image_status: wantImage ? "pending" : "skipped",
      image_url: null,
      image_error: null,
      content_generated: false,
    };
  }, []);

  if (!open) return null;

  async function handleGenerate() {
    if (!ideaId || !token) return toast.warning("Chargez un projet avant de planifier.");
    if (!(prompt || "").trim()) return toast.warning("Décrivez ce que vous voulez publier.");
    setLoading(true);
    try {
      const out = await apiGenerateWeeklyPlan(token, {
        idea_id: ideaId,
        user_prompt: prompt.trim(),
        timezone,
        platforms: ["linkedin", "facebook", "instagram"],
        align_with_project: true,
        include_images: true,
        distribution_mode: "auto",
        requested_post_count: null,
        access_token: token,
      });
      setPlan(out);
      setStage("planning");
      toast.success("Plan généré ! Ajustez puis approuvez.");
    } catch (e) {
      toast.error(e?.message || "Génération impossible.");
    } finally {
      setLoading(false);
    }
  }

  function patchItem(itemId, patch) {
    setPlan((prev) =>
      prev ? { ...prev, items: prev.items.map((it) => (it.item_id === itemId ? { ...it, ...patch } : it)) } : prev
    );
  }

  function togglePlatform(itemId, platform) {
    setPlan((prev) => {
      if (!prev) return prev;
      const idx = prev.items.findIndex((it) => it.item_id === itemId);
      if (idx < 0) return prev;
      return {
        ...prev,
        items: prev.items.map((it) => {
          if (it.item_id !== itemId) return it;
          const existing = (it.variants || []).find((v) => v.platform === platform);
          if (existing) {
            return {
              ...it,
              variants: it.variants.map((v) =>
                v.variant_id === existing.variant_id
                  ? { ...v, status: v.status === "removed_by_user" ? "added_by_user" : "removed_by_user" }
                  : v
              ),
            };
          }
          const ref = (it.variants || []).find((v) => v.status !== "removed_by_user");
          return { ...it, variants: [...(it.variants || []), buildVariant(idx, platform, ref, it)] };
        }),
      };
    });
  }

  function removeItem(itemId) {
    setPlan((prev) => (prev ? { ...prev, items: prev.items.filter((it) => it.item_id !== itemId) } : prev));
  }

  function addIntent() {
    setPlan((prev) => {
      const base = prev || { items: [], notes: [], timezone };
      const idx = base.items.length;
      return {
        ...base,
        items: [
          ...base.items,
          {
            item_id: `wp-new-${Date.now()}`,
            objective: "",
            recommended_platforms: [],
            platform_rationale: {},
            content_type: "other",
            status: "added_by_user",
            scheduled_date: null,
            date_hint: null,
            day_hint: null,
            variants: [],
          },
        ],
      };
    });
  }

  function patchVariant(itemId, variantId, patch) {
    setPlan((prev) =>
      prev
        ? {
            ...prev,
            items: prev.items.map((it) =>
              it.item_id !== itemId
                ? it
                : { ...it, variants: (it.variants || []).map((v) => (v.variant_id === variantId ? { ...v, ...patch } : v)) }
            ),
          }
        : prev
    );
  }

  function toggleVariantRemoved(itemId, variantId) {
    setPlan((prev) =>
      prev
        ? {
            ...prev,
            items: prev.items.map((it) =>
              it.item_id !== itemId
                ? it
                : {
                    ...it,
                    variants: (it.variants || []).map((v) =>
                      v.variant_id !== variantId
                        ? v
                        : { ...v, status: v.status === "removed_by_user" ? "added_by_user" : "removed_by_user" }
                    ),
                  }
            ),
          }
        : prev
    );
  }

  async function handleApproveRecommendations() {
    if (!plan?.items?.length) return toast.warning("Générez un plan d'abord.");
    if (!activeVariantsCount) return toast.warning("Sélectionnez au moins une plateforme.");
    const missing = plan.items.find((it) => !(it.objective || "").trim());
    if (missing) return toast.warning("Renseignez un objectif pour chaque post.");

    const progressList = [];
    for (const item of plan.items) {
      for (const v of item.variants || []) {
        if (v.status !== "removed_by_user") {
          progressList.push({
            id: v.variant_id,
            label: `${item.objective?.slice(0, 30) || "Post"}... — ${PLATFORMS[v.platform]?.label || v.platform}`,
          });
        }
      }
    }

    setProgressTitle("Génération du contenu en cours");
    setProgressItems(progressList);
    setProgressIndex(0);
    setProgressOpen(true);

    try {
      const out = await apiGenerateWeeklyPlanContent(token, {
        idea_id: ideaId,
        access_token: token,
        items: plan.items,
      });

      let idx = 0;
      for (const item of out.items || []) {
        for (const v of item.variants || []) {
          if (v.status !== "removed_by_user") {
            idx++;
            setProgressIndex(idx);
            await new Promise((r) => setTimeout(r, 150));
          }
        }
      }

      setPlan((prev) => ({ ...(prev || {}), items: out.items || [] }));
      setStage("content_ready");
      toast.success("Contenu généré ! Vérifiez puis validez.");
    } catch (e) {
      toast.error(e?.message || "Génération impossible.");
    } finally {
      setProgressOpen(false);
    }
  }

  async function handleFinalApprove() {
    if (!plan?.items?.length) return toast.warning("Générez un plan d'abord.");
    if (!generatedCount) return toast.warning("Générez le contenu d'abord.");

    const progressList = [];
    for (const item of plan.items) {
      for (const v of item.variants || []) {
        if (v.status !== "removed_by_user" && v.content_generated) {
          progressList.push({
            id: v.variant_id,
            label: `${item.objective?.slice(0, 30) || "Post"}... — ${PLATFORMS[v.platform]?.label || v.platform}`,
          });
        }
      }
    }

    setProgressTitle("Ajout au calendrier");
    setProgressItems(progressList);
    setProgressIndex(0);
    setProgressOpen(true);

    try {
      await apiApproveWeeklyPlan(token, {
        idea_id: ideaId,
        access_token: token,
        timezone,
        items: plan.items,
      });

      for (let i = 0; i <= progressList.length; i++) {
        setProgressIndex(i);
        await new Promise((r) => setTimeout(r, 100));
      }

      toast.success("Plan ajouté au calendrier !");
      onApproved?.();
      onClose?.();
    } catch (e) {
      toast.error(e?.message || "Approbation impossible.");
    } finally {
      setProgressOpen(false);
    }
  }

  function openRegenerate(variant) {
    setFeedbackVariant(variant);
    setFeedbackOpen(true);
  }

  async function handleRetryImage(variant) {
    if (!variant || !ideaId) return;
    const parentItem = plan?.items?.find((it) =>
      (it.variants || []).some((v) => v.variant_id === variant.variant_id),
    );
    setRetryingVariantId(variant.variant_id);
    setLoading(true);
    try {
      const out = await apiRetryWeeklyVariantImage(token, {
        variant,
        objective: parentItem?.objective || "",
        idea_id: ideaId,
        access_token: token,
        align_with_project: true,
      });
      const itemId = parentItem?.item_id;
      if (itemId && out?.variant) {
        patchVariant(itemId, variant.variant_id, out.variant);
      }
      if (out?.variant?.image_url) {
        toast.success("Image régénérée.");
      } else {
        toast.warning(out?.variant?.image_error || "L'image n'a pas pu être générée.");
      }
    } catch (e) {
      toast.error(e?.message || "Retry image impossible.");
    } finally {
      setRetryingVariantId(null);
      setLoading(false);
    }
  }

  async function handleRegenerate(feedback) {
    if (!feedbackVariant || !ideaId) return;
    const parentItem = plan?.items?.find((it) =>
      (it.variants || []).some((v) => v.variant_id === feedbackVariant.variant_id),
    );
    setLoading(true);
    try {
      const out = await apiRegenerateWeeklyItem(token, {
        item: {
          ...feedbackVariant,
          objective: parentItem?.objective || "",
        },
        feedback,
        idea_id: ideaId,
        access_token: token,
        align_with_project: true,
      });
      const itemId = parentItem?.item_id;
      if (itemId) {
        patchVariant(itemId, feedbackVariant.variant_id, out.item);
      }
      toast.success(
        feedbackVariant.image_mode !== "none" || feedbackVariant.platform === "instagram"
          ? "Texte et image régénérés."
          : "Texte régénéré.",
      );
    } catch (e) {
      toast.error(e?.message || "Régénération impossible.");
    } finally {
      setLoading(false);
      setFeedbackOpen(false);
    }
  }

  return (
    <>
      <ProgressModal open={progressOpen} title={progressTitle} items={progressItems} currentIndex={progressIndex} />
      <FeedbackModal
        open={feedbackOpen}
        onClose={() => setFeedbackOpen(false)}
        onSubmit={handleRegenerate}
        platform={PLATFORMS[feedbackVariant?.platform]?.label || feedbackVariant?.platform || ""}
      />

      <div
        className="fixed inset-0 z-[135] flex items-center justify-center bg-black/50 p-4 backdrop-blur-sm"
        onClick={(e) => e.target === e.currentTarget && onClose?.()}
        role="dialog"
        aria-modal="true"
      >
        <div className="flex max-h-[92vh] w-full max-w-5xl flex-col overflow-hidden rounded-3xl border border-brand-border bg-white shadow-2xl">
          <div className="flex items-center justify-between border-b border-brand-border bg-gradient-to-r from-brand-light/50 to-white px-5 py-4">
            <div>
              <h3 className="text-lg font-extrabold text-brand-dark">Plan de la semaine</h3>
              <p className="text-xs text-ink-muted">
                {stage === "planning" ? "Étape 1 : Vérifiez les recommandations" : "Étape 2 : Vérifiez le contenu généré"}
              </p>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 rounded-full border border-brand-border bg-white px-3 py-1">
                <span
                  className={`h-2 w-2 rounded-full ${stage === "planning" ? "bg-brand" : "bg-emerald-500"}`}
                />
                <span className="text-xs font-medium text-ink">
                  {stage === "planning" ? "Recommandations" : "Contenu prêt"}
                </span>
              </div>
              <button
                type="button"
                onClick={onClose}
                className="flex h-8 w-8 items-center justify-center rounded-full border border-brand-border hover:bg-brand-light"
              >
                <FiX className="h-4 w-4 text-ink-muted" />
              </button>
            </div>
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto p-4">
            <div className="mb-4 rounded-2xl border border-brand-border bg-brand-light/10 p-4">
              <label className="mb-2 block text-xs font-bold uppercase text-ink-muted">Décrivez vos posts</label>
              <textarea
                rows={5}
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Ex: Demain lancement produit, vendredi promo -20%, 1er mai témoignage client"
                className="mb-3 min-h-[120px] w-full resize-y rounded-xl border border-brand-border px-3 py-3 text-sm leading-relaxed focus:border-brand focus:outline-none"
              />
              <div className="flex flex-wrap items-center gap-3">
                <span className="text-xs text-ink-muted">Fuseau : {timezone}</span>
                <div className="ml-auto">
                  <Button type="button" variant="secondary" size="sm" onClick={handleGenerate} disabled={loading}>
                    {loading ? <FiLoader className="h-4 w-4 animate-spin" /> : <FiSend className="h-4 w-4" />}
                    {loading ? "Génération..." : plan ? "Régénérer" : "Générer"}
                  </Button>
                </div>
              </div>
            </div>

            {plan?.items?.length ? (
              <>
                {(plan.notes || []).length > 0 && (
                  <ul className="mb-3 rounded-xl border border-amber-200 bg-amber-50/80 px-3 py-2 text-xs text-amber-900">
                    {plan.notes.map((n, i) => (
                      <li key={i}>{n}</li>
                    ))}
                  </ul>
                )}

                <div className="mb-3 flex items-center gap-4">
                  <span className="text-xs font-semibold text-ink-muted">
                    {plan.items.length} post(s) · {activeVariantsCount} variante(s)
                    {plan.project_context_used ? " · contexte projet" : ""}
                    {stage === "content_ready" && ` · ${generatedCount} générée(s)`}
                  </span>
                  {stage === "planning" && (
                    <button
                      type="button"
                      onClick={addIntent}
                      className="inline-flex items-center gap-1 text-xs font-semibold text-brand hover:underline"
                    >
                      <FiPlus className="h-3.5 w-3.5" />
                      Ajouter un post
                    </button>
                  )}
                </div>

                <div className="space-y-4">
                  {plan.items.map((item, idx) =>
                    stage === "planning" ? (
                      <PlanningCard
                        key={item.item_id}
                        item={item}
                        index={idx}
                        onPatch={(patch) => patchItem(item.item_id, patch)}
                        onTogglePlatform={(p) => togglePlatform(item.item_id, p)}
                        onRemove={() => removeItem(item.item_id)}
                      />
                    ) : (
                      <ContentCard
                        key={item.item_id}
                        item={item}
                        index={idx}
                        onPatchVariant={(vid, patch) => patchVariant(item.item_id, vid, patch)}
                        onRegenerate={(v) => openRegenerate(v)}
                        onRetryImage={(v) => handleRetryImage(v)}
                        retryingVariantId={retryingVariantId}
                        onToggleRemoved={(vid) => toggleVariantRemoved(item.item_id, vid)}
                      />
                    )
                  )}
                </div>
              </>
            ) : (
              <div className="flex h-40 items-center justify-center rounded-2xl border border-dashed border-brand-border bg-white text-sm text-ink-muted">
                Décrivez vos posts puis cliquez sur Générer
              </div>
            )}
          </div>

          <div className="flex items-center justify-between border-t border-brand-border bg-white px-5 py-3">
            <p className="text-xs text-ink-muted">
              {stage === "planning"
                ? "Ajustez les plateformes et horaires, puis approuvez pour générer le contenu."
                : "Vérifiez/modifiez les captions, puis validez pour ajouter au calendrier."}
            </p>
            <div className="flex items-center gap-2">
              <Button type="button" variant="ghost" size="sm" onClick={onClose}>
                Fermer
              </Button>
              {stage === "planning" ? (
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  onClick={handleApproveRecommendations}
                  disabled={!activeVariantsCount}
                >
                  <FiCheck className="h-4 w-4" />
                  Approuver et générer contenu
                </Button>
              ) : (
                <>
                  <Button type="button" variant="ghost" size="sm" onClick={() => setStage("planning")}>
                    ← Retour
                  </Button>
                  <Button
                    type="button"
                    variant="secondary"
                    size="sm"
                    onClick={handleFinalApprove}
                    disabled={!generatedCount}
                  >
                    <FiCalendar className="h-4 w-4" />
                    Ajouter au calendrier
                  </Button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
