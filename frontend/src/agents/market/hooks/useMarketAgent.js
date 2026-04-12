import { useCallback, useMemo, useRef, useState } from "react";
import { useSSEStream } from "@/agents/shared/hooks/useSSEStream";
import { getLatestMarketAnalysis, marketApi } from "../api/market.api";
import { mapMarketReport } from "../utils/mapMarketReport";

export function useMarketAgent({ idea, token }) {
  const [activeTab, setActiveTab] = useState("overview");
  const [report, setReport] = useState(null);
  const [rawReport, setRawReport] = useState(null);
  const [xaiSteps, setXaiSteps] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const inFlightRef = useRef(false);
  const runIdRef = useRef(0);
  const hasStreamErrorRef = useRef(false);

  const { readSSEStream } = useSSEStream();

  const loadLatest = useCallback(async () => {
    if (!idea?.id || !token) return null;
    const latest = await getLatestMarketAnalysis(idea.id, token);
    const raw = latest?.result_json || latest;
    const mapped = mapMarketReport(raw);
    setRawReport(raw || null);
    setReport(mapped);
    return { raw: raw || null, mapped };
  }, [idea?.id, token]);

  const startMarketAnalysis = useCallback(
    async ({ clarifiedIdea, onDone, mode = "pipeline" } = {}) => {
      if (!idea || !token) return;
      if (inFlightRef.current) {
        return;
      }
      inFlightRef.current = true;
      hasStreamErrorRef.current = false;
      const runId = Date.now() + Math.random();
      runIdRef.current = runId;

      setIsLoading(true);
      setError("");
      setXaiSteps([]);
      const payload =
        mode === "market_only"
          ? {
              idea_id: idea.id,
              name:
                clarifiedIdea?.short_pitch ||
                idea.clarity_short_pitch ||
                idea.name ||
                "",
              sector:
                clarifiedIdea?.sector ||
                idea.clarity_sector ||
                idea.sector ||
                "",
              description:
                clarifiedIdea?.solution_description ||
                idea.clarity_solution ||
                idea.description ||
                "",
              target_audience:
                clarifiedIdea?.target_users ||
                idea.clarity_target_users ||
                idea.target_audience ||
                "",
              short_pitch:
                clarifiedIdea?.short_pitch ||
                idea.clarity_short_pitch ||
                idea.name ||
                "",
              solution_description:
                clarifiedIdea?.solution_description ||
                idea.clarity_solution ||
                idea.description ||
                "",
              target_users:
                clarifiedIdea?.target_users ||
                idea.clarity_target_users ||
                idea.target_audience ||
                "",
              problem:
                clarifiedIdea?.problem ||
                idea.clarity_problem ||
                idea.description ||
                "",
              country_code:
                clarifiedIdea?.country_code ||
                idea.clarity_country_code ||
                "TN",
              language:
                clarifiedIdea?.language || idea.clarity_language || "fr",
              access_token: token,
            }
          : {
              idea_id: idea.id,
              access_token: token,
            };

      try {
        const streamUrl =
          mode === "market_only"
            ? marketApi.marketOnlyStreamUrl()
            : marketApi.streamUrl();

        await readSSEStream(streamUrl, payload, async (eventType, data) => {
          if (runIdRef.current !== runId) return;
          console.log("[market SSE]", { runId, eventType, data });

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
            hasStreamErrorRef.current = true;
            setError(data?.message || "Erreur pendant l'analyse de marché");
            console.error("[market SSE error]", { runId, data });
          }

          if (eventType === "done") {
            if (data?.success) {
              if (mode !== "market_only" && data?.stopped_at === "clarifier") {
                setError(
                  "Le pipeline s'est arrêté au Clarifier (questions/refus).",
                );
              } else {
                await loadLatest();
                onDone?.();
              }
            } else {
              // Keep the real stream error if already received.
              if (!hasStreamErrorRef.current) {
                setError(
                  data?.message ||
                    "Impossible de lancer le pipeline pour le moment. Veuillez réessayer.",
                );
              }
              console.error("[market SSE done:failed]", { runId, data });
            }
            inFlightRef.current = false;
            setIsLoading(false);
          }
        });
      } catch (e) {
        if (runIdRef.current !== runId) return;
        setError(e.message || "Erreur stream market");
        console.error("[market SSE catch]", { runId, error: e });
        inFlightRef.current = false;
        setIsLoading(false);
      } finally {
        if (runIdRef.current === runId && inFlightRef.current) {
          inFlightRef.current = false;
          setIsLoading(false);
        }
      }
    },
    [idea, token, readSSEStream, loadLatest],
  );

  const hasData = useMemo(() => !!report, [report]);

  return {
    activeTab,
    setActiveTab,
    report,
    rawReport,
    hasData,
    xaiSteps,
    isLoading,
    error,
    loadLatest,
    startMarketAnalysis,
  };
}
