import { useCallback, useEffect, useState } from "react";
import { useLocation } from "react-router-dom";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";

function authHeaders(token) {
  return { Authorization: "Bearer " + token };
}

/**
 * usePipelineData
 * Extracted from PipelineLayout — owns the idea fetch and module-availability checks.
 *
 * Behaviour is identical to the original refetchIdea callback:
 *   - Fetches the idea on every pathname change (route navigation)
 *   - Conditionally checks market/marketing/branding availability based on active route
 *
 * Returns: { idea, hasMarketResult, hasMarketingResult, hasBrandIdentityResult, refetch }
 */
export function usePipelineData(id, token) {
  const location = useLocation();

  const [idea,                   setIdea]                   = useState(null);
  const [hasMarketResult,        setHasMarketResult]        = useState(false);
  const [hasMarketingResult,     setHasMarketingResult]     = useState(false);
  const [hasBrandIdentityResult, setHasBrandIdentityResult] = useState(false);

  const refetch = useCallback(async () => {
    if (!id || !token) return null;

    const pathname = location.pathname;
    const checkBrand  = pathname.includes("/brand");
    const checkMarket = pathname.includes("/market") ||
                        pathname.includes("/marketing") ||
                        pathname.includes("/results");

    try {
      const res  = await fetch(`${API_URL}/ideas/${id}`, { headers: authHeaders(token) });
      const data = res.ok ? await res.json() : null;
      if (data) setIdea(data);

      const pipelineMayHaveResults = ["market_done", "done", "running"].includes(data?.status);

      const needsAvailability =
        data &&
        ((checkMarket && pipelineMayHaveResults) || checkBrand);

      if (needsAvailability) {
        try {
          const avRes = await fetch(
            `${API_URL}/ideas/${id}/pipeline-availability`,
            { headers: authHeaders(token) },
          );
          if (avRes.ok) {
            const av = await avRes.json();
            if (checkMarket && pipelineMayHaveResults) {
              setHasMarketResult(!!av.has_market_analysis);
              setHasMarketingResult(!!av.has_marketing_plan);
            } else {
              setHasMarketResult(false);
              setHasMarketingResult(false);
            }
            if (checkBrand) {
              setHasBrandIdentityResult(!!av.has_brand_kit);
            } else {
              setHasBrandIdentityResult(false);
            }
          } else {
            setHasMarketResult(false);
            setHasMarketingResult(false);
            setHasBrandIdentityResult(false);
          }
        } catch {
          setHasMarketResult(false);
          setHasMarketingResult(false);
          setHasBrandIdentityResult(false);
        }
      } else {
        setHasMarketResult(false);
        setHasMarketingResult(false);
        setHasBrandIdentityResult(false);
      }
      return data;
    } catch (e) {
      console.error("[usePipelineData] refetch error:", e);
      setHasMarketResult(false);
      setHasMarketingResult(false);
      setHasBrandIdentityResult(false);
      return null;
    }
  }, [id, token, location.pathname]);

  useEffect(() => {
    refetch();
  }, [refetch]);

  return {
    idea,
    hasMarketResult,
    hasMarketingResult,
    hasBrandIdentityResult,
    refetch,
  };
}
