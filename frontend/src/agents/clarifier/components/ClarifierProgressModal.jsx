import { createPortal } from "react-dom";

/**
 * ClarifierProgressModal
 *
 * Modal overlay displayed while the Clarifier SSE stream is active
 * (currentStep === "analyzing" | "answering").
 *
 * Receives the same `xaiSteps` array as XaiBlock — no new state needed.
 * Renders step-by-step progress with the XAI colour palette and an
 * indeterminate / determinate progress bar at the bottom.
 */

/* ── Status colours (matches XaiBlock palette) ─────────────────────────── */
const STATUS_COLOR = {
  success: "text-[#1D9E75]",
  error:   "text-rose-600",
  loading: "text-gray-400",
  info:    "text-[#534AB7]",
};

const STATUS_ICON = {
  success: "✓",
  error:   "✗",
  info:    "→",
};

/* ── Single step row ──────────────────────────────────────────────────────── */
function StepRow({ step }) {
  const color = STATUS_COLOR[step.status] ?? "text-gray-400";

  return (
    <div className="flex flex-col gap-0.5">
      <div className={`flex gap-2 font-mono text-[11px] ${color}`}>
        {/* Status icon */}
        <span className="w-[14px] shrink-0">
          {step.status === "loading" ? (
            <span className="inline-flex gap-[2px]">
              <span className="animate-[pulse_1s_0ms_infinite]">·</span>
              <span className="animate-[pulse_1s_200ms_infinite]">·</span>
              <span className="animate-[pulse_1s_400ms_infinite]">·</span>
            </span>
          ) : (
            STATUS_ICON[step.status] ?? "·"
          )}
        </span>

        {/* Message + inline extras */}
        <span>{step.text}</span>
      </div>
    </div>
  );
}

/* ── Main component ───────────────────────────────────────────────────────── */
export default function ClarifierProgressModal({ open, steps, currentStep }) {
  if (!open) return null;

  const successCount = steps.filter((s) => s.status === "success").length;
  const hasError     = steps.some((s) => s.status === "error");

  /* progress bar */
  const totalExpected   = 5; // typical step count
  const progressPercent = steps.length > 0
    ? Math.min(Math.round((successCount / Math.max(totalExpected, steps.length)) * 100), 95)
    : 0;
  const isIndeterminate = successCount === 0;

  const title = currentStep === "answering"
    ? "Vérification des réponses…"
    : "Analyse de l'idée…";

  const modal = (
    <div
      className="fixed inset-0 z-[9999] flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
      aria-label={title}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/50 backdrop-blur-md" />

      {/* Card */}
      <div className="relative w-full max-w-md overflow-hidden rounded-3xl bg-white shadow-2xl animate-[slideUp_0.3s_ease_forwards]">

        {/* ── Header ─────────────────────────────────────────────────────── */}
        <div
          className="flex items-center gap-3 px-5 py-4"
          style={{ background: "linear-gradient(135deg,#085041,#1D9E75)" }}
        >
          {/* Icon */}
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/20">
            <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
              <circle cx="9" cy="9" r="6" stroke="white" strokeWidth="1.4" />
              <path d="M9 6v4M9 12v.5" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
            </svg>
          </div>

          <div className="flex-1">
            <p className="text-sm font-bold text-white">{title}</p>
            <p className="text-2xs text-white/70">Idea clarifier — XAI</p>
          </div>

          {/* Live dot + bouncing dots */}
          <div className="flex items-center gap-1.5">
            {!hasError && (
              <span className="flex items-center gap-[3px] font-mono text-[11px] text-white/80">
                <span className="animate-[bounce_0.8s_0ms_infinite] inline-block">●</span>
                <span className="animate-[bounce_0.8s_150ms_infinite] inline-block">●</span>
                <span className="animate-[bounce_0.8s_300ms_infinite] inline-block">●</span>
              </span>
            )}
          </div>
        </div>

        {/* ── Steps list ─────────────────────────────────────────────────── */}
        <div
          className="flex flex-col gap-1 overflow-y-auto px-5 py-4"
          style={{ maxHeight: "260px" }}
        >
          {steps.length === 0 ? (
            /* Skeleton rows while first events arrive */
            [1, 2, 3].map((n) => (
              <div key={n} className="flex gap-2 font-mono text-[11px] text-gray-300">
                <span className="w-[14px] shrink-0">·</span>
                <span
                  className="h-3 animate-pulse rounded bg-gray-100"
                  style={{ width: `${40 + n * 15}%` }}
                />
              </div>
            ))
          ) : (
            steps.map((step) => <StepRow key={step.id} step={step} />)
          )}
        </div>

        {/* ── Progress bar ───────────────────────────────────────────────── */}
        <div className="border-t border-[#d1fae5] bg-[#f8fffe] px-5 py-3">
          <div className="relative h-1.5 w-full overflow-hidden rounded-full bg-[#d1fae5]">
            {isIndeterminate ? (
              <div
                className="absolute inset-y-0 w-1/3 rounded-full bg-[#1D9E75]/60"
                style={{ animation: "clarifierShimmer 1.4s ease-in-out infinite" }}
              />
            ) : (
              <div
                className="absolute inset-y-0 left-0 rounded-full bg-[#1D9E75] transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            )}
          </div>
          <p className="mt-1.5 text-right font-mono text-2xs text-[#1D9E75]">
            {isIndeterminate
              ? "Initialisation…"
              : `${successCount} étape${successCount !== 1 ? "s" : ""} ✓`}
          </p>
        </div>

      </div>

      {/* Keyframe for indeterminate shimmer */}
      <style>{`
        @keyframes clarifierShimmer {
          0%   { left: -33%; }
          100% { left: 100%; }
        }
      `}</style>
    </div>
  );

  return createPortal(modal, document.body);
}
