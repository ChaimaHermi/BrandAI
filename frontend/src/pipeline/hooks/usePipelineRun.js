// Hook stub to manage BrandAI multi-agent pipeline run state.
// TODO: connect to real pipeline API and SSE when backend is ready.

import { useState, useCallback } from "react";
import { runPipeline, getPipelineStatus } from "../api/pipeline.api";

export function usePipelineRun(ideaId) {
  const [status, setStatus] = useState("idle"); // idle | running | done | error
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const start = useCallback(
    async (options = {}) => {
      if (!ideaId) return;
      setStatus("running");
      setError(null);
      try {
        const res = await runPipeline(ideaId, options);
        setResults(res);
        setStatus("done");
      } catch (e) {
        setError(e);
        setStatus("error");
      }
    },
    [ideaId],
  );

  const refresh = useCallback(
    async () => {
      if (!ideaId) return;
      try {
        const res = await getPipelineStatus(ideaId);
        setResults(res);
      } catch (e) {
        setError(e);
      }
    },
    [ideaId],
  );

  return {
    status,
    results,
    error,
    start,
    refresh,
  };
}

export default usePipelineRun;

