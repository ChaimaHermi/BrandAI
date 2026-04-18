import { ToolStep } from "./ToolStep";
import { GUARANTEED_TOOLS, OPTIONAL_TOOLS } from "./constants";

/**
 * Renders the full ordered list of tool steps.
 *
 * - Guaranteed tools are always visible (pending until they run).
 * - Optional tools appear only once they show up in `steps`.
 *
 * @param {{ steps: Array<{ tool: string, status: 'running' | 'done' }> }} props
 */
export function ProgressStepper({ steps }) {
  /**
   * @param {string} tool
   * @returns {'pending' | 'running' | 'done'}
   */
  function getStatus(tool) {
    return steps.find((s) => s.tool === tool)?.status ?? "pending";
  }

  // Collect optional tools that have appeared so far
  const visibleOptional = OPTIONAL_TOOLS.filter((t) =>
    steps.some((s) => s.tool === t)
  );

  const allVisible = [...GUARANTEED_TOOLS, ...visibleOptional];

  return (
    <div className="divide-y divide-gray-100">
      {allVisible.map((tool) => (
        <ToolStep key={tool} tool={tool} status={getStatus(tool)} />
      ))}
    </div>
  );
}
