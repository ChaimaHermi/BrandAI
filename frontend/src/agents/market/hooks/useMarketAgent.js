import { useCallback, useMemo, useState } from "react";
import { useSSEStream } from "@/agents/shared/hooks/useSSEStream";
import { getLatestMarketAnalysis, marketApi } from "../api/market.api";
import { mapMarketReport } from "../utils/mapMarketReport";

export function useMarketAgent({ idea, token }) {
  const [activeTab, setActiveTab] = useState("overview");
  const [report, setReport] = useState(null);
  const [xaiSteps, setXaiSteps] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const { readSSEStream } = useSSEStream();

  const loadLatest = useCallback(async () => {
    if (!idea?.id || !token) return null;
    const latest = await getLatestMarketAnalysis(idea.id, token);
    const mapped = mapMarketReport(latest?.result_json || latest);
    setReport(mapped);
    return mapped;
  }, [idea?.id, token]);

  const startMarketAnalysis = useCallback(
    async ({ clarifiedIdea, onDone, mode = "pipeline" } = {}) => {
      if (!idea || !token) return;
      setIsLoading(true);
      setError("");
      setXaiSteps([]);

      const resolvedShortPitch =
        clarifiedIdea?.short_pitch || idea.clarity_short_pitch || idea.name || "";
      const resolvedSolutionDescription =
        clarifiedIdea?.solution_description || idea.clarity_solution || idea.description || "";
      const resolvedTargetUsers =
        clarifiedIdea?.target_users || idea.clarity_target_users || idea.target_audience || "";
      const resolvedProblem =
        clarifiedIdea?.problem || idea.clarity_problem || idea.description || "";
      const resolvedSector = clarifiedIdea?.sector || idea.clarity_sector || idea.sector || "";
      const resolvedCountryCode =
        clarifiedIdea?.country_code || idea.clarity_country_code || "TN";
      const resolvedLanguage = clarifiedIdea?.language || idea.clarity_language || "fr";

      const payload = {
        idea_id: idea.id,
        name: resolvedShortPitch || idea.name || "",
        sector: resolvedSector,
        description: resolvedSolutionDescription || idea.description || "",
        target_audience: resolvedTargetUsers || idea.target_audience || "",
        short_pitch: resolvedShortPitch,
        solution_description: resolvedSolutionDescription,
        target_users: resolvedTargetUsers,
        problem: resolvedProblem,
        country_code: resolvedCountryCode,
        language: resolvedLanguage,
        access_token: token,
      };

      try {
        const streamUrl =
          mode === "market_only" ? marketApi.marketOnlyStreamUrl() : marketApi.streamUrl();

        await readSSEStream(streamUrl, payload, async (eventType, data) => {
          if (eventType === "step") {
            setXaiSteps((prev) => [
              ...prev,
              {
                id: Date.now() + Math.random(),
                status: data?.status || "loading",
                stage: data?.stage || "",
                message: data?.message || "",
              },
            ]);
          }

          if (eventType === "error") {
            setError(data?.message || "Erreur pendant l'analyse de marché");
          }

          if (eventType === "done") {
            if (data?.success) {
              if (mode !== "market_only" && data?.stopped_at === "clarifier") {
                setError("Le pipeline s'est arrêté au Clarifier (questions/refus).");
              } else {
                await loadLatest();
                onDone?.();
              }
            }
            setIsLoading(false);
          }
        });
      } catch (e) {
        setError(e.message || "Erreur stream market");
        setIsLoading(false);
      }
    },
    [idea, token, readSSEStream, loadLatest],
  );

  const hasData = useMemo(() => !!report, [report]);

  return {
    activeTab,
    setActiveTab,
    report,
    hasData,
    xaiSteps,
    isLoading,
    error,
    loadLatest,
    startMarketAnalysis,
  };
}

