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
    async ({ clarifiedIdea, onDone } = {}) => {
      if (!idea || !token) return;
      setIsLoading(true);
      setError("");
      setXaiSteps([]);

      const payload = {
        idea_id: idea.id,
        name: idea.name || clarifiedIdea?.short_pitch || "",
        sector: clarifiedIdea?.sector || idea.sector || "",
        description: idea.description || clarifiedIdea?.solution_description || "",
        target_audience: idea.target_audience || clarifiedIdea?.target_users || "",
        short_pitch: clarifiedIdea?.short_pitch || idea.name || "",
        solution_description: clarifiedIdea?.solution_description || idea.description || "",
        target_users: clarifiedIdea?.target_users || idea.target_audience || "",
        problem: clarifiedIdea?.problem || idea.description || "",
        country_code: clarifiedIdea?.country_code || "TN",
        language: clarifiedIdea?.language || "fr",
        access_token: token,
      };

      try {
        await readSSEStream(marketApi.streamUrl(), payload, async (eventType, data) => {
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
              await loadLatest();
              onDone?.();
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

