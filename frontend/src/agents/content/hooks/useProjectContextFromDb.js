import { useCallback, useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useAuth } from "@/shared/hooks/useAuth";
import { apiGetIdea } from "@/services/ideaApi";
import { fetchBrandingBundle } from "@/agents/brand/api/brandIdentity.api";
import { buildContentProjectDisplay } from "../utils/projectContextFromDb";

/**
 * GET /api/ideas/:id + GET /api/branding/ideas/:id/bundle (backend-api).
 * Utilise l’id dans l’URL et le JWT — ne dépend pas du PipelineContext pour afficher le bandeau.
 */
export function useProjectContextFromDb() {
  const { id: routeId } = useParams();
  const { token } = useAuth();

  const ideaId =
    routeId != null && String(routeId).length > 0
      ? Number.parseInt(String(routeId), 10)
      : null;
  const validId = Number.isFinite(ideaId) && ideaId > 0 ? ideaId : null;

  const [ideaRow, setIdeaRow] = useState(null);
  const [bundle, setBundle] = useState(null);
  const [loading, setLoading] = useState(Boolean(validId && token));
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    if (!validId || !token) {
      setIdeaRow(null);
      setBundle(null);
      setLoading(false);
      setError(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const [ideaRes, bundleRes] = await Promise.all([
        apiGetIdea(validId, token),
        fetchBrandingBundle(validId, token),
      ]);
      setIdeaRow(ideaRes);
      setBundle(bundleRes);
    } catch (e) {
      setIdeaRow(null);
      setBundle(null);
      setError(e?.message || "Impossible de charger le projet.");
    } finally {
      setLoading(false);
    }
  }, [validId, token]);

  useEffect(() => {
    load();
  }, [load]);

  const display = buildContentProjectDisplay(ideaRow, bundle);

  return {
    ideaId: validId,
    hasToken: Boolean(token),
    ideaRow,
    bundle,
    loading,
    error,
    display,
    refetch: load,
  };
}
