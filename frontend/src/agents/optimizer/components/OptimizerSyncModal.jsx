import { createPortal } from "react-dom";
import {
  FiCheckCircle,
  FiXCircle,
  FiLoader,
  FiAlertTriangle,
  FiZap,
} from "react-icons/fi";

const PLATFORM_META = {
  facebook: { label: "Facebook", color: "#1877F2", bg: "#EBF3FF", short: "FB" },
  instagram: {
    label: "Instagram",
    color: "#E4405F",
    bg: "#FEF0F3",
    short: "IG",
  },
  linkedin: { label: "LinkedIn", color: "#0A66C2", bg: "#EAF3FB", short: "LN" },
};

function getPlatformMeta(raw) {
  const key = (raw || "")
    .toLowerCase()
    .replace("_business", "")
    .replace("_page", "");
  return (
    PLATFORM_META[key] || {
      label: raw || "?",
      color: "#854F0B",
      bg: "#FAEEDA",
      short: "??",
    }
  );
}

function PlatformChip({ platform }) {
  const meta = getPlatformMeta(platform);
  return (
    <span
      className="inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-bold"
      style={{ background: meta.bg, color: meta.color }}
    >
      {meta.label}
    </span>
  );
}

function EventRow({ ev, completeHasFailure }) {
  const isError = ev.type === "fatal" || ev.type === "platform_error";
  const isDone = ev.type === "platform_done";
  const isComplete = ev.type === "complete";
  const isStart = ev.type === "platform_start" || ev.type === "started";

  let icon, iconColor;
  if (isError || (isComplete && completeHasFailure)) {
    icon = <FiXCircle size={13} />;
    iconColor = "#DC2626";
  } else if (isDone || (isComplete && !completeHasFailure)) {
    icon = <FiCheckCircle size={13} />;
    iconColor = "#16A34A";
  } else if (isStart) {
    icon = <FiLoader size={13} className="animate-spin" />;
    iconColor = "#854F0B";
  } else {
    icon = <FiAlertTriangle size={13} />;
    iconColor = "#D97706";
  }

  return (
    <div
      className={`flex items-start gap-2.5 rounded-xl px-3 py-2.5 transition-all ${
        isError
          ? "bg-red-50"
          : isDone || (isComplete && !completeHasFailure)
            ? "bg-green-50"
            : isStart
              ? "bg-orange-50/60"
              : "bg-gray-50"
      }`}
    >
      <span className="mt-[1px] shrink-0" style={{ color: iconColor }}>
        {icon}
      </span>
      <div className="flex min-w-0 flex-1 flex-wrap items-center gap-1.5">
        {ev.platform && <PlatformChip platform={ev.platform} />}
        <p className="break-words text-xs text-ink leading-relaxed">
          {rowLabel(ev, completeHasFailure)}
        </p>
        {isDone && ev.posts_count != null && (
          <span className="ml-auto shrink-0 rounded-full bg-green-100 px-2 py-0.5 text-[10px] font-bold text-green-700">
            {ev.posts_count} post{ev.posts_count > 1 ? "s" : ""}
          </span>
        )}
      </div>
    </div>
  );
}

function rowLabel(ev, completeHasFailure) {
  switch (ev.type) {
    case "started":
      return `Lancement de la collecte — ${ev.platforms_total ?? "?"} plateforme(s) détectée(s)`;
    case "platform_start":
      return "Collecte des publications et métriques en cours…";
    case "platform_done":
      return "Collecte terminée, calcul des indicateurs…";
    case "platform_error":
      return ev.error ? `Échec : ${ev.error}` : "Échec de la collecte";
    case "complete":
      if (completeHasFailure)
        return `${ev.platforms_done ?? "?"}/${ev.platforms_total ?? "?"} plateformes collectées avec succès`;
      return "Toutes les plateformes collectées — indicateurs mis à jour";
    case "fatal":
      return ev.detail
        ? `Erreur critique : ${ev.detail}`
        : "Erreur critique inattendue";
    case "warnings":
      return `Avertissement : ${(ev.warnings || []).join(" · ")}`;
    default:
      return "";
  }
}

function ProgressBar({ events }) {
  const total = events.find((e) => e?.type === "started")?.platforms_total || 0;
  const done = events.filter(
    (e) => e?.type === "platform_done" || e?.type === "platform_error",
  ).length;
  const pct = total > 0 ? Math.round((done / total) * 100) : 0;
  if (!total) return null;
  return (
    <div className="px-6 pb-3">
      <div className="flex items-center justify-between mb-1">
        <span className="text-[10px] text-ink-subtle font-medium">
          Progression
        </span>
        <span className="text-[10px] font-bold text-ink">
          {done}/{total} plateformes
        </span>
      </div>
      <div className="h-1.5 w-full rounded-full bg-gray-100 overflow-hidden">
        <div
          className="h-full rounded-full bg-gradient-to-r from-brand to-brand-dark transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

export default function OptimizerSyncModal({
  open,
  events,
  isLoading,
  onClose,
}) {
  if (!open) return null;

  const hasError = events.some(
    (e) => e?.type === "fatal" || e?.type === "platform_error",
  );
  const isDone = !isLoading && events.some((e) => e?.type === "complete");
  const completeEvent = [...events]
    .reverse()
    .find((e) => e?.type === "complete");
  const completeHasFailure = Number(completeEvent?.platforms_failed || 0) > 0;

  const headerBg = hasError
    ? "from-red-500 to-red-700"
    : isDone && !completeHasFailure
      ? "from-green-500 to-green-700"
      : "from-[#854F0B] to-[#412402]";

  const statusLabel = hasError
    ? "Collecte interrompue"
    : isDone
      ? completeHasFailure
        ? "Collecte partielle"
        : "Collecte réussie"
      : "Collecte en cours…";

  const modal = (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
    >
      <div className="absolute inset-0 bg-black/50 backdrop-blur-md" />
      <div className="relative z-10 w-full max-w-md overflow-hidden rounded-3xl bg-white shadow-2xl animate-[slideUp_0.3s_ease_forwards]">
        {/* ── Header ── */}
        <div className={`bg-gradient-to-br ${headerBg} px-6 py-5`}>
          <div className="flex items-center justify-between gap-3">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-white/20 p-2">
                <FiZap size={18} className="text-white" />
              </div>
              <div>
                <p className="text-sm font-extrabold text-white leading-tight">
                  Collecte des données sociales
                </p>
                <p className="mt-0.5 text-xs text-white/80">{statusLabel}</p>
              </div>
            </div>
            <div className="rounded-full bg-white/20 px-2.5 py-1 text-xs font-bold text-white">
              {events.length} étape{events.length > 1 ? "s" : ""}
            </div>
          </div>
        </div>

        {/* ── Progress bar ── */}
        <div className="pt-4">
          <ProgressBar events={events} />
        </div>

        {/* ── Events list ── */}
        <div className="max-h-[300px] overflow-y-auto px-4 pb-3">
          {events.length === 0 ? (
            <div className="flex items-center gap-2 rounded-xl bg-gray-50 px-3 py-3">
              <FiLoader size={13} className="animate-spin text-brand" />
              <p className="text-xs text-ink-subtle">
                Initialisation de la collecte…
              </p>
            </div>
          ) : (
            <div className="flex flex-col gap-1.5">
              {events.map((ev, i) => (
                <EventRow
                  key={`${ev.type}-${i}`}
                  ev={ev}
                  completeHasFailure={completeHasFailure}
                />
              ))}
            </div>
          )}
        </div>

        {/* ── Footer ── */}
        <div className="border-t border-gray-100 px-4 py-3">
          {isLoading ? (
            <div className="flex items-center justify-center gap-2">
              <FiLoader size={12} className="animate-spin text-brand" />
              <p className="text-[11px] text-ink-subtle">
                Collecte et calcul des indicateurs en cours…
              </p>
            </div>
          ) : (
            <div className="flex items-center justify-between gap-3">
              <p className="text-[11px] text-ink-subtle">
                {isDone && !hasError
                  ? "Les indicateurs sont maintenant à jour."
                  : hasError
                    ? "Vérifiez vos connexions sociales et réessayez."
                    : ""}
              </p>
              <button
                type="button"
                onClick={onClose}
                className="rounded-full bg-brand px-5 py-1.5 text-xs font-bold text-white hover:bg-brand-dark transition-colors"
              >
                Fermer
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );

  return createPortal(modal, document.body);
}
