import { FiCheck } from "react-icons/fi";
import { TOOL_META } from "./constants";

/**
 * A single row in the generation progress stepper.
 *
 * @param {{ tool: string, status: 'pending' | 'running' | 'done' }} props
 */
export function ToolStep({ tool, status }) {
  const meta = TOOL_META[tool] ?? {
    label: tool,
    description: "",
    Icon: null,
  };
  const { label, description, Icon } = meta;

  const isPending = status === "pending";
  const isRunning = status === "running";
  const isDone = status === "done";

  return (
    <div className="flex items-center gap-3 py-2">
      {/* Status indicator circle */}
      <div className="relative flex-shrink-0">
        {isDone ? (
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-success/10 ring-1 ring-success/30">
            <FiCheck className="h-3.5 w-3.5 text-success" strokeWidth={2.5} />
          </div>
        ) : isRunning ? (
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-brand/10 ring-1 ring-brand/40">
            {/* Animated brand dot */}
            <span className="block h-2.5 w-2.5 animate-pulse rounded-full bg-brand" />
          </div>
        ) : (
          <div className="flex h-7 w-7 items-center justify-center rounded-full bg-gray-100 ring-1 ring-gray-200">
            <span className="block h-2.5 w-2.5 rounded-full bg-gray-300" />
          </div>
        )}
      </div>

      {/* Tool icon + labels */}
      <div className="flex min-w-0 flex-1 items-center gap-2">
        {Icon && (
          <Icon
            className={
              isDone
                ? "h-4 w-4 flex-shrink-0 text-success"
                : isRunning
                  ? "h-4 w-4 flex-shrink-0 text-brand"
                  : "h-4 w-4 flex-shrink-0 text-ink-subtle"
            }
          />
        )}
        <div className="min-w-0">
          <p
            className={
              "truncate text-sm font-medium " +
              (isDone
                ? "text-success"
                : isRunning
                  ? "text-brand-dark"
                  : "text-ink-subtle")
            }
          >
            {label}
            {isRunning && (
              <span className="ml-1 inline-block animate-pulse tracking-widest text-brand">
                ...
              </span>
            )}
          </p>
          {description && (
            <p className="truncate text-2xs text-ink-muted">{description}</p>
          )}
        </div>
      </div>

      {/* Right-side indicator */}
      <div className="flex-shrink-0 text-right">
        {isRunning && (
          <svg
            className="h-4 w-4 animate-spin text-brand"
            viewBox="0 0 24 24"
            fill="none"
            aria-hidden="true"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
            />
          </svg>
        )}
        {isDone && (
          <span className="text-2xs font-semibold uppercase tracking-wide text-success">
            Fait
          </span>
        )}
      </div>
    </div>
  );
}
