import { useCallback, useEffect, useState } from "react";
import {
  fetchOptimizerConnections,
  fetchRecommendation,
  regenerateRecommendation,
  runOptimizerSocialEtlSyncStream,
} from "../api/optimizer.api";

const INITIAL_PLATFORM = "global";

/**
 * @param {{ ideaId: number|null, token: string|null }} params
 */
export function useOptimizer({ ideaId, token }) {
  const [activePlatform, setActivePlatform] = useState(INITIAL_PLATFORM);

  /** @type {[import('../types/optimizer.types').Recommendation|null, Function]} */
  const [recommendation, setRecommendation] = useState(null);
  const [recoLoading, setRecoLoading] = useState(false);

  /** @type {[object|null, Function]} */
  const [connections, setConnections] = useState(null);
  const [connectionsLoading, setConnectionsLoading] = useState(false);

  const [syncLoading, setSyncLoading] = useState(false);
  const [syncError, setSyncError] = useState(null);
  /** @type {[object|null, Function]} */
  const [lastSyncResult, setLastSyncResult] = useState(null);
  /** @type {[object[], Function]} */
  const [syncEvents, setSyncEvents] = useState([]);

  const loadConnections = useCallback(async () => {
    if (!ideaId) return;
    setConnectionsLoading(true);
    try {
      const data = await fetchOptimizerConnections(ideaId, token);
      setConnections(data);
    } catch {
      setConnections(null);
    } finally {
      setConnectionsLoading(false);
    }
  }, [ideaId, token]);

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
    setRecommendation(null);
  }, []);

  const runSocialEtlSync = useCallback(async () => {
    if (!ideaId) return;
    setSyncLoading(true);
    setSyncError(null);
    setLastSyncResult(null);
    setSyncEvents([]);
    let warningsAcc = [];
    try {
      await runOptimizerSocialEtlSyncStream(ideaId, token, {
        onEvent: (ev) => {
          setSyncEvents((prev) => [...prev, ev]);
          if (ev.type === "warnings" && Array.isArray(ev.warnings)) {
            warningsAcc = ev.warnings;
          }
          if (ev.type === "fatal") {
            throw new Error(ev.detail || "Échec du pipeline");
          }
          if (ev.type === "complete") {
            setLastSyncResult({
              output_dir: ev.output_dir,
              runs: ev.runs ?? [],
              warnings: warningsAcc,
            });
          }
        },
      });
      await loadConnections();
    } catch (e) {
      setSyncError(e?.message || "Échec de la synchronisation");
    } finally {
      setSyncLoading(false);
    }
  }, [ideaId, token, loadConnections]);

  useEffect(() => {
    loadConnections();
  }, [loadConnections]);

  useEffect(() => {
    loadRecommendation();
  }, [loadRecommendation]);

  return {
    activePlatform,
    onPlatformChange: handlePlatformChange,
    recommendation,
    recoLoading,
    onRegenerate: handleRegenerate,
    connections,
    connectionsLoading,
    syncLoading,
    syncError,
    lastSyncResult,
    syncEvents,
    runSocialEtlSync,
    refetchConnections: loadConnections,
  };
}
