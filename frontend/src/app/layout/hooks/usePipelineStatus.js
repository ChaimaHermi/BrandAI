import { useMemo } from "react";
import { CLARITY_SCORE_MIN_PIPELINE } from "@/agents/clarifier/constants";

/**
 * usePipelineStatus
 * Extracted from PipelineLayout — computes all derived status booleans and the
 * per-agent status function.
 *
 * Behaviour is identical to the original PipelineLayout computations.
 *
 * Returns:
 *   getStatus(agentId)  — "done" | "active" | "pending"
 *   progressPct         — 0–100
 *   pipelineEnabled     — boolean (clarified + score threshold met)
 *   pipelineCompleted   — boolean (market or marketing done)
 */
export function usePipelineStatus({
  idea,
  hasMarketResult,
  hasMarketingResult,
  hasBrandIdentityResult,
  activeAgentId,
}) {
  return useMemo(() => {
    const clarifierDone = idea?.clarity_status === "clarified";

    const marketDone =
      hasMarketResult || ["market_done", "done"].includes(idea?.status);

    const marketingDone =
      hasMarketingResult || idea?.status === "done";

    const brandIdentityDone =
      hasBrandIdentityResult ||
      (Array.isArray(idea?.pipeline_progress?.brand_identity?.name_options) &&
        idea.pipeline_progress.brand_identity.name_options.length > 0);

    const pipelineCompleted = marketDone || marketingDone;

    const completedImplemented = [clarifierDone, marketDone, marketingDone].filter(Boolean).length;
    const progressPct = pipelineCompleted
      ? 100
      : Math.round((completedImplemented / 3) * 100);

    const pipelineEnabled =
      idea?.clarity_status === "clarified" &&
      (idea?.clarity_score ?? 0) >= CLARITY_SCORE_MIN_PIPELINE;

    function getStatus(agentId) {
      if (agentId === "clarifier") return clarifierDone ? "done" : "active";
      if (agentId === "market") {
        if (marketDone) return "done";
        return activeAgentId === "market" ? "active" : "pending";
      }
      if (agentId === "marketing") {
        if (marketingDone) return "done";
        return activeAgentId === "marketing" ? "active" : "pending";
      }
      if (agentId === "brand") {
        if (brandIdentityDone) return "done";
        return activeAgentId === "brand" ? "active" : "pending";
      }
      // Placeholder agents (content, website, optimizer)
      if (pipelineCompleted) return "pending";
      return "pending";
    }

    return {
      getStatus,
      progressPct,
      pipelineEnabled,
      pipelineCompleted,
      clarifierDone,
      marketDone,
      marketingDone,
      brandIdentityDone,
    };
  }, [
    idea,
    hasMarketResult,
    hasMarketingResult,
    hasBrandIdentityResult,
    activeAgentId,
  ]);
}
