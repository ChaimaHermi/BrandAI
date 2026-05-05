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
  const [hasContentResult, setHasContentResult] = useState(false);
  const [hasWebsiteResult, setHasWebsiteResult] = useState(false);
  const [hasOptimizerResult, setHasOptimizerResult] = useState(false);

  const refetch = useCallback(async () => {
    if (!id || !token) return null;

    const pathname = location.pathname;
    const checkBrand  = pathname.includes("/brand");
    const checkMarket = pathname.includes("/market") ||
                        pathname.includes("/marketing") ||
                        pathname.includes("/results");
    const checkContent = true;
    const checkWebsite = true;
    const checkOptimizer = true;

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

      if (data && checkContent) {
        try {
          const [countRes, socialRes] = await Promise.all([
            fetch(`${API_URL}/ideas/${id}/generated-contents/count`, {
              headers: authHeaders(token),
            }),
            fetch(`${API_URL}/ideas/${id}/social-connections`, {
              headers: authHeaders(token),
            }),
          ]);

          let hasGeneratedContent = false;
          if (countRes.ok) {
            const countData = await countRes.json();
            hasGeneratedContent = Number(countData?.count || 0) > 0;
          }

          let hasConnectedSocial = false;
          if (socialRes.ok) {
            const socialData = await socialRes.json();
            hasConnectedSocial = Boolean(socialData?.meta || socialData?.linkedin);
          }

          setHasContentResult(hasGeneratedContent || hasConnectedSocial);
        } catch {
          setHasContentResult(false);
        }
      }

      if (data && checkWebsite) {
        try {
          const projectRes = await fetch(`${API_URL}/website/ideas/${id}`, {
            headers: authHeaders(token),
          });
          if (projectRes.ok) {
            const project = await projectRes.json();
            const hasHtml = Boolean(String(project?.current_html || "").trim());
            const isDeployed = Boolean(project?.last_deployment_url || project?.last_deployment_id);
            const hasDescription = Boolean(project?.description_json);
            setHasWebsiteResult(hasHtml || isDeployed || hasDescription);
          } else {
            setHasWebsiteResult(false);
          }
        } catch {
          setHasWebsiteResult(false);
        }
      }

      if (data && checkOptimizer) {
        try {
          const statsRes = await fetch(
            `${API_URL}/ideas/${id}/optimizer/stats?platform=facebook`,
            { headers: authHeaders(token) },
          );
          if (statsRes.ok) {
            const stats = await statsRes.json();
            const postCount = Number(stats?.kpis?.post_count || 0);
            const hasTopPosts = Array.isArray(stats?.top_posts) && stats.top_posts.length > 0;
            const hasReactions = stats?.reactions_breakdown && Object.keys(stats.reactions_breakdown).length > 0;
            setHasOptimizerResult(postCount > 0 || hasTopPosts || hasReactions);
          } else {
            setHasOptimizerResult(false);
          }
        } catch {
          setHasOptimizerResult(false);
        }
      }
      return data;
    } catch (e) {
      console.error("[usePipelineData] refetch error:", e);
      setHasMarketResult(false);
      setHasMarketingResult(false);
      setHasBrandIdentityResult(false);
      setHasContentResult(false);
      setHasWebsiteResult(false);
      setHasOptimizerResult(false);
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
    hasContentResult,
    hasWebsiteResult,
    hasOptimizerResult,
    refetch,
  };
}
