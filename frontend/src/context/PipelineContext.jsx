import { createContext, useContext } from "react";

/**
 * PipelineContext
 * Provides shared pipeline state to all agent pages rendered inside PipelineLayout.
 * Replaces the Outlet context pattern ({idea, setIdea, token, refetchIdea}).
 *
 * Shape: { idea, token, refetch }
 *   idea    — the current idea object (or null while loading)
 *   token   — the auth JWT string
 *   refetch — call to re-fetch the idea and module availability flags
 *
 * Usage in child pages:
 *   import { usePipeline } from "@/context/PipelineContext";
 *   const { idea, token, refetch } = usePipeline();
 */
export const PipelineContext = createContext(null);

export function usePipeline() {
  const ctx = useContext(PipelineContext);
  if (!ctx) {
    // Keep pages resilient if routed outside PipelineLayout.
    // Components can still render their empty states without a hard crash.
    return { idea: null, token: null, refetch: async () => {} };
  }
  return ctx;
}
