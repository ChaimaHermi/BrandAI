import { FaInstagram, FaFacebookF, FaLinkedinIn } from "react-icons/fa";
import { ProgressStepper } from "./ProgressStepper";
import { GUARANTEED_TOOLS, OPTIONAL_TOOLS } from "./constants";

/** Per-platform visual config. */
const PLATFORM_CONFIG = {
  instagram: {
    label: "Instagram",
    Icon: FaInstagram,
    headerClass:
      "bg-gradient-to-r from-purple-500 via-pink-500 to-orange-400 text-white",
  },
  facebook: {
    label: "Facebook",
    Icon: FaFacebookF,
    headerClass: "text-white",
    headerStyle: { backgroundColor: "#1877F2" },
  },
  linkedin: {
    label: "LinkedIn",
    Icon: FaLinkedinIn,
    headerClass: "text-white",
    headerStyle: { backgroundColor: "#0A66C2" },
  },
};

/**
 * Full-screen overlay modal displayed while the SSE generation is in progress.
 *
 * Props:
 *   open        — boolean, whether the modal is visible
 *   platform    — 'instagram' | 'facebook' | 'linkedin'
 *   steps       — array of { tool, status } from useContentGenerationSSE
 *   isStreaming  — boolean (true while SSE is open)
 *   error       — string | null
 */
export function GenerationProgressModal({ open, platform, steps, isStreaming, error }) {
  if (!open) return null;

  const config = PLATFORM_CONFIG[platform] ?? PLATFORM_CONFIG.instagram;
  const { label, Icon, headerClass, headerStyle = {} } = config;

  // Progress bar computation
  const totalTools = [...GUARANTEED_TOOLS, ...OPTIONAL_TOOLS].filter(
    (t) =>
      GUARANTEED_TOOLS.includes(t) || steps.some((s) => s.tool === t)
  );
  const doneCount = steps.filter((s) => s.status === "done").length;
  const totalCount = Math.max(
    GUARANTEED_TOOLS.length,
    steps.length,
    totalTools.length
  );
  const progressPercent =
    totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0;

  // Use an indeterminate shimmer when nothing has completed yet
  const isIndeterminate = doneCount === 0 && isStreaming;

  return (
    <div
      className="fixed inset-0 z-[200] flex items-center justify-center p-4"
      aria-modal="true"
      role="dialog"
      aria-label={`Génération ${label}`}
    >
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" />

      {/* Card */}
      <div className="relative w-full max-w-md rounded-2xl bg-white shadow-card overflow-hidden">
        {/* Header */}
        <div
          className={`flex items-center gap-3 px-5 py-4 ${headerClass}`}
          style={headerStyle}
        >
          <Icon className="h-5 w-5 flex-shrink-0" />
          <h2 className="text-base font-semibold tracking-tight">
            Génération {label}
          </h2>
          {isStreaming && (
            <span className="ml-auto text-xs font-normal opacity-80 animate-pulse">
              En cours…
            </span>
          )}
        </div>

        {/* Body */}
        <div className="px-5 py-4">
          {error ? (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error}
            </div>
          ) : (
            <ProgressStepper steps={steps} />
          )}
        </div>

        {/* Footer — progress bar */}
        <div className="px-5 pb-5">
          <div className="relative h-2 w-full overflow-hidden rounded-full bg-gray-100">
            {isIndeterminate ? (
              /* Indeterminate shimmer */
              <div
                className="absolute inset-y-0 w-1/3 rounded-full bg-brand/60"
                style={{
                  animation: "shimmer 1.4s ease-in-out infinite",
                }}
              />
            ) : (
              /* Determinate fill */
              <div
                className="absolute inset-y-0 left-0 rounded-full bg-brand transition-all duration-500 ease-out"
                style={{ width: `${progressPercent}%` }}
              />
            )}
          </div>
          <p className="mt-1.5 text-right text-2xs text-ink-muted">
            {isIndeterminate
              ? "Initialisation…"
              : `${doneCount} / ${totalCount} étapes`}
          </p>
        </div>
      </div>

      {/* Inline keyframe for the indeterminate shimmer */}
      <style>{`
        @keyframes shimmer {
          0%   { left: -33%; }
          100% { left: 100%; }
        }
      `}</style>
    </div>
  );
}
