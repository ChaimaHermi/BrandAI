import { useCallback, useEffect, useState } from "react";
import {
  fetchOptimizerStats,
  fetchRecommendation,
  regenerateRecommendation,
} from "../api/optimizer.api";

const INITIAL_PLATFORM = "global";

/**
 * @param {{ ideaId: number|null, token: string|null }} params
 */
export function useOptimizer({ ideaId, token }) {
  const [activePlatform, setActivePlatform] = useState(INITIAL_PLATFORM);

  /** @type {[import('../types/optimizer.types').PlatformStats|null, Function]} */
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(false);

  /** @type {[import('../types/optimizer.types').Recommendation|null, Function]} */
  const [recommendation, setRecommendation] = useState(null);
  const [recoLoading, setRecoLoading] = useState(false);

  const loadStats = useCallback(async () => {
    if (!ideaId) return;
    setStatsLoading(true);
    try {
      const data = await fetchOptimizerStats(ideaId, activePlatform, token);
      setStats(data);
    } catch {
      // Backend pas encore disponible — on affiche simplement l'état vide
      setStats(null);
    } finally {
      setStatsLoading(false);
    }
  }, [ideaId, activePlatform, token]);

  const loadRecommendation = useCallback(async () => {
    if (!ideaId) return;
    setRecoLoading(true);
    try {
      const data = await fetchRecommendation(ideaId, activePlatform, token);
      setRecommendation(data);
    } catch {
      setRecommendation(null);
    } finally {
      setRecoLoading(false);
    }
  }, [ideaId, activePlatform, token]);

  const handleRegenerate = useCallback(async () => {
    if (!ideaId) return;
    setRecoLoading(true);
    try {
      const data = await regenerateRecommendation(ideaId, activePlatform, token);
      setRecommendation(data);
    } catch {
      setRecommendation(null);
    } finally {
      setRecoLoading(false);
    }
  }, [ideaId, activePlatform, token]);

  const handlePlatformChange = useCallback((platform) => {
    setActivePlatform(platform);
    setStats(null);
    setRecommendation(null);
  }, []);

  useEffect(() => {
    loadStats();
    loadRecommendation();
  }, [loadStats, loadRecommendation]);

  return {
    activePlatform,
    onPlatformChange: handlePlatformChange,
    stats,
    statsLoading,
    recommendation,
    recoLoading,
    onRegenerate: handleRegenerate,
  };
}
