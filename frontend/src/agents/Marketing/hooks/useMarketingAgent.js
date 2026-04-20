import { useCallback, useMemo, useState } from "react";
import { toast } from "react-toastify";
import { getLatestMarketingPlan } from "../api/marketing.api";
import { mapMarketingPlan } from "../utils/mapMarketingPlan";

export function useMarketingAgent({ idea, token }) {
  const [plan, setPlan] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const loadLatest = useCallback(async () => {
    if (!idea?.id || !token) return null;
    setIsLoading(true);
    setError("");
    try {
      const latest = await getLatestMarketingPlan(idea.id, token);
      const mapped = mapMarketingPlan(latest?.result_json || latest);
      setPlan(mapped);
      return mapped;
    } catch (e) {
      const errMsg = e.message || "Erreur lecture plan marketing";
      setError(errMsg);
      toast.error(`Impossible de charger le plan marketing : ${errMsg}`);
      return null;
    } finally {
      setIsLoading(false);
    }
  }, [idea?.id, token]);

  return {
    plan,
    isLoading,
    error,
    loadLatest,
    hasData: useMemo(() => !!plan, [plan]),
  };
}
